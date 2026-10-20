import numpy as np
import pytest

from segelphysik.core.bewegung import rotation_matrix
from segelphysik.core.dynamik_6dof import (
    Zustand6DOF, anzeige_interpolieren, quaternion_slerp,
)
from segelphysik.core.native_backend import zustand_vorbereiten
from segelphysik.core.rechenpfad import python_referenz
from segelphysik.core.stationaer_hydrodynamik import _rotation
from segelphysik.core.stoerung import rotationsmatrix
from werkzeuge.migration_worker import folgevergleich


def test_slerp_1000_zufaellige_und_antipodale_quaternionen(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(20261020)
    for i in range(1000):
        anfang, ende = rng.normal(size=(2, 4))
        if i % 3 == 0:
            ende = -anfang
        anteil = rng.uniform(-1., 2.)
        with python_referenz():
            erwartet = quaternion_slerp(anfang, ende, anteil)
        np.testing.assert_allclose(
            quaternion_slerp(anfang, ende, anteil), erwartet, rtol=0., atol=1e-14)


@pytest.mark.parametrize("rueckstand", [0., 1., 10.])
def test_anzeigefolge_mit_wachsendem_puffer_bleibt_paritaetisch(monkeypatch, rueckstand):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    verlauf = [(i * .1, Zustand6DOF(
        position=(i * .01, -.2, .1), quaternion=(1., 0., 0., i * .01),
        geschwindigkeit_koerper=(i, .2, .1))) for i in range(4)]
    zeit = 0.
    for i in range(200):
        if i % 3 == 0:
            t = verlauf[-1][0] + .1
            verlauf.append((t, Zustand6DOF(position=(t, 0., 0.))))
        vergangen = 0. if i % 20 == 0 else .016
        with python_referenz():
            erwartet = anzeige_interpolieren(verlauf, zeit, vergangen, rueckstand)
        aktuell = anzeige_interpolieren(verlauf, zeit, vergangen, rueckstand)
        assert aktuell[:2] == erwartet[:2]
        assert aktuell[0] >= zeit
        assert aktuell[0] <= verlauf[-1][0]
        np.testing.assert_allclose(
            zustand_vorbereiten(aktuell[2]).werte,
            zustand_vorbereiten(erwartet[2]).werte, rtol=0., atol=1e-14)
        zeit = aktuell[0]
        verlauf = verlauf[aktuell[1]:]


def test_einzelpose_wird_nicht_veraendert(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    pose = Zustand6DOF(quaternion=(2., 0., 0., 0.))
    assert anzeige_interpolieren([(0., pose)], 0., 1., .1)[2] is pose


def test_rotationen_und_achsenwinkel_mit_standardargument(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(15)
    for winkel in rng.uniform(-np.pi, np.pi, size=(100, 3)):
        with python_referenz():
            euler = _rotation(*winkel)
            achse = rotation_matrix(winkel[0])
        np.testing.assert_allclose(_rotation(*winkel), euler, rtol=0., atol=1e-15)
        np.testing.assert_allclose(rotationsmatrix(winkel), euler, rtol=0., atol=1e-15)
        np.testing.assert_allclose(rotation_matrix(winkel[0]), achse, rtol=0., atol=1e-15)
        np.testing.assert_array_equal(
            rotation_matrix(phi=winkel[0]), rotation_matrix(winkel[0]))


def test_vorlaeufige_pruefung_bewahrt_strenge_fehler_und_erkennt_grobe_mutation():
    def daten():
        return {
            "zeit_s": np.array([0., .004]), "zustaende": np.zeros((2, 13)),
            "kraft_offsets": np.array([0, 16], dtype=np.int64),
            "schema_indices": np.array([0], dtype=np.int64),
            "kraftwerte": np.zeros(16),
        }
    ref, cpp = daten(), daten()
    cpp["zustaende"][1, 0] = 1e-8
    cpp["kraftwerte"][7] = .2
    result = folgevergleich(ref, cpp, [()], [()])
    assert result["vorlaeufig_bestanden"]
    assert not result["streng_zustand_bestanden"]
    assert not result["streng_kraft_bestanden"]
    cpp["kraftwerte"][7] = 10.
    assert not folgevergleich(ref, cpp, [()], [()])["vorlaeufig_bestanden"]
    cpp["zustaende"][0, 0] = np.nan
    with pytest.raises(AssertionError, match="Nicht-endliche"):
        folgevergleich(ref, cpp, [()], [()])
