"""Grafik-Bruecke V3 (Additivprinzip): verbindet die fertige v0.4-
Render-Pipeline (code/python/segelphysik/render/vista.py) mit der
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
import math
import numpy as np

try:
    from . import wasser_schnitt as ws
except ImportError:
    from segelphysik import wasser_schnitt as ws
from .core.overlays import (LayerRegistry, hauptachsen,
                            LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                            LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT,
                            LAYER_HYDRO_RUMPF, LAYER_HYDRO_KIEL,
                            LAYER_HYDRO_RUDER)
from .core.frames import pose_mit_gelenkwinkel
from .core.rechenpfad import rechenpfad
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
    return _dreiecks_polydaten(pv, vertices, gesichter)


def _dreiecks_polydaten(pv, punkte, dreiecke):
    dreiecke = np.asarray(dreiecke, dtype=np.int64)
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden
        faces = native_laden().grafik_dreieckszellen(dreiecke)
        return pv.PolyData(np.asarray(punkte, dtype=np.float64), faces.ravel())
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
    def hat_gelenk(knoten):
        return (
            knoten.gelenkdefinition is not None
            or any(hat_gelenk(kind) for kind, _pose in knoten.teile))

    gelenke = bool(koerper.teile) and hat_gelenk(koerper)
    if koerper.teile and rechenpfad() == "cpp":
        return _farbgruppen_nativ(koerper, gelenke)
    if gelenke:
        gruppen = []

        def sammle(knoten, rotation, translation):
            for kind, _pose in knoten.teile:
                pose = pose_mit_gelenkwinkel(
                    kind.basis_pose,
                    kind.gelenkdefinition,
                    kind.gelenkwinkel_rad,
                )
                kind_rotation = rotation @ pose.rotationsmatrix
                kind_translation = (
                    translation + rotation @ np.asarray(pose.translation_m))
                if kind.teile:
                    sammle(kind, kind_rotation, kind_translation)
                    continue
                if not len(kind.dreiecke):
                    continue
                schwerpunkt = (
                    kind_translation
                    + kind_rotation @ np.asarray(kind._r_eingabe, float))
                gruppen.append({
                    "knoten_id": kind.knoten_id,
                    "punkte": kind.punkte @ kind_rotation.T + schwerpunkt,
                    "dreiecke": np.asarray(kind.dreiecke, np.int64),
                    "farbe_oben": kind.farbe,
                    "farbe_unten": kind.unterwasser_farbe(),
                    "glanz": kind.glanz,
                })

        sammle(
            koerper,
            np.eye(3),
            -np.asarray(koerper._r_eingabe, dtype=np.float64),
        )
        return gruppen

    if not getattr(koerper, "teile", None):
        if not len(koerper.dreiecke):
            return []
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
            if len(k.dreiecke):
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


def _farbgruppen_nativ(koerper, gelenke):
    from .core.native_backend import native_laden

    eltern, rotationen, translationen, zentren = [], [], [], []
    blaetter, punkte, gruppen = [], [], []

    def sammeln(knoten, elternindex, rotation, translation):
        if not knoten.teile and not len(knoten.dreiecke):
            return
        index = len(eltern)
        eltern.append(elternindex)
        rotationen.append(np.asarray(rotation, dtype=np.float64).reshape(9))
        translationen.append(np.asarray(translation, dtype=np.float64))
        zentren.append(
            np.asarray(knoten._r_eingabe, dtype=np.float64)
            if gelenke and not knoten.teile else np.zeros(3))
        for kind, (r, t) in knoten.teile:
            if gelenke:
                pose = pose_mit_gelenkwinkel(
                    kind.basis_pose, kind.gelenkdefinition, kind.gelenkwinkel_rad)
                r, t = pose.rotationsmatrix, pose.translation_m
            sammeln(kind, index, r, t)
        if knoten.teile:
            return
        blaetter.append(index)
        punkte.append(np.asarray(knoten.punkte, dtype=np.float64))
        daten = {
            "dreiecke": np.asarray(knoten.dreiecke, dtype=np.int64),
            "farbe_oben": knoten.farbe,
            "farbe_unten": knoten.unterwasser_farbe(),
            "glanz": knoten.glanz,
        }
        gruppen.append(
            {"knoten_id": knoten.knoten_id, **daten} if gelenke else daten)

    sammeln(koerper, -1, np.eye(3),
            -np.asarray(koerper._r_eingabe, dtype=np.float64) if gelenke else np.zeros(3))
    geometrien = native_laden().grafik_farbgeometrie(
        np.asarray(eltern, dtype=np.int64), np.asarray(rotationen, dtype=np.float64),
        np.asarray(translationen, dtype=np.float64), np.asarray(zentren, dtype=np.float64),
        np.asarray(blaetter, dtype=np.int64), punkte)
    for gruppe, geometrie in zip(gruppen, geometrien):
        gruppe["punkte"] = geometrie
    return gruppen


def _benetzte_geometrie(koerper):
    """Fasst nur verdrängende Blattmeshes im Schwerpunktframe zusammen."""
    snapshot = koerper.snapshot()
    meshes = snapshot.blatt_meshes
    if not meshes:
        return None
    if rechenpfad() == "cpp":
        from .core.native_backend import mesh_vorbereiten, native_laden
        return native_laden().grafik_meshes_vereinen([
            mesh_vorbereiten(p, f) for p, f in meshes])
    punkte = []
    dreiecke = []
    versatz = 0
    for mesh_punkte, mesh_dreiecke in meshes:
        mesh_punkte = np.asarray(mesh_punkte, dtype=np.float64)
        mesh_dreiecke = np.asarray(mesh_dreiecke, dtype=np.int64)
        punkte.append(mesh_punkte)
        dreiecke.append(mesh_dreiecke + versatz)
        versatz += len(mesh_punkte)
    return np.concatenate(punkte), np.concatenate(dreiecke)


def _hauptachsen_geometrie(punkte, eigenvektoren, rotation):
    if rechenpfad() == "cpp":
        from .core.native_backend import native_laden
        return native_laden().grafik_hauptachsen(
            np.asarray(punkte, dtype=float),
            np.asarray(eigenvektoren, dtype=float),
            np.asarray(rotation, dtype=float))
    richtungen = np.asarray(eigenvektoren, dtype=float) @ np.asarray(
        rotation, dtype=float).T
    rel = np.asarray(punkte, dtype=float)
    laengen = []
    for richtung in richtungen:
        proj = rel @ richtung if len(rel) else np.zeros(1)
        laengen.append(max(1.05 * float(np.abs(proj).max()), 0.05))
    return richtungen, np.asarray(laengen)


class GrafikBruecke:
    """Baut das Fenster mit dem ORIGINAL-Renderer; haelt MEHRERE Koerper."""

    _folge_aktiv = False
    _folge_letzt = None
    _wasserpunkte = None
    _wasserpunkte_meshes = {}
    _wasserpunkte_an = True
    _wasserpunkte_actor = None
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
        self._kraftsnapshots_ausstehend = set()
        self._stil = pfeilstil.Stil()
        self._vg_renderer = None
        self._vg_actors = {}
        self._vg_unmoeglich = False
        self._folge_aktiv = False
        self._folge_letzt = None
        self._navigationskamera = None
        self._navigationskamera_name = None
        self._navigationskamera_heading = None
        self._navigationskamera_busy = False
        self._navigationskamera_observer = None
        self._wasserpunkte = None
        self._wasserpunkte_meshes = {}
        self._wasserpunkte_actor = None
        self._wasserpunkte_an = True

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
        self._wasserpunkte_actor = None
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
        if not self._wasserpunkte_an:
            return
        punkte, spuren, alpha = self._wasserpunkte.aktualisieren(xy)
        n, s, _ = spuren.shape
        if n == 0:
            return

        def rgba(a):
            farbe = np.empty((a.size, 4), dtype=np.uint8)
            farbe[:, :3] = 255
            farbe[:, 3] = np.clip(a * 255.0, 0, 255).astype(np.uint8)
            return farbe

        alt = self._wasserpunkte_meshes.get("wasser_spuren")
        if (alt is not None and alt.n_points == n * s
                and alt.n_lines == n * (s - 1)):
            alt.points = spuren.reshape(-1, 3)
            alt["rgba"] = rgba(alpha.ravel())
            return
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
                self._wasserpunkte_actor = self._plotter.add_mesh(
                    mesh, scalars="rgba", rgba=True,
                    name=name, lighting=False,
                    reset_camera=False, pickable=False, **kw)
                self._wasserpunkte_meshes[name] = mesh
            else:
                alt.copy_from(mesh)

    def wasserpunkte_sichtbar_setzen(self, sichtbar):
        """Bewegungspunkte und Spuren nur in der Echtzeit; statisch bleibt
        nur die Wasserflaeche."""
        self._wasserpunkte_an = bool(sichtbar)
        actor = self._wasserpunkte_actor
        if actor is not None:
            actor.SetVisibility(self._wasserpunkte_an)
        if self._plotter is not None:
            self.render()
        return True

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
        self.koerper_entfernen(name)
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
        self._koerper[name]["benetzte_geometrie"] = _benetzte_geometrie(koerper)
        self._einhaengen(name)

    def gelenkwinkel_setzen(self, name, knoten_id, winkel_rad):
        """Grafisches Gelenk; physische Ruderwinkel setzt das Kraftmodell separat."""
        koerperanzeige = self._koerper.get(name)
        if koerperanzeige is None:
            return False
        koerper = koerperanzeige.get("koerper")
        if koerper is None:
            return False
        koerper.gelenkwinkel_setzen(knoten_id, winkel_rad)
        neue_gruppen = _farbgruppen(koerper)
        alte_gruppen = koerperanzeige.get("gruppen", [])
        if len(neue_gruppen) != len(alte_gruppen):
            raise RuntimeError(
                "Gelenkänderung hat die Blattanzahl des Renderers geändert")
        for alt, neu in zip(alte_gruppen, neue_gruppen):
            if alt.get("knoten_id") != neu.get("knoten_id"):
                raise RuntimeError(
                    "Gelenkänderung hat die Blattreihenfolge des Renderers geändert")
            if not np.array_equal(alt["dreiecke"], neu["dreiecke"]):
                raise RuntimeError(
                    "Gelenkänderung hat die Blatt-Topologie des Renderers geändert")
            alt["punkte"] = neu["punkte"]
            alt["pd"]["referenz_punkte"] = np.array(
                neu["punkte"], dtype=np.float64, copy=True)
        koerperanzeige["benetzte_geometrie"] = _benetzte_geometrie(koerper)
        self._statisch_anwenden(name, koerperanzeige)
        return True

    def koerper_entfernen(self, name):
        """Entfernt Modell, Overlays und Anzeige-Caches eines Laufzeitkoerpers."""
        alt = self._koerper.get(name)
        if alt is None:
            return
        namen = self._actor_namen(name) + self._overlay_namen(name)
        for actor_name in namen:
            self._actor_weg(actor_name)
        self.kraefte_daten_entfernen(name)
        self._koerper.pop(name)

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
            for n in self._actor_namen(name) + self._overlay_namen(name):
                try:
                    self._actor_weg(n)
                except Exception:
                    pass
            self._kraefte_entfernen(name)
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
        self._navigationskamera_busy = True
        try:
            self._plotter.camera_position = presets[preset]
            if self._folge_aktiv and self._folge_letzt is not None:
                delta = np.array(
                    [self._folge_letzt[0], self._folge_letzt[1], 0.0])
                kamera = self._plotter.camera
                kamera.position = tuple(
                    np.asarray(kamera.position) + delta)
                kamera.focal_point = tuple(
                    np.asarray(kamera.focal_point) + delta)
        finally:
            self._navigationskamera_busy = False
        self._navigationskamera = None
        self._navigationskamera_name = None
        self._navigationskamera_heading = None
        self.render()
        return True

    def _navigationskamera_geaendert(self, _kamera, _ereignis):
        if (self._navigationskamera_busy
                or self._navigationskamera is None
                or self._navigationskamera_heading is None):
            return
        kamera = self._plotter.camera
        position = np.asarray(kamera.position, dtype=np.float64)
        ziel = np.asarray(kamera.focal_point, dtype=np.float64)
        if rechenpfad() == "cpp":
            from .core.native_backend import native_laden
            lage = native_laden().kameralage(
                position, ziel, self._navigationskamera_heading)
            if lage is not None:
                self._navigationskamera = lage
            return
        richtung = position - ziel
        distanz = float(np.linalg.norm(richtung))
        horizontal = float(np.linalg.norm(richtung[:2]))
        if (not np.isfinite(richtung).all() or not math.isfinite(distanz)
                or distanz <= 1e-10):
            return
        elevation = math.atan2(float(richtung[2]), horizontal)
        if horizontal <= 1e-10:
            offset = None
        else:
            azimut = math.atan2(-float(richtung[1]),
                                float(richtung[0]))
            from .core.navigationsanzeigen import wrap_180
            offset = wrap_180(azimut - self._navigationskamera_heading)
        self._navigationskamera = (offset, elevation, distanz)

    def navigationskamera_aktualisieren(self, name, ziel, heading_rad):
        """Koppelt den Kamera-Standpunkt gierfest, ohne Stampfen/Krängung."""
        if self._plotter is None:
            return None, None
        ziel = np.asarray(ziel, dtype=np.float64)
        heading = None if heading_rad is None else float(heading_rad)
        if (ziel.shape != (3,) or not np.isfinite(ziel).all()
                or (heading is not None and not math.isfinite(heading))):
            raise ValueError("Navigationskamera benötigt endliche Posewerte")
        kamera = self._plotter.camera
        if self._navigationskamera_observer is None:
            self._navigationskamera_observer = kamera.AddObserver(
                "ModifiedEvent", self._navigationskamera_geaendert)
        if rechenpfad() == "cpp":
            from .core.native_backend import native_laden
            alt = (self._navigationskamera
                   if self._navigationskamera_name == name else None)
            neu = native_laden().kamera_aktualisieren(
                np.asarray(kamera.position, dtype=np.float64),
                np.asarray(kamera.focal_point, dtype=np.float64),
                np.asarray(kamera.up, dtype=np.float64), ziel, heading,
                self._navigationskamera_heading, alt)
            if neu is None:
                return None, None
            lage, letzter_heading, position, oben, geaendert = neu
            self._navigationskamera = lage
            self._navigationskamera_name = name
            self._navigationskamera_heading = letzter_heading
            if geaendert:
                self._navigationskamera_busy = True
                try:
                    kamera.position = tuple(position)
                    kamera.focal_point = tuple(ziel)
                    kamera.up = tuple(oben)
                finally:
                    self._navigationskamera_busy = False
            return lage[:2]

        if (self._navigationskamera is None
                or self._navigationskamera_name != name):
            position = np.asarray(kamera.position, dtype=np.float64)
            fokus = np.asarray(kamera.focal_point, dtype=np.float64)
            richtung = position - fokus
            distanz = float(np.linalg.norm(richtung))
            horizontal = float(np.linalg.norm(richtung[:2]))
            if (not np.isfinite(richtung).all()
                    or not math.isfinite(distanz) or distanz <= 1e-10):
                return None, None
            elevation = math.atan2(float(richtung[2]), horizontal)
            if horizontal <= 1e-10:
                offset = None
            elif heading is None:
                offset = None
            else:
                azimut = math.atan2(-float(richtung[1]),
                                    float(richtung[0]))
                from .core.navigationsanzeigen import wrap_180
                offset = wrap_180(azimut - heading)
            self._navigationskamera = (offset, elevation, distanz)
            self._navigationskamera_name = name

        offset, elevation, distanz = self._navigationskamera
        if heading is not None:
            self._navigationskamera_heading = heading
            if offset is None:
                position = np.asarray(kamera.position, dtype=np.float64)
                fokus = np.asarray(kamera.focal_point, dtype=np.float64)
                richtung = position - fokus
                horizontal = float(np.linalg.norm(richtung[:2]))
                if horizontal > 1e-10:
                    azimut = math.atan2(-float(richtung[1]),
                                        float(richtung[0]))
                    from .core.navigationsanzeigen import wrap_180
                    offset = wrap_180(azimut - heading)
                    self._navigationskamera = (
                        offset, elevation, distanz)

        if offset is None:
            versatz = (np.asarray(kamera.position, dtype=np.float64)
                       - np.asarray(kamera.focal_point, dtype=np.float64))
        else:
            azimut = (heading if heading is not None
                      else self._navigationskamera_heading) + offset
            versatz = distanz * np.array((
                math.cos(elevation) * math.cos(azimut),
                -math.cos(elevation) * math.sin(azimut),
                math.sin(elevation),
            ))
        blickrichtung = -versatz / max(float(np.linalg.norm(versatz)), 1e-10)
        hoch = np.array((0.0, 0.0, 1.0))
        oben = hoch - float(np.dot(hoch, blickrichtung)) * blickrichtung
        oben_betrag = float(np.linalg.norm(oben))
        if oben_betrag > 1e-10:
            oben /= oben_betrag
        else:
            oben = np.asarray(kamera.up, dtype=np.float64)

        neue_position = ziel + versatz
        neue_oben = np.asarray(oben, dtype=np.float64)
        if (np.allclose(kamera.position, neue_position, rtol=0.0, atol=1e-9)
                and np.allclose(
                    kamera.focal_point, ziel, rtol=0.0, atol=1e-9)
                and np.allclose(
                    kamera.up, neue_oben, rtol=0.0, atol=1e-9)):
            return offset, elevation
        self._navigationskamera_busy = True
        try:
            kamera.position = tuple(neue_position)
            kamera.focal_point = tuple(ziel)
            kamera.up = tuple(neue_oben)
        finally:
            self._navigationskamera_busy = False
        return offset, elevation

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
        if self._plotter is None or getattr(self._plotter, "_closed", False):
            return False
        if hasattr(self, "_kraefte_zeichner"):
            self._kraftkamera_beobachten()
            kamera = self._kraefte_zeichner.kamera()
            if kamera != getattr(self, "_kraftkamera", None):
                self._kraftkamera = kamera
                self._kraftsnapshots_ausstehend.update(self._kraefte_daten)
        for name in tuple(getattr(self, "_kraftsnapshots_ausstehend", ())):
            self._kraefte_actors(name)
        self._vordergrund_kamera_abgleichen()
        # QtInteractor.paintGL rendert selbst. Ein synchroner Render davor
        # zeichnet dieselbe Szene doppelt; update koalesziert nur GUI-Anfragen.
        from PySide6.QtOpenGLWidgets import QOpenGLWidget
        if isinstance(self._plotter, QOpenGLWidget):
            if not getattr(self, "_render_swap_verbunden", False):
                self._plotter.frameSwapped.connect(self._render_swap_fertig)
                self._render_swap_verbunden = True
            self._render_ausstehend = True
            QOpenGLWidget.update(self._plotter)
        else:
            self._plotter.render()
        return True

    def _render_swap_fertig(self):
        self._render_ausstehend = False

    def kantenglaettung_setzen(self, samples):
        if self._plotter is None:
            return False
        self._plotter.render_window.SetMultiSamples(int(samples))
        self.render()
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
        self._kraftsnapshots_ausstehend.update(self._kraefte_daten)
        for name, k in self._koerper.items():
            if k.get("aktiv"):
                self._overlays_aktualisieren(
                    name, k, k.get("statisch_R", np.eye(3)))

    def layer_ist_an(self, layer):
        return self._layer.ist_an(layer)

    # ---------------- Phase C: Kraeftebild (Taste 7) ----------------

    def kraefte_daten_setzen(self, name, erg, masse, g, skala=None, fremd=None):
        """Gemeinsamer Snapshotpfad; skala bleibt nur als ignoriertes Altargument."""
        from dataclasses import replace
        from .core.kraftmodell import KraftErgebnis, Kraftmodell
        from .core.frames import Pose
        from .core.dynamik_6dof import quaternion_aus_matrix
        from .core.kraefte_anzeige import KraefteAnzeigeAdapter
        k = self._koerper[name]
        pose = Pose(
            "simulationsframe", "koerper", tuple(k["position"]),
            quaternion_aus_matrix(k.get("statisch_R", np.eye(3))))
        if not isinstance(erg, KraftErgebnis):
            modell = Kraftmodell(lambda *_args, **_kwargs: erg, masse=masse, g=g)
            modell.fremdkraft_setzen(fremd)
            erg = modell.mit_hydrostatik(
                erg, lage=(pose.translation_m, pose.rotation_quaternion_wxyz))
        elif erg.kraftpose is None:
            erg = replace(erg, kraftpose=pose)
        vorher = self._kraefte_daten.get(name)
        snapshot = KraefteAnzeigeAdapter().aus_ergebnis(
            erg, koerper_id=name,
            generation=0 if vorher is None else vorher.generation,
            sequenz=0 if vorher is None else vorher.sequenz + 1,
            zeit_s=0.0, masse_kg=masse, g_m_s2=g)
        self.kraefte_snapshot_setzen(snapshot)

    def kraefte_snapshot_setzen(self, snapshot):
        from .core.kraefte_anzeige import KraefteAnzeigeSnapshot
        if not isinstance(snapshot, KraefteAnzeigeSnapshot):
            raise TypeError("Grafik braucht einen KraefteAnzeigeSnapshot")
        name = snapshot.koerper_id
        if name not in self._koerper:
            raise ValueError("Anzeigekoerper fehlt: " + name)
        vorher = self._kraefte_daten.get(name)
        if vorher is not None and (snapshot.generation, snapshot.sequenz) < (
                vorher.generation, vorher.sequenz):
            return False
        self._kraefte_daten[name] = snapshot
        self._kraftzeichner().generation_setzen(snapshot)
        self._kraftsnapshots_ausstehend.add(name)
        return True

    def kraefte_snapshot_ermitteln(self, name):
        return self._kraefte_daten.get(name)

    def _kraftzeichner(self):
        if not hasattr(self, "_kraefte_zeichner"):
            from .grafik_kraefte import KraefteZeichner
            self._kraefte_zeichner = KraefteZeichner(self)
            self._kraftkamera_beobachten()
        return self._kraefte_zeichner

    def _kraftkamera_beobachten(self):
        from PySide6.QtWidgets import QWidget
        if isinstance(self._plotter, QWidget):
            kamera = self._plotter.renderer.GetActiveCamera()
            alt = getattr(self, "_kraftkamera_beobachter", None)
            if alt is None or alt[0] is not kamera:
                if alt is not None:
                    alt[0].RemoveObserver(alt[1])
                self._kraftkamera_beobachter = (
                    kamera, kamera.AddObserver(
                        "ModifiedEvent", self._kraftkamera_geaendert))

    def kraefte_anzeige_beenden(self):
        beobachter = getattr(self, "_kraftkamera_beobachter", None)
        if beobachter is not None:
            beobachter[0].RemoveObserver(beobachter[1])
            self._kraftkamera_beobachter = None
        for name in tuple(self._kraefte_daten):
            self.kraefte_daten_entfernen(name)
        if hasattr(self, "_kraefte_zeichner"):
            del self._kraefte_zeichner
        self._kraftpfeil_vorlage = None

    def _kraftkamera_geaendert(self, *_):
        from PySide6.QtCore import QTimer
        if not getattr(self, "_kraftkamera_update_ausstehend", False):
            self._kraftkamera_update_ausstehend = True
            QTimer.singleShot(0, self._kraftkamera_aktualisieren)

    def _kraftkamera_aktualisieren(self):
        self._kraftkamera_update_ausstehend = False
        if hasattr(self, "_kraefte_zeichner"):
            self.render()

    def kraefte_auswahl_setzen(self, instanz_id):
        self._kraftzeichner().auswahl = instanz_id
        self.kraefte_neu_zeichnen()

    def kraefte_sichtbarkeit_setzen(self, instanz_id, sichtbar):
        self._kraftzeichner().sichtbar[instanz_id] = bool(sichtbar)
        self.kraefte_neu_zeichnen()

    def kraefte_koerperumfang_setzen(self, koerper_ids):
        zeichner = self._kraftzeichner()
        umfang = frozenset(koerper_ids)
        if umfang != zeichner.koerperumfang:
            zeichner.koerperumfang = umfang
            self.kraefte_neu_zeichnen()

    def kraefte_neu_einpassen(self):
        for snapshot in self._kraefte_daten.values():
            self._kraftzeichner().neu_einpassen(snapshot)
        self.kraefte_neu_zeichnen()

    def kraefte_neu_zeichnen(self):
        """Zeichnet Kraefte, Momente und Schwerpunkte aus den gespeicherten
        Daten neu (z. B. nach geaenderter Fremdkraft)."""
        self._kraftsnapshots_ausstehend.update(self._kraefte_daten)
        self._layer_aktualisieren()
        return self.render()

    def kraefte_daten_entfernen(self, name):
        self._kraefte_daten.pop(name, None)
        getattr(self, "_kraftsnapshots_ausstehend", set()).discard(name)
        if hasattr(self, "_kraefte_zeichner"):
            self._kraefte_zeichner.entfernen(name)
        self._kraefte_entfernen(name)

    def kraefte_daten_veralten(self, name):
        """Keine alten Kraefte zeigen; manuelle/initialisierte Skalen erhalten."""
        self._kraefte_daten.pop(name, None)
        getattr(self, "_kraftsnapshots_ausstehend", set()).discard(name)
        self._kraefte_entfernen(name)

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
        getattr(self, "_kugel_cache", {}).pop(name, None)
        getattr(self, "_overlay_mesh_cache", {}).pop(name, None)
        getattr(self, "_achsen_mesh_cache", {}).pop(name, None)
        actor = self._vg_actors.pop(name, None)
        if actor is not None:
            if self._vg_renderer is not None:
                self._vg_renderer.RemoveActor(actor)
            return
        if self._plotter is not None and not getattr(self._plotter, "_closed", False):
            self._plotter.remove_actor(name, reset_camera=False, render=False)

    def _actor_neu(self, name, mesh, **kwargs):
        """Neuer Vordergrundactor; kein stiller Wechsel zum raeumlichen Modus."""
        if self._vg_unmoeglich:
            raise RuntimeError(
                "Vordergrundebene nicht verfuegbar; raeumliche Darstellung waehlen")
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
        except (AttributeError, RuntimeError, TypeError, ValueError) as fehler:
            self._vg_unmoeglich = True
            raise RuntimeError(
                "Vordergrundebene konnte nicht angelegt werden") from fehler

    def _mesh_setzen(self, store, name, mesh, vordergrund=False, *,
                     kontur=None, **kwargs):
        """Wie _mesh_actor_setzen, optional in der Vordergrundebene."""
        actor = store.get(name)
        if actor is not None and mesh is not None:
            if (name in self._vg_actors) != (
                    vordergrund and not self._vg_unmoeglich):
                self._actor_weg(name)
                store.pop(name, None)
                actor = None
        if actor is None and mesh is not None and vordergrund:
            store[name] = self._actor_neu(name, mesh, **kwargs)
        else:
            _mesh_actor_setzen(self._plotter, store, name, mesh, **kwargs)
        konturname = name + "_kontur"
        if kontur and mesh is not None:
            from vtkmodules.vtkFiltersHybrid import vtkPolyDataSilhouette
            import pyvista as pv
            kamera = self._plotter.renderer.GetActiveCamera()
            silhouette = vtkPolyDataSilhouette()
            silhouette.SetInputData(mesh.clean())
            silhouette.SetCamera(kamera)
            if kamera.GetParallelProjection():
                silhouette.SetDirectionToCameraVector()
            else:
                silhouette.SetDirectionToCameraOrigin()
            silhouette.SetEnableFeatureAngle(False)
            silhouette.SetBorderEdges(False)
            silhouette.Update()
            ratio = (self._plotter.devicePixelRatioF()
                     if hasattr(self._plotter, "devicePixelRatioF") else 1.)
            self._mesh_setzen(
                store, konturname, pv.wrap(silhouette.GetOutput()), vordergrund,
                color=kontur, opacity=kwargs.get("opacity", 1),
                line_width=max(1., ratio), lighting=False)
            actor = store.get(konturname)
            if actor is not None and hasattr(actor, "GetProperty"):
                actor.GetProperty().SetLineWidth(max(1., ratio))
        elif konturname in store:
            self._actor_weg(konturname)
            store.pop(konturname)

    def _stil_pfeil(self, pfeil_id, k):
        return self._stil.pfeil(pfeil_id, self._ausdehnung(k))

    def _overlay_translation_aus_cache(self, store, name, signatur, anker):
        eintrag = getattr(self, "_overlay_mesh_cache", {}).get(name)
        actor = store.get(name)
        if (eintrag is None or eintrag[0] is not actor
                or eintrag[1] != signatur):
            return False
        actor.SetPosition(*(np.asarray(anker) - eintrag[2]))
        actor.SetVisibility(True)
        kontur = store.get(name + "_kontur")
        if kontur is not None:
            kontur.SetPosition(*actor.GetPosition())
            kontur.SetVisibility(True)
        return True

    def _overlay_translation_merke(self, store, name, signatur, anker):
        actor = store.get(name)
        if actor is None:
            return
        if not hasattr(self, "_overlay_mesh_cache"):
            self._overlay_mesh_cache = {}
        actor.SetPosition(0.0, 0.0, 0.0)
        kontur = store.get(name + "_kontur")
        if kontur is not None:
            kontur.SetPosition(0.0, 0.0, 0.0)
        self._overlay_mesh_cache[name] = (
            actor, signatur, np.asarray(anker, dtype=float).copy())

    def _overlay_signatur(self, st, *form):
        kamerasignatur = None
        if st.get("kontur"):
            kamera = self._plotter.renderer.GetActiveCamera()
            kamerasignatur = (kamera.GetPosition(), kamera.GetFocalPoint(),
                             kamera.GetParallelProjection())
        return (
            repr(sorted(st.items())),
            bool(getattr(self, "_vg_unmoeglich", False)),
            kamerasignatur,
            tuple(np.asarray(w, dtype=np.float64).tobytes() for w in form),
        )

    def _kraftpfeil_zeichnen(self, store, name, st, pfeil):
        import pyvista as pv
        signatur = self._overlay_signatur(
            st, pfeil["richtung"], pfeil["laenge"], pfeil["kopf_laenge"],
            pfeil["kopf_radius"], pfeil["schaft_radius"])
        if self._overlay_translation_aus_cache(
                store, name, signatur, pfeil["start"]):
            return
        kw = {"color": st["farbe"], "opacity": st["deckkraft"],
              "smooth_shading": True, "kontur": st.get("kontur")}
        if not st["gestrichelt"]:
            netz = self._kraftpfeil_netz(pfeil)
            self._mesh_setzen(store, name, netz, st["vordergrund"], **kw)
            self._overlay_translation_merke(store, name, signatur, pfeil["start"])
            return
        punkte, zellen = kb_strich(
            [pfeil["schaft_start"], pfeil["schaft_ende"]],
            st["strich"], st["luecke"])
        linie = pv.PolyData(punkte, lines=zellen)
        schaft = linie.tube(radius=pfeil["schaft_radius"], n_sides=8,
                            capping=True)
        kopf = pv.Cone(
            center=tuple(0.5 * (pfeil["schaft_ende"] + pfeil["spitze"])),
            direction=tuple(pfeil["richtung"]),
            height=pfeil["kopf_laenge"], radius=pfeil["kopf_radius"],
            resolution=16)
        self._mesh_setzen(store, name, schaft.append_polydata(kopf),
                          st["vordergrund"], **kw)
        self._overlay_translation_merke(
            store, name, signatur, pfeil["start"])

    def _kraftpfeil_netz(self, pfeil):
        import pyvista as pv
        vorlage = getattr(self, "_kraftpfeil_vorlage", None)
        if vorlage is None:
            schaft = pv.Line((0, 0, 0), (1, 0, 0)).tube(
                radius=1, n_sides=8, capping=True)
            kopf = pv.Cone(center=(.5, 0, 0), direction=(1, 0, 0),
                           height=1, radius=1, resolution=16)
            kopf = kopf.compute_normals(
                point_normals=True, cell_normals=False, split_vertices=True)
            netz = schaft.append_polydata(kopf)
            netz.point_data["Normals"] = np.vstack(
                (schaft.point_normals, kopf.point_normals))
            netz.GetPointData().SetActiveNormals("Normals")
            vorlage = self._kraftpfeil_vorlage = (
                netz, np.asarray(netz.points, dtype=float).copy(),
                np.asarray(netz.point_data["Normals"], dtype=float).copy(),
                schaft.n_points)
        netz, punkte, normalen, grenze = vorlage
        punkte, normalen = punkte.copy(), normalen.copy()
        schaftlaenge = pfeil["laenge"] - pfeil["kopf_laenge"]
        for bereich, laenge, radius, versatz in (
                (slice(None, grenze), schaftlaenge, pfeil["schaft_radius"], 0),
                (slice(grenze, None), pfeil["kopf_laenge"],
                 pfeil["kopf_radius"], schaftlaenge)):
            punkte[bereich] *= (laenge, radius, radius)
            punkte[bereich, 0] += versatz
            # Inverse transponierte Skalierung, ohne Division durch kleine Masse.
            normalen[bereich] *= (radius, laenge, laenge)
        norm = np.linalg.norm(normalen, axis=1, keepdims=True)
        np.divide(normalen, norm, out=normalen, where=norm > 0)
        richtung = np.asarray(pfeil["richtung"])
        referenz = (0, 0, 1) if abs(richtung[2]) < .9 else (0, 1, 0)
        quer = np.cross(referenz, richtung)
        quer /= np.linalg.norm(quer)
        basis = np.column_stack((richtung, quer, np.cross(richtung, quer)))
        ergebnis = netz.copy(deep=True)
        ergebnis.points = punkte @ basis.T + pfeil["start"]
        ergebnis.point_data["Normals"] = normalen @ basis.T
        return ergebnis

    def _momentbogen_zeichnen(self, store, name, st, moment, mitte, radius,
                              achse=None, *, bogen=None):
        """Zeichnet den Bogen; False, wenn das Moment verschwindet."""
        import pyvista as pv
        from .core import kraefte_bild as kb
        signatur = self._overlay_signatur(
            st, moment, radius, achse if bogen is None else bogen.richtung)
        if self._overlay_translation_aus_cache(
                store, name, signatur, mitte):
            return True
        bogen = (kb.moment_bogen_achse(moment, mitte, radius, achse)
                 if bogen is None else {
                     "punkte": np.asarray(bogen.punkte),
                     "richtung": np.asarray(bogen.richtung)})
        if bogen is None:
            return False
        kopf_l = min(st["kopf_laenge"], 0.5 * radius)
        kopf_r = 0.5 * st["kopf_durchmesser"] * kopf_l / max(
            st["kopf_laenge"], 1e-12)
        punkte = bogen["punkte"]
        spitze = punkte[-1] + kopf_l * bogen["richtung"]
        kw = {"color": st["farbe"], "opacity": st["deckkraft"],
              "smooth_shading": True, "kontur": st.get("kontur")}
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
        self._mesh_setzen(store, name, kurve.append_polydata(kopf),
                          st["vordergrund"], **kw)
        self._overlay_translation_merke(store, name, signatur, mitte)
        return True

    def _kugel_zeichnen(self, store, name, mitte, radius, farbe, kontur,
                        kontur_breite, vordergrund):
        """Schwerpunktkugel; die Kontur ist eine groessere Hohlkugel
        (Vorderseiten ausgeblendet), die nur den Rand zeigt."""
        self._kugel_mesh_setzen(
            store, name, mitte, radius, farbe, vordergrund)
        n_kontur = name + "_kontur"
        if not kontur:
            self._actor_weg(n_kontur)
            store.pop(n_kontur, None)
            return
        self._kugel_mesh_setzen(
            store, n_kontur, mitte, radius * (1.0 + kontur_breite),
            kontur, vordergrund, lighting=False)
        actor = store.get(n_kontur)
        if actor is not None and hasattr(actor, "GetProperty"):
            actor.GetProperty().SetFrontfaceCulling(True)

    def _kugel_mesh_setzen(self, store, name, mitte, radius, farbe,
                           vordergrund, lighting=True):
        import pyvista as pv

        cache = getattr(self, "_kugel_cache", None)
        if cache is None:
            cache = self._kugel_cache = {}
        key = (
            float(radius), repr(farbe), bool(vordergrund), bool(lighting),
            bool(vordergrund and not getattr(self, "_vg_unmoeglich", False)),
        )
        eintrag = cache.get(name)
        actor = store.get(name)
        if (eintrag is not None and eintrag[0] is actor
                and eintrag[1] == key):
            # Nur die starre Translation ändert sich; Kugelnetz und Normale
            # bleiben unverändert. Keine Physik- oder Overlaydaten werden gehalten.
            actor.SetPosition(*(np.asarray(mitte) - eintrag[2]))
            actor.SetVisibility(True)
            return
        kugel = pv.Sphere(center=tuple(mitte), radius=radius,
                          theta_resolution=24, phi_resolution=24)
        self._mesh_setzen(
            store, name, kugel, vordergrund, color=farbe, lighting=lighting)
        actor = store.get(name)
        if actor is not None:
            actor.SetPosition(0.0, 0.0, 0.0)
            cache[name] = (actor, key, np.asarray(mitte, dtype=float).copy())

    def _kraefte_actors(self, name):
        getattr(self, "_kraftsnapshots_ausstehend", set()).discard(name)
        if not any(self._layer.ist_an(layer) for layer in (
                LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT,
                LAYER_HYDRO_RUMPF, LAYER_HYDRO_KIEL, LAYER_HYDRO_RUDER,
                LAYER_SCHWERPUNKT)):
            self._kraefte_entfernen(name)
            return
        snapshot = self._kraefte_daten.get(name)
        k = self._koerper.get(name)
        zeichner = self._kraftzeichner()
        if zeichner.koerperumfang is not None and name not in zeichner.koerperumfang:
            self._kraefte_entfernen(name)
            return
        if snapshot is not None and k is not None:
            self._kraftzeichner().zeichnen(snapshot, k)

    def _kraefte_entfernen(self, name):
        if hasattr(self, "_kraefte_zeichner"):
            self._kraefte_zeichner.zeichenzustaende.pop(name, None)
            self._kraefte_zeichner.labels_entfernen(name)
            self._kraefte_zeichner.picklinien = {
                q: v for q, v in self._kraefte_zeichner.picklinien.items()
                if q[0] != name}
        store = self._koerper.get(name, {}).get("kraefte_actors", {})
        for n in tuple(store):
            self._actor_weg(n)
            store.pop(n)

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
        gruppen = (k.get("gruppen") or []) if k.get("aktiv", True) else []
        if rechenpfad() == "cpp":
            from .core.native_backend import native_laden
            geometrien = native_laden().grafik_transformieren(
                np.asarray(R, dtype=np.float64), np.asarray(k["position"], dtype=np.float64),
                [np.asarray(p["referenz_punkte"], dtype=np.float64)
                 for p in [pd] + [g["pd"] for g in gruppen]])
            welt = geometrien[0]
        else:
            welt = pd["referenz_punkte"] @ R.T + k["position"]
        pd.points = welt
        if not k.get("aktiv", True):
            # Ausgeblendete Koerper (Objektwechsel) duerfen ihre Actors
            # nicht neu aufbauen, sonst ueberlagern sie den neuen Koerper.
            return
        if k.get("gruppen"):
            for i, g in enumerate(k["gruppen"]):
                g["pd"].points = (
                    geometrien[i + 1] if rechenpfad() == "cpp"
                    else g["pd"]["referenz_punkte"] @ R.T + k["position"])
            self._gruppen_actors(name, k)
        else:
            self._actors_aktualisieren(name, welt)
        self._overlays_aktualisieren(name, k, R)

    def kraefte_entfernen(self, name):
        """Oeffentlich: entfernt Actors + Daten (Objektwechsel)."""
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
            richtungen, laengen = _hauptachsen_geometrie(
                koerper.punkte, vektoren, R)
            self._overlay_hauptachsen_setzen(name, cm, richtungen, laengen)
        else:
            self._overlay_hauptachsen_entfernen(name)
        # Phase C: Kraeftebild nur, wenn Layer an UND Daten vorliegen.
        if ((self._layer.ist_an(LAYER_KRAEFTE)
             or self._layer.ist_an(LAYER_MOMENTE)
             or self._layer.ist_an(LAYER_FREMDKRAFT)
             or self._layer.ist_an(LAYER_SCHWERPUNKT)
             or self._layer.ist_an(LAYER_HYDRO_RUMPF)
             or self._layer.ist_an(LAYER_HYDRO_KIEL)
             or self._layer.ist_an(LAYER_HYDRO_RUDER))
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
        from vtkmodules.vtkCommonMath import vtkMatrix4x4
        namen = self._overlay_namen(name)
        k = self._koerper[name]
        store = k.setdefault("overlay_actors", {})
        ha = self._stil.hauptachsen(self._ausdehnung(k))
        rr = 0.5 * ha["durchmesser"]
        if not hasattr(self, "_achsen_mesh_cache"):
            self._achsen_mesh_cache = {}
        for i in range(3):
            l = laengen[i] if hasattr(laengen, "__len__") else laengen
            n = namen[i + 1]
            key = (rr, repr(ha["farben"][i]), ha["vordergrund"],
                   bool(getattr(self, "_vg_unmoeglich", False)))
            actor = store.get(n)
            eintrag = self._achsen_mesh_cache.get(n)
            if (eintrag is None or eintrag[0] is not actor
                    or eintrag[1] != key):
                try:
                    mesh = pv.Line((-1., 0., 0.), (1., 0., 0.)).tube(
                        radius=rr, n_sides=12)
                    kw = {"color": ha["farben"][i], "smooth_shading": True}
                except Exception:
                    mesh = pv.Line((-1., 0., 0.), (1., 0., 0.))
                    kw = {"color": ha["farben"][i], "line_width": 4}
                self._mesh_setzen(store, n, mesh, ha["vordergrund"], **kw)
                actor = store[n]
                self._achsen_mesh_cache[n] = (actor, key)
            x = np.asarray(richtungen[i], dtype=float)
            x = x / np.linalg.norm(x)
            hilfe = np.eye(3)[int(np.argmin(np.abs(x)))]
            y = np.cross(x, hilfe)
            y /= np.linalg.norm(y)
            z = np.cross(x, y)
            matrix = vtkMatrix4x4()
            for zeile in range(3):
                for spalte, vektor in enumerate((l * x, y, z, cm)):
                    matrix.SetElement(zeile, spalte, float(vektor[zeile]))
            actor.SetUserMatrix(matrix)
            actor.SetVisibility(True)

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
