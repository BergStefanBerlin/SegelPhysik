import os
import time
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from segelphysik.gui.hauptfenster import HauptFenster
from segelphysik.core.overlays import (
    LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN, LAYER_KRAEFTE, LAYER_MOMENTE,
)


def test_modusknopfe_sind_gegenseitig_exklusiv():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    zeitschieber = (fenster._btn_halt, fenster._btn_vor)

    assert fenster._btn_halt.text() == "="
    assert fenster._btn_vor.text() == ">"
    assert fenster._btn_statisch.isChecked()
    assert not fenster._btn_echtzeit.isChecked()
    assert all(not knopf.isEnabled() for knopf in zeitschieber)
    assert all(not knopf.styleSheet() for knopf in zeitschieber)

    QTest.mouseClick(fenster._btn_echtzeit, Qt.MouseButton.LeftButton)

    assert not fenster._btn_statisch.isChecked()
    assert fenster._btn_echtzeit.isChecked()
    assert all(knopf.isEnabled() for knopf in zeitschieber)
    assert sum("#0078d4" in knopf.styleSheet() for knopf in zeitschieber) == 1
    fenster._echtzeit_kraftfunktion = object()
    QTest.mouseClick(fenster._btn_vor, Qt.MouseButton.LeftButton)
    assert fenster._echtzeit_timer.isActive()
    assert fenster._btn_vor.isChecked() and not fenster._btn_halt.isChecked()
    assert "#0078d4" in fenster._btn_vor.styleSheet()
    assert not fenster._btn_halt.styleSheet()
    QTest.mouseClick(fenster._btn_halt, Qt.MouseButton.LeftButton)
    assert not fenster._echtzeit_timer.isActive()
    assert fenster._btn_halt.isChecked() and not fenster._btn_vor.isChecked()
    assert "#0078d4" in fenster._btn_halt.styleSheet()
    assert not fenster._btn_vor.styleSheet()
    QTest.mouseClick(fenster._btn_vor, Qt.MouseButton.LeftButton)
    assert fenster._echtzeit_timer.isActive()

    QTest.mouseClick(fenster._btn_statisch, Qt.MouseButton.LeftButton)

    assert fenster._btn_statisch.isChecked()
    assert not fenster._btn_echtzeit.isChecked()
    assert all(not knopf.isEnabled() for knopf in zeitschieber)
    assert all(not knopf.styleSheet() for knopf in zeitschieber)
    fenster.close()
    app.processEvents()


def test_layer_und_darstellungssteuerung_sind_angebunden():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()

    class Bruecke:
        def __init__(self):
            self.layer = []
            self.darstellung = []
            self.renders = 0

        def layer_setzen(self, layer, aktiviert):
            self.layer.append((layer, aktiviert))

        def render(self):
            self.renders += 1

        def kamera_preset_setzen(self, preset):
            self.darstellung.append(("kamera", preset))
            return True

        def hintergrund_setzen(self, preset):
            self.darstellung.append(("hintergrund", preset))
            return True

        def beleuchtung_setzen(self, aktiviert):
            self.darstellung.append(("licht", aktiviert))
            return True

        def wasser_sichtbar_setzen(self, sichtbar):
            self.darstellung.append(("wasser", sichtbar))
            return True

        def wasseroptik_setzen(self, aktiviert):
            self.darstellung.append(("wasseroptik", aktiviert))
            return True

        def ssao_setzen(self, aktiviert):
            self.darstellung.append(("ssao", aktiviert))
            return True

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    fenster._layer_checks["Schwerpunkt"].click()
    fenster._layer_checks["Achsen"].click()
    fenster._layer_checks["Kräfte"].click()
    fenster._layer_checks["Momente"].click()
    fenster._kamera_auswahl.setCurrentIndex(
        fenster._kamera_auswahl.findData("bug"))
    fenster._hintergrund_auswahl.setCurrentIndex(1)
    fenster._ssao_check.click()

    assert bruecke.layer == [
        (LAYER_SCHWERPUNKT, False), (LAYER_HAUPTACHSEN, True),
        (LAYER_KRAEFTE, False), (LAYER_MOMENTE, False)]
    assert bruecke.darstellung == [
        ("kamera", "bug"), ("hintergrund", "weiss"), ("ssao", False)]
    assert bruecke.renders == 4
    fenster.close()
    app.processEvents()


def test_pause_bucht_inflight_schritte_genau_einmal_zurueck():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    fenster._echtzeit_generation = 3
    fenster._echtzeit_name = "alt"
    fenster._echtzeit_physik = SimpleNamespace(dt_s=0.004)
    fenster._echtzeit_angefordert_s = 0.5
    fenster._echtzeit_berechnet_s = 0.2
    fenster._echtzeit_akkumulator = 0.1
    fenster._echtzeit_schritte_laufend = 50
    fenster._echtzeit_aufgabe_laeuft = True
    fenster._echtzeit_aufgabe_sequenz_laufend = 7

    fenster._zeit_pausieren()

    assert abs(fenster._echtzeit_akkumulator - 0.3) < 1e-12
    assert fenster._echtzeit_schritte_laufend == 0
    assert abs(fenster._echtzeit_rueckstand_s() - 0.3) < 1e-12
    fenster._echtzeit_name = "neu"
    fenster._echtzeit_generation += 1
    fenster._echtzeit_aufgabe_abgeschlossen(
        3, 7, "alt", object(), object(), None, 0.01)
    assert abs(fenster._echtzeit_akkumulator - 0.3) < 1e-12
    assert abs(fenster._echtzeit_rueckstand_s() - 0.3) < 1e-12
    fenster.close()
    app.processEvents()


def test_fortsetzen_waehlt_nachholmodus_fuer_erhaltenen_rueckstand():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    fenster._echtzeit_kraftfunktion = object()
    fenster._echtzeit_angefordert_s = 0.5
    fenster._echtzeit_akkumulator = 0.5
    fenster._btn_echtzeit.setChecked(True)

    fenster._zeit_fortsetzen()

    assert fenster._echtzeit_modus == "nachholen"
    assert fenster._echtzeit_timer.isActive()
    fenster._zeit_pausieren()
    fenster.close()
    app.processEvents()


def test_ueberlast_wird_nach_fuenf_sekunden_automatisch_pausiert(
        monkeypatch):
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    fenster._einstellungen.setzen("dynamisch", "zeitgenau", True)
    jetzt = 105.0
    fenster._echtzeit_zustand = object()
    fenster._echtzeit_physik = SimpleNamespace(dt_s=0.01)
    fenster._echtzeit_angefordert_s = 1.0
    fenster._echtzeit_akkumulator = 1.0
    fenster._echtzeit_modus = "ueberlast_beobachtung"
    fenster._echtzeit_ueberlast_seit = 100.0
    fenster._echtzeit_letzte_wandzeit = jetzt
    fenster._echtzeit_timer.start()
    monkeypatch.setattr(time, "perf_counter", lambda: jetzt)

    fenster._echtzeit_takt()

    assert fenster._echtzeit_modus == "automatisch_pausiert"
    assert not fenster._echtzeit_timer.isActive()
    assert fenster._echtzeit_rueckstand_s() == 1.0
    fenster.close()
    app.processEvents()


def test_alter_auftragsabschluss_wird_an_sequenzverworfen():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    fenster._echtzeit_aufgabe_laeuft = True
    fenster._echtzeit_aufgabe_sequenz_laufend = 8
    fenster._echtzeit_schritte_laufend = 4

    fenster._echtzeit_aufgabe_abgeschlossen(
        1, 7, "yacht1", object(), object(), None, 0.01)

    assert fenster._echtzeit_aufgabe_laeuft
    assert fenster._echtzeit_aufgabe_sequenz_laufend == 8
    assert fenster._echtzeit_schritte_laufend == 4
    fenster.close()
    app.processEvents()


def test_vor_koerperwechsel_uebernommener_schritt_wird_nicht_doppelt_gebucht():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    fenster._echtzeit_generation = 2
    fenster._echtzeit_name = "alt"
    fenster._echtzeit_zustand = object()
    fenster._echtzeit_physik = SimpleNamespace(dt_s=0.1)
    fenster._echtzeit_angefordert_s = 0.2
    fenster._echtzeit_aufgabe_sequenz_laufend = 9
    fenster._echtzeit_schritte_laufend = 2
    fenster._btn_echtzeit.setChecked(True)
    alter_zustand = object()

    fenster._echtzeit_aufgabe_abgeschlossen(
        2, 9, "alt", alter_zustand, object(), None, 0.1)

    assert fenster._echtzeit_berechnet_s == 0.2
    assert fenster._echtzeit_zustand is alter_zustand
    neuer_zustand = object()
    fenster._echtzeit_generation += 1
    fenster._echtzeit_name = "neu"
    fenster._echtzeit_zustand = neuer_zustand
    fenster._echtzeit_aufgabe_abgeschlossen(
        2, 9, "alt", alter_zustand, object(), None, 0.1)

    assert fenster._echtzeit_berechnet_s == 0.2
    assert fenster._echtzeit_zustand is neuer_zustand
    fenster.close()
    app.processEvents()


def test_unterschreiten_der_ueberlastschwelle_setzt_frist_zurueck(
        monkeypatch):
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    fenster._einstellungen.setzen("dynamisch", "zeitgenau", True)
    fenster._echtzeit_zustand = object()
    fenster._echtzeit_physik = SimpleNamespace(dt_s=0.01)
    fenster._echtzeit_angefordert_s = 0.989
    fenster._echtzeit_akkumulator = 0.989
    fenster._echtzeit_modus = "ueberlast_beobachtung"
    fenster._echtzeit_ueberlast_seit = 94.0
    fenster._echtzeit_letzte_wandzeit = 99.99
    fenster._echtzeit_aufgabe_laeuft = True
    fenster._echtzeit_timer.start()
    monkeypatch.setattr(time, "perf_counter", lambda: 100.0)

    fenster._echtzeit_takt()

    assert fenster._echtzeit_modus == "normal"
    assert fenster._echtzeit_ueberlast_seit is None
    assert fenster._echtzeit_timer.isActive()
    fenster._zeit_pausieren()
    fenster.close()
    app.processEvents()


def _statischen_fehler_zustellen(fenster, status, diagnose):
    from segelphysik.core.statisch import SolverFehler

    class Bruecke:
        def __init__(self):
            self.gesetzt = []
            self.geloescht = []

        def statische_pose_setzen(self, name, z, phi):
            self.gesetzt.append((name, z, phi))
            return True

        def statische_pose_loeschen(self, name):
            self.geloescht.append(name)

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    fenster._laufzeit_koerper["k"] = object()
    fenster._statisch_generation = 3
    fenster._btn_statisch.setChecked(True)
    fenster._statische_ergebnisse["k"] = {"z": 0.0}
    werte = {}
    fenster._solver_status_aktualisieren = werte.update
    fenster._statische_aufgabe_abgeschlossen(
        3, "k", None, None,
        SolverFehler("x", status=status, diagnose=diagnose))
    return bruecke, werte


def test_instabiler_kandidat_wird_als_solcher_angezeigt():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    for status in ("instabile_lage", "stagnation", "budget_erschoepft"):
        bruecke, werte = _statischen_fehler_zustellen(
            fenster, status, {"z": 0.1, "phi": 0.2})
        assert bruecke.gesetzt == [("k", 0.1, 0.2)]
        assert werte["Lösungstyp"].startswith("Kandidat")
        assert "k" not in fenster._statische_ergebnisse
    fenster.close()
    app.processEvents()


def test_ungueltige_rechenergebnisse_zeigen_keine_pose():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    bruecke, werte = _statischen_fehler_zustellen(
        fenster, "ungueltige_rechenergebnisse",
        {"z": float("nan"), "phi": 0.2})
    assert bruecke.gesetzt == []
    assert bruecke.geloescht == ["k"]
    assert not werte["Lösungstyp"].startswith("Kandidat")
    fenster.close()
    app.processEvents()

def test_umbau_haelt_modellpose_bei_schwerpunktwechsel():
    from types import SimpleNamespace
    import numpy as np
    from segelphysik.core.dynamik_6dof import Zustand6DOF, quaternion_matrix
    from segelphysik.gui.hauptfenster import HauptFenster

    phi = 0.3
    q = (np.cos(phi / 2), np.sin(phi / 2), 0.0, 0.0)
    zustand = Zustand6DOF(position=(1.0, 2.0, -0.5), quaternion=q)
    fake = SimpleNamespace(
        _echtzeit_zustand=zustand, _echtzeit_name="yacht",
        _laufzeit_schwerpunkt={"yacht": (0.0, 0.0, 0.2)})
    alt = {"yacht": (0.0, 0.0, -0.4)}

    neu = HauptFenster._zustand_nach_umbau(fake, alt)

    r = quaternion_matrix(q)
    punkt = np.array([0.3, 0.1, 0.0])
    vorher = np.array(zustand.position) + r @ (punkt - np.array(alt["yacht"]))
    nachher = np.array(neu.position) + r @ (
        punkt - np.array(fake._laufzeit_schwerpunkt["yacht"]))
    assert np.allclose(vorher, nachher)