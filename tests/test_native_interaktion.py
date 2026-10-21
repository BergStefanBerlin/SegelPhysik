from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core import dynamik, stoerung
from segelphysik.core.auftrieb import baue_kraftfunktion
from segelphysik.core.rechenpfad import python_referenz
from segelphysik.core.statisch import SolverFehler
from werkzeuge.migration_szenarien import koerper_laden

pytestmark = [pytest.mark.native]


def test_native_vereinfachte_dynamik_1000_zustaende(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(29)
    for _ in range(1000):
        zustand = dynamik.Bewegungszustand(*rng.normal(size=4))
        added = rng.uniform(0., 10., size=6)
        kraft = SimpleNamespace(
            F_A=SimpleNamespace(z=rng.normal() * 100.),
            M=SimpleNamespace(x=rng.normal() * 20.), added_mass_diagonal=added)
        beschleunigungen = []
        kraft.mit_beschleunigung = lambda a: beschleunigungen.append(a) or kraft
        args = (zustand, lambda *_a, **_k: kraft, 10., 5., .004, 9.81, 3., 2.)
        with python_referenz():
            ref, ref_kraft = dynamik.schritt_mit_kraeften(*args)
        cpp, cpp_kraft = dynamik.schritt_mit_kraeften(*args)
        assert ref_kraft is cpp_kraft is kraft
        np.testing.assert_allclose(
            [cpp.z, cpp.phi, cpp.v_z, cpp.omega_x],
            [ref.z, ref.phi, ref.v_z, ref.omega_x], rtol=0., atol=1e-14)
        np.testing.assert_allclose(*beschleunigungen, rtol=0., atol=1e-14)


def test_native_stoerpose_und_projektion_1000_faelle(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(9)
    for _ in range(1000):
        stoer = stoerung.stoerung_ziehen(rng)
        basis = rng.normal(size=3)
        with python_referenz():
            r, p = stoerung.stoss_pose(basis, stoer)
            ref = stoerung.projektion(p, stoer)
        rc, pc = stoerung.stoss_pose(basis, stoer)
        np.testing.assert_allclose(rc, r, rtol=0., atol=1e-15)
        np.testing.assert_array_equal(pc, p)
        assert stoerung.projektion(pc, stoer) == ref


def test_native_loesungsauswahl_behaelt_identitaet_prioritaet_und_gleichstand(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(10)
    for _ in range(1000):
        loesungen = [
            {"gm": rng.choice([None, -.1, 0., .1]), "z": float(rng.integers(-2, 3)),
             "stabil": bool(rng.integers(2)), "neutral": bool(rng.integers(2))}
            for _ in range(int(rng.integers(10)))]
        with python_referenz():
            ref = stoerung.beste_loesung(loesungen)
        assert stoerung.beste_loesung(loesungen) is ref
    assert stoerung.beste_loesung([{}]) is None


@pytest.mark.parametrize("start", [-5., -.1, 5.])
def test_native_kontaktsuche_ohne_pythoncallbacks(monkeypatch, start):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    _, physik, snapshot = koerper_laden("optimist")
    with python_referenz():
        hydro_python = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)
        ref = stoerung.kontakt_start(hydro_python, start, .1)
    hydro_cpp = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)

    def verboten(*_args, **_kwargs):
        raise AssertionError("Pythonkraftcallback in nativer Kontaktsuche")

    verboten.native_kontext = hydro_cpp.native_kontext
    assert stoerung.kontakt_start(verboten, start, .1) == ref


@pytest.mark.parametrize("start, meldung", [(-100., "voll getaucht"), (100., "kein Wasserkontakt")])
def test_native_kontaktsuche_behaelt_solverfehler(monkeypatch, start, meldung):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    _, physik, snapshot = koerper_laden("optimist")
    hydro = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)
    with pytest.raises(SolverFehler, match=meldung):
        stoerung.kontakt_start(hydro, start, .1, max_schritte=1)
