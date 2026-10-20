"""Isoliert die CPU-intensive Echtzeitphysik vom GUI-Prozess."""
from __future__ import annotations

import operator
import time

_kraftfunktion = None
_masse = None
_traegheit = None
_dt = None
_g = None
_native_kontext = None


def initialisieren(koerper, rho_w, physik, hydrostatik_pfad="exakt_union",
                   cd_volumenkoerper=None):
    """Bereitet das unveränderliche Kraftmodell einmal pro Worker vor."""
    global _kraftfunktion, _masse, _traegheit, _dt, _g, _native_kontext
    from .auftrieb import baue_kraftfunktion_6dof
    from .kraftmodell import KraftmodellMitHydroCache, baue_kraftmodell
    from .hydrodynamik import HydrodynamikModell
    from .rechenpfad import rechenpfad

    _kraftfunktion = None
    _native_kontext = None

    hydrostatik = baue_kraftfunktion_6dof(
        koerper, rho_w=rho_w, g=physik.g_m_pro_s2,
        pfad=hydrostatik_pfad)
    hydrodynamik = HydrodynamikModell.aus_koerper(
        koerper, rho_kg_m3=rho_w,
        cd_volumenkoerper=cd_volumenkoerper,
        fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
        fluidwinkelgeschwindigkeit=physik.fluidwinkelgeschwindigkeit)
    _kraftfunktion = KraftmodellMitHydroCache(
        baue_kraftmodell(
            hydrostatik, physik, masse=koerper.masse,
            g=physik.g_m_pro_s2, hydrodynamik=hydrodynamik),
        intervall=1)
    _masse = float(koerper.masse)
    _traegheit = koerper.traegheitstensor
    _dt = float(physik.dt_s)
    _g = float(physik.g_m_pro_s2)
    if rechenpfad() == "cpp" and hydrostatik_pfad == "exakt_union":
        from .native_backend import physikkontext_vorbereiten

        _native_kontext = physikkontext_vorbereiten(
            koerper, rho_w, physik, hydrostatik, hydrodynamik)


def schritte_berechnen(zustand, anzahl_schritte, fremdkraft=None,
                       ruderwinkel_rad=0.0):
    """Berechnet einen Batch und gibt nur pickelbare Ergebnisdaten zurück."""
    from .dynamik_6dof import schritt
    from .native_backend import NativeBackendFehler
    from .rechenpfad import rechenpfad

    startzeit = time.perf_counter()
    ergebnis = None
    try:
        if _kraftfunktion is None:
            raise ValueError("Physikworker ist nicht initialisiert")
        if isinstance(anzahl_schritte, bool):
            raise ValueError("Batchanzahl darf kein Wahrheitswert sein")
        anzahl_schritte = operator.index(anzahl_schritte)
        if anzahl_schritte < 1:
            raise ValueError("Batch braucht mindestens einen Schritt")
        _kraftfunktion.aktualisieren()
        _kraftfunktion.fremdkraft_setzen(fremdkraft)
        _kraftfunktion.ruderwinkel_setzen(ruderwinkel_rad)
        if rechenpfad() == "cpp" and _native_kontext is not None:
            from .native_backend import (
                ergebnis_nach_python, native_laden, zustand_vorbereiten,
            )

            ergebnis = _native_kontext.batch(
                zustand_vorbereiten(zustand), anzahl_schritte, fremdkraft,
                float(ruderwinkel_rad), native_laden().Abbruch())
            neu, kraft = ergebnis_nach_python(ergebnis)
            return neu, kraft, None, time.perf_counter() - startzeit
        for _ in range(anzahl_schritte):
            zustand, ergebnis = schritt(
                zustand, _kraftfunktion, _masse, _traegheit, _dt, _g)
    except (ArithmeticError, KeyError, TypeError, ValueError, NativeBackendFehler) as fehler:
        return None, None, str(fehler), time.perf_counter() - startzeit
    return zustand, ergebnis, None, time.perf_counter() - startzeit
