import numpy as np
import pytest

from segelphysik.core.hydrostatik import (
    HydrostatikFehler,
    wasserlinien_bei_pose,
    wasserlinien_querschnitt,
)
from segelphysik.core.koerper_formen import bau_quader


@pytest.fixture
def ponton():
    return bau_quader(2.0, 2.0, 2.0)


def test_zentrierter_ponton_liefert_analytische_querschnittswerte(ponton):
    ergebnis = wasserlinien_bei_pose([ponton], z=0.0, phi=0.0)

    assert ergebnis.flaeche_m2 == pytest.approx(4.0)
    assert ergebnis.schwerpunkt_m == pytest.approx((0.0, 0.0, 0.0))
    np.testing.assert_allclose(
        ergebnis.flaechenkern_m4,
        ((4.0 / 3.0, 0.0), (0.0, 4.0 / 3.0)))


def test_geneigter_ponton_liefert_analytische_flaeche_und_tensor(ponton):
    ergebnis = wasserlinien_bei_pose([ponton], z=0.0, phi=np.pi / 4)

    assert ergebnis.flaeche_m2 == pytest.approx(4.0 * np.sqrt(2.0))
    assert ergebnis.schwerpunkt_m == pytest.approx((0.0, 0.0, 0.0))
    np.testing.assert_allclose(
        ergebnis.flaechenkern_m4,
        ((8.0 * np.sqrt(2.0) / 3.0, 0.0),
         (0.0, 4.0 * np.sqrt(2.0) / 3.0)), atol=1e-12)


def test_trockene_pose_und_tangentialkontakt_liefern_endliche_werte(ponton):
    trocken = wasserlinien_bei_pose([ponton], z=2.0, phi=0.0)
    tangential = wasserlinien_bei_pose([ponton], z=1.0, phi=0.0)

    assert trocken.flaeche_m2 == 0.0
    assert np.array_equal(trocken.schwerpunkt_m, np.zeros(3))
    assert np.array_equal(trocken.flaechenkern_m4, np.zeros((2, 2)))
    assert tangential.flaeche_m2 == pytest.approx(4.0)
    assert np.isfinite(tangential.schwerpunkt_m).all()
    assert np.isfinite(tangential.flaechenkern_m4).all()


def test_getrennte_pontons_werden_als_mehrere_ringe_aggregiert(ponton):
    punkte, dreiecke = ponton
    rechts = (punkte + np.array((3.0, 0.0, 0.0)), dreiecke)
    ergebnis = wasserlinien_querschnitt([ponton, rechts])

    assert ergebnis.flaeche_m2 == pytest.approx(8.0)
    assert ergebnis.schwerpunkt_m == pytest.approx((1.5, 0.0, 0.0))
    np.testing.assert_allclose(
        ergebnis.flaechenkern_m4,
        ((8.0 / 3.0, 0.0), (0.0, 62.0 / 3.0)))


def test_gegenlaeufig_orientiertes_mesh_wird_normalisiert(ponton):
    punkte, dreiecke = ponton
    umgekehrt = (punkte, dreiecke[:, [0, 2, 1]])

    ergebnis = wasserlinien_querschnitt([umgekehrt])

    assert ergebnis.flaeche_m2 == pytest.approx(4.0)
    np.testing.assert_allclose(
        ergebnis.flaechenkern_m4,
        ((4.0 / 3.0, 0.0), (0.0, 4.0 / 3.0)))


def test_offenes_mesh_und_ungueltige_toleranz_werden_abgelehnt(ponton):
    punkte, dreiecke = ponton

    with pytest.raises(HydrostatikFehler, match="geschlossene"):
        wasserlinien_querschnitt([(punkte, dreiecke[:-1])])
    with pytest.raises(HydrostatikFehler, match="Toleranz"):
        wasserlinien_querschnitt([ponton], toleranz=0.0)
