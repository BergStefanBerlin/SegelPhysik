"""SegelPhysik V3 - kinematische Demo (alle drei Koerper, Eigenrotation).

Animation ueber die dokumentierte interactive_update-Schleife
(funktionsunabhaengig von PyVista-Timer-APIs -> Rotation laeuft immer).
Start: python -m segelphysik.demo_app
Tasten: 1/2/3 Koerper ein/aus | 4 Boot | a alle an | Leertaste Pause | r Reset
        +/- (auch Pfeile) Wiedergabefaktor | q Beenden
"""
from __future__ import annotations
import time

from .core import bewegung as kin
from .core import fabriken
from .core.konfig_lader import lade_konfiguration
from .grafik_bruecke import GrafikBruecke, FARBE_UNTEN, FARBE_OBEN
from .steuerung import ControlPanel

TYPEN = (("kegel", "cone"), ("quader", "box"), ("pyramide", "pyramid"))
TYPEN_DEUTSCH = {"cone": "Kegel", "box": "Quader", "pyramid": "Pyramide"}
POSITIONEN = {"cone": (-2.5, 0.0, 0.0), "box": (0.0, 0.0, 0.0),
              "pyramid": (2.5, 0.0, 0.0)}   # Plan M3: nebeneinander


def _phi_grad(t):
    if hasattr(kin, "phi_grad"):
        return kin.phi_grad(t)
    return kin.phi_deg(t)


def main():
    konfig = lade_konfiguration()   # Spec J: einzige Quelle, kein stiller Fallback
    bruecke = GrafikBruecke()
    plotter = bruecke.fenster_bauen()

    panel = ControlPanel()
    uhr = kin.Uhr(wiedergabe=panel.wiedergabe)
    zustand = {"letzte_zeit": time.perf_counter()}
    sichtbar = {}

    def spawne(name, typ):
        szene = kin.Szene.standard(typ)
        d = szene.koerper[0]
        bauer = {"cone": fabriken.baue_kegel, "box": fabriken.baue_quader,
                 "pyramid": fabriken.baue_pyramide}[typ]
        k = bauer(konfig, **d["dims"])
        bruecke.koerper_objekt_setzen(name, k, POSITIONEN[typ],
                                      achse=d["axis"], phase=d["phase"],
                                      farbe_unten=FARBE_UNTEN,
                                      farbe_oben=FARBE_OBEN)
        sichtbar[name] = True

    def umschalten(index):
        name, typ = TYPEN[index]
        if name not in sichtbar:
            spawne(name, typ)
        else:
            sichtbar[name] = not sichtbar[name]
            bruecke.sichtbar_setzen(name, sichtbar[name])

    def taktschlag():
        jetzt = time.perf_counter()
        real_dt = jetzt - zustand["letzte_zeit"]
        zustand["letzte_zeit"] = jetzt
        if panel.laeuft:
            uhr.weiter_real(real_dt)
        bruecke.aktualisieren(uhr.t)
        phi = _phi_grad(uhr.t)
        pause = "" if panel.laeuft else "   [PAUSE]"
        aktiv = "/".join([n for n, _ in TYPEN if sichtbar.get(n)]
                         + (["boot"] if sichtbar.get("boot") else []))
        bruecke.status(
            "Aktiv: %s   phi(t): %8.2f Grad   Umdrehung: %d   "
            "Animationszeit: %7.2f s   Wiedergabe: %.2fx%s"
            % (aktiv, phi, int(phi // 360), uhr.t, panel.wiedergabe, pause))

    # Alle drei Koerper initial spawnen (K6-Kriterium): nebeneinander.
    for name, typ in TYPEN:
        spawne(name, typ)

    # Boot (statisch auf der Wasserlinie, einfarbig hellgrau) - Taste 4.
    try:
        boot, r_modell = fabriken.baue_boot(konfig)
        bruecke.koerper_objekt_setzen(
            "boot", boot, position=(0.0, 2.5, 0.0) + r_modell,
            farbe_unten="#c9c9c9", farbe_oben="#c9c9c9")   # Schritt 1: wie bisher
        sichtbar["boot"] = True
    except (FileNotFoundError, ImportError) as fehler:
        print("Hinweis: Boot nicht geladen:", fehler)

    # Tasten: 1/2/3 = einzelner Koerper ein/aus, a = alle an.
    for index in range(3):
        plotter.add_key_event(str(index + 1), lambda i=index: umschalten(i))
    plotter.add_key_event("a", lambda: [bruecke.sichtbar_setzen(n, True)
                                        for n, _ in TYPEN])

    def boot_umschalten():
        if "boot" in sichtbar:
            sichtbar["boot"] = not sichtbar["boot"]
            bruecke.sichtbar_setzen("boot", sichtbar["boot"])
    plotter.add_key_event("4", boot_umschalten)
    plotter.add_key_event("space", lambda: panel.umschalten())
    plotter.add_key_event("r", uhr.ruecksetzen)
    for taste in ("plus", "up", "kp_add"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(2.0))
    for taste in ("minus", "down", "kp_subtract"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(0.5))
    plotter.add_key_event("q", plotter.close)

    # Robuste Animationsschleife: interactive_update + update()
    plotter.show(interactive_update=True, auto_close=False)
    try:
        while True:
            taktschlag()
            plotter.update()
            time.sleep(0.012)
    except Exception:
        pass


if __name__ == "__main__":
    main()
