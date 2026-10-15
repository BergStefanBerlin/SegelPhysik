# SegelPhysik – Spezifikation v1.1

**Grundlage:** [Lehrbuch Schwimmsimulation](./lehrbuch_schwimmsimulation.md),
Bestandsaufnahme des Codes auf `main` nach Commit `5a58ea1` und die unten
festgehaltenen Nutzerentscheidungen.

**Ziel:** Die hydrostatische und dynamische Physik schrittweise fachlich
absichern und erweitern. Die bestehende Darstellung und Bedienung bleibt
unverändert.

**GPU-Leitlinie:** Wenn eine geeignete GPU und ein kompatibles Rechenbackend
verfügbar sind, werden die im Code dafür vorgesehenen Physikberechnungen auf
der GPU ausgeführt. Welche Aufgaben CPU oder GPU nutzen, wird bei der
Implementierung anhand der erwarteten Arbeitslast entschieden. CPU-Ausführung
bleibt immer als korrekter Fallback verfügbar.

## 1. Verbindliche Leitplanken

- Die vorhandene GUI-Darstellung und Bedienung bleibt 1:1 erhalten:
  Fensteraufbau, Docks, Beschriftungen, Statusbereiche, Farben, Kamera- und
  Hintergrundauswahl, Layer, Körperbaum sowie Simulationsmodi und Zeittasten
  werden weder umgestaltet noch um neue allgemeine Bedienelemente erweitert.
- Nur ein ausdrücklich erforderlicher Dialog zur Auswahl bei einer erkannten
  Bauteilüberschneidung ist neu zulässig. Er ändert weder den 3D-Aufbau noch
  die vorhandenen Simulationssteuerungen.
- Der Physikkern rechnet in SI-Einheiten. Bestehende Konfigurationsdateien,
  Einheiten, Material- und Farbregeln bleiben erhalten.
- Bestehende Körperarten bleiben unterstützt: homogene Volumenkörper,
  zusammengesetzte Körper mit unterschiedlichen Materialdichten sowie
  flächenmassige Schalen. Verdrängung richtet sich nach der äußeren
  Geometrie, Masse und Trägheit nach den Material- und Masseneigenschaften.
- Ein physikalischer Standardlauf sucht eine geeignete stabile Gleichgewichtslage,
  nicht sämtliche möglichen Gleichgewichtslagen. Eine exhaustive Mehrfachsuche
  ist wegen ihrer Laufzeit nicht Teil dieses Umfangs.

## 2. Körpergeometrie und Bauteilüberschneidungen

- OBJ-Modelle und prozedurale Körper bilden Geometrie und Darstellung. Die
  Physik muss geschlossene, gültige Volumennetze von offenen
  Schalen-/Flächenmeshes unterscheiden; offene Flächen dürfen nicht als
  geschlossenes verdrängendes Volumen interpretiert werden.
- Zusammengesetzte Volumenkörper dürfen im Inneren keine Überlappungen
  enthalten. Berührende gemeinsame Grenzen sind zulässig. Masse, Schwerpunkt,
  Trägheit und verdrängtes Volumen müssen dieselbe korrigierte Geometrie
  zugrunde legen und Überschneidungen nicht doppelt zählen.
- Bei erkannter Überschneidung wird der Lauf angehalten und die betroffenen
  Bauteile werden benannt. Der Nutzer wählt, welcher Körper unangetastet
  bleibt. Der jeweils andere Körper wird durch eine Boolesche Differenz am
  Rohmodell so beschnitten, dass seine Geometrie außerhalb des
  Vorrangkörpers liegt. Das gilt für OBJ-Modelle ebenso wie für prozedural
  erzeugte Körper.
- Die Korrektur wird dauerhaft in der ursprünglichen Modellquelle gespeichert:
  in der OBJ-Datei oder in der prozeduralen Definition bzw. deren
  Quelldaten. Sie muss beim nächsten Laden erhalten bleiben und darf nicht
  nur auf ein vorübergehend erzeugtes Laufzeit-Mesh angewendet werden. Vor
  der Änderung wird die Modellquelle gesichert. Die Änderung wird nur
  übernommen, wenn das gespeicherte Rohmodell erneut geladen, validiert und
  auf Überlappungsfreiheit geprüft werden kann. Andernfalls wird die
  Modellquelle wiederhergestellt und der Fehler verständlich gemeldet.
- Nach erfolgreicher Korrektur werden Körper, Masse, Schwerpunkt, Trägheit,
  Voxelrepräsentation und Darstellung neu geladen bzw. aufgebaut. Die
  Wiederholung der Prüfung muss den Konflikt als behoben bestätigen.

## 3. Masse, Schwerpunkt und Trägheit

- Volumenkörper erhalten Masse und Trägheit aus ihrer validierten Meshgeometrie
  und Dichte; Schalen aus ihrer Flächengeometrie und Flächenmasse.
- Zusammengesetzte Körper verwenden massengewichteten Schwerpunkt und
  Parallelaxensatz für den Gesamtträgheitstensor.
- Der Trägheitstensor am Schwerpunkt muss symmetrisch und positiv semidefinit
  sein; die Hauptträgheitsmomente müssen die Dreiecksungleichungen erfüllen.
- Materialänderungen bleiben sitzungsgebunden und verändern keine
  Konfigurations-JSON-Datei. Sie aktualisieren Laufzeitkörper und Darstellung
  unmittelbar. Solver-Neuberechnung nach GUI-Eigenschaftsänderungen bleibt
  zurückgestellt, bis diese Frage ausdrücklich neu entschieden wird.

## 4. Hydrostatik und Geometrieauswertung

- Weltkoordinaten bleiben rechtshändig mit z nach oben; die Wasserlinie liegt
  bei z = 0. Auftrieb wirkt vertikal nach oben und entspricht
  `rho_w * g * V_disp`. Sein Moment wird um den Massenschwerpunkt aus dem
  Auftriebsschwerpunkt berechnet.
- Die bestehende Voxelrechnung bleibt zunächst Referenz für das Verhalten.
  Als Ziel wird die starre Volumengeometrie beim Laden einmalig in einem
  körperfesten Raster vorbereitet. Pro Lage wird die Wasserebene in dieses
  Körpersystem transformiert; das Raster selbst wird nicht mit dem Körper
  neu erzeugt.
- Eine Auswertung liefert verdrängtes Volumen und dessen Volumenschwerpunkt.
  Außerdem sollen die Wasserlinienfläche und ihr Flächenträgheitstensor
  verfügbar sein, sobald sie für Stabilitätsdiagnostik benötigt werden.
- Kein Kontakt, tangentialer Kontakt und vollständiges Eintauchen haben
  definierte, endliche Ergebnisse; ein Auftriebsschwerpunkt wird bei
  verschwindendem verdrängtem Volumen nicht durch Division durch null
  berechnet.
- Der exakte Mesh-/Tetraederpfad bleibt Referenz für geschlossene
  Testgeometrien. Voxelwerte werden gegen analytische oder exakte Referenzen
  und die konfigurierten Auflösungs-/Fehlerschranken geprüft.
- Vorbereitete Geometriedaten werden nur bei Modell-, Material- oder
  Auflösungsänderungen neu berechnet, nicht bei jeder Kraftauswertung.

## 5. Hardwarebeschleunigung

- Beim Start wird nur festgestellt, ob eine GPU vorhanden ist. Es gibt keine
  Laufzeitprüfung der Backend-Kompatibilität, keine Laufzeit-Benchmarks und
  keine leistungsabhängige Auswahl pro Aufgabe. Die Zuordnung der Aufgaben
  zu CPU oder GPU ist im Code festgelegt; ist eine GPU vorhanden, wird ein
  dafür vorgesehener GPU-Pfad ohne zusätzliche Nutzerbedienung verwendet.
- Die tatsächliche Wahl des Rechenpfads (GPU mit Gerätename oder CPU-Fallback)
  wird im vorhandenen Protokoll nachvollziehbar ausgegeben; dafür wird kein
  neues GUI-Element eingeführt.
- Eine Grafikkarte, die nur für die Darstellung verfügbar ist, gilt nicht
  automatisch als GPU-Rechenbackend. Rendering und Physikberechnung bleiben
  getrennte Pfade.
- GPU-Ausführung muss mindestens für Voxelberechnung und Kraftauswertung
  anhand ihrer erwarteten Arbeitslast bewertet und bei voraussichtlichem
  Vorteil gegenüber der CPU im Code dafür vorgesehen werden. Weitere Solver-
  und Integrationsarbeit wird nach derselben Vorabentscheidung zugeordnet.
  Diese Zuordnung wird vor der Freigabe durch Entwicklungsbenchmarks
  überprüft, nicht durch Laufzeitmessungen geändert.
- GPU-Backend-Kompatibilität wird während Entwicklung und Abnahme für die
  unterstützten Geräte nachgewiesen, nicht zur Laufzeit. Die Laufzeit prüft
  nur, ob eine GPU vorhanden ist; der vorgesehene GPU-Pfad wird ausprobiert
  und fällt bei einem Initialisierungs- oder Ausführungsfehler auf die CPU
  zurück. Unterstützte integrierte GPUs sind eingeschlossen, sofern Backend,
  Treiber und verfügbarer Speicher für den vorgesehenen Pfad ausreichen.
- Für eine AMD Radeon 760M unter Windows muss beim Technologieentscheid
  geprüft werden, welche GPU-Rechen-Backends mit der eingesetzten Python-,
  Treiber- und Bibliotheksversion tatsächlich funktionieren. Diese
  Spezifikation schreibt kein bestimmtes Framework vor und setzt weder
  CUDA-Verfügbarkeit noch dedizierten Grafikspeicher voraus.
- Ist keine GPU vorhanden oder kann ein vorgesehener GPU-Pfad bei seiner
  Initialisierung oder Ausführung nicht verwendet werden, wird die betroffene
  Berechnung automatisch auf der CPU ausgeführt. Backendfehler werden erst
  beim tatsächlichen Initialisieren oder Ausführen des GPU-Pfads erkannt,
  nachvollziehbar protokolliert und nicht als erfolgreiche GPU-Ausführung
  ausgegeben.
- GPU und CPU verwenden dasselbe fachliche Modell und dieselben
  SI-Konventionen. Parallelreduktions- und Rundungsunterschiede sind zulässig,
  sofern Referenztests, Konvergenz und konfigurierte Fehlergrenzen eingehalten
  werden.
- Die GPU-Ausführung darf weder die bestehende GUI-Bedienung verändern noch
  lange Initialisierung oder Berechnung unbemerkt in der GUI blockieren.
  Initialisierungs- und Berechnungsfehler werden nachvollziehbar protokolliert;
  bei fehlender GPU-Unterstützung bleibt die CPU funktionsfähig.
- Entwicklungsbenchmarks berücksichtigen Datentransfers und vergleichen
  repräsentative Arbeitslasten, einschließlich Vorberechnung und wiederholter
  Auswertung. Die Ergebnisse dienen dazu, die feste Aufgabenverteilung im
  Code festzulegen oder für eine spätere Version anzupassen. Es gibt keinen
  Laufzeitwechsel zur CPU, nur weil eine GPU-Ausführung im Einzelfall langsam
  ist; der CPU-Fallback greift bei fehlender Verfügbarkeit oder einem Fehler
  des GPU-Pfads.

## 6. Simulation – statisch

- Die erste Ausbaustufe erhält den aktuellen Bewegungsumfang aus Tiefgang z
  und Krängung phi und macht den robusten Solver gegen die stufige
  Voxel-Kraftfunktion zuverlässig.
- Der Standardlauf versucht innerhalb eines begrenzten Suchbudgets eine
  geeignete stabile Gleichgewichtslage zu finden. Neutrale, instabile,
  stagnierende und nicht konvergierte Ergebnisse werden unterschieden und
  im vorhandenen Solver-Status korrekt gemeldet. Bei ausbleibendem Erfolg
  weist der Solver Abbruchstatus und Restfehler aus, statt eine erfolgreiche
  Lösung vorzutäuschen. Eine gefundene stabile Lage darf zurückgegeben
  werden; der Solver garantiert weder, alle stabilen Gleichgewichte zu
  finden, noch eine global günstigste Lage zu bestimmen.
- Zur Laufzeitbegrenzung wird keine systematische Multi-Start-Suche über
  viele Orientierungen gefordert. Der Solver darf lokale Starts,
  begrenzte Fallbacks und Wiederanlaufstrategien verwenden; Abbruch und
  Restfehler sind explizit auszuweisen.
- Eine erfolgreiche statische Pose und die vorhandenen Kennwerte werden wie
  bisher in Status und 3D-Ansicht ausgegeben.
- Mehrere Gleichgewichte werden nicht vollständig gesucht oder in einer neuen
  GUI-Liste dargestellt.

## 7. Simulation – dynamisch

### 7.1 Erste Stufe: Tiefgang und Krängung

- Zustand und Integration umfassen z, phi, vertikale Geschwindigkeit und
  Rollgeschwindigkeit. Die vorhandene exklusive Modusauswahl bleibt bestehen:
  Echtzeit startet beim Aktivieren; `=` pausiert und `>` setzt fort.
- Es wird mit festem, konfiguriertem SI-Zeitschritt integriert. Die
  Wandzeit bestimmt nur, wie viele vollständige Physikschritte nachzuholen
  sind; sie ersetzt nie den festen Integrationsschritt.
- Auftrieb und resultierendes Moment stammen aus derselben Kraftfunktion wie
  beim statischen Solver. Schwerkraft wirkt im Schwerpunktframe ohne
  zusätzliches Eigenmoment.
- Die aktuelle lineare Tauch- und Krängungsdämpfung bleibt als
  Übergangsmodell konfigurierbar. Zuerst werden ungedämpfte Grenzfälle und
  Energieverhalten geprüft; Dämpfung darf nicht unbeabsichtigt Energie
  zuführen.

### 7.2 Spätere Stufe: sechs Freiheitsgrade

- Nach abgesicherter erster Stufe wird die Bewegung auf drei translatorische
  Freiheitsgrade und eine normierte Quaternion-Orientierung erweitert.
- Translation und Rotation folgen den Newton-Euler-Gleichungen. Kräfte und
  Momente werden mit konsistenter Umrechnung zwischen Welt- und
  Körperkoordinaten bilanziert; der Trägheitstensor bleibt im Körperframe.
- Quaternionen werden nach Integration normiert. Freiheitsgrade ohne
  rückstellende äußere Kräfte dürfen nicht künstlich stabilisiert werden.
- Die bestehenden GUI-Modi, Zeitsteuerungen und Darstellungselemente bleiben
  auch in dieser Stufe unverändert.

### 7.3 Kraftmodule

- Die Kraftberechnung erhält eine einheitliche Schnittstelle aus Zustand,
  Geschwindigkeit, Winkelgeschwindigkeit und Hydrostatik-Ergebnis. Sie liefert
  Gesamtkräfte und -momente; bestehende Auftriebsdaten bleiben für die
  Darstellung verfügbar.
- Die aktuelle lineare Dämpfung wird in konfigurierbare Kraft-/Momentanteile
  überführt. Erweiterungen für linearen und quadratischen Widerstand,
  Fluidgeschwindigkeit und Added Mass müssen ohne Änderung am Integrator
  ergänzt werden können.
- Für Widerstands- und Added-Mass-Parameter werden keine unbelegten
  Standardwerte erfunden. Aktivierung und numerische Werte benötigen
  validierte Konfigurationen bzw. fachlich bestätigte Koeffizienten.

## 8. Darstellung und Bedienung – unverändert

- Folgende vorhandene Oberflächen und Zustände bleiben erhalten:
  - „Statisch“ / „Echtzeit“ exklusiv; aktiver Modus blau.
  - `=` Pause und `>` Fortsetzen, nur im Echtzeitmodus aktiv und blau.
  - Komponentenbaum, Auswahl-/Aktivitätscheckboxen und vorhandenes
    Klappverhalten.
  - Layer-Checkboxen Schwerpunkt, Achsen, Kräfte und Momente mit unabhängigem
    globalem Schaltverhalten.
  - Kamera-Presets Bug, Heck, Drei Viertel und Draufsicht.
  - Hintergründe Verlauf, Weiß und Dunkel; Studio-Beleuchtung, Wasseroberfläche,
    Wasseroptik und separat schaltbares SSAO.
  - Körperfarben, Wasserlinienschnitt, Pose, bestehende Docks und Statusfelder.
- Im oberen Bereich der Visualisierung erscheinen weiterhin keine
  Hinweis-/Tastentexte. Dekorative Effekte dürfen keine Physik vortäuschen.
- Neue Anzeigen, allgemeine Steuerungen und Änderungen an der GUI-Anordnung
  sind nicht Teil dieser Spezifikation.

## 9. Prüfung und Abnahme

- Referenztests decken analytische Körper, Massenschwerpunkt, Trägheit,
  Komposition, Schalen, Dichteunterschiede, geschlossene/offene Netze,
  Wasserdichtheit und Einheiten ab.
- Hydrostatiktests prüfen Volumen und Auftriebsschwerpunkt für trockene,
  teilweise und vollständig eingetauchte Körper, Monotonie über Tiefgang,
  getrennte Teilbereiche, Drehmomentvorzeichen, Voxelkonvergenz und Abgleich
  mit dem exakten Referenzpfad.
- Überschneidungstests prüfen Auswahl des Vorrangteils, korrekte Boolesche
  Differenz, unveränderte Vorranggeometrie, dauerhafte Speicherung in der
  ursprünglichen OBJ- oder prozeduralen Modellquelle, konfliktfreies erneutes
  Laden sowie Rollback bei fehlerhafter Korrektur.
- Statiktests prüfen Restkraft, Restmoment, Stabilität, Neutralität,
  Stagnation, Fehlerfälle und begrenzte Laufzeit am Produktivmodell.
- Dynamiktests prüfen festen Zeitschritt, Determinismus, Energieverhalten
  ohne Dämpfung, nicht zunehmende Energie bei passiver Dämpfung und
  Einmünden in eine stabile Gleichgewichtslage.
- Für die spätere 6-DOF-Stufe kommen Quaternion-Normierung,
  Impuls-/Drehimpulsbilanz, reine Translation/Rotation und koordinatenfeste
  Kraft-/Momentenbilanzen hinzu.
- GUI-Regressionstests sichern bestehende Bedienung und visuelle
  Steuerverbindungen. Keine Änderung der allgemeinen Darstellung oder
  Steuerung darf ohne neue Nutzerentscheidung freigegeben werden.
- Performance wird auf repräsentativen Produktivkörpern gemessen und mit
  dokumentierter Rasterauflösung und Hardware ausgewiesen. Maßgeblich ist,
  dass sich die Anwendung für den Nutzer flüssig und jederzeit bedienbar
  anfühlt; eine feste Laufzeitgrenze für einzelne Kraftauswertungen oder
  Solverläufe ist kein Selbstzweck. Die GUI-Ereignisschleife darf durch
  Rechenarbeit nicht blockiert werden. Als überprüfbare Richtwerte bleiben
  Eingabereaktionen innerhalb von 100 ms und mindestens 30 Bilder pro
  Sekunde unter repräsentativer Last. Warte- oder Abbruchzustände werden in
  vorhandenen Statusflächen nachvollziehbar angezeigt; zusätzliche
  allgemeine Bedienelemente sind ausgeschlossen.
- Die Anforderungen an eine flüssige Bedienung gelten für CPU- und
  GPU-Ausführung. Messungen weisen Reaktionszeit, Bildrate und
  Berechnungsdauer getrennt aus.
- Bei Vorhandensein kompatibler GPU-Hardware werden dieselben
  Referenzkörper auf GPU und CPU geprüft. Die Implementierungen stimmen
  innerhalb der Toleranz überein, wenn die absoluten Abweichungen des
  verdrängten Volumens `|ΔV_disp|` höchstens
  `schranke_volumen_m3` und – sofern definiert – des
  Auftriebsschwerpunkts höchstens `schranke_punkt_m` betragen. Der
  Schwerpunktvergleich gilt nur, wenn das verdrängte Volumen auf beiden
  Pfaden größer als die Volumenschranke ist. Daraus folgt für die
  Auftriebskraft:
  `|ΔF_A| <= rho_w * g * schranke_volumen_m3` und
  für das Auftriebsmoment gilt bei Volumen oberhalb dieser Schranke auf beiden
  Pfaden:
  `|ΔM_A| <= rho_w * g * (L_max * schranke_volumen_m3 + V_max * schranke_punkt_m)`,
  wobei `L_max` der größere Abstand eines berechneten Auftriebsschwerpunkts
  vom Massenschwerpunkt und `V_max` das größere berechnete verdrängte Volumen
  der beiden Pfade ist. Liegt das Volumen mindestens eines Pfads höchstens
  bei der Volumenschranke, wird der Schwerpunktvergleich ausgelassen und
  stattdessen bei bereits erfüllter Volumenschranke
  `|ΔM_A| <= 3 * rho_w * g * L_body * schranke_volumen_m3` geprüft;
  `L_body` ist der größte Abstand eines Punkts der verdrängenden Geometrie
  vom Massenschwerpunkt. Die GPU/CPU-Übereinstimmung gilt nur, wenn alle
  jeweils anwendbaren Volumen-, Schwerpunkt-, Kraft- und Momentschranken
  eingehalten sind. Referenz- und Konvergenztests verwenden dieselben
  Schranken, sofern sie dieselben Größen vergleichen. GPU-Ausführung darf
  nicht lediglich anhand eines erfolgreichen Imports als funktionsfähig
  gelten.
- Benchmarkberichte unterscheiden Hardwareerkennung, Backend-Initialisierung,
  einmalige Vorberechnung, Datentransfer und wiederholte Kraftauswertung.
  Mindestens der konfigurierte Quader und ein repräsentativer komplexer
  Modellkörper werden während Entwicklung und Abnahme gemessen. Diese
  Benchmarks verändern nicht die Aufgabenverteilung während der Laufzeit.
- Hardwareprofil für die erste Zielvalidierung: Windows x64, AMD Ryzen 5
  8600G mit integrierter Radeon 760M und 32 GB RAM. Die gemeldeten 512 MB
  Grafik-Speicher werden als Geräte-/Treiberangabe behandelt; verfügbarer
  gemeinsamer Speicher wird zur Laufzeit ermittelt. Geräte- und Produkt-IDs
  sind keine Konfigurations- oder Spezifikationsdaten.

## 10. Bestandsaufnahme bei Erstellung

- OBJ-Teile werden aktuell mit einem einfachen Leser für `v`-/`f`-Zeilen
  geladen. Die Physik schneidet getauchte Blattmeshes je Kraftauswertung und
  berechnet daraus ein globales Voxelraster; ein körperfest vorberechnetes
  Voxelraster und Wasserlinien-Flächenträgheit sind nicht vorhanden.
- Die Voxel-Union verhindert derzeit Doppelzählung beim verdrängten Volumen.
  Die Körperfabrik addiert Masse und Trägheit ihrer Teile; geometrische
  Überschneidungen werden nicht allgemein vorab korrigiert.
- `wasserdichtheit()` existiert als Meshprüfung, wird aber nicht als
  durchgängige Modellvalidierung beim OBJ-Laden erzwungen. Volumenkörper und
  flächenmassige Teile sind im Modell bereits unterschiedliche Fälle.
- Statische und dynamische Kraftauswertung verwenden dieselbe
  Auftriebsfunktion. Deren `v`-/`omega`-Argumente werden noch nicht für
  Widerstand oder Added Mass ausgewertet.
- Der robuste statische Solver arbeitet lokal in z und phi, wählt eine
  stabile Lage und kann an Voxel-Stufen stagnieren. Die Echtzeitintegration
  verwendet semi-implizites Euler für z und phi mit konfigurierter linearer
  Dämpfung.
- Lokale CPU-Messung am konfigurierten Quader mit Python 3.13:
  fünf Kraftauswertungen im Mittel ca. **36,9 ms** je Auswertung; der aktuelle
  robuste Einzellauf ca. **1,50 s**. Dies ist eine Bestandsmessung auf der
  Erstellungsumgebung, keine Garantie für andere Körper oder Hardware.
- Als Größenordnung, nicht als Messung: 100 Starts mit je 10 äußeren und
  10 inneren Iterationen ergäben bei der gemessenen Auswertungszeit bereits
  ungefähr **369 s** reine Kraftauswertungszeit. Die genaue Zahl hängt stark
  von Raster, Mesh und Solverpfad ab.
- Boolesche Geometrieoperationen zur Überlappungskorrektur sind gemäß
  Abschnitt 2 Bestandteil dieser Spezifikation und dürfen das Rohmodell erst
  nach ausdrücklicher Auswahl des unangetasteten Vorrangkörpers verändern.
  6-DOF und zusätzliche Widerstandsmodule bleiben spätere Ausbaustufen.
- Ein GPU-Rechenpfad und Entwicklungsbenchmarks zum CPU/GPU-Vergleich sind
  im geprüften Stand nicht nachgewiesen; die GUI-3D-Darstellung allein belegt
  keine GPU-Beschleunigung der Physik. Eine leistungsabhängige Auswahl zur
  Laufzeit ist nicht vorgesehen.

## 11. Bewusst gestufter Umfang

1. Physikalische Referenzen und Fehlerbehandlung der bestehenden 2-DOF-Statik
   und -Dynamik festigen.
2. GPU-Backend-Kompatibilität auf der Zielhardware prüfen und einen
   CPU/GPU-Referenz- und Benchmarkpfad herstellen; fehlende GPU-Unterstützung
   darf den CPU-Betrieb nicht verhindern.
3. Meshvalidierung und die gewählte, rückrollbare Überlappungskorrektur in
   den ursprünglichen OBJ- oder prozeduralen Modellquellen umsetzen.
4. Körperfestes vorberechnetes Voxelmodell und Wasserlinienkennwerte ergänzen;
   Genauigkeit und Laufzeit auf CPU und verfügbarer GPU vergleichen.
5. Kraftmodule und anschließend 6-DOF-Dynamik schrittweise ergänzen.
6. Nach jeder Stufe vollständige Regression ausführen und alle bestehenden
   Darstellungs- und Steuerungstests unverändert bestehen lassen.

Die Umsetzungsreihenfolge erlaubt keine Änderung von Quellmodellen ohne die
in Abschnitt 2 beschriebene Erkennung, Benennung und ausdrückliche Auswahl
durch den Nutzer. Nach dieser Auswahl ist die abgesicherte, dauerhaft
gespeicherte Korrektur des OBJ- oder prozeduralen Rohmodells gemäß Abschnitt 2
Teil des Umfangs.

Weitere Änderungen an Quellmodellen oder Physik-Code außerhalb dieser
Spezifikation bedürfen einer gesonderten Beauftragung.
