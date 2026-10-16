import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.gui.baum import (
    aktive_blaetter, blatt_setzen, finde, sichtbarkeit_setzen,
    summenkoerper, welt_aus_konfig,
)
from segelphysik.gui.baum_widget import BaumWidget


def _yachtbaum(konfig):
    welt = welt_aus_konfig(konfig)
    return welt, finde(welt, "yacht1")


def _blaetter(koerper):
    if not koerper.teile:
        return [koerper]
    return [
        blatt
        for kind, _pose in koerper.teile
        for blatt in _blaetter(kind)
    ]


def test_repo_baum_verwendet_manifest_ids_und_haelt_rolle_separat():
    konfig = lade_konfig()
    welt, yacht = _yachtbaum(konfig)

    assert yacht.id == "root"
    assert yacht.name == "yacht1"
    assert yacht.label == "Yacht 1"
    assert finde(welt, "rigg").rolle_default == "stehendes_gut"
    assert ("Rolle (Standard)", "stehendes_gut") not in (
        finde(welt, "rigg").eigenschaften)
    assert finde(welt, "bulb").rolle == "kiel"
    assert finde(welt, "bulb").verdrangend is True

    sichtbarkeit_setzen(welt, "yacht1")
    bulb = finde(welt, "bulb")
    blatt_setzen(welt, bulb, False)

    assert not bulb.aktiv
    assert bulb.rolle == "kiel"


def test_paketfabrik_nutzt_aktive_manifest_ids():
    konfig = lade_konfig()
    welt, yacht = _yachtbaum(konfig)
    sichtbarkeit_setzen(welt, "yacht1")
    bulb = finde(welt, "bulb")

    koerper, _ = baue_summenkoerper(
        konfig, "yacht1", aktive_blaetter=[bulb])

    assert [blatt._name for blatt in _blaetter(koerper)] == ["bulb"]


def test_legacy_schalter_mappt_manifestteil_ids_auf_altblaetter():
    konfig = lade_konfig()
    konfig.paketfabrik_aktiv = False
    welt, yacht = _yachtbaum(konfig)
    sichtbarkeit_setzen(welt, "yacht1")
    for blatt in yacht.blaetter():
        blatt.aktiv = False
    rumpf = finde(welt, "rumpf")
    mastteil = finde(welt, "mast")
    rumpf.aktiv = True
    mastteil.aktiv = True

    koerper, _ = baue_summenkoerper(
        konfig, yacht.name, aktive_blaetter=[rumpf, mastteil])

    assert [blatt._name for blatt in _blaetter(koerper)] == [
        "rumpf", "mast"]


def test_paketfabrik_uebernimmt_sitzungsedit_aus_gui():
    QApplication.instance() or QApplication([])
    konfig = lade_konfig()
    welt, yacht = _yachtbaum(konfig)
    sichtbarkeit_setzen(welt, "yacht1")
    widget = BaumWidget()
    widget.lade(welt)
    widget._eigenschaft_setzen(finde(welt, "bulb"), "Material", "Stahl")
    koerper, _ = baue_summenkoerper(
        konfig, yacht.name, aktive_blaetter=["bulb"])
    widget.close()

    bulb = _blaetter(koerper)[0]
    assert bulb.massendefinition["material"] == "Stahl"
    assert bulb.massendefinition["dichte_kg_pro_m3"] == konfig.dichte_von(
        "Stahl")


def test_paketkoerper_ohne_manifestkinder_ignoriert_leere_auswahl():
    konfig = lade_konfig()
    welt = welt_aus_konfig(konfig)
    kugel = next(k for k in summenkoerper(welt) if k.name == "kugel")

    koerper, _ = baue_summenkoerper(
        konfig, kugel.name, aktive_blaetter=aktive_blaetter(kugel))

    assert koerper.masse > 0
