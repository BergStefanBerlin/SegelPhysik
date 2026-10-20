"""Kraeftebild (P5c Phase C) - reine Geometrie/Daten fuer Taste 7.

D1: gemeinsame FIXE Skala (skala_waehlen). P5a-Muster: pyvista-frei.
Spec V4A rev B: moment_bogen() liefert die Geometrie des Drehmoment-
Bogenpfeils um die Rollachse (x) - Richtung nach Vorzeichen von M_x
(Rechte-Hand-Regel); im Gleichgewicht (|M_x| ~ 0) verschwindet er (Z3).
"""
import math

import numpy as np

from .rechenpfad import nativer_kern, rechenpfad

FARBE_FG = "gray"       # Gewicht
FARBE_FA = "#2166ac"    # Auftrieb (Wasserblau)
FARBE_ARM = "black"
FARBE_MOMENT = "#762a83"  # Drehmoment (violett)
FARBEN_MOMENT = ("#762a83", "#1b7837", "#e08214")  # um x, y, z
FARBE_REST = "#d73027"    # Resultierende Kraft
FARBE_ZUSATZ = "#e08214"  # Widerstand/Added Mass
FARBE_FREMD = "#f1c40f"   # Fremdkraft (gelb)

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
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        return native_laden().pfeil_daten(
            start, vektor, KOPFANTEIL, KOPF_RADIUS_FAKTOR)
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


@nativer_kern("pfeil_fest", skalare=(2, 3, 4, 5))
def pfeil_fest(start, vektor, durchmesser, kopf_durchmesser, kopf_laenge,
               mindestlaenge=0.0):
    """Pfeil mit fester Dicke: nur die Laenge folgt dem Vektor.

    Kopf und Schaft haben absolute Masse; nur wenn der Pfeil kuerzer als
    der doppelte Kopf ist, schrumpft der Kopf proportional. Unter
    `mindestlaenge` wird mindestens diese Laenge gezeichnet.
    """
    start = np.asarray(start, dtype=float)
    vektor = np.asarray(vektor, dtype=float)
    betrag = float(np.linalg.norm(vektor))
    if betrag <= 0.0:
        raise ValueError("Pfeil mit Null-Laenge unzulaessig")
    richtung = vektor / betrag
    laenge = max(betrag, float(mindestlaenge))
    kopf_l = float(kopf_laenge)
    kopf_r = 0.5 * float(kopf_durchmesser)
    if kopf_l > 0.5 * laenge:
        faktor = 0.5 * laenge / kopf_l
        kopf_l *= faktor
        kopf_r *= faktor
    spitze = start + laenge * richtung
    return {"start": start.copy(), "richtung": richtung, "laenge": laenge,
            "betrag": betrag, "schaft_start": start.copy(),
            "schaft_ende": spitze - kopf_l * richtung, "spitze": spitze,
            "kopf_laenge": kopf_l, "kopf_radius": kopf_r,
            "schaft_radius": 0.5 * float(durchmesser)}


def strich_linien(punkte, strich, luecke, max_abstand=None):
    """Zerlegt einen Linienzug in Striche.

    Liefert (punkte, zellen) fuer pyvista.PolyData(punkte, lines=zellen):
    jeder Strich ist ein eigener Linienzug; Striche beginnen bei 0 und
    wiederholen sich mit Periode strich + luecke.
    """
    p = np.asarray(punkte, dtype=float)
    strich = float(strich)
    luecke = float(luecke)
    if strich <= 0.0 or luecke < 0.0:
        raise ValueError("strich > 0 und luecke >= 0 erforderlich")
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        abstand = float(max_abstand if max_abstand else strich / 4.0)
        return native_laden().strich_linien(p, strich, luecke, abstand)
    segment = np.linalg.norm(np.diff(p, axis=0), axis=1)
    kum = np.concatenate([[0.0], np.cumsum(segment)])
    gesamt = float(kum[-1])
    if gesamt <= 0.0:
        raise ValueError("Linienzug ohne Laenge")
    abstand = max_abstand if max_abstand else strich / 4.0
    alle = []
    zellen = []
    s = 0.0
    n = 0
    while s < gesamt - 1e-12:
        ende = min(s + strich, gesamt)
        anzahl = max(2, int(math.ceil((ende - s) / abstand)) + 1)
        t = np.linspace(s, ende, anzahl)
        pts = np.stack([np.interp(t, kum, p[:, i]) for i in range(3)], axis=1)
        alle.append(pts)
        zellen.extend([anzahl] + list(range(n, n + anzahl)))
        n += anzahl
        s += strich + luecke
    return np.vstack(alle), np.asarray(zellen, dtype=np.int64)


def paar_moment_auftrieb(erg, r_s):
    """Moment des Paars Gewicht/Auftrieb um r_S: (K - r_S) x F_A.
    F_G greift in r_S an und traegt nichts bei."""
    k = np.asarray(erg.K.as_array(), dtype=float)
    if rechenpfad() == "cpp":
        return paar_moment_kraft(k, erg.F_A.as_array(), r_s)
    return np.cross(k - np.asarray(r_s, dtype=float), erg.F_A.as_array())


@nativer_kern("kraft_paarmoment")
def paar_moment_kraft(angriff, kraft, r_s):
    """Moment einer Kraft um r_S: (Angriff - r_S) x F."""
    return np.cross(np.asarray(angriff, dtype=float)
                    - np.asarray(r_s, dtype=float),
                    np.asarray(kraft, dtype=float))


@nativer_kern("kraft_skala", skalare=(0, 1, 2, 3))
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
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        return native_laden().kraft_pfeile(
            r_s, np.asarray(erg.K.as_array(), dtype=float), float(erg.F_A.z),
            float(masse), float(g), float(skala), KOPFANTEIL, KOPF_RADIUS_FAKTOR)
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
    """Bogenpfeil fuer das Drehmoment um die Rollachse (x, D11)."""
    bogen = moment_bogen_achse(moment_x, mittelpunkt, radius, 0)
    if bogen is not None:
        bogen["moment_x"] = bogen["moment"]
    return bogen


def moment_bogen_achse(moment, mittelpunkt, radius, achse):
    """Bogenpfeil fuer das Drehmoment um Welt-Achse achse (0=x, 1=y, 2=z).

    Der Bogen liegt in der Ebene senkrecht zur Achse; positives Moment
    laeuft im positiven Drehsinn (Rechte-Hand-Regel, zyklisch x: y->z,
    y: z->x, z: x->y). Bei |M| <= BOGEN_SCHWELLWERT_NM: None (Z3).
    """
    mx = float(moment)
    mitte = np.asarray(mittelpunkt, dtype=float)
    radius = float(radius)
    if radius <= 0.0:
        raise ValueError("radius muss positiv sein")
    if achse not in (0, 1, 2):
        raise ValueError("achse muss 0, 1 oder 2 sein")
    if abs(mx) <= BOGEN_SCHWELLWERT_NM:
        return None
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        return native_laden().moment_bogen(
            mx, mitte, radius, achse, BOGEN_SCHWELLWERT_NM,
            BOGEN_START_GRAD, BOGEN_WINKEL_GRAD, BOGEN_PUNKTE)
    vorzeichen = 1.0 if mx > 0.0 else -1.0
    u = np.zeros(3)
    v = np.zeros(3)
    u[(achse + 1) % 3] = 1.0
    v[(achse + 2) % 3] = 1.0
    a0 = math.radians(BOGEN_START_GRAD)
    spanne = math.radians(BOGEN_WINKEL_GRAD)
    a = a0 + spanne * vorzeichen * np.linspace(0.0, 1.0, BOGEN_PUNKTE)
    punkte = (mitte + radius * np.cos(a)[:, None] * u
              + radius * np.sin(a)[:, None] * v)
    a_ende = float(a[-1])
    tangente = vorzeichen * (-math.sin(a_ende) * u + math.cos(a_ende) * v)
    richtung = tangente / np.linalg.norm(tangente)
    kopf_laenge = 0.35 * radius
    return {"punkte": punkte, "spitze": punkte[-1] + kopf_laenge * richtung,
            "richtung": richtung, "kopf_laenge": kopf_laenge,
            "kopf_radius": 0.12 * radius, "moment": mx, "achse": achse}


def zusatz_pfeile(erg, r_s, masse, g, skala, schwelle_n=1e-6):
    """(rest, zusatz): Resultierende (F_ges + F_G) und nicht-hydrostatische
    Kraft (F_ges - F_A: Widerstand, Added Mass) ab r_S; None unter Schwelle."""
    r_s = np.asarray(r_s, dtype=float)
    f_ges = erg.F_gesamt.as_array()
    f_a = erg.F_A.as_array()
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        return native_laden().zusatz_pfeile(
            r_s, np.asarray(f_ges, dtype=float), np.asarray(f_a, dtype=float),
            float(masse), float(g), float(skala), float(schwelle_n),
            KOPFANTEIL, KOPF_RADIUS_FAKTOR)
    fg = np.array([0.0, 0.0, -float(masse) * float(g)])
    ergebnis = []
    for vektor in (f_ges + fg, f_ges - f_a):
        if float(np.linalg.norm(vektor)) <= schwelle_n:
            ergebnis.append(None)
        else:
            ergebnis.append(pfeil_daten(r_s, vektor * skala))
    return tuple(ergebnis)


def wirkungslinie_auf_geometrie(kraft, moment, bezugspunkt, punkte, dreiecke,
                                rotation=None, toleranz=1e-9):
    """Schnitt der Kraftwirkungslinie mit der benetzten Dreiecksgeometrie.

    ``moment`` ist um ``bezugspunkt`` angegeben. Ohne geometrischen
    Schnittpunkt wird der Linienanker samt Richtung zur expliziten
    Wirkungslinienanzeige zurueckgegeben.
    """
    kraft = np.asarray(kraft, dtype=np.float64)
    moment = np.asarray(moment, dtype=np.float64)
    bezugspunkt = np.asarray(bezugspunkt, dtype=np.float64)
    punkte = np.asarray(punkte, dtype=np.float64)
    dreiecke = np.asarray(dreiecke)
    if (kraft.shape != (3,) or moment.shape != (3,)
            or bezugspunkt.shape != (3,) or not np.isfinite(kraft).all()
            or not np.isfinite(moment).all()
            or not np.isfinite(bezugspunkt).all()):
        raise ValueError("Wirkungslinie benoetigt endliche 3D-Wrenchdaten")
    if (punkte.ndim != 2 or punkte.shape[1] != 3
            or not np.isfinite(punkte).all()
            or not np.issubdtype(dreiecke.dtype, np.integer)
            or dreiecke.ndim != 2 or dreiecke.shape[1] != 3
            or np.any(dreiecke < 0) or np.any(dreiecke >= len(punkte))):
        raise ValueError("Wirkungslinie benoetigt ein gueltiges Dreiecksmesh")
    kraftquadrat = float(np.dot(kraft, kraft))
    if kraftquadrat <= toleranz * toleranz:
        raise ValueError("Kraftwirkungslinie ist fuer Nullkraft undefiniert")
    R = np.eye(3) if rotation is None else np.asarray(rotation, dtype=float)
    if (R.shape != (3, 3) or not np.isfinite(R).all()
            or not np.allclose(R.T @ R, np.eye(3), atol=1e-8, rtol=0.0)
            or not np.isclose(np.linalg.det(R), 1.0,
                              atol=1e-8, rtol=0.0)):
        raise ValueError("Wirkungslinie benoetigt eine gueltige Rotation")
    if rechenpfad() == "cpp":
        from .native_backend import mesh_vorbereiten, native_laden
        return native_laden().wirkungslinie(
            kraft, moment, bezugspunkt, mesh_vorbereiten(punkte, dreiecke),
            R, float(toleranz))
    norm = math.sqrt(kraftquadrat)
    richtung = kraft / norm
    anker = bezugspunkt + np.cross(kraft, moment) / kraftquadrat
    weltpunkte = punkte @ R.T + bezugspunkt
    ecken = weltpunkte[dreiecke]
    e1 = ecken[:, 1] - ecken[:, 0]
    e2 = ecken[:, 2] - ecken[:, 0]
    pvec = np.cross(np.broadcast_to(richtung, e2.shape), e2)
    det = np.einsum("ij,ij->i", e1, pvec)
    gueltig = np.abs(det) > toleranz
    inv_det = np.zeros_like(det)
    inv_det[gueltig] = 1.0 / det[gueltig]
    tvec = anker - ecken[:, 0]
    u = np.einsum("ij,ij->i", tvec, pvec) * inv_det
    qvec = np.cross(tvec, e1)
    v = np.einsum("j,ij->i", richtung, qvec) * inv_det
    t = np.einsum("ij,ij->i", e2, qvec) * inv_det
    schnitt = (
        gueltig & (u >= -toleranz) & (v >= -toleranz)
        & (u + v <= 1.0 + toleranz))
    positionen = anker + t[:, None] * richtung
    schnitt &= positionen[:, 2] <= toleranz
    indices = np.flatnonzero(schnitt)
    punkt = None
    if len(indices):
        index = indices[int(np.argmin(np.abs(t[indices])))]
        punkt = positionen[index]
    return {
        "schnittpunkt": None if punkt is None else punkt.copy(),
        "anker": anker.copy(),
        "richtung": richtung.copy(),
    }
