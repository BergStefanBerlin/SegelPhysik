# ============================================================
# app.py - GUI (QuaderApp): Slider, Buttons, Maus, Timer
# ------------------------------------------------------------
# Nutzt dynamics.Simulation (Physik) und rendering.scene (3D-Szene).
# Die Physik-Module kennen diese Datei nicht -> headless testbar.
# ============================================================
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
import mpl_toolkits.mplot3d.proj3d as proj3d
from matplotlib.patches import FancyArrowPatch, Ellipse

from config import G, DT, NSUB, MAST_H_FAKTOR
from slider_defs import SLIDER_DEFS
from dynamics import Simulation
from rendering.scene import (boot_ansicht, welt_ansicht, dr,
                             zeichne_szene, wasser_schritt)


class QuaderApp:
    def __init__(self):
        plt.rcParams['font.size'] = 9
        self.fig = plt.figure(figsize=(13, 7.5))
        try:
            self.fig.canvas.manager.set_window_title(
                'Segelphysik - Schwimmender Koerper, 6 Freiheitsgrade')
        except Exception:
            pass
        self.ax = self.fig.add_axes([0.28, 0.05, 0.70, 0.90], projection='3d')
        # Unsichtbare 2D-Ebene exakt ueber der 3D-Axes: nimmt Kraftpfeile
        # und Labels auf und wird IMMER zuletzt gezeichnet.
        self.axov = self.fig.add_axes(self.ax.get_position().bounds)
        self.axov.set_zorder(10)

        # --------------------- MENUE (linke Spalte) ---------------------
        self.slider = {}
        y = 0.965
        for key, name, lo, hi, val, step in SLIDER_DEFS:
            sax = self.fig.add_axes([0.055, y, 0.175, 0.020])
            self.slider[key] = Slider(sax, name, lo, hi,
                                      valinit=val, valstep=step)
            self.slider[key].on_changed(self._dirty)
            y -= 0.028

        # Greifkraft-Regler deaktivieren (Funktion bleibt im Code):
        self.slider['Fk'].eventson = False
        self.slider['Fk'].label.set_text('Klick-Kraft [g] (aus)')
        self.slider['Fk'].ax.patch.set_alpha(0.35)

        # --- Aktions-Buttons ---
        for x0, name, fn in [(0.050, 'Neu starten', self._btn_reset),
                             (0.118, 'Gleichg.', self._btn_gg),
                             (0.183, 'Stoss', self._btn_stoss)]:
            bax = self.fig.add_axes([x0, 0.620, 0.060, 0.032])
            Button(bax, name).on_clicked(fn)

        # --- Zeit-Wiedergabe: Start/Stopp, Einzelschritt, Tempo, Richtung ---
        self.fig.text(0.055, 0.585, 'Wiedergabe (Zeit)', fontweight='bold')
        self.playing = True
        self.tempo = 1.0
        self.richtung = 'vor'
        self._acc = 0.0
        self._rew_acc = 0.0
        self.hist = []
        bax = self.fig.add_axes([0.050, 0.545, 0.085, 0.030])
        self.btn_play = Button(bax, '\u25a0 Stopp')
        self.btn_play.on_clicked(self._btn_play)
        bax = self.fig.add_axes([0.145, 0.545, 0.036, 0.030])
        Button(bax, '\u25c0').on_clicked(self._btn_schritt_zurueck)
        bax = self.fig.add_axes([0.188, 0.545, 0.036, 0.030])
        Button(bax, '\u25b6').on_clicked(self._btn_schritt_vor)
        cax = self.fig.add_axes([0.050, 0.400, 0.085, 0.130])
        self.rad_tempo = RadioButtons(cax, ['1x', '0.3x', '0.1x'])
        self.rad_tempo.on_clicked(self._set_tempo)
        cax = self.fig.add_axes([0.150, 0.435, 0.075, 0.070])
        self.rad_richtung = RadioButtons(cax, ['vor', 'zur\u00fcck'])
        self.rad_richtung.on_clicked(self._set_richtung)

        # --- Ansicht: Presets + freie Mausrotation ---
        self.fig.text(0.055, 0.370, 'Ansicht (Beobachter)', fontweight='bold')
        self.ansicht_name = 'Frei (Maus)'
        cax = self.fig.add_axes([0.050, 0.075, 0.140, 0.285])
        self.rad_ansicht = RadioButtons(
            cax, ['Frei (Maus)', 'Oben', 'Unten', 'Links', 'Rechts',
                  'Vorn', 'Hinten'])
        self.rad_ansicht.on_clicked(self._set_ansicht)

        self.txt = self.fig.text(0.975, 0.06, '', ha='right', va='bottom',
                                 fontsize=8, family='monospace',
                                 bbox=dict(boxstyle='round', fc='#eef3f6',
                                           ec='#99aabb', alpha=0.9))

        # Fahrt-Anzeige oben links im Bild (m/s und Knoten)
        self.txt_fahrt = self.fig.text(
            0.295, 0.985, '', ha='left', va='top', fontsize=11,
            fontweight='bold', family='monospace', color='#00325a',
            bbox=dict(boxstyle='round', fc='#e8f2fa', ec='#4a7fa5',
                      alpha=0.9), zorder=20)

        self.sim = None
        self.wasser = None
        self._w_off = np.zeros(2)     # Boot-Position in der Zeichen-Welt
        self._w_yaw = 0.0             # aufsummierter Gierwinkel
        self._dirty_flag = False
        self._neu()
        self.timer = self.fig.canvas.new_timer(interval=40)
        self.timer.add_callback(self._frame)
        self.timer.start()
        # --- Maus-Greif-Funktion: Kraft am angeklickten Koerperpunkt ---
        # Greiffunktion DEAKTIVIERT (nur abgeschaltet, Code bleibt
        # vollstaendig erhalten -> jederzeit wieder aktivierbar):
        self.grab_aktiv = False
        self.grab = None   # dict: r_body, p_welt, px0, F, richtung
        self.view_drag = None   # aktive View-Drehung (Frei-Modus)
        self._ax_cids = []
        self.fig.canvas.mpl_connect('button_press_event', self._on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self._on_release)

    def _ax_rotation_sperren(self, sperren):
        """View-Rotation waehrend des Greifens einfrieren."""
        if sperren:
            self._view0 = (self.ax.azim, self.ax.elev)
            self._gesperrt = True
        else:
            self._gesperrt = False

    def _proj_px(self, P3):
        """3D-Punkte (Nx3) -> Bildschirm-Pixel (Nx2)."""
        P3 = np.atleast_2d(P3)
        x2, y2, _ = proj3d.proj_transform(P3[:, 0], P3[:, 1], P3[:, 2],
                                          self.ax.get_proj())
        return self.ax.transData.transform(np.column_stack([x2, y2]))

    def _on_press(self, ev):
        if ev.inaxes not in (self.ax, self.axov) or ev.button != 1:
            return   # Klick ausserhalb der 3D-Ansicht (axov liegt UEBER ax
                     # und faengt daher die Klicks ab -> beide akzeptieren)
        if not getattr(self, 'grab_aktiv', False):
            # Greiffunktion aus: JEDER Klick dient nur der View-Rotation.
            if self.ansicht_name == 'Frei (Maus)':
                self.view_drag = (ev.x, ev.y, self.ax.azim, self.ax.elev)
            return
        s = self.sim
        R, p = s.R, s.p
        P = s.q.P @ R.T + p            # alle Voxel-Zentren (World)
        Pd = boot_ansicht(s, P)        # -> Boot-Ansicht
        px = self._proj_px(Pd)
        d2 = (px[:, 0] - ev.x)**2 + (px[:, 1] - ev.y)**2
        i = int(np.argmin(d2))
        if d2[i] > (0.12 * max(self.axov.bbox.width,
                               self.axov.bbox.height))**2:
            if self.ansicht_name == 'Frei (Maus)':
                self.view_drag = (ev.x, ev.y, self.ax.azim, self.ax.elev)
            return                      # Klick lag nicht am Koerper
        p_welt = welt_ansicht(s, Pd[i])[0]   # zurueckrechnen (World)
        cg_w = R @ s.q.c_body + p
        r_body = R.T @ (p_welt - cg_w)
        self.grab = {'r_body': r_body, 'p_welt': p_welt,
                     'px0': np.array([ev.x, ev.y]), 'F': np.zeros(3),
                     'richtung': np.array([0.0, 0.0, 1.0])}
        self._ax_rotation_sperren(True)
        self.view_drag = None

    def _on_motion(self, ev):
        if ev.x is None or ev.y is None:
            return
        if self.grab is None:
            if getattr(self, 'view_drag', None) is not None:
                x0, y0, az0, el0 = self.view_drag
                self.ax.azim = az0 - (ev.x - x0) * 0.5
                self.ax.elev = max(-90.0, min(90.0, el0 + (ev.y - y0) * 0.5))
            return
        g = self.grab
        d_px = np.array([ev.x, ev.y]) - g['px0']
        if np.linalg.norm(d_px) < 6:
            g['richtung'] = None
            return
        s = self.sim
        p_d = boot_ansicht(s, g['p_welt'])
        ex = self._proj_px(p_d + dr(s, [0.05, 0, 0])) - self._proj_px(p_d)
        ey = self._proj_px(p_d + dr(s, [0, 0.05, 0])) - self._proj_px(p_d)
        A = np.column_stack([ex[0], ey[0]])
        try:
            ab = np.linalg.solve(A, d_px)
        except np.linalg.LinAlgError:
            return
        welt = ab[0] * np.array([1.0, 0, 0]) + ab[1] * np.array([0, 1.0, 0])
        nl = np.linalg.norm(welt)
        if nl < 1e-9:
            return
        g['richtung'] = welt / nl

    def _on_release(self, ev):
        if self.grab is not None:
            self.grab = None
            self.sim.F_ext = np.zeros(3)
            self.sim.tau_ext = np.zeros(3)
            self._ax_rotation_sperren(False)
        self.view_drag = None

    def _scheiben_kraft_anwenden(self):
        """Kraft der Masttop-Scheibe: Angriffspunkt Mastspitze, Richtung
        horizontal im Welt-Azimut FW, Betrag FM [N]. Heelt die Yacht."""
        s = self.sim
        if s is None:
            return
        FM = float(self.slider['FM'].val)
        FW = np.radians(float(self.slider['FW'].val))
        if FM <= 1e-9:
            s.F_ext = np.zeros(3)
            s.tau_ext = np.zeros(3)
            return
        q = s.q
        # Bootrelativer Kraftwinkel: 0 deg = Bug (+x), 90 deg = Steuerbord
        # (-y), 180 deg = Heck, 270 deg = Backbord (+y). Die Bootachsen
        # werden dazu in die Weltebene projiziert -> die Kraft bleibt
        # IMMER horizontal, auch bei Kraengung/Trimm.
        x_w = s.R @ np.array([1.0, 0.0, 0.0]); x_w[2] = 0.0
        y_w = s.R @ np.array([0.0, 1.0, 0.0]); y_w[2] = 0.0
        nx, ny = np.linalg.norm(x_w), np.linalg.norm(y_w)
        if nx < 1e-9 or ny < 1e-9:      # Mast fast horizontal: skip
            s.F_ext = np.zeros(3)
            s.tau_ext = np.zeros(3)
            return
        x_w, y_w = x_w/nx, y_w/ny
        d_w = np.cos(FW)*x_w - np.sin(FW)*y_w
        F_w = FM * d_w
        r_top = np.array([float(q.c_body[0]), 0.0, q.H/2 + MAST_H_FAKTOR*q.L])
        s.F_ext = F_w
        # Hebelarm RELATIV zum CG (Newton-Euler bezieht Momente auf den
        # CG) -> kein Phantom-Moment mehr durch den CG-Versatz.
        s.tau_ext = s.R.T @ np.cross(s.R @ (r_top - q.c_body), F_w)

    def _grab_kraft_anwenden(self):
        """Pro Bild: Greifkraft + Moment aus aktueller Richtung setzen."""
        if self.grab is None:
            return
        g, s = self.grab, self.sim
        g_val = float(self.slider['Fk'].val)
        if g['richtung'] is None:
            s.F_ext = np.zeros(3)
            s.tau_ext = np.zeros(3)
            g['F'] = np.zeros(3)
            return
        F = g_val * G * s.q.m * g['richtung']
        r_welt = s.R @ g['r_body']
        cg_w = s.R @ s.q.c_body + s.p
        tau_welt = np.cross(r_welt, F)
        s.F_ext = F
        s.tau_ext = s.R.T @ tau_welt
        g['F'] = F
        g['p_welt'] = cg_w + r_welt

    def _werte(self):
        return {k: float(s.val) for k, s in self.slider.items()}

    def _dirty(self, *_):
        self._dirty_flag = True

    def _neu(self):
        w = self._werte()
        self.sim = Simulation(w['L'], w['B'], w['H'], w['rho'], int(w['n']),
                              w['lk'], w['tk'], w['rk'])
        self.sim.reset(heel_deg=25.0)
        self.wasser = None

    def _weiter_rechnen(self):
        """Parameterwechsel: Modell neu aufbauen, Zustand uebernehmen."""
        w = self._werte()
        alt = self.sim
        neu = Simulation(w['L'], w['B'], w['H'], w['rho'], int(w['n']),
                         w['lk'], w['tk'], w['rk'])
        if alt is not None:
            neu.p = alt.p.copy()
            neu.quat = alt.quat.copy()
            neu.v = alt.v.copy()
            neu.om = alt.om.copy()
            neu.t = alt.t
        neu.aktualisiere()
        self.grab = None
        self.wasser = None
        self.sim = neu
        if hasattr(self, 'hist'):
            self.hist.clear()

    def _btn_reset(self, *_):
        self._neu()

    def _btn_gg(self, *_):
        # FIX gegenueber quader_app_4: Slider-Werte lk/tk/rk mitgeben
        # (frueher stillschweigende Defaults -> falsche Geometrie).
        w = self._werte()
        self.sim = Simulation(w['L'], w['B'], w['H'], w['rho'], int(w['n']),
                              w['lk'], w['tk'], w['rk'])
        gg = self.sim.gleichgewicht()
        if gg:
            self.sim.setze(gg['z_c'], gg['roll'], gg['pitch'])
        if hasattr(self, 'hist'):
            self.hist.clear()

    def _btn_stoss(self, *_):
        self.sim.stoss(60.0)

    # ---------- Zeit-Wiedergabe (vor/zurueck, tempostaffelt) ----------
    def _snap(self):
        s = self.sim
        self.hist.append((s.p.copy(), s.quat.copy(), s.v.copy(),
                          s.om.copy(), s.t,
                          self._w_off.copy(), self._w_yaw))
        if len(self.hist) > 4000:
            self.hist.pop(0)

    def _pop(self):
        if not self.hist:
            return
        p, quat, v, om, t, off, yaw = self.hist.pop()
        s = self.sim
        s.p, s.quat, s.v, s.om, s.t = p, quat, v, om, t
        self._w_off, self._w_yaw = off, yaw
        s.aktualisiere()

    def _btn_play(self, *_):
        self.playing = not self.playing
        self.btn_play.label.set_text('\u25a0 Stopp' if self.playing
                                     else '\u25b6 Start')

    def _btn_schritt_vor(self, *_):
        self._grab_kraft_anwenden()
        self._scheiben_kraft_anwenden()
        self.sim.rw_soll = np.radians(float(self.slider['RW'].val))
        for _ in range(NSUB):
            self.sim.schritt()
        wasser_schritt(self, NSUB * DT)
        self._snap()

    def _btn_schritt_zurueck(self, *_):
        self._pop()

    def _set_tempo(self, label):
        self.tempo = {'1x': 1.0, '0.3x': 0.3, '0.1x': 0.1}[label]

    def _set_richtung(self, label):
        self.richtung = 'vor' if label == 'vor' else 'zurueck'

    # Bug = +x ('Vorn'), Heck = -x. Steuerbord (Rechts) = -y,
    # Backbord (Links) = +y. Oben/Unten = ueber Deck / Kielseite.
    ANSICHTEN = {'Vorn': (0.0, 0.0), 'Hinten': (180.0, 0.0),
                 'Rechts': (-90.0, 0.0), 'Links': (90.0, 0.0),
                 'Oben': (-60.0, 90.0), 'Unten': (-60.0, -90.0)}

    def _set_ansicht(self, label):
        self.ansicht_name = label
        if label in self.ANSICHTEN:
            az, el = self.ANSICHTEN[label]
            self.ax.azim, self.ax.elev = az, el

    def _frame(self):
        if getattr(self, '_gesperrt', False):
            self.ax.azim, self.ax.elev = getattr(self, '_view0',
                                                 (self.ax.azim, self.ax.elev))
        if self.ansicht_name in self.ANSICHTEN:
            az, el = self.ANSICHTEN[self.ansicht_name]
            self.ax.azim, self.ax.elev = az, el
        if self._dirty_flag:
            self._dirty_flag = False
            self._weiter_rechnen()
        elif self.playing:
            if self.richtung == 'vor':
                self._acc += self.tempo
                while self._acc >= 1.0:
                    self._acc -= 1.0
                    self._grab_kraft_anwenden()
                    self._scheiben_kraft_anwenden()
                    self.sim.rw_soll = np.radians(float(self.slider['RW'].val))
                    for _ in range(NSUB):
                        self.sim.schritt()
                    wasser_schritt(self, NSUB * DT)
                    self._snap()
            else:
                self._rew_acc += self.tempo
                while self._rew_acc >= 1.0:
                    self._rew_acc -= 1.0
                    self._pop()
        self._zeichnen()
        self._text()
        self.fig.canvas.draw_idle()

    def _zeichnen(self):
        ax = self.ax
        az0, el0 = ax.azim, ax.elev
        ax.clear()
        if self.ansicht_name in self.ANSICHTEN:
            az0, el0 = self.ANSICHTEN[self.ansicht_name]
        ax.view_init(elev=el0, azim=az0)
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

        # Overlay: Kraftvektoren (1 g = ca. 2 cm Screen)
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

        e_g = pfeil(CG, [0, 0, -1], px_pro_g, (0.85, 0.10, 0.10), shrink_pts)
        e_b = None
        if CB is not None and s.h['F_A'] > 1e-9:
            a_b = s.h['F_A'] / q.m
            e_b = pfeil(CB, [0, 0, 1], px_pro_g * a_b / G,
                        (0.10, 0.35, 0.90), 0.0)

        if CB is not None:
            ax.plot([CG[0], CB[0]], [CG[1], CB[1]], [CG[2], CB[2]],
                    'k--', lw=1, alpha=0.6)

        def label(px_end, text, farbe, dx_px, dy_px):
            f = px2frac(np.array([px_end[0] + dx_px, px_end[1] + dy_px]))
            self.axov.text(f[0], f[1], text, color=farbe, fontsize=9,
                           fontweight='bold', ha='left', va='center',
                           zorder=5)

        label(cg_px, 'CG', '#303030', 14, 14)
        if e_g is not None:
            label(e_g[1], 'G = %.1f kN' % (q.m * G / 1000), '#a00000', 10, -16)
        if e_b is not None:
            label(e_b[1], 'F_A = %.1f kN' % (s.h['F_A'] / 1000), '#003ca0',
                  10, 16)
        if CB is not None and s.h['F_A'] > 1e-9:
            label(zu_px(CB), 'CB', '#003ca0', 12, -14)

        if self.grab is not None and np.linalg.norm(self.grab['F']) > 1e-6:
            gv = self.grab
            a_g = np.linalg.norm(gv['F']) / q.m
            p_d = boot_ansicht(s, gv['p_welt'])
            pfeil(p_d, dr(s, gv['richtung']),
                  px_pro_g * a_g / G, (0.75, 0.0, 0.75), 0.0)
            label(zu_px(p_d + dr(s, gv['richtung']) * 0.01),
                  '%.1f g' % (a_g / G), '#900090', 10, 18)

        FM = float(self.slider['FM'].val)
        FW = np.radians(float(self.slider['FW'].val))
        if FM > 1e-9:
            x_w = s.R @ np.array([1.0, 0.0, 0.0]); x_w[2] = 0.0
            y_w = s.R @ np.array([0.0, 1.0, 0.0]); y_w[2] = 0.0
            nx, ny = np.linalg.norm(x_w), np.linalg.norm(y_w)
            if nx > 1e-9 and ny > 1e-9:
                f_r = (np.cos(FW)*(x_w/nx) - np.sin(FW)*(y_w/ny))
                pfeil(top_v, dr(s, f_r), px_pro_g * FM/1000.0,
                      (0.00, 0.70, 0.15), 0.0)
                label(zu_px(top_v + dr(s, f_r) * 0.02),
                      'F_M = %.0f N' % FM, '#008000', 10, 18)

        # --- Kiel- und Ruder-Kraftvektoren (Overlay) -----------------
        # Teal  = Kielkraft am Angriffspunkt der Flosse (spaeter:
        #         echter laterale Druckpunkt CLR),
        # Gold  = Ruderkraft am Ruder-Angriffspunkt.
        # Die pfeil()-Funktion projiziert den 3D-Vektor automatisch auf
        # die Bildebene -> es wird nur der zur Blickrichtung gehoerige
        # Anteil gezeichnet (gleiche Logik wie bei G/F_A/F_M).
        # Skala wie F_M: 1000 N entsprechen 1 g-Pfeillaenge (2 cm).
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
            f'L={q.L:g}  B={q.B:g}  H={q.H:g} m   rho={q.rho:g} kg/m^3   '
            f'm={q.m:.0f} kg   t={s.t:6.1f} s   '
            f'Fahrt={np.linalg.norm(s.v[:2]):4.2f} m/s   '
            f'Gieren={np.degrees(s.yaw):5.1f} grad   |   1 g = 2 cm',
            fontsize=9)

    def _text(self):
        s, q = self.sim, self.sim.q
        h = s.h
        zeilen = [f't              = {s.t:8.1f} s',
                  f'Masse m        = {q.m:8.0f} kg',
                  f'F_A (Auftrieb) = {h["F_A"]/1000:8.2f} kN',
                  f'G  (Gewicht)   = {q.m*G/1000:8.2f} kN',
                  f'F_netto (z)    = {(h["F_A"]-q.m*G)/1000:8.2f} kN']
        if s.sinkt:
            zeilen.append('>>> Dichte >= 1000: SINKT')
            if s.am_grund:
                zeilen.append('    liegt am Grund')
        else:
            def _w(x):
                return (np.degrees(x) + 180.0) % 360.0 - 180.0
            zeilen += [f'Tiefgang       = {h["tiefgang"]:8.3f} m',
                       f'Kraengung      = {_w(s.roll):8.1f} grad',
                       f'Trimm          = {_w(s.pitch):8.1f} grad',
                       f'Gieren         = {_w(s.yaw):8.1f} grad',
                       f'Pos x/y        = {s.p[0]:+7.3f}/{s.p[1]:+7.3f} m',
                       f'v x/y/z        = {s.v[0]:+6.2f}/{s.v[1]:+6.2f}/{s.v[2]:+6.2f} m/s',
                       f'|omega|       = {np.degrees(np.linalg.norm(s.om)):7.1f} grad/s']
            # --- Kraftbilanz horizontal (Weltframe): eingepraegte
            #     Mastkraft vs. Reaktionen aus Kiel/Ruder/Rumpf ---
            hd = getattr(s, 'hydrodyn', None)
            if hd is not None:
                F_sum = (s.F_ext + hd.F_kiel + hd.F_rud + hd.F_rumpf)
                zeilen += ['--- Kraftbilanz horizontal ---',
                           f'Abdrift       = {_w(hd.drift):8.1f} grad',
                           f'F_Mast   x/y  = {s.F_ext[0]:+7.0f}/{s.F_ext[1]:+7.0f} N',
                           f'F_Kiel   x/y  = {hd.F_kiel[0]:+7.0f}/{hd.F_kiel[1]:+7.0f} N',
                           f'F_Ruder  x/y  = {hd.F_rud[0]:+7.0f}/{hd.F_rud[1]:+7.0f} N',
                           f'F_Rumpf  x/y  = {hd.F_rumpf[0]:+7.0f}/{hd.F_rumpf[1]:+7.0f} N',
                           f'Summe    x/y  = {F_sum[0]:+7.0f}/{F_sum[1]:+7.0f} N']
        # Fahrt oben links (m/s und Knoten)
        vh = float(np.hypot(s.v[0], s.v[1]))
        self.txt_fahrt.set_text(
            f'Fahrt: {vh:4.2f} m/s  =  {vh*1.94384:4.2f} kn')
        self.txt.set_text('\n'.join(zeilen))

    def show(self):
        plt.show()
