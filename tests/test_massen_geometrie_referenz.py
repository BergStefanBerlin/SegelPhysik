"""Massen geometrie referenz: bestehende Referenzvertraege."""
import numpy as np
import pytest
from segelphysik.core import massen
from segelphysik.core.koerper_formen import build_box


def test_scalar_schnittpraedikate_gegen_einfache_geometrie():
    a = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    normale = massen._kreuzprodukt_3d(a[1] - a[0], a[2] - a[0])
    np.testing.assert_array_equal(normale, (0., 0., 1.))
    assert massen._koplanare_dreiecke_schneiden(a, a + (.1, .1, 0.), normale, 1e-12)
    assert not massen._koplanare_dreiecke_schneiden(a, a + (3., 0., 0.), normale, 1e-12)
    assert massen._segment_dreieck_schneiden(
        np.array([.2, .2, -1.]), np.array([.2, .2, 1.]), a, 1e-12)
    assert not massen._segment_dreieck_schneiden(
        np.array([2., 2., -1.]), np.array([2., 2., 1.]), a, 1e-12)


def test_meshflaeche_quader_und_leere_flaechen():
    punkte, dreiecke = build_box(2., 3., 4.)
    assert massen.mesh_flaeche(punkte, dreiecke) == pytest.approx(52., abs=1e-12)
    assert massen.mesh_flaeche(punkte, np.empty((0, 3), dtype=np.int64)) == 0.
