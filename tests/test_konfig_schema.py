"""Block H - Schema-Reform: zwei Konfig-Dateien, material+wanddicke_m."""
import json, os, tempfile
from segelphysik.core.konfig_lader import lade_konfig, KonfigFehler
import pytest

def _schreibe(ordner, mat, kor):
    with open(os.path.join(ordner, "materialien.json"), "w", encoding="utf-8") as f:
        json.dump(mat, f)
    with open(os.path.join(ordner, "koerper.json"), "w", encoding="utf-8") as f:
        json.dump(kor, f)

def _basis():
    mat = {"materialien": {"Test": {"dichte_kg_pro_m3": 1000, "farbe": "#cccccc", "farbe_unter_wasser": "#999999"}},
           "wasser": {"dichten_kg_pro_m3": {"Suess": 1000}, "standard": "Suess"}}
    kor = {"boot": {"teile": [{"name": "wuerfel", "material": "Test"}]},
           "darstellung": {"delta_helligkeit_unterwasser": 0.4,
                           "farbe_standard": "#c9c9c9"}}
    return mat, kor

def test_h1_zahl_als_material_abgeschafft():
    """Die alte Syntax material=<Zahl> ist seit der Reform ein Fehler."""
    with tempfile.TemporaryDirectory() as od:
        mat, kor = _basis()
        kor["boot"]["teile"][0]["material"] = 1250
        _schreibe(od, mat, kor)
        with pytest.raises(KonfigFehler):
            lade_konfig(od)


def test_h2_zahl_mit_wanddicke_abgeschafft():
    """Auch material=<Zahl> + wanddicke_m ist abgeschafft (Tripel gilt)."""
    with tempfile.TemporaryDirectory() as od:
        mat, kor = _basis()
        kor["boot"]["teile"][0].update({"material": 1250, "wanddicke_m": 0.0004})
        _schreibe(od, mat, kor)
        with pytest.raises(KonfigFehler):
            lade_konfig(od)


def test_h3_fremder_massenschluessel_fehler():
    with tempfile.TemporaryDirectory() as od:
        mat, kor = _basis()
        kor["boot"]["teile"][0]["flaechenmasse_kg_pro_m2"] = 0.5
        _schreibe(od, mat, kor)
        try:
            lade_konfig(od); assert False, "KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_h4_unbekanntes_material_cross_file():
    with tempfile.TemporaryDirectory() as od:
        mat, kor = _basis()
        kor["boot"]["teile"][0]["material"] = "Unobtainium"
        _schreibe(od, mat, kor)
        try:
            lade_konfig(od); assert False, "KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_h5_doppelter_schluessel_beide_dateien():
    with tempfile.TemporaryDirectory() as od:
        mat, kor = _basis()
        roh = '{"materialien": {"A": 1, "A": 2}, "wasser": {"dichten_kg_pro_m3": {"S": 1000}, "standard": "S"}}'
        with open(os.path.join(od, "materialien.json"), "w", encoding="utf-8") as f:
            f.write(roh)
        with open(os.path.join(od, "koerper.json"), "w", encoding="utf-8") as f:
            json.dump(kor, f)
        try:
            lade_konfig(od); assert False, "KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_h6_gruppe_mit_masseschluessel_fehler():
    with tempfile.TemporaryDirectory() as od:
        mat, kor = _basis()
        kor["boot"]["teile"][0] = {"name": "g", "material": "Test",
                                   "teile": [{"name": "a", "material": "Test"}]}
        _schreibe(od, mat, kor)
        try:
            lade_konfig(od); assert False, "KonfigFehler erwartet"
        except KonfigFehler:
            pass
