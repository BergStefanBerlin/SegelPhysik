# UMSETZUNGSPLAN V4 – Körper-Klasse & Architektur

Status: VERBINDLICH · Grundlage: doc/Spezifikation_v4.md (Fassung 11.10.2026, mit
Text-Überarbeitungsdurchlauf) · Datum: 11.10.2026

Dieser Plan setzt die in der Spec V4 getroffenen Entscheidungen (P1–P7,
R1–R6) in vier Schritten um (Reihenfolge gemäß Spec R3). Additivprinzip:
Der Altbestand bleibt unberührt; alle neuen Dateien kommen neu hinzu.

---

## Schritt 0 – Vorbereitung (vor Schritt 1)

| Nr | Aufgabe | Ergebnis |
|---|---|---|
| 0.1 | Arbeitsdatei erzeugen: `konfiguration.json` aus `doc/configuration_template.json` kopieren (Template-Muster, Spec J) | Datei im Projekt-Root |
| 0.2 | Loader `core/konfig_lader.py` anlegen: liest AUSSCHLIESSLICH `konfiguration.json`; Doppelschlüssel-Erkennung Pflicht (`object_pairs_hook`, Spec J); fehlende Datei → klarer Fehler mit Hinweis auf die Vorlage | Modul + Tests |
| 0.3 | Rekursive Validierung des teile-Baums (Gruppe/Blatt-Regeln, Genau-eins-Regel, leere Gruppe → Fehler); Praxisbeispiele aus der Vorlage: Gruppen `kielsystem` und `rigg` | Validierer + Tests |

**Abnahmekriterium Schritt 0:** Lader-Tests grün; Verstoßfälle (Doppelschlüssel,
fehlender Schlüssel, Gruppe mit Masse, Blatt ohne Massengröße) werfen Fehler.

---

## Schritt 1 – Körper-Klasse + Massenintegration (Kern von V4)

Neue Dateien (Spec R4):

| Datei | Inhalt |
|---|---|
| `core/massen.py` | Divergenzsatz-Volumen, Flächeninhalt, Schwerpunkt, Trägheitstensor – rein numpy, exakt testbar |
| `core/koerper.py` | Klasse `Koerper`: Form, genau-eins-Massen-Input (masse/dichte/material/flaechenmasse), Farbe (P4), Teile-Liste (P2), automatische r_S/I_S-Berechnung (P1), Pose in Welt (A1) |
| Fabrik-Funktionen | dünne Erzeuger für Quader, Kegel, Pyramide, Boot (aus OBJ + konfiguration.json) |
| `tests/test_koerper.py` | Testfälle gemäß doc/Testfaelle_v4.md |

Regeln, die im Code sichtbar werden müssen:
- Schwerpunktframe als einziges System (P1): nach Erzeugung sind ALLE Punkte um −r_S verschoben; Konstruktionskoordinaten existieren nur intern.
- Rekursion (P2): jede Tiefe identisch; Teil-Tensoren werden vor der Summation mit der rel_Pose rotiert (P1).
- Genau-eins-Regel (P3): Validierungsfehler bei 0 oder ≥2 Massengrößen; Segel (volumenlos) nur über flaechenmasse; reine Gruppen ohne Massen-Parameter (P2.5).
- Farben (P4): farbe + optionale farbe_unter_wasser; Default-Aufhellung ΔL = +0,25 aus konfiguration.json.
- SI-Einheiten (R6): keine Umrechnung im Kern.

Umstellung der vier bekannten Körper (Kegel, Quader, Pyramide, Boot) auf die
Klasse; demo_app/steuerung nutzen weiterhin die Brücke.

**Abnahmekriterium Schritt 1:** Alle Tests aus doc/Testfaelle_v4.md grün UND die
bestehende Regression (22 Tests) bleibt grün UND die Darstellung ist visuell
unverändert (K5″-Prinzip: nichts Neues sichtbar).

---

## Schritt 2 – Grafik-Optimierung K1 + K2 + K5 (Spec P7)

| Nr | Aufgabe | Hinweis |
|---|---|---|
| 2.1 | Studio-Beleuchtung (Key/Fill/Rim) + SSAO | PyVista-eingebaut |
| 2.2 | Hintergrundverlauf (Himmelblau → Dunstweiß) | statt reinem Weiß |
| 2.3 | Wasser: Fresnel-Glanz + kalibrierte Tiefenfärbung | Deko, dokumentiert; KEINE Wellen (Spec-Grenze) |
| 2.4 | Kamera-Presets per Tastendruck (Bug/Heck/3⁄4/Draufsicht) + sanfter Übergang | neue Tasten, dokumentieren |
| 2.5 | Zweiton-Färbung über P4-Farben der Klasse | ersetzt fest verdrahtete Blau/Rot-Logik |

Alles additiv in der Brücke; vista.py bleibt byteidentisch (Einstellungen
werden von außen gesetzt).

**Abnahmekriterium Schritt 2:** Visuelle Abnahme durch den Nutzer (Screenshot);
60 FPS mit 4+ Körpern weiterhin erreicht; keine physik-suggerierende Deko.

---

## Schritt 3 – Overlays (r_S, Hauptachsen) gemäß P5a/P5b

| Nr | Aufgabe |
|---|---|
| 3.1 | Layer-Registry (global, nicht pro Körper; Körper kennt keine Layer) |
| 3.2 | Layer „schwerpunkt": Marker am r_S (Pose-transformiert) |
| 3.3 | Layer „hauptachsen": drei Linien durch r_S aus den Eigenvektoren von I_S |
| 3.4 | Tasten zum Ein-/Ausschalten der Layer (z. B. Taste 5/6) |

**Abnahmekriterium Schritt 3:** Bei symmetrischen Körpern fallen die
Hauptachsen nahezu mit den Konstruktionsachsen zusammen (numerisch geprüft);
am asymmetrischen Rumpf sind sie sichtbar verschieden. Layer schalten
unabhängig und betreffen alle Körper gleichzeitig.

---

## Schritt 4 – Materialglanz K3 + Tube-Overlays K4 (gemäß P7 NACH Schritt 3)

Glanzgrade pro Material (Anknüpfung an Materialtabelle P3), Tube-Rendering für
Overlay-Linien, Farbkonvention (Kräfte rot, Achsen Gelb/Cyan, Schwerpunkt weiß).

**Abnahmekriterium Schritt 4:** Visuelle Abnahme; Overlays aus Schritt 3
nutzen Tubes; Physik-Darstellung bleibt unverändert ehrlich (keine Kräfte
vor V4 – P5b).

---

## Bewusst NICHT in diesem Plan (Spec-begründet)

- **Physik / Zwei-Modi (P5c):** Zielbild festgelegt, Umsetzung ausdrücklich
  später (Nutzer-Beschluss 11.10.). Die Architektur (eine Kraftfunktion,
  zwei Treiber; Solver nutzt wasser_schnitt) ist ab Schritt 1 eingehalten.
- **Konfigurator (P6):** nur gemerkt; Vorläufer ist konfiguration.json.
- **Muster/Texturen (P4.4):** bewusst nicht vorgesehen.

## Meilensteine / Git-Checkpoints

Nach jedem Schritt: Commit mit Tests-Status in der Nachricht. Tags empfohlen:
`v4.0-schritt1`, `v4.0-schritt2`, `v4.0-schritt3`, `v4.0-schritt4`.
