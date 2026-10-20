"""Reproduzierbare Vorher-/Nachhermessung der Kraftanzeige ohne Physiksolver."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from types import SimpleNamespace

import numpy as np
import pyvista as pv

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "code" / "python"))

from segelphysik.core.auftrieb import Vektor
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import bau_quader
from segelphysik.core.kraftmodell import (
    KraftErgebnis, Kraftbeitrag, Wrench, aggregiere_kraftbeitraege,
)
from segelphysik.core.overlays import (
    LAYER_HYDRO_RUMPF, LAYER_KRAEFTE, LAYER_MOMENTE,
)
from segelphysik.core.pfeilstil import Stil, standard_bereiche
from segelphysik.core.rechenpfad import rechenpfad
from segelphysik.grafik_bruecke import GrafikBruecke


class _Speicher(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        *[(name, ctypes.c_size_t) for name in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage",
            "PrivateUsage")],
    ]


def privater_speicher():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(_Speicher), wintypes.DWORD)
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    daten = _Speicher()
    daten.cb = ctypes.sizeof(daten)
    if not psapi.GetProcessMemoryInfo(
            kernel.GetCurrentProcess(), ctypes.byref(daten), daten.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return daten.PrivateUsage


def ergebnis(anzahl, faktor=1.0):
    beitraege = [
        Kraftbeitrag("hydrostatik", Wrench(
            "simulationsframe", (0, 0, 0), (0, 0, 9.81), (0, 0, 0)),
            "auftrieb", (0, 0, 0)),
        Kraftbeitrag("schwerkraft", Wrench(
            "simulationsframe", (0, 0, 0), (0, 0, -9.81), (0, 0, 0)),
            "gewicht", (0, 0, 0)),
    ]
    for i in range(anzahl):
        beitraege.append(Kraftbeitrag("hydrodynamik_rumpf", Wrench(
            "simulationsframe", (0, i * 0.01, 0),
            (-faktor, 0.01 * i * faktor, 0), (0, 0, 0)), "rumpf:" + str(i)))
    gesamt, normalisiert = aggregiere_kraftbeitraege(beitraege, (0, 0, 0))
    hydro = SimpleNamespace(
        F_A=Vektor((0, 0, 9.81)), M=Vektor((0, 0, 0)),
        K=Vektor((0, 0, 0)), V_tauch=0.001)
    return KraftErgebnis(
        hydro, Vektor(gesamt.kraft_N), Vektor(gesamt.moment_Nm),
        (0.0,) * 6, normalisiert, (0, 0, 0), True)


def messen(anzahl, sichtbar, wiederholungen, abbildung=None, veraenderlich=False):
    bruecke = GrafikBruecke()
    plotter = pv.Plotter(off_screen=True, window_size=(800, 600))
    bruecke._plotter = plotter
    bereiche = standard_bereiche()
    bereiche["kraefteanzeige"] = {"beschriftung": False}
    bruecke._stil = Stil(bereiche.__getitem__)
    koerper = Koerper(form=bau_quader(1, 1, 1), dichte=1)
    bruecke._koerper["referenz"] = {
        "koerper": koerper, "aktiv": True, "position": (0, 0, 0),
        "statisch_R": np.eye(3),
    }
    plotter.add_mesh(pv.Cube(), opacity=0.3)
    plotter.camera_position = [(4, 4, 3), (0, 0, 0), (0, 0, 1)]
    for layer in (LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_HYDRO_RUMPF):
        bruecke._layer.setzen(layer, sichtbar)
    erg = ergebnis(anzahl)
    bruecke.kraefte_daten_setzen("referenz", erg, 1, 9.81, 0.01)
    snapshot = bruecke._kraefte_daten["referenz"]
    for beitrag in (*snapshot.beitraege, snapshot.bilanz):
        bruecke._kraftzeichner().sichtbar[beitrag.instanz_id] = True
    plotter.show(auto_close=False, interactive=False)
    if plotter.ren_win.GetNeverRendered():
        plotter.close()
        raise RuntimeError("Baselinefenster hat keinen Frame gerendert")
    render_ereignisse = []
    observer = plotter.ren_win.AddObserver(
        "EndEvent", lambda *_: render_ereignisse.append(time.perf_counter_ns()))
    zeiten, frames, actors, speicher = [], [], [], []
    tracemalloc.start()
    try:
        for i in range(wiederholungen + 3):
            if veraenderlich:
                bruecke.kraefte_daten_setzen(
                    "referenz", ergebnis(anzahl, 1 + .001 * i), 1, 9.81, .01)
            beginn = time.perf_counter_ns()
            bruecke._kraefte_actors("referenz")
            aktualisiert = time.perf_counter_ns()
            plotter.ren_win.Render()
            fertig = time.perf_counter_ns()
            if i >= 3:
                zeiten.append((aktualisiert - beginn) / 1e6)
                frames.append((fertig - beginn) / 1e6)
                actors.append(
                    plotter.renderer.GetActors().GetNumberOfItems()
                    + (bruecke._vg_renderer.GetActors().GetNumberOfItems()
                       if bruecke._vg_renderer is not None else 0))
                speicher.append(privater_speicher())
        python_aktuell, python_spitze = tracemalloc.get_traced_memory()
        if len(render_ereignisse) < wiederholungen + 3:
            raise RuntimeError("Nicht jeder Messzyklus hat einen Frame erzeugt")
        if abbildung is not None:
            plotter.screenshot(str(abbildung))
    finally:
        tracemalloc.stop()
        plotter.ren_win.RemoveObserver(observer)
        bruecke.kraefte_anzeige_beenden()
        plotter.close()
    return {
        "hydrodynamische_beitraege": anzahl, "anzeige_an": sichtbar,
        "veraenderliche_kraefte": veraenderlich,
        "update_ms": zeiten, "frame_inklusive_update_ms": frames,
        "update_median_ms": statistics.median(zeiten),
        "frame_median_ms": statistics.median(frames),
        "actors": actors, "prozess_private_bytes": speicher,
        "python_bytes_aktuell": python_aktuell,
        "python_bytes_spitze": python_spitze,
        "render_ereignisse": len(render_ereignisse),
        "einschraenkung": (
            ("Wechselnde Kraftvektoren, " if veraenderlich else "Identische Daten, ")
            + "ein Koerper, offscreen, keine Worker/Qt-Tabelle; "
            "kein sichtbarer Leistungs- oder Lifecycle-Abnahmenachweis"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ausgabe", type=Path, required=True)
    parser.add_argument("--wiederholungen", type=int, default=20)
    parser.add_argument("--abbildung", type=Path)
    parser.add_argument("--veraenderlich", action="store_true")
    args = parser.parse_args()
    if args.wiederholungen < 2:
        parser.error("Mindestens zwei Wiederholungen erforderlich")
    daten = {
        "zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "arbeitsbaum": subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True),
        "python": sys.version, "plattform": platform.platform(),
        "prozessor": platform.processor(), "rechenpfad": rechenpfad(),
        "numpy": np.__version__, "pyvista": pv.__version__,
        "vtk": str(pv.vtk_version_info), "viewport": [800, 600],
        "wiederholungen": args.wiederholungen, "aufwaermzyklen": 3,
        "vergleich": (
            "Unveraenderte physikalische Vektoren und Kamera der Baseline; "
            "additive stabile Quell-IDs/Originalpunkte, alle Einzelbeitraege "
            "sichtbar wie zuvor; neue Gruppen aus, Labels aus. "
            "Geometrie und Skalen folgen absichtlich dem V0.11-Renderer, "
            "keine isolierte Kern- oder identische Pixelmessung."),
        "faelle": [
            messen(anzahl, sichtbar, args.wiederholungen,
                   args.abbildung if anzahl == 24 and sichtbar else None,
                   args.veraenderlich)
            for anzahl in (1, 24) for sichtbar in (False, True)],
    }
    args.ausgabe.write_text(
        json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8")
    print(args.ausgabe)
    for fall in daten["faelle"]:
        print(
            fall["hydrodynamische_beitraege"], fall["anzeige_an"],
            "Update %.3f ms, Frame %.3f ms, Actors %d..%d"
            % (fall["update_median_ms"], fall["frame_median_ms"],
               min(fall["actors"]), max(fall["actors"])))


if __name__ == "__main__":
    main()
