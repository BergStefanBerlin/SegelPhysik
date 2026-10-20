import numpy as np
import pytest

from segelphysik.core.dynamik_6dof import Zustand6DOF, schritt
from segelphysik.core.kraftmodell import KraftmodellMitHydroCache
from segelphysik.core.native_backend import (
    ergebnis_nach_python, native_laden, zustand_vorbereiten,
)
from segelphysik.core.rechenpfad import python_referenz
from werkzeuge.migration_batch import kontexte
from werkzeuge.migration_szenarien import kraftzeile


@pytest.fixture(autouse=True)
def unabhaengige_python_referenz():
    """Beide Pfade werden hier pro Auswertung statt fuer den ganzen Test gewaehlt."""
    yield


@pytest.mark.parametrize("name", ["optimist", "folkeboot", "yacht1"])
def test_nativer_batch_gegen_jeden_referenzschritt(monkeypatch, name):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    k, physik, kraft, kontext = kontexte(name)
    zustand = Zustand6DOF(
        position=(0., 0., -.05), quaternion=(1., .01, .005, 0.),
        geschwindigkeit_koerper=(.1, .02, -.01),
        winkelgeschwindigkeit_koerper=(.01, -.01, .005))
    native = native_laden()
    kandidat = zustand_vorbereiten(zustand)
    for _ in range(1000):
        with python_referenz():
            zustand, erwartet = schritt(
                zustand, kraft, k.masse, k.traegheitstensor, physik.dt_s, physik.g_m_pro_s2)
        ergebnis = kontext.batch(kandidat, 1, None, 0., native.Abbruch())
        kandidat = ergebnis.zustand
        np.testing.assert_allclose(
            ergebnis.zustand.werte, zustand_vorbereiten(zustand).werte,
            rtol=0., atol=1e-12)
        _, aktuell = ergebnis_nach_python(ergebnis)
        assert [b.name for b in aktuell.beitraege] == [b.name for b in erwartet.beitraege]
        np.testing.assert_allclose(
            aktuell.F_gesamt.as_array(), erwartet.F_gesamt.as_array(),
            rtol=0., atol=1e-9)  # Exakter Kraftvergleich: pruefe_genauigkeit_v09.py.
        schema_ref, werte_ref = kraftzeile(erwartet)
        schema_cpp, werte_cpp = kraftzeile(aktuell)
        assert schema_cpp == schema_ref
        np.testing.assert_allclose(werte_cpp, werte_ref, rtol=0., atol=1e-9)


def test_batch_ohne_python_schritt_oder_kraftcallback(monkeypatch):
    from segelphysik.core import dynamik_6dof

    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    _, _, _, kontext = kontexte("optimist")
    native = native_laden()
    start = Zustand6DOF(position=(0., 0., -.05))
    fremd = ((12., -3., 1.), (.3, .1, -.2))
    zustand = zustand_vorbereiten(start)
    for _ in range(100):
        erwartet = kontext.batch(
            zustand, 1, fremd, .1, native.Abbruch())
        zustand = erwartet.zustand

    def verboten(*_args, **_kwargs):
        raise AssertionError("Pythoncallback in nativem Physikbatch")

    monkeypatch.setattr(dynamik_6dof, "schritt", verboten)
    monkeypatch.setattr(KraftmodellMitHydroCache, "__call__", verboten)
    aktuell = kontext.batch(
        zustand_vorbereiten(start), np.int64(100), fremd, .1, native.Abbruch())
    neu, kraft = ergebnis_nach_python(aktuell)
    np.testing.assert_array_equal(zustand_vorbereiten(neu).werte, erwartet.zustand.werte)
    _, kraft_ref = ergebnis_nach_python(erwartet)
    assert kraftzeile(kraft)[0] == kraftzeile(kraft_ref)[0]
    np.testing.assert_array_equal(kraftzeile(kraft)[1], kraftzeile(kraft_ref)[1])


@pytest.mark.parametrize("anzahl", [0, -1, True, False, 1.5, "2", 2**64])
def test_batch_lehnt_ungueltige_batchanzahl_ab(monkeypatch, anzahl):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    _, _, _, kontext = kontexte("optimist")
    native = native_laden()
    with pytest.raises((ValueError, TypeError, OverflowError)):
        kontext.batch(zustand_vorbereiten(Zustand6DOF()), anzahl, None, 0., native.Abbruch())


def test_batch_abbruch_auch_vor_dem_ersten_schritt(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    _, _, _, kontext = kontexte("optimist")
    native = native_laden()
    abbruch = native.Abbruch()
    abbruch.abbrechen()
    with pytest.raises(RuntimeError, match="abgebrochen"):
        kontext.batch(zustand_vorbereiten(Zustand6DOF()), 1, None, 0., abbruch)


@pytest.mark.parametrize("matrix", [
    np.zeros((3, 3)), np.full((3, 3), np.nan), np.full((3, 3), np.inf),
])
def test_linearer_loeser_lehnt_singulaere_oder_nichtendliche_matrix_ab(matrix):
    with pytest.raises(ValueError):
        native_laden().linear_loesen(matrix, np.ones(3))
