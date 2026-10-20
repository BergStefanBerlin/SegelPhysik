"""Misst die tatsaechlichen produktiven Adapter gegen die explizite Referenz."""
import argparse
from contextlib import nullcontext
import hashlib
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segelphysik import grafik_bruecke, wasser_schnitt
from segelphysik.core import (
    auftrieb, dynamik, dynamik_6dof, frames, hydrostatik, koerper_formen, kraefte_bild,
    massen, mesh, voxelmodell,
    navigationsanzeigen, overlays, stoerung, wasserpunkte,
)
from segelphysik.core.auftrieb import Vektor, baue_kraftfunktion, baue_kraftfunktion_6dof
from segelphysik.core.bewegung import rotation_matrix
from segelphysik.core.fabriken import baue_modellpaket
from segelphysik.core.hydrodynamik import HydrodynamikModell
from segelphysik.core.konfig_lader import lade_konfig, lade_physik
from segelphysik.core.kraftmodell import baue_kraftmodell
from segelphysik.core.koerper import KoerperSnapshot
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.native_backend import native_laden
from segelphysik.core.rechenpfad import python_referenz, rechenpfad
from segelphysik.core.statisch import loese
from segelphysik.core.statisch_robust import loese_robust
from segelphysik.core.stationaer_hydrodynamik import (
    _rotation, loese_stationaer, pruefe_stationaer_dynamisch,
)
from segelphysik.render import vista
from werkzeuge.benchmark_profil import umgebung
from werkzeuge.migration_baseline import buildinventar
from werkzeuge.migration_inventar import (
    PRODUKTIVE_MIGRATIONSDATEIEN, referenzmanifest, schreiben, texthash,
)
from werkzeuge.migration_vergleich import performancevergleich


def zeitreihe(funktion, anzahl):
    start = time.perf_counter()
    for _ in range(anzahl):
        funktion()
    return (time.perf_counter() - start) / anzahl


def messfall(name, anforderungen, funktion, anzahl, eingabe):
    vorher, nachher = [], []
    for referenz in (True, False):
        with python_referenz() if referenz else nullcontext():
            funktion()
    for wiederholung in range(7):
        for referenz in ((True, False) if wiederholung % 2 == 0 else (False, True)):
            with python_referenz() if referenz else nullcontext():
                (vorher if referenz else nachher).append(zeitreihe(funktion, anzahl))
    return {
        "funktion_oder_elternblock": name, "anforderungen": anforderungen,
        "eingabe": eingabe, "aufrufe_pro_wiederholung": anzahl,
        "vergleich": performancevergleich(vorher, nachher),
        "pfad": "produktiver oeffentlicher Pythonadapter -> C++",
        "kosten": "Adapter, Validierung, Konvertierung und Ausgaben enthalten",
        "paritaetsnachweis": "JUnit-Nachweis mit Hash in umgebung.json; "
                            "kein Ersatz fuer strenge Langzeitnumerik oder GUI-Liveabnahme",
        "uebernahmeschranke_performance": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-verzeichnis", type=Path, required=True)
    parser.add_argument("--paritaetsnachweis", type=Path, required=True)
    args = parser.parse_args()
    if rechenpfad() != "cpp":
        raise ValueError("Produktivvergleich verlangt SEGELPHYSIK_RECHENPFAD=cpp")
    native = native_laden()
    suiten = list(ET.parse(args.paritaetsnachweis).getroot().iter("testsuite"))
    if not suiten or any(int(s.attrib["failures"]) or int(s.attrib["errors"]) for s in suiten):
        raise ValueError("Ein erfolgreicher JUnit-Produktivnachweis ist erforderlich")
    if sum(int(s.attrib["tests"]) for s in suiten) < 1:
        raise ValueError("Leerer Produktivnachweis ist unzulaessig")
    args.output.mkdir(parents=True, exist_ok=False)
    quellen = [ROOT / p for p in PRODUKTIVE_MIGRATIONSDATEIEN]
    quellen += list((ROOT / "code" / "cpp" / "src").glob("*"))
    quellen += [ROOT / "code" / "python" / "segelphysik" / "core" / p
                for p in ("rechenpfad.py", "native_backend.py")]
    quellen.append(Path(__file__))
    schreiben(args.output / "umgebung.json", {
        "umgebung": umgebung(), "build": buildinventar(args.build_verzeichnis),
        "native_modul": native.__file__,
        "native_binary_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "paritaetsnachweis": str(args.paritaetsnachweis),
        "paritaetsnachweis_sha256": hashlib.sha256(
            args.paritaetsnachweis.read_bytes()).hexdigest(),
        "referenzmanifest": referenzmanifest(
            native_kandidaten=True, produktive_migration=True),
        "quellen_sha256": {str(p.relative_to(ROOT)): texthash(p) for p in quellen},
        "referenzwahl": "Threadlokaler expliziter python_referenz-Kontext; "
                       "andere Threads und Prozesse werden nicht umgeschaltet",
    })
    faelle = []
    iso_wasser = vista.IsoSurfaceWater(
        3., 2.5, 1.2, .2, cell=.45, kernel_r=.55)
    wasserpartikel = np.random.default_rng(27026).uniform(
        [-1.8, -1.5, -1.5], [1.8, 1.5, .5], size=(250, 3))
    kalibrierungsraster = np.random.default_rng(27027).uniform(
        0., 2., size=iso_wasser.grid.shape).astype(np.float32)
    faelle.extend((
        messfall(
            "IsoSurfaceWater._mirrored", ["A-V0.10-00027"],
            lambda: iso_wasser._mirrored(wasserpartikel), 100,
            {"partikel": len(wasserpartikel), "becken_und_bodenrand": "gespiegelt"}),
        messfall(
            "IsoSurfaceWater.splat ohne Marching Cubes", ["A-V0.10-00027"],
            lambda: iso_wasser.splat(wasserpartikel), 3,
            {"partikel": len(wasserpartikel), "grid": list(iso_wasser.grid.shape),
             "offsets_je_partikel": len(iso_wasser._off),
             "kosten": "Spiegelung, float32-Gewichte, bincount-Aggregation, "
                       "Randkopie; PyVista-Isoflaechenextraktion ausgeschlossen"}),
        messfall(
            "IsoSurfaceWater._calibrate", ["A-V0.10-00027"],
            lambda: (setattr(iso_wasser, "_norm_eff", None)
                     or iso_wasser._calibrate(kalibrierungsraster)), 20,
            {"grid": list(iso_wasser.grid.shape), "dtype": "float32"}),
    ))
    voxel_p, voxel_f = build_box(2., 2., 2.)
    voxel_raster = voxelmodell.KoerperfestesVoxelmodell(
        [(voxel_p, voxel_f)], .2)
    voxel_pose = rotation_matrix(.37)
    voxel_position = np.array((.12, -.08, -.31), dtype=np.float64)
    voxel_quaternion = np.array(
        [np.cos(.185), np.sin(.185), 0., 0.], dtype=np.float64)
    faelle.extend((
        messfall(
            "KoerperfestesVoxelmodell.auswerten",
            ["A-V0.10-00030"],
            lambda: voxel_raster.auswerten(-.31, .37), 100,
            {"voxelzentren": len(voxel_raster.zentren_lokal),
             "aufloesung_m": .2, "pose": {"z_m": -.31, "roll_rad": .37}}),
        messfall(
            "KoerperfestesVoxelmodell.auswerten_6dof",
            ["A-V0.10-00030"],
            lambda: voxel_raster.auswerten_6dof(
                voxel_position, voxel_quaternion), 100,
            {"voxelzentren": len(voxel_raster.zentren_lokal),
             "aufloesung_m": .2, "position_m": voxel_position.tolist(),
             "quaternion_wxyz": voxel_quaternion.tolist()}),
        messfall(
            "KoerperfestesVoxelmodell Vorbereitung und erste Pose",
            ["A-V0.10-00030"],
            lambda: voxelmodell.KoerperfestesVoxelmodell(
                [(voxel_p, voxel_f)], .2).auswerten_6dof(
                    voxel_position, voxel_quaternion), 5,
            {"meshpunkte": len(voxel_p), "meshdreiecke": len(voxel_f),
             "aufloesung_m": .2, "kosten": "Validierung, Rasteraufbau, "
                                             "native Datenkopie und erste Auswertung"}),
        messfall(
            "Voxel-Saeulenintervalle im Koerpermit-Pfad",
            ["A-V0.10-00030"],
            lambda: auftrieb._y_intervalle_saeule_v(
                voxel_p, voxel_f, .13, -.27), 100,
            {"meshpunkte": len(voxel_p), "meshdreiecke": len(voxel_f),
             "xz_m": [.13, -.27],
             "kosten": "Pythonadapter und Arrayschnittstelle enthalten"}),
        messfall(
            "Voxel gesamter Unterwasser-Rasterpfad",
            ["A-V0.10-00030"],
            lambda: auftrieb._voxel_koerper(
                [(voxel_p, voxel_f)], .2), 2,
            {"meshpunkte": len(voxel_p), "meshdreiecke": len(voxel_f),
             "aufloesung_m": .2,
             "kosten": "Wasserschnitt, Raster, Saeulenintervalle, Vereinigung "
                       "und Schwerpunkt; keine OpenCL-GPU"}),
    ))
    q = np.array([2., -.3, .2, .4])
    with python_referenz():
        rotation = dynamik_6dof.quaternion_matrix(q)
    for name, funktion, parameter in (
        ("build_cone", lambda: koerper_formen.build_cone(2., .5, 64),
         {"H": 2., "R": .5, "nseg": 64}),
        ("build_box", lambda: koerper_formen.build_box(2., 3., 4.),
         {"dx": 2., "dy": 3., "dz": 4.}),
        ("build_pyramid", lambda: koerper_formen.build_pyramid(2., 3.),
         {"a": 2., "H": 3.}),
        ("build_sphere", lambda: koerper_formen.build_sphere(.5, 64),
         {"R": .5, "nseg": 64}),
        ("build_cylinder stehend", lambda: koerper_formen.build_cylinder(.5, 2., 64),
         {"R": .5, "H": 2., "nseg": 64, "lage": "stehend"}),
        ("build_cylinder liegend", lambda: koerper_formen.build_cylinder(.5, 2., 64, "liegend"),
         {"R": .5, "H": 2., "nseg": 64, "lage": "liegend"}),
        ("build_plate", lambda: koerper_formen.build_plate(2., 1., .02),
         {"dx": 2., "dy": 1., "dicke": .02}),
        ("build_hexprism", lambda: koerper_formen.build_hexprism(.004, .17),
         {"umkreisradius": .004, "H": .17, "spitzenlaenge": 0., "lage": "stehend"}),
        ("build_hexprism Spitze liegend",
         lambda: koerper_formen.build_hexprism(.004, .17, .03, "liegend"),
         {"umkreisradius": .004, "H": .17, "spitzenlaenge": .03, "lage": "liegend"}),
    ):
        faelle.append(messfall(name, ["A-V0.10-00022"], funktion, 20,
                              {"parameter_si": parameter}))
    form_p, form_f = build_box(2., 3., 4.)
    for name, funktion in (
        ("Formring", lambda: koerper_formen._ring(.5, .3, 64)),
        ("Formvolumenschwerpunkt",
         lambda: koerper_formen._volumenschwerpunkt(form_p, form_f)),
        ("Formzentrierung", lambda: koerper_formen._zentriert(form_p, form_f)),
        ("Liegendtransformation", lambda: koerper_formen._liegend(form_p)),
    ):
        faelle.append(messfall(name, ["A-V0.10-00022"], funktion, 100,
                              {"quaderpunkte": 8, "dreiecke": 12,
                               "ringparameter": [.5, .3, 64]}))
    for n in (8, 24, 64):
        huellpunkte = np.random.default_rng(20260 + n).normal(size=(n, 3))
        faelle.append(messfall(
            "build_polyhedron Konvexhuelle", ["A-V0.10-00022"],
            lambda: koerper_formen.build_polyhedron(huellpunkte), 1,
            {"punkte": n, "sortierung": "unveraendertes natives NumPy argsort"}))
    polygone = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
                [2, 3, 7, 6], [1, 2, 6, 5], [3, 0, 4, 7]]
    faelle.append(messfall(
        "build_polyhedron explizite Polygonflaechen", ["A-V0.10-00022"],
        lambda: koerper_formen.build_polyhedron(form_p, polygone), 100,
        {"punkte": 8, "vierecke": 6}))
    winkel = np.linspace(0., 2. * np.pi, 32, endpoint=False)
    radien = np.where(np.arange(32) % 2, .7, 1.)
    polygon = np.column_stack((radien * np.cos(winkel), radien * np.sin(winkel)))
    polygon3 = np.column_stack((polygon, np.zeros(32)))
    for name, funktion in (
        ("Polygon-Selbstschnitt",
         lambda: mesh._polygon_selbstschneidet(polygon, 1e-10)),
        ("OBJ-Ohrtriangulierung",
         lambda: mesh._trianguliere_polygon(polygon3, list(range(32)), "messung.obj", 33)),
    ):
        faelle.append(messfall(name, ["A-V0.10-00022"], funktion, 20,
                              {"punkte": 32, "polygon": "einfach und konkav"}))
    with tempfile.TemporaryDirectory(prefix="segelphysik-obj-benchmark-") as verzeichnis:
        paket = Path(verzeichnis)
        zeilen = ["v %.17g %.17g %.17g" % tuple(p) for p in polygon3]
        zeilen.append("f " + " ".join(str(i + 1) for i in range(32)))
        (paket / "messung.obj").write_text("\n".join(zeilen) + "\n", encoding="utf-8")

        def obj_importieren():
            mesh._obj_mesh_cached.cache_clear()
            return mesh.mesh_aus_quelle(
                {"quelle": "obj", "datei": "messung.obj"}, paketwurzel=paket,
                obj_zu_m=.3, obj_achsenmatrix_zu_blatt=rotation)

        faelle.append(messfall(
            "OBJ-Import mit kaltem Anwendungscache", ["A-V0.10-00022"],
            obj_importieren, 20,
            {"punkte": 32, "skalierung": .3, "rotation": rotation.tolist(),
             "kosten": "Cacheleeren, Dateilesen/Parsen, Triangulierung, Transformation, "
                       "Validierung und unveraenderliches Mesh enthalten; "
                       "Betriebssystem-Dateicache nicht geleert"}))
    pose = frames.Pose("welt", "rumpf", (1., 2., 3.), tuple(q))
    innen = frames.Pose("rumpf", "kiel", (-1., 0., 0.), (1., 0., 0., 0.))
    for name, funktion in (
        ("quaternion_normalisieren", lambda: dynamik_6dof.quaternion_normalisieren(q)),
        ("quaternion_matrix", lambda: dynamik_6dof.quaternion_matrix(q)),
        ("quaternion_aus_matrix", lambda: dynamik_6dof.quaternion_aus_matrix(rotation)),
        ("quaternion_slerp", lambda: dynamik_6dof.quaternion_slerp(q, -q, .3)),
        ("_quaternion_multiplizieren", lambda: dynamik_6dof._quaternion_multiplizieren(q, q)),
        ("_orientierung_schritt", lambda: dynamik_6dof._orientierung_schritt(q, np.ones(3), .004)),
        ("Pose.__post_init__", lambda: frames.Pose("welt", "rumpf", (1., 2., 3.), tuple(q))),
        ("Pose.rotationsmatrix", lambda: pose.rotationsmatrix),
        ("Pose.punkt_transformieren", lambda: pose.punkt_transformieren(np.ones(3))),
        ("Pose.vektor_transformieren", lambda: pose.vektor_transformieren(np.ones(3))),
        ("Pose.invers", pose.invers),
        ("Pose.komponieren", lambda: pose.komponieren(innen)),
        ("rotationsmatrix_achsenwinkel", lambda: frames.rotationsmatrix_achsenwinkel(np.ones(3), .3)),
        ("pose_aus_modellpose", lambda: frames.pose_aus_modellpose(None, "welt", "rumpf")),
        ("pose_mit_gelenkwinkel", lambda: frames.pose_mit_gelenkwinkel(None, None)),
    ):
        faelle.append(messfall(
            name, ["A-V0.10-00006", "A-V0.10-00020"], funktion, 200,
            {"quaternion": q.tolist()}))
    for n in (1, 1000, 100000):
        p = np.random.default_rng(n).normal(size=(n, 3))
        faelle.append(messfall(
            "Pose.punkte_transformieren", ["A-V0.10-00020"],
            lambda: pose.punkte_transformieren(p), 20 if n < 100000 else 5,
            {"punkte": n}))
    verlauf = [
        (i * .004, dynamik_6dof.Zustand6DOF(
            (i * .001, 0., -.1), (1., 0., 0., 0.), (0., 0., 0.), (0., 0., 0.)))
        for i in range(101)]
    gitter = np.arange(-500, 500, dtype=np.int64)
    wasserfeld = wasserpunkte.WasserPunktFeld()
    with python_referenz():
        for _ in range(wasserfeld.historie):
            wasserfeld.aktualisieren((.1, .2))
    for name, funktion, aids, eingabe in (
        ("anzeige_interpolieren mit 101 Samples",
         lambda: dynamik_6dof.anzeige_interpolieren(verlauf, .1, .016, .1),
         ["A-V0.10-00024"], {"samples": 101, "anzeigezeit_s": .1, "dt_s": .016, "verzoegerung_s": .1}),
        ("rotation_matrix einschliesslich Defaultachse", lambda: rotation_matrix(.3),
         ["A-V0.10-00029"], {"phi_rad": .3, "achse": [0., 1., 0.]}),
        ("stationaere Eulerrotation", lambda: _rotation(.1, .2, .3),
         ["A-V0.10-00019"], {"winkel_rad": [.1, .2, .3]}),
        ("Stoerrotation", lambda: stoerung.rotationsmatrix((.1, .2, .3)),
         ["A-V0.10-00029"], {"winkel_rad": [.1, .2, .3]}),
        ("stoss_pose", lambda: stoerung.stoss_pose(
            (1., 2., 3.), {"winkel": (.1, .2, .3), "versatz": (.2, -.1, .5)}),
         ["A-V0.10-00029"], {"position": [1., 2., 3.], "winkel_rad": [.1, .2, .3],
                               "versatz_m": [.2, -.1, .5]}),
        ("projektion", lambda: stoerung.projektion(
            (1., 2., 3.), {"winkel": (.1, .2, .3)}),
         ["A-V0.10-00029"], {"position": [1., 2., 3.], "winkel_rad": [.1, .2, .3]}),
        ("beste_loesung", lambda: stoerung.beste_loesung([
            {"z": -.1, "gm": None, "neutral": True},
            {"z": .1, "gm": .2}, {"z": 0., "gm": .3}]),
         ["A-V0.10-00029"], {"loesungen": [
             {"z": -.1, "gm": None, "neutral": True}, {"z": .1, "gm": .2}, {"z": 0., "gm": .3}]}),
        ("navigationswerte_ableiten", lambda: navigationsanzeigen.navigationswerte_ableiten(
            (1., .1, .2, .3), .4, .5, .1), ["A-V0.10-00028"],
         {"quaternion_wxyz": [1., .1, .2, .3], "offset_rad": .4,
          "elevation_rad": .5, "segelwinkel_rad": .1}),
        ("winkel_360", lambda: navigationsanzeigen.winkel_360(-10.),
         ["A-V0.10-00028"], {"winkel_rad": -10.}),
        ("wrap_180", lambda: navigationsanzeigen.wrap_180(10.),
         ["A-V0.10-00028"], {"winkel_rad": 10.}),
        ("richtung_16", lambda: navigationsanzeigen.richtung_16(75.),
         ["A-V0.10-00028"], {"heading_grad": 75.}),
        ("_hash01: 1000 Gitterzellen", lambda: wasserpunkte._hash01(gitter, gitter, 1),
         ["A-V0.10-00027"], {"gx_gy_int64": [-500, 499], "zellen": 1000, "salz": 1}),
        ("punktlage: 1000 Gitterzellen", lambda: wasserpunkte.punktlage(gitter, gitter),
         ["A-V0.10-00027"], {"gx_gy_int64": [-500, 499], "zellen": 1000, "abstand_m": 1.5}),
        ("dunst_gitter: unveraenderte Standardaufloesung", wasserpunkte.dunst_gitter,
         ["A-V0.10-00027"], {"r_innen_m": 30., "r_aussen_m": 2000., "hoehe_m": 600.,
                               "ringe": 28, "hoehenstufen": 8, "segmente": 96,
                               "z_basis_m": -.05, "farbe_rgb": [200, 220, 238]}),
        ("WasserPunktFeld.punkte_welt", lambda: wasserfeld.punkte_welt((.1, .2)),
         ["A-V0.10-00027"], {"zentrum_m": [.1, .2], "radius_m": 12., "abstand_m": 1.5}),
        ("WasserPunktFeld.aktualisieren mit vollem Verlauf",
         lambda: wasserfeld.aktualisieren((.1, .2)), ["A-V0.10-00027"],
         {"zentrum_m": [.1, .2], "radius_m": 12., "abstand_m": 1.5, "historie": 12, "spur_punkte": 6}),
    ):
        faelle.append(messfall(name, aids, funktion, 200, eingabe))
    p_box, f_box = build_box(1., 1., 1.)
    zeichnung = SimpleNamespace(
        K=Vektor((.1, .2, -.3)), F_A=Vektor((0., 0., 900.)),
        F_gesamt=Vektor((30., -20., 1000.)))
    linie = np.column_stack((np.linspace(0., 10., 101),
                            np.zeros(101), np.zeros(101)))
    for name, funktion, eingabe in (
        ("pfeil_daten", lambda: kraefte_bild.pfeil_daten((1., 2., 3.), (4., 5., 6.)),
         {"start": [1., 2., 3.], "vektor": [4., 5., 6.]}),
        ("pfeil_fest", lambda: kraefte_bild.pfeil_fest(
            (1., 2., 3.), (4., 5., 6.), .1, .2, .3),
         {"start": [1., 2., 3.], "vektor": [4., 5., 6.],
          "durchmesser": .1, "kopf_durchmesser": .2, "kopf_laenge": .3}),
        ("paar_moment_auftrieb", lambda: kraefte_bild.paar_moment_auftrieb(
            zeichnung, (0., 0., 0.)), {"auftrieb_N": 900., "angriff": [.1, .2, -.3]}),
        ("paar_moment_kraft", lambda: kraefte_bild.paar_moment_kraft(
            (.1, .2, -.3), (30., -20., 1000.), (0., 0., 0.)),
         {"kraft_N": [30., -20., 1000.], "angriff": [.1, .2, -.3]}),
        ("skala_waehlen", lambda: kraefte_bild.skala_waehlen(100., 9.81, 2.),
         {"masse_kg": 100., "g_m_pro_s2": 9.81, "referenz_laenge_m": 2.}),
        ("kraft_pfeile", lambda: kraefte_bild.kraft_pfeile(
            zeichnung, (0., 0., 0.), 100., 9.81, .001),
         {"masse_kg": 100., "g_m_pro_s2": 9.81, "skala": .001}),
        ("zusatz_pfeile", lambda: kraefte_bild.zusatz_pfeile(
            zeichnung, (0., 0., 0.), 100., 9.81, .001),
         {"masse_kg": 100., "g_m_pro_s2": 9.81, "skala": .001}),
        ("moment_bogen", lambda: kraefte_bild.moment_bogen(
            10., (1., 2., 3.), .5), {"moment_Nm": 10., "radius_m": .5, "punkte": 49}),
        ("moment_bogen_achse", lambda: kraefte_bild.moment_bogen_achse(
            -10., (1., 2., 3.), .5, 2),
         {"moment_Nm": -10., "radius_m": .5, "achse": 2, "punkte": 49}),
        ("strich_linien", lambda: kraefte_bild.strich_linien(linie, .1, .05),
         {"stuetzpunkte": 101, "laenge_m": 10., "strich_m": .1, "luecke_m": .05}),
        ("wirkungslinie_auf_geometrie", lambda: kraefte_bild.wirkungslinie_auf_geometrie(
            (1., 0., 0.), (0., 0., .25), (0., 0., 0.), p_box, f_box),
         {"modell": "analytischer Einheitsquader", "dreiecke": len(f_box)}),
        ("hauptachsen: NumPy-Eigenloeser und native Sortierung/Kanonisierung",
         lambda: overlays.hauptachsen(np.array([[2., .1, .2], [.1, 3., .1], [.2, .1, 4.]])),
         {"traegheit_kg_m2": [[2., .1, .2], [.1, 3., .1], [.2, .1, 4.]]}),
        ("_kanonisiere", lambda: overlays._kanonisiere((-1., .3, .2)),
         {"vektor": [-1., .3, .2]}),
    ):
        faelle.append(messfall(name, ["A-V0.10-00026"], funktion, 50, eingabe))
    import pyvista as pv
    for name, funktion in (
        ("_polydaten", grafik_bruecke._polydaten),
        ("_dreiecks_polydaten", grafik_bruecke._dreiecks_polydaten),
    ):
        faelle.append(messfall(
            name + " einschliesslich PyVista-Datenobjekt", ["A-V0.10-00025"],
            lambda: funktion(pv, p_box, f_box), 100,
            {"modell": "analytischer Einheitsquader", "dreiecke": len(f_box)}))
    y_wasser, x_wasser = np.indices((40, 40), dtype=float)
    z_wasser = .02 * np.sin(x_wasser) * np.cos(y_wasser)
    defekt_wasser = z_wasser.copy()
    defekt_wasser[5:10, 10:15] = np.nan
    renderer = vista.PyVistaRenderer.__new__(vista.PyVistaRenderer)
    renderer.dx, renderer.smooth_passes = .1, 2
    for name, funktion, eingabe in (
        ("_surface_polydata einschliesslich PyVista-Datenobjekt",
         lambda: vista._surface_polydata(pv, x_wasser, y_wasser, z_wasser),
         {"raster": [40, 40], "dreiecke": 3042}),
        ("_bilinear_upsample", lambda: vista._bilinear_upsample(z_wasser, 3),
         {"raster": [40, 40], "faktor": 3}),
        ("_unit_circle", lambda: vista._unit_circle(48), {"punkte": 48}),
        ("_unit_square", vista._unit_square, {"punkte": 5}),
        ("PyVistaRenderer._smooth_surface: Loecher, Median, Laplace",
         lambda: renderer._smooth_surface(defekt_wasser),
         {"raster": [40, 40], "fehlende_hoehen": 25, "smooth_passes": 2, "dx_m": .1}),
    ):
        faelle.append(messfall(name, ["A-V0.10-00027"], funktion, 30, eingabe))
    kamera_bridge = grafik_bruecke.GrafikBruecke()
    kamera_bridge._plotter = SimpleNamespace(camera=pv.Camera())
    kamera_bridge._plotter.camera.position = (3., 4., 5.)
    kamera_bridge._plotter.camera.focal_point = (0., 0., 0.)
    kamera_bridge._plotter.camera.up = (0., 0., 1.)
    zaehler = [0]

    def kamera_folgen():
        zaehler[0] += 1
        return kamera_bridge.navigationskamera_aktualisieren(
            "kameratest", (1., 2., 3.), .3 if zaehler[0] % 2 else .4)

    faelle.append(messfall(
        "navigationskamera_aktualisieren einschliesslich VTK-Kamera und Observer",
        ["A-V0.10-00028"], kamera_folgen, 100,
        {"ziel": [1., 2., 3.], "wechselnde_headings_rad": [.3, .4],
         "rendering": "nicht enthalten"}))
    faelle.append(messfall(
        "_navigationskamera_geaendert: manuelle Kamerageometrie",
        ["A-V0.10-00028"],
        lambda: kamera_bridge._navigationskamera_geaendert(None, None), 100,
        {"ausgangsabstand": "vorbereiteter Kamera-Folgepfad", "rendering": "nicht enthalten"}))
    kamera_bridge._plotter.camera.RemoveObserver(kamera_bridge._navigationskamera_observer)

    from PySide6.QtWidgets import QApplication
    from segelphysik.gui import navigationswidgets
    app = QApplication.instance() or QApplication([])
    anzeigewerte = navigationsanzeigen.Navigationswerte(47., 20., -15., 87., 37., 23., .2)
    instrumente = navigationswidgets.NavigationsWidgetFenster()
    instrumente._werte = anzeigewerte
    instrumente._geschwindigkeit_m_pro_s = 3.5
    for widget in instrumente.widgets:
        faelle.append(messfall(
            "SVGInstrumentWidget.aktualisieren: " + widget.typ,
            ["A-V0.10-00028"], lambda: widget.aktualisieren(anzeigewerte, {}), 20,
            {"typ": widget.typ, "winkel_grad": [47., 20., -15.],
             "kosten": "einschliesslich XML- und Qt-SVG-Aufbereitung, ohne Paint-Event"}))
    faelle.append(messfall(
        "GeschwindigkeitsWidget.aktualisieren einschliesslich XML und Qt-SVG",
        ["A-V0.10-00028"], lambda: instrumente.geschwindigkeit_widget.aktualisieren(3.5), 20,
        {"geschwindigkeit_m_pro_s": 3.5, "paint_event": "nicht enthalten"}))
    faelle.append(messfall(
        "NavigationsWidgetFenster._instrumente_rendern: alle vier Anzeigen",
        ["A-V0.10-00028"], instrumente._instrumente_rendern, 10,
        {"instrumente": 4, "geschwindigkeit_m_pro_s": 3.5, "paint_event": "nicht enthalten"}))
    faelle.append(messfall(
        "SVG-Rahmen: gemeinsamer numerischer Paint-Event-Block",
        ["A-V0.10-00028"], lambda: navigationswidgets._svg_rahmen(501, 301, 624, 810), 100,
        {"widget_px": [501, 301], "svg_px": [624, 810]}))
    faelle.append(messfall(
        "Geschwindigkeitseinheiten: m/s, km/h, kn",
        ["A-V0.10-00028"], lambda: navigationswidgets._geschwindigkeitseinheiten(3.5), 100,
        {"geschwindigkeit_m_pro_s": 3.5}))
    instrumente.close()
    box = KoerperSnapshot(500., np.eye(3) * 100., ((p_box, f_box),), (0., 0., 0.), None, 0)
    physik_box = lade_physik(ROOT / "konfigurationen")

    def stationaeres_modell():
        hydro = baue_kraftfunktion(box, pfad="exakt_union", g=physik_box.g_m_pro_s2)
        modell = baue_kraftmodell(hydro, physik_box, masse=500., g=physik_box.g_m_pro_s2)
        modell.linear_widerstand = np.array([100., 0., 0., 0., 0., 0.])
        modell.quadratischer_widerstand = np.zeros(6)
        modell.fremdkraft_setzen(((50., 0., 0.), (0., 0., 0.)))
        return modell

    with python_referenz():
        stationaer_python = stationaeres_modell()
    stationaer_cpp = stationaeres_modell()
    with python_referenz():
        stationaere_stufe = loese_stationaer(
            stationaer_python, charakteristische_kraft_N=500.,
            charakteristische_laenge_m=1., referenzgeschwindigkeit_m_s=.5,
            start=(.2, -.05, .01, 0., 0., 0.)).stufen[-1]
    faelle.append(messfall(
        "loese_stationaer: beide Stufen einschliesslich Newton/Jacobi/Daempfung",
        ["A-V0.10-00019"],
        lambda: loese_stationaer(
            stationaer_python if rechenpfad() == "python" else stationaer_cpp,
            charakteristische_kraft_N=500., charakteristische_laenge_m=1.,
            referenzgeschwindigkeit_m_s=.5, start=(.2, -.05, .01, 0., 0., 0.)),
        3, {"modell": "analytischer Einheitsquader", "masse_kg": 500.}))
    faelle.append(messfall(
        "pruefe_stationaer_dynamisch: nativer 1-s-Nachlauf ohne Pythoncallbacks",
        ["A-V0.10-00019"],
        lambda: pruefe_stationaer_dynamisch(
            stationaer_python if rechenpfad() == "python" else stationaer_cpp,
            stationaere_stufe, masse_kg=500., traegheit_koerper=np.eye(3) * 100.,
            charakteristische_laenge_m=1., dt_s=.004,
            g_m_pro_s2=physik_box.g_m_pro_s2, dauer_s=1.),
        1, {"modell": "analytischer Einheitsquader", "masse_kg": 500.,
            "dauer_s": 1., "dt_s": .004}))
    for name in ("optimist", "folkeboot", "yacht1"):
        with python_referenz():
            konfig = lade_konfig(ROOT / "konfigurationen")
            physik = lade_physik(ROOT / "konfigurationen")
            k, _ = baue_modellpaket(konfig, ROOT / "code" / "modelle" / name)
            snapshot = k.snapshot()
            kraft_python = baue_kraftfunktion_6dof(snapshot, pfad="exakt_union")
            rollen_python = HydrodynamikModell.aus_koerper(
                snapshot, rho_kg_m3=konfig.wasser_dichte())
            modell_python = baue_kraftmodell(
                kraft_python, physik, masse=snapshot.masse,
                g=physik.g_m_pro_s2, hydrodynamik=rollen_python)
            hydro_ergebnis = kraft_python(((0., 0., -.05), (1., 0., 0., 0.)))
            statik_python = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)
            gleichgewicht = loese_robust(
                statik_python, snapshot.masse, g=physik.g_m_pro_s2,
                start=(-.1, .01), tol=1e-6)
        kraft_cpp = baue_kraftfunktion_6dof(snapshot, pfad="exakt_union")
        rollen_cpp = HydrodynamikModell.aus_koerper(
            snapshot, rho_kg_m3=konfig.wasser_dichte())
        modell_cpp = baue_kraftmodell(
            kraft_cpp, physik, masse=snapshot.masse,
            g=physik.g_m_pro_s2, hydrodynamik=rollen_cpp)
        statik_cpp = baue_kraftfunktion(snapshot, pfad="exakt_union", g=physik.g_m_pro_s2)
        for name_block, funktion in (
            ("_farbgruppen", lambda: grafik_bruecke._farbgruppen(k)),
            ("_benetzte_geometrie", lambda: grafik_bruecke._benetzte_geometrie(k)),
        ):
            faelle.append(messfall(
                name_block + ": gesamte numerische Grafikvorbereitung",
                ["A-V0.10-00025"], funktion, 10,
                {"modell": name, "punkte": len(k.punkte), "dreiecke": len(k.dreiecke)}))
        _werte, hauptachsen_vektoren = grafik_bruecke.hauptachsen(
            k.traegheitstensor)
        faelle.append(messfall(
            "Hauptachsen-Overlay: native Richtungsrotation und Projektionsausdehnung",
            ["A-V0.10-00025"],
            lambda: grafik_bruecke._hauptachsen_geometrie(
                k.punkte, hauptachsen_vektoren, rotation),
            20, {"modell": name, "punkte": len(k.punkte)}))

        class GrafikDaten(dict):
            points = None

        bridge = grafik_bruecke.GrafikBruecke()
        bridge._actors_aktualisieren = lambda *args: None
        bridge._gruppen_actors = lambda *args: None
        bridge._overlays_aktualisieren = lambda *args: None
        anzeigegruppen = grafik_bruecke._farbgruppen(k)
        grafik = {
            "pd": GrafikDaten(referenz_punkte=k.punkte),
            "gruppen": [
                {"pd": GrafikDaten(referenz_punkte=g["punkte"])} for g in anzeigegruppen],
            "statisch_R": rotation, "position": np.array([.1, .2, -.1]),
        }
        faelle.append(messfall(
            "GrafikBruecke._statisch_anwenden: numerischer Sammelblock ohne Actor-/Overlayausgabe",
            ["A-V0.10-00025"], lambda: bridge._statisch_anwenden(name, grafik), 20,
            {"modell": name, "gruppen": len(anzeigegruppen),
             "punkte": len(k.punkte), "actor_und_overlayausgabe": "explizit ausgeschlossen"}))
        faelle.append(messfall(
            "kontakt_start einschliesslich nativer Hydrostatik",
            ["A-V0.10-00029"],
            lambda: stoerung.kontakt_start(
                statik_python if rechenpfad() == "python" else statik_cpp, 2., .1),
            5, {"modell": name, "z_start": 2., "phi": .1}))
        faelle.append(messfall(
            "dynamik.schritt_mit_kraeften: vereinfachter SI-Schritt einschliesslich Kraftadapter",
            ["A-V0.10-00029"],
            lambda: dynamik.schritt_mit_kraeften(
                dynamik.Bewegungszustand(-.1, .01, .05, .01),
                statik_python if rechenpfad() == "python" else statik_cpp,
                snapshot.masse, snapshot.traegheitstensor[0, 0], .004,
                physik.g_m_pro_s2, 1., 1.),
            20, {"modell": name, "dt_s": .004}))
        for funktion, aid in ((loese, "A-V0.10-00018"), (loese_robust, "A-V0.10-00017")):
            faelle.append(messfall(
                funktion.__module__ + "." + funktion.__name__, [aid],
                lambda: funktion(
                    statik_python if rechenpfad() == "python" else statik_cpp,
                    snapshot.masse, g=physik.g_m_pro_s2,
                    start=(gleichgewicht["z"] + .001, gleichgewicht["phi"] + .001), tol=1e-6),
                3, {"modell": name, "z0": gleichgewicht["z"] + .001,
                    "phi0": gleichgewicht["phi"] + .001}))
        p, f = snapshot.blatt_meshes[0]
        def selbstschnitt_kalt():
            with massen._SELBSTSCHNITT_CACHE_LOCK:
                massen._SELBSTSCHNITT_CACHE.clear()
            return massen.pruefe_mesh_selbstueberschneidung(p, f)

        faelle.append(messfall(
            "Mesh-Selbstschnitt: kalter Sweep-and-prune-Elternblock mit Dreieckspraedikaten",
            ["A-V0.10-00021"], selbstschnitt_kalt, 3,
            {"modell": name, "punkte": len(p), "dreiecke": len(f), "cache": "vor jedem Aufruf geleert"}))
        for funktion in (
                massen.mesh_volumen, massen.mesh_flaeche,
                massen.schwerpunkt_homogen, massen.schwerpunkt_flaechig,
                massen.traegheitstensor_homogen, massen.traegheitstensor_flaechig):
            faelle.append(messfall(
                funktion.__name__, ["A-V0.10-00021"], lambda: funktion(p, f), 30,
                {"modell": name, "punkte": len(p), "dreiecke": len(f)}))
        def kraft():
            return (kraft_python if rechenpfad() == "python" else kraft_cpp)(
                ((0., 0., -.05), (1., 0., 0., 0.)))
        def rollen():
            return (rollen_python if rechenpfad() == "python" else rollen_cpp).beitraege_erzeugen(
                ((0., 0., -.05), (1., 0., 0., 0.)), (.5, .1, .01), (.01, 0., .02))
        def kraftbilanz():
            return (modell_python if rechenpfad() == "python" else modell_cpp).mit_hydrostatik(
                hydro_ergebnis, (.5, .1, .01), (.01, 0., .02),
                ((0., 0., -.05), (1., 0., 0., 0.)))
        for block, funktion, n, aids in (
            ("Koerper.snapshot", k.snapshot, 50, ["A-V0.10-00020"]),
            ("Koerper.punkte_in_welt", k.punkte_in_welt, 50, ["A-V0.10-00020"]),
            ("Modellaufbau einschliesslich Koerper.verband/_baue_verband",
             lambda: baue_modellpaket(konfig, ROOT / "code" / "modelle" / name),
             1, ["A-V0.10-00020"]),
            ("baue_kraftfunktion_6dof: vorbereitete exakte Union/Ebenenschnitt",
             kraft, 50, ["A-V0.10-00012", "A-V0.10-00013", "A-V0.10-00014"]),
            ("wasserlinien_querschnitt/_ringe_aus_mesh/_ringmomente",
             lambda: hydrostatik.wasserlinien_querschnitt(snapshot.blatt_meshes),
             2, ["A-V0.10-00016"]),
            ("schneide_am_wasser mit Deckel: Elternblock inklusive Konturketten",
             lambda: wasser_schnitt.schneide_am_wasser(
                 snapshot.blatt_meshes[0][0], snapshot.blatt_meshes[0][1],
                 mit_deckel=True),
             5, ["A-V0.10-00015"]),
            ("HydrodynamikModell.aus_koerper einschliesslich nativer Vorbereitung",
             lambda: HydrodynamikModell.aus_koerper(
                 snapshot, rho_kg_m3=konfig.wasser_dichte()),
             5, ["A-V0.10-00011"]),
            ("HydrodynamikModell.beitraege_erzeugen: alle vorhandenen Rollen",
             rollen, 50, ["A-V0.10-00009", "A-V0.10-00010"]),
            ("Kraftmodell.mit_hydrostatik: Widerstand, Rollen und Gesamtwrench",
             kraftbilanz, 50, ["A-V0.10-00007", "A-V0.10-00008"]),
        ):
            faelle.append(messfall(block, aids, funktion, n, {"modell": name}))
    schreiben(args.output / "produktive_vergleiche.json", {
        "faelle": faelle,
        "hinweis": "Tatsaechliche oeffentliche Adapter, keine reine Kernzeit. "
                   "Noch kein vollstaendiger Migrations-/GUI-Live-Gesamtvergleich.",
        "nutzervorgabe": "Produktivuebernahme auch bei Verschlechterung; "
                        "Paritaet und Robustheit bleiben Pflicht.",
    })
    for fall in faelle:
        print("%s %s: Faktor %.3f" % (
            fall["funktion_oder_elternblock"], fall["eingabe"],
            fall["vergleich"]["beschleunigungsfaktor"]))


if __name__ == "__main__":
    main()
