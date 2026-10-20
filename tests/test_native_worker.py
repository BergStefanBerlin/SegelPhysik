from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import pickle

import numpy as np
import pytest

from segelphysik.core import dynamik_6dof, echtzeit_prozess
from segelphysik.core.dynamik_6dof import Zustand6DOF
from segelphysik.core.kraftmodell import KraftmodellMitHydroCache
from segelphysik.core.native_backend import (
    ergebnis_nach_python, native_laden, zustand_vorbereiten,
)
from segelphysik.core.rechenpfad import python_referenz
from werkzeuge.migration_szenarien import koerper_laden, kraftzeile


@pytest.fixture
def worker(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    konfig, physik, snapshot = koerper_laden("optimist")
    echtzeit_prozess.initialisieren(snapshot, konfig.wasser_dichte(), physik)
    return snapshot, konfig.wasser_dichte(), physik


@pytest.mark.parametrize("anzahl", [1, 10, 100])
def test_worker_nutzt_ganzen_nativer_batch_ohne_pythoncallback(monkeypatch, worker, anzahl):
    start = Zustand6DOF(position=(0., 0., -.05))
    fremd = ((12., -3., 1.), (.3, .1, -.2))
    native = native_laden()
    erwartet = echtzeit_prozess._native_kontext.batch(
        zustand_vorbereiten(start), anzahl, fremd, .1, native.Abbruch())

    def verboten(*_args, **_kwargs):
        raise AssertionError("Pythoncallback in nativem Workerbatch")

    monkeypatch.setattr(dynamik_6dof, "schritt", verboten)
    monkeypatch.setattr(KraftmodellMitHydroCache, "__call__", verboten)
    neu, kraft, fehler, dauer = echtzeit_prozess.schritte_berechnen(
        start, np.int64(anzahl), fremd, .1)
    assert fehler is None
    assert dauer > 0.
    np.testing.assert_array_equal(zustand_vorbereiten(neu).werte, erwartet.zustand.werte)
    _, kraft_ref = ergebnis_nach_python(erwartet)
    assert kraftzeile(kraft)[0] == kraftzeile(kraft_ref)[0]
    np.testing.assert_array_equal(kraftzeile(kraft)[1], kraftzeile(kraft_ref)[1])
    assert pickle.loads(pickle.dumps(neu)) == neu
    np.testing.assert_array_equal(
        kraftzeile(pickle.loads(pickle.dumps(kraft)))[1], kraftzeile(kraft)[1])


@pytest.mark.parametrize("anzahl", [0, -1, True, False, 1.5, "2", 2**64])
def test_worker_meldet_ungueltige_batchzahl(worker, anzahl):
    neu, kraft, fehler, _ = echtzeit_prozess.schritte_berechnen(Zustand6DOF(), anzahl)
    assert neu is None and kraft is None and fehler


@pytest.mark.parametrize("ruder,fremd", [
    (np.nan, None), (2., None), (0., ((np.inf, 0., 0.), (0., 0., 0.))),
])
def test_worker_meldet_ungueltige_steuerung(worker, ruder, fremd):
    neu, kraft, fehler, _ = echtzeit_prozess.schritte_berechnen(
        Zustand6DOF(), 1, fremd, ruder)
    assert neu is None and kraft is None and fehler


def test_worker_ohne_initialisierung_meldet_fehler(monkeypatch):
    monkeypatch.setattr(echtzeit_prozess, "_kraftfunktion", None)
    assert echtzeit_prozess.schritte_berechnen(Zustand6DOF(), 1)[2]


def test_explizite_python_referenz_verwendet_keinen_nativen_batch(monkeypatch, worker):
    with python_referenz():
        echtzeit_prozess.initialisieren(*worker)
        assert echtzeit_prozess._native_kontext is None
        neu, kraft, fehler, _ = echtzeit_prozess.schritte_berechnen(Zustand6DOF(), 3)
    assert fehler is None and neu is not None and kraft is not None


def test_native_worker_im_spawnprozess(worker):
    start = Zustand6DOF(position=(0., 0., -.05))
    erwartet = echtzeit_prozess.schritte_berechnen(start, 10)
    with ProcessPoolExecutor(
            max_workers=1, mp_context=multiprocessing.get_context("spawn"),
            initializer=echtzeit_prozess.initialisieren, initargs=worker) as pool:
        aktuell = pool.submit(echtzeit_prozess.schritte_berechnen, start, 10).result(timeout=60)
    assert aktuell[2] is None
    assert aktuell[0] == erwartet[0]
    np.testing.assert_array_equal(kraftzeile(aktuell[1])[1], kraftzeile(erwartet[1])[1])
