"""Weitere M1-Referenzszenarien; keine native oder produktive Umschaltung.

Dynamik friert jeden Integrationszeitpunkt samt Einzelwrenches ein.
Prozessmessungen trennen Serialisierung und Workerrechnung vom Roundtrip.
Regressionprofile weisen Aufrufe nach, nicht uninstrumentierte Performance.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import redirect_stdout
from dataclasses import asdict, replace
from functools import wraps
import hashlib
import json
import math
import multiprocessing
import os
import pickle
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from werkzeuge.benchmark_profil import eingabe_hash, umgebung
from werkzeuge.migration_baseline import (
    MODELLE, CallbackProfil, buildinventar, funktionsmessungen, kraftdaten,
    profilieren, serialisieren,
)
from werkzeuge.migration_inventar import (
    REFERENZ, profilbewertung, referenzmanifest, schreiben, texthash,
)
from werkzeuge.migration_vergleich import messen, vergleiche, zeitstatistik


def schrittanzahl(dauer_s, dt_s):
    if (not math.isfinite(dauer_s) or not math.isfinite(dt_s)
            or dauer_s <= 0 or dt_s <= 0):
        raise ValueError("Dauer und Zeitschritt muessen positiv und endlich sein")
    anzahl = round(dauer_s / dt_s)
    if anzahl < 1 or not math.isclose(anzahl * dt_s, dauer_s, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Messdauer muss ein ganzzahliges Vielfaches von dt sein")
    return anzahl


def koerper_laden(name):
    from segelphysik.core.fabriken import baue_modellpaket
    from segelphysik.core.konfig_lader import lade_konfig, lade_physik

    konfig = lade_konfig(ROOT / "konfigurationen")
    physik = lade_physik(ROOT / "konfigurationen")
    koerper, _ = baue_modellpaket(konfig, ROOT / "code" / "modelle" / name)
    return konfig, physik, koerper.snapshot()


def startzustand(snapshot, konfig, physik):
    from segelphysik.core.auftrieb import baue_kraftfunktion
    from segelphysik.core.dynamik_6dof import Zustand6DOF
    from segelphysik.core.stationaer_hydrodynamik import _rotation
    from segelphysik.core.dynamik_6dof import quaternion_aus_matrix
    from segelphysik.core.statisch_robust import loese_robust

    hydro = baue_kraftfunktion(
        snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2,
        pfad="exakt_union")
    gleichgewicht = loese_robust(hydro, snapshot.masse, g=physik.g_m_pro_s2)
    zustand = Zustand6DOF(
        position=(0., 0., gleichgewicht["z"] + .01),
        quaternion=quaternion_aus_matrix(_rotation(
            gleichgewicht["phi"] + math.radians(5),
            math.radians(2), 0.)),
    )
    return zustand, gleichgewicht


def zustandszeile(zustand):
    return np.asarray((
        *zustand.position, *zustand.quaternion,
        *zustand.geschwindigkeit_koerper, *zustand.winkelgeschwindigkeit_koerper,
    ), dtype=np.float64)


def kraftzeile(ergebnis):
    labels = []
    werte = [
        ergebnis.V_tauch, *ergebnis.K.as_array(), *ergebnis.F_A.as_array(),
        *ergebnis.F_gesamt.as_array(), *ergebnis.M_gesamt.as_array(),
        *ergebnis.bezugspunkt_m,
    ]
    for beitrag in ergebnis.beitraege:
        wrench = beitrag.wrench
        labels.append((beitrag.name, wrench.frame))
        werte.extend((*wrench.bezugspunkt_m, *wrench.kraft_N, *wrench.moment_Nm))
    daten = np.asarray(werte, dtype=np.float64)
    if not np.isfinite(daten).all():
        raise ValueError("Nicht-endliche Dynamikreferenz")
    return tuple(labels), daten


def folge_berechnen(start, anzahl, dt_s, batchfunktion):
    if isinstance(anzahl, bool) or not isinstance(anzahl, int) or anzahl < 1:
        raise ValueError("Positive ganzzahlige Schrittanzahl erforderlich")
    schrittanzahl(anzahl * dt_s, dt_s)
    zustaende = np.empty((anzahl + 1, 13), dtype=np.float64)
    zustaende[0] = zustandszeile(start)
    if not np.isfinite(zustaende[0]).all():
        raise ValueError("Nicht-endlicher Anfangszustand")
    kraefte = []
    schemas = []
    schema_indices = []
    workerzeiten = []
    zustand = start
    startzeit = time.perf_counter()
    for index in range(anzahl):
        zustand, ergebnis, fehler, dauer = batchfunktion(zustand, 1)
        if fehler is not None:
            raise RuntimeError("Dynamikschritt %d: %s" % (index + 1, fehler))
        zustaende[index + 1] = zustandszeile(zustand)
        schema, kraft = kraftzeile(ergebnis)
        if schema not in schemas:
            schemas.append(schema)
        schema_indices.append(schemas.index(schema))
        kraefte.append(kraft)
        workerzeiten.append(dauer)
    if not np.isfinite(zustaende).all():
        raise ValueError("Nicht-endliche Zustandsfolge")
    # Beitraege koennen bei trocken/nass wechseln: kein Padding mit Erfolgsnullen.
    offsets = np.cumsum([0] + [len(k) for k in kraefte], dtype=np.int64)
    daten = {
        "zeit_s": np.arange(anzahl + 1, dtype=np.float64) * dt_s,
        "zustaende": zustaende,
        "kraftwerte": np.concatenate(kraefte),
        "kraft_offsets": offsets,
        "schema_indices": np.asarray(schema_indices, dtype=np.int64),
    }
    return daten, schemas, {
        "gesamt_s": time.perf_counter() - startzeit,
        "worker_einzelschritte": zeitstatistik(workerzeiten),
    }


def folge_pruefen(daten, schemas, dauer_s, dt_s):
    anzahl = schrittanzahl(dauer_s, dt_s)
    if set(daten) != {
            "zeit_s", "zustaende", "kraftwerte", "kraft_offsets", "schema_indices"}:
        raise ValueError("Unvollstaendiges Dynamikdatenformat")
    for key in ("zeit_s", "zustaende", "kraftwerte"):
        if daten[key].dtype != np.float64 or not np.isfinite(daten[key]).all():
            raise ValueError("Float64-Endlichkeit verletzt: " + key)
    for key, shape in (
            ("zeit_s", (anzahl + 1,)), ("zustaende", (anzahl + 1, 13)),
            ("kraft_offsets", (anzahl + 1,)), ("schema_indices", (anzahl,))):
        if daten[key].shape != shape:
            raise ValueError("Dynamikdatenform verletzt: " + key)
    np.testing.assert_array_equal(
        daten["zeit_s"], np.arange(anzahl + 1, dtype=np.float64) * dt_s)
    if (daten["kraft_offsets"].dtype != np.int64
            or daten["schema_indices"].dtype != np.int64
            or daten["kraftwerte"].ndim != 1 or not schemas
            or np.any(daten["schema_indices"] < 0)
            or np.any(daten["schema_indices"] >= len(schemas))):
        raise ValueError("Ungueltige Dynamikindizes oder Schemas")
    if any(not isinstance(wert, str) or not wert
           for schema in schemas for paar in schema for wert in paar):
        raise ValueError("Beitragsname/Frame fehlt im Kraftschema")
    if any(len(paar) != 2 for schema in schemas for paar in schema):
        raise ValueError("Kraftschema braucht Name und Frame je Beitrag")
    laengen = np.array([16 + 9 * len(s) for s in schemas], dtype=np.int64)
    erwartet = np.cumsum(np.r_[np.int64(0), laengen[daten["schema_indices"]]])
    np.testing.assert_array_equal(daten["kraft_offsets"], erwartet)
    if daten["kraftwerte"].size != erwartet[-1]:
        raise ValueError("Fehlende oder ueberzaehlige Kraftwerte")
    np.testing.assert_allclose(
        np.linalg.norm(daten["zustaende"][:, 3:7], axis=1),
        1., rtol=0, atol=1e-8)


def schwingungskennwerte(zeiten, werte, gleichgewicht):
    zeiten = np.asarray(zeiten, dtype=np.float64)
    werte = np.asarray(werte, dtype=np.float64)
    if (zeiten.ndim != 1 or zeiten.size < 3 or werte.shape != zeiten.shape
            or not np.isfinite(zeiten).all() or not np.isfinite(werte).all()
            or not math.isfinite(gleichgewicht) or not np.all(np.diff(zeiten) > 0)):
        raise ValueError("Endliche gleichlange Schwingungsreihen mit steigender Zeit erforderlich")
    signal = werte - gleichgewicht
    indizes = np.flatnonzero((signal[:-1] < 0) & (signal[1:] >= 0))
    nullen = [
        float(zeiten[i] - signal[i] * (zeiten[i + 1] - zeiten[i])
              / (signal[i + 1] - signal[i])) for i in indizes]
    perioden = np.diff(nullen)
    amplitude = np.abs(signal)
    maxima = list(np.flatnonzero(
        (amplitude[1:-1] > amplitude[:-2])
        & (amplitude[1:-1] >= amplitude[2:])) + 1)
    if amplitude[0] > amplitude[1]:
        maxima.insert(0, 0)
    unter_grenze = amplitude[maxima] < amplitude[0] / math.e
    abklingzeit = None
    for i in range(len(maxima) - 1):
        if amplitude[0] > 0 and np.all(unter_grenze[i:]):
            abklingzeit = float(zeiten[maxima[i]] - zeiten[0])
            break
    return {
        "gleichgewicht": gleichgewicht,
        "anfangsamplitude": float(amplitude[0]),
        "gleichgerichtete_nulldurchgaenge_s": nullen,
        "perioden_s": perioden.tolist(),
        "periode_median_s": float(np.median(perioden)) if perioden.size else None,
        "periodenstatus": "messbar" if perioden.size else
            "nicht messbar: weniger als zwei aufwaertsgerichtete Nulldurchgaenge",
        "maxima_zeit_s": zeiten[maxima].tolist(),
        "maxima_amplitude": amplitude[maxima].tolist(),
        "abklingzeit_s": abklingzeit,
        "abklingstatus": "messbar" if abklingzeit is not None else
            "nicht messbar: keine zwei bleibend unter 1/e liegenden Maxima im Fenster",
        "verfahren": (
            "Gleichgewichtsabzug, linear interpolierte aufwaertsgerichtete "
            "Nulldurchgaenge; lokale Maxima des Betrags ohne Glaettung. "
            "Abklingen: erstes von mindestens zwei aufeinanderfolgenden "
            "Maxima unter Anfangsamplitude/e, ohne spaetere Ueberschreitung "
            "im aufgezeichneten Fenster. Kein Nachweis jenseits dieses Fensters."),
    }


def schwingungsauswertung(daten, gleichgewicht):
    from segelphysik.core.dynamik_6dof import quaternion_matrix

    rotationen = np.asarray([
        quaternion_matrix(q) for q in daten["zustaende"][:, 3:7]])
    roll = np.unwrap(np.arctan2(rotationen[:, 2, 1], rotationen[:, 2, 2]))
    # Der Solver darf denselben Gleichgewichtswinkel auf einem anderen 2*pi-Ast liefern.
    roll += math.tau * round((gleichgewicht["phi"] - roll[0]) / math.tau)
    nick = np.arctan2(
        -rotationen[:, 2, 0], np.hypot(rotationen[:, 2, 1], rotationen[:, 2, 2]))
    return {
        name: schwingungskennwerte(daten["zeit_s"], werte, lage)
        for name, werte, lage in (
            ("heben_m", daten["zustaende"][:, 2], gleichgewicht["z"]),
            ("rollen_rad", roll, gleichgewicht["phi"]),
            ("nicken_rad", nick, 0.))
    }


def dynamik(name, ziel, dauer_s=30.):
    from segelphysik.core import echtzeit_prozess

    konfig, physik, snapshot = koerper_laden(name)
    zustand, gleichgewicht = startzustand(snapshot, konfig, physik)
    anzahl = schrittanzahl(dauer_s, physik.dt_s)
    referenz = None
    schema_referenz = None
    zeitwerte = []
    for wiederholung in range(1, 4):
        echtzeit_prozess.initialisieren(snapshot, konfig.wasser_dichte(), physik)
        # Gleicher Warmup je Wiederholung, danach Modellkontext zuruecksetzen.
        warmup = echtzeit_prozess.schritte_berechnen(zustand, 10)
        if warmup[2] is not None:
            raise RuntimeError("Dynamikwarmup: " + warmup[2])
        echtzeit_prozess.initialisieren(snapshot, konfig.wasser_dichte(), physik)
        daten, schemas, zeiten = folge_berechnen(
            zustand, anzahl, physik.dt_s, echtzeit_prozess.schritte_berechnen)
        folge_pruefen(daten, schemas, dauer_s, physik.dt_s)
        if referenz is None:
            referenz, schema_referenz = daten, schemas
        else:
            vergleiche(schema_referenz, schemas)
            vergleiche(referenz, daten)
        zeitwerte.append(zeiten)
        print("%s: %g-s-Folge %d/3, %d Schritte exakt reproduzierbar"
              % (name, dauer_s, wiederholung, anzahl), flush=True)
    datei = ziel / (name + "_dynamik.npz")
    with datei.open("xb") as stream:
        np.savez_compressed(stream, **referenz)
    with np.load(datei, allow_pickle=False) as geladen:
        vergleiche(referenz, dict(geladen))
    return {
        "modell": name, "dauer_s": dauer_s, "dt_s": physik.dt_s, "schritte": anzahl,
        "schwingungskennwerte": schwingungsauswertung(referenz, gleichgewicht),
        "startzustand": asdict(zustand), "gleichgewicht": gleichgewicht,
        "eingabe_sha256": eingabe_hash(
            snapshot, physik, konfig.wasser_dichte(), "exakt_union", None),
        "daten": datei.name, "sha256": hashlib.sha256(datei.read_bytes()).hexdigest(),
        "wiederholungen": 3, "wiederholungen_exakt_identisch": True,
        "schemas": schema_referenz, "zeitmessungen": zeitwerte,
        "zustandsspalten": [
            "x", "y", "z", "qw", "qx", "qy", "qz", "u", "v", "w", "wx", "wy", "wz"],
        "kraftschema": {
            "vorspann": ["V_tauch", "K_x", "K_y", "K_z", "FA_x", "FA_y", "FA_z",
                         "F_x", "F_y", "F_z", "M_x", "M_y", "M_z", "bezug_x", "bezug_y", "bezug_z"],
            "je_beitrag": ["bezug_x", "bezug_y", "bezug_z",
                           "F_x", "F_y", "F_z", "M_x", "M_y", "M_z"],
            "offsets": "kraft_offsets[i]:kraft_offsets[i+1] gehoert zu Schritt i+1",
            "zeitzuordnung": (
                "KraftErgebnis ist der unveraenderte Rueckgabevertrag des Schritts; "
                "nicht als neue Kraftauswertung am Endzustand interpretieren."),
        },
        "vergleich": "Exakte Python-Reproduzierbarkeit; kein nativer Kandidatenvergleich.",
        "messhinweis": (
            "Gesamtzeit enthaelt Referenzerfassung/Allokation und Einzelbatchadapter; "
            "keine produktive Batchperformance. Workerzeiten separat."),
    }


def kalter_aufbau(name):
    start = time.perf_counter()
    konfig, physik, snapshot = koerper_laden(name)
    return {
        "dauer_s": time.perf_counter() - start,
        "eingabe_sha256": eingabe_hash(
            snapshot, physik, konfig.wasser_dichte(), "exakt_union", None),
    }


def prozessmessung(name):
    from segelphysik.core import echtzeit_prozess

    konfig, physik, snapshot = koerper_laden(name)
    zustand, _ = startzustand(snapshot, konfig, physik)
    args = (snapshot, konfig.wasser_dichte(), physik)
    serialisierung, payloads = messen(lambda: pickle.dumps(args))
    deserialisierung, _ = messen(lambda: pickle.loads(payloads[0]))
    kalt = []
    # Pro Messung ein neuer Interpreter; OS-Dateicaches werden nicht manipuliert.
    for _ in range(3):
        cmd = [sys.executable, str(Path(__file__).resolve()), "--kind-aufbau", name]
        ausgabe = subprocess.check_output(cmd, cwd=ROOT, text=True, encoding="utf-8")
        kalt.append(json.loads(ausgabe))
    start = time.perf_counter()
    with ProcessPoolExecutor(
            max_workers=1, mp_context=multiprocessing.get_context("spawn"),
            initializer=echtzeit_prozess.initialisieren, initargs=args) as pool:
        erstes = pool.submit(echtzeit_prozess.schritte_berechnen, zustand, 10).result(timeout=120)
        startkosten = time.perf_counter() - start
        if erstes[2] is not None:
            raise RuntimeError("Prozesswarmup: " + erstes[2])
        antworten = []
        roundtrips = []
        for _ in range(3):
            start = time.perf_counter()
            result = pool.submit(
                echtzeit_prozess.schritte_berechnen, zustand, 10).result(timeout=120)
            roundtrips.append(time.perf_counter() - start)
            if result[2] is not None:
                raise RuntimeError("Prozessfehler: " + result[2])
            antworten.append(result)
    echtzeit_prozess.initialisieren(*args)
    direkt = echtzeit_prozess.schritte_berechnen(zustand, 10)
    if direkt[2] is not None:
        raise RuntimeError("Direkte Referenz: " + direkt[2])
    from werkzeuge.migration_baseline import kraftdaten
    for antwort in antworten:
        vergleiche(direkt[0], antwort[0])
        vergleiche(kraftdaten(direkt[1]), kraftdaten(antwort[1]))
    antwortserialisierung, antwortpayload = messen(lambda: pickle.dumps(antworten[0][:3]))
    antwortdeserialisierung, _ = messen(lambda: pickle.loads(antwortpayload[0]))
    return {
        "modell": name, "schritte_pro_batch": 10,
        "snapshot_pickle_bytes": len(payloads[0]),
        "snapshot_serialisierung": serialisierung,
        "snapshot_deserialisierung": deserialisierung,
        "antwort_pickle_bytes": len(antwortpayload[0]),
        "antwort_serialisierung": antwortserialisierung,
        "antwort_deserialisierung": antwortdeserialisierung,
        "neuer_interpreter_aufbau": kalt,
        "prozessstart_bis_erster_batch_s": startkosten,
        "roundtrip": zeitstatistik(roundtrips),
        "worker": zeitstatistik([a[3] for a in antworten]),
        "roundtrip_minus_worker_s": [r - a[3] for r, a in zip(roundtrips, antworten)],
        "prozess_direkt_paritaet": "Zustaende und alle Wrenches exakt identisch",
        "hinweis": (
            "Differenz enthaelt Scheduling, Queue, Transport und Pickle, nicht reine IPC. "
            "Neue Interpreter sind kein Nachweis geleerter Betriebssystem-Dateicaches."),
    }


def beladungsfaelle(werte):
    faelle = []
    for faktor in (.8, 1., 1.2):
        for achse, delta in [(None, 0.)] + [
                (achse, delta) for achse in range(3) for delta in (-.2, .2)]:
            position = list(werte["position_rumpf_m"])
            if achse is not None:
                position[achse] += delta
            faelle.append({
                "masse_kg": werte["masse_kg"] * faktor,
                "position_rumpf_m": position,
            })
    return faelle


def aenderungsmessung(name):
    from segelphysik.core import echtzeit_prozess
    from segelphysik.core.dynamik_6dof import Zustand6DOF
    from segelphysik.core.fabriken import baue_modellpaket
    from segelphysik.core.konfig_lader import lade_konfig, lade_physik
    from segelphysik.core.modell_lader import lade_modellmanifest
    from segelphysik.core.segler_einstellungen import SeglerEinstellungen

    konfig = lade_konfig(ROOT / "konfigurationen")
    physik = lade_physik(ROOT / "konfigurationen")
    paket = ROOT / "code" / "modelle" / name
    manifest = lade_modellmanifest(paket, konfig.materialien_blocks)
    zustand = Zustand6DOF(
        position=(0., 0., -.14), geschwindigkeit_koerper=(.2, -.1, 0.),
        winkelgeschwindigkeit_koerper=(.01, -.01, .02))

    def aufzeichnen(fabrik):
        aufbau, koerperwerte = messen(fabrik)
        snapshots = [k.snapshot() for k in koerperwerte]
        for snapshot in snapshots[1:]:
            vergleiche(snapshots[0], snapshot)
        snapshot = snapshots[0]
        vorbereitung, _ = messen(lambda: echtzeit_prozess.initialisieren(
            snapshot, konfig.wasser_dichte(), physik))

        def batch():
            echtzeit_prozess._kraftfunktion.aktualisieren()
            ende, kraft, fehler, _ = echtzeit_prozess.schritte_berechnen(zustand, 10)
            if fehler is not None:
                raise RuntimeError("Aenderungsszenario %s: %s" % (name, fehler))
            return {"zustand": ende, "kraefte": kraftdaten(kraft)}

        batchzeiten, ergebnisse = messen(batch)
        for ergebnis in ergebnisse[1:]:
            vergleiche(ergebnisse[0], ergebnis)
        return snapshot, {
            "aufbau": aufbau, "worker_vorbereitung": vorbereitung,
            "workerbatch_ohne_ipc": batchzeiten,
            "snapshot": snapshot, "ergebnis": ergebnisse[0],
            "eingabe_sha256": eingabe_hash(
                snapshot, physik, konfig.wasser_dichte(), "exakt_union", None),
            "wiederholungen_exakt_identisch": True,
        }

    basis, basisdaten = aufzeichnen(lambda: baue_modellpaket(konfig, paket)[0])
    faelle = [{"art": "basis", **basisdaten}]
    punktmassen = []

    def sammeln(knoten):
        if knoten.masse_kg is not None:
            punktmassen.append(knoten)
        for kind in knoten.teile:
            sammeln(kind)

    sammeln(manifest.koerper)
    if len(punktmassen) > 1:
        raise ValueError("Mehrere Punktmassen brauchen getrennte bestehende Einstellungs-IDs")
    if punktmassen:
        punkt = punktmassen[0]
        originale_einstellungen = konfig.segler_einstellungen
        originalwerte = konfig.segler_einstellungen.werte(
            name, punkt.masse_kg, punkt.position_rumpf_m)
        with tempfile.TemporaryDirectory(prefix="segelphysik-m1-beladung-") as temp:
            konfig.segler_einstellungen = SeglerEinstellungen(Path(temp) / "segler.json")
            for werte in beladungsfaelle(originalwerte):
                konfig.segler_einstellungen.setzen(name, werte)
                _, daten = aufzeichnen(lambda: baue_modellpaket(konfig, paket)[0])
                faelle.append({"art": "beladung", "werte": werte, **daten})
            konfig.segler_einstellungen.setzen(name, originalwerte)
            rueckgestellt, daten = aufzeichnen(lambda: baue_modellpaket(konfig, paket)[0])
            vergleiche(basis, rueckgestellt)
            vergleiche(basisdaten["ergebnis"], daten["ergebnis"])
            faelle.append({"art": "beladung_rueckstellung", **daten})
        konfig.segler_einstellungen = originale_einstellungen

    for gelenk in basis.gelenkzustaende:
        for delta in (-math.radians(10.), math.radians(10.)):
            def fabrik(rueckstellung=False):
                koerper = baue_modellpaket(konfig, paket)[0]
                koerper.gelenkwinkel_setzen(
                    gelenk.knoten_id, gelenk.winkel_rad + delta)
                if rueckstellung:
                    koerper.gelenkwinkel_setzen(gelenk.knoten_id, gelenk.winkel_rad)
                return koerper

            _, daten = aufzeichnen(fabrik)
            faelle.append({
                "art": "gelenk", "knoten_id": gelenk.knoten_id,
                "winkel_rad": gelenk.winkel_rad + delta, **daten})
            rueckgestellt, daten = aufzeichnen(lambda: fabrik(rueckstellung=True))
            vergleiche(basis, replace(rueckgestellt, version=basis.version))
            vergleiche(basisdaten["ergebnis"], daten["ergebnis"])
            faelle.append({
                "art": "gelenk_rueckstellung", "knoten_id": gelenk.knoten_id,
                "versionszaehler": "Steigt bestimmungsgemaess; nur fuer Rueckstellvergleich ausgenommen.",
                **daten})
    return json.loads(json.dumps({
        "modell": name, "startzustand": asdict(zustand), "faelle": faelle,
        "beladungsabdeckung": "21 Kombinationen und Rueckstellung" if punktmassen else
            "Keine Punktmasse im bestehenden Modell; keine Beladung erfunden.",
        "gelenkanzahl": len(basis.gelenkzustaende),
        "hinweis": (
            "Drei Wiederholungen nach Warmup je Fall. Paket- und Nutzereinstellungen "
            "unveraendert; Beladung nur in temporaerer isolierter Einstellungsdatei. "
            "Aufbauzeit von Worker-Vorbereitung und Batch getrennt. "
            "Keine GUI-Latenzmessung und kein nativer Vergleich."),
    }, default=serialisieren, allow_nan=False))


def regressionsprofil(ziel, tests):
    import pytest

    ergebnisse = []

    class ErgebnisSammler:
        def pytest_runtest_logreport(self, report):
            if report.when == "call" or report.outcome != "passed":
                ergebnisse.append({
                    "test": report.nodeid, "phase": report.when,
                    "ergebnis": report.outcome, "dauer_s": report.duration,
                    "grund": str(report.longrepr) if report.longrepr else None,
                })

    code, profil = profilieren(
        lambda: pytest.main(["-q", "-rs", *tests], plugins=[ErgebnisSammler()]))
    schreiben(ziel / "regressionen.json", {
        "exitcode": int(code), "tests": ergebnisse, "profil": profil,
        "kommando": ["pytest", "-q", "-rs", *tests],
        "hinweis": "Instrumentierte Regression, keine Performancebaseline oder C++-Paritaet.",
    })
    if code != 0:
        raise RuntimeError("Profilierte Regression fehlgeschlagen: %s" % code)
    zeilen = funktionsmessungen([{
        "modell": "regressionsmatrix", "eingabe_sha256": "siehe Testfall und Referenzmanifest",
        "punkte": None, "dreiecke": None,
        "instrumentierte_profile": {"regressionen": profil},
    }])
    for eintrag in zeilen["eintraege"]:
        for beleg in eintrag["profilbelege"]:
            beleg["rohdatei"] = "regressionen.json"
    schreiben(ziel / "funktionsmessungen.json", zeilen)


def direkte_testprofile(ziel, tests):
    import pytest

    profile = {}
    ergebnisse = []
    quellhashes = {}

    class Sammler:
        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_call(self, item):
            pfad = Path(str(item.path))
            quellhashes[pfad.relative_to(ROOT).as_posix()] = texthash(pfad)
            original = item.obj
            profil = CallbackProfil()
            profil.messen = True

            @wraps(original)
            def aufrufen(*args, **kwargs):
                return profil.aufrufen(original, *args, **kwargs)

            item.obj = aufrufen
            try:
                return (yield)
            finally:
                item.obj = original
                if profil.aufrufe:
                    profile[item.nodeid] = profil.bericht()

        def pytest_runtest_logreport(self, report):
            if report.when == "call" or report.outcome != "passed":
                ergebnisse.append({
                    "test": report.nodeid, "phase": report.when,
                    "ergebnis": report.outcome,
                    "grund": str(report.longrepr) if report.longrepr else None,
                })

    code = pytest.main(["-q", "-rs", *tests], plugins=[Sammler()])
    schreiben(ziel / "testprofile.json", {
        "exitcode": int(code), "tests": ergebnisse, "testprofile": profile,
        "testquellen_sha256": quellhashes,
        "hinweis": (
            "Threadlokale Profile je tatsaechlicher Testfunktion. Fixtureaufbau "
            "und andere Threads sind nicht enthalten. Ein Aufruf in einem "
            "bestandenen Test ist kein automatischer Nachweis, dass genau dessen "
            "Rueckgabewert numerisch geprueft wurde. Kein Performancenachweis."),
    })
    if code != 0:
        raise RuntimeError("Direkte Referenztests fehlgeschlagen: " + str(code))


def stationaere_messung(name):
    from segelphysik.core.auftrieb import baue_kraftfunktion
    from segelphysik.core.fabriken import baue_summenkoerper
    from segelphysik.core.hydrodynamik import (
        HydrodynamikModell, hydrodynamik_teile_aus_koerper,
        hydrodynamik_testprofil, wasserlinienlaenge_m,
    )
    from segelphysik.core.konfig_lader import lade_konfig, lade_physik
    from segelphysik.core.kraftmodell import baue_kraftmodell
    from segelphysik.core.stationaer_hydrodynamik import (
        loese_stationaer, pruefe_stationaer_dynamisch,
    )
    from segelphysik.core.statisch_robust import loese_robust

    konfig = lade_konfig(ROOT / "konfigurationen")
    physik = lade_physik(ROOT / "konfigurationen")
    profil = hydrodynamik_testprofil(name, konfig.hydrodynamik_profile.get(name))
    if profil is None:
        raise ValueError("Kein bestehendes stationaeres Testprofil fuer " + name)
    koerper, _ = baue_summenkoerper(konfig, name)
    snapshot = koerper.snapshot()
    hydro = baue_kraftfunktion(
        snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2,
        pfad="exakt_union")
    hd = HydrodynamikModell.aus_koerper(
        snapshot, rho_kg_m3=konfig.wasser_dichte(),
        cd_volumenkoerper=profil.cd_volumenkoerper,
        fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
        fluidwinkelgeschwindigkeit=physik.fluidwinkelgeschwindigkeit,
        ruderwinkel_rad=math.radians(profil.ruderwinkel_grad))
    modell = baue_kraftmodell(
        hydro, physik, masse=snapshot.masse, g=physik.g_m_pro_s2, hydrodynamik=hd)
    azimut, elevation = math.radians(profil.azimut_grad), math.radians(profil.elevation_grad)
    modell.fremdkraft_setzen((
        (profil.kraft_betrag_N * math.cos(elevation) * math.cos(azimut),
         profil.kraft_betrag_N * math.cos(elevation) * math.sin(azimut),
         profil.kraft_betrag_N * math.sin(elevation)), profil.angriffspunkt_m))
    statisch = loese_robust(modell, snapshot.masse, g=physik.g_m_pro_s2)
    if name == "yacht1":
        laenge = wasserlinienlaenge_m(
            hydrodynamik_teile_aus_koerper(snapshot),
            z_m=statisch["z"], phi_rad=statisch["phi"])
        ref_v = .8 * 1.34 * .514444 * np.sqrt(laenge / .3048)
    else:
        laenge = float(np.ptp(np.concatenate(
            [p for p, _ in snapshot.blatt_meshes]), axis=0).max())
        ref_v = profil.referenzgeschwindigkeit_m_pro_s

    def solver():
        ergebnis = loese_stationaer(
            modell, charakteristische_kraft_N=profil.kraft_betrag_N,
            charakteristische_laenge_m=laenge, referenzgeschwindigkeit_m_s=ref_v,
            start=(ref_v, statisch["z"], 0., 0., statisch["phi"], 0.),
            ruderwinkel_rad=math.radians(profil.ruderwinkel_grad))
        daten = asdict(ergebnis)
        del daten["laufzeit_s"]
        return daten, ergebnis

    zeiten, resultate = messen(solver)
    for daten, _ in resultate[1:]:
        vergleiche(resultate[0][0], daten)

    def nachpruefung():
        ergebnis = pruefe_stationaer_dynamisch(
            modell, resultate[0][1].stufen[-1], masse_kg=snapshot.masse,
            traegheit_koerper=snapshot.traegheitstensor,
            charakteristische_laenge_m=laenge, dt_s=physik.dt_s,
            g_m_pro_s2=physik.g_m_pro_s2)
        if not ergebnis.bestanden:
            raise RuntimeError("Stationaere Dynamikpruefung: " + str(ergebnis.fehlergrund))
        daten = asdict(ergebnis)
        del daten["laufzeit_s"]
        return daten

    dynamikzeiten, pruefungen = messen(nachpruefung)
    for pruefung in pruefungen[1:]:
        vergleiche(pruefungen[0], pruefung)
    _, profilwerte = profilieren(solver)
    return {
        "modell": name, "testprofil": asdict(profil),
        "eingabe_sha256": eingabe_hash(
            snapshot, physik, konfig.wasser_dichte(), "exakt_union", None),
        "solver": zeiten, "ergebnis": resultate[0][0],
        "dynamikpruefung_10s": dynamikzeiten, "dynamikergebnis": pruefungen[0],
        "wiederholungen_exakt_identisch": True, "instrumentiertes_solverprofil": profilwerte,
        "hinweis": "Bestehendes Testprofil; keine unabhaengige hydrodynamische Modellvalidierung.",
    }


def gui_profil(ziel):
    from werkzeuge.benchmark_gui_live import benchmark

    for name in MODELLE:
        bericht, profil = profilieren(lambda: benchmark(
            name, 2., 15., measure_lifecycle=True, viewport_size=(640, 480)))
        pruefe_gui_lifecycle(bericht)
        schreiben(ziel / (name + ".json"), {
            "bericht": bericht, "profil": profil,
            "hinweis": "Kurzer instrumentierter Diagnoselauf; keine Live-Performancebaseline.",
        })
        referenzmanifest()
        print("GUI-Lifecycleprofil: " + name, flush=True)


def gui_callbacks(ziel):
    berichte = []
    for name in MODELLE:
        for schulung in (False, True):
            for wiederholung in range(1, 4):
                datei = ziel / ("%s_%s_%d.json" % (
                    name, "schulung" if schulung else "standard", wiederholung))
                kommando = [
                    sys.executable, str(ROOT / "werkzeuge" / "benchmark_gui_live.py"),
                    "--scene", name, "--warmup", "2", "--duration", "15",
                    "--measure-lifecycle", "--callback-profile",
                    "--viewport-width", "640", "--viewport-height", "480",
                    "--output", str(datei),
                ]
                if schulung:
                    kommando.append("--schulungsdarstellung")
                env = dict(os.environ, QT_QPA_PLATFORM="windows", PYTHONUTF8="1")
                prozess = subprocess.run(
                    kommando, cwd=ROOT, env=env, capture_output=True,
                    text=True, encoding="utf-8", timeout=180)
                if prozess.returncode != 0:
                    raise RuntimeError(
                        "GUI-Callbacklauf fehlgeschlagen:\n%s\n%s"
                        % (prozess.stdout, prozess.stderr))
                bericht = json.loads(datei.read_text(encoding="utf-8"))
                pruefe_gui_lifecycle(bericht)
                bewertung = profilbewertung(bericht["gui_callback_profil"])
                if not bewertung["zeitbewertung_gueltig"]:
                    raise ValueError("Inkonsistente Callbackprofilzeiten: " + datei.name)
                berichte.append({
                    "datei": datei.name, "sha256": texthash(datei),
                    "modell": name, "schulungsdarstellung": schulung,
                    "wiederholung": wiederholung,
                    "profilaufrufe": bericht["gui_callback_profil_aufrufe"],
                })
                referenzmanifest()
                print("GUI-Callbackprofil: " + datei.name, flush=True)
    schreiben(ziel / "auswertung.json", {
        "berichte": berichte,
        "hinweis": (
            "18 isolierte Callbackdiagnosen, keine 300-s-Performancebaseline "
            "und kein Ersatz fuer nicht erfasste GUI-/Instrumentfunktionen."),
    })


class VerzoegertesSignal:
    """Haelt genau ein wirklich berechnetes Ergebnis fuer einen definierten Race-Test."""

    def __init__(self, ziel):
        self.ziel = ziel
        self.bereit = threading.Event()
        self.freigabe = threading.Event()
        self.ergebnis = None
        self.fehler = None

    def emit(self, *args):
        self.ergebnis = args
        self.bereit.set()
        if not self.freigabe.wait(90.):
            self.fehler = "Ergebnisfreigabe fehlt nach 90 s"
            raise TimeoutError(self.fehler)
        self.ziel.emit(*args)


def warte_bis(app, bedingung, beschreibung, timeout_s=90.):
    ende = time.perf_counter() + timeout_s
    while not bedingung():
        if time.perf_counter() >= ende:
            raise TimeoutError(beschreibung)
        app.processEvents()
        time.sleep(.001)
    app.processEvents()


def gui_lastfall(name, aktion):
    if name not in MODELLE or aktion not in ("wechsel", "schliessen"):
        raise ValueError("Bekanntes Boot und Wechsel-/Schliessaktion erforderlich")
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui import hauptfenster as hauptfenster_mod
    from segelphysik.gui.app import _szene_einbetten, welt_laden
    from segelphysik.gui.baum import sichtbarkeit_setzen
    from werkzeuge.benchmark_gui_live import _fenster_schliessen

    app = QApplication.instance() or QApplication([])
    if app.platformName() != "windows":
        raise ValueError("Sichtbarer Lastfall erfordert Windows-QPA")
    welt = welt_laden()
    sichtbarkeit_setzen(welt, name)
    fenster = hauptfenster_mod.HauptFenster()
    original_run = hauptfenster_mod._EchtzeitAufgabe.run
    tor = [None]
    signale = []
    swaps = []
    fenster.baum_setzen(welt)
    try:
        _szene_einbetten(fenster)
        fenster._bruecke._plotter.setFixedSize(640, 480)
        fenster._bruecke._plotter.frameSwapped.connect(
            lambda: swaps.append(time.perf_counter()))
        fenster.show()
        warte_bis(app, lambda: name in fenster._statische_ergebnisse,
                  "Ausgangsstatik fehlt im Lastfall")
        fenster._echtzeit_signale.abgeschlossen.connect(
            lambda *args: signale.append(args))

        def run(aufgabe):
            if tor[0] is None and aufgabe.koerper_name == name:
                tor[0] = VerzoegertesSignal(aufgabe.signale.abgeschlossen)
                aufgabe.signale = SimpleNamespace(abgeschlossen=tor[0])
            return original_run(aufgabe)

        hauptfenster_mod._EchtzeitAufgabe.run = run
        fenster._btn_echtzeit.click()
        warte_bis(app, lambda: tor[0] is not None and tor[0].bereit.is_set(),
                  "Kein echtes berechnetes Echtzeitergebnis zum Verzoegern")
        ergebnis = tor[0].ergebnis
        if ergebnis[5] is not None:
            raise RuntimeError("Lastfall-Workerfehler: " + str(ergebnis[5]))
        generation_alt = ergebnis[0]
        if (not fenster._echtzeit_aufgabe_laeuft
                or generation_alt != fenster._echtzeit_generation):
            raise ValueError("Race-Test hat kein ausstehendes aktuelles Workerresultat")
        start = time.perf_counter()
        ziel = None
        if aktion == "wechsel":
            ziel = MODELLE[(MODELLE.index(name) + 1) % len(MODELLE)]
            sichtbarkeit_setzen(welt, ziel)
            fenster.baum.lade(welt)
            fenster._laufzeit_objekte_aktualisieren()
            if fenster._echtzeit_name != ziel:
                raise ValueError("Modellwechsel hat den neuen Echtzeitkoerper nicht aktiviert")
            # Nur die erneute Auftragserteilung bis zur Stale-Pruefung anhalten.
            fenster._echtzeit_timer.stop()
            fenster._echtzeit_render_timer.stop()
        else:
            fenster.close()
            if fenster.isVisible() or fenster._echtzeit_prozess_executor is not None:
                raise ValueError("Schliessen hat Fenster/Executor nicht freigegeben")
        aktionsdauer = time.perf_counter() - start
        generation_neu = fenster._echtzeit_generation
        if generation_neu <= generation_alt:
            raise ValueError("Lastaktion hat alte Auftraege nicht invalidiert")

        def zustand():
            return {
                "name": fenster._echtzeit_name,
                "zustand": fenster._echtzeit_zustand,
                "berechnet_s": fenster._echtzeit_berechnet_s,
                "kraftresultat": kraftdaten(fenster._echtzeit_kraefteresultat)
                    if fenster._echtzeit_kraefteresultat is not None else None,
            }

        vor_zustellung = zustand()
        tor[0].freigabe.set()
        warte_bis(app, lambda: bool(signale), "Altes Workerresultat wurde nicht zugestellt")
        if tor[0].fehler is not None:
            raise RuntimeError(tor[0].fehler)
        vergleiche(vor_zustellung, zustand())
        if fenster._echtzeit_aufgabe_laeuft:
            raise ValueError("Veralteter Auftrag bleibt nach Zustellung als laufend markiert")
        weitergerechnet = False
        if aktion == "wechsel":
            swaps_vorher = len(swaps)
            fenster._zeit_fortsetzen()
            warte_bis(
                app, lambda: fenster._echtzeit_berechnet_s > vor_zustellung["berechnet_s"]
                and len(swaps) > swaps_vorher,
                "Neues Modell rechnet oder praesentiert nach Wechsel nicht weiter")
            weitergerechnet = True
        return {
            "modell": name, "aktion": aktion, "zielmodell": ziel,
            "aktionsdauer_s": aktionsdauer, "qpa_plattform": app.platformName(),
            "viewport_px": list(fenster._bruecke._plotter.render_window.GetSize()),
            "generation_alt": generation_alt, "generation_neu": generation_neu,
            "altes_ergebnis_tatsaechlich_berechnet": True,
            "altes_ergebnis_nach_aktion_zugestellt": True,
            "veraltetes_ergebnis_ohne_zustandsaenderung_verworfen": True,
            "neues_modell_rechnet_und_praesentiert": weitergerechnet,
            "hinweis": (
                "Deterministischer Race-Test: echtes Workerresultat vor Signalzustellung "
                "gehalten, Wechsel/Schliessen ohne vorheriges Warten auf Worker. "
                "Beim Wechsel neue Timer nur fuer die Stale-Pruefung angehalten, "
                "danach echte weitere Physik und Qt-Swaps nachgewiesen. "
                "Aktionsdauer dieses instrumentierten Falls ist keine Performancebaseline."),
        }
    finally:
        if tor[0] is not None:
            tor[0].freigabe.set()
        hauptfenster_mod._EchtzeitAufgabe.run = original_run
        _fenster_schliessen(app, fenster, hauptfenster_mod)


def gui_lastserie(ziel):
    berichte = []
    for name in MODELLE:
        for aktion in ("wechsel", "schliessen"):
            for wiederholung in range(1, 4):
                datei = ziel / ("%s_%s_%d.json" % (name, aktion, wiederholung))
                prozess = subprocess.run([
                    sys.executable, str(Path(__file__).resolve()),
                    "--kind-gui-last", name, "--last-aktion", aktion,
                    "--output", str(datei),
                ], cwd=ROOT, env=dict(os.environ, QT_QPA_PLATFORM="windows", PYTHONUTF8="1"),
                    capture_output=True, text=True, encoding="utf-8", timeout=180)
                if prozess.returncode != 0:
                    raise RuntimeError("GUI-Lastfall fehlgeschlagen:\n%s\n%s"
                                       % (prozess.stdout, prozess.stderr))
                bericht = json.loads(datei.read_text(encoding="utf-8"))
                pruefe_gui_lastfall(bericht)
                berichte.append({"datei": datei.name, "sha256": texthash(datei)})
                referenzmanifest()
                print("GUI-Lastfall: " + datei.name, flush=True)
    schreiben(ziel / "auswertung.json", {"berichte": berichte})


def pruefe_gui_lastfall(bericht):
    if (bericht["qpa_plattform"] != "windows" or bericht["viewport_px"] != [640, 480]
            or bericht["modell"] not in MODELLE
            or bericht["aktion"] not in ("wechsel", "schliessen")
            or bericht["generation_neu"] <= bericht["generation_alt"]
            or not math.isfinite(bericht["aktionsdauer_s"])
            or bericht["aktionsdauer_s"] < 0
            or not all(bericht[key] is True for key in (
                "altes_ergebnis_tatsaechlich_berechnet",
                "altes_ergebnis_nach_aktion_zugestellt",
                "veraltetes_ergebnis_ohne_zustandsaenderung_verworfen"))
            or (bericht["aktion"] == "wechsel"
                and (bericht["neues_modell_rechnet_und_praesentiert"] is not True
                     or bericht["zielmodell"] not in MODELLE
                     or bericht["zielmodell"] == bericht["modell"]))):
        raise ValueError("Ungueltiger Wechsel-/Schliessnachweis unter Last")


def aktoren_snapshot(bruecke):
    import pyvista as pv

    ergebnis = {}
    aktoren = {
        "szene:" + name: actor
        for name, actor in bruecke._plotter.renderer.actors.items()}
    aktoren.update({"vordergrund:" + name: actor
                    for name, actor in bruecke._vg_actors.items()})
    for name, actor in sorted(aktoren.items()):
        if not actor.IsA("vtkActor"):
            continue
        mapper = actor.GetMapper()
        if mapper is None or not hasattr(mapper, "GetInput"):
            continue
        mesh = mapper.GetInput()
        if mesh is None or not mesh.IsA("vtkDataSet"):
            continue
        mesh = pv.wrap(mesh)
        digest = hashlib.sha256()
        for art in ("points", "faces", "lines", "verts", "strips"):
            if not hasattr(mesh, art):
                continue
            daten = np.asarray(getattr(mesh, art))
            if not np.isfinite(daten).all():
                raise ValueError("Nicht-endliche Actorgeometrie: " + name)
            digest.update(art.encode("ascii"))
            digest.update(str((daten.dtype.str, daten.shape)).encode("ascii"))
            digest.update(daten.tobytes())
        for art, daten in (("punktdaten", mesh.point_data), ("zelldaten", mesh.cell_data)):
            for key in sorted(daten):
                array = np.asarray(daten[key])
                if array.dtype.hasobject:
                    raise ValueError("Nicht binaer vergleichbare Actorattribute: " + name)
                digest.update((art + key).encode("utf-8"))
                digest.update(str((array.dtype.str, array.shape)).encode("ascii"))
                digest.update(array.tobytes())
        matrix = actor.GetMatrix()
        if matrix is None:
            raise ValueError("3D-Actor ohne Transformationsmatrix: " + name)
        prop = actor.GetProperty()
        ergebnis[name] = {
            "sichtbar": bool(actor.GetVisibility()),
            "geometrie_sha256": digest.hexdigest(),
            "punkte": mesh.n_points, "zellen": mesh.n_cells,
            "matrix": [[matrix.GetElement(i, j) for j in range(4)] for i in range(4)],
            "farbe": prop.GetColor(), "deckkraft": prop.GetOpacity(),
            "linienbreite": prop.GetLineWidth(), "glanz": prop.GetSpecular(),
            "darstellung": prop.GetRepresentation(),
        }
    if not ergebnis:
        raise ValueError("Keine echten Geometrieactoren erfasst")
    return ergebnis


def gui_variantenfall(name):
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui import hauptfenster as hauptfenster_mod
    from segelphysik.gui.app import _szene_einbetten, welt_laden
    from segelphysik.gui.baum import sichtbarkeit_setzen
    from segelphysik.core.overlays import LAYER_ALL
    from segelphysik.core.navigationsanzeigen import navigationswerte_ableiten
    from segelphysik.core.pfeilstil import Stil, standard_bereiche
    from werkzeuge.benchmark_gui_live import _fenster_schliessen
    from werkzeuge.migration_baseline import CallbackProfil

    app = QApplication.instance() or QApplication([])
    if app.platformName() != "windows":
        raise ValueError("Sichtbare Variantenpruefung erfordert Windows-QPA")
    welt = welt_laden()
    sichtbarkeit_setzen(welt, name)
    fenster = hauptfenster_mod.HauptFenster()
    fenster.baum_setzen(welt)
    try:
        _szene_einbetten(fenster)
        bruecke = fenster._bruecke
        bruecke._plotter.setFixedSize(640, 480)
        swaps = []
        bruecke._plotter.frameSwapped.connect(lambda: swaps.append(time.perf_counter()))
        fenster.show()
        warte_bis(app, lambda: name in fenster._statische_ergebnisse,
                  "Variantenpruefung hat kein statisches Ausgangsergebnis")
        fenster._btn_echtzeit.click()
        warte_bis(app, lambda: fenster._echtzeit_berechnet_s > 0.,
                  "Variantenpruefung hat kein echtes Echtzeitergebnis")
        fenster._zeit_pausieren()
        warte_bis(app, lambda: not fenster._echtzeit_aufgabe_laeuft,
                  "Ausstehender Worker vor deterministischer Variantenpruefung")
        fenster._navigations_timer.stop()
        zustand = fenster._echtzeit_zustand
        nav = fenster._navigationsfenster
        if nav is None:
            raise ValueError("Navigationsfenster fehlt")
        profil = CallbackProfil()
        profil.messen = True
        referenzen = None
        zeitwerte = []

        def zeichnen(funktion):
            vorher = len(swaps)
            start = time.perf_counter()
            profil.aufrufen(funktion)
            bruecke.render()
            warte_bis(app, lambda: len(swaps) > vorher, "Kein Qt-Swap fuer Variante", 10.)
            return time.perf_counter() - start

        for wiederholung in range(3):
            bruecke.stil_setzen(Stil())
            faelle = []
            zeiten = []
            for index in range(2 ** len(LAYER_ALL)):
                maske = index ^ (index >> 1)
                def layer_setzen():
                    for bit, layer in enumerate(LAYER_ALL):
                        wert = bool(maske & (1 << bit))
                        if bruecke.layer_ist_an(layer) != wert:
                            bruecke.layer_setzen(layer, wert)
                zeiten.append(zeichnen(layer_setzen))
                faelle.append({
                    "art": "layer", "maske": maske,
                    "layer": {layer: bruecke.layer_ist_an(layer) for layer in LAYER_ALL},
                    "actoren": aktoren_snapshot(bruecke),
                })
            for layer in LAYER_ALL:
                bruecke.layer_setzen(layer, True)
            for vordergrund in (False, True):
                for gestrichelt in (False, True):
                    bereiche = standard_bereiche()
                    for eintrag in bereiche.values():
                        if "vordergrund" in eintrag:
                            eintrag["vordergrund"] = vordergrund
                        if "gestrichelt" in eintrag:
                            eintrag["gestrichelt"] = gestrichelt
                    stil = Stil(lambda key: bereiche[key])
                    zeiten.append(zeichnen(lambda: bruecke.stil_setzen(stil)))
                    faelle.append({
                        "art": "stil", "vordergrund": vordergrund,
                        "gestrichelt": gestrichelt, "actoren": aktoren_snapshot(bruecke),
                    })
            nav.show()
            for maske in range(16):
                optionen = {
                    key: bool(maske & (1 << i))
                    for i, key in enumerate((
                        "titel_sichtbar", "titel_beschreibung_sichtbar",
                        "analog_sichtbar", "numerisch_sichtbar"))}
                for lage in ("normal", "fehler", "gefahr"):
                    q = (zustand.quaternion if lage == "normal" else
                         ((0., 0., 0., 0.) if lage == "fehler" else
                          (math.cos(math.radians(55)), math.sin(math.radians(55)), 0., 0.)))
                    werte = navigationswerte_ableiten(
                        q, .3, .4, segelwinkel_rad=.1)
                    start = time.perf_counter()
                    profil.aufrufen(nav.aktualisieren, werte, optionen, 2.)
                    app.processEvents()
                    zeiten.append(time.perf_counter() - start)
                    faelle.append({
                        "art": "instrumente", "maske": maske, "lage": lage,
                        "svg_sha256": [
                            hashlib.sha256(widget._rendered_bytes).hexdigest()
                            for widget in (*nav.widgets, nav.geschwindigkeit_widget)],
                    })
            nav.hide()
            if referenzen is None:
                referenzen = faelle
            else:
                vergleiche(referenzen, faelle)
            zeitwerte.append(zeiten)
        profil.messen = False
        profile = profil.bericht()
        if not profilbewertung(profile)["zeitbewertung_gueltig"]:
            raise ValueError("Inkonsistente Variantenprofilzeiten")
        return {
            "modell": name, "qpa_plattform": app.platformName(), "wiederholungen": 3,
            "wiederholungen_exakt_identisch": True,
            "viewport_px": list(bruecke._plotter.render_window.GetSize()),
            "faelle": referenzen, "instrumentierte_fallzeiten_s": zeitwerte,
            "profil": profile,
            "hinweis": (
                "256 Layerkombinationen, vier Standardstil-Kombinationen und "
                "16 Instrument-Sichtbarkeitskombinationen in Normal-/Fehler-/Gefahrenlage. "
                "Dreimal gleiche angehaltene Referenzpose; Actorgeometrie, Attribute, "
                "Transforms, Farben und SVG-Bytes exakt verglichen. Zeitwerte sind "
                "instrumentierte Diagnosen einschliesslich Qt-Swap-Warten, keine "
                "End-to-End-Performancebaseline. Keine Behauptung aller stetigen "
                "Farb-/Groessenwerte oder aller Kreuzprodukte von Stil und Layer."),
        }
    finally:
        _fenster_schliessen(app, fenster, hauptfenster_mod)


def gui_variantenserie(ziel):
    for name in MODELLE:
        datei = ziel / (name + ".json")
        prozess = subprocess.run([
            sys.executable, str(Path(__file__).resolve()),
            "--kind-gui-varianten", name, "--output", str(datei),
        ], cwd=ROOT, env=dict(os.environ, QT_QPA_PLATFORM="windows", PYTHONUTF8="1"),
            capture_output=True, text=True, encoding="utf-8", timeout=900)
        if prozess.returncode != 0:
            raise RuntimeError("GUI-Variantenfall fehlgeschlagen:\n%s\n%s"
                               % (prozess.stdout, prozess.stderr))
        referenzmanifest()
        print("GUI-Varianten: " + name, flush=True)


def pruefe_gui_lifecycle(bericht):
    if (not bericht["messlauf_gueltig"] or bericht["fehler"]
            or bericht["qpa_plattform"] != "windows"
            or bericht["renderzustand"]["fenstergroesse_px"] != [640, 480]):
        raise ValueError("Ungueltiger sichtbarer GUI-Lifecyclelauf")
    phasen = bericht["lebenszyklus"]
    if [p["phase"] for p in phasen] != [
            "pause", "fortsetzung", "wechsel_statisch", "wechsel_echtzeit"]:
        raise ValueError("GUI-Lifecyclephasen fehlen oder sind falsch geordnet")
    if (phasen[0]["modus"] != "pausiert"
            or phasen[2]["modus"] != "pausiert"
            or phasen[1]["modus"] not in ("normal", "ueberlast_beobachtung")
            or phasen[3]["modus"] not in ("normal", "ueberlast_beobachtung")):
        raise ValueError("GUI-Lifecycle hat falsche Modusuebergaenge")
    if phasen[0]["angefordert_s"] != phasen[1]["angefordert_s"]:
        raise ValueError("Simulationszeitanforderung laeuft waehrend Pause weiter")
    zeiten = [p["wandzeit_s"] for p in phasen]
    if not all(math.isfinite(t) and t >= 0 for t in zeiten) or zeiten != sorted(zeiten):
        raise ValueError("Ungueltige Lifecyclezeitfolge")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--art", choices=(
        "dynamik", "prozess", "regressionen", "stationaer", "gui-profil",
        "gui-kallback", "gui-last", "gui-varianten", "direktnachweise", "aenderungen"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tests", nargs="+")
    parser.add_argument("--dynamik-dauer", type=float)
    parser.add_argument("--kind-aufbau", choices=MODELLE, help=argparse.SUPPRESS)
    parser.add_argument("--kind-gui-last", choices=MODELLE, help=argparse.SUPPRESS)
    parser.add_argument("--kind-gui-varianten", choices=MODELLE, help=argparse.SUPPRESS)
    parser.add_argument("--last-aktion", choices=("wechsel", "schliessen"),
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.kind_aufbau:
        # Bestehende Plausibilitaetsmeldungen nicht ausblenden oder als JSON parsen.
        with redirect_stdout(sys.stderr):
            daten = kalter_aufbau(args.kind_aufbau)
        print(json.dumps(daten))
        return
    if args.kind_gui_last:
        if args.output is None or args.last_aktion is None:
            parser.error("--kind-gui-last braucht --last-aktion und --output")
        referenzmanifest()
        bericht = gui_lastfall(args.kind_gui_last, args.last_aktion)
        pruefe_gui_lastfall(bericht)
        referenzmanifest()
        schreiben(args.output, bericht)
        return
    if args.kind_gui_varianten:
        if args.output is None:
            parser.error("--kind-gui-varianten braucht --output")
        referenzmanifest()
        bericht = gui_variantenfall(args.kind_gui_varianten)
        referenzmanifest()
        schreiben(args.output, bericht)
        return
    if args.art is None or args.output is None:
        parser.error("--art und --output erforderlich")
    if args.tests and args.art not in ("regressionen", "direktnachweise"):
        parser.error("--tests nur bei --art regressionen oder direktnachweise")
    if args.dynamik_dauer is not None and (
            args.art != "dynamik" or not math.isfinite(args.dynamik_dauer)
            or args.dynamik_dauer <= 0):
        parser.error("--dynamik-dauer nur positiv und endlich bei --art dynamik")
    manifest = referenzmanifest()
    args.output.mkdir(parents=True, exist_ok=False)
    schreiben(args.output / "umgebung.json", {
        "referenzmanifest": manifest, "referenzcommit": REFERENZ,
        "umgebung": umgebung(), "build": buildinventar(), "kommando": sys.argv,
        "messwerkzeuge_sha256": {
            name: texthash(ROOT / "werkzeuge" / name)
            for name in ("migration_szenarien.py", "migration_baseline.py",
                         "migration_vergleich.py", "migration_inventar.py")},
    })
    if args.art == "regressionen":
        regressionsprofil(args.output, args.tests or ["tests"])
    elif args.art == "direktnachweise":
        direkte_testprofile(args.output, args.tests or [
            str(p) for p in sorted((ROOT / "tests").glob("test_*.py"))
            if p.name not in ("test_migration_v010.py", "test_migration_szenarien.py")])
    elif args.art == "gui-profil":
        gui_profil(args.output)
    elif args.art == "gui-kallback":
        gui_callbacks(args.output)
    elif args.art == "gui-last":
        gui_lastserie(args.output)
    elif args.art == "gui-varianten":
        gui_variantenserie(args.output)
    elif args.art == "stationaer":
        for name in ("yacht1", "platte"):
            schreiben(args.output / (name + ".json"), stationaere_messung(name))
            print("Stationaere Referenz: " + name, flush=True)
        schreiben(args.output / "modellabdeckung.json", {
            "optimist": "Kein konfiguriertes stationaeres Testprofil; keine Kraft erfinden.",
            "folkeboot": "Kein konfiguriertes stationaeres Testprofil; keine Kraft erfinden.",
            "yacht1": "Bestehendes Testprofil mit Wiederholungen gemessen.",
            "platte": "Bestehendes analytisch/generisches Testprofil gemessen.",
        })
    else:
        for name in MODELLE:
            if args.art == "dynamik":
                daten = dynamik(name, args.output, args.dynamik_dauer
                               if args.dynamik_dauer is not None else 30.)
            elif args.art == "aenderungen":
                daten = aenderungsmessung(name)
            else:
                daten = prozessmessung(name)
            schreiben(args.output / (name + ".json"), daten)
            print("Szenario abgeschlossen: %s/%s" % (args.art, name), flush=True)
    referenzmanifest()
    schreiben(args.output / "teillauf_abgeschlossen.json", {
        "art": args.art, "m1_freigegeben": False,
        "hinweis": "Nur die dokumentierten Szenarien sind nachgewiesen; kein Migrationsabschluss.",
    })


if __name__ == "__main__":
    main()
