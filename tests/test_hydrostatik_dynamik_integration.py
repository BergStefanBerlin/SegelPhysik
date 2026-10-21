"""Hydrostatik dynamik integration: bestehende Referenzvertraege."""
from types import SimpleNamespace
import pytest
from segelphysik.core.dynamik import Bewegungszustand, schritt

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(("start_z", "start_phi"), [
    (0.1, 0.1),
    (0.2, -0.15),
    (-0.1, 0.2),
])
def test_hydrostatik_dynamik_mundet_in_statische_solverlage(
        start_z, start_phi):
    import numpy as np

    from segelphysik.core.auftrieb import baue_kraftfunktion
    from segelphysik.core.koerper_formen import build_box
    from segelphysik.core.statisch_robust import loese_robust

    masse, g = 8000.0, 9.81
    traegheit_xx = masse * (4.0 ** 2 + 2.0 ** 2) / 12.0
    koerper = SimpleNamespace(
        blatt_meshes=[build_box(2.0, 4.0, 2.0)],
        r_S=np.zeros(3))
    kraft = baue_kraftfunktion(
        koerper, rho_w=1000.0, g=g, pfad="exakt")
    statisch = loese_robust(kraft, masse, g, start=(0.1, 0.1))

    zustand = Bewegungszustand(z=start_z, phi=start_phi)
    for _ in range(800):
        zustand = schritt(
            zustand, kraft, masse, traegheit_xx, 0.01, g,
            daempfung_tauchung=20000.0,
            daempfung_kraengung=30000.0)

    kraefte = kraft((zustand.z, zustand.phi, 0.0))
    assert zustand.z == pytest.approx(statisch["z"], abs=1e-4)
    assert zustand.phi == pytest.approx(statisch["phi"], abs=1e-4)
    assert abs(kraefte.F_A.z - masse * g) < 2.0
    assert abs(kraefte.M.x) < 2.0


def test_yacht_dynamik_naehert_sich_union_solvergleichgewicht():
    from segelphysik.core.auftrieb import baue_kraftfunktion
    from segelphysik.core.fabriken import baue_summenkoerper
    from segelphysik.core.konfig_lader import lade_konfig, lade_physik
    from segelphysik.core.statisch_robust import loese_robust
    from segelphysik.gui.baum import aktive_blaetter, finde, welt_aus_konfig

    konfiguration = lade_konfig()
    physik = lade_physik(konfiguration.ordner)
    welt = welt_aus_konfig(konfiguration)
    yacht_knoten = finde(welt, "yacht1")
    koerper, _ = baue_summenkoerper(
        konfiguration, "yacht1",
        aktive_blaetter=aktive_blaetter(yacht_knoten))
    kraft = baue_kraftfunktion(
        koerper, rho_w=konfiguration.wasser_dichte(),
        g=physik.g_m_pro_s2, pfad="exakt_union")
    statisch = loese_robust(
        kraft, koerper.masse, g=physik.g_m_pro_s2,
        start=(-0.14, 0.15))

    zustand = Bewegungszustand(
        z=statisch["z"] + 0.01, phi=statisch["phi"] + 0.01)
    for _ in range(200):
        zustand = schritt(
            zustand, kraft, koerper.masse,
            koerper.traegheitstensor[0, 0], physik.dt_s,
            physik.g_m_pro_s2, physik.daempfung_tauchung,
            physik.daempfung_kraengung)

    kraefte = kraft((zustand.z, zustand.phi, 0.0))
    assert abs(zustand.z - statisch["z"]) < 0.002
    assert abs(zustand.phi - statisch["phi"]) < 0.01
    assert abs(kraefte.F_A.z - koerper.masse * physik.g_m_pro_s2) < 20.0
    assert abs(kraefte.M.x) < 15.0
