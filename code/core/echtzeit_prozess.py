"""Isoliert die CPU-intensive Echtzeitphysik vom GUI-Prozess."""
from __future__ import annotations

import time

_kraftfunktion = None
_masse = None
_traegheit = None
_dt = None
_g = None


def initialisieren(koerper, rho_w, physik, hydrostatik_pfad="exakt_union"):
    """Bereitet das unveränderliche Kraftmodell einmal pro Worker vor."""
    global _kraftfunktion, _masse, _traegheit, _dt, _g
    from .auftrieb import baue_kraftfunktion_6dof
    from .kraftmodell import KraftmodellMitHydroCache, baue_kraftmodell

    hydrostatik = baue_kraftfunktion_6dof(
        koerper, rho_w=rho_w, g=physik.g_m_pro_s2,
        pfad=hydrostatik_pfad)
    _kraftfunktion = KraftmodellMitHydroCache(
        baue_kraftmodell(
            hydrostatik, physik, masse=koerper.masse,
            g=physik.g_m_pro_s2),
        intervall=1)
    _masse = float(koerper.masse)
    _traegheit = koerper.traegheitstensor
    _dt = float(physik.dt_s)
    _g = float(physik.g_m_pro_s2)


def schritte_berechnen(zustand, anzahl_schritte, fremdkraft=None):
    """Berechnet einen Batch und gibt nur pickelbare Ergebnisdaten zurück."""
    from .dynamik_6dof import schritt

    startzeit = time.perf_counter()
    ergebnis = None
    _kraftfunktion.aktualisieren()
    try:
        _kraftfunktion.fremdkraft_setzen(fremdkraft)
        for _ in range(anzahl_schritte):
            zustand, ergebnis = schritt(
                zustand, _kraftfunktion, _masse, _traegheit, _dt, _g)
    except (ArithmeticError, KeyError, ValueError) as fehler:
        return None, None, str(fehler), time.perf_counter() - startzeit
    return zustand, ergebnis, None, time.perf_counter() - startzeit
