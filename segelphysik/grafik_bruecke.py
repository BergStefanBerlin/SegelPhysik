"""Grafik-Bruecke V3 (Additivprinzip): verbindet die fertige v0.4-
Render-Pipeline (segelphysik/render/vista.py - UNVERAENDERT) mit der
kinematischen Demo. Mehrkoerper-faehig.

Wasserlinie (Verfahren B): Jeder Koerper wird pro Frame von
segelphysik.wasser_schnitt exakt an der Ebene z = 0 in zwei geschlossene
Teil-Meshes zerlegt und EINFARBIG eingefaerbt (dunkelblau unter Wasser,
rot darueber). Die Wasserlinie ist die exakte Schnittkante - scharf fuer
beliebig geformte Koerper und jede Orientierung.
"""
from __future__ import annotations
import numpy as np

try:
    from . import wasser_schnitt as ws
except ImportError:
    from segelphysik import wasser_schnitt as ws

FARBE_UNTEN = "#2166ac"
FARBE_OBEN = "#b2182b"

BASIN_LX, BASIN_LY, WASSER_TIEFE, DX = 10.0, 10.0, 3.0, 0.25


class _Konfig:
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
    def __init__(self):
        self.cfg = _Konfig()
        self.world = _Welt()


def _polydaten(pv, vertices, gesichter):
    gesicht = np.asarray(gesichter, dtype=np.int64)
    kopf = np.full((len(gesicht), 1), 3, dtype=np.int64)
    return pv.PolyData(np.asarray(vertices, dtype=np.float64),
                       np.hstack([kopf, gesicht]).ravel())


def _dreiecks_polydaten(pv, punkte, dreiecke):
    dreiecke = np.asarray(dreiecke, dtype=np.int64)
    kopf = np.full((len(dreiecke), 1), 3, dtype=np.int64)
    return pv.PolyData(np.asarray(punkte, dtype=np.float64),
                       np.hstack([kopf, dreiecke]).ravel())


class GrafikBruecke:
    """Baut das Fenster mit dem ORIGINAL-Renderer; haelt MEHRERE Koerper."""

    def __init__(self):
        self.app = StellvertreterApp()
        self._renderer = None
        self._plotter = None
        self._koerper = {}

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
            "SegelPhysik v3.0 | [1/2/3] Koerper ein/aus  [a] alle  "
            "[Leertaste] Pause  [r] Reset  [+/-] Tempo  [q] Ende")
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

    def koerper_setzen(self, name, typ, dims, achse, phase, position=(0.0, 0.0, 0.0)):
        from .core import koerper_formen as formen
        bauer = {"cone": formen.bau_kegel, "box": formen.bau_quader,
                 "pyramid": formen.bau_pyramide}[typ]
        v, f = bauer(**dims)
        import pyvista as pv
        pd = _polydaten(pv, v, f)
        pd["referenz_punkte"] = pd.points.copy()
        self._koerper[name] = {"typ": typ, "dims": dims, "achse": tuple(achse),
                               "phase": phase, "position": np.asarray(position, float),
                               "pd": pd, "aktiv": True}
        self._einhaengen(name)

    def _actor_namen(self, name):
        return ("koerper_%s_unten" % name, "koerper_%s_oben" % name,
                "kontur_%s" % name)

    def _einhaengen(self, name):
        k = self._koerper[name]
        welt = k["pd"]["referenz_punkte"] + k["position"]
        k["pd"].points = welt
        self._actors_aktualisieren(name, welt)

    def _actors_aktualisieren(self, name, welt):
        import pyvista as pv
        p = self._plotter
        pd = self._koerper[name]["pd"]
        u_p, u_t, o_p, o_t, kontur = ws.schneide_am_wasser(welt, _gesichter(pd))
        n_unten, n_oben, n_kontur = self._actor_namen(name)

        if len(u_t):
            un = _dreiecks_polydaten(pv, u_p, u_t)
            p.add_mesh(un, color=FARBE_UNTEN, opacity=0.95,
                       show_edges=False, smooth_shading=True, name=n_unten)
        else:
            p.remove_actor(n_unten)

        if len(o_t):
            ob = _dreiecks_polydaten(pv, o_p, o_t)
            p.add_mesh(ob, color=FARBE_OBEN, opacity=0.95,
                       show_edges=False, smooth_shading=True, name=n_oben)
        else:
            p.remove_actor(n_oben)

        if len(kontur):
            linien = pv.line_segments_from_points(kontur)
            p.add_mesh(linien, color="black", line_width=3, name=n_kontur)
        else:
            p.remove_actor(n_kontur)

    def sichtbar_setzen(self, name, sichtbar):
        k = self._koerper.get(name)
        if k is None:
            return
        k["aktiv"] = bool(sichtbar)
        p = self._plotter
        if not sichtbar:
            for n in self._actor_namen(name):
                try:
                    p.remove_actor(n)
                except Exception:
                    pass
        else:
            self._einhaengen(name)

    def aktualisieren(self, t):
        from .core import bewegung as kin
        for name, k in self._koerper.items():
            if not k["aktiv"]:
                continue
            R, _ = kin.koerper_pose(t, achse=k["achse"], phase=k["phase"])
            pd = k["pd"]
            welt = pd["referenz_punkte"] @ R.T + k["position"]
            pd.points = welt
            self._actors_aktualisieren(name, welt)
        return True

    def status(self, text):
        self._renderer.set_status(text)

    def hud(self, text):
        self._renderer.set_hud(text)


def _gesichter(pd):
    f = np.asarray(pd.faces).reshape(-1, 4)
    return f[:, 1:4]
