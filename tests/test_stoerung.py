"""Block S - Tests zur Stoer-Taste (Spec V4A rev C, Zielbild Z1-Z6).

pytest-kompatibel und standalone lauffaehig. Rein: keine pyvista-
Abhaengigkeit; Kraftfunktion ist ein analytischer Quader (deterministisch).
"""
from __future__ import annotations

import math
import random
import sys
import traceback

import numpy as np

from segelphysik.core import kraefte_bild as kb
from segelphysik.core import sim_modus as sm
from segelphysik.core import stoerung as st
from segelphysik.core.statisch import SolverFehler, loese


# ---- analytischer Quader (L=4, B=1.2, H=2.0; m=6000 kg, GM=0.5 m) ----
RHO = 1000.0
G = 9.81
_L, _B, _H = 4.0, 1.2, 2.0
_M = 6000.0


class _V3:
    def __init__(self, x, y, z):
        self.a = np.array([float(x), float(y), float(z)], dtype=float)

    def as_array(self):
        return self.a

    @property
    def z(self):
        return self.a[2]


class _Erg:
    def __init__(self, F_A, M, K, V):
        self.F_A = F_A
        self.M = M
        self.K = K
        self.V_tauch = V


def _quader_kf(lage, theta=0.0, trim=0.0):
    z, phi = float(lage[0]), float(lage[1])
    tiefe = min(max(_H / 2.0 - z, 0.0), _H)
    V = _L * _B * tiefe
    F_A = RHO * G * V
    K_z = z - _H / 2.0 + tiefe / 2.0
    M_x = -RHO * G * V * 0.5 * math.sin(phi)
    return _Erg(_V3(0.0, 0.0, F_A), _V3(M_x, 0.0, 0.0),
                _V3(0.0, 0.0, K_z), V)


def _kf_trocken(lage, theta=0.0, trim=0.0):
    return _Erg(_V3(0.0, 0.0, 0.0), _V3(0.0, 0.0, 0.0),
                _V3(0.0, 0.0, 0.0), 0.0)


# ---- S1-S4: Ziehen (St-1/St-2, Z6) ----
def test_s1_schranken_translation():
    rng = random.Random(7)
    for _ in range(2000):
        for d in st.stoerung_ziehen(rng)["versatz"]:
            assert abs(d) <= st.MAX_TRANSLATION_M + 1e-12


def test_s2_schranken_rotation():
    rng = random.Random(8)
    for _ in range(2000):
        for w in st.stoerung_ziehen(rng)["winkel"]:
            assert abs(w) <= st.MAX_ROTATION_RAD + 1e-12


def test_s3_seed_determinismus():
    assert st.stoerung_ziehen(random.Random(42)) == \
           st.stoerung_ziehen(random.Random(42))
    assert st.stoerung_ziehen(random.Random(42)) != \
           st.stoerung_ziehen(random.Random(43))


def test_s4_komponenten_streuen():
    rng = random.Random(9)
    werte = [st.stoerung_ziehen(rng) for _ in range(500)]
    for i in range(3):
        vs = np.array([w["versatz"][i] for w in werte])
        ws = np.array([w["winkel"][i] for w in werte])
        assert vs.std() > 0.5 and ws.std() > 1.0
        assert (vs > 0).any() and (vs < 0).any()


# ---- S5-S7: Rotationsmatrix (St-3) ----
def test_s5_einheitsmatrix():
    assert np.allclose(st.rotationsmatrix((0.0, 0.0, 0.0)), np.eye(3))


def test_s6_orthogonalitaet():
    rng = random.Random(10)
    for _ in range(50):
        R = st.rotationsmatrix(st.stoerung_ziehen(rng)["winkel"])
        assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
        assert abs(np.linalg.det(R) - 1.0) < 1e-12


def test_s7_achsenfolge_x_y_z():
    R = st.rotationsmatrix((math.pi / 2, 0.0, 0.0))
    assert np.allclose(R @ np.array([0.0, 1.0, 0.0]), [0.0, 0.0, 1.0])
    w = (0.3, -0.7, 1.1)
    rx, ry, rz = w
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    assert np.allclose(st.rotationsmatrix(w), Rz @ Ry @ Rx)


# ---- S8-S10: Pose + Projektion (St-2/St-6) ----
def test_s8_stoss_pose_versatz_und_rotation():
    R, pos = st.stoss_pose((1.0, 2.0, 3.0),
                           {"versatz": (0.1, 0.2, 0.3),
                            "winkel": (0.4, 0.5, 0.6)})
    assert np.allclose(pos, [1.1, 2.2, 3.3])
    assert np.allclose(R, st.rotationsmatrix((0.4, 0.5, 0.6)))


def test_s9_kein_basis_drift():
    basis = (0.0, 0.0, -0.25)
    s = {"versatz": (1.0, -1.0, 0.5), "winkel": (0.2, 0.2, 0.2)}
    r1 = st.stoss_pose(basis, s)
    r2 = st.stoss_pose(basis, s)
    assert np.allclose(r1[1], r2[1]) and np.allclose(r1[0], r2[0])


def test_s10_projektion_trim_verworfen():
    z, phi = st.projektion((5.0, 6.0, 7.0),
                           {"versatz": (0.0, 0.0, 0.0),
                            "winkel": (0.7, 1.3, -2.1)})
    assert z == 7.0 and phi == 0.7


# ---- S11-S14: kontakt_start (St-8) ----
def test_s11_kontaktstart_trocken():
    z, phi = st.kontakt_start(_quader_kf, 3.0, 0.0)
    assert z < _H / 2.0 and _quader_kf((z, phi, 0.0)).V_tauch > 0.0


def test_s12_kontaktstart_volltauchend():
    z, phi = st.kontakt_start(_quader_kf, -5.0, 0.0)
    V = _quader_kf((z, phi, 0.0)).V_tauch
    assert 0.0 < V < _L * _B * _H


def test_s13_kontaktstart_teiltauchung_bleibt():
    assert st.kontakt_start(_quader_kf, 0.0, 0.3) == (0.0, 0.3)


def test_s14_kontaktstart_scheitert_sauber():
    try:
        st.kontakt_start(_kf_trocken, 3.0, 0.0)
        assert False, "SolverFehler erwartet"
    except SolverFehler:
        pass


# ---- S15-S16: StoerSequenz ----
def test_s15_countdown_einmal_true():
    seq = sm.StoerSequenz(2.0)
    seq.starten()
    assert [seq.tick(0.5) for _ in range(6)] == \
           [False, False, False, True, False, False]
    assert seq.text() == ""


def test_s16_abbrechen_und_statustext():
    seq = sm.StoerSequenz(5.0)
    assert seq.text() == ""
    seq.starten()
    assert seq.tick(1.0) is False
    assert "Solver in" in seq.text() and "4.0 s" in seq.text()
    seq.abbrechen()
    assert seq.tick(10.0) is False
    assert seq.text() == ""


# ---- S17-S18: moment_bogen ----
def test_s17_bogenrichtung_rechte_hand():
    mitte = np.array([0.5, -0.2, 1.0])
    for mx in (120.0, -120.0):
        b = kb.moment_bogen(mx, mitte, 0.8)
        u = b["punkte"][-1] - mitte
        u = u / np.linalg.norm(u)
        tangente_steigend = np.cross([1.0, 0.0, 0.0], u)
        soll = math.copysign(1.0, mx) * tangente_steigend
        assert np.allclose(b["richtung"], soll, atol=1e-9)
        assert abs(float(np.dot(b["richtung"], u))) < 1e-12
    assert kb.moment_bogen(120.0, mitte, 0.8)["punkte"].shape \
        == (kb.BOGEN_PUNKTE, 3)


def test_s18_bogen_verschwindet_im_gleichgewicht():
    assert kb.moment_bogen(0.0, (0.0, 0.0, 0.0), 1.0) is None
    assert kb.moment_bogen(1e-9, (0.0, 0.0, 0.0), 1.0) is None
    try:
        kb.moment_bogen(1.0, (0.0, 0.0, 0.0), 0.0)
        assert False, "ValueError erwartet"
    except ValueError:
        pass


# ---- S19-S20: beste_loesung (St-9, rev C) ----
def test_s19_beste_loesung_waehlt_stabile_tiefste():
    loesungen = [{"z": 0.1, "gm": 0.3},      # stabil, hoch
                 {"z": -0.5, "gm": 0.2},     # stabil, tief -> Gewinner
                 {"z": -1.0, "gm": None}]    # instabil/unbestimmt
    assert st.beste_loesung(loesungen)["z"] == -0.5


def test_s20_beste_loesung_ohne_stabile_none():
    assert st.beste_loesung([{"z": 0.0, "gm": None},
                             {"z": 1.0, "gm": -0.1}]) is None
    assert st.beste_loesung([]) is None


# ---- Regression Block M ----
def test_m_regression_simsteuerung():
    k = sm.SimSteuerung()
    assert k.modus is sm.Modus.RUHEND
    assert k.taste("s") is True and k.modus is sm.Modus.STATISCH
    assert k.taste("s") is False
    assert k.taste("x") is False
    assert k.taste("r") is True and k.modus is sm.Modus.RUHEND
    assert k.wechsel == 2
    assert "RUHEND" in k.text()


# ---- Integration: St-8-Kette (Z1/Z5) ----
def test_integration_kette_mit_solver():
    seed = None
    for s in range(200):
        _, phi = st.projektion((0.0, 0.0, 0.0),
                               st.stoerung_ziehen(random.Random(s)))
        if abs(phi) <= 1.0:
            seed = s
            break
    assert seed is not None
    sto = st.stoerung_ziehen(random.Random(seed))
    z_start, phi_start = st.projektion((0.0, 0.0, -0.25), sto)
    z_k, phi_k = st.kontakt_start(_quader_kf, z_start, phi_start)
    erg = loese(_quader_kf, _M, G, start=(z_k, phi_k))
    assert abs(erg["z"] - (-0.25)) < 1e-4
    assert abs(erg["phi"]) < 1e-4
    assert erg["gm"] is not None and erg["gm"] > 0.0


def test_integration_ohne_kontaktstart_sauberer_fehler():
    try:
        loese(_quader_kf, _M, G, start=(3.0, 0.0))
        assert False, "SolverFehler erwartet"
    except SolverFehler:
        pass


def test_integration_trockenkette_findet_gleichgewicht():
    z_k, phi_k = st.kontakt_start(_quader_kf, 3.0, 0.2)
    erg = loese(_quader_kf, _M, G, start=(z_k, phi_k))
    assert abs(erg["z"] - (-0.25)) < 1e-4
    assert abs(erg["phi"]) < 1e-4


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
