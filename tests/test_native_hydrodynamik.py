import pickle

import numpy as np
import pytest

from segelphysik.core.hydrodynamik import HydrodynamikModell, HydrodynamikTeil
from segelphysik.core.koerper_formen import bau_quader
from segelphysik.core.rechenpfad import python_referenz

pytestmark = [pytest.mark.native]


def beitraege_vergleichen(erwartet, aktuell):
    assert len(aktuell) == len(erwartet)
    for a, b in zip(erwartet, aktuell):
        assert a.name == b.name
        assert a.wrench.frame == b.wrench.frame
        for feld in ("bezugspunkt_m", "kraft_N", "moment_Nm"):
            np.testing.assert_allclose(
                getattr(b.wrench, feld), getattr(a.wrench, feld),
                rtol=0., atol=1e-12)


@pytest.mark.parametrize("rolle", ["rumpf", "kiel", "ruder", "volumenkoerper"])
def test_produktive_rollenkraefte_gegen_unabhaengige_referenz(monkeypatch, rolle):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = bau_quader(.2, .1, .3)
    teil = HydrodynamikTeil("test", rolle, p, f)
    modell = HydrodynamikModell(
        [teil], ruderwinkel_rad=.3, cd_volumenkoerper=.8,
        fluidgeschwindigkeit=(.01, -.02, 0.),
        fluidwinkelgeschwindigkeit=(.01, 0., -.02))
    rng = np.random.default_rng(10419)
    for _ in range(50):
        lage = (rng.uniform(-.3, .3, size=3), rng.normal(size=4))
        v, omega = rng.uniform(-.3, .3, size=(2, 3))
        with python_referenz():
            erwartet = modell.beitraege_erzeugen(lage, v=v, omega=omega)
        beitraege_vergleichen(
            erwartet, modell.beitraege_erzeugen(lage, v=v, omega=omega))


def test_hydrokontext_wird_beim_pickle_neu_aufgebaut(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = bau_quader(.2, .1, .3)
    modell = HydrodynamikModell([HydrodynamikTeil("test", "rumpf", p, f)])
    neu = pickle.loads(pickle.dumps(modell))
    assert neu._native_teile is not modell._native_teile
    lage = ((0., 0., -.1), (1., 0., 0., 0.))
    beitraege_vergleichen(
        modell.beitraege_erzeugen(lage, v=(.1, .1, 0.)),
        neu.beitraege_erzeugen(lage, v=(.1, .1, 0.)))
