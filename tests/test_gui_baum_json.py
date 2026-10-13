# -*- coding: utf-8 -*-
"""G2: Baum aus der echten koerper.json (Struktur, Eigenschaften, Regeln)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from segelphysik.gui.baum import (  # noqa: E402
    welt_aus_json, ART_SUMMEN, ART_GRUPPE, ART_BLATT,
    sichtbarkeit_setzen, blatt_setzen, finde, aktive_blaetter,
)

_JSON = {
    "_beschreibung": "Test-Stellvertreter der echten Datei",
    "boot": {
        "teile": [
            {"name": "rumpf", "material": "GfK", "wanddicke_m": 0.005},
            {"name": "ruder", "material": "GfK", "wanddicke_m": 0.005},
            {"name": "kielsystem", "teile": [
                {"name": "kiel", "material": "Stahl"},
                {"name": "bulb", "material": "Blei"},
            ]},
            {"name": "rigg", "teile": [
                {"name": "mast", "material": "Aluminium",
                 "wanddicke_m": 0.002},
                {"name": "boom", "material": "Aluminium",
                 "wanddicke_m": 0.002},
                {"name": "grosssegel", "dichte_kg_pro_m3": 1250,
                 "farbe": "#fbfaf7", "wanddicke_m": 0.0004},
                {"name": "fock", "dichte_kg_pro_m3": 1250,
                 "farbe": "#fbfaf7", "wanddicke_m": 0.0004},
            ]},
        ]
    },
    "darstellung": {"grundkoerper": {"cone": "#ff6a00"}},
}


def test_g2_struktur_aus_json():
    w = welt_aus_json(_JSON)
    assert w.art == "welt" and w.name == "Welt"
    summen = [k for k in w.kinder if k.art == ART_SUMMEN]
    assert [s.name for s in summen] == ["boot"]
    boot = summen[0]
    assert [k.name for k in boot.kinder] == [
        "rumpf", "ruder", "kielsystem", "rigg"]
    kielsystem = finde(w, "kielsystem")
    assert kielsystem.art == ART_GRUPPE
    assert [k.name for k in kielsystem.kinder] == ["kiel", "bulb"]
    rigg = finde(w, "rigg")
    assert [k.name for k in rigg.kinder] == [
        "mast", "boom", "grosssegel", "fock"]
    assert len(list(w.blaetter())) == 8


def test_g2_eigenschaften_aus_json():
    w = welt_aus_json(_JSON)
    rumpf = finde(w, "rumpf")
    assert rumpf.art == ART_BLATT
    assert ("Material", "GfK") in rumpf.eigenschaften
    assert ("Wanddicke", "5 mm") in rumpf.eigenschaften
    grosssegel = finde(w, "grosssegel")
    assert ("Dichte", "1250 kg/m3") in grosssegel.eigenschaften
    assert ("Farbe", "#fbfaf7") in grosssegel.eigenschaften
    assert finde(w, "rigg").eigenschaften == []


def test_g2_single_choice_und_blatt_abwaehlen():
    w = welt_aus_json(_JSON)
    sichtbarkeit_setzen(w, "boot")
    boot = finde(w, "boot")
    assert boot.sichtbar is True
    assert all(k.aktiv for k in boot.iteriere()
               if k.art in (ART_GRUPPE, ART_BLATT))
    blatt_setzen(w, "rumpf", False)
    assert finde(w, "rumpf").aktiv is False
    assert finde(w, "kiel").aktiv is True
    aktive = [b.name for b in aktive_blaetter(boot)]
    assert "rumpf" not in aktive and "kiel" in aktive
    blatt_setzen(w, "rumpf", True)
    assert finde(w, "rumpf").aktiv is True


def test_g2_fehlerfaelle():
    w = welt_aus_json(_JSON)
    for schlecht in ("Welt", "rigg", "gibtsnicht"):
        try:
            sichtbarkeit_setzen(w, schlecht)
        except ValueError:
            pass
        else:
            raise AssertionError("ValueError fehlt für %r" % schlecht)
