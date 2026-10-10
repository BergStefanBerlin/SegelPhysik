"""SegelPhysik V3 - Koerper-Formen (rein geometrische Fabrik) (SPEC_V3.md Abschnitt 3).

KEINE Physik: keine Dichte, keine Masse, keine Kraefte. Geschlossene
Dreiecks-Meshes (vertices, faces) im KOERPERFRAME; Ursprung im geometrischen
Schwerpunkt (Kegel/Pyramide: H/4 ueber der Basis).

V4-Schnittstelle: spaetere Physik (Volumen-/Schwerpunktintegration,
Ebenen-Clip fuer V_sub) konsumiert diese Meshes als Consumer, ohne sie zu
veraendern. Altbestand core/bodies.py dient nur als Referenz, nicht als
Importquelle.
"""
from __future__ import annotations
import numpy as np

__all__ = ["build_cone", "build_box", "build_pyramid"]


def _close(vertices, faces):
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)
    assert f.min() >= 0 and f.max() < len(v)
    return v, f


def build_cone(H=2.0, R=1.0, nseg=64):
    """Kegel, Achse = Koerper-z, Spitze oben; Basis z=-H/4, Spitze z=+3H/4.

    Hinweis: Die Basis ist ein regulaeres n-Eck (n = nseg). Das Mesh-Volumen
    weicht daher vom Kreiskegel um den Faktor (n/(2*pi))*sin(2*pi/n) ab
    (bei n=64: -0.16 %); mit steigendem nseg konvergiert es quadratisch.
    """
    if H <= 0 or R <= 0 or nseg < 3:
        raise ValueError("H>0, R>0, nseg>=3 erforderlich")
    zb, zt = -H / 4.0, 3.0 * H / 4.0
    ang = 2.0 * np.pi * np.arange(nseg) / nseg
    ring = np.stack([R*np.cos(ang), R*np.sin(ang), np.full(nseg, zb)], axis=1)
    v = np.vstack([ring, [[0.0, 0.0, zt]], [[0.0, 0.0, zb]]])
    i = np.arange(nseg); j = (i + 1) % nseg
    side = np.stack([i, j, np.full(nseg, nseg)], axis=1)      # nach aussen orientiert
    base = np.stack([np.full(nseg, nseg+1), j, i], axis=1)    # nach unten orientiert
    return _close(v, np.vstack([side, base]))


def build_box(dx=2.0, dy=2.0, dz=2.0):
    """Quader dx*dy*dz, zentriert im Ursprung (= Schwerpunkt)."""
    if min(dx, dy, dz) <= 0:
        raise ValueError("dx, dy, dz > 0 erforderlich")
    hx, hy, hz = dx/2.0, dy/2.0, dz/2.0
    v = np.array([[-hx,-hy,-hz],[hx,-hy,-hz],[hx,hy,-hz],[-hx,hy,-hz],
                  [-hx,-hy,hz],[hx,-hy,hz],[hx,hy,hz],[-hx,hy,hz]])
    quads = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(3,0,4,7)]
    f = []
    for a,b,c,d in quads:
        f += [[a,b,c],[a,c,d]]
    return _close(v, f)


def build_pyramid(a=2.0, H=2.0):
    """Quadratische Pyramide Basis a*a, Hoehe H; Basis z=-H/4, Spitze z=+3H/4."""
    if a <= 0 or H <= 0:
        raise ValueError("a>0, H>0 erforderlich")
    h = a/2.0; zb, zt = -H/4.0, 3.0*H/4.0
    v = np.array([[-h,-h,zb],[h,-h,zb],[h,h,zb],[-h,h,zb],[0.0,0.0,zt]])
    f = [[0,1,4],[1,2,4],[2,3,4],[3,0,4],[0,3,2],[0,2,1]]
    return _close(v, f)


# --- deutsche Alias-Namen (sprechende API) ---
bau_kegel = build_cone
bau_quader = build_box
bau_pyramide = build_pyramid
