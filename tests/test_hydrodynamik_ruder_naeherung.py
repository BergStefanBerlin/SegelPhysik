import math
from pathlib import Path

import numpy as np
import pytest

from segelphysik.core.dynamik_6dof import quaternion_matrix
from segelphysik.core.hydrodynamik_ruder_naeherung import (
    HydrodynamikModellFehler,
    RUDER_ALPHA_MAX_RAD,
    RUDER_MODELL_STATUS,
    RuderGeometrie,
    RuderKraftNaeherung,
    RuderTestkinematik,
)
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.kraftmodell import aggregiere_kraftbeitraege
from segelphysik.core.modell_lader import lade_modellpaket


@pytest.fixture
def yacht_ruder():
    wurzel = Path(__file__).resolve().parents[1]
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    paket = lade_modellpaket(
        wurzel / "segelphysik" / "modelle" / "yacht1",
        konfiguration.materialien_blocks,
    )
    geometrie = RuderGeometrie.aus_mesh(paket.meshes["ruder"])
    modell = RuderKraftNaeherung(
        geometrie,
        konfiguration.wasser_dichten["Süßwasser"],
    )
    return geometrie, modell


def test_rudergeometrie_und_streckung_werden_aus_mesh_abgeleitet(yacht_ruder):
    geometrie, modell = yacht_ruder

    assert geometrie.planform_flaeche_m2 == pytest.approx(0.0858247253125)
    assert geometrie.spannweite_m == pytest.approx(0.424575)
    assert geometrie.streckung == pytest.approx(2.10037293995)
    assert geometrie.flaechenzentrum_m == pytest.approx(
        (-1.96928503, 0.0, -0.269169448))
    assert modell.f_alpha_pro_rad == pytest.approx(2.95958215528)
    assert modell.geometrie.testkinematik.annahme == (
        "nutzerbeauftragte_testannahme_vorderkante")


def test_testpose_dreht_um_vorderkantenachse_ohne_achsenverschiebung():
    kinematik = RuderTestkinematik()
    winkel = math.radians(8.0)
    pose = kinematik.pose(winkel)
    punkt = np.asarray(kinematik.achspunkt_m)

    assert pose.punkt_transformieren(punkt) == pytest.approx(punkt)
    assert quaternion_matrix(
        pose.rotation_quaternion_wxyz) @ np.asarray(kinematik.achse) == (
            pytest.approx(kinematik.achse))
    assert pose.translation_m != (0.0, 0.0, 0.0)


def test_nullwinkel_und_nullfluss_erzeugen_keine_ruderkraft(yacht_ruder):
    _, modell = yacht_ruder

    ergebnis = modell.beitrag_erzeugen(
        (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0,
        frame="yacht1_blatt")
    stillstand = modell.beitrag_erzeugen(
        (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0,
        frame="yacht1_blatt")

    assert ergebnis.beitrag.wrench.kraft_N == pytest.approx((0.0, 0.0, 0.0))
    assert stillstand.beitrag.wrench.kraft_N == pytest.approx(
        (0.0, 0.0, 0.0))
    assert ergebnis.modell_status == RUDER_MODELL_STATUS
    assert ergebnis.c_induzierter_widerstand == pytest.approx(0.0)


def test_kraft_symmetrie_beim_vorzeichenwechsel_des_ruderwinkels(yacht_ruder):
    _, modell = yacht_ruder
    winkel = math.radians(5.0)
    positiv = modell.beitrag_erzeugen(
        (1.5, 0.0, 0.0), (0.0, 0.0, 0.0), winkel,
        frame="yacht1_blatt")
    negativ = modell.beitrag_erzeugen(
        (1.5, 0.0, 0.0), (0.0, 0.0, 0.0), -winkel,
        frame="yacht1_blatt")

    f_pos = np.asarray(positiv.beitrag.wrench.kraft_N)
    f_neg = np.asarray(negativ.beitrag.wrench.kraft_N)
    assert f_pos[1] < 0.0
    assert f_neg[1] > 0.0
    assert f_pos[0] == pytest.approx(f_neg[0])
    assert f_pos[1] == pytest.approx(-f_neg[1])
    assert f_pos[2] == pytest.approx(0.0)


def test_lokale_giergeschwindigkeit_geht_in_anstellwinkel_ein(yacht_ruder):
    _, modell = yacht_ruder
    ergebnis = modell.beitrag_erzeugen(
        (1.0, 0.0, 0.0), (0.0, 0.0, 0.01), 0.0,
        frame="yacht1_blatt")

    assert ergebnis.anstellwinkel_effektiv_rad < 0.0
    assert ergebnis.c_normalkraft < 0.0
    assert ergebnis.beitrag.wrench.kraft_N[1] > 0.0


def test_normalkraft_und_induzierter_widerstand_dissipieren(yacht_ruder):
    _, modell = yacht_ruder
    geschwindigkeit = np.array((1.0, 0.05, 0.0))
    ergebnis = modell.beitrag_erzeugen(
        geschwindigkeit, (0.0, 0.0, 0.0), math.radians(2.0),
        frame="yacht1_blatt")
    leistung = np.dot(
        np.asarray(ergebnis.beitrag.wrench.kraft_N), geschwindigkeit)

    assert ergebnis.c_induzierter_widerstand > 0.0
    assert leistung < 0.0


def test_beitrag_verwendet_wrench_hebelarmkonvention(yacht_ruder):
    _, modell = yacht_ruder
    ergebnis = modell.beitrag_erzeugen(
        (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), math.radians(5.0),
        frame="yacht1_blatt")
    wrench = ergebnis.beitrag.wrench
    summe, beitraege = aggregiere_kraftbeitraege(
        (ergebnis.beitrag,), (0.0, 0.0, 0.0), frame="yacht1_blatt")
    erwartet = np.cross(
        np.asarray(wrench.bezugspunkt_m),
        np.asarray(wrench.kraft_N),
    )

    assert len(beitraege) == 1
    assert summe.moment_Nm == pytest.approx(erwartet)


def test_modell_lehnt_winkel_ausserhalb_des_gueltigkeitsbereichs_ab(
        yacht_ruder):
    _, modell = yacht_ruder

    with pytest.raises(HydrodynamikModellFehler, match="Modellbereich"):
        modell.beitrag_erzeugen(
            (1.0, 0.0, 0.0), (0.0, 0.0, 0.0),
            RUDER_ALPHA_MAX_RAD + math.radians(0.1),
            frame="yacht1_blatt")


@pytest.mark.parametrize(
    "geschwindigkeit, omega",
    [
        ((1.0, 0.0, 0.1), (0.0, 0.0, 0.0)),
        ((1.0, 0.0, 0.0), (0.01, 0.0, 0.0)),
        ((-1.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ],
)
def test_nicht_unterstuetzte_bewegung_wird_explizit_abgelehnt(
        yacht_ruder, geschwindigkeit, omega):
    _, modell = yacht_ruder

    with pytest.raises(HydrodynamikModellFehler):
        modell.beitrag_erzeugen(
            geschwindigkeit, omega, 0.0, frame="yacht1_blatt")


@pytest.mark.parametrize("faktor", (0.5, 1.0, 1.5))
def test_sensitivitaetsfaktor_skaliert_normalkraft(yacht_ruder, faktor):
    geometrie, modell = yacht_ruder
    sensitivitaet = RuderKraftNaeherung(
        geometrie,
        modell.wasserdichte_kg_pro_m3,
        sensitivitaetsfaktor=faktor,
    )
    winkel = math.radians(4.0)
    basis = modell.beitrag_erzeugen(
        (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), winkel,
        frame="yacht1_blatt")
    geaendert = sensitivitaet.beitrag_erzeugen(
        (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), winkel,
        frame="yacht1_blatt")

    assert geaendert.normalkraft_N == pytest.approx(
        faktor * basis.normalkraft_N)
    assert geaendert.c_induzierter_widerstand == pytest.approx(
        faktor**2 * basis.c_induzierter_widerstand)


def test_rudermoment_vorzeichen_ist_mit_testkinematik_konsistent(yacht_ruder):
    _, modell = yacht_ruder
    winkel = math.radians(5.0)
    momente = []
    for auslenkung in (winkel, -winkel):
        beitrag = modell.beitrag_erzeugen(
            (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), auslenkung,
            frame="yacht1_blatt").beitrag
        summe, _ = aggregiere_kraftbeitraege(
            (beitrag,), (0.0, 0.0, 0.0), frame="yacht1_blatt")
        momente.append(summe.moment_Nm[2])

    assert momente[0] > 0.0
    assert momente[1] < 0.0


def test_ungueltige_dichte_und_sensitivitaet_werden_abgelehnt(yacht_ruder):
    geometrie, _ = yacht_ruder

    with pytest.raises(HydrodynamikModellFehler, match="Wasserdichte"):
        RuderKraftNaeherung(geometrie, 0.0)
    with pytest.raises(HydrodynamikModellFehler, match="Sensitivitaetsfaktor"):
        RuderKraftNaeherung(geometrie, 1000.0, 0.0)


def test_ungueltiger_meshinput_wird_explizit_abgelehnt():
    with pytest.raises(HydrodynamikModellFehler, match="Mesh"):
        RuderGeometrie.aus_mesh(object())
