# ============================================================
# scene.py - 3D-Szene (Wasser, Rumpf, Mast, Scheibe, Pfeile)
# ------------------------------------------------------------
# Enthaelt die bootfesten Ansichts-Transformationen (das Boot steht
# im Bild still, Fahrt/Gieren zeigt das Wasserfeld) und den Aufbau
# der tiefensortierten Polygonsammlung. Die Kraftpfeile des Overlays
# bleiben in app.py (brauchen GUI-Zugriff auf Slider/Grab).
# ============================================================
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from config import PFEIL_VOR, MAST_H_FAKTOR, W_OPTO
from water import WasserFeld
from rendering.arrows import _pfeil_polys, _clip_z


def boot_ansicht(sim, Pw):
    """World-Punkte -> Boot-Ansicht: horizontale Position des Boots
    und Gierwinkel werden herausgerechnet (z bleibt unveraendert).
    Akzeptiert (...,3)-Arrays und einzelne Punkte."""
    yaw = sim.yaw
    cy, sy_ = np.cos(yaw), np.sin(yaw)
    cg = sim.R @ sim.q.c_body + sim.p     # Welt-Position des Schwerpunkts
    Q = np.asarray(Pw, float)
    dx = Q[..., 0] - cg[0]
    dy = Q[..., 1] - cg[1]
    out = np.array(Q, dtype=float, copy=True)
    out[..., 0] = cy*dx + sy_*dy
    out[..., 1] = -sy_*dx + cy*dy
    return out


def welt_ansicht(sim, Pd):
    """Boot-Ansicht -> World (inverse Transformation)."""
    yaw = sim.yaw
    cy, sy_ = np.cos(yaw), np.sin(yaw)
    cg = sim.R @ sim.q.c_body + sim.p
    Q = np.atleast_2d(np.asarray(Pd, float))
    out = np.array(Q, dtype=float, copy=True)
    out[:, 0] = cg[0] + cy*Q[:, 0] - sy_*Q[:, 1]
    out[:, 1] = cg[1] + sy_*Q[:, 0] + cy*Q[:, 1]
    return out


def dr(sim, v):
    """Richtung/Vektor in die Boot-Ansicht drehen (nur horizontal)."""
    yaw = sim.yaw
    cy, sy_ = np.cos(yaw), np.sin(yaw)
    V = np.asarray(v, float)
    out = np.array(V, dtype=float, copy=True)
    out[..., 0] = cy*V[..., 0] + sy_*V[..., 1]
    out[..., 1] = -sy_*V[..., 0] + cy*V[..., 1]
    return out


def wasser_schritt(app, dt):
    """Wasserzeichen-Welt pro Zeitschritt fortbewegen: Translation
    entgegen der Fahrt, Rotation entgegen dem Gieren."""
    if dt <= 0.0:
        return
    s = app.sim
    om_w = s.R @ s.om                 # Winkelgeschwindigkeit im World
    app._w_yaw += om_w[2] * dt
    # Optischer Boost: Wasserzeichen wandern sichtbar schneller als die
    # reale Fahrt (reine Anzeige-Verstaerkung, Physik bleibt unberuehrt).
    app._w_off = app._w_off + W_OPTO * s.v[:2] * dt


def zeichne_szene(app, ax, axov):
    """Baut die komplette 3D-Szene in ax auf (tiefensortierte Sammlung).
    app muss bereitstellen: sim, wasser, _w_off, _w_yaw.
    Liefert ein dict mit Referenzpunkten fuer das Overlay:
      CG, CB, top_v (Mastspitze), r (Darstellungsradius)."""
    ax.clear()
    s = app.sim
    q = s.q

    # BOOTFESTES Bild-Koordinatensystem: Das Boot steht IMMER still
    # (CG bei x=y=0, Wasseroberflaeche z=0). Nur Roll/Pitch/Einsinken
    # veraendern die Geometrie; Fahrt und Gieren zeigt das Wasserfeld.
    r = 0.75 * max(q.L, q.B, q.H)
    # Darstellungsraum bis ueber die Mastspitze erweitern:
    z_top = q.H/2 + MAST_H_FAKTOR*q.L + 0.12*r
    zmax = max(r, z_top)
    zmin = s.z_bed - 0.3 if (s.sinkt or s.am_grund) else -r
    ax.set_xlim(-r, r); ax.set_ylim(-r, r)
    ax.set_zlim(zmin, zmax)
    ax.set_box_aspect((1, 1, (zmax - zmin) / (2 * r)))
    ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); ax.set_zlabel('z [m]')

    # --- alle Polygone in EINER tiefensortierten Sammlung ---
    polys, fc, ec, lw = [], [], [], []

    # 1) Wasservolumen (halbdurchsichtig, unten dunkler).
    w_seite = (0.086, 0.29, 0.47, 0.20)
    w_boden = (0.03, 0.15, 0.28, 0.30)
    w_flache = (0.18, 0.52, 0.76, 0.38)
    NK = 14                       # Kacheln pro Richtung
    ka = np.linspace(-r, r, NK + 1)
    for i in range(NK):
        for j in range(NK):
            polys.append(np.array([
                [ka[i],  ka[j],  0], [ka[i+1], ka[j],  0],
                [ka[i+1], ka[j+1], 0], [ka[i],  ka[j+1], 0]]))
            fc.append(w_flache); ec.append('none'); lw.append(0)
    for i in range(NK):
        for j in range(NK):
            polys.append(np.array([
                [ka[i],  ka[j],  zmin], [ka[i+1], ka[j],  zmin],
                [ka[i+1], ka[j+1], zmin], [ka[i],  ka[j+1], zmin]]))
            fc.append(w_boden); ec.append('none'); lw.append(0)
    for sx in (-r, r):
        for j in range(NK):
            polys.append(np.array([[sx, ka[j], 0], [sx, ka[j+1], 0],
                                   [sx, ka[j+1], zmin], [sx, ka[j], zmin]]))
            fc.append(w_seite); ec.append('none'); lw.append(0)
    for sy in (-r, r):
        for j in range(NK):
            polys.append(np.array([[ka[j], sy, 0], [ka[j+1], sy, 0],
                                   [ka[j+1], sy, zmin], [ka[j], sy, zmin]]))
            fc.append(w_seite); ec.append('none'); lw.append(0)

    # 2) YAcht-Rumpf + Kiel + Bulb + Ruder: Geometrie in WORLD, dann
    #    in die Boot-Ansicht heben (Fahrt/Gieren herausgerechnet).
    WeltN = boot_ansicht(s, q.netz @ s.h['R'].T + s.p)
    NS = WeltN.shape[0]
    holz = (0.78, 0.61, 0.42, 1.0)
    nass = (0.87, 0.74, 0.56, 1.0)
    wl_segs = []
    for i in range(NS - 1):
        for j in range(WeltN.shape[1] - 1):
            quad = np.array([WeltN[i, j], WeltN[i, j+1],
                             WeltN[i+1, j+1], WeltN[i+1, j]])
            if abs(quad[:, 2].mean()) > 1.6 * max(q.H, 1e-9):
                continue
            dry = _clip_z(quad, False)
            wet = _clip_z(quad, True)
            if dry is not None:
                polys.append(dry); fc.append(holz)
                ec.append('#7a5c38'); lw.append(0.25)
            if wet is not None:
                polys.append(wet); fc.append(nass)
                ec.append('#7a5c38'); lw.append(0.25)
            pts = []
            for k in range(len(quad)):
                aa, bb2 = quad[k], quad[(k + 1) % len(quad)]
                if (aa[2] < 0) != (bb2[2] < 0):
                    t = aa[2] / (aa[2] - bb2[2])
                    pts.append(aa + t * (bb2 - aa))
            if len(pts) == 2:
                wl_segs.append((pts[0], pts[1]))
    # Deck als geschlossene Flaeche oben drauf:
    top = WeltN[:, 0]
    bot = WeltN[:, -1]
    for i in range(NS - 1):
        quad = np.array([top[i], top[i+1], bot[i+1], bot[i]])
        polys.append(quad); fc.append((0.72, 0.55, 0.36, 1.0))
        ec.append('#6b4f30'); lw.append(0.25)

    # --- Fin-Kiel (Box mit Pfeilung) ---
    WeltF = boot_ansicht(s, q.fin_box @ s.h['R'].T + s.p)
    FF = [[0,1,2,3], [4,5,6,7],
          [0,1,5,4], [1,2,6,5], [2,3,7,6], [3,0,4,7]]
    fin_farbe = (0.30, 0.32, 0.38, 1.0)
    fin_nass = (0.42, 0.45, 0.52, 1.0)
    for f in FF:
        poly = WeltF[f]
        dry = _clip_z(poly, False)
        wet = _clip_z(poly, True)
        if dry is not None:
            polys.append(dry); fc.append(fin_farbe); ec.append('k'); lw.append(0.6)
        if wet is not None:
            polys.append(wet); fc.append(fin_nass); ec.append('k'); lw.append(0.6)

    # --- Bulb (Ellipsoid-Netz) ---
    WeltB = boot_ansicht(s, q.bulb_netz @ s.h['R'].T + s.p)
    bulb_farbe = (0.24, 0.26, 0.31, 1.0)
    bulb_nass = (0.36, 0.39, 0.45, 1.0)
    nb = WeltB.shape[0]
    for i in range(nb - 1):
        for j in range(WeltB.shape[1] - 1):
            quad = np.array([WeltB[i, j], WeltB[i, j+1],
                             WeltB[i+1, j+1], WeltB[i+1, j]])
            dry = _clip_z(quad, False)
            wet = _clip_z(quad, True)
            if dry is not None:
                polys.append(dry); fc.append(bulb_farbe)
                ec.append('#1a1c22'); lw.append(0.2)
            if wet is not None:
                polys.append(wet); fc.append(bulb_nass)
                ec.append('#1a1c22'); lw.append(0.2)

    # --- Spade-Ruder ---
    WeltR = boot_ansicht(s, q.rud_box @ s.h['R'].T + s.p)
    rud_farbe = (0.45, 0.47, 0.52, 1.0)
    rud_nass = (0.58, 0.60, 0.65, 1.0)
    for f in FF:
        poly = WeltR[f]
        dry = _clip_z(poly, False)
        wet = _clip_z(poly, True)
        if dry is not None:
            polys.append(dry); fc.append(rud_farbe); ec.append('k'); lw.append(0.6)
        if wet is not None:
            polys.append(wet); fc.append(rud_nass); ec.append('k'); lw.append(0.6)

    # --- Mast (starr mit der Yacht verbunden): steht senkrecht auf dem
    #     Deck UEBER DEM RUHESCHWERPUNKT (CG). Reine Zeichnung, keine
    #     Masse/Belastung in der Physik. Beim Kraengen kippt der Mast
    #     starr mit dem Rumpf mit. ---
    mast_h = MAST_H_FAKTOR * q.L            # Masthoehe ueber Deck
    wm = max(0.045, 0.008 * q.L)            # halbe Mastbreite
    xm = float(q.c_body[0])                 # CG-x in Koerperkoords
    z_deck = q.H / 2                        # Deckhoehe (Koerperframe)
    mb = np.array([
        [xm-wm, -wm, z_deck], [xm+wm, -wm, z_deck],
        [xm+wm,  wm, z_deck], [xm-wm,  wm, z_deck],
        [xm-wm, -wm, z_deck+mast_h], [xm+wm, -wm, z_deck+mast_h],
        [xm+wm,  wm, z_deck+mast_h], [xm-wm,  wm, z_deck+mast_h]])
    WeltM = boot_ansicht(s, mb @ s.h['R'].T + s.p)
    mast_f = (0.55, 0.56, 0.60, 1.0)       # trocken
    mast_n = (0.68, 0.70, 0.74, 1.0)       # nass
    for f in FF:
        poly = WeltM[f]
        dry = _clip_z(poly, False)
        wet = _clip_z(poly, True)
        if dry is not None:
            polys.append(dry); fc.append(mast_f); ec.append('k'); lw.append(0.5)
        if wet is not None:
            polys.append(wet); fc.append(mast_n); ec.append('k'); lw.append(0.5)

    # --- Krafteinwirkungsscheibe an der Mastspitze ---
    rs_d = 0.10 * q.L                       # Scheibenradius
    top_b = np.array([xm, 0.0, z_deck + mast_h])   # Mastspitze (Koerper)
    top_w = s.R @ top_b + s.p                      # Welt
    top_v = boot_ansicht(s, np.array([top_w]))[0]  # Boot-Ansicht
    phi = np.linspace(0.0, 2.0*np.pi, 33)
    ring_w = np.column_stack([top_w[0] + rs_d*np.cos(phi),
                              top_w[1] + rs_d*np.sin(phi),
                              np.full_like(phi, top_w[2])])
    ring_v = boot_ansicht(s, ring_w)
    polys.append(ring_v)
    fc.append((0.15, 0.80, 0.25, 0.28))     # transparent gruen
    ec.append((0.00, 0.55, 0.10, 0.90)); lw.append(1.2)
    # Kreuz-Markierung der Scheibenmitte
    for ax_ in ((1, 0), (0, 1)):
        q4 = np.array([[top_w[0]-ax_[0]*rs_d, top_w[1]-ax_[1]*rs_d, top_w[2]],
                       [top_w[0]+ax_[0]*rs_d, top_w[1]+ax_[1]*rs_d, top_w[2]]])
        q4_v = boot_ansicht(s, q4)
        d4 = q4_v[1] - q4_v[0]
        L4 = np.linalg.norm(d4[:2])
        if L4 > 1e-9:
            n4 = np.array([-d4[1], d4[0]])/L4 * (0.006*r)
            polys.append(np.array([
                [q4_v[0][0]-n4[0], q4_v[0][1]-n4[1], q4_v[0][2]],
                [q4_v[0][0]+n4[0], q4_v[0][1]+n4[1], q4_v[0][2]],
                [q4_v[1][0]+n4[0], q4_v[1][1]+n4[1], q4_v[1][2]],
                [q4_v[1][0]-n4[0], q4_v[1][1]-n4[1], q4_v[1][2]]]))
            fc.append((0.00, 0.55, 0.10, 0.75)); ec.append('none'); lw.append(0)

    # 3) Wasserlinie als kraeftige Markierung direkt am Rumpf:
    for p1, p2 in wl_segs:
        d = p2 - p1
        nv = np.array([-d[1], d[0], 0.0])
        nl = np.linalg.norm(nv)
        if nl < 1e-12:
            continue
        nv *= (0.014 * r) / nl
        dz = 0.006 * r
        band = np.array([p1 + [0, 0, dz], p2 + [0, 0, dz],
                         p2 + nv + [0, 0, dz], p1 + nv + [0, 0, dz]])
        polys.append(band)
        fc.append((0.0, 0.85, 1.0, 0.85)); ec.append('#00d5ff'); lw.append(0.8)

    # 4) CB-Markierung (Raute) - Teil der tiefensortierten Szene.
    CG = np.array([0.0, 0.0, s.p[2]])
    CG_w = s.R @ q.c_body + s.p              # World-CG (fuer Physik)
    CB = boot_ansicht(s, np.array([s.h['CB'] + CG_w]))[0] \
         if s.h['CB'] is not None else None
    if CB is not None:
        d = 0.035 * r
        sp = [CB + [d, 0, 0], CB - [d, 0, 0], CB + [0, d, 0],
              CB - [0, d, 0], CB + [0, 0, d], CB - [0, 0, d]]
        tris = [[sp[0], sp[2], sp[4]], [sp[0], sp[4], sp[3]],
                [sp[0], sp[3], sp[5]], [sp[0], sp[5], sp[2]],
                [sp[1], sp[2], sp[5]], [sp[1], sp[5], sp[3]],
                [sp[1], sp[3], sp[4]], [sp[1], sp[4], sp[2]]]
        polys += tris
        fc += [(0.10, 0.35, 0.90, 0.95)] * 8
        ec += ['#103070'] * 8
        lw += [0.4] * 8

    # --- Wasserzeichen als Polygone IN der tiefensortierten Szene ---
    if app.wasser is None:
        app.wasser = WasserFeld(r)
    pkt, sa, sb, pkt_t = app.wasser.ansicht(app._w_off, app._w_yaw)
    z_w = app.wasser.z
    g_p = 0.007 * r          # Halbkante Oberflaechen-Punkt
    g_s = 0.0022 * r         # halbe Strichbreite
    g_t = 0.009 * r          # Halbkante Tiefen-Punkt
    for xy in pkt:
        polys.append(np.array([
            [xy[0]-g_p, xy[1]-g_p, z_w], [xy[0]+g_p, xy[1]-g_p, z_w],
            [xy[0]+g_p, xy[1]+g_p, z_w], [xy[0]-g_p, xy[1]+g_p, z_w]]))
        fc.append((0.80, 0.92, 1.00, 0.60)); ec.append('none'); lw.append(0)
    for a2, b2 in zip(sa, sb):
        d2 = b2 - a2
        L2 = np.hypot(d2[0], d2[1])
        if L2 < 1e-9:
            continue
        n2 = np.array([-d2[1], d2[0]]) / L2 * g_s
        polys.append(np.array([
            [a2[0]-n2[0], a2[1]-n2[1], z_w],
            [a2[0]+n2[0], a2[1]+n2[1], z_w],
            [b2[0]+n2[0], b2[1]+n2[1], z_w],
            [b2[0]-n2[0], b2[1]-n2[1], z_w]]))
        fc.append((0.80, 0.92, 1.00, 0.50)); ec.append('none'); lw.append(0)
    for p3 in pkt_t:
        polys.append(np.array([
            [p3[0]-g_t, p3[1]-g_t, p3[2]], [p3[0]+g_t, p3[1]-g_t, p3[2]],
            [p3[0]+g_t, p3[1]+g_t, p3[2]], [p3[0]-g_t, p3[1]+g_t, p3[2]]]))
        fc.append((0.30, 0.85, 0.75, 0.55)); ec.append('none'); lw.append(0)

    # ---- Dynamische Kurs-/Drehpfeile in der Wasserebene vor dem Bug:
    # ein gerader Pfeil zeigt die Fahrtrichtung (Laenge ~ Fahrt), ein
    # gebogener Pfeil verbiegt sich je nach Drehgeschwindigkeit (Gieren)
    # nach Backbord oder Steuerbord. Beide liegen knapp ueber z=0.----
    om_w = s.R @ s.om
    yaw_dot = float(om_w[2])            # Drehgeschw. um Hochachse [rad/s]
    v_h = np.array([s.v[0], s.v[1], 0.0])
    sp_h = float(np.linalg.norm(v_h))
    x_b = s.R @ np.array([1.0, 0.0, 0.0]); x_b[2] = 0.0
    nx = np.linalg.norm(x_b)
    if nx > 1e-9:
        x_b = x_b / nx
        z_p = 0.02                       # Hoehe ueber Wasser
        x0 = PFEIL_VOR * q.L             # Ansatzpunkt vorn
        # --- gerader Kurspfeil: Richtung = Fahrt (oder Bug bei Stillstand)
        if sp_h > 0.02:
            d_k = v_h / sp_h
        else:
            d_k = x_b.copy()
        L_k = min(0.9 + 0.55 * sp_h, 3.2)   # Laenge mit Fahrt
        pk = _pfeil_polys([x0, 0.0, z_p], d_k, L_k, 0.055 * q.B)
        for po in pk:
            polys.append(po)
            fc.append((1.00, 0.62, 0.00, 0.90)); ec.append('#b34700')
            lw.append(0.5)
        # --- Biegepfeil: Verbiegung ~ Giergeschwindigkeit ---
        b = np.clip(yaw_dot / 0.60, -1.0, 1.0)   # normiert ~34 deg/s
        if abs(b) > 0.02:
            n_seg = 7
            Lb = 1.9
            pts = []
            for i2 in range(n_seg + 1):
                t2 = i2 / n_seg
                q2 = b * 1.15 * t2**2    # Parabel-Biegung quer
                pts.append([x0 + t2 * Lb,
                            +q2 * q.L * 0.16, z_p])
            pts = np.array(pts)
            breit = 0.050 * q.B
            for i2 in range(n_seg):
                a3, b3 = pts[i2], pts[i2 + 1]
                t3 = a3 - b3
                nv = np.array([-t3[1], t3[0], 0.0])
                nl = np.linalg.norm(nv)
                if nl > 1e-12:
                    nv = nv / nl * breit
                    polys.append(np.array([
                        [a3[0]+nv[0], a3[1]+nv[1], z_p],
                        [b3[0]+nv[0], b3[1]+nv[1], z_p],
                        [b3[0]-nv[0], b3[1]-nv[1], z_p],
                        [a3[0]-nv[0], a3[1]-nv[1], z_p]]))
                    fc.append((0.95, 0.20, 0.20, 0.90))
                    ec.append('#8b0000'); lw.append(0.4)
            ric = pts[-1] - pts[-2]
            rl = np.linalg.norm(ric)
            if rl > 1e-9:
                pk2 = _pfeil_polys(pts[-1], ric/rl, 0.42, 0.05*q.B)
                for po in pk2:
                    polys.append(po)
                    fc.append((0.95, 0.20, 0.20, 0.90))
                    ec.append('#8b0000'); lw.append(0.4)

    coll = Poly3DCollection(polys, facecolors=fc, edgecolors=ec,
                            linewidths=lw)
    ax.add_collection3d(coll)

    return {'CG': CG, 'CB': CB, 'top_v': top_v, 'r': r}
