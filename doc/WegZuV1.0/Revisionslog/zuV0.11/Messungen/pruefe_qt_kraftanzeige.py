"""Begrenzte reale Qt-/VTK-Bedienprobe mit isolierten Einstellungen."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import gc
import json
from pathlib import Path
import sys
import tempfile
import time
import tracemalloc
from types import SimpleNamespace

import numpy as np
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication
from pyvistaqt import QtInteractor

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "code" / "python"))

from segelphysik.core.auftrieb import Auftriebsergebnis
from segelphysik.core.einstellungen import Einstellungen
from segelphysik.core.koerper import Koerper
from segelphysik.core.koerper_formen import build_box
from segelphysik.core.kraftmodell import Kraftmodell
from segelphysik.core.overlays import LAYER_KRAEFTE, LAYER_MOMENTE
from segelphysik.grafik_bruecke import GrafikBruecke
from segelphysik.gui.hauptfenster import HauptFenster


class _Prozessspeicher(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        *[(name, ctypes.c_size_t) for name in (
            "PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
            "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
            "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")],
    ]


def prozessspeicher():
    """Windows-Prozesswerte inklusive Python, VTK und nativen Allokationen."""
    if sys.platform != "win32":
        raise RuntimeError("Die Prozessspeicherprobe verlangt Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    messen = kernel.K32GetProcessMemoryInfo
    messen.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(_Prozessspeicher), wintypes.DWORD)
    messen.restype = wintypes.BOOL
    daten = _Prozessspeicher()
    daten.cb = ctypes.sizeof(daten)
    if not messen(kernel.GetCurrentProcess(), ctypes.byref(daten), daten.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(
        private_bytes=daten.PrivateUsage,
        working_set_bytes=daten.WorkingSetSize,
        working_set_spitze_bytes=daten.PeakWorkingSetSize)


def pruefen(abbildung: Path, wechselanzahl=60):
    if wechselanzahl <= 12:
        raise ValueError("Mehr als 12 Wechsel fuer Aufwaerm- und Messzyklen erforderlich")
    app = QApplication.instance() or QApplication([])
    if app.platformName().casefold() in ("offscreen", "minimal"):
        raise RuntimeError("Diese Probe verlangt ein echtes Qt-Bildschirmfenster")
    with tempfile.TemporaryDirectory(prefix="segelphysik-sichtprobe-") as ordner:
        einstellungen = Einstellungen(str(Path(ordner) / "settings.json"))
        einstellungen.setzen("pfeil_f_a", "gestrichelt", False)
        original = Einstellungen.__dict__["laden"]
        try:
            Einstellungen.laden = classmethod(lambda cls: einstellungen)
            fenster = HauptFenster()
        finally:
            Einstellungen.laden = original
        ansicht = QtInteractor(fenster, off_screen=False)
        bruecke = GrafikBruecke()
        bruecke._plotter = ansicht
        try:
            fenster.ansicht_setzen(ansicht)
            fenster.bruecke_setzen(bruecke)
            koerper = Koerper(form=build_box(1, 1, .5), dichte=2)
            bruecke.koerper_objekt_setzen("boot", koerper)
            fenster._laufzeit_koerper["boot"] = koerper
            bruecke._layer.setzen(LAYER_KRAEFTE, True)
            bruecke._layer.setzen(LAYER_MOMENTE, True)
            modell = Kraftmodell(lambda *_a, **_kw: Auftriebsergebnis(
                .01, (0, .2, 0), (0, 0, 10), (2, 0, 0)),
                masse=koerper.masse, g=10)
            fenster._kraftbild_daten_setzen(
                bruecke, "boot", koerper, modell,
                SimpleNamespace(g_m_pro_s2=10), 0, 0,
                ergebnis=modell(((0, 0, 0), (1, 0, 0, 0))))
            snapshot = fenster._kraftanzeige_snapshots["boot"]
            fenster.resize(1250, 850)
            fenster.show()
            dock = fenster._kraefte_werte
            dock.oeffnen()
            dock.setFloating(True)
            dock.resize(1050, 650)
            ansicht.camera_position = [(2, -3, 1.6), (0, 0, 0), (0, 0, 1)]
            ansicht.enable_parallel_projection()
            ansicht.camera.parallel_scale = .8
            ansicht.camera.clipping_range = (.01, 10000)
            swaps = QSignalSpy(ansicht.frameSwapped)
            bruecke.render()
            QTest.qWait(300)
            if swaps.count() == 0:
                raise RuntimeError("Das reale Qt-Fenster hat keinen Frame ausgegeben")
            for key in ("koerperframe", "weltursprung", "komponenten"):
                QTest.mouseClick(dock.optionen[key], Qt.MouseButton.LeftButton)
                QTest.qWait(30)
                assert einstellungen.get("kraefteanzeige", key)
            index = dock.modell.index_fuer_id(("boot", "hydrostatik"))
            dock.baum.scrollTo(index)
            QTest.mouseClick(dock.baum.viewport(), Qt.MouseButton.LeftButton,
                             pos=dock.baum.visualRect(index).center())
            assert bruecke._kraftzeichner().auswahl == ("boot", "hydrostatik")
            messungen = []
            for parallel in (False, True):
                ansicht.camera.parallel_projection = parallel
                for zoom in (.6, 1.3):
                    ansicht.camera_position = [(0, -5, 0), (0, 0, 0), (0, 0, 1)]
                    ansicht.camera.parallel_scale = zoom
                    ansicht.camera.view_angle = 30 * zoom
                    ansicht.camera.clipping_range = (.01, 10000)
                    bruecke.render()
                    QTest.qWait(50)
                    actor = bruecke._koerper["boot"]["kraefte_actors"][
                        "kraefte_('boot', 'hydrostatik')_F"]
                    punkte = []
                    for punkt in actor.mapper.dataset.points:
                        welt = actor.GetMatrix().MultiplyPoint((*punkt, 1))
                        ansicht.renderer.SetWorldPoint(*welt)
                        ansicht.renderer.WorldToDisplay()
                        punkte.append(ansicht.renderer.GetDisplayPoint()[:2])
                    punkte = np.asarray(punkte) / ansicht.devicePixelRatioF()
                    grenze = bruecke._kraftpfeil_vorlage[3]
                    schaft, kopf = punkte[:grenze], punkte[grenze:]
                    masse = (np.ptp(schaft[:, 0]), np.ptp(kopf[:, 0]),
                             np.ptp(kopf[:, 1]))
                    soll = (5, 7, einstellungen.get("kraefteanzeige", "kopflaenge_px"))
                    assert all(abs(a - b) <= 1 for a, b in zip(masse, soll)), (
                        parallel, zoom, masse, soll)
                    messungen.append(dict(
                        parallel=parallel, zoom=zoom, schaft_px=float(masse[0]),
                        kopfbreite_px=float(masse[1]), kopflaenge_px=float(masse[2])))
            zeichner = bruecke._kraftzeichner()
            dock.auswaehlen(("boot", "schwerkraft"))
            bruecke.kraefte_auswahl_setzen(("boot", "schwerkraft"))
            for linie in zeichner.picklinien[("boot", "hydrostatik")]:
                for punkt in linie:
                    ansicht.renderer.SetWorldPoint(*punkt, 1)
                    ansicht.renderer.WorldToDisplay()
                    x, y, _ = ansicht.renderer.GetDisplayPoint()
                    x, y = x / ansicht.devicePixelRatioF(), y / ansicht.devicePixelRatioF()
                    if zeichner.kandidaten((x, y)) == (("boot", "hydrostatik"),):
                        QTest.mouseClick(ansicht, Qt.MouseButton.LeftButton,
                                         pos=QPoint(round(x), round(ansicht.height() - y)))
                        break
                if zeichner.auswahl == ("boot", "hydrostatik"):
                    break
            assert zeichner.auswahl == ("boot", "hydrostatik")
            assert dock._aktive_id == ("boot", "hydrostatik")
            dock.close()
            QTest.qWait(30)
            dock.oeffnen()
            QTest.qWait(100)
            assert fenster._kraftanzeige_snapshots["boot"] is snapshot
            assert bruecke.kraefte_snapshot_ermitteln("boot") is snapshot
            assert dock.modell.rowCount() == 1
            assert swaps.count() >= 2
            zeichner = bruecke._kraftzeichner()
            actors = bruecke._koerper["boot"].get("kraefte_actors", {})
            assert actors and zeichner.picklinien
            assert zeichner.labels
            tracemalloc.start()
            ressourcen = []
            bekannte_groessen = {}
            try:
                for wechsel in range(wechselanzahl):
                    fall = wechsel % 3
                    modell.fremdkraft_setzen(
                        (((0., float(fall), 0.), (0., .1, 0.)))
                        if fall else None)
                    start = time.perf_counter()
                    if wechsel % 10 == 0:
                        bruecke.koerper_objekt_setzen("boot", koerper)
                    fenster._kraftbild_daten_setzen(
                        bruecke, "boot", koerper, modell,
                        SimpleNamespace(g_m_pro_s2=10), 0, 0,
                        ergebnis=modell(((0, 0, 0), (1, 0, 0, 0))))
                    if wechsel % 10 == 0:
                        dock.close()
                        dock.oeffnen()
                    bruecke.render()
                    app.processEvents()
                    groessen = (
                        len(bruecke._koerper["boot"]["kraefte_actors"]),
                        len(zeichner.labels), len(zeichner.label_linien),
                        len(zeichner.picklinien),
                        ansicht.renderer.GetActors().GetNumberOfItems())
                    if wechsel >= 12:
                        if fall in bekannte_groessen:
                            assert groessen == bekannte_groessen[fall], (
                                wechsel, groessen, bekannte_groessen[fall])
                        bekannte_groessen[fall] = groessen
                        assert len(fenster._kraftanzeige_snapshots) == 1
                        assert len(bruecke._kraefte_daten) == 1
                        assert len(zeichner.generationen) == 1
                        assert len(zeichner.skalen) == 1
                        assert dock._snapshots[0] is (
                            fenster._kraftanzeige_snapshots["boot"])
                        gc.collect()
                        aktuell, spitze = tracemalloc.get_traced_memory()
                        ressourcen.append(dict(
                            wechsel=wechsel, fall=fall, groessen=groessen,
                            python_bytes=aktuell, python_spitze_bytes=spitze,
                            **prozessspeicher(),
                            update_render_ms=(time.perf_counter() - start) * 1000))
            finally:
                tracemalloc.stop()
            abbildung.with_suffix(".json").write_text(json.dumps(dict(
                plattform=app.platformName(), dpr=ansicht.devicePixelRatioF(),
                swaps=swaps.count(), pixelmessungen=messungen,
                ressourcenwechsel=ressourcen,
                ressourcenhinweis=(
                    f"{wechselanzahl} wechselnde Snapshotupdates, "
                    "davon 12 Aufwaermzyklen; "
                    f"{(wechselanzahl + 9) // 10} Koerperersetzungen und "
                    "Wiedereroeffnungen. Windows-Prozessspeicher inklusive "
                    "nativer Allokationen; tracemalloc und Messpunktliste "
                    "beeinflussen den Speicher. Keine Leckfreiheits- oder "
                    "Leistungsfreigabe. "
                    "Updatezeit einschliesslich Qt-Events und GC."),
                hinweis="QT_SCALE_FACTOR, kein physischer Monitorwechsel"),
                indent=2), encoding="utf-8")
            if not dock.grab().save(str(abbildung)):
                raise RuntimeError("Qt-Bildschirmbeleg konnte nicht gespeichert werden")
            ansicht.screenshot(str(abbildung.with_name(
                abbildung.stem + "_vtk.png")))
            print(
                f"Qt={app.platformName()}, DPR={ansicht.devicePixelRatioF()}, "
                f"Swaps={swaps.count()}, Komponenten-/Bezug-/Framewechsel, "
                "Kamera und Wiedereroeffnen ohne neue Physikauswertung bestanden.")
        finally:
            fenster.close()
            ansicht.close()
            app.processEvents()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abbildung", type=Path, required=True)
    parser.add_argument("--wechsel", type=int, default=60)
    argumente = parser.parse_args()
    pruefen(argumente.abbildung, argumente.wechsel)
