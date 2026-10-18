# Umsetzungsplan: Navigationswidgets v0.7

**Stand:** 18.10.2026<br>
**Zugehörige Spezifikationen:**
[Navigationswidgets v0.7](../Spezifikationen/Spezifikation_Navigationswidgets_v0.7.md),
[Weltsystem, Umwelt und Körperbewegung v0.7](../Spezifikationen/Spezifikation_Weltsystem_Bewegung_v0.7.md),
[Konzept Navigationsanzeigen v0.7](../Spezifikationen/Konzept_Navigationsanzeigen_v0.7.md)<br>
**Status:** Umsetzung implementiert und automatisiert verifiziert;
Desktop-Abnahme (M5/M6) und Produktivfreigabe stehen aus<br>
**Geltungsbereich:** Erste Laufzeitstufe für Kompass, Krängung und Stampfen
einschließlich Snapshot-Anbindung, Anzeigeoptionen und frei schwebendem
Widgetfenster.

## 0. Zweck und verbindliche Grenzen

Dieser Plan ordnet die Umsetzung in abhängige, einzeln prüfbare Arbeitspunkte
und Freigabemeilensteine. Es gibt für diesen Umfang nur diesen einen
Umsetzungsplan. `NAV-NNNN` sind dauerhafte, in diesem Dokument eineindeutige
Arbeitspunktkennungen. Bestehende Kennungen bleiben bei späteren Änderungen
erhalten; neue Arbeitspunkte erhalten bisher unbenutzte Nummern. Die
`SpecNNNN`-Kennungen verweisen auf Anforderungen und werden nicht durch
Arbeitspunktkennungen ersetzt.

Verbindlich sind folgende Grenzen:

- Die drei Quelldateien
  [Widget_Kompass.svg](../Widgets/Widget_Kompass.svg),
  [Widget_Krängung.svg](../Widgets/Widget_Kr%C3%A4ngung.svg) und
  [Widget_Stampfen.svg](../Widgets/Widget_Stampfen.svg) bleiben bytegenau
  unverändert. Laufzeitänderungen sind ausschließlich an flüchtigen
  Renderinstanzen zulässig.
- Physikzustand und Körperorientierung bleiben unverändert. Anzeigegrößen
  werden aus einem gemeinsamen, konsistenten Snapshot abgeleitet.
- Die erste Interface-Stufe umfasst Messwerte, Gültigkeit,
  Nebenwerte und die spezifizierten gemeinsamen Sichtbarkeitsoptionen. Sie
  enthält keine benutzerdefinierten Texte und keine freien oder nummerierten
  Layoutparameter.
- Die Zwischenlösung ist ein separates, frei bewegliches Fenster mit allen
  drei Widgets gleichzeitig in der festen Reihenfolge Kompass, Krängung,
  Stampfen.
- Ein nicht verfügbarer Wert wird niemals durch `0°`, einen anderen gültigen
  Ersatzwert oder einen scheinbar normalen Zustand kaschiert.
- Umwelt-/Fahrtanzeigen (`Spec0080`–`Spec0082`), die Implementierung der
  Gelenkkinematik (`Spec0083`, `Spec0085`, `Spec0086`) und die langfristige
  Zielkomposition weiterer Instrumentkarten aus `Spec0087` sind keine
  Implementierungsziele dieses Plans. Ihre Verträge bleiben unberührt; die
  Rückverfolgbarkeitstabelle kennzeichnet ihre Prüfung als Voraussetzung,
  Regression oder ausdrücklich außerhalb des Umfangs.
- Der Plan und seine Quellen bleiben auf Dokumente und Assets innerhalb
  von `zuV0.7` beschränkt.

## 1. Spezifikationsumfang und Rückverfolgbarkeit

Jeder nummerierte Punkt der beiden formalen v0.7-Spezifikationen ist hier
zugeordnet. Anforderungen aus dem nicht nummerierten Konzept sind in der
anschließenden Konzeptmatrix erfasst. „Außerhalb“ bedeutet, dass die
Anforderung in diesem Widget-Vorhaben nicht implementiert wird; sie wird
dadurch nicht verworfen oder inhaltlich geändert.

| Spezifikationspunkt | Planbezug und Behandlung |
|---|---|
| `Spec0067` | `NAV-0002`, `NAV-0004`–`NAV-0005`: Frames, Einheiten und Vorzeichen für angezeigte Winkel einhalten und testen. |
| `Spec0068` | `NAV-0001`–`NAV-0002`: lokales Nord verwenden; keine geografische oder magnetische Referenz einführen. |
| `Spec0069` | `NAV-0001`–`NAV-0002`: Umwelt-, Körper- und Gelenkzustand getrennt halten; keine bestehende Physik ersetzen. |
| `Spec0070` | `NAV-0002`: Weltachsen und Rechtshändigkeit als Basis der Richtungsableitung prüfen. |
| `Spec0071` | `NAV-0002`: Körperachsen und level-Nord-Referenz für die Winkelableitung prüfen. |
| `Spec0072` | `NAV-0001`: Teilframes als bestehenden Modellvertrag berücksichtigen; neue Teilkinematik ist außerhalb des Umfangs. |
| `Spec0073` | `NAV-0002`: Welt-/Körpertransformationen und freie Vektoren korrekt behandeln. |
| `Spec0074` | `NAV-0002`, `NAV-0004`–`NAV-0005`: intern rad, GUI-Winkel in Grad. |
| `Spec0075` | `NAV-0002`: lokale Vertikale und Horizontprojektion für Winkel und Kamera verwenden; ungültige Schwerkraft nicht kaschieren. |
| `Spec0076` | `NAV-0001`: gemeinsame Umweltquelle und Standardströmung als Bestand prüfen; Umweltmodellierung selbst ist außerhalb des Umfangs. |
| `Spec0077` | `NAV-0001`, `NAV-0007`: ausgewählten Körperzustand und seinen Snapshot verwenden; keine unabhängigen Umweltkopien anlegen. |
| `Spec0078` | `NAV-0002`, `NAV-0004`–`NAV-0005`: Quaternion bleibt autoritativ; `HDG`, `φ`, `θ` und Singularitäten gemäß Vertrag behandeln. |
| `Spec0079` | `NAV-0007`: Körperwechsel darf keine Pose oder Werte eines anderen Körpers übernehmen. |
| `Spec0080` | `NAV-0001`: Begriffs-/Einheitenvertrag für vorhandene Messwerte bewahren; übrige Umwelt- und Fahrtdatenanzeigen sind außerhalb des Umfangs. |
| `Spec0081` | `NAV-0001`, `NAV-0009`: Geschwindigkeits- und Windformeln nicht verändern; vollständige Umwelt-/Bewegungsberechnung ist außerhalb des Umfangs. |
| `Spec0082` | `NAV-0001`, `NAV-0009`: Vektoraddition nicht durch skalare Fahrtrechnung ersetzen; keine Umsetzung einer Fahrtanzeige in diesem Vorhaben. |
| `Spec0083` | `NAV-0001`: vorhandene Gelenktransformationen nicht ändern; Implementierung neuer Gelenkkinematik ist außerhalb des Umfangs. |
| `Spec0084` | `NAV-0001`, `NAV-0005`: Segeltrim nur als Spiegelungseingang verwenden; Vorzeichen testen, fehlend/null/negativ bedeutet Backbord. Keine neue Trimkinematik. |
| `Spec0085` | `NAV-0001`, `NAV-0009`: Rudervertrag unberührt lassen; Ruderkinematik ist außerhalb des Umfangs. |
| `Spec0086` | `NAV-0001`, `NAV-0009`: Schwertvertrag unberührt lassen; Schwertkinematik ist außerhalb des Umfangs. |
| `Spec0087` | `NAV-0004`–`NAV-0008`: Anzeige-, Snapshot-, Einheiten- und Sichtbarkeitsverträge für den Widgetumfang umsetzen; spätere Instrumentkarten bleiben außerhalb des Umfangs. |
| `Spec0088` | `NAV-0002`, `NAV-0004`–`NAV-0006`, `NAV-0009`: relevante Frame-, Winkel-, Fehler- und Einstellungsnachweise ausführen; Umwelt- und Stellwerttests bleiben Regressionen des bestehenden Systems. |
| `Spec0089` | `NAV-0001`, `NAV-0009`: Umwelt-/Bewegungstests nicht als neue Funktion implementieren; bestehende Regressionen laufen, sofern betroffen. |
| `Spec0090` | `NAV-0001`, `NAV-0009`: Stellwert-/Gelenktests nicht als neue Funktion implementieren; bestehende Regressionen laufen, sofern betroffen. |
| `Spec0091` | `NAV-0001`–`NAV-0009`: Modellmapping vor Codeintegration und die dort festgelegte Reihenfolge/Gates einhalten; gesperrte Physikerweiterungen nicht freigeben. |
| `Spec0092` | `NAV-0001`–`NAV-0002`, `NAV-0004`–`NAV-0005`, `NAV-0009`: Kameraazimut, Offset, Elevation, Horizontstabilität und Fehlerbehandlung abbilden und testen. |
| `Spec0093` | `NAV-0003`, `NAV-0005`, `NAV-0009`: Lagewidgetgeometrie, Referenzachsen, gekoppelte Pose und Vorzeichen unverändert umsetzen und prüfen. |
| `Spec0094` | `NAV-0001`, `NAV-0009`: dauerhafte Kennungen im gesamten v0.7-Umfang beibehalten; jede Spezifikationskennung bis Arbeitspunkt, Test, Meilenstein oder begründeter Umfangsgrenze verfolgen. |
| `Spec0095` | `NAV-0003`–`NAV-0005`, `NAV-0009`: drei Widget-SVG-Quellen bytegenau erhalten; nur flüchtige, spezifizierte Renderinstanzen aktualisieren. |
| `Spec0096` | `NAV-0002`, `NAV-0006`–`NAV-0007`: Snapshot, Validität und getrennte Interfacephasen einhalten. |
| `Spec0097` | `NAV-0004`: Kompassfunktion ausführen. |
| `Spec0098` | `NAV-0002`, `NAV-0004`: Kompassdateninterface aus demselben Snapshot speisen. |
| `Spec0099` | `NAV-0006`: Kompass-Sichtbarkeit ohne freie Texte oder Layoutparameter steuern. |
| `Spec0100` | `NAV-0005`: Krängungsfunktion, posegekoppelte Yacht und Gefahren-/Fehlerzustand umsetzen. |
| `Spec0101` | `NAV-0002`, `NAV-0005`: Krängungswinkel, Segelseite und Kameraprojektion als getrennte Eingänge behandeln. |
| `Spec0102` | `NAV-0006`: Krängungsanzeigeoptionen gemäß gemeinsamer Sichtbarkeit umsetzen. |
| `Spec0103` | `NAV-0005`: Stampfenfunktion, Pose und Gefahren-/Fehlerzustand umsetzen. |
| `Spec0104` | `NAV-0002`, `NAV-0005`: Stampfenwinkel und projizierte Kamera aus demselben Snapshot beziehen. |
| `Spec0105` | `NAV-0006`: Stampfenanzeigeoptionen gemäß gemeinsamer Sichtbarkeit umsetzen. |
| `Spec0106` | `NAV-0003`–`NAV-0009`: definierte SVG-, Snapshot-, Status-, Einstellungs- und Integrationsprüfungen ausführen. |
| `Spec0107` | `NAV-0008`: separates Fenster und feste Reihenfolge Kompass, Krängung, Stampfen umsetzen. |
| `Spec0108` | `NAV-0002`, `NAV-0005`, `NAV-0009`: Kamerastandpunkt in Lageansichten projizieren; null/ungültige Projektionen nicht ersetzen. |
| `Spec0109` | `NAV-0001`, `NAV-0003`, `NAV-0009`: alle vier Spezifikationsgrafiken gegen ihren Textvertrag und ihre Tests abgleichen; grafische Beispiele sind keine Laufzeitwerte. |
| `Spec0110` | `NAV-0009`: langfristige Vier-Karten-Zielanordnung und gemeinsame Elementgestaltung dokumentiert; keine Umsetzung in der ersten Widgetstufe. |
| `Spec0111` | `NAV-0009`: Anforderungen an die spätere Grundbewegungskarte nachvollziehen; außerhalb des Implementierungsumfangs. |
| `Spec0112` | `NAV-0009`: Anforderungen an die spätere Wasserbewegungskarte nachvollziehen; außerhalb des Implementierungsumfangs. |
| `Spec0113` | `NAV-0009`: Anforderungen an die spätere Windkarte und deren Nichtverfügbarkeitszustand nachvollziehen; außerhalb des Implementierungsumfangs. |

Die Zielkomposition mit Grund-, Wasser- und Windkarten sowie die
Master-Elementbibliothek sind für die spätere Instrumentstufe dokumentiert
und werden nicht als zusätzliche Laufzeitwidgets in diesem Plan umgesetzt.
Die Mastergrafik bleibt gleichwohl die visuelle Referenz; gemeinsame
Elementgestaltung und stabile Elementnamen dürfen durch diese Zwischenstufe
nicht abweichen.

Alle Anforderungen aus dem Konzept sind in der formalen Spezifikation
verankert und werden wie folgt nachverfolgt. Herstellerbeispiele und
Quellenangaben im Konzept sind ausschließlich Hintergrund und keine
umzusetzenden Anforderungen.

| Konzeptanforderung | Spezifikations-ID | Planbezug und Behandlung |
|---|---|---|
| Zwischenlösung: drei Widgets im separaten Fenster, 3D-Szene bleibt im Hauptfenster | `Spec0107` | `NAV-0008`: Fenster und Lebenszyklus umsetzen und testen. |
| Gemeinsamer nummerierter Master, konsistente gemeinsame Kartengestaltung und Ausblenden nicht verwendeter Elemente | `Spec0087`, `Spec0110` | `NAV-0003`–`NAV-0005`, `NAV-0009`: Master und stabile Elementsemantik beibehalten. |
| Kompasskarte: Titel/Beschreibung, Rose, Teilstriche, Kardinalbeschriftung, Abstände, Zeiger, Kameraelement, digitales Feld, Sektorgrenzen und keine geografische Referenz | `Spec0087`, `Spec0092`, `Spec0095`, `Spec0097`–`Spec0099` | `NAV-0002`–`NAV-0004`, `NAV-0009`: Darstellung und Verhalten samt Grenztests abnehmen. |
| Zukünftige Grundbewegungskarte: `SOG`/`COG`, Richtungsscheibe zeigt `COG` | `Spec0080`–`Spec0081`, `Spec0111` | `NAV-0009`: Anforderung nachvollziehen; Karte selbst liegt außerhalb dieser Laufzeitstufe. |
| Zukünftige Wasserbewegungskarte: `STW`/`CTW`/`λ`, unterscheidbare Wasserreferenz und Vorzeichen | `Spec0080`–`Spec0082`, `Spec0112` | `NAV-0009`: Anforderung nachvollziehen; Karte selbst liegt außerhalb dieser Laufzeitstufe. |
| Zukünftige Windkarte: `TWS`/`TWD`/`AWS`/`AWA`/`TWA`, keine künstlichen Nullwerte bei fehlendem Wind | `Spec0076`, `Spec0080`–`Spec0081`, `Spec0087`, `Spec0113` | `NAV-0009`: Anforderung nachvollziehen; keine Windkarte oder Ersatzwerte in der ersten Stufe. |
| Mockup-Zahlen, Vektoren und Yachtformen sind illustrativ, keine Laufzeit-/Startwerte | `Spec0087`, `Spec0095`, `Spec0109` | `NAV-0003`, `NAV-0009`: Originalwerte nicht als Simulationsdaten verwenden. |
| Einzelgrafiken: gemeinsame Kartenbasis, Yachtansichten, Pose, Referenzachsen und Statusfarben | `Spec0093`, `Spec0095`–`Spec0106` | `NAV-0003`–`NAV-0006`, `NAV-0009`: SVG-Integrität und Darstellung testen. |
| Messgrößen, Bezugsrahmen und Richtungsauflösung | `Spec0070`–`Spec0082`, `Spec0087`–`Spec0089` | `NAV-0001`–`NAV-0002`, `NAV-0009`: Datenvertrag erhalten; nur die drei spezifizierten Widgetwinkel implementieren. |
| Eigene Qt-Widgetklassen und stabile semantische SVG-Elementnamen | `Spec0087`, `Spec0095` | `NAV-0001`, `NAV-0003`–`NAV-0005`: Integrations- und Elementbindung prüfen. |
| Vier unabhängige globale Sichtbarkeitseinstellungen und Fehler-Vorrang | `Spec0087`, `Spec0096`, `Spec0099`, `Spec0102`, `Spec0105` | `NAV-0006`: Optionen, Migration und Fehlerzustand testen. |
| Gemeinsamer unveränderlicher Snapshot, aktueller GUI-Updatepfad, getrennte Wertfelder und kein Blockieren der Physik | `Spec0087`, `Spec0096`, `Spec0106` | `NAV-0002`, `NAV-0007`, `NAV-0009`: Snapshotkonsistenz und nicht blockierende Updates prüfen. |
| Kameramarker am Kompass und horizonstabile Kamera, deren Bootsneigung sichtbar bleibt | `Spec0092`, `Spec0097`–`Spec0098`, `Spec0108` | `NAV-0002`, `NAV-0004`–`NAV-0005`, `NAV-0009`: Kopplung und Projektionen testen. |
| Werte des ausgewählten Körpers; gemeinsame Welt-/Umweltwerte bleiben beim Körperwechsel konsistent | `Spec0077`, `Spec0079`, `Spec0087`, `Spec0096` | `NAV-0007`: Körperwechsel und gemeinsamer Snapshot testen. |
| Einzelne sichtbare Elemente, Fenstergröße und gleichzeitige Verfügbarkeit aller drei Widgets | `Spec0087`, `Spec0107` | `NAV-0006`, `NAV-0008`: Sichtbarkeit und Resize/Lifecycle testen. |
| Fehler, Gefahr, ungültige Nebenwerte und unverfügbare Richtungen ohne Ersatz-Nullwerte | `Spec0081`, `Spec0087`–`Spec0088`, `Spec0096`, `Spec0100`–`Spec0106`, `Spec0108` | `NAV-0002`, `NAV-0004`–`NAV-0006`, `NAV-0009`: jeweilige gültige/ungültige Zustände testen. |
| Konzept-Abnahme: `HDG`, Kompassrose und Zeiger verwenden dieselbe Nordreferenz und denselben Snapshot | `Spec0075`, `Spec0078`, `Spec0096`–`Spec0098` | `NAV-0002`, `NAV-0004`, `NAV-0007`, `NAV-0009`: Quelle, Richtung und Updatekonsistenz nachweisen. |
| Konzept-Abnahme: Kompassstriche, Kardinalpunkte, Richtungstext und Zeigerüberdeckung | `Spec0087`, `Spec0097`–`Spec0098` | `NAV-0004`, `NAV-0009`: Sektorgrenzen automatisiert und Layout visuell prüfen. |
| Konzept-Abnahme: äußerer Kameramarker folgt `KAM_AZ` und zeigt nach innen | `Spec0092`, `Spec0095`, `Spec0097`–`Spec0098` | `NAV-0003`–`NAV-0004`, `NAV-0009`: Elementbindung und Azimut prüfen. |
| Konzept-Abnahme: Kamera folgt dem Gieren, bleibt bei Elevation/Roll horizonstabil | `Spec0092` | `NAV-0002`, `NAV-0009`: Poseänderungen und Horizontbezug testen. |
| Konzept-Abnahme: Kamerarahmen-Grafik erklärt Draufsicht, Elevation und sichtbare Bootsneigung | `Spec0092`, `Spec0109` | `NAV-0001`, `NAV-0009`: Grafik und Textvertrag abgleichen. |
| Konzept-Abnahme: Grund- und Wasserbewegungskarten bleiben getrennt und korrekt beschriftet | `Spec0080`, `Spec0087`, `Spec0111`–`Spec0112` | `NAV-0009`: als spätere Kartenanforderung verfolgen; keine Implementierung in dieser Stufe. |
| Konzept-Abnahme: Richtungsauflösung und Verfügbarkeit von `λ` | `Spec0081`, `Spec0087`–`Spec0089`, `Spec0112` | `NAV-0009`: Daten- und Grenzbedingungen nachweisen; Wasserkarte bleibt später. |
| Konzept-Abnahme: fehlender Wind erzeugt weder Windzahlen noch künstliche Nullwerte | `Spec0076`, `Spec0080`–`Spec0081`, `Spec0087`, `Spec0113` | `NAV-0009`: keine Windkarte oder Ersatzwerte in der ersten Stufe. |
| Konzept-Abnahme: GUI blockiert/beschleunigt keine Physik und verwendet jüngsten Snapshot | `Spec0087`, `Spec0096`, `Spec0106` | `NAV-0002`, `NAV-0007`, `NAV-0009`: Snapshot- und Laufzeittests. |
| Konzept-Abnahme: SVG-Beispielwerte sind keine Simulations-Start-/Fallbackwerte | `Spec0087`, `Spec0095`, `Spec0109` | `NAV-0003`, `NAV-0009`: Quellbytes und Datenfluss prüfen. |

## 2. Reihenfolge, Abhängigkeiten und Freigabegates

Arbeitspunkte werden in der angegebenen Reihenfolge abgeschlossen. Ein
Arbeitspunkt darf erst beginnen, wenn alle aufgeführten Abhängigkeiten
abgenommen sind. Unabhängige technische Teilarbeiten dürfen parallel
vorbereitet werden, aber eine spätere Freigabe darf kein offenes
Vorgängergate umgehen.

| Reihenfolge | Arbeitspunkte | Abhängigkeit | Meilenstein |
|---:|---|---|---|
| 1 | `NAV-0001` | — | **M0 – Baseline und Integrationspfad geklärt** |
| 2 | `NAV-0002`, `NAV-0003` | M0 | **M1 – Datenableitung und SVG-Laufzeitpfad isoliert getestet** |
| 3 | `NAV-0004`, `NAV-0005` | M1 | **M2 – Drei Widgets erfüllen ihre lokalen Funktionsverträge** |
| 4 | `NAV-0006` | M2 | **M3 – Gemeinsame Optionen und Fehlerzustände korrekt** |
| 5 | `NAV-0007` | M2, M3 | **M4 – Widgets beziehen konsistente Laufzeitwerte** |
| 6 | `NAV-0008` | M4 | **M5 – Frei schwebendes Fenster erfüllt Anordnung und Lebenszyklus** |
| 7 | `NAV-0009` | M5 | **M6 – Regression, manuelle Abnahme und Freigabe abgeschlossen** |

**Gate-Regel:** Ein Meilenstein gilt nur dann als bestanden, wenn alle
aufgeführten automatisierten Tests erfolgreich sind und alle manuellen
Kriterien des Meilensteins nachweisbar erfüllt sind. Ein Fehlschlag blockiert
den nächsten Meilenstein. Abweichungen werden mit Ursache und betroffenen
Arbeitspunktkennungen dokumentiert; Tests werden nicht übersprungen oder
durch visuelle Plausibilität ersetzt.

## 3. Arbeitspunkte

### NAV-0001 – Baseline und Integrationspfad feststellen

**Spezifikationsbezug:** `Spec0067`–`Spec0096`, `Spec0107`, `Spec0109`
**Abhängigkeit:** keine

1. Branch, Arbeitsbaum und bereits bestehende Änderungen festhalten; fremde
   Änderungen nicht verwerfen oder überschreiben.
2. Die aktuelle GUI- und Laufzeitstruktur verfolgen: `HauptFenster`,
   GUI-Ereignisfluss, ausgewählter Laufzeitkörper, Zustand aus dem
   Echtzeitpfad, Snapshot-API, aktive Kamera sowie Qt- und PyVista-Integration.
3. Für `Spec0076`–`Spec0086` die tatsächlich vorhandenen Umwelt-, Körper-
   und Gelenkeingänge feststellen. Keine Umweltkopien, Bewegungsformeln oder
   Gelenkkinematik neu einführen oder verändern. Der Segelstellwinkel aus
   `Spec0084` darf ausschließlich als Anzeigeeingang für die Spiegelung
   verwendet werden; seine tatsächliche Quelle und sein Gültigkeitszustand
   sind festzustellen.
4. Nachweisen, welche Orientierung und welcher Kamerastandpunkt in jedem
   Betriebsmodus tatsächlich verfügbar sind. Die Kameraeingänge müssen dem
   Vertrag aus `Spec0092` entsprechen: `KAM_AZ` ist an `HDG` mit konstantem
   `Δ_Kamera` gekoppelt; `KAM_EL` bleibt relativ zum lokalen Horizont fest.
   Die konkrete Konfiguration beziehungsweise die Ableitung aus der
   aktiven Kamerapose ist explizit festzustellen und zu dokumentieren. Werte
   dürfen nicht aus einem illustrativen SVG-Wert oder einem ungeprüften
   Default stammen.
5. Vor Änderungen die passenden bestehenden Tests ausführen:

   ```powershell
   $env:QT_QPA_PLATFORM = "offscreen"
   .\.venv\Scripts\python.exe -m pytest -q tests\test_gui_app.py tests\test_gui_laufzeit_edit.py tests\test_gui_steuerung.py tests\test_echtzeit_prozess.py tests\test_koerper.py tests\test_dynamik_6dof.py tests\test_einstellungen.py
   ```

6. Verfügbarkeit und Verhalten der eingesetzten Qt-SVG-Laufzeit prüfen,
   insbesondere Laden aus Speicher, Zugriff auf die spezifizierten
   SVG-Elemente und Neudarstellung ohne Änderung der Quelldateien. Die
   geeignete Technik wird anhand dieses Tests festgelegt, nicht vorausgesetzt.
7. Die vier Diagramme im Spezifikationsordner gegen ihre Zuordnung in
   `Spec0109` prüfen. Jede für die Umsetzung relevante Aussage muss einem
   Textpunkt und einem passenden Nachweis zugeordnet sein; insbesondere
   dürfen Schemawinkel, Abstände oder Modellannahmen nicht als Produktions-
   oder Laufzeitwerte übernommen werden.

**Tests und Nachweise:** Baseline des obigen Testlaufs; dokumentierter
Datenfluss für statischen und Echtzeitmodus; Nachweis der SVG-Laufzeit-
fähigkeiten und der Quelle der Kameradaten.

**Abnahme M0:** Der Integrationspunkt für das Widgetfenster, die
Snapshotquelle und die Kameraeingänge ist durch Code oder reproduzierbare
Tests belegt. Es bestehen keine ungeklärten Import-, Qt- oder
Ressourcenpfadprobleme. Vorbestehende Testfehler sind isoliert und blockieren
die betroffenen Freigaben.

### NAV-0002 – Messwerte und Kameraansichten aus einem Snapshot ableiten

**Spezifikationsbezug:** `Spec0067`–`Spec0075`, `Spec0078`, `Spec0088`,
`Spec0092`, `Spec0096`, `Spec0108`, `Spec0109`
**Abhängigkeit:** `NAV-0001`

1. Eine reine, deterministische Anzeige-Datenaufbereitung verwenden. Sie
   erhält denselben vollständigen, unveränderlichen Physik-Snapshot und
   erzeugt daraus alle für die drei Widgets benötigten Werte und
   Gültigkeitszustände. Getrennte Abfragen je Widget oder ein Mischen von
   Zuständen beziehungsweise Snapshotversionen ist unzulässig.
2. `HDG`, `φ` und `θ` ausschließlich gemäß `Spec0078` aus Quaternion,
   lokalem Horizont und Nordrichtung ableiten. Die Quaternion bleibt
   autoritativ. Singularitäten, ungültige Orientierung und nicht definierter
   Headingwinkel werden als nicht verfügbar ausgewiesen.
3. `KAM_AZ` und `KAM_EL` gemäß `Spec0092` aus der in `NAV-0001`
   nachgewiesenen Kameraquelle beziehungsweise expliziten Konfiguration
   beziehen. `KAM_AZ = wrap_360(HDG + Δ_Kamera)`; `Δ_Kamera` bleibt konstant
   relativ zum Bug. `KAM_EL` bleibt relativ zum lokalen Horizont fest.
   Fehlende oder ungültige Kameradaten bleiben nicht verfügbar; sie dürfen
   weder den Primärmesswert ungültig machen noch auf null zurückfallen.
4. Für die Lageansichten die Formeln aus `Spec0108` umsetzen:

   ```text
   c_W = cos(KAM_EL)·cos(KAM_AZ)·n_W
       − cos(KAM_EL)·sin(KAM_AZ)·w_W
       + sin(KAM_EL)·u_W
   f_h = cos(HDG)·n_W − sin(HDG)·w_W
   s_h = f_h × u_W
   α_pitch = atan2(c_W·u_W, c_W·f_h)
   α_roll = atan2(c_W·u_W, c_W·s_h)
   ```

   Der Kompass verwendet `KAM_AZ` direkt. Lagewidgets verwenden die
   projizierten Winkel nur zur Kameramarkerposition; diese Werte sind keine
   zusätzlichen numerischen Anzeigen.
5. Die Sign- und SVG-Rotationsumrechnung für den oben liegenden
   Kameramarker aus `Spec0108` zentral und ohne Veränderung der physikalischen
   Kamera-Pose abbilden.

**Tests:** neue reine Unit-Tests, mindestens:

- Bug Nord/Ost/Süd/West ergibt `HDG` 0°/90°/180°/270°; Nullpose ergibt
  `φ=0°`, `θ=0°`.
- positive und negative `φ`- und `θ`-Orientierungen ergeben die in
  `Spec0078` festgelegten Vorzeichen; Nähe zur Euler-Singularität erzeugt
  Nichtverfügbarkeit statt eines erfundenen Winkels. Positives `θ` hebt den
  Bug und negatives `θ` senkt ihn; die SVG rotiert dazu jeweils um `−θ`.
- Kameraprojektionen für unterschiedliche `HDG`, `KAM_AZ` und `KAM_EL`
  stimmen mit `Spec0108` überein; die SVG-Rotationsabbildung stimmt mit der
  Uhrzeigersinn-Konvention überein.
- Eine Headingänderung um `δ` ändert `KAM_AZ` um dasselbe `δ` und hält
  `wrap_180(KAM_AZ − HDG)` konstant. Reine Stampf- und Krängungsänderungen
  ändern weder `KAM_EL` noch die Kamera-Rollung relativ zum Horizont.
- Nichtendliche, fehlende und ungültige Werte sowie Nullprojektionen liefern
  jeweils den spezifizierten Nichtverfügbarkeitszustand.
- Kameraeingangsfehler ändern gültige `HDG`-, `φ`- und `θ`-Messwerte nicht.
- Alle Widgets verwenden für eine Aktualisierung dieselbe Snapshotversion;
  sie berechnen keine unabhängige oder interpolierte Physikpose.

**Abnahme M1-Anteil:** Die Datenaufbereitung ist unabhängig von Qt und
verändert weder Snapshot noch Physikobjekt. Grenzfälle und Vorzeichen sind
automatisiert geprüft.

### NAV-0003 – Unveränderliche SVGs als flüchtige Laufzeitinstanzen rendern

**Spezifikationsbezug:** `Spec0095`, `Spec0096`, `Spec0106`, `Spec0109`
**Abhängigkeit:** `NAV-0001`

1. Für jedes Widget die tatsächlich vorhandenen SVG-IDs und die in der
   Spezifikation erlaubten Laufzeitbindungen erfassen. SVG-IDs gelten
   dateispezifisch; gleiche Namen in verschiedenen Dateien sind getrennte
   Namensräume.
2. Einen klar abgegrenzten Adapter für flüchtige SVG-Renderinstanzen
   bereitstellen. Er darf nur spezifizierte Elemente aktualisieren, darunter
   Heading-/Lagepose, Kameramarker, Messwert, Segelspiegelung und notwendige
   Statusüberlagerungen.
3. Originaldateien weder editieren noch zurückschreiben. Adapterfehler beim
   Laden, bei fehlenden Pflicht-IDs oder beim Rendern müssen erkennbar
   gemeldet werden; keine stillen Ersatzgrafiken oder Erfolgs-Fallbacks.
4. Keine Datenbindung anhand von SVG-Reihenfolge, Textsuche oder
   ungeprüften Offsets vornehmen. Elementzugriff muss an überprüfte IDs und
   explizite Widgetverträge gebunden sein.
5. Die SVGs einschließlich benötigter Ressourcendateien in die Anwendung
   einbinden, ohne Abhängigkeit vom aktuellen Arbeitsverzeichnis.

**Tests:** SVG-Adapter-Tests prüfen alle drei Quellen, Pflicht-IDs,
Ladefehler, eine Aktualisierung repräsentativer Laufzeitwerte, unveränderte
Quelldatei-Bytes nach wiederholten Updates sowie Ressourcenauflösung aus
einem fremden Arbeitsverzeichnis.

**Abnahme M1-Anteil:** Alle drei Original-SVGs werden gerendert; zulässige
Änderungen betreffen nur die flüchtige Instanz. Keine Quelldatei und kein
nicht spezifiziertes Element wird verändert.

### NAV-0004 – Kompass-Widget umsetzen

**Spezifikationsbezug:** `Spec0087`–`Spec0088`, `Spec0095`,
`Spec0097`–`Spec0099`, `Spec0106`, `Spec0109`
**Abhängigkeit:** `NAV-0002`, `NAV-0003`

1. Das Kompass-Widget zeigt `HDG`, die gemäß `Spec0087` abgeleitete
   16-Punkt-Richtung, Rose und Headingzeiger synchron aus demselben
   Messwert.
2. Den äußeren Kameramarker anhand von `KAM_AZ` positionieren. Er darf nicht
   mit dem Headingzeiger verwechselt oder an den projizierten
   Lagewinkel gekoppelt werden.
3. Nicht verfügbare Primärwerte und optionale Nebenwerte getrennt behandeln.
   Bei fehlerhaftem `HDG` bleibt das Widget sichtbar; der spezifizierte
   Fehlerzustand hat Vorrang vor normaler Darstellung. Ein ungültiges
   `KAM_AZ` betrifft ausschließlich den Kameramarker.
4. Geometrie, Zeichenreihenfolge und Drehpunkt aus der unveränderten
   Kompass-SVG bewahren.
5. Den numerischen Winkel einschließlich Gradkennzeichnung gemäß
   Spezifikation anzeigen; die 16-Punkt-Richtung wird aus demselben
   normalisierten `HDG` abgeleitet.

**Tests:** Headingwerte an den 16 Sektorgrenzen einschließlich exakt
11,25°-Grenzen; Wraparound bei 0°/360°; synchroner Zeiger- und Zahlenwert;
Kameramarker unabhängig von `HDG`; fehlerhafter Headingwert ohne
Nullwertdarstellung.

**Abnahme:** Kompass-Messwert, Richtungstext und Zeiger entsprechen
automatisiert demselben `HDG`; der Marker entspricht `KAM_AZ`.

### NAV-0005 – Krängungs- und Stampfen-Widgets umsetzen

**Spezifikationsbezug:** `Spec0078`, `Spec0084`, `Spec0088`, `Spec0093`,
`Spec0095`, `Spec0100`–`Spec0108`, `Spec0109`
**Abhängigkeit:** `NAV-0002`, `NAV-0003`

1. Eigenständige Widgets für `φ` und `θ` erstellen. Pose und Lagezeiger
   drehen gemeinsam um die festgelegten Mittelpunkte mit den Vorzeichen
   `−φ` beziehungsweise `−θ`; Skalen und Referenzachsen bleiben fest.
   Zahlenwerte werden in Grad mit eindeutiger Gradkennzeichnung gezeigt.
2. Die SVG-Kameramarker anhand `90° − α_roll` beziehungsweise
   `90° − α_pitch` positionieren. Sie gehören nicht zur rotierenden
   Posegruppe der Yacht.
3. Im Krängungswidget die Spiegelung nur auf das vorgesehene Segel-Element
   anwenden: negativer, nullwertiger oder fehlender Segelstellwinkel bedeutet
   Backbord-Grundlage; positiver Winkel bedeutet Steuerbord-Spiegelung. Die
   Lagepose bleibt davon unberührt.
4. Für gültige Lagewinkel außerhalb `[-90°, +90°]` ausschließlich das
   Ringband rot darstellen. Bei ungültigem oder logisch fehlerhaftem
   Primärwinkel ausschließlich Innenfläche rot und Wertfeld „FEHLER“
   darstellen; der Gefahrenzustand bleibt aus.
5. Nicht verfügbare Kameraeingänge oder Projektionen beeinflussen weder
   Primärwinkel noch Statusdarstellung.

**Tests:** Für beide Widgets positive, negative, nullwertige und
Grenzwinkel `−90°`, `+90°` sowie knapp außerhalb; Vorzeichen/Drehpunkt,
unbewegte Achsen, normale Anzeige exakt auf `−90°` und `+90°`, alleinige
Rotfärbung des Ringbands im gültigen Gefahrenfall, alleinige rote Innenfläche
plus „FEHLER“ im Fehlerfall und Nichtverfügbarkeit der Kamera ohne
Ersatzwinkel. Für Krängung zusätzlich
fehlende/negative/null/positive Segelstellung und Nachweis, dass nur das
Segelmotiv gespiegelt wird.

**Abnahme M2:** Beide Lagewidgets erfüllen die Einzelverträge. Die SVG-Pose,
der Zeiger und die Statusanzeige lassen keine Pose-, Farb- oder
Fehlerzustandsänderung außerhalb der spezifizierten Elemente erkennen.

### NAV-0006 – Gemeinsame Anzeigeoptionen und Sichtbarkeitsvertrag

**Spezifikationsbezug:** `Spec0087`, `Spec0096`, `Spec0099`, `Spec0102`,
`Spec0105`, `Spec0106`
**Abhängigkeit:** `NAV-0004`, `NAV-0005`

1. Die vier gemeinsamen Sichtbarkeiten für Titel, Titelbeschreibung,
   analoge Darstellung und numerische Darstellung getrennt steuerbar
   machen. Jede Option blendet ausschließlich ihr zugeordnetes Element
   aus.
2. Fehlende Optionen in bestehenden Einstellungen erhalten die
   spezifizierten aktivierten Standardwerte. Persistenz und Migration
   folgen dem bestehenden Einstellungsmechanismus.
3. Sichtbarkeitswechsel ändern keine Messwerte, Winkel, Pose, Physik oder
   Kamera. Der Fehlerzustand (rote Innenfläche und „FEHLER“) bleibt auch
   bei ausgeblendeter normaler Analog- oder numerischer Darstellung
   sichtbar.
4. Keine benutzerdefinierten Titel, Beschreibungen oder Layoutparameter in
   dieser Interface-Stufe ergänzen.

**Tests:** jede der vier Optionen einzeln und in Kombination toggeln; nur
das zugeordnete Element verschwindet; Fehlerstatus bleibt bei ausgeblendeter
Analog- und Digitaldarstellung sichtbar; alte Einstellungsdateien erhalten
die aktivierten Defaults; Einstellungsänderungen verändern keinen
Physik-Snapshot.

**Abnahme M3:** Die vier Sichtbarkeiten sind unabhängig, rückwärtskompatibel
und datenrein. Fehleranzeige hat spezifizierten Vorrang.

### NAV-0007 – Konsistente Snapshot-Anbindung für alle Widgets

**Spezifikationsbezug:** `Spec0087`, `Spec0092`, `Spec0096`, `Spec0101`,
`Spec0104`, `Spec0106`
**Abhängigkeit:** `NAV-0004`, `NAV-0005`, `NAV-0006`

1. Die drei Widgets von einem gemeinsamen Aktualisierungspunkt mit Werten
   desselben ausgewählten Körpers und desselben konsistenten Zustands
   versorgen. Keine Widgetklasse darf getrennt oder zu unterschiedlichen
   Zeitpunkten den Physikzustand abfragen.
2. Statischen Zustand, pausierte Simulation und laufende Echtzeitsimulation
   einheitlich behandeln. Pro Anzeigeaktualisierung sind alle Widgetwerte
   und ihre angezeigte Pose aus demselben neuesten vollständigen,
   abgeschlossenen Snapshot abzuleiten. Eine interpolierte Pose oder
   unabhängig abgefragte Zwischenwerte dürfen nicht mit Snapshotwerten
   vermischt werden. Simulationsarbeit darf weder in der
   GUI-Ereignisschleife ausgeführt noch durch eine Widgetaktualisierung
   erzwungen werden.
3. Körperwechsel und Änderungen am Laufzeitmodell dürfen keine Werte des
   vorherigen Körpers, alte Kamera-Projektionen oder veraltete
   Asynchron-Ergebnisse in die Widgetanzeige übernehmen.
4. Anzeigewerte und Fehlerzustände werden nach jedem relevanten Zustand-
   beziehungsweise Poseupdate aktualisiert. Die Widgets schreiben nie in
   den Physikzustand zurück.

**Tests:** gezielte GUI-Tests mit fiktiven Snapshots und mehreren
Körperidentitäten; alle Widgets erhalten jeweils denselben Snapshot und
aktualisieren gemeinsam; Körperwechsel zeigt nur die neuen Körperwerte;
verspätete/ungültige Resultate werden nicht übernommen; Update verändert
Snapshotversion und Physikzustand nicht. Bestehende Echtzeit- und
GUI-Steuerungstests bleiben grün.

**Abnahme M4:** Messwerte, Pose und Kameradaten sind pro Aktualisierung
konsistent; GUI-Updates führen keine Physikberechnung aus und blockieren
keine Simulationsschritte.

### NAV-0008 – Frei schwebendes Widgetfenster und Lebenszyklus

**Spezifikationsbezug:** `Spec0087`, `Spec0107`
**Abhängigkeit:** `NAV-0007`

1. Beim Anwendungsstart ein eigenes, vom Hauptfenster unabhängiges,
   frei bewegliches Fenster mit den drei Widgets öffnen.
2. In einem vertikalen Layout dauerhaft von oben nach unten anordnen:
   Kompass, Krängung, Stampfen. Ein Messwert, Fehlerstatus oder
   Fensterresize verändert weder Reihenfolge noch Anzahl der Widgets.
3. Alle drei Widgets müssen gleichzeitig sichtbar und bei geeigneter
   Fenstergröße vollständig erreichbar sein; eine Tab-Umschaltung oder
   automatische Ausblendung ist kein Ersatz.
4. Fenster und enthaltene Widgets werden vom Hauptfenster verwaltet.
   Schließen des Hauptfensters beendet Timer und Fenster sauber. Ein
   erneutes Anzeigen darf keine doppelt laufenden Updatepfade oder
   duplizierten Widgetfenster erzeugen.
5. Die Widgetanordnung darf das 3D-Hauptfenster und dessen Szenenlayout nicht
   ersetzen oder verändern.

**Tests:** Qt-Offscreen-Tests für Start/Existenz, getrennte Fensterinstanz,
Reihenfolge, gemeinsames Sichtbarsein, Resize, Schließen des Hauptfensters
und genau eine Aktualisierung pro Takt. Ergänzend GUI-Sichtprüfung unter
normalem Desktopbetrieb.

**Abnahme M5:** Start und Lebenszyklus entsprechen `Spec0107`; die
3D-Szene bleibt im Hauptfenster und alle drei Widgets sind gleichzeitig
sichtbar.

### NAV-0009 – Gesamtvalidierung, manuelle Abnahme und Freigabe

**Spezifikationsbezug:** `Spec0088`–`Spec0091`, `Spec0106`–`Spec0113`
**Abhängigkeit:** `NAV-0008`

1. Alle neuen Unit- und GUI-Tests sowie alle betroffenen bestehenden Tests
   ausführen. Bei Änderungen an gemeinsamen Modulen anschließend die
   vollständige Testsuite ausführen.
2. Testen, dass die ausgelieferten SVG-Dateien mit ihren Quellbytes
   übereinstimmen; Änderungen an SVG-Dateien sind bei diesem Umfang nicht
   zulässig.
3. `git diff --check` und die Prüfung der Anwendungsressourcen aus einem
   anderen Arbeitsverzeichnis ausführen.
4. Jede der vier Grafiken aus dem Spezifikationsordner anhand der Matrix in
   `Spec0109` abgleichen: Achsen und Frame-Bezüge, Lagewinkelvorzeichen,
   Kamera-Kopplung und Projektion sowie Segel-, Ruder- und Schwert-
   Konventionen müssen jeweils im zugeordneten Textvertrag stehen. Für
   außerhalb des Widgetumfangs liegende Umwelt- und Gelenkfunktionen muss
   bestätigt sein, dass die Widgets sie weder implementieren noch verändern.
   Zusätzlich muss die Konzeptmatrix bestätigen, dass die Zielkarten
   `Spec0110`–`Spec0113` eindeutig als spätere Anforderungen erfasst sind und
   keine davon versehentlich in die erste Laufzeitstufe gezogen wurde.
5. Manuelle Abnahme mit statischem Modus, pausierter und laufender
   Echtzeitsimulation durchführen:
   - Werte und Vorzeichen anhand definierter Testposen prüfen.
   - Heading ändern; `KAM_AZ` folgt mit konstantem `Δ_Kamera`, während
     `KAM_EL` relativ zum Horizont fest bleibt. Die Lagekameramarker folgen
     den Projektionen nach `Spec0108`.
   - Genau `−90°` und `+90°` bleiben im Normalzustand; Werte knapp außerhalb
     zeigen ausschließlich das rote Ringband. Ungültige Messwerte zeigen
     ausschließlich rote Innenfläche und „FEHLER“.
   - Fehlende oder ungültige Kameraeingänge kennzeichnen ausschließlich
     den Kameramarker als nicht verfügbar; sie täuschen keinen gültigen
     Kamerawinkel vor.
   - Segelseitenspiegelung und vier Sichtbarkeitseinstellungen einzeln
     prüfen.
   - Widgetfenster verschieben, vergrößern und schließen; Reihenfolge,
     gleichzeitige Verfügbarkeit und 3D-Hauptansicht prüfen.
6. Ergebnisse, verwendete Revision, Testbefehle und bekannte Abweichungen
   im Abschluss dieses Arbeitspunkts festhalten. Fehlerhafte oder nicht
   ausgeführte Kriterien verhindern die Freigabe.

**Tests:**

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_navigationswidgets.py tests\test_einstellungen.py tests\test_gui_app.py tests\test_gui_laufzeit_edit.py tests\test_gui_steuerung.py tests\test_echtzeit_prozess.py tests\test_koerper.py tests\test_dynamik_6dof.py
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

**Abnahme M6:** Alle gezielten und vollständigen Tests sind erfolgreich,
manuelle Kriterien sind protokolliert, SVG-Quellen bleiben bytegenau
unverändert und es gibt keine offenen Freigabeblocker. Die fachliche
Produktivfreigabe erfolgt erst nach diesem Gate.

## 4. Testmatrix und Fehlerreaktion

| Bereich | Mindestnachweis | Blockiert mindestens |
|---|---|---|
| Frames, Einheiten, Orientierung | `HDG`, `φ`, `θ`, Vorzeichen, Wraparound und Singularität gemäß `Spec0078` | `NAV-0002`, `NAV-0004`, `NAV-0005` |
| Kamera | `KAM_AZ` direkt im Kompass, projizierte Winkel, Rotationskonvention und undefinierte Projektion | `NAV-0002`, `NAV-0004`, `NAV-0005` |
| SVG-Integrität | Alle Assets lesbar, IDs vorhanden, Originalbytes unverändert, kein CWD-abhängiger Pfad | `NAV-0003` und alle Widgetabnahmen |
| Statusdarstellung | Genau `−90°` und `+90°` normal; außerhalb rot ausschließlich das Ringband; Fehler ausschließlich Innenfläche plus „FEHLER“ | `NAV-0005`, `NAV-0006` |
| Snapshotkonsistenz | Alle Werte desselben Körpers und desselben Updatezustands; keine Rückschreibung oder UI-Physikberechnung | `NAV-0007` |
| Optionen und Migration | Vier Sichtbarkeiten unabhängig; Defaults für alte Einstellungen; Fehlerzustand hat Vorrang | `NAV-0006` |
| Fenster und Laufzeit | Separate Fenster, feste Reihenfolge, gleichzeitig sichtbar, korrekter Lebenszyklus | `NAV-0008` |
| Regression und Freigabe | Gezielte Tests, vollständige Suite, manuelle Sichtprüfung, `git diff --check` | `NAV-0009` |

Bei einem Fehler wird zunächst der verursachende Arbeitspunkt korrigiert und
dessen Tests erneut ausgeführt. Ein Fehler in der SVG- oder GUI-Schicht darf
nicht durch Änderungen an Physikdefinitionen, Winkelvorzeichen oder
Quelldateien kompensiert werden. Ein fehlender oder fachlich nicht
eindeutiger Eingang bleibt sichtbar nicht verfügbar und blockiert nur die
von ihm abhängige Anzeige beziehungsweise Freigabe.

## 5. Abschlusskriterien

Der Umsetzungsplan ist abgeschlossen, wenn:

1. alle Arbeitspunkte `NAV-0001` bis `NAV-0009` und Meilensteine M0 bis M6
   bestanden sind;
2. alle Anforderungen dieses Plans auf implementierte Elemente oder
   bestandene Tests zurückverfolgt werden können;
3. alle drei Widgets im vorgesehenen Fenster gleichzeitig verfügbar sind,
   ihre Fehler-, Gefahren-, Kamera- und Sichtbarkeitsregeln erfüllen und
   denselben konsistenten Snapshot darstellen;
4. die Original-SVGs unverändert geblieben sind und alle Tests einschließlich
   vollständiger Regression erfolgreich sind; und
5. keine unbelegte Nichtverfügbarkeit, stiller Ersatzwert oder offene
   fachliche Entscheidung als bestanden behandelt wird.

## 6. Umsetzungsnachweis

Die Widgetlogik, Snapshot-Anbindung, Fensterintegration und
Heading-gekoppelte Kameraführung sind implementiert. Die im Plan
vorgeschriebenen vollständigen automatisierten Regressionstests liefen mit
`616 passed, 1 skipped`; `git diff --check` meldete keine Fehler.

| Gate / Arbeitspunkt | Ergebnis dieses Laufs |
|---|---|
| M0 / `NAV-0001` | Integrationspfade, Snapshotquelle, Kamerapose, Segelwinkel-Eingang und Qt-SVG-Laufzeit anhand des bestehenden Codes und der Tests geprüft. Die vor der Implementierung ausgeführte Baseline hatte 107 bestandene Tests. |
| M1 / `NAV-0002`–`NAV-0003` | Winkel-, Singularitäts- und Kameraprojektionstests bestanden; die SVGs laden aus dem anwendungsrelativen Pfad, ihre Laufzeitinstanzen bleiben flüchtig. |
| M2 / `NAV-0004`–`NAV-0005` | Kompass-, Krängungs- und Stampfenverträge einschließlich Vorzeichen, Spiegelung, Gefahr und Fehlerdarstellung automatisiert geprüft. |
| M3 / `NAV-0006` | Unabhängige Sichtbarkeiten, Fehlerpriorität und Statusdarstellung automatisiert geprüft. |
| M4 / `NAV-0007` | Snapshot-/Updatepfad und Kamerafolge automatisiert geprüft; die GUI stößt keine zusätzliche Physikberechnung an. |
| M5 / `NAV-0008` | Getrenntes Fenster, feste Reihenfolge, gleichzeitige Sichtbarkeit, Resize und Lebenszyklus sind durch Offscreen-Tests abgedeckt. Eine interaktive Sichtprüfung des laufenden Desktopfensters ist noch offen; M5 daher nicht formal abgenommen. |
| M6 / `NAV-0009` | Vollständige Testsuite bestanden. Die im Arbeitspunkt geforderte manuelle Prüfung in statischem, pausiertem und laufendem Desktopbetrieb sowie die interaktive Prüfung aller Anzeigezustände und Einstellungen wurde nicht durchgeführt. M6 und Produktivfreigabe bleiben offen. |

Die drei Widget-SVGs stimmen bytegenau mit den zu Beginn dieses
Implementierungslaufs festgehaltenen Prüfsummen überein:

| Datei | SHA-256 |
|---|---|
| `Widget_Kompass.svg` | `8bfa42a4556a2ec73d8d9d97bd591b8acc4776a1d6abab9254f930d9178114a4` |
| `Widget_Krängung.svg` | `9d68520a2c6e237c9504cf77c607ce3f69921125c2a4e855af172e9c35a0bdba` |
| `Widget_Stampfen.svg` | `b48289877c4e300ba9fbf454f804738f20b8121503da03e85f8ddfebc32f480b` |

Bei `QT_QPA_PLATFORM=offscreen` enthält Qt keine auflösbaren Schriftfamilien;
deshalb ist eine dort erzeugte Textvorschau nicht aussagekräftig. Unter dem
nativen Windows-Qt-Backend wurden 287 Schriftfamilien geladen und alle drei
Laufzeit-SVGs mit lesbaren Texten gerendert. Das ersetzt nicht die oben
offene interaktive Desktopabnahme. Die Arbeitskopie enthielt bereits andere
Änderungen; diese wurden nicht zurückgesetzt oder committet.
