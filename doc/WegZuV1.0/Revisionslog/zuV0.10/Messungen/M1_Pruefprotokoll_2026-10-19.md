# M1: Referenz, Inventar und Vergleichsharness

**Stand:** 19.10.2026

**Entscheidung:** M1-Gate bestanden; M2 darf begonnen werden.
Keine Rechenfunktion wurde produktiv nach C++ umgeschaltet.

**Aktueller Vollsuite-Abschluss:** 909 Tests
bestanden, ein vorbestehender Windows-Symlink-Skip; exakter v0.9-Replay
bestanden. Inzwischen 34 aktive A-IDs, 20 U-Schritte, 298 Inventareinträge,
37 Profilbewertungen aus 31 unveränderten Profilquellen und konkrete
Referenztestzuordnung für 298/298 Einträge. Die zusätzlich ausgeführten
Fach-/Harnessprüfungen und die abgeschlossene Speicherbaseline sind unten
getrennt dokumentiert.
Frühere Testzahlen im Dokument bezeichnen frühere Teilstände.

## U-V0.10-000001: Referenzsicherung

- Python-Referenz: `7a955c24ceb6c0825e05a574b959dd1176be2e2c`, auf
  `v0.10` und `origin/v0.10` gesichert; historischer Ursprung `0.9`/`1b16648`.
- [Referenzmanifest](M1_Referenzmanifest.json): 116 versionierte Quellen,
  Modelle, Konfigurationen, Build-/Abhängigkeitsdefinitionen und
  SVG-Instrumentdateien einschließlich der eingefrorenen v0.9-Referenz.
  Hashvergleich zum Sicherungscommit, ausschließlich CRLF/LF normalisiert.
- [Umgebungsinventar](M1_Kernbaseline_2026-10-19/umgebung.json): Python,
  Bibliotheken, CPU/GPU/RAM, MSVC-Konfiguration und Releaseflags,
  Messwerkzeughashes und vollständige Referenzdateihashes.
- Der Messrunner verweigert eine Baseline bei abweichenden Referenzdateien.
  Er aktiviert weder einen nativen Kandidaten noch einen Fallback.
- Vollsuite nach Viewportkorrektur: **800 bestanden, 1 übersprungen**. Der vorhandene Skip betrifft
  fehlende Windows-Symlinkberechtigung, nicht native Installation.
- Eingefrorener Hydrostatikreplay für alle drei Modelle bestanden.
  Keine Referenzwerte oder Toleranzen neu erzeugt bzw. gelockert.
- Sichtbare Smoke-Prüfung unter Windows-QPA: alle drei Modelle mit
  Qt-Swaps, Physikbatches und ohne Workerfehler; anschließend alle
  Referenzdateien weiterhin unverändert. Je 3 s nach 1 s Warmup:
  ausdrücklich **keine** Performancebaseline.

## U-V0.10-000002: Einzelfunktionsinventar und erste Baselines

[Funktionsinventar](../Umsetzungsplan/Funktionsinventar_V0.10.json):
Nach genehmigter Teilrücknahme 271 spezifizierte Funktions-/Blockeinträge
und zusätzlich 27 erzeugte Closures, insgesamt 298 aktive Einträge.
Der ursprüngliche Messumfang enthielt 275 plus 27, insgesamt 302 Einträge.
Alle 25 Funktionsanforderungen
A-V0.10-00006 bis A-V0.10-00030 sind enthalten. Jeder benannte Eintrag
wird eindeutig gegen den AST seines Moduls aufgelöst, mit U-Zuordnung,
Quellhash, Profilzeile, bestehenden Regressionstestgruppen und geplantem
direktem Paritätsfall. Testgruppen sind kein vorgetäuschter direkter
C++-Paritätsnachweis.

Die [Profilzuordnung](M1_Kernbaseline_2026-10-19/funktionsmessungen.json)
enthält für 63/302 Einträge tatsächliche Aufrufzahlen, Eigen-/Gesamtzeit,
Aufrufer und Eingabegrößen aus instrumentierten Aufbau-, Worker- und
Statikläufen. Nicht beobachtete Funktionen bleiben offen. Innere Blöcke
derselben Funktion teilen lediglich deren Profilbeleg; diese Zeiten
werden nicht mehrfach addiert und nicht als Einzelblockzeiten ausgegeben.

Uninstrumentierte Kernbaseline, jeweils ein Warmup und drei Wiederholungen;
Angaben sind Mediane in Millisekunden:

| Modell | Warmer Modellaufbau | Workervorbereitung | 10 Schritte ohne IPC | Robuster statischer Solver |
|---|---:|---:|---:|---:|
| Optimist | 19,682 | 34,799 | 22,603 | 2160,229 |
| Folkeboot | 9,070 | 8,599 | 22,017 | 17,743 |
| yacht1 | 25,445 | 45,238 | 28,054 | 6,591 |

Rohdaten einschließlich P95, Spannweite und Standardabweichung:
[Optimist](M1_Kernbaseline_2026-10-19/optimist.json),
[Folkeboot](M1_Kernbaseline_2026-10-19/folkeboot.json),
[yacht1](M1_Kernbaseline_2026-10-19/yacht1.json).
Die wiederholten Workerresultate wurden exakt einschließlich benannter
Einzelkräfte/-momente und Frames verglichen. Solverzeiten enthalten
die vorhandene Suche; unterschiedliche Zeiten der Modelle sind kein
Sprachwechselgewinn. Die bestehende Kiel-Massenplausibilitätswarnung des
Folkeboots wurde nicht unterdrückt oder verändert.

## U-V0.10-000003: Vergleichs- und Berichtsharness

- Struktureller Vergleich von Feldern, Sequenzen, Datentypen, Arrayformen,
  Dataclasses, Beitragsnamen und Frames; keine NaN/Inf-Gleichheit.
- Ohne explizite feldbezogene Toleranz gilt exakte Gleichheit. Unbenutzte,
  negative oder nicht-endliche Toleranzen sind Fehler.
  Ganzzahlindizes bleiben exakt, auch jenseits der Float64-Ganzzahlauflösung.
- Mutationen von Kraftwert, Frame, fehlendem Beitrag, Beitragsname,
  Rotation, Arrayform, Float-Datentyp und NaN werden tatsächlich abgewiesen.
- Fehlende Zeitrohwerte sind Fehler, keine Nullwerte. Mindestens drei
  Wiederholungen; Median/P95/Streuung und absolute/prozentuale Einsparung
  sowie Faktor sind auswertbar. Der Zeitvergleich allein erteilt weder
  Paritäts- noch Produktivfreigabe.
- Neue Belegdateien werden nicht überschrieben. Fehler in Messfunktionen
  oder Unterprozessen werden durchgereicht; ein fehlgeschlagener Lauf
  erhält keinen Abschlussnachweis.
- Native Vergleichsfälle bleiben bis zur jeweiligen Implementierung
  geplante Pflichtprüfungen, nicht bestandene oder übersprungene Tests.

## Reproduktion

Aus dem Repository-Hauptverzeichnis, neue Ausgabeziele verwenden:

```powershell
.\.venv\Scripts\python.exe werkzeuge\migration_inventar.py --referenzmanifest --output <neues-manifest.json>
.\.venv\Scripts\python.exe werkzeuge\migration_inventar.py --output <neues-inventar.json>
.\.venv\Scripts\python.exe werkzeuge\migration_baseline.py --art kern --output <neuer-kernmessordner>
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe werkzeuge\pruefe_genauigkeit_v09.py
```

Nach jedem Befehl den Exitcode prüfen; Fehler sperren die Fortsetzung.
Die Platzhalter stehen für noch nicht existierende Ausgabeziele.

Die sichtbare Messreihe wird getrennt und ohne parallele schwere Last
ausgeführt:

```powershell
.\.venv\Scripts\python.exe werkzeuge\migration_baseline.py --art live --output doc\WegZuV1.0\Revisionslog\zuV0.10\Messungen\M1_Livebaseline_Fixviewport_2026-10-19
```

Sie umfasst drei Wiederholungen je Modell und Optik, insgesamt 18
eigenständige Windows-QPA-Läufe mit jeweils 30 s Warmup und mindestens
300 s Messdauer. Standardoptik und vorhandener Schulungsmodus bleiben
getrennt; die Renderkonfiguration muss über Wiederholungen identisch sein.
Der Render-Viewport ist ausdrücklich auf 640 × 480 Pixel festgelegt und
wird nach dem Warmup und am Ende geprüft. Die Vorgabe betrifft nur den
Messaufbau, nicht die reguläre GUI; gleiche Maße sind für spätere
Kandidatenmessungen verpflichtend.
Der Runner setzt keine verringerte Physik-/Anzeigenqualität voraus und
verweigert ungültige Läufe, fehlende Messgrößen oder geänderte Referenzdaten.
Die Qt-Swaprate und Eingabelatenz bleiben Softwareproxies, kein
Scanout-/Photonennachweis.

## Offene M1-Gates

1. Die ursprüngliche 18-Lauf-Messreihe unter
   `M1_Livebaseline_2026-10-19` wurde beim achten Lauf korrekt am
   Vergleichsgate abgebrochen: Optimist/Schulungsmodus hatte statt
   929 × 828 nun 491 × 828 Viewportpixel. Alle acht Einzelberichte bleiben
   erhalten; sie bilden **keine vergleichbare Gesamtbaseline**.
   Ursache im Messharness: Der Viewport wurde beobachtet, aber nicht
   fixiert; vom Fensterlayout abhängige Größen waren möglich.
   Korrektur: optionale feste Viewportvorgabe im GUI-Benchmark, im
   M1-Runner verpflichtend 640 × 480. Zwei sichtbare Smoke-Läufe im
   betroffenen Modus hatten danach identische Viewports und Renderzustände
   ohne Workerfehler; ungültige Vorgaben/abweichende Viewports werden
   zusätzlich automatisiert abgewiesen.
   Die neue vollständige Messreihe unter
   `M1_Livebaseline_Fixviewport_2026-10-19` ist inzwischen abgeschlossen:
   **18/18 Läufe** erfolgreich, jeweils mindestens 300 s nach 30 s
   Warmup, keine Workerfehler und keine automatische Überlastpause.
   Alle Wiederholungen jeder Modell-/Optikgruppe haben identische
   Renderzustände und einen Viewport von 640 × 480 Pixeln.
   Alle Referenzdateien sind nach Abschluss unverändert.
   [Auswertung mit Einzelwerten und Spannweiten](M1_Livebaseline_Fixviewport_2026-10-19/auswertung.json).
   Alte Rohdaten wurden nicht mit neuen vermischt; keine Gates gelockert.
2. Stationärer Solver, generische Körper, Kinematik und optionale Pfade
   haben inzwischen Aufrufbelege. Alle relevanten Farb-/Layer- und
   Instrumentvarianten bleiben gesondert nachzuweisen.
3. Kalter Aufbau, Prozesskosten, Pause/Weiter/Moduswechsel,
   30-/120-s-Zustandsfolgen und Beladungsänderungen samt Rückstellung
   sind inzwischen nachgewiesen. Offen bleiben insbesondere sichtbare
   Gelenk-/Änderungslatenzen und Modellwechsel/Schließen unter Last.
4. Native Bibliotheksanteile und
   tatsächliche Zeitkritikalität je Block entscheiden, ohne aus fehlenden
   Aufrufen auf Irrelevanz zu schließen.
5. Direkte blockbezogene Vergleichsfälle und unveränderte fachliche
   Toleranzen vervollständigen; anschließend M1 gemeinsam abnehmen.

Dieser Teilstand erfüllt weder die vollständige Inventarbewertung nach
A-V0.10-00001 noch den Gewinn-/Migrationsabschluss nach A-V0.10-00032 bis
A-V0.10-00034. Daher noch kein Abschluss dieser Anforderungen im Projektlog.

## Ergebnis der sichtbaren Python-Baseline

Je Zelle Median der drei Laufkennwerte; Frame-/Eingabespalten sind
damit Mediane der jeweiligen Lauf-P95, keine zusammengefassten P95.
Einzelwerte und Minimum/Maximum bleiben in der verlinkten Auswertung.

| Modell | Optik | Qt-Swaps/s | Frame-P95 ms | Eingabeproxy-P95 ms |
|---|---|---:|---:|---:|
| Optimist | Standard | 16,49 | 93,018 | 62,087 |
| Optimist | Schulung | 23,42 | 62,890 | 50,480 |
| Folkeboot | Standard | 22,60 | 73,252 | 56,081 |
| Folkeboot | Schulung | 29,64 | 52,431 | 46,197 |
| yacht1 | Standard | 15,49 | 98,735 | 64,941 |
| yacht1 | Schulung | 23,99 | 62,929 | 50,635 |

Das sind ausschließlich Ausgangswerte, kein C++-Gewinn. Die
30-Swap/s-Zielmarke wird in diesen Gruppenmedianen nicht erreicht;
die Standardoptik überschreitet auch 67 ms Frame-P95. Alle
Gruppenmediane des Eingabeproxies liegen unter 100 ms.
Gültige Baselines setzen keine bereits bestandenen Leistungsziele voraus.
Mit früheren Messungen bei anderen Viewports nicht unmittelbar vergleichen.
M1 bleibt wegen der übrigen oben genannten Pflichtfälle offen.

## Fortsetzung: Dynamik, Prozesskosten und gezielte Aufruflücken

Abschließende Regression dieses Teilstands: **846 bestanden, 1 vorhandener
Windows-Symlink-Skip**. Eingefrorener exakter Hydrostatikreplay bestanden.
Dokumentlinks, zehn Profilquellen und unveränderte Referenzdateien geprüft.
Branch weiterhin `v0.10`; kein zusätzlicher Commit, Push oder Tag.

### Tatsächlich zusätzlich ausgeführte Nachweise

- [30-s-Dynamikreferenzen](M1_Dynamik_2026-10-19/teillauf_abgeschlossen.json):
  Optimist, Folkeboot und yacht1 jeweils drei Läufe mit Originalzeitschritt
  0,004 s, also je 7.500 Schritten. Ausgangspunkt ist das statische
  Gleichgewicht mit 5 Grad zusätzlichem Roll, 2 Grad Nick und 0,01 m
  zusätzlicher Höhe. Alle drei Wiederholungen eines Modells waren an
  jedem Zeitpunkt exakt identisch, einschließlich benannter Wrenches,
  Bezugspunkte und Frames. Anfangszustand und vollständige Zustandsfolge
  liegen als Float64-Arrays vor; variable Beitragslisten sind ohne
  Null-Padding über Schema-/Offsetarrays gespeichert.
- Metadaten, Eingabehashes und Binärhashes:
  [Optimist](M1_Dynamik_2026-10-19/optimist.json),
  [Folkeboot](M1_Dynamik_2026-10-19/folkeboot.json),
  [yacht1](M1_Dynamik_2026-10-19/yacht1.json).
  Die komprimierten NPZ-Dateien wurden nach dem Schreiben ohne Pickle
  wieder eingelesen. Nachträglich wurden Hashes, exakte Zeitachsen,
  Arrayformen, Endlichkeit, Quaternionnormen, Schemaindizes und
  Beitragslängen aller drei Dateien erneut geprüft.
- [Prozessmessungen](M1_Prozess_Verifiziert_2026-10-19/teillauf_abgeschlossen.json):
  je Modell drei Wiederholungen für Snapshot-/Antwort-Pickle,
  Serialisierung/Deserialisierung und warme 10-Schritt-Prozessroundtrips;
  außerdem Modellaufbau in drei jeweils neuen Interpretern. Prozessstart
  und erster Batch separat. Keine Betriebssystem-Dateicaches gelöscht.
  Prozess- und Direktresultate waren exakt gleich, einschließlich
  sämtlicher Einzelwrenches.
- [Stationäre Wiederholungen](M1_Stationaer_2026-10-19/teillauf_abgeschlossen.json):
  die bereits vorhandenen Testprofile für yacht1 und Platte wurden
  jeweils nach Warmup dreimal gelöst und dreimal dynamisch für 10 s
  nachgeprüft. Alle Nachprüfungen bestanden; Resultate ohne Laufzeitfelder
  waren exakt reproduzierbar. Optimist/Folkeboot haben kein konfiguriertes
  stationäres Testprofil; dies ist ausdrücklich dokumentiert, nicht durch
  erfundene Kräfte ergänzt.
- [Fachliche Regressionsprofile](M1_Regressionsprofile_2026-10-19/regressionen.json):
  733 Tests bestanden, ein vorhandener Windows-Symlink-Skip.
  Instrumentiert, daher keine Performancebaseline.
- [Gezielte zusätzliche Referenzpfade](M1_Referenzpfade_Vollstaendig_2026-10-19/regressionen.json):
  18 Tests bestanden, unter anderem Polygonclip, Konturpunktprüfung,
  skalare Schnittprädikate, Meshfläche, relative Pose, Wasserinterpolation
  in drei Größen, Isofläche mit bestehendem Zweiframecache und echte
  VTK-Bildschirm-/Wasserkameratransformation.
- Sichtbare Lifecycleprofile:
  [Optimist](M1_GUI_Lifecycleprofile_2026-10-19/optimist.json),
  [Folkeboot](M1_GUI_Lifecycleprofile_2026-10-19/folkeboot.json),
  [yacht1](M1_GUI_Lifecycleprofile_2026-10-19/yacht1.json).
  Jeweils Pause, Fortsetzung, Wechsel zur Statik und zurück zur Echtzeit
  in richtiger Reihenfolge, ohne neue Zeitanforderung während der Pause,
  ohne Workerfehler. Kurze instrumentierte Diagnoseläufe, nicht mit den
  300-s-Performancebaselines vermischt. Die unter Instrumentierung
  beobachteten Überlastbeobachtungsmodi sind keine unbeeinflussten
  Leistungswerte.

Median der warmen 10-Schritt-Prozessmessung in Millisekunden:

| Modell | Roundtrip | Workerrechnung | Snapshot-Pickle in Bytes |
|---|---:|---:|---:|
| Optimist | 11,898 | 11,265 | 126272 |
| Folkeboot | 12,413 | 11,749 | 33587 |
| yacht1 | 21,515 | 20,920 | 301426 |

Roundtrip minus Worker ist ausdrücklich nicht reine IPC-Zeit; enthalten
sind Queue, Scheduling, Transport und Pickle. Datenaufbereitung der
Dynamikfolgen wird ebenfalls nicht als reine Physikzeit ausgegeben.

Die erste Prozessmessung wurde beim Folkeboot durch eine bereits
vorhandene Plausibilitätsausgabe auf stdout als JSON-Protokollfehler
abgebrochen. Die Meldung wird im Kindprozess nun auf stderr ausgegeben,
nicht unterdrückt. Der Fehlerweg ist automatisiert getestet; die
vollständige Ersatzserie ist oben verlinkt. Die Teilserie bleibt als
abgebrochener Nachweis erhalten.

### Kumulierte Funktionsbelege und tatsächlicher Blocker

[Funktionsnachweise](../Umsetzungsplan/Funktionsnachweise_V0.10.json):
**302/302 Inventareinträge haben einen Aufrufbeleg**, auf zehn explizit
angegebene Rohprofile mit Hashes zurückführbar. Dies umfasst ausdrücklich
Fehlerfälle und ist weder 302-mal bestandene numerische Parität noch
eine pauschale Feststellung von Zeitkritikalität.

Vier in der Spezifikation benannte Legacy-Rendererfunktionen importieren
das bereits im Referenzcommit nicht vorhandene Modul
`segelphysik.core.bodies`:

| Anforderung | Funktion | Beobachteter Bestand |
|---|---|---|
| A-V0.10-00027 | `PyVistaRenderer._update_ring` | `ModuleNotFoundError` vor numerischer Ausführung |
| A-V0.10-00027 | `PyVistaRenderer._clamp_to_bodies` | `ModuleNotFoundError` vor numerischer Ausführung |
| A-V0.10-00027 | `PyVistaRenderer.update` | `ModuleNotFoundError` vor numerischer Ausführung |
| A-V0.10-00029 | `PyVistaRenderer._body_half_height` | `ModuleNotFoundError` vor numerischer Ausführung |

Diese Fälle sind gezielt getestet und nicht durch einen erfundenen
`Sphere`-Ersatz repariert. Der aktive GrafikBruecke-Pfad funktioniert
weiterhin; die sichtbaren Nachweise belegen das. Eine Wiederherstellung
des alten Körper-/SPH-Renderers wäre zusätzliche Funktionalität, keine
reine C++-Performanceübertragung.

**Nachfolgende Nutzerentscheidung:** Nur diese vier nicht ausführbaren
Altpfade werden unter den ursprünglichen A-IDs in „Nicht umsetzen“
archiviert. Die übrigen Teile von A-V0.10-00027 und A-V0.10-00029
bleiben aktiv; kein Quellcode und keine Referenzdaten wurden verändert.
Das aktualisierte Inventar und die daraus neu abgeleitete Belegmatrix
enthalten **298/298 aktive Einträge mit Aufrufbeleg** (271 benannte
Einträge und 27 Closures). Die zehn Rohprofile bleiben unverändert;
die vorherigen 302 beziehen sich auf den historischen Umfang.

### Damals offene M1-Punkte

- Die vollständige Bewertung der Zeitkritikalität und nativen
  Bibliotheksanteile je Block; Aufrufbelege allein reichen nicht.
- Vollständige Zuordnung direkter Szenarien/Toleranzen; die nachfolgenden
  Beladungs- und 120-s-Fälle ergänzen, ersetzen aber nicht alle Direktfälle.
- Zeitbewertung der inkonsistenten Thread-/GUI-Profile durch geeignete
  getrennte Messungen ersetzen; Aufrufbelege bleiben reine Aufrufbelege.
- Modellwechsel/Schließen unter Last und alle relevanten
  Darstellungs-/Instrumentvarianten als explizite Messfälle.

Keine Anforderung wird bereits als vollständig nach C++ übertragen
markiert. Keine Folgeintegration vor M1-Gate und keine automatische
Produktivumschaltung oder Veröffentlichung.
Die nachfolgenden Fortsetzungen schließen einzelne dieser Restpunkte;
die aktuelle Restliste steht am Dokumentende.

## Fortsetzung nach genehmigter Teilrücknahme

### 120-s-Dynamik und Schwingungskennwerte

[Vollständige 120-s-Serie](M1_Dynamik_120s_2026-10-19/teillauf_abgeschlossen.json):
alle drei Boote, jeweils Warmup und drei vollständige Wiederholungen,
jeweils **30.000 Schritte mit unverändertem dt = 0,004 s**. Alle
Zustände, Einzelkräfte/-momente, Schemas und Frames sind innerhalb jedes
Modells exakt reproduzierbar. Gespeicherte NPZ-Dateien wurden separat
mit SHA256, vollständiger Zeitachse, Datentypen, Formen, Beitragslängen
und Quaternionnorm geprüft.

Die [verifizierte Schwingungsauswertung](M1_Dynamik_120s_2026-10-19/schwingungsauswertung_verifiziert.json)
weist messbare und nicht messbare Größen getrennt aus. Perioden entstehen
aus gleichgerichteten interpolierten Nulldurchgängen nach Abzug der
unveränderten statischen Gleichgewichtslage. Abklingen wird nur ausgewiesen,
wenn mindestens zwei aufeinanderfolgende Betragsmaxima unter 1/e der
Anfangsamplitude liegen und im verbleibenden Fenster keine Überschreitung
mehr folgt. Keine Glättung, erzwungene Periodizität oder Erfolgsnullwerte.

| Modell | Rollperiode, Median / s | Rollabklingen / s |
|---|---:|---:|
| Optimist | Nicht messbar: kein ausreichender Gleichgewichtsdurchgang | Im Fenster nicht messbar |
| Folkeboot | 0,807063 | 2,920 |
| yacht1 | 0,917179 | 7,268 |

Die Kennwerte beschreiben den vorhandenen gekoppelten Referenzlauf, nicht
eine unabhängige Bestätigung der physikalischen Modellgüte oder eine
einzelne entkoppelte Eigenmode. Vollständige Einzelperioden und Maxima
bleiben im Bericht verfügbar; der Median allein ist kein Paritätsgate.

Bei der nachgelagerten Plausibilitätsprüfung wurde ein Fehler der neuen
Auswertung erkannt: Der Optimist-Solver liefert einen äquivalenten
Gleichgewichtsrollwinkel auf einem anderen 2π-Ast. Die anfängliche
Auswertung zog diesen vom Hauptwert des Quaternion-Rollwinkels ab.
Die Auswertung richtet jetzt beide auf denselben Winkelast aus; Tests
für 0, ±2π und 4π verhindern die Wiederholung dieses Fehlers.
**Die verifizierte Auswertungsdatei ersetzt das Feld
`schwingungskennwerte` der ursprünglichen drei Modellberichte.**
Diese bleiben als historische Rohberichte erhalten. Zustands-/Kraftfolgen,
Zeitmessungen und ihre Hashes wurden nicht geändert oder neu erzeugt.

### Beladungsänderungen und Rückstellung

[Optimist](M1_Aenderungen_2026-10-19/optimist.json),
[Folkeboot](M1_Aenderungen_2026-10-19/folkeboot.json),
[yacht1](M1_Aenderungen_2026-10-19/yacht1.json):
**47 tatsächlich ausgeführte Modellfälle**, jeweils drei Wiederholungen
nach Warmup. Für jedes Boot mit bestehender Punktmasse: 80/100/120 %
der Ausgangsmasse, kombiniert mit Ausgangsposition und ±0,2 m auf jeder
Achse (21 Kombinationen), dazu Ausgangsfall und vollständige Rückstellung.
Snapshots und Zehn-Schritt-Ergebnisse einschließlich aller Wrenches wurden
exakt verglichen; auch die Rückstellung reproduziert den Ausgangsfall.
Aufbau, Workervorbereitung und Batch sind getrennt gemessen.

Nutzereinstellungen werden nur gelesen. Änderungen erfolgen in einer
isolierten temporären Einstellungsdatei, die danach entfernt wird;
Paketdaten bleiben unverändert. Tests prüfen insbesondere die Verwendung
tatsächlicher Ausgangseinstellungen, vollständige Kombinationen,
Rückstellung und die Weitergabe von Workerfehlern.

yacht1 definiert keine Punktmasse; keine neue Beladung wurde erfunden.
Die drei aktuellen Bootmodelle definieren auch keine Laufzeitgelenke.
Die generische Gelenkfunktion bleibt aktiv: Der bestehende reale
Gelenk-/Darstellungstest ist in den Regressionen enthalten. Der neue
Orchestrierungstest prüft Änderung und Rückstellung mit einem gezielten
Testkörper; dies ist kein gemessener GUI-Gelenkfall eines dieser Boote.

### Python-/Native-Anteile der Profile

Die [Funktionsnachweise](../Umsetzungsplan/Funktionsnachweise_V0.10.json)
enthielten zu diesem Teilstand 16 getrennte Profilbewertungen, exklusive Anteile je
belegtem Funktionseintrag und einzeln zugeordnete direkte native
Unteraufrufe. Native Kanten werden dem direkten Aufrufer zugeordnet,
nicht allen transitiven Eltern zugeschlagen. Gesamtzeiten überlappender
Funktionen, mehrfach referenzierter Funktionen und unterschiedlicher
Szenarien werden nicht addiert.

Instrumentierte Zehn-Schritt-Workerprofile:

| Modell | Exklusive Projekt-Pythonzeit / Profil | Exklusive native Profilrahmen / Profil |
|---|---:|---:|
| Optimist | 42,4 % | 22,4 % |
| Folkeboot | 41,8 % | 21,3 % |
| yacht1 | 52,4 % | 21,1 % |

Die übrigen Anteile liegen unter anderem in Python-Bibliotheken und
Messrahmen. „Nativ“ umfasst CPython, I/O und Warten, nicht nur numerische
Bibliotheken; direkte native Kanten sind kein vollständiger transitiver
Bibliotheksanteil. Beispielsweise benötigt
`HydrodynamikModell.beitraege_erzeugen` allein 10,9/8,4/24,5 % der
exklusiven Worker-Profilzeit (Optimist/Folkeboot/yacht1). Das begründet
eine Kandidatenpriorität, aber weder einen C++-Gewinn noch eine Abnahme.

**Explizite Messsperre:** Das allgemeine Regressionprofil und alle drei
GUI-Lifecycleprofile enthalten inkonsistente cProfile-Zeilen mit
Gesamtzeit kleiner als Eigenzeit, insbesondere bei Thread-/Qt-Rahmen.
Die Rohdaten bleiben unverändert, die Anomalien sind einzeln aufgeführt.
Diese vier Profile sind als Zeitbewertung gesperrt; Funktionsanteile
werden dort nicht als gültige Zahlen ausgegeben. Ihre Aufruf- und
bestandenen Verhaltensbelege werden dadurch nicht in Performancenachweise
umgedeutet. Die uninstrumentierte 18-Lauf-Livebaseline ist davon getrennt.

### Threadlokale sichtbare Callbackdiagnosen

[18 vollständige Läufe](M1_GUI_Callbackprofile_Threadlokal_2026-10-19/auswertung.json):
drei Boote, Standard-/Schulungsdarstellung, jeweils drei Wiederholungen.
Alle Lifecycle-Gates bestanden; keine inkonsistenten Profilzeiten.
Je 15 s nach 2 s Warmup, ausdrücklich instrumentierte Diagnose und keine
300-s-Performancebaseline.

Auch synchron begrenztes `cProfile.enable()/disable()` erfasste in dieser
Python-/Qt-Umgebung fremde Workerthreads und erzeugte inkonsistente Zeiten.
Die abgebrochene Callbackserie bleibt als Fehlernachweis erhalten.
Der Ersatz verwendet den threadlokalen Standardbibliotheksprofiler
`profile.Profile` mit einem neuen Teilprofil je synchronem Aufruf.
Nur abgeschlossene Teilprofile werden aggregiert; Wartezeit zwischen
Callbacks geht nicht als synthetische Pythonzeit ein. Verschachtelte
Aufrufe werden vom äußeren Profil erfasst, nicht doppelt aktiviert.
Native Aufrufkanten dieses Profilers enthalten Aufrufzahlen, jedoch keine
Kantenzeiten; fehlende Zeiten bleiben `null`, nicht erfundene Nullwerte.

### Modellwechsel und Schließen bei ausstehendem Workerresultat

[18 reale Lastfälle](M1_GUI_Last_2026-10-19/auswertung.json):
drei Boote, Modellwechsel und Schließen, jeweils drei Wiederholungen.
Das erste **wirklich berechnete** Physikresultat wird unmittelbar vor
seiner Qt-Signalzustellung angehalten. Bei tatsächlich ausstehendem
Auftrag wird gewechselt bzw. das sichtbare Fenster geschlossen.
Anschließend wird genau dieses unveränderte Resultat zugestellt.

In allen Fällen steigt die Generation und das veraltete Resultat
verändert weder Zustand, Kräfte noch berechnete Simulationszeit.
Nach Modellwechsel müssen zusätzlich neue Physikzeit und ein echter
Qt-Swap auftreten. Beim Schließfall wird das Fenster ausdrücklich vor
dem Warten auf den Worker geschlossen; der bisherige Benchmark-Cleanup
allein wäre kein solcher Lasttest. Signal-/Threadfehler und Timeouts
sperren den Nachweis. Dies prüft die kontrollierte Zustellrace, nicht
den Abbruch einer gerade laufenden nativen Rechnung.

### Darstellungs- und Instrumentvarianten

[Optimist](M1_GUI_Varianten_3D_2026-10-19/optimist.json),
[Folkeboot](M1_GUI_Varianten_3D_2026-10-19/folkeboot.json),
[yacht1](M1_GUI_Varianten_3D_2026-10-19/yacht1.json):
je **308 Fälle mit drei exakt gleichen Wiederholungen**, insgesamt
924 unterschiedliche Referenzfälle bzw. 2772 Ausführungen.

- Alle 256 Kombinationen der acht bestehenden Layer.
- Vier Standardstilkombinationen: Vordergrund an/aus und gestrichelt an/aus.
- Alle 16 Instrument-Sichtbarkeitskombinationen, jeweils normale,
  ungültige Quaternion- und Gefahrenlage: weitere 48 Fälle.
- Echte Qt-/VTK-Szene mit festem 640 × 480-Viewport, unveränderte Pose.
  Hashvergleich sämtlicher 3D-Actor-Geometrie und Punkt-/Zellattribute,
  vollständige Transformationsmatrix, Sichtbarkeit, Farbe und Stil.
  Instrumente über ihre vollständigen SVG-Bytes verglichen.

Keine Behauptung aller stetigen Farb-/Größenwerte oder aller Kreuzprodukte
von Stil und Layer. Instrumentierte Fallzeiten einschließlich Qt-Swap-Warten
sind keine Performancebaseline. 2D-Textactoren besitzen keine 3D-Matrix:
Die erste Serie scheiterte korrekt an diesem neuen Snapshotfehler; die
Ersatzserie vergleicht ausdrücklich die 3D-Actor-Geometrie und separat die
SVG-Instrumente. Der ursprüngliche Abbruch bleibt nachvollziehbar.

### Konkrete Referenztests je aktivem Funktionseintrag

[Vollständige Testprofile](M1_Testmatrix_Vollstaendig_2026-10-19/testprofile.json):
**772 bestandene Fach-/Referenztests, ein bestehender Windows-Symlink-Skip**.
Die tatsächlichen Test-Call-Phasen wurden einzeln threadlokal profiliert;
Fixtureaufbau und fremde Threads sind nicht Bestandteil dieser Profile.
Nur aufgerufene Funktionen in bestandenen Call-Phasen zählen als Beleg.
Die Rohdatei enthält die Hashes der tatsächlich verwendeten Testmodule.

[Konkrete Funktions-Testmatrix](../Umsetzungsplan/Funktions_Testmatrix_V0.10.json):
**298/298 Einträge** sind einem tatsächlich bestandenen parametrisierten
Testfall zugeordnet. Rohprofilhash, sämtliche Testquellenhashes und die
vollständige Wiederableitung dieser Matrix wurden unabhängig geprüft.
Ein Aufruf beweist nicht jeden internen Zweig oder jeden Rückgabewert.
Alle nativen Vergleiche bleiben deshalb ausdrücklich `false`; diese
Zuordnung ist keine native Paritäts- oder Performanceabnahme.

Drei ergänzte Referenztests prüfen einen echten synchronen Workerbatch
gegen denselben Prozessbatch, den bestehenden Segelwinkelvertrag sowie
echte PyVista-Farbgruppen und Schwerpunkte. Bestandsbesonderheit:
`add_mesh(smooth_shading=True)` erzeugt bei der Actor-Erstanlage Normalen,
während ein späteres `SetInputData(mesh)` andere Meshattribute besitzt.
Erstanlage und stabiler Updatepfad werden getrennt geprüft; wiederholte
Updates sind exakt gleich. Kein Produktivverhalten wurde dafür verändert.

[Kumulierte Profilmatrix](../Umsetzungsplan/Funktionsnachweise_V0.10.json):
31 unveränderte Rohquellen mit 37 Profilbewertungen, davon 33 zeitlich
gültig. Die vier alten inkonsistenten Profile bleiben gesperrt. Alle
298 aktiven Einträge haben weiterhin einen Aufrufbeleg.

### Speicherentwicklung und noch offene Gates

A-V0.10-00032 fordert auch Speicherentwicklung. Die bisherigen vollständigen
Livebaselines enthalten diese Zeitreihe nicht und werden nicht nachträglich
mit erfundenen Daten ergänzt. Der Benchmark erfasst jetzt sekündlich
Working Set und Private Bytes des GUI-Prozesses und jedes eigenen
Physikprozesses über die Windows-Prozess-API, ohne neue Abhängigkeit.
Zähler-/Prozessfehler werden als Messfehler weitergegeben.

[Sichtbarer Speicher-Smoke](M1_Speicher_Smoke_2026-10-19.json):
15 s mit echtem Physikprozess erfolgreich; **148 gezielte Harness-,
Szenario- und Referenztests bestanden** vor diesem Smoke. Ein anschließend
ergänzter Fremdthread-Abgrenzungstest ist darin noch nicht enthalten.
Die vollständige neue Serie läuft getrennt ohne parallele schwere Last
unter `M1_Livebaseline_Speicher_2026-10-19`: erneut 18 Läufe, je 300 s nach
30 s Warmup, unveränderte Optik und 640 × 480. Erst ein Abschlussmarker
und die Prüfung sämtlicher Einzelberichte gelten als vollständiger Nachweis.

Die Serie wurde nach zehn gültigen Einzelberichten beim elften Bericht
korrekt abgewiesen: yacht1/Standard, Wiederholung 2, hatte trotz echter
Physikbatches und VTK-Renderereignissen **keinen einzigen Qt-Swap** und
keine messbare Eingabereaktion. Kein Schluss auf eine bestimmte
Desktop-/Treiberursache und keine Umdeutung von VTK-Ereignissen in Swaps.
Der [gezielte anschließende Swap-Smoke](M1_Speicher_Swapdiagnose_2026-10-19.json)
lieferte wieder 193 Qt-Swaps in 15 s.

Vor der Fortsetzung bestanden **901 Tests, ein bestehender Skip**, sowie
der exakte v0.9-Replay. Der Runner kann nun explizit benannte gültige
Einzelberichte erneut durch sämtliche Gates prüfen und unverändert
referenzieren. Doppelte/unbekannte Namen und ungültige Berichte werden
abgewiesen. Die zehn gültigen Berichte werden so weiterverwendet; der
ungültige Bericht bleibt unverändert und wird nicht als Erfolg referenziert.
Die acht fehlenden/ersetzten Messungen laufen unter
`M1_Livebaseline_Speicher_Fortsetzung_2026-10-19`. Dessen Quellenmanifest
verknüpft erst nach vollständigem Erfolg alle 18 Berichte mit Hashes.
Weitere danach ergänzte Prüfplan-Tests sind nicht im 901er-Teststand enthalten.

Der [Einzelfunktions-Prüfplan](../Umsetzungsplan/Funktionspruefplan_V0.10.json)
führt je Eintrag originale Testdefinition/Parametrisierung mit Zeilen und
Hash, Modell-/Viewportgrößen aus Rohberichten, Aufrufer und getrennte
Eigen-/Gesamtzeiten zusammen. Die höchste beobachtete exklusive Quote
ist ausdrücklich szenariobezogen, keine globale Hotspotklassifikation.
Fehlen separate Szenariozeiten, werden gültige Einzeltestprofile als
Diagnose ausgewiesen; die Elternblock-Performance bleibt dann Pflicht
des jeweiligen Kandidaten. Der Vergleich bleibt standardmäßig exakt;
vorhandene fachliche Grenzen stehen in den unveränderten zugeordneten
Tests und werden nicht aus Kandidatenergebnissen abgeleitet.

Aktuelle Restgates:

1. Vollständige Speicher-Livebaseline abschließen und auswerten.
2. Je Block konkrete Eingabegrößen und vorhandene Toleranz-/Testquellen
   zusammenführen; instrumentierte Eigenzeit-/Bibliotheksanteile
   szenariobezogen bewerten, nicht alle 298 Einträge pauschal als Hotspot.
3. Erneute Vollsuite und eingefrorenen Referenzreplay nach den Ergänzungen
   ausführen; alle Referenzdateien und Nachweishashes prüfen.

### M1-Abschlussprüfung

Die unmittelbar zuvor genannten Restgates sind inzwischen geprüft:

- **909 Tests bestanden, ein vorbestehender Windows-Symlink-Skip**,
  anschließend exakter v0.9-Replay erfolgreich.
- [18/18 vollständige Speicher-Livebaselines](M1_Livebaseline_Speicher_Fortsetzung_2026-10-19/liveberichte.json)
  mit je mindestens 300 s nach 30 s Warmup, drei Wiederholungen je
  Modell/Optik, unverändertem 640 × 480-Viewport und identischer Gruppenoptik.
  Alle Einzelberichte erneut durch sämtliche Gates und Hashprüfungen geprüft.
- [Speicherauswertung](M1_Livebaseline_Speicher_Fortsetzung_2026-10-19/speicherauswertung.json)
  getrennt je GUI-/Physikprozess: Start, Ende, Maximum und Differenz
  für Working Set und Private Bytes. Working Sets enthalten gemeinsame
  Seiten und sind kein addierbarer physischer Gesamtverbrauch.
  Die begrenzten Zeitfenster sind kein langfristiger Leakbeweis.
- 298/298 aktive Einträge mit konkreten Originaltest-/Eingabequellen
  sowie gültiger, getrennt ausgewiesener Zeitdiagnose:
  152 über Szenarioprofile, weitere 146 über individuelle Referenztestprofile.
  Kleine Testanteile begründen keine pauschale Irrelevanz. Der native
  Elternblock muss seinen reproduzierbaren End-to-End-Gewinn später
  selbst belegen. Bestehende Testtoleranzen nicht global übernommen.
- Vollständiger Funktionsprüfplan erneut exakt aus seinen Quellen
  reproduziert; sämtliche 116 Referenzdateien weiterhin unverändert.
  Die vier alten inkonsistenten Zeitprofile bleiben gesperrt.

Damit sind U-V0.10-000001 bis U-V0.10-000003 als Referenz-/Harnessaufbau
abgeschlossen. **M2 beginnt ohne weitere Zwischenfreigabe.**
Keine bereits migrierte Rechenfunktion, native Produktivfreigabe,
zusätzlicher Commit, Push oder Tag wird damit behauptet.
