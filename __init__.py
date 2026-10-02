"""Segelphysik - dynamische Simulation einer segelnden Yacht (6 DOF).

Struktur:
    config.py          Physik-/Anzeige-Konstanten, Presets
    slider_defs.py     GUI-Slider-Definitionen
    math_utils.py      Quaternionen / Rotationen
    geometry.py        Rumpf + Kiel/Bulb/Ruder (QuaderVoxel)
    hydrostatics.py    Auftrieb, CB, Momente
    dynamics.py        Simulation (Newton-Euler, 6 Freiheitsgrade)
    hydrodynamics.py   Hydrodynamik (Schritt 2, aktuell Stub)
    water.py           Wasserzeichen-Feld
    rendering/         3D-Szene und Zeichen-Helfer
    app.py             GUI (QuaderApp)
    main.py            Einstiegspunkt
"""

__version__ = "0.1.0"
