"""Qt-Tests fuer sichtbare Baumzustaende und die C-8-Bedienbarkeit."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QHeaderView, QStyleOptionViewItem
from PySide6.QtWidgets import QApplication

from segelphysik.gui.baum import sichtbarkeit_setzen, welt_aus_json
from segelphysik.gui.hauptfenster import HauptFenster
from segelphysik.gui.baum_widget import BaumWidget, TeilaktivDelegate


_JSON = {
    "summenkoerper": {
        "yacht1": {
            "teile": [
                {"name": "rumpf", "material": "GfK"},
                {"name": "kielsystem", "teile": [
                    {"name": "kiel", "material": "Stahl"},
                    {"name": "bulb", "material": "Blei"},
                ]},
            ],
        },
        "yacht2": {
            "teile": [{"name": "rumpf2", "material": "GfK"}],
        },
    },
}


def _qt_app():
    return QApplication.instance() or QApplication([])


def _item(widget, text):
    treffer = []
    stack = [widget.topLevelItem(i)
             for i in range(widget.topLevelItemCount())]
    while stack:
        item = stack.pop()
        if item.text(0).strip() == text:
            treffer.append(item)
        stack.extend(item.child(i) for i in range(item.childCount()))
    assert treffer
    return treffer[0]


def _klick_checkbox(widget, item):
    rect = widget.visualRect(widget.indexFromItem(item, 1))
    QTest.mouseClick(
        widget.viewport(), Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        rect.topLeft() + QPoint(8, rect.height() // 2))
    QTest.qWait(10)
    QApplication.processEvents()


def _klick_pfeil(widget, item):
    rect = widget.visualRect(widget.indexFromItem(item, 0))
    position = QPoint(rect.left() - widget.indentation() // 2,
                      rect.center().y())
    QTest.mouseClick(widget.viewport(), Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, position)
    QApplication.processEvents()


def test_start_zeigt_nur_welt_und_hauptkoerper():
    _qt_app()
    welt = welt_aus_json(_JSON)
    widget = BaumWidget()
    widget.resize(340, 500)
    widget.lade(welt)

    assert _item(widget, "Welt").isExpanded()
    assert not _item(widget, "yacht1").isExpanded()
    assert not _item(widget, "yacht2").isExpanded()
    assert widget.header().sectionResizeMode(0) == QHeaderView.Stretch
    assert widget.header().sectionResizeMode(1) == QHeaderView.ResizeToContents
    widget.close()


def test_ein_ausklappen_nur_mit_pfeil_nicht_durch_text_doppelklick_oder_checkbox():
    _qt_app()
    welt = welt_aus_json(_JSON)
    sichtbarkeit_setzen(welt, "yacht1")
    widget = BaumWidget()
    widget.resize(340, 500)
    widget.lade(welt)
    widget.show()
    QApplication.processEvents()

    haupt = _item(widget, "yacht1")
    assert not haupt.isExpanded()
    text_rect = widget.visualRect(widget.indexFromItem(haupt, 0))
    QTest.mouseDClick(widget.viewport(), Qt.MouseButton.LeftButton,
                      Qt.KeyboardModifier.NoModifier, text_rect.center())
    QApplication.processEvents()
    assert not _item(widget, "yacht1").isExpanded()

    haupt = _item(widget, "yacht1")
    _klick_checkbox(widget, haupt)
    assert not _item(widget, "yacht1").isExpanded()

    _klick_pfeil(widget, _item(widget, "yacht1"))
    assert _item(widget, "yacht1").isExpanded()
    _klick_pfeil(widget, _item(widget, "yacht1"))
    assert not _item(widget, "yacht1").isExpanded()
    widget.close()


def test_hauptkoerperwechsel_klappt_baum_zu_und_sperrt_inaktive_knoten():
    _qt_app()
    welt = welt_aus_json(_JSON)
    sichtbarkeit_setzen(welt, "yacht1")
    widget = BaumWidget()
    widget.lade(welt)

    yacht1_item = _item(widget, "yacht1")
    kielsystem_item = _item(widget, "kielsystem")
    yacht1_item.setExpanded(True)
    kielsystem_item.setExpanded(True)
    assert yacht1_item.isExpanded()
    assert kielsystem_item.isExpanded()

    _item(widget, "yacht2").setCheckState(
        1, Qt.CheckState.Checked)
    QTest.qWait(10)
    QApplication.processEvents()

    assert _item(widget, "Welt").isExpanded()
    assert not _item(widget, "yacht1").isExpanded()
    assert not _item(widget, "yacht2").isExpanded()
    assert welt.kinder[1].sichtbar

    yacht1_item = _item(widget, "yacht1")
    yacht1_item.setExpanded(True)
    assert not yacht1_item.isExpanded()
    kielsystem_item = _item(widget, "kielsystem")
    kielsystem_item.setExpanded(True)
    assert not kielsystem_item.isExpanded()
    _item(widget, "yacht2").setExpanded(True)
    assert _item(widget, "yacht2").isExpanded()
    widget.close()


def test_checkbox_mausklick_aendert_blatt_gruppe_und_hauptkoerper():
    _qt_app()
    welt = welt_aus_json(_JSON)
    sichtbarkeit_setzen(welt, "yacht1")
    widget = BaumWidget()
    widget.resize(340, 500)
    widget.lade(welt)
    widget.show()
    QApplication.processEvents()
    _klick_pfeil(widget, _item(widget, "yacht1"))
    _klick_pfeil(widget, _item(widget, "kielsystem"))

    _klick_checkbox(widget, _item(widget, "kiel"))
    assert not welt.kinder[0].kinder[1].kinder[0].aktiv
    assert _item(widget, "kielsystem").checkState(1) == Qt.CheckState.PartiallyChecked
    assert _item(widget, "yacht1").isExpanded()

    _klick_checkbox(widget, _item(widget, "kielsystem"))
    assert welt.kinder[0].kinder[1].kinder[0].aktiv
    assert welt.kinder[0].kinder[1].kinder[1].aktiv
    _klick_checkbox(widget, _item(widget, "kielsystem"))
    assert not welt.kinder[0].kinder[1].kinder[0].aktiv
    assert not welt.kinder[0].kinder[1].kinder[1].aktiv

    _klick_checkbox(widget, _item(widget, "yacht2"))
    assert welt.kinder[1].sichtbar
    assert _item(widget, "rumpf2").checkState(1) == Qt.CheckState.Checked
    widget.close()


def test_widget_zeigt_teilaktivitaet_und_gruppen_checkbox():
    _qt_app()
    welt = welt_aus_json(_JSON)
    sichtbarkeit_setzen(welt, "yacht1")
    widget = BaumWidget()
    widget.lade(welt)

    kiel = _item(widget, "kiel")
    kiel.setCheckState(1, Qt.CheckState.Unchecked)
    QApplication.processEvents()

    assert _item(widget, "kielsystem").checkState(1) == Qt.CheckState.PartiallyChecked
    assert _item(widget, "yacht1").checkState(1) == Qt.CheckState.PartiallyChecked

    gruppe = _item(widget, "kielsystem")
    gruppe.setCheckState(1, Qt.CheckState.Unchecked)
    QApplication.processEvents()
    assert _item(widget, "kielsystem").checkState(1) == Qt.CheckState.Unchecked
    assert not welt.kinder[0].kinder[1].kinder[0].aktiv
    widget.close()


def test_teilaktiv_checkbox_wird_grau_gezeichnet():
    _qt_app()
    welt = welt_aus_json(_JSON)
    sichtbarkeit_setzen(welt, "yacht1")
    from segelphysik.gui.baum import blatt_setzen
    blatt_setzen(welt, "kiel", False)
    widget = BaumWidget()
    widget.lade(welt)

    delegate = widget.itemDelegateForColumn(1)
    assert isinstance(delegate, TeilaktivDelegate)
    index = widget.indexFromItem(_item(widget, "kielsystem"), 1)
    bild = QImage(32, 24, QImage.Format.Format_ARGB32)
    bild.fill(Qt.GlobalColor.transparent)
    painter = QPainter(bild)
    option = QStyleOptionViewItem()
    option.rect = bild.rect()
    delegate.paint(painter, option, index)
    painter.end()

    grautoene = [
        bild.pixelColor(x, y).red()
        for y in range(bild.height())
        for x in range(bild.width())
        if bild.pixelColor(x, y).red()
        == bild.pixelColor(x, y).green()
        == bild.pixelColor(x, y).blue()
    ]
    assert any(grau < 150 for grau in grautoene)
    widget.close()


def test_c8_sperrt_inaktive_unterobjekte_und_laesst_hauptobjekte_waehlen():
    _qt_app()
    welt = welt_aus_json(_JSON)
    sichtbarkeit_setzen(welt, "yacht1")
    widget = BaumWidget()
    widget.lade(welt)
    widget.nur_aktives_bedienbar_setzen(True)

    assert not (_item(widget, "rumpf2").flags() & Qt.ItemFlag.ItemIsEnabled)
    yacht2 = _item(widget, "yacht2")
    assert yacht2.flags() & Qt.ItemFlag.ItemIsEnabled

    yacht2.setCheckState(1, Qt.CheckState.Checked)
    QApplication.processEvents()
    assert _item(widget, "rumpf2").flags() & Qt.ItemFlag.ItemIsEnabled
    widget.close()


def test_c8_einstellung_im_hauptfenster_ist_standardmaessig_aus():
    _qt_app()
    fenster = HauptFenster()
    fenster.baum_setzen(welt_aus_json(_JSON))
    sichtbarkeit_setzen(fenster.baum._welt, "yacht1")
    fenster.baum.lade(fenster.baum._welt)

    assert not fenster._act_nur_aktives.isChecked()
    fenster._act_nur_aktives.setChecked(True)
    assert not (_item(fenster.baum, "rumpf2").flags()
                & Qt.ItemFlag.ItemIsEnabled)
    fenster._act_nur_aktives.setChecked(False)
    assert _item(fenster.baum, "rumpf2").flags() & Qt.ItemFlag.ItemIsEnabled
    fenster.close()


def test_eigenschaften_einfacher_formen_werden_angezeigt():
    _qt_app()
    welt = welt_aus_json({
        "summenkoerper": {
            "quader": {
                "form": {"typ": "box", "dx_m": 1.0, "dy_m": 2.0, "dz_m": 3.0},
                "dichte_kg_pro_m3": 900,
                "farbe": "#00b140",
            },
        },
    })
    widget = BaumWidget()
    widget.lade(welt)

    assert _item(widget, "Form: Quader 1x2x3 m")
    assert _item(widget, "Dichte: 900 kg/m3")
    assert _item(widget, "Farbe: #00b140")
    widget.close()
