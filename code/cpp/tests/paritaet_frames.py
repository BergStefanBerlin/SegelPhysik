"""Direkte M2-Kandidatenvergleiche; keine produktive Backendumschaltung."""
import gc

import numpy as np
import pytest

import _segelphysik_native as native
from segelphysik.core import dynamik_6dof as referenz
from segelphysik.core import frames

pytestmark = [pytest.mark.native, pytest.mark.integration]


# Grenze aus tests/test_frames.py; kein pauschales Physikfehlerbudget.
ATOL = 1e-12


def gleich(a, b):
    np.testing.assert_allclose(a, b, rtol=0., atol=ATOL)


@pytest.mark.parametrize("q", [
    [1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., 1., 0.], [0., 0., 0., 1.],
    [1., 1., 1., 0.], [-1., -2., .3, .4], [3., 0., 0., 0.],
])
def test_quaternionen_und_alle_matrixfallzweige(q):
    q = np.array(q)
    gleich(native.quaternion_normalisieren(q), referenz.quaternion_normalisieren(q))
    rotation = native.quaternion_matrix(q)
    gleich(rotation, referenz.quaternion_matrix(q))
    gleich(native.quaternion_aus_matrix(rotation), referenz.quaternion_aus_matrix(rotation))
    gleich(native.quaternion_matrix(native.quaternion_aus_matrix(rotation)), rotation)


def test_quaternion_und_matrix_1000_deterministische_eingaben():
    rng = np.random.default_rng(1010)
    for q in rng.normal(size=(1000, 4)):
        rotation = referenz.quaternion_matrix(q)
        gleich(native.quaternion_normalisieren(q), referenz.quaternion_normalisieren(q))
        gleich(native.quaternion_matrix(q), rotation)
        gleich(native.quaternion_aus_matrix(rotation), referenz.quaternion_aus_matrix(rotation))
        p = rng.normal(size=4)
        gleich(native.quaternion_multiplizieren(q, p),
               referenz._quaternion_multiplizieren(q, p))


@pytest.mark.parametrize("winkel", [
    0., np.pi, -np.pi, 2. * np.pi / 3.,
    np.nextafter(2. * np.pi / 3., 0.), np.nextafter(2. * np.pi / 3., np.inf),
])
@pytest.mark.parametrize("achse", [[1., 0., 0.], [1., 1., 1.], [-1., -1., 0.]])
def test_matrixzweiggrenzen_und_pose_inverse_erhalten_quaternionvorzeichen(winkel, achse):
    rotation = frames.rotationsmatrix_achsenwinkel(achse, winkel)
    q = np.array(referenz.quaternion_aus_matrix(rotation))
    gleich(native.quaternion_aus_matrix(rotation), q)
    p = frames.Pose("welt", "rumpf", (1., 2., 3.), q)
    n = native.Pose("welt", "rumpf", np.array([1., 2., 3.]), q)
    gleich(n.invers().rotation_quaternion_wxyz, p.invers().rotation_quaternion_wxyz)


@pytest.mark.parametrize("q", [np.zeros(4), np.full(4, np.nan), np.full(4, np.inf)])
def test_ungueltige_quaternionen_scheitern_in_beiden_pfaden(q):
    for funktion in (referenz.quaternion_normalisieren, native.quaternion_normalisieren):
        with pytest.raises(ValueError):
            funktion(q)


@pytest.mark.parametrize("rotation", [
    np.zeros((3, 3)), np.diag([-1., 1., 1.]), np.full((3, 3), np.nan),
    np.eye(3) * 2., np.zeros((4, 3)),
])
def test_ungueltige_matrix_scheitert_in_beiden_pfaden(rotation):
    for funktion in (referenz.quaternion_aus_matrix, native.quaternion_aus_matrix):
        with pytest.raises(ValueError):
            funktion(rotation)


@pytest.mark.parametrize("omega", [
    [0., 0., 0.], [1e-16, 0., 0.], [.1, -.2, .3], [3., 2., -1.],
])
def test_orientierung_schritt(omega):
    q = np.array([2., -.3, .2, .4])
    omega = np.array(omega)
    gleich(native.orientierung_schritt(q, omega, .004),
           referenz._orientierung_schritt(q, omega, .004))


@pytest.mark.parametrize("achse", [[1., 0., 0.], [1., 2., -3.]])
@pytest.mark.parametrize("winkel", [0., .3, -1.2, np.pi])
def test_achsenwinkel(achse, winkel):
    gleich(native.rotationsmatrix_achsenwinkel(np.array(achse), winkel),
           frames.rotationsmatrix_achsenwinkel(achse, winkel))


@pytest.mark.parametrize("achse,winkel", [
    ([0., 0., 0.], .3), ([np.nan, 0., 0.], .3), ([1., 0., 0.], np.inf),
])
def test_achsenwinkel_ungueltig(achse, winkel):
    for funktion in (native.rotationsmatrix_achsenwinkel, frames.rotationsmatrix_achsenwinkel):
        with pytest.raises(ValueError):
            funktion(np.array(achse), winkel)


def test_pose_komposition_inverse_punkte_vektoren_und_langlebige_ausgabe():
    rng = np.random.default_rng(1010)
    for _ in range(100):
        t, q = rng.normal(size=3), rng.normal(size=4)
        t2, q2 = rng.normal(size=3), rng.normal(size=4)
        p = frames.Pose("welt", "rumpf", t, q)
        innen = frames.Pose("rumpf", "kiel", t2, q2)
        n = native.Pose("welt", "rumpf", t, q)
        n_innen = native.Pose("rumpf", "kiel", t2, q2)
        for original, kandidat in ((p, n), (p.invers(), n.invers()),
                                    (p.komponieren(innen), n.komponieren(n_innen))):
            assert original.ziel_frame == kandidat.ziel_frame
            assert original.quell_frame == kandidat.quell_frame
            gleich(kandidat.translation_m, original.translation_m)
            gleich(kandidat.rotationsmatrix, original.rotationsmatrix)
            punkt = rng.normal(size=3)
            gleich(kandidat.punkt_transformieren(punkt), original.punkt_transformieren(punkt))
            gleich(kandidat.vektor_transformieren(punkt), original.vektor_transformieren(punkt))
            punkte = rng.normal(size=(60, 3))[::-2]
            gleich(kandidat.punkte_transformieren(punkte), original.punkte_transformieren(punkte))
            vorbereitete = native.Mesh(punkte, np.empty((0, 3), dtype=np.int64))
            gleich(kandidat.vorbereitete_punkte_transformieren(vorbereitete),
                   original.punkte_transformieren(punkte))
    ausgabe = n.punkte_transformieren(np.zeros((0, 3)))
    del n
    gc.collect()
    assert ausgabe.shape == (0, 3) and ausgabe.dtype == np.float64


def test_pose_frames_und_ungueltige_eingaben():
    n = native.Pose("welt", "rumpf", np.zeros(3), np.array([1., 0., 0., 0.]))
    with pytest.raises(ValueError, match="Frames"):
        n.komponieren(native.Pose("falsch", "kiel", np.zeros(3), np.array([1., 0., 0., 0.])))
    for funktion in (n.punkt_transformieren, n.vektor_transformieren):
        with pytest.raises(ValueError):
            funktion(np.full(3, np.nan))
    with pytest.raises(ValueError):
        n.punkte_transformieren(np.full((5, 3), np.nan))


def test_punkttransform_ueberlauf_liefert_keine_nichtendliche_erfolgsantwort():
    n = native.Pose(
        "welt", "rumpf", np.full(3, 1e308), np.array([1., 0., 0., 0.]))
    punkte = np.full((1, 3), 1e308)
    mesh = native.Mesh(punkte, np.empty((0, 3), dtype=np.int64))
    for rechnen in (lambda: n.punkte_transformieren(punkte),
                    lambda: n.vorbereitete_punkte_transformieren(mesh)):
        with pytest.raises(ValueError, match="nicht endlich"):
            rechnen()


@pytest.mark.parametrize("anzahl", [1, 3, 30])
def test_vorbereitete_koerperaggregation_mit_steiner_und_punktmassen(anzahl):
    from segelphysik.core.koerper import Koerper
    from segelphysik.core.koerper_formen import build_box
    from segelphysik.core.massen import validiere_traegheitstensor

    rng = np.random.default_rng(1010)
    python_teile, native_teile = [], []
    for nummer in range(anzahl):
        if nummer % 3 == 1:
            kind = Koerper(
                punktmasse=True, masse=2., verdrangend=False, zustand=None)
        else:
            kind = Koerper(form=build_box(1., 2., 3.), masse=2., zustand=None)
        q = referenz.quaternion_normalisieren(rng.normal(size=4))
        rotation, translation = referenz.quaternion_matrix(q), rng.normal(size=3)
        python_teile.append((kind, (rotation, translation)))
        native_teile.append(native.Koerperteil(
            kind.masse, kind.traegheitstensor,
            native.Mesh(kind.punkte, kind.dreiecke, verdraengend=kind.verdrangend),
            native.Pose("verband", "teil", translation, q)))
    original = Koerper(teile=python_teile, zustand=None)
    kandidat = native.verband_aggregieren(native_teile, native.Abbruch())
    kontext = native.VerbandKontext(native_teile, 7)
    assert kontext.version == 7
    aus_kontext = kontext.aggregieren(native.Abbruch())
    np.testing.assert_array_equal(aus_kontext.traegheit, kandidat.traegheit)
    np.testing.assert_array_equal(aus_kontext.punkte, kandidat.punkte)
    del native_teile, kontext
    gc.collect()
    assert kandidat.masse == original.masse
    gleich(kandidat.schwerpunkt, original._r_eingabe)
    # Die vorhandene native NumPy-Eigenwertvalidierung bleibt Aufbaugrenze.
    gleich(validiere_traegheitstensor(kandidat.traegheit), original.traegheitstensor)
    gleich(kandidat.punkte, original.punkte)
    np.testing.assert_array_equal(kandidat.dreiecke, original.dreiecke)
    for nummer, (_kind, (r, t)) in enumerate(original.teile):
        gleich(kandidat.teilrotationen[nummer], r)
        gleich(kandidat.teilzentren[nummer], t)


def test_aggregation_bricht_explizit_ab_und_verlangt_teile():
    with pytest.raises(ValueError):
        native.verband_aggregieren([], native.Abbruch())
    abbruch = native.Abbruch()
    abbruch.abbrechen()
    teil = native.Koerperteil(
        1., np.eye(3), native.Mesh(np.empty((0, 3)), np.empty((0, 3), dtype=np.int64)),
        native.Pose("verband", "teil", np.zeros(3), np.array([1., 0., 0., 0.])))
    with pytest.raises(RuntimeError, match="abgebrochen"):
        native.verband_aggregieren([teil], abbruch)


@pytest.mark.parametrize("basis_vorhanden", [False, True])
@pytest.mark.parametrize("gelenk_vorhanden", [False, True])
@pytest.mark.parametrize("winkel", [None, -.3, 1.])
def test_modellpose_gelenkwinkel_und_override(basis_vorhanden, gelenk_vorhanden, winkel):
    from types import SimpleNamespace
    from segelphysik.core import native_backend

    pose = SimpleNamespace(
        translation_m=(1., 2., 3.),
        rotation_quaternion_wxyz=(.5, .5, .5, .5)) if basis_vorhanden else None
    gelenk = SimpleNamespace(
        achse_eltern=(1., 2., -3.), winkel_rad=.7) if gelenk_vorhanden else None
    original = frames.pose_mit_gelenkwinkel(pose, gelenk, winkel)
    kandidat = native_backend.pose_mit_gelenkwinkel(pose, gelenk, winkel)
    assert kandidat.ziel_frame == original.ziel_frame
    assert kandidat.quell_frame == original.quell_frame
    gleich(kandidat.translation_m, original.translation_m)
    gleich(kandidat.rotation_quaternion_wxyz, original.rotation_quaternion_wxyz)
    gleich(kandidat.rotationsmatrix, original.rotationsmatrix)
