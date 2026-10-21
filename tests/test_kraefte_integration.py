from dataclasses import replace
import math
import pickle

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from segelphysik.core.auftrieb import Auftriebsergebnis
from segelphysik.core.dynamik_6dof import Zustand6DOF, schritt
from segelphysik.core.frames import Pose
from segelphysik.core.kraftmodell import (
    Kraftbeitrag, Kraftmodell, Wrench, aggregiere_kraftbeitraege,
)
from segelphysik.core.kraefte_anzeige import KraefteAnzeigeAdapter
from segelphysik.core.hydrodynamik import HydrodynamikModell, HydrodynamikTeil
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.native_backend import (
    beitrag_nach_python, beitrag_vorbereiten, ergebnis_nach_python,
    ergebnis_vorbereiten,
)
from segelphysik.core.overlays import LAYER_KRAEFTE, LAYER_MOMENTE
from segelphysik.grafik_bruecke import GrafikBruecke

pytestmark = [pytest.mark.gui, pytest.mark.integration]


@pytest.fixture(params=("python", "cpp"), autouse=True)
def backend(request, monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", request.param)


def _modell(**kwargs):
    return Kraftmodell(lambda *_a, **_kw: Auftriebsergebnis(
        .01, (0, .2, 0), (0, 0, 10), (2, 0, 0)),
        masse=1, g=10, **kwargs)


def _snapshot(erg=None, generation=1, sequenz=0):
    if erg is None:
        erg = _modell()(((0, 0, 0), (1, 0, 0, 0)))
    return KraefteAnzeigeAdapter().aus_ergebnis(
        erg, koerper_id="boot", generation=generation, sequenz=sequenz,
        zeit_s=1.25, masse_kg=1, g_m_s2=10)


def test_normalisierung_und_native_rundreise_erhalten_herkunft():
    b = Kraftbeitrag("fremdkraft", Wrench(
        "simulationsframe", (1, 2, 3), (0, 0, 10), (1, 0, 0)),
        "modell:knoten-fest", [1, 2, 3])
    _, beitraege = aggregiere_kraftbeitraege((b,), (0, 0, 0))
    assert beitraege[0].quell_id == b.quell_id
    assert beitraege[0].originalangriff_m == (1, 2, 3)
    assert beitraege[0].wrench.moment_Nm == (21, -10, 0)
    assert beitrag_nach_python(beitrag_vorbereiten(beitraege[0])) == beitraege[0]


def test_fremdangriff_bleibt_nach_aggregation_und_added_mass_erhalten():
    modell = _modell(added_mass_diagonal=(2,) * 6)
    modell.fremdkraft_setzen(((0, 0, 10), (1, 0, 0)))
    pose = ((5, 6, 7), (1, 0, 0, 0))
    erg = modell(pose)
    quelle = next(b for b in erg.beitraege if b.name == "fremdkraft")
    assert quelle.originalangriff_m == (6, 6, 7)
    assert quelle.wrench.bezugspunkt_m == (5, 6, 7)
    assert erg.kraftpose.translation_m == (5, 6, 7)
    korrigiert = erg.mit_beschleunigung((0,) * 6)
    assert korrigiert.kraftpose is erg.kraftpose
    assert next(b for b in korrigiert.beitraege if b.name == "added_mass").quell_id
    assert _snapshot(erg).vollstaendigkeit == "teilsumme"
    assert _snapshot(korrigiert).vollstaendigkeit == "vollstaendig"
    _, rundreise = ergebnis_nach_python(ergebnis_vorbereiten(
        Zustand6DOF(position=(9, 9, 9)), korrigiert))
    assert rundreise.kraftpose == erg.kraftpose
    assert rundreise.beitraege == korrigiert.beitraege
    assert pickle.loads(pickle.dumps(rundreise)).kraftpose == erg.kraftpose


def test_quellinstanzen_bei_gleichen_namen_bleiben_eindeutig_und_null_explizit():
    p, f = build_box(1, 1, 1)
    teile = (
        HydrodynamikTeil("gleich", "rumpf", p, f, "knoten:a"),
        HydrodynamikTeil("gleich", "rumpf", p + (2, 0, 0), f, "knoten:b"),
    )
    modell = _modell(hydrodynamik=HydrodynamikModell(teile))
    erg = modell(((0, 0, 10), (1, 0, 0, 0)), v=(0, 0, 0))
    hydro = [b for b in erg.beitraege if b.name == "hydrodynamik_rumpf"]
    assert {b.quell_id for b in hydro} == {"knoten:a", "knoten:b"}
    assert all(b.wrench.kraft_N == (0, 0, 0) for b in hydro)
    assert _snapshot(erg).vollstaendigkeit == "vollstaendig"
    with pytest.raises(ValueError, match="nicht eindeutig"):
        HydrodynamikModell((teile[0], teile[0]))


def test_dynamik_snapshot_hat_kraftpose_nicht_endpose():
    anfang = Zustand6DOF(position=(1, 2, -3), geschwindigkeit_koerper=(1, 0, 0))
    ende, erg = schritt(anfang, _modell(), 1, np.eye(3), .1, 10)
    assert ende.position != anfang.position
    snapshot = _snapshot(erg)
    assert snapshot.kraftpose.translation_m == anfang.position
    assert snapshot.kraftpose.rotation_quaternion_wxyz == anfang.quaternion
    assert snapshot.rechenbilanz == snapshot.bilanz.wrench


@pytest.mark.parametrize("modellname", (None, "folkeboot"))
def test_anzeigebilanz_entspricht_tatsaechlichem_implizitem_integratorschritt(modellname):
    from segelphysik.core.dynamik_6dof import quaternion_matrix
    added = np.array((2, 3, 4, 1, 2, 3), dtype=float)
    linear = np.array((3, 4, 5, 6, 7, 8), dtype=float)
    quadratisch = np.array((1, 2, 1, 2, 1, 2), dtype=float)
    parameter = dict(
        added_mass_diagonal=added, linear_widerstand=linear,
        quadratischer_widerstand=quadratisch,
        fluidgeschwindigkeit=(.1, -.2, 0),
        fluidwinkelgeschwindigkeit=(0, .1, 0))
    masse, inertia, g = 1, np.diag((4., 5., 6.)), 10
    if modellname is None:
        modell = _modell(**parameter)
    else:
        from segelphysik.core.auftrieb import baue_kraftfunktion_6dof
        from segelphysik.core.kraftmodell import KraftmodellMitHydroCache
        from werkzeuge.migration_szenarien import koerper_laden
        konfig, physik, koerper = koerper_laden(modellname)
        masse, inertia, g = koerper.masse, koerper.traegheitstensor, physik.g_m_pro_s2
        hydro = HydrodynamikModell.aus_koerper(
            koerper, rho_kg_m3=konfig.wasser_dichte(),
            fluidgeschwindigkeit=parameter["fluidgeschwindigkeit"],
            fluidwinkelgeschwindigkeit=parameter["fluidwinkelgeschwindigkeit"])
        assert hydro is not None
        modell = KraftmodellMitHydroCache(Kraftmodell(baue_kraftfunktion_6dof(
            koerper, rho_w=konfig.wasser_dichte(), g=g, pfad="exakt_union"),
            masse=masse, g=g, hydrodynamik=hydro, **parameter))
    modell.fremdkraft_setzen(((5, -3, 2), (1, .2, -.1)))
    anfang = Zustand6DOF(
        quaternion=(.9238795325112867, 0, 0, .3826834323650898),
        geschwindigkeit_koerper=(.2, .1, -.3),
        winkelgeschwindigkeit_koerper=(.1, -.2, .3))
    dt = .03
    ende, erg = schritt(anfang, modell, masse, inertia, dt, g)
    snapshot = KraefteAnzeigeAdapter().aus_ergebnis(
        erg, koerper_id=modellname or "boot", generation=1, sequenz=1,
        zeit_s=0, masse_kg=masse, g_m_s2=g)
    rotation = quaternion_matrix(anfang.quaternion)
    v, omega = (np.asarray(anfang.geschwindigkeit_koerper),
                np.asarray(anfang.winkelgeschwindigkeit_koerper))
    a = (np.asarray(ende.geschwindigkeit_koerper) - v) / dt
    alpha = (np.asarray(ende.winkelgeschwindigkeit_koerper) - omega) / dt
    relativ = np.r_[rotation @ v - parameter["fluidgeschwindigkeit"],
                    rotation @ omega - parameter["fluidwinkelgeschwindigkeit"]]
    rate = linear + quadratisch * abs(relativ)
    # Added Mass ist bereits als Diagnosekraft ausgewiesen, die implizite
    # Daempfung und koerperfesten Coriolisterme muessen noch umgerechnet werden.
    kraft = (masse * a + np.cross(omega, (masse + added[:3]) * v)
             + dt * rotation.T @ np.diag(rate[:3]) @ rotation @ a)
    moment = (inertia @ alpha
              + np.cross(omega, (inertia + np.diag(added[3:])) @ omega)
              + dt * rotation.T @ np.diag(rate[3:]) @ rotation @ alpha)
    assert rotation.T @ snapshot.bilanz.wrench.kraft_N == pytest.approx(
        kraft, abs=1e-9, rel=1e-9)
    assert rotation.T @ snapshot.bilanz.wrench.moment_Nm == pytest.approx(
        moment, abs=1e-9, rel=1e-9)
    assert snapshot.vollstaendigkeit == "vollstaendig"
    assert any(b.name == "added_mass" for b in snapshot.beitraege)
    if modellname is not None:
        assert any(b.name.startswith("hydrodynamik_") for b in snapshot.beitraege)
        assert any("Modellueberlagerung" in h for h in snapshot.modellhinweise)


@pytest.mark.parametrize("mit_widerstand", (False, True))
@pytest.mark.parametrize("tempo", (0., .2))
def test_modellueberlagerung_bleibt_auch_bei_nullkraeften_sichtbar(
        mit_widerstand, tempo):
    from segelphysik.gui.kraefte_werte import KraefteWerteModell
    QApplication.instance() or QApplication([])
    punkte, faces = build_box(1, 1, 1)
    modell = _modell(
        linear_widerstand=(1.,) * 6 if mit_widerstand else (0.,) * 6,
        hydrodynamik=HydrodynamikModell((
            HydrodynamikTeil("kiel", "kiel", punkte, faces, "kiel:1"),)))
    ergebnis = modell(((0, 0, 0), (1, 0, 0, 0)), v=(tempo, 0, 0))
    snapshot = _snapshot(ergebnis)
    assert bool(snapshot.modellhinweise) == mit_widerstand
    werte = KraefteWerteModell()
    werte.snapshots_setzen((snapshot,))
    kopf = werte.kopftext(snapshot)
    assert ("Modellueberlagerung" in kopf) == mit_widerstand
    if mit_widerstand:
        assert "Linearer Widerstand (6D)" in kopf
        assert "ungeklaert" in kopf
        assert "Modellueberlagerung" in werte.detailtext(("boot", "widerstand"))
    assert snapshot.bilanz.wrench.kraft_N == pytest.approx(
        ergebnis.F_gesamt.as_array(), abs=1e-9)
    assert snapshot.bilanz.wrench.moment_Nm == pytest.approx(
        ergebnis.M_gesamt.as_array(), abs=1e-9)


def test_nachtraeglich_zugeordnete_modellknoten_bleiben_stabile_quellen():
    from segelphysik.core.fabriken import baue_quader
    koerper = baue_quader(dx=1, dy=1, dz=1)
    andere_instanz = baue_quader(dx=1, dy=1, dz=1)
    assert koerper.quell_id != andere_instanz.quell_id
    koerper.knoten_id = andere_instanz.knoten_id = "modell:blatt"
    assert koerper.quell_id == andere_instanz.quell_id == "knoten:modell:blatt"
    assert koerper.snapshot().blatt_quell_ids == ("knoten:modell:blatt",)


def test_native_batch_transportiert_letzte_eingangspose_ohne_neuauswertung():
    from segelphysik.core import echtzeit_prozess
    from werkzeuge.migration_szenarien import koerper_laden
    konfig, physik, snapshot = koerper_laden("optimist")
    echtzeit_prozess.initialisieren(snapshot, konfig.wasser_dichte(), physik)
    anfang = Zustand6DOF(position=(0, 0, -.05), geschwindigkeit_koerper=(.2, 0, 0))
    vorletzter, _, fehler, _ = echtzeit_prozess.schritte_berechnen(anfang, 2)
    assert fehler is None
    ende, erg, fehler, _ = echtzeit_prozess.schritte_berechnen(anfang, 3)
    assert fehler is None
    assert erg.kraftpose.translation_m == pytest.approx(vorletzter.position)
    assert ende.position != erg.kraftpose.translation_m
    assert all(b.quell_id for b in erg.beitraege)


@pytest.fixture
def bruecke():
    import pyvista as pv
    plotter = pv.Plotter(off_screen=True, window_size=(800, 600))
    plotter.camera_position = [(0, -5, 2), (0, 0, 0), (0, 0, 1)]
    plotter.enable_parallel_projection()
    plotter.camera.parallel_scale = 1
    b = GrafikBruecke()
    b._plotter = plotter
    b._koerper["boot"] = {
        "aktiv": True, "position": np.zeros(3), "overlay_skala": (1, .05)}
    b._layer.setzen(LAYER_KRAEFTE, True)
    b._layer.setzen(LAYER_MOMENTE, True)
    yield b
    plotter.close()


def test_echter_vtk_renderer_erhaelt_wrench_und_stabile_actors(bruecke):
    snapshot = _snapshot()
    assert bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke._kraefte_actors("boot")
    store = bruecke._koerper["boot"]["kraefte_actors"]
    assert "kraefte_('boot', 'hydrostatik')_F" in store
    assert any(n.endswith("_M") for n in store)
    vorher = dict(store)
    bruecke._kraefte_actors("boot")
    assert store.keys() == vorher.keys()
    assert all(store[n] is vorher[n] for n in store)
    assert bruecke._kraefte_daten["boot"] is snapshot
    assert not bruecke.kraefte_snapshot_setzen(replace(snapshot, generation=0))
    assert bruecke._kraefte_daten["boot"] is snapshot
    bruecke.kraefte_daten_entfernen("boot")
    assert not store and "boot" not in bruecke._kraftzeichner().skalen
    assert not bruecke._kraftzeichner().labels


def test_kompatibler_dateneingang_hat_keinen_zweiten_weltmassstab(bruecke):
    ergebnis = _modell()(((0, 0, 0), (1, 0, 0, 0)))
    bruecke.kraefte_daten_setzen("boot", ergebnis, 1, 10)
    bruecke.render()
    skalen = dict(bruecke._kraftzeichner().skalen)
    punkte = {
        name: actor.mapper.dataset.points.copy()
        for name, actor in bruecke._koerper["boot"]["kraefte_actors"].items()
    }
    for alt_skala in (.0001, 100.):
        bruecke.kraefte_daten_setzen("boot", ergebnis, 1, 10, alt_skala)
        bruecke.render()
        assert bruecke._kraftzeichner().skalen == skalen
        aktuell = bruecke._koerper["boot"]["kraefte_actors"]
        assert aktuell.keys() == punkte.keys()
        for name, original in punkte.items():
            assert aktuell[name].mapper.dataset.points == pytest.approx(original)


def test_echtes_vtk_picking_liefert_alle_ueberlagerten_kandidaten(bruecke):
    snapshot = _snapshot()
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke._kraefte_actors("boot")
    zeichner = bruecke._kraftzeichner()
    p = np.array([.1, .2, .3])
    zeichner.picklinien = {
        ("boot", "a"): (np.array([p, p + (.1, 0, 0)]),),
        ("boot", "b"): (np.array([p, p + (.1, 0, 0)]),)}
    renderer = bruecke._plotter.renderer
    renderer.SetWorldPoint(*p, 1)
    renderer.WorldToDisplay()
    x, y, _ = renderer.GetDisplayPoint()
    assert zeichner.kandidaten((x, y)) == (("boot", "a"), ("boot", "b"))
    assert zeichner.kandidaten((x, y + 7)) == ()


@pytest.mark.parametrize("parallel", (True, False))
@pytest.mark.parametrize("dpi", (1., 1.5, 2.))
def test_echte_projektion_haelt_kopf_und_schaft_in_logischen_pixeln(
        bruecke, monkeypatch, parallel, dpi):
    plotter = bruecke._plotter
    monkeypatch.setattr(type(plotter), "devicePixelRatioF",
                        lambda self: dpi, raising=False)
    plotter.camera_position = [(0, -5, 0), (0, 0, 0), (0, 0, 1)]
    plotter.camera.parallel_projection = parallel
    pfeile = []
    zeichnen = bruecke._kraftpfeil_zeichnen

    def aufzeichnen(store, name, stil, pfeil):
        pfeile.append(pfeil)
        zeichnen(store, name, stil, pfeil)

    monkeypatch.setattr(bruecke, "_kraftpfeil_zeichnen", aufzeichnen)
    bruecke.kraefte_snapshot_setzen(_snapshot())
    bruecke._kraefte_actors("boot")
    assert pfeile
    for pfeil in pfeile:
        pixel = bruecke._kraftzeichner().kamera().welt_pro_pixel(pfeil["start"])
        assert 2 * pfeil["schaft_radius"] / pixel == pytest.approx(3)
        projiziert = []
        for p in (pfeil["schaft_ende"], pfeil["spitze"]):
            plotter.renderer.SetWorldPoint(*p, 1)
            plotter.renderer.WorldToDisplay()
            projiziert.append(np.array(plotter.renderer.GetDisplayPoint()[:2]) / dpi)
        assert abs(np.linalg.norm(projiziert[1] - projiziert[0]) - 10) <= 1


@pytest.mark.parametrize("laenge", (.02, .5, 5.))
@pytest.mark.parametrize("richtung", ((1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 2, -3)))
def test_tatsaechliches_solidnetz_erhaelt_kopf_und_schaftmasse(
        bruecke, laenge, richtung):
    from segelphysik.core import kraefte_bild as kb
    richtung = np.array(richtung, dtype=float)
    richtung /= np.linalg.norm(richtung)
    start = np.array((1., -2., 3.))
    pfeil = kb.pfeil_fest(start, laenge * richtung, .01, .025, .05)
    stil = bruecke._stil.pfeil("f_g", 1)
    store = bruecke._koerper["boot"].setdefault("kraefte_actors", {})
    bruecke._kraftpfeil_zeichnen(store, "massprobe", stil, pfeil)
    netz = store["massprobe"].mapper.dataset
    punkte = np.asarray(netz.points) - start
    axial = punkte @ richtung
    radien = np.linalg.norm(punkte - axial[:, None] * richtung, axis=1)
    assert axial.min() == pytest.approx(0, abs=1e-7)
    assert axial.max() == pytest.approx(laenge, abs=1e-7)
    assert radien[np.isclose(axial, 0)].max() == pytest.approx(.005, rel=1e-5)
    kopfbasis = laenge - pfeil["kopf_laenge"]
    kopfradien = radien[np.isclose(axial, kopfbasis)]
    assert len(kopfradien) > 0
    assert np.any(np.isclose(kopfradien, pfeil["kopf_radius"], rtol=1e-5))
    assert kopfradien.max() == pytest.approx(
        max(pfeil["kopf_radius"], pfeil["schaft_radius"]), rel=1e-5)
    assert np.linalg.norm(netz.point_data["Normals"], axis=1) == pytest.approx(
        np.ones(netz.n_points), abs=1e-6)
    assert netz.GetPointData().GetNormals() is not None
    ursprung = netz.points.copy()
    bruecke._kraftpfeil_netz(kb.pfeil_fest(
        (2, 3, 4), (1, 0, 0), .02, .05, .1))
    np.testing.assert_array_equal(netz.points, ursprung)


def test_skalen_log_modus_manuelle_referenzen_und_neueinpassen(bruecke, tmp_path):
    from segelphysik.core.einstellungen import Einstellungen
    from segelphysik.core.pfeilstil import Stil
    ein = Einstellungen(str(tmp_path / "settings.json"))
    ein.setzen("kraefteanzeige", "kraftreferenz_N", 100)
    ein.setzen("kraefteanzeige", "momentreferenz_Nm", 20)
    ein.setzen("kraefteanzeige", "logarithmisch", True)
    bruecke._stil = Stil(ein.bereich)
    snapshot = _snapshot()
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke._kraefte_actors("boot")
    zeichner = bruecke._kraftzeichner()
    kraft, moment = zeichner.skalen["boot"]
    assert (kraft.referenz, moment.referenz) == (100, 20)
    assert (kraft.modus, moment.modus) == ("log", "log")
    assert moment.maximum_px == 48
    zeichner.neu_einpassen(snapshot)
    bruecke._kraefte_actors("boot")
    assert zeichner.skalen["boot"][0].referenz == pytest.approx(11)
    assert ein.get("kraefteanzeige", "kraftreferenz_N") == 100
    assert not any(k in ein._daten["kraefteanzeige"]
                   for k in ("sequenz", "beitraege", "solver", "automatische_referenz"))


def test_neuer_snapshot_wird_ohne_pose_oder_timerwechsel_gezeichnet(bruecke):
    bruecke.kraefte_snapshot_setzen(_snapshot())
    bruecke.render()
    name = "kraefte_('boot', 'hydrostatik')_F"
    actor = bruecke._koerper["boot"]["kraefte_actors"][name]
    vorher = actor.mapper.dataset.lines.copy()
    bruecke.kraefte_daten_veralten("boot")
    assert bruecke._kraftzeichner().skalen["boot"][0].referenz == 10
    modell = Kraftmodell(lambda *_a, **_kw: Auftriebsergebnis(
        .005, (0, .2, 0), (0, 0, 5), (1, 0, 0)), masse=1, g=10)
    erg = modell(((0, 0, 0), (1, 0, 0, 0)))
    bruecke.kraefte_snapshot_setzen(_snapshot(erg, generation=2))
    bruecke.render()
    assert bruecke._kraftzeichner().skalen["boot"][0].referenz == 10
    nachher = bruecke._koerper["boot"]["kraefte_actors"][name].mapper.dataset.points
    assert not np.array_equal(vorher, nachher)
    assert not bruecke._kraftsnapshots_ausstehend


def test_ausgeschaltete_layer_zeigen_auch_keine_nullmarker_oder_labels(bruecke):
    modell = Kraftmodell(lambda *_a, **_kw: Auftriebsergebnis(
        .01, (0, 0, 0), (0, 0, 10), (0, 0, 0)), masse=1, g=10)
    erg = modell(((0, 0, 0), (1, 0, 0, 0)))
    bruecke.kraefte_snapshot_setzen(_snapshot(erg))
    bruecke.render()
    assert bruecke._kraftzeichner().labels
    bruecke._layer.setzen(LAYER_KRAEFTE, False)
    bruecke._layer.setzen(LAYER_MOMENTE, False)
    bruecke.kraefte_snapshot_setzen(_snapshot(erg, sequenz=1))
    bruecke.render()
    assert not bruecke._koerper["boot"]["kraefte_actors"]
    assert not bruecke._kraftzeichner().labels
    assert not bruecke._kraftzeichner().picklinien


def test_auswahl_zeigt_moment_um_p_und_komponenten_ohne_neue_physik(
        bruecke, monkeypatch, tmp_path):
    from segelphysik.core.einstellungen import Einstellungen
    from segelphysik.core.pfeilstil import Stil
    ein = Einstellungen(str(tmp_path / "anzeige.json"))
    ein.setzen("kraefteanzeige", "komponenten", True)
    bruecke._stil = Stil(ein.bereich)
    snapshot = _snapshot()
    bruecke.kraefte_snapshot_setzen(snapshot)
    zeichner = bruecke._kraftzeichner()
    bruecke._kraefte_actors("boot")
    zeichner.auswahl = ("boot", "hydrostatik")
    aufrufe = []
    zeichnen = bruecke._momentbogen_zeichnen

    def aufzeichnen(store, name, stil, moment, mitte, radius, **kw):
        aufrufe.append((name, tuple(moment), tuple(mitte)))
        return zeichnen(store, name, stil, moment, mitte, radius, **kw)

    monkeypatch.setattr(bruecke, "_momentbogen_zeichnen", aufzeichnen)
    bruecke._kraefte_actors("boot")
    assert any(n.endswith("'hydrostatik')_M") and m == (2, 0, 0)
               and p == (0, 0, 0) for n, m, p in aufrufe)
    assert any(n.endswith("'hydrostatik')_M_x") for n, _, _ in aufrufe)
    store = bruecke._koerper["boot"]["kraefte_actors"]
    assert any(n.endswith("_hebelarm") for n in store)
    assert any(n.endswith("_wirkungslinie") for n in store)
    assert any(n.endswith("_P") for n in store)
    assert bruecke._kraefte_daten["boot"] is snapshot


def test_historische_hebelarmoptionen_wirken_auch_im_snapshotrenderer(bruecke, tmp_path):
    from segelphysik.core.einstellungen import Einstellungen
    from segelphysik.core.pfeilstil import Stil
    ein = Einstellungen(str(tmp_path / "stil.json"))
    ein.setzen("pfeil_hebelarm", "farbe", "#112233")
    ein.setzen("pfeil_hebelarm", "deckkraft", .4)
    ein.setzen("pfeil_hebelarm", "vordergrund", False)
    bruecke.stil_setzen(Stil(ein.bereich))
    snapshot = _snapshot()
    auswahl = next(
        b.instanz_id for b in snapshot.beitraege if b.name == "hydrostatik")
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke.kraefte_auswahl_setzen(auswahl)
    bruecke.render()
    assert bruecke._kraftzeichner().auswahl == auswahl
    actor_name = next(
        name for name in bruecke._koerper["boot"]["kraefte_actors"]
        if name.endswith("_hebelarm"))
    actor = bruecke._koerper["boot"]["kraefte_actors"][actor_name]
    assert actor.GetProperty().GetColor() == pytest.approx(
        np.array((0x11, 0x22, 0x33)) / 255)
    assert actor.GetProperty().GetOpacity() == pytest.approx(.4)
    assert actor_name not in bruecke._vg_actors
    ein.setzen("pfeil_hebelarm", "sichtbar", False)
    bruecke.stil_setzen(Stil(ein.bereich))
    bruecke.render()
    assert not any(
        name.endswith("_hebelarm")
        for name in bruecke._koerper["boot"]["kraefte_actors"])
    assert bruecke._kraefte_daten["boot"].bilanz.wrench.moment_Nm == (2, 0, 0)


def test_auswahl_neuer_generation_bleibt_vor_erstem_render_erhalten(bruecke):
    auswahl = ("boot", "hydrostatik")
    for generation in (1, 2, 3):
        bruecke.kraefte_snapshot_setzen(_snapshot(generation=generation))
        assert bruecke._kraftzeichner().auswahl is None
        bruecke.kraefte_auswahl_setzen(auswahl)
        bruecke.render()
        assert bruecke._kraftzeichner().auswahl == auswahl
        assert any(n.endswith("_hebelarm")
                   for n in bruecke._koerper["boot"]["kraefte_actors"])


def test_anzeigekoerperumfang_veraendert_keine_physische_aktivierung(bruecke):
    snapshot = _snapshot()
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke.kraefte_koerperumfang_setzen(("boot",))
    bruecke._kraefte_actors("boot")
    assert bruecke._koerper["boot"]["kraefte_actors"]
    aktiv = bruecke._koerper["boot"]["aktiv"]
    bruecke.kraefte_koerperumfang_setzen(())
    assert not bruecke._koerper["boot"]["kraefte_actors"]
    assert not bruecke._kraftzeichner().labels
    assert bruecke._koerper["boot"]["aktiv"] is aktiv
    assert bruecke._kraefte_daten["boot"] is snapshot


def test_statischer_szenenversatz_verschiebt_nur_geometrie(bruecke, monkeypatch):
    snapshot = replace(_snapshot(), szenenversatz_m=(3, 4, 0))
    bruecke._plotter.camera_position = [(3, -5, 2), (3, 4, 0), (0, 0, 1)]
    pfeile = {}
    zeichnen = bruecke._kraftpfeil_zeichnen

    def aufzeichnen(store, name, stil, pfeil):
        pfeile[name] = pfeil
        return zeichnen(store, name, stil, pfeil)

    monkeypatch.setattr(bruecke, "_kraftpfeil_zeichnen", aufzeichnen)
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke._kraefte_actors("boot")
    assert pfeile["kraefte_('boot', 'hydrostatik')_F"]["start"] == pytest.approx(
        (3, 4.2, 0))
    assert snapshot.kraftpose.translation_m == (0, 0, 0)
    assert snapshot.beitraege[0].wrench.bezugspunkt_m == (0, 0, 0)


def test_resize_und_dpi_buendeln_render_ohne_physik():
    from types import SimpleNamespace
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QWidget
    from segelphysik.gui.kraefte_auswahl import KraefteAuswahlFilter
    app = QApplication.instance() or QApplication([])
    ansicht = QWidget()
    aufrufe = []
    bruecke = SimpleNamespace(_kraftkamera_geaendert=lambda: aufrufe.append(1))
    filter_ = KraefteAuswahlFilter(ansicht, bruecke, None)
    try:
        for typ in (QEvent.Type.Resize, QEvent.Type.ScreenChangeInternal,
                    QEvent.Type.DevicePixelRatioChange):
            filter_.eventFilter(ansicht, QEvent(typ))
        assert len(aufrufe) == 3
    finally:
        ansicht.removeEventFilter(filter_)
        ansicht.close()
        ansicht.deleteLater()
        app.processEvents()


def test_vordergrundfehler_wechselt_nicht_still_den_zeichenmodus(bruecke, monkeypatch):
    import pyvista as pv
    vorher = bruecke._plotter.renderer.GetActors().GetNumberOfItems()

    def fehler():
        raise RuntimeError("Kein Renderlayer")

    monkeypatch.setattr(bruecke, "_vordergrund_renderer", fehler)
    store = {}
    with pytest.raises(RuntimeError, match="Vordergrundebene"):
        bruecke._mesh_setzen(store, "probe", pv.Cube(), True)
    assert not store
    assert bruecke._plotter.renderer.GetActors().GetNumberOfItems() == vorher
    with pytest.raises(RuntimeError, match="raeumliche Darstellung waehlen"):
        bruecke._mesh_setzen(store, "probe", pv.Cube(), True)


def test_identische_grafikdaten_werden_auch_bei_neuer_sequenz_wiederverwendet(
        bruecke, monkeypatch):
    snapshot = _snapshot()
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke._kraefte_actors("boot")
    vorher = dict(bruecke._koerper["boot"]["kraefte_actors"])

    def verboten(*_a, **_kw):
        raise AssertionError("Unveraenderte Geometrie wurde neu vorbereitet")

    monkeypatch.setattr(bruecke._stil, "beitragsstil", verboten)
    bruecke.kraefte_snapshot_setzen(replace(snapshot, sequenz=7, zeit_s=8.5))
    bruecke._kraefte_actors("boot")
    assert bruecke._koerper["boot"]["kraefte_actors"] == vorher
    assert bruecke._kraefte_daten["boot"].sequenz == 7


def test_wiederholtes_entfernen_baut_labels_actoren_und_caches_ab(bruecke):
    renderer = bruecke._plotter.renderer
    vorher = renderer.GetViewProps().GetNumberOfItems()
    for generation in range(1, 11):
        bruecke.kraefte_snapshot_setzen(_snapshot(generation=generation))
        bruecke._kraefte_actors("boot")
        bruecke.kraefte_daten_entfernen("boot")
        assert renderer.GetViewProps().GetNumberOfItems() == vorher
        zeichner = bruecke._kraftzeichner()
        assert not zeichner.labels and not zeichner.label_linien
        assert not zeichner.skalen and not zeichner.skalen_parameter
        assert not zeichner.picklinien
        assert not bruecke._overlay_mesh_cache
    bruecke.kraefte_anzeige_beenden()
    assert bruecke._kraftpfeil_vorlage is None


def test_koerperentfernung_bereinigt_auch_ohne_angeschlossenen_plotter():
    bruecke = GrafikBruecke()
    bruecke._koerper["boot"] = {"kraefte_actors": {}}
    bruecke.kraefte_snapshot_setzen(_snapshot())
    zeichner = bruecke._kraftzeichner()
    assert zeichner.generationen["boot"] == 1
    assert "boot" in bruecke._kraftsnapshots_ausstehend
    bruecke.koerper_entfernen("boot")
    bruecke.koerper_entfernen("boot")
    assert not bruecke._koerper
    assert not bruecke._kraefte_daten
    assert not bruecke._kraftsnapshots_ausstehend
    assert not zeichner.generationen
    assert not zeichner.skalen
    assert not zeichner.zeichenzustaende


def test_labels_verwenden_echte_textmasse_und_blenden_bei_platzmangel_aus(bruecke):
    bruecke._plotter.window_size = (900, 500)
    snapshot = _snapshot()
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke._kraefte_actors("boot")
    id_ = ("boot", "hydrostatik")
    bruecke.kraefte_auswahl_setzen(id_)
    bruecke._kraefte_actors("boot")
    zeichner = bruecke._kraftzeichner()
    assert id_ in zeichner.labels
    assert len(zeichner.labels) == 2
    assert all(not linie.GetMapper().GetScalarVisibility()
               for linie in zeichner.label_linien.values())
    rechtecke = []
    for actor in zeichner.labels.values():
        groesse = [0., 0.]
        actor.GetSize(bruecke._plotter.renderer, groesse)
        x, y = actor.GetPosition()
        breite, hoehe = groesse
        assert 0 <= x < x + breite <= 900
        assert 0 <= y < y + hoehe <= 500
        rechtecke.append((x, y, breite, hoehe))
    x, y, breite, hoehe = rechtecke[0]
    ox, oy, ob, oh = rechtecke[1]
    assert x + breite <= ox or ox + ob <= x or y + hoehe <= oy or oy + oh <= y
    bruecke._plotter.window_size = (220, 200)
    bruecke._kraefte_actors("boot")
    assert id_ not in zeichner.labels
    assert id_ in zeichner.picklinien
    assert bruecke.kraefte_snapshot_ermitteln("boot") is snapshot


@pytest.mark.parametrize("parallel", (False, True))
def test_gesamtsumme_hat_kameraabhaengige_dunkle_kontur(bruecke, parallel):
    kamera = bruecke._plotter.camera
    kamera.parallel_projection = parallel
    snapshot = _snapshot()
    bruecke.kraefte_snapshot_setzen(snapshot)
    bruecke._kraefte_actors("boot")
    store = bruecke._koerper["boot"]["kraefte_actors"]
    name = "kraefte_" + repr(snapshot.bilanz.instanz_id) + "_M_kontur"
    actor = store[name]
    assert actor.GetProperty().GetColor() == pytest.approx((.2, .2, .2))
    assert actor.mapper.dataset.n_cells > 0
    vorher = actor.mapper.dataset.points.copy()
    kamera.position = (4, 2, 3)
    bruecke._kraefte_actors("boot")
    assert store[name] is actor
    nachher = actor.mapper.dataset.lines
    assert not np.array_equal(vorher, nachher)
    bruecke.kraefte_daten_entfernen("boot")
    assert not store


def test_stil_aendern_wertet_keine_physik_erneut_aus():
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    from types import SimpleNamespace
    stile = []
    fenster._bruecke = SimpleNamespace(stil_setzen=stile.append)
    fenster._btn_echtzeit.setChecked(True)

    def verboten(*_a, **_kw):
        raise AssertionError("Eine Stilaenderung darf keine Physik auswerten")

    fenster._echtzeit_kraftfunktion = verboten
    fenster._aktuelles_kraftbild_aktualisieren = verboten
    fenster._statisches_kraftbild_aktualisieren = verboten
    fenster._stil_anwenden()
    assert len(stile) == 1
    fenster.close()
    app.processEvents()


@pytest.mark.parametrize("statisch", (True, False))
def test_gui_api_ansichten_sichtbarkeit_und_reset_ohne_physik(
        bruecke, monkeypatch, tmp_path, statisch):
    from types import SimpleNamespace
    from PySide6.QtCore import Qt
    from segelphysik.core.einstellungen import Einstellungen
    from segelphysik.gui.hauptfenster import HauptFenster
    from segelphysik.gui.kraefte_werte import SNAPSHOT_ROLLE
    app = QApplication.instance() or QApplication([])
    ein = Einstellungen(str(tmp_path / "settings.json"))
    monkeypatch.setattr(Einstellungen, "laden", lambda: ein)
    fenster = HauptFenster()
    fenster._bruecke = bruecke
    try:
        if not statisch:
            fenster._btn_echtzeit.setChecked(True)
        bruecke._koerper["boot"]["position_basis"] = (3, 4, 0)
        fenster._kraftbild_daten_setzen(
            bruecke, "boot", SimpleNamespace(masse=1, quell_id="knoten:boot"),
            _modell(), SimpleNamespace(g_m_pro_s2=10), 0, 0,
            ergebnis=_modell()(((0, 0, 0), (1, 0, 0, 0))))
        snapshot = fenster._kraftanzeige_snapshots["boot"]
        assert snapshot.szenenversatz_m == ((3, 4, 0) if statisch else (0, 0, 0))

        def verboten(*_a, **_kw):
            raise AssertionError("Anzeigeoption hat Physik gestartet")

        fenster._aktuelles_kraftbild_aktualisieren = verboten
        fenster._statische_simulation_ausfuehren = verboten
        api = fenster.steuer_api
        for titel in ("Koerperframe", "Bezug Weltursprung", "Momentenkomponenten"):
            id_ = next(c["id"] for c in api.controls() if c["label"] == titel)
            api.set_control(id_, True)
        assert ein.get("kraefteanzeige", "komponenten")
        assert ein.get("kraefteanzeige", "koerperframe")
        assert "Weltursprung" in fenster._kraefte_werte.kopf.text()
        assert not fenster._echtzeit_timer.isActive()
        modell = fenster._kraefte_werte.modell
        assert modell.index(0, 0).data(SNAPSHOT_ROLLE) is snapshot
        id_ = ("boot", "hydrostatik")
        modell.setData(modell.index_fuer_id(id_, 1), Qt.CheckState.Unchecked,
                       Qt.ItemDataRole.CheckStateRole)
        assert ein.get("kraefteanzeige", "sichtbarkeiten") == {
            "knoten:boot": {"hydrostatik": False}}
        assert bruecke._kraftzeichner().sichtbar[id_] is False
        fenster._kraftanzeige_zuruecksetzen()
        assert not ein.get("kraefteanzeige", "komponenten")
        assert not ein.get("kraefteanzeige", "sichtbarkeiten")
        assert modell.index_fuer_id(id_, 1).data(
            Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked.value
        assert bruecke._kraefte_daten["boot"] is snapshot
    finally:
        fenster.close()
        app.processEvents()


@pytest.mark.parametrize("statisch", (True, False))
def test_echte_stildialogfelder_aktualisieren_statikkraefte_und_pause_ohne_worker(
        bruecke, monkeypatch, statisch):
    from PySide6.QtWidgets import QCheckBox
    from segelphysik.core import pfeilstil as ps
    from segelphysik.gui.einstellungen_dialog import FarbFeld
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()

    def verboten(*_args, **_kwargs):
        raise AssertionError("Grafische Einstellung startet einen Physikauftrag")

    try:
        fenster._bruecke = bruecke
        if not statisch:
            fenster._btn_echtzeit.setChecked(True)
        snapshot = _snapshot()
        fenster._kraftanzeige_snapshots["boot"] = snapshot
        fenster._kraefte_werte.snapshots_setzen((snapshot,))
        bruecke.kraefte_snapshot_setzen(snapshot)
        bruecke.render()
        monkeypatch.setattr(fenster, "_statische_simulation_ausfuehren", verboten)
        monkeypatch.setattr(fenster, "_aktuelles_kraftbild_aktualisieren", verboten)
        felder = (
            ("kraefteanzeige", "logarithmisch", True),
            ("kraefteanzeige", "kraftreferenz_N", 20.),
            ("kraefteanzeige", "momentreferenz_Nm", 5.),
            ("kraefteanzeige", "kraftmaximum_px", 150.),
            ("kraefteanzeige", "momentmaximum_px", 40.),
            ("kraefteanzeige", "breite_px", 4.),
            ("kraefteanzeige", "kopflaenge_px", 12.),
            ("kraefteanzeige", "beschriftung", False),
            ("kraefteanzeige", "farbe_hydrostatik", "#123456"),
            (ps.BEREICH_ALLGEMEIN, "dicke", .7),
            (ps.BEREICH_ALLGEMEIN, "kopf_laenge", 6.),
            (ps.BEREICH_ALLGEMEIN, "kopf_durchmesser", 3.),
            (ps.BEREICH_ALLGEMEIN, "strich_laenge", 4.),
            (ps.BEREICH_ALLGEMEIN, "strich_luecke", 3.),
            (ps.BEREICH_ALLGEMEIN, "mindestlaenge", 3.),
            (ps.BEREICH_ALLGEMEIN, "kraftskala", .1),
            (ps.BEREICH_ALLGEMEIN, "momentskala", .1),
            (ps.BEREICH_ALLGEMEIN, "vordergrund", False),
            ("pfeil_f_a", "kopf", 1.4),
            ("pfeil_f_a", "gestrichelt", False),
            ("pfeil_f_a", "deckkraft", .6),
            ("pfeil_f_a", "skala", 1.2),
        )
        formular = [
            (b, [k for gruppe, k, _wert in felder if gruppe == b])
            for b in dict.fromkeys(b for b, _k, _wert in felder)]
        fenster._pfeil_dialog("kp_triggerprobe", "Triggerprobe", formular)
        dialog = fenster._einstellungen_dialoge["kp_triggerprobe"]
        for bereich, key, wert in felder:
            feld = next(
                feld for b, k, feld in dialog._feld_liste if (b, k) == (bereich, key))
            alter_stil = bruecke._stil
            if isinstance(feld, QCheckBox):
                feld.setChecked(wert)
            elif isinstance(feld, FarbFeld):
                feld._text.setText(wert)
                feld._text.editingFinished.emit()
            else:
                feld.setValue(wert)
            assert fenster._einstellungen.get(bereich, key) == wert
            assert bruecke._stil is not alter_stil
            assert bruecke._kraftzeichner().zeichenzustaende["boot"][7] is bruecke._stil
            assert bruecke.kraefte_snapshot_ermitteln("boot") is snapshot
            assert fenster._kraefte_werte._snapshots[0] is snapshot
            assert not fenster._echtzeit_timer.isActive()
        actor = bruecke._koerper["boot"]["kraefte_actors"][
            "kraefte_('boot', 'hydrostatik')_F"]
        assert actor.GetProperty().GetOpacity() == pytest.approx(.6)
        assert actor.GetProperty().GetColor() == pytest.approx((
            0x12 / 255, 0x34 / 255, 0x56 / 255))
        assert not bruecke._kraftzeichner().labels
    finally:
        fenster.close()
        app.processEvents()


def test_identische_snapshots_haben_modusunabhaengige_geometrie_und_tabellenwerte(
        bruecke):
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    snapshot = _snapshot()
    referenz = None

    def zeilen(modell, parent=None):
        from PySide6.QtCore import QModelIndex
        parent = QModelIndex() if parent is None else parent
        ergebnis = []
        for row in range(modell.rowCount(parent)):
            ergebnis.append(tuple(
                modell.index(row, col, parent).data()
                for col in range(modell.columnCount(parent))))
            ergebnis.extend(zeilen(modell, modell.index(row, 0, parent)))
        return ergebnis

    for modus in ("statisch", "stationaer", "pause", "dynamisch"):
        fenster = HauptFenster()
        try:
            bruecke.kraefte_daten_entfernen("boot")
            fenster._bruecke = bruecke
            if modus in ("pause", "dynamisch"):
                fenster._btn_echtzeit.setChecked(True)
            for key, wert in (("kraftreferenz_N", 20.), ("momentreferenz_Nm", 5.),
                              ("komponenten", True)):
                fenster._einstellungen.setzen("kraefteanzeige", key, wert)
            fenster._kraftanzeige_snapshots["boot"] = snapshot
            fenster._kraefte_werte.snapshots_setzen((snapshot,))
            bruecke.kraefte_snapshot_setzen(snapshot)
            fenster._stil_anwenden()
            bruecke.render()
            geometrie = {
                name: actor.mapper.dataset.points.copy()
                for name, actor in bruecke._koerper["boot"]["kraefte_actors"].items()
            }
            werte = zeilen(fenster._kraefte_werte.modell)
            assert geometrie and werte
            if referenz is None:
                referenz = geometrie, werte
            else:
                original, zahlen = referenz
                assert geometrie.keys() == original.keys(), modus
                for name, punkte in geometrie.items():
                    assert punkte == pytest.approx(original[name]), (modus, name)
                assert werte == zahlen, modus
            assert fenster._kraefte_werte._snapshots[0] is snapshot
            assert bruecke.kraefte_snapshot_ermitteln("boot") is snapshot
        finally:
            fenster.close()
            app.processEvents()


def test_brueckenwechsel_und_schliessen_hinterlassen_keine_doppelten_signale(
        monkeypatch):
    from types import SimpleNamespace
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QWidget
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])

    class Ansicht(QWidget):
        frameSwapped = Signal()

    eins, zwei = Ansicht(), Ansicht()
    beendet, frames = [], []

    def bruecke(ansicht):
        return SimpleNamespace(
            _plotter=ansicht, layer_setzen=lambda *_a: None,
            kraefte_anzeige_beenden=lambda: beendet.append(ansicht))

    b1, b2 = bruecke(eins), bruecke(zwei)
    fenster = HauptFenster()
    fenster._navigationsfenster = QWidget()
    for name in ("_stil_anwenden", "_darstellung_auf_bruecke_anwenden",
                 "_laufzeit_objekte_aktualisieren"):
        monkeypatch.setattr(fenster, name, lambda *_a: None)
    monkeypatch.setattr(fenster, "_schulungsframe_fertig", lambda: frames.append(1))
    try:
        fenster.bruecke_setzen(b1)
        fenster.bruecke_setzen(b1)
        eins.frameSwapped.emit()
        assert len(frames) == 1
        fenster.bruecke_setzen(b2)
        eins.frameSwapped.emit()
        zwei.frameSwapped.emit()
        assert len(frames) == 2 and beendet == [eins]
        fenster.close()
        zwei.frameSwapped.emit()
        assert len(frames) == 2 and beendet == [eins, zwei]
        assert fenster._kraftauswahl_filter is None
    finally:
        fenster.close()
        eins.close()
        zwei.close()
        eins.deleteLater()
        zwei.deleteLater()
        app.processEvents()


def test_gui_und_renderer_erhalten_identischen_snapshot(monkeypatch, tmp_path):
    from segelphysik.core.einstellungen import Einstellungen
    from segelphysik.gui.hauptfenster import HauptFenster
    from segelphysik.gui.kraefte_werte import SNAPSHOT_ROLLE
    from types import SimpleNamespace
    app = QApplication.instance() or QApplication([])
    ein = Einstellungen(str(tmp_path / "settings.json"))
    monkeypatch.setattr(Einstellungen, "laden", lambda: ein)
    fenster = HauptFenster()
    try:
        ergebnis = _modell()(((0, 0, 0), (1, 0, 0, 0)))
        class Bruecke:
            def kraefte_snapshot_setzen(self, snapshot):
                self.snapshot = snapshot
            def kraefte_daten_setzen(self, *_a, **_kw):
                raise AssertionError("GUI benutzt den alten Dateneingang")
        bruecke = Bruecke()
        fenster._kraftbild_daten_setzen(
            bruecke, "boot", SimpleNamespace(masse=1, punkte=np.array([[0, 0, 0], [1, 1, 1]])),
            _modell(), SimpleNamespace(g_m_pro_s2=10, dt_s=.01), 0, 0,
            ergebnis=ergebnis, solverdiagnose=(
                "Originalsolver", ("z", "rollen"),
                (("Solverresiduum", 2.0, .5),), False, False))
        index = fenster._kraefte_werte.modell.index(0, 0)
        assert index.data(SNAPSHOT_ROLLE) is bruecke.snapshot
        assert fenster._kraftanzeige_snapshots["boot"] is bruecke.snapshot
        assert bruecke.snapshot.solverbewertung.kriterien == (
            ("Solverresiduum", 2.0, .5),)
        assert bruecke.snapshot.gleichgewichtsstatus == "Kriterien nicht erfuellt"
    finally:
        fenster.close()
        app.processEvents()


def test_statik_liefert_fuer_jeden_sichtbaren_koerper_einen_snapshot(
        bruecke, monkeypatch):
    from types import SimpleNamespace
    from segelphysik.core.koerper import Koerper
    from segelphysik.gui import hauptfenster as hf
    from segelphysik.gui import baum
    app = QApplication.instance() or QApplication([])
    fenster = hf.HauptFenster()
    aufgaben = []
    namen = ("boot", "zweites")
    try:
        fenster._bruecke = bruecke
        fenster.baum._welt = SimpleNamespace(konfiguration=SimpleNamespace(
            ordner="isolierter-test", wasser_dichte=lambda: 1000))
        monkeypatch.setattr(baum, "summenkoerper", lambda _welt: [
            SimpleNamespace(name=name, sichtbar=True) for name in namen]
            + [SimpleNamespace(name="unsichtbar", sichtbar=False)])
        monkeypatch.setattr(
            hf.QThreadPool, "globalInstance",
            lambda: SimpleNamespace(start=aufgaben.append, maxThreadCount=lambda: 2))
        monkeypatch.setattr(fenster, "_navigationsanzeigen_aktualisieren", lambda: None)
        bruecke.statische_pose_setzen = lambda *_args: True
        for name in namen:
            fenster._laufzeit_koerper[name] = Koerper(
                form=build_box(1, 1, 1), dichte=1)
            bruecke._koerper[name] = {
                "aktiv": False, "position": np.zeros(3),
                "overlay_skala": (1, .05)}
        fenster._statische_simulation_ausfuehren()
        assert [a.name for a in aufgaben] == list(namen)
        assert len({a.generation for a in aufgaben}) == 1
        generation = fenster._statisch_generation
        for aufgabe in reversed(aufgaben):
            modell = _modell()
            ergebnis = {
                "z": 0., "phi": 0., "gm": .2, "iterationen": 1,
                "restkraft": 0., "restmoment": 2.,
                "kraft_ergebnis": modell(((0, 0, 0), (1, 0, 0, 0)))}
            fenster._statische_aufgabe_abgeschlossen(
                generation, aufgabe.name, ergebnis,
                (modell, SimpleNamespace(g_m_pro_s2=10)), None)
        assert set(fenster._kraftanzeige_snapshots) == set(namen)
        fenster._kraftansicht_setzen("mehrkoerper", True)
        assert fenster._kraefte_werte.modell.rowCount() == 2
        for name in namen:
            assert bruecke.kraefte_snapshot_ermitteln(name) is (
                fenster._kraftanzeige_snapshots[name])
            assert not bruecke._koerper[name]["aktiv"]
        # Neue fachliche Generation entfernt beide alten Anzeigen sofort.
        fenster._statische_simulation_ausfuehren()
        assert not bruecke._kraefte_daten
        fenster._statische_aufgabe_abgeschlossen(
            generation, "boot", ergebnis, (modell, SimpleNamespace(g_m_pro_s2=10)),
            ValueError("ueberholter Testfehler"))
        assert not fenster._kraftanzeige_snapshots
        assert "ueberholter Testfehler" in fenster.protokoll.toPlainText()
    finally:
        fenster.close()
        app.processEvents()


@pytest.mark.parametrize("kapazitaet", (-1, 0, 1, 2))
def test_statikqueue_beachtet_qt_mindestkapazitaet_und_startet_alle_aktuellen_koerper(
        monkeypatch, kapazitaet):
    from types import SimpleNamespace
    from segelphysik.gui import hauptfenster as hf
    app = QApplication.instance() or QApplication([])
    gestartet = []
    monkeypatch.setattr(hf.QThreadPool, "globalInstance", lambda: SimpleNamespace(
        start=gestartet.append, maxThreadCount=lambda: kapazitaet))
    fenster = hf.HauptFenster()
    try:
        for index in range(3):
            fenster._statische_aufgabe_starten(SimpleNamespace(
                name="boot_%s" % index, generation=fenster._statisch_generation))
        assert len(gestartet) == min(3, max(1, kapazitaet))
        erledigt = []
        while gestartet:
            aufgabe = gestartet.pop(0)
            erledigt.append(aufgabe.name)
            fenster._statische_aufgabe_abgeschlossen(
                aufgabe.generation, aufgabe.name, None, None, None)
            assert len(fenster._statische_aufgaben) <= max(1, kapazitaet)
        assert erledigt == ["boot_0", "boot_1", "boot_2"]
        assert not fenster._statische_aufgaben
        assert not fenster._statische_aufgaben_ausstehend
    finally:
        fenster.close()
        app.processEvents()


@pytest.mark.slow
@pytest.mark.parametrize("abschluss", ("neuester-stand", "moduswechsel", "schliessen"))
def test_statische_aenderungsserien_halten_nur_den_neuesten_folgeauftrag(
        bruecke, monkeypatch, abschluss):
    from types import SimpleNamespace
    from segelphysik.core.koerper import Koerper
    from segelphysik.gui import baum, hauptfenster as hf
    app = QApplication.instance() or QApplication([])
    fenster = hf.HauptFenster()
    aufgaben = []
    try:
        fenster._bruecke = bruecke
        fenster.baum._welt = SimpleNamespace(konfiguration=SimpleNamespace(
            ordner="isolierter-test", wasser_dichte=lambda: 1000))
        monkeypatch.setattr(baum, "summenkoerper", lambda _welt: [
            SimpleNamespace(name="boot", sichtbar=True)])
        monkeypatch.setattr(
            hf.QThreadPool, "globalInstance",
            lambda: SimpleNamespace(start=aufgaben.append, maxThreadCount=lambda: 2))
        fenster._laufzeit_koerper["boot"] = Koerper(
            form=build_box(1, 1, 1), dichte=1)
        fenster._statische_simulation_ausfuehren()
        erste = aufgaben[0]
        fenster._fremd_check.setChecked(True)
        for betrag in range(1, 101):
            fenster.steuer_api.set_control("fremd_felder.betrag", betrag)
        for key, wert in (("azimut", 35), ("elevation", 20),
                          ("x", .1), ("y", .2), ("z", .3)):
            fenster.steuer_api.set_control("fremd_felder." + key, wert)
        fenster._ruderwinkel_feld.setEnabled(True)
        fenster.steuer_api.set_control("ruderwinkel_feld", 12)
        fenster._einstellungen_dialog("statisch")
        dialog = fenster._einstellungen_dialoge["statisch"]
        for key, wert in (("toleranz", 1e-7), ("max_iterationen", 42),
                          ("stagnation_anteil", .1)):
            dialog._felder[key].setValue(wert)
        assert len(aufgaben) == 1
        assert len(fenster._statische_aufgaben_ausstehend) == 1
        letzte = fenster._statische_aufgaben_ausstehend["boot"]
        assert np.linalg.norm(letzte.fremdkraft[0]) == pytest.approx(100)
        assert letzte.fremdkraft == fenster._fremdkraft_aktuell()
        assert letzte.ruderwinkel_rad == pytest.approx(math.radians(12))
        assert letzte.parameter == {
            "tol": 1e-7, "max_iter": 42, "stagnation_anteil": .1}
        if abschluss == "moduswechsel":
            monkeypatch.setattr(fenster, "_echtzeit_starten", lambda: None)
            fenster._btn_echtzeit.click()
        elif abschluss == "schliessen":
            fenster.close()
        fenster._statische_aufgabe_abgeschlossen(
            erste.generation, "boot", None, None, ValueError("Alter Solverfehler"))
        assert "Alter Solverfehler" in fenster.protokoll.toPlainText()
        assert not fenster._kraftanzeige_snapshots
        assert not fenster._statische_aufgaben_ausstehend
        assert len(aufgaben) == (2 if abschluss == "neuester-stand" else 1)
        if abschluss == "neuester-stand":
            assert aufgaben[-1] is letzte
            assert fenster._statische_aufgaben == {"boot": letzte.generation}
        else:
            assert not fenster._statische_aufgaben
    finally:
        fenster.close()
        app.processEvents()


def test_echtzeit_werte_verzoegern_nicht_3d_und_pause_zeigt_endwert(
        bruecke, monkeypatch):
    from types import SimpleNamespace
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    try:
        fenster._bruecke = bruecke
        monkeypatch.setattr(fenster, "_echtzeit_pose_anzeigen", lambda *_a, **_kw: None)
        monkeypatch.setattr(fenster, "_navigationsanzeigen_aktualisieren", lambda: None)
        fenster._echtzeit_timer.start()
        koerper = SimpleNamespace(masse=1, punkte=np.array([[0, 0, 0], [1, 1, 1]]))
        physik = SimpleNamespace(g_m_pro_s2=10)
        modell = _modell()
        erg = modell(((0, 0, 0), (1, 0, 0, 0)))
        fenster._kraftbild_daten_setzen(
            bruecke, "boot", koerper, modell, physik, 0, 0, ergebnis=erg)
        snapshot = fenster._kraftanzeige_snapshots["boot"]
        assert bruecke._kraefte_daten
        assert fenster._kraefte_werte._werte_timer.isActive()
        assert fenster._kraefte_werte.modell.rowCount() == 0
        fenster._zeit_pausieren()
        assert fenster._kraefte_werte._snapshots == (snapshot,)
        assert not fenster._kraefte_werte._werte_timer.isActive()
        fenster._echtzeit_timer.start()
        fenster._kraftanzeige_verwerfen("Kraftauswertung fehlgeschlagen")
        fenster._zeit_pausieren()
        assert "Kraftauswertung fehlgeschlagen" in fenster._kraefte_werte.kopf.text()
    finally:
        fenster.close()
        app.processEvents()


def test_ungueltiges_folgeergebnis_entfernt_die_alte_anzeige(bruecke):
    from types import SimpleNamespace
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    try:
        fenster._bruecke = bruecke
        koerper = SimpleNamespace(masse=1, punkte=np.array([[0, 0, 0], [1, 1, 1]]))
        physik = SimpleNamespace(g_m_pro_s2=10)
        modell = _modell()
        erg = modell(((0, 0, 0), (1, 0, 0, 0)))
        fenster._kraftbild_daten_setzen(
            bruecke, "boot", koerper, modell, physik, 0, 0, ergebnis=erg)
        bruecke.render()
        assert bruecke._koerper["boot"]["kraefte_actors"]
        fenster._kraftbild_daten_setzen(
            bruecke, "boot", koerper, modell, physik, 0, 0,
            ergebnis=replace(erg, kraftpose=None))
        assert not fenster._kraftanzeige_snapshots
        assert not bruecke._kraefte_daten
        assert not bruecke._koerper["boot"]["kraefte_actors"]
        assert "ungueltige Anzeigedaten" in fenster._kraefte_werte.kopf.text()
        assert "ausgewertete Kraftpose" in fenster.protokoll.toPlainText()
    finally:
        fenster.close()
        app.processEvents()


def test_fehlendes_ergebnis_startet_keine_ersatzphysik_im_anzeigepfad(bruecke):
    from types import SimpleNamespace
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    aufrufe = []

    def kraftfunktion(*_args, **_kwargs):
        aufrufe.append(True)
        raise AssertionError("GUI darf fehlende Workerdaten nicht selbst berechnen")

    try:
        fenster._bruecke = bruecke
        snapshot = _snapshot()
        fenster._kraftanzeige_snapshots["boot"] = snapshot
        bruecke.kraefte_snapshot_setzen(snapshot)
        fenster._kraefte_werte.snapshots_setzen((snapshot,))
        fenster._kraftbild_daten_setzen(
            bruecke, "boot", SimpleNamespace(masse=1), kraftfunktion,
            SimpleNamespace(g_m_pro_s2=10), 0, 0)
        assert not aufrufe
        assert not fenster._kraftanzeige_snapshots
        assert not bruecke._kraefte_daten
        assert "Kraftergebnis fehlt" in fenster.protokoll.toPlainText()
        assert "ungueltige Anzeigedaten" in fenster._kraefte_werte.kopf.text()
    finally:
        fenster.close()
        app.processEvents()


@pytest.mark.slow
@pytest.mark.parametrize(("eigenschaft", "wert"), (
    ("Material", "Stahl"), ("Dichte", 2000.), ("Wanddicke", 6.),
    ("Masse", 55.), ("Position x", .15), ("Position y", .25),
    ("Position z", .35), ("Bauteil", False), ("Modell", True),
    ("Modellpfad", False)))
@pytest.mark.parametrize("statisch", (True, False))
def test_reale_baumeigenschaft_erneuert_snapshot_gewicht_und_schwerpunkt(
        bruecke, monkeypatch, tmp_path, eigenschaft, wert, statisch):
    from pathlib import Path
    from types import SimpleNamespace
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QTreeWidgetItemIterator
    from segelphysik.core.konfig_lader import lade_konfig
    from segelphysik.core.segler_einstellungen import SeglerEinstellungen
    from segelphysik.gui import baum, hauptfenster as hf
    from segelphysik.gui.baum_widget import SPALTE_CHECK, SPALTE_NAME
    app = QApplication.instance() or QApplication([])
    konfig = lade_konfig(str(Path(__file__).resolve().parents[1] / "konfigurationen"))
    konfig.segler_einstellungen = SeglerEinstellungen(tmp_path / "segler.json")
    welt = baum.welt_aus_konfig(konfig)
    segler = eigenschaft == "Masse" or eigenschaft.startswith("Position ")
    name = ("optimist"
            if eigenschaft in ("Dichte", "Bauteil", "Modell") or segler
            else "yacht1")
    baum.sichtbarkeit_setzen(welt, name)
    aufgaben = []
    monkeypatch.setattr(
        hf.QThreadPool, "globalInstance",
        lambda: SimpleNamespace(start=aufgaben.append, maxThreadCount=lambda: 2))
    fenster = hf.HauptFenster()
    try:
        fenster.baum_setzen(welt)
        fenster._bruecke = bruecke
        if not statisch:
            fenster._btn_echtzeit.setChecked(True)
        monkeypatch.setattr(
            fenster, "_geometrie_konflikte_bereinigen", lambda *_args: True)
        fenster._laufzeit_objekte_aktualisieren("start")
        assert len(aufgaben) == 1, fenster.protokoll.toPlainText()
        aufgaben.pop().run()
        alt = fenster._kraftanzeige_snapshots[name]
        masse_alt = fenster._laufzeit_koerper[name].masse
        schwerpunkt_alt = fenster._laufzeit_schwerpunkt[name]
        if eigenschaft == "Modellpfad":
            fenster._einstellungen_dialog("modell")
            dialog = fenster._einstellungen_dialoge["modell"]
            dialog._felder["paketfabrik_aktiv"].setChecked(wert)
            assert konfig.paketfabrik_aktiv is wert
        elif eigenschaft in ("Bauteil", "Modell"):
            knoten = (baum.finde(baum.finde(welt, name), "segel")
                      if eigenschaft == "Bauteil" else baum.finde(welt, "folkeboot"))
            iterator = QTreeWidgetItemIterator(fenster.baum)
            while iterator.value() is not None:
                item = iterator.value()
                if item.data(SPALTE_NAME, Qt.ItemDataRole.UserRole) is knoten:
                    item.setCheckState(
                        SPALTE_CHECK,
                        Qt.CheckState.Checked if wert else Qt.CheckState.Unchecked)
                    break
                iterator += 1
            else:
                pytest.fail("Koerperknoten fehlt im echten Baum")
            app.processEvents()
            if eigenschaft == "Modell":
                name = "folkeboot"
        else:
            knoten = baum.finde(baum.finde(welt, name), "segler" if segler else "rumpf")
            fenster.baum._eigenschaft_setzen(knoten, eigenschaft, wert)
        assert not fenster._kraftanzeige_snapshots
        assert not bruecke._kraefte_daten
        assert len(aufgaben) == 1, fenster.protokoll.toPlainText()
        aufgaben.pop().run()
        assert name in fenster._kraftanzeige_snapshots, fenster.protokoll.toPlainText()
        neu = fenster._kraftanzeige_snapshots[name]
        koerper = fenster._laufzeit_koerper[name]
        assert neu.generation > alt.generation
        if eigenschaft == "Modellpfad":
            assert neu is not alt
        elif eigenschaft.startswith("Position "):
            assert koerper.masse == pytest.approx(masse_alt)
            assert fenster._laufzeit_schwerpunkt[name] != pytest.approx(schwerpunkt_alt)
        else:
            assert koerper.masse != pytest.approx(masse_alt)
        gewicht = next(b for b in neu.beitraege if b.name == "schwerkraft")
        physik = (fenster._statische_arbeitsdaten[name][1]
                  if statisch else fenster._echtzeit_physik)
        assert gewicht.wrench.kraft_N == pytest.approx((
            0, 0, -koerper.masse * physik.g_m_pro_s2))
        assert bruecke.kraefte_snapshot_ermitteln(name) is neu
        assert fenster._kraefte_werte._snapshots[0] is neu
        assert not fenster._echtzeit_timer.isActive()
        assert fenster._echtzeit_berechnet_s == 0
    finally:
        fenster.close()
        app.processEvents()


@pytest.mark.parametrize("schritte", (0, 1))
def test_echtzeitantwort_ohne_kraftergebnis_invalidiert_statt_alte_anzeige(
        bruecke, schritte):
    from types import SimpleNamespace
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    fenster = HauptFenster()
    try:
        fenster._btn_echtzeit.setChecked(True)
        fenster._bruecke = bruecke
        fenster._echtzeit_name = "boot"
        fenster._echtzeit_physik = SimpleNamespace(dt_s=.01, g_m_pro_s2=10)
        fenster._echtzeit_generation = 1
        fenster._echtzeit_aufgabe_sequenz_laufend = 3
        fenster._echtzeit_aufgabe_laeuft = True
        fenster._echtzeit_schritte_laufend = schritte
        snapshot = _snapshot()
        fenster._kraftanzeige_snapshots["boot"] = snapshot
        bruecke.kraefte_snapshot_setzen(snapshot)
        fenster._kraefte_werte.snapshots_setzen((snapshot,))
        bruecke.render()
        fenster._echtzeit_aufgabe_abgeschlossen(
            1, 3, "boot", Zustand6DOF(), None, None, 0)
        assert not fenster._kraftanzeige_snapshots
        assert not bruecke._kraefte_daten
        assert not bruecke._koerper["boot"]["kraefte_actors"]
        assert not fenster._kraefte_werte._snapshots
        assert fenster._echtzeit_berechnet_s == 0
        assert not fenster._echtzeit_aufgabe_laeuft
        assert "kein Kraftergebnis" in fenster.protokoll.toPlainText()
    finally:
        fenster.close()
        app.processEvents()


@pytest.mark.slow
@pytest.mark.parametrize("statisch", (True, False))
@pytest.mark.parametrize("aenderung", (
    "g", "rho", "widerstand", "added_mass", "fluid", "koerperwechsel", "importserie"))
def test_konfigurationsimport_erneuert_umgebung_und_modellparameter_ohne_timer(
        bruecke, monkeypatch, tmp_path, statisch, aenderung):
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from segelphysik.core.konfig_lader import lade_konfig
    from segelphysik.gui import baum, hauptfenster as hf
    app = QApplication.instance() or QApplication([])
    root = Path(__file__).resolve().parents[1] / "konfigurationen"
    material = json.loads((root / "materialien.json").read_text(encoding="utf-8"))
    physik = json.loads((root / "physik.json").read_text(encoding="utf-8"))
    physik["physik"]["daempfung"] = {"tauchung": 0., "kraengung": 0.}
    kraefte = physik["physik"]["kraefte"] = {
        "linear_widerstand_kg_pro_s": [1. if aenderung == "fluid" else 0.] * 6,
        "quadratischer_widerstand_kg_pro_m": [0.] * 6,
        "added_mass_kg_und_kg_m2": [0.] * 6,
        "fluidgeschwindigkeit_m_pro_s": [0.] * 3,
        "fluidwinkelgeschwindigkeit_rad_pro_s": [0.] * 3,
    }
    name = "pruefquader"
    (tmp_path / "koerper.json").write_text(json.dumps({
        "darstellung": {"delta_helligkeit_unterwasser": .2,
                        "farbe_standard": "#888888"},
        "summenkoerper": {name: {
            "form": {"typ": "box", "dx_m": 2., "dy_m": 2., "dz_m": 1.},
            "dichte_kg_pro_m3": 500., "farbe": "#00b140",
            "farbe_unter_wasser": "#00802e"}}}), encoding="utf-8")

    def konfig_schreiben():
        for datei, daten in (("materialien.json", material), ("physik.json", physik)):
            (tmp_path / datei).write_text(json.dumps(daten), encoding="utf-8")
        welt = baum.welt_aus_konfig(lade_konfig(str(tmp_path)))
        baum.sichtbarkeit_setzen(welt, name)
        return welt

    aufgaben = []
    monkeypatch.setattr(
        hf.QThreadPool, "globalInstance",
        lambda: SimpleNamespace(start=aufgaben.append, maxThreadCount=lambda: 2))
    fenster = hf.HauptFenster()
    try:
        welt = konfig_schreiben()
        fenster.baum_setzen(welt)
        fenster._bruecke = bruecke
        if not statisch:
            fenster._btn_echtzeit.setChecked(True)
        fenster._laufzeit_objekte_aktualisieren("start")
        assert len(aufgaben) == 1, fenster.protokoll.toPlainText()
        aufgaben.pop().run()
        assert name in fenster._kraftanzeige_snapshots, fenster.protokoll.toPlainText()
        alt = fenster._kraftanzeige_snapshots[name]
        if aenderung == "g":
            physik["physik"]["g_m_pro_s2"] = 8.
        elif aenderung == "rho":
            wasser = material["wasser"]
            wasser["dichten_kg_pro_m3"][wasser["standard"]] = 1050.
        elif aenderung == "widerstand":
            kraefte["linear_widerstand_kg_pro_s"] = [1.] * 6
            kraefte["quadratischer_widerstand_kg_pro_m"] = [.2] * 6
        elif aenderung == "added_mass":
            kraefte["added_mass_kg_und_kg_m2"] = [.1] * 6
        elif aenderung in ("koerperwechsel", "importserie"):
            daten = json.loads((tmp_path / "koerper.json").read_text(encoding="utf-8"))
            name = "importierter_quader"
            daten["summenkoerper"] = {name: daten["summenkoerper"]["pruefquader"]}
            (tmp_path / "koerper.json").write_text(json.dumps(daten), encoding="utf-8")
        else:
            kraefte["fluidgeschwindigkeit_m_pro_s"] = [.2, -.1, 0.]
            kraefte["fluidwinkelgeschwindigkeit_rad_pro_s"] = [.1, .1, .1]
        fenster.baum_setzen(konfig_schreiben())
        if aenderung == "importserie":
            baum.finde(fenster.baum._welt, name).sichtbar = False
            fenster._laufzeit_objekte_aktualisieren("auswahl")
            assert name not in fenster._laufzeit_koerper
            for index in range(100):
                alter_name = name
                daten = json.loads(
                    (tmp_path / "koerper.json").read_text(encoding="utf-8"))
                name = "importquader_%s" % index
                daten["summenkoerper"] = {
                    name: daten["summenkoerper"][alter_name]}
                (tmp_path / "koerper.json").write_text(
                    json.dumps(daten), encoding="utf-8")
                fenster.baum_setzen(konfig_schreiben())
                assert alter_name not in bruecke._koerper
                assert len(aufgaben) <= (2 if statisch else 1)
                assert len(fenster._statische_aufgaben_ausstehend) <= 1
        assert not fenster._kraftanzeige_snapshots
        assert not bruecke._kraefte_daten
        assert 1 <= len(aufgaben) <= 2, fenster.protokoll.toPlainText()
        anzahl_ausgefuehrt = 0
        while aufgaben:
            aufgaben.pop(0).run()
            anzahl_ausgefuehrt += 1
            assert anzahl_ausgefuehrt <= 3
        assert name in fenster._kraftanzeige_snapshots, fenster.protokoll.toPlainText()
        neu = fenster._kraftanzeige_snapshots[name]
        assert neu.generation > alt.generation
        funktion, parameter = (
            fenster._statische_arbeitsdaten[name] if statisch else
            (fenster._echtzeit_kraftfunktion.kraftmodell, fenster._echtzeit_physik))
        gewicht = next(b for b in neu.beitraege if b.name == "schwerkraft")
        assert gewicht.wrench.kraft_N[2] == pytest.approx(
            -fenster._laufzeit_koerper[name].masse * physik["physik"]["g_m_pro_s2"])
        assert funktion.linear_widerstand == pytest.approx(
            kraefte["linear_widerstand_kg_pro_s"])
        assert funktion.quadratischer_widerstand == pytest.approx(
            kraefte["quadratischer_widerstand_kg_pro_m"])
        assert funktion.added_mass_diagonal == pytest.approx(
            kraefte["added_mass_kg_und_kg_m2"])
        assert parameter.g_m_pro_s2 == physik["physik"]["g_m_pro_s2"]
        if aenderung == "rho":
            if statisch:
                assert neu.kraftpose.translation_m[2] != pytest.approx(
                    alt.kraftpose.translation_m[2])
            else:
                auftrieb_alt = next(b for b in alt.beitraege if b.name == "hydrostatik")
                auftrieb_neu = next(b for b in neu.beitraege if b.name == "hydrostatik")
                assert auftrieb_neu.wrench.kraft_N[2] == pytest.approx(
                    auftrieb_alt.wrench.kraft_N[2] * 1050 / 1000)
        elif aenderung == "fluid":
            widerstand = next(b for b in neu.beitraege if b.name == "widerstand")
            assert widerstand.wrench.kraft_N == pytest.approx((.2, -.1, 0.))
            assert widerstand.wrench.moment_Nm == pytest.approx((.1, .1, .1))
        elif aenderung == "added_mass":
            added_mass = next(b for b in neu.beitraege if b.name == "added_mass")
            if statisch:
                assert neu.vollstaendigkeit == "vollstaendig"
                assert added_mass.wrench.kraft_N == (0.,) * 3
                assert added_mass.wrench.moment_Nm == (0.,) * 3
            else:
                assert neu.vollstaendigkeit == "teilsumme"
                assert added_mass.wrench is None
        assert bruecke.kraefte_snapshot_ermitteln(name) is neu
        assert fenster._kraefte_werte._snapshots[0] is neu
        assert not fenster._echtzeit_timer.isActive()
        if aenderung in ("koerperwechsel", "importserie"):
            for cache in (fenster._laufzeit_koerper, fenster._laufzeit_schwerpunkt,
                          fenster._statische_ergebnisse, fenster._statische_arbeitsdaten,
                          bruecke._koerper, bruecke._kraftzeichner().generationen,
                          bruecke._kraftzeichner().skalen):
                assert "pruefquader" not in cache
            assert fenster._laufzeit_weltnamen == {name}
    finally:
        fenster.close()
        app.processEvents()


def test_pausierte_kraftauswertung_ist_asynchron_begrenzt_und_letzter_stand_gewinnt(
        bruecke, monkeypatch):
    import threading
    import time
    from types import SimpleNamespace
    from PySide6.QtCore import QThreadPool
    from segelphysik.core.koerper import Koerper
    from segelphysik.gui.hauptfenster import HauptFenster
    app = QApplication.instance() or QApplication([])
    pool = QThreadPool()
    gestartet, freigabe = threading.Event(), threading.Event()
    aufrufe = []
    punkte, faces = build_box(1, 1, 1)
    modell = _modell(hydrodynamik=HydrodynamikModell((
        HydrodynamikTeil("ruder", "ruder", punkte, faces, "ruder:1"),)))

    class LangsameKraft:
        def fremdkraft_setzen(self, wert):
            modell.fremdkraft_setzen(wert)

        def ruderwinkel_setzen(self, wert):
            modell.ruderwinkel_setzen(wert)

        def __call__(self, *args, **kwargs):
            aufrufe.append(threading.get_ident())
            if len(aufrufe) == 1:
                gestartet.set()
                if not freigabe.wait(5):
                    raise ValueError("Testfreigabe des Workers ausgeblieben")
            return modell(*args, **kwargs)

    fenster = HauptFenster()
    try:
        fenster._btn_echtzeit.setChecked(True)
        fenster._bruecke = bruecke
        koerper = Koerper(form=build_box(1, 1, 1), dichte=1)
        koerper.zustand = Zustand6DOF()
        fenster._laufzeit_koerper["boot"] = koerper
        fenster._echtzeit_name = "boot"
        fenster._echtzeit_zustand = koerper.zustand
        fenster._echtzeit_physik = SimpleNamespace(dt_s=.01, g_m_pro_s2=10)
        fenster._echtzeit_kraftfunktion = LangsameKraft()
        monkeypatch.setattr(QThreadPool, "globalInstance", lambda: pool)
        fenster._aktuelles_kraftbild_aktualisieren()
        assert gestartet.wait(2)
        assert not fenster._kraftanzeige_snapshots
        assert not fenster._echtzeit_timer.isActive()
        fenster._fremd_check.setChecked(True)
        for wert in range(1, 51):
            fenster.steuer_api.set_control("fremd_felder.betrag", wert)
        for key, wert in (("azimut", 35), ("elevation", 20),
                          ("x", .1), ("y", .2), ("z", .3)):
            fenster.steuer_api.set_control("fremd_felder." + key, wert)
        fenster._ruderwinkel_feld.setEnabled(True)
        fenster.steuer_api.set_control("ruderwinkel_feld", 12)
        assert len(aufrufe) == 1
        assert fenster._echtzeit_kraftauswertung_ausstehend
        assert not fenster._kraftanzeige_snapshots
        freigabe.set()
        ende = time.monotonic() + 5
        while (fenster._echtzeit_aufgabe_laeuft
               or fenster._echtzeit_kraftauswertung_ausstehend):
            app.processEvents()
            assert time.monotonic() < ende
            time.sleep(.005)
        snapshot = fenster._kraftanzeige_snapshots["boot"]
        fremd = next(b for b in snapshot.beitraege if b.name == "fremdkraft")
        assert np.linalg.norm(fremd.wrench.kraft_N) == pytest.approx(50)
        kraft, angriff = fenster._fremdkraft_aktuell()
        assert fremd.wrench.kraft_N == pytest.approx(kraft)
        assert fremd.originalangriff_m == pytest.approx(angriff)
        assert fremd.wrench.moment_Nm == pytest.approx(np.cross(angriff, kraft))
        assert modell.hydrodynamik.ruderwinkel_rad == pytest.approx(math.radians(12))
        assert len(aufrufe) == 2
        assert all(t != threading.get_ident() for t in aufrufe)
        assert fenster._echtzeit_berechnet_s == 0
        assert koerper.zustand == Zustand6DOF()
        assert not fenster._echtzeit_anzeige_verlauf
        assert bruecke.kraefte_snapshot_ermitteln("boot") is snapshot
        assert fenster._kraefte_werte._snapshots[0] is snapshot
    finally:
        freigabe.set()
        pool.waitForDone(5000)
        fenster.close()
        app.processEvents()


def test_mehrkoerper_labelauswahl_hat_globale_prioritaet(bruecke):
    bruecke._plotter.window_size = (900, 180)
    erste = _snapshot()
    zweite = KraefteAnzeigeAdapter().aus_ergebnis(
        _modell()(((0, 0, 0), (1, 0, 0, 0))), koerper_id="zweites",
        generation=1, sequenz=1, zeit_s=0, masse_kg=1, g_m_s2=10)
    bruecke._koerper["zweites"] = {
        "aktiv": False, "position": np.zeros(3), "overlay_skala": (1, .05)}
    bruecke.kraefte_snapshot_setzen(erste)
    bruecke.kraefte_snapshot_setzen(zweite)
    bruecke.render()
    for id_ in (("zweites", "hydrostatik"), ("boot", "hydrostatik")):
        bruecke.kraefte_auswahl_setzen(id_)
        zeichner = bruecke._kraftzeichner()
        assert id_ in zeichner.labels
        rechtecke = []
        for actor in zeichner.labels.values():
            groesse = [0., 0.]
            actor.GetSize(bruecke._plotter.renderer, groesse)
            x, y = actor.GetPosition()
            breite, hoehe = groesse
            assert 0 <= x < x + breite <= 900
            assert 0 <= y < y + hoehe <= 180
            for ox, oy, ob, oh in rechtecke:
                assert (x + breite <= ox or ox + ob <= x
                        or y + hoehe <= oy or oy + oh <= y)
            rechtecke.append((x, y, breite, hoehe))
    bruecke._layer.setzen(LAYER_KRAEFTE, False)
    bruecke.layer_setzen(LAYER_MOMENTE, False)
    bruecke.render()
    assert not zeichner.labels
    assert not zeichner.picklinien


@pytest.mark.parametrize("dichte,abmessungen,rho,g,zusatz", (
    (400., (.5, .4, .3), 1000., 9.81, 0.),
    (500., (.5, .4, .3), 1000., 9.81, 0.),
    (400., (.8, .6, .3), 1000., 9.81, 0.),
    (400., (.5, .4, .3), 1025., 9.81, 0.),
    (400., (.5, .4, .3), 1000., 8., 0.),
    (400., (.5, .4, .3), 1000., 9.81, 10.),
))
def test_realer_statikworker_und_anzeige_folgen_unabhaengiger_quaderbilanz(
        monkeypatch, dichte, abmessungen, rho, g, zusatz):
    from pathlib import Path
    from types import SimpleNamespace
    from segelphysik.core import konfig_lader
    from segelphysik.core.koerper import Koerper
    from segelphysik.gui.hauptfenster import _StatischeAufgabe
    ordner = Path(__file__).resolve().parents[1] / "konfigurationen"
    physik = konfig_lader.lade_physik(str(ordner))
    physik.g_m_pro_s2 = g
    monkeypatch.setattr(konfig_lader, "lade_physik", lambda _ordner: physik)
    koerper = Koerper(form=build_box(*abmessungen), dichte=dichte)
    antworten = []
    signale = SimpleNamespace(
        abgeschlossen=SimpleNamespace(emit=lambda *a: antworten.append(a)),
        fortschritt=SimpleNamespace(emit=lambda *_a: None))
    aufgabe = _StatischeAufgabe(
        1, "pruefquader", koerper, str(ordner), rho, signale,
        fremdkraft=None if zusatz == 0 else ((0, 0, zusatz), (0, 0, 0)))
    aufgabe.run()
    assert len(antworten) == 1
    _, _, resultat, _, fehler = antworten[0]
    assert fehler is None
    laenge, breite, hoehe = abmessungen
    z_soll = hoehe / 2 - (koerper.masse * g - zusatz) / (rho * g * laenge * breite)
    assert resultat["z"] == pytest.approx(z_soll, abs=1e-9)
    assert resultat["phi"] == pytest.approx(0, abs=1e-9)
    erg = resultat["kraft_ergebnis"]
    snapshot = KraefteAnzeigeAdapter().aus_ergebnis(
        erg, koerper_id="quader", generation=1, sequenz=1, zeit_s=0,
        masse_kg=koerper.masse, g_m_s2=g)
    beitraege = {b.name: b.wrench for b in snapshot.beitraege}
    assert beitraege["schwerkraft"].kraft_N == pytest.approx(
        (0, 0, -koerper.masse * g), abs=1e-9)
    assert beitraege["hydrostatik"].kraft_N == pytest.approx(
        (0, 0, koerper.masse * g - zusatz), abs=1e-8)
    if zusatz:
        assert beitraege["fremdkraft"].kraft_N == (0, 0, zusatz)
    assert snapshot.bilanz.wrench.kraft_N == pytest.approx((0, 0, 0), abs=1e-8)


@pytest.mark.slow
@pytest.mark.parametrize("modellname,konvergiert", [
    ("folkeboot", True),
    pytest.param("yacht1", False, marks=pytest.mark.diagnostic),
])
@pytest.mark.parametrize("zusatzmodelle", (False, True))
def test_reale_modelle_zeigen_die_tatsaechlichen_statischen_und_stationaeren_residuen(
        modellname, konvergiert, zusatzmodelle):
    from segelphysik.core.auftrieb import baue_kraftfunktion
    from segelphysik.core.stationaer_hydrodynamik import (
        StationaerSolverFehler, loese_stationaer,
    )
    from segelphysik.core.statisch_robust import loese_robust
    from segelphysik.gui.hauptfenster import _stationaere_kraftlage
    from werkzeuge.migration_szenarien import koerper_laden
    konfig, physik, koerper = koerper_laden(modellname)
    g = physik.g_m_pro_s2
    modell = Kraftmodell(
        baue_kraftfunktion(koerper, rho_w=konfig.wasser_dichte(), g=g,
                          pfad="exakt_union"),
        masse=koerper.masse, g=g,
        linear_widerstand=[.01 if zusatzmodelle else 0.] * 6,
        quadratischer_widerstand=[.001 if zusatzmodelle else 0.] * 6,
        added_mass_diagonal=[.1 if zusatzmodelle else 0.] * 6,
        hydrodynamik=HydrodynamikModell.aus_koerper(
            koerper, rho_kg_m3=konfig.wasser_dichte()))
    loesung = loese_robust(modell, koerper.masse, g=g)
    ergebnis = modell((loesung["z"], loesung["phi"], 0)).mit_beschleunigung(
        (0.,) * 6)
    snapshot = KraefteAnzeigeAdapter().aus_ergebnis(
        ergebnis, koerper_id=modellname, generation=1, sequenz=1,
        zeit_s=0, masse_kg=koerper.masse, g_m_s2=g)
    assert snapshot.bilanz.wrench.kraft_N[2] == pytest.approx(
        loesung["restkraft"], abs=1e-8, rel=1e-9)
    assert snapshot.bilanz.wrench.moment_Nm[0] == pytest.approx(
        loesung["restmoment"], abs=1e-8, rel=1e-9)
    testkraft = .01 * koerper.masse * g
    modell.fremdkraft_setzen(((testkraft, 0, 0), (0, 0, 0)))
    laenge = np.ptp(np.concatenate(
        [mesh[0] for mesh in koerper.blatt_meshes]), axis=0).max()
    parameter = dict(charakteristische_kraft_N=testkraft,
        charakteristische_laenge_m=laenge, referenzgeschwindigkeit_m_s=1,
        start=np.array((1, loesung["z"], 0, 0, loesung["phi"], 0)))
    if zusatzmodelle:
        try:
            stationaer = loese_stationaer(modell, **parameter)
        except StationaerSolverFehler as fehler:
            assert "Residuum" in str(fehler)
            stufen = fehler.stufen
        else:
            assert stationaer.konvergiert
            stufen = stationaer.stufen
    elif konvergiert:
        stationaer = loese_stationaer(modell, **parameter)
        assert stationaer.konvergiert
        stufen = stationaer.stufen
    else:
        with pytest.raises(StationaerSolverFehler, match="Residuum") as fehler:
            loese_stationaer(modell, **parameter)
        stufen = fehler.value.stufen
    assert stufen
    for sequenz, stufe in enumerate(stufen, 2):
        pose, v, omega, _ = _stationaere_kraftlage(stufe)
        ergebnis = modell(pose, v=v, omega=omega).mit_beschleunigung((0.,) * 6)
        snapshot = KraefteAnzeigeAdapter().aus_ergebnis(
            ergebnis, koerper_id=modellname, generation=1, sequenz=sequenz,
            zeit_s=0, masse_kg=koerper.masse, g_m_s2=g)
        assert snapshot.bilanz.wrench.kraft_N == pytest.approx(
            stufe.restkraft_N, abs=1e-8, rel=1e-9)
        assert snapshot.bilanz.wrench.moment_Nm == pytest.approx(
            stufe.restmoment_Nm, abs=1e-8, rel=1e-9)
        assert snapshot.vollstaendigkeit == "vollstaendig"
        if zusatzmodelle:
            beitraege = {b.name: b for b in snapshot.beitraege}
            assert "widerstand" in beitraege
            added = beitraege["added_mass"]
            assert added.wrench.kraft_N == pytest.approx((0.,) * 3)
            assert added.wrench.moment_Nm == pytest.approx((0.,) * 3)
            assert snapshot.modellhinweise


def test_weltursprung_beruecksichtigt_statischen_szenenversatz(bruecke):
    from segelphysik.core.kraefte_anzeige import anzeige_wrench
    from segelphysik.gui.kraefte_werte import KraefteWerteModell
    snapshot = replace(_snapshot(), szenenversatz_m=(5, 6, 0))
    beitrag = next(b for b in snapshot.beitraege if b.name == "hydrostatik")
    wrench = anzeige_wrench(snapshot, beitrag, weltursprung=True)
    assert wrench.bezugspunkt_m == (-5, -6, 0)
    assert wrench.moment_Nm == pytest.approx((62, -50, 0))
    modell = KraefteWerteModell()
    modell.ansicht_setzen(weltursprung=True)
    wert = modell.anzeigebeitrag(snapshot, beitrag)
    assert wert.wrench.bezugspunkt_m == (0, 0, 0)
    assert wert.originalangriff_m == (5, 6.2, 0)
    assert wert.wrench.moment_Nm == wrench.moment_Nm
    assert beitrag.originalangriff_m == (0, .2, 0)
    assert snapshot.kraftpose.translation_m == (0, 0, 0)
    modell.ansicht_setzen(weltursprung=True, koerperframe=True)
    wert = modell.anzeigebeitrag(snapshot, beitrag)
    assert wert.wrench.bezugspunkt_m == (-5, -6, 0)
    assert wert.wrench.moment_Nm == wrench.moment_Nm


@pytest.mark.parametrize("wertefenster_offen", (False, True))
def test_langsame_gui_blockiert_worker_nicht_und_haelt_auftragszahl_begrenzt(
        bruecke, monkeypatch, wertefenster_offen):
    import threading
    import time
    from types import SimpleNamespace
    from segelphysik.core.koerper import Koerper
    from segelphysik.gui import hauptfenster as hf
    app = QApplication.instance() or QApplication([])
    fenster = hf.HauptFenster()
    pool = hf.QThreadPool()
    gestartet = []
    def starten(aufgabe):
        gestartet.append(aufgabe)
        pool.start(aufgabe)
    monkeypatch.setattr(
        hf.QThreadPool, "globalInstance",
        lambda: SimpleNamespace(start=starten, maxThreadCount=lambda: 2))
    gui_thread = threading.get_ident()
    pose_threads = []
    monkeypatch.setattr(
        fenster, "_echtzeit_pose_anzeigen",
        lambda *_a, **_kw: pose_threads.append(threading.get_ident()) or True)
    monkeypatch.setattr(fenster, "_navigationsanzeigen_aktualisieren", lambda: None)
    try:
        fenster.show()
        if wertefenster_offen:
            fenster._kraefte_werte.oeffnen()
        else:
            fenster._kraefte_werte.close()
        app.processEvents()
        assert fenster._kraefte_werte.isVisible() == wertefenster_offen
        taktintervall = fenster._echtzeit_timer.interval()
        koerper = Koerper(form=build_box(1, 1, 1), dichte=1)
        koerper.zustand = Zustand6DOF()
        fenster._bruecke = bruecke
        fenster._btn_echtzeit.setChecked(True)
        fenster._laufzeit_koerper["boot"] = koerper
        fenster._echtzeit_name = "boot"
        fenster._echtzeit_zustand = koerper.zustand
        fenster._echtzeit_kraftfunktion = _modell()
        fenster._echtzeit_physik = SimpleNamespace(dt_s=.001, g_m_pro_s2=10)
        fenster._echtzeit_akkumulator = .005
        fenster._echtzeit_angefordert_s = .005
        fenster._echtzeit_letzte_wandzeit = time.perf_counter()
        fenster._echtzeit_takt()
        # Keine GUI-Ereignisse: Die Workerantwort bleibt absichtlich ausstehend.
        assert pool.waitForDone(5000)
        assert pool.activeThreadCount() == 0
        assert fenster._echtzeit_aufgabe_laeuft
        assert not fenster._kraftanzeige_snapshots
        for _ in range(50):
            fenster._echtzeit_takt()
        assert len(gestartet) == 1
        assert not pose_threads
        app.processEvents()
        assert not fenster._echtzeit_aufgabe_laeuft
        assert pose_threads == [gui_thread]
        snapshot = fenster._kraftanzeige_snapshots["boot"]
        assert bruecke.kraefte_snapshot_ermitteln("boot") is snapshot
        assert snapshot.zeit_s == pytest.approx(
            max(0., fenster._echtzeit_berechnet_s - .001))
        assert fenster._kraefte_werte.modell.rowCount() == 1
        assert fenster._kraefte_werte.isVisible() == wertefenster_offen
        assert fenster._echtzeit_timer.interval() == taktintervall
    finally:
        assert pool.waitForDone(5000)
        fenster.close()
        app.processEvents()
