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
from .core.overlays import (LayerRegistry, hauptachsen,
                            LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN)

FARBE_UNTEN = "#2166ac"
FARBE_OBEN = "#b2182b"

# Schritt 3 (P5b): Farbkonvention der Overlays (K4-Vorgriff, Linien
# statt Tubes bis Schritt 4). 1./2./3. Hauptachse = gold/cyan/magenta,
# Schwerpunkt-Marker = weiss.
OVERLAY_FARBEN_ACHSEN = ("gold", "cyan", "magenta")

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
        self._layer = LayerRegistry()   # P5a: global, nicht pro Koerper

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
            "SegelPhysik v4 | [1/2/3] Koerper  [4] Boot  [a] alle  [F1-F4] Kamera  "
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

    def mesh_setzen(self, name, punkte, gesichter, position=(0.0, 0.0, 0.0),
                    farbe_unten=FARBE_UNTEN, farbe_oben=FARBE_OBEN):
        """Haengt ein fertiges Dreiecks-Mesh ein (z. B. Boot). achse=None
        bedeutet: statisch, keine Rotation."""
        import pyvista as pv
        pd = _dreiecks_polydaten(pv, punkte, gesichter)
        pd["referenz_punkte"] = pd.points.copy()
        self._koerper[name] = {"typ": "mesh", "dims": {}, "achse": None,
                               "phase": 0.0,
                               "position": np.asarray(position, float),
                               "pd": pd, "aktiv": True,
                               "farbe_unten": farbe_unten,
                               "farbe_oben": farbe_oben}
        self._einhaengen(name)

    def koerper_objekt_setzen(self, name, koerper, position=(0.0, 0.0, 0.0),
                              achse=None, phase=0.0,
                              farbe_unten=None, farbe_oben=None):
        """Haengt einen Koerper (core.koerper.Koerper) ein (Spec V4).

        Ohne Farb-Override gelten die P4-Farben des Koerpers (aktiv ab
        Schritt 2.5); mit Override bleibt das alte Erscheinungsbild
        exakt erhalten (Schritt 1: visuell unveraendert).
        """
        self.mesh_setzen(name, koerper.punkte, koerper.dreiecke,
                         position=position,
                         farbe_unten=(farbe_unten if farbe_unten is not None
                                      else koerper.unterwasser_farbe()),
                         farbe_oben=(farbe_oben if farbe_oben is not None
                                     else koerper.farbe))
        if achse is not None:
            self._koerper[name]["achse"] = tuple(achse)
            self._koerper[name]["phase"] = phase
        # Schritt 3 (P5a/P5b): Koerper-Objekt + Overlay-Skala merken, damit
        # die Overlays (r_S, Hauptachsen) pro Frame aus der Wahrheit des
        # Koerpers projiziert werden koennen (nie im Koerper gespeichert).
        self._koerper[name]["koerper"] = koerper
        self._koerper[name]["overlay_skala"] = self._overlay_skala(koerper)

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
        k = self._koerper[name]
        farbe_u = k.get("farbe_unten", FARBE_UNTEN)
        farbe_o = k.get("farbe_oben", FARBE_OBEN)
        pd = k["pd"]
        u_p, u_t, o_p, o_t, kontur = ws.schneide_am_wasser(welt, _gesichter(pd))
        n_unten, n_oben, n_kontur = self._actor_namen(name)
        refs = k.setdefault("actors", {})

        if len(u_t):
            un = _dreiecks_polydaten(pv, u_p, u_t)
            refs[n_unten] = p.add_mesh(un, color=farbe_u, opacity=0.95,
                                       show_edges=False, smooth_shading=True,
                                       name=n_unten)
        else:
            refs.pop(n_unten, None)
            try:
                p.remove_actor(n_unten)
            except Exception:
                pass

        if len(o_t):
            ob = _dreiecks_polydaten(pv, o_p, o_t)
            refs[n_oben] = p.add_mesh(ob, color=farbe_o, opacity=0.95,
                                      show_edges=False, smooth_shading=True,
                                      name=n_oben)
        else:
            refs.pop(n_oben, None)
            try:
                p.remove_actor(n_oben)
            except Exception:
                pass

        if len(kontur):
            linien = pv.line_segments_from_points(kontur)
            refs[n_kontur] = p.add_mesh(linien, color="black", line_width=3,
                                        name=n_kontur)
        else:
            refs.pop(n_kontur, None)
            try:
                p.remove_actor(n_kontur)
            except Exception:
                pass

    def sichtbar_setzen(self, name, sichtbar):
        """Ein-/Ausblenden (Fix nach Sichtprobe): Actor-Referenzen werden
        mitgespeichert und per SetVisibility geschaltet. Nur remove_actor
        reichte nicht zuverlaessig - Koerper 'froren' dann nur ein."""
        k = self._koerper.get(name)
        if k is None:
            return
        k["aktiv"] = bool(sichtbar)
        refs = (list(k.get("actors", {}).values())
                + list(k.get("overlay_actors", {}).values()))
        if sichtbar:
            self._einhaengen(name)
            self._overlays_aktualisieren(name, k, np.eye(3))
        for a in refs:
            try:
                a.SetVisibility(bool(sichtbar))
            except Exception:
                pass
        if not sichtbar:
            for n in self._actor_namen(name) + self._overlay_namen(name):
                try:
                    self._plotter.remove_actor(n)
                except Exception:
                    pass

    def aktualisieren(self, t):
        from .core import bewegung as kin
        for name, k in self._koerper.items():
            if not k["aktiv"]:
                continue
            pd = k["pd"]
            if k["achse"] is None:      # statisch (z. B. Boot)
                R = np.eye(3)
                welt = pd["referenz_punkte"] + k["position"]
            else:
                R, _ = kin.koerper_pose(t, achse=k["achse"], phase=k["phase"])
                welt = pd["referenz_punkte"] @ R.T + k["position"]
            pd.points = welt
            self._actors_aktualisieren(name, welt)
            self._overlays_aktualisieren(name, k, R)
        return True

    def status(self, text):
        self._renderer.set_status(text)

    def hud(self, text):
        self._renderer.set_hud(text)

    # ------------------------------------------------------------------
    # Schritt 3 - Overlay-Layer (P5a/P5b): r_S-Marker + Hauptachsen
    # ------------------------------------------------------------------
    def layer_umschalten(self, layer):
        """Globaler Layer-Schalter (P5a): betrifft ALLE Koerper gleichzeitig."""
        return self._layer.umschalten(layer)

    def layer_ist_an(self, layer):
        return self._layer.ist_an(layer)

    def _overlay_skala(self, koerper):
        """Achsen-Laenge + Marker-Radius aus der Koerpergroesse (eigene Punkte,
        Schwerpunktframe -> halbe Max-Ausdehnung = typischer Radius)."""
        halbe = float(np.abs(koerper.punkte).max()) if len(koerper.punkte) else 0.0
        if halbe <= 0.0:
            halbe = 1.0
        laenge = 1.1 * halbe
        radius = min(max(0.040 * halbe, 0.020), 0.160)
        return laenge, radius

    def _overlay_namen(self, name):
        return (["overlay_%s_schwerpunkt" % name]
                + ["overlay_%s_achse%d" % (name, i) for i in (1, 2, 3)])

    def _overlays_aktualisieren(self, name, k, R):
        koerper = k.get("koerper")
        if koerper is None:
            return
        _laenge, radius = k["overlay_skala"]
        cm = k["position"]                       # Welt-Schwerpunkt (P1)
        if self._layer.ist_an(LAYER_SCHWERPUNKT):
            self._overlay_schwerpunkt_setzen(name, cm, radius)
        else:
            self._overlay_schwerpunkt_entfernen(name)
        if self._layer.ist_an(LAYER_HAUPTACHSEN):
            _werte, vektoren = hauptachsen(koerper.traegheitstensor)
            richtungen = vektoren @ R.T           # gleiche Rotation wie das Mesh
            # Achsenlaenge je Hauptachse: echte halbe Ausdehnung des Koerpers
            # entlang dieser Achse (+5 % Luft). Vorher pauschal 1.1*max -
            # das gab v. a. beim Boot bildfuellende Achsen.
            rel = np.asarray(koerper.punkte, dtype=float)
            laengen = []
            for i in range(3):
                proj = rel @ richtungen[i] if len(rel) else np.zeros(1)
                halbe = float(np.abs(proj).max())
                laengen.append(max(1.05 * halbe, 0.05))
            self._overlay_hauptachsen_setzen(name, cm, richtungen, laengen)
        else:
            self._overlay_hauptachsen_entfernen(name)

    def _overlay_schwerpunkt_setzen(self, name, cm, radius):
        import pyvista as pv
        kugel = pv.Sphere(center=tuple(cm), radius=radius)
        n = self._overlay_namen(name)[0]
        actor = self._plotter.add_mesh(kugel, color="white", name=n)
        self._koerper[name].setdefault("overlay_actors", {})[n] = actor

    def _overlay_schwerpunkt_entfernen(self, name):
        n = self._overlay_namen(name)[0]
        self._koerper.get(name, {}).get("overlay_actors", {}).pop(n, None)
        try:
            self._plotter.remove_actor(n)
        except Exception:
            pass

    def _overlay_hauptachsen_setzen(self, name, cm, richtungen, laengen):
        import pyvista as pv
        namen = self._overlay_namen(name)
        store = self._koerper[name].setdefault("overlay_actors", {})
        for i in range(3):
            l = laengen[i] if hasattr(laengen, "__len__") else laengen
            start = cm - l * richtungen[i]
            ende = cm + l * richtungen[i]
            linie = pv.Line(start, ende)
            store[namen[i + 1]] = self._plotter.add_mesh(
                linie, color=OVERLAY_FARBEN_ACHSEN[i], line_width=4,
                name=namen[i + 1])

    def _overlay_hauptachsen_entfernen(self, name):
        namen = self._overlay_namen(name)
        store = self._koerper.get(name, {}).get("overlay_actors", {})
        for n in namen[1:]:
            store.pop(n, None)
            try:
                self._plotter.remove_actor(n)
            except Exception:
                pass


def _gesichter(pd):
    f = np.asarray(pd.faces).reshape(-1, 4)
    return f[:, 1:4]
