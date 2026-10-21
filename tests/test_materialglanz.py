"""Materialglanz: Konfiguration, Koerper und Grafikadapter (historisch J/K3).

Jede Zahl analytisch hergeleitet oder gemessen (Projekt-Lektion).
Laeuft ohne Plotter: Rendering-Parameter werden ueber glanz_kw geprueft.
"""
import json
import os
import pytest

from segelphysik.core import konfig_lader as kl
from segelphysik.core.koerper import Koerper, GLANZ_DEFAULT
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.fabriken import _specs_aus_konfig


def quader_mesh(dx, dy, dz, verschiebung=(0.0, 0.0, 0.0)):
    punkte, dreiecke = build_box(dx, dy, dz)
    return punkte + verschiebung, dreiecke


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
def test_w2_glanz_kw_lineare_steigung():
    from segelphysik.grafik_bruecke import glanz_kw
    a, b = glanz_kw(0.2), glanz_kw(0.7)
    steigung_power = (b["specular_power"] - a["specular_power"]) / 0.5
    assert steigung_power == pytest.approx(115.0)
    steigung_spec = (b["specular"] - a["specular"]) / 0.5
    assert steigung_spec == pytest.approx(1.0)
def test_w4_migration_alte_materialien_laden_ohne_glanz(tmp_path):
    """H7-artige Gegenprobe: der alte Stand (ohne 'glanz') laedt unveraendert."""
    m = json.loads(json.dumps(MATERIALIEN_BASIS))
    for block in m["materialien"].values():
        block.pop("glanz", None)
    konfig = _konfig_aus_dict(m, KOERPER_BASIS, tmp_path)
    for name in ("GfK", "Stahl", "Blei", "Aluminium"):
        assert konfig.glanz_von(name) == 0.15
