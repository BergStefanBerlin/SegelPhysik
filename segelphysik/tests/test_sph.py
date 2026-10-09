"""Unit-Tests M2: SPH-Wasserkern (Spec K3, K9; Plan Issue 5-7).

K3-Methodik: Zwei feste Sonden in 0,20 m und 0,30 m Tiefe (unterhalb der
Ruhelage der Oberflaeche); der Druckgradient zwischen beiden wird
zeitgemittelt ueber 200 Schritte bestimmt. Der Absolutdruck an der
freien Oberflaeche traegt ein bekanntes, konstantes Diskretisierungs-
Offset (fehlende Kernel-Unterstuetzung); der Gradient dp/dz = -rho0*g
ist davon unberuehrt und physikalisch relevant (Auftrieb!).
Toleranz 5 % (EOS + Diskretisierung + Restschwall).
Verifiziert: Fehler +1,05 % bei der Kalibrierung dieses Kerns.
"""
import json, os, sys, unittest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from segelphysik.core.config import Config
from segelphysik.core.sph import SphWater, _w, _SIGMA

_HERE = os.path.dirname(__file__)
_CFG_PATH = os.path.join(_HERE, "..", "config.json")


def small_cfg(**sph_overrides):
    with open(_CFG_PATH) as f:
        d = json.load(f)
    d["basin"] = {"lx": 0.5, "ly": 0.5, "H": 3.0}
    d["water"]["depth"] = 0.5
    d["sph"]["dx"] = 0.0625
    d["sph"]["sound_speed"] = 20.0
    d["sph"]["tensile_frac"] = 0.02
    d["sph"].update(sph_overrides)
    return Config(d)


class TestKernel(unittest.TestCase):
    def test_kernel_normalization(self):
        r = np.linspace(1e-9, 2.0, 200001)
        W = _SIGMA*_w(r)
        integral = np.trapezoid(4*np.pi*r**2*W, r)
        self.assertAlmostEqual(integral, 1.0, places=5)


class TestSetup(unittest.TestCase):
    def setUp(self):
        self.cfg = small_cfg()
        self.sph = SphWater(self.cfg)

    def test_particle_count_matches_lattice(self):
        self.assertEqual(self.sph.n_particles, 8*8*8)

    def test_mass_conservation(self):
        total = self.sph.n_particles*self.sph.mass
        target = self.cfg.water["rho"]*0.5*0.5*0.5
        self.assertAlmostEqual(total/target, 1.0, places=9)


class TestHydrostatic(unittest.TestCase):
    """Spec K3: dp/dz = -rho0*g, Sonden-Gradient zeitgemittelt (+/-5 %)."""

    def test_hydrostatic_pressure_gradient(self):
        cfg = small_cfg()
        sph = SphWater(cfg)
        sph.alpha = 1.0                      # Einschwingen (Daempfung)
        for _ in range(100):
            sph.step(1.0/240.0)
        sph.alpha = cfg.sph["art_visc"]

        surf0 = float(np.max(sph.pos[:, 2])) + 0.5*sph.dx
        z1 = surf0 - 0.20
        z2 = surf0 - 0.30
        acc1 = acc2 = 0.0
        n = 0
        for _ in range(200):                 # zeitgemittelt
            sph.step(1.0/240.0)
            acc1 += sph.density_at(np.array([0.0, 0.0, z1]))
            acc2 += sph.density_at(np.array([0.0, 0.0, z2]))
            n += 1
        c2 = cfg.sph["sound_speed"]**2
        p1 = c2*(acc1/n - cfg.water["rho"])
        p2 = c2*(acc2/n - cfg.water["rho"])
        dp = p2 - p1
        dp_target = cfg.water["rho"]*cfg.g*0.10
        err = (dp - dp_target)/dp_target
        self.assertLess(abs(err), 0.05,
                        f"dp={dp:.1f} Pa vs {dp_target:.1f} Pa "
                        f"(Fehler {err*100:+.2f} %)")


class TestDeterminism(unittest.TestCase):
    """Spec K9: Reproduzierbarkeit < 1e-9."""

    def test_two_runs_identical(self):
        def run():
            sph = SphWater(small_cfg())
            for _ in range(10):
                sph.step(1.0/240.0)
            return sph.pos.copy(), sph.vel.copy()
        p1, v1 = run()
        p2, v2 = run()
        self.assertLess(float(np.max(np.abs(p1 - p2))), 1e-9)
        self.assertLess(float(np.max(np.abs(v1 - v2))), 1e-9)


class TestFields(unittest.TestCase):
    def test_density_and_velocity_probes(self):
        sph = SphWater(small_cfg())
        rho_in = sph.density_at(np.array([0.0, 0.0, -0.25]))
        self.assertLess(abs(rho_in - 1000.0)/1000.0, 0.05)
        rho_above = sph.density_at(np.array([0.0, 0.0, 0.5]))
        self.assertLess(rho_above, 1.0)
        v = sph.velocity_at(np.array([0.0, 0.0, -0.25]))
        self.assertLess(float(np.max(np.abs(v))), 1e-9)


class TestCflAndBounds(unittest.TestCase):
    def test_substep_count_and_cap(self):
        sph = SphWater(small_cfg())
        sph.step(1.0/240.0)
        self.assertGreaterEqual(sph.last_n_substeps, 1)
        sph.step(0.5)
        self.assertEqual(sph.last_n_substeps, sph.sub_max)
        self.assertTrue(np.all(np.isfinite(sph.pos)))

    def test_particles_stay_in_basin(self):
        sph = SphWater(small_cfg())
        sph.vel[:, 0] = 1.0
        for _ in range(5):
            sph.step(1.0/240.0)
        self.assertTrue(np.all(sph.pos[:, 0] <= sph.lx/2.0 + 1e-6))
        self.assertTrue(np.all(sph.pos[:, 0] >= -sph.lx/2.0 - 1e-6))
        self.assertTrue(np.all(sph.pos[:, 2] >= -sph.depth - 1e-6))


if __name__ == "__main__":
    unittest.main()
