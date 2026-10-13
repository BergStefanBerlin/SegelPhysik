import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from segelphysik.gui.hauptfenster import HauptFenster


def test_modusknopfe_sind_gegenseitig_exklusiv():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    zeitschieber = (
        fenster._btn_rueck,
        fenster._btn_halt,
        fenster._btn_vor,
    )

    assert fenster._btn_statisch.isChecked()
    assert not fenster._btn_echtzeit.isChecked()
    assert all(not knopf.isEnabled() for knopf in zeitschieber)
    assert all(not knopf.styleSheet() for knopf in zeitschieber)

    QTest.mouseClick(fenster._btn_echtzeit, Qt.MouseButton.LeftButton)

    assert not fenster._btn_statisch.isChecked()
    assert fenster._btn_echtzeit.isChecked()
    assert all(knopf.isEnabled() for knopf in zeitschieber)
    assert all("#0078d4" in knopf.styleSheet() for knopf in zeitschieber)

    QTest.mouseClick(fenster._btn_statisch, Qt.MouseButton.LeftButton)

    assert fenster._btn_statisch.isChecked()
    assert not fenster._btn_echtzeit.isChecked()
    assert all(not knopf.isEnabled() for knopf in zeitschieber)
    assert all(not knopf.styleSheet() for knopf in zeitschieber)
    fenster.close()
    app.processEvents()
