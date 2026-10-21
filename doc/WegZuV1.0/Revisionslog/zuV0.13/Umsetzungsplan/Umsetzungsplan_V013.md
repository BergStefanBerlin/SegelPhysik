# Umsetzungsplan V0.13: Performance-Kandidaten

**Stand:** 21.10.2026  
**Status:** Kandidaten und verfügbare Baselines wurden geprüft; sichere Optimierungen sind umgesetzt, ungeeignete oder nicht belegte Varianten bleiben mit Begründung deaktiviert.

**Maßgebliche Spezifikation:** [Spezifikation V0.13](../Spezifikationen/Spezifikation_V013.md)

## 1. Zweck und verbindliche Grenzen

Dieser Plan ist die einzige maßgebliche Umsetzungsliste für die Kandidaten
P-01 bis P-12 in V0.13. Er setzt den in der Spezifikation festgehaltenen
Nutzerauftrag um, ohne die historischen V0.12-Dokumente nachträglich zu
ändern.

Der Nutzer untersagt doppelte Messungen, nicht gezielte Messungen fehlender
Baselines oder notwendige Nachher-Vergleiche. Vor jeder Codeänderung wird
deshalb der vorhandene Beleg gegen die tatsächlich betroffene Messgrenze
geprüft. Ausreichende Baselines werden unverändert übernommen; nur fehlende
oder nicht isolierte Pfade erhalten eine gezielte Baseline vor der Umsetzung.
Nachhermessungen erfolgen unter vergleichbaren Bedingungen. Korrektheitstests
bleiben unabhängig davon verpflichtend.

Die Arbeitsbereiche können parallel bearbeitet werden, soweit sie
unabhängige Dateien und Verträge betreffen. Integration, gemeinsame
Schnittstellen und Regressionstests werden kontrolliert zusammengeführt.
Bestehende Änderungen im Arbeitsbaum werden nicht verworfen oder
überschrieben.

Es erfolgen keine Commit-, Push-, Tag- oder Release-Aktionen.

## 2. Arbeitsregeln

- Vor einer Änderung den konkreten Quellpfad, direkte Verbraucher,
  bestehende Tests und bereits veränderte Dateien untersuchen.
- Vorhandene Baseline-Messungen und Rohdaten inventarisieren; pro
  Kandidatenpfad festhalten, ob sie als ausreichend übernommen oder gezielt
  einmal nachgemessen werden müssen.
- Keine Baseline erneut erheben, wenn vorhandene Daten denselben Pfad,
  dieselben Eingaben und die notwendige Messgrenze ausreichend abdecken.
  Eine allgemeine Pose-/Render-/Workerzeit ist keine isolierte Baseline für
  Snapshot, Wasserlinienschnitt oder Splat.
- Fehlende Baselines vor dem ersten Codeeingriff des jeweiligen Pfads messen.
  Danach denselben Pfad nach der Änderung messen; keine parallele
  Benchmark-/Testlast während Vergleichsreihen.
- Neu erhobene Varianten: separater Warm-up, danach mindestens fünf Läufe,
  Rohdaten, Median und Streuung. Messgrenze, Quell-/Buildstand, Modell,
  Eingaben und Umgebung dokumentieren.
- Bereits vorhandene Änderungen des Arbeitsbaums nicht überschreiben.
  Besonders die aktuelle native Hydrodynamik-Arbeitsbereichsänderung ist
  Bestandteil des zu bewahrenden Arbeitsstands und wird nicht als sauberer
  V0.13-Baselinezustand ausgegeben.
- Tests gegen unabhängige analytische oder bestehende Referenzen verwenden.
  Bestehende Toleranzen bleiben erhalten; keine Performance-Grenzen in
  gewöhnliche Regressionstests aufnehmen.
- Gemeinsame Python/C++-Verträge mit passenden Paritätstests prüfen.
  Eine Schnittstellenänderung erfordert CPPI-ID und Registerpflege.
- P-10 darf nur als aktiver Pfad integriert werden, wenn exakte
  Korrektheit vollständig nachgewiesen ist. Andernfalls bleibt der bestehende
  exakte Algorithmus produktiv und der Prototyp wird nicht aktiv geschaltet.
- Keine Messzeit aus Testlaufdauer ableiten. Keine Baselines wiederholen,
  die für den konkreten Pfad bereits ausreichend sind.

## 3. Baseline-Abgleich vor Umsetzung

„Gezielt nachholen“ bedeutet ausschließlich die in der Tabelle benannte
Kandidatenmessung; vollständige GUI-Baselines werden nicht wiederholt.

| Kandidat | Vorhandener Beleg | Baseline-Eignung für den Kandidaten | Vorabentscheidung |
|---|---|---|---|
| P-01 Snapshot | Worker-Batch und Roundtrip im GUI-Gesamtlauf; gezielte Native-Kontexttests im aktuellen Arbeitsbaum | Historischer Snapshotanteil fehlt. Eine isolierte Gegenmessung Wiederverwendung vs. Neuaufbau wurde im aktuellen Arbeitsbaum erhoben. | A/B-Beleg wiederverwenden; keinen identischen Lauf wiederholen. Historische Vorher-/Nachher-Aussage bleibt mangels sauberem Vorherstand offen. |
| P-02 Wasserlinienschnitt | Pose- und Renderaufruf im GUI-Gesamtlauf; gezielte Cachetreffer-/Neuberechnung-A/B-Messung auf Folkeboot-Meshgruppe | Historischer Schnittanteil fehlt. Die aktuelle Messung isoliert Cachelookup gegen Schnitt-/Geometrieerzeugung, nicht den gesamten Frame. | A/B-Beleg wiederverwenden; keinen identischen Lauf wiederholen. Historischer Vorher-/Nachher-Vergleich bleibt mangels sauberem Vorherstand offen. |
| P-03 Batchgröße | V0.12 Worker-Batch/Roundtrip; gezielter nativer Vergleich Batchgrößen 1, 4, 16, 64 | Vergleich pro nativen Schritt; Task-Queue und GUI-Latenz nicht enthalten. Batch 16/64 Spannweiten überlappen. | Bestehende 16 beibehalten; 64 nicht als Verbesserung übernehmen. [Messbeleg](../Messungen/messung_p03_native_batchgroessen_v0.13.json) |
| P-04 Wasser-Splat | Gesamter Renderaufruf; aktueller C++-gegen-Python-Splat-A/B-Beleg | Isolierter Kernelvergleich vorhanden, aber kein Frameanteil oder historischer nativer Vorherstand | Native Implementierung erhalten; keinen Gewinn gegenüber früherem nativen Pfad behaupten |
| P-05 Gelenk-Updates | Kein historischer Ereigniskostenvergleich; Timer-Coalescing bereits im Arbeitsbaum | Fehlender Vorherstand kann aus den vorhandenen Quellen nicht rekonstruiert werden | Bestehenden Endwert-/Zusammenfassungsvertrag testen; Performancegewinn als nicht belegt ausweisen |
| P-06 Python-Validierung | Gezielte 6-DOF-Referenzmessung vor Änderung erhoben | Ausreichend für wiederholte Positivdefinitheitsprüfung, nicht für Produktions-Worker | Begrenzte Werte-Cache-Optimierung umgesetzt und nachgemessen; Beleg [P-06](../Messungen/messung_p06_python_schritt_validation_v0.13.json) |
| P-07 Python-Kraft-/Wrench-Kette | Gezielte Aggregationsmessung mit drei Folkebootbeiträgen | Ausreichend für diese Objektkette; nicht für den vollständigen Kraftschritt | Keine Kopier-/Validierungsregeln ohne sicheren Vertrag umgehen; unverändert lassen und Beleg [P-07](../Messungen/messung_p07_python_wrench_kette_v0.13.json) führen |
| P-08 Python-Hydrodynamik-Temporärdaten | Vorher-/Nachhermessung der Python-Hydrodynamikauswertung | Ausreichend für die vorhandene Normalenmaskenänderung; Streuung überlappt | Maske wiederverwenden; keinen eindeutigen Laufzeitgewinn behaupten |
| P-09 native Arbeitsbereiche | Fünf Hydrodynamik-Referenz-/Kandidatenläufe plus gezielte exakte Hydrostatik-Baseline | Hydrodynamik-Worker-Batch und isolierte Hydrostatik-Auswertung gemessen; einzelne Allokationen nicht attribuiert | Schnitt-Arbeitsbereich task-/batchlokal wiederverwenden; Korrektheit prüfen. Gesamt-Batch-Recheck dokumentieren, aber wegen unvollständig dokumentierter alter Eingabepose keinen Vorher-/Nachher-Gewinn behaupten. |
| P-10 hierarchischer exakter Schnitt | Gezielt erhobene native Hydrostatik-Baseline: Folkeboot, Median 26,796 µs/Aufruf | Baseline vorhanden; kein Hierarchie-Prototyp und kein Gegenbeleg zur Exaktheit | Kein alternativer Algorithmus aktiviert; exakten Bestandsalgorithmus erhalten, da Korrektheit/Verbesserung nicht nachgewiesen |
| P-11 Compiler/PGO | Keine projektspezifische Buildvergleichsmessung | Kein sicherer, toolchainübergreifender Schalter mit belegtem Projektgewinn | Compiler-/Buildoptionen unverändert lassen; keine Genauigkeitsflags einführen |
| P-12 VTK-PlaneCutter | P-02 isoliert Cachetreffer gegen aktuellen GUI-Schnitt | Keine Vergleichsreihe mit VTK-Ausgabe, Deckel-/Konturverträgen oder Kaltstart | Bestehenden GUI-Pfad erhalten; PlaneCutter nicht als Drop-in-Ersatz aktivieren |

Messfragen, die denselben unveränderten Codepfad, Datensatz und Lauf
betreffen, dürfen gemeinsam erfasst werden. Eine Messung wird nicht
dupliziert, nur weil sie mehrere Anforderungen belegt. Abweichende Workloads
oder Messgrenzen erhalten getrennte Werte.

## 4. Umsetzungsreihenfolge und Arbeitspakete

Die folgenden unabhängigen Arbeitspfade können parallel begonnen werden.
Abhängigkeiten nennen Integrations- und Abnahmereihenfolge, nicht eine
Erlaubnis zum Überspringen von Tests.

| Umsetzungsschritt | Anforderungen | Abhängigkeiten | Arbeit und Prüfkriterien | Status |
|---|---|---|---|---|
| U-V0.13-000001 | A-V0.13-00013 | Keine | Baseline-Inventar prüfen und gezielt fehlende Messungen aus Abschnitt 3 vor Codeänderungen erheben. Quellen, Laufbedingungen, Rohdaten, Median/Streuung und Messgrenze dokumentieren; ausreichende frühere Reihen nicht wiederholen. | Abgeschlossen: Baseline-Matrix und gezielte fehlende P-01/02/03/04/06/07/08/09/10-Messungen dokumentiert; keine ausreichende Reihe doppelt erhoben. |
| U-V0.13-000002 | A-V0.13-00001, A-V0.13-00002, A-V0.13-00005 | U-V0.13-000001 | Snapshot-Lebensdauer/Invalidierung, GUI-Wasserlinienschnitt-Cache und Gelenk-Ereignisverarbeitung getrennt prüfen. Vorhandene Implementierungen im Arbeitsbaum nicht überschreiben; fehlenden historischen Vorherstand explizit ausweisen. | Teilweise abgenommen: P-01/P-02-Tests und A/B-Belege vorhanden; P-05-Endwert-/Coalescingtest bestanden. Für P-01/P-02 fehlt ein historischer Vorherstand, für P-05 eine Vorhermessung. |
| U-V0.13-000003 | A-V0.13-00003, A-V0.13-00009 | U-V0.13-000001 | Nativen Batchvertrag und Arbeitsbereichslebensdauer prüfen. Hydrodynamik-Wiederverwendung erhalten; Hydrostatik-Scratch task-/batchlokal wiederverwenden. Exakte Werte, Abbruch und Parität testen. | Umgesetzt: Batch 16 beibehalten; Hydrostatik-Schnittarbeitsbereich wird batchlokal wiederverwendet. Native Geometrie-/Batchtests bestehen, Optimist-Batch-Paritätsabweichung bleibt unverändert bekannt. Isolierter Hydrostatik-Gewinn nicht belegt. |
| U-V0.13-000004 | A-V0.13-00006, A-V0.13-00007, A-V0.13-00008 | U-V0.13-000001 | Python-Referenzpfad auf wiederholte Validierung, Ergebnisobjekte/Kopien und temporäre Hydrodynamikdaten prüfen. Fehler-, Werte-, Mutabilitäts- und Paritätsverträge erhalten. | Teilweise umgesetzt: P-06-Cache mit nicht überlappender Messstreuung und geändertem-Eingabe-Test; P-08-Maske vorhanden, Gewinn nicht belastbar; P-07 gemessen, keine sichere Kopiereliminierung begründet. |
| U-V0.13-000005 | A-V0.13-00004, A-V0.13-00010, A-V0.13-00011, A-V0.13-00012 | U-V0.13-000001 | Wasser-Splat, VTK-GUI-Schnitt, exakten Hierarchie-Prototyp und sichere Compiler-/Buildoptionen getrennt bewerten; nichts aktivieren, dessen Referenzverträge nicht nachgewiesen sind. | Abgeschlossen als sichere Nichtänderungsentscheidung: vorhandenen nativen Splatpfad erhalten; P-10/11/12 nicht aktivieren, da exakte/GUI-/Build-Vergleichsnachweise fehlen. |
| U-V0.13-000006 | A-V0.13-00014, A-V0.13-00015 | U-V0.13-000002 bis U-V0.13-000005 | Nachher-Messungen derselben Messgrenzen und Szenarien erheben; Unsicherheit/Regressionen berichten und Ergebnisliste P-01 bis P-12 vervollständigen. | Abgeschlossen für messbare Änderungen; P-01/02 sind aktuelle A/B-Vergleiche statt historischer Vorher-/Nachher-Belege; P-05 ohne historischen Vorherstand; P-08 unklar innerhalb der Streuung; P-09 post-Änderungs-Gesamtbatch gemessen, aber wegen fehlender exakter alter Eingabepose nicht vergleichbar. P-10 ohne Algorithmusänderung. |
| U-V0.13-000007 | A-V0.13-00013 bis A-V0.13-00015 | U-V0.13-000001 bis U-V0.13-000006 | Messinventar, Codeänderungen, Tests, Vorher-/Nachher-Werte und Traceability abschließend gegen Spezifikation prüfen. | Dokumenten-/Messprüfung abgeschlossen: IDs und Links stimmen; M3-Testfehler sowie fehlende historische/isolierte Belege sind sichtbar ausgewiesen. |
| U-V0.13-000008 | A-V0.13-00016 bis A-V0.13-00018 | Keine Abhängigkeit von offenen P-07/10/11/12-Arbeiten; vorhandene GUI-/Workerverträge erhalten | Zahlenanzeigen mit präzisen 100-ms-Timern bündeln, finale und ungültige Zustände sofort behandeln; identische Text-/SVG-Updates unterlassen; normalen Logpfad prüfen. | Implementiert; gezielte GUI-/Worker-Regression und Nachweise siehe Abschnitt 8. Keine Zeitmarker oder Änderung der Simulationsgeschwindigkeit. |
| U-V0.13-000009 | A-V0.13-00019 | Bestehende gemeinsame Zahlenformatierung und Anzeigeverträge prüfen | Gemeinsamen Formatter für Kräfte/Momente und Längen ändern; Rechtsbündigkeit erhalten, Rundung nur für Textausgabe testen. | Implementiert und softwareseitig geprüft: 382 Tests bestanden; siehe Abschnitt 9. |

## 4. Meilensteine

| Meilenstein | Eintritt | Prüfkriterium für Abschluss | Status |
|---|---|---|---|
| M1 – Baseline-Abgleich | Nutzerauftrag und vorhandene V0.12-Belege geprüft | Baseline-Matrix pro Kandidat bestätigt; keine ausreichende Baseline wiederholt; alle neu erforderlichen Messungen vor Änderung erhoben. | Erreicht; nicht messbare historische Vorherstände sind als Lücke gekennzeichnet. |
| M2 – unabhängige Arbeitspfade umgesetzt | U-V0.13-000001 abgeschlossen | Kandidaten bewertet, sichere Optimierungen integriert und ungeeignete Varianten begründet nicht aktiviert. | Teilweise erreicht; siehe P-01 bis P-12 und U-000002 bis U-000005. |
| M3 – Korrektheit integriert | M2 abgeschlossen | Gezielte Tests für jeden geänderten Vertrag bestanden; erforderliche native/Python-Parität vorhanden; Fehlversuche und Prüflücken dokumentiert. | Nach dem nativen Arbeitsbereichsumbau: Gesamtprüfung **1757 bestanden, 3 fehlgeschlagen, 1 übersprungen**. Fehler: zwei bestehende V0.10-Migrationsprüfungen und Optimist-Batch-Parität (1,01024e-9 bei bestehender 1e-9-Toleranz); keine Toleranz gelockert. Fokussierte Vertragsprüfung: **67 bestanden**; native Batch-Paritätsfehler bleibt separat erfasst. |
| M4 – Vorher-/Nachher-Vergleich | M1 und M3 abgeschlossen | Vergleichbare Messgrenzen; Rohdaten, Median und Streuung; Gewinne nur bei nicht überlappenden Spannweiten behaupten. | Teilweise erreicht; P-06 klarer begrenzter Gewinn, P-08 unklar; historische Vorherstände P-01/02/P-05 fehlen. |
| M5 – Ergebnisliste und Rückverfolgbarkeit | M4 abgeschlossen | P-01 bis P-12 einzeln berichtet; Messgrenzen korrekt begrenzt; alle aktiven A-IDs verknüpft. | Ergebnisliste und Traceability für P-01 bis P-12 vollständig; uneingeschränkte Abnahme wegen der M3-Fehler und der ausdrücklich dokumentierten Messlücken nicht erteilt. |
| M6 – Ergänzungsauftrag Zahlenanzeigen | Nutzerfreigabe für A-V0.13-00016 bis A-V0.13-00018; bestehende GUI-/Workerverträge gelesen | Gebündelte Zahlenanzeigen, unmittelbare Fehler-/Endwerte, unveränderte Analog-/3D-Ausgabe, No-ops und Logprüfung nachgewiesen | Softwareseitige Teilabnahme: 343 gezielte Tests bestanden; siehe Abschnitt 8. Keine Gesamtfreigabe der ursprünglichen Kandidatenarbeit. |

## 5. Teststrategie

Performance- und Korrektheitsnachweise werden getrennt geführt. Für
Performancevergleiche gelten die Baselineentscheidungen aus Abschnitt 3.
Vor Testauswahl werden bestehende Tests auf gleiche
Abdeckung geprüft. Änderungen an gemeinsam genutzten Modell-/Workerzuständen,
GUI-Geometrie, nativen Verträgen oder zentralen Fixtures erfordern eine
risikogerecht erweiterte Integration.

Vorgesehene Abdeckungsbereiche:

- Snapshot: identischer Zustand, Pose-/Gelenk-/Meshänderung, paralleler
  Workerzugriff und unabhängige frische Snapshot-Referenz.
- GUI-Geometrie und Gelenke: unveränderte Pose, geänderte Pose/Geometrie,
  mehrere Sliderereignisse und finaler Gelenkwert.
- Batch und Hydrostatik: gleiche Schrittzahl und Reihenfolge, Abbruch,
  leere/degenerierte/analytische Körper sowie Python/C++-Parität, wo betroffen.
- Splat und VTK-Schnitt: Skip-Verhalten, Rand- und Leerfälle, geschlossene
  Konturen/Deckel und unveränderte Ausgabe gegenüber dem vorhandenen
  Referenzverfahren.
- Python-Referenz: gültige und ungültige Eingaben, Ergebniswerte,
  Mutabilität/Lebensdauer und unveränderte öffentliche Fehlerverträge.
- Hierarchischer Schnitt und Compiler: Quader/Kugel bzw. gezielte Meshfälle
  gegen bestehende exakte Resultate und vorhandene numerische Verträge.

Der genaue pytest-Aufruf wird je Änderung aus dem bestehenden Testbestand
gewählt und im Nachweis genannt. Testlaufzeiten werden nicht als
Performanceergebnisse ausgewertet.

## 6. Vorhandene Performance-Ergebnisse

Eine gezielte A/B-Gegenmessung für P-01 wurde durchgeführt. Sie vergleicht
die aktuelle Kontextwiederverwendung mit dem expliziten Neuaufbaupfad und ist
kein historischer Vorher-/Nachher-Vergleich.

| Kandidat/Stand | Vorhandener Vergleich | Ergebnis und Aussage |
|---|---|---|
| P-03 Batchgröße, V0.13 | Native Folkeboot-Batches 1/4/16/64; je fünf Läufe mit zehn Batchaufrufen | Median **20,640 / 17,490 / 16,758 / 16,559 µs pro Schritt**. Batch 64 liegt nur minimal vor 16 bei überlappenden Spannweiten. Konfiguration 16 bleibt unverändert; die Messung sagt nichts über Queue-/GUI-Latenz. Details: [P-03-Rohdaten und Bedingungen](../Messungen/messung_p03_native_batchgroessen_v0.13.json). |
| P-01 Snapshot-Kontext, V0.13 A/B | Folkeboot, nativer Pfad; fünf Läufe mit je 20 Aufrufen pro Variante | Median **98,475 µs** wiederverwendet gegenüber **256,355 µs** Neuaufbau (**-61,59 %**, 2,60x); Spannweiten überlappen nicht. Vorteil **157,88 µs pro Snapshot**. Nur Kontextmessgrenze, kein vollständiger Worker-/GUI-Gewinn und kein historischer Vorher-/Nachher-Beleg. Details: [P-01-Rohdaten und Bedingungen](../Messungen/messung_p01_kontextwiederverwendung_v0.13.json). |
| P-02 Wasserlinienschnitt-Cache, V0.13 A/B | Folkeboot-Meshgruppe mit 189 Punkten/374 Dreiecken; fünf Läufe mit je 20 Aufrufen pro Variante | Median **4,240 µs** Cachetreffer gegenüber **271,125 µs** Neuberechnung (**-98,44 %**, 63,94x); Spannweiten überlappen nicht. Vorteil **266,885 µs pro Treffer**. Kein Rendering/Frame und kein historischer Vorher-/Nachher-Beleg. Details: [P-02-Rohdaten und Bedingungen](../Messungen/messung_p02_wasserliniencache_v0.13.json). |
| P-04 Wasser-Splat, aktueller Backendvergleich | 700 synthetische Partikel; C++ und Python, fünf Läufe pro Variante | C++ **2,021 ms**, Python **19,411 ms** Median (9,61x). Isolierter Kernelvergleich; kein Renderframeanteil und kein Vergleich mit einem früheren nativen Kernel. Details: [P-04-Messbeleg](../Messungen/messung_p04_wassersplat_cpp_python_v0.13.json). |
| P-05 Gelenk-Coalescing | Vorhandene GUI-Verhaltensprüfung mit vier Sliderereignissen in einem Zeitfenster | Eine Geometrie-/Darstellungsaktualisierung und ein Render; finaler Winkel bleibt erhalten. Keine belastbare Laufzeitmessung und kein historischer Vorherstand. |
| P-06 Trägheitstensorvalidierung | Python-6-DOF-Schritt, synthetischer Kraftstub; je fünf Läufe mit 5 Warm-ups | Median **150,078 → 126,887 µs/Schritt** (**-15,45 %**, 23,191 µs); Spannweiten überlappen nicht. Eingeschränkter Referenz-Workload, nicht der Produktions-Worker. Details: [P-06-Rohdaten und Bedingungen](../Messungen/messung_p06_python_schritt_validation_v0.13.json). |
| P-07 Python-Wrench-Kette | Folkeboot, drei reale Hydrodynamikbeiträge; fünf Läufe mit 1000 Aggregationen | Median **95,745 µs/Aggregation**, Spannweite **95,647–98,622 µs**. Kein alternativer Kopierpfad zum Vergleich; keine unsichere Validierungsumgehung vorgenommen. Details: [P-07-Messbeleg](../Messungen/messung_p07_python_wrench_kette_v0.13.json). |
| P-08 Normalenmaske, Python-Referenz | Folkeboot, gleiche Pose/Geschwindigkeit; fünf Läufe mit je 100 Aufrufen vor und nach Änderung | Median **387,833 → 375,610 µs** (**-3,15 %**), Spannweiten überlappen. Kein eindeutiger Laufzeitgewinn über der Streuung belegt. Details: [P-08-Rohdaten und Bedingungen](../Messungen/messung_p08_python_normalenmaske_v0.13.json). |
| P-09 native Arbeitsbereiche | Vorhandener V0.12-Worker-Batch 1,66495 → 1,47140 ms plus V0.13-Hydrostatik-Baseline und post-change Batch-Recheck | Der V0.12-Gewinn von -11,62 % gilt nur für den Worker-Batch. Exakte Hydrostatik im Folkeboot vor der Änderung: Median **26,796 µs/Aufruf**, Spannweite **26,184–27,097 µs**. Nach dem Schnitt-Scratch-Umbau Gesamt-Batchmediane 22,250/17,220/15,516/15,377 µs für Batches 1/4/16/64; kein direkter Vorher-/Nachhervergleich, weil die alte Eingabepose nicht dokumentiert ist. Keine isolierte Gewinnbehauptung. [P-09/P-10-Messbeleg](../Messungen/messung_p09_p10_native_hydrostatik_v0.13.json). |
| P-10 Hierarchischer exakter Schnitt | Native exakte Hydrostatik-Auswertung im vorbereiteten Folkeboot-Kontext, fünf Posen, fünf Läufe | Median **26,796 µs/Aufruf**, Spannweite **26,184–27,097 µs**; kein Hierarchie-Prototyp verglichen. Der Bestandsalgorithmus bleibt aktiv; kein alternativer Genauigkeits-/Laufzeitgewinn behauptet. [P-09/P-10-Messbeleg](../Messungen/messung_p09_p10_native_hydrostatik_v0.13.json). |
| P-11 Compiler/PGO | Kein projektspezifischer Release-Build-Vergleich | Keine Buildoption geändert; kein Gewinn behauptet. |
| P-12 VTK-PlaneCutter | Kein PlaneCutter-gegen-GUI-Referenzvergleich | Nicht integriert; Eingabe-, Kontur-, Deckel-, Kaltstart- und Leerfallverträge sind nicht belegt. |
| Marker-Kugelvorlage, bereits vorhanden | Qt-Swap-Intervall 168,298 → 151,201 ms, fünf Läufe | Vorhandener Gewinn von rund 10,16 %; bleibt außerhalb der neuen P-01–P-12-Umsetzung. |
| P-01 bis P-12 | Kandidatenstatus, Messgrenzen, Änderungen und verbleibende Beleglücken | P-01/02 A/B-Belege sind kein historischer Vorher-/Nachher-Nachweis; P-03/04/05/07/09/10/11/12 ohne beanspruchten historischen Optimierungsgewinn. Entscheidungen stehen einzeln in Abschnitt 3 und der Kandidatenliste. |

Quellen: [Hydro-Arbeitsbereich-Messung](../../zuV0.12/Messungen/Speed_V0.12_2026-10-21/hydro_workspace_assessment_v0.12.json),
[GUI-Kandidaten-Auswertung](../../zuV0.12/Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json)
und [V0.12-Umsetzungsplan](../../zuV0.12/Umsetzungsanleitungen/Umsetzungsplan_V0.12.md).

## 7. Rückverfolgbarkeit

| Aktive Anforderung | Umsetzungsschritt(e) | Nachweis / Status |
|---|---|---|
| A-V0.13-00001 | U-V0.13-000002 | Snapshot-Invalidierung und dynamische Zustandsübernahme gezielt getestet; A/B-Beleg vorhanden, historischer Vorherstand fehlt. |
| A-V0.13-00002 | U-V0.13-000002 | Cache-Treffer/Invalidierung und A/B-Messung vorhanden; kein vollständiger Frame- oder historischer Vergleich. |
| A-V0.13-00003 | U-V0.13-000003 | Batchgrößen 1/4/16/64 verglichen; 16 bleibt wegen fehlendem belastbarem Vorteil bei 64. Queue-/GUI-Latenz nicht gemessen. |
| A-V0.13-00004 | U-V0.13-000005 | Vorhandener nativer Splatpfad erhalten; C++/Python-Kernelvergleich vorhanden, Identität zum historischen nativen Pfad und Renderframeanteil nicht belegt. |
| A-V0.13-00005 | U-V0.13-000002 | Ereignis-Coalescing-Endwerttest bestanden; keine historische Vorhermessung, daher kein Gewinn behauptet. |
| A-V0.13-00006 | U-V0.13-000004 | Begrenzter Cache positiver Trägheitstensorvalidierung; geänderte Matrix wird erneut validiert; P-06-Messung zeigt nicht überlappende Spannweiten im synthetischen Python-Workload. |
| A-V0.13-00007 | U-V0.13-000004 | Aggregationsbaseline dokumentiert; kein sicherer Alternativpfad für Kopiereliminierung belegt, daher keine Semantikänderung. |
| A-V0.13-00008 | U-V0.13-000004 | Unveränderliche Normalenmaske wiederverwendet; gezielter Maskentest und frühere Hydrodynamik-/Paritätstests; Messspannweiten überlappen. |
| A-V0.13-00009 | U-V0.13-000003, U-V0.13-000005 | V0.12-Hydrodynamikbeleg bleibt auf Worker-Batch begrenzt; native Hydrostatik-Baseline und Batch-Recheck dokumentiert. Task-/batchlokale Schnitt-Scratch-Vektoren wiederverwendet; Tests bestehen, isolierter Hydrostatikgewinn nicht nachgewiesen. |
| A-V0.13-00010 | U-V0.13-000005 | Native Hydrostatik-Baseline dokumentiert; kein hierarchischer Algorithmus aktiviert, da unabhängiger Gleichheitsnachweis und Prototypvergleich fehlen. |
| A-V0.13-00011 | U-V0.13-000005 | Keine Compiler-/PGO-Option mangels projektspezifischer Buildmessung geändert; keine Genauigkeitslockerung. |
| A-V0.13-00012 | U-V0.13-000005 | PlaneCutter nicht integriert; aktuelle GUI-Referenzpfade bleiben aktiv, da Ausgabe- und Randverträge nicht verglichen wurden. |
| A-V0.13-00013 | U-V0.13-000001, U-V0.13-000007 | Baseline-Matrix je Kandidat aktualisiert; wiederverwendbare bestehende Belege nicht doppelt erhoben; fehlende Belege einzeln benannt. |
| A-V0.13-00014 | U-V0.13-000006 | Vorher-/Nachher-Messung für P-06 und P-08; A/B-Messungen P-01/P-02 klar als nicht-historisch gekennzeichnet. |
| A-V0.13-00015 | U-V0.13-000006, U-V0.13-000007 | Kandidatentabelle P-01 bis P-12 mit Status, Messgrenze, Tests und fehlenden Nachweisen ergänzt; Gesamtprüfung ausgeführt, uneingeschränkte Abnahme wegen der M3-Fehler nicht erreicht. |
| A-V0.13-00016 | U-V0.13-000008 | 100-ms-Timer, Bündelung ohne Neustart, neuester Endwert, sofortige Fehler/Erholung/Invalidierung/Pause und unabhängige 3D-/Analogausgabe werden gezielt geprüft; siehe Abschnitt 8. |
| A-V0.13-00017 | U-V0.13-000008 | Unveränderte QLabel-/Detailtexte und SVG-Ladeaufrufe werden nicht wiederholt; Solverstatus vergleicht vor setText. Kein neuer Serializer oder Markerumbau. |
| A-V0.13-00018 | U-V0.13-000008 | Aktiver GUI-/Physikpfad geprüft; keine normalen Schritt-/Frame-Logs gefunden. Startup, Nutzeraktionen, Warnungen und Fehler unverändert erhalten. |
| A-V0.13-00019 | U-V0.13-000009 | Gemeinsamer Formatter, Rundung/negative Null, Rechtsbündigkeit, Detaildarstellung, ursprüngliche Kleinwerte/Status und unverändertes Zeitformat geprüft; 382 Tests bestanden, siehe Abschnitt 9. |

## 8. Ergänzungsauftrag: Zahlenanzeigen und Logging

Umgesetzt in
[hauptfenster.py](../../../../../code/python/segelphysik/gui/hauptfenster.py),
[kraefte_werte.py](../../../../../code/python/segelphysik/gui/kraefte_werte.py) und
[navigationswidgets.py](../../../../../code/python/segelphysik/gui/navigationswidgets.py):

- Echtzeit-Krafttabellen/-karten/-details übernehmen gebündelt den neuesten
  Snapshot nach 100 ms. Der Timer wird durch neue Werte nicht verschoben.
  Die 3D-Brücke erhält ihren Snapshot weiterhin unmittelbar. Pause übernimmt
  ausstehende Werte sofort; Leeren/Fehler verwirft sie, ohne den Fehlertext
  anschließend durch einen alten Wert zu überschreiben.
- Digitale Winkel/Geschwindigkeit werden unabhängig von analogen Zeigern
  aktualisiert. Fehler-/Verfügbarkeitswechsel, Erholung und statische
  Aktualisierungen sind sofort sichtbar. Verborgene Navigationsfenster
  stoppen ihren Zahlentimer und zeigen beim Öffnen den neuesten Stand.
- Gleiche Texte werden vor `setText`/`setPlainText` verglichen.
  Byte-identische SVGs werden nicht erneut in den Renderer geladen;
  identische gerundete Geschwindigkeiten vermeiden auch die Serialisierung.
- Loggingprüfung: `gui/app.py`, `gui/hauptfenster.py`, GUI-Worker,
  `core/echtzeit_prozess.py`, `core/auftrieb.py` und
  `core/physik_backend.py`. Im normalen aktiven Schritt-/Framepfad keine
  unnötigen Ausgaben gefunden. OpenCL-Ausgaben gehören zu Setup/Fallback;
  der allgemeine Fallback-Prototyp wird vom aktiven Physikpfad nicht
  aufgerufen. Deshalb keine Loggingänderung und kein behaupteter Loggewinn.

Nachweise: zusätzliche Tests in
[test_kraefte_werte.py](../../../../../tests/test_kraefte_werte.py),
[test_navigationswidgets.py](../../../../../tests/test_navigationswidgets.py),
[test_gui_steuerung.py](../../../../../tests/test_gui_steuerung.py) und
[test_kraefte_integration.py](../../../../../tests/test_kraefte_integration.py).
Sie prüfen
30 gebündelte Eingänge mit einem Timerstart/einer finalen Kraftanzeige,
100 ms mit `PreciseTimer`, aktuell bleibende analoge Zeiger, Endwert,
Fehler/Erholung/Pause, synchrone Eingabevalidierung und ausbleibende
Text-/SVG-Ladeaufrufe. Das sind Verhaltensprüfungen, keine Laufzeitmessungen.
Isolierte CPU-/Framebeschleunigung: **nicht gemessen; Verbesserung nicht
belegt**. Kein nativer Umbau und keine neuen Zeitmarker.

Abschließender gezielter Testlauf (Offscreen, Python-/C++-Parameter gemäß
bestehender Testauswahl):

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_kraefte_werte.py tests\test_navigationswidgets.py tests\test_kraefte_integration.py tests\test_gui_steuerung.py tests\test_gui_app.py tests\test_gui_worker_referenz.py tests\test_native_instrumente.py
```

**Ergebnis: 343 bestanden, keine Fehler, keine Skips oder Abwahlen,
96,59 s.** Die Auswahl deckt geänderte Anzeigeverträge, Pause/Fehler,
direkte Hauptfensteranbindung, GUI-/Workerintegration und native
Instrumentaufbereitung ab. Auch verborgene Fenster und ein fehlgeschlagener
SVG-Ladeversuch mit anschließend erneutem Versuch sind geprüft.
`git diff --check` ohne Formatfehler.

Dies ist keine erneute Gesamtsuite oder interaktive Nutzerabnahme.
Die historischen Gesamtbefunde von M3 wurden in diesem Teilauftrag nicht
erneut geprüft; offene ursprüngliche Kandidaten werden dadurch nicht
abgeschlossen. Keine Commit-/Push-/Tag-Aktion; der Arbeitsstand bleibt
uncommittiert.

## 9. Ergänzungsauftrag: feste Anzeigepräzision

Die zentrale Funktion `zahlenwert` in
[kraefte_darstellung.py](../../../../../code/python/segelphysik/core/kraefte_darstellung.py)
formatiert Kräfte mit ganzen N, Momente mit ganzen Nm und Längen mit zwei
Nachkommastellen in m. Keine kN/kNm-Umschaltung; Dezimalkomma und
Tausendergliederung mit Leerzeichen. Negative gerundete Null wird als
`0 N`, `0 Nm` bzw. `0,00 m` angezeigt. Das gilt auch für Details und
Tooltips; deren bisherige zusätzliche Dezimalstellen für diese Größen
entfallen ausdrücklich. Das Zeitformat bleibt erhalten.

Alle bestehenden Verbraucher nutzen dieselbe Formatierung: Krafttabelle,
Karten, Kopfzeile, Details/Tooltips, Legenden und 3D-Beschriftungen.
Die vorhandene Rechtsbündigkeit der numerischen Tabellenspalten bleibt
unverändert. Es werden keine Simulationswerte gerundet oder zurückgeschrieben.
Kleine aktive Kräfte dürfen als `0 N` erscheinen, behalten aber ihren
internen Wert und ihren Status; dies bestätigt kein Gleichgewicht.
Pfeillängen und Momentenradien rechnen weiterhin mit den unveränderten Werten.

Nachweis:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_kraefte_darstellung.py tests\test_kraefte_werte.py tests\test_kraefte_integration.py
```

**382 bestanden, keine Fehler, Skips oder Abwahlen; 91,96 s.**
Die Auswahl prüft den gemeinsamen Formatter samt Grenzwerten, Tabellen/
Details, Rechtsbündigkeit und die bestehende Kräfte-/3D-Integration mit
Python-/C++-Parametern. Keine neue Gesamtprüfung oder interaktive
Nutzerabnahme; ursprüngliche V0.13-Restpunkte bleiben offen.
Keine Laufzeitmessung und kein behaupteter Simulationsgeschwindigkeitsgewinn.
Änderungen bleiben uncommittiert.

## 10. Ausnahmesicherung am Tagesende: Tag 0.13

**Ausdrückliche Nutzerfreigabe am 21.10.2026 um 19:24 Uhr:**
„Gut, lass uns die Test bei nächsten korrigieren. Dokumentier das und mache
comit, tag, push. Als ausnahme von mir genehmigt“.

Die Freigabe erlaubt einmalig Commit, Tag `0.13` und Push trotz der beiden
bekannten verbleibenden Testfehler. Sie ist weder eine generelle Änderung
der Release-Regel noch eine vollständige fachliche V0.13-Abnahme. Frühere
Angaben „uncommittiert“ beschreiben den jeweiligen damaligen Arbeitsstand;
dieser Abschnitt dokumentiert die anschließende Sicherungsfreigabe.

Ungefilterte vollständige Prüfung vor der Sicherung:
**1824 bestanden, 2 fehlgeschlagen, 1 übersprungen; 147,76 s.**
Die korrigierten Navigations- und Inventartests bestehen im Gesamtlauf.
Weiter offen und beim nächsten Termin zu bearbeiten:

| Prüfung | Tatsächlicher Befund | Nächster Schritt |
|---|---|---|
| Referenzmanifest, `test_migration_v010.py` | Aktuelle GUI-Konfiguration weicht in `konfigurationen/settings.json` vom historischen Referenzcommit ab. | Historischen Referenzvertrag und spätere Einstellungen getrennt prüfen, ohne Originalhashes zu ersetzen. |
| Optimist-Schrittparität, `paritaet_batch.py` | Momentenabweichung maximal 1,01024256e-9 bei bestehender Grenze 1e-9; Gesamtmoment z und Kielmoment z betroffen. | Numerische Ursache und Paritätsvertrag untersuchen; keine pauschale Toleranzlockerung. |

Details und ausführbarer Testbefehl:
[Testdokumentation](../../../../../tests/README.md#ausdrücklich-genehmigte-sicherung-als-tag-013).
Die ursprünglichen offenen Kandidaten P-07/P-10/P-11/P-12 und fehlenden
Performancebelege werden durch die Sicherung nicht abgeschlossen.
Nicht freigegebene Backlogänderungen bleiben außerhalb der Sicherung.
