# Hydrodynamik – kritische Bewertung und Spezifikationsentwurf

**Status:** Diskussionsentwurf, nicht beschlossen und bewusst ohne Spezifikations-IDs  
**Arbeitsstand:** zuV0.8  
**Grundlage:** [`hydrodynamik_anleitung.md`](./hydrodynamik_anleitung.md) und der aktuelle Projektcode

## Ziel

Eine belastbare horizontale Dynamik für die Yacht schaffen: Vorwärtsfahrt muss
bei fehlendem Antrieb durch hydrodynamischen Widerstand abgebaut werden;
Abdrift, Gierbewegung und Ruderausschlag müssen über nachvollziehbare Kräfte
an Rumpf, Kiel und Ruder wirken. Die bestehende vertikale Hydrostatik aus
Gewicht und Auftrieb bleibt dabei erhalten.

Das Modell soll zunächst Verdrängungsfahrt abdecken. Es ist ein
echtzeitfähiges Näherungsmodell, kein CFD-Ersatz. Rechenaufwand und
Darstellungsqualität sind wichtig, dürfen aber physikalische Vorzeichen,
Einheiten, Angriffsorte und Gültigkeitsgrenzen nicht verschleiern.

## Kritische Bewertung der Anleitung

### Was daran tragfähig ist

- Die Trennung zwischen Hydrostatik und hydrodynamischen Kräften ist sinnvoll.
- Ein Modell mit vorberechneten Geometriekennwerten ist ein pragmatischer
  erster Schritt zwischen globalen Handkoeffizienten und CFD.
- Lokale Anströmung aus Translation und Rotation ist nötig, um Hebelarme und
  Gierdämpfung realistisch abzubilden.
- Kräfte als getrennte Beiträge mit Angriffspunkt ermöglichen eine
  nachvollziehbare Summierung, Momentenbildung und spätere Kraftpfeile.
- Verdrängungsfahrt zuerst und Gleiten später zu behandeln, begrenzt den
  anfänglichen Gültigkeitsbereich sinnvoll.

### Was vor einer Umsetzung präzisiert werden muss

- **Geometrie ist nicht gleich hydrodynamische Koeffizienten.** Benetzte Fläche,
  Projektionsfläche, Bezugslänge und Streckung helfen bei der Herleitung,
  bestimmen aber allein weder den tatsächlichen Widerstand noch die
  Kiel-/Ruderpolare. Profil, Rauheit, Interferenz, Einbau und Strömungszustand
  bleiben relevante Einflüsse. Die behauptete Genauigkeit von 10–20 % ist ohne
  Validierungsdaten nicht belegt.
- **Die ITTC-Reibungsformel hat einen begrenzten Anwendungsbereich.** In der
  Anleitung wird sie über `max(Re, 1)` auch nahe Stillstand verwendet; das
  regularisiert weder die Formel fachlich noch beschreibt es den laminaren
  Bereich. Gültigkeitsbereich, Übergang und Verhalten bei sehr kleinen
  Geschwindigkeiten müssen explizit festgelegt und numerisch stetig sein.
- **Der vorgeschlagene Rumpfwiderstand ist unvollständig.** Er bezeichnet
  Vorwärts-, Quer- und Vertikalwiderstand, berechnet aber nur x- und
  y-Komponenten. Die Reibung wird aus der Gesamtgeschwindigkeit ermittelt,
  während die Kraft anschließend nur entlang x wirkt. Das ist keine
  hinreichend begründete allgemeine Reibungsformel. Für Querströmung wird ein
  Crossflow-Term skizziert, für Heave, Roll, Pitch und Yaw fehlt ein
  vollständiger Ansatz.
- **Die Lift-Skizze ist kein ausführbarer Algorithmus.** Richtung und
  Vorzeichen der Kraft, Koordinatenframe, Projektion in den Weltframe und
  Momentenbildung bleiben als Auslassung markiert. Die Beziehung zwischen
  `Tiefe`, Spannweite und `AR` ist uneinheitlich beschrieben; Streckung muss
  für jedes Teil mit eindeutiger Geometriedefinition bestimmt werden.
- **Widerstand und Lift müssen sauber getrennt werden.** Ein Liftanteil soll
  quer zur lokalen Anströmung wirken; Profil- und induzierter Widerstand
  entgegen ihr. Es muss verhindert werden, dass ein Kraftanteil unbeabsichtigt
  Energie zuführt oder dieselbe Querströmung doppelt als Crossflow und
  Profilwiderstand gezählt wird.
- **Benetzung ist lageabhängig.** Ein einmal vorberechneter Wert für
  benetzte Fläche reicht bei veränderlichem Tiefgang, Krängung und Trimm nicht
  automatisch aus. Die Anleitung braucht eine konkrete, performante Strategie,
  wie benetzte Flächen während der Fahrt aktualisiert oder angenähert werden.
- **Die Bauteiltopologie ist zu grob beschrieben.** Die aktuelle Yacht enthält
  Rumpf, Ruder, Kielsystem mit Kiel und Bulb sowie Rigg-Bestandteile. Es muss
  festgelegt werden, welche Meshes hydrodynamisch aktiv sind und wie das
  Kielsystem als gemeinsamer hydrodynamischer Teil behandelt wird.
- **Die Rudersteuerung ist nicht nur ein Mesh-Problem.** Rudergelenk,
  Winkelkonvention, zulässiger Ausschlag und die Quelle des Steuerwinkels
  müssen mit dem vorhandenen Körper-/GUI-Zustand verbunden werden. Eine
  angenommene Achse darf nicht als vermessene Konstruktionsgeometrie gelten.
- **Der Gleitübergang ist nicht Bestandteil des ersten stabilen Modells.**
  Die Anleitung schlägt später einen Blend vor, benennt aber noch keine
  validierten Koeffizienten für den Gleitbereich. Ein solcher Übergang würde
  das erste Ziel und seine Prüfung unnötig vergrößern.
- **Die Roadmap unterschätzt die Validierung.** Aussagen wie „1 Tag“ geben
  keine fachliche Abdeckung. Vor allem Widerstandskennwerte, Vorzeichen und
  gekoppelte Fahrversuche brauchen messbare Akzeptanzkriterien und
  Referenzwerte.

## Vergleich mit dem aktuellen Code

| Thema | Stand im Projekt | Konsequenz |
|---|---|---|
| Gesamtwiderstand | [`kraftmodell.py`](../../../code/core/kraftmodell.py) berechnet lineare/quadratische Widerstände über sechs Komponenten relativ zur Fluidgeschwindigkeit. In [`physik.json`](../../../konfigurationen/physik.json) sind x- und y-Widerstand derzeit nicht gesetzt. | Das vorhandene Modul erklärt, warum die Yacht aktuell horizontal nicht abbremst; es kann als Kompatibilitäts- und Vergleichspfad dienen, ersetzt aber kein bauteilbezogenes Modell. |
| Kraftintegration | [`dynamik_6dof.py`](../../../code/core/dynamik_6dof.py) integriert einen starren Gesamtverband. Kräfte und Momente müssen vor dem Integrator zu einem Ergebnis aggregiert sein. | Einzelteile können eigene Kraftbeiträge liefern, brauchen aber zunächst keine separaten dynamischen Freiheitsgrade. |
| Hydrostatik | [`auftrieb.py`](../../../code/core/auftrieb.py) wertet das verdrängende Mesh des Gesamtverbands aus; die 6-DOF-Kraftfunktion ist im Echtzeitprozess eingebunden. | Hydrostatik sollte unverändert bleiben. Die Anleitung verweist an dieser Stelle auf `hydrostatik.py`, im aktuellen Code liegt der einschlägige Pfad in `auftrieb.py`. |
| Bauteilgeometrie | [`koerper.json`](../../../konfigurationen/koerper.json) bildet Rumpf, Ruder, Kielsystem und Rigg als Teile ab. [`boot_bau.py`](../../../code/core/boot_bau.py) kann OBJ-Teile einzeln laden; `baue_boot()` vereinigt sie dagegen zu einem Mesh. | Die bestehende Teilehierarchie ist verwendbar, aber hydrodynamische Rollen, lokale Frames und benetzte Geometrien müssen explizit abgebildet werden. |
| Ruder-Näherung | [`hydrodynamik_ruder_naeherung.py`](../../../code/core/hydrodynamik_ruder_naeherung.py) und [`test_hydrodynamik_ruder_naeherung.py`](../../../tests/test_hydrodynamik_ruder_naeherung.py) enthalten eine aus dem Ruder-Mesh abgeleitete Geometrie und einen MMG-artigen Normalkraftansatz. | Das ist ein getesteter Prototyp, aber bewusst nur eine Näherung: Vorwärtsanströmung, horizontale Translation/Gierbewegung, höchstens ±10° effektiver Anstellwinkel und angenommene Ruderkinematik. |
| Produktionsintegration des Ruderansatzes | [`echtzeit_prozess.py`](../../../code/core/echtzeit_prozess.py) baut derzeit Hydrostatik plus konfiguriertes `Kraftmodell`. Der Ruderansatz wird dort nicht aufgerufen. | Die Tests beweisen isoliertes Verhalten, nicht das Verhalten der laufenden Yacht. |
| Konfiguration | [`konfig_lader.py`](../../../code/core/konfig_lader.py) lädt die aktuellen globalen Widerstands- und Added-Mass-Parameter. Die im Anleitungsvorschlag gezeigte `hydrodynamik`-Konfiguration ist kein aktuelles Schema. | Vor Einführung müssen Schema, Defaults, Validierung und Migrationsverhalten definiert werden. Keine stillen Defaults mit scheinbar physikalischer Bedeutung. |
| Kraftpfeile | [`kraftmodell.py`](../../../code/core/kraftmodell.py) führt benannte `Kraftbeitrag`-Wrenches und kann sie auf einen Bezugspunkt aggregieren. | Diese vorhandene Abstraktion sollte wiederverwendet werden; das Rendern eines eigenen Pfeils je Teil ist ein zusätzlicher GUI-Schritt und nicht bereits durch die Physikbeiträge garantiert. |

Die Aussage der Anleitung, es fehle „nur“ die Verknüpfung zwischen Rumpfform
und Koeffizienten, greift daher zu kurz: Es fehlen außerdem ein
wohldefinierter Kraftalgorithmus, die Integration in den Produktionspfad,
eine Lage-/Benetzungsstrategie, Konfigurationsregeln und Validierung am
Gesamtmodell.

## Unnummerierter Spezifikationsentwurf

### Vorgeschlagene Anforderungen

- Die dynamische Yacht erhält hydrodynamische Kraftbeiträge aus Rumpf,
  Kielsystem und Ruder. Rigg und Segel erzeugen in dieser Spezifikation keine
  hydrodynamischen Beiträge.
- Der erste Gültigkeitsbereich ist ruhiges Wasser und Verdrängungsfahrt ohne
  Wellen, Slamming und Gleiten. Das Modell unterstützt Vorwärtsfahrt,
  Rückwärtsfahrt, Seitwärtsfahrt, Abdrift und Gierbewegung, soweit die
  jeweiligen Näherungen fachlich festgelegt und getestet sind.
- Das Kraftmodell verwendet die lokale Relativgeschwindigkeit des jeweiligen
  Kraftangriffspunkts gegenüber dem Wasser. Sie berücksichtigt
  Körpertranslation, Winkelgeschwindigkeit, Bauteilposition und
  Fluidgeschwindigkeit. Frames und Vorzeichen sind an einer Stelle verbindlich
  definiert.
- Der Rumpf erzeugt einen längsgerichteten Widerstand und einen
  querbewegungsabhängigen Widerstand. Jeder Anteil wirkt dissipativ gegenüber
  der lokalen Wasserströmung. Vertikale Hydrostatik bleibt beim bestehenden
  Modell; eine hydrodynamische Heave-Erweiterung ist nur einzuschließen, wenn
  sie getrennt hergeleitet und geprüft ist.
- Kielsystem und Ruder erzeugen bei ausreichender Anströmung eine
  auftriebsartige Seitenkraft und einen dazugehörigen Widerstand. Die
  Kraftangriffspunkte führen über Hebelarme zu Momenten am Gesamtkörper. Beim
  Ruder ist der wirksame Anstellwinkel aus Ruderwinkel und lokaler Anströmung
  zu bestimmen; eine Wirkung der Giergeschwindigkeit ist explizit zu testen.
- Verhalten nahe Stillstand, bei sehr kleiner Reynolds-Zahl und an den Grenzen
  des Modellbereichs ist endlich, stetig und frei von unphysikalischen
  Kraftsprüngen. Außerhalb ausdrücklich unterstützter Bereiche wird ein
  ungeeigneter Zustand sichtbar abgelehnt oder kontrolliert begrenzt; er wird
  nicht als gültige Physik ausgegeben.
- Geometriekennwerte werden aus den bestehenden Bauteilmeshes und ihren
  Einbauposen abgeleitet. Die Daten benennen Teil, Frame, Einheiten,
  Annahmen und Modellstatus. Lageabhängige Benetzung wird entweder
  nachvollziehbar berechnet oder innerhalb eines dokumentierten
  Betriebsbereichs begründet angenähert.
- Keine Koeffizienten werden ohne Quelle, Herleitung oder ausdrücklich
  vereinbarte Kalibrierannahme als Yacht1-Realwerte ausgegeben. Ein
  Sensitivitätsparameter kann für Experimente dienen, ersetzt aber keine
  Kalibrierung.
- Die Hydrodynamik wird als benannte Kraftbeiträge mit Angriffspunkten an das
  bestehende Wrench-/Aggregationsmodell angeschlossen. Die Gesamtkräfte werden
  genau einmal an den 6-DOF-Integrator übergeben. Bestehendes Verhalten bleibt
  erhalten, wenn das neue Modul für andere Körper nicht konfiguriert ist.
- Die Echtzeitberechnung führt keine Mesh-I/O oder unnötige Mesh-Integration
  pro Zeitschritt aus. Vorbereitete Geometrie und etwaige Kennfeldwerte werden
  beim Modellaufbau erzeugt; Leistung und Genauigkeit werden gemessen.
- Die GUI kann die Teilbeiträge getrennt sichtbar machen. Diese Anzeige muss
  dieselben Kraftbeiträge und Angriffspunkte verwenden, die in die
  Dynamikrechnung eingehen.
- Der statische Solver bleibt zunächst ein hydrostatischer
  Lagegleichgewichtssolver. Eine stationäre Fahrtgeschwindigkeit ist kein
  Ziel dieser Spezifikation; sie erfordert zusätzlich eine Antriebsquelle und
  ein eigenes Gleichgewichtsproblem.

### Abnahmekriterien

- Stillstand und gleiche Geschwindigkeit wie das umgebende Wasser erzeugen
  keine hydrodynamische Kraft.
- Reiner Vorwärts- oder Rückwärtslauf ohne Antrieb erzeugt eine Kraft entgegen
  der Relativfahrt; eine dynamische Testfahrt baut den Betrag der
  Vorwärtsgeschwindigkeit über die Zeit ab, ohne Vorzeichen- oder
  Integrationssprung.
- Reine Seitwärtsfahrt erzeugt eine klar definierte quergerichtete
  Widerstandsreaktion. Eine Vorwärtsfahrt ohne Abdrift soll keine
  Kiel-Seitenkraft aus einem künstlichen Abdriftwinkel erhalten.
- Ein Ruderausschlag erzeugt bei Vorwärtsfahrt eine Seitenkraft mit
  dokumentierter Vorzeichenkonvention und ein Moment mit richtigem Hebelarm.
  Bei Ruderrückstellung und Gierbewegung entsteht ein stabilisierendes
  Giermoment im getesteten Betriebsbereich.
- Für jeden dissipativen Widerstandsbeitrag ist die Leistung relativ zum
  Wasser nicht positiv. Ein idealer Liftanteil wird getrennt geprüft, damit
  er nicht fälschlich als Widerstand oder Energiequelle wirkt.
- Kraft und Moment aus den Einzelbeiträgen stimmen mit der summierten Wrench
  überein; Transformation zwischen Körper- und Weltframe erhält diese
  Ergebnisse.
- Spiegelungs- und Vorzeichen-Tests prüfen Backbord/Steuerbord sowie positiven
  und negativen Ruderwinkel.
- Eine Referenzfahrt ohne Antrieb und eine Fahrt mit definierter Quer- oder
  Ruderanregung liefern reproduzierbare Kurven für Geschwindigkeit,
  Abdrift und Giergeschwindigkeit. Erwartungsbereiche sind vor Abnahme
  festzulegen; bloß „sieht plausibel aus“ reicht nicht.
- Der Echtzeitpfad bleibt mit aktivierter Hydrodynamik innerhalb des
  vereinbarten Rechenbudgets und behält seine Echtzeitsemantik.

## Weg zum Ziel

1. **Begriffe und Referenzen fixieren:** Achsen, Frames, Vorzeichen,
   Angriffspunkte, Wasserbewegung und Modell-Gültigkeitsbereich an einfachen
   Testkörpern festlegen. Für Yacht1 fehlende Maße und Ruderkinematik als
   Annahmen kenntlich machen.
2. **Zuerst ein überprüfbares Basismodell:** Den bestehenden globalen
   Widerstand als Vergleich behalten und einen längsgerichteten,
   dissipativen Widerstand für die Yacht konfigurieren oder herleiten.
   Messbare Geschwindigkeitsabnahme im dynamischen Lauf verifizieren, bevor
   weitere Kopplungen hinzukommen.
3. **Kraftbeiträge und Frames integrieren:** Ein gemeinsames Modul für lokale
   Anströmung und Wrench-Aggregation anlegen. Die schon vorhandene
   Ruder-Näherung nur hinter ihren Grenzen und mit ihrem Status einhängen;
   keine stillschweigende Erweiterung ihres Gültigkeitsbereichs.
4. **Bauteile schrittweise aktivieren:** Rumpf-Längswiderstand, Rumpf-
   Querwiderstand, Kiel-Seitenkraft und zuletzt Ruderwirkung getrennt
   hinzufügen. Nach jedem Schritt Tests und kontrollierte Yachtläufe
   auswerten.
5. **Benetzung und Koeffizienten kalibrieren:** Geometrieableitung und
   Wasserlinienänderungen gegen Mesh-Referenzen prüfen. Fehlende empirische
   Daten entweder beschaffen oder mit dem Nutzer als explizite
   Näherungsannahmen festlegen; Unsicherheit dokumentieren.
6. **Gesamtverhalten freigeben:** Kraftpfeile mit den berechneten Beiträgen
   verbinden und die Abnahmekriterien einschließlich Energie-, Symmetrie-,
   Langzeit- und Performance-Tests ausführen.
7. **Gleiten separat entscheiden:** Erst nach erfolgreicher Verdrängungsfahrt
   klären, ob Yacht1 tatsächlich im Zielbereich gleiten soll und welche Daten
   einen Gleit-Blend oder dynamischen Rumpfauftrieb stützen.

Die Anleitung sollte vor der Umsetzung entsprechend überarbeitet werden:
erst Frames, Gleichungen, Bereichsgrenzen und Datenquellen festlegen, dann
konkrete Module und Konfigurationsfelder spezifizieren. Der aktuelle Entwurf
trifft noch keine Entscheidung über reale Yacht1-Koeffizienten.
