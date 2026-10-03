#!/usr/bin/env python3
# ============================================================
# viewer_bridge.py - Kopplung Segelphysik -> Godot-Viewer
# ------------------------------------------------------------
# Start:  python viewer_bridge.py [--fm 1200] [--fw 70]
# Sendet 60 Hz UDP/JSON an 127.0.0.1:9999 (Pose, Kraefte,
# Stroemung, Stats); empfaengt Befehle auf 127.0.0.1:9998.
# Koordinaten: Simulation Z-up -> Godot Y-up via (x, z, -y).
# ============================================================
import socket, json, time, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import G
from dynamics import Simulation

PORT_GODOT = 9999
PORT_CMD = 9998
NSUB_VIEWER = 3


def zu_godot_v(v):
    return [float(v[0]), float(v[2]), float(-v[1])]


def zu_godot_q(q):
    return [float(q[0]), float(q[1]), float(q[3]), float(-q[2])]


def export_obj(sim, pfad_hull, pfad_keel):
    q = sim.q

    def schreibe(pfad, teile):
        with open(pfad, 'w') as f:
            f.write('# Segelphysik Export (Y-up, Meter)\n')
            off = 1
            for name, P, faces in teile:
                f.write('o %s\n' % name)
                for p in P:
                    f.write('v %.4f %.4f %.4f\n' % (p[0], p[2], -p[1]))
                for a, b, c, d in faces:
                    f.write('f %d %d %d %d\n' % (off+a, off+b, off+c, off+d))
                off += len(P)

    N = q.netz
    NS, MS = N.shape[0], N.shape[1]
    faces = []
    for i in range(NS - 1):
        for j in range(MS - 1):
            v0 = i*MS + j
            faces.append((v0, v0+1, v0+MS+1, v0+MS))
    schreibe(pfad_hull, [('rumpf', N.reshape(-1, 3), faces)])

    ff = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
          (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    Bn = q.bulb_netz
    nb, mb = Bn.shape[0], Bn.shape[1]
    bf = []
    for i in range(nb - 1):
        for j in range(mb - 1):
            v0 = i*mb + j
            bf.append((v0, v0+1, v0+mb+1, v0+mb))
    schreibe(pfad_keel, [('fin', q.fin_box, ff),
                         ('bulb', Bn.reshape(-1, 3), bf),
                         ('ruder', q.rud_box, ff)])


def _kraefte_setzen(sim, fm, fw):
    if fm <= 1e-9:
        sim.F_ext = np.zeros(3)
        sim.tau_ext = np.zeros(3)
        return
    x_w = sim.R @ np.array([1.0, 0, 0]); x_w[2] = 0.0
    y_w = sim.R @ np.array([0, 1.0, 0]); y_w[2] = 0.0
    nx, ny = np.linalg.norm(x_w), np.linalg.norm(y_w)
    if nx < 1e-9 or ny < 1e-9:
        sim.F_ext = np.zeros(3)
        sim.tau_ext = np.zeros(3)
        return
    x_w, y_w = x_w/nx, y_w/ny
    F_w = fm*(np.cos(fw)*x_w - np.sin(fw)*y_w)
    r_top = np.array([float(sim.q.c_body[0]), 0.0,
                      sim.q.H/2 + 1.45*sim.q.L])
    sim.F_ext = F_w
    sim.tau_ext = sim.R.T @ np.cross(sim.R @ (r_top - sim.q.c_body), F_w)


def _fluss(sim, n_max=64):
    q, R = sim.q, sim.R
    pts = []
    for x in np.linspace(-0.45*q.L, 0.45*q.L, 6):
        for y in (-(q.B/2 + 0.3), 0.0, (q.B/2 + 0.3)):
            for z in (-0.25, -0.6, -1.0):
                r = np.array([x, y, z])
                pw = R @ r + sim.p
                if pw[2] > -0.08:
                    continue
                u_b = -(sim.v + np.cross(sim.om, r - q.c_body))
                pts.append({'p': zu_godot_v(pw),
                            'u': zu_godot_v(R @ u_b)})
                if len(pts) >= n_max:
                    return pts
    return pts


def _paket(sim, fm):
    s, q, R = sim, sim.q, sim.R
    cg_w = R @ q.c_body + s.p
    cb_w = cg_w + s.h['CB'] if s.h['CB'] is not None else cg_w
    r_top = np.array([float(q.c_body[0]), 0.0, q.H/2 + 1.45*q.L])
    top_w = R @ r_top + s.p
    kraefte = [
        {'name': 'Auftrieb', 'gruppe': 'vertikal', 'rolle': 'prim',
         'p': zu_godot_v(cb_w), 'F': [0.0, float(s.h['F_A']), 0.0]},
        {'name': 'Gewicht', 'gruppe': 'vertikal', 'rolle': 'gegen',
         'p': zu_godot_v(cg_w), 'F': [0.0, float(-q.m*G), 0.0]},
        {'name': 'Segel', 'gruppe': 'seiten', 'rolle': 'prim',
         'p': zu_godot_v(top_w), 'F': zu_godot_v(s.F_ext)},
        {'name': 'Kiel', 'gruppe': 'seiten', 'rolle': 'gegen',
         'p': zu_godot_v(cg_w + R @ (q.r_kiel - q.c_body)),
         'F': zu_godot_v(s.hydrodyn.F_kiel)},
        {'name': 'Ruder', 'gruppe': 'seiten', 'rolle': 'gegen',
         'p': zu_godot_v(cg_w + R @ (q.r_rud - q.c_body)),
         'F': zu_godot_v(s.hydrodyn.F_rud)},
        {'name': 'Widerstand', 'gruppe': 'seiten', 'rolle': 'gegen',
         'p': zu_godot_v(cg_w), 'F': zu_godot_v(s.hydrodyn.F_rumpf)}]
    vb = R.T @ s.v
    drift = float(np.degrees(np.arctan2(vb[1], abs(vb[0]) + 1e-9)))
    res = float(np.linalg.norm(s.F_ext + s.hydrodyn.F_kiel
                               + s.hydrodyn.F_rud + s.hydrodyn.F_rumpf))
    fahrt = float(np.hypot(s.v[0], s.v[1]))
    return {'t': float(s.t),
            'pose': {'pos': zu_godot_v(s.p), 'quat': zu_godot_q(s.quat)},
            'forces': kraefte, 'flow': _fluss(s),
            'stats': {'fahrt': fahrt, 'kn': fahrt*1.9438,
                      'drift': drift, 'roll': float(np.degrees(s.roll)),
                      'bilanz': res, 'rw': float(np.degrees(s.hydrodyn.rw)),
                      'fm': float(fm)}}


def main(test=False):
    sim = Simulation(9.0, 2.96, 1.6, 130, 16, 0.11, 1.35, 11300)
    sim.reset(heel_deg=0.0)
    base = os.path.dirname(os.path.abspath(__file__))
    vdir = os.path.join(base, 'viewer')
    export_obj(sim, os.path.join(vdir, 'yacht_hull.obj'),
               os.path.join(vdir, 'yacht_keel.obj'))
    if test:
        t0 = time.time()
        pkt = None
        for _ in range(150):
            _kraefte_setzen(sim, 1200.0, np.radians(70.0))
            for _ in range(NSUB_VIEWER):
                sim.schritt()
            pkt = _paket(sim, 1200.0)
        ms = 1000*(time.time() - t0)/150
        js = json.dumps(pkt)
        print('TEST: 150 Frames, %.2f ms/Frame' % ms)
        print('TEST: Paket %d Bytes, JSON ok' % len(js))
        print('TEST: stats =', json.dumps(pkt['stats']))
        print('TEST: %d Kraefte, %d Flusspunkte' %
              (len(pkt['forces']), len(pkt['flow'])))
        return
    fm = float(sys.argv[sys.argv.index('--fm')+1]) if '--fm' in sys.argv else 1200.0
    fw_deg = float(sys.argv[sys.argv.index('--fw')+1]) if '--fw' in sys.argv else 70.0
    fw = np.radians(fw_deg)
    rw = 0.0
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = ('127.0.0.1', PORT_GODOT)
    cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cmd.bind(('127.0.0.1', PORT_CMD))
    cmd.setblocking(False)
    frame = 1.0/60.0
    print('Bridge laeuft -> %s:%d (Strg+C beendet)' % addr)
    n = 0
    try:
        while True:
            t0 = time.time()
            while True:
                try:
                    data, _ = cmd.recvfrom(2048)
                    m = json.loads(data.decode())
                    if 'rw_deg' in m: rw = float(m['rw_deg'])
                    if 'fm' in m: fm = float(m['fm'])
                    if 'fw_deg' in m: fw = np.radians(float(m['fw_deg']))
                    if m.get('cmd') == 'reset': sim.reset(heel_deg=0.0)
                except BlockingIOError:
                    break
                except Exception:
                    break
            sim.rw_soll = np.radians(rw)
            for _ in range(NSUB_VIEWER):
                _kraefte_setzen(sim, fm, fw)
                sim.schritt()
            sock.sendto(json.dumps(_paket(sim, fm)).encode(), addr)
            n += 1
            rest = frame - (time.time() - t0)
            if rest > 0:
                time.sleep(rest)
    except KeyboardInterrupt:
        print('Beendet nach %d Frames' % n)


if __name__ == '__main__':
    main(test='--test' in sys.argv)
