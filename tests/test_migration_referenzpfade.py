"""Direkte Referenzfaelle fuer zuvor nicht aufgerufene Inventarfunktionen."""
from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik import wasser_schnitt
from segelphysik.core import massen
from segelphysik.core.auftrieb import _y_intervalle_saeule
from segelphysik.core.bewegung import body_pose, koerper_pose
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box
from segelphysik.render.vista import (
    IsoSurfaceWater, PyVistaRenderer, _bilinear_upsample,
    _surface_polydata, _unit_circle, _unit_square,
)


@pytest.mark.parametrize("oberhalb", [False, True])
def test_polygonbeschnitt_und_fan_bleiben_im_gewaehlten_halbraum(oberhalb):
    polygon = np.array([[-1., -1., -1.], [1., -1., 1.],
                        [1., 1., 1.], [-1., 1., -1.]])
    punkte = wasser_schnitt._clip_polygon(polygon, 0., oberhalb)
    assert len(punkte) == 4
    assert all(p[2] >= 0 if oberhalb else p[2] <= 0 for p in punkte)
    dreiecke = wasser_schnitt._fan_triangulieren(punkte)
    assert len(dreiecke) == 2
    flaeche = sum(np.linalg.norm(np.cross(b - a, c - a)) / 2
                  for a, b, c in dreiecke)
    assert flaeche == pytest.approx(2 * np.sqrt(2), abs=1e-12)
    assert wasser_schnitt._clip_polygon([], 0., oberhalb) == []
    assert wasser_schnitt._fan_triangulieren([]) == []


def test_punkt_in_ring_innen_aussen_und_konkaver_ring():
    ring = np.array([[0., 0., 0.], [2., 0., 0.], [2., 2., 0.],
                     [1., 1., 0.], [0., 2., 0.]])
    assert wasser_schnitt._punkt_in_ring((.5, .5), ring)
    assert not wasser_schnitt._punkt_in_ring((3., .5), ring)
    assert not wasser_schnitt._punkt_in_ring((1., 1.8), ring)


def test_scalar_schnittpraedikate_gegen_einfache_geometrie():
    a = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    normale = massen._kreuzprodukt_3d(a[1] - a[0], a[2] - a[0])
    np.testing.assert_array_equal(normale, (0., 0., 1.))
    assert massen._koplanare_dreiecke_schneiden(a, a + (.1, .1, 0.), normale, 1e-12)
    assert not massen._koplanare_dreiecke_schneiden(a, a + (3., 0., 0.), normale, 1e-12)
    assert massen._segment_dreieck_schneiden(
        np.array([.2, .2, -1.]), np.array([.2, .2, 1.]), a, 1e-12)
    assert not massen._segment_dreieck_schneiden(
        np.array([2., 2., -1.]), np.array([2., 2., 1.]), a, 1e-12)


def test_meshflaeche_quader_und_leere_flaechen():
    punkte, dreiecke = build_box(2., 3., 4.)
    assert massen.mesh_flaeche(punkte, dreiecke) == pytest.approx(52., abs=1e-12)
    assert massen.mesh_flaeche(punkte, np.empty((0, 3), dtype=np.int64)) == 0.


def test_relative_pose_und_kinematikalias_erhalten_frames():
    punkte, dreiecke = build_box(1., 1., 1.)
    k = Koerper(form=(punkte, dreiecke), dichte=500.)
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    k.setze_rel_pose((rotation, (1., 2., 3.)))
    np.testing.assert_array_equal(k._rel_R, rotation)
    np.testing.assert_array_equal(k._rel_t, (1., 2., 3.))
    for t in (0., .5, 10.):
        r, x = koerper_pose(t, achse=(1., 0., 0.), phase=.1)
        rb, xb = body_pose(t, axis=(1., 0., 0.), phase=.1)
        np.testing.assert_array_equal(r, rb)
        np.testing.assert_array_equal(x, xb)


@pytest.mark.parametrize("n", [3, 12, 40])
def test_wasserflaechen_interpolation_normale_und_spitzenbehandlung(n):
    import pyvista as pv

    x, y = np.meshgrid(np.linspace(-1., 1., n), np.linspace(-1., 1., n))
    z = x + 2 * y
    netz = _surface_polydata(pv, x, y, z)
    assert netz.n_points == n * n
    assert netz.n_cells == 2 * (n - 1) ** 2
    np.testing.assert_array_equal(netz.points[:, 2], z.ravel())
    interpoliert = _bilinear_upsample(z, 2)
    np.testing.assert_allclose(interpoliert[::2, ::2], z, rtol=0, atol=1e-15)
    assert interpoliert.shape == (2 * n - 1, 2 * n - 1)
    assert _bilinear_upsample(z, 1) is z
    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    renderer.dx = .1
    renderer.smooth_passes = 2
    defekt = z.copy()
    defekt[n // 2, n // 2] = np.nan
    glatt = renderer._smooth_surface(defekt)
    assert np.isfinite(glatt).all()
    assert glatt.shape == z.shape
    np.testing.assert_array_equal(
        renderer._smooth_surface(np.full((n, n), np.nan)), np.zeros((n, n)))
    kreis = _unit_circle(n)
    np.testing.assert_allclose(np.linalg.norm(kreis, axis=1), 1., rtol=0, atol=1e-15)
    assert _unit_square().shape == (5, 2)


def test_vorhandene_isoflaeche_und_bestehender_zweiframecache():
    import pyvista as pv

    wasser = IsoSurfaceWater(2., 2., 1., .2, cell=.2)
    x, y, z = np.meshgrid(
        np.arange(-.9, 1., .2), np.arange(-.9, 1., .2),
        np.arange(-.9, 0., .2), indexing="ij")
    punkte = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    wasser.splat(punkte)
    mesh = wasser.mesh(pv)
    assert mesh.n_points > 0
    assert np.isfinite(mesh.points).all()
    assert wasser._norm_eff is not None
    wasser.splat(punkte)
    assert not wasser._skip
    wasser.mesh(pv)
    wasser.splat(punkte)
    assert wasser._skip
    assert wasser.mesh(pv) is wasser._cache


@pytest.mark.parametrize("methode,args", [
    ("_body_half_height", (SimpleNamespace(half=(1., 1., 1.)),)),
    ("_update_ring", (0, SimpleNamespace())),
    ("_clamp_to_bodies", (np.zeros((3, 3)),)),
    ("update", ()),
])
def test_entfernter_legacy_body_typ_ist_keine_ausfuehrbare_referenz(methode, args):
    """Den bekannten Importfehler offen dokumentieren, keine Ersatzphysik erfinden."""
    from importlib.util import find_spec

    assert find_spec("segelphysik.core.bodies") is None
    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    with pytest.raises(ModuleNotFoundError, match="segelphysik.core.bodies"):
        getattr(renderer, methode)(*args)


def test_polydaten_hilfsvertrag_und_rueckextraktion():
    import pyvista as pv
    from segelphysik.grafik_bruecke import _gesichter, _polydaten

    punkte, dreiecke = build_box(1., 1., 1.)
    daten = _polydaten(pv, punkte, dreiecke)
    np.testing.assert_array_equal(daten.points, punkte)
    np.testing.assert_array_equal(_gesichter(daten), dreiecke)


def test_alter_skalarer_voxel_saeulenpfad_bleibt_separat_nachgewiesen():
    punkte, dreiecke = build_box(2., 2., 2.)
    np.testing.assert_allclose(
        _y_intervalle_saeule(punkte, dreiecke, .1, .2),
        [(-1., 1.)], rtol=0, atol=1e-12)
    assert _y_intervalle_saeule(punkte, dreiecke, 10., 0.) == []


def test_legacy_kraftpfeile_verwenden_bestehende_laengen_farben_und_schwellen():
    import pyvista as pv

    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    renderer.pv = pv
    renderer.app = SimpleNamespace(world=SimpleNamespace(environment=SimpleNamespace(g=10.)))
    renderer._arrow_f = renderer._arrow_v = None
    meshes = []
    entfernt = []

    def hinzufuegen(mesh, **kwargs):
        meshes.append((mesh, kwargs))
        return object()

    renderer._plotter = SimpleNamespace(add_mesh=hinzufuegen, remove_actor=entfernt.append)
    koerper = SimpleNamespace(
        mass=1., force=(10., 0., 0.), vel=(0., 1., 0.), pos=(0., 0., 0.))
    renderer._refresh_arrows(koerper)
    assert len(meshes) == 2
    assert meshes[0][1]["color"] == "#e67e22"
    assert meshes[1][1]["color"] == "#27ae60"
    assert np.isfinite(meshes[0][0].points).all()
    koerper.force = koerper.vel = (0., 0., 0.)
    renderer._refresh_arrows(koerper)
    assert len(entfernt) == 2 and len(meshes) == 2
    assert renderer._arrow_f is None and renderer._arrow_v is None


def test_bildschirm_zu_wasser_ohne_plotter_und_mit_echter_vtk_kamera():
    import pyvista as pv

    renderer = PyVistaRenderer.__new__(PyVistaRenderer)
    renderer._plotter = None
    assert renderer.screen_to_water(10., 10.) is None
    plotter = pv.Plotter(off_screen=True, window_size=(640, 480))
    try:
        plotter.camera_position = [(0., 0., 10.), (0., 0., 0.), (0., 1., 0.)]
        plotter.render()
        renderer._plotter = plotter
        renderer.lx = renderer.ly = 10.
        punkt = renderer.screen_to_water(320., 240.)
        assert punkt is not None
        np.testing.assert_allclose(punkt, (0., 0.), rtol=0, atol=1e-9)
    finally:
        plotter.close()


def test_synchrone_gui_workeraufgabe_entspricht_dem_produktiven_batch():
    from segelphysik.core import echtzeit_prozess
    from segelphysik.core.dynamik_6dof import Zustand6DOF
    from segelphysik.core.konfig_lader import lade_physik
    from segelphysik.gui.hauptfenster import _EchtzeitAufgabe
    from werkzeuge.migration_baseline import kraftdaten
    from werkzeuge.migration_inventar import ROOT
    from werkzeuge.migration_vergleich import vergleiche

    koerper = Koerper(form=build_box(1., 1., 1.), dichte=500.)
    physik = lade_physik(ROOT / "konfigurationen")
    start = Zustand6DOF(position=(0., 0., -.1))
    echtzeit_prozess.initialisieren(koerper.snapshot(), 1000., physik)
    referenz = echtzeit_prozess.schritte_berechnen(start, 10)
    assert referenz[2] is None
    echtzeit_prozess.initialisieren(koerper.snapshot(), 1000., physik)
    antworten = []
    aufgabe = _EchtzeitAufgabe(
        7, 9, "quader", start, echtzeit_prozess._kraftfunktion, koerper,
        physik, physik.dt_s, 10,
        SimpleNamespace(abgeschlossen=SimpleNamespace(
            emit=lambda *args: antworten.append(args))))
    aufgabe.run()
    assert len(antworten) == 1
    generation, sequenz, name, ende, kraft, fehler, dauer = antworten[0]
    assert (generation, sequenz, name, fehler) == (7, 9, "quader", None)
    assert dauer >= 0.
    vergleiche(referenz[0], ende)
    vergleiche(kraftdaten(referenz[1]), kraftdaten(kraft))


def test_segelwinkel_bestandsvertrag_ohne_eindeutiges_gelenk_und_mit_einem():
    from segelphysik.gui.baum import ART_SUMMEN, Knoten
    from segelphysik.gui.hauptfenster import HauptFenster

    boot = Knoten("boot", ART_SUMMEN, "wuerfel")
    welt = SimpleNamespace(kinder=[boot])
    fenster = SimpleNamespace(baum=SimpleNamespace(_welt=welt))
    assert HauptFenster._segelwinkel_ermitteln(fenster, "boot") is None
    segel = SimpleNamespace(
        rolle="segel", gelenkdefinition=object(), gelenkwinkel_rad=.2, teile=())
    boot.teile = [(segel, None)]
    assert HauptFenster._segelwinkel_ermitteln(fenster, "boot") == .2
    boot.teile.append((segel, None))
    assert HauptFenster._segelwinkel_ermitteln(fenster, "boot") is None
    assert HauptFenster._segelwinkel_ermitteln(fenster, "unbekannt") is None


def test_echte_actorgruppen_und_schwerpunkt_ohne_neue_optik():
    import pyvista as pv
    from segelphysik.grafik_bruecke import GrafikBruecke
    from werkzeuge.migration_szenarien import aktoren_snapshot

    bruecke = GrafikBruecke()
    plotter = pv.Plotter(off_screen=True)
    bruecke._plotter = plotter
    bruecke._vg_unmoeglich = True
    try:
        koerper = Koerper(
            form=build_box(1., 1., 1.), dichte=500.,
            farbe="#112233", farbe_unter_wasser="#445566")
        bruecke.koerper_objekt_setzen("quader", koerper)
        bruecke._overlay_schwerpunkt_setzen("quader", np.array((.1, .2, .3)))
        snapshot = aktoren_snapshot(bruecke)
        assert "szene:koerper_quader_g0_oben" in snapshot
        assert "szene:koerper_quader_g0_unten" in snapshot
        assert pv.Color(snapshot["szene:koerper_quader_g0_oben"]["farbe"]).hex_rgb == "#112233"
        assert pv.Color(snapshot["szene:koerper_quader_g0_unten"]["farbe"]).hex_rgb == "#445566"
        bruecke._actors_aktualisieren("quader", koerper.punkte)
        # Actoranlage (PyVista-Normalen) und bestehender Mapper-Updatevertrag sind getrennte Pfade.
        snapshot = aktoren_snapshot(bruecke)
        bruecke._actors_aktualisieren("quader", koerper.punkte)
        assert aktoren_snapshot(bruecke) == snapshot
    finally:
        plotter.close()
