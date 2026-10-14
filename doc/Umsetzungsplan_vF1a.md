# SegelPhysik – Umsetzungsplan vF1a

Diese Fassung baut auf dem [Umsetzungsplan vF1](./Umsetzungsplan_vF1.md) auf.
Bereits abgeschlossene Phasen und ihre Messergebnisse bleiben historisch
unverändert. Für die noch ausstehenden Arbeiten hat eine flüssige Anzeige
Vorrang vor höherer Genauigkeit, solange die hier festgelegten Abweichungen
eingehalten werden. Die vorhandene GUI-Darstellung und Bedienung bleibt 1:1
erhalten; einzig der für erkannte Bauteilüberschneidungen erforderliche
Auswahldialog ist neu zulässig.

Für den künftig optimierten interaktiven Rechenpfad gelten gegenüber der
exakten Union-Referenz folgende Zielgrenzen: Volumenabweichung höchstens
`1 %` des Gesamtvolumens, Winkelabweichung höchstens `1°` und Abweichung
übriger physikalischer Ergebnisgrößen höchstens `1 %`. Für Referenzwerte nahe
null werden vor den Benchmarks dimensionsgerechte absolute Grenzwerte
festgelegt, damit relative Prozentwerte dort nicht undefiniert oder
irreführend sind. Die bisherige `0,5 %`-Volumengrenze wird für diesen
interaktiven Rechenpfad durch `1 %` ersetzt; frühere Messergebnisse und
Referenzpfade werden dadurch nicht nachträglich umgedeutet.

## 1. Arbeitsregeln und Abnahmeprinzip

- Vor jeder Phase werden Arbeitsbaum, Python-Version, Abhängigkeiten und
  Testergebnis festgehalten. Die vorhandenen Nutzerdaten und Modellquellen
  werden nicht durch Testläufe verändert.
- Zuerst werden die vorhandenen Implementierungen und Tests genutzt bzw.
  erweitert. Neue Abhängigkeiten und neue Modulgrenzen werden nur eingeführt,
  wenn ein konkreter Bedarf nachgewiesen ist.
- Jede Phase endet mit den unten genannten gezielten Tests und einer
  GUI-Regression. Fehler und Abweichungen werden vor dem Beginn der nächsten
  abhängigen Phase behoben oder ausdrücklich als blockierend dokumentiert.
- Physiktests verwenden SI-Einheiten und analytische oder exakte
  Referenzgeometrien. Die Abweichungsgrenzen dieses Plans sind die
  verbindliche Obergrenze für den interaktiven Rechenpfad; sie rechtfertigen
  weder stilles Überspringen fehlerhafter Körper noch Erfolgsmeldungen bei
  nicht konvergierter Rechnung.
- Bestehende GUI-Steuerelemente, Beschriftungen, Docks, Farben, Anordnung,
  Kamera, Layer, Baumverhalten und Simulationsmodi werden nicht umgestaltet.
  Längere Berechnungen dürfen die GUI-Ereignisschleife nicht blockieren.
- Vorhandene Statusflächen und das Protokoll melden Rechenpfad, Fehler,
  Solverstatus und Wartezustand nachvollziehbar. Eine Fehlerbehandlung darf
  keinen erfolgreichen Zustand vortäuschen.
- Vorrangiges Leistungsziel ist eine flüssige Anzeige: mindestens `30 FPS`
  und höchstens `100 ms` Eingabereaktion unter repräsentativer Last.
  Rendering-Bildrate, Eingabereaktion und Physikdurchsatz werden getrennt
  gemessen; 30 FPS bedeuten nicht automatisch 30 Physikschritte pro Sekunde.
  Die Anzeige darf zwischen Physikupdates interpolieren, aber keinen
  physikalischen Zustand als berechnet ausgeben, der es nicht ist.
- Der feste SI-Zeitschritt und die bisherige Semantik, aufgelaufene
  Simulationszeit nicht still zu verwerfen, bleiben erhalten, bis eine
  gesonderte Verhaltensentscheidung getroffen wurde. Ein Rückstand wird
  sichtbar gemessen und berichtet.
- Quellmodellkorrekturen erfolgen nur nach Erkennung des Konflikts und
  ausdrücklicher Auswahl des unangetasteten Vorrangkörpers. Die
  Ausgangsquelle wird vorher gesichert und bei jedem Fehler wiederhergestellt.
- Kein Commit und kein Push ohne ausdrückliche Beauftragung.

## 2. Phasenübersicht und Abhängigkeiten

| Phase | Ergebnis | Abhängigkeit |
|---|---|---|
| 0 | Reproduzierbare Ausgangsmessung und abgesicherte Testbasis | keine |
| 1 | Gültige Mesh-, Masse- und Trägheitsdaten | Phase 0 |
| 2 | GPU-Backend-Kompatibilität und reproduzierbarer Vergleichsprototyp | Phase 0 |
| 3 | Erkennung und dauerhaft-transaktionale Konfliktkorrektur | Phase 1 |
| 4 | CPU-Referenz, körperfestes Voxelmodell und Wasserlinienkennwerte | Phasen 1 und 3; Phase 2 für GPU-Vergleiche |
| 5 | Belastbarer 2-DOF-Solver und dynamische Kraftschnittstelle | Phasen 0 und 4 |
| 5a | Reproduzierbares Profiling und Optimierung für flüssige Anzeige | abgeschlossene Phasen 0–5 |
| 6 | Weitere Kraftmodule mit belegten Parametern | Phasen 5 und 5a |
| 7 | 6-DOF-Dynamik | Phasen 1, 4, 5, 5a und 6 |
| 8 | Gesamtabnahme und Freigabe | alle freizugebenden Phasen |

Die abgeschlossenen Phasen 0–5 bleiben Grundlage. Als nächstes wird Phase 5a
vor Phase 6 und 7 ausgeführt, damit die bekannten GUI- und
Physikdurchsatzprobleme anhand reproduzierbarer Messungen gezielt angegangen
werden. Phase 2 weist zunächst nur Backend-Kompatibilität und einen
tatsächlichen GPU-Kernel nach; eine endgültige CPU/GPU-Zuordnung oder
GPU-Implementierung der Hydrostatik erfolgt erst, wenn Phase 4 eine
repräsentative CPU-Referenz des körperfesten Rasters und der wiederholten
Auswertung bereitstellt. Der vollständige Vergleich umfasst Datentransfers und
Vorbereitung.

## 3. Phase 0 – Ausgangsbasis und Messbarkeit

### Umsetzung

1. Arbeitsbaum und vorhandene Änderungen sichern; insbesondere keine
   ungetrackten Nutzerdateien oder Modellquellen in Tests einbeziehen.
2. Mit der Projektumgebung unter `.venv` Python-Version und tatsächlich
   installierte Pakete erfassen. Ausgangszustand der vollständigen Testsuite
   und vorhandene Warnungen protokollieren.
3. Bestehende Messfälle für konfigurierten Quader und Yachtmodell festlegen.
   Pro Fall Mesh-/Voxelauflösung, Zahl der Teile, Hardware, Vorbereitungszeit,
   einzelne Hydrostatik-/Kraftauswertung und Solverlauf getrennt erfassen.
4. Einen reproduzierbaren GUI-Smoke-Test für Start, Szenenaufbau,
   Simulationsmodi, Zeitsteuerungen, Körperbaum und sämtliche bestehenden
   Darstellungssteuerungen festhalten: Layer, Kamera-Presets, Hintergründe,
   Beleuchtung, Wasseroberfläche, Wasseroptik und SSAO.
5. Den Ausgangszustand der Materialbearbeitung festhalten: Änderungen gelten
   nur für die Sitzung, aktualisieren Laufzeitkörper und Darstellung,
   schreiben keine Konfigurations-JSON und lösen keine Solver-Neuberechnung
   aus.
6. Referenzdaten und Testeingaben isolieren, damit Tests keine
   `konfigurationen/*.json` oder OBJ-Dateien verändern.

### Prüfungen und Abnahme

- Vollständige Bestandstests laufen in der Projektumgebung reproduzierbar
  durch; die tatsächlichen Ergebnisse werden dokumentiert, ohne eine frühere
  Testanzahl als Sollwert vorauszusetzen.
- Referenzmessungen sind wiederholbar und enthalten getrennte Zeiten für
  einmalige Vorbereitung und wiederholte Auswertungen.
- GUI-Smoke-Test startet in einer Qt-Offscreen-Sitzung und zusätzlich als
  normaler Windows-Prozess mit eingebettetem QtInteractor.
- Regressionen sichern die oben genannten Darstellungsfunktionen und das
  sitzungsgebundene Verhalten von Materialänderungen einschließlich
  unverändert gebliebener JSON-Dateien und ausbleibender Solver-Neuberechnung.
- Bekannte Basisfehler werden von später neu eingeführten Fehlern
  unterscheidbar festgehalten.

## 4. Phase 1 – Meshvalidierung, Masse und Trägheit

### Umsetzung

1. Die Mesh-Eingangsgrenze bei OBJ-Laden und prozeduraler Erzeugung
   vereinheitlichen. Vor jeder Volumenrechnung Punkte und Indizes auf
   Endlichkeit, gültige Indizes, leere Daten, entartete Dreiecke,
   geschlossene Kanten und konsistente Orientierung prüfen.
2. Geschlossene Volumenmeshes von offenen, flächenmassigen Schalen
   unterscheiden. Ein offenes Mesh darf nicht stillschweigend als
   verdrängendes Volumen behandelt werden; Schalen behalten ihre
   flächenbezogene Masse.
3. Volumen-, Flächen-, Schwerpunkt- und Trägheitsberechnung in
   `core/massen.py` und `core/koerper.py` anhand analytischer Formen prüfen.
   Fehlertexte sollen das betroffene Teil und die verletzte Meshbedingung
   identifizieren.
4. Für Verbände Transformationen, massengewichteten Schwerpunkt und
   Parallelaxensatz für alle Teile einschließlich unterschiedlicher Dichten
   und Schalen systematisch prüfen.
5. Sicherstellen, dass der Trägheitstensor um den Schwerpunkt symmetrisch und
   positiv semidefinit ist und seine Hauptmomente die
   Dreiecksungleichungen erfüllen. Rundungsabweichungen werden nur in
   begründeten numerischen Toleranzen akzeptiert.

### Betroffene Bereiche und Tests

- Produktionskandidaten: `segelphysik/core/massen.py`,
  `segelphysik/core/koerper.py`, `segelphysik/core/koerper_formen.py`,
  `segelphysik/core/fabriken.py` und `segelphysik/core/boot_bau.py`.
- Tests ergänzen: `tests/test_koerper.py`,
  `tests/test_bewegung_und_formen.py` und bei Bedarf ein eigenes
  `tests/test_mesh_validierung.py`.
- Abdecken: analytischer Quader und Kegel, Translation/Rotation eines
  Einzelteils, Verband mit versetzten Teilen und unterschiedlichen Dichten,
  Schalenfläche/-masse, offene/geschlossene/ungültige Meshes und endliche
  positive Masseneigenschaften.

### Abnahme

Ungültige Eingaben scheitern nachvollziehbar; Volumenkörper und Schalen
bleiben korrekt unterscheidbar. Alle Referenzwerte für Masse, Schwerpunkt
und Trägheit stimmen innerhalb der fachlich begründeten numerischen
Toleranzen.

## 5. Phase 2 – CPU/GPU-Technologieentscheid und Rechenpfad

### Technologieentscheid vor Implementierung

1. Für Windows x64 und Python 3.14.8 die praktisch verfügbaren
   GPU-Rechenbackends anhand offizieller Paket-/Treiberunterstützung und eines
   minimalen Ende-zu-Ende-Prototyps auf der AMD Radeon 760M prüfen. Eine
   erfolgreiche Installation oder ein erfolgreicher Import gilt nicht als
   Nachweis. Dieser Schritt entscheidet nur über technische Kompatibilität,
   noch nicht über die endgültige CPU/GPU-Zuordnung der Hydrostatik.
2. Mindestens Initialisierung, Speicherverfügbarkeit, Datentransfer,
   numerische Ausgabe und Fehlerverhalten eines tatsächlichen Rechenkernels
   testen. Rendering über PyVista/VTK ist kein Nachweis für GPU-Physik.
3. In Phase 2 nur Geräteerkennung, Backend-Initialisierung, Speicherzugriff
   und einen kleinen tatsächlichen Rechenkern mit Datentransfer auf der
   Zielhardware prüfen. Diese Prototypmessung weist technische
   Kompatibilität nach; sie ist kein repräsentativer CPU/GPU-Benchmark und
   entscheidet nicht über die Aufgabenverteilung. Quader und komplexes
   Modell werden erst nach Vorliegen der CPU-Referenz in Phase 4 für den
   maßgeblichen Vergleich einschließlich Vorberechnung, Transfers und
   wiederholter Kraftauswertung verwendet.
4. In dieser Phase nur Kandidaten und Messverfahren vorbereiten. Die
   endgültige Arbeitslastmessung und feste Aufgabenverteilung erfolgen nach
   Vorliegen der CPU-Referenz des körperfesten Rasters in Phase 4; dabei
   werden erwartete wiederholte Aufrufe, Vorbereitung und Transfers
   einbezogen. Die Zuordnung wird vor Freigabe durch Entwicklungsbenchmarks
   überprüft und bleibt zur Laufzeit unverändert.
5. Bei fehlendem kompatiblem Backend bleibt CPU der korrekte Betriebsweg.
   Kompatibilitätsnachweis und späterer Zuordnungsentscheid werden getrennt
   dokumentiert; es gibt keine automatische Laufzeit-Benchmark- oder
   Leistungswahl.

### Implementierung

- Eine kleine Physik-Backend-Grenze kapselt die festgelegte CPU- und
  gegebenenfalls GPU-Ausführung, ohne GUI- oder Rendercode mit
  Rechenbackend-Details zu vermischen.
- Beim Start wird ausschließlich GPU-Präsenz festgestellt. Ist eine GPU
  vorhanden und die Aufgabe laut Code dem GPU-Pfad zugeordnet, wird dieser
  versucht. Fehler bei tatsächlicher Initialisierung oder Ausführung werden
  im Protokoll mit Backend und Ursache ausgegeben; genau diese Berechnung
  wird auf der CPU wiederholt. Ein langsamer, aber fehlerfreier GPU-Aufruf
  löst keinen Laufzeitwechsel aus.
- CPU und GPU verwenden dasselbe fachliche Modell, dieselben SI-Einheiten und
  definierte Rückgabedaten. GPU-Ergebnisse, die unvollständig oder nicht
  endlich sind, gelten als Fehler und nicht als Erfolg.
- Neue Laufzeitabhängigkeiten werden nur nach erfolgreichem Zielhardwaretest
  in `requirements.txt` und gegebenenfalls `requirements-dev.txt`
  aufgenommen. Optionale GPU-Abhängigkeiten gehören in eine separate
  `requirements-gpu.txt`; der CPU-Betrieb darf nicht von ihnen abhängen.

Der OpenCL-Kompatibilitätsprototyp wurde unter Windows x64 mit Python 3.14.8,
PyOpenCL 2026.1.4 und AMD Radeon 760M (`gfx1103`, Treiber 3652.0) erfolgreich
ausgeführt. Kernelkompilierung, Host-/Gerätetransfers und numerische Ausgabe
wurden Ende-zu-Ende geprüft; der Treiber meldet 13.066.846.208 Byte
OpenCL-Gerätespeicher (gemeinsam genutzter Speicher, keine Aussage über
dedizierten Grafikspeicher). Dieser Prototyp weist nur die technische
Kompatibilität nach; die Zuordnung der Hydrostatik und der repräsentative
CPU/GPU-Benchmark bleiben Phase 4 vorbehalten. PyOpenCL ist daher optional
und wird über `requirements-gpu.txt` installiert.

### Prüfungen und Abnahme

- CPU-Tests laufen unabhängig von GPU und Backendinstallation.
- Mocktests decken GPU nicht vorhanden, erfolgreichen GPU-Aufruf,
  Initialisierungsfehler und Ausführungsfehler mit CPU-Fallback ab. Sie
  ersetzen nicht den realen Abnahmelauf auf unterstützter Hardware.
- Bei verfügbarer GPU werden CPU/GPU mit identischen Testdaten verglichen:
  `|ΔV_disp| <= schranke_volumen_m3`; der Schwerpunkt wird nur verglichen,
  wenn beide Volumina oberhalb der Schranke liegen, dann
  `|ΔK| <= schranke_punkt_m`. Kraft- und Momentabweichungen werden zusätzlich
  mit den in Spezifikation Abschnitt 9 festgelegten, aus diesen Grenzen
  abgeleiteten Schranken geprüft.
- GPU-Erfolg wird anhand ausgeführter Rechenarbeit und erfüllter
  Genauigkeitstests nachgewiesen, nicht anhand eines Imports.
- Der tatsächlich verwendete Rechenpfad wird im vorhandenen Protokoll
  nachvollziehbar ausgegeben. GPU-Meldungen enthalten Backend und
  Gerätenamen; der CPU-Fallback und dessen Ursache werden ebenfalls
  ausgewiesen.
- Benchmarkbericht enthält Hardware, Treiber, Python-/Backendversion,
  Rasterauflösung, alle getrennten Zeitanteile und CPU/GPU-Ergebnisvergleich.

## 6. Phase 3 – Überschneidungen und dauerhafte Modellkorrektur

### Umsetzung

1. Für geschlossene, volumetrische Komponenten pro Hauptkörper eine
   robuste Konflikterkennung ergänzen. Berührende gemeinsame Grenzen gelten
   nicht als Volumenüberschneidung. Offene Schalen werden nicht als
   geschlossene Volumenkörper klassifiziert.
2. Vor dem Physiklauf betroffene Bauteile eindeutig benennen und bei
   erkanntem Konflikt anhalten. Ausschließlich für diesen Fall einen Dialog
   zur Auswahl des unangetasteten Vorrangkörpers verwenden; die bestehende
   allgemeine GUI bleibt unverändert.
3. Die Boolesche Differenz `Konfliktkörper minus Vorrangkörper` zunächst auf
   einer temporären Kopie berechnen. Nullvolumen, offene oder ungültige
   Resultate und fehlgeschlagene Operationen zurückweisen. Für stabile
   Schnitte auch an koplanaren Flächen Manifold3D 3.5.4 mit `Mesh64`
   verwenden; die VTK-Boolean-Filter sind dafür nicht zuverlässig genug.
4. Die dauerhafte Speicherung für beide Quellarten konkret umsetzen:
   - OBJ: korrigierte Geometrie in der ursprünglichen OBJ-Quelle speichern
     und Koordinatentransformation/Skalierung verlustfrei berücksichtigen.
   - Prozedurale Definition: die korrigierte Geometrie als dauerhaft
     gespeicherte Mesh-Quelle/Geometrie-Überschreibung des betroffenen
     prozeduralen Bauteils in dessen ursprünglicher Definition bzw.
     Quelldaten ablegen. Der Lader muss diese gespeicherte Geometrie beim
     erneuten Laden anstelle der unbeschnittenen prozeduralen Ausgabe
     verwenden; die unveränderte prozedurale Definition bleibt als
     nachvollziehbare Herkunft erhalten. Datenformat und Lade-/Speicherpfad
     werden mit einem Prototyp vor der eigentlichen Konfliktkorrektur
     festgelegt und rückwärtskompatibel gehalten.
5. Vor jeder Änderung eine bytegetreue Sicherung erstellen (`.bak`, bei
   Folgekorrigierungen `.bak.1`, `.bak.2` usw.; vorhandene Sicherungen nie
   überschreiben). Erst eine
   transaktionale Speicherung übernehmen, die nach erneutem Laden dieselbe
   Geometrie ergibt und die Konfliktprüfung besteht. Bei jedem Fehler
   Ausgangsdatei wiederherstellen und verständlichen Fehler melden.
6. Nach erfolgreicher Korrektur Körper, Masse, Schwerpunkt, Trägheit,
   vorbereitete Geometriedaten und Darstellung vollständig neu aufbauen.
   Wiederholtes Laden darf die Korrektur weder verlieren noch erneut
   anwenden.

### Betroffene Bereiche und Tests

- Produktionskandidaten: `core/boot_bau.py`, `core/fabriken.py`,
  `core/koerper.py`, GUI-Lade-/Baumfluss in `gui/app.py`,
  `gui/baum.py`, `gui/hauptfenster.py`; neue Geometrieoperationen in einem
  klar abgegrenzten Physikkernmodul. Die geprüfte Runtime-Abhängigkeit
  `manifold3d==3.5.4` wird in `requirements.txt` fixiert.
- Tests ergänzen: `tests/test_baum_regeln.py`,
  `tests/test_gui_baum_json.py` und gezielte neue Tests unter
  `tests/test_geometrie_konflikte.py`.
- Tests verwenden isolierte temporäre Modellquellen, niemals die
  Produktions-OBJ-Dateien.

### Prüfungen und Abnahme

- Keine Überlappung, bloße Berührung, eindeutige Überschneidung und mehrere
  benannte Konflikte testen.
- Vorrangkörpergeometrie bleibt unverändert; nur das andere Teil wird
  beschnitten. Volumen, Masse, Schwerpunkt und Trägheit basieren danach
  auf derselben korrigierten Geometrie.
- Für OBJ und prozedurale Quelle jeweils Auswahl, gespeicherte Differenz,
  erneutes Laden und konfliktfreie Wiederholungsprüfung testen.
- Für die prozedurale Quelle zusätzlich prüfen, dass nach erneutem Laden
  nicht die ursprüngliche unbeschnittene Erzeugung die gespeicherte
  Geometrie-Überschreibung verdrängt und dass unveränderte Definitionen
  weiterhin wie bisher geladen werden.
- Fehler vor dem Schreiben, während des Schreibens und bei der erneuten
  Validierung simulieren; in jedem Fall muss die ursprüngliche Datei
  bytegleich wiederhergestellt sein.
- Ohne ausdrückliche Auswahl darf keine Quelldatei verändert werden.

## 7. Phase 4 – Körperfestes Raster und Hydrostatik

### Umsetzung

1. Auf der nach Phase 3 geprüften und konfliktfreien Geometrie zunächst
   eine CPU-Referenz des körperfesten Rasters implementieren. Den aktuellen
   globalen Voxelpfad in `core/auftrieb.py` als Vergleichsreferenz erhalten,
   bis neue CPU-Ausgaben analytisch und gegen den exakten
   Mesh-/Tetraederpfad geprüft sind. Der neue Referenzpfad wird zunächst
   explizit als `voxel_koerperfest` angefordert; der bestehende Standardpfad
   bleibt bis zur repräsentativen Leistungs- und Genauigkeitsbewertung aktiv.
2. Beim Laden dieser validierten und gegebenenfalls dauerhaft korrigierten
   Geometrie ein körperfestes Raster einmalig
   vorbereiten. Rasterursprung, Auflösung und Abdeckung sind deterministisch;
   Modell-, Material- oder Auflösungsänderung invalidieren und erneuern die
   vorbereiteten Daten.
3. Für eine Pose die Wasserhalbebene in das Körperkoordinatensystem
   transformieren. Das Raster bleibt starr; es wird nicht pro Lage oder
   Kraftauswertung neu erzeugt. Die Auswertung liefert endliches
   verdrängtes Volumen und Volumenschwerpunkt.
4. Wasserlinienfläche und Flächenträgheit in einer klaren
   Hydrostatik-Ausgabe verfügbar machen, sobald die Stabilitätsdiagnostik sie
   benötigt. `core/hydrostatik.py` stellt dafür Fläche, Welt-Schwerpunkt und
   zentrierten 2x2-Flächenträgheitstensor bereit; die Pose-API verarbeitet
   körperlokale Meshes. Die Matrixdiagonale ist
   `(int(y² dA), int(x² dA))`, die Nebendiagonale `-int(xy dA)`.
   Ein fehlender Schnitt ergibt endliche Nullwerte. Eine exakt tangential
   berührte ebene Fläche gilt als geometrischer Schnitt und behält ihre
   Schnittfläche; damit sind Nullvolumen und Wasserlinienfläche unabhängig
   definiert und eine Division durch null wird vermieden.
5. Voxel-Union und Überlappungskorrektur auf eine gemeinsame,
   korrigierte Geometrie beziehen; keine doppelte Volumenzählung.
6. Nach der CPU-Referenz die endgültige Zuordnung für Vorbereitung und
   wiederholte Auswertung anhand repräsentativer vollständiger Arbeitslasten
   festlegen. Anschließend nur die laut Code GPU-zugeordneten Aufgaben
   implementieren. Der CPU-Pfad bleibt immer eigenständig ausführbar.

### Zwischenmessung CPU-Referenz (2026-10-14)

Auf Windows mit Python 3.14.8 und AMD Ryzen 5 8600G wurden neun Yacht-Posen
(`z = -0,1/0/0,1 m`, `phi = 0/10/20°`) bei der konfigurierten Auflösung
`0,05 m` einmal durch beide Voxelpfade ausgewertet. Der globale Pfad benötigte
für die neun Auswertungen insgesamt 1,56 s. Das körperfeste Raster benötigte
3,40 s Vorbereitung und 0,0027 s für neun Auswertungen zusammen. In diesem
Posefeld betrugen die maximalen Abweichungen zwischen den beiden CPU-Pfaden
`0,01025 m³` beim Volumen und `0,01145 m` beim Auftriebsschwerpunkt. Bezogen
auf das Yacht-Gesamtvolumen entspricht die Volumenabweichung `0,3236 %`;
damit erfüllt sie zwar die nun geltende relative CPU-Volumengrenze, aber der
Schwerpunktfehler liegt über `0,005 m`. Diese Raster-zu-Raster-Messung wird
durch den späteren Vergleich beider Raster mit der exakten Union-Referenz
ergänzt. Die Vorbereitung überwiegt zudem den Zeitgewinn der neun
Wiederholungen.

Damit bleibt `voxel_koerperfest` ein Opt-in-Referenzpfad und wird weder
Standard noch Genauigkeitsreferenz. Die beiden Voxelpfade verwenden bei
geneigter Lage unterschiedlich orientierte Raster. Der exakte Pfad summiert
Einzelblattvolumina statt eine Boolesche Vereinigung zu berechnen und ist
daher für die zusammengesetzte Yacht keine gültige Union-Referenz.

Als union-konsistente CPU-Referenz wurde der explizite Pfad `exakt_union`
ergänzt. Er vereinigt die pose-transformierten Volumenmeshes mit Manifold3D,
schneidet die Union an der Welt-Wasserlinie und integriert Volumen sowie
Schwerpunkt aus dem geschlossenen Ergebnis. Der vorhandene Pfad `exakt`
bleibt für bisherige Tests unverändert.

Mit derselben Yacht und denselben neun Posen bei `0,05 m` Rasterweite dauerte
die exakte Union insgesamt 0,22 s; die Vorbereitung des körperfesten Rasters
war 3,40 s, seine neun Auswertungen 0,0029 s. Die maximalen Abweichungen zur
Union-Referenz waren `0,00730 m³` und `0,00908 m`. Relativ zum gesamten
Yacht-Unionvolumen von `3,16786 m³` sind `0,00730 m³` etwa `0,2304 %`;
die neue relative Volumengrenze ist damit erfüllt, die separate
Schwerpunktgrenze von `0,005 m` bei `0,05 m` Rasterweite jedoch nicht.
Bei halbierter Rasterweite `0,025 m` betrugen die Vorbereitungszeit 12,97 s,
die neun Auswertungen 0,0176 s und die maximalen Abweichungen
`0,00247 m³` sowie `0,00328 m`; beide neuen Phase-4-Grenzen wurden damit
eingehalten.

Bei `0,0125 m` betrug die Vorbereitung 57,76 s für 1.621.907 gespeicherte
Voxelzentren; neun Auswertungen benötigten 0,205 s. Die exakte Union derselben
neun Posen benötigte 0,245 s. Die maximale Volumenabweichung sank auf
`0,0008982 m³`, die maximale Schwerpunktabweichung auf `0,001672 m`.
Die Volumenabweichung entspricht etwa `0,0284 %` des gesamten Yachtvolumens;
beide neuen Phase-4-Grenzen wurden eingehalten. Die hohe Vorbereitungszeit
überwiegt den gemessenen Zeitvorteil für neun Auswertungen; GPU- und
GUI-Performance wurden nicht gemessen.

### Aktualisierte CPU-Konvergenz-Abnahme (2026-10-14)

Die folgenden Messwerte und Grenzwerte dokumentieren die abgeschlossene
Phase 4 unter vF1. Sie bleiben als historische Referenz bestehen. Für den
künftigen, auf flüssige Anzeige optimierten interaktiven Rechenpfad gilt
stattdessen das in vF1a festgelegte Genauigkeitsbudget von höchstens `1 %`
Volumenabweichung, höchstens `1°` Winkelabweichung und höchstens `1 %`
Abweichung der übrigen Ergebnisgrößen.

Für den Phase-4-CPU-Vergleich wird die Volumenabweichung ab jetzt relativ zum
gesamten, ungeschnittenen geometrischen Unionvolumen des Körpers definiert:

`e_V = |V_voxel - V_union,unterwasser| / V_union,gesamt <= 0,005`.

Die Grenze beträgt somit `0,5 %` des vollständigen geometrischen
Körpervolumens und ist poseunabhängig. Für das Yachtmodell mit
`V_union,gesamt = 3,16785757 m³` entspricht sie `0,01583929 m³`.
Der Schwerpunkt wird weiterhin separat mit `|ΔK| <= 0,005 m` verglichen,
sofern beide verdrängten Volumina oberhalb der dafür vorgesehenen
Referenzschranke liegen. Die Grenzwerte müssen für sämtliche Abnahmeposen
gelten.

Die bereits gemessenen Höchstabweichungen führen damit zu folgenden
Genauigkeitsurteilen: `0,05 m` erfüllt die relative Volumengrenze, verfehlt
aber die Schwerpunktgrenze; `0,025 m` erfüllt beide und ist die gröbste der
gemessenen, damit abgenommenen Rasterweiten; `0,0125 m` erfüllt beide
ebenfalls, ohne gegenüber `0,025 m` für diese Abnahmeposen erforderlich zu
sein. Eine Umstellung des Standardpfads folgt daraus nicht automatisch.

Ein erneuter Messlauf bei `0,025 m` auf derselben Maschine ergab
`V_union,gesamt = 3,16785757 m³`, eine erlaubte Volumenabweichung von
`0,01583929 m³` und eine maximale relative Abweichung von `0,077852 %`.
Der maximale Schwerpunktfehler war `0,0032703 m`. Die Rastervorbereitung
dauerte `14,63 s`; neun globale Voxel-Auswertungen dauerten `5,58 s`, neun
körperfeste Rasterauswertungen `0,0195 s` und neun exakte Union-Referenzen
`0,216 s`. Einschließlich Vorbereitung ist das körperfeste Raster bei neun
Auswertungen langsamer; sein erheblicher Vorteil bei der wiederholten
Auswertung kann sich bei längeren Läufen amortisieren. Vor einer
Standardumstellung ist deshalb zusätzlich eine repräsentative vollständige
Solver-/Anwendungsarbeitslast einschließlich Vorbereitungszeit zu messen.

### Vollständiger Yacht-Solverlauf (2026-10-14)

Der geforderte Solververgleich wurde mit `yacht1`, `rho_w` und `g` aus der
Projektkonfiguration, Rasterweite `0,025 m`, Kontaktstart aus der Ruhelage
und `loese_robust` ausgeführt. Hardware und Python entsprechen der
Zwischenmessung oben.

| Pfad | Vorbereitungszeit | Solverzeit | Kraftauswertungen | Ergebnis `(z, phi)` | Solver-Rest `(Fz, Mx)` |
|---|---:|---:|---:|---|---|
| Globales Voxel (`voxel`) | < 0,001 s | 190,69 s | 152 | `(-0,14385 m, 0,176°)` | `(0,044 N, 0,034 N·m)` |
| Körperfestes Raster (`voxel_koerperfest`) | 17,77 s | 0,29 s | 130 | `(-0,14220 m, 3,952°)` | `(18,12 N, 76,20 N·m)` |
| Exakte Union (`exakt_union`) | < 0,001 s | 0,83 s | 32 | `(-0,14352 m, 0,171°)` | numerisch null |

Die Gesamtzeit des körperfesten Pfads einschließlich Rastervorbereitung
betrug rund `18,06 s`, gegenüber `190,69 s` für den globalen Solverlauf.
`exakt_union` benötigte einschließlich Solverauswertungen rund `0,88 s`.
Die Zeiten sind einzelne CPU-Messungen und nicht als allgemeine
Performancegarantie zu verstehen.

Die globale Solverlage stimmt mit der Referenzlage aus `exakt_union` bis auf
`0,00033 m` in `z` und `0,005°` in `phi` überein. Die körperfeste Rasterlage
weicht dagegen um `0,00132 m` und `3,78°` ab. An der exakten
Union-Gleichgewichtslage weicht das körperfeste Raster um `0,01512 m³` ab,
das sind `0,4773 %` des gesamten Yachtvolumens und damit knapp innerhalb der
neuen Volumengrenze. Der Schwerpunktfehler beträgt dort jedoch
`0,00666 m` und überschreitet die weiterhin geltende `0,005 m`-Grenze.
Außerdem liefert die exakte Union an der vom körperfesten Solver gefundenen
Lage ein Restmoment von `-78,50 N·m`. Der körperfeste Pfad erfüllt somit in
den vorher geprüften neun Rasterposen die neuen Grenzen, aber noch nicht
alle Genauigkeitskriterien im vollständigen Solverlauf.

Deshalb wird trotz des gemessenen Geschwindigkeitsgewinns keiner der Pfade
zum neuen Anwendungsstandard erklärt. Der globale Pfad bleibt unverändert,
bis eine Raster-/Solverkonfiguration auch die Gleichgewichtslage,
Schwerpunkt- und Momentenübereinstimmung auf repräsentativen Arbeitslasten
erfüllt. `exakt_union` ist derzeit eine CPU-Referenz und wurde nicht als
Produktionsstandard freigegeben. Darstellungsgeschwindigkeit wurde nicht
gemessen; dieser Lauf belegt ausschließlich Rechenzeit des statischen
Solvers.

In vF1 ersetzte diese relative Grenze ausschließlich die
CPU-Konvergenzgrenze für `voxel_koerperfest` in Phase 4. Die
Spezifikations- und CPU/GPU-Übereinstimmungsschranken aus Phase 2 blieben
damals gemäß Spezifikation absolute, konfigurierte Grenzen. Für den künftig
optimierten interaktiven Produktionspfad gilt das abweichende, in Phase 5a
festgelegte Genauigkeitsbudget.

### Betroffene Bereiche und Tests

- Produktionskandidaten: `core/auftrieb.py`, `wasser_schnitt.py`,
  Geometrie-/Körperdaten aus Phase 1 sowie `core/hydrostatik.py` für
  Wasserlinienkennwerte; `core/voxelmodell.py` für das körperfeste Raster und
  `core/volumen_union.py` für die exakte Union-Referenz.
- Bestehende Tests erweitern: `tests/test_auftrieb.py`,
  `tests/test_wasser_schnitt.py`, `tests/test_wasserlinie_geometrie.py`;
  analytische Hydrostatikfälle in `tests/test_hydrostatik.py` sowie
  Vereinigungs-/Referenzfälle in `tests/test_volumen_union.py`.

### Prüfungen und Abnahme

- Analytische Fälle: trocken, tangentialer Kontakt, teilweise und vollständig
  eingetaucht, geneigte Körper, getrennte Teile und Mehrfachbelegung.
- Wasserlinienfläche und Flächenträgheit mit analytischen Schnittflächen
  prüfen, darunter zentrierter Quader/Ponton bei bekannter Eintauchtiefe,
  geneigter Schnitt und verschwindende Wasserlinienfläche. Fläche,
  Schwerpunkt und Tensorachsen müssen zur festgelegten Welt-/Körperkonvention
  passen und bei degeneriertem Schnitt endliche definierte Ergebnisse liefern.
- Verdrängtes Volumen ist monoton mit zunehmendem Tiefgang; Auftrieb ist
  `rho_w * g * V_disp`; Momentenvorzeichen entsprechen der Rollkonvention.
- Körperfestes Raster bleibt beim Lagewechsel identisch und wird nur bei
  Modell-/Material-/Auflösungsänderung neu erstellt.
- Die abgeschlossene Phase-4-CPU-Voxelkonvergenz wurde gegen die geometrische
  Union-Referenz mit den damals festgelegten Grenzen von `0,5 %` Volumen und
  `0,005 m` Schwerpunktabweichung geprüft. Diese historischen Ergebnisse
  bleiben unverändert; der spätere interaktive Produktionspfad wird nach
  Phase 5a mit dem neuen Genauigkeitsbudget bewertet.
- CPU/GPU-Prüfungen erfüllen zusätzlich sämtliche in Phase 2 genannten
  Volumen-, Schwerpunkt-, Kraft- und Momentschranken.
- Vergleichsmessung weist Vorbereitungszeit, Transfers und wiederholte
  Auswertung getrennt aus.

## 8. Phase 5 – Statische Statik und 2-DOF-Dynamik absichern

### Statischer Solver

1. `core/statisch.py`, `core/statisch_robust.py` und
   `core/stoerung.py` so abstimmen, dass ein begrenztes Suchbudget gilt und
   nur eine geeignete stabile Lage gesucht wird; keine exhaustive
   Multi-Start-Suche ergänzen.
2. Erfolg, instabile Lage, neutrale Lage, Stagnation, Budgetende und
   ungültige Rechenergebnisse als unterscheidbare Ergebnisse/Fehler
   behandeln. Restkraft, Restmoment und Abbruchursache dürfen bei Misserfolg
   nicht verloren gehen.
3. Vorhandene Statusausgabe und 3D-Pose mit dem tatsächlichen Solverstatus
   verbinden. Keine neue Liste mehrerer Gleichgewichte und keine zusätzlichen
   allgemeinen GUI-Steuerelemente.

### Dynamik

1. Den festen SI-Zeitschritt aus `physik.json` als einzige Integrationsbasis
   erhalten. Wandzeit/Akkumulator bestimmt nur die Zahl vollständiger
   Schritte.
2. Bestehende z-/phi-Dynamik in `core/dynamik.py` gegen dieselbe
   Hydrostatik- und Kraftfunktion wie den Solver prüfen.
3. Ungedämpfte Grenzfälle, deterministische Wiederholung und passive
   Dämpfung testen. Dämpfung darf keine Energie zuführen; Schwerkraft wirkt
   im Schwerpunktframe ohne künstliches Eigenmoment.
4. Echtzeitaufrufe über bestehende `HauptFenster`-Timer-/Modussteuerung
   einbinden. Berechnung darf keine GUI-Änderung erzwingen und die
   Ereignisschleife nicht blockieren; Visualisierung wird sicher im
   GUI-Thread aktualisiert.

### Zwischenstand (2026-10-14)

- `SolverFehler` kann Abbruchstatus und Diagnosewerte transportieren.
  `loese_robust` erhält bei erschöpftem Budget, Stagnation und instabiler
  Lage die letzte Pose, Restkraft, Restmoment und Iterationszahl; nicht-
  endliche Kraft-/Momentenresiduen werden als ungültige Rechenergebnisse
  ausgewiesen.
- Die Solver-Statusanzeige enthält nun Restkraft und Restmoment und zeigt
  Stagnation bzw. konkrete Solver-Abbruchgründe an.
- Regressionstests decken Solverdiagnosen, nicht-endliche Ergebnisse,
  Energieabweichung des festen Integrators, nicht zunehmende Energie bei
  passiver Dämpfung und das Einmünden eines Pontons in die mit derselben
  Hydrostatik-Kraftfunktion bestimmte statische Solverlage ab.
- Die Echtzeitphysik läuft jetzt in Hintergrundaufgaben mit höchstens vier
  festen SI-Schritten je Aufgabe. Der Timer und die Wandzeitakkumulation
  bleiben im Hauptfenster; Posen, Kraftbilder und Rendering werden erst nach
  Rückkehr der Aufgabe im GUI-Thread aktualisiert. Aufgestaute Simulationszeit
  wird nicht verworfen, sondern mit begrenzten Batches nachgeholt.
- Ein GUI-Regressionstest hält die Kraftauswertung künstlich an und weist
  nach, dass die Qt-Ereignisschleife währenddessen weiterarbeitet und
  Darstellungsmethoden im GUI-Thread aufgerufen werden.
- Auch der statische Solver läuft jetzt als Hintergrundaufgabe. Veraltete
  Ergebnisse werden nach Modus-, Körper- oder Laufzeitobjektwechsel verworfen;
  Status, Fehlerbehandlung, Kraftbild und Pose werden im GUI-Thread
  aktualisiert. Ein blockierter Solver wurde per GUI-Regression geprüft.
- Ein repräsentatives zusammengesetztes Yachtmodell wurde mit der
  `exakt_union`-Kraftfunktion aus einer gestörten Lage über 200 konfigurierte
  SI-Schritte integriert. Gegenüber dem statischen Gleichgewicht blieben
  Tiefgangsabweichung unter `0,002 m`, Krängungsabweichung unter `0,01 rad`,
  Restkraft unter `20 N` und Restmoment unter `15 N·m`.
- Zielhardwaremessung mit dem normalen globalen Yacht-Voxelpfad: ein
  Echtzeitbatch von höchstens vier Schritten benötigte `0,624 s`;
  `HauptFenster._echtzeit_takt()` kehrte nach `0,095 ms` zurück und ein
  eingereihtes GUI-Ereignis wurde nach `16,4 ms` verarbeitet. Die
  Darstellungsmethoden liefen im GUI-Thread. Der Ereignis-Richtwert
  `100 ms` wurde in diesem Lauf eingehalten; die vier Schritte entsprechen
  nur `0,016 s` Simulationszeit. Die Physik kann damit deutlich hinter der
  Wandzeit zurückbleiben; Zeit wird derzeit nicht verworfen.
- **Phase 5 – Umsetzung und festgelegte Regressionen abgeschlossen.**
  Der feste SI-Schritt, Kraftfunktionsgleichheit, Solverdiagnosen,
  Störungs-Einschwingen, GUI-Thread-Trennung und GUI-Reaktionsfähigkeit sind
  abgedeckt. Die gemessene Echtzeit-Unterdeckung bleibt als
  Performance-Optimierung im Backlog; sie ändert nicht stillschweigend die
  Zeitsemantik. Eine Bildratenmessung gehört zur Gesamtabnahme in Phase 8.

### Tests und Abnahme

- Bestehende Referenztests aus `tests/test_statisch.py`,
  `tests/test_statisch_robust.py`, `tests/test_stoerung.py`,
  `tests/test_dynamik.py` und `tests/test_sim_modus.py` erweitern.
- Solver: Gleichgewicht, Restfehler, Stabilität/Neutralität, Stagnation,
  ungültige Werte und begrenzte Abbrüche prüfen.
- Dynamik: fester Schritt, Determinismus, Kraft-/Momentenbilanz,
  Energieerhaltung im ungedämpften geeigneten Referenzfall und nicht
  zunehmende Energie bei passiver Dämpfung prüfen. Zusätzlich aus
  repräsentativen Anfangsstörungen das Einmünden in eine stabile
  Gleichgewichtslage testen; Endpose und Restkraft/-moment gegen die
  statische Solverlösung vergleichen.
- GUI-Regression mit `tests/test_gui_steuerung.py`,
  `tests/test_gui_laufzeit_edit.py`, `tests/test_gui_app.py`,
  `tests/test_grafik_bruecke_darstellung.py` und
  `tests/test_vista_ui.py`: Modi bleiben exklusiv; `=` und `>` bleiben nur
  im Echtzeitmodus aktiv; Baum- und Layersteuerung, Kamera-Presets,
  Hintergründe, Beleuchtung, Wasseroberfläche, Wasseroptik, SSAO, Farben,
  Wasserlinienschnitt, Pose und Docks bleiben funktionsgleich. Sitzungsgebundene
  Materialänderungen dürfen JSON-Dateien nicht verändern und lösen gemäß
  Spezifikation keine Solver-Neuberechnung aus.

## 9. Phase 5a – Profiling und Optimierung für flüssige Anzeige

### Ausgangsmessung und Profiling

1. Die Messungen mit einem reproduzierbaren Szenario für einen einfachen
   Ponton und das zusammengesetzte Yachtmodell wiederholen. Eingaben,
   Posefolge, Rasterauflösung, Hardware, Python-/Backendversion und
   Konfiguration festhalten.
2. Rendering-Bildrate und Framezeiten, Eingabereaktionszeit, GUI-Thread-
   Auslastung, Physikschrittzeit, Batchdauer und Simulationsrückstand getrennt
   messen. Median und hohe Perzentile über mehrere Wiederholungen berichten;
   Initialisierung und einmalige Rastervorbereitung nicht mit wiederholter
   Poseauswertung vermischen.
3. Zeiten für Mesh-/Wasserlinienschnitt, Rastervorbereitung,
   Säulen-/Voxelklassifikation, Hydrostatik, Kraftauswertung, Solver und
   Rendering getrennt erfassen. GPU-Präsenz oder Renderer-GPU-Auslastung
   gelten nicht als Nachweis beschleunigter Physik.
4. Vor einer Optimierung den dominanten Engpass mit Profiling belegen und
   Baseline-Ergebnisse für Rechenzeit und numerische Abweichung speichern.
   Die vorhandenen `voxel`, `voxel_koerperfest` und `exakt_union`-Pfade
   werden als Vergleichs- bzw. Referenzpfade erhalten.

### Optimierung und Abnahme

1. Zuerst den gemessenen Engpass optimieren. Kandidaten sind insbesondere
   Wiederverwendung vorbereiteter Geometriedaten, ein korrekt invalidierter
   Geometrie-/Rastercache, effizientere Voxelklassifikation und die
   Entkopplung der Bildwiederholrate von der Physikschrittfrequenz. GPU-
   Rechenarbeit wird nur weiterverfolgt, wenn der vollständige gemessene
   Arbeitsablauf einschließlich Vorbereitung und Transfers einen Vorteil
   erwarten lässt.
2. Ziel sind mindestens `30 FPS` und höchstens `100 ms` Eingabereaktion in
   den dokumentierten repräsentativen Lastfällen. Physikdurchsatz und
   Rückstand werden zusätzlich ausgewiesen; eine flüssige Darstellung darf
   nicht als Nachweis dafür gelten, dass die Simulation Wandzeitgeschwindigkeit
   erreicht.
3. Den optimierten Pfad über einen repräsentativen Posebereich und
   Gleichgewichtslagen mit `exakt_union` vergleichen. Maximal zulässig sind
   `1 %` Volumenabweichung relativ zum Gesamtvolumen, `1°`
   Gleichgewichtswinkel-Abweichung und `1 %` Abweichung aller übrigen
   physikalischen Ergebnisgrößen. Für Vergleichswerte nahe null sind vor der
   Messung absolute, einheitenbezogene Grenzwerte festzulegen.
4. Zusätzlich Vorzeichen, Endlichkeit, Stabilität und Konvergenz prüfen.
   Das gelockerte Genauigkeitsbudget erlaubt keine nicht-endlichen Ergebnisse,
   falschen Kraft-/Momentenvorzeichen oder fälschlich als konvergiert
   gemeldeten Solverzustände.
5. Feste SI-Schritte bleiben erhalten. Aufgelaufene Simulationszeit wird
   weiterhin nicht stillschweigend verworfen. Reichen die optimierten
   Physikupdates nicht für Wandzeitgeschwindigkeit aus, wird der Rückstand
   gemessen und sichtbar gemacht; eine andere Zeitsemantik erfordert eine
   eigene Nutzerentscheidung.
6. Den vollständigen Benchmark nach jeder Optimierung mit identischen
   Eingaben wiederholen. Genauigkeits-, Leistungsergebnis, Streuung und
   Profilingdaten dokumentieren und die betroffenen Backlog-Einträge
   aktualisieren. Nur ein Pfad, der sowohl die Anzeigeziele als auch alle
   Genauigkeits- und Stabilitätsgrenzen erfüllt, darf für die interaktive
   Anwendung freigegeben werden.

## 10. Phase 6 – Kraftmodule

### Umsetzung

1. Eine gemeinsame Kraftschnittstelle einführen bzw. die bestehende
   Kraftfunktion so erweitern, dass sie Zustand, lineare Geschwindigkeit,
   Winkelgeschwindigkeit und Hydrostatikergebnis entgegennimmt.
2. Ausgabe von Gesamtkräften und -momenten von den für vorhandene
   Darstellung benötigten Auftriebsdaten trennen, aber über ein stabiles
   Ergebnisobjekt gemeinsam verfügbar halten.
3. Bestehende lineare Tauch-/Krängungsdämpfung als konfigurierbare Anteile
   in das Kraftmodell überführen, ohne die Integration von konkreten
   Kraftmodulen abhängig zu machen.
4. Linearen/quadratischen Widerstand, Fluidgeschwindigkeit und Added Mass
   einzeln ergänzen. Keine unbelegten Koeffizienten erfinden: Module bleiben
   deaktiviert, bis fachlich bestätigte Werte in einer validierten
   Konfiguration vorliegen.

### Prüfungen und Abnahme

- Jedes Modul mit isolierten Vorzeichen-, Einheiten-, Grenzfall- und
  Energieprüfungen testen; Nullgeschwindigkeit und Nullparameter liefern
  keinen künstlichen Beitrag.
- Superposition der Module gegen die gemeinsame Gesamtkraft prüfen.
- Sicherstellen, dass Solver und Echtzeitintegration dasselbe Kraftmodell
  aufrufen und die bestehenden Auftriebsdarstellungen weiter funktionieren.
- Konfigurationstests prüfen fehlende, ungültige und nicht endliche
  Koeffizienten. Nicht bestätigte oder ungültige Werte dürfen nicht still
  durch Standardwerte ersetzt werden.

## 11. Phase 7 – 6-DOF-Dynamik

Diese Phase beginnt erst, wenn 2-DOF, Kraftschnittstelle, Trägheitstensor und
Hydrostatik abgenommen sind.

### Umsetzung

1. Zustand um drei translatorische Freiheitsgrade und normierte
   Quaternion-Orientierung erweitern; bestehende 2-DOF-Schnittstellen
   kontrolliert weiterverwenden oder klar migrieren.
2. Newton-Euler-Kräfte und -Momente konsistent zwischen Körper- und
   Weltkoordinaten transformieren. Trägheit bleibt im Körperframe;
   Quaternionen werden nach jedem Schritt normiert.
3. Freiheitsgrade ohne rückstellende äußere Kräfte nicht künstlich
   stabilisieren. Keine neue GUI-Steuerung oder Änderung der Bedienmodi;
   vorhandene Pose-/Darstellungspipeline nimmt die berechnete Pose entgegen.
4. Festen Zeitschritt sowie numerische Stabilität für den erweiterten Zustand
   beibehalten und Fehler-/Abbruchzustände sichtbar machen.

### Prüfungen und Abnahme

- Quaternion-Normierung und Orientierungs-Transformationsinvarianten testen.
- Reine Translation, reine Rotation, Impuls- und Drehimpulsbilanz und
  Koordinateninvarianz mit analytischen Fällen prüfen.
- Gravitation ohne künstliches Moment und frei bewegliche Achsen prüfen.
- 2-DOF-Regression und alle GUI-Bedienungstests unverändert bestehen lassen.

## 12. Phase 8 – Gesamtabnahme

1. Gezielte Tests jeder geänderten Physik-, Geometrie-, Konfigurations- und
   GUI-Schnittstelle ausführen.
2. Vollständige Testsuite mit der Projekt-Pythonversion ausführen:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest
   ```

3. Konfiguration und Abhängigkeiten prüfen:

   ```powershell
   .\.venv\Scripts\python.exe -m pip check
   ```

4. GUI-Regression unter Offscreen-Qt und anschließend den realen
   Windows-Start mit QtInteractor prüfen. Sichtbare Bedienelemente,
   Beschriftungen, Anordnung, Farben, Kamera-Presets, Hintergründe,
   Beleuchtung, Wasseroberfläche, Wasseroptik, SSAO, Layer, Wasserlinienschnitt,
   Pose, Docks, Körperbaum und Simulationssteuerung mit der Ausgangsbasis
   vergleichen. Materialänderungen auf Sitzungsbindung, JSON-Unverändertheit
   und ausbleibende Solver-Neuberechnung prüfen.
5. Auf der Zielhardware interaktive Lasttests mit dem freigegebenen
   Produktionspfad und – falls verfügbar – mit dem unterstützten GPU-Pfad
   ausführen. Eingabereaktion, Bildrate, Physikdurchsatz, Rückstand,
   Initialisierung, Berechnungsdauer und Speicher-/Transferkosten getrennt
   berichten. Unter repräsentativer Last gelten mindestens `30 FPS` und
   höchstens `100 ms` Eingabereaktion sowie die Genauigkeitsgrenzen aus
   Phase 5a. Warte- und Abbruchzustände müssen in bestehenden Statusflächen
   nachvollziehbar sein. Bei CPU-only-Ausführung bleibt die Anwendung
   vollständig bedienbar.
6. Vorher-/Nachher-Modellquellen prüfen: Tests haben keine echten
   Projektmodelle oder JSON-Konfigurationen verändert. Dauerhafte
   Korrekturtests haben ihre temporären Daten aufgeräumt.
7. `git diff --check` ausführen und Änderungen gegen den Arbeitsbaum vor
   Beginn der Umsetzung abgleichen. Keine fremden Nutzerdaten aufnehmen.

### Freigabekriterien

- Alle gezielten Tests und die vollständige Regression bestehen; begründete
  Ausnahmen sind einzeln dokumentiert und bedürfen ausdrücklicher
  Vereinbarung.
- Numerische Referenzen und das Genauigkeitsbudget aus Phase 5a,
  Konfliktkorrektur inklusive Rollback, Solverfehlerfälle und
  Dynamikprüfungen bestehen.
- GPU wird nur dann als verfügbarer Physikpfad ausgewiesen, wenn ein
  tatsächlicher Kernel auf der Zielhardware gelaufen ist und die numerischen
  Grenzwerte eingehalten wurden. Sonst wird der CPU-Pfad korrekt protokolliert.
- Bestehende Darstellung und Bedienung sind regressionsgeprüft; die
  GUI-Ereignisschleife bleibt unter repräsentativer Last bedienbar.
- Bekannte Warnungen, Backend-/Hardwaregrenzen und Messbedingungen sind
  nachvollziehbar dokumentiert.

## 13. Ausdrücklich nicht Teil dieses Plans

- Änderungen an GUI-Anordnung, Beschriftungen, vorhandenen Steuerungen oder
  allgemeinen Bedienelementen.
- Systematische Suche nach allen stabilen Gleichgewichtslagen.
- Automatische Benchmarkläufe oder leistungsabhängiger CPU/GPU-Wechsel zur
  Laufzeit.
- Automatisches Ändern von Modellquellen ohne Konflikterkennung und
  Vorrangkörperauswahl.
- Erfundenes Speichern von Sitzungs-Materialänderungen in Konfigurations-JSON.
- Widerstands-/Added-Mass-Koeffizienten ohne fachliche Grundlage.
- Änderungen an der Simulationszeitsemantik ohne ausdrückliche Vereinbarung.
