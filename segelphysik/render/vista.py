"""PyVista-Renderer (v0.3f): Echtzeit-3D mit Orbit-Steuerung.

v0.3a.1: Oberflaechen-Nachbearbeitung (_smooth_surface): NaN-Loecher
werden aus Nachbarwerten gefuellt, Spritzernadeln gegen den lokalen
Median gekappt -> geschlossene Wasserflaeche.

v0.3b: Tiefenfaerbung (color_by_depth), HUD (set_hud), screen_to_water()
fuer Klick-Spawning (Spec K8).

v0.3c: Wasser-Look: Vertex-Zellen-Fix, feineres Raster mit bilinearem
Upsampling, Smooth-Shading + Glanz, Spike-Cap an dx gekoppelt.

v0.3g: Kontakt-Klemme (Wasser liegt am Koerper an), weiche
Wasserlinie (tanh), Anti-Aliasing, schaerferes Glanzlicht.

v0.3f: Koerper-Darstellung nach Spec SS6:
- Fix Doppel-Offset: Meshes im Ursprung gebaut, Position nur am Actor.
- Zwei-Ton-Koerper: unter z=0 blau, darueber rot -> Eintauchen sichtbar.
- Wasserlinien-Ring an z=0 pro Koerper.
- Kraftpfeil (orange) + Geschwindigkeitspfeil (gruen) am gewaehlten
  Koerper (resultierende Kraefte).
- Status-HUD unten rechts: Position, v, Eintauchtiefe, Tauchfraktion,
  Kraftvektor des zuletzt gewaehlten Koerpers (Plan-Issue 14).
"""
import numpy as np


def _surface_polydata(pv, X, Y, Z):
    ny, nx = X.shape
    pts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()]).astype(np.float64)
    I, J = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
    a = (J * nx + I).ravel(); b = a + 1; c = a + nx; d = c + 1
    faces = np.empty((a.size * 2, 4), dtype=np.int64)
    faces[0::2, 0] = 3; faces[0::2, 1] = a; faces[0::2, 2] = b; faces[0::2, 3] = d
    faces[1::2, 0] = 3; faces[1::2, 1] = a; faces[1::2, 2] = d; faces[1::2, 3] = c
    return pv.PolyData(pts, faces=faces.ravel())


def _bilinear_upsample(Z, f):
    f = max(1, int(f))
    if f == 1:
        return Z
    ny, nx = Z.shape
    xi = np.linspace(0.0, nx - 1.0, (nx - 1) * f + 1)
    yi = np.linspace(0.0, ny - 1.0, (ny - 1) * f + 1)
    x0 = np.floor(xi).astype(int); x1 = np.minimum(x0 + 1, nx - 1)
    y0 = np.floor(yi).astype(int); y1 = np.minimum(y0 + 1, ny - 1)
    wx = (xi - x0)[None, :]; wy = (yi - y0)[:, None]
    Z00 = Z[np.ix_(y0, x0)]; Z01 = Z[np.ix_(y0, x1)]
    Z10 = Z[np.ix_(y1, x0)]; Z11 = Z[np.ix_(y1, x1)]
    return (Z00 * (1 - wx) * (1 - wy) + Z01 * wx * (1 - wy)
            + Z10 * (1 - wx) * wy + Z11 * wx * wy)


def _unit_circle(n=48):
    a = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return np.column_stack([np.cos(a), np.sin(a)])


def _unit_square():
    c = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0)]
    return np.array(c)


NL = chr(10)


class IsoSurfaceWater:
    """v0.4: Wasseroberflaeche als Isoflaeche des 3D-Partikel-Dichtefelds
    (Standardansatz nach SPlisHSPlasH/splashsurf).

    v0.4-Fixes:
    - Auto-Kalibrierung der Normierung aus dem ungestoerten Ruhewasser
      (Frame 1): Median der Tiefwasserzellen = homogene Dichte. Damit
      ist iso=0.6 immer richtig, egal wie Kernel/Abstand wirklich sind.
    - Neumann-Rand an den Beckenwaenden: Dichte wird gespiegelt, die
      Isoflaeche stoesst bündig an die Wand (kein Einrollen mehr).
    - Splatting via bincount (C-Tempo) statt np.add.at (~20x schneller).
    """

    def __init__(self, lx, ly, depth, dx, cell=None, iso_frac=0.6,
                 kernel_r=None):
        self.lx, self.ly, self.depth = float(lx), float(ly), float(depth)
        self.dx = float(dx)
        self.cell = max(0.18, self.dx) if cell is None else float(cell)
        self.kr = 2.0 * 1.3 * self.dx if kernel_r is None else float(kernel_r)
        self.iso = float(iso_frac)
        # analytische Normierung des separablen Produktkerns (Fallback,
        # wird aus dem Ruhewasser kalibriert):
        # homogenes Gitter Abstand dx -> Feld = ((16/15) * kr/dx)^3
        self.norm = (16.0 / 15.0 * self.kr / self.dx) ** 3
        self._norm_eff = None
        self.nx = int(np.ceil(self.lx / self.cell)) + 1
        self.ny = int(np.ceil(self.ly / self.cell)) + 1
        self.nz = max(8, int(np.ceil((self.depth + 0.8) / self.cell)) + 1)
        self.grid = np.zeros((self.nx, self.ny, self.nz), dtype=np.float32)
        r = np.arange(-self._half(), self._half() + 1)
        self._off = np.stack([a.ravel() for a in
                              np.meshgrid(r, r, r, indexing="ij")], axis=1)

    def _half(self):
        return int(np.ceil(self.kr / self.cell))

    def _calibrate(self, g):
        """Normierung aus ungestoertem Tiefwasser (Median der belegten
        Zellen im unteren Drittel, weg vom Rand)."""
        nx, ny, nz = self.nx, self.ny, self.nz
        sub = g[3:max(4, nx - 3), 3:max(4, ny - 3), :max(2, nz // 3)]
        vals = sub[sub > 0.0]
        if vals.size >= 20:
            m = float(np.median(vals))
            if m > 1e-6:
                self._norm_eff = m

    def _mirrored(self, pos):
        """Partikel an Beckenwaenden/Boden spiegeln (Boundary-Pad).
        Sequenziell ueber die akkumulierte Liste => an Kanten/Ecken
        entstehen automatisch alle Kombinationen. Nur Partikel nahe
        der jeweiligen Wand werden gespiegelt (kr + 1 Zelle)."""
        kr = self.kr
        out = [pos]
        cur = pos
        for axis, wall in ((0, -self.lx * 0.5), (0, self.lx * 0.5),
                           (1, -self.ly * 0.5), (1, self.ly * 0.5)):
            d = np.abs(cur[:, axis] - wall)
            sel = cur[d <= kr + self.cell]
            if sel.shape[0]:
                m = sel.copy()
                m[:, axis] = 2.0 * wall - m[:, axis]
                out.append(m)
                cur = np.vstack([cur, m])
        d = np.abs(cur[:, 2] + self.depth)
        sel = cur[d <= kr + self.cell]
        if sel.shape[0]:
            m = sel.copy()
            m[:, 2] = -2.0 * self.depth - m[:, 2]
            out.append(m)
        return np.vstack(out)

    def splat(self, pos):
        self._rf = getattr(self, '_rf', 0) + 1
        if self._rf % 2 != 0 and getattr(self, '_has_mesh', False):
            self._skip = True
            return
        self._skip = False
        """Vektorisiertes Splatting aller Fluido-Partikel ins Grid."""
        g = self.grid
        g[...] = 0.0
        pos = np.asarray(pos, dtype=np.float64)
        if len(pos) == 0:
            return
        pos = self._mirrored(pos)
        inv = 1.0 / self.cell
        nx, ny, nz = self.nx, self.ny, self.nz
        fx = (pos[:, 0] + self.lx * 0.5) * inv
        fy = (pos[:, 1] + self.ly * 0.5) * inv
        fz = (pos[:, 2] + self.depth) * inv
        cx, cy, cz = fx.astype(np.int64), fy.astype(np.int64), \
            fz.astype(np.int64)
        off = self._off
        ii = cx[:, None] + off[None, :, 0]
        jj = cy[:, None] + off[None, :, 1]
        kk = cz[:, None] + off[None, :, 2]
        valid = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < ny) & \
            (kk >= 0) & (kk < nz)
        W = np.empty(ii.shape, dtype=np.float32)
        for t in range(off.shape[0]):
            qx = np.abs((ii[:, t] - fx) * self.cell) / self.kr
            qy = np.abs((jj[:, t] - fy) * self.cell) / self.kr
            qz = np.abs((kk[:, t] - fz) * self.cell) / self.kr
            wx = np.where(qx >= 1.0, 0.0, (1.0 - qx * qx) ** 2)
            wy = np.where(qy >= 1.0, 0.0, (1.0 - qy * qy) ** 2)
            wz = np.where(qz >= 1.0, 0.0, (1.0 - qz * qz) ** 2)
            W[:, t] = wx * wy * wz
        sel = valid & (W > 0.0)
        flat = ((ii[sel] * ny) + jj[sel]) * nz + kk[sel]
        g[...] = np.bincount(flat, weights=W[sel],
                             minlength=nx * ny * nz
                             ).reshape(nx, ny, nz).astype(np.float32)
        # Neumann-Rand: Dichte an Beckenwaenden/Boden spiegeln, damit
        # die Isoflaeche bündig anstoesst (kein Einrollen am Rand).
        if nx > 2:
            g[0, :, :] = g[1, :, :]
            g[-1, :, :] = g[-2, :, :]
        if ny > 2:
            g[:, 0, :] = g[:, 1, :]
            g[:, -1, :] = g[:, -2, :]
        if nz > 2:
            g[:, :, 0] = g[:, :, 1]
        if self._norm_eff is None:
            self._calibrate(g)

    def mesh(self, pv):
        if getattr(self, '_skip', False) and getattr(self, '_cache', None) is not None:
            return self._cache
        """Isoflaeche per Marching Cubes extrahieren."""
        grid = pv.ImageData(
            dimensions=(self.nx, self.ny, self.nz),
            spacing=(self.cell, self.cell, self.cell),
            origin=(-self.lx * 0.5, -self.ly * 0.5, -self.depth))
        grid.point_data["d"] = self.grid.ravel(order="F")
        neff = self._norm_eff if self._norm_eff is not None else self.norm
        out = grid.contour([self.iso * neff], scalars="d",
                           method="marching_cubes")
        self._cache = out
        self._has_mesh = True
        return out



class PyVistaRenderer:
    def __init__(self, app, nx=64, ny=64, off_screen=False,
                 color_by_depth=True, upsample=2,
                 smooth_passes=2, time_damp=0.4):
        import pyvista as pv
        self.pv = pv; self.app = app
        b = app.cfg.basin
        self.lx, self.ly = float(b["lx"]), float(b["ly"])
        self.depth = float(app.cfg.water["depth"])
        self.dx = float(getattr(app.cfg, "dx", 0.25) or 0.25)
        self.nx, self.ny = int(nx), int(ny)
        self.upsample = max(1, int(upsample))
        self._xs = np.linspace(-self.lx / 2, self.lx / 2, self.nx)
        self._ys = np.linspace(-self.ly / 2, self.ly / 2, self.ny)
        self.X, self.Y = np.meshgrid(self._xs, self._ys)
        self._Xr, self._Yr = self.X, self.Y
        self._plotter = None; self._surf = None
        self._bodies = {}
        self._body_pd = {}
        self._extents = {}
        self._rings = {}
        self._ring_pd = {}
        self._ring_tpl = {}
        self._arrow_f = None; self._arrow_v = None
        self._selected = None
        self._prev_n = -1
        self.off_screen = off_screen
        self.color_by_depth = bool(color_by_depth)
        self.smooth_passes = max(0, int(smooth_passes))
        self.time_damp = min(1.0, max(0.05, float(time_damp)))
        self._z_prev = None
        self._elev_key = "elev"
        self._hud_actor = None
        self._status_actor = None
        self._circle_tpl = _unit_circle(48)
        self._square_tpl = _unit_square()
        self._frame = 0

    def attach(self, surface):
        self.X, self.Y = surface.X, surface.Y
        self.ny, self.nx = self.X.shape
        f = self.upsample
        xr = np.linspace(-self.lx / 2, self.lx / 2, (self.nx - 1) * f + 1)
        yr = np.linspace(-self.ly / 2, self.ly / 2, (self.ny - 1) * f + 1)
        self._Xr, self._Yr = np.meshgrid(xr, yr)

    def _smooth_surface(self, Z):
        Z = np.array(Z, dtype=np.float64, copy=True)
        bad = ~np.isfinite(Z)
        if bad.all():
            return np.zeros_like(Z)
        def _shift(a, dy, dx):
            p = np.pad(a, 1, mode="edge")
            if dy == -1:   p = p[2:, :]
            elif dy == 1:  p = p[:-2, :]
            else:          p = p[1:-1, :]
            if dx == -1:   p = p[:, 2:]
            elif dx == 1:  p = p[:, :-2]
            else:          p = p[:, 1:-1]
            return p
        for _ in range(25):
            if not bad.any():
                break
            Zf = np.where(bad, 0.0, Z)
            cnt = (~bad).astype(np.float64)
            acc = np.zeros_like(Zf); c = np.zeros_like(Zf)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    acc += _shift(Zf, dy, dx)
                    c += _shift(cnt, dy, dx)
            fill = np.where(c > 0, acc / np.maximum(c, 1e-12), np.nan)
            newly = bad & np.isfinite(fill)
            Z[newly] = fill[newly]
            bad = ~np.isfinite(Z)
        if bad.any():
            Z[bad] = np.nanmedian(Z)
        stack = np.empty((9,) + Z.shape, dtype=np.float64)
        i = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                stack[i] = _shift(Z, dy, dx)
                i += 1
        loc = np.median(stack, axis=0)
        cap = 2.5 * self.dx
        spike = np.abs(Z - loc) > cap
        Z[spike] = loc[spike]
        # v0.3f: raeumliche Glaettung (Laplace-Relaxation) -> ruhige Flaeche
        for _ in range(self.smooth_passes):
            acc = np.zeros_like(Z)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    acc += _shift(Z, dy, dx)
            mean8 = acc / 8.0
            Z = Z + 0.5 * (mean8 - Z)
        return Z

    def build(self):
        pv = self.pv
        p = pv.Plotter(window_size=(1280, 800), off_screen=self.off_screen)
        p.set_background("white")
        lx, ly, d = self.lx, self.ly, self.depth
        seg = []
        z_levels = (-d, 0.0)
        for z in z_levels:
            corners = [(-lx/2, -ly/2), (lx/2, -ly/2), (lx/2, ly/2),
                       (-lx/2, ly/2), (-lx/2, -ly/2)]
            for i in range(4):
                seg.append((corners[i][0], corners[i][1], z))
                seg.append((corners[i+1][0], corners[i+1][1], z))
        for x in (-lx/2, lx/2):
            for y in (-ly/2, ly/2):
                seg.append((x, y, -d)); seg.append((x, y, 0.0))
        p.add_mesh(pv.line_segments_from_points(np.array(seg)),
                   color="gray", line_width=2)
        p.add_mesh(pv.Line((0.0, -ly/2, 0.05), (1.0, -ly/2, 0.05)),
                   color="black", line_width=5)
        p.add_mesh(pv.Plane(center=(0, 0, -d), direction=(0, 0, 1),
                            i_size=lx, j_size=ly),
                   color="lightsteelblue", opacity=0.25)
        light = dict(smooth_shading=True, specular=0.8, specular_power=60,
                     diffuse=0.9, ambient=0.15)
        if not getattr(self, "skip_surf", False):
            self._surf = _surface_polydata(pv, self._Xr, self._Yr,
                                           np.zeros_like(self._Xr))
            if self.color_by_depth:
                self._surf[self._elev_key] = np.zeros(self._Xr.size,
                                                      dtype=np.float64)
                p.add_mesh(self._surf, scalars=self._elev_key,
                           cmap="Blues_r", opacity=0.7, show_edges=False,
                           clim=(-0.5, 0.5), show_scalar_bar=False, **light)
            else:
                p.add_mesh(self._surf, color="tab:blue", opacity=0.6,
                           show_edges=False, **light)
        p.add_axes(xlabel="x (Bug)", ylabel="y (Backbord)", zlabel="z")
        p.add_text("SegelPhysik v0.4 | [g/G] g  [w/W] Wind  [space] Pause"
                   "  [r] Reset  [s] Kugel  [n] Typ  [Klick] Spawn  [q] Ende",
                   position="upper_left", font_size=10)
        self._hud_actor = p.add_text(" ", position="upper_right",
                                     font_size=10, color="black")
        self._status_actor = p.add_text(" ", position="lower_right",
                                        font_size=10, color="black")
        self._plotter = p
        return p

    def set_hud(self, text):
        a = self._hud_actor
        if a is None:
            return
        if hasattr(a, "SetInput"):
            a.SetInput(str(text)); a.Modified()

    def set_status(self, text):
        a = self._status_actor
        if a is None:
            return
        if hasattr(a, "SetInput"):
            a.SetInput(str(text)); a.Modified()

    def screen_to_water(self, x, y):
        p = self._plotter
        if p is None:
            return None
        import vtk
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(float(x), float(y))
        w = np.asarray(coord.GetComputedWorldValue(p.renderer),
                       dtype=np.float64)
        cam = p.camera
        pos = np.asarray(cam.position, dtype=np.float64)
        d = w - pos
        if abs(d[2]) < 1e-9:
            return None
        t = -pos[2] / d[2]
        if t <= 0.0:
            return None
        pt = pos + t * d
        r = 0.75
        cx = min(max(float(pt[0]), -self.lx/2 + r), self.lx/2 - r)
        cy = min(max(float(pt[1]), -self.ly/2 + r), self.ly/2 - r)
        return cx, cy

    def _body_half_height(self, b):
        from ..core.bodies import Sphere
        if isinstance(b, Sphere):
            return float(b.r)
        return float(b.half[2])

    def _update_ring(self, k, b):
        from ..core.bodies import Sphere
        actor = self._rings.get(k)
        pd = self._ring_pd.get(k)
        if actor is None or pd is None:
            return
        zc = float(b.pos[2])
        if isinstance(b, Sphere):
            r = float(b.r)
            visible = abs(zc) < r
            sx = (r * r - zc * zc) ** 0.5 if visible else 0.0
            sy = sx
        else:
            hz = float(b.half[2])
            visible = -hz < zc < hz
            sx = float(b.half[0])
            sy = float(b.half[1])
        try:
            actor.visibility = bool(visible)
        except Exception:
            pass
        if not visible:
            return
        tmpl = self._ring_tpl.get(k)
        if tmpl is None:
            return
        n = tmpl.shape[0]
        pts = np.empty((n, 3))
        pts[:, 0] = tmpl[:, 0] * sx + float(b.pos[0])
        pts[:, 1] = tmpl[:, 1] * sy + float(b.pos[1])
        pts[:, 2] = tmpl[:, 2]
        pd.points = pts

    def _refresh_arrows(self, b):
        p = self._plotter
        for att in ("_arrow_f", "_arrow_v"):
            a = getattr(self, att)
            if a is not None:
                try:
                    p.remove_actor(a)
                except Exception:
                    pass
                setattr(self, att, None)
        g = float(self.app.world.environment.g)
        F = np.asarray(b.force, dtype=np.float64)
        v = np.asarray(b.vel, dtype=np.float64)
        fmag = float(np.linalg.norm(F))
        vmag = float(np.linalg.norm(v))
        ref = max(abs(b.mass) * abs(g), 1.0)
        if fmag > 0.02 * ref:
            L = float(np.clip(fmag / ref, 0.3, 3.0))
            d = F / max(fmag, 1e-12)
            self._arrow_f = p.add_mesh(
                self.pv.Arrow(start=tuple(b.pos), direction=tuple(d),
                              scale=L), color="#e67e22", line_width=5)
        if vmag > 0.05:
            L = float(np.clip(0.4 * vmag, 0.2, 2.5))
            d = v / max(vmag, 1e-12)
            self._arrow_v = p.add_mesh(
                self.pv.Arrow(start=tuple(b.pos), direction=tuple(d),
                              scale=L), color="#27ae60", line_width=5)

    def _update_status(self, k, b):
        from ..core.bodies import Sphere
        hh = self._body_half_height(b)
        bottom = float(b.pos[2]) - hh
        depth = min(max(-bottom, 0.0), 2.0 * hh)
        if isinstance(b, Sphere):
            vol = 4.0 / 3.0 * np.pi * b.r ** 3
            kind = "Kugel"
        else:
            hx, hy, hz = (float(t) for t in b.half)
            vol = 8.0 * hx * hy * hz
            kind = "Quader"
        frac = b.submerged_volume(0.0) / vol if vol > 0 else 0.0
        F = np.asarray(b.force); v = np.asarray(b.vel)
        txt = (
            "Koerper #%d (%s)" % (k, kind) + NL +
            "pos  x=%+.2f  y=%+.2f  z=%+.2f m" % (b.pos[0], b.pos[1], b.pos[2]) + NL +
            "vel  |v|=%.2f m/s" % float(np.linalg.norm(v)) + NL +
            "Eintauchtiefe %.2f m  (%.0f%% verdringt)" % (depth, 100.0 * frac) + NL +
            "F  (%+.0f, %+.0f, %+.0f) N  |F|=%.1f kN"
            % (F[0], F[1], F[2], float(np.linalg.norm(F)) / 1000.0)
        )
        self.set_status(txt)

    def _clamp_to_bodies(self, Z):
        """v0.3g (A1+A2): Hebt die Wasseroberflaeche im Koerper-Fussabdruck
        fuellt die Senke am Koerper sanft auf die Wasserlinie
        (smoothstep, keine Klippe). Wird NACH Glaettung/EMA angewendet, kann also
        nicht weggezaeht werden; hebt nur an, senkt nie."""
        from ..core.bodies import Sphere
        for b in self.app.world.bodies:
            if not isinstance(b, Sphere):
                continue
            zc = float(b.pos[2]); r = float(b.r)
            if zc >= r or zc <= -r:
                continue  # kein Schnitt mit der Wasserebene
            rw = (r * r - zc * zc) ** 0.5
            d = np.hypot(self.X - float(b.pos[0]), self.Y - float(b.pos[1]))
            w = max(0.15, 0.75 * self.dx)
            # weicher smoothstep-Blend Richtung max(Z, 0): fuellt die
            # Senke am Koerper sanft auf Wasserlinie, OHNE Klippe,
            # und hebt nie ueber lokale Wellenkämme hinaus
            a = np.clip((rw + w - d) / w, 0.0, 1.0)
            a = a * a * (3.0 - 2.0 * a)
            Zn = np.where(np.isfinite(Z), Z, 0.0)
            Z = a * np.maximum(Zn, 0.0) + (1.0 - a) * Zn
        return Z

    def update(self, surface=None):
        from ..core.bodies import Sphere
        if surface is not None:
            # Hull-Partikel ausschliessen (kein falscher Berg am Koerper)
            ex = []
            for b in self.app.world.bodies:
                if isinstance(b, Sphere):
                    rr = float(b.r) + 1.6 * self.dx
                    ex.append((float(b.pos[0]), float(b.pos[1]),
                               float(b.pos[2]), rr))
            if ex:
                surface.update(np.asarray(self.app.sph.get_state()[0])
                               if hasattr(self.app.sph, "get_state")
                               else self.app.sph.pos[:self.app.sph.n_real],
                               exclude=np.asarray(ex))
            Zs = self._smooth_surface(surface.Z)
            # v0.3f: zeitliche Daempfung -> kein Flackern, ruhige Wellen
            if self._z_prev is not None and self._z_prev.shape == Zs.shape:
                Zs = self.time_damp * Zs + (1.0 - self.time_damp) * self._z_prev
            self._z_prev = np.array(Zs, copy=True)
            Zs = self._clamp_to_bodies(Zs)
            Zr = _bilinear_upsample(Zs, self.upsample)
            self._surf.points = np.column_stack(
                [self._Xr.ravel(), self._Yr.ravel(), Zr.ravel()])
            try:
                self._surf.compute_normals(cell_normals=False, inplace=True)
            except Exception:
                pass
            if self.color_by_depth and self._frame % 3 == 0:
                self._surf[self._elev_key] = Zr.ravel()

        bodies = self.app.world.bodies
        n = len(bodies)
        if n != self._prev_n:
            self._prev_n = n
            self._selected = (n - 1) if n > 0 else None

        alive = set()
        for k, b in enumerate(bodies):
            alive.add(k)
            if k not in self._bodies:
                if isinstance(b, Sphere):
                    ext = float(b.r)
                    m = self.pv.Sphere(radius=ext)
                else:
                    hx, hy, hz = (float(t) for t in b.half)
                    ext = hz
                    m = self.pv.Box(bounds=(-hx, -hy, -hz, hx, hy, hz))
                self._extents[k] = ext
                m["wet"] = np.tanh((m.points[:, 2] + float(b.pos[2])) / 0.08)
                self._body_pd[k] = m
                self._bodies[k] = self._plotter.add_mesh(
                    m, scalars="wet", cmap=["#2166ac", "#b2182b"],
                    clim=(-1.0, 1.0), show_scalar_bar=False, opacity=0.95,
                    smooth_shading=True)
                if isinstance(b, Sphere):
                    t2 = self._circle_tpl
                else:
                    t2 = self._square_tpl
                pts3 = np.column_stack([t2[:, 0], t2[:, 1],
                                        np.full(t2.shape[0], 0.02)])
                self._ring_tpl[k] = pts3
                closed = np.vstack([pts3, pts3[:1]])
                rp = self.pv.lines_from_points(closed)
                self._ring_pd[k] = rp
                self._rings[k] = self._plotter.add_mesh(
                    rp, color="black", line_width=3)
            else:
                self._bodies[k].position = tuple(b.pos)
                m = self._body_pd[k]
                m["wet"] = np.tanh((m.points[:, 2] + float(b.pos[2])) / 0.08)
            self._update_ring(k, b)
        for k in list(self._bodies):
            if k not in alive:
                self._plotter.remove_actor(self._bodies.pop(k))
                self._ring_pd.pop(k, None)
                a = self._rings.pop(k, None)
                if a is not None:
                    try:
                        self._plotter.remove_actor(a)
                    except Exception:
                        pass
                self._extents.pop(k, None)

        sel = self._selected
        if sel is not None and sel in alive:
            b = bodies[sel]
            self._update_status(sel, b)
            if self._frame % 2 == 0:
                self._refresh_arrows(b)
        else:
            self.set_status(" ")

        self._frame += 1
