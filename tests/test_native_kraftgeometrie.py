from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core import kraefte_bild as kb, overlays
from segelphysik.core.auftrieb import Vektor
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.rechenpfad import python_referenz

pytestmark = [pytest.mark.native]


def _gleich(cpp, ref):
    if isinstance(ref, dict):
        assert cpp.keys() == ref.keys()
        for name in ref:
            _gleich(cpp[name], ref[name])
    elif isinstance(ref, tuple):
        assert type(cpp) is tuple and len(cpp) == len(ref)
        for a, b in zip(cpp, ref):
            _gleich(a, b)
    elif ref is None:
        assert cpp is None
    else:
        if isinstance(ref, np.ndarray):
            assert cpp.shape == ref.shape and cpp.dtype == ref.dtype
        np.testing.assert_allclose(cpp, ref, rtol=0., atol=2e-12)


@pytest.mark.slow
def test_native_kraftpfeile_momente_und_skala_gegen_referenz(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(4026)
    for _ in range(1000):
        start, kraft, bezug, gesamt = rng.normal(size=(4, 3))
        erg = SimpleNamespace(K=Vektor(start), F_A=Vektor(kraft),
                              F_gesamt=Vektor(gesamt))
        for funktion, args in (
            (kb.pfeil_daten, (start, kraft)),
            (kb.pfeil_fest, (start, kraft, .1, .2, 1., .3)),
            (kb.pfeil_fest, (start, kraft, .1, .2, .01, 3.)),
            (kb.paar_moment_kraft, (start, kraft, bezug)),
            (kb.paar_moment_auftrieb, (erg, bezug)),
            (kb.skala_waehlen, (100., 9.81, float(np.linalg.norm(start)))),
            (kb.kraft_pfeile, (erg, bezug, 100., 9.81, .01)),
            (kb.zusatz_pfeile, (erg, bezug, 100., 9.81, .01)),
        ):
            with python_referenz():
                ref = funktion(*args)
            _gleich(funktion(*args), ref)


@pytest.mark.parametrize("achse", [0, 1, 2])
def test_native_momentboegen_behalten_alle_punkte_richtung_und_schwellen(monkeypatch, achse):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(1026 + achse)
    for _ in range(1000):
        moment = float(rng.uniform(-100., 100.))
        start = rng.normal(size=3)
        radius = float(rng.uniform(.001, 10.))
        with python_referenz():
            ref = kb.moment_bogen_achse(moment, start, radius, achse)
        _gleich(kb.moment_bogen_achse(moment, start, radius, achse), ref)
    for moment in (0., -1e-6, 1e-6, 1.00001e-6, -1.00001e-6):
        with python_referenz():
            ref = kb.moment_bogen_achse(moment, (1., 2., 3.), .5, achse)
        _gleich(kb.moment_bogen_achse(moment, (1., 2., 3.), .5, achse), ref)
    with python_referenz():
        ref = kb.moment_bogen(-10., (1., 2., 3.), .5)
    _gleich(kb.moment_bogen(-10., (1., 2., 3.), .5), ref)


@pytest.mark.parametrize("max_abstand", [None, 0., .03, -1.])
def test_native_strichlinien_behalten_zellen_und_doppelte_stuetzpunkte(monkeypatch, max_abstand):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(27)
    for _ in range(100):
        p = rng.normal(size=(10, 3))
        p[1] = p[0]
        p[5] = p[4]
        p[-1] = p[-2]
        with python_referenz():
            punkte, zellen = kb.strich_linien(p, .1, .03, max_abstand)
        cpp_punkte, cpp_zellen = kb.strich_linien(p, .1, .03, max_abstand)
        np.testing.assert_array_equal(cpp_zellen, zellen)
        np.testing.assert_allclose(cpp_punkte, punkte, rtol=0., atol=2e-12)
        assert cpp_zellen.dtype == np.int64


def test_native_wirkungslinien_gegen_referenz_mit_gedrehter_geometrie(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    from segelphysik.core.dynamik_6dof import quaternion_matrix

    p, f = build_box(2., 2., 2.)
    rng = np.random.default_rng(7026)
    for _ in range(1000):
        kraft, moment, bezug = rng.normal(size=(3, 3))
        rotation = quaternion_matrix(rng.normal(size=4))
        with python_referenz():
            ref = kb.wirkungslinie_auf_geometrie(
                kraft, moment, bezug, p, f, rotation)
        _gleich(kb.wirkungslinie_auf_geometrie(
            kraft, moment, bezug, p, f, rotation), ref)


def test_native_hauptachsen_uebernehmen_numpy_eigenloeser_unveraendert(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(8026)
    tensoren = [np.eye(3), np.zeros((3, 3)), np.diag([2., 2., 1.])]
    tensoren.extend(rng.normal(size=(1000, 3, 3)))
    for tensor in tensoren:
        with python_referenz():
            ref = overlays.hauptachsen(tensor)
        for a, b in zip(overlays.hauptachsen(tensor), ref):
            np.testing.assert_array_equal(a, b)
    for v in ((-1., 1., 0.), (0., -2., 2.), (-0., 0., 0.)):
        with python_referenz():
            ref = overlays._kanonisiere(v)
        np.testing.assert_array_equal(overlays._kanonisiere(v), ref)


@pytest.mark.parametrize("funktion,args", [
    (kb.pfeil_daten, ((0., 0., 0.), (0., 0., 0.))),
    (kb.pfeil_fest, ((0., 0., 0.), (0., 0., 0.), .1, .2, .3)),
    (kb.skala_waehlen, (0., 9.81, 1.)),
    (kb.strich_linien, (np.zeros((3, 3)), .1, .1)),
    (kb.strich_linien, (np.ones((3, 3)), 0., .1)),
    (kb.strich_linien, (np.ones((3, 3)), .1, -.1)),
    (kb.moment_bogen_achse, (1., (0., 0., 0.), 0., 1)),
    (kb.moment_bogen_achse, (1., (0., 0., 0.), 1., 3)),
])
def test_native_kraftgeometrie_behaelt_fehlertexte(monkeypatch, funktion, args):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz(), pytest.raises(ValueError) as ref:
        funktion(*args)
    with pytest.raises(ValueError) as cpp:
        funktion(*args)
    assert str(cpp.value) == str(ref.value)


def test_native_pfeilausgaben_besitzen_eigene_unabhaengige_arrays(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    start, kraft = np.ones(3), np.array([1., 2., 3.])
    p = kb.pfeil_daten(start, kraft)
    start[:] = 100.
    kraft[:] = 200.
    np.testing.assert_array_equal(p["start"], np.ones(3))
    p["start"][:] = 300.
    np.testing.assert_array_equal(p["schaft_start"], np.ones(3))
