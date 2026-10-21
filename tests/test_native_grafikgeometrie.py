from pathlib import Path

import numpy as np
import pytest

from segelphysik import grafik_bruecke as gb
from segelphysik.core.dynamik_6dof import quaternion_matrix
from segelphysik.core.fabriken import baue_modellpaket
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.rechenpfad import python_referenz

pytestmark = [pytest.mark.native]


ROOT = Path(__file__).resolve().parents[1]


def _farbgruppen_gleich(k):
    with python_referenz():
        ref = gb._farbgruppen(k)
    cpp = gb._farbgruppen(k)
    assert len(cpp) == len(ref)
    for a, b in zip(cpp, ref):
        assert a.keys() == b.keys()
        np.testing.assert_allclose(a["punkte"], b["punkte"], rtol=0., atol=2e-12)
        np.testing.assert_array_equal(a["dreiecke"], b["dreiecke"])
        for name in a.keys() - {"punkte", "dreiecke"}:
            assert a[name] == b[name]


@pytest.mark.parametrize("modell", ["optimist", "folkeboot", "yacht1"])
def test_native_farbgruppen_und_benetzte_geometrie_aller_modelle(monkeypatch, modell):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    konfig = lade_konfig(ROOT / "konfigurationen")
    k, _ = baue_modellpaket(konfig, ROOT / "code" / "modelle" / modell)
    _farbgruppen_gleich(k)
    with python_referenz():
        ref = gb._benetzte_geometrie(k)
    cpp = gb._benetzte_geometrie(k)
    for a, b in zip(cpp, ref):
        np.testing.assert_allclose(a, b, rtol=0., atol=2e-12)

    def gelenke(knoten):
        if knoten.gelenkdefinition is not None:
            yield knoten.knoten_id
        for kind, _ in knoten.teile:
            yield from gelenke(kind)

    for index, ident in enumerate(gelenke(k)):
        k.gelenkwinkel_setzen(ident, .1 + index * .02)
        _farbgruppen_gleich(k)


def test_native_farbgruppen_generischer_verschachtelter_koerper(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = build_box(1., 2., 3.)
    a = Koerper(form=(p, f), dichte=100., farbe="#123456", glanz=.2)
    b = Koerper(form=(p * .3 + 2., f), dichte=200., farbe="#654321", glanz=.7)
    c = Koerper(teile=[(a, None), (b, None)])
    d = Koerper(teile=[(c, None), (a, None)])
    for k in (a, c, d):
        _farbgruppen_gleich(k)


@pytest.mark.parametrize("aktiv", [False, True])
@pytest.mark.parametrize("gruppenanzahl", [0, 1, 4])
def test_native_statische_gesamtdarstellung_behaelt_sichtbarkeit_und_alle_posen(
        monkeypatch, aktiv, gruppenanzahl):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(11026)

    class Pd(dict):
        points = None

    punkte = [rng.normal(size=(30, 3)) for _ in range(gruppenanzahl + 1)]
    bridge = gb.GrafikBruecke()
    bridge._actors_aktualisieren = lambda *args: None
    bridge._gruppen_actors = lambda *args: None
    bridge._overlays_aktualisieren = lambda *args: None
    for _ in range(100):
        rotation = quaternion_matrix(rng.normal(size=4))
        position = rng.normal(size=3)
        def daten():
            return {
                "pd": Pd(referenz_punkte=punkte[0]),
                "gruppen": [{"pd": Pd(referenz_punkte=p)} for p in punkte[1:]],
                "aktiv": aktiv, "statisch_R": rotation, "position": position,
            }
        ref, cpp = daten(), daten()
        with python_referenz():
            bridge._statisch_anwenden("boot", ref)
        bridge._statisch_anwenden("boot", cpp)
        np.testing.assert_allclose(cpp["pd"].points, ref["pd"].points, rtol=0., atol=2e-12)
        for a, b in zip(cpp["gruppen"], ref["gruppen"]):
            if not aktiv:
                assert a["pd"].points is b["pd"].points is None
            else:
                np.testing.assert_allclose(
                    a["pd"].points, b["pd"].points, rtol=0., atol=2e-12)


def test_native_polydaten_behalten_dreieckszellen(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = build_box(1., 2., 3.)

    class Pv:
        @staticmethod
        def PolyData(punkte, faces):
            return punkte, faces

    for funktion in (gb._polydaten, gb._dreiecks_polydaten):
        with python_referenz():
            ref = funktion(Pv, p, f)
        for a, b in zip(funktion(Pv, p, f), ref):
            np.testing.assert_array_equal(a, b)


def test_native_hauptachsen_overlay_geometrie_gegen_referenz(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(22026)
    for _ in range(200):
        punkte = rng.normal(size=(rng.integers(0, 100), 3))
        eigenvektoren = quaternion_matrix(rng.normal(size=4))
        rotation = quaternion_matrix(rng.normal(size=4))
        with python_referenz():
            erwartet = gb._hauptachsen_geometrie(
                punkte, eigenvektoren, rotation)
        aktuell = gb._hauptachsen_geometrie(
            punkte, eigenvektoren, rotation)
        np.testing.assert_allclose(aktuell[0], erwartet[0], rtol=0., atol=2e-12)
        np.testing.assert_allclose(aktuell[1], erwartet[1], rtol=0., atol=2e-12)
