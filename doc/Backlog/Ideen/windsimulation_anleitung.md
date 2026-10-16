# Softwareanleitung: Windsimulation (Stufe C2) in SegelPhysik

Stand: 16.10.2026 - basiert auf Codeanalyse des Repos main (134 Commits).
Verwandte Dokumente: `hydrodynamik_anleitung.md` (Wasserseite),
`umbauanleitung_koerper_struktur.md` (Koerper-/Bootstruktur).

---

## 0) Kurzfassung

Ziel ist die Windkraft auf Fock und Grosssegel nach der **Streifenmethode**
(Stufe C2): Das Segel wird in horizontale Streifen zerlegt, jeder Streifen
erhaelt seine **lokale wahre Windgeschwindigkeit** (Windgradient ueber der
Hoehe), daraus den **scheinbaren Wind** (Apparent Wind, unter Beruecksichtigung
der Bootsbewegung), und liefert Lift+Drag nach einer Plattenpolare mit Stall.
Die Streifenkraefte werden zu einer Gesamtkraft mit Angriffspunkt summiert und
ueber die bestehende `fremdkraft_setzen`-Schnittstelle in die Dynamik
eingespeist. Die Stufe N=1 (ein einziger Streifen) ist zugleich der
Testfall gegen die Handrechnung.

Architekturprinzipien (aus dem Struktur-Umbau uebernommen):
Segel als **Segmentliste** modellieren, lokale Anstraemung als **austauschbare
Funktion** - damit bleibt eine spatere Panel-Methode (E, offline als
Kalibrierwerkzeug) moeglich, ohne die Laufzeitstruktur zu veraendern.

---

## 1) Ausgangslage: Codebestand (Rechercheergebnis)

### 1.1 Was es gibt (Relevanz fuer die Windsimulation)

| Modul / Datei | Inhalt | Relevanz |
|---|---|---|
| `core/kraftmodell.py` | `Kraftmodell` mit linearer/quadratischer Daempfung, Fluidgeschwindigkeit, Added Mass; `fremdkraft_setzen(kraft, angriffspunkt)`; `KraftmodellMitHydroCache` | **Injektionspunkt**: Windkraft kommt als Fremdkraft hinzu |
| `core/echtzeit_prozess.py` | Worker: `initialisieren(koerper, rho_w, physik, ...)`, `schritte_berechnen(zustand, anzahl_schritte, fremdkraft=None)` | Nimmt Fremdkraft pro Batch entgegen - hier fliesst der Wind rein |
| `core/dynamik_6dof.py` | `schritt(zustand, kraftfunktion, masse, traegheit, dt, g)` - Newton-Euler, dt = 4 ms | unveraendert |
| `core/auftrieb.py` | `baue_kraftfunktion_6dof`, `als_bindung().blatt_meshes` | Liefert Blatt-Meshes (auch Segel) fuer die Diskretisierung |
| `core/konfig_lader.py` | `lade_konfig()`, `lade_physik()` (D8: dt/g/Daempfung/Voxel aus `physik.json`) | Windparameter kommen nach `physik.json` |
| `core/fabriken.py` / `core/boot_bau.py` | `baue_boot(konfig)`, `baue_teil(name)` - laedt OBJ-Teile (u. a. `grosssegel.obj`, `fock.obj`) | Quelle der Segelgeometrie |
| `core/hydrostatik.py`, `voxelmodell.py`, `wasser_schnitt.py` | Auftrieb nur unter Wasserlinie | Segel liegen UEBER der Wasserlinie - Hydrostatik beruehrt sie nicht, keine Konflikte |
| `core/kraefte_bild.py`, `overlays.py`, `pfeilstil.py` | Kraftpfeile je Koerper/Teil | Windpfeile spaeter hier darstellen |
| `demo_app.py` | Modi RUHEND/STATISCH/ECHTZEIT, Objektauswahl (kegel/quader/pyramide/boot), Taktschlag-Schleife | GUI-Anbindung: Windanzeige + ECHTZEIT-Modus |
| `core/stoerung.py` | Zufaellige Stoerpose (nicht windbezogen) | unveraendert |

### 1.2 Kernbefunde

1. **Es existiert KEIN Windmodul.** Weder True Wind noch Apparent Wind noch
   Aerodynamik sind vorhanden. Die Segel tragen derzeit nur Masse (ueber
   Wanddicke im JSON), keine Kraft.
2. **Die Kraftinjektion ist fertig:** `Kraftmodell.fremdkraft_setzen()` nimmt
   Kraft MIT Angriffspunkt (relativ zum Schwerpunkt) - genau das, was der Wind
   am Segeldruckpunkt braucht. `echtzeit_prozess.schritte_berechnen` reicht
   sie pro Batch durch.
3. **Der ECHTZEIT-Modus der Demo treibt die Uhr, aber nicht die 6DOF-Dynamik**
   - die Dynamikschleife (`dynamik_6dof.schritt` im Worker) ist von der Demo
   noch nicht verdrahtet. Die Windsimulation sollte daher von Anfang an an
   `echtzeit_prozess` andocken (nicht an die Demo-Animation).
4. **Segelgeometrie:** `grosssegel.obj` und `fock.obj` liegen als eigene Teile
   vor (Unity-Konvention, gemeinsamer Ursprung, SKALA 0,25). Fuer die
   Streifenmethode brauchen wir je Segel: Flaeche, Sehne je Hoehe,
   Vorliek-Achse. Nach dem Struktur-Umbau kommt das sauber ueber die Rolle
   `segel`; bis dahin ueber `baue_teil("grosssegel")` / `baue_teil("fock")`.
5. **Konfigurationsstil:** strenge Validierung, kein stiller Fallback -
   der neue `wind`-Zweig in `physik.json` folgt diesem Stil (Pflichtfelder,
   Bereichspruefung, Vorlage in `doc/`).

---

## 2) Zielbild Stufe C2

```
True Wind (physik.json: Geschw., Richtung, Bezugshoehe 10 m, Exponent p)
        |
        v  Windprofil v(z) = v10 * (z/10)^p          [core/wind.py]
        |
        v  Apparent Wind je Streifen: v_A = v_T(z) - v_Boot
        |
        v  Segelstreifen (N Streifen je Segel)       [core/segelaero.py]
        |     je Streifen: Flaeche, Mittelpunkt, Sehnenrichtung, alpha
        |     Plattenpolare mit Stall -> Lift, Drag
        v
   Summe je Segel: (Gesamtkraft, Angriffspunkt)  -> fremdkraft_setzen
        |
        v
   dynamik_6dof.schritt  (unveraendert)
```

**N=1-Teststufe:** Mit N=1 Streifen (Flaeche = Gesamtflaeche, Mittelpunkt =
Flaechenschwerpunkt) muss das Modul exakt das Ergebnis der Handrechnung
liefern. Erst danach wird der Windgradient zugeschaltet (C2 voll).

**Vorbereitung auf E (bewusst schmal):**
- Segel als Segmentliste (`Segelstreifen`-Objekte mit Position/Normale/Sehne),
  nicht als ein monolithisches Segelobjekt.
- Kraftfunktion pro Segment nimmt die LOKALE Anstraemung entgegen - ein
  spaeteres induziertes Geschwindigkeitsfeld (Spalt Fock/Grosssegel) kann
  dazwischengeschaltet werden, ohne die Kraftintegration anzufassen.
- Mehr wird nicht vorbereitet: Panel-Methoden brauchen andere Datenstrukturen;
  ihr realistischer Einsatz ist offline (Kalibrierung der Polaren), nicht in
  der Echtzeitschleife.

---

## 3) Physikalischer Kern (kurz)

**Apparent Wind** (pro Schritt, pro Streifenhoehe z):

    v_A = v_T(z) - v_Boot        (Vektoren in Weltkoordinaten)

**Windprofil** (Potenzgesetz, Bezugshoehe z_ref = 10 m):

    v_T(z) = v10 * (max(z, z_min) / z_ref)^p * e_richtung

p typisch 0.10 (offene See) bis 0.20 (Binnenland); z_min ~ 0.5 m gegen
Singularitaet am Boden.

**Anstellwinkel** je Streifen:

    alpha = Winkel zwischen v_A (Projektion senkrecht zur Drehachse) und
            der Sehnenrichtung des Streifens (nach Trim-Winkel delta)

**Plattenpolare mit Stall** (duenne Platte, endliche Streckung):

    C_L(alpha) = 2*pi*s* sin(alpha)   fuer |alpha| <= alpha_stall
    C_L        = C_L,stall * sign(alpha), linear abklingend dahinter
    C_D(alpha) = C_D0 + C_L^2 * (1/(pi*e_AR*AR))   (induzierter Anteil)
                 + Plattenanteil ~ 1.2 * sin^2(alpha)

s = AR/(AR+2) (endliche Streckung), AR = Sehnenverhaeltnis des Segels.
Parameter (alpha_stall ~ 15-18 Grad, C_D0 ~ 0.02, e_AR ~ 0.8) kommen nach
`physik.json`, nicht in den Code.

**Kraft je Streifen** (in der Horizontalebene, vereinfachend; Krengungs-
komponente folgt automatisch aus dem Hoehenarm des Angriffspunkts):

    F_L = 0.5 * rho_luft * v_A^2 * A_streifen * C_L(alpha)   (senkrecht zu v_A)
    F_D = 0.5 * rho_luft * v_A^2 * A_streifen * C_D(alpha)   (parallel zu v_A)

rho_luft = 1.225 kg/m^3 (konfigurierbar).

**Summation je Segel:**

    F_gesamt = Summe F_i
    M_gesamt = Summe r_i x F_i      (r_i = Streifenmittelpunkt relativ zum
                                     Bootsschwerpunkt)
    Angriffspunkt = Schwerpunkt des resultierenden Kraftvektors:
    r_D = Summe (r_i * |F_i|) / Summe |F_i|

Uebergeben wird das Paar (F_gesamt, M_gesamt) bzw. (F_gesamt, r_D) an
`fremdkraft_setzen` - je nachdem, welche Form die Schnittstelle erwartet
(siehe S5).

---

## 4) Neue und geaenderte Dateien

### 4.1 Neu: `segelphysik/core/wind.py`

Rein, zustandslos, SI-Einheiten (Stil wie `koerper_formen.py`):

    def windprofil(hoehe_m, v10, exponent_p, bezugshoehe_m=10.0, z_min=0.5)
        -> float
    def wahrer_wind(v10, richtung_rad, hoehe_m, exponent_p, ...)
        -> np.ndarray        # 3D-Vektor, Weltrahmen
    def scheinbarer_wind(v_true, v_boot) -> np.ndarray

Kein Zustand: Die Demo/der Worker ruft dies pro Streifen auf. Ein
`Windfeld`-Objekt (v10, Richtung, p) wird einmal gebaut und an die
Kraftfunktion gebunden (Muster wie `baue_kraftfunktion_6dof`).

### 4.2 Neu: `segelphysik/core/segelaero.py`

    class Segelstreifen:
        flaeche_m2: float
        mittelpunkt: np.ndarray    # Weltrahmen, relativ Bootsschwerpunkt
        sehne: np.ndarray          # Einheitsvektor (Sehnenrichtung)
        achse: np.ndarray          # Drehachse (Vorliek bzw. Mast)

    def segel_streifen(mesh_punkte, mesh_faces, n_streifen,
                       achse, ursprung) -> list[Segelstreifen]
        # Zerlegt das Segel-Mesh entlang der Achse in n horizontale
        # Streifen; je Streifen: Dreiecksflaechen summieren, Flaechen-
        # schwerpunkt mitteln, Sehne = groesste Ausdehnung senkrecht
        # zur Achse im Streifen.

    def streifen_kraft(streifen, v_apparent, delta_rad, polare, rho)
        -> (np.ndarray kraft, np.ndarray hebelarm)
        # alpha aus v_apparent und Sehne (nach delta um `achse`
        # gedreht); Polare auswerten; Kraft in Horizontalebene.

    def segel_kraft_gesamt(streifen_liste, windfeld, v_boot, deltas,
                           polare, rho) -> (F_gesamt, M_gesamt)
        # Schleife ueber Streifen: lokalen wahren Wind (Hoehe des
        # Streifens!), apparent, Kraft; Summation zu F und M.

    class PlattenPolare: alpha_stall, c_d0, e_ar, ar
        def c_l(alpha), c_d(alpha) -> float

### 4.3 Geaendert: `konfigurationen/physik.json` - neuer Zweig

    "wind": {
        "an": true,
        "geschwindigkeit_m_pro_s": 5.0,
        "richtung_grad": 90.0,          # meteorologisch: woher (0=Nord)
        "bezugshoehe_m": 10.0,
        "profil_exponent": 0.14,
        "dichte_kg_pro_m3": 1.225,
        "polare": {
            "typ": "platte",
            "alpha_stall_grad": 16.0,
            "c_d0": 0.02,
            "e_ar": 0.8
        },
        "streifen": 8
    }

Validierung in `konfig_lader.lade_physik()`: Pflichtfelder, Geschwindigkeit
>= 0, Exponent in [0.05, 0.4], Streifen >= 1, "an": false schaltet die Kraft
ab (dann null-Vektoren, keine Sonderfaelle im Code). Vorlage in `doc/`
ergaenzen (kein stiller Fallback).

### 4.4 Geaendert: `core/kraftmodell.py` (minimal)

`Kraftmodell` erhaelt neben der bestehenden Einzel-Fremdkraft optional eine
Liste von Fremdkraeften (je Segel eine):

    def fremdkraefte_setzen(self, liste):   # [(kraft, angriffspunkt), ...]
        self._fremdkraefte = tuple(liste)

In `mit_hydrostatik()` werden alle Beitraege (Kraft + Moment ueber den
Hebelarm) addiert. Die alte Einzelmethode bleibt (Rueckwaertskompatibilitaet
der Tests). Alternativ - falls die Summation im Worker bevorzugt wird -
bleibt alles beim Einzelaufruf und `segelaero` liefert pro Segel ein Paar;
der Worker summiert. Entscheidung S5.

### 4.5 Geaendert: `core/echtzeit_prozess.py`

`initialisieren()` erhaelt zusaetzlich: Segelstreifen (einmal aus den
Blatt-Meshes gebaut), Windfeld, Polare. `schritte_berechnen()` berechnet pro
Batch VOR dem ersten Schritt die Windkraefte aus dem aktuellen Zustand
(Geschwindigkeit des Bootes steckt im Zustand) und setzt sie als
Fremdkraefte. Innerhalb eines Batches (N Schritte) bleibt der Wind eingefroren
- bei Batchgroesse <= 4 Schritten (16 ms) vertretbar; Dokumentation des
Fehlers nicht vergessen.

### 4.6 Geaendert: `demo_app.py` (zuletzt)

- Statuszeile: True Wind, Apparent Wind (Geschwindigkeit + Richtung) am
  Standardmesspunkt (Masttop).
- Taste fuer Wind an/aus + Richtungs-/Staerkenregler (ueber `ControlPanel`).
- Kraftpfeil am Segel (ueber `kraefte_bild`/`overlays`, Layer `wind`),
  Angriffspunkt = r_D aus 3).

---

## 5) Informationsfluss

                    physik.json ("wind")
                           |  lade_physik()
                           v
   +------------------ Windfeld ------------------+
   |                                              |
   v                                              v
 Segelstreifen (einmalig                    v_Boot (Zustand)
  aus Blatt-Meshes)                              |
   |                                             v
   +--------> segelaero.segel_kraft_gesamt <-----+
                    |
                    v
          [(F_i, r_i)] je Segel
                    |
                    v
     echtzeit_prozess.schritte_berechnen(fremdkraft=...)
                    |
                    v
          kraftmodell.fremdkraft_setzen
                    |
                    v
          dynamik_6dof.schritt (unveraendert)

Einmalig (Bootbau): Mesh -> Streifen. Pro Batch: Wind -> Kraefte. Pro
Schritt: Kraefte -> Dynamik. Keine Mesh-Operationen im Heisspfad.

---

## 6) Umsetzungsschritte (Baustellen)

### S1 - Polare + Windfeld (rein, testbar ohne Boot)

**Dateien:** `core/wind.py` (neu), `core/segelaero.py` (nur `PlattenPolare`).

1. `PlattenPolare` implementieren: `c_l(alpha)` mit Stall-Modell,
   `c_d(alpha)` mit induziertem + Plattenanteil. Winkel immer auf
   (-pi, pi] normalisieren; alpha = 0 muss c_l = 0 liefern (Symmetrie).
2. `windprofil`, `wahrer_wind`, `scheinbarer_wind` implementieren.
3. **Tests** (`tests/test_wind.py`):
   - Profil: v(10 m) = v10 (Bezugshoehe); v(0.5 m) = v10 * (0.05)^p;
     monoton steigend in z.
   - Apparent Wind: Boot in Windrichtung fahrend -> v_A = v_T - v_Boot
     (Vektorpruefung, Handrechnung).
   - Polare: c_l(0) = 0; c_l(alpha_stall) maximal; c_l > 0 fuer kleine
     positive alpha; c_d(alpha) >= c_d0 ueberall; Symmetrie c_l(-a) = -c_l(a).

### S2 - Streifenzerlegung (einmalig pro Segel)

**Dateien:** `core/segelaero.py` (`segel_streifen`), Aufruf spaeter in
`echtzeit_prozess.initialisieren`.

1. Eingabe: Blatt-Mesh des Segels (Welt-Konvention, skaliert - wie die
   Hydrostatik es von `als_bindung().blatt_meshes` bekommt), Drehachse
   (aus dem `beweglich`-Manifest bzw. bis dahin fest: Mast fuer
   Grosssegel, virtuelle Linie 1/3 von vorn fuer Fock), n Streifen.
2. Zerlegung entlang der Hochachse (Weltrahmen z): Streifengrenzen aus
   min/max der Meshpunkte; je Streifen Dreiecke zuordnen (Mittelpunkt-z),
   Flaeche summieren, Flaechenschwerpunkt mitteln, Sehne = maximale
   Ausdehnung senkrecht zur Achse.
3. Randfall: leere Streifen (Mesh-Luecken) -> Flaeche 0, beim Summieren
   uebersprungen (kein Sonderfall im Kraftpfad).
4. **Tests** (`tests/test_segelaero.py`):
   - Rechtecksegel (aus `form: box`, z. B. 2 m x 1 m): 8 Streifen ->
     jede Streifenflaeche = 2*1/8, Summe = 2 m^2 (analytisch).
   - Streifenmittelpunkte aequidistant, aufsteigend in z.
   - N=1: eine Streifen, Flaeche = Gesamtflaeche, Mittelpunkt =
     Flaechenschwerpunkt.

### S3 - Kraftfunktion je Streifen + Summation

**Dateien:** `core/segelaero.py` (`streifen_kraft`, `segel_kraft_gesamt`).

1. `streifen_kraft`: delta um die Achse rotieren (Rotationsformel wie in
   der Umbauanleitung, Rodrigues); alpha = Winkel(v_A_proj, Sehne);
   Vorzeichenkonvention festhalten (positive alpha = Druckseite Luv? -
   dokumentieren und in Tests verankern, analog D11-Konvention).
2. Kraft in Horizontalebene: Lift senkrecht zu v_A-Projektion, Drag
   parallel; Hebelarm = Streifenmittelpunkt - Bootsschwerpunkt.
3. `segel_kraft_gesamt`: Schleife, Summation zu (F, M) bzw. (F, r_D).
4. **Tests**:
   - N=1 gegen Handrechnung: gegeben v_A = 5 m/s senkrecht zur Sehne,
     alpha = 90 Grad -> Stall -> F = 0.5*rho*v^2*A*c_d(90 Grad), Richtung
     parallel v_A. Zahlen im Test hart codiert (Handrechnung).
   - Windgradient aus (p = 0, alle Streifen gleiche Hoehe wirken nicht -
     stattdessen: alle Streifen gleiche Geschwindigkeit erzwingen) ->
     Ergebnis identisch zu N=1 mit gleicher Gesamtflaeche (Konsistenz-
     test C1 vs. C2).
   - Moment: Ein Streifen oben am Mast muss ein groesseres
     Kraengungsmoment liefern als derselbe unten (Hebelarm-Check).
   - delta = 0, Wind genau von vorn (alpha ~ 0) -> Kraft ~ 0 (nur Drag).

### S4 - Konfiguration

**Dateien:** `konfigurationen/physik.json`, `core/konfig_lader.py`,
Vorlage in `doc/`.

1. `wind`-Zweig ergaenzen (siehe 4.3), Validierung streng:
   unbekannte Schluessel = Fehler, Bereiche pruefen, "an": false erlaubt.
2. `lade_physik()` liefert das Windfeld-Dict an den Aufrufer.
3. **Tests**: fehlender Zweig bei "an": true -> Fehlermeldung mit Pfad;
   Exponent 0.5 -> Fehler; "an": false -> Windfeld inaktiv, Kraft null.

### S5 - Injektion in die Dynamik

**Dateien:** `core/kraftmodell.py`, `core/echtzeit_prozess.py`.

1. Entscheidung dokumentieren: Mehrfach-Fremdkraefte im Kraftmodell
   (`fremdkraefte_setzen`, Liste) ODER Summation im Worker. Empfehlung:
   Liste im Kraftmodell - dort ist der Hebelarm-Mechanismus schon
   vorhanden, und die GUI kann spaeter die Einzelkraefte je Segel
   abgreifen, ohne sie erneut zu rechnen.
2. `initialisieren()` erweitern: Segelstreifen + Windfeld + Polare
   binden (einmalig pro Worker).
3. `schritte_berechnen()`: vor der Batchschleife Windkraefte aus dem
   AKTUELLEN Zustand berechnen und setzen; innerhalb des Batches
   eingefroren (Dokumentation: Fehler < 1 % bei Batch <= 4 Schritte).
4. **Tests**: Boot ruhend, Wind konstant -> Kraft konstant; Boot mit
   Geschwindigkeit in Windrichtung -> apparent sinkt -> Kraft sinkt
   (Monotonie-Test).

### S6 - GUI-Anbindung

**Dateien:** `demo_app.py`, `core/kraefte_bild.py` bzw. `overlays.py`,
`steuerung.py`.

1. Statuszeile: True/Apparent Wind am Masttop (Geschw. + Richtung).
2. Layer `wind`: Pfeil am Segeldruckpunkt (r_D), Stil wie Kraeftepfeile.
3. Tasten: Wind an/aus, Staerke +/-, Richtung drehen (ueber ControlPanel;
   Tastenbelegung dokumentieren - freie Tasten suchen, 'v'/'7' etc. sind
   belegt).
4. ECHTZEIT-Modus: Windkraft wirkt auf die Dynamik (sobald diese
   verdrahtet ist); RUHEND/STATISCH: nur Anzeige.

---

## 7) Reihenfolge und Aufwand

| Reihenfolge | Baustelle | Abhaengigkeit | Aufwand |
|---|---|---|---|
| 1 | S1 Polare + Windfeld | keine | 0.5 Tag |
| 2 | S2 Streifenzerlegung | S2 unabhaengig von S1, parallel moeglich | 1 Tag |
| 3 | S3 Kraftfunktion + Summation | S1 + S2 | 1 Tag |
| 4 | S4 Konfiguration | S1 (Feldnamen) | 0.5 Tag |
| 5 | S5 Injektion | S3 + S4 | 1 Tag |
| 6 | S6 GUI | S5 | 0.5-1 Tag |

Gesamt: ca. 4-5 Tage. Jede Stufe endet mit gruenem Teststand; die
N=1-Handrechnung (S3) ist der Meilenstein "Physik steht".

**Abhaengigkeit vom Struktur-Umbau:** S2 liest die Segel-Meshes. Vor dem
Umbau ueber `baue_teil("grosssegel")` / `baue_teil("fock")`; nach dem
Umbau ueber die Rollen-Sicht (`rolle "segel" -> Blatt-Meshes`). Die
Drehachsen kommen aus dem `beweglich`-Manifest (nach Umbau) bzw. als
Konstanten mit TODO-Markierung (vor Umbau). Die Windsimulation kann
VOR dem Umbau gebaut werden, wenn die zwei Konstanten akzeptiert werden.

---

## 8) Softwarestruktur nach der Umsetzung

    core/
      wind.py           NEU   Windfeld, Profil, apparent wind (rein)
      segelaero.py      NEU   Streifen, Polare, Kraftsumme (rein)
      kraftmodell.py    GEAE  Mehrfach-Fremdkraefte
      echtzeit_prozess.py GEAE Windbindung, Kraefte pro Batch
      konfig_lader.py   GEAE  wind-Zweig validieren
      dynamik_6dof.py   UNVERAENDERT
      auftrieb/hydrostatik/voxel UNVERAENDERT (Wind = oberhalb Wasserlinie)

Schichtregel: wind/segelaero kennen keine GUI und keinen Zustand;
echtzeit_prozess ist der einzige Ort, der Zustand + Wind verbindet;
demo_app nur Anzeige/Steuerung. Damit bleiben alle neuen Module im
Testkontext ohne PyVista lauffaehig (wie der Rest von core/).

---

## 9) Modellimport / Parametrierung fuer die Segel

1. Segel-Meshes muessen (wie alle Teile) geschlossen orientierte Flaeche
   haben? Fuer die Streifenmethode NICHT zwingend: Wir brauchen nur
   Dreiecksflaechen + Normalen, keine geschlossene Huelle. Doppelflaechen
   (beidseitig sichtbare Segel) fuehren zu doppelten Kraeften - Loader-
   Warnung, wenn Dreieckspaare deckungsgleich sind.
2. Sehne und Vorliek: Aus dem Mesh abgeleitet (groesste Ausdehnung je
   Streifen). Bei exotischen Segelformen (Rundmast-Genua) Streifenanzahl
   erhoehen; Konvergenz testen (Ergebnis bei N und 2N < 5 % Differenz).
3. Polaren-Parameter je Segel moeglich (Grosssegel dicker/Spalt zur
   Fock): Der `polare`-Zweig kann pro Rolle variiert werden - erst wenn
   Mess-/Referenzwerte vorliegen (sonst Kalibrierillusion).

---

## 10) Offene Punkte (bewusst vertagt)

1. Spalt Fock/Grosssegel (C3): empirischer Multiplikator oder Abwind-
   korrektur - erst nach C2-Erfahrung.
2. Kraengung des Segels bei gekrängtem Boot: Streifen liegen im
   Weltrahmen horizontal - bei Kraengung muessten sie der Segelgeometrie
   folgen. Erste Version: Streifen im Koerperrahmen definieren, lokale
   Hoehe fuer das Windprofil NAEHERN (Fehler dokumentieren).
3. Zeitlich variabler Wind (Boeen): Windfeld ist statisch; Boeen =
   spaeteres Modul, Schnittstelle (Windfeld -> Geschwindigkeit je Hoehe)
   bleibt gleich.
4. Panel-Methode (E): nur offline als Kalibrierwerkzeug; keine
   Schnittstelle in dieser Stufe.
