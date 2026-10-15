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

Phase C (P5c, Umsetzungsplan V5 rev 9 §5): globaler GUI-Layer 'kraefte'.
Die Kraefte-Daten (Auftriebsergebnis + Skala) setzt die Demo ueber
kraefte_daten_setzen(); die Bruecke projiziert sie pro Frame (P5a-Muster:
Daten setzen, Renderer projiziert). D1: gemeinsame fixe Skala.

Spec V4A rev B: stoer_pose_setzen() friert einen Koerper in einer
voll 3-achsig gestoerten Anzeige-Pose ein (Basis wird gesichert und beim
Loeschen restauriert). Im Kraeftebild wird zusaetzlich der Drehmoment-
Bogenpfeil um die Rollachse gerendert (kb.moment_bogen, violett); im
Gleichgewicht verschwindet er automatisch (Zielbild Z3).
"""
from __future__ import annotations
import numpy as np

try:
    from . import wasser_schnitt as ws
except ImportError:
    from segelphysik import wasser_schnitt as ws
from .core.overlays import (LayerRegistry, hauptachsen,
                            LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                            LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT)
from .core import pfeilstil

FARBE_UNTEN = "#2166ac"
FARBE_OBEN = "#b2182b"

OVERLAY_FARBEN_ACHSEN = ("gold", "cyan", "magenta")

BASIN_LX, BASIN_LY, WASSER_TIEFE, DX = 10.0, 10.0, 3.0, 0.25
OZEAN_GROESSE = 2800.0   # Quadrat liegt komplett im Dunstring
DUNST_RADIUS = 2000.0
WASSER_FARBE = (44 / 255, 106 / 255, 153 / 255)
OZEAN_OPAZITAET = 0.88
VOLUMEN_HALB = 400.0    # Halbkante des Unterwasser-Volumens
VOLUMEN_TIEFE = 60.0
GLAS_FARBE = (30, 130, 135)
GLAS_ALPHA_OBEN = 0.10
GLAS_ALPHA_UNTEN = 0.30


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


def kb_strich(punkte, strich, luecke):
    from .core import kraefte_bild as kb
    return kb.strich_linien(punkte, strich, luecke)


def _mesh_actor_setzen(plotter, refs, name, mesh, **kwargs):
    actor = refs.get(name)
    if mesh is None:
        if actor is not None:
            actor.SetVisibility(False)
        return
    if actor is None:
        refs[name] = plotter.add_mesh(mesh, name=name, **kwargs)
        return
    actor.mapper.SetInputData(mesh)
    actor.mapper.Modified()
    actor.SetVisibility(True)


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

    _folge_aktiv = False
    _folge_letzt = None
    _wasserpunkte = None
    _wasserpunkte_meshes = {}
    _ozean_actor = None
    _dunst_actor = None
    _dunst_wand_actor = None
    _volumen_actor = None
    _ozean_mesh = None

    def __init__(self):
        self.app = StellvertreterApp()
        self._renderer = None
        self._plotter = None
        self._koerper = {}
        self._layer = LayerRegistry()
        self._kraefte_daten = {}
        self._stil = pfeilstil.Stil()
        self._vg_renderer = None
        self._vg_actors = {}
        self._vg_unmoeglich = False
        self._folge_aktiv = False
        self._folge_letzt = None
        self._wasserpunkte = None
        self._wasserpunkte_meshes = {}

    def wasser_bewegung_setzen(self, aktiv=True):
        """Koerper bleibt zentriert (Kamera folgt), ein weltfestes
        Punktfeld mit Schattenspuren zeigt die Bewegung im Wasser.
        Der einzige Darstellungsmodus; mehrfaches Aufrufen ist harmlos."""
        if self._plotter is None:
            return False
        if self._folge_aktiv:
            return True
        self._folge_aktiv = True
        from .core.wasserpunkte import WasserPunktFeld
        self._wasserpunkte = WasserPunktFeld()
        self._wasserpunkte_meshes = {}
        self._ozean_setzen()
        self._folge_letzt = None
        self.render()
        return True

    def _flaeche_verschieben(self, x, y):
        """Hinweis: Becken und Simulationsflaeche sind im Folgemodus
        ausgeblendet; die Ozeanebene folgt dem Koerper, die Textur wird
        gegen die Bewegung verschoben (Punkte bleiben weltfest)."""
        if self._ozean_actor is None:
            return
        self._ozean_actor.SetPosition(float(x), float(y), 0.0)
        for a in (self._dunst_actor, self._dunst_wand_actor,
                  self._volumen_actor):
            if a is not None:
                a.SetPosition(float(x), float(y), 0.0)

    def _becken_sichtbar_folge(self, sichtbar):
        """Beckenbox/Simulationsflaeche aus bzw. an (Folgemodus)."""
        actors = list(getattr(self._renderer, "_becken_actors", None) or [])
        a = getattr(self._renderer, "_surf_actor", None)
        if a is not None:
            actors.append(a)
        for akt in actors:
            akt.SetVisibility(bool(sichtbar))

    def _ozean_setzen(self):
        """Unendlich wirkende Wasserflaeche: grosse texturierte Ebene,
        die dem Koerper folgt; die Textur enthaelt die weltfesten Punkte."""
        import pyvista as pv
        from .core.wasserpunkte import dunst_gitter
        mesh = pv.Plane(center=(0.0, 0.0, -0.05), direction=(0, 0, 1),
                        i_size=OZEAN_GROESSE, j_size=OZEAN_GROESSE,
                        i_resolution=1, j_resolution=1)
        self._ozean_mesh = mesh
        self._ozean_actor = self._plotter.add_mesh(
            mesh, color=WASSER_FARBE, opacity=OZEAN_OPAZITAET,
            lighting=False, reset_camera=False, pickable=False)
        volumen = pv.Box(bounds=(-VOLUMEN_HALB, VOLUMEN_HALB,
                                 -VOLUMEN_HALB, VOLUMEN_HALB,
                                 -VOLUMEN_TIEFE, -0.06), level=8)
        # Glaseffekt: gruenlich-blaue Toenung, die mit der Tiefe dichter wird
        tiefe = np.clip(-volumen.points[:, 2] / VOLUMEN_TIEFE, 0.0, 1.0)
        glas = np.empty((volumen.n_points, 4), dtype=np.uint8)
        glas[:, :3] = GLAS_FARBE
        glas[:, 3] = (255 * (GLAS_ALPHA_OBEN + (GLAS_ALPHA_UNTEN
                      - GLAS_ALPHA_OBEN) * tiefe ** 0.5)).astype(np.uint8)
        volumen["rgba"] = glas
        self._volumen_actor = self._plotter.add_mesh(
            volumen, scalars="rgba", rgba=True,
            lighting=False, reset_camera=False, pickable=False)
        punkte, flaechen, rgba = dunst_gitter(r_aussen=DUNST_RADIUS)
        # Ring und Wand getrennt: Transparente Actors werden nach Abstand
        # ihres Mittelpunkts sortiert; der Ring muss nach der Wasserebene
        # gezeichnet werden, sonst ueberdeckt diese den Dunst.
        n_ring = (28 - 1) * 96
        for name, fl in (("ring", flaechen[:n_ring]),
                         ("wand", flaechen[n_ring:])):
            dunst = pv.PolyData(punkte, faces=fl.ravel())
            dunst["rgba"] = rgba
            actor = self._plotter.add_mesh(
                dunst, scalars="rgba", rgba=True, lighting=False,
                reset_camera=False, pickable=False)
            if name == "ring":
                self._dunst_actor = actor
            else:
                self._dunst_wand_actor = actor
        self._becken_sichtbar_folge(False)
        self._koerper_opazitaet_setzen(1.0)
        self._flaeche_verschieben(0.0, 0.0)

    def _koerper_opazitaet(self):
        return 1.0 if self._folge_aktiv else 0.95

    def _koerper_opazitaet_setzen(self, wert):
        """Koerper undurchsichtig, damit Wasserpunkte und Spuren nie
        durch sie hindurch sichtbar sind."""
        for k in self._koerper.values():
            for n, a in k.get("actors", {}).items():
                if n.startswith("koerper_"):
                    a.GetProperty().SetOpacity(float(wert))

    def _wasser_bewegung_nachfuehren(self, position):
        if not self._folge_aktiv or self._plotter is None:
            return
        xy = np.asarray(position, dtype=np.float64)[:2]
        if self._folge_letzt is not None:
            delta = np.array([xy[0] - self._folge_letzt[0],
                              xy[1] - self._folge_letzt[1], 0.0])
            kamera = self._plotter.camera
            kamera.position = tuple(np.asarray(kamera.position) + delta)
            kamera.focal_point = tuple(np.asarray(kamera.focal_point) + delta)
        self._folge_letzt = xy.copy()
        self._flaeche_verschieben(xy[0], xy[1])
        self._wasserpunkte_zeichnen(xy)

    def _wasserpunkte_zeichnen(self, xy):
        import pyvista as pv
        punkte, spuren, alpha = self._wasserpunkte.aktualisieren(xy)
        n, s, _ = spuren.shape
        if n == 0:
            return

        def rgba(a):
            farbe = np.empty((a.size, 4), dtype=np.uint8)
            farbe[:, :3] = 255
            farbe[:, 3] = np.clip(a * 255.0, 0, 255).astype(np.uint8)
            return farbe

        linien = np.empty((n * (s - 1), 3), dtype=np.int64)
        basis = (np.arange(n)[:, None] * s + np.arange(s - 1)[None, :]).ravel()
        linien[:, 0] = 2
        linien[:, 1] = basis
        linien[:, 2] = basis + 1
        spur = pv.PolyData(spuren.reshape(-1, 3), lines=linien.ravel())
        spur["rgba"] = rgba(alpha.ravel())
        for name, mesh, kw in (
                ("wasser_spuren", spur, dict(line_width=2)),):
            alt = self._wasserpunkte_meshes.get(name)
            if alt is None:
                self._plotter.add_mesh(mesh, scalars="rgba", rgba=True,
                                       name=name, lighting=False,
                                       reset_camera=False, pickable=False,
                                       **kw)
                self._wasserpunkte_meshes[name] = mesh
            else:
                alt.copy_from(mesh)

    def fenster_bauen(self):
        try:
            from .render.vista import PyVistaRenderer
        except ImportError:
            from segelphysik.render.vista import PyVistaRenderer
        self._renderer = PyVistaRenderer(self.app)
        self._renderer.skip_surf = False
        p = self._renderer.build()
        self._plotter = p
        return p

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
        self._koerper_ersetzen(name)
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

    def _koerper_ersetzen(self, name):
        alt = self._koerper.get(name)
        if alt is None:
            return
        if self._plotter is not None:
            namen = (self._actor_namen(name) + self._overlay_namen(name)
                     + self._kraefte_namen(name))
            for actor_name in namen:
                self._actor_weg(actor_name)
        self._koerper.pop(name)
        self._kraefte_daten.pop(name, None)

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

        kw_basis = {"opacity": self._koerper_opazitaet(), "show_edges": False,
                    "smooth_shading": True}
        if glanz is not None:
            kw_basis.update(glanz_kw(glanz))

        _mesh_actor_setzen(
            p, refs, n_unten,
            _dreiecks_polydaten(pv, u_p, u_t) if len(u_t) else None,
            color=farbe_u, **kw_basis)
        _mesh_actor_setzen(
            p, refs, n_oben,
            _dreiecks_polydaten(pv, o_p, o_t) if len(o_t) else None,
            color=farbe_o, **kw_basis)
        _mesh_actor_setzen(
            p, refs, n_kontur,
            pv.line_segments_from_points(kontur) if len(kontur) else None,
            color="black", line_width=3)

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
            for n in self._actor_namen(name) + self._overlay_namen(name) \
                    + self._kraefte_namen(name):
                try:
                    self._actor_weg(n)
                except Exception:
                    pass
            k["actors"] = {}
            k["overlay_actors"] = {}
            k["kraefte_actors"] = {}

    def aktualisieren(self, t):
        from .core import bewegung as kin
        for name, k in self._koerper.items():
            if not k["aktiv"]:
                continue
            pd = k["pd"]
            if k.get("statisch_R") is not None:
                R = k["statisch_R"]   # B2/V4A: eingefrorene (statische oder Stoer-) Lage
            elif k["achse"] is None:
                R = np.eye(3)
            else:
                R, _ = kin.koerper_pose(t, achse=k["achse"], phase=k["phase"])
            welt = pd["referenz_punkte"] @ R.T + k["position"]
            pd.points = welt
            if k.get("gruppen"):
                for g in k["gruppen"]:
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

    def statusoverlay_setzen(self, text, schwere="info"):
        if self._renderer is None:
            return False
        return self._renderer.set_statusoverlay(text, schwere)

    def kamera_preset_setzen(self, preset):
        if self._plotter is None:
            return False
        from .grafik_optimierung import kamera_presets
        presets = kamera_presets(
            self.app.cfg.basin["lx"], self.app.cfg.basin["ly"],
            self.app.cfg.water["depth"])
        if preset not in presets:
            raise ValueError("Unbekanntes Kamera-Preset: %s" % preset)
        self._plotter.camera_position = presets[preset]
        if self._folge_aktiv and self._folge_letzt is not None:
            delta = np.array([self._folge_letzt[0], self._folge_letzt[1], 0.0])
            kamera = self._plotter.camera
            kamera.position = tuple(np.asarray(kamera.position) + delta)
            kamera.focal_point = tuple(np.asarray(kamera.focal_point) + delta)
        self.render()
        return True

    def hintergrund_setzen(self, preset):
        if self._plotter is None:
            return False
        hintergruende = {
            "verlauf": ("#f2f7fc", "#9dc3e6"),
            "weiss": ("white", None),
            "dunkel": ("#202124", None),
        }
        if preset not in hintergruende:
            raise ValueError("Unbekannter Hintergrund: %s" % preset)
        farbe, oben = hintergruende[preset]
        if oben is None:
            self._plotter.set_background(farbe)
        else:
            self._plotter.set_background(farbe, top=oben)
        self.render()
        return True

    def beleuchtung_setzen(self, aktiviert):
        if self._plotter is None:
            return False
        if aktiviert:
            self._plotter.enable_lightkit()
        else:
            self._plotter.remove_all_lights()
        self.render()
        return True

    def ssao_setzen(self, aktiviert):
        if self._plotter is None:
            return False
        if aktiviert:
            try:
                self._plotter.enable_ssao(radius=0.8, bias=0.002)
            except TypeError:
                self._plotter.enable_ssao()
        else:
            self._plotter.disable_ssao()
        self.render()
        return True

    def wasser_sichtbar_setzen(self, sichtbar):
        if self._renderer is None:
            return False
        gesetzt = self._renderer.wasser_sichtbar_setzen(sichtbar)
        if self._ozean_actor is not None:
            self._ozean_actor.SetVisibility(bool(sichtbar))
            for a in (self._dunst_actor, self._dunst_wand_actor,
                      self._volumen_actor):
                if a is not None:
                    a.SetVisibility(bool(sichtbar))
            self._becken_sichtbar_folge(False)
        if gesetzt:
            self.render()
        return gesetzt

    def wasseroptik_setzen(self, aktiviert):
        if self._renderer is None:
            return False
        gesetzt = self._renderer.wasseroptik_setzen(aktiviert)
        if gesetzt:
            self.render()
        return gesetzt

    def render(self):
        if self._plotter is None:
            return False
        self._vordergrund_kamera_abgleichen()
        self._plotter.render()
        return True

    def layer_umschalten(self, layer):
        """Globaler Layer-Schalter (P5a)."""
        aktiv = self._layer.umschalten(layer)
        self._layer_aktualisieren()
        return aktiv

    def layer_setzen(self, layer, aktiv):
        """Setzt einen globalen Layer und aktualisiert seine Geometrie."""
        self._layer.setzen(layer, aktiv)
        self._layer_aktualisieren()

    def _layer_aktualisieren(self):
        for name, k in self._koerper.items():
            if k.get("aktiv"):
                self._overlays_aktualisieren(
                    name, k, k.get("statisch_R", np.eye(3)))

    def layer_ist_an(self, layer):
        return self._layer.ist_an(layer)

    # ---------------- Phase C: Kraeftebild (Taste 7) ----------------

    def kraefte_daten_setzen(self, name, erg, masse, g, skala, fremd=None):
        """Speichert die Kraefte-Daten eines Objekts (P5a-Muster: die Demo
        setzt die Wahrheit, die Bruecke projiziert sie pro Frame).
        fremd: ((fx, fy, fz) Welt, (x, y, z) koerperfest rel. Schwerpunkt)."""
        self._kraefte_daten[name] = {"erg": erg, "masse": float(masse),
                                     "g": float(g), "skala": float(skala),
                                     "fremd": fremd}

    def kraefte_daten_entfernen(self, name):
        self._kraefte_daten.pop(name, None)

    # Pfeil-id -> Namensendung des Actors (Name: kraefte_<koerper>_<endung>)
    _ACTOR_ENDUNG = {
        "f_g": "fg", "f_a": "fa", "hebelarm": "arm", "m_x": "moment",
        "m_y": "moment_y", "m_z": "moment_z", "rest": "rest",
        "zusatz": "zusatz", "fremd": "fremd", "fremd_mx": "fremdm_x",
        "fremd_my": "fremdm_y", "fremd_mz": "fremdm_z",
        "mges_x": "mges_x", "mges_y": "mges_y", "mges_z": "mges_z",
    }

    def _kraefte_namen(self, name):
        return ["kraefte_%s_fg" % name, "kraefte_%s_fa" % name,
                "kraefte_%s_arm" % name, "kraefte_%s_moment" % name,
                "kraefte_%s_moment_y" % name, "kraefte_%s_moment_z" % name,
                "kraefte_%s_rest" % name, "kraefte_%s_zusatz" % name,
                "kraefte_%s_auftriebsp" % name, "kraefte_%s_fremd" % name,
                "kraefte_%s_fremdm_x" % name, "kraefte_%s_fremdm_y" % name,
                "kraefte_%s_fremdm_z" % name, "kraefte_%s_mges_x" % name,
                "kraefte_%s_mges_y" % name, "kraefte_%s_mges_z" % name,
                "kraefte_%s_auftriebsp_kontur" % name]

    def _pfeil_name(self, name, pfeil_id):
        return "kraefte_%s_%s" % (name, self._ACTOR_ENDUNG[pfeil_id])

    # ---------------- Darstellung: Stil und Vordergrundebene ----------------

    def stil_setzen(self, stil):
        """Neuer Pfeilstil (core.pfeilstil.Stil): alle Pfeile, Schwerpunkte
        und Hauptachsen werden mit den neuen Massen neu aufgebaut."""
        self._stil = stil
        for name in list(self._koerper):
            self._kraefte_entfernen(name)
            self._overlay_schwerpunkt_entfernen(name)
            self._overlay_hauptachsen_entfernen(name)
        self._layer_aktualisieren()
        self.render()

    def _ausdehnung(self, k):
        """Groesste Koerperausdehnung (m) als Bezug fuer relative Masse."""
        try:
            punkte = np.asarray(k["koerper"].punkte, dtype=float)
            ausdehnung = float(np.ptp(punkte, axis=0).max())
        except Exception:
            laenge = k.get("overlay_skala", (1.1, 0.04))[0]
            ausdehnung = 2.0 * float(laenge) / 1.1
        return max(ausdehnung, 0.05)

    def _vordergrund_renderer(self):
        """Zweite Renderebene (Layer 1) mit eigenem Tiefenpuffer ueber der
        Szene und gemeinsamer Kamera: ihre Actors sind nie verdeckt."""
        if self._vg_renderer is None:
            from vtkmodules.vtkRenderingCore import vtkRenderer
            fenster = self._plotter.ren_win
            fenster.SetNumberOfLayers(2)
            self._plotter.renderer.SetLayer(0)
            renderer = vtkRenderer()
            renderer.SetLayer(1)
            renderer.InteractiveOff()
            fenster.AddRenderer(renderer)
            self._vg_renderer = renderer
        self._vg_renderer.SetActiveCamera(
            self._plotter.renderer.GetActiveCamera())
        return self._vg_renderer

    def _vordergrund_kamera_abgleichen(self):
        """Pyvista kann die Kamera austauschen: Vordergrund folgt ihr."""
        if getattr(self, "_vg_renderer", None) is not None \
                and self._plotter is not None:
            kamera = self._plotter.renderer.GetActiveCamera()
            if self._vg_renderer.GetActiveCamera() is not kamera:
                self._vg_renderer.SetActiveCamera(kamera)

    def _actor_weg(self, name):
        actor = self._vg_actors.pop(name, None)
        if actor is not None:
            if self._vg_renderer is not None:
                self._vg_renderer.RemoveActor(actor)
            return
        try:
            self._plotter.remove_actor(name)
        except Exception:
            pass

    def _actor_neu(self, name, mesh, **kwargs):
        """Neuer Actor in der Vordergrundebene; None, wenn nicht moeglich."""
        if self._vg_unmoeglich:
            return None
        try:
            renderer = self._vordergrund_renderer()
            actor = self._plotter.add_mesh(
                mesh, name=name, reset_camera=False, render=False,
                pickable=False, **kwargs)
            self._plotter.remove_actor(
                actor, reset_camera=False, render=False)
            renderer.AddActor(actor)
            self._vg_actors[name] = actor
            return actor
        except Exception as fehler:
            self._vg_unmoeglich = True
            import sys
            print("[SegelPhysik] Vordergrundebene nicht moeglich: %r" % fehler,
                  file=sys.stderr, flush=True)
            return None

    def _mesh_setzen(self, store, name, mesh, vordergrund=False, **kwargs):
        """Wie _mesh_actor_setzen, optional in der Vordergrundebene."""
        actor = store.get(name)
        if actor is not None and mesh is not None:
            if (name in self._vg_actors) != (
                    vordergrund and not self._vg_unmoeglich):
                self._actor_weg(name)
                store.pop(name, None)
                actor = None
        if actor is None and mesh is not None and vordergrund:
            neu = self._actor_neu(name, mesh, **kwargs)
            if neu is not None:
                store[name] = neu
                return
        _mesh_actor_setzen(self._plotter, store, name, mesh, **kwargs)

    def _stil_pfeil(self, pfeil_id, k):
        return self._stil.pfeil(pfeil_id, self._ausdehnung(k))

    def _kraftpfeil_zeichnen(self, store, name, st, pfeil):
        import pyvista as pv
        kw = {"color": st["farbe"], "opacity": st["deckkraft"],
              "smooth_shading": True}
        try:
            if st["gestrichelt"]:
                punkte, zellen = kb_strich(
                    [pfeil["schaft_start"], pfeil["schaft_ende"]],
                    st["strich"], st["luecke"])
                linie = pv.PolyData(punkte, lines=zellen)
            else:
                linie = pv.Line(tuple(pfeil["schaft_start"]),
                                tuple(pfeil["schaft_ende"]))
            schaft = linie.tube(radius=pfeil["schaft_radius"], n_sides=8,
                                capping=True)
            kopf = pv.Cone(
                center=tuple(0.5 * (pfeil["schaft_ende"] + pfeil["spitze"])),
                direction=tuple(pfeil["richtung"]),
                height=pfeil["kopf_laenge"], radius=pfeil["kopf_radius"],
                resolution=16)
            self._mesh_setzen(store, name, schaft + kopf,
                              st["vordergrund"], **kw)
        except Exception:
            linie = pv.line_segments_from_points(
                [tuple(pfeil["start"]), tuple(pfeil["spitze"])])
            self._mesh_setzen(
                store, name, linie, st["vordergrund"], color=st["farbe"],
                opacity=st["deckkraft"], line_width=5)

    def _momentbogen_zeichnen(self, store, name, st, moment, mitte, radius,
                              achse):
        """Zeichnet den Bogen; False, wenn das Moment verschwindet."""
        import pyvista as pv
        from .core import kraefte_bild as kb
        bogen = kb.moment_bogen_achse(moment, mitte, radius, achse)
        if bogen is None:
            return False
        kopf_l = min(st["kopf_laenge"], 0.5 * radius)
        kopf_r = 0.5 * st["kopf_durchmesser"] * kopf_l / max(
            st["kopf_laenge"], 1e-12)
        punkte = bogen["punkte"]
        spitze = punkte[-1] + kopf_l * bogen["richtung"]
        kw = {"color": st["farbe"], "opacity": st["deckkraft"],
              "smooth_shading": True}
        try:
            if st["gestrichelt"]:
                dpunkte, zellen = kb_strich(
                    punkte, st["strich"], st["luecke"])
                linie = pv.PolyData(dpunkte, lines=zellen)
            else:
                linie = pv.lines_from_points(punkte)
            kurve = linie.tube(radius=0.5 * st["durchmesser"], n_sides=8,
                               capping=True)
            kopf = pv.Cone(center=tuple(0.5 * (punkte[-1] + spitze)),
                           direction=tuple(bogen["richtung"]),
                           height=kopf_l, radius=kopf_r, resolution=16)
            self._mesh_setzen(store, name, kurve + kopf,
                              st["vordergrund"], **kw)
        except Exception:
            seg = pv.line_segments_from_points(punkte)
            self._mesh_setzen(store, name, seg, st["vordergrund"],
                              color=st["farbe"], line_width=4)
        return True

    def _kugel_zeichnen(self, store, name, mitte, radius, farbe, kontur,
                        kontur_breite, vordergrund):
        """Schwerpunktkugel; die Kontur ist eine groessere Hohlkugel
        (Vorderseiten ausgeblendet), die nur den Rand zeigt."""
        import pyvista as pv
        kugel = pv.Sphere(center=tuple(mitte), radius=radius,
                          theta_resolution=24, phi_resolution=24)
        self._mesh_setzen(store, name, kugel, vordergrund, color=farbe)
        n_kontur = name + "_kontur"
        if not kontur:
            self._actor_weg(n_kontur)
            store.pop(n_kontur, None)
            return
        huelle = pv.Sphere(center=tuple(mitte),
                           radius=radius * (1.0 + kontur_breite),
                           theta_resolution=24, phi_resolution=24)
        self._mesh_setzen(store, n_kontur, huelle, vordergrund,
                          color=kontur, lighting=False)
        actor = store.get(n_kontur)
        if actor is not None and hasattr(actor, "GetProperty"):
            actor.GetProperty().SetFrontfaceCulling(True)

    def _kraefte_actors(self, name):
        """Baut die Kraefte-Actors aus den gesetzten Daten (Kraeftepaare,
        Momentenboegen, Hebelarm, Auftriebsschwerpunkt)."""
        from .core import kraefte_bild as kb
        import pyvista as pv
        daten = self._kraefte_daten.get(name)
        if daten is None:
            return
        k = self._koerper.get(name)
        if k is None or not k.get("aktiv"):
            return
        erg = daten["erg"]
        ausdehnung = self._ausdehnung(k)
        allg = self._stil.allgemein(ausdehnung)
        skala = allg["kraftskala"]
        cm = np.asarray(k["position"], float)
        r_s = cm   # P1: r_S liegt im Ursprung des Koerperframes -> Weltposition = cm
        store = k.setdefault("kraefte_actors", {})
        gezeichnet = set()

        def kraft(pfeil_id, start, vektor, schwelle=1e-9):
            """Kraftpfeil mit fester Dicke; False wenn unsichtbar."""
            st = self._stil_pfeil(pfeil_id, k)
            vektor = np.asarray(vektor, dtype=float) * skala * st["skala"]
            if not st["sichtbar"] or float(np.linalg.norm(vektor)) <= schwelle:
                return False
            pfeil = kb.pfeil_fest(
                start, vektor, st["durchmesser"], st["kopf_durchmesser"],
                st["kopf_laenge"], st["mindestlaenge"])
            n = self._pfeil_name(name, pfeil_id)
            self._kraftpfeil_zeichnen(store, n, st, pfeil)
            gezeichnet.add(n)
            return True

        def momente(praefix, vektor):
            for achse, achse_name in enumerate("xyz"):
                pfeil_id = praefix + achse_name
                st = self._stil_pfeil(pfeil_id, k)
                if not st["sichtbar"]:
                    continue
                n = self._pfeil_name(name, pfeil_id)
                radius = (allg["momentskala"] * abs(float(vektor[achse]))
                          * st["skala"])
                radius = max(radius, st["mindestlaenge"])
                if radius > 0.0 and self._momentbogen_zeichnen(
                        store, n, st, float(vektor[achse]), r_s, radius,
                        achse):
                    gezeichnet.add(n)

        if self._layer.ist_an(LAYER_KRAEFTE):
            kraft("f_g", r_s, (0.0, 0.0, -daten["masse"] * daten["g"]), 0.0)
            kraft("f_a", erg.K.as_array(), (0.0, 0.0, erg.F_A.z), 0.0)
            f_ges = erg.F_gesamt.as_array()
            fg = np.array([0.0, 0.0, -daten["masse"] * daten["g"]])
            kraft("rest", r_s, f_ges + fg, 1e-6)
            kraft("zusatz", r_s, f_ges - erg.F_A.as_array(), 1e-6)
            st = self._stil_pfeil("hebelarm", k)
            a, b = kb.hebelarm_segment(erg.K.as_array(), r_s)
            if st["sichtbar"] and float(np.linalg.norm(a - b)) > 1e-9:
                n = self._pfeil_name(name, "hebelarm")
                try:
                    arm = pv.Line(tuple(a), tuple(b)).tube(
                        radius=0.5 * st["durchmesser"], n_sides=8)
                    self._mesh_setzen(
                        store, n, arm, st["vordergrund"], color=st["farbe"],
                        opacity=st["deckkraft"], smooth_shading=True)
                    gezeichnet.add(n)
                except Exception:
                    pass

        fremd_kraft = fremd_angriff = None
        if daten.get("fremd") is not None:
            kraft_f = np.asarray(daten["fremd"][0], float)
            if float(np.linalg.norm(kraft_f)) > 1e-9:
                R = k.get("statisch_R")
                R = np.eye(3) if R is None else np.asarray(R, float)
                fremd_kraft = kraft_f
                fremd_angriff = cm + R @ np.asarray(daten["fremd"][1], float)
        fremd_an = (self._layer.ist_an(LAYER_FREMDKRAFT)
                    and fremd_kraft is not None)
        if fremd_an:
            kraft("fremd", fremd_angriff, fremd_kraft)

        if self._layer.ist_an(LAYER_MOMENTE):
            momente("m_", kb.paar_moment_auftrieb(erg, r_s))
            momente("mges_", erg.M.as_array())
            if fremd_an:
                momente("fremd_m", kb.paar_moment_kraft(
                    fremd_angriff, fremd_kraft, r_s))

        auftriebsp = "kraefte_%s_auftriebsp" % name
        if self._layer.ist_an(LAYER_SCHWERPUNKT):
            sp = self._stil.schwerpunkte(ausdehnung)
            self._kugel_zeichnen(
                store, auftriebsp, erg.K.as_array(), sp["k_radius"],
                sp["k_farbe"], sp["s_kontur"], sp["kontur_breite"],
                sp["vordergrund"])
            gezeichnet.update((auftriebsp, auftriebsp + "_kontur"))
        self._kraefte_actors_entfernen(
            name, [n for n in self._kraefte_namen(name)
                   if n not in gezeichnet])

    def _kraefte_actors_entfernen(self, name, namen):
        store = self._koerper.get(name, {}).get("kraefte_actors", {})
        for actor_name in namen:
            if store.pop(actor_name, None) is None:
                continue
            try:
                self._actor_weg(actor_name)
            except Exception:
                pass

    def _kraefte_entfernen(self, name):
        store = self._koerper.get(name, {}).get("kraefte_actors", {})
        for n in self._kraefte_namen(name):
            if store.pop(n, None) is None:
                continue
            try:
                self._actor_weg(n)
            except Exception:
                pass

    def statische_pose_setzen(self, name, z, phi):
        """Phase B2: friert den Koerper in der statischen Gleichgewichts-
        lage ein (D11: r_S bei Welt-z = z, Rotation R_x(phi) um r_S)."""
        return self.physik_pose_setzen(name, z, phi)

    def physik_pose_setzen(self, name, z, phi):
        """Wendet Tauchposition und Kraengung auf einen Laufzeitkoerper an."""
        k = self._koerper.get(name)
        if k is None:
            return False
        c, s = np.cos(float(phi)), np.sin(float(phi))
        R = np.array([[1.0, 0.0, 0.0],
                      [0.0, c, -s],
                      [0.0, s, c]])
        basis = self.physik_basis_position_ermitteln(name)
        position = np.array([basis[0], basis[1], float(z)])
        return self.physik_pose_6dof_setzen(name, R, position)

    def physik_basis_position_ermitteln(self, name):
        """Liefert die unveraenderte Startposition des Koerper-Schwerpunkts."""
        k = self._koerper.get(name)
        if k is None:
            raise ValueError("Koerper %r fehlt in der 3D-Ansicht" % name)
        basis = k.get("position_basis", k["position"])
        return np.asarray(basis, dtype=np.float64).copy()

    def physik_pose_6dof_setzen(self, name, rotation, position):
        """Wendet eine vollstaendige starre 3D-Pose im GUI-Thread an."""
        k = self._koerper.get(name)
        if k is None:
            return False
        rotation = np.asarray(rotation, dtype=np.float64)
        position = np.asarray(position, dtype=np.float64)
        if (rotation.shape != (3, 3) or position.shape != (3,)
                or not np.isfinite(rotation).all()
                or not np.isfinite(position).all()
                or not np.allclose(rotation.T @ rotation, np.eye(3),
                                   rtol=0.0, atol=1e-8)
                or not np.isclose(np.linalg.det(rotation), 1.0,
                                  rtol=0.0, atol=1e-8)):
            raise ValueError("3D-Pose muss eine endliche starre Rotation "
                             "und Position enthalten")
        if "position_basis" not in k:
            k["position_basis"] = np.asarray(k["position"], float).copy()
        k["statisch_R"] = rotation.copy()
        k["position"] = position.copy()
        self._statisch_anwenden(name, k)
        self._wasser_bewegung_nachfuehren(position)
        return True

    def stoer_pose_setzen(self, name, R, position):
        """Spec V4A: friert den Koerper in der voll 3-achsig gestoerten
        Anzeige-Pose ein (St-2). Basis wird einmalig gesichert und beim
        Loeschen restauriert - kein Drift ueber mehrere Stoerungen (Z4)."""
        k = self._koerper.get(name)
        if k is None:
            return False
        if "position_basis" not in k:
            k["position_basis"] = np.asarray(k["position"], float).copy()
        k["statisch_R"] = np.asarray(R, float)
        k["position"] = np.asarray(position, float).copy()
        self._statisch_anwenden(name, k)
        return True

    def stoer_pose_loeschen(self, name):
        """Gibt die Stoerpose frei (Basis zurueck, Animation uebernimmt)."""
        return self.statische_pose_loeschen(name)

    def statische_pose_loeschen(self, name):
        """Gibt die Pose wieder frei (Modus r/z): Basis-Position zurueck,
        die Animation uebernimmt wieder."""
        k = self._koerper.get(name)
        if k is None or "position_basis" not in k:
            return False
        k["position"] = k["position_basis"].copy()
        k.pop("statisch_R", None)
        k.pop("position_basis", None)
        self._statisch_anwenden(name, k)
        return True

    def _statisch_anwenden(self, name, k):
        """Wendet die aktuelle (statische oder freigegebene) Pose an."""
        pd = k["pd"]
        R = k.get("statisch_R")
        if R is None:
            R = np.eye(3)
        welt = pd["referenz_punkte"] @ R.T + k["position"]
        pd.points = welt
        if not k.get("aktiv", True):
            # Ausgeblendete Koerper (Objektwechsel) duerfen ihre Actors
            # nicht neu aufbauen, sonst ueberlagern sie den neuen Koerper.
            return
        if k.get("gruppen"):
            for g in k["gruppen"]:
                g["pd"].points = g["pd"]["referenz_punkte"] @ R.T + k["position"]
            self._gruppen_actors(name, k)
        else:
            self._actors_aktualisieren(name, welt)
        self._overlays_aktualisieren(name, k, R)

    def kraefte_entfernen(self, name):
        """Oeffentlich: entfernt Actors + Daten (Objektwechsel)."""
        self._kraefte_entfernen(name)
        self.kraefte_daten_entfernen(name)

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

    def _roehre_oder_linie(
            self, pv, start, ende, farbe, radius, name, actor=None):
        """K4: Achsen-Segment als Tube (pv.Line().tube()); Fallback Linie."""
        try:
            mesh = pv.Line(start, ende).tube(radius=radius, n_sides=12)
            kwargs = {"color": farbe, "smooth_shading": True}
        except Exception:
            mesh = pv.Line(start, ende)
            kwargs = {"color": farbe, "line_width": 4}
        if actor is None:
            return self._plotter.add_mesh(mesh, name=name, **kwargs)
        actor.mapper.SetInputData(mesh)
        actor.mapper.Modified()
        actor.SetVisibility(True)
        return actor

    def _overlay_namen(self, name):
        return (["overlay_%s_schwerpunkt" % name]
                + ["overlay_%s_achse%d" % (name, i) for i in (1, 2, 3)]
                + ["overlay_%s_schwerpunkt_kontur" % name])

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
        # Phase C: Kraeftebild nur, wenn Layer an UND Daten vorliegen.
        if ((self._layer.ist_an(LAYER_KRAEFTE)
             or self._layer.ist_an(LAYER_MOMENTE)
             or self._layer.ist_an(LAYER_FREMDKRAFT)
             or self._layer.ist_an(LAYER_SCHWERPUNKT))
                and name in self._kraefte_daten):
            self._kraefte_actors(name)
        else:
            self._kraefte_entfernen(name)

    def _overlay_schwerpunkt_setzen(self, name, cm, radius=None):
        n = self._overlay_namen(name)[0]
        k = self._koerper[name]
        store = k.setdefault("overlay_actors", {})
        sp = self._stil.schwerpunkte(self._ausdehnung(k))
        self._kugel_zeichnen(
            store, n, cm, sp["s_radius"], sp["s_farbe"], sp["s_kontur"],
            sp["kontur_breite"], sp["vordergrund"])

    def _overlay_schwerpunkt_entfernen(self, name):
        namen = self._overlay_namen(name)
        store = self._koerper.get(name, {}).get("overlay_actors", {})
        for n in (namen[0], namen[4]):
            if store.pop(n, None) is None:
                continue
            self._actor_weg(n)

    def _overlay_hauptachsen_setzen(self, name, cm, richtungen, laengen):
        import pyvista as pv
        namen = self._overlay_namen(name)
        k = self._koerper[name]
        store = k.setdefault("overlay_actors", {})
        ha = self._stil.hauptachsen(self._ausdehnung(k))
        rr = 0.5 * ha["durchmesser"]
        for i in range(3):
            l = laengen[i] if hasattr(laengen, "__len__") else laengen
            start = cm - l * richtungen[i]
            ende = cm + l * richtungen[i]
            try:
                mesh = pv.Line(start, ende).tube(radius=rr, n_sides=12)
                kw = {"color": ha["farben"][i], "smooth_shading": True}
            except Exception:
                mesh = pv.Line(start, ende)
                kw = {"color": ha["farben"][i], "line_width": 4}
            self._mesh_setzen(store, namen[i + 1], mesh, ha["vordergrund"],
                              **kw)

    def _overlay_hauptachsen_entfernen(self, name):
        namen = self._overlay_namen(name)
        store = self._koerper.get(name, {}).get("overlay_actors", {})
        for n in namen[1:4]:
            if store.pop(n, None) is None:
                continue
            self._actor_weg(n)

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
            kw_g = {"opacity": self._koerper_opazitaet(), "show_edges": False,
                    "smooth_shading": True}
            if g.get("glanz") is not None:
                kw_g.update(glanz_kw(g["glanz"]))
            _mesh_actor_setzen(
                p, refs, n_u,
                _dreiecks_polydaten(pv, u_p, u_t) if len(u_t) else None,
                color=g["farbe_unten"], **kw_g)
            _mesh_actor_setzen(
                p, refs, n_o,
                _dreiecks_polydaten(pv, o_p, o_t) if len(o_t) else None,
                color=g["farbe_oben"], **kw_g)
            _mesh_actor_setzen(
                p, refs, n_k,
                pv.line_segments_from_points(kontur) if len(kontur) else None,
                color="black", line_width=3)


def _gesichter(pd):
    f = np.asarray(pd.faces).reshape(-1, 4)
    return f[:, 1:4]
