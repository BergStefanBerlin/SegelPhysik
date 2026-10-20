import numpy as np
import pytest

from segelphysik.core import mesh
from segelphysik.core.dynamik_6dof import quaternion_matrix
from segelphysik.core.rechenpfad import python_referenz


def test_native_obj_polygontriangulierung_behaelt_ohren_und_indexreihenfolge(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(18026)
    for _ in range(1000):
        n = int(rng.integers(4, 20))
        a = np.linspace(0., 2. * np.pi, n, endpoint=False)
        radien = rng.uniform(.3, 2., size=n)
        p = np.column_stack((radien * np.cos(a), radien * np.sin(a), np.zeros(n)))
        r = quaternion_matrix(rng.normal(size=4))
        p = p @ r.T + rng.normal(size=3)
        ids = list(range(n))
        if rng.random() < .5:
            ids.reverse()
        if rng.random() < .5:
            ids.append(ids[0])
        with python_referenz():
            ref = mesh._trianguliere_polygon(p, ids, "probe.obj", 17)
        cpp = mesh._trianguliere_polygon(p, ids, "probe.obj", 17)
        assert cpp == ref
        assert type(cpp) is list and all(type(f) is tuple for f in cpp)


def test_native_polygon_selbstschnittpruefung_gegen_referenz(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    rng = np.random.default_rng(19026)
    for _ in range(1000):
        p = rng.normal(size=(int(rng.integers(3, 20)), 2))
        if rng.random() < .5:
            p += 1e6
        with python_referenz():
            ref = mesh._polygon_selbstschneidet(p, 1e-10)
        assert mesh._polygon_selbstschneidet(p, 1e-10) is ref


@pytest.mark.parametrize("punkte,index", [
    ([(0., 0., 0.), (1., 0., 0.)], [0, 1]),
    ([(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)], [0, 1, 1, 2]),
    ([(0., 0., 0.), (1., 0., 0.), (2., 0., 0.), (3., 0., 0.)], [0, 1, 2, 3]),
    ([(0., 0., 0.), (1., 0., 0.), (1., 1., .1), (0., 1., 0.)], [0, 1, 2, 3]),
    ([(0., 0., 0.), (1., 1., 0.), (0., 1., 0.), (1., 0., 0.)], [0, 1, 2, 3]),
])
def test_native_obj_polygonfehler_behalten_datei_zeile_und_text(monkeypatch, punkte, index):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    with python_referenz(), pytest.raises(ValueError) as ref:
        mesh._trianguliere_polygon(punkte, index, "probe.obj", 17)
    with pytest.raises(ValueError) as cpp:
        mesh._trianguliere_polygon(punkte, index, "probe.obj", 17)
    assert str(cpp.value) == str(ref.value)


def test_native_obj_skalierung_rotation_und_pfadgetrennter_dateicache(monkeypatch, tmp_path):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    (tmp_path / "flaeche.obj").write_text(
        "v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf 1 2 3 4\n", encoding="utf-8")
    quelle = {"quelle": "obj", "datei": "flaeche.obj"}
    r = quaternion_matrix((1., .1, .2, .3))
    kwargs = dict(paketwurzel=tmp_path, obj_zu_m=.3, obj_achsenmatrix_zu_blatt=r)
    mesh._obj_mesh_cached.cache_clear()
    cpp = mesh.mesh_aus_quelle(quelle, **kwargs)
    with python_referenz():
        ref = mesh.mesh_aus_quelle(quelle, **kwargs)
        assert mesh.mesh_aus_quelle(quelle, **kwargs) is ref
    assert mesh.mesh_aus_quelle(quelle, **kwargs) is cpp
    assert cpp is not ref
    assert mesh._obj_mesh_cached.cache_info().currsize == 2
    np.testing.assert_allclose(cpp.punkte_si, ref.punkte_si, rtol=0., atol=1e-15)
    np.testing.assert_array_equal(cpp.dreiecke, ref.dreiecke)
    assert cpp.metadaten == ref.metadaten and cpp.frame == ref.frame
    assert not cpp.punkte_si.flags.writeable
