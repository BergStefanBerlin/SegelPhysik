# Quellstruktur ab V0.10

| Ordner | Inhalt |
|---|---|
| [python/segelphysik](python/segelphysik) | Python-Anwendung: core, gui, render und verbindende Module |
| [cpp](cpp) | Kuenftiger nativer C++-Code einschliesslich Python-Anbindung |
| [modelle](modelle) | Sprachunabhaengige Modellpakete, Geometrien und zugehoerige Erzeugungswerkzeuge |

Modelldaten bleiben bewusst ausserhalb der Sprachordner. Ein zu einem
Modellpaket gehoerendes Erzeugungsskript bleibt bei seinen Modelldaten.
Weitere Sprachen koennen bei Bedarf eigene direkte Unterordner erhalten.

Projektweite Tests bleiben unter `tests`, Entwicklungswerkzeuge unter
`werkzeuge`, Benutzereinstellungen unter `konfigurationen` und
Dokumentation unter `doc` im Repository-Hauptverzeichnis.

Der Adapter `segelphysik.py` im Hauptverzeichnis erhaelt die bestehenden
Importe `segelphysik.core`, `segelphysik.gui` und `segelphysik.render`.
Der Start aus dem Repository-Hauptverzeichnis bleibt unveraendert:

```powershell
.\.venv\Scripts\python.exe -m segelphysik.gui.app
```

Die Trennung veraendert weder Physikverfahren noch Modellpakete.
Die native Modulgrundlage und deren Buildanleitung stehen unter
[cpp](cpp). Die Buildabhaengigkeiten sind in der `pyproject.toml` im
Repository-Hauptverzeichnis definiert. Buildprodukte liegen unter
`build/native`, nicht in den Quellordnern.
