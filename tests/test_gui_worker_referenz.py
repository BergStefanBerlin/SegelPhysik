"""Gui worker referenz: bestehende Referenzvertraege."""
from types import SimpleNamespace
import pytest
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box

pytestmark = pytest.mark.integration


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
