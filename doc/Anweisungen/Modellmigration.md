# Externe Legacy-Modelle migrieren

`werkzeuge.migriere_modellpaket` konvertiert `koerper.json` und
`materialien.json` in validierte Modellpakete. Standardmäßig wird nur ein
Dry-run ausgeführt. Die Quellen bleiben unverändert; vorhandene Zielpakete
werden abgelehnt und nicht überschrieben.

## Unterstütztes Eingabeformat

- Konfigurationsordner mit `koerper.json` und `materialien.json`
- Ein Geometrieordner mit einer OBJ-Datei `<Blattname>.obj` je OBJ-Blatt
- OBJ-Skalierung `0.25` und die bisherige Unity-Abbildung
  `(x, y, z) → (z, x, y)`
- Parametrische Legacy-Formen bleiben parametrische Formen und werden nicht
  in OBJ-Dateien umgewandelt.

Alte Konfigurationen enthalten keine Rollenangabe. Nicht anderweitig
gekennzeichnete Blätter erhalten deshalb die neutrale Rolle `allgemein`.
Das Verdrängungskennzeichen wird wie im bisherigen Laufzeitkörper aus
geschlossenem Mesh und Mindestvolumen abgeleitet. Jede Geometrie wird mit dem
aktuellen Paketloader einschließlich Topologie- und
Selbstüberschneidungsprüfung validiert.

## Vorschau

```powershell
.\.venv\Scripts\python.exe -m werkzeuge.migriere_modellpaket `
  --konfiguration "C:\Daten\MeinModell\konfigurationen" `
  --geometrien "C:\Daten\MeinModell\obj" `
  --ausgabe "C:\Daten\MeinModell\pakete"
```

Der JSON-Bericht wird auf der Konsole ausgegeben. Bei Fehlern wird kein
Zielpaket geschrieben und der Prozess endet mit einem Fehlercode.

## Anwenden

Zuerst muss die Vorschau vollständig erfolgreich sein. Danach kann derselbe
Befehl mit `--anwenden` wiederholt werden:

```powershell
.\.venv\Scripts\python.exe -m werkzeuge.migriere_modellpaket `
  --konfiguration "C:\Daten\MeinModell\konfigurationen" `
  --geometrien "C:\Daten\MeinModell\obj" `
  --ausgabe "C:\Daten\MeinModell\pakete" `
  --anwenden
```

Pro Modell wird ein Ordner mit `modell.json` und den kopierten OBJ-Dateien
angelegt. Die bestehende Materialdatei bleibt die Quelle für Materialnamen,
Dichten und Farben; sie muss im Zielbetrieb weiterhin verfügbar sein. Dieses
Werkzeug ersetzt keine manuelle Integration der Pakete in den jeweiligen
Modellkatalog und löscht oder verändert keine Legacy-Dateien.
