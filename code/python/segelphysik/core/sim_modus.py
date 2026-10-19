"""P5c Schritt 1 - Simulationsmodi (nur Umschaltung, KEINE Physik).

Modi: RUHEND / STATISCH / ECHTZEIT, Tasten r / s / z.
StoerSequenz (Spec V4A rev B): reiner Countdown zwischen Stoerpose und
Solver-Start (Standard 5 s, nur STATISCH). Rein, vollvermascht testbar.
"""
from __future__ import annotations
from enum import Enum


class Modus(Enum):
    RUHEND = "RUHEND"
    STATISCH = "STATISCH"
    ECHTZEIT = "ECHTZEIT"


MODUS_TASTEN = {"r": Modus.RUHEND, "s": Modus.STATISCH, "z": Modus.ECHTZEIT}

COUNTDOWN_S = 5.0


class SimSteuerung:
    """Zustandsautomat der drei Simulationsmodi (rein, ohne Grafik)."""

    def __init__(self, start=Modus.RUHEND):
        if not isinstance(start, Modus):
            raise ValueError("start muss ein Modus sein, nicht %r" % (start,))
        self.modus = start
        self.wechsel = 0

    def taste(self, taste):
        """Wendet eine Taste an. True nur bei echtem Moduswechsel."""
        ziel = MODUS_TASTEN.get(taste)
        if ziel is None or ziel is self.modus:
            return False
        self.modus = ziel
        self.wechsel += 1
        return True

    def text(self):
        """Textdarstellung fuer die Statuszeile."""
        return "MODUS: %s" % self.modus.value


class StoerSequenz:
    """Countdown zwischen Stoerpose und Solver-Start (Spec V4A, rein).

    starten() setzt den Timer; tick(dt) liefert GENAU EINMAL True beim
    Ablauf; abbrechen() bricht ab (Moduswechsel waehrend des Countdowns).
    """

    def __init__(self, dauer_s=COUNTDOWN_S):
        self.dauer = float(dauer_s)
        if self.dauer <= 0.0:
            raise ValueError("dauer_s muss positiv sein")
        self.rest = 0.0
        self.aktiv = False

    def starten(self):
        self.aktiv = True
        self.rest = self.dauer

    def abbrechen(self):
        self.aktiv = False
        self.rest = 0.0

    def tick(self, dt):
        """Zaehlt herunter. True genau beim Ablauf (einmalig)."""
        if not self.aktiv:
            return False
        self.rest = max(0.0, self.rest - float(dt))
        if self.rest <= 0.0:
            self.aktiv = False
            return True
        return False

    def text(self):
        """Statuszeilentext waehrend des Countdowns (leer, wenn aus)."""
        if not self.aktiv:
            return ""
        return "Solver in %.1f s" % self.rest
