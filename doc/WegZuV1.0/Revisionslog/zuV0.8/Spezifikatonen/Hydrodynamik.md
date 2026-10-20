# Spezifikation: Hydrodynamik der Yacht

**Arbeitsbereich:** ausschließlich zuV0.8  
**Status:** Arbeitsfassung zur Abstimmung; aktive Anforderungen, Umsetzung offen  
**Geltungsbereich:** Hydrodynamik, stationäres Gleichgewicht und zugehörige Darstellung  
**Grundlage:** [Nummerierungs-Instruction](../../../../../.github/instructions/nummerierung.instructions.md), [Hydrodynamik-Anleitung](../hydrodynamik_anleitung.md), [kritische Bewertung](../hydrodynamik_spezifikation_entwurf.md) und aktueller Projektcode.

## Ziel

Die Yacht soll in horizontaler Richtung nachvollziehbar und stabil
physikalisch reagieren. Bei Fahrt ohne Antrieb muss sie durch
hydrodynamischen Widerstand langsamer werden. Bei einer definierten
Antriebskraft soll sich ein stationärer Zustand mit ausgeglichenen Kräften
und Momenten finden lassen. Rumpf, Kiel/Schwert und Ruder sollen erkennbare
hydrodynamische Beiträge liefern.

Der bestehende hydrostatische Anteil aus Gewicht und Auftrieb ist für diese
Arbeit vorerst gültig und darf durch die neue Hydrodynamik nicht verändert
werden. Das Hydrodynamikmodell ist eine echtzeitfähige Näherung, kein
CFD-Modell. Unvalidierte Koeffizienten dürfen nicht als reale Yacht1-Werte
ausgegeben werden.

## Kennungen und Änderungsgrundsätze

Die aktiven Anforderungen verwenden projektweit das Format
`A-V0.8-<laufende-nummer>`. Frühere `SpecNNNN`-Kennungen sind ausschließlich
im Anhang als historische Zuordnung aufgeführt. Eine einmal vergebene
Anforderungs-ID wird nicht wiederverwendet.

Der frühere Punkt `A-V0.8-00003` widersprach der jetzt gewünschten
stationären Fahrtlösung. Er wird deshalb zurückgezogen und am Dokumentende
archiviert; die neue statische Anforderung erhält eine neue ID. Die
Umsetzungsschritte gehören in einen zugehörigen Umsetzungsplan, erhalten
`U-V0.8-…`-Kennungen und verweisen auf die aktiven A-IDs.

## Aktive Anforderungen

| ID | Bereich | Anforderung |
|---|---|---|
| A-V0.8-00001 | Geltungsbereich | Verdrängungsfahrt als erster Gültigkeitsbereich |
| A-V0.8-00002 | Hydrostatik | Vertikale Hydrostatik unverändert erhalten |
| A-V0.8-00004 | Dynamik | Lokale Relativströmung an jedem Kraftangriffspunkt |
| A-V0.8-00005 | Dynamik | Dissipativer Widerstand bei Vorwärts- und Rückwärtsfahrt |
| A-V0.8-00006 | Dynamik | Seitlicher Rumpfwiderstand |
| A-V0.8-00007 | Dynamik | Kielwirkung bei Abdrift |
| A-V0.8-00008 | Dynamik | Ruderwirkung und Gierdämpfung |
| A-V0.8-00009 | Modellgrenzen | Begrenzte und stetige Modellbereiche |
| A-V0.8-00010 | Dynamik | Energetisch konsistente Kraftanteile |
| A-V0.8-00011 | Geometrie | Geometriebezug und Modellannahmen offenlegen |
| A-V0.8-00012 | Geometrie | Lageabhängige Benetzung berücksichtigen |
| A-V0.8-00013 | Dynamik | Bauteilbeiträge korrekt aggregieren |
| A-V0.8-00014 | Kompatibilität | Nicht konfigurierte Körper unverändert lassen |
| A-V0.8-00015 | Laufzeit | Echtzeitfähige Auswertung |
| A-V0.8-00016 | GUI | Hydrodynamische Beiträge aus den berechneten Kräften anzeigen |
| A-V0.8-00017 | Konfiguration | Physikparameter explizit validieren |
| A-V0.8-00018 | Validierung | Gesamtverhalten reproduzierbar testen |
| A-V0.8-00019 | Statik | Stationären hydrodynamischen Gleichgewichtspunkt direkt lösen |
| A-V0.8-00020 | Statik | Laufzeitziel für den stationären Solver |
| A-V0.8-00021 | Dynamik | Körperbezogene Gleichgewichtsreferenz im Verdrängerbereich |
| A-V0.8-00022 | GUI | Kraft- und Momentenpfeile an physikalisch begründeten Orten anzeigen |
| A-V0.8-00023 | Settings | Detailkraftanzeigen einzeln schalten, standardmäßig eingeschaltet |
| A-V0.8-00024 | GUI | Ergebnis und Konvergenz des stationären Solvers anzeigen |
| A-V0.8-00025 | Testbarkeit/API | APIs zur einfacheren automatisierten Prüfung anpassen, ohne Produktfunktionen zu verändern |
| A-V0.8-00026 | Settings/GUI | Körperbezogene Hydrodynamik-Defaults beim Körperwechsel laden |
| A-V0.8-00027 | Solver/Validierung | Konvergenz und dynamische Gleichgewichtsprüfung quantifizieren |
| A-V0.8-00028 | Settings/GUI | Ruderausschlag als eigenständige Körpereinstellung führen |

## 1. Geltungsbereich und Hydrostatik

### A-V0.8-00001 – Verdrängungsfahrt als erster Gültigkeitsbereich

Das erste integrierte Hydrodynamikmodell ist für ruhiges Wasser und
Verdrängungsfahrt auszulegen und soll anhand der Körpergeometrie für
unterschiedliche Längen und Rumpfformen parametrierbar sein. Yacht1 darf
nicht als fest codierter Sonderfall vorausgesetzt werden. Wellen, Slamming
und Gleiten sind nicht Teil dieses Umfangs. Mit „Wellen“ sind hier Seegang
und von außen eingetragene Wellen gemeint; der empirische
Wellenbildungswiderstand des Rumpfes im ruhigen Wasser bleibt gemäß
A-V0.8-00005 Bestandteil des Widerstandsmodells. Eine spätere Gleitfahrt
benötigt ein separates, dafür begründetes Modell; Verdrängerformeln dürfen
nicht stillschweigend in diesen Bereich extrapoliert werden. Der
dokumentierte Modellbereich darf nicht als für höhere Geschwindigkeiten
validierte Yachtprognose ausgegeben werden.

**Abnahme:** Modellstatus und Gültigkeitsbereich sind dokumentiert und die
festgelegten Bereichsgrenzen werden getestet.

### A-V0.8-00002 – Vertikale Hydrostatik unverändert erhalten

Die bestehende Hydrostatik aus Gewicht und Auftrieb bleibt unverändert.
Hydrodynamische Beiträge dürfen den Auftrieb weder doppelt ansetzen noch
die vorhandene Hydrostatikberechnung ersetzen.

**Abnahme:** Bestehende Hydrostatik-Regressionen bestehen. Bei ruhendem
Wasser und fehlender hydrodynamischer Anströmung bleibt die bisherige
hydrostatische Kraftbilanz erhalten.

## 2. Statischer stationärer Gleichgewichtspunkt

Der bisherige statische Solver sucht einen hydrostatischen Lagezustand. Die
stationäre Fahrt ist ein gekoppeltes Gleichgewichtsproblem: Die unbekannte
Fahrtgeschwindigkeit beeinflusst die hydrodynamischen Kräfte; diese müssen
gemeinsam mit Antrieb, Lage und Angriffspunktmomenten ausgeglichen sein.

### A-V0.8-00019 – Stationären hydrodynamischen Gleichgewichtspunkt direkt lösen

Der statische Berechnungsweg muss neben dem hydrostatischen Lagezustand einen
stationären hydrodynamischen Gleichgewichtspunkt für eine vorgegebene,
konstante, körperbezogene Antriebs-/Testkraft und deren dokumentierten
Angriffspunkt bestimmen können.

Die Suche erfolgt gestuft. Zunächst wird ein symmetrischer Geradeauslauf
gelöst, wobei Vorwärtsgeschwindigkeit, Hub/Eintauchen und Nick-/Trimmlage
frei sind; seitliche Bewegung, Krängung und Gieren sind in diesem Stadium
beschränkt. Danach werden die übrigen relevanten Freiheitsgrade schrittweise
freigegeben. In jedem Folgestadium müssen alle bereits freigegebenen
Unbekannten gemeinsam erneut gelöst werden. Im endgültigen stationären
Zustand sind die resultierenden äußeren Kräfte und Momente ausgeglichen,
sodass keine translatorische oder rotatorische Beschleunigung verbleibt.
Antriebskraft und hydrodynamische Reaktion dürfen an unterschiedlichen
Punkten angreifen; ihre Momente gehören in denselben Gleichgewichtsnachweis.

Der vorhandene hydrostatische Gleichgewichtspunkt darf als Startwert für
die gekoppelte Suche verwendet werden. Die Kopplung muss anschließend
direkt als Gleichungssystem gelöst werden. Ein wiederholtes Abwechseln
zwischen hydrostatischem Solver und zeitlicher Dynamikintegration ist nicht
das Suchverfahren. Die Dynamik darf danach als unabhängige Verifikation
des gefundenen Zustands dienen.

Der Solver muss Konvergenz, Restkräfte/-momente und den Grund eines
Fehlschlags explizit liefern. Er darf keinen nicht konvergierten Zustand
als erfolgreiches Gleichgewicht melden. Ein Zwischenstadium ist stets als
vorläufiges Teilgleichgewicht zu kennzeichnen.

**Abnahme:** Für einen festgelegten Betriebsfall findet der Solver einen
reproduzierbaren Zustand mit Restkräften und Restmomenten innerhalb der
festgelegten normierten Toleranzen. Fehler in einem späteren Stadium lassen
den letzten gültigen Zwischenstand verfügbar, aber sichtbar als nicht
vollständig konvergiert. Eine unabhängige Dynamikverifikation prüft den
endgültigen Zustand.

### A-V0.8-00020 – Laufzeitziel für den stationären Solver

Für einen repräsentativen Yacht1-Gleichgewichtsfall soll die statische
Berechnung im Idealfall höchstens fünf Sekunden dauern. Dies ist zunächst
ein angestrebtes Gesamtlaufzeitziel und keine Abbruchfrist oder vorab
garantierte harte Echtzeitgrenze. Dauert die Suche länger, läuft sie mit
Fortschrittsmeldungen weiter und bleibt abbrechbar.
Geometrie und andere unveränderliche Daten sollen vorbereitet und
wiederverwendet werden; die Suche selbst soll ohne unnötige dynamische
Zeitschrittintegration erfolgen.

**Abnahme:** Die Laufzeit wird für einen dokumentierten Referenzfall und
eine festgelegte Referenzumgebung gemessen und berichtet. Vor einer
verbindlichen harten Grenze werden Referenzhardware, Startbedingungen und
Messmethode festgelegt. Zielwert: höchstens fünf Sekunden.

### A-V0.8-00027 – Konvergenz und dynamische Gleichgewichtsprüfung quantifizieren

Der stationäre Solver gilt nur dann als konvergiert, wenn sowohl die
Restkraft als auch das Restmoment jeweils höchstens **1 %** ihrer
körperbezogen normierten Referenzgröße betragen. Die Kraft wird relativ
zur charakteristischen Antriebskraft normiert, das Moment relativ zum
Produkt aus charakteristischer Antriebskraft und Körperlänge. Zusätzlich
müssen festzulegende numerische Iterationsschranken erfüllt sein. Die GUI
zeigt neben den normierten Werten auch Restkräfte in N und Restmomente in
Nm.

Der endgültige stationäre Zustand wird unabhängig mit unveränderter
Testkraft **10 simulierte Sekunden** dynamisch vorwärts gerechnet. Die
Vorwärtsgeschwindigkeit darf sich dabei um höchstens **1 %** ändern;
Lage- und Drehbewegungen dürfen nicht systematisch anwachsen. Während
dieser Verifikation wird weder die Kraft nachgeregelt noch der stationäre
Solver erneut ausgeführt. Die GUI zeigt bestanden/nicht bestanden und die
gemessenen Abweichungen.

**Abnahme:** Tests prüfen die normierten und tatsächlichen Restwerte sowie
die 10-Sekunden-Verifikation mit stabilen und instabilen Fällen. Die
konkreten Iterationsschranken und der Umgang mit sehr kleinen
Referenzgrößen sind dokumentiert und getestet.

## 3. Dynamische Hydrodynamik

### A-V0.8-00004 – Lokale Relativströmung

Jeder hydrodynamische Beitrag muss die lokale Geschwindigkeit seines
Angriffspunkts relativ zum Wasser verwenden. Körpertranslation,
Körperrotation und der Hebelarm des Angriffspunkts sind einzubeziehen.
Eine konfigurierte Fluidgeschwindigkeit ist in konsistenten Koordinaten zu
berücksichtigen.

**Abnahme:** Tests mit Translation, Rotation und bewegtem Wasser prüfen
lokale Geschwindigkeit, Frame-Transformation und Vorzeichen.

### A-V0.8-00005 – Dissipativer Widerstand in Längsrichtung

Bei von null verschiedener Längs-Relativgeschwindigkeit muss der
hydrodynamische Widerstand entgegen der Relativfahrt wirken. Das gilt für
Vorwärts- und Rückwärtsfahrt. Der Rumpfwiderstand ist als Komponentenmodell
aus viskosem Reibungsanteil und empirischem Form-/Wellenwiderstand
aufzubauen. Die Anteile werden anhand der jeweiligen Geometrie und
physikalischen Kennzahlen bestimmt; konkrete Fachformeln und
Gültigkeitsbereiche sind zu recherchieren und zu dokumentieren. Der
Wellenwiderstand bezeichnet hier den empirischen Wellenbildungswiderstand
des Rumpfes im ruhigen Wasser, nicht Widerstand durch Seegang oder äußere
Wellen. Bei ausgeschaltetem Antrieb muss der Betrag der anfänglichen
Längsgeschwindigkeit im dynamischen Lauf abnehmen.

**Abnahme:** Kraftvorzeichen und dynamische Abbremsung werden in beiden
Fahrtrichtungen geprüft. Die Komponenten sind getrennt auswertbar und
werden nicht doppelt gezählt.

### A-V0.8-00006 – Seitlicher Rumpfwiderstand

Bei seitlicher Relativbewegung muss der Rumpf eine definierte
hydrodynamische Reaktion entgegen der Querbewegung erzeugen. Eine
Kraftkomponente in einer anderen Richtung darf bei isolierter Bewegung
nicht ohne ausdrücklich hergeleitete und dokumentierte Kopplung entstehen.

**Abnahme:** Reine Längs- und Querbewegung werden getrennt geprüft; der
Querwiderstand ist dissipativ.

### A-V0.8-00007 – Kielwirkung bei Abdrift

Das Kielsystem muss bei ausreichender Anströmung eine seitliche Kraft
aufgrund des Abdriftwinkels erzeugen können. Bei fehlender Anströmung darf
keine dynamische Kiel-Auftriebskraft entstehen. Geradeausfahrt ohne
Abdrift darf keinen künstlichen Abdriftwinkel erhalten.

**Abnahme:** Nullanströmung, Nullabdrift sowie positive und negative
Abdrift werden mit dokumentierter Vorzeichenkonvention getestet. Eine
Spiegelung der Abdrift kehrt die Seitenkraft konsistent um.

### A-V0.8-00008 – Ruderwirkung und Gierdämpfung

Der Ruderwinkel ist ein expliziter, von der Fremdkraft unabhängiger Eingang
des Modells. Er wird in der GUI in der Nähe der Fremdkraft-Einstellungen
angeboten, aber als eigene Ruder-Einstellung behandelt. Der einstellbare
Winkelbereich ist −90° bis +90°; der Default ist 0°. Bei ausreichender Fahrt
erzeugt Ruderausschlag eine Seitenkraft gemäß einer dokumentierten
Winkel- und Achsenkonvention. Die lokale Anströmung am Ruder berücksichtigt
Körperrotation und Hebelarm und erzeugt das entsprechende Moment am
Gesamtkörper. Der stationäre Gleichgewichtssolver behandelt den eingestellten
Ruderwinkel als vorgegebenen Eingang und verändert ihn nicht automatisch.
Eine automatische Lenkregelung gehört nicht zu diesem Umfang. Außerhalb des
physikalisch abgesicherten Modellbereichs muss die GUI den Gültigkeitsstatus
sichtbar melden. Der Winkel darf nicht stillschweigend auf einen engeren
Bereich gekappt werden.

**Abnahme:** Beide Rudervorzeichen und das Giermoment bei Rudernull werden
mit Kraft- und Momentenvorzeichen geprüft. Default, Eingabebereich und
Modellbereichs-Status werden geprüft.

### A-V0.8-00009 – Begrenzte und stetige Modellbereiche

Bei Stillstand, sehr kleiner Anströmung und an Modellgrenzen liefert das
Modell endliche und stetige Werte. Insbesondere gehen Widerstandskräfte
stetig gegen null, wenn die Relativgeschwindigkeit gegen null geht.
Numerische Schutzmaßnahmen dürfen keine unbegründete physikalische Aussage
erzeugen. Nicht unterstützte Zustände werden kontrolliert begrenzt oder als
Modellbereichsfehler kenntlich gemacht; außerhalb des dokumentierten
Verdrängerbereichs darf keine gültige Gleitfahrtprognose vorgetäuscht
werden.

**Abnahme:** Grenzwerttests prüfen Endlichkeit, Stetigkeit und die
festgelegte Fehlerbehandlung.

### A-V0.8-00010 – Energetische Konsistenz der Kraftanteile

Widerstandsanteile wirken der lokalen Relativbewegung entgegen und führen
ihr keine Energie zu. Auftriebsartige Anteile werden getrennt vom
Widerstand berechnet. Dieselbe Wirkung wird nicht doppelt als
Querwiderstand und Profil- oder induzierter Widerstand angesetzt.

**Abnahme:** Die Leistung jedes Widerstandsbeitrags relativ zum Wasser ist
nicht positiv. Auftriebs- und Widerstandsanteile werden separat geprüft.

### A-V0.8-00011 – Geometriebezug und Modellannahmen offenlegen

Jeder hydrodynamische Geometriewert ist einem Bauteil und Frame zugeordnet.
Die Koeffizienten und Widerstandsanteile werden mit empirischen
Fachmodellen und aus der jeweiligen Geometrie hergeleitet. Einheiten,
Quellen, Herleitung, Gültigkeitsbereich, Unsicherheit und Annahmen sind
dokumentiert. Die Hydrodynamikkoeffizienten dürfen nicht allein so
hingetrimmt werden, dass der Referenzlauf eine gewünschte Geschwindigkeit
erreicht. Meshwerte gelten ohne Validierung nicht als reale
Yachtkoeffizienten.

**Abnahme:** Quelle oder Herleitung, Einheit, Bauteil und Status sind
nachvollziehbar; ausgewählte Geometrie- und Modellwerte werden gegen
Referenzen geprüft und ihre Gültigkeit für unterschiedliche Körper ist
ausgewiesen.

### A-V0.8-00012 – Lageabhängige Benetzung berücksichtigen

Die benetzte Geometrie berücksichtigt die aktuelle Körperpose und
Wasserlinie. Solver, Dynamik und Kraftdarstellung verwenden konsistente
Benetzungsdaten. Die Berechnung ist für den dynamischen Hot-Path
vorzubereiten oder effizient zwischenzuspeichern; eine feste benetzte
Fläche ist kein Ersatz für die lageabhängige Auswertung.

**Abnahme:** Bei Wasserlinienänderung wird die Änderung der Kennwerte
nachgewiesen. Solver, Dynamik und angezeigte Kraftbeiträge verwenden
konsistente Geometrie- und Benetzungsstände.

### A-V0.8-00013 – Bauteilbeiträge korrekt aggregieren

Hydrodynamische Beiträge von Rumpf, Kiel/Schwert und Ruder gehen als
benannte Kräfte mit Angriffspunkten in das vorhandene Wrench- und
Aggregationsmodell ein. Hebelarme erzeugen korrekte Momente am
Gesamtkörper. Die aggregierte Kraft wird dem 6-DOF-Integrator genau einmal
übergeben.

**Abnahme:** Einzel-Wrenches, Gesamt-Wrench und Integratoreingabe stimmen
überein; Hebelarmmomente und Framewechsel werden geprüft.

### A-V0.8-00014 – Nicht konfigurierte Körper unverändert lassen

Für Körper ohne Hydrodynamikkonfiguration bleibt das neue Modul
deaktiviert. Das bisherige Verhalten nicht betroffener Körper sowie die
Hydrostatik- und Kraftmodell-API bleiben erhalten.

**Abnahme:** Regressionstests prüfen nicht konfigurierte Körper.

### A-V0.8-00015 – Echtzeitfähige Auswertung

Mesh-I/O und unnötige Mesh-Integration erfolgen nicht pro Simulationsschritt.
Vorbereitbare Geometrie- und Kennwertdaten werden außerhalb des
Integrations-Hot-Paths berechnet. Die Simulation läuft nicht schneller als
Echtzeit. Wenn Berechnungen länger als die verstrichene Echtzeit dauern,
darf die GUI warten; Simulationszeit darf weder verworfen noch die
Simulation deshalb automatisch gestoppt werden. Die vorhandene
Echtzeitsemantik bleibt erhalten.

**Abnahme:** Hot-Path-Prüfung weist unnötige Mesh-Operationen aus;
Laufzeitmessungen mit aktivierter Hydrodynamik berichten Verzögerungen,
ohne Simulationszeit zu überspringen oder ungewollt zu stoppen.

### A-V0.8-00018 – Gesamtverhalten reproduzierbar testen

Einzelkrafttests und reproduzierbare dynamische Tests sichern Abbremsen
ohne Antrieb, Querbewegung, Abdrift, Ruderwirkung, Gierdämpfung und
Gleichgewichtsverhalten ab. Erwartungsbereiche und Referenzdaten werden
festgelegt, bevor quantitative Genauigkeit behauptet wird.

**Abnahme:** Automatisierte Regressionen prüfen vereinbarte
Akzeptanzbereiche; definierte Yacht1-Läufe sind reproduzierbar.

### A-V0.8-00021 – Körperbezogene Gleichgewichtsreferenz im Verdrängerbereich

Für Yachtkörper wird als Referenzgeschwindigkeit **80 % der empirisch
geschätzten Rumpfgeschwindigkeit** verwendet. Für Yacht1 ergibt die
konstruktive Wasserlinie näherungsweise **4,14 m** Wasserlinienlänge. Mit
der empirischen Näherung \(1{,}34\sqrt{L_\mathrm{WL}\,[\mathrm{ft}]}\)
ergibt sich eine Rumpfgeschwindigkeit von rund **4,94 kn** und damit eine
Referenzgeschwindigkeit von rund **3,95 kn**. Die Rumpfgeschwindigkeit ist
ein Vergleichswert, keine harte physikalische Grenze; die Näherung und
ihre Anwendbarkeit auf andere Rumpfformen sind zu dokumentieren.

Für Körper ohne sinnvolle Rumpfgeschwindigkeit, darunter generische
Volumenkörper, werden körperbezogene Referenzwerte so gewählt und
dokumentiert, dass plausible normale Geschwindigkeiten entstehen. Die
konkreten Werte dürfen während der Umsetzung anhand der Geometrie,
geeigneter Fachquellen und reproduzierbarer Versuche ermittelt werden.

Der Referenzlauf verwendet die vorhandene Fremdkraft-Konfiguration mit
konstanter, körperbezogener Testkraft und festgelegtem Angriffspunkt. Bei
Yachten werden Betrag und Angriffspunkt so gewählt, dass der theoretische
stationäre Zustand die Referenzgeschwindigkeit erreichen kann. Der
Test-Wrench wird nicht als reale Segelkraft ausgegeben. Da die Testkraft
gezielt auf die Referenzgeschwindigkeit abgestimmt wird, ist das Erreichen
dieser Geschwindigkeit allein kein unabhängiger Nachweis für die
Richtigkeit der hydrodynamischen Koeffizienten.

Im stationären Zustand gleichen sich die **Gesamtsysteme** aus: Die Summe
aller äußeren Kräfte und die Summe aller Momente sind innerhalb der
festgelegten Toleranzen null. Es wird keine paarweise Gleichheit einzelner
Antriebs- und Hydrodynamikkräfte und kein gemeinsamer Angriffspunkt
vorausgesetzt. Die dynamische Verifikation prüft unabhängig, ob dieser
Zustand bei unveränderter Testkraft stabil bleibt.

Geschwindigkeiten wie 100 kn liegen ausdrücklich außerhalb des
spezifizierten Verdrängungsmodells. Das Modell darf dort keine gültige
Yachtprognose behaupten oder durch eine willkürliche
Geschwindigkeitsbegrenzung vortäuschen.

**Abnahme:** Für Yachtkörper stellt sich aus den dokumentierten
körperbezogenen Testeingaben ein reproduzierbarer Gleichgewichtszustand
nahe 80 % der empirischen Rumpfgeschwindigkeit ein. Für Volumenkörper
werden die dokumentierten plausiblen Referenzbereiche erreicht. Die
Gleichgewichtsbilanz und die unabhängige dynamische Prüfung erfüllen die
Kriterien aus **A-V0.8-00027**.

## 4. Settings

### A-V0.8-00026 – Körperbezogene Hydrodynamik-Defaults beim Körperwechsel laden

Für jeden hydrodynamisch unterstützten Körper wird ein eigenes
Referenzprofil mit der Testkraft und ihrem Angriffspunkt festgelegt. Das
Profil wird geladen, wenn der Körper ausgewählt wird, und ist für diesen
Körper zunächst aktiv. Die Werte bleiben vom Nutzer während der Auswahl
änderbar. Ein Wechsel zu einem anderen Körper und die spätere Rückkehr
laden wieder die Defaults des zurückgewählten Körpers; nutzergeänderte
Werte werden durch den Wechsel nicht als neue Defaults übernommen. Die
Werte werden aus der jeweiligen Geometrie und dem Referenzfall nach
A-V0.8-00021 hergeleitet und dokumentiert.

**Abnahme:** Tests mit mehreren Körpern prüfen getrennte Defaultprofile,
das Laden bei Auswahl, die Änderbarkeit und das Zurücksetzen beim
Wiederaufrufen eines Körpers.

### A-V0.8-00017 – Physikparameter explizit validieren

Hydrodynamische Physikparameter werden über das bestehende
Konfigurations-/Ladesystem eingelesen und validiert. Einheiten, zulässige
Werte sowie optionale und erforderliche Parameter sind eindeutig.
Fehlende Werte werden nicht stillschweigend als physikalisch begründete
Yacht1-Koeffizienten interpretiert.

**Abnahme:** Gültige, fehlende und ungültige Konfigurationen werden
automatisiert geprüft; ungültige Werte erzeugen eine nachvollziehbare
Fehlermeldung.

### A-V0.8-00028 – Ruderausschlag als eigenständige Körpereinstellung führen

Die GUI bietet einen Ruderwinkel-Regler im Bereich der Fremdkraft-Eingaben,
aber getrennt von Betrag, Richtung und Angriffspunkt der Fremdkraft. Der
Eingabebereich reicht von **−90° bis +90°**; der Default pro Körper ist
**0°**. Beim Körperwechsel wird der jeweilige Default geladen. Nutzer können
den Winkel ändern, bis der Körper gewechselt wird. Das Hydrodynamikmodell
meldet sichtbar, wenn ein Winkel außerhalb seines physikalisch
abgesicherten Bereichs liegt; es darf den Eingabewert nicht stillschweigend
begrenzen.

**Abnahme:** Eingabebereich, Default, Körperwechselverhalten und
Gültigkeitsmeldung außerhalb des abgesicherten Winkelbereichs werden
geprüft.

### A-V0.8-00023 – Detailkraftanzeigen unabhängig schalten

In den Settings lassen sich die hydrodynamischen Detailkraftpfeile für
Rumpf, Ruder und Kiel/Schwert unabhängig voneinander ein- und ausschalten.
Alle drei Anzeigen sind standardmäßig eingeschaltet. Der Zustand wird
entsprechend dem bestehenden Settings-Verhalten gespeichert.

Das Umschalten beeinflusst ausschließlich Sichtbarkeit und Darstellung.
Physikberechnung, Bewegung, Einzelbeiträge und hydrodynamische Summenpfeile
bleiben unverändert.

**Abnahme:** Jede Anzeige ist unabhängig schaltbar, startet standardmäßig
aktiv und verändert bei Umschalten weder berechnete Beiträge noch
Simulationszustand.

## 5. GUI und Kraftvisualisierung

Hydrostatische Kraftpfeile und ihre bisherige Berechnung bleiben von allen
Anforderungen dieses Abschnitts unberührt.

### A-V0.8-00016 – Hydrodynamische Beiträge aus berechneten Kräften anzeigen

Die GUI zeigt hydrodynamische Beiträge aus denselben Kraftdaten an, die in
die Dynamik eingehen. Sie berechnet keine abweichenden Ersatzkräfte nur
für die Anzeige.

**Abnahme:** Für einen festgelegten Zustand stimmen dargestellte
hydrodynamische Beiträge mit Kraftmodellbeiträgen überein.

### A-V0.8-00022 – Kraft- und Momentenpfeile an physikalisch begründeten Orten

Jeder hydrodynamische Detailkraftpfeil wird am vom Modell gelieferten
Angriffspunkt des zugehörigen Beitrags dargestellt. Das gilt getrennt für
Rumpf, Ruder und Kiel/Schwert. Der Punkt muss eine dokumentierte
Modellannahme oder eine begründete Geometrie-/Kraftangriffsstelle sein; er
darf nicht allein zur Vereinfachung auf den Gesamtschwerpunkt verschoben
werden.

Die hydrodynamische Summenkraft wird aus allen hydrodynamischen
Einzelbeiträgen gebildet. Ihr Pfeil liegt auf der Wirkungslinie der
resultierenden Kraft und nicht pauschal am Schwerpunkt oder an einem
willkürlichen Modell-Referenzpunkt. Der Kraftpfeil wird an einem
Schnittpunkt dieser Wirkungslinie mit der benetzten Körpergeometrie
gezeichnet. Existiert kein solcher Schnittpunkt, wird die Wirkungslinie
selbst gezeigt, statt einen körperlichen Angriffspunkt zu erfinden. Ein
zum resultierenden Wrench gehörendes freies Restmoment wird separat als
Moment dargestellt.

Ist die Summenkraft innerhalb der festgelegten numerischen Toleranz null,
ist ihre Wirkungslinie nicht bestimmbar. Dann wird kein Summenkraftpfeil an
einem erfundenen Punkt gezeigt; ein vorhandenes Summenmoment bleibt
sichtbar.

Der hydrodynamische Summenmomentenpfeil stellt das aggregierte
hydrodynamische Moment dar. Er wird als Momentenvektor und nicht als
Kraftpfeil mit scheinbarem Kraftangriffspunkt visualisiert. Sein
Darstellungspunkt ist der für die GUI festgelegte Momenten-Referenzpunkt;
er ändert nicht den physikalischen Bezug oder die Wrench-Aggregation.
Kraft- und Momentenmaßstäbe sind getrennt und so zu wählen, dass Länge und
Richtung die jeweiligen Vektoren erkennbar wiedergeben.

Segel- oder Testkräfte, etwa eine definierte Kraft im oberen Mastbereich,
bleiben an ihrem jeweiligen konfigurierten Angriffspunkt sichtbar.
Hydrodynamische Beiträge bleiben an ihren Modell-Angriffspunkten. Die GUI
erzwingt weder gleiche Einzelkraftbeträge noch einen gemeinsamen
Angriffspunkt. Im stationären Gleichgewichtskriterium werden die gesamten
Kraft- und Momentensysteme verglichen.

**Abnahme:** Detailpfeile stimmen in Vektor und Angriffspunkt mit ihren
Modellbeiträgen überein. Summenkraft, Wirkungslinie, gegebenenfalls
verbleibendes Moment und Summenmoment stimmen mit der Wrench-Aggregation
überein. Der hydrostatische Kraftpfeil bleibt unverändert.

### A-V0.8-00024 – Ergebnis und Konvergenz des stationären Solvers anzeigen

Die GUI zeigt während jedes Solverstadiums den aktuellen Status und ein neu
gerendertes Bild des letzten gültigen Körperzustands. Geradeaus- und
Folgestadien sind als vorläufige Teilgleichgewichte zu kennzeichnen. Nach
Abschluss zeigt die GUI Konvergenzstatus, gefundene Fahrtgeschwindigkeit,
Restkräfte und Restmomente sowie Rechenzeit an. Ein fehlgeschlagenes
Folgestadium lässt das letzte gültige Bild sichtbar, kennzeichnet es aber
als nicht vollständig konvergiert. Ein ungültiger Lauf darf nicht als
erfolgreiches Gleichgewicht erscheinen.

**Abnahme:** Erfolgreiche und fehlgeschlagene Solverläufe zeigen klar
unterscheidbare Stadien und Ergebnis-/Fehlerdaten. Zwischenbilder
entsprechen jeweils dem angezeigten letzten gültigen Zustand.

## 6. Testbarkeit und API

### A-V0.8-00025 – Test- und Steuer-APIs anpassen, ohne Produktfunktionen zu verändern

APIs und interne Schnittstellen dürfen ergänzt oder angepasst werden, wenn
dies automatisierte Tests der Anforderungen vereinfacht oder zuverlässiger
macht. Dazu zählen insbesondere programmatische Steuerung der GUI,
Laufzeitdiagnose, Ergebniszugriff und kontrollierbare Testeingaben.

Solche Änderungen sind auf die Prüfbarkeit zu begrenzen. Sie dürfen keine
vorhandene Produktfunktion entfernen, abschalten oder in ihrem
Nutzerverhalten verändern. Physikalische Berechnungen, Standardwerte,
Bedienabläufe und sichtbare Ergebnisse müssen unverändert bleiben, sofern
eine separate aktive Anforderung keine ausdrückliche Verhaltensänderung
verlangt. Die Test- und Steuer-API selbst darf dafür geändert werden;
betroffene Aufrufer, Tests und Dokumentation sind konsistent anzupassen.
Neue Testzugänge dürfen keine zusätzlichen Änderungen am
Produktionsverhalten auslösen.

**Abnahme:** Bestehende Produkt- und Regressionstests zeigen unverändertes
Verhalten. Neue Test- oder Steuerzugänge ermöglichen die automatisierte
Prüfung der Hydrodynamik, ohne dafür die fachliche Funktion zu verändern.

## 7. Rückverfolgbarkeit zur Umsetzung

Der zugehörige [Folge-Umsetzungsplan](../Umsetzungsplan/Hydrodynamik_2.md)
führt die verbliebenen U-Schritte, Abhängigkeiten und Meilensteine fort.
Die Statusangaben unten beruhen auf dem dokumentierten Stand des
Vorgängerplans und dessen Folgeplan; sie unterscheiden vorhandene
Teilnachweise von noch ausstehender vollständiger Abnahme. Alle aktiven
A-IDs sind mindestens einem Umsetzungsschritt zugeordnet.

| Aktive A-ID | Abschnitt | Umsetzungsschritt(e) | Test/Abnahme | Status |
|---|---|---|---|---|
| A-V0.8-00001 | Geltungsbereich und Hydrostatik | U-V0.8-000001, U-V0.8-000003, U-V0.8-000006, U-V0.8-000008 | Mesh-LWL 3,789 m; Abgleich mit 4,14 m und unabhängige Widerstandsreferenz offen | teilweise |
| A-V0.8-00002 | Geltungsbereich und Hydrostatik | U-V0.8-000004, U-V0.8-000008 | Hydrostatik-Regression | teilweise |
| A-V0.8-00004 | Dynamik | U-V0.8-000003, U-V0.8-000008 | Lokale Anströmung und Frames | teilweise |
| A-V0.8-00005 | Dynamik | U-V0.8-000001, U-V0.8-000003, U-V0.8-000008 | Widerstandskomponenten und Abbremsen vorwärts/rückwärts | teilweise |
| A-V0.8-00006 | Dynamik | U-V0.8-000003, U-V0.8-000008 | Querwiderstand und Energietest | teilweise |
| A-V0.8-00007 | Dynamik | U-V0.8-000003, U-V0.8-000008 | Kielkraft bei Abdrift | teilweise |
| A-V0.8-00008 | Dynamik | U-V0.8-000001, U-V0.8-000003, U-V0.8-000007, U-V0.8-000008 | Ruderwirkung und Gierdämpfung | teilweise |
| A-V0.8-00009 | Dynamik | U-V0.8-000003, U-V0.8-000008 | Grenz- und Stetigkeitstests | teilweise |
| A-V0.8-00010 | Dynamik | U-V0.8-000003, U-V0.8-000008 | Leistungs-/Dissipationstest | teilweise |
| A-V0.8-00011 | Dynamik | U-V0.8-000001, U-V0.8-000003, U-V0.8-000008 | Geometrieherkunft und Modellstatus | teilweise |
| A-V0.8-00012 | Dynamik | U-V0.8-000002, U-V0.8-000003, U-V0.8-000008 | Benetzungs-/Gültigkeitsnachweis | teilweise |
| A-V0.8-00013 | Dynamik | U-V0.8-000004, U-V0.8-000008 | Wrench-Summe und Momente | teilweise |
| A-V0.8-00014 | Dynamik | U-V0.8-000004, U-V0.8-000008 | Regression nicht konfigurierter Körper | teilweise |
| A-V0.8-00015 | Dynamik | U-V0.8-000004, U-V0.8-000008 | Hot-Path- und Laufzeitmessung | teilweise |
| A-V0.8-00016 | GUI | U-V0.8-000007, U-V0.8-000008 | Anzeige entspricht Rechenbeiträgen | teilweise |
| A-V0.8-00017 | Settings | U-V0.8-000002, U-V0.8-000008 | Additives Profil-Schema und Negativtests; vollständige Abnahme offen | teilweise |
| A-V0.8-00018 | Validierung | U-V0.8-000001, U-V0.8-000006, U-V0.8-000008 | Reproduzierbare Systemtests | teilweise |
| A-V0.8-00019 | Statik | U-V0.8-000005, U-V0.8-000008 | Gestufter Solver, dynamische Fehlerregression und Plattenfall; fünf generische Profile erreichen kein Gleichgewicht | teilweise |
| A-V0.8-00020 | Statik | U-V0.8-000005, U-V0.8-000008 | Laufzeitmessung, Ziel ≤ 5 s | erfüllt (0,315 s gemessen) |
| A-V0.8-00021 | Dynamik | U-V0.8-000001, U-V0.8-000006, U-V0.8-000008 | LWL-basierte Yacht1-Kalibrierung reproduzierbar; unabhängige Validierung offen | teilweise |
| A-V0.8-00022 | GUI | U-V0.8-000007, U-V0.8-000008 | Angriffspunkte und resultierende Wrenches | teilweise |
| A-V0.8-00023 | Settings | U-V0.8-000007, U-V0.8-000008 | Drei unabhängige Toggles, Default ein | teilweise |
| A-V0.8-00024 | GUI | U-V0.8-000005, U-V0.8-000007, U-V0.8-000008 | Solverstatus und dynamische Fehlergründe; vollständige Zwischenbild-/Ergebnisabnahme offen | teilweise |
| A-V0.8-00025 | Testbarkeit/API | U-V0.8-000008 | Automatisierte Prüfung bei unverändertem Produktverhalten | teilweise |
| A-V0.8-00026 | Settings | U-V0.8-000002, U-V0.8-000006, U-V0.8-000007, U-V0.8-000008 | Konfigurierte Profile für vorhandene Körper; GUI- und Abnahmematrix offen | teilweise |
| A-V0.8-00027 | Solver/Validierung | U-V0.8-000005, U-V0.8-000007, U-V0.8-000008 | 1-%-Bilanz und dynamische 10-s-Prüfung | Umsetzung belegt; M7/M8-Abnahme offen |
| A-V0.8-00028 | Settings/GUI | U-V0.8-000002, U-V0.8-000003, U-V0.8-000007, U-V0.8-000008 | Rudereingabe, Default und Gültigkeitsmeldung | teilweise |

## 8. Noch offene Festlegungen

Die folgenden Umsetzungswerte sind noch anhand der Körpergeometrien,
Fachquellen und Tests zu bestimmen und zu dokumentieren:

- Konkrete empirische Fachformeln, Koeffizienten, Gültigkeitsbereiche und
  Unsicherheiten für Reibungs-, Form-/Wellen- und Auftriebsanteile.
- Zuverlässige Geometrie- und Benetzungsdaten je Körper sowie die
  Vorbereitung/Zwischenspeicherung für den Echtzeit-Hot-Path.
- Unabhängige Validierung der vorläufig konfigurierten Testkraft-Wrenches,
  Angriffspunkte und Referenzgeschwindigkeiten für Yacht1 und generische
  Volumenkörper. Für Yachtkörper gilt 80 % der empirischen
  Rumpfgeschwindigkeit als Kalibrierziel; die konkrete Testkraft darf
  nicht als Segelkraft ausgegeben werden.
- Ruderdrehachsen je Körper und der Winkelbereich, für den das jeweilige
  hydrodynamische Rudermodell physikalisch abgesichert ist.
- Numerische Iterationsschranken und robuste Normierung bei sehr kleinen
  Referenzkräften oder charakteristischen Längen.
- Referenzhardware und Messmethode für das Fünf-Sekunden-Laufzeitziel.
- Laufzeitmessung des dynamischen Hot-Paths; die bereits festgelegte
  Echtzeitsemantik (keine übersprungene Simulationszeit und kein
  automatischer Stopp) bleibt dabei verbindlich.

Die Rumpfgeschwindigkeit ist eine empirische Näherung aus der
Wasserlinienlänge und keine harte Grenze. Werte oberhalb des
Verdrängungsbereichs benötigen ein separates Modell und eine eigene
Validierung.

## Anhang A – Übergang von der alten Nummerierung

Die rechte Spalte nennt die aktiven A-IDs. Ehemalige Kennungen erscheinen
nur in diesem historischen Zuordnungskontext. Der frühere Punkt 3 wurde
inhaltlich zurückgezogen und hat keinen aktiven Nachfolger mit derselben
ID; die neue stationäre Gleichgewichtsanforderung besitzt eine neue
Kennung.

| Alte Kennung | Neue aktive Kennung oder Status |
|---|---|
| Spec0001 | A-V0.8-00001 |
| Spec0002 | A-V0.8-00002 |
| Spec0003 | A-V0.8-00003 (zurückgezogen) |
| Spec0004 | A-V0.8-00004 |
| Spec0005 | A-V0.8-00005 |
| Spec0006 | A-V0.8-00006 |
| Spec0007 | A-V0.8-00007 |
| Spec0008 | A-V0.8-00008 |
| Spec0009 | A-V0.8-00009 |
| Spec0010 | A-V0.8-00010 |
| Spec0011 | A-V0.8-00011 |
| Spec0012 | A-V0.8-00012 |
| Spec0013 | A-V0.8-00013 |
| Spec0014 | A-V0.8-00014 |
| Spec0015 | A-V0.8-00015 |
| Spec0016 | A-V0.8-00016 |
| Spec0017 | A-V0.8-00017 |
| Spec0018 | A-V0.8-00018 |

## Nicht umsetzen

### A-V0.8-00003 – Keine Fahrtgeschwindigkeit im statischen Solver

**Zurückgezogen.** Der Punkt legte fest, dass der statische Solver keine
stationäre Fahrtgeschwindigkeit berechnet. Das widerspricht dem jetzt
festgelegten Ziel, im statischen Berechnungsweg einen gekoppelten
hydrodynamischen Gleichgewichtspunkt direkt zu bestimmen. Die alte ID
bleibt reserviert. Die neue Anforderung ist **A-V0.8-00019**; sie ist eine
inhaltliche Neufassung, keine Wiederverwendung der alten Kennung.
