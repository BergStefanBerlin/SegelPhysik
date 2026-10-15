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


def benchmark(scene, warmup_s, duration_s, backend="exakt_union"):
    from PySide6.QtCore import QObject, Qt, QTimer, Signal
    from PySide6.QtWidgets import QApplication

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
    fenster.show()
    app.processEvents()

    bridge = fenster._bruecke
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
    _warte(app, round(warmup_s * 1000))

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
    _warte(app, round(duration_s * 1000))
    laufzeit = time.perf_counter() - laufzeit_start
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
        "tatsaechlich_praesentierte_fps": None,
        "eingabe_bis_praesentierter_frame_ms": None,
        "praesentierungszeitpunkt_verfuegbar": False,
        "eingabelatenz_abnahme_gueltig": False,
        "eingabelatenz_messhinweis": (
            "QtInteractor stellt keinen belastbaren Präsentierungszeitpunkt "
            "für den Frame mit sichtbarer Eingabereaktion bereit."),
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
    fenster._zeit_pausieren()
    fenster.close()
    app.processEvents()
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
    args = parser.parse_args(argv)
    if (not all(math.isfinite(wert) for wert in (args.warmup, args.duration))
            or args.warmup < 0.0
            or args.duration <= 0.0):
        parser.error("Warmup muss nicht-negativ und Dauer positiv sein.")
    ergebnis = benchmark(
        args.scene, args.warmup, args.duration, backend=args.backend)
    print(json.dumps(ergebnis, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
