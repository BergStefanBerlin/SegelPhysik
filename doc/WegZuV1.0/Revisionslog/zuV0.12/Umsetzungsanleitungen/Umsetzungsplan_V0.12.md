# Umsetzungsplan V0.12

**Stand:** 21.10.2026

**Status:** Kandidaten bewertet und Entscheidungen dokumentiert; zwei messgestützte Optimierungen sind umgesetzt, für weitere Kandidaten ist derzeit keine Produktivänderung freigegeben.

**Maßgebliche Spezifikationen:** [Testumbau V0.12](../Spezifikatonen/Spezifikation_Testumbau_V0.12.md) und [Speed V0.12](../Spezifikatonen/Spezifikation_Speed_V0.12.md)

**Historische Durchführung und Messbelege:** [Abschlussnachweis Teststruktur und bisherige Speed-Arbeiten](./Abschlussnachweis_Teststruktur_und_Speed_V0.12.md)

## 1. Zweck und verbindliche Grenzen

Dieser Plan ist die einzige maßgebliche Umsetzungsplanung für V0.12. Die
Teststruktur-Arbeiten und die früheren Speed-Versuche sind im verlinkten
Abschlussnachweis als bereits erfolgte Arbeit mit ihren Einschränkungen
festgehalten. Die bisherigen Speed-Schritte behandeln A-V0.12-00001 bis
A-V0.12-00012. Die ergänzten Echtzeit- und Kapazitätsziele
A-V0.12-00016 bis A-V0.12-00019 werden in U-V0.12-000024 ff.
nachverfolgt.

Die Speed-Spezifikation ist maßgeblich für fachlichen Umfang und Abnahme.
Dieser Plan ersetzt weder eine dort erforderliche Nutzerentscheidung noch
autorisiert er für sich allein Produktivcodeänderungen. Für die hier
dokumentierte Kandidatenumsetzung liegt der ausdrückliche Nutzerauftrag
„Führe den Umsetzungsplan möglichst selbständig aus“ vom 21.10.2026 vor;
er wurde auf den ausgewählten, messgestützten Kandidaten begrenzt.
Voxel-, Delta-Cache- und andere Näherungsverfahren bleiben ohne vorherige
ausdrückliche Freigabe ausgeschlossen.

Für diesen Plan gelten die
[Nummerierungsregel](../../../../../.github/instructions/nummerierung.instructions.md),
die [Releaseumsetzungs-Instruction](../../../../../.github/instructions/releaseumsetzung.instructions.md)
und die [Testpflege-Instruction](../../../../../.github/instructions/teststruktur.instructions.md).
Commit, Push, Tag und Release sind nicht beauftragt.

## 2. Arbeitsregeln

- Bereits erfolgte Messungen sind zu inventarisieren und mit den tatsächlich
  erhobenen Werten, Bedingungen, Messgrenzen und Rohdatenverweisen zu
  übernehmen. Sie werden nicht wiederholt, aktualisiert oder ergänzt, um
  eine Mindeststichprobengröße zu erreichen.
- Für die Ergänzung der Echtzeit- und Kapazitätsziele werden keine Messungen
  erneut ausgeführt. Vorhandene GUI-, Worker- und Durchsatzwerte werden
  unverändert als Ist-Befund verwendet; zusätzliche Kandidatenmessungen
  bleiben an eine neue, noch unbeantwortete Messfrage und eine gesonderte
  Auswahl gebunden.
- Für eine Messfrage, die in vorhandenen Belegen noch nicht erhoben wurde,
  darf die erforderliche Messung geplant werden. Ein passender vorhandener
  Referenzwert wird wiederverwendet. Eine Wiederholung bereits abgedeckter
  Messfragen ist nur nach vorheriger ausdrücklicher Nutzerfreigabe zulässig;
  der Standardweg ist, Einschränkungen als Nachweislücke auszuweisen.
- Es gibt keinen prozentualen Mindestgewinn. Kleine, belastbar erkennbare
  Zugewinne sind relevant. Ergebnisse innerhalb der vorab festgelegten
  Messunsicherheit sind unklar und kein belegter Gewinn. Jede
  Performance-Regression in einem Pflichtszenario ist separat zu bewerten
  und nicht automatisch durch einen Gewinn an anderer Stelle aufrechenbar.
- Messungen, Codeänderungen, Tests und fachliche Abnahme erhalten getrennte
  Statusangaben. Keine Schätzung oder Profil-Summe als Messwert ausgeben.
- Bestehende Testfälle werden vor dem Ergänzen neuer Tests auf passende
  Abdeckung geprüft; gleichwertige Testfälle werden nicht dupliziert.
  Bereits bestandene Testergebnisse dürfen für unveränderte Quell-,
  Build- und Teststände als Beleg referenziert werden. Nach einer
  Codeänderung werden die kleinsten fachlich ausreichenden bestehenden
  Tests für den geänderten Pfad erneut ausgeführt. Unveränderte, nicht
  betroffene Testbereiche werden nicht routinemäßig wiederholt; bei
  gemeinsam genutzten Verträgen, unklarer Reichweite oder einer
  Revisionsabnahme wird die Prüfung risikobasiert erweitert. Ein früherer
  Testlauf auf einem anderen Code- oder Buildstand ersetzt keine Prüfung
  der Änderung.
- Kandidaten in der Spezifikation sind Untersuchungshinweise, keine Pflicht,
  sie alle zu implementieren. Aufwand je Aufruf × belegte Aufrufhäufigkeit
  und realer Szenarioanteil bestimmen die Priorisierung, nicht allein ein
  Mikrobenchmark.

## 3. Übernommene Messbasis

Die folgenden Werte sind aus den vorhandenen Messdateien übernommen; sie
werden nicht neu erhoben. Die Messgrenzen sind nicht austauschbar und die
Teilwerte dürfen nicht additiv als End-to-End-Ersparnis interpretiert
werden.

| Vorhandenes Szenario / Stand | Metrik | Übernommener Wert | Beleg |
|---|---|---:|---|
| Folkeboot, `exakt_union`, C++-GUI-Baseline, fünf Läufe | Qt-`frameSwapped`-Intervall-Median | 168,298 ms | [Baseline-Rohdaten](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json), `baseline` |
| Dasselbe Baseline-Szenario | Render-Aufruf-Median | 24,920 ms | gleicher Beleg |
| Dasselbe Baseline-Szenario | Pose-Aufruf-Median | 4,447 ms | gleicher Beleg |
| Dasselbe Baseline-Szenario | Worker-Batch-Median | 1,639 ms | gleicher Beleg |
| Dasselbe Baseline-Szenario | Worker-Roundtrip-Median | 15,259 ms | gleicher Beleg |
| Dasselbe Baseline-Szenario | Simulationsdurchsatz | 0,975985 Simulationssekunden/Wandsekunde | gleicher Beleg |
| Exakter Marker-Geometriekandidat, fünf Läufe | Qt-`frameSwapped`-Intervall-Median | 151,201 ms | gleicher Beleg, `marker_template_candidate` |
| Derselbe Kandidatenstand | Render-Aufruf / Pose-Aufruf | 21,131 ms / 4,374 ms | gleicher Beleg |
| Derselbe Kandidatenstand | Worker-Batch / Roundtrip | 1,215 ms / 17,629 ms | gleicher Beleg |
| Derselbe Kandidatenstand | Simulationsdurchsatz | 0,976887 Simulationssekunden/Wandsekunde | gleicher Beleg |
| Marker plus SVG-no-op, zehn Läufe; verworfen | Qt-`frameSwapped`-Intervall-Median | 160,004 ms; kein belastbarer Gewinn, weitere Signale regressiv | gleicher Beleg, `marker_svg_candidate` |
| SVG-Vorlagen-Serializer, fünf Läufe; verworfen | Qt-`frameSwapped`-Intervall-Median | 178,82 ms; Regression gegenüber vorhandener Baseline | [Abschlussnachweis](./Abschlussnachweis_Teststruktur_und_Speed_V0.12.md), Abschnitt 8.5, und Kandidaten-Rohdaten |

Die Stichprobenumfänge, Rohwerte und vorhandenen Unsicherheitsinformationen
bleiben in den Messdateien maßgeblich. Insbesondere ist das
`acceptance`-Feld im Kandidaten-JSON ein historischer Metadatenstand und
keine aktuelle Abnahmeregel; dafür gelten Spezifikation und dieser Plan.
Für diese Bestandsdaten werden weder fehlende Läufe ergänzt noch
Baseline- oder Kandidatenläufe wiederholt.

### 3.1 Neue, zuvor nicht separat erhobene Kandidatenmessfrage

Für die Wiederverwendung nativer Hydrodynamik-Arbeitsbereiche gab es keinen
isolierten Vorher-/Nachher-Wert. Deshalb wurde ausschließlich diese neue
Messfrage erhoben: je fünf Folkeboot-Läufe mit 10 s Warm-up und 45 s
Messzeit, `exakt_union`, C++-Pfad und 640 × 480 Viewport. Die fünf früheren
GUI-/Worker-Messreihen blieben unangetastet. Rohdaten, Quell-/Umgebungs-
informationen und Einschränkungen stehen in der
[Vergleichsauswertung](../Messungen/Speed_V0.12_2026-10-21/hydro_workspace_assessment_v0.12.json).

| Messgrenze | Referenz-Median (Bereich der fünf Laufmediane) | Kandidat-Median (Bereich) | Veränderung | Bewertung |
|---|---:|---:|---:|---|
| Native Worker-Batchzeit | 1,66495 ms (1,61910–1,70480) | 1,47140 ms (1,40400–1,48415) | -11,62 % | Belastbarer Gewinn über die beobachteten Laufbereiche. |
| Worker-Roundtrip | 16,14165 ms (12,22700–18,24875) | 15,64300 ms (13,65540–19,96890) | -3,09 % | Bereiche überlappen; Effekt unklar. |
| Qt-`frameSwapped`-Intervall | 165,99450 ms (162,49400–170,57250) | 167,07395 ms (163,64545–173,73410) | +0,65 % | Bereiche überlappen; weder Regression noch Verbesserung belegt. |
| GUI-Eingabe-bis-Swap-Median | 88,659 ms (84,541–96,146) | 93,636 ms (89,548–95,498) | +5,61 % | Median höher, aber Bereiche überlappen; Nichtverschlechterung nicht abschließend belegt. |
| Simulationsdurchsatz | 0,978208 | 0,978205 | -0,00 % | Innerhalb der beobachteten Streuung unverändert. |

Run-Bereiche sind hier eine deskriptive Unsicherheitsanzeige, kein formales
Konfidenzintervall. Der Worker-Batch-Gewinn ist klar; die übrigen
GUI-/Echtzeitsignale zeigen keine belastbare Regression, erlauben aber auch
keine vollständige Behauptung, dass jede Messgrenze unverändert blieb. Diese
Unterscheidung bleibt für die Entscheidung über weitere Kandidaten und eine
spätere fachliche Abnahme maßgeblich.

## 4. Umsetzungsschritte

Die Schritte U-V0.12-000016 bis U-V0.12-000023 führen den bisherigen
Speed-Strang dieses Plans fort. U-V0.12-000024 ff. ergänzen die
Echtzeit- und Kapazitätsziele. Die bestehenden U-V0.12-000001 bis
U-V0.12-000015 werden nicht neu vergeben oder umgedeutet; ihr damaliger
Status bleibt im Abschlussnachweis nachvollziehbar.

| Schritt | Anforderungen | Voraussetzung | Arbeit und prüfbares Ergebnis | Status |
|---|---|---|---|---|
| U-V0.12-000016 | A-V0.12-00001, A-V0.12-00007 | Planfreigabe | Vorhandene V0.12-Messungen inventarisieren: Messfrage/Kandidat, Metrik, Rohwert bzw. ausgewiesener Kennwert, Messgrenze, Modell/Pfad, Bedingungen, Stichprobe/Unsicherheit und Rohdatenlink. Quellen unverändert übernehmen. Jede Wiederholungsmessung bereits abgedeckter Fragen unterbleibt; Abweichungen und Datenlücken werden markiert. | Erledigt und nachgetragen; [Messinventar](../Messungen/Speed_V0.12_2026-10-21/speed_messinventar_v0.12.json) enthält 64 Quellen: zehn neue Läufe zur Hydrodynamik-Arbeitsbereichsfrage, fünf bereits abgeschlossene SSAO-off-Läufe zu einer gesonderten GUI-Frage und ein instrumentiertes GUI-Aufrufprofil. Die ursprünglichen Baseline-Reihen wurden nicht wiederholt. |
| U-V0.12-000017 | A-V0.12-00002, A-V0.12-00003, A-V0.12-00006, A-V0.12-00008, A-V0.12-00010, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000016 | Relevante Workloads, Messgrenzen und Pflichtszenarien auf Basis der übernommenen Belege festlegen. Den nativen dynamischen Standardpfad vom GUI-Pfad trennen; Folkeboot nur für notwendige reale Integration und Grundkörper für gezielte analytische Verträge verwenden. Kandidaten anhand belegtem Engpass, Aufrufhäufigkeit, Gesamtkostenbeitrag, Risiko und Unsicherheit priorisieren. Unsicherheit vor neuen Messungen festlegen; keinen prozentualen Mindestgewinn ansetzen. | Erledigt für den Kandidaten „wiederverwendbare native Hydrodynamik-Arbeitsbereiche“. Die Snapshot-Aufbereitung liegt im Setup/Workerstart und nicht im wiederholten Einzelschritt. Die P-ID ist zwischen Kandidatenliste (P-09) und Spezifikation (P-03) uneinheitlich; Bezeichnung bleibt maßgeblich, Kennungen wurden nicht geändert. |
| U-V0.12-000018 | A-V0.12-00001, A-V0.12-00002, A-V0.12-00003, A-V0.12-00007, A-V0.12-00009, A-V0.12-00010, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000016, U-V0.12-000017 | Nur für ausgewählte Kandidaten unbeantwortete Messfragen und fehlende native Profilanteile erheben. Neue Messungen erhalten Quell-/Build-/Umgebungsidentität, gleiche Referenz-/Kandidatenbedingungen, getrennte Messgrenzen, Warm-up, mindestens fünf neue Messungen je erforderlicher Variante und Rohdaten. Passende vorhandene Referenzwerte werden wiederverwendet. Gibt es für eine bislang nicht erhobene Messfrage keinen passenden Referenzwert, wird nur die fehlende Referenzmessung neu erhoben. Bereits gemessene Referenzen oder Kandidatenläufe werden nicht erneut ausgeführt. | Erledigt mit Einschränkung: je fünf Referenz-/Kandidatenläufe, 10 s Warm-up und 45 s Messzeit am Folkeboot. Der Hash der Referenz-Binärdatei wurde vor dem Neubau nicht erfasst; Quellstand, Umgebung und Kandidaten-Binärhash sind dokumentiert. Rohdaten und [Auswertung](../Messungen/Speed_V0.12_2026-10-21/hydro_workspace_assessment_v0.12.json). |
| U-V0.12-000019 | A-V0.12-00003, A-V0.12-00004, A-V0.12-00005, A-V0.12-00008, A-V0.12-00009, A-V0.12-00010, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000017, U-V0.12-000018 | Für den jeweils ausgewählten Kandidaten den konkreten Vertrag, Datenlebensdauer/Invalidierung, Thread-Sicherheit, betroffene Verbraucher, Randfälle und bereits vorhandene Testabdeckung dokumentieren. Vorhandene Tests wiederverwenden, statt gleichwertige Testfälle zu duplizieren; die Auswahl der nach der Änderung erneut auszuführenden Tests begründen und auf den kleinsten ausreichenden Umfang begrenzen. Exakte Optimierungen von Näherungen trennen. Approximationen nur nach separater vorheriger fachlicher Nutzerfreigabe, Fehlerbudget und Referenzplan weiterführen. | Erledigt: Arbeitsbereich lebt lokal pro Worker-Batch, wird nicht geteilt und ändert keine öffentliche Python/C++-Schnittstelle. Wiederverwendet werden vorhandene Worker-, Hydrodynamik-, Statik- und Paritätstests. |
| U-V0.12-000020 | A-V0.12-00003, A-V0.12-00004, A-V0.12-00005, A-V0.12-00006, A-V0.12-00008, A-V0.12-00009, A-V0.12-00010, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000019; zusätzlicher ausdrücklicher Auftrag für Produktivcode erforderlich | Einen freigegebenen Kandidaten isoliert und rückverfolgbar implementieren. Änderungen an bestehenden Funktionen begrenzen; keine neuen Physikfunktionen, keine Vertragslockerung und keine unfreigegebene Approximation. Ist der Messbeitrag nicht plausibel oder überwiegt ein Pflichtszenario-Risiko, wird der Kandidat nicht implementiert. | Erledigt aufgrund des Nutzerauftrags vom 21.10.2026: C++-Hydrodynamik-Arbeitsvektoren und Ergebnisvektor werden innerhalb eines nativen Batches wiederverwendet. |
| U-V0.12-000021 | A-V0.12-00004, A-V0.12-00005, A-V0.12-00006, A-V0.12-00009, A-V0.12-00010, A-V0.12-00011 | U-V0.12-000020 | Für den geänderten Code die vorhandenen, kleinsten fachlich ausreichenden Tests erneut ausführen; keine gleichwertigen Testfälle neu duplizieren und unveränderte, nicht betroffene Bereiche nicht routinemäßig erneut laufen lassen. Bei gemeinsam genutzten Verträgen, unklarer Reichweite oder Revisionsabnahme passend erweitern. Unabhängige Referenzen und bei Vertrags-/Backendänderungen notwendige Integration und Parität einbeziehen. Ergebnisse, Befehle, Skips/Abwahlen und offene Prüflücken ausweisen. | Durchgeführt: Build erfolgreich; 63 Tests bestanden. Ein bekannter Optimist-Paritätsfehler blieb bestehen (Abweichung 1,01024256e-9 bei atol=1e-9), bereits im historischen Ausgangsstand dokumentiert; kein neuer Fehler erkennbar. |
| U-V0.12-000022 | A-V0.12-00001, A-V0.12-00006, A-V0.12-00007, A-V0.12-00009, A-V0.12-00010, A-V0.12-00011 | U-V0.12-000018, U-V0.12-000020, U-V0.12-000021 | Ausschließlich den neuen Kandidatenlauf gegen methodisch passende vorhandene Referenzwerte vergleichen. Vorhandene Baseline-/Referenzmessungen nicht wiederholen. Gewinn, Unklarheit innerhalb der Unsicherheit und jede Regression je Pflichtszenario getrennt ausweisen; kleine belegte Gewinne zählen, unsichere Effekte nicht. Regressionen nicht mit Gewinnen anderer Messgrenzen saldieren. | [Auswertung](../Messungen/Speed_V0.12_2026-10-21/hydro_workspace_assessment_v0.12.json): Worker-Batch-Median 1,66495 auf 1,47140 ms (-11,62 %); die fünf Laufmediane überlappen nicht. GUI-Frameintervall, Rückstand, Durchsatz und Eingabelatenz sind innerhalb der beobachteten Streuung unklar; keine belastbare Regression nachgewiesen, aber auch keine vollständige GUI-Nichtverschlechterung belegt. |
| U-V0.12-000023 | A-V0.12-00001 bis A-V0.12-00012 | U-V0.12-000016 bis U-V0.12-000022, soweit zutreffend | Messinventar, Kandidatenentscheidungen, Änderungen, Tests, tatsächliche Vorher-/Nachher-Werte, Unsicherheiten, Regressionen und Lücken konsolidieren. Relevante CPPI-Einträge nur bei tatsächlichen Schnittstellenänderungen aktualisieren. Alle A-Kennungen mit Umsetzung und Belegen abgleichen; offene/gesperrte Punkte bleiben offen. | Erledigt für den ausgeführten Kandidaten; Rückverfolgbarkeit der damaligen zwölf Speed-Anforderungen aktualisiert. Weitere bedingte Kandidaten sind nicht umgesetzt und bleiben ausweislich der Spezifikation offen. |
| U-V0.12-000024 | A-V0.12-00016, A-V0.12-00017, A-V0.12-00019 | U-V0.12-000016, U-V0.12-000017, U-V0.12-000022 | Vorhandene Durchsatz-, Frameintervall-, Eingabe-bis-Swap- und Workerwerte als Ist-Befund zusammenführen. Realtime-Nachholen und flüssige GUI-Signale als überprüfbare Ziele formulieren, die Bedeutung und Grenzen von `frameSwapped` dokumentieren sowie alle zwölf Kandidaten nach vorhandenem Messstand und offenen Fragen einordnen. Keine bestehende Messreihe wiederholen. | Erledigt in der ergänzten Speed-Spezifikation; Durchsatz bleibt unter 1:1, die vorhandenen Swap-Signale belegen keine flüssige Anzeige, und die vorgeschlagenen Schwellenwerte sind noch zu bestätigen. |
| U-V0.12-000025 | A-V0.12-00016, A-V0.12-00017, A-V0.12-00019 | U-V0.12-000024 | Für alle Kandidaten P-01 bis P-12 eine ausdrückliche Entscheidung dokumentieren: umsetzen, nicht umsetzen oder durch einen belegten Vorläufer blockiert. Den nächsten konkreten Umsetzungskandidaten mit Messbeleg, erwarteter Messgrenze, betroffenen Verträgen, Tests und Abnahmekriterien benennen. Bereits erhobene Messfragen nicht wiederholen. Fehlt eine ausreichende Evidenz, lautet die Entscheidung ausdrücklich „derzeit keine weitere Produktivmaßnahme freigegeben“; die fehlende Evidenz und ein gezielter, noch nicht abgedeckter Profilbedarf sind zu benennen, statt Kandidaten unbestimmt offen zu lassen. | Erledigt: P-01 bis P-12 sind entschieden. Die exakte Marker-Kugelvorlage und P-03 Hydrodynamik-Arbeitsbereiche bleiben als zwei bestehende Maßnahmen aktiv. Die fünf SSAO-off-Läufe rechtfertigen keine Darstellungsänderung. Ein zusätzliches instrumentiertes GUI-Aufrufprofil ist erhoben und inventarisiert; wegen des deutlichen Instrumentierungseinflusses dienen Zeitwerte nicht als Performancebeleg. Es isoliert keinen offenen P-Kandidaten ausreichend. Für die übrigen Kandidaten ist derzeit keine weitere Produktivmaßnahme freigegeben. |
| U-V0.12-000026 | A-V0.12-00018 | U-V0.12-000024 | Als vorläufigen Kapazitätsrichtwert für künftige Planung 25 % geschätzte Wind-Zusatzlast und 20 % verbleibende Reserve ansetzen; daraus folgt aufgerundet 1,6× des heutigen Durchsatzes. Annahme ausdrücklich als Schätzung, nicht als Messung oder validierter Windlastnachweis kennzeichnen. Keine Windphysik oder Windlastsimulation implementieren. | Erledigt als vorläufige Planungsannahme: Zielrichtwert 1,6×; tatsächliche Zusatzlast bleibt mangels Windsimulation ungemessen und ist bei späterer Windplanung neu zu bewerten. |

Ein Kandidatenschritt kann für mehrere Kandidaten nacheinander ausgeführt
werden; pro Änderung sind Messfrage, betroffene Verträge und Freigabe
eindeutig. Nach jedem Kandidaten erfolgt ein Entscheidungstor, bevor der
nächste Kandidat angefasst wird. Das verhindert, dass kumulierte Änderungen
eine Regression oder ihren tatsächlichen Beitrag verdecken.

## 5. Meilensteine und Entscheidungstore

| Meilenstein | Eintritt | Prüfkriterium für Abschluss |
|---|---|---|
| M1 – vorhandene Messwerte übernommen | U-V0.12-000016 abgeschlossen | Erreicht; 64 Quellen sind inventarisiert. Die fünf SSAO-off-Läufe und das instrumentierte GUI-Aufrufprofil wurden als eigenständige Messfragen aufgenommen; bestehende Baselines wurden nicht wiederholt. |
| M2 – Szenarien und Kandidaten festgelegt | M1 abgeschlossen; U-V0.12-000017 abgeschlossen | Erreicht für den ausgewählten nativen Hydrodynamik-Kandidaten. P-ID-Abweichung zwischen Kandidatenliste und Spezifikation ist offengelegt; keine ID eigenmächtig umnummeriert. |
| M3 – Messlücken und Vertrag bewertet | M2 abgeschlossen; U-V0.12-000018 und U-V0.12-000019 abgeschlossen | Erreicht mit offener Einschränkung: Referenz-Binärhash fehlt; Lebensdauer, lokale Nutzung und vorhandene Testabdeckung dokumentiert. |
| M4 – Kandidat verifiziert | M3 abgeschlossen; Nutzerauftrag vom 21.10.2026 liegt vor | Erreicht mit bekanntem Testbefund: gezielte Tests und Build liefen, 63 bestanden; die bekannte Optimist-Paritätsabweichung bleibt offen. Worker-Batch-Gewinn ist belegt; GUI-Gegensignale sind nicht belastbar genug, um vollständige Nichtverschlechterung zu behaupten. |
| M5 – Rückverfolgbarkeit abgeschlossen | M4 abgeschlossen oder begründete Entscheidung, keine Umsetzung vorzunehmen | Erreicht für den ausgeführten Kandidaten: die damaligen zwölf Speed-Anforderungen sind Status und Nachweis zugeordnet. Die später ergänzten Ziele werden ab M6 nachverfolgt. Weitere optionale Kandidaten und offene Nachweislücken bleiben ausdrücklich offen. |
| M6 – Echtzeit-Ist-Befund und offene Kandidaten aufgenommen | U-V0.12-000024 abgeschlossen | Erreicht: vorhandene Durchsatz-, GUI- und Workerwerte unverändert übernommen; Kandidatenstatus und Messgrenzen dokumentiert. Keine Baseline wiederholt. |
| M7 – nächste Maßnahmen verbindlich entschieden | U-V0.12-000025 abgeschlossen | Erreicht: Die exakte Marker-Kugelvorlage und P-03 sind die zwei bereits belegten und umgesetzten Optimierungen. SSAO-off und alle weiteren P-01 bis P-12 sind nicht als nächste Produktivmaßnahme ausgewählt. Das instrumentierte GUI-Profil und seine Grenzen sind dokumentiert; keine Baseline wurde wiederholt. |
| M8 – Kapazitätsannahmen festgelegt | U-V0.12-000026 abgeschlossen | Erreicht als vorläufiger Planungswert: 25 % geschätzte Zusatzlast, 20 % Reserve und 1,6× Durchsatz. Kein Windlastnachweis und keine Windsimulation; Annahme bei tatsächlicher Windplanung zu validieren. |

## 6. Rückverfolgbarkeit Speed

| Aktive Anforderung | Umsetzungsschritte | Nachweis / aktueller Status |
|---|---|---|
| A-V0.12-00001 | U-V0.12-000016, U-V0.12-000018, U-V0.12-000022, U-V0.12-000023, U-V0.12-000025 | Erfüllt mit Einschränkung: 64 Quellen inventarisiert; der Referenz-Binärhash für die Hydrodynamik-Arbeitsbereichsmessung fehlt. |
| A-V0.12-00002 | U-V0.12-000017, U-V0.12-000018 | Erfüllt für Folkeboot; nativer Worker und GUI-Messgrenzen getrennt. Keine Übertragung auf alle Modelle. |
| A-V0.12-00003 | U-V0.12-000017, U-V0.12-000018, U-V0.12-000019, U-V0.12-000020 | Erfüllt mit Einschränkung: wiederholte Hydrodynamik-Allokationen im nativen Batch identifiziert; deren Einzelanteil wurde nicht separat gemessen. Gesamter Worker-Batch sank belastbar. |
| A-V0.12-00004 | U-V0.12-000019, U-V0.12-000020, U-V0.12-000021 | Technisch geprüft; bestehende Verträge erhalten. Ein bekannter Optimist-Paritätsbefund bleibt offen. |
| A-V0.12-00005 | U-V0.12-000019, U-V0.12-000020, U-V0.12-000021, U-V0.12-000023 | Erfüllt: keine Approximation oder Toleranzlockerung eingeführt. |
| A-V0.12-00006 | U-V0.12-000017, U-V0.12-000020, U-V0.12-000021, U-V0.12-000022, U-V0.12-000023 | Erfüllt für Worker-Batch: -11,62 % und getrennte Ausweisung aller unklaren GUI-/Echtzeitsignale; kein Mindestgewinn. |
| A-V0.12-00007 | U-V0.12-000016, U-V0.12-000018, U-V0.12-000022 | Erfüllt: vorliegende Messreihen nicht wiederholt; nur die bislang fehlende Referenz- und Kandidatenfrage neu erhoben. |
| A-V0.12-00008 | U-V0.12-000017, U-V0.12-000019, U-V0.12-000020 | Erfüllt: bestehende Hydrodynamik im wiederholt ausgeführten nativen Workerpfad optimiert. |
| A-V0.12-00009 | U-V0.12-000018, U-V0.12-000019, U-V0.12-000020, U-V0.12-000021 | Erfüllt mit Einschränkung: nativer Batch gemessen; Arbeitsbereiche sind batchlokal und nicht geteilt. Setupzeit nicht Teil der Änderung. |
| A-V0.12-00010 | U-V0.12-000017, U-V0.12-000018, U-V0.12-000021, U-V0.12-000022 | Gegengates erhoben: Frameintervall, Rückstand und Durchsatz unklar innerhalb der Streuung; Eingabelatenzmedian +5,61 %, aber überlappende Laufbereiche. Keine belastbare Regression, vollständige Nichtverschlechterung nicht belegt. |
| A-V0.12-00011 | U-V0.12-000017, U-V0.12-000019, U-V0.12-000021, U-V0.12-000022 | GUI-Pose/Render und Frameintervall ausgewiesen; Unterschiede liegen innerhalb der beobachteten Streuung. |
| A-V0.12-00012 | U-V0.12-000017, U-V0.12-000019, U-V0.12-000021, U-V0.12-000022 | Nicht zutreffend für diese Änderung: Python-Referenzpfad unverändert; native Verbesserung getrennt ausgewiesen. |
| A-V0.12-00016 | U-V0.12-000024, U-V0.12-000025 | Ist-Befund dokumentiert: vorhandener Durchsatz 0,975985 bzw. 0,978205–0,978208 Simulationssekunden/Wandsekunde. 1:1-Ziel noch nicht erreicht; bleibt Leistungsziel, keine weitere Maßnahme ohne Kandidatenbeleg. |
| A-V0.12-00017 | U-V0.12-000024, U-V0.12-000025 | Vorhandenes `frameSwapped`-Intervall 165,99450–167,07395 ms; vorgeschlagene Zielwerte 30 Signale/s im Median und p95 ≤50 ms sind nicht erreicht. Instrumentiertes Profil ist kein Performancevergleich. |
| A-V0.12-00018 | U-V0.12-000026 | Vorläufiger Planungsrichtwert 1,6× aus angenommener Zusatzlast von 25 % und 20 % Reserve; keine Windlast gemessen oder simuliert; bei späterer Windplanung zu validieren. |
| A-V0.12-00019 | U-V0.12-000024, U-V0.12-000025 | Alle P-01 bis P-12 anhand der vorhandenen Evidenz entschieden: Marker-Kugelvorlage und P-03 bleiben umgesetzt; SSAO-off und die übrigen Kandidaten sind nicht als nächste Produktivmaßnahme ausgewählt. Das instrumentierte GUI-Aufrufprofil ergab keinen hinreichend belegten neuen Kandidaten; vorhandene Baselines wurden nicht wiederholt. |

## 7. Testumbau V0.12 – frühere Arbeiten und offene Abnahmebefunde

Der Testumbau und seine noch offenen fachlichen Abnahmebefunde sind im
[historischen Abschlussnachweis](./Abschlussnachweis_Teststruktur_und_Speed_V0.12.md)
dokumentiert. Die ursprünglichen U-V0.12-000001 bis U-V0.12-000009 bleiben
dort unverändert referenzierbar; ihre Kennungen werden nicht wiederverwendet.
Die dort ausgewiesenen zwei Ausgangsfehler und das nicht belegte
Iterationszeit-Ziel bleiben offene Abnahmebefunde und werden nicht als
gelöst dargestellt. Dieser Plan ergänzt für den Speed-Strang ausschließlich
U-V0.12-000016 ff. Die Zuordnung der Testumbau-Anforderungen zu ihren
historischen Umsetzungsschritten bleibt Teil der Rückverfolgbarkeit:

| Testumbau-Anforderung | Historische Schritte | Status laut Abschlussnachweis |
|---|---|---|
| A-V0.12-00001 | U-V0.12-000001, U-V0.12-000009 | Technisch geprüft |
| A-V0.12-00002 | U-V0.12-000001, U-V0.12-000007 | Technisch geprüft; GPU-Baseline eingeschränkt |
| A-V0.12-00003 | U-V0.12-000002, U-V0.12-000005 | Technisch geprüft |
| A-V0.12-00004 | U-V0.12-000002, U-V0.12-000005 | Technisch geprüft |
| A-V0.12-00005 | U-V0.12-000002, U-V0.12-000003, U-V0.12-000006 | Technisch geprüft |
| A-V0.12-00006 | U-V0.12-000003, U-V0.12-000006 | Technisch geprüft |
| A-V0.12-00007 | U-V0.12-000005 | Technisch geprüft |
| A-V0.12-00008 | U-V0.12-000004 | Technisch geprüft |
| A-V0.12-00009 | U-V0.12-000002, U-V0.12-000005 | Technisch geprüft |
| A-V0.12-00010 | U-V0.12-000002, U-V0.12-000004, U-V0.12-000005, U-V0.12-000006 | Verträge unverändert; Optimist-Parität offen |
| A-V0.12-00011 | U-V0.12-000007 | Messverfahren geprüft; keine Produktivänderung |
| A-V0.12-00012 | U-V0.12-000007 | Iterationsgewinn nicht belastbar belegt |
| A-V0.12-00013 | U-V0.12-000001, U-V0.12-000003, U-V0.12-000004, U-V0.12-000006, U-V0.12-000009 | Technisch geprüft |
| A-V0.12-00014 | U-V0.12-000001, U-V0.12-000005, U-V0.12-000009 | Zuordnung geprüft; Gesamtfreigabe offen |
| A-V0.12-00015 | U-V0.12-000008 | Technisch geprüft |

## 8. Statusführung

Für den ausgewählten Kandidaten sind Messungen, Codeänderung, gezielte Tests
und Vergleich getrennt belegt. Die bekannten Einschränkungen sind keine
pauschale Revisionsabnahme: insbesondere fehlt der Referenz-Binärhash, der
Optimist-Paritätsbefund bleibt offen und mehrere GUI-Gegengates sind unklar.
Nicht ausgeführte Kandidaten bleiben bewusst offen oder werden erst nach
einem passenden Profilbefund ausgewählt; weder Kandidatenliste noch
Teilfortschritt begründen eine pauschale Umsetzung oder Abnahme.
