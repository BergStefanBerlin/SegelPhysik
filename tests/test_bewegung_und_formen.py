"""Test-Suite V3-Kern (SPEC_V3.md Abschnitte 8/9): K1'', K2'', K7'', Mesh-Checks."""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from segelphysik.core import bewegung as kin
from segelphysik.core import koerper_formen as msh

TOL_DEG, TOL_MM = 0.01, 1e-3


def test_k1_period():
    assert abs(kin.phi_deg(15.0)-360.0) <= TOL_DEG
    assert kin.phi_deg(0.0) == 0.0
    assert abs(kin.phi_deg(7.5)-180.0) <= TOL_DEG


def test_k1_omega_value():
    assert abs(kin.OMEGA - 2*math.pi/15.0) < 1e-15
    assert abs(math.degrees(kin.OMEGA) - 24.0) < 1e-12


def test_k2_center_fixed():
    for t in np.linspace(0.0, 30.0, 201):
        _, r_S = kin.body_pose(float(t))
        assert np.max(np.abs(r_S)) <= TOL_MM


def test_d1_axis_horizontal():
    R = kin.rotation_matrix(math.pi/2.0, axis=(0,1,0))
    ez = R @ np.array([0.0,0.0,1.0])
    assert abs(ez[1]) < 1e-12 and abs(ez[0]-1.0) < 1e-12


def test_k7_determinism():
    s1 = kin.Scene.default("cone").to_json()
    assert s1 == kin.Scene.from_json(s1).to_json()
    seqs = []
    for _ in range(2):
        c = kin.Clock(); seq = []
        for _ in range(1000):
            c.advance_real(kin.DT); seq.append(c.t)
        seqs.append(seq + [kin.phi_deg(c.t)])
    assert seqs[0] == seqs[1]


def test_clock_pause_step_reset():
    c = kin.Clock()
    assert c.advance_real(1.0) == 240
    c.paused = True; assert c.advance_real(1.0) == 0
    c.paused = False; c.step_once()
    assert abs(c.t - 241*kin.DT) < 1e-15
    c.reset(); assert c.t == 0.0


def test_playback_scaling():
    assert kin.Clock(playback=0.25).advance_real(1.0) == 60
    assert kin.Clock(playback=4.0).advance_real(1.0) == 960


def test_scene_multiposition_rule():
    """Spec-§7-JSON kennt kein 'position': zwei Koerper ohne position -> Fehler."""
    b = {"type": "cone", "dims": {"H": 2.0, "R": 1.0}, "axis": [0.0, 1.0, 0.0],
         "omega": kin.OMEGA, "phase": 0.0}
    js = json.dumps({"bodies": [dict(b), dict(b)]})
    try:
        kin.Scene.from_json(js); raised = False
    except ValueError: raised = True
    assert raised, "Pflicht-Pruefung griff nicht"
    ok = json.dumps({"bodies": [dict(b, position=[-2.0, 0.0, 0.0]),
                                dict(b, position=[2.0, 0.0, 0.0])]})
    kin.Scene.from_json(ok)


def _volume(v, f):
    p0,p1,p2 = v[f[:,0]], v[f[:,1]], v[f[:,2]]
    return float(np.sum(np.einsum("ij,ij->i", p0, np.cross(p1,p2)))/6.0)


def _cone_polygon_volume(n, H=2.0, R=1.0):
    """Exaktes Volumen des facettierten Kegels (regulaeres n-Eck als Basis)."""
    return (1.0/3.0) * (n/2.0) * R*R * math.sin(2*math.pi/n) * H


def test_mesh_geometries():
    # Kegel: Mesh-Volumen exakt gegen facettierte Referenz ...
    v,f = msh.build_cone()
    assert abs(_volume(v,f) - _cone_polygon_volume(64)) < 1e-12, _volume(v,f)
    # ... und Konvergenz gegen den wahren Kreiskegel (quadratisch, hier < 1e-6):
    v2,f2 = msh.build_cone(nseg=4096)
    assert abs(_volume(v2,f2) - math.pi*2.0/3.0) < 1e-6
    assert abs(v[:,2].min()+0.5) < 1e-12 and abs(v[:,2].max()-1.5) < 1e-12
    # Quader:
    v,f = msh.build_box()
    assert abs(_volume(v,f)-8.0) < 1e-12
    # Pyramide:
    v,f = msh.build_pyramid()
    assert abs(_volume(v,f)-8.0/3.0) < 1e-12
    assert abs(v[:,2].min()+0.5) < 1e-12 and abs(v[:,2].max()-1.5) < 1e-12
