"""Geometrische Kerne von M2 (SPEC_V3.md Abschnitt 5): K3''-Stichprobe, K4''-Kontur."""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from segelphysik.core import bewegung as kin
from segelphysik.core import koerper_formen as msh

BUILDERS = {"cone": msh.build_cone, "box": msh.build_box, "pyramid": msh.build_pyramid}
PHASES = [0.0, 30.0, 60.0, 90.0, 120.0]


def _transformed(builder, phi_deg):
    v, f = builder()
    R = kin.rotation_matrix(math.radians(phi_deg))
    return v @ R.T, f


def test_k3_twotone_classification():
    for name, b in BUILDERS.items():
        for ph in PHASES:
            v, _ = _transformed(b, ph)
            below = int(np.sum(v[:, 2] < 0.0)); above = int(np.sum(v[:, 2] >= 0.0))
            assert below > 0 and above > 0, (name, ph, below, above)


def test_k4_contour_exists():
    for name, b in BUILDERS.items():
        for ph in PHASES:
            v, f = _transformed(b, ph)
            z = v[:, 2]
            crossings = sum(1 for tri in f
                            if (z[tri] < 0).any() and (z[tri] > 0).any())
            assert crossings >= 1, (name, ph)


def test_contour_symmetry_quarter_turns():
    counts = []
    for ph in (0.0, 90.0, 180.0, 270.0):
        v, _ = _transformed(BUILDERS["box"], ph)
        counts.append(int(np.sum(v[:, 2] < 0.0)))
    assert counts[0] == counts[1] == counts[2] == counts[3]
