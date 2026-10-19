# Genauigkeitsvorschläge für das Schulungstool zuV0.9

**Stand:** 19.10.2026  
**Fassung:** 1  
**Status:** Fassung 1 vollständig vom Nutzer freigegeben; bis Abschluss v0.9 gegen Lockerung gesperrt; noch kein Näherungspfad implementiert  
**Planbezug:** U-V0.9-000010  
**Anforderung:** A-V0.9-00009  
**Zugehöriger Plan:** [Umsetzungsplan zuV0.9](Umsetzungsplan_Echtzeit_und_Modellpakete_v0.9.md)

## Zweck und Geltungsbereich

Diese Vorlage legt die vom Nutzer freigegebenen Grenzen für einen
ausdrücklich gekennzeichneten Schulungs-Näherungsmodus fest. Sie definiert keine neue Anforderung und
ändert keine vorhandene numerische Regressionstoleranz. Die Werte sind
pädagogisch begründete Ausgangsvorschläge, keine aus Messungen abgeleiteten
Genauigkeitszusagen. Ob ein konkreter Näherungspfad sie einhalten kann und
welchen Geschwindigkeitsvorteil er bringt, muss gesondert geprüft werden.

Der vorgeschlagene Geltungsbereich umfasst qualitative Versuche zu
Auftrieb, Beladung, Krängung, Stampfen und gedämpfter Rückkehr zum
Gleichgewicht. Versuche werden mit identischen Modell- und Umweltparametern
gegen den bisherigen exakten Rechenpfad verglichen. Die Vorschläge sind
keine Freigabe für Aussagen über reale Bootsleistungen, Kentergrenzen,
Konstruktion oder Wettfahrtoptimierung.

Für den ersten Nachweis werden die geladenen Modellfassungen von Optimist,
Folkeboot und yacht1 festgehalten. Nach Änderungen ihrer Geometrie, Masse
oder Seglerposition sind betroffene Fälle erneut zu prüfen. Die geschätzten
Geometrie- und Massendaten dieser Modelle bleiben eine davon unabhängige
Unsicherheit: Übereinstimmung mit dem Referenzprogramm ist kein Nachweis der
Genauigkeit gegenüber einem realen Boot.

## Gemeinsame Definitionen und Prüfregeln

- `L` und `B` sind die explizit dokumentierte Rumpflänge und Rumpfbreite
  des geprüften Modellfalls in Metern, nicht die Gesamtmaße des Riggs.
- `m` ist die Gesamtmasse einschließlich eingestellter Seglermasse,
  `g` die im Test konfigurierte Erdbeschleunigung.
- `V0` ist das Referenz-Verdrängungsvolumen bei vollständig eingetauchten
  verdrängenden Bauteilen, ohne Doppelzählung von Überlappungen.
- `ref` bezeichnet den Wert des exakten Vergleichspfads. Vergleiche
  von Kräften und Momenten verwenden denselben Frame und Bezugspunkt.
- Die Prüfung gilt für jede Stichprobe; eine Einhaltung nur im Mittel
  oder im 95. Perzentil genügt nicht.
- Für Vektoren wird die euklidische Norm ihrer Differenz geprüft.
  Winkelorientierungen werden über den kleinsten Quaternion-
  Rotationsabstand verglichen, nicht über rohe Euler-Winkeldifferenzen.
- Exakte Implementierungsoptimierungen, Gesamtmasse, Schwerpunkt- und
  Trägheitsaggregation des Seglers sowie Persistenz bleiben bei ihren
  bisherigen numerischen bzw. funktionalen Kriterien.

## Empfohlener Grenzwertsatz

| Größe / Lernziel | Vorgeschlagene Grenze gegenüber Referenz | Begründung und Einschränkung |
|---|---|---|
| Eingetauchtes Volumen / zunehmender Auftrieb bei tieferem Eintauchen | `abs(ΔV) ≤ 0,001 · V0 + 0,02 · abs(Vref)` | 2 % relativer Anteil ist für qualitative Auftriebsversuche ein vertretbarer Startvorschlag; der kleine absolute Anteil behandelt Werte nahe null. Trocken und benetzt dürfen dadurch nicht verwechselt werden. |
| Auftriebskraft / Größenordnung der Tragwirkung | `norm(ΔF_A) ≤ 0,01 · m · g + 0,03 · norm(F_A,ref)` | Größenordnung soll erhalten bleiben; das kombinierte Budget vermeidet Division durch nahezu null. Kraft muss im benetzten Fall die richtige Richtung behalten. |
| Auftriebsmoment / Richtung der Rückstellwirkung | `norm(ΔM_A) ≤ 0,001 · m · g · B + 0,05 · norm(M_A,ref)` | Moment ist empfindlich gegenüber dem Kraftangriffspunkt. Ein größerer relativer Anteil ist vorgeschlagen, aber falsche Rückstellrichtung oder zusätzliches Gleichgewicht sind nicht zulässig. |
| Auftriebsschwerpunkt / Einfluss der Verdrängungsverteilung | `norm(ΔK) ≤ min(0,005 · L, 0,03 m)` für `Vref ≥ 0,05 · V0` | Bei geringer Benetzung ist der Schwerpunkt stark empfindlich; unterhalb dieser Schwelle werden Volumen, Kraft und Moment statt einer isolierten Schwerpunktgrenze geprüft. |
| Statischer Gleichgewichtszustand / Wirkung von Beladung | Höhenabweichung `≤ min(0,01 · L, 0,02 m)`; Orientierungsabweichung `≤ 1°` | Für die Schulung sollen die Schwimmlage und kleine Beladungsänderungen anschaulich bleiben. Die Richtung der Änderung nach Massenverschiebung muss mit der Referenz übereinstimmen. |
| Dynamische Lage / sichtbare Roll-, Nick- und Hubbewegung | Über 30 s Simulationszeit: Positionsabweichung `≤ min(0,02 · L, 0,05 m)` und Orientierungsabweichung `≤ 2°` | Begrenztes Zeitfenster für gleich gestartete Schulungsversuche; kein Anspruch auf langfristig präzise Bahnvorhersage. Es wird nach gleicher Simulationszeit verglichen, nicht nach gleicher Wandzeit. |
| Geschwindigkeit / Größenordnung der Bewegung | Im selben 30-s-Vergleich: `norm(Δv) ≤ 0,02 m/s + 0,05 · norm(vref)` | Kleine absolute Basis für den Stillstandsbereich und 5 % relativer Anteil für Bewegung. Keine Freigabe für Regatta- oder Leistungsprognosen. |
| Rückkehr bzw. Schwingung / verständliche Bewegungscharakteristik | Periodendauer und Abklingzeit jeweils höchstens 10 % Abweichung, wenn die Referenz eine eindeutig messbare Periode bzw. Abklingzeit besitzt | Messdefinition und Auswertefenster werden vor dem Kandidatenlauf festgelegt. Nicht schwingende oder nicht abklingende Referenzfälle erhalten kein erfundenes Maß. |

Die vorgeschlagenen Grenzen gelten gemeinsam. Das Bestehen einer Zeile
ersetzt nicht die übrigen Prüfungen. So darf beispielsweise ein noch
zulässiger Momentfehler nahe dem Gleichgewicht keine falsche
Rückstellrichtung erzeugen.

## Qualitative Kriterien ohne Lockerung

- Kein NaN/Inf, keine negative Masse oder negative eingetauchte Volumina.
- Keine zusätzlichen Eigenbewegungen oder Auftriebseffekte des Seglers.
- Kein Wechsel von trocken zu benetzt oder umgekehrt entgegen dem
  Referenzfall außerhalb ausdrücklich untersuchter Wasserlinien-Grenzfälle.
- Richtungswechsel, stabile/instabile Lage und Rückstellrichtung müssen
  erhalten bleiben. Bei sehr kleinen Referenzmomenten wird dies durch
  gezielte Störungen beiderseits des Gleichgewichts geprüft, nicht durch
  das Vorzeichen eines Rundungsrests.
- Kein Näherungsartefakt darf einen gedämpften Referenzfall in eine
  aufschaukelnde Bewegung umwandeln.
- Kleine, für das Lernziel bewusst gewählte Eingabeänderungen müssen
  erkennbar bleiben. Sind deren Referenzeffekte kleiner als das zugelassene
  Fehlerbudget, wird der exakte Modus verwendet oder die betreffende
  Näherung für dieses Lernziel nicht freigegeben.

## Vorab festzulegende Testfälle

1. **Hydrostatik:** trocken, vollständig eingetaucht, fünf gleichmäßig
   verteilte Teil-Eintauchlagen; Krängung `−20°, −10°, 0°, 10°, 20°`,
   Stampfen `−5°, 0°, 5°` und ausgewählte kombinierte Lagen.
2. **Wasserliniengrenzen:** kleine beidseitige Änderungen um Eintritt und
   Austritt jedes relevanten verdrängenden Bauteils. Die konkreten
   Höhenpositionen werden für die jeweilige Modellfassung vorab ermittelt
   und gespeichert.
3. **Beladung:** Referenzmasse und je ein vorher festgelegter leichterer
   bzw. schwererer Fall; Seglerverschiebung getrennt in x, y und z sowie
   Rückstellung auf die Ausgangsposition. Werte bleiben modellbezogen
   und werden nicht von einem Boot auf ein anderes übertragen.
4. **Dynamik:** gleiche Startzustände mit kleiner Roll-, Nick- und
   Höhenstörung; gleiche Umwelt und Zeitschritte, Vergleich nach gleicher
   Simulationszeit. Zunächst 30 s für die Bahn-/Lageabweichung, separate
   längere Läufe für Abklingen und numerische Stabilität.
5. **Fünfminütiger Echtzeitlauf:** zusätzlich Leistungs-/Bedienbarkeitsziele
   aus A-V0.9-00004 messen. Dieser Lauf ersetzt die numerischen
   Vergleichsfälle nicht.

Konkrete Referenzzustände, Massen, Seglerkoordinaten, Störungsgrößen,
Abklingdefinitionen und Stichprobenzeitpunkte sind vor dem Kandidatenlauf
festzuschreiben. Falls ein Referenzfall selbst scheitert, wird er als
blockiert dokumentiert und nicht als bestandener Vergleich ausgegeben.

## Alternativen zur empfohlenen Auswahl

- **Nur exakter Modus:** keine neue numerische Lockerung; reine
  Darstellungs- und Implementierungsoptimierungen. Geringstes
  Abweichungsrisiko, aber ungewisser erreichbarer Leistungsgewinn.
- **Empfohlener Schulungsmodus:** obiger Grenzwertsatz, alle qualitativen
  Kriterien und sichtbare Kennzeichnung „Schulungsnäherung“. Ausgewogenes
  Ziel für qualitative Versuche; Nutzen und Einhaltung noch zu messen.
- **Engerer Unterrichtsfall:** wenn der allgemeine Grenzwertsatz nicht
  tragfähig ist, nur ausgewählte Modelle oder Unterrichtsszenarien
  freigeben. Das ist einer pauschalen nachträglichen Lockerung vorzuziehen.

## Freigabeprotokoll

| Fassung | Entscheidung des Nutzers | Freigegebene Grenzen und Gültigkeit | Datum |
|---|---|---|---|
| 1 | Vollständig freigegeben | Alle Grenzen, Gültigkeitsbereiche und qualitativen Kriterien dieser Fassung; Lockerung bis Abschluss v0.9 ausgeschlossen | 19.10.2026 |

Die Freigabe erfolgte ausdrücklich mit der Auswahl „Fassung 1 vollständig
freigeben“. Der Nutzer hat ergänzend festgelegt:

> Weitere Aufweichung der Grenzwerte sind bis zum Abschluss von V0.9
> nicht zulässig. Auch durch mich nicht.

Damit darf U-V0.9-000003 diese Fassung als verbindliche Grundlage
übernehmen. Bis zum Abschluss v0.9 darf weder eine automatische noch eine
vom Nutzer gewünschte Lockerung angewendet werden. Dies gilt auch für die
qualitativen Kriterien und Gültigkeitsbedingungen; das Streichen eines
fehlgeschlagenen Prüffalls ist kein zulässiger Ersatz für das Bestehen.
Scheitert ein Kandidat, muss er verbessert oder nicht freigegeben werden.
Eine echte Einschränkung seines Einsatzbereichs wird ausdrücklich
dokumentiert, nicht als bestandene allgemeine Freigabe ausgegeben.
