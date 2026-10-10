# SPEC v2 – SegelPhysik: Hydrostatik inhomogener Körper

**Status:** Verbindliche Spezifikation Version 2 – ersetzt doc/SPEC.md (v0.2.5)
und die unter „Spec v1.1" geplante Anpassung. Basis: Release v0.4 (10.10.2026).
**Version:** 2.1 · **Datum:** 10.10.2026
**Zweck:** Bewusster Scope-Rücksetzer. Die Simulation reduziert sich auf
hydrostatischen Auftrieb an statischem Wasser – jetzt für nichthomogene Körper
mit nichthomogener Massenverteilung inkl. Aufrichtmoment. Wind-, Wellen- und
Widerstandsphysik entfallen. Die grafische Darstellung bleibt unverändert.

**Leitprinzip (v2.1):** Massenschwerpunkt S und Auftriebsanschwerpunkt B
(Formschwerpunkt des verdrängten Volumens) werden für inhomogene Körper mit
komplexer Geometrie **exakt** ermittelt – bei **jedem** Krängungs- oder
Eintauchwinkel, nicht nur in der Ruhelage.

---

## 0. Änderungslog gegenüber SPEC v0.2.5

### Entfernt
| Alt | Inhalt |
|---|---|
| §3 | Luftphase komplett: Dichte ρ_L, quadratischer Luftwiderstand, c_w-Defaults, Windfeld (Pflichtfeature) |
| §4 | Hydrodynamischer Widerstand ½·ρ_W·c_w·A_ref·v_rel², Stokes-Dämpfungsterm, A_ref-Anforderung |
| §2 | Viskosität η / Stokes-Verweis in der Phasentabelle |
| §5 | SPH als Physikquelle: Partikelauflösung, Glättungslänge h, CFL-Begrenzung, Fluid↔Körper-Kopplung, einseitige Partikel↔Körper-Kollision |
| §6 | Wellende freie Oberfläche; UI-Regler „Wind Richtung/Geschwindigkeit"; Kontrollfelder Δx/h/Partikelanzahl |
| §8 | K4 (Luftwiderstand & Wind), K5 (Wellenoberfläche), K7 (20k Partikel @ 30 FPS) |

### Geändert
| Alt → Neu | Inhalt |
|---|---|
| §2 | Wasser ist statisch: ebene Oberfläche bei z = 0, hydrostatisches Druckfeld p(z) = ρ_W·g·h analytisch (keine Diskretisierung mehr) |
| §4 | Körper sind nicht mehr homogen: Masse/Schwerpunkt/Trägheitstensor aus Dichteverteilung ρ(x) (Abschnitt 4/5) |
| §5 | Starrkörper-Solver mit vollständiger Rotation: Quaternion-Orientierung, voller Trägheitstensor im Körperframe, Kreiselterm ω×(Iω) |
| §5 | Auftrieb analytisch aus Eintauchgeometrie (exakter Ebenen-Clip), nicht aus Partikelfeld |
| §6 | Wasseroberfläche = statische, transparente Ebene bei z = 0 (Tiefenfärbung, Zweiton-Körper, Wasserlinien-Kontur bleiben); Kraftpfeile erweitert um Auftriebsvektor in B und Gewichtspfeil in S |
| §8 | Neue Kriterien K1′–K13′ (Abschnitt 9) |

### Neu
- Dichteverteilungen: zusammengesetzte Primitive mit je konstanter Dichte;
  Kegel zusätzlich mit linearem Dichteprofil entlang der Achse (Abschnitt 4).
- Auftriebsmoment M_A = (r_B − r_S) × F_A → Metazentrum-Stabilität,
  passives Aufrichten/Kippen (Abschnitt 5).
- Exakte Eintauchgeometrie für beliebige Orientierung (Abschnitt 5.2, v2.1).
- Referenzkörper „Bojenkegel" mit geschlossenen Sollwerten und exakten
  Referenzmomenten (Abschnitt 8).
- Spawn-Presets im UI (Abschnitt 7).

### Übernommen (unverändert)
§1 Welt & Koordinatensystem (rechtshändig, z nach oben, Becken 10×10×9 m,
offene Oberseite, g = 9,81 m/s²) · SI-Einheiten durchgängig · Δt = 1/240 s mit
Akkumulator-Muster · Determinismus bei fixem Seed/Substeps · Szenen-
Serialisierung · Körper↔Körper- sowie Körper↔Wand/Boden-Kollision ·
gesamte grafische Spezifikation mit Ausnahme der wellenden Oberfläche.

---

## 1. Welt & Koordinatensystem
Unverändert gegenüber v0.2.5 §1: rechtshändiges System, z nach oben, Ursprung
auf der Wasseroberfläche, x Richtung Bug, y nach Backbord. Becken-Defaults
10 m × 10 m Grundfläche, H = 9 m, offene Oberseite. g = 9,81 m/s²
(UI-konfigurierbar).

## 2. Phase Wasser (statisch)

| Größe | Wert |
|---|---|
| Dichte ρ_W | 1000 kg/m³ |
| Oberfläche | statisch, eben bei z = 0 |
| Druck | p(z) = ρ_W · g · h, h = −z (analytisch, exakt) |
| Auftrieb | F_A = ρ_W · V_sub · g, angreifend im Formschwerpunkt B des verdrängten Volumens |

Das Wasser ist kein simuliertes Fluid mehr. Es liefert ausschließlich das
hydrostatische Feld und die Verdrängung. Der SPH-Code (segelphysik/fluid,
core/sph.py) bleibt im Repo erhalten, liegt hinter dem Fluid-Interface (§7.1)
und ist nicht Teil der v2-Abnahme. Das Marching-Cubes-Rendering ruht;
gerendert wird die ebene Oberfläche (Abschnitt 6).

## 3. Phase Luft
Entfällt. Keine Kräfte, kein Windfeld, keine Parameter. (Abschnittsnummer
reserviert; Luft wird später für die Segelphysik wieder eingeführt.)

## 4. Simulierbare Objekte – Dichteverteilungen

### 4.1 Körpermodell
Starre Körper Kugel, Quader und Kegel. Jeder Körper trägt eine
Dichteverteilung ρ(x,y,z) im Körperframe. Masse, Schwerpunkt und Trägheitstensor
werden daraus integriert (Abschnitt 5.1) – niemals als Dichte × Volumen mit
Mittelpunktsannahme.


### 4.3 Konfiguration
Dichteverteilungen werden deklarativ in der Szenen-JSON definiert
(Primitive-Liste mit Typ, Pose relativ zum Körperursprung, Abmessungen,
ρ bzw. Profil-Parameter). Das Spawn-UI bietet mindestens drei Presets:
- „Homogene Kugel" (Regression gegen v0.4),
- „Bojenkegel" (Abschnitt 8),
- „Ballast-Kiel-Quader" (zwei Primitive: leichter Rumpf + dichter Kiel,
  demonstratives Aufrichtverhalten).

### 4.4 Verhalten
ρ̄ = m/V < ρ_W → schwimmt; > ρ_W → sinkt (bewertet über die integrierte
mittlere Dichte, nicht über eine Eingabe-Dichte).

## 5. Physik der inhomogenen Körper (Kern von v2)

### 5.1 Integrierte Masseneigenschaften (Körperframe, SI)
$$m = \int_V \rho(\mathbf{x})\,dV, \qquad
\mathbf{r}_S = \frac{1}{m}\int_V \rho(\mathbf{x})\,\mathbf{x}\,dV, \qquad
\mathbf{I}_S = \int_V \rho(\mathbf{x})\left(\|\mathbf{x}-\mathbf{r}_S\|^2\,\mathbb{1}
-(\mathbf{x}-\mathbf{r}_S)(\mathbf{x}-\mathbf{r}_S)^{\!\top}\right)dV$$

Für zusammengesetzte Primitive: Summation mit Parallel-Achsen-Satz
(m_i = ρ_i·V_i, I_i um den jeweiligen Eigenschwerpunkt + Steiner-Term
m_i(|d|²𝟙 − ddᵀ)). Für den Kegel mit linearem Profil gelten die geschlossenen
Ausdrücke aus Abschnitt 8. Der Trägheitstensor wird im Körperframe gespeichert
und pro Zeitschritt über die Rotation transformiert: I_welt = R·I_körper·Rᵀ.

### 5.2 Exakte Eintauchgeometrie bei beliebiger Orientierung (Pflichtverfahren)

Verdrängtes Volumen und Angriffspunkt B werden aus dem **exakten Schnitt**
der Körpermitte mit der Wasserebene z = 0 bestimmt – für jeden Krängungs- und
Eintauchwinkel, ohne Kleine-Winkel- oder Achsenparallelitäts-Näherung:

- **Verfahren:** Polyeder-Ebenen-Clip. Der Körper liegt als geschlossene
  Dreiecks-Mesh vor (Primitive werden zur Körpermesh vereinigt); der Clip
  gegen die Halbebene z ≤ 0 liefert das verdrängte Polyeder. V_sub folgt
  per Divergenzsatz, B als flächengewichtetes Mittel der geschlossenen
  Teilmantelflächen – beide exakt bis auf Maschinenpräzision.
- **Genauigkeitsanforderung:** relativer Fehler von V_sub und r_B ≤ 0,1 %
  gegenüber analytischen Referenzen (Kugelkappe, gekippter Kegelstumpf,
  geclippter Quader) – nachgewiesen in Unit-Tests über einen Winkel-Sweep
  0°–90° in 5°-Schritten (K13′).
- **Voxel-Sampling ist kein Abnahmeverfahren** und nur als optionales
  Debug-/Visualisierungswerkzeug zulässig (die frühere Architektur-
  Vereinfachung „Rotationsanteil vernachlässigt" ist damit obsolet).
- Kugel: alternativ geschlossene Kappenformel zulässig (rotationsinvariant).

### 5.3 Auftrieb, Gewicht, Auftriebsmoment
$$\mathbf{F}_A = \rho_W\,V_{sub}\,g\,\hat{z} \text{ in } \mathbf{r}_B, \qquad
\mathbf{F}_G = -m\,g\,\hat{z} \text{ in } \mathbf{r}_S, \qquad
\mathbf{M}_A = (\mathbf{r}_B - \mathbf{r}_S)\times\mathbf{F}_A$$

Das Aufrichtmoment ergibt sich vollständig aus dem Momentengleichgewicht
dieser beiden Kräfte – keine separate Metazentrum-Implementierung in der
Physik. Die Metazentrum-Formel dient ausschließlich als analytischer
Vergleichswert in Tests (Abschnitt 8/9).

### 5.4 Gleichgewicht und Stabilität (analytische Referenz)
Schwimmebene: m = ρ_W·V_sub. Anfangsstabilität (Kleine-Winkel-Näherung):
$$GM = KB + BM - KG, \qquad BM = \frac{I_{wp}}{V_{sub}}$$
mit KB/KG = Höhe von B/S über dem Kiel, I_wp = Flächenmoment 2. Ordnung der
Wasserlinienfläche. GM > 0 → aufrichtend, GM < 0 → kippend. Gültigkeit: die
Näherung weicht beim Bojenkegel bei 10° um ≈ 5,6 % ab (verifiziert), bei 20°
um ≈ 24 % – daher prüfen die Akzeptanzkriterien gegen exakte Referenzmomente
(Abschnitt 8.2), nicht gegen die Formel.

### 5.5 Starrkörper-Solver
- Translation: semi-implizite Euler mit F = m·a.
- Rotation: Quaternion-Orientierung q, Winkelgeschwindigkeit ω;
  ω̇ = I_körper⁻¹(M_körper − ω × (I_körper·ω)) im Körperframe (Kreiselterm
  verpflichtend). Quaternionen werden nach jedem Schritt renormalisiert.
- Kollisionen Körper↔Körper sowie Körper↔Wände/Boden unverändert
  (impulsbasiert, μ = 0,5, e = 0,3, Defaults UI-änderbar).
- Keine Partikel-Interaktion (statisches Wasser; die frühere einseitige
  Partikel↔Körper-Kollision entfällt mit dem SPH-Rückzug aus der
  Physikschleife).

### 5.6 Zeitschritt & Determinismus
Unverändert: Δt = 1/240 s, Akkumulator-Muster, Substeps-Obergrenze (Default 8),
Realtime-Factor ≈ 1, reproduzierbar bei fixem Seed und Substeps (K9′).

## 6. Visualisierung & UI

Unverändert gegenüber v0.2.5 §6 mit folgenden Festlegungen:
- **Wasseroberfläche:** statische, transparente, beleuchtete Ebene bei z = 0
  mit Tiefenfärbung unterhalb. Keine Wellen, keine Verformung.
- Zweiton-Körper (unter/über Wasserlinie) mit Wasserlinien-Kontur: bleibt,
  bewertet gegen die Ebene z = 0.
- Technisches Gitter, Maßstabsleiste, HUD (RTF, FPS, Simulationszeit): bleiben.
- **Kraftpfeile (erweitert):**
  - Auftriebspfeil ab r_B (exakter Angriffspunkt aus 5.2), Länge ∝ F_A,
  - Gewichtspfeil ab r_S, Länge ∝ m·g,
  - Geschwindigkeitspfeil ab r_S,
  - optional einschaltbar: Momentenarm als Linie r_S ↔ r_B,
  - Pfeil-Skalierung, Farbcodes und Beschriftung wie in der bestehenden
    Implementierung (v0.4) – keine visuelle Regression.
- **Status-Panel** (pro gewähltem Körper): Position, |v|, Orientierung
  (Quaternion/Euler), Tiefgang, V_verdrängt, m, r_S, r_B, resultierende
  Kraft, Moment, GM-Schätzwert.
- **Kontrollpanel:** g, Zeitsteuerung (Pause/Schritt/Reset), Spawn mit
  Presets (§4.3) inkl. Dichteprofil-Parameter, Beckenmaße (nach Reset).
  Entfallen: Wind-Regler, Partikelanzahl, Δx/h.

## 7. Technische Rahmenbedingungen & Erweiterbarkeit

- Python 3.11+, PyVista-Rendering, Simulation ohne Rendering-Abhängigkeiten.
- NumPy als Pflichtpfad für den Solver; Taichi bleibt optional für spätere
  Ausbaustufen (kein Abnahmekriterium in v2).
- §7.1 aus v0.2.5 bleibt verbindlich mit Anpassungen:
  - SI-Einheiten, zentrales Parameterobjekt (JSON/YAML) ohne hart kodierte
    Konstanten – ohne Wind/c_w/η-Parameter, dafür mit Dichteprofil-Parametern.
  - Kraftmodul-Schnittstelle apply(body, environment, dt) -> Kraft/Moment
    bleibt; aktive Module in v2: Buoyancy, Gravity. Drag/Stokes/Wind werden
    als deaktivierte Module geführt oder entfernt.
  - Body-/Shape-Interface – Mindestanforderung je Form:
    (a) V_sub und r_B für beliebige Schnitt-Ebene und beliebige Orientierung
        (exakt, siehe 5.2),
    (b) integrierte Masseneigenschaften aus ρ(x): m, r_S, I_S,
    (c) Trägheitstensor-Transformation in den Weltframe.
    A_ref entfällt.
  - Fluid-Interface bleibt als Erweiterungspunkt (SPH ruht dahinter).
  - Szenen-Serialisierung inklusive Dichteverteilungen (reproduzierbare
    Läufe, Regressionstests).

## 8. Referenzkörper „Bojenkegel"

Geometrie: Kegel, H = 2 m, R = 1 m, Spitze im Körperursprung, Achse = +z.
Dichteprofil: ρ(s) = 1200 → 200 kg/m³ linear von der Spitze zur Basis.

### 8.1 Geschlossene Sollwerte

| Größe | Geschlossener Ausdruck | Wert |
|---|---|---|
| Volumen | πR²H/3 | 2,0944 m³ |
| Masse | πR²H·(ρ_tip + 3ρ_base)/12 | 300π ≈ 942,478 kg |
| Mittlere Dichte | (ρ_tip + 3ρ_base)/4 | 450 kg/m³ |
| Schwerpunkt ab Spitze | 3H(ρ_tip + 4ρ_base)/(5(ρ_tip + 3ρ_base)) | 4/3 ≈ 1,3333 m |
| V_verdrängt (Gleichgewicht) | m/ρ_W = 0,3π | 0,9425 m³ |
| Tiefgang ab Spitze | d = (3H²·V_sub/(πR²))^(1/3) = 3,6^(1/3) | 1,5326 m |
| Auftrieb = Gewicht | 300π·g | 9245,7 N |
| Wasserlinienradius | R·d/H | 0,7663 m |
| BM | I_wp/V_sub, I_wp = π·r_w⁴/4 | 0,2874 m |
| KB (ab Spitze) | 3d/4 | 1,1495 m |
| GM (Spitze unten) | KB + BM − KG | +0,1035 m → stabil |
| GM (Basis unten, invertiert gespawnt) | analog, d′ ≈ 0,361 m | −0,1223 m → instabil |

Zweiter Referenzkörper (Regression): homogene Kugel r = 1,0 m mit
ρ = 500 kg/m³ (schwimmt) und ρ = 2000 kg/m³ (sinkt) – Verhalten muss dem
Stand v0.4 entsprechen.

### 8.2 Exakte Referenzmomente (statische Krängung um S, V_sub konstant)

Aufrichtendes Moment bei erzwungener Krängung φ um den Massenschwerpunkt bei
erhaltener Verdrängung V_sub = 0,3π (Kraftgleichgewicht). Referenzwerte per
unabhängiger hochauflösender Monte-Carlo-Integration der wahren
Eintauchgeometrie verifiziert (Statistikfehler < 0,1 %); in der Test-Suite
als Fixture hinterlegen:

| φ | M_exakt | M_Näherung = m·g·GM·sin φ | Abweichung der Näherung |
|---|---|---|---|
| 2° | 32,9 N·m | 33,4 N·m | −1,5 % |
| 5° | 84,5 N·m | 83,4 N·m | +1,3 % |
| 10° | 175,5 N·m | 166,2 N·m | +5,6 % |
| 20° | 404,3 N·m | 327,3 N·m | +23,5 % |

Vorzeichenkonvention: aufrichtend (gegenläufig zur Krängung) positiv.

## 9. Akzeptanzkriterien (Definition of Done für v2)

| K | Kriterium | Prüfung / Toleranz |
|---|---|---|
| K1′ | Regression Schwimmen/Sinken: homogene Kugeln ρ = 500 / 2000 kg/m³ verhalten sich wie v0.4 | QUICK; stationäre Tiefgangslage ± 2 % |
| K2′ | Statischer Auftrieb: Quader 2×2×2 m, halb eingetaucht → F_A = 39.240 N | QUICK; < 1 % |
| K3′ | Hydrostatischer Druck p(z) = ρ_W·g·h exakt am Interface abfragbar | QUICK; < 0,1 % |
| K4′ | Massenintegration: Bojenkegel m = 300π, r_S = 4/3 m ab Spitze; zusammengesetzter Körper gegen numerische Quadratur | QUICK; < 0,1 % |
| K5′ | Bojenkegel erreicht Schwimmebene: Tiefgang 1,533 m ± 2 %, F_A = G ± 1 % | QUICK |
| K6′ | Passives Aufrichten: Bojenkegel invertiert (Basis unten) gespawnt richtet sich in Spitzen-Lage auf; Endkrängung < 5°, innerhalb 20 s Simulationszeit | QUICK |
| K7′ | Aufrichtmoment gegen exakte Referenz: bei statischer Krängung φ ∈ {2°, 5°, 10°, 20°} um S (V_sub konstant) gilt M_sim innerhalb ± 2 % der Werte aus Abschnitt 8.2; Vorzeichen aufrichtend | QUICK; ± 2 % |
| K8′ | Kollisionen: Eindringung < 1 %, Impulserhaltung, Wände/Boden dicht (wie alt-K6) | QUICK |
| K9′ | Reproduzierbarkeit: zwei Läufe, 1.000 Substeps, Abweichung < 1e-9 | QUICK |
| K10′ | Echtzeit: ≥ 10 Körper (inkl. Bojenkegel) bei ≥ 60 FPS auf mittlerer Desktop-Hardware (ohne SPH-Last neu gesetzt) | manuell/Hardware-abhängig |
| K11′ | Interaktion: Klick-Spawn mit Presets, g zur Laufzeit änderbar und sofort wirksam | QUICK |
| K12′ | Test-Suite grün (unittest/pytest) | QUICK |
| K13′ | Geometrie bei beliebiger Lage: V_sub und r_B über Winkel-Sweep 0°–90° (5°-Schritte) für Kugel (gegen Kappenformel), gekippten Kegel und Quader (gegen analytischen Clip) | QUICK; ≤ 0,1 % |

## 10. Unit-Tests: entfallend und neu

**Entfallen (aus v0.4-Suite):** Luftwiderstandsgesetz/v_term (alt K4),
Stokes-Term, SPH-Kernel/Kontinuität/Dichteabfragen, K3-Gradiententest FULL,
Partikel↔Körper-Ausschlusskollision, Wellen-/Heightfield-Tests (alt K5),
c_w-/A_ref-Tests, K7-Partikel-Benchmark.

**Neu:** Massen-/Schwerpunkt-/Tensorintegration (Primitive-Summe vs.
Quadratur), geschlossene Kegelwerte (§8.1), V_sub/r_B-Winkel-Sweep gegen
analytische Referenzen (K13′), exakte Referenzmomente als Fixture (K7′),
Auftriebsmoment-Vorzeichen und Metazentrum-Konsistenz bei kleinen Winkeln,
Quaternion-Integration (Renormierung, Kreiselterm-Konsistenz),
Dichteprofil-Serialisierung, Preset-Spawn.

## 11. Ausbaustufen (nicht Teil von v2)
- v2.1: Widerstands- und Windmodule als optionale Kraftmodule reaktivieren
  (Schnittstelle steht, §7.1).
- v3: Segelflächen/Rumpfgeometrien, frei definierte asymmetrische Körper,
  SPH-Rückkehr als Kraftquelle hinter dem Fluid-Interface, Thermodynamik.

---

## Anhang A – Verifikationshistorie der Referenzwerte
- 10.10.2026: Geschlossene Formeln (§8.1) symbolisch hergeleitet und per
  Monte-Carlo-Integration (8 Mio. Punkte, volumengetreues Sampling)
  bestätigt: Gleichgewicht F_A = G auf 0,05 %, B auf 0,0002 m, S exakt.
- 10.10.2026: Exakte Momente (§8.2) per Monte-Carlo (40 Mio. Punkte)
  bei Krängung um S mit V_sub-Konstanthaltung (Sekantenverfahren auf die
  Schwimmebene) bestimmt; Metazentrum-Näherung als Gegenprobe.
