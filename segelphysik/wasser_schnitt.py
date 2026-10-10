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
    auf_hoehe = (np.abs(P[rand[:, 0], 2] - ebene_z) <= tol) &                 (np.abs(P[rand[:, 1], 2] - ebene_z) <= tol)
    rand = rand[auf_hoehe]
    if len(rand) == 0:
        return np.zeros((0, 3))
    return np.concatenate([P[rand[:, 0]][:, None, :],
                           P[rand[:, 1]][:, None, :]], axis=1).reshape(-1, 3)


def schneide_am_wasser(punkte, gesichter, ebene_z=0.0):
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
    kontur_p = np.vstack([k for k in kontur if len(k)])         if any(len(k) for k in kontur) else np.zeros((0, 3))
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
        if np.linalg.norm(np.cross(v1[:2], v2[:2])) > 1e-9 * max(n1, n2, 1.0):
            behalten.append(sortiert[i])
    return np.asarray(behalten)
