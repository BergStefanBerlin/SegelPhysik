"""Misst die M2-Kandidaten in der expliziten nativen Testinstallation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segelphysik.core import dynamik_6dof as python
from segelphysik.core import frames
from segelphysik.core import native_backend
from segelphysik.core.native_backend import native_laden
from segelphysik.core.rechenpfad import python_referenz
from werkzeuge.benchmark_profil import umgebung
from werkzeuge.migration_baseline import buildinventar
from werkzeuge.migration_inventar import referenzmanifest, schreiben, texthash
from werkzeuge.migration_vergleich import performancevergleich


def zeitreihe(funktion, anzahl, wiederholungen=7):
    if anzahl < 1 or wiederholungen < 3:
        raise ValueError("Positive Aufrufzahl und mindestens drei Wiederholungen erforderlich")
    funktion()
    werte = []
    for _ in range(wiederholungen):
        start = time.perf_counter()
        for _ in range(anzahl):
            funktion()
        werte.append((time.perf_counter() - start) / anzahl)
    return werte


def messfall(name, original, kandidat, anzahl, eingabe):
    a, b = original(), kandidat()
    np.testing.assert_allclose(a, b, rtol=0., atol=1e-12)
    vorher = zeitreihe(original, anzahl)
    nachher = zeitreihe(kandidat, anzahl)
    return {
        "funktion": name, "eingabe": eingabe, "aufrufe_pro_wiederholung": anzahl,
        "python_s": vorher, "cpp_s": nachher,
        "vergleich": performancevergleich(vorher, nachher),
        "max_abs_abweichung": float(np.max(np.abs(np.asarray(a) - np.asarray(b)))),
        "paritaetsgrenze": {
            "rtol": 0., "atol": 1e-12, "quelle": "tests/test_frames.py"},
        "produktiv_freigegeben": False,
        "hinweis": (
            "Diagnostischer Einzelaufruf einschliesslich pybind-/Arrayuebergabe "
            "und genannter Ausgabeaufbereitung. Keine GUI-/Physikbatch-Abnahme."),
    }


def messen(native):
    q = np.array([2., -.3, .2, .4])
    p = np.array([.7, .1, -.2, .4])
    t = np.array([1., 2., 3.])
    omega = np.array([.1, -.2, .3])
    rotation = python.quaternion_matrix(q)
    pose = frames.Pose("welt", "rumpf", t, q)
    innen = frames.Pose("rumpf", "kiel", -t, p)
    np_pose = native.Pose("welt", "rumpf", t, q)
    np_innen = native.Pose("rumpf", "kiel", -t, p)
    eingabe = {"quaternion": q.tolist(), "translation": t.tolist()}
    modellpose = SimpleNamespace(translation_m=t, rotation_quaternion_wxyz=q)
    gelenk = SimpleNamespace(achse_eltern=(1., 2., -3.), winkel_rad=.3)
    faelle = [
        ("quaternion_normalisieren", lambda: python.quaternion_normalisieren(q),
         lambda: native.quaternion_normalisieren(q)),
        ("quaternion_matrix", lambda: python.quaternion_matrix(q),
         lambda: native.quaternion_matrix(q)),
        ("quaternion_aus_matrix", lambda: python.quaternion_aus_matrix(rotation),
         lambda: tuple(native.quaternion_aus_matrix(rotation))),
        ("_quaternion_multiplizieren", lambda: python._quaternion_multiplizieren(q, p),
         lambda: native.quaternion_multiplizieren(q, p)),
        ("_orientierung_schritt", lambda: python._orientierung_schritt(q, omega, .004),
         lambda: native.orientierung_schritt(q, omega, .004)),
        ("rotationsmatrix_achsenwinkel", lambda: frames.rotationsmatrix_achsenwinkel(t, .3),
         lambda: native.rotationsmatrix_achsenwinkel(t, .3)),
        ("Pose.__post_init__", lambda: frames.Pose("welt", "rumpf", t, q).rotation_quaternion_wxyz,
         lambda: tuple(native.Pose("welt", "rumpf", t, q).rotation_quaternion_wxyz)),
        ("Pose.rotationsmatrix", lambda: pose.rotationsmatrix,
         lambda: np_pose.rotationsmatrix),
        ("Pose.punkt_transformieren", lambda: pose.punkt_transformieren(t),
         lambda: np_pose.punkt_transformieren(t)),
        ("Pose.vektor_transformieren", lambda: pose.vektor_transformieren(t),
         lambda: np_pose.vektor_transformieren(t)),
        ("Pose.invers", lambda: pose.invers().rotationsmatrix,
         lambda: np_pose.invers().rotationsmatrix),
        ("Pose.komponieren", lambda: pose.komponieren(innen).rotationsmatrix,
         lambda: np_pose.komponieren(np_innen).rotationsmatrix),
        ("pose_aus_modellpose",
         lambda: frames.pose_aus_modellpose(modellpose, "welt", "rumpf").rotation_quaternion_wxyz,
         lambda: tuple(native_backend.pose_aus_modellpose(
             modellpose, "welt", "rumpf").rotation_quaternion_wxyz)),
        ("pose_mit_gelenkwinkel",
         lambda: frames.pose_mit_gelenkwinkel(modellpose, gelenk).rotation_quaternion_wxyz,
         lambda: tuple(native_backend.pose_mit_gelenkwinkel(
             modellpose, gelenk).rotation_quaternion_wxyz)),
    ]
    ergebnisse = [
        messfall(name, original, kandidat, 2000, eingabe)
        for name, original, kandidat in faelle]
    rng = np.random.default_rng(1010)
    for groesse in (1, 1000, 100000):
        punkte = rng.normal(size=(groesse, 3))
        ergebnisse.append(messfall(
            "Pose.punkte_transformieren",
            lambda: pose.punkte_transformieren(punkte),
            lambda: np_pose.punkte_transformieren(punkte),
            2000 if groesse == 1 else 100 if groesse == 1000 else 10,
            {"form": list(punkte.shape), "dtype": str(punkte.dtype),
             "sha256": hashlib.sha256(punkte.tobytes()).hexdigest(),
             "seed": 1010, "groessenfolge": [1, 1000, 100000]},
        ))
        mesh = native.Mesh(punkte, np.empty((0, 3), dtype=np.int64))
        ergebnisse.append(messfall(
            "Pose.punkte_transformieren (vorbereiteter nativer Meshkontext)",
            lambda: pose.punkte_transformieren(punkte),
            lambda: np_pose.vorbereitete_punkte_transformieren(mesh),
            2000 if groesse == 1 else 100 if groesse == 1000 else 10,
            {"form": list(punkte.shape), "dtype": str(punkte.dtype),
             "sha256": hashlib.sha256(punkte.tobytes()).hexdigest(),
             "vorbereitung_s": zeitreihe(
                 lambda: native.Mesh(punkte, np.empty((0, 3), dtype=np.int64)), 10)},
        ))
    return ergebnisse


def aggregation_messen(native):
    from segelphysik.core.koerper import Koerper
    from segelphysik.core.koerper_formen import build_box
    from segelphysik.core.massen import validiere_traegheitstensor

    ergebnisse = []
    for anzahl in (1, 30, 300):
        rng = np.random.default_rng(1010)
        kind = Koerper(form=build_box(1., 2., 3.), masse=2., zustand=None)
        originalteile = [
            (kind, (np.eye(3), rng.normal(size=3))) for _ in range(anzahl)]

        def vorbereiten():
            return [
                native.Koerperteil(
                    k.masse, k.traegheitstensor,
                    native.Mesh(k.punkte, k.dreiecke),
                    native.Pose("verband", "teil", t, np.array([1., 0., 0., 0.])))
                for k, (_rotation, t) in originalteile]

        teile = vorbereiten()
        kontext = native.VerbandKontext(teile, 0)
        abbruch = native.Abbruch()

        def original():
            k = Koerper(teile=originalteile, zustand=None)
            return {
                "masse": k.masse, "schwerpunkt": k._r_eingabe,
                "traegheit": k.traegheitstensor, "punkte": k.punkte, "dreiecke": k.dreiecke}

        def ausgabe(v):
            return {
                "masse": v.masse, "schwerpunkt": v.schwerpunkt,
                "traegheit": validiere_traegheitstensor(v.traegheit),
                "punkte": v.punkte, "dreiecke": v.dreiecke}

        def kandidat():
            return ausgabe(kontext.aggregieren(abbruch))

        def neuaufbau():
            return ausgabe(native.VerbandKontext(vorbereiten(), 0).aggregieren(abbruch))

        a, b = original(), kandidat()
        for name in a:
            np.testing.assert_allclose(a[name], b[name], rtol=0., atol=1e-12)
        aufrufe = 100 if anzahl < 300 else 10
        vorher = zeitreihe(original, aufrufe)
        nachher = zeitreihe(kandidat, aufrufe)
        gesamtkosten = zeitreihe(neuaufbau, aufrufe)
        ergebnisse.append({
            "funktion": "Koerper._baue_verband (vorbereiteter numerischer Block)",
            "teile": anzahl, "punkte": anzahl * len(kind.punkte),
            "dreiecke": anzahl * len(kind.dreiecke),
            "aufrufe_pro_wiederholung": aufrufe,
            "python_s": vorher, "cpp_vorbereitet_s": nachher,
            "cpp_mit_neuaufbau_s": gesamtkosten,
            "vorbereitet_vergleich": performancevergleich(vorher, nachher),
            "neuaufbau_vergleich": performancevergleich(vorher, gesamtkosten),
            "native_vorbereitung_s": zeitreihe(vorbereiten, aufrufe),
            "kontextaufbau_s": zeitreihe(lambda: native.VerbandKontext(teile, 0), aufrufe),
            "reiner_kern_s": zeitreihe(lambda: kontext.aggregieren(abbruch), aufrufe),
            "produktiv_freigegeben": False,
            "hinweis": (
                "Unveraenderte native NumPy-Eigenwertvalidierung ausserhalb der "
                "Aggregation; keine Python-Kraftcallbacks. Vorbereitete Kontexte "
                "kopieren Modelldaten nicht je Rechnung. Neuaufbau separat "
                "einschliesslich aller Konvertierungen und Ausgabearrays. "
                "Noch keine vollstaendige Koerper-/GUI-/Snapshotintegration."),
        })
    return ergebnisse


def snapshot_messen():
    from segelphysik.core.fabriken import baue_modellpaket
    from segelphysik.core.konfig_lader import lade_konfig
    from werkzeuge.migration_vergleich import vergleiche

    ergebnisse = []
    konfig = lade_konfig(ROOT / "konfigurationen")
    for name in ("optimist", "folkeboot", "yacht1"):
        k, _ = baue_modellpaket(konfig, ROOT / "code" / "modelle" / name)
        kontext = native_backend.NativeKoerperKontext(k)
        a, b = k.snapshot(), kontext.snapshot(k)
        for attribut in ("masse", "traegheitstensor", "r_S", "zustand",
                         "version", "basis_pose", "gelenkzustaende"):
            vergleiche(getattr(a, attribut), getattr(b, attribut))
        if (len(a.blatt_meshes) != len(b.blatt_meshes)
                or len(a.hydrodynamik_teile) != len(b.hydrodynamik_teile)):
            raise ValueError("Snapshot-Meshschema geaendert: " + name)
        for (p, f), (p2, f2) in zip(a.blatt_meshes, b.blatt_meshes):
            np.testing.assert_allclose(p2, p, rtol=0., atol=1e-12)
            np.testing.assert_array_equal(f2, f)
        for (rolle, titel, p, f), (rolle2, titel2, p2, f2) in zip(
                a.hydrodynamik_teile, b.hydrodynamik_teile):
            if (rolle2, titel2) != (rolle, titel):
                raise ValueError("Snapshot-Rolle oder -Name geaendert: " + name)
            np.testing.assert_allclose(p2, p, rtol=0., atol=1e-12)
            np.testing.assert_array_equal(f2, f)
        vorher = zeitreihe(k.snapshot, 100)
        nachher = zeitreihe(lambda: kontext.snapshot(k), 100)
        ergebnisse.append({
            "funktion": "Koerper.snapshot", "modell": name,
            "punkte": sum(len(p) for p, _ in a.blatt_meshes),
            "dreiecke": sum(len(f) for _, f in a.blatt_meshes),
            "python_s": vorher, "cpp_s": nachher,
            "vergleich": performancevergleich(vorher, nachher),
            "kontext_vorbereitung_s": zeitreihe(
                lambda: native_backend.NativeKoerperKontext(k), 10),
            "produktiv_freigegeben": False,
            "hinweis": (
                "Gesamter Snapshotadapter inklusive exakter Quell-/Unterbaum-/"
                "Meshinvalidierung vor und nach der nativen Rechnung sowie "
                "Ausgabekopien. Unveraenderliche Geometrie wird beim Kontextaufbau "
                "einmal nativ transformiert; deren exakte Vorlage wird danach "
                "ohne gerundete Zustandsschluessel kopiert. Vorbereitung separat. "
                "Python-Baumvorbereitung bleibt Aufbaugrenze; "
                "kein Callback waehrend der nativen Geometrietransformation."),
        })
    return ergebnisse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-verzeichnis", type=Path, required=True)
    args = parser.parse_args(argv)
    native = native_laden()
    args.output.mkdir(parents=True, exist_ok=False)
    schreiben(args.output / "umgebung.json", {
        "umgebung": umgebung(), "build": buildinventar(args.build_verzeichnis),
        "native_modul": native.__file__,
        "native_binary_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "native_abi": native.ABI_VERSION, "rechenpfad": native.RECHENPFAD,
        "referenzmanifest": referenzmanifest(
            native_kandidaten=True, produktive_migration=True),
        "quellen_sha256": {
            str(p.relative_to(ROOT)): texthash(p)
            for p in [Path(__file__), ROOT / "code" / "cpp" / "src" / "modul.cpp",
                      ROOT / "code" / "cpp" / "src" / "datentypen.hpp",
                      ROOT / "code" / "cpp" / "src" / "frames.hpp",
                      ROOT / "code" / "cpp" / "src" / "koerperkontext.hpp",
                      ROOT / "code" / "cpp" / "CMakeLists.txt",
                      ROOT / "code" / "python" / "segelphysik" / "core" / "native_backend.py"]},
    })
    with python_referenz():
        ergebnisse = messen(native)
        aggregation = aggregation_messen(native)
        snapshots = snapshot_messen()
    schreiben(args.output / "mathematik_frames.json", {
        "faelle": ergebnisse, "produktiv_freigegeben": False,
        "aggregation": aggregation,
        "snapshots": snapshots,
        "hinweis": "M2-Kandidatenmikromessungen, keine abgeschlossene U5-/End-to-End-Abnahme.",
    })
    for fall in ergebnisse:
        print("%s %s: Faktor %.3f" % (
            fall["funktion"], fall["eingabe"].get("form", ""),
            fall["vergleich"]["beschleunigungsfaktor"]))
    for fall in aggregation:
        print("Aggregation %d Teile: vorbereitet %.3f, Neuaufbau %.3f" % (
            fall["teile"], fall["vorbereitet_vergleich"]["beschleunigungsfaktor"],
            fall["neuaufbau_vergleich"]["beschleunigungsfaktor"]))
    for fall in snapshots:
        print("Snapshot %s: Faktor %.3f" % (
            fall["modell"], fall["vergleich"]["beschleunigungsfaktor"]))


if __name__ == "__main__":
    main()
