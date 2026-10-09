"""SimulationApp: Steuerung + Einspawner + Status (Plan Issues 12-14, M4).

Kontrollfunktionen (g, Wind, Pause/Reset) als testbare API - das GUI
ruft genau diese Methoden. Einspawner erzwingt die Auflösungsregel
Spec §4 (>= 8*dx) auch programmatisch (Plan v1.2).
"""
import json, os
import numpy as np
from .config import Config, validate_resolution
from .bodies import Sphere, Box
from .forces import Gravity, Buoyancy, WaterDrag, AirDrag
from .solver import World, TimeLoop
from .sph import SphWater


def _default_modules():
    return [Gravity(), Buoyancy(), WaterDrag(), AirDrag()]


class SimulationApp:
    def __init__(self, config_dict=None, config_path=None):
        if config_path is not None:
            cfg = Config.load(config_path)
        else:
            here = os.path.dirname(__file__)
            with open(os.path.join(here, "..", "config.json")) as f:
                cfg = Config(json.load(f))
        if config_dict is not None:
            cfg = Config(config_dict)
        self.cfg = cfg
        self._spawn_specs = []
        self._build()

    def _build(self):
        self.sph = SphWater(self.cfg)
        self.world = World(self.cfg, fluid=self.sph,
                           force_modules=_default_modules())
        self.loop = TimeLoop(self.world)
        self.paused = False
        for spec in self._spawn_specs:
            self._spawn_from_spec(spec)

    # ---------- Einspawner (Issue 13) ----------
    def _spawn_from_spec(self, spec):
        if spec["kind"] == "sphere":
            b = Sphere(radius=spec["radius"], density=spec["density"],
                       position=spec["position"], **spec.get("kw", {}))
        else:
            b = Box(edges=spec["edges"], density=spec["density"],
                    position=spec["position"], **spec.get("kw", {}))
        self.world.add(b)
        return b

    def spawn_sphere(self, radius, density, position, **kw):
        validate_resolution(2.0*radius, self.cfg.dx)   # Spec §4
        spec = dict(kind="sphere", radius=float(radius),
                    density=float(density),
                    position=tuple(float(p) for p in position), kw=kw)
        self._spawn_specs.append(spec)
        return self._spawn_from_spec(spec)

    def spawn_box(self, edges, density, position, **kw):
        validate_resolution(float(min(edges)), self.cfg.dx)
        spec = dict(kind="box", edges=[float(e) for e in edges],
                    density=float(density),
                    position=tuple(float(p) for p in position), kw=kw)
        self._spawn_specs.append(spec)
        return self._spawn_from_spec(spec)

    # ---------- Kontrollpanel (Issue 12) ----------
    def set_g(self, value):
        self.cfg.raw["gravity"] = float(value)
        self.cfg.g = float(value)
        self.sph.g = float(value)

    def set_wind(self, speed, azimuth_deg):
        self.cfg.raw["wind"] = {"speed": float(speed),
                                "azimuth_deg": float(azimuth_deg)}
        self.world.environment.wind.speed = float(speed)
        self.world.environment.wind.azimuth_deg = float(azimuth_deg)

    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused

    def reset(self):
        self._build()

    # ---------- Takt (Issue 12) ----------
    def step_frame(self, real_dt=1.0/60.0):
        if self.paused:
            return 0
        return self.loop.advance(real_dt)

    # ---------- Statusanzeige (Issue 14) ----------
    def status(self, index=0):
        b = self.world.bodies[index]
        v_sub = b.submerged_volume(0.0)
        return {
            "position": b.pos.copy(),
            "velocity": b.vel.copy(),
            "submerged_volume": float(v_sub),
            "submerged_fraction": float(v_sub / b.volume()),
            "force": b.force.copy(),
            "time": float(self.world.time),
            "n_substeps_last_frame": int(self.loop.substeps_done),
        }
