"""Tests: Szenen-Serialisierung (Plan Issue 15)."""
import json
import os
import tempfile
import unittest
from segelphysik.core.scene import Scene, SceneError


def _base_cfg():
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "..", "config.json")) as f:
        return json.load(f)


def _small_cfg():
    cfg = _base_cfg()
    cfg["basin"] = {"lx": 2.0, "ly": 2.0, "H": 4.0}
    cfg["water"] = {"rho": 1000.0, "eta": 0.001, "depth": 0.5}
    return cfg


class TestSceneRoundTrip(unittest.TestCase):
    def test_round_trip_preserves_everything(self):
        cfg = _base_cfg()
        spawns = [
            dict(kind="sphere", radius=1.0, density=500.0,
                 position=[0.0, 0.0, 2.0], kw={"e": 0.5}),
            dict(kind="box", edges=[2.0, 2.0, 2.0], density=800.0,
                 position=[1.0, -1.0, 3.0], kw={}),
        ]
        scene = Scene(cfg, spawns)
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "scene.json")
            scene.save(p)
            loaded = Scene.load(p)
        self.assertEqual(loaded.spawns, spawns)
        self.assertEqual(loaded.config_dict["gravity"], cfg["gravity"])
        self.assertEqual(loaded.config_dict["basin"], cfg["basin"])

    def test_create_app_replays_spawns(self):
        cfg = _small_cfg()
        spawns = [dict(kind="sphere", radius=1.0, density=300.0,
                       position=[0.0, 0.0, 2.0], kw={})]
        app = Scene(cfg, spawns).create_app()
        self.assertEqual(len(app.world.bodies), 1)
        self.assertAlmostEqual(app.world.bodies[0].density, 300.0)
        app.reset()
        self.assertEqual(len(app.world.bodies), 1)

    def test_load_rejects_resolution_violation(self):
        cfg = _base_cfg()
        spawns = [dict(kind="sphere", radius=0.1, density=500.0,
                       position=[0, 0, 2], kw={})]
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "bad.json")
            data = {"version": 1, "config": cfg, "spawns": spawns}
            with open(p, "w") as f:
                json.dump(data, f)
            with self.assertRaises(SceneError):
                Scene(cfg, spawns)
            with self.assertRaises(SceneError):
                Scene.load(p)

    def test_load_rejects_broken_schema(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "broken.json")
            with open(p, "w") as f:
                json.dump({"foo": 1}, f)
            with self.assertRaises(SceneError):
                Scene.load(p)


if __name__ == "__main__":
    unittest.main()
