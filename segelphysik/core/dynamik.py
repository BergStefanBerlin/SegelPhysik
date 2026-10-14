"""Fester SI-Zeitschritt fuer Tauchbewegung und Kraengung."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class Bewegungszustand:
    z: float = 0.0
    phi: float = 0.0
    v_z: float = 0.0
    omega_x: float = 0.0


def schritt(zustand, kraftfunktion, masse, traegheit_xx, dt, g,
            daempfung_tauchung=0.0, daempfung_kraengung=0.0):
    """Fuehrt genau einen semi-impliziten Schritt aus."""
    neuer_zustand, _ = schritt_mit_kraeften(
        zustand, kraftfunktion, masse, traegheit_xx, dt, g,
        daempfung_tauchung, daempfung_kraengung)
    return neuer_zustand


def schritt_mit_kraeften(zustand, kraftfunktion, masse, traegheit_xx, dt, g,
                         daempfung_tauchung=0.0, daempfung_kraengung=0.0):
    """Fuehrt einen Schritt aus und gibt die dabei ausgewerteten Kraefte mit."""
    werte = (masse, traegheit_xx, dt, g,
             daempfung_tauchung, daempfung_kraengung,
             zustand.z, zustand.phi, zustand.v_z, zustand.omega_x)
    if not all(math.isfinite(float(wert)) for wert in werte):
        raise ValueError("Dynamikparameter und Zustand muessen endlich sein.")
    if masse <= 0.0 or traegheit_xx <= 0.0 or dt <= 0.0 or g <= 0.0:
        raise ValueError("Masse, Traegheit, Zeitschritt und g muessen positiv sein.")
    if daempfung_tauchung < 0.0 or daempfung_kraengung < 0.0:
        raise ValueError("Daempfungswerte duerfen nicht negativ sein.")

    ergebnis = kraftfunktion(
        (zustand.z, zustand.phi, 0.0),
        v=(0.0, 0.0, zustand.v_z),
        omega=(zustand.omega_x, 0.0, 0.0))
    gesamt_kraft = getattr(ergebnis, "F_gesamt", ergebnis.F_A)
    gesamt_moment = getattr(ergebnis, "M_gesamt", ergebnis.M)
    added = np.asarray(
        getattr(ergebnis, "added_mass_diagonal", (0.0,) * 6),
        dtype=np.float64)
    if added.shape != (6,) or not np.isfinite(added).all() \
            or np.any(added < 0.0):
        raise ValueError("Added-Mass-Werte muessen sechs endliche "
                         "nicht-negative Werte enthalten.")
    effektive_masse = np.array([
        [masse + added[2], 0.0],
        [0.0, traegheit_xx + added[3]],
    ])
    beschleunigung = np.linalg.solve(
        effektive_masse,
        np.array([
            gesamt_kraft.z - masse * g
            - daempfung_tauchung * zustand.v_z,
            gesamt_moment.x - daempfung_kraengung * zustand.omega_x,
        ]))
    a_z, alpha_x = beschleunigung
    v_z = zustand.v_z + a_z * dt
    omega_x = zustand.omega_x + alpha_x * dt
    if hasattr(ergebnis, "mit_beschleunigung"):
        resultierende_beschleunigung = np.zeros(6, dtype=np.float64)
        resultierende_beschleunigung[2] = a_z
        resultierende_beschleunigung[3] = alpha_x
        ergebnis = ergebnis.mit_beschleunigung(
            resultierende_beschleunigung)
    return (Bewegungszustand(
        z=zustand.z + v_z * dt,
        phi=zustand.phi + omega_x * dt,
        v_z=v_z,
        omega_x=omega_x), ergebnis)
