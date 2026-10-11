"""Schritt-2-Tests: Kamera-Presets (K5) - rein rechnerisch, pyvista-frei."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from segelphysik.grafik_optimierung import kamera_presets


def test_presets_vollstaendig():
    p = kamera_presets()
    assert set(p) == {"bug", "heck", "drei_viertel", "draufsicht"}
    for pos, blick, up in p.values():
        assert len(pos) == len(blick) == len(up) == 3


def test_bug_heck_spiegelsymmetrisch():
    p = kamera_presets()
    (b1, _, _), (b2, _, _) = p["bug"], p["heck"]
    assert b1[0] > 0 and b2[0] < 0          # Bug +x, Heck -x (A1)
    assert abs(abs(b1[0]) - abs(b2[0])) < 1e-12


def test_draufsicht_von_oben():
    (pos, blick, up) = kamera_presets()["draufsicht"]
    assert pos[2] > 0 and blick[2] == 0.0   # Kamera ueber dem Becken
    assert abs(up[2]) < 1e-12               # Up nicht parallel zur Blickrichtung


def test_skalierung_mit_becken():
    gross = kamera_presets(lx=20.0, ly=10.0, d=3.0)
    klein = kamera_presets(lx=10.0, ly=10.0, d=3.0)
    assert abs(gross["bug"][0][0]) == 2.0 * abs(klein["bug"][0][0])
