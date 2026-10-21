# Optimierungskandidaten Performance V0.13

**Stand:** 21.10.2026  
**Zweck:** Übernommene Kandidatenliste aus V0.12 mit geprüftem Umsetzungsstand
und Priorität für die Umsetzung in V0.13. Die verbindlichen Anforderungen
stehen in der [Spezifikation V0.13](./Spezifikationen/Spezifikation_V013.md);
die Umsetzungsschritte stehen im
[Umsetzungsplan V0.13](./Umsetzungsplan/Umsetzungsplan_V013.md).

**Status und Priorität:** „Teilweise umgesetzt“ bezeichnet nur den belegten
Teilumfang; übrige Kandidaten sind nicht umgesetzt. Die Ränge aus der
vorherigen Einordnung bleiben die ursprüngliche Prüfpriorität. Der
Nutzerauftrag vom 21.10.2026 wählt jetzt alle zwölf Kandidaten zur
Bearbeitung aus. Ausreichende vorhandene Baselines werden wiederverwendet und
nicht erneut gemessen. Nur für nicht ausreichend oder nicht isoliert
abgedeckte Pfade werden gezielte Baselines vor der Änderung erhoben; danach
wird dieselbe Messgrenze zum Vergleich gemessen. Ohne geeigneten Vergleich
bleibt ein Performancegewinn unbewiesen.

Der V0.12-Plan führt wiederverwendbare native Hydrodynamik-Arbeitsbereiche
unter P-03; die Kandidatenliste führt denselben Kandidaten als P-09. Diese
historische ID-Abweichung bleibt unverändert und wird hier über die
Bezeichnung aufgelöst.

Die vorhandene Messreihe bleibt die Baseline; vollständige Baseline-Läufe
sollen nicht wiederholt werden. Die folgenden Messwerte stammen aus dem
Folkeboot-Szenario mit `exakt_union` und C++-Rechenpfad. Wo kein Einzelwert
vorliegt, ist der Kandidat nicht isoliert gemessen. Prozent- und
Millisekundenschätzungen aus der Codeanalyse sind Hypothesen, keine
nachgewiesenen Gewinne.

## Bestehende Optimierungskandidaten

| Temp-ID | Name | Kurzbeschreibung | Aktuelle Messzeit (Median) | Optimierungspotenzial | Umsetzungsstand | Priorität für weitere Prüfung |
|---|---|---|---|---|---|---|
| **P-01** | Snapshot pro Echtzeit-Task | Körper-/Mesh-Snapshots bei unveränderter vorbereiteter Geometrie wiederverwenden. Mesh-, Basis-/Relativpose-, Gelenk- oder Modelländerungen invalidieren; dynamische 6-DOF-Pose je Snapshot übernehmen, ohne den geometrieunabhängigen Kontext neu aufzubauen. | A/B-Median: wiederverwendeter Kontext **98,475 µs**, Neuaufbau **256,355 µs**. Gegenmessung im aktuellen Arbeitsbaum; kein historischer Vorherstand. | A/B-Messung: **61,59 %** bzw. **157,88 µs** pro Snapshot niedriger; vollständiger Worker-/GUI-Gewinn nicht belegt. | Im aktuellen uncommitted Arbeitsbaum implementiert; gezielte Tests belegen statische Invalidierung und dynamische Zustandsübernahme. Messreihe und Einschränkung im [P-01-Messbeleg](./Messungen/messung_p01_kontextwiederverwendung_v0.13.json). | Weitere Vorher-/Nachhermessung nur mit rekonstruierbarem historischen Stand; A/B-Vergleich nicht als historische Regression ausgeben. |
| **P-02** | Wasserlinienschnitt bei unveränderter Pose | Im GUI-Framepfad Schnitt und Geometrie nur bei geänderter Pose oder Geometrie neu berechnen. | A/B-Median auf Folkeboot-Meshgruppe: Cachetreffer **4,240 µs**, Neuberechnung **271,125 µs**; kein historischer Vorherstand. | A/B-Messung: **98,44 %** bzw. **266,885 µs** niedriger pro Cachetreffer; kein vollständiger Framegewinn belegt. | Im aktuellen uncommitted Arbeitsbaum existiert ein exakter Geometrie-Cache mit Tests für Treffer und Invalidierung. Messgrenze und Rohdaten im [P-02-Messbeleg](./Messungen/messung_p02_wasserliniencache_v0.13.json). | Weiterer historischer Vorher-/Nachher-Nachweis nur mit rekonstruierbarem Vorherstand; kein Renderinganteil erfasst. |
| **P-03** | Task-Batchgröße und Übergabekosten | Vorhandene Schrittbündelung anhand vorhandener Worker-/Roundtrip-Metriken prüfen, ohne Rückstand, Eingabelatenz oder Anzeigeaktualität zu verschlechtern. Batchgröße nicht pauschal erhöhen. | Nativer Batchaufruf: **20,640 µs/Schritt** bei Batch 1, **16,758 µs/Schritt** bei 16, **16,559 µs/Schritt** bei 64; Bereiche 16/64 überlappen deutlich. | Batchamortisierung sichtbar, aber über 16 kein belastbarer Vorteil; Queue-/Latenzanteil nicht gemessen. | Beibehaltene Batchgröße 16. Die 64er-Variante wird nicht als Optimierung übernommen, weil ihr winziger Medianvorteil innerhalb der Streuung liegt und größere Tasklatenz droht. [P-03-Messbeleg](./Messungen/messung_p03_native_batchgroessen_v0.13.json). | Bestehende Einstellung 16 erhalten; Worker-Roundtrip-/Latenzwerte nicht aus dem isolierten Nativeaufruf ableiten. |
| **P-04** | Wasser-Splat im Renderpfad | Nur weiter untersuchen, wenn Messungen den Splat als relevanten Frameanteil ausweisen. Mesh-abhängiges Überspringen jedes zweiten Aufrufs und nativen C++-Pfad berücksichtigen. | Synthetische 700 Partikel: C++ **2,021 ms**, Python **19,411 ms** Median (9,61x). | Vorhandener nativer Pfad ist im isolierten A/B klar schneller; kein Anteil am vollständigen Renderframe gemessen. | Native C++-Splatberechnung und meshabhängiges Überspringen sind im Arbeitsbaum vorhanden. Kein Vorher-/Nachher-Beleg gegen einen früheren nativen Kernel. Details im [P-04-Messbeleg](./Messungen/messung_p04_wassersplat_cpp_python_v0.13.json). | Native/Skip-Vertragstests erhalten; weitere Änderung erst nach isoliertem Produktionsprofil. |
| **P-05** | Gelenk-Updates in der GUI | Bei häufigen Slider-Ereignissen wiederholte Geometriearbeit untersuchen; Endstellung und Bedienvertrag müssen erhalten bleiben. | Zeit pro Ereignis nicht gemessen. | Bedingt durch Nutzung und gemessene Ereigniskosten. | Im aktuellen uncommitted Arbeitsbaum fasst ein Timer Gelenkereignisse zusammen; Verhaltenstest belegt vier Ereignisse zu einer Geometrie-/Renderaktualisierung und bewahrt den Endwert. Historischer Vorherstand fehlt; kein Leistungsgewinn belegt. | Vorhandene Coalescing-Änderung und Vertrag erhalten; historische Zeitersparnis bleibt unbelegt. |
| **P-06** | Python-Referenzpfad: Validierungsaufwand | Konstante Eingaben gegebenenfalls einmal beim Setup validieren, ohne Fehler- und Eingabeverträge zu entfernen. | Python-6-DOF-Schritt mit synthetischem Kraftstub: **150,078 → 126,887 µs/Schritt** Median (**-15,45 %**); Spannweiten überlappen nicht. | Belegter Gewinn in diesem begrenzten Python-Referenz-Workload; kein Produktions-Workergewinn daraus ableitbar. | Wiederholte Positivdefinitheitsprüfung wird für identische numerische Trägheitstensorwerte begrenzt gecacht; geänderte Werte werden erneut validiert. [P-06-Messbeleg](./Messungen/messung_p06_python_schritt_validation_v0.13.json). | Keine Erweiterung ohne Produktionsprofil; Fehlervertrag bei geänderten Werten bleibt getestet. |
| **P-07** | Python-Referenzpfad: Kraft-/Wrench-Objektkette | Interne Ergebnisobjekte und wiederholte Kopien reduzieren, ohne äußere APIs oder Ergebniswerte zu ändern. | Folkeboot-Aggregation mit drei Beiträgen: **95,745 µs/Aufruf** Median; keine alternative Kopierstrategie verglichen. | Möglicherweise relevant bei kleinen Modellen im Python-Pfad; kein belegter Gewinn im C++-Produktionspfad. | Nicht verändert: die Baseline allein quantifiziert keine eliminierbaren Kopien; Umgehen der Frame-/Wrenchvalidierung wäre nicht sicher. [P-07-Messbeleg](./Messungen/messung_p07_python_wrench_kette_v0.13.json). | Keine Änderung ohne Profilbeleg und vertragstreuen Alternativpfad. |
| **P-08** | Python-Referenzpfad: Hydrodynamik-Temporärdaten | Erneute Normalenmasken und temporäre Arrays im Python-Hydrodynamikpfad prüfen. | Folkeboot Python-Referenz: **387,833 → 375,610 µs** Median (-3,15 %); Laufspannweiten überlappen. | Kleiner möglicher Hebel nur im Python-Referenzpfad; Verbesserung nicht eindeutig über der Streuung belegt. | Unveränderliche Maske gültiger Normalen wird bei Geometrievorbereitung berechnet und wiederverwendet. Gezielter Test prüft Maskengleichheit/Unveränderlichkeit; Messdaten im [P-08-Messbeleg](./Messungen/messung_p08_python_normalenmaske_v0.13.json). | Keine weitere Optimierung ohne belastbaren Profilbeleg; bestehenden Referenz-/Paritätstest erhalten. |

## Ergänzende Ansätze aus der Recherche

Diese Ansätze wurden gegen die aktuellen nativen C++-Pfade geprüft. Die
extern publizierten Beschleunigungsfaktoren sind nicht auf dieses Projekt
übertragbar; sie begründen nur, warum ein passender, begrenzter Versuch
interessant sein könnte.

| Temp-ID | Name | Kurzbeschreibung | Aktuelle Messzeit | Optimierungspotenzial | Umsetzungsstand | Priorität für weitere Prüfung |
|---|---|---|---|---|---|---|
| **P-09** | Wiederverwendbare Arbeitsbereiche in den nativen Hotloops | In `EbenenSchnitt::auswerten` werden pro Aufruf Abstände und mehrere Volumen-/Moment-Akkumulatoren aufgebaut; `hydrodynamik_beitraege` legt pro Teil wiederholt dynamische Vektoren an. Arbeitsbereiche/kapazitäten task- oder kontextlokal wiederverwenden und unnötige Zuweisungen vermeiden. | Vorhandener Worker-Batch: **1,639 ms** Median; isolierte Hydrostatik-Auswertung vor Änderung: Folkeboot **26,796 µs** Median. Nach dem Umbau Batch-Recheck: **22,250 / 17,220 / 15,516 / 15,377 µs/Schritt** bei Batch 1/4/16/64; alte Eingabepose nicht vollständig dokumentiert, daher kein direkter Vorher-/Nachhervergleich. | Speicherbereiche werden im Batch wiederverwendet; isolierter Hydrostatik-Laufzeitgewinn und Allokationsanteil nicht belegt. | **Teilweise umgesetzt:** vorhandene Hydrodynamik-Arbeitsvektoren bleiben; Hydrostatik-Abstände und Volumen/Moment-Akkumulatoren werden über einen batchlokalen Scratch-Arbeitsbereich wiederverwendet. Native Geometrie-/Batchtests bestanden; der bekannte Optimist-Paritätsfehler bleibt. [P-09/P-10-Messbeleg](./Messungen/messung_p09_p10_native_hydrostatik_v0.13.json). | Änderung erhalten; keine zusätzliche Performancebehauptung ohne exakt passende Vorhermessung. |
| **P-10** | Hierarchischer exakter Ebenenschnitt mit aggregierten Momenten | Forschungsansatz: unveränderliche Meshbereiche hierarchisch gruppieren, je Knoten Begrenzungen und voraggregierte signierte Volumen-/Momentbeiträge speichern. Liegt eine Schnittebene vollständig auf einer Seite des Knotens, könnte ein vollständig enthaltener Bereich aggregiert und ein vollständig äußerer Bereich übersprungen werden; nur schneidende Bereiche würden Dreieck für Dreieck ausgewertet. | Exakte native Hydrostatik-Baseline: Folkeboot **26,796 µs/Aufruf** Median bei fünf festen Posen; kein Hierarchie-Prototyp verglichen. | Möglicher Hebel bei großen Meshes, aber hoher Validierungsaufwand und Rundungsrisiko durch geänderte Summationsreihenfolge. Keine Verbesserung belegt. | Nicht umgesetzt/aktiviert; der Bestandsalgorithmus bleibt produktiv, da weder unabhängiger exakter Gleichheitsnachweis noch Prototypvergleich vorliegt. [P-09/P-10-Messbeleg](./Messungen/messung_p09_p10_native_hydrostatik_v0.13.json). | Exakten Bestand erhalten; Hierarchie erst nach Profilbeleg und belastbarem numerischem Fehlerbudget erneut erwägen. |
| **P-11** | Compiler-gestützte Vektorisierung und Profiloptimierung | Für die nativen Schleifen über Vertices/Dreiecke Vektorisierungsberichte auswerten; Datenlayout und Schleifen nur dort anpassen, wo der Compiler und ein repräsentatives Profil konkretes Potenzial zeigen. Release-Build-Profiloptimierung kann ebenfalls verglichen werden. | Keine projektspezifische Vektorisierungs- oder PGO-Messung dokumentiert. | **Niedrig bis mittel, breit nutzbar**, aber compiler-/hardwareabhängig. Keine pauschalen SIMD-Annahmen oder „fast math“/Genauigkeitslockerungen. | Nicht umgesetzt; keine projektspezifischen Vektorisierungs- oder PGO-Belege. | Rang 4 – erst bei konkretem Hotloop-Profil und reproduzierbarem Build-Szenario. |
| **P-12** | VTK-PlaneCutter als GUI-Alternative prüfen | `vtkPlaneCutter` ist ein paralleler, für wiederholte Ebenenschnitte ausgelegter Filter mit möglicher Vorverarbeitung/Spatial-Index. Allenfalls gegen den GUI-Wasserlinienschnitt vergleichen; nicht als Ersatz für die Hydrostatik-Volumen-/Schwerpunktberechnung einsetzen. Eingabetyp, Kontur-/Deckelverträge und Kaltstartkosten zuerst prüfen. | Nicht gemessen; die vorhandenen Pose-/Renderwerte sind **4,447 / 24,920 ms** und isolieren den Schnitt nicht. | **Möglicher GUI-Hebel**, abhängig von VTK-Datentyp, Overhead und Wiederverwendung. Kein belegter Gewinn und keine direkte Änderung des Physikkerns. | Nicht umgesetzt; kein Vergleich oder Gewinnbeleg. | Rang 3 – nur falls P-02 den Schnitt als relevanten Anteil bestätigt; Kaltstart und Ausgabe-Verträge mitmessen. |

### Recherche-Einordnung und Grenzen

- Der Standardpfad ist bereits C++ und verarbeitet mehrere Schritte im
  nativen Batch; die pybind11-Bindung gibt den GIL für die native Berechnung
  frei. Ein allgemeiner Wechsel von Python zu C++ oder bloßes GIL-Freigeben
  ist daher kein neuer Hebel.
- Die VTK-Dokumentation beschreibt `vtkPlaneCutter` als parallelen
  Ebenenschneider, der bei wiederholten Schnitten Vorverarbeitung nutzen kann.
  Das ist für Darstellung interessant, aber die Ausgabe ist keine
  Hydrostatik-Auswertung mit Volumen und Schwerpunkt.
- CGAL 6.1 berichtet für seine neu geschriebene Mesh-Clip-/Split-Funktion
  einen bis zu zehnfachen Gewinn bei den gezeigten Fällen. Diese Funktion
  erzeugt bzw. verfeinert ein geschnittenes Oberflächenmesh; sie ist kein
  drop-in Ersatz für den hier verwendeten Schnitt, der direkt Volumen und
  Schwerpunkt integriert. Außerdem müssen Paketlizenz und Integrationskosten
  vor einer Verwendung geprüft werden.
- Compiler-PGO, Autovektorisierung und VTK-Speedups sind
  workload-, Build- und Hardware-spezifisch. Veröffentliche Zahlen sind
  keine Prognose für den SegelPhysik-Hotpath.

## Bereits gemessene Kandidatenentscheidungen

| Kandidat | Ergebnis aus vorhandener Messreihe | Einordnung |
|---|---|---|
| Marker-Kugelvorlage | Qt-Swap-Intervall-Median **168,298 → 151,201 ms** (rund **10,16 %** niedriger). Simulationsdurchsatz **0,9760 → 0,9769 Simulationssekunden/Wandsekunde** (rund **+0,09 %**). | Bereits umgesetzt und gemessen; kein neuer Kandidat. |
| Marker plus SVG-no-op | Swap-Median rund **4,93 %** niedriger; Laufstreuung überlappt Baseline und mehrere Signale verschlechtern sich. | Nicht übernehmen. |
| SVG-Template-Serializer | Swap-Median rund **6,25 %** langsamer als Baseline. | Verworfen. |

## Nicht Teil dieser Kandidatenliste

- Delta-basierte Hydrostatik-Caches: würden Ergebnisse trotz geänderter Pose
  wiederverwenden und sind daher näherungsbehaftet.
- Voxel-Optimierungen oder Pfadwechsel: kein Standardpfad der aktuellen
  Echtzeitphysik beziehungsweise nicht freigegebene Näherung.
- Doppelte Quaternion-Berechnung: die Rotationen beziehen sich auf
  unterschiedliche Zustände und sind keine bestätigte Redundanz.
- OBJ-Import und Konfigurationsladen: Ladezeitoptimierungen, keine laufende
  Dynamiklast.
- Neue Windsimulation oder neue physikalische Funktionen: außerhalb des
  aktuellen Umfangs.

## Quellen

- [Speed-Analyse V0.12](../zuV0.12/Optimierung/Speed_2_2_2_2_2.md)
- [V0.12-Umsetzungsplan](../zuV0.12/Umsetzungsanleitungen/Umsetzungsplan_V0.12.md)
- [Vorhandene Messdaten](../zuV0.12/Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json)
- [VTK: `vtkPlaneCutter`](https://vtk.org/doc/nightly/html/classvtkPlaneCutter.html)
- [Kitware: VTK/ParaView Filter Performance Improvements](https://www.kitware.com/vtk-paraview-filters-performance-improvements/)
- [CGAL: Improved Surface Mesh Clipping (CGAL 6.1)](https://www.cgal.org/2025/06/06/new_clip/)
- [Microsoft: Profile-guided optimizations](https://learn.microsoft.com/en-us/cpp/build/profile-guided-optimizations?view=msvc-170)
- [Microsoft: Auto-Parallelization and Auto-Vectorization](https://learn.microsoft.com/en-us/cpp/parallel/auto-parallelization-and-auto-vectorization?view=msvc-170)
- [Microsoft: `/Qvec-report`](https://learn.microsoft.com/en-us/cpp/build/reference/qvec-report-auto-vectorizer-reporting-level?view=msvc-170)
- [pybind11: Global Interpreter Lock](https://pybind11.readthedocs.io/en/stable/advanced/misc.html#global-interpreter-lock-gil)
- [CGAL: License](https://doc.cgal.org/latest/Manual/license.html)
