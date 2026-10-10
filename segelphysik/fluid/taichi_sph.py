"""Taichi/GPU-SPH (v0.3a) - beschleunigter Wasserkern fuer Echtzeit.

Physik wie die NumPy-Referenz (core/sph.py): WCSPH mit Kontinuitaetsdichte,
Monaghan-Viskositaet, Tensil-Spielraum, CFL-Substepping. Unterschied: die
Wandbehandlung erfolgt durch STATISCHE WAND-PARTIKEL (Standard-Boundary-
Methode) statt Spiegel-Geistern - deterministisch, GPU-freundlich und ohne die
O(N^2)-Pathologie des Zell-Clampings der Referenz.

Interface: identisch zu FluidSolver (core/fluid.py) -> austauschbar (Spec 7.1).

Determinismus (K9): Zellsortierung deterministisch auf der CPU (stabiles
argsort nach Index), Nachbarsummen in fester Reihenfolge -> zwei Laeufe
bit-identisch. GPU-seitige Slot-Belegung per Atomic wuerde die Summations-
reihenfolge variieren und K9 verletzen.

Backend: Vulkan (AMD/Intel/NVIDIA) mit CPU-Fallback.
Windows/Python 3.10-3.14:  pip install taichi-forge
"""
import numpy as np
try:
    import taichi_forge as ti   # Fork: Python 3.10-3.14, Vulkan
except ImportError:
    import taichi as ti         # upstream (Python <= 3.10)

from ..core.fluid import FluidSolver

SIGMA = 1.0 / np.pi
_STATE = {"init": False, "backend": "?"}


@ti.func
def _w(q):
    r = 0.0
    if q < 1.0:
        r = 1.0 - 1.5 * q * q + 0.75 * q * q * q
    elif q < 2.0:
        t = 2.0 - q
        r = 0.25 * t * t * t
    return r


@ti.func
def _dw(q):
    r = 0.0
    if q < 1.0:
        r = -3.0 * q + 2.25 * q * q
    elif q < 2.0:
        t = 2.0 - q
        r = -0.75 * t * t
    return r


def _w_py(q):
    if q < 1.0:
        return 1.0 - 1.5 * q * q + 0.75 * q * q * q
    if q < 2.0:
        t = 2.0 - q
        return 0.25 * t * t * t
    return 0.0


@ti.data_oriented
class TaichiSphWater(FluidSolver):
    """WCSPH in Taichi. Gleiche Schnittstelle wie core.sph.SphWater."""

    def __init__(self, cfg, arch=None):
        self.dx = float(cfg.dx)
        self.h = float(cfg.sph.get("h_factor", 1.3)) * self.dx
        self.rho0 = float(cfg.water["rho"])
        self.depth = float(cfg.water["depth"])
        self.lx = float(cfg.basin["lx"])
        self.ly = float(cfg.basin["ly"])
        self.c = float(cfg.sph.get("sound_speed", 60.0))
        self.alpha = float(cfg.sph.get("art_visc", 0.1))
        self.tensile_frac = float(cfg.sph.get("tensile_frac", 0.02))
        self.cfl = float(cfg.sph["cfl"])
        self.cfl_ac = float(cfg.sph.get("cfl_acoustic", 0.2))
        self.sub_max = int(cfg.sph.get("substep_fluid_max", 50))
        self.mass = self.rho0 * self.dx ** 3
        self._h2 = self.h * self.h
        self._W0 = SIGMA / self.h ** 3
        self._p_min = -self.tensile_frac * self.rho0 * self.c ** 2
        self._c2 = self.c * self.c

        if not _STATE["init"]:
            if arch is None:
                try:
                    ti.init(arch=ti.vulkan)
                    _STATE["backend"] = "vulkan"
                except Exception:
                    ti.init(arch=ti.cpu)
                    _STATE["backend"] = "cpu"
            else:
                ti.init(arch=ti.vulkan if arch == "vulkan" else ti.cpu)
                _STATE["backend"] = arch
            _STATE["init"] = True
        self.backend = _STATE["backend"]

        nx = int(round(self.lx / self.dx))
        ny = int(round(self.ly / self.dx))
        nz = int(round(self.depth / self.dx))
        xs = -self.lx / 2 + (np.arange(nx) + 0.5) * self.dx
        ys = -self.ly / 2 + (np.arange(ny) + 0.5) * self.dx
        zs = -self.depth + (np.arange(nz) + 0.5) * self.dx
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
        fluid = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
        self.N = fluid.shape[0]

        wall = self._make_walls()
        self.NW = wall.shape[0]
        self.M = self.N + self.NW
        pos_np = np.vstack([fluid, wall]).astype(np.float32)

        self.cs = 2.0 * self.h
        self.gx0 = -self.lx / 2 - 2 * self.h
        self.gy0 = -self.ly / 2 - 2 * self.h
        self.gz0 = -self.depth - 2 * self.h
        self.ncx = max(int(np.ceil((self.lx + 4 * self.h) / self.cs)), 1)
        self.ncy = max(int(np.ceil((self.ly + 4 * self.h) / self.cs)), 1)
        self.ncz = max(int(np.ceil((self.depth + 4 * self.h) / self.cs)), 1)
        self.ncells = self.ncx * self.ncy * self.ncz

        self.pos = ti.Vector.field(3, ti.f32, shape=self.M)
        self.vel = ti.Vector.field(3, ti.f32, shape=self.M)
        self.rho = ti.field(ti.f32, shape=self.M)
        self.acc = ti.Vector.field(3, ti.f32, shape=self.N)
        self.drho = ti.field(ti.f32, shape=self.N)
        self.rho_sum = ti.field(ti.f32, shape=self.N)
        self.cell = ti.field(ti.i32, shape=self.M)
        self.order = ti.field(ti.i32, shape=self.M)
        self.cnt = ti.field(ti.i32, shape=self.ncells + 1)
        self.start = ti.field(ti.i32, shape=self.ncells + 1)
        self.cur = ti.field(ti.i32, shape=self.ncells + 1)
        self.vmax = ti.field(ti.f32, shape=())
        self.gf = ti.field(ti.f32, shape=())
        self.gf[None] = float(cfg.g)

        # v0.3f: Koerper fuer einseitige Ausschlusskollision (Alternative 2):
        # Partikel werden aus Koerpervolumen herausprojiziert, OHNE
        # Rueckkraft auf den Koerper (Auftrieb/Drag bleiben beim
        # Kontinuum-Modell aus forces.py - keine Doppelberechnung).
        self.MAXB = 32
        self._col_margin = 0.5 * self.dx
        self.n_sph = ti.field(ti.i32, shape=())
        self.sph_c = ti.Vector.field(3, ti.f32, shape=self.MAXB)
        self.sph_r = ti.field(ti.f32, shape=self.MAXB)
        self.n_box = ti.field(ti.i32, shape=())
        self.box_c = ti.Vector.field(3, ti.f32, shape=self.MAXB)
        self.box_h = ti.Vector.field(3, ti.f32, shape=self.MAXB)
        self.box_q = ti.Vector.field(4, ti.f32, shape=self.MAXB)
        self.n_sph[None] = 0
        self.n_box[None] = 0

        self.pos.from_numpy(pos_np)
        self.vel.fill(0.0)
        self.rho.fill(self.rho0)
        self.last_n_substeps = 0
        self._pos_np = pos_np[:self.N].astype(np.float64)
        self._vel_np = np.zeros((self.N, 3))
        self._rho_np = np.full(self.N, self.rho0)

        self._sort()
        self._k_summation()
        rs = self.rho_sum.to_numpy()
        d = np.maximum(-pos_np[:self.N, 2], 0.0)
        self.rho.from_numpy(
            np.concatenate([rs + self.rho0 * float(cfg.g) * d / self._c2,
                            np.full(self.NW, self.rho0)]).astype(np.float32))
        self._sort()
        self._pull()

    def _make_walls(self):
        dx, t = self.dx, 2.0 * self.h
        lx, ly, d = self.lx, self.ly, self.depth
        parts = []
        xs = np.arange(-lx / 2 + dx / 2, lx / 2, dx)
        ys = np.arange(-ly / 2 + dx / 2, ly / 2, dx)
        zs = np.arange(-d - t + dx / 2, -d, dx)
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
        parts.append(np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1))
        xs = np.concatenate([np.arange(-lx / 2 - t + dx / 2, -lx / 2, dx),
                             np.arange(lx / 2 + dx / 2, lx / 2 + t, dx)])
        ys = np.arange(-ly / 2 + dx / 2, ly / 2, dx)
        zs = np.arange(-d + dx / 2, 0.0, dx)
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
        parts.append(np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1))
        xs = np.arange(-lx / 2 + dx / 2, lx / 2, dx)
        ys = np.concatenate([np.arange(-ly / 2 - t + dx / 2, -ly / 2, dx),
                             np.arange(ly / 2 + dx / 2, ly / 2 + t, dx)])
        zs = np.arange(-d + dx / 2, 0.0, dx)
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
        parts.append(np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1))
        return np.vstack(parts)

    @property
    def n_particles(self):
        return self.N

    @property
    def g(self):
        return float(self.gf[None])

    @g.setter
    def g(self, v):
        self.gf[None] = float(v)

    def get_state(self):
        return (self._pos_np.copy(), self._vel_np.copy(), self._rho_np.copy())

    def _pull(self):
        self._pos_np = self.pos.to_numpy()[:self.N].astype(np.float64)
        self._vel_np = self.vel.to_numpy()[:self.N].astype(np.float64)
        self._rho_np = self.rho.to_numpy()[:self.N].astype(np.float64)

    def _push(self):
        v = self.vel.to_numpy()
        v[:self.N] = self._vel_np.astype(np.float32)
        self.vel.from_numpy(v)

    @ti.func
    def _cell_of(self, p):
        ix = ti.cast(ti.floor((p[0] - self.gx0) / self.cs), ti.i32)
        iy = ti.cast(ti.floor((p[1] - self.gy0) / self.cs), ti.i32)
        iz = ti.cast(ti.floor((p[2] - self.gz0) / self.cs), ti.i32)
        ix = ti.max(0, ti.min(ix, self.ncx - 1))
        iy = ti.max(0, ti.min(iy, self.ncy - 1))
        iz = ti.max(0, ti.min(iz, self.ncz - 1))
        return (ix * self.ncy + iy) * self.ncz + iz

    def _sort(self):
        """Deterministisches Sortieren auf der CPU (stabil nach Partikelindex).

        Die Vulkan-Atomics liefern korrekte Zellcounts, aber die Reihenfolge,
        in der die Slots belegt werden, haengt vom GPU-Zeitplan ab. Damit
        variiert die Summationsreihenfolge der Nachbarn -> Float-Rundungs-
        unterschiede -> K9 (Determinismus) verletzt. Das stabile argsort in
        numpy garantiert bit-identische Sortierung bei jedem Lauf; der
        Transfer von M Indizes pro Substep ist dagegen vernachlaessigbar.
        """
        p = self.pos.to_numpy()
        cx = np.clip(np.floor((p[:, 0] - self.gx0) / self.cs).astype(np.int64),
                     0, self.ncx - 1)
        cy = np.clip(np.floor((p[:, 1] - self.gy0) / self.cs).astype(np.int64),
                     0, self.ncy - 1)
        cz = np.clip(np.floor((p[:, 2] - self.gz0) / self.cs).astype(np.int64),
                     0, self.ncz - 1)
        cell = (cx * self.ncy + cy) * self.ncz + cz
        order = np.argsort(cell, kind="stable").astype(np.int32)
        counts = np.bincount(cell, minlength=self.ncells)
        start = np.zeros(self.ncells + 1, dtype=np.int32)
        start[1:] = np.cumsum(counts).astype(np.int32)
        self.cell.from_numpy(cell.astype(np.int32))
        self.order.from_numpy(order)
        self.start.from_numpy(start)

    @ti.kernel
    def _k_summation(self):
        for i in range(self.N):
            pi = self.pos[i]
            ci = self.cell[i]
            cx = ci // (self.ncy * self.ncz)
            cy = (ci // self.ncz) % self.ncy
            cz = ci % self.ncz
            s = self.mass * self._W0
            for ox in ti.static(range(-1, 2)):
                for oy in ti.static(range(-1, 2)):
                    for oz in ti.static(range(-1, 2)):
                        nx = cx + ox
                        ny = cy + oy
                        nz = cz + oz
                        if 0 <= nx < self.ncx and 0 <= ny < self.ncy and 0 <= nz < self.ncz:
                            c = (nx * self.ncy + ny) * self.ncz + nz
                            for k in range(self.start[c], self.start[c + 1]):
                                j = self.order[k]
                                if j != i:
                                    r = (pi - self.pos[j]).norm()
                                    if r < 2.0 * self.h:
                                        s += self.mass * SIGMA / self.h ** 3 * _w(r / self.h)
            self.rho_sum[i] = s

    @ti.kernel
    def _k_vmax(self):
        for i in range(self.N):
            ti.atomic_max(self.vmax[None], self.vel[i].norm())

    @ti.func
    def _qrot(self, q, v):
        """Rotation von v mit Quaternion q=(w,x,y,z) - identische
        Konvention wie bodies.quat_rotate."""
        w = q[0]
        x = q[1]
        y = q[2]
        z = q[3]
        t = 2.0 * ti.Vector([y * v[2] - z * v[1],
                             z * v[0] - x * v[2],
                             x * v[1] - y * v[0]])
        return v + w * t + ti.Vector([x, y, z]).cross(t)

    def set_bodies(self, bodies):
        """Uebergibt die aktuellen Koerper an den Kollisionskernel
        (vom Solver einmal pro Fluidschritt aufgerufen). Die Felder
        sind MAXB-gross; taichi.from_numpy verlangt exakte Formen,
        daher wird bis MAXB mit Nullen aufgefuellt (unbenutzte
        Slots werden vom Kernel nie erreicht, da n_* die Schleifen
        begrenzt)."""
        s = [b for b in bodies if hasattr(b, "r")][:self.MAXB]
        bx = [b for b in bodies if hasattr(b, "half")][:self.MAXB]
        ns, nb = len(s), len(bx)
        self.n_sph[None] = ns
        self.n_box[None] = nb
        cs = np.zeros((self.MAXB, 3), dtype=np.float32)
        rs = np.zeros(self.MAXB, dtype=np.float32)
        if ns:
            cs[:ns] = np.array([b.pos for b in s], dtype=np.float32)
            rs[:ns] = np.array([b.r for b in s], dtype=np.float32)
        self.sph_c.from_numpy(cs)
        self.sph_r.from_numpy(rs)
        cb = np.zeros((self.MAXB, 3), dtype=np.float32)
        hb = np.zeros((self.MAXB, 3), dtype=np.float32)
        qb = np.zeros((self.MAXB, 4), dtype=np.float32)
        qb[:, 0] = 1.0  # Identitaets-Quaternion fuer unbenutzte Slots
        if nb:
            cb[:nb] = np.array([b.pos for b in bx], dtype=np.float32)
            hb[:nb] = np.array([b.half for b in bx], dtype=np.float32)
            qb[:nb] = np.array([b.q for b in bx], dtype=np.float32)
        self.box_c.from_numpy(cb)
        self.box_h.from_numpy(hb)
        self.box_q.from_numpy(qb)

    @ti.kernel
    def _k_body_collision(self):
        """Einseitige Ausschlusskollision (v0.3f, Alternative 2):
        Fluid-Partikel, die in einen Koerper eindringen, werden auf
        die Oberflaeche projiziert (Kugel: radiale Projektion, Box:
        Push-out entlang der tiefsten Penetrationsachse im Koerper-
        frame) und ihre Einstrom-Geschwindigkeit genullt. Keine
        Rueckkraft auf den Koerper - die Fluidwirkung auf den
        Koerper liefert ausschliesslich das Kontinuum-Modell
        (Archimedes + Drag aus forces.py)."""
        for i in range(self.N):
            # v0.4: nur Fluid-Partikel (0..N); Wandpartikel (N..M) sind
            # statisch und koennen nicht mit Koerpern kollidieren
            p = self.pos[i]
            v = self.vel[i]
            m = self._col_margin
            for j in range(self.n_sph[None]):
                c = self.sph_c[j]
                rr = self.sph_r[j] + m
                d = p - c
                dist = d.norm()
                if dist < rr and dist > 1e-9:
                    n = d / dist
                    p = c + n * rr
                    vn = v.dot(n)
                    if vn < 0.0:
                        v = v - vn * n
            for j in range(self.n_box[None]):
                c = self.box_c[j]
                hh = self.box_h[j]
                q = self.box_q[j]
                qc = ti.Vector([q[0], -q[1], -q[2], -q[3]])
                pl = self._qrot(qc, p - c)
                ex = abs(pl[0]) - (hh[0] + m)
                ey = abs(pl[1]) - (hh[1] + m)
                ez = abs(pl[2]) - (hh[2] + m)
                # Taichi: Variablen, die nach der Verzweigung benutzt
                # werden, muessen VOR der Verzweigung deklariert sein
                nl = ti.Vector([0.0, 0.0, 0.0])
                if ex < 0.0 and ey < 0.0 and ez < 0.0:
                    if ex >= ey and ex >= ez:
                        sgn = 1.0 if pl[0] >= 0.0 else -1.0
                        pl = ti.Vector([sgn * (hh[0] + m), pl[1], pl[2]])
                        nl = ti.Vector([sgn, 0.0, 0.0])
                    elif ey >= ez:
                        sgn = 1.0 if pl[1] >= 0.0 else -1.0
                        pl = ti.Vector([pl[0], sgn * (hh[1] + m), pl[2]])
                        nl = ti.Vector([0.0, sgn, 0.0])
                    else:
                        sgn = 1.0 if pl[2] >= 0.0 else -1.0
                        pl = ti.Vector([pl[0], pl[1], sgn * (hh[2] + m)])
                        nl = ti.Vector([0.0, 0.0, sgn])
                    nw = self._qrot(q, nl)
                    p = c + self._qrot(q, pl)
                    vn = v.dot(nw)
                    if vn < 0.0:
                        v = v - vn * nw
            self.pos[i] = p
            self.vel[i] = v

    def step(self, dt):
        self._push()
        self.vmax[None] = 0.0
        self._k_vmax()
        vm = max(float(self.vmax[None]), 1e-6)
        dt_ac = min(self.cfl_ac * self.h / self.c, self.cfl * self.h / vm)
        n = min(int(np.ceil(dt / dt_ac)), self.sub_max)
        self.last_n_substeps = n
        dts = dt / n
        # v0.3a-Perf: Sortierung einmal pro step()-Aufruf statt pro internem
        # Substep - die Nachbarschaft bleibt ueber einen Frame gueltig (Partikel
        # bewegen sich deutlich weniger als h). Spart 12 von 16 CPU-Sortier-
        # zyklen pro Frame. Physik unveraendert (gleiche Kernel-Reihenfolge).
        self._sort()
        for _ in range(n):
            self._k_density(dts)
            self._k_force(dts)
            self._k_integrate(dts)
            self._k_body_collision()
        self._pull()

    @ti.kernel
    def _k_density(self, dt: ti.f32):
        for i in range(self.N):
            pi = self.pos[i]
            vi = self.vel[i]
            ci = self.cell[i]
            cx = ci // (self.ncy * self.ncz)
            cy = (ci // self.ncz) % self.ncy
            cz = ci % self.ncz
            s = 0.0
            for ox in ti.static(range(-1, 2)):
                for oy in ti.static(range(-1, 2)):
                    for oz in ti.static(range(-1, 2)):
                        nx = cx + ox
                        ny = cy + oy
                        nz = cz + oz
                        if 0 <= nx < self.ncx and 0 <= ny < self.ncy and 0 <= nz < self.ncz:
                            c = (nx * self.ncy + ny) * self.ncz + nz
                            for k in range(self.start[c], self.start[c + 1]):
                                j = self.order[k]
                                if j != i:
                                    d = pi - self.pos[j]
                                    r = d.norm()
                                    if r < 2.0 * self.h:
                                        gw = SIGMA / self.h ** 4 * _dw(r / self.h) / ti.max(r, 1e-12)
                                        s += self.mass * (vi - self.vel[j]).dot(d) * gw
            self.drho[i] = s

    @ti.kernel
    def _k_force(self, dt: ti.f32):
        for i in range(self.N):
            self.rho[i] += self.drho[i] * dt
            pi = self.pos[i]
            vi = self.vel[i]
            ri = self.rho[i]
            ci = self.cell[i]
            cx = ci // (self.ncy * self.ncz)
            cy = (ci // self.ncz) % self.ncy
            cz = ci % self.ncz
            a = ti.Vector([0.0, 0.0, -self.gf[None]])
            for ox in ti.static(range(-1, 2)):
                for oy in ti.static(range(-1, 2)):
                    for oz in ti.static(range(-1, 2)):
                        nx = cx + ox
                        ny = cy + oy
                        nz = cz + oz
                        if 0 <= nx < self.ncx and 0 <= ny < self.ncy and 0 <= nz < self.ncz:
                            c = (nx * self.ncy + ny) * self.ncz + nz
                            for k in range(self.start[c], self.start[c + 1]):
                                j = self.order[k]
                                if j != i:
                                    d = pi - self.pos[j]
                                    r = d.norm()
                                    if r < 2.0 * self.h:
                                        gw = SIGMA / self.h ** 4 * _dw(r / self.h) / ti.max(r, 1e-12)
                                        rj = self.rho[j]
                                        pj = ti.max(self._c2 * (rj - self.rho0), self._p_min)
                                        p_i = ti.max(self._c2 * (ri - self.rho0), self._p_min)
                                        fp = -self.mass * (p_i / (ri * ri) + pj / (rj * rj)) * gw * d
                                        rv = (vi - self.vel[j]).dot(d)
                                        mu = 0.0
                                        if rv < 0.0:
                                            mu = self.h * rv / (r * r + 0.01 * self._h2)
                                        rb = 0.5 * (ri + rj)
                                        fv = -self.mass * (-self.alpha * self.c * mu / rb) * gw * d
                                        a += fp + fv
            self.acc[i] = a

    @ti.kernel
    def _k_integrate(self, dt: ti.f32):
        for i in range(self.N):
            self.vel[i] += self.acc[i] * dt
            self.pos[i] += self.vel[i] * dt
            lo0 = -self.lx / 2 + 1e-6
            hi0 = self.lx / 2 - 1e-6
            lo1 = -self.ly / 2 + 1e-6
            hi1 = self.ly / 2 - 1e-6
            lo2 = -self.depth + 1e-6
            if self.pos[i][0] < lo0:
                self.pos[i][0] = lo0
                if self.vel[i][0] < 0:
                    self.vel[i][0] = 0.0
            if self.pos[i][0] > hi0:
                self.pos[i][0] = hi0
                if self.vel[i][0] > 0:
                    self.vel[i][0] = 0.0
            if self.pos[i][1] < lo1:
                self.pos[i][1] = lo1
                if self.vel[i][1] < 0:
                    self.vel[i][1] = 0.0
            if self.pos[i][1] > hi1:
                self.pos[i][1] = hi1
                if self.vel[i][1] > 0:
                    self.vel[i][1] = 0.0
            if self.pos[i][2] < lo2:
                self.pos[i][2] = lo2
                if self.vel[i][2] < 0:
                    self.vel[i][2] = 0.0

    def density_at(self, pos):
        p = np.asarray(pos, dtype=np.float64)
        d = self._pos_np - p
        r = np.sqrt(np.einsum("ij,ij->i", d, d))
        m = r < 2.0 * self.h
        if not np.any(m):
            return 0.0
        W = SIGMA / self.h ** 3 * np.array([_w_py(x / self.h) for x in r[m]])
        num = np.sum(self.mass * W)
        den = np.sum(self.mass / self._rho_np[m] * W)
        return float(num / den) if den > 0 else 0.0

    def velocity_at(self, pos):
        p = np.asarray(pos, dtype=np.float64)
        d = self._pos_np - p
        r = np.sqrt(np.einsum("ij,ij->i", d, d))
        m = r < 2.0 * self.h
        if not np.any(m):
            return np.zeros(3)
        W = self.mass * SIGMA / self.h ** 3 * np.array([_w_py(x / self.h) for x in r[m]])
        den = np.sum(W)
        if den <= 0:
            return np.zeros(3)
        return (W[:, None] * self._vel_np[m]).sum(0) / den

    def apply_body_force(self, pos, force, dt):
        p = np.asarray(pos, dtype=np.float64)
        f = np.asarray(force, dtype=np.float64)
        if np.linalg.norm(f) == 0.0:
            return
        d = self._pos_np - p
        r = np.sqrt(np.einsum("ij,ij->i", d, d))
        m = r < 2.0 * self.h
        if not np.any(m):
            return
        W = SIGMA / self.h ** 3 * np.array([_w_py(x / self.h) for x in r[m]])
        s = float(np.sum(W))
        if s <= 0:
            return
        self._vel_np[m] += (W / s)[:, None] * (dt * f / self.mass)
