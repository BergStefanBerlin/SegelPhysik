"""Exakte Volumen- und Schwerpunktberechnung für Mesh-Vereinigungen."""
from __future__ import annotations

import numpy as np

from .massen import validiere_mesh


class VolumenUnionFehler(ValueError):
    """Ungültige Eingabe oder fehlgeschlagene Mesh-Vereinigung."""


def _manifolds_aus_meshes(blatt_meshes):
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
    return m3d, solide


def _volumen_schwerpunkt_aus_soliden(solide, ebene_z=None):
    import manifold3d as m3d

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
    return _volumen_schwerpunkt_aus_union(union, ebene_z)


def _volumen_schwerpunkt_aus_union(union, ebene_z=None,
                                   ebene_normale=None, ebene_offset=None):
    import manifold3d as m3d

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
        ebene_normale = (0.0, 0.0, -1.0)
        ebene_offset = -ebene_z
    if ebene_normale is not None:
        normale = np.asarray(ebene_normale, dtype=np.float64)
        try:
            ebene_offset = float(ebene_offset)
        except (TypeError, ValueError, OverflowError) as fehler:
            raise VolumenUnionFehler(
                "Ebenenoffset muss eine endliche Zahl sein") from fehler
        laenge = float(np.linalg.norm(normale))
        if (normale.shape != (3,) or not np.isfinite(normale).all()
                or not np.isfinite(ebene_offset) or laenge <= 0.0):
            raise VolumenUnionFehler(
                "Ebene benötigt eine endliche, nicht-null Normale und Offset")
        normale = normale / laenge
        ebene_offset /= laenge
        union = union.trim_by_plane(normale.tolist(), ebene_offset)
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


class VorbereitetesUnionModell:
    """Vereint starre Teilmeshes einmalig und wertet Posen wiederholt aus."""

    def __init__(self, blatt_meshes):
        m3d, solide = _manifolds_aus_meshes(blatt_meshes)
        if not solide:
            self._union = None
            return
        try:
            union = m3d.Manifold.batch_boolean(solide, m3d.OpType.Add)
        except (ValueError, RuntimeError) as fehler:
            raise VolumenUnionFehler(
                "Boolesche Volumen-Union ist fehlgeschlagen: %s"
                % fehler) from fehler
        if union.status() != m3d.Error.NoError:
            raise VolumenUnionFehler(
                "Boolesche Volumen-Union lieferte ungültigen Status: %s"
                % union.status())
        self._union = union
        self._gesamt = _volumen_schwerpunkt_aus_union(union)

    def auswerten(self, transform=None, ebene_z=None):
        if self._union is None:
            return 0.0, np.zeros(3, dtype=np.float64)
        union = self._union
        if transform is not None:
            matrix = np.asarray(transform, dtype=np.float64)
            if matrix.shape != (3, 4) or not np.isfinite(matrix).all():
                raise VolumenUnionFehler(
                    "Pose muss eine endliche affine 3x4-Matrix sein")
            try:
                union = union.transform(matrix.tolist())
            except (TypeError, ValueError, RuntimeError) as fehler:
                raise VolumenUnionFehler(
                    "Union-Pose konnte nicht angewendet werden: %s"
                    % fehler) from fehler
        return _volumen_schwerpunkt_aus_union(union, ebene_z)

    def auswerten_ebene(self, normale, offset):
        """Schneidet im vorbereiteten Frame; Manifold behält normale·x >= offset."""
        if self._union is None:
            return 0.0, np.zeros(3, dtype=np.float64)
        return _volumen_schwerpunkt_aus_union(
            self._union, ebene_normale=normale, ebene_offset=offset)

    def gesamtwerte(self):
        """Liefert unveränderte Union-Gesamtwerte (Volumen, Schwerpunkt)."""
        if self._union is None:
            return 0.0, np.zeros(3, dtype=np.float64)
        volumen, schwerpunkt = self._gesamt
        return volumen, schwerpunkt.copy()


def volumen_schwerpunkt_union(blatt_meshes, ebene_z=None):
    """Gibt Volumen und Schwerpunkt einer Mesh-Union zurück.

    Wenn `ebene_z` angegeben ist, wird nur der Bereich unterhalb dieser
    horizontalen Ebene integriert; Manifold3D schließt dabei die Schnittfläche.
    """
    _m3d, solide = _manifolds_aus_meshes(blatt_meshes)
    return _volumen_schwerpunkt_aus_soliden(solide, ebene_z)
