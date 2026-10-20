"""Explizite Prozessauswahl zwischen produktiver Migration und Referenz."""
from functools import wraps
from contextlib import contextmanager
from contextvars import ContextVar
from inspect import signature
import os

import numpy as np

_referenz = ContextVar("segelphysik_python_referenz", default=False)


@contextmanager
def python_referenz():
    """Lokaler Referenzvergleich ohne Umschaltung anderer Threads."""
    token = _referenz.set(True)
    try:
        yield
    finally:
        _referenz.reset(token)


def rechenpfad():
    if _referenz.get():
        return "python"
    pfad = os.environ.get("SEGELPHYSIK_RECHENPFAD", "cpp")
    if pfad not in ("cpp", "python"):
        raise ValueError(
            "SEGELPHYSIK_RECHENPFAD muss 'cpp' oder 'python' sein")
    return pfad


def nativer_kern(name, *, skalare=(), tuple_ausgabe=False):
    def dekorieren(referenz):
        signatur = signature(referenz)

        @wraps(referenz)
        def rechnen(*args, **kwargs):
            if rechenpfad() == "python":
                return referenz(*args, **kwargs)
            from .native_backend import native_laden

            if kwargs or len(args) != len(signatur.parameters):
                gebunden = signatur.bind(*args, **kwargs)
                gebunden.apply_defaults()
                args = tuple(gebunden.arguments.values())
            werte = tuple(
                float(wert) if i in skalare else np.asarray(wert, dtype=np.float64)
                for i, wert in enumerate(args))
            ergebnis = getattr(native_laden(), name)(*werte)
            return tuple(float(w) for w in ergebnis) if tuple_ausgabe else ergebnis
        return rechnen
    return dekorieren
