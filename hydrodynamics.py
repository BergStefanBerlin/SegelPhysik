# ============================================================
# hydrodynamics.py - Hydrodynamik: Kiel + Ruder als Tragfluegel,
# Rumpfwiderstand laengs/quer getrennt.  (Schritt 2)
# ------------------------------------------------------------
# Normalkraft-Modell (gueltig 0..90 deg Anstellwinkel):
#   CN(alpha) = CLa*sin(a)*cos(a) + CD90*sin(a)*|sin(a)|
#   CLa       = 2*pi*AR/(AR+2)          (endliche Streckung)
# Erster Term: Potential-Zirkulation (kleine alpha: linear),
# zweiter Term: Querstrom-Widerstand (dominiert im Stall ->
# natuerliches Abreissen ohne Polter-Kraefte).
# Momente um den GESAMT-CG (Newton-Euler im Koerperframe).
# Die Anstroemung am Blatt enthaelt omega x r -> Kiel und Ruder
# liefern automatisch Roll-/Gierdaempfung.
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
        self.k_l = 0.5 * RHO_W * 0.010 * A_l
        A_q = q.L * (abs(q.d_r) + 0.6*q.t_fin)
        self.k_q = 0.5 * RHO_W * 0.35 * A_q
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

    def _tragfluegel(self, u_body, A, AR, r_rel, cd0=0.015, CD90=1.0):
        u = np.asarray(u_body, float)
        U = float(np.hypot(u[0], u[1]))
        if U < 1e-4 or A <= 1e-9:
            return np.zeros(3), np.zeros(3), 0.0
        alpha = float(np.arctan2(u[1], abs(u[0])))
        sa, ca = np.sin(alpha), np.cos(alpha)
        CLa = 2.0*np.pi*AR/(AR + 2.0)
        CN = CLa*sa*ca + CD90*sa*abs(sa)
        CT = -cd0*ca*abs(ca)*float(np.sign(u[0]))
        q_dyn = 0.5*RHO_W*U*U
        F_body = q_dyn*A*np.array([CT, CN, 0.0])
        F_world = self.sim.R @ F_body
        tau_body = np.cross(r_rel, F_body)
        return F_world, tau_body, alpha

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
        F_k, _, self.alpha_k = self._tragfluegel(
            u_k, q.A_fin, q.AR_fin, r_k, cd0=0.012, CD90=1.1)
        vor = 1.0 if u_r[0] < 0.0 else -1.0
        U_r = float(np.hypot(u_r[0], u_r[1]))
        alpha_flow = float(np.arctan2(u_r[1], abs(u_r[0])))
        self.alpha_r = alpha_flow - vor*self.rw
        u_r_eff = np.array([u_r[0], U_r*np.sin(self.alpha_r), 0.0])
        F_r, _, _ = self._tragfluegel(
            u_r_eff, q.A_rud, q.AR_rud, r_r, cd0=0.015, CD90=1.0)
        fac_k = self._tauche(q.r_kiel, q.t_fin)
        fac_r = self._tauche(q.r_rud, q.t_rud)
        F_k, F_r = F_k*fac_k, F_r*fac_r
        # Alle Hydrodynamik-Kraefte wirken AUSSCHLIESSLICH in der Ebene
        # der Wasseroberflaeche (keine Z-Komponente im Weltframe, auch
        # nicht bei Kraengung/Trimm). Die Tragfluegel-Physik (Anstell-
        # winkel, CN) bleibt im Koerperframe; nur die resultierende
        # Kraft wird auf die Horizontale projiziert.
        F_k[2] = 0.0
        F_r[2] = 0.0
        # Momente konsistent um den CG: Hebelarm UND Kraft im Weltframe,
        # dann das Moment in den Koerperframe drehen.
        tau_k = R.T @ np.cross(R @ r_k, F_k)
        tau_r = R.T @ np.cross(R @ r_r, F_r)
        F_h_b = np.array([-self.k_l*abs(v[0])*v[0],
                          -self.k_q*abs(v[1])*v[1], 0.0])
        F_h = R @ F_h_b
        F_h[2] = 0.0
        self.F_kiel, self.F_rud, self.F_rumpf = F_k, F_r, F_h
        self.tau_hyd = tau_k + tau_r
        return F_k + F_r + F_h, self.tau_hyd
