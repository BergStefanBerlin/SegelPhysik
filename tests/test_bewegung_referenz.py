"""Bewegung referenz: bestehende Referenzvertraege."""
import numpy as np
from segelphysik.core.bewegung import body_pose, koerper_pose
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box


def test_relative_pose_und_kinematikalias_erhalten_frames():
    punkte, dreiecke = build_box(1., 1., 1.)
    k = Koerper(form=(punkte, dreiecke), dichte=500.)
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    k.setze_rel_pose((rotation, (1., 2., 3.)))
    np.testing.assert_array_equal(k._rel_R, rotation)
    np.testing.assert_array_equal(k._rel_t, (1., 2., 3.))
    for t in (0., .5, 10.):
        r, x = koerper_pose(t, achse=(1., 0., 0.), phase=.1)
        rb, xb = body_pose(t, axis=(1., 0., 0.), phase=.1)
        np.testing.assert_array_equal(r, rb)
        np.testing.assert_array_equal(x, xb)
