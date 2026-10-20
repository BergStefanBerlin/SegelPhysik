from dataclasses import asdict

import numpy as np
import pytest

from segelphysik.core.auftrieb import baue_kraftfunktion
from segelphysik.core.hydrodynamik import HydrodynamikModell
from segelphysik.core.kraftmodell import Kraftmodell, baue_kraftmodell
from segelphysik.core.native_backend import native_laden, statikkontext_vorbereiten
from segelphysik.core.rechenpfad import python_referenz
from segelphysik.core.statisch import SolverFehler, loese
from segelphysik.core.statisch_robust import loese_robust
from segelphysik.core.stationaer_hydrodynamik import (
    _pose_und_bewegung, loese_stationaer, pruefe_stationaer_dynamisch,
)
from werkzeuge.migration_szenarien import koerper_laden


@pytest.mark.parametrize("name", ["optimist", "folkeboot", "yacht1"])
@pytest.mark.parametrize("solver", [loese, loese_robust])
def test_beide_solver_mit_exaktem_modell_nativ_und_ohne_pythonresiduum(
        monkeypatch, name, solver):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz():
        konfig, physik, snapshot = koerper_laden(name)
        original = baue_kraftfunktion(
            snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2, pfad="exakt_union")
        basis = loese_robust(original, snapshot.masse, g=physik.g_m_pro_s2)
        start = (basis["z"] + .001, basis["phi"] + .001)
        erwartet = solver(original, snapshot.masse, g=physik.g_m_pro_s2, start=start)
    kandidat = baue_kraftfunktion(
        snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2, pfad="exakt_union")
    modul = "statisch" if solver is loese else "statisch_robust"

    def verboten(*_args, **_kwargs):
        raise AssertionError("Pythonresiduum im nativen Solver")

    monkeypatch.setattr("segelphysik.core." + modul + "._residuum", verboten)
    aktuell = solver(kandidat, snapshot.masse, g=physik.g_m_pro_s2, start=start)
    assert aktuell.keys() == erwartet.keys()
    np.testing.assert_allclose(
        [aktuell["z"], aktuell["phi"]], [erwartet["z"], erwartet["phi"]],
        rtol=0., atol=1e-6)
    assert aktuell["restkraft"] < 1e-6
    assert aktuell["restmoment"] < 1e-6
    if aktuell["gm"] is not None and erwartet["gm"] is not None:
        np.testing.assert_allclose(aktuell["gm"], erwartet["gm"], rtol=1e-6, atol=1e-6)


def test_native_statikresiduen_mit_fluid_ruder_und_fremdkraft(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    konfig, physik, snapshot = koerper_laden("optimist")
    hydro = baue_kraftfunktion(
        snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2, pfad="exakt_union")
    rollen = HydrodynamikModell.aus_koerper(
        snapshot, rho_kg_m3=konfig.wasser_dichte(),
        fluidgeschwindigkeit=(.2, .1, 0.), ruderwinkel_rad=.1)
    kraft = baue_kraftmodell(
        hydro, physik, masse=snapshot.masse, g=physik.g_m_pro_s2, hydrodynamik=rollen)
    kraft.fluidgeschwindigkeit = np.array([.2, .1, 0.])
    kraft.fremdkraft_setzen(((12., -3., 1.), (.3, .1, -.2)))
    kontext = statikkontext_vorbereiten(kraft)
    for z, phi in np.random.default_rng(22).uniform([-.3, -.5], [.3, .5], size=(50, 2)):
        erwartet = kraft((z, phi, 0.))
        aktuell = kontext.residuum(z, phi, snapshot.masse, physik.g_m_pro_s2, native_laden().Abbruch())
        np.testing.assert_allclose(
            aktuell, [erwartet.F_gesamt.as_array()[2], erwartet.M.as_array()[0]],
            rtol=1e-10, atol=1e-8)


def test_nativer_solver_meldet_budget_und_abbruch(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    konfig, physik, snapshot = koerper_laden("optimist")
    hydro = baue_kraftfunktion(
        snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2, pfad="exakt_union")
    with pytest.raises(SolverFehler):
        loese_robust(hydro, snapshot.masse, start=(-.1, .1), max_iter=1, stoerleiter=(),
                     stagnation_anteil=0.)
    abbruch = native_laden().Abbruch()
    abbruch.abbrechen()
    with pytest.raises(RuntimeError, match="abgebrochen"):
        statikkontext_vorbereiten(hydro).loesen(
            snapshot.masse, physik.g_m_pro_s2, np.zeros(2), 1e-8, 50,
            [], True, .05, 1e-9, abbruch)


def test_native_solver_ignorieren_keine_ueberschriebenen_kraftcallbacks(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    _, physik, snapshot = koerper_laden("optimist")
    hydro = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)

    class ErweitertesKraftmodell(Kraftmodell):
        def __call__(self, *_args, **_kwargs):
            raise ValueError("Erweiterter Kraftcallback muss ausgewertet werden")

    modell = ErweitertesKraftmodell(hydro, masse=snapshot.masse)
    assert statikkontext_vorbereiten(modell) is None
    with pytest.raises(ValueError, match="Erweiterter Kraftcallback"):
        loese_robust(modell, snapshot.masse)


@pytest.mark.parametrize("solver", [loese, loese_robust])
@pytest.mark.parametrize("budget", [1.5, "2"])
def test_native_statik_trunkiert_keine_ungueltigen_iterationsbudgets(monkeypatch, solver, budget):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    _, physik, snapshot = koerper_laden("optimist")
    hydro = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)
    with pytest.raises(TypeError):
        solver(hydro, snapshot.masse, max_iter=budget)


def test_stationaere_native_kraftauswertung_gegen_oeffentlichen_vertrag(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    konfig, physik, snapshot = koerper_laden("optimist")
    hydro = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)
    rollen = HydrodynamikModell.aus_koerper(
        snapshot, rho_kg_m3=1000., ruderwinkel_rad=.1)
    kraft = baue_kraftmodell(
        hydro, physik, masse=snapshot.masse, g=physik.g_m_pro_s2, hydrodynamik=rollen)
    kraft.fremdkraft_setzen(((15., 2., 0.), (.2, .1, -.1)))
    kontext = statikkontext_vorbereiten(kraft)
    for werte in np.random.default_rng(42).uniform(
            [.1, -.3, -.2, -.2, -.3, -.5], [1., .3, .2, .2, .3, .5], size=(100, 6)):
        pose, v, omega = _pose_und_bewegung(werte)
        erwartet = kraft(pose, v=v, omega=omega)
        f, m = kontext.stationaere_kraft(werte, native_laden().Abbruch())
        np.testing.assert_allclose(f, erwartet.F_gesamt.as_array(), rtol=1e-10, atol=1e-8)
        np.testing.assert_allclose(m, erwartet.M_gesamt.as_array(), rtol=1e-10, atol=1e-8)


@pytest.mark.parametrize("start", [
    (.2, -.05, .01, 0., 0., 0.),
    (.2, -.05, .01, .03, .02, .01),
])
def test_stationaerer_solver_rechnet_stufen_ohne_pythonresiduum(monkeypatch, start):
    from segelphysik.core.konfig_lader import lade_physik
    from segelphysik.core.koerper import KoerperSnapshot
    from segelphysik.core.koerper_formen import build_box
    from werkzeuge.migration_inventar import ROOT

    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = build_box(1., 1., 1.)
    snapshot = KoerperSnapshot(
        masse=500., traegheitstensor=np.eye(3) * 100.,
        blatt_meshes=((p, f),), r_S=(0., 0., 0.), zustand=None, version=0)
    physik = lade_physik(ROOT / "konfigurationen")
    kwargs = dict(
        charakteristische_kraft_N=500., charakteristische_laenge_m=1.,
        referenzgeschwindigkeit_m_s=.5, start=start)

    def bauen():
        hydro = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)
        kraft = baue_kraftmodell(hydro, physik, masse=500., g=physik.g_m_pro_s2)
        kraft.linear_widerstand = np.array([100., 100., 0., 0., 0., 0.])
        kraft.quadratischer_widerstand = np.zeros(6)
        kraft.added_mass_diagonal = np.arange(1., 7.)
        kraft.fremdkraft_setzen(((50., 0., 0.), (.2, 0., 0.)))
        return kraft

    with python_referenz():
        erwartet = loese_stationaer(bauen(), **kwargs)
    kraft = bauen()

    def verboten(*_args, **_kwargs):
        raise AssertionError("Pythonresiduum in stationaerem Solver")

    monkeypatch.setattr("segelphysik.core.stationaer_hydrodynamik._residuum", verboten)
    fortschritt = []
    aktuell = loese_stationaer(kraft, **kwargs, fortschritt=fortschritt.append)
    assert len(fortschritt) == len(aktuell.stufen) == 2
    if start[3]:
        assert aktuell.stufen[1].iterationen > 1
    assert aktuell.konvergiert == erwartet.konvergiert
    for a, b in zip(aktuell.stufen, erwartet.stufen):
        assert a.name == b.name and a.konvergiert == b.konvergiert
        np.testing.assert_allclose(a.pose, b.pose, rtol=0., atol=1e-6)
        np.testing.assert_allclose(a.geschwindigkeit_m_s, b.geschwindigkeit_m_s,
                                   rtol=0., atol=1e-6)
    pruefparameter = dict(
        masse_kg=501., traegheit_koerper=np.eye(3) * 100.,
        charakteristische_laenge_m=1., dt_s=.004,
        g_m_pro_s2=physik.g_m_pro_s2, dauer_s=.203)
    with python_referenz():
        referenz_nachlauf = pruefe_stationaer_dynamisch(
            bauen(), aktuell.stufen[-1], **pruefparameter)
    monkeypatch.setattr("segelphysik.core.stationaer_hydrodynamik.schritt", verboten)
    nativer_nachlauf = pruefe_stationaer_dynamisch(
        kraft, aktuell.stufen[-1], **pruefparameter)
    assert nativer_nachlauf.bestanden == referenz_nachlauf.bestanden
    for name, wert in asdict(referenz_nachlauf).items():
        if name in ("laufzeit_s", "bestanden"):
            continue
        if wert is None:
            assert getattr(nativer_nachlauf, name) is None
        else:
            assert getattr(nativer_nachlauf, name) == pytest.approx(wert, rel=0., abs=1e-7)
