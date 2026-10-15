"""Tests zum robusten Solver-Wrapper (rev D): Voxel-Treppen-Fall.

Der Kern der Sichtprobe vom 12.10.: eine TREPPENFUNKTION (wie der
Voxel-Kern) bringt das klassische Newton zum Absturz (im echten Lauf
sogar mit NaN statt sauberem SolverFehler). loese_robust muss daraus
die Gleichgewichtslage finden.
"""
from __future__ import annotations

import math
import sys
import traceback

import numpy as np

from segelphysik.core.statisch import SolverFehler, loese
from segelphysik.core.statisch_robust import loese_robust
from segelphysik.core.stoerung import beste_loesung, kontakt_start


RHO_G = 9810.0          # rho*g
_L, _B, _H = 4.0, 1.2, 2.0
_M = 6000.0
_DZ = 0.05              # Voxel-Stufenhoehe in z


class _V3:
    def __init__(self, a):
        self.a = np.asarray(a, float)

    def as_array(self):
        return self.a


class _Erg:
    def __init__(self, F_A, M, K, V):
        self.F_A = F_A
        self.M = M
        self.K = K
        self.V_tauch = V


def _stufe(x, breite):
    """Quantisierung auf Stufen (wie der Voxel-Kern); NaN-sicher."""
    if not math.isfinite(x):
        return breite * 1e6   # nicht-finite Lage -> trocken
    return round(x / breite) * breite


def _treppen_kf(lage, theta=0.0, trim=0.0):
    """Quader mit VOXEL-Treppen in z UND phi (M_x stufenweise)."""
    z, phi = float(lage[0]), float(lage[1])
    tiefe = min(max(_H / 2.0 - _stufe(z, _DZ), 0.0), _H)
    V = _L * _B * tiefe
    F_A = RHO_G * V
    K_z = z - _H / 2.0 + tiefe / 2.0
    M_x = -RHO_G * V * 0.5 * math.sin(_stufe(phi, 0.02))
    return _Erg(_V3([0.0, 0.0, F_A]), _V3([M_x, 0.0, 0.0]),
                _V3([0.0, 0.0, K_z]), V)


def _glatt_kf(lage, theta=0.0, trim=0.0):
    z, phi = float(lage[0]), float(lage[1])
    tiefe = min(max(_H / 2.0 - z, 0.0), _H)
    V = _L * _B * tiefe
    M_x = -RHO_G * V * 0.5 * math.sin(phi)
    return _Erg(_V3([0.0, 0.0, RHO_G * V]), _V3([M_x, 0.0, 0.0]),
                _V3([0.0, 0.0, z - _H / 2.0 + tiefe / 2.0]), V)


def _neutral_kf(lage, theta=0.0, trim=0.0):
    """Roll-neutral: M_x identisch 0 (Kegel liegend / Spantonne)."""
    z, phi = float(lage[0]), float(lage[1])
    tiefe = min(max(_H / 2.0 - z, 0.0), _H)
    V = _L * _B * tiefe
    return _Erg(_V3([0.0, 0.0, RHO_G * V]), _V3([0.0, 0.0, 0.0]),
                _V3([0.0, 0.0, z - _H / 2.0 + tiefe / 2.0]), V)


# ---- T1/T2: Der Anlassfall ----
def test_t1_klassischer_solver_scheitert_an_treppe():
    """Dokumentiert den Befund: der klassische Solver scheitert an der
    Treppenfunktion - im Sichtproben-Lauf sogar mit NaN-Absturz statt
    sauberem SolverFehler. Beides ist Scheitern."""
    fehlgeschlagen = False
    try:
        loese(_treppen_kf, _M, 9.81, start=(0.0, 0.0))
    except Exception:
        fehlgeschlagen = True
    assert fehlgeschlagen, "Erwartet: klassischer Solver scheitert an Treppe"


def test_t2_robuster_solver_findet_gleichgewicht():
    erg = loese_robust(_treppen_kf, _M, 9.81, start=(0.0, 0.0))
    assert abs(erg["z"] - (-0.25)) < 0.06   # innerhalb der Stufenhoehe
    assert abs(erg["phi"]) < 0.03
    assert erg["gm"] is not None and erg["gm"] > 0.0
    assert erg["restkraft"] < 0.05 * _M * 9.81
    assert erg["neutral"] is False and isinstance(erg["neutral"], bool)
    assert isinstance(erg["stagnation"], bool)


# ---- T3-T5: Randfaelle ----
def test_t3_robust_glatte_funktion_gleiches_ergebnis():
    """Vertragliche Kompatibilitaet: auf der glatten Funktion liefert
    loese_robust dasselbe Ergebnis wie der klassische Solver."""
    a = loese(_glatt_kf, _M, 9.81, start=(0.0, 0.0))
    b = loese_robust(_glatt_kf, _M, 9.81, start=(0.0, 0.0))
    assert abs(a["z"] - b["z"]) < 1e-6 and abs(a["phi"] - b["phi"]) < 1e-6


def test_solver_verwendet_kraftwerte_identischer_pose_nur_einmal():
    posen = []

    def zaehler(lage):
        posen.append((float(lage[0]), float(lage[1])))
        return _glatt_kf(lage)

    ergebnis = loese_robust(zaehler, _M, 9.81, start=(0.0, 0.0))

    assert abs(ergebnis["z"] - (-0.25)) < 1e-6
    assert len(posen) == len(set(posen))
    assert ergebnis["kraftauswertungen"] == len(posen)
    assert ergebnis["wiederverwendete_kraftwerte"] > 0


def test_t4_neutral_wird_erkannt():
    erg = loese_robust(_neutral_kf, _M, 9.81, start=(0.0, 0.0))
    assert erg["neutral"] is True
    assert isinstance(erg["neutral"], bool)
    assert erg["gm"] is None
    assert abs(erg["z"] - (-0.25)) < 1e-3


def test_t5_beste_loesung_neutraler_fallback():
    stabil = {"z": -0.3, "gm": 0.4, "neutral": False}
    neutral = {"z": -0.5, "gm": None, "neutral": True}
    assert beste_loesung([neutral, stabil])["z"] == -0.3   # stabil gewinnt
    assert beste_loesung([neutral])["z"] == -0.5           # Fallback greift
    assert beste_loesung([{"z": 0.0, "gm": None, "neutral": False}]) is None


def test_t6_treppe_aus_gestoerter_lage():
    """Demo-Kette (Spec St-8 + St-6): Kontaktstart bringt die trockene/
    verstörte Lage zuerst auf Teiltauchung, dann loest der robuste
    Solver bis in die Gleichgewichtslage."""
    z_k, phi_k = kontakt_start(_treppen_kf, 1.5, 0.6)
    assert _treppen_kf((z_k, phi_k, 0.0)).V_tauch > 0.0
    erg = loese_robust(_treppen_kf, _M, 9.81, start=(z_k, phi_k))
    assert abs(erg["z"] - (-0.25)) < 0.08
    assert abs(erg["phi"]) < 0.05


def test_t7_budgetende_enthaelt_letzte_residuen():
    def keine_verbesserung(_lage, theta=0.0, trim=0.0):
        return _Erg(_V3([0.0, 0.0, 0.0]), _V3([1e6, 0.0, 0.0]),
                    _V3([0.0, 0.0, 0.0]), 0.0)

    try:
        loese_robust(keine_verbesserung, _M, 9.81, max_iter=6,
                     stoerleiter=())
        raise AssertionError("Erschoepftes Budget muss fehlschlagen")
    except SolverFehler as fehler:
        assert fehler.status == "stagnation"
        assert fehler.diagnose["restkraft"] == _M * 9.81
        assert fehler.diagnose["restmoment"] == 1e6
        assert fehler.diagnose["iterationen"] == 6


def test_t8_instabile_lage_wird_mit_diagnose_abgelehnt():
    def instabil(lage, theta=0.0, trim=0.0):
        erg = _glatt_kf(lage, theta, trim)
        return _Erg(erg.F_A, _V3([-erg.M.as_array()[0], 0.0, 0.0]),
                    erg.K, erg.V_tauch)

    try:
        loese_robust(instabil, _M, 9.81, start=(-0.25, 0.0),
                     stoerleiter=())
        raise AssertionError("Instabile Gleichgewichtslage muss fehlschlagen")
    except SolverFehler as fehler:
        assert fehler.status == "instabile_lage"
        assert fehler.diagnose["stabil"] is False
        assert fehler.diagnose["restkraft"] < 1e-8
        assert fehler.diagnose["restmoment"] < 1e-8


def test_t9_nichtendliche_kraefte_werden_klassifiziert():
    def ungueltig(_lage, theta=0.0, trim=0.0):
        return _Erg(_V3([0.0, 0.0, float("nan")]),
                    _V3([float("nan"), 0.0, 0.0]),
                    _V3([0.0, 0.0, 0.0]), 0.0)

    try:
        loese_robust(ungueltig, _M, 9.81)
        raise AssertionError("Nicht-endliche Kraefte muessen fehlschlagen")
    except SolverFehler as fehler:
        assert fehler.status == "ungueltige_rechenergebnisse"
        assert fehler.diagnose["z"] == 0.0
        assert fehler.diagnose["phi"] == 0.0


if __name__ == "__main__":
    fehler = 0
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        try:
            fn()
            print("PASS %s" % name)
        except Exception:
            fehler += 1
            print("FAIL %s" % name)
            traceback.print_exc()
    print("---")
    print("%d/%d bestanden" % (len(tests) - fehler, len(tests)))
    sys.exit(1 if fehler else 0)
