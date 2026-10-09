"""Interaktive Echtzeit-GUI (v0.3a).

Aufruf:  python gui.py [--backend taichi|numpy] [--full] [--frames N]

Steuerung im Fenster:
  g / G      Gravitation +1 / -1 m/s^2
  w / W      Wind +1 / -1 m/s
  Leertaste  Pause
  r          Reset
  s          Kugel einspawnen
  q          Ende
"""
import argparse
import json
import os
import sys
import time

import numpy as np


def build_app(backend="taichi", small=True):
    from segelphysik.core.app import SimulationApp

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "segelphysik", "config.json")) as f:
        data = json.load(f)
    if small:
        data["basin"] = {"lx": 8.0, "ly": 8.0, "H": 9.0}
        data["water"]["depth"] = 3.0
    app = SimulationApp(config_dict=data)
    if backend == "taichi":
        try:
            from segelphysik.fluid import TaichiSphWater
            if TaichiSphWater is None:
                raise ImportError("taichi nicht verfuegbar")
            app.fluid_factory = TaichiSphWater
            app._build()
            print(f"[v0.3a] Taichi-Backend: {app.sph.backend}  "
                  f"({app.sph.n_particles} Partikel)")
        except Exception as e:
            print(f"[v0.3a] Taichi nicht verfuegbar ({e}) -> NumPy-Referenz")
    else:
        print(f"[v0.3a] NumPy-Referenz ({app.sph.n_particles} Partikel)")
    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="taichi", choices=["taichi", "numpy"])
    ap.add_argument("--full", action="store_true", help="Default-Becken 10x10x3")
    ap.add_argument("--frames", type=int, default=0, help="0 = bis Fenster zu")
    args = ap.parse_args()

    from segelphysik.core.render import HeightFieldSurface
    from segelphysik.render.vista import PyVistaRenderer

    app = build_app(args.backend, small=not args.full)
    app.spawn_sphere(radius=1.0, density=300.0, position=(0, 0, 2.5))
    app.spawn_box(edges=(2.0, 2.0, 2.0), density=700.0, position=(2.5, 0, 1.5))

    cell_target = 1.5 * float(app.cfg.dx)
    nx = max(8, int(round(app.cfg.basin['lx'] / cell_target)))
    ny = max(8, int(round(app.cfg.basin['ly'] / cell_target)))
    print(f'[v0.3a] Oberflaechenraster: {nx}x{ny} Zellen (~1.5*dx)')
    surf = HeightFieldSurface(app.cfg.basin, nx=nx, ny=ny)
    ren = PyVistaRenderer(app, nx=nx, ny=ny)
    ren.attach(surf)
    p = ren.build()
    state = {"paused": False, "quit": False}

    def on_key(key):
        if key == "g":
            app.set_g(app.cfg.g + 1.0)
        elif key == "G":
            app.set_g(max(app.cfg.g - 1.0, 0.0))
        elif key == "w":
            app.set_wind(app.world.environment.wind.speed + 1.0,
                         app.world.environment.wind.azimuth_deg)
        elif key == "W":
            app.set_wind(app.world.environment.wind.speed - 1.0,
                         app.world.environment.wind.azimuth_deg)
        elif key == "space":
            state["paused"] = not state["paused"]
        elif key == "r":
            app.reset()
        elif key == "s":
            app.spawn_sphere(radius=1.0, density=300.0,
                             position=(float(np.random.uniform(-2, 2)), 0.0, 2.5))
        elif key == "q":
            state["quit"] = True

    for k in ("g", "G", "w", "W", "space", "r", "s", "q"):
        p.add_key_event(k, lambda k=k: on_key(k))

    p.show(interactive_update=True, auto_close=False)
    t0 = time.perf_counter(); frames = 0
    try:
        while not state["quit"]:
            if not state["paused"]:
                app.step_frame(1.0 / 60.0)
            pos = (app.sph.get_state()[0] if hasattr(app.sph, "get_state")
                   else app.sph.pos[:app.sph.n_real])
            surf.update(pos)
            ren.update(surf)
            p.update()
            frames += 1
            if args.frames and frames >= args.frames:
                break
    except KeyboardInterrupt:
        pass
    wall = time.perf_counter() - t0
    if wall > 0:
        print(f"{frames} Frames in {wall:.1f} s -> {frames/wall:.1f} FPS")
    p.close()


if __name__ == "__main__":
    sys.exit(main())
