"""Reproduzierbare Hydrostatik- und Solverbenchmarks.

Aus dem Repository-Hauptverzeichnis starten:
    .venv\\Scripts\\python.exe werkzeuge\\benchmark_physik.py
    .venv\\Scripts\\python.exe werkzeuge\\benchmark_physik.py --solver
    .venv\\Scripts\\python.exe werkzeuge\\benchmark_physik.py --bodyfixed
"""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os
import platform
import statistics
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from segelphysik.core.auftrieb import als_bindung, baue_kraftfunktion
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig, lade_physik
from segelphysik.core.statisch_robust import loese_robust
from segelphysik.core.volumen_union import volumen_schwerpunkt_union
from segelphysik.gui.baum import aktive_blaetter, finde, welt_aus_konfig


POSES = ((-0.14, 0.15), (-0.145, 0.16), (-0.14, 0.17),
         (-0.1435, 0.171))


def _perzentil_95(werte):
    sortiert = sorted(werte)
    return sortiert[min(len(sortiert) - 1,
                        int(0.95 * (len(sortiert) - 1) + 0.5))]


def _statistik(werte):
    return {
        "median_s": statistics.median(werte),
        "p95_s": _perzentil_95(werte),
        "werte_s": werte,
    }


def _koerper_und_konfiguration(name):
    konfiguration = lade_konfig(os.path.join(ROOT, "konfigurationen"))
    physik = lade_physik(os.path.join(ROOT, "konfigurationen"))
    welt = welt_aus_konfig(konfiguration)
    knoten = finde(welt, name)
    if knoten is None:
        raise ValueError("Unbekannter Benchmark-Körper: %s" % name)
    koerper, _ = baue_summenkoerper(
        konfiguration, name, aktive_blaetter=aktive_blaetter(knoten))
    return konfiguration, physik, koerper


def benchmark(args):
    konfiguration, physik, koerper = _koerper_und_konfiguration(args.scene)
    bindung = als_bindung(koerper)
    grenzen_min = np.min(
        [punkte.min(axis=0) for punkte, _ in bindung.blatt_meshes], axis=0)
    grenzen_max = np.max(
        [punkte.max(axis=0) for punkte, _ in bindung.blatt_meshes], axis=0)
    laenge = float(np.linalg.norm(grenzen_max - grenzen_min))
    gesamtvolumen, _ = volumen_schwerpunkt_union(bindung.blatt_meshes)
    reference = baue_kraftfunktion(
        koerper, rho_w=konfiguration.wasser_dichte(),
        g=physik.g_m_pro_s2, pfad="exakt_union")
    referenzwerte = [reference((z, phi, 0.0)) for z, phi in POSES]
    pfade = ["voxel", "exakt_union"]
    if args.bodyfixed:
        pfade.append("voxel_koerperfest")

    ergebnisse = {}
    for pfad in pfade:
        vorbereitung = []
        auswertungen = []
        abweichungen = []
        solverzeiten = []
        solverergebnisse = []
        for _ in range(args.repeats):
            start = time.perf_counter()
            funktion = baue_kraftfunktion(
                koerper, rho_w=konfiguration.wasser_dichte(),
                g=physik.g_m_pro_s2,
                aufloesung=physik.voxel_aufloesung_m, pfad=pfad)
            vorbereitung.append(time.perf_counter() - start)
            aktuell = []
            for (z, phi), referenz in zip(POSES, referenzwerte):
                start = time.perf_counter()
                wert = funktion((z, phi, 0.0))
                auswertungen.append(time.perf_counter() - start)
                aktuell.append(wert)
                abweichungen.append({
                    "pose_z_phi": [z, phi],
                    "volumen_rel_zum_gesamtvolumen": (
                        abs(wert.V_tauch - referenz.V_tauch) / gesamtvolumen),
                    "schwerpunkt_m": float(
                        ((wert.K.as_array() - referenz.K.as_array()) ** 2)
                        .sum() ** 0.5),
                    "auftrieb_rel": abs(wert.F_A.z - referenz.F_A.z)
                    / max(abs(referenz.F_A.z),
                          0.01 * koerper.masse * physik.g_m_pro_s2),
                    "moment_rel": abs(wert.M.x - referenz.M.x)
                    / max(abs(referenz.M.x),
                          0.01 * koerper.masse * physik.g_m_pro_s2 * laenge),
                })
            if args.solver:
                start = time.perf_counter()
                try:
                    loesung = loese_robust(
                        funktion, koerper.masse, g=physik.g_m_pro_s2,
                        start=(-0.14, 0.15))
                except ValueError as fehler:
                    solverergebnisse.append({"fehler": str(fehler)})
                else:
                    solverergebnisse.append({
                        "z_m": loesung["z"],
                        "phi_grad": loesung["phi"] * 180.0 / 3.141592653589793,
                        "restkraft_N": loesung["restkraft"],
                        "restmoment_Nm": loesung["restmoment"],
                        "iterationen": loesung["iterationen"],
                    })
                solverzeiten.append(time.perf_counter() - start)
        ergebnisse[pfad] = {
            "vorbereitung": _statistik(vorbereitung),
            "poseauswertung": _statistik(auswertungen),
            "maximale_abweichung": {
                schluessel: max(wert[schluessel] for wert in abweichungen)
                for schluessel in (
                    "volumen_rel_zum_gesamtvolumen", "schwerpunkt_m",
                    "auftrieb_rel", "moment_rel")
            },
            "poseabweichungen": abweichungen,
        }
        maxima = ergebnisse[pfad]["maximale_abweichung"]
        ergebnisse[pfad]["genauigkeit_bestanden"] = (
            maxima["volumen_rel_zum_gesamtvolumen"] <= 0.01
            and maxima["schwerpunkt_m"] <= 0.01 * laenge
            and maxima["auftrieb_rel"] <= 0.01
            and maxima["moment_rel"] <= 0.01)
        if args.solver:
            ergebnisse[pfad]["solver"] = {
                "laufzeit": _statistik(solverzeiten),
                "ergebnisse": solverergebnisse,
            }

    if args.solver:
        referenz_solver = ergebnisse["exakt_union"]["solver"]["ergebnisse"][0]
        if "fehler" not in referenz_solver:
            kraft_near_zero = 0.01 * koerper.masse * physik.g_m_pro_s2
            moment_near_zero = kraft_near_zero * laenge
            for pfad in pfade:
                vergleich = []
                for loesung in ergebnisse[pfad]["solver"]["ergebnisse"]:
                    if "fehler" in loesung:
                        vergleich.append({"fehler": loesung["fehler"]})
                        continue
                    abweichung = {
                        "z_rel_referenzlaenge": abs(
                            loesung["z_m"] - referenz_solver["z_m"]) / laenge,
                        "winkel_grad": abs(
                            loesung["phi_grad"]
                            - referenz_solver["phi_grad"]),
                        "restkraft_delta_N": abs(
                            loesung["restkraft_N"]
                            - referenz_solver["restkraft_N"]),
                        "restmoment_delta_Nm": abs(
                            loesung["restmoment_Nm"]
                            - referenz_solver["restmoment_Nm"]),
                    }
                    abweichung["restkraft_rel"] = (
                        loesung["restkraft_N"] / kraft_near_zero)
                    abweichung["restmoment_rel"] = (
                        loesung["restmoment_Nm"] / moment_near_zero)
                    abweichung["bestanden"] = (
                        abweichung["z_rel_referenzlaenge"] <= 0.01
                        and abweichung["winkel_grad"] <= 1.0
                        and abweichung["restkraft_rel"] <= 1.0
                        and abweichung["restmoment_rel"] <= 1.0)
                    vergleich.append(abweichung)
                ergebnisse[pfad]["solver"]["abweichung_zur_exakten_referenz"] \
                    = vergleich

    ausgabe = {
        "umgebung": {
            "python": sys.version,
            "plattform": platform.platform(),
            "prozessor": platform.processor(),
            "numpy": __import__("numpy").__version__,
            "manifold3d": version("manifold3d"),
            "koerper": args.scene,
            "masse_kg": koerper.masse,
            "gesamtvolumen_m3": gesamtvolumen,
            "referenzlaenge_m": laenge,
            "rasterweite_m": physik.voxel_aufloesung_m,
            "wiederholungen": args.repeats,
            "posen_z_phi": POSES,
            "genauigkeitsgrenzen": {
                "volumen_rel_gesamt": 0.01,
                "winkel_grad": 1.0,
                "andere_groessen_rel": 0.01,
                "schwerpunkt_near_zero_m": 0.01 * laenge,
                "kraft_near_zero_N": 0.01 * koerper.masse * physik.g_m_pro_s2,
                "moment_near_zero_Nm": (
                    0.01 * koerper.masse * physik.g_m_pro_s2 * laenge),
            },
        },
        "pfade": ergebnisse,
    }
    print(json.dumps(ausgabe, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default="yacht1")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--solver", action="store_true")
    parser.add_argument(
        "--bodyfixed", action="store_true",
        help="Körperfestes Raster mit einmaliger Vorbereitung messen")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats muss mindestens 1 sein")
    benchmark(args)


if __name__ == "__main__":
    main()
