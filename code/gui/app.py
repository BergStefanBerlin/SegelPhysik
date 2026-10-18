# -*- coding: utf-8 -*-
"""Startpunkt der GUI: python -m segelphysik.gui.app.

rev H: ausfuehrliches Terminal-Logging + faulthandler (diagnostiziert
spontanes Schliessen), Standard-Sichtbarkeit aus der Konfiguration,
doppelte Layout-Einsetzung des QtInteractor entfernt.
"""
from __future__ import annotations

import faulthandler
import os
import sys
import traceback


def _log(msg):
    """Protokolliert NACH Terminal (flush!) und in das GUI-Protokoll-Dock."""
    print("[SegelPhysik] %s" % (msg,), flush=True)
    try:
        import segelphysik.gui.hauptfenster as hf
        f = hf._aktives_fenster
        if f is not None:
            f.protokoll_schreiben(str(msg))
    except Exception:
        pass


def _finde_koerper_json():
    ordner = os.path.dirname(os.path.abspath(__file__))
    kandidaten = [
        os.path.abspath(os.path.join(ordner, "..", "..",
                                     "konfigurationen", "koerper.json")),
        os.path.abspath(os.path.join(os.getcwd(), "konfigurationen",
                                     "koerper.json")),
    ]
    for k in kandidaten:
        if os.path.exists(k):
            return k
    return None


def _gpu_praesenz_protokollieren():
    from ..core.physik_backend import BackendNichtVerfuegbar, OpenCLBackend
    try:
        geraete = OpenCLBackend.gpu_namen_ermitteln()
    except BackendNichtVerfuegbar as fehler:
        _log("OpenCL-GPU nicht verfügbar; CPU bleibt einsatzbereit: %s" % fehler)
        return
    if geraete:
        _log("OpenCL-GPU vorhanden: %s" % ", ".join(geraete))
    else:
        _log("Keine OpenCL-GPU vorhanden; CPU bleibt einsatzbereit.")


def welt_laden():
    from .baum import (welt_aus_konfig, einfache_figur, Knoten,
                       sichtbarkeit_setzen, summenkoerper)
    pfad = _finde_koerper_json()
    if pfad is None:
        _log("koerper.json NICHT gefunden - nutze Demo-Grundkoerper.")
        welt = Knoten("Welt", "welt", "globus", aktiv=True, sichtbar=False)
        for name in ("Kegel", "Quader", "Pyramide"):
            welt.hinzufuegen(einfache_figur(name))
        standard = None
    else:
        _log("koerper.json geladen: %s" % pfad)
        from ..core.konfig_lader import lade_konfig
        konfig = lade_konfig(os.path.dirname(pfad))
        welt = welt_aus_konfig(konfig)
        namen = {k.name.casefold() for k in welt.kinder}
        for name in ("Kegel", "Quader", "Pyramide"):
            if name.casefold() not in namen:
                welt.hinzufuegen(einfache_figur(name))
                _log("Einfache Figur ergaenzt: %s" % name)
        standard = konfig.standard_ansicht
    hauptobjekte = summenkoerper(welt)
    namen = {k.name.casefold(): k.name for k in hauptobjekte}
    auswahl = namen.get(standard.casefold()) if standard else None
    if auswahl is None and hauptobjekte:
        auswahl = hauptobjekte[0].name
    if auswahl is not None:
        sichtbarkeit_setzen(welt, auswahl)
        _log("Standard-Sichtbarkeit: %s" % auswahl)
    n = sum(1 for _ in welt.iteriere())
    _log("Baum aufgebaut: %d Knoten." % n)
    return welt


def _szene_einbetten(fenster):
    """Betttet die bestehende Szene-Pipeline in den QtInteractor ein."""
    from pyvistaqt import QtInteractor
    import pyvista as pv
    from segelphysik.grafik_bruecke import GrafikBruecke

    _log("QtInteractor wird erzeugt ...")
    qt_interactor = QtInteractor(None)
    _log("QtInteractor steht.")

    # A2 (Additivprinzip): core/render/bruecke bleiben UNBERUEHRT.
    # Der Renderer erzeugt seine Szene via pv.Plotter(...); fuer diesen
    # einen Aufruf liefert hier der QtInteractor. Danach Restaurierung.
    _orig_plotter = pv.Plotter
    pv.Plotter = lambda **kwargs: qt_interactor
    try:
        _log("GrafikBruecke.fenster_bauen() laeuft (Szene im QtInteractor) ...")
        bruecke = GrafikBruecke()
        bruecke.fenster_bauen()
        _log("Szene aufgebaut.")
    finally:
        pv.Plotter = _orig_plotter

    # EINMALIG ins zentrale Layout (rev G: ansicht_setzen ersetzt den
    # Platzhalter; hier KEIN zweites addWidget mehr!)
    fenster.ansicht_setzen(qt_interactor)
    _log("QtInteractor ins zentrale Layout eingesetzt.")
    fenster.bruecke_setzen(bruecke)
    _log("3D-Ansicht aktiv (QtInteractor eingebettet).")
    return qt_interactor


def main():
    faulthandler.enable()   # Abstuerze OHNE Traceback sichtbar machen
    print("[SegelPhysik] Start (rev H), Python %s" % sys.version, flush=True)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from .hauptfenster import HauptFenster

    app = QApplication(sys.argv)
    fenster = HauptFenster()
    import segelphysik.gui.hauptfenster as hf
    hf._aktives_fenster = fenster

    def _excepthook(typ, wert, tb):
        _log("UNBEHANDELT Exception:\n" + "".join(
            traceback.format_exception(typ, wert, tb)))
        sys.__excepthook__(typ, wert, tb)
    sys.excepthook = _excepthook

    _gpu_praesenz_protokollieren()

    try:
        fenster.baum_setzen(welt_laden())
    except Exception:
        _log("Baum-Fehler:\n" + traceback.format_exc())

    try:
        _szene_einbetten(fenster)
    except Exception:
        _log("Szenenaufbau fehlgeschlagen:\n" + traceback.format_exc())
        try:
            from PySide6.QtWidgets import QLabel
            platz = QLabel("3D-Ansicht nicht verfuegbar "
                           "(siehe Protokoll/Terminal).")
            platz.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fenster.ansicht_setzen(platz)
        except Exception:
            pass

    fenster.show()
    _log("Fenster sichtbar - Ereignisschleife laeuft.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
