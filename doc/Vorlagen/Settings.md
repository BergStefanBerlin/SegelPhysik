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

Historische Einträge wie `pfeil_hebelarm` bleiben aktiv: Farbe, Deckkraft,
Vordergrund und Strichstil werden in der aktuellen gemeinsamen
Snapshotdarstellung weiterhin angewendet.

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

## Parameter (Version 1.6: gemeinsame Kraft-/Momentenanzeige)

Der zusätzliche Bereich `kraefteanzeige` wird beim Laden alter Dateien
additiv ergänzt. Vorhandene Farben, Pfeilfelder und unbekannte Schlüssel
bleiben erhalten; es werden keine Modell- oder Physikparameter migriert.

- `logarithmisch`: lineare bzw. log1p-Abbildung beider getrennten Domänen.
- `kraftreferenz_N`, `momentreferenz_Nm`: positive manuelle Referenzen;
  `0` fordert eine einmalige Initialisierung je Körper an. Automatische
  Referenzen und das Ergebnis von „Neu einpassen“ bleiben ausschließlich
  im Arbeitsspeicher.
- `kraftmaximum_px`, `momentmaximum_px`, `breite_px`, `kopflaenge_px`:
  Größen in logischen Pixeln; Defaults 180, 48, 3 und 10.
- `farbe_<quellart>`: Rollenfarben des gemeinsamen Beitragsregisters.
  Abweichende bisherige Einzel-/Paarfarben werden weiter berücksichtigt;
  eine abweichende neue Rollenfarbe hat Vorrang.
- `beschriftung`: Auswahl-/Bilanzlabels ein- oder ausblenden.
- `koerperframe`: Komponenten im Körperframe statt im Weltframe anzeigen;
  die 3D-Geometrie verbleibt am tatsächlichen Ort in der Szene.
- `weltursprung`: Momentenbezug Weltursprung statt Schwerpunkt.
  Die vorhandenen Wrenches werden nur für die Anzeige verschoben.
- `komponenten`: ergänzende x-/y-/z-Momentenbögen; Gesamtmoment
  und Komponenten werden nicht nochmals summiert.
- `mehrkoerper`: getrennte Zweige der vorhandenen Körpersnapshots;
  standardmäßig genau ein Anzeigekörper. Der Schalter verändert
  weder physische Aktivierung noch Kraftmodell und startet keinen Solver.
- `sichtbarkeiten`: verschachtelte Wahrheitswerte nach Körper-Quell-ID
  und Beitrags-Quell-ID, nicht nach Listenposition oder Anzeigename.
- `fensterlayout`: geprüfte Qt-Geometrie, Dockbereich, Floating-Zustand,
  Sichtbarkeit und Headerzustand einschließlich Spaltenreihenfolge/-breiten.
  Eine nicht mehr erreichbare Monitorposition wird in den verfügbaren
  Bildschirmbereich zurückgesetzt.

Bedienung: *Einstellungen → Kraftpfeildarstellung → Skalen und
Bildschirmgroessen*; „Neu einpassen“ ist auch im Wertefenster verfügbar.
Stil-/Skalenänderungen verwenden vorhandene Snapshots und starten keinen
Solver. Schließen des Hauptfensters speichert das Wertefensterlayout.
Sequenzen, Kräfte, Momente, Solverentscheide und temporäre Auswahl werden
nicht als neue Settings-Felder persistiert.

Die vier zusätzlichen booleschen Optionen sind standardmäßig aus.
Körperwahl, Optionen und „Anzeigestandard wiederherstellen“ sind im
Wertefenster erreichbar. Der Reset setzt neue Anzeigeoptionen und alte
Pfeilstilbereiche zurück, bewahrt das Fensterlayout und verändert keine
Physikeinstellung.

### Zuordnung historischer Pfeiloptionen in V0.11

Historische Felder und gespeicherte Einheiten bleiben erhalten.
Die neue Bildschirmabbildung verwendet deren Verhältnis zum bisherigen
Default als Gestaltungsfaktor, nicht als zweite unabhängige Weltmaßskala:

| Historisches Feld | Wirkung in der gemeinsamen Anzeige |
| --- | --- |
| `kraftskala`, `momentskala`, individuelle `skala` | Faktor gegenüber 0,05 cm/N bzw. 0,05 cm/Nm, multipliziert mit `skala`; abweichende Faktoren werden in der Legende genannt |
| `dicke`, `kopf`, Kopfmaße | Relative Kopf-/Schaftgestaltung auf Basis der neuen logischen Pixelmaße; keine betragsabhängige Dicke |
| `strich_laenge`, `luecke` | Relative Faktoren gegenüber 3 % bzw. 2 % der Körperausdehnung; Bildschirmbasis 8 bzw. 5 logische Pixel |
| `mindestlaenge` | Kleinwert-Markierungsgrenze, mindestens ein logischer Pixel; keine künstliche Verlängerung der Kraft |
| `m_x/y/z`, `fremd_mx/y/z`, `mges_x/y/z` | Individuelle Momentenkomponentenstile; vom historischen Default abweichende Sichtbarkeit überschreibt den neuen gemeinsamen Komponentenschalter |
| Farben, Deckkraft, Linienart, Vordergrund | Gemeinsame wirksame Beitragsstile; Tabelle und 3D verwenden dieselben Farben |

Automatische Skalen bleiben körperbezogen. Für einen belastbaren
Größenvergleich mehrerer Körper sind gemeinsame manuelle Kraft- und
Momentenreferenzen einzustellen. Die Legende weist darauf hin.
Darstellungsintegration und Reset sind automatisiert geprüft. Jede registrierte
historische Pfeil-ID wird mit individuellen Feldern und globalen Größen durch
Schema-1.0-Migration, Speichern und Neuladen geprüft; erwartete Bildschirmmaße
und Skalenfaktoren werden numerisch kontrolliert. Zwei echte
Hauptfensterinstanzen prüfen den Neustart einschließlich Layout, Stil,
Referenzen, Sichtbarkeiten und Optionen, ohne Kräfte, Snapshots, temporäre
Auswahl oder Dynamikzustand wiederherzustellen. Die echten Stildialoge werden
in Statik und Pause über 22 Eingabefelder geprüft, jeweils ohne Physikauftrag.
Diese automatisierten Nachweise ersetzen keine physische Monitorwechsel-
oder menschliche Darstellungsabnahme.
Belege und offene Punkte stehen im
[V0.11-Umsetzungsplan](../WegZuV1.0/Revisionslog/zuV0.11/Umsetzungsplan_V0.11.md#913-trigger--import--und-modellabschlussnachweise).

GUI-Tests laden ihre Standardkonfiguration in ein temporäres Verzeichnis,
damit ein Testlauf keine persönliche Settings-Datei anlegt oder migriert.
