import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from segelphysik.core import formerkennung, statusanzeige
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.gui.hauptfenster import (
    _StatischeAufgabe, _StatischeAufgabeSignale)


def _lauf(name):
    QApplication.instance() or QApplication([])
    konfig = lade_konfig("konfigurationen")
    koerper, _ = baue_summenkoerper(konfig, name)
    signale = _StatischeAufgabeSignale()
    empfangen = []
    signale.abgeschlossen.connect(lambda *a: empfangen.append(a))
    _StatischeAufgabe(1, name, koerper, konfig.ordner,
                      konfig.wasser_dichte(), signale).run()
    _gen, _name, ergebnis, _arbeit, fehler = empfangen[0]
    return koerper, ergebnis, fehler


def test_kugel_ist_rotationsneutral():
    koerper, ergebnis, fehler = _lauf("kugel")
    assert fehler is None
    assert ergebnis["neutral"] is True
    form = formerkennung.klassifiziere_koerper(koerper)
    assert statusanzeige.status_aus_ergebnis(ergebnis, form=form) == (
        "rotationsneutral (Kugel)", "ok")


def test_quader_bleibt_stabil_nicht_neutral():
    koerper, ergebnis, fehler = _lauf("quader")
    assert fehler is None
    assert not ergebnis["neutral"]
