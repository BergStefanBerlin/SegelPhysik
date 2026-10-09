"""Fluid-Backends (v0.3a): NumPy-Referenz (core.sph) und Taichi/GPU.

Der GPU-Kern importiert bevorzugt `taichi_forge` (Fork, Python 3.10-3.14,
Vulkan) und faellt auf upstream `taichi` (Python <= 3.10) zurueck.
"""
try:
    from .taichi_sph import TaichiSphWater  # noqa: F401
except ImportError:  # taichi nicht installiert -> nur NumPy-Referenz
    TaichiSphWater = None
