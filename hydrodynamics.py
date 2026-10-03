# ============================================================
# hydrodynamics.py - Hydrodynamik: Kiel + Ruder als Tragfluegel,
# Rumpfwiderstand laengs/quer getrennt.  (Schritt 6)
# ------------------------------------------------------------
# Tragfluegel-Modell, gueltig fuer ALLE Anstroemrichtungen:
#   Zerlegung der Anstroemung am Blatt in Sehnenkomponente (ut,
#   Koerper-x) und Normalkomponente (un, Koerper-y):
#     Normalkraft  CN = f_circ*CLa*sin(a)cos(a) + CD90*sin(a)|sin(a)|
#       - Zirkulationsanteil NUR bei Anstroemung von vorn (ut < 0),
#         quadratischer Fade mit ut/U -> bei Quer-/Rueckwarts-
#         anstroemung reiner Querstrom.
#       - Querstrom-Widerstand wirkt IMMER entlang der Normalkompo-
#         nente der Relativstroemung -> streng dissipativ.
#     Reibung CT entlang der Sehne, immer entgegen der Gleit-
#         geschwindigkeit (Vorzeichen = ut).
#   Damit gilt F·u >= 0 fuer JEDE Anstroemrichtung: Die Kraft kann
#   dem System nie Energie zufuehren (keine Anti-Daempfung mehr,
#   kein Aufschaukeln bei Drehbewegungen - Fix der Schritt-5-
#   Instabilitaet).
#   CLa = 2*pi*AR/(AR+2)  (endliche Streckung)
#
# Ruder: Die Anstroemung wird um den Ruderwinkel in das Ruderframe
#   gedreht, die Kraft zurueckgedreht. Konvention: rw > 0 -> Bug
#   nach Backbord (+y). Stetig fuer alle Anstroemrichtungen.
#
# Momente um den GESAMT-CG (Newton-Euler im Koerperframe). Alle
# Hydrodynamik-Kraefte wirken ausschliesslich in der Ebene der
# Wasseroberflaeche (keine Z-Komponente im Weltframe).
# ============================================================
import numpy as np
from config import RHO_W


class HydroDyn:
    """Kiel und Ruder als vertikale Tragfluegel im Wasser plus
    quadratischer Rumpfwiderstand (laengs/quer getrennt)."""

    def __init__(self, sim):
        self.sim = sim
        q = sim.q
        A_l = 2.2 * q.L * abs(q.d_r)
        self.k_l = 0.5 * RHO_W * 0.030 * A_l
        A_q = q.L * abs(q.d_r)
        self.k_q = 0.5 * RHO_W * 0.060 * A_q
        self.rw = 0.0
        self.drift = 0.0
        self.alpha_k = 0.0
        self.alpha_r = 0.0
        self.F_kiel = np.zeros(3)
        self.F_rud = np.zeros(3)
        self.F_rumpf = np.zeros(3)
        self.tau_hyd = np.zeros(3)

    def _tauche(self, p_body, tiefe):
        z_w = float((self.sim.R @ p_body + self.sim.p)[2])
        return float(np.clip(-z_w / max(0.5*tiefe, 0.05), 0.0, 1.0))

    def _tragfluegel_b(self, u_body, A, AR, cd0=0.015, CD90=1.0):
        """Tragfluegel im KOERPERframe. u_body: Relativstroemung am
        Blatt. Vorwaertsfahrt -> u[0] < 0. Rueckgabe: (F_body, alpha).
        F ist streng dissipativ: F·u >= 0 fuer alle Richtungen."""
        u = np.asarray(u_body, float)
        ut, un = float(u[0]), float(u[1])
        U = float(np.hypot(ut, un))
        if U < 1e-4 or A <= 1e-9:
            return np.zeros(3), 0.0
        alpha = float(np.arctan2(un, abs(ut)))
        sa, ca = np.sin(alpha), np.cos(alpha)
        CLa = 2.0*np.pi*AR/(AR + 2.0)
        f_vorn = max(-ut, 0.0)/U          # Zirkulation nur von vorn
        f_circ = f_vorn*f_vorn
        CN = f_circ*CLa*sa*ca + CD90*sa*abs(sa)
        CT = cd0*abs(ca)*ut/U             # immer bremsend
        q_dyn = 0.5*RHO_W*U*U
        F_body = q_dyn*A*np.array([CT, CN, 0.0])
        return F_body, alpha

    def kraefte(self, dt):
        s = self.sim
        q = s.q
        R, v, om = s.R, s.v, s.om
        soll = float(getattr(s, 'rw_soll', 0.0))
        rate = 3.0
        self.rw += float(np.clip(soll - self.rw, -rate*dt, rate*dt))
        r_k = q.r_kiel - q.c_body
        r_r = q.r_rud - q.c_body
        u_k = -(v + np.cross(om, r_k))
        u_r = -(v + np.cross(om, r_r))
        vb = v + np.cross(om, r_k)
        self.drift = float(np.arctan2(vb[1], abs(vb[0]) + 1e-9))

        Fk_b, self.alpha_k = self._tragfluegel_b(
            u_k, q.A_fin, q.AR_fin, cd0=0.012, CD90=1.1)

        c, s_ = np.cos(self.rw), np.sin(self.rw)
        u_rr = np.array([c*u_r[0] - s_*u_r[1],
                         s_*u_r[0] + c*u_r[1], 0.0])
        Fr_rud, self.alpha_r = self._tragfluegel_b(
            u_rr, q.A_rud, q.AR_rud, cd0=0.015, CD90=1.0)
        Fr_b = np.array([c*Fr_rud[0] + s_*Fr_rud[1],
                         -s_*Fr_rud[0] + c*Fr_rud[1], 0.0])

        fac_k = self._tauche(q.r_kiel, q.t_fin)
        fac_r = self._tauche(q.r_rud, q.t_rud)
        Fk_b, Fr_b = Fk_b*fac_k, Fr_b*fac_r

        F_k = R @ Fk_b
        F_r = R @ Fr_b
        F_k[2] = 0.0
        F_r[2] = 0.0
        tau_k = R.T @ np.cross(R @ r_k, F_k)
        tau_r = R.T @ np.cross(R @ r_r, F_r)

        vb_w = R.T @ v
        F_h_b = np.array([-self.k_l*abs(vb_w[0])*vb_w[0],
                          -self.k_q*abs(vb_w[1])*vb_w[1], 0.0])
        F_h = R @ F_h_b
        F_h[2] = 0.0

        self.F_kiel, self.F_rud, self.F_rumpf = F_k, F_r, F_h
        self.tau_hyd = tau_k + tau_r
        return F_k + F_r + F_h, self.tau_hyd
