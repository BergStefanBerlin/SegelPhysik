"""SegelPhysik V3 - kinematische Demo.

Grafik: die FERTIGE v0.4-Render-Pipeline (render/vista.py, unveraendert),
angefluensert ueber grafik_bruecke.GrafikBruecke. Keine Physik-Module.
Start: python -m segelphysik.demo_app
Tasten: Leertaste Pause/Play | r Reset | 1/2/3 Kegel/Quader/Pyramide
        +/- (auch Pfeile) Wiedergabefaktor | q Beenden
"""
from __future__ import annotations
import time

from .core import bewegung as kin
from .grafik_bruecke import GrafikBruecke
from .steuerung import ControlPanel

TYPEN_DEUTSCH = {"cone": "Kegel", "box": "Quader", "pyramid": "Pyramide"}


def _starte_takt(plotter, funktion, intervall_ms=16):
    """Animationstakt versionsunabhaengig verbinden
    (Plotter.add_callback existiert in neueren PyVista-Versionen nicht mehr;
    dann VTK-Timer des Interactors)."""
    if hasattr(plotter, "add_callback"):
        plotter.add_callback(funktion, interval=intervall_ms)
        return
    iren = plotter.iren

    def vtk_rueckruf(objekt, ereignis):
        funktion()

    iren.add_observer("TimerEvent", vtk_rueckruf)
    interaktor = getattr(iren, "interactor", iren)
    for methode in ("CreateRepeatingTimer", "create_repeating_timer"):
        erzeuger = getattr(interaktor, methode, None)
        if erzeuger is not None:
            erzeuger(intervall_ms)
            return
    raise RuntimeError("Kein Timer-Mechanismus gefunden.")


def main():
    bruecke = GrafikBruecke()
    plotter = bruecke.fenster_bauen()

    panel = ControlPanel()
    szene = kin.Szene.standard(panel.body_type)
    uhr = kin.Uhr(wiedergabe=panel.wiedergabe)
    zustand = {"letzte_zeit": time.perf_counter()}

    def spawne(typ):
        szene_neu = kin.Szene.standard(typ)
        d = szene_neu.koerper[0]
        uhr.ruecksetzen()
        bruecke.koerper_setzen(d["type"], d["dims"], d["axis"], d["phase"])
        zustand["letzte_zeit"] = time.perf_counter()

    def taktschlag():
        jetzt = time.perf_counter()
        real_dt = jetzt - zustand["letzte_zeit"]
        zustand["letzte_zeit"] = jetzt
        if panel.laeuft:
            uhr.weiter_real(real_dt)
        bruecke.aktualisieren(uhr.t)
        phi = kin.phi_grad(uhr.t)
        pause = "" if panel.laeuft else "   [PAUSE]"
        bruecke.status(
            "Koerpertyp: %s   phi(t): %8.2f Grad   Umdrehung: %d   "
            "Animationszeit: %7.2f s   Wiedergabe: %.2fx%s"
            % (TYPEN_DEUTSCH.get(panel.body_type, panel.body_type),
               phi, int(phi // 360), uhr.t, panel.wiedergabe, pause))

    panel.verdrahte(plotter, spawne)
    spawne(panel.body_type)
    plotter.add_key_event("space", lambda: panel.umschalten())
    plotter.add_key_event("r", uhr.ruecksetzen)
    for taste in ("plus", "up", "kp_add"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(2.0))
    for taste in ("minus", "down", "kp_subtract"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(0.5))
    _starte_takt(plotter, taktschlag, 16)
    plotter.show()


if __name__ == "__main__":
    main()
