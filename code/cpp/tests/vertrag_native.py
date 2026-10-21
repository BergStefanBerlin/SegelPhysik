"""Explizite Kandidatentests in der gesonderten nativen Testumgebung."""
import gc
import threading

import numpy as np
import pytest

import _segelphysik_native as native

pytestmark = [pytest.mark.native, pytest.mark.integration]


def zustand_array():
    werte = np.arange(13, dtype=np.float64)
    werte[3:7] = (1., 0., 0., 0.)
    return werte


def mesh():
    return native.Mesh(
        np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]),
        np.array([[0, 1, 2]], dtype=np.int64), "blatt", "rumpf", True)


def wrench(frame="simulationsframe"):
    return native.Wrench(frame, np.zeros(3), np.array([1., 2., 3.]), np.zeros(3))


def test_abi_und_datenpfad_sind_keine_behauptete_volle_physik():
    assert native.ABI_VERSION == 1
    assert native.RECHENPFAD == "cpp/datenschicht"
    assert not hasattr(native, "hallo")
    assert not hasattr(native, "schritte_berechnen")


@pytest.mark.parametrize("layout", ["c", "gestridet", "rueckwaerts", "readonly"])
def test_zustand_kopiert_eingaben_einmal_und_ausgaben_leben_unabhaengig(layout):
    original = zustand_array()
    if layout == "gestridet":
        gross = np.zeros(26)
        gross[::2] = original
        eingabe = gross[::2]
    elif layout == "rueckwaerts":
        eingabe = original[::-1].copy()[::-1]
    else:
        eingabe = original.copy()
    if layout == "readonly":
        eingabe.setflags(write=False)
    zustand = native.Zustand(eingabe)
    if eingabe.flags.writeable:
        eingabe[:] = 0.
    del eingabe
    gc.collect()
    ergebnis = zustand.werte
    np.testing.assert_array_equal(ergebnis, original)
    ergebnis[0] = 999.
    np.testing.assert_array_equal(zustand.werte, original)
    del zustand
    gc.collect()
    assert ergebnis[0] == 999.
    assert ergebnis.dtype == np.float64 and ergebnis.flags.c_contiguous
    assert ergebnis.flags.owndata


@pytest.mark.parametrize("eingabe,fehler", [
    (np.zeros(12), ValueError), (np.zeros((1, 13)), ValueError),
    (np.zeros(13, dtype=np.float32), TypeError),
    (np.zeros(13, dtype=np.int64), TypeError), ([0.] * 13, TypeError),
    (np.zeros(13), ValueError), (np.full(13, np.nan), ValueError),
    (np.full(13, np.inf), ValueError),
])
def test_zustand_lehnt_falsche_daten_ab(eingabe, fehler):
    with pytest.raises(fehler):
        native.Zustand(eingabe)


def test_mesh_kopiert_stridepunkte_und_flaechen_ohne_python_besitz():
    p = np.arange(18, dtype=np.float64).reshape(6, 3)[::2]
    f = np.array([[0, 1, 2]], dtype=np.int64)
    erwartet = p.copy()
    m = native.Mesh(p, f, "test", "kiel", False)
    p[:] = 99.
    f[:] = 0
    del p, f
    gc.collect()
    np.testing.assert_array_equal(m.punkte, erwartet)
    np.testing.assert_array_equal(m.dreiecke, [[0, 1, 2]])
    assert m.name == "test" and m.rolle == "kiel" and not m.verdraengend
    ausgabe = m.punkte
    del m
    gc.collect()
    np.testing.assert_array_equal(ausgabe, erwartet)


@pytest.mark.parametrize("mutation", ["negativ", "zu_gross", "floatindex", "punktform", "nan"])
def test_mesh_fehler_werden_abgewiesen(mutation):
    p = np.zeros((3, 3))
    f = np.array([[0, 1, 2]], dtype=np.int64)
    if mutation == "negativ":
        f[0, 0] = -1
    elif mutation == "zu_gross":
        f[0, 0] = 3
    elif mutation == "floatindex":
        f = f.astype(np.float64)
    elif mutation == "punktform":
        p = np.zeros((3, 2))
    else:
        p[0, 0] = np.nan
    with pytest.raises((TypeError, ValueError)):
        native.Mesh(p, f)


def test_modell_haelt_eigene_meshes_und_version_ohne_veraenderbare_views():
    m = mesh()
    inertia = np.diag([1., 2., 3.])
    modell = native.Modell(2., inertia, [m], 42, np.array([0., 0., 1.]))
    inertia[:] = 0.
    del m, inertia
    gc.collect()
    assert modell.masse == 2. and modell.version == 42
    np.testing.assert_array_equal(modell.traegheit, np.diag([1., 2., 3.]))
    assert modell.meshes[0].punkte.shape == (3, 3)
    modell.meshes[0].punkte[:] = 999.
    assert modell.meshes[0].punkte[0, 0] == 0.
    with pytest.raises(AttributeError):
        modell.version = 43


@pytest.mark.parametrize("mutation", ["masse", "asymmetrisch", "negativ", "nan", "version"])
def test_modell_lehnt_ungueltige_physikdaten_ab(mutation):
    inertia = np.eye(3)
    masse, version = 1., 0
    if mutation == "masse":
        masse = 0.
    elif mutation == "asymmetrisch":
        inertia[0, 1] = 1.
    elif mutation == "negativ":
        inertia[0, 0] = -1.
    elif mutation == "nan":
        inertia[0, 0] = np.nan
    else:
        version = -1
    with pytest.raises((TypeError, ValueError)):
        native.Modell(masse, inertia, [], version, np.zeros(3))


@pytest.mark.parametrize("tensor", [np.zeros((3, 3)), np.diag([0., 1., 1.])])
def test_datenkontext_erlaubt_punktmassen_ohne_dynamikinversion(tensor):
    m = native.Modell(1., tensor, [], 0, np.zeros(3))
    np.testing.assert_array_equal(m.traegheit, tensor)


def test_parameter_halten_si_werte_und_eigene_vektoren():
    sechs = np.arange(6, dtype=np.float64)
    p = native.Parameter(1000., 9.81, .004, sechs, sechs, sechs, np.zeros(3), np.zeros(3))
    sechs[:] = 99.
    np.testing.assert_array_equal(p.linear, np.arange(6))
    np.testing.assert_array_equal(p.quadratisch, np.arange(6))
    np.testing.assert_array_equal(p.added_mass, np.arange(6))
    assert (p.rho, p.g, p.dt) == (1000., 9.81, .004)


@pytest.mark.parametrize("index,wert", [(0, 0.), (1, np.inf), (2, -1.)])
def test_parameter_ungueltige_si_skala(index, wert):
    args = [1000., 9.81, .004]
    args[index] = wert
    with pytest.raises(ValueError):
        native.Parameter(*args, np.zeros(6), np.zeros(6), np.zeros(6),
                         np.zeros(3), np.zeros(3))


@pytest.mark.parametrize("index", [0, 1, 2])
def test_parameter_negative_widerstaende_und_added_mass(index):
    args = [np.zeros(6), np.zeros(6), np.zeros(6)]
    args[index][0] = -1.
    with pytest.raises(ValueError):
        native.Parameter(1000., 9.81, .004, *args, np.zeros(3), np.zeros(3))


def test_ergebnis_behaelt_beitragsnamen_frames_und_lebt_nach_eingaben():
    z = native.Zustand(zustand_array())
    w = wrench()
    beitraege = [native.Beitrag("auftrieb", w), native.Beitrag("gewicht", w)]
    ergebnis = native.Ergebnis(
        z, 1., np.zeros(3), w, beitraege, w, np.arange(6, dtype=np.float64),
        np.ones(6), np.full(6, 2.), np.ones(3), np.full(3, 2.), True)
    del z, w, beitraege
    gc.collect()
    assert [b.name for b in ergebnis.beitraege] == ["auftrieb", "gewicht"]
    assert ergebnis.gesamt.frame == "simulationsframe"
    assert ergebnis.auftrieb.frame == "simulationsframe"
    assert ergebnis.schwerkraft_beruecksichtigt is True
    np.testing.assert_array_equal(ergebnis.added_mass, np.arange(6))
    np.testing.assert_array_equal(ergebnis.linear, np.ones(6))
    np.testing.assert_array_equal(ergebnis.quadratisch, np.full(6, 2.))
    np.testing.assert_array_equal(ergebnis.fluid, np.ones(3))
    np.testing.assert_array_equal(ergebnis.fluidrotation, np.full(3, 2.))
    ausgabe = ergebnis.zustand.werte
    beitrag = ergebnis.beitraege[0]
    del ergebnis
    gc.collect()
    np.testing.assert_array_equal(ausgabe, zustand_array())
    np.testing.assert_array_equal(beitrag.wrench.kraft, [1., 2., 3.])


@pytest.mark.parametrize("mutation", ["frame", "beitragsname", "beitragsframe", "volumen"])
def test_ergebnis_und_wrenches_lehnen_ungueltige_vertraege_ab(mutation):
    with pytest.raises(ValueError):
        if mutation == "frame":
            wrench("")
        elif mutation == "beitragsname":
            native.Beitrag("", wrench())
        else:
            native.Ergebnis(
                native.Zustand(zustand_array()), -1. if mutation == "volumen" else 1.,
                np.zeros(3), wrench(),
                [native.Beitrag("test", wrench("falsch"))] if mutation == "beitragsframe" else [],
                wrench(), np.zeros(6), np.zeros(6), np.zeros(6),
                np.zeros(3), np.zeros(3), False)


def test_abbruch_ist_threaduebergreifend_explizit_und_keine_erfolgsantwort():
    abbruch = native.Abbruch()
    assert not abbruch.abgebrochen
    assert abbruch.pruefen() is None
    thread = threading.Thread(target=abbruch.abbrechen)
    thread.start()
    thread.join(10)
    assert not thread.is_alive()
    assert abbruch.abgebrochen
    with pytest.raises(RuntimeError, match="abgebrochen"):
        abbruch.pruefen()


def test_ergebnisadapter_ist_exakter_rundlauf_mit_allen_benannten_kraeften():
    from segelphysik.core.auftrieb import Auftriebsergebnis, Vektor
    from segelphysik.core.dynamik_6dof import Zustand6DOF
    from segelphysik.core.kraftmodell import Kraftbeitrag, KraftErgebnis, Wrench
    from segelphysik.core.native_backend import ergebnis_nach_python, ergebnis_vorbereiten
    from werkzeuge.migration_vergleich import vergleiche

    zustand = Zustand6DOF(
        (1., 2., 3.), (.5, .5, .5, .5), (.1, -.2, .3), (-.1, .2, -.3))
    hydro = Auftriebsergebnis(.3, [1., 2., 3.], [0., 0., 100.], [2., 3., 0.])
    k = KraftErgebnis(
        hydro, Vektor([1., 2., 30.]), Vektor([2., 3., 4.]), (1., 2., 3., 4., 5., 6.),
        (Kraftbeitrag("auftrieb", Wrench(
            "simulationsframe", (0., 1., 2.), (0., 0., 100.), (2., 3., 0.))),
         Kraftbeitrag("gewicht", Wrench(
             "simulationsframe", (1., 0., 2.), (1., 2., -70.), (0., 0., 4.)))),
        (0., 1., 2.), True, (1.,) * 6, (2.,) * 6, (.1, .2, .3), (-.1, -.2, -.3))
    n = ergebnis_vorbereiten(zustand, k)
    z2, k2 = ergebnis_nach_python(n)
    del n
    gc.collect()
    vergleiche(zustand, z2)

    def daten(e):
        return {
            "V_tauch": e.V_tauch, "K": e.K.as_array(), "F_A": e.F_A.as_array(),
            "hydro_moment": e.hydrostatik.M.as_array(),
            "gesamt": e.gesamt_wrench, "beitraege": e.beitraege,
            **{name: getattr(e, name) for name in (
                "added_mass_diagonal", "linear_widerstand", "quadratischer_widerstand",
                "fluidgeschwindigkeit", "fluidwinkelgeschwindigkeit",
                "schwerkraft_beruecksichtigt", "bezugspunkt_m")},
        }

    vergleiche(daten(k), daten(k2))


def test_modelladapter_behaelt_geometrie_rollen_und_beladung_getrennt():
    from segelphysik.core.dynamik_6dof import Zustand6DOF
    from segelphysik.core.koerper import KoerperSnapshot
    from segelphysik.core.native_backend import modell_vorbereiten

    p = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    f = np.array([[0, 1, 2]], dtype=np.int64)
    s = KoerperSnapshot(
        30., np.eye(3), ((p, f),), (0., 0., 0.), Zustand6DOF(), 5,
        hydrodynamik_teile=(("ruder", "Ruder1", p, f),))
    m = modell_vorbereiten(s)
    s2 = KoerperSnapshot(
        40., np.eye(3) * 2., ((p, f),), (0., 0., 0.), Zustand6DOF(), 6)
    m2 = modell_vorbereiten(s2)
    del s, s2
    gc.collect()
    assert (m.masse, m.version, m2.masse, m2.version) == (30., 5, 40., 6)
    assert len(m.meshes) == 2
    assert m.meshes[0].verdraengend and not m.meshes[1].verdraengend
    assert m.meshes[1].rolle == "ruder" and m.meshes[1].name == "Ruder1"
    np.testing.assert_array_equal(m.meshes[0].punkte, p)
    np.testing.assert_array_equal(m.traegheit, np.eye(3))
    np.testing.assert_array_equal(m2.traegheit, np.eye(3) * 2.)


def test_parameteradapter_enthaelt_auch_bestehende_tauch_und_rolldaempfung():
    from segelphysik.core.konfig_lader import lade_physik
    from segelphysik.core.kraftmodell import baue_kraftmodell
    from segelphysik.core.native_backend import parameter_vorbereiten
    from werkzeuge.migration_inventar import ROOT

    physik = lade_physik(ROOT / "konfigurationen")
    original = baue_kraftmodell(lambda lage: None, physik, masse=1.)
    kandidat = parameter_vorbereiten(physik, 1000.)
    assert kandidat.dt == physik.dt_s
    assert kandidat.g == physik.g_m_pro_s2
    np.testing.assert_array_equal(kandidat.linear, original.linear_widerstand)
    np.testing.assert_array_equal(kandidat.quadratisch, original.quadratischer_widerstand)
    np.testing.assert_array_equal(kandidat.added_mass, original.added_mass_diagonal)
