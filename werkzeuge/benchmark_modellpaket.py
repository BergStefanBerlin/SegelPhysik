"""Gepaartes B-03-Performancegate für Legacy- und Paketfabrik.

Aufruf aus dem Repository-Hauptverzeichnis:
    .venv\\Scripts\\python.exe werkzeuge\\benchmark_modellpaket.py
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segelphysik.core.fabriken import baue_modellpaket, baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.modell_lader import lade_modellkatalog


def _argumente():
    parser = argparse.ArgumentParser(
        description="Misst B-03 gepaart für ein Modellpaket.")
    parser.add_argument("--modell", default="yacht1")
    parser.add_argument("--paare", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--bootstrap-resamples", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=9421)
    argumente = parser.parse_args()
    if (argumente.paare < 1 or argumente.warmups < 0
            or argumente.bootstrap_resamples < 1):
        parser.error("Paare und Bootstrap müssen positiv, Warm-ups nichtnegativ sein")
    return argumente


def main():
    argumente = _argumente()
    konfiguration = lade_konfig(ROOT / "konfigurationen")
    katalog = lade_modellkatalog(
        ROOT / "code" / "modelle",
        konfiguration.materialien_blocks)
    manifest = next(
        (eintrag for eintrag in katalog
         if eintrag.id == argumente.modell),
        None,
    )
    if manifest is None:
        raise ValueError("Unbekanntes Benchmark-Modell: %s" % argumente.modell)

    legacy_zeit = []
    paket_zeit = []
    verhaeltnisse = []

    def messen(pfad):
        start = time.perf_counter()
        if pfad == "legacy":
            baue_summenkoerper(
                konfiguration, argumente.modell,
                eintrag=konfiguration.summenkoerper[argumente.modell])
        else:
            baue_modellpaket(konfiguration, manifest.paketwurzel)
        return time.perf_counter() - start

    for _ in range(argumente.warmups):
        messen("legacy")
        messen("paket")
    for index in range(argumente.paare):
        reihenfolge = (
            ("legacy", "paket") if index % 2 == 0
            else ("paket", "legacy"))
        werte = {pfad: messen(pfad) for pfad in reihenfolge}
        legacy_zeit.append(werte["legacy"])
        paket_zeit.append(werte["paket"])
        verhaeltnisse.append(werte["paket"] / werte["legacy"])

    bootstrap = np.median(
        np.random.default_rng(argumente.seed).choice(
            np.asarray(verhaeltnisse),
            (argumente.bootstrap_resamples, argumente.paare),
            replace=True,
        ),
        axis=1,
    )
    ausgabe = {
        "python": platform.python_version(),
        "plattform": platform.platform(),
        "messaufbau": {
            "modell": argumente.modell,
            "warmups_je_pfad": argumente.warmups,
            "paare": argumente.paare,
            "reihenfolge": "abwechselnd Legacy/Paket und Paket/Legacy",
            "legacy": (
                "baue_summenkoerper(konfiguration, modell, "
                "eintrag=konfiguration.summenkoerper[modell])"),
            "kandidat": "baue_modellpaket(konfiguration, manifest.paketwurzel)",
            "bootstrap_resamples": argumente.bootstrap_resamples,
            "bootstrap_seed": argumente.seed,
        },
        "auswertung": {
            "legacy_median_s": statistics.median(legacy_zeit),
            "kandidat_median_s": statistics.median(paket_zeit),
            "median_verhaeltnis_kandidat_zu_legacy": statistics.median(
                verhaeltnisse),
            "bootstrap_95_prozent_intervall_median_verhaeltnis": [
                float(wert) for wert in np.quantile(bootstrap, [0.025, 0.975])
            ],
            "gate_bestanden": bool(
                np.quantile(bootstrap, 0.975) <= 1.0),
        },
        "rohwerte_legacy_s": legacy_zeit,
        "rohwerte_kandidat_s": paket_zeit,
        "paarverhaeltnisse_kandidat_zu_legacy": verhaeltnisse,
    }
    print(json.dumps(ausgabe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
