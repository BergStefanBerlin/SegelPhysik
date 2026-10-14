"""Gemeinsames Kraftmodell fuer statischen Solver und Dynamikintegration."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .auftrieb import Vektor


def _vektor(werte, name, nichtnegativ=False):
    try:
        ergebnis = np.asarray(werte, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("%s muss aus sechs Zahlen bestehen" % name) from fehler
    if ergebnis.shape != (6,) or not np.isfinite(ergebnis).all():
        raise ValueError("%s muss sechs endliche Zahlen enthalten" % name)
    if nichtnegativ and np.any(ergebnis < 0.0):
        raise ValueError("%s darf keine negativen Werte enthalten" % name)
    return ergebnis


def _flussvektor(werte, name):
    try:
        ergebnis = np.asarray(werte, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("%s muss aus drei Zahlen bestehen" % name) from fehler
    if ergebnis.shape != (3,) or not np.isfinite(ergebnis).all():
        raise ValueError("%s muss drei endliche Zahlen enthalten" % name)
    return ergebnis


@dataclass(frozen=True)
class KraftErgebnis:
    """Hydrostatikdaten plus summierte aeussere Kraft- und Momentenvektoren."""

    hydrostatik: object
    F_gesamt: Vektor
    M_gesamt: Vektor
    added_mass_diagonal: tuple[float, ...]

    @property
    def V_tauch(self):
        return self.hydrostatik.V_tauch

    @property
    def K(self):
        return self.hydrostatik.K

    @property
    def F_A(self):
        return self.hydrostatik.F_A

    @property
    def M(self):
        return self.M_gesamt

    def mit_beschleunigung(self, beschleunigung, rotation=None):
        beschleunigung = _vektor(beschleunigung, "Beschleunigung")
        added_mass = np.asarray(self.added_mass_diagonal, dtype=np.float64)
        rotation = (np.eye(3) if rotation is None
                    else np.asarray(rotation, dtype=np.float64))
        if (rotation.shape != (3, 3) or not np.isfinite(rotation).all()
                or not np.allclose(rotation.T @ rotation, np.eye(3),
                                   rtol=0.0, atol=1e-8)):
            raise ValueError("Added-Mass-Transformation braucht eine "
                             "gueltige 3x3-Rotation.")
        beschleunigung_koerper = np.concatenate((
            rotation.T @ beschleunigung[:3],
            rotation.T @ beschleunigung[3:]))
        zusatz_koerper = -added_mass * beschleunigung_koerper
        zusatz = np.concatenate((
            rotation @ zusatz_koerper[:3],
            rotation @ zusatz_koerper[3:]))
        if not np.any(zusatz):
            return self
        kraft = self.F_gesamt.as_array() + zusatz[:3]
        moment = self.M_gesamt.as_array() + zusatz[3:]
        return KraftErgebnis(
            self.hydrostatik, Vektor(kraft), Vektor(moment),
            self.added_mass_diagonal)


class Kraftmodell:
    """Hydrostatik, Widerstand, Fluidbewegung und Added Mass.

    Komponentenreihenfolge der Widerstands- und Added-Mass-Werte:
    Welt-x/y/z, Roll/Pitch/Yaw. Nicht konfigurierte Module sind null.
    """

    def __init__(self, hydrostatik, *, linear_widerstand=(0.0,) * 6,
                 quadratischer_widerstand=(0.0,) * 6,
                 fluidgeschwindigkeit=(0.0, 0.0, 0.0),
                 fluidwinkelgeschwindigkeit=(0.0, 0.0, 0.0),
                 added_mass_diagonal=(0.0,) * 6):
        if not callable(hydrostatik):
            raise TypeError("Hydrostatik muss aufrufbar sein")
        self.hydrostatik = hydrostatik
        self.linear_widerstand = _vektor(
            linear_widerstand, "Linearer Widerstand", nichtnegativ=True)
        self.quadratischer_widerstand = _vektor(
            quadratischer_widerstand, "Quadratischer Widerstand",
            nichtnegativ=True)
        self.fluidgeschwindigkeit = _flussvektor(
            fluidgeschwindigkeit, "Fluidgeschwindigkeit")
        self.fluidwinkelgeschwindigkeit = _flussvektor(
            fluidwinkelgeschwindigkeit, "Fluid-Winkelgeschwindigkeit")
        self.added_mass_diagonal = _vektor(
            added_mass_diagonal, "Added Mass", nichtnegativ=True)

    def __call__(self, lage, v=None, omega=None):
        hydro = self.hydrostatik(lage, v=v, omega=omega)
        return self.mit_hydrostatik(hydro, v=v, omega=omega)

    def mit_hydrostatik(self, hydro, v=None, omega=None):
        """Wendet Kraftmodule auf ein bereits ausgewertetes Hydrostatikergebnis an."""
        geschwindigkeit = _flussvektor(
            (0.0, 0.0, 0.0) if v is None else v, "Koerpergeschwindigkeit")
        winkelgeschwindigkeit = _flussvektor(
            (0.0, 0.0, 0.0) if omega is None else omega,
            "Koerper-Winkelgeschwindigkeit")
        relativ = np.concatenate((
            geschwindigkeit - self.fluidgeschwindigkeit,
            winkelgeschwindigkeit - self.fluidwinkelgeschwindigkeit))
        widerstand = (
            -self.linear_widerstand * relativ
            -self.quadratischer_widerstand * np.abs(relativ) * relativ)
        kraft = hydro.F_A.as_array() + widerstand[:3]
        moment = hydro.M.as_array() + widerstand[3:]
        return KraftErgebnis(
            hydro, Vektor(kraft), Vektor(moment),
            tuple(float(wert) for wert in self.added_mass_diagonal))


class KraftmodellMitHydroCache:
    """Berechnet teure Hydrostatik periodisch und aktualisiert Kraftmodule je Schritt."""

    def __init__(self, kraftmodell, intervall=4):
        if not isinstance(kraftmodell, Kraftmodell):
            raise TypeError("Hydro-Cache braucht ein Kraftmodell")
        if not isinstance(intervall, int) or intervall < 1:
            raise ValueError("Hydro-Cache-Intervall muss positiv sein")
        self.kraftmodell = kraftmodell
        self.intervall = intervall
        self.aktualisieren()

    def aktualisieren(self):
        self._hydrostatik = None
        self._schritte_bis_aktualisierung = 0

    def __call__(self, lage, v=None, omega=None):
        if self._schritte_bis_aktualisierung <= 0:
            self._hydrostatik = self.kraftmodell.hydrostatik(lage)
        ergebnis = self.kraftmodell.mit_hydrostatik(
            self._hydrostatik, v=v, omega=omega)
        self._schritte_bis_aktualisierung = (
            self.intervall - 1 if self._schritte_bis_aktualisierung <= 0
            else self._schritte_bis_aktualisierung - 1)
        return ergebnis


def baue_kraftmodell(hydrostatik, physik):
    """Baut das konfigurierte Gesamtmodell; ungesetzte Module bleiben aus."""
    linear = list(physik.linear_widerstand)
    linear[2] += physik.daempfung_tauchung
    linear[3] += physik.daempfung_kraengung
    return Kraftmodell(
        hydrostatik,
        linear_widerstand=linear,
        quadratischer_widerstand=physik.quadratischer_widerstand,
        fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
        fluidwinkelgeschwindigkeit=physik.fluidwinkelgeschwindigkeit,
        added_mass_diagonal=physik.added_mass_diagonal)
