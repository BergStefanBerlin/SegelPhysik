"""SegelPhysik V4 - Demo (P5c Schritt 1b: Ein-Objekt-Anzeige).

Start: python -m segelphysik.demo_app
Tasten: [space] Objekt wechseln (wrap-around) | [n] Uhr-Reset
        [r/s/z] Simulationsmodus | [+/-] Tempo | [F1-F4] Kamera
        [o] SSAO | [5] r_S | [6] Hauptachsen | [q] Ende

Ein-Objekt-Regel (12.10.): Immer genau EIN Objekt sichtbar, platziert
in der Mitte des Wassers. Space blaettert durch OBJEKTE. Die fruehere
Pausenfunktion ist entfernt (Space ist jetzt Objektwechsel).
"""
from __future__ import annotations
import time

import numpy as np

from .core import bewegung as kin
from .core import fabriken
from .core.konfig_lader import lade_konfig
from .grafik_bruecke import GrafikBruecke, FARBE_UNTEN, FARBE_OBEN
from .steuerung import ControlPanel
from .core.sim_modus import SimSteuerung, Modus
from . import grafik_optimierung
from .core.overlays import LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN

# Objekt-Liste fuer die Space-Umschaltung (wrap-around). Weitere Objekte
# einfach als (name, typ)-Paar anhaengen; typ=None bedeutet Boot.
# Ein neuer Mesh-Typ braucht einen eigenen Zweig in spawne().
OBJEKTE = (("kegel", "cone"), ("quader", "box"),
           ("pyramide", "pyramid"), ("boot", None))
MITTE = np.array([0.0, 0.0, 0.0])   # Mitte des Wassers


def _phi_grad(t):
    if hasattr(kin, "phi_grad"):
        return kin.phi_grad(t)
    return kin.phi_deg(t)


def main():
    konfig = lade_konfig()   # Spec J: einzige Quelle, kein stiller Fallback
    bruecke = GrafikBruecke()
    plotter = bruecke.fenster_bauen()
    opt = grafik_optimierung.anwenden(bruecke)   # Schritt 2: K1+K2+K5

    panel = ControlPanel()
    sim = SimSteuerung()   # P5c Schritt 1: nur Umschaltung
    uhr = kin.Uhr(wiedergabe=panel.wiedergabe)
    zustand = {"letzte_zeit": time.perf_counter()}
    aktuell = {"index": 0}
    erzeugt = {}

    def spawne(name, typ):
        """Erzeugt das Objekt in der Beckenmitte. True = Erfolg."""
        if typ is None:
            try:
                boot, r_modell = fabriken.baue_boot(konfig)
            except (FileNotFoundError, ImportError) as fehler:
                print("Hinweis: Boot nicht geladen:", fehler)
                return False
            bruecke.koerper_objekt_setzen(
                name, boot, position=MITTE + np.asarray(r_modell, float))
        else:
            szene = kin.Szene.standard(typ)
            d = szene.koerper[0]
            bauer = {"cone": fabriken.baue_kegel, "box": fabriken.baue_quader,
                     "pyramid": fabriken.baue_pyramide}[typ]
            k = bauer(konfig, **d["dims"])
            bruecke.koerper_objekt_setzen(name, k, MITTE,
                                          achse=d["axis"], phase=d["phase"])
        erzeugt[name] = True
        return True

    def objekt_anzeigen(index):
        """Zeigt genau EIN Objekt; das vorherige wird ausgeblendet."""
        name, typ = OBJEKTE[index]
        if name not in erzeugt:
            if not spawne(name, typ):
                return None
        else:
            bruecke.sichtbar_setzen(name, True)
        alter = OBJEKTE[aktuell["index"]][0]
        if alter != name and alter in erzeugt:
            bruecke.sichtbar_setzen(alter, False)
        aktuell["index"] = index
        return name

    letzte_schaltung = {"t": 0.0}

    def umschalten_objekt():
        """Space: ein Objekt weiter (wrap-around). Entprellt, weil die
        Taste ueber mehrere Kanaelle gemeldet werden kann."""
        jetzt = time.perf_counter()
        if jetzt - letzte_schaltung["t"] < 0.15:
            return
        letzte_schaltung["t"] = jetzt
        naechster = (aktuell["index"] + 1) % len(OBJEKTE)
        objekt_anzeigen(naechster)

    letzte_poll_taste = {"sym": None}

    def tasten_poll():
        """Fallback: liest die zuletzt gedrueckte Taste direkt am
        Interactor (falls der KeyPress-Beobachter nicht feuert).
        Loest nur bei Tastenwechsel aus -> kein Dauerfeuer."""
        try:
            sym = (plotter.iren.GetKeySym() or "").lower()
        except Exception:
            return
        if not sym or sym == letzte_poll_taste["sym"]:
            return
        letzte_poll_taste["sym"] = sym
        if sym in ("r", "s", "z"):
            if sim.taste(sym):
                print("MODUS ->", sim.text())
        elif sym == "space":
            umschalten_objekt()

    def taktschlag():
        jetzt = time.perf_counter()
        real_dt = jetzt - zustand["letzte_zeit"]
        zustand["letzte_zeit"] = jetzt
        tasten_poll()
        if sim.modus is not Modus.RUHEND:
            uhr.weiter_real(real_dt)
        bruecke.aktualisieren(uhr.t)
        opt.tick()
        phi = _phi_grad(uhr.t)
        name = OBJEKTE[aktuell["index"]][0]
        info = ("Objekt: %s   phi(t): %8.2f Grad   Animationszeit: %7.2f s"
                "   Wiedergabe: %.2fx" % (name, phi, uhr.t, panel.wiedergabe))
        _status_setzen(sim.text() + "   " + info)
        bruecke.status(info)

    # Genau EIN Objekt initial (Ein-Objekt-Regel).
    objekt_anzeigen(0)

    # Tasten: space = Objektwechsel, n = Uhr-Reset (war 'r'), r/s/z = Modus.
    plotter.add_key_event("space", umschalten_objekt)
    plotter.add_key_event("n", uhr.ruecksetzen)
    for m_taste in ("r", "s", "z"):
        plotter.add_key_event(m_taste, lambda t=m_taste: sim.taste(t))
    for taste in ("plus", "up", "kp_add"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(2.0))
    for taste in ("minus", "down", "kp_subtract"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(0.5))
    # Kamera-Presets (K5): F1 Bug, F2 Heck, F3 3/4, F4 Draufsicht
    for taste, preset in (("F1", "bug"), ("F2", "heck"),
                          ("F3", "drei_viertel"), ("F4", "draufsicht")):
        plotter.add_key_event(taste, lambda n=preset: opt.kamera(n))
    plotter.add_key_event("q", plotter.close)

    # Robuste Animationsschleife: interactive_update + update()
    plotter.show(interactive_update=True, auto_close=False)

    def _status_setzen(text):
        # vtkCornerAnnotation: Slot 0 = unten links (Sichtprobe 12.10.).
        # Der Prop wird initial LEER angelegt, damit oben rechts nichts
        # stehen bleibt; alle Updates laufen ueber Slot 0.
        try:
            status.SetText(0, text)
            status.Modified()
            return
        except Exception:
            pass
        try:
            status.SetInput(text)
            status.Modified()
        except Exception:
            pass

    # Alter V3-Titel (fest in vista.py) wird ENTFERNT: Alle Text-Props,
    # deren Inhalt den alten Text enthaelt, kommen aus dem Renderer raus.
    try:
        entfernt = 0
        for prop in list(plotter.renderer.GetViewProps()):
            name = type(prop).__name__
            if not any(s in name for s in ("CornerAnnotation", "TextActor")):
                continue
            texte = []
            fn = getattr(prop, "GetInput", None)
            if fn:
                try:
                    texte.append(str(fn() or ""))
                except Exception:
                    pass
            gt = getattr(prop, "GetText", None)
            if gt:
                try:
                    texte += [str(gt(i) or "") for i in range(4)]
                except Exception:
                    pass
            if any(("v0.4" in t) or ("[g/G]" in t) for t in texte):
                plotter.renderer.RemoveActor(prop)
                entfernt += 1
        print("Alter Titel entfernt (%d Actor(s))" % entfernt)
    except Exception as fehler:
        print("Alter Titel nicht entfernbar:", fehler)

    # Titel + Status-Prop (initial LEER -> oben rechts bleibt leer;
    # der Modus-/Info-Text lebt unten links, Slot 0).
    plotter.add_text(
        "SegelPhysik v4  [space] Objekt  [n] Reset  [r/s/z] Modus  "
        "[+/-] Tempo  [F1-F4] Kamera  [o] SSAO  [5] r_S  [6] Hauptachsen  "
        "[q] Ende",
        position="upper_left", font_size=10, color="black", name="titel_v4")
    status = plotter.add_text(" ", position="upper_right",
                              font_size=12, color="darkred", name="status")
    _status_setzen(sim.text())

    def _tasten_beobachter(objekt, ereignis):
        sym = (objekt.GetKeySym() or "").lower()
        print("TASTE:", sym)
        if sym == "o":
            try:
                meldung = opt.ssao_umschalten()
            except Exception as fehler:
                meldung = "Fehler: %s" % fehler
            _status_setzen("SSAO: %s" % meldung)
        elif sym in ("f1", "f2", "f3", "f4"):
            _status_setzen("Kamera: %s" % sym.upper())
        elif sym in ("r", "s", "z"):
            if sim.taste(sym):
                print("MODUS ->", sim.text())
        elif sym == "n":
            uhr.ruecksetzen()
        elif sym in ("5", "6"):
            layer = LAYER_SCHWERPUNKT if sym == "5" else LAYER_HAUPTACHSEN
            an = bruecke.layer_umschalten(layer)
            _status_setzen("Layer '%s': %s" % (layer, "AN" if an else "AUS"))
        elif sym == "space":
            umschalten_objekt()
    try:
        plotter.iren.add_observer("KeyPressEvent", _tasten_beobachter)
    except Exception as fehler:
        print("Tasten-Beobachter nicht registrierbar:", fehler)
    try:
        while True:
            taktschlag()
            plotter.update()
            time.sleep(0.012)
    except Exception:
        pass


if __name__ == "__main__":
    main()
