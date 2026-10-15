"""Schritt-2-Tests: Kamera-Presets (K5) - rein rechnerisch, pyvista-frei."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from segelphysik.grafik_optimierung import kamera_presets


def test_presets_vollstaendig():
    p = kamera_presets()
    ecken = {"%s_%s_%s" % (h, s, l) for h in ("oben", "unten")
             for s in ("backbord", "steuerbord") for l in ("bug", "heck")}
    seiten = {"bug", "heck", "backbord", "steuerbord", "oben", "unten"}
    assert set(p) == ecken | seiten
    for pos, blick, up in p.values():
        assert len(pos) == len(blick) == len(up) == 3


def test_seitenansichten_liegen_auf_wasserlinie():
    p = kamera_presets()
    for name in ("bug", "heck", "backbord", "steuerbord"):
        pos, blick, _ = p[name]
        assert pos[2] == 0.0 and blick[2] == 0.0


def test_ecken_liegen_im_richtigen_oktanten():
    p = kamera_presets()
    pos = p["unten_steuerbord_heck"][0]
    assert pos[0] < 0 and pos[1] < 0 and pos[2] < 0
    pos = p["oben_backbord_bug"][0]
    assert pos[0] > 0 and pos[1] > 0 and pos[2] > 0


def test_bug_heck_spiegelsymmetrisch():
    p = kamera_presets()
    (b1, _, _), (b2, _, _) = p["bug"], p["heck"]
    assert b1[0] > 0 and b2[0] < 0          # Bug +x, Heck -x (A1)
    assert abs(abs(b1[0]) - abs(b2[0])) < 1e-12


def test_ansicht_von_oben_und_unten():
    for name, vorzeichen in (("oben", 1), ("unten", -1)):
        (pos, blick, up) = kamera_presets()[name]
        assert pos[2] * vorzeichen > 0 and blick[2] == 0.0
        assert abs(up[2]) < 1e-12           # Up nicht parallel zur Blickrichtung


def test_skalierung_mit_becken():
    gross = kamera_presets(lx=20.0, ly=10.0, d=3.0)
    klein = kamera_presets(lx=10.0, ly=10.0, d=3.0)
    assert abs(gross["bug"][0][0]) == 2.0 * abs(klein["bug"][0][0])
