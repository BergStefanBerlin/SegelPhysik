# Spezifikation V0.12: Echtzeit-Performance und messgestützte Speed-Optimierung

**Stand:** 21.10.2026  
**Status:** Entwurf; Echtzeit- und Kapazitätsziele ergänzt, vorgeschlagene Schwellenwerte noch zu bestätigen
**Ausgangsbasis:** V0.12, Branch `main`, Revision `5632ff3` zuzüglich des bei der Messung exakt zu erfassenden Arbeitsstands  
**Maßgebliche Spezifikation für V0.12:** diese Datei

## 1. Ziel, Geltung und Grundlagen

Ziel ist, die bestehende dynamische Simulation so zu optimieren, dass sie
im repräsentativen Echtzeitbetrieb die angeforderte Simulationszeit
zuverlässig nachholt und eine flüssige Anzeige ermöglicht. Zusätzlich soll
eine geschätzte Rechenreserve für eine spätere Windsimulation eingeplant
werden. Die Windsimulation selbst, neue Funktionen, Kräfte, physische Modelle
und neue Simulationsverfahren sind nicht Teil dieses Umfangs.

Es gibt keinen prozentualen Mindestwert für eine einzelne Maßnahme oder für
die Gesamtbeschleunigung. Jede belastbar nachgewiesene Verbesserung wird
berücksichtigt; auch kleine Verbesserungen können sich kumulativ auszahlen.
Ergebnisse innerhalb der Messunsicherheit gelten als unklar und dürfen nicht
als Verbesserung behauptet werden. Ein Messgewinn wird nur für die
tatsächlich gemessene Messgrenze ausgewiesen; isolierte Komponenten- oder
Mikrobenchmarkgewinne belegen für sich allein keine Verbesserung des
End-to-End-Workflows.

Optimierungen dürfen weder fachliche Ergebnisse und Stabilität noch die
Performance in einem vorab festgelegten Pflichtszenario relevant
verschlechtern. Eine reproduzierbare Verschlechterung außerhalb der
Messunsicherheit in einem Pflichtszenario spricht gegen die Maßnahme und
wird nicht automatisch durch einen Gewinn in einem anderen Szenario
aufgewogen.

Diese Spezifikation gilt für die Speed-Arbeit in V0.12. Sie autorisiert
weder Produktivcodeänderungen noch die Lockerung von Genauigkeitsverträgen,
die Einführung einer Approximation oder Git-Aktionen. Die historische
Speed-Analyse und ihre Nachprüfung in Abschnitt 9 dienen als Kandidaten-
und Bewertungsquelle, nicht als bestätigte Leistungsmessung.

Grundlagen und Regelungen:

- [Speed-Analyse und V0.12-Nachprüfung](../../zuV0.12/Optimierung/Speed_2_2_2_2_2.md):
  historische Codeanalyse und aktualisierter Befundabgleich. Ihre geschätzten
  Millisekunden, Faktoren, Prozentwerte und FPS sind keine Messwerte und keine
  verbindlichen Zielwerte.
- [Vorläufige Optimierungsliste Performance V0.12](../Optimierung/Vorlaeufige_Optimierungsliste_Performance_V0.12.md):
  Kandidatenbeschreibung und vorgeschlagene Arbeitsreihenfolge; sie ist
  unterstützende Quelle und keine zweite Spezifikation.
- [V0.12-Speed-Messdaten](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json):
  Rohwerte und bereits bewertete GUI-Kandidaten. Das dort gespeicherte
  frühere Akzeptanzfeld ist historischer Metadatenstand; für die aktuelle
  Bewertung gelten ausschließlich diese Spezifikation und der
  [Umsetzungsplan V0.12](../Umsetzungsanleitungen/Umsetzungsplan_V0.12.md).
  Vollständige Baseline-Läufe werden nicht wiederholt.
- [Testpflege-Instruction](../../../../../.github/instructions/teststruktur.instructions.md):
  maßgebliche Regeln für Testauswahl, unabhängige Referenzen und
  reproduzierbare Performancebelege.
- [Nummerierungs-Instruction](../../../../../.github/instructions/nummerierung.instructions.md):
  maßgebliche Kennungs- und Rückverfolgbarkeitsregeln.
- [Releaseumsetzungs-Instruction](../../../../../.github/instructions/releaseumsetzung.instructions.md):
  maßgeblich für den
  [Umsetzungsplan V0.12](../Umsetzungsanleitungen/Umsetzungsplan_V0.12.md)
  und die Statusführung.

Der Umfang dieser Spezifikation ist auf die Optimierung bereits
implementierter Funktionen begrenzt. Eine neue Windsimulation, neue
Kraftgesetze, neue physische Modelle und Näherungsverfahren sind nicht
enthalten. Eine Reserve für spätere Windlast ist ausschließlich ein
vorläufiges Kapazitätsziel, keine Implementierung oder Simulation dieser
Last. Die in der vorläufigen Optimierungsliste aufgeführten P-IDs sind
Kandidatenverweise, keine Anforderungskennungen und keine pauschale Freigabe
zur Umsetzung. Vorhandene Messdaten werden als Baseline übernommen. Für
diese Spezifikation werden keine Messungen wiederholt oder neu gestartet;
spätere Kandidatenmessungen unterliegen A-V0.12-00007 und erfordern einen
ausgewählten Kandidaten mit einer bislang unbeantworteten Messfrage.

## 2. Aktive Anforderungen

| Kennung | Anforderung | Abnahmekriterium |
|---|---|---|
| A-V0.12-00001 | Reproduzierbare Ausgangsleistung je relevantem Szenario erfassen | Für neue Messungen sind Ausgangsrevision und exakter Arbeitsstand, Eingaben/Modell, Hardware und Build, Rechenpfad, Thread-/Prozesszahl, Batch-/Schrittzahl, Warm-up, Messgrenzen, mindestens fünf Messungen je neu gemessener Variante, Median, Streuung und Rohdaten dokumentiert. Bereits vorhandene Messreihen werden unverändert übernommen; ihre Stichprobengröße und dokumentierte Streuung werden berichtet und nicht durch Wiederholung oder Auffüllen ergänzt (A-V0.12-00007). Kaltstart/Setup und wiederholter Warm-Pfad sind getrennt, sofern beides relevant ist und noch nicht bereits erhoben wurde. |
| A-V0.12-00002 | Nur repräsentative, tatsächlich relevante Workloads messen | Der native CPP-Standardpfad und der relevante GUI-Pfad werden getrennt betrachtet. Python-Referenz-, Voxel- oder OpenCL-Messungen werden nur aufgenommen, wenn der jeweilige Pfad im V0.12-Umfang tatsächlich genutzt oder gezielt geändert wird. Für teure reale Integration wird das Folkeboot verwendet; analytische Grundkörper sichern unabhängig davon gezielte Fachverträge. Es gibt kein routinemäßiges Kreuzprodukt über alle Yachten. |
| A-V0.12-00003 | Umsetzungsumfang nach dem gemessenen Engpass festlegen | Vor einer Produktivoptimierung werden Profilbefund, Aufrufhäufigkeit, Beitrag zur Gesamtlaufzeit, betroffener Rechenpfad und erwartete Messunsicherheit dokumentiert. Nur daraus priorisierte Maßnahmen gehören zum Umfang; die Baseline allein ist kein Umsetzungsauftrag. |
| A-V0.12-00004 | Fachliche Korrektheit und bestehende Rechenverträge erhalten | Für jeden geänderten Pfad bestehen vor/nach der Änderung passende gezielte Tests und unabhängige Referenzen. Analytische, Grenzfall-, Integrations- und erforderlichenfalls Python/C++-Paritätsprüfungen bleiben erfolgreich; bestehende Toleranzen und bit-exakte Verträge werden nicht pauschal gelockert. |
| A-V0.12-00005 | Näherungsverfahren von exakten Pfaden trennen und ausdrücklich freigeben | Voxel-, Delta-Cache- oder andere Näherungen dürfen nicht stillschweigend einen exakten Produktionspfad ersetzen. Eine etwaige Aufnahme erfordert eine vorherige fachliche Nutzerentscheidung, dokumentiertes Fehlerbudget und unabhängige Validierung gegen den exakten Referenzpfad; ohne diese Freigabe bleibt die Maßnahme ausgeschlossen. |
| A-V0.12-00006 | Belastbare Performanceverbesserungen ohne relevante Regressionen erzielen | Es gilt kein prozentualer Mindestwert für eine einzelne Optimierung oder die Gesamtbeschleunigung. Jede nachweisbare Verbesserung wird mit Messgrenze, Referenzwert, Kandidatenwert, Rohdaten und Unsicherheit dokumentiert; mehrere Verbesserungen dürfen kumulativ ausgewiesen werden, sofern ihre Wirkung auf derselben vergleichbaren Messgrenze tatsächlich gemessen ist. Ein Ergebnis innerhalb der Messunsicherheit wird als unklar und nicht als Verbesserung ausgewiesen. In keinem vorab festgelegten Pflichtszenario darf eine reproduzierbare Performanceverschlechterung außerhalb der Messunsicherheit auftreten; ebenso müssen Korrektheit und Stabilität erhalten bleiben. Ein Gewinn in einem Szenario gleicht eine solche Regression in einem anderen nicht automatisch aus. Ein isolierter Mikrobenchmarkgewinn belegt keine Verbesserung des End-to-End-Workflows. |
| A-V0.12-00007 | Vorhandene Messungen verbindlich übernehmen und Wiederholungen ausschließen | Alle bereits erfolgten, für V0.12 relevanten Messungen werden mit ihren tatsächlich erhobenen Werten und einem Verweis auf Rohdaten bzw. Messbericht übernommen; dieselben Messungen werden nicht erneut ausgeführt, um Werte zu aktualisieren, zu bestätigen oder eine neue Baseline zu erzeugen. Das gilt insbesondere für bereits gemessene Folkeboot-/GUI-Metriken und Kandidatenvergleiche. Vorhandene Messungen werden inventarisiert und hinsichtlich Messgrenze und Bedingungen eingeordnet. Fehlende oder nicht vergleichbare Daten werden als Lücke bzw. Einschränkung ausgewiesen; eine erneute Messung einer bereits abgedeckten Messfrage erfordert eine vorherige ausdrückliche Nutzerfreigabe. Neu gemessen werden dürfen nur bisher nicht erhobene, für einen ausgewählten Kandidaten notwendige Werte, insbesondere dessen Kandidatenlauf; ein vorhandener, methodisch passender Referenzwert wird dabei wiederverwendet. |
| A-V0.12-00008 | Ausschließlich bestehende Funktionen optimieren | Umsetzungskandidaten betreffen nur bereits implementierte Physik-, Echtzeit- oder GUI-Funktionen. Neue Windsimulation, neue Kräfte, neue Yachtmodelle und neue physikalische Verfahren gehören nicht zu diesem Umfang. Ein Kandidat darf nur in den Umfang übernommen werden, wenn Profiling seine Relevanz für einen tatsächlich genutzten Pfad bestätigt. |
| A-V0.12-00009 | Native Dynamik-Kandidaten messgesteuert und vertragswahrend behandeln | Snapshot-/Kontextwiederverwendung, native Arbeitsbereiche, Compileroptimierung und hierarchische Beschleunigung des exakten Ebenenschnitts werden getrennt bewertet. Vor Umsetzung ist ihr Beitrag im nativen C++-Standardpfad einschließlich relevanter Setup- und Batchkosten zu belegen. Änderungen an Snapshot-Lebensdauer oder Speicherwiederverwendung müssen Thread-Sicherheit, Eigentum und Invalidierung für Modell-, Mesh- und Gelenkänderungen erhalten. Ein hierarchischer Ebenenschnitt darf nur übernommen werden, wenn seine mathematische Korrektheit für Volumen und Schwerpunkt nachgewiesen und Parität innerhalb der bestehenden Verträge belegt ist. |
| A-V0.12-00010 | Worker-Batchgröße nur unter Echtzeit-Gegengates variieren | Änderungen an der Batch-/Taskgröße werden nur bei belegtem Übergabeanteil untersucht. Neben dem Rechendurchsatz werden Rückstandstrend, Eingabelatenz, Bedienbarkeit und Aktualität der Anzeige unter gleichen Bedingungen verglichen. Keine pauschale Batchvergrößerung. |
| A-V0.12-00011 | GUI-Optimierungen auf den tatsächlich betroffenen Framepfad begrenzen | Wasserlinienschnitt, alternative VTK-Schnittverfahren, Wasser-Splat und Gelenk-Updates werden nur weiterverfolgt, wenn eine gezielte Messung den jeweiligen GUI-/Interaktionsanteil bestätigt. Ruhelage und bewegte Lage sind getrennt zu betrachten. Alternative Schnittverfahren müssen den bestehenden Geometrie-, Deckel- und Anzeigevertrag erhalten; ein GUI-Schnittverfahren ersetzt nicht die Hydrostatik-Auswertung von Volumen und Schwerpunkt. |
| A-V0.12-00012 | Python-Referenzoptimierungen vom nativen Produktionspfad trennen | Python-Validierungs-, Wrench-/Objektketten- und Hydrodynamik-Temporärdaten-Kandidaten werden nur umgesetzt, wenn der Python-Referenzpfad ausdrücklich zum freigegebenen Nutzungs-/Prüfumfang gehört oder dort ein relevanter Engpass nachgewiesen ist. Ihre Ergebnisse dürfen nicht als Beschleunigung des nativen C++-Standardpfads gewertet werden. |
| A-V0.12-00016 | Echtzeitdurchsatz und Rückstand für die dynamische Simulation erfüllen | Im bestehenden repräsentativen Folkeboot-Szenario muss die angeforderte Simulationszeit nach der Anlaufphase mindestens im Verhältnis 1:1 zur Wandzeit nachgeholt werden; der Physikrückstand darf im Messfenster keinen positiven Wachstumstrend zeigen. Hardware, Modell und Rechenpfad werden gegenüber dem passenden vorhandenen Beleg gleich gehalten. Bestehende Durchsatz- und Rückstandswerte sind Ausgangsbefund und werden nicht wiederholt. |
| A-V0.12-00017 | Flüssige GUI-Aktualisierung anhand tatsächlicher Swap-Signale nachweisen | Vorgeschlagenes Ziel: mindestens 30 Qt-`frameSwapped`-Signale/s im Median und höchstens 50 ms Frameintervall beim 95. Perzentil. Eingabe-bis-Swap wird getrennt berichtet; ein `frameSwapped`-Signal belegt keine tatsächliche Monitor-Präsentation. Schwellenwerte sind vor Umsetzung fachlich zu bestätigen. |
| A-V0.12-00018 | Geschätzte Reserve für eine spätere Windsimulation einplanen | Vorgeschlagenes Planungsziel: mindestens 1,6-facher Durchsatz des aktuellen Basisszenarios. Die Schätzung setzt vorläufig 25 % Zusatzlast für eine spätere Windberechnung und 20 % verbleibende Kapazitätsreserve an; beide Werte sind Planungsannahmen, keine gemessene Windlast. Es wird keine Windsimulation implementiert oder ausgeführt. Die Annahmen und Zielschwelle sind vor Umsetzung fachlich zu bestätigen. |
| A-V0.12-00019 | Die nächste Optimierungsrunde auf vorhandene Evidenz und offene Kandidaten begrenzen | Die vorhandenen Speed-Messungen und bereits abgeschlossenen Kandidaten werden als Ist-Stand übernommen. Noch offene Kandidaten aus der Optimierungsliste werden anhand des belegten Gesamtszenario-Engpasses, Aufrufhäufigkeit, Risiko und Unsicherheit priorisiert. Nicht gemessene Potentialschätzungen sind keine Leistungsnachweise; Kandidaten werden nicht pauschal umgesetzt. |

## 3. Mess- und Vergleichsregeln

### 3.1 Ausgangszustand und Messgrenzen

Die bereits erfassten V0.12-Speed-Messdaten sind verbindliche Messbelege für
die darin enthaltenen Folkeboot-/GUI-Signale. Ihre Werte werden unverändert
aus den vorhandenen Messdateien übernommen und mit Verweis auf Messdatei,
Metrik und Messbedingungen dokumentiert. Bereits erhobene Messungen werden
nicht wiederholt, auch nicht zur Aktualisierung oder Bestätigung der
Baseline. Das gilt ebenso für bereits dokumentierte Kandidatenmessungen.
Eine abweichende Revision, Messgrenze oder Bedingung macht einen vorhandenen
Wert gegebenenfalls nur eingeschränkt vergleichbar; sie ist als Einschränkung
zu dokumentieren und rechtfertigt für sich allein keine Wiederholung.

Vor Beginn ergänzender Messungen wird ein Inventar der vorhandenen Messwerte
erstellt, das mindestens Messfrage/Kandidat, Metrik, Messgrenze, Modell bzw.
Pfad, Messbedingungen, vorhandenen Wert und Rohdatenverweis festhält.
Fehlende native Dynamik- oder Komponentenanteile dürfen gezielt neu gemessen
werden, sofern sie bisher nicht erhoben wurden und für einen ausgewählten
Kandidaten notwendig sind. Dabei wird ein passender vorhandener Referenzwert
wiederverwendet; die Referenzmessung wird nicht erneut ausgeführt. Ergibt das
Inventar eine Vergleichbarkeits- oder Nachweislücke für eine bereits
abgedeckte Messfrage, wird diese zunächst als Lücke ausgewiesen. Eine
Wiederholung genau dieser Messung ist nur nach vorheriger ausdrücklicher
Nutzerfreigabe zulässig. Die vollständige Baseline-Messreihe wird nicht
erneut ausgeführt.

Für jede ergänzende Messung ist der Ausgangszustand eindeutig festzuhalten. Dazu
gehören mindestens der Git-Commit und – bei nicht sauberem Arbeitsbaum – die
relevanten Änderungen einschließlich eines reproduzierbaren Patches oder
Hash-Belegs, Python-/Compiler-/Build-Identität, Betriebssystem und
Hardwarekonfiguration. Baseline und Kandidat müssen auf demselben
Ausgangsstand aufbauen; fremde oder nicht zum Auftrag gehörende Änderungen
dürfen nicht unbemerkt in eine Variante einfließen.

Referenz und Kandidat verwenden dieselben Eingaben, Modellstände,
Rechenpfade, Prozess-/Threadzahlen und Batch-/Schrittzahlen. Messungen
weisen explizit aus, ob sie Setup, Snapshot-Erzeugung, Datentransfer,
Integration, GUI-Schnitt, Rendering oder Gesamtworkflow umfassen.
Verschachtelte oder überlappende Komponentenmessungen werden nicht
additiv als Gesamtersparnis interpretiert.

Für neu zu erhebende Varianten wird mindestens ein separater Warm-up-Lauf
und danach eine Serie von mindestens fünf Messungen verwendet. Berichtet
werden Rohdaten, Median und Streuung. Bereits vorhandene Messreihen werden
mit ihrer tatsächlichen Stichprobengröße, ihren tatsächlich erhobenen
Werten und ihrer vorhandenen Streuungsinformation übernommen; sie werden
weder wiederholt noch zur Erfüllung einer Mindeststichprobengröße ergänzt.
Fehlende Streuungs- oder Umgebungsangaben werden als Einschränkung
ausgewiesen, nicht durch erneutes Messen ersetzt. Kaltstart, Cache-Aufbau
und wiederholter Lauf werden nur dann getrennt neu erfasst, wenn diese
Nutzungssituationen für den Kandidaten relevant und nicht schon gemessen
sind. Während neu erhobener Variantenmessungen darf keine konkurrierende
Benchmark- oder Testlast laufen.

### 3.2 Szenarien und Modelle

- **Native Physik:** vollständige repräsentative Batch-Ausführung im
  Standardpfad einschließlich der für den Nutzer relevanten Worker- und
  Übergabekosten; isolierte native Mikrobenchmarks ergänzen, ersetzen aber
  nicht die End-to-End-Messung.
- **GUI:** Schnitt-/Geometrieaufbereitung, Renderanforderung und
  Frame-Gesamtdauer unterscheidbar messen; Ruhelage und bewegte Lage nicht
  vermischen.
- **Bedingte Pfade:** Python-Referenz, voxelbasiert und optional OpenCL nur
  dann messen und berichten, wenn dieser Pfad Bestandteil des freigegebenen
  Umfangs ist. Ergebnisse verschiedener Pfade werden nicht zu einer
  Rangliste ohne Nutzungsgewichtung zusammengefasst.
- **Reale Integration:** Folkeboot als repräsentative Yacht für notwendige
  teure Messungen. Quader und gegebenenfalls Kugel dienen schnellen,
  analytisch prüfbaren Verträgen. Der Optimist ist wegen des bekannten
  instabilen Modellstands kein allgemeiner Performance- oder
  Stabilitäts-Abnahmemaßstab; spezifische bestehende Verträge werden dadurch
  nicht automatisch aufgehoben.

### 3.3 Auswahl der Optimierung

Die Baseline muss zunächst zeigen, welche Kosten im relevanten Szenario
signifikant sind. Eine hohe asymptotische Komplexität, sichtbare Schleife,
geschätzte Einsparung oder niedrige Aufwandseinschätzung allein reicht nicht
als Priorisierungsnachweis. Für jeden gewählten Kandidaten werden
Nutzungsbedingung, Messbefund, betroffene Verträge, Risiko und
End-to-End-Erwartung festgehalten.

Vor Kandidatenmessungen und Produktivänderungen sind die relevanten
Nutzungsszenarien, Messgrenzen, Messmethoden und Pflichtszenarien im
Umsetzungsplan festzuschreiben. Es gibt keine Mindestgröße für den Gewinn:
kleine Verbesserungen werden berücksichtigt, wenn sie anhand der Messdaten
belastbar von der Unsicherheit unterschieden werden können. Ein
Mikrobenchmarkgewinn wird nur dem gemessenen Teilpfad zugerechnet und nicht
als End-to-End-Gewinn ausgegeben. Performanceverschlechterungen außerhalb
der Messunsicherheit in einem Pflichtszenario sind als Regression
auszuweisen und schließen eine vorbehaltlose Abnahme der Maßnahme aus.

### 3.4 Kandidaten und vorgeschlagene Reihenfolge

Die vorläufigen IDs beziehen sich auf die
[Vorläufige Optimierungsliste Performance V0.12](../Optimierung/Vorlaeufige_Optimierungsliste_Performance_V0.12.md).
Sie bleiben Arbeitsverweise; maßgeblich sind die Anforderungen dieser
Spezifikation. Die Reihenfolge ist eine Untersuchungshypothese und wird nach
Profilbefund angepasst. Sie bedeutet nicht, dass alle Kandidaten zwingend
implementiert werden.

| Reihenfolge | Kandidat | Spezifikationsbehandlung |
|---:|---|---|
| 0 | Baseline und gezieltes Profiling | Vorhandene Messreihe übernehmen. Für den ersten relevanten Kandidaten fehlende Zeitanteile gezielt messen; keinen vollständigen Baseline-Lauf ohne konkreten Bedarf wiederholen. |
| 1 | **P-02 Snapshot pro Echtzeit-Task** | Im nativen Pfad Snapshot- und Kontextaufbereitung getrennt profilieren. Wiederverwendung nur bei belegtem Aufwand und nachgewiesener Invalidierung/Lebensdauer. |
| 2 | **P-03 Wiederverwendbare native Arbeitsbereiche** | Allokationen und temporäre Speicherarbeit in den nativen Hydrostatik- und Hydrodynamikschleifen profilieren; bei relevantem Anteil gezielt reduzieren. |
| 3 | **P-04 Compiler-Vektorisierung und Profiloptimierung** | Für relevante Release-Schleifen Compilerberichte und gegebenenfalls PGO prüfen. Compiler-/Hardwareeffekt messen; keine ungesicherten Genauigkeitslockerungen oder pauschalen Flags. |
| 4 | **P-01 Hierarchischer exakter Ebenenschnitt** | Nur bei relevantem Hydrostatikanteil prototypisch untersuchen. Aggregation vollständig ein-/ausgeschlossener Meshbereiche mathematisch herleiten; gegen den bestehenden exakten Algorithmus prüfen. |
| 5 | **P-06 Task-Batchgröße und Übergabekosten** | Nur bei relevantem Worker-/Übergabeanteil vergleichen; Echtzeit-Gegengates aus A-V0.12-00010 gelten. |
| 6 | **P-07 GUI-Wasserlinienschnitt bei unveränderter Pose** | Messung im Ruhe- und Bewegungsszenario; nur tatsächlich redundante Arbeit bei unveränderter Pose/Geometrie vermeiden. |
| 7 | **P-08 VTK-PlaneCutter für GUI-Schnitte** | Alternative nur dann vergleichen, wenn P-07 einen relevanten GUI-Schnittanteil zeigt. Kaltstart, Wiederverwendung, Ausgabe- und Deckelvertrag berücksichtigen. |
| 8 | **P-11 Wasser-Splat** | Nur bei nachgewiesenem Anteil im tatsächlichen Renderpfad; natives Backend und vorhandene Skip-Logik berücksichtigen. |
| 9 | **P-12 Gelenk-Updates in der GUI** | Nur bei nachgewiesener relevanter Interaktionslast; Endstellung und Bedienvertrag erhalten. |
| bedingt | **P-05, P-09, P-10 Python-Referenzpfad** | Nur bei ausdrücklicher Einbeziehung des Referenzpfads und Profilnachweis; getrennt vom nativen Standardpfad berichten. |

Für jeden Kandidaten wird vor der Umsetzung festgehalten, welcher Anteil
gemessen wird, wie oft er im repräsentativen Szenario auftritt, welche
Messwerte vorhanden sind und welche Korrektheits-/Vertragsprüfungen gelten.
Als derzeit vorhandene, nicht kandidatenisolierte Referenzen gelten:
Worker-Batch **1,639 ms**, Worker-Roundtrip **15,259 ms**, Pose-Aufruf
**4,447 ms**, Render-Aufruf **24,920 ms** sowie Durchsatz **0,976
Simulationssekunden/Wandsekunde** im dokumentierten Folkeboot-Szenario.
Diese Werte dürfen nicht als gemessene Einzelkosten eines Kandidaten
ausgegeben werden. Einzelzeit-Schätzungen aus Codeanalyse sind ausdrücklich
keine Messwerte.

#### Kandidatenstatus nach vorhandener Evidenz

Die Kandidaten-IDs und Namen beziehen sich auf die
[vorläufige Optimierungsliste](../Optimierung/Vorlaeufige_Optimierungsliste_Performance_V0.12.md).
Die Bezeichnung ist maßgeblich, falls sie in älteren Texten abweichend
zugeordnet wurde.

| Kandidat | Stand anhand vorhandener Belege | Weiteres Vorgehen |
|---|---|---|
| P-01 Hierarchischer exakter Ebenenschnitt | Keine isolierte Messung oder Umsetzung belegt. | **Derzeit nicht ausgewählt.** Erst nach Profilnachweis eines relevanten Hydrostatikanteils erneut entscheiden; exakte Volumen- und Schwerpunktverträge erhalten. |
| P-02 Snapshot pro Echtzeit-Task | Snapshot-Aufbereitung liegt im Setup/Workerstart; kein wiederholter Einzelstep-Gewinn belegt. | **Nicht ausgewählt.** Kein wiederholter Taskanteil ist nachgewiesen. |
| P-03 Wiederverwendbare native Arbeitsbereiche | Hydrodynamik-Arbeitsbereich umgesetzt; Worker-Batch-Median 1,66495 → 1,47140 ms (-11,62 %). Hydrostatik-Arbeitsbereiche sind damit nicht als erledigt belegt. | **Umgesetzt und beibehalten:** nur der gemessene Hydrodynamik-Anteil. Hydrostatik-Erweiterung nicht ausgewählt, solange kein eigener Kostenbeleg vorliegt. |
| P-04 Compiler-Vektorisierung und Profiloptimierung | Keine projektspezifische Messung oder Umsetzung belegt. | **Derzeit nicht ausgewählt.** Es fehlt ein belegter nativer Hotspot und ein zugehöriger Buildvergleich. |
| P-05 Python: Kraft-/Wrench-Objektkette | Keine Messung oder Umsetzung belegt; Python-Referenzpfad ist nicht der native Produktionspfad. | **Nicht ausgewählt** für das Ziel des nativen Echtzeit- und GUI-Pfads. |
| P-06 Task-Batchgröße und Übergabekosten | Worker-Batch und Worker-Roundtrip wurden gemessen; keine Vergleichsreihe verschiedener Batchgrößen. | **Derzeit nicht ausgewählt.** Die Roundtrip-Differenz ist keine reine Übergabezeit; es fehlt ein belegter Vorteil bei bestandenen Echtzeit-Gegengates. |
| P-07 GUI-Wasserlinienschnitt bei unveränderter Pose | Keine isolierte Schnittmessung belegt. | **Derzeit nicht ausgewählt.** Erst nach Nachweis, dass Schnittaufbau im relevanten Framepfad einen nennenswerten Anteil hat. |
| P-08 VTK-PlaneCutter für GUI-Schnitte | Keine Vergleichsmessung belegt. | **Nicht ausgewählt:** keine Vergleichsevidenz und P-07-Anteil nicht belegt. |
| P-09 Python: konstante Validierungen | Keine Messung oder Umsetzung belegt; Python-Referenzpfad. | **Nicht ausgewählt** für das Ziel des nativen Echtzeit- und GUI-Pfads. |
| P-10 Python: Hydrodynamik-Temporärdaten | Keine Messung oder Umsetzung belegt; Python-Referenzpfad. | **Nicht ausgewählt** für das Ziel des nativen Echtzeit- und GUI-Pfads. |
| P-11 Wasser-Splat im Renderpfad | Kein isolierter Zeitwert belegt. | **Derzeit nicht ausgewählt.** Es fehlt ein Messnachweis des Splat-Anteils im tatsächlichen Renderpfad. |
| P-12 Gelenk-Updates in der GUI | Ereigniszeit und Ereignishäufigkeit sind nicht isoliert belegt. | **Nicht ausgewählt** für den normalen dynamischen Lauf; keine repräsentative Gelenk-Interaktionslast liegt vor. |

#### Entscheidung zum SSAO-off-Versuch

Die fünf bereits abgeschlossenen Folkeboot-Läufe mit deaktiviertem SSAO
werden als vorhandene Kandidatenmessung übernommen; sie sind kein Auftrag,
SSAO dauerhaft abzuschalten. Gegenüber den fünf vorhandenen
GUI-Baseline-Läufen zeigen die Laufmediane:

| Metrik | Baseline-Median | SSAO-off-Median | Einordnung |
|---|---:|---:|---|
| Abgeschlossene Frames/s | 6,79 | 6,37 | Kein Gewinn; Median niedriger. |
| Frameintervall p95 | 200,489 ms | 227,502 ms | Deskriptiv schlechter; Laufbereiche überlappen teilweise. |
| Renderaufruf-Median | 24,920 ms | 23,249 ms | Teilpfad um ca. 6,7 % kürzer, aber kein Beleg für einen End-to-End-Gewinn. |
| Physikdurchsatz | 0,975985 | 0,978823 Simulationssekunden/Wandsekunde | Unterschied klein und angesichts der Laufstreuung nicht als belastbarer Gewinn belegt. |

Rohdaten: `gui_native_1.json` bis `gui_native_5.json` und
`render_no_ssao_1.json` bis `render_no_ssao_5.json` im Verzeichnis
`../Messungen/Speed_V0.12_2026-10-21/`. Der Versuch rechtfertigt weder eine
Standardänderung an der Darstellung noch die Behauptung einer flüssigeren
GUI. „SSAO standardmäßig deaktivieren“ wird deshalb **nicht** als
Umsetzungsmaßnahme ausgewählt.

#### Vorhandene Echtzeit-Ausgangswerte und vorgeschlagene Zielschwellen

Die folgenden Werte stammen aus den bereits vorhandenen Messdateien. Es
wurden für diese Spezifikation keine Baseline- oder Kandidatenläufe
wiederholt. Die fünf SSAO-off-Läufe waren bereits abgeschlossen und werden
im vorstehenden Abschnitt bewertet:

| Messsignal | Vorhandener Wert | Bedeutung für das Ziel |
|---|---:|---|
| Folkeboot-Simulationsdurchsatz, ursprüngliche Baseline | 0,975985 Simulationssekunden/Wandsekunde | Unter dem Verhältnis 1:1 aus A-V0.12-00016; kein verlässliches Echtzeit-Nachholen belegt. |
| Folkeboot-Simulationsdurchsatz, Arbeitsbereichs-Referenz/Kandidat | 0,978208 / 0,978205 Simulationssekunden/Wandsekunde | Innerhalb der beobachteten Streuung unverändert und weiterhin unter 1:1. |
| Qt-`frameSwapped`-Intervall, Arbeitsbereichs-Referenz/Kandidat | 165,99450 / 167,07395 ms | Keine belastbare Verbesserung; der Kandidatenwert entspricht reziprok etwa 6,0 Swap-Signalen/s. Das Signal ist kein Beleg für tatsächlich am Monitor präsentierte Bilder. |
| GUI-Eingabe-bis-Swap-Median, Referenz/Kandidat | 88,659 / 93,636 ms | Median im Kandidaten höher, aber Laufbereiche überlappen; vollständige Nichtverschlechterung ist nicht belegt. |
| Worker-Batch-Median, Referenz/Kandidat | 1,66495 / 1,47140 ms | Belastbarer Gewinn für diese Messgrenze, nicht als End-to-End- oder GUI-Gewinn auszugeben. |
| Worker-Roundtrip-Median, Referenz/Kandidat | 16,14165 / 15,64300 ms | Laufbereiche überlappen; kein belastbarer Gewinn und keine reine Übergabezeit. |
| SSAO-off-Test, fünf Läufe | 6,37 abgeschlossene Frames/s; Render-Median 23,249 ms | Gegenüber Baseline kein GUI-Gewinn belegt; Einzelheiten und Entscheidung stehen oben. |
| Gezieltes GUI-Aufrufprofil | 528 Zeichenaufrufe; 4.383 Kugelmesh-Aufrufe; 2.270 `pyvista.Sphere`-Aufrufe | Diagnostische Aufrufzahlen, keine uninstrumentierten Kosten oder Performanceaussage. |

#### Gezieltes GUI-Aufrufprofil

Ein zusätzlicher 45-s-Folkeboot-Lauf mit `--callback-profile` wurde
ausschließlich zur Aufrufattribution erhoben. Das Profil erfasste 650
instrumentierte Render-/Pose-Aufrufe; darin traten unter anderem
`KraefteZeichner.zeichnen` 528-mal, `_kugel_mesh` 4.383-mal und
`pyvista.Sphere` 2.270-mal auf. Die Profilierung verlangsamt den GUI-Pfad
stark: der gemessene Durchsatz sank im Diagnoselauf auf 0,739
Simulationssekunden/Wandsekunde; Render-/Pose-Mediane stiegen auf 65,150 /
82,645 ms. Diese Laufzeiten sind Instrumentierungseffekte und keine
vergleichbaren Leistungswerte. Die Aufrufzahlen lokalisieren lediglich
wiederholte Overlay-/Kugelgeometriearbeit; sie belegen weder deren
unprofilierte Zeitersparnis noch einen Gewinn für einen konkreten P-01 bis
P-12-Kandidaten. Die bereits implementierte Marker-Kugelvorlage bleibt
bestehen; ein neuer Geometriepfad wird nicht ohne exakte
Geometrievertragsprüfung und uninstrumentierten Kandidatenvergleich
eingeführt.

Aus dem vorhandenen Messstand folgt damit eine eindeutige aktuelle
Maßnahmenentscheidung: Die exakte Marker-Kugelvorlage bleibt als bereits
umgesetzte GUI-Optimierung bestehen; der gemessene Qt-Swap-Median sank
168,298 auf 151,201 ms, während der Simulationsdurchsatz nur von 0,975985
auf 0,976887 Simulationssekunden/Wandsekunde stieg. P-03
(Hydrodynamik-Arbeitsbereiche) bleibt als bereits umgesetzte native
Optimierung bestehen und hat einen belastbaren Gewinn auf der
Worker-Batch-Messgrenze. „SSAO dauerhaft deaktivieren“ wird verworfen.
**Keine weitere P-Maßnahme ist derzeit zur Umsetzung ausgewählt.** Die Daten
zeigen zwar einen GUI-/Frame-Pfad unter Ziel, belegen aber nicht, welcher
noch offene P-Kandidat diesen Engpass kausal behebt. Eine konkrete weitere
Codeänderung ohne diesen Nachweis wäre Spekulation und könnte die Darstellung
oder Echtzeitlatenz verschlechtern.

Belege: [bestehende Speed-Kandidatenmessungen](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json)
und [Hydrodynamik-Arbeitsbereichsauswertung](../Messungen/Speed_V0.12_2026-10-21/hydro_workspace_assessment_v0.12.json)
sowie [GUI-Aufrufprofil](../Messungen/Speed_V0.12_2026-10-21/gui_callback_attribution_2026-10-21.json).
Die Run-Bereiche sind deskriptiv und kein formales Konfidenzintervall. Ein
Qt-`frameSwapped`-Signal ist außerdem nicht gleichbedeutend mit einer
tatsächlichen Anzeige am Monitor.

Die 1,6-fache Kapazität in A-V0.12-00018 ist ein vorläufiger
Planungsrichtwert, keine aus den vorhandenen Messungen abgeleitete
Windlastmessung. Sie ergibt sich als aufgerundeter Wert aus
`(1 + 0,25) / (1 - 0,20) = 1,5625`: geschätzte Zusatzlast von 25 % des
heutigen Rechenbedarfs bei 20 % verbleibender Kapazitätsreserve. Beide
Annahmen müssen vor einer Umsetzungsfreigabe bestätigt oder angepasst
werden.

## 4. Genauigkeit, Stabilität und Näherungen

Exakte Optimierungen müssen das bestehende fachliche Ergebnis innerhalb
der geltenden Vertrags- und Toleranzgrenzen bewahren. Tests sollen die
betroffenen Randfälle und Backendgrenzen abdecken; Referenzwerte sind
unabhängig herzuleiten oder aus einem belegten Referenzverfahren zu
beziehen. Gewöhnliche Regressionstests erhalten keine fragilen
Wandzeitgrenzen.

Eine Optimierung gilt nicht allein deshalb als exakt, weil ein
Schwellwert klein, ein Cacheintervall kurz oder ein Vergleich im
ausgewählten Fall nahe an der Referenz ist. Wiederverwendung von
Hydrostatik bei geänderter Pose, Voxelraster und weitere diskrete
Näherungen verändern grundsätzlich das Rechenverfahren und benötigen
die Freigabe und Nachweise aus A-V0.12-00005.

## 5. Nachweise, Status und Abnahme

Der [Umsetzungsplan V0.12](../Umsetzungsanleitungen/Umsetzungsplan_V0.12.md)
führt für jede aktive A-Kennung mindestens einen Umsetzungsschritt,
Abhängigkeiten und prüfbare Meilenstein-/Abnahmekriterien auf. Messdaten
dürfen als unterstützende Nachweise separat gespeichert werden; die
verbindlichen Anforderungen und Schritte bleiben in den je einer
Spezifikation und einem Umsetzungsplan.

Der Abschlussbericht unterscheidet mindestens:

- Baseline erstellt oder fehlend,
- gemessene Kandidaten und begründete Auswahl,
- umgesetzte Änderungen und tatsächliche Vorher-/Nachher-Ergebnisse,
- bestandene, fehlgeschlagene oder nicht ausgeführte Korrektheitsprüfungen,
- Messunsicherheit, bekannte Regressionen und offene Punkte.

Nicht ausgeführte Pfade, Geräteprüfungen oder Gesamtprofile werden als
Prüflücke ausgewiesen. Weder ein abgeschlossener Codeänderungsschritt noch
ein schnellerer Mikrobenchmark allein bedeutet fachliche Abnahme.

## 6. Nicht umsetzen

Es wurden keine Anforderungen dieser Spezifikation zurückgezogen. Die
folgenden historischen Speed-Aussagen werden jedoch nicht als aktive
Anforderungen oder bestätigte Leistungsziele übernommen:

| Ursprüngliche Kennung/Aussage | Begründung |
|---|---|
| D1: Delta-Invalidierung sei „nahezu exakt“ beziehungsweise ohne Genauigkeitsverlust | Das Wiederverwenden der Hydrostatik bei geänderter Pose ist eine Approximation. Eine mögliche Umsetzung bleibt an A-V0.12-00005 gebunden. |
| D5: doppelte Quaternion-Rotation sei redundant | Die beiden Rotationen beziehen sich auf die alte und die neue Orientierung und sind fachlich verschieden. |
| Zeit-/Faktor-/FPS-Schätzungen aus den Abschnitten 7 und 8 der Speed-Analyse | Codeanalyse-Schätzungen ohne aktuelle Messung; sie sind weder Abnahmekriterien noch garantierte Ergebnisse. |
