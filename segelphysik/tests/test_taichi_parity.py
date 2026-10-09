"""Paritaets- und Stabilitaetstests fuer den Taichi/GPU-SPH-Kern (v0.3a).

Wird uebersprungen, wenn taichi nicht installiert ist (pip install taichi-forge).
Geprueft: Interface-Konformitaet, Stabilitaet, Wand-Einhaltung,
Determinismus (K9), hydrostatischer Druckgradient (Paritaet zur Referenz).
"""
import json
import os
import unittest

import numpy as np

from segelphysik.core.config import Config
from segelphysik.core.fluid import FluidSolver

try:
    from segelphysik.fluid import TaichiSphWater
    HAVE_TAICHI = TaichiSphWater is not None
except Exception:
    HAVE_TAICHI = False


_BASE_CFG = None


def _load_base_cfg():
    global _BASE_CFG
    if _BASE_CFG is None:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "config.json")) as f:
            _BASE_CFG = json.load(f)
    return _BASE_CFG


def small_cfg():
    data = json.loads(json.dumps(_load_base_cfg()))
    data["basin"] = {"lx": 2.0, "ly": 2.0, "H": 3.0}
    data["water"]["depth"] = 1.0
    return Config(data)


@unittest.skipUnless(HAVE_TAICHI, "taichi nicht installiert (pip install taichi-forge)")
class TestTaichiSph(unittest.TestCase):

    def test_is_fluidsolver(self):
        self.assertIsInstance(TaichiSphWater(small_cfg()), FluidSolver)

    def test_particle_count(self):
        # 2x2x1 m Becken bei dx=0.25 -> 8*8*4 = 256 Fluidpartikel
        self.assertEqual(TaichiSphWater(small_cfg()).n_particles, 256)

    def test_backend_reported(self):
        self.assertIn(TaichiSphWater(small_cfg()).backend, ("vulkan", "cpu"))

    def test_stable_over_steps(self):
        w = TaichiSphWater(small_cfg())
        for _ in range(20):
            w.step(1.0 / 240.0)
        pos, vel, rho = w.get_state()
        self.assertTrue(np.all(np.isfinite(pos)))
        self.assertTrue(np.all(np.isfinite(vel)))
        self.assertTrue(np.all(np.isfinite(rho)))
        self.assertLess(float(np.max(np.linalg.norm(vel, axis=1))), 50.0)

    def test_walls_contain_particles(self):
        w = TaichiSphWater(small_cfg())
        for _ in range(30):
            w.step(1.0 / 240.0)
        pos = w.get_state()[0]
        self.assertGreaterEqual(float(pos[:, 0].min()), -1.0 - 1e-3)
        self.assertLessEqual(float(pos[:, 0].max()), 1.0 + 1e-3)
        self.assertGreaterEqual(float(pos[:, 2].min()), -1.0 - 1e-3)

    def test_determinism(self):
        a = TaichiSphWater(small_cfg())
        b = TaichiSphWater(small_cfg())
        for _ in range(10):
            a.step(1.0 / 240.0)
            b.step(1.0 / 240.0)
        pa, va, _ = a.get_state()
        pb, vb, _ = b.get_state()
        self.assertLess(float(np.max(np.abs(pa - pb))), 1e-9)
        self.assertLess(float(np.max(np.abs(va - vb))), 1e-9)

    def test_hydrostatic_gradient_parity(self):
        """dp/dz = -rho0*g. Zeitgemittelte Methodik wie der verifizierte
        Referenztest (Spec K3): Einschwingen, dann Mittelung des Drucks in
        zwei Tiefenbaendern ueber viele Schritte (Einzel-Momentaufnahmen sind
        im einschwingenden Becken reines Schwall-Rauschen). c=30 hebt das
        Dichte-Signal (dp/c^2) wie bei der Referenzkalibration."""
        data = json.loads(json.dumps(_load_base_cfg()))
        data["sph"]["sound_speed"] = 30.0
        w = TaichiSphWater(Config(data))
        for _ in range(120):          # Einschwingen (~0.5 s)
            w.step(1.0 / 240.0)
        sum_a = sum_b = 0.0
        za, zb = -0.70, -0.35         # Bandzentren (Tiefe 1.0 m)
        n = 0
        for _ in range(150):          # Zeitmittelung (~0.6 s)
            w.step(1.0 / 240.0)
            pos, vel, rho = w.get_state()
            z = pos[:, 2]
            p = w._c2 * (rho - w.rho0)
            ma = (z > -0.80) & (z < -0.60)
            mb = (z > -0.45) & (z < -0.25)
            if ma.sum() < 5 or mb.sum() < 5:
                continue
            sum_a += float(p[ma].mean())
            sum_b += float(p[mb].mean())
            n += 1
        self.assertGreater(n, 100, "zu wenige verwertbare Schritte")
        slope = (sum_a - sum_b) / (za - zb) / n
        expected = -w.rho0 * w.g
        self.assertLess(abs(slope - expected) / abs(expected), 0.20,
                        f"Gradient {slope:.1f} vs {expected:.1f}")

    def test_velocity_at_returns_vector(self):
        self.assertEqual(TaichiSphWater(small_cfg()).velocity_at(
            np.array([0.0, 0.0, -0.5])).shape, (3,))

    def test_density_at_positive_in_water(self):
        self.assertGreater(TaichiSphWater(small_cfg()).density_at(
            np.array([0.0, 0.0, -0.5])), 500.0)


if __name__ == "__main__":
    unittest.main()
