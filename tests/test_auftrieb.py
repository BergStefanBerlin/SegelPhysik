"""Block N (Phase A, Umsetzungsplan V5 rev 9): Auftrieb analytisch.
Konventionen (D11): z positiv nach oben, Wasserlinie der Welt bei z=0,
phi positiv nach Steuerbord, Momente positiv Richtung wachsendem phi.
Voxel-Toleranzen sind O(h*A) ehrlich gesetzt; die scharfen Referenzen
prueft der exakte Pfad (D10: Testreferenz).
"""
import os, json, sys
import numpy as np

sys.path.insert(0, os.getcwd())

from segelphysik.core import auftrieb as au
from segelphysik.core import konfig_lader as kl
from segelphysik.core.konfig_lader import KonfigFehler


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

def verschiebe(mesh, dx, dy, dz):
    v, f = mesh
    return v + np.array([dx, dy, dz]), f

class DummyKoerper:
    def __init__(self, blaetter, r_S=(0.0, 0.0, 0.0)):
        self.blatt_meshes = list(blaetter)
        self.r_S = np.array(r_S, dtype=float)

RHO_W = 1000.0
G = 9.80665
H = 0.05
VOX_TOL = 0.02


def test_n0a_synthetic_geschlossen():
    v, f = quader_mesh(2, 2, 2)
    ok, schlecht, vol = au.wasserdichtheit(v, f)
    assert ok and schlecht == 0
    assert abs(vol - 8.0) < 1e-9

def test_n0b_synthetic_offen():
    v, f = quader_mesh(2, 2, 2)
    ok, schlecht, _ = au.wasserdichtheit(v, f[:-1])
    assert (not ok) and schlecht > 0

def test_n0c_windung_inverse_negativ():
    v, f = quader_mesh(2, 2, 2)
    _ok, _schlecht, vol = au.wasserdichtheit(v, f[:, ::-1])
    assert abs(vol + 8.0) < 1e-9

def test_n1_quader_halb_getaucht():
    k = DummyKoerper([zentriere(quader_mesh(2, 2, 2))])
    erg_x = au.kraftfunktion_berechne(k, (0.0, 0.0, 0.0), pfad="exakt")
    assert abs(erg_x.V_tauch - 4.0) < 1e-9
    assert abs(erg_x.K.z - (-0.5)) < 1e-9
    assert abs(erg_x.K.x) < 1e-9 and abs(erg_x.K.y) < 1e-9
    erg = au.kraftfunktion_berechne(k, (0.0, 0.0, 0.0), aufloesung=H)
    assert abs(erg.V_tauch - 4.0) < VOX_TOL, erg.V_tauch
    assert abs(erg.K.z - (-0.5)) < 1e-6, erg.K.z

def test_n2_quader_vollstaendig_getaucht():
    v, f = zentriere(quader_mesh(2, 2, 2))
    v = v - np.array([0.0, 0.0, 2.0])
    k = DummyKoerper([(v, f)])
    erg_x = au.kraftfunktion_berechne(k, (0.0, 0.0, 0.0), pfad="exakt")
    assert abs(erg_x.V_tauch - 8.0) < 1e-9
    assert abs(erg_x.K.z - (-2.0)) < 1e-9
    erg = au.kraftfunktion_berechne(k, (0.0, 0.0, 0.0), aufloesung=H)
    assert abs(erg.V_tauch - 8.0) < VOX_TOL, erg.V_tauch
    assert abs(erg.K.z - (-2.0)) < 1e-6, erg.K.z

def test_n3_schwimmender_quader_restkraft_null():
    rho_k = 500.0
    k = DummyKoerper([zentriere(quader_mesh(2, 2, 2))])
    m = rho_k * 8.0
    erg = au.kraftfunktion_berechne(k, (0.0, 0.0, 0.0), rho_w=RHO_W,
                                    aufloesung=H)
    assert abs(erg.V_tauch - m / RHO_W) < VOX_TOL
    assert abs(erg.F_A.z - m * G) < VOX_TOL * RHO_W * G

def test_n4_gekraengter_ponton_stabilisierend():
    v, f = zentriere(quader_mesh(2.0, 4.0, 2.0))
    k = DummyKoerper([(v, f)])
    erg = au.kraftfunktion_berechne(k, (0.0, np.radians(10.0), 0.0),
                                    pfad="exakt")
    assert erg.V_tauch > 0.0
    assert erg.M.x < 0.0, "Ponton muss restaurieren (M_x<0 bei phi>0)"

def test_n5_instabiler_wuerfel_destabilisierend():
    v, f = zentriere(quader_mesh(2, 2, 2))
    k = DummyKoerper([(v, f)])
    phi = np.radians(10.0)
    erg = au.kraftfunktion_berechne(k, (0.0, phi, 0.0), pfad="exakt")
    assert erg.M.x > 0.0, "Wuerfel muss destabilisieren (M_x>0 bei phi>0)"
    GM, BM, V = -1.0/6.0, 1.0/3.0, 4.0
    m_ref = -RHO_W * G * V * (GM + 0.5 * BM * np.tan(phi)**2) * np.sin(phi)
    assert abs(erg.M.x - m_ref) < 0.03 * m_ref, (erg.M.x, m_ref)

def test_n6_segel_ueber_wasser_null():
    p = np.array([[0,0,3],[1,0,3],[0,0,5]], dtype=float)
    f = np.array([[0,1,2]], dtype=np.int64)
    k = DummyKoerper([(p, f)])
    for pfad in ("voxel", "exakt"):
        erg = au.kraftfunktion_berechne(k, (0.0, 0.0, 0.0), pfad=pfad)
        assert erg.V_tauch == 0.0 and erg.F_A.z == 0.0

def test_n7_additivitaet_disjunkt():
    # quader_mesh baut [0,a]^3: m1 -> z in [-2.5,-1.5] (komplett unter Wasser),
    # K1=(0.5,0.5,-2); m2 -> x+5, K2=(5.5,0.5,-2).
    m1 = verschiebe(quader_mesh(1, 1, 1), 0.0, 0.0, -2.5)
    m2 = verschiebe(quader_mesh(1, 1, 1), 5.0, 0.0, -2.5)
    gruppe = DummyKoerper([m1, m2])
    e_gx = au.kraftfunktion_berechne(gruppe, (0.0, 0.0, 0.0), pfad="exakt")
    assert abs(e_gx.V_tauch - 2.0) < 1e-9
    K_erw = (1.0 * np.array([0.5, 0.5, -2.0]) + 1.0 * np.array([5.5, 0.5, -2.0])) / 2.0
    assert np.allclose(np.array(e_gx.K.as_array()), K_erw, atol=1e-9), e_gx.K.as_array()
    e1 = au.kraftfunktion_berechne(DummyKoerper([m1]), (0.0, 0.0, 0.0),
                                   aufloesung=H)
    e2 = au.kraftfunktion_berechne(DummyKoerper([m2]), (0.0, 0.0, 0.0),
                                   aufloesung=H)
    e_g = au.kraftfunktion_berechne(gruppe, (0.0, 0.0, 0.0), aufloesung=H)
    assert abs(e_g.V_tauch - (e1.V_tauch + e2.V_tauch)) < 1e-9
    assert abs(e_g.F_A.z - (e1.F_A.z + e2.F_A.z)) < 1e-9

def test_n8_ueberlappung_union():
    # A=[0,2]^3 um z=-1 -> z in [-1,1]: HALB getaucht (getauchtes V=4 je Blatt,
    # K_z=-0.5). Getauchte Bereiche: A x[0,2] (K_x=1), B x[1,3] (K_x=2).
    # Union: nur-A x[0,1] V=2 (K_x=0.5), Schnitt x[1,2] V=2 (K_x=1.5),
    # nur-B x[2,3] V=2 (K_x=2.5) -> V_union=6, K_x=1.5, K_z=-0.5.
    # Exakter Pfad: Blattsumme 8 (dokumentiert die Doppelzaehlung).
    A = verschiebe(quader_mesh(2, 2, 2), 0.0, 0.0, -1.0)
    B = verschiebe(quader_mesh(2, 2, 2), 1.0, 0.0, -1.0)
    gruppe = DummyKoerper([A, B])
    erg = au.kraftfunktion_berechne(gruppe, (0.0, 0.0, 0.0), aufloesung=H)
    assert abs(erg.V_tauch - 6.0) < VOX_TOL, erg.V_tauch
    assert abs(erg.K.as_array()[0] - 1.5) < 1e-6, erg.K.as_array()[0]
    assert abs(erg.K.as_array()[2] - (-0.5)) < 1e-6, erg.K.as_array()[2]
    erg_x = au.kraftfunktion_berechne(gruppe, (0.0, 0.0, 0.0), pfad="exakt")
    assert abs(erg_x.V_tauch - 8.0) < 1e-9  # dokumentiert die Blatt-Doppelzaehlung

def test_n9_theta_wache():
    k = DummyKoerper([quader_mesh(1, 1, 1)])
    try:
        au.kraftfunktion_berechne(k, (0.0, 0.0, 0.05))
        raise RuntimeError("haette werfen sollen")
    except au.AuftriebFehler:
        pass

def test_n10_pfad_validierung():
    k = DummyKoerper([quader_mesh(1, 1, 1)])
    try:
        au.kraftfunktion_berechne(k, (0.0, 0.0, 0.0), pfad="magie")
        raise RuntimeError("haette werfen sollen")
    except au.AuftriebFehler:
        pass

def test_n11_binding_f19():
    k = DummyKoerper([zentriere(quader_mesh(2, 2, 2))])
    fk = au.baue_kraftfunktion(k, rho_w=RHO_W, aufloesung=H)
    erg = fk((0.0, 0.0, 0.0), v=np.zeros(3), omega=np.zeros(3))
    assert abs(erg.V_tauch - 4.0) < VOX_TOL, erg.V_tauch
    erg2 = fk((0.0, 0.0, 0.0))
    assert erg2.V_tauch == erg.V_tauch

def test_n17_verband_echter_koerper():
    try:
        from segelphysik.core.koerper import Koerper
    except ImportError:
        print("   N17 uebersprungen (Koerper-Klasse nicht verfuegbar)")
        return
    w1 = Koerper(form=quader_mesh(1, 1, 1), dichte=500.0)
    w2 = Koerper(form=quader_mesh(1, 1, 1), dichte=500.0)
    verband = Koerper(teile=[
        (w1, (np.eye(3), np.array([-3.0, 0.0, -2.5]))),
        (w2, (np.eye(3), np.array([ 3.0, 0.0, -2.5]))),
    ])
    assert abs(verband.masse - 1000.0) < 1e-9
    # P1: der Verband lebt im SCHWERPUNKTFRAME - r_S liegt im Ursprung, die
    # Wuerfel (je 500 kg, Zentren +/-3 in x) sind damit bei z=0 zentriert und
    # HALB getaucht: V_tauch = 1.0 (Gleichgewicht: m=1000 kg <-> rho_W*V),
    # K_z = -0.25 (getauchte Haelften z in [-0.5,0]).
    fk = au.baue_kraftfunktion(verband, rho_w=RHO_W, aufloesung=H)
    erg = fk((0.0, 0.0, 0.0))
    assert abs(erg.V_tauch - 1.0) < VOX_TOL, erg.V_tauch
    assert abs(erg.K.as_array()[0]) < 1e-6
    assert abs(erg.K.as_array()[2] - (-0.25)) < 1e-6, erg.K.as_array()[2]
    assert abs(erg.F_A.z - 1000.0 * G) < VOX_TOL * RHO_W * G

def _schreibe(ordner, inhalt):
    os.makedirs(ordner, exist_ok=True)
    with open(os.path.join(ordner, "physik.json"), "w", encoding="utf-8") as f:
        f.write(inhalt)

GUELTIG = json.dumps({"physik": {
    "dt_s": 0.004, "g_m_pro_s2": 9.80665,
    "daempfung": {"tauchung": 8000.0, "kraengung": 8000.0},
    "voxel": {"aufloesung_m": 0.05, "schranke_volumen_m3": 0.0005,
              "schranke_punkt_m": 0.005}}})

def test_n12_physik_laadt():
    _schreibe("tmp_physik_ok", GUELTIG)
    p = kl.lade_physik("tmp_physik_ok")
    assert p.dt_s == 0.004 and p.g_m_pro_s2 == 9.80665
    assert p.daempfung_tauchung == 8000.0 and p.daempfung_kraengung == 8000.0
    assert p.voxel_aufloesung_m == 0.05
    assert p.schranke_volumen_m3 == 0.0005 and p.schranke_punkt_m == 0.005

def test_n13_physik_fremder_schluessel():
    _schreibe("tmp_physik_fremd", json.dumps({"physik": {
        "dt_s": 0.01, "g_m_pro_s2": 9.80665, "zauber": 1,
        "daempfung": {"tauchung": 1, "kraengung": 1},
        "voxel": {"aufloesung_m": 0.1, "schranke_volumen_m3": 0.001,
                  "schranke_punkt_m": 0.01}}}))
    try:
        kl.lade_physik("tmp_physik_fremd")
        raise RuntimeError("haette werfen sollen")
    except KonfigFehler:
        pass

def test_n14_physik_negatives_dt():
    _schreibe("tmp_physik_neg", json.dumps({"physik": {
        "dt_s": -0.01, "g_m_pro_s2": 9.80665,
        "daempfung": {"tauchung": 1, "kraengung": 1},
        "voxel": {"aufloesung_m": 0.1, "schranke_volumen_m3": 0.001,
                  "schranke_punkt_m": 0.01}}}))
    try:
        kl.lade_physik("tmp_physik_neg")
        raise RuntimeError("haette werfen sollen")
    except KonfigFehler:
        pass

def test_n15_physik_fehlt_kein_fallback():
    try:
        kl.lade_physik("tmp_gibts_nicht")
        raise RuntimeError("haette werfen sollen")
    except KonfigFehler:
        pass

def test_n16_vorlage_selbst_gueltig():
    with open(os.path.join("doc", "physik_vorlage.json"), encoding="utf-8") as f:
        d = json.load(f)
    w = kl._val_physik(d, "vorlage")
    assert w["dt_s"] > 0 and w["g_m_pro_s2"] == 9.80665
