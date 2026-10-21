"""Rendererfreie Skalierung und Geometrie der gemeinsamen Kraftanzeige."""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np

from . import kraefte_bild
from .kraefte_anzeige import AnzeigeId, Datenstatus, GUELTIGE_STATUS, Vektor3


def _positiv(wert, name):
    wert = float(wert)
    if not math.isfinite(wert) or wert <= 0:
        raise ValueError("%s muss endlich positiv sein" % name)
    return wert


def _vektor(wert, name, laenge=3):
    array = np.asarray(wert, dtype=np.float64)
    if array.shape != (laenge,) or not np.isfinite(array).all():
        raise ValueError("%s braucht %d endliche Werte" % (name, laenge))
    return array


@dataclass(frozen=True, slots=True)
class SkalenWert:
    relativ: float
    groesse_px: float
    abgeschnitten: bool
    kleinwert: bool


@dataclass(frozen=True, slots=True)
class SkalenAbbildung:
    referenz: float
    maximum_px: float
    modus: str = "linear"

    def __post_init__(self):
        object.__setattr__(self, "referenz", _positiv(self.referenz, "Referenz"))
        object.__setattr__(self, "maximum_px", _positiv(self.maximum_px, "Maximalgroesse"))
        if self.modus not in ("linear", "log"):
            raise ValueError("Skalenmodus muss linear oder log sein")

    def abbilden(self, betrag: float) -> SkalenWert:
        betrag = float(betrag)
        if not math.isfinite(betrag) or betrag < 0:
            raise ValueError("Skalenbetrag muss endlich und nichtnegativ sein")
        abgeschnitten = betrag > self.referenz
        anteil = min(betrag, self.referenz) / self.referenz
        # Algebraisch log1p(m/m0)/log1p(R/m0), ohne Unterlauf von m0=R/100.
        u = (anteil if self.modus == "linear"
             else math.log1p(100 * anteil) / math.log1p(100))
        groesse = self.maximum_px * u
        return SkalenWert(u, groesse, abgeschnitten, betrag > 0 and groesse < 1)

    def neu_einpassen(self, betraege) -> SkalenAbbildung:
        werte = tuple(float(w) for w in betraege)
        if any(not math.isfinite(w) or w < 0 for w in werte):
            raise ValueError("Neu einpassen braucht endliche nichtnegative Betraege")
        maximum = max(werte, default=0.0)
        if maximum == 0:
            return self
        return replace(self, referenz=_positiv(1.1 * maximum, "Neue Referenz"))

    def legende(self) -> tuple[tuple[float, SkalenWert], ...]:
        return tuple((m, self.abbilden(m))
                     for m in (0.01 * self.referenz, 0.1 * self.referenz, self.referenz))


def anfangsreferenz(betraege, *, untergrenze=0.0, manuell=None) -> float:
    untergrenze = float(untergrenze)
    werte = tuple(float(w) for w in betraege)
    if (not math.isfinite(untergrenze) or untergrenze < 0
            or any(not math.isfinite(w) or w < 0 for w in werte)):
        raise ValueError("Referenzinitialisierung braucht gueltige nichtnegative Werte")
    if manuell is not None:
        return _positiv(manuell, "Manuelle Referenz")
    maximum = max((untergrenze, *werte))
    return maximum if maximum > 0 else 1.0


def zahlenwert(wert, einheit: str, *, status=Datenstatus.GUELTIG,
               details=False) -> str:
    status = Datenstatus(status)
    if status not in GUELTIGE_STATUS:
        return status.value
    if wert is None or not math.isfinite(float(wert)):
        raise ValueError("Gueltige Zahlenanzeige braucht einen endlichen Wert")
    wert = float(wert)
    if status == Datenstatus.NULL and wert != 0:
        raise ValueError("Nullstatus widerspricht dem Zahlenwert")
    if einheit not in ("N", "N*m", "m", "s"):
        raise ValueError("Unbekannte Anzeigeeinheit: %s" % einheit)
    if einheit in ("N", "N*m", "m"):
        text = format(wert, ",.2f" if einheit == "m" else ",.0f")
        if text in ("-0", "-0.00"):
            text = text[1:]
        text = text.replace(",", " ").replace(".", ",")
    else:
        text = ("0" if wert == 0 else
                format(wert, ".17g" if details else ".4g").replace(".", ","))
    return text + " " + ("Nm" if einheit == "N*m" else einheit)


@dataclass(frozen=True, slots=True)
class KameraAbbildung:
    position: Vektor3
    ziel: Vektor3
    viewport_logisch: tuple[float, float]
    parallel: bool
    parallel_scale: float
    blickwinkel_grad: float
    horizontaler_blickwinkel: bool = False

    def __post_init__(self):
        position = _vektor(self.position, "Kameraposition")
        ziel = _vektor(self.ziel, "Kameraziel")
        groesse = _vektor(self.viewport_logisch, "Viewport", 2)
        if math.hypot(*(ziel - position)) == 0 or np.any(groesse <= 0):
            raise ValueError("Kamerarichtung und Viewport duerfen nicht null sein")
        if (not isinstance(self.parallel, bool)
                or not isinstance(self.horizontaler_blickwinkel, bool)):
            raise ValueError("Kameramodus muss boolesch sein")
        winkel = float(self.blickwinkel_grad)
        if not math.isfinite(winkel) or not 0 < winkel < 180:
            raise ValueError("Kamerablickwinkel muss zwischen 0 und 180 Grad liegen")
        object.__setattr__(self, "position", tuple(float(w) for w in position))
        object.__setattr__(self, "ziel", tuple(float(w) for w in ziel))
        object.__setattr__(self, "viewport_logisch", tuple(float(w) for w in groesse))
        object.__setattr__(self, "parallel_scale",
                           _positiv(self.parallel_scale, "Parallelmassstab"))
        object.__setattr__(self, "blickwinkel_grad", winkel)

    def welt_pro_pixel(self, anker) -> float:
        anker = _vektor(anker, "Grafikanker")
        if self.parallel:
            return 2 * self.parallel_scale / self.viewport_logisch[1]
        richtung = np.asarray(self.ziel) - self.position
        richtung /= math.hypot(*richtung)
        tiefe = float(np.dot(anker - self.position, richtung))
        if tiefe <= 0:
            raise ValueError("Grafikanker liegt nicht vor der Kamera")
        achse = 0 if self.horizontaler_blickwinkel else 1
        return _positiv(
            2 * tiefe * math.tan(math.radians(self.blickwinkel_grad) / 2)
            / self.viewport_logisch[achse], "Weltmass je Pixel")


@dataclass(frozen=True, slots=True)
class MomentenBogen:
    punkte: tuple[Vektor3, ...]
    richtung: Vektor3
    achse: Vektor3
    radius_m: float


class BogenVerlauf:
    def __init__(self):
        self._generationen: dict[str, int] = {}
        self._basen: dict[AnzeigeId, Vektor3] = {}

    def koerper_entfernen(self, koerper_id: str):
        self._generationen.pop(koerper_id, None)
        self._basen = {key: basis for key, basis in self._basen.items()
                       if key[0] != koerper_id}

    def bogen(self, instanz_id: AnzeigeId, generation: int, moment,
              mittelpunkt, radius_m: float) -> MomentenBogen | None:
        instanz_id = tuple(instanz_id)
        if (len(instanz_id) != 2
                or any(not isinstance(w, str) or not w for w in instanz_id)
                or type(generation) is not int or generation < 0):
            raise ValueError("Bogen braucht Instanz-ID und gueltige Generation")
        moment = _vektor(moment, "Moment")
        mittelpunkt = _vektor(mittelpunkt, "Bogenmittelpunkt")
        radius_m = _positiv(radius_m, "Bogenradius")
        koerper_id = instanz_id[0]
        if generation < self._generationen.get(koerper_id, generation):
            raise ValueError("Veraltete Bogengeneration")
        if self._generationen.get(koerper_id) != generation:
            self.koerper_entfernen(koerper_id)
            self._generationen[koerper_id] = generation
        betrag = math.hypot(*moment)
        if betrag == 0:
            return None
        _positiv(betrag, "Momentbetrag")
        achse = moment / betrag
        vorher = self._basen.get(instanz_id)
        radial = (None if vorher is None
                  else np.asarray(vorher) - np.dot(vorher, achse) * achse)
        startwinkel = math.radians(kraefte_bild.BOGEN_START_GRAD)
        if radial is None or math.hypot(*radial) <= 1e-12:
            referenz = np.eye(3)[int(np.argmin(np.abs(achse)))]
            u = referenz - np.dot(referenz, achse) * achse
            u /= math.hypot(*u)
            radial = (math.cos(startwinkel) * u
                      + math.sin(startwinkel) * np.cross(achse, u))
        else:
            radial /= math.hypot(*radial)
            u = (math.cos(startwinkel) * radial
                 - math.sin(startwinkel) * np.cross(achse, radial))
        v = np.cross(achse, u)
        self._basen[instanz_id] = tuple(float(w) for w in radial)
        basis = np.column_stack((u, v, achse))
        # Der vorhandene native/Referenzkern erzeugt genau einen Einheitsbogen.
        # Physikalischer Betrag und Kleinwertgrenzen bleiben davon unabhaengig.
        bogen = kraefte_bild.moment_bogen_achse(1.0, (0, 0, 0), radius_m, 2)
        if bogen is None:
            raise RuntimeError("Vorhandener Bogenkern lieferte keinen Einheitsbogen")
        punkte = np.asarray(bogen["punkte"]) @ basis.T + mittelpunkt
        richtung = basis @ bogen["richtung"]
        return MomentenBogen(
            tuple(tuple(float(w) for w in punkt) for punkt in punkte),
            tuple(float(w) for w in richtung),
            tuple(float(w) for w in achse), radius_m)


def senkrechter_hebelarm(bezugspunkt, angriffspunkt, kraft) -> tuple[Vektor3, Vektor3]:
    bezug = _vektor(bezugspunkt, "Momentenbezug")
    angriff = _vektor(angriffspunkt, "Angriffspunkt")
    kraft = _vektor(kraft, "Kraft")
    skaliert = kraft / _positiv(float(np.max(np.abs(kraft))), "Kraftbetrag")
    richtung = skaliert / math.hypot(*skaliert)
    arm = angriff - bezug
    lot = angriff - np.dot(arm, richtung) * richtung
    return tuple(float(w) for w in bezug), tuple(float(w) for w in lot)


def abstand_zum_linienzug_px(punkt, linienzug) -> float:
    punkt = _vektor(punkt, "Bildschirmpunkt", 2)
    linie = np.asarray(linienzug, dtype=np.float64)
    if (linie.ndim != 2 or linie.shape[1] != 2 or len(linie) < 1
            or not np.isfinite(linie).all()):
        raise ValueError("Picking braucht einen endlichen Nx2-Linienzug")
    if len(linie) == 1:
        return math.hypot(*(punkt - linie[0]))
    segment = np.diff(linie, axis=0)
    quadrat = np.einsum("ij,ij->i", segment, segment)
    anteil = np.divide(
        np.einsum("ij,ij->i", punkt - linie[:-1], segment), quadrat,
        out=np.zeros_like(quadrat), where=quadrat != 0)
    lot = linie[:-1] + np.clip(anteil, 0, 1)[:, None] * segment
    return min(math.hypot(*delta) for delta in punkt - lot)
