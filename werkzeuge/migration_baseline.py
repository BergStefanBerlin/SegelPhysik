"""Reproduzierbare Python-Baselines fuer M1, ohne produktive Umschaltung.

Jeder Aufruf schreibt ein neues Ergebnisverzeichnis. Kernmessungen und
sichtbare Live-Laeufe sind getrennt; instrumentierte Zeiten sind nie Baselines.
"""
from __future__ import annotations

import argparse
import cProfile
import ctypes
from ctypes import wintypes
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import profile
import pstats
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from werkzeuge.benchmark_profil import eingabe_hash, umgebung
from werkzeuge.migration_inventar import (
    REFERENZ, inventar, referenzmanifest, schreiben, texthash,
)
from werkzeuge.migration_vergleich import messen, vergleiche

MODELLE = ("optimist", "folkeboot", "yacht1")


def windows_prozessspeicher(pid=None):
    class Zaehler(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            *[(name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")],
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.K32GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(Zaehler), wintypes.DWORD)
    kernel.K32GetProcessMemoryInfo.restype = wintypes.BOOL
    handle = kernel.GetCurrentProcess() if pid is None else kernel.OpenProcess(0x410, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        daten = Zaehler()
        daten.cb = ctypes.sizeof(daten)
        if not kernel.K32GetProcessMemoryInfo(handle, ctypes.byref(daten), daten.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return {
            "pid": os.getpid() if pid is None else pid,
            "working_set_bytes": daten.WorkingSetSize,
            "private_bytes": daten.PrivateUsage,
        }
    finally:
        if pid is not None and not kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def profilieren(funktion):
    profil = cProfile.Profile()
    ergebnis = profil.runcall(funktion)
    return ergebnis, profilzeilen(profil)


def profilzeilen(profil):
    daten = profil.stats if isinstance(profil, pstats.Stats) else pstats.Stats(profil).stats
    zeilen = []
    for (datei, zeile, name), werte in sorted(daten.items()):
        if datei == "profile" and zeile == 0:
            continue
        if datei == "" and zeile == 0:
            datei = "~"
        quellpfad = Path(datei)
        if quellpfad.is_absolute() and quellpfad.is_relative_to(ROOT):
            datei = quellpfad.relative_to(ROOT).as_posix()
        zeilen.append({
            "datei": datei, "zeile": zeile, "funktion": name,
            "primitive_aufrufe": werte[0], "aufrufe": werte[1],
            "eigenzeit_s": werte[2], "gesamtzeit_s": werte[3],
            "aufrufer": [
                {"datei": caller[0], "zeile": caller[1], "funktion": caller[2],
                 "statistik": counts}
                for caller, counts in sorted(werte[4].items())
            ],
        })
    return zeilen


class CallbackProfil:
    """Misst nur abgeschlossene synchrone GUI-Aufrufe, keine Ereignisschleife."""

    def __init__(self):
        self.statistik = None
        self.aktiv = False
        self.messen = False
        self.aufrufe = 0

    def aufrufen(self, funktion, *args, **kwargs):
        if not self.messen or self.aktiv:
            return funktion(*args, **kwargs)
        self.aktiv = True
        self.aufrufe += 1
        # sys.setprofile ist threadlokal; cProfile/Monitoring erfasst hier auch Qt-Worker.
        teilprofil = profile.Profile(timer=time.perf_counter)
        try:
            return teilprofil.runcall(funktion, *args, **kwargs)
        finally:
            self.aktiv = False
            if self.statistik is None:
                self.statistik = pstats.Stats(teilprofil)
            else:
                self.statistik.add(teilprofil)

    def bericht(self):
        if self.aktiv or self.aufrufe == 0:
            raise ValueError("Abgeschlossene synchrone Profilaufrufe fehlen")
        return profilzeilen(self.statistik)


def buildinventar(buildverzeichnis=None):
    verzeichnis = (ROOT / "build" / "native" / "cp314-cp314-win_amd64"
                   if buildverzeichnis is None else Path(buildverzeichnis))
    cache = verzeichnis / "CMakeCache.txt"
    daten = {}
    for zeile in cache.read_text(encoding="utf-8").splitlines():
        if zeile.startswith((
                "CMAKE_CXX_FLAGS:", "CMAKE_CXX_FLAGS_RELEASE:",
                "CMAKE_GENERATOR:", "CMAKE_GENERATOR_PLATFORM:",
                "CMAKE_GENERATOR_INSTANCE:")):
            key, wert = zeile.split("=", 1)
            daten[key] = wert
    compilerdateien = list(cache.parent.glob("CMakeFiles\\*\\CMakeCXXCompiler.cmake"))
    if len(compilerdateien) != 1:
        raise ValueError("Eindeutiger konfigurierter C++-Compiler fehlt")
    daten["compilerkonfiguration"] = compilerdateien[0].read_text(encoding="utf-8")
    daten["buildtyp"] = "Release (pyproject.toml)"
    daten["native_paketversion"] = importlib.metadata.version("segelphysik-native")
    return daten


def hardware():
    befehl = (
        "$ErrorActionPreference='Stop'; "
        "@{cpu=@(Get-CimInstance Win32_Processor | "
        "Select-Object Name,NumberOfCores,NumberOfLogicalProcessors); "
        "gpu=@(Get-CimInstance Win32_VideoController | "
        "Select-Object Name,DriverVersion); "
        "ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory} "
        "| ConvertTo-Json -Depth 4"
    )
    return json.loads(subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", befehl],
        text=True, encoding="utf-8"))


def kraftdaten(ergebnis):
    return {
        "volumen_m3": float(ergebnis.V_tauch),
        "auftrieb_N": ergebnis.F_A.as_array(),
        "schwerpunkt_m": ergebnis.K.as_array(),
        "gesamt_wrench": ergebnis.gesamt_wrench,
        "beitraege": ergebnis.beitraege,
    }


def serialisieren(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError("Nicht serialisierbarer Messwert: %s" % type(obj).__name__)


def kernmessung(name, wiederholungen):
    from segelphysik.core import echtzeit_prozess
    from segelphysik.core.auftrieb import baue_kraftfunktion
    from segelphysik.core.dynamik_6dof import Zustand6DOF
    from segelphysik.core.fabriken import baue_modellpaket
    from segelphysik.core.konfig_lader import lade_konfig, lade_physik
    from segelphysik.core.statisch_robust import loese_robust

    konfig = lade_konfig(ROOT / "konfigurationen")
    physik = lade_physik(ROOT / "konfigurationen")
    paket = ROOT / "code" / "modelle" / name
    aufbau, koerperwerte = messen(
        lambda: baue_modellpaket(konfig, paket)[0], wiederholungen=wiederholungen)
    koerper = koerperwerte[-1]
    snapshot = koerper.snapshot()
    vorbereitung, _ = messen(
        lambda: echtzeit_prozess.initialisieren(
            snapshot, konfig.wasser_dichte(), physik),
        wiederholungen=wiederholungen)
    zustand = Zustand6DOF(
        position=(0.0, 0.0, -0.14),
        geschwindigkeit_koerper=(0.2, -0.1, 0.0),
        winkelgeschwindigkeit_koerper=(0.01, -0.01, 0.02))

    def batch():
        echtzeit_prozess._kraftfunktion.aktualisieren()
        resultat = echtzeit_prozess.schritte_berechnen(zustand, 10)
        if resultat[2] is not None:
            raise RuntimeError("%s: Workerfehler: %s" % (name, resultat[2]))
        return {"zustand": resultat[0], "kraefte": kraftdaten(resultat[1])}

    zeiten, ergebnisse = messen(batch, wiederholungen=wiederholungen)
    for wert in ergebnisse[1:]:
        vergleiche(ergebnisse[0], wert)
    _, workerprofil = profilieren(batch)
    hydro = baue_kraftfunktion(
        snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2,
        pfad="exakt_union")

    def solver():
        return loese_robust(hydro, snapshot.masse, g=physik.g_m_pro_s2,
                            start=(-0.14, 0.15))

    solverzeiten, solverwerte = messen(solver, wiederholungen=wiederholungen)
    _, solverprofil = profilieren(solver)
    _, aufbauprofil = profilieren(lambda: baue_modellpaket(konfig, paket))
    return {
        "modell": name, "backend": "python/exakt_union",
        "eingabe_sha256": eingabe_hash(
            snapshot, physik, konfig.wasser_dichte(), "exakt_union", None),
        "masse_kg": snapshot.masse, "dt_s": physik.dt_s,
        "dreiecke": sum(len(f) for _, f in snapshot.blatt_meshes),
        "punkte": sum(len(p) for p, _ in snapshot.blatt_meshes),
        "schritte_pro_batch": 10, "startzustand": asdict(zustand),
        "modellaufbau_warm": aufbau, "worker_vorbereitung": vorbereitung,
        "workerbatch_ohne_ipc": zeiten, "statischer_solver": solverzeiten,
        "worker_ergebnis": ergebnisse[0], "solver_ergebnisse": solverwerte,
        "instrumentierte_profile": {
            "workerbatch": workerprofil, "statischer_solver": solverprofil,
            "modellaufbau": aufbauprofil},
        "offene_messungen": [
            "Stationaerer Solver, analytische/generische Koerper, Fehlerszenarien",
            "30-s-Dynamikfolgen, Beladung/Gelenke und kalter Modellaufbau",
            "IPC/Kopien/GIL und alle Darstellungs-/optionalen Pfade"],
        "hinweis": "Profile getrennt von uninstrumentierten Zeiten; kein C++-Gewinn.",
    }


def funktionsmessungen(modelldaten):
    zeilen = []
    for eintrag in inventar()["eintraege"]:
        belege = []
        for daten in modelldaten:
            for szenario, profil in daten["instrumentierte_profile"].items():
                for funktion in profil:
                    if (funktion["datei"] ==
                            "code/python/segelphysik/" + eintrag["modul"]
                            and funktion["zeile"] == eintrag["profilzeile"]):
                        belege.append({
                            "rohdatei": daten["modell"] + ".json",
                            "szenario": szenario, "modell": daten["modell"],
                            "eingabe_sha256": daten["eingabe_sha256"],
                            "punkte": daten["punkte"], "dreiecke": daten["dreiecke"],
                            "profil": funktion,
                        })
        zeilen.append({
            "anforderung": eintrag["anforderung"],
            "modul": eintrag["modul"], "funktion": eintrag["funktion"],
            "spec_zeile": eintrag["spec_zeile"], "profilbelege": belege,
            "messstatus": ("im instrumentierten Kernlauf aufgerufen" if belege
                          else "in diesen Kernlaeufen nicht beobachtet; gezielter Fall offen"),
            "blockhinweis": (
                "Innerer Block ist nur im Profil seiner ganzen Funktion enthalten; "
                "nicht als eigene Zeit oder mehrfach addieren."),
            "migrationsentscheidung": "noch offen/blockiert, mit konkreter Ursache",
        })
    return {"fassung": 1, "referenzcommit": REFERENZ, "eintraege": zeilen}


def live_kommando(modell, optik, ziel, *, warmup=30.0, dauer=300.0):
    if modell not in MODELLE or optik not in ("standard", "schulung"):
        raise ValueError("Unbekanntes Modell oder Optik")
    if (not math.isfinite(warmup) or not math.isfinite(dauer)
            or warmup < 0 or dauer < 300):
        raise ValueError("Live-Baseline braucht Warmup >= 0 und Dauer >= 300 s")
    cmd = [
        sys.executable, str(ROOT / "werkzeuge" / "benchmark_gui_live.py"),
        "--scene", modell, "--backend", "exakt_union",
        "--warmup", str(warmup), "--duration", str(dauer),
        "--viewport-width", "640", "--viewport-height", "480",
        "--measure-memory",
        "--output", str(ziel),
    ]
    if optik == "schulung":
        cmd.append("--schulungsdarstellung")
    return cmd


def speicherreihe_pruefen(reihe, dauer):
    if (len(reihe) < 3 or reihe[0]["wandzeit_s"] > 5.
            or reihe[-1]["wandzeit_s"] < dauer - 5.):
        raise ValueError("Speicherzeitreihe deckt das Messfenster nicht ab")
    zeiten = [punkt["wandzeit_s"] for punkt in reihe]
    if (not all(math.isfinite(t) and t >= 0 for t in zeiten)
            or not all(b > a for a, b in zip(zeiten, zeiten[1:]))):
        raise ValueError("Speicherzeitpunkte sind nicht endlich und streng steigend")
    for punkt in reihe:
        if not punkt["worker"]:
            raise ValueError("Physikprozess fehlt in der Speichermessung")
        for prozess in [punkt["gui"], *punkt["worker"]]:
            if any(isinstance(prozess[key], bool) or not isinstance(prozess[key], int)
                   or prozess[key] <= 0
                   for key in ("pid", "working_set_bytes", "private_bytes")):
                raise ValueError("Positive Prozess-/Speicherzaehler erforderlich")


def live_pruefen(daten, modell, optik, dauer, *, speicher=False):
    if (daten["szene"] != modell or daten["qpa_plattform"] != "windows"
            or daten["hydrostatik_backend"] != "exakt_union"
            or not daten["messlauf_gueltig"] or daten["fehler"]
            or daten["messdauer_s"] < dauer or daten["physik_batches"] < 1
            or daten["qt_frame_swapped"] < 2):
        raise ValueError("Ungueltige sichtbare Baseline: " + modell)
    if (daten["warmup_s"] != 30
            or daten["render_optionen_override"] != {
                "schulungsdarstellung": optik == "schulung"}
            or not daten["aktive_layer"]
            or not all(daten["aktive_layer"].values())):
        raise ValueError("Warmup, Optik oder Pflichtlayer veraendert: " + modell)
    if (daten["viewport_vorgabe_px"] != [640, 480]
            or daten["viewport_start_px"] != [640, 480]
            or daten["renderzustand"]["fenstergroesse_px"] != [640, 480]):
        raise ValueError("Fixierter Live-Viewport veraendert: " + modell)
    for feld in ("frameabstand_p95_ms", "batch_median_ms",
                 "eingabe_bis_praesentierter_frame_ms"):
        wert = daten[feld]
        if wert is None or not math.isfinite(wert) or wert <= 0:
            raise ValueError("Fehlender/ungueltiger Live-Messwert: " + feld)
    if speicher:
        speicherreihe_pruefen(daten["rohwerte"]["speicher_zeitreihe"], dauer)


def vorhandene_liveberichte(dateien, wiederholungen):
    erwartet = {
        "%s_%s_%d" % (modell, optik, nummer): (modell, optik)
        for nummer in range(1, wiederholungen + 1)
        for modell in MODELLE for optik in ("standard", "schulung")
    }
    berichte = {}
    for datei in dateien:
        name = datei.stem
        if name not in erwartet or name in berichte:
            raise ValueError("Unbekannter oder doppelter Live-Bericht: " + str(datei))
        daten = json.loads(datei.read_text(encoding="utf-8"))
        live_pruefen(daten, *erwartet[name], 300, speicher=True)
        berichte[name] = (datei.resolve(), daten)
    return berichte


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--art", choices=("kern", "live"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wiederholungen", type=int, default=3)
    parser.add_argument("--vorhandene-live", nargs="+", type=Path, default=[],
                        help="Explizite gueltige Einzelberichte weiterverwenden; Rohdaten bleiben unveraendert")
    args = parser.parse_args(argv)
    if args.wiederholungen < 3:
        parser.error("Mindestens drei Wiederholungen erforderlich")
    if args.vorhandene_live and args.art != "live":
        parser.error("--vorhandene-live nur bei --art live")
    vorhandene = vorhandene_liveberichte(args.vorhandene_live, args.wiederholungen)
    manifest = referenzmanifest()
    args.output.mkdir(parents=True, exist_ok=False)
    schreiben(args.output / "umgebung.json", {
        "referenzcommit": REFERENZ, "start_utc": datetime.now(timezone.utc).isoformat(),
        "umgebung": umgebung(), "build": buildinventar(), "hardware": hardware(),
        "kommando": sys.argv, "referenzmanifest": manifest,
        "messwerkzeuge_sha256": {
            name: texthash(ROOT / "werkzeuge" / name)
            for name in ("migration_baseline.py", "migration_inventar.py",
                         "migration_vergleich.py", "benchmark_gui_live.py",
                         "benchmark_profil.py")
        },
        "hinweis": "Keine vollstaendige M1-Abnahme durch diesen Teillauf.",
    })
    if args.art == "kern":
        modelldaten = []
        for modell in MODELLE:
            daten = kernmessung(modell, args.wiederholungen)
            with (args.output / (modell + ".json")).open("x", encoding="utf-8") as stream:
                json.dump(daten, stream, ensure_ascii=False, indent=2,
                          default=serialisieren, allow_nan=False)
            modelldaten.append(daten)
            print("Kernbaseline: " + modell, flush=True)
        schreiben(args.output / "funktionsmessungen.json", funktionsmessungen(modelldaten))
    else:
        env = dict(os.environ, QT_QPA_PLATFORM="windows", PYTHONUTF8="1")
        renderzustaende = {}
        liveberichte = []
        for wiederholung in range(1, args.wiederholungen + 1):
            for modell in MODELLE:
                for optik in ("standard", "schulung"):
                    name = "%s_%s_%d" % (modell, optik, wiederholung)
                    ziel = (args.output / (name + ".json")).resolve()
                    if name in vorhandene:
                        ziel, bericht = vorhandene[name]
                        print("Live-Einzelbericht erneut geprueft: " + name, flush=True)
                    else:
                        cmd = live_kommando(modell, optik, ziel)
                        print("Live-Baseline startet: " + name, flush=True)
                        with (args.output / (name + ".log")).open("x", encoding="utf-8") as log:
                            subprocess.run(cmd, cwd=ROOT, env=env, stdout=log,
                                           stderr=subprocess.STDOUT, check=True, timeout=900)
                        bericht = json.loads(ziel.read_text(encoding="utf-8"))
                    live_pruefen(bericht, modell, optik, 300, speicher=True)
                    liveberichte.append({
                        "name": name, "datei": ziel.relative_to(ROOT).as_posix(),
                        "sha256": texthash(ziel),
                        "aus_vorherigem_lauf": name in vorhandene,
                    })
                    key = (modell, optik)
                    if key in renderzustaende:
                        vergleiche(renderzustaende[key], bericht["renderzustand"])
                    else:
                        renderzustaende[key] = bericht["renderzustand"]
                    referenzmanifest()
                    print("Live-Baseline geprueft: " + name, flush=True)
        schreiben(args.output / "liveberichte.json", {
            "berichte": liveberichte,
            "hinweis": "Explizit gepruefte Einzelberichte; kein Ersetzen ungueltiger Rohdaten.",
        })
    schreiben(args.output / "teillauf_abgeschlossen.json", {
        "art": args.art, "wiederholungen": args.wiederholungen,
        "m1_freigegeben": False,
        "hinweis": "Andere Pflichtszenarien und Einzelfunktionsbelege bleiben erforderlich.",
    })


if __name__ == "__main__":
    main()
