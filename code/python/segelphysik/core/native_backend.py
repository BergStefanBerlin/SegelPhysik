"""Expliziter Zugang zum nativen Kandidaten, ohne Referenz-Fallback."""
from __future__ import annotations

import importlib
import operator

import numpy as np


ABI_VERSION = 1
DATENTYPEN = (
    "Zustand", "Mesh", "Modell", "Parameter", "Wrench", "Beitrag", "Ergebnis", "Abbruch",
    "Pose", "Koerperteil", "Verband", "VerbandKontext", "BlattKontext", "SnapshotKontext",
    "EbenenSchnitt",
    "HydroTeil", "HydroKontext",
    "HydrostatikKontext", "HydrostatikWerte",
    "PhysikKontext",
    "StatikKontext",
    "_VoxelKontext",
)
FUNKTIONEN = (
    "quaternion_normalisieren", "quaternion_matrix", "quaternion_aus_matrix",
    "quaternion_multiplizieren", "orientierung_schritt",
    "rotationsmatrix_achsenwinkel", "pose_mit_gelenkwinkel",
    "verband_aggregieren", "wasserschnitt", "wasserlinie", "clip_polygon",
    "konturketten", "ringflaeche", "ringmomente", "wasserlinien_ringe",
    "punkt_in_ring", "einzigartige_konturpunkte", "polygonzug", "deckel_setzen",
    "mesh_volumen", "ittc_reibungsbeiwert", "wrench_verschieben",
    "aggregiere_kraftbeitraege", "widerstand", "added_mass_kraft",
    "quaternion_slerp", "anzeige_interpolieren",
    "euler_rotation", "rotation_matrix",
    "mesh_flaeche", "massenschwerpunkt", "massentraegheit",
    "dynamik2d", "stoss_pose", "projektion", "beste_loesung",
    "winkel_360", "wrap_180", "richtungssektor", "navigationswerte",
    "wasser_hash", "punktlage", "wasserpunkte", "wasserspuren", "dunst_gitter",
    "mesh_selbstschnitt",
    "pfeil_daten", "pfeil_fest", "kraft_paarmoment", "kraft_skala",
    "kraft_pfeile", "zusatz_pfeile", "moment_bogen", "strich_linien",
    "wirkungslinie", "achse_kanonisieren", "hauptachsen_aufbereiten",
    "wasser_upsample", "wasser_glaetten", "wasser_flaeche",
    "wasser_kreis", "wasser_quadrat",
    "grafik_transformieren", "grafik_hauptachsen", "grafik_farbgeometrie",
    "grafik_meshes_vereinen", "grafik_dreieckszellen",
    "kameralage", "kamera_aktualisieren",
    "instrument_aufbereitung", "svg_rahmen", "geschwindigkeitseinheiten",
    "form_mesh", "form_ring", "form_schwerpunkt", "form_zentrieren", "form_liegend",
    "polygon_selbstschnitt", "polygon_triangulieren", "obj_transformieren",
    "form_huellflaechen", "form_huelldreiecke", "form_faecher",
    "wasser_spiegeln", "wasser_splat", "wasser_kalibrieren",
    "voxel_paare_bereit", "voxel_intervalle",
)
METHODEN = {
    "PhysikKontext": ("batch",),
    "StatikKontext": (
        "residuum", "loesen", "kontakt_start", "stationaere_kraft",
        "stationaere_stufe", "stationaere_dynamik"),
}


class NativeBackendFehler(RuntimeError):
    """Der angeforderte native Rechenpfad ist nicht verfuegbar."""


def native_laden():
    try:
        modul = importlib.import_module("_segelphysik_native")
    except (ImportError, OSError) as fehler:
        raise NativeBackendFehler(
            "C++-Backend konnte nicht geladen werden; Python-Referenz wurde "
            "nicht automatisch aktiviert: %s" % fehler) from fehler
    if getattr(modul, "ABI_VERSION", None) != ABI_VERSION:
        raise NativeBackendFehler(
            "C++-Backend hat eine inkompatible ABI; erwartet %d" % ABI_VERSION)
    fehlend = [name for name in DATENTYPEN + FUNKTIONEN if not hasattr(modul, name)]
    if fehlend:
        raise NativeBackendFehler(
            "C++-Backend unvollstaendig; fehlende Exporte: " + ", ".join(fehlend))
    fehlend = [
        klasse + "." + name for klasse, namen in METHODEN.items()
        for name in namen if not callable(getattr(getattr(modul, klasse), name, None))]
    if fehlend:
        raise NativeBackendFehler(
            "C++-Backend unvollstaendig; fehlende Methoden: " + ", ".join(fehlend))
    if getattr(modul, "RECHENPFAD", None) != "cpp/datenschicht":
        raise NativeBackendFehler("C++-Backend meldet keinen gueltigen Rechenpfad")
    return modul


def zustand_vorbereiten(zustand):
    from .dynamik_6dof import Zustand6DOF

    if not isinstance(zustand, Zustand6DOF):
        raise TypeError("Native Vorbereitung erwartet einen Zustand6DOF")
    werte = np.concatenate([
        np.asarray(zustand.position, dtype=np.float64),
        np.asarray(zustand.quaternion, dtype=np.float64),
        np.asarray(zustand.geschwindigkeit_koerper, dtype=np.float64),
        np.asarray(zustand.winkelgeschwindigkeit_koerper, dtype=np.float64),
    ])
    if any(np.asarray(w).shape != (n,) for w, n in (
            (zustand.position, 3), (zustand.quaternion, 4),
            (zustand.geschwindigkeit_koerper, 3),
            (zustand.winkelgeschwindigkeit_koerper, 3))):
        raise ValueError("Native Zustandskomponenten haben falsche Dimensionen")
    return native_laden().Zustand(werte)


def mesh_vorbereiten(punkte, dreiecke):
    return native_laden().Mesh(
        np.asarray(punkte, dtype=np.float64), np.asarray(dreiecke, dtype=np.int64))


def pose_aus_modellpose(pose, ziel_frame, quell_frame):
    translation = (0., 0., 0.) if pose is None else pose.translation_m
    quaternion = (1., 0., 0., 0.) if pose is None else pose.rotation_quaternion_wxyz
    return native_laden().Pose(
        ziel_frame, quell_frame, np.asarray(translation, dtype=np.float64),
        np.asarray(quaternion, dtype=np.float64))


def pose_mit_gelenkwinkel(pose, gelenk, winkel_rad=None):
    basis = pose_aus_modellpose(pose, "eltern", "knoten")
    if gelenk is None:
        return basis
    winkel = gelenk.winkel_rad if winkel_rad is None else winkel_rad
    return native_laden().pose_mit_gelenkwinkel(
        basis, np.asarray(gelenk.achse_eltern, dtype=np.float64), float(winkel))


def modell_vorbereiten(snapshot):
    from .koerper import KoerperSnapshot
    from .massen import validiere_traegheitstensor

    if not isinstance(snapshot, KoerperSnapshot):
        raise TypeError("Native Modellvorbereitung erwartet einen KoerperSnapshot")
    native = native_laden()
    meshes = [
        native.Mesh(p, f, "verdrangend_%d" % nummer, "", True,
                    snapshot.blatt_quell_ids[nummer])
        for nummer, (p, f) in enumerate(snapshot.blatt_meshes)]
    meshes.extend(
        native.Mesh(p, f, name, rolle, False,
                    snapshot.hydrodynamik_quell_ids[index]
                    if snapshot.hydrodynamik_quell_ids else "")
        for index, (rolle, name, p, f) in enumerate(snapshot.hydrodynamik_teile))
    return native.Modell(
        float(snapshot.masse), validiere_traegheitstensor(snapshot.traegheitstensor), meshes,
        snapshot.version, np.asarray(snapshot.r_S, dtype=np.float64))


def parameter_vorbereiten(physik, rho):
    linear = np.array(physik.linear_widerstand, dtype=np.float64, copy=True)
    if linear.shape != (6,):
        raise ValueError("Linearer Widerstand muss sechs Werte enthalten")
    linear[2] += physik.daempfung_tauchung
    linear[3] += physik.daempfung_kraengung
    return native_laden().Parameter(
        float(rho), float(physik.g_m_pro_s2), float(physik.dt_s),
        linear,
        np.asarray(physik.quadratischer_widerstand, dtype=np.float64),
        np.asarray(physik.added_mass_diagonal, dtype=np.float64),
        np.asarray(physik.fluidgeschwindigkeit, dtype=np.float64),
        np.asarray(physik.fluidwinkelgeschwindigkeit, dtype=np.float64))


def wrench_vorbereiten(wrench):
    return native_laden().Wrench(
        wrench.frame, np.asarray(wrench.bezugspunkt_m, dtype=np.float64),
        np.asarray(wrench.kraft_N, dtype=np.float64),
        np.asarray(wrench.moment_Nm, dtype=np.float64))


def hydrostatik_vorbereiten(
        unionmodell, minimum, maximum, volumen, schwerpunkt, r_s, rho, g):
    native = native_laden()
    schnitt = unionmodell._schnitt
    mesh = native.Mesh(
        np.empty((0, 3), dtype=np.float64) if schnitt is None else schnitt.punkte,
        np.empty((0, 3), dtype=np.int64) if schnitt is None else
        np.asarray(schnitt.dreiecke, dtype=np.int64))
    return native.HydrostatikKontext(
        mesh, np.asarray(minimum, dtype=np.float64),
        np.asarray(maximum, dtype=np.float64), float(volumen),
        np.asarray(schwerpunkt, dtype=np.float64), np.asarray(r_s, dtype=np.float64),
        float(rho), float(g))


def _hydrodynamik_vorbereiten(hydrodynamik, rho):
    native = native_laden()
    rollen = native.HydroKontext([]) if hydrodynamik is None else hydrodynamik._native_teile
    if rollen is None:
        hydrodynamik._native_vorbereiten()
        rollen = hydrodynamik._native_teile
    parameter = np.array([
        float(rho), 1.004e-6, .2, 1.17, .8, .01, 0.], dtype=np.float64)
    if hydrodynamik is not None:
        parameter = np.array([
            hydrodynamik.rho, hydrodynamik.nu, hydrodynamik.formfaktor_rumpf,
            hydrodynamik.cd_quer, hydrodynamik.wirkungsgrad,
            hydrodynamik.cd0_profil, hydrodynamik.ruderwinkel_rad], dtype=np.float64)
    return rollen, parameter, (
        None if hydrodynamik is None else hydrodynamik.cd_volumenkoerper)


def physikkontext_vorbereiten(koerper, rho, physik, hydrostatik, hydrodynamik):
    native = native_laden()
    if hydrostatik.native_kontext is None:
        raise NativeBackendFehler(
            "Native Batchvorbereitung braucht einen vorbereiteten exakten Hydrostatikkontext")
    rollen, parameter, cd = _hydrodynamik_vorbereiten(hydrodynamik, rho)
    return native.PhysikKontext(
        hydrostatik.native_kontext, rollen, parameter, cd,
        float(koerper.masse), np.asarray(koerper.traegheitstensor, dtype=np.float64),
        parameter_vorbereiten(physik, rho))


def statikkontext_vorbereiten(funktion):
    from .kraftmodell import Kraftmodell

    native = native_laden()
    modell = funktion if type(funktion) is Kraftmodell else None
    hydro = funktion if modell is None else modell.hydrostatik
    kontext = getattr(hydro, "native_kontext", None)
    if kontext is None:
        return None
    rollen, parameter, cd = _hydrodynamik_vorbereiten(
        None if modell is None else modell.hydrodynamik, 1000.)
    return native.StatikKontext(
        kontext, rollen,
        np.zeros(6) if modell is None else modell.linear_widerstand,
        np.zeros(6) if modell is None else modell.quadratischer_widerstand,
        np.zeros(3) if modell is None else modell.fluidgeschwindigkeit,
        np.zeros(3) if modell is None else modell.fluidwinkelgeschwindigkeit,
        parameter, cd,
        None if modell is None or modell.masse is None else modell.masse * modell.g,
        None if modell is None else modell.fremdkraft, modell is not None)


def statik_loesen(funktion, m, g, start, tol, max_iter, stoerleiter, *,
                 robust, stagnation=.05, neutral=1e-9):
    from .statisch import SolverFehler

    kontext = statikkontext_vorbereiten(funktion)
    if kontext is None:
        return None
    erfolgreich, daten, status, meldung = kontext.loesen(
        float(m), float(g), np.asarray(start, dtype=np.float64),
        float(tol), operator.index(max_iter), tuple(float(x) for x in stoerleiter),
        robust, float(stagnation), float(neutral), native_laden().Abbruch())
    if not erfolgreich:
        raise SolverFehler(meldung, status=status, diagnose=daten if robust else None)
    return daten


def wrench_nach_python(wrench):
    from .kraftmodell import Wrench

    return Wrench(
        wrench.frame, tuple(wrench.bezugspunkt),
        tuple(wrench.kraft), tuple(wrench.moment))


def beitrag_vorbereiten(beitrag):
    return native_laden().Beitrag(
        beitrag.name, wrench_vorbereiten(beitrag.wrench),
        beitrag.quell_id, beitrag.originalangriff_m)


def beitrag_nach_python(beitrag):
    from .kraftmodell import Kraftbeitrag

    return Kraftbeitrag(
        beitrag.name, wrench_nach_python(beitrag.wrench), beitrag.quell_id,
        None if beitrag.originalangriff is None else tuple(beitrag.originalangriff))


def ergebnis_vorbereiten(zustand, ergebnis):
    from .kraftmodell import KraftErgebnis

    if not isinstance(ergebnis, KraftErgebnis):
        raise TypeError("Native Ergebnisvorbereitung erwartet ein KraftErgebnis")
    native = native_laden()

    hydrostatik = ergebnis.hydrostatik
    auftrieb = native.Wrench(
        "simulationsframe", np.asarray(ergebnis.bezugspunkt_m, dtype=np.float64),
        hydrostatik.F_A.as_array(), hydrostatik.M.as_array())
    return native.Ergebnis(
        zustand_vorbereiten(zustand), float(hydrostatik.V_tauch),
        hydrostatik.K.as_array(), wrench_vorbereiten(ergebnis.gesamt_wrench),
        [beitrag_vorbereiten(b) for b in ergebnis.beitraege],
        auftrieb, np.asarray(ergebnis.added_mass_diagonal, dtype=np.float64),
        np.asarray(ergebnis.linear_widerstand, dtype=np.float64),
        np.asarray(ergebnis.quadratischer_widerstand, dtype=np.float64),
        np.asarray(ergebnis.fluidgeschwindigkeit, dtype=np.float64),
        np.asarray(ergebnis.fluidwinkelgeschwindigkeit, dtype=np.float64),
        ergebnis.schwerkraft_beruecksichtigt,
        None if ergebnis.kraftpose is None else native.Zustand(np.array((
            *ergebnis.kraftpose.translation_m,
            *ergebnis.kraftpose.rotation_quaternion_wxyz,
            *zustand.geschwindigkeit_koerper,
            *zustand.winkelgeschwindigkeit_koerper), dtype=np.float64)))


def ergebnis_nach_python(ergebnis):
    from .auftrieb import Auftriebsergebnis, Vektor
    from .dynamik_6dof import Zustand6DOF
    from .kraftmodell import Kraftbeitrag, KraftErgebnis, Wrench

    if not isinstance(ergebnis, native_laden().Ergebnis):
        raise TypeError("Ergebnisadapter erwartet ein natives Ergebnis")
    if ergebnis.gesamt.frame != "simulationsframe":
        raise ValueError("Ergebnisadapter erwartet den simulationsframe")
    werte = ergebnis.zustand.werte
    zustand = Zustand6DOF(
        tuple(werte[:3]), tuple(werte[3:7]), tuple(werte[7:10]), tuple(werte[10:13]))
    hydrostatik = Auftriebsergebnis(
        ergebnis.volumen, ergebnis.auftriebsschwerpunkt,
        ergebnis.auftrieb.kraft, ergebnis.auftrieb.moment)
    beitraege = tuple(beitrag_nach_python(b) for b in ergebnis.beitraege)
    from .frames import Pose
    kraftpose = None
    if ergebnis.kraftzustand is not None:
        kraftwerte = ergebnis.kraftzustand.werte
        kraftpose = Pose("simulationsframe", "koerper",
                         tuple(kraftwerte[:3]), tuple(kraftwerte[3:7]))
    return zustand, KraftErgebnis(
        hydrostatik, Vektor(ergebnis.gesamt.kraft), Vektor(ergebnis.gesamt.moment),
        tuple(ergebnis.added_mass), beitraege, tuple(ergebnis.gesamt.bezugspunkt),
        ergebnis.schwerkraft_beruecksichtigt, tuple(ergebnis.linear),
        tuple(ergebnis.quadratisch), tuple(ergebnis.fluid),
        tuple(ergebnis.fluidrotation), kraftpose)


class NativeKoerperKontext:
    """Explizit vorbereiteter Kandidat; veraltete Koerper werden abgewiesen."""

    def __init__(self, koerper):
        from .koerper import GelenkSnapshot, Koerper, KoerperSnapshot

        if not isinstance(koerper, Koerper):
            raise TypeError("Nativer Koerperkontext erwartet einen Koerper")
        native = native_laden()
        blaetter, gelenke = [], []
        self._wachen = []

        def sammeln(knoten, rotation, translation, rolle_default=None):
            mesh = None
            if knoten.gelenkdefinition is not None:
                gelenke.append(GelenkSnapshot(
                    knoten.knoten_id, knoten.gelenkdefinition.eltern_id,
                    knoten.gelenkdefinition.achse_eltern, knoten.gelenkwinkel_rad))
            if knoten.teile:
                for kind, (r, t) in knoten.teile:
                    sammeln(kind, rotation @ r, translation + rotation @ t,
                            getattr(knoten, "rolle_default", None) or rolle_default)
            else:
                rolle = knoten.rolle or rolle_default
                mesh = native.Mesh(
                    knoten.punkte, knoten.dreiecke,
                    str(knoten.name or knoten.knoten_id or knoten.rolle),
                    "" if rolle is None else rolle, knoten.verdrangend,
                    knoten.quell_id)
                blaetter.append(native.BlattKontext(mesh, rotation, translation))
            self._wachen.append((
                knoten, self._signatur(knoten, knoten is not koerper),
                mesh))

        sammeln(koerper, np.eye(3), np.zeros(3))
        self._quelle = koerper
        self._version = koerper._version
        self._gelenke = tuple(gelenke)
        self._basis_pose = koerper.basis_pose
        self._kontext = native.SnapshotKontext(
            koerper.masse, koerper.traegheitstensor, self._version, blaetter)
        modell = self._kontext.auswerten(native.Abbruch())
        blatt_meshes, hydrodynamik, hydro_ids, blatt_ids = [], [], [], []
        for mesh in modell.meshes:
            p, f = mesh.punkte, mesh.dreiecke
            if mesh.verdraengend:
                blatt_meshes.append((p, f))
                blatt_ids.append(mesh.quell_id)
            else:
                hydrodynamik.append((mesh.rolle, mesh.name, p, f))
                hydro_ids.append(mesh.quell_id)
        self._vorlage = KoerperSnapshot(
            modell.masse, modell.traegheit, tuple(blatt_meshes), (0., 0., 0.),
            koerper.zustand, self._version, self._basis_pose,
            self._gelenke, tuple(hydrodynamik), tuple(hydro_ids), tuple(blatt_ids))

    @staticmethod
    def _signatur(knoten, version_beruecksichtigen=True):
        gelenk = knoten.gelenkdefinition
        return (
            knoten._version if version_beruecksichtigen else None,
            knoten.masse, tuple(knoten.traegheitstensor.ravel()),
            knoten.rolle, knoten.rolle_default, knoten.name, knoten.knoten_id,
            knoten.verdrangend, knoten.gelenkwinkel_rad, knoten.basis_pose,
            None if gelenk is None else (
                gelenk.eltern_id, tuple(gelenk.achse_eltern), gelenk.winkel_rad),
            tuple((id(kind), tuple(np.asarray(r).ravel()), tuple(t))
                  for kind, (r, t) in knoten.teile))

    def gueltig_fuer(self, koerper):
        if koerper is not self._quelle:
            return False
        for knoten, signatur, mesh in self._wachen:
            if self._signatur(
                    knoten, knoten is not self._quelle) != signatur:
                return False
            if mesh is not None and not mesh.eingabe_identisch(
                    np.asarray(knoten.punkte, dtype=np.float64),
                    np.asarray(knoten.dreiecke, dtype=np.int64)):
                return False
        return True

    def snapshot(self, koerper):
        from .koerper import KoerperSnapshot

        if not self.gueltig_fuer(koerper):
            raise NativeBackendFehler(
                "Nativer Koerperkontext ist veraltet; explizite Neuaufbereitung erforderlich")
        v = self._vorlage
        snapshot = KoerperSnapshot(
            v.masse, v.traegheitstensor, v.blatt_meshes, v.r_S,
            koerper.zustand, koerper._version, self._basis_pose,
            self._gelenke, v.hydrodynamik_teile, v.hydrodynamik_quell_ids,
            v.blatt_quell_ids)
        if not self.gueltig_fuer(koerper):
            raise NativeBackendFehler(
                "Nativer Koerperkontext wurde während der Snapshot-Erzeugung verändert")
        return snapshot
