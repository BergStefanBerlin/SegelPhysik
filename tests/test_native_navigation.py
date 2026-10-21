from dataclasses import astuple

import numpy as np
import pytest

from segelphysik.core import navigationsanzeigen as navi
from segelphysik.core.rechenpfad import python_referenz

pytestmark = [pytest.mark.native]


def test_native_navigationswerte_1000_quaternionen_und_kameralagen(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(28)
    for _ in range(1000):
        q = rng.normal(size=4)
        offset, elevation, segel = rng.uniform(-5., 5., size=3)
        with python_referenz():
            ref = navi.navigationswerte_ableiten(q, offset, elevation, segel)
        aktuell = navi.navigationswerte_ableiten(q, offset, elevation, segel)
        for a, b in zip(astuple(aktuell), astuple(ref)):
            if a is None or b is None:
                assert a is b
            else:
                assert a == pytest.approx(b, rel=0., abs=1e-12)


@pytest.mark.parametrize("q", [None, (), [0., 0., 0., 0.], [float("nan")] * 4])
def test_native_navigation_behaelt_ungueltige_pose_als_unbekannt(monkeypatch, q):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz():
        erwartet = navi.navigationswerte_ableiten(q, "ungueltig", True, None)
    assert navi.navigationswerte_ableiten(q, "ungueltig", True, None) == erwartet


def test_native_winkel_und_kompasssektoren_1000_faelle(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    for winkel in np.linspace(-1000., 1000., 1000):
        with python_referenz():
            w360 = navi.winkel_360(winkel)
            w180 = navi.wrap_180(winkel)
            sektor = navi.richtung_16(winkel)
        assert navi.winkel_360(winkel) == w360
        assert navi.wrap_180(winkel) == w180
        assert navi.richtung_16(winkel) == sektor
