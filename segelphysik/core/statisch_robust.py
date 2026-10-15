"""Robuster Solver-Wrapper (Spec V4A rev D): adaptives Newton + Sekanten-
Fallback fuer den VOXEL-Kern.

Anlass (Sichtprobe 12.10., Kegel): Der Voxel-Kern liefert V_tauch und M_x
als TREPPENFUNKTIONEN (stufig ueber z bzw. phi). Mit infinitesimalen
Differenzenschritten (1e-6) ist die Jacobi daraus fast ueberall singulaer
(dV/dz = 0 zwischen zwei Voxel-Schichten) - der im Umsetzungsplan
dokumentierte "Voxel-Treppen"-Risikofall, am echten Koerper materialisiert
(dort sogar mit NaN-Absturz des klassischen Solvers, siehe Test T1).

loese_robust() haelt die vertragliche Schnittstelle von statisch.loese()
ein (gleiche Signatur, gleiches Ergebnis-Dict, Erweiterungen siehe unten)
und erweitert sie:
  1. Adaptierte FD-Schritte: die Differenzenschritte wachsen gestuft
     (1e-6 -> 0.1 m bzw. 0.15 rad), bis eine Jacobi-Spalte nicht-null ist.
  2. Sekanten-Fallback je Freiheitsgrad, falls die Jacobi trotzdem
     singulaer bleibt: z per Sekante auf F_rest_z, phi per gedaempfter
     Sekante auf M_roll.
  3. Stagnations-Akzeptanz: auf einer Treppenfunktion kann ein Restwert
     unter der Stufenhoehe unerreichbar sein. Verbessert sich der
     Residuumsbetrag ueber 6 Auswertungen nicht mehr und ist klein
     gegenueber stagnation_anteil * m * g (Standard 5 % - entspricht
     wenigen cm Tiefgang), wird die Lage als Loesung akzeptiert und
     "stagnation": True gemeldet (Restkraft steht ehrlich im Protokoll).
  4. Roll-neutrale Koerper (Kreisquerschnitt auf der Seite, z. B. Kegel
     liegend): M_x identisch 0 -> keine Roll-Rueckstellung. Das ist
     Physik, kein Bug (GM = 0 wie bei einer rundum runden Spantonne).
     Der Solver meldet "neutral": True; beste_loesung() nimmt neutrale
     Loesungen nur, falls es keine stabile (GM > 0) gibt.
  5. Haertung: nicht-finite Newton-Schritte werden verworfen (Fallback);
     alle Flags sind echte Python-bools.

Hinweis: loese_robust setzt eine Lage MIT Wasserkontakt voraus - in der
Demo laeuft immer zuerst kontakt_start() (Spec St-8). Repo-statisch.py
bleibt UNVERAENDERT (Block-P-Tests unberuehrt).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from .statisch import G_NORM, STOERLEITER_GRAD, SolverFehler

_SCHRITTE_Z = (1e-6, 1e-3, 0.02, 0.1)
_SCHRITTE_PHI = (1e-6, 1e-3, 0.02, 0.15)
_STAG_WARTEN = 6
_STAG_ANTEIL = 0.05


def _residuum(funktion, z, phi, m, g):
    erg = funktion((float(z), float(phi), 0.0))
    residuum = np.array([float(erg.F_A.as_array()[2]) - m * g,
                         float(erg.M.as_array()[0])])
    if not np.all(np.isfinite(residuum)):
        raise SolverFehler(
            "Kraftfunktion lieferte nicht-endliche Restkraefte oder Momente",
            status="ungueltige_rechenergebnisse",
            diagnose={"z": float(z), "phi": float(phi)})
    return residuum


def _fd_spalte(funktion, z, phi, m, g, index, schritte):
    """FD-Spalte der Jacobi mit gestuft wachsendem Schritt (Treppen!)."""
    r0 = _residuum(funktion, z, phi, m, g)
    for h in schritte:
        args = [z, phi]
        args[index] = args[index] + h
        r1 = _residuum(funktion, args[0], args[1], m, g)
        d = (r1 - r0) / h
        if np.linalg.norm(d) > 0.0:
            return d
    return np.zeros(2)


def _sekante_1d(f, x0, delta=0.05, max_iter=40, grenze=2.0):
    """Sekantenloeser f(x) = 0 ab x0. None, wenn keine Verbesserung."""
    f0 = f(x0)
    if not math.isfinite(f0):
        return None
    if abs(f0) < 1e-12:
        return x0
    x1 = x0 + delta
    f1 = f(x1)
    for _ in range(int(max_iter)):
        if not math.isfinite(f1) or abs(f1 - f0) < 1e-15:
            delta *= 2.0
            if delta > grenze:
                break
            x1 = x0 + delta
            f1 = f(x1)
            continue
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        schritt = x2 - x1
        if abs(schritt) > grenze:
            schritt = math.copysign(grenze, schritt)
            x2 = x1 + schritt
        f2 = f(x2)
        x0, f0, x1, f1 = x1, f1, x2, f2
        if abs(f1) < 1e-9 or abs(x1 - x0) < 1e-12:
            return x1
    return x1 if (math.isfinite(f1) and abs(f1) < abs(f0)) else None


def _dmdphi(funktion, z, phi, m, g):
    for h in (1e-4, 1e-3, 0.02):
        Mp = _residuum(funktion, z, phi + h, m, g)[1]
        Mm = _residuum(funktion, z, phi - h, m, g)[1]
        d = (Mp - Mm) / (2.0 * h)
        if abs(d) > 0.0:
            return d
    return 0.0


def _newton_versuch(funktion, start, m, g, tol, max_iter, stag_anteil):
    """Ein Newton-Versuch. Rueckgabe: (lage, r, iterationen, stagnation)
    plus Abbruchursache; der Aufrufer entscheidet ueber einen Restart."""
    z, phi = float(start[0]), float(start[1])
    r = _residuum(funktion, z, phi, m, g)
    best_n = float(np.linalg.norm(r))
    best = (z, phi, r)
    schlechte = 0
    for it in range(1, int(max_iter) + 1):
        if best_n < tol:
            return (best[0], best[1]), best[2], it, False, "konvergiert"
        J = np.column_stack([
            _fd_spalte(funktion, z, phi, m, g, 0, _SCHRITTE_Z),
            _fd_spalte(funktion, z, phi, m, g, 1, _SCHRITTE_PHI)])
        schritt = None
        if (np.linalg.norm(J[:, 0]) > 0.0 or np.linalg.norm(J[:, 1]) > 0.0):
            try:
                schritt = np.linalg.solve(J, -r)
            except np.linalg.LinAlgError:
                schritt = None
        if schritt is None or not np.all(np.isfinite(schritt)):
            # Koordinaten-Fallback (Treppen-/Neutral-Fall)
            z_neu = _sekante_1d(
                lambda zz: _residuum(funktion, zz, phi, m, g)[0], z)
            if z_neu is not None:
                z = float(z_neu)
            r_tmp = _residuum(funktion, z, phi, m, g)
            if abs(r_tmp[1]) > 1e-12:
                phi_neu = _sekante_1d(
                    lambda pp: _residuum(funktion, z, pp, m, g)[1],
                    phi, delta=0.1, grenze=0.5)
                if phi_neu is not None:
                    phi = float(phi_neu)
            r = _residuum(funktion, z, phi, m, g)
        else:
            if abs(schritt[1]) > 0.35:
                schritt *= 0.35 / abs(schritt[1])
            if abs(schritt[0]) > 0.5:
                schritt *= 0.5 / abs(schritt[0])
            z += float(schritt[0])
            phi += float(schritt[1])
            r = _residuum(funktion, z, phi, m, g)
        if not np.all(np.isfinite(r)):
            r = _residuum(funktion, best[0], best[1], m, g)
            z, phi = best[0], best[1]
        n = float(np.linalg.norm(r))
        if n < best_n * (1.0 - 0.01):
            best_n, best, schlechte = n, (z, phi, r), 0
        else:
            if n < best_n:
                best_n, best = n, (z, phi, r)
            schlechte += 1
            if schlechte >= _STAG_WARTEN:
                grenze = max(tol, stag_anteil * m * g)
                if best_n <= grenze:
                    return (best[0], best[1]), best[2], it, True, "stagnation"
                return (best[0], best[1]), best[2], it, False, "stagnation"
    grenze = max(tol, stag_anteil * m * g)
    if best_n <= grenze:
        return (best[0], best[1]), best[2], int(max_iter), True, "stagnation"
    return (best[0], best[1]), best[2], int(max_iter), False, "budget_erschoepft"


def _diagnose(lage, r, iterationen, restarts, stagnation, stabil=None):
    werte = {
        "z": float(lage[0]),
        "phi": float(lage[1]),
        "restkraft": float(abs(r[0])),
        "restmoment": float(abs(r[1])),
        "iterationen": int(iterationen),
        "restarts": int(restarts),
        "stagnation": bool(stagnation),
    }
    if stabil is not None:
        werte["stabil"] = bool(stabil)
    return werte


def loese_robust(funktion, m, g=G_NORM, start=(0.0, 0.0), tol=1e-8,
                 max_iter=60, stoerleiter=STOERLEITER_GRAD,
                 stagnation_anteil=_STAG_ANTEIL, neutral_toleranz=1e-9):
    """Vertraglich kompatibel zu statisch.loese(), zusaetzlich im Dict:
    "stagnation": bool und "neutral": bool (Roll neutral, gm dann None).

    neutral_toleranz: |dM/dphi| <= neutral_toleranz * m*g gilt als neutral.
    Fuer geometrisch erkannte Kugeln wird sie gelockert (Netzrauschen)."""
    leiter = tuple(float(x) for x in stoerleiter)
    aktuelle = (float(start[0]), float(start[1]))
    restarts = 0
    @lru_cache(maxsize=512)
    def ausgewertet(lage):
        return funktion(lage)

    def cache_kennzahlen():
        info = ausgewertet.cache_info()
        return {
            "kraftauswertungen": info.misses,
            "wiederverwendete_kraftwerte": info.hits,
        }

    while True:
        ergebnis = _newton_versuch(ausgewertet, aktuelle, m, g, tol,
                                   max_iter, stagnation_anteil)
        lage, r, it, stag, abbruch = ergebnis
        diagnose = _diagnose(lage, r, it, restarts, stag)
        if abbruch == "konvergiert" or (abbruch == "stagnation" and stag):
            dM = _dmdphi(ausgewertet, lage[0], lage[1], m, g)
            neutral = bool(abs(dM) <= neutral_toleranz * max(m * g, 1.0)
                           and abs(float(r[1])) <= 1e-6 * max(m * g, 1.0))
            basis = {**diagnose, "neutral": neutral,
                     # rev E: dM<0 ist der direkte Stabilitaetsnachweis
                     # (restaurierendes Moment). GM-Schaetzung kann an der
                     # Voxel-Treppe leer bleiben - dann traegt dieses Flag.
                     "stabil": bool(dM < 0.0)}
            basis.update(cache_kennzahlen())
            if neutral:
                basis["gm"] = None
                return basis
            if dM < 0.0:
                h_gm = None
                for h in (1e-4, 1e-3, 0.02):
                    Mp = _residuum(
                        ausgewertet, lage[0], h, m, g)[1]
                    Mm = _residuum(
                        ausgewertet, lage[0], -h, m, g)[1]
                    if abs(Mp - Mm) > 0.0:
                        h_gm = -(Mp - Mm) / (2.0 * h) / (m * g)
                        break
                basis["gm"] = h_gm
                return basis
            if restarts >= len(leiter):
                raise SolverFehler(
                    "Stoerleiter erschoepft (%d Stufen), lage=%r"
                    % (len(leiter), lage), status="instabile_lage",
                    diagnose=basis)
            aktuelle = (lage[0], lage[1] + math.radians(leiter[restarts]))
            restarts += 1
        else:
            if restarts >= len(leiter):
                diagnose["restarts"] = restarts
                diagnose.update(cache_kennzahlen())
                raise SolverFehler(
                    "Keine Konvergenz, Stoerleiter erschoepft (%d Stufen)"
                    % len(leiter), status=abbruch, diagnose=diagnose)
            aktuelle = (aktuelle[0],
                        aktuelle[1] + math.radians(leiter[restarts]))
            restarts += 1
