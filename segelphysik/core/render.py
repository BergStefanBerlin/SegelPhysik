"""Rendering (Plan Issues 10-11, M4).

HeightFieldSurface: extrahiert die Wasseroberfläche datenseitig aus den
SPH-Partikeln (v0.3c: update() vektorisiert) (höchstes Fluido-Partikel pro (x,y)-Zelle) - renderbar und
testbar (Trennung Extraktion <-> Darstellung, Spec §7.1).
MatplotlibRenderer: transparente Oberfläche, Koordinatengitter, Maßstab,
Körper als Drahtgitter. Läuft headless (Agg) und interaktiv lokal.
PyVista/ModernGL als 3D-Backend bleibt in ARCHITECTURE.md als Option notiert.
"""
import numpy as np


class HeightFieldSurface:
    """Wasseroberfläche als Höhenfeld: pro (x,y)-Zelle das höchste
    Fluido-Partikel (Geister ausgeschlossen, leere Zellen = NaN)."""

    def __init__(self, basin, nx=40, ny=40, fill=np.nan):
        self.lx = float(basin["lx"]); self.ly = float(basin["ly"])
        self.nx = int(nx); self.ny = int(ny)
        self.fill = float(fill)
        xs = np.linspace(-self.lx/2, self.lx/2, self.nx)
        ys = np.linspace(-self.ly/2, self.ly/2, self.ny)
        self.X, self.Y = np.meshgrid(xs, ys)
        self.Z = np.full_like(self.X, self.fill)

    def update(self, pos, exclude=None):
        """pos: (N,3) Array der Fluido-Partikel (ohne Geister).
        exclude: optional (M,3) Punkte, deren Nahe Umgebung ignoriert
        wird (v0.3g: an Koerperhullen projizierte Partikel - sie sind
        kein freies Wasser und wuerden als falscher "Berg" erscheinen).

        v0.3c: vollstaendig vektorisiert - sortiere nach Zelle (primar)
        und z (sekundaer, aufsteigend); der LETZTE Treffer je Zelle ist
        das hoechste Partikel. Semantik identisch zur alten Schleife,
        aber ohne Python-Loop ueber alle Partikel pro Frame.
        """
        self.Z[...] = self.fill
        if len(pos) == 0:
            return
        pos = np.asarray(pos)
        if exclude is not None and len(exclude) > 0:
            ex = np.asarray(exclude)
            keep = np.ones(len(pos), dtype=bool)
            for j in range(len(ex)):
                keep &= (np.abs(pos[:, 0] - ex[j, 0]) > ex[j, 3]) \
                     | (np.abs(pos[:, 1] - ex[j, 1]) > ex[j, 3]) \
                     | (np.abs(pos[:, 2] - ex[j, 2]) > ex[j, 3])
            pos = pos[keep]
            if len(pos) == 0:
                return
        ix = np.clip(((pos[:, 0] + self.lx/2) / self.lx * self.nx).astype(int),
                     0, self.nx - 1)
        iy = np.clip(((pos[:, 1] + self.ly/2) / self.ly * self.ny).astype(int),
                     0, self.ny - 1)
        flat = iy * self.nx + ix
        order = np.lexsort((pos[:, 2], flat))
        cells = flat[order]
        last = np.empty(cells.size, dtype=bool)
        last[-1] = True
        if cells.size > 1:
            last[:-1] = cells[:-1] != cells[1:]
        sel = order[last]          # Index des höchsten Partikels je Zelle
        self.Z.flat[flat[sel]] = pos[sel, 2]


class MatplotlibRenderer:
    """Headless-fähiger Renderer (Agg im Test, interaktiv lokal)."""

    def __init__(self, elev=22, azim=-60):
        self.elev = elev; self.azim = azim

    def render(self, world, surface=None):
        import matplotlib
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection="3d")
        b = world.cfg.basin
        depth = float(world.cfg.water["depth"])
        # Beckenrahmen (technisches Gitter, Spec §6)
        for z in (-depth, 0.0):
            ax.plot([-b["lx"]/2, b["lx"]/2, b["lx"]/2, -b["lx"]/2, -b["lx"]/2],
                    [-b["ly"]/2, -b["ly"]/2, b["ly"]/2, b["ly"]/2, -b["ly"]/2],
                    [z]*5, color="gray", lw=0.8)
        for x in (-b["lx"]/2, b["lx"]/2):
            for y in (-b["ly"]/2, b["ly"]/2):
                ax.plot([x, x], [y, y], [-depth, 0], color="gray", lw=0.6)
        # Maßstab: 1-m-Lineal entlang x (Spec §6)
        y0 = -b["ly"]/2
        ax.plot([0, 1.0], [y0, y0], [0.05, 0.05], color="black", lw=2)
        # Wasseroberfläche transparent (Spec §6)
        if surface is not None and np.any(np.isfinite(surface.Z)):
            ax.plot_surface(surface.X, surface.Y, surface.Z,
                            alpha=0.45, color="tab:blue", linewidth=0)
        # Körper als Drahtgitter
        from .bodies import Sphere, Box
        for bd in world.bodies:
            if isinstance(bd, Sphere):
                u, v = np.mgrid[0:2*np.pi:12j, 0:np.pi:8j]
                ax.plot_wireframe(bd.pos[0] + bd.r*np.cos(u)*np.sin(v),
                                  bd.pos[1] + bd.r*np.sin(u)*np.sin(v),
                                  bd.pos[2] + bd.r*np.cos(v),
                                  color="tab:red", lw=0.7)
            elif isinstance(bd, Box):
                hx, hy, hz = bd.half
                for sx in (-hx, hx):
                    for sy in (-hy, hy):
                        ax.plot([bd.pos[0]+sx]*2, [bd.pos[1]+sy]*2,
                                [bd.pos[2]-hz, bd.pos[2]+hz], color="tab:red")
                for sz in (-hz, hz):
                    for sx in (-hx, hx):
                        ax.plot([bd.pos[0]+sx]*2,
                                [bd.pos[1]-hy, bd.pos[1]+hy],
                                [bd.pos[2]+sz]*2, color="tab:red")
        ax.set_xlim(-b["lx"]/2, b["lx"]/2)
        ax.set_ylim(-b["ly"]/2, b["ly"]/2)
        ax.set_zlim(-depth, 2*b["H"]/3)
        ax.set_xlabel("x (Bug)"); ax.set_ylabel("y (Backbord)"); ax.set_zlabel("z")
        ax.view_init(elev=self.elev, azim=self.azim)
        return fig
