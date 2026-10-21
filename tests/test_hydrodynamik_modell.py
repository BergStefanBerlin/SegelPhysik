import numpy as np
import pytest
from types import SimpleNamespace

from segelphysik.core.hydrodynamik import (
    HydrodynamikModell,
    HydrodynamikTeil,
    _benetzte_dreiecksflaechen,
    ittc_reibungsbeiwert,
    hydrodynamik_testprofil,
    wasserlinienlaenge_m,
)
from segelphysik.core.auftrieb import Vektor
from segelphysik.core.koerper import Koerper
from segelphysik.core.kraftmodell import Kraftmodell
from segelphysik.core.koerper_formen import build_sphere


_WUERFEL_PUNKTE = np.array([
    (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
    (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5),
    (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5),
], dtype=float)
_WUERFEL_DREIECKE = np.array([
    (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
    (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
    (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
], dtype=np.int64)


def _teile(rolle, punkte=_WUERFEL_PUNKTE, dreiecke=_WUERFEL_DREIECKE):
    return HydrodynamikTeil("test", rolle, punkte, dreiecke)


def test_ittc_reibungsbeiwert_bleibt_finit_und_stetig():
    werte = [ittc_reibungsbeiwert(x) for x in (0.0, 1.0, 1e5, 1e5 + 1, 5e5)]
    assert all(np.isfinite(werte))
    assert all(wert >= 0.0 for wert in werte)
    assert abs(werte[2] - werte[3]) < 1e-5


def test_benetzung_ist_lageabhaengig_und_flachengenau():
    alle_punkte = _WUERFEL_PUNKTE.copy()
    alle_punkte[:, 2] -= 2.0
    voll = _benetzte_dreiecksflaechen(
        alle_punkte, _WUERFEL_DREIECKE).sum()
    halb = _benetzte_dreiecksflaechen(
        _WUERFEL_PUNKTE, _WUERFEL_DREIECKE).sum()
    trocken_punkte = _WUERFEL_PUNKTE.copy()
    trocken_punkte[:, 2] += 2.0
    trocken = _benetzte_dreiecksflaechen(
        trocken_punkte, _WUERFEL_DREIECKE).sum()
    assert np.isclose(voll, 6.0)
    assert np.isclose(halb, 3.0)
    assert trocken == 0.0


def test_benetzung_bleibt_finit_wenn_eine_ecke_genau_auf_wasserlinie_liegt():
    punkte = np.array([
        (0.0, 0.0, -1.0),
        (1.0, 0.0, -1.0),
        (0.0, 1.0, 0.0),
    ])
    dreiecke = np.array([(0, 1, 2)], dtype=np.int64)

    with np.errstate(divide="raise", invalid="raise"):
        flaeche = _benetzte_dreiecksflaechen(punkte, dreiecke)

    assert flaeche == pytest.approx((np.sqrt(2.0) / 2.0,))


def test_hydrodynamikteil_cached_immutable_normal_mask_matches_normal_vectors():
    teil = _teile("rumpf")

    np.testing.assert_array_equal(
        teil._normalen_gueltig,
        np.linalg.norm(teil._normalen, axis=1) > 0.0)
    assert not teil._normalen_gueltig.flags.writeable


def test_rumpfwiderstand_zeigt_entgegen_der_fahrt():
    modell = HydrodynamikModell((_teile("rumpf"),))
    beitraege = modell.beitraege_erzeugen(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
        v=(2.0, 0.0, 0.0))
    kraft = np.asarray(beitraege[0].wrench.kraft_N)
    assert kraft[0] < 0.0
    assert abs(kraft[1]) < 1e-12
    assert abs(kraft[2]) < 1e-12
    assert np.dot(kraft, (2.0, 0.0, 0.0)) < 0.0


def test_kiel_querkraft_daempft_abdrift_ohne_leistungseintrag():
    punkte = np.array([
        (-0.5, -0.025, -0.5), (0.5, -0.025, -0.5),
        (0.5, 0.025, -0.5), (-0.5, 0.025, -0.5),
        (-0.5, -0.025, 0.5), (0.5, -0.025, 0.5),
        (0.5, 0.025, 0.5), (-0.5, 0.025, 0.5),
    ])
    teil = _teile("kiel", punkte)
    modell = HydrodynamikModell((teil,))
    beitrag = modell.beitraege_erzeugen(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
        v=(2.0, 0.2, 0.0))[0]
    kraft = np.asarray(beitrag.wrench.kraft_N)
    assert kraft[1] < 0.0
    assert np.dot(kraft, (2.0, 0.2, 0.0)) < 0.0


def test_ruderwinkel_hat_null_default_und_beeinflusst_querrichtung():
    teil = _teile("ruder")
    modell = HydrodynamikModell((teil,))
    assert modell.ruderwinkel_rad == 0.0

    modell.ruderwinkel_setzen(0.1)
    positiv = modell.beitraege_erzeugen(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
        v=(2.0, 0.0, 0.0))[0].wrench.kraft_N
    modell.ruderwinkel_setzen(-0.1)
    negativ = modell.beitraege_erzeugen(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
        v=(2.0, 0.0, 0.0))[0].wrench.kraft_N
    assert positiv[1] == pytest.approx(-negativ[1])
    assert positiv[1] < 0.0 < negativ[1]

    with pytest.raises(ValueError, match="-90"):
        modell.ruderwinkel_setzen(np.pi)


def test_rotationsgeschwindigkeit_erzeugt_moment_am_angriffspunkt():
    teil = _teile("rumpf")
    modell = HydrodynamikModell((teil,))
    beitraege = modell.beitraege_erzeugen(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
        v=(1.0, 0.0, 0.0), omega=(0.0, 0.0, 1.0))
    assert beitraege
    assert not np.allclose(beitraege[0].wrench.bezugspunkt_m, (0, 0, 0))


def test_snapshot_und_kraftmodell_integrieren_hydrodynamik():
    koerper = Koerper(
        form=(_WUERFEL_PUNKTE, _WUERFEL_DREIECKE),
        masse=1.0,
        name="Rumpf",
        rolle="rumpf",
    )
    snapshot = koerper.snapshot()
    modell = HydrodynamikModell.aus_koerper(snapshot)
    assert modell is not None
    assert len(modell.teile) == 1
    assert not snapshot.hydrodynamik_teile[0][2].flags.writeable

    hydro = SimpleNamespace(
        V_tauch=0.5,
        K=Vektor((0.0, 0.0, 0.0)),
        F_A=Vektor((0.0, 0.0, 0.0)),
        M=Vektor((0.0, 0.0, 0.0)),
    )
    kraftmodell = Kraftmodell(
        lambda *_args, **_kwargs: hydro,
        hydrodynamik=modell,
    )
    statischer_zustand = kraftmodell((0.0, 0.0, 0.0))
    ergebnis = kraftmodell(
        (snapshot.zustand.position, snapshot.zustand.quaternion),
        v=(1.0, 0.0, 0.0),
    )

    assert statischer_zustand.F_gesamt.as_array() == pytest.approx(
        (0.0, 0.0, 0.0))
    assert ergebnis.F_gesamt.x < 0.0
    assert "hydrodynamik_rumpf" in {
        beitrag.name for beitrag in ergebnis.beitraege}


def test_generischer_opt_in_erzeugt_geometrieabhaengigen_widerstand():
    koerper_klein = Koerper(
        form=(_WUERFEL_PUNKTE, _WUERFEL_DREIECKE),
        masse=1.0, name="klein")
    koerper_gross = Koerper(
        form=(_WUERFEL_PUNKTE * 2.0, _WUERFEL_DREIECKE),
        masse=1.0, name="gross")
    klein = HydrodynamikModell.aus_koerper(
        koerper_klein.snapshot(), cd_volumenkoerper=1.2)
    gross = HydrodynamikModell.aus_koerper(
        koerper_gross.snapshot(), cd_volumenkoerper=1.2)

    assert klein is not None and gross is not None
    assert klein.beitraege_erzeugen(
        (0.0, 0.0, 0.0), v=(2.0, 0.0, 0.0))[0].wrench.kraft_N[0] < 0
    kraft_klein = -klein.beitraege_erzeugen(
        (0.0, 0.0, 0.0), v=(2.0, 0.0, 0.0))[0].wrench.kraft_N[0]
    kraft_gross = -gross.beitraege_erzeugen(
        (0.0, 0.0, 0.0), v=(2.0, 0.0, 0.0))[0].wrench.kraft_N[0]
    assert kraft_gross == pytest.approx(4.0 * kraft_klein)


def test_generischer_widerstand_haengt_auch_von_der_form_ab():
    kugel_punkte, kugel_dreiecke = build_sphere(R=0.5, nseg=24)
    kugel = Koerper(
        form=(kugel_punkte, kugel_dreiecke), masse=1.0, name="kugel")
    wuerfel = Koerper(
        form=(_WUERFEL_PUNKTE, _WUERFEL_DREIECKE),
        masse=1.0, name="wuerfel")
    modell_kugel = HydrodynamikModell.aus_koerper(
        kugel.snapshot(), cd_volumenkoerper=0.47)
    modell_wuerfel = HydrodynamikModell.aus_koerper(
        wuerfel.snapshot(), cd_volumenkoerper=0.47)

    kraft_kugel = modell_kugel.beitraege_erzeugen(
        (0.0, 0.0, 0.0), v=(2.0, 0.0, 0.0))[0].wrench.kraft_N[0]
    kraft_wuerfel = modell_wuerfel.beitraege_erzeugen(
        (0.0, 0.0, 0.0), v=(2.0, 0.0, 0.0))[0].wrench.kraft_N[0]

    assert np.isfinite(kraft_kugel) and np.isfinite(kraft_wuerfel)
    assert kraft_kugel < 0.0 and kraft_wuerfel < 0.0
    assert not np.isclose(kraft_kugel, kraft_wuerfel)


def test_generischer_koerper_haengt_rotationswiderstand_an_der_oberflaeche_an():
    modell = HydrodynamikModell((_teile("volumenkoerper"),),
                                cd_volumenkoerper=1.2)

    beitrag = modell.beitraege_erzeugen(
        ((0.0, 0.0, -2.0), (1.0, 0.0, 0.0, 0.0)),
        v=(0.0, 0.0, 0.0), omega=(0.0, 0.0, 1.0))[0]

    assert np.linalg.norm(beitrag.wrench.kraft_N) < 1e-10
    assert beitrag.wrench.moment_Nm[2] < 0.0


def test_wasserlinienlaenge_kommt_aus_rumpfmesh():
    rumpf = _teile("rumpf")

    assert wasserlinienlaenge_m((rumpf,)) == pytest.approx(1.0)


def test_hydrodynamikprofil_liest_kraftvektor_und_volumenkoerper_cd():
    profil = hydrodynamik_testprofil("kugel", {
        "modell": "generischer_volumenkoerper",
        "cd_volumenkoerper": 0.47,
        "testkraft_N": [3.0, 4.0, 0.0],
        "angriffspunkt_m": [1.0, 2.0, 3.0],
        "referenzgeschwindigkeit_m_pro_s": 1.25,
        "ruderwinkel_grad": 0.0,
        "status": "vorläufig",
    })

    assert profil.kraft_betrag_N == pytest.approx(5.0)
    assert profil.azimut_grad == pytest.approx(53.1301023542)
    assert profil.angriffspunkt_m == (1.0, 2.0, 3.0)
    assert profil.cd_volumenkoerper == pytest.approx(0.47)
    assert profil.referenzgeschwindigkeit_m_pro_s == pytest.approx(1.25)
