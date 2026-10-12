"""Wasser-Schnitt V3: exakte Zerlegung eines beliebigen Dreiecks-Meshes
an der Ebene z = ebene_z (Default Wasseroberflaeche z = 0).

Der Koerper wird "virtuell" in zwei Koerper geteilt (unter/oberhalb der
Wasserlinie); beide Teil-Meshes sind geschlossen und werden in der Demo
einfarbig eingefaerbt. Die Wasserlinie wird als Gesamtheit der Randkanten
der Teil-Meshes auf Schnitthoehe extrahiert - vollstaendig auch bei
Kanten komplett IN der Ebene (z. B. gekippte Quader).

Rein numpy-basiert -> deterministisch, versionsunabhaengig, unit-testbar.
"""
from __future__ import annotations
import numpy as np

EPS = 1e-12


def _clip_polygon(polygon, ebene_z, oberhalb):
    """Sutherland-Hodgman: Polygon gegen Halbraum schneiden.
    Aufeinanderfolgende Duplikate werden entfernt (keine entarteten Dreiecke)."""
    if len(polygon) == 0:
        return []
    def wert(p):
        return p[2] - ebene_z
    roh = []
    n = len(polygon)
    for i in range(n):
        aktuell = polygon[i]
        naechster = polygon[(i + 1) % n]
        da, dn = wert(aktuell), wert(naechster)
        innen_a = (da >= 0) if oberhalb else (da <= 0)
        innen_n = (dn >= 0) if oberhalb else (dn <= 0)
        if innen_a:
            roh.append(aktuell)
        if innen_a != innen_n:
            t = da / (da - dn) if abs(da - dn) > EPS else 0.0
            roh.append(aktuell + t * (naechster - aktuell))
    ergebnis = []
    for p in roh:
        if not ergebnis or np.linalg.norm(p - ergebnis[-1]) > EPS:
            ergebnis.append(p)
    if len(ergebnis) >= 2 and np.linalg.norm(ergebnis[0] - ergebnis[-1]) <= EPS:
        ergebnis.pop()
    return ergebnis


def _fan_triangulieren(polygon):
    return [(polygon[0], polygon[i], polygon[i + 1])
            for i in range(1, len(polygon) - 1)]


def wasserlinie_aus_teilmesh(punkte, dreiecke, ebene_z=0.0, tol=1e-9):
    """Randkanten eines Teil-Meshes, die vollstaendig auf Schnitthoehe liegen."""
    P = np.asarray(punkte, dtype=float)
    T = np.asarray(dreiecke, dtype=np.int64)
    if len(T) == 0:
        return np.zeros((0, 3))
    E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    E.sort(axis=1)
    uniq, counts = np.unique(E, axis=0, return_counts=True)
    rand = uniq[counts == 1]
    if len(rand) == 0:
        return np.zeros((0, 3))
    auf_hoehe = ((np.abs(P[rand[:, 0], 2] - ebene_z) <= tol)
                 & (np.abs(P[rand[:, 1], 2] - ebene_z) <= tol))
    rand = rand[auf_hoehe]
    if len(rand) == 0:
        return np.zeros((0, 3))
    return np.concatenate([P[rand[:, 0]][:, None, :],
                           P[rand[:, 1]][:, None, :]], axis=1).reshape(-1, 3)


def schneide_am_wasser(punkte, gesichter, ebene_z=0.0, mit_deckel=False):
    """Zerschneidet ein Dreiecks-Mesh an der Ebene z = ebene_z.

    Rueckgabe: (unten_punkte, unten_dreiecke, oben_punkte, oben_dreiecke, kontur)
        kontur : (2s,3) Wasserlinien-Segmentendpunkte (Paare)"""
    P = np.asarray(punkte, dtype=float)
    F = np.asarray(gesichter, dtype=np.int64)

    unten_pts, unten_tris = [], []
    oben_pts, oben_tris = [], []

    def register(liste, punkt):
        liste.append(punkt)
        return len(liste) - 1

    for tri in F:
        eck = [P[tri[0]], P[tri[1]], P[tri[2]]]
        dz = [p[2] - ebene_z for p in eck]
        alle_oben = all(d > 0 or abs(d) <= EPS for d in dz)
        alle_unten = all(d < 0 or abs(d) <= EPS for d in dz)
        if alle_oben:
            for poly in _fan_triangulieren(eck):
                idx = [register(oben_pts, p) for p in poly]
                oben_tris.append(idx)
            continue
        if alle_unten:
            for poly in _fan_triangulieren(eck):
                idx = [register(unten_pts, p) for p in poly]
                unten_tris.append(idx)
            continue
        poly_unten = _clip_polygon(eck, ebene_z, oberhalb=False)
        poly_oben = _clip_polygon(eck, ebene_z, oberhalb=True)
        for poly, pts, tris in ((poly_unten, unten_pts, unten_tris),
                                (poly_oben, oben_pts, oben_tris)):
            if len(poly) >= 3:
                for dtri in _fan_triangulieren(poly):
                    idx = [register(pts, p) for p in dtri]
                    tris.append(idx)

    unten_p = np.asarray(unten_pts, dtype=float).reshape(-1, 3)
    oben_p = np.asarray(oben_pts, dtype=float).reshape(-1, 3)
    unten_t = np.asarray(unten_tris, dtype=np.int64).reshape(-1, 3)
    oben_t = np.asarray(oben_tris, dtype=np.int64).reshape(-1, 3)

    kontur = [wasserlinie_aus_teilmesh(unten_p, unten_t, ebene_z),
              wasserlinie_aus_teilmesh(oben_p, oben_t, ebene_z)]
    kontur_p = (np.vstack([k for k in kontur if len(k)])
                if any(len(k) for k in kontur) else np.zeros((0, 3)))
    if mit_deckel:
        unten_p, unten_t = _deckel_setzen(unten_p, unten_t, ebene_z,
                                          teil_oben=False)
        oben_p, oben_t = _deckel_setzen(oben_p, oben_t, ebene_z,
                                        teil_oben=True)
    return unten_p, unten_t, oben_p, oben_t, kontur_p


def mesh_volumen(punkte, dreiecke):
    """Signiertes Volumen eines geschlossenen Dreiecks-Meshes (Divergenzsatz)."""
    P = np.asarray(punkte, dtype=float)
    T = np.asarray(dreiecke, dtype=np.int64)
    if len(T) == 0:
        return 0.0
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    return float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6.0)


def einzigartige_konturpunkte(kontur, tol=1e-9):
    if len(kontur) == 0:
        return np.zeros((0, 3))
    gerundet = np.round(kontur / tol).astype(np.int64)
    _, idx = np.unique(gerundet, axis=0, return_index=True)
    return kontur[np.sort(idx)]


def polygonzug_der_kontur(kontur, tol=1e-9):
    """Ordnet Konturpunkte zu einem geschlossenen Polygonzug (konvexe Wasserlinie)."""
    punkte = einzigartige_konturpunkte(kontur, tol)
    if len(punkte) < 3:
        return punkte
    zentrum = punkte.mean(axis=0)
    ebenen_punkte = punkte[:, :2] - zentrum[:2]
    winkel = np.arctan2(ebenen_punkte[:, 1], ebenen_punkte[:, 0])
    sortiert = punkte[np.argsort(winkel)]
    behalten = [sortiert[0]]
    for i in range(1, len(sortiert)):
        v1 = sortiert[i] - behalten[-1]
        v2 = sortiert[(i + 1) % len(sortiert)] - sortiert[i]
        n1, n2 = np.linalg.norm(v1[:2]), np.linalg.norm(v2[:2])
        # Quick-Win: np.cross auf 2D-Vektoren ist seit NumPy 2.0 deprecated.
        # |norm(cross(v1,v2))| ist fuer 2D analytisch identisch mit
        # |v1x*v2y - v1y*v2x| -> direkt berechnet (10000 Zufallspaare: diff 0.0).
        if abs(v1[0] * v2[1] - v1[1] * v2[0]) > 1e-9 * max(n1, n2, 1.0):
            behalten.append(sortiert[i])
    return np.asarray(behalten)


# ---------------- Deckel (Schritt 4.1, gegen SSAO-Flackern) ----------------
# Der Wasserschnitt hinterlaesst OFFENE Teil-Meshes. Screen-Space-AO (SSAO)
# erzeugt an dieser Tiefenkante einen Saum, der mit der Kamera flackert.
# Abhilfe: Die Schnittflaeche wird mit einem Deckel aus Dreiecken geschlossen
# (Fan um das Ringzentrum, Normale nach aussen: unten +z, oben -z).
# Ringe ineinander (Loch im Ring, z.B. Hohlprofil): nur der AEUSSERE Ring
# wird gefaechert - der Fan deckt das Innere mit ab. Ein eigener Fan im
# Innenring haette die Gegen-Normale und wuerde gerade das Z-Fighting
# erzeugen, das hier beseitigt werden soll.

DECKEL_TOL = 1e-7


def _ketten(segmente, tol=DECKEL_TOL):
    """Verkettet Kantenpaare zu geschlossenen Ringen (Reihenfolge beliebig)."""
    seg = np.asarray(segmente, dtype=float)
    if seg.size == 0:
        return []
    seg = seg.reshape(-1, 2, 3)
    q = np.round(seg / tol).astype(np.int64)
    abgang = {}
    for i in range(len(seg)):
        abgang.setdefault(tuple(q[i, 0]), []).append(i)
    benutzt = [False] * len(seg)
    ringe = []
    for i0 in range(len(seg)):
        if benutzt[i0]:
            continue
        benutzt[i0] = True
        punkte = [seg[i0, 0], seg[i0, 1]]
        ziel = tuple(q[i0, 1])
        start = tuple(q[i0, 0])
        schritte = 0
        while ziel != start and schritte <= len(seg):
            naechster = None
            for j in abgang.get(ziel, ()):
                if not benutzt[j]:
                    naechster = j
                    break
            if naechster is None:
                break
            benutzt[naechster] = True
            punkte.append(seg[naechster, 1])
            ziel = tuple(q[naechster, 1])
            schritte += 1
        if ziel == start and len(punkte) >= 4:
            ringe.append(np.array(punkte[:-1]))
    return ringe


def _ring_flaeche_xy(ring):
    """Signierte Flaeche in der Ebene z=const (positiv = gegen Uhrzeigersinn
    von +z aus gesehen)."""
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def _punkt_in_ring(p, ring):
    """Punkt-in-Polygon (Ray Casting) in der xy-Ebene."""
    x, y = float(p[0]), float(p[1])
    rx, ry = ring[:, 0], ring[:, 1]
    drinnen = False
    n = len(ring)
    for i in range(n):
        x1, y1 = rx[i], ry[i]
        x2, y2 = rx[(i + 1) % n], ry[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xs = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xs:
                drinnen = not drinnen
    return drinnen


def _deckel_setzen(punkte, dreiecke, ebene_z, teil_oben):
    """Schliesst die Schnittkante an z=ebene_z mit Deckeldreiecken.
    teil_oben=True  -> Teil-Mesh liegt oberhalb, Deckelnormale nach unten (-z).
    teil_oben=False -> Teil-Mesh liegt unterhalb, Deckelnormale nach oben (+z).
    Rueckgabe: neue Punkte- und Dreiecks-Arrays (Original bleibt unangetastet)."""
    P = np.asarray(punkte, dtype=float).reshape(-1, 3)
    T = np.asarray(dreiecke, dtype=np.int64).reshape(-1, 3)
    if len(T) == 0:
        return P, T
    rand = wasserlinie_aus_teilmesh(P, T, ebene_z)
    if len(rand) == 0:
        return P, T
    ringe = _ketten(rand)
    # Aeussere Ringe zuerst; Ringe innerhalb eines groesseren Rings sind
    # Locher und werden vom aeusseren Fan mit abgedeckt (kein eigener Fan).
    ringe.sort(key=lambda r: -abs(_ring_flaeche_xy(r)))
    aeussere = []
    for ring in ringe:
        zentrum = ring.mean(axis=0)
        if any(_punkt_in_ring(zentrum, a) for a in aeussere):
            continue
        aeussere.append(ring)
    if not aeussere:
        return P, T
    teile_p = [P]
    teile_t = [T]
    basis = len(P)
    for ring in aeussere:
        n = len(ring)
        flaeche = _ring_flaeche_xy(ring)
        if abs(flaeche) < 1e-14:
            continue
        if (flaeche > 0.0) == bool(teil_oben):
            ring = ring[::-1]
        c = ring.mean(axis=0)
        c[2] = ebene_z
        idx = basis + np.arange(n + 1)
        tri = np.column_stack([np.full(n, idx[n]),
                               idx[:n],
                               np.roll(idx[:n], -1)])
        teile_p.append(np.vstack([ring, c[None, :]]))
        teile_t.append(tri)
        basis += n + 1
    if len(teile_p) == 1:
        return P, T
    return np.vstack(teile_p), np.vstack(teile_t).astype(np.int64)
