# Settings (konfigurationen/settings.json)

Versionierte Einstellungen für die Solver-Parameter
(Menü *Einstellungen → Solver-Parameter → Statisch / Dynamisch*).
Änderungen im Dialog werden sofort gespeichert und wirken sofort.

- Code: `segelphysik/core/einstellungen.py`, Dialog: `segelphysik/gui/einstellungen_dialog.py`
- Vorlage mit Defaults, Einheiten und Grenzen: `doc/settings_vorlage.json`
  (zusätzlich fest im Code als Rückfallebene). Der Button „Standardwerte“
  lädt die Defaults daraus – auch nach Jahren und bei altem Dateistand.

## Versionsregeln (`schema_version`, `Major.Minor`)

**Die Datei muss abwärtskompatibel bleiben.**

- Neuer Eintrag: nur additiv, Minor erhöhen, `seit_version` in der Vorlage setzen,
  Default angeben. Fehlende Werte in alten Dateien werden mit dem Default ergänzt.
- Umbenennen, Löschen oder geänderte Bedeutung: Major erhöhen und eine Migration
  in `MIGRATIONEN` eintragen (`{alte_major: funktion}`).
- Nach jeder Änderung: `SCHEMA_VERSION` und `doc/settings_vorlage.json` anpassen.
  Der Test `test_doc_vorlage_entspricht_eingebauter_vorlage` prüft, dass beide gleich sind.
- `ALTE_DATEI_1_0` in `tests/test_einstellungen.py` bleibt unverändert und muss
  immer ladbar sein.

## Verhalten beim Laden

| Fall | Verhalten |
| --- | --- |
| Datei fehlt | Defaults, Datei wird angelegt |
| Datei kaputt | Sicherung `settings.json.bak`, Defaults |
| Wert ungültig | Default für diesen Wert, Protokolleintrag |
| Major neuer als der Code | Defaults im Speicher, Datei wird nie überschrieben |
| Unbekannte Schlüssel | bleiben beim Speichern erhalten |

## Parameter (Version 1.0)

Statisch: `toleranz`, `max_iterationen`, `stagnation_anteil`.
Dynamisch: `zeitgenau` (aus: so schnell wie möglich, Simulationszeit folgt nicht mehr der Uhr),
`max_schritte_pro_aufgabe`, `max_schritte_nachholen`, `ueberlast_rueckstand_s`,
`ueberlast_dauer_s`, `nachholen_ende_rueckstand_s`, `nachholrate_ziel`.
