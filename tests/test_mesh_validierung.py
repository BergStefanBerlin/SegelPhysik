import numpy as np
import pytest

from segelphysik.core import auftrieb, boot_bau, koerper_formen, massen
from segelphysik.core.koerper import Koerper, KoerperFehler


@pytest.fixture
def quader():
    return koerper_formen.bau_quader(2.0, 2.0, 2.0)


def test_validiertes_volumenmesh_hat_analytische_masse_und_traegheit(quader):
    punkte, flaechen = quader
    koerper = Koerper(form=quader, dichte=1000.0)

    assert koerper.verdrangend
    assert koerper.masse == pytest.approx(8000.0)
    assert np.allclose(koerper.traegheitstensor, np.eye(3) * (8000.0 * 2.0 / 3.0))
    assert np.allclose(koerper.traegheitstensor, koerper.traegheitstensor.T)
    assert np.linalg.eigvalsh(koerper.traegheitstensor).min() >= 0.0
    assert massen.validiere_mesh(punkte, flaechen)[4]


@pytest.mark.parametrize("punkte,flaechen", [
    (np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
               [0.0, np.nan, 1.0]]), np.array([[0, 1, 2]])),
    (np.array([[1e308, 0.0, 0.0], [-1e308, 0.0, 0.0],
               [0.0, 1e308, 0.0]]), np.array([[0, 1, 2]])),
    (np.zeros((3, 3)), np.array([[0, 1.5, 2]])),
    (np.zeros((3, 3)), np.array([[0, 1, 3]])),
    (np.zeros((3, 3)), np.array([[0, 0, 1]])),
    (np.zeros((0, 3)), np.array([[0, 1, 2]])),
    (np.zeros((3, 3)), np.zeros((0, 3), dtype=int)),
])
def test_mesh_eingangsvalidierung_lehnt_ungueltige_daten_ab(punkte, flaechen):
    with pytest.raises(ValueError):
        massen.validiere_mesh(punkte, flaechen)


def test_entartete_dreiecke_werden_abgelehnt():
    punkte = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="entartete"):
        massen.validiere_mesh(punkte, np.array([[0, 0, 1]]))


def test_offenes_mesh_mit_dichte_ist_keine_volumenkoerperforderung(quader):
    punkte, flaechen = quader
    with pytest.raises(KoerperFehler, match="geschlossen"):
        Koerper(form=(punkte, flaechen[:-1]), dichte=1000.0)


def test_offene_schale_ist_nicht_verdraengend_auch_mit_pseudovolumen(quader):
    punkte, flaechen = quader
    schale = Koerper(form=(punkte, flaechen[:-1]), flaechenmasse=1.0)
    assert not schale.verdrangend
    assert schale._volumen == 0.0

    ergebnis = auftrieb.kraftfunktion_berechne(
        schale, (0.0, 0.0, 0.0), pfad="exakt")
    assert ergebnis.V_tauch == 0.0
    assert ergebnis.F_A.z == 0.0


def test_widerspruechliche_flaechenorientierung_wird_abgelehnt(quader):
    punkte, flaechen = quader
    inkonsistent = flaechen.copy()
    inkonsistent[0] = inkonsistent[0, ::-1]

    with pytest.raises(KoerperFehler, match="Orientierung"):
        Koerper(form=(punkte, inkonsistent), dichte=1000.0)


def test_obj_lader_lehnt_ungueltige_meshdaten_mit_pfad_ab(tmp_path):
    obj = tmp_path / "ungueltig.obj"
    obj.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 4\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ungueltig.obj.*außerhalb"):
        boot_bau.lade_obj(str(obj))


@pytest.mark.parametrize("rotation,translation", [
    (np.eye(2), np.zeros(3)),
    (np.eye(3), np.array([0.0, np.inf, 0.0])),
    (np.diag([-1.0, 1.0, 1.0]), np.zeros(3)),
])
def test_verbands_pose_muss_endliche_rechtshaendige_rotation_sein(
        quader, rotation, translation):
    kind = Koerper(form=quader, dichte=1000.0)
    with pytest.raises(KoerperFehler, match="Relative"):
        Koerper(teile=[(kind, (rotation, translation))])


@pytest.mark.parametrize("dichte", [0.0, -1.0, np.inf, np.nan])
def test_dichte_muss_endlich_und_positiv_sein(quader, dichte):
    with pytest.raises(KoerperFehler, match="Dichte"):
        Koerper(form=quader, dichte=dichte)


def test_traegheitstensor_prueft_symmetrie_positivitaet_und_dreieck():
    with pytest.raises(ValueError, match="symmetrisch"):
        massen.validiere_traegheitstensor(
            np.array([[1.0, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]))
    with pytest.raises(ValueError, match="positiv semidefinit"):
        massen.validiere_traegheitstensor(np.diag([-1.0, 1.0, 1.0]))
    with pytest.raises(ValueError, match="Dreiecksungleichung"):
        massen.validiere_traegheitstensor(np.diag([1.0, 1.0, 3.0]))
