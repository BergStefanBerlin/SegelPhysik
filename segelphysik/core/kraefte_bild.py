"""Kraeftebild (P5c Phase C) - reine Geometrie/Daten fuer Taste 7.

D1: gemeinsame FIXE Skala (skala_waehlen). P5a-Muster: pyvista-frei.
Spec V4A rev B: moment_bogen() liefert die Geometrie des Drehmoment-
Bogenpfeils um die Rollachse (x) - Richtung nach Vorzeichen von M_x
(Rechte-Hand-Regel); im Gleichgewicht (|M_x| ~ 0) verschwindet er (Z3).
"""
import math

import numpy as np

FARBE_FG = "gray"       # Gewicht
FARBE_FA = "#2166ac"    # Auftrieb (Wasserblau)
FARBE_ARM = "black"
FARBE_MOMENT = "#762a83"  # Drehmoment (violett)

KOPFANTEIL = 0.25
KOPF_RADIUS_FAKTOR = 0.08
FUELLFAKTOR = 0.75

BOGEN_SCHWELLWERT_NM = 1e-6
BOGEN_START_GRAD = 30.0
BOGEN_WINKEL_GRAD = 240.0
BOGEN_PUNKTE = 49


def pfeil_daten(start, vektor):
    """Pfeilgeometrie (Schaft + Spitze). Rein numpy, deterministisch."""
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
    """D1: fixe Skala - F_G-Pfeil fuellt fuellfaktor der Referenzlaenge."""
    fg = float(masse) * float(g)
    ref = float(referenz_laenge)
    if fg <= 0.0 or ref <= 0.0:
        raise ValueError("masse*g und referenz_laenge muessen positiv sein")
    return fuellfaktor * ref / fg


def kraft_pfeile(erg, r_s, masse, g, skala):
    """(fg, fa): F_G ab r_S abwaerts, F_A ab K aufwaerts (D1-Skala)."""
    r_s = np.asarray(r_s, dtype=float)
    fg_vektor = np.array([0.0, 0.0, -float(masse) * float(g) * skala])
    fa_vektor = np.array([0.0, 0.0, erg.F_A.z * skala])
    return pfeil_daten(r_s, fg_vektor), pfeil_daten(erg.K.as_array(), fa_vektor)


def hebelarm_segment(k, r_s):
    """Endpunkte des Hebelarms K<->r_S."""
    return np.asarray(k, dtype=float), np.asarray(r_s, dtype=float)


def text_zeile(erg):
    """Statuszeile des Kraeftebilds (V_tauch, F_A, |M|)."""
    return ("V_tauch=%7.3f m^3   F_A=%9.1f N   |M|=%9.1f N*m"
            % (erg.V_tauch, erg.F_A.z,
               float(np.linalg.norm(erg.M.as_array()))))


def moment_bogen(moment_x, mittelpunkt, radius):
    """Bogenpfeil fuer das Drehmoment um die Rollachse (x, D11).

    Bogen in der y-z-Ebene durch mittelpunkt; positives M_x laeuft im
    positiven Drehsinn um +x (+y -> +z, Rechte-Hand-Regel). Bei
    |M_x| <= BOGEN_SCHWELLWERT_NM: None (Gleichgewicht -> kein Bogen, Z3).
    """
    mx = float(moment_x)
    mitte = np.asarray(mittelpunkt, dtype=float)
    radius = float(radius)
    if radius <= 0.0:
        raise ValueError("radius muss positiv sein")
    if abs(mx) <= BOGEN_SCHWELLWERT_NM:
        return None
    vorzeichen = 1.0 if mx > 0.0 else -1.0
    a0 = math.radians(BOGEN_START_GRAD)
    spanne = math.radians(BOGEN_WINKEL_GRAD)
    a = a0 + spanne * vorzeichen * np.linspace(0.0, 1.0, BOGEN_PUNKTE)
    punkte = np.column_stack([
        np.full(BOGEN_PUNKTE, mitte[0]),
        mitte[1] + radius * np.cos(a),
        mitte[2] + radius * np.sin(a)])
    a_ende = float(a[-1])
    tangente = vorzeichen * np.array([0.0, -math.sin(a_ende),
                                      math.cos(a_ende)])
    richtung = tangente / np.linalg.norm(tangente)
    kopf_laenge = 0.35 * radius
    return {"punkte": punkte, "spitze": punkte[-1] + kopf_laenge * richtung,
            "richtung": richtung, "kopf_laenge": kopf_laenge,
            "kopf_radius": 0.12 * radius, "moment_x": mx}
