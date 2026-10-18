"""SegelPhysik V3 - Steuerung (Kontrollpanel-Zustand, Spec Abschnitt 6).

Kein GUI-Framework: haelt den Steuerzustand und verdrahtet Tasten eines
PyVista-Plotters. Entfallene Regler der Altversionen werden nicht erzeugt.
"""
from __future__ import annotations

KOERPER_TYPEN = ("cone", "box", "pyramid")


class ControlPanel:
    """Steuerzustand: Spawn-Auswahl, Start/Pause/Reset, Wiedergabefaktor."""

    def __init__(self):
        self.laeuft = True
        self.wiedergabe = 1.0            # Spec: 0.25x - 4x
        self.body_type = "cone"

    def umschalten(self): self.laeuft = not self.laeuft
    def start(self): self.laeuft = True
    def pause(self): self.laeuft = False

    def aendere_wiedergabe(self, faktor):
        self.wiedergabe = max(0.25, min(4.0, self.wiedergabe * faktor))

    def waehle_koerper(self, typ):
        if typ not in KOERPER_TYPEN: raise ValueError(typ)
        self.body_type = typ

    def verdrahte(self, plotter, spawn_callback):
        for taste, typ in zip("123", KOERPER_TYPEN):
            plotter.add_key_event(taste, lambda t=typ: (self.waehle_koerper(t),
                                                        spawn_callback(t)))
