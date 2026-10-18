# Spezifikation: Navigationswidgets v0.7

**Stand:** 18.10.2026<br>
**Status:** Fachliche Spezifikation; keine Implementierungs- oder
Produktivfreigabe<br>
**Geltungsbereich:** Kompass-, Krängungs- und Stampfen-Widget einschließlich
ihrer Dateninterfaces und Anzeigeeinstellungen.

## Kennzeichnungs- und Änderungsverfahren

### Spec0094 — Dauerhafte Kennungen und fachliche Abgrenzung

Jeder normative Punkt der beiden formalen Spezifikationen in diesem
v0.7-Umfang erhält eine dauerhafte Kennung im Format `SpecNNNN`. Jede
normative Anforderung im Konzept muss auf mindestens eine solche Kennung
verweisen; neue, dort noch nicht erfasste Anforderungen erhalten eine neue
Kennung in der Spezifikation. Die Nummerierung setzt
`Spezifikation_Weltsystem_Bewegung_v0.7.md` nach `Spec0093` fort. Kennungen
werden bei Änderungen beibehalten und nie wiederverwendet. Neue Punkte
erhalten unbenutzte Kennungen; entfallene oder verworfene Punkte werden am
Dokumentende unter ihrer bisherigen Kennung mit Begründung archiviert. Jede
Kennung muss im einzigen v0.7-Umsetzungsplan auffindbar und bis zu einem
Arbeitspunkt, Test, Meilenstein oder einer begründeten Umfangsgrenze
rückverfolgbar sein.

Dieses Dokument konkretisiert die drei Navigationswidgets. Es ersetzt weder
die Welt- und Körperdefinitionen aus `Spec0070`–`Spec0078` noch die
Kameraregel aus `Spec0092` oder die Gestaltungs- und Lagewinkelregeln aus
`Spec0093`. Bei fachlichen Konflikten ist eine explizite Änderung der
betroffenen bestehenden Spezifikation erforderlich; diese Spezifikation
ändert insbesondere keine Winkeldefinition.

## 1. Gemeinsamer Vertrag für alle Widgets

### Spec0095 — SVG-Quelldateien unverändert übernehmen

Die drei vorhandenen Einzel-SVGs
[Widget_Kompass.svg](../Widgets/Widget_Kompass.svg),
[Widget_Krängung.svg](../Widgets/Widget_Kr%C3%A4ngung.svg) und
[Widget_Stampfen.svg](../Widgets/Widget_Stampfen.svg) sind die verbindlichen
Gestaltungsvorlagen. Sie müssen als Quelldateien unverändert übernommen und
mit der Anwendung ausgeliefert werden. Es dürfen weder ihre Geometrie noch
ihre Element-IDs, Ebenenreihenfolge, Farben, Schrift, Strichstärken,
Zifferblattbeschriftung, Referenzlinien, Drehpunkte oder Winkeldefinitionen
umgezeichnet, angepasst oder ersetzt werden.

Laufzeitwerte dürfen an die dafür vorgesehenen SVG-Elemente gebunden werden,
ohne die Quelldatei zu verändern oder eine geänderte Datei zurückzuschreiben.
Eine dafür nötige Laufzeitinstanz ist flüchtig. Sie darf ausschließlich die
von den folgenden Widget-Interfaces benannten Messwert-, Pose-, Kamera- und
Spiegelelemente aktualisieren. Statusdarstellungen dürfen als getrennte
Render-Ebenen über der unveränderten SVG ergänzt werden: Ein Fehler im
primären Messwert des Widgets färbt die Zifferblattfläche innerhalb des
Innenrings rot und zeigt im Winkelwertfeld „FEHLER“. Ein gültig erkannter
Kenter-/Gefahrenzustand färbt ausschließlich das Ringband zwischen Innen-
und Außenring rot; Winkelwert und Zifferblattfläche bleiben normal. Diese
Render-Ebenen sind keine Änderung oder Neufassung der Quelldatei. Drehpunkt,
Drehachse und Zuordnung zwischen physikalischem Winkel und SVG-Rotation
dürfen nicht verändert werden.

Die Element-IDs in den Einzel-SVGs und in
[BeschreibungElementeWidgets.svg](../Widgets/BeschreibungElementeWidgets.svg)
sind die stabilen Bindungsnamen. Bei gleichlautenden IDs in verschiedenen
SVG-Dateien ist die jeweilige SVG-Datei der Namensraum. Beispiele in den
Quelldateien sind illustrative Vorführwerte und dürfen nicht als
Simulationsstartwerte oder Ersatzwerte verwendet werden.

### Spec0096 — Widgetdaten und Interfacephasen

Alle drei Widgets müssen ihre Werte aus demselben unveränderlichen,
vollständigen Physik-Snapshot eines ausgewählten Körpers beziehen. Ein
Widget darf weder Physikzustände verändern noch selbst eine zweite
physikalische Winkeldefinition, eine alternative Bezugsachse oder eine
eigene Physikberechnung einführen. Einheiten und Bezugsrahmen richten sich
nach `Spec0074`, `Spec0078`, `Spec0092` und `Spec0093`. Ungültige,
singuläre oder fehlende Werte müssen als ungültig beziehungsweise nicht
verfügbar behandelt werden; sie dürfen nicht stillschweigend als `0°`
erscheinen.

Alle drei Widgets bleiben verfügbar und werden unabhängig von der Gültigkeit
ihrer Eingabewerte angezeigt. Ein ungültiger oder logisch fehlerhafter
primärer Messwert (`HDG`, `φ` oder `θ`) wird als Fehlerzustand dargestellt,
nicht durch Ausblenden des Widgets oder durch einen Ersatzwert. Bei
ungültigem Lagewinkel ist ein Kenter-/Gefahrenzustand aus diesem Winkel nicht
bestimmbar; in diesem Fall wird ausschließlich der Fehlerzustand angezeigt.
Fehler- und Kenter-/Gefahrenzustände sind gemäß `Spec0106` gegenseitig
ausschließend. Ein ungültiger Nebenwert wie `KAM_AZ` betrifft nur das
zugehörige Anzeigeelement und macht einen gültigen primären Messwert nicht
ungültig.
Der Fehlerzustand hat Vorrang vor den normalen Sichtbarkeitseinstellungen:
„FEHLER“ und die rote Innenfläche müssen auch dann sichtbar bleiben, wenn die
normale numerische oder analoge Darstellung ausgeblendet wurde.

Die Interfaceausbaustufen sind getrennt:

1. **Erste Stufe:** Übergabe physikalischer Messwerte und ihrer Gültigkeit.
   Ein zusätzliches Statussignal bezeichnet ausschließlich einen fachlichen
   Fehler des primären Messwerts. Ungültige Nebenwerte betreffen nur ihr
   jeweiliges Anzeigeelement. Es gibt keine Texteingabe durch die Physik und
   keine Layout-Eingaben.
2. **Spätere Textstufe:** Übersetzte Titel, Beschreibungen und weitere
   Anzeigetexte werden als eigenes Präsentationsinterface ergänzt. Texte
   dürfen keine physikalischen Eingaben ersetzen oder verändern.
3. **Spätere Layoutstufe:** Es dürfen ausschließlich vordefinierte,
   nummerierte Layoutmuster (Option 1 bis N) gewählt werden. Freie
   Positions-, Größen-, Drehpunkt- oder Winkeldefinitionen sind kein
   Layoutmuster.

Die späteren Stufen dürfen weder die Quelldateien noch die Winkel- und
Drehpunktregeln aus Spec0095 verändern.

## 2. Kompass-Widget

### Spec0097 — Kompass: Widgetfunktion

Das Kompass-Widget zeigt die Bugrichtung `HDG` relativ zum lokalen Nord sowie
die daraus abgeleitete 16-Punkt-Himmelsrichtung. Es ist eine Weltazimutanzeige,
keine GPS-, Magnetkompass- oder geografische Positionsanzeige. Die Rose und
der Heading-Zeiger müssen denselben `HDG`-Wert darstellen.

Das außen umlaufende Kamerasymbol zeigt ausschließlich den Kamerastandpunkt-
Azimut `KAM_AZ` gemäß `Spec0092`. Die Kameraausrichtung ist kein zweiter
Headingwert. Ein Fehler im primären Messwert wird durch eine rote
Zifferblattfläche innerhalb des Innenrings und „FEHLER“ im Winkelwertfeld
gekennzeichnet; ein Ringbandzustand ist dem gültig erkannten
Kenter-/Gefahrenzustand vorbehalten.

### Spec0098 — Kompass: Widget-Interface

Das Eingangsinterface umfasst:

| Wert | Bedeutung | Abbildung |
|---|---|---|
| `HDG` | Headingwinkel im Weltframe mit Gültigkeitsstatus; intern rad, dargestellt in Grad | Zahlenwert, Richtungstext und `heading_pointer`; die vorhandene SVG-Zuordnung und ihr Drehpunkt bleiben unverändert. |
| Kamerastandpunkt | `KAM_AZ` gemäß `Spec0092` | `camera_symbol` wird mit `KAM_AZ` positioniert; der angezeigte Kompasswinkel ist `KAM_AZ`. Bei ungültigem Winkel wird kein gültiger Kamerastandpunkt vorgetäuscht. |
| `status` (optional) | Expliziter logischer Fehler im primären Messwert `HDG` | Fehleranzeige wie unten festgelegt. |

`HDG` muss für die Darstellung in den in der Spezifikation definierten
Azimutbereich normalisiert werden. Die 16-Punkt-Richtung wird deterministisch
aus demselben gültigen Winkel gemäß `Spec0087` abgeleitet. Ist `HDG` ungültig
oder zeigt ein übergebenes Statussignal einen logischen Fehler des primären
Messwerts an, bleibt das Widget sichtbar, färbt die Zifferblattfläche
innerhalb des Innenrings rot und zeigt im Winkelwertfeld „FEHLER“. Ungültiges
`KAM_AZ` betrifft ausschließlich das Kamerasymbol. Ungültige Werte dürfen
weder Zahl, Richtungstext, Zeiger noch Kamerasymbol als gültigen Wert
vortäuschen. Der Fehlerstatus ist vom späteren Textinterface getrennt.

### Spec0099 — Kompass: Einstellungsanforderungen

Anzeigeeinstellungen dürfen Titel, Titelbeschreibung, analoge Rose und
numerische Darstellung unabhängig voneinander ein- und ausblenden; sie folgen
dem gemeinsamen Sichtbarkeitsvertrag aus `Spec0087`. Das Ausblenden verändert
weder `HDG`, `KAM_AZ` noch den Physik-Snapshot. Insbesondere bleiben
Drehpunkt und Winkeldefinition des Heading-Zeigers sowie die feste
Kamerakopplung aus `Spec0092` unveränderlich.

In der ersten Interface-Stufe sind keine nutzerdefinierten Texte und keine
Layoutparameter erforderlich. Spätere Übersetzungen und vordefinierte
Layoutmuster unterliegen ausschließlich `Spec0096`.

## 3. Krängungs-Widget

### Spec0100 — Krängung: Widgetfunktion

Das Krängungs-Widget zeigt den aus der Körperorientierung abgeleiteten
Krängungswinkel `φ` und die dazugehörige Heckansicht der Yacht. Skala,
Referenzachsen und Zifferblatt bleiben fest; Yacht und Lagezeiger bilden die
gemeinsam rotierende Pose. Die Yachtkonturen bleiben gemäß `Spec0093` weiß,
ohne Mast.

Die visuelle Pose folgt `Spec0093`: Die SVG rotiert um `−φ`; positives `φ`
hebt die Steuerbordseite, negatives `φ` die Backbordseite. Die
Segelstellungsseite darf die Yachtgrafik an ihrer festgelegten senkrechten
Mittelachse spiegeln, aber weder Lagewinkel, Messwert, Zeigerwinkel noch
Drehpunkt beeinflussen. Fehlender oder nullwertiger Segelstellwinkel bedeutet
Backbord als Standarddarstellung; positiver Segelstellwinkel bedeutet
Steuerbord.

Für `−90° ≤ φ ≤ +90°` wird die Normalanzeige gezeigt. Bei `φ < −90°` oder
`φ > +90°` wird ausschließlich für dieses Widget der Gefahrenzustand
aktiviert. Bei gültigem Winkel färbt er nur das Band zwischen den Ringen rot;
die Winkelzahl und die Innenfläche bleiben normal. Ist `φ` ungültig oder
logisch fehlerhaft, ist ein Kenterzustand nicht bestimmbar. Dann wird
ausschließlich die Innenfläche rot und der Winkelwert durch „FEHLER“ ersetzt;
das Ringband bleibt normal. Die Grenzwerte `−90°` und `+90°` gehören zur
Normalanzeige. Die Anzeige wird aus `Spec0078` und `Spec0093` abgeleitet und
führt keine unabhängige Krängungsdefinition ein.

### Spec0101 — Krängung: Widget-Interface

Das Eingangsinterface umfasst:

| Wert | Bedeutung | Abbildung |
|---|---|---|
| `φ` | Gültiger Krängungswinkel des ausgewählten Körpers gemäß `Spec0078`; intern rad, dargestellt in Grad | Messwert und `roll_pose`; Pose-Rotation mit dem in `Spec0093` festgelegten Vorzeichen um den festgelegten Mittelpunkt. |
| Segelstellwinkel | Gültige Segelstellung nach `Spec0084`; intern rad | Ausschließlich Auswahl der Backbord-/Steuerbord-Spiegelung von `roll_sail_side`; negativ, null oder fehlend ergibt Backbord. |
| Kamerastandpunkt | `KAM_AZ`, `KAM_EL` und `HDG` gemäß `Spec0092`/`Spec0078` aus demselben Snapshot | `roll_camera` wird mit dem auf die Heckansicht projizierten Winkel gemäß `Spec0108` positioniert. Bei ungültiger Projektion wird der Marker als nicht verfügbar behandelt. |
| `status` (optional) | Expliziter logischer Fehler im primären Messwert `φ` | Innenfläche rot und Winkelwertfeld „FEHLER“; kein Kenter-/Gefahrenstatus. |

Die Gültigkeit von `φ` muss unabhängig von der Segelstellungsseite behandelt
werden. Bei ungültigem `φ` oder einem übergebenen logischen Fehler in `φ`
wird kein Nullwinkel und kein scheinbar gültiger Gefahrenzustand erzeugt. Die
Innenfläche wird rot und das Winkelwertfeld zeigt „FEHLER“; das Ringband
bleibt normal, weil eine Kenterung aus einem ungültigen `φ` nicht bestimmbar
ist. Ungültige Kameraeingänge oder eine nicht definierte Projektion betreffen
ausschließlich das Kamerasymbol und ändern die Auswertung von `φ` nicht. Die
Referenzachsen bleiben fest; sie sind nicht Teil von `roll_pose`.

### Spec0102 — Krängung: Einstellungsanforderungen

Titel, Titelbeschreibung, analoge Darstellung und numerischer Winkel müssen
gemäß `Spec0087` unabhängig sichtbar sein. Einstellungen dürfen nicht die
Spiegelregel der Segelstellung, das Rotationsvorzeichen, den Pose-Drehpunkt,
die Achsen, die Gefahren-Grenzen oder den Ringbereich verändern.

In der ersten Interface-Stufe werden keine Texte und keine Layoutwerte aus
Einstellungen an das Widget übergeben. Übersetzte Texte und nummerierte
Layoutmuster sind spätere, getrennte Präsentationsstufen nach `Spec0096`.

## 4. Stampfen-Widget

### Spec0103 — Stampfen: Widgetfunktion

Das Stampfen-Widget zeigt den aus der Körperorientierung abgeleiteten
Stampfwinkel `θ` und die Seitenansicht der Yacht mit Bug nach rechts. Yacht
und Lagezeiger bilden eine gemeinsame Pose; Skala, Referenzachsen und
Zifferblatt bleiben fest. Die Yachtkonturen bleiben gemäß `Spec0093` weiß,
ohne Mast; der Aufbau behält die Geometrie und Position der verbindlichen
Stampfen-SVG.

Die visuelle Pose rotiert gemäß `Spec0093` um `−θ`: positives `θ` hebt den
Bug, negatives `θ` senkt ihn. Für `−90° ≤ θ ≤ +90°` wird die Normalanzeige
gezeigt; außerhalb dieses Bereichs wird ausschließlich für dieses Widget
der Gefahrenzustand aktiviert. Bei gültigem Winkel färbt er ausschließlich
das Ringband zwischen Innen- und Außenkreis rot; Winkelwert und Innenfläche
bleiben normal. Ist `θ` ungültig oder logisch fehlerhaft, ist ein
Kenterzustand nicht bestimmbar. Dann wird ausschließlich die Innenfläche rot
und der Winkelwert durch „FEHLER“ ersetzt; das Ringband bleibt normal. Genau
`−90°` und `+90°` gehören zur Normalanzeige. Eine Änderung der Darstellung
darf weder `θ` umdefinieren noch den Drehpunkt oder die festgelegte
Rotationsrichtung ändern.

### Spec0104 — Stampfen: Widget-Interface

Das Eingangsinterface umfasst:

| Wert | Bedeutung | Abbildung |
|---|---|---|
| `θ` | Gültiger Stampfwinkel des ausgewählten Körpers gemäß `Spec0078`; intern rad, dargestellt in Grad | Messwert und `pitch_pose`; Pose-Rotation mit dem in `Spec0093` festgelegten Vorzeichen um den festgelegten Mittelpunkt. |
| Kamerastandpunkt | `KAM_AZ`, `KAM_EL` und `HDG` gemäß `Spec0092`/`Spec0078` aus demselben Snapshot | `pitch_camera` wird mit dem auf die Seitenansicht projizierten Winkel gemäß `Spec0108` positioniert. Bei ungültiger Projektion wird der Marker als nicht verfügbar behandelt. |
| `status` (optional) | Expliziter logischer Fehler im primären Messwert `θ` | Innenfläche rot und Winkelwertfeld „FEHLER“; kein Kenter-/Gefahrenstatus. |

Bei ungültigem oder singulärem `θ` oder einem übergebenen logischen Fehler in
`θ` muss das Widget die Messung als Fehler kennzeichnen: Die
Innenfläche wird rot und das Winkelwertfeld zeigt „FEHLER“. Das Ringband
bleibt normal, weil der Kenterzustand aus einem ungültigen `θ` nicht
bestimmbar ist. Ungültige Kameraeingänge oder eine nicht definierte
Projektion betreffen ausschließlich das Kamerasymbol und ändern die
Auswertung von `θ` nicht. Das Widget darf weder
`0°` noch eine davon abgeleitete Normalpose als scheinbar gültigen Wert
einsetzen. Die Referenzachsen bleiben fest und liegen außerhalb der
beweglichen Posegruppe.

### Spec0105 — Stampfen: Einstellungsanforderungen

Titel, Titelbeschreibung, analoge Darstellung und numerischer Winkel müssen
gemäß `Spec0087` unabhängig sichtbar sein. Einstellungen dürfen weder
Stampfen-Vorzeichen und Rotationsrichtung noch Drehpunkt, Yachtgeometrie,
Referenzachsen oder die `±90°`-Gefahrengrenzen verändern.

Die erste Interface-Stufe erhält keine benutzerdefinierten Texte oder
Layoutparameter. Übersetzte Texte und nummerierte Layoutmuster dürfen nur in
den getrennten späteren Präsentationsstufen gemäß `Spec0096` ergänzt werden.

## 5. Gemeinsame Abnahme

### Spec0106 — Widget-, Interface- und Einstellungstests

Die Umsetzung ist erst abnahmefähig, wenn automatisierte oder reproduzierbare
Tests mindestens Folgendes nachweisen:

1. Alle drei Quelldateien werden unverändert ausgeliefert; ihre
   Element-IDs und Geometrien sind erhalten.
2. Für jedes Widget stammen Messwert und grafische Pose aus demselben
   Snapshot; Aktualisierung der Anzeige verändert keinen Physikzustand.
3. Die festgelegten Rotationsvorzeichen, Drehpunkte und Achsen bleiben für
   positive, negative und nullwertige Winkel erhalten.
4. Krängungs- und Stampfengefahrenzustände schalten nur beim Überschreiten
   von `±90°` um und färben bei gültigem Winkel ausschließlich das Ringband.
5. Ein fehlender, ungültiger oder logisch fehlerhafter Lagewinkel färbt
   ausschließlich die Innenfläche rot und ersetzt den Winkelwert durch
   „FEHLER“; er erzeugt keinen Kenter-/Gefahrenzustand.
6. Ein ungültiger primärer Messwert oder ein expliziter logischer Fehler in
   diesem Messwert färbt die Innenfläche rot und zeigt „FEHLER“; das Widget
   bleibt sichtbar und der Fehler wird nicht als Kenterung behandelt. Diese
   Fehlermeldung bleibt auch bei ausgeblendeter normaler Analog- oder
   numerischer Darstellung sichtbar.
7. Die optionale Segelseitenspiegelung ändert nur die Krängungsgrafik und
   folgt dem spezifizierten Vorzeichen; fehlt der Wert, gilt Backbord.
8. Jede Sichtbarkeitseinstellung wirkt nur auf das zugeordnete Anzeigeelement
   und ändert weder Messwert noch Physikzustand.
9. Der Kompass positioniert den Kameramarker nach `KAM_AZ`; Stampfen und
   Krängung verwenden den gemäß `Spec0108` auf ihre Ansicht projizierten
   Kamerastandpunktwinkel.
10. Änderungen durch spätere Text- oder Layoutoptionen verändern weder die
   Quelldateien noch Drehpunkte, Winkeldefinitionen oder die verbindlichen
   Widgetgeometrien.

## 6. Zwischenlösung für die Fensteranordnung

### Spec0107 — Zwischenlösung mit frei schwebendem Widgetfenster

Für die erste Darstellungsstufe müssen alle drei Widgets gemeinsam in einem
separaten, frei schwebenden Fenster angezeigt werden. Das Fenster ist nicht
in das Hauptfenster oder dessen 3D-Szene eingebettet. Innerhalb des Fensters
stehen die Widgets in einer vertikalen Spalte und in folgender Reihenfolge:

1. Kompass oben;
2. Krängung darunter;
3. Stampfen darunter.

Die drei Widgets sind gleichzeitig sichtbar; ihre Reihenfolge darf nicht
durch Messwerte, Fenstergröße oder Aktualisierungen wechseln. Das Fenster
darf unabhängig vom Hauptfenster positioniert werden. Diese Anordnung ist
ausdrücklich eine Zwischenlösung und kein endgültiges Dashboard- oder
Layoutmuster. Eine spätere Ablösung oder Neuanordnung erfordert eine
gesonderte Spezifikationsänderung mit neuer beziehungsweise aktualisierter
Kennung. Sie ändert weder die Funktionen und Interfaces der Widgets noch die
verbindlichen SVG-Vorlagen aus `Spec0095`.

Abnahmekriterien:

- Beim Start werden Kompass, Krängung und Stampfen gemeinsam in einem
  separaten frei schwebenden Fenster dargestellt.
- Die sichtbare Reihenfolge von oben nach unten lautet Kompass, Krängung,
  Stampfen.
- Alle drei Widgets bleiben gleichzeitig verfügbar; eine geringe
  Fenstergröße darf sie nicht ausblenden oder durch eine Umschaltung ersetzen.
  Das Fenster muss eine Größe zulassen, in der alle drei Widgets sichtbar
  sind.
- Die Fensteranordnung verändert weder die 3D-Szene noch Widgetgeometrie,
  Messwertdarstellung oder Rotationsdefinitionen.

## 7. Kamerawinkel für die drei Widgetansichten

### Spec0108 — Projektion des Kamerastandpunkts in die Widgetansicht

Der Kameramarker stellt in jedem Widget die projizierte Richtung vom Zielpunkt
zum Kamerastandpunkt dar. Grundlage sind `KAM_AZ`, `KAM_EL` und `HDG` desselben
Snapshots sowie die lokalen Einheitsvektoren `n_W` (Nord), `w_W` (West) und
`u_W` (oben) aus `Spec0075` und `Spec0092`. `HDG` ist gemäß `Spec0078` die
Richtung der auf den Horizont projizierten Körperlängsachse.

Der normierte Richtungsvektor vom Zielpunkt zum Kamerastandpunkt im Weltframe
ist:

```text
c_W = cos(KAM_EL)·cos(KAM_AZ)·n_W
    − cos(KAM_EL)·sin(KAM_AZ)·w_W
    + sin(KAM_EL)·u_W
f_h = cos(HDG)·n_W − sin(HDG)·w_W
s_h = f_h × u_W
```

`f_h` ist die horizontale Richtung nach vorn; `s_h` ist die horizontale
Richtung nach Steuerbord. Die angezeigten Kamerawinkel in den Lagewidgets
sind orthogonale Projektionen von `c_W` auf die jeweilige vertikale
Ansichtsebene. `atan2(y, x)` bezeichnet den signierten Winkel gegen den
Uhrzeigersinn, ausgehend von der horizontalen Bildschirmrichtung nach
rechts. Der Winkel wird in rad berechnet und für die Anzeige in Grad
umgerechnet.

| Widget | Projektionsebene; Bildschirm rechts/oben | Angezeigter Winkel |
|---|---|---|
| Kompass | Horizontale Welt-Ebene; nautischer Azimut im Uhrzeigersinn ab lokalem Nord | `KAM_AZ`, gemäß `Spec0092`; keine Körperansichtsprojektion. |
| Stampfen | Vertikale Ebene durch `f_h`; rechts `f_h` (voraus), oben `u_W` | `α_pitch = atan2(c_W·u_W, c_W·f_h)` |
| Krängung | Vertikale Ebene durch `s_h`; rechts `s_h` (Steuerbord), oben `u_W` | `α_roll = atan2(c_W·u_W, c_W·s_h)` |

`α_pitch` und `α_roll` bestimmen ausschließlich die Position des
Kameramarkers auf dem Zifferblatt; sie werden nicht als separate Zahlenwerte
angezeigt.

Die Lagewinkelanzeigen verwenden somit nicht unverändert denselben Zahlenwert
`KAM_AZ` wie der Kompass. Ihre Projektionen hängen von `KAM_AZ`, `KAM_EL` und
`HDG` ab. Die vertikalen Ansichtsebenen sind horizonstabil und an die
horizontale Headingrichtung gekoppelt; die Bootspose rotiert weiterhin
unabhängig in der Widgetgrafik. Die Projektionen verändern weder `KAM_AZ`
noch die Kamera-Pose in der Physik.

In den beiden Lage-SVGs liegt die ungedrehte Kameramarkierung oben am
Zifferblatt. Damit sie bei der dargestellten Konvention am projizierten
Standpunkt erscheint, wird sie für Stampfen mit `90° − α_pitch` und für
Krängung mit `90° − α_roll` um den Zifferblattmittelpunkt gedreht. Die
positive SVG-Rotation verläuft im Bildschirmkoordinatensystem im
Uhrzeigersinn. Für den Kompass bleibt die bestehende Zuordnung von `KAM_AZ`
unverändert.

Ist ein erforderlicher Kameraeingang ungültig oder die Projektion in der
jeweiligen Ansichtsebene numerisch nicht definiert (beide
Projektionskomponenten sind null), wird ausschließlich der Kameramarker als
nicht verfügbar behandelt. Ein gültiger primärer Messwert des Widgets bleibt
gültig; eine nicht definierte Projektion darf nicht durch `0°` ersetzt
werden. Die illustrativen Kamerarotationen in den unveränderten
SVG-Quelldateien sind keine Laufzeitwerte.

## 9. Zielkomposition weiterer Instrumentkarten

Die folgenden Karten gehören zur langfristigen Zielkomposition und nicht zur
Zwischenlösung aus `Spec0107`. Ihre spätere Umsetzung erfordert passende
Interfaces, verfügbare Physikdaten und die bestehende gemeinsame
Elementgestaltung gemäß `Spec0087`.

### Spec0110 — Zielkomposition und Kartenpositionen

Die langfristige Instrumentansicht ordnet vier getrennte Karten an:

1. Kompass oben links;
2. Fahrt über Grund oben rechts;
3. Fahrt durchs Wasser unten links;
4. Wind unten rechts.

Jede Karte ist eine eigene Qt-Widget-Klasse. Gemeinsame Rahmengestaltung,
Typografie und Elemente folgen der nummerierten Master-Elementgrafik und
`Spec0087`; eine Karte zeigt nur ihre fachlich zugehörigen Elemente. Diese
Zielanordnung ersetzt nicht die bis zu einer gesonderten Spezifikations-
änderung verbindliche Zwischenlösung.

### Spec0111 — Zielkarte Fahrt über Grund

Die Karte für Fahrt über Grund zeigt `SOG` als Betrag der
Körpergeschwindigkeit über Grund und `COG` als deren gültige horizontale
Richtung gemäß `Spec0080`–`Spec0081`. Ihre kleine Richtungsscheibe kennzeichnet
ausschließlich `COG`, nicht `HDG`. Werte und Labels müssen den Bezugsrahmen
erkennen lassen. Die Karte gehört zur späteren Zielkomposition und wird durch
die erste Widgetstufe nicht implementiert.

### Spec0112 — Zielkarte Fahrt durchs Wasser

Die Karte für Fahrt durchs Wasser zeigt `STW`, `CTW` und den
vorzeichenbehafteten Abdriftwinkel `λ` gemäß `Spec0080`–`Spec0082`. Ihre
Kennzeichnung muss die Wasserreferenz von der Grundbewegung unterscheiden.
`λ` folgt Backbord-negativ/Steuerbord-positiv und ist nur anzuzeigen, wenn
Heading und Kurs durchs Wasser gültig sind. Diese Karte gehört zur späteren
Zielkomposition und wird durch die erste Widgetstufe nicht implementiert.

### Spec0113 — Zielkarte Wind

Die Windkarte ist für `TWS`, `TWD`, `AWS`, `AWA` und `TWA` gemäß
`Spec0080`–`Spec0081` vorgesehen. Solange kein gültiger Windzustand verfügbar
ist, zeigt sie einen ausdrücklichen Nichtverfügbarkeitszustand, keine
Windzahlen und keine künstlichen Nullwerte. Gültige Werte müssen dieselbe
Gültigkeits- und Einheitenbehandlung wie die übrigen Instrumentkarten
erhalten. Die Karte gehört zur späteren Zielkomposition und wird durch die
erste Widgetstufe nicht implementiert.

## 8. Spezifikationsgrafiken

### Spec0109 — Grafiken, Textvertrag und Rückverfolgbarkeit

Die SVG-Grafiken im Ordner `Spezifikationen` sind erklärende Schemata. Ihre
fachlich relevanten Achsen, Vorzeichen, Winkelbeziehungen und
Bewegungskonventionen müssen durch die jeweils genannten Textpunkte dieser
Spezifikation beschrieben und durch deren Tests überprüfbar sein. Die Grafik
ist weder eine zusätzliche Datenquelle noch eine Erlaubnis, nicht
spezifizierte Produktionswerte, Gelenkgrenzen oder Yachtgeometrien
anzunehmen. Rein illustrative Abstände, Formen und Beispielwinkel sind nicht
maßstäblich und keine Laufzeit- oder Defaultwerte.

| Grafik | Verbindlicher Textvertrag |
|---|---|
| [Grafik_Welt_und_Koerperachsen.svg](./Grafik_Welt_und_Koerperachsen.svg) | Welt- und Körperachsen, Rechtshändigkeit, gemeinsamer Weltzustand und Transformation in den Körperframe gemäß `Spec0070`–`Spec0077`; Prüfnachweise gemäß `Spec0088`. |
| [Koerperlage_und_Winkel.svg](./Koerperlage_und_Winkel.svg) | Ableitung von `HDG`, `φ`, `θ` und `ψ`, ihre Vorzeichen und die Trennung zwischen physikalischer Rotation und Anzeigevorzeichen gemäß `Spec0078`, `Spec0079` und `Spec0093`; Prüfnachweise gemäß `Spec0088`. |
| [Kamerawinkel_Weltkompass_v0.7.svg](./Kamerawinkel_Weltkompass_v0.7.svg) | Giergekoppelter Kameraazimut, konstanter Offset, horizonstabile Elevation und Rollfreiheit gemäß `Spec0092`; Projektion in die Widgetansichten gemäß `Spec0108`. |
| [Bewegliche_Teile_und_Stellwinkel.svg](./Bewegliche_Teile_und_Stellwinkel.svg) | Teilpose und Gelenktransformation, Segeltrim, Ruderwinkel sowie alternative Schwertkinematiken und Stellungsanteile gemäß `Spec0083`–`Spec0086`; Prüfnachweise gemäß `Spec0090`. |

Die Zuordnung ist vollständig: Eine fachliche Aussage, die für Umsetzung oder
Abnahme erforderlich ist, darf nicht allein in einer Grafik stehen. Wird eine
Grafik fachlich geändert, müssen ihre zugeordneten Textpunkte und Tests
gemeinsam geprüft und bei Bedarf geändert werden; die Bilddatei selbst
erweitert oder überschreibt keinen Textvertrag.
