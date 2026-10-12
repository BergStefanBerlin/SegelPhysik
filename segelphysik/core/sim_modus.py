"""P5c Schritt 1 - Simulationsmodi (nur Umschaltung, KEINE Physik).

Drei Modi (Beschluss 12.10.):
  RUHEND   - Grafik only (heutiger Zustand)
  STATISCH - Solver sucht Gleichgewicht (spaeter)
  ECHTZEIT - Integration mit festem dt (spaeter)

Diese Stufe implementiert ausschliesslich den Zustaandsautomaten und seine
Textdarstellung - bewusst ohne jede Physik-Funktion ("langsam langsam").

Tasten (Beschluss 12.10.): r -> RUHEND, s -> STATISCH, z -> ECHTZEIT.
Regeln: gleiche Taste im selben Modus ist ein No-op; unbekannte Tasten
veraendern nichts; der Zaehler erfasst nur echte Wechsel.
"""
from __future__ import annotations
from enum import Enum


class Modus(Enum):
    RUHEND = "RUHEND"
    STATISCH = "STATISCH"
    ECHTZEIT = "ECHTZEIT"


MODUS_TASTEN = {"r": Modus.RUHEND, "s": Modus.STATISCH, "z": Modus.ECHTZEIT}


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
