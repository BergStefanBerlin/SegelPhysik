"""Strikte Vergleichs- und Messhelfer fuer die C++-Migration (M1).

Toleranzen sind pro Zahlenfeld vorzugeben; ohne Vorgabe gilt exakte
Gleichheit. Fehlende Beitraege, Frames und nicht-endliche Werte sind Fehler.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
import math
import statistics
import time

import numpy as np


def vergleiche(referenz, kandidat, *, toleranzen=None):
    grenzen = {} if toleranzen is None else toleranzen
    verwendet = set()
    for pfad, grenze in grenzen.items():
        if (not isinstance(pfad, str) or not isinstance(grenze, (tuple, list))
                or len(grenze) != 2
                or any(isinstance(w, bool) or not isinstance(w, (int, float))
                       or not math.isfinite(w) or w < 0
                       for w in grenze)):
            raise ValueError("Toleranzen brauchen Feldpfad und endliches (rtol, atol)")

    def pruefen(a, b, pfad):
        if is_dataclass(a) and not isinstance(a, type):
            if not is_dataclass(b) or type(a) is not type(b):
                raise AssertionError("%s: Datentyp veraendert" % pfad)
            a, b = asdict(a), asdict(b)
        if isinstance(a, dict):
            if not isinstance(b, dict) or a.keys() != b.keys():
                raise AssertionError("%s: Felder/Beitraege veraendert" % pfad)
            for key in a:
                pruefen(a[key], b[key], pfad + "." + str(key))
        elif isinstance(a, (tuple, list)):
            if type(a) is not type(b) or len(a) != len(b):
                raise AssertionError("%s: Sequenzstruktur veraendert" % pfad)
            for index, (links, rechts) in enumerate(zip(a, b)):
                pruefen(links, rechts, "%s[%d]" % (pfad, index))
        elif isinstance(a, (np.ndarray, int, float, np.number)) and not isinstance(
                a, (bool, np.bool_)):
            links, rechts = np.asarray(a), np.asarray(b)
            if (links.dtype.kind not in "iuf" or rechts.dtype.kind not in "iuf"
                    or links.shape != rechts.shape
                    or links.dtype != rechts.dtype):
                raise AssertionError("%s: Zahlenform/Datentyp veraendert" % pfad)
            if not np.isfinite(links).all() or not np.isfinite(rechts).all():
                raise AssertionError("%s: Nicht-endlicher Wert" % pfad)
            if pfad in grenzen:
                verwendet.add(pfad)
            rtol, atol = grenzen.get(pfad, (0.0, 0.0))
            if links.dtype.kind in "iu" and (rtol or atol):
                raise ValueError("%s: Indizes/Zaehler brauchen exakte Gleichheit" % pfad)
            if rtol == 0 and atol == 0:
                np.testing.assert_array_equal(rechts, links, err_msg=pfad)
            else:
                np.testing.assert_allclose(
                    rechts, links, rtol=rtol, atol=atol, equal_nan=False,
                    err_msg=pfad)
        elif type(a) is not type(b) or a != b:
            raise AssertionError("%s: Wert/Frame veraendert" % pfad)

    pruefen(referenz, kandidat, "$")
    if grenzen.keys() != verwendet:
        raise ValueError("Unbenutzte Toleranzpfade: %s" % sorted(grenzen.keys() - verwendet))


def zeitstatistik(werte):
    if (not werte or any(isinstance(w, bool) or not math.isfinite(w) or w <= 0
                         for w in werte)):
        raise ValueError("Positive endliche Zeitrohwerte erforderlich")
    return {
        "anzahl": len(werte),
        "median_s": statistics.median(werte),
        "p95_s": float(np.percentile(werte, 95)),
        "minimum_s": min(werte), "maximum_s": max(werte),
        "spannweite_s": max(werte) - min(werte),
        "standardabweichung_s": statistics.pstdev(werte),
        "rohwerte_s": list(werte),
    }


def messen(funktion, *, wiederholungen=3, warmups=1):
    for name, wert, minimum in (
            ("Wiederholungen", wiederholungen, 3), ("Warmups", warmups, 0)):
        if isinstance(wert, bool) or not isinstance(wert, int) or wert < minimum:
            raise ValueError("%s muss ganzzahlig und >= %d sein" % (name, minimum))
    for _ in range(warmups):
        funktion()
    werte = []
    ergebnisse = []
    for _ in range(wiederholungen):
        start = time.perf_counter()
        ergebnisse.append(funktion())
        werte.append(time.perf_counter() - start)
    return zeitstatistik(werte), ergebnisse


def performancevergleich(python_s, cpp_s):
    vorher, nachher = zeitstatistik(python_s), zeitstatistik(cpp_s)
    if min(vorher["anzahl"], nachher["anzahl"]) < 3:
        raise ValueError("Mindestens drei Wiederholungen pro Stand erforderlich")
    differenz = vorher["median_s"] - nachher["median_s"]
    return {
        "python": vorher, "cpp": nachher,
        "ersparnis_s": differenz,
        "ersparnis_prozent": 100 * differenz / vorher["median_s"],
        "beschleunigungsfaktor": vorher["median_s"] / nachher["median_s"],
        "vorteil_groesser_als_spannweiten": differenz > max(
            vorher["spannweite_s"], nachher["spannweite_s"]),
        "hinweis": "Zeitvergleich allein ist keine Paritaets-/Produktivfreigabe.",
    }
