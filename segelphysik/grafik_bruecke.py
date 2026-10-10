"""Grafik-Bruecke V3 (Additivprinzip): verbindet die fertige v0.4-
Render-Pipeline (segelphysik/render/vista.py - UNVERAENDERT) mit der
kinematischen Demo.

Der alte Renderer erwartet ein app-Objekt mit cfg/world; hier wird ein
minimaler Stellvertreter bereitgestellt (keine Physik). Die drei
Spec-Koerper werden als Meshes aus koerper_formen.py in denselben
Plotter gehaengt und im originalen v0.4-Zweiton-Look gefaerbt
(tanh-Farbverlauf, blau unter / rot ueber der Wasserlinie).
"""
from __future__ import annotations
import numpy as np

BASIN_LX, BASIN_LY, WASSER_TIEFE, DX = 10.0, 10.0, 3.0, 0.25


class _Konfig:
    """Stellvertreter fuer app.cfg (nur die Felder, die der Renderer liest)."""

    def __init__(self):
        self.basin = {"lx": BASIN_LX, "ly": BASIN_LY}
        self.water = {"depth": WASSER_TIEFE}
        self.dx = DX


class _Umgebung:
    g = 9.81


class _Welt:
    def __init__(self):
        self.bodies = []
        self.environment = _Umgebung()


class StellvertreterApp:
    """Minimal-App-Interface fuer PyVistaRenderer (ohne Physik)."""

    def __init__(self):
        self.cfg = _Konfig()
        self.world = _Welt()


def _polydaten(pv, vertices, gesichter):
    gesicht = np.asarray(gesichter, dtype=np.int64)
    kopf = np.full((len(gesicht), 1), 3, dtype=np.int64)
    return pv.PolyData(np.asarray(vertices, dtype=np.float64),
                       np.hstack([kopf, gesicht]).ravel())


def wasserlinie_segmente(punkte, gesichter, eps=1e-9):
    """Schnitte der Dreiecke mit der Ebene z=0 -> Punktpaare (Segmente).

    Dies ist die Wasserlinien-Kontur aus der Grafik-Spec (Abschnitt 5),
    hier fuer beliebig rotierte Meshes je Frame berechnet. Hinweis:
    benachbarte Dreiecke liefern dieselbe Kante doppelt (harmlos fuer
    die Darstellung).
    """
    P = np.asarray(punkte, dtype=float)
    F = np.asarray(gesichter, dtype=int)
    z = P[:, 2]
    punkte_liste = []
    for dreieck in F:
        pz = z[dreieck]
        if (pz > eps).all() or (pz < -eps).all():
            continue
        schnitt = []
        for i in range(3):
            a, b = dreieck[i], dreieck[(i + 1) % 3]
            za, zb = z[a], z[b]
            if (za > eps and zb < -eps) or (za < -eps and zb > eps):
                t = za / (za - zb)
                schnitt.append(P[a] + t * (P[b] - P[a]))
            elif abs(za) <= eps:
                schnitt.append(P[a])
        if len(schnitt) >= 2:
            punkte_liste.append(schnitt[0])
            punkte_liste.append(schnitt[1])
    if not punkte_liste:
        return np.zeros((0, 3))
    return np.asarray(punkte_liste)


def zweiton_wert(z_welt, weichheit=0.08):
    """Originaler v0.4-Farbverlauf: tanh um die Wasserlinie."""
    return np.tanh(np.asarray(z_welt, dtype=float) / weichheit)


class GrafikBruecke:
    """Baut das Fenster mit dem ORIGINAL-Renderer und haelt die Koerper."""

    def __init__(self):
        self.app = StellvertreterApp()
        self._renderer = None
        self._plotter = None
        self._koerper = None

    def fenster_bauen(self):
        try:
            from .render.vista import PyVistaRenderer
        except ImportError:
            from segelphysik.render.vista import PyVistaRenderer
        self._renderer = PyVistaRenderer(self.app)
        self._renderer.skip_surf = False
        p = self._renderer.build()
        self._plotter = p
        self._hilfetext_ersetzen(
            "SegelPhysik v3.0 | [Leertaste] Pause  [r] Reset  "
            "[1/2/3] Koerper  [+/-] Tempo  [q] Ende")
        return p

    def _hilfetext_ersetzen(self, text):
        p = self._plotter
        aktoren = []
        for attribut in ("text_actors", "_text_actors"):
            aktoren = getattr(p, attribut, None) or []
            if aktoren:
                break
        for a in aktoren:
            try:
                alt = a.GetInput()
            except Exception:
                continue
            if isinstance(alt, str) and "v0.4" in alt:
                try:
                    a.SetInput(text)
                    a.Modified()
                except Exception:
                    pass

    def koerper_setzen(self, typ, dims, achse, phase):
        from .core import koerper_formen as formen
        p = self._plotter
        for name in ("koerper", "kontur"):
            try:
                p.remove_actor(name)
            except Exception:
                pass
        bauer = {"cone": formen.bau_kegel, "box": formen.bau_quader,
                 "pyramid": formen.bau_pyramide}[typ]
        v, f = bauer(**dims)
        import pyvista as pv
        pd = _polydaten(pv, v, f)
        pd["referenz_punkte"] = pd.points.copy()
        pd.point_data["wet"] = zweiton_wert(pd.points[:, 2])
        self._koerper = {"type": typ, "dims": dims, "axis": achse,
                         "phase": phase, "pd": pd}
        p.add_mesh(pd, scalars="wet",
                   cmap=["#2166ac", "#b2182b"], clim=(-1.0, 1.0),
                   show_scalar_bar=False, opacity=0.95,
                   smooth_shading=True, name="koerper")

    def aktualisieren(self, t):
        from .core import bewegung as kin
        k = self._koerper
        if k is None:
            return
        R, r_S = kin.koerper_pose(t, achse=k["axis"], phase=k["phase"])
        pd = k["pd"]
        welt = pd["referenz_punkte"] @ R.T + r_S
        pd.points = welt
        pd.point_data["wet"] = zweiton_wert(welt[:, 2])
        segs = wasserlinie_segmente(welt, _gesichter(pd))
        if len(segs):
            import pyvista as pv
            linien = pv.line_segments_from_points(segs)
            self._plotter.add_mesh(linien, color="black", line_width=3,
                                   name="kontur")
        self._renderer.set_hud("SegelPhysik v3.0 - kinematische Demo")
        return R, r_S

    def status(self, text):
        self._renderer.set_status(text)

    def hud(self, text):
        self._renderer.set_hud(text)


def _gesichter(pd):
    f = np.asarray(pd.faces).reshape(-1, 4)
    return f[:, 1:4]
