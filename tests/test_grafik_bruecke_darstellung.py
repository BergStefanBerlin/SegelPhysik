from types import SimpleNamespace

import pytest

from segelphysik.grafik_bruecke import GrafikBruecke
from segelphysik.grafik_optimierung import kamera_presets


class _Plotter:
    def __init__(self):
        self.calls = []
        self.camera_position = None

    def render(self):
        self.calls.append(("render",))

    def set_background(self, farbe, top=None):
        self.calls.append(("hintergrund", farbe, top))

    def enable_lightkit(self):
        self.calls.append(("licht_an",))

    def remove_all_lights(self):
        self.calls.append(("licht_aus",))

    def enable_ssao(self, **kwargs):
        self.calls.append(("ssao_an", kwargs))

    def disable_ssao(self):
        self.calls.append(("ssao_aus",))


class _Renderer:
    def __init__(self):
        self.calls = []

    def wasser_sichtbar_setzen(self, sichtbar):
        self.calls.append(("wasser", sichtbar))
        return True

    def wasseroptik_setzen(self, aktiviert):
        self.calls.append(("wasseroptik", aktiviert))
        return True


def _bruecke():
    bruecke = GrafikBruecke.__new__(GrafikBruecke)
    bruecke.app = SimpleNamespace(cfg=SimpleNamespace(
        basin={"lx": 10.0, "ly": 8.0}, water={"depth": 3.0}))
    bruecke._plotter = _Plotter()
    bruecke._renderer = _Renderer()
    return bruecke


def test_kamera_presets_hintergrund_und_beleuchtung():
    bruecke = _bruecke()

    assert bruecke.kamera_preset_setzen("draufsicht")
    assert bruecke._plotter.camera_position == kamera_presets(
        10.0, 8.0, 3.0)["draufsicht"]
    assert bruecke.hintergrund_setzen("verlauf")
    assert bruecke.hintergrund_setzen("dunkel")
    assert bruecke.beleuchtung_setzen(True)
    assert bruecke.beleuchtung_setzen(False)
    assert ("hintergrund", "#f2f7fc", "#9dc3e6") in bruecke._plotter.calls
    assert ("hintergrund", "#202124", None) in bruecke._plotter.calls
    assert ("licht_an",) in bruecke._plotter.calls
    assert ("licht_aus",) in bruecke._plotter.calls


def test_ssao_und_wasseroptik_sind_unabhaengig_schaltbar():
    bruecke = _bruecke()

    assert bruecke.ssao_setzen(True)
    assert bruecke.ssao_setzen(False)
    assert bruecke.wasser_sichtbar_setzen(False)
    assert bruecke.wasseroptik_setzen(True)
    assert ("ssao_an", {"radius": 0.8, "bias": 0.002}) \
        in bruecke._plotter.calls
    assert ("ssao_aus",) in bruecke._plotter.calls
    assert bruecke._renderer.calls == [
        ("wasser", False), ("wasseroptik", True)]


def test_unbekanntes_kamera_preset_wird_abgelehnt():
    with pytest.raises(ValueError, match="Unbekanntes Kamera-Preset"):
        _bruecke().kamera_preset_setzen("unbekannt")
