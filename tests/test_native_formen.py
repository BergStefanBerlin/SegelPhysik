import numpy as np
import pytest

from segelphysik.core import koerper_formen as formen
from segelphysik.core.rechenpfad import python_referenz

pytestmark = [pytest.mark.native]


@pytest.mark.parametrize("nseg", [6, 7, 16, 48, 64, 129])
def test_native_grundformen_behalten_punkte_dreiecke_und_aufloesung(monkeypatch, nseg):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(16026 + nseg)
    for _ in range(10):
        r, h, a = rng.uniform(.01, 10., size=3)
        for funktion, args, kwargs in (
            (formen.build_cone, (h, r, nseg), {}),
            (formen.build_box, (r, h, a), {}),
            (formen.build_pyramid, (r, h), {}),
            (formen.build_sphere, (r, nseg), {}),
            (formen.build_cylinder, (r, h, nseg), {}),
            (formen.build_cylinder, (r, h, nseg), {"lage": "liegend"}),
            (formen.build_plate, (r, h, a), {}),
            (formen.build_hexprism, (r, h, 0.), {}),
            (formen.build_hexprism, (r, h, .3 * h), {"lage": "liegend"}),
        ):
            with python_referenz():
                ref_p, ref_f = funktion(*args, **kwargs)
            p, f = funktion(*args, **kwargs)
            assert p.shape == ref_p.shape and p.dtype == ref_p.dtype
            assert f.shape == ref_f.shape and f.dtype == ref_f.dtype
            np.testing.assert_allclose(p, ref_p, rtol=0., atol=2e-12)
            np.testing.assert_array_equal(f, ref_f)


def test_native_ring_zentrierung_lage_und_schwerpunkt_gegen_referenz(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(17026)
    for _ in range(100):
        r, z, versatz = rng.normal(size=3)
        with python_referenz():
            ring = formen._ring(r, z, 31, versatz)
        np.testing.assert_allclose(formen._ring(r, z, 31, versatz), ring,
                                   rtol=0., atol=2e-12)
        p, f = formen.build_box(1., 2., 3.)
        p += rng.normal(size=3)
        with python_referenz():
            zentrum = formen._volumenschwerpunkt(p, f)
            zentriert, ref_f = formen._zentriert(p, f)
            liegend = formen._liegend(p)
        np.testing.assert_allclose(formen._volumenschwerpunkt(p, f), zentrum,
                                   rtol=0., atol=2e-12)
        cpp_p, cpp_f = formen._zentriert(p, f)
        np.testing.assert_allclose(cpp_p, zentriert, rtol=0., atol=2e-12)
        np.testing.assert_array_equal(cpp_f, ref_f)
        np.testing.assert_array_equal(formen._liegend(p), liegend)


@pytest.mark.parametrize("funktion,args", [
    (formen.build_cone, (0., 1., 64)),
    (formen.build_cone, (1., 1., 2)),
    (formen.build_box, (1., 0., 1.)),
    (formen.build_pyramid, (0., 1.)),
    (formen.build_sphere, (1., 5)),
    (formen.build_cylinder, (1., -1., 64)),
    (formen.build_hexprism, (1., 2., 2.)),
])
def test_native_formen_behalten_fehlervertraege(monkeypatch, funktion, args):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz(), pytest.raises(ValueError) as ref:
        funktion(*args)
    with pytest.raises(ValueError) as cpp:
        funktion(*args)
    assert str(cpp.value) == str(ref.value)


def test_native_formzentrierung_behaelt_bisherige_volumenschwelle(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    p, f = formen.build_box(1e-7, 1e-7, 1e-7)
    with python_referenz(), pytest.raises(ValueError, match="Koerper ohne Volumen"):
        formen._volumenschwerpunkt(p, f)
    with pytest.raises(ValueError, match="Koerper ohne Volumen"):
        formen._volumenschwerpunkt(p, f)


@pytest.mark.slow
def test_native_polyeder_behalten_huellflaechen_dreiecksfans_und_zentrierung(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(20026)
    box, _ = formen.build_box(2., 3., 4.)
    punkte = [box, box[::-1], np.array([[0., 0., 0.], [1., 0., 0.],
                                      [0., 1., 0.], [0., 0., 1.]])]
    punkte.extend(rng.normal(size=(12, 3)) for _ in range(100))
    for p in punkte:
        with python_referenz():
            ref_p, ref_f = formen._konvexe_huelle(p)
            ref_z, ref_zf = formen.build_polyhedron(p)
        cpp_p, cpp_f = formen._konvexe_huelle(p)
        assert cpp_p is p and ref_p is p
        np.testing.assert_array_equal(cpp_f, ref_f)
        cpp_z, cpp_zf = formen.build_polyhedron(p)
        np.testing.assert_array_equal(cpp_zf, ref_zf)
        np.testing.assert_allclose(cpp_z, ref_z, rtol=0., atol=2e-12)
    polygone = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
                [2, 3, 7, 6], [1, 2, 6, 5], [3, 0, 4, 7]]
    with python_referenz():
        ref_p, ref_f = formen.build_polyhedron(box, polygone)
    cpp_p, cpp_f = formen.build_polyhedron(box, polygone)
    np.testing.assert_array_equal(cpp_f, ref_f)
    np.testing.assert_allclose(cpp_p, ref_p, rtol=0., atol=2e-12)


@pytest.mark.parametrize("punkte", [
    np.ones((65, 3)), np.zeros((4, 3)),
    np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [1., 1., 0.]]),
])
def test_native_polyeder_behalten_fehlertexte(monkeypatch, punkte):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz(), pytest.raises(ValueError) as ref:
        formen.build_polyhedron(punkte)
    with pytest.raises(ValueError) as cpp:
        formen.build_polyhedron(punkte)
    assert str(cpp.value) == str(ref.value)
