"""Kraeftebild (P5c Phase C, Umsetzungsplan V5 rev 9 §5).

Reine Geometrie/Daten fuer das Kraefte-Overlay (Taste 7, Layer 'kraefte'):
Gewicht F_G ab r_S abwaerts (grau), Auftrieb F_A ab K aufwaerts (blau),
Hebelarm K<->r_S als Verbindungslinie, Textzeile mit V_tauch/F_A/|M|.

D1: gemeinsame FIXE Skala pro Szene (skala_waehlen) - beide Pfeile teilen
denselben Massstab, damit das Verhaeltnis der Kraefte lesbar bleibt und
Restkraefte sichtbar sind. P5a-Muster: pyvista-frei, rein numpy - die
Wahrheit kommt aus core.auftrieb, hier wird nur projiziert.
"""
import numpy as np

FARBE_FG = "gray"       # Gewicht
FARBE_FA = "#2166ac"    # Auftrieb (Wasserblau, wie FARBE_UNTEN)
FARBE_ARM = "black"

KOPFANTEIL = 0.25
KOPF_RADIUS_FAKTOR = 0.08
FUELLFAKTOR = 0.75


def pfeil_daten(start, vektor):
    """Pfeilgeometrie: Schaft von start bis (1-KOPFANTEIL)*L, Spitze am Ende.

    Rueckgabe-Dict mit start/richtung/laenge/schaft_start/schaft_ende/
    spitze/kopf_laenge/kopf_radius. Rein numpy, deterministisch.
    """
    start = np.asarray(start, dtype=float)
    vektor = np.asarray(vektor, dtype=float)
    laenge = float(np.linalg.norm(vektor))
    if laenge <= 0.0:
        raise ValueError("Pfeil mit Null-Laenge unzulaessig")
    richtung = vektor / laenge
    schaft_ende = start + (1.0 - KOPFANTEIL) * laenge * richtung
    spitze = start + laenge * richtung
    return {"start": start.copy(), "richtung": richtung, "laenge": laenge,
            "schaft_start": start.copy(), "schaft_ende": schaft_ende,
            "spitze": spitze, "kopf_laenge": KOPFANTEIL * laenge,
            "kopf_radius": KOPF_RADIUS_FAKTOR * laenge}


def skala_waehlen(masse, g, referenz_laenge, fuellfaktor=FUELLFAKTOR):
    """D1: fixe Skala - der F_G-Pfeil fuellt fuellfaktor der Referenzlaenge."""
    fg = float(masse) * float(g)
    if fg <= 0.0:
        raise ValueError("masse*g muss positiv sein")
    ref = float(referenz_laenge)
    if ref <= 0.0:
        raise ValueError("referenz_laenge muss positiv sein")
    return fuellfaktor * ref / fg


def kraft_pfeile(erg, r_s, masse, g, skala):
    """(fg, fa): F_G ab r_S abwaerts, F_A ab K (Verdraengungsschwerpunkt) aufwaerts.

    Beide Pfeile teilen dieselbe Skala (D1) - das Verhaeltnis der
    Pfeillaengen ist das Verhaeltnis der Kraefte.
    """
    r_s = np.asarray(r_s, dtype=float)
    fg_vektor = np.array([0.0, 0.0, -float(masse) * float(g) * skala])
    fa_vektor = np.array([0.0, 0.0, erg.F_A.z * skala])
    return pfeil_daten(r_s, fg_vektor), pfeil_daten(erg.K.as_array(), fa_vektor)


def hebelarm_segment(k, r_s):
    """Endpunkte des Hebelarms K<->r_S (Verbindungslinie)."""
    return np.asarray(k, dtype=float), np.asarray(r_s, dtype=float)


def text_zeile(erg):
    """Statuszeile des Kraeftebilds (V_tauch, F_A, |M|)."""
    return ("V_tauch=%7.3f m^3   F_A=%9.1f N   |M|=%9.1f N*m"
            % (erg.V_tauch, erg.F_A.z,
               float(np.linalg.norm(erg.M.as_array()))))
