# SPEC V3 – SegelPhysik: Kinematische Körperdemo an der Wasseroberfläche

**Status:** Verbindliche Spezifikation Version 3 – ersetzt vollständig SPEC_v2.md (v2.3a).
**Version:** 3.0 · **Datum:** 10.10.2026
**Zweck:** Vollständiger Physik-Entzug. Es gibt keine Kräfte, keinen Solver, keine
Massenberechnung und keine Kollisionen mehr. Übrig bleibt eine rein kinematische,
grafische Demo: drei starre Körper rotieren gleichförmig durch die statische
Wasseroberfläche. Die gesamte grafische Spezifikation aus v2.3 bleibt erhalten.

---

## 0. Änderungslog gegenüber SPEC_v2.md (v2.3a)

### Entfernt (vollständig verworfen)
| Alt | Inhalt |
|---|---|
| §4/§5 | Gesamte Körperphysik: Dichteverteilungen, Massen-/Schwerpunkt-/Tensorintegration, Auftrieb, Auftriebsmoment, Metazentrum-Stabilität |
| §5.2 | Exakte Eintauchgeometrie (Polyeder-Ebenen-Clip), V_sub/r_B-Berechnung, K13′-Winkel-Sweep |
| §5.4/§5.5 | LinearDamping, c_rot-Frage, Starrkörper-Dynamik (Translation, Quaternionen-Integration, Kreiselterm) |
| §5.6 | Alle Kollisionen (Körper↔Körper, Wände, Boden) |
| §2/§3 | Hydrostatisches Druckfeld p(z), Phasenmodell als Physik |
| §8 | Alle Referenzwerte und Referenzmomente (Bojenkegel-Sollwerte, §8.1/§8.2) – entfallen ersatzlos |
| §9 | Akzeptanzkriterien K1′–K13′ – ersetzt durch K1″–K8″ (Abschnitt 8) |
| §10 | Unit-Tests zu Physik – entfallen; neue, schlanke Testliste in Abschnitt 9 |

### Geändert
| Alt → Neu | Inhalt |
|---|---|
| §4 | Körper sind rein kinematische Objekte: Masse wird nicht berechnet und ist ohne Wirkung („homogen, irrelevant") |
| §5 | Dynamics-Solver entfällt; ersetzt durch kinematische Animation (Abschnitt 4): feste Rotation 360°/15 s, Schwerpunkt fixiert auf der Wasseroberfläche |
| §6 | Kraft- und Geschwindigkeitspfeile entfallen (es gibt keine Kräfte/Geschwindigkeiten mehr); Status-Panel auf Animationsgrößen reduziert |

### Übernommen (unverändert aus v2.3)
§1 Welt & Koordinatensystem · statisches Wasser mit ebener Oberfläche bei z = 0 ·
gesamte grafische Spezifikation: Zweiton-Körper unter/über Wasserlinie,
Wasserlinien-Kontur, Tiefenfärbung, technische Gitter, Maßstabsleiste, HUD
(RTF/FPS/Simulationszeit), Beckengeometrie (10×10×9 m, offene Oberseite),
SI-Einheiten, Δt = 1/240 s Akkumulator-Muster für die Animationsuhr,
Determinismus der Animation, Szenen-Serialisierung.

---

## 1. Welt & Koordinatensystem
Unverändert: rechtshändiges System, z nach oben, Ursprung auf der Wasseroberfläche,
Becken 10 m × 10 m Grundfläche, H = 9 m, offene Oberseite. g wird nicht mehr
gebraucht und entfällt aus dem Parameterobjekt.

## 2. Wasser (rein grafisch)
Statische, transparente, beleuchtete Ebene bei z = 0 mit Tiefenfärbung unterhalb.
Keine Wellen, keine Verformung, kein Druckfeld, keine Fluidsimulation. Das Wasser
ist ausschließlich Referenzebene für die Zweiton-Färbung und Wasserlinien-Kontur.

## 3. Körper

Drei Primitive, alle **homogen** (Dichte wird nicht verwendet – keine Physik):

| Körper | Default-Abmessungen |
|---|---|
| Kegel | H = 2 m, R = 1 m (Achse = Körper-z) |
| Quader | 2 m × 2 m × 2 m |
| Pyramide | quadratische Basis a = 2 m, H = 2 m (Achse = Körper-z) |

- Der „Bojenkegel" mit Dichteprofil entfällt; der Kegel ist jetzt homogen.
- Abmessungen sind im Szenen-JSON konfigurierbar (keine UI-Pflicht).
- Der Körperursprung liegt im **Schwerpunkt** des Körpers (geometrischer
  Mittelpunkt; für Kegel/Pyramide bei H/4 bzw. H/4 über der Basis – rein
  definitorisch, da ohne physikalische Wirkung).

## 4. Kinematik (Kern von V3)

Jeder Körper bewegt sich rein vorgeschrieben (kein Integrator, keine Zustandsgleichungen):

$$\varphi(t) = \omega \cdot t, \qquad \omega = \frac{360^\circ}{15\,\mathrm{s}} = 24^\circ/\mathrm{s} = \frac{2\pi}{15}\,\mathrm{rad/s}$$

- **D1 – Rotationsachse (Festlegung):** horizontal liegende Achse durch den
  Schwerpunkt, im Weltframe Richtung y. Der Körper kippt dadurch kontinuierlich
  durch die Wasseroberfläche (Eintauchen/Auftauchen sichtbar). Die Achse ist im
  Szenen-JSON konfigurierbar (Alternative: vertikale Drehachse = reines
  Wasserspinnt).
- **D2 – Position (Festlegung):** Der Schwerpunkt bleibt fixiert auf der
  Wasseroberfläche: r_S(t) = (0, 0, 0). Keine Translation, kein Absinken.
- **D3 – Phasenbezug (Festlegung):** φ(0) = 0 entspricht Körper-z-Achse
  parallel zur Welt-z-Achse (Ausgangslage aufrecht). Reset setzt t = 0.
- Die Rotation ist exakt periodisch: nach 15 s ist die Ausgangslage wieder
  erreicht (bei symmetrischen Körpern visuell früher – irrelevant).
- Pause/Single-Step frieren die Animationsuhr ein; Zeitlupe/Wiedergabefaktor
  skaliert ω (Default 1× = Echtzeit).

## 5. Visualisierung

Unverändert aus v2.3 §6, mit zwei Festlegungen:
- **Zweiton-Körper:** Bewertung der Färbung gegen die Ebene z = 0 (Teile mit
  Schwerpunktz < 0 = „unter Wasser", Rest = „über Wasser"). Da keine Physik
  existiert, ist die Färbung rein geometrisch definiert.
- **Wasserlinien-Kontur:** Schnittkurve Körper ∩ Ebene z = 0, wie bisher gerendert.
- **Entfallen:** Kraftpfeile, Geschwindigkeitspfeile, Momentenarm (keine Kräfte).
- **Status-Panel (reduziert):** Körpertyp, φ(t) in Grad, Umdrehungsnummer,
  Animationszeit, RTF, FPS. Keine Massen-, Kraft-, GM- oder Tiefgangsanzeigen.
- Technisches Gitter, Maßstabsleiste, HUD, Becken: unverändert.

## 6. UI & Steuerung

- Spawn-Auswahl der drei Körper (Kegel / Quader / Pyramide), jeweils einer
  gleichzeitig oder mehrere nebeneinander (Default: genau einer).
- Start/Pause/Reset, Wiedergabefaktor (0,25×–4×), Kamera-Steuerung wie v0.4.
- Entfallen: g-Regler, Dämpfung c, μ/e, Dichteprofil-Parameter, Wind-Regler.

## 7. Technische Rahmenbedingungen

- Python 3.11+, PyVista-Rendering; NumPy genügt vollständig – **Taichi und der
  gesamte SPH-Code sind für V3 ohne Funktion** (im Repo belassen, nicht Teil
  der Abnahme).
- Kein Solver-Modul im Ablauf; die Animation ist eine geschlossene Funktion
  der Animationsuhr (deterministisch, reproduzierbar, K9-Geist lebt weiter).
- Szenen-JSON: Körpertyp, Abmessungen, Rotationsachse, ω, Startphase.
- Kraftmodul-Schnittstelle (§7.1 alt) entfällt; falls später Physik zurückkommt,
  wird sie neu spezifiziert (v4-Vorbehalt).

## 8. Akzeptanzkriterien

| K | Kriterium | Prüfung / Toleranz |
|---|---|---|
| K1″ | Rotation exakt: nach 15,000 s Simulationszeit ist φ = 360° (± 0,01°) | QUICK |
| K2″ | Schwerpunkt fix: r_S = (0,0,0) für alle t (± 1 mm) | QUICK |
| K3″ | Zweiton-Färbung korrekt: Flächenanteile unter/über z = 0 stimmen mit der Schnittebene überein (visuelle Prüfung + Stichproben-Vertex-Test) | QUICK |
| K4″ | Wasserlinien-Kontur sichtbar und korrekt für alle drei Körper bei mindestens 5 Prüfphasen | QUICK |
| K5″ | Alle drei Körper laden, rotieren und werden sauber gerendert (keine Z-Fighting an der Ebene, keine clipping-artefakte) | manuell |
| K6″ | ≥ 60 FPS bei 3 gleichzeitig rotierenden Körpern auf mittlerer Desktop-Hardware | manuell/Hardware |
| K7″ | Determinismus: zwei Läufe mit identischer Szenen-JSON liefern bitidentische φ(t)-Folgen über 1.000 Substeps | QUICK |
| K8″ | Test-Suite grün (neue Suite, Abschnitt 9) | QUICK |

## 9. Unit-Tests (neu, schlank)

**Neu:** Kinematik (φ(t)-Formel, Periodizität, Pause/Step-Verhalten),
Szenen-Serialisierung (Rundtrip JSON ↔ Szene), Schwerpunkt-Fixierung,
Zweiton-Klassifikation gegen Stichprobenvertices, Kontur-Existenz je Phase.
**Entfallen:** sämtliche Physik-, Geometrie-, Kollisions- und SPH-Tests der
v0.4/v2-Suiten (inkl. K13′-Sweep-Infrastruktur).

## 10. Ausbaustufen (nicht Teil von V3)
- V4-Vorbehalt: Wiedereinführung von Physik (Auftrieb o. Wind) erfordert neue
  Spec; die kinematische Animation bleibt dann als Referenz-Darstellung erhalten.

---

## Anhang A – Entscheidungen D1–D3 (in V3.0 vorläufig festgelegt)
- **D1** Rotationsachse horizontal (y-Richtung) durch den Schwerpunkt → Körper
  taucht durch die Oberfläche. Alternativ wäre vertikale Achse (Spinnt an der
  Oberfläche). Bitte bestätigen oder ändern.
- **D2** Schwerpunkt fixiert auf z = 0, keine Translation. Bitte bestätigen
  (alternativ: vertikale Oszillation o. ä. – wäre neue Kinematik).
- **D3** φ(0) = 0 ⇒ aufrecht; Reset setzt die Uhr auf null.
