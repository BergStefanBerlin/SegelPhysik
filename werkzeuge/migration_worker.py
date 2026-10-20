"""Misst produktive Worker und dokumentiert strenge sowie vorlaeufige Paritaet."""
import argparse
from contextlib import nullcontext
import hashlib
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segelphysik.core import echtzeit_prozess
from segelphysik.core.rechenpfad import python_referenz, rechenpfad
from segelphysik.core.native_backend import native_laden
from werkzeuge.benchmark_profil import umgebung
from werkzeuge.migration_inventar import (
    PRODUKTIVE_MIGRATIONSDATEIEN, referenzmanifest, schreiben,
)
from werkzeuge.migration_szenarien import (
    folge_berechnen, folge_pruefen, koerper_laden, schrittanzahl, startzustand,
)
from werkzeuge.migration_vergleich import performancevergleich


VORLAEUFIG_ZUSTAND_ATOL = np.array([1e-5] * 3 + [1e-6] * 4 + [1e-5] * 6)
VORLAEUFIG_KRAFT_RTOL = 1e-6
VORLAEUFIG_KRAFT_ATOL = 1.


def folgevergleich(ref, cpp, schemas_ref, schemas_cpp):
    if schemas_ref != schemas_cpp:
        raise AssertionError("Kraftbeitragsnamen oder Frames veraendert")
    for feld in ("zeit_s", "kraft_offsets", "schema_indices"):
        np.testing.assert_array_equal(ref[feld], cpp[feld], err_msg=feld)
    for daten in (ref, cpp):
        if any(not np.isfinite(a).all() for a in daten.values()):
            raise AssertionError("Nicht-endliche Trajektoriendaten")
    dz = np.abs(cpp["zustaende"] - ref["zustaende"])
    dk = np.abs(cpp["kraftwerte"] - ref["kraftwerte"])
    bestanden = bool(np.all(dz <= VORLAEUFIG_ZUSTAND_ATOL))
    for index, schema_index in enumerate(ref["schema_indices"]):
        start, ende = ref["kraft_offsets"][index:index + 2]
        atol = np.array(
            [1e-7] + [1e-5] * 3 + [VORLAEUFIG_KRAFT_ATOL] * 9 + [1e-5] * 3
            + ([1e-5] * 3 + [VORLAEUFIG_KRAFT_ATOL] * 6) * len(schemas_ref[schema_index]))
        bestanden &= bool(np.all(np.isclose(
                cpp["kraftwerte"][start:ende], ref["kraftwerte"][start:ende],
                rtol=VORLAEUFIG_KRAFT_RTOL, atol=atol, equal_nan=False)))
    return {
        "vorlaeufig_bestanden": bestanden,
        "streng_zustand_bestanden": bool(np.all(dz <= 1e-12)),
        "streng_kraft_bestanden": bool(np.all(dk <= 1e-9)),
        "max_zustandsabweichung_je_komponente": dz.max(axis=0).tolist(),
        "max_kraftfeldabweichung": float(dk.max()),
        "vorlaeufig_zustand_atol": VORLAEUFIG_ZUSTAND_ATOL.tolist(),
        "vorlaeufig_kraft_rtol": VORLAEUFIG_KRAFT_RTOL,
        "vorlaeufig_kraft_atol": {
            "volumen_m3": 1e-7, "punkte_m": 1e-5,
            "kraefte_N_momente_Nm": VORLAEUFIG_KRAFT_ATOL},
        "hinweis": "Nutzerfreigabe 20.10.2026; vorlaeufiger Naeherungsvergleich, "
                   "kein Nachweis strenger numerischer Paritaet.",
    }


def modellvergleich(name, ziel, dauer):
    with python_referenz():
        konfig, physik, snapshot = koerper_laden(name)
        start, _ = startzustand(snapshot, konfig, physik)
    anzahl = schrittanzahl(dauer, physik.dt_s)
    folgen, schemas, zeiten = [], [], []
    for referenz in (True, False):
        with python_referenz() if referenz else nullcontext():
            echtzeit_prozess.initialisieren(snapshot, konfig.wasser_dichte(), physik)
            daten, schema, zeit = folge_berechnen(
                start, anzahl, physik.dt_s, echtzeit_prozess.schritte_berechnen)
        folge_pruefen(daten, schema, dauer, physik.dt_s)
        folgen.append(daten)
        schemas.append(schema)
        zeiten.append(zeit)
    datei = ziel / (name + "_folgen.npz")
    with datei.open("xb") as stream:
        np.savez_compressed(stream, **{
            ("python_" if i == 0 else "cpp_") + key: a
            for i, daten in enumerate(folgen) for key, a in daten.items()})
    schreiben(ziel / (name + "_schemas.json"), schemas)
    vergleich = folgevergleich(*folgen, *schemas)
    # Uninstrumentierte ganze Batches: gleiche Startdaten, wechselnde Reihenfolge.
    messungen = {True: [], False: []}
    aufbau = {True: [], False: []}
    for wiederholung in range(7):
        for referenz in ((True, False) if wiederholung % 2 == 0 else (False, True)):
            with python_referenz() if referenz else nullcontext():
                t = time.perf_counter()
                echtzeit_prozess.initialisieren(snapshot, konfig.wasser_dichte(), physik)
                aufbau[referenz].append(time.perf_counter() - t)
                t = time.perf_counter()
                ergebnis = echtzeit_prozess.schritte_berechnen(start, 1000)
                messungen[referenz].append(time.perf_counter() - t)
                if ergebnis[2] is not None:
                    raise RuntimeError(ergebnis[2])
    result = {
        "modell": name, "dauer_s": dauer, "dt_s": physik.dt_s, "schritte": anzahl,
        "daten": datei.name, "sha256": hashlib.sha256(datei.read_bytes()).hexdigest(),
        "vergleich": vergleich, "einzelschrittfolge_zeiten": zeiten,
        "batch_1000_performance": performancevergleich(messungen[True], messungen[False]),
        "kontextaufbau_performance": performancevergleich(aufbau[True], aufbau[False]),
        "kosten": "Ganzen Workeraufruf inklusive Eingabe-/Ergebnisadapter gemessen; "
                  "Kontextaufbau separat. Kein Prozess-/GUI-/Live-Gesamtvergleich.",
    }
    schreiben(ziel / (name + ".json"), result)
    print("%s: %g s, Max Zustand %.9g, Max Kraftfeld %.9g, Batchfaktor %.3f" % (
        name, dauer, max(vergleich["max_zustandsabweichung_je_komponente"]),
        vergleich["max_kraftfeldabweichung"],
        result["batch_1000_performance"]["beschleunigungsfaktor"]), flush=True)
    return vergleich["vorlaeufig_bestanden"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dauer", type=float, default=30.)
    parser.add_argument("--modelle", nargs="+", choices=("optimist", "folkeboot", "yacht1"),
                        default=["optimist", "folkeboot", "yacht1"])
    args = parser.parse_args()
    if rechenpfad() != "cpp" or not np.isfinite(args.dauer) or args.dauer <= 0:
        raise ValueError("Expliziter cpp-Pfad und positive endliche Dauer erforderlich")
    args.output.mkdir(parents=True, exist_ok=False)
    quellen = [ROOT / p for p in PRODUKTIVE_MIGRATIONSDATEIEN]
    quellen += list((ROOT / "code" / "cpp" / "src").glob("*"))
    quellen += [Path(__file__), ROOT / "code" / "python" / "segelphysik" / "core" / "native_backend.py"]
    schreiben(args.output / "umgebung.json", {
        "umgebung": umgebung(),
        "native_binary_sha256": hashlib.sha256(
            Path(native_laden().__file__).read_bytes()).hexdigest(),
        "quellen_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in quellen},
        "referenzmanifest": referenzmanifest(
            native_kandidaten=True, produktive_migration=True),
    })
    bestanden = True
    for name in args.modelle:
        bestanden &= modellvergleich(name, args.output, args.dauer)
    return 0 if bestanden else 1


if __name__ == "__main__":
    raise SystemExit(main())
