"""Wasser render referenz: bestehende Referenzvertraege."""
import numpy as np
import pytest
from segelphysik.render.vista import (
    IsoSurfaceWater, PyVistaRenderer, _bilinear_upsample,
    _surface_polydata, _unit_circle, _unit_square,
)


@pytest.mark.parametrize("n", [3, 12, 40])
def test_wasserflaechen_interpolation_normale_und_spitzenbehandlung(n):
    import pyvista as pv

    x, y = np.meshgrid(np.linspace(-1., 1., n), np.linspace(-1., 1., n))
    z = x + 2 * y
    netz = _surface_polydata(pv, x, y, z)
    assert netz.n_points == n * n
    assert netz.n_cells == 2 * (n - 1) ** 2
    np.testing.assert_array_equal(netz.points[:, 2], z.ravel())
    interpoliert = _bilinear_upsample(z, 2)
    np.testing.assert_allclose(interpoliert[::2, ::2], z, rtol=0, atol=1e-15)
    assert interpoliert.shape == (2 * n - 1, 2 * n - 1)
    assert _bilinear_upsample(z, 1) is z
    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    renderer.dx = .1
    renderer.smooth_passes = 2
    defekt = z.copy()
    defekt[n // 2, n // 2] = np.nan
    glatt = renderer._smooth_surface(defekt)
    assert np.isfinite(glatt).all()
    assert glatt.shape == z.shape
    np.testing.assert_array_equal(
        renderer._smooth_surface(np.full((n, n), np.nan)), np.zeros((n, n)))
    kreis = _unit_circle(n)
    np.testing.assert_allclose(np.linalg.norm(kreis, axis=1), 1., rtol=0, atol=1e-15)
    assert _unit_square().shape == (5, 2)


def test_vorhandene_isoflaeche_und_bestehender_zweiframecache():
    import pyvista as pv

    wasser = IsoSurfaceWater(2., 2., 1., .2, cell=.2)
    x, y, z = np.meshgrid(
        np.arange(-.9, 1., .2), np.arange(-.9, 1., .2),
        np.arange(-.9, 0., .2), indexing="ij")
    punkte = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    wasser.splat(punkte)
    mesh = wasser.mesh(pv)
    assert mesh.n_points > 0
    assert np.isfinite(mesh.points).all()
    assert wasser._norm_eff is not None
    wasser.splat(punkte)
    assert not wasser._skip
    wasser.mesh(pv)
    wasser.splat(punkte)
    assert wasser._skip
    assert wasser.mesh(pv) is wasser._cache
