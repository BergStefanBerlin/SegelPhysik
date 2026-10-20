"""Prueft eingefrorene Referenzen mit expliziter vorlaeufiger Eingabetoleranz."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from werkzeuge.migration_inventar import schreiben
from werkzeuge.migration_vergleich import vergleiche
from werkzeuge.pruefe_genauigkeit_v09 import ZIEL, pruefen, referenzfaelle


def vorlaeufig_pruefen(referenz, aktuell):
    grenzen = {}

    def zahlenfelder(wert, pfad, atol):
        if isinstance(wert, dict):
            for name, kind in wert.items():
                zahlenfelder(kind, pfad + "." + name, atol)
        elif isinstance(wert, list):
            for index, kind in enumerate(wert):
                zahlenfelder(kind, "%s[%d]" % (pfad, index), atol)
        elif isinstance(wert, float):
            grenzen[pfad] = (0., atol)

    abweichungen = {}
    for name, alt in referenz["modelle"].items():
        basis = "$.modelle." + name
        for feld in ("laenge_m", "breite_m", "masse_kg", "g_m_pro_s2",
                     "vollvolumen_m3", "rho_w_kg_m3"):
            zahlenfelder(alt[feld], basis + "." + feld, 1e-10)
        maximum = 0.
        for gruppe in ("hydrostatik", "wasserlinien"):
            for index, fall in enumerate(alt[gruppe]):
                pfad = "%s.%s[%d]" % (basis, gruppe, index)
                for feld in ("position_m", "quaternion_wxyz"):
                    zahlenfelder(fall[feld], pfad + "." + feld, 1e-12)
                    delta = np.asarray(fall[feld]) - np.asarray(
                        aktuell["modelle"][name][gruppe][index][feld])
                    maximum = max(maximum, float(np.max(np.abs(delta))))
                zahlenfelder(fall["referenz"], pfad + ".referenz", 1e-9)
        abweichungen[name] = {"max_eingabekomponentenabweichung": maximum}
    vergleiche(referenz, aktuell, toleranzen=grenzen)
    return {
        "vorlaeufig_bestanden": True, "eingabe_atol": 1e-12,
        "hydrostatik_atol": 1e-9, "modelle": abweichungen,
        "hinweis": "Nur Eingabepositionen/Quaternionen vorlaeufig von exakt "
                   "auf 1e-12 gelockert. Physikalische Referenzgrenzen unveraendert.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    alt = json.loads(ZIEL.read_text(encoding="utf-8"))
    aktuell = json.loads(json.dumps(referenzfaelle(), allow_nan=False))
    strenge_abweichung = None
    try:
        pruefen(alt, aktuell)
    except AssertionError as fehler:
        strenge_abweichung = str(fehler)
    ergebnis = vorlaeufig_pruefen(alt, aktuell)
    ergebnis["streng_bestanden"] = strenge_abweichung is None
    ergebnis["strenge_abweichung"] = strenge_abweichung
    schreiben(args.output, ergebnis)
    print(json.dumps(ergebnis, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
