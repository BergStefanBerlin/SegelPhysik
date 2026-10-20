from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.grafik_bruecke import GrafikBruecke
from segelphysik.core.rechenpfad import python_referenz


class Kamera:
    def __init__(self, position, fokus, oben):
        self.position = tuple(position)
        self.focal_point = tuple(fokus)
        self.up = tuple(oben)
        self.beobachter = None

    def AddObserver(self, ereignis, callback):
        assert ereignis == "ModifiedEvent"
        self.beobachter = callback
        return 1


def _bruecke(position, fokus=(0., 0., 0.), oben=(0., 0., 1.)):
    b = GrafikBruecke()
    b._plotter = SimpleNamespace(camera=Kamera(position, fokus, oben))
    return b


def _lage_gleich(a, b):
    if b is None:
        assert a is None
        return
    assert len(a) == len(b)
    for x, y in zip(a, b):
        if y is None:
            assert x is None
        else:
            np.testing.assert_allclose(x, y, rtol=0., atol=2e-12)


@pytest.mark.parametrize("ausgang", [
    (1., 2., 3.), (0., 0., 4.), (0., 0., -4.), (1e-11, 0., 4.), (1., 0., 0.),
])
def test_native_navigationskamera_behaelt_folgezustaende_und_objektwechsel(monkeypatch, ausgang):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    ref, cpp = _bruecke(ausgang), _bruecke(ausgang)
    rng = np.random.default_rng(12026)
    for i in range(1000):
        ziel = rng.normal(size=3)
        heading = None if i % 7 == 0 else float(rng.uniform(-10., 10.))
        name = "anderes_boot" if i % 13 == 0 else "boot"
        with python_referenz():
            rueckgabe = ref.navigationskamera_aktualisieren(name, ziel, heading)
        _lage_gleich(cpp.navigationskamera_aktualisieren(name, ziel, heading), rueckgabe)
        _lage_gleich(cpp._navigationskamera, ref._navigationskamera)
        assert cpp._navigationskamera_name == ref._navigationskamera_name
        assert cpp._navigationskamera_heading == ref._navigationskamera_heading
        for feld in ("position", "focal_point", "up"):
            np.testing.assert_allclose(
                getattr(cpp._plotter.camera, feld), getattr(ref._plotter.camera, feld),
                rtol=0., atol=2e-12)
        assert cpp._navigationskamera_busy is ref._navigationskamera_busy is False


def test_native_kamera_uebernimmt_manuelle_aenderungen_und_laesst_busy_unberuehrt(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    ref, cpp = _bruecke((1., 2., 3.)), _bruecke((1., 2., 3.))
    for b in (ref, cpp):
        b._navigationskamera = (0., .3, 5.)
        b._navigationskamera_heading = .7
    rng = np.random.default_rng(13026)
    for _ in range(1000):
        position, fokus = rng.normal(size=(2, 3))
        for b in (ref, cpp):
            b._plotter.camera.position = tuple(position)
            b._plotter.camera.focal_point = tuple(fokus)
        with python_referenz():
            ref._navigationskamera_geaendert(None, None)
        cpp._navigationskamera_geaendert(None, None)
        _lage_gleich(cpp._navigationskamera, ref._navigationskamera)
    lage = cpp._navigationskamera
    cpp._navigationskamera_busy = True
    cpp._plotter.camera.position = (50., 60., 70.)
    cpp._navigationskamera_geaendert(None, None)
    assert cpp._navigationskamera == lage


@pytest.mark.parametrize("position", [
    (0., 0., 0.), (1e-11, 0., 0.), (np.nan, 0., 0.), (np.inf, 0., 0.),
])
def test_native_kamera_behaelt_undefinierte_ausgangsansicht(monkeypatch, position):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    b = _bruecke(position)
    assert b.navigationskamera_aktualisieren("boot", (1., 2., 3.), .3) == (None, None)
    assert b._navigationskamera is None
    assert b._navigationskamera_heading is None


def test_native_kamera_stellt_gueltige_gespeicherte_pose_wieder_her(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    ref, cpp = _bruecke((np.nan, 0., 0.)), _bruecke((np.nan, 0., 0.))
    for b in (ref, cpp):
        b._navigationskamera = (.2, .3, 5.)
        b._navigationskamera_name = "boot"
        b._navigationskamera_heading = .7
    with python_referenz():
        ausgabe = ref.navigationskamera_aktualisieren("boot", (1., 2., 3.), .7)
    _lage_gleich(cpp.navigationskamera_aktualisieren("boot", (1., 2., 3.), .7), ausgabe)
    np.testing.assert_allclose(cpp._plotter.camera.position, ref._plotter.camera.position,
                               rtol=0., atol=2e-12)
