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
import random
import statistics
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from segelphysik.core.auftrieb import (
    als_bindung, baue_kraftfunktion, baue_kraftfunktion_6dof,
)
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig, lade_physik
from segelphysik.core.dynamik_6dof import Zustand6DOF, schritt
from segelphysik.core.auftrieb import Auftriebsergebnis
from segelphysik.core.dynamik_6dof import quaternion_matrix
from segelphysik.core.physik_backend import (
    BackendNichtVerfuegbar, OpenCLVoxelHydrostatik,
)
from segelphysik.core.voxelmodell import KoerperfestesVoxelmodell
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


def _quaternion_multiplizieren(a, b):
    w, x, y, z = a
    p, q, r, s = b
    return (
        w * p - x * q - y * r - z * s,
        w * q + x * p + y * s - z * r,
        w * r - x * s + y * p + z * q,
        w * s + x * r - y * q + z * p,
    )


def _benchmark_6dof(koerper, konfiguration, physik, wiederholungen):
    identitaet = (1.0, 0.0, 0.0, 0.0)
    roll = (np.cos(0.075), np.sin(0.075), 0.0, 0.0)
    nick = (np.cos(0.05), 0.0, np.sin(0.05), 0.0)
    gier = (np.cos(0.1), 0.0, 0.0, np.sin(0.1))
    posen = (
        ("neutral", (0.0, 0.0, -0.14), identitaet),
        ("roll", (0.0, 0.0, -0.14), roll),
        ("nick", (0.0, 0.0, -0.14), nick),
        ("gier", (0.0, 0.0, -0.14), gier),
        ("kombiniert", (0.0, 0.0, -0.14),
         _quaternion_multiplizieren(
             _quaternion_multiplizieren(roll, nick), gier)),
    )
    funktion = baue_kraftfunktion_6dof(
        koerper, rho_w=konfiguration.wasser_dichte(),
        g=physik.g_m_pro_s2, pfad="exakt_union")
    messungen = {}
    for name, position, quaternion in posen:
        posezeiten = []
        schrittzeiten = []
        ergebnis = None
        for _ in range(wiederholungen):
            start = time.perf_counter()
            ergebnis = funktion((position, quaternion))
            posezeiten.append(time.perf_counter() - start)
            zustand = Zustand6DOF(position=position, quaternion=quaternion)
            start = time.perf_counter()
            ende, _ = schritt(
                zustand, funktion, koerper.masse,
                koerper.traegheitstensor, physik.dt_s,
                physik.g_m_pro_s2)
            schrittzeiten.append(time.perf_counter() - start)
            if (not np.isfinite(ende.position).all()
                    or not np.isfinite(ende.quaternion).all()):
                raise RuntimeError(
                    "6-DOF-Benchmark lieferte einen nicht-endlichen Zustand")
        messungen[name] = {
            "position": position,
            "quaternion": quaternion,
            "volumen_m3": ergebnis.V_tauch,
            "schwerpunkt_welt_m": ergebnis.K.as_array().tolist(),
            "kraft_welt_N": ergebnis.F_A.as_array().tolist(),
            "moment_welt_Nm": ergebnis.M.as_array().tolist(),
            "poseauswertung": _statistik(posezeiten),
            "vollstaendiger_6dof_schritt": _statistik(schrittzeiten),
        }
    return messungen


def _bootstrap_median_ci(werte, resamples=10_000, seed=1202):
    generator = random.Random(seed)
    medians = []
    for _ in range(resamples):
        sample = [werte[generator.randrange(len(werte))]
                  for _ in range(len(werte))]
        medians.append(statistics.median(sample))
    medians.sort()
    return {
        "resamples": resamples,
        "unteres_2_5_prozent": medians[int(0.025 * (resamples - 1))],
        "oberes_97_5_prozent": medians[int(0.975 * (resamples - 1))],
    }


def _benchmark_cpu_gpu_paar(koerper, konfiguration, physik, anzahl_paare,
                            schritte_pro_paar):
    physik_koerper = koerper
    koerper = als_bindung(koerper)
    aufloesung = physik.voxel_aufloesung_m
    cpu_start = time.perf_counter()
    raster = KoerperfestesVoxelmodell(
        koerper.blatt_meshes, aufloesung)
    cpu_vorbereitung_s = time.perf_counter() - cpu_start
    try:
        gpu_start = time.perf_counter()
        gpu = OpenCLVoxelHydrostatik.oeffnen(
            raster.zentren_lokal, aufloesung ** 3)
        gpu_vorbereitung_s = time.perf_counter() - gpu_start
    except BackendNichtVerfuegbar as fehler:
        return {
            "abgeschlossen": False,
            "grund": str(fehler),
            "cpu_vorbereitung_s": cpu_vorbereitung_s,
        }

    grenzen_min = raster.zentren_lokal.min(axis=0)
    grenzen_max = raster.zentren_lokal.max(axis=0)
    rho_w = konfiguration.wasser_dichte()
    gravity = physik.g_m_pro_s2
    masse = float(physik_koerper.masse)
    traegheit = physik_koerper.traegheitstensor
    r_s = np.asarray(getattr(
        physik_koerper, "r_S", koerper.r_S), dtype=np.float64)

    def cpu_kraft(lage, v=None, omega=None):
        position = np.asarray(lage[0], dtype=np.float64)
        rotation = quaternion_matrix(lage[1])
        volumen, schwerpunkt = raster.auswerten_6dof(position, lage[1])
        kraft = np.array((0.0, 0.0, rho_w * gravity * volumen))
        moment = np.cross(
            schwerpunkt - (rotation @ r_s + position), kraft)
        return Auftriebsergebnis(volumen, schwerpunkt, kraft, moment)

    def gpu_kraft(lage, v=None, omega=None):
        position = np.asarray(lage[0], dtype=np.float64)
        rotation = quaternion_matrix(lage[1])
        volumen, schwerpunkt = gpu.auswerten_6dof(
            rotation, position, grenzen_min, grenzen_max)
        kraft = np.array((0.0, 0.0, rho_w * gravity * volumen))
        moment = np.cross(
            schwerpunkt - (rotation @ r_s + position), kraft)
        return Auftriebsergebnis(volumen, schwerpunkt, kraft, moment)

    identitaet = (1.0, 0.0, 0.0, 0.0)
    roll = (np.cos(0.075), np.sin(0.075), 0.0, 0.0)
    nick = (np.cos(0.05), 0.0, np.sin(0.05), 0.0)
    gier = (np.cos(0.1), 0.0, 0.0, np.sin(0.1))
    poses = (
        ((0.0, 0.0, -0.14), identitaet),
        ((0.0, 0.0, -0.14), roll),
        ((0.0, 0.0, -0.14), nick),
        ((0.0, 0.0, -0.14), gier),
        ((0.0, 0.0, -0.14),
         _quaternion_multiplizieren(
             _quaternion_multiplizieren(roll, nick), gier)),
    )
    genaue_kraft = baue_kraftfunktion_6dof(
        koerper, rho_w=rho_w, g=gravity, pfad="exakt_union")
    genauigkeit = []
    exakt_werte = [genaue_kraft(pose) for pose in poses]
    volumen_skala = max(abs(wert.V_tauch) for wert in exakt_werte)
    kraft_skala = max(
        float(np.linalg.norm(wert.F_A.as_array()))
        for wert in exakt_werte)
    moment_skala = max(
        float(np.linalg.norm(wert.M.as_array()))
        for wert in exakt_werte)
    referenzlaenge = float(np.linalg.norm(np.ptp(
        np.concatenate([punkte for punkte, _ in koerper.blatt_meshes]),
        axis=0)))
    if kraft_skala <= np.finfo(np.float64).tiny:
        kraft_skala = max(physik_koerper.masse * gravity, 1e-12)
    if moment_skala <= np.finfo(np.float64).tiny:
        moment_skala = max(
            physik_koerper.masse * gravity * referenzlaenge, 1e-12)
    for pose, exakt in zip(poses, exakt_werte):
        cpu = cpu_kraft(pose)
        gpu_result = gpu_kraft(pose)
        volumen_skala_pose = max(abs(exakt.V_tauch), volumen_skala, 1e-12)
        kraft_skala_pose = max(
            float(np.linalg.norm(exakt.F_A.as_array())), kraft_skala, 1e-12)
        moment_skala_pose = max(
            float(np.linalg.norm(exakt.M.as_array())), moment_skala, 1e-12)
        genauigkeit.append({
            "pose": [list(pose[0]), list(pose[1])],
            "cpu_volumen_rel": (
                abs(cpu.V_tauch - exakt.V_tauch) / volumen_skala_pose),
            "gpu_volumen_rel": (
                abs(gpu_result.V_tauch - exakt.V_tauch)
                / volumen_skala_pose),
            "cpu_kraft_rel": (
                np.linalg.norm(cpu.F_A.as_array() - exakt.F_A.as_array())
                / kraft_skala_pose),
            "gpu_kraft_rel": (
                np.linalg.norm(gpu_result.F_A.as_array()
                               - exakt.F_A.as_array()) / kraft_skala_pose),
            "cpu_moment_rel": (
                np.linalg.norm(cpu.M.as_array() - exakt.M.as_array())
                / moment_skala_pose),
            "gpu_moment_rel": (
                np.linalg.norm(gpu_result.M.as_array()
                               - exakt.M.as_array()) / moment_skala_pose),
            "gpu_cpu_schwerpunkt_abstand_m": float(np.linalg.norm(
                gpu_result.K.as_array() - cpu.K.as_array())),
        })

    generator = random.Random(6102)
    gepaarte_verbesserungen = []
    cpu_p95 = []
    gpu_p95 = []
    cpu_zeit = []
    gpu_zeit = []
    gpu_schritte = []
    cpu_schritte = []
    for funktion in (cpu_kraft, gpu_kraft):
        start_pose = poses[0]
        for _ in range(5):
            schritt(
                Zustand6DOF(position=start_pose[0],
                            quaternion=start_pose[1]),
                funktion, masse, traegheit, physik.dt_s, gravity)
    for paar in range(anzahl_paare):
        reihenfolge = ("cpu", "gpu") if paar % 2 == 0 else ("gpu", "cpu")
        laufzeiten = {"cpu": [], "gpu": []}
        for pfad in reihenfolge:
            funktion = cpu_kraft if pfad == "cpu" else gpu_kraft
            messwerte = cpu_schritte if pfad == "cpu" else gpu_schritte
            for index in range(schritte_pro_paar):
                position, quaternion = poses[generator.randrange(len(poses))]
                zustand = Zustand6DOF(
                    position=position, quaternion=quaternion)
                start = time.perf_counter()
                ende, _ergebnis = schritt(
                    zustand, funktion, masse, traegheit,
                    physik.dt_s, gravity)
                dauer = time.perf_counter() - start
                if (not np.isfinite(ende.position).all()
                        or not np.isfinite(ende.quaternion).all()):
                    raise RuntimeError(
                        "%s lieferte einen nicht-endlichen 6-DOF-Schritt"
                        % pfad.upper())
                laufzeiten[pfad].append(dauer)
                messwerte.append(dauer)
        p95_cpu = _perzentil_95(laufzeiten["cpu"])
        p95_gpu = _perzentil_95(laufzeiten["gpu"])
        cpu_p95.append(p95_cpu)
        gpu_p95.append(p95_gpu)
        cpu_zeit.append(statistics.median(laufzeiten["cpu"]))
        gpu_zeit.append(statistics.median(laufzeiten["gpu"]))
        gepaarte_verbesserungen.append(
            (p95_cpu - p95_gpu) / p95_cpu if p95_cpu else 0.0)
    ci = _bootstrap_median_ci(gepaarte_verbesserungen)
    maxima = {
        schluessel: max(probe[schluessel] for probe in genauigkeit)
        for schluessel in (
            "cpu_volumen_rel", "gpu_volumen_rel", "cpu_kraft_rel",
            "gpu_kraft_rel", "cpu_moment_rel", "gpu_moment_rel",
            "gpu_cpu_schwerpunkt_abstand_m")
    }
    return {
        "abgeschlossen": True,
        "geraet": gpu.name,
        "treiber": gpu.driver_version,
        "gpu_speicher_bytes": gpu.global_memory_bytes,
        "pyopencl_version": version("pyopencl"),
        "cpu_voxel_vorbereitung_s": cpu_vorbereitung_s,
        "gpu_voxel_und_buffer_vorbereitung_s": gpu_vorbereitung_s,
        "rasterzentren": len(raster.zentren_lokal),
        "voxelvolumen_m3": aufloesung ** 3,
        "poseanzahl": len(poses),
        "schritte_pro_backend_und_paar": schritte_pro_paar,
        "messpaare": anzahl_paare,
        "cpu_p95_s_pro_paar": cpu_p95,
        "gpu_p95_s_pro_paar": gpu_p95,
        "cpu_median_s_pro_paar": cpu_zeit,
        "gpu_median_s_pro_paar": gpu_zeit,
        "cpu_schrittstatistik": _statistik(cpu_schritte),
        "gpu_schrittstatistik": _statistik(gpu_schritte),
        "paarweise_p95_verbesserung": gepaarte_verbesserungen,
        "verbesserung_median": statistics.median(gepaarte_verbesserungen),
        "verbesserung_95_prozent_ci_median": ci,
        "gpu_vorteil_10_prozent_gate": ci["unteres_2_5_prozent"] >= 0.10,
        "genauigkeitsmaxima_gegen_exakte_union": maxima,
        "genauigkeit_max_rel_gate_1_prozent": all(
            maxima[name] <= 0.01 for name in (
                "cpu_volumen_rel", "gpu_volumen_rel", "cpu_kraft_rel",
                "gpu_kraft_rel", "cpu_moment_rel", "gpu_moment_rel")),
        "poses": genauigkeit,
        "einschraenkung": (
            "Isolierter CPU-Physikvergleich ohne parallele Renderlast; "
            "keine Produktionsfreigabe nach Phase 6/9."),
    }


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
                        "kraftauswertungen": loesung["kraftauswertungen"],
                        "wiederverwendete_kraftwerte": loesung[
                            "wiederverwendete_kraftwerte"],
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
    if args.sixdof:
        ausgabe["6dof_exakt_union"] = _benchmark_6dof(
            koerper, konfiguration, physik, args.repeats)
    if args.gpu_pairs:
        ausgabe["cpu_gpu_voxel_6dof"] = _benchmark_cpu_gpu_paar(
            koerper, konfiguration, physik,
            args.gpu_pairs, args.gpu_steps)
    print(json.dumps(ausgabe, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default="yacht1")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--solver", action="store_true")
    parser.add_argument(
        "--bodyfixed", action="store_true",
        help="Körperfestes Raster mit einmaliger Vorbereitung messen")
    parser.add_argument(
        "--sixdof", action="store_true",
        help="Beliebige Quaternionposen und vollständige exakte 6-DOF-Schritte messen")
    parser.add_argument(
        "--gpu-pairs", type=int, default=0,
        help="Gepaarter OpenCL-/CPU-Voxelvergleich (10 bis 30 Messpaare)")
    parser.add_argument(
        "--gpu-steps", type=int, default=20,
        help="6-DOF-Schritte je Backend und Messpaar für --gpu-pairs")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats muss mindestens 1 sein")
    if args.gpu_pairs and not 10 <= args.gpu_pairs <= 30:
        parser.error("--gpu-pairs muss zwischen 10 und 30 liegen")
    if args.gpu_steps < 10:
        parser.error("--gpu-steps muss mindestens 10 betragen")
    benchmark(args)


if __name__ == "__main__":
    main()
