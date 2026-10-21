"""Renderer legacy vertrag: bestehende Referenzvertraege."""
from types import SimpleNamespace
import numpy as np
import pytest
from segelphysik.render.vista import PyVistaRenderer


@pytest.mark.parametrize("methode,args", [
    ("_body_half_height", (SimpleNamespace(half=(1., 1., 1.)),)),
    ("_update_ring", (0, SimpleNamespace())),
    ("_clamp_to_bodies", (np.zeros((3, 3)),)),
    ("update", ()),
])
def test_entfernter_legacy_body_typ_ist_keine_ausfuehrbare_referenz(methode, args):
    """Den bekannten Importfehler offen dokumentieren, keine Ersatzphysik erfinden."""
    from importlib.util import find_spec

    assert find_spec("segelphysik.core.bodies") is None
    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    with pytest.raises(ModuleNotFoundError, match="segelphysik.core.bodies"):
        getattr(renderer, methode)(*args)


def test_legacy_renderer_zeichnet_nur_geschwindigkeit_keine_zweite_kraftanzeige():
    import pyvista as pv

    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    renderer.pv = pv
    renderer.app = SimpleNamespace(world=SimpleNamespace(environment=SimpleNamespace(g=10.)))
    renderer._arrow_v = None
    meshes = []
    entfernt = []

    def hinzufuegen(mesh, **kwargs):
        meshes.append((mesh, kwargs))
        return object()

    renderer._plotter = SimpleNamespace(add_mesh=hinzufuegen, remove_actor=entfernt.append)
    koerper = SimpleNamespace(
        mass=1., force=(10., 0., 0.), vel=(0., 1., 0.), pos=(0., 0., 0.))
    renderer._refresh_arrows(koerper)
    assert len(meshes) == 1
    assert meshes[0][1]["color"] == "#27ae60"
    assert np.isfinite(meshes[0][0].points).all()
    koerper.force = koerper.vel = (0., 0., 0.)
    renderer._refresh_arrows(koerper)
    assert len(entfernt) == 1 and len(meshes) == 1
    assert not hasattr(renderer, "_arrow_f") and renderer._arrow_v is None


def test_bildschirm_zu_wasser_ohne_plotter_und_mit_echter_vtk_kamera():
    import pyvista as pv

    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    renderer._plotter = None
    assert renderer.screen_to_water(10., 10.) is None
    plotter = pv.Plotter(off_screen=True, window_size=(640, 480))
    try:
        plotter.camera_position = [(0., 0., 10.), (0., 0., 0.), (0., 1., 0.)]
        plotter.render()
        renderer._plotter = plotter
        renderer.lx = renderer.ly = 10.
        punkt = renderer.screen_to_water(320., 240.)
        assert punkt is not None
        np.testing.assert_allclose(punkt, (0., 0.), rtol=0, atol=1e-9)
    finally:
        plotter.close()
