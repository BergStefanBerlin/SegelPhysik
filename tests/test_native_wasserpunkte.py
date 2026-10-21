import numpy as np
import pytest

from segelphysik.core import wasserpunkte as wasser
from segelphysik.core.rechenpfad import python_referenz

pytestmark = [pytest.mark.native]


def test_nativer_wasserhash_und_punktlage_sind_deterministisch_und_periodisch(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(27)
    x = rng.integers(-1000000, 1000000, size=(100, 100))
    y = rng.integers(-1000000, 1000000, size=(100, 1))
    for salz in (1, 2, -1, 1024):
        with python_referenz():
            ref = wasser._hash01(x, y, salz)
        np.testing.assert_array_equal(wasser._hash01(x, y, salz), ref)
    with python_referenz():
        ref = wasser.punktlage(x, y)
        skalar = wasser.punktlage(-15, 16)
    for a, b in zip(wasser.punktlage(x, y), ref):
        np.testing.assert_array_equal(a, b)
    assert wasser.punktlage(-15, 16) == skalar


@pytest.mark.parametrize("spur_punkte", [2, 3, 6, 7, 20])
@pytest.mark.parametrize("historie", [2, 12])
def test_native_wasserpunkte_spuren_und_transparenz_gegen_referenz(
        monkeypatch, spur_punkte, historie):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    kwargs = dict(spur_punkte=spur_punkte, historie=historie,
                  hoehe=lambda x, y: .01 * np.sin(x) * np.cos(y))
    ref_feld, cpp_feld = wasser.WasserPunktFeld(**kwargs), wasser.WasserPunktFeld(**kwargs)
    for i in range(40):
        zentrum = (i * .13 - 4., i * .27 - 8.)
        with python_referenz():
            ref = ref_feld.aktualisieren(zentrum)
        cpp = cpp_feld.aktualisieren(zentrum)
        for a, b in zip(cpp, ref):
            assert a.shape == b.shape and a.dtype == b.dtype
            np.testing.assert_allclose(a, b, rtol=0., atol=1e-13)
    cpp_feld.zuruecksetzen()
    ref_feld.zuruecksetzen()
    with python_referenz():
        ref = ref_feld.aktualisieren((0., 0.))
    for a, b in zip(cpp_feld.aktualisieren((0., 0.)), ref):
        np.testing.assert_allclose(a, b, rtol=0., atol=1e-13)


@pytest.mark.parametrize("kwargs", [
    {}, {"ringe": 3, "segmente": 7, "hoehenstufen": 2},
    {"hoehenstufen": 0}, {"farbe": (20, 30, 40), "ringe": 1},
])
def test_nativer_dunst_behaelt_aufloesung_farben_und_flaechen(monkeypatch, kwargs):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz():
        punkte, flaechen, farben = wasser.dunst_gitter(**kwargs)
    p, f, c = wasser.dunst_gitter(**kwargs)
    np.testing.assert_allclose(p, punkte, rtol=0., atol=1e-12)
    np.testing.assert_array_equal(f, flaechen)
    np.testing.assert_array_equal(c, farben)
    assert f.dtype == np.int64 and c.dtype == np.uint8
