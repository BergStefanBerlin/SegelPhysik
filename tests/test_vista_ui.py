from types import SimpleNamespace

from segelphysik.render.vista import PyVistaRenderer

import pytest
pytestmark = [pytest.mark.gui, pytest.mark.integration]


class _Plotter:
    def __init__(self):
        self.texts = []

    def set_background(self, _color):
        pass

    def add_mesh(self, *_args, **_kwargs):
        pass

    def add_axes(self, **_kwargs):
        pass

    def add_text(self, text, **kwargs):
        self.texts.append((text, kwargs))


def test_visualisierung_zeigt_keine_texte_am_oberen_rand():
    plotter = _Plotter()
    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    renderer.pv = SimpleNamespace(
        Plotter=lambda **_kwargs: plotter,
        line_segments_from_points=lambda points: points,
        Line=lambda *args: args,
        Plane=lambda **kwargs: kwargs,
    )
    renderer.off_screen = True
    renderer.lx = 10
    renderer.ly = 8
    renderer.depth = 4
    renderer.skip_surf = True

    renderer.build()

    assert all(kwargs.get("position") != "upper_left"
               for _, kwargs in plotter.texts)
    assert all(kwargs.get("position") != "upper_right"
               for _, kwargs in plotter.texts)
