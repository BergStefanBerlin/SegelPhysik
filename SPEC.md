# SPEC – 3D-Physiksimulations-Umgebung (SegelPhysik, v0.2)

**Status:** Verbindliche Spezifikation für den Neustart auf `main`
**Version:** 0.2.1 · **Datum:** 09.10.2026
**Zweck:** Eigenständige Echtzeit-3D-Umgebung mit Zwei-Phasen-Welt (Wasser/Luft),
Starrkörper-Dynamik und gekoppelter Fluid↔Festkörper-Interaktion als Fundament
für die spätere Segelboot-Simulation.

**Änderungen gegenüber v0.2:** Achsenkonvention konsistent auf z-Achse nach oben
umgestellt; Rolle der Luftphase präzisiert (vereinfachtes Kraftmodell, keine
Fluidsimulation); Becken-Default an Partikelauflösung gekoppelt; Glättungslänge
`h` definiert; Formulierungen in Abschnitt 4 und Kriterium 6 korrigiert.

---

## 1. Welt & Koordinatensystem

- Quaderförmiger Raum mit kartesischem Koordinatensystem.
- **Konvention:** Rechtshändiges System (x × y = z).
  - **z-Achse** zeigt nach oben; der Ursprung liegt auf der ungestörten
    Wasseroberfläche.
  - **x-Achse** zeigt in der Ebene der ungestörten Wasseroberfläche in Richtung
    Bug der späteren Yacht (Vorbereitung für v0.3; in v0.2 nur Namenskonvention).
  - **y-Achse** zeigt quer dazu in der Ebene der ungestörten Wasseroberfläche
    (positiv nach Steuerbord).
- Gesamthöhe `H` (konfigurierbar, Default: 9 m):
  - **Luft** (obere zwei Drittel): `z ∈ (0, 2H/3]` → Default: 6 m
  - **Wasser** (unteres Drittel): `z ∈ [−H/3, 0]` → Default: 3 m Wassertiefe
- Grundfläche des Raums konfigurierbar (Default: 10 m × 10 m); Wände und Boden
  sind feste Kollisionsgrenzen.
- Gravitation: `g = 9,81 m/s²` in negativer z-Richtung (im UI konfigurierbar).

> **Begründung der Defaults:** Wasser-Volumen = 10 · 10 · 3 = 300 m³. Bei der in
> Abschnitt 5 geforderten Partikelauflösung `Δx ≈ 0,25 m` ergibt sich
> N ≈ 300 / 0,25³ ≈ 19.200 ≈ 20.000 Partikel – eine Auflösung, bei der
> Oberflächenwellen sichtbar darstellbar sind (vgl. Kriterium 5).

## 2. Phase Wasser

| Größe | Wert |
|---|---|
| Dichte ρ_W | 1000 kg/m³ |
| Dynamische Viskosität η | ≈ 1 mPa·s |
| Hydrostatischer Druck | `p = ρ_W · g · h` (linear mit Tiefe h) |
| Auftrieb (Archimedes) | `F_A = ρ_W · V_verdrängt · g` |

- **Freie Oberfläche** bei z = 0 als Grenzschicht zur Luft; leicht wellend.
  Die Oberfläche ergibt sich implizit aus der SPH-Partikelverteilung
  (Partikeldichte-Schwellwert oder Oberflächen-Extraktion, z. B. Marching Cubes).

## 3. Phase Luft (vereinfachtes Kraftmodell – keine Fluidsimulation)

Die Luft wird in v0.2 **nicht** als Fluid simuliert (kein SPH für Luft). Sie geht
nur über die folgenden Kraftmodelle in die Dynamik ein:

| Größe | Wert |
|---|---|
| Dichte ρ_L | 1,225 kg/m³ (15 °C, Meereshöhe) |
| Quadratischer Widerstand | `F_D = ½ · ρ_L · c_w · A · v_rel²` |

- `v_rel = v_Körper − v_Wind`: der Widerstand wirkt relativ zum lokalen Windfeld.
- **Windfeld (Pflichtfeature, nicht optional):**
  - Konfigurierbar über Richtung (Azimut) und Geschwindigkeit (m/s).
  - Default: homogenes Feld; Schnittstelle so entwerfen, dass später ein
    ortsabhängiges Feld (Profile, Böen) eingesetzt werden kann.

## 4. Simulierbare Objekte

- **Starre Körper:** Kugeln und Quader.
  - Attribute: Masse, Dichte, Reibungskoeffizient, Restitutionskoeffizient,
    Anfangsposition/-geschwindigkeit.
  - Defaults: Reibungskoeffizient μ = 0,5; Restitutionskoeffizient e = 0,3
    (im UI pro Objekt änderbar).
- **Verhalten:** Dichte < 1000 kg/m³ → schwimmt; > 1000 kg/m³ → sinkt.
- **Kollisionen:** Körper↔Körper sowie Körper↔Wände/Boden.
- **Teil-Eintauchen:** Der verdrängte Teilvolumenanteil wird explizit berechnet:
  - Quader: analytisch über den eingetauchten Anteil der Höhe.
  - Kugel: analytisch über die Kappenhöhe (Segmentvolumen).
- **Kräfte im Wasser:** Auftrieb nach Archimedes (mit Teilvolumen),
  hydrodynamischer Widerstand proportional zu `½ · ρ_W · c_w · A_proj · v_rel²`,
  Zusatzdämpfung durch η (als vereinfachter Stokes-Term erlaubt, solange
  dokumentiert).

## 5. Physik-Kern

- **Fluid:** SPH (Smoothed Particle Hydrodynamics) für das Wasser in Echtzeit.
  - Partikelauflösung: `Δx ≈ 0,25 m` im Default-Becken → ca. 20.000 Partikel.
  - Zielgröße: ≥ 20.000 Partikel bei ≥ 30 FPS auf üblicher Desktop-Hardware
    (Ziel, nicht harte Grenze).
  - **Glättungslänge:** `h ≈ 1,3 · Δx` (Standardwahl in SPH); `h` ist als
    Simulationsparameter verfügbar.
- **Starrkörper-Solver:** Impulsbasiert, mit Kollisionsauflösung und Reibung.
- **Fluid↔Festkörper-Kopplung:**
  - Auftrieb + Widerstand auf die Körper (siehe Abschnitte 2–4).
  - Impulsübertrag: Körper drücken SPH-Partikel weg (einfache Penetrations-
    abstoßung reicht für v0.2; Zwei-Wege-Kraftkopplung dokumentieren).
- **Zeitschritt:** Fester Zeitschritt `Δt = 1/240 s`, 4–8 Substeps pro Renderframe;
  CFL-Begrenzung im SPH-Teil (Partikel dürfen pro Substep max. ~0,3·h wandern,
  d. h. bei `h ≈ 0,33 m` max. ~0,1 m pro Substep).
- **Determinismus:** Bei fixem Seed und fixen Substeps ist der Simulationsverlauf
  reproduzierbar.

## 6. Visualisierung & UI

- Transparente, beleuchtete Wasseroberfläche (Tiefenfarbe abhängig von Tiefe).
- Technisches Koordinatengitter mit Beschriftung, Maßstabsleiste.
- Kontrollpanel:
  - Gravitation g (m/s²)
  - Wind: Richtung + Geschwindigkeit
  - Zeitsteuerung: Pause / Schritt / Reset
  - Simulationsparameter: Partikelanzahl, Δt, Substeps
- **Einspawnen von Objekten per Klick** in die Szene (Kugel/Quader, wählbare
  Dichte, wählbare Reibung/Restitution).
- Anzeige von Statuswerten des zuletzt gewählten Körpers: Position,
  Geschwindigkeit, Eintauchtiefe, resultierende Kräfte.

## 7. Technische Rahmenbedingungen

- Python 3.11+; Rendering und Simulation laufen interaktiv in Echtzeit.
- Empfohlene Basis: **Taichi** (GPU-kompatibler SPH-Kern) oder **PyBullet/NumPy**
  für Starrkörper – Entscheidung beim Issue „Architektur" treffen und dort begründen.
- Saubere Trennung: Simulationskern ohne Rendering-Abhängigkeiten (testbar),
  Rendering/UI als separate Schicht.
- Tests: Mindestens Unit-Tests für Auftrieb (Teilvolumen), hydrostatischen Druck,
  Widerstandsgesetz und Kollisionsauflösung.

## 8. Akzeptanzkriterien (Definition of Done für v0.2)

1. **Schwimmen/Sinken:** Eine Kugel mit ρ = 500 kg/m³ schwimmt stabil an der
   Oberfläche (Restwelligkeit < 10 % des Radius nach 10 s); eine Kugel mit
   ρ = 2000 kg/m³ sinkt zum Boden und bleibt liegen.
2. **Auftrieb korrekt:** Ein Quader, zur Hälfte eingetaucht, erfährt statisch
   `F_A = ρ_W · (V/2) · g`; numerisches Gleichgewicht weicht um < 5 % ab.
3. **Hydrostatischer Druck:** Druck am Boden entspricht `ρ_W · g · (H/3)` ± 1 %.
4. **Luftwiderstand & Wind:** Ein Körper mit v₀ ≠ 0 in ruhender Luft erreicht
   asymptotisch v → 0; bei aktivem Wind stellt sich `v → v_Wind` ein (± 5 %).
5. **Wellenoberfläche:** Nach Einsprung eines Körpers entstehen sichtbare
   Oberflächenwellen (Amplitude ≥ 2 · Δx), die sich innerhalb des Beckens
   ausbreiten und abklingen.
6. **Kollisionen:** Zwei Körper kollidieren mit einer maximalen Restdurchdringung
   < 1 % des kleinsten Radius und übertragen Impuls plausibel; Wände/Boden
   halten dicht.
7. **Echtzeit:** ≥ 20.000 SPH-Partikel + ≥ 10 starre Körper bei ≥ 30 FPS
   (Referenz-Hardware: mittleres Desktop-Notebook).
8. **Interaktion:** Objekte lassen sich per Klick einspawnen; Gravitation und
   Wind sind zur Laufzeit änderbar und wirken sofort.
9. **Reproduzierbarkeit:** Zwei Läufe mit identischen Startwerten liefern nach
   1.000 Substeps identische Zustände (Bit-gleich oder < 1e-9 Abweichung).
10. **Tests:** Alle Unit-Tests aus Abschnitt 7 bestehen (`pytest` grün).

## 9. Ausbaustufen (nicht Teil von v0.2)

- **v0.3:** Ortsabhängiges Windfeld (Höhenprofil, Böen), Segelflächen als
  aerodynamische Körper.
- **v0.4:** Zwei-Wege-Fluid↔Körper-Kopplung verfeinern (Impuls auf Partikel,
  Spritzverhalten).
- **v0.5+:** Thermodynamik (Temperatur → Dichte/Viskosität), ggf. Mehrphasen-SPH.
