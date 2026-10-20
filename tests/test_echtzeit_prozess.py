import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from segelphysik.core import echtzeit_prozess
from segelphysik.core.koerper import KoerperSnapshot


def test_worker_initialisierung_uebernimmt_feste_hydrostatikzuordnung(
        monkeypatch):
    aufrufe = []
    kraftmodell_aufrufe = []

    def kraftfunktion(_koerper, **kwargs):
        aufrufe.append(kwargs)
        return lambda *_args, **_kwargs: None

    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion_6dof",
        kraftfunktion)
    monkeypatch.setattr(
        "segelphysik.core.kraftmodell.baue_kraftmodell",
        lambda funktion, _physik, **kwargs: (
            kraftmodell_aufrufe.append(kwargs) or funktion))
    monkeypatch.setattr(
        "segelphysik.core.kraftmodell.KraftmodellMitHydroCache",
        lambda funktion, intervall: funktion)

    koerper = SimpleNamespace(
        masse=3.0, traegheitstensor=((1.0, 0.0, 0.0),
                                     (0.0, 1.0, 0.0),
                                     (0.0, 0.0, 1.0)))
    physik = SimpleNamespace(
        dt_s=0.01, g_m_pro_s2=9.81,
        fluidgeschwindigkeit=(0.0, 0.0, 0.0),
        fluidwinkelgeschwindigkeit=(0.0, 0.0, 0.0))
    echtzeit_prozess.initialisieren(
        koerper, 1000.0, physik, hydrostatik_pfad="voxel_opencl")

    assert aufrufe == [{
        "rho_w": 1000.0, "g": 9.81, "pfad": "voxel_opencl"}]
    assert kraftmodell_aufrufe == [{
        "masse": 3.0, "g": 9.81, "hydrodynamik": None}]


def test_worker_initialisierung_uebernimmt_generischen_cd(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "python")
    aufrufe = []
    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion_6dof",
        lambda *_args, **_kwargs: lambda *_a, **_k: None)
    monkeypatch.setattr(
        "segelphysik.core.hydrodynamik.HydrodynamikModell.aus_koerper",
        lambda _koerper, **kwargs: aufrufe.append(kwargs) or None)
    monkeypatch.setattr(
        "segelphysik.core.kraftmodell.baue_kraftmodell",
        lambda funktion, _physik, **_kwargs: funktion)
    monkeypatch.setattr(
        "segelphysik.core.kraftmodell.KraftmodellMitHydroCache",
        lambda funktion, intervall: funktion)

    koerper = SimpleNamespace(
        masse=3.0, traegheitstensor=((1.0, 0.0, 0.0),
                                     (0.0, 1.0, 0.0),
                                     (0.0, 0.0, 1.0)))
    physik = SimpleNamespace(
        dt_s=0.01, g_m_pro_s2=9.81,
        fluidgeschwindigkeit=(0.0, 0.0, 0.0),
        fluidwinkelgeschwindigkeit=(0.0, 0.0, 0.0))
    echtzeit_prozess.initialisieren(
        koerper, 1000.0, physik, cd_volumenkoerper=1.05)

    assert aufrufe[0]["cd_volumenkoerper"] == 1.05


def test_gui_erstellt_prozessworker_fuer_unveraenderlichen_koerpersnapshot(
        monkeypatch):
    from PySide6.QtWidgets import QApplication

    from segelphysik.gui import hauptfenster
    from segelphysik.gui.hauptfenster import HauptFenster

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        QApplication, "platformName", lambda: "windows")
    snapshot = KoerperSnapshot(
        masse=1.0,
        traegheitstensor=((1.0, 0.0, 0.0),
                          (0.0, 1.0, 0.0),
                          (0.0, 0.0, 1.0)),
        blatt_meshes=(),
        r_S=(0.0, 0.0, 0.0),
        zustand=None,
        version=0)
    erstellte_executor = []

    class FakeExecutor:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.beendet = False
            erstellte_executor.append(self)

        def shutdown(self, **_kwargs):
            self.beendet = True

    monkeypatch.setattr(
        "concurrent.futures.ProcessPoolExecutor", FakeExecutor)
    fenster = HauptFenster()
    try:
        executor = fenster._echtzeit_prozess_pool_aktualisieren(
            snapshot, 1000.0,
            SimpleNamespace(g_m_pro_s2=9.81, dt_s=0.004),
            "exakt_union", cd_volumenkoerper=1.05)

        assert executor is erstellte_executor[0]
        assert executor.kwargs["max_workers"] == 1
        assert executor.kwargs["initargs"][0] is snapshot
        assert executor.kwargs["initargs"][-1] == 1.05
    finally:
        fenster.close()
        app.processEvents()
    assert erstellte_executor[0].beendet
