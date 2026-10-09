# SPEC – 3D-Physiksimulations-Umgebung (SegelPhysik, v0.2)

**Status:** Verbindliche Spezifikation für den Neustart auf `main`
**Version:** 0.2 · **Datum:** 09.10.2026
**Zweck:** Eigenständige Echtzeit-3D-Umgebung mit Zwei-Phasen-Welt (Wasser/Luft),
Starrkörper-Dynamik und gekoppelter Fluid↔Festkörper-Interaktion als Fundament
für die spätere Segelboot-Simulation.

---

## 1. Welt & Koordinatensystem

- Quaderförmiger Raum mit kartesischem Koordinatensystem.
- **Konvention:** z-Achse zeigt nach oben, Ursprung liegt auf der ungestörten
  Wasseroberfläche.
  x-Achse zeigt in Richtung Yacht (Bug) in der Ebene der  ungestörten
  Wasseroberfläche.
  y-Achse zeigt quer dazu in der Ebene der  ungestörten
  Wasseroberfläche.
- Gesamthöhe `H` (konfigurierbar, Default: 30 m).
  - **Luft** (obere zwei Drittel): `y ∈ (0, 2H/3]`
  - **Wasser** (unteres Drittel): `y ∈ [−H/3, 0]`
- Grundfläche des Raums konfigurierbar (Default: 20 m × 20 m), Wände und Boden
  sind feste Kollisionsgrenzen.
- Gravitation: `g = 9,81 m/s²` in negativer Z-Richtung (im UI konfigurierbar).

## 2. Phase Wasser

| Größe | Wert |
|---|---|
| Dichte ρ_W | 1000 kg/m³ |
| Dynamische Viskosität η | ≈ 1 mPa·s |
| Hydrostatischer Druck | `p = ρ_W · g · h` (linear mit Tiefe h) |
| Auftrieb (Archimedes) | `F_A = ρ_W · V_verdrängt · g` |

- **Freie Oberfläche** bei z = 0 als Grenzschicht zur Luft; leicht wellend.
  Die Oberfläche ergibt sich implizit aus der SPH-Partikelverteilung
  (Partikeldichte-Schwellwert oder Marching Squares/Cubes über Partikelnichtdistanz).

## 3. Phase Luft (Zunächst nur MockUp, erste Später implementieren)

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
- **Verhalten:** Dichte < 1000 kg/m³ → schwimmt; > 1000 kg/m³ → sinkt.
- **Kollisionen:** Körper↔Körper sowie Körper↔Wände/Boden.
- **Teil-Eintauchen:** Der verdrängte Teilvolumenanteil wird explizit berechnet:
  - Quader: analytisch über den eingetauchten Anteil der Höhe.
  - Kugel: analytisch über die Kappenhöhe (Segmentvolumen).
- **Kräfte im Wasser:** Auftrieb nach Archimedes (mit Teilvolumen), hydrodynamischer
  Widerstand proportional zu `½ · ρ_W · c_w · A_proj · v_rel²`, Zusatzdämpfung
  durch η (als vereinfachte Stokes-Terms erlaubt, solange dokumentiert).

## 5. Physik-Kern

- **Fluid:** SPH (Smoothed Particle Hydrodynamics) für das Wasser in Echtzeit.
  - Zielgröße: ≥ 5.000 Partikel bei ≥ 30 FPS auf üblicher Desktop-Hardware
    (Ziel, nicht harte Grenze).
- **Starrkörper-Solver:** Impulsbasiert, mit Kollisionsauflösung und Reibung.
- **Fluid↔Festkörper-Kopplung:**
  - Auftrieb + Widerstand auf die Körper (siehe Abschnitte 2–4).
  - Impulsübertrag: Körper drücken SPH-Partikel weg (einfache Penetrations-
    abstoßung reicht für v0.2; Zwei-Wege-Kraftkopplung dokumentieren).
- **Zeitschritt:** Fester Zeitschritt `Δt = 1/240 s`, 4–8 Substeps pro Renderframe;
  CFL-Begrenzung im SPH-Teil (Partikel dürfen pro Substep max. ~0,3·h wandern).
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
- **Einspawnen von Objekten per Klick** in die Szene (Kugel/Quader, wählbare Dichte).
- Anzeige von Statuswerten des zuletzt gewählten Körpers: Position, Geschwindigkeit,
  Eintauchtiefe, resultierende Kräfte.

## 7. Technische Rahmenbedingungen

- Python 3.11+; Rendering und Simulation laufen interaktiv in Echtzeit.
- Empfohlene Basis: **Taichi** (GPU-kompatibler SPH-Kern) oder **PyBullet/NumPy**
  für Starrkörper – Entscheidung beim Issue „Architektur" treffen und dort begründen.
- Saubere Trennung: Simulationskern ohne Rendering-Abhängigkeiten (testbar),
  Rendering/UI als separate Schicht.
- Tests: Mindestens Unit-Tests für Auftrieb (Teilvolumen), hydrostatischen Druck,
  Widerstandsgesetz und Kollisionsauflösung.

---

## 8. Akzeptanzkriterien (Definition of Done für v0.2)

1. **Schwimmen/Sinken:** Eine Kugel mit ρ = 500 kg/m³ schwimmt stabil an der
   Oberfläche (Restwelligkeit < 10 % des Radius nach 10 s); eine Kugel mit
   ρ = 2000 kg/m³ sinkt zum Boden und bleibt liegen.
2. **Auftrieb korrekt:** Ein Quader, zur Hälfte eingetaucht, erfährt statisch
   `F_A = ρ_W · (V/2) · g`; numerisches Gleichgewicht weicht um < 5 % ab.
3. **Hydrostatischer Druck:** Druck am Boden entspricht `ρ_W · g · (H/3)` ± 1 %.
4. **Luftwiderstand:** Ein Körper mit v₀ ≠ 0 in ruhender Luft erreicht asymptotisch
   v → 0; bei aktivem Wind stellt sich `v → v_Wind` ein (± 5 %).
5. **Wellenoberfläche:** Nach Einsprung eines Körpers entstehen sichtbare
   Oberflächenwellen, die sich innerhalb des Beckens ausbreiten und abklingen.
6. **Kollisionen:** Zwei Körper kollidieren ohne Durchdringung (> 1 % des
   kleinsten Radius) und übertragen Impuls plausibel; Wände/Boden halten dicht.
7. **Echtzeit:** ≥ 5.000 SPH-Partikel + ≥ 10 starre Körper bei ≥ 30 FPS
   (Referenz-Hardware: mittleres Desktop-Notebook).
8. **Interaktion:** Objekte lassen sich per Klick einspawnen; Gravitation und Wind
   sind zur Laufzeit änderbar und wirken sofort.
9. **Reproduzierbarkeit:** Zwei Läufe mit identischen Startwerten liefern nach
   1.000 Substeps identische Zustände (Bit-gleich oder < 1e-9 Abweichung).
10. **Tests:** Alle Unit-Tests aus Abschnitt 7 bestehen (`pytest` grün).

---

## 9. Ausbaustufen (nicht Teil von v0.2)

- **v0.3:** Ortsabhängiges Windfeld (Höhenprofil, Böen), Segelflächen als
  aerodynamische Körper.
- **v0.4:** Zwei-Wege-Fluid↔Körper-Kopplung verfeinern (Impuls auf Partikel,
  Spritzverhalten).
- **v0.5+:** Thermodynamik (Temperatur → Dichte/Viskosität), ggf. Mehrphasen-SPH.
