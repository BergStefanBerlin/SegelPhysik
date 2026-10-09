import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from segelphysik.core.config import Config, validate_resolution

CFG = os.path.join(os.path.dirname(__file__), "..", "config.json")

class TestConfig(unittest.TestCase):
    def setUp(self): self.cfg = Config.load(CFG)
    def test_defaults(self):
        self.assertAlmostEqual(self.cfg.g, 9.81)
        self.assertEqual(self.cfg.water["rho"], 1000.0)
        self.assertAlmostEqual(self.cfg.air["rho"], 1.225)
        self.assertAlmostEqual(self.cfg.solver["dt"], 1/240)
    def test_resolution_rule_ok(self):
        validate_resolution(2.0, 0.25)
    def test_resolution_rule_fails(self):
        with self.assertRaises(ValueError):
            validate_resolution(1.9, 0.25)
