# Vorläufige Optimierungsliste Performance V0.12

**Stand:** 21.10.2026  
**Status:** Arbeitsliste, keine Spezifikation und keine Umsetzungsfreigabe.

Die Reihenfolge schätzt die mögliche Gesamtwirkung als
**Ersparnis je Aufruf × Aufrufhäufigkeit**. Sie ist vorläufig: Für die meisten
Kandidaten gibt es keine isolierte Zeitmessung. Codeanalyse-Schätzungen sind
keine Messwerte und keine zugesicherten Gewinne.

Als vorhandene Referenz dienen die Folkeboot-Messungen mit `exakt_union` und
C++-Rechenpfad: Worker-Batch **1,639 ms**, Worker-Roundtrip **15,259 ms**,
Pose-Aufruf **4,447 ms**, Render-Aufruf **24,920 ms**. Der gemessene
Durchsatz von **0,976 Simulationssekunden/Wandsekunde** bei `dt = 4 ms`
entspricht rechnerisch rund **244 Physikschritten pro Wandsekunde**. Der
16-ms-Echtzeittakt entspricht nominal rund **62,5 Tasks pro Sekunde**.
Diese Raten sind Häufigkeitsanker aus dem Basisszenario, keine Messung der
Aufrufzahl einzelner Kandidaten. Insbesondere sind sie nicht auf den
Python-Referenzpfad übertragbar.

| Vorläufige ID | Name | Beschreibung | Messung | Potential |
|---|---|---|---|---|
| **P-01** | Hierarchischer exakter Ebenenschnitt | Meshbereiche räumlich hierarchisch gliedern; für vollständig ober- oder unterhalb der Ebene liegende Bereiche könnten vorberechnete Volumen-/Momentbeiträge verwendet bzw. Dreiecke übersprungen werden. | Kein Prototyp, keine Einzelzeit. Referenz des gesamten nativen Worker-Batches: **1,639 ms**. Der Schnitt ist im aktuellen dynamischen Physikschritt relevant, aber sein Anteil ist nicht isoliert. | **Sehr hoch, aber spekulativ und aufwendig.** Potenzial je Physikschritt, also häufig (nominal ca. 244 Schritte/Wands). Nur wenn die Ebene wenige Hierarchiebereiche schneidet. Exaktheit und numerische Parität müssen gegen den bestehenden Algorithmus geprüft werden. |
| **P-02** | Snapshot pro Echtzeit-Task | Unveränderte Körper-/Mesh-Snapshots und native Kontextdaten wiederverwenden; Invalidierung für Pose, Gelenke, Meshes und Modelländerungen sicherstellen. | Nicht isoliert gemessen. Speed-Dokument schätzt **1–5 ms pro Task**, ausdrücklich ungemessen. Nominal ca. **62,5 Tasks/s**; rechnerisch wären das **0,063–0,313 s CPU-Zeit je Wandsekunde**, falls die Schätzung zutrifft. | **Hoch, vorläufig.** Häufiger Taskpfad und auffällige geschätzte Kosten. Cachevertrag/Invalidierung ist das zentrale Risiko. |
| **P-03** | Wiederverwendbare native Arbeitsbereiche | Allokationen in `EbenenSchnitt::auswerten` und `hydrodynamik_beitraege` reduzieren; temporäre Vektoren/Akkumulatoren mit ausreichender Lebensdauer und Kapazität wiederverwenden. | Allokationen nicht separat gemessen. Worker-Batch **1,639 ms** umfasst zahlreiche Berechnungen und eignet sich nicht als Allokationszeit. | **Mittel bis hoch, plausibel.** Betroffene Schleifen laufen im nativen Physikpfad wiederholt, nominal bis zu ca. 244 Schritte/Wands. Tatsächliche Kosten müssen gezielt profiliert werden. |
| **P-04** | Compiler-Vektorisierung und Profiloptimierung | Release-Build mit Vektorisierungsberichten untersuchen; Schleifen/Datenlayout nur für nachweislich relevante native Hotspots anpassen. PGO separat mit repräsentativer Last vergleichen. | Keine projektspezifische Vektorisierungs- oder PGO-Messung. | **Mittel, breit wirksam möglich.** Potenziell viele Aufrufe im Physikkern, aber stark von Compiler, Build, Hardware und Datenlayout abhängig. Kein fixer Gewinn ableitbar. |
| **P-05** | Python: Kraft-/Wrench-Objektkette | Interne Objektkonstruktion und Kopien im Python-Referenzpfad reduzieren, äußere API und Ergebnisverträge beibehalten. | Nicht gemessen. Codeanalyse-Schätzung **0,2–0,5 ms pro Schritt**. | **Hoch innerhalb des Python-Referenzpfads**, da pro Schritt; im standardmäßigen C++-Produktionspfad kein direkter Gewinn. Die native Schrittfrequenz darf nicht als Python-Messrate angesetzt werden. |
| **P-06** | Task-Batchgröße und Übergabekosten | Batch-/Taskgröße des bestehenden Workflows anhand gespeicherter Worker- und Roundtrip-Metriken prüfen; Rückstand, Eingabelatenz und Anzeigeaktualität als Gegengates berücksichtigen. | Worker-Batch **1,639 ms**, Roundtrip **15,259 ms**. Keine Vergleichsreihe unterschiedlicher Batchgrößen. Nominal ca. **62,5 Tasks/s**. | **Mittel, unbestimmt.** Wiederkehrend, aber der Anteil vermeidbarer Übergabezeit ist unbekannt; pauschales Vergrößern könnte Latenz und Rückstand verschlechtern. |
| **P-07** | GUI-Wasserlinienschnitt bei unveränderter Pose | Wasserlinienschnitt und zugehörige Geometrie bei unveränderter Pose/Geometrie nicht erneut aufbauen. | Schnitt nicht isoliert. Baseline: Pose-Aufruf **4,447 ms**, Render-Aufruf **24,920 ms**. Die Werte umfassen andere Arbeit. | **Mittel in ruhenden/pausierten Szenen**, im bewegten Echtzeitbetrieb vermutlich geringer. Frequenz und Schnittanteil fehlen. |
| **P-08** | VTK-PlaneCutter für GUI-Schnitte | VTKs parallelen Ebenenschneider allenfalls als Alternative für den GUI-Wasserlinienschnitt vergleichen; nicht als Ersatz für die native Hydrostatik mit Volumen und Schwerpunkt. | Nicht gemessen; dieselben nicht isolierten Pose-/Render-Referenzen wie P-07. Vorverarbeitungs-/Kaltstartkosten ebenfalls unbekannt. | **Bedingt mittel für die GUI.** Nur sinnvoll, wenn Datentyp, Schnitt-/Deckelvertrag und Wiederverwendung passen. Überschneidet sich mit P-07 und ist eine Alternative, kein zusätzlicher sicherer Gewinn. |
| **P-09** | Python: konstante Validierungen aus dem Schrittpfad | Konstante Modell-/Eingabeprüfungen im Python-Referenzpfad gegebenenfalls in eine sichere Setupvalidierung verschieben. Fehlerverhalten erhalten. | Nicht gemessen. Codeanalyse-Schätzung **0,05–0,1 ms pro Schritt**. | **Klein bis mittel im Python-Referenzpfad**, wiederholt pro Schritt; kein direkter Effekt auf den standardmäßigen nativen C++-Pfad. |
| **P-10** | Python: Hydrodynamik-Temporärdaten | Wiederholte Normalenmasken und temporäre Arrays im Python-Hydrodynamikpfad verringern. | Nicht gemessen. Codeanalyse-Schätzung **0,02–0,05 ms pro Schritt**. | **Klein im Python-Referenzpfad**, dafür pro Schritt wiederholt; nicht direkt auf den C++-Pfad übertragbar. |
| **P-11** | Wasser-Splat im Renderpfad | Nur bei nachgewiesenem Frameanteil Kernel-/Offsetarbeit verbessern; berücksichtigen, dass bei vorhandenem Mesh jeder zweite Aufruf übersprungen wird und im nativen Pfad der Splat nativ läuft. | Kein isolierter Zeitwert. | **Bedingt, derzeit niedrig priorisiert.** Die ursprüngliche ca. 3x-Schätzung bezieht sich nur auf den betroffenen Frameabschnitt, nicht auf die Gesamtsimulation. |
| **P-12** | Gelenk-Updates in der GUI | Bei tatsächlicher häufiger Slider-/Gelenkbedienung wiederholte Geometriearbeit reduzieren, ohne Endstellungen oder Bedienverträge zu verlieren. | Ereigniszeit und Ereignishäufigkeit nicht gemessen. | **Niedrig im normalen Lauf, potenziell mittel bei aktiver Bedienung.** Nur anhand einer repräsentativen Interaktionslast bewerten. |

## Bereits bewertete Punkte, keine offenen Kandidaten

- **Marker-Kugelvorlage:** bereits umgesetzt. Vorhandener Swap-Median
  **168,298 → 151,201 ms** (ca. **10,16 %** Verbesserung); Simulationsdurchsatz
  nur ca. **+0,09 %**. Nicht erneut als offene Optimierung führen.
- **Marker plus SVG-no-op:** nicht übernehmen; ca. **4,93 %** niedrigerer
  Swap-Median, aber überlappende Laufstreuung und Verschlechterungen anderer
  Signale.
- **SVG-Template-Serializer:** verworfen; ca. **6,25 %** langsamerer
  Swap-Median.

## Einordnung der Rangfolge

- **P-01** steht zuerst wegen des möglichen Algorithmushebels über häufige
  Physikschritte; die Größe des Gewinns ist völlig ungemessen und das Risiko
  hoch.
- **P-02** folgt wegen häufiger Task-Aufrufe und einer vorhandenen, aber
  unbestätigten Einzelkosten-Schätzung.
- **P-03/P-04** adressieren den laufenden nativen Pfad und könnten viele
  Physikschritte betreffen; ohne Profiling ist ihre Einsparung je Aufruf
  unbekannt.
- **P-05/P-09/P-10** gelten nur für den Python-Referenzpfad. Sie sind aus
  einer V0.12-Liste nicht automatisch auszuschließen, aber kein Ersatz für
  Verbesserungen des C++-Standardpfads.
- **P-07/P-08/P-11/P-12** betreffen bedingte GUI- oder Interaktionslasten,
  nicht die Kosten jedes Physikschritts.

## Vorschlag für die Umsetzungsreihenfolge

Die Reihenfolge unten priorisiert nicht allein den theoretischen Maximalgewinn,
sondern auch Messbarkeit, Eingriffsrisiko und Wiederverwendbarkeit der
vorhandenen Baseline. Sie ist ein Vorschlag, kein freigegebener
Umsetzungsplan.

| Reihenfolge | Kandidat | Vorgehen und Begründung |
|---:|---|---|
| 0 | Vorhandene Baseline und gezieltes Profil | Die vorhandenen Folkeboot-Messungen unverändert als Referenz übernehmen. Keine vollständige Baseline-Messreihe wiederholen. Nur die Messgrenze ergänzen, die zur Trennung von Snapshot-, nativer Physik-, Übergabe- oder GUI-Zeit für den gewählten Kandidaten erforderlich ist. |
| 1 | **P-02 – Snapshot pro Echtzeit-Task** | Snapshot- und native Kontextaufbauzeit zunächst isoliert erfassen. Bei relevantem Anteil Wiederverwendung implementieren und Invalidierung für Pose, Gelenke, Meshes und Modelländerungen absichern. Der erwartete Gewinn pro Task könnte hoch sein; der Cachevertrag ist aber ein Korrektheitsrisiko. |
| 2 | **P-03 – Wiederverwendbare native Arbeitsbereiche** | Nach Profilbefund unnötige Allokationen in den wiederholt ausgeführten nativen Ebenenschnitt- und Hydrodynamikschleifen reduzieren. Das ist ein begrenzter Eingriff ohne geplante Änderung des Physikmodells und kann viele Schritte betreffen. |
| 3 | **P-04 – Compiler-Vektorisierung und Profiloptimierung** | Für den tatsächlich dominierenden nativen Loop Compilerberichte und Release-Build prüfen; erst danach gezielt Datenlayout/Schleifen oder PGO vergleichen. Keine pauschalen Compilerflags, Architekturannahmen oder Genauigkeitslockerungen. |
| 4 | **P-01 – Hierarchischer exakter Ebenenschnitt** | Erst beginnen, wenn Profiling bestätigt, dass die Hydrostatik im nativen Standardpfad einen hinreichend großen Gesamtanteil hat. Zunächst einen begrenzten Prototyp mit vorberechneten Bereichsmomenten gegen den bestehenden exakten Schnitt vergleichen. Wegen Algorithmus-, Rundungs- und Validierungsrisiko separat behandeln. |
| 5 | **P-06 – Task-Batchgröße und Übergabekosten** | Nur variieren, wenn die vorhandenen Worker-/Roundtrip-Messungen einen relevanten Übergabeanteil nahelegen. Kleine, gezielte Vergleichsreihe durchführen und Rückstand, Eingabelatenz sowie Aktualität der Anzeige gemeinsam auswerten. |
| 6 | **P-07 – GUI-Wasserlinienschnitt bei unveränderter Pose** | GUI-Schnitt und Geometrieaufbau im Ruhe- und Bewegungsszenario gezielt instrumentieren. Einen exakten Dirty-Check/Cache nur bei nachgewiesen wiederholter Arbeit umsetzen. |
| 7 | **P-08 – VTK-PlaneCutter als Alternative** | Nur falls P-07 einen relevanten GUI-Schnittanteil belegt. Als alternative Implementierung desselben GUI-Vertrags vergleichen, nicht als zusätzliche Maßnahme oder Ersatz für die Hydrostatik-Volumenberechnung. |
| 8 | **P-11 – Wasser-Splat** | Nur weiterverfolgen, wenn die vorhandenen oder gezielt ergänzten Frameprofile den Splat trotz Skip-Verhalten und nativem Pfad als relevanten Engpass ausweisen. |
| 9 | **P-12 – Gelenk-Updates in der GUI** | Nur bei belegter häufiger Bedienlast und relevanter Ereigniszeit. Bedienverträge und angewendete Endstellung erhalten. |
| optional | **P-05/P-09/P-10 – Python-Referenzpfad** | Nur aufnehmen, falls der Python-Referenzpfad ausdrücklich zum V0.12-Umfang gehört oder dort ein konkret benötigter Workflow gemessen wird. Die Optimierungen wirken nicht unmittelbar auf den C++-Standardpfad. |

Nach jeder angenommenen Änderung folgen zunächst passende Korrektheits- und
Paritätstests, dann eine gezielte Kandidatenmessung mit denselben Eingaben
und Messgrenzen wie die vorhandene Referenz. Ein End-to-End-Lauf wird nur
für Änderungen wiederholt, die den vollständigen Nutzungspfad beeinflussen;
verschachtelte Einzelmessungen werden nicht als additive Einsparungen
interpretiert. Wird ein Kandidat durch Profiling als unbedeutend ausgewiesen,
wird er zurückgestellt statt allein aufgrund einer Codeanalyse-Schätzung
umgesetzt.

Die bestehende Baseline und Rohdaten stehen im
[Speed-Messvergleich](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json).
Die ausführliche Kandidatenbewertung und Recherchequellen stehen in der
[Optimierungskandidatenliste](./Optimierungskandidaten_Performance_V0.12.md).
