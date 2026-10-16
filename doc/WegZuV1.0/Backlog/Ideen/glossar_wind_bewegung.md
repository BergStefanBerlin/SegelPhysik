# Glossar: Wind- und Yachtbewegungsgrößen (SegelPhysik)

Stand: 16.10.2026

## Zweck

Feste Begriffsliste für die Windsimulation (`wind.py`, `segelaero.py`) und das
Yachtbewegungsmodell. Alle Größen werden nach und nach implementiert; der
Umsetzungsplan steht am Ende.

**Nicht Teil des Projekts:** Wahrer Kurs (TC), missweisender Kurs (MC),
Kompasskurs (CC) - es gibt derzeit kein Nord/Süd/Ost/West im Modell. Die
Richtung "0 Grad" ist immer die Bootslängsachse bzw. eine simulierte
Weltreferenzrichtung, keine geografische.

Konvention: Windrichtungen sind immer "aus dem" Winkel kommend
(meteorologisch), Kurse sind "nach dem" Winkel gerichtet (nautisch).

## 1) Windarten und Windgroessen

| Deutsch | Englisch | Abkuerzung | Definition | Umsetzung |
|---|---|---|---|---|
| Wahrer Wind | True Wind | TW | Wind ueber Grund, ungestoert durch die Bootsbewegung | S1 (Konfiguration) |
| Wahre Windgeschwindigkeit | True Wind Speed | TWS | Betrag des wahren Winds, bezogen auf Bezugshoehe 10 m | S1 |
| Wahre Windrichtung | True Wind Direction | TWD | Richtung, aus der der wahre Wind weht | S1 |
| Fahrtwind | Boat Wind / Head Wind | BW | Vom Boot erzeugter Gegenwind; Betrag = Bootsgeschwindigkeit, Richtung = entgegen Kurs | S3 |
| Scheinbarer Wind | Apparent Wind | AW | Vektorsumme aus wahrem Wind und Fahrtwind - was am fahrenden Boot ankommt | S3 |
| Scheinbare Windgeschwindigkeit | Apparent Wind Speed | AWS | Betrag des scheinbaren Winds | S3 |
| Scheinbare Windrichtung | Apparent Wind Direction | AWD | Richtung, aus der der scheinbare Wind ankommt (am Boot gemessen) | S3 |
| Windgradient | Wind Gradient / Wind Shear | - | Zunahme der Windgeschwindigkeit mit der Hoehe: v(z) = v10 * (z/10)^p | S2 |
| Boe / Boenwind | Gust / Squall | - | Kurzzeitige Erhoehung von Geschwindigkeit und/oder Richtungsanderung | spaeter (offen) |

## 2) Winkel zwischen Boot und Wind

| Deutsch | Englisch | Abkuerzung | Definition | Umsetzung |
|---|---|---|---|---|
| Wahrer Windwinkel | True Wind Angle | TWA | Winkel zwischen Bootslaengsachse und wahrem Wind | S3 |
| Scheinarer Windwinkel | Apparent Wind Angle | AWA | Winkel zwischen Bootslaengsachse und scheinbarem Wind - steuert den Segeltrim | S3 |
| Am-Wind-Winkel | Upwind Angle / Close-Hauled | - | Kleiner TWA (~30-45 Grad), hart am Wind segeln | Didaktik, keine Berechnung |
| Raumwind-Winkel | Downwind Angle / Running | - | Grosser TWA (~150-180 Grad) | Didaktik |
| Halber/Facher Wind | Beam Reach / Broad Reach | - | TWA ~90 Grad (Querwind) bzw. ~135 Grad | Didaktik |
| Anstellwinkel (Segel) | Angle of Attack | AoA / alpha | Winkel zwischen scheinbarer Anstroemung und Segelsehne - bestimmt Lift/Stall | S4 (je Streifen) |
| Einfallswinkel | Incidence Angle | - | Synonym zu Anstellwinkel (Tragfluegeltheorie) | - |

## 3) Kurs und Geschwindigkeit

| Deutsch | Englisch | Abkuerzung | Definition | Umsetzung |
|---|---|---|---|---|
| Heading / Steuerkurs | Heading | HDG | Richtung der Bootslaengsachse (wo die Nase hinzeigt) | S3 (aus Zustand6DOF) |
| Kurs durchs Wasser | Course Through Water | CTW | Tatsaechliche Bewegungsrichtung relativ zum Wasser (Heading + Abdrift) | S5 |
| Kurs ueber Grund | Course Over Ground | COG | Bewegungsrichtung relativ zum Grund (CTW + Versatz durch Stroemung) | spaeter (mit Stroemung) |
| Bootsgeschwindigkeit | Boat Speed / Speed Through Water | BS / STW | Geschwindigkeit relativ zum Wasser | S3 |
| Geschwindigkeit ueber Grund | Speed Over Ground | SOG | Geschwindigkeit relativ zum Grund (BS +/- Stroemung) | spaeter |
| Abdriftwinkel | Leeway Angle / Drift Angle | lambda | Winkel zwischen Heading und CTW - das "Abwaertsrutschen" durch Seitenkraft (Kiel) | S5 (mit Hydrodynamik) |
| Versatz durch Stroemung | Current Set and Drift | - | Vektorsumme aus CTW -> COG (Wasserstroemung) | spaeter |
| Geschwindigkeit in Windrichtung | Velocity Made Good | VMG | Fortschrittskomponente entlang der Windrichtung - entscheidend fuer die optimale Kreuz | S6 (Anzeige) |
| Zielgeschwindigkeit | Velocity Made Good to Course | VMG-C / VMC | Fortschrittskomponente entlang des Zielkurses | spaeter |

## 4) Bewegungsgroessen (6 DOF)

| Deutsch | Englisch | Abkuerzung | Definition | Umsetzung |
|---|---|---|---|---|
| Laengsbewegung | Surge | - | Translation entlang x (voraus) | vorhanden (Zustand6DOF) |
| Querbewegung | Sway | - | Translation entlang y (seitlich) | vorhanden |
| Vertikalbewegung | Heave | - | Translation entlang z (hoch/runter) | vorhanden |
| Gieren | Yaw | psi | Rotation um die Hochachse (Kursaenderung) | vorhanden |
| Kraengen | Roll / Heel | phi | Rotation um die Laengsachse | vorhanden |
| Stampfen / Trimmen | Pitch | theta | Rotation um die Querachse (Bug hoch/runter) | vorhanden |
| Kraengungswinkel | Heel Angle | phi | Momentaner Rollwinkel | vorhanden |
| Giergeschwindigkeit | Yaw Rate | psi_punkt | Drehgeschwindigkeit um die Hochachse (wichtig fuer Ruder-/Fock-Anstroemung) | vorhanden |
| Schlagen | Yawing / Snaking | - | Periodisches Gieren am Raumwind (selbsterregt) | Phaenomen, keine Groesse |

## 5) Wichtige Zusammenhaenge (Merksaetze)

- **Wind-Dreieck:** v_AW = v_TW + v_BW, wobei v_BW = -v_BS
  (Fahrtwind ist der negative Vektor der Bootsgeschwindigkeit).
- **AWA != TWA:** Nur bei stehendem Boot sind sie gleich. Am Wind wird der
  scheinbare Wind spitzer (dreht nach vorn), raumwaerts weiter.
- **Kurskette:** Heading -> (+lambda) -> CTW -> (+Stroemung) -> COG.
- **Wer braucht was:**
  - Segelkraft: AWS/AWA je Streifen (lokal!)
  - Kiel-/Ruderhydrodynamik: STW + Abdriftwinkel lambda (Anstellwinkel der Finne)
  - Navigation/Anzeige: SOG/COG, VMG

## 6) Umsetzungsplan (gekoppelt an windsimulation_anleitung.md, S1-S6)

| Stufe | Baustelle | Neue Groessen |
|---|---|---|
| S1 | wind.py: True Wind aus physik.json | TW, TWS, TWD |
| S2 | Windprofil ueber Hoehe | Windgradient |
| S3 | Apparent Wind pro Streifen/Messpunkt | BW, AW, AWS, AWD, TWA, HDG, BS/STW |
| S4 | Segelkraft | AoA/alpha (je Streifen) |
| S5 | mit Hydrodynamik | CTW, lambda |
| S6 | Anzeige/Demo | VMG; spaeter: SOG, COG, Stroemung, Boen |

Offen: Boenmodell, Wasserstroemung (-> COG/SOG), Zielkurs (VMC).
