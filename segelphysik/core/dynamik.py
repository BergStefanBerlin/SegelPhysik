"""Fester SI-Zeitschritt fuer Tauchbewegung und Kraengung."""
from __future__ import annotations

from dataclasses import dataclass
import math


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
    a_z = (ergebnis.F_A.z - masse * g
           - daempfung_tauchung * zustand.v_z) / masse
    alpha_x = (ergebnis.M.x
               - daempfung_kraengung * zustand.omega_x) / traegheit_xx
    v_z = zustand.v_z + a_z * dt
    omega_x = zustand.omega_x + alpha_x * dt
    return (Bewegungszustand(
        z=zustand.z + v_z * dt,
        phi=zustand.phi + omega_x * dt,
        v_z=v_z,
        omega_x=omega_x), ergebnis)
