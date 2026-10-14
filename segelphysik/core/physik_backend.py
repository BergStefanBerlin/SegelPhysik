"""Optionaler Rechenbackend-Prototyp und expliziter CPU-Fallback."""
from __future__ import annotations

import logging
from collections.abc import Callable

import numpy as np

_LOGGER = logging.getLogger(__name__)


class BackendFehler(RuntimeError):
    """GPU-Ergebnis oder GPU-Ausführung ist unbrauchbar."""


class BackendNichtVerfuegbar(BackendFehler):
    """OpenCL oder ein OpenCL-GPU-Gerät ist nicht verfügbar."""


def _opencl_laden():
    try:
        import pyopencl as cl
    except ImportError as fehler:
        raise BackendNichtVerfuegbar(
            "PyOpenCL fehlt; GPU-Unterstützung ist optional") from fehler
    return cl


def _opencl_gpu_geraete(cl):
    try:
        return [
            geraet
            for plattform in cl.get_platforms()
            for geraet in plattform.get_devices(
                device_type=cl.device_type.GPU)
        ]
    except Exception as fehler:
        raise BackendNichtVerfuegbar(
            "OpenCL-GPU-Geräte konnten nicht ermittelt werden: %s" % fehler
        ) from fehler


def ausfuehren_mit_fallback(*, cpu: Callable, gpu: Callable | None,
                            gpu_verfuegbar: bool, backend: str,
                            geraet: str | None,
                            ergebnis_gueltig: Callable,
                            protokoll: Callable[[str], None] | None = None):
    """Versucht den fest zugeordneten GPU-Pfad und fällt bei Fehlern auf CPU zurück.

    Die GPU-Aufgabe wird vom aufrufenden Code festgelegt. Diese Funktion trifft
    keine Leistungswahl und prüft kein Backend auf Geschwindigkeit.
    """
    def melde(nachricht, *, fehler=False):
        if protokoll is not None:
            protokoll(nachricht)
        elif fehler:
            _LOGGER.warning(nachricht)
        else:
            _LOGGER.info(nachricht)

    def pruefe(ergebnis, pfad):
        try:
            gueltig = bool(ergebnis_gueltig(ergebnis))
        except Exception as fehler:
            raise BackendFehler(
                "%s-Ergebnis konnte nicht validiert werden: %s"
                % (pfad, fehler)) from fehler
        if not gueltig:
            raise BackendFehler("%s lieferte ein ungültiges oder unvollständiges Ergebnis"
                                % pfad)
        return ergebnis

    if gpu_verfuegbar and gpu is not None:
        try:
            ergebnis = pruefe(gpu(), "GPU")
        except Exception as fehler:
            melde("%s GPU%s fehlgeschlagen; dieselbe Berechnung läuft auf CPU: %s"
                  % (backend, " (%s)" % geraet if geraet else "", fehler),
                  fehler=True)
        else:
            melde("%s GPU-Pfad aktiv%s"
                  % (backend, " (%s)" % geraet if geraet else ""))
            return ergebnis
    elif not gpu_verfuegbar:
        melde("CPU-Pfad aktiv (keine GPU verfügbar)")
    else:
        melde("CPU-Pfad aktiv (Aufgabe ist im Code der CPU zugeordnet)")

    return pruefe(cpu(), "CPU")


class OpenCLBackend:
    """Kleiner OpenCL-Prototyp für Geräte-, Transfer- und Kernelprüfung."""

    _KERNEL = """
    __kernel void add_vectors(__global const float *left,
                              __global const float *right,
                              __global float *result) {
        size_t i = get_global_id(0);
        result[i] = left[i] + right[i];
    }
    """

    def __init__(self, cl, device, context, queue, program):
        self._cl = cl
        self._device = device
        self._context = context
        self._queue = queue
        self._program = program

    @property
    def name(self):
        return str(self._device.name).strip()

    @property
    def driver_version(self):
        return str(self._device.driver_version)

    @property
    def global_memory_bytes(self):
        return int(self._device.global_mem_size)

    @classmethod
    def gpu_namen_ermitteln(cls):
        """Ermittelt nur verfügbare GPU-Gerätenamen, ohne Backendinitialisierung."""
        cl = _opencl_laden()
        return tuple(str(geraet.name).strip()
                     for geraet in _opencl_gpu_geraete(cl))

    @classmethod
    def oeffnen(cls):
        cl = _opencl_laden()
        geraete = _opencl_gpu_geraete(cl)
        if not geraete:
            raise BackendNichtVerfuegbar("Kein OpenCL-GPU-Gerät vorhanden")

        geraet = geraete[0]
        try:
            kontext = cl.Context([geraet])
            warteschlange = cl.CommandQueue(kontext)
            programm = cl.Program(kontext, cls._KERNEL).build()
        except Exception as fehler:
            raise BackendFehler(
                "OpenCL-Initialisierung für %s fehlgeschlagen: %s"
                % (geraet.name, fehler)) from fehler
        return cls(cl, geraet, kontext, warteschlange, programm)

    def addiere_vektoren(self, links, rechts):
        """Führt als Kompatibilitätsprobe elementweise float32-Addition aus."""
        try:
            links = np.ascontiguousarray(links, dtype=np.float32)
            rechts = np.ascontiguousarray(rechts, dtype=np.float32)
        except (TypeError, ValueError, OverflowError) as fehler:
            raise ValueError("GPU-Eingaben müssen numerische float32-Vektoren sein") from fehler
        if (links.ndim != 1 or rechts.ndim != 1 or links.size == 0
                or links.shape != rechts.shape):
            raise ValueError("GPU-Eingaben müssen gleich lange, nichtleere Vektoren sein")
        if not np.isfinite(links).all() or not np.isfinite(rechts).all():
            raise ValueError("GPU-Eingaben enthalten nicht-endliche Werte")

        cl = self._cl
        flags = cl.mem_flags
        try:
            links_gpu = cl.Buffer(
                self._context, flags.READ_ONLY | flags.COPY_HOST_PTR,
                hostbuf=links)
            rechts_gpu = cl.Buffer(
                self._context, flags.READ_ONLY | flags.COPY_HOST_PTR,
                hostbuf=rechts)
            ergebnis_gpu = cl.Buffer(
                self._context, flags.WRITE_ONLY, size=links.nbytes)
            ereignis = self._program.add_vectors(
                self._queue, (links.size,), None,
                links_gpu, rechts_gpu, ergebnis_gpu)
            ergebnis = np.empty_like(links)
            cl.enqueue_copy(
                self._queue, ergebnis, ergebnis_gpu,
                wait_for=[ereignis]).wait()
        except Exception as fehler:
            raise BackendFehler(
                "OpenCL-Kernel oder Datentransfer auf %s fehlgeschlagen: %s"
                % (self.name, fehler)) from fehler
        if ergebnis.shape != links.shape or not np.isfinite(ergebnis).all():
            raise BackendFehler("OpenCL lieferte ein unvollständiges oder nicht-endliches Ergebnis")
        return ergebnis
