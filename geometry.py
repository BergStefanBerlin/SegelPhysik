# ============================================================
# geometry.py - Parametrische Yacht-Geometrie (QuaderVoxel)
# ------------------------------------------------------------
# Rumpfform (spitzer Bug, volles Mittelschiff, breites Heck mit
# Transomspiegel, auslaufender Rumpfkiel) + FIN-KIEL mit BLEI-BULB
# + SPADE-RUDER.
# Masseneigenschaften ueber Monte-Carlo-Punktwolken (exakt
# y-symmetrisch, kalibriertes dV) -> EIN starrer Koerper.
# Konstruktionsziel (Winner 9.00, verifizierte Daten):
# LOA 9.0 m, Breite 2.96 m, Verdraengung 3300 kg, Ballast 1350 kg
# (41 %), Tiefgang 1.60 m, Fin+Bullet, Spaderuder.
# ============================================================
import numpy as np

from config import RHO_W


class QuaderVoxel:
    BR = 0.41          # Ballastquote (Ballast/Verdraengung)
    RHO_FIN = 7850.0   # Stahl
    RHO_RUD = 500.0    # Ruderbauweise (GFK/Schaum)

    def __init__(self, L, B, H, rho, n=24, lk=0.11, tk=1.0, rhok=11300.0):
        self.L, self.B, self.H = float(L), float(B), float(H)
        self.rho = float(rho)                 # eff. Rumpfstruktur-Dichte
        self.lk_f, self.tk_f, self.rhok = float(lk), float(tk), float(rhok)
        self.x_bug = 0.50 * self.L
        self.x_heck = -0.50 * self.L
        self.d_r = 0.035 * self.L             # Rumpfkiel-Tiefgang (Canoe)
        zt = self.H / 2                       # Deckhoehe
        p_sec = 0.45                          # Sektionsform (U/V-Mischung)

        # ---- Linienriss: Decksbreite und Kiellinie ----
        # NOTE: np.where berechnet BEIDE Zweige fuer alle Elemente -> bei
        # negativer Basis und Bruch-Exponenten entstehen NaNs (nur
        # Warnungen, aber laut). Deshalb: stueckweise Auswertung, bei der
        # jeder Zweig NUR auf seinem gueltigen Bereich gerechnet wird.
        def _stueckweise(x, f_vor, f_heck):
            x = np.asarray(x, dtype=float)
            skalar = (x.ndim == 0)
            xf = np.clip(np.atleast_1d(x), self.x_heck, self.x_bug)
            out = np.empty_like(xf)
            vor = xf >= 0.0
            if vor.any():
                out[vor] = f_vor(xf[vor])
            if (~vor).any():
                out[~vor] = f_heck(xf[~vor])
            return out[0] if skalar else out

        def ymax(x):
            return _stueckweise(
                x,
                lambda t: (self.B/2)*(1.0 - (t/self.x_bug)**1.6)**0.8,
                lambda t: (self.B/2)*(1.0 - 0.25*(t/self.x_heck)**2))

        def zb(x):
            return _stueckweise(
                x,
                lambda t: -self.d_r*(1.0 - (t/self.x_bug)**1.5)**0.7,
                lambda t: -self.d_r*(1.0 - 0.6*(t/self.x_heck)**1.5))

        self._ymax, self._zb = ymax, zb

        def inside_rumpf(x, y, z):
            ym = ymax(x); zbn = zb(x)
            u = (z - zbn)/np.maximum(zt - zbn, 1e-9)
            return ((x >= self.x_heck) & (x <= self.x_bug) &
                    (u >= 0.0) & (u <= 1.0) &
                    (np.abs(y) <= ym*np.maximum(u, 0.0)**p_sec + 1e-9))

        # ---- Anhaenge: Fin, Bulb, Ruder (Geometrie skaliert mit L) ----
        cf = self.lk_f * self.L               # Flossen-Wurzel-Sehne
        tf = self.tk_f * 0.105 * self.L       # Tiefe unter dem Rumpfboden
        self.xf0 = 0.02 * self.L              # Flossen-Anfang (vorderkante)
        z_fin_top = -float(zb(self.xf0 + 0.5*cf))   # Rumpfboden am Kiel

        def fin_geometrie(d):   # d = Tiefenanteil 0..1
            xle = self.xf0 + 0.18*cf*d        # Pfeilung der Vorderkante
            xte = self.xf0 + cf*(1.0 - 0.15*d)
            dicke = cf*(0.085 - 0.035*d)
            return xle, xte, dicke

        def inside_fin(x, y, z):
            d = (z_fin_top - z)/max(tf, 1e-9)
            xle, xte, dicke = fin_geometrie(np.clip(d, 0.0, 1.0))
            return ((d >= 0.0) & (d <= 1.0) & (x >= xle) & (x <= xte) &
                    (np.abs(y) <= dicke/2 + 1e-9))

        # Ruder (Spade): hinter der Flosse, freistehend. Die Oberkante
        # folgt dem AUSLAUFENDEN Rumpfboden (zb am Ruder-Mittel-x), damit
        # das Ruder wirklich am Rumpf ansetzt und nicht mit Spalt darunter
        # haengt; kleine 1-cm-Ueberlappung gegen Renderluecken.
        # Ganz ans Heck geschoben: Hinterkante knapp vor dem Transomspiegel
        # (2 % L Luft), das Blatt liegt damit moeglichst weit achtern.
        cr, tr = 0.55*cf, 0.70*tf
        xr0 = self.x_heck - 0.02*self.L   # Vorderkante 2 % L vor dem Spiegel
        z_rud_top = float(self._zb(xr0 + 0.5*cr)) + 0.01

        def inside_rud(x, y, z):
            d = (z_rud_top - z)/max(tr, 1e-9)
            dc = np.clip(d, 0.0, 1.0)
            xle = xr0 + 0.15*cr*dc
            xte = xr0 + cr*(1.0 - 0.10*dc)
            return ((d >= 0.0) & (d <= 1.0) & (x >= xle) & (x <= xte) &
                    (np.abs(y) <= cr*0.05/2*(1.0-0.3*dc) + 1e-9))

        # ---- Monte-Carlo-Punktwolken (exakt y-symmetrisch) ----
        def mc_wolke(inside, bbox, N, rho_wert):
            x0, x1, y1, z0, z1 = bbox
            rng = np.random.default_rng(12345)
            x = rng.uniform(x0, x1, N)
            y = rng.uniform(0.0, y1, N)       # nur +y, dann spiegeln
            z = rng.uniform(z0, z1, N)
            m_ = inside(x, y, z)
            x, y, z = x[m_], y[m_], z[m_]
            P = np.stack([x, y, z], axis=1)
            P = np.vstack([P, P*np.array([1.0, -1.0, 1.0])])
            V = (len(x)/N)*(x1-x0)*y1*(z1-z0)*2.0
            dv = V/max(len(P), 1)
            return P, dv, np.full(len(P), float(rho_wert)), V

        self.P, self.dV, rho_arr, self.V = mc_wolke(
            inside_rumpf, (self.x_heck, self.x_bug, self.B/2,
                           -self.d_r - 1e-9, zt), 150000, self.rho)

        Pf, dVf, rhof, V_fin = mc_wolke(
            inside_fin, (self.xf0 - 0.02, self.xf0 + cf + 0.02, 0.06,
                         z_fin_top - tf - 0.01, z_fin_top + 0.01),
            60000, self.RHO_FIN)
        Pr, dVr, rhor, V_rud = mc_wolke(
            inside_rud, (xr0 - 0.02, xr0 + cr + 0.02, 0.04,
                         z_rud_top - tr - 0.01, z_rud_top + 0.01),
            30000, self.RHO_RUD)

        # Bulb-Volumen so loesen, dass Ballastquote = BR gilt:
        num = (self.BR*(self.rho*self.V + self.RHO_RUD*V_rud)/(1-self.BR)
               - self.RHO_FIN*V_fin)
        V_b = max(num/self.rhok, 0.004)
        a_b = 0.70*cf                            # halbe Bullet-Laenge
        r_b = (3*V_b/(4*np.pi*a_b))**0.5         # Bullet-Radius
        self.xb_bulb = self.xf0 + 0.65*cf        # Mitte (leicht achtern)
        self.zb_bulb = z_fin_top - tf - 0.6*r_b  # ueberlappt Flossenende

        def inside_bulb(x, y, z):
            return (((x-self.xb_bulb)/a_b)**2 + (y/r_b)**2 +
                    ((z-self.zb_bulb)/r_b)**2) <= 1.0 + 1e-9

        Pb, dVb, rhob, V_b_mc = mc_wolke(
            inside_bulb, (self.xb_bulb-a_b-0.02, self.xb_bulb+a_b+0.02,
                          r_b+0.02, self.zb_bulb-r_b-0.02,
                          self.zb_bulb+r_b+0.02), 80000, self.rhok)

        # Anhang-Wolke (Fin + Bulb + Ruder) mit Punktdichten
        self.Pk = np.vstack([Pf, Pb, Pr])
        self.rhok_arr = np.concatenate([rhof, rhob, rhor])
        self.Vk = V_fin + V_b_mc + V_rud
        self.dVk = self.Vk/len(self.Pk)
        self.rhok = self.rhok_arr                # Array je Punkt

        # ---- Kiel-Rueckverschiebung (Trimm-Kalibrierung) -------------
        # Fin+Bulb werden GEMEINSAM so weit nach achtern (-x) verschoben,
        # dass im Ruhegleichgewicht (even keel) CB lotrecht unter CG
        # liegt -> kein Trimmmoment, Deck waagerecht, Mast senkrecht.
        # Gewichtung EXAKT wie in hydro(): uniformes dV bzw. dVk je Wolke.
        # Das Ruder bleibt am Transomspiegel (wird nicht verschoben).
        _n_fb = len(Pf) + len(Pb)
        _x_all = np.concatenate([self.P[:, 0], self.Pk[:, 0]])
        _z_all = np.concatenate([self.P[:, 2], self.Pk[:, 2]])
        _w_all = np.concatenate([np.full(len(self.P), self.dV),
                                 np.full(len(self.Pk), self.dVk)])
        _rho_all = np.concatenate([np.full(len(self.P), self.rho),
                                   self.rhok_arr])
        _m_ges = float((_rho_all * _w_all).sum())
        _V_ziel = _m_ges / RHO_W

        def _trimm_arm(dx):
            """CG_x - CB_x bei even keel; Schwimmhoehe per Bisektion so,
            dass das Tauchvolumen exakt der Verdraengung entspricht."""
            x = _x_all.copy()
            x[len(self.P):len(self.P) + _n_fb] += dx   # nur Fin+Bulb
            lo, hi = float(_z_all.min()) - 1.0, float(_z_all.max())
            for _ in range(55):
                mit = 0.5*(lo + hi)
                if float(_w_all[_z_all < mit].sum()) < _V_ziel:
                    lo = mit
                else:
                    hi = mit
            sub = _z_all < 0.5*(lo + hi)
            cb_x = float((x[sub]*_w_all[sub]).sum())/_w_all[sub].sum()
            cg_x = float((x*_rho_all*_w_all).sum())/_m_ges
            return cg_x - cb_x

        _d0, _d1 = 0.0, -0.30
        _f0, _f1 = _trimm_arm(_d0), _trimm_arm(_d1)
        for _ in range(15):
            if abs(_f1) < 1e-10:
                break
            _den = _f1 - _f0
            _d2 = (_d1 - _f1*(_d1 - _d0)/_den if abs(_den) > 1e-14
                   else _d1 - 0.05)
            _d0, _f0 = _d1, _f1
            _d1, _f1 = _d2, _trimm_arm(_d2)
        self.kiel_dx = float(np.clip(_d1, -0.45*self.L, 0.10*self.L))
        # Anwenden: Pk wurde via vstack KOPIERT -> hier direkt verschreiben
        self.Pk[:_n_fb, 0] += self.kiel_dx
        Pf[:, 0] += self.kiel_dx
        Pb[:, 0] += self.kiel_dx
        self.xf0 += self.kiel_dx
        self.xb_bulb += self.kiel_dx

        # ---- Kombinierte Masseneigenschaften ----
        m_r = self.rho*self.V
        m_k = float((self.rhok_arr*self.dVk).sum())
        m_ru = self.RHO_RUD*V_rud
        self.m_ballast = m_k - m_ru              # Fin+Bulb = Ballast
        self.ballast_anteil = self.m_ballast/(m_r + m_k + m_ru)
        self.m = m_r + m_k          # Ruder steckt in m_k bereits (rhok_arr)
        c_r = self.rho*self.dV*self.P.sum(axis=0)   # SUMME, nicht Mittelwert
        c_k = ((self.rhok_arr*self.dVk)[:, None]*self.Pk).sum(axis=0)
        self.c_body = (c_r + c_k)/self.m

        I = np.zeros((3, 3))
        for Pw, dv, rh in ((self.P, self.dV, np.full(len(self.P), self.rho)),
                           (self.Pk, self.dVk, self.rhok_arr)):
            r = Pw - self.c_body
            r2 = (r**2).sum(axis=1)
            wgt = rh*dv
            for i in range(3):
                for j in range(3):
                    if i == j:
                        I[i, i] += np.sum((r2 - r[:, i]**2)*wgt)
                    else:
                        I[i, j] += -np.sum(r[:, i]*r[:, j]*wgt)
        self.I_num = I

        # ---- Tragfluegel-Kennzahlen (fuer Hydrodynamik) -------------
        cf_f = self.lk_f * self.L
        tf_f = self.tk_f * 0.105 * self.L
        self.t_fin, self.t_rud = tf_f, 0.70*tf_f
        self.A_fin = max(tf_f * 0.835 * cf_f, 1e-4)
        self.AR_fin = max(tf_f*tf_f/self.A_fin, 0.2)
        self.r_kiel = np.array([self.xf0 + 0.45*cf_f, 0.0,
                                z_fin_top - 0.55*tf_f])
        cr_r, tr_r = 0.55*cf_f, 0.70*tf_f
        self.A_rud = max(tr_r * 0.875 * cr_r, 1e-4)
        self.AR_rud = max(tr_r*tr_r/self.A_rud, 0.2)
        self.r_rud = np.array([xr0 + 0.50*cr_r, 0.0,
                               z_rud_top - 0.50*tr_r])

        # ---- Flaechnetz zum Zeichnen (Stationen x Ring) ----
        NS, MS = 26, 6
        xs = np.linspace(self.x_heck, self.x_bug, NS)
        ring = []
        for x in xs:
            ym = float(ymax(x)); zbn = float(zb(x))
            for u in np.linspace(1.0, 0.0, MS):          # Backbord oben->kiel
                ring.append([x, ym*u**p_sec, zbn + u*(zt - zbn)])
            for u in np.linspace(0.0, 1.0, MS)[1:]:      # Steuerbord kiel->oben
                ring.append([x, -ym*u**p_sec, zbn + u*(zt - zbn)])
        self.netz = np.array(ring).reshape(NS, 2*MS - 1, 3)
        # Anhang-Netze (Flossen-/Ruder-Box, Bullet-Ellipsoid)
        d0, d1 = 0.0, 1.0
        xl0, xt0, dk0 = fin_geometrie(d0); xl1, xt1, dk1 = fin_geometrie(d1)
        self.fin_box = np.array([
            [xl0,-dk0/2,z_fin_top], [xt0,-dk0/2,z_fin_top],
            [xt0, dk0/2,z_fin_top], [xl0, dk0/2,z_fin_top],
            [xl1,-dk1/2,z_fin_top-tf], [xt1,-dk1/2,z_fin_top-tf],
            [xt1, dk1/2,z_fin_top-tf], [xl1, dk1/2,z_fin_top-tf]])
        xrle0, xrte0 = xr0, xr0 + cr
        xrle1, xrte1 = xr0 + 0.15*cr, xr0 + cr*0.9
        dr0, dr1 = cr*0.05/2, cr*0.035/2
        self.rud_box = np.array([
            [xrle0,-dr0,z_rud_top], [xrte0,-dr0,z_rud_top],
            [xrte0, dr0,z_rud_top], [xrle0, dr0,z_rud_top],
            [xrle1,-dr1,z_rud_top-tr], [xrte1,-dr1,z_rud_top-tr],
            [xrte1, dr1,z_rud_top-tr], [xrle1, dr1,z_rud_top-tr]])
        # Bullet-Ellipsoid-Netz
        nu, nv = 14, 8
        bu = np.linspace(0, 2*np.pi, nu+1)
        bv = np.linspace(0, np.pi, nv+1)
        BU, BV = np.meshgrid(bu, bv)
        self.bulb_netz = np.stack([
            self.xb_bulb + a_b*np.cos(BU)*np.sin(BV),
            r_b*np.sin(BU)*np.sin(BV),
            self.zb_bulb + r_b*np.cos(BV)], axis=-1)
