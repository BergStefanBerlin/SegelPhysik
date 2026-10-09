"""Formale Akzeptanz-Suite zu Spec §8, K1-K10 (Plan Issue 16).

Zwei Stufen: QUICK (Standard, CI) und FULL (SEGELPHYSIK_FULL=1).
Dokumentierte Abweichungen: siehe doc/ACCEPTANCE.md.
"""
import json
import math
import os
import unittest
import numpy as np

from segelphysik.core.config import Config
from segelphysik.core.bodies import Sphere, Box
from segelphysik.core.solver import World, TimeLoop
from segelphysik.core.fluid import NullFluid
from segelphysik.core.forces import Gravity, Buoyancy, WaterDrag, AirDrag
from segelphysik.core.scene import Scene

FULL = os.environ.get("SEGELPHYSIK_FULL", "")


def _cfg(**over):
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "..", "config.json")) as f:
        data = json.load(f)
    data.update(over)
    return Config(data)


def _small_data():
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "..", "config.json")) as f:
        data = json.load(f)
    data["basin"] = {"lx": 2.0, "ly": 2.0, "H": 4.0}
    data["water"] = {"rho": 1000.0, "eta": 0.001, "depth": 0.5}
    return data


def _rigid_world(cfg, modules):
    return World(cfg, fluid=NullFluid(), force_modules=modules)


class K1FloatSink(unittest.TestCase):
    """K1: Schwimmen/Sinken (QUICK: analytischer Auftrieb, NullFluid)."""

    def test_sphere_500_floats_stable(self):
        cfg = _cfg()
        w = _rigid_world(cfg, [Gravity(), Buoyancy(), WaterDrag()])
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, 0.05))
        w.add(s)
        loop = TimeLoop(w)
        dt = cfg.solver["dt"]
        for _ in range(int(10.0 / dt)):
            loop.advance(dt)
        self.assertLess(abs(s.pos[2]), 0.10)
        zs = []
        for _ in range(int(2.0 / dt)):
            loop.advance(dt)
            zs.append(s.pos[2])
        self.assertLess(max(abs(z - s.pos[2]) for z in zs), 0.10)

    def test_sphere_2000_sinks_and_rests(self):
        cfg = _cfg()
        w = _rigid_world(cfg, [Gravity(), Buoyancy(), WaterDrag()])
        s = Sphere(radius=1.0, density=2000.0, position=(0, 0, 1.0))
        w.add(s)
        loop = TimeLoop(w)
        dt = cfg.solver["dt"]
        for _ in range(int(8.0 / dt)):
            loop.advance(dt)
        ground = -cfg.basin["H"] / 3.0 + 1.0
        self.assertLess(s.pos[2], ground + 0.05)
        self.assertLess(abs(s.vel[2]), 0.05)


class K2Buoyancy(unittest.TestCase):
    """K2: Auftrieb statisch exakt (Sollwert 39.240 N)."""

    def test_half_submerged_box_force(self):
        cfg = _cfg()
        w = _rigid_world(cfg, [Buoyancy()])
        b = Box(edges=(2.0, 2.0, 2.0), density=500.0, position=(0, 0, 0.0))
        w.add(b)
        for m in w.force_modules:
            m.apply(b, w.environment, 0.0)
        expected = 1000.0 * 4.0 * 9.81
        self.assertAlmostEqual(b.force[2], expected, delta=0.01 * expected)


class K4AirDragWind(unittest.TestCase):
    """K4: Luftwiderstand & Wind."""

    def test_terminal_velocity_matches_analytic(self):
        cfg = _cfg()
        w = _rigid_world(cfg, [Gravity(), AirDrag()])
        r, rho = 0.5, 1.0
        s = Sphere(radius=r, density=rho, position=(0, 0, 6.0))
        w.add(s)
        m = rho * (4.0 / 3.0) * math.pi * r ** 3
        a = math.pi * r ** 2
        cw = w.environment.cw_default(s)
        v_term = math.sqrt(2.0 * m * cfg.g / (1.225 * cw * a))
        self.assertLess(v_term, 23.0)
        floor = -cfg.basin["H"] / 3.0
        loop = TimeLoop(w)
        dt = cfg.solver["dt"]
        reached = False
        for _ in range(int(3.0 / dt)):
            loop.advance(dt)
            if abs(s.vel[2]) >= 0.95 * v_term:
                reached = True
                break
            if s.pos[2] - r <= floor + 0.5:
                break
        self.assertTrue(reached, "v_term nicht erreicht vor Bodenaufprall")
        self.assertLess(abs(abs(s.vel[2]) - v_term), 0.05 * v_term)

    def test_horizontal_relaxes_to_wind(self):
        # Gemessen (Kalibrierlauf): bei v_Wind = 2 m/s erreicht die leichte
        # Kugel 95 % nach ~22 s bei x ~ 37 m (quadratische Relaxation ist
        # bei kleinen Relativgeschwindigkeiten langsam). Becken 100 m
        # (mit NullFluid kostenlos), Abbruch bei Erreichen von 95 %.
        data = json.loads(json.dumps(_cfg().raw))
        data["gravity"] = 0.0
        data["basin"] = {"lx": 100.0, "ly": 100.0, "H": 9.0}
        cfg = Config(data)
        w = _rigid_world(cfg, [AirDrag()])
        w.environment.wind.speed = 2.0
        w.environment.wind.azimuth_deg = 0.0
        s = Sphere(radius=0.5, density=1.0, position=(0, 0, 1.0))
        w.add(s)
        loop = TimeLoop(w)
        dt = cfg.solver["dt"]
        reached = False
        for _ in range(int(30.0 / dt)):
            loop.advance(dt)
            if s.vel[0] >= 0.95 * 2.0:
                reached = True
                break
        self.assertTrue(reached, "v_Wind nicht innerhalb von 30 s erreicht")
        self.assertLess(abs(s.vel[0] - 2.0), 0.05 * 2.0)


class K6Collisions(unittest.TestCase):
    """K6: Kollisionen - Eindringtiefe, Impuls, Waende."""

    def test_head_on_exchange_penetration_and_momentum(self):
        cfg = _cfg()
        w = _rigid_world(cfg, [Gravity()])
        a = Sphere(radius=1.0, density=500.0, position=(-2.5, 0, 5.0),
                   velocity=(3.0, 0, 0), e=1.0)
        b = Sphere(radius=1.0, density=500.0, position=(2.5, 0, 5.0),
                   velocity=(-3.0, 0, 0), e=1.0)
        w.add(a); w.add(b)
        loop = TimeLoop(w)
        dt = cfg.solver["dt"]
        min_gap = float("inf")
        p0 = a.mass * a.vel[0] + b.mass * b.vel[0]
        for _ in range(int(2.0 / dt)):
            loop.advance(dt)
            gap = np.linalg.norm(b.pos - a.pos) - 2.0
            min_gap = min(min_gap, gap)
        self.assertGreater(min_gap, -0.02)
        p1 = a.mass * a.vel[0] + b.mass * b.vel[0]
        self.assertAlmostEqual(p0, p1, places=9)

    def test_floor_holds(self):
        cfg = _cfg()
        w = _rigid_world(cfg, [Gravity()])
        s = Sphere(radius=1.0, density=2000.0, position=(0, 0, 2.0), e=0.1)
        w.add(s)
        loop = TimeLoop(w)
        dt = cfg.solver["dt"]
        for _ in range(int(4.0 / dt)):
            loop.advance(dt)
        floor = -cfg.basin["H"] / 3.0
        self.assertGreaterEqual(s.pos[2] - 1.0, floor - 0.02)


class K8Interaction(unittest.TestCase):
    """K8: API-Interaktion - Spawn, g/Wind zur Laufzeit."""

    def test_runtime_changes_take_effect(self):
        from segelphysik.core.app import SimulationApp
        app = SimulationApp(config_dict=_small_data())
        app.spawn_sphere(radius=1.0, density=500.0, position=(0, 0, 2.0))
        self.assertEqual(len(app.world.bodies), 1)
        app.set_g(1.62)
        self.assertAlmostEqual(app.cfg.g, 1.62)
        self.assertAlmostEqual(app.sph.g, 1.62)
        app.set_wind(speed=7.0, azimuth_deg=90.0)
        self.assertAlmostEqual(app.world.environment.wind.speed, 7.0)
        app.toggle_pause()
        self.assertEqual(app.step_frame(), 0)
        app.toggle_pause()
        self.assertGreater(app.step_frame(), 0)


class K9Determinism(unittest.TestCase):
    """K9: Reproduzierbarkeit - 1.000 Substeps, < 1e-9."""

    def test_two_runs_identical(self):
        data = _small_data()
        cfg = Config(data)
        spawns = [dict(kind="sphere", radius=1.0, density=500.0,
                       position=[0, 0, 2.0], kw={"e": 0.5}),
                  dict(kind="box", edges=[2.0, 2.0, 2.0], density=800.0,
                       position=[1.5, 0, 4.0], kw={})]
        scene = Scene(data, spawns)
        finals = []
        for _ in range(2):
            app = scene.create_app()
            loop = TimeLoop(app.world)
            dt = cfg.solver["dt"]
            for _ in range(1000):
                loop.advance(dt)
            finals.append(np.concatenate(
                [b.pos.copy() for b in app.world.bodies] +
                [b.vel.copy() for b in app.world.bodies]))
        self.assertLess(float(np.max(np.abs(finals[0] - finals[1]))), 1e-9)


class K5WavesFull(unittest.TestCase):
    """K5: Wellen nach Einsprung (FULL: echter SPH-Kern)."""

    @unittest.skipUnless(FULL, "FULL-Stufe: SEGELPHYSIK_FULL=1 setzen")
    def test_splash_creates_waves(self):
        from segelphysik.core.sph import SphWater
        from segelphysik.core.render import HeightFieldSurface
        data = _small_data()
        cfg = Config(data)
        w = _rigid_world(cfg, [Gravity(), Buoyancy(), WaterDrag()])
        sph = SphWater(cfg)
        w.environment.fluid = sph
        s = Sphere(radius=0.5, density=500.0, position=(0, 0, 1.5))
        w.add(s)
        loop = TimeLoop(w)
        surf = HeightFieldSurface(cfg.basin, nx=16, ny=16)
        dt = cfg.solver["dt"]
        amp = 0.0
        for _ in range(int(1.5 / dt)):
            loop.advance(dt)
            surf.update(sph.pos[:sph.n_real])
            h = surf.height
            if h is not None:
                finite = h[np.isfinite(h)]
                if finite.size:
                    amp = max(amp, float(finite.max() - finite.min()))
        self.assertGreaterEqual(amp, 2.0 * cfg.dx)


if __name__ == "__main__":
    unittest.main()
