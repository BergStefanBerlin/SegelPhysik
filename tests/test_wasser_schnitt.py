"""Tests fuer den exakten Wasser-Schnitt (Verfahren B)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from segelphysik import wasser_schnitt as ws
from segelphysik.core import koerper_formen as formen

Q_V = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
                [-1,-1, 1],[1,-1, 1],[1,1, 1],[-1,1, 1]], float)
Q_F = np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
                [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])


def _umfang(zug):
    return sum(np.linalg.norm(zug[i]-zug[(i+1)%len(zug)]) for i in range(len(zug)))


def _keine_entarteten(pp, tt):
    if len(tt):
        a, b, c = pp[tt[:,0]], pp[tt[:,1]], pp[tt[:,2]]
        flaeche = 0.5*np.linalg.norm(np.cross(b-a, c-a), axis=1)
        assert flaeche.min() > 1e-12


def test_quader_mittig():
    u_p,u_t,o_p,o_t,k = ws.schneide_am_wasser(Q_V, Q_F)
    assert abs(ws.mesh_volumen(u_p,u_t)-4.0) < 1e-9
    assert abs(ws.mesh_volumen(o_p,o_t)-4.0) < 1e-9
    zug = ws.polygonzug_der_kontur(k)
    assert len(zug) == 4 and abs(_umfang(zug)-8.0) < 1e-9
    _keine_entarteten(u_p,u_t); _keine_entarteten(o_p,o_t)


def test_kegel_komplett_unter_wasser():
    kv, kf = formen.bau_kegel(H=2.0, R=1.0)
    u_p,u_t,o_p,o_t,k = ws.schneide_am_wasser(kv + np.array([0,0,-3.0]), kf)
    assert len(o_t) == 0 and len(k) == 0
    assert abs(ws.mesh_volumen(u_p,u_t) - 2*np.pi/3) < 5e-3


def test_kegel_auf_wasserlinie_erhaltung():
    kv, kf = formen.bau_kegel(H=2.0, R=1.0)
    u_p,u_t,o_p,o_t,k = ws.schneide_am_wasser(kv, kf)
    gesamt = ws.mesh_volumen(u_p,u_t)+ws.mesh_volumen(o_p,o_t)
    zug = ws.polygonzug_der_kontur(k)
    assert abs(gesamt - 2*np.pi/3) < 5e-3 and len(zug) == 64


def test_gekippter_quader_45_grad():
    w = 45*np.pi/180
    R = np.array([[np.cos(w),0,np.sin(w)],[0,1,0],[-np.sin(w),0,np.cos(w)]])
    u_p,u_t,o_p,o_t,k = ws.schneide_am_wasser(Q_V @ R.T, Q_F)
    gesamt = ws.mesh_volumen(u_p,u_t)+ws.mesh_volumen(o_p,o_t)
    zug = ws.polygonzug_der_kontur(k)
    assert abs(gesamt-8.0) < 1e-9
    assert len(zug) == 4 and abs(_umfang(zug)-(4*np.sqrt(2)+4)) < 1e-9
    _keine_entarteten(u_p,u_t); _keine_entarteten(o_p,o_t)


def test_pyramide_auf_wasserlinie():
    pv_, pf_ = formen.bau_pyramide(a=2.0, H=2.0)
    u_p,u_t,o_p,o_t,k = ws.schneide_am_wasser(pv_, pf_)
    gesamt = ws.mesh_volumen(u_p,u_t)+ws.mesh_volumen(o_p,o_t)
    zug = ws.polygonzug_der_kontur(k)
    assert abs(gesamt - 8/3) < 1e-9
    assert len(zug) == 4 and abs(_umfang(zug)-6.0) < 1e-9


def test_spiegelsymmetrie_betrag():
    u2,t2,o2,d2,k2 = ws.schneide_am_wasser(-Q_V, Q_F)
    assert abs(abs(ws.mesh_volumen(u2,t2))-4.0) < 1e-9


def test_kegel_liegend_90_grad():
    kv, kf = formen.bau_kegel(H=2.0, R=1.0)
    R8 = np.array([[0.,0.,1.],[0.,1.,0.],[-1.,0.,0.]])
    u_p,u_t,o_p,o_t,k = ws.schneide_am_wasser(kv @ R8.T, kf)
    gesamt = ws.mesh_volumen(u_p,u_t)+ws.mesh_volumen(o_p,o_t)
    zug = ws.polygonzug_der_kontur(k)
    assert abs(gesamt - 2*np.pi/3) < 5e-3 and len(zug) >= 3 and len(k) > 0
    _keine_entarteten(u_p,u_t); _keine_entarteten(o_p,o_t)


def test_winkel_sweep_volumenerhaltung():
    fehler_max = 0.0
    for winkel in range(0, 91, 5):
        ww = np.radians(winkel)
        Rw = np.array([[np.cos(ww),0,np.sin(ww)],[0,1,0],[-np.sin(ww),0,np.cos(ww)]])
        up,tp,op,dp,kk = ws.schneide_am_wasser(Q_V @ Rw.T, Q_F)
        vsum = ws.mesh_volumen(up,tp)+ws.mesh_volumen(op,dp)
        fehler_max = max(fehler_max, abs(vsum-8.0))
        _keine_entarteten(up,tp); _keine_entarteten(op,dp)
    assert fehler_max < 1e-9
