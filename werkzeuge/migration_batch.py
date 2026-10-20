"""Diagnostiziert den noch nicht freigegebenen nativen Batch ohne Produktivumschaltung."""
import argparse
import hashlib
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segelphysik.core.auftrieb import baue_kraftfunktion_6dof
from segelphysik.core.dynamik_6dof import Zustand6DOF, schritt
from segelphysik.core.fabriken import baue_modellpaket
from segelphysik.core.hydrodynamik import HydrodynamikModell
from segelphysik.core.konfig_lader import lade_konfig, lade_physik
from segelphysik.core.kraftmodell import KraftmodellMitHydroCache, baue_kraftmodell
from segelphysik.core.native_backend import (
    ergebnis_nach_python, native_laden, physikkontext_vorbereiten, zustand_vorbereiten,
)
from segelphysik.core.rechenpfad import python_referenz, rechenpfad
from werkzeuge.benchmark_profil import umgebung
from werkzeuge.migration_inventar import (
    PRODUKTIVE_MIGRATIONSDATEIEN, referenzmanifest, schreiben,
)
from werkzeuge.migration_szenarien import kraftzeile


def kontexte(name):
    konfig = lade_konfig(ROOT / "konfigurationen")
    physik = lade_physik(ROOT / "konfigurationen")
    with python_referenz():
        k, _ = baue_modellpaket(konfig, ROOT / "code" / "modelle" / name)
        snapshot = k.snapshot()
        hydro_python = baue_kraftfunktion_6dof(
            snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2)
        rollen_python = HydrodynamikModell.aus_koerper(
            snapshot, rho_kg_m3=konfig.wasser_dichte(),
            fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
            fluidwinkelgeschwindigkeit=physik.fluidwinkelgeschwindigkeit)
        kraft = KraftmodellMitHydroCache(baue_kraftmodell(
            hydro_python, physik, masse=k.masse, g=physik.g_m_pro_s2,
            hydrodynamik=rollen_python), intervall=1)
    hydro_cpp = baue_kraftfunktion_6dof(
        snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2)
    rollen_cpp = HydrodynamikModell.aus_koerper(
        snapshot, rho_kg_m3=konfig.wasser_dichte(),
        fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
        fluidwinkelgeschwindigkeit=physik.fluidwinkelgeschwindigkeit)
    return k, physik, kraft, physikkontext_vorbereiten(
        snapshot, konfig.wasser_dichte(), physik, hydro_cpp, rollen_cpp)


def diagnose(name, ziel, anzahl):
    k, physik, kraft, kontext = kontexte(name)
    native = native_laden()
    zustand = Zustand6DOF(
        position=(0., 0., -.05), quaternion=(1., .01, .005, 0.),
        geschwindigkeit_koerper=(.1, .02, -.01),
        winkelgeschwindigkeit_koerper=(.01, -.01, .005))
    kandidat = zustand_vorbereiten(zustand)
    zustandsreihen = [kandidat.werte.copy()], [kandidat.werte.copy()]
    fehler_eingang, kraft_ref, kraft_cpp, schemas = [], [], [], []
    matrizen, rhs, loesungen_ref, loesungen_cpp = [], [], [], []
    original = np.linalg.solve

    def loesen(a, b):
        x = original(a, b)
        matrizen.append(a.copy())
        rhs.append(b.copy())
        loesungen_ref.append(x.copy())
        loesungen_cpp.append(native.linear_loesen(a, b))
        return x

    with patch.object(np.linalg, "solve", loesen):
        for _ in range(anzahl):
            gleicher_eingang = kontext.batch(
                zustand_vorbereiten(zustand), 1, None, 0., native.Abbruch())
            with python_referenz():
                zustand, erwartet = schritt(
                    zustand, kraft, k.masse, k.traegheitstensor,
                    physik.dt_s, physik.g_m_pro_s2)
            aktuell = kontext.batch(kandidat, 1, None, 0., native.Abbruch())
            kandidat = aktuell.zustand
            _, ergebnis = ergebnis_nach_python(aktuell)
            schema_ref, werte_ref = kraftzeile(erwartet)
            schema_cpp, werte_cpp = kraftzeile(ergebnis)
            if schema_cpp != schema_ref:
                raise AssertionError("Beitragsnamen oder Frames unterscheiden sich")
            schemas.append(schema_ref)
            kraft_ref.append(werte_ref)
            kraft_cpp.append(werte_cpp)
            zustandsreihen[0].append(zustand_vorbereiten(zustand).werte)
            zustandsreihen[1].append(kandidat.werte)
            fehler_eingang.append(
                gleicher_eingang.zustand.werte - zustand_vorbereiten(zustand).werte)
    ref, cpp = map(np.asarray, zustandsreihen)
    differenz = cpp - ref
    offsets = np.cumsum([0] + [len(k) for k in kraft_ref], dtype=np.int64)
    daten = {
        "referenz": ref, "kandidat": cpp,
        "fehler_gleicher_eingang": np.asarray(fehler_eingang),
        "kraft_referenz": np.concatenate(kraft_ref),
        "kraft_kandidat": np.concatenate(kraft_cpp),
        "kraft_offsets": offsets,
        "loesermatrizen": np.asarray(matrizen), "rechte_seiten": np.asarray(rhs),
        "loesungen_referenz": np.asarray(loesungen_ref),
        "loesungen_kandidat": np.asarray(loesungen_cpp),
    }
    if any(not np.isfinite(a).all() for a in daten.values()):
        raise ValueError("Nicht-endlicher Diagnosewert")
    datei = ziel / (name + ".npz")
    with datei.open("xb") as stream:
        np.savez_compressed(stream, **daten)
    result = {
        "modell": name, "schritte": anzahl, "dt_s": physik.dt_s,
        "daten": datei.name, "sha256": hashlib.sha256(datei.read_bytes()).hexdigest(),
        "schemas_je_schritt": schemas,
        "max_zustandsfehler_je_komponente": np.max(np.abs(differenz), axis=0).tolist(),
        "max_fehler_gleicher_eingang": float(np.max(np.abs(fehler_eingang))),
        "max_kraftfeldfehler": float(np.max(np.abs(
            daten["kraft_kandidat"] - daten["kraft_referenz"]))),
        "max_loeserfehler": float(np.max(np.abs(
            daten["loesungen_kandidat"] - daten["loesungen_referenz"]))),
        "trajektoriengrenze_zustand_1e12_bestanden": bool(np.all(np.abs(differenz) <= 1e-12)),
        "trajektoriengrenze_kraft_1e9_bestanden": bool(np.all(np.abs(
            daten["kraft_kandidat"] - daten["kraft_referenz"]) <= 1e-9)),
        "produktiver_batch": False,
    }
    schreiben(ziel / (name + ".json"), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schritte", type=int, default=1000)
    args = parser.parse_args()
    if args.schritte < 1 or rechenpfad() != "cpp":
        raise ValueError("Positive Schrittzahl und expliziter cpp-Pfad erforderlich")
    args.output.mkdir(parents=True, exist_ok=False)
    native = native_laden()
    quellen = [ROOT / p for p in PRODUKTIVE_MIGRATIONSDATEIEN]
    quellen += list((ROOT / "code" / "cpp" / "src").glob("*"))
    quellen += [
        Path(__file__),
        ROOT / "code" / "python" / "segelphysik" / "core" / "native_backend.py",
        ROOT / "code" / "python" / "segelphysik" / "core" / "rechenpfad.py",
    ]
    schreiben(args.output / "umgebung.json", {
        "umgebung": umgebung(),
        "native_binary_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "quellen_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in quellen},
        "referenzmanifest": referenzmanifest(
            native_kandidaten=True, produktive_migration=True),
        "hinweis": "Numerikdiagnose, keine Performance- oder M5-Abnahme. "
                   "Die bisherige Trajektorienpruefung wird nicht gelockert.",
    })
    bestanden = True
    for name in ("optimist", "folkeboot", "yacht1"):
        daten = diagnose(name, args.output, args.schritte)
        print("%s: Zustand %.12g, Kraftfelder %.12g, identischer Eingang %.12g" % (
            name, max(daten["max_zustandsfehler_je_komponente"]),
            daten["max_kraftfeldfehler"], daten["max_fehler_gleicher_eingang"]), flush=True)
        bestanden &= (daten["trajektoriengrenze_zustand_1e12_bestanden"]
                      and daten["trajektoriengrenze_kraft_1e9_bestanden"])
    return 0 if bestanden else 1


if __name__ == "__main__":
    raise SystemExit(main())
