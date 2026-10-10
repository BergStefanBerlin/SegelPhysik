"""Starrkörper-Solver + Akkumulator-Zeitschleife (Plan Issues 3-4).
Semi-implizite Euler, impulsbasierte Kollisionsauflösung mit Restitution
und Coulomb-Reibung. Wände/Boden geschlossen, Oberseite offen (Spec §1)."""
import numpy as np
from .fluid import NullFluid
from .bodies import Sphere, quat_integrate

class World:
    def __init__(self, config, fluid=None, force_modules=None):
        self.cfg = config
        self.bodies = []
        self.fluid = fluid if fluid is not None else NullFluid()
        from .forces import Environment, Gravity
        self.environment = Environment(config, self.fluid)
        self.force_modules = force_modules if force_modules is not None \
            else [Gravity()]
        self.time = 0.0
    def add(self, body):
        self.bodies.append(body); return body
    def _walls(self):
        """Wände als (Achse, Vorzeichen, Limit, Innennormale).
        Boden bei z = -depth (Spec: Wasser z in [-H/3, 0]), Oberseite offen."""
        b = self.cfg.basin
        depth = float(self.cfg.water["depth"])
        return [("x", +1, b["lx"]/2, np.array([-1.0,0,0])),
                ("x", -1, b["lx"]/2, np.array([ 1.0,0,0])),
                ("y", +1, b["ly"]/2, np.array([0,-1.0,0])),
                ("y", -1, b["ly"]/2, np.array([0, 1.0,0])),
                ("z", -1, depth,      np.array([0,0, 1.0]))]
    def step(self, dt: float, step_fluid: bool = True):
        """Ein fester Substep (dt = 1/240 s).

        step_fluid=False unterdrueckt den Fluidaufruf (v0.3a-Perf: der
        Solver buendelt den Fluidschritt einmal pro Frame in advance(),
        die Rueckwirkung der Koerperkraefte auf die Partikel laeuft
        weiter pro Substep ueber die Kraftmodule)."""
        for b in self.bodies:
            b.force = np.zeros(3); b.torque = np.zeros(3)
        for mod in self.force_modules:
            for b in self.bodies:
                mod.apply(b, self.environment, dt)
        if step_fluid:
            self.fluid.step(dt)
        for b in self.bodies:
            b.vel += b.force / b.mass * dt
            b.omega += (b.torque / b.inertia_diag()) * dt  # diag-Näherung (v0.2)
        for _ in range(8):
            self._resolve_contacts()
        for b in self.bodies:
            b.pos += b.vel * dt
            b.q = quat_integrate(b.q, b.omega, dt)
        self.time += dt
    def _resolve_contacts(self):
        n = len(self.bodies)
        for i in range(n):
            for j in range(i+1, n):
                a, b = self.bodies[i], self.bodies[j]
                if isinstance(a, Sphere) and isinstance(b, Sphere):
                    self._sphere_sphere(a, b)
        for b in self.bodies:
            for axis, sign, limit, normal in self._walls():
                self._wall_contact(b, axis, sign, limit, normal)
    def _sphere_sphere(self, a, b):
        d = b.pos - a.pos; dist = np.linalg.norm(d)
        rsum = a.r + b.r
        if dist >= rsum or dist == 0: return
        n = d/dist
        pen = rsum - dist
        a.pos -= n*pen*0.5; b.pos += n*pen*0.5
        vrel = np.dot(b.vel - a.vel, n)
        if vrel > 0: return
        e = min(a.e, b.e)
        jn = -(1+e)*vrel / (1/a.mass + 1/b.mass)
        a.vel -= n*(jn/a.mass); b.vel += n*(jn/b.mass)
        vt = (b.vel - a.vel) - np.dot(b.vel - a.vel, n)*n
        sp = np.linalg.norm(vt)
        if sp > 1e-9:
            mu = min(a.mu, b.mu)
            jt = min(mu*jn, sp/(1/a.mass + 1/b.mass))
            t = vt/sp
            a.vel -= t*(jt/a.mass); b.vel += t*(jt/b.mass)
    def _wall_contact(self, b, axis, sign, limit, normal):
        rad = b.r if hasattr(b, "r") else float(np.min(b.half))
        s = b.pos[{"x":0,"y":1,"z":2}[axis]] * sign
        pen = (s + rad) - limit
        if pen <= 0: return
        vn = np.dot(b.vel, normal)   # <0 => Bewegung in die Wand
        if vn >= 0: return
        b.vel -= (1+b.e)*vn*normal
        vt = b.vel - np.dot(b.vel, normal)*normal
        sp = np.linalg.norm(vt)
        if sp > 1e-9:
            jt = min(b.mu*abs((1+b.e)*vn), sp)
            b.vel -= vt/sp*jt
        b.pos += normal*pen

class TimeLoop:
    """Akkumulator-Muster (Spec §5): feste dt, Substep-Obergrenze."""
    def __init__(self, world):
        self.world = world
        self.dt = float(world.cfg.solver["dt"])
        self.max_sub = int(world.cfg.solver["substep_max"])
        self._acc = 0.0
        self.substeps_done = 0
    def advance(self, real_dt: float) -> int:
        self._acc += real_dt
        n = min(int(self._acc / self.dt), self.max_sub)
        # v0.3a-Perf: Koerper-Substeps ohne Fluidaufruf; der Fluidschritt
        # wird einmal mit der Summe aller Substeps aufgerufen. Die interne
        # CFL-Unterteilung des Fluidsolvers erzeugt dieselben SPH-Substeps
        # wie zuvor - nur Sortier-/Transferzyklen gehen von 4 auf 1 runter.
        for _ in range(n): self.world.step(self.dt, step_fluid=False)
        if n > 0:
            self.world.fluid.step(n * self.dt)
        self._acc -= n*self.dt
        if self._acc > self.max_sub*self.dt: self._acc = 0.0  # Spiral-of-Death-Schutz
        self.substeps_done += n
        return n
