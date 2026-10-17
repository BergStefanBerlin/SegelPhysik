# Glossar: Wind- und Yachtbewegungsgroessen (SegelPhysik)

**Neuordnung nach Medium -> Skalar / Vektor / Winkel**

Stand: 17.10.2026
Vorlage: `doc/Backlog/Ideen/glossar_wind_bewegung.md` (Stand 16.10.2026)
Bezug: `windsimulation_anleitung.md` (Stufen S1-S6)

## Zweck

Feste Begriffsliste fuer die Windsimulation (`wind.py`, `segelaero.py`) und das
Yachtbewegungsmodell. Alle Groessen werden nach und nach implementiert.

**Nicht Teil des Projekts:** Wahrer Kurs (TC), missweisender Kurs (MC),
Kompasskurs (CC) - es gibt derzeit kein Nord/Sued/Ost/West im Modell. Die
Richtung "0 Grad" ist immer die Bootslaengsachse bzw. eine simulierte
Weltreferenzrichtung, keine geografische.

**Konvention:** Windrichtungen sind immer "aus dem" Winkel kommend
(meteorologisch), Kurse sind "nach dem" Winkel gerichtet (nautisch).

---

## Ordnungsprinzip

**Primaer: Medium / Bezugssystem** - worin oder worauf die Groesse definiert ist.

| # | Medium / Bezugssystem | Was dort gemessen wird |
|---|---|---|
| A | **Luft** | Wind (wahr, scheinbar, Fahrtwind), Windprofil |
| B | **Wasser** | Fahrt durchs Wasser, Stroemung, Abdrift |
| C | **Grund** | Fahrt ueber Grund, Fortschritt zum Ziel |
| D | **Boot** (Bezugssystem, kein Medium) | Kurs, Lage, Bewegung des Rumpfes |
| E | **Segel** (lokales Bezugssystem) | Anstroemung am Profil |

**Sekundaer: Typ der Groesse**

| Typ | Bedeutung | Beispiel |
|---|---|---|
| **Skalar** | nur ein Betrag, keine Richtung | TWS, SOG, VMG |
| **Vektor** | Betrag **und** Richtung | v_TW, v_AW, v_COG |
| **Winkel** | skalare Richtungsangabe (der Richtungsanteil eines Vektors) | TWD, TWA, HDG |

> **Wichtig:** Eine Richtung allein ist noch kein Vektor. TWD ist ein Winkel;
> erst zusammen mit TWS wird daraus der Vektor v_TW. Diese Trennung ist der
> Grund fuer die dritte Kategorie.

---

## Uebersichtsmatrix

| Medium | Skalar | Vektor | Winkel |
|---|---|---|---|
| **A Luft** | TWS, AWS, Windgradient, Boee | v_TW, v_AW, v_BW | TWD, AWD, TWA, AWA |
| **B Wasser** | BS/STW | v_BS, v_CTW, v_Stroemung | lambda |
| **C Grund** | SOG, VMG, VMC | v_COG | COG-Richtung |
| **D Boot** | psi_punkt | Translationsvektor, Rotationsvektor | HDG, psi, phi, theta |
| **E Segel** | alpha, AWS_lokal | v_lokal | AWA_lokal |

---

## A) Medium Luft

### A.1 Skalare

| Deutsch | Englisch | Abk. | Definition | Einheit | Umsetzung |
|---|---|---|---|---|---|
| Wahre Windgeschwindigkeit | True Wind Speed | TWS | Betrag des wahren Winds, Bezugshoehe 10 m; TWS = Betrag(v_TW) | m/s | S1 |
| Scheinbare Windgeschwindigkeit | Apparent Wind Speed | AWS | Betrag des scheinbaren Winds; AWS = Betrag(v_AW) | m/s | S3 |
| Windgradient | Wind Gradient / Wind Shear | - | Zunahme der Windgeschwindigkeit mit der Hoehe: v(z) = v10 * (z/10)^p | m/s | S2 |
| Boeenstaerke | Gust Magnitude | - | Kurzzeitige Erhoehung der Windgeschwindigkeit | m/s | offen |

### A.2 Vektoren

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Wahrer Wind | True Wind | v_TW | Wind ueber Grund, ungestoert durch die Bootsbewegung | S1 |
| Fahrtwind | Boat Wind / Head Wind | v_BW | Vom Boot erzeugter Gegenwind; v_BW = -v_BS | S3 |
| Scheinbarer Wind | Apparent Wind | v_AW | Vektorsumme aus wahrem Wind und Fahrtwind: v_AW = v_TW + v_BW | S3 |
| Boeenvektor | Gust Vector | - | Richtungsaenderung waehrend einer Boee | offen |

### A.3 Winkel / Richtungen

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Wahre Windrichtung | True Wind Direction | TWD | Richtung, aus der der wahre Wind weht | S1 |
| Scheinbare Windrichtung | Apparent Wind Direction | AWD | Richtung, aus der der scheinbare Wind am Boot ankommt | S3 |
| Wahrer Windwinkel | True Wind Angle | TWA | Winkel zwischen Bootslaengsachse und wahrem Wind | S3 |
| Scheinbarer Windwinkel | Apparent Wind Angle | AWA | Winkel zwischen Bootslaengsachse und scheinbarem Wind - steuert den Segeltrim | S3 |

---

## B) Medium Wasser

### B.1 Skalare

| Deutsch | Englisch | Abk. | Definition | Einheit | Umsetzung |
|---|---|---|---|---|---|
| Bootsgeschwindigkeit | Boat Speed / Speed Through Water | BS / STW | Geschwindigkeit relativ zum Wasser; BS = Betrag(v_BS) | m/s | S3 |

### B.2 Vektoren

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Bootsgeschwindigkeit (Vektor) | Boat Velocity | v_BS | Bewegungsvektor des Bootes relativ zum Wasser | S3 |
| Kurs durchs Wasser | Course Through Water | v_CTW | Tatsaechliche Bewegungsrichtung relativ zum Wasser (Heading + Abdrift) | S5 |
| Stroemung | Current Set and Drift | v_Stroemung | Wasserstroemung; Set = Richtung, Drift = Betrag | offen |

### B.3 Winkel

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Abdriftwinkel | Leeway Angle / Drift Angle | lambda | Winkel zwischen Heading und CTW - das "Abwaertsrutschen" durch Seitenkraft (Kiel) | S5 |

---

## C) Medium Grund

### C.1 Skalare

| Deutsch | Englisch | Abk. | Definition | Einheit | Umsetzung |
|---|---|---|---|---|---|
| Geschwindigkeit ueber Grund | Speed Over Ground | SOG | Geschwindigkeit relativ zum Grund (BS +/- Stroemung) | m/s | offen |
| Geschwindigkeit in Windrichtung | Velocity Made Good | VMG | Fortschrittskomponente entlang der Windrichtung - entscheidend fuer die optimale Kreuz | m/s | S6 |
| Zielgeschwindigkeit | Velocity Made Good to Course | VMC | Fortschrittskomponente entlang des Zielkurses | m/s | offen |

### C.2 Vektoren

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Kurs ueber Grund | Course Over Ground | v_COG | Bewegungsrichtung relativ zum Grund (CTW + Stroemung) | offen |

### C.3 Winkel

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Grundkurs-Richtung | Course Over Ground (direction) | COG | Richtungsanteil von v_COG | offen |

---

## D) Bezugssystem Boot

### D.1 Skalare

| Deutsch | Englisch | Abk. | Definition | Einheit | Umsetzung |
|---|---|---|---|---|---|
| Giergeschwindigkeit | Yaw Rate | psi_punkt | Drehgeschwindigkeit um die Hochachse (wichtig fuer Ruder-/Fock-Anstroemung) | rad/s | vorhanden |

### D.2 Vektoren

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Translationsvektor | Translation | - | Surge (x, voraus), Sway (y, seitlich), Heave (z, hoch/runter) | vorhanden |
| Rotationsvektor | Rotation | - | Roll (phi), Pitch (theta), Yaw (psi) | vorhanden |

### D.3 Winkel

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Heading / Steuerkurs | Heading | HDG | Richtung der Bootslaengsachse (wo die Nase hinzeigt) | S3 |
| Gieren | Yaw | psi | Rotation um die Hochachse (Kursaenderung) | vorhanden |
| Kraengen | Roll / Heel | phi | Rotation um die Laengsachse | vorhanden |
| Stampfen / Trimmen | Pitch | theta | Rotation um die Querachse (Bug hoch/runter) | vorhanden |

---

## E) Bezugssystem Segel (lokal)

### E.1 Skalare

| Deutsch | Englisch | Abk. | Definition | Einheit | Umsetzung |
|---|---|---|---|---|---|
| Anstellwinkel | Angle of Attack | alpha / AoA | Winkel zwischen scheinbarer Anstroemung und Segelsehne - bestimmt Lift/Stall | Grad | S4 |
| Lokale scheinbare Windgeschwindigkeit | Local Apparent Wind Speed | AWS_lokal | AWS je Streifen/Messpunkt | m/s | S3 |

### E.2 Vektoren

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Lokaler Anstroemvektor | Local Flow Vector | v_lokal | Anstroemung am Segelstreifen | S3 |

### E.3 Winkel

| Deutsch | Englisch | Abk. | Definition | Umsetzung |
|---|---|---|---|---|
| Lokaler scheinbarer Windwinkel | Local Apparent Wind Angle | AWA_lokal | AWA je Streifen/Messpunkt | S3 |
| Einfallswinkel | Incidence Angle | - | Synonym zu Anstellwinkel (Tragfluegeltheorie) | - |

---

## F) Paare: Vektor und sein Betrag

Jeder Vektor hat einen skalaren Betrag. Diese Paare gehoeren zusammen:

| Vektor | Betrag (Skalar) | Richtung (Winkel) | Medium |
|---|---|---|---|
| v_TW | TWS | TWD | Luft |
| v_AW | AWS | AWD | Luft |
| v_BW | Betrag(v_BW) = BS | entgegen HDG | Luft |
| v_BS | BS / STW | HDG + lambda | Wasser |
| v_CTW | Betrag(v_CTW) | CTW | Wasser |
| v_Stroemung | Drift | Set | Wasser |
| v_COG | SOG | COG | Grund |

---

## G) Wichtige Zusammenhaenge (Merksaetze)

- **Wind-Dreieck:** v_AW = v_TW + v_BW, wobei v_BW = -v_BS
  (Fahrtwind ist der negative Vektor der Bootsgeschwindigkeit).
- **AWA != TWA:** Nur bei stehendem Boot sind sie gleich. Am Wind wird der
  scheinbare Wind spitzer (dreht nach vorn), raumwaerts weiter.
- **Kurskette:** Heading -> (+lambda) -> CTW -> (+Stroemung) -> COG.
- **Wer braucht was:**
  - Segelkraft: AWS/AWA je Streifen (lokal!)
  - Kiel-/Ruderhydrodynamik: STW + Abdriftwinkel lambda (Anstellwinkel der Finne)
  - Navigation/Anzeige: SOG/COG, VMG

---

## H) Kursbezeichnungen (Didaktik, keine Groessen)

Diese Begriffe beschreiben Segelkurse, sind aber keine messbaren Groessen:

| Deutsch | Englisch | Bedeutung |
|---|---|---|
| Am-Wind-Winkel | Upwind Angle / Close-Hauled | Kleiner TWA (~30-45 Grad), hart am Wind segeln |
| Halber Wind | Beam Reach | TWA ~90 Grad (Querwind) |
| Facher Wind | Broad Reach | TWA ~135 Grad |
| Raumwind-Winkel | Downwind Angle / Running | Grosser TWA (~150-180 Grad) |
| Schlagen | Yawing / Snaking | Periodisches Gieren am Raumwind (selbsterregt) - Phaenomen, keine Groesse |

---

## I) Umsetzungsplan (gekoppelt an windsimulation_anleitung.md, S1-S6)

| Stufe | Baustelle | Neue Groessen | Medium |
|---|---|---|---|
| S1 | wind.py: True Wind aus physik.json | TW, TWS, TWD | Luft |
| S2 | Windprofil ueber Hoehe | Windgradient | Luft |
| S3 | Apparent Wind pro Streifen/Messpunkt | BW, AW, AWS, AWD, TWA, HDG, BS/STW | Luft / Wasser / Boot |
| S4 | Segelkraft | AoA/alpha (je Streifen) | Segel |
| S5 | mit Hydrodynamik | CTW, lambda | Wasser |
| S6 | Anzeige/Demo | VMG; spaeter: SOG, COG, Stroemung, Boeen | Grund / Wasser / Luft |

Offen: Boeenmodell, Wasserstroemung (-> COG/SOG), Zielkurs (VMC).
