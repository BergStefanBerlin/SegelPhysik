"""Testblock J - Schritt 4 (K3 Materialglanz + K4 Tube-Overlays).

Jede Zahl analytisch hergeleitet oder gemessen (Projekt-Lektion).
Laeuft OHNE pyvista: die Rendering-Nahen Teile werden ueber die
deterministischen Helfer (glanz_kw, roehren_radius) geprueft.
"""
import json
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from segelphysik.core import konfig_lader as kl
from segelphysik.core.koerper import Koerper, GLANZ_DEFAULT
from segelphysik.core.fabriken import _specs_aus_konfig


def quader_mesh(dx, dy, dz, verschiebung=(0.0, 0.0, 0.0)):
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    punkte = np.array([[sx * hx, sy * hy, sz * hz]
                       for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
    punkte = punkte + np.asarray(verschiebung, float)
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 2, 6, 4),
             (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6)]
    dreiecke = []
    for q in quads:
        dreiecke.append([q[0], q[1], q[2]])
        dreiecke.append([q[0], q[2], q[3]])
    return punkte, np.asarray(dreiecke, np.int64)


def _konfig_aus_dict(m_dict, k_dict, tmp_path):
    ordner = str(tmp_path / "konfig")
    os.makedirs(ordner, exist_ok=True)
    with open(os.path.join(ordner, "materialien.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(m_dict, ensure_ascii=False))
    with open(os.path.join(ordner, "koerper.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(k_dict, ensure_ascii=False))
    return kl.lade_konfig(ordner)


MATERIALIEN_BASIS = {
    "_beschreibung": "Test",
    "materialien": {
        "GfK": {"dichte_kg_pro_m3": 1900, "farbe": "#1f4e79",
                "farbe_unter_wasser": "#7a8a99", "glanz": 0.35},
        "Stahl": {"dichte_kg_pro_m3": 7850, "farbe": "#4a4f55",
                  "farbe_unter_wasser": "#3a3e43", "glanz": 0.75},
        "Blei": {"dichte_kg_pro_m3": 11340, "farbe": "#23262a",
                 "farbe_unter_wasser": "#17191c", "glanz": 0.55},
        "Aluminium": {"dichte_kg_pro_m3": 2700, "farbe": "#c4c8cd",
                      "farbe_unter_wasser": "#9aa0a8", "glanz": 0.65},
    },
    "wasser": {"_einheit": "kg/m^3",
               "dichten_kg_pro_m3": {"Suesswasser": 1000, "Salzwasser": 1025},
               "standard": "Suesswasser"},
}

KOERPER_BASIS = {
    "_beschreibung": "Test",
    "summenkoerper": {"yacht1": {"teile": [
        {"name": "rumpf", "material": "GfK", "wanddicke_m": 0.005},
    ]}},
    "darstellung": {"delta_helligkeit_unterwasser": 0.4,
                    "farbe_standard": "#c9c9c9"},
}


def test_j1_glanz_wird_geladen(tmp_path):
    konfig = _konfig_aus_dict(MATERIALIEN_BASIS, KOERPER_BASIS, tmp_path)
    assert konfig.glanz_von("Stahl") == 0.75
    assert konfig.glanz_von("GfK") == 0.35


def test_j2_glanz_default_wenn_fehlt(tmp_path):
    m = json.loads(json.dumps(MATERIALIEN_BASIS))
    del m["materialien"]["Stahl"]["glanz"]
    konfig = _konfig_aus_dict(m, KOERPER_BASIS, tmp_path)
    assert konfig.glanz_von("Stahl") == kl.GLANZ_DEFAULT == 0.15


@pytest.mark.parametrize("wert", [-0.1, 1.1, "hoch", True])
def test_j3_glanz_validierung_verstoesse(wert, tmp_path):
    m = json.loads(json.dumps(MATERIALIEN_BASIS))
    m["materialien"]["Stahl"]["glanz"] = wert
    with pytest.raises(kl.KonfigFehler):
        _konfig_aus_dict(m, KOERPER_BASIS, tmp_path)


def test_j4_glanz_grenzen_erlaubt(tmp_path):
    m = json.loads(json.dumps(MATERIALIEN_BASIS))
    m["materialien"]["Stahl"]["glanz"] = 0
    m["materialien"]["GfK"]["glanz"] = 1
    konfig = _konfig_aus_dict(m, KOERPER_BASIS, tmp_path)
    assert konfig.glanz_von("Stahl") == 0.0
    assert konfig.glanz_von("GfK") == 1.0


def test_j5_blatt_glanz_default():
    p, f = quader_mesh(1.0, 1.0, 1.0)
    k = Koerper(form=(p, f), dichte=1000.0)
    assert k.glanz == GLANZ_DEFAULT == 0.15


def test_j6_blatt_glanz_explicit():
    p, f = quader_mesh(1.0, 1.0, 1.0)
    k = Koerper(form=(p, f), dichte=1000.0, glanz=0.9)
    assert k.glanz == 0.9


def test_j7_verband_blaetter_behalten_glanz():
    pa, fa = quader_mesh(1.0, 1.0, 1.0)
    pb, fb = quader_mesh(0.5, 0.5, 0.5, (0, 0, 2.0))
    a = Koerper(form=(pa, fa), dichte=1000.0, glanz=0.2)
    b = Koerper(form=(pb, fb), dichte=500.0, glanz=0.8)
    v = Koerper(teile=[(a, None), (b, None)])
    werte = sorted(kind.glanz for kind, _rel in v.teile)
    assert werte == [0.2, 0.8]


def test_j8_fabriken_reichen_glanz_durch(tmp_path, monkeypatch):
    """K3-Durchreichung; die OBJ-Abhaengigkeit wird per monkeypatch ersetzt
    (der Test prueft die Glanz-Durchreichung, nicht den OBJ-Lader)."""
    from segelphysik.core import boot_bau
    p_mesh, f_mesh = quader_mesh(1.0, 1.0, 1.0)
    monkeypatch.setattr(
        boot_bau, "baue_teil",
        lambda name, skala=1.0, ordner=None: (p_mesh.copy(), f_mesh.copy()))
    konfig = _konfig_aus_dict(MATERIALIEN_BASIS, KOERPER_BASIS, tmp_path)
    eintraege = [{"name": "rumpf", "material": "Stahl", "wanddicke_m": 0.005}]
    specs = _specs_aus_konfig(eintraege, konfig, skala=1.0, ordner="egal")
    assert specs[0]["glanz"] == 0.75
    eintraege2 = [{"name": "segel", "dichte_kg_pro_m3": 1250,
                   "farbe": "#fbfaf7", "farbe_unter_wasser": "#d9d7cf"}]
    specs2 = _specs_aus_konfig(eintraege2, konfig, skala=1.0, ordner="egal")
    assert "glanz" not in specs2[0]
    kwargs = {k: v for k, v in specs2[0].items()
              if not k.startswith("_") and k != "form"}
    k = Koerper(form=specs2[0]["form"], **kwargs)
    assert k.glanz == GLANZ_DEFAULT


def test_j9_glanz_kw_endpunkte_und_linearitaet():
    from segelphysik.grafik_bruecke import glanz_kw
    kw0 = glanz_kw(0.0)
    kw1 = glanz_kw(1.0)
    assert kw0["specular"] == 0.0 and kw0["specular_power"] == 15.0
    assert kw1["specular"] == 1.0 and kw1["specular_power"] == 130.0
    kw05 = glanz_kw(0.5)
    assert kw05["specular"] == 0.5
    assert kw05["specular_power"] == pytest.approx(72.5)
    assert kw05["pbr"] is False
    with pytest.raises(ValueError):
        glanz_kw(1.5)


def test_j10_farbgruppen_tragen_glanz():
    from segelphysik.grafik_bruecke import _farbgruppen
    pa, fa = quader_mesh(1.0, 1.0, 1.0)
    a = Koerper(form=(pa, fa), dichte=1000.0, glanz=0.42)
    gruppen = _farbgruppen(a)
    assert len(gruppen) == 1 and gruppen[0]["glanz"] == 0.42
    pb, fb = quader_mesh(0.5, 0.5, 0.5, (0, 0, 2.0))
    b = Koerper(form=(pb, fb), dichte=500.0, glanz=0.77)
    v = Koerper(teile=[(a, None), (b, None)])
    gruppen_v = _farbgruppen(v)
    assert sorted(g["glanz"] for g in gruppen_v) == [0.42, 0.77]


def test_w1_schalentensor_wuerfel_analytisch():
    """Offener Wuerfel (5 Flaechen, Kante a=1, fm=1): A = 5*a^2,
    r_z = -a/10; Tensor unabhaengig ueber Plattenformeln + Steiner."""
    from segelphysik.core.massen import traegheitstensor_flaechig, schwerpunkt_flaechig
    a = 1.0
    flaechen = [
        np.array([[-.5,-.5,-.5],[.5,-.5,-.5],[.5,.5,-.5],[-.5,.5,-.5]], float),
        np.array([[-.5,-.5,-.5],[.5,-.5,-.5],[.5,-.5,.5],[-.5,-.5,.5]], float),
        np.array([[-.5,.5,-.5],[.5,.5,-.5],[.5,.5,.5],[-.5,.5,.5]], float),
        np.array([[-.5,-.5,-.5],[-.5,.5,-.5],[-.5,.5,.5],[-.5,-.5,.5]], float),
        np.array([[.5,-.5,-.5],[.5,.5,-.5],[.5,.5,.5],[.5,-.5,.5]], float),
    ]
    punkte, dreiecke = [], []
    off = 0
    for quad in flaechen:
        idx = [off, off + 1, off + 2, off + 3]
        dreiecke += [[idx[0], idx[1], idx[2]], [idx[0], idx[2], idx[3]]]
        punkte += [list(q) for q in quad]
        off += 4
    punkte = np.asarray(punkte, float)
    dreiecke = np.asarray(dreiecke, np.int64)
    fm = 1.0
    r, A = schwerpunkt_flaechig(punkte, dreiecke)
    assert A == pytest.approx(5 * a * a)
    assert r[2] == pytest.approx(-0.1)
    I_ref = np.zeros((3, 3))
    mb = a * a * fm                       # Bodenplatte, Zentrum (0,0,-0.5)
    d_b = np.array([0.0, 0.0, -0.5]) - r  # = (0,0,-0.4)
    I_ref[0, 0] += mb * a * a / 12 + mb * (d_b[1]**2 + d_b[2]**2)
    I_ref[1, 1] += mb * a * a / 12 + mb * (d_b[0]**2 + d_b[2]**2)
    I_ref[2, 2] += mb * a * a / 6
    for sx, sy, sz in ((0, -.5, 0), (0, .5, 0), (-.5, 0, 0), (.5, 0, 0)):
        mw = a * a * fm                   # Seitenflaeche, Zentrum (sx,sy,0)
        d = np.array([sx, sy, sz]) - r    # z-Komponente ist +0.1, nicht -0.4!
        if abs(sy) > 0:                   # Normale y: Iyy = a^2/6 (Normalachse)
            Ixx, Iyy, Izz = mw * a * a / 12, mw * a * a / 6, mw * a * a / 12
        else:                             # Normale x: Ixx = a^2/6
            Ixx, Iyy, Izz = mw * a * a / 6, mw * a * a / 12, mw * a * a / 12
        I_ref[0, 0] += Ixx + mw * (d[1]**2 + d[2]**2)
        I_ref[1, 1] += Iyy + mw * (d[0]**2 + d[2]**2)
        I_ref[2, 2] += Izz + mw * (d[0]**2 + d[1]**2)
    J = traegheitstensor_flaechig(punkte, dreiecke, fm)
    np.testing.assert_allclose(np.diag(J), np.diag(I_ref), rtol=1e-10)
    np.testing.assert_allclose(J - np.diag(np.diag(J)), 0.0, atol=1e-12)


def test_schalentensor_bleibt_bei_grossen_absolutkoordinaten_stabil():
    from segelphysik.core.massen import (
        traegheitstensor_flaechig,
        validiere_traegheitstensor,
    )
    punkte = np.array([
        [0.0, 0.0, 0.0],
        [0.01, 0.0, 0.0],
        [0.01, 0.008, 0.002],
        [0.0, 0.008, 0.002],
    ])
    dreiecke = np.array([[0, 1, 2], [0, 2, 3]])
    versatz = np.array([0.2862, 0.016625, 5.13055])

    referenz = traegheitstensor_flaechig(punkte, dreiecke, 5.4)
    verschoben = traegheitstensor_flaechig(
        punkte + versatz, dreiecke, 5.4)

    np.testing.assert_allclose(verschoben, referenz, rtol=1e-12, atol=1e-20)
    validiere_traegheitstensor(verschoben)


def test_w2_glanz_kw_lineare_steigung():
    from segelphysik.grafik_bruecke import glanz_kw
    a, b = glanz_kw(0.2), glanz_kw(0.7)
    steigung_power = (b["specular_power"] - a["specular_power"]) / 0.5
    assert steigung_power == pytest.approx(115.0)
    steigung_spec = (b["specular"] - a["specular"]) / 0.5
    assert steigung_spec == pytest.approx(1.0)


def test_w3_roehrenradius_formel():
    """roehren_radius = max(0.25 * marker_radius, 0.006); Marker-Radius =
    clamp(0.04 * halbe_Ausdehnung, 0.02, 0.16)."""
    from segelphysik.grafik_bruecke import GrafikBruecke
    br = GrafikBruecke.__new__(GrafikBruecke)
    class P:
        pass
    p1 = P(); p1.punkte = np.array([[0.2, 0, 0]])
    assert GrafikBruecke.roehren_radius(br, p1) == pytest.approx(0.006)
    p2 = P(); p2.punkte = np.array([[2.0, 0, 0]])
    assert GrafikBruecke.roehren_radius(br, p2) == pytest.approx(0.02)


def test_w4_migration_alte_materialien_laden_ohne_glanz(tmp_path):
    """H7-artige Gegenprobe: der alte Stand (ohne 'glanz') laedt unveraendert."""
    m = json.loads(json.dumps(MATERIALIEN_BASIS))
    for block in m["materialien"].values():
        block.pop("glanz", None)
    konfig = _konfig_aus_dict(m, KOERPER_BASIS, tmp_path)
    for name in ("GfK", "Stahl", "Blei", "Aluminium"):
        assert konfig.glanz_von(name) == 0.15
