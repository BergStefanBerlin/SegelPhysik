import numpy as np
import pytest

from segelphysik.core.navigationsanzeigen import Navigationswerte
from segelphysik.core.rechenpfad import python_referenz
from segelphysik.gui.navigationswidgets import (
    GeschwindigkeitsWidget, SVGInstrumentWidget,
    _geschwindigkeitseinheiten, _svg_rahmen,
)


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("typ", ["kompass", "kraengung", "stampfen"])
def test_native_instrumentaufbereitung_behaelt_exakte_svgbytes(monkeypatch, qapp, typ):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz():
        ref = SVGInstrumentWidget(typ)
    cpp = SVGInstrumentWidget(typ)
    rng = np.random.default_rng(14026)
    pruefwerte = [None, 0., -0., 90., -90., 90.000001, -90.000001, 359.5, -1e-300]
    pruefwerte.extend(rng.uniform(-1000., 1000., size=100))
    for i, wert in enumerate(pruefwerte):
        werte = Navigationswerte(wert, wert, wert, wert, wert, wert, None if i % 2 else .3)
        optionen = {"analog_sichtbar": i % 3 != 0, "numerisch_sichtbar": i % 5 != 0}
        with python_referenz():
            ref.aktualisieren(werte, optionen)
        cpp.aktualisieren(werte, optionen)
        assert cpp._rendered_bytes == ref._rendered_bytes
    ref.close()
    cpp.close()


@pytest.mark.parametrize("typ", ["kompass", "kraengung", "stampfen"])
def test_native_svg_rahmen_behalten_pixelabbild(monkeypatch, qapp, typ):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz():
        ref = SVGInstrumentWidget(typ)
    cpp = SVGInstrumentWidget(typ)
    werte = Navigationswerte(47., 20., -15., 87., 37., 23., .2)
    for groesse in ((380, 380), (501, 301), (301, 501)):
        ref.resize(*groesse)
        cpp.resize(*groesse)
        with python_referenz():
            ref.aktualisieren(werte, {})
            bild = ref.grab().toImage()
        cpp.aktualisieren(werte, {})
        anderes = cpp.grab().toImage()
        assert anderes.size() == bild.size()
        assert anderes.constBits().tobytes() == bild.constBits().tobytes()
    ref.close()
    cpp.close()


def test_native_geschwindigkeitsanzeige_behaelt_texte_fehler_und_svg(monkeypatch, qapp):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz():
        ref = GeschwindigkeitsWidget()
    cpp = GeschwindigkeitsWidget()
    for wert in (None, 0., .01, .015, 1., 3.5, 5.025, 1000., -1., np.nan, np.inf):
        with python_referenz():
            ref.aktualisieren(wert)
        cpp.aktualisieren(wert)
        assert cpp._rendered_bytes == ref._rendered_bytes
    ref.close()
    cpp.close()


def test_native_rahmen_und_einheiten_gegen_referenz(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(15026)
    for _ in range(1000):
        masse = tuple(rng.integers(0, 10000, size=4))
        wert = float(rng.uniform(0., 1e6))
        with python_referenz():
            rahmen = _svg_rahmen(*masse)
            einheiten = _geschwindigkeitseinheiten(wert)
        assert _svg_rahmen(*masse) == rahmen
        assert _geschwindigkeitseinheiten(wert) == einheiten
