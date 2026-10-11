# Tagesbericht 2026-10-11 – SegelPhysik V4

**Repo:** github.com/BergStefanBerlin/SegelPhysik · **Endstand:** Commit `9a72ddd`-Nachfolge `9a30458` → Feierabend-Push, Tag **`v4.0-schritt3`**
**Tests:** 72/72 grün (pytest 9.1.1, Python 3.14.0)

---

## 1. Meilensteine

| Schritt | Inhalt | Status |
|---|---|---|
| Schritt 0 | Konfig-Lader + Validierung | ✅ (Tag `v4.0-schritt1`) |
| Schritt 1 | Körper-Klasse + Massen (P1–P4, rekursive Komposition, Schwerpunktframe) | ✅ (Tag `v4.0-schritt1`) |
| Schritt 2 | Grafik K1 Licht + K2 Wasser/Verlauf + K5 Kamera F1–F4, P4-Farben aktiv | ✅ (Tag `v4.0-schritt2`) |
| Schritt 3 | Overlays: Layer-Registry, r_S-Marker (Taste 5), Hauptträgheitsachsen (Taste 6) | ✅ (**Tag `v4.0-schritt3`, heute**) |
| Schritt 4 | K3 Materialglanz + K4 Tube-Overlays | ⬜ offen |
| P5c | Physik-Wiederaufnahme (Solver zuerst, dann Echtzeit) | ⬜ nächster Block |

## 2. Option A – Ehrliche Massen (Kern des Tages)

Ausgangspunkt: Nutzer-Einschätzung „der Schwerpunkt müsste tiefer liegen" – bestätigt durch Audit.

| Szenario | Masse | CM z | Ballast |
|---|---|---|---|
| Vollkörper-Rumpf (Start) | 6304,7 kg | −0,024 m | 4,9 % |
| Rumpf/Ruder als GfK-Schale 5 mm | 524,0 kg | −0,166 m | 58,6 % |
| **+ Mast/Boom als Alu-Hohlprofil 2 mm (Endstand)** | **459,44 kg** | **−0,495 m** | **66,9 %** |

- Neu: exakter Schalen-Trägheitstensor `traegheitstensor_flaechig()` in `core/massen.py`
  (vorher: Schalen hätten `I = 0` gehabt – bei den winzigen Segeln nie aufgefallen)
- Analytisch verifiziert: Platte `Iz = 8,000000000`, Hohlwürfel `I = 80/3`; Rumpf gegen
  unabhängige Fein-Unterteilung auf 6e-5
- Teileliste jetzt physikalisch ehrlich: Schale für Schale (Rumpf, Ruder, Mast, Boom,
  Segel), Massivkörper nur für Ballast (Kiel Stahl 178,5 kg, Bulb Blei 128,7 kg)

## 3. Schema-Reform der Eingabeschicht

- **Zwei Dateien:** `konfigurationen/materialien.json` (Stoffdaten inkl. Wasser-Block) +
  `konfigurationen/koerper.json` (Hierarchie + Darstellung); Vorlagen in `doc/`
- **Ein Kanal pro Größe:** `material` Pflicht (Name aus Tabelle **oder** direkte Dichte als
  Zahl), optional `wanddicke_m` ⇒ Schale mit `fm = rho*t`; jeder andere Massenschlüssel
  ist Validierungsfehler. Doppeleinträge per Konstruktion unmöglich.
- Lade-Protokoll je Teil (`mast: SCHALE rho=2700 * t=0.002 = 5.400 kg/m^2`)
  + 40-%-Plausibilitäts-Warnung (hätte den Vollkörper-Rumpf sofort gemeldet)
- Migrations-Gegenprobe: identische Bootswerte über beide Schemata (459,4368 kg)

## 4. Overlays (Schritt 3) und Fixes

- Taste 5: weiße Masseschwerpunkt-Marker; Taste 6: Hauptachsen (gold/cyan/magenta),
  körpergerechte Längen, Mitrotation; Layer-Registry global (P5a)
- Messung: near-vertikale Hauptachse real **21,6° vom Mast gekippt**
  (`I_xz = -11,0`, Fast-Entartung `I_xx ≈ I_zz`) – kein Fehler, sondern Rumpf-Asymmetrie;
  Segel tragen nur +0,7 davon (Leave-one-out belegt)
- Fix Sichtbarkeit: `SetVisibility` statt `remove_actor`-only (Tasten 1–3 froren nur ein)
- Fix `_gesichter`: Merge-Verlust der Hilfsfunktion wiederhergestellt (App-Start-Crash)

## 5. Aufräumen & Quick-Wins

- Gelöscht: `LIESMICH_V3.txt`, `konfigurationen/konfiguration.json`, leeres
  `segelphysik/__init__.py`, `doc/configuration_template.json`,
  `doc/LIESMICH_V4_Schritt2_Patches.txt` (byteidentisches Duplikat)
- NumPy-DeprecationWarning behoben (`np.cross` auf 2D → Determinante, ~80 Warnungen/Lauf weg)
- Smoke-Test `test_demo_importierbar` ergänzt
- `.gitignore` um `.pytest_cache/` ergänzt

## 6. Testabdeckung (Blöcke A–H)

A Loader/Zwei-Dateien-Schema · B Körper/Massen analytisch (inkl. B9/B10 Schalentensor) ·
C Komposition (flach ≡ gruppiert, TC-C5) · D Boot-Referenzen unabhängig nachgerechnet
(D3/D5 Hohlprofil-Stand) · E Farben (ΔL = 0,4) · F Duplikate · G Overlays · H Schema-Reform

## 7. Offene Punkte / Nächste Schritte

1. **P5c – Physik:** statischer Solver zuerst (Tauchgang + Krängung als Gleichgewicht,
   über `wasser_schnitt.py`), dann Echtzeit-Integration; eine Kraftfunktion, zwei Treiber
2. **Schritt 4 – Grafik:** K3 Materialglanz, K4 Tube-Overlays
3. **Konfigurator (P6):** gemerkt, nicht gemacht
4. Kleinigkeiten: SSAO bleibt Experimental-Option (flackert auf dieser GPU grundsätzlich);
   Spec-Nachtrag „Modelle `modelle/<bootname>/<name>.obj`" formalisieren

## 8. Wichtige Lektionen des Tages

- **R5 bewährt:** Jede Zahl im Test analytisch herleiten oder messen – zwei meiner
  Prüfstände hatten selbst Fehler (Windung, Tetraeder-Schwerpunkt), nicht das Modul
- **Vergessene Wanddicke ist die gefährlichste Eingabe-Fehlerklasse** (stiller
  Vollkörper-Rumpf) → Protokoll + Plausibilitäts-Warnung als Antwort
- **Patch-Zips ohne committeten Basis-Stand sind gefährdet** (Overlay-Verdrängung durch
  Schema-Reform-Demo) → erst committen, dann weiterschichten
