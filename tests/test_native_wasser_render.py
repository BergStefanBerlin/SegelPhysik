import numpy as np
import pytest

from segelphysik.core.rechenpfad import python_referenz
from segelphysik.render import vista


@pytest.mark.parametrize("shape", [(1, 1), (1, 9), (8, 1), (3, 7), (40, 31)])
@pytest.mark.parametrize("faktor", [1, 2, 3, 5])
def test_natives_bilineares_wasserraster_behaelt_werte_form_und_identitaet(
        monkeypatch, shape, faktor):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(9026)
    z = rng.normal(size=shape)
    z.setflags(write=False)
    with python_referenz():
        ref = vista._bilinear_upsample(z, faktor)
    cpp = vista._bilinear_upsample(z, faktor)
    np.testing.assert_array_equal(cpp, ref)
    assert cpp.shape == ref.shape and cpp.dtype == ref.dtype
    if faktor == 1:
        assert cpp is z


@pytest.mark.parametrize("shape", [(1, 1), (1, 9), (8, 1), (3, 7), (40, 31)])
@pytest.mark.parametrize("durchlaeufe", [-1, 0, 1, 3])
def test_native_wasserglaettung_behaelt_lochfuellung_median_und_laplace(
        monkeypatch, shape, durchlaeufe):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(10026)
    renderer = vista.PyVistaRenderer.__new__(vista.PyVistaRenderer)
    renderer.dx = .1
    renderer.smooth_passes = durchlaeufe
    for _ in range(10):
        z = rng.normal(size=shape)
        z[rng.random(size=shape) < .4] = np.nan
        with python_referenz():
            ref = renderer._smooth_surface(z)
        np.testing.assert_array_equal(renderer._smooth_surface(z), ref)
    for wert in (np.nan, np.inf, -np.inf):
        np.testing.assert_array_equal(
            renderer._smooth_surface(np.full(shape, wert)), np.zeros(shape))


def test_native_glaettung_behaelt_medianrestfuellung_nach_25_runden(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    renderer = vista.PyVistaRenderer.__new__(vista.PyVistaRenderer)
    renderer.dx, renderer.smooth_passes = .1, 2
    z = np.full((80, 90), np.nan)
    z[0, 0], z[-1, -1] = .2, -.3
    with python_referenz():
        ref = renderer._smooth_surface(z)
    np.testing.assert_array_equal(renderer._smooth_surface(z), ref)


@pytest.mark.parametrize("shape", [(0, 0), (0, 3), (3, 0), (1, 1), (3, 7), (40, 31)])
def test_native_wasserflaeche_behaelt_gesichterreihenfolge_und_punkte(monkeypatch, shape):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")

    class Poly:
        @staticmethod
        def PolyData(punkte, faces):
            return punkte, faces

    y, x = np.indices(shape, dtype=float)
    z = x + 2. * y
    with python_referenz():
        ref = vista._surface_polydata(Poly, x, y, z)
    cpp = vista._surface_polydata(Poly, x, y, z)
    for a, b in zip(cpp, ref):
        assert a.shape == b.shape and a.dtype == b.dtype
        np.testing.assert_array_equal(a, b)


@pytest.mark.parametrize("n", [0, 1, 3, 48, 1000])
def test_native_wassergrundformen_behalten_aufloesung_und_geometrie(monkeypatch, n):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz():
        kreis, quadrat = vista._unit_circle(n), vista._unit_square()
    np.testing.assert_allclose(vista._unit_circle(n), kreis, rtol=0., atol=1e-15)
    np.testing.assert_array_equal(vista._unit_square(), quadrat)


def test_natives_wasserraster_akzeptiert_strides_und_nanmasken(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    z = np.arange(60., dtype=float).reshape(6, 10)[::-1, ::2]
    z[1, 1] = np.nan
    z.setflags(write=False)
    with python_referenz():
        ref = vista._bilinear_upsample(z, 3)
    np.testing.assert_array_equal(vista._bilinear_upsample(z, 3), ref)


@pytest.mark.parametrize("anzahl", [0, 1, 20, 250])
def test_native_iso_wasser_spiegelung_splat_und_kalibrierung(monkeypatch, anzahl):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(25026 + anzahl)
    wasser_python = vista.IsoSurfaceWater(
        3., 2.5, 1.2, .2, cell=.45, kernel_r=.55)
    wasser_cpp = vista.IsoSurfaceWater(
        3., 2.5, 1.2, .2, cell=.45, kernel_r=.55)
    punkte = rng.uniform(
        [-1.8, -1.5, -1.5], [1.8, 1.5, .5], size=(anzahl, 3))
    if anzahl:
        punkte[:min(5, anzahl), 0] = [-1.5, 1.5, -1.49, 1.49, 0.0][:min(5, anzahl)]
        punkte[:min(5, anzahl), 1] = [-1.25, 1.25, 0.0, 0.0, 1.24][:min(5, anzahl)]
        punkte[:min(5, anzahl), 2] = [-1.2, -1.19, -.65, -.1, .2][:min(5, anzahl)]
    with python_referenz():
        gespiegelt = wasser_python._mirrored(punkte)
    gespiegelt_cpp = wasser_cpp._mirrored(punkte)
    np.testing.assert_array_equal(gespiegelt_cpp, gespiegelt)
    with python_referenz():
        wasser_python.splat(punkte)
    wasser_cpp.splat(punkte)
    assert wasser_cpp.grid.dtype == np.float32
    np.testing.assert_array_equal(wasser_cpp.grid, wasser_python.grid)
    assert wasser_cpp._norm_eff == wasser_python._norm_eff


def test_native_iso_wasser_kalibrierungsmedian_und_gitterbesitz(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(26026)
    python = vista.IsoSurfaceWater(5., 5., 3., .2, cell=.25, kernel_r=.5)
    cpp = vista.IsoSurfaceWater(5., 5., 3., .2, cell=.25, kernel_r=.5)
    for _ in range(20):
        g = rng.uniform(0., 3., size=python.grid.shape).astype(np.float32)
        g[rng.random(size=g.shape) < .6] = 0.
        with python_referenz():
            python._norm_eff = None
            python._calibrate(g)
        cpp._norm_eff = None
        cpp._calibrate(g)
        assert cpp._norm_eff == python._norm_eff


def test_native_iso_wasser_behaelt_pyvista_marching_cubes_und_zweiframecache(monkeypatch):
    import pyvista as pv

    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    python = vista.IsoSurfaceWater(2., 2., 1., .2, cell=.2)
    cpp = vista.IsoSurfaceWater(2., 2., 1., .2, cell=.2)
    x, y, z = np.meshgrid(
        np.arange(-.9, 1., .2), np.arange(-.9, 1., .2),
        np.arange(-.9, 0., .2), indexing="ij")
    punkte = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    with python_referenz():
        python.splat(punkte)
    cpp.splat(punkte)
    np.testing.assert_array_equal(cpp.grid, python.grid)
    with python_referenz():
        mesh_python = python.mesh(pv)
    mesh_cpp = cpp.mesh(pv)
    np.testing.assert_array_equal(mesh_cpp.points, mesh_python.points)
    np.testing.assert_array_equal(mesh_cpp.faces, mesh_python.faces)
    python.splat(punkte)
    cpp.splat(punkte)
    assert python._skip is False and cpp._skip is False
    python.mesh(pv)
    cpp.mesh(pv)
    python.splat(punkte)
    cpp.splat(punkte)
    assert python._skip is True and cpp._skip is True
    assert python.mesh(pv) is python._cache
    assert cpp.mesh(pv) is cpp._cache
