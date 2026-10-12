"""Grafik-Bruecke V3 (Additivprinzip): verbindet die fertige v0.4-
Render-Pipeline (segelphysik/render/vista.py - UNVERAENDERT) mit der
kinematischen Demo. Mehrkoerper-faehig.

Wasserlinie (Verfahren B): Jeder Koerper wird pro Frame von
segelphysik.wasser_schnitt exakt an der Ebene z = 0 in zwei geschlossene
Teil-Meshes zerlegt und EINFARBIG eingefaerbt (dunkelblau unter Wasser,
rot darueber). Die Wasserlinie ist die exakte Schnittkante - scharf fuer
beliebig geformte Koerper und jede Orientierung.

Schritt 4 (K3/K4): K3 Materialglanz - specular/specular_power je Blatt aus
der Materialtabelle via Koerper.glanz; Phong, bewusst KEIN PBR (SSAO-
Lektion: keine GPU-abhaengigen Effekte in der Standard-Ansicht). K4
Tube-Overlays: Hauptachsen als Roehren (pv.Line().tube()), Fallback dicke
Linie; Farben gold/cyan/magenta unveraendert.
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

OVERLAY_FARBEN_ACHSEN = ("gold", "cyan", "magenta")

BASIN_LX, BASIN_LY, WASSER_TIEFE, DX = 10.0, 10.0, 3.0, 0.25


def glanz_kw(glanz):
    """K3: add_mesh-kwargs fuer Glanzgrad g in [0..1] (Phong).

    Endpunkte analytisch: g=0 -> specular 0.0 / power 15;
    g=1 -> specular 1.0 / power 130. Linear dazwischen.
    """
    g = float(glanz)
    if not 0.0 <= g <= 1.0:
        raise ValueError("glanz muss in [0..1] liegen, gefunden: %r" % glanz)
    return {"pbr": False, "specular": g,
            "specular_power": 15.0 + 115.0 * g}


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


def _farbgruppen(koerper):
    """Farbgruppen eines Koerpers (P4 nach der Material-Reform)."""
    if not getattr(koerper, "teile", None):
        return [{"punkte": np.asarray(koerper.punkte, float),
                 "dreiecke": np.asarray(koerper.dreiecke, np.int64),
                 "farbe_oben": koerper.farbe,
                 "farbe_unten": koerper.unterwasser_farbe(),
                 "glanz": koerper.glanz}]
    blaetter = []

    def sammle(k, R, t):
        if k.teile:
            for kind, (R2, t2) in k.teile:
                sammle(kind, R @ np.asarray(R2, float),
                       t + R @ np.asarray(t2, float))
        else:
            blaetter.append((k, R, t))

    sammle(koerper, np.eye(3), np.zeros(3))
    gruppen = []
    for kind, R, t in blaetter:
        gruppen.append({"punkte": kind.punkte @ R.T + t,
                        "dreiecke": np.asarray(kind.dreiecke, np.int64),
                        "farbe_oben": kind.farbe,
                        "farbe_unten": kind.unterwasser_farbe(),
                        "glanz": kind.glanz})
    return gruppen


class GrafikBruecke:
    """Baut das Fenster mit dem ORIGINAL-Renderer; haelt MEHRERE Koerper."""

    def __init__(self):
        self.app = StellvertreterApp()
        self._renderer = None
        self._plotter = None
        self._koerper = {}
        self._layer = LayerRegistry()

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
        """Haengt ein fertiges Dreiecks-Mesh ein (z. B. Boot)."""
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
        """Haengt einen Koerper (core.koerper.Koerper) ein (Spec V4/P4)."""
        import pyvista as pv
        gruppen = _farbgruppen(koerper)
        if farbe_oben is not None or farbe_unten is not None:
            for g in gruppen:
                if farbe_oben is not None:
                    g["farbe_oben"] = farbe_oben
                if farbe_unten is not None:
                    g["farbe_unten"] = farbe_unten
        for g in gruppen:
            pd = _dreiecks_polydaten(pv, g["punkte"], g["dreiecke"])
            pd["referenz_punkte"] = pd.points.copy()
            g["pd"] = pd
        erster = gruppen[0]
        self._koerper[name] = {"typ": "mesh", "dims": {}, "achse": None,
                               "phase": 0.0,
                               "position": np.asarray(position, float),
                               "pd": erster["pd"], "aktiv": True,
                               "farbe_unten": erster["farbe_unten"],
                               "farbe_oben": erster["farbe_oben"],
                               "gruppen": gruppen}
        if achse is not None:
            self._koerper[name]["achse"] = tuple(achse)
            self._koerper[name]["phase"] = phase
        self._koerper[name]["koerper"] = koerper
        self._koerper[name]["overlay_skala"] = self._overlay_skala(koerper)
        self._einhaengen(name)

    def _actor_namen(self, name):
        namen = ["koerper_%s_unten" % name, "koerper_%s_oben" % name,
                 "kontur_%s" % name]
        for i in range(len(self._koerper.get(name, {}).get("gruppen", []))):
            namen += ["koerper_%s_g%d_unten" % (name, i),
                      "koerper_%s_g%d_oben" % (name, i),
                      "kontur_%s_g%d" % (name, i)]
        return namen

    def _einhaengen(self, name):
        k = self._koerper[name]
        welt = k["pd"]["referenz_punkte"] + k["position"]
        k["pd"].points = welt
        for g in k.get("gruppen", []):
            g["pd"].points = g["pd"]["referenz_punkte"] + k["position"]
        self._actors_aktualisieren(name, welt)

    def _actors_aktualisieren(self, name, welt):
        k = self._koerper[name]
        if k.get("gruppen"):
            self._gruppen_actors(name, k)
            return
        import pyvista as pv
        p = self._plotter
        farbe_u = k.get("farbe_unten", FARBE_UNTEN)
        farbe_o = k.get("farbe_oben", FARBE_OBEN)
        glanz = k.get("glanz")
        pd = k["pd"]
        u_p, u_t, o_p, o_t, kontur = ws.schneide_am_wasser(welt, _gesichter(pd),
                                  mit_deckel=True)
        n_unten, n_oben, n_kontur = self._actor_namen(name)
        refs = k.setdefault("actors", {})

        kw_basis = {"opacity": 0.95, "show_edges": False,
                    "smooth_shading": True}
        if glanz is not None:
            kw_basis.update(glanz_kw(glanz))

        if len(u_t):
            un = _dreiecks_polydaten(pv, u_p, u_t)
            refs[n_unten] = p.add_mesh(un, color=farbe_u, name=n_unten,
                                       **kw_basis)
        else:
            refs.pop(n_unten, None)
            try:
                p.remove_actor(n_unten)
            except Exception:
                pass

        if len(o_t):
            ob = _dreiecks_polydaten(pv, o_p, o_t)
            refs[n_oben] = p.add_mesh(ob, color=farbe_o, name=n_oben,
                                      **kw_basis)
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
        """Ein-/Ausblenden (Fix nach Sichtprobe)."""
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
            if k["achse"] is None:
                R = np.eye(3)
                welt = pd["referenz_punkte"] + k["position"]
            else:
                R, _ = kin.koerper_pose(t, achse=k["achse"], phase=k["phase"])
                welt = pd["referenz_punkte"] @ R.T + k["position"]
            pd.points = welt
            if k.get("gruppen"):
                for g in k["gruppen"]:
                    if k["achse"] is None:
                        gw = g["pd"]["referenz_punkte"] + k["position"]
                    else:
                        gw = g["pd"]["referenz_punkte"] @ R.T + k["position"]
                    g["pd"].points = gw
                self._gruppen_actors(name, k)
            else:
                self._actors_aktualisieren(name, welt)
            self._overlays_aktualisieren(name, k, R)
        return True

    def status(self, text):
        self._renderer.set_status(text)

    def hud(self, text):
        self._renderer.set_hud(text)

    def layer_umschalten(self, layer):
        """Globaler Layer-Schalter (P5a)."""
        return self._layer.umschalten(layer)

    def layer_ist_an(self, layer):
        return self._layer.ist_an(layer)

    def _overlay_skala(self, koerper):
        """Achsen-Laenge + Marker-Radius aus der Koerpergroesse."""
        halbe = float(np.abs(koerper.punkte).max()) if len(koerper.punkte) else 0.0
        if halbe <= 0.0:
            halbe = 1.0
        laenge = 1.1 * halbe
        radius = min(max(0.040 * halbe, 0.020), 0.160)
        return laenge, radius

    def roehren_radius(self, koerper):
        """K4: Tube-Radius aus der Overlay-Skala (koerpergerecht)."""
        _laenge, marker_radius = self._overlay_skala(koerper)
        return max(0.25 * marker_radius, 0.006)

    def _roehre_oder_linie(self, pv, start, ende, farbe, radius, name):
        """K4: Achsen-Segment als Tube (pv.Line().tube()); Fallback Linie."""
        try:
            roehre = pv.Line(start, ende).tube(radius=radius, n_sides=12)
            return self._plotter.add_mesh(roehre, color=farbe, name=name,
                                          smooth_shading=True)
        except Exception:
            linie = pv.Line(start, ende)
            return self._plotter.add_mesh(linie, color=farbe, line_width=4,
                                          name=name)

    def _overlay_namen(self, name):
        return (["overlay_%s_schwerpunkt" % name]
                + ["overlay_%s_achse%d" % (name, i) for i in (1, 2, 3)])

    def _overlays_aktualisieren(self, name, k, R):
        koerper = k.get("koerper")
        if koerper is None:
            return
        _laenge, radius = k["overlay_skala"]
        cm = k["position"]
        if self._layer.ist_an(LAYER_SCHWERPUNKT):
            self._overlay_schwerpunkt_setzen(name, cm, radius)
        else:
            self._overlay_schwerpunkt_entfernen(name)
        if self._layer.ist_an(LAYER_HAUPTACHSEN):
            _werte, vektoren = hauptachsen(koerper.traegheitstensor)
            richtungen = vektoren @ R.T
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
        koerper = self._koerper[name].get("koerper")
        rr = self.roehren_radius(koerper) if koerper is not None else 0.01
        for i in range(3):
            l = laengen[i] if hasattr(laengen, "__len__") else laengen
            start = cm - l * richtungen[i]
            ende = cm + l * richtungen[i]
            store[namen[i + 1]] = self._roehre_oder_linie(
                pv, start, ende, OVERLAY_FARBEN_ACHSEN[i], rr, namen[i + 1])

    def _overlay_hauptachsen_entfernen(self, name):
        namen = self._overlay_namen(name)
        store = self._koerper.get(name, {}).get("overlay_actors", {})
        for n in namen[1:]:
            store.pop(n, None)
            try:
                self._plotter.remove_actor(n)
            except Exception:
                pass

    def _gruppen_actors(self, name, k):
        """Faerbt die Farbgruppen je Blatt (Material-Reform, K3-Glanz)."""
        import pyvista as pv
        p = self._plotter
        refs = k.setdefault("actors", {})
        for i, g in enumerate(k["gruppen"]):
            n_u = "koerper_%s_g%d_unten" % (name, i)
            n_o = "koerper_%s_g%d_oben" % (name, i)
            n_k = "kontur_%s_g%d" % (name, i)
            u_p, u_t, o_p, o_t, kontur = ws.schneide_am_wasser(
                np.asarray(g["pd"].points, float), g["dreiecke"],
                mit_deckel=True)
            kw_g = {"opacity": 0.95, "show_edges": False, "smooth_shading": True}
            if g.get("glanz") is not None:
                kw_g.update(glanz_kw(g["glanz"]))
            if len(u_t):
                un = _dreiecks_polydaten(pv, u_p, u_t)
                refs[n_u] = p.add_mesh(un, color=g["farbe_unten"], name=n_u,
                                       **kw_g)
            else:
                refs.pop(n_u, None)
                try:
                    p.remove_actor(n_u)
                except Exception:
                    pass
            if len(o_t):
                ob = _dreiecks_polydaten(pv, o_p, o_t)
                refs[n_o] = p.add_mesh(ob, color=g["farbe_oben"], name=n_o,
                                       **kw_g)
            else:
                refs.pop(n_o, None)
                try:
                    p.remove_actor(n_o)
                except Exception:
                    pass
            if len(kontur):
                linien = pv.line_segments_from_points(kontur)
                refs[n_k] = p.add_mesh(linien, color="black", line_width=3,
                                       name=n_k)
            else:
                refs.pop(n_k, None)
                try:
                    p.remove_actor(n_k)
                except Exception:
                    pass


def _gesichter(pd):
    f = np.asarray(pd.faces).reshape(-1, 4)
    return f[:, 1:4]
