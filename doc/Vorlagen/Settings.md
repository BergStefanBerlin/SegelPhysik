# Settings (konfigurationen/settings.json)

Versionierte Einstellungen für die Solver-Parameter
(Menü *Einstellungen → Solver-Parameter → Statisch / Dynamisch*).
Änderungen im Dialog werden sofort gespeichert und wirken sofort.

- Code: `code/core/einstellungen.py`, Dialog: `code/gui/einstellungen_dialog.py`
- Vorlage mit Defaults, Einheiten und Grenzen: `settings_vorlage.json`
  (zusätzlich fest im Code als Rückfallebene). Der Button „Standardwerte“
  lädt die Defaults daraus – auch nach Jahren und bei altem Dateistand.

## Versionsregeln (`schema_version`, `Major.Minor`)

**Die Datei muss abwärtskompatibel bleiben.**

- Neuer Eintrag: nur additiv, Minor erhöhen, `seit_version` in der Vorlage setzen,
  Default angeben. Fehlende Werte in alten Dateien werden mit dem Default ergänzt.
- Umbenennen, Löschen oder geänderte Bedeutung: Major erhöhen und eine Migration
  in `MIGRATIONEN` eintragen (`{alte_major: funktion}`).
- Nach jeder Änderung: `SCHEMA_VERSION` und `settings_vorlage.json` anpassen.
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
Dynamisch: `zeitgenau` (Legacy-Checkbox, ohne Einfluss auf die aktuelle
Zeitsteuerung), `max_schritte_pro_aufgabe`, `max_schritte_nachholen` und
`ueberlast_rueckstand_s`.

Die dynamische Simulation fordert Simulationszeit nur im Umfang der seit dem
letzten Takt verstrichenen Echtzeit an. Rechenrückstand wird gesammelt und
angezeigt; Zeit wird nicht übersprungen und auch bei anhaltender Überlast
erfolgt keine automatische Pause. `ueberlast_dauer_s`,
`nachholen_ende_rueckstand_s` und `nachholrate_ziel` bleiben aus Gründen der
Settings-Kompatibilität gespeichert, haben aber keine Wirkung mehr.

## Parameter (Version 1.1: Kraftpfeildarstellung)

Menü: Einstellungen → Kraftpfeildarstellung. Registry der Paare und Pfeile:
`code/core/pfeilstil.py` (neue Paare nur dort eintragen).

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

## Parameter (Version 1.2: Modellfabrik)

Menü: Einstellungen → Modellfabrik. `modell.paketfabrik_aktiv` wählt
explizit den paketbasierten Laufzeitpfad. Der Standard ist aktiviert; bei
Deaktivierung bleibt für die Repository-Modelle der Legacy-Konfigurationspfad
als Rückfall-/Vergleichspfad verfügbar.

## Parameter (Version 1.3: Anzeigeoptionen)

Menü: Einstellungen → Anzeigeoptionen. Die gemeinsamen Sichtbarkeitsschalter
für Instrumentkarten sind:

- `titel_sichtbar`: Anzeigetitel ein-/ausblenden.
- `titel_beschreibung_sichtbar`: Beschreibung unter dem Titel ein-/ausblenden.
- `analog_sichtbar`: analoge Anzeigeelemente ein-/ausblenden.
- `numerisch_sichtbar`: numerische Werte ein-/ausblenden.

Alle Optionen sind standardmäßig aktiviert. Vorläufig gelten sie gemeinsam
für alle Instrumentkarten; individuelle Werte pro Anzeige können bei der
Umsetzung der jeweiligen Anzeige-Klassen ergänzt werden. Die Einstellungen
stellen zunächst nur die Konfiguration bereit; sie ändern noch keine
Darstellung, solange die jeweilige Anzeige-Klasse nicht implementiert ist.

## Parameter (Version 1.4: Hydrodynamische Detailanzeigen)

Die Detailanzeigen sind unabhängig voneinander und standardmäßig eingeschaltet:

- `anzeigen.hydrodynamik_rumpf`
- `anzeigen.hydrodynamik_kiel`
- `anzeigen.hydrodynamik_ruder`

Sie steuern ausschließlich die Sichtbarkeit der berechneten Kraftpfeile und
ändern weder Kraftmodell noch Bewegung.

## Parameter (Version 1.5: expliziter Schulungs-Darstellungsmodus)

`anzeigen.schulungs_darstellung` ist standardmäßig **ausgeschaltet**.
Der gleichnamige Schalter im Darstellungsdock ist sofort wirksam und
persistent; der Modus kann auch über Anzeigeoptionen gewählt werden.
Er reduziert ausschließlich die Optik (SSAO und MSAA aus; der bestehende
Wasseroptik-Helfer reduziert Glanz/Transparenz auf seine Basiswerte).
Körperlage, Wasserlinie, Wasserbewegung sowie alle gewählten Kraft-/Moment-,
Hydrodynamik-, Schwerpunkt- und Achsenanzeigen bleiben erhalten.
Physikverfahren, Physikzeitschritt und Genauigkeitsgrenzen ändern sich nicht.

Im Modus folgt die Vorbereitung des nächsten Anzeigebildes dem abgeschlossenen
Qt-Swap. Eine bereits zum Swap anstehende Pose wird nicht vor ihrem Bild erneut
aufbereitet; es gibt keinen eigenen selteneren Kraft-/Momentdetailtakt.
Der 20-ms-Timer bleibt als Anstoß/Rückfall aktiv. Beim Ausschalten werden
vorherige SSAO-/Wasseroptik-/MSAA-Werte und der normale 33-ms-Timer wiederhergestellt.
Der Modus garantiert keine feste FPS-Zahl; Live-Messungen und eingeschränkter
Darstellungsstatus bleiben maßgeblich. `frameSwapped` ist kein
Monitor-Scanout-Nachweis.
