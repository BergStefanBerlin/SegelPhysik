import copy
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from segelphysik.core import formerkennung, statusanzeige
from segelphysik.core.fabriken import baue_form, baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.gui.hauptfenster import (
    _StatischeAufgabe, _StatischeAufgabeSignale)


def _lauf(name, dichte=None, form_ueberschreiben=None, fremdkraft=None):
    QApplication.instance() or QApplication([])
    konfig = lade_konfig("konfigurationen")
    if dichte is None and form_ueberschreiben is None:
        koerper, _ = baue_summenkoerper(konfig, name)
    else:
        eintrag = copy.deepcopy(konfig.summenkoerper[name])
        if dichte is not None:
            eintrag["dichte_kg_pro_m3"] = dichte
        if form_ueberschreiben:
            eintrag["form"].update(form_ueberschreiben)
        koerper = baue_form(konfig, eintrag)
    signale = _StatischeAufgabeSignale()
    empfangen = []
    signale.abgeschlossen.connect(lambda *a: empfangen.append(a))
    _StatischeAufgabe(1, name, koerper, konfig.ordner,
                      konfig.wasser_dichte(), signale,
                      fremdkraft=fremdkraft).run()
    _gen, _name, ergebnis, _arbeit, fehler = empfangen[0]
    return koerper, ergebnis, fehler


def test_liegende_rolle_ist_rollneutral():
    for dichte in (500, 700, 900):
        koerper, ergebnis, fehler = _lauf("rolle", dichte=dichte)
        assert fehler is None
        assert ergebnis["neutral"] is True, dichte
        form = formerkennung.klassifiziere_koerper(koerper)
        assert statusanzeige.status_aus_ergebnis(ergebnis, form=form) == (
            "rollneutral (Zylinder)", "ok")


def test_stehender_zylinder_ist_nicht_neutral():
    # flach (H klein gegen R): stabil schwimmend, hat echtes GM
    koerper, ergebnis, fehler = _lauf(
        "rolle", dichte=500,
        form_ueberschreiben={"lage": "stehend", "H_m": 0.4})
    assert fehler is None
    assert not ergebnis["neutral"]


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


def test_statische_loesung_beruecksichtigt_fremdkraft():
    _, ohne_kraft, fehler_ohne = _lauf("kugel")
    _, mit_kraft, fehler_mit = _lauf(
        "kugel", fremdkraft=((0.0, 0.0, 500.0), (0.0, 0.0, 0.0)))

    assert fehler_ohne is None
    assert fehler_mit is None
    assert mit_kraft["z"] > ohne_kraft["z"]
