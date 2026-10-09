"""PyVista-Renderer (v0.3a.1): Echtzeit-3D mit Orbit-Steuerung.

v0.3a.1: Robuste Oberflaechen-Nachbearbeitung (_smooth_surface):
NaN-Loecher werden aus Nachbarwerten gefuellt, Spritzer-Nadeln
werden gegen den lokalen Median gekappt -> geschlossene Wasserflaeche.
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
    pd = pv.PolyData(pts); pd.faces = faces.ravel()
    return pd


class PyVistaRenderer:
    def __init__(self, app, nx=64, ny=64, off_screen=False):
        import pyvista as pv
        self.pv = pv; self.app = app
        b = app.cfg.basin
        self.lx, self.ly = float(b["lx"]), float(b["ly"])
        self.depth = float(app.cfg.water["depth"])
        self.nx, self.ny = int(nx), int(ny)
        self._xs = np.linspace(-self.lx / 2, self.lx / 2, self.nx)
        self._ys = np.linspace(-self.ly / 2, self.ly / 2, self.ny)
        self.X, self.Y = np.meshgrid(self._xs, self._ys)
        self._plotter = None; self._surf = None; self._bodies = {}
        self.off_screen = off_screen

    def attach(self, surface):
        # Renderer und Heightfield teilen sich EIN Gitter:
        # X/Y werden vom tatsaechlichen Surface-Objekt uebernommen.
        self.X, self.Y = surface.X, surface.Y
        self.ny, self.nx = self.X.shape

    # ---------- Oberflaechen-Nachbearbeitung ----------
    def _smooth_surface(self, Z):
        """Loecher fuellen + Nadeln kappen (v0.3a.1).

        1) NaN-Zellen erhalten iterativ den Mittelwert ihrer finiten
           Nachbarn; isolierte Rest-NaN fallen auf den Feldmedian.
        2) Ausreisser > 0.35 m ueber dem lokalen 3x3-Mittel werden auf
           dieses gekappt (Spritz-Nadeln gehoeren nicht in die
           geschlossene Darstellungsflaeche).
        """
        Z = np.array(Z, dtype=np.float64, copy=True)
        bad = ~np.isfinite(Z)
        if bad.all():
            return np.zeros_like(Z)
        def _shift(a, dy, dx):
            # Verschiebung OHNE Umwickeln: ausserhalb liegt der Randwert
            # (edge) -> keine Spiegelartefakte an Beckenraendern.
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
        # Nadeln kappen: lokaler 3x3-Median (ignoriert den Ausreisser selbst)
        stack = np.empty((9,) + Z.shape, dtype=np.float64)
        i = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                stack[i] = _shift(Z, dy, dx)
                i += 1
        loc = np.median(stack, axis=0)
        spike = np.abs(Z - loc) > 0.35
        Z[spike] = loc[spike]
        return Z

    # ---------- Aufbau ----------
    def build(self):
        pv = self.pv
        p = pv.Plotter(window_size=(1280, 800), off_screen=self.off_screen)
        p.set_background("white")
        lx, ly, d = self.lx, self.ly, self.depth
        # Rahmen als explizite Segmente (Paare von Punkten!)
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
        # Maßstab 1 m
        p.add_mesh(pv.Line((0.0, -ly/2, 0.05), (1.0, -ly/2, 0.05)),
                   color="black", line_width=5)
        p.add_mesh(pv.Plane(center=(0, 0, -d), direction=(0, 0, 1),
                            i_size=lx, j_size=ly),
                   color="lightsteelblue", opacity=0.25)
        self._surf = _surface_polydata(pv, self.X, self.Y,
                                       np.zeros_like(self.X))
        p.add_mesh(self._surf, color="tab:blue", opacity=0.55,
                   show_edges=False)
        p.add_axes(xlabel="x (Bug)", ylabel="y (Backbord)", zlabel="z")
        p.add_text("SegelPhysik v0.3a | [g/G] g  [w/W] Wind  [space] Pause"
                   "  [r] Reset  [s] Kugel  [q] Ende",
                   position="upper_left", font_size=10)
        self._plotter = p
        return p

    # ---------- Aktualisierung ----------
    def update(self, surface):
        Z = self._smooth_surface(surface.Z)
        self._surf.points = np.column_stack(
            [self.X.ravel(), self.Y.ravel(), Z.ravel()])
        from ..core.bodies import Sphere
        alive = set()
        for k, b in enumerate(self.app.world.bodies):
            alive.add(k)
            if k not in self._bodies:
                if isinstance(b, Sphere):
                    m = self.pv.Sphere(radius=b.r, center=tuple(b.pos))
                else:
                    m = self.pv.Box(bounds=(
                        b.pos[0]-b.half[0], b.pos[0]+b.half[0],
                        b.pos[1]-b.half[1], b.pos[1]+b.half[1],
                        b.pos[2]-b.half[2], b.pos[2]+b.half[2]))
                self._bodies[k] = self._plotter.add_mesh(
                    m, color="tab:red", opacity=0.95)
            else:
                self._bodies[k].position = tuple(b.pos)
        for k in list(self._bodies):
            if k not in alive:
                self._plotter.remove_actor(self._bodies.pop(k))
