# ============================================================
# arrows.py - Zeichen-Helfer (Pfeile, Clipping, Wasserlinie)
# ============================================================
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def _pfeil_polys(p0, richtung, laenge, w):
    """Pfeil als Polygone (Schaft-Prisma + Pyramidenspitze), damit er in der
    gleichen tiefensortierten Sammlung wie Koerper und Wasser liegt und
    korrekt verdeckt wird."""
    p0 = np.asarray(p0, float)
    d = np.asarray(richtung, float)
    d = d / np.linalg.norm(d)
    ref = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(d, ref); u /= np.linalg.norm(u)
    v = np.cross(d, u)

    def q(along, a, b):
        return p0 + d * along + u * a * w + v * b * w

    ls = 0.74 * laenge          # Schaftlaenge
    wh = 1.75 * w               # Spitzenradius
    c0 = [q(0, -1, -1), q(0, 1, -1), q(0, 1, 1), q(0, -1, 1)]
    c1 = [q(ls, -1, -1), q(ls, 1, -1), q(ls, 1, 1), q(ls, -1, 1)]
    polys = []
    for i in range(4):
        j = (i + 1) % 4
        polys.append(np.array([c0[i], c0[j], c1[j], c1[i]]))
    hb = [q(ls, -wh, -wh), q(ls, wh, -wh), q(ls, wh, wh), q(ls, -wh, wh)]
    tip = p0 + d * laenge
    for i in range(4):
        j = (i + 1) % 4
        polys.append(np.array([hb[i], hb[j], tip]))
    return polys


class _Vorne(Poly3DCollection):
    """Poly3DCollection, die immer im Vordergrund gezeichnet wird
    (do_3d_projection liefert maximalen Projektionswert -> zuletzt gemalt)."""
    def do_3d_projection(self):
        try:
            super().do_3d_projection()
        except Exception:
            pass
        return 1e9


def _clip_z(poly, unten):
    """Clippt ein Polygon (Nx3) an der Ebene z=0 (Sutherland-Hodgman).
    unten=True  -> behaelt den Teil mit z<=0 (nass),
    unten=False -> behaelt den Teil mit z>=0 (trocken)."""
    res = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ain = (a[2] <= 0) if unten else (a[2] >= 0)
        bin_ = (b[2] <= 0) if unten else (b[2] >= 0)
        if ain:
            res.append(a)
        if ain != bin_:
            t = a[2] / (a[2] - b[2])
            res.append(a + t * (b - a))
    return np.array(res) if len(res) >= 3 else None


def _wasserlinie(W, Ecken_idx):
    """Schnittpolygon des rotierten Koerpers mit der Ebene z=0 (Weltkoord.).
    W: Eckpunkte im Weltkoordinatensystem (8x3)."""
    punkte = []
    for a, b in Ecken_idx:
        za, zb = W[a, 2], W[b, 2]
        if (za < 0.0) != (zb < 0.0):
            t = za / (za - zb)
            punkte.append(W[a] + t * (W[b] - W[a]))
    if len(punkte) < 3:
        return None
    P = np.array(punkte)
    c = P.mean(axis=0)
    ang = np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0])
    return P[np.argsort(ang)]
