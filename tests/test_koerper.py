"""Testfaelle V4 (doc/Testfaelle_v4.md) - Bloecke A bis E plus F4.

Referenzwerte sind analytisch bzw. unabhaengig berechnet (nie mit der
getesteten Funktion selbst). Determinismus: feste Seeds, keine Zeitbezuege.
"""
import json
import math
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from segelphysik.core import boot_bau
from segelphysik.core import fabriken
from segelphysik.core import koerper_formen as formen
from segelphysik.core import massen as ma
from segelphysik.core.koerper import Koerper, KoerperFehler, helle_auf
from segelphysik.core.konfig_lader import KonfigFehler, lade_konfig

KONFIG_ORDNER = os.path.join(ROOT, "konfigurationen")
MAT_VORLAGE = os.path.join(ROOT, "doc", "materialien_vorlage.json")
KOR_VORLAGE = os.path.join(ROOT, "doc", "koerper_vorlage.json")
YACHT = fabriken.YACHT_ORDNER


@pytest.fixture(scope="module")
def konfig():
    return lade_konfig(KONFIG_ORDNER)


@pytest.fixture(scope="module")
def mat_vorlage():
    with open(MAT_VORLAGE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def kor_vorlage():
    with open(KOR_VORLAGE, encoding="utf-8") as f:
        return json.load(f)


def _temp_konfig(tmp_path, mat, kor):
    """Schreibt beide Dateien in einen temporaeren Ordner (Schema-Reform)."""
    with open(os.path.join(str(tmp_path), "materialien.json"), "w",
              encoding="utf-8") as f:
        json.dump(mat, f)
    with open(os.path.join(str(tmp_path), "koerper.json"), "w",
              encoding="utf-8") as f:
        json.dump(kor, f)
    return str(tmp_path)


def _kopie(vorlage):
    return json.loads(json.dumps(vorlage))


# ---------------- Block A: Konfig-Lader (Spec J, Schema-Reform) ----------------

def test_tc_a1_arbeitsdateien_entsprechen_vorlagen(konfig, mat_vorlage, kor_vorlage):
    assert konfig.materialien == mat_vorlage["materialien"]
    assert konfig.wasser_dichten == mat_vorlage["wasser"]["dichten_kg_pro_m3"]
    assert konfig.farbe_standard == kor_vorlage["darstellung"]["farbe_standard"]
    assert konfig.delta_helligkeit == kor_vorlage["darstellung"]["delta_helligkeit_unterwasser"]


def test_tc_a2_fehlende_datei_kein_stiller_fallback(tmp_path):
    with pytest.raises(KonfigFehler) as info:
        lade_konfig(str(tmp_path))
    assert "Vorlage" in str(info.value)


def test_tc_a3_doppelschluessel_wird_erkannt(tmp_path, mat_vorlage, kor_vorlage):
    text = '{"materialien": {"Blei": 1, "Blei": 11340}, "wasser": {"dichten_kg_pro_m3": {"S": 1000}, "standard": "S"}}'
    od = _temp_konfig(tmp_path, mat_vorlage, kor_vorlage)
    with open(os.path.join(od, "materialien.json"), "w", encoding="utf-8") as f:
        f.write(text)
    with pytest.raises(KonfigFehler) as info:
        lade_konfig(od)
    assert "Doppelter" in str(info.value)


def test_tc_a4_unbekanntes_material_cross_file(tmp_path, mat_vorlage, kor_vorlage):
    kor = _kopie(kor_vorlage)
    for e in kor["boot"]["teile"]:
        if e["name"] == "rumpf":
            e["material"] = "Unobtainium"
    od = _temp_konfig(tmp_path, mat_vorlage, kor)
    with pytest.raises(KonfigFehler) as info:
        lade_konfig(od)
    assert "Unobtainium" in str(info.value)


def test_tc_a5_gruppe_mit_masse_fehler(tmp_path, mat_vorlage, kor_vorlage):
    kor = _kopie(kor_vorlage)
    for e in kor["boot"]["teile"]:
        if e["name"] == "kielsystem":
            e["dichte"] = 500.0
    od = _temp_konfig(tmp_path, mat_vorlage, kor)
    with pytest.raises(KonfigFehler) as info:
        lade_konfig(od)
    assert "P2.5" in str(info.value)


def test_tc_a6_blatt_ohne_material_fehler(tmp_path, mat_vorlage, kor_vorlage):
    kor = _kopie(kor_vorlage)
    for e in kor["boot"]["teile"]:
        if e["name"] == "rumpf":
            del e["material"]
    od = _temp_konfig(tmp_path, mat_vorlage, kor)
    with pytest.raises(KonfigFehler) as info:
        lade_konfig(od)
    assert "material" in str(info.value)


def test_tc_a7_fremder_massenschluessel_fehler(tmp_path, mat_vorlage, kor_vorlage):
    kor = _kopie(kor_vorlage)
    for e in kor["boot"]["teile"]:
        if e["name"] == "rumpf":
            e["flaechenmasse_kg_pro_m2"] = 9.5
    od = _temp_konfig(tmp_path, mat_vorlage, kor)
    with pytest.raises(KonfigFehler) as info:
        lade_konfig(od)
    assert "unzulaessiger Massenschluessel" in str(info.value)


def test_tc_a8_leere_gruppe_fehler(tmp_path, mat_vorlage, kor_vorlage):
    kor = _kopie(kor_vorlage)
    for e in kor["boot"]["teile"]:
        if e["name"] == "rigg":
            e["teile"] = []
    od = _temp_konfig(tmp_path, mat_vorlage, kor)
    with pytest.raises(KonfigFehler) as info:
        lade_konfig(od)
    assert "leer" in str(info.value)


def test_tc_a9_direkte_dichte_zahl_zulaessig(tmp_path, mat_vorlage, kor_vorlage):
    kor = _kopie(kor_vorlage)
    for e in kor["boot"]["teile"]:
        if e["name"] == "kielsystem":
            for kind in e["teile"]:
                if kind["name"] == "bulb":
                    kind["material"] = 11340
    od = _temp_konfig(tmp_path, mat_vorlage, kor)
    k = lade_konfig(od)
    assert k.dichte_von(11340) == 11340.0


# ---------------- Block B: Massen einzelner Koerper ----------------

def test_tc_b1_quader_exakt():
    v, f = formen.bau_quader(2.0, 2.0, 2.0)
    k = Koerper(form=(v, f), dichte=1000.0)
    assert abs(k.masse - 8000.0) < 1e-9
    assert np.max(np.abs(k.punkte.mean(axis=0))) < 1e-9      # r_S = Mitte (AK-P1a)
    assert abs(ma.mesh_volumen(k.punkte, k.dreiecke) - 8.0) < 1e-12


def test_tc_b2_kegel_masse_und_com_shift():
    v, f = formen.bau_kegel(H=2.0, R=1.0)
    k = Koerper(form=(v, f), dichte=1000.0)
    n = 64
    v_ref = (1.0 / 3.0) * (n / 2.0) * 1.0 * math.sin(2 * math.pi / n) * 2.0
    assert abs(k.masse - 1000.0 * v_ref) < 1e-6
    # COM-Shift-Eigenschaft (P1): Eingabe verschieben verschiebt _r_eingabe mit,
    # der Schwerpunktframe bleibt unveraendert (V3-Kegel ist COM-zentriert).
    k2 = Koerper(form=(v + np.array([0.0, 0.0, 10.0]), f), dichte=1000.0)
    assert abs(k2._r_eingabe[2] - 10.0) < 1e-9
    assert np.max(np.abs(k2.punkte - k.punkte)) < 1e-12


def test_tc_b3_tensor_quader_analytisch():
    v, f = formen.bau_quader(1.0, 2.0, 3.0)
    k = Koerper(form=(v, f), dichte=1000.0)
    m = 6000.0
    assert abs(k.traegheitstensor[0, 0] - m * 13 / 12) < 1e-6
    assert abs(k.traegheitstensor[1, 1] - m * 10 / 12) < 1e-6
    assert abs(k.traegheitstensor[2, 2] - m * 5 / 12) < 1e-6
    assert np.max(np.abs(k.traegheitstensor - np.diag(np.diag(k.traegheitstensor)))) < 1e-6


def test_tc_b4_symmetrie_wuerfel_und_kegel():
    v, f = formen.bau_quader(2.0, 2.0, 2.0)
    k = Koerper(form=(v, f), dichte=1000.0)
    d = np.diag(k.traegheitstensor)
    assert np.max(np.abs(d - d.mean())) < 1e-6 * d.mean()
    vk, fk = formen.bau_kegel(H=2.0, R=1.0)
    kk = Koerper(form=(vk, fk), dichte=1000.0)
    m = kk.masse
    assert abs(kk.traegheitstensor[2, 2] - 3 * m * 1.0 / 10) < 0.01 * 3 * m / 10


def test_tc_b5_flaechenmasse_segelflaeche():
    s = math.sqrt(10.0)
    v = np.array([[0, -s / 2, -s / 2], [0, s / 2, -s / 2],
                  [0, s / 2, s / 2], [0, -s / 2, s / 2]], float)
    f = np.array([[0, 1, 2], [0, 2, 3]])
    k = Koerper(form=(v, f), flaechenmasse=0.5)
    assert abs(k.masse - 5.0) < 1e-12                        # AK-P3d
    assert abs(ma.mesh_volumen(v, f)) < 1e-12


def test_tc_b6_volumenlos_mit_dichte_fehler():
    s = 2.0
    v = np.array([[0, -s / 2, -s / 2], [0, s / 2, -s / 2],
                  [0, s / 2, s / 2], [0, -s / 2, s / 2]], float)
    f = np.array([[0, 1, 2], [0, 2, 3]])
    with pytest.raises(KoerperFehler) as info:
        Koerper(form=(v, f), dichte=1000.0)
    assert "flaechenmasse" in str(info.value)


def test_tc_b7_genau_eins_regel():
    v, f = formen.bau_quader(1.0, 1.0, 1.0)
    with pytest.raises(KoerperFehler):
        Koerper(form=(v, f), masse=1.0, dichte=1.0)
    with pytest.raises(KoerperFehler):
        Koerper(form=(v, f))


def test_tc_b8_material_aufloesung(konfig):
    p, fv = boot_bau.baue_teil("bulb", ordner=YACHT)
    k1 = Koerper(form=(p, fv), material="Blei", materialien=konfig.materialien)
    k2 = Koerper(form=(p, fv), dichte=konfig.materialien["Blei"])
    assert abs(k1.masse - k2.masse) < 1e-9
    assert abs(k1.masse - konfig.materialien["Blei"] * abs(ma.mesh_volumen(p, fv))) < 1e-6


def test_tc_b9_flaechentensor_platte_analytisch():
    # Platte s=2 in der xy-Ebene, fm=3 -> m=12; I_z = m*s^2/6 = 8, I_x = I_y = 4
    v = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], float)
    f = np.array([[0, 1, 2], [0, 2, 3]])
    k = Koerper(form=(v, f), flaechenmasse=3.0)
    assert abs(k.masse - 12.0) < 1e-12
    I = k.traegheitstensor
    assert abs(I[2, 2] - 8.0) < 1e-9
    assert abs(I[0, 0] - 4.0) < 1e-9 and abs(I[1, 1] - 4.0) < 1e-9
    assert np.max(np.abs(I - np.diag(np.diag(I)))) < 1e-9


def test_tc_b10_flaechentensor_hohlwuerfel_analytisch():
    # Hohlwuerfel a=2, fm=1 -> m=24; I = 5*m*a^2/18 = 80/3 (exakt, alle Achsen gleich)
    s = 1.0
    ecken = [(-s,-s,-s),(s,-s,-s),(s,s,-s),(-s,s,-s),
             (-s,-s,s),(s,-s,s),(s,s,s),(-s,s,s)]
    quads = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(2,3,7,6),(0,3,7,4),(1,2,6,5)]
    tris = []
    for q in quads:
        tris += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    v = np.array(ecken, float); f = np.array(tris, np.int64)
    k = Koerper(form=(v, f), flaechenmasse=1.0)
    assert abs(k.masse - 24.0) < 1e-9
    I = k.traegheitstensor
    assert abs(I[0, 0] - 80.0 / 3.0) < 1e-9
    assert np.max(np.abs(I - np.diag(np.diag(I)))) < 1e-9


# ---------------- Block C: Rekursion (P2) ----------------

def _zwei_teile():
    vg, fg = formen.bau_quader(2.0, 2.0, 2.0)
    vk, fk = formen.bau_quader(1.0, 1.0, 1.0)
    return (vg, fg), (vk, fk)


def test_tc_c1_c2_zweiteilkoerper_parallel_achsen():
    (vg, fg), (vk, fk) = _zwei_teile()
    specs = [{"form": (vg + np.array([2.0, 0, 0]), fg), "dichte": 1000.0},
             {"form": (vk + np.array([-1.0, 0, 0]), fk), "dichte": 1000.0}]
    k = Koerper.verband(specs)
    assert abs(k.masse - 9000.0) < 1e-9
    ixx = 8000 * 8 / 12 + 1000 * 2 / 12
    iyy = ixx + 8000 * (1 / 3) ** 2 + 1000 * (8 / 3) ** 2
    assert abs(k.traegheitstensor[0, 0] - ixx) < 1e-6
    assert abs(k.traegheitstensor[1, 1] - iyy) < 1e-6


def test_tc_c3_tensor_rotation():
    v, f = formen.bau_quader(1.0, 2.0, 3.0)
    kind = Koerper(form=(v, f), dichte=1000.0)
    w = math.pi / 2
    Rz = np.array([[math.cos(w), -math.sin(w), 0],
                   [math.sin(w), math.cos(w), 0], [0, 0, 1]])
    verband = Koerper(teile=[(kind, (Rz, np.zeros(3)))])
    gedreht = Koerper(form=(v @ Rz.T, f), dichte=1000.0)
    assert np.max(np.abs(verband.traegheitstensor - gedreht.traegheitstensor)) < 1e-6


def test_tc_c4_gruppe_gleich_summe(konfig):
    baum = fabriken._specs_aus_konfig(konfig.boot_teile, konfig,
                                      boot_bau.SKALA, YACHT)
    kielsystem = next(s for s in baum if "teile" in s)       # erste Gruppe
    gruppe = Koerper.verband([kielsystem])
    flach = Koerper.verband(kielsystem["teile"])
    assert abs(gruppe.masse - flach.masse) < 1e-9
    assert np.max(np.abs(gruppe.traegheitstensor - flach.traegheitstensor)) < 1e-9


def test_tc_c5_flach_gleich_gruppiert_gesamtboot(konfig):
    baum = fabriken._specs_aus_konfig(konfig.boot_teile, konfig,
                                      boot_bau.SKALA, YACHT)
    flach_specs = []

    def flach_machen(specs):
        for s in specs:
            if "teile" in s:
                flach_machen(s["teile"])
            else:
                flach_specs.append(s)

    flach_machen(baum)
    gruppiert = Koerper.verband(baum)
    flach = Koerper.verband(flach_specs)
    assert abs(gruppiert.masse - flach.masse) < 1e-9
    assert np.max(np.abs(gruppiert.traegheitstensor - flach.traegheitstensor)) < 1e-9
    assert np.max(np.abs(gruppiert.punkte.min(0) - flach.punkte.min(0))) < 1e-9
    assert np.max(np.abs(gruppiert.punkte.max(0) - flach.punkte.max(0))) < 1e-9


def test_tc_c7_schwerpunktframe_invariante(konfig):
    boot, _r = fabriken.baue_boot(konfig)
    mr = sum(m * r for m, r in boot.teil_aggregate())
    assert np.max(np.abs(mr)) < 1e-6          # Summe m_i*r_i = 0 (P1-Invariante)


# ---------------- Block D: Boot ----------------

def test_tc_d1_boot_acht_teile_aus_konfiguration(konfig):
    boot, _r = fabriken.baue_boot(konfig)
    blaetter = []

    def sammle(x):
        if not x.teile:
            blaetter.append(x)
        for kind, _rel in x.teile:
            sammle(kind)

    sammle(boot)
    assert len(blaetter) == 8


def test_tc_d2_boot_rs_unter_geometrischer_mitte(konfig):
    boot, r_modell = fabriken.baue_boot(konfig)
    alle = [boot_bau.baue_teil(n, ordner=YACHT)[0] for n in
            ("rumpf", "ruder", "kiel", "bulb", "mast", "boom",
             "grosssegel", "fock")]
    pa = np.vstack(alle)
    z_geo = (pa[:, 2].min() + pa[:, 2].max()) / 2.0
    assert r_modell[2] < z_geo                # Schalenrumpf: CM liegt unter der geometrischen Mitte (AK-P1d)


def test_tc_d3_boot_masse_unabhaengige_referenz(konfig):
    boot, _r = fabriken.baue_boot(konfig)

    def vol(p, t):
        p0, p1, p2 = p[t[:, 0]], p[t[:, 1]], p[t[:, 2]]
        return float(np.sum(np.einsum("ij,ij->i", p0, np.cross(p1, p2))) / 6.0)

    def flaeche(p, t):
        p0, p1, p2 = p[t[:, 0]], p[t[:, 1]], p[t[:, 2]]
        return float(0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1).sum())

    mat = konfig.materialien
    FM_GFK = mat["GfK"] * 0.005          # 5 mm GfK-Laminate (fm = rho*t, Spec P3)
    FM_ALU_WAND = mat["Aluminium"] * 0.002   # 2 mm Alu-Wand (Hohlprofil)
    erwartung = 0.0
    for name in ("rumpf", "ruder"):
        p, t = boot_bau.baue_teil(name, ordner=YACHT)
        erwartung += FM_GFK * flaeche(p, t)
    for name, rho in (("kiel", mat["Stahl"]), ("bulb", mat["Blei"])):
        p, t = boot_bau.baue_teil(name, ordner=YACHT)
        erwartung += rho * abs(vol(p, t))
    for name in ("mast", "boom"):
        p, t = boot_bau.baue_teil(name, ordner=YACHT)
        erwartung += FM_ALU_WAND * flaeche(p, t)
    for name in ("grosssegel", "fock"):
        p, t = boot_bau.baue_teil(name, ordner=YACHT)
        erwartung += 0.5 * flaeche(p, t)
    assert abs(boot.masse - erwartung) < 1e-6
    einzeln = {}
    for name in ("rumpf", "ruder"):
        p, t = boot_bau.baue_teil(name, ordner=YACHT)
        einzeln[name] = FM_GFK * flaeche(p, t)
    for name, rho in (("kiel", mat["Stahl"]), ("bulb", mat["Blei"])):
        p, t = boot_bau.baue_teil(name, ordner=YACHT)
        einzeln[name] = rho * abs(vol(p, t))
    for name in ("mast", "boom"):
        p, t = boot_bau.baue_teil(name, ordner=YACHT)
        einzeln[name] = FM_ALU_WAND * flaeche(p, t)
    assert max(einzeln, key=einzeln.get) == "kiel"
    assert einzeln["rumpf"] > einzeln["bulb"] > einzeln["mast"]


def test_tc_d4_segeln_sind_flaechenkoerper(konfig):
    boot, _r = fabriken.baue_boot(konfig)
    segel = []

    def sammle(x):
        if not x.teile and x._volumen is not None and x._volumen < 1e-12:
            segel.append(x)
        for kind, _rel in x.teile:
            sammle(kind)

    sammle(boot)
    assert len(segel) == 2                    # grosssegel + fock
    for s in segel:
        assert s._flaeche > 0.0


def test_tc_d5_schalenboot_kennzahlen(konfig):
    """Kennzahlen des Schalenboots (gemessen, Hohlprofil-Modell)."""
    boot, r_modell = fabriken.baue_boot(konfig)
    assert abs(boot.masse - 459.4368) < 0.01      # Gesamtmasse (gemessen)
    assert r_modell[2] < 0.0                       # CM unter der Wasserlinie
    assert abs(r_modell[2] - (-0.494574)) < 0.001  # CM-Tiefe (gemessen)
    d = np.diag(boot.traegheitstensor)
    assert abs(d[0] - 243.990) < 0.05
    assert abs(d[1] - 427.215) < 0.05
    assert abs(d[2] - 220.610) < 0.05



# ---------------- Block E: Farbe (P4) ----------------

def test_tc_e1_default_aufhellung_lightness_25():
    referenz = helle_auf("#c9c9c9", 0.25)
    l = 201.0 / 255.0
    l_neu = l + 0.25 * (1.0 - l)              # Spec P4: "Lightness +25%"
    erwartet = "#" + "%02x" % int(l_neu * 255.0 + 0.5) * 3
    assert referenz == erwartet
    assert referenz != "#c9c9c9"              # gut sichtbar heller
    assert helle_auf("#000000", 1.0) == "#ffffff"


def test_tc_e2_beide_farben_gesetzt():
    v, f = formen.bau_quader(1.0, 1.0, 1.0)
    k = Koerper(form=(v, f), dichte=1000.0, farbe="#123456",
                farbe_unter_wasser="#654321")
    assert k.farbe == "#123456"
    assert k.unterwasser_farbe() == "#654321"


def test_tc_e3_default_farbe_aus_konfig(konfig):
    k = fabriken.baue_kegel(konfig)
    assert k.farbe == konfig.farbe_standard == "#c9c9c9"


def test_tc_e4_delta_aus_konfig(tmp_path, mat_vorlage, kor_vorlage):
    kor = _kopie(kor_vorlage)
    kor["darstellung"]["delta_helligkeit_unterwasser"] = 0.4
    k4 = lade_konfig(_temp_konfig(tmp_path, mat_vorlage, kor))
    k = fabriken.baue_kegel(k4)
    assert k.delta_helligkeit == 0.4
    assert k.unterwasser_farbe() == helle_auf("#c9c9c9", 0.4)


# ---------------- Block F: Regression ----------------

def test_tc_f4_keine_stillen_duplikate(konfig, mat_vorlage, kor_vorlage):
    assert konfig.materialien == mat_vorlage["materialien"]
    assert konfig.wasser_dichten == mat_vorlage["wasser"]["dichten_kg_pro_m3"]
    assert konfig.farbe_standard == kor_vorlage["darstellung"]["farbe_standard"]
    assert konfig.delta_helligkeit == kor_vorlage["darstellung"]["delta_helligkeit_unterwasser"]
