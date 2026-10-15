# SegelPhysik – Spezifikation vF1.2

**Status:** Arbeitsgrundlage für die Überarbeitung des
[Umsetzungsplans vF1](./Umsetzungsplan_vF1.md); noch nicht umgesetzt.

**Grundlage:** [Spezifikation vF1.1](./Spezifikation_vF1.1.md),
[Umsetzungsplan vF1](./Umsetzungsplan_vF1.md),
[Umsetzungsplan vF1a](./Umsetzungsplan_vF1a.md), dokumentierte
Performance-Messungen und die nachfolgenden Nutzerentscheidungen.

**Ziel:** Eine für den Nutzer flüssige, bedienbare Echtzeitsimulation mit
konservativem Genauigkeitsverlust. Die Physik soll mit der Wandzeit Schritt
halten; Beschleunigungen durch Geometrieausschluss, vorberechnete Daten,
CPU-Vektorisierung und geeignete GPU-Kernel haben Vorrang vor einer
unbelegten Verringerung der Modellgenauigkeit.

Diese Fassung präzisiert und erweitert die Performance- und Echtzeitanforderungen
der vF1.1/vF1a. Sie ändert die bestehenden Umsetzungspläne nicht automatisch.
Vor der nächsten Planumsetzung ist der Plan mit dieser Spezifikation
abzugleichen. Anforderungen aus vF1.1, die hier nicht ausdrücklich geändert
werden, bleiben bestehen. Bei einem Widerspruch zu einer ausdrücklich
geänderten Performanceanforderung ist vF1.2 maßgeblich, sobald sie als
Arbeitsgrundlage freigegeben wurde.

## 1. Verbindliche Leitplanken

- Die bestehende GUI-Darstellung und Bedienung bleibt erhalten:
  Fensteraufbau, Docks, Beschriftungen, Farben, Kamera- und
  Hintergrundauswahl, Layer, Körperbaum, Simulationsmodi und Zeittasten
  werden nicht ohne gesonderte Nutzerentscheidung umgestaltet.
- Längere Physikberechnungen dürfen die GUI-Ereignisschleife nicht blockieren.
  Darstellung und Physikzustand werden über eine threadsichere bzw.
  ereignisbasierte Schnittstelle entkoppelt.
- Der Physikkern rechnet in SI-Einheiten. Die Wasserlinie liegt im
  Weltkoordinatensystem bei `z = 0`; z zeigt nach oben.
- Gültige Volumengeometrie und eine konsistente Behandlung von Überlappungen
  sind Voraussetzung jeder Hydrostatikoptimierung. Eine Beschleunigung darf
  weder verdrängtes Volumen doppelt zählen noch relevante Geometrie
  ausschließen.
- Exakte Mesh-/Unionpfade und analytische Testfälle bleiben als
  nachvollziehbare Referenz erhalten. Ein schnellerer Pfad wird erst dann
  freigegeben, wenn seine Genauigkeit und Laufzeit gemessen sind.
- Ungültige, nicht endliche oder fehlgeschlagene Ergebnisse werden explizit
  gemeldet. Fallbacks dürfen keinen Erfolg vortäuschen.
- Nutzerdateien, Modellquellen und Konfigurationsdateien dürfen durch
  Benchmarks und Tests nicht unbeabsichtigt verändert werden.

## 2. Leistungsziel und Messgrößen

### 2.1 Interaktive Zielwerte

Unter der in Abschnitt 9 definierten repräsentativen Last gelten folgende
Ziele:

| Messgröße | Freigabeziel | Messweise |
|---|---:|---|
| Bildrate | Freigabegate: mindestens 30 FPS; Zielwert 60 FPS | tatsächlich präsentierte Frames; Messung mit repräsentativen sichtbaren Layern |
| Eingabereaktion | Freigabegate: p95 höchstens 100 ms | Eingabe bis zur sichtbaren Reaktion, nicht nur Qt-Event-Dispatch |
| Physikdurchsatz | Freigabegate: mindestens 1,0 Simulationssekunde je Wandsekunde im stationären Betrieb | Fortschritt des Physikzeitstempels über Dauerlast |
| Physikrückstand | Freigabegate: p95 höchstens 100 ms und Rückstandszunahme höchstens 50 ms je Fünf-Minuten-Trendfenster gemäß Abschnitt 9.3 | Differenz aus angeforderter und berechneter Simulationszeit |
| Durchsatzreserve | mindestens 1,25 Simulationssekunden je Wandsekunde, solange ein Rückstand abgearbeitet wird | Freigabegate für den Rückstandsabbau; im rückstandsfreien stationären Betrieb bleibt mindestens 1,0x das Gate |

30 FPS allein belegen keine Echtzeitphysik. Bildrate, Eingabelatenz,
Physikdurchsatz, Rückstand und Rechenzeit sind getrennt auszuweisen. Ein
einzelner langsamer Schritt ist nicht automatisch ein Fehler, sofern die
GUI bedienbar bleibt und der Rückstand im stationären Betrieb nicht wächst.
Zielwerte sind auf der Zielhardware nachzuweisen; Abweichungen sind mit
Ursache und Auswirkung offenzulegen, nicht durch veränderte Messbedingungen
zu verdecken.

### 2.2 Simulationszeit und Überlast

- Der Integrator verwendet einen festen, konfigurierten SI-Zeitschritt.
  Für den aktuellen Echtzeitpfad ist der bestehende Wert `dt = 0,004 s`
  beizubehalten, bis eine gesonderte numerische Prüfung eine Änderung
  begründet.
- Wandzeit legt fest, wie viele vollständige Schritte fällig sind; sie darf
  den Integrationsschritt nicht ersetzen oder variabel machen.
- Aufgelaufene Simulationszeit darf nicht still verworfen, übersprungen oder
  durch einen größeren Physikschritt kaschiert werden. Der berechnete
  Simulationszeitstempel muss der tatsächlich integrierten Zeit entsprechen.
- Bei vorübergehender Überlast darf die Anzeige den letzten berechneten
  Zustand interpolieren, sofern Interpolation nur die Darstellung betrifft
  und keine Physikresultate vortäuscht. Der Rückstand bleibt messbar.
- Überlast wird als anhaltend behandelt, wenn der Rückstand mindestens
  `1,0 s` beträgt und diese Schwelle mindestens `5 s` ununterbrochen
  erreicht oder überschritten bleibt. Gleichheit zählt: bei genau `1,0 s`
  beginnt die Fünf-Sekunden-Frist. Dann wird die Echtzeitsimulation automatisch
  pausiert; die GUI bleibt bedienbar, der Pausengrund und der Rückstand werden
  in vorhandenen Statusflächen bzw. im Protokoll gemeldet.
- Die automatische Pausierung verwirft oder überspringt keine Simulationszeit.
  Der noch nicht berechnete Rückstand bleibt erhalten. Während der Pause wird
  keine weitere Simulationszeit angefordert. Beim Fortsetzen wird der
  Rückstand mit dem festen Zeitschritt und mindestens `1,25x` Durchsatz
  abgearbeitet, bis der Rückstand wieder höchstens `100 ms` beträgt. Ein
  ausdrückliches Zurücksetzen oder Verwerfen des Rückstands ist nicht Teil
  dieser Spezifikation. Die Nachholrate wird als integrierte
  Simulationssekunden pro Wandsekunde gemessen. Sobald der Rückstand höchstens
  `100 ms` beträgt, wechselt die Simulation zurück in den normalen
  Echtzeitbetrieb mit `1,0x` angeforderter Simulationszeit pro Wandsekunde.
  Sie wird über vollständige, aufeinanderfolgende Ein-Sekunden-Fenster und
  zusätzlich aggregiert vom Fortsetzen bis zum Erreichen der Rückstandsschwelle
  ausgewiesen. Liegt der Rückstand beim Fortsetzen bereits bei höchstens
  `100 ms`, beginnt unmittelbar der Normalbetrieb; eine Nachholrate wird für
  diesen Fall nicht behauptet. Wird die Rate unterschritten, ist das Gate
  nicht bestanden; der Rückstand wird dennoch ohne Zeitverwerfung mit dem
  maximal verfügbaren Durchsatz weiter abgearbeitet.

## 3. Genauigkeit und Referenzverhalten

- Für den freigegebenen interaktiven Rechenpfad gelten gegenüber der exakten
  Union-Referenz weiterhin die vF1a-Zielgrenzen:
  - verdrängtes Gesamtvolumen: höchstens `1 %` relative Abweichung;
  - Gleichgewichts-Krängungswinkel: höchstens `1°` absolute Abweichung;
  - übrige physikalische Ergebnisgrößen: höchstens `1 %` relative Abweichung.
- Für Referenzwerte nahe null müssen vor dem Benchmark dimensionsgerechte
  absolute Grenzwerte festgelegt und dokumentiert werden. Ein Prozentwert
  allein ist dort nicht ausreichend. Für jede Messgröße wird vor dem Lauf
  eine charakteristische Skala `S` aus dem Referenzfall festgehalten; bei
  Zeitverläufen ist `S` das Maximum des Absolutwerts der Referenzgröße über
  den vorab festgelegten Messzeitraum. Ist dieses Maximum null oder fachlich
  ungeeignet, muss vor dem Lauf eine begründete dimensionsgerechte Skala
  festgelegt werden. Der normierte Fehler eines Wertes lautet
  `e = abs(test - referenz) / max(abs(referenz), S)`. `S` und die daraus
  folgende absolute Toleranz `0,01 * S` sind zu dokumentieren und dürfen nach
  Sichtung der Ergebnisse nicht nachträglich angepasst werden.
- Skalare werden mit dem absoluten Skalarfehler verglichen. Vektoren werden
  mit der euklidischen Norm ihres Fehlervektors und einer dimensionsgleichen
  Referenzskala verglichen; einzelne Komponenten dürfen nicht durch
  Vorzeichenwechsel oder Mittelung verdeckt werden. Winkel werden mit dem
  kleinsten gewrappten Winkelabstand verglichen. Für 3D-Orientierungen aus
  normierten Quaternionen ist der Fehlerwinkel
  `2 * acos(clamp(abs(dot(q_test, q_ref)), 0, 1))`; die Quaternionen werden
  vor dem Vergleich normiert und `q`/`-q` gelten als dieselbe Orientierung.
- Genauigkeitsgates gelten für vollständige Ergebnisse, nicht nur einzelne
  Hydrostatikaufrufe. Zu prüfen sind mindestens Gleichgewichtslage,
  Auftriebsschwerpunkt, Kräfte, Momente und repräsentative dynamische
  Zeitverläufe. Dynamische Verläufe werden bei gleichen Simulationszeitpunkten
  verglichen; für jede vorab festgelegte Zustands- und Kraftgröße müssen
  sowohl der maximale normierte Fehler `max(e)` als auch der RMS-Fehler
  `sqrt(mean(e^2))` höchstens `1 %` betragen. Winkel und 3D-Orientierungen
  werden über die oben definierten Winkelabstände geprüft und dürfen maximal
  `1°` abweichen. Für Größen nahe null gilt die oben definierte Skala `S`.
- Die Zielgrenzen sind Freigabeobergrenzen, kein Soll zur Ausschöpfung der
  Abweichung. Wenn höhere Leistung ohne zusätzlichen Fehler erreichbar ist,
  ist die genauere Variante vorzuziehen.
- Exakte Referenzpfade dürfen optimiert werden, müssen aber gegenüber
  analytischen Geometrien und dem bisherigen Referenzverhalten verifiziert
  bleiben. Ein Näherungspfad darf die Referenz nicht ersetzen.
- Voxelauflösung, Kennfeldauflösung, Interpolation und arithmetische
  Genauigkeit sind zusammen zu bewerten. Eine gröbere Auflösung ist nur
  zulässig, wenn alle Genauigkeitsgates für sämtliche Pflichtfälle bestehen.

## 4. Geometrische Ausschlüsse und Broad-Phase

### 4.1 Sicherheitsprinzip

- Ausschlüsse sind konservativ: Sie dürfen zusätzliche Arbeit zulassen, aber
  niemals Geometrie ausschließen, die zur tatsächlich nassen Geometrie
  gehört.
- Jede Näherungsgrenze berücksichtigt numerische Toleranzen. Bei uneindeutiger
  Lage wird der Kandidat weitergereicht und genauer geprüft.
- Für einen Punktabstand `d` zur Wasserfläche wird eine dokumentierte
  konservative Sicherheitsbreite `delta = max(delta_abs, delta_rel * L,
  delta_num)` verwendet. `L` ist die Diagonale der Körper-AABB; `delta_abs`
  berücksichtigt Modell-/Meshgenauigkeit und `delta_num` die
  Koordinatentransformation sowie Backend-/Gleitkommatoleranzen. `delta_abs`,
  `delta_rel` und `delta_num` werden pro Rechenpfad festgelegt und mit
  Grenztests validiert. Mit vorzeichenbehafteten Wasserflächendistanzen darf
  ein Objekt nur als trocken klassifiziert werden, wenn die Untergrenze
  seiner Bounds größer als `+delta` ist; vollständig eingetaucht nur, wenn
  die Obergrenze kleiner als `-delta` ist. Überlappende oder grenznahe Bounds
  bleiben Kandidaten.
- Broad-Phase-Ergebnisse sind Kandidatenmengen, keine Ersatzentscheidung für
  exakte Schnitt-, Überlappungs- oder Volumenberechnung.

### 4.2 Zulässige Ausschlüsse

- Ein Körper oder validiertes, unabhängiges Teil darf vollständig als trocken
  klassifiziert werden, wenn eine konservative Welt-Höhenuntergrenze strikt
  oberhalb der Wasserfläche einschließlich Sicherheitsabstand liegt.
- Ein Körper oder Teil darf vollständig als eingetaucht klassifiziert werden,
  wenn seine konservative Welt-Höhenobergrenze strikt unterhalb der
  Wasserfläche einschließlich Sicherheitsabstand liegt. Dann dürfen
  vorberechnete Gesamtvolumen- und Schwerpunktdaten verwendet werden.
- Die Bounds eines gedrehten Körpers müssen alle möglichen Extrema
  einschließen, etwa durch Transformation aller AABB-Ecken oder eine
  nachweislich konservative Supportfunktion. Eine nur am Schwerpunkt
  ausgewertete Höhe ist nicht ausreichend.
- Für Mesh-/Union-Schnitte dürfen räumliche Bäume, Bounding-Volumes und
  Wasserlinienabstände Dreiecke, Zellen oder Teilgeometrien ausschließen,
  deren konservative Bounds sicher vollständig trocken oder vollständig
  eingetaucht sind.
- In einem Raster dürfen vollständig nasse oder trockene Säulen ohne
  Einzelprüfung aller Voxel ausgewertet werden. Grenzsäulen werden mit der
  vollständigen Klassifikationsregel geprüft.
- Für viele Körper darf eine Broad-Phase Kandidaten mit sicherem Abstand
  zur Ebene früh klassifizieren. Kandidaten nahe der Wasserlinie verbleiben
  in der Narrow-Phase.

### 4.3 Überlappungen und zusammengesetzte Körper

- Einzelteile dürfen nur dann unabhängig addiert werden, wenn ihre
  Disjunktheit oder eine unionskonsistente Volumenbehandlung sichergestellt
  ist.
- Bei überlappenden Körperteilen muss die Verdrängung weiterhin der äußeren
  Union entsprechen. Das bloße Weglassen eines vollständig nassen/trockenen
  Teils darf weder Überlappungsvolumen doppelt zählen noch ein anderes
  Teilvolumen fälschlich entfernen.
- Geometrische Konfliktkorrekturen und Änderungen an Quellmodellen bleiben
  den Regeln der vF1.1 unterworfen; Performanceoptimierung ist keine
  Erlaubnis, Rohmodelle automatisch zu ändern.

## 5. Körperfestes Raster und schnelle CPU-Auswertung

- Starre Geometrie wird bei Modell-/Auflösungsänderung einmalig in einem
  körperfesten Raster oder einer gleichwertigen vorbereiteten Struktur
  repräsentiert. Eine Poseauswertung erzeugt dieses Raster nicht erneut.
- Der schnelle 6-DOF-Pfad muss beliebige Translationen und normierte
  Quaternionorientierungen unterstützen. Für ein lokales Voxelzentrum `p`
  gilt bei Rotation `R` und Translation `t`:
  `z_welt = e_z · (R p + t) = (R^T e_z) · p + t_z`.
  Die nasse/trockene Klassifikation folgt derselben Wasserflächenkonvention
  wie der Referenzpfad.
- Voxelklassifikation muss ohne Python-Schleife über jedes einzelne Voxel
  implementiert werden; Vektorisierung, kompakte Datenlayouts oder ein
  Kernel sind zulässig.
- Als Optimierung dürfen Voxel zu Säulen/Zeilen mit konstanten zwei lokalen
  Koordinaten gruppiert werden. Vorberechnete sortierte Achsenwerte und
  Präfixsummen für Volumen- und Schwerpunktbeiträge können die Auswertung
  auf Randbereiche der Säulen reduzieren.
- Säulenalgorithmen müssen beliebige 6-DOF-Orientierungen abdecken. Ein
  gewählter Säulenvektor mit nahezu null Wasserhöhengradient ist als
  Sonderfall zu behandeln: andere Achse/Struktur wählen oder auf eine
  geprüfte vektorisierte Auswertung zurückfallen. Keine Division durch
  nahezu null und keine unvollständige Klassifikation.
- Präfixsummen müssen alle für den Volumenschwerpunkt erforderlichen
  gewichteten Koordinaten enthalten. Summationsreihenfolge darf numerisch
  abweichen, muss aber die Ergebnis- und GPU/CPU-Gates erfüllen.
- Das körperfeste Raster ist zunächst eine Näherung gegenüber der exakten
  Union. Es darf erst als interaktiver Produktionspfad gelten, wenn
  Abschnitt 3 für alle Pflichtfälle einschließlich Gleichgewichtslösung
  bestanden ist.
- Vorbereitete Geometrie- und Summendaten werden wiederverwendet und nur
  nach Modell-, Geometrie- oder Auflösungsänderung neu aufgebaut. Aufbauzeit
  und Speicherbedarf werden getrennt von der Poseauswertung gemessen.

## 6. Exakte Hydrostatik und Solveroptimierungen

- Der exakte Unionpfad bleibt Referenz. Eine Poseauswertung soll nach
  Möglichkeit die Wasserfläche in den Körperframe transformieren statt die
  vollständige Union für jede Pose zu transformieren.
- Für `x_welt = R x_körper + t` lautet die Wasserflächenbedingung im
  Körperframe `(R^T e_z) · x_körper + t_z <= 0`. Ebenenrichtung, Vorzeichen,
  Abstand und zurücktransformierte Momente sind gegen analytische Fälle zu
  prüfen, bevor diese Optimierung freigegeben wird.
- Exakte Schnitte dürfen konservative Bounds und vorberechnete
  Beschleunigungsstrukturen verwenden. Für jede Geometrieausschließung muss
  nachgewiesen werden, dass sie das Referenzvolumen und -moment nicht
  verändert.
- Der statische Solver darf physikalisch begründete Kraft-/Momenttoleranzen,
  Warmstarts aus benachbarten Posen, analytische oder semianalytische
  Jacobi-Startwerte und Wiederverwendung bereits berechneter Werte verwenden.
- Solver-Toleranzen dürfen nicht kleiner vorgeben, als Rasterstufen,
  Rundungsfehler oder Modellgenauigkeit sinnvoll auflösen können. Sie dürfen
  aber auch keine falsche Konvergenz melden: Restkraft, Restmoment,
  Stabilitätsstatus, Stagnation und Abbruchgrund bleiben explizit.
- Wasserlinienfläche und deren Trägheit dürfen als Ableitungsinformation
  verwendet werden, wenn die Vorzeichen und Gültigkeitsbedingungen anhand
  analytischer Fälle bestätigt sind. Finite Differenzen bleiben als
  Vergleichs-/Fallbackweg verfügbar, bis die Ersatzableitungen verifiziert
  sind.
- Adaptive Hydrostatik-Kennfelder und Interpolation sind zulässige
  Beschleuniger. Sie müssen ihren Gültigkeitsbereich und Fehlergrenzen
  kennen, nachweislich alle Genauigkeitsgates einhalten und außerhalb des
  freigegebenen Bereichs auf einen genaueren Pfad zurückfallen. Kennfelder
  dürfen nicht über unstetige Übergänge hinweg unkontrolliert interpolieren.

## 7. GPU-Nutzung

- GPU-Beschleunigung ist ausdrücklich erwünscht, wenn sie auf der Zielhardware
  einen messbaren Ende-zu-Ende-Vorteil bietet. Kandidaten sind insbesondere
  körperfeste Voxel-/Säulenklassifikation und -reduktion sowie parallele
  wiederholte Hydrostatikberechnungen.
- Eine GPU-Verfügbarkeit oder ein erfolgreicher Bibliotheksimport allein
  belegt keine Physikbeschleunigung. Es muss ein echter Physikkernel mit
  Eingabedaten, Berechnung, Ergebnisrückgabe und Numerikvergleich ausgeführt
  werden.
- Große, poseunabhängige Geometriedaten sollen nach Möglichkeit dauerhaft
  im Gerätespeicher verbleiben. Pro Schritt sind nur Poseparameter und
  kompakte Ergebnisdaten zu übertragen, soweit das Backend dies zuverlässig
  unterstützt. Initialisierung, Vorberechnung, Transfers, Kernelzeit und
  Reduktion sind getrennt sowie als amortisierte Ende-zu-Ende-Zeit zu messen.
- Kernel dürfen CPU und GUI nicht synchron blockieren. Geeignete asynchrone
  Queues, Events und doppelte/gestaffelte Puffer sind zulässig, sofern
  Ergebnisreihenfolge, Speicherlebensdauer und Fehlerbehandlung korrekt
  bleiben.
- Die integrierte GPU konkurriert mit dem Rendering um Rechenzeit und
  gemeinsam genutzten Speicher. Benchmarks müssen daher sowohl isolierte
  Physik als auch gleichzeitige GUI-/Renderlast ausweisen.
- Der Rechenpfad wird anhand reproduzierbarer Entwicklungsbenchmarks
  festgelegt. Ein Wechsel CPU/GPU pro Pose aufgrund kurzfristiger
  Performancewerte ist nicht erforderlich. Verfügbarkeit, Initialisierungs-
  und Ausführungsfehler müssen jedoch behandelt werden: ein fehlerhafter
  GPU-Aufruf wird protokolliert und die betroffene Berechnung auf der CPU
  wiederholt, falls die CPU-Referenz verfügbar ist.
- CPU-only bleibt ein vollständiger, getesteter Betriebsweg. GPU-Abhängigkeiten
  bleiben optional, sofern eine Pflichtinstallation auf allen Zielsystemen
  nicht ausdrücklich entschieden wird.
- GPU und CPU folgen demselben fachlichen Modell und denselben
  SI-Konventionen. Abweichungen der Parallelreduktion sind nur innerhalb der
  Genauigkeitsgates zulässig. Nicht endliche oder unvollständige GPU-Ergebnisse
  gelten als Fehler.
- Das erste Hardware-Abnahmeprofil ist Windows x64 mit AMD Ryzen 5 8600G,
  integrierter AMD Radeon 760M und 32 GB RAM. Andere Geräte dürfen zusätzlich
  geprüft werden; ein Geräteerfolg darf nicht ohne Messung auf andere
  Treiber-/Backendkombinationen verallgemeinert werden.

## 8. Rendering und Physikzustand

- Render-FPS und Physikdurchsatz sind unabhängige Größen. Die Darstellung darf
  zwischen berechneten Zuständen interpolieren, aber keine extrapolierte
  oder interpolierte Pose in den Physikzustand zurückschreiben.
- GUI-Thread, Physikworker und gegebenenfalls GPU-Queue kommunizieren über
  klar definierte, unveränderliche Zustands-Snapshots oder eine gleichwertig
  threadsichere Übergabe.
- Ein veralteter Snapshot darf dargestellt werden, solange sein
  Simulationszeitstempel intern eindeutig dem Snapshot zugeordnet und in
  Messprotokollen auslesbar bleibt. Eine neue sichtbare Zeitstempelanzeige ist
  nicht gefordert. Berechnete Ergebnisse werden in zeitlicher Reihenfolge
  angewendet; verspätete GPU-Ergebnisse dürfen keinen neueren Zustand
  überschreiben.
- Sichtbare Kräfte, Momente, Wasserlinie und Körperpose müssen zum selben
  tatsächlich berechneten Snapshot gehören. Dazwischenliegende reine
  Renderinterpolation ist davon getrennt.
- Die vF1.1-Anforderung, bestehende GUI-Steuerungen und Anordnung zu erhalten,
  bleibt bestehen. Statusmeldungen nutzen vorhandene Flächen/Protokolle,
  sofern keine spätere Nutzerentscheidung zusätzliche Oberfläche zulässt.

## 9. Benchmark- und Testabnahme

### 9.1 Pflichtfälle

- analytische Grundkörper mit vollständigem, teilweisem und keinem
  Eintauchen;
- Körper in aufrechter Lage sowie repräsentative Roll-, Nick- und kombinierte
  6-DOF-Orientierungen;
- zusammengesetztes Produktivmodell einschließlich nachgewiesener
  Überlappungs-/Unionbehandlung;
- Wasserfläche fern von Geometrie, tangentialer Kontakt und nahezu
  verschwindendes verdrängtes Volumen;
- statische Solverlösung und dynamischer Dauerlauf mit repräsentativen
  Anfangszuständen;
- CPU- und, sofern verfügbar, GPU-Ergebnisvergleich mit identischen Eingaben.

### 9.2 Messprotokoll

Die repräsentative interaktive Last besteht mindestens aus dem konfigurierten
Yacht-Produktivmodell, aktivem Echtzeitmodus, sichtbarer 3D-Ansicht und den
für die normale Bedienung aktivierten Layern Schwerpunkt, Achsen, Kräfte und
Momente. Modell, Layer, Simulationsparameter und Kamera bleiben für
CPU-/GPU-Vergleiche identisch. Zusätzlich wird ein isolierter Physiklauf ohne
Rendering als Diagnose ausgewiesen; er ersetzt nicht den interaktiven
Abnahmelauf.

Jeder Leistungsbericht nennt mindestens:

- Hardware, Betriebssystem, Python-, Bibliotheks-, Treiber- und Backendversion;
- Modell, Zahl und Art der Meshteile, Raster-/Kennfeldauflösung sowie
  Genauigkeitseinstellungen;
- kalte Initialisierung und Vorbereitungszeit, Speicherbedarf,
  Host-Gerät-Transfer, Kernel-/Posezeit und Ergebnisreduktion getrennt;
- p50, p95 und Maximum repräsentativer Pose-/Schrittzeiten;
- Bildrate, p95-Eingabereaktion, Physikdurchsatz und Rückstandsverlauf;
- CPU/GPU-Ergebnisabweichung und Ergebnis gegenüber der exakten Referenz;
- Messung unter gleichzeitiger GUI-/Renderlast und einen zehnminütigen
  Dauerlastlauf nach mindestens 30 Sekunden Warm-up. Der Rückstand wird
  während des Laufs mindestens einmal pro Sekunde erfasst; p95 wird über den
  gesamten zehnminütigen Messabschnitt berechnet.

Vorbereitungskosten dürfen nicht aus der Bilanz verschwinden: einmalige
Kosten werden zusätzlich amortisiert über die tatsächlich gemessene Zahl
wiederholter Auswertungen ausgewiesen. Benchmarks müssen dieselbe
Lastkonfiguration und denselben Genauigkeitsfall für alle verglichenen
Rechenpfade verwenden.

### 9.3 Freigabekriterien

- Genauigkeitsgrenzen aus Abschnitt 3 sind für alle Pflichtfälle erfüllt.
- Sämtliche Freigabegates aus Abschnitt 2.1 müssen erfüllt sein. Eine
  dokumentierte Abweichung macht ein nicht erfülltes Gate transparent, ersetzt
  es aber nicht und erlaubt keine Freigabe des interaktiven Rechenpfads.
- Im zehnminütigen Dauerlasttest gelten die Freigabegates aus Abschnitt 2.1.
  Zusätzlich wird der Rückstandstrend über die letzten fünf Minuten
  bestimmt: Der Rückstand wird sekündlich abgetastet und eine lineare
  Regression gegen Wandzeit berechnet; die vorhergesagte Zunahme vom Anfang
  bis zum Ende dieses Fensters darf höchstens `50 ms` betragen. Dieser
  Grenzwert operationalisiert den Ausschluss eines anhaltenden positiven
  Trends; Zunahmen innerhalb dieser Toleranz gelten für dieses Gate als
  bestanden. Ein Auslösen der automatischen Überlastpause während dieses
  Abnahmelaufs gilt als verfehltes Freigabegate, auch wenn der Rückstand
  danach abgebaut wird.
  Der Physikdurchsatz wird sowohl über die gesamte Wandzeit des Messfensters
  als auch während tatsächlich aktiver Nachholung ausgewiesen; Pausenzeiten
  dürfen nicht aus dem stationären Durchsatz herausgerechnet werden.
  Simulationszeit wird nicht still verworfen.
- Ein GPU-Pfad wird nur als freigegeben ausgewiesen, wenn ein tatsächlicher
  Kernel auf der Zielhardware läuft, numerische Gates besteht und unter
  repräsentativer gleichzeitiger Renderlast einen messbaren Vorteil gegenüber
  dem CPU-Pfad bietet. Für jedes vollständige, gleichartige Laufpaar wird
  die relative Verbesserung als `(p95_CPU - p95_GPU) / p95_CPU` berechnet.
  Mindestens zehn Laufpaare werden ausgewertet; Laufpaare, nicht einzelne
  zeitlich benachbarte Schritte, bilden die unabhängigen Stichproben.
  Das 95-%-Konfidenzintervall des Medians der paarweisen Verbesserungen wird
  mit 10.000 gepaarten Perzentil-Bootstrap-Resamples berechnet. Die untere
  Grenze des Intervalls muss mindestens `10 %` betragen. Andernfalls darf
  bis höchstens 30 Laufpaare erweitert werden; bleibt das untere
  Intervallende darunter, ist der Vorteil nicht belegt. Laufreihenfolge
  innerhalb eines Paares wird randomisiert oder alterniert. Die Verbesserung
  darf weder Genauigkeit noch Bildrate oder Eingabereaktion verschlechtern.
  Ist der Vorteil nicht belegt, bleibt CPU der Produktionspfad, bis eine
  weitere Messung eine Änderung rechtfertigt.
- Geometrische Ausschlüsse werden durch Grenz- und Tangentialtests gegen die
  vollständige Referenz geprüft. Kein Pflichtfall darf wegen eines
  Broad-Phase-Fehlers ausgelassen werden.
- Exakte Referenz, CPU-Näherung und GPU-Implementierung werden getrennt
  identifiziert. Backendfehler, Fallbacks und nicht konvergierte Solverläufe
  erscheinen im Bericht als solche.
- Vorher-/Nachher-Diff, gezielte Tests, vollständige Regression und
  GUI-Smoke-Test werden nach dem bestehenden Umsetzungsplan ausgeführt.

## 10. Zulässige Optimierungskandidaten und Reihenfolge

Die Reihenfolge ist eine Abhängigkeitsleitlinie, keine Vorabgarantie für
Gewinn oder Genauigkeit:

| Rang | Kandidat | Nutzen | Voraussetzung/Freigabe |
|---:|---|---|---|
| 1 | Profiler + reproduzierbarer Livebenchmark | zeigt dominierende Kosten und Rückstandswachstum | gleiche Yacht-/GUI-Last, Zeiten getrennt |
| 2 | konservative vollständige Nass-/Trocken-Ausschlüsse und räumliche Broad-Phase | vermeidet unnötige Schnitt- und Rasterarbeit | Grenztests; keine ausgelassene nasse Geometrie |
| 3 | körperfestes 6-DOF-Raster, vektorisierte Klassifikation | spart erneute Meshtransformation und Schnitte | Genauigkeitsgates einschließlich Solver |
| 4 | Säulen-/Präfixsummen und GPU-residente Daten | reduziert wiederholte Arbeit pro Pose | degenerierte Achsenfälle, GPU/CPU- und Referenzvergleich |
| 5 | Ebene im Körperframe für exakte Union | spart Geometrie-Transformation im Referenzpfad | analytische Verifikation von Ebenen- und Momententransformation |
| 6 | Solver-Warmstart, physikalische Ableitungen und toleranzgerechter Abbruch | reduziert nötige Kraftauswertungen | Restfehler-/Stabilitätsstatus bleiben korrekt |
| 7 | adaptives Hydrostatik-Kennfeld | sehr schnelle wiederholte Auswertung | Bereichsgrenzen, Fehlergates und geprüfter Fallback |
| 8 | GPU-Kernel-/Speicherlayoutoptimierung | parallele Auswertung bei großer Arbeitslast | Ende-zu-Ende-Vorteil unter Renderlast |

Optimierungen dürfen in einer anderen Reihenfolge erprobt werden, sofern
Abhängigkeiten und Messbarkeit gewahrt bleiben. Eine globale Rastervergröberung
ohne erneuten Gate-Lauf, Entfernen exakter Referenzpfade, unsichere
Teilvolumenaddition und adaptive Zeitschritte als Ersatz für schnellere
Kraftauswertung sind nicht freigegeben.

## 11. Kompatibilität mit vF1.1 und erforderliche Plananpassung

Die Überarbeitung von Umsetzungsplan vF1 muss insbesondere:

1. die bisherigen Richtwerte „30 FPS/100 ms“ durch die verbindlichen
   Freigabegates und die getrennten Durchsatz-/Rückstandsziele sowie
   Dauerlastmessung aus Abschnitt 2 ersetzen;
2. die automatische Pausierung bei anhaltender Überlast gemäß Abschnitt 2.2
   samt Rückstandsbehandlung, Meldung und Fortsetzungs-/Nachholrate umsetzen;
3. geometrische Ausschlusskriterien samt konservativen Bounds,
   Union-/Überlappungsregeln und Grenztests als konkrete Arbeitsschritte
   aufnehmen;
4. körperfestes Raster und Säulenreduktion für beliebige 6-DOF-Orientierungen
   spezifizieren, statt nur die 3-DOF-Auswertung zu betrachten;
5. den exakten Unionpfad einschließlich Körperframe-Ebene als Referenz und
   Optimierungskandidat beibehalten;
6. GPU-Arbeit nach dem Vorliegen eines repräsentativen CPU-Pfads anhand von
   kompletter Vorbereitung, Transfers, Kernelzeit, numerischer Qualität und
   gleichzeitiger GUI-Last freigeben;
7. den bestehenden Verzicht auf Laufzeit-Leistungswahl beibehalten, aber
   Fehlerfallback und Ausgabe des tatsächlichen Rechenpfads absichern;
8. Kennfelder und Solverbeschleunigungen nur mit eigenen Fehler-,
   Gültigkeitsbereichs- und Robustheitstests zulassen.

Die aktuell bekannten Reibungspunkte, die der Plan explizit auflösen muss,
sind die Abweichung des körperfesten Rasters bei der Gleichgewichtslösung,
die Lücke zwischen flüssiger Bilddarstellung und wachsendem Physikrückstand,
die fehlende 6-DOF-Säulen-/GPU-Auswertung sowie bisher nur prototypische
GPU-Nutzung. Das sind zu prüfende Arbeitspakete, keine bereits gelösten
Eigenschaften.

## 12. Nichtziele und Änderungen nur nach Freigabe

- Keine ungeprüfte Verringerung der Genauigkeit oder Rasterauflösung.
- Kein stiller Wechsel des Integrationszeitschritts und kein stiller Verlust
  simulierter Zeit.
- Kein GPU-Pfad ohne echten Kernel, Zielhardwaremessung und
  CPU-/Referenzvergleich.
- Kein automatischer Eingriff in Modellquellen durch
  Performanceoptimierungen.
- Keine Entfernung oder Verfälschung der exakten Referenzpfade.
- Keine GUI-Umgestaltung und keine neuen allgemeinen Bedienelemente ohne
  gesonderte Nutzerentscheidung.
- Keine Annahme, dass eine GPU in jedem Fall schneller als CPU ist; maßgeblich
  ist der gemessene Ende-zu-Ende-Vorteil unter repräsentativer Last.
