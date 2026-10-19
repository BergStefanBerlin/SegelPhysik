"""SVG-basierte Laufzeitdarstellung der drei Navigationswidgets."""
from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree as ET

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from ..core.navigationsanzeigen import Navigationswerte, richtung_16


_SVG_NS = "http://www.w3.org/2000/svg"
_WIDGET_ASSETS = {
    "kompass": ("Widget_Kompass.svg", "compass"),
    "kraengung": ("Widget_Krängung.svg", "roll"),
    "stampfen": ("Widget_Stampfen.svg", "pitch"),
}
_SICHTBARKEITS_IDS = {
    "kompass": {
        "titel_sichtbar": ("card_title",),
        "titel_beschreibung_sichtbar": ("card_description",),
        "analog_sichtbar": (
            "dial_outer_ring", "dial_inner_ring", "compass_ticks",
            "compass_references", "heading_pointer", "camera_symbol",
            "cardinal_labels",
        ),
        "numerisch_sichtbar": (
            "heading_value", "heading_direction", "heading_label",
        ),
    },
    "kraengung": {
        "titel_sichtbar": ("roll_card_title",),
        "titel_beschreibung_sichtbar": ("roll_card_description",),
        "analog_sichtbar": (
            "roll_ring_outer", "roll_ring_inner",
            "roll_reference_horizontal", "roll_reference_vertical",
            "roll_scale_ticks", "roll_scale_labels", "roll_pose",
            "roll_camera", "roll_pivot",
        ),
        "numerisch_sichtbar": ("roll_value", "roll_label"),
    },
    "stampfen": {
        "titel_sichtbar": ("pitch_card_title",),
        "titel_beschreibung_sichtbar": ("pitch_card_description",),
        "analog_sichtbar": (
            "pitch_ring_outer", "pitch_ring_inner",
            "pitch_reference_horizontal", "pitch_reference_vertical",
            "pitch_scale_ticks", "pitch_scale_labels", "pitch_pose",
            "pitch_camera", "pitch_pivot",
        ),
        "numerisch_sichtbar": ("pitch_value", "pitch_label"),
    },
}
_PFLICHT_IDS = {
    "kompass": (
        "compass_face", "card_title", "card_description",
        "heading_pointer", "camera_symbol", "heading_value",
        "heading_direction", "heading_label", "dial_status",
        "dial_outer_ring", "dial_inner_ring",
    ),
    "kraengung": (
        "roll_face", "roll_card_title", "roll_card_description",
        "roll_pose", "roll_camera", "roll_value", "roll_label",
        "roll_ring_outer", "roll_ring_inner",
    ),
    "stampfen": (
        "pitch_face", "pitch_card_title", "pitch_card_description",
        "pitch_pose", "pitch_camera", "pitch_value", "pitch_label",
        "pitch_ring_outer", "pitch_ring_inner",
    ),
}
_GESCHWINDIGKEIT_SVG = b"""\
<svg xmlns="http://www.w3.org/2000/svg" width="580" height="190"
     viewBox="22 0 580 190">
  <defs>
    <linearGradient id="card_gradient" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#193448"/>
      <stop offset="1" stop-color="#11283a"/>
    </linearGradient>
    <style>
      text { font-family: "Segoe UI", Arial, sans-serif; fill: #f4f8fb; }
      .card { fill: url(#card_gradient); stroke: #315066; stroke-width: 1.5; }
      .card-title { font-size: 19px; font-weight: 700; letter-spacing: 1.2px; fill: #b8cad5; }
      .speed-value { font-size: 34px; font-weight: 700; }
      .speed-unit { font-size: 14px; fill: #8da9bb; }
      .divider { stroke: #315066; stroke-width: 1.5; }
    </style>
  </defs>
  <g id="speed_widget">
    <rect class="card" x="42" y="10" width="540" height="166" rx="24"/>
    <text class="card-title" x="70" y="46">GESCHWINDIGKEIT</text>
    <path class="divider" d="M222 64 V154 M402 64 V154"/>
    <text id="speed_ms" class="speed-value" x="132" y="112"
          text-anchor="middle">&#8212;</text>
    <text class="speed-unit" x="132" y="142" text-anchor="middle">m/s</text>
    <text id="speed_kmh" class="speed-value" x="312" y="112"
          text-anchor="middle">&#8212;</text>
    <text class="speed-unit" x="312" y="142" text-anchor="middle">km/h</text>
    <text id="speed_kn" class="speed-value" x="492" y="112"
          text-anchor="middle">&#8212;</text>
    <text class="speed-unit" x="492" y="142" text-anchor="middle">kn</text>
  </g>
</svg>
"""


def _svg_tag(name):
    return "{%s}%s" % (_SVG_NS, name)


def _style_setzen(element, name, value):
    eintraege = {}
    for teil in element.attrib.get("style", "").split(";"):
        if ":" in teil:
            schluessel, eintrag = teil.split(":", 1)
            eintraege[schluessel.strip()] = eintrag.strip()
    if value is None:
        eintraege.pop(name, None)
    else:
        eintraege[name] = value
    element.set("style", "; ".join(
        "%s: %s" % eintrag for eintrag in eintraege.items()))


def _sichtbar_setzen(element, sichtbar):
    _style_setzen(element, "display", None if sichtbar else "none")


def _rotation_setzen(element, grad):
    for name in ("transform", "transform-origin", "transform-box"):
        _style_setzen(element, name, None)
    element.set("transform", "rotate(%.12g 312 405)" % grad)


def _fehlerkreis():
    return ET.Element(_svg_tag("circle"), {
        "id": "runtime_error_disk",
        "cx": "312",
        "cy": "405",
        "r": "165.5",
        "fill": "#ff0000",
        "pointer-events": "none",
    })


def _gefahrenring():
    return ET.Element(_svg_tag("path"), {
        "id": "runtime_danger_ring",
        "d": (
            "M312 195 A210 210 0 1 1 312 615 A210 210 0 1 1 312 195 Z "
            "M312 238.5 A166.5 166.5 0 1 0 312 571.5 "
            "A166.5 166.5 0 1 0 312 238.5 Z"
        ),
        "fill": "#ff0000",
        "fill-rule": "evenodd",
        "pointer-events": "none",
    })


class SVGInstrumentWidget(QWidget):
    def __init__(self, typ, parent=None):
        super().__init__(parent)
        if typ not in _WIDGET_ASSETS:
            raise ValueError("Unbekanntes Widget: %s" % typ)
        self.typ = typ
        self._prefix = _WIDGET_ASSETS[typ][1]
        widget_dir = (
            Path(__file__).resolve().parents[2]
            / "doc" / "WegZuV1.0" / "Revisionslog" / "zuV0.7" / "Widgets"
        )
        self._source_path = widget_dir / _WIDGET_ASSETS[typ][0]
        try:
            self._source_bytes = self._source_path.read_bytes()
            self._xml = ET.fromstring(self._source_bytes)
        except (OSError, ET.ParseError) as fehler:
            raise RuntimeError(
                "Widget-SVG %s kann nicht geladen werden: %s"
                % (self._source_path, fehler)) from fehler
        self._elemente = {
            element.attrib["id"]: element
            for element in self._xml.iter() if "id" in element.attrib
        }
        fehlend = set(_PFLICHT_IDS[typ]) - self._elemente.keys()
        if fehlend:
            raise RuntimeError(
                "Widget-SVG %s fehlen Pflicht-IDs: %s"
                % (self._source_path, ", ".join(sorted(fehlend))))
        self._face = self._elemente[
            {"kompass": "compass_face",
             "kraengung": "roll_face",
             "stampfen": "pitch_face"}[typ]]
        self._error_disk = _fehlerkreis()
        self._danger_ring = _gefahrenring()
        self._overlay_einfuegen()
        self._renderer = QSvgRenderer()
        self._rendered_bytes = b""
        self.setMinimumSize(220, 220)
        self._render(None, {})

    def sizeHint(self):
        return QSize(380, 380)

    def _overlay_einfuegen(self):
        kinder = list(self._face)
        ring_aussen = self._elemente[
            {"kompass": "dial_outer_ring",
             "kraengung": "roll_ring_outer",
             "stampfen": "pitch_ring_outer"}[self.typ]]
        index = kinder.index(ring_aussen) + 1
        self._face.insert(index, self._danger_ring)
        self._face.insert(index + 1, self._error_disk)
        if self.typ == "kompass":
            self._elemente["dial_status"].set("fill", "#ff0000")

    def _visibility_apply(self, optionen, fehler, gefahr):
        for option, ids in _SICHTBARKEITS_IDS[self.typ].items():
            sichtbar = bool(optionen.get(option, True))
            if option == "numerisch_sichtbar" and fehler:
                sichtbar = True
            for element_id in ids:
                element = self._elemente.get(element_id)
                if element is not None:
                    _sichtbar_setzen(element, sichtbar)
        _sichtbar_setzen(self._error_disk, fehler)
        if self.typ == "kompass":
            self._elemente["dial_status"].set(
                "fill-opacity", "1" if gefahr else "0")
            _sichtbar_setzen(self._danger_ring, False)
        else:
            _sichtbar_setzen(self._danger_ring, gefahr)
        if not optionen.get("analog_sichtbar", True) and (fehler or gefahr):
            for element_id in (
                    {"kompass": ("dial_outer_ring", "dial_inner_ring"),
                     "kraengung": ("roll_ring_outer", "roll_ring_inner"),
                     "stampfen": ("pitch_ring_outer", "pitch_ring_inner")}
                    [self.typ]):
                _sichtbar_setzen(self._elemente[element_id], True)

    def _render(self, werte, optionen):
        heading = getattr(werte, "heading_grad", None)
        roll = getattr(werte, "kraengung_grad", None)
        pitch = getattr(werte, "stampfen_grad", None)
        error_value = {
            "kompass": heading,
            "kraengung": roll,
            "stampfen": pitch,
        }[self.typ]
        fehler = error_value is None
        gefahr = (not fehler and self.typ != "kompass"
                  and abs(error_value) > 90.0)
        if self.typ == "kompass":
            camera = getattr(werte, "kamera_azimut_grad", None)
            if heading is not None:
                grad = heading % 360.0
                _rotation_setzen(
                    self._elemente["heading_pointer"], grad)
                gerundet = int(math.floor(grad + 0.5)) % 360
                self._elemente["heading_value"].text = "%03d°" % gerundet
                self._elemente["heading_direction"].text = (
                    richtung_16(grad) or "")
            self._elemente["heading_value"].text = (
                "FEHLER" if fehler else self._elemente["heading_value"].text)
            if camera is not None:
                _rotation_setzen(
                    self._elemente["camera_symbol"], camera % 360.0)
        else:
            winkel = roll if self.typ == "kraengung" else pitch
            id_prefix = self._prefix
            kamera_winkel = (
                getattr(werte, "kamera_kraengung_grad", None)
                if self.typ == "kraengung"
                else getattr(werte, "kamera_stampfen_grad", None))
            _rotation_setzen(
                self._elemente[id_prefix + "_pose"],
                -winkel if winkel is not None else 0.0)
            self._elemente[id_prefix + "_value"].text = (
                self._winkel_text(winkel) if winkel is not None else "FEHLER")
            if kamera_winkel is not None:
                _rotation_setzen(
                    self._elemente[id_prefix + "_camera"],
                    90.0 - kamera_winkel)
            if self.typ == "kraengung":
                sail = getattr(werte, "segelwinkel_rad", None)
                sail_element = self._elemente["roll_sail_side"]
                sail_element.set(
                    "transform",
                    "translate(324 0) scale(-1 1)"
                    if sail is not None and sail > 0.0 else "")

        self._visibility_apply(optionen, fehler, gefahr)
        analog = bool(optionen.get("analog_sichtbar", True))
        if self.typ == "kompass":
            _sichtbar_setzen(
                self._elemente["heading_pointer"],
                analog and heading is not None)
            _sichtbar_setzen(
                self._elemente["camera_symbol"],
                analog and camera is not None)
        else:
            _sichtbar_setzen(
                self._elemente[self._prefix + "_pose"],
                analog and winkel is not None)
            _sichtbar_setzen(
                self._elemente[self._prefix + "_camera"],
                analog and kamera_winkel is not None)
        self._rendered_bytes = ET.tostring(
            self._xml, encoding="utf-8", xml_declaration=True)
        if not self._renderer.load(QByteArray(self._rendered_bytes)):
            raise RuntimeError(
                "Laufzeit-SVG konnte nicht gerendert werden: %s"
                % self._source_path)
        self.update()

    @staticmethod
    def _winkel_text(winkel):
        gerundet = round(winkel)
        vorzeichen = "+" if gerundet > 0 else ""
        text = "%s%d°" % (vorzeichen, gerundet)
        return text.replace("-", "−")

    def aktualisieren(self, werte, optionen):
        if not isinstance(werte, Navigationswerte):
            raise TypeError("Navigationswerte erwartet")
        self._render(werte, optionen)

    def paintEvent(self, ereignis):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        svg_size = self._renderer.defaultSize()
        scale = min(
            self.width() / max(svg_size.width(), 1),
            self.height() / max(svg_size.height(), 1))
        width = svg_size.width() * scale
        height = svg_size.height() * scale
        bounds = QRectF(
            (self.width() - width) / 2.0,
            (self.height() - height) / 2.0,
            width,
            height,
        )
        self._renderer.render(painter, bounds)


class GeschwindigkeitsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 90)
        self._xml = ET.fromstring(_GESCHWINDIGKEIT_SVG)
        self._elemente = {
            element.attrib["id"]: element
            for element in self._xml.iter() if "id" in element.attrib
        }
        self._renderer = QSvgRenderer()
        self._rendered_bytes = b""
        self.aktualisieren(None)

    def sizeHint(self):
        return QSize(380, 125)

    def aktualisieren(self, geschwindigkeit_m_pro_s):
        werte = ("\u2014", "\u2014", "\u2014")
        if geschwindigkeit_m_pro_s is not None:
            geschwindigkeit = float(geschwindigkeit_m_pro_s)
            if math.isfinite(geschwindigkeit) and geschwindigkeit >= 0.0:
                werte = (
                    "%.2f" % geschwindigkeit,
                    "%.2f" % (geschwindigkeit * 3.6),
                    "%.2f" % (geschwindigkeit * 1.9438444924406),
                )
            else:
                werte = ("FEHLER", "FEHLER", "FEHLER")
        for element_id, wert in zip(
                ("speed_ms", "speed_kmh", "speed_kn"), werte):
            self._elemente[element_id].text = wert
        self._rendered_bytes = ET.tostring(
            self._xml, encoding="utf-8", xml_declaration=True)
        if not self._renderer.load(QByteArray(self._rendered_bytes)):
            raise RuntimeError("Geschwindigkeitsanzeige konnte nicht "
                               "gerendert werden")
        self.update()

    def paintEvent(self, ereignis):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        svg_size = self._renderer.defaultSize()
        scale = min(
            self.width() / max(svg_size.width(), 1),
            self.height() / max(svg_size.height(), 1))
        width = svg_size.width() * scale
        height = svg_size.height() * scale
        bounds = QRectF(
            (self.width() - width) / 2.0,
            (self.height() - height) / 2.0,
            width,
            height,
        )
        self._renderer.render(painter, bounds)


class NavigationsWidgetFenster(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setWindowTitle("Navigationsanzeigen")
        self.setMinimumSize(300, 900)
        self.resize(400, 1020)
        self._werte = Navigationswerte(None, None, None, None, None, None)
        self._optionen = {}
        self._geschwindigkeit_m_pro_s = None
        inhalt = QWidget()
        layout = QVBoxLayout(inhalt)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        self.widgets = tuple(
            SVGInstrumentWidget(typ, inhalt)
            for typ in ("kompass", "kraengung", "stampfen"))
        for widget in self.widgets:
            layout.addWidget(widget, 1)
        self.geschwindigkeit_widget = GeschwindigkeitsWidget(inhalt)
        layout.addWidget(self.geschwindigkeit_widget)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(inhalt)
        fenster_layout = QVBoxLayout(self)
        fenster_layout.setContentsMargins(0, 0, 0, 0)
        fenster_layout.addWidget(scroll)

    def aktualisieren(self, werte, optionen, geschwindigkeit_m_pro_s=None):
        self._werte = werte
        self._optionen = dict(optionen)
        self._geschwindigkeit_m_pro_s = geschwindigkeit_m_pro_s
        for widget in self.widgets:
            widget.aktualisieren(self._werte, self._optionen)
        self.geschwindigkeit_widget.aktualisieren(
            self._geschwindigkeit_m_pro_s)

    def sichtbarkeit_setzen(self, optionen):
        self._optionen = dict(optionen)
        self.aktualisieren(
            self._werte, self._optionen, self._geschwindigkeit_m_pro_s)


__all__ = [
    "GeschwindigkeitsWidget", "NavigationsWidgetFenster",
    "SVGInstrumentWidget",
]
