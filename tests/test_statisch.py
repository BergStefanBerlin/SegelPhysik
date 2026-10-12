"""Block P: Statischer Solver (Phase B, Umsetzungsplan V5 rev 9 §4).
Alle Referenzen analytisch. Ponton (stabil, w=2h) und Würfel halbgetaucht
(instabil, GM=-b/12, stabile Lage 45°). Kraftfunktion mit pfad="exakt"
(D10: disjunkte Testgeometrien als Referenz).

Referenzherleitungen:
  Ponton: zentrierter Quader L=2, w=4, h=2, rho_k=500 -> m=8000 kg,
    V_eq=8 m^3, t=V/(L*w)=1.0 m, Unterkante Welt=-1 -> z*=0.
    GM = BM + KB - KG = w^2/(12t) + t/2 - h/2 = 4/3 + 0.5 - 1 = 5/6.
  Wuerfel: a=2, rho_k=500 -> halb getaucht, GM=-b/12<0 (instabil),
    stabile Lage 45°; Störleiter 5°/15° laufen zur instabilen Wurzel
    zurück, 30° findet 45° -> erwartete Restarts: 2.
"""
import numpy as np

from segelphysik.core import auftrieb as au
from segelphysik.core import statisch as st


def quader_mesh(a, b, h):
    v = np.array([[0,0,0],[a,0,0],[a,b,0],[0,b,0],
                  [0,0,h],[a,0,h],[a,b,h],[0,b,h]], dtype=float)
    f = np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],
                  [0,1,5],[0,5,4],[2,3,7],[2,7,6],
                  [0,7,3],[0,4,7],[1,2,6],[1,6,5]], dtype=np.int64)
    return v, f


def zentriere(mesh):
    v, f = mesh
    return v - np.array([v[:,0].mean(), v[:,1].mean(), v[:,2].mean()]), f


class DummyKoerper:
    def __init__(self, blaetter, r_S=(0.0, 0.0, 0.0)):
        self.blatt_meshes = list(blaetter)
        self.r_S = np.array(r_S, dtype=float)


RHO_W = 1000.0
G = 9.80665


def _funktion(k):
    return au.baue_kraftfunktion(k, rho_w=RHO_W, pfad="exakt")


# ---------- P1: Ponton (stabil): z*=0, phi*=0, GM=5/6 ----------

def test_p1_ponton_gleichgewicht():
    L, w, h = 2.0, 4.0, 2.0
    m = 500.0 * L * w * h          # 8000 kg
    k = DummyKoerper([zentriere(quader_mesh(L, w, h))])
    erg = st.loese(_funktion(k), m, start=(0.5, 0.0))
    assert abs(erg["phi"]) < 1e-6
    assert abs(erg["z"]) < 1e-3, erg["z"]
    assert erg["restarts"] == 0
    assert erg["gm"] is not None and erg["gm"] > 0.0
    assert abs(erg["gm"] - 5.0/6.0) < 5e-3, erg["gm"]


# ---------- P2: Kenterfall: D9 findet die stabile 45°-Lage ----------

def test_p2_wuerfel_kentert_in_45_grad():
    a = 2.0
    m = 500.0 * a**3
    k = DummyKoerper([zentriere(quader_mesh(a, a, a))])
    erg = st.loese(_funktion(k), m, start=(0.5, 0.0))
    phi_deg = np.degrees(erg["phi"])
    assert min(abs(phi_deg - 45.0), abs(phi_deg + 45.0)) < 1.0, phi_deg
    assert erg["restarts"] >= 1


# ---------- P3: Lösung ist exakt kraftfrei ----------

def test_p3_loesung_ist_kraftfrei():
    L, w, h = 2.0, 4.0, 2.0
    m = 500.0 * L * w * h
    k = DummyKoerper([zentriere(quader_mesh(L, w, h))])
    f = _funktion(k)
    erg = st.loese(f, m, start=(0.5, 0.0))
    r, e = st._residuum(f, (erg["z"], erg["phi"], 0.0), m, G)
    assert abs(r[0]) < 1e-6 and abs(r[1]) < 1e-6


# ---------- P4: Konvergenz aus gestörter Pose ohne Restart ----------

def test_p4_konvergenz_aus_stoerung():
    L, w, h = 2.0, 4.0, 2.0
    m = 500.0 * L * w * h
    k = DummyKoerper([zentriere(quader_mesh(L, w, h))])
    erg = st.loese(_funktion(k), m, start=(0.5, np.radians(10.0)))
    assert abs(erg["phi"]) < 1e-4
    assert erg["restarts"] == 0


# ---------- P5: erschöpfte Leiter -> saubere Meldung ----------

def test_p5_budget_erschoepft_saubere_meldung():
    a = 2.0
    m = 500.0 * a**3
    k = DummyKoerper([zentriere(quader_mesh(a, a, a))])
    try:
        st.loese(_funktion(k), m, start=(0.5, 0.0), stoerleiter=())
        raise RuntimeError("haette werfen sollen")
    except st.SolverFehler:
        pass


# ---------- P6: Determinismus ----------

def test_p6_determinismus():
    L, w, h = 2.0, 4.0, 2.0
    m = 500.0 * L * w * h
    k = DummyKoerper([zentriere(quader_mesh(L, w, h))])
    f = _funktion(k)
    e1 = st.loese(f, m, start=(0.5, np.radians(7.0)))
    e2 = st.loese(f, m, start=(0.5, np.radians(7.0)))
    assert e1["z"] == e2["z"] and e1["phi"] == e2["phi"]
    assert e1["iterationen"] == e2["iterationen"]
