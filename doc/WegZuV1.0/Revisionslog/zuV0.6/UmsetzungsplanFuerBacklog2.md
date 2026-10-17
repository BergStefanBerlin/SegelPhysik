# Umsetzungsplan für Backlog 2 – ideale Punkte

**Stand:** 17.10.2026
**Backlog:** [Backlog v1](../../../Backlog/Backlog_v1.md)
**Umfang:** BL5 (Solver findet stabile prismatische Gleichgewichtslage) und
BL6 (generische Geometrie-Importinfrastruktur). Diese Arbeiten sind empfohlen, aber
keine Voraussetzung für die Hydrodynamik. BL5 ist ausschließlich eine
gezielte Korrektur des bereits implementierten statischen
Auftriebs-/Gleichgewichtssolvers. BL6 ist ausschließlich generische
Import-Infrastruktur für Geometrie und vorhandene Material-/Massendaten;
dieser Plan fügt keine neuen physikalischen Modelle, Kraftgesetze oder
Simulationsbeiträge hinzu.

## 0. Verbindliche Abgrenzung

Die Nutzerfreigabe gilt für die Auftriebssimulation und physikalische Teile,
die bereits implementiert sind. Daher darf BL5 einen reproduzierten Fehler
im bestehenden hydrostatischen Solver beheben. Dabei werden keine neuen
physikalischen Annahmen oder Kräfte eingeführt; die vorhandene
Auftriebssimulation bleibt Referenz.

BL6 darf allgemeine Modell-/Geometrie-Importverträge und deren Validierung
vorbereiten oder vervollständigen. Es werden keine neuen Beispiel-Yachten,
Rümpfe, Segel, hydrodynamischen Datensätze oder zusätzlichen
Simulationsbeiträge erstellt. Tests verwenden synthetische Meshfixtures und
bereits vorhandene Modelle. Jegliche Änderung an Kraftberechnung,
Hydrostatiksemantik oder Aerodynamik liegt außerhalb des Umfangs von BL6.

## 1. Reihenfolge und Freigaberegel

| Reihenfolge | Backlog-ID | Zweck | Abhängigkeit |
|---:|---|---|---|
| 1 | BL5 | Stabile Gleichgewichtslagen bei Prismen zuverlässig finden | Bestehender exakter Hydrostatik- und Solverpfad |
| 2 | BL6 | Generische Geometrie sicher validieren und Importinfrastruktur vorbereiten | Manifest-/Paketverträge und Meshvalidierung |

Die Arbeitspakete sind fachlich unabhängig; die Reihenfolge ist eine
Priorisierung, keine technische Abhängigkeit. BL5 ist eine Fehlerkorrektur
des vorhandenen Auftriebssolvers, BL6 eine generische Import-Infrastruktur-
Vorbereitung. Keine physikalische Toleranz darf gelockert werden, um einen
Punkt als erledigt zu markieren. BL6 erweitert keine physikalische
Modellbibliothek und nimmt keine neuen Modelle in den produktiven Katalog auf.

## 2. BL5 – Stabile prismatische Gleichgewichtslagen

### Ausgangslage und Ziel – bestehende Auftriebssimulation

Der dokumentierte liegende Sechskantstab `bleistift` kann mit
„Störleiter erschöpft“ enden, obwohl eine stabile Lage bei einem Winkel außerhalb der bisherigen
Störstufen erwartet wird. Ausschließlich dieser bereits vorhandene
statische Solverpfad darf korrigiert werden. Der Solver muss stabile
Gleichgewichtslagen zuverlässig erkennen oder einen klaren, diagnostisch
korrekten Nichtkonvergenzstatus liefern. Ein instabiles Nullstellenresultat
darf nicht als stabile Lösung ausgegeben werden. Neue Auftriebs- oder
Widerstandsmodelle sind ausgeschlossen.

Reproduzierter Befund: Bei vertikalem Kräftegleichgewicht wechselt das
Rollmoment um `89,97°` das Vorzeichen; die lokale Momentenableitung ist
negativ. Die bisherige Störleiter bleibt dagegen an einer instabilen Lage
nahe `0°` hängen. Die Korrektur darf daher nur nach einem konvergierten,
aber instabilen Ergebnis einen begrenzten Winkel-Fallback nutzen.

### Arbeitsschritte

1. Bestehenden Fall reproduzieren; Anfangspose, Solverparameter,
   Kraft-/Momentenresiduum, Störleiter und Rückgabestatus als unveränderliche
   Regression erfassen.
2. Residuum und Stabilitätskriterium fachlich prüfen. Für den dokumentierten
   2D-Rollfall muss das Momentengleichgewicht numerisch nahe null liegen und
   die lokale Stabilitätsbedingung (Vorzeichen der Momentenableitung nach
   Winkel gemäß Projektkonvention) erfüllt sein.
3. Solverablauf und Form-/Symmetrieerkennung untersuchen, bevor ein neuer
   Algorithmus eingeführt wird. Winkelabtastung, Nulldurchgangssuche und
   stabilitätsgeprüfte Newton-Starts sind mögliche Ansätze, aber nur nach
   Messung des konkreten Fehlers.
4. Falls nach der Diagnose eine Winkelabtastung als Korrektur des bestehenden
   Solvers nötig ist: periodischen Bereich, Auflösung, mögliche
   Mehrfachgleichgewichte und Übergang zu 6-DOF eindeutig behandeln.
   Kandidaten an jeder gefundenen Nullstelle lokal verfeinern und die
   Stabilität unabhängig prüfen.
5. Diagnose für „kein Nullpunkt“, „nur instabile Gleichgewichte“,
   „mehrere stabile Gleichgewichte“ und „Abtastung/Verfeinerung
   fehlgeschlagen“ sichtbar und deterministisch machen.
6. Keine globale Solverstrategie ändern, wenn der Fehler durch einen
   begrenzten prismatischen Spezialfall behoben werden kann. Änderungen
   dürfen Kugelneutralität, bestehende stabile Körper und Nichtkonvergenz-
   Diagnosen nicht regressieren.

### Testfälle

- `bleistift` aus der dokumentierten Ausgangspose: stabile Lage wird
  gefunden oder ein fachlich korrekter, reproduzierbarer Fehlerstatus
  zurückgegeben; niemals eine instabile Lage als stabil ausgeben.
- Residuum am akzeptierten Gleichgewicht liegt innerhalb eines vorab
  gesetzten Kraft-/Momentenbudgets.
- Stabilität wird durch definierte kleine Winkelstörungen beidseits der
  Gleichgewichtslage geprüft.
- Synthetische Solvertests für periodische Winkel, Mehrfachnullstellen und
  Verfeinerungsgrenzen; dafür keine neuen physischen Modellpakete anlegen.
- Mehrere Gleichgewichte, Symmetrie-/Grenzwinkel, keine stabile Lage und
  nicht konvergierender Solverkandidat.
- Regressionen für Kugelneutralität, Instabilität, Stagnation und bereits
  konvergierende Formen.
- Wiederholung mit identischen Eingaben ergibt deterministischen Status und
  innerhalb der Baseline-Toleranz gleiche Lösung.

### Testanweisungen

Zuerst die bestehenden Solver-/Stabilitätstests und danach die vollständige
Suite aus dem Repository-Hauptverzeichnis ausführen:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_statisch.py tests\test_statisch_robust.py tests\test_statisch_kugel.py tests\test_rev_e.py
.\.venv\Scripts\python.exe -m pytest -q
```

Den bereits vorhandenen Fall `bleistift` zusätzlich über den
reproduzierbaren Projektpfad bzw. Benchmark ausführen und Solverstatus,
Endresiduum, Iterationen und Laufzeit protokollieren. Eine automatisierte
Regression darf die existierende Konfiguration referenzieren; dafür keine
neue physikalische Modellkonfiguration anlegen. Ein manueller Erfolg allein
reicht nicht.

### Abnahme

- Der Ausgangsfehler ist dauerhaft als automatisierter Test abgedeckt.
- Der Fall `bleistift` findet aus der dokumentierten Ausgangspose eine
  stabile Gleichgewichtslage innerhalb der vorab festgelegten Residuum- und
  Stabilitätsgrenzen. Eine Diagnose „keine stabile Lösung“ ist ein
  reproduzierbarer Fehlerbefund, aber kein erfolgreicher Abschluss von BL5.
- Falls eine stabile Lösung aufgrund eines reproduzierbaren fachlichen oder
  geometrischen Hindernisses nicht gefunden werden kann, bleibt BL5 offen/
  blockiert; die Ursache wird dokumentiert und es wird keine neue Physik
  ersatzweise eingeführt.
- Kein bestehender Solver- oder Körperfall regressiert.
- Laufzeit ist gegen denselben Ausgangsfall und dieselbe Konfiguration
  gemessen; eine signifikante Verschlechterung blockiert die Freigabe.

Umsetzung: Nach konvergiertem, aber instabilem 2D-Rollergebnis durchsucht
der Solver den periodischen Winkelbereich in 180 festen Intervallen,
bestimmt je Winkel das vertikale Gleichgewicht, verfeinert Momenten-
Nulldurchgänge und akzeptiert ausschließlich Kandidaten mit negativem
Rollmomentgradienten und geprüftem Residuum. Die vorhandene Störleiter und
der Sonderfall einer ausdrücklich leeren Störleiter bleiben erhalten. Ein
Regressionstest prüft das echte `bleistift`-Modell im `exakt_union`-Pfad.

## 3. BL6 – Generische Geometrie-Import-Infrastruktur, keine neuen Körpermodelle

### Ziel und Architekturgrenze

Die vorhandene Paket-/Manifestinfrastruktur soll generische, vordefinierte
Mesh-Geometrien sicher validieren und ihre Importmetadaten vorbereiten,
ohne einen zweiten Loader aufzubauen. Gegenstand sind Datenvertrag,
Dateipfade, Geometrievalidierung und – falls für den Importvertrag nötig –
die generische Übergabe an bestehende Laufzeitkörper-/Darstellungspfade.
Neue Geometrien dürfen ausschließlich synthetische Testfixtures sein; sie
werden nicht als neue Produktivmodelle, Beispiele oder Simulationsszenarien
registriert. Der vorhandene Paketkatalog und die bestehenden Modelle bleiben
unverändert. Es werden keine neuen physischen Modellpakete ausgeliefert und
keine neuen Kraft-/Auftriebsgesetze implementiert. Vor einer Codeänderung
ist festzulegen, wie die bisherige Beschreibung über `teile` in die aktuell
maßgebliche Paket-/Manifestarchitektur passt.

Bestandsprüfung: Der Repository-Code enthält bereits einen versionierten
Modellmanifest- und Paketloader für Form- und OBJ-Geometrie, sichere relative
Paketpfade, Meshvalidierung, die gemeinsame Fabrikpipeline sowie ein
Migrationswerkzeug mit Dry-run und Schutz vor Überschreiben. Die Test-Fixtures
decken synthetischen OBJ-Import, Pfad-/Meshfehler, Paketmigration und
Bestandsparität ab. BL6 verlangt deshalb keine parallele Importlogik; der
Plan wird nur dann wieder geöffnet, wenn ein konkreter ungedeckter
Importvertrag nachgewiesen wird.

### Arbeitsschritte

1. Unterstützte Importabläufe, Modellordner, Identitäten, Skalierung,
   Einheiten, Materialien/Dichten, Farben und Baumstruktur dokumentieren.
   Bestehende parametrische `koerper.json`-Modelle und das Yachtpaket nur als
   Kompatibilitätsreferenzen verwenden.
2. Datenvertrag festlegen: Paketwurzel, relative Geometriepfade, OBJ-Scale
   und Achsenabbildung, Materialquelle, Blatt-/Gruppensemantik sowie
   versioniertes Schema. Das Format muss zu bestehendem Loader und
   Migrationswerkzeug passen.
3. Vorhandene OBJ-Resolver und gemeinsame Meshvalidierung verwenden:
   sichere Paketpfade, geschlossene/orientierte Geometrie für Volumenmasse,
   positive Volumina, Selbstüberschneidung und Nullflächen gemäß aktuellem
   Vertrag. Keine stillschweigende Meshreparatur.
4. Material- oder Dichtewerte ausschließlich nach bestehendem Vertrag
   validieren; keine neue Materialphysik oder Kennwertberechnung definieren.
   Unvollständige und widersprüchliche Angaben mit Modell-/Knotenpfad melden.
5. Wenn eine Implementierung freigegeben wird, importierte Geometrie nur über
   dieselbe Laufzeitkörper-/Fabrikpipeline und den bestehenden
   Komponentenbaum anbinden. Übergabe in synthetischen Tests prüfen; keine
   neue Geometrie in den Produktivkatalog aufnehmen und keine neue
   physikalische Berechnung an den Importpfad koppeln.
6. Dry-run/Fehlerbericht und Nichtüberschreiben sicherstellen, soweit der
   Import neue Pakete oder Migrationen erzeugt. Quellen und bestehende
   Modellpakete unverändert lassen.
7. Bestehende Workflows erst nach Parität und Leistungsmessung erweitern;
   parametrische Formen bleiben unterstützt. Kein neues Simulationsmodell
   oder Beispielszenario als Teil dieser Erweiterung hinzufügen.

### Testfälle

- Synthetische Meshfixtures prüfen OBJ-Parsing, Einheiten, Pfadsicherheit,
  Validierungsfehler und stabile, eindeutige Baum-IDs.
- Vorhandene Fabriktests prüfen weiterhin Material-/Massenkennwerte;
  BL6 ergänzt keine neue Kennwert- oder Kraftberechnung.
- Positive/negative OBJ-Indizes, erlaubte Achsenvarianten und nichttriviale
  Transformationen werden gemäß bestehendem Meshvertrag behandelt.
- Offene oder falsch orientierte Volumenmesh-Geometrie, Nullvolumen,
  Selbstüberschneidung, fehlende Datei, Pfad außerhalb der Paketwurzel,
  unbekanntes Material sowie widersprüchliche Material-/Dichtewerte werden
  explizit abgelehnt.
- Fehlermeldungen nennen Paket und Knoten; Fehler produziert keinen
  teilweise veröffentlichten Laufzeitkörper oder Erfolgsschatten.
- Wiederholtes Laden ist deterministisch; vorhandene Ziele werden nicht
  überschrieben.
- Alle parametrischen Formen und das bestehende Yachtpaket laden weiterhin
  mit unveränderten Golden-Daten; synthetische Testfixtures erscheinen nicht
  im Produktivkatalog und es wird keine neue physische Modellkonfiguration
  aufgenommen.
- Kalt-/Warm-Ladezeit, Parsezeit, Fabrikzeit, Mesh-/Knotenanzahl und
  Speicherverbrauch gegen die passende Baseline messen. Keine doppelte
  OBJ-Parse-/Transformationsrunde.

### Testanweisungen

Gezielte Paket-, Mesh-, Fabrik- und Migrationstests:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_modell_lader.py tests\test_mesh.py tests\test_mesh_validierung.py tests\test_koerper.py tests\test_manifest_baum.py tests\test_migriere_modellpaket.py tests\test_active_body_factory.py
```

Nach den gezielten Läufen die volle Suite ausführen:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Zusätzlich synthetische gültige und fehlerhafte Geometriepakete durch Loader
und Validierung führen. Falls ein Ende-zu-Ende-Test des Importpfads nötig ist,
darauf beschränken, die synthetische Geometrie zu laden und wieder zu
verwerfen; keine Simulation starten. GUI-/Darstellungstests verwenden
ausschließlich vorhandene Modellpakete. Performancewerte mit gleicher Hardware,
Python-Version, Modellgröße und Warm-/Kaltkonfiguration vergleichen;
Benchmark-Rohdaten aufbewahren.

### Abnahme

- Ein freigegebener, dokumentierter Datenvertrag wird mit bestehenden
  Loader-/Paketkomponenten umgesetzt; es entsteht kein paralleler Sonderpfad.
- Alle positiven und negativen Testfälle bestehen; Fehler sind sichtbar,
  kontextreich und ohne Teilveröffentlichung.
- Parametrische Formen, Legacy-Kompatibilität und Yachtmodell bestehen ihre
  Golden-/Regressionstests.
- Neue Importfähigkeit wird nur mit synthetischen Testfixtures nachgewiesen;
  diese werden weder als physische Modelle ausgeliefert noch in den
  Produktivkatalog aufgenommen. Ein Importtest startet keine Simulation.
- Masse, Schwerpunkt, Trägheit und Volumen stimmen innerhalb vorab
  festgelegter numerischer Toleranzen; Messrauschen darf nicht nachträglich
  als neue Toleranz ausgegeben werden.
- Leistung und Speicherbedarf sind getrennt ausgewiesen; ein signifikanter
  Rückgang sperrt die Freigabe, bis Ursache und Korrektur geprüft sind.
- Es werden keine neuen physikalischen Modelle, Kraftgesetze oder
  produktiven Beispielmodelle hinzugefügt.

## 4. Gemeinsame Abschlussprüfung

Jede Änderung wird als eigener, fachlich abgegrenzter Schritt umgesetzt.
Nach gezielten Tests folgt die vollständige Suite. Der Arbeitsbericht nennt
Backlog-ID, Dateien/Verträge, Testkommandos und -ergebnisse, Messbedingungen,
Abweichungen, offene Risiken und Abnahmeentscheidung.

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q
```

Fehlgeschlagene Tests, offene Genauigkeits-/Performance-Gates oder eine
unbestätigte Referenz blockieren die Abnahme. Die Arbeit an BL5/BL6 ändert
nicht die Freigabebedingungen der Hydrodynamik aus BL1 und BL2.
