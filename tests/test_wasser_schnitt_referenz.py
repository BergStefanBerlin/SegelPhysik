"""Wasser schnitt referenz: bestehende Referenzvertraege."""
import numpy as np
import pytest
from segelphysik import wasser_schnitt
from segelphysik.core.auftrieb import _y_intervalle_saeule
from segelphysik.core.koerper_formen import build_box


@pytest.mark.parametrize("oberhalb", [False, True])
def test_polygonbeschnitt_und_fan_bleiben_im_gewaehlten_halbraum(oberhalb):
    polygon = np.array([[-1., -1., -1.], [1., -1., 1.],
                        [1., 1., 1.], [-1., 1., -1.]])
    punkte = wasser_schnitt._clip_polygon(polygon, 0., oberhalb)
    assert len(punkte) == 4
    assert all(p[2] >= 0 if oberhalb else p[2] <= 0 for p in punkte)
    dreiecke = wasser_schnitt._fan_triangulieren(punkte)
    assert len(dreiecke) == 2
    flaeche = sum(np.linalg.norm(np.cross(b - a, c - a)) / 2
                  for a, b, c in dreiecke)
    assert flaeche == pytest.approx(2 * np.sqrt(2), abs=1e-12)
    assert wasser_schnitt._clip_polygon([], 0., oberhalb) == []
    assert wasser_schnitt._fan_triangulieren([]) == []


def test_punkt_in_ring_innen_aussen_und_konkaver_ring():
    ring = np.array([[0., 0., 0.], [2., 0., 0.], [2., 2., 0.],
                     [1., 1., 0.], [0., 2., 0.]])
    assert wasser_schnitt._punkt_in_ring((.5, .5), ring)
    assert not wasser_schnitt._punkt_in_ring((3., .5), ring)
    assert not wasser_schnitt._punkt_in_ring((1., 1.8), ring)


def test_alter_skalarer_voxel_saeulenpfad_bleibt_separat_nachgewiesen():
    punkte, dreiecke = build_box(2., 2., 2.)
    np.testing.assert_allclose(
        _y_intervalle_saeule(punkte, dreiecke, .1, .2),
        [(-1., 1.)], rtol=0, atol=1e-12)
    assert _y_intervalle_saeule(punkte, dreiecke, 10., 0.) == []
