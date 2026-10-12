"""SegelPhysik V4 - Demo (P5c Phase C: Kraeftebild + Beenden-Fix).

Start: python -m segelphysik.demo_app
Tasten: [space] Objekt wechseln | [n] Uhr-Reset | [r/s/z] Simulationsmodus
        [7] Kraeftebild (F_G/F_A/Hebelarm, nur in STATISCH/ECHTZEIT)
        [+/-] Tempo | [F1-F4] Kamera | [o] SSAO | [5] r_S | [6] Hauptachsen
        [q] Ende (beendet jetzt auch das Terminal, kein Strg+C mehr noetig)

Phase C (Umsetzungsplan V5 rev 9 §5): Die Demo setzt pro Objekt einmal das
Auftriebsergebnis der Kraftfunktion (Pose 0,0,0) als Daten an die Bruecke
(P5a-Muster: Daten setzen, Renderer projiziert). Das Kraeftebild ist nur
im Modus STATISCH/ECHTZEIT sichtbar - im RUHEND gibt es nichts zu zeigen.
"""
from __future__ import annotations
import sys
import time

import numpy as np

from .core import bewegung as kin
from .core import fabriken
from .core import auftrieb
from .core import kraefte_bild as kb
from .core.konfig_lader import lade_konfig, lade_physik
from .grafik_bruecke import GrafikBruecke, FARBE_UNTEN, FARBE_OBEN
from .steuerung import ControlPanel
from .core.sim_modus import SimSteuerung, Modus
from . import grafik_optimierung
from .core.overlays import (LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                            LAYER_KRAEFTE)

# Objekt-Liste fuer die Space-Umschaltung (wrap-around). Weitere Objekte
# einfach als (name, typ)-Paar anhaengen; typ=None bedeutet Boot.
OBJEKTE = (("kegel", "cone"), ("quader", "box"),
           ("pyramide", "pyramid"), ("boot", None))
MITTE = np.array([0.0, 0.0, 0.0])   # Mitte des Wassers


def _phi_grad(t):
    if hasattr(kin, "phi_grad"):
        return kin.phi_grad(t)
    return kin.phi_deg(t)


def main():
    konfig = lade_konfig()   # Spec J: einzige Quelle, kein stiller Fallback
    physik = lade_physik()   # D8: dt/g/Daempfung/Voxel aus physik.json
    bruecke = GrafikBruecke()
    plotter = bruecke.fenster_bauen()
    opt = grafik_optimierung.anwenden(bruecke)   # Schritt 2: K1+K2+K5

    panel = ControlPanel()
    sim = SimSteuerung()   # P5c Schritt 1: Umschaltung
    uhr = kin.Uhr(wiedergabe=panel.wiedergabe)
    zustand = {"letzte_zeit": time.perf_counter()}
    aktuell = {"index": 0}
    erzeugt = {}
    kraefte_cache = {}      # name -> (erg, masse, g, skala)
    beenden = {"aktiv": False}

    def spawne(name, typ):
        """Erzeugt das Objekt in der Beckenmitte. True = Erfolg."""
        if typ is None:
            try:
                boot, r_modell = fabriken.baue_boot(konfig)
            except (FileNotFoundError, ImportError) as fehler:
                print("Hinweis: Boot nicht geladen:", fehler)
                return False
            objekt = boot
            bruecke.koerper_objekt_setzen(
                name, objekt, position=MITTE + np.asarray(r_modell, float))
        else:
            szene = kin.Szene.standard(typ)
            d = szene.koerper[0]
            bauer = {"cone": fabriken.baue_kegel, "box": fabriken.baue_quader,
                     "pyramid": fabriken.baue_pyramide}[typ]
            objekt = bauer(konfig, **d["dims"])
            bruecke.koerper_objekt_setzen(name, objekt, MITTE,
                                          achse=d["axis"], phase=d["phase"])
        erzeugt[name] = True
        # Phase C: Auftriebsergebnis der Ruhepose einmal rechnen und als
        # Daten an die Bruecke geben (P5a-Muster). Fehler killen die Demo
        # nicht - das Kraeftebild bleibt dann einfach aus.
        try:
            rho_w = konfig.wasser_dichte()
            g = physik.g_m_pro_s2
            kf = auftrieb.baue_kraftfunktion(
                objekt, rho_w=rho_w, g=g,
                aufloesung=physik.voxel_aufloesung_m)
            erg = kf((0.0, 0.0, 0.0))
            halbe = float(np.abs(np.asarray(objekt.punkte, float)).max()) or 1.0
            skala = kb.skala_waehlen(objekt.masse, g, referenz_laenge=1.1 * halbe)
            kraefte_cache[name] = (erg, objekt.masse, g, skala)
        except Exception as fehler:
            print("Hinweis: Kraeftebild nicht verfuegbar fuer %s:" % name, fehler)
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
        _kraefte_modus_anpassen()
        return name

    letzte_schaltung = {"t": 0.0}

    def umschalten_objekt():
        """Space: ein Objekt weiter (wrap-around). Entprellt."""
        jetzt = time.perf_counter()
        if jetzt - letzte_schaltung["t"] < 0.15:
            return
        letzte_schaltung["t"] = jetzt
        naechster = (aktuell["index"] + 1) % len(OBJEKTE)
        objekt_anzeigen(naechster)

    def _kraefte_modus_anpassen():
        """Phase C: Kraeftebild nur ausserhalb von RUHEND (Plan §5)."""
        name = OBJEKTE[aktuell["index"]][0]
        if sim.modus is Modus.RUHEND:
            bruecke.kraefte_entfernen(name)
        elif name in kraefte_cache:
            erg, m, g, sk = kraefte_cache[name]
            bruecke.kraefte_daten_setzen(name, erg, m, g, sk)

    letzte_kraefte_taste = {"t": 0.0}

    def umschalten_kraefte():
        """Taste 7: Layer 'kraefte' ein-/ausschalten (entprellt).

        Der Tastendruck kommt ueber Key-Event UND Poll-Fallback; ohne
        Entprellung toggelt eine physische Taste zweimal und der Layer
        endet immer AUS (Sichtprobe 12.10.)."""
        jetzt = time.perf_counter()
        if jetzt - letzte_kraefte_taste["t"] < 0.15:
            return
        letzte_kraefte_taste["t"] = jetzt
        an = bruecke.layer_umschalten(LAYER_KRAEFTE)
        if an:
            _kraefte_modus_anpassen()   # Daten sicherstellen (ECHTZEIT/STATISCH)
        _status_setzen("Layer 'kraefte': %s" % ("AN" if an else "AUS"))

    def _beenden():
        """q: vollstaendig beenden - Fenster UND Terminal-Schleife."""
        beenden["aktiv"] = True
        try:
            plotter.close()
        except Exception:
            pass

    letzte_poll_taste = {"sym": None}

    def tasten_poll():
        """Fallback: liest die zuletzt gedrueckte Taste direkt am Interactor."""
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
                _kraefte_modus_anpassen()
        elif sym == "space":
            umschalten_objekt()
        elif sym == "7":
            umschalten_kraefte()
        elif sym == "q":
            _beenden()

    def taktschlag():
        jetzt = time.perf_counter()
        real_dt = jetzt - zustand["letzte_zeit"]
        zustand["letzte_zeit"] = jetzt
        tasten_poll()
        # Uhr nur in ECHTZEIT weiterlaufen lassen: STATISCH zeigt die
        # statische Lage (eingefroren, Plan §4), nicht weiterrotierend.
        if sim.modus is Modus.ECHTZEIT:
            uhr.weiter_real(real_dt)
        bruecke.aktualisieren(uhr.t)
        opt.tick()
        phi = _phi_grad(uhr.t)
        name = OBJEKTE[aktuell["index"]][0]
        info = ("Objekt: %s   phi(t): %8.2f Grad   Animationszeit: %7.2f s"
                "   Wiedergabe: %.2fx" % (name, phi, uhr.t, panel.wiedergabe))
        if (bruecke.layer_ist_an(LAYER_KRAEFTE)
                and sim.modus is not Modus.RUHEND
                and name in kraefte_cache):
            info += "   " + kb.text_zeile(kraefte_cache[name][0])
        _status_setzen(sim.text() + "   " + info)
        bruecke.status(info)

    # Genau EIN Objekt initial (Ein-Objekt-Regel).
    objekt_anzeigen(0)

    # Tasten: space/n/r-s-z/+/-/F1-F4/o/5/6 wie gehabt; 7 = Kraeftebild;
    # q = vollstaendiges Beenden (vorher nur plotter.close -> Terminal hing).
    plotter.add_key_event("space", umschalten_objekt)
    plotter.add_key_event("n", uhr.ruecksetzen)
    for m_taste in ("r", "s", "z"):
        plotter.add_key_event(m_taste, lambda t=m_taste: sim.taste(t))
    plotter.add_key_event("7", umschalten_kraefte)
    plotter.add_key_event("q", _beenden)
    for taste in ("plus", "up", "kp_add"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(2.0))
    for taste in ("minus", "down", "kp_subtract"):
        plotter.add_key_event(taste, lambda: panel.aendere_wiedergabe(0.5))
    for taste, preset in (("F1", "bug"), ("F2", "heck"),
                          ("F3", "drei_viertel"), ("F4", "draufsicht")):
        plotter.add_key_event(taste, lambda n=preset: opt.kamera(n))

    plotter.show(interactive_update=True, auto_close=False)

    def _status_setzen(text):
        # vtkCornerAnnotation: Slot 0 = unten links (Sichtprobe 12.10.).
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

    try:
        entfernt = 0
        for prop in list(plotter.renderer.GetViewProps()):
            name_p = type(prop).__name__
            if not any(s in name_p for s in ("CornerAnnotation", "TextActor")):
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

    plotter.add_text(
        "SegelPhysik v4  [space] Objekt  [n] Reset  [r/s/z] Modus  "
        "[7] Kraefte  [+/-] Tempo  [F1-F4] Kamera  [o] SSAO  "
        "[5] r_S  [6] Hauptachsen  [q] Ende",
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
                _kraefte_modus_anpassen()
        elif sym == "n":
            uhr.ruecksetzen()
        elif sym in ("5", "6"):
            layer = LAYER_SCHWERPUNKT if sym == "5" else LAYER_HAUPTACHSEN
            an = bruecke.layer_umschalten(layer)
            _status_setzen("Layer '%s': %s" % (layer, "AN" if an else "AUS"))
        elif sym == "7":
            umschalten_kraefte()
        elif sym == "q":
            _beenden()
        elif sym == "space":
            umschalten_objekt()
    try:
        plotter.iren.add_observer("KeyPressEvent", _tasten_beobachter)
    except Exception as fehler:
        print("Tasten-Beobachter nicht registrierbar:", fehler)
    try:
        while not beenden["aktiv"]:
            taktschlag()
            plotter.update()
            time.sleep(0.012)
    finally:
        try:
            plotter.close()
        except Exception:
            pass
    print("SegelPhysik beendet.")


if __name__ == "__main__":
    main()
