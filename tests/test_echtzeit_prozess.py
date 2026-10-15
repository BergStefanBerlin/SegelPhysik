from types import SimpleNamespace

from segelphysik.core import echtzeit_prozess


def test_worker_initialisierung_uebernimmt_feste_hydrostatikzuordnung(
        monkeypatch):
    aufrufe = []

    def kraftfunktion(_koerper, **kwargs):
        aufrufe.append(kwargs)
        return lambda *_args, **_kwargs: None

    monkeypatch.setattr(
        "segelphysik.core.auftrieb.baue_kraftfunktion_6dof",
        kraftfunktion)
    monkeypatch.setattr(
        "segelphysik.core.kraftmodell.baue_kraftmodell",
        lambda funktion, _physik: funktion)
    monkeypatch.setattr(
        "segelphysik.core.kraftmodell.KraftmodellMitHydroCache",
        lambda funktion, intervall: funktion)

    koerper = SimpleNamespace(
        masse=3.0, traegheitstensor=((1.0, 0.0, 0.0),
                                     (0.0, 1.0, 0.0),
                                     (0.0, 0.0, 1.0)))
    physik = SimpleNamespace(dt_s=0.01, g_m_pro_s2=9.81)
    echtzeit_prozess.initialisieren(
        koerper, 1000.0, physik, hydrostatik_pfad="voxel_opencl")

    assert aufrufe == [{
        "rho_w": 1000.0, "g": 9.81, "pfad": "voxel_opencl"}]
