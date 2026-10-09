"""WCSPH-Wasserkern - NumPy-Referenzimplementierung (M2, Plan Issue 5-7).

Spec-Bezug:
  §2  Wasser: rho=1000 kg/m³, Oberfläche z=0, Wasser z in [-depth, 0]
  §5  fester Zeitschritt mit Substepping: akustisches CFL im Inneren
      (dt_akustisch = cfl_ac*h/c; advektives CFL = cfl*h/vmax)
  §7.1 implementiert das FluidSolver-Interface (core/fluid.py)
  K3: hydrostatisches Druckprofil   K9: Determinismus < 1e-9

Physik/Numerik:
  - Kubischer-Spline-Kernel (3D), h = h_factor*dx, Stützlänge 2h
  - Lineare Zustandsgleichung p = c²*(rho - rho0); Default c = 60 m/s
    (EOS-Kompressibilitätsfehler über die Default-Tiefe 3 m: ~0,41 %)
  - Dichte-Entwicklung über die Kontinuitätsgleichung
    drho/dt = Σ m_j (v_i - v_j)·∇W_ij (WCSPH, Monaghan 1992).
    Begründung: Neuberechnung per Summation mit Shepard-Normalisierung
    glättet die hydrostatische Schichtung weg und zerstört die
    Druckgradient-Gravitation-Balance.
  - Initialisierung: Startdichte = Summationsdichte des Partikelgitters
    (inkl. Ghosts, Selbstterm) + hydrostatischer Offset rho0*g*d/c²;
    danach Einschwingen (Settle-Phase mit erhöhter künstlicher Viskosität).
  - Tensil-Spielraum: Druck wird nicht bei 0 geklemmt, sondern bei
    -tensile_frac*rho0*c². Verhindert das Auseinanderfallen der obersten
    Partikelschichten an der freien Oberfläche. Kalibriert: 0.02.
  - Bekannte Diskretisierungseigenschaft: An der freien Oberfläche fehlt
    Kernel-Unterstützung -> konstantes Dichte-/Druck-Offset. Das
    hydrostatische DRUCKPROFIL (Gradient dp/dz = -rho0*g) ist davon
    unberührt; K3 wird über den Druckgradienten zwischen zwei Tiefen
    validiert (zeitgemittelt).
  - Spiegel-Partikel (Ghosts) an Boden und Seitenwänden (Oberseite offen,
    §1), Normalkomponente der Geschwindigkeit gespiegelt (Gleitbedingung)
  - Zelllisten-Nachbarsuche ohne Wrap-Artefakt, deterministisch (K9);
    Paar-Kräfte via bincount-Scatter auf Ziel-Partikel
  - Künstliche Viskosität (Monaghan): Pi_ij = -alpha*c*mu/rho_bar,
    Kraft auf i: -m_j*Pi_ij*∇W_ij (dämpfend); eta (Spec §2) informativ

Performance: NumPy-Referenz für Korrektheit/Tests (CPU, kleine
Konfigurationen). Taichi/GPU-Portierung folgt im selben Meilenstein;
Schnittstelle identisch.
"""
import numpy as np
from .fluid import FluidSolver

_SIGMA = 1.0 / np.pi


def _w(q):
    """Skalarer Anteil des Kubischen Splines, q = r/h."""
    w = np.zeros_like(q)
    m1 = q < 1.0
    m2 = (q >= 1.0) & (q < 2.0)
    q1 = q[m1]; q2 = q[m2]
    w[m1] = 1.0 - 1.5*q1*q1 + 0.75*q1*q1*q1
    w[m2] = 0.25*(2.0 - q2)**3
    return w


def _dw_dq(q):
    d = np.zeros_like(q)
    m1 = q < 1.0
    m2 = (q >= 1.0) & (q < 2.0)
    q1 = q[m1]; q2 = q[m2]
    d[m1] = -3.0*q1 + 2.25*q1*q1
    d[m2] = -0.75*(2.0 - q2)**2
    return d


class SphWater(FluidSolver):
    """WCSPH-Wasserbecken (Quader, Oberfläche z=0, Boden z=-depth)."""

    def __init__(self, cfg):
        self.dx = cfg.dx
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
        self.g = float(cfg.g)

        self.mass = self.rho0 * self.dx**3

        nx = int(round(self.lx/self.dx))
        ny = int(round(self.ly/self.dx))
        nz = int(round(self.depth/self.dx))
        xs = -self.lx/2.0 + (np.arange(nx)+0.5)*self.dx
        ys = -self.ly/2.0 + (np.arange(ny)+0.5)*self.dx
        zs = -self.depth + (np.arange(nz)+0.5)*self.dx
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
        self.pos = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
        self.vel = np.zeros_like(self.pos)
        self.n_real = self.pos.shape[0]

        self.last_n_substeps = 0
        self._h2 = self.h*self.h
        self._W0 = _SIGMA/self.h**3
        self._p_min = -self.tensile_frac*self.rho0*self.c**2

        # SPH-konsistente Initialisierung. Vorbelegung von self.rho ist
        # noetig, weil _make_ghosts (in _summation_density) self.rho liest.
        self.rho = np.full(self.n_real, self.rho0)
        rho_sum = self._summation_density(self.pos)
        d_surf = np.maximum(-self.pos[:, 2], 0.0)
        self.rho = rho_sum + self.rho0*self.g*d_surf/self.c**2

    @property
    def n_particles(self):
        return self.n_real

    def _summation_density(self, positions):
        """rho_i = Σ_j m_j W_ij inkl. Selbstterm (nur Initialisierung)."""
        N = positions.shape[0]
        gp, gv, grho, gm = self._make_ghosts()
        Ng = gp.shape[0]
        pos_all = np.vstack([positions, gp]) if Ng else positions.copy()
        I, J = self._cell_pairs(pos_all)
        rij = pos_all[I] - pos_all[J]
        r = np.sqrt(np.einsum('ij,ij->i', rij, rij))
        m_k = r < 2.0*self.h
        I, J, r = I[m_k], J[m_k], r[m_k]
        Wk = _SIGMA/self.h**3 * _w(r/self.h)
        num = np.bincount(I, weights=self.mass*Wk, minlength=N+Ng)[:N]
        return self.mass*self._W0 + num

    def density_at(self, pos):
        """Shepard-interpolierte Dichte an einem Punkt (Abfrage für M3)."""
        pos = np.asarray(pos, dtype=float)
        d = self.pos - pos
        r = np.sqrt(np.einsum('ij,ij->i', d, d))
        m = r < 2.0*self.h
        if not np.any(m):
            return 0.0
        W = _SIGMA/self.h**3 * _w(r[m]/self.h)
        num = np.sum(self.mass*W)
        den = np.sum(self.mass/self.rho[m]*W)
        return num/den if den > 0 else 0.0

    def velocity_at(self, pos):
        """Shepard-gewichtete mittlere Fluidgeschwindigkeit (Abfrage M3)."""
        pos = np.asarray(pos, dtype=float)
        d = self.pos - pos
        r = np.sqrt(np.einsum('ij,ij->i', d, d))
        m = r < 2.0*self.h
        if not np.any(m):
            return np.zeros(3)
        W = self.mass*_SIGMA/self.h**3 * _w(r[m]/self.h)
        den = np.sum(W)
        if den <= 0:
            return np.zeros(3)
        return (W[:, None]*self.vel[m]).sum(axis=0)/den

    def step(self, dt):
        vmax = float(np.max(np.linalg.norm(self.vel, axis=1))) if self.n_real else 0.0
        dt_adv = self.cfl*self.h/max(vmax, 1e-6)
        dt_ac = min(self.cfl_ac*self.h/self.c, dt_adv)
        n = int(np.ceil(dt/dt_ac))
        if n > self.sub_max:
            n = self.sub_max
        self.last_n_substeps = n
        dt_sub = dt/n
        for _ in range(n):
            self._substep(dt_sub)

    def _make_ghosts(self):
        R2 = 2.0*self.h
        pos, vel, rho = self.pos, self.vel, self.rho
        gp, gv, gm = [], [], []
        specs = [('z', -self.depth, -1),
                 ('x', -self.lx/2.0, -1), ('x', self.lx/2.0, +1),
                 ('y', -self.ly/2.0, -1), ('y', self.ly/2.0, +1)]
        for axis, wall, side in specs:
            a = {'x': 0, 'y': 1, 'z': 2}[axis]
            near = (pos[:, a] - wall)*side < R2
            if not np.any(near):
                continue
            p = pos[near].copy()
            p[:, a] = 2.0*wall - p[:, a]
            v = vel[near].copy()
            v[:, a] *= -1.0
            gp.append(p); gv.append(v); gm.append(np.nonzero(near)[0])
        if gp:
            return (np.vstack(gp), np.vstack(gv),
                    np.concatenate([rho[i] for i in gm]),
                    np.concatenate(gm))
        e = np.zeros((0, 3))
        return e, e.copy(), np.zeros(0), np.zeros(0, dtype=int)

    def _cell_pairs(self, pos_all):
        h = self.h
        mins = np.array([-self.lx/2.0-2*h, -self.ly/2.0-2*h, -self.depth-2*h])
        ext = np.array([self.lx+4*h, self.ly+4*h, self.depth+4*h])
        nc = np.maximum(np.ceil(ext/h).astype(int), 1)
        ncells = int(nc[0])*int(nc[1])*int(nc[2])
        idx = np.floor((pos_all - mins)/h).astype(np.int64)
        idx = np.clip(idx, 0, nc-1)
        key = (idx[:, 0]*nc[1] + idx[:, 1])*nc[2] + idx[:, 2]
        order = np.argsort(key, kind='stable')
        key_s = key[order]
        starts = np.searchsorted(key_s, np.arange(ncells), side='left')
        ends = np.searchsorted(key_s, np.arange(ncells), side='right')
        I_parts, J_parts = [], []
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for oz in (-1, 0, 1):
                    nx = idx[:, 0]+ox; ny = idx[:, 1]+oy; nz = idx[:, 2]+oz
                    valid = ((nx >= 0) & (nx < nc[0]) &
                             (ny >= 0) & (ny < nc[1]) &
                             (nz >= 0) & (nz < nc[2]))
                    vi = np.nonzero(valid)[0]
                    if vi.size == 0:
                        continue
                    kk = (nx[vi]*nc[1] + ny[vi])*nc[2] + nz[vi]
                    s = starts[kk]; e = ends[kk]
                    counts = e - s
                    total = int(counts.sum())
                    if total == 0:
                        continue
                    rep = np.repeat(np.arange(vi.size), counts)
                    csum = np.concatenate([[0], np.cumsum(counts)])[:-1]
                    within = np.arange(total) - np.repeat(csum, counts)
                    I_parts.append(vi[rep]); J_parts.append(order[s[rep]+within])
        I = np.concatenate(I_parts); J = np.concatenate(J_parts)
        keep = I != J
        return I[keep], J[keep]

    def _substep(self, dt):
        N = self.n_real
        gp, gv, grho, gm = self._make_ghosts()
        Ng = gp.shape[0]
        pos_all = np.vstack([self.pos, gp]) if Ng else self.pos.copy()
        vel_all = np.vstack([self.vel, gv]) if Ng else self.vel.copy()
        rho_all = np.concatenate([self.rho, self.rho[gm]]) if Ng else self.rho.copy()

        I, J = self._cell_pairs(pos_all)
        rij = pos_all[I] - pos_all[J]
        r2 = np.einsum('ij,ij->i', rij, rij)
        r = np.sqrt(r2)
        m_k = r < 2.0*self.h
        I, J, rij, r2, r = I[m_k], J[m_k], rij[m_k], r2[m_k], r[m_k]
        q = r/self.h
        grad = _SIGMA/self.h**3 * _dw_dq(q)/self.h
        grad_vec = grad[:, None]*rij/np.maximum(r[:, None], 1e-12)

        # ---- Kontinuität: drho_i/dt = Σ m_j (v_i-v_j)·∇W_ij
        vij_dot_gw = np.einsum('ij,ij->i', vel_all[I] - vel_all[J], grad_vec)
        drho = np.bincount(I, weights=self.mass*vij_dot_gw, minlength=N+Ng)[:N]
        self.rho = self.rho + drho*dt
        rho_all = np.concatenate([self.rho, self.rho[gm]]) if Ng else self.rho.copy()

        # ---- Druck (lineare EOS, Tensil-Spielraum)
        p_all = self.c**2*(rho_all - self.rho0)
        p_all = np.maximum(p_all, self._p_min)

        # ---- Kräfte (nur reale Ziel-Partikel)
        sel = I < N
        It, Jt = I[sel], J[sel]
        gvt = grad_vec[sel]
        pi = p_all[It]/rho_all[It]**2
        pj = p_all[Jt]/rho_all[Jt]**2
        acc_p = -self.mass*(pi + pj)[:, None]*gvt

        rv = np.einsum('ij,ij->i', vel_all[It] - vel_all[Jt],
                       pos_all[It] - pos_all[Jt])
        mu = np.where(rv < 0.0,
                      self.h*rv/(r2[sel] + 0.01*self._h2), 0.0)
        rho_bar = 0.5*(rho_all[It] + rho_all[Jt])
        Pi = -self.alpha*self.c*mu/rho_bar
        acc_v = -self.mass*Pi[:, None]*gvt   # daempfend (Vorzeichen!)

        acc_pair = acc_p + acc_v
        acc = np.zeros((N, 3))
        for k in range(3):
            acc[:, k] = np.bincount(It, weights=acc_pair[:, k], minlength=N)
        acc += np.array([0.0, 0.0, -self.g])

        self.vel += acc*dt
        self.pos += self.vel*dt

        eps = 1e-6
        for a, lo, hi in ((0, -self.lx/2, self.lx/2),
                          (1, -self.ly/2, self.ly/2),
                          (2, -self.depth, None)):
            lo_v = lo + eps
            hit_lo = self.pos[:, a] < lo_v
            if np.any(hit_lo):
                self.pos[hit_lo, a] = lo_v
                neg = self.vel[hit_lo, a] < 0
                idx_hit = np.nonzero(hit_lo)[0][neg]
                self.vel[idx_hit, a] = 0.0
            if hi is not None:
                hi_v = hi - eps
                hit_hi = self.pos[:, a] > hi_v
                if np.any(hit_hi):
                    self.pos[hit_hi, a] = hi_v
                    pos_v = self.vel[hit_hi, a] > 0
                    idx_hit = np.nonzero(hit_hi)[0][pos_v]
                    self.vel[idx_hit, a] = 0.0


    def apply_body_force(self, pos, force, dt):
        """Verteilt eine Körperkraft kernelgewichtet auf Partikel im
        Stützradius (Impulsübertrag Spec §5). Deterministisch."""
        pos = np.asarray(pos, dtype=float)
        force = np.asarray(force, dtype=float)
        d = self.pos - pos
        r = np.sqrt(np.einsum('ij,ij->i', d, d))
        m = r < 2.0*self.h
        if not np.any(m) or np.linalg.norm(force) == 0.0:
            return
        W = _SIGMA/self.h**3 * _w(r[m]/self.h)
        s = float(np.sum(W))
        if s <= 0:
            return
        frac = W/s
        dv = dt*force/self.mass
        self.vel[m] += frac[:, None]*dv
