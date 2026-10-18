import math
from pathlib import Path
from xml.etree import ElementTree as ET
from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core.dynamik_6dof import (
    quaternion_aus_matrix,
)
from segelphysik.core.navigationsanzeigen import (
    navigationswerte_ableiten,
    richtung_16,
)
from segelphysik.gui.navigationswidgets import (
    NavigationsWidgetFenster,
    SVGInstrumentWidget,
)
from segelphysik.grafik_bruecke import GrafikBruecke


def _roll_phi(winkel):
    matrix = np.array((
        (1.0, 0.0, 0.0),
        (0.0, math.cos(winkel), math.sin(winkel)),
        (0.0, -math.sin(winkel), math.cos(winkel)),
    ))
    return quaternion_aus_matrix(matrix)


def _stampfen_theta(winkel):
    matrix = np.array((
        (math.cos(winkel), 0.0, -math.sin(winkel)),
        (0.0, 1.0, 0.0),
        (math.sin(winkel), 0.0, math.cos(winkel)),
    ))
    return quaternion_aus_matrix(matrix)


def _gieren_heading(winkel):
    matrix = np.array((
        (math.cos(winkel), math.sin(winkel), 0.0),
        (-math.sin(winkel), math.cos(winkel), 0.0),
        (0.0, 0.0, 1.0),
    ))
    return quaternion_aus_matrix(matrix)


def test_posewinkel_nord_ost_sued_west_und_vorzeichen():
    headings = (0.0, 90.0, 180.0, 270.0)
    for richtung, grad in zip(headings, (0, 90, 180, 270)):
        werte = navigationswerte_ableiten(
            _gieren_heading(math.radians(richtung)))
        assert werte.heading_grad == pytest.approx(grad)
        assert werte.kraengung_grad == pytest.approx(0.0)
        assert werte.stampfen_grad == pytest.approx(0.0)

    assert navigationswerte_ableiten(_roll_phi(math.radians(25))
                                     ).kraengung_grad == pytest.approx(25)
    assert navigationswerte_ableiten(_stampfen_theta(math.radians(-17))
                                     ).stampfen_grad == pytest.approx(-17)


def test_singularitaet_und_ungueltige_quaternionen_bleiben_nicht_verfuegbar():
    senkrecht = navigationswerte_ableiten(_stampfen_theta(math.pi / 2))
    assert senkrecht.stampfen_grad == pytest.approx(90.0)
    assert senkrecht.heading_grad is None
    assert senkrecht.kraengung_grad is None

    ungueltig = navigationswerte_ableiten((0.0, 0.0, 0.0, 0.0))
    assert ungueltig.heading_grad is None
    assert ungueltig.kraengung_grad is None
    assert ungueltig.stampfen_grad is None
    assert ungueltig.kamera_azimut_grad is None


def test_kameraprojektionen_folgen_heading_offset_und_elevation():
    elevation = math.radians(32.0)
    offset = math.radians(47.0)
    ergebnis = []
    for heading in (0.0, 90.0, 225.0):
        werte = navigationswerte_ableiten(
            _gieren_heading(math.radians(heading)),
            offset, elevation)
        ergebnis.append(werte)
        assert werte.kamera_azimut_grad == pytest.approx(
            (heading + 47.0) % 360.0)
        relativ = math.radians(47.0)
        assert werte.kamera_stampfen_grad == pytest.approx(
            math.degrees(math.atan2(
                math.sin(elevation),
                math.cos(elevation) * math.cos(relativ))))
        assert werte.kamera_kraengung_grad == pytest.approx(
            math.degrees(math.atan2(
                math.sin(elevation),
                math.cos(elevation) * math.sin(relativ))))
    assert all(
        ((wert.kamera_azimut_grad - wert.heading_grad) % 360.0)
        == pytest.approx(47.0)
        for wert in ergebnis)


def test_ungueltige_kameraaussicht_beeinflusst_keine_posewinkel():
    werte = navigationswerte_ableiten(
        _roll_phi(math.radians(12)),
        kamera_offset_rad=0.5,
        kamera_elevation_rad=math.pi / 2)
    assert werte.kraengung_grad == pytest.approx(12.0)
    assert werte.heading_grad == pytest.approx(0.0)
    assert werte.kamera_azimut_grad is None
    assert werte.kamera_kraengung_grad is None
    assert werte.kamera_stampfen_grad is None


@pytest.mark.parametrize(
    ("heading", "expected"),
    ((0, "N"), (11.249, "N"), (11.25, "NNO"), (33.75, "NO"),
     (74, "ONO"), (359.9, "N"), (-0.1, "N")))
def test_16_punkt_richtung_an_sektorgrenzen(heading, expected):
    assert richtung_16(heading) == expected


def test_svg_laden_ist_cwd_unabhaengig_und_quellbytes_bleiben_unveraendert(
        tmp_path, monkeypatch, qapp):
    root = Path(__file__).resolve().parents[1]
    assets = root / "doc" / "WegZuV1.0" / "Revisionslog" / "zuV0.7" / "Widgets"
    paths = tuple(assets / name for name in (
        "Widget_Kompass.svg", "Widget_Krängung.svg", "Widget_Stampfen.svg"))
    original = tuple(path.read_bytes() for path in paths)
    monkeypatch.chdir(tmp_path)
    widgets = tuple(
        SVGInstrumentWidget(name)
        for name in ("kompass", "kraengung", "stampfen"))
    values = navigationswerte_ableiten(
        _roll_phi(math.radians(20)),
        math.radians(35),
        math.radians(30),
        segelwinkel_rad=math.radians(1))
    for widget in widgets:
        widget.aktualisieren(values, {})
        assert widget._renderer.isValid()
    assert tuple(path.read_bytes() for path in paths) == original


def test_svg_statusprioritaet_spiegelung_und_sichtbarkeit(qapp):
    widget = SVGInstrumentWidget("kraengung")
    fehler = navigationswerte_ableiten((0.0, 0.0, 0.0, 0.0))
    widget.aktualisieren(fehler, {
        "analog_sichtbar": False,
        "numerisch_sichtbar": False,
    })
    xml = ET.fromstring(widget._rendered_bytes)
    elemente = {element.attrib.get("id"): element for element in xml.iter()}
    assert elemente["runtime_error_disk"].attrib["style"] == ""
    assert elemente["roll_value"].text == "FEHLER"
    assert elemente["roll_pose"].attrib["style"].endswith("display: none")
    assert elemente["roll_ring_outer"].attrib["style"] == ""

    gekentert = navigationswerte_ableiten(_roll_phi(math.radians(91)))
    widget.aktualisieren(gekentert, {"analog_sichtbar": True})
    xml = ET.fromstring(widget._rendered_bytes)
    elemente = {element.attrib.get("id"): element for element in xml.iter()}
    assert elemente["runtime_error_disk"].attrib["style"].endswith(
        "display: none")
    assert elemente["runtime_danger_ring"].attrib["style"] == ""
    assert "rotate(-91" in elemente["roll_pose"].attrib["transform"]
    assert elemente["roll_sail_side"].attrib["transform"] == ""

    widget.aktualisieren(
        navigationswerte_ableiten(
            _roll_phi(math.radians(20)), segelwinkel_rad=0.1), {})
    xml = ET.fromstring(widget._rendered_bytes)
    sail = next(e for e in xml.iter()
                if e.attrib.get("id") == "roll_sail_side")
    assert sail.attrib["transform"] == "translate(324 0) scale(-1 1)"


def test_kompass_zeigt_gerundetes_wraparound_heading_und_fehlermeldung(qapp):
    widget = SVGInstrumentWidget("kompass")
    widget.aktualisieren(
        navigationswerte_ableiten(_gieren_heading(math.radians(359.8))),
        {})
    xml = ET.fromstring(widget._rendered_bytes)
    elemente = {element.attrib.get("id"): element for element in xml.iter()}
    assert elemente["heading_value"].text == "000°"
    assert elemente["heading_direction"].text == "N"

    widget.aktualisieren(
        navigationswerte_ableiten((0.0, 0.0, 0.0, 0.0)),
        {"numerisch_sichtbar": False})
    xml = ET.fromstring(widget._rendered_bytes)
    elemente = {element.attrib.get("id"): element for element in xml.iter()}
    assert elemente["heading_value"].text == "FEHLER"
    assert elemente["heading_value"].attrib["style"] == ""
    assert elemente["heading_pointer"].attrib["style"].endswith(
        "display: none")


def test_fenster_zeigt_drei_widgets_stapelbar_und_settings_unabhaengig(qapp):
    window = NavigationsWidgetFenster()
    window.show()
    qapp.processEvents()
    assert window.isWindow()
    assert tuple(widget.typ for widget in window.widgets) == (
        "kompass", "kraengung", "stampfen")
    for widget in window.widgets:
        oben = widget.mapTo(window, widget.rect().topLeft()).y()
        assert widget.isVisible()
        assert oben >= 0
        assert oben + widget.height() <= window.height()
    values = navigationswerte_ableiten(_gieren_heading(0.0))
    window.aktualisieren(values, {})
    window.sichtbarkeit_setzen({"titel_sichtbar": False})
    assert all(
        "display: none" in widget._rendered_bytes.decode("utf-8")
        for widget in window.widgets)
    window.close()


def test_sichtbarkeitseinstellungen_werden_unabhaengig_angewendet(qapp):
    widget = SVGInstrumentWidget("kompass")
    values = navigationswerte_ableiten(
        _gieren_heading(math.radians(74)),
        math.radians(45),
        math.radians(30))
    for option in (
            "titel_sichtbar", "titel_beschreibung_sichtbar",
            "analog_sichtbar", "numerisch_sichtbar"):
        options = {option: False}
        widget.aktualisieren(values, options)
        xml = ET.fromstring(widget._rendered_bytes)
        elements = {e.attrib.get("id"): e for e in xml.iter()}
        for current, ids in {
                "titel_sichtbar": ("card_title",),
                "titel_beschreibung_sichtbar": ("card_description",),
                "analog_sichtbar": (
                    "dial_outer_ring", "heading_pointer", "camera_symbol"),
                "numerisch_sichtbar": (
                    "heading_value", "heading_direction", "heading_label"),
        }.items():
            for element_id in ids:
                hidden = "display: none" in elements[element_id].attrib.get(
                    "style", "")
                assert hidden is (current == option)


def test_navigationskamera_haelt_offset_und_elevation_beim_gieren():
    class Camera:
        def __init__(self):
            self.position = (0.0, 2.0, 2.0)
            self.focal_point = (0.0, 0.0, 0.0)
            self.up = (0.0, 0.0, 1.0)

        def AddObserver(self, _event, _callback):
            return 1

    camera = Camera()
    bridge = GrafikBruecke()
    bridge._plotter = SimpleNamespace(camera=camera)
    offset, elevation = bridge.navigationskamera_aktualisieren(
        "boot", (0.0, 0.0, 0.0), 0.0)
    assert math.degrees(offset) == pytest.approx(-90.0)
    assert math.degrees(elevation) == pytest.approx(45.0)

    bridge.navigationskamera_aktualisieren(
        "boot", (5.0, 1.0, 3.0), math.radians(45.0))
    position = np.asarray(camera.position)
    target = np.asarray(camera.focal_point)
    relative = position - target
    assert np.linalg.norm(relative) == pytest.approx(math.sqrt(8.0))
    azimut = math.degrees(math.atan2(-relative[1], relative[0])) % 360.0
    assert azimut == pytest.approx(315.0)
    assert camera.focal_point == pytest.approx((5.0, 1.0, 3.0))

    camera.position = (5.0, -math.sqrt(2.0), 3.0)
    camera.focal_point = (5.0, 1.0, 3.0)
    bridge._navigationskamera_geaendert(camera, "ModifiedEvent")
    offset, elevation, _distance = bridge._navigationskamera
    assert math.degrees(offset) == pytest.approx(45.0)
    assert math.degrees(elevation) == pytest.approx(0.0)


def test_navigationskamera_hält_senkrechte_ansicht_und_markiert_sie_ungueltig():
    class Camera:
        position = (0.0, 0.0, 2.0)
        focal_point = (0.0, 0.0, 0.0)
        up = (0.0, 1.0, 0.0)

        def AddObserver(self, _event, _callback):
            return 1

    camera = Camera()
    bridge = GrafikBruecke()
    bridge._plotter = SimpleNamespace(camera=camera)
    offset, elevation = bridge.navigationskamera_aktualisieren(
        "boot", (1.0, 2.0, 3.0), 0.0)
    assert offset is None
    assert elevation == pytest.approx(math.pi / 2)
    assert camera.position == pytest.approx((1.0, 2.0, 5.0))
    assert navigationswerte_ableiten(
        quaternion_aus_matrix(np.eye(3)), offset, elevation
    ).kamera_azimut_grad is None


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])
