from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core import auftrieb, koerper_formen
from segelphysik.core.volumen_union import (
    VolumenUnionFehler,
    VorbereitetesUnionModell,
    volumen_schwerpunkt_union,
)


@pytest.fixture
def quader():
    return koerper_formen.bau_quader(2.0, 2.0, 2.0)


def test_union_eines_quaders_ist_exakt(quader):
    volumen, schwerpunkt = volumen_schwerpunkt_union([quader])

    assert volumen == pytest.approx(8.0)
    assert schwerpunkt == pytest.approx((0.0, 0.0, 0.0))


def test_union_ueberlappender_quader_vermeidet_doppelzaehlung(quader):
    verschoben = (
        quader[0] + np.array((1.0, 0.0, 0.0)), quader[1])

    volumen, schwerpunkt = volumen_schwerpunkt_union([quader, verschoben])

    assert volumen == pytest.approx(12.0)
    assert schwerpunkt == pytest.approx((0.5, 0.0, 0.0))


def test_union_identischer_und_getrennter_meshes(quader):
    getrennt = (
        quader[0] + np.array((4.0, 0.0, 0.0)), quader[1])

    volumen, schwerpunkt = volumen_schwerpunkt_union(
        [quader, quader, getrennt])

    assert volumen == pytest.approx(16.0)
    assert schwerpunkt == pytest.approx((2.0, 0.0, 0.0))


def test_kraftfunktion_bietet_exakte_union_als_opt_in_referenz(quader):
    koerper = SimpleNamespace(
        blatt_meshes=[
            (quader[0] + np.array((0.0, 0.0, -0.5)), quader[1]),
            (quader[0] + np.array((1.0, 0.0, -0.5)), quader[1]),
        ],
        r_S=np.zeros(3), teile=[])

    ergebnis = auftrieb.kraftfunktion_berechne(
        koerper, (0.0, 0.0, 0.0), pfad="exakt_union")

    assert ergebnis.V_tauch == pytest.approx(9.0)
    assert ergebnis.K.as_array() == pytest.approx((0.5, 0.0, -0.75))
    assert ergebnis.F_A.z == pytest.approx(
        1000.0 * auftrieb.G_NORM * ergebnis.V_tauch)


def test_exakte_union_kraftfunktion_gibt_bei_trockenem_koerper_null(quader):
    koerper = SimpleNamespace(
        blatt_meshes=[quader], r_S=np.zeros(3), teile=[])

    ergebnis = auftrieb.kraftfunktion_berechne(
        koerper, (2.0, 0.0, 0.0), pfad="exakt_union")

    assert ergebnis.V_tauch == 0.0
    assert ergebnis.K.as_array() == pytest.approx(np.zeros(3))
    assert ergebnis.F_A.as_array() == pytest.approx(np.zeros(3))


def test_offene_meshes_werden_als_union_abgelehnt(quader):
    with pytest.raises(VolumenUnionFehler, match="geschlossen"):
        volumen_schwerpunkt_union([(quader[0], quader[1][:-1])])


def test_leere_union_hat_endliche_nullwerte():
    volumen, schwerpunkt = volumen_schwerpunkt_union([])

    assert volumen == 0.0
    assert np.array_equal(schwerpunkt, np.zeros(3))


@pytest.mark.parametrize(("z", "phi"), [
    (0.0, 0.0), (-0.3, 0.17), (0.2, -0.4),
])
def test_vorbereitete_union_bleibt_bei_posewechsel_exakt(quader, z, phi):
    meshes = [
        (quader[0] + np.array((-0.25, 0.0, -0.4)), quader[1]),
        (quader[0] + np.array((0.75, 0.0, -0.4)), quader[1]),
    ]
    c, s = np.cos(phi), np.sin(phi)
    transform = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, c, -s, 0.0],
        [0.0, s, c, z],
    ])
    vorbereitet = VorbereitetesUnionModell(meshes)
    erwartet = volumen_schwerpunkt_union([
        (punkte @ transform[:, :3].T + transform[:, 3], dreiecke)
        for punkte, dreiecke in meshes
    ], ebene_z=0.0)

    volumen, schwerpunkt = vorbereitet.auswerten(
        transform=transform, ebene_z=0.0)

    assert volumen == pytest.approx(erwartet[0], abs=1e-12)
    assert schwerpunkt == pytest.approx(erwartet[1], abs=1e-12)


def test_vorbereitete_union_lehnt_ungueltige_pose_ab(quader):
    vorbereitet = VorbereitetesUnionModell([quader])

    with pytest.raises(VolumenUnionFehler, match="3x4"):
        vorbereitet.auswerten(transform=np.eye(4))
