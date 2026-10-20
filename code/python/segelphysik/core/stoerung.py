"""Stoerung (Spec V4A rev C): zufaellige Stoerpose - rein, RNG injiziert.

St-1/St-2: Translation je Achse <= 2 m, Rotation je Weltachse <= +/-180 Grad,
unabhaengig gezogen; feste Weltachsen-Folge x -> y -> z (St-3).
St-6: projektion() liefert den Solver-Startwert (z, phi) - Rollwinkel aus
der x-Drehung, Trim/Nick verworfen (Theta-Wache D6/F3 bleibt intakt).
St-8: kontakt_start() findet vor Newton eine Lage mit Wasserkontakt UND
Teiltauchung (bei V_tauch = 0 oder Volltauchung waere die z-Spalte der
Jacobi singulaer). Scheitert die Suche: saubere SolverFehler-Meldung (Z5).
St-9 (rev C, Sichtprobe 12.10.): beste_loesung() waehlt unter mehreren
Solver-Starts die physikalisch tragende Loesung - nur stabile (GM > 0),
davon die tiefste Lage (minimale potentielle Energie m*g*z). Schein-
Gleichgewichte aus wilden Störlagen (z. B. "liegend") verlieren damit
gegen die aufrechte Schwimmlage.
"""
from __future__ import annotations

import math

import numpy as np

from .statisch import SolverFehler
from .rechenpfad import rechenpfad

MAX_TRANSLATION_M = 2.0
MAX_ROTATION_RAD = math.pi


def stoerung_ziehen(rng, max_translation=MAX_TRANSLATION_M,
                    max_rotation=MAX_ROTATION_RAD):
    """Zieht eine Stoerung (St-1/St-2); Rueckgabe Dict versatz/winkel."""
    versatz = tuple((rng.random() * 2.0 - 1.0) * float(max_translation)
                    for _ in range(3))
    winkel = tuple((rng.random() * 2.0 - 1.0) * float(max_rotation)
                   for _ in range(3))
    return {"versatz": versatz, "winkel": winkel}


def rotationsmatrix(winkel):
    """Rotationsmatrix: Weltachsen-Folge x -> y -> z (St-3)."""
    from .rechenpfad import rechenpfad

    if rechenpfad() == "cpp":
        from .stationaer_hydrodynamik import _rotation

        return _rotation(*(float(w) for w in winkel))
    rx, ry, rz = (float(w) for w in winkel)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    r_x = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    r_y = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    r_z = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return r_z @ r_y @ r_x


def stoss_pose(position_basis, stoerung):
    """Welt-Pose (R, Position) der Stoerpose aus der Basis-Lage (St-2).

    Jede neue Stoerung (Taste v, beliebig oft) startet von der Basis -
    keine Drift ueber mehrere Stoerungen.
    """
    if rechenpfad() == "cpp":
        from .native_backend import native_laden

        return native_laden().stoss_pose(
            np.asarray(position_basis, dtype=np.float64),
            np.asarray(stoerung["versatz"], dtype=np.float64),
            np.asarray(stoerung["winkel"], dtype=np.float64))
    basis = np.asarray(position_basis, dtype=float)
    return (rotationsmatrix(stoerung["winkel"]),
            basis + np.asarray(stoerung["versatz"], dtype=float))


def projektion(position, stoerung):
    """Solver-Startwert (z, phi) aus der Stoerpose (St-6, Option A)."""
    if rechenpfad() == "cpp":
        from .native_backend import native_laden

        return native_laden().projektion(
            np.asarray(position, dtype=np.float64),
            np.asarray(stoerung["winkel"], dtype=np.float64))
    z = float(np.asarray(position, dtype=float)[2])
    phi = float(stoerung["winkel"][0])
    return z, phi


def kontakt_start(funktion, z_start, phi, schritt=0.5, max_schritte=40):
    """St-8: Kontaktstart vor Newton (rein, deterministisch).

    V_tauch = 0 -> z senken bis Kontakt; Volltauchung -> z anheben bis
    V_tauch abnimmt. Ohne Erfolg: saubere SolverFehler-Meldung (Z5).
    """
    if rechenpfad() == "cpp":
        from .native_backend import native_laden, statikkontext_vorbereiten

        kontext = statikkontext_vorbereiten(funktion)
        if kontext is not None:
            status, z = kontext.kontakt_start(
                float(z_start), float(phi), float(schritt), int(max_schritte),
                native_laden().Abbruch())
            if status == 0:
                return z, float(phi)
            if status == 1:
                raise SolverFehler(
                    "St-8: voll getaucht, keine Oberflaeche innerhalb %.1f m"
                    % (max_schritte * schritt))
            raise SolverFehler(
                "St-8: kein Wasserkontakt innerhalb %.1f m" % (max_schritte * schritt))

    def v_tauch(z):
        return float(funktion((float(z), float(phi), 0.0)).V_tauch)

    z0 = float(z_start)
    v0 = v_tauch(z0)
    if v0 > 0.0:
        if v_tauch(z0 + schritt) < v0:
            return z0, float(phi)   # Teiltauchung, Oberflaeche in Reichweite
        z = z0
        for _ in range(int(max_schritte)):
            z += schritt
            v = v_tauch(z)
            if v < v0:
                if v > 0.0:
                    return z, float(phi)
                return z - 0.5 * schritt, float(phi)
        raise SolverFehler(
            "St-8: voll getaucht, keine Oberflaeche innerhalb %.1f m"
            % (max_schritte * schritt))
    z = z0
    for _ in range(int(max_schritte)):
        z -= schritt
        if v_tauch(z) > 0.0:
            return z, float(phi)
    raise SolverFehler(
        "St-8: kein Wasserkontakt innerhalb %.1f m" % (max_schritte * schritt))


def beste_loesung(loesungen):
    """St-9 (rev E): waehlt die tragende Loesung aus mehreren Ergebnissen.

    1. stabile Loesungen mit GM > 0 - davon die tiefste (min. m*g*z).
    2. stabile Loesungen ohne GM-Wert ("stabil": True, restaurierendes
       Moment direkt nachgewiesen, GM-Schaetzung an der Voxel-Treppe
       leer) - ebenfalls tiefste zuerst.  [rev E, schloss den Fall, der
       in der Sichtprobe 29.6 s rechnete und dann alles verwarf]
    3. roll-NEUTRALE Loesungen ("neutral": True, z. B. Kegel/Balken
       quer - GM = 0 ist dort Physik).
    4. Ohne beides: None.
    """
    if rechenpfad() == "cpp":
        from .native_backend import native_laden

        daten = []
        for loesung in loesungen:
            gm = loesung.get("gm")
            gm = None if gm is None else float(gm)
            stabil = loesung.get("stabil") is True
            neutral = loesung.get("neutral") is True
            aktiv = gm is not None and gm > 0. or stabil or neutral
            daten.append((float(loesung["z"]) if aktiv else None, gm, stabil, neutral))
        index = native_laden().beste_loesung(daten)
        return None if index is None else loesungen[index]
    stabile = [L for L in loesungen
               if L.get("gm") is not None and float(L["gm"]) > 0.0]
    if stabile:
        return min(stabile, key=lambda L: float(L["z"]))
    stabil_flag = [L for L in loesungen
                   if L.get("stabil") is True and L.get("neutral") is not True]
    if stabil_flag:
        return min(stabil_flag, key=lambda L: float(L["z"]))
    neutrale = [L for L in loesungen if L.get("neutral") is True]
    if neutrale:
        return min(neutrale, key=lambda L: float(L["z"]))
    return None
