"""Grafik roehrenradius: bestehende Referenzvertraege."""
import numpy as np
import pytest


def test_w3_roehrenradius_formel():
    """roehren_radius = max(0.25 * marker_radius, 0.006); Marker-Radius =
    clamp(0.04 * halbe_Ausdehnung, 0.02, 0.16)."""
    from segelphysik.grafik_bruecke import GrafikBruecke
    br = GrafikBruecke.__new__(GrafikBruecke)
    class P:
        pass
    p1 = P(); p1.punkte = np.array([[0.2, 0, 0]])
    assert GrafikBruecke.roehren_radius(br, p1) == pytest.approx(0.006)
    p2 = P(); p2.punkte = np.array([[2.0, 0, 0]])
    assert GrafikBruecke.roehren_radius(br, p2) == pytest.approx(0.02)
