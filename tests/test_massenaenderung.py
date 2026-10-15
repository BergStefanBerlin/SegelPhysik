import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.gui.baum import finde, sichtbarkeit_setzen, welt_aus_konfig
from segelphysik.gui.hauptfenster import HauptFenster


class _Bruecke:
    def __getattr__(self, _name):
        return lambda *args, **kwargs: True


def _fenster(monkeypatch, statisch):
    QApplication.instance() or QApplication([])
    welt = welt_aus_konfig(lade_konfig("konfigurationen"))
    sichtbarkeit_setzen(welt, "kugel")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    monkeypatch.setattr(
        "segelphysik.core.fabriken.baue_summenkoerper",
        lambda *_a, **_k: (object(), None))
    monkeypatch.setattr(
        fenster, "_geometrie_konflikte_bereinigen", lambda *_a: True)
    aufrufe = []
    fenster._statische_simulation_ausfuehren = lambda: aufrufe.append("s")
    fenster._echtzeit_starten = lambda *a, **k: aufrufe.append("e")
    fenster.bruecke_setzen(_Bruecke())
    fenster._btn_statisch.blockSignals(True)
    fenster._btn_statisch.setChecked(statisch)
    fenster._btn_echtzeit.setChecked(not statisch)
    fenster._btn_statisch.blockSignals(False)
    aufrufe.clear()
    return fenster, welt, aufrufe


def test_dichteaenderung_rechnet_statische_lage_neu(monkeypatch):
    fenster, welt, aufrufe = _fenster(monkeypatch, statisch=True)
    kugel = finde(welt, "kugel")
    fenster.baum._eigenschaft_setzen(kugel, "Dichte", 1200.0)
    assert kugel.eintrag["dichte_kg_pro_m3"] == 1200.0
    assert aufrufe == ["s"]
    fenster.close()


def test_dichteaenderung_im_echtzeitmodus_startet_neu(monkeypatch):
    fenster, welt, aufrufe = _fenster(monkeypatch, statisch=False)
    fenster.baum._eigenschaft_setzen(finde(welt, "kugel"), "Dichte", 1200.0)
    assert aufrufe == ["e"]
    fenster.close()
