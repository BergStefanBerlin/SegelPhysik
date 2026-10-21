import numpy as np
import pytest

from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.modell_lader import ModellGelenk


def test_snapshot_koerperkontext_wird_bei_pose_update_wiederverwendet():
    koerper = Koerper(form=build_box(1.0, 1.0, 1.0), dichte=500.0)

    vorher = koerper.snapshot()
    kontext = koerper._snapshot_native_context
    koerper.position = np.array((0.2, 0.0, 0.0))
    nachher = koerper.snapshot()

    assert koerper._snapshot_native_context is kontext
    assert nachher.version == koerper._version
    assert nachher.zustand.position == (0.2, 0.0, 0.0)
    assert nachher.blatt_meshes[0][0] is vorher.blatt_meshes[0][0]
    assert not nachher.blatt_meshes[0][0].flags.writeable


def test_snapshot_kontext_wird_bei_meshaenderung_invalidiert():
    koerper = Koerper(form=build_box(1.0, 1.0, 1.0), dichte=500.0)

    vorher = koerper.snapshot()
    kontext = koerper._snapshot_native_context
    koerper.punkte[0, 0] += 0.01
    nachher = koerper.snapshot()

    assert koerper._snapshot_native_context is not kontext
    assert nachher.blatt_meshes[0][0] is not vorher.blatt_meshes[0][0]


def test_snapshot_kontext_wird_bei_gelenkaenderung_invalidiert():
    kind = Koerper(
        form=build_box(1.0, 1.0, 1.0),
        dichte=500.0,
        knoten_id="ruder",
        gelenkdefinition=ModellGelenk(
            "rumpf", (0.0, 1.0, 0.0), 0.0),
    )
    koerper = Koerper(teile=[(kind, (np.eye(3), np.zeros(3)))])

    vorher = koerper.snapshot()
    kontext = koerper._snapshot_native_context
    koerper.gelenkwinkel_setzen("ruder", 0.25)
    nachher = koerper.snapshot()

    assert koerper._snapshot_native_context is not kontext
    assert nachher.gelenkzustaende[0].winkel_rad == 0.25
    assert nachher.blatt_meshes[0][0] is not vorher.blatt_meshes[0][0]


@pytest.mark.gui
def test_wasserlinienschnitt_cache_nutzt_gleiche_pose_und_invalidiert(
        monkeypatch):
    import pyvista as pv
    from segelphysik import grafik_bruecke as gb

    punkte, dreiecke = build_box(1.0, 1.0, 1.0)
    cache = {}
    schnitte = []
    schnitt_alt = gb.ws.schneide_am_wasser

    def schnitt_zaehlen(*args, **kwargs):
        schnitte.append(1)
        return schnitt_alt(*args, **kwargs)

    monkeypatch.setattr(gb.ws, "schneide_am_wasser", schnitt_zaehlen)
    erster = gb._wasserlinien_actors(pv, cache, punkte, dreiecke)
    erneut = gb._wasserlinien_actors(pv, cache, punkte.copy(), dreiecke)

    assert len(schnitte) == 1
    assert erneut is erster

    bewegte_punkte = punkte + np.array((0.0, 0.0, 0.1))
    bewegt = gb._wasserlinien_actors(
        pv, cache, bewegte_punkte, dreiecke)
    assert len(schnitte) == 2
    assert bewegt is not erster


@pytest.mark.gui
def test_gelenkwinkelereignisse_werden_zusammengefasst(qapp, monkeypatch):
    from segelphysik.grafik_bruecke import GrafikBruecke

    ruder = Koerper(
        form=build_box(0.2, 0.2, 0.2),
        dichte=500.0,
        knoten_id="ruder",
        gelenkdefinition=ModellGelenk(
            "rumpf", (0.0, 1.0, 0.0), 0.0),
    )
    koerper = Koerper(teile=[(ruder, (np.eye(3), np.zeros(3)))])
    bruecke = GrafikBruecke()
    bruecke._plotter = object()
    bruecke._koerper["test"] = {"koerper": koerper, "gruppen": []}
    aktualisierungen = []
    renders = []
    monkeypatch.setattr(
        "segelphysik.grafik_bruecke._farbgruppen",
        lambda _koerper: aktualisierungen.append("geometrie") or [])
    monkeypatch.setattr(
        "segelphysik.grafik_bruecke._benetzte_geometrie",
        lambda _koerper: object())
    monkeypatch.setattr(
        bruecke, "_statisch_anwenden",
        lambda *_args: aktualisierungen.append("darstellung"))
    monkeypatch.setattr(bruecke, "render", lambda: renders.append(True))

    for wert in (0.1, 0.2, 0.3, 0.4):
        assert bruecke.gelenkwinkel_setzen("test", "ruder", wert)

    assert ruder.gelenkwinkel_rad == 0.4
    assert aktualisierungen == []
    bruecke._gelenk_update_timer.stop()
    bruecke._gelenk_updates_ausfuehren()

    assert aktualisierungen == ["geometrie", "darstellung"]
    assert renders == [True]
