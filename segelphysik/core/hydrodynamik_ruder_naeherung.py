"""Isoliertes, nicht validiertes Kleinwinkelmodell fuer ein Yacht-Ruder."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .dynamik_6dof import quaternion_aus_matrix
from .frames import Pose, rotationsmatrix_achsenwinkel
from .kraftmodell import Kraftbeitrag, Wrench

RUDER_MODELL_STATUS = "berechnete_naeherung"
RUDER_ALPHA_MAX_RAD = math.radians(10.0)
RUDER_YACHT1_ACHSPUNKT_M = (-1.825, 0.0, -0.318675)
RUDER_YACHT1_ACHSE = (0.0, 0.0, 1.0)
RUDER_YACHT1_KINEMATIK = "nutzerbeauftragte_testannahme_vorderkante"


class HydrodynamikModellFehler(ValueError):
    """Ungueltige oder ausserhalb des Modellbereichs liegende Eingabe."""


def _vektor3(wert, name):
    try:
        vektor = np.asarray(wert, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise HydrodynamikModellFehler(
            "%s muss drei endliche Zahlen enthalten" % name) from fehler
    if vektor.shape != (3,) or not np.isfinite(vektor).all():
        raise HydrodynamikModellFehler(
            "%s muss drei endliche Zahlen enthalten" % name)
    return vektor


def _skalar(wert, name):
    try:
        skalar = float(wert)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise HydrodynamikModellFehler(
            "%s muss eine endliche Zahl sein" % name) from fehler
    if not math.isfinite(skalar):
        raise HydrodynamikModellFehler(
            "%s muss eine endliche Zahl sein" % name)
    return skalar


@dataclass(frozen=True, slots=True)
class RuderTestkinematik:
    """Explizite Testannahme; keine Behauptung ueber die Yachtkonstruktion."""

    achspunkt_m: tuple[float, float, float] = RUDER_YACHT1_ACHSPUNKT_M
    achse: tuple[float, float, float] = RUDER_YACHT1_ACHSE
    annahme: str = RUDER_YACHT1_KINEMATIK

    def __post_init__(self):
        punkt = _vektor3(self.achspunkt_m, "Ruder-Testachspunkt")
        achse = _vektor3(self.achse, "Ruder-Testachse")
        norm = float(np.linalg.norm(achse))
        if norm <= 1e-12:
            raise HydrodynamikModellFehler(
                "Ruder-Testachse darf nicht null sein")
        normierte_achse = achse / norm
        if not np.allclose(
                normierte_achse, (0.0, 0.0, 1.0),
                rtol=0.0, atol=1e-12):
            raise HydrodynamikModellFehler(
                "Dieses Rudermodell erwartet die angenommene +z-Achse")
        if not isinstance(self.annahme, str) or not self.annahme.strip():
            raise HydrodynamikModellFehler(
                "Ruder-Testkinematik braucht einen Annahmestatus")
        object.__setattr__(
            self, "achspunkt_m", tuple(float(wert) for wert in punkt))
        object.__setattr__(
            self, "achse",
            tuple(float(wert) for wert in normierte_achse))

    def pose(self, winkel_rad: float) -> Pose:
        winkel = _skalar(winkel_rad, "Ruderwinkel")
        rotation = rotationsmatrix_achsenwinkel(self.achse, winkel)
        punkt = np.asarray(self.achspunkt_m, dtype=np.float64)
        translation = punkt - rotation @ punkt
        return Pose(
            "yacht1_blatt",
            "yacht1_ruder_mesh",
            tuple(float(wert) for wert in translation),
            quaternion_aus_matrix(rotation),
        )


@dataclass(frozen=True, slots=True)
class RuderGeometrie:
    """Geometrisch abgeleitete Daten einer duennen, vertikalen Ruderflaeche."""

    planform_flaeche_m2: float
    spannweite_m: float
    flaechenzentrum_m: tuple[float, float, float]
    testkinematik: RuderTestkinematik = RuderTestkinematik()

    def __post_init__(self):
        flaeche = float(self.planform_flaeche_m2)
        spannweite = float(self.spannweite_m)
        zentrum = _vektor3(self.flaechenzentrum_m, "Ruder-Flaechenzentrum")
        if not math.isfinite(flaeche) or flaeche <= 0.0:
            raise HydrodynamikModellFehler(
                "Ruder-Planformflaeche muss positiv und endlich sein")
        if not math.isfinite(spannweite) or spannweite <= 0.0:
            raise HydrodynamikModellFehler(
                "Ruder-Spannweite muss positiv und endlich sein")
        if not isinstance(self.testkinematik, RuderTestkinematik):
            raise TypeError(
                "Ruder-Geometrie braucht eine RuderTestkinematik")
        object.__setattr__(self, "planform_flaeche_m2", flaeche)
        object.__setattr__(self, "spannweite_m", spannweite)
        object.__setattr__(
            self, "flaechenzentrum_m",
            tuple(float(wert) for wert in zentrum))

    @property
    def streckung(self) -> float:
        return self.spannweite_m**2 / self.planform_flaeche_m2

    @classmethod
    def aus_mesh(cls, mesh, testkinematik=None):
        """Leitet Planformflaeche und Flaechenschwerpunkt aus einem Mesh ab.

        Die Projektion setzt eine vertikale Ruderflaeche in der x-z-Ebene
        voraus. Die absolute Dreiecksprojektion zaehlt beide Meshseiten;
        deshalb wird ihre Summe halbiert.
        """
        if getattr(mesh, "frame", None) != "blatt":
            raise HydrodynamikModellFehler(
                "Ruder-Mesh muss im Blatt-Frame vorliegen")
        try:
            punkte = np.asarray(
                getattr(mesh, "punkte_si", None), dtype=np.float64)
            dreiecke_roh = np.asarray(getattr(mesh, "dreiecke", None))
        except (TypeError, ValueError, OverflowError) as fehler:
            raise HydrodynamikModellFehler(
                "Ruder-Mesh enthaelt ungueltige Punkte oder Dreiecke"
            ) from fehler
        if not np.issubdtype(dreiecke_roh.dtype, np.integer):
            raise HydrodynamikModellFehler(
                "Ruder-Meshdreiecke muessen ganzzahlige Indizes enthalten")
        dreiecke = dreiecke_roh.astype(np.int64, copy=False)
        if (punkte.ndim != 2 or punkte.shape[1] != 3 or len(punkte) < 3
                or not np.isfinite(punkte).all()):
            raise HydrodynamikModellFehler(
                "Ruder-Meshpunkte muessen ein endliches Nx3-Array sein")
        if (dreiecke.ndim != 2 or dreiecke.shape[1] != 3
                or len(dreiecke) == 0
                or np.any(dreiecke < 0)
                or np.any(dreiecke >= len(punkte))):
            raise HydrodynamikModellFehler(
                "Ruder-Meshdreiecke muessen gueltige Nx3-Indizes enthalten")

        dreieckspunkte = punkte[dreiecke]
        kreuz = np.cross(
            dreieckspunkte[:, 1] - dreieckspunkte[:, 0],
            dreieckspunkte[:, 2] - dreieckspunkte[:, 0],
        )
        projektionsflaechen = np.abs(kreuz[:, 1]) * 0.5
        projektionssumme = float(np.sum(projektionsflaechen))
        if not math.isfinite(projektionssumme) or projektionssumme <= 0.0:
            raise HydrodynamikModellFehler(
                "Ruder-Mesh hat keine positive x-z-Planformprojektion")

        zentrum = np.average(
            dreieckspunkte.mean(axis=1),
            axis=0,
            weights=projektionsflaechen,
        )
        spannweite = float(np.ptp(punkte[:, 2]))
        return cls(
            planform_flaeche_m2=projektionssumme * 0.5,
            spannweite_m=spannweite,
            flaechenzentrum_m=tuple(float(wert) for wert in zentrum),
            testkinematik=(
                RuderTestkinematik()
                if testkinematik is None else testkinematik),
        )


@dataclass(frozen=True, slots=True)
class RuderKraftErgebnis:
    beitrag: Kraftbeitrag
    anstellwinkel_effektiv_rad: float
    geschwindigkeit_m_s: float
    normalkraft_N: float
    c_normalkraft: float
    c_induzierter_widerstand: float
    f_alpha_pro_rad: float
    modell_status: str = RUDER_MODELL_STATUS


@dataclass(frozen=True, slots=True)
class RuderKraftNaeherung:
    """MMG-artige Ruder-Normalkraft ohne Yacht-/Kielinteraktionsmodell.

    Das Modell gilt nur fuer Vorwaertsfahrt und effektive Anstellwinkel bis
    zehn Grad. Profilwiderstand und Stall sind nicht enthalten.
    """

    geometrie: RuderGeometrie
    wasserdichte_kg_pro_m3: float
    sensitivitaetsfaktor: float = 1.0

    def __post_init__(self):
        dichte = _skalar(
            self.wasserdichte_kg_pro_m3, "Wasserdichte")
        faktor = _skalar(
            self.sensitivitaetsfaktor, "Sensitivitaetsfaktor")
        if not isinstance(self.geometrie, RuderGeometrie):
            raise TypeError("Ruder-Naeherung braucht RuderGeometrie")
        if not math.isfinite(dichte) or dichte <= 0.0:
            raise HydrodynamikModellFehler(
                "Wasserdichte muss positiv und endlich sein")
        if not math.isfinite(faktor) or faktor <= 0.0:
            raise HydrodynamikModellFehler(
                "Sensitivitaetsfaktor muss positiv und endlich sein")
        object.__setattr__(self, "wasserdichte_kg_pro_m3", dichte)
        object.__setattr__(self, "sensitivitaetsfaktor", faktor)

    @property
    def f_alpha_pro_rad(self) -> float:
        streckung = self.geometrie.streckung
        return (
            6.13 * streckung / (streckung + 2.25)
            * self.sensitivitaetsfaktor
        )

    def beitrag_erzeugen(
            self, geschwindigkeit_m_s, winkelgeschwindigkeit_rad_s,
            ruderwinkel_rad, *, frame,
            geschwindigkeits_bezugspunkt_m=(0, 0, 0)
            ) -> RuderKraftErgebnis:
        """Erzeugt einen Kraftbeitrag im angegebenen Koerperframe.

        Translation und Giergeschwindigkeit beziehen sich auf
        ``geschwindigkeits_bezugspunkt_m`` im selben Koerperframe.
        """
        geschwindigkeit = _vektor3(
            geschwindigkeit_m_s, "Ruder-Bezugspunktgeschwindigkeit")
        omega = _vektor3(
            winkelgeschwindigkeit_rad_s, "Koerper-Winkelgeschwindigkeit")
        bezugspunkt = _vektor3(
            geschwindigkeits_bezugspunkt_m, "Geschwindigkeitsbezugspunkt")
        winkel = _skalar(ruderwinkel_rad, "Ruderwinkel")
        if not isinstance(frame, str) or not frame.strip():
            raise HydrodynamikModellFehler(
                "Es muss ein benannter Koerperframe angegeben sein")
        if (abs(geschwindigkeit[2]) > 1e-12
                or np.any(np.abs(omega[:2]) > 1e-12)):
            raise HydrodynamikModellFehler(
                "Rudermodell unterstuetzt nur horizontale Translation "
                "und Gierbewegung")

        pose = self.geometrie.testkinematik.pose(winkel)
        rotationsmatrix = pose.rotationsmatrix
        zentrum = np.asarray(
            self.geometrie.flaechenzentrum_m, dtype=np.float64)
        kraftpunkt = rotationsmatrix @ zentrum + pose.translation_m
        arm = kraftpunkt - bezugspunkt
        lokale_geschwindigkeit = geschwindigkeit + np.cross(omega, arm)
        lokale_geschwindigkeit[2] = 0.0
        tempo = float(np.linalg.norm(lokale_geschwindigkeit[:2]))

        if tempo > 0.0 and lokale_geschwindigkeit[0] <= 0.0:
            raise HydrodynamikModellFehler(
                "Ruder-Naeherung unterstuetzt nur Vorwaertsanstroemung")
        beta = (
            math.atan2(
                lokale_geschwindigkeit[1], lokale_geschwindigkeit[0])
            if tempo > 0.0 else 0.0
        )
        alpha = winkel + beta
        if abs(alpha) > RUDER_ALPHA_MAX_RAD + 1e-12:
            raise HydrodynamikModellFehler(
                "Effektiver Ruder-Anstellwinkel %.6f deg liegt ausserhalb "
                "des Modellbereichs +/-10 deg"
                % math.degrees(alpha))

        ar = self.geometrie.streckung
        f_alpha = self.f_alpha_pro_rad
        c_n = f_alpha * math.sin(alpha)
        c_d_i = c_n * c_n / (math.pi * ar)
        q = 0.5 * self.wasserdichte_kg_pro_m3 * tempo * tempo
        normalkraft = q * self.geometrie.planform_flaeche_m2 * c_n
        kraft = np.zeros(3, dtype=np.float64)
        if tempo > 0.0:
            richtung_bewegung = lokale_geschwindigkeit / tempo
            port_normale = np.array((
                -richtung_bewegung[1], richtung_bewegung[0], 0.0))
            kraft_lift = -normalkraft * port_normale
            widerstand = (
                q * self.geometrie.planform_flaeche_m2 * c_d_i)
            kraft_widerstand = -widerstand * richtung_bewegung
            kraft = kraft_lift + kraft_widerstand

        wrench = Wrench(
            frame,
            tuple(float(wert) for wert in kraftpunkt),
            tuple(float(wert) for wert in kraft),
            (0.0, 0.0, 0.0),
        )
        return RuderKraftErgebnis(
            Kraftbeitrag("ruder_naeherung", wrench),
            alpha,
            tempo,
            normalkraft,
            c_n,
            c_d_i,
            f_alpha,
        )
