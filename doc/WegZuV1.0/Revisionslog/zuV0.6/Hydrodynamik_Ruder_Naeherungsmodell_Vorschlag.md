# Ruderkraft-Näherungsmodell – Vorschlag vor Implementierung

**Stand:** 17.10.2026<br>
**Status:** Isoliert implementiert nach Nutzerfreigabe; nicht validiert und
nicht produktiv aktiviert<br>
**Zweck:** Eingrenzung eines ausdrücklich nicht validierten, isolierten
Ruderkraft-Zweigs. Keine Produktivfreigabe und kein Nachweis, dass das
Yachtruder ausreichend dimensioniert ist.

## 1. Nutzerentscheidungen und harte Grenzen

Am 17.10.2026 hat die Nutzerin:

- einem getrennten, nicht validierten Näherungszweig zugestimmt, sofern
  Gleichungen, Parameter und Gültigkeitsgrenzen vor der Implementierung
  fachlich geprüft werden;
- für die Testkinematik die vorhandene `yacht1`-Rudergeometrie und eine
  angenommene Achse an der Vorderkante vorgegeben;
- den Geltungsbereich auf Verdrängungsfahrt begrenzt;
- die fachliche Quellen-/Gleichungsprüfung dem Assistenten übertragen.

Die bestehende Spezifikation Spec0065 verlangt weiterhin einen Nachweis aus
einer autoritativen Konstruktionsquelle. Die folgende, nutzerbeauftragte
Geometrieannahme erfüllt diesen Nachweis **nicht**. Sie darf daher nur in
einem getrennten Testaufbau verwendet werden. Das Yachtmanifest, sein
Produktivgelenk und die Produktionspose bleiben unverändert.

## 2. Quellenbefund

1. Yasukawa und Yoshimura beschreiben das MMG-Manövriermodell für Schiffe.
   Es liefert eine nachvollziehbare Modellstruktur für Ruder-Normalkraft,
   lokale Anströmung und endliche Streckung. Seine Interaktionsparameter und
   Koeffizienten stammen aus dem jeweiligen Schiff-/Versuchskontext und
   werden hier **nicht** auf `yacht1` übertragen.
2. TU-Delft-Schleppversuche und RANS-Vergleiche zur Segelyacht zeigen, dass
   Rumpf und Kiel den Rudereinfluss verändern können. Die Arbeit berichtet
   asymmetrischen Stall, Abweichungen zwischen Versuchsreihen und nicht
   erklärbare negative Widerstandswerte eines Aufbaus. Eine isolierte
   Ruderkennlinie ist deshalb keine validierte Yachtkennlinie.
3. Eine CFD-Studie zur 470-Klasse berichtet für ihre eigene Geometrie
   Stallwinkel in der Größenordnung 30–35°. Diese Werte sind weder
   mechanische Ausschläge noch auf `yacht1` übertragbare Kennwerte. Sie
   begründen hier insbesondere keine Nutzung des Näherungsmodells im Stall.
4. Die übliche Bauart unterscheidet unbalancierte Ruder mit Drehachse an der
   Vorderkante von balancierten Rudern mit einer hinter der Vorderkante
   liegenden Achse. „Achse an der Vorderkante“ ist daher eine plausible
   **unbalancierte Testannahme**, aber keine allgemeingültige Aussage über
   Segelyachten.

## 3. Vorgeschlagene Testkinematik

Das Manifest ordnet die Yachtachsen rechtshändig als `x` nach vorn (Bug),
`y` nach Backbord und `z` nach oben zu. Die Modellwasserlinie liegt bei
`z = 0`.

Im unveränderten Blatt-Frame hat `ruder` folgende abgeleitete Geometrie:

| Größe | Messwert |
|---|---:|
| Ausdehnung | `0,2625 × 0,0275 × 0,424575 m` |
| Vorderkantenabschnitt des Meshes | `x = -1,825 m`, `y` um die Mittellinie, `z = -0,4375 … -0,19985 m` |
| vorgeschlagener Achspunkt | `(-1,825; 0; -0,318675) m` |
| vorgeschlagene Achsrichtung | `(0; 0; 1)` |

Der Punkt liegt auf dem geraden Vorderkantenabschnitt; die Richtung ist
tangential zu diesem Abschnitt. Für den Test wird die Rotation um diesen
Punkt berechnet, sodass die Achse stationär bleibt. Vorzeichen- und
Reglerrichtung werden durch einen automatisierten Kleinwinkelsign-/Moment-
Test festgelegt. Diese Geometrieableitung beweist weder einen vorhandenen
Ruderschaft noch Lagerung, mechanische Grenzen oder konstruktive Freigängigkeit.

**Nicht festgelegt:** reale mechanische Winkelanschläge. Für das erste
Rechenmodell wird stattdessen ein Gültigkeitsbereich des effektiven
Anströmwinkels verwendet; Eingaben außerhalb dieses Bereichs müssen explizit
als nicht unterstützt abgelehnt werden und dürfen nicht stillschweigend
geclippt werden.

## 4. Vorgeschlagenes isoliertes Kraftmodell

Nur der Ruder-Normalkraft-/Auftriebsanteil wird modelliert; kein
Rumpfwiderstand, keine Rumpf-/Kielinteraktion, kein Propeller, keine Wellen,
keine Profilwiderstandskennlinie und kein Stallmodell.

Für ruhendes Wasser wird die lokale Geschwindigkeit des Ruder-Bezugspunkts
aus der Starrkörperkinematik berechnet:

```text
v_R = v_Koerper + omega_Koerper × r_R
U_R = Betrag der horizontalen Komponente von v_R
beta_R = atan2(v_R,y, v_R,x)
alpha_R = delta_R + beta_R
```

Vorzeichen werden so gewählt, dass bei Vorwärtsfahrt ein positiver
Ruderwinkel die erwartete Gegenkraft erzeugt; die Konvention muss in
Kleinwinkelsolltests bestehen.

Die vorläufige MMG-artige Normalkraft lautet:

```text
F_N = 0,5 * rho * U_R^2 * A_R * f_alpha * sin(alpha_R)
f_alpha = 6,13 * AR / (AR + 2,25)
AR = span^2 / A_R
```

Die Kraft wird in der horizontalen Ebene normal zur lokalen Bewegungsrichtung
angesetzt; ein idealisierter induzierter Widerstandsanteil wird als
`C_D,i = C_N^2 / (pi * AR)` mit idealisiertem Oswald-Faktor `e = 1`
ergänzt. Dieser Anteil ist nur ein idealisierter induzierter
Widerstand; Profil-/Formwiderstand bliebe ausdrücklich unmodelliert.

### Geometrisch abgeleitete Eingaben für `yacht1`

| Parameter | Wert | Herkunft/Status |
|---|---:|---|
| Projektion der Rudermeshfläche auf die `x-z`-Ebene `A_R` | `0,0858247253 m²` | Meshmessung; geometrisch abgeleitet, hydrodynamische Bezugsfläche nicht extern bestätigt |
| Spannweite | `0,424575 m` | Meshmessung |
| Streckung `AR` | `2,10037294` | `span²/A_R`, geometrisch abgeleitet |
| MMG-artiger Steigungsfaktor `f_alpha` | `2,95958216 rad⁻¹` | Formel aus der Literatur; Anwendung auf dieses Yachtmesh ist eine Näherung |
| Wasserdichte `rho` | aus der vorhandenen Materialkonfiguration | keine neue Stoffkonstante |

Die Fläche nutzt die Projektion des vollständigen Rudermeshes. Sie ist kein
vermessener wirksamer Flächenwert im Kiel-/Rumpf-Nachlauf. Der
Hauptlauf verwendet den aus der Formel abgeleiteten Faktor; als
**Sensitivitätsfälle**, nicht als statistisches Konfidenzintervall, werden
`0,5`, `1,0` und `1,5` mal `f_alpha` vorgeschlagen. Die breite Spanne ist
eine explizite Robustheitsprüfung, keine behauptete Messunsicherheit.
Die Wirkung greift am geometrischen Flächenschwerpunkt an; dieser ist kein
nachgewiesener Druckmittelpunkt.

### Gültigkeitsbereich

- Quasi-stationäre horizontale Anströmung, Verdrängungsfahrt und
  effektiver Anströmwinkel `|alpha_R| <= 10°`.
- Außerhalb des Bereichs wird der Modellaufruf abgelehnt. Keine
  Stall-Extrapolation.
- Die 10° sind eine konservative Modellgrenze für diesen unvalidierten
  Zweig, kein aus dem `yacht1`-Versuch abgeleiteter Stallwinkel.
- Kraftstatus: `berechnete_naeherung`; nie
  `gegen_externe_referenz_validiert`.
- Die Resultate dürfen nicht für eine Produktivkonfiguration, eine Aussage
  zur Rudergröße oder einen nautischen Sicherheitsnachweis verwendet werden.

## 5. Geschwindigkeits-Sensitivitätsfälle

Die Länge an der bestehenden Modellwasserlinie `z = 0` wurde aus dem
Rumpfmesh mit etwa `L_WL = 4,13894 m` abgeleitet. Als nachvollziehbarer
Sensitivitätsraster wird vorgeschlagen:

| Froude-Zahl `Fn` | Geschwindigkeit (m/s) | Geschwindigkeit (kn) |
|---:|---:|---:|
| 0,10 | 0,6371 m/s | 1,238 kn |
| 0,20 | 1,2742 m/s | 2,477 kn |
| 0,30 | 1,9113 m/s | 3,715 kn |
| 0,35 | 2,2298 m/s | 4,334 kn |

`Fn = V / sqrt(g * L_WL)` dient hier der reproduzierbaren Skalierung. Die
Obergrenze `Fn = 0,35` ist eine konservative Grenze dieses Testplans, keine
universelle Definition des Übergangs von Verdrängungs- zu Gleitfahrt. Es
wird kein Rumpfauftrieb oder Gleitfahrtmodell ergänzt.

## 6. Fachliche Review-Entscheidung

Die Nutzerin hat den Vorschlag am 17.10.2026 für den getrennten
Software-/Lehrmodellzweig freigegeben. Die Implementierung hält folgende
Grenzen ein:

1. Testkinematik und Quellenstatus sind in
   `segelphysik/core/hydrodynamik_ruder_naeherung.py` als Annahme markiert;
   das Produktivmanifest ist unverändert.
2. Modellgleichung, Eingaben und Gültigkeitsbereich stehen in Code/API und
   dieser Dokumentation; außerhalb des Winkelbereichs folgt eine explizite
   Fehlerantwort.
3. `tests/test_hydrodynamik_ruder_naeherung.py` prüft Geometrieableitung,
   Testachsenpose, Nullfluss, Kraft- und Momentvorzeichen, Symmetrie bei
   Vorzeichenwechsel, lokale Giergeschwindigkeit, Kraft-/Moment-Hebelarm,
   Dissipation, Sensitivitätsfaktoren `0,5`, `1,0` und `1,5` sowie Ablehnung
   außerhalb des Bereichs.
4. Die 50-%-/10-s-Manöverabnahme und ein Variantenentscheid zur Rudermasse
   oder -größe bleiben gesperrt, bis ein externer passender Referenzvergleich
   und reale Ruderkinematikdaten vorliegen.
5. Das Modell ist nicht an den Produktivsolver angeschlossen; die aktuelle
   Live-Performance-Abnahme ist ohnehin nicht bestanden.

Review-Entscheidung und Nutzerfreigabe sind keine unabhängige
hydrodynamische Validierung. Der implementierte Zweig kann Softwareverhalten
und Sensitivität demonstrieren, nicht die reale Yachtleistung vorhersagen.

## 7. Quellen

- Yasukawa, H.; Yoshimura, Y. (2015), *Introduction of MMG standard method
  for ship maneuvering predictions*,
  [DOI 10.1007/s00773-014-0293-y](https://doi.org/10.1007/s00773-014-0293-y).
- TU Delft, *Keel-Rudder Interaction*,
  [Repository abstract](https://repository.tudelft.nl/record/uuid:1be75bf7-04b2-4089-95af-95ac4031e034).
- Lin et al. (2018), *Investigation on Rudder Hydrodynamics for 470 Class
  Yacht*, [DOI 10.3390/proceedings2060308](https://doi.org/10.3390/proceedings2060308).
- U.S. Naval Academy, *Naval Engineering I, Chapter 9*,
  [PDF](https://usna.edu/NAOE/_files/documents/Courses/EN400/02.09%20Chapter%209.pdf).
- Für die Froude-Skalierung siehe die Darstellung von
  [Geschwindigkeit, Froude-Zahl und Rumpflänge](https://superyachtguide.com/superyacht-design/naval-architecture/resistance-powering-efficiency/speed-froude-number-and-hull-length-effects/).
- Für Abgrenzung von Modell- und Referenzmessung siehe außerdem die
  [ITTC recommended procedures](https://www.ittc.info/media/1301/75-02-06-02.pdf).
