"""Baut das Boot aus den Unity-OBJ-Teilen (code/modelle/).

Die Teile liegen im gemeinsamen Ursprung (Unity-Konvention: Y-up,
Laenge entlang z). Transformation ins Welt-Koordinatensystem
(rechtshaendig, z nach oben, x = Bug, y = Backbord):

    (x_welt, y_welt, z_welt) = (z_unity, x_unity, y_unity) * SKALA

Die Konstruktions-Wasserlinie des Modells liegt bei y_unity = 0 und wird
damit exakt zu z_welt = 0 -> das Boot liegt von selbst richtig im Wasser
(Rumpf kreuzt die Wasserlinie, Kiel/Bulb unter, Mast/Rigg ueber Wasser).
Kein Physik-Anteil (V3: rein kinematisch/statisch).
"""
from __future__ import annotations
import os
import numpy as np
from .massen import validiere_mesh_eingaben

MODELL_ORDNER = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "modelle"))
TEILE = ("rumpf", "kiel", "bulb", "mast", "boom", "grosssegel", "fock", "ruder")
SKALA = 0.25   # Modell ~16.9 lang -> ~4.2 m im 10-m-Becken


def lade_obj(pfad):
    """Kompatibilitätsadapter für die bisher unterstützten Yacht-OBJ-Dateien."""
    punkte, gesichter = [], []
    with open(pfad) as datei:
        for zeile in datei:
            tokens = zeile.split()
            if not tokens:
                continue
            if tokens[0] == "v":
                punkte.append([float(x) for x in tokens[1:4]])
            elif tokens[0] == "f":
                index = [int(token.split("/")[0]) - 1 for token in tokens[1:]]
                for position in range(1, len(index) - 1):
                    gesichter.append(
                        [index[0], index[position], index[position + 1]])
    try:
        punkte, gesichter, _ = validiere_mesh_eingaben(
            np.asarray(punkte, dtype=np.float64),
            np.asarray(gesichter, dtype=np.int64))
    except ValueError as fehler:
        raise ValueError(
            "Ungültiges OBJ-Mesh in %s: %s" % (pfad, fehler)) from fehler
    return punkte, gesichter


def baue_boot(skala=SKALA, teile=TEILE, ordner=MODELL_ORDNER):
    """Fuegt alle Teile zu EINEM Mesh zusammen (Welt-Koordinatensystem).

    rueckgabe: (punkte, dreiecke) - Wasserlinie liegt bei z = 0.
    """
    alle_p, alle_f, versatz = [], [], 0
    for teil in teile:
        p, f = baue_teil(teil, skala=skala, ordner=ordner)
        if len(p) == 0:
            continue
        alle_p.append(p)
        alle_f.append(f + versatz)
        versatz += len(p)
    return np.vstack(alle_p), np.vstack(alle_f)


def baue_teil(teil, skala=SKALA, ordner=MODELL_ORDNER):
    """Einzelnes Teil im Welt-Koordinatensystem (fuer getrennte Analyse)."""
    punkte, dreiecke = lade_obj(os.path.join(ordner, teil + ".obj"))
    return np.stack(
        [punkte[:, 2], punkte[:, 0], punkte[:, 1]], axis=1) * skala, dreiecke
