# Prüf- und Abnahmeprotokoll zuV0.9

**Datum:** 19.10.2026  
**Status:** Technische Integration geprüft; pädagogische Nutzerabnahme ausdrücklich offen  
**Plan:** [Umsetzungsplan](Umsetzungsplan_Echtzeit_und_Modellpakete_v0.9.md)

## Verbindliche Grundlage

- Die [Genauigkeitsgrenzen Fassung 1](Genauigkeitsvorschlaege_v0.9.md)
  bleiben unverändert. Keine Lockerung und kein Näherungsmodus als
  Abkürzung für fehlgeschlagene Leistungsziele.
- Projektumgebung: Windows 11, Projektinterpreter Python 3.14.8;
  Qt-Regressionen mit `QT_QPA_PLATFORM=offscreen`, sichtbare Leistungs-
  messungen separat mit Windows-QPA.
- Neue Seglerdefaults wurden ausdrücklich freigegeben: Optimist 50 kg
  bei (0;0;0,45) m, Folkeboot 150 kg bei (0;0;0,85) m relativ zum
  expliziten Rumpfreferenzpunkt. Separate lokale Benutzereinstellung;
  yacht1 bleibt ladbares Migrationsmodell ohne neue Seglerdefinition.

## M1 – Modellverträge

**Anforderungen:** A-V0.9-00001, A-V0.9-00002  
**Schritte:** U-V0.9-000001, U-V0.9-000002

Implementiert:

- Automatische Paketübernahme ohne Registrierung, unveränderte
  Legacy-/Override-Pfade und explizite Paketfehler.
- Striktes Massenblatt, expliziter Rumpfreferenzpunkt, keine Dummy-
  Geometrie und kein zusätzliches Auftriebsvolumen.
- Masse, alle drei Schwerpunktkoordinaten und vollständiger
  Steiner-Anteil im Gesamtkörper.
- Baumeditor, atomare Speicherung, erneutes Laden und explizite
  Behandlung ungültiger Eingaben bzw. fehlgeschlagener Speicherung.
- Reale GUI-Moduswechsel übergeben den gemeinsamen Gesamtkörper an
  statische und dynamische Worker. Der Integrationstest fängt die
  tatsächlich erzeugten Workeraufträge ab; er ist kein separater
  Physik-Solvernachweis. Die Seglermasse wird nicht autonom integriert.

Vollständige Regression nach der ersten M1-Integration:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q
```

**Ergebnis:** 706 bestanden, 1 übersprungen, 43,61 s.
Der Lauf lag vor den anschließend ergänzten Genauigkeits- und weiteren
GUI-Übergabetests; eine abschließende integrierte Vollsuite folgt unter M4.

Zusatzprüfung nach Einbau des echten GUI-Moduswechseltests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_segler.py tests\test_genauigkeit_v09.py
```

**Ergebnis dieses Laufs:** 25 bestanden, 1,34 s.
Weitere Eingabe-/Dateifehlerfälle werden im finalen Lauf mitgeprüft.

## M2 – Genauigkeitsgrundlage und Referenzdatensatz

**Anforderung:** A-V0.9-00009  
**Schritte:** U-V0.9-000010, U-V0.9-000003

Die Nutzerfreigabe der Fassung 1 ist dokumentiert. Ausführbare Gates
prüfen Volumen, Auftriebskraft/-moment/-schwerpunkt, statische Höhe und
Orientierung, dynamische Position/Orientierung/Geschwindigkeit sowie
messbare Perioden- und Abklingzeiten. Vektorgrößen werden im gemeinsamen
Frame, Orientierungen als kleinster Quaternionabstand verglichen.
Trocken-/Benetztzustand und bei expliziten Rückstelltests die
Momentenrichtung sind zusätzliche harte Gates.

Grenzüberschreitungen führen zu Fehlern pro Stichprobe, nicht zu einer
Bewertung allein nach Median oder P95. Das Modul ersetzt keine engeren
exakten Regressionstoleranzen und gibt keine Näherung frei.

[Eingefrorener Referenzdatensatz](../Messungen/Genauigkeit_Referenzfaelle_v0.9.json):

| Modell | Masse einschließlich Segler | L / B | Hydrostatikfälle | Wasserlinienfälle |
|---|---:|---|---:|---:|
| Optimist | 92,587072 kg | 2,359926 / 1,12 m | 105 | 36 |
| Folkeboot | 1.661,606680 kg | 7,68 / 2,20 m | 105 | 20 |
| yacht1 (Migration) | 450,365556 kg | 4,225 / 1,2648155 m | 105 | 24 |

Pro Modell: trocken, vollständig eingetaucht und fünf Zwischenhöhen,
jeweils kombiniert mit −20/−10/0/10/20° Roll- und −5/0/5° Nickwinkel.
Hinzu kommen beidseitige Wasserlinienhöhen mit 0,1 mm Abstand für jedes
verdrängende Blatt. Das Vollvolumen stammt aus der exakten Union, nicht
aus einer Summe überlappender Blattvolumina.

Der Datensatz hält Paket-/Geometriehashes, Referenzwerte, Rumpfmaße,
Umwelt, konkrete Beladungsvarianten und dynamische Prüfvorgaben fest.
Die SHA256-Fingerabdrücke der textuellen JSON-/OBJ-Quellen verwenden
LF-normalisierte Zeilenenden: Ein Git-Checkout mit anderer
CRLF-Einstellung ändert die Modellidentität nicht. Inhaltliche
Geometrie-/Manifeständerungen werden weiterhin abgelehnt.
Die gespeicherten numerischen Werte stammen aus dem exakten Pfad.
Die 30-s-Dynamik- und längeren Abkling-Kandidatenvergleiche sind
**Prüfvorgaben**, keine bereits ausgeführten Näherungsfreigaben.
Es wurde keine solche Näherung eingebaut.

Bewusste erstmalige Erzeugung und anschließende unabhängige Wiederholung:

```powershell
.\.venv\Scripts\python.exe werkzeuge\pruefe_genauigkeit_v09.py --schreiben
.\.venv\Scripts\python.exe werkzeuge\pruefe_genauigkeit_v09.py
```

**Ergebnis:** Beide Läufe erfolgreich. Wiederholungsvergleich mit
absolut 1e−9 für die exakten Hydrostatikwerte, nicht mit dem größeren
Schulungsbudget. Geänderte Paket-/Geometriehashes werden abgelehnt.
Eine spätere Neuerzeugung darf keine fehlgeschlagene Kandidatenprüfung
verdecken.

Modellannahmen stehen im Modellbaum und Solverstatus; geschätzte Modelle
werden nicht als Engineering- oder Wettkampfvorhersagen präsentiert.

Der komponentengetrennte Echtzeitprofilnachweis einschließlich
Messmethodenkorrektur, Start/Pause/Fortsetzung/Moduswechsel und Regressionen
liegt im [Echtzeitbericht](../Messungen/Echtzeit_Abnahme_U000004-U000008_2026-10-19.md).
Nicht direkt zuordenbare Queue-/Serialisierungs-/IPC-/Protokollzeit wird
als Rest ausgewiesen, nicht als isoliert gemessener IPC-Anteil. Damit ist
die technische M2-Grundlage vorhanden.

## M3 und M4

Historischer Integrationsbefund: Die erste Vollsuite nach dem Kugelcache fand
17 Fehler, 722 bestandene und einen übersprungenen Test. Ein Fehler
betraf die neue Punktmassen-Erkennung im Fabrikprotokoll und wurde durch
ein explizites Punktmassenkennzeichen statt eines angenommenen
Dreiecksattributs korrigiert. Die übrigen 16 Fälle betreffen Actor-Doubles
der Layerkombinationstests. Sie wurden durch Actor-Doubles mit den
tatsächlich benötigten Methoden korrigiert, nicht durch Überspringen
oder produktives Abfangen fehlender Methoden.
Es wurde nach diesem fehlgeschlagenen Lauf nicht committet.

Anschließende Parent-Regression:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_active_body_factory.py tests\test_genauigkeit_v09.py tests\test_segler.py tests\test_modellkatalog_auto.py tests\test_gui_laufzeit_edit.py
.\.venv\Scripts\python.exe werkzeuge\pruefe_genauigkeit_v09.py
```

**Ergebnis:** 66 Tests bestanden, 5,35 s; eingefrorene exakte Referenzen
unverändert reproduziert. Weitere Tests werden anschließend im finalen
Lauf mitgeprüft.

Der erste Echtzeitkandidat verbessert die Poseaufbereitung, erreicht die
Bildratenziele jedoch nicht. Der Nutzer hat deshalb ausdrücklich die
Prüfung eines **umschaltbaren, sichtbar gekennzeichneten Schulungs-
Darstellungsmodus** mit reduzierter Wasseroptik/SSAO/Kantenglättung
freigegeben. Alle zentralen Lernanzeigen sollen erhalten bleiben.
Ein reduzierter Aktualisierungstakt von Kraft-/Momentdetails wurde
**nicht** freigegeben. Physik, Zeitschritte und Genauigkeitsgrenzen
bleiben unverändert.

### Implementierter Renderumfang

Die Anzeigeuhr verwendet einen monotonen, wandzeitgeführten Puffer und
interpoliert ausschließlich berechnete Zustände. Neue Workerbatches
bewirken kein Vorspulen; ein größerer Puffer keine Rückwärtssprünge.
Bei Überlast darf die Anzeige warten; universelle Ruckelfreiheit unter
beliebiger Last ist nicht zugesichert.

Marker/Konturen, Pfeile/Momentbögen, Achsen und Wasserspuren verwenden bei
unveränderter Form vorhandene Daten/Actors wieder. Versteckte
Navigationsfenster speichern Daten, ohne SVGs zu rendern. Qt-Repaint
ersetzt doppelte synchrone VTK-Renderdurchgänge; Swap-Backpressure
verhindert wiederholte aufwendige Vorbereitung desselben ausstehenden Bilds.

Der explizite Schalter **Schulungs-Darstellung** reduziert nur Optik:
SSAO und MSAA aus, Basiswasseroptik. Ausschalten stellt vorherige Optionen
wieder her. Der persistente Default bleibt `false`; hochwertige
Standardoptik ist nicht als 30-FPS-fähig abgenommen. Kraft-/Momentdetails,
Physikzeitschritt und alle Genauigkeitsgrenzen bleiben unverändert.

### Wiederholte sichtbare Software-Leistungsabnahme

Jeweils Windows-QPA, 5 s Warm-up, Folkeboot einschließlich 150 kg Segler,
Prozessworker, `dt=0,004 s`, `exakt_union`, 1x, Viewport 491 × 828,
DPR 1, Wasser/Spuren und Lernanzeigen sichtbar. Identischer
Physik-/Modellhash in Baseline und beiden Abschlussläufen:
`069e175c50bee9d3f9831599ff7bc53c9e76295ccd8204798cb8ead86cda4073`.

| Messgröße | Lauf 1 | Unabhängige Wiederholung | Ziel |
|---|---:|---:|---:|
| Messdauer | 300,044 s | 300,034 s | mindestens 300 s |
| Qt-Swaps/s | 33,64 | 33,68 | mindestens 30 |
| Frameabstand-P95 | 47,343 ms | 47,242 ms | höchstens 67 ms |
| Eingabeproxy-P95 | 39,896 ms | 41,277 ms | höchstens 100 ms |
| Beantwortete Eingaben | 300/300 | 299/299 | alle |
| Rückstandtrend | negativ | negativ | nicht dauerhaft wachsend |
| Workerfehler | 0 | 0 | 0 |

[Rohdaten Lauf 1](../Messungen/Schulungsmodus_final_2026-10-19.json),
[Wiederholung](../Messungen/Schulungsmodus_wiederholung_2026-10-19.json)
und jeweilige Worker-JSONL bleiben erhalten. Details, Vorherwerte,
fehlgeschlagene Kandidaten und reproduzierbare Kommandos stehen im
[Echtzeitbericht](../Messungen/Echtzeit_Abnahme_U000004-U000008_2026-10-19.md).

**Grenzen:** Gezählt wird `QOpenGLWidget.frameSwapped`, nicht VTK-EndEvent
und nicht tatsächlicher Monitor-Scanout. Eingabelatenz ist Kamerareaktion
bis Qt-Swap mit veränderter Kameraposition, kein optischer Pixelnachweis.
Die Baseline erfasste die Viewportmaße noch nicht; der Vorher-/Nachher-
Vergleich ist deshalb nicht streng geometrisch identisch. Beide
Abschlussläufe sind untereinander gleich konfiguriert. Alte VTK-„FPS“
sind ausdrücklich keine gültige Bildratenabnahme.

### Dokumentierte negative Kandidatenentscheidungen

| Anforderungen / Schritt | Ergebnis |
|---|---|
| A-V0.9-00005/00006, U-V0.9-000006 | GUI-CPU-Aufbereitung war der wesentliche End-to-End-Engpass; der Worker hält annähernd 1x. Keine zusätzliche Physik-CPU-/Unionoptimierung mit nachgewiesenem Nutzen implementiert; keine spekulative JIT-/Native-Abhängigkeit. |
| A-V0.9-00007, U-V0.9-000007 | 74.810 Hydrostatikaufrufe mit 74.810 bitexakt verschiedenen Ganzposen: null direkte Treffer. Kein Ganzpose-Ergebniscache eingebaut; Rundung und veraltete Ergebnisse nicht freigegeben. Kein größerer Hydrostatiktakt. |
| A-V0.9-00008, U-V0.9-000008 | NPU-Gerät/Treiber vorhanden; Projektlaufzeit/Provider und geeigneter großer Tensorkernel nicht nachgewiesen. Machbarkeit negativ für produktiven Einsatz abgeschlossen, kein gerechtfertigter Kernelbenchmark und keine NPU-Abhängigkeit. |

Dies schließt die Kandidatenbewertung ab, macht nicht implementierte
Beschleunigungen aber nicht zu erfüllten Spezifikationsanforderungen.
Sie bleiben in der Statusmatrix sichtbar und werden nicht als
implementiert im zentralen Log geführt.

### Abschließende integrierte Regression

Nach allen Codeänderungen und der unabhängigen Live-Wiederholung:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe werkzeuge\pruefe_genauigkeit_v09.py
```

**Letztes Ergebnis am 19.10.2026:** 749 bestanden, 1 übersprungen in 48,78 s.
Der einzige Skip betrifft den Windows-Symlinktest
`tests/test_mesh.py:229`: Symlinks sind in dieser Umgebung nicht verfügbar.
Es ist kein übersprungener Genauigkeits- oder Leistungstest.
Der anschließende Replay reproduziert alle eingefrorenen exakten
Hydrostatikreferenzen der drei Modelle unverändert. Die bekannte
Kiel-Massenplausibilitätswarnung ist keine neue fehlgeschlagene Prüfung.
Vorherige integrierte Läufe: 748/1 in 44,87 s und 51,73 s.

Beim abschließenden Git-Indexvergleich fiel auf, dass rohe Dateihashes
bei CRLF/LF-Konvertierung nach einem frischen Checkout ungültig würden.
Die Fingerabdrücke normalisieren deshalb ausschließlich CRLF zu LF.
Ein zusätzlicher Regressionstest belegt Zeilenendenäquivalenz und
fortbestehende Erkennung geänderter Geometriewerte. Ein separater
Strukturvergleich vor dem erneuten Replay bestätigt: Nur die 13
betroffenen Hashwerte ändern sich, sämtliche numerischen Referenzen,
Szenarien und Genauigkeitsgrenzen bleiben exakt identisch; die neuen
Hashes passen zum gestagten Git-Inhalt. Keine Referenzwerte wurden
neu berechnet oder auf ein fehlerhaftes Kandidatenergebnis angepasst.

### Freigabestand

Der Nutzer entschied nach Vorlage der Ergebnisse ausdrücklich:
**technischen Stand lokal committen; pädagogische Nutzerabnahme offen
lassen**. Daher keine behauptete vollständige Gesamtfreigabe, keine
Unterrichtserprobung, Realbootvalidierung oder Monitor-Scanoutmessung.
M1/M2 sind technisch geprüft, M3 hat Implementierung/Regression und
Kandidatenentscheidungen, M4 die erfolgreiche technische Integration.
Die pädagogische Sichtabnahme von A-V0.9-00004 bleibt offen.
Die verbindlichen Genauigkeitsgrenzen bleiben gesperrt.
Kein Tag, Push oder GitHub-Release ist beauftragt.
