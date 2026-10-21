"""Grafik geometrie referenz: bestehende Referenzvertraege."""
import numpy as np
import pytest
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box

pytestmark = [pytest.mark.gui, pytest.mark.integration]


def test_polydaten_hilfsvertrag_und_rueckextraktion():
    import pyvista as pv
    from segelphysik.grafik_bruecke import _gesichter, _polydaten

    punkte, dreiecke = build_box(1., 1., 1.)
    daten = _polydaten(pv, punkte, dreiecke)
    np.testing.assert_array_equal(daten.points, punkte)
    np.testing.assert_array_equal(_gesichter(daten), dreiecke)


def test_echte_actorgruppen_und_schwerpunkt_ohne_neue_optik():
    import pyvista as pv
    from segelphysik.grafik_bruecke import GrafikBruecke
    from werkzeuge.migration_szenarien import aktoren_snapshot

    bruecke = GrafikBruecke()
    plotter = pv.Plotter(off_screen=True)
    bruecke._plotter = plotter
    from segelphysik.core.pfeilstil import BEREICH_ALLGEMEIN, Stil, standard_bereiche
    bereiche = standard_bereiche()
    bereiche[BEREICH_ALLGEMEIN]["vordergrund"] = False
    bruecke._stil = Stil(bereiche.__getitem__)
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
