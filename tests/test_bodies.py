import os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from segelphysik.core.bodies import Sphere, Box, quat_rotate

class TestBodies(unittest.TestCase):
    def test_box_half_submerged_4m3(self):
        b = Box((2,2,2), 500.0, position=(0,0,0))
        self.assertAlmostEqual(b.submerged_volume(0.0), 4.0, places=9)
    def test_sphere_half_submerged(self):
        s = Sphere(1.0, 500.0, position=(0,0,0))
        self.assertAlmostEqual(s.submerged_volume(0.0), (2/3)*np.pi, places=9)
    def test_sphere_full_submerged(self):
        s = Sphere(1.0, 500.0, position=(0,0,-5))
        self.assertAlmostEqual(s.submerged_volume(0.0), s.volume(), places=9)
    def test_sphere_above_water(self):
        s = Sphere(1.0, 500.0, position=(0,0,5))
        self.assertAlmostEqual(s.submerged_volume(0.0), 0.0, places=9)
    def test_a_ref_box_along_z(self):
        self.assertAlmostEqual(Box((2,2,2), 500.0).a_ref((0,0,1)), 4.0, places=9)
    def test_a_ref_sphere(self):
        self.assertAlmostEqual(Sphere(1.0, 500.0).a_ref((1,0,0)), np.pi, places=9)
    def test_inertia_box(self):
        b = Box((2,2,2), 125.0)  # 1000 kg
        self.assertAlmostEqual(b.inertia_diag()[0], 1000/12*(4+4), places=6)
    def test_quat_rotate_identity(self):
        self.assertTrue(np.allclose(quat_rotate((1,0,0,0), (1,2,3)), (1,2,3)))
