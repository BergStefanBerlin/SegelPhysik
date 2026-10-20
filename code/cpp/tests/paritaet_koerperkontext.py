import numpy as np
import pytest

from segelphysik.core.dynamik_6dof import Zustand6DOF
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.native_backend import NativeBackendFehler, NativeKoerperKontext
from werkzeuge.migration_vergleich import vergleiche


def snapshot_vergleichen(a, b):
    for name in ("masse", "traegheitstensor", "r_S", "zustand", "version",
                 "basis_pose", "gelenkzustaende"):
        vergleiche(getattr(a, name), getattr(b, name))
    assert len(a.blatt_meshes) == len(b.blatt_meshes)
    assert len(a.hydrodynamik_teile) == len(b.hydrodynamik_teile)
    for (p, f), (p2, f2) in zip(a.blatt_meshes, b.blatt_meshes):
        np.testing.assert_allclose(p2, p, rtol=0., atol=1e-12)
        np.testing.assert_array_equal(f2, f)
    for (rolle, name, p, f), (rolle2, name2, p2, f2) in zip(
            a.hydrodynamik_teile, b.hydrodynamik_teile):
        assert (rolle2, name2) == (rolle, name)
        np.testing.assert_allclose(p2, p, rtol=0., atol=1e-12)
        np.testing.assert_array_equal(f2, f)


@pytest.mark.parametrize("name", ["optimist", "folkeboot", "yacht1"])
def test_echte_modellsnapshots_und_mehrfache_ausgaben(name):
    from segelphysik.core.fabriken import baue_modellpaket
    from segelphysik.core.konfig_lader import lade_konfig
    from werkzeuge.migration_inventar import ROOT

    k, _ = baue_modellpaket(lade_konfig(ROOT / "konfigurationen"), ROOT / "code" / "modelle" / name)
    kontext = NativeKoerperKontext(k)
    original = k.snapshot()
    for _ in range(3):
        snapshot_vergleichen(original, kontext.snapshot(k))


def test_punktmassen_bleiben_ohne_verdrangung_und_rollen_werden_vererbt():
    blatt = Koerper(form=build_box(1., 2., 3.), masse=2., zustand=None)
    punkt = Koerper(punktmasse=True, masse=70., verdrangend=False, zustand=None)
    gruppe = Koerper(
        teile=[(blatt, (np.eye(3), np.array([1., 2., 3.]))),
               (punkt, (np.eye(3), np.array([-1., 0., 2.])))],
        rolle_default="rumpf", zustand=None)
    wurzel = Koerper(teile=[(gruppe, (np.eye(3), np.array([2., 0., 0.])))])
    snapshot_vergleichen(wurzel.snapshot(), NativeKoerperKontext(wurzel).snapshot(wurzel))
    assert len(wurzel.snapshot().blatt_meshes) == 1
    snapshot_vergleichen(punkt.snapshot(), NativeKoerperKontext(punkt).snapshot(punkt))


@pytest.mark.parametrize("mutation", [
    "zustand", "pose", "basis_pose", "masse", "traegheit", "identitaet"])
def test_geaenderte_koerper_werden_explizit_invalidiert(mutation):
    k = Koerper(form=build_box(1., 2., 3.), masse=2.)
    kontext = NativeKoerperKontext(k)
    if mutation == "zustand":
        k.zustand = Zustand6DOF(position=(1., 2., 3.))
    elif mutation == "pose":
        k.setze_pose((1., 2., 3.))
    elif mutation == "basis_pose":
        from segelphysik.core.frames import Pose

        k.basis_pose = Pose(
            "eltern", "kind", (1., 2., 3.), (1., 0., 0., 0.))
    elif mutation == "masse":
        k.masse += 1.
    elif mutation == "traegheit":
        k.traegheitstensor = k.traegheitstensor * 2.
    else:
        k = Koerper(form=build_box(1., 2., 3.), masse=2.)
    with pytest.raises(NativeBackendFehler, match="veraltet"):
        kontext.snapshot(k)
    snapshot_vergleichen(k.snapshot(), NativeKoerperKontext(k).snapshot(k))


def test_gelenkwechsel_behaelt_den_tatsaechlichen_referenzvertrag():
    from types import SimpleNamespace

    definition = SimpleNamespace(
        winkel_rad=.3, achse_eltern=(1., 0., 0.), eltern_id="wurzel")
    blatt = Koerper(
        form=build_box(1., 2., 3.), masse=2., knoten_id="gelenk",
        gelenkdefinition=definition, zustand=None)
    k = Koerper(teile=[blatt])
    kontext = NativeKoerperKontext(k)
    snapshot_vergleichen(k.snapshot(), kontext.snapshot(k))
    k.gelenkwinkel_setzen("gelenk", -.7)
    with pytest.raises(NativeBackendFehler, match="veraltet"):
        kontext.snapshot(k)
    neu = NativeKoerperKontext(k).snapshot(k)
    snapshot_vergleichen(k.snapshot(), neu)
    assert neu.gelenkzustaende[0].winkel_rad == -.7


@pytest.mark.parametrize("mutation", ["punkt", "dreieck", "rolle", "translation", "kindversion"])
def test_unversionierte_mesh_und_unterbaum_aenderungen_sind_keine_stillen_cachetreffer(mutation):
    blatt = Koerper(form=build_box(1., 2., 3.), masse=2., zustand=None)
    k = Koerper(teile=[blatt])
    kontext = NativeKoerperKontext(k)
    if mutation == "punkt":
        blatt.punkte[0, 0] += .01
    elif mutation == "dreieck":
        blatt.dreiecke[0] = blatt.dreiecke[0, ::-1]
    elif mutation == "rolle":
        blatt.rolle = "ruder"
    elif mutation == "translation":
        k.teile[0][1][1][0] += .01
    else:
        blatt.zustand = Zustand6DOF()
    with pytest.raises(NativeBackendFehler, match="veraltet"):
        kontext.snapshot(k)
    snapshot_vergleichen(k.snapshot(), NativeKoerperKontext(k).snapshot(k))


def test_snapshotausgaben_teilen_keinen_speicher_mit_der_internen_vorlage():
    k = Koerper(form=build_box(1., 2., 3.), masse=2.)
    kontext = NativeKoerperKontext(k)
    erster = kontext.snapshot(k)
    p, f = erster.blatt_meshes[0]
    p.setflags(write=True)
    f.setflags(write=True)
    p[:] = 999.
    f[:] = 0
    snapshot_vergleichen(k.snapshot(), kontext.snapshot(k))
