# Nativer C++-Code

Das native Modul wird mit CMake und pybind11 als Python-Erweiterung
`_segelphysik_native` gebaut (unter Windows eine `.pyd`-Datei).
Standardmaessig werden Quaternionen, Frames, Koerperaggregation,
Snapshotgeometrie, exakter 6DOF-Auftrieb, Wasserschnitt und Wasserlinienkerne,
hydrodynamische Rollen sowie Wrench-/Widerstands-/Added-Mass-Kerne produktiv
in C++ berechnet. Python behaelt die oeffentlichen Daten- und GUI-Vertraege.
Der exakte Worker fuehrt den gesamten `PhysikKontext`-Batch ohne innere
Pythonkraftcallbacks nativ aus. Beide statischen Solver und stationaere
3-/6D-Newtonstufen samt vollstaendigem dynamischen Nachlauf rechnen fuer
vorbereitete exakte Modelle in C++.
SLERP, Anzeigeinterpolation, Rotationen und die sechs grundlegenden
Mesh-Masseneigenschaften sind ebenfalls produktiv nativ angebunden.
Die gesamte Sweep-and-prune-Selbstschnittpruefung einschliesslich
Dreieckspraedikaten ist nativ; allgemeine Eingabe-/Topologievalidierung
bleibt davon getrennt.
Hinzu kommen Kontakt-/Stoerungs-/Loesungsauswahl, vereinfachte Dynamik,
Navigations-/Kamerawerte sowie deterministische Wasserpunkte, Spuren und
Dunstgitter. Qt-/VTK-Objektverwaltung bleibt Python beziehungsweise in
den bereits nativen Bibliotheken.
Kraftpfeile, Momentboegen, Strichlinien, Wirkungslinien und die
Hauptachsenaufbereitung sind nativ; der bereits native NumPy-Eigenloeser
bleibt erhalten. Auch die Overlay-Richtungsrotation und deren
Punktprojektionen/Achsenlaengen laufen nativ; der VTK-Actoradapter bleibt
Python. IsoSurfaceWater-Spiegelung, Partikelsplatting und Kalibrierung
sowie die numerischen Koerper-Voxelpfade sind ebenfalls angebunden;
PyVista-Marching-Cubes und der optionale OpenCL-Backendadapter bleiben
getrennt. Auch Farbgruppen mit Gelenkhierarchie, benetzte
Sammelgeometrie, Dreieckszellen und die statische Sammeltransformation
werden nativ vorbereitet. Wasseroberflaechen-Triangulierung, bilineare
Verfeinerung und vollstaendige Loch-/Median-/Laplaceaufbereitung laufen
in C++, ohne Aufloesung oder Glaettungsverfahren zu aendern.
Auch die ganze Kamera-Folgegeometrie und manuelle Kameralageableitung,
Instrumentwinkel/-warnungen, SVG-Zielrechtecke und Geschwindigkeitseinheiten
werden nativ berechnet. XML-Metadaten, unveraenderte statische SVG-Elemente,
Textformatierung und Qt-/VTK-Objektverwaltung bleiben Pythonadapter.
Grundformen, Formschwerpunkte/Zentrierung, Liegendtransformation,
Polyederflaecher und Konvexhuellengeometrie werden ebenfalls nativ berechnet.
Die Konvexhuelle behaelt das vorhandene native NumPy-`argsort`, damit
Sortier- und Dreiecksreihenfolge erhalten bleiben. OBJ-Selbstschnitt,
Planaritaet, Ohrtriangulierung und Skalierung/Rotation laufen in C++;
Datei-/Schemaadapter bleiben Python. Der OBJ-Cache ist nach explizitem
Rechenpfad getrennt und vermischt keine Referenz-/Produktivergebnisse.
Generische Python-Kraftcallbacks bleiben explizite Erweiterungspfade;
optionale Voxel-/OpenCL-Verfahren werden nicht automatisch umgeschaltet.

Performanceverschlechterungen sind nach Nutzerentscheidung kein
Zurueckstellungsgrund mehr. Kosten und Gewinne werden dennoch je
Uebertragung dokumentiert. Nach ausdruecklichem Nutzerauftrag vom
20.10.2026 darf numerische Paritaet vorlaeufig mit gelockerten Grenzen
geprueft werden. Urspruengliche strenge Ergebnisse bleiben erhalten.
Endlichkeit, Frames, Schemas, Fehler und Datenbesitz bleiben strenge Gates.
Grenzen, Abweichungen und Restarbeiten stehen im
[Pruefprotokoll](../../doc/WegZuV1.0/Revisionslog/zuV0.10/Messungen/Produktiv_Pruefprotokoll_2026-10-20.md).

## Entwicklung unter Windows

Voraussetzungen: MSVC-x64-Buildtools, Windows SDK und CMake.
Im Repository-Hauptverzeichnis mit dem Projektinterpreter bauen:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -c "import _segelphysik_native as n; print(n.__file__)"
.\.venv\Scripts\python.exe -m segelphysik.gui.app
```

Die Buildabhaengigkeiten stehen in der `pyproject.toml` im
Repository-Hauptverzeichnis und werden isoliert durch pip installiert.
CMake verwendet den Visual-Studio-Generator; ein globaler Compiler-PATH
ist nicht erforderlich. Python und Compilerziel muessen beide x64 sein.
Der Buildtyp ist Release; keine Fast-Math-Optionen werden aktiviert.

Nach C++-Aenderungen erneut `pip install -e .` mit dem Projektinterpreter
ausfuehren. Vorher die GUI schliessen, damit Windows die geladene
`.pyd`-Datei freigibt. Nach Python-Versionswechsel das Modul neu bauen.

`requirements-dev.txt` schliesst den nativen Build mit ein. Fuer die
Entwicklung und die vollstaendige Testsuite sind deshalb auch die oben
genannten Compilerwerkzeuge erforderlich. Ohne installiertes natives Modul
ist nur die ausdruecklich gewaehlte Python-Referenz zulaessig:

```powershell
$env:SEGELPHYSIK_RECHENPFAD = 'python'
.\.venv\Scripts\python.exe -m segelphysik.gui.app
```

Fuer den regulaeren Produktivpfad `cpp` waehlen oder die Variable entfernen.
Ein fehlendes natives Modul fuehrt nie zu einem automatischen Fallback.

Quellen liegen unter `src`, Buildprodukte ausserhalb der Quellen unter
`build/native` im Repository-Hauptverzeichnis. Modelldaten liegen unter
[../modelle](../modelle), Pythonquellen unter
[../python/segelphysik](../python/segelphysik).

## Native Vertraege

- ABI-Version `1`, historischer Modulbezeichner `cpp/datenschicht`.
  Dieser Bezeichner ist keine Aussage ueber den inzwischen groesseren Umfang.
  Der explizite Python-Lader in
  [native_backend.py](../python/segelphysik/core/native_backend.py)
  meldet fehlendes Modul, DLL-Fehler, falsche ABI und fehlende Exporte.
  Er aktiviert niemals stillschweigend die Python-Referenz.
- `Zustand.werte`: Float64, Form `(13,)`, Reihenfolge Position xyz,
  Quaternion wxyz, Koerpergeschwindigkeit xyz, Koerperwinkelgeschwindigkeit xyz.
  SI-Einheiten und die bestehenden Framekonventionen gelten unveraendert.
- Punkte: Float64 `(N,3)`; Dreiecke: Int64 `(M,3)` mit gueltigen Indizes.
  Traegheit: Float64 `(3,3)` im Koerperschwerpunktframe.
  Semidefinite Tensoren sind fuer Punktmassendaten zulaessig; daraus
  folgt keine Freigabe zur Inversion in der Dynamik.
  Parametervektoren: Float64 `(6,)` bzw. Fluidvektoren `(3,)`.
  Kein implizites Float32-/Listen-Casting an der nativen Grenze.
- Zusammenhaengende, gestridete, negative Strides und schreibgeschuetzte
  Arrays werden akzeptiert. Beim Kontextaufbau werden Daten explizit
  einmal in eigenen C++-Speicher kopiert. Kein geliehener NumPy-Zeiger
  ueberlebt den Aufruf. Diagnostische Arrayausgaben sind eigene,
  zusammenhaengende Float64-/Int64-Kopien und leben ohne Kontext weiter.
- Native Klassen sind nach Aufbau nicht von Python aus veraenderbar.
  Geaenderte Masse, Geometrie, Gelenke oder Beladung benoetigen einen
  neuen Kontext; Versionen sind Metadaten, kein gerundeter Zustandscache.
- Reine groessere C++-Arbeit gibt den GIL frei, nachdem Eingaben
  kopiert und Ausgabespeicher angelegt sind. Innerhalb des freigegebenen
  Bereichs keine Python-/NumPy-/Qt-/VTK-Aufrufe.
  `Abbruch` ist ein atomarer, monotoner Abbruchauftrag; eine Pruefung
  wirft einen expliziten Fehler, keine Ersatzantwort.
- `VerbandKontext` haelt vorbereitete Teile dauerhaft. Die bestehende
  physikalische NumPy-Eigenwertvalidierung bleibt bewusst ausserhalb
  dieses numerischen Aggregationsblocks erhalten. Der Block ersetzt
  weder den vollstaendigen Koerperkonstruktor noch dessen Material-,
  Topologie- oder Modellbaumvalidierung.
- `NativeKoerperKontext` berechnet konstante Snapshotgeometrie einmal.
  Ausgaben besitzen unabhaengige Kopien. Exakte Quellpruefungen vor und
  nach der Ausgabe erkennen auch unversionierte Mesh-/Unterbaumaenderungen;
  veraltete Kontexte werden mit Fehler abgewiesen und nicht still erneuert.
  Dieser Gesamtadapter ist noch nicht fuer alle Modelle schneller.
  Grosse NumPy-Punktoperationen zeigen ebenfalls keinen robusten Vorteil.
  Die Adapter sind auf Nutzerwunsch trotzdem produktiv; dies ist keine
  Behauptung eines Gesamtgewinns oder einer abgeschlossenen Migration.
- `HydroKontext` und `HydrostatikKontext` besitzen ihre vorbereiteten
  Meshdaten. Python-Pickles enthalten keine geborgten nativen Zeiger;
  benoetigte Kontexte werden beim Wiederaufbau explizit vorbereitet.

## Gesonderte Kandidatenpruefung

Die laufende Projektumgebung muss nicht aktualisiert werden:

```powershell
.\.venv\Scripts\python.exe -m pip wheel . --no-deps --wheel-dir build\native-m2-wheels -Cbuild-dir=build\native-m2-clean
.\.venv\Scripts\python.exe -m venv --system-site-packages build\native-m2-testenv
.\build\native-m2-testenv\Scripts\python.exe -m pip install --no-deps --ignore-installed .\build\native-m2-wheels\segelphysik_native-0.10.0-cp314-cp314-win_amd64.whl
.\build\native-m2-testenv\Scripts\python.exe -c "import pathlib,sysconfig; pathlib.Path(sysconfig.get_path('purelib'),'segelphysik_referenz.pth').write_text(str(pathlib.Path('.venv\Lib\site-packages').resolve())+'\n',encoding='utf-8')"
```

Die Testumgebung verwendet fuer identische Bibliotheksversionen einen
lokalen `.pth`-Verweis auf `.venv\Lib\site-packages`. Dabei muss ihr eigenes
`site-packages` vor dem Verweis stehen: Das Kandidatenmodul kommt aus der
Testumgebung, NumPy/PySide6 aus der unveraenderten Referenzumgebung.
Beide tatsaechlichen Importpfade vor der Messung pruefen.
Ohne diesen Verweis installiert man die deklarierten Laufzeitabhaengigkeiten
in die Testumgebung; ein fehlendes Paket ist kein erfolgreicher Test.

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\build\native-m2-testenv\Scripts\python.exe -m pytest -q code\cpp\tests\vertrag_native.py code\cpp\tests\paritaet_frames.py code\cpp\tests\paritaet_koerperkontext.py tests\test_native_backend.py
.\build\native-m2-testenv\Scripts\python.exe werkzeuge\migration_native_m2.py --build-verzeichnis build\native-m2-clean --output <neuer-messordner>
```

Die Kandidatentests werden explizit aufgerufen, nicht als fehlende native
Exporte uebersprungen. Die regulaere Produktivsuite benoetigt die oben
genannten produktiven Exporte einschliesslich Physik-/Statikkontext.
Neue Messordner verwenden; Build-/Messrohdaten nicht ueberschreiben.

Der produktive Batch hat einen eigenen, weiterhin nicht vollstaendig
bestandenen strengen Paritaetsnachweis. Die Workeraktivierung ist nach
Nutzerfreigabe vorlaeufig erfolgt; diese Pruefung bleibt unveraendert:

```powershell
.\build\native-m2-testenv\Scripts\python.exe -m pytest -q code\cpp\tests\paritaet_batch.py
.\build\native-m2-testenv\Scripts\python.exe werkzeuge\migration_batch.py --output <neuer-diagnoseordner>
```

Die Numerikdiagnose benoetigt den Diagnosebuild mit `linear_loesen`.
Sie speichert unabhaengige Trajektorien, alle Kraftfelder, gleiche
Eingangszustaende und originale Loesermatrizen. Ueberschrittene Grenzen
geben Exitcode 1 zurueck, keinen erfolgreichen Ersatzbericht.
