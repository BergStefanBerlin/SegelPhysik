# SegelPhysik – Umsetzungsplan vF1 Reste (Weg zu vF2)

Dieser Plan sammelt alle Punkte aus [Umsetzungsplan_vF1](./Umsetzungsplan_vF1.md),
[Umsetzungsplan_vF1.2](./Umsetzungsplan_vF1.2.md) und
[Backlog_v1](../Backlog/Backlog_v1.md), die bis zur Version vF2 noch offen sind.
Er ist ein Entwurf zur Abstimmung. Eine vF2-Spezifikation existiert noch
nicht; Abschnitt 6 benennt die Entscheidungen, die vorab zu treffen sind.

Stand: Phasen 0–3 sowie 5–7 sind umgesetzt; Phase 4 ist bis auf das
Genauigkeitsgate der Voxelpfade und die Arbeitslastbewertung umgesetzt.
375 Tests bestehen. Die Gesamtabnahme (Phase 8) ist nur teilweise erfolgt.
Wichtig: Der Produktionspfad `exakt_union` erreicht im Echtzeitbetrieb nur
etwa 0,43 simulierte s je Wand-s (vier Schritte à 0,004 s in median 37,24 ms,
B-08) und verfehlt damit das Durchsatzgate 1,0x deutlich. Die Arbeitsregeln aus vF1 Abschnitt 1
gelten unverändert (GUI 1:1 erhalten, kein stilles Überspringen, kein Commit
oder Push ohne Auftrag).

## 0. Leitprinzip (Nutzervorgabe 15.10.2026)

SegelPhysik ist kein Werkzeug zur Ermittlung technischer Werte, sondern stellt
Wirkprinzipien einfach dar. Daraus folgt die Rangordnung:

1. **Flüssiges, bedienbares Verhalten steht über allem** (Bildrate,
   Eingabereaktion, Echtzeit-Durchsatz ohne wachsenden Rückstand).
2. **Genauigkeit ist wichtig, aber nachrangig:** Sie muss ausreichen, damit
   die dargestellten Wirkprinzipien (Auftrieb, Aufrichtmoment, Eintauchen,
   Stabilität) qualitativ korrekt und konsistent erscheinen.
3. **Physikalische Korrektheit bleibt Pflicht:** Keine Rechenabkürzung darf
   Vorzeichen, Gleichgewichtslagen oder Stabilität falsch darstellen und
   keinen Erfolg vortäuschen.

Folgen für diesen Plan:
- R-5 (Durchsatz) und R-3/R-4a (Flüssigkeit messen) haben Vorrang vor R-2
  (Genauigkeit).
- Das 1-%-Genauigkeitsgate aus Spezifikation vF1.2 wird für den
  interaktiven Pfad **nicht automatisch fallengelassen**. Eine Lockerung
  (z. B. größere Toleranz für Echtzeit-Visualisierung bei erhaltener
  Gleichgewichts- und Stabilitätslage) ist eine Spezifikationsänderung und
  wird vor der Umsetzung ausdrücklich vereinbart (Abschnitt 6, Punkt 3).
- Die Genauigkeitsreferenz `exakt_union` bleibt für Tests und
  Solver-Vergleiche erhalten; der interaktive Pfad darf davon abweichen,
  sofern die vereinbarte Toleranz gilt.

## 1. Übersicht

| ID | Paket | Quelle | Priorität | Abhängigkeit |
|---|---|---|---|---|
| R-1 | Anzeige instabiler/nicht konvergierter Solver-Kandidaten | Nutzerbeobachtung (Rumpf ohne Kiel) | hoch | keine |
| R-2 | Genauigkeit der Voxelpfade (1-%-Gate) | B-10, B-03, vF1 Phase 4 | hoch | keine |
| R-3 | Präsentationszeitpunkt, FPS und Eingabelatenz messbar machen | B-11 | hoch | keine |
| R-4 | Zehnminütige Live-Abnahme auf Zielhardware: R-4a CPU, R-4b GPU | B-11, B-08, vF1 Phase 8 | hoch | R-3; R-4b zusätzlich R-2 |
| R-5 | Echtzeit-Durchsatz (aktuell ca. 0,43x) und Nachholmodus optimieren | B-08 | hoch | R-4a (Messung), vorab Profiling |
| R-6 | Solver-Auswertungen, Warmstart, adaptive Kennfelder | B-12, B-03 | niedrig | R-2, Profiling-Nachweis |
| R-7 | Raster-/Geometriecache über Laufzeitänderungen | B-07 | mittel | R-2 |
| R-8 | GPU-Freigabe (nur bei erfülltem Gate) | B-10, vF1 Phase 8 | mittel | R-2, R-4b |
| R-9 | Realer Windows-Start und GUI-Regression dokumentieren | vF1 Phase 0/8 | mittel | keine |
| R-10 | Kraftmodule mit belegten Koeffizienten aktivieren | vF1 Phase 6 | niedrig | fachliche Daten |
| R-11 | Restabnahme und Release vF2 | vF1 Phase 8 | – | alle freizugebenden |

## 2. Pakete im Einzelnen

### R-1 – Instabile Solver-Kandidaten anzeigen

- **Problem:** Bei `SolverFehler` (z. B. yacht1 ohne Kielsystem, Kandidat
  z≈0,6965 m, instabil) ruft `hauptfenster.py` `statische_pose_loeschen` auf.
  Der Körper bleibt in der Ausgangslage und wirkt „zu tief eingetaucht“.
- **Code:** `_statische_aufgabe_abgeschlossen` in `hauptfenster.py` löscht bei
  jedem Fehler die Pose; `SolverFehler.diagnose` enthält bereits `z`, `phi`,
  Restkraft und Restmoment und wird nur im Statustext angezeigt.
- **Umsetzung:** Bei den Status `instabile_lage`, `stagnation` und
  `budget_erschoepft` die letzte endliche Kandidatenpose aus `diagnose`
  anzeigen und in den bestehenden Statusflächen eindeutig als „instabil“ bzw.
  „nicht konvergiert“ kennzeichnen. Bei `ungueltige_rechenergebnisse` und
  fehlenden Diagnosewerten bleibt die Pose gelöscht. Kein Eintrag in
  `_statische_ergebnisse`, keine Kraftbild-Daten als Erfolg, keine neuen
  Steuerelemente.
- **Entscheidung nötig:** Darstellung nur der Pose mit Textkennzeichnung oder
  zusätzlich Farbhinweis in der vorhandenen Statuszeile.
- **Tests:** `tests/test_gui_steuerung.py`, `tests/test_statisch_robust.py`
  (Kandidat bleibt erhalten, Status ≠ stabil, Pose wird gesetzt).
- **Abnahme:** Rumpf ohne Kiel zeigt die Kandidatenlage und den Status
  „instabil“; stabile Fälle bleiben unverändert.

### R-2 – Genauigkeit der Voxelpfade

- **Problem:** Beide Voxelpfade verfehlen gegen `exakt_union` das 1-%-Gate
  (max. ca. 5,99 % bei Volumen/Kraft; Moment 0,96 %).
- **Umsetzung:** Ursachen der Randzellen-Fehler an der Wasserfläche
  analysieren (Teilzellen-Volumen, Zellschwerpunkt). Verfahren zur
  Randkorrektur prüfen (z. B. anteilige Zellfüllung statt Zentrumstest) und
  gegen `exakt_union` auf allen Abnahmeposen messen.
- **Abnahme:** Maßgeblich ist das Gate der Spezifikation vF1.2 (Volumen,
  Kraft und übrige Ergebnisgrößen höchstens 1 % relative Abweichung gegen
  `exakt_union`, über alle Pflichtposen). Die Phase-4-Grenzen aus vF1
  (0,5 % des Gesamtvolumens, Schwerpunkt ≤ 0,005 m) gelten zusätzlich für den
  CPU-Referenzpfad bei der Abnahmerasterweite 0,025 m; sie sind bereits
  nachgewiesen. CPU/GPU-Schranken aus vF1 Phase 2 bleiben erfüllt.
- **Tests:** `tests/test_voxelmodell.py`, `tests/test_auftrieb.py`,
  `tests/test_physik_backend.py`; Benchmark `werkzeuge/benchmark_physik.py`.
- **Risiko:** Feineres Raster erhöht die Vorbereitungszeit stark (0,0125 m:
  ca. 58 s). Korrekturverfahren ist daher gegenüber Verfeinerung zu
  bevorzugen.

### R-3 – Präsentationszeitpunkt messbar machen

- **Problem:** FPS und Eingabelatenz sind `null`, weil QtInteractor keinen
  belastbaren Präsentationszeitpunkt liefert.
- **Umsetzung:** Verfahren prüfen, das einen echten Präsentationszeitpunkt
  liefert (z. B. VTK-Render-Endereignis mit erzwungenem Frame-Abschluss,
  validierte externe Messmethode wie Bildschirmaufnahme mit Zeitstempel).
  Der Benchmark liefert bisher `tatsaechlich_praesentierte_fps = null`.
- **Wichtig:** Laut vF1.2-Plan ist die Baseline ohne belastbaren
  Präsentationszeitpunkt für das FPS-/Latenzgate ungültig. Gerenderte
  Frames je Wandsekunde sind kein Ersatz. Findet sich keine Methode, bleibt
  das GUI-Gate offen und die Freigabe des interaktiven Pfads blockiert; das
  ist ausdrücklich zu dokumentieren und mit dem Nutzer zu entscheiden.
- **Abnahme:** `werkzeuge/benchmark_gui_live.py` liefert belastbare Werte
  (FPS ≥ 30, Eingabereaktion p95 ≤ 100 ms).

### R-4 – Zehnminütige Live-Abnahme

- **Umsetzung:** Lauf mit Pflicht-Layern auf Zielhardware (Ryzen 5 8600G,
  Radeon 760M, 32 GB RAM): 30 s Warm-up, 10 min Messung. R-4a mit CPU-Pfad
  `exakt_union` (nach R-3); R-4b mit GPU-Pfad erst, wenn R-2 die
  Genauigkeit nachweist. Sekündliche Rückstandszeitreihe, Reaktionszeit,
  Initialisierung, Berechnungsdauer, Speicher-/Transferkosten getrennt
  berichten.
- **Gates (vF1.2-Plan 12.2):** FPS ≥ 30, Eingabereaktion p95 ≤ 100 ms,
  stationärer Physikdurchsatz ≥ 1,0x, Nachholrate ≥ 1,25x, Rückstand
  p95 ≤ 100 ms, Rückstandszunahme ≤ 50 ms (Regression über die letzten
  fünf Minuten). Jede automatische Überlastpause im Lauf ist ein
  fehlgeschlagenes Gate; Messbedingungen dürfen nicht nachträglich geändert
  werden.
- **Erwartung:** Mit `exakt_union` (ca. 0,43x) wird R-4a voraussichtlich
  fehlschlagen; das Ergebnis wird ehrlich dokumentiert und löst R-5 aus.
- **Abnahme:** Bericht in `doc/` mit Messbedingungen. Die Nutzerbewertung
  „ausreichende Rechengeschwindigkeit“ bleibt dokumentiert, ersetzt aber das
  Gate nicht.

### R-5 – Echtzeit-Durchsatz

- **Ausgangswerte:** Produktionspfad `exakt_union`: ca. 0,43 simulierte s je
  Wand-s (vier Schritte in median 37,24 ms, P95 50,78 ms; Rückstand wuchs in
  10 s auf ca. 7,47 s). Zum Vergleich der GPU-Smoke (`voxel_opencl`, nicht
  Produktionspfad, keine Abnahme): ca. 0,846 und Rückstand 0,185 s.
- **Umsetzung:** Zuerst profilieren (Hydrostatik/Union, Wasserlinienschnitt,
  Actor-Update, Prozessübergabe). Optionen: Optimierung der exakten Union,
  genauere Voxel-/GPU-Variante nach R-2, Umstellung des Produktionspfads nur
  nach ausdrücklicher Entscheidung. Ein Hydrostatik-Cache mit
  Vier-Schritt-Intervall wurde bereits verworfen (Momentfehler bis 9,95 N·m).
  Zeitsemantik (fester SI-Schritt, keine verworfene Zeit außer durch die
  dokumentierte Überlastpause) bleibt.
- **Abnahme:** Stationär ≥ 1,0x und Nachholrate ≥ 1,25x unter der
  Abnahmelast, Rückstand p95 ≤ 100 ms (siehe R-4), ohne Überlastpause.

### R-6 – Solver-Auswertungen und Kennfelder

- **Stand:** Ein auf einen Solve-Aufruf beschränkter Cache (512 Resultate)
  existiert; Yacht-`exakt_union`-Solverlauf ca. 138 ms (15 Auswertungen,
  8 Cachetreffer). Ein Vorher-nachher-Vergleich fehlt.
- **Umsetzung:** Erst Profiling der Eingangsableitungen, dann
  mathematisch begründeter Warmstart/Jacobi-Startwert. Adaptive Kennfelder
  (Hydrostatik als Funktion von z, φ) nur, wenn das Profiling den Engpass
  belegt und R-2 gültige Referenzdaten sowie einen sicheren Fallback
  ermöglicht.
- **Abnahme:** Gleichgewichtslagen stimmen mit direktem Solver innerhalb der
  Toleranz überein; Anzahl der Auswertungen je Solverlauf sinkt messbar.
- **Risiko:** Kennfeldfehler dürfen keine falsche Stabilität vortäuschen.

### R-7 – Raster- und Geometriecache

- **Umsetzung:** Cache-Invalidierung bei Modell-, Material-, Auflösungs- und
  Konfliktkorrekturänderung verwalten; Lebensdauer über Laufzeitänderungen
  klären (B-07). Sitzungsgebundene Materialänderungen schreiben weiterhin
  keine JSON.
- **Tests:** `tests/test_voxelmodell.py`, `tests/test_gui_laufzeit_edit.py`.

### R-8 – GPU-Freigabe

- **Voraussetzung:** R-2 (Genauigkeit) und R-4 (Live-Messung).
- **Stand:** OpenCL-Kernel läuft, p95-Verbesserung im Median 79,3 %
  (Bootstrap-KI 77,3–82,8 %), CPU-Fallback getestet. Freigabe aber gesperrt,
  solange das Genauigkeitsgate verfehlt ist.
- **Abnahme:** Gate laut vF1 Phase 8 („tatsächlicher Kernel gelaufen und
  Grenzwerte eingehalten“); Umstellung von
  `_ECHTZEIT_HYDROSTATIK_PFAD = "exakt_union"` nur nach ausdrücklicher
  Entscheidung. Kein leistungsabhängiger Laufzeitwechsel.

### R-9 – Windows-Start und GUI-Regression

- **Umsetzung:** Realen Start (`python -m segelphysik.gui.app`) mit
  eingebettetem QtInteractor dokumentiert prüfen: Layer, Kamera-Presets,
  Hintergründe, Beleuchtung, Wasseroberfläche, Wasseroptik, SSAO, Docks,
  Körperbaum, Simulationssteuerung, Materialänderungen (JSON unverändert,
  keine Neuberechnung). Offscreen-Regression bleibt Teil der Suite.

### R-10 – Kraftmodule

- Widerstand, Fluidgeschwindigkeit und Added Mass sind implementiert, aber
  deaktiviert. Aktivierung nur mit fachlich belegten Koeffizienten in einer
  validierten Konfiguration; keine erfundenen Werte, kein stilles Ersetzen
  durch Standardwerte. Ohne Fachdaten bleibt das Paket zurückgestellt.

### R-11 – Restabnahme und Release

- `pytest` vollständig, `pip check`, `git diff --check`, Vorher-/Nachher-
  Prüfung der Modellquellen und JSON-Konfigurationen.
- Backlog aktualisieren: erledigte Einträge mit Datum und Ergebnis, offene
  begründet weiterführen.
- Versionierung nach Vereinbarung: Commit erhöht die dritte Stelle, Push die
  zweite (dritte auf 0). Push nur nach ausdrücklicher Bestätigung.

## 3. Empfohlene Reihenfolge

Gemäß Leitprinzip (Abschnitt 0) zuerst Flüssigkeit, dann Genauigkeit:

1. **R-5** Profiling des Echtzeitpfads (Engpässe bei ca. 0,43x) und
   **R-3** (Messbarkeit von FPS/Latenz) parallel.
2. **R-5** Optimierung bzw. Pfadentscheidung (Abschnitt 6, Punkt 3), danach
   **R-4a** (CPU-Live-Abnahme).
3. **R-1** (klein, sichtbarer Nutzen) und **R-9** (Basis sichern) jederzeit
   zwischendurch.
4. **R-2** (Genauigkeit) im Rahmen der vereinbarten Toleranz; Voraussetzung
   für **R-7**, **R-6** (bei Bedarf) und **R-4b** → **R-8** (GPU).
6. **R-10** bei Vorliegen fachlicher Daten.
7. **R-11** Gesamtabnahme.

## 4. Zwischenabnahmen

Nach jedem Paket: gezielte Tests, vollständige Suite, GUI-Regression
(Offscreen), Backlog-Eintrag. Neu gefundene, nicht sofort umsetzbare Punkte
kommen in [`../Backlog/Backlog_v1.md`](../Backlog/Backlog_v1.md).

**Genauigkeitsbericht (Nutzervorgabe 15.10.2026):** Am Ende jedes Pakets, das
Hydrostatik, Solver oder Rechenpfade berührt, und im Abschlussbericht von R-11
wird die erreichte Genauigkeit ausdrücklich zurückgemeldet: max. relative
Abweichung von Volumen, Kraft und Moment sowie Schwerpunktfehler (m) des
interaktiven Pfads gegen `exakt_union` über die Pflichtposen, jeweils mit
Pfad, Rasterweite und Messbedingungen. Die Auswertung der Toleranzfrage
(Abschnitt 6, Punkt 3) erfolgt anschließend gemeinsam mit dem Nutzer.

**Erreichte Genauigkeit (Abschlussstand 15.10.2026):**

| Pfad | Volumen | Kraft | Moment | Schwerpunkt |
|---|---|---|---|---|
| Produktion `exakt_union` (Referenz) | 0 | 0 | 0 | 0 m |
| Neuer exakter Ebenenschnitt vs. bisheriger Manifold-Pfad (300 Zufallsebenen, 4298 Dreiecke) | ≤ 3,8e-11 m³ absolut | – | – | ≤ 5,3e-11 m |
| Voxel/GPU (zurückgestellt, nicht produktiv) | bis ca. 5,99 % | bis ca. 5,99 % | 0,96 % | nicht neu gemessen |

Der Produktionspfad ist die Referenz selbst; die Voxelwerte stammen aus den
früheren Messungen (Backlog B-03/B-10) und werden nicht verwendet.
## 5. Ausdrücklich nicht Teil dieses Plans

- Änderungen an GUI-Anordnung, Beschriftungen und allgemeinen Bedienelementen.
- Suche nach allen stabilen Gleichgewichtslagen.
- Automatischer, leistungsabhängiger CPU/GPU-Wechsel zur Laufzeit.
- Widerstands-/Added-Mass-Koeffizienten ohne fachliche Grundlage.
- Commit, Tag oder Push ohne ausdrücklichen Auftrag.

## 6. Offene Entscheidungen für vF2

1. **Umfang vF2:** Nur die obigen Reste, oder zusätzlich neue Funktionen
   (z. B. Segel-/Windkräfte, Seegang, Kielhydrodynamik)? Dafür wäre eine
   eigene Spezifikation vF2 nötig.
2. **R-1:** Form der Instabil-Kennzeichnung.
3. **R-2/R-5/R-8 (Leitprinzip):** Welche Genauigkeitstoleranz genügt dem
   interaktiven Pfad (statt 1 %), und darf der Produktionspfad dafür auf
   Voxel/GPU umgestellt werden, wenn Flüssigkeit sonst nicht erreichbar ist?
   Stabilitäts- und Gleichgewichtsaussagen bleiben dabei Pflicht.
4. **R-10:** Gibt es belegte Koeffizienten, oder bleibt das Paket
   zurückgestellt?

## 7. Umsetzungsstand (15.10.2026)

| Paket | Stand |
|---|---|
| R-5 | erledigt: `exakt_union` 0,43x → 1,0x (Commit 0.1.16) |
| R-3 | erledigt: Präsentierte FPS und Eingabelatenz messbar |
| R-4a | **bestanden** (inkl. Nachholrate 4,4–4,8x), siehe `Abnahme_R-4a.md` |
| R-1 | erledigt: Kandidatenpose bei `instabile_lage`, `stagnation`, `budget_erschoepft` |
| R-9 | erledigt: Windows-Start mit sichtbarem Fenster, 10-min-Lauf ohne Fehler, 384 Tests |
| R-2, R-7, R-6, R-4b, R-8 | **zurückgestellt** (Nutzerentscheidung 15.10.2026), Backlog B-13 |
| R-10 | **zurückgestellt**, keine belegten Koeffizienten (B-13) |
| R-11 | in Arbeit |
