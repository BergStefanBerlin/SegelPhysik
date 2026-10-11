"""Smoke-Test (Quick-Win): Die Demo muss importierbar sein.

Schliesst die Luecke aus Schritt 2: Die Testsuite pruefte Bausteine,
aber nie, dass demo_app ueberhaupt importierbar ist (Lektion: Ein
gruener Baustein-Test beweist nicht, dass die Demo startet).
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pytest


def test_demo_importierbar_und_main_vorhanden():
    """demo_app muss ladbar sein; fehlt pyvista, wird geskippt (nicht rot)."""
    try:
        demo = importlib.import_module("segelphysik.demo_app")
    except ImportError as fehler:
        pytest.skip("Optionale Grafik-Abhaengigkeit fehlt: %s" % fehler)
    assert callable(getattr(demo, "main", None)), \
        "demo_app.main fehlt oder ist nicht aufrufbar"
