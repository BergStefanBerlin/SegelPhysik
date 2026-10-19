# GUI-Steuer- und Diagnose-API

Die GUI stellt eine Python-API fuer Steuerung und Laufzeitdiagnose bereit. Sie
ist fuer Tests und Automatisierung innerhalb desselben Python-Prozesses gedacht.
Es gibt keine HTTP-, Socket- oder sonstige externe Schnittstelle.

## Zugriff

`HauptFenster` erstellt beim Aufbau des Fensters die API-Instanz
`fenster.steuer_api`:

```python
api = fenster.steuer_api
```

Der aufrufende Code muss im selben Prozess wie die GUI laufen und die
Fensterinstanz erhalten. Die gestartete GUI stellt die API nicht automatisch
einem separaten Python-Prozess zur Verfuegung.

Alle API-Aufrufe muessen im Qt-GUI-Thread erfolgen. Ein Aufruf aus einem
anderen Thread loest `RuntimeError` aus. Qt-Ereignisse und Timer laufen
normal weiter; bei Messschleifen sollte die Ereignisschleife nicht durch
blockierende Arbeit angehalten werden.

## Steuerelemente finden

`controls()` liefert eine nach ID sortierte Liste der erkannten
Bedienelemente. Jeder Eintrag beschreibt unter anderem:

| Feld | Bedeutung |
| --- | --- |
| `id` | ID fuer Lese-, Schreib- und Aktivierungsaufrufe |
| `aliases` | Weitere IDs, sofern ein Element mehrere Fensterattribute hat |
| `kind` | Qt-Elementtyp |
| `label` | Angezeigte Beschriftung oder Elementname |
| `enabled`, `visible` | Qt-Aktivierbarkeit und Sichtbarkeit |
| `value` | Aktueller Wert |
| `minimum`, `maximum` | Wertebereich numerischer Elemente |
| `options` | Texte der Auswahloptionen einer Combobox |

Beispiel:

```python
for control in api.controls():
    print(control["id"], control["kind"], control["value"])
```

Fensterattribute erzeugen die bevorzugten IDs. Fuehrende Unterstriche werden
entfernt; Elemente aus einem Attribut-Dictionary erhalten die ID
`attribut.schluessel`. Beispiele sind `fremd_check`,
`fremd_felder.betrag` und `btn_echtzeit`.

Menueaktionen erhalten IDs in der Form `menu.Menue.Aktion`. Baumknoten erhalten
eine ID aus dem ID-Praefix des Baums und ihrem sichtbaren Pfad, beispielsweise
`baum.item.Yacht1`. Der angezeigte Name ist massgeblich; bei geaenderten
Bezeichnungen ist die aktuelle ID erneut mit `controls()` zu ermitteln.
Elemente ohne Fensterattribut erhalten eine generierte ID aus ihrem Qt-
Elternpfad.

## Lesen und Aendern

`get_control(control_id)` liefert die Beschreibung des aktuellen Zustands
eines Elements:

```python
wert = api.get_control("fremd_felder.betrag")
print(wert["value"])
```

`set_control(control_id, value)` setzt einen Wert und liefert danach die
aktuelle Beschreibung zurueck:

```python
api.set_control("fremd_felder.betrag", 20.0)
api.set_control("fremd_felder.azimut", 0.0)
api.set_control("fremd_check", True)
```

Unterstuetzte Elemente und Werte:

- Checkbare Schaltflaechen: `bool`. Zum Setzen wird bei Bedarf ein normaler
  Klick ausgeloest, damit die verbundenen GUI-Signale ausgefuehrt werden.
- Numerische Felder und Slider: Wert innerhalb des jeweiligen Qt-Bereichs.
  Die von Qt angewandte Begrenzung ist im zurueckgegebenen Wert sichtbar.
- Comboboxen: Optionsindex, sichtbarer Optionstext oder Optionsdaten
  (`itemData`).
- Textfelder: Text; Nicht-Textwerte werden mit `str()` umgewandelt.
- Checkbare Baumknoten: `bool`; der Wert wird in der Checkbox-Spalte gesetzt.

Nicht-checkbare Schaltflaechen sind nicht mit `set_control()` setzbar.
`activate(control_id)` loest stattdessen eine Aktion aus: Schaltflaechen werden
angeklickt, Menueaktionen ausgeloest und checkbare Baumknoten zwischen
aktiviert und deaktiviert umgeschaltet. Der Rueckgabewert ist jeweils die
aktuelle Elementbeschreibung.

Beispiel fuer eine Menueaktion:

```python
api.activate("menu.Ansicht.Kamera")
```

Die konkreten Menue- und Baumnamen koennen von der geladenen Konfiguration
abhaengen. Fuer gueltige IDs daher `controls()` verwenden.

## Laufzeitdaten lesen

`snapshot()` liefert einen zusammenhaengenden, fuer `json.dumps()` geeigneten
Snapshot der GUI- und Simulationsdaten:

| Schluessel | Inhalt |
| --- | --- |
| `mode` | `statisch` oder `echtzeit` |
| `simulation` | Timer, Worker, angeforderte/berechnete Zeit, Rueckstand, Modus und Solverstatus |
| `body` | Aktiver Koerper, Masse, Traegheit, Modellzentrum, Version und Bewegungszustand |
| `physics` | Aktive Physikparameter oder `null`, falls noch keine Echtzeitphysik geladen ist |
| `external_force` | Aktuelle Fremdkraft und Angriffspunkt oder `null`, wenn deaktiviert |
| `force_model` | Serialisierte Daten des aktiven Kraftmodells oder `null` |
| `force_result` | Letztes Echtzeit-Kraefteergebnis oder `null` |
| `static_results` | Vorhandene Ergebnisse der statischen Berechnung |
| `settings` | Einstellungen einschliesslich Pfad, Daten, Meldungen und Schreibschutzstatus |
| `controls` | Map von Steuerelement-ID auf aktuellem Wert |
| `variables` | Serialisierte, nicht-aufrufbare Attribute des Hauptfensters |

Bei nicht verfuegbarem Laufzeitkoerper ist `body` weiterhin ein Objekt mit
`available: false`. Der `state`-Inhalt in `body` sowie einige Werte im Snapshot
haengen davon ab, ob bereits eine Simulation oder Berechnung stattgefunden hat.
Der Snapshot ist eine Diagnoseaufnahme zum Aufrufzeitpunkt, keine Historie.

Beispiel fuer den gewuenschten Vorwaerts-Kraftversuch:

```python
# Erst den gewuenschten Hauptkoerper im Komponentenbaum aktivieren.
yacht_id = next(
    control["id"] for control in api.controls()
    if control["kind"] == "QTreeWidgetItem"
    and control["label"].strip().casefold() == "yacht1"
    and control["value"]["checkable"]
)
api.set_control(yacht_id, True)

api.set_control("fremd_felder.betrag", 20.0)
api.set_control("fremd_felder.azimut", 0.0)
api.set_control("fremd_felder.elevation", 0.0)
api.set_control("fremd_felder.x", 0.28)
api.set_control("fremd_felder.y", 0.0)
api.set_control("fremd_felder.z", 3.21)
api.set_control("fremd_check", True)
api.set_control("btn_echtzeit", True)
api.activate("btn_vor")

start = api.snapshot()
assert start["external_force"] is not None
assert start["mode"] == "echtzeit"
```

Azimut `0` und Hoehe `0` richten die Kraft in Welt-`+X`. Der Angriffspunkt
wird relativ zum Koerperschwerpunkt angegeben. Der Snapshot sollte unmittelbar
nach der Konfiguration geprueft werden, bevor Messwerte als Versuchsergebnis
interpretiert werden. Der Knotenname `yacht1` ist die Bezeichnung in der
aktuellen Projektkonfiguration; bei einer anderen Konfiguration den passenden
Hauptkoerper ueber `controls()` ermitteln.

## Werte serialisieren und Fehler

`variables()` gibt die nicht-aufrufbaren Instanzattribute des Hauptfensters
zurueck. NumPy-Werte, Enums, Pfade, Dataclasses, bekannte Physikobjekte,
Sequenzen und Dictionaries werden in JSON-kompatible Strukturen umgewandelt.
Qt-Widgets und nicht speziell abgebildete Objekte werden als Typbeschreibung
ausgegeben; dadurch wird kein vollstaendiger interner Qt- oder Python-
Objektzustand zugesichert.

Ungueltige IDs fuehren zu `KeyError`. Nicht unterstuetzte Operationen oder
falsche Eingabetypen fuehren zu `TypeError`; ungueltige numerische Werte,
Comboboxoptionen oder Bereichsangaben zu `ValueError`. Ein API-Aufruf aus dem
falschen Thread fuehrt zu `RuntimeError`. Solche Fehler sollten im
aufrufenden Test bzw. Automatisierungscode ausdruecklich behandelt werden.

## Tests

Die API- und GUI-Regressionstests befinden sich in
`tests/test_gui_steuer_api.py` und `tests/test_gui_steuerung.py`. Unter Windows
lassen sie sich mit folgendem Befehl ausfuehren:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gui_steuer_api.py tests\test_gui_steuerung.py
```
