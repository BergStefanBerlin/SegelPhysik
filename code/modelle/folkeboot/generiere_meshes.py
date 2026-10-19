"""Erzeugt die dokumentierte Geometrienäherung für das Folkeboot."""
from __future__ import annotations

import math
from pathlib import Path


PAKET = Path(__file__).resolve().parent


def _obj_schreiben(dateiname, punkte, flaechen):
    pfad = PAKET / dateiname
    with pfad.open("w", encoding="ascii", newline="\n") as datei:
        datei.write("# Geschaetzte Geometrie; siehe NAEHERUNG.md\n")
        for x, y, z in punkte:
            datei.write(f"v {y:.7f} {z:.7f} {x:.7f}\n")
        for flaeche in flaechen:
            datei.write("f " + " ".join(str(i + 1) for i in flaeche) + "\n")


def _hull():
    laenge = 7.68
    stationen = (
        (-0.500, 0.025, 0.05, 0.08),
        (-0.450, 0.200, -0.04, 0.20),
        (-0.360, 0.440, -0.31, 0.34),
        (-0.250, 0.735, -0.40, 0.37),
        (-0.125, 0.945, -0.45, 0.39),
        ( 0.000, 1.075, -0.47, 0.41),
        ( 0.125, 1.100, -0.46, 0.43),
        ( 0.250, 1.035, -0.42, 0.46),
        ( 0.360, 0.845, -0.34, 0.50),
        ( 0.450, 0.535, 0.23, 0.55),
        ( 0.500, 0.025, 0.57, 0.62),
    )
    seitenpunkte = 17
    punkte = []
    for anteil, halbe_breite, kiel_z, sheer_z in stationen:
        x = anteil * laenge
        punkte.append((x, halbe_breite, sheer_z))
        for index in range(1, 9):
            anteil_seite = 1.0 - index / 8.0
            y = halbe_breite * anteil_seite
            z = kiel_z + (sheer_z - kiel_z) * anteil_seite ** 0.62
            punkte.append((x, y, z))
        for index in range(1, 9):
            anteil_seite = index / 8.0
            y = -halbe_breite * anteil_seite
            z = kiel_z + (sheer_z - kiel_z) * anteil_seite ** 0.62
            punkte.append((x, y, z))

    flaechen = []
    for station in range(len(stationen) - 1):
        for index in range(seitenpunkte):
            a = station * seitenpunkte + index
            b = station * seitenpunkte + (index + 1) % seitenpunkte
            c = (station + 1) * seitenpunkte + (index + 1) % seitenpunkte
            d = (station + 1) * seitenpunkte + index
            flaechen.extend(((a, b, c), (a, c, d)))

    heck_index = len(punkte)
    punkte.append((stationen[0][0] * laenge, 0.0,
                   (stationen[0][2] + stationen[0][3]) / 2.0))
    bug_index = len(punkte)
    punkte.append((stationen[-1][0] * laenge, 0.0,
                   (stationen[-1][2] + stationen[-1][3]) / 2.0))
    for index in range(seitenpunkte):
        naechster = (index + 1) % seitenpunkte
        flaechen.append((heck_index, naechster, index))
        letzter = (len(stationen) - 1) * seitenpunkte
        flaechen.append((bug_index, letzter + index, letzter + naechster))
    _obj_schreiben("rumpf.obj", punkte, flaechen)


def _extrusion(dateiname, polygon_xz, halbe_breite):
    punkte = (
        [(x, -halbe_breite, z) for x, z in polygon_xz]
        + [(x, halbe_breite, z) for x, z in polygon_xz]
    )
    n = len(polygon_xz)
    flaechen = []
    for index in range(1, n - 1):
        flaechen.extend(((0, index + 1, index), (n, n + index, n + index + 1)))
    for index in range(n):
        naechster = (index + 1) % n
        flaechen.extend(
            ((index, naechster, n + naechster),
             (index, n + naechster, n + index))
        )
    _obj_schreiben(dateiname, punkte, flaechen)


def _mast():
    mast_x = 0.45
    querschnitt = 12
    punkte = []
    for z, radius_x, radius_y in ((0.38, 0.055, 0.045), (10.55, 0.04, 0.035)):
        for index in range(querschnitt):
            winkel = 2.0 * math.pi * index / querschnitt
            punkte.append((
                mast_x + radius_x * math.cos(winkel),
                radius_y * math.sin(winkel),
                z,
            ))
    flaechen = []
    for index in range(querschnitt):
        naechster = (index + 1) % querschnitt
        flaechen.extend(
            ((index, naechster, querschnitt + naechster),
             (index, querschnitt + naechster, querschnitt + index))
        )
    flaechen.extend(
        (0, index + 1, index) for index in range(1, querschnitt - 1))
    flaechen.extend(
        (querschnitt, querschnitt + index, querschnitt + index + 1)
        for index in range(1, querschnitt - 1)
    )
    _obj_schreiben("mast.obj", punkte, flaechen)


def main():
    _hull()
    _extrusion(
        "kiel.obj",
        [(-0.42, -0.32), (0.42, -0.32), (0.32, -0.75),
         (0.17, -1.20), (-0.20, -1.20), (-0.36, -0.83)],
        0.08,
    )
    _extrusion(
        "ruder.obj",
        [(-3.74, -0.16), (-3.30, -0.20), (-3.43, -0.81),
         (-3.68, -0.87), (-3.82, -0.56)],
        0.035,
    )
    _mast()
    _extrusion(
        "grossbaum.obj",
        [(-2.92, 0.74), (0.45, 0.74), (0.45, 0.80), (-2.92, 0.80)],
        0.035,
    )
    _extrusion(
        "grosssegel.obj",
        [(0.40, 0.78), (-2.82, 0.78), (-0.10, 9.80), (0.40, 10.20)],
        0.004,
    )
    _extrusion(
        "fock.obj",
        [(1.80, 0.78), (3.46, 0.68), (0.52, 9.92)],
        0.004,
    )


if __name__ == "__main__":
    main()
