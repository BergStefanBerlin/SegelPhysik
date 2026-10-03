# ============================================================
# app.py - GUI (QuaderApp), Schritt 8: Paneel-Layout
# ------------------------------------------------------------
# Umgestaltung gegenueber Schritt 6:
#   * KEINE Schieberegler mehr (Parameter sind feste Werte)
#   * KEINE Buttons (Neustart/Gleichgewicht/Stoss) und keine
#     Zeitkontrolle (Start/Pause/Einzelschritt/Tempo/Richtung)
#   * Layout: LINKS die 3D-Szene, RECHTS zwei Listen
#       - oben: feste Parameter
#       - unten: aktuelle Messwerte, thematisch gruppiert
#         (Kraefte paarweise, Geschwindigkeiten, Lage, Bewegung)
#       - Summenkraefte pro Achse als Balkendarstellung
#   * Ansicht: freie Mausrotation (linke Maustaste ziehen)
# Die Physik-Module kennen diese Datei nicht -> headless testbar.
# ============================================================
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.proj3d as proj3d
from matplotlib.patches import FancyArrowPatch, Ellipse

from config import G, DT, NSUB, MAST_H_FAKTOR
from dynamics import Simulation
from rendering.scene import boot_ansicht, dr, zeichne_szene, wasser_schritt

# --- feste Einstellwerte (ehemalige Slider-Defaults; FM/FW so, dass
#     die Yacht segelt; siehe Parameterliste rechts oben) ---
P_L, P_B, P_H, P_RHO, P_N = 9.0, 2.96, 1.6, 130.0, 16
P_LK, P_TK, P_RK = 0.11, 1.35, 11300.0
P_FM, P_FW_DEG, P_RW_DEG = 1200.0, 35.0, 0.0


class QuaderApp:
    def __init__(self):
        plt.rcParams['font.size'] = 9
        self.fig = plt.figure(figsize=(14.5, 8.0))
        try:
            self.fig.canvas.manager.set_window_title(
                'Segelphysik - Schwimmender Koerper, 6 Freiheitsgrade')
        except Exception:
            pass
        self.fig.patch.set_facecolor('#f4f6f8')

        # --------------------- LAYOUT ---------------------
        # Links: 3D-Szene (+ unsichtbare Overlay-Ebene fuer Pfeile)
        self.ax = self.fig.add_axes([0.015, 0.02, 0.64, 0.95],
                                    projection='3d')
        self.axov = self.fig.add_axes(self.ax.get_position().bounds)
        self.axov.set_zorder(10)

        # Rechts oben: Parameterliste (statisch)
        self.axp = self.fig.add_axes([0.675, 0.60, 0.315, 0.37])
        # Rechts Mitte: Messwert-Listen (gruppiert, live)
        self.axw = self.fig.add_axes([0.675, 0.145, 0.315, 0.44])
        # Rechts unten: Summenkraefte pro Achse (Balken)
        self.axs = self.fig.add_axes([0.685, 0.025, 0.295, 0.105])

        for a in (self.axp, self.axw, self.axs):
            a.set_xticks([]); a.set_yticks([])
            a.set_facecolor('#eef3f6')
            for sp in a.spines.values():
                sp.set_color('#99aabb')

        # Fahrt-Anzeige ueber der Szene
        self.txt_fahrt = self.fig.text(
            0.035, 0.985, '', ha='left', va='top', fontsize=12,
            fontweight='bold', family='monospace', color='#00325a',
            bbox=dict(boxstyle='round', fc='#e8f2fa', ec='#4a7fa5',
                      alpha=0.9), zorder=20)

        self.sim = None
        self.wasser = None
        self._w_off = np.zeros(2)     # Boot-Position in der Zeichen-Welt
        self._w_yaw = 0.0             # aufsummierter Gierwinkel
        self._neu()
        self._parameter_zeichnen()

        self.timer = self.fig.canvas.new_timer(interval=40)
        self.timer.add_callback(self._frame)
        self.timer.start()

        # --- freie Mausrotation der Szene ---
        self.view_drag = None
        self.fig.canvas.mpl_connect('button_press_event', self._on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self._on_release)

    # ------------------------------------------------------------
    # Rechte Panels
    # ------------------------------------------------------------
    def _parameter_zeichnen(self):
        q = self.sim.q if self.sim is not None else None
        L = q.L if q else P_L
        B = q.B if q else P_B
        H = q.H if q else P_H
        rho = q.rho if q else P_RHO
        m = q.m if q else 0.0
        z = [('Rumpflaenge L', '%g m' % L),
             ('Rumpfbreite B', '%g m' % B),
             ('Rumpfhoehe H', '%g m' % H),
             ('Strukturdichte', '%g kg/m^3' % rho),
             ('Gesamtmasse m', '%.0f kg' % m),
             ('Kiel-Laenge/L', '%g' % P_LK),
             ('Kiel-Tiefe/L', '%g' % P_TK),
             ('Bulb-Dichte', '%.0f kg/m^3' % P_RK),
             ('Scheiben-Kraft FM', '%.0f N' % P_FM),
             ('Kraftwinkel FW', '%g deg (0=Bug)' % P_FW_DEG),
             ('Ruderwinkel RW', '%g deg' % P_RW_DEG)]
        self.axp.clear()
        self.axp.set_xlim(0, 1); self.axp.set_ylim(0, 1)
        self.axp.text(0.03, 0.955, 'PARAMETER (fest)', fontsize=10,
                      fontweight='bold', va='top', color='#00325a')
        y = 0.86
        for name, val in z:
            self.axp.text(0.03, y, name, fontsize=8.5, va='top',
                          color='#304050')
            self.axp.text(0.97, y, val, fontsize=8.5, va='top',
                          ha='right', family='monospace', color='#103050')
            y -= 0.082

    @staticmethod
    def _kN(x):
        return ('%8.2f kN' % (x / 1000.0) if abs(x) >= 1000.0
                else '%8.1f N' % x)

    def _messwerte_zeichnen(self):
        s, q = self.sim, self.sim.q
        h = s.h
        hd = getattr(s, 'hydrodyn', None)
        vh = float(np.hypot(s.v[0], s.v[1]))
        F_sum_h = ((s.F_ext + hd.F_kiel + hd.F_rud + hd.F_rumpf)
                   if hd is not None else s.F_ext.copy())
        F_z = h['F_A'] - q.m * G
        F_ges = np.array([F_sum_h[0], F_sum_h[1], F_z])

        def _w(x):
            return (np.degrees(x) + 180.0) % 360.0 - 180.0

        self.axw.clear()
        self.axw.set_xlim(0, 1); self.axw.set_ylim(0, 1)

        def gruppe(y, titel):
            self.axw.text(0.03, y, titel, fontsize=9, fontweight='bold',
                          va='top', color='#00325a')
            return y - 0.075

        def zeile(y, name, val, farbe='#103050'):
            self.axw.text(0.09, y, name, fontsize=8.2, va='top',
                          color='#304050')
            self.axw.text(0.97, y, val, fontsize=8.2, va='top', ha='right',
                          family='monospace', color=farbe)
            return y - 0.062

        y = 0.98
        self.axw.text(0.03, y, 'MESSWERTE   t = %.1f s' % s.t, fontsize=10,
                      fontweight='bold', va='top', color='#00325a')
        y -= 0.085

        # --- Kraefte (paarweise: G <-> F_A) ---
        y = gruppe(y, 'Kr\u00e4fte')
        y = zeile(y, 'G  (Gewicht)', self._kN(q.m * G), '#a00000')
        y = zeile(y, 'F_A (Auftrieb)', self._kN(h['F_A']), '#003ca0')
        y = zeile(y, 'Netto z (F_A-G)', self._kN(F_z),
                  '#000000' if abs(F_z) < 100.0 else '#b06000')
        if hd is not None:
            y = zeile(y, 'F_Mast (Antrieb)',
                      '%7.0f N' % np.linalg.norm(s.F_ext), '#008000')
            y = zeile(y, 'F_Kiel (Seitenkraft)',
                      '%7.0f N' % np.linalg.norm(hd.F_kiel), '#00806e')
            y = zeile(y, 'F_Ruder',
                      '%7.0f N' % np.linalg.norm(hd.F_rud), '#a87f00')
            y = zeile(y, 'F_Rumpf (Widerstand)',
                      '%7.0f N' % np.linalg.norm(hd.F_rumpf), '#606060')
        y -= 0.015

        # --- Geschwindigkeiten ---
        y = gruppe(y, 'Geschwindigkeiten')
        y = zeile(y, 'horizontal (Fahrt)',
                  '%5.2f m/s = %4.2f kn' % (vh, vh * 1.94384))
        y = zeile(y, 'vertikal (v_z)', '%+5.2f m/s' % s.v[2])
        y = zeile(y, 'resultierend |v|',
                  '%5.2f m/s' % float(np.linalg.norm(s.v)))
        y -= 0.015

        # --- Lage ---
        y = gruppe(y, 'Lage')
        y = zeile(y, 'Kr\u00e4ngung', '%7.1f deg' % _w(s.roll))
        y = zeile(y, 'Trimm', '%7.1f deg' % _w(s.pitch))
        y = zeile(y, 'Gieren', '%7.1f deg' % _w(s.yaw))
        if hd is not None:
            y = zeile(y, 'Abdrift', '%7.1f deg' % _w(hd.drift))
        y = zeile(y, 'Tiefgang', '%7.3f m' % h['tiefgang'])
        y -= 0.015

        # --- Position / Bewegung ---
        y = gruppe(y, 'Position / Bewegung')
        y = zeile(y, 'Position x/y',
                  '%+6.1f / %+6.1f m' % (s.p[0], s.p[1]))
        y = zeile(y, 'Drehgeschw. |omega|',
                  '%6.1f deg/s' % np.degrees(np.linalg.norm(s.om)))
        y = zeile(y, 'Beschleunigung |F|/m',
                  '%6.2f m/s^2' % (float(np.linalg.norm(F_ges)) / q.m))
        if s.sinkt:
            self.axw.text(0.03, y, '>>> Dichte >= 1000: SINKT' +
                          ('  (am Grund)' if s.am_grund else ''),
                          fontsize=9, fontweight='bold', va='top',
                          color='#b00000')

        # --- Summenkraefte pro Achse: Balken ---
        self.axs.clear()
        self.axs.set_xlim(0, 1); self.axs.set_ylim(0, 1)
        self.axs.text(0.03, 0.97, 'SUMMENKRAFT (Achsen)', fontsize=9,
                      fontweight='bold', va='top', color='#00325a')
        fmax = max(500.0, float(np.max(np.abs(F_ges))) * 1.15)
        for i, (nm, fv) in enumerate(zip(['Fx', 'Fy', 'Fz'], F_ges)):
            yb = 0.62 - i * 0.26
            self.axs.plot([0.16, 0.90], [yb, yb], color='#b8c4cc', lw=0.8)
            frac = float(np.clip(fv / fmax, -1.0, 1.0)) * 0.37
            farbe = '#2a7fba' if abs(fv) < 100.0 else '#d08000'
            self.axs.add_patch(plt.Rectangle(
                (0.535, yb - 0.075), frac, 0.15,
                facecolor=farbe, edgecolor='none'))
            self.axs.text(0.03, yb, nm, fontsize=8, va='center',
                          family='monospace', color='#304050')
            self.axs.text(0.97, yb, '%+8.0f N' % fv, fontsize=8,
                          va='center', ha='right', family='monospace',
                          color='#103050')

    # ------------------------------------------------------------
    # Physik-Takt (immer laufend, keine Zeitkontrolle mehr)
    # ------------------------------------------------------------
    def _scheiben_kraft_anwenden(self):
        """Konstante Mastspitzen-Kraft FM, Richtung aus FW (bootrelativ,
        immer horizontal), Moment um den CG."""
        s = self.sim
        FM, FW = P_FM, np.radians(P_FW_DEG)
        if FM <= 1e-9:
            s.F_ext = np.zeros(3)
            s.tau_ext = np.zeros(3)
            return
        x_w = s.R @ np.array([1.0, 0.0, 0.0]); x_w[2] = 0.0
        y_w = s.R @ np.array([0.0, 1.0, 0.0]); y_w[2] = 0.0
        nx, ny = np.linalg.norm(x_w), np.linalg.norm(y_w)
        if nx < 1e-9 or ny < 1e-9:
            s.F_ext = np.zeros(3)
            s.tau_ext = np.zeros(3)
            return
        x_w, y_w = x_w / nx, y_w / ny
        d_w = np.cos(FW) * x_w - np.sin(FW) * y_w
        F_w = FM * d_w
        r_top = np.array([float(s.q.c_body[0]), 0.0,
                          s.q.H / 2 + MAST_H_FAKTOR * s.q.L])
        s.F_ext = F_w
        s.tau_ext = s.R.T @ np.cross(s.R @ (r_top - s.q.c_body), F_w)

    def _frame(self):
        self._scheiben_kraft_anwenden()
        self.sim.rw_soll = np.radians(P_RW_DEG)
        for _ in range(NSUB):
            self.sim.schritt()
        wasser_schritt(self, NSUB * DT)
        self._zeichnen()
        self._messwerte_zeichnen()
        self.fig.canvas.draw_idle()

    # ------------------------------------------------------------
    # Szene + Kraftpfeile (Overlay)
    # ------------------------------------------------------------
    def _zeichnen(self):
        ax = self.ax
        ax.clear()
        ax.set_proj_type('ortho')
        self.axov.clear()
        self.axov.set_xlim(0, 1); self.axov.set_ylim(0, 1)
        self.axov.axis('off')
        self.axov.patch.set_visible(False)
        self.axov.set_zorder(10)
        s = self.sim
        q = s.q

        ref = zeichne_szene(self, ax, self.axov)
        CG, CB, top_v, r = ref['CG'], ref['CB'], ref['top_v'], ref['r']

        dpi = self.fig.dpi
        px_pro_g = 2.0 / 2.54 * dpi
        bb = self.axov.bbox

        def zu_px(p3):
            x2, y2, _ = proj3d.proj_transform(p3[0], p3[1], p3[2],
                                              ax.get_proj())
            return np.array(ax.transData.transform((x2, y2)))

        def px2frac(p):
            return ((p[0] - bb.x0) / bb.width, (p[1] - bb.y0) / bb.height)

        cg_px = zu_px(CG)
        shrink_pts = 0.0

        def pfeil(start3d, richtung3d, laenge_px, farbe, shrink_pts):
            start3d = np.asarray(start3d, dtype=float)
            u = np.asarray(richtung3d, dtype=float)
            nl = np.linalg.norm(u)
            if nl < 1e-12:
                return None
            u = u / nl
            start_px = zu_px(start3d)
            d_px = 2 * 3.2 * dpi / 72.0
            self.axov.add_patch(Ellipse(
                px2frac(start_px), d_px / bb.width, d_px / bb.height,
                facecolor=farbe, edgecolor='none', zorder=5,
                transform=self.axov.transAxes))
            az, el = np.radians(ax.azim), np.radians(ax.elev)
            view = np.array([np.cos(el) * np.cos(az),
                             np.cos(el) * np.sin(az), np.sin(el)])
            f = float(np.sqrt(max(0.0, 1.0 - float(u @ view) ** 2)))
            if f < 0.04:
                return None
            dpx = zu_px(start3d + u * (0.05 * r)) - start_px
            L = np.linalg.norm(dpx)
            if L < 1e-9:
                return None
            ende = start_px + dpx * (laenge_px * f / L)
            arr = FancyArrowPatch(px2frac(start_px), px2frac(ende),
                                  arrowstyle='-|>', mutation_scale=26,
                                  lw=3.2, color=farbe, zorder=4,
                                  shrinkA=shrink_pts, shrinkB=1,
                                  transform=self.axov.transAxes)
            self.axov.add_patch(arr)
            return start_px, ende

        def label(px_end, text, farbe, dx_px, dy_px):
            f = px2frac(np.array([px_end[0] + dx_px, px_end[1] + dy_px]))
            self.axov.text(f[0], f[1], text, color=farbe, fontsize=9,
                           fontweight='bold', ha='left', va='center',
                           zorder=5)

        e_g = pfeil(CG, [0, 0, -1], px_pro_g, (0.85, 0.10, 0.10), shrink_pts)
        e_b = None
        if CB is not None and s.h['F_A'] > 1e-9:
            a_b = s.h['F_A'] / q.m
            e_b = pfeil(CB, [0, 0, 1], px_pro_g * a_b / G,
                        (0.10, 0.35, 0.90), 0.0)

        if CB is not None:
            ax.plot([CG[0], CB[0]], [CG[1], CB[1]], [CG[2], CB[2]],
                    'k--', lw=1, alpha=0.6)

        label(cg_px, 'CG', '#303030', 14, 14)
        if e_g is not None:
            label(e_g[1], 'G = %.1f kN' % (q.m * G / 1000), '#a00000',
                  10, -16)
        if e_b is not None:
            label(e_b[1], 'F_A = %.1f kN' % (s.h['F_A'] / 1000), '#003ca0',
                  10, 16)
        if CB is not None and s.h['F_A'] > 1e-9:
            label(zu_px(CB), 'CB', '#003ca0', 12, -14)

        if P_FM > 1e-9:
            FW = np.radians(P_FW_DEG)
            x_w = s.R @ np.array([1.0, 0.0, 0.0]); x_w[2] = 0.0
            y_w = s.R @ np.array([0.0, 1.0, 0.0]); y_w[2] = 0.0
            nx, ny = np.linalg.norm(x_w), np.linalg.norm(y_w)
            if nx > 1e-9 and ny > 1e-9:
                f_r = (np.cos(FW) * (x_w / nx) - np.sin(FW) * (y_w / ny))
                pfeil(top_v, dr(s, f_r), px_pro_g * P_FM / 1000.0,
                      (0.00, 0.70, 0.15), 0.0)
                label(zu_px(top_v + dr(s, f_r) * 0.02),
                      'F_M = %.0f N' % P_FM, '#008000', 10, 18)

        hd = getattr(s, 'hydrodyn', None)
        if hd is not None:
            p_kiel_v = boot_ansicht(s, s.R @ q.r_kiel + s.p)
            p_rud_v = boot_ansicht(s, s.R @ q.r_rud + s.p)
            F_k = np.asarray(hd.F_kiel, float)
            F_r = np.asarray(hd.F_rud, float)
            if float(np.linalg.norm(F_k)) > 20.0:
                e_k = pfeil(p_kiel_v, dr(s, F_k),
                            px_pro_g * float(np.linalg.norm(F_k)) / 1000.0,
                            (0.00, 0.60, 0.55), 0.0)
                if e_k is not None:
                    label(e_k[1], 'F_Kiel = %.0f N' % np.linalg.norm(F_k),
                          '#00806e', 10, -16)
            if float(np.linalg.norm(F_r)) > 20.0:
                e_r = pfeil(p_rud_v, dr(s, F_r),
                            px_pro_g * float(np.linalg.norm(F_r)) / 1000.0,
                            (0.95, 0.72, 0.10), 0.0)
                if e_r is not None:
                    label(e_r[1], 'F_Ruder = %.0f N' % np.linalg.norm(F_r),
                          '#a87f00', 10, 16)

        ax.set_title(
            'Winner 9.00   L=%g  B=%g  H=%g m   m=%.0f kg   t=%6.1f s'
            '   1 g = 2 cm' % (q.L, q.B, q.H, q.m, s.t), fontsize=9)

    # ------------------------------------------------------------
    # Maus: freie Rotation der Szene
    # ------------------------------------------------------------
    def _on_press(self, ev):
        if ev.inaxes not in (self.ax, self.axov) or ev.button != 1:
            return
        self.view_drag = (ev.x, ev.y, self.ax.azim, self.ax.elev)

    def _on_motion(self, ev):
        if ev.x is None or ev.y is None or self.view_drag is None:
            return
        x0, y0, az0, el0 = self.view_drag
        self.ax.azim = az0 - (ev.x - x0) * 0.5
        self.ax.elev = max(-90.0, min(90.0, el0 + (ev.y - y0) * 0.5))

    def _on_release(self, ev):
        self.view_drag = None

    # ------------------------------------------------------------
    def _neu(self):
        self.sim = Simulation(P_L, P_B, P_H, P_RHO, P_N,
                              P_LK, P_TK, P_RK)
        self.sim.reset(heel_deg=25.0)
        self.wasser = None

    def show(self):
        plt.show()
