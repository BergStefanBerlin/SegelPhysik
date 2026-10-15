# Optimierungs-Backlog v1

Dieses Backlog sammelt Optimierungskandidaten und Leistungsbefunde aus der
Entwicklung. Ein Eintrag ist kein Auftrag, die Physik, die Bedienung oder die
Abnahmekriterien ungeprüft zu ändern. Vor einer Umsetzung sind Nutzen,
Messbarkeit und Regressionen zu prüfen.

## Erfasste Kandidaten

### B-01 – Statische Berechnung von der GUI-Ereignisschleife entkoppeln

- **Priorität:** Hoch
- **Status:** Umsetzung und GUI-Reaktionsmessung erfolgt
- **Befund:** Der statische Solver und die Echtzeit-Physik laufen nun in
  Hintergrundaufgaben. Künstlich blockierende GUI-Regressionen prüfen, dass
  Qt-Ereignisse weiterlaufen und veraltete Solverergebnisse nicht angewendet
  werden. Unter echter Yacht-Voxelarbeit kehrte der Echtzeit-Takt in
  `0,095 ms` zurück; ein GUI-Ereignis wurde nach `16,4 ms` verarbeitet.
  Der globale Voxelpfad hatte zuvor im vollständigen Solverlauf `190,69 s`
  benötigt.
- **Restarbeit:** Fortschrittsanzeige oder expliziter Solverabbruch bleiben
  ungeprüft und benötigen eine gesonderte UX-Entscheidung. Ergebnisse werden
  bereits ausschließlich im GUI-Thread angewendet.
- **Abnahme:** Ereignis-Richtwert `100 ms` in der dokumentierten Lastprobe
  eingehalten. Künstlich blockierender Solver, sichere GUI-Thread-
  Poseaktualisierung und Verwerfen eines nach Moduswechsel veralteten
  Ergebnisses regressionsgeprüft.

### B-02 – Globalen Voxelpfad und Solver-Arbeitslast profilieren

- **Priorität:** Hoch
- **Status:** Profiling abgeschlossen; als interaktiver Standard abgelehnt
- **Befund:** Im Yacht-Solververgleich bei `0,025 m` wurden 152
  Kraftauswertungen benötigt und der globale Pfad brauchte 190,69 s. Die
  wiederholbare F1a-Messung bei `0,05 m` ergab für Yachtposen `0,306 s`
  Median und `0,475 s` P95; der Solver brauchte `94,33 s`. Die Posewerte
  überschritten mit bis zu `2,20 %` Momentabweichung das F1a-Budget.
- **Ergebnis:** Die besonders teure Mesh-/Wasserlinienarbeit wurde für die
  Darstellung vektorisiert und Renderer-Actors werden wiederverwendet. Das
  beschleunigt die GUI, ändert aber nicht die Ablehnung des globalen
  Voxelkraftpfads.
- **Später prüfen:** Den Voxel-Kraftpfad nur nach einer getrennten,
  messbaren Beschleunigung erneut erwägen; Referenz, Semantik und
  Genauigkeitsgrenzen erhalten.

### B-03 – Körperfestes Raster schneller vorbereiten und korrekt in den
Solver integrieren

- **Priorität:** Hoch
- **Status:** Offen – Genauigkeitslücke beim Solvergleichgewicht
- **Befund:** Bei `0,025 m` speichert das Yacht-Raster rund 202.704
  Voxelzentren. Die Vorbereitung lag in wiederholten Läufen bei etwa
  14,6–17,8 s; neun Poseauswertungen dauerten etwa 0,018–0,020 s. Der Solver
  inklusive Vorbereitung war deutlich schneller als der globale Voxelpfad
  (etwa 18,06 s statt 190,69 s), fand aber eine um rund `3,78°` abweichende
  Rollage. Am exakten Union-Gleichgewicht lag der Schwerpunktfehler über der
  damaligen Grenze von `0,005 m`. Im F1a-Vergleich bei `0,05 m` dauerte die
  Vorbereitung `4,01 s` und eine Pose `0,66 ms`; trotz `0,29 %`
  Volumenabweichung lagen Auftrieb um `1,96 %` und Moment um `4,20 %`
  daneben. Damit besteht dieser Pfad das gelockerte F1a-Budget ebenfalls
  nicht.
- **Später prüfen:** Rastererzeugung profilieren und beschleunigen;
  Solvergleichgewicht und Momentenrest gegen `exakt_union` validieren. Keine
  Standardumstellung, solange Gleichgewichtslage, Schwerpunkt und Momente
  nicht innerhalb der geltenden Abnahmekriterien übereinstimmen.
- **Abnahme:** Phase-4-CPU-Volumenabweichung höchstens `0,5 %` des
  ungeschnittenen Gesamtvolumens, Schwerpunktabweichung höchstens `0,005 m`
  in allen Abnahmeposen sowie ausreichende Übereinstimmung der vollständigen
  Solverlösung. Die absolute CPU/GPU-Schranke aus der Spezifikation ist davon
  getrennt und bleibt unverändert.

### B-04 – Wiederholbare Benchmark-Suite für vollständige Arbeitslasten

- **Priorität:** Hoch
- **Status:** Benchmarkwerkzeug umgesetzt und ausgeführt
- **Befund:** Bisherige CPU-Messungen waren einzelne manuelle Läufe. Die
  Vergleichbarkeit litt zudem an doppelter Rastervorbereitung in einem
  Solver-Benchmark; der dokumentierte Wert wurde anschließend durch einen
  Einmal-Aufbau-Lauf korrigiert.
- **Ergebnis:** `werkzeuge/benchmark_physik.py` erfasst Plattform,
  Versionen, Geometrie, Posen, Rasterweite, getrennte Vorbereitungs-,
  Pose- und Solverzeiten, Wiederholungen sowie Genauigkeits- und
  Solverabweichungen. Drei Posewiederholungen und je ein vollständiger
  Solverlauf wurden ausgeführt; die Solverreferenz wird ausdrücklich mit
  Winkel-, Lage- und Restkraftkriterien verglichen.
- **Abnahme:** Vorbereitung und wiederholte Auswertung sind getrennt
  ausgewiesen. Genauigkeitsgrenzen erscheinen als explizites
  `genauigkeit_bestanden` statt nur als Messwert.

### B-05 – Exakte Union-Referenz bei Bedarf beschleunigen

- **Priorität:** Mittel
- **Status:** Exakter Unionpfad für Solver und Echtzeit ausgewählt
- **Befund:** `exakt_union` benötigte für neun Yachtposen ungefähr `0,22 s`
  und für den vollständigen Solverlauf ungefähr `0,83 s`. Der Pfad ist
  union-konsistent und wird mit einmalig vorbereiteter Geometrie in Solver
  und Echtzeit wiederverwendet. Die neue Yachtmessung ergab `20,8 ms`
  Vorbereitung, `8,52 ms` Median und `12,39 ms` P95 je Pose; der vollständige
  Solverlauf brauchte `225,6 ms` bei fünf Iterationen.
- **Später prüfen:** Vorbereitung und Cacheinvalidierung bei künftig
  veränderlicher Geometrie erneut profilieren; die aktuelle GUI ersetzt den
  Laufzeitkörper nach Geometrieänderung statt alte Uniondaten weiterzuverwenden.
- **Abnahme:** Referenzwerte stimmen mit analytischen und
  Booleschen Regressionstests überein; Fehler werden ausdrücklich gemeldet,
  nicht als Erfolg oder Nullvolumen kaschiert.

### B-06 – Darstellung und GPU-Nutzung separat messen

- **Priorität:** Mittel
- **Status:** Live-Yachtlauf mit exakter Physik und QtInteractor gemessen; GPU-Physik nicht aktiviert
- **Befund:** Die bisher dokumentierten Leistungswerte betreffen CPU-
  Berechnung; anschließend wurde ein realer Yacht-Actor in einem sichtbaren
  Windows-QtInteractor vermessen. Nach Vektorisierung des Wasserlinienschnitts
  und Wiederverwendung von Mesh-, Achsen- und Kräfte-Actors lief ein
  zehnsekündiger Ende-zu-Ende-Test mit aktivierten Achsen-/Kräfte-Layern bei
  `30,34 FPS`. Die Poseaktualisierung lag bei `14,50 ms` Median (`20,20 ms`
  P95), der Renderer bei `4,55 ms` Median (`6,63 ms` P95). Ein 50-ms-
  Ereignis wurde über einen separaten Thread in die Qt-Ereignisschleife
  eingereiht: `18,83 ms` P95 und `25,66 ms` maximale Dispatch-Latenz.
  Historische render-only Messungen von `40,1–49,7 FPS` sind kein Ersatz für
  diesen integrierten Lasttest.
- **Grenze:** Diese Messung belegt die CPU-gestützte Darstellung, nicht
  GPU-beschleunigte Physik. Der Physik-Rückstand wuchs im zehnsekündigen
  Live-Test auf etwa `7,47 s`; die genaue Physik rechnet langsamer als
  Wandzeit, ohne Schritte zu verwerfen. Ein GPU-Kernel wird nicht als
  Produktionspfad ausgewiesen.
- **Später prüfen:** Andere Körper, höhere Meshkomplexität, Layer/SSAO und
  längere Lastläufe ebenfalls messen; Optimierungen dürfen weder Geometrie
  noch sichtbare Darstellung stillschweigend ändern.
- **Abnahme:** Yacht-Referenzszene erfüllt `>=30 FPS` und die gemessene
  Ereignisreaktion bleibt unter `100 ms`.

### B-07 – Raster- und Geometriecache über Laufzeitänderungen verwalten

- **Priorität:** Mittel
- **Status:** Offen
- **Befund:** Ein gebundenes körperfestes Raster wird einmal erstellt und
  während Poseauswertungen wiederverwendet. Die Laufzeit-GUI kann Körper nach
  Materialänderungen neu aufbauen. Eine Integration des körperfesten Pfads
  in diesen Lebenszyklus ist noch nicht freigegeben.
- **Später prüfen:** Cache-Lebenszyklus an Geometrie- und
  Auflösungsänderungen binden; sicherstellen, dass Masse-/Materialänderungen
  Solverdaten aktualisieren, ohne unnötig unveränderte Geometrie neu zu
  rasterisieren. Keine veralteten vorbereiteten Daten weiterverwenden.
- **Abnahme:** Tests für unveränderte Geometrie, Geometrieänderung,
  Auflösungsänderung und Materialänderung belegen korrekte Invalidierung
  sowie die erwartete Zahl von Rasteraufbauten.

### B-08 – Echtzeit-Rückstand unter Last messen

- **Priorität:** Mittel
- **Status:** Zeitbilanz, automatische Pause und Nachholmodus implementiert;
  Zielhardware-Abnahme und Durchsatzoptimierung offen
- **Befund:** Die Echtzeitphysik wird jetzt außerhalb der GUI-Ereignisschleife
  in Batches mit höchstens vier festen SI-Schritten berechnet. Der zuvor
  getestete Hydrostatik-Cache mit vier-Schritt-Intervall verursachte in einer
  fünfsekündigen Yacht-Trajektorie zwar nur `0,0055 %` Volumen-/Kraftfehler,
  aber bis zu `9,95 N·m` absoluten Momentfehler (relativ sehr groß bei
  Momenten nahe null). Er wurde deshalb aus dem Echtzeitpfad entfernt;
  Hydrostatik wird jetzt bei jedem Physikschritt exakt ausgewertet.
- **Neuer Messstand:** Der exakte Pfad vergleicht in 500 Schritten über fünf
  Sekunden exakt gleich mit sich selbst (keine Cacheabweichung; maximale
  Positionsdifferenz `0 m`, Winkelabweichung numerisch unter `0,000002°`).
  Vier exakte Schritte dauerten im Live-Prozess median `37,24 ms` (P95
  `50,78 ms`) für `0,016 s` Simulationszeit. Der Rückstand wuchs im
  zehnsekündigen Test auf etwa `7,47 s`; keine
  aufgelaufene Simulationszeit wird stillschweigend verworfen.
- **Änderung vom 15.10.2026:** Angeforderte und übernommene Simulationszeit
  werden getrennt geführt; in-flight-Schritte werden beim Pausieren genau
  einmal zurückgebucht. Ein Rückstand ab `1,0 s` löst nach fünf ununterbrochenen
  Sekunden eine automatische Pause aus. Fortsetzen arbeitet zunächst mit
  priorisierten Batches den erhaltenen Rückstand ab und protokolliert
  Ein-Sekunden-Nachholraten sowie die Gesamtrate. Regressionen decken
  Rückbuchung, Nachholmodus, die exakte `1,0 s`/`5 s`-Schwelle sowie
  verspätete und bereits übernommene Workerresultate bei einem Körperwechsel
  ab; weder Rückstand noch berechnete Zeit werden doppelt gebucht.
- **Später prüfen:** Die geforderte Zielhardware-Langzeitmessung muss die
  Nachholrate von mindestens `1,25 s/s`, den Rückstand und das Verhalten bei
  Körper-/Moduswechsel über zehn Minuten nachweisen. Physikdurchsatz separat
  optimieren; Zeitbegrenzung oder Verwerfung darf nicht stillschweigend
  eingeführt werden.
- **Abnahme:** Die gezielten Zustandsregressionen bestehen. Der zehnminütige
  Zielhardwarelauf und die zugehörigen Durchsatz-/Trendgates sind noch offen.

### B-09 – Wasserlinienschnitt und Actor-Neuaufbau pro Frame

- **Priorität:** Hoch
- **Status:** Optimiert und unter integrierter Live-Last gemessen
- **Befund:** Poseprofiling zeigte vor der Änderung bei der Yacht `43 ms`
  für Wasserlinienschnitte und `39 ms` für wiederholtes `add_mesh` pro Frame;
  insgesamt waren es nur etwa `8,5 FPS`.
- **Ergebnis:** Vollständige, nicht geschnittene Dreiecke werden vektorisiert
  verarbeitet, Schnittsegmente direkt aus durchstochenen Dreiecken gewonnen
  und vorhandene Actor-Mapper auch für Achsen und Kräfte wiederverwendet.
  Exakte Schnittgeometrie-Regressionen bestehen. Die Yacht-Referenzszene
  erreicht mit exakten Physikschritten und aktiven Achsen-/Kräfte-Layern
  über zehn Sekunden `30,34 FPS`; das frühere render-only Ergebnis bleibt
  separat historisch.
- **Wiederholen:** `.venv\\Scripts\\python.exe werkzeuge\\benchmark_gui_live.py`
  startet denselben sichtbaren Test; `--duration 10` verlängert die Messung.
- **Abnahme:** Wasserliniensegmente stimmen geometrisch mit dem Mesh-Schnitt
  überein, Deckelvolumen bleibt erhalten und der integrierte Yachtlauf erreicht
  mindestens `30 FPS`. Die Physik selbst läuft weiterhin langsamer als
  Wandzeit; siehe B-08.

### B-10 – vF1.2-6-DOF-OpenCL-Hydrostatik

- **Datum:** 15.10.2026
- **Priorität:** Hoch
- **Status:** Optionaler OpenCL-Voxelreduktionskernel implementiert und
  numerisch gegen die körperfeste CPU-Referenz geprüft; Produktionsfreigabe
  nicht bestanden/nicht beantragt
- **Befund (aktualisiert am 15.10.2026):** Das GPU-Backend hält die
  körperfesten Voxelzentren resident, reduziert nasse Anzahl und
  Schwerpunktbeiträge je Workgroup und fällt bei
  Initialisierungs-/Kernelproblemen oder grenznahen Voxeln auf dieselbe
  Pose der CPU-Referenz zurück. Die vorhandene Zielhardware meldet OpenCL-GPU
  `gfx1103`; Regressionen für neutrale, Roll- und Nickpose stimmen mit dem
  CPU-Raster überein. Der gepaarte Zehn-Paar-Mikrobenchmark (je zehn
  vollständige 6-DOF-Schritte pro Backend und Paar, fünf Quaternionposen,
  alternierte Reihenfolge) ergab auf dem Yachtmodell mit `0,05 m` Raster
  `4,57 ms` CPU-P95 gegenüber `0,95 ms` GPU-P95 und einen Median der
  paarweisen P95-Verbesserung von `79,3 %` (Bootstrap-95-%-KI:
  `77,3–82,8 %`). Die GPU war damit in dieser isolierten Voxel-Arbeitslast
  schneller; das ist kein Ende-zu-Ende-/Renderlastnachweis. Die CPU-
  Rastervorbereitung dauerte `3,45 s`, GPU-Kernel-/Bufferinitialisierung
  `0,69 s`. Ein zusätzlicher Regressionstest erzwingt nun eine Pose mit
  Voxeln numerisch auf der Wasserfläche und bestätigt den CPU-Fallback.
- **Genauigkeit:** Beide Voxelvarianten stimmten im Schwerpunkt auf
  `8e-17 m` überein, verfehlten aber gegenüber `exakt_union` das 1-%-Gate
  deutlich: maximal `5,99 %` normierter Volumen- und Kraftfehler. Der
  schnelle GPU-Pfad bleibt daher gesperrt; eine
  Leistungsverbesserung heilt keinen fachlichen Fehler.
- **Restarbeit:** Der Benchmark kann nun per `--backend` denselben festen
  Hydrostatikpfad im Echtzeit-GUI-Lauf verwenden. Gepaarte, sichtbare
  CPU/GPU-Messreihen auf dem Zielsystem einschließlich Renderlast sowie
  sämtliche statischen und dynamischen Genauigkeitsvergleiche fehlen weiter.
  Die Prozessinitialisierung übernimmt dieselbe feste Zuordnung; der
  Produktionspfad bleibt `exakt_union`, bis alle Gates bestehen. GPU und
  CPU-Voxelpfad approximieren beide und verfehlen derzeit das Genauigkeitsgate.
- **Abnahme:** Alle numerischen, statischen Solver-, dynamischen Verlaufs-,
  Genauigkeits- und vollständigen p95-Konfidenzintervall-Gates aus Phase 6
  müssen bestehen, bevor eine Produktionszuordnung geändert wird.

### B-11 – vF1.2-Live-Abnahme und Präsentationszeitpunkt

- **Datum:** 15.10.2026
- **Priorität:** Hoch
- **Status:** Benchmark um Pflicht-Layer, sekündliche Rückstandszeitreihe,
  Rückstandstrend und explizite Kennzeichnung nicht messbarer Präsentation
  erweitert; gültige Live-Abnahme offen
- **Befund:** Ein aktueller kurzer Offscreen-Smoke-Test mit festem
  `voxel_opencl`-Pfad (1,2 s nach 0,2 s Warm-up) aktivierte alle vier
  Pflicht-Layer und erfasste 64 Physik-Batches. Median/P95 der Batches waren
  `3,71/5,19 ms`; die gemessenen Renderaufrufe lagen bei `30,70/s`, der
  Rückstand am Messende bei `0,185 s`. Präsentierte FPS sowie
  Eingabe-bis-sichtbar-Latenz waren `null`. Der Lauf
  ist wegen Offscreen-Betrieb, kurzer Dauer und fehlendem Präsentierungszeitpunkt
  ausdrücklich keine Abnahme. `QWidget`-/QtInteractor-Renderaufrufe belegen
  weder tatsächlich präsentierte FPS noch Eingabe-bis-sichtbar-Latenz;
  beide Abnahmewerte werden daher `null` ausgewiesen. Der Benchmark ist
  standardmäßig auf 30 s Warm-up plus zehn Minuten Messzeit gesetzt.
- **Erweiterung vom 15.10.2026:** Der Livebenchmark meldet zusätzlich
  angeforderte/berechnete Simulationszeit, Durchsatz über gesamte Wandzeit,
  Rückstand-p95/Maximum, automatische Überlastpause und eine 300-s-
  Rückstandsregression. Auch bei einem sichtbaren Qt-Fenster liefert die
  bestehende QtInteractor-Schnittstelle keinen belastbaren Präsentations-
  zeitpunkt; präsentierte FPS und Eingabe-bis-sichtbar-Latenz bleiben deshalb
  `null` und blockieren das formale GUI-Freigabegate. `--backend` erlaubt
  gezielte Läufe mit `exakt_union`, `voxel_koerperfest` oder
  `voxel_opencl`; Standard bleibt `exakt_union`.
- **Restarbeit:** Eine belastbare Zeitmarke des tatsächlich präsentierten
  Frames mit sichtbarer Eingabereaktion über Renderer-/Qt-Schnittstelle
  bereitstellen oder eine validierte externe Messmethode verwenden. Danach
  Benchmark mit sichtbarer GUI auf Zielhardware vollständig ausführen.
- **Erledigt (15.10.2026, R-3/R-4a):** Präsentationszeitpunkt = VTK-`EndEvent`
  mit `WaitForCompletion`; Eingabelatenz = simulierte Mausdrehung bis zum
  ersten Frame mit geänderter Kamera. Zehnminütiger CPU-Lauf
  (`exakt_union`, Windows-QPA, 30 s Warm-up): FPS 69,8, Frameabstand
  p95 31,6 ms, Eingabereaktion p95 4,1 ms, Durchsatz 0,9999x, Rückstand
  p95 49 ms, Trend +0,09 ms/s, keine Überlastpause, keine Fehler.
  Nicht gemessen: Nachholrate 1,25x. Bericht: `doc/Abnahme_R-4a.md`.
- **Abnahme:** Präsentierte FPS, Eingabelatenz, Pflicht-Layer, sekündliche
  Rückstandszeitreihe und Fünf-Minuten-Trend valide erfassen; alle
  Phase-0-/Phase-9-Gates bestehen.

### B-12 – Solver-Auswertungen und adaptive Kennfelder

- **Datum:** 15.10.2026
- **Priorität:** Mittel
- **Status:** Identische Residuumspunkte innerhalb eines Solverlaufs werden
  begrenzt memoisiert; Kennfeldphase nicht begonnen
- **Befund:** Der robuste Solver wertet an identischen Positionen wiederholt
  dieselbe reine Kraftfunktion aus. Ein lokaler, auf 512 Resultate begrenzter
  Cache bleibt auf einen einzigen Solve-Aufruf beschränkt und liefert
  Auswertungs-/Trefferzahlen zur Diagnose. Im wiederholten Yacht-
  `exakt_union`-Solverbenchmark (3 Läufe, `dt` und Geometrie unverändert)
  lag die Laufzeit bei `136,9–144,3 ms` (Median `138,4 ms`); pro Lauf wurden
  15 eindeutige Kraftauswertungen ausgeführt und 8 Wiederholungen aus dem
  Cache bedient. Die Solverpose und Restgrößen waren in allen drei Läufen
  identisch. Das globale Voxelverfahren benötigte weiterhin rund `47,6 s`
  je Solverlauf und verfehlte das Momentengenauigkeitsgate; es bleibt
  ungeeignet.
- **Restarbeit:** Kein belastbarer Vorher-nachher-Ende-zu-Ende-Vergleich
  wurde mit demselben Code-/Messmanifest erhoben. Profiling der
  Eingangsableitungen und ein mathematisch begründeter Warmstart/Jacobi-
  Startwert sind offen. Adaptive Kennfelder sind nach dem dokumentierten
  genauen CPU/GPU-Pfad nicht eingeführt: Voxelgenauigkeit verfehlt derzeit
  bereits das Gate, daher fehlen gültige Referenzdaten und eine sichere
  Interpolations-/Fallbackfreigabe.
- **Abnahme:** Der lokale Cache besteht Solverregressionen; eine
  messbare Beschleunigung ist noch nicht als Freigabeerfolg ausgewiesen.
  Kennfeld-/Warmstartarbeit erst fortsetzen, wenn exakte Pfade das Profiling
  als relevanten Engpass belegen und die Genauigkeitsgates erfüllbar sind.

### B-13 – Voxel-/GPU-/Cache-/Warmstart-Pfade zurückgestellt (vF2-Entscheidung)

- **Datum:** 15.10.2026
- **Priorität:** Niedrig
- **Status:** Zurückgestellt (Entscheidung Nutzer: Technologie ist Mittel zum
  Zweck; `exakt_union` genügt)
- **Betroffen:** R-2 (Voxel-Genauigkeit), R-4b (GPU-Live-Abnahme), R-6
  (Warmstart/Kennfelder), R-7 (Raster-Cache), R-8 (GPU-Freigabe), B-03, B-07,
  B-10, B-12.
- **Begründung:** `exakt_union` erreicht auf Zielhardware 1,0x Durchsatz,
  69,8 FPS, Eingabereaktion p95 4,1 ms und Nachholrate 4,4–4,8x. Voxel/GPU
  verfehlen das 1-%-Gate (Volumen/Kraft bis ca. 5,99 %).
- **Wiederaufnahme nur, wenn:** `exakt_union` auf schwächerer Hardware die
  Gates verfehlt oder deutlich größere Modelle den Durchsatz drücken.
- **R-10 (Kraftmodule):** zurückgestellt, da belegte Widerstands-/Added-Mass-
  Koeffizienten fehlen.

### B-14 – Beliebige vordefinierte Körper importieren (wie die Yacht)

- **Datum:** 15.10.2026
- **Priorität:** Mittel
- **Status:** Offen (Wunsch Nutzer)
- **Ziel:** Beliebige vordefinierte Körper aus Dateien importieren, nicht nur
  die parametrischen Formen der `koerper.json` (cone, box, pyramid, sphere,
  cylinder, plate, hexprism, polyhedron). Der Ablauf soll dem der Yacht
  entsprechen: Teile als OBJ unter `modelle/<name>/`, in der `koerper.json`
  über `teile` mit Material oder Dichte beschrieben.
- **Zu klären:** Ordnerstruktur und Skalierung, Mesh-Prüfung (geschlossen,
  orientiert, Volumen > 0), Farben/Materialien, Anzeige im Komponentenbaum.
- **Ausgangspunkt:** `fabriken.baue_summenkoerper`, `boot_bau.baue_teil`,
  `koerper_formen.FORMEN`.

## Messkontext und Grenzen

- Yachtmodell: geometrisches Unionvolumen ungefähr `3,16786 m³`.
- CPU-Messungen vom 14.10.2026: Windows x64, Python 3.14.8,
  AMD Ryzen 5 8600G mit integrierter Radeon 760M.
- Phase-4-CPU-Konvergenz: relative Volumenabweichung höchstens `0,5 %` des
  ungeschnittenen Gesamtvolumens und Schwerpunktabweichung höchstens
  `0,005 m`. Das ersetzt nicht die absoluten, separat geltenden
  CPU/GPU-Schranken der Spezifikation.
- Solverzeiten sind Einzelmessungen; sie sind keine Laufzeitgarantie.
- Der Rendering-Smoke-Test umfasst einen realen QtInteractor, den Yacht-Actor
  und eine repräsentative Posefolge; er ersetzt keine Langzeitmessung aller
  Darstellungsoptionen.
- Der Echtzeit-Physikdurchsatz bleibt niedriger als die Wandzeit. Physik-
  Rückstand wird angezeigt, nicht verworfen.
- Weiterführende Quellen: [Umsetzungsplan](./Umsetzungsplan_vF1.md),
  [Spezifikation](./Spezifikation_v1.1.md),
  [Voxelmodell](../segelphysik/core/voxelmodell.py),
  [Auftrieb](../segelphysik/core/auftrieb.py),
  [Union-Referenz](../segelphysik/core/volumen_union.py),
  [Solver](../segelphysik/core/statisch_robust.py) und
  [GUI-Hauptfenster](../segelphysik/gui/hauptfenster.py).

## Backlog pflegen

Neue Erkenntnisse als eigenen Eintrag mit Datum, Status, Messbedingungen,
Ergebnis, Abnahmekriterium und Verweis auf betroffene Tests/Dokumente
ergänzen. Überholte Befunde nicht stillschweigend entfernen, sondern mit
einem Folgeeintrag und begründeter Statusänderung nachvollziehbar ablösen.
