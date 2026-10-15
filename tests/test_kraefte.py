"""Block R: Kraeftebild (P5c Phase C) - alle Referenzen analytisch."""
import numpy as np

from segelphysik.core import kraefte_bild as kb
from segelphysik.core.overlays import (LayerRegistry, LAYER_KRAEFTE,
                                       LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                                       LAYER_MOMENTE)


class _V:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = float(x), float(y), float(z)
    def as_array(self):
        return np.array([self.x, self.y, self.z])


class _Erg:
    """Stub mit derselben Oberflaeche wie Auftriebsergebnis."""
    def __init__(self, V, K, FA_z, M):
        self.V_tauch = float(V)
        self.K = _V(*K)
        self.F_A = _V(0.0, 0.0, FA_z)
        self.M = _V(*M)


def _wirft(funktion, *args):
    """Shim fuer pytest.raises: True, wenn eine Exception geworfen wird."""
    try:
        funktion(*args)
    except Exception:
        return True
    return False


def test_r1_registry_kraefte_layer():
    reg = LayerRegistry()
    assert set(reg.zustand()) == {LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                                  LAYER_KRAEFTE, LAYER_MOMENTE}
    assert not reg.ist_an(LAYER_KRAEFTE)
    assert reg.umschalten(LAYER_KRAEFTE) is True
    assert reg.ist_an(LAYER_KRAEFTE)
    assert reg.umschalten(LAYER_KRAEFTE) is False


def test_r2_pfeil_daten_analytisch():
    p = kb.pfeil_daten((1.0, 2.0, 3.0), (0.0, 0.0, -4.0))
    assert abs(p["laenge"] - 4.0) < 1e-12
    assert np.allclose(p["richtung"], (0.0, 0.0, -1.0))
    assert np.allclose(p["schaft_ende"], (1.0, 2.0, 0.0))
    assert np.allclose(p["spitze"], (1.0, 2.0, -1.0))
    assert abs(p["kopf_laenge"] - 1.0) < 1e-12
    assert abs(p["kopf_radius"] - 0.32) < 1e-12


def test_r3_nullvektor_fehler():
    assert _wirft(kb.pfeil_daten, (0, 0, 0), (0, 0, 0))


def test_r4_skala_fuellt_referenz():
    masse, g = 100.0, 9.80665
    skala = kb.skala_waehlen(masse, g, referenz_laenge=2.0)
    assert abs(masse * g * skala - 1.5) < 1e-12   # 0.75 * 2.0


def test_r5_kraft_pfeile_gleichgewicht():
    erg = _Erg(1.0, (0.1, 0.2, 0.3), 981.0, (0, 0, 0))
    fg, fa = kb.kraft_pfeile(erg, (0, 0, 0), masse=100.0, g=9.81, skala=1e-3)
    assert np.allclose(fg["start"], (0, 0, 0))
    assert np.allclose(fa["start"], (0.1, 0.2, 0.3))
    assert np.allclose(fg["richtung"], (0, 0, -1))
    assert np.allclose(fa["richtung"], (0, 0, 1))
    assert abs(fg["laenge"] - 0.981) < 1e-12
    assert abs(fa["laenge"] - 0.981) < 1e-12


def test_r6_hebelarm_endpunkte():
    a, b = kb.hebelarm_segment((1, 2, 3), (0, 0, 0))
    assert np.allclose(a, (1, 2, 3)) and np.allclose(b, (0, 0, 0))


def test_r7_text_zeile_format():
    zeile = kb.text_zeile(_Erg(2.5, (0, 0, 0), 24516.6, (3, 4, 0)))
    assert "V_tauch=" in zeile and "F_A=" in zeile and "|M|=" in zeile
    assert "2.500" in zeile and "24516.6" in zeile and "5.0" in zeile


def test_r8_gemeinsame_skala_d1():
    """Verhaeltnis der Pfeillaengen = Verhaeltnis der Kraefte (D1)."""
    erg = _Erg(1.0, (0, 0, 0), 500.0 * 9.81 * 0.8, (0, 0, 0))
    fg, fa = kb.kraft_pfeile(erg, (0, 0, 0), 500.0, 9.81, skala=1e-3)
    verhaeltnis = fa["laenge"] / fg["laenge"]
    assert abs(verhaeltnis - 0.8) < 1e-12


def test_r9_restkraft_sichtbar():
    """D1-Kern: Restkraft bleibt als Pfeillaengen-Differenz sichtbar."""
    erg = _Erg(1.0, (0, 0, 0), 500.0 * 9.81 * 1.1, (0, 0, 0))
    fg, fa = kb.kraft_pfeile(erg, (0, 0, 0), 500.0, 9.81, skala=1e-3)
    assert fa["laenge"] > fg["laenge"]      # Auftrieb ueberwiegt -> Boot steigt


def test_r10_bridge_kraefte_api_ohne_pyvista():
    """Bruecke-API: Namen, Datenfluss und sicheres Entfernen ohne Plotter."""
    from segelphysik.grafik_bruecke import GrafikBruecke
    b = GrafikBruecke()
    assert b._kraefte_namen("boot") == ["kraefte_boot_fg", "kraefte_boot_fa",
                                        "kraefte_boot_arm", "kraefte_boot_moment"]
    erg = _Erg(1.0, (0, 0, 0), 981.0, (0, 0, 0))
    b.kraefte_daten_setzen("boot", erg, 100.0, 9.81, 1e-3)
    assert "boot" in b._kraefte_daten
    b.kraefte_entfernen("boot")             # ohne Plotter: kein Absturz
    assert "boot" not in b._kraefte_daten


def test_ausgeblendeter_koerper_baut_bei_posenupdate_keine_actors_auf():
    """Objektwechsel im Echtzeitmodus: alte Pose darf den Altkoerper nicht
    wieder einblenden (Ueberlagerung)."""
    from segelphysik.grafik_bruecke import GrafikBruecke
    b = GrafikBruecke()
    aufrufe = []
    b._actors_aktualisieren = lambda *a: aufrufe.append("actors")
    b._gruppen_actors = lambda *a: aufrufe.append("gruppen")
    b._overlays_aktualisieren = lambda *a: aufrufe.append("overlays")
    punkte = np.zeros((3, 3))

    class _Pd(dict):
        points = punkte

    pd = _Pd(referenz_punkte=punkte)
    b._koerper["alt"] = {"pd": pd, "position": np.zeros(3), "aktiv": False}
    assert b.physik_pose_6dof_setzen("alt", np.eye(3), np.array([1., 2., 3.]))
    assert aufrufe == []
    assert np.allclose(b._koerper["alt"]["position"], (1., 2., 3.))

    b._koerper["alt"]["aktiv"] = True
    b.physik_pose_6dof_setzen("alt", np.eye(3), np.array([1., 2., 3.]))
    assert aufrufe == ["actors", "overlays"]