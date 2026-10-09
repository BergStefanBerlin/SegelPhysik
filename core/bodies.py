"""Starre Körper: Body-Basisklasse, Sphere, Box (Spec §4, Plan Issue 2)."""
import numpy as np

def quat_mul(a, b):
    w1,x1,y1,z1 = a; w2,x2,y2,z2 = b
    return np.array([w1*w2 - x1*x2 - y1*y2 - z1*z2,
                     w1*x2 + x1*w2 + y1*z2 - z1*y2,
                     w1*y2 - x1*z2 + y1*w2 + z1*x2,
                     w1*z2 + x1*y2 - y1*x2 + z1*w2])
def quat_rotate(q, v):
    w,x,y,z = q; vx,vy,vz = v
    tx = 2*(y*vz - z*vy); ty = 2*(z*vx - x*vz); tz = 2*(x*vy - y*vx)
    return v + w*np.array([tx,ty,tz]) + np.cross([x,y,z], [tx,ty,tz])
def quat_normalize(q): return q / np.linalg.norm(q)
def quat_integrate(q, omega, dt):
    """dq/dt = 0.5 * omega_quat * q (omega im Weltframe)."""
    wq = np.array([0.0, omega[0], omega[1], omega[2]])
    return quat_normalize(q + dt * 0.5 * quat_mul(wq, q))

class Body:
    """Basisklasse aller starren Körper (Shape-Interface, Spec §7.1)."""
    def __init__(self, mass, density, mu=0.5, e=0.3,
                 position=(0,0,0), velocity=(0,0,0),
                 orientation=(1,0,0,0), angular_velocity=(0,0,0)):
        self.mass = float(mass); self.density = float(density)
        self.mu = float(mu); self.e = float(e)
        self.pos = np.asarray(position, float)
        self.vel = np.asarray(velocity, float)
        self.q = quat_normalize(np.asarray(orientation, float))
        self.omega = np.asarray(angular_velocity, float)
        self.force = np.zeros(3); self.torque = np.zeros(3)
    def volume(self): raise NotImplementedError
    def submerged_volume(self, waterline): raise NotImplementedError
    def a_ref(self, direction): raise NotImplementedError
    def characteristic_dim(self): raise NotImplementedError
    def inertia_diag(self): raise NotImplementedError
    def apply_force(self, force, at=None):
        self.force += np.asarray(force, float)
        if at is not None:
            self.torque += np.cross(np.asarray(at, float) - self.pos, force)

class Sphere(Body):
    def __init__(self, radius, density, **kw):
        super().__init__(mass=(4.0/3.0)*np.pi*radius**3*density, density=density, **kw)
        self.r = float(radius)
    def volume(self): return (4.0/3.0)*np.pi*self.r**3
    def submerged_volume(self, waterline):
        """Volumen unterhalb der Ebene z=waterline (Kugelkappe, analytisch)."""
        d = waterline - self.pos[2]; r = self.r
        if d <= -r: return 0.0
        if d >= r:  return self.volume()
        if d >= 0:
            h = r - d   # Kappe oberhalb der Ebene
            return self.volume() - np.pi*h*h*(r - h/3.0)
        h = r + d   # eingetauchte untere Kappe
        return np.pi*h*h*(r - h/3.0)
    def a_ref(self, direction):
        if np.linalg.norm(direction) == 0: return 0.0
        return np.pi*self.r**2
    def characteristic_dim(self): return 2.0*self.r
    def inertia_diag(self):
        i = 0.4*self.mass*self.r**2
        return np.array([i,i,i])

class Box(Body):
    """Quader. Vereinfachung (dokumentiert in ARCHITECTURE.md):
    Teilvolumen achsenparallel; Rotationsanteil vernachlässigt (v0.2)."""
    def __init__(self, edges, density, **kw):
        super().__init__(mass=float(np.prod(edges))*density, density=density, **kw)
        self.half = np.asarray(edges, float)/2.0
    def volume(self): return float(8*np.prod(self.half))
    def submerged_volume(self, waterline):
        lo = self.pos[2]-self.half[2]; hi = self.pos[2]+self.half[2]
        sub = max(0.0, min(2*self.half[2], min(hi, waterline) - lo))
        return self.volume() * sub/(2*self.half[2])
    def a_ref(self, direction):
        d = np.abs(np.asarray(direction, float)); n = np.linalg.norm(d)
        if n == 0: return 0.0
        d = d/n; a,b,c = self.half
        return 4.0*(a*b*d[2] + a*c*d[1] + b*c*d[0])
    def characteristic_dim(self): return float(2*np.min(self.half))
    def inertia_diag(self):
        ex,ey,ez = 2*self.half; m = self.mass
        return np.array([m/12*(ey**2+ez**2), m/12*(ex**2+ez**2), m/12*(ex**2+ey**2)])
