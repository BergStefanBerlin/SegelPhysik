# ============================================================
# dynamics.py - Simulation des frei schwimmenden Koerpers (6 DOF)
# ------------------------------------------------------------
# Newton-Euler (Rotation im Koerperframe):
#    (m+m_a)*v'   = F_A - m*g + F_ext + F_hyd - Daempfung
#    I*om' + om x (I*om) = tau - c_rot*om   (Kreiseleffekt inkl.)
# Quaternion-Integration: q' = 0.5 * q * (0, omega), renormalisiert.
# Semi-implizites Euler, dt = DT, NSUB Teilschritte pro Bild.
# ============================================================
import numpy as np

from config import G, RHO_W, DT, M_ADD_FAKTOR
from math_utils import (quat_mul, quat_from_euler, quat_to_R,
                        rotationsmatrix, euler_aus_R)
from geometry import QuaderVoxel
from hydrostatics import hydro
from hydrodynamics import HydroDyn


class Simulation:
    """Dynamik des frei schwimmenden Quaders mit 6 Freiheitsgraden:
    Position p(3), Quaternion q(4), v(3), omega(3, Koerperframe)."""

    def __init__(self, L, B, H, rho, n=24, lk=0.25, tk=0.5, rhok=3000.0):
        self.q = QuaderVoxel(L, B, H, rho, n, lk, tk, rhok)
        q = self.q
        m = q.m
        self.sinkt = q.m >= RHO_W * (q.V + q.Vk)
        # Traegheitstensor (numerisch aus den Wolken, um den CG)
        self.I = q.I_num.copy()
        self.I_ges = 1.2 * self.I          # + added rotational inertia
        self.m_a = M_ADD_FAKTOR * m
        # Daempfung (aus aufrechter Hydrostatik abgeleitet, grob skaliert)
        A_wl = 0.72 * q.L * q.B            # eff. Wasserlinienflaeche
        k_h = RHO_W * G * A_wl
        self.c_lin = 2 * 0.30 * np.sqrt(k_h * (m + self.m_a))
        # Horizontal (Surge/Sway): quadratischer Wasserwiderstand des
        # Unterwasserrumpfs (F = k_drag * |v_h| * v_h). c_lin oben ist
        # fuer die Heave-Schwingung abgeleitet und wuerde horizontal
        # eine unrealistisch hohe Fahrtdaempfung erzeugen.
        A_sw = q.L * ((m / RHO_W) / A_wl)     # eff. Seitenflaeche
        self.k_drag = 0.5 * RHO_W * 2.0 * A_sw
        V_sub0 = m / RHO_W
        if not self.sinkt:
            KG = q.c_body[2]
            KB = 0.45 * (-q.d_r) + 0.05    # grob: CB des Rumpfkoerpers
            BM_r = (0.60*q.L * q.B**3 / 12) / V_sub0
            BM_p = (q.B * (0.85*q.L)**3 / 12) / V_sub0
            GM_r, GM_p = KB + BM_r - KG, KB + BM_p - KG
            K_r = RHO_W * G * V_sub0 * GM_r
            K_p = RHO_W * G * V_sub0 * GM_p
            c_r = 2*0.35*np.sqrt(K_r*self.I[0, 0]) if K_r > 0 else 0.4*self.I[0, 0]
            c_p = 2*0.35*np.sqrt(K_p*self.I[1, 1]) if K_p > 0 else 0.4*self.I[1, 1]
        else:
            c_r = c_p = 0.4 * self.I[0, 0]
        self.c_rot = np.array([c_r, c_p, 0.5*c_r])
        self.z_bed = -3.0 * max(q.L, q.B, q.H)
        self.F_ext = np.zeros(3)      # externe Kraft (Weltframe) [N]
        self.tau_ext = np.zeros(3)    # externes Moment (Koerperframe) [Nm]
        self.rw_soll = 0.0            # Soll-Ruderwinkel [rad]
        self.hydrodyn = HydroDyn(self)   # Schritt 2: Hydrodynamik
        self.reset()

    # ---------- Anzeige-/Kompatibilitaets-Eigenschaften ----------
    @property
    def z_c(self): return self.p[2]
    @property
    def roll(self):  return euler_aus_R(self.R)[0]
    @property
    def pitch(self): return euler_aus_R(self.R)[1]
    @property
    def yaw(self):   return euler_aus_R(self.R)[2]
    @property
    def vz(self): return self.v[2]
    @property
    def wr(self): return self.om[0]

    def setze(self, z_c, roll, pitch):
        """Zustand direkt setzen (z. B. aus der Gleichgewichtssuche)."""
        self.p = np.array([0.0, 0.0, z_c])
        self.quat = quat_from_euler(roll, pitch, 0.0)
        self.v = np.zeros(3)
        self.om = np.zeros(3)
        self.F_ext = np.zeros(3)      # keine alten Greifkraefte uebernehmen
        self.tau_ext = np.zeros(3)
        self._p_ok = self.p.copy()
        self._q_ok = self.quat.copy()
        self.aktualisiere()

    def reset(self, heel_deg=25.0):
        q = self.q
        if self.sinkt:
            z0 = q.H / 2 + 0.10
        else:
            # Kiel ist praktisch immer getaucht: Restvolumen vom Rumpf
            z0 = q.H/2 - max(q.m/RHO_W - q.Vk, 0.0) / (q.L * q.B)
        self.p = np.array([0.0, 0.0, z0])
        self.quat = quat_from_euler(np.radians(heel_deg), 0.0, 0.0)
        self.v = np.zeros(3)
        self.om = np.zeros(3)
        self.F_ext = np.zeros(3)
        self.tau_ext = np.zeros(3)
        self.t = 0.0
        self.am_grund = False
        self._p_ok = self.p.copy()
        self._q_ok = self.quat.copy()
        self.aktualisiere()

    def aktualisiere(self):
        self.R = quat_to_R(self.quat)
        self.h = hydro(self.q, self.R, self.p)

    def stoss(self, d_wr_deg=60.0):
        self.om[0] += np.radians(d_wr_deg)   # Roll-Stoss um Koerper-x

    def schritt(self, dt=DT):
        q = self.q
        self.aktualisiere()
        h = self.h
        # --- Translation (Weltframe): Auftrieb, Gewicht, Daempfung ---
        v_h = self.v[:2]
        F_d = np.array([0.0, 0.0, -self.c_lin * self.v[2]])
        F_hyd, tau_hyd = self.hydrodyn.kraefte(dt)
        F = (np.array([0.0, 0.0, h['F_A'] - q.m*G]) + F_d
             + self.F_ext + F_hyd)
        a = F / (q.m + self.m_a)
        # --- Rotation (Koerperframe): Newton-Euler mit Kreiselterm ---
        tau = h['tau_body'] - self.c_rot * self.om + self.tau_ext + tau_hyd
        gyro = np.cross(self.om, self.I @ self.om)
        alpha = np.linalg.solve(self.I_ges, tau - gyro)
        # --- semi-implizites Euler ---
        self.v += a * dt
        self.om += alpha * dt
        self.p += self.v * dt
        dq = 0.5 * quat_mul(self.quat, np.concatenate([[0.0], self.om]))
        self.quat = self.quat + dq * dt
        self.quat /= np.linalg.norm(self.quat)
        self.t += dt
        # --- Schutzschranken: Auch eine durch eine starke Greifkraft
        # erzwungene 360-Grad-Drehung muss die Integration ueberstehen;
        # Geschwindigkeiten werden begrenzt, NaN/inf stellt den letzten
        # gueltigen Zustand wieder her. ---
        np.clip(self.v, -50.0, 50.0, out=self.v)
        om_abs = np.linalg.norm(self.om)
        if om_abs > 25.0:
            self.om *= 25.0 / om_abs
        if not (np.all(np.isfinite(self.p)) and np.all(np.isfinite(self.v))
                and np.all(np.isfinite(self.om))
                and np.all(np.isfinite(self.quat))):
            self.p = self._p_ok.copy()
            self.quat = self._q_ok.copy()
            self.v[:] = 0.0
            self.om[:] = 0.0
        else:
            self._p_ok = self.p.copy()
            self._q_ok = self.quat.copy()
        # --- Grundkontakt ---
        lowest = h['W'][:, 2].min()
        self.am_grund = False
        if lowest < self.z_bed:
            self.p[2] += (self.z_bed - lowest)
            if self.v[2] < 0:
                self.v[2] = 0.0
            self.om *= 0.85
            self.am_grund = True

    def gleichgewicht(self):
        """Energie-Minimum ueber alle Lagen (Grobsuche + Mustersuche).
        Gewichtet: Rumpf-Punkte mit rho, Anhang-Punkte mit rhok-Array."""
        q = self.q
        if self.sinkt:
            return None
        V_ziel = q.m / RHO_W
        # Geometrische Volumina (NICHT dichtegewichtet!): Die Verdraengung
        # haengt nur von der getauchten Geometrie ab, nicht von der Dichte.
        w1 = np.full(len(q.P), q.dV)
        w2 = np.full(len(q.Pk), q.dVk)
        ww = np.concatenate([w1, w2])
        P_all = np.vstack([q.P, q.Pk])

        def energie(roll, pitch):
            R = rotationsmatrix(roll, pitch)
            zz = (P_all @ R.T)[:, 2]
            idx = np.argsort(zz)
            zz_s, ww_s = zz[idx], ww[idx]
            cum = np.cumsum(ww_s)
            k = int(np.searchsorted(cum, V_ziel))
            rest = V_ziel - (cum[k-1] if k > 0 else 0.0)
            E_int = (np.sum(zz_s[:max(k-1, 0)] * ww_s[:max(k-1, 0)])
                     + (zz_s[k-1] * rest if k > 0 else 0.0))
            E = q.m * G * (R @ q.c_body)[2] - RHO_W * G * E_int
            z_c = -0.5*(zz_s[k-1] + zz_s[k]) if k > 0 else 0.0
            return E, z_c

        winkel = np.radians(np.arange(0, 180, 15))
        best = None
        for roll in winkel:
            for pitch in winkel:
                E, z_c = energie(roll, pitch)
                if best is None or E < best[0]:
                    best = (E, z_c, roll, pitch)
        E, z_c, roll, pitch = best
        schritt = np.radians(7.5)
        for _ in range(12):
            verb = False
            for d_r, d_p in [(schritt, 0), (-schritt, 0), (0, schritt),
                             (0, -schritt), (schritt, schritt),
                             (-schritt, -schritt), (schritt, -schritt),
                             (-schritt, schritt)]:
                E2, z2 = energie(roll+d_r, pitch+d_p)
                if E2 < E:
                    E, z_c, roll, pitch = E2, z2, roll+d_r, pitch+d_p
                    verb = True
            schritt *= 0.5
            if not verb and schritt < np.radians(0.02):
                break
        return {'z_c': z_c, 'roll': roll, 'pitch': pitch}
