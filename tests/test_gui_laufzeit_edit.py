import os
import time
from types import SimpleNamespace

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.auftrieb import Vektor
from segelphysik.gui.baum import (
    aktive_blaetter, finde, sichtbarkeit_setzen, welt_aus_konfig,
)
from segelphysik.gui.baum_widget import BaumWidget
from segelphysik.gui.hauptfenster import HauptFenster

def _qt_app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    "berechnet,erwartet",
    [(2.8, "bestanden"), (1.0, "nicht erreicht")],
)
def test_nachholrate_aktualisiert_sichtbares_gate(berechnet, erwartet,
                                                  monkeypatch):
    app = _qt_app()
    fenster = HauptFenster()
    jetzt = time.perf_counter()
    schwellen = {
        "zeitgenau": True,
        "nachholen_ende_rueckstand_s": 0.1,
        "nachholrate_ziel": 1.25,
        "ueberlast_rueckstand_s": 5.0,
        "max_schritte_nachholen": 64,
        "max_schritte_pro_aufgabe": 64,
    }
    monkeypatch.setattr(
        fenster, "_dyn", lambda schluessel: schwellen[schluessel])
    fenster._echtzeit_physik = SimpleNamespace(dt_s=0.004)
    fenster._echtzeit_zustand = SimpleNamespace()
    fenster._echtzeit_modus = "nachholen"
    fenster._echtzeit_nachholen_start = jetzt - 2.0
    fenster._echtzeit_berechnet_s = berechnet
    fenster._echtzeit_angefordert_s = berechnet
    fenster._echtzeit_letzte_wandzeit = jetzt

    try:
        fenster._echtzeit_takt()

        assert fenster._solver_werte["Nachholrate ≥1,25"].text(1) == erwartet
    finally:
        fenster.close()
        app.processEvents()


def _koerper_stub(**werte):
    koerper = SimpleNamespace(**werte)

    def snapshot():
        return SimpleNamespace(**werte, version=0)

    koerper.snapshot = snapshot
    return koerper


def _physik_stub(g=9.81, aufloesung=0.05, dt=0.004):
    return SimpleNamespace(
        dt_s=dt, g_m_pro_s2=g, daempfung_tauchung=0.0,
        daempfung_kraengung=0.0, voxel_aufloesung_m=aufloesung,
        linear_widerstand=(0.0,) * 6,
        quadratischer_widerstand=(0.0,) * 6,
        fluidgeschwindigkeit=(0.0,) * 3,
        fluidwinkelgeschwindigkeit=(0.0,) * 3,
        added_mass_diagonal=(0.0,) * 6)


def _konfig_kopie(tmp_path):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(root, "konfigurationen")
    for name in ("materialien.json", "koerper.json"):
        with open(os.path.join(config_dir, name), "rb") as original:
            (tmp_path / name).write_bytes(original.read())
    return lade_konfig(str(tmp_path))


def test_gui_aenderungen_bleiben_sitzungsgebunden(tmp_path):
    app = _qt_app()
    konfig = _konfig_kopie(tmp_path)
    dateien = ("materialien.json", "koerper.json")
    vorher = {name: (tmp_path / name).read_bytes() for name in dateien}
    welt = welt_aus_konfig(konfig)
    rumpf = finde(welt, "rumpf")
    widget = BaumWidget()
    widget.lade(welt)

    widget._eigenschaft_setzen(rumpf, "Material", "Stahl")
    widget._eigenschaft_setzen(rumpf, "Wanddicke", 6.0)

    assert rumpf.eintrag["material"] == "Stahl"
    assert rumpf.eintrag["wanddicke_m"] == 0.006
    assert ("Material", "Stahl") in rumpf.eigenschaften
    assert ("Wanddicke", "6 mm") in rumpf.eigenschaften
    assert {name: (tmp_path / name).read_bytes() for name in dateien} == vorher
    widget.close()


def test_gui_materialaenderung_baut_laufzeitkoerper_neu(monkeypatch, tmp_path):
    _qt_app()
    welt = welt_aus_konfig(_konfig_kopie(tmp_path))
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)

    gebaut = []

    def fake_bauen(konfig, name, aktive_blaetter=None):
        gebaut.append((konfig, name, tuple(b.name for b in aktive_blaetter)))
        return object(), (1.0, 2.0, 3.0)

    class Bruecke:
        def __init__(self):
            self.koerper = []
            self.sichtbarkeit = []

        def layer_setzen(self, _layer, _aktiviert):
            pass

        def kamera_preset_setzen(self, _preset):
            return True

        def hintergrund_setzen(self, _preset):
            return True

        def beleuchtung_setzen(self, _aktiviert):
            return True

        def wasser_sichtbar_setzen(self, _sichtbar):
            return True

        def wasseroptik_setzen(self, _aktiviert):
            return True

        def render(self):
            pass

        def koerper_objekt_setzen(self, name, koerper, position):
            self.koerper.append((name, koerper, position))

        def sichtbar_setzen(self, name, sichtbar):
            self.sichtbarkeit.append((name, sichtbar))

    bruecke = Bruecke()
    monkeypatch.setattr(
        "segelphysik.core.fabriken.baue_summenkoerper", fake_bauen)
    monkeypatch.setattr(
        fenster, "_geometrie_konflikte_bereinigen", lambda *_args: True)
    fenster._statische_simulation_ausfuehren = lambda: None
    fenster.bruecke_setzen(bruecke)

    rumpf = finde(welt, "rumpf")
    fenster.baum._eigenschaft_setzen(rumpf, "Material", "Stahl")

    assert len(gebaut) == 2
    assert all(eintrag[0] is welt.konfiguration for eintrag in gebaut)
    assert all(eintrag[1] == "yacht1" for eintrag in gebaut)
    assert bruecke.koerper[-1][0] == "yacht1"
    assert bruecke.koerper[-1][2] == (1.0, 2.0, 3.0)
    fenster.close()


@pytest.mark.parametrize(("vorrang", "erfolgreich"), [
    ("a", True),
    (None, False),
])
def test_geometriekonflikt_wird_vor_dem_lauf_prioritaetsbasiert_behandelt(
        monkeypatch, tmp_path, vorrang, erfolgreich):
    from segelphysik.core import boot_bau, fabriken
    from segelphysik.core import geometrie_konflikte as gk
    from segelphysik.core import koerper_formen

    _qt_app()
    modellordner = tmp_path / "modelle"
    quellordner = modellordner / "testboot"
    quellordner.mkdir(parents=True)
    monkeypatch.setattr(boot_bau, "MODELL_ORDNER", str(modellordner))

    form_a = koerper_formen.bau_quader(2.0, 2.0, 2.0)
    form_b = (
        form_a[0] + np.array((0.5, 0.0, 0.0)), form_a[1])
    originale = {}
    for name, form in (("a", form_a), ("b", form_b)):
        quelle = quellordner / (name + ".obj")
        quelle.write_bytes(gk._obj_schreiben(
            gk._welt_zu_obj(form[0], boot_bau.SKALA), form[1]))
        originale[name] = quelle.read_bytes()

    def specs_aus_quellen(_eintraege, _konfig, skala, ordner,
                          aktive_namen=None):
        specs = []
        for name in ("a", "b"):
            if aktive_namen is not None and name not in aktive_namen:
                continue
            pfad = os.path.join(ordner, name + ".obj")
            punkte, dreiecke = boot_bau.lade_obj(pfad)
            specs.append({
                "form": (gk._obj_zu_welt(punkte, skala), dreiecke),
                "_name": name,
                "_konflikt_name": name,
                "_quellpfad": pfad,
                "dichte": 1000.0,
            })
        return specs

    monkeypatch.setattr(fabriken, "_specs_aus_konfig", specs_aus_quellen)
    fenster = HauptFenster()
    fenster._vorrang_bei_konflikt_waehlen = lambda _konflikt: vorrang
    knoten = SimpleNamespace(
        name="testboot", eintrag={"teile": [{"name": "a"}, {"name": "b"}]})
    aktiv = [SimpleNamespace(name="a"), SimpleNamespace(name="b")]

    assert fenster._geometrie_konflikte_bereinigen(
        SimpleNamespace(), knoten, aktiv) is erfolgreich
    if erfolgreich:
        assert (quellordner / "a.obj").read_bytes() == originale["a"]
        assert not (quellordner / "a.obj.bak").exists()
        assert (quellordner / "b.obj").read_bytes() != originale["b"]
        assert (quellordner / "b.obj.bak").read_bytes() == originale["b"]
    else:
        for name in ("a", "b"):
            assert (quellordner / (name + ".obj")).read_bytes() == originale[name]
            assert not (quellordner / (name + ".obj.bak")).exists()
    fenster.close()


def test_abgebrochene_geometriekorrektur_stoppt_physiklauf(
        monkeypatch, tmp_path):
    from segelphysik.core import fabriken

    _qt_app()
    welt = welt_aus_konfig(_konfig_kopie(tmp_path))
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    fenster._geometrie_konflikte_bereinigen = lambda *_args: False

    class Bruecke:
        def __init__(self):
            self.sichtbarkeit = []

        def sichtbar_setzen(self, name, sichtbar):
            self.sichtbarkeit.append((name, sichtbar))

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    fenster._laufzeit_koerper["yacht1"] = object()
    simulation = []
    fenster._statische_simulation_ausfuehren = (
        lambda: simulation.append("gestartet"))
    monkeypatch.setattr(
        fabriken, "baue_summenkoerper",
        lambda *_args, **_kwargs: pytest.fail("Körper darf nicht gebaut werden"))

    fenster._laufzeit_objekte_aktualisieren("start")

    assert ("yacht1", False) in bruecke.sichtbarkeit
    assert all(not sichtbar for _name, sichtbar in bruecke.sichtbarkeit)
    assert "yacht1" not in fenster._laufzeit_koerper
    assert simulation == []
    fenster.close()


def test_statisch_modus_ruft_solver_auf_und_zeigt_ergebnis(
        monkeypatch, tmp_path):
    import math
    import time

    app = _qt_app()
    konfig = _konfig_kopie(tmp_path)
    welt = welt_aus_konfig(konfig)
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    koerper = _koerper_stub(masse=123.0)
    fenster._laufzeit_koerper["yacht1"] = koerper

    class Bruecke:
        def __init__(self):
            self.poses = []
            self.geloescht = []

        def statische_pose_setzen(self, name, z, phi):
            self.poses.append((name, z, phi))
            return True

        def statische_pose_loeschen(self, name):
            self.geloescht.append(name)

        def physik_pose_setzen(self, name, z, phi):
            return True

        def physik_basis_position_ermitteln(self, _name):
            return np.zeros(3)

        def physik_pose_6dof_setzen(self, _name, _rotation, _position):
            return True

        def layer_ist_an(self, _layer):
            return False

        def render(self):
            pass

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    params = _physik_stub(g=9.7, aufloesung=0.03)
    kraftaufrufe = []
    solveraufrufe = []
    hydrostatik = lambda *_args, **_kwargs: None
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik",
        lambda ordner: params)
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion",
        lambda koerper_arg, **kwargs:
            kraftaufrufe.append((koerper_arg, kwargs)) or hydrostatik)
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion_6dof",
        lambda *_args, **_kwargs: hydrostatik)
    monkeypatch.setattr(
        "segelphysik.core.statisch_robust.loese_robust",
        lambda kraft, masse, g, **_kw: solveraufrufe.append(
            (kraft, masse, g)) or {
            "z": 0.12, "phi": math.radians(5.0), "gm": 0.42,
            "iterationen": 7, "neutral": False, "stagnation": False,
            "restkraft": 0.0, "restmoment": 0.0,
        })

    fenster._btn_echtzeit.click()
    fenster._btn_statisch.click()
    ende = time.monotonic() + 2.0
    while not solveraufrufe and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)
    while fenster._solver_werte["Lösungstyp"].text(1) == \
            "Statische Berechnung läuft" and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)

    assert solveraufrufe
    assert len(kraftaufrufe) == 1
    assert kraftaufrufe[0][0] is not koerper
    assert kraftaufrufe[0][0].version == 0
    assert kraftaufrufe[0][1]["rho_w"] == konfig.wasser_dichte()
    assert kraftaufrufe[0][1]["g"] == params.g_m_pro_s2
    assert kraftaufrufe[0][1]["aufloesung"] == params.voxel_aufloesung_m
    assert len(solveraufrufe) == 1
    assert solveraufrufe[0][0].hydrostatik is hydrostatik
    assert solveraufrufe[0][1:] == (koerper.masse, 9.7)
    assert bruecke.poses[0][0] == "yacht1"
    assert bruecke.poses[0][1:] == (0.12, math.radians(5.0))
    assert fenster._solver_werte["z*"].text(1) == "0.1200 m"
    assert fenster._solver_werte["phi*"].text(1) == "5.00°"
    assert fenster._solver_werte["GM"].text(1) == "0.4200 m"
    assert fenster._solver_werte["Restkraft"].text(1) == "0 N"
    assert fenster._solver_werte["Restmoment"].text(1) == "0 N·m"
    assert fenster._solver_werte["Iterationen"].text(1) == "7"
    assert fenster._solver_werte["Lösungstyp"].text(1) == "stabil"
    fenster.close()


def test_echtzeit_gui_integriert_feste_physikschritte(monkeypatch, tmp_path):
    import numpy as np
    import threading
    import time

    app = _qt_app()
    welt = welt_aus_konfig(_konfig_kopie(tmp_path))
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    koerper = _koerper_stub(
        masse=2.0, traegheitstensor=np.diag([3.0, 1.0, 1.0]))
    fenster._laufzeit_koerper["yacht1"] = koerper

    class Bruecke:
        def __init__(self):
            self.poses = []
            self.renders = 0
            self.gui_thread = threading.get_ident()
            self.pose_thread = None
            self.render_thread = None

        def statische_pose_loeschen(self, name):
            pass

        def physik_pose_setzen(self, name, z, phi):
            self.pose_thread = threading.get_ident()
            self.poses.append((name, z, phi))
            return True

        def physik_basis_position_ermitteln(self, _name):
            return np.zeros(3)

        def physik_pose_6dof_setzen(self, name, rotation, position):
            self.pose_thread = threading.get_ident()
            self.poses.append((name, rotation, position))
            return True

        def layer_ist_an(self, _layer):
            return False

        def render(self):
            self.render_thread = threading.get_ident()
            self.renders += 1

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    physik = _physik_stub()
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik", lambda _ordner: physik)
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion_6dof",
        lambda *_args, **_kwargs: lambda *_a, **_k: SimpleNamespace(
            F_A=Vektor((0.0, 0.0, 0.0)),
            M=Vektor((0.0, 0.0, 0.0))))
    fenster._btn_echtzeit.click()

    fenster._echtzeit_letzte_wandzeit = 10.0
    fenster._echtzeit_timer.stop()
    monkeypatch.setattr(time, "perf_counter", lambda: 10.006)
    fenster._echtzeit_takt()
    ende = time.monotonic() + 2.0
    while fenster._echtzeit_aufgabe_laeuft and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)

    assert not fenster._echtzeit_aufgabe_laeuft
    assert fenster._echtzeit_zustand.geschwindigkeit_koerper[2] \
        == pytest.approx(-9.81 * 0.004), (
        fenster._echtzeit_aufgabe_laeuft,
        fenster._echtzeit_generation,
        fenster._solver_werte["Lösungstyp"].text(1),
        fenster.protokoll.toPlainText())
    assert fenster._echtzeit_zustand.position[2] \
        == pytest.approx(-9.81 * 0.004 ** 2)
    monkeypatch.setattr(time, "perf_counter", lambda: 10.03)
    fenster._echtzeit_render_takt()
    assert bruecke.poses[-1][0] == "yacht1"
    assert bruecke.poses[-1][2] == pytest.approx(
        (0.0, 0.0, -9.81 * 0.004 ** 2))
    assert bruecke.renders == 2
    assert bruecke.pose_thread == bruecke.gui_thread
    assert bruecke.render_thread == bruecke.gui_thread
    assert fenster._echtzeit_akkumulator == pytest.approx(0.002)
    fenster._zeit_pausieren()
    fenster.close()


def test_echtzeit_render_timer_misst_erfolgreiche_frames():
    from PySide6.QtCore import QEventLoop, QTimer
    from segelphysik.core.dynamik_6dof import Zustand6DOF

    _qt_app()
    fenster = HauptFenster()

    class Bruecke:
        def __init__(self):
            self.renders = 0

        def physik_pose_6dof_setzen(self, _name, _rotation, _position):
            return True

        def render(self):
            self.renders += 1

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    fenster._echtzeit_name = "yacht1"
    pose = Zustand6DOF()
    fenster._echtzeit_anzeige_start = pose
    fenster._echtzeit_anzeige_ziel = pose
    schleife = QEventLoop()
    QTimer.singleShot(1150, schleife.quit)
    fenster._echtzeit_render_timer.start()
    schleife.exec()

    fenster._echtzeit_render_timer.stop()
    assert fenster._echtzeit_render_timer.interval() == 33
    assert fenster._echtzeit_render_timer.timerType().name == "PreciseTimer"
    assert bruecke.renders >= 30
    assert fenster._echtzeit_angeforderte_fps >= 27.0
    fenster.close()


def test_echtzeit_physik_blockiert_gui_nicht_und_verwirft_pause_ergebnis(
        monkeypatch, tmp_path):
    import threading
    import time

    import numpy as np

    app = _qt_app()
    welt = welt_aus_konfig(_konfig_kopie(tmp_path))
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    fenster._laufzeit_koerper["yacht1"] = _koerper_stub(
        masse=2.0, traegheitstensor=np.diag([3.0, 1.0, 1.0]))

    class Bruecke:
        def __init__(self):
            self.gui_thread = threading.get_ident()
            self.pose_thread = None
            self.render_thread = None

        def statische_pose_loeschen(self, _name):
            pass

        def physik_pose_setzen(self, _name, _z, _phi):
            self.pose_thread = threading.get_ident()
            return True

        def physik_basis_position_ermitteln(self, _name):
            return np.zeros(3)

        def physik_pose_6dof_setzen(self, _name, _rotation, _position):
            self.pose_thread = threading.get_ident()
            return True

        def layer_ist_an(self, _layer):
            return False

        def render(self):
            self.render_thread = threading.get_ident()

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    physik = _physik_stub()
    gestartet = threading.Event()
    freigeben = threading.Event()
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik", lambda _ordner: physik)

    def langsame_kraftfunktion(*_args, **_kwargs):
        gestartet.set()
        freigeben.wait(timeout=2.0)
        return SimpleNamespace(
            F_A=Vektor((0.0, 0.0, 0.0)),
            M=Vektor((0.0, 0.0, 0.0)))

    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion_6dof",
        lambda *_args, **_kwargs: langsame_kraftfunktion)
    fenster._btn_echtzeit.click()
    fenster._echtzeit_timer.stop()
    bruecke.pose_thread = None
    bruecke.render_thread = None
    fenster._echtzeit_letzte_wandzeit = 10.0
    monkeypatch.setattr(time, "perf_counter", lambda: 10.006)
    fenster._echtzeit_takt()
    assert gestartet.wait(timeout=1.0)

    gui_ereignis = threading.Event()
    QTimer.singleShot(0, gui_ereignis.set)
    ende = time.monotonic() + 0.1
    while not gui_ereignis.is_set() and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)
    assert gui_ereignis.is_set()

    fenster._zeit_pausieren()
    freigeben.set()
    ende = time.monotonic() + 2.0
    while fenster._echtzeit_aufgabe_laeuft and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)
    assert not fenster._echtzeit_aufgabe_laeuft
    assert bruecke.pose_thread is None
    assert bruecke.render_thread is None
    fenster.close()


def test_solverfehler_zeigt_abbruchgrund_und_letzte_residuen(
        monkeypatch, tmp_path):
    import time

    from segelphysik.core.statisch import SolverFehler

    _qt_app()
    welt = welt_aus_konfig(_konfig_kopie(tmp_path))
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    fenster._laufzeit_koerper["yacht1"] = _koerper_stub(masse=10.0)

    class Bruecke:
        def __init__(self):
            self.poses = []

        def statische_pose_setzen(self, name, z, phi):
            self.poses.append((name, z, phi))
            return True

        def statische_pose_loeschen(self, _name):
            pass

    fenster._bruecke = Bruecke()
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik",
        lambda _ordner: _physik_stub())
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion",
        lambda *_args, **_kwargs: lambda *_a, **_k: None)

    def solverfehler(*_args, **_kwargs):
        raise SolverFehler(
            "Störleiter erschöpft", status="instabile_lage",
            diagnose={"z": -0.2, "phi": 0.1, "restkraft": 2.5,
                      "restmoment": 4.0})

    monkeypatch.setattr(
        "segelphysik.core.statisch_robust.loese_robust", solverfehler)

    fenster._statische_simulation_ausfuehren()
    ende = time.monotonic() + 2.0
    while fenster._solver_werte["Lösungstyp"].text(1) == \
            "Statische Berechnung läuft" and time.monotonic() < ende:
        QApplication.processEvents()
        time.sleep(0.005)

    assert fenster._solver_werte["Lösungstyp"].text(1).startswith(
        "Kandidat nicht übernommen – Instabile Lage:")
    assert fenster._bruecke.poses == []
    assert fenster._solver_werte["Restkraft"].text(1) == "2.5 N"
    assert fenster._solver_werte["Restmoment"].text(1) == "4 N·m"
    assert fenster._solver_werte["z*"].text(1) == "-0.2000 m"
    assert fenster._solver_werte["phi*"].text(1) == "5.73°"
    fenster.close()


def test_statischer_solver_blockiert_gui_nicht_und_verwirft_altes_ergebnis(
        monkeypatch, tmp_path):
    import threading
    import time

    app = _qt_app()
    welt = welt_aus_konfig(_konfig_kopie(tmp_path))
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    fenster._laufzeit_koerper["yacht1"] = _koerper_stub(masse=10.0)
    gestartet = threading.Event()
    freigeben = threading.Event()

    class Bruecke:
        def __init__(self):
            self.poses = []
            self.geloescht = []

        def statische_pose_setzen(self, *pose):
            self.poses.append(pose)
            return True

        def statische_pose_loeschen(self, name):
            self.geloescht.append(name)

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik",
        lambda _ordner: _physik_stub())
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion",
        lambda *_args, **_kwargs: lambda *_a, **_k: None)

    def langsamer_solver(*_args, **_kwargs):
        gestartet.set()
        freigeben.wait(timeout=2.0)
        return {
            "z": 0.1, "phi": 0.2, "gm": 0.3, "iterationen": 4,
            "restkraft": 0.0, "restmoment": 0.0,
            "neutral": False, "stagnation": False,
        }

    monkeypatch.setattr(
        "segelphysik.core.statisch_robust.loese_robust", langsamer_solver)
    fenster._kraftbild_daten_setzen = lambda *_args, **_kwargs: None
    fenster._statische_simulation_ausfuehren()
    assert gestartet.wait(timeout=1.0)

    gui_ereignis = threading.Event()
    QTimer.singleShot(0, gui_ereignis.set)
    ende = time.monotonic() + 0.1
    while not gui_ereignis.is_set() and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)
    assert gui_ereignis.is_set()

    fenster._echtzeit_starten = lambda **_kwargs: None
    fenster._btn_echtzeit.click()
    freigeben.set()
    ende = time.monotonic() + 2.0
    while fenster._solver_werte["Lösungstyp"].text(1) == \
            "Statische Berechnung läuft" and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)

    assert not bruecke.poses
    assert fenster._solver_werte["Lösungstyp"].text(1) != "stabil"
    fenster.close()


def test_echtzeit_yacht_voxel_last_laesst_gui_reagieren(
        monkeypatch, tmp_path):
    import threading
    import time

    import numpy as np

    app = _qt_app()
    konfiguration = _konfig_kopie(tmp_path)
    welt = welt_aus_konfig(konfiguration)
    sichtbarkeit_setzen(welt, "yacht1")
    yacht_knoten = finde(welt, "yacht1")
    from segelphysik.core.fabriken import baue_summenkoerper
    from segelphysik.core.konfig_lader import lade_physik

    koerper, _ = baue_summenkoerper(
        konfiguration, "yacht1",
        aktive_blaetter=aktive_blaetter(yacht_knoten))
    projektordner = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    physik = lade_physik(os.path.join(projektordner, "konfigurationen"))
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    fenster._laufzeit_koerper["yacht1"] = koerper

    class Bruecke:
        def __init__(self):
            self.gui_thread = threading.get_ident()
            self.pose_thread = None
            self.render_thread = None

        def statische_pose_loeschen(self, _name):
            pass

        def physik_pose_setzen(self, _name, _z, _phi):
            self.pose_thread = threading.get_ident()
            return True

        def physik_basis_position_ermitteln(self, _name):
            return np.zeros(3)

        def physik_pose_6dof_setzen(self, _name, _rotation, _position):
            self.pose_thread = threading.get_ident()
            return True
        def layer_ist_an(self, _layer):
            return False

        def render(self):
            self.render_thread = threading.get_ident()

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik",
        lambda _ordner: physik)
    fenster._btn_echtzeit.click()
    fenster._echtzeit_timer.stop()
    fenster._echtzeit_letzte_wandzeit = time.perf_counter() - 0.016

    gui_ereignis = threading.Event()
    QTimer.singleShot(0, gui_ereignis.set)
    ereignis_start = time.perf_counter()
    fenster._echtzeit_takt()
    ende = time.monotonic() + 30.0
    while not gui_ereignis.is_set() and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.001)
    reaktionszeit = time.perf_counter() - ereignis_start
    assert gui_ereignis.is_set()
    assert reaktionszeit < 0.1

    ende = time.monotonic() + 30.0
    while fenster._echtzeit_aufgabe_laeuft and time.monotonic() < ende:
        app.processEvents()
        time.sleep(0.005)

    assert not fenster._echtzeit_aufgabe_laeuft
    fenster._echtzeit_render_takt()
    assert bruecke.pose_thread == bruecke.gui_thread
    assert bruecke.render_thread == bruecke.gui_thread
    assert fenster._echtzeit_zustand is not None
    fenster._zeit_pausieren()
    fenster.close()


def test_statusliste_kennt_alle_echtzeit_schluessel():
    _qt_app()
    fenster = HauptFenster()
    fenster._solver_status_aktualisieren({
        "Bildrate": "60.0 FPS", "Zeitfaktor": "1.00 ×",
        "Physik angefordert": "1.000 s", "Unbekannt": "x"})
    assert fenster._solver_werte["Zeitfaktor"].text(1) == "1.00 ×"
    assert fenster._solver_werte["Bildrate"].text(1) == "60.0 FPS"


def test_fremdkraftaenderung_startet_statische_neuberechnung(monkeypatch):
    app = _qt_app()
    fenster = HauptFenster()
    aufrufe = []

    def neuberechnen():
        fremdkraft = fenster._fremdkraft_aktuell()
        aufrufe.append(fremdkraft)
        fenster._statische_fremdkraft = fremdkraft

    monkeypatch.setattr(
        fenster, "_statische_simulation_ausfuehren",
        neuberechnen)
    try:
        fenster._fremd_felder["betrag"].setValue(125.0)
        assert aufrufe == []

        fenster._fremd_check.setChecked(True)
        assert len(aufrufe) == 1
        assert aufrufe[-1] is not None

        fenster._fremd_felder["betrag"].setValue(250.0)
        assert len(aufrufe) == 2
        assert aufrufe[-1][0][1] == pytest.approx(250.0)

        fenster._fremd_check.setChecked(False)
        assert len(aufrufe) == 3
        assert aufrufe[-1] is None

        fenster._fremd_felder["betrag"].setValue(500.0)
        assert len(aufrufe) == 3
    finally:
        fenster.close()
        app.processEvents()
