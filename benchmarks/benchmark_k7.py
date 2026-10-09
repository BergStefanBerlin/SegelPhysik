"""K7-Benchmark: >= 20.000 SPH-Partikel + >= 10 Koerper bei >= 30 FPS.

Manuelles Skript ausserhalb der CI (GitHub-Runner haben keine dedizierte
GPU). Benchmark-Konfiguration: dx = 0,24 m -> ~21.700 Partikel (Plan-Fix
fuer K7; h = 1,3*dx = 0,312 m, CFL-Grenze ~22,5 m/s).

Aufruf:  python benchmarks/benchmark_k7.py [--frames 300]
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from segelphysik.core.app import SimulationApp      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=300)
    args = ap.parse_args()

    here = os.path.dirname(__file__)
    with open(os.path.join(here, "..", "segelphysik", "config.json")) as f:
        data = json.load(f)
    data["sph"]["dx"] = 0.24
    app = SimulationApp(config_dict=data)
    for i in range(10):
        x = -3.0 + 0.6 * i
        app.spawn_sphere(radius=1.0, density=500.0,
                         position=(x, 0.0, 3.0 + 0.5 * (i % 3)))
    n = app.sph.n_real
    print(f"Partikel: {n}  Koerper: {len(app.world.bodies)}")

    t0 = time.perf_counter()
    for _ in range(args.frames):
        app.step_frame(1.0 / 60.0)
    wall = time.perf_counter() - t0
    fps = args.frames / wall
    print(f"{args.frames} Frames in {wall:.1f} s  ->  {fps:.1f} FPS")
    ok = n >= 20000 and len(app.world.bodies) >= 10 and fps >= 30.0
    print("K7:", "BESTANDEN" if ok else "NICHT BESTANDEN")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
