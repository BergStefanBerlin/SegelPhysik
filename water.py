# ============================================================
# water.py - Seezeichen-Muster (Bewegungsreferenz auf dem Wasser)
# ------------------------------------------------------------
# World-festes Muster (Punkte + Striche) in einem periodischen
# Kachelraster. Das Boot steht im Bild still - die Zeichen
# verschieben sich entgegen der Fahrt ueber Grund und rotieren
# entgegen dem Gieren -> Bewegungssuggestion.
# ============================================================
import numpy as np


class WasserFeld:
    def __init__(self, r, n_pkt=650, n_str=90, n_tief=220, seed=7):
        self.T = 2.6 * r                      # Kachelgroesse (periodisch)
        rng = np.random.default_rng(seed)
        self.P = rng.uniform(-self.T/2, self.T/2, (n_pkt, 2))
        self.S = rng.uniform(-self.T/2, self.T/2, (n_str, 2))
        self.phi = rng.uniform(0.0, np.pi, n_str)   # world-feste Richtung
        self.halb = (0.02 + 0.03*rng.random(n_str)) * r
        self.z = 0.004 * r                    # leichte Anhebung ueber z=0
        # Unterwasser-Layer (3D): eigene Punkte in verschiedenen Tiefen,
        # damit die Bewegungsreferenz auch von UNTEN lesbar ist.
        self.PT = rng.uniform(-self.T/2, self.T/2, (n_tief, 2))
        self.zt = rng.uniform(-0.45*r, -0.06*r, n_tief)

    def ansicht(self, off, yaw):
        """Zeichen in Boot-Koordinaten: exakte Transformation
        rel = Rz(-yaw) @ (P_welt - Position), dann modulo Kachelgroesse
        wrapen (unendlicher Ozean). Strichrichtungen drehen mit -yaw."""
        c, s_ = np.cos(yaw), np.sin(yaw)
        Rz = np.array([[c, s_], [-s_, c]])    # Rz(-yaw), Zeilenvektoren
        rel = (self.P - off) @ Rz.T
        rel = (rel + self.T/2) % self.T - self.T/2
        rels = (self.S - off) @ Rz.T
        rels = (rels + self.T/2) % self.T - self.T/2
        dv = np.stack([np.cos(self.phi - yaw),
                       np.sin(self.phi - yaw)], axis=1)
        a = rels - dv * self.halb[:, None]
        b = rels + dv * self.halb[:, None]
        relt = (self.PT - off) @ Rz.T
        relt = (relt + self.T/2) % self.T - self.T/2
        return rel, a, b, np.column_stack([relt, self.zt])
