"""Szenen-Serialisierung (Plan Issue 15, Spec §7.1/K9).

Eine Szene = Konfiguration + Einspann-Spezifikationen. Voraussetzung
fuer Reproduzierbarkeit (K9) und Regressionstests. Beim Laden wird die
Aufloesungsregel (Spec §4: Koerperabmessung >= 8*dx) erzwungen - auch
fuer Szenendateien (Plan v1.2, Fund 3).
"""
import copy
import json
from .config import Config, validate_resolution
from .app import SimulationApp


class SceneError(ValueError):
    """Ungueltige Szenendatei (Schema- oder Regelverletzung)."""


class Scene:
    def __init__(self, config_dict, spawns):
        self.config_dict = copy.deepcopy(config_dict)
        self.spawns = copy.deepcopy(spawns)
        self._validate()

    def _validate(self):
        cfg = Config(copy.deepcopy(self.config_dict))
        dx = cfg.dx
        for i, spec in enumerate(self.spawns):
            if spec["kind"] == "sphere":
                dim = 2.0 * float(spec["radius"])
            elif spec["kind"] == "box":
                dim = float(min(spec["edges"]))
            else:
                raise SceneError(f"Spawn {i}: unbekannter Typ {spec['kind']!r}")
            try:
                validate_resolution(dim, dx)
            except ValueError as exc:
                raise SceneError(f"Spawn {i}: {exc}") from exc

    def to_dict(self):
        return {"version": 1, "config": self.config_dict, "spawns": self.spawns}

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "config" not in data or "spawns" not in data:
            raise SceneError("Szenendatei: Schema verletzt (config/spawns fehlen)")
        return cls(data["config"], data["spawns"])

    def create_app(self):
        """Baut eine frische SimulationApp exakt nach Szenenstand."""
        app = SimulationApp(config_dict=copy.deepcopy(self.config_dict))
        for spec in self.spawns:
            if spec["kind"] == "sphere":
                app.spawn_sphere(spec["radius"], spec["density"],
                                 spec["position"], **spec.get("kw", {}))
            else:
                app.spawn_box(spec["edges"], spec["density"],
                              spec["position"], **spec.get("kw", {}))
        return app

    @classmethod
    def from_app(cls, app):
        return cls(app.cfg.raw, app._spawn_specs)
