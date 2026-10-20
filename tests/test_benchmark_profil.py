from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import json
import uuid

import numpy as np
import pytest

from segelphysik.core import dynamik_6dof, echtzeit_prozess
from segelphysik.core.dynamik_6dof import Zustand6DOF
from segelphysik.core.koerper import KoerperSnapshot
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.konfig_lader import lade_physik
from segelphysik.grafik_bruecke import GrafikBruecke, _farbgruppen
from werkzeuge.benchmark_profil import (
    WorkerProfil, eingabe_hash, profil_initialisieren,
    profil_schritte_berechnen, statistik, worker_bericht,
)
from werkzeuge.benchmark_gui_live import _kugelcache_deaktivieren


@pytest.fixture
def profildatei():
    # Mess-/Testartefakte bleiben im Projekt, nicht im System-Temp.
    datei = Path(".pytest_cache") / ("worker-" + uuid.uuid4().hex + ".jsonl")
    datei.parent.mkdir(exist_ok=True)
    try:
        yield datei
    finally:
        datei.unlink(missing_ok=True)


def test_statistik_kennzeichnet_fehlende_werte():
    assert statistik([])["p95_ms"] is None
    assert statistik([0.001, 0.003])["median_ms"] == pytest.approx(2.0)


def test_poseprobe_rundet_nicht_und_ist_kein_ergebniscache(profildatei):
    profil = WorkerProfil(profildatei)
    aufrufe = []
    funktion = profil.hydro_messen(lambda lage: aufrufe.append(lage) or 42)
    lage = ((0., 0., 0.), (1., 0., 0., 0.))
    assert funktion(lage) == 42
    assert funktion(lage) == 42
    assert funktion(((0., 0., 1e-16), lage[1])) == 42
    assert len(aufrufe) == 3
    assert profil.treffer == 1
    assert len(profil.posen) == 2


def test_messwrapper_reicht_fehler_durch(profildatei):
    def fehler():
        raise ValueError("kein Ersatzwert")
    profil = WorkerProfil(profildatei)
    with pytest.raises(ValueError, match="kein Ersatzwert"):
        profil.messen("test", fehler)()
    assert len(profil.werte["test"]) == 1


def test_eingabehash_beruecksichtigt_alle_slots_parameter():
    physik = lade_physik("konfigurationen")
    vorher = eingabe_hash(None, physik, 1000., "exakt_union", None)
    physik.fluidgeschwindigkeit = (0., 0., 0.01)
    assert eingabe_hash(None, physik, 1000., "exakt_union", None) != vorher


@pytest.mark.parametrize("rechenpfad", ["python", "cpp"])
def test_worker_profil_laesst_zustand_und_kraefte_unveraendert(
        monkeypatch, profildatei, rechenpfad):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", rechenpfad)
    punkte, dreiecke = build_box(1., 1., 1.)
    snapshot = KoerperSnapshot(
        masse=500., traegheitstensor=tuple(map(tuple, np.eye(3) * 100.)),
        blatt_meshes=((punkte, dreiecke),), r_S=(0., 0., 0.),
        zustand=None, version=0)
    physik = lade_physik("konfigurationen")
    echtzeit_prozess.initialisieren(snapshot, 1000., physik)
    referenz = echtzeit_prozess.schritte_berechnen(Zustand6DOF(), 3)
    monkeypatch.setattr(dynamik_6dof, "schritt", dynamik_6dof.schritt)
    profil_initialisieren(snapshot, 1000., physik, datei=profildatei, cpu_batches=1)
    kandidat = profil_schritte_berechnen(Zustand6DOF(), 3)
    assert kandidat[0] == referenz[0]
    assert kandidat[1].F_gesamt.as_array() == pytest.approx(
        referenz[1].F_gesamt.as_array(), rel=0., abs=1e-12)
    assert kandidat[1].M_gesamt.as_array() == pytest.approx(
        referenz[1].M_gesamt.as_array(), rel=0., abs=1e-12)
    bericht = worker_bericht(profildatei)
    assert bericht["batchanzahl"] == 1
    assert bericht["cache_pruefung"]["cache_pose_aufrufe"] == (
        3 if rechenpfad == "python" else None)
    roh = [json.loads(z) for z in profildatei.read_text(encoding="utf-8").splitlines()]
    batch = roh[1]
    komponenten = (
        ("hydrostatik_geometrie", "hydrodynamik", "kraftaggregation_exklusiv",
         "integrator_exklusiv", "kraftaufruf_rest", "worker_rest")
        if rechenpfad == "python" else ("nativer_batch", "worker_rest"))
    if rechenpfad == "cpp":
        assert batch["hydrostatik_geometrie_s"] is None
        assert bericht["batchkomponenten"]["hydrostatik_geometrie"]["anzahl"] == 0
        assert bericht["batchkomponenten"]["nativer_batch_inkl_kraefte"]["anzahl"] == 1
    summe = sum(batch[k + "_s"] for k in komponenten)
    assert summe == pytest.approx(batch["worker_s"], abs=1e-12)
    assert bericht["cpu_hotspots"]
    assert eingabe_hash(snapshot, physik, 1000., "exakt_union", None) != eingabe_hash(
        replace(snapshot, masse=501.), physik, 1000., "exakt_union", None)


@pytest.mark.parametrize("pfad", ["einzeln", "starr", "gelenk"])
def test_farbgruppen_ueberspringen_leere_punktmassen(monkeypatch, pfad):
    punkt = SimpleNamespace(
        teile=[], dreiecke=np.empty((0, 3), dtype=np.int64),
        punkte=np.empty((0, 3)), gelenkdefinition=None,
        basis_pose=None, gelenkwinkel_rad=0.)
    if pfad == "einzeln":
        wurzel = punkt
    else:
        wurzel = SimpleNamespace(
            teile=[(punkt, (np.eye(3), np.zeros(3)))],
            gelenkdefinition=object() if pfad == "gelenk" else None,
            _r_eingabe=(0., 0., 0.))
        monkeypatch.setattr(
            "segelphysik.grafik_bruecke.pose_mit_gelenkwinkel",
            lambda *_args: SimpleNamespace(
                rotationsmatrix=np.eye(3), translation_m=(0., 0., 0.)))
    assert _farbgruppen(wurzel) == []


def test_kugelnetz_wird_nur_bei_form_oder_stilaenderung_erneuert(monkeypatch):
    import pyvista as pv

    bruecke = GrafikBruecke.__new__(GrafikBruecke)
    store = {}
    meshes = []

    def setzen(store, name, mesh, _vordergrund, **_kwargs):
        meshes.append(mesh)
        if name not in store:
            store[name] = pv.Actor(mapper=pv.DataSetMapper(mesh))
        else:
            store[name].mapper.SetInputData(mesh)

    monkeypatch.setattr(bruecke, "_mesh_setzen", setzen)
    bruecke._kugel_mesh_setzen(store, "marker", (1., 2., 3.), .2, "red", False)
    originalpunkte = np.asarray(meshes[0].points).copy()
    bruecke._kugel_mesh_setzen(store, "marker", (2., 4., 6.), .2, "red", False)
    assert len(meshes) == 1
    assert store["marker"].GetPosition() == (1., 2., 3.)
    assert meshes[0].points == pytest.approx(originalpunkte, rel=0., abs=0.)
    bruecke._kugel_mesh_setzen(store, "marker", (2., 4., 6.), .3, "red", False)
    assert len(meshes) == 2
    assert store["marker"].GetPosition() == (0., 0., 0.)
    bruecke._kugel_mesh_setzen(store, "marker", (2., 4., 6.), .3, "blue", False)
    assert len(meshes) == 3
    bruecke._kugel_mesh_setzen(store, "marker", (2., 4., 6.), .3, "blue", True)
    assert len(meshes) == 4
    bruecke._kugel_mesh_setzen(
        store, "marker", (2., 4., 6.), .3, "blue", True, lighting=False)
    assert len(meshes) == 5
    bruecke._vg_unmoeglich = True
    bruecke._kugel_mesh_setzen(
        store, "marker", (2., 4., 6.), .3, "blue", True, lighting=False)
    assert len(meshes) == 6
    store.clear()
    bruecke._kugel_mesh_setzen(
        store, "marker", (2., 4., 6.), .3, "blue", True, lighting=False)
    assert len(meshes) == 7


def test_markerentfernung_invalidiert_geometriecache():
    bruecke = GrafikBruecke.__new__(GrafikBruecke)
    bruecke._kugel_cache = {"marker": object()}
    bruecke._vg_actors = {}
    bruecke._plotter = SimpleNamespace(remove_actor=lambda _name, **_kw: None)
    bruecke._actor_weg("marker")
    assert bruecke._kugel_cache == {}


def test_benchmark_referenzschalter_erzeugt_marker_jedes_mal_neu():
    aufrufe = []
    bruecke = SimpleNamespace(_kugel_cache={"marker": 42})
    bruecke._kugel_mesh_setzen = lambda _store, name: aufrufe.append(
        name in bruecke._kugel_cache)
    _kugelcache_deaktivieren(bruecke)
    bruecke._kugel_mesh_setzen({}, "marker")
    bruecke._kugel_cache["marker"] = 42
    bruecke._kugel_mesh_setzen({}, "marker")
    assert aufrufe == [False, False]


@pytest.mark.parametrize("typ", ["kraft", "moment"])
def test_formgleiche_kraftoverlays_werden_exakt_nur_translatiert(monkeypatch, typ):
    import pyvista as pv
    from segelphysik.core.kraefte_bild import pfeil_fest
    from segelphysik.core.pfeilstil import Stil

    bruecke = GrafikBruecke()
    store, meshes = {}, []

    def setzen(store, name, mesh, _vordergrund, **_kwargs):
        meshes.append(mesh)
        if name not in store:
            store[name] = pv.Actor(mapper=pv.DataSetMapper(mesh))
        else:
            store[name].mapper.SetInputData(mesh)

    monkeypatch.setattr(bruecke, "_mesh_setzen", setzen)
    stil = Stil().pfeil("f_a", 4.)
    def zeichnen(start, st=stil, betrag=2.):
        if typ == "kraft":
            pfeil = pfeil_fest(
                start, (0., 0., betrag), .02, .05, .1)
            bruecke._kraftpfeil_zeichnen(store, "marker", st, pfeil)
        else:
            bruecke._momentbogen_zeichnen(
                store, "marker", st, betrag, np.asarray(start), .5, 1)

    zeichnen((1., 2., 3.))
    original = np.asarray(meshes[0].points).copy()
    zeichnen((2., 4., 6.))
    assert len(meshes) == 1
    assert store["marker"].GetPosition() == (1., 2., 3.)
    assert meshes[0].points == pytest.approx(original, rel=0., abs=0.)
    zeichnen((2., 4., 6.), betrag=3.)
    assert len(meshes) == 2
    assert store["marker"].GetPosition() == (0., 0., 0.)
    zeichnen((2., 4., 6.), st={**stil, "farbe": "#123456"}, betrag=3.)
    assert len(meshes) == 3


def test_hauptachsen_transformieren_nur_laenge_und_pose(monkeypatch):
    import pyvista as pv
    bruecke = GrafikBruecke()
    bruecke._koerper = {"test": {"overlay_skala": (1., .05)}}
    monkeypatch.setattr(bruecke, "_ausdehnung", lambda _k: 4.)
    meshes = []

    def setzen(store, name, mesh, _vordergrund, **_kwargs):
        meshes.append(mesh)
        store[name] = pv.Actor(mapper=pv.DataSetMapper(mesh))

    monkeypatch.setattr(bruecke, "_mesh_setzen", setzen)
    bruecke._overlay_hauptachsen_setzen(
        "test", np.zeros(3), np.eye(3), (1., 2., 3.))
    assert len(meshes) == 3
    bruecke._overlay_hauptachsen_setzen(
        "test", np.array((1., 2., 3.)), np.eye(3), (2., 3., 4.))
    assert len(meshes) == 3
    store = bruecke._koerper["test"]["overlay_actors"]
    for i, actor in enumerate(store.values()):
        matrix = actor.GetUserMatrix()
        assert [matrix.GetElement(j, 3) for j in range(3)] == [1., 2., 3.]
        assert np.linalg.norm([matrix.GetElement(j, 0) for j in range(3)]) == pytest.approx(i + 2.)
        assert np.linalg.norm([matrix.GetElement(j, 1) for j in range(3)]) == pytest.approx(1.)
        assert np.linalg.norm([matrix.GetElement(j, 2) for j in range(3)]) == pytest.approx(1.)


def test_schulungsdarstellung_ist_explizit_persistent_und_reversibel(
        monkeypatch, profildatei):
    from PySide6.QtWidgets import QApplication
    from segelphysik.core.einstellungen import Einstellungen
    from segelphysik.gui.hauptfenster import HauptFenster
    from segelphysik.core.overlays import LAYER_KRAEFTE, LAYER_MOMENTE

    app = QApplication.instance() or QApplication([])
    pfad = profildatei.with_suffix(".settings.json")
    original_laden = Einstellungen.laden
    monkeypatch.setattr(
        Einstellungen, "laden", classmethod(
            lambda cls: original_laden(str(pfad))))
    fenster = HauptFenster()
    aufrufe = []
    rw = SimpleNamespace(GetMultiSamples=lambda: 8)
    fenster._bruecke = SimpleNamespace(
        _plotter=SimpleNamespace(render_window=rw),
        ssao_setzen=lambda wert: aufrufe.append(("ssao", wert)) or True,
        wasseroptik_setzen=lambda wert: aufrufe.append(("wasser", wert)) or True,
        kantenglaettung_setzen=lambda wert: aufrufe.append(("samples", wert)) or True)
    vorher = (fenster._echtzeit_angefordert_s, fenster._echtzeit_berechnet_s)
    try:
        assert not fenster._schulungsdarstellung_check.isChecked()
        fenster._schulungsdarstellung_check.click()
        assert original_laden(str(pfad)).get("anzeigen", "schulungs_darstellung")
        assert ("samples", 0) in aufrufe
        assert ("ssao", False) in aufrufe and ("wasser", False) in aufrufe
        assert fenster._echtzeit_render_timer.interval() == 20
        assert not fenster._ssao_check.isEnabled()
        assert vorher == (
            fenster._echtzeit_angefordert_s, fenster._echtzeit_berechnet_s)
        zweite = HauptFenster()
        assert zweite._schulungsdarstellung_check.isChecked()
        zweite.close()
        fenster._schulungsdarstellung_check.click()
        assert not original_laden(str(pfad)).get("anzeigen", "schulungs_darstellung")
        assert ("samples", 8) in aufrufe
        assert fenster._ssao_check.isChecked()
        assert fenster._wasseroptik_check.isChecked()
        assert fenster._echtzeit_render_timer.interval() == 33
        assert fenster._layer_checks["Kräfte"].isChecked()
        assert fenster._layer_checks["Momente"].isChecked()
    finally:
        fenster.close()
        app.processEvents()
        pfad.unlink(missing_ok=True)


def test_verdeckte_navigationsanzeigen_halten_aktuelle_daten_bis_show(monkeypatch):
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui.navigationswidgets import NavigationsWidgetFenster
    from segelphysik.core.navigationsanzeigen import navigationswerte_ableiten

    app = QApplication.instance() or QApplication([])
    fenster = NavigationsWidgetFenster()
    aufrufe = []
    for widget in fenster.widgets:
        monkeypatch.setattr(
            widget, "aktualisieren",
            lambda werte, optionen: aufrufe.append((werte, optionen)))
    werte = navigationswerte_ableiten((1., 0., 0., 0.))
    fenster.aktualisieren(werte, {"titel_sichtbar": False}, 3.)
    assert not aufrufe
    assert fenster._geschwindigkeit_m_pro_s == 3.
    fenster.show()
    app.processEvents()
    assert len(aufrufe) == 3
    assert all(wert == werte for wert, _optionen in aufrufe)
    fenster.close()


def test_qt_renderanforderung_koalesziert_bis_zum_swap(monkeypatch):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    from segelphysik.gui.hauptfenster import HauptFenster

    app = QApplication.instance() or QApplication([])
    widget = QOpenGLWidget()
    bruecke = GrafikBruecke()
    bruecke._plotter = widget
    aufrufe = []
    monkeypatch.setattr(QOpenGLWidget, "update", lambda self: aufrufe.append(self))
    assert bruecke.render()
    assert bruecke._render_ausstehend
    assert aufrufe == [widget]
    widget.frameSwapped.emit()
    assert not bruecke._render_ausstehend
    fenster = HauptFenster()
    fenster._bruecke = bruecke
    fenster._schulungsdarstellung_check.blockSignals(True)
    fenster._schulungsdarstellung_check.setChecked(True)
    fenster._schulungsdarstellung_check.blockSignals(False)
    bruecke._render_ausstehend = True
    # Würde bei fehlender Backpressure als Verlauf ausgewertet werden.
    fenster._echtzeit_anzeige_verlauf = object()
    fenster._echtzeit_render_takt()
    assert bruecke._render_ausstehend
    fenster._echtzeit_anzeige_verlauf = []
    fenster.close()
    widget.close()
    app.processEvents()


def test_wasserspur_mesh_behaelt_topologie_bei_neuen_punkten():
    import pyvista as pv

    bruecke = GrafikBruecke()
    bruecke._wasserpunkte_an = True
    bruecke._wasserpunkte_meshes = {}
    spuren = np.arange(18, dtype=float).reshape(2, 3, 3)
    alpha = np.ones((2, 3))
    bruecke._wasserpunkte = SimpleNamespace(
        aktualisieren=lambda _xy: (spuren[:, -1], spuren, alpha))
    bruecke._plotter = SimpleNamespace(
        add_mesh=lambda mesh, **_kw: pv.Actor(mapper=pv.DataSetMapper(mesh)))
    bruecke._wasserpunkte_zeichnen((0., 0.))
    mesh = bruecke._wasserpunkte_meshes["wasser_spuren"]
    linien = np.asarray(mesh.lines).copy()
    spuren += .5
    bruecke._wasserpunkte_zeichnen((1., 0.))
    assert bruecke._wasserpunkte_meshes["wasser_spuren"] is mesh
    assert mesh.points == pytest.approx(spuren.reshape(-1, 3), rel=0., abs=0.)
    assert np.array_equal(mesh.lines, linien)
    assert mesh["rgba"][:, 3].tolist() == [255] * 6
