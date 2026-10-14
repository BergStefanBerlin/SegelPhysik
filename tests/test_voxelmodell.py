from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core import auftrieb, koerper_formen, voxelmodell as vm


@pytest.fixture
def quader():
    return koerper_formen.bau_quader(2.0, 2.0, 2.0)


def test_koerperfestes_raster_liefert_analytisches_tauchvolumen(quader):
    raster = vm.KoerperfestesVoxelmodell([quader], aufloesung=0.5)

    volumen, schwerpunkt = raster.auswerten(z=-0.5, phi=0.0)

    assert volumen == pytest.approx(6.0)
    assert schwerpunkt == pytest.approx((0.0, 0.0, -0.75))


def test_trocken_tangential_und_vollstaendig_eingetaucht(quader):
    raster = vm.KoerperfestesVoxelmodell([quader], aufloesung=0.5)

    assert raster.auswerten(z=2.0, phi=0.0)[0] == 0.0
    assert raster.auswerten(z=1.0, phi=0.0)[0] == 0.0
    assert raster.auswerten(z=-1.0, phi=0.0)[0] == pytest.approx(8.0)
    assert raster.auswerten(z=2.0, phi=0.0)[1] == pytest.approx(
        np.zeros(3))


def test_union_doppelter_und_getrennter_volumina_zaehlt_voxel_nur_einmal(
        quader):
    identisch = vm.KoerperfestesVoxelmodell(
        [quader, quader], aufloesung=0.5)
    einzeln = vm.KoerperfestesVoxelmodell([quader], aufloesung=0.5)
    getrennt = (
        quader[0] + np.array((3.0, 0.0, 0.0)), quader[1])
    nebeneinander = vm.KoerperfestesVoxelmodell(
        [quader, getrennt], aufloesung=0.5)

    assert identisch.auswerten(-0.5, 0.0)[0] == einzeln.auswerten(
        -0.5, 0.0)[0]
    assert nebeneinander.auswerten(-0.5, 0.0)[0] == pytest.approx(12.0)


def test_geneigte_wasserhalbebene_wird_im_koerperfesten_raster_ausgewertet(
        quader):
    raster = vm.KoerperfestesVoxelmodell([quader], aufloesung=0.5)
    vor_pose = raster.zentren_lokal.copy()

    volumen, schwerpunkt = raster.auswerten(z=-0.5, phi=np.pi / 2)

    assert volumen == pytest.approx(6.0)
    assert schwerpunkt[2] == pytest.approx(-0.75)
    assert np.array_equal(raster.zentren_lokal, vor_pose)
    assert not raster.zentren_lokal.flags.writeable


def test_gebundene_kraftfunktion_bereitet_raster_nur_einmal_vor(
        quader, monkeypatch):
    original = vm.KoerperfestesVoxelmodell
    erstellungen = []

    class ModellZaehler(original):
        def __init__(self, *args, **kwargs):
            erstellungen.append(1)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(vm, "KoerperfestesVoxelmodell", ModellZaehler)
    koerper = SimpleNamespace(
        blatt_meshes=[quader], r_S=np.zeros(3), teile=[])
    funktion = auftrieb.baue_kraftfunktion(
        koerper, aufloesung=0.5, pfad="voxel_koerperfest")

    ergebnis_a = funktion((-0.5, 0.0, 0.0))
    ergebnis_b = funktion((0.0, 0.0, 0.0))

    assert len(erstellungen) == 1
    assert ergebnis_a.V_tauch == pytest.approx(6.0)
    assert ergebnis_b.V_tauch == pytest.approx(4.0)
    assert ergebnis_a.F_A.z == pytest.approx(1000.0 * auftrieb.G_NORM * 6.0)


def test_koerperfestes_und_globales_raster_stimmen_mit_exaktem_ponton_ueberein(
        quader):
    koerper = SimpleNamespace(
        blatt_meshes=[quader], r_S=np.zeros(3), teile=[])

    for lage, volumen in (((-0.5, 0.0, 0.0), 6.0),
                          ((0.0, 0.0, 0.0), 4.0)):
        koerperfest = auftrieb.kraftfunktion_berechne(
            koerper, lage, aufloesung=0.5, pfad="voxel_koerperfest")
        globales_raster = auftrieb.kraftfunktion_berechne(
            koerper, lage, aufloesung=0.5, pfad="voxel")
        exakt = auftrieb.kraftfunktion_berechne(
            koerper, lage, pfad="exakt")

        assert koerperfest.V_tauch == pytest.approx(volumen)
        assert globales_raster.V_tauch == pytest.approx(volumen)
        assert exakt.V_tauch == pytest.approx(volumen)


def test_tauchvolumen_ist_monoton_mit_zunehmendem_tiefgang(quader):
    raster = vm.KoerperfestesVoxelmodell([quader], aufloesung=0.25)
    tiefgaenge = (0.75, 0.5, 0.25, 0.0, -0.5, -1.0, -1.25)
    volumina = [raster.auswerten(z, 0.0)[0] for z in tiefgaenge]

    assert volumina == sorted(volumina)


def test_offenes_mesh_und_ungueltige_rasterparameter_werden_abgelehnt(quader):
    punkte, dreiecke = quader

    with pytest.raises(vm.VoxelmodellFehler, match="geschlossene"):
        vm.KoerperfestesVoxelmodell(
            [(punkte, dreiecke[:-2])], aufloesung=0.5)
    with pytest.raises(vm.VoxelmodellFehler, match="Auflösung"):
        vm.KoerperfestesVoxelmodell([quader], aufloesung=0.0)
