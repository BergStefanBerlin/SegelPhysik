# Nativer C++-Code

Das native Modul wird mit CMake und pybind11 als Python-Erweiterung
`_segelphysik_native` gebaut (unter Windows eine `.pyd`-Datei).
Es enthaelt aktuell noch keine Rechenfunktionen und wird von der GUI
nicht aufgerufen. Die Physik bleibt unveraendert in Python.

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
genannten Compilerwerkzeuge erforderlich. Die Python-GUI kann ohne
installiertes natives Modul weiterhin starten.

Quellen liegen unter `src`, Buildprodukte ausserhalb der Quellen unter
`build/native` im Repository-Hauptverzeichnis. Modelldaten liegen unter
[../modelle](../modelle), Pythonquellen unter
[../python/segelphysik](../python/segelphysik).
