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
from .core.rechenpfad import rechenpfad

EPS = 1e-12


def _native_mesh(punkte, dreiecke=None):
    from .core.native_backend import mesh_vorbereiten

    if dreiecke is None:
        dreiecke = np.empty((0, 3), dtype=np.int64)
    return mesh_vorbereiten(
        np.asarray(punkte, dtype=np.float64).reshape(-1, 3),
        np.asarray(dreiecke, dtype=np.int64).reshape(-1, 3))


def _clip_polygon(polygon, ebene_z, oberhalb):
    """Sutherland-Hodgman: Polygon gegen Halbraum schneiden.
    Aufeinanderfolgende Duplikate werden entfernt (keine entarteten Dreiecke)."""
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return list(native_laden().clip_polygon(
            _native_mesh(polygon), float(ebene_z), bool(oberhalb)))
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


def _schnittkontur_berechnen(punkte, gesichter, abstand, ebene_z):
    """Liefert Schnittsegmente direkt aus den durchstochenen Dreiecken."""
    schnitt = np.any(abstand < 0.0, axis=1) & np.any(abstand > 0.0, axis=1)
    if not schnitt.any():
        return np.zeros((0, 3))
    dreiecke = np.asarray(punkte, dtype=float)[
        np.asarray(gesichter, dtype=np.int64)[schnitt]]
    dz = abstand[schnitt]
    segmente = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        kreuzt = ((dz[:, a] < 0.0) & (dz[:, b] > 0.0)
                  | (dz[:, a] > 0.0) & (dz[:, b] < 0.0))
        start = dreiecke[:, a]
        delta = dreiecke[:, b] - start
        t = np.divide(
            -dz[:, a], dz[:, b] - dz[:, a],
            out=np.zeros_like(dz[:, a]), where=kreuzt)
        schnittpunkte = start + t[:, None] * delta
        schnittpunkte[:, 2] = ebene_z
        segmente.append((schnittpunkte, kreuzt))
    kandidaten = np.stack([punkte for punkte, _maske in segmente], axis=1)
    maske = np.stack([maske for _punkte, maske in segmente], axis=1)
    return kandidaten[maske].reshape(-1, 3)


def wasserlinie_aus_teilmesh(punkte, dreiecke, ebene_z=0.0, tol=1e-9):
    """Randkanten eines Teil-Meshes, die vollstaendig auf Schnitthoehe liegen."""
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().wasserlinie(
            _native_mesh(punkte, dreiecke), float(ebene_z), float(tol))
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
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        native = native_laden()
        return native.wasserschnitt(
            _native_mesh(punkte, gesichter), float(ebene_z),
            bool(mit_deckel), native.Abbruch())
    P = np.asarray(punkte, dtype=float)
    F = np.asarray(gesichter, dtype=np.int64)
    abstand = P[F, 2] - ebene_z
    alle_oben = np.all(abstand >= -EPS, axis=1)
    alle_unten = ~alle_oben & np.all(abstand <= EPS, axis=1)
    geschnitten = np.flatnonzero(~alle_oben & ~alle_unten)

    def vollstaendige_teile(maske):
        flaechen = F[maske]
        if len(flaechen) == 0:
            return (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64))
        teile_punkte = P[flaechen].reshape(-1, 3)
        teile_dreiecke = np.arange(
            len(teile_punkte), dtype=np.int64).reshape(-1, 3)
        return teile_punkte, teile_dreiecke

    unten_p_teile, unten_t_teile = [], []
    oben_p_teile, oben_t_teile = [], []
    unten_p, unten_t = vollstaendige_teile(alle_unten)
    oben_p, oben_t = vollstaendige_teile(alle_oben)
    if len(unten_p):
        unten_p_teile.append(unten_p)
        unten_t_teile.append(unten_t)
    if len(oben_p):
        oben_p_teile.append(oben_p)
        oben_t_teile.append(oben_t)

    def geschnittene_teile(ebene, oberhalb, punkte_teile, dreiecke_teile):
        offset = sum(len(teil) for teil in punkte_teile)
        if not len(geschnitten):
            return
        dreiecke = P[F[geschnitten]]
        dz = abstand[geschnitten]
        innerhalb = dz >= 0.0 if oberhalb else dz <= 0.0
        anzahl_innerhalb = np.count_nonzero(innerhalb, axis=1)
        nenner = dz - np.roll(dz, -1, axis=1)
        t = np.divide(
            dz, nenner, out=np.zeros_like(dz),
            where=np.abs(nenner) > EPS)
        schnittpunkte = (
            dreiecke + t[:, :, None]
            * (np.roll(dreiecke, -1, axis=1) - dreiecke))
        schnittpunkte[:, :, 2] = ebene
        erzeugt = []
        for index in range(3):
            einzeln = (anzahl_innerhalb == 1) & innerhalb[:, index]
            if einzeln.any():
                vorher = (index - 1) % 3
                erzeugt.append(np.stack((
                    dreiecke[einzeln, index],
                    schnittpunkte[einzeln, index],
                    schnittpunkte[einzeln, vorher]), axis=1))

            ausserhalb = (anzahl_innerhalb == 2) & ~innerhalb[:, index]
            if ausserhalb.any():
                start = (index + 1) % 3
                ende = (index + 2) % 3
                a = np.stack((
                    dreiecke[ausserhalb, start],
                    dreiecke[ausserhalb, ende],
                    schnittpunkte[ausserhalb, ende]), axis=1)
                b = np.stack((
                    dreiecke[ausserhalb, start],
                    schnittpunkte[ausserhalb, ende],
                    schnittpunkte[ausserhalb, index]), axis=1)
                erzeugt.extend((a, b))
        if not erzeugt:
            return
        dreiecke_punkte = np.concatenate(erzeugt, axis=0)
        kanten = np.roll(dreiecke_punkte, -1, axis=1) - dreiecke_punkte
        nicht_entartet = np.all(
            np.linalg.norm(kanten, axis=2) > EPS, axis=1)
        dreiecke_punkte = dreiecke_punkte[nicht_entartet]
        if not len(dreiecke_punkte):
            return
        dreiecke_punkte = dreiecke_punkte.reshape(-1, 3)
        indices = np.arange(
            offset, offset + len(dreiecke_punkte),
            dtype=np.int64).reshape(-1, 3)
        punkte_teile.append(dreiecke_punkte)
        dreiecke_teile.append(indices)

    geschnittene_teile(
        ebene_z, False, unten_p_teile, unten_t_teile)
    geschnittene_teile(
        ebene_z, True, oben_p_teile, oben_t_teile)

    def zusammenfuehren(punkte_teile, dreiecke_teile):
        if not punkte_teile:
            return (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64))
        return np.concatenate(punkte_teile), np.concatenate(dreiecke_teile)

    unten_p, unten_t = zusammenfuehren(unten_p_teile, unten_t_teile)
    oben_p, oben_t = zusammenfuehren(oben_p_teile, oben_t_teile)

    direkte_kontur = not np.any(np.abs(abstand) <= EPS)
    if direkte_kontur:
        kontur_p = _schnittkontur_berechnen(P, F, abstand, ebene_z)
    else:
        kontur = [wasserlinie_aus_teilmesh(unten_p, unten_t, ebene_z),
                  wasserlinie_aus_teilmesh(oben_p, oben_t, ebene_z)]
        kontur_p = (np.vstack([k for k in kontur if len(k)])
                    if any(len(k) for k in kontur) else np.zeros((0, 3)))
    if mit_deckel:
        unten_p, unten_t = _deckel_setzen(unten_p, unten_t, ebene_z,
                                          teil_oben=False,
                                          rand=kontur_p if direkte_kontur
                                          else None)
        oben_p, oben_t = _deckel_setzen(oben_p, oben_t, ebene_z,
                                        teil_oben=True,
                                        rand=kontur_p if direkte_kontur
                                        else None)
    return unten_p, unten_t, oben_p, oben_t, kontur_p


def mesh_volumen(punkte, dreiecke):
    """Signiertes Volumen eines geschlossenen Dreiecks-Meshes (Divergenzsatz)."""
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().mesh_volumen(_native_mesh(punkte, dreiecke))
    P = np.asarray(punkte, dtype=float)
    T = np.asarray(dreiecke, dtype=np.int64)
    if len(T) == 0:
        return 0.0
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    return float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6.0)


def einzigartige_konturpunkte(kontur, tol=1e-9):
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().einzigartige_konturpunkte(
            _native_mesh(kontur), float(tol))
    if len(kontur) == 0:
        return np.zeros((0, 3))
    gerundet = np.round(kontur / tol).astype(np.int64)
    _, idx = np.unique(gerundet, axis=0, return_index=True)
    return kontur[np.sort(idx)]


def polygonzug_der_kontur(kontur, tol=1e-9):
    """Ordnet Konturpunkte zu einem geschlossenen Polygonzug (konvexe Wasserlinie)."""
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().polygonzug(_native_mesh(kontur), float(tol))
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
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().konturketten(_native_mesh(segmente), float(tol))
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
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().ringflaeche(_native_mesh(ring))
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def _punkt_in_ring(p, ring):
    """Punkt-in-Polygon (Ray Casting) in der xy-Ebene."""
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().punkt_in_ring(
            np.array([p[0], p[1], 0.], dtype=np.float64), _native_mesh(ring))
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


def _deckel_setzen(punkte, dreiecke, ebene_z, teil_oben, rand=None):
    """Schliesst die Schnittkante an z=ebene_z mit Deckeldreiecken.
    teil_oben=True  -> Teil-Mesh liegt oberhalb, Deckelnormale nach unten (-z).
    teil_oben=False -> Teil-Mesh liegt unterhalb, Deckelnormale nach oben (+z).
    Rueckgabe: neue Punkte- und Dreiecks-Arrays (Original bleibt unangetastet)."""
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden

        return native_laden().deckel_setzen(
            _native_mesh(punkte, dreiecke), float(ebene_z), bool(teil_oben),
            None if rand is None else _native_mesh(rand))
    P = np.asarray(punkte, dtype=float).reshape(-1, 3)
    T = np.asarray(dreiecke, dtype=np.int64).reshape(-1, 3)
    if len(T) == 0:
        return P, T
    if rand is None:
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
