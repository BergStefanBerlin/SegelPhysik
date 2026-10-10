"""PyVista-Renderer (v0.3b): Echtzeit-3D mit Orbit-Steuerung.

v0.3a.1: Robuste Oberflaechen-Nachbearbeitung (_smooth_surface):
NaN-Loecher werden aus Nachbarwerten gefuellt, Spritzer-Nadeln
werden gegen den lokalen Median gekappt -> geschlossene Wasserflaeche.

v0.3b: Tiefen-/Hoehenfaerbung der Oberflaeche (color_by_depth),
HUD-Textzeile (set_hud) fuer RTF/FPS, screen_to_water() fuer
Klick-Spawning (Spec K8).
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
    def __init__(self, app, nx=64, ny=64, off_screen=False,
                 color_by_depth=True):
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
        self.color_by_depth = bool(color_by_depth)
        self._elev_key = "elev"
        self._hud_actor = None
        self._frame = 0

    def attach(self, surface):
        # Renderer und Heightfield teilen sich EIN Gitter:
        # X/Y werden vom tatsaechlichen Surface-Objekt uebernommen.
        self.X, self.Y = surface.X, surface.Y
        self.ny, self.nx = self.X.shape

    # ---------- Oberflaechen-Nachbearbeitung ----------
    def _smooth_surface(self, Z):
        """Loecher fuellen + Nadeln kappen (v0.3a.1)."""
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
        # Massstab 1 m
        p.add_mesh(pv.Line((0.0, -ly/2, 0.05), (1.0, -ly/2, 0.05)),
                   color="black", line_width=5)
        p.add_mesh(pv.Plane(center=(0, 0, -d), direction=(0, 0, 1),
                            i_size=lx, j_size=ly),
                   color="lightsteelblue", opacity=0.25)
        self._surf = _surface_polydata(pv, self.X, self.Y,
                                       np.zeros_like(self.X))
        if self.color_by_depth:
            # Hoehe relativ zum Ruhewasser: Blau-Abstufung (M4-Kosmetik)
            self._surf[self._elev_key] = np.zeros(self.X.size,
                                                  dtype=np.float64)
            p.add_mesh(self._surf, scalars=self._elev_key, cmap="Blues_r",
                       opacity=0.65, show_edges=False, clim=(-0.4, 0.4),
                       show_scalar_bar=False)
        else:
            p.add_mesh(self._surf, color="tab:blue", opacity=0.55,
                       show_edges=False)
        p.add_axes(xlabel="x (Bug)", ylabel="y (Backbord)", zlabel="z")
        p.add_text("SegelPhysik v0.3b | [g/G] g  [w/W] Wind  [space] Pause"
                   "  [r] Reset  [s] Kugel  [n] Typ  [Klick] Spawn  [q] Ende",
                   position="upper_left", font_size=10)
        # HUD rechts oben (RTF/FPS), leer bis zur ersten Aktualisierung
        self._hud_actor = p.add_text(" ", position="upper_right",
                                     font_size=10, color="black")
        self._plotter = p
        return p

    # ---------- HUD ----------
    def set_hud(self, text):
        """HUD-Zeile (RTF/FPS/Simulationszeit) aktualisieren."""
        a = self._hud_actor
        if a is None:
            return
        if hasattr(a, "SetInput"):
            a.SetInput(str(text))
            a.Modified()

    # ---------- Klick -> Wasserebene (Spec K8) ----------
    def screen_to_water(self, x, y):
        """Bildschirmkoordinate -> Punkt auf der Wasserebene z = 0.

        Kamerastrahl durch den Bildpunkt, Schnitt mit z = 0; das
        Ergebnis wird ins Beckeninnere geklemmt. Rueckgabe None, wenn
        der Strahl die Ebene nicht schneidet.
        """
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
        r = 0.75  # Randmargin: Koerper sollen ganz im Becken bleiben
        cx = min(max(float(pt[0]), -self.lx/2 + r), self.lx/2 - r)
        cy = min(max(float(pt[1]), -self.ly/2 + r), self.ly/2 - r)
        return cx, cy

    # ---------- Aktualisierung ----------
    def update(self, surface):
        Z = self._smooth_surface(surface.Z)
        self._surf.points = np.column_stack(
            [self.X.ravel(), self.Y.ravel(), Z.ravel()])
        if self.color_by_depth and self._frame % 3 == 0:
            # Farbskala nur jeden 3. Frame neu hochladen (Perf: VTK-Upload)
            self._surf[self._elev_key] = Z.ravel()
        self._frame += 1
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
