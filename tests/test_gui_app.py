"""GUI-App-Start: Baumimport und Standardobjekt aus der Konfiguration."""
import os
from types import SimpleNamespace

from segelphysik.gui import app
from segelphysik.gui.baum import finde, summenkoerper
from segelphysik.core.physik_backend import (
    BackendNichtVerfuegbar,
    OpenCLBackend,
)


def test_welt_laden_baut_baum_und_waehlt_standardobjekt(monkeypatch):
    konfig_pfad = os.path.join(
        os.path.dirname(__file__), "..", "konfigurationen", "koerper.json")
    monkeypatch.setattr(app, "_finde_koerper_json",
                        lambda: os.path.abspath(konfig_pfad))
    monkeypatch.setattr(app, "_log", lambda _nachricht: None)

    welt = app.welt_laden()

    namen = [k.name.casefold() for k in summenkoerper(welt)]
    assert namen.count("kegel") == 1
    assert namen.count("quader") == 1
    assert namen.count("pyramide") == 1
    assert finde(welt, "quader").sichtbar
    assert not finde(welt, "yacht1").sichtbar


def test_koerper_json_pfad_ist_unabhaengig_vom_arbeitsordner(
        monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    pfad = app._finde_koerper_json()

    erwartet = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "konfigurationen", "koerper.json"))
    assert pfad == erwartet


def test_welt_laden_verwendet_standardansicht_aus_der_konfiguration(
        monkeypatch, tmp_path):
    koerper_pfad = tmp_path / "koerper.json"
    koerper_pfad.write_text("{}", encoding="utf-8")
    konfig = SimpleNamespace(
        summenkoerper={
            "pyramide": {
                "form": {"typ": "pyramid", "a_m": 2.0, "H_m": 2.0},
                "dichte_kg_pro_m3": 500,
                "farbe": "#d40078",
                "farbe_unter_wasser": "#99005a",
            },
        },
        standard_ansicht="pyramide",
    )
    aufrufe = []
    monkeypatch.setattr(app, "_finde_koerper_json", lambda: str(koerper_pfad))
    monkeypatch.setattr(
        "segelphysik.core.konfig_lader.lade_konfig",
        lambda ordner: aufrufe.append(ordner) or konfig)
    monkeypatch.setattr(app, "_log", lambda _nachricht: None)

    welt = app.welt_laden()

    assert finde(welt, "pyramide").sichtbar
    assert not finde(welt, "Quader").sichtbar
    assert aufrufe == [str(tmp_path)]


def test_gpu_praesenz_wird_im_bestehenden_protokoll_ausgegeben(monkeypatch):
    protokoll = []
    monkeypatch.setattr(app, "_log", protokoll.append)
    monkeypatch.setattr(
        OpenCLBackend, "gpu_namen_ermitteln",
        classmethod(lambda _cls: ("gfx1103",)))

    app._gpu_praesenz_protokollieren()

    assert protokoll == ["OpenCL-GPU vorhanden: gfx1103"]


def test_opencl_fehlt_und_cpu_betrieb_bleibt_verfuegbar(monkeypatch):
    protokoll = []
    monkeypatch.setattr(app, "_log", protokoll.append)

    def nicht_verfuegbar(_cls):
        raise BackendNichtVerfuegbar("PyOpenCL fehlt")

    monkeypatch.setattr(
        OpenCLBackend, "gpu_namen_ermitteln",
        classmethod(nicht_verfuegbar))

    app._gpu_praesenz_protokollieren()

    assert protokoll == [
        "OpenCL-GPU nicht verfügbar; CPU bleibt einsatzbereit: PyOpenCL fehlt"]
