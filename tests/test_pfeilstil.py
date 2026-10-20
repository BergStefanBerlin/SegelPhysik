"""Kraftpfeildarstellung: Stil, feste Dicke, Strichelung, Einstellungen."""
import json

import numpy as np
import pytest

from segelphysik.core import kraefte_bild as kb
from segelphysik.core import pfeilstil as ps
from segelphysik.core.einstellungen import Einstellungen, VORLAGE


def test_paarfarben_und_vererbung():
    stil = ps.Stil()
    blau = stil.paarfarbe("gewicht_auftrieb")
    assert stil.pfeil("f_g", 5.0)["farbe"] == blau
    assert stil.pfeil("m_x", 5.0)["farbe"] == blau
    assert stil.pfeil("fremd", 5.0)["farbe"] == stil.paarfarbe("fremdkraft")
    assert stil.paarfarbe("fremdkraft") == "#d73027"
    assert stil.pfeil("f_a", 5.0)["gestrichelt"]
    assert not stil.pfeil("f_g", 5.0)["gestrichelt"]


def test_einzelfarbe_ueberschreibt_paarfarbe():
    def bereich(name):
        if name == "pfeil_f_g":
            return {"farbe": "#00ff00"}
        return ps.standard_bereiche()[name]
    assert ps.Stil(bereich).pfeil("f_g", 5.0)["farbe"] == "#00ff00"


def test_dicke_ist_laengenunabhaengig():
    stil = ps.Stil().pfeil("f_g", 4.0)
    a = kb.pfeil_fest((0, 0, 0), (0, 0, -1.0), stil["durchmesser"],
                      stil["kopf_durchmesser"], stil["kopf_laenge"], 0.0)
    b = kb.pfeil_fest((0, 0, 0), (0, 0, -3.0), stil["durchmesser"],
                      stil["kopf_durchmesser"], stil["kopf_laenge"], 0.0)
    assert a["schaft_radius"] == b["schaft_radius"]
    assert a["kopf_radius"] == pytest.approx(b["kopf_radius"])
    assert b["laenge"] > a["laenge"]


def test_mindestlaenge_bei_kleiner_kraft():
    p = kb.pfeil_fest((0, 0, 0), (0, 1e-6, 0), 0.01, 0.025, 0.05, 0.1)
    assert p["laenge"] == pytest.approx(0.1)
    assert p["richtung"][1] > 0


def test_strichelung_hat_luecken():
    punkte, zellen = kb.strich_linien([(0, 0, 0), (1, 0, 0)], 0.1, 0.1)
    xs = np.unique(np.round(punkte[:, 0], 6))
    assert xs.min() == pytest.approx(0.0)
    assert xs.max() <= 1.0 + 1e-9
    assert not np.any((punkte[:, 0] > 0.105) & (punkte[:, 0] < 0.195))


def test_paarmoment_um_schwerpunkt():
    from types import SimpleNamespace
    erg = SimpleNamespace(K=SimpleNamespace(as_array=lambda: np.array([1.0, 0, 0])),
                          F_A=SimpleNamespace(as_array=lambda: np.array([0, 0, 10.0])))
    assert np.allclose(kb.paar_moment_auftrieb(erg, np.zeros(3)), (0, -10, 0))
    assert np.allclose(kb.paar_moment_kraft((0, 0, 2.0), (0, 5.0, 0), (0, 0, 0)),
                       (-10, 0, 0))


def test_alle_pfeile_haben_bereich_in_vorlage():
    for p in ps.PFEILE:
        assert ps.pfeil_bereich(p[0]) in VORLAGE
    for pid, _t, _f in ps.PAARE:
        assert "farbe_" + pid in VORLAGE[ps.BEREICH_PAARE]


def test_alte_datei_1_0_wird_mit_neuen_bereichen_aufgefuellt(tmp_path):
    pfad = tmp_path / "settings.json"
    pfad.write_text(json.dumps({"schema_version": "1.0",
                                "statisch": {"max_iterationen": 33}}),
                    encoding="utf-8")
    e = Einstellungen.laden(str(pfad))
    assert e.get("statisch", "max_iterationen") == 33
    assert e.get(ps.BEREICH_ALLGEMEIN, "dicke") == 0.5
    assert ps.Stil(e.bereich).paarfarbe("fremdkraft") == "#d73027"


def test_historische_skalen_und_groessen_haben_definierte_pixelwirkung(tmp_path):
    ein = Einstellungen(str(tmp_path / "settings.json"))
    ein.setzen(ps.BEREICH_ALLGEMEIN, "kraftskala", .1)
    ein.setzen(ps.BEREICH_ALLGEMEIN, "momentskala", .15)
    ein.setzen(ps.BEREICH_ALLGEMEIN, "mindestlaenge", 6)
    ein.setzen("pfeil_f_g", "skala", 2)
    ein.setzen("pfeil_f_g", "dicke", 1)
    ein.setzen("pfeil_f_g", "kopf", 1.5)
    stil = ps.Stil(ein.bereich)
    pixel = stil.bildschirmstil(stil.pfeil("f_g", 10), 10, .01)
    assert pixel["kraftfaktor"] == pytest.approx(4)
    assert pixel["momentfaktor"] == pytest.approx(6)
    assert pixel["kleinwert_px"] == pytest.approx(3)
    assert pixel["durchmesser"] == pytest.approx(.06)
    assert pixel["kopf_laenge"] == pytest.approx(.15)
    assert pixel["kopf_durchmesser"] == pytest.approx(.105)


def test_historische_momentkomponenten_und_quellenfarbe_bleiben_wirksam(tmp_path):
    from types import SimpleNamespace
    ein = Einstellungen(str(tmp_path / "settings.json"))
    ein.setzen("pfeil_m_x", "sichtbar", True)
    ein.setzen("pfeil_m_x", "farbe", "#123456")
    beitrag = SimpleNamespace(
        name="hydrostatik", herkunft="Einzelbeitrag", gruppe="gewicht_auftrieb")
    stil = ps.Stil(ein.bereich)
    komponenten = stil.momentkomponenten(beitrag, 1)
    assert [an for an, _ in komponenten] == [True, False, False]
    assert komponenten[0][1]["farbe"] == "#123456"
    ein.setzen("kraefteanzeige", "komponenten", True)
    assert all(an for an, _ in stil.momentkomponenten(beitrag, 1))


@pytest.mark.parametrize("pfeil_id", [p[0] for p in ps.PFEILE])
def test_alle_historischen_pfeilfelder_ueberstehen_migration_und_neustart(
        tmp_path, pfeil_id):
    bereich = ps.pfeil_bereich(pfeil_id)
    allgemein = {
        "vordergrund": True, "dicke": .75, "kopf_durchmesser": 3.,
        "kopf_laenge": 6., "kraftskala": .12, "momentskala": .09,
        "mindestlaenge": 3.5, "strich_laenge": 4., "strich_luecke": 3.,
    }
    individuell = {
        "sichtbar": False, "farbe": "#123456", "dicke": .8, "kopf": 1.4,
        "gestrichelt": True, "skala": 1.3, "deckkraft": .6,
        "vordergrund": False,
    }
    pfad = tmp_path / "historisch.json"
    pfad.write_text(json.dumps({
        "schema_version": "1.0", ps.BEREICH_ALLGEMEIN: allgemein,
        bereich: individuell}), encoding="utf-8")
    ein = Einstellungen.laden(str(pfad))
    for gruppe, werte in ((ps.BEREICH_ALLGEMEIN, allgemein),
                          (bereich, individuell)):
        assert all(ein.get(gruppe, key) == wert for key, wert in werte.items())
    stil = ps.Stil(ein.bereich)
    wirkung = stil.pfeil(pfeil_id, 10.)
    pixel = stil.bildschirmstil(wirkung, 10., .01)
    assert wirkung["farbe"] == "#123456"
    assert wirkung["deckkraft"] == .6
    assert not wirkung["vordergrund"]
    assert not wirkung["sichtbar"]
    assert wirkung["gestrichelt"]
    assert pixel["durchmesser"] == pytest.approx(3 * (.8 / .5) * .01)
    assert pixel["kopf_laenge"] == pytest.approx(10 * (6 * 1.4 / 5) * .01)
    assert pixel["kopf_durchmesser"] == pytest.approx(7 * (3 * 1.4 / 2.5) * .01)
    assert pixel["kraftfaktor"] == pytest.approx(1.3 * .12 / .05)
    assert pixel["momentfaktor"] == pytest.approx(1.3 * .09 / .05)
    assert pixel["kleinwert_px"] == pytest.approx(3.5 / 2)
    assert pixel["strich"] == pytest.approx(8 * .01 * 4 / 3)
    assert pixel["luecke"] == pytest.approx(5 * .01 * 3 / 2)
    ein.speichern()
    neustart = Einstellungen.laden(str(pfad))
    neu = ps.Stil(neustart.bereich)
    assert neu.bildschirmstil(neu.pfeil(pfeil_id, 10.), 10., .01) == pixel


def test_farbe_wird_geprueft(tmp_path):
    e = Einstellungen.laden(str(tmp_path / "s.json"))
    e.setzen("pfeil_f_g", "farbe", "#112233")
    e.setzen("pfeil_f_g", "farbe", "")
    with pytest.raises(ValueError):
        e.setzen("pfeil_f_g", "farbe", "rot")


@pytest.mark.parametrize("maske", range(32))
def test_alle_layerkombinationen_zeichnen_ohne_fehler(maske):
    from types import SimpleNamespace
    from vtkmodules.vtkRenderingCore import vtkCamera
    from segelphysik import grafik_bruecke as gb
    from segelphysik.core.auftrieb import Auftriebsergebnis, Vektor
    from segelphysik.core.kraefte_darstellung import KameraAbbildung

    gezeichnet = {}
    b = gb.GrafikBruecke()
    bereiche = ps.standard_bereiche()
    bereiche[ps.BEREICH_ALLGEMEIN]["vordergrund"] = False
    b._stil = ps.Stil(bereiche.__getitem__)
    kamera = vtkCamera()
    b._plotter = SimpleNamespace(
        remove_actor=lambda *a, **k: None,
        renderer=SimpleNamespace(GetActiveCamera=lambda: kamera))
    gb_mesh = gb._mesh_actor_setzen
    class Actor:
        def SetPosition(self, *position):
            self.position = position

        def SetVisibility(self, sichtbar):
            self.sichtbar = sichtbar

        def SetUserMatrix(self, matrix):
            self.matrix = matrix

    gb._mesh_actor_setzen = (
        lambda plotter, store, n, mesh, **kw: (
            store.__setitem__(n, Actor()), gezeichnet.__setitem__(n, mesh)))
    try:
        hydro = Auftriebsergebnis(1.0, (0.3, 0.0, 0.0), (0.0, 0.0, 1000.0),
                                  (0.0, 0.0, 0.0))
        erg = hydro
        b._koerper["boot"] = {"aktiv": True, "position": np.zeros(3),
                              "overlay_skala": (1.0, 0.05)}
        b.kraefte_daten_setzen("boot", erg, 100.0, 9.81, 0.01,
                               fremd=((0.0, 50.0, 0.0), (1.0, 0.0, 0.0)))
        b._kraftzeichner().kamera = lambda: KameraAbbildung(
            (0, -5, 2), (0, 0, 0), (1000, 800), True, 2, 30)
        b._kraftzeichner()._labels = lambda *_args: None
        layer = (gb.LAYER_KRAEFTE, gb.LAYER_FREMDKRAFT, gb.LAYER_MOMENTE,
                 gb.LAYER_SCHWERPUNKT, gb.LAYER_HAUPTACHSEN)
        for i, l in enumerate(layer):
            b._layer.setzen(l, bool(maske >> i & 1))
        b._kraefte_actors("boot")
    finally:
        gb._mesh_actor_setzen = gb_mesh
    assert ("kraefte_('boot', 'fremdkraft')_F" in gezeichnet) == bool(maske & 2)
    assert ("kraefte_('boot', 'schwerkraft')_F" in gezeichnet) == bool(maske & 1)
    assert ("kraefte_('boot', 'hydrostatik')_angriff" in gezeichnet) == bool(maske & 8)
    assert any(n.endswith("_M") for n in gezeichnet) == bool(maske & 4)
