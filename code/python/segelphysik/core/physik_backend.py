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


class OpenCLVoxelHydrostatik:
    """GPU-Reduktion eines körperfesten Voxelrasters für beliebige Poseebenen."""

    _KERNEL = """
    #pragma OPENCL EXTENSION cl_khr_fp64 : enable
    __kernel void reduce_wet_centres(
            __global const double *points, const ulong count,
            const double nx, const double ny, const double nz,
            const double offset, const double margin,
            __global double *partial,
            __local double *local_count, __local double *local_x,
            __local double *local_y, __local double *local_z,
            __local double *local_uncertain) {
        const size_t i = get_global_id(0);
        const size_t lane = get_local_id(0);
        const size_t width = get_local_size(0);
        double n = 0.0, x = 0.0, y = 0.0, z = 0.0, uncertain = 0.0;
        if (i < count) {
            const double px = points[3 * i];
            const double py = points[3 * i + 1];
            const double pz = points[3 * i + 2];
            const double signed_distance = nx * px + ny * py + nz * pz
                                           + offset;
            if (fabs(signed_distance) <= margin) {
                uncertain = 1.0;
            } else if (signed_distance < 0.0) {
                n = 1.0;
                x = px;
                y = py;
                z = pz;
            }
        }
        local_count[lane] = n;
        local_x[lane] = x;
        local_y[lane] = y;
        local_z[lane] = z;
        local_uncertain[lane] = uncertain;
        barrier(CLK_LOCAL_MEM_FENCE);
        for (size_t stride = width / 2; stride > 0; stride >>= 1) {
            if (lane < stride) {
                local_count[lane] += local_count[lane + stride];
                local_x[lane] += local_x[lane + stride];
                local_y[lane] += local_y[lane + stride];
                local_z[lane] += local_z[lane + stride];
                local_uncertain[lane] += local_uncertain[lane + stride];
            }
            barrier(CLK_LOCAL_MEM_FENCE);
        }
        if (lane == 0) {
            const size_t group = get_group_id(0);
            partial[5 * group] = local_count[0];
            partial[5 * group + 1] = local_x[0];
            partial[5 * group + 2] = local_y[0];
            partial[5 * group + 3] = local_z[0];
            partial[5 * group + 4] = local_uncertain[0];
        }
    }
    """

    def __init__(self, cl, device, context, queue, program,
                 points_gpu, partial_gpu, point_count, group_size,
                 group_count, voxel_volume):
        self._cl = cl
        self._device = device
        self._context = context
        self._queue = queue
        self._program = program
        self._kernel = cl.Kernel(program, "reduce_wet_centres")
        self._points_gpu = points_gpu
        self._partial_gpu = partial_gpu
        self._point_count = point_count
        self._group_size = group_size
        self._group_count = group_count
        self._voxel_volume = voxel_volume

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
    def oeffnen(cls, voxelzentren, voxelvolumen):
        cl = _opencl_laden()
        geraete = _opencl_gpu_geraete(cl)
        if not geraete:
            raise BackendNichtVerfuegbar("Kein OpenCL-GPU-Gerät vorhanden")
        geraet = geraete[0]
        if "cl_khr_fp64" not in str(geraet.extensions).split():
            raise BackendNichtVerfuegbar(
                "OpenCL-Gerät unterstützt keine fp64-Reduktion")
        try:
            punkte = np.ascontiguousarray(voxelzentren, dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as fehler:
            raise ValueError("Voxelzentren müssen endliche 3D-Werte sein") from fehler
        if (punkte.ndim != 2 or punkte.shape[1] != 3 or len(punkte) == 0
                or not np.isfinite(punkte).all()):
            if punkte.ndim == 2 and punkte.shape == (0, 3):
                raise BackendNichtVerfuegbar(
                    "Körperfestes Raster enthält keine Voxelzentren")
            raise ValueError("Voxelzentren müssen eine nichtleere endliche Nx3-Matrix sein")
        gruppengroesse = min(
            128, int(geraet.max_work_group_size),
            int(geraet.max_work_item_sizes[0]))
        gruppengroesse = 1 << (gruppengroesse.bit_length() - 1)
        gruppen = (len(punkte) + gruppengroesse - 1) // gruppengroesse
        try:
            kontext = cl.Context([geraet])
            warteschlange = cl.CommandQueue(kontext)
            programm = cl.Program(kontext, cls._KERNEL).build()
            flags = cl.mem_flags
            punkte_gpu = cl.Buffer(
                kontext, flags.READ_ONLY | flags.COPY_HOST_PTR,
                hostbuf=punkte)
            partial_gpu = cl.Buffer(
                kontext, flags.WRITE_ONLY, size=gruppen * 5 * 8)
        except Exception as fehler:
            raise BackendFehler(
                "OpenCL-Hydrostatikinitialisierung für %s fehlgeschlagen: %s"
                % (geraet.name, fehler)) from fehler
        return cls(
            cl, geraet, kontext, warteschlange, programm, punkte_gpu,
            partial_gpu, len(punkte), gruppengroesse, gruppen,
            float(voxelvolumen))

    def auswerten_6dof(self, rotation, position, grenzen_min, grenzen_max):
        rotation = np.asarray(rotation, dtype=np.float64)
        position = np.asarray(position, dtype=np.float64)
        if (rotation.shape != (3, 3) or position.shape != (3,)
                or not np.isfinite(rotation).all()
                or not np.isfinite(position).all()):
            raise ValueError("Pose muss eine endliche 3x3-Rotation und Position sein")
        skala = max(
            1.0, float(np.linalg.norm(grenzen_min)),
            float(np.linalg.norm(grenzen_max)),
            float(np.linalg.norm(position)))
        margin = 64.0 * np.finfo(np.float64).eps * skala
        normale = rotation[2, :]
        cl = self._cl
        try:
            lokal_speicher = [
                cl.LocalMemory(self._group_size * 8) for _ in range(5)]
            ereignis = self._kernel(
                self._queue,
                (self._group_count * self._group_size,),
                (self._group_size,),
                self._points_gpu,
                np.uint64(self._point_count),
                np.float64(normale[0]), np.float64(normale[1]),
                np.float64(normale[2]), np.float64(position[2]),
                np.float64(margin), self._partial_gpu,
                *lokal_speicher)
            teile = np.empty((self._group_count, 5), dtype=np.float64)
            cl.enqueue_copy(
                self._queue, teile, self._partial_gpu,
                wait_for=[ereignis]).wait()
        except Exception as fehler:
            raise BackendFehler(
                "OpenCL-Hydrostatik auf %s fehlgeschlagen: %s"
                % (self.name, fehler)) from fehler
        if not np.isfinite(teile).all():
            raise BackendFehler("OpenCL-Hydrostatik lieferte nicht-endliche Summen")
        summen = teile.sum(axis=0)
        if summen[4] > 0.0:
            raise BackendFehler(
                "Voxel liegen numerisch auf der Wasserfläche; CPU-Referenz nötig")
        if summen[0] == 0.0:
            return 0.0, np.zeros(3, dtype=np.float64)
        schwerpunkt_lokal = summen[1:4] / summen[0]
        schwerpunkt_welt = rotation @ schwerpunkt_lokal + position
        volumen = float(summen[0] * self._voxel_volume)
        if (not np.isfinite(volumen)
                or not np.isfinite(schwerpunkt_welt).all()):
            raise BackendFehler("OpenCL-Hydrostatik lieferte ungültige Messwerte")
        return volumen, schwerpunkt_welt
