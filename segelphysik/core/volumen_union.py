"""Exakte Volumen- und Schwerpunktberechnung für Mesh-Vereinigungen."""
from __future__ import annotations

import numpy as np

from .massen import validiere_mesh


class VolumenUnionFehler(ValueError):
    """Ungültige Eingabe oder fehlgeschlagene Mesh-Vereinigung."""


def volumen_schwerpunkt_union(blatt_meshes, ebene_z=None):
    """Gibt Volumen und Schwerpunkt einer Mesh-Union zurück.

    Wenn `ebene_z` angegeben ist, wird nur der Bereich unterhalb dieser
    horizontalen Ebene integriert; Manifold3D schließt dabei die Schnittfläche.
    """
    try:
        import manifold3d as m3d
    except ImportError as fehler:
        raise VolumenUnionFehler(
            "Manifold3D wird für die exakte Volumen-Union benötigt") from fehler

    solide = []
    for index, (punkte, dreiecke) in enumerate(blatt_meshes):
        try:
            punkte, dreiecke, volumen, *_ = validiere_mesh(
                punkte, dreiecke, geschlossen_erforderlich=True)
            if volumen < 0.0:
                dreiecke = dreiecke[:, [0, 2, 1]]
            mesh = m3d.Mesh64(
                np.array(punkte, dtype=np.float64, order="C", copy=True),
                np.array(dreiecke, dtype=np.uint64, order="C", copy=True))
            teil = m3d.Manifold(mesh)
        except (TypeError, ValueError, OverflowError) as fehler:
            raise VolumenUnionFehler(
                "Volumenmesh %d ist ungültig: %s" % (index, fehler)) from fehler
        if teil.status() != m3d.Error.NoError:
            raise VolumenUnionFehler(
                "Manifold3D hat Volumenmesh %d zurückgewiesen: %s"
                % (index, teil.status()))
        solide.append(teil)

    if not solide:
        return 0.0, np.zeros(3, dtype=np.float64)
    try:
        union = m3d.Manifold.batch_boolean(solide, m3d.OpType.Add)
    except (ValueError, RuntimeError) as fehler:
        raise VolumenUnionFehler(
            "Boolesche Volumen-Union ist fehlgeschlagen: %s" % fehler) from fehler
    if union.status() != m3d.Error.NoError:
        raise VolumenUnionFehler(
            "Boolesche Volumen-Union lieferte ungültigen Status: %s"
            % union.status())
    if union.is_empty() or union.volume() <= 1e-15:
        return 0.0, np.zeros(3, dtype=np.float64)
    if ebene_z is not None:
        try:
            ebene_z = float(ebene_z)
        except (TypeError, ValueError, OverflowError) as fehler:
            raise VolumenUnionFehler(
                "Schnittebene muss eine endliche Zahl sein") from fehler
        if not np.isfinite(ebene_z):
            raise VolumenUnionFehler(
                "Schnittebene muss eine endliche Zahl sein")
        union = union.trim_by_plane((0.0, 0.0, -1.0), -ebene_z)
        if union.status() != m3d.Error.NoError:
            raise VolumenUnionFehler(
                "Ebene hat ein ungültiges Union-Ergebnis erzeugt: %s"
                % union.status())
        if union.is_empty() or union.volume() <= 1e-15:
            return 0.0, np.zeros(3, dtype=np.float64)

    mesh = union.to_mesh64()
    punkte = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    dreiecke = np.asarray(mesh.tri_verts, dtype=np.int64)
    try:
        punkte, dreiecke, signiertes_volumen, *_ = validiere_mesh(
            punkte, dreiecke, geschlossen_erforderlich=True)
    except ValueError as fehler:
        raise VolumenUnionFehler(
            "Union-Ergebnis ist kein geschlossenes Volumenmesh: %s"
            % fehler) from fehler
    if signiertes_volumen < 0.0:
        dreiecke = dreiecke[:, [0, 2, 1]]

    a, b, c = (punkte[dreiecke[:, i]] for i in range(3))
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    volumen = float(vol6.sum() / 6.0)
    if not np.isfinite(volumen) or volumen <= 1e-15:
        raise VolumenUnionFehler(
            "Union-Ergebnis hat kein positives endliches Volumen")
    schwerpunkt = (vol6[:, None] * (a + b + c)).sum(axis=0) / (
        24.0 * volumen)
    if not np.isfinite(schwerpunkt).all():
        raise VolumenUnionFehler(
            "Union-Schwerpunkt ist nicht endlich")
    return volumen, schwerpunkt
