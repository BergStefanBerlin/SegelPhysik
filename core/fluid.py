"""SPH-Interface (Spec §7.1, Plan Issue 5). Konkrete Implementierung: M2 (Taichi)."""
from abc import ABC, abstractmethod
import numpy as np

class FluidSolver(ABC):
    @abstractmethod
    def step(self, dt): ...
    @abstractmethod
    def density_at(self, pos) -> float: ...
    @abstractmethod
    def velocity_at(self, pos) -> np.ndarray: ...
    @property
    @abstractmethod
    def n_particles(self) -> int: ...

class NullFluid(FluidSolver):
    """Ersatzimplementierung für M1-Tests (kein Wasser)."""
    def __init__(self): self._n = 0
    def step(self, dt): pass
    def density_at(self, pos): return 0.0
    def velocity_at(self, pos): return np.zeros(3)
    @property
    def n_particles(self): return self._n
