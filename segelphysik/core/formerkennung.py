"""Geometrische Formerkennung am Dreiecksnetz (ohne Kenntnis des Formtyps).

Erkennt Kugel, Zylinder, Kegel und allgemeine Rotationskoerper. Grundlage sind
Oberflaechenpunkte (flaechengewichtet, deterministisch) im Volumenschwerpunkt:

* Kugel: alle Punkte haben (nahezu) denselben Abstand vom Schwerpunkt.
* Rotationskoerper um eine Achse: die Punkte der seitlichen Flaechen liegen im
  (z, rho)-Diagramm auf einer Kurve (rho = Abstand zur Achse). Ebene Deckel
  senkrecht zur Achse zaehlen nicht mit. Ein Quader erfuellt das nicht, auch
  wenn seine Traegheitsmomente gleich sind.
* Achsenkandidaten: Hauptachsen des Volumens und die flaechenstaerksten
  Flaechennormalen (noetig, wenn die Hauptmomente entartet sind).

Rueckgabe von klassifiziere(): "kugel", "zylinder", "kegel",
"rotationskoerper" oder "beliebig".
"""
from __future__ import annotations

import numpy as np

KUGEL = "kugel"
ZYLINDER = "zylinder"
KEGEL = "kegel"
ROTATIONSKOERPER = "rotationskoerper"
BELIEBIG = "beliebig"

_PUNKTE = 12000
_ZELLEN = 48
_KURVE_MAX_ZELLEN = 4.5          # Zellen je z-Spalte, die eine Kurve belegen darf
_KUGEL_TOL = 0.02


def _dreiecke_daten(punkte, dreiecke):
    p = np.asarray(punkte, float)
    f = np.asarray(dreiecke, np.int64)
    a, b, c = p[f[:, 0]], p[f[:, 1]], p[f[:, 2]]
    n = np.cross(b - a, c - a)
    flaeche = 0.5 * np.linalg.norm(n, axis=1)
    return a, b, c, n, flaeche


def _schwerpunkt_und_kovarianz(punkte, dreiecke):
    a, b, c, _, _ = _dreiecke_daten(punkte, dreiecke)
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    gesamt = vol.sum()
    if not np.isfinite(gesamt) or abs(gesamt) < 1e-18:
        return None
    s = a + b + c
    schwer = (s / 4.0 * vol[:, None]).sum(axis=0) / gesamt
    summe = (np.einsum("ni,nj->nij", a, a) + np.einsum("ni,nj->nij", b, b)
             + np.einsum("ni,nj->nij", c, c) + np.einsum("ni,nj->nij", s, s))
    moment = (summe * (vol / 20.0)[:, None, None]).sum(axis=0) / gesamt
    kov = moment - np.outer(schwer, schwer)
    return schwer, 0.5 * (kov + kov.T)


def _oberflaechenpunkte(a, b, c, flaeche, anzahl=_PUNKTE):
    gesamt = flaeche.sum()
    if gesamt <= 0:
        return np.empty((0, 3)), np.empty(0, np.int64)
    # deterministisch: gleichmaessige Quantile der kumulierten Flaeche
    kum = np.cumsum(flaeche) / gesamt
    q = (np.arange(anzahl) + 0.5) / anzahl
    idx = np.minimum(np.searchsorted(kum, q), len(flaeche) - 1)
    golden = 0.6180339887498949
    u = (np.arange(anzahl) * golden) % 1.0
    v = (np.arange(anzahl) * 0.7548776662466927) % 1.0
    flip = u + v > 1.0
    u[flip], v[flip] = 1.0 - u[flip], 1.0 - v[flip]
    pts = a[idx] + u[:, None] * (b[idx] - a[idx]) + v[:, None] * (c[idx] - a[idx])
    return pts, idx


def _achsenkandidaten(kov, n, flaeche):
    kandidaten = []
    _, vek = np.linalg.eigh(kov)
    kandidaten += [vek[:, i] for i in range(3)]
    laenge = np.linalg.norm(n, axis=1)
    ok = laenge > 0
    nn = np.zeros_like(n)
    nn[ok] = n[ok] / laenge[ok, None]
    # Normalen gleicher Richtung (Vorzeichen egal) gruppieren, Flaeche summieren
    vorz = np.where(np.abs(nn[:, 0]) > 1e-6, np.sign(nn[:, 0]),
                    np.where(np.abs(nn[:, 1]) > 1e-6, np.sign(nn[:, 1]),
                             np.sign(nn[:, 2])))
    nk = nn * vorz[:, None]
    gruppen = {}
    for schl, row, fl in zip(map(tuple, np.round(nk, 2)), nk, flaeche):
        g = gruppen.setdefault(schl, [np.zeros(3), 0.0])
        g[0] += row * fl
        g[1] += fl
    for vec, fl in sorted(gruppen.values(), key=lambda g: -g[1])[:4]:
        nv = np.linalg.norm(vec)
        if nv > 0:
            kandidaten.append(vec / nv)
    eindeutig = []
    for k in kandidaten:
        if not any(abs(float(k @ e)) > 0.9999 for e in eindeutig):
            eindeutig.append(k)
    return eindeutig


def _ist_kurve(z, rho, rmax, zmin, zmax):
    """True, wenn die (z, rho)-Punkte auf einer Kurve liegen (nicht flaechig)."""
    if len(z) < 50 or zmax - zmin <= 0 or rmax <= 0:
        return False
    iz = np.minimum(((z - zmin) / (zmax - zmin) * _ZELLEN).astype(int),
                    _ZELLEN - 1)
    ir = np.minimum((rho / rmax * _ZELLEN).astype(int), _ZELLEN - 1)
    belegt = np.zeros((_ZELLEN, _ZELLEN), bool)
    belegt[iz, ir] = True
    spalten = np.count_nonzero(belegt.any(axis=1))
    if spalten < _ZELLEN // 3:
        return False
    return belegt.sum() <= _KURVE_MAX_ZELLEN * spalten


def _profil_art(z, rho):
    """Unterart aus der Profilkurve: konstant -> Zylinder, linear -> Kegel."""
    rmax = rho.max()
    if np.ptp(rho) <= 0.04 * rmax:
        return ZYLINDER
    A = np.stack([z, np.ones_like(z)], axis=1)
    koef, *_ = np.linalg.lstsq(A, rho, rcond=None)
    if np.abs(A @ koef - rho).max() <= 0.04 * rmax:
        return KEGEL
    return ROTATIONSKOERPER


def klassifiziere(punkte, dreiecke):
    """Ordnet ein geschlossenes Dreiecksnetz einer Grundform zu."""
    try:
        a, b, c, n, flaeche = _dreiecke_daten(punkte, dreiecke)
        res = _schwerpunkt_und_kovarianz(punkte, dreiecke)
        if res is None or flaeche.sum() <= 0:
            return BELIEBIG
        schwer, kov = res
        pts, idx = _oberflaechenpunkte(a, b, c, flaeche)
        pts = pts - schwer
        abstand = np.linalg.norm(pts, axis=1)
        if abstand.max() > 0 and np.ptp(abstand) <= _KUGEL_TOL * abstand.max():
            return KUGEL
        laenge = np.linalg.norm(n[idx], axis=1)
        normalen = n[idx] / np.where(laenge > 0, laenge, 1.0)[:, None]
        for achse in _achsenkandidaten(kov, n, flaeche):
            z = pts @ achse
            rho = np.linalg.norm(pts - np.outer(z, achse), axis=1)
            seitlich = np.abs(normalen @ achse) < 0.999
            if seitlich.sum() < 200:
                continue
            zs, rs = z[seitlich], rho[seitlich]
            if _ist_kurve(zs, rs, rs.max(), z.min(), z.max()):
                return _profil_art(zs, rs)
        return BELIEBIG
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return BELIEBIG


def klassifiziere_koerper(koerper):
    """Grundform eines Koerpers; zusammengesetzte Koerper gelten als beliebig."""
    try:
        from .auftrieb import als_bindung
        blaetter = als_bindung(koerper).blatt_meshes
    except Exception:
        return BELIEBIG
    if len(blaetter) != 1:
        return BELIEBIG
    return klassifiziere(blaetter[0][0], blaetter[0][1])
