# SPEC – 3D-Physiksimulations-Umgebung (SegelPhysik)

**Status:** Verbindliche Spezifikation für den Neustart auf `main`
**Version:** 0.2.5 · **Datum:** 09.10.2026
**Zweck:** Eigenständige Echtzeit-3D-Umgebung mit Zwei-Phasen-Welt (Wasser/Luft),
Starrkörper-Dynamik und gekoppelter Fluid↔Festkörper-Interaktion als Fundament
für die spätere Segelboot-Simulation.

**Änderungen gegenüber v0.2.4:** Kriterium 2 an den vergrößerten
Testquader angepasst (2 × 2 × 2 m = 8 m³ statt 1 m³ – der alte Wert
verstieß gegen die eigene Auflösungsregel ≥ 8·Δx); Abschnitt 7 um
verbindliche Erweiterbarkeitsanforderungen ergänzt (Konfigurationsformat,
Kraftmodul-Schnittstelle, Body-/Shape-Interface, austauschbarer SPH-Kern,
Szenen-Serialisierung, SI-Einheiten) – die Spec ist ausdrücklich als
Basis für v0.3+ gedacht; veralteten Verweis `A_proj` korrigiert.

**Änderungen gegenüber v0.2.3:** Testkörper vergrößert (Kugel r = 1 m,
Quader 2 m Kante) – die bisherigen Körper waren mit nur 4·Δx Kantenlänge
bzw. 2·Δx Radius von der SPH-Auflösung her nicht aufgelöst (Kriterium 2
nicht erfüllbar); Regel „Körperabmessung ≥ 8·Δx" ergänzt; c_w-Defaults
definiert (Kugel 0,47, Quader 1,05) – ohne sie ist der Terminalgeschwindigkeits-
Test aus Kriterium 4 unbestimmt; Terminalgeschwindigkeits-Test auf
CFL-verträglichen Geschwindigkeitsbereich begrenzt; Irrelevanz des
Stokes-Terms bei diesen Skalen dokumentiert.

**Änderungen gegenüber v0.2.2:** Kriterium 4 physikalisch korrigiert (nur
horizontaler Geschwindigkeitsanteil bzw. Test mit g = 0 – ein freier Körper
erreicht unter Gravitation seine Fallterminalgeschwindigkeit, nicht v = 0);
Substep-Angabe präzisiert (4 Substeps bei 60 FPS = Realtime-Factor 1);
Raum-Oberseite als offen definiert; Referenzfläche einheitlich `A_ref`;
Beckenmaße ins UI-Panel aufgenommen.

---

## 1. Welt & Koordinatensystem

- Quaderförmiger Raum mit kartesischem Koordinatensystem.
- **Konvention:** Rechtshändiges System (x × y = z).
  - **z-Achse** zeigt nach oben; der Ursprung liegt auf der ungestörten
    Wasseroberfläche.
  - **x-Achse** zeigt in der Ebene der ungestörten Wasseroberfläche in Richtung
    Bug der späteren Yacht (Vorbereitung für v0.3; in v0.2 nur Namenskonvention).
  - **y-Achse** zeigt quer dazu in der Ebene der ungestörten Wasseroberfläche,
    **positiv nach Backbord** (folgt zwingend aus x = Bug, z = oben und dem
    Rechtssystem: y = z × x).
- Gesamthöhe `H` (konfigurierbar, Default: 9 m):
  - **Luft** (obere zwei Drittel): `z ∈ (0, 2H/3]` → Default: 6 m
  - **Wasser** (unteres Drittel): `z ∈ [−H/3, 0]` → Default: 3 m Wassertiefe
- Grundfläche des Raums konfigurierbar (Default: 10 m × 10 m); Wände und Boden
  sind feste Kollisionsgrenzen. **Die Oberseite des Raums ist offen** – Objekte
  können von oberhalb der Wasserlinie eingesponnen werden und fallen frei ein.
- Gravitation: `g = 9,81 m/s²` in negativer z-Richtung (im UI konfigurierbar).

> **Begründung der Defaults:** Wasser-Volumen = 10 · 10 · 3 = 300 m³. Bei der in
> Abschnitt 5 geforderten Partikelauflösung `Δx ≈ 0,25 m` ergibt sich
> N ≈ 300 / 0,25³ ≈ 19.200 ≈ 20.000 Partikel – eine Auflösung, bei der
> Oberflächenwellen sichtbar darstellbar sind (vgl. Kriterium 5).

## 2. Phase Wasser

| Größe | Wert |
|---|---|
| Dichte ρ_W | 1000 kg/m³ |
| Dynamische Viskosität η | ≈ 1 mPa·s (nur informativ; wirksam ausschließlich über den dokumentierten Stokes-Dämpfungsterm aus Abschnitt 4) |
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
| Quadratischer Widerstand | `F_D = ½ · ρ_L · c_w · A_ref · v_rel²` |

**c_w-Defaults (pro Objekt im UI änderbar):** Kugel `c_w = 0,47`;
Quader (Anströmung senkrecht zur Fläche) `c_w = 1,05`. Ohne feste
Defaults wäre der Terminalgeschwindigkeits-Test aus Kriterium 4
nicht bestimmt.

- `A_ref`: Referenzfläche des Körpers (projizierte Fläche senkrecht zur
  Relativbewegung); gleiche Definition wie in Abschnitt 4.
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
  - **Default-Testkörper (für die Akzeptanzkriterien):**
    - Testkugel: Radius r = 1,0 m
    - Testquader: 2 m × 2 m × 2 m (Kantenlänge 2 m)
  - **Auflösungsregel:** Jede simulierbare Körperabmessung muss
    `≥ 8 · Δx` betragen (bei Default-Δx = 0,25 m also ≥ 2 m), damit die
    SPH-Umströmung – und damit Auftrieb und Widerstand – überhaupt
    aufgelöst wird. Das Einspawner-UI begrenzt die minimale Körpergröße
    entsprechend.
- **Verhalten:** Dichte < 1000 kg/m³ → schwimmt; > 1000 kg/m³ → sinkt.
- **Kollisionen:** Körper↔Körper sowie Körper↔Wände/Boden.
- **Teil-Eintauchen:** Der verdrängte Teilvolumenanteil wird explizit berechnet:
  - Quader: analytisch über den eingetauchten Anteil der Höhe.
  - Kugel: analytisch über die Kappenhöhe (Segmentvolumen).
- **Kräfte im Wasser:** Auftrieb nach Archimedes (mit Teilvolumen),
  hydrodynamischer Widerstand proportional zu
  `½ · ρ_W · c_w · A_ref · v_rel²` mit
  `v_rel = v_Körper − v_Fluid(lokal)` – bezogen auf die lokale SPH-Fluid-
  geschwindigkeit am Körperort (nicht auf Wind),
  Zusatzdämpfung durch η (als vereinfachter Stokes-Term erlaubt, solange
  dokumentiert). **Hinweis:** Bei den hier simulierten Skalen (Objekte ≥ 2 m,
  Wasser) ist der Stokes-Term (`6π·η·r` für Kugeln ≈ 0,02 N·s/m) rund vier
  Größenordnungen schwächer als der quadratische Widerstandsterm und damit
  numerisch vernachlässigbar; er dient nur der Stabilität bei sehr kleinen
  Relativgeschwindigkeiten und muss nicht kalibriert werden.

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
- **Zeitschritt & Echtzeit:**
  - Fester Zeitschritt `Δt = 1/240 s`.
  - **Akkumulator-Muster:** Pro Renderframe rückt die Simulationszeit um die
    real verstrichene Zeit nach; die Substep-Anzahl ergibt sich daraus.
    Bei 60 FPS und Realtime-Factor 1 sind das genau **4 Substeps pro Frame**
    (60 · 4 · 1/240 s = 1 s); die im UI einstellbare Substeps-Obergrenze
    (Default: 8) begrenzt den Rückstand nur bei Frame-Jitter und verhindert
    einen „Spiral of Death". Ziel: Realtime-Factor ≈ 1.
    Läuft die Darstellung langsamer (z. B. 30 FPS), darf der Realtime-Factor
    unter 1 fallen – die Physik bleibt davon unberührt (feste Δt, fester Seed).
  - CFL-Begrenzung im SPH-Teil (Partikel dürfen pro Substep max. ~0,3·h wandern,
    d. h. bei `h ≈ 0,33 m` max. ~0,1 m pro Substep).
- **Determinismus:** Bei fixem Seed und fixen Substeps ist der Simulationsverlauf
  reproduzierbar.
- **Partikelanzahl als Restart-Parameter:** Eine Änderung der Partikelanzahl
  (und damit von `Δx`/`h`) erfordert einen Simulations-Reset; sie ist nicht
  zur Laufzeit mitten in einer Szene änderbar.

## 6. Visualisierung & UI

- Transparente, beleuchtete Wasseroberfläche (Tiefenfarbe abhängig von Tiefe).
- Technisches Koordinatengitter mit Beschriftung, Maßstabsleiste.
- Kontrollpanel:
  - Gravitation g (m/s²)
  - Wind: Richtung + Geschwindigkeit
  - Zeitsteuerung: Pause / Schritt / Reset
  - Simulationsparameter: Partikelanzahl (wirkt nach Reset), Δt,
    Substeps-Obergrenze
  - Beckenmaße: Grundfläche (L × B) und Höhe H (wirken nach Reset)
- **Einspawnen von Objekten per Klick** in die Szene (Kugel/Quader, wählbare
  Dichte, wählbare Reibung/Restitution).
- Anzeige von Statuswerten des zuletzt gewählten Körpers: Position,
  Geschwindigkeit, Eintauchtiefe, resultierende Kräfte.

## 7. Technische Rahmenbedingungen

- Python 3.11+; Rendering und Simulation laufen interaktiv in Echtzeit
  (Realtime-Factor ≈ 1, siehe Abschnitt 5).
- Empfohlene Basis: **Taichi** (GPU-kompatibler SPH-Kern) oder **PyBullet/NumPy**
  für Starrkörper – Entscheidung beim Issue „Architektur" treffen und dort begründen.
  Dort auch adressieren: Kriterium 7 (20.000 Partikel @ 30 FPS) auf reiner CPU
  ist ambitioniert; GPU-Pfad bevorzugen oder CPU-Fallback mit reduzierter
  Partikelzahl definieren.
- Saubere Trennung: Simulationskern ohne Rendering-Abhängigkeiten (testbar),
  Rendering/UI als separate Schicht.
- Tests: Mindestens Unit-Tests für Auftrieb (Teilvolumen), hydrostatischen Druck,
  Widerstandsgesetz und Kollisionsauflösung.

### 7.1 Erweiterbarkeit (verbindlich – diese Spec ist Basis für v0.3+)

- **Einheiten:** Durchgängig SI-Einheiten; das ist verbindlich und wird
  nirgends verlassen (auch nicht in Konfigurationsdateien).
- **Konfiguration:** Alle physikalischen Parameter und Defaults
  (ρ_W, ρ_L, g, c_w, μ, e, Beckenmaße, Δt, Δx/h, Wind) werden über ein
  zentrales Parameterobjekt verwaltet, das aus einer Konfigurationsdatei
  (JSON oder YAML) geladen werden kann. Keine physikalischen Konstanten
  hart im Solver-Code.
- **Kraftmodule:** Jedes Kraftmodell (Auftrieb, Widerstand, Stokes-Dämpfung,
  später Wind-/Segelkräfte) ist ein austauschbares Modul hinter einer
  gemeinsamen Schnittstelle (`apply(body, environment, dt) -> Kraft/Moment`);
  der Solver kennt nur die Schnittstelle, nicht die konkreten Modelle.
- **Körper als Interface:** `Body`-Basisklasse mit Shape-Abstraktion;
  Kugel und Quader sind die ersten Implementierungen. Neue Formen
  (Segelflächen, Rumpfgeometrien in v0.3+) erweitern das System, ohne den
  Solver zu ändern. Mindestanforderung je Form: Teilvolumen unter Wasser-
  linie, `A_ref`, Trägheitstensor.
- **SPH-Kern austauschbar:** Der Fluidsolver liegt hinter einem Interface
  (Partikelzustand lesen/schreiben, Dichte/Feldabfragen am Körperort), damit
  in v0.5 Thermodynamik/Mehrphasen andockbar sind, ohne die Kopplung neu
  zu schreiben. Das Windfeld-Interface aus Abschnitt 3 ist das Muster dafür.
- **Szenen-Serialisierung:** Der komplette Szenenzustand (Parameter,
  Körper, Partikel-Seed) lässt sich speichern und laden – Voraussetzung
  für die reproduzierbaren Läufe aus Kriterium 9 und für Regressionstests
  in allen folgenden Versionen.

## 8. Akzeptanzkriterien (Definition of Done für v0.2)

1. **Schwimmen/Sinken:** Eine Testkugel (r = 1,0 m) mit ρ = 500 kg/m³ schwimmt
   stabil an der Oberfläche (Restwelligkeit < 10 % des Radius nach 10 s); eine
   Testkugel mit ρ = 2000 kg/m³ sinkt zum Boden und bleibt liegen.
2. **Auftrieb korrekt:** Ein Testquader (2 × 2 × 2 m, V = 8 m³), zur Hälfte
   eingetaucht, erfährt statisch `F_A = ρ_W · (V/2) · g = 39.240 N`;
   numerisches Gleichgewicht weicht um < 5 % ab.
3. **Hydrostatischer Druck:** Druck am Boden entspricht `ρ_W · g · (H/3)` ± 1 %.
4. **Luftwiderstand & Wind:** Der **horizontale** Geschwindigkeitsanteil eines
   Körpers in ruhender Luft (Test entweder mit g = 0 oder Auswertung nur der
   x/y-Komponente) klingt asymptotisch gegen 0 ab; bei aktivem Wind stellt sich
   `v_horizontal → v_Wind` ein (± 5 %). Vertikal gilt stattdessen die
   Fallterminalgeschwindigkeit aus dem Kräftegleichgewicht – diese wird separat
   als Unit-Test gegen den analytischen Wert
   `v_term = sqrt(2·m·g / (ρ_L · c_w · A_ref))` geprüft (Testkonfiguration so
   wählen, dass v_term unterhalb der CFL-Grenze von ~23 m/s bleibt, z. B.
   leichte Kugel oder reduziertes g).
5. **Wellenoberfläche:** Nach Einsprung eines Körpers entstehen sichtbare
   Oberflächenwellen (Amplitude ≥ 2 · Δx, bezogen auf den jeweils aktiven
   `Δx` der Simulation), die sich innerhalb des Beckens ausbreiten und abklingen.
6. **Kollisionen:** Zwei Körper kollidieren mit einer maximalen Restdurchdringung
   < 1 % der kleinsten charakteristischen Abmessung des kleineren Körpers und
   übertragen Impuls plausibel; Wände/Boden halten dicht.
7. **Echtzeit:** ≥ 20.000 SPH-Partikel + ≥ 10 starre Körper bei ≥ 30 FPS
   (Referenz-Hardware: mittleres Desktop-Notebook; siehe Risiko-Hinweis in
   Abschnitt 7).
8. **Interaktion:** Objekte lassen sich per Klick einspawnen; Gravitation und
   Wind sind zur Laufzeit änderbar und wirken sofort.
9. **Reproduzierbarkeit:** Zwei Läufe mit identischen Startwerten liefern nach
   1.000 Substeps Zustände mit Abweichung < 1e-9 (Position und Geschwindigkeit).
10. **Tests:** Alle Unit-Tests aus Abschnitt 7 bestehen (`pytest` grün).

## 9. Ausbaustufen (nicht Teil von v0.2)

- **v0.3:** Ortsabhängiges Windfeld (Höhenprofil, Böen), Segelflächen als
  aerodynamische Körper.
- **v0.4:** Zwei-Wege-Fluid↔Körper-Kopplung verfeinern (Impuls auf Partikel,
  Spritzverhalten).
- **v0.5+:** Thermodynamik (Temperatur → Dichte/Viskosität), ggf. Mehrphasen-SPH.
