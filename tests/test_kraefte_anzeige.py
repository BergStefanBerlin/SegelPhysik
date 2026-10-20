from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core.auftrieb import Vektor
from segelphysik.core.frames import Pose
from segelphysik.core.kraftmodell import (
    KraftErgebnis, Kraftbeitrag, Kraftmodell, Wrench, aggregiere_kraftbeitraege,
)
from segelphysik.core.kraefte_anzeige import (
    BeitragsAnzeige, Datenstatus, KraefteAnzeigeAdapter, Quellbezug,
    SolverBewertung, anzeige_wrench, wirkungslinie, wrench_transformieren,
)
from segelphysik.core.pfeilstil import (
    BEITRAGS_DEFINITIONEN, PFEILE, beitragsdefinition,
)

FRAME = "simulationsframe"
P = (0.0, 0.0, 0.0)


@pytest.fixture(params=("python", "cpp"), autouse=True)
def backend(request, monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", request.param)


def _wrench(kraft=(0, 0, 0), moment=(0, 0, 0), punkt=P):
    return Wrench(FRAME, punkt, kraft, moment)


def _ergebnis(beitraege, gewicht=True):
    gesamt, normalisiert = aggregiere_kraftbeitraege(beitraege, P)
    hydro = SimpleNamespace(
        F_A=Vektor((0, 0, 10)), M=Vektor((0, 0, 0)),
        K=Vektor(P), V_tauch=0.001)
    return KraftErgebnis(
        hydro, Vektor(gesamt.kraft_N), Vektor(gesamt.moment_Nm),
        (0.0,) * 6, normalisiert, P, gewicht)


def _snapshot(beitraege=(), *, quellen=None, erwartet="automatisch",
              gewicht=False, **kwargs):
    if quellen is None:
        quellen = tuple(Quellbezug(b.name, b.name) for b in beitraege)
    if erwartet == "automatisch":
        erwartet = tuple(quellen)
        if not any(q.name == "schwerkraft" for q in erwartet):
            erwartet += (Quellbezug("gewicht", "schwerkraft"),)
    parameter = dict(
        koerper_id="boot", generation=2, sequenz=3, zeit_s=1.25,
        kraftpose=Pose(FRAME, "koerper", P, (1, 0, 0, 0)),
        quellen=quellen, erwartet=erwartet, masse_kg=1, g_m_s2=10)
    parameter.update(kwargs)
    return KraefteAnzeigeAdapter().snapshot(
        _ergebnis(beitraege, gewicht), **parameter)


def test_register_hat_eindeutige_definitionen_und_bestehende_stilreferenzen():
    ids = [d.id for d in BEITRAGS_DEFINITIONEN]
    assert len(ids) == len(set(ids)) == 9
    pfeil_ids = {p[0] for p in PFEILE}
    for definition in BEITRAGS_DEFINITIONEN:
        assert definition.kraft_id in pfeil_ids
        assert set(definition.moment_ids) <= pfeil_ids
    assert beitragsdefinition("neue_quelle").gruppe == "nicht_zugeordnet"
    with pytest.raises(ValueError):
        beitragsdefinition("")


def test_anzeige_bezug_und_frame_erhalten_den_originalsnapshot():
    pose = Pose(FRAME, "koerper", (2, 3, 4), (2**-.5, 0, 0, 2**-.5))
    quelle = Kraftbeitrag(
        "fremdkraft", _wrench((10, 0, 0), (0, 0, 5), punkt=(2, 3, 4)))
    snapshot = _snapshot((quelle,), kraftpose=pose)
    beitrag = snapshot.beitraege[0]
    welt = anzeige_wrench(snapshot, beitrag, weltursprung=True)
    assert welt.kraft_N == (10, 0, 0)
    assert welt.moment_Nm == pytest.approx((0, 40, -25))
    koerper = anzeige_wrench(snapshot, beitrag, koerperframe=True)
    assert koerper.kraft_N == pytest.approx((0, -10, 0), abs=1e-12)
    assert koerper.moment_Nm == pytest.approx((0, 0, 5), abs=1e-12)
    assert koerper.bezugspunkt_m == pytest.approx((0, 0, 0), abs=1e-12)
    assert snapshot.kraftpose is pose
    assert beitrag.wrench.moment_Nm != welt.moment_Nm


@pytest.mark.parametrize("arm,kraft,moment", [
    ((0, 0, 0), (0, 0, 10), (0, 0, 0)),
    ((0, 0.35, 0), (0, 0, 10), (3.5, 0, 0)),
    ((0.10, 0.35, -0.30), (0, 0, 49050), (17167.5, -4905, 0)),
])
def test_referenz_einzelkraft_hat_genau_ein_hebelarmmoment(arm, kraft, moment):
    quelle = Kraftbeitrag("fremdkraft", _wrench(kraft, punkt=arm))
    snapshot = _snapshot((quelle,))
    beitrag = snapshot.beitraege[0]
    np.testing.assert_allclose(beitrag.wrench.moment_Nm, moment, rtol=1e-10, atol=1e-9)
    assert beitrag.wrench.kraft_N == kraft
    np.testing.assert_allclose(snapshot.bilanz.wrench.moment_Nm, moment,
                               rtol=1e-10, atol=1e-9)


def test_kraeftepaar_ist_bezugspunktunabhaengig():
    a = Kraftbeitrag("a", _wrench((0, 0, 10), punkt=(0, 0.35, 0)))
    b = Kraftbeitrag("b", _wrench((0, 0, -10)))
    w, _ = aggregiere_kraftbeitraege((a, b), P)
    assert w.kraft_N == P
    np.testing.assert_allclose(w.moment_Nm, (3.5, 0, 0), rtol=1e-10, atol=1e-9)
    assert w.auf_bezugspunkt((17, -3, 4)).moment_Nm == w.moment_Nm


@pytest.mark.parametrize("gewicht", (True, False))
def test_gewicht_genau_einmal_und_ungleiches_gewicht_auftrieb_bleibt(gewicht):
    beitraege = [Kraftbeitrag("hydrostatik", _wrench((0, 0, 8)))]
    if gewicht:
        beitraege.append(Kraftbeitrag("schwerkraft", _wrench((0, 0, -10))))
    s = _snapshot(tuple(beitraege), gewicht=gewicht)
    assert s.vollstaendigkeit == "vollstaendig"
    assert len([b for b in s.beitraege if b.name == "schwerkraft"]) == 1
    assert s.bilanz.wrench.kraft_N == (0, 0, -2)
    assert s.rechenbilanz.kraft_N == (0, 0, -2)
    assert s.gleichgewichtsstatus == "Gleichgewicht nicht bewertet"


def test_inkonsistentes_gewichtsmerkmal_wird_abgewiesen():
    with pytest.raises(ValueError, match="Gewichtsmerkmal"):
        _snapshot((Kraftbeitrag("schwerkraft", _wrench((0, 0, -10))),))


def test_gleichnamige_quellen_bleiben_beim_umordnen_identisch():
    a = Kraftbeitrag("hydrodynamik_rumpf", _wrench((1, 0, 0)))
    b = Kraftbeitrag("hydrodynamik_rumpf", _wrench((2, 0, 0)))
    ids = (Quellbezug("rumpf-links", a.name), Quellbezug("rumpf-rechts", b.name))
    s1 = _snapshot((a, b), quellen=ids)
    s2 = _snapshot((b, a), quellen=tuple(reversed(ids)))
    assert {b.instanz_id: b.wrench for b in s1.beitraege} == {
        b.instanz_id: b.wrench for b in s2.beitraege}
    assert s1.bilanz.wrench.kraft_N == (3, 0, -10)
    assert s1.bilanz.wrench == s2.bilanz.wrench
    with pytest.raises(ValueError, match="nicht eindeutig"):
        _snapshot((a, b), quellen=(ids[0], ids[0]))


def test_summen_referenzieren_nur_atomare_quellen():
    s = _snapshot((Kraftbeitrag("hydrostatik", _wrench((0, 0, 10))),))
    atomare_ids = {b.instanz_id for b in s.beitraege}
    assert set(s.bilanz.quell_ids) == atomare_ids
    assert all(set(g.quell_ids) <= atomare_ids for g in s.gruppen)
    assert not atomare_ids & {g.instanz_id for g in s.gruppen}
    assert s.bilanz.status == Datenstatus.NULL
    assert s.bilanz.wrench.kraft_N == P


@pytest.mark.parametrize("status", (
    Datenstatus.FEHLEND, Datenstatus.NICHT_BERECHNET,
    Datenstatus.UNGUELTIG, Datenstatus.VERALTET,
))
def test_fehlende_aktive_quelle_ist_keine_null(status):
    erwartet = (Quellbezug("gewicht", "schwerkraft"),
                Quellbezug("ruder", "hydrodynamik_ruder", status))
    s = _snapshot(erwartet=erwartet)
    assert s.vollstaendigkeit == "teilsumme"
    assert s.gleichgewichtsstatus == "nicht bewertbar"
    assert s.fehlende_quellen == (("boot", "ruder"),)
    ruder = next(b for b in s.beitraege if b.name == "hydrodynamik_ruder")
    assert ruder.wrench is None and ruder.status == status
    hydrogruppe = next(g for g in s.gruppen if g.gruppe == "hydrodynamik")
    assert hydrogruppe.wrench is None
    assert hydrogruppe.status == Datenstatus.FEHLEND
    assert "unvollstaendig" in s.bilanz.name


def test_deaktiviert_ist_keine_luecke_unbekannter_umfang_bleibt_ungeklaert():
    erwartet = (Quellbezug("gewicht", "schwerkraft"),
                Quellbezug("ruder", "hydrodynamik_ruder", Datenstatus.DEAKTIVIERT))
    assert _snapshot(erwartet=erwartet).vollstaendigkeit == "vollstaendig"
    s = _snapshot(erwartet=None)
    assert s.vollstaendigkeit == "ungeklaert"
    assert s.gleichgewichtsstatus == "nicht bewertbar"
    assert _snapshot(gewicht=True, erwartet=None).fehlende_quellen == (
        ("boot", "solver:schwerkraft"),)
    assert _snapshot(gewicht=True, erwartet=None).bilanz.wrench is None


def test_nicht_zugeordnete_quelle_bleibt_in_bilanz():
    s = _snapshot((Kraftbeitrag("bekannte_neue_physik", _wrench((2, 3, 4))),))
    assert s.beitraege[0].gruppe == "nicht_zugeordnet"
    assert s.beitraege[0].name == "bekannte_neue_physik"
    assert s.bilanz.wrench.kraft_N == (2, 3, -6)


def test_solverbewertung_braucht_denselben_zustand_und_quellenumfang():
    bewertung = SolverBewertung(
        "boot", 2, 3, ("gewicht",), "Statiksolver",
        ("z", "rollen"), (("F_z", 0.0, 1e-8), ("M_x", 0.0, 1e-8)), True)
    s = _snapshot(solverbewertung=bewertung)
    assert s.gleichgewichtsstatus == "Teilgleichgewicht gemaess Solver"
    assert _snapshot(solverbewertung=replace(
        bewertung, erfuellt=False)).gleichgewichtsstatus == "Kriterien nicht erfuellt"
    assert _snapshot(solverbewertung=replace(
        bewertung, stationaer=True)).gleichgewichtsstatus == (
            "stationaerer Zustand gemaess Solver")
    for falsch in (
        replace(bewertung, sequenz=4), replace(bewertung, generation=1),
        replace(bewertung, koerper_id="anderes_boot"),
        replace(bewertung, quell_ids=("unbekannt",)),
    ):
        with pytest.raises(ValueError, match="nicht zu diesem Snapshot"):
            _snapshot(solverbewertung=falsch)
    komplett = replace(
        bewertung, freiheitsgrade=("x", "y", "z", "rollen", "nicken", "gieren"))
    assert _snapshot(solverbewertung=komplett).gleichgewichtsstatus == "Im Gleichgewicht"


def test_snapshot_und_quellen_besitzen_keine_veraenderlichen_arrays():
    punkt = np.array((1.0, 2.0, 3.0))
    quelle = Quellbezug("hydro", "hydrostatik", originalangriff_m=punkt)
    s = _snapshot((Kraftbeitrag("hydrostatik", _wrench((0, 0, 10))),),
                  quellen=[quelle])
    punkt[:] = 100
    assert s.beitraege[0].originalangriff_m == (1, 2, 3)
    with pytest.raises(FrozenInstanceError):
        s.sequenz = 99
    assert isinstance(s.beitraege, tuple)
    assert isinstance(s.bilanz.quell_ids, tuple)
    with pytest.raises(TypeError):
        s.beitraege[0].wrench.kraft_N[0] = 99
    import pickle
    assert pickle.loads(pickle.dumps(s)) == s
    with pytest.raises(TypeError, match="unveraenderliche"):
        replace(s, kraftpose=SimpleNamespace(translation_m=np.zeros(3)))
    with pytest.raises(TypeError, match="unveraenderliche"):
        replace(s, bilanz=SimpleNamespace(kraft=np.ones(3)))


def test_reiner_moment_und_wrench_restmoment_rekonstruieren_original():
    rein = _wrench(moment=(0, 0, 5))
    zeige_rein = wirkungslinie(rein, f_char_N=10, koerperausdehnung_m=1)
    assert not zeige_rein.aequivalent
    assert zeige_rein.restmoment_Nm == rein.moment_Nm
    wrench = _wrench((0, 0, 10), (2, 0, 3))
    zeige = wirkungslinie(wrench, f_char_N=10, koerperausdehnung_m=1)
    assert zeige.aequivalent
    np.testing.assert_allclose(zeige.anker_m, (0, 0.2, 0), rtol=1e-10, atol=1e-9)
    np.testing.assert_allclose(zeige.restmoment_Nm, (0, 0, 3), rtol=1e-10, atol=1e-9)
    rekonstruiert = np.cross(
        np.array(zeige.anker_m) - wrench.bezugspunkt_m, wrench.kraft_N
    ) + zeige.restmoment_Nm
    np.testing.assert_allclose(rekonstruiert, wrench.moment_Nm, rtol=1e-10, atol=1e-9)


def test_reines_hebelarmmoment_erzeugt_keine_subtraktiven_restmomentmarker():
    for i in range(1, 25):
        kraft = np.array((-1.003, .01 * i * 1.003, 0))
        moment = np.cross((0, .01 * i, 0), kraft)
        wrench = _wrench(kraft, moment)
        zeige = wirkungslinie(wrench, f_char_N=1, koerperausdehnung_m=1)
        assert zeige.aequivalent
        assert zeige.restmoment_Nm == (0, 0, 0)
        np.testing.assert_allclose(
            np.cross(np.asarray(zeige.anker_m) - wrench.bezugspunkt_m, kraft),
            moment, rtol=1e-10, atol=1e-9)


@pytest.mark.parametrize("kraft,erwartet", [(0.999e-9, False), (1e-9, False),
                                          (1.001e-9, True)])
def test_wirkungsliniengrenze_beidseits_epsilon(kraft, erwartet):
    assert wirkungslinie(_wrench((kraft, 0, 0)), f_char_N=1,
                        koerperausdehnung_m=1).aequivalent == erwartet


@pytest.mark.parametrize("abstand,erwartet", [(9.999, True), (10, True), (10.001, False)])
def test_ankergrenze_beidseits_zehn_ausdehnungen(abstand, erwartet):
    w = _wrench((0, 0, 1), (abstand, 0, 0))
    anzeige = wirkungslinie(w, f_char_N=1, koerperausdehnung_m=1)
    assert anzeige.aequivalent == erwartet
    if not erwartet:
        assert anzeige.anker_m == w.bezugspunkt_m
        assert anzeige.restmoment_Nm == w.moment_Nm


def test_wirkungslinie_ohne_geometrie_und_bei_extremwerten():
    w = _wrench((0, 0, 1), (1, 0, 0))
    assert not wirkungslinie(w, f_char_N=1, koerperausdehnung_m=None).aequivalent
    gross = _wrench((1.7e308, 1.7e308, 0), (1, 0, 0))
    zeige = wirkungslinie(gross, f_char_N=1, koerperausdehnung_m=1)
    assert not zeige.aequivalent
    assert zeige.restmoment_Nm == gross.moment_Nm
    klein = _wrench((1e-20, 0, 0), (1, 2, 3))
    assert wirkungslinie(klein, f_char_N=1, koerperausdehnung_m=1).restmoment_Nm == (
        klein.moment_Nm)


def test_nahezu_ausloeschende_verteilte_kraefte_erhalten_restmoment():
    quellen = (
        Kraftbeitrag("links", _wrench((1, 0, 0), punkt=(0, 1, 0))),
        Kraftbeitrag("rechts", _wrench((-1 + 1e-13, 0, 0), punkt=(0, -1, 0))),
    )
    wrench, _ = aggregiere_kraftbeitraege(quellen, P)
    assert wrench.kraft_N[0] != 0
    zeige = wirkungslinie(wrench, f_char_N=1, koerperausdehnung_m=1)
    assert not zeige.aequivalent
    assert zeige.restmoment_Nm == wrench.moment_Nm
    assert abs(zeige.restmoment_Nm[2]) > 1.9


@pytest.mark.parametrize("wert", (float("nan"), float("inf"), -float("inf")))
def test_nichtendliche_quelldaten_werden_vor_snapshot_erzeugung_abgewiesen(wert):
    with pytest.raises(ValueError, match="endlich"):
        _wrench((wert, 0, 0))
    with pytest.raises(ValueError, match="endlich"):
        Quellbezug("quelle", "fremdkraft", originalangriff_m=(0, wert, 0))


def test_framewechsel_kommutiert_mit_bezugspunktverschiebung():
    # 90 Grad um z und Translation; Richtungen erhalten keine Translation.
    pose = Pose("ziel", FRAME, (1, 2, 3), (2**-0.5, 0, 0, 2**-0.5))
    w = _wrench((1, 0, 0), (0, 2, 0), (1, 0, 0))
    ziel = (0, 1, 0)
    a = wrench_transformieren(w.auf_bezugspunkt(ziel), pose)
    b = wrench_transformieren(w, pose).auf_bezugspunkt(
        pose.punkt_transformieren(ziel))
    np.testing.assert_allclose(a.kraft_N, (0, 1, 0), rtol=1e-10, atol=1e-9)
    np.testing.assert_allclose(a.moment_Nm, b.moment_Nm, rtol=1e-10, atol=1e-9)
    np.testing.assert_allclose(a.bezugspunkt_m, b.bezugspunkt_m,
                               rtol=1e-10, atol=1e-9)
    with pytest.raises(ValueError, match="Quellframe"):
        wrench_transformieren(w, pose.invers())


@pytest.mark.parametrize("kwargs", [
    {"generation": -1}, {"sequenz": True}, {"zeit_s": float("nan")},
    {"masse_kg": 0}, {"g_m_s2": float("inf")}, {"koerper_id": ""},
    {"erwartet": ()},
])
def test_ungueltige_snapshotmetadaten_werden_abgewiesen(kwargs):
    with pytest.raises(ValueError):
        _snapshot(**kwargs)


def test_quellzuordnung_braucht_passenden_namen_frame_und_vollstaendigen_umfang():
    beitrag = Kraftbeitrag("hydrostatik", _wrench((0, 0, 10)))
    with pytest.raises(ValueError, match="Quellname"):
        _snapshot((beitrag,), quellen=(Quellbezug("a", "widerstand"),))
    with pytest.raises(ValueError, match="Quellbezug"):
        _snapshot((beitrag,), quellen=())
    with pytest.raises(ValueError, match="Quellenumfang"):
        _snapshot((beitrag,), erwartet=(Quellbezug("gewicht", "schwerkraft"),))
    with pytest.raises(ValueError, match="anderen Frames"):
        _snapshot(kraftpose=Pose("falsch", "koerper", P, (1, 0, 0, 0)))
    with pytest.raises(ValueError, match="kollidiert"):
        _snapshot((beitrag,), quellen=(Quellbezug("summe:gesamt", "hydrostatik"),))


def test_anzeigeobjekt_kopiert_listen_und_lehnt_scheinwerte_ab():
    ids = [["boot", "quelle"]]
    b = BeitragsAnzeige(
        ["boot", "summe"], "Test", "Test", _wrench(), Datenstatus.NULL,
        "Gruppensumme", ids)
    ids[0][1] = "geaendert"
    assert b.quell_ids == (("boot", "quelle"),)
    with pytest.raises(ValueError, match="Wrench"):
        replace(b, wrench=None)
    with pytest.raises(ValueError, match="Nullstatus"):
        replace(b, wrench=_wrench((1e-30, 0, 0)))


def test_kleine_endliche_kraft_bleibt_in_der_bilanz():
    b = Kraftbeitrag("fremdkraft", _wrench((1e-20, 0, 0), (1e-22, 0, 0)))
    s = _snapshot((b,))
    assert s.beitraege[0].status == Datenstatus.GUELTIG
    assert s.bilanz.wrench.kraft_N[0] == 1e-20
    assert s.bilanz.wrench.moment_Nm[0] == 1e-22


def test_erster_solververgleich_nutzt_dieselbe_tatsaechliche_kraftbilanz():
    from segelphysik.core.statisch import loese

    def hydro(lage, **_):
        return SimpleNamespace(
            F_A=Vektor((0, 0, 10 - 100 * lage[0])),
            M=Vektor((-20 * lage[1], 0, 0)), K=Vektor(P), V_tauch=0.001)

    modell = Kraftmodell(hydro, masse=1, g=10)

    def solverfunktion(lage, v_z, omega_x):
        return modell(lage, v=(0, 0, v_z), omega=(omega_x, 0, 0))

    loesung = loese(solverfunktion, 1, g=10, start=(0.02, 0.01), tol=1e-8)
    pose = (loesung["z"], loesung["phi"], 0)
    ergebnis = modell(pose)
    quellen = tuple(Quellbezug(b.name, b.name) for b in ergebnis.beitraege)
    s = KraefteAnzeigeAdapter().snapshot(
        ergebnis, koerper_id="solverboot", generation=0, sequenz=1,
        zeit_s=0, kraftpose=Pose(
            FRAME, "koerper", (0, 0, pose[0]),
            (np.cos(pose[1] / 2), np.sin(pose[1] / 2), 0, 0)),
        quellen=quellen, erwartet=quellen, masse_kg=1, g_m_s2=10)
    np.testing.assert_allclose(
        s.bilanz.wrench.kraft_N, ergebnis.F_gesamt.as_array(),
        rtol=1e-10, atol=1e-9)
    np.testing.assert_allclose(
        s.bilanz.wrench.moment_Nm, ergebnis.M_gesamt.as_array(),
        rtol=1e-10, atol=1e-9)
    assert abs(s.bilanz.wrench.kraft_N[2]) < 1e-8
    assert abs(s.bilanz.wrench.moment_Nm[0]) < 1e-8


def test_dynamischer_snapshot_behaelt_auswertungs_pose_statt_endpose():
    from segelphysik.core.dynamik_6dof import Zustand6DOF, schritt

    def hydro(*_args, **_kwargs):
        return SimpleNamespace(
            F_A=Vektor((0, 0, 8)), M=Vektor(P), K=Vektor(P), V_tauch=0.001)

    modell = Kraftmodell(hydro, masse=1, g=10,
                         added_mass_diagonal=(0, 0, 2, 0, 0, 0))
    start = Zustand6DOF(position=(0, 0, 0.25))
    ende, ergebnis = schritt(start, modell, 1, np.eye(3), 0.1, 10)
    quellen = tuple(Quellbezug(b.name, b.name) for b in ergebnis.beitraege)
    s = KraefteAnzeigeAdapter().snapshot(
        ergebnis, koerper_id="boot", generation=0, sequenz=1,
        zeit_s=0, kraftpose=Pose(FRAME, "koerper", start.position, start.quaternion),
        quellen=quellen, erwartet=quellen, masse_kg=1, g_m_s2=10)
    assert s.kraftpose.translation_m == start.position
    assert s.kraftpose.translation_m != ende.position
    assert any(b.name == "added_mass" for b in s.beitraege)
    np.testing.assert_allclose(
        s.bilanz.wrench.kraft_N, ergebnis.F_gesamt.as_array(),
        rtol=1e-10, atol=1e-9)
    assert s.gleichgewichtsstatus == "Gleichgewicht nicht bewertet"
