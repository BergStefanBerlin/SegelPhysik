import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.gui.baum import finde, sichtbarkeit_setzen, welt_aus_konfig
from segelphysik.gui.baum_widget import BaumWidget
from segelphysik.gui.hauptfenster import HauptFenster


def _qt_app():
    return QApplication.instance() or QApplication([])


def _konfig_kopie(tmp_path):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(root, "konfigurationen")
    for name in ("materialien.json", "koerper.json"):
        with open(os.path.join(config_dir, name), "rb") as original:
            (tmp_path / name).write_bytes(original.read())
    return lade_konfig(str(tmp_path))


def test_gui_aenderungen_bleiben_sitzungsgebunden(tmp_path):
    _qt_app()
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


def test_statisch_modus_ruft_solver_auf_und_zeigt_ergebnis(
        monkeypatch, tmp_path):
    import math

    _qt_app()
    konfig = _konfig_kopie(tmp_path)
    welt = welt_aus_konfig(konfig)
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    koerper = SimpleNamespace(masse=123.0)
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

        def layer_ist_an(self, _layer):
            return False

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    params = SimpleNamespace(g_m_pro_s2=9.7, voxel_aufloesung_m=0.03)
    kraftaufrufe = []
    solveraufrufe = []
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik",
        lambda ordner: params)
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion",
        lambda koerper_arg, **kwargs:
            kraftaufrufe.append((koerper_arg, kwargs)) or "kraftfunktion")
    monkeypatch.setattr(
        "segelphysik.core.statisch_robust.loese_robust",
        lambda kraft, masse, g: solveraufrufe.append((kraft, masse, g)) or {
            "z": 0.12, "phi": math.radians(5.0), "gm": 0.42,
            "iterationen": 7, "neutral": False,
        })

    fenster._btn_echtzeit.click()
    fenster._btn_statisch.click()

    assert len(kraftaufrufe) == 2
    assert kraftaufrufe[0][0] is koerper
    assert kraftaufrufe[0][1]["rho_w"] == konfig.wasser_dichte()
    assert kraftaufrufe[0][1]["g"] == params.g_m_pro_s2
    assert kraftaufrufe[0][1]["aufloesung"] == params.voxel_aufloesung_m
    assert solveraufrufe == [("kraftfunktion", koerper.masse, 9.7)]
    assert bruecke.poses[0][0] == "yacht1"
    assert bruecke.poses[0][1:] == (0.12, math.radians(5.0))
    assert fenster._solver_werte["z*"].text(1) == "0.1200 m"
    assert fenster._solver_werte["phi*"].text(1) == "5.00°"
    assert fenster._solver_werte["GM"].text(1) == "0.4200 m"
    assert fenster._solver_werte["Iterationen"].text(1) == "7"
    assert fenster._solver_werte["Lösungstyp"].text(1) == "stabil"
    fenster.close()


def test_echtzeit_gui_integriert_feste_physikschritte(monkeypatch, tmp_path):
    import numpy as np
    import time

    _qt_app()
    welt = welt_aus_konfig(_konfig_kopie(tmp_path))
    sichtbarkeit_setzen(welt, "yacht1")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    koerper = SimpleNamespace(
        masse=2.0, traegheitstensor=np.diag([3.0, 1.0, 1.0]))
    fenster._laufzeit_koerper["yacht1"] = koerper

    class Bruecke:
        def __init__(self):
            self.poses = []
            self.renders = 0

        def statische_pose_loeschen(self, name):
            pass

        def physik_pose_setzen(self, name, z, phi):
            self.poses.append((name, z, phi))
            return True

        def layer_ist_an(self, _layer):
            return False

        def render(self):
            self.renders += 1

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    physik = SimpleNamespace(
        dt_s=0.004, g_m_pro_s2=9.81, daempfung_tauchung=0.0,
        daempfung_kraengung=0.0, voxel_aufloesung_m=0.05)
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_physik", lambda _ordner: physik)
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion",
        lambda *_args, **_kwargs: lambda *_a, **_k: SimpleNamespace(
            F_A=SimpleNamespace(z=0.0), M=SimpleNamespace(x=0.0)))
    fenster._btn_echtzeit.click()

    fenster._echtzeit_letzte_wandzeit = 10.0
    monkeypatch.setattr(time, "perf_counter", lambda: 10.006)
    fenster._echtzeit_takt()

    assert fenster._echtzeit_zustand.v_z == pytest.approx(-9.81 * 0.004)
    assert fenster._echtzeit_zustand.z == pytest.approx(-9.81 * 0.004 ** 2)
    assert bruecke.poses[-1][0] == "yacht1"
    assert bruecke.poses[-1][1:] == pytest.approx(
        (-9.81 * 0.004 ** 2, 0.0))
    assert bruecke.renders == 1
    fenster._zeit_pausieren()
    fenster.close()
