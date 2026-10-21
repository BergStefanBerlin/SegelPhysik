# Optimierungskandidaten Performance V0.12

**Stand:** 21.10.2026  
**Zweck:** Kandidaten für eine mögliche V0.12-Spezifikation. Dies ist keine
Spezifikation und erteilt keine Umsetzungsfreigabe.

Die vorhandene Messreihe bleibt die Baseline; vollständige Baseline-Läufe
sollen nicht wiederholt werden. Die folgenden Messwerte stammen aus dem
Folkeboot-Szenario mit `exakt_union` und C++-Rechenpfad. Wo kein Einzelwert
vorliegt, ist der Kandidat nicht isoliert gemessen. Prozent- und
Millisekundenschätzungen aus der Codeanalyse sind Hypothesen, keine
nachgewiesenen Gewinne.

## Kandidaten für bereits implementierte Funktionen

| Temp-ID | Name | Kurzbeschreibung | Aktuelle Messzeit (Median) | Optimierungspotenzial |
|---|---|---|---|---|
| **P-01** | Snapshot pro Echtzeit-Task | Prüfen, ob Körper-/Mesh-Snapshots bei unverändertem Modell wiederverwendet werden können. Cache-Invalidierung muss Änderungen an Meshes, Gelenken und Pose erkennen. | Snapshot nicht einzeln gemessen. Baseline: Worker-Batch **1,639 ms**, Worker-Roundtrip **15,259 ms**. Diese Werte enthalten mehr als den Snapshot. | Potenziell mittel bis hoch, aber nicht belegt. Die Schätzung von **1–5 ms pro Task** im Speed-Dokument ist ungemessen. |
| **P-02** | Wasserlinienschnitt bei unveränderter Pose | Im GUI-Framepfad Schnitt und Geometrie nur bei geänderter Pose oder Geometrie neu berechnen. | Nicht isoliert gemessen. Baseline: Pose-Aufruf **4,447 ms**, Render-Aufruf **24,920 ms**. Der Schnittanteil ist unbekannt. | Potenziell mittel in ruhenden/pausierten Szenen; ungemessene Codeanalyse-Hypothese. |
| **P-03** | Task-Batchgröße und Übergabekosten | Vorhandene Schrittbündelung anhand vorhandener Worker-/Roundtrip-Metriken prüfen, ohne Rückstand, Eingabelatenz oder Anzeigeaktualität zu verschlechtern. | Worker-Batch **1,639 ms**, Roundtrip **15,259 ms**. Keine systematische Messreihe mehrerer Batchgrößen vorhanden. | Unbekannt, aber relevant für den C++-Echtzeitpfad. Batchgröße nicht pauschal erhöhen. |
| **P-04** | Wasser-Splat im Renderpfad | Nur weiter untersuchen, wenn Messungen den Splat als relevanten Frameanteil ausweisen. Mesh-abhängiges Überspringen jedes zweiten Aufrufs und nativen C++-Pfad berücksichtigen. | Nicht isoliert gemessen. | Bedingt und derzeit nachrangig. Die Schätzung von etwa 3x gilt nur für diesen Frameabschnitt und ist nicht gemessen. |
| **P-05** | Gelenk-Updates in der GUI | Bei häufigen Slider-Ereignissen wiederholte Geometriearbeit untersuchen; Endstellung und Bedienvertrag müssen erhalten bleiben. | Zeit pro Ereignis nicht gemessen. | Bedingt durch Nutzung und gemessene Ereigniskosten. |
| **P-06** | Python-Referenzpfad: Validierungsaufwand | Konstante Eingaben gegebenenfalls einmal beim Setup validieren, ohne Fehler- und Eingabeverträge zu entfernen. | Nicht isoliert gemessen. Die Schätzung von **0,05–0,1 ms pro Schritt** ist unbestätigt. | Klein bis mittel und nur für den Python-Referenzpfad; der Standardpfad rechnet nativ. |
| **P-07** | Python-Referenzpfad: Kraft-/Wrench-Objektkette | Interne Ergebnisobjekte und wiederholte Kopien reduzieren, ohne äußere APIs oder Ergebniswerte zu ändern. | Nicht isoliert gemessen. Die Schätzung von **0,2–0,5 ms pro Schritt** ist unbestätigt. | Möglicherweise relevant bei kleinen Modellen im Python-Pfad; größerer Eingriff, kein belegter Gewinn im C++-Produktionspfad. |
| **P-08** | Python-Referenzpfad: Hydrodynamik-Temporärdaten | Erneute Normalenmasken und temporäre Arrays im Python-Hydrodynamikpfad prüfen. | Nicht isoliert gemessen. Die Schätzung von **0,02–0,05 ms pro Schritt** ist unbestätigt. | Eher klein und nur für den Python-Referenzpfad relevant. |

## Ergänzende Ansätze aus der Recherche

Diese Ansätze wurden gegen die aktuellen nativen C++-Pfade geprüft. Die
extern publizierten Beschleunigungsfaktoren sind nicht auf dieses Projekt
übertragbar; sie begründen nur, warum ein passender, begrenzter Versuch
interessant sein könnte.

| Temp-ID | Name | Kurzbeschreibung | Aktuelle Messzeit | Optimierungspotenzial |
|---|---|---|---|---|
| **P-09** | Wiederverwendbare Arbeitsbereiche in den nativen Hotloops | In `EbenenSchnitt::auswerten` werden pro Aufruf Abstände und mehrere Volumen-/Moment-Akkumulatoren aufgebaut; `hydrodynamik_beitraege` legt pro Teil wiederholt dynamische Vektoren an. Arbeitsbereiche/kapazitäten task- oder kontextlokal wiederverwenden und unnötige Zuweisungen vermeiden. | Keine isolierte Messung dieser Allokationen. Vorhandener Worker-Batch: **1,639 ms** Median; kein Anteil daraus ist den Allokationen zugeordnet. | **Plausibler mittlerer Hebel**, besonders bei vielen Schritten und Dreiecken. Geringeres Risiko als ein Algorithmuswechsel, aber nur durch Profiling und gezielte Messung belegen. |
| **P-10** | Hierarchischer exakter Ebenenschnitt mit aggregierten Momenten | Forschungsansatz: unveränderliche Meshbereiche hierarchisch gruppieren, je Knoten Begrenzungen und voraggregierte signierte Volumen-/Momentbeiträge speichern. Liegt eine Schnittebene vollständig auf einer Seite des Knotens, könnte ein vollständig enthaltener Bereich aggregiert und ein vollständig äußerer Bereich übersprungen werden; nur schneidende Bereiche würden Dreieck für Dreieck ausgewertet. | Nicht implementiert oder gemessen. Referenzwert für den gesamten Worker-Batch: **1,639 ms** Median; kein Hydrostatik-Einzelwert vorhanden. | **Potenziell hoher Algorithmushebel bei großen Meshes**, falls wenige Bereiche die Ebene schneiden. Hoher Implementierungs- und Validierungsaufwand; Ergebnis muss gegen die vorhandene exakte Methode auf Volumen, Schwerpunkt, Kraft und Moment geprüft werden. Andere Summationsreihenfolge kann kleine Rundungsabweichungen erzeugen. |
| **P-11** | Compiler-gestützte Vektorisierung und Profiloptimierung | Für die nativen Schleifen über Vertices/Dreiecke Vektorisierungsberichte auswerten; Datenlayout und Schleifen nur dort anpassen, wo der Compiler und ein repräsentatives Profil konkretes Potenzial zeigen. Release-Build-Profiloptimierung kann ebenfalls verglichen werden. | Keine projektspezifische Vektorisierungs- oder PGO-Messung dokumentiert. | **Niedrig bis mittel, breit nutzbar**, aber compiler-/hardwareabhängig. Keine pauschalen SIMD-Annahmen oder „fast math“/Genauigkeitslockerungen. |
| **P-12** | VTK-PlaneCutter als GUI-Alternative prüfen | `vtkPlaneCutter` ist ein paralleler, für wiederholte Ebenenschnitte ausgelegter Filter mit möglicher Vorverarbeitung/Spatial-Index. Allenfalls gegen den GUI-Wasserlinienschnitt vergleichen; nicht als Ersatz für die Hydrostatik-Volumen-/Schwerpunktberechnung einsetzen. Eingabetyp, Kontur-/Deckelverträge und Kaltstartkosten zuerst prüfen. | Nicht gemessen; die vorhandenen Pose-/Renderwerte sind **4,447 / 24,920 ms** und isolieren den Schnitt nicht. | **Möglicher GUI-Hebel**, abhängig von VTK-Datentyp, Overhead und Wiederverwendung. Kein belegter Gewinn und keine direkte Änderung des Physikkerns. |

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

- [Speed-Analyse V0.12](./Speed_2_2_2_2_2.md)
- [Vorhandene Messdaten](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json)
- [VTK: `vtkPlaneCutter`](https://vtk.org/doc/nightly/html/classvtkPlaneCutter.html)
- [Kitware: VTK/ParaView Filter Performance Improvements](https://www.kitware.com/vtk-paraview-filters-performance-improvements/)
- [CGAL: Improved Surface Mesh Clipping (CGAL 6.1)](https://www.cgal.org/2025/06/06/new_clip/)
- [Microsoft: Profile-guided optimizations](https://learn.microsoft.com/en-us/cpp/build/profile-guided-optimizations?view=msvc-170)
- [Microsoft: Auto-Parallelization and Auto-Vectorization](https://learn.microsoft.com/en-us/cpp/parallel/auto-parallelization-and-auto-vectorization?view=msvc-170)
- [Microsoft: `/Qvec-report`](https://learn.microsoft.com/en-us/cpp/build/reference/qvec-report-auto-vectorizer-reporting-level?view=msvc-170)
- [pybind11: Global Interpreter Lock](https://pybind11.readthedocs.io/en/stable/advanced/misc.html#global-interpreter-lock-gil)
- [CGAL: License](https://doc.cgal.org/latest/Manual/license.html)
