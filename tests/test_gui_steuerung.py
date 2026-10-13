import os

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
    assert all("#0078d4" in knopf.styleSheet() for knopf in zeitschieber)
    fenster._echtzeit_kraftfunktion = object()
    QTest.mouseClick(fenster._btn_vor, Qt.MouseButton.LeftButton)
    assert fenster._echtzeit_timer.isActive()
    QTest.mouseClick(fenster._btn_halt, Qt.MouseButton.LeftButton)
    assert not fenster._echtzeit_timer.isActive()
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
    fenster._kamera_auswahl.setCurrentIndex(1)
    fenster._hintergrund_auswahl.setCurrentIndex(1)
    fenster._ssao_check.click()

    assert bruecke.layer == [
        (LAYER_SCHWERPUNKT, True), (LAYER_HAUPTACHSEN, False),
        (LAYER_KRAEFTE, False), (LAYER_MOMENTE, True)]
    assert bruecke.darstellung == [
        ("kamera", "bug"), ("hintergrund", "weiss"), ("ssao", True)]
    assert bruecke.renders == 4
    fenster.close()
    app.processEvents()
