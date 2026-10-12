# Umsetzungsplan V5 – P5c Physik-Wiederaufnahme
**Stand:** 12.10.2026 · Status: Phase A offen · Vorgänger: Umsetzungsplan_v4 (Schritte 0–4 abgeschlossen, Tag `v4.0-schritt4`)

## §0 Grundprinzip (aus Spec V4, unverändert)

**Eine Kraftfunktion, zwei Treiber.** Die Kraftfunktion ist eine reine Funktion – kein Zustand,
keine Grafik, keine Zeit-Annahmen. Sie wird vom statischen Solver und von der Echtzeit-Integration
gleichermaßen genutzt. Alle physikalischen Größen in SI-Einheiten (R6); Umrechnung nur in der
Darstellungsschicht.

## §1 Physik-Kern

- **Auftrieb:** F_A = rho_W * g * V_tauch, Richtung +z, angreifend im **Verdrängungsschwerpunkt K**
  (Schwerpunkt des unterwasser liegenden Volumens)
- **Gewicht:** F_G = m * g abwärts, angreifend in r_S
- **Moment um r_S:** M = (K − r_S) × F_A (das Gewicht hat keinen Hebelarm im Schwerpunktframe)
- **Gleichgewicht** genau dann, wenn V_tauch = m / rho_W **und** K senkrecht unter/über r_S liegt

### Berechnungskette (Phase A)

1. **Verdrängtes Volumen V_tauch:** `wasser_schnitt.schneide_am_wasser` schneidet jedes Blatt-Mesh
   an z=0; Tetraeder-Integration liefert das getauchte Teilvolumen → Summe über alle Blätter
2. **Auftriebskraft:** F_A = rho_W * g * V_tauch, Richtung +z
3. **Auftriebssummenpunkt K:** flächengewichtetes Mittel der Teilschwerpunkte der getauchten
   Tetraeder – der Schwerpunkt *des verdrängten Volumens*, nicht des Körpers
4. **Moment um r_S:** (K − r_S) × F_A

Bei verteilten Blättern (Rumpf, Kiel, Segel …) werden je Blatt Volumen und Schwerpunkt gerechnet
und summiert – die Additivität aus Testblock C4, nur unter Wasser.

## §2 Modi-Umschaltung (bereits implementiert, Tag-Kandidat `v4.0-p5c-schritt1`)

- Tasten **r** (RUHEND) / **s** (STATISCH) / **z** (ECHTZEIT), vollvermascht, Ziel-Startwert ist
  immer die aktuelle Pose; gleiche Taste = No-op; Modus-Text unten links; Ein-Objekt-Anzeige (Space)
- RUHEND friert die Szene ein; STATISCH/ECHTZEIT sind derzeit Platzhalter ohne Physik

## §3 Phase A – Kraftfunktion (rein, keine Grafik, pytest)

**Neu:** `segelphysik/core/auftrieb.py`

- Eingabe: Pose (Tauchung z, Krängung φ, Trim θ) + Körper/Meshes
- Nutzt `wasser_schnitt.schneide_am_wasser` je Blatt-Mesh, summiert Teilvolumina und
  Teilschwerpunkte zum Gesamtauftrieb
- Ausgabe: `Auftriebsergebnis(V_tauch, K, F_A, M)` – ein Datenrecord, von beiden Treibern nutzbar

**Tests Block N (alle analytisch):**

| Fall | Referenz |
|---|---|
| N0 Wasserdichtheits-Check | Vorzeichenkonsistenz der Tetraeder-Volumina aller 8 Boot-Meshes |
| Quader, Tauchtiefe t | V = a·b·t, K in t/2 Tiefe |
| Quader vollständig getaucht | V = abc, K = Quaderzentrum |
| Schwimmender Quader | Gleichgewicht bei t = (rho_K/rho_W)·h |
| Gekrängter Quader | Restmoment ≠ 0, Vorzeichen stabilisierend |
| Segel über Wasser | trägt null zum Auftrieb bei |
| Additivität | Auftrieb der Gruppe = Summe der Blätter (C4-Pendant) |

**⚠ Offenes Risiko (N0 zuerst):** Der Rumpf ist als Schale modelliert (Flächenmasse 5 mm), aber die
OBJ-Geometrie stammt aus dem Unity-Modell. V_tauch braucht ein **geschlossenes Volumen**. Ist ein
Mesh offen, entscheidet man zwischen Mesh-Reparatur oder Wanddicke-Modell
(V_tauch aus getauchter Fläche × Dicke). Die Entscheidung fällt, wenn N0 vorliegt.

## §4 Phase B – Statischer Solver

**Neu:** `segelphysik/core/statisch.py`

- Newton-Iteration über **(z, φ)** (Trim später): Startwert = aktuelle Pose,
  Konvergenzkriterium auf |Restmoment| und |ΔF|
- Rückgabe: Lösung + Iterationszahl + **metazentrische Höhe** (Nebenprodukt)
- Hängt sich in den STATISCH-Platzhalter von `sim_modus.py` ein; Startmodus bleibt RUHEND
- Solver springt nach Konvergenz sofort in die Gleichgewichtslage (animiertes Suchen später)

**Tests Block P:** Quader-Gleichgewichte geschlossen verifiziert · Konvergenz aus gestörter Pose
(±15°) · Nicht-Konvergenz wird sauber gemeldet (kein Endlosloop) · STATISCH-Lösung ist exakt
kraftfrei (Residuum < ε)

## §5 Phase C – Kräftebild (Pfeile)

**Neu:** Overlay-Layer „Kräfte" (P5a-Muster), Taste **7**:

- Pfeil F_G ab r_S abwärts (grau), Pfeil F_A ab K aufwärts (blau), Länge ∝ Kraft mit
  **gemeinsamer fester Skala** (Beckenmaßstab) – sonst sieht man die Restkraft beim Einpendeln nicht
- Hebelarm K ↔ r_S als dünne Verbindungslinie
- Textzeile: V_tauch, F_A, |M| – nur im Modus STATISCH/ECHTZEIT sichtbar

Kann parallel zu B/D gebaut werden, sobald A steht.

## §6 Phase D – Dynamik (Echtzeit)

**Neu:** `segelphysik/core/dynamik.py`

- Semi-implizites Euler, **festes dt aus der Konfiguration** (Determinismus K7″,
  Akkumulator-Muster – nie Wanduhr-dt)
- Freiheitsgrade: Tauchung (Translation z) + Krängung (Rotation um die durch r_S laufende
  Längsachse); Trim später
- Trägheitstensor aus `massen.py` (existiert, geprüft)

### Dämpfung (Entscheidung D2 – getroffen 12.10.)

Die Dämpfung wird **zunächst so angenommen, dass kaum Schwingung entsteht** (stark gedämpft,
quasi-aperiodisches Einschwingen). Sie ist ein **expliziter, dokumentierter Modellparameter** in
der Konfiguration (kein versteckter Hack) – getrennt für Tauchung und Krängung.
**Später wird die Dämpfung über hydro- bzw. aerodynamische Effekte gerechnet** und ersetzt dann
diesen Übergangswert. Bis dahin gilt: Physik korrekt, Bewegung visuell ruhig.

**Tests Block Q:** STATISCH-Lösung als Startzustand → Boot bleibt liegen (Verkettungs-Gegenprobe) ·
Energie monoton abnehmend bei Dämpfung > 0 · gleicher Start → bitidentische Bahn (K7″) ·
Schwebungsdauer des ungedämpften Quaders analytisch gegenrechenbar

## §7 Phase E – Abnahme & Einchecken

- Konsolen-Protokoll des Solvers (Iterationen, Residuum)
- Sichtprobe: Space→Boot, `s`, Pfeile an (7), Solver-Protokoll in der Konsole
- Commit + Tag `v4.0-p5c-schritt2`

## §8 Reihenfolge & Größenordnung

| Phase | Lieferung | hängt ab von |
|---|---|---|
| A | auftrieb.py + Block N | wasser_schnitt ✓, massen ✓ |
| B | statisch.py + Block P | A |
| C | Pfeil-Layer + Taste 7 | A (nur Anzeige) |
| D | dynamik.py + Block Q | A, B |
| E | Abnahme | alle |

## §9 Getroffene Entscheidungen

| ID | Entscheidung | Stand |
|---|---|---|
| D1 | Pfeilskala **fix** pro Szene (Beckenmaßstab) | entschieden |
| D2 | Dämpfung zunächst stark (kaum Schwingung), expliziter Modellparameter; später Ersatz durch Hydro-/Aerodynamik | **entschieden 12.10.** |
| D3 | Taste 7 fürs Kräftebild (Konstruktionsachsen-Idee zurückgestellt) | entschieden |
| D4 | g = 9,80665 m/s² (Norm-Schwere) für alle Referenzwerte | entschieden |
| D5 | Tasten r/s/z statt Zyklus-Taste p; Uhr-Reset auf `n` | entschieden 12.10. |

## §10 Abgrenzung (später)

- Stör-Tasten (←/→ Krängung, ↑/↓ Trim, Bild↑/↓ Tauchung) → Schritt 3
- Trim (θ) als dritter Freiheitsgrad → nach Schritt 2
- Hydro-/Aerodynamische Dämpfungsmodelle → nach Schritt 2 (ersetzen den Übergangswert aus D2)
- Konfigurator (P6) → danach
