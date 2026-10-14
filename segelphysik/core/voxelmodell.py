"""Deterministisches, körperfestes CPU-Referenzraster für verdrängtes Volumen."""
from __future__ import annotations

import numpy as np

from .massen import validiere_mesh


class VoxelmodellFehler(ValueError):
    """Ungültige Geometrie oder Rasterparameter."""


def _positiv(wert, name):
    try:
        wert = float(wert)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise VoxelmodellFehler(
            "%s muss endlich und positiv sein" % name) from fehler
    if not np.isfinite(wert) or wert <= 0.0:
        raise VoxelmodellFehler("%s muss endlich und positiv sein" % name)
    return wert


def _intervalle_saeule(punkte, dreiecke, x, z):
    p0 = punkte[dreiecke[:, 0]]
    p1 = punkte[dreiecke[:, 1]]
    p2 = punkte[dreiecke[:, 2]]
    d = ((p1[:, 0] - p0[:, 0]) * (p2[:, 2] - p0[:, 2])
         - (p2[:, 0] - p0[:, 0]) * (p1[:, 2] - p0[:, 2]))
    gueltig = np.abs(d) >= 1e-15
    if not gueltig.any():
        return ()
    n1 = ((x - p0[:, 0]) * (p2[:, 2] - p0[:, 2])
          - (p2[:, 0] - p0[:, 0]) * (z - p0[:, 2]))
    n2 = ((p1[:, 0] - p0[:, 0]) * (z - p0[:, 2])
          - (x - p0[:, 0]) * (p1[:, 2] - p0[:, 2]))
    w1 = np.divide(n1, d, out=np.zeros_like(d), where=gueltig)
    w2 = np.divide(n2, d, out=np.zeros_like(d), where=gueltig)
    innerhalb = (gueltig & (w1 >= -1e-12) & (w2 >= -1e-12)
                 & (w1 + w2 <= 1.0 + 1e-12))
    if not innerhalb.any():
        return ()
    schnitte = (p0[innerhalb, 1]
                + w1[innerhalb] * (p1[innerhalb, 1] - p0[innerhalb, 1])
                + w2[innerhalb] * (p2[innerhalb, 1] - p0[innerhalb, 1]))
    schnitte.sort()
    gedichtet = [float(schnitte[0])]
    for schnitt in schnitte[1:]:
        if schnitt - gedichtet[-1] > 1e-9:
            gedichtet.append(float(schnitt))
    while len(gedichtet) % 2:
        if len(gedichtet) < 4:
            return ()
        gedichtet = gedichtet[1:-1]
    return tuple(zip(gedichtet[::2], gedichtet[1::2]))


class KoerperfestesVoxelmodell:
    """Unveränderliches Voxelzentrumraster; Poseänderungen schneiden nur eine Ebene."""

    def __init__(self, blatt_meshes, aufloesung):
        self.aufloesung = _positiv(aufloesung, "Auflösung")
        blaetter = []
        for punkte, dreiecke in blatt_meshes:
            try:
                p, f, _, _, geschlossen, _ = validiere_mesh(
                    punkte, dreiecke, geschlossen_erforderlich=True)
            except ValueError as fehler:
                raise VoxelmodellFehler(
                    "Raster benötigt gültige geschlossene Volumenmeshes: %s"
                    % fehler) from fehler
            if not geschlossen:
                raise VoxelmodellFehler(
                    "Raster benötigt geschlossene Volumenmeshes")
            blaetter.append((p, f))
        if not blaetter:
            raise VoxelmodellFehler("Mindestens ein Volumenmesh ist erforderlich")

        lo = np.min([p.min(axis=0) for p, _ in blaetter], axis=0)
        hi = np.max([p.max(axis=0) for p, _ in blaetter], axis=0)
        h = self.aufloesung

        def zentren(untergrenze, obergrenze):
            k0 = int(np.ceil(untergrenze / h - 0.5))
            k1 = int(np.floor(obergrenze / h - 0.5))
            return (np.arange(k0, k1 + 1, dtype=np.int64) + 0.5) * h

        xs, ys, zs = (zentren(lo[i], hi[i]) for i in range(3))
        spalten = []
        for x in xs:
            for z in zs:
                innen = np.zeros(len(ys), dtype=bool)
                for punkte, dreiecke in blaetter:
                    for unten, oben in _intervalle_saeule(
                            punkte, dreiecke, x, z):
                        innen |= (ys > unten) & (ys < oben)
                if innen.any():
                    spalten.append(np.column_stack((
                        np.full(np.count_nonzero(innen), x),
                        ys[innen],
                        np.full(np.count_nonzero(innen), z))))
        zentren_lokal = (
            np.vstack(spalten) if spalten
            else np.empty((0, 3), dtype=np.float64))
        zentren_lokal.setflags(write=False)
        self.zentren_lokal = zentren_lokal

    def auswerten(self, z, phi):
        """Gibt (Volumen, Schwerpunkt_world) unter der Wasserfläche z_world=0."""
        try:
            z, phi = float(z), float(phi)
        except (TypeError, ValueError, OverflowError) as fehler:
            raise VoxelmodellFehler("Pose muss endliche Zahlen enthalten") from fehler
        if not np.isfinite(z) or not np.isfinite(phi):
            raise VoxelmodellFehler("Pose muss endliche Zahlen enthalten")
        if len(self.zentren_lokal) == 0:
            return 0.0, np.zeros(3)
        c, s = np.cos(phi), np.sin(phi)
        punkte = self.zentren_lokal
        z_welt = z + s * punkte[:, 1] + c * punkte[:, 2]
        nass = z_welt <= 0.0
        anzahl = int(np.count_nonzero(nass))
        if not anzahl:
            return 0.0, np.zeros(3)
        tauchzentrum_lokal = punkte[nass].mean(axis=0)
        tauchzentrum_welt = tauchzentrum_lokal @ np.array(
            [[1.0, 0.0, 0.0],
             [0.0, c, -s],
             [0.0, s, c]]).T
        tauchzentrum_welt[2] += z
        volumen = anzahl * self.aufloesung ** 3
        if not np.isfinite(volumen) or not np.isfinite(tauchzentrum_welt).all():
            raise VoxelmodellFehler("Rasterauswertung ergab nicht-endliche Werte")
        return float(volumen), tauchzentrum_welt
