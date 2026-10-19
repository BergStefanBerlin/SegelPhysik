"""Unveränderliche numerische Gates der freigegebenen v0.9-Fassung 1.

Diese Gates ersetzen keine exakten Regressionstoleranzen und geben keinen
Näherungspfad frei. Qualitative Lernzielprüfungen kommen zusätzlich hinzu.
"""
from dataclasses import dataclass
import math

import numpy as np


def _vektor(wert, laenge):
    a = np.asarray(wert, dtype=float)
    if a.shape != (laenge,) or not np.isfinite(a).all():
        raise ValueError("Endlicher Vektor mit %d Komponenten erwartet" % laenge)
    return a


def _positiv(wert):
    if (isinstance(wert, bool)
            or not isinstance(wert, (int, float, np.floating))
            or not math.isfinite(wert) or wert <= 0):
        raise ValueError("Positive endliche Referenzgröße erwartet")
    return float(wert)


def _abstand(a, b):
    return float(np.linalg.norm(_vektor(a, 3) - _vektor(b, 3)))


def _winkel(a, b):
    a, b = _vektor(a, 4), _vektor(b, 4)
    if not (np.isclose(np.linalg.norm(a), 1, rtol=0, atol=1e-8)
            and np.isclose(np.linalg.norm(b), 1, rtol=0, atol=1e-8)):
        raise ValueError("Normierte Orientierungsquaternionen erwartet")
    return 2 * math.acos(min(1.0, abs(float(a @ b))))


def _grenze(name, fehler, grenze):
    if not math.isfinite(fehler) or fehler > grenze:
        raise ValueError(
            "%s: Abweichung %.12g überschreitet %.12g (Fassung 1)"
            % (name, fehler, grenze))


@dataclass(frozen=True)
class GenauigkeitV09:
    laenge_m: float
    breite_m: float
    masse_kg: float
    g_m_pro_s2: float
    vollvolumen_m3: float

    def __post_init__(self):
        for wert in (self.laenge_m, self.breite_m, self.masse_kg,
                     self.g_m_pro_s2, self.vollvolumen_m3):
            _positiv(wert)

    def hydrostatik(self, referenz, kandidat, *,
                    wasserliniengrenze=False, rueckstelltest=False):
        """Dicts: volumen_m3, kraft_N, moment_Nm, schwerpunkt_m."""
        for daten in (referenz, kandidat):
            v = daten["volumen_m3"]
            if (isinstance(v, bool) or not isinstance(v, (int, float, np.floating))
                    or not math.isfinite(v) or v < 0):
                raise ValueError("Eingetauchtes Volumen muss endlich und >=0 sein")
            for feld in ("kraft_N", "moment_Nm", "schwerpunkt_m"):
                _vektor(daten[feld], 3)
        v = referenz["volumen_m3"]
        mg = self.masse_kg * self.g_m_pro_s2
        _grenze("Volumen", abs(kandidat["volumen_m3"] - v),
                .001 * self.vollvolumen_m3 + .02 * abs(v))
        _grenze("Auftriebskraft", _abstand(kandidat["kraft_N"], referenz["kraft_N"]),
                .01 * mg + .03 * np.linalg.norm(referenz["kraft_N"]))
        _grenze("Auftriebsmoment",
                _abstand(kandidat["moment_Nm"], referenz["moment_Nm"]),
                .001 * mg * self.breite_m
                + .05 * np.linalg.norm(referenz["moment_Nm"]))
        if v >= .05 * self.vollvolumen_m3:
            _grenze("Auftriebsschwerpunkt",
                    _abstand(kandidat["schwerpunkt_m"], referenz["schwerpunkt_m"]),
                    min(.005 * self.laenge_m, .03))
        if not wasserliniengrenze and (
                (v > 0) != (kandidat["volumen_m3"] > 0)):
            raise ValueError("Trocken-/Benetztzustand verändert")
        if v > 0 and np.dot(referenz["kraft_N"], kandidat["kraft_N"]) <= 0:
            raise ValueError("Auftriebsrichtung verändert")
        if rueckstelltest and (
                np.dot(referenz["moment_Nm"], kandidat["moment_Nm"]) <= 0):
            raise ValueError("Rückstellrichtung nicht erhalten")

    def statik(self, position_ref, q_ref, position, q):
        ref, neu = _vektor(position_ref, 3), _vektor(position, 3)
        _grenze("Gleichgewichtshöhe", abs(neu[2] - ref[2]),
                min(.01 * self.laenge_m, .02))
        _grenze("Gleichgewichtsorientierung", _winkel(q_ref, q), math.radians(1))

    def dynamik(self, zeit_ref_s, zeit_s, zustand_ref, zustand):
        if (not math.isfinite(zeit_s) or zeit_s != zeit_ref_s
                or not 0 <= zeit_s <= 30):
            raise ValueError("Dynamikvergleich benötigt gleiche Simulationszeit in [0,30] s")
        _grenze("Dynamikposition",
                _abstand(zustand.position, zustand_ref.position),
                min(.02 * self.laenge_m, .05))
        _grenze("Dynamikorientierung",
                _winkel(zustand.quaternion, zustand_ref.quaternion),
                math.radians(2))
        from .dynamik_6dof import quaternion_matrix
        # Körpergeschwindigkeiten müssen vor dem Vergleich in denselben Frame.
        vref = quaternion_matrix(zustand_ref.quaternion) @ _vektor(
            zustand_ref.geschwindigkeit_koerper, 3)
        v = quaternion_matrix(zustand.quaternion) @ _vektor(
            zustand.geschwindigkeit_koerper, 3)
        _vektor(zustand.winkelgeschwindigkeit_koerper, 3)
        _vektor(zustand_ref.winkelgeschwindigkeit_koerper, 3)
        _grenze("Geschwindigkeit", _abstand(vref, v),
                .02 + .05 * np.linalg.norm(vref))

    def schwingung(self, periode_ref_s, periode_s,
                   abklingzeit_ref_s, abklingzeit_s):
        for name, ref, neu in (
                ("Periode", periode_ref_s, periode_s),
                ("Abklingzeit", abklingzeit_ref_s, abklingzeit_s)):
            if ref is None:
                if neu is not None:
                    raise ValueError("%s ohne messbare Referenz" % name)
                continue
            _positiv(ref)
            _positiv(neu)
            _grenze(name, abs(neu - ref), .1 * ref)
