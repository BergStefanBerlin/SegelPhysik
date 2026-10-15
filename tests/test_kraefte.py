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
    assert b._kraefte_namen("boot")[:4] == [
        "kraefte_boot_fg", "kraefte_boot_fa",
        "kraefte_boot_arm", "kraefte_boot_moment"]
    assert len(b._kraefte_namen("boot")) == 9
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

def test_moment_bogen_achse_liegt_senkrecht_zur_achse():
    import numpy as np
    from segelphysik.core import kraefte_bild as kb

    for achse in (0, 1, 2):
        bogen = kb.moment_bogen_achse(5.0, (1.0, 2.0, 3.0), 0.5, achse)
        assert np.allclose(bogen["punkte"][:, achse], (1.0, 2.0, 3.0)[achse])
        assert abs(bogen["richtung"][achse]) < 1e-12
    assert kb.moment_bogen_achse(0.0, (0, 0, 0), 1.0, 1) is None


def test_zusatz_pfeile_zeigen_querkraefte_und_resultierende():
    import numpy as np
    from types import SimpleNamespace
    from segelphysik.core import kraefte_bild as kb
    from segelphysik.core.auftrieb import Vektor

    erg = SimpleNamespace(
        F_gesamt=Vektor((30.0, -20.0, 1000.0)), F_A=Vektor((0.0, 0.0, 1000.0)))
    rest, zusatz = kb.zusatz_pfeile(erg, (0, 0, 0), 100.0, 9.81, 0.01)
    assert np.allclose(zusatz["richtung"] * zusatz["laenge"],
                       np.array([30.0, -20.0, 0.0]) * 0.01)
    assert rest["laenge"] > 0.0
    gleichgewicht = SimpleNamespace(
        F_gesamt=Vektor((0.0, 0.0, 981.0)), F_A=Vektor((0.0, 0.0, 981.0)))
    assert kb.zusatz_pfeile(gleichgewicht, (0, 0, 0), 100.0, 9.81, 0.01) == (
        None, None)

def test_fremdkraft_wirkt_als_kraft_und_moment_um_den_schwerpunkt():
    import numpy as np
    from segelphysik.core.auftrieb import Auftriebsergebnis
    from segelphysik.core.kraftmodell import Kraftmodell

    def hydro(lage, v=None, omega=None):
        return Auftriebsergebnis(1.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1000.0),
                                 (0.0, 0.0, 0.0))

    modell = Kraftmodell(hydro)
    lage = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0))
    ohne = modell(lage)
    modell.fremdkraft_setzen(((0.0, 100.0, 0.0), (0.0, 0.0, 2.0)))
    mit = modell(lage)

    assert np.allclose(ohne.F_gesamt.as_array(), (0.0, 0.0, 1000.0))
    assert np.allclose(mit.F_gesamt.as_array(), (0.0, 100.0, 1000.0))
    # r=(0,0,2) x F=(0,100,0) = (-200, 0, 0)
    assert np.allclose(mit.M_gesamt.as_array(), (-200.0, 0.0, 0.0))
    modell.fremdkraft_setzen(None)
    assert np.allclose(modell(lage).F_gesamt.as_array(), (0.0, 0.0, 1000.0))


def test_fremdkraft_angriffspunkt_dreht_mit_dem_koerper():
    import numpy as np
    from segelphysik.core.auftrieb import Auftriebsergebnis
    from segelphysik.core.kraftmodell import Kraftmodell

    def hydro(lage, v=None, omega=None):
        return Auftriebsergebnis(1.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                                 (0.0, 0.0, 0.0))

    modell = Kraftmodell(hydro)
    modell.fremdkraft_setzen(((0.0, 0.0, 10.0), (1.0, 0.0, 0.0)))
    w = np.sqrt(0.5)
    # 90 Grad um z: Angriffspunkt (1,0,0) -> (0,1,0); (0,1,0) x (0,0,10) = (10,0,0)
    erg = modell(((0.0, 0.0, 0.0), (w, 0.0, 0.0, w)))
    assert np.allclose(erg.M_gesamt.as_array(), (10.0, 0.0, 0.0), atol=1e-9)