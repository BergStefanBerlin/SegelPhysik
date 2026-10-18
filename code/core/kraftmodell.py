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
class Wrench:
    """Kraft und Moment in einem Frame, bezogen auf denselben Punkt."""

    frame: str
    bezugspunkt_m: tuple[float, float, float]
    kraft_N: tuple[float, float, float]
    moment_Nm: tuple[float, float, float]

    def __post_init__(self):
        if not isinstance(self.frame, str) or not self.frame:
            raise ValueError("Wrench braucht einen benannten Frame")
        for attribut, name in (
                ("bezugspunkt_m", "Wrench-Bezugspunkt"),
                ("kraft_N", "Wrench-Kraft"),
                ("moment_Nm", "Wrench-Moment")):
            object.__setattr__(
                self, attribut,
                tuple(float(w) for w in _flussvektor(
                    getattr(self, attribut), name)))

    def auf_bezugspunkt(self, punkt_m):
        ziel = _flussvektor(punkt_m, "Neuer Wrench-Bezugspunkt")
        momentan = np.asarray(self.bezugspunkt_m, dtype=np.float64)
        kraft = np.asarray(self.kraft_N, dtype=np.float64)
        moment = np.asarray(self.moment_Nm, dtype=np.float64)
        verschoben = moment + np.cross(momentan - ziel, kraft)
        return Wrench(
            self.frame,
            tuple(float(w) for w in ziel),
            self.kraft_N,
            tuple(float(w) for w in verschoben),
        )


@dataclass(frozen=True)
class Kraftbeitrag:
    name: str
    wrench: Wrench


def aggregiere_kraftbeitraege(beitraege, bezugspunkt_m,
                               frame="simulationsframe"):
    """Bringt alle Beiträge einmal auf denselben Punkt und summiert sie."""
    bezugspunkt = _flussvektor(bezugspunkt_m, "Gesamt-Wrench-Bezugspunkt")
    normalisiert = []
    kraft = np.zeros(3, dtype=np.float64)
    moment = np.zeros(3, dtype=np.float64)
    for beitrag in beitraege:
        if beitrag.wrench.frame != frame:
            raise ValueError(
                "Kraftbeitrag %r liegt im Frame %r statt %r"
                % (beitrag.name, beitrag.wrench.frame, frame))
        wrench = beitrag.wrench.auf_bezugspunkt(bezugspunkt)
        normalisiert.append(Kraftbeitrag(beitrag.name, wrench))
        kraft += np.asarray(wrench.kraft_N)
        moment += np.asarray(wrench.moment_Nm)
    gesamt = Wrench(
        frame,
        tuple(float(w) for w in bezugspunkt),
        tuple(float(w) for w in kraft),
        tuple(float(w) for w in moment),
    )
    return gesamt, tuple(normalisiert)


@dataclass(frozen=True)
class KraftErgebnis:
    """Hydrostatikdaten plus summierte aeussere Kraft- und Momentenvektoren."""

    hydrostatik: object
    F_gesamt: Vektor
    M_gesamt: Vektor
    added_mass_diagonal: tuple[float, ...]
    beitraege: tuple[Kraftbeitrag, ...] = ()
    bezugspunkt_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    schwerkraft_beruecksichtigt: bool = False

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

    @property
    def gesamt_wrench(self):
        return Wrench(
            "simulationsframe",
            self.bezugspunkt_m,
            tuple(float(w) for w in self.F_gesamt.as_array()),
            tuple(float(w) for w in self.M_gesamt.as_array()),
        )

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
        beitraege = self.beitraege + (Kraftbeitrag(
            "added_mass", Wrench(
                "simulationsframe", self.bezugspunkt_m,
                tuple(float(w) for w in zusatz[:3]),
                tuple(float(w) for w in zusatz[3:]))),)
        return KraftErgebnis(
            self.hydrostatik, Vektor(kraft), Vektor(moment),
            self.added_mass_diagonal, beitraege,
            self.bezugspunkt_m, self.schwerkraft_beruecksichtigt)


class Kraftmodell:
    """Hydrostatik, Widerstand, Fluidbewegung und Added Mass.

    Komponentenreihenfolge der Widerstands- und Added-Mass-Werte:
    Welt-x/y/z, Roll/Pitch/Yaw. Nicht konfigurierte Module sind null.
    """

    def __init__(self, hydrostatik, *, linear_widerstand=(0.0,) * 6,
                 quadratischer_widerstand=(0.0,) * 6,
                 fluidgeschwindigkeit=(0.0, 0.0, 0.0),
                 fluidwinkelgeschwindigkeit=(0.0, 0.0, 0.0),
                 added_mass_diagonal=(0.0,) * 6, masse=None,
                 g=9.80665):
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
        self.masse = None if masse is None else float(masse)
        self.g = float(g)
        if self.masse is not None and (
                not np.isfinite(self.masse) or self.masse <= 0.0):
            raise ValueError("Körpermasse muss endlich und positiv sein")
        if not np.isfinite(self.g) or self.g <= 0.0:
            raise ValueError(
                "Schwerebeschleunigung muss positiv und endlich sein")
        self.fremdkraft = None

    def __call__(self, lage, v=None, omega=None):
        hydro = self.hydrostatik(lage, v=v, omega=omega)
        return self.mit_hydrostatik(hydro, v=v, omega=omega, lage=lage)

    def fremdkraft_setzen(self, fremdkraft):
        """Setzt eine Welt-Kraft (N) an einem koerperfesten Punkt relativ zum
        Schwerpunkt (m) als ((fx, fy, fz), (rx, ry, rz)); None schaltet ab."""
        if fremdkraft is None:
            self.fremdkraft = None
            return
        kraft, punkt = fremdkraft
        self.fremdkraft = (_flussvektor(kraft, "Fremdkraft"),
                           _flussvektor(punkt, "Fremdkraft-Angriffspunkt"))

    def mit_hydrostatik(self, hydro, v=None, omega=None, lage=None):
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
        position = _position_aus_lage(lage)
        beitraege = [
            Kraftbeitrag("hydrostatik", Wrench(
                "simulationsframe", position,
                tuple(float(w) for w in hydro.F_A.as_array()),
                tuple(float(w) for w in hydro.M.as_array()))),
            Kraftbeitrag("widerstand", Wrench(
                "simulationsframe", position,
                tuple(float(w) for w in widerstand[:3]),
                tuple(float(w) for w in widerstand[3:]))),
        ]
        if self.fremdkraft is not None and lage is not None:
            kraft_f, punkt = self.fremdkraft
            q = np.asarray(lage[1], dtype=np.float64)
            if q.shape == (4,):
                from .dynamik_6dof import quaternion_matrix
                arm = quaternion_matrix(q) @ punkt
            elif isinstance(lage, (tuple, list)) and len(lage) >= 3:
                phi = float(lage[1])
                c, s = np.cos(phi), np.sin(phi)
                rotation = np.array([
                    [1.0, 0.0, 0.0],
                    [0.0, c, -s],
                    [0.0, s, c],
                ])
                arm = rotation @ punkt
            else:
                arm = punkt
            beitraege.append(Kraftbeitrag("fremdkraft", Wrench(
                "simulationsframe", tuple(
                    float(w) for w in np.asarray(position) + arm),
                tuple(float(w) for w in kraft_f),
                (0.0, 0.0, 0.0))))
        schwerkraft_beruecksichtigt = self.masse is not None
        if schwerkraft_beruecksichtigt:
            gewicht = np.array((0.0, 0.0, -self.masse * self.g))
            beitraege.append(Kraftbeitrag("schwerkraft", Wrench(
                "simulationsframe", position,
                tuple(float(w) for w in gewicht), (0.0, 0.0, 0.0))))
        gesamt, beitraege = aggregiere_kraftbeitraege(
            beitraege, position)
        return KraftErgebnis(
            hydro, Vektor(gesamt.kraft_N), Vektor(gesamt.moment_Nm),
            tuple(float(wert) for wert in self.added_mass_diagonal),
            beitraege, position, schwerkraft_beruecksichtigt)


class KraftmodellMitHydroCache:
    """Exakter Cache standardmäßig; Intervalle > 1 sind explizite Approximation."""

    def __init__(self, kraftmodell, intervall=1):
        if not isinstance(kraftmodell, Kraftmodell):
            raise TypeError("Hydro-Cache braucht ein Kraftmodell")
        if not isinstance(intervall, int) or intervall < 1:
            raise ValueError("Hydro-Cache-Intervall muss positiv sein")
        self.kraftmodell = kraftmodell
        self.intervall = intervall
        self.aktualisieren()

    def fremdkraft_setzen(self, fremdkraft):
        self.kraftmodell.fremdkraft_setzen(fremdkraft)

    def aktualisieren(self):
        self._hydrostatik = None
        self._schritte_bis_aktualisierung = 0

    def __call__(self, lage, v=None, omega=None):
        # Intervall > 1 hält Hydrostatik bei geänderter Pose absichtlich fest.
        if self._schritte_bis_aktualisierung <= 0:
            self._hydrostatik = self.kraftmodell.hydrostatik(lage)
        ergebnis = self.kraftmodell.mit_hydrostatik(
            self._hydrostatik, v=v, omega=omega, lage=lage)
        self._schritte_bis_aktualisierung = (
            self.intervall - 1 if self._schritte_bis_aktualisierung <= 0
            else self._schritte_bis_aktualisierung - 1)
        return ergebnis


def _position_aus_lage(lage):
    if isinstance(lage, (tuple, list)) and len(lage) == 2:
        position = np.asarray(lage[0], dtype=np.float64)
        if position.shape == (3,) and np.isfinite(position).all():
            return tuple(float(w) for w in position)
    try:
        z = float(lage[0])
    except (TypeError, ValueError, IndexError, OverflowError):
        return (0.0, 0.0, 0.0)
    return (0.0, 0.0, z) if np.isfinite(z) else (0.0, 0.0, 0.0)


def baue_kraftmodell(hydrostatik, physik, *, masse=None, g=None):
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
        added_mass_diagonal=physik.added_mass_diagonal,
        masse=masse,
        g=physik.g_m_pro_s2 if g is None else g)
