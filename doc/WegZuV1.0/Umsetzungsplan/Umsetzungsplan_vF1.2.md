# SegelPhysik – Umsetzungsplan vF1.2

Dieser Plan setzt die Anforderungen aus
[Spezifikation vF1.2](../Spezifikationen/Spezifikation_vF1.2.md) in überprüfbare Arbeitspakete
um. Er baut auf den dokumentierten Arbeiten in
[Umsetzungsplan vF1](./Umsetzungsplan_vF1.md) und
[Umsetzungsplan vF1a](./Umsetzungsplan_vF1a.md) auf, ersetzt deren historische
Messergebnisse aber nicht. Bereits vorhandene Mesh-, Solver-, GUI- und
6-DOF-Funktionen werden zunächst geprüft und gezielt erweitert; sie werden
nicht ohne Befund neu implementiert.

Der Schwerpunkt liegt auf einem messbar echtzeitfähigen Physikpfad,
konservativen geometrischen Ausschlüssen, CPU-Vektorisierung und einem
gegebenenfalls belegten GPU-Kernel. Die bestehende GUI bleibt erhalten. Die
automatische Überlastpause und der Rückstandsabbau erfolgen über die
bestehenden Simulationssteuerungen und Statusflächen.

## 1. Verbindliche Arbeitsregeln

- Vor Arbeitsbeginn Arbeitsbaum, Python-Version, Abhängigkeiten, bestehende
  Testergebnisse und betroffene Nutzerdaten dokumentieren. Änderungen anderer
  Nutzer bleiben unangetastet.
- Die Phasen 0–5 aus vF1 sowie bereits ausgeführte Arbeiten aus vF1a sind
  historische Grundlage. Ihr Status wird zu Beginn anhand des aktuellen
  Arbeitsbaums überprüft; frühere Messungen werden weder als neue Messung
  ausgegeben noch nachträglich umgedeutet.
- Jede Optimierung benötigt vor ihrer Umsetzung einen benannten Engpass, eine
  reproduzierbare Baseline, einen numerischen Vergleich und einen konkreten
  Rückfallpfad. Nach jeder Optimierung werden dieselben Eingaben erneut
  gemessen.
- Für Genauigkeitsvergleiche gelten ausschließlich die Definitionen und
  Normalisierungen aus Abschnitt 3 der Spezifikation vF1.2. Grenzwerte werden
  vor dem Lauf festgehalten und nicht nach Betrachtung der Ergebnisse
  verändert.
- Broad-Phase-/AABB-Regeln sind konservative Ausschlüsse, keine Ersetzung von
  Union- oder Narrow-Phase-Berechnungen. Unsichere Fälle verbleiben in der
  genaueren Prüfung.
- Exakte Referenzpfade bleiben erhalten. Näherungspfade, Kennfelder und
  GPU-Pfade werden nur freigegeben, wenn alle einschlägigen Genauigkeits-,
  Stabilitäts- und Performance-Gates erfüllt sind.
- Keine GUI-Neugestaltung, keine neuen allgemeinen Steuerungen und keine
  Änderung an Modellquellen allein aus Performancegründen. Konfliktkorrekturen
  bleiben an die ausdrückliche Vorrangkörperauswahl und die
  Transaktionsregeln aus vF1.1 gebunden.
- Keine Änderung des festen Integrationsschritts, keine stille Verwerfung
  von Simulationszeit und keine stillen Erfolgszustände bei Fehlern.
- CPU-only bleibt vollständig funktionsfähig. GPU-Abhängigkeiten bleiben
  optional, sofern keine neue Nutzerentscheidung sie verbindlich macht.
- Kein Commit, Tag oder Push ohne ausdrückliche Beauftragung.

## 2. Ausgangsstand und Phasenabhängigkeiten

### 2.1 Phasenübersicht

| Phase | Ergebnis | Abhängigkeit | Ausgangsstatus laut Vorgängerplan |
|---|---|---|---|
| 0 | Arbeitsstand, Baseline und reproduzierbare Messlast feststellen | keine | teilweise dokumentiert; neu verifizieren |
| 1 | konservative Geometrie-Broad-Phase und Ausschlusstests | Phase 0; gültige Geometrie aus vF1 Phase 1 | offen für die neuen Kriterien |
| 2 | schnellerer exakter Unionpfad mit Körperframe-Wasserfläche | Phase 0; `exakt_union` aus vF1; Phase 1 nur für deren Ausschlussintegration | offen/zu profilieren |
| 3 | vektorisierter körperfester CPU-Pfad für beliebige 6-DOF-Posen | Phasen 0–1; vorhandenes 3-DOF-Voxelmodell aus vF1 | 3-DOF-Grundlage vorhanden; 6-DOF-Erweiterung und Freigabe offen |
| 4 | Säulen-/Präfixsummenpfad für CPU | Phase 3 | neu |
| 5 | Solveraufrufe und Hydrostatik-Kennwerte effizienter wiederverwenden | Phasen 2–4 | teilweise vorhanden; gezielt profilieren |
| 6 | GPU-Hydrostatik-Kernel und feste CPU/GPU-Zuordnung | Phasen 2–4; Phase 5 soweit Solverlast relevant | Backendprototyp vorhanden; echter Physikkernel offen |
| 7 | Echtzeit-Rückstand, automatische Pause und kontrolliertes Fortsetzen | Phase 0; GUI-/Worker-Trennung aus vF1a | Workertrennung vorhanden; Überlastverhalten offen |
| 8 | optionale adaptive Hydrostatik-Kennfelder | Phasen 2–5; nur bei nachgewiesenem Engpass | optional, nicht freigegeben |
| 9 | Zielhardware-Gesamtabnahme und Freigabe | alle für den Produktionspfad gewählten Phasen | offen |

Die Reihenfolge ist nach Abhängigkeiten gewählt. Die Körperframe-Umstellung
des exakten Unionpfads in Phase 2 kann parallel zur Entwicklung der
Broad-Phase in Phase 1 beginnen; deren gemeinsame Integration hängt von
Phase 1 ab. Phase 3 beginnt mit CPU-Referenz und nutzt die
Geometrieausschlüsse aus Phase 1. Phase 4 hängt von einer nachgemessenen
körperfesten CPU-Baseline ab. Die GPU-Implementierung beginnt erst, wenn
ein CPU-Pfad mit identischer Arbeitslast und korrekter Unionbehandlung
vorliegt. Phase 7 kann ihre Zustandsmaschine parallel zu den
Hydrostatikoptimierungen vorbereiten; ihre End-to-End-Abnahme hängt von einem
produktionsfähigen Kraftpfad ab.

### 2.2 Bereits vorhandene Grundlage

Die Vorgängerpläne dokumentieren folgende implementierte oder geprüfte
Grundlagen. Sie gelten nicht automatisch als vF1.2-Freigabe:

- validierte Körper-/Massen-/Trägheitsgrundlagen und Konfliktkorrektur mit
  Rückrollregeln;
- exakte Unionreferenz `exakt_union` und körperfestes Voxelmodell;
- fester SI-Zeitschritt und Solverdiagnosen;
- Hintergrundausführung für Echtzeitphysik und statischen Solver, getrennte
  GUI-Aktualisierung sowie Verwerfen veralteter Workerresultate;
- 6-DOF-Dynamik, Quaternionpose und bestehende Renderinterpolation;
- optionale OpenCL-Geräte-/Kernelkompatibilität auf der dokumentierten
  Windows-/Radeon-760M-Konfiguration.

Das vorhandene körperfeste Voxelmodell ist aktuell ein 3-DOF-Modell
`(z, phi)`, kein bereits verfügbarer 6-DOF-Produktionspfad. Seine Erweiterung
auf beliebige Quaternionposen ist daher eine neue Implementierung und muss
gegen die bestehende 3-DOF-Referenz sowie die exakte Union validiert werden.
Der vorhandene globale Voxelpfad vektorisiert Teile der Säulenberechnung,
enthält aber weiterhin Python-Schleifen über Rasterspalten und
Geometrieelemente. Der vorhandene OpenCL-Prototyp belegt die
Geräte-/Kernelanbindung, nicht einen Hydrostatik-Kernel. Diese Grundlagen
sind in Baseline und Phasenabnahme entsprechend getrennt auszuweisen.

Die dokumentierten Messungen zeigen jedoch, dass ein flüssiger Renderpfad
keine Echtzeitphysik belegt: Im zehnsekündigen Live-Test stieg der
Physikrückstand auf etwa `7,47 s`; vier exakte Schritte dauerten auf der
Zielhardware im Prozessworker median `37,24 ms` bei `dt = 0,004 s`. Die
körperfeste Näherung ist ebenfalls nicht automatisch freigegeben: im
Yacht-Solververgleich verfehlte sie unter anderem die Winkel-, Schwerpunkt-
und Momentenkriterien. Diese Befunde sind Startprobleme für die neuen Phasen,
keine bereits gelösten Eigenschaften.

### 2.3 Voraussichtliche Code- und Messoberflächen

Die Umsetzung nutzt zuerst bestehende Schnittstellen und Tests. Die
endgültige Dateiauswahl wird nach Phase 0 anhand des aktuellen Codes bestätigt:

- Hydrostatik und Kraftpfade: `segelphysik/core/auftrieb.py`,
  `segelphysik/core/volumen_union.py`, `segelphysik/core/hydrostatik.py`;
- körperfestes Raster und Backend: `segelphysik/core/voxelmodell.py`,
  `segelphysik/core/physik_backend.py`;
- 6-DOF-Physik und Echtzeitsteuerung: `segelphysik/core/dynamik_6dof.py`
  sowie die vorhandenen Worker-/Timer-Schnittstellen in
  `segelphysik/gui/hauptfenster.py`;
- Messwerkzeuge: `werkzeuge/benchmark_physik.py` und
  `werkzeuge/benchmark_gui_live.py`;
- bestehende Referenztests unter `tests/`, insbesondere die bereits in vF1/vF1a
  verwendeten Hydrostatik-, Solver-, Dynamik- und GUI-Regressionen.

Eine neue Modulgrenze oder Abhängigkeit wird nur eingeführt, wenn Profiling
und ein konkreter technischer Bedarf dies belegen.

Die genannten Messwerkzeuge decken die vF1.2-Abnahme derzeit nicht vollständig
ab. Phase 0 muss daher ihre nötigen Erweiterungen als Arbeitsergebnis
umfassen: Der GUI-Benchmark muss Pflicht-Layer tatsächlich aktivieren und
ihre Sichtbarkeit verifizieren, Eingaben bis zu einer präsentierten
Reaktion zeitlich zuordnen sowie den Rückstand mindestens sekündlich als
Zeitreihe erfassen. Qt-Event-Dispatch allein gilt nicht als
Eingabelatenzmessung. Falls die vorhandene Renderer-/Qt-Schnittstelle keinen
Zeitpunkt der tatsächlichen Präsentation zugänglich macht, ist die
Messmethode vor der Baseline zu ergänzen; nicht messbare Werte dürfen nicht
als bestanden ausgewiesen werden. Der Physikbenchmark verwendet derzeit
wenige feste 3-DOF-Posen und CPU-Pfade; er muss für vF1.2 um beliebige
Pflicht-Quaternionposen, vollständige 6-DOF-Schritte und den gepaarten
CPU/GPU-Vergleich erweitert werden. Die bisherigen 3-DOF-Fälle bleiben als
Regressionen erhalten und ersetzen diese neuen Messfälle nicht.

## 3. Phase 0 – Arbeitsstand und reproduzierbare Baseline

### Umsetzung

1. Arbeitsbaum, aktive Python-Umgebung, Python-/Paket-/Treiberstände und
   vorhandene Änderungen erfassen. Ungetrackte Nutzermodelle und Änderungen
   an Spezifikationen weder in Tests einbeziehen noch überschreiben.
2. Den Zustand der in Abschnitt 2.2 genannten Grundlagen mit gezielten
   vorhandenen Tests bestätigen. Fehlende oder regressierte Grundlagen werden
   vor Beschleunigungsarbeit behoben oder als blockierend festgehalten.
3. Ein unveränderliches Benchmarkmanifest für den konfigurierten Ponton und
   das Yacht-Produktivmodell erstellen: Modell-/Meshidentität,
   Geometrie-/Materialkonfiguration, Posefolge, Raster- und Kennfeldparameter,
   sichtbare Layer, Kamera, GPU-/CPU-Modus und Zielhardware festhalten.
4. Als repräsentative interaktive Last den Yachtkörper im Echtzeitmodus mit
   sichtbarer 3D-Ansicht und den Layern Schwerpunkt, Achsen, Kräfte und
   Momente verwenden. Dieselbe Posefolge und Konfiguration für CPU und GPU
   benutzen. Einen isolierten Physiklauf ohne Rendering nur als Diagnose
   ergänzen.
5. Mit mindestens 30 Sekunden Warm-up und anschließend zehn Minuten Messzeit
   erfassen: tatsächlich präsentierte FPS, Eingabe-bis-sichtbar-Latenz,
   Physikschritt-/Batchzeit, angeforderte und berechnete Simulationszeit,
   Rückstand, Speicher und Rendererzeiten. Rückstand mindestens einmal pro
   Sekunde abtasten. Eingabelatenz beginnt beim Zeitstempel der synthetisch
   oder reproduzierbar ausgelösten Eingabe und endet beim ersten tatsächlich
   präsentierten Frame, der deren sichtbare Zustandsänderung enthält.
   Pflicht-Layer müssen im Lauf sichtbar sein; ein bloßes Erfassen ihres
   Aktivierungszustands genügt nicht.
6. p50, p95, Maximum und Streuung ausweisen. Für jeden vollständigen,
   gleichartigen CPU/GPU-Lauf eines Messpaares die p95-Zeit des vollständigen
   Physikschritts berechnen und die relative Verbesserung als
   `(p95_CPU - p95_GPU) / p95_CPU` bestimmen. Laufreihenfolge innerhalb jedes
   Paares randomisieren oder alternieren, damit systematische Reihenfolge-
   und Erwärmungseffekte nicht stets dasselbe Backend begünstigen. Die
   unabhängigen Stichproben sind Laufpaare, nicht einzelne zeitlich
   benachbarte Frames oder Schritte. Mindestens zehn gepaarte Läufe
   verwenden; das 95-%-Konfidenzintervall des Medians der paarweisen
   Verbesserungen wird per gepaartem Perzentil-Bootstrap mit 10.000
   Resamples berechnet. Das untere 2,5-%-Quantil dieses Intervalls muss
   mindestens `10 %` betragen. Andernfalls wird die Stichprobe bis höchstens
   30 Laufpaare erweitert; bleibt das untere Intervallende darunter, ist der
   GPU-Vorteil nicht nachgewiesen. Messzahl und Verfahren sind zu berichten.
   Vorbereitung, Erstinitialisierung,
   Speichertransfer, Kernel, Ergebnisreduktion und wiederholte Poseauswertung
   getrennt messen. Zusätzlich die amortisierte Gesamtkostenkurve über die
   reale Anzahl wiederholter Aufrufe darstellen.
7. Die Genauigkeitsreferenz je Pflichtpose mit der exakten Union und den
   analytischen Grundkörpern vorab festlegen. Die Skalen `S`, Messgrößen und
   Testzeitpunkte schriftlich einfrieren, bevor Varianten verglichen werden.

### Prüfungen und Abnahme

- Baseline ist aus einem sauberen Neustart wiederholbar; Hardware und
  Konfiguration sind vollständig protokolliert.
- Die Baseline unterscheidet Renderleistung von Physikdurchsatz und
  dokumentiert den Rückstand über Wandzeit. Sie weist eine Zeitreihe mit
  mindestens sekündlicher Abtastung sowie p95 und Trend aus. Der Trend ist
  die per linearer Regression aus den sekündlichen Messpunkten bestimmte
  Rückstandszunahme über fünf Minuten; höchstens `50 ms` Zunahme ist
  zulässig und definiert hier abschließend den tolerierten positiven Trend.
- Die Pflicht-Layer sind im Benchmark sichtbar; die Eingabelatenz endet erst
  beim präsentierten Frame mit der sichtbaren Reaktion. Fehlt ein belastbarer
  Präsentationszeitpunkt, ist die Baseline für dieses Gate nicht gültig.
- Benchmarkläufe verändern keine Projekt-OBJ-, JSON- oder Quelldateien.
- Vorhandene GUI-Smoke- und Regressionstests bestätigen unveränderte
  Bedienung, Darstellungszustände und Material-Sitzungssemantik.
- Bekannte Fehler und frühere Messwerte bleiben von neuen Ergebnissen
  unterscheidbar.

## 4. Phase 1 – Konservative Geometrieausschlüsse

### Umsetzung

1. Vorzeichenbehaftete Distanz zur Welt-Wasserfläche sowie eine einheitliche
   Sicherheitsbreite je Rechenpfad implementieren:
   `delta = max(delta_abs, delta_rel * L, delta_num)`, wobei `L` die
   Körper-AABB-Diagonale ist. `delta_abs`, `delta_rel` und `delta_num`
   berücksichtigen Modell-/Meshgenauigkeit bzw. Transformations- und
   Gleitkommafehler und sind vor Abnahme festzulegen.
2. Für gedrehte Bounds die Extrema konservativ bestimmen (z. B. alle
   AABB-Ecken transformieren oder eine verifizierte Supportfunktion nutzen).
   Nur bei Untergrenze `> +delta` vollständig trocken, nur bei Obergrenze
   `< -delta` vollständig eingetaucht klassifizieren; grenznahe Kandidaten
   an die Narrow-Phase übergeben.
3. Für den exakten Mesh-/Unionpfad räumliche Bounds/Bäume nutzen, um
   Dreiecke, Zellen oder Untergeometrien sicher vollständig trocken oder
   eingetaucht zu klassifizieren. Vollständig eingetauchte Beiträge nur
   dann über vorberechnete Gesamtvolumen-/Schwerpunktdaten verwenden, wenn
   die Union-/Überlappungsbehandlung dieselbe äußere Geometrie erhält.
4. Für Rasterpfade vollständig nasse und trockene Bereiche bzw. Säulen
   früh klassifizieren; Zellen an oder nahe der Wasserfläche verbleiben in
   der vollständigen Klassifikation.
5. Jedes Ausschlussresultat mit einer instrumentierten Referenzoption
   vergleichbar machen. Instrumentierung und Diagnosedaten dürfen den
   Produktionspfad nicht dauerhaft verlangsamen.

### Tests und Abnahme

- Analytische Quader/Pontons werden bei Abständen `±(delta - epsilon)`,
  `±delta` und `±(delta + epsilon)` geprüft; tangentiale und koplanare Fälle
  werden an die genaue Prüfung weitergereicht.
- Alle Boundsprüfungen umfassen aufrechte, gerollte, genickte und kombinierte
  Quaternionorientierungen sowie Translationen.
- Trocken, vollständig eingetaucht, teilweise eingetaucht und
  Wasserlinienkontakt vergleichen Volumen, Schwerpunkt, Kraft und Moment
  gegen den vollständigen Referenzpfad.
- Überlappende Unionteile, berührende Grenzen, geschlossene Volumen und
  offene Schalen dürfen nicht durch unzulässige Einzeladdition verändert
  werden.
- Für alle Pflichtfälle gilt: Ausschlüsse dürfen gegenüber derselben
  Referenzpose kein anderes Ergebnis außerhalb der numerischen
  Rundungstoleranz erzeugen. Ein nicht sicher entscheidbarer Fall wird
  niemals ausgeschlossen.

## 5. Phase 2 – Exakte Union: Wasserfläche im Körperframe

### Umsetzung

1. Den aktuellen `exakt_union`-Pfad getrennt profilieren: Unionaufbau,
   Pose-/Meshtransformation, Ebenenschnitt, Volumen-/Schwerpunktintegration
   und Rücktransformation von Momenten.
2. Die Geometrie in Körperlage belassen und für Pose `x_welt = R x_körper + t`
   die Wasserbedingung im Körperframe als
   `(R^T e_z) · x_körper + t_z <= 0` anwenden. Die API soll Ebenennormale,
   Ebenenabstand und Koordinatenframe explizit transportieren, damit
   Vorzeichen-/Framefehler nicht still verborgen bleiben.
3. Bestehende Boolesche Union/Clipping-Funktion nur dort erweitern, wo sie
   eine nicht transformierte Geometrie zuverlässig trimmen kann. Wenn die
   Bibliothek intern dennoch eine Kopie oder vollständige Transformation
   erzeugt, Profiling belegt das und die Maßnahme wird nicht als Optimierung
   behauptet.
4. Momente um den Massenschwerpunkt nach dem Schnitt konsistent in Welt- und
   Körperkoordinaten ausgeben. Die exakte Referenz-API und Fehlerbehandlung
   bleiben eindeutig identifizierbar.
5. Die in Phase 1 sichere Broad-Phase auf den Unionpfad anwenden, ohne die
   Unionsemantik für überlappende Komponenten zu ändern.

### Tests und Abnahme

- Analytische ebene Schnitte durch Quader/Pontons in mehreren Orientierungen
  prüfen Ebene, Vorzeichen, Volumen, Schwerpunkt, Kraft und Moment.
- Körperframe- und bisheriger Weltframe-Pfad werden auf identischen Posen
  verglichen. Volumen-/Kraft-/Momentunterschiede müssen innerhalb der
  begründeten numerischen Referenztoleranz liegen.
- Tangential-, Nullvolumen-, vollständig trocken/nass-, koplanare und
  mehrfach überlappende Geometrien werden geprüft.
- Vorbereitung und wiederholte Posen getrennt messen. Diese Phase gilt nur
  als Performancegewinn, wenn die p95-Schrittzeit oder Gesamtkosten bei
  gleicher Korrektheit messbar sinken.

## 6. Phase 3 – Körperfestes 6-DOF-Raster und vektorisierte CPU-Referenz

### Umsetzung

1. Das vorbereitete Raster nur bei Modell-, Geometrie-, Material- oder
   Auflösungsänderung neu erzeugen. Rasterursprung, Abdeckung, Zellmaß,
   Gewicht und Körperframe eindeutig speichern und cachen.
2. Die nasse Klassifikation für beliebige normierte Quaternionen mit
   `z_welt = (R^T e_z) · p_lokal + t_z` aufbauen. Es darf keine Python-Schleife
   über jedes Voxel geben; zunächst den aktuell besten korrekt
   vektorisierten NumPy-CPU-Pfad als reproduzierbare Basis herstellen.
3. Volumen und alle gewichteten lokalen Koordinaten für den
   Volumenschwerpunkt berechnen. Danach den Schwerpunkt korrekt in den
   Weltframe transformieren. Null-/nahezu-null Volumen liefert definierte
   finite Ergebnisse ohne Division durch null.
4. Zwischenergebnisse/Arrays so anlegen, dass unnötige vollständige
   temporäre Kopien und Allokationen pro Pose vermieden werden. Cache-
   Invalidierung und Speicherbedarf instrumentieren.
5. Nur nach korrekter Voxel-/Unionsemantik den Pfad als Kandidat für die
   interaktive Produktion markieren. Den Kandidaten über dieselbe
   Hydrostatik-/Kraftfunktionsschnittstelle wie den bestehenden
   `baue_kraftfunktion_6dof`-Pfad integrierbar machen und die Aufrufstellen
   für GUI-Echtzeit und Prozessworker explizit erfassen. Bis zum Bestehen
   aller Solver- und Live-Gates bleibt die bisherige Produktionszuordnung
   unverändert; danach erfolgt die Auswahl fest und nachvollziehbar, nicht
   leistungsabhängig pro Pose.

### Tests und Abnahme

- Körperfeste Rasterdaten bleiben über Posewechsel identisch; Veränderungen
  an Modell, Rasterauflösung oder gültigen Körperdaten invalidieren sie
  zuverlässig.
- Beliebige Rotation einschließlich reiner Roll-, Nick-, Gier- und
  kombinierter Orientierung gegen exakte Union und analytische Fälle testen.
- Monotonie über Tiefgang, nasse/trockene Grenzfälle, Überlappungsunion,
  Schwerpunktframe, Kraft-/Momentvorzeichen und Endlichkeit sichern.
- Für jede Pflichtpose das Fehlermaß aus Spezifikation Abschnitt 3 bestimmen.
  Eine Rasterpose-Übereinstimmung allein genügt nicht: Gleichgewichts-Solver,
  Kräfte, Momente und dynamische Verläufe müssen ebenfalls bestehen.
- Vorbereitungszeit, Speicherbedarf, p50/p95/Maximum je Pose und amortisierte
  Arbeitslast gegen `exakt_union` berichten.

## 7. Phase 4 – Säulen-/Präfixsummenpfad

### Umsetzung

1. Das körperfeste Raster nach zwei lokalen Achsen in Säulen aufteilen und
   pro Säule die geordnete Koordinate entlang der gewählten Achse sowie
   Präfixsummen für Volumen und Schwerpunktbeiträge vorberechnen.
2. Pro Pose den Wasserhöhengradienten aus `R^T e_z` bestimmen und je Säule
   den nassen zusammenhängenden Bereich durch binäre Suche/`searchsorted`
   ermitteln. Rand- bzw. Grenzvoxel werden gemäß derselben Klassifikation
   wie die vektorisierte Referenz behandelt.
3. Für nahezu verschwindenden Gradienten entlang der gewählten Säulenachse
   eine alternative Achse oder die geprüfte Vektorisierung auswählen. Jede
   Degenerationsentscheidung muss definiert, numerisch stabil und testbar
   sein; keine Division durch nahezu null.
4. Präfixsummen müssen mindestens Volumen und drei gewichtete lokale
   Koordinatensummen liefern. Numerische Akkumulationsmethode und
   Gleitkommatyp dokumentieren. Falls Summenfehler die Genauigkeitsgates
   verletzen, stabilere Summation oder geprüfte Vektorreduktion verwenden.
5. Einmalige Vorbereitung, zusätzliche Speicherbelegung und Laufzeit je
   Pose getrennt messen. Säulenpfad bleibt optional, wenn die Vorbereitung
   bei repräsentativer tatsächlicher Nutzung nicht amortisiert wird.

### Tests und Abnahme

- Für mehrere Quaternionen gezielt jede Achse als Säulenrichtung, nahezu
  null Gradient, Vorzeichenwechsel und Grenzschnitt erzeugen.
- Vergleich mit vektorisierter körperfester CPU-Referenz und exakter Union
  für V, Schwerpunkt, Kraft und Moment. Pflichtfälle schließen die
  Gleichgewichtslage und dynamische Verläufe ein.
- Vergleich verschiedener Summationsreihenfolgen mit dokumentierten
  Toleranzen; nicht-endliche oder unvollständige Präfixdaten müssen als
  Fehler sichtbar werden.
- Leistung einschließlich Vorbereitung und realer Wiederholungszahl
  ausweisen; keine Auswahl allein anhand eines besonders günstigen
  Einzelposes.

## 8. Phase 5 – Solver- und Kennwertoptimierung

### Umsetzung

1. Mit Profiling belegen, welcher Anteil der interaktiven Last und der
   statischen Lösung auf Solverwiederholungen, Kraftauswertungen,
   Ableitungen oder Linearsysteme entfällt.
2. Vorhandene berechnete Pose-/Kraftwerte und angrenzende Zustandswerte
   wiederverwenden, wo die Eingaben identisch sind. Cache-Schlüssel müssen
   Zustand, Geometrie-/Materialrevision, Backend und numerische Parameter
   umfassen; bei jeder relevanten Änderung invalidieren.
3. Solverwarmstarts aus der letzten gültigen Pose oder einem nahegelegenen
   Kennwert nur für klar abgegrenzte Zustände verwenden. Fehlerhafte oder
   veraltete Starts müssen auf den robusten vorhandenen Solverpfad
   zurückfallen.
4. Physikalisch abgeleitete Jacobi-Startwerte aus Wasserlinienfläche bzw.
   Flächenträgheit nur verwenden, wenn Gültigkeitsbereich, Vorzeichen und
   Einheiten analytisch geprüft sind. Finite Differenzen zunächst als
   Vergleichs-/Fallbackpfad behalten.
5. Abbruch- und Solverresttoleranzen in Kraft/Moment SI-Einheiten begründen
   und vor den Benchmarkfällen einfrieren. Eine erreichte Toleranz darf
   keine falsche Stabilität, Gleichgewichtslage oder Konvergenz melden.
6. Nur bei weiterem gemessenem Bedarf ein adaptives Kennfeld bauen:
   Pose-/Parameterbereich, Interpolationsordnung, Fehlerabschätzung und
   sichere Fallbackregel auf exakte/CPU-Hydrostatik definieren. Keine
   Interpolation über unkontrollierte Nass-/Trocken- oder
   Topologieübergänge.

### Tests und Abnahme

- Solverergebnisse gegen exakte Unionreferenz und vorhandene robuste
  Diagnosen vergleichen: Restkraft, Restmoment, Winkel, Stabilität,
  Neutralität, Stagnation und Budgetende bleiben korrekt.
- Ableitungen an analytischen Körpern sowie mit unabhängigen
  Finite-Differenzen prüfen.
- Cachetests umfassen identische Eingaben, geänderte Pose, Geometrie, Material,
  Auflösung und Rechenbackend; keine veraltete Kraft darf wiederverwendet
  werden.
- Kennfeldtests prüfen Grenzen und Zwischenwerte des gesamten freigegebenen
  Bereichs sowie Out-of-range-, Grenzflächen- und Fallbackfälle.
- Abnahme nur bei erfüllten Genauigkeitsgrenzen und gemessenem Gewinn im
  vollständigen Solver- oder Echtzeit-Lastlauf.

## 9. Phase 6 – GPU-Physikpfad und feste Zuordnung

### Technologie- und Arbeitslastentscheid

1. Die dokumentierte OpenCL-Kompatibilität auf der AMD Radeon 760M als
   Plattformnachweis behandeln, nicht als Nachweis eines Hydrostatik-
   Produktionspfads. Vor einer Implementierung Treiber, Python-/Backend-
   Version und verfügbaren Speicher auf dem tatsächlichen Zielsystem erneut
   erfassen.
2. Den CPU-Pfad aus Phase 3 oder 4 als fachliche und zeitliche Referenz
   festlegen. Zuerst einen Physikkernel für Voxel-/Säulenklassifikation und
   Reduktion entwerfen; nur kleine Poseparameter hineinsenden und
   poseunabhängige Daten möglichst GPU-resident halten.
3. Vorbereitung, Transfers, Kernel, Synchronisation, Ergebnisreduktion und
   vollständige Physikschrittzeit separat messen. GPU mit paralleler
   Renderinglast und isoliert vergleichen; der interaktive Lauf ist für die
   Entscheidung maßgeblich.
4. Eine feste Zuordnung im Code nur nach Ende-zu-Ende-Benchmark entscheiden.
   Es gibt kein leistungsabhängiges Umschalten pro Pose. Ist der Vorteil nicht
   nachgewiesen, bleibt der CPU-Pfad für Produktion zuständig; GPU bleibt
   optional und als Entwicklungs-/Vergleichspfad verfügbar.

### Implementierung und Fehlerbehandlung

1. GPU-Backend hinter der vorhandenen Physikschnittstelle kapseln; GUI- und
   Rendercode bleiben unabhängig vom Backend.
2. Backend-/Gerätenamen und tatsächlich gewählten Pfad nachvollziehbar
   protokollieren. CPU-Tests dürfen PyOpenCL oder ein anderes GPU-Paket nicht
   voraussetzen.
3. Bei fehlendem Gerät, Initialisierungsfehler, Kernel-/Transferfehler,
   nicht endlichen, unvollständigen oder verspäteten Ergebnissen den Fehler
   mit Ursache melden und exakt dieselbe Pose auf der CPU wiederholen, wenn
   der CPU-Referenzpfad verfügbar ist.
4. Ergebnisreihenfolge und Snapshot-Identität sichern. Verspätete GPU-
   Ergebnisse dürfen keine neueren Physikzustände überschreiben. Puffer
   dürfen erst nach abgeschlossener Queue-/Eventnutzung wiederverwendet
   werden.
5. GPU-Abhängigkeiten nur in der optionalen GPU-Anforderungsdatei führen,
   wenn der CPU-Betrieb dadurch unabhängig bleibt.
6. Den GPU-Pfad über dieselbe Produktionsschnittstelle und in denselben
   Echtzeit-/Prozessworker-Aufrufstellen wie den abgenommenen CPU-Pfad
   integrieren. CPU/GPU-Zuordnung bleibt pro Konfiguration fest; GUI und
   Renderer dürfen keine eigene Backendwahl oder Pose-für-Pose-Umschaltung
   implementieren.

### Tests und Abnahme

- Identische CPU-/GPU-Eingaben für alle analytischen und Yachtpflichtfälle;
  V, Schwerpunkt, Kraft, Moment, statische Lösung und dynamische
  Zeitverläufe nach Spezifikation Abschnitt 3 prüfen.
- Mock-/Fehlertests: GPU nicht vorhanden, erfolgreicher Kernel,
  Initialisierungsfehler, Ausführungsfehler, nicht-endliche Ausgabe,
  verspätetes Resultat und CPU-Fallback.
- Auf Zielhardware gepaarte vollständige Messreihen mit identischer
  Renderlast und unverändertem Messverfahren aus Phase 0. Ein GPU-Pfad kann
  nur Produktionskandidat werden, wenn die p95-Zeit je vollständigem
  Physikschritt mindestens `10 %` geringer ist als CPU und das untere
  2,5-%-Quantil des nach Phase 0 berechneten 95-%-Konfidenzintervalls der
  relativen Verbesserung mindestens `10 %` beträgt. Die Verbesserung darf
  Genauigkeit, FPS oder
  Eingabelatenz nicht verschlechtern.
- Wenn dieser Vorteil fehlt, GPU-Pfad nicht als beschleunigte Produktion
  ausweisen; CPU bleibt der Betriebsweg und die Entscheidung wird
  nachvollziehbar dokumentiert.

## 10. Phase 7 – Echtzeit-Überlast, automatische Pause und Fortsetzen

### Umsetzung

1. Die vorhandene GUI-/Physikworker-Trennung und den festen
   Wandzeitakkumulator prüfen. Zustandsübergänge und Zeitstempel müssen
   eindeutig zwischen GUI, Physikworker und GPU-Queue weitergegeben werden.
2. Angeforderte Simulationszeit, berechnete Simulationszeit und Rückstand
   getrennt führen. Rückstand ist `angeforderte Zeit - berechnete Zeit`;
   Darstellung/interpolierte Pose verändert weder diese Größen noch den
   Physikzustand. Noch nicht eingereichte Zeit und eingereichte, aber noch
   nicht übernommene Worker-/GPU-Zeit sind getrennte Buchungsposten; beide
   zählen genau einmal zum Rückstand. Die berechnete Zeit wird ausschließlich
   bei Übernahme des zugehörigen Resultats fortgeschrieben.
3. Zustände mindestens als normaler Echtzeitbetrieb, Überlastbeobachtung,
   automatisch pausiert und Rückstandsnachholung unterscheiden. Die
   Schwellenbedingung ist eindeutig: Rückstand `>= 1,0 s` während
   `>= 5 s` ununterbrochen löst die automatische Pause aus; bei genau `1,0 s`
   beginnt die Fünf-Sekunden-Frist. Fällt der Rückstand vor Fristablauf unter
   `1,0 s`, wird die Frist zurückgesetzt. GUI bleibt bedienbar; Pausengrund
   und Rückstand werden über bestehende Statusflächen bzw. das Protokoll
   gemeldet.
4. Angeforderte Zeit, berechnete Zeit, Rückstand, Laufgeneration und
   Sequenznummer jedes Worker-/GPU-Auftrags eindeutig führen. Beim
   Pausieren bereits berechnete Ergebnisse in Sequenzreihenfolge genau
   einmal übernehmen. Die berechnete Simulationszeit wird erst fortgeschrieben,
   wenn das Resultat genau einmal in den gültigen Zustand übernommen wurde.
   Noch laufende oder veraltete Aufträge dürfen sicher abgeschlossen und
   übernommen oder verworfen werden; bei Verwerfen bleibt ihr noch nicht
   übernommenes Zeitintervall genau einmal im Rückstand und wird erneut
   eingeplant. Bereits übernommene Intervalle werden nicht erneut angefordert.
   Die bestehende Generation-/In-flight-Logik muss dabei ausdrücklich
   migriert bzw. erhalten werden. Keine fällige Simulationszeit verwerfen.
5. Während jeder Pause keine neue Simulationszeit anfordern. Manuelle
   Pausierung und Wechsel zwischen Echtzeit- und statischem Modus dürfen den
   noch nicht berechneten Rückstand nicht zurücksetzen; der statische Solver
   verbraucht oder verändert diese Zeitbilanz nicht. Ein Körperwechsel ist
   ein Szenariowechsel am letzten übernommenen Simulationszeitstempel:
   Ergebnisse und Aufträge des alten Körpers, die noch nicht übernommen
   wurden, werden anhand ihrer Snapshot-Identität ungültig. Ihre Intervalle
   werden genau einmal vom In-flight- in den noch nicht eingereichten
   Buchungsposten verschoben; der Gesamtrückstand ändert sich dadurch nicht.
   Die ausstehende Zeit wird anschließend mit dem neu ausgewählten
   Körpermodell berechnet.
   Zustand und Pose des neuen Körpers werden nach derselben Initialisierungs-
   regel wie bei einem regulären Echtzeitstart bestimmt, nicht aus dem alten
   Körperzustand übertragen. Bereits übernommene Schritte werden nicht
   zurückgerollt. Ein Wechsel setzt weder Rückstand noch Simulationsuhr
   zurück. Innerhalb eines laufenden Anwendungsprozesses gilt jeder Neustart
   des Echtzeitmodus als Fortsetzung desselben Laufs; er darf den Rückstand
   nicht nullsetzen. Ein neuer Lauf mit leerer Zeitbilanz ist nur nach
   Abschluss des vorherigen Laufs ohne offenen Rückstand zulässig. Beim
   Prozessende endet der Lauf; ein neuer Prozess ist ein neuer Lauf und setzt
   den vorherigen nicht fort. Ein noch offener Rückstand wird beim
   Anwendungsschluss als unberechnet protokolliert und nicht als abgeschlossen
   ausgegeben; eine Wiederaufnahme nach Prozessende ist nicht zugesichert.
6. Beim manuellen Fortsetzen zunächst ausschließlich den erhaltenen
   Rückstand mit festem `dt` und mindestens `1,25` integrierten
   Simulationssekunden je Wandsekunde abarbeiten. Während dieses
   Nachholmodus keine neue Live-Wandzeit zum Rückstand addieren. Die
   Nachholrate als tatsächlich übernommene Simulationszeit geteilt durch
   verstrichene Wandzeit messen. Nicht überlappende, aufeinanderfolgende
   Ein-Sekunden-Fenster ab Fortsetzen sowie die Gesamtrate vom Fortsetzen bis
   zum Erreichen von höchstens `100 ms` ausweisen. Ist der Rückstand beim
   Fortsetzen bereits höchstens `100 ms`, entfällt die Nachholung und der
   normale Echtzeitbetrieb beginnt unmittelbar; dafür wird keine
   Nachholraten-Freigabe behauptet.
   Sobald der Rückstand höchstens `100 ms` beträgt, in normalen
   Echtzeitbetrieb mit angeforderter Simulationszeit von `1,0 s` je
   Wandsekunde wechseln. Eine noch kleinere Rückstandsmenge bleibt dabei
   erhalten und wird nicht auf null gerundet.
7. Wird in einem vollständigen Ein-Sekunden-Fenster die Rate `1,25x`
   unterschritten, wird das als verfehlte Nachholratenanforderung
   protokolliert und darf nicht als erfüllt gemeldet werden. Die Simulation
   arbeitet den Rückstand weiterhin mit maximal verfügbarem Durchsatz ab;
   sobald der Rückstand höchstens `100 ms` beträgt, gilt der in Punkt 6
   festgelegte Wechsel in den Normalbetrieb. Auch eine Gesamtrate unter
   `1,25x` ist ein Abnahmefehler. Fehlende Rechenleistung führt weder zu
   einem Erfolgstatus noch zum Verwerfen von Zeit.
8. Pausen-/Fortsetzenstatus mit bestehenden Steuerungen abbilden; keine neue
   allgemeine GUI-Steuerung hinzufügen. Automatische Pause muss für den
   Nutzer vom regulären manuellen Pausieren unterscheidbar gemeldet werden.

### Tests und Abnahme

- Deterministische Zeitsimulationen erzeugen kurze Spitzen unterhalb der
  Schwelle, genau `1,0 s`, knapp darunter/darüber sowie Fälle knapp unter
  und genau bei fünf Sekunden. Bei `>= 1,0 s` während `>= 5 s`
  ununterbrochen wird automatisch pausiert; ein Rückstand unter `1,0 s`
  setzt die Frist zurück.
- Nach automatischer Pause bleibt der gesamte Rückstand erhalten und es
  werden keine weiteren Wandzeitforderungen addiert.
- Manuelles Fortsetzen weist mindestens `1,25x` Nachholrate bis `100 ms`
  nach und wechselt dann auf normalen `1,0x` Betrieb. Zeiten werden weder
  doppelt angerechnet noch ausgelassen. Ein Test mit absichtlich
  unzureichender Rechenleistung muss den Nachholmodus, die gemeldete
  Unterschreitung und die fortgesetzte Rückstandsbilanz nachweisen; nach
  Erreichen von `100 ms` darf der Normalbetrieb einsetzen, aber der
  fehlgeschlagene Raten-Gate muss im Ergebnis sichtbar bleiben und darf nicht
  als bestanden ausgewiesen werden. Ein Start mit höchstens `100 ms`
  Rückstand wechselt direkt in den Normalbetrieb und meldet keine gemessene
  Nachholrate.
- Manuelle Pause, Wechsel zwischen statischem und Echtzeitmodus sowie
  Körperwechsel erhalten den Rückstand. Der statische Solver verändert ihn
  nicht. Ein Körperwechsel bildet eine Szenariogrenze am letzten übernommenen
  Simulationszeitstempel: alle noch nicht übernommenen Intervalle, auch die
  eines abgebrochenen In-flight-Auftrags, werden genau einmal dem neu
  ausgewählten Körper zugeordnet. Dessen Zustand wird nach der regulären
  Echtzeitstartregel initialisiert; ein Zustandstransfer vom alten Körper
  findet nicht statt. Bereits übernommene Schritte werden weder
  zurückgerollt noch erneut integriert. Tests prüfen Körperwechsel vor,
  während und nach einem Workerabschluss sowie, dass die Gesamtzeitbilanz
  beim Wechsel unverändert bleibt und kein In-flight-Intervall doppelt
  gebucht oder integriert wird.
- Veraltete Worker-/GPU-Ergebnisse und Anwendungsschluss erzeugen keine
  Rückschreibung oder falsche Pose; sequenzierte Ergebnisse werden weder
  verloren noch doppelt integriert. Ein verworfenes, noch nicht übernommenes
  Intervall bleibt genau einmal als Rückstand bestehen und wird erneut
  eingeplant. Beim Anwendungsschluss wird ein nicht berechneter Rückstand als
  solcher protokolliert und nicht als abgeschlossene Simulationszeit gemeldet.
- Während blockierter Physik- und GPU-Aufgaben bleibt die Qt-Ereignisschleife
  bedienbar; GUI-Aktualisierungen erfolgen nur im GUI-Thread.
- Bei der Abnahme darf im zehnminütigen stationären Dauerlastlauf keine
  automatische Überlastpause auftreten.

## 11. Phase 8 – Optionale adaptive Hydrostatik-Kennfelder

Diese Phase wird nur begonnen, wenn das Profiling nach Phasen 1–7 einen
relevanten Restengpass belegt und die korrekte CPU-/GPU-Auswertung die
Echtzeitgates nicht erreicht. Sie ist kein Ersatz für sichere Ausschlüsse,
den Säulenpfad oder einen belegten Kernel.

### Umsetzung

1. Eingangsgrößen, Freiheitsgrade, gültigen Pose-/Geschwindigkeitsbereich,
   Kennfeldauflösung und Interpolationsverfahren vorab definieren.
2. Samples aus der exakten Unionreferenz deterministisch erzeugen und
   Kennfelder mit Fehlerabschätzung und Gültigkeitsmetadaten speichern.
3. Out-of-range- und Unsicherheitsfälle auf den freigegebenen exakten
   Rechenpfad zurückführen. Keine stillen Clamp-/Extrapolationsresultate.
4. Speicherbedarf, Aufbauzeit, Lookup-/Interpolationszeit und exakte
   Fallbackquote getrennt erfassen. Kennfeldversionen müssen zur
   Geometrie-/Materialrevision passen und sonst invalidiert werden.

### Tests und Abnahme

- Dichte Prüfposegitter, Randbereiche, Wasserlinienübergänge, nicht glatte
  Bereiche und statische Gleichgewichte gegen exakte Referenz vergleichen.
- Alle Kräfte, Momente und dynamischen Zustandsverläufe bestehen die
  vF1.2-Fehlergates; Interpolation darf keine falsche Solverkonvergenz
  verursachen.
- End-to-End-Benchmark muss gegenüber dem besten bereits abgenommenen Pfad
  einen messbaren Gewinn zeigen und denselben Überlast-/GUI-Test bestehen.
- Bei einem fehlgeschlagenen Genauigkeits- oder Performancegate bleibt das
  Kennfeld deaktiviert; exakter CPU-/GPU-Pfad bleibt verfügbar.

## 12. Phase 9 – Gesamtabnahme

### 12.1 Numerische und funktionale Abnahme

1. Gezielte Tests für alle geänderten Geometrie-, Hydrostatik-, Solver-,
   Backend-, Zeitschritt- und GUI-Schnittstellen ausführen.
2. Analytische Körper in trockenem, tangentialem, teilweisem und vollständigem
   Eintauchen sowie in aufrechter, Roll-, Nick- und kombinierten
   6-DOF-Orientierungen auswerten.
3. Yacht-Union mit Überlappungsbehandlung, repräsentative Gleichgewichtslage,
   statische Solverdiagnosen und dynamische Zeitverläufe prüfen.
4. Für alle Vergleichswerte vorab `S`, Zustands-/Kraftgrößen, Einheiten,
   Zeitpunkte und Normen festhalten. Maximal- und RMS-Fehler, Winkel- und
   Quaternionenabstand gemäß Spezifikation berechnen.
5. Geometrieausschlüsse mit Grenz- und Tangentialtests gegen die vollständige
   Referenz bestätigen. Kein Pflichtkörper darf durch die Broad-Phase
   verloren gehen.

### 12.2 Performanceabnahme

1. Zielhardware: dokumentiertes Windows-x64-Profil mit Ryzen 5 8600G,
   Radeon 760M und 32 GB RAM. Treiber, Python, Pakete und Backendversion
   zusammen mit dem Lauf protokollieren.
2. Repräsentative interaktive Last gemäß Phase 0 mindestens zehn Minuten
   nach 30 Sekunden Warm-up ausführen; Rückstand sekündlich erfassen.
3. Freigabegates aus Spezifikation Abschnitt 2.1 vollständig bestehen:
   mindestens 30 FPS, Eingabereaktion p95 höchstens 100 ms, mindestens
   `1,0x` stationärer Physikdurchsatz, Rückstand p95 höchstens 100 ms und
   Rückstandszunahme höchstens `50 ms`. Dafür die sekündlichen
   Rückstandswerte der letzten fünf Minuten linear gegen Wandzeit regressieren
   und die vorhergesagte Zunahme vom Anfang bis zum Ende des Fensters prüfen.
4. Jede automatische Überlastpause im zehnminütigen Abnahmelauf ist ein
   fehlgeschlagenes Freigabegate, selbst wenn der Rückstand anschließend
   abgebaut wird. Physikdurchsatz sowohl über gesamte Wandzeit als auch
   aktive Nachholung berichten; Pausenzeit nicht aus der Gesamtmessung
   herausrechnen.
5. Messbedingungen nicht nachträglich ändern, um ein Gate zu erreichen.
   Abweichungen samt Ursache und Messstreuung dokumentieren; ein nicht
   bestandenes Gate blockiert die Freigabe des interaktiven Pfads.
6. CPU und GPU mit identischer Eingabe, Renderlast und Genauigkeit messen.
   GPU nur dann als Produktionspfad freigeben, wenn reales Kernelresultat,
   Numerikgates und das Phase-0-Verfahren gemeinsam nachweisen, dass das
   untere Ende des 95-%-Konfidenzintervalls der relativen p95-Verbesserung
   mindestens `10 %` beträgt. Bildrate und Eingabelatenz dürfen sich nicht
   verschlechtern. Andernfalls CPU verwenden.

### 12.3 Regression und Abschluss

- Vollständige Testsuite mit der Projektumgebung ausführen:

  ```powershell
  .\.venv\Scripts\python.exe -m pytest
  ```

- Abhängigkeiten prüfen:

  ```powershell
  .\.venv\Scripts\python.exe -m pip check
  ```

- GUI unter Qt-Offscreen und als normaler Windows-Prozess mit QtInteractor
  starten. Bestehende Modi, Zeittasten, Körperbaum, Layer, Kamera,
  Hintergründe, Beleuchtung, Wasseroberfläche, Wasseroptik, SSAO, Farben,
  Wasserlinienschnitt, Pose, Docks und Material-Sitzungssemantik regressiv
  prüfen.
- `git diff --check` ausführen und prüfen, dass reale Modellquellen und
  JSON-Konfigurationen unverändert sind. Temporäre Korrektur-/Benchmarkdaten
  aufräumen.
- Abschlussbericht enthält genaue Testresultate, alle Gates, Hardware,
  Laufparameter, bekannte Einschränkungen, aktive Rechenpfade und
  Fallbackverhalten. Kein dokumentierter Messwert wird als allgemeine
  Garantie für abweichende Hardware ausgegeben.

## 13. Freigabe- und Rückfallregeln

- Der Produktionspfad ist nur freigegeben, wenn numerische, funktionale,
  GUI- und Performancegates dieser Spezifikation bestanden sind.
- Eine dokumentierte Ausnahme ersetzt kein Freigabegate. Bei fehlendem Gate
  bleibt der zuletzt freigegebene funktionsfähige Pfad aktiv; ein nicht
  freigegebener Näherungs- oder GPU-Pfad bleibt Opt-in bzw. deaktiviert.
- Jede GPU-Störung wird mit Ursache protokolliert; bei verfügbarer,
  korrekter CPU-Ausführung wird dieselbe Pose auf CPU wiederholt.
- Ein falsches oder nicht endliches Resultat darf niemals als erfolgreicher
  Physikschritt oder als erfolgreich abgeschlossene Nachholung gelten.
- Die automatische Überlastpause erhält den Rückstand und meldet ihn über
  vorhandene Statusflächen. Im Abnahmelauf führt jede automatische Pause zum
  Nichtbestehen; während Entwicklung bleibt die Pause ein Schutz gegen
  unbeschränktes Rückstandswachstum.
- Keine Auflösung, Kennfeldgrenze, Solver-/Fehlertoleranz oder
  Lastkonfiguration wird nach Kenntnis eines Fehlers still gelockert.

## 14. Nichtziele

- Keine Änderung der bestehenden GUI-Anordnung und keine neuen allgemeinen
  Bedienelemente.
- Keine Suche nach sämtlichen stabilen Gleichgewichtslagen.
- Kein adaptiver Integrationszeitschritt als Ersatz für schnellere
  Kraftauswertung.
- Keine Laufzeit-Benchmarks oder leistungsabhängige CPU/GPU-Umschaltung pro
  Pose.
- Keine GPU-Freigabe allein aufgrund von Geräteerkennung, Import oder
  isolierter Kernelzeit.
- Keine automatische Änderung an Modellquellen durch Broad-Phase,
  Näherungs- oder Performanceoptimierungen.
- Keine Verwendung unbelegter Widerstands-/Added-Mass-Koeffizienten.
- Kein Commit, Tag oder Push ohne ausdrücklichen Auftrag.
