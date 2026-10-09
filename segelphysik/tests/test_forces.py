"""Unit-Tests M3: Kopplung Fluid <-> Festkörper (Plan Issue 8-9).

Abgedeckte Spec-Kriterien (Vorstufen):
  K2: Auftrieb halb getauchter Quader 39240 N
  K4-Vorbereitung: Fallterminalgeschwindigkeit in Luft (asymptotisch)
  §3: quadratisches Luftwiderstandsgesetz mit Wind (Kraft in Windrichtung!)
  §5: Impulsübertrag Körper -> SPH-Partikel
"""
import json, os, sys, unittest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from segelphysik.core.config import Config
from segelphysik.core.bodies import Sphere, Box
from segelphysik.core.forces import (Environment, WindField, Gravity,
                                     Buoyancy, WaterDrag, AirDrag)
from segelphysik.core.solver import World, TimeLoop
from segelphysik.core.fluid import NullFluid
from segelphysik.core.sph import SphWater

_HERE = os.path.dirname(__file__)
_CFG_PATH = os.path.join(_HERE, "..", "config.json")


def load_cfg():
    with open(_CFG_PATH) as f:
        return Config(json.load(f))


class TestBuoyancy(unittest.TestCase):
    def test_sphere_half_submerged(self):
        cfg = load_cfg()
        env = Environment(cfg, NullFluid())
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, 0))
        Buoyancy().apply(s, env, 1e-3)
        v_half = 0.5*s.volume()
        f_target = cfg.water["rho"]*v_half*cfg.g
        self.assertAlmostEqual(s.force[2], f_target, delta=1e-6*f_target)
        self.assertAlmostEqual(s.force[0], 0.0, places=12)

    def test_box_half_submerged_k2_value(self):
        """Spec K2: 2x2x2-Quader halb eingetaucht -> 39240 N."""
        cfg = load_cfg()
        env = Environment(cfg, NullFluid())
        b = Box(edges=(2, 2, 2), density=500.0, position=(0, 0, 0))
        Buoyancy().apply(b, env, 1e-3)
        self.assertAlmostEqual(b.force[2], 39240.0, delta=0.1)

    def test_sphere_deep_submerged(self):
        cfg = load_cfg()
        env = Environment(cfg, NullFluid())
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, -5))
        Buoyancy().apply(s, env, 1e-3)
        f_target = cfg.water["rho"]*s.volume()*cfg.g
        self.assertAlmostEqual(s.force[2], f_target, delta=1e-9*f_target)

    def test_above_water_no_force(self):
        cfg = load_cfg()
        env = Environment(cfg, NullFluid())
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, 5))
        Buoyancy().apply(s, env, 1e-3)
        self.assertAlmostEqual(float(np.linalg.norm(s.force)), 0.0, places=12)


class TestDrag(unittest.TestCase):
    def test_water_drag_quadratic(self):
        cfg = load_cfg()
        env = Environment(cfg, NullFluid())
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, -2))
        s.vel = np.array([1.0, 0, 0])
        d1 = WaterDrag(); d1.apply(s, env, 1e-3)
        f1 = s.force.copy(); s.force = np.zeros(3)
        s.vel = np.array([2.0, 0, 0])
        d1.apply(s, env, 1e-3)
        ratio = s.force[0]/f1[0]
        self.assertAlmostEqual(ratio, 4.0, places=9)

    def test_air_drag_with_wind(self):
        """Spec §3: ruhender Körper im Wind 10 m/s wird MITGERISSEN:
        F = +1/2 rho cw A v² in Windrichtung (+x)."""
        cfg = load_cfg()
        env = Environment(cfg, NullFluid())
        env.wind = WindField(speed=10.0, azimuth_deg=0.0)
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, 5))
        s.cw = 0.47
        AirDrag().apply(s, env, 1e-3)
        f_target = 0.5*cfg.air["rho"]*0.47*np.pi*100.0
        self.assertAlmostEqual(s.force[0], f_target, delta=1e-6*f_target)

    def test_terminal_velocity_approach(self):
        """K4-Vorbereitung: Fallterminalgeschwindigkeit.
        Leichte Kugel (rho=2): v_term ~ 4,77 m/s; nach 320 Substeps
        (2,7 Zeitkonstanten) > 95 % erreicht, Fallstrecke ~3,2 m -
        die Kugel bleibt sicher über dem Boden (Aufprall vermieden).
        Fallen = negative z-Richtung, daher Betrag vergleichen."""
        cfg = load_cfg()
        s = Sphere(radius=0.25, density=2.0, position=(0, 0, 5.0))
        s.cw = 0.47
        world = World(cfg, force_modules=[Gravity(), AirDrag()])
        world.add(s)
        loop = TimeLoop(world)
        m = s.mass
        v_term = np.sqrt(2*m*cfg.g/(cfg.air["rho"]*0.47*np.pi*0.25**2))
        for _ in range(320):
            loop.advance(1.0/240.0)
        self.assertGreater(abs(s.vel[2]), 0.95*v_term)
        self.assertLess(abs(s.vel[2]), v_term)      # nie drueber
        self.assertGreater(s.pos[2], 0.0)           # noch in der Luft


class TestWindField(unittest.TestCase):
    def test_azimuth_rotation(self):
        w0 = WindField(speed=5.0, azimuth_deg=0.0)
        np.testing.assert_allclose(w0.velocity(), [5.0, 0.0, 0.0], atol=1e-12)
        w90 = WindField(speed=5.0, azimuth_deg=90.0)
        np.testing.assert_allclose(w90.velocity(), [0.0, 5.0, 0.0], atol=1e-12)


class TestFeedback(unittest.TestCase):
    def test_impulse_transfer_to_particles(self):
        """Spec §5: Wasserwiderstand beschleunigt umliegende Partikel."""
        with open(_CFG_PATH) as f:
            d = json.load(f)
        d["basin"] = {"lx": 0.5, "ly": 0.5, "H": 3.0}
        d["water"]["depth"] = 0.5
        d["sph"]["dx"] = 0.0625
        d["sph"]["sound_speed"] = 20.0
        cfg = Config(d)
        sph = SphWater(cfg)
        center = np.array([0.0, 0.0, -0.25])
        v_before = sph.velocity_at(center).copy()
        sph.apply_body_force(center, np.array([100.0, 0, 0]), 1.0/240.0)
        v_after = sph.velocity_at(center)
        self.assertGreater(v_after[0] - v_before[0], 1e-3)

    def test_world_with_sph_runs(self):
        """Integration: World + SPH + alle Kraftmodule laufen deterministisch."""
        with open(_CFG_PATH) as f:
            d = json.load(f)
        d["basin"] = {"lx": 0.5, "ly": 0.5, "H": 3.0}
        d["water"]["depth"] = 0.5
        d["sph"]["dx"] = 0.0625
        d["sph"]["sound_speed"] = 20.0
        cfg = Config(d)
        sph = SphWater(cfg)
        w = World(cfg, fluid=sph,
                  force_modules=[Gravity(), Buoyancy(), WaterDrag(), AirDrag()])
        s = Sphere(radius=0.25, density=500.0, position=(0, 0, 1.0))
        w.add(s)
        loop = TimeLoop(w)
        for _ in range(4):
            loop.advance(1.0/60.0)
        self.assertTrue(np.all(np.isfinite(s.pos)))
        self.assertTrue(np.all(np.isfinite(sph.pos)))


class TestEquilibrium(unittest.TestCase):
    def test_neutral_buoyant_sphere_stays(self):
        """rho=500-Kugel, halb getaucht: Kräftegleichgewicht -> bleibt."""
        cfg = load_cfg()
        w = World(cfg, force_modules=[Gravity(), Buoyancy(), WaterDrag()])
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, 0))
        w.add(s)
        loop = TimeLoop(w)
        for _ in range(240):
            loop.advance(1.0/240.0)
        self.assertLess(abs(s.pos[2]), 1e-9)

    def test_perturbed_returns_toward_equilibrium(self):
        cfg = load_cfg()
        w = World(cfg, force_modules=[Gravity(), Buoyancy(), WaterDrag()])
        s = Sphere(radius=1.0, density=500.0, position=(0, 0, 0.1))
        w.add(s)
        loop = TimeLoop(w)
        for _ in range(480):
            loop.advance(1.0/240.0)
        self.assertLess(abs(s.pos[2]), 0.15)


if __name__ == "__main__":
    unittest.main()
