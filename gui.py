"""Interaktive Echtzeit-GUI (v0.3b).

Aufruf:  python gui.py [--backend taichi|numpy] [--full] [--frames N]
                      [--no-depth-color]

Steuerung im Fenster:
  g / G      Gravitation +1 / -1 m/s^2
  w / W      Wind +1 / -1 m/s
  Leertaste  Pause
  r          Reset
  s          Kugel einspawnen (Zufallsposition)
  n          Spawn-Typ umschalten (Kugel <-> Box)
  Linksklick Koerper an Klickposition einspawnen (Spec K8)
  q          Ende

Neu in v0.3b: Klick-Spawning (K8), RTF-/FPS-Anzeige im HUD,
Tiefenfaerbung der Wasseroberflaeche.
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
            print(f"[v0.3b] Taichi-Backend: {app.sph.backend}  "
                  f"({app.sph.n_particles} Partikel)")
        except Exception as e:
            print(f"[v0.3b] Taichi nicht verfuegbar ({e}) -> NumPy-Referenz")
    else:
        print(f"[v0.3b] NumPy-Referenz ({app.sph.n_particles} Partikel)")
    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="taichi", choices=["taichi", "numpy"])
    ap.add_argument("--full", action="store_true", help="Default-Becken 10x10x3")
    ap.add_argument("--frames", type=int, default=0, help="0 = bis Fenster zu")
    ap.add_argument("--no-depth-color", action="store_true",
                    help="Oberflaeche einfarbig statt Tiefenfaerbung")
    args = ap.parse_args()

    from segelphysik.core.render import HeightFieldSurface
    from segelphysik.render.vista import PyVistaRenderer

    app = build_app(args.backend, small=not args.full)
    app.spawn_sphere(radius=1.0, density=300.0, position=(0, 0, 2.5))
    app.spawn_box(edges=(2.0, 2.0, 2.0), density=700.0, position=(2.5, 0, 1.5))

    cell_target = 1.5 * float(app.cfg.dx)
    nx = max(8, int(round(app.cfg.basin['lx'] / cell_target)))
    ny = max(8, int(round(app.cfg.basin['ly'] / cell_target)))
    print(f'[v0.3b] Oberflaechenraster: {nx}x{ny} Zellen (~1.5*dx)')
    surf = HeightFieldSurface(app.cfg.basin, nx=nx, ny=ny)
    ren = PyVistaRenderer(app, nx=nx, ny=ny,
                          color_by_depth=not args.no_depth_color)
    ren.attach(surf)
    p = ren.build()
    state = {"paused": False, "quit": False, "kind": "sphere"}

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
        elif key == "n":
            state["kind"] = "box" if state["kind"] == "sphere" else "sphere"
            print(f"[v0.3b] Spawn-Typ: {state['kind']}")
        elif key == "q":
            state["quit"] = True

    for k in ("g", "G", "w", "W", "space", "r", "s", "n", "q"):
        p.add_key_event(k, lambda k=k: on_key(k))

    # ---- Klick-Spawning (Spec K8) ----
    def on_click(pos):
        if not pos:
            return
        target = ren.screen_to_water(pos[0], pos[1])
        if target is None:
            return
        try:
            if state["kind"] == "sphere":
                app.spawn_sphere(radius=1.0, density=300.0,
                                 position=(target[0], target[1], 2.5))
            else:
                app.spawn_box(edges=(2.0, 2.0, 2.0), density=700.0,
                              position=(target[0], target[1], 1.5))
            print(f"[v0.3b] {state['kind']} bei "
                  f"({target[0]:.2f}, {target[1]:.2f}) gespawnt")
        except ValueError as e:
            print(f"[v0.3b] Spawn ignoriert: {e}")

    try:
        p.track_click_position(side="left", callback=on_click)
    except Exception as e:  # sehr alte pyvista-Versionen
        print(f"[v0.3b] Klick-Spawning nicht verfuegbar ({e})")

    p.show(interactive_update=True, auto_close=False)

    # ---- RTF-/FPS-Messung (M4 Issue 14) ----
    rtf = None
    fps_ema = None
    start_t = time.perf_counter()
    last_t = start_t
    frames = 0
    try:
        while not state["quit"]:
            now = time.perf_counter()
            wall_dt = now - last_t
            last_t = now
            t_sim0 = app.world.time
            if not state["paused"]:
                app.step_frame(1.0 / 60.0)
            sim_dt = app.world.time - t_sim0
            if wall_dt > 1e-9:
                inst_rtf = sim_dt / wall_dt
                inst_fps = 1.0 / wall_dt
                rtf = inst_rtf if rtf is None else 0.9 * rtf + 0.1 * inst_rtf
                fps_ema = (inst_fps if fps_ema is None
                           else 0.9 * fps_ema + 0.1 * inst_fps)
            pos = (app.sph.get_state()[0] if hasattr(app.sph, "get_state")
                   else app.sph.pos[:app.sph.n_real])
            surf.update(pos)
            ren.update(surf)
            if frames % 15 == 0 and rtf is not None:
                ren.set_hud(f"RTF {rtf:5.2f} | {fps_ema:5.1f} FPS | "
                            f"t = {app.world.time:6.1f} s"
                            + (" | PAUSE" if state["paused"] else ""))
            p.update()
            frames += 1
            if args.frames and frames >= args.frames:
                break
    except KeyboardInterrupt:
        pass
    wall = time.perf_counter() - start_t
    if wall > 0:
        print(f"{frames} Frames in {wall:.1f} s -> {frames/wall:.1f} FPS")
        if rtf is not None:
            print(f"Realtime-Faktor (EMA): {rtf:.2f}")
    p.close()


if __name__ == "__main__":
    sys.exit(main())
