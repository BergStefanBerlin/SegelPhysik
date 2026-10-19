# Spezifikation: Echtzeitberechnung und Darstellung als Schulungstool

**Stand:** 19.10.2026  
**Version:** zuV0.9  
**Status:** Anforderungen für Profiling und mögliche Leistungsoptimierungen  
**Zielhardware für die erste Abnahme:** AMD Ryzen 5 8600G, 32 GB RAM,
integrierte Radeon 760M; NPU-Zugriff ist gesondert nachzuweisen.

## Zweck und fachliche Einordnung

SegelPhysik soll in diesem Vorhaben ein interaktives Schulungs- und
Anschauungstool sein. Lernende sollen qualitativ nachvollziehen können, wie
Änderungen an Modell, Beladung, Wind oder Einstellungen die dargestellte
Bewegung und die berechneten Größen beeinflussen. Ein flüssiger, verständlicher
Eindruck und reproduzierbare Vergleichsversuche sind wichtige Ziele.

Die Anwendung ist weder eine Engineering-Simulation noch ein Werkzeug für
Konstruktions-, Sicherheits- oder Zulassungsnachweise und auch kein
Race-Optimizer. Ergebnisse dürfen nicht als belastbare Vorhersage für ein
reales Boot oder als Grundlage für Bau-, Sicherheits- oder Wettkampfentscheidungen
ausgegeben werden. Höhere Rechengeschwindigkeit ist kein Grund, eine
Näherung als genauer oder physikalisch validiert darzustellen.

## Aktive Anforderungen

### A-V0.9-00003 — Reproduzierbares Profil des interaktiven Echtzeitpfads

Vor gezielten Beschleunigungsarbeiten muss der aktuelle Standardfall auf der
Zielhardware reproduzierbar profiliert werden. Der Messlauf muss die
Berechnungszeit mindestens für Hydrostatik/Geometrie, Hydrodynamik,
Integration, Worker-/Prozesskommunikation und Rendering getrennt erfassen.
Er muss außerdem angeforderte und tatsächlich berechnete Simulationszeit,
Physikrückstand, effektive Simulationszeit pro Wandsekunde, Bildrate,
Frameabstände und Eingabelatenz ausweisen.

Der Messbericht hält Modell, Simulationsmodus, Parameter, Python- und
Bibliotheksversionen, Betriebssystem, Hardware, Renderoptionen, Aufwärmphase,
Wiederholungen sowie Median und 95. Perzentil fest. Start, Pause/Fortsetzung
und Wechsel zwischen relevanten Simulationsmodi sind als eigene Abschnitte
oder Messfälle zu erfassen. Ein isolierter Mikrobenchmark ersetzt keinen
End-to-End-Lauf.

**Abnahmekriterien**

- Ein dokumentierter Lauf lässt sich mit denselben Eingaben auf derselben
  Hardware wiederholen.
- Kostenanteile der genannten Bereiche sind getrennt messbar; nicht
  zuordenbare Zeit wird als solche ausgewiesen und nicht stillschweigend einem
  anderen Bereich zugeschlagen.
- Die Auswertung enthält Rohmesswerte und kennzeichnet fehlgeschlagene,
  unterbrochene oder nicht vergleichbare Läufe.

**Herkunft:** `I-BL-000001`

### A-V0.9-00004 — Sichtbare, pädagogisch ausreichende Echtzeitdarstellung

Die Darstellung soll im freigegebenen Schulungs-Standardfall Bewegungen
hinreichend flüssig und ohne irreführende Sprünge zeigen. Physikzeit,
Renderzeit und Anzeigeinterpolation sind getrennt zu behandeln. Eine
Darstellungsoptimierung darf weder Physikzustände verändern noch aus
Darstellungsinterpolation eine zusätzliche physikalische Bewegung ableiten.

Als zunächst vorgeschlagene Abnahmeziele gelten im Standardfall auf der
Zielhardware mindestens 30 angezeigte Bilder pro Sekunde, ein
Frameabstand-P95 von höchstens 67 ms, eine Eingabelatenz-P95 von höchstens
100 ms sowie kein dauerhaft wachsender Physikrückstand bei
Simulationsgeschwindigkeit 1x über einen fünfminütigen Lauf. Werden diese
Ziele trotz vertretbarer
Optimierung nicht erreicht, muss die Anwendung den eingeschränkten
Darstellungs- oder Simulationszustand erkennbar machen. Messwerte dürfen
nicht durch ausgelassene Frames oder Messfenster verborgen werden.

Darstellungsoptionen wie Wasseroptik, Schatten, SSAO und zusätzliche
Overlays dürfen zur Verbesserung der Bedienbarkeit reduziert oder abschaltbar
sein, sofern zentrale Lerninhalte, Körperlage und relevante Anzeigen
verständlich bleiben.

**Abnahmekriterien**

- Die Ziele werden mit dem in A-V0.9-00003 festgelegten Standardfall und
  Messverfahren geprüft.
- Änderungen am Rendering verändern bei identischen Eingaben keine
  Physikergebnisse außerhalb der für den unveränderten Physikpfad bereits
  geltenden numerischen Testtoleranzen.
- Ein Vorher-/Nachher-Vergleich dokumentiert Bildrate, Frameabstände,
  Physikrückstand, Eingabelatenz und die erhaltenen Lerninformationen.

**Herkunft:** `I-BL-000010`

### A-V0.9-00005 — Profilgeführte CPU-Optimierung

CPU-Optimierungen dürfen erst umgesetzt werden, wenn A-V0.9-00003 einen konkreten
relevanten Hotspot belegt. Die Änderung ist auf diesen Hotspot zu begrenzen;
ein Profilbefund rechtfertigt nicht automatisch Änderungen an anderen
Algorithmen oder physikalischen Annahmen. JIT- oder nativer Code ist nur dann
ein Kandidat, wenn der End-to-End-Gewinn den zusätzlichen Installations-,
Kompatibilitäts- und Wartungsaufwand für das Schulungstool rechtfertigt.

**Abnahmekriterien**

- Der optimierte Pfad wird mit dem bisherigen Pfad auf denselben Eingaben
  verglichen; die Änderung bringt einen reproduzierbaren End-to-End-Vorteil
  im interaktiven Standardfall.
- Physikergebnisse bleiben innerhalb der geltenden Toleranzen des
  unveränderten Rechenverfahrens.
- Fehler aus dem optimierten Pfad werden erkennbar gemeldet; ein Fehler darf
  nicht als erfolgreicher oder physikalisch gültiger Ersatzwert erscheinen.
- Installations- und Laufzeitverhalten bleiben für die unterstützte
  Standardumgebung nachvollziehbar.

**Herkunft:** `I-BL-000007`

### A-V0.9-00006 — Gezielte Optimierung des exakten Unionpfads

Der `exakt_union`-Pfad bleibt Referenz für die gegenwärtige
Hydrostatik-/Geometrieberechnung. Optimierungen an Vorbereitungsdaten,
Booleschen Operationen oder Poseauswertung sind nur zulässig, wenn sie durch
A-V0.9-00003 als relevante Kosten belegt wurden. Die Bedeutung des Pfads als
Referenz darf durch eine Optimierung nicht stillschweigend geändert werden.

**Abnahmekriterien**

- Referenzfälle und numerische Toleranzen werden vor dem Kandidatenlauf
  festgehalten und für Ausgangs- und optimierten Pfad identisch verwendet.
- Geometrische, hydrostatische und aggregierte Ergebnisse bestehen die
  vorhandenen Referenz- und Regressionstests.
- Zusätzlich ist ein messbarer End-to-End-Gewinn im Standardfall
  nachgewiesen; reine Mikrobenchmark-Gewinne reichen nicht.
- Abweichungen und Fehlerzustände werden ausgewiesen. Ein Näherungsverfahren
  gilt nicht allein durch ähnliche Laufzeit als Optimierung dieses exakten
  Pfads.

**Herkunft:** `I-BL-000002`

### A-V0.9-00007 — Sichere Wiederverwendung von Hydrostatikergebnissen

Hydrostatikergebnisse dürfen wiederverwendet werden, wenn ihre Gültigkeit für
die aktuelle Pose, Geometrie, Wasserlage und sonstigen Eingaben eindeutig
feststeht. Cache- oder Invalidierungslogik muss Änderungen aller
ergebnisrelevanten Eingaben berücksichtigen. Der bestehende exakte
Einzelschritt bleibt verfügbar und dient als Vergleichsreferenz.

Ein reduziertes Berechnungsintervall oder eine andere näherungsbehaftete
Wiederverwendung ist eine eigene Schulungsnäherung und keine exakte
Cache-Optimierung. Sie darf nur in einem entsprechend gekennzeichneten Modus
eingesetzt werden, nachdem ihre Auswirkungen auf die jeweiligen Lernziele
gemessen und nach A-V0.9-00009 freigegeben wurden. Der Standardmodus darf nicht
unbemerkt auf eine solche Näherung wechseln.

**Abnahmekriterien**

- Tests belegen, dass Änderungen jeder ergebnisrelevanten Eingabe den Cache
  korrekt invalidieren oder einen nachweislich gültigen Eintrag verwenden.
- Exakte Wiederverwendung ergibt dieselben Resultate innerhalb der
  bestehenden Toleranzen.
- Für näherungsbehaftete Wiederverwendung werden Vergleichsfälle,
  Lernzielbezug und vorab festgelegte Fehlergrenzen gemäß A-V0.9-00009
  dokumentiert.
- Cachetreffer, Neuberechnungen und gemessener End-to-End-Nutzen sind
  nachvollziehbar.

**Herkunft:** `I-BL-000003`

### A-V0.9-00008 — NPU-Machbarkeit auf dem Ryzen 5 8600G

Die Zielhardware umfasst laut Nutzerangabe einen AMD Ryzen 5 8600G mit
Radeon 760M. Eine NPU oder ein geeigneter Softwarepfad darf für dieses Projekt
nicht allein aus der Prozessorbezeichnung abgeleitet werden: verfügbare
Hardware, Treiber, Betriebssystem, Laufzeit und unterstützte Operatoren sind
zur Laufzeit oder in der Entwicklungsumgebung nachzuweisen. Die integrierte
Radeon-GPU ist von der NPU getrennt zu bewerten.

Zunächst ist ausschließlich eine begrenzte Machbarkeitsprüfung vorgesehen.
Ein NPU-Kernel darf nur benchmarked werden, wenn A-V0.9-00003 einen ausreichend
großen und für die verfügbaren Operatoren geeigneten Tensor-/Vektorteilpfad
belegt. Boolesche Mesh-Union oder beliebige NumPy-Geometrieoperationen sind
nicht ohne Nachweis als NPU-geeignet anzunehmen.

**Abnahmekriterien**

- Inventar dokumentiert, ob die NPU tatsächlich verfügbar ist, welche
  Laufzeit sie unterstützt und ob diese mit der Projektumgebung nutzbar ist.
- Ein geeigneter Kernel wird gegen einen CPU-Referenzlauf mit denselben
  Eingaben, Genauigkeitsgrenzen und Warm-up-/Wiederholungsbedingungen
  benchmarked. Transfer-, Start- und Synchronisationskosten werden
  mitgemessen.
- Eine produktive NPU-Nutzung wird nur vorgeschlagen, wenn sie einen
  reproduzierbaren End-to-End-Vorteil für den Schulungs-Standardfall bringt
  und die Genauigkeits- sowie Robustheitskriterien erfüllt.
- Bei fehlender Laufzeit oder fehlendem geeigneten Kernel wird dies als
  Ergebnis der Machbarkeitsprüfung dokumentiert; die CPU-Ausführung bleibt
  der unterstützte Pfad. Eine NPU-Abhängigkeit ist nicht Voraussetzung für
  die Nutzung des Programms.

**Herkunft:** `I-BL-000006`

### A-V0.9-00009 — Genauigkeit, Näherungskennzeichnung und Lernzielbezug

**Freigegebene Genauigkeitsgrundlage:** Der Nutzer hat am 19.10.2026 die
[Grenzwertvorlage Fassung 1](../Umsetzungsplan/Genauigkeitsvorschlaege_v0.9.md)
vollständig freigegeben. Diese Grenzen einschließlich qualitativer Kriterien
und Gültigkeitsbedingungen dürfen bis zum Abschluss v0.9 nicht gelockert
werden, auch nicht auf späteren Wunsch des Nutzers. Scheitert ein Kandidat,
ist er zu verbessern oder nicht freizugeben; ein fehlgeschlagener Test darf
nicht durch geänderte Akzeptanzgrenzen zum Erfolg erklärt werden.

Genauigkeit ist für dieses Schulungstool in zwei getrennten Fragen zu
bewerten:

1. **Numerische Übereinstimmung einer Implementierungsoptimierung:** Wenn
   Algorithmus und physikalische Annahmen gleich bleiben, darf eine
   Optimierung die bestehenden numerischen Toleranzen nicht pauschal
   lockern. Referenzpfad, Testfälle und Toleranzen werden vor dem Vergleich
   festgehalten.
2. **Pädagogische Eignung eines vereinfachten Modells oder Verfahrens:** Eine
   Näherung kann zulässig sein, wenn sie für ein ausdrücklich benanntes
   Lernziel genügt. Es gibt dafür keine pauschale Prozentgrenze für alle
   Größen und Szenarien. Die zulässige Abweichung ist vor der Umsetzung für
   jede betroffene Messgröße zu begründen und festzulegen; sie muss
   relevante qualitative Zusammenhänge, Vorzeichen und Größenordnungen des
   Lernziels erhalten. Grenz-, Wechsel- und repräsentative Standardfälle
   sind einzubeziehen.

Die technische Rechengenauigkeit ist nicht mit der physikalischen Güte des
Modells gegenüber einem realen Boot gleichzusetzen. Ein mathematisch
wiederholbares Ergebnis eines geschätzten Modells kann physikalisch ungenau
sein. Modelle und Verfahrensoptionen mit nicht verifizierter Geometrie,
Masse oder Kalibrierung müssen diese Einschränkung bei Auswahl und Ergebnis
erkennbar machen. Quantitative Ausgaben werden mit Einheiten und
Modell-/Verfahrenshinweis dargestellt, wo die Oberfläche dies unterstützt.

**Abnahmekriterien**

- Für jeden näherungsbehafteten Pfad stehen Lernziel, betroffene Größen,
  Referenz, vorab genehmigte absolute und/oder relative Grenzen, Testfälle
  und bekannte Einschränkungen vor der Implementierung fest.
- Die Grenzwerte werden anhand der Lerninhalte und der Empfindlichkeit der
  betreffenden Größe gewählt, nicht nachträglich so erweitert, dass ein
  fehlgeschlagener Kandidat besteht.
- Eine Näherung, fehlende Kalibrierung oder nicht validierte Modellannahme
  wird dem Nutzer klar als solche angezeigt; ihre Ergebnisse werden nicht
  als Engineering- oder Race-Optimizer-Aussagen präsentiert.
- Bei Überschreitung einer Grenze wird der Kandidat nicht stillschweigend
  freigegeben. Es ist entweder die Näherung anzupassen, der betroffene
  Lernumfang einzuschränken oder die Option nicht umzusetzen.

## Empfohlene Reihenfolge

1. A-V0.9-00003: reproduzierbare, komponentengetrennte Baseline erstellen.
2. A-V0.9-00004: Renderengpass und Darstellungsoptionen bewerten.
3. A-V0.9-00005 und A-V0.9-00006: nur den durch das Profil belegten CPU- bzw.
   `exakt_union`-Hotspot optimieren.
4. A-V0.9-00007: exakte Wiederverwendung zuerst prüfen; Näherungsintervalle nur
   mit gesonderter pädagogischer Genauigkeitsfreigabe.
5. A-V0.9-00008: NPU-Inventar frühzeitig, Kernelbenchmark nur bei passendem
   Profilbefund.
6. A-V0.9-00009 gilt als gemeinsames Freigabegate für alle Kandidaten, die
   numerische Ergebnisse verändern oder Näherungen einführen.

Die Schritte legen keine produktive Umstellung vor Bestehen der jeweiligen
Mess-, Genauigkeits-, Robustheits- und Bedienbarkeitsnachweise fest.

## Herkunft und bewusst nicht übernommene Ideen

Die aktiven Anforderungen verwenden ausschließlich die versionsbezogenen
Kennungen `A-V0.9-…` gemäß Nummerierungs-Anweisung. Die neuen Anforderungen
beginnen nach den bestehenden Kennungen `A-V0.9-00001` und `A-V0.9-00002`
mit `A-V0.9-00003`. Die `I-BL-…`-Kennungen bleiben unverändert als
Herkunftsverweise im Backlog erhalten.

| Backlog-Idee | Spezifikationspunkt | Entscheidung |
|---|---|---|
| `I-BL-000001` | A-V0.9-00003 | Übernommen: Profiling als Voraussetzung |
| `I-BL-000002` | A-V0.9-00006 | Übernommen: gezielte Optimierung des exakten Pfads |
| `I-BL-000003` | A-V0.9-00007 | Übernommen: Wiederverwendung mit exakter/näherungsweiser Trennung |
| `I-BL-000006` | A-V0.9-00008 | Übernommen: NPU-Machbarkeitsprüfung |
| `I-BL-000007` | A-V0.9-00005 | Übernommen: Profilgeführte CPU-Optimierung |
| `I-BL-000010` | A-V0.9-00004 | Übernommen: Darstellung und Bedienbarkeit |
| `I-BL-000004`, `I-BL-000005` | — | Nicht Teil dieses Vorhabens: Voxel- und GPU-Hydrostatik haben bestehende Genauigkeits-/Freigaberisiken und werden nicht als kurzfristige Optimierung eingeplant. |
| `I-BL-000008`, `I-BL-000009` | — | Nicht Teil dieses Vorhabens: Parallelisierung sowie adaptive/größere Zeitschritte erfordern höheren Umbau- und Validierungsaufwand und ändern die numerische bzw. physikalische Ausführung stärker. |

Die nicht übernommenen Ideen sind keine verworfenen Spezifikationspunkte:
Sie behalten ihre `I-BL-…`-Kennungen und ihren Status im Backlog.

## Historische Zuordnung der fehlerhaften Vorfassung

Die folgende `SpecNNNN`-Schreibweise wurde in einer früheren Fassung
irrtümlich als aktive Anforderungskennung verwendet. Sie ist nicht das
gültige Schema und darf in neuen Verweisen nicht verwendet werden. Die
aktiven Anforderungen tragen ausschließlich die jeweils zugeordnete
`A-V0.9-…`-Kennung.

| Fehlerhafte Kennung aus der Vorfassung | Gültige aktive Kennung |
|---|---|
| `Spec0116` | `A-V0.9-00003` |
| `Spec0117` | `A-V0.9-00004` |
| `Spec0118` | `A-V0.9-00005` |
| `Spec0119` | `A-V0.9-00006` |
| `Spec0120` | `A-V0.9-00007` |
| `Spec0121` | `A-V0.9-00008` |
| `Spec0122` | `A-V0.9-00009` |
