# Spezifikation V0.13: Umsetzung der Performance-Kandidaten

**Stand:** 21.10.2026  
**Status:** Entwurf; fachlicher Umfang und selektive Messregel aus den Nutzeraufträgen vom 21.10.2026
**Maßgebliche Spezifikation für diesen Umfang:** diese Datei

## 1. Ziel und Geltung

Ziel ist, alle zwölf Kandidaten P-01 bis P-12 aus der
[Kandidatenliste V0.13](../Optimierungskandidaten_Performance_V0.13.md)
als zusammenhängenden Arbeitsumfang zu behandeln und ihre beschriebene
Funktion zu implementieren, soweit dies ohne Änderung bestehender
Fachverträge möglich ist. Die Kandidaten-IDs bleiben vorläufige
Arbeitsverweise; die Anforderungen dieser Spezifikation tragen die
verbindlichen A-IDs.

Die Umsetzung darf in voneinander unabhängigen Arbeitspfaden parallel
erfolgen. Abhängige oder konkurrierende Änderungen werden vor der Integration
zusammengeführt und gemeinsam auf Korrektheit geprüft. „Parallel“ hebt weder
fachliche Abhängigkeiten noch die Pflicht zur Integration und Regressionstestung
auf.

Vor jeder Änderung wird für den jeweiligen Pfad geprüft, ob eine passende,
ausreichende Baseline vorliegt. Ausreichende vorhandene Baselines werden
unverändert wiederverwendet; sie werden nicht doppelt gemessen. Nur fehlende
oder für den Kandidaten nicht isolierte Baselines dürfen vor der Änderung
gezielt einmal erhoben werden. Nach der Änderung wird dieselbe Messgrenze
unter vergleichbaren Bedingungen gemessen. Messungen für einen Pfad dürfen
nicht als Beleg für einen anderen Pfad ausgegeben werden.

Die bestehende Entscheidung „derzeit keine weitere Produktivmaßnahme
freigegeben“ im V0.12-Umsetzungsplan wird durch diese neue, ausdrückliche
Beauftragung für V0.13 ersetzt, aber nicht rückwirkend umgeschrieben.

## 2. Verbindliche Arbeits- und Messregeln

- Vorhandene Messinventare und Rohdaten gegen den jeweiligen Kandidatenpfad,
  Eingaben, Build und Messgrenze prüfen. Ausreichende, vergleichbare
  Messreihen werden übernommen und nicht wiederholt.
- Eine neue Baseline wird nur für einen Kandidaten erhoben, dessen
  benötigter Pfad in den vorhandenen Unterlagen nicht passend und isoliert
  gemessen ist. Die Baseline muss vor jeder Codeänderung dieses Pfads
  vorliegen.
- Neue Baselines und Nachher-Messungen verwenden gleiche Eingaben,
  Modell-/Quellstand soweit vergleichbar, Hardware/Build, Thread-/Prozesszahl,
  Warm-up und Messgrenze. Mindestens ein separater Warm-up und fünf
  Messungen je neu gemessener Variante sind erforderlich, sofern keine
  begründete freigegebene Messregel eine Abweichung vorsieht. Rohdaten,
  Median und Streuung werden gespeichert.
- Keine vollständigen Baseline-Läufe wiederholen, wenn nur ein fehlender
  Teilpfad nachgemessen werden muss. Eine übergeordnete Messung ersetzt
  keine Kandidatenisolierung; verschachtelte Zeiten werden weder addiert
  noch einem einzelnen Kandidaten zugeschrieben.
- Änderungen und Testergebnisse nach Stand kennzeichnen. Eine bestandene
  Korrektheitsprüfung belegt keine Laufzeitverbesserung. Wo ein geeigneter
  Vorher-/Nachher-Vergleich fehlt, lautet das Performanceergebnis
  „nicht gemessen; Verbesserung nicht belegt“.
- Fachliche Genauigkeit, Fehlerbehandlung, native/Python-Verträge,
  GUI-Verhalten und Echtzeitfunktion bleiben erhalten. Bestehende Toleranzen
  dürfen nicht pauschal gelockert werden.
- Keine Näherungsverfahren, Approximationen, veraltete Cache-Ergebnisse oder
  Genauigkeitslockerungen einführen. P-10 muss den vorhandenen exakten
  Ebenenschnitt erhalten.
- Neue Python/C++-Schnittstellen sind zu vermeiden. Falls eine Änderung
  fachlich unvermeidbar ist, muss die CPPI-Kennung vor der Implementierung
  vergeben und das Schnittstellenregister aktualisiert werden.
- Die Marker-Kugelvorlage ist bereits umgesetzt und gemessen. Sie wird als
  bestehender Stand erhalten und nicht durch verworfene SVG-Varianten ersetzt.

## 3. Aktive Anforderungen

| Kennung | Kandidat | Anforderung | Prüfergebnis / Abnahmekriterium |
|---|---|---|---|
| A-V0.13-00001 | P-01 | Körper-/Mesh-Snapshots pro unverändertem Geometrie-/Modellzustand wiederverwenden, sofern ein sicherer Versions- und Lebensdauerschlüssel möglich ist. Änderungen an Mesh, Basis-/Relativpose, Gelenken oder Modell invalidieren den Cache. Die dynamische 6-DOF-Pose wird pro Snapshot neu übernommen und invalidiert den geometrieunabhängigen Kontext nicht. | Tests belegen Cache-Wiederverwendung bei dynamischen Zustandsänderungen, Invalidierung nach jeder unterstützten Änderung an vorbereiteter Geometrie sowie unveränderte Snapshot-Inhalte gegenüber einer frisch erzeugten Referenz. Kein veralteter dynamischer Zustand darf an Worker oder Solver gelangen. |
| A-V0.13-00002 | P-02 | Wasserlinienschnitt und abgeleitete GUI-Geometrie bei unveränderter Pose und Geometrie wiederverwenden; bei Änderung vollständig neu berechnen. | Tests für Ruhelage, bewegte Pose und Geometrieänderung belegen exakte Übereinstimmung der Unterwasser-/Überwasserflächen und Kontur mit dem uncached Referenzpfad sowie korrekte Sichtbarkeit/Aktualisierung. |
| A-V0.13-00003 | P-03 | Task-Batchverarbeitung und Übergaben behandeln, ohne Simulationsschritte, Reihenfolge, Abbruchverhalten, Eingabereaktion oder Anzeigevertrag zu verlieren. | Bestehende Worker- und Batchverträge bestehen. Bei fehlendem Messbeleg darf keine konkrete Batchgrößenänderung als Optimierung oder schneller ausgewiesen werden; ein unveränderter Batchwert ist als nicht optimiert zu dokumentieren. |
| A-V0.13-00004 | P-04 | Wasser-Splat-Arbeit nur innerhalb der bestehenden Render- und Skip-Logik reduzieren; nativen und Python-Pfad berücksichtigen. | Tests belegen identische Ausgabe, korrekte Skip-Frequenz und Randbehandlung für leere, kleine und reguläre Netze. Keine Änderung am physikalischen Standardpfad. |
| A-V0.13-00005 | P-05 | Wiederholte GUI-Arbeit bei Gelenk-Sliderereignissen vermeiden, soweit Ereignisverarbeitung dies erlaubt; Ereignisreihenfolge und endgültige Gelenkstellung beibehalten. | Tests mit einzelnen und dicht aufeinanderfolgenden Ereignissen belegen korrekte Endstellung, sichtbare Aktualisierung, keine verlorenen finalen Werte und korrekte Neuaufbereitung gelenkabhängiger Geometrie. |
| A-V0.13-00006 | P-06 | Unveränderliche Eingaben im Python-Referenzpfad nicht unnötig wiederholt validieren, sofern Setup-Validierung denselben Fehlervertrag sicherstellt. | Gültige Eingaben liefern dieselben Resultate; ungültige und Grenzwerteingaben lösen dieselben öffentlichen Fehlerarten aus. Native Standardpfade bleiben unberührt. |
| A-V0.13-00007 | P-07 | Interne Kraft-/Wrench-Ergebnisobjekte und Kopien im Python-Referenzpfad reduzieren, ohne öffentliche APIs, Eigentums-/Mutabilitätsverträge oder Ergebniswerte zu verändern. | Gezielte Referenztests vergleichen Kräfte, Momente, Frames und Objektlebensdauer; äußere APIs und native/Python-Parität bleiben erhalten. |
| A-V0.13-00008 | P-08 | Hydrodynamische Normalenmasken und temporäre Arrays im Python-Referenzpfad nur dann wiederverwenden, wenn die zugehörigen Mesh-/Normalendaten unveränderlich sind oder korrekt invalidiert werden. | Tests belegen identische Ergebnisse, korrekte Meshänderungsbehandlung und getrennte Zustandshaltung pro Modell/Aufruf. Vorhandene Normalenmaske wird einmal bei der unveränderlichen Geometrievorbereitung berechnet und ist nicht schreibbar. |
| A-V0.13-00009 | P-09 | Native Arbeitsbereiche in Hydrodynamik und exaktem Ebenenschnitt task-/kontextlokal wiederverwenden, um vermeidbare dynamische Speicherarbeit zu vermeiden. Bereits vorhandene Hydrodynamik-Wiederverwendung bleibt erhalten; Hydrostatik darf keinen gemeinsam veränderlichen Zustand zwischen parallelen Aufrufen teilen. | Native Batch-, Hydrostatik-, Abbruch- und Paritätstests bestehen. Ergebniswerte entsprechen dem bisherigen exakten Vertrag. Die vorhandene Hydrodynamikmessung wird ausschließlich als historische Messung dieses Kandidaten berichtet; der nicht gemessene Hydrostatikanteil bleibt ungemessen. |
| A-V0.13-00010 | P-10 | Einen hierarchischen exakten Ebenenschnitt mit voraggregierten Momenten als alternative interne Auswertung implementieren, sofern die bestehenden exakten Ergebnisse und Geometrieannahmen erhalten bleiben. | Analytische Grundkörper und gezielte Mesh-/Grenzfälle vergleichen Volumen, Schwerpunkt, Kraft und Moment gegen den bestehenden exakten Algorithmus. Fehlerbudget und bestehende Toleranzen werden eingehalten. Bei fehlendem sicheren exakten Nachweis wird der neue Algorithmus nicht als aktiv verwendet und die Abweichung dokumentiert. |
| A-V0.13-00011 | P-11 | Compiler-Vektorisierung und Release-Profiloptimierung nur mit sicheren, reproduzierbaren Projekteinstellungen unterstützen; keine Genauigkeitslockerung und keine nicht belegten Hardwareannahmen. | Build-/Paritätstests bestehen; Compileroptionen sind auf unterstützte Toolchains begrenzt und verändern keine numerischen Verträge. Ohne neue Messungen wird kein Laufzeitgewinn behauptet. |
| A-V0.13-00012 | P-12 | `vtkPlaneCutter` als alternative GUI-Schnittimplementierung integrieren, sofern vorhandene Eingabe-, Kontur-, Deckel- und Meshverträge vollständig erhalten bleiben; die Hydrostatik-Volumen-/Schwerpunktrechnung darf nicht ersetzt werden. | GUI-Referenzfälle vergleichen Schnittgeometrie und Konturen mit dem bisherigen Verfahren, einschließlich leerer, koplanarer und mehrfacher Konturen. Scheitert ein Vertragstest, bleibt der bisherige GUI-Pfad aktiv und die Abweichung wird dokumentiert. |
| A-V0.13-00013 | Messregeln | Vor Codeänderungen die Baseline-Abdeckung je Kandidatenpfad prüfen. Vorhandene ausreichende Baselines wiederverwenden; nur fehlende oder nicht isolierte Baselines gezielt und einmal vorab erheben. | Baseline-Matrix weist für P-01 bis P-12 Quelle, Messgrenze, Eignung und Entscheidung „wiederverwenden“/„gezielt nachholen“ aus. Kein bereits ausreichend gemessener Pfad wird erneut baseline-gemessen. |
| A-V0.13-00014 | Nachher-Messungen | Nach Implementierung jede Änderung an derselben geeigneten Messgrenze wie ihre Baseline messen; ausreichende vorhandene Baselines nicht wiederholen. | Vorher-/Nachher-Bedingungen sind vergleichbar; Rohdaten, Median und Streuung liegen vor. Unterschiede innerhalb der Streuung gelten als unklar. |
| A-V0.13-00015 | Ergebnisbericht | Für jeden Kandidaten Änderung, Implementierungsstatus, Korrektheitstests und Performancebeleg getrennt berichten. | P-01 bis P-12 erscheinen einzeln in der Ergebnisliste. Vorhandene oder neue Messwerte werden mit Messgrenze/Quelle ausgewiesen; fehlende Vergleiche lauten ausdrücklich „nicht gemessen; Verbesserung nicht belegt“. |
| A-V0.13-00016 | Ergänzungsauftrag: Zahlenanzeigen | Numerische Kraft-, Winkel- und Geschwindigkeitsanzeigen im laufenden Echtzeitbetrieb auf höchstens 10 Hz bündeln. Physik, Kamera, analoge Zeiger und 3D-Kraftdarstellung behalten ihren bisherigen Takt. | Ein präziser 100-ms-Einmaltimer übernimmt jeweils den neuesten Wert, ohne bei weiteren Eingängen neu zu starten. Der letzte Wert erscheint auch ohne weiteren Eingang. Statik, Pause, Fehler-/Verfügbarkeitswechsel und Bedienung bleiben unmittelbar; Invalidierung löscht ausstehende Altwerte. |
| A-V0.13-00017 | Ergänzungsauftrag: identische Anzeigen | Unveränderte Texte der Kraftanzeigen und Solverstatus nicht erneut setzen; identische Navigations-SVGs nicht erneut laden oder zeichnen. | Tests zählen Text-/SVG-Ladeaufrufe und belegen No-ops bei identischen Anzeigewerten. Änderungen und Fehleranzeigen bleiben sichtbar, Detailauswahl wird durch identische Texte nicht zurückgesetzt. Kein alternativer SVG-Serializer und kein Markerumbau. |
| A-V0.13-00018 | Ergänzungsauftrag: Logprüfung | Unnötige normale Schritt-/Frame-Logs und teure Logargumente im aktiven GUI-/Physikpfad prüfen und nur bei vorhandenem Befund entfernen oder absichern. Warnungen und Fehler erhalten. | Quellprüfung dokumentiert betroffene Pfade und Ergebnis. Sind keine unnötigen Normalfallausgaben vorhanden, keine künstliche Loggingänderung; keine unbelegte Beschleunigungsbehauptung. |
| A-V0.13-00019 | Ergänzungsauftrag: Zahlenformat | Kräfte in ganzen N und Momente in ganzen Nm darstellen, ohne kN/kNm oder wissenschaftliche Notation. Positionen, Abstände und Hebelarme in m mit genau zwei Nachkommastellen. Dieselben Regeln für Tabelle, Kopf/Karten, Details/Tooltips, Legenden und 3D-Beschriftungen verwenden. Numerische Tabellenspalten bleiben rechtsbündig. | Anzeige rundet statt abzuschneiden, unterdrückt negative Null und verwendet Dezimalkomma sowie Leerzeichen zur Tausendergliederung. Interne Werte, Status, Gleichgewichtsbewertung und physikalische Skalierung bleiben unverändert; gerundete Null ist kein Gleichgewichtsnachweis. Zeitformat bleibt unverändert. |

## 4. Kandidatenbehandlung und Parallelität

Die fachlichen Arbeitsbereiche können parallel bearbeitet werden:

| Arbeitspfad | Kandidaten | Integrationshinweis |
|---|---|---|
| Snapshot- und GUI-Geometrie | P-01, P-02, P-05 | Gemeinsame Zustands-/Invalidierungstests; Änderungen an GUI- und Körperversionen zusammenführen. |
| Native Batch- und Arbeitsbereiche | P-03, P-09 | Native Worker- und Abbruchverträge gemeinsam prüfen. Bestehende P-09-Änderungen im Arbeitsbaum zuerst integrieren, nicht überschreiben. |
| Python-Referenzpfad | P-06, P-07, P-08 | Änderungen am Referenzpfad gemeinsam mit analytischen und Paritätstests abnehmen; Produktionspfad nicht stillschweigend umschalten. |
| Renderpfade | P-04, P-12 | Wasser-Splat und GUI-Schnitt getrennt halten; `vtkPlaneCutter` nicht in die Hydrostatik einführen. |
| Exakter Hydrostatikalgorithmus und Build | P-10, P-11 | Algorithmusänderung und Compileroptionen getrennt schalten und testen; keine Approximation. |

Die Einteilung erlaubt parallele Bearbeitung, ist aber kein Auftrag,
konkurrierende Änderungen an derselben Datei ungeprüft zu überschreiben.
Schnittstellen, gemeinsame Fixtures und Regressionstests werden vor
Integration abgestimmt. Wenn die notwendige Korrektheit mit der vorhandenen
Testabdeckung nicht sicher nachgewiesen werden kann, bleibt die betreffende
Änderung deaktiviert oder wird als offen dokumentiert.

### Ergänzungsauftrag: kurzfristige GUI-Entlastung

Der spätere Nutzerauftrag „Implementiere 1–3. Die Zeitmarker machen wir
später noch mal“ ergänzt die Kandidatenarbeit um A-V0.13-00016 bis
A-V0.13-00018. Zeitmarker und eine Änderung der Simulationsgeschwindigkeit
gehören ausdrücklich nicht dazu. Nachgewiesen werden Anzeigehäufigkeit,
Endwerte, unveränderte Analog-/3D-Aktualisierung und vermiedene Schreib-/
Ladeaufrufe. Diese Funktionsnachweise sind keine Laufzeitmessung; ein
isolierter oder gesamter Performancegewinn bleibt ohne Vergleichsmessung
unbelegt. Die ursprünglichen Messanforderungen für P-01 bis P-12 bleiben
unverändert.

## 5. Vorhandene Leistungsbelege und Grenzen

Die Messwerte stammen aus den vorhandenen V0.12-Unterlagen. Sie sind keine
neuen V0.13-Messungen.

| Bereits gemessener Stand | Vorhandener Wert | Zulässige Aussage |
|---|---:|---|
| Folkeboot, `exakt_union`, C++-GUI-Baseline, fünf Läufe | Worker-Batch-Median **1,639 ms**; Worker-Roundtrip **15,259 ms**; Pose **4,447 ms**; Render **24,920 ms** | Gesamt-/Aufrufwerte; isolieren weder Snapshot, Wasserlinienschnitt noch Splat. |
| Native Hydrodynamik-Arbeitsbereich, Referenz vs. Kandidat, fünf Läufe je Variante | Worker-Batch-Median **1,66495 → 1,47140 ms** (**-11,62 %**); die Wertebereiche der Laufmediane überlappen nicht. | Historischer Gewinn für den gemessenen Worker-Batch des P-09-Hydrodynamikanteils. Kein separater Allokations- oder Hydrostatikgewinn. Worker-Roundtrip- und GUI-Metriken sind unklar bzw. überlappend. |
| Exakte Marker-Kugelvorlage, fünf Läufe | Qt-Swap-Intervall-Median **168,298 → 151,201 ms** (rund **-10,16 %**); Durchsatz **0,975985 → 0,976887 Simulationssekunden/Wandsekunde** | Bereits umgesetzter und gemessener Stand, kein Nachweis für P-01 bis P-12 und kein neuer V0.13-Gewinn. |
| Alle übrigen P-01 bis P-08 und P-10 bis P-12 | Kein geeigneter isolierter Vorher-/Nachher-Beleg vorhanden | Vorher-Messung fehlt oder ist nicht isoliert; gezielte Baseline vor Umsetzung erforderlich. |

Primärquellen:

- [Kandidatenliste V0.13](../Optimierungskandidaten_Performance_V0.13.md)
- [V0.12-Umsetzungsplan](../../zuV0.12/Umsetzungsanleitungen/Umsetzungsplan_V0.12.md)
- [Hydrodynamik-Arbeitsbereich-Auswertung](../../zuV0.12/Messungen/Speed_V0.12_2026-10-21/hydro_workspace_assessment_v0.12.json)
- [GUI-Kandidaten-Auswertung](../../zuV0.12/Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json)
- [Speed-Analyse V0.12](../../zuV0.12/Optimierung/Speed_2_2_2_2_2.md)
- [Nummerierungs-Instruction](../../../../../.github/instructions/nummerierung.instructions.md)
- [Testpflege-Instruction](../../../../../.github/instructions/teststruktur.instructions.md)
- [Schnittstellenregister-Instruction](../../../../../.github/instructions/schnittstellenregister.instructions.md)
- [Releaseumsetzungs-Instruction](../../../../../.github/instructions/releaseumsetzung.instructions.md)

## 6. Nicht umsetzen

- **Marker plus SVG-no-op** (keine A-ID): Der historische Kombinationsversuch
  belegte keinen belastbaren Gewinn; mehrere Signale verschlechterten sich.
  Diesen Markerumbau nicht erneut aufnehmen. Der spätere ausdrückliche
  GUI-Auftrag A-V0.13-00017 erlaubt separat das Unterlassen identischer
  Text-/SVG-Ladeaufrufe, behauptet aber keinen gemessenen Laufzeitgewinn.
- **SVG-Template-Serializer** (keine A-ID): Der vorhandene Vergleich zeigte
  eine Regression. Nicht erneut aufnehmen.
- Näherungsbasierte Hydrostatik-Caches, Voxel-Pfadwechsel und
  Genauigkeitslockerungen: nicht Bestandteil der Kandidaten P-01 bis P-12;
  sie verletzen den exakten Rechenvertrag ohne gesonderte fachliche Freigabe.
- Neue Windsimulation, neue Physik oder Änderungen an nicht aufgeführten
  Performancepfaden: außerhalb des freigegebenen Umfangs.

## 7. Umsetzungs- und Abnahmestatus

Der verbindliche Arbeitsstand, Abhängigkeiten, Meilensteine, Tests,
Baselinemessungen, Vergleiche und Rückverfolgbarkeit stehen im einzigen
[Umsetzungsplan V0.13](../Umsetzungsplan/Umsetzungsplan_V013.md). Planung,
Implementierung, Test, Integration und Abnahme sind getrennte Status.
Performance-Abnahme erfordert ausreichende, vergleichbare Messungen. Dieses
Dokument autorisiert gezielte Messungen nur für vorher als unzureichend
festgestellte Baselines und dazugehörige Nachher-Vergleiche.
