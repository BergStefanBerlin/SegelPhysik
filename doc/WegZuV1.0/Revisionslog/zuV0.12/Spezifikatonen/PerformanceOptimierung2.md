# Spezifikation PerformanceOptimierung2 – zuV0.12

**Stand:** 21.10.2026  
**Status:** Umgesetzt und gezielt geprüft; Nachher-Messungen dokumentiert.  
**Geltung:** Diese Spezifikation konkretisiert und ersetzt für die drei unten
genannten Kandidaten widersprechende Auswahl- und Vorprofiling-Vorgaben der
[Speed-Spezifikation V0.12](./Spezifikation_Speed_V0.12.md). Deren
Korrektheits-, Mess- und Regressionsregeln gelten weiter, soweit diese Datei
sie nicht ausdrücklich konkretisiert. Die P-IDs beziehen sich ausschließlich
auf die [Optimierungskandidaten Performance V0.12](../Optimierung/Optimierungskandidaten_Performance_V0.12.md).

## 1. Ziel und Grenzen

Diese Spezifikation beschreibt die gezielte Optimierung von drei
ausgewählten, bereits vorhandenen Funktionen. Es wurden keine Vorabtests,
Vorab-Benchmarks, Profiling-Läufe oder erneuten Baseline-Läufe ausgeführt.
Die Änderungen wurden aktiviert, danach gezielt geprüft und gemessen. Die
vorhandenen Messdaten blieben unverändert.

Neue Physik, Näherungsverfahren, eine Änderung des fachlichen Ergebnisses,
eine Lockerung von Genauigkeitstoleranzen und Änderungen an nicht genannten
Kandidaten sind ausgeschlossen. Insbesondere darf die Optimierung keinen
exakten Schnitt durch einen approximativen Cache ersetzen.

## 2. Aktive Anforderungen

| Kennung | Kandidat | Anforderung und Abnahmekriterium |
|---|---|---|
| **A-V0.12-00020** | Umfang und Ablauf | Ausschließlich P-01, P-05 und P-02 aus Abschnitt 3 umsetzen. Keine Vorabtests, Profiling-Läufe oder erneuten Baseline-Läufe. Vorhandene Messdaten bleiben unverändert; gezielte Prüfungen und Nachmessungen erfolgen erst nach Aktivierung der jeweiligen Änderung. |
| **A-V0.12-00021** | P-01 – Snapshot pro Echtzeit-Task | Unveränderte Körper-/Mesh-Snapshots dürfen im Echtzeitpfad wiederverwendet werden. Ein Cachetreffer ist nur bei identischem vollständigem Modellzustand zulässig. Pose-, Gelenk-, Mesh- und Modelländerungen müssen den Cache zuverlässig invalidieren. Eigentum, Unveränderlichkeit, Lebensdauer und Thread-Sicherheit der geteilten Daten bleiben korrekt; ein veralteter Snapshot darf keinen Task erreichen. Das unveränderte Modell muss fachlich identische Ergebnisse wie eine frische Snapshot-Erzeugung liefern. |
| **A-V0.12-00022** | P-05 – Gelenk-Updates in der GUI | Wiederholte Geometriearbeit während einer zusammenhängenden Slider-Interaktion ist zu reduzieren. Wird die Darstellung während des Ziehens zusammengefasst, muss der zuletzt angeforderte Gelenkwinkel zuverlässig übernommen und nach Ende der Interaktion dargestellt werden. Bedienvertrag, Endstellung, Gelenkkinematik, Geometrie und physikalische Ergebnisse bleiben unverändert; Eingaben dürfen nicht dauerhaft verloren gehen oder die GUI blockieren. |
| **A-V0.12-00023** | P-02 – Wasserlinienschnitt bei unveränderter Pose | Schnitt- und Anzeigegeometrie dürfen bei vollständig unverändertem Körperzustand, Pose und Wasserstand wiederverwendet werden. Änderungen an Pose, Gelenken, Mesh/Modell, Wasserstand oder anderen schnittrelevanten Eingaben müssen eine Neuberechnung auslösen. Die Geometrie muss im bewegten Fall aktuell bleiben und mit dem bisherigen exakten Schnitt übereinstimmen. Die Optimierung gilt nur für den GUI-Pfad, nicht für Hydrostatik- oder Physikergebnisse. |
| **A-V0.12-00024** | Korrektheit und Regressionen | Nach den Änderungen müssen vorhandene, passende gezielte Tests sowie erforderliche unabhängige Referenz- und Invalidierungsprüfungen bestehen. Bestehende numerische und GUI-Verträge bleiben erhalten. Eine Performance-Regression außerhalb der Messunsicherheit in einem Pflichtszenario schließt eine vorbehaltlose Abnahme aus. |
| **A-V0.12-00025** | Nachmessung und Ergebnisdarstellung | Nach Aktivierung wird jeder Kandidat mit einer gezielten, reproduzierbaren Messung ausgewertet. Für jeden Punkt werden Messgrenze, Szenario, Referenz, Nachherwert, Stichproben-/Streuungsinformation und Veränderung ausgewiesen. Eine Verbesserung wird nur behauptet, wenn Messwerte vergleichbar und außerhalb der Messunsicherheit unterscheidbar sind; andernfalls ist der Befund als unklar oder nicht quantifizierbar zu kennzeichnen. |

## 3. Ausgewählte Kandidaten und Messwerte

Die Reihenfolge entspricht der priorisierten Liste des Auftrags. Referenzwerte
unten stammen aus den bestehenden Folkeboot-Messungen mit `exakt_union`,
C++-Rechenpfad, 640 × 480 Viewport, 10 s Warm-up und 45 s Messzeit. Sie
isolieren die Kandidaten nicht und sind daher nur Kontext, keine gemessenen
Einzelkosten.

| Priorität | Kandidat | Vorhandener Referenzwert (Median) | Nach Aktivierung gezielt erfassen |
|---:|---|---|---|
| 1 | **P-01 – Snapshot pro Echtzeit-Task** | Worker-Batch **1,639 ms**, Worker-Roundtrip **15,259 ms**, Durchsatz **0,976 Simulationssekunden/Wandsekunde**, maximaler Rückstand **1,177 s**. Keine Snapshot-Einzelzeit oder Cache-Trefferrate vorhanden. | Frische Snapshot-Erzeugungszeit und Wiederverwendungszeit getrennt; Treffer-/Fehlerrate; Zeit für Task und Worker-Batch/Roundtrip; Durchsatz und maximaler Rückstand. Ergebnis der Snapshot-Zeit nur als isolierten Pfadwert ausweisen; Worker-/Durchsatzänderungen separat als End-to-End-Signal einordnen. |
| 2 | **P-05 – Gelenk-Updates in der GUI** | Render-Aufruf **24,920 ms**, Pose-Aufruf **4,447 ms**, `frameSwapped`-Intervall **168,298 ms**, Eingabe-bis-Swap **91,579 ms**. Keine Messung einer Slider-Sequenz oder Geometriearbeit je Gelenkereignis vorhanden. | Für eine festgelegte, reproduzierbare Slider-Sequenz: Anzahl Eingabeereignisse und tatsächlicher Geometrieaktualisierungen, Zeit je Geometrieaktualisierung, Eingabe-bis-dargestellte-Endstellung sowie Endwinkelabweichung. Frame-/Eingabelatenz als separates GUI-Gegengate berichten. |
| 3 | **P-02 – Wasserlinienschnitt bei unveränderter Pose** | Pose-Aufruf **4,447 ms**, Render-Aufruf **24,920 ms**, `frameSwapped`-Intervall **168,298 ms**. Keiner dieser Werte isoliert den Wasserlinienschnitt. | Zeit und Zahl der Schnitte/Geometrieaufbauten in einer ruhenden Szene; entsprechender Aktualisierungsaufwand bei bewegter Pose; Frameintervall und sichtbare Aktualisierungslatenz. Cachetreffer dürfen den bewegten Pfad nicht veralten lassen. |

Die Referenz- und Rohdaten stehen in der
[Speed-Messreihe vom 21.10.2026](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json).
Vorhandene Messreihen werden nicht erneut ausgeführt oder ergänzt. Da die
historischen Referenzen keine isolierten Gelenk- oder Wasserlinienschnitt-
Werte enthalten und keine Snapshot-Einzelzeit erfassen, dürfen diese Werte
nicht nachträglich als solche interpretiert werden. Ein isolierter
Vorher-/Nachher-Gewinn ist für eine Metrik ohne vergleichbare Bestandsmessung
als **nicht quantifizierbar** auszuweisen; der tatsächlich gemessene
Nachherwert und die verbleibende Nachweislücke sind trotzdem pro Kandidat
darzustellen.

## 4. Mess- und Abnahmeregeln nach Aktivierung

1. Keine Messung vor der Umsetzung oder Aktivierung. Änderungen, Buildstand
   und aktivierte Funktion sind vor dem Messlauf zu dokumentieren.
2. Die bisherige Referenzreihe bleibt unverändert. Neue Messungen beschränken
   sich auf die in Abschnitt 3 genannten bislang nicht erhobenen
   Kandidatenfragen; vollständige Baseline-Läufe werden nicht wiederholt.
3. Für jede neu erhobene Variante sind Szenario, Modell, Rechenpfad,
   Hardware/Build, Messgrenze, Warm-up, Rohdaten und mindestens fünf
   Messläufe mit Median und Streuung zu dokumentieren. Ruhende und bewegte
   GUI-Szenarien sind getrennt zu halten. Keine konkurrierende Test- oder
   Benchmarklast darf die Messungen beeinflussen.
4. Je Kandidat werden gemessener Nachherwert und belastbar vergleichbarer
   Referenzwert nebeneinander ausgewiesen. Prozentuale Veränderung:
   `(Referenz − Nachher) / Referenz × 100` für Zeit-/Latenzwerte;
   `(Nachher − Referenz) / Referenz × 100` für Durchsatz. Zusätzlich sind
   absolute Differenz und Messunsicherheit anzugeben. Cachetrefferquote oder
   vermiedene Geometrieaufbauten sind ergänzende Arbeitsmetriken, kein
   Ersatz für End-to-End-Werte.
5. Ein Ergebnis innerhalb der Streuung/Messunsicherheit ist **unklar**, nicht
   „verbessert“. Ein fehlender vergleichbarer Vorherwert ist **nicht
   quantifizierbar**. Es gibt keinen prozentualen Mindestgewinn.
6. Nach Abschluss ist für alle drei Punkte eine Ergebnistabelle mit
   Messwerten, Differenz, Prozentwert (falls zulässig), Streuung und
   Bewertung zu ergänzen. Nicht gemessene Werte bleiben als solche markiert;
   Schätzungen dürfen nicht als erreichte Verbesserung erscheinen.

## 5. Ergebnisprotokoll

**Umsetzung:** P-01 verwendet einen pro Körper geschützten nativen
Snapshot-Kontext und teilt unveränderliche Geometriearrays zwischen
Snapshots; Pose bleibt pro Task aktuell und Änderungen an Mesh oder Gelenk
invalidieren den Kontext. P-05 fasst Gelenk-Geometrieupdates pro GUI-
Zeitfenster zusammen und rendert nach dem Flush. P-02 speichert die exakte
Schnitt- und Anzeigegeometrie anhand der vollständigen Punkt- und
Dreiecksarrays. Geänderte Eingaben durchlaufen weiterhin den bisherigen
exakten Schnitt. Die gezielten Regressionstests befinden sich in
[test_performance_optimierung2.py](../../../../../tests/test_performance_optimierung2.py).

Die Rohwerte und Laufbedingungen liegen in der
[Nachmessung PerformanceOptimierung2 V0.12](../Messungen/PerformanceOptimierung2_V0.12_2026-10-21.json).
Die Snapshot- und Wasserlinienschnitt-Nachmessungen liefen nach Aktivierung
am Folkeboot-Modell `yacht1`. Die Gelenk-Eventsequenz nutzte einen
synthetischen Körper mit einem echten Modellgelenk; Geometrie- und Renderarbeit
wurden dabei gemockt. Alle Messungen liefen mit C++-Rechenpfad, Python 3.14.8,
Windows 11, 640 × 480 und ohne konkurrierende Last. Je Arbeitslast wurde ein
ungemessener Warm-up und danach fünf Messläufe durchgeführt. GUI-
Mikroarbeitslasten liefen offscreen; dort wurden Geometrieaktualisierung bzw.
Renderanforderung gemessen, nicht der physische Monitor-Scanout.

| Kandidat | Vergleich und Messgrenze | Nachher-Median (Bereich der fünf Laufwerte) | Veränderung | Befund |
|---|---|---:|---:|---|
| **P-01 Snapshot pro Echtzeit-Task** | Wiederverwendeter nativer Snapshot gegen gleichstandigen Frischaufbau-Kontrollpfad; pro Snapshot. Historische Worker-/Durchsatzwerte bleiben unverändert und werden durch fünf vollständige Nachherläufe ergänzt. | Cachetreffer **0,147759 ms** (**0,146276–0,148104**); Frischaufbau plus Snapshot **0,700382 ms** (**0,640938–0,761018**). Cachetreffer **100 %** in den Messschleifen. | **−78,90 %** gegenüber dem gleichstandigen Frischaufbau-Kontrollpfad. | Isolierter, belastbarer Vorteil gegenüber dem absichtlich neu aufgebauten Kontext; kein historischer isolierter Snapshot-Vorherwert. Vollständige GUI-/Worker-Nachherwerte siehe unten; kein End-to-End-Gewinn belegt. |
| **P-05 Gelenk-Updates in der GUI** | Reproduzierbarer Burst mit 500 Gelenkereignissen an einem synthetischen Körper mit echtem Modellgelenk; Anzahl Geometrieaktualisierungen, Burstzeit und Qt-Timer bis zur Renderanforderung. Geometrie- und Renderarbeit für die Zeitmessung gemockt. | Burst-Eingabe **3,138 ms** (**2,548–8,696**); Eingabe bis gebündelter Renderanforderung **16,524 ms** (**10,117–16,809**); **1** Geometrieaktualisierung je 500 Ereignisse in allen fünf Läufen; Endwinkelabweichung **0 rad**. | Geometrieaktualisierungen **−99,8 %** innerhalb des Bursts. | Coalescing und Übernahme der letzten Eingabe belegt. Kein vergleichbarer historischer Slider-Lauf und kein echtes `frameSwapped`/Display-Latenzmaß; GUI-End-to-End-Gewinn nicht quantifizierbar. |
| **P-02 Wasserlinienschnitt bei unveränderter Pose** | Cachetreffer bei unveränderter Weltgeometrie gegen gleichstandigen Cache-Miss; zusätzliche Kontrollmessung mit geändertem Pose-Input. Zeiten pro Schnitt/Anzeigedatensatz. | Unverändert **0,006702 ms** (**0,006399–0,007189**); Cache-Miss **0,696550 ms** (**0,691157–0,722473**); bewegte Pose **0,729123 ms** (**0,712940–0,754283**). | Unverändert **−99,04 %** gegenüber dem gleichstandigen Cache-Miss-Kontrollpfad. | Ruhender Cachetreffer ist deutlich günstiger; geänderte Pose löst weiterhin Neuberechnung aus. Kein historischer isolierter Vorherwert; vollständiger GUI-End-to-End-Gewinn nicht belegt. |

Die Prozentwerte vergleichen jeweils Nachher-Messungen mit dem
gleichstandigen Kontrollpfad derselben Revision, nicht mit einer alten
Vorhermessung. Deshalb belegen sie den Aufwand des Cachetreffers relativ zum
Frischaufbau bzw. Cache-Miss, aber keinen historischen End-to-End-Gewinn.
Die bisherigen GUI-/Worker-Messreihen wurden nicht wiederholt.

Zusätzlich wurden auf dem endgültigen Quellstand fünf gültige
Live-GUI-Kandidatenläufe mit je 10 s Warm-up und 45 s Messzeit ausgeführt.
Die Mediane der fünf Laufmediane waren: `frameSwapped`-Intervall
**175,123 ms** (Bereich **171,478–184,484 ms**), Eingabe-bis-Swap
**96,777 ms** (**92,259–103,009 ms**), Render-Aufruf **23,517 ms**
(**23,002–24,136 ms**), Worker-Batch **7,723 ms** (**7,622–7,946 ms**),
Worker-Roundtrip **16,580 ms** (**15,871–18,324 ms**), Durchsatz
**0,975630 Simulationssekunden/Wandsekunde** (**0,975472–0,976031**) und
maximaler Rückstand **1,201 s** (**1,138–1,217 s**). Die gespeicherten
Einzelberichte sind in der
[Nachmessung](../Messungen/PerformanceOptimierung2_V0.12_2026-10-21.json)
verlinkt. Die Bestandsreferenzwerte zeigen überlappende Bereiche bei
Frameintervall, Durchsatz und Rückstand, aber gemischte Signale in anderen
Metriken. Die historische Rohreihe enthält keinen exakten Hash des damaligen
Arbeitsbaums; der aktuelle Arbeitsbaum hatte bereits vor diesen Änderungen
andere uncommittete Quelländerungen. Daher lässt sich aus diesem
End-to-End-Vergleich weder eine Regression noch ein Gewinn kausal den drei
Optimierungen zuschreiben. Insbesondere wird die isolierte Einsparung nicht
als Verbesserung des vollständigen Simulations-Workflows ausgegeben.

**Gezielte Korrektheitsprüfung:** `69 passed` mit
`tests/test_performance_optimierung2.py`, `tests/test_native_backend.py`,
`tests/test_native_worker.py`, `tests/test_gui_worker_referenz.py`,
`tests/test_koerper.py` und `tests/test_grafik_geometrie_referenz.py`.
Abgedeckt sind Snapshot-Wiederverwendung bei Poseänderung,
Snapshot-Invalidierung bei Mesh- und Gelenkänderung, exakter
Wasserlinienschnitt mit Wiederverwendung nur für gleiche Geometrie sowie
Zusammenfassung der Slider-Ereignisse mit unveränderter Endstellung.
