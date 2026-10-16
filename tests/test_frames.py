import numpy as np
import pytest

from segelphysik.core.frames import Pose


def test_posekomposition_inversion_und_vektortransformation():
    wurzel = Pose(
        "modell", "wurzel", (2.0, 0.0, 0.0),
        (2.0 ** -0.5, 0.0, 0.0, 2.0 ** -0.5),
    )
    blatt = Pose(
        "wurzel", "blatt", (1.0, 0.0, 0.0),
        (1.0, 0.0, 0.0, 0.0),
    )
    zusammengesetzt = wurzel.komponieren(blatt)

    np.testing.assert_allclose(
        zusammengesetzt.punkt_transformieren((1.0, 0.0, 0.0)),
        (2.0, 2.0, 0.0),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        zusammengesetzt.vektor_transformieren((1.0, 0.0, 0.0)),
        (0.0, 1.0, 0.0),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        zusammengesetzt.invers().punkt_transformieren((2.0, 2.0, 0.0)),
        (1.0, 0.0, 0.0),
        atol=1e-12,
    )
    assert zusammengesetzt.ziel_frame == "modell"
    assert zusammengesetzt.quell_frame == "blatt"


def test_posekomposition_lehnt_unpassende_frames_und_ungueltige_daten_ab():
    pose = Pose("modell", "rumpf", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0))
    andere = Pose(
        "kamera", "blatt", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0))

    with pytest.raises(ValueError, match="Frames passen nicht"):
        pose.komponieren(andere)
    with pytest.raises(ValueError, match="Translation"):
        Pose("modell", "rumpf", (float("nan"), 0.0, 0.0),
             (1.0, 0.0, 0.0, 0.0))
