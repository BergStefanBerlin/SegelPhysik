"""Statische Darstellung: Wasserpunkte aus, Kraftbild folgt der Fremdkraft."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PySide6.QtWidgets import QApplication

from segelphysik.gui.hauptfenster import HauptFenster

import pytest
pytestmark = [pytest.mark.gui, pytest.mark.integration]


def test_fremdkraft_aenderung_invalidiert_statt_gui_physik_doppelt_zu_rechnen():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()

    class Bruecke:
        def __init__(self):
            self.daten = []
            self.neu = 0

        def kraefte_daten_setzen(self, name, erg, masse, g, skala, fremd=None):
            self.daten.append(fremd)

        def kraefte_neu_zeichnen(self):
            self.neu += 1

    class Koerper:
        masse = 10.0
        punkte = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]

    class Physik:
        g_m_pro_s2 = 9.81

    bruecke = Bruecke()
    fenster._bruecke = bruecke
    fenster._btn_statisch.setChecked(True)
    fenster._laufzeit_koerper["k"] = Koerper()
    fenster._statische_ergebnisse["k"] = {"z": 0.0, "phi": 0.0}
    fenster._statische_arbeitsdaten["k"] = (
        lambda *a, **k: object(), Physik())
    fenster._fremd_check.setChecked(True)
    generation = fenster._statisch_generation
    assert "Statische Berechnung laeuft" in fenster._kraefte_werte.kopf.text()
    assert bruecke.neu == 0
    assert bruecke.daten == []
    fenster._fremd_check.setChecked(False)
    assert fenster._statisch_generation == generation + 1
    assert bruecke.daten == []
    fenster.close()
    app.processEvents()


def test_wasserpunkte_nur_in_der_echtzeit():
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    aufrufe = []

    class Bruecke:
        def wasserpunkte_sichtbar_setzen(self, sichtbar):
            aufrufe.append(sichtbar)

    fenster._bruecke = Bruecke()
    fenster._wasserpunkte_fuer_modus(True)
    fenster._wasserpunkte_fuer_modus(False)
    assert aufrufe == [False, True]
    fenster.close()
    app.processEvents()
