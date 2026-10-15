"""Statustext der statischen Darstellung (Overlay unten links).

Reine Logik ohne Qt/VTK: ordnet Solver-Ergebnis bzw. -Fehler einem Kurztext
und einer Schwere zu. Schweren: "ok" (gruen), "hinweis" (gelb),
"problem" (rot), "info" (grau).
"""
from __future__ import annotations

import numpy as np

SCHWEREN = ("ok", "hinweis", "problem", "info")

BERECHNUNG_LAEUFT = ("Berechnung läuft …", "info")
KEIN_HAUPTKOERPER = ("Kein Hauptkörper ausgewählt", "info")
KOERPER_FEHLT = ("Körper nicht in der 3D-Ansicht", "info")

_KANDIDATEN_STATUS = ("stagnation", "budget_erschoepft")


def ist_rotationssymmetrisch(traegheitstensor, toleranz=1e-3):
    """True, wenn alle drei Hauptträgheitsmomente (nahezu) gleich sind."""
    if traegheitstensor is None:
        return False
    try:
        werte = np.linalg.eigvalsh(np.asarray(traegheitstensor, float))
    except (ValueError, np.linalg.LinAlgError):
        return False
    if not np.all(np.isfinite(werte)) or werte[-1] <= 0.0:
        return False
    return bool((werte[-1] - werte[0]) <= toleranz * werte[-1])


def status_aus_ergebnis(ergebnis, rotationssymmetrisch=False):
    """Status für ein konvergiertes Solver-Ergebnis."""
    if ergebnis.get("neutral"):
        if rotationssymmetrisch:
            return "rotationsneutral (Kugel)", "ok"
        return "rollneutral (Zylinder)", "ok"
    if ergebnis.get("stagnation"):
        return "stabile Näherung", "ok"
    return "stabil", "ok"


def status_aus_fehler(fehler, kandidat_gezeigt=False):
    """Status für einen Solver-Fehler (SolverFehler oder andere Ausnahme)."""
    status = getattr(fehler, "status", None)
    if status is None:
        return "Fehler", "problem"
    if status == "sinkt":
        return "Sinken", "hinweis"
    if status == "schwebt":
        return "Schweben", "hinweis"
    if status == "instabile_lage":
        return "instabil", "hinweis"
    if status in _KANDIDATEN_STATUS and kandidat_gezeigt:
        return "Näherungslösung", "hinweis"
    return "nicht lösbar", "problem"


def schwimmpruefung(kraftfunktion, koerper, masse, g):
    """Prüft vor dem Solver, ob der Körper überhaupt tragen kann.

    Liefert "schwebt" (nichts verdrängt Wasser), "sinkt" (Gewicht größer als
    der Auftrieb des voll eingetauchten Körpers) oder None.
    """
    from .auftrieb import als_bindung

    try:
        blaetter = als_bindung(koerper).blatt_meshes
    except Exception:
        return None
    if not blaetter:
        return "schwebt"
    punkte = np.vstack([np.asarray(b[0], float) for b in blaetter])
    if punkte.size == 0:
        return "schwebt"
    ausdehnung = float(np.max(np.linalg.norm(punkte, axis=1))) + 1e-3
    auftrieb = 0.0
    for z in (-ausdehnung, 0.0):
        erg = kraftfunktion((z, 0.0, 0.0))
        auftrieb = max(auftrieb, float(erg.F_A.as_array()[2]))
    if auftrieb <= 0.0:
        return "schwebt"
    if auftrieb < masse * g * (1.0 - 1e-9):
        return "sinkt"
    return None
