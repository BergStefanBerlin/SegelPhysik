import numpy as np
import pytest

from segelphysik.core.mesh import (
    Mesh,
    lade_obj,
    mesh_aus_quelle,
    pfad_im_paket_aufloesen,
    validiere_mesh_fuer_masse,
)
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.massen import pruefe_mesh_selbstueberschneidung


def test_mesh_ist_unveraenderlich_und_uebernimmt_eingaben_nicht():
    punkte = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    dreiecke = np.array([[0, 1, 2]], dtype=np.int64)
    mesh = Mesh.aus_legacy_tupel(
        (punkte, dreiecke), frame="blatt", metadaten={"quelle": "test"})
    punkte[0] = 9
    dreiecke[0] = 2

    assert np.array_equal(mesh.punkte_si[0], [0, 0, 0])
    assert np.array_equal(mesh.dreiecke[0], [0, 1, 2])
    with pytest.raises(ValueError):
        mesh.punkte_si[0, 0] = 2
    with pytest.raises(ValueError):
        mesh.punkte_si.setflags(write=True)
    with pytest.raises(TypeError):
        mesh.metadaten["quelle"] = "geändert"


def test_mesh_fuer_volumenmasse_normiert_globale_innenorientierung():
    punkte, dreiecke = build_box(2.0, 1.0, 0.5)
    mesh = Mesh(punkte, dreiecke[:, [0, 2, 1]], frame="blatt")

    korrigiert = validiere_mesh_fuer_masse(mesh)

    assert korrigiert.dreiecke.shape == dreiecke.shape
    assert np.array_equal(
        korrigiert.dreiecke, dreiecke)


def test_mesh_massengueltigkeit_unterscheidet_volumen_und_schale():
    punkte = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    mesh = Mesh(punkte, [[0, 1, 2]], frame="blatt")

    with pytest.raises(ValueError, match="geschlossen"):
        validiere_mesh_fuer_masse(mesh)
    assert validiere_mesh_fuer_masse(
        mesh, wanddicke_m=0.01).frame == "blatt"


def test_mesh_fuer_schale_lehnt_lokalen_orientierungsfehler_ab():
    punkte = np.array(
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)
    mesh = Mesh(punkte, [[0, 1, 2], [0, 3, 2]], frame="blatt")

    with pytest.raises(ValueError, match="Orientierung"):
        validiere_mesh_fuer_masse(mesh, wanddicke_m=0.01)


def test_meshvalidierung_erkennt_nicht_benachbarte_selbstueberschneidung():
    punkte = np.array([
        [0, 0, 0], [2, 0, 0], [0, 2, 0],
        [0.5, 0.2, -1], [0.5, 1, 1], [0.5, 1, -1],
    ], dtype=float)
    dreiecke = np.array([[0, 1, 2], [3, 4, 5]])

    with pytest.raises(ValueError, match="Dreiecke 0 und 1"):
        pruefe_mesh_selbstueberschneidung(punkte, dreiecke)


def test_meshvalidierung_erkennt_koplanare_ueberlappung():
    punkte = np.array([
        [0, 0, 0], [2, 0, 0], [0, 2, 0],
        [0.5, 0.5, 0], [2, 0.5, 0], [0.5, 2, 0],
    ], dtype=float)

    with pytest.raises(ValueError, match="selbstüberschneidend"):
        pruefe_mesh_selbstueberschneidung(
            punkte, [[0, 1, 2], [3, 4, 5]])


def test_meshvalidierung_cache_prueft_geaenderte_geometrie_erneut():
    dreiecke = [[0, 1, 2], [3, 4, 5]]
    getrennt = np.array([
        [0, 0, 0], [2, 0, 0], [0, 2, 0],
        [0.5, 0.2, 2], [0.5, 1, 3], [0.5, 1, 2],
    ], dtype=float)
    pruefe_mesh_selbstueberschneidung(getrennt, dreiecke)

    ueberschneidend = getrennt.copy()
    ueberschneidend[3:] = [
        [0.5, 0.2, -1], [0.5, 1, 1], [0.5, 1, -1]]
    with pytest.raises(ValueError, match="Dreiecke 0 und 1"):
        pruefe_mesh_selbstueberschneidung(ueberschneidend, dreiecke)


def test_meshvalidierung_ignoriert_geteilte_kanten_und_getrennte_komponenten():
    punkte = np.array([
        [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
        [3, 0, 0], [4, 0, 0], [3, 1, 0],
    ], dtype=float)

    pruefe_mesh_selbstueberschneidung(
        punkte, [[0, 1, 2], [0, 2, 3], [4, 5, 6]])


def test_meshvalidierung_gibt_selbstueberschneidung_mit_kontext_weiter():
    punkte = np.array([
        [0, 0, 0], [2, 0, 0], [0, 2, 0],
        [0.5, 0.2, -1], [0.5, 1, 1], [0.5, 1, -1],
    ], dtype=float)
    mesh = Mesh(punkte, [[0, 1, 2], [3, 4, 5]], frame="blatt")

    with pytest.raises(
            ValueError, match="yacht1/rigg/mast: Mesh ist selbstüberschneidend"):
        validiere_mesh_fuer_masse(
            mesh, wanddicke_m=0.01,
            fehlerkontext="yacht1/rigg/mast")


def test_obj_lader_unterstuetzt_negative_indizes_uv_normalen_und_quads(tmp_path):
    pfad = tmp_path / "quad.obj"
    pfad.write_text(
        "v 0 0 0\n"
        "v 1 0 0\n"
        "v 1 1 0\n"
        "v 0 1 0\n"
        "vt 0 0\n"
        "vt 1 0\n"
        "vt 1 1\n"
        "vt 0 1\n"
        "vn 0 0 1\n"
        "f -4/1/1 -3/2/1 -2/3/1 -1/4/1\n",
        encoding="utf-8",
    )

    mesh = lade_obj(pfad)

    assert mesh.frame == "obj"
    assert mesh.dreiecke.shape == (2, 3)
    assert sum(
        np.linalg.norm(np.cross(
            mesh.punkte_si[t[1]] - mesh.punkte_si[t[0]],
            mesh.punkte_si[t[2]] - mesh.punkte_si[t[0]]))
        / 2.0 for t in mesh.dreiecke) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "zusaetze,face",
    [
        ("vt 0 0\n", "f 1/2 2/1 3/1\n"),
        ("vn 0 0 1\n", "f 1//2 2//1 3//1\n"),
        ("vt nan 0\n", "f 1/1 2/1 3/1\n"),
        ("vn 0 inf 1\n", "f 1//1 2//1 3//1\n"),
    ],
)
def test_obj_lader_prueft_textur_und_normalenreferenzen(
        tmp_path, zusaetze, face):
    pfad = tmp_path / "ungueltige_referenz.obj"
    pfad.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\n"
        + zusaetze + face,
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        lade_obj(pfad)


def test_obj_lader_trianguliert_konkaves_polygon_ohne_faecherfehler(tmp_path):
    pfad = tmp_path / "konkav.obj"
    pfad.write_text(
        "v 0 0 0\n"
        "v 2 0 0\n"
        "v 2 2 0\n"
        "v 1 1 0\n"
        "v 0 2 0\n"
        "f 1 2 3 4 5\n",
        encoding="utf-8",
    )

    mesh = lade_obj(pfad)
    flaeche = sum(
        np.linalg.norm(np.cross(
            mesh.punkte_si[t[1]] - mesh.punkte_si[t[0]],
            mesh.punkte_si[t[2]] - mesh.punkte_si[t[0]]))
        / 2.0 for t in mesh.dreiecke)

    assert mesh.dreiecke.shape == (3, 3)
    assert flaeche == pytest.approx(3.0)


@pytest.mark.parametrize(
    "vertices,face,fehler",
    [
        ("v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 1\n",
         "f 1 2 3 4\n", "nicht-planare"),
        ("v 0 0 0\nv 2 2 0\nv 0 2 0\nv 2 0 0\nv 3 3 0\n",
         "f 1 2 3 4 5\n", "selbstschneidend"),
        ("v 0 0 0\nv 1 0 0\nv 0 1 0\n",
         "f 0 2 3\n", "beginnen bei 1"),
    ],
)
def test_obj_lader_lehnt_unsichere_polygone_und_indizes_ab(
        tmp_path, vertices, face, fehler):
    pfad = tmp_path / "ungueltig.obj"
    pfad.write_text(vertices + face, encoding="utf-8")

    with pytest.raises(ValueError, match=fehler):
        lade_obj(pfad)


def test_paketpfade_weisen_traversal_absolute_pfade_und_symlink_ausserhalb_ab(
        tmp_path):
    paket = tmp_path / "paket"
    paket.mkdir()
    ausserhalb = tmp_path / "ausserhalb.obj"
    ausserhalb.write_text("mesh", encoding="utf-8")
    with pytest.raises(ValueError, match="Traversal"):
        pfad_im_paket_aufloesen(paket, "../ausserhalb.obj")
    with pytest.raises(ValueError, match="relativ|absolut"):
        pfad_im_paket_aufloesen(paket, str(ausserhalb.resolve()))
    try:
        (paket / "link.obj").symlink_to(ausserhalb)
    except OSError:
        pytest.skip("Symlinks sind in dieser Windows-Umgebung nicht verfügbar")
    with pytest.raises(ValueError, match="Paketwurzel"):
        pfad_im_paket_aufloesen(paket, "link.obj")


def test_quellenresolver_wendet_obj_einheiten_und_achsenmatrix_an(tmp_path):
    paket = tmp_path / "yacht1"
    (paket / "mesh").mkdir(parents=True)
    (paket / "mesh" / "teil.obj").write_text(
        "v 4 2 3\nv 5 2 3\nv 4 3 3\nf 1 2 3\n",
        encoding="utf-8",
    )
    achsen = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]

    mesh = mesh_aus_quelle(
        {"quelle": "obj", "datei": "mesh/teil.obj"},
        paketwurzel=paket,
        obj_zu_m=0.25,
        obj_achsenmatrix_zu_blatt=achsen,
        fehlerkontext="yacht1/root/teil",
    )

    assert mesh.frame == "blatt"
    np.testing.assert_allclose(
        mesh.punkte_si,
        [[0.75, 1.0, 0.5], [0.75, 1.25, 0.5], [0.75, 1.0, 0.75]],
    )
    assert np.array_equal(mesh.dreiecke, [[0, 1, 2]])


def test_obj_mesh_cache_wird_nach_dateiaenderung_invalidiert(tmp_path):
    paket = tmp_path / "yacht1"
    paket.mkdir()
    datei = paket / "teil.obj"
    achsen = np.eye(3)
    datei.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
        encoding="utf-8",
    )
    quelle = {"quelle": "obj", "datei": "teil.obj"}
    erster = mesh_aus_quelle(
        quelle, paketwurzel=paket, obj_zu_m=1.0,
        obj_achsenmatrix_zu_blatt=achsen)

    datei.write_text(
        "v 0 0 0\nv 10 0 0\nv 0 1 0\nf 1 2 3\n",
        encoding="utf-8",
    )
    zweiter = mesh_aus_quelle(
        quelle, paketwurzel=paket, obj_zu_m=1.0,
        obj_achsenmatrix_zu_blatt=achsen)

    assert erster.punkte_si[1, 0] == 1.0
    assert zweiter.punkte_si[1, 0] == 10.0


def test_quellenresolver_formquelle_liefert_kanonisches_si_mesh():
    mesh = mesh_aus_quelle(
        {
            "quelle": "form",
            "parameter": {"typ": "box", "dx_m": 2, "dy_m": 1, "dz_m": 0.5},
        },
        paketwurzel=".",
        obj_zu_m=0.25,
        obj_achsenmatrix_zu_blatt=np.eye(3),
    )

    assert mesh.frame == "blatt"
    assert mesh.punkte_si.shape[1] == 3
    assert mesh.dreiecke.shape[1] == 3
    assert mesh.metadaten["typ"] == "box"
