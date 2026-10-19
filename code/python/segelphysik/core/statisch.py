"""Statischer Solver (P5c Phase B, Umsetzungsplan V5 rev 9 §4).

Newton ueber (z, phi) mit Residuen F23: z-Komponente der Restkraft
(F_A - F_G) und Rollachsenkomponente des Moments (D11: Rollachse = x).
Numerische Jacobi-Matrix, gedämpfte Schritte.

D9 Stabilitätsauswahl: Nach jeder Konvergenz wird dM/dphi an der Lösung
geprüft; instabil (dM/dphi >= 0) -> verwerfen und mit eskalierender
Störung (5/15/30/44 Grad, erweiterbar) von der VERWORFENEN Lösung aus
neu starten (rev 7). Erschöpft die Leiter: saubere Meldung.

GM nur aufrecht definiert (F18): GM = -(dM/dphi)/(m*g) am Gleichgewicht
- dort exakt, weil m*g = rho_W*g*V.
"""
from __future__ import annotations

import numpy as np

from .auftrieb import G_NORM


class SolverFehler(RuntimeError):
    """Solver konnte keine stabile Gleichgewichtslage finden."""

    def __init__(self, nachricht, *, status="fehler", diagnose=None):
        super().__init__(nachricht)
        self.status = status
        self.diagnose = dict(diagnose or {})


STOERLEITER_GRAD = (5.0, 15.0, 30.0, 44.0)


def _residuum(funktion, lage, m, g):
    """Residuen nach F23: [Restkraft_z, Rollachsenmoment]."""
    erg = funktion(lage, 0.0, 0.0)
    F_rest_z = (
        erg.F_gesamt.as_array()[2]
        if getattr(erg, "schwerkraft_beruecksichtigt", False)
        else erg.F_A.as_array()[2] - m * g)
    M_roll = erg.M.as_array()[0]
    return np.array([F_rest_z, M_roll]), erg


def _dmdphi(funktion, lage, m, g, h=1e-6):
    """Rollachsenmoment bei phi+h (z fest) - D9-Kriterium."""
    _, erg = _residuum(funktion, (lage[0], lage[1] + h, 0.0), m, g)
    return float(erg.M.as_array()[0])


def loese(funktion, m, g=G_NORM, start=(0.0, 0.0), tol=1e-8,
          max_iter=50, stoerleiter=STOERLEITER_GRAD):
    """Findet die STABILE Gleichgewichtslage (z, phi).

    Rueckgabe: dict(z, phi, iterationen, restarts, restkraft, restmoment, gm)
    Wirft SolverFehler bei Nichtkonvergenz oder erschöpfter Leiter.
    """
    leiter = tuple(float(x) for x in stoerleiter)
    aktuelle = tuple(float(x) for x in start)
    restarts = 0

    while True:
        lage = (aktuelle[0], aktuelle[1], 0.0)
        konvergiert = False
        r = None
        it = 0
        for it in range(1, max_iter + 1):
            r, erg = _residuum(funktion, lage, m, g)
            if abs(r[0]) < tol and abs(r[1]) < tol:
                konvergiert = True
                break
            J = np.zeros((2, 2))
            hz = max(1e-6, abs(lage[0]) * 1e-6)
            rz_p, _ = _residuum(funktion, (lage[0] + hz, lage[1], 0.0), m, g)
            rz_p2, _ = _residuum(funktion, (lage[0], lage[1] + 1e-6, 0.0), m, g)
            J[:, 0] = (rz_p - r) / hz
            J[:, 1] = (rz_p2 - r) / 1e-6
            try:
                schritt = np.linalg.solve(J, -r)
            except np.linalg.LinAlgError:
                raise SolverFehler("Jacobi singulär bei %r" % (lage,))
            if abs(schritt[1]) > 0.35:
                schritt *= 0.35 / abs(schritt[1])
            if abs(schritt[0]) > 0.5:
                schritt *= 0.5 / abs(schritt[0])
            lage = (lage[0] + schritt[0], lage[1] + schritt[1], 0.0)

        if not konvergiert:
            raise SolverFehler(
                "Keine Konvergenz nach %d Iterationen (lage=%r)"
                % (max_iter, lage))

        dM = _dmdphi(funktion, lage, m, g)
        if dM < 0.0:
            gm = _metazentrische_hoehe(funktion, lage, m, g)
            return {"z": lage[0], "phi": lage[1], "iterationen": it,
                    "restarts": restarts,
                    "restkraft": float(abs(r[0])),
                    "restmoment": float(abs(r[1])), "gm": gm}

        if restarts >= len(leiter):
            raise SolverFehler(
                "Störleiter erschöpft (%d Stufen); letzte (instabile) "
                "Lösung: z=%.6f phi=%.6f rad" % (len(leiter), lage[0], lage[1]))
        stoerung = np.radians(leiter[restarts])
        aktuelle = (lage[0], lage[1] + stoerung)
        restarts += 1


def _metazentrische_hoehe(funktion, lage, m, g):
    """GM nur aufrecht (F18): numerisch -(dM/dphi)/(m*g) bei phi=0."""
    if abs(lage[1]) > 1e-6:
        return None
    h = 1e-4
    Mp, _ = _residuum(funktion, (lage[0], h, 0.0), m, g)
    Mm, _ = _residuum(funktion, (lage[0], -h, 0.0), m, g)
    return -(Mp[1] - Mm[1]) / (2.0 * h) / (m * g)
