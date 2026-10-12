"""SegelPhysik V4 - Demo (P5c Phase C + B2 + Spec V4A rev C: Stoer-Taste v).

Start: python -m segelphysik.demo_app
Tasten: [space] Objekt wechseln | [n] Uhr-Reset | [r/s/z] Simulationsmodus
        [v] Zufaellige Stoerpose (Spec V4A: <= 2 m, alle 3 Achsen +/-180 Grad;
            STATISCH: 5-s-Countdown, dann Solver ab projizierter Stoerpose;
            RUHEND: Koerper bleibt stehen, beliebig oft wiederholbar)
        [7] Kraeftebild (F_G/F_A/Hebelarm/Moment-Bogen, STATISCH/ECHTZEIT)
        [+/-] Tempo | [F1-F4] Kamera | [o] SSAO | [5] r_S | [6] Hauptachsen
        [q] Ende

rev C (Sichtprobe 12.10.):
  1. PyVista belegt 'v' WERKSSEITIG mit der Isometrie-Kamera - diese
     Bindung wird beim Start entfernt (sonst springt die Kamera bei v).
  2. Solver-Fehler raeumen auf: keine eingefrorene gekippte Störpose
     mehr - der Koerper kehrt in die Ruhepose zurueck, Status meldet
     den Befund (das Bild war vorher NICHT das Solverbild).
  3. St-9 Multi-Start: Solver laeuft ab projizierter Störpose UND ab
     Ruhepose; unter den stabilen Loesungen (GM > 0) gewinnt die
     tiefste Lage (min. potentielle Energie) - Schein-Gleichgewichte
     ("liegend") verlieren gegen die aufrechte Schwimmlage.
"""
from __future__ import annotations
import random
import sys
import time

import numpy as np

from .core import bewegung as kin
from .core import fabriken
from .core import auftrieb
from .core import kraefte_bild as kb
from .core import stoerung as sto
from .core.konfig_lader import lade_konfig, lade_physik
from .grafik_bruecke import GrafikBruecke, FARBE_UNTEN, FARBE_OBEN
from .steuerung import ControlPanel
from .core.sim_modus import SimSteuerung, StoerSequenz, Modus
from .core.statisch import SolverFehler
from .core.statisch_robust import loese_robust as statisch_loese
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


def _v_werksbindung_entfernen(plotter):
    """rev C: PyVista registriert in Plotter.__init__ werksseitig
    add_key_event('v', isometric_view_interactive) - deshalb sprang bei
    'v' die Kamera (Sichtprobe 12.10.). Wir leeren diese Bindung, bevor
    unsere eigene registriert wird."""
    cb = getattr(plotter, "_key_press_event_callbacks", None)
    if isinstance(cb, dict) and "v" in cb:
        cb["v"] = []
        print("PyVista-Werksbindung 'v' (Isometrie-Kamera) entfernt.")
        return True
    print("WARNUNG: PyVista-Werksbindung 'v' nicht auffindbar. Springt die "
          "Kamera bei 'v' trotzdem, bitte Rueckmeldung geben (Ausweich-"
          "taste waere 'x').")
    return False


def main():
    konfig = lade_konfig()   # Spec J: einzige Quelle, kein stiller Fallback
    physik = lade_physik()   # D8: dt/g/Daempfung/Voxel aus physik.json
    bruecke = GrafikBruecke()
    plotter = bruecke.fenster_bauen()
    _v_werksbindung_entfernen(plotter)   # rev C: Kamera-Sprung bei v fix
    opt = grafik_optimierung.anwenden(bruecke)   # Schritt 2: K1+K2+K5

    panel = ControlPanel()
    sim = SimSteuerung()   # P5c Schritt 1: Umschaltung
    sequenz = StoerSequenz(5.0)   # Spec V4A: Countdown Stoerpose -> Solver
    stoer_rng = random.Random()   # echtes Rauschen in der Demo (Tests: Seed)
    uhr = kin.Uhr(wiedergabe=panel.wiedergabe)
    zustand = {"letzte_zeit": time.perf_counter()}
    aktuell = {"index": 0}
    erzeugt = {}
    kraefte_cache = {}      # name -> (erg, masse, g, skala)
    kraefte_start = {}      # name -> Ruhepose-Ergebnis (Restore bei r/z)
    kraftfunktionen = {}    # name -> gebundene Kraftfunktion (F19)
    statisch_info = {}      # name -> Kurzinfo der Loesung fuer die Statuszeile
    stoer_basis = {}        # name -> ungestoerte Basis-Position (St-2)
    stoer_start = {}        # name -> projizierte Solver-Startlage (St-6)
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
            position = MITTE + np.asarray(r_modell, float)
            bruecke.koerper_objekt_setzen(name, objekt, position=position)
        else:
            szene = kin.Szene.standard(typ)
            d = szene.koerper[0]
            bauer = {"cone": fabriken.baue_kegel, "box": fabriken.baue_quader,
                     "pyramid": fabriken.baue_pyramide}[typ]
            objekt = bauer(konfig, **d["dims"])
            position = MITTE
            bruecke.koerper_objekt_setzen(name, objekt, MITTE,
                                          achse=d["axis"], phase=d["phase"])
        erzeugt[name] = True
        stoer_basis[name] = np.asarray(position, float).copy()
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
            kraefte_start[name] = kraefte_cache[name]
            kraftfunktionen[name] = kf
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

    def _statisch_loesen_und_setzen(name, startliste=((0.0, 0.0),)):
        """Phase B2 + Spec V4A rev C: Solver ab mehreren Startlagen
        (St-9: projizierte Stoerpose + Ruhepose), jeweils mit Kontaktstart
        (St-8); unter den stabilen Loesungen gewinnt die tiefste Lage.
        Ohne stabile Loesung: Befund in Konsole/Status UND Rueckkehr in
        die Ruhepose (keine eingefrorene gekippte Störpose mehr)."""
        eintrag = kraefte_cache.get(name)
        kf = kraftfunktionen.get(name)
        if eintrag is None or kf is None:
            print("STATISCH: keine Kraefte-Daten fuer %s - Solver uebersprungen" % name)
            return
        _erg, m, g, _sk = eintrag
        print("STATISCH: Solver laeuft (%s), %d Startlage(n) ..."
              % (name, len(startliste)))
        _status_setzen("STATISCH: Solver rechnet ... (Protokoll in der Konsole)")
        try:
            plotter.update()
        except Exception:
            pass
        t0 = time.perf_counter()
        loesungen = []
        for start in startliste:
            try:
                z0, phi0 = sto.kontakt_start(kf, float(start[0]),
                                             float(start[1]))
            except SolverFehler as fehler:
                print("STATISCH: Kontaktstart (St-8) ab %r fehlgeschlagen: %s"
                      % (start, fehler))
                continue
            try:
                loesungen.append(statisch_loese(kf, m, g=g, start=(z0, phi0)))
                if ((loesungen[-1].get("gm") is not None and loesungen[-1]["gm"] > 0.0) or loesungen[-1].get("stabil") is True):
                    break   # rev E: erster tragbarer Treffer
            except SolverFehler as fehler:
                print("STATISCH: Solver ab %r fehlgeschlagen: %s"
                      % (start, fehler))
        beste = sto.beste_loesung(loesungen)
        dauer = time.perf_counter() - t0
        if beste is None:
            print("STATISCH: keine stabile Loesung nach %.2f s (%d Versuche) "
                  "- Rueckkehr in die Ruhepose" % (dauer, len(startliste)))
            _status_setzen("STATISCH: keine stabile Loesung (siehe Konsole)")
            statisch_info.pop(name, None)
            bruecke.stoer_pose_loeschen(name)   # rev C: nicht gekippt stehen lassen
            # rev D: Kraefte-Daten an der RUHEPOSE setzen, damit Taste 7
            # auch ohne stabile Loesung Pfeile zeigt (Sichtprobe 12.10.).
            erg_r = kf((0.0, 0.0, 0.0))
            kraefte_cache[name] = (auftrieb.Auftriebsergebnis(
                erg_r.V_tauch, np.asarray(erg_r.K.as_array(), float),
                erg_r.F_A, erg_r.M), m, g, _sk)
            erg, mm, gg, sk2 = kraefte_cache[name]
            bruecke.kraefte_daten_setzen(name, erg, mm, gg, sk2)
            return
        z, phi = float(beste["z"]), float(beste["phi"])
        gm = beste["gm"]
        vermerk = []
        if beste.get("stagnation"):
            vermerk.append("Stagnation akzeptiert (Voxel-Treppe, Rest s. u.)")
        if beste.get("neutral"):
            vermerk.append("Roll NEUTRAL (GM=0 ist hier Physik)")
        print("STATISCH: z*=%.4f m  phi*=%.2f Grad  Iterationen=%d  Restarts=%d  "
              "Restkraft=%.2e N  Restmoment=%.2e N*m  GM=%s  Dauer=%.2f s%s"
              % (z, np.degrees(phi), beste["iterationen"], beste["restarts"],
                 beste["restkraft"], beste["restmoment"],
                 ("%.4f m" % gm) if gm is not None else "n/a", dauer,
                 ("  [" + "; ".join(vermerk) + "]") if vermerk else ""))
        # Ergebnis AN DER LOESUNG holen. K ist Welt (D11: r_S dort bei
        # (0,0,z)) -> fuer die Bruecke auf r_S normieren (Vertrag: K relativ).
        erg_l = kf((z, phi, 0.0))
        K_rel = (np.asarray(erg_l.K.as_array(), float)
                 - np.array([0.0, 0.0, z]))
        erg_anzeige = auftrieb.Auftriebsergebnis(
            erg_l.V_tauch, K_rel, erg_l.F_A, erg_l.M)
        # D1: Skala bleibt die feste Szene-Skala - nicht neu waehlen.
        kraefte_cache[name] = (erg_anzeige, m, g, _sk)
        kenn = " (Roll neutral)" if beste.get("neutral") else ""
        statisch_info[name] = "z*=%7.3f m  phi*=%6.2f Grad%s" \
            % (z, np.degrees(phi), kenn)
        bruecke.statische_pose_setzen(name, z, phi)
        erg, mm, gg, sk2 = kraefte_cache[name]
        bruecke.kraefte_daten_setzen(name, erg, mm, gg, sk2)
        _status_setzen("STATISCH: Gleichgewicht z*=%.3f m  phi*=%.2f Grad"
                       % (z, np.degrees(phi)))

    def _startliste_fuer(name):
        """St-9: projizierte Störpose + Ruhepose als Startkandidaten."""
        start = stoer_start.pop(name, None)
        if start is None:
            return ((0.0, 0.0),)
        return (start, (0.0, 0.0))

    def stoeren():
        """Taste v (Spec V4A SS3/SS4): zufaellige Stoerpose anzeigen.

        RUHEND: Koerper bleibt stehen, beliebig oft wiederholbar.
        STATISCH: 5-s-Countdown, dann Solver ab projizierter Stoerpose.
        ECHTZEIT: nur Anzeige (Dynamik = Phase D, spaeter).
        """
        jetzt = time.perf_counter()
        if jetzt - letzte_stoer_taste["t"] < 0.15:
            return
        letzte_stoer_taste["t"] = jetzt
        name = OBJEKTE[aktuell["index"]][0]
        if name not in stoer_basis or name not in kraftfunktionen:
            print("STOER: keine Daten fuer %s - uebersprungen" % name)
            return
        st = sto.stoerung_ziehen(stoer_rng)
        R, pos = sto.stoss_pose(stoer_basis[name], st)
        bruecke.stoer_pose_setzen(name, R, pos)
        z_start, phi_start = sto.projektion(pos, st)
        dx, dy, dz = st["versatz"]
        wx, wy, wz = (np.degrees(w) for w in st["winkel"])
        print("STOER[%s]: versatz=(%.2f, %.2f, %.2f) m  "
              "winkel=(%.1f, %.1f, %.1f) Grad"
              % (name, dx, dy, dz, wx, wy, wz))
        if sim.modus is Modus.STATISCH:
            stoer_start[name] = (z_start, phi_start)
            sequenz.starten()
            _status_setzen("Stoerpose gesetzt - Solver in %.0f s"
                           % sequenz.dauer)
        elif sim.modus is Modus.RUHEND:
            _status_setzen("Stoerpose gesetzt (RUHEND: Koerper bleibt)")
        else:
            _status_setzen("Stoerpose gesetzt (ECHTZEIT: nur Anzeige)")

    def _kraefte_modus_anpassen():
        """Phase C+B2+V4A: Kraeftebild ausserhalb von RUHEND (Plan §5);
        STATISCH loest die Gleichgewichtslage - waehrend des Stoer-
        Countdowns aber erst nach Ablauf (Taktschlag)."""
        name = OBJEKTE[aktuell["index"]][0]
        if sim.modus is Modus.RUHEND:
            bruecke.kraefte_entfernen(name)
            bruecke.statische_pose_loeschen(name)
            # Stoerpose bleibt stehen (Spec SS4: in RUHEND bleibt der Koerper)
        elif sim.modus is Modus.STATISCH:
            if sequenz.aktiv:
                pass   # Countdown laeuft; der Taktschlag loest dann
            else:
                _statisch_loesen_und_setzen(name)
        else:
            sequenz.abbrechen()
            bruecke.stoer_pose_loeschen(name)
            bruecke.statische_pose_loeschen(name)
            if name in kraefte_start:
                kraefte_cache[name] = kraefte_start[name]
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
        elif sym == "v":
            stoeren()
        elif sym == "q":
            _beenden()

    def taktschlag():
        jetzt = time.perf_counter()
        real_dt = jetzt - zustand["letzte_zeit"]
        zustand["letzte_zeit"] = jetzt
        tasten_poll()
        # Spec V4A: Countdown nur in STATISCH; nach Ablauf loest der Solver
        # ab der projizierten Stoerpose (St-6 + St-8 + St-9).
        if sequenz.aktiv:
            if sim.modus is not Modus.STATISCH:
                sequenz.abbrechen()
            elif sequenz.tick(real_dt):
                name_c = OBJEKTE[aktuell["index"]][0]
                _statisch_loesen_und_setzen(name_c,
                                            startliste=_startliste_fuer(name_c)
                                                + [(0.0, math.pi / 2.0)])
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
        if sequenz.aktiv and sim.modus is Modus.STATISCH:
            info += "   " + sequenz.text()
        if (bruecke.layer_ist_an(LAYER_KRAEFTE)
                and sim.modus is not Modus.RUHEND
                and name in kraefte_cache):
            info += "   " + kb.text_zeile(kraefte_cache[name][0])
        if sim.modus is Modus.STATISCH and name in statisch_info:
            info += "   " + statisch_info[name]
        _status_setzen(sim.text() + "   " + info)
        bruecke.status(info)

    # Genau EIN Objekt initial (Ein-Objekt-Regel).
    objekt_anzeigen(0)

    # Tasten: space/n/r-s-z/v/+/-/F1-F4/o/5/6 wie gehabt; 7 = Kraeftebild;
    # q = vollstaendiges Beenden.
    plotter.add_key_event("space", umschalten_objekt)
    plotter.add_key_event("n", uhr.ruecksetzen)
    for m_taste in ("r", "s", "z"):
        plotter.add_key_event(m_taste, lambda t=m_taste: sim.taste(t))
    plotter.add_key_event("v", stoeren)
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
        "[v] Stoeren  [7] Kraefte  [+/-] Tempo  [F1-F4] Kamera  [o] SSAO  "
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
        elif sym == "v":
            stoeren()
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
