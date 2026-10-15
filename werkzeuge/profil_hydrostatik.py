"""Profiling einer exakten Union-Auswertung (R-5).

    .venv\\Scripts\\python.exe werkzeuge\\profil_hydrostatik.py
"""
from __future__ import annotations

import cProfile
import os
import pstats
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from benchmark_physik import _koerper_und_konfiguration  # noqa: E402
from segelphysik.core.auftrieb import baue_kraftfunktion_6dof  # noqa: E402
from segelphysik.core.dynamik_6dof import Zustand6DOF  # noqa: E402


def main():
    koerper = _koerper_und_konfiguration("yacht1")[2]
    funktion = baue_kraftfunktion_6dof(koerper, pfad="exakt_union")
    lage = (np.array([0.0, 0.0, -0.1435]),
            np.array([np.cos(0.08), np.sin(0.08), 0.0, 0.0]))
    funktion(lage)
    n = 50
    start = time.perf_counter()
    for _ in range(n):
        funktion(lage)
    print("Auswertung: %.3f ms" % (1000 * (time.perf_counter() - start) / n))
    profil = cProfile.Profile()
    profil.enable()
    for _ in range(n):
        funktion(lage)
    profil.disable()
    pstats.Stats(profil).sort_stats("cumulative").print_stats(14)


if __name__ == "__main__":
    main()
