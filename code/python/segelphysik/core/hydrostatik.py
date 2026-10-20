"""Wasserlinien-Querschnittswerte aus orientierten Volumenmeshes."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .massen import validiere_mesh
from .rechenpfad import rechenpfad


class HydrostatikFehler(ValueError):
    """Fehler beim Bilden eines Wasserlinienquerschnitts."""


@dataclass(frozen=True)
class WasserlinienErgebnis:
    flaeche_m2: float
    schwerpunkt_m: np.ndarray
    flaechenkern_m4: np.ndarray


def _ringe_aus_mesh(punkte, dreiecke, ebene_z, toleranz):
    try:
        punkte, dreiecke, volumen, *_ = validiere_mesh(
            punkte, dreiecke, geschlossen_erforderlich=True)
    except ValueError as fehler:
        raise HydrostatikFehler(
            "Wasserlinienberechnung benötigt gültige geschlossene Volumenmeshes: "
            "%s" % fehler) from fehler
    if volumen < 0.0:
        dreiecke = dreiecke[:, [0, 2, 1]]

    if rechenpfad() == "cpp":
        from .native_backend import native_laden

        native = native_laden()
        try:
            return native.wasserlinien_ringe(
                native.Mesh(punkte, np.asarray(dreiecke, dtype=np.int64)),
                float(ebene_z), float(toleranz))
        except ValueError as fehler:
            raise HydrostatikFehler(str(fehler)) from fehler

    knoten = {}
    knoten_punkte = []
    segmente = {}

    def knoten_id(punkt):
        schluessel = tuple(np.rint(punkt / toleranz).astype(np.int64))
        if schluessel not in knoten:
            knoten[schluessel] = len(knoten_punkte)
            knoten_punkte.append(punkt.copy())
        return knoten[schluessel]

    for tri in dreiecke:
        ecken = punkte[tri]
        abstaende = ecken[:, 2] - ebene_z
        if np.all(np.abs(abstaende) <= toleranz):
            continue
        schnittpunkte = []
        for i in range(3):
            a, b = ecken[i], ecken[(i + 1) % 3]
            da, db = abstaende[i], abstaende[(i + 1) % 3]
            a_auf_ebene = abs(da) <= toleranz
            b_auf_ebene = abs(db) <= toleranz
            if a_auf_ebene:
                schnittpunkte.append(a.copy())
            elif b_auf_ebene:
                schnittpunkte.append(b.copy())
            elif (da < 0.0) != (db < 0.0):
                schnittpunkte.append(a + da / (da - db) * (b - a))

        eindeutige = {}
        for punkt in schnittpunkte:
            punkt[2] = ebene_z
            eindeutige[knoten_id(punkt)] = punkt
        if len(eindeutige) != 2:
            continue
        ids = tuple(eindeutige)
        p, q = (eindeutige[ids[0]], eindeutige[ids[1]])
        normale = np.cross(ecken[1] - ecken[0], ecken[2] - ecken[0])
        tangent = np.array((-normale[1], normale[0], 0.0))
        if np.dot(q - p, tangent) < 0.0:
            ids = (ids[1], ids[0])
        undirected = tuple(sorted(ids))
        segmente.setdefault(undirected, ids)

    ausgehend = {}
    eingehend = {}
    for start, ende in segmente.values():
        ausgehend.setdefault(start, []).append(ende)
        eingehend.setdefault(ende, []).append(start)
    if not segmente:
        return []
    if (any(len(ziel) != 1 for ziel in ausgehend.values())
            or any(len(start) != 1 for start in eingehend.values())
            or set(ausgehend) != set(eingehend)):
        raise HydrostatikFehler(
            "Wasserliniensegmente bilden keine eindeutigen geschlossenen Ringe")

    ringe = []
    benutzt = set()
    for anfang in ausgehend:
        if anfang in benutzt:
            continue
        ring = []
        aktuell = anfang
        while aktuell not in benutzt:
            benutzt.add(aktuell)
            ring.append(aktuell)
            aktuell = ausgehend[aktuell][0]
        if aktuell != anfang or len(ring) < 3:
            raise HydrostatikFehler("Offener oder entarteter Wasserlinienring")
        ringe.append(np.asarray([knoten_punkte[idx] for idx in ring]))
    return ringe


def _ringmomente(ring):
    if rechenpfad() == "cpp":
        from .native_backend import native_laden

        native = native_laden()
        ergebnis = native.ringmomente(native.Mesh(
            np.asarray(ring, dtype=np.float64).reshape(-1, 3),
            np.empty((0, 3), dtype=np.int64)))
        return None if ergebnis is None else tuple(ergebnis)
    xy = ring[:, :2]
    x, y = xy[:, 0], xy[:, 1]
    xn, yn = np.roll(x, -1), np.roll(y, -1)
    kreuz = x * yn - xn * y
    flaeche = 0.5 * float(kreuz.sum())
    if abs(flaeche) <= 1e-15:
        return None
    sx = float(np.sum((x + xn) * kreuz) / (6.0 * flaeche))
    sy = float(np.sum((y + yn) * kreuz) / (6.0 * flaeche))
    x2 = float(np.sum((x*x + x*xn + xn*xn) * kreuz) / 12.0)
    y2 = float(np.sum((y*y + y*yn + yn*yn) * kreuz) / 12.0)
    xy_moment = float(np.sum(
        (2*x*y + x*yn + xn*y + 2*xn*yn) * kreuz) / 24.0)
    return (flaeche, flaeche * sx, flaeche * sy,
            x2, y2, xy_moment)


def wasserlinien_querschnitt(blatt_meshes, ebene_z=0.0, toleranz=1e-9):
    """Liefert Fläche, Schwerpunkt und zentriertes Flächenträgheitstensor xy.

    Die Wasserfläche liegt in Welt-xy; Tensorreihenfolge ist (x, y), mit
    diagonalen Einträgen int(y² dA), int(x² dA) und symmetrischem Produkt.
    Getrennte Ringe werden orientierungstreu summiert, sodass Löcher abziehen.
    """
    try:
        ebene_z = float(ebene_z)
        toleranz = float(toleranz)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise HydrostatikFehler(
            "Schnittebene und Toleranz müssen endliche Zahlen sein") from fehler
    if (not np.isfinite(ebene_z) or not np.isfinite(toleranz)
            or toleranz <= 0.0):
        raise HydrostatikFehler(
            "Schnittebene muss endlich und Toleranz positiv sein")

    gesamt = np.zeros(6, dtype=np.float64)
    for punkte, dreiecke in blatt_meshes:
        punkte = np.asarray(punkte, dtype=np.float64)
        ringe = _ringe_aus_mesh(
            punkte, dreiecke, ebene_z, toleranz)
        for ring in ringe:
            momente = _ringmomente(ring)
            if momente is not None:
                gesamt += momente

    flaeche, moment_x, moment_y, x2, y2, xy = gesamt
    if flaeche <= 1e-15:
        return WasserlinienErgebnis(
            0.0, np.zeros(3), np.zeros((2, 2)))
    sx, sy = moment_x / flaeche, moment_y / flaeche
    schwerpunkt = np.array((sx, sy, ebene_z), dtype=np.float64)
    tensor = np.array([
        [y2 - flaeche * sy * sy, -(xy - flaeche * sx * sy)],
        [-(xy - flaeche * sx * sy), x2 - flaeche * sx * sx],
    ], dtype=np.float64)
    tensor = 0.5 * (tensor + tensor.T)
    if (not np.isfinite(flaeche) or not np.isfinite(schwerpunkt).all()
            or not np.isfinite(tensor).all()):
        raise HydrostatikFehler(
            "Wasserlinienquerschnitt ergab nicht-endliche Kennwerte")
    return WasserlinienErgebnis(float(flaeche), schwerpunkt, tensor)


def wasserlinien_bei_pose(blatt_meshes, z, phi, toleranz=1e-9):
    """Berechnet den Wasserlinienquerschnitt lokaler Meshes bei Pose (z, phi)."""
    try:
        z, phi = float(z), float(phi)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise HydrostatikFehler(
            "Pose muss endliche Zahlen enthalten") from fehler
    if not np.isfinite(z) or not np.isfinite(phi):
        raise HydrostatikFehler("Pose muss endliche Zahlen enthalten")
    c, s = np.cos(phi), np.sin(phi)
    rotation = np.array([
        [1.0, 0.0, 0.0],
        [0.0, c, -s],
        [0.0, s, c],
    ])
    mesh_welt = [
        (np.asarray(punkte, dtype=np.float64) @ rotation.T
         + np.array((0.0, 0.0, z)), dreiecke)
        for punkte, dreiecke in blatt_meshes
    ]
    return wasserlinien_querschnitt(mesh_welt, toleranz=toleranz)
