import sys
from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core.physik_backend import (
    BackendFehler,
    BackendNichtVerfuegbar,
    OpenCLBackend,
    ausfuehren_mit_fallback,
)


def _vektor_gueltig(ergebnis):
    return (isinstance(ergebnis, np.ndarray)
            and ergebnis.ndim == 1
            and np.isfinite(ergebnis).all())


def test_cpu_pfad_bei_fehlernder_gpu_verfuegbarkeit():
    protokoll = []
    ergebnis = ausfuehren_mit_fallback(
        cpu=lambda: np.array([3.0]),
        gpu=lambda: pytest.fail("GPU darf ohne Gerät nicht aufgerufen werden"),
        gpu_verfuegbar=False,
        backend="OpenCL",
        geraet=None,
        ergebnis_gueltig=_vektor_gueltig,
        protokoll=protokoll.append,
    )

    assert np.array_equal(ergebnis, [3.0])
    assert protokoll == ["CPU-Pfad aktiv (keine GPU verfügbar)"]


def test_cpu_zuordnung_bleibt_unveraendert_trotz_gpu():
    protokoll = []
    ergebnis = ausfuehren_mit_fallback(
        cpu=lambda: np.array([4.0]),
        gpu=None,
        gpu_verfuegbar=True,
        backend="OpenCL",
        geraet="gfx1103",
        ergebnis_gueltig=_vektor_gueltig,
        protokoll=protokoll.append,
    )

    assert np.array_equal(ergebnis, [4.0])
    assert protokoll == ["CPU-Pfad aktiv (Aufgabe ist im Code der CPU zugeordnet)"]


def test_gpu_erfolg_verwendet_gpu_ergebnis_und_protokolliert_geraet():
    protokoll = []
    cpu_aufgerufen = False

    def cpu():
        nonlocal cpu_aufgerufen
        cpu_aufgerufen = True
        return np.array([-1.0])

    ergebnis = ausfuehren_mit_fallback(
        cpu=cpu,
        gpu=lambda: np.array([5.0]),
        gpu_verfuegbar=True,
        backend="OpenCL",
        geraet="gfx1103",
        ergebnis_gueltig=_vektor_gueltig,
        protokoll=protokoll.append,
    )

    assert np.array_equal(ergebnis, [5.0])
    assert not cpu_aufgerufen
    assert protokoll == ["OpenCL GPU-Pfad aktiv (gfx1103)"]


@pytest.mark.parametrize("gpu", [
    lambda: (_ for _ in ()).throw(RuntimeError("Initialisierung fehlgeschlagen")),
    lambda: np.array([np.inf]),
    lambda: np.array([[1.0]]),
])
def test_gpu_initialisierungs_ausfuehrungs_und_ergebnisfehler_fallen_zurueck(gpu):
    protokoll = []
    cpu_aufrufe = 0

    def cpu():
        nonlocal cpu_aufrufe
        cpu_aufrufe += 1
        return np.array([8.0])

    ergebnis = ausfuehren_mit_fallback(
        cpu=cpu,
        gpu=gpu,
        gpu_verfuegbar=True,
        backend="OpenCL",
        geraet="gfx1103",
        ergebnis_gueltig=_vektor_gueltig,
        protokoll=protokoll.append,
    )

    assert np.array_equal(ergebnis, [8.0])
    assert cpu_aufrufe == 1
    assert len(protokoll) == 1
    assert "OpenCL GPU (gfx1103) fehlgeschlagen" in protokoll[0]
    assert "dieselbe Berechnung läuft auf CPU" in protokoll[0]


def test_cpu_fehler_und_ungueltiges_cpu_ergebnis_werden_nicht_verschluckt():
    gemeinsame_argumente = {
        "gpu": lambda: pytest.fail("GPU ist nicht zugeordnet"),
        "gpu_verfuegbar": False,
        "backend": "OpenCL",
        "geraet": None,
        "ergebnis_gueltig": _vektor_gueltig,
    }
    with pytest.raises(RuntimeError, match="CPU-Fehler"):
        ausfuehren_mit_fallback(
            cpu=lambda: (_ for _ in ()).throw(RuntimeError("CPU-Fehler")),
            **gemeinsame_argumente,
        )
    with pytest.raises(BackendFehler, match="CPU lieferte"):
        ausfuehren_mit_fallback(
            cpu=lambda: np.array([np.nan]),
            **gemeinsame_argumente,
        )


def test_gpu_praesenz_ermittelt_geraete_ohne_backendinitialisierung(monkeypatch):
    geraet = SimpleNamespace(name="gfx-test")
    plattform = SimpleNamespace(
        get_devices=lambda device_type: (
            [geraet] if device_type == "GPU"
            else pytest.fail("GPU-Typ muss abgefragt werden")))
    fake_opencl = SimpleNamespace(
        device_type=SimpleNamespace(GPU="GPU"),
        get_platforms=lambda: [plattform],
        Context=lambda *_args: pytest.fail("Präsenztest darf keinen Kontext bauen"),
    )
    monkeypatch.setitem(sys.modules, "pyopencl", fake_opencl)

    assert OpenCLBackend.gpu_namen_ermitteln() == ("gfx-test",)


def test_opencl_geraet_stellt_treiber_und_speicherangaben_bereit():
    geraet = SimpleNamespace(
        name="gfx-test", driver_version="1.2.3", global_mem_size=1024)
    backend = OpenCLBackend(
        cl=None, device=geraet, context=None, queue=None, program=None)

    assert backend.name == "gfx-test"
    assert backend.driver_version == "1.2.3"
    assert backend.global_memory_bytes == 1024


def test_opencl_vektoraddition_auf_gpu_wenn_verfuegbar():
    try:
        backend = OpenCLBackend.oeffnen()
    except BackendNichtVerfuegbar as fehler:
        pytest.skip(str(fehler))

    links = np.array([-3.25, 0.0, 1.5, 17.0], dtype=np.float32)
    rechts = np.array([1.0, 8.5, -2.0, 0.25], dtype=np.float32)
    ergebnis = backend.addiere_vektoren(links, rechts)

    assert np.allclose(ergebnis, links + rechts, rtol=1e-6, atol=1e-6)
    assert np.isfinite(ergebnis).all()
    assert backend.global_memory_bytes > 0


@pytest.mark.parametrize("links,rechts", [
    (np.array([], dtype=float), np.array([], dtype=float)),
    (np.array([1.0]), np.array([1.0, 2.0])),
    (np.array([[1.0]]), np.array([[2.0]])),
    (np.array([np.nan]), np.array([1.0])),
])
def test_opencl_vektoren_validiert_eingaben(links, rechts):
    backend = OpenCLBackend(
        cl=None, device=type("Device", (), {"name": "test"})(),
        context=None, queue=None, program=None)
    with pytest.raises(ValueError):
        backend.addiere_vektoren(links, rechts)
