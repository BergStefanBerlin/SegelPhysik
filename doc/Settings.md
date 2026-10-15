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
Dynamisch: `zeitgenau` (Checkbox „Echtzeitgenau“; Schlüsselname bleibt aus Kompatibilitätsgründen; aus: so schnell wie möglich, aber nie schneller als die reale Zeit, Zeitlupe statt Überlast-Stopp),
`max_schritte_pro_aufgabe`, `max_schritte_nachholen`, `ueberlast_rueckstand_s`,
`ueberlast_dauer_s`, `nachholen_ende_rueckstand_s`, `nachholrate_ziel`.

## Parameter (Version 1.1: Kraftpfeildarstellung)

Menü: Einstellungen → Kraftpfeildarstellung. Registry der Paare und Pfeile:
`segelphysik/core/pfeilstil.py` (neue Paare nur dort eintragen).

- `kraftpfeile_allgemein`: Vordergrund, Grunddicke, Kopfmaße, `kraftskala`
  (cm Pfeillänge je N, Default 0,05), `momentskala` (cm Bogenradius je Nm,
  Default 0,05), Mindestlänge, Strichmaße. Dicken in Prozent der größten
  Körperausdehnung. `skala` je Pfeil ist ein zusätzlicher Faktor (Default 1).
- `kraftpfeile_paare`: `farbe_<paar>` (Paar 1 Gewicht/Auftrieb blau, Paar 2 Fremdkraft rot).
- `pfeil_<id>` je Pfeil: `sichtbar`, `farbe` (leer = Paarfarbe), `dicke` (0 = Grunddicke),
  `kopf`, `gestrichelt`, `skala`, `deckkraft`, `vordergrund`. Die Dicke ist fest,
  nur die Länge folgt dem Betrag.
- `schwerpunkte`: Radius und Farbe von S und K, Kontur.
- `hauptachsen`: Dicke, Farben, Vordergrund.
