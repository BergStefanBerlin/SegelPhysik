# Spezifikation Hydrodynamik v1.0

**Stand:** 17.10.2026<br>
**Status:** Fachlich finalisierte Spezifikation; Umsetzung nur nach den
Stufen und Freigabegates dieses Dokuments sowie der zugehörigen
Umsetzungsanleitung<br>
**Geltungsbereich:** Hydrodynamische Kräfte an Rumpf, Kiel/Schwert und Ruder
bei Verdrängungsfahrt.

## Kennzeichnung und Änderungsverfahren

### Spec000 — Dauerhafte Spezifikationskennungen

Jeder normative Spezifikationspunkt besitzt eine eindeutige Kennung. `Spec000`
bezeichnet diese übergreifende Kennzeichnungsregel; Einzelpunkte beginnen mit
`Spec0001`. Kennungen werden bei Überarbeitungen nicht geändert oder
wiederverwendet. Inhaltlich angepasste Punkte behalten ihre Kennung. Neue
Punkte erhalten bisher unbenutzte Kennungen und werden an ihrer logisch
passenden Stelle eingefügt; bestehende Punkte werden dafür nicht umnummeriert.
Entfallene oder verworfene Punkte werden aus dem aktiven Teil entfernt und am
Dokumentende unter ihrer bisherigen Kennung mit „Nicht umsetzen“ oder
„So nicht umsetzen“ und einer Begründung dokumentiert.

## 1. Zweck und Abgrenzung

### Spec0001 — Spezifikationsstatus und Implementierungsfreigabe

Dieses Dokument spezifiziert Anforderungen an eine spätere
Hydrodynamik-Erweiterung. Es genehmigt keine vorzeitige Produktivaktivierung
und keine Änderung bestehender Modellmeshes. Die Umsetzung darf gemäß der
zugehörigen Umsetzungsanleitung in isolierten, optionalen Schritten erfolgen.
Produktivaktivierung und Modellfreigabe benötigen die Gates nach Spec0037,
Spec0046 und Spec0047.

### Spec0002 — Erhalt vorhandener Physik

Die bereits implementierte Hydrostatik und Auftriebssimulation, Dynamik,
konfigurierbaren linearen/quadratischen Widerstände und diagonale Added Mass
bleiben erhalten. Neue Beiträge dürfen vorhandene Effekte nicht doppelt
berechnen.

### Spec0003 — Erste Gültigkeitsstufe

Die erste Modellstufe beschränkt sich auf Verdrängungsfahrt und
nachvollziehbare Kraft- und Momentenbeiträge von Rumpf, Kiel/Schwert und
Ruder.

### Spec0004 — Gleitfahrt als spätere Erweiterung

Gleitfahrt und dynamischer Auftrieb des Rumpfs gehören nicht zum Umfang dieser
Version. Sie erfordern eine eigene Spezifikation mit Quellen, Gültigkeits-
und Abnahmekriterien.

### Spec0005 — Ausgeschlossene Verfahren und Funktionen

FEM, CFD/SPH, Wellenschlag, Slamming, neue Antriebe, autonome Ruderbewegung
und eine neue Mehrkörperdynamik sind nicht Bestandteil dieser Spezifikation.

## 2. Verbindlicher Bestand und Integrationsgrenzen

### Spec0006 — Vorhandene Integrationsgrundlage

Der aktuelle Code enthält Integrationspunkte, jedoch noch keinen Nachweis
für eine geometrieabhängige hydrodynamische Berechnung:

| Bestandteil | Vorhandene Funktion |
|---|---|
| [kraftmodell.py](../../../../segelphysik/core/kraftmodell.py) | `Kraftmodell`, Fluidgeschwindigkeit, lineare/quadratische Widerstände, Added Mass sowie `Kraftbeitrag`-/`Wrench`-Werte mit Frame und Bezugspunkt |
| [konfig_lader.py](../../../../segelphysik/core/konfig_lader.py) | strikt validierte Physikkonfiguration; unbekannte Schlüssel werden abgelehnt |
| [koerper.py](../../../../segelphysik/core/koerper.py) | starre Körperverbände, relative Posen, Gelenkdefinitionen und Mesh-Snapshots |
| [boot_bau.py](../../../../segelphysik/core/boot_bau.py) | Yacht-OBJ-Teile und Achsenabbildung; der Kompatibilitätspfad vereinigt aktuell Meshes |
| [frames.py](../../../../segelphysik/core/frames.py) | benannte Pose- und Frame-Transformationen |

### Spec0007 — Bestehende Verträge wiederverwenden

Neue hydrodynamische Beiträge müssen die bestehenden Kraftbeitrags-,
Wrench-, Frame-, Körper- und Konfigurationsverträge verwenden. Eine parallele
Aggregation oder ein widersprüchlicher zweiter Vertrag ist unzulässig.

### Spec0008 — Laufzeitpfad vor Implementierung nachweisen

Vor einer Implementierung sind die tatsächlich verwendete Pose-,
Gelenk-, Mesh- und Kraftbeitragskette der Yacht anhand des aktuellen Codes und
von Tests nachzuweisen. Beispielcode oder APIs aus älteren Anleitungen sind
nicht verbindlich.

## 3. Koordinaten, Frames und Vorzeichen

### Spec0009 — SI-Einheiten

Alle Längen, Geschwindigkeiten, Kräfte, Momente, Flächen und Dichten sind
einheitlich in SI-Einheiten anzugeben. Bei dimensionslosen Größen ist die
Definition samt Bezugsgrößen festzuhalten.

### Spec0010 — Achsen- und Wasserlinienkonvention

Der vorhandene Bootbau bildet Modellachsen auf ein rechtshändiges System mit
x nach vorn (Bug), y nach Backbord und z nach oben ab; die Modell-Wasserlinie
liegt nach der Abbildung bei z = 0. Vor Verwendung dieser Konvention in einer
Kraftberechnung ist ihre Übereinstimmung mit den tatsächlichen
Laufzeitframes und Regressionstests zu bestätigen.

### Spec0011 — Kraft- und Momentenbezug

Jeder Kraft- und Momentenbeitrag muss Frame und Bezugspunkt eindeutig
angeben. Teilbeiträge sind mit dem bestehenden Wrench-Vertrag auf den
vereinbarten Gesamtbezugspunkt zu transformieren und erst danach zu
aggregieren.

### Spec0012 — Vorzeichenkonventionen

Vorzeichen für Abdrift, Ruderwinkel, Anstellwinkel, Kiel-/Ruderquerkraft und
Giermoment sind aus den aktuellen Frame- und Gelenkdefinitionen herzuleiten.
Jede Konvention ist mit einem gezielten positiven und negativen Regressionstest
festzuschreiben.

### Spec0013 — Lokale Anströmung

Die lokale Anströmung eines Teils muss Rumpftranslation,
Rumpfwinkelgeschwindigkeit und Teilposition berücksichtigen. Fluidtranslation
und Fluidrotation sind gemäß dem bestehenden Fluidvertrag einzubeziehen.
Kein Rotationsanteil darf doppelt in Relativgeschwindigkeit und
Anstellwinkel eingehen.

## 4. Körper und Geometrieklassen

### 4.1 Rumpf

### Spec0014 — Abgrenzung des Rumpfbeitrags

Der Rumpf erhält in dieser Spezifikation keinen Tragflügel-Auftriebsbeitrag.
Ein späterer Rumpfwiderstand ist als eigener, dokumentierter Beitrag von der
bestehenden Hydrostatik und dem Tauchvolumen getrennt zu halten.

### 4.2 Kiel/Schwert und Ruder

### Spec0015 — Profilierte Geometrieklasse

Ein Kiel, ein Schwert oder ein Ruder darf als profilierte Fläche behandelt
werden, wenn Profilgeometrie und die für das gewählte Modell erforderlichen
Abmessungen ausreichend bekannt und aufgelöst sind. Das Profilmodell muss
Gültigkeitsbereich, Reynolds- und Streckungseinfluss, Ablöseverhalten sowie
Quellen seiner Kennwerte dokumentieren.

### Spec0016 — Unprofilierte Geometrieklasse

Eine flache Platte, ein unbekannter Querschnitt oder ein Mesh ohne
ausreichende Profildaten ist als unprofiliert bzw. unzureichend beschrieben
zu klassifizieren. Dafür ist entweder ein ausdrücklich vereinfachtes
Platten-/Crossflow-Modell mit eigenem Gültigkeitsbereich zu spezifizieren
oder der betreffende Lift-Fall als nicht ausreichend spezifiziert
abzulehnen. Dieser Zweig darf nicht als gleichwertig zu einem validierten
Profilmodell dargestellt werden.

### Spec0017 — Explizite Klassifikation je Teil

Die Geometrieklasse ist für jedes hydrodynamisch berücksichtigte Teil
gesondert festzustellen. Ein Meshname oder eine visuelle Ähnlichkeit allein
ist kein Nachweis für ein Tragflächenprofil. Fehlende Profilkennwerte dürfen
nicht stillschweigend ergänzt werden.

### Spec0018 — Profil-Bezugsgrößen

Ein Profilmodell muss mindestens Bezugsfläche, Spannweite, Profilsehne,
effektiven Anstellwinkel und lokale Anströmung eindeutig definieren. Die
Streckung ist nach einer anerkannten, dimensionslosen Definition aus
Spannweite und Bezugsfläche herzuleiten und für jede Geometrie konsistent
anzuwenden.

### 4.3 Ruderwinkel und Rudergröße der aktuellen Yacht

### Spec0019 — Vorgegebene Ruderstellung

Im Grundumfang wird eine vorgegebene Ruderstellung als Gelenkpose
berücksichtigt. Gelenkachse, Winkelgrenzen, Eingabepfad und Vorzeichen sind
aus dem aktuellen Modell-/Gelenkvertrag abzuleiten und zu testen. Ein eigener
dynamischer Ruderintegrator ist ausgeschlossen.

### Spec0020 — Separate Prüfung eines vergrößerten Ruders

Das aktuelle Rudermesh darf in einer getrennten Variante nach unten
vergrößert werden, falls eine dokumentierte Messung und ein Vergleich gegen
vorab festgelegte Referenzfälle belegen, dass das vorhandene Ruder für den
freigegebenen Zweck unzureichend ist. Diese Möglichkeit ist keine Freigabe,
das Produktivmesh jetzt zu ändern.

### Spec0021 — Anforderungen an eine Rudervariante

Für jede Rudervariante sind Originalmesh und Originalmaße unverändert zu
erhalten. Größe und Ausdehnung der Variante sind auszuweisen und auf
Kollisionen sowie Freigängigkeit zu Rumpf, vorhandenen Antriebsteilen,
Wasserlinie und Boden zu prüfen. Ruderschaft, Drehachse, Gelenkpose, Masse,
Schwerpunkt und Trägheit müssen mit der Variante konsistent sein. Modellklasse
und benötigte Profildaten sind nachzuweisen.

### Spec0022 — Vergleich und Freigabe einer Rudervariante

Ausgangs- und Variantenmesh sind mit denselben Geometrie-, Gelenk-,
Masseneigenschafts- und Hydrodynamiktests zu vergleichen. Eine
Produktivverwendung der Variante benötigt eine gesonderte dokumentierte
Freigabe. Ohne belastbare Messung werden keine Vergrößerungsmaße festgelegt.

### Spec0064 — Reproduzierbares Referenzmanöver für die Ruderwirkung

Der Rudergrößenvergleich verwendet als festgelegten Referenztest einen
anfänglichen Kurs-über-Grund-Fehler von 10° zu einem Zielkurs von 0°. Zu
Beginn stehen Bootskörper-Heading und Kurs auf 10°, die Giergeschwindigkeit
und die Seitwärtsgeschwindigkeit sind null. Der Kurs ist die Richtung des
Geschwindigkeitsvektors im globalen horizontalen Inertialframe; der
Bootskörper-Heading ist eine getrennte Messgröße. Der Testaufbau hält für
jeden vorab ausgewählten Geschwindigkeitsfall die Vorwärtskomponente der
Geschwindigkeit im Bootskörperframe relativ zum ruhenden Wasser
reproduzierbar vor. Da die Umgebung in diesem Test ruht, stimmen Kurs über
Grund und Kurs durchs Wasser überein. Die Geschwindigkeitsvorgabe ist eine
Test-Randbedingung, kein Produktiv-Antriebs- oder Segelmodell.
Seitwärtsbewegung und Gierbewegung bleiben dynamisch. Wind, Wellen und
Strömung sind ausgeschaltet.

Ein ausschließlich für den Test verwendeter, dokumentierter
Proportionalregler befiehlt das Ruder proportional zum gewrappten
Kursfehler, mit Begrenzung auf die nachgewiesenen Gelenkgrenzen. Vorzeichen
und Verstärkung des Reglers sind zu dokumentieren und vor dem Vergleich
festzuschreiben. Regler, Ruderwinkelgrenzen, Anfangszustand, Zeitschritt und
Geschwindigkeiten sind für Original und Variante identisch. Wenn die
Spezifikation des aktuellen Rudergelenks keine Rate vorgibt, wird die
Gelenkpose direkt gesetzt; daraus folgt kein neues Produktivmodell der
Rudermechanik.

Primärmessgröße ist der Betrag des Kurs-über-Grund-Fehlers. Das Ziel aus
Spec0051 gilt als bestanden, wenn der Betrag innerhalb von höchstens 10 s
auf höchstens 50 % des Anfangsbetrags sinkt und ab dem ersten Erreichen
dieser Grenze bis zum Ende des 10-s-Fensters höchstens 50 % des
Anfangsbetrags bleibt. Zusätzlich sind Kurs, Bootskörper-Heading, Ruderwinkel,
Kräfte, Momente, Geschwindigkeit und Überschwingung vollständig
zu protokollieren. Als Überschwingen zählt ein Vorzeichenwechsel des
Kursfehlers mit einem Gegenseitenbetrag oberhalb der vorab festgelegten
Winkeltoleranz; ein solcher Lauf gilt nicht als bestanden. Jeder vorab
festgelegte Geschwindigkeitsfall wird einzeln bewertet. Eine Rudervariante
darf nur empfohlen werden, wenn sie die Referenzfälle, in denen das Original
das Ziel verfehlt, besteht und keinen Referenzfall, den das Original besteht,
zum Fehlschlag verschlechtert. Das Testergebnis ist ein reproduzierbarer
Variantenvergleich, kein nautischer Sicherheits- oder Vollsystemnachweis.

### Spec0065 — Nachweis der Ruderkinematik vor dem Manövertest

Vor einer Ruder-Manöver- oder Größenbewertung müssen Drehachse,
Drehpunkt/Bezugslage, positives Vorzeichen und zulässige Winkelgrenzen aus
einer autoritativen Modell- oder Konstruktionsquelle nachgewiesen sein. Ein
Meshname, eine Bounding-Box oder eine visuelle Schätzung genügt dafür nicht.
Fehlen Gelenk und Pose im Modellmanifest, bleibt der Test blockiert, bis
diese Angaben dokumentiert und die Testkinematik ausdrücklich festgelegt
sind. Es darf weder stillschweigend ein Gelenk erzeugt noch eine
Produktivgeometrie oder -pose verändert werden.

### Spec0066 — Ausdrücklich angenommene Testkinematik ohne Produktionsnachweis

Eine ausdrücklich von der Nutzerin freigegebene, aus dem vorhandenen Mesh
abgeleitete Ruderdrehachse darf ausschließlich in einem getrennten
Test-/Lehrmodell als klar markierte Annahme verwendet werden. Sie gilt nicht
als Erfüllung von Spec0065, nicht als Nachweis der realen Konstruktion und
nicht als Freigabe eines Produktivgelenks, einer Rudervariante oder einer
Manöver-/Größenbewertung. Das bestehende Yachtmanifest, die Pose und das
Produktivverhalten bleiben unverändert. Der Näherungszweig muss außerhalb
seines dokumentierten Gültigkeitsbereichs explizit abbrechen und darf keinen
Validierungsstatus vortäuschen.

## 5. Modellanforderungen

### 5.1 Widerstand am Rumpf

### Spec0023 — Rumpfwiderstandsmodell

Ein späteres Modell darf Reibungs- und Form-/Querwiderstand getrennt
abbilden. Für jede Komponente sind Formel, Bezugsfläche, Bezugsgröße,
Fluidwerte, Gültigkeitsbereich, Einheit und Datenquelle festzulegen.

### Spec0024 — Begründung dimensionsloser Kennzahlen

Reynolds- und Froude-Zahlen dürfen nur verwendet werden, wenn Bezugsgrößen,
Definition und Gültigkeitsbereich für den betrachteten Anwendungsfall
dokumentiert sind. Kandidaten aus älteren Anleitungen gelten nicht als
validierte Modellentscheidung.

### 5.2 Lift und Widerstand an Kiel/Schwert und Ruder

### Spec0025 — Profilmodell für Querkraft und Widerstand

Ein Profilmodell muss Querkraft und Widerstand konsistent aus lokaler
Anströmung und wirksamem Winkel bestimmen. Der gültige Winkel- und
Strömungsbereich sowie das Verhalten bei Ablösung/Stall sind ausdrücklich zu
definieren und durch Quellen oder Referenzdaten zu begründen. Eine
reproduzierbar berechnete Kurve darf als gekennzeichnete Näherung
wiederverwendet werden; sie ist erst nach unabhängiger Validierung im
zugehörigen Geometrie- und Betriebsbereich als validierte Referenz
freigegeben (Spec0062).

### Spec0026 — Vereinfachtes Plattenmodell

Ein vereinfachtes Plattenmodell ist ausdrücklich als Näherung mit eigener
Unsicherheit und eigenem Gültigkeitsbereich auszuweisen. Es darf nicht als
Profilmodell bezeichnet oder unmarkiert mit Profilparametern vermischt
werden.

### Spec0063 — Fachquellen und Grenzen ihrer Übertragbarkeit

Die folgenden Quellen sind Ausgangspunkte für die Recherche, keine pauschale
Freigabe von Formeln, Koeffizienten oder Zahlenwerten:

- [ITTC Recommended Procedure 7.5-02-02-01, Resistance Test](https://ittc.info/media/11780/75-02-02-01.pdf):
  methodischer Bezug für Widerstandstests und deren Auswertung. Eine
  Reibungslinie ist kein vollständiges Modell des Gesamtwiderstands eines
  konkreten Yacht-Rumpfs.
- [Keel-rudder interaction on a sailing yacht, TU Delft](https://research.tudelft.nl/en/publications/keel-rudder-interaction-on-a-sailing-yacht/):
  spezifische Yacht-Untersuchung und Kandidat für Referenz-/Interaktions-
  befunde. Daten dürfen nur übernommen werden, wenn Geometrie,
  Versuchsbedingungen und Gültigkeitsbereich zum Vergleich passen.
- [Keel-Rudder Interaction, TU Delft Repository](https://repository.tudelft.nl/record/uuid:1be75bf7-04b2-4089-95af-95ac4031e034):
  ergänzender Forschungsbericht; vor Nutzung sind Inhalt, Datenzugang,
  Konfiguration und Übertragbarkeit zu prüfen.
- [XFOIL 6.9 User Primer, MIT](https://web.mit.edu/drela/Public/web/xfoil/xfoil_doc.txt):
  beschreibt ein isoliertes 2D-Profilanalysewerkzeug mit begrenzter
  Separation-/Stallbehandlung. Ergebnisse ersetzen keine Validierung für
  ein vollständiges 3D-Kiel-/Rudersystem oder dessen Interaktion.

Die Quellenliste ist versioniert zu ergänzen, wenn die Recherche weitere
Modelle oder Referenzdaten auswählt. Für jede übernommene Zahl sind konkrete
Quelle, Seiten-/Tabellen-/Datensatzstelle, Einheit, Bedingungen und
Gültigkeitsbereich anzugeben.

### Spec0027 — Angriffspunkte und Teilmomente

Kiel- und Ruderkräfte sind an den tatsächlichen, im Teilframe definierten
Angriffspunkten anzusetzen. Momente sind unter Berücksichtigung der
Hebelarme auf den Gesamtbezugspunkt gemäß Spec0011 zu transformieren.

### 5.3 Bestehende Beiträge und Added Mass

### Spec0028 — Vermeidung doppelter Beiträge

Vorhandene lineare/quadratische Widerstände,
Tauchungs-/Krängungsdämpfung, Fluidbewegung, Hydrostatik und Added Mass sind
vor einer Integration den modellierten Effekten zuzuordnen. Derselbe
physikalische Effekt darf nicht unbeabsichtigt gleichzeitig durch alten und
neuen Beitrag berechnet werden.

### Spec0029 — Keine geometrische Added-Mass-Erweiterung in Stufe 1

Eine aus Geometrie abgeleitete Added Mass ist nicht Teil der ersten
Implementierungsstufe. Vorhandene konfigurierte Added-Mass-Werte bleiben
unverändert, bis eine eigene Spezifikation, Datenbasis und Paritätsprüfung
dafür freigegeben sind.

## 6. Benetzung, Geometrievorbereitung und Laufzeit

### Spec0030 — Statische und zustandsabhängige Geometriewerte

Statische Meshkennwerte dürfen außerhalb des Simulations-Hot-Paths
vorberechnet werden, wenn ihre Definition eindeutig und reproduzierbar ist.
Benetzte Flächen und eingetauchte Projektionen sind pose- und
wasserlinienabhängig und dürfen bei veränderlichem Eintauchen nicht als
unveränderliche Werte behandelt werden.

### Spec0031 — Mesh- und Flächenvalidierung

Für jede verwendete Flächenberechnung sind Dreiecksorientierung,
Abschattung/Doppelzählung, ungültige oder offene Meshes und
Wasserlinienschnitt zu spezifizieren und zu testen. Meshreparaturen im
Simulations-Hot-Path sind unzulässig.

### Spec0032 — Cache-Gültigkeit

Cache-Schlüssel und Invalidierung müssen alle für das Ergebnis relevanten
Änderungen berücksichtigen, insbesondere Mesh, Teilpose, Gelenkwinkel und
Wasserlinien-/Eintauchzustand.

### Spec0033 — Performancegate

Geometrie- oder Integrationskosten dürfen nur dann in den Echtzeitpfad
aufgenommen werden, wenn Messungen auf der vereinbarten Zielhardware die
geltenden Live-Performance-Gates bestehen. Messkonfiguration und Rohdaten
müssen reproduzierbar dokumentiert werden.

### Spec0034 — Sichtbarkeit von Teilbeiträgen

Die GUI zeigt die resultierenden Summenkräfte, Momente und Angriffspunkte
grundsätzlich an. Teilkräfte, Teilmomente und ihre Angriffspunkte müssen
zusätzlich optional hierarchisch zuschaltbar sein. Summe und Komponenten
müssen sich auf denselben Frame, Zeitpunkt und Bezugspunkt beziehen.
Komponenten dürfen die Summendarstellung nicht doppelt überlagern, sofern
der Nutzer sie nicht ausdrücklich aktiviert. Die GUI-Ausgestaltung darf in
einem späteren UI-Schritt erfolgen; die funktionale Forderung ist hiermit
festgelegt.

## 7. Konfiguration und Kompatibilität

### Spec0035 — Konfigurationsvalidierung

Eine spätere Konfigurationserweiterung muss den strikt validierten Vertrag
des aktuellen Konfigurationsladers einhalten. Schema, Typen, Einheiten,
Wertebereiche und Fehlerpfade sind explizit festzulegen; unvollständige oder
ungültige Werte müssen klar abgelehnt werden.

### Spec0036 — Defaults und Kompatibilität

Unbelegte Beispielwerte aus älteren Anleitungen dürfen nicht als
physikalisch bestätigte Defaults übernommen werden. Vorhandene
Konfigurationen müssen weiter ladbar bleiben und bei deaktivierter
Erweiterung bisheriges Verhalten und Golden-Ergebnisse erhalten. Neue
Beiträge bleiben bis zur dokumentierten fachlichen Freigabe deaktiviert.

### Spec0061 — Automatisch abgeleitete Geometriemetadaten

Beim Import hydrodynamisch relevanter Geometrien sind reproduzierbar
berechenbare Geometriemetadaten automatisch abzuleiten und im Modellpaket
oder in einem eindeutig damit verknüpften, versionierten Datenartefakt
abzulegen. Dazu gehören mindestens die verwendeten Maße und Flächen sowie
Volumen, Profil-/Querschnittsmerkmale und Streckung, soweit diese für die
Geometrieklasse berechenbar sind. Nicht ableitbare Werte sind als fehlend
auszuweisen, nicht zu schätzen. Die Ablage dokumentiert Einheiten,
Berechnungsverfahren und -version sowie einen Hash der Eingangsgeometrie.

### Spec0062 — Vorberechnete Hydrodynamikdaten und Vertrauensstatus

Kennlinien oder Modellwerte dürfen optional außerhalb des Echtzeitpfads für
ein importiertes Modell berechnet und für spätere Nutzung dauerhaft
gespeichert werden. Jeder Datensatz muss Geometriehash, Modell-/Solvername
und Version, Eingangsparameter, Fluid- und Strömungsbedingungen,
Gültigkeitsbereich, Ergebnisgrößen, Unsicherheitsangabe und Datenherkunft
enthalten. Der Status ist mindestens als „geometrisch abgeleitet“,
„berechnete Näherung“ oder „gegen externe Referenz validiert“ auszuweisen.
Eine berechnete Näherung darf nicht als belastbare Referenz bezeichnet
werden. Eine Importpipeline kann Vollständigkeit und Provenienz des
Datensatzes garantieren, nicht dessen physikalische Richtigkeit. Nicht
validierte Daten dürfen daher keinen Validierungsstatus vortäuschen; ob sie
für einen ausdrücklich als Näherung gekennzeichneten Simulationszweig
verwendbar sind, muss die Modellfreigabe festlegen. Eine externe Messung für
jede einzelne importierte Geometrie ist nicht zwingend erforderlich, wenn
der verwendete Rechenweg für dieselbe Geometrieklasse und den gesamten
Anwendungsbereich unabhängig validiert wurde und die konkrete Geometrie
sowie Betriebsbedingungen nachweislich innerhalb dieses Bereichs liegen.
Außerhalb des Validierungsbereichs bleibt das Ergebnis eine Näherung.

### Spec0037 — Integrationsgrenze

Neue Beiträge sind über die bestehenden Kraftbeitrags- und Wrench-Verträge
zu integrieren. Eine Änderung der Hydrostatik oder des 6-DOF-Integrators
benötigt eine eigene Begründung und Freigabe; sie ist kein stillschweigender
Bestandteil dieser Erweiterung.

## 8. Verifikation und Abnahmekriterien

### Spec0038 — Nullanströmung und Dissipation

Automatisierte Tests müssen bei Nullanströmung null hydrodynamische Kraft und
null hydrodynamisches Moment nachweisen. Widerstandsbeiträge dürfen keine
positive Arbeit leisten; der Testfall und die ausgewertete Energiebilanz
müssen exakt definiert sein.

### Spec0039 — Frames, Bezugspunkt und Symmetrie

Automatisierte Tests müssen äquivalente Gesamt-Wrenches nach
Rotation/Translation und Bezugspunktwechsel sowie erwartungsgemäß
transformierte Resultate bei Spiegelung nachweisen.

### Spec0040 — Geometrieklassen und fehlende Daten

Automatisierte Tests müssen den profilierten und unprofilierten Modellzweig
unterscheiden. Fehlende oder unzureichende Profildaten dürfen nicht
stillschweigend als Profilfall verarbeitet werden.

### Spec0041 — Winkel- und Gierverhalten

Automatisierte Tests müssen Nullwinkel sowie festgelegte positive und
negative Anstell- und Ruderwinkel einschließlich zulässiger Grenzen prüfen.
Der Einfluss der Rumpfwinkelgeschwindigkeit und der lokale Hebelarm sind
gegen einen unabhängigen, dokumentierten Referenzfall zu validieren.

### Spec0042 — Regression vorhandener Physik

Bestehende Hydrostatik-, Solver-, Dynamik- und Konfigurationsregressionen
müssen bestehen. Bei deaktivierter Erweiterung dürfen keine bisherigen
Kraft-, Added-Mass- oder Golden-Ergebnisse unbeabsichtigt abweichen.

### Spec0043 — Geometrievarianten

Das Originalmodell und jede separate Rudervariante müssen getrennt geladen
und getestet werden. Meshvalidierung, Gelenkpose, Masseneigenschaften,
Kollision und Freigängigkeit sind vor einer Variantenfreigabe nachzuweisen.

### Spec0044 — Quantitative Referenzen

Jeder quantitative Test benötigt vor seiner Abnahme einen Zahlenwert oder
Messbereich, Toleranzen, Einheiten, Herkunft und ein reproduzierbares
Messverfahren. Ein nicht belegter „bekannter Wert“ ist kein
Abnahmekriterium. Ohne belastbare Referenz bleibt der betreffende
Modellzweig unabgenommen.

### Spec0045 — Laufzeit- und Liveabnahme

Der integrierte Pfad muss auf der vereinbarten Zielhardware die geltenden
Laufzeit- und Live-Performance-Gates bestehen. Benchmarklast,
Konfiguration, Rohdaten und Auswertung sind zu dokumentieren.

### Spec0054 — Zielhardware und Live-Gates

Für Integrationsmessungen ist die aktuelle Projekt-Zielhardware mit den
bereits etablierten Projekt-Gates zu verwenden. Fehlende, unklare oder nicht
mehr reproduzierbare Gates sind vor der Freigabe offenzulegen und zu klären;
sie dürfen nicht stillschweigend als bestanden gelten.

## 9. Stufen und Freigabegates

### Spec0046 — Geordnete Freigabestufen

Die spätere Umsetzung erfolgt in dieser Reihenfolge:

| Stufe | Inhalt | Abschlussbedingung |
|---|---|---|
| A | Bestands- und Datenaufnahme | Geometrien, Gelenke, Frames, Kraftbeiträge und Referenzdaten sind nachvollziehbar dokumentiert. |
| B | Fachliche Modellauswahl | Widerstands- und Profil-/Plattenmodelle sind samt Gültigkeit, Quellen, Unsicherheit und Referenzfällen entschieden. |
| C | Isolierte Implementierung | Neue Beiträge sind optional und deaktiviert; synthetische Fixtures decken Verträge und Fehlerfälle ab. |
| D | Yachtintegration | Teilbeiträge, Kräfte, Momente und Laufzeit sind gegen unabhängige Referenzen geprüft; jede Rudervariante bleibt bis zu eigener Freigabe getrennt. |
| E | Produktivfreigabe | Fachliche Abnahme, Konfigurations-/Golden-Parität, Performance-Gates, Dokumentation und explizite Freigabe liegen vor. |

### Spec0047 — Gatefehler blockiert Freigabe

Ein nicht bestandenes Gate stoppt den Übergang zur nächsten Freigabestufe.
Fehlende Messwerte, Quellen oder Geometriedaten dürfen nicht durch
Schätzwerte ersetzt werden.

## 10. Verbindliche Nachweisaufträge vor den jeweiligen Freigaben

### Spec0048 — Fachliche Quellen und Modellgültigkeit

Für Widerstands- und Profilmodelle sind geeignete Fachquellen, Rechenwege
und Referenzdaten samt Gültigkeitsbereichen zu recherchieren. Ein Vorschlag
mit Grenzen und Validierungsstatus ist vor Implementierungsfreigabe fachlich
vorzulegen. Eine reproduzierbare Rechnung allein gilt nicht als unabhängige
Validierung. Der Modellzweck ist ein Lehrmodell mit ausdrücklich markierten
Näherungen. Wo belastbare Referenzen existieren, sind sie vorzuziehen; wo
dies praktikabel nicht erreichbar ist, darf ein Näherungszweig nur mit
ausgewiesener Unsicherheit und ohne Validierungsbehauptung vorgeschlagen
werden.

### Spec0049 — Klassifikation der vorhandenen Yachtteile

Für Kiel, Schwert und Ruder der aktuellen Yacht ist anhand ihrer Geometrie
festzustellen, ob sie als profilierte, unprofilierte oder unzureichend
beschriebene Fläche gelten. Eine erste read-only Auswertung des geladenen
Yachtpakets ergibt für das Rudermesh 50 Eckpunkte und 96 Dreiecke. Seine
lokalen Achsenausdehnungen betragen ungefähr 0,2625 m × 0,0275 m × 0,4246 m.
Diese Kennwerte allein beweisen weder ein gültiges Tragflächenprofil noch
dessen hydrodynamische Eignung. Die Klassifikation bleibt offen, bis
Querschnittsgeometrie und meshbedingte Auflösung geprüft sind. Die
Nutzereinschätzung, das Ruder sei visuell zu klein, ist festgehalten; die
quantitative Eignung wird nach Spec0051 geprüft.

### Spec0050 — Geometriedaten der Anhänge

Die validierten Bezugsflächen, Spannweiten, Sehnen und gegebenenfalls
Profilkennwerte für jedes berücksichtigte Teil sind zu bestimmen oder
ausdrücklich als fehlend zu markieren. Die erste Auswertung des bestehenden
Rudermeshes liefert zusätzlich eine Dreiecksoberfläche von ungefähr
0,205962 m² und ein geschlossenes Meshvolumen von ungefähr 0,002360 m³.
Diese geometrischen Werte sind keine hydrodynamischen Bezugsflächen oder
Referenzkennwerte; dafür müssen Bezugsdefinition und Eignung gesondert
bestätigt werden. Sie wurden aus dem unveränderten Yachtpaket nach dessen
Manifest-Einheiten und Achsentransformation geladen und berechnet.

### Spec0051 — Nachweis zur Rudergröße

Gemäß dem reproduzierbaren Referenzmanöver aus Spec0064 muss die Yacht
innerhalb von höchstens 10 Sekunden mindestens 50 % des anfänglichen
Kurs-über-Grund-Fehlers abbauen und nach dem ersten Erreichen der Grenze bis
zum Ende des 10-s-Fensters höchstens 50 % des Anfangsfehlers beibehalten.
Dieses projektspezifische Ziel ist kein allgemeiner
nautischer Sicherheits- oder Leistungsnachweis. Ausgangsruder und getrennte,
nach unten vergrößerte Variante werden unter denselben, vorab dokumentierten
Geschwindigkeits-, Regler- und Anfangsbedingungen verglichen. Die
Rudervariante ist erst dann zu empfehlen, wenn das Original das Ziel in
mindestens einem vorab festgelegten Geschwindigkeitsfall verfehlt, die
Variante jeden solchen Fall besteht und sie keinen zuvor bestandenen
Referenzfall verschlechtert.

### Spec0052 — Variantenfreigabe und Freigängigkeit

Für eine mögliche Rudervariante sind Nachweise zu Bodenfreiheit,
Freigängigkeit, Gelenkgeometrie und geänderten Masseneigenschaften zu
erbringen.

### Spec0053 — Benetzung und Hydrostatik-Konsistenz

Die Methode zur Ermittlung benetzter Flächen ist für die aktuelle Geometrie
festzulegen und gegen den bestehenden Hydrostatikpfad abzugleichen.

### Spec0055 — GUI-Anforderungen

Die grundsätzliche Anzeige von Summen und das optionale hierarchische
Einblenden der Teilbeiträge sind durch Spec0034 entschieden. Der
Umsetzungsschritt muss Summe und optionale Komponenten als Kraft, Moment und
Angriffspunkt darstellen. Offen bleibt nur die konkrete visuelle
Bediengestaltung; vor UI-Freigabe ist sie gegen die dauerhafte
Summendarstellung und die optionale hierarchische Zuschaltung zu prüfen.

## Nicht umsetzen / So nicht umsetzen

Die folgenden Kennungen markieren verworfene Ansätze aus dem früheren
Entwurfsstand. Sie bleiben als Entscheidungsverlauf erhalten und dürfen
nicht als aktive Anforderungen interpretiert werden.

| Kennung | Markierung | Verworfener Ansatz und Begründung |
|---|---|---|
| Spec0056 | **So nicht umsetzen** | Die Beispielwerte `CD_PLATTE = 1.17`, `cl_max = 1.2` und `nu_wasser = 1e-6` aus dem früheren Entwurf nicht ungeprüft als universelle oder projektspezifisch bestätigte Konstanten übernehmen. Werte sind nur nach Quellen- und Gültigkeitsprüfung zulässig. |
| Spec0057 | **So nicht umsetzen** | Die frühere Näherung `Streckung = Tiefe² / Profilfläche` nicht verwenden. Ihre Bedeutung ist nicht hinreichend belegt; Spec0018 verlangt eine anerkannte, konsistente Definition. |
| Spec0058 | **So nicht umsetzen** | Den früher vorgeschlagenen festen Froude-Übergang mit Schwellen 0,4/0,6 und sigmoidförmigem Blend nicht in diese Verdrängungsfahrt-Spezifikation übernehmen. Gleitfahrt ist gemäß Spec0004 separat zu spezifizieren. |
| Spec0059 | **So nicht umsetzen** | Die frühere Beispielimplementierung von `hydrodynamik.py`, `hydroteil_hinzufuegen()` und direkter Verdrahtung in `mit_hydrostatik()` nicht als verbindlichen API- oder Architekturvertrag übernehmen. Zuerst gilt die Bestandsaufnahme nach Spec0008; Integration erfolgt gemäß Spec0007 und Spec0037. |
| Spec0060 | **Nicht umsetzen** | Keine pauschale Änderung oder automatische Ersetzung des Produktiv-Rudermeshes. Zulässig bleibt ausschließlich die separate, nach Spec0020–Spec0022 geprüfte und freigegebene Variante. |
