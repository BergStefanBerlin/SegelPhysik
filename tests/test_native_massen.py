import numpy as np
import pytest

from segelphysik.core import massen
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.rechenpfad import python_referenz


@pytest.mark.parametrize("verschiebung", [0., 1., 1e6])
def test_native_schalenmomente_und_schwerpunkt_gegen_referenz(monkeypatch, verschiebung):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = build_box(2., 3., 4.)
    p = p + verschiebung
    for funktion in (
            massen.mesh_flaeche, massen.schwerpunkt_flaechig, massen.traegheitstensor_flaechig):
        with python_referenz():
            erwartet = funktion(p, f)
        aktuell = funktion(p, f)
        if isinstance(erwartet, tuple):
            np.testing.assert_allclose(aktuell[0], erwartet[0], rtol=0., atol=1e-9)
            np.testing.assert_allclose(aktuell[1], erwartet[1], rtol=0., atol=1e-12)
        else:
            np.testing.assert_allclose(aktuell, erwartet, rtol=1e-12, atol=1e-8)


def test_native_homogene_momente_100_meshvarianten(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(24)
    for _ in range(100):
        p, f = build_box(*rng.uniform(.1, 4., size=3))
        p = p + rng.uniform(-2., 2., size=3)
        for funktion in (
                massen.mesh_volumen, massen.schwerpunkt_homogen, massen.traegheitstensor_homogen):
            with python_referenz():
                erwartet = funktion(p, f)
            aktuell = funktion(p, f)
            if isinstance(erwartet, tuple):
                np.testing.assert_allclose(aktuell[0], erwartet[0], rtol=0., atol=1e-12)
                np.testing.assert_allclose(aktuell[1], erwartet[1], rtol=0., atol=1e-12)
            else:
                np.testing.assert_allclose(aktuell, erwartet, rtol=0., atol=1e-11)


@pytest.mark.parametrize("funktion", [
    massen.schwerpunkt_homogen, massen.schwerpunkt_flaechig,
    massen.traegheitstensor_homogen, massen.traegheitstensor_flaechig,
])
def test_native_massenkerne_melden_leeres_mesh(monkeypatch, funktion):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with pytest.raises(ValueError, match="Leeres Mesh"):
        funktion(np.empty((0, 3)), np.empty((0, 3), dtype=np.int64))


def test_nativer_selbstschnitt_1000_meshes_gegen_referenz(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(21)

    def ergebnis(p, f):
        try:
            massen.pruefe_mesh_selbstueberschneidung(p, f)
        except ValueError as fehler:
            assert "selbstüberschneidend" in str(fehler)
            return str(fehler)
        return None

    for i in range(1000):
        p = rng.normal(size=(15, 3))
        if i % 3 == 0:
            p[:, 2] = 0.
        if i % 5 == 0:
            p += 1e6
        f = np.arange(15, dtype=np.int64).reshape(-1, 3)
        with python_referenz():
            erwartet = ergebnis(p, f)
        assert ergebnis(p, f) == erwartet


def test_nativer_selbstschnitt_verwendet_keine_pythonpraedikate(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = build_box(1.13, 2.17, 3.19)

    def verboten(*_args, **_kwargs):
        raise AssertionError("Pythonpraedikat in nativer Selbstschnittpruefung")

    monkeypatch.setattr(massen, "_selbstschnitt_python", verboten)
    monkeypatch.setattr(massen, "_dreieckspaare_schneiden", verboten)
    massen.pruefe_mesh_selbstueberschneidung(p, f)


def test_selbstschnittcache_uebernimmt_keine_freigabe_aus_anderem_rechenpfad(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = build_box(1.11, 2.22, 3.33)
    with python_referenz():
        massen.pruefe_mesh_selbstueberschneidung(p, f)
    native = massen.native_laden()
    aufrufe = []
    original = native.mesh_selbstschnitt

    def protokolliert(*args):
        aufrufe.append(True)
        return original(*args)

    monkeypatch.setattr(native, "mesh_selbstschnitt", protokolliert)
    massen.pruefe_mesh_selbstueberschneidung(p, f)
    assert aufrufe == [True]
