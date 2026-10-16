"""Messung der sichtbaren Echtzeit-GUI mit dem produktiven Yachtmodell.

Aus dem Repository-Hauptverzeichnis starten:
    .venv\\Scripts\\python.exe werkzeuge\\benchmark_gui_live.py

Standardmäßig werden 30 Sekunden aufgewärmt und zehn Minuten gemessen.
Renderaufrufe und Qt-Event-Dispatch gelten nicht als präsentierte FPS oder
Eingabe-bis-sichtbar-Latenz; nicht verfügbare Messwerte bleiben ausdrücklich
unbestimmt.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import sys
import threading
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _perzentil(werte, anteil):
    if not werte:
        return None
    sortiert = sorted(werte)
    index = min(len(sortiert) - 1,
                int(anteil * (len(sortiert) - 1) + 0.5))
    return sortiert[index]


def _warte(app, dauer_ms):
    from PySide6.QtCore import QEventLoop, QTimer

    schleife = QEventLoop()
    QTimer.singleShot(dauer_ms, schleife.quit)
    schleife.exec()
    app.processEvents()


def _fenster_schliessen(app, fenster, hauptfenster_mod):
    from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool

    fenster._zeit_pausieren()
    if not QThreadPool.globalInstance().waitForDone(120_000):
        raise RuntimeError(
            "GUI-Benchmark kann nicht schließen: Worker läuft nach 120 s.")
    app.processEvents()
    fenster._statische_arbeitsdaten.clear()
    fenster._statische_ergebnisse.clear()
    fenster._laufzeit_koerper.clear()
    fenster._echtzeit_kraftfunktion = None
    fenster._echtzeit_kraefteresultat = None
    fenster.close()
    if hauptfenster_mod._aktives_fenster is fenster:
        hauptfenster_mod._aktives_fenster = None
    fenster.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


def benchmark(scene, warmup_s, duration_s, backend="exakt_union",
              measure_parameter_change=False):
    from PySide6.QtCore import QObject, Qt, QTimer, Signal
    from PySide6.QtWidgets import QApplication

    startup_start = time.perf_counter()

    class EreignisSignal(QObject):
        impuls = Signal(float)

    app = QApplication.instance() or QApplication([])
    from segelphysik.gui.app import _szene_einbetten, welt_laden
    from segelphysik.gui.baum import sichtbarkeit_setzen
    from segelphysik.gui import hauptfenster as hauptfenster_mod
    from segelphysik.gui.hauptfenster import HauptFenster
    from segelphysik.core.overlays import (
        LAYER_HAUPTACHSEN, LAYER_KRAEFTE, LAYER_MOMENTE,
        LAYER_SCHWERPUNKT,
    )

    hauptfenster_mod._ECHTZEIT_HYDROSTATIK_PFAD = backend
    welt = welt_laden()
    sichtbarkeit_setzen(welt, scene)
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    _szene_einbetten(fenster)
    bridge = fenster._bruecke
    first_scene_presented_s = [None]
    render_fenster = bridge._plotter.render_window

    def first_scene_presented(_obj, _ereignis):
        if first_scene_presented_s[0] is not None:
            return
        if hasattr(render_fenster, "WaitForCompletion"):
            render_fenster.WaitForCompletion()
        first_scene_presented_s[0] = time.perf_counter() - startup_start

    render_fenster.AddObserver("EndEvent", first_scene_presented)
    fenster.show()
    app.processEvents()
    gui_bedienbar_s = time.perf_counter() - startup_start

    pflicht_layer = {
        "schwerpunkt": LAYER_SCHWERPUNKT,
        "hauptachsen": LAYER_HAUPTACHSEN,
        "kraefte": LAYER_KRAEFTE,
        "momente": LAYER_MOMENTE,
    }
    for layer in pflicht_layer.values():
        bridge.layer_setzen(layer, True)
    renderzeiten = []
    posezeiten = []
    batchzeiten = []
    fehler = []
    render_alt = bridge.render
    pose_alt = bridge.physik_pose_6dof_setzen

    def render_messen():
        start = time.perf_counter()
        erfolgreich = render_alt()
        dauer = time.perf_counter() - start
        if erfolgreich:
            renderzeiten.append(dauer)
        return erfolgreich

    def pose_messen(*args):
        start = time.perf_counter()
        erfolgreich = pose_alt(*args)
        posezeiten.append(time.perf_counter() - start)
        return erfolgreich

    bridge.render = render_messen
    bridge.physik_pose_6dof_setzen = pose_messen

    # Präsentationszeitpunkt: VTK-EndEvent liegt nach SwapBuffers; mit
    # WaitForCompletion (glFinish) ist der Frame vom Treiber abgeschlossen.
    plotter = bridge._plotter
    render_fenster = plotter.render_window
    praesentiert = []
    reaktionen = []
    stimulus = {"zeit": None, "kamera": None}

    def kamera_zustand():
        return tuple(np.round(plotter.camera.position, 6))

    def frame_beendet(_obj, _ereignis):
        if hasattr(render_fenster, "WaitForCompletion"):
            render_fenster.WaitForCompletion()
        jetzt = time.perf_counter()
        praesentiert.append(jetzt)
        if (stimulus["zeit"] is not None
                and kamera_zustand() != stimulus["kamera"]):
            reaktionen.append(jetzt - stimulus["zeit"])
            stimulus["zeit"] = None

    render_fenster.AddObserver("EndEvent", frame_beendet)
    _warte(app, round(warmup_s * 1000))
    if measure_parameter_change:
        from segelphysik.gui.baum import finde

        def abbrechen_nach_workerende(nachricht):
            _fenster_schliessen(app, fenster, hauptfenster_mod)
            raise RuntimeError(nachricht)

        anfang = {"fertig": False, "fehler": None}

        def anfang_fertig(gemeldet, name, _ergebnis, _arbeitsdaten, fehler):
            if (gemeldet == fenster._statisch_generation and name == scene):
                anfang["fertig"] = True
                anfang["fehler"] = fehler

        anfang_signale = fenster._statisch_signale
        anfang_signale.abgeschlossen.connect(anfang_fertig)
        deadline_anfang = time.perf_counter() + 60.0
        try:
            while True:
                alter_koerper = fenster._laufzeit_koerper.get(scene)
                altes_ergebnis = fenster._statische_ergebnisse.get(scene)
                if alter_koerper is not None and altes_ergebnis is not None:
                    break
                if anfang["fertig"]:
                    abbrechen_nach_workerende(
                        "Ausgangsberechnung fehlgeschlagen: %s"
                        % anfang["fehler"])
                if time.perf_counter() >= deadline_anfang:
                    abbrechen_nach_workerende(
                        "Ausgangskörper oder akzeptiertes Statikergebnis "
                        "fehlt nach 60 s.")
                app.processEvents()
                time.sleep(0.001)
        finally:
            anfang_signale.abgeschlossen.disconnect(anfang_fertig)

        knoten = finde(welt, "rumpf")
        if knoten is None or "wanddicke_m" not in knoten.eintrag:
            abbrechen_nach_workerende(
                "Parameterbenchmark benötigt ein Rumpfblatt mit Wanddicke.")

        edit_start = time.perf_counter()
        statik = {"fertig": False, "fehler": None, "abgeschlossen_s": None}
        erste_konsistente_praesentation = [None]
        generation = None

        def statik_fertig(gemeldet, name, ergebnis, _arbeitsdaten, fehler):
            if gemeldet == generation and name == scene:
                statik["fertig"] = True
                statik["fehler"] = fehler
                statik["abgeschlossen_s"] = time.perf_counter() - edit_start

        def edit_frame(_obj, _ereignis):
            if (not statik["fertig"] or statik["fehler"] is not None
                    or fenster._laufzeit_koerper.get(scene) is alter_koerper
                    or fenster._statische_ergebnisse.get(scene)
                    is altes_ergebnis):
                return
            if hasattr(render_fenster, "WaitForCompletion"):
                render_fenster.WaitForCompletion()
            erste_konsistente_praesentation[0] = (
                time.perf_counter() - edit_start)

        fenster._statisch_signale.abgeschlossen.connect(statik_fertig)
        render_fenster.AddObserver("EndEvent", edit_frame)
        alte_wanddicke_mm = 1000.0 * float(knoten.eintrag["wanddicke_m"])
        alte_masse = float(alter_koerper.masse)
        fenster.baum._eigenschaft_setzen(
            knoten, "Wanddicke", alte_wanddicke_mm + 1.0)
        generation = fenster._statisch_generation
        neuer_koerper = fenster._laufzeit_koerper.get(scene)
        rebuild_s = time.perf_counter() - edit_start
        if neuer_koerper is None or neuer_koerper is alter_koerper:
            raise RuntimeError(
                "Parameteränderung hat keinen neuen Laufzeitkörper gebaut.")

        deadline = time.perf_counter() + 60.0
        while (not statik["fertig"]
               or (statik["fehler"] is None
                   and erste_konsistente_praesentation[0] is None)):
            if time.perf_counter() >= deadline:
                fenster._statisch_signale.abgeschlossen.disconnect(statik_fertig)
                abbrechen_nach_workerende(
                    "Parameteränderung, Solver oder sichtbare Aktualisierung "
                    "nicht innerhalb von 60 s abgeschlossen.")
            app.processEvents()
            time.sleep(0.001)
        fenster._statisch_signale.abgeschlossen.disconnect(statik_fertig)
        _fenster_schliessen(app, fenster, hauptfenster_mod)
        result = {
            "operation": "Rumpf-Wanddicke um 1 mm erhöhen",
            "wanddicke_vorher_mm": alte_wanddicke_mm,
            "wanddicke_nachher_mm": 1000.0 * float(
                knoten.eintrag["wanddicke_m"]),
            "masse_vorher_kg": alte_masse,
            "masse_nachher_kg": float(neuer_koerper.masse),
            "laufzeit_bis_neuer_koerper_s": round(rebuild_s, 6),
            "laufzeit_bis_solverabschluss_s": (
                round(statik["abgeschlossen_s"], 6)
                if statik["abgeschlossen_s"] is not None else None),
            "laufzeit_bis_konsistenter_praesentierter_frame_s": (
                round(erste_konsistente_praesentation[0], 6)
                if erste_konsistente_praesentation[0] is not None else None),
            "solverfehler": (
                str(statik["fehler"]) if statik["fehler"] is not None else None),
            "fehler": (
                None if statik["fertig"]
                and statik["fehler"] is None
                and erste_konsistente_praesentation[0] is not None
                else "Parameteränderung, Solver oder sichtbare Aktualisierung "
                     "nicht innerhalb von 60 s abgeschlossen."),
        }
        return {"parameter_change": result}

    verspaetungen = []
    ereignis_signal = EreignisSignal()
    ereignis_signal.impuls.connect(
        lambda gesendet: verspaetungen.append(
            max(0.0, time.perf_counter() - gesendet)),
        Qt.ConnectionType.QueuedConnection)
    stop_probe = threading.Event()

    def ereignis_senden():
        while not stop_probe.wait(0.05):
            ereignis_signal.impuls.emit(time.perf_counter())

    ereignis_thread = threading.Thread(
        target=ereignis_senden, name="gui-event-probe", daemon=True)

    def batch_abgeschlossen(
            _generation, _sequenz, _koerper, _zustand, _ergebnis,
            batch_fehler, dauer):
        if batch_fehler is None:
            batchzeiten.append(float(dauer))
        else:
            fehler.append(str(batch_fehler))

    fenster._echtzeit_signale.abgeschlossen.connect(batch_abgeschlossen)
    angefordert_start = fenster._echtzeit_angefordert_s
    berechnet_start = fenster._echtzeit_berechnet_s
    fenster._btn_echtzeit.click()
    laufzeit_start = time.perf_counter()
    rueckstand_zeitreihe = []

    def rueckstand_aufnehmen():
        rueckstand_zeitreihe.append((
            time.perf_counter() - laufzeit_start,
            fenster._echtzeit_rueckstand_s(),
            fenster._echtzeit_angefordert_s,
            fenster._echtzeit_berechnet_s))

    rueckstand_timer = QTimer(fenster)
    rueckstand_timer.setInterval(1000)
    rueckstand_timer.timeout.connect(rueckstand_aufnehmen)
    rueckstand_timer.start()
    ereignis_thread.start()
    praesentiert_start = len(praesentiert)

    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest
    ziel = plotter.interactor if hasattr(plotter.interactor, "mapFromGlobal") \
        else plotter
    mitte = QPoint(ziel.width() // 2, ziel.height() // 2)
    stimuli_gesendet = [0]

    def eingabe_senden():
        # Mausziehen dreht die Kamera; Reaktion = erster Frame mit Änderung.
        if stimulus["zeit"] is not None:
            return
        stimulus["kamera"] = kamera_zustand()
        stimulus["zeit"] = time.perf_counter()
        stimuli_gesendet[0] += 1
        QTest.mousePress(ziel, Qt.MouseButton.LeftButton, pos=mitte)
        QTest.mouseMove(ziel, mitte + QPoint(12, 6))
        QTest.mouseRelease(
            ziel, Qt.MouseButton.LeftButton, pos=mitte + QPoint(12, 6))

    eingabe_timer = QTimer(fenster)
    eingabe_timer.setInterval(1000)
    eingabe_timer.timeout.connect(eingabe_senden)
    eingabe_timer.start()
    _warte(app, round(duration_s * 1000))
    eingabe_timer.stop()
    laufzeit = time.perf_counter() - laufzeit_start
    frames = praesentiert[praesentiert_start:]
    frame_abstaende = [b - a for a, b in zip(frames, frames[1:])]
    praesentiert_fps = len(frames) / laufzeit if laufzeit > 0 else None
    rueckstand_timer.stop()
    rueckstand_aufnehmen()
    stop_probe.set()
    ereignis_thread.join(timeout=1.0)

    renderaufrufe_pro_s = len(renderzeiten) / laufzeit if laufzeit > 0 else 0.0
    trend_messfenster = [
        punkt for punkt in rueckstand_zeitreihe
        if punkt[0] >= max(0.0, laufzeit - 300.0)]
    trend_s_pro_s = None
    if len(trend_messfenster) >= 2:
        trend_s_pro_s = float(np.polyfit(
            [punkt[0] for punkt in trend_messfenster],
            [punkt[1] for punkt in trend_messfenster], 1)[0])
    angefordert_s = fenster._echtzeit_angefordert_s - angefordert_start
    berechnet_s = fenster._echtzeit_berechnet_s - berechnet_start
    status = {
        "szene": scene,
        "hydrostatik_backend": backend,
        "startup_gui_bedienbar_s": round(gui_bedienbar_s, 3),
        "startup_erste_3d_szene_praesentiert_s": (
            round(first_scene_presented_s[0], 3)
            if first_scene_presented_s[0] is not None else None),
        "python": platform.python_version(),
        "plattform": platform.platform(),
        "messdauer_s": round(laufzeit, 3),
        "warmup_s": warmup_s,
        "aktive_layer": {
            name: bridge.layer_ist_an(layer)
            for name, layer in pflicht_layer.items()
        },
        "exakte_hydrostatik_jeder_schritt": backend == "exakt_union",
        "prozess_worker": fenster._echtzeit_prozess_executor is not None,
        "renderaufrufe_pro_s": round(renderaufrufe_pro_s, 2),
        "qpa_plattform": app.platformName(),
        "tatsaechlich_praesentierte_fps": (
            round(praesentiert_fps, 2) if praesentiert_fps else None),
        "frameabstand_p95_ms": (
            round(1000 * _perzentil(frame_abstaende, 0.95), 3)
            if frame_abstaende else None),
        "frameabstand_max_ms": (
            round(1000 * max(frame_abstaende), 3)
            if frame_abstaende else None),
        "eingaben_gesendet": stimuli_gesendet[0],
        "eingaben_mit_reaktion": len(reaktionen),
        "eingabe_bis_praesentierter_frame_ms": (
            round(1000 * _perzentil(reaktionen, 0.95), 3)
            if reaktionen else None),
        "eingabe_bis_praesentierter_frame_median_ms": (
            round(1000 * statistics.median(reaktionen), 3)
            if reaktionen else None),
        "praesentierungszeitpunkt_verfuegbar": bool(frames),
        # Nur auf einer echten Plattform (nicht offscreen) gültig.
        "eingabelatenz_abnahme_gueltig": bool(
            reaktionen and app.platformName() != "offscreen"),
        "eingabelatenz_messhinweis": (
            "Präsentierung = VTK-EndEvent nach SwapBuffers plus "
            "WaitForCompletion; Latenz = simulierte Mausdrehung bis erster "
            "Frame mit geänderter Kameraposition. Offscreen ungültig."),
        "erfolgreiche_renderaufrufe": len(renderzeiten),
        "pose_median_ms": round(
            1000 * statistics.median(posezeiten), 3) if posezeiten else None,
        "pose_p95_ms": (
            round(1000 * _perzentil(posezeiten, 0.95), 3)
            if posezeiten else None),
        "pose_max_ms": (
            round(1000 * max(posezeiten), 3) if posezeiten else None),
        "render_median_ms": round(
            1000 * statistics.median(renderzeiten), 3)
            if renderzeiten else None,
        "render_p95_ms": (
            round(1000 * _perzentil(renderzeiten, 0.95), 3)
            if renderzeiten else None),
        "render_max_ms": (
            round(1000 * max(renderzeiten), 3) if renderzeiten else None),
        "ereignisprobe_anzahl": len(verspaetungen),
        "qt_event_dispatch_p95_ms": (
            round(1000 * _perzentil(verspaetungen, 0.95), 3)
            if verspaetungen else None),
        "qt_event_dispatch_max_ms": (
            round(1000 * max(verspaetungen), 3) if verspaetungen else None),
        "physik_batches": len(batchzeiten),
        "batch_median_ms": (
            round(1000 * statistics.median(batchzeiten), 3)
            if batchzeiten else None),
        "batch_p95_ms": (
            round(1000 * _perzentil(batchzeiten, 0.95), 3)
            if batchzeiten else None),
        "physik_rueckstand": fenster._rueckstand_text(),
        "angeforderte_simulationszeit_s": angefordert_s,
        "berechnete_simulationszeit_s": berechnet_s,
        "physik_durchsatz_sim_s_pro_wand_s": (
            berechnet_s / laufzeit if laufzeit > 0.0 else 0.0),
        "automatische_ueberlastpause": (
            fenster._echtzeit_modus == "automatisch_pausiert"),
        "rueckstand_p95_s": (
            _perzentil([punkt[1] for punkt in rueckstand_zeitreihe], 0.95)
            if rueckstand_zeitreihe else None),
        "rueckstand_max_s": (
            max(punkt[1] for punkt in rueckstand_zeitreihe)
            if rueckstand_zeitreihe else None),
        "rueckstand_zeitreihe_s": [
            {
                "wandzeit_s": round(punkt[0], 3),
                "rueckstand_s": round(punkt[1], 6),
                "angefordert_s": round(punkt[2], 6),
                "berechnet_s": round(punkt[3], 6),
            }
            for punkt in rueckstand_zeitreihe
        ],
        "trendfenster_s": 300,
        "rueckstand_trend_s_pro_s": trend_s_pro_s,
        "fehler": fehler,
    }
    _fenster_schliessen(app, fenster, hauptfenster_mod)
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default="yacht1")
    parser.add_argument("--warmup", type=float, default=30.0)
    parser.add_argument("--duration", type=float, default=600.0)
    parser.add_argument(
        "--backend", choices=(
            "exakt_union", "voxel_koerperfest", "voxel_opencl"),
        default="exakt_union",
        help="Fester Echtzeit-Hydrostatikpfad für einen gezielten Vergleich")
    parser.add_argument(
        "--measure-parameter-change", action="store_true",
        help="Misst Material-/Masseneigenschaft bis zum konsistenten 3D-Frame")
    args = parser.parse_args(argv)
    if (not all(math.isfinite(wert) for wert in (args.warmup, args.duration))
            or args.warmup < 0.0
            or args.duration <= 0.0):
        parser.error("Warmup muss nicht-negativ und Dauer positiv sein.")
    ergebnis = benchmark(
        args.scene, args.warmup, args.duration, backend=args.backend,
        measure_parameter_change=args.measure_parameter_change)
    import gc
    gc.collect()
    print(json.dumps(ergebnis, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
