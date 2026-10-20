"""Deterministische Anzeigegrößen für die Navigationswidgets."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from .rechenpfad import nativer_kern, rechenpfad


_EPSILON = 1e-10


@dataclass(frozen=True)
class Navigationswerte:
    heading_grad: float | None
    kraengung_grad: float | None
    stampfen_grad: float | None
    kamera_azimut_grad: float | None
    kamera_stampfen_grad: float | None
    kamera_kraengung_grad: float | None
    segelwinkel_rad: float | None = None


@nativer_kern("winkel_360", skalare=(0,))
def winkel_360(winkel_rad):
    return float(winkel_rad % (2.0 * math.pi))


@nativer_kern("wrap_180", skalare=(0,))
def wrap_180(winkel_rad):
    return float((winkel_rad + math.pi) % (2.0 * math.pi) - math.pi)


def _endlicher_winkel(wert):
    if wert is None or isinstance(wert, bool):
        return None
    try:
        wert = float(wert)
    except (TypeError, ValueError, OverflowError):
        return None
    return wert if math.isfinite(wert) else None


def navigationswerte_ableiten(
        quaternion, kamera_offset_rad=None, kamera_elevation_rad=None,
        segelwinkel_rad=None):
    """Leitet alle Widgetwerte aus einer einzigen wxyz-Quaternion ab."""
    from .dynamik_6dof import quaternion_matrix

    try:
        rotation = quaternion_matrix(quaternion)
    except (TypeError, ValueError, OverflowError):
        rotation = None

    if rechenpfad() == "cpp":
        from .native_backend import native_laden

        return Navigationswerte(*native_laden().navigationswerte(
            rotation, _endlicher_winkel(kamera_offset_rad),
            _endlicher_winkel(kamera_elevation_rad), _endlicher_winkel(segelwinkel_rad)))

    heading = kraengung = stampfen = None
    if rotation is not None and np.isfinite(rotation).all():
        bug = rotation[:, 0]
        horizont_betrag = math.hypot(float(bug[0]), float(bug[1]))
        if horizont_betrag > _EPSILON:
            heading = math.atan2(-float(bug[1]), float(bug[0])) % (
                2.0 * math.pi)
        stampfen = math.atan2(float(bug[2]), horizont_betrag)
        if horizont_betrag > _EPSILON:
            kraengung = math.atan2(
                -float(rotation[2, 1]), float(rotation[2, 2]))

    offset = _endlicher_winkel(kamera_offset_rad)
    elevation = _endlicher_winkel(kamera_elevation_rad)
    azimut = kamera_stampfen = kamera_kraengung = None
    if (heading is not None and offset is not None and elevation is not None
            and 0.0 <= elevation < math.pi / 2.0):
        azimut = winkel_360(heading + offset)
        kamera = np.array((
            math.cos(elevation) * math.cos(azimut),
            -math.cos(elevation) * math.sin(azimut),
            math.sin(elevation),
        ))
        bug_h = np.array((math.cos(heading), -math.sin(heading), 0.0))
        steuerbord_h = np.cross(bug_h, np.array((0.0, 0.0, 1.0)))
        pitch_x = float(np.dot(kamera, bug_h))
        roll_x = float(np.dot(kamera, steuerbord_h))
        if math.hypot(pitch_x, float(kamera[2])) > _EPSILON:
            kamera_stampfen = math.atan2(float(kamera[2]), pitch_x)
        if math.hypot(roll_x, float(kamera[2])) > _EPSILON:
            kamera_kraengung = math.atan2(float(kamera[2]), roll_x)

    segelwinkel = _endlicher_winkel(segelwinkel_rad)
    return Navigationswerte(
        heading_grad=(None if heading is None else math.degrees(heading)),
        kraengung_grad=(
            None if kraengung is None else math.degrees(kraengung)),
        stampfen_grad=(
            None if stampfen is None else math.degrees(stampfen)),
        kamera_azimut_grad=(
            None if azimut is None else math.degrees(azimut)),
        kamera_stampfen_grad=(
            None if kamera_stampfen is None
            else math.degrees(kamera_stampfen)),
        kamera_kraengung_grad=(
            None if kamera_kraengung is None
            else math.degrees(kamera_kraengung)),
        segelwinkel_rad=segelwinkel,
    )


RICHTUNGEN_16 = (
    "N", "NNO", "NO", "ONO", "O", "OSO", "SO", "SSO",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
)


def richtung_16(heading_grad):
    """Liefert den nächstliegenden 16-Punkt-Kompassstrich."""
    heading = _endlicher_winkel(heading_grad)
    if heading is None:
        return None
    if rechenpfad() == "cpp":
        from .native_backend import native_laden

        return RICHTUNGEN_16[native_laden().richtungssektor(heading)]
    sektor = int(math.floor((heading % 360.0 + 11.25) / 22.5)) % 16
    return RICHTUNGEN_16[sektor]
