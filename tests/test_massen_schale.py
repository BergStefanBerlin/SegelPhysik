"""Massen schale: bestehende Referenzvertraege."""
import numpy as np
import pytest


def test_w1_schalentensor_wuerfel_analytisch():
    """Offener Wuerfel (5 Flaechen, Kante a=1, fm=1): A = 5*a^2,
    r_z = -a/10; Tensor unabhaengig ueber Plattenformeln + Steiner."""
    from segelphysik.core.massen import traegheitstensor_flaechig, schwerpunkt_flaechig
    a = 1.0
    flaechen = [
        np.array([[-.5,-.5,-.5],[.5,-.5,-.5],[.5,.5,-.5],[-.5,.5,-.5]], float),
        np.array([[-.5,-.5,-.5],[.5,-.5,-.5],[.5,-.5,.5],[-.5,-.5,.5]], float),
        np.array([[-.5,.5,-.5],[.5,.5,-.5],[.5,.5,.5],[-.5,.5,.5]], float),
        np.array([[-.5,-.5,-.5],[-.5,.5,-.5],[-.5,.5,.5],[-.5,-.5,.5]], float),
        np.array([[.5,-.5,-.5],[.5,.5,-.5],[.5,.5,.5],[.5,-.5,.5]], float),
    ]
    punkte, dreiecke = [], []
    off = 0
    for quad in flaechen:
        idx = [off, off + 1, off + 2, off + 3]
        dreiecke += [[idx[0], idx[1], idx[2]], [idx[0], idx[2], idx[3]]]
        punkte += [list(q) for q in quad]
        off += 4
    punkte = np.asarray(punkte, float)
    dreiecke = np.asarray(dreiecke, np.int64)
    fm = 1.0
    r, A = schwerpunkt_flaechig(punkte, dreiecke)
    assert A == pytest.approx(5 * a * a)
    assert r[2] == pytest.approx(-0.1)
    I_ref = np.zeros((3, 3))
    mb = a * a * fm                       # Bodenplatte, Zentrum (0,0,-0.5)
    d_b = np.array([0.0, 0.0, -0.5]) - r  # = (0,0,-0.4)
    I_ref[0, 0] += mb * a * a / 12 + mb * (d_b[1]**2 + d_b[2]**2)
    I_ref[1, 1] += mb * a * a / 12 + mb * (d_b[0]**2 + d_b[2]**2)
    I_ref[2, 2] += mb * a * a / 6
    for sx, sy, sz in ((0, -.5, 0), (0, .5, 0), (-.5, 0, 0), (.5, 0, 0)):
        mw = a * a * fm                   # Seitenflaeche, Zentrum (sx,sy,0)
        d = np.array([sx, sy, sz]) - r    # z-Komponente ist +0.1, nicht -0.4!
        if abs(sy) > 0:                   # Normale y: Iyy = a^2/6 (Normalachse)
            Ixx, Iyy, Izz = mw * a * a / 12, mw * a * a / 6, mw * a * a / 12
        else:                             # Normale x: Ixx = a^2/6
            Ixx, Iyy, Izz = mw * a * a / 6, mw * a * a / 12, mw * a * a / 12
        I_ref[0, 0] += Ixx + mw * (d[1]**2 + d[2]**2)
        I_ref[1, 1] += Iyy + mw * (d[0]**2 + d[2]**2)
        I_ref[2, 2] += Izz + mw * (d[0]**2 + d[1]**2)
    J = traegheitstensor_flaechig(punkte, dreiecke, fm)
    np.testing.assert_allclose(np.diag(J), np.diag(I_ref), rtol=1e-10)
    np.testing.assert_allclose(J - np.diag(np.diag(J)), 0.0, atol=1e-12)


def test_schalentensor_bleibt_bei_grossen_absolutkoordinaten_stabil():
    from segelphysik.core.massen import (
        traegheitstensor_flaechig,
        validiere_traegheitstensor,
    )
    punkte = np.array([
        [0.0, 0.0, 0.0],
        [0.01, 0.0, 0.0],
        [0.01, 0.008, 0.002],
        [0.0, 0.008, 0.002],
    ])
    dreiecke = np.array([[0, 1, 2], [0, 2, 3]])
    versatz = np.array([0.2862, 0.016625, 5.13055])

    referenz = traegheitstensor_flaechig(punkte, dreiecke, 5.4)
    verschoben = traegheitstensor_flaechig(
        punkte + versatz, dreiecke, 5.4)

    np.testing.assert_allclose(verschoben, referenz, rtol=1e-12, atol=1e-20)
    validiere_traegheitstensor(verschoben)
