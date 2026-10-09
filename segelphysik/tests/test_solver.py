import os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from segelphysik.core.config import Config
from segelphysik.core.bodies import Sphere
from segelphysik.core.solver import World, TimeLoop

CFG = os.path.join(os.path.dirname(__file__), "..", "config.json")

def make_world(): return World(Config.load(CFG))

class TestSolver(unittest.TestCase):
    def test_collision_momentum_conserved_x(self):
        # Impulserhaltung gilt pro Achse ohne äußere Kraft; in z wirkt g.
        w = make_world()
        a = w.add(Sphere(0.5, 1000.0, position=(-1.0,0,-2.5), velocity=( 1.0,0,0), e=1.0, mu=0.0))
        b = w.add(Sphere(0.5, 1000.0, position=( 1.0,0,-2.5), velocity=(-1.0,0,0), e=1.0, mu=0.0))
        px_before = (a.mass*a.vel + b.mass*b.vel)[0]
        for _ in range(300): w.step(1/240)
        px_after = (a.mass*a.vel + b.mass*b.vel)[0]
        self.assertAlmostEqual(px_before, px_after, places=9)
    def test_collision_elastic_swap(self):
        # Gleiche Massen, e=1: Geschwindigkeiten werden getauscht.
        w = make_world()
        a = w.add(Sphere(0.5, 1000.0, position=(-1.0,0,-2.5), velocity=( 1.0,0,0), e=1.0, mu=0.0))
        b = w.add(Sphere(0.5, 1000.0, position=( 1.0,0,-2.5), velocity=(-1.0,0,0), e=1.0, mu=0.0))
        for _ in range(300): w.step(1/240)
        self.assertLess(a.vel[0], -0.9)
        self.assertGreater(b.vel[0], 0.9)
    def test_floor_bounce_restitution(self):
        w = make_world()
        s = w.add(Sphere(0.5, 2000.0, position=(0,0,-1.0), velocity=(0,0,-2.0), e=0.5, mu=0.0))
        max_upward = 0.0
        for _ in range(600):
            w.step(1/240)
            max_upward = max(max_upward, s.vel[2])
        self.assertGreater(max_upward, 0.5)
        self.assertLess(abs(s.vel[2]), 0.05)
        self.assertGreater(s.pos[2], -3.0 + 0.49)
    def test_frame_60fps_gives_4_substeps(self):
        tl = TimeLoop(make_world())
        self.assertEqual(tl.advance(1/60), 4)
        self.assertAlmostEqual(tl.world.time, 4/240, places=12)
    def test_realtime_over_60_frames(self):
        tl = TimeLoop(make_world())
        for _ in range(60): tl.advance(1/60)
        self.assertEqual(tl.substeps_done, 240)
        self.assertAlmostEqual(tl.world.time, 1.0, places=12)
    def test_accumulator_cap(self):
        tl = TimeLoop(make_world())
        self.assertEqual(tl.advance(10.0), tl.max_sub)
    def test_free_fall_semi_implicit_euler(self):
        # Semi-implizite Euler: x_N = x0 - 0.5*g*t^2 - 0.5*g*t*dt (diskret exakt)
        w = make_world()
        s = w.add(Sphere(0.5, 2000.0, position=(0,0,3.0)))
        for _ in range(240): w.step(1/240)
        expected = 3.0 - 0.5*9.81*(1.0 + 1.0/240.0)
        self.assertAlmostEqual(s.pos[2], expected, places=6)

if __name__ == "__main__":
    unittest.main()
