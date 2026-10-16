"""Unveränderliche Posen und zentrale Frame-Transformationen."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .dynamik_6dof import (
    quaternion_aus_matrix,
    quaternion_matrix,
    quaternion_normalisieren,
)


@dataclass(frozen=True, slots=True)
class Pose:
    """Transformation ``T_ziel<-quelle`` mit Metern und Quaternion wxyz."""

    ziel_frame: str
    quell_frame: str
    translation_m: tuple[float, float, float]
    rotation_quaternion_wxyz: tuple[float, float, float, float]

    def __post_init__(self):
        if not isinstance(self.ziel_frame, str) or not self.ziel_frame:
            raise ValueError("Ziel-Frame muss ein nichtleerer Name sein")
        if not isinstance(self.quell_frame, str) or not self.quell_frame:
            raise ValueError("Quell-Frame muss ein nichtleerer Name sein")
        translation = np.asarray(self.translation_m, dtype=np.float64)
        if translation.shape != (3,) or not np.isfinite(translation).all():
            raise ValueError("Pose-Translation muss drei endliche Werte enthalten")
        try:
            quaternion = tuple(float(w) for w in quaternion_normalisieren(
                self.rotation_quaternion_wxyz))
        except (TypeError, ValueError, OverflowError) as fehler:
            raise ValueError("Pose-Quaternion ist ungültig: %s" % fehler) \
                from fehler
        object.__setattr__(
            self, "translation_m", tuple(float(w) for w in translation))
        object.__setattr__(self, "rotation_quaternion_wxyz", quaternion)

    @property
    def rotationsmatrix(self):
        return quaternion_matrix(self.rotation_quaternion_wxyz)

    def punkt_transformieren(self, punkt):
        vektor = np.asarray(punkt, dtype=np.float64)
        if vektor.shape != (3,) or not np.isfinite(vektor).all():
            raise ValueError("Punkt muss drei endliche Werte enthalten")
        return self.rotationsmatrix @ vektor + self.translation_m

    def vektor_transformieren(self, vektor):
        array = np.asarray(vektor, dtype=np.float64)
        if array.shape != (3,) or not np.isfinite(array).all():
            raise ValueError("Vektor muss drei endliche Werte enthalten")
        return self.rotationsmatrix @ array

    def punkte_transformieren(self, punkte):
        array = np.asarray(punkte, dtype=np.float64)
        if (array.ndim != 2 or array.shape[1] != 3
                or not np.isfinite(array).all()):
            raise ValueError("Punkte müssen ein endliches Nx3-Array sein")
        return array @ self.rotationsmatrix.T + self.translation_m

    def invers(self):
        rotation = self.rotationsmatrix.T
        translation = -(rotation @ np.asarray(self.translation_m))
        return Pose(
            self.quell_frame,
            self.ziel_frame,
            tuple(float(w) for w in translation),
            quaternion_aus_matrix(rotation),
        )

    def komponieren(self, innen: Pose):
        """Komponiert ``T_A<-B`` mit ``T_B<-C`` zu ``T_A<-C``."""
        if not isinstance(innen, Pose):
            raise TypeError("Komposition erwartet eine Pose")
        if self.quell_frame != innen.ziel_frame:
            raise ValueError(
                "Pose-Frames passen nicht: %s != %s"
                % (self.quell_frame, innen.ziel_frame))
        rotation = self.rotationsmatrix @ innen.rotationsmatrix
        translation = (
            self.rotationsmatrix @ np.asarray(innen.translation_m)
            + np.asarray(self.translation_m))
        return Pose(
            self.ziel_frame,
            innen.quell_frame,
            tuple(float(w) for w in translation),
            quaternion_aus_matrix(rotation),
        )


def pose_aus_modellpose(pose, ziel_frame, quell_frame):
    """Erzeugt eine benannte Pose aus der unveränderlichen Manifestpose."""
    if pose is None:
        return Pose(ziel_frame, quell_frame, (0.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0))
    return Pose(
        ziel_frame,
        quell_frame,
        pose.translation_m,
        pose.rotation_quaternion_wxyz,
    )


def rotationsmatrix_achsenwinkel(achse, winkel_rad):
    achse = np.asarray(achse, dtype=np.float64)
    winkel = float(winkel_rad)
    if (achse.shape != (3,) or not np.isfinite(achse).all()
            or not np.isfinite(winkel)):
        raise ValueError("Gelenkachse und Winkel müssen endlich sein")
    norm = float(np.linalg.norm(achse))
    if norm <= 1e-12:
        raise ValueError("Gelenkachse darf nicht null sein")
    x, y, z = achse / norm
    c, s = np.cos(winkel), np.sin(winkel)
    t = 1.0 - c
    return np.array([
        [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
        [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
        [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
    ])


def pose_mit_gelenkwinkel(pose, gelenk, winkel_rad=None):
    """Faltet die Rotation um die Elternframe-Achse in eine lokale Pose."""
    basis = pose_aus_modellpose(pose, "eltern", "knoten")
    if gelenk is None:
        return basis
    winkel = gelenk.winkel_rad if winkel_rad is None else winkel_rad
    rotation = (
        rotationsmatrix_achsenwinkel(gelenk.achse_eltern, winkel)
        @ basis.rotationsmatrix)
    return Pose(
        basis.ziel_frame,
        basis.quell_frame,
        basis.translation_m,
        quaternion_aus_matrix(rotation),
    )
