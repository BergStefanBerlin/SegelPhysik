"""Zentrales Parameterobjekt - einzige Quelle der Wahrheit (Spec 1.0 §7.1)."""
import json

class Config:
    def __init__(self, data: dict):
        self.raw = data
        self.basin = data["basin"]
        self.water = data["water"]
        self.air = data["air"]
        self.g = float(data["gravity"])
        self.wind = data["wind"]
        self.solver = data["solver"]
        self.sph = data["sph"]
        self.defaults_body = data["defaults_body"]
        self.test_bodies = data["test_bodies"]
        self._validate()
    @classmethod
    def load(cls, path):
        with open(path) as f: return cls(json.load(f))
    def _validate(self):
        dx = float(self.sph["dx"])
        if dx <= 0: raise ValueError("dx muss > 0 sein")
        if float(self.solver["dt"]) <= 0: raise ValueError("dt muss > 0 sein")
        if self.water["depth"] <= 0 or self.water["depth"] > self.basin["H"]/3 + 1e-9:
            raise ValueError("Wassertiefe muss 0 < d <= H/3 sein")
    @property
    def dx(self): return float(self.sph["dx"])

def validate_resolution(body_dim: float, dx: float) -> None:
    """Auflösungsregel Spec §4: Körperabmessung >= 8*dx.
    Generische Funktion (Plan v1.2): angewendet im Einspawner (M4),
    Szenenladen (M5) und vor Simulationsstart."""
    if body_dim < 8.0 * dx - 1e-12:
        raise ValueError(f"Auflösungsregel verletzt: {body_dim} < 8*dx = {8*dx}")
