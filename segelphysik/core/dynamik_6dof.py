"""Deterministischer Newton-Euler-Schritt mit sechs Freiheitsgraden."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class Zustand6DOF:
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    quaternion: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    geschwindigkeit_koerper: tuple[float, float, float] = (0.0, 0.0, 0.0)
    winkelgeschwindigkeit_koerper: tuple[float, float, float] = (
        0.0, 0.0, 0.0)


def _vektor(werte, name, laenge):
    try:
        ergebnis = np.asarray(werte, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("%s muss aus %d Zahlen bestehen"
                         % (name, laenge)) from fehler
    if ergebnis.shape != (laenge,) or not np.isfinite(ergebnis).all():
        raise ValueError("%s muss %d endliche Zahlen enthalten"
                         % (name, laenge))
    return ergebnis


def quaternion_normalisieren(quaternion):
    q = _vektor(quaternion, "Quaternion", 4)
    norm = float(np.linalg.norm(q))
    if norm <= np.finfo(np.float64).tiny:
        raise ValueError("Quaternion darf nicht die Nullrotation sein")
    return q / norm


def quaternion_matrix(quaternion):
    w, x, y, z = quaternion_normalisieren(quaternion)
    return np.array([
        [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w),
         2.0 * (x * z + y * w)],
        [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z),
         2.0 * (y * z - x * w)],
        [2.0 * (x * z - y * w), 2.0 * (y * z + x * w),
         1.0 - 2.0 * (x * x + y * y)],
    ])


def quaternion_slerp(anfang, ende, anteil):
    q0 = quaternion_normalisieren(anfang)
    q1 = quaternion_normalisieren(ende)
    anteil = float(anteil)
    if not math.isfinite(anteil):
        raise ValueError("Interpolationsanteil muss endlich sein")
    anteil = min(1.0, max(0.0, anteil))
    punkt = float(np.dot(q0, q1))
    if punkt < 0.0:
        q1 = -q1
        punkt = -punkt
    if punkt > 0.9995:
        return quaternion_normalisieren(q0 + anteil * (q1 - q0))
    winkel = math.acos(min(1.0, max(-1.0, punkt)))
    sinus = math.sin(winkel)
    return (math.sin((1.0 - anteil) * winkel) / sinus * q0
            + math.sin(anteil * winkel) / sinus * q1)


def _quaternion_multiplizieren(q, p):
    w, x, y, z = q
    a, b, c, d = p
    return np.array([
        w * a - x * b - y * c - z * d,
        w * b + x * a + y * d - z * c,
        w * c - x * d + y * a + z * b,
        w * d + x * c - y * b + z * a,
    ])


def _orientierung_schritt(q, omega_koerper, dt):
    betrag = float(np.linalg.norm(omega_koerper))
    winkel = betrag * dt
    if betrag <= 1e-15:
        delta = np.array((1.0, 0.0, 0.0, 0.0))
    else:
        halber = 0.5 * winkel
        delta = np.concatenate((
            (math.cos(halber),),
            omega_koerper * (math.sin(halber) / betrag)))
    return quaternion_normalisieren(_quaternion_multiplizieren(q, delta))


def schritt(zustand, kraftfunktion, masse, traegheit_koerper, dt, g):
    """Integriert genau einen festen SI-Schritt im Koerperkoordinatensystem.

    Position, Kraefte und Momente sind in Weltkoordinaten. Geschwindigkeiten,
    Winkelgeschwindigkeiten und der Traegheitstensor sind koerperfest.
    """
    position = _vektor(zustand.position, "Position", 3)
    q = quaternion_normalisieren(zustand.quaternion)
    v = _vektor(
        zustand.geschwindigkeit_koerper, "Koerpergeschwindigkeit", 3)
    omega = _vektor(
        zustand.winkelgeschwindigkeit_koerper, "Koerper-Winkelgeschwindigkeit",
        3)
    masse, dt, g = float(masse), float(dt), float(g)
    if not all(math.isfinite(wert) for wert in (masse, dt, g)) \
            or masse <= 0.0 or dt <= 0.0 or g <= 0.0:
        raise ValueError("Masse, Zeitschritt und g muessen endlich positiv sein")
    inertia = np.asarray(traegheit_koerper, dtype=np.float64)
    if inertia.shape != (3, 3) or not np.isfinite(inertia).all():
        raise ValueError("Traegheitstensor muss eine endliche 3x3-Matrix sein")
    if not np.allclose(inertia, inertia.T, rtol=0.0, atol=1e-10):
        raise ValueError("Traegheitstensor muss symmetrisch sein")
    if float(np.linalg.eigvalsh(inertia)[0]) <= 0.0:
        raise ValueError("Traegheitstensor muss positiv definit sein")

    rotation = quaternion_matrix(q)
    ergebnis = kraftfunktion(
        (position, q), v=rotation @ v, omega=rotation @ omega)
    kraft = np.asarray(
        getattr(ergebnis, "F_gesamt", ergebnis.F_A).as_array(),
        dtype=np.float64)
    moment = np.asarray(
        getattr(ergebnis, "M_gesamt", ergebnis.M).as_array(),
        dtype=np.float64)
    if (kraft.shape != (3,) or moment.shape != (3,)
            or not np.isfinite(kraft).all()
            or not np.isfinite(moment).all()):
        raise ValueError("Kraftmodell lieferte nicht-endliche 3D-Kraefte")

    added = np.asarray(
        getattr(ergebnis, "added_mass_diagonal", (0.0,) * 6),
        dtype=np.float64)
    if (added.shape != (6,) or not np.isfinite(added).all()
            or np.any(added < 0.0)):
        raise ValueError("Added Mass muss sechs endliche nicht-negative "
                         "Werte enthalten")
    mass_translation = np.diag(np.full(3, masse) + added[:3])
    mass_rotation = inertia + np.diag(added[3:])

    gravity_welt = np.array((0.0, 0.0, -masse * g))
    kraft_koerper = rotation.T @ (kraft + gravity_welt)
    moment_koerper = rotation.T @ moment
    a = np.linalg.solve(
        mass_translation,
        kraft_koerper - np.cross(omega, mass_translation @ v))
    alpha = np.linalg.solve(
        mass_rotation,
        moment_koerper - np.cross(omega, mass_rotation @ omega))
    v_neu = v + a * dt
    omega_neu = omega + alpha * dt
    q_neu = _orientierung_schritt(q, omega_neu, dt)
    rotation_neu = quaternion_matrix(q_neu)
    position_neu = position + rotation_neu @ v_neu * dt

    if hasattr(ergebnis, "mit_beschleunigung"):
        acceleration_welt = np.concatenate((
            rotation @ a, rotation @ alpha))
        ergebnis = ergebnis.mit_beschleunigung(
            acceleration_welt, rotation=rotation)
    return Zustand6DOF(
        tuple(position_neu), tuple(q_neu), tuple(v_neu), tuple(omega_neu),
    ), ergebnis
