# ============================================================
# app.py - GUI (QuaderApp), Schritt 8.2
# ------------------------------------------------------------
#   * KEINE Slider, KEINE Zeitkontrolle
#   * Layout: LINKS Szene (+ Ansicht-Buttons unten links),
#             RECHTS Parameter- und Messwert-Panel
#   * FM / FW / RW einstellbar:
#       - Klick auf "-" / "+" im Parameter-Panel
#       - Tasten:  Bild auf/ab        = FM +/-100 N
#                  Pfeil auf/ab       = FW +/-5 deg
#                  Pfeil links/rechts = RW +/-5 deg
#   * Simulation laeuft permanent
# ============================================================
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Ellipse
from matplotlib.widgets import Button
import mpl_toolkits.mplot3d.proj3d as proj3d

# Farbschema Kraftpfeile (Paare mit gleicher Farbe wirken gegeneinander):
#   ROT   : G (Gewicht, abwaerts) <-> F_A (Auftrieb, aufwaerts)
#   GRUEN : F_M (Vortrieb)        <-> F_Rumpf (Widerstand)
#   BLAU  : F_Kiel + F_Ruder      (laterales System)
import time as _time

from config import G, DT, NSUB, MAST_H_FAKTOR
from dynamics import Simulation
from rendering.scene import boot_ansicht, dr, zeichne_szene, wasser_schritt

# --- feste Rumpf-Parameter ---
P_L, P_B, P_H, P_RHO, P_N = 9.0, 2.96, 1.6, 130.0, 16
P_LK, P_TK, P_RK = 0.11, 1.35, 11300.0

FM_SCHRITT, FW_SCHRITT, RW_SCHRITT = 100.0, 5.0, 5.0

# --- Ansichts-Presets: (Name, Azimut, Elevation) ---
ANSICHTEN = [('3/4', -60.0, 22.0), ('Seite', 90.0, 8.0),
             ('Bug', 0.0, 8.0), ('Heck', 180.0, 8.0),
             ('Oben', -90.0, 89.0)]


class QuaderApp:
    def __init__(self):
        plt.rcParams['font.size'] = 9
        self.fig = plt.figure(figsize=(14.5, 8.2))
        try:
            self.fig.canvas.manager.set_window_title(
                'Segelphysik - Schwimmender Koerper, 6 Freiheitsgrade')
        except Exception:
            pass
        self.fig.patch.set_facecolor('#f4f6f8')

        # --------------------- LAYOUT ---------------------
        self.ax = self.fig.add_axes([0.015, 0.075, 0.64, 0.895],
                                    projection='3d')
        self.axov = self.fig.add_axes(self.ax.get_position().bounds)
        self.axov.set_zorder(10)

        # --- Ansicht-Buttons unten links unter der Szene ---
        self._btn_axes = []
        self._btns = []          # Referenzen halten (sonst GC -> tot)
        bw = 0.085
        for i, (name, az, el) in enumerate(ANSICHTEN):
            bax = self.fig.add_axes(
                [0.025 + i * (bw + 0.010), 0.012, bw, 0.042])
            btn = Button(bax, name)
            btn.on_clicked(lambda ev, az=az, el=el: self._ansicht(az, el))
            self._btn_axes.append(bax)
            self._btns.append(btn)

        self.axp = self.fig.add_axes([0.675, 0.640, 0.315, 0.330])
        self.axw = self.fig.add_axes([0.675, 0.115, 0.315, 0.515])
        self.axs = self.fig.add_axes([0.685, 0.018, 0.295, 0.090])
        for a in (self.axp, self.axw, self.axs):
            a.set_xticks([]); a.set_yticks([])
            a.set_facecolor('#eef3f6')
            for sp in a.spines.values():
                sp.set_color('#99aabb')

        self.txt_fahrt = self.fig.text(
            0.035, 0.985, '', ha='left', va='top', fontsize=12,
            fontweight='bold', family='monospace', color='#00325a',
            bbox=dict(boxstyle='round', fc='#e8f2fa', ec='#4a7fa5',
                      alpha=0.9), zorder=20)

        # --- regelbare Groessen ---
        self.fm = 0.0         # Scheiben-Kraft [N] (Start: kraftfrei)
        self.fw_deg = 35.0    # Kraftwinkel [deg], 0 = Bug
        self.rw_deg = 0.0     # Ruderwinkel [deg]

        self.sim = None
        self.wasser = None
        self._klick_zonen = {}
        self._neu()

        self.timer = self.fig.canvas.new_timer(interval=15)
        self.timer.add_callback(self._frame)
        self.timer.start()
        self._uhr = _time.perf_counter()   # Echtzeit-Regler
        self._rueckstand = 0.0
        self._zeitfaktor = 1.0

        self.view_drag = None
        self.fig.canvas.mpl_connect('button_press_event', self._on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self._on_release)
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)

    def show(self):
        """Kompatibel zum alten Einstieg: startet die matplotlib-Hauptschleife."""
        plt.show()

    def _neu(self):
        self.sim = Simulation(P_L, P_B, P_H, P_RHO, n=P_N,
                              lk=P_LK, tk=P_TK, rhok=P_RK)
        self.wasser = None
        self._w_off = np.zeros(2)
        self._w_yaw = 0.0

    def _ansicht(self, azimut, elevation):
        self.ax.azim = azimut
        self.ax.elev = elevation

    # ------------------------------------------------------------
    # Parameter-Panel (oben rechts)
    # ------------------------------------------------------------
    def _parameter_zeichnen(self):
        q = self.sim.q
        z = [('Rumpflaenge L', '%g m' % q.L),
             ('Rumpfbreite B', '%g m' % q.B),
             ('Rumpfhoehe H', '%g m' % q.H),
             ('Strukturdichte', '%g kg/m^3' % q.rho),
             ('Gesamtmasse m', '%.0f kg' % q.m),
             ('Kiel-Laenge/L', '%g' % P_LK),
             ('Kiel-Tiefe/L', '%g' % P_TK),
             ('Bulb-Dichte', '%.0f kg/m^3' % P_RK)]
        self.axp.clear()
        self.axp.set_xticks([]); self.axp.set_yticks([])
        self.axp.set_xlim(0, 1); self.axp.set_ylim(0, 1)
        self.axp.text(0.03, 0.965, 'PARAMETER', fontsize=10,
                      fontweight='bold', va='top', color='#00325a')
        y = 0.875
        for name, val in z:
            self.axp.text(0.03, y, name, fontsize=8.5, va='top',
                          color='#304050')
            self.axp.text(0.97, y, val, fontsize=8.5, va='top',
                          ha='right', family='monospace', color='#103050')
            y -= 0.075

        self.axp.text(0.03, y, 'einstellbar (-/+ klicken oder Tasten):',
                      fontsize=7.2, va='top', color='#708090')
        y -= 0.055
        self._klick_zonen = {}
        regel = [('fm', 'Scheiben-Kraft FM', '%.0f N' % self.fm),
                 ('fw', 'Kraftwinkel FW', '%g deg (weltfest)' % self.fw_deg),
                 ('rw', 'Ruderwinkel RW', '%g deg' % self.rw_deg)]
        for key, name, val in regel:
            self.axp.text(0.03, y, name, fontsize=8.5, va='top',
                          color='#304050')
            self.axp.text(0.62, y, '-', fontsize=13, va='top', ha='center',
                          fontweight='bold', color='#a00000',
                          family='monospace')
            self.axp.text(0.78, y, val, fontsize=8.2, va='top', ha='center',
                          family='monospace', color='#103050')
            self.axp.text(0.94, y, '+', fontsize=11, va='top', ha='center',
                          fontweight='bold', color='#006000',
                          family='monospace')
            self._klick_zonen[key] = y
            y -= 0.075

    @staticmethod
    def _kN(x):
        return ('%8.2f kN' % (x / 1000.0) if abs(x) >= 1000.0
                else '%8.1f N' % x)

    # ------------------------------------------------------------
    # Messwert-Panel (Mitte rechts) + Summenkraft (unten rechts)
    # ------------------------------------------------------------
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
        self.axw.set_xticks([]); self.axw.set_yticks([])
        self.axw.set_xlim(0, 1); self.axw.set_ylim(0, 1)

        def gruppe(y, titel):
            self.axw.text(0.03, y, titel, fontsize=9, fontweight='bold',
                          va='top', color='#00325a')
            return y - 0.052

        def zeile(y, name, val, farbe='#103050'):
            self.axw.text(0.09, y, name, fontsize=8.2, va='top',
                          color='#304050')
            self.axw.text(0.97, y, val, fontsize=8.2, va='top', ha='right',
                          family='monospace', color=farbe)
            return y - 0.038

        y = 0.98
        self.axw.text(0.03, y, 'MESSWERTE   t = %.1f s' % s.t, fontsize=10,
                      fontweight='bold', va='top', color='#00325a')
        y -= 0.075

        y = gruppe(y, 'Kraefte')
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
        y -= 0.006

        y = gruppe(y, 'Geschwindigkeiten')
        y = zeile(y, 'horizontal (Fahrt)',
                  '%5.2f m/s = %4.2f kn' % (vh, vh * 1.94384))
        y = zeile(y, 'vertikal (v_z)', '%+5.2f m/s' % s.v[2])
        y = zeile(y, 'resultierend |v|',
                  '%5.2f m/s' % float(np.linalg.norm(s.v)))
        y -= 0.006

        y = gruppe(y, 'Lage')
        y = zeile(y, 'Kraengung', '%7.1f deg' % _w(s.roll))
        y = zeile(y, 'Trimm', '%7.1f deg' % _w(s.pitch))
        y = zeile(y, 'Gieren', '%7.1f deg' % _w(s.yaw))
        if hd is not None:
            y = zeile(y, 'Abdrift', '%7.1f deg' % _w(hd.drift))
        y = zeile(y, 'Tiefgang', '%7.3f m' % h['tiefgang'])
        y -= 0.006

        y -= 0.006
        y = gruppe(y, 'Gleichgewicht (Validierung)')
        F_res = getattr(s, 'F_res', None)
        tau_res = getattr(s, 'tau_res', None)
        if F_res is not None:
            ok_f = float(np.linalg.norm(F_res)) < 100.0
            y = zeile(y, 'Summe F  x/y/z',
                      '%+5.0f/%+5.0f/%+5.0f N'
                      % (F_res[0], F_res[1], F_res[2]),
                      '#007000' if ok_f else '#b06000')
            y = zeile(y, '|Summe F|',
                      '%7.0f N' % float(np.linalg.norm(F_res)),
                      '#007000' if ok_f else '#b06000')
            if tau_res is not None:
                ok_m = float(np.linalg.norm(tau_res)) < 500.0
                y = zeile(y, '|Summe M| (Drehmoment)',
                          '%7.0f Nm' % float(np.linalg.norm(tau_res)),
                          '#007000' if ok_m else '#b06000')
        y -= 0.006
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

        # --- Summenkraft-Balken ---
        self.axs.clear()
        self.axs.set_xticks([]); self.axs.set_yticks([])
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
    # Aenderung der regelbaren Groessen
    # ------------------------------------------------------------
    def _aendern(self, key, richtung):
        if key == 'fm':
            self.fm = float(np.clip(self.fm + richtung * FM_SCHRITT,
                                    0.0, 4000.0))
        elif key == 'fw':
            self.fw_deg = float(np.clip(self.fw_deg + richtung * FW_SCHRITT,
                                        0.0, 180.0))
        elif key == 'rw':
            self.rw_deg = float(np.clip(self.rw_deg + richtung * RW_SCHRITT,
                                        -35.0, 35.0))

    def _on_key(self, ev):
        k = ev.key
        if k in ('up', 'pageup'):
            self._aendern('fm', +1)
        elif k in ('down', 'pagedown'):
            self._aendern('fm', -1)
        elif k == 'left':
            self._aendern('rw', -1)
        elif k == 'right':
            self._aendern('rw', +1)
        elif k == 'shift+up':
            self._aendern('fw', +1)
        elif k == 'shift+down':
            self._aendern('fw', -1)

    def _on_press(self, ev):
        if ev.inaxes is self.axp and self._klick_zonen:
            xf, yf = ev.xdata, ev.ydata
            if xf is not None and yf is not None:
                for key, yz in self._klick_zonen.items():
                    if abs(yf - yz) < 0.05:
                        if 0.55 <= xf <= 0.69:
                            self._aendern(key, -1); return
                        if 0.87 <= xf <= 1.00:
                            self._aendern(key, +1); return
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
    # Physik-Takt
    # ------------------------------------------------------------
    def _scheiben_kraft_anwenden(self):
        """Konstante Kraft FM an der Mastspitze, Richtung aus FW
        (bootrelativ, immer horizontal), Moment um den CG."""
        s = self.sim
        FM, FW = self.fm, np.radians(self.fw_deg)
        if FM <= 1e-9:
            s.F_ext = np.zeros(3)
            s.tau_ext = np.zeros(3)
            return
        # WELTFESTE Richtung (wie Wind aus fester Richtung): FW ist
        # der Winkel zur Welt-x-Achse, NICHT zum Boot. Sonst dreht die
        # Kraft beim Gieren mit und es existiert kein Gleichgewicht.
        d_w = np.array([np.cos(FW), -np.sin(FW), 0.0])
        F_w = FM * d_w
        r_top = np.array([float(s.q.c_body[0]), 0.0,
                          s.q.H / 2 + MAST_H_FAKTOR * s.q.L])
        s.F_ext = F_w
        s.tau_ext = s.R.T @ np.cross(s.R @ (r_top - s.q.c_body), F_w)

    def _frame(self):
        # --- Echtzeit-Regler: verstrichene Wanduhr-Zeit in Physik-
        #     Schritte umsetzen. Die Simulation folgt der echten Uhr,
        #     egal wie schnell oder langsam der Rechner ist.
        jetzt = _time.perf_counter()
        dt_wand = min(jetzt - self._uhr, 0.25)   # Deckel (Tab-Wechsel etc.)
        self._uhr = jetzt
        self._rueckstand += dt_wand

        schritte = 0
        while self._rueckstand >= DT and schritte < 240:
            self._scheiben_kraft_anwenden()
            self.sim.rw_soll = np.radians(self.rw_deg)
            self.sim.schritt()
            self._rueckstand -= DT
            schritte += 1
        if self._rueckstand > 1.0:      # hoffnungslos hinterher -> verwerfen
            self._rueckstand = 0.0
        if schritte:
            wasser_schritt(self, schritte * DT)
        if dt_wand > 1e-4:
            faktor_neu = schritte * DT / dt_wand
            self._zeitfaktor += 0.1 * (faktor_neu - self._zeitfaktor)

        self._zeichnen()
        self._messwerte_zeichnen()
        self._parameter_zeichnen()
        self.txt_fahrt.set_text(
            'Fahrt %5.2f m/s (%4.2f kn)   t = %.1f s   Realzeit x%.2f'
            % (float(np.hypot(self.sim.v[0], self.sim.v[1])),
               float(np.hypot(self.sim.v[0], self.sim.v[1])) * 1.94384,
               self.sim.t, self._zeitfaktor))
        self.fig.canvas.draw_idle()

    # ------------------------------------------------------------
    # Szene + Kraftpfeile (Overlay im Vordergrund)
    # ------------------------------------------------------------
    def _zeichnen(self):
        ax = self.ax
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

        bb = self.axov.bbox

        def zu_px(p3):
            x2, y2, _ = proj3d.proj_transform(float(p3[0]), float(p3[1]),
                                              float(p3[2]), ax.get_proj())
            return np.asarray(ax.transData.transform((x2, y2)), float)

        def px2frac(p):
            return ((p[0] - bb.x0) / bb.width, (p[1] - bb.y0) / bb.height)

        az, el = np.radians(ax.azim), np.radians(ax.elev)
        view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az),
                         np.sin(el)])

        def pfeil(start_v, d_v, px_len, farbe, label=None):
            u = np.asarray(d_v, float)
            nl = np.linalg.norm(u)
            if nl < 1e-12:
                return
            u = u / nl
            f = float(np.sqrt(max(0.0, 1.0 - float(u @ view) ** 2)))
            if f < 0.06:
                return
            s_px = zu_px(start_v)
            dpx = zu_px(np.asarray(start_v, float) + u * (0.06 * r)) - s_px
            L = np.linalg.norm(dpx)
            if L < 1e-9:
                return
            e_px = s_px + dpx * (px_len * f / L)
            self.axov.add_patch(Ellipse(
                px2frac(s_px), 5.0 / bb.width, 5.0 / bb.height,
                facecolor=farbe, edgecolor='none', zorder=5,
                transform=self.axov.transAxes))
            self.axov.add_patch(FancyArrowPatch(
                px2frac(s_px), px2frac(e_px),
                transform=self.axov.transAxes, color=farbe,
                arrowstyle='-|>', mutation_scale=13, lw=1.8,
                shrinkA=0, shrinkB=0, zorder=6))
            if label is not None:
                self.axov.text(px2frac(e_px)[0] + 0.008,
                               px2frac(e_px)[1] + 0.008, label,
                               transform=self.axov.transAxes, fontsize=7,
                               color=farbe, zorder=7)

        # Kraftskala: Pixel pro Kilonewton, gedeckelt
        def sk(F):
            return float(min(30.0 * max(np.linalg.norm(F), 1e-9) / 1000.0
                             + 28.0, 240.0))

        # G und F_A (vertikal, Welt-Richtung)
        FG = q.m * G
        pfeil(CG, [0, 0, -1], sk(FG), '#c00000',
              'G %.1f kN' % (FG / 1000.0))
        if CB is not None:
            FA = s.h['F_A']
            pfeil(CB, [0, 0, +1], sk(FA), '#c00000',
                  'F_A %.1f kN' % (FA / 1000.0))

        # Horizontale Kraefte: Richtung World -> Boot-Ansicht (dr)
        def dview(F_w):
            d2 = dr(s, np.asarray(F_w, float)[:2])
            return np.array([float(d2[0]), float(d2[1]), 0.0])

        if np.linalg.norm(s.F_ext) > 1e-9:
            pfeil(top_v, dview(s.F_ext), sk(s.F_ext), '#008800',
                  'F_M %.0f N' % np.linalg.norm(s.F_ext))
        hd = getattr(s, 'hydrodyn', None)
        if hd is not None:
            zk = -0.55 * P_TK * P_L
            if np.linalg.norm(hd.F_kiel) > 1e-9:
                pfeil([0.0, 0.0, zk], dview(hd.F_kiel), sk(hd.F_kiel),
                      '#0055bb', 'Kiel %.0f N' % np.linalg.norm(hd.F_kiel))
            if np.linalg.norm(hd.F_rud) > 1e-9:
                pfeil([-0.42 * P_L, 0.0, zk * 0.85], dview(hd.F_rud),
                      sk(hd.F_rud), '#0055bb',
                      'Rud %.0f N' % np.linalg.norm(hd.F_rud))
            if np.linalg.norm(hd.F_rumpf) > 1e-9:
                pfeil(CG, dview(hd.F_rumpf), sk(hd.F_rumpf), '#008800',
                      'Drag %.0f N' % np.linalg.norm(hd.F_rumpf))


# ------------------------------------------------------------
if __name__ == '__main__':
    QuaderApp().fig.canvas.manager.show()
