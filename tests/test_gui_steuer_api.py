import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication, QLabel, QTreeWidgetItem

from segelphysik.gui.hauptfenster import HauptFenster
from segelphysik.core.stationaer_hydrodynamik import StationaereStufe
from segelphysik.core.konfig_lader import lade_konfig


@pytest.fixture
def fenster():
    app = QApplication.instance() or QApplication([])
    widget = HauptFenster()
    yield widget
    widget.close()
    app.processEvents()


def test_controls_are_discoverable_and_snapshot_is_json_serializable(fenster):
    api = fenster.steuer_api

    control_list = api.controls()
    controls = {item["id"]: item for item in control_list}

    assert len(controls) == len(control_list)
    assert "fremd_felder.betrag" in controls
    assert "fremd_check" in controls
    assert controls["fremd_felder.betrag"]["value"] == 100.0
    assert api.get_control("fremd_felder.betrag")["value"] == 100.0

    snapshot = api.snapshot()
    json.dumps(snapshot)
    for control_id in controls:
        api.get_control(control_id)
    assert snapshot["mode"] == "statisch"
    assert snapshot["body"]["available"] is False
    assert snapshot["settings"]["data"]
    assert snapshot["external_force"] is None


def test_set_control_uses_gui_signals_and_checks_input_types(fenster):
    api = fenster.steuer_api

    api.set_control("fremd_felder.betrag", 20.0)
    api.set_control("fremd_felder.azimut", 0.0)
    api.set_control("fremd_check", True)

    assert fenster._fremd_felder["betrag"].value() == 20.0
    assert fenster._fremd_check.isChecked()
    assert fenster.steuer_api.snapshot()["external_force"] == [
        [20.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    with pytest.raises(TypeError, match="boolesch"):
        api.set_control("fremd_check", "false")

    api.set_control("btn_echtzeit", True)
    assert api.snapshot()["mode"] == "echtzeit"
    assert not fenster._btn_statisch.isChecked()


def test_body_switch_reloads_the_calibrated_test_force_profile(fenster):
    fenster._laufzeit_koerper["yacht1"] = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            hydrodynamik_teile=(("rumpf", "Rumpf", (), ()),)))
    fenster._hydrodynamik_profil_auswahl_setzen("yacht1")

    assert fenster._fremd_check.isChecked()
    assert fenster._fremd_felder["betrag"].value() == pytest.approx(510.1)
    assert fenster._fremd_felder["azimut"].value() == 0.0
    assert fenster._fremd_felder["elevation"].value() == 0.0
    assert fenster._fremd_felder["z"].value() == pytest.approx(1.5)
    kraft, punkt = fenster._fremdkraft_aktuell()
    assert kraft == pytest.approx((510.1, 0.0, 0.0))
    assert punkt == pytest.approx((0.0, 0.0, 1.5))

    fenster._fremd_felder["betrag"].setValue(125.0)
    fenster._hydrodynamik_profil_auswahl_setzen("yacht1")
    assert fenster._fremd_felder["betrag"].value() == pytest.approx(125.0)
    fenster._hydrodynamik_profil_auswahl_setzen("quader")
    assert not fenster._fremd_check.isChecked()
    assert fenster._fremd_felder["betrag"].value() == 0.0
    assert fenster._ruderwinkel_feld.value() == 0.0

    fenster._hydrodynamik_profil_auswahl_setzen("yacht1")
    assert fenster._fremd_check.isChecked()
    assert fenster._fremd_felder["betrag"].value() == pytest.approx(510.1)
    assert fenster._fremd_felder["z"].value() == pytest.approx(1.5)


def test_body_switch_loads_configured_generic_hydrodynamic_profile(fenster):
    profile = {
        "quader": {
            "modell": "generischer_volumenkoerper",
            "cd_volumenkoerper": 1.05,
            "testkraft_N": [20.0, 0.0, 0.0],
            "angriffspunkt_m": [0.0, 0.0, 0.0],
            "referenzgeschwindigkeit_m_pro_s": 1.0,
            "ruderwinkel_grad": 0.0,
            "status": "vorläufig",
        }
    }
    fenster.baum._welt = SimpleNamespace(
        konfiguration=SimpleNamespace(hydrodynamik_profile=profile))
    fenster._laufzeit_koerper["quader"] = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            blatt_meshes=((np.zeros((3, 3)), np.zeros((1, 3))),),
            hydrodynamik_teile=()))
    fenster._hydrodynamik_profil_auswahl_setzen("quader")

    assert fenster._fremd_check.isChecked()
    assert fenster._fremd_felder["betrag"].value() == pytest.approx(20.0)
    assert fenster._hydrodynamik_profil_koerper == "quader"


@pytest.mark.parametrize(
    "koerper_id",
    (
        "kegel", "quader", "pyramide", "kugel",
        "rolle", "platte", "bleistift", "unregelmaessig",
    ),
)
def test_gui_loads_each_configured_generic_default(fenster, koerper_id):
    wurzel = Path(__file__).resolve().parents[1]
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    profil = konfiguration.hydrodynamik_profile[koerper_id]
    fenster.baum._welt = SimpleNamespace(konfiguration=konfiguration)
    fenster._laufzeit_koerper[koerper_id] = SimpleNamespace(
        snapshot=lambda: SimpleNamespace(
            blatt_meshes=((np.zeros((3, 3)), np.zeros((1, 3))),),
            hydrodynamik_teile=()))

    fenster._hydrodynamik_profil_auswahl_setzen(koerper_id)

    kraft, punkt = fenster._fremdkraft_aktuell()
    assert fenster._fremd_check.isChecked()
    assert kraft == pytest.approx(profil["testkraft_N"])
    assert punkt == pytest.approx(profil["angriffspunkt_m"])
    assert fenster._ruderwinkel_feld.value() == pytest.approx(
        profil["ruderwinkel_grad"])


@pytest.mark.parametrize(
    ("solver_konvergiert", "dynamik_bestanden", "fehlergrund"),
    ((True, True, None), (True, False, None),
     (True, False, "ValueError: Kraftmodell instabil"),
     (False, None, None)))
def test_stationary_status_reports_dynamic_verification(
        fenster, monkeypatch, solver_konvergiert, dynamik_bestanden,
        fehlergrund):
    monkeypatch.setattr(
        "segelphysik.gui.hauptfenster.formerkennung.klassifiziere_koerper",
        lambda _koerper: "yacht")
    monkeypatch.setattr(
        "segelphysik.gui.hauptfenster.statusanzeige.status_aus_ergebnis",
        lambda *_args, **_kwargs: ("statisch", "ok"))
    fenster._statisch_generation = 1
    fenster._laufzeit_koerper["yacht1"] = object()
    fenster._navigationsanzeigen_aktualisieren = lambda: None
    fenster._kraftbild_daten_setzen = lambda *_args, **_kwargs: None
    werte = {}
    overlays = []
    fenster._solver_status_aktualisieren = werte.update
    fenster._statusoverlay = overlays.append

    class Bruecke:
        @staticmethod
        def physik_basis_position_ermitteln(_name):
            return np.zeros(3)

        @staticmethod
        def physik_pose_6dof_setzen(_name, _rotation, _position):
            return True

        @staticmethod
        def statische_pose_setzen(_name, _z, _phi):
            return True

    fenster._bruecke = Bruecke()
    stufe = StationaereStufe(
        "gekoppeltes Gleichgewicht", solver_konvergiert, 3,
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0), (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0, 0.0)
    ergebnis = {
        "z": 0.0, "phi": 0.0, "gm": None, "restkraft": 0.0,
        "restmoment": 0.0, "iterationen": 3,
        "stationaer_hydrodynamik": SimpleNamespace(
            konvergiert=solver_konvergiert,
            stufen=(stufe,), laufzeit_s=0.37),
    }
    if dynamik_bestanden is not None:
        ergebnis["stationaer_dynamikpruefung"] = SimpleNamespace(
            bestanden=dynamik_bestanden,
            relative_vorwaertsabweichung=(
                0.0 if dynamik_bestanden else 0.02),
            orientierung_ende_rad=(
                0.0 if dynamik_bestanden else 0.1),
            winkelgeschwindigkeit_ende_rad_s=(
                0.0 if dynamik_bestanden else 0.02),
            fehlergrund=fehlergrund)
    else:
        ergebnis["stationaer_fehler"] = "Newton-Stufe fehlgeschlagen"
    fenster._statische_aufgabe_abgeschlossen(
        1, "yacht1", ergebnis,
        (lambda *_args, **_kwargs: None, object()), None)

    if not solver_konvergiert:
        assert "nicht vollständig konvergiert" in werte["Lösungstyp"]
        assert "Nicht ausgeführt" in werte["Dynamikprüfung"]
    else:
        assert ("Bestanden" if dynamik_bestanden else "Nicht bestanden") in (
            werte["Dynamikprüfung"])
        if fehlergrund:
            assert fehlergrund in werte["Dynamikprüfung"]
            assert fehlergrund in overlays[-1][0]
    assert overlays[-1][1] == (
        "ok" if dynamik_bestanden else "problem")


def test_tree_item_checkboxes_use_the_tree_check_column(fenster):
    item = QTreeWidgetItem(["Welt"])
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(1, Qt.CheckState.Unchecked)
    fenster.baum.addTopLevelItem(item)

    api = fenster.steuer_api
    assert api.get_control("baum.item.Welt")["value"]["checked"] is False

    api.set_control("baum.item.Welt", True)
    assert item.checkState(1) == Qt.CheckState.Checked
    api.set_control("baum.item.Welt", False)
    assert item.checkState(1) == Qt.CheckState.Unchecked


def test_snapshot_serializes_deleted_qt_widget_references(fenster):
    deleted = QLabel(fenster)
    fenster.deleted_widget = deleted
    deleted.deleteLater()
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    assert fenster.steuer_api.variables()["deleted_widget"] == {
        "type": "QLabel", "valid": False}
    json.dumps(fenster.steuer_api.snapshot())
