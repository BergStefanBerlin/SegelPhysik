# Numerische Präzision & Stabilität — Befunde N-Serie

Repo: BergStefanBerlin/SegelPhysik · Branch `main` · Stand: 20.10.2026
Fragestellung: Wo reicht float32 (v. a. Render-Pfad)? Wie ist der Determinismus zwischen
C++-Batch und Python-Referenz gesichert, und welche Toleranzen sind bewusst zu wählen?

Geprüfte Dateien: `render/vista.py`, `core/mesh.py`, `core/native_backend.py`,
`core/dynamik_6dof.py`, `code/cpp/src/wasserpartikel.hpp`, `code/cpp/tests/paritaet_batch.py`.

---

## 1. Was bereits richtig gemacht ist (Stabilität)

| Punkt | Beleg |
|-------|-------|
| Quaternion-Drift ist kontrolliert | `dynamik_6dof.py`: `_orientierung_schritt` baut den Rotationsschritt als Exponentialmap (Achse-Winkel aus ω) und **normalisiert das Quaternion in jedem Schritt** (`quaternion_normalisieren`) — Standardverfahren gegen Drift |
| Robuste Quaternion-Rückgewinnung | `quaternion_aus_matrix` nutzt Shepperd-Methode (Verzweigung nach größter Diagonale) statt naiver Spur-Formel — numerisch stabil über den ganzen Winkelbereich |
| Slerp abgesichert | `acos`-Argument wird auf [-1, 1] geklemmt; Nähfall (dot > 0.9995) separat behandelt |
| Semi-implizite Dämpfung | `schritt()` löst `(M + dt·R)·v_neu = …` als lineares System — steife Dämpfung kann die Geschwindigkeit in einem Schritt nicht umkehren (Kommentar im Code bestätigt die Absicht). Das ist das stabile Verfahren |
| Eingabevalidierung je Schritt | Alle Zustandsgrößen auf Endlichkeit und Form geprüft; Trägheitstensor auf Symmetrie und Positive-Definitheit (`eigvalsh`) |
| Konsistente Rasterindizierung | Python `astype(np.int64)` und C++ `static_cast<int64_t>` schneiden beide Richtung Null ab — beide Pfade liefern identische Zellzuordnung |

**Fazit Stabilität:** Der Integrationskern ist nach Stand der Technik gebaut; hier gibt es
keinen Handlungsbedarf.

---

## 2. Präzision: Wo float64 Pflicht ist und wo float32 reicht

### 2.1 Physikkern: float64 ist richtig und wird konsequent durchgehalten ✓

Die ABI-Grenze (`native_backend.py`) erzwingt ausnahmslos `np.asarray(..., dtype=np.float64)`
— Zustand, Meshes, Wrenches, Parameter. Auch der C++-Kern rechnet in `double`
(`Vektor3` = `std::array<double,3>`). Das ist die richtige Wahl: Volumen-/Momentintegrale
über Dreiecke nahe der Wasserlinie sind Differenzen großer Terme; in float32 gäbe es hier
messbare Fehler, und die Paritätstests (Abschnitt 3) würden sofort brechen.
**Keine Umstellung empfohlen.**

### 2.2 Render-Pfad: teilweise schon float32, aber nicht durchgängig

| ID | Stelle | Befund | Verbesserung | Potenzial |
|----|--------|--------|--------------|-----------|
| N1 | `vista.py` → `_surface_polydata` + `update()`: `self._surf.points = np.column_stack([...Zr...])` mit float64 | Die Wasseroberfläche wird **je Frame** als float64-Punktarray an VTK übergeben. VTK/OpenGL wandelt beim Rendern ohnehin nach float32 — die doppelte Genauigkeit bringt visuell nichts, kostet aber doppelte Upload-Bandbreite und Speicher | Vor der Zuweisung `.astype(np.float32)`; auch `_Xr/_Yr` einmalig als float32 halten | Upload-/Bandbreite halbiert; spürbar bei großen Rastern (nx·ny·Upsample-Punkte je Frame) |
| N2 | `vista.py` → `_smooth_surface`: NaN-Füllung, Median-Stack (9 Ebenen), Laplace-Glättung — alles float64 | Reine Render-Nachbearbeitung je Frame in float64 | Intern float32 (Ergebnisvisualisierung; NaN-/Median-Logik unverändert). Risiko gering, aber Test gegen sichtbare Artefakte nötig | ~halber Speicher/Bandbreite dieses Schritts |
| N3 | `vista.py` → `_bilinear_upsample` (Python-Zweig) und `elev`-Skalar (`float64`) | Upsampling und Farbskalar in float64 | float32 genügt für Farbcodierung und Geometrie | klein–mittel |
| N4 | `vista.py` → `IsoSurfaceWater.grid` ist **bereits float32** ✓; `pv.Sphere`/`pv.Box`-Meshes sind float32 ✓ | — | kein Handlungsbedarf | — |

**Faustregel:** Alles, was nach `pv.PolyData`/Actor geht, darf float32 sein; alles, was in
`schritt()`, `_EbenenSchnitt`, Hydrostatik oder Massen fließt, bleibt float64.

### 2.3 SPH-Wasserraster: Mischung ist konsistent ✓

`wasserpartikel.hpp` (`wasser_splat`): Kernelgewichte werden in double berechnet, als
float pro Beitrag gespeichert, aber in eine **double-Summe** akkumuliert; Ausgabe float.
Die Python-Seite macht dasselbe (float32-Gewichte → `np.bincount` akkumuliert float64 →
`.astype(np.float32)`). Beide Pfade sind äquivalent — keine Änderung nötig. Eine volle
float32-Akkumulation wäre schneller, würde aber die Pfad-Parität brechen: nicht empfohlen.

---

## 3. Determinismus: Ist bereits gelöst — und schränkt künftige Optimierungen ein

Der zentrale Befund: **Das Projekt hat das Determinismusproblem bereits explizit gelöst.**
`paritaet_batch.py` verlangt:

| Prüfung | Toleranz | Bedeutung |
|---------|----------|-----------|
| Zustand (C++-Batch vs. Python-Referenz, 1000 Schritte) | `rtol=0, atol=1e-12` | Bitnahe Übereinstimmung der Integration |
| Kräfte/Beiträge | `rtol=0, atol=1e-9` | Exakter Kraftvergleich (Kommentar verweist auf `pruefe_genauigkeit_v09.py`) |
| Batch(1) nacheinander vs. Batch(100) am Stück | `assert_array_equal` — **bit-exakt** | Die Batchgröße darf das Ergebnis nicht ändern dürfen |

Das heißt: Summationsreihenfolge im nativen Batch ist heute identisch zur sequentiellen
Einzelschritt-Ausführung. Zwei Konsequenzen:

1. **Die Sorge „Batch rechnet anders als die Referenz" ist durch Tests abgedeckt** — gut so.
   Die gewählten Toleranzen sind bewusst streng (keine Nachlässigkeit), das ist die richtige
   Politik für einen Referenz-Vergleich.
2. **Diese Strenge ist der harte Rand für P1/P2 aus `Parallelitaet.md`:**
   - P1 (SIMD/SoA im Ebenenschnitt): horizontale Summationen müssen in fester Reihenfolge
     erfolgen (kein FMA-Reassoziieren über Dreiecke hinweg); Klassifikation selbst ist
     branch-frei möglich, ohne Summen anzutasten.
   - P2 (OpenMP über Körperteile): bricht `atol=1e-12`, sobald Teilsummen in beliebiger
     Reihenfolge addiert werden. Nur umsetzbar mit fester Teil→Thread-Zuordnung oder
     bewusster Toleranzlockerung.
   - Niemals `-ffast-math` / `/fp:fast` — würde die Parität sofort zerstören.

**Empfehlung Toleranzpolitik:** Die 1e-12/1e-9-Parität als Regressionsanker behalten.
Falls P2 umgesetzt wird: neuen Testmodus „tolerante Parität" mit dokumentiertem
Fehlerbudget (z. B. relativer Fehler < 1e-9 über 1000 Schritte) daneben legen, statt die
strengen Schwellen global zu senken.

### Kleine Pfad-Differenz (kosmetisch, aber der Vollständigkeit halber)

| ID | Stelle | Befund |
|----|--------|--------|
| N5 | `_calibrate`: Python nutzt `np.median` (Mittelung der zwei Mittelwerte in float64), C++ `wasser_kalibrieren` mittelt in float (`(untere + median) / 2.f`) | Bei gerader Anzahl kalibrierter Zellen können sich Python- und C++-Normierung im letzten Bit unterscheiden. Betrifft nur das Iso-Level der **Wasserdarstellung**, nie die Physik. Falls bitidentische Render-Parität gewünscht: Mittelung in double wie in Python |

---

## 4. Sortierte Empfehlungen

| Rang | ID | Maßnahme | Aufwand | Risiko |
|------|----|----------|---------|--------|
| 1 | N1 | Wasseroberfläche als float32 an VTK übergeben | gering (1–2 Zeilen) | vernachlässigbar |
| 2 | N3 | Upsample/elev-Skalare float32 | gering | gering |
| 3 | N5 | Kalibrier-Mittelung angleichen (optional, nur Render-Parität) | gering | keins |
| 4 | N2 | `_smooth_surface` intern float32 | mittel | mäßig (Artefakte testen) |
| — | §3 | Toleranzpolitik: strenge Parität behalten, P1 branch-frei/reihenfolgetreu umsetzen, P2 nur mit Fehlerbudget | Konzeptentscheid | — |

Physikkern float64: unverändert lassen (Abschnitt 2.1).

---

## 5. Quellen

- Direkt gelesen (Branch `main`, 20.10.2026): `render/vista.py`, `core/mesh.py`,
  `core/native_backend.py`, `core/dynamik_6dof.py`, `code/cpp/src/wasserpartikel.hpp`,
  `code/cpp/tests/paritaet_batch.py`.
- Verfahren: Quaternion-Normalisierung/Exponentialmap und Shepperd-Methode sind
  Standardliteratur (z. B. Diebel, *Representing Attitude*, 2006); semi-implizite
  Integration mit Dämpfungsmatrix ist Standard der Mehrkörpersimulation.
