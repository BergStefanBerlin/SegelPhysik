import numpy as np
import pytest

from segelphysik import wasser_schnitt
from segelphysik.core import hydrostatik
from segelphysik.core.koerper_formen import bau_quader
from segelphysik.core.rechenpfad import python_referenz
from segelphysik.core.volumen_union import _EbenenSchnitt

pytestmark = [pytest.mark.native]


@pytest.mark.parametrize("deckel", [False, True])
def test_produktiver_wasserschnitt_bewahrt_arrayreihenfolge_und_werte(monkeypatch, deckel):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(10319)
    punkte, dreiecke = bau_quader(1., 2., 3.)
    for _ in range(50):
        from segelphysik.core.frames import rotationsmatrix_achsenwinkel

        with python_referenz():
            rotation = rotationsmatrix_achsenwinkel(rng.normal(size=3), rng.uniform(-3., 3.))
        p = punkte @ rotation.T + rng.uniform(-1., 1., size=3)
        z = rng.uniform(-1., 1.)
        with python_referenz():
            erwartet = wasser_schnitt.schneide_am_wasser(p, dreiecke, z, deckel)
        aktuell = wasser_schnitt.schneide_am_wasser(p, dreiecke, z, deckel)
        for a, b in zip(aktuell, erwartet):
            np.testing.assert_array_equal(a, b)
            assert a.dtype == b.dtype


def test_produktiver_ebenenschnitt_gegen_unabhaengige_python_reduktion(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    punkte, dreiecke = bau_quader(1., 2., 3.)
    with python_referenz():
        referenz = _EbenenSchnitt(punkte, dreiecke)
    kandidat = _EbenenSchnitt(punkte, dreiecke)
    rng = np.random.default_rng(10320)
    for _ in range(200):
        normale = rng.normal(size=3)
        normale /= np.linalg.norm(normale)
        offset = rng.uniform(-3., 3.)
        with python_referenz():
            v, s = referenz.auswerten(normale, offset)
        v2, s2 = kandidat.auswerten(normale, offset)
        np.testing.assert_allclose(v2, v, rtol=0., atol=1e-12)
        np.testing.assert_allclose(s2, s, rtol=0., atol=1e-12)


@pytest.mark.parametrize("z", [-2., -1.5, -1.4999, 0., 1.4999, 1.5, 2.])
def test_produktive_wasserlinienringe_und_momente(monkeypatch, z):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    punkte, dreiecke = bau_quader(1., 2., 3.)
    with python_referenz():
        erwartet = hydrostatik.wasserlinien_querschnitt([(punkte, dreiecke)], z)
    aktuell = hydrostatik.wasserlinien_querschnitt([(punkte, dreiecke)], z)
    assert aktuell.flaeche_m2 == erwartet.flaeche_m2
    np.testing.assert_array_equal(aktuell.schwerpunkt_m, erwartet.schwerpunkt_m)
    np.testing.assert_array_equal(aktuell.flaechenkern_m4, erwartet.flaechenkern_m4)
