"""Opt-in-Instrumentierung des produktiven Workers; keine Physikänderung."""
from __future__ import annotations

import cProfile
from dataclasses import asdict, is_dataclass
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import pstats
import time

import numpy as np

_profil = None


def statistik(werte):
    if not werte:
        return {"anzahl": 0, "summe_s": 0.0, "median_ms": None, "p95_ms": None}
    return {
        "anzahl": len(werte),
        "summe_s": float(sum(werte)),
        "median_ms": float(np.median(werte) * 1000),
        "p95_ms": float(np.percentile(werte, 95) * 1000),
    }


def cpu_statistik(profil, limit=30):
    daten = pstats.Stats(profil).stats
    return [
        {"datei": os.path.basename(datei), "zeile": zeile, "funktion": name,
         "aufrufe": werte[1], "eigenzeit_s": werte[2],
         "kumulativ_s": werte[3]}
        for (datei, zeile, name), werte in sorted(
            daten.items(), key=lambda item: item[1][3], reverse=True)[:limit]
    ]


def eingabe_hash(koerper, physik, rho_w, backend, cd):
    """Alle Snapshotdaten einschließlich Masse/Trägheit ohne Pickle serialisieren."""
    digest = hashlib.sha256()

    def wert(obj):
        if isinstance(obj, np.ndarray):
            digest.update(str((obj.dtype.str, obj.shape)).encode())
            digest.update(obj.tobytes())
        elif isinstance(obj, (tuple, list)):
            digest.update(b"[")
            for teil in obj:
                wert(teil)
            digest.update(b"]")
        elif is_dataclass(obj):
            wert(asdict(obj))
        elif hasattr(obj, "__slots__"):
            wert({key: getattr(obj, key) for key in obj.__slots__})
        elif hasattr(obj, "__dict__"):
            wert(vars(obj))
        elif isinstance(obj, dict):
            for key in sorted(obj):
                digest.update(str(key).encode())
                wert(obj[key])
        else:
            digest.update(repr(obj).encode("utf-8"))

    wert((koerper, physik, rho_w, backend, cd))
    return digest.hexdigest()


def umgebung():
    versionen = {}
    for paket in ("numpy", "PySide6", "pyvista", "pyvistaqt", "vtk", "manifold3d"):
        versionen[paket] = importlib.metadata.version(paket)
    return {
        "python": platform.python_version(), "plattform": platform.platform(),
        "prozessor": platform.processor(), "cpu_threads": os.cpu_count(),
        "bibliotheken": versionen,
        "npu": {
            "onnxruntime_installiert": importlib.util.find_spec("onnxruntime") is not None,
            "zugriff_nachgewiesen": False,
            "operatoren_nachgewiesen": [],
            "hinweis": "Ohne NPU-Execution-Provider kein Operator-/Kernelnachweis.",
        },
    }


class WorkerProfil:
    def __init__(self, datei, cpu_batches=0):
        self.datei = Path(datei)
        self.cpu_batches = cpu_batches
        self.cpu = cProfile.Profile()
        self.batch = 0
        self.letzte_pose = None
        self.posen = set()
        self.werte = {}
        self.treffer = 0
        self.aufrufe = 0

    def messen(self, name, funktion):
        def aufruf(*args, **kwargs):
            start = time.perf_counter()
            try:
                return funktion(*args, **kwargs)
            finally:
                self.werte.setdefault(name, []).append(time.perf_counter() - start)
        return aufruf

    def hydro_messen(self, funktion):
        gemessen = self.messen("hydrostatik_geometrie", funktion)

        def aufruf(lage, *args, **kwargs):
            # Bitexakte ganze Pose, kein Runden, kein toleranzbasierter Cache.
            schluessel = tuple(np.asarray(w, dtype=np.float64).tobytes() for w in lage)
            self.treffer += schluessel == self.letzte_pose
            self.letzte_pose = schluessel
            self.posen.add(schluessel)
            self.aufrufe += 1
            return gemessen(lage, *args, **kwargs)
        return aufruf

    def schreiben(self, daten):
        with self.datei.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(daten, ensure_ascii=False) + "\n")


class _KraftMessung:
    def __init__(self, kraftfunktion, profil):
        self.original = kraftfunktion
        self.gemessen = profil.messen("kraefte_gesamt", kraftfunktion)

    def __getattr__(self, name):
        return getattr(self.original, name)

    def __call__(self, *args, **kwargs):
        return self.gemessen(*args, **kwargs)


def profil_initialisieren(koerper, rho_w, physik, hydrostatik_pfad="exakt_union",
                         cd_volumenkoerper=None, *, datei, cpu_batches=0):
    global _profil
    from segelphysik.core import echtzeit_prozess as worker
    from segelphysik.core import dynamik_6dof

    start = time.perf_counter()
    worker.initialisieren(
        koerper, rho_w, physik, hydrostatik_pfad, cd_volumenkoerper)
    _profil = WorkerProfil(datei, cpu_batches)
    modell = worker._kraftfunktion.kraftmodell
    modell.hydrostatik = _profil.hydro_messen(modell.hydrostatik)
    if modell.hydrodynamik is not None:
        modell.hydrodynamik.beitraege_erzeugen = _profil.messen(
            "hydrodynamik", modell.hydrodynamik.beitraege_erzeugen)
    modell.mit_hydrostatik = _profil.messen(
        "kraftaggregation_inkl_hydrodynamik", modell.mit_hydrostatik)
    original = getattr(dynamik_6dof.schritt, "_benchmark_original", dynamik_6dof.schritt)
    dynamik_6dof.schritt = _profil.messen("integrator_inkl_kraefte", original)
    dynamik_6dof.schritt._benchmark_original = original
    worker._kraftfunktion = _KraftMessung(worker._kraftfunktion, _profil)
    _profil.schreiben({
        "typ": "initialisierung", "dauer_s": time.perf_counter() - start,
        "eingabe_sha256": eingabe_hash(
            koerper, physik, rho_w, hydrostatik_pfad, cd_volumenkoerper),
        "masse_kg": float(koerper.masse), "dt_s": float(physik.dt_s),
        "schwerpunkt": np.asarray(koerper.r_S).tolist(),
        "hydrostatik_backend": hydrostatik_pfad, "pid": os.getpid(),
        "instrumentierung_version": 2,
        "physikparameter": {key: getattr(physik, key) for key in physik.__slots__},
    })


def profil_schritte_berechnen(zustand, anzahl_schritte, fremdkraft=None,
                            ruderwinkel_rad=0.0):
    from segelphysik.core import echtzeit_prozess as worker

    _profil.werte = {}
    profilieren = _profil.batch < _profil.cpu_batches
    if profilieren:
        _profil.cpu.enable()
    start = time.perf_counter()
    try:
        ergebnis = worker.schritte_berechnen(
            zustand, anzahl_schritte, fremdkraft, ruderwinkel_rad)
    finally:
        if profilieren:
            _profil.cpu.disable()
    dauer = time.perf_counter() - start
    _profil.batch += 1
    werte = _profil.werte
    hydro = sum(werte.get("hydrostatik_geometrie", []))
    aggregation = sum(werte.get("kraftaggregation_inkl_hydrodynamik", []))
    dynamik = sum(werte.get("hydrodynamik", []))
    kraefte = sum(werte.get("kraefte_gesamt", []))
    integration = sum(werte.get("integrator_inkl_kraefte", []))
    _profil.schreiben({
        "typ": "batch", "batch": _profil.batch, "schritte": anzahl_schritte,
        "worker_s": dauer, "cpu_profiliert": profilieren,
        "hydrostatik_geometrie_s": hydro, "hydrodynamik_s": dynamik,
        "kraftaggregation_exklusiv_s": aggregation - dynamik,
        "integrator_exklusiv_s": integration - kraefte,
        "kraftaufruf_rest_s": kraefte - hydro - aggregation,
        "worker_rest_s": dauer - integration,
        "rohwerte_s": werte, "cache_pose_aufrufe": _profil.aufrufe,
        "cache_pose_direkte_treffer": _profil.treffer,
        "cache_pose_eindeutig": len(_profil.posen),
        "fehler": ergebnis[2],
        "cpu_hotspots": cpu_statistik(_profil.cpu) if (
            profilieren and _profil.batch == _profil.cpu_batches) else None,
    })
    return ergebnis


def worker_bericht(datei, roundtrips=None):
    with Path(datei).open(encoding="utf-8") as stream:
        roh = [json.loads(zeile) for zeile in stream if zeile.strip()]
    batches = [zeile for zeile in roh if zeile["typ"] == "batch"]
    komponenten = {}
    for name in (
        "hydrostatik_geometrie", "hydrodynamik", "kraftaggregation_exklusiv",
        "integrator_exklusiv", "worker_rest",
    ):
        komponenten[name] = statistik([b[name + "_s"] for b in batches])
    if batches and "kraftaufruf_rest_s" in batches[0]:
        komponenten["kraftaufruf_rest"] = statistik([
            b["kraftaufruf_rest_s"] for b in batches])
    elif batches:
        komponenten["integration_inkl_kraftaufruf_rest"] = komponenten.pop(
            "integrator_exklusiv")
    schritte = {}
    for name in (
        "hydrostatik_geometrie", "hydrodynamik",
        "kraftaggregation_inkl_hydrodynamik", "integrator_inkl_kraefte",
        "kraefte_gesamt",
    ):
        schritte[name] = statistik([
            wert for batch in batches
            for wert in batch["rohwerte_s"].get(name, [])
        ])
    roundtrips = roundtrips or []
    paare = list(zip(roundtrips, batches))
    return {
        "initialisierung": [z for z in roh if z["typ"] == "initialisierung"],
        "batchkomponenten": komponenten,
        "schrittmessungen": schritte,
        "worker_queue_ipc_protokoll_rest": statistik([
            dauer - batch["worker_s"] for dauer, batch in paare
        ]),
        "roundtrip_zugeordnet": len(paare),
        "roundtrip_nicht_zugeordnet": abs(len(roundtrips) - len(batches)),
        "cache_pruefung": {
            key: batches[-1][key] if batches else 0 for key in (
                "cache_pose_aufrufe", "cache_pose_direkte_treffer", "cache_pose_eindeutig")
        },
        "cpu_hotspots": [b["cpu_hotspots"] for b in batches if b["cpu_hotspots"]],
        "rohdatei": str(Path(datei).resolve()),
        "batchanzahl": len(batches),
        "messhinweis": (
            "Opt-in-Timer; Integrator exklusiv = Schritt minus Hydrostatik und "
            "Kraftaggregation im Schema 1 (inkl. Kraftaufrufverwaltung); "
            "Schema 2 trennt gesamten Kraftaufruf und dessen Rest zusätzlich ab. "
            "Worker-Rest separat. CPU-Profilbatches markiert. "
            "Cachetreffer sind nur beobachtet, kein Ergebniscache eingebaut."),
    }
