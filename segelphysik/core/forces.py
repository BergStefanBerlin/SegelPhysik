"""Kraftmodul-Schnittstelle (Spec §7.1, Plan Issue 8 - Interface ab M0,
konkrete Fluid-Module in M3)."""
import numpy as np
from abc import ABC, abstractmethod

class ForceModule(ABC):
    @abstractmethod
    def apply(self, body, environment, dt):
        """Addiert Kraft/Moment auf body."""

class Gravity(ForceModule):
    def apply(self, body, environment, dt):
        body.apply_force(np.array([0.0, 0.0, -environment.g]) * body.mass)

class Buoyancy(ForceModule):
    def apply(self, body, environment, dt):
        raise NotImplementedError("M3: Issue 8")

class WaterDrag(ForceModule):
    def apply(self, body, environment, dt):
        raise NotImplementedError("M3: Issue 8")

class AirDrag(ForceModule):
    def apply(self, body, environment, dt):
        raise NotImplementedError("M3: Issue 8")
