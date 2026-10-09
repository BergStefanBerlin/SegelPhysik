"""Unit-Tests M4: Oberflächenextraktion, Renderer, App-Steuerung,
Einspawner mit Auflösungsregel, Statusanzeige (Plan Issues 10-14)."""
import json, os, sys, unittest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from segelphysik.core.config import Config
from segelphysik.core.app import SimulationApp
from segelphysik.core.render import HeightFieldSurface, MatplotlibRenderer

_HERE = os.path.dirname(__file__)
_CFG_PATH = os.path.join(_HERE, "..", "config.json")


def small_cfg():
    with open(_CFG_PATH) as f:
        d = json.load(f)
    d["basin"] = {"lx": 0.5, "ly": 0.5, "H": 3.0}
    d["water"]["depth"] = 0.5
    d["sph"]["dx"] = 0.0625
    d["sph"]["sound_speed"] = 20.0
    return d


class TestSurface(unittest.TestCase):
    def test_heightfield_dims_and_range(self):
        surf = HeightFieldSurface({"lx": 2.0, "ly": 2.0}, nx=20, ny=20)
        rng = np.random.default_rng(42)
        pos = np.column_stack([rng.uniform(-1, 1, 500),
                               rng.uniform(-1, 1, 500),
                               rng.uniform(-0.5, 0.0, 500)])
        surf.update(pos)
        self.assertEqual(surf.Z.shape, (20, 20))
        fin = surf.Z[np.isfinite(surf.Z)]
        self.assertTrue(np.all(fin <= 1e-12))
        self.assertTrue(np.all(fin >= -0.5 - 1e-12))

    def test_topmost_particle_wins(self):
        surf = HeightFieldSurface({"lx": 2.0, "ly": 2.0}, nx=4, ny=4)
        pos = np.array([[0.0, 0.0, -0.5], [0.0, 0.0, -0.1], [0.0, 0.0, -0.3]])
        surf.update(pos)
        self.assertAlmostEqual(surf.Z[2, 2], -0.1)   # Zelle um (0,0)


class TestRenderer(unittest.TestCase):
    def test_headless_render_produces_image(self):
        import matplotlib
        matplotlib.use("Agg")
        app = SimulationApp(config_dict=small_cfg())
        app.spawn_sphere(radius=0.25, density=500.0, position=(0, 0, 0.5))
        surf = HeightFieldSurface(app.cfg.basin, nx=24, ny=24)
        surf.update(app.sph.pos[:app.sph.n_real])
        fig = MatplotlibRenderer().render(app.world, surf)
        import io
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        self.assertGreater(len(buf.getvalue()), 1000)
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestSpawner(unittest.TestCase):
    def test_resolution_rule_enforced(self):
        app = SimulationApp(config_dict=small_cfg())
        with self.assertRaises(ValueError):
            app.spawn_sphere(radius=0.1, density=500.0, position=(0, 0, 1))
        with self.assertRaises(ValueError):
            app.spawn_box(edges=(0.3, 0.3, 0.3), density=500.0,
                          position=(0, 0, 1))
        b = app.spawn_sphere(radius=0.25, density=500.0, position=(0, 0, 1))
        self.assertEqual(len(app.world.bodies), 1)

    def test_spawn_survives_reset(self):
        app = SimulationApp(config_dict=small_cfg())
        app.spawn_sphere(radius=0.25, density=500.0, position=(0, 0, 1.0))
        for _ in range(2):
            app.step_frame()
        z1 = app.world.bodies[0].pos.copy()
        app.reset()
        self.assertEqual(len(app.world.bodies), 1)   # Spawn bleibt erhalten
        for _ in range(2):
            app.step_frame()
        np.testing.assert_array_equal(app.world.bodies[0].pos, z1)


class TestControls(unittest.TestCase):
    def test_set_g_and_wind(self):
        app = SimulationApp(config_dict=small_cfg())
        app.set_g(1.62)   # Mond
        self.assertAlmostEqual(app.cfg.g, 1.62)
        self.assertAlmostEqual(app.sph.g, 1.62)
        app.set_wind(speed=7.0, azimuth_deg=90.0)
        np.testing.assert_allclose(app.world.environment.wind.velocity(),
                                   [0.0, 7.0, 0.0], atol=1e-12)

    def test_pause_stops_time(self):
        app = SimulationApp(config_dict=small_cfg())
        app.toggle_pause()
        n = app.step_frame()
        self.assertEqual(n, 0)
        self.assertEqual(app.world.time, 0.0)


class TestStatus(unittest.TestCase):
    def test_status_fields_finite(self):
        app = SimulationApp(config_dict=small_cfg())
        app.spawn_sphere(radius=0.25, density=500.0, position=(0, 0, 0.5))
        app.step_frame()
        s = app.status(0)
        for key in ("position", "velocity", "submerged_volume",
                    "submerged_fraction", "force", "time"):
            self.assertIn(key, s)
        self.assertTrue(np.all(np.isfinite(s["position"])))
        self.assertTrue(np.all(np.isfinite(s["force"])))
        self.assertGreaterEqual(s["time"], 0.0)

    def test_falling_sphere_gains_speed(self):
        app = SimulationApp(config_dict=small_cfg())
        app.spawn_sphere(radius=0.25, density=500.0, position=(0, 0, 1.0))
        for _ in range(3):
            app.step_frame()
        self.assertLess(app.world.bodies[0].vel[2], -0.01)


if __name__ == "__main__":
    unittest.main()
