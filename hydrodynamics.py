# ============================================================
# hydrodynamics.py - Hydrodynamik (Kiel/Ruder/Widerstand)
# ------------------------------------------------------------
# SCHRITT 2 (Platzhalter): Hier entsteht die nichtlineare
# Hydrodynamik des Unterwassers:
#   - Kiel + Ruder als vertikale Tragfluegel (Normalkraft-Modell,
#     natuerlicher Stall): CN(alpha) = CLa*sin(a)*cos(a)
#                             + CD90*sin(a)*|sin(a)|
#   - Rumpfwiderstand laengs/quer getrennt (quadratisch)
#   - Momente UMG DEN CG (nicht um den Koerperursprung!)
# Die Simulation ruft kraefte() bereits auf; aktuell werden
# Nullkraefte geliefert (Verhalten identisch zu quader_app_4).
# ============================================================
import numpy as np


class HydroDyn:
    """Stub: Schnittstelle steht, Physik folgt in Schritt 2."""

    def __init__(self, sim):
        self.sim = sim
        # Diagnosegroessen (werden in Schritt 2 gefuellt)
        self.F_kiel = np.zeros(3)    # Weltframe [N]
        self.F_rud = np.zeros(3)     # Weltframe [N]
        self.F_rumpf = np.zeros(3)   # Weltframe [N]
        self.drift = 0.0             # Abdriftwinkel [rad]

    def kraefte(self, dt):
        """Liefert (F_world, tau_body_um_CG) der Hydrodynamik.
        Aktuell: Nullkraefte (nur Hydrostatik + Daempfung aktiv)."""
        return np.zeros(3), np.zeros(3)
