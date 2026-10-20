# Kritische Bewertung der Idee zur Kraft- und Momentendarstellung

**Stand:** 20.10.2026  
**Status:** Diskussionsgrundlage, keine Spezifikation und keine Umsetzungsfreigabe  
**Quelle:** [BeispielSpecPfeile.md](BeispielSpecPfeile.md)

Die Kennungen in den Tabellen stammen unverändert aus der Idee. Die Spalte
„Kommentare“ bleibt für Nutzeranmerkungen leer.

**Legende:** ✅ übernehmen · 🟡 geändert übernehmen · ❌ nicht übernehmen

## Gesamturteil

Die Idee ist als Verbesserung der Kraft- und Momentendarstellung gut
geeignet, aber nicht unverändert zur Übernahme. Ihre größten Stärken sind
bessere Lesbarkeit, nachvollziehbare Momentenquellen und eine gemeinsame
Skalierung. Die größten Probleme liegen in der physikalisch falschen
Kopplung von Auftrieb und Gewicht, der Interpretation von Momentenachsen
und widersprüchlichen Skalierungsregeln.

Die Bewertung berücksichtigt die Idee und die vorhandenen
Darstellungsfunktionen. Die folgenden Empfehlungen legen weder eine
Spezifikation noch einen Umsetzungsplan fest.

## 1. Physik und Datenmodell

| Kennung | Bewertung | Kritische Einschätzung und Empfehlung | Kommentare |
|---|---|---|---|
| KO-01 | ✅ | SI-Einheiten und doppelte Genauigkeit beibehalten. Vier signifikante Stellen sind für kompakte Anzeigen sinnvoll; Detailanzeigen sollten zusätzliche Stellen ermöglichen. | OK |
| KO-02 | 🟡 | Welt- und Körperkoordinaten ausdrücklich unterscheiden. Keinen neuen festen Ursprung „Kielmitte“ einführen. Die bestehende Darstellung verwendet die Schwerpunktposition als Momentenbezug. Ein Wechsel würde Physik und Anzeige unnötig vermischen. | Physikalisch korrekter Drehpunkt erwünscht |
| KO-03 | 🟡 | Eindeutige Objektkennungen sind sinnvoll. Zusätzliche C-/S-/R-/B-Kennungen nicht als neues projektweites Anforderungsnummernsystem übernehmen. Vorhandene Pfeil-IDs möglichst erhalten. | OK |
| KO-04, C-02.3–4 | 🟡 | Vektoren als Datenquelle verwenden; Betrag und Richtung daraus ableiten. Nullkräfte und Nullmomente sind gültige Ergebnisse, auch wenn ihre Richtung nicht normierbar ist. Null, Vorzeichenwechsel sowie ungültige Werte benötigen unterschiedliche Behandlung. | OK |
| C-02 | 🟡 | Gemeinsame Darstellungsdaten für ID, Farbe, Sichtbarkeit und Beschriftung sind sinnvoll. Eine konkrete Vererbungshierarchie ist dafür nicht zwingend nötig. Physikdaten, Skalierung und VTK-Rendering getrennt halten. | sinnhafter vorschlag erwünscht|
| C-03 | 🟡 | Kraftpfeil mit eindeutigem Angriffspunkt und Richtung übernehmen. Die konkrete Klassenstruktur anhand der bestehenden Helfer entscheiden. |OK |
| C-04.1–3 | 🟡 | Momentenvektor und Bezugspunkt übernehmen. Normierte Achse plus gesonderter Drehsinn können redundant oder widersprüchlich werden. Besser: Momentenvektor als eindeutige Quelle; Drehsinn daraus ableiten. | OK |
| C-04.5–6 | 🟡 | Herkunft und Ableitungsart eines Moments explizit angeben. Eine leere Quellenliste beweist kein extern aufgeprägtes Moment; sie kann auch fehlende Zuordnung bedeuten. Quellen sollten fachliche Daten referenzieren, nicht zwingend sichtbare Pfeilobjekte. | ???Klären. Ggf.sollten wir beim eine Liste alle Kräfte und abgeleiteten Momente pflegen, hier könnten wir ggf. auch die Default-Layouts festlegen |
| C-05.1–4, B-03 | 🟡 | Fachliche Gruppierung und Gruppenfarben übernehmen. Gruppen sollten beliebig viele Kräfte und direkte Momentenbeiträge enthalten können, nicht immer genau Kraft, Gegenkraft und ein Moment. | Sollte es nicht immer eine Kraft und gegenkraft und ein MOment geben . wenn nicht gegenbeispiel erwünscht |
| C-05.5, C-05.7, B-01 | ❌ | Auftrieb ist keine automatisch gleich große Gegenkraft zur Gewichtskraft. Beide wirken auf dasselbe Boot und stammen aus unterschiedlichen Wechselwirkungen. Ihre Gleichheit ist ein besonderer Gleichgewichtsfall, keine allgemeine Kopplungsregel. | ja |
| C-05.8, B-02, B-05 | 🟡 | Momente konsistent aus denselben Simulationsdaten beziehen. Für eine allgemeine Gruppe gilt: Mₚ = Σ((rᵢ − p) × Fᵢ) + ΣMᵢ. Direkte Momentenbeiträge fehlen bislang. Änderungen an Richtung, Bezugspunkt oder direktem Moment müssen ebenfalls berücksichtigt werden. | siehe liste, hier sollten wir die Momentenkräfte paar festlegen. Die sollten doch immer gleich bleibne?|
| B-02: „nie gespeichert“, „jeder Frame“ | ❌ | Diese absolute Vorgabe nicht übernehmen. Abgeleitete Daten dürfen mit dem passenden Simulationsstand gespeichert oder zwischengespeichert werden. Wichtig sind Konsistenz und Herkunft, nicht ein Caching-Verbot. Die GUI darf keine zweite unabhängige Physikberechnung etablieren. | Ok|
| B-04 | ✅ | Eigenständige Kraft- und Momentenbeiträge ohne künstliche Gegenkraftgruppe zulassen. |  Das verstehe ich nicht. Wir dürfen nur mit den bekannten Kräftenarbeiten. Wenn eine Kraft fehlt müsssen wir die einführen.|

Ein dargestelltes Moment beschreibt nicht automatisch eine tatsächliche
Drehachse oder einen festen Drehpunkt. Ein Kräftepaar besitzt ein vom
Bezugspunkt unabhängiges Moment; bei einer resultierenden Kraft ist das
Gesamtmoment dagegen bezugspunktabhängig.

## 2. Skalierung und Lesbarkeit

| Kennung | Bewertung | Kritische Einschätzung und Empfehlung | Kommentare |
|---|---|---|---|
| C-01, getrennte Kraft-/Momentenskalen | ✅ | Gemeinsame Vergleichsskalen je physikalischer Größe sind sinnvoll: Newton und Newtonmeter dürfen nicht dieselbe Skala teilen. | OK |
| C-01: genau zwei Instanzen pro Szene | 🟡 | Gemeinsame Skalierungsregeln festlegen, nicht zwingend exakt zwei Objekte. Bei mehreren Ansichten oder bewusst getrennten Vergleichsgruppen kann mehr als eine Skala sinnvoll sein. | ja, so, oder halt logarithmisch|
| C-01.1, C-01.6 | 🟡 | Manuelle beziehungsweise fixierte Skala anbieten. Nur sichtbare Pfeile für Auto-Range zu verwenden bedeutet: Ausblenden eines Pfeils verändert die übrigen Pfeillängen. Das erschwert Vergleiche und sollte bewusst wählbar sein. | OK, |
| C-01.2–5, S-01 | 🟡 | Logarithmische Skalierung als optionalen Darstellungsmodus übernehmen. Nullwerte, identische Min-/Max-Werte, Werte außerhalb der Grenzen und sehr kleine Kräfte definieren. Begrenzte Abbildungen sind nicht überall „strikt monoton“. | Gut , schlage eine bessere Lösung vor|
| S-02 | 🟡 | Betragsabhängige Dicke höchstens ergänzend verwenden. Eine ausreichend konstante Mindestdicke verbessert Lesbarkeit; dünne Pfeile dürfen nicht verschwinden. Länge und Dicke gleichzeitig nach Betrag zu verändern verstärkt Unterschiede visuell. | |
| S-03 | 🟡 | Konstanter Momentenradius ist gut für ruhige Darstellung. Momentengrößen nur durch 1–4 Pixel Dicke zu unterscheiden ist aber schwach. Zahlenanzeige und Legende benötigen hier besonderes Gewicht. | weiß ich auch nicht |
| S-04 | 🟡 | Hysterese übernehmen, aber vollständig definieren: Erweiterung, verzögertes Verkleinern, Ausreißer und manuelles Einfrieren. „20 % außerhalb“ allein löst diese Fälle nicht. | schlage lösung vor|
| S-05 | 🟡 | Zahlenwerte immer zugänglich machen, nicht zwingend alle dauerhaft einblenden. „Exakte Werte“ durch „numerische Werte mit ausgewiesener Rundung“ ersetzen. | OK  |
| I-03 | ✅ | Linear/Log umschaltbar; abgeschnittene Werte sichtbar kennzeichnen. Die Kennzeichnung sollte auch für Begrenzungen im Log-Modus gelten. | ggf. gibt es eine noch besser Lösung. |

Empfehlung: Für vergleichende Analysen zunächst eine fixierbare lineare
Skala erhalten; Logarithmik als zusätzliche Übersicht für sehr
unterschiedliche Größen anbieten.

## 3. Rendering und Bedienung

| Kennung | Bewertung | Kritische Einschätzung und Empfehlung | Kommentare |
|---|---|---|---|
| R-01 | ✅ | Angriffspunkt, Richtung und Pfeilspitze eindeutig darstellen. Ein zusätzliches Punktsymbol bei Bedarf ausblendbar machen. | |
| R-02 | 🟡 | Bildschirmstabile Pfeilköpfe sind sinnvoll, aber Kameradistanz, Perspektive, Fenstergröße und DPI beachten. Entlang der Blickrichtung kann ein 3D-Pfeil trotzdem stark verkürzt erscheinen. | richtig|
| R-03 | 🟡 | Gruppenfarbe übernehmen, aber nicht ausschließlich auf Farbe setzen. Beschriftung und unterscheidbare Linienarten erhalten. Bestehende individuelle Farboptionen nicht unbeabsichtigt entfernen. |muss aber definiert sein, sieh tabelle |
| R-04 | 🟡 | Bogenpfeile und Rechte-Hand-Regel übernehmen. 270° nicht zwingend festschreiben; der vorhandene Code verwendet 240°. Ein Wechsel braucht einen tatsächlichen Lesbarkeitsvorteil. | OK |
| R-05 | 🟡 | Optional eine Linie parallel zum Momentenvektor anzeigen. Als Momentenrichtung beziehungsweise Bezugsachse kennzeichnen, nicht pauschal als tatsächliche Drehachse. | Hebelarm und Drehpunkt. Lass uns erst mal über die 3D -Darstellung reden, ggf. kommen später noch ableitungen in 2D dazu|
| R-06, I-01 | ✅ | Quellen hervorheben, Hebelarme und Einzelbeiträge erklären. Bezugspunkt, resultierende Kraft und direkte Momentenbeiträge dabei berücksichtigen. | |
| R-07 | 🟡 | Größere Auswahlfläche übernehmen. „12 px“ als erprobbaren Startwert behandeln; DPI und überlappende Treffer berücksichtigen. Eindeutige Auswahlregel statt beliebiger Trefferauswahl. | |
| R-08 | 🟡 | Legende übernehmen. Bei einer Log-Skala reicht ein einzelner Maßstabsbalken nicht: mehrere Referenzwerte und die Kennzeichnung „logarithmisch“ zeigen. |ein eigenens, zunächst als mockup, freifliegendes Menu, welches gruppiert alle Kräfte und Summen und momente, ggf. auch angriffpunkt am Objekt ausgibt mitdenken |
| R-09 | ❌ | Nicht als feste Regel übernehmen. Ohne gegenseitigen Tiefentest entsteht keine verlässliche räumliche Reihenfolge; überlappende Pfeile bleiben trotzdem überlagert. Den bestehenden Vordergrundmodus erhalten und eine normale räumliche Darstellung anbieten. | |
| I-02 | ❌ | Automatische Auftrieb-/Gewichtskopplung und deren Bearbeitungssperre entfallen. Anklicken einer Darstellung sollte nicht automatisch das Editieren berechneter Simulationskräfte erlauben. | |

## 4. Prüfung der Beispielwerte

| Kennung | Bewertung | Befund und Empfehlung | Kommentare |
|---|---|---|---|
| E-01–02 | ✅ | Als Testwerte für Kraft- und Momentenskalen geeignet, nicht als allgemeine Standardbereiche aller Boote. | |
| E-03–05 | 🟡 | Gleiche Kräfte ausdrücklich als angenommenen Gleichgewichtsfall behandeln. Nicht durch eine automatische Kopplung erzeugen. | |
| E-06: Momentenberechnung | 🟡 | Aus den angegebenen Weltkoordinaten folgt um G: (0,10; 0,35; −0,30) m × (0; 0; 49,05) kN = (17,1675; −4,905; 0) kN·m. Es entsteht zusätzlich ein y-Moment. Dieses zeigen oder den x-Versatz für ein reines Rollbeispiel entfernen. | |
| E-06: Bezeichnung | 🟡 | Aufrichtendes, krängendes und gesamtes Rollmoment fachlich unterscheiden. Ob das positive x-Moment aufrichtend wirkt, lässt sich ohne eindeutig festgelegtes Krängungsvorzeichen nicht entscheiden. | |
| E-07 | 🟡 | Ein unabhängiger Momentenbeitrag ist ein gutes Beispiel. Ein reines Moment „durch F“ beweist aber keinen dort liegenden Drehpunkt. Wellenerregung nicht ohne vorhandene Datenquelle als reale Physik voraussetzen. | |
| Skalierungsprobe | 🟡 | Die gerundeten Dickenwerte sind korrekt: etwa 3,24 px für 17,17 kN·m und 2,90 px für 8 kN·m. Widersprüchlich ist der Vergleich von Momentenlängen, obwohl S-03 einen konstanten Radius vorsieht. Das Beispiel an ein eindeutiges Kodierungskonzept anpassen. | |
| Abschließende Annahme „natürliche Kopplung“ | ❌ | Die behauptete physikalische Kopplung von Auftrieb und Gewicht streichen. | |

**Korrektur gegenüber der ersten Chatbewertung:** Dort wurden die
gerundeten Dickenwerte irrtümlich als falsch bezeichnet. Sie stimmen mit
S-02 überein. Die Kritik an den Momentenlängen bei gleichzeitig konstantem
Bogenradius bleibt bestehen.

## 5. Vorhandenen Code nutzen

| Bestehender Baustein | Vorhandener Nutzen und Empfehlung | Kommentare |
|---|---|---|
| [pfeilstil.py](../../../../code/python/segelphysik/core/pfeilstil.py) | Pfeilregister, Gruppenfarben, Sichtbarkeit und individuelle Einstellungen erhalten und gezielt erweitern. | |
| [kraefte_bild.py](../../../../code/python/segelphysik/core/kraefte_bild.py) | Kraftpfeile, Momentenbögen, Kreuzprodukte und Skalierung; teilweise bereits mit nativen Rechenpfaden. Bestehende Helfer und Verträge als Ausgangspunkt verwenden. | |
| [grafik_bruecke.py](../../../../code/python/segelphysik/grafik_bruecke.py) | Darstellung, Geometrie-Caching, Momentenkomponenten und separater Vordergrundrenderer sind vorhanden. Keine komplette neue Klassenwelt parallel aufbauen. | |

Vorhandene IDs, Einstellungen, Caches und native Verträge sollten
Ausgangspunkt der Weiterentwicklung sein.

## 6. Frei verfügbare Bausteine und bewährte Ansätze

Die allgemeine Websuche war bei der Bewertung technisch nicht verfügbar.
Die folgenden Möglichkeiten wurden direkt anhand offizieller
Dokumentation geprüft. Es wurde kein fertiges Gesamtpaket für genau die
vorgeschlagene Kraft-/Momentenbedienung nachgewiesen.

| Baustein / Quelle | Nutzen und Grenze | Kommentare |
|---|---|---|
| [VTK vtkDistanceToCamera](https://vtk.org/doc/nightly/html/classvtkDistanceToCamera.html) | Liefert Skalierungsdaten für gewünschte Bildschirmgrößen. Baustein für kamerabhängige Glyphengrößen; löst nicht automatisch getrennte Schaft-/Kopfskalierung. | |
| [VTK vtkGlyph3DMapper](https://vtk.org/doc/nightly/html/classvtkGlyph3DMapper.html) | Kandidat für viele wiederverwendete Pfeilgeometrien. Bei messbarem Bedarf einsetzen, nicht allein wegen einer vermeintlich schnelleren Architektur. | |
| [PyVista-Glyph-Beispiele mit herunterladbarem Python-Code](https://docs.pyvista.org/examples/01-filter/glyph.html) | Frei zugängliche Beispiele für Orientierung und Skalierung von Pfeilen. Kein fertiges Kraft-/Momentenmodell. Vor Codeübernahme die Lizenz des konkreten Beispiels beachten. | |
| [VTK vtkArcSource](https://vtk.org/doc/nightly/html/classvtkArcSource.html) | Kreisbögen mit Normalenvektor und Winkel; passend für beliebig orientierte Momentenbögen. Bestehende Bogenhelfer zuerst prüfen. | |
| [PyVista Picking](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.Plotter.enable_point_picking.html) | Vorhandene Auswahlmechanismen nutzen. Die dokumentierte Toleranz ist bei unterstützten Pickern ein Anteil der Fensterdiagonale, keine direkte Pixelangabe. | |
| [VTK-Projektbeschreibung und Lizenzhinweis](https://vtk.org/about/) | VTK ist unter einer BSD-artigen Lizenz frei nutzbar. Eine zusätzliche große Grafikbibliothek ist für diese Idee nicht nötig. | |

## 7. Empfohlene Prioritäten

| Priorität | Empfehlung | Kommentare |
|---|---|---|
| 1 | Physikalisch korrekte Daten und eindeutige Bezugspunkte sicherstellen. | |
| 2 | Vorhandene Darstellung um Zahlenwerte, Legende und Quellenhervorhebung verbessern. | |
| 3 | Fixierbare gemeinsame Skalen erhalten; Log-Modus optional ergänzen. | |
| 4 | Bildschirmstabile Größen und komfortables Picking gezielt erproben. | |

Insbesondere nicht übernehmen: künstliche Auftrieb-/Gewichtskopplung,
Gleichsetzung von Momentenlinie und tatsächlicher Drehachse sowie ein
pauschaler Architektur-Neubau.
