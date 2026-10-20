import concurrent.futures

import numpy as np
import pytest

from segelphysik.core import dynamik_6dof
from segelphysik.core.native_backend import NativeBackendFehler
from segelphysik.core.rechenpfad import python_referenz, rechenpfad


def test_cpp_ist_standard_und_referenz_ist_explizit(monkeypatch):
    monkeypatch.delenv("SEGELPHYSIK_RECHENPFAD", raising=False)
    assert rechenpfad() == "cpp"
    with python_referenz():
        assert rechenpfad() == "python"
        with python_referenz():
            assert rechenpfad() == "python"
        assert rechenpfad() == "python"
    assert rechenpfad() == "cpp"
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "python")
    assert rechenpfad() == "python"
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "unbekannt")
    with pytest.raises(ValueError, match="SEGELPHYSIK_RECHENPFAD"):
        rechenpfad()


def test_referenzkontext_schaltet_keine_fremden_threads_um(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        with python_referenz():
            assert pool.submit(rechenpfad).result() == "cpp"
            assert rechenpfad() == "python"


def test_produktiver_aufruf_hat_keinen_stillen_fallback(monkeypatch):
    from segelphysik.core import native_backend

    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")

    def fehlt():
        raise NativeBackendFehler("absichtlich nicht installiert")

    monkeypatch.setattr(native_backend, "native_laden", fehlt)
    with pytest.raises(NativeBackendFehler, match="absichtlich"):
        dynamik_6dof.quaternion_matrix((1., 0., 0., 0.))
    with python_referenz():
        np.testing.assert_array_equal(
            dynamik_6dof.quaternion_matrix((1., 0., 0., 0.)), np.eye(3))


@pytest.mark.parametrize("name,args", [
    ("quaternion_normalisieren", ((2., .1, -.3, .4),)),
    ("quaternion_matrix", ((2., .1, -.3, .4),)),
    ("quaternion_aus_matrix", (np.eye(3),)),
    ("_quaternion_multiplizieren", ((1., 0., 0., 0.), (0., 1., 0., 0.))),
    ("_orientierung_schritt", ((1., 0., 0., 0.), np.array([.1, .2, .3]), .004)),
])
def test_produktive_quaternionadapter_gegen_explizite_referenz(monkeypatch, name, args):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    funktion = getattr(dynamik_6dof, name)
    with python_referenz():
        erwartet = funktion(*args)
    np.testing.assert_allclose(funktion(*args), erwartet, rtol=0., atol=1e-12)
    assert isinstance(funktion(*args), type(erwartet))
