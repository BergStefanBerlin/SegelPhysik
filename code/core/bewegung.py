"""SegelPhysik V3 - Bewegung (Kinematik) (SPEC_V3.md Abschnitt 4).

Rein vorgeschriebene Bewegung: KEIN Integrator. phi(t) = omega*t,
omega = 360 Grad / 15 s. D1: horizontale Achse (Welt-y) durch den Schwerpunkt;
D2: r_S fixiert (0,0,0); D3: phi(0)=0 => aufrecht, Reset setzt t=0.
Determinismus (K7''): phi ist reine Funktion von t.
"""
from __future__ import annotations
import math, json
import numpy as np

__all__ = ["OMEGA","PERIOD_S","DT","phi_rad","phi_deg","rotation_matrix",
           "body_pose","Clock","Scene"]

PERIOD_S = 15.0
OMEGA = 2.0*math.pi/PERIOD_S          # rad/s = 24 Grad/s
DT = 1.0/240.0                        # Animationsuhr (Spec: 1/240 s)


def phi_rad(t): return OMEGA*float(t)
def phi_deg(t): return math.degrees(phi_rad(t))


def rotation_matrix(phi, axis=(0.0,1.0,0.0)):
    """3x3 Rotationsmatrix um axis (Weltframe), Winkel phi in rad."""
    a = np.asarray(axis, dtype=np.float64); n = np.linalg.norm(a)
    if n == 0: raise ValueError("Rotationsachse darf nicht der Nullvektor sein")
    a = a/n
    K = np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0.0]])
    return np.eye(3) + math.sin(phi)*K + (1.0-math.cos(phi))*(K@K)


def body_pose(t, axis=(0.0,1.0,0.0), phase=0.0):
    """Pose zur Animationszeit t -> (R 3x3, r_S)."""
    return rotation_matrix(phase + phi_rad(t), axis), np.zeros(3)   # D2


class Clock:
    """Animationsuhr: Akkumulator, DT-Substeps, Pause/Step, Reset, playback."""
    def __init__(self, playback=1.0):
        if playback <= 0: raise ValueError("playback > 0 erforderlich")
        self.playback = float(playback); self.t = 0.0; self._acc = 0.0
        self.paused = False

    def reset(self):
        self.t = 0.0; self._acc = 0.0                 # D3

    def advance_real(self, real_dt):
        """Verarbeitet akkumulierte DT-Substeps; liefert Substep-Anzahl."""
        if self.paused or real_dt <= 0: return 0
        self._acc += real_dt*self.playback
        n = int(self._acc/DT); self._acc -= n*DT; self.t += n*DT
        return n

    def step_once(self):
        self.t += DT


class Scene:
    """Szenen-Container mit JSON-Rundtrip (Spec Abschnitt 7).
    position ist spec-deviation (Plan M3): Pflicht bei > 1 Koerper ohne
    position-Feld (das Spec-§7-JSON kennt position nicht)."""
    def __init__(self, bodies=None): self.bodies = list(bodies) if bodies else []

    @classmethod
    def default(cls, body_type="cone"):
        dims = {"cone":{"H":2.0,"R":1.0},"box":{"dx":2.0,"dy":2.0,"dz":2.0},
                "pyramid":{"a":2.0,"H":2.0}}[body_type]
        return cls([{"type":body_type,"dims":dims,"axis":[0.0,1.0,0.0],
                     "omega":OMEGA,"phase":0.0,"position":[0.0,0.0,0.0]}])

    def to_json(self): return json.dumps({"bodies":self.bodies}, sort_keys=True)

    @classmethod
    def from_json(cls, s):
        sc = cls(json.loads(s)["bodies"])
        if len(sc.bodies) > 1:
            for b in sc.bodies:
                if "position" not in b:
                    raise ValueError("Mehrere Koerper: 'position' ist Pflicht")
        return sc


# ================= Deutschsprachige Fassade (sprechende API) =================
class Uhr(Clock):
    """Animationsuhr mit deutschen Namen (Basis: Clock)."""

    def __init__(self, wiedergabe=1.0):
        super().__init__(playback=wiedergabe)

    def weiter_real(self, real_dt):
        """Verarbeitet reale Zeit; liefert Anzahl der DT-Substeps."""
        return self.advance_real(real_dt)

    def ruecksetzen(self):
        self.reset()


class Szene(Scene):
    """Szene mit deutschen Namen (Basis: Scene)."""

    @property
    def koerper(self):
        return self.bodies

    @classmethod
    def standard(cls, koerpertyp="cone"):
        return cls.default(koerpertyp)


def koerper_pose(t, achse=(0.0, 1.0, 0.0), phase=0.0):
    """Pose zur Animationszeit t -> (R 3x3, r_S). Deutsche Parameter-Namen."""
    return body_pose(t, axis=achse, phase=phase)


phi_grad = phi_deg
