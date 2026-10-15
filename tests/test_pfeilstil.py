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


def test_farbe_wird_geprueft(tmp_path):
    e = Einstellungen.laden(str(tmp_path / "s.json"))
    e.setzen("pfeil_f_g", "farbe", "#112233")
    e.setzen("pfeil_f_g", "farbe", "")
    with pytest.raises(ValueError):
        e.setzen("pfeil_f_g", "farbe", "rot")


@pytest.mark.parametrize("maske", range(32))
def test_alle_layerkombinationen_zeichnen_ohne_fehler(maske):
    from types import SimpleNamespace
    from segelphysik import grafik_bruecke as gb
    from segelphysik.core.auftrieb import Auftriebsergebnis, Vektor
    from segelphysik.core.kraftmodell import KraftErgebnis

    gezeichnet = {}
    b = gb.GrafikBruecke()
    b._vg_unmoeglich = True
    b._plotter = SimpleNamespace(remove_actor=lambda *a, **k: None)
    gb_mesh = gb._mesh_actor_setzen
    gb._mesh_actor_setzen = (
        lambda plotter, store, n, mesh, **kw: (
            store.__setitem__(n, object()), gezeichnet.__setitem__(n, mesh)))
    try:
        hydro = Auftriebsergebnis(1.0, (0.3, 0.0, 0.0), (0.0, 0.0, 1000.0),
                                  (0.0, 0.0, 0.0))
        erg = KraftErgebnis(hydro, Vektor((0.0, 50.0, 1000.0)),
                            Vektor((0.0, 0.0, 0.0)), (0.0,) * 6)
        b._koerper["boot"] = {"aktiv": True, "position": np.zeros(3),
                              "overlay_skala": (1.0, 0.05)}
        b.kraefte_daten_setzen("boot", erg, 100.0, 9.81, 0.01,
                               fremd=((0.0, 50.0, 0.0), (1.0, 0.0, 0.0)))
        layer = (gb.LAYER_KRAEFTE, gb.LAYER_FREMDKRAFT, gb.LAYER_MOMENTE,
                 gb.LAYER_SCHWERPUNKT, gb.LAYER_HAUPTACHSEN)
        for i, l in enumerate(layer):
            b._layer.setzen(l, bool(maske >> i & 1))
        b._kraefte_actors("boot")
    finally:
        gb._mesh_actor_setzen = gb_mesh
    assert ("kraefte_boot_fremd" in gezeichnet) == bool(maske & 2)
    assert ("kraefte_boot_fg" in gezeichnet) == bool(maske & 1)
    assert ("kraefte_boot_auftriebsp" in gezeichnet) == bool(maske & 8)
    assert ("kraefte_boot_moment_y" in gezeichnet) == bool(maske & 4)
