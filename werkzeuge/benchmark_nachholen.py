"""Misst die Nachholrate nach künstlichem Rückstand (Gate: >= 1,25 s/s)."""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def messen(scene, rueckstand_s, wiederholungen):
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from segelphysik.gui.app import _szene_einbetten, welt_laden
    from segelphysik.gui.baum import sichtbarkeit_setzen
    from segelphysik.gui.hauptfenster import HauptFenster

    welt = welt_laden()
    sichtbarkeit_setzen(welt, scene)
    fenster = HauptFenster()
    fenster.baum_setzen(welt)
    _szene_einbetten(fenster)
    fenster.show()
    app.processEvents()

    def warte(sekunden, bedingung=None):
        ende = time.perf_counter() + sekunden
        while time.perf_counter() < ende:
            app.processEvents()
            if bedingung is not None and bedingung():
                return True
            time.sleep(0.002)
        return False

    fenster._btn_echtzeit.click()
    warte(5.0)
    ergebnisse = []
    for _ in range(wiederholungen):
        fenster._zeit_pausieren()
        fenster._echtzeit_angefordert_s += rueckstand_s
        fenster._echtzeit_akkumulator += rueckstand_s
        start = time.perf_counter()
        fenster._zeit_fortsetzen()
        modus_nachholen = fenster._echtzeit_modus == "nachholen"
        fertig = warte(
            60.0, lambda: fenster._echtzeit_modus != "nachholen")
        dauer = time.perf_counter() - start
        ergebnisse.append({
            "nachholmodus_gestartet": modus_nachholen,
            "abgeschlossen": fertig,
            "dauer_s": round(dauer, 3),
            "rate_gesamt_s_pro_s": fenster._solver_werte[
                "Nachholrate gesamt"].text(1),
            "gate": fenster._solver_werte["Nachholrate ≥1,25"].text(1),
            "fenster_raten": fenster._solver_werte[
                "Nachholfenster s/s"].text(1),
            "rueckstand_danach_s": round(fenster._echtzeit_rueckstand_s(), 4),
        })
        warte(2.0)
    fenster._zeit_pausieren()
    fenster.close()
    app.processEvents()
    return ergebnisse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", default="yacht1")
    parser.add_argument("--rueckstand", type=float, default=3.0)
    parser.add_argument("--wiederholungen", type=int, default=3)
    args = parser.parse_args(argv)
    print(json.dumps(
        messen(args.scene, args.rueckstand, args.wiederholungen),
        indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
