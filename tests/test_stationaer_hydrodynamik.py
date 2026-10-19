import math
from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core.auftrieb import Vektor
from segelphysik.core.stationaer_hydrodynamik import (
    StationaereStufe,
    StationaerSolverFehler,
    loese_stationaer,
    pruefe_stationaer_dynamisch,
)


class _TestKraftfunktion:
    def __init__(self, ruderwinkel_rad=0.0):
        self.hydrodynamik = SimpleNamespace(
            ruderwinkel_rad=ruderwinkel_rad)

    def __call__(self, pose, v, omega):
        quaternion = pose[1]
        w, x, y, zq = quaternion
        phi = math.atan2(
            2.0 * (w * x + y * zq),
            1.0 - 2.0 * (x * x + y * y))
        theta = math.asin(max(-1.0, min(
            1.0, 2.0 * (w * y - zq * x))))
        psi = math.atan2(
            2.0 * (w * zq + x * y),
            1.0 - 2.0 * (y * y + zq * zq))
        z = pose[0][2]
        kraft = (
            4.0 - 2.0 * v[0],
            -5.0 * v[1],
            10.0 * (-0.2 - z),
        )
        moment = (-4.0 * phi, -20.0 * theta, -3.0 * psi)
        return SimpleNamespace(
            F_gesamt=Vektor(kraft),
            M_gesamt=Vektor(moment),
        )


class _StabilesTestmodell:
    def __call__(self, pose, v, omega):
        z = pose[0][2]
        w, x, y, zq = pose[1]
        phi = math.atan2(
            2.0 * (w * x + y * zq),
            1.0 - 2.0 * (x * x + y * y))
        theta = math.asin(max(-1.0, min(
            1.0, 2.0 * (w * y - zq * x))))
        psi = math.atan2(
            2.0 * (w * zq + x * y),
            1.0 - 2.0 * (y * y + zq * zq))
        kraft = Vektor((2.0 - v[0], -2.0 * v[1],
                        -2.0 * z - 2.0 * v[2]))
        moment = Vektor((-2.0 * phi - 2.0 * omega[0],
                         -2.0 * theta - 2.0 * omega[1],
                         -2.0 * psi - 2.0 * omega[2]))
        return SimpleNamespace(
            F_gesamt=kraft, F_A=kraft, M_gesamt=moment, M=moment,
            added_mass_diagonal=(0.0,) * 6,
            schwerkraft_beruecksichtigt=True,
        )


def test_gestufter_solver_loest_geradeaus_und_gekoppelte_bilanz():
    fortschritt = []
    ergebnis = loese_stationaer(
        _TestKraftfunktion(),
        charakteristische_kraft_N=4.0,
        charakteristische_laenge_m=2.0,
        referenzgeschwindigkeit_m_s=2.0,
        fortschritt=fortschritt.append,
    )

    assert ergebnis.konvergiert
    assert len(ergebnis.stufen) == 2
    assert fortschritt == list(ergebnis.stufen)
    assert all(stufe.konvergiert for stufe in ergebnis.stufen)
    assert ergebnis.stufen[-1].geschwindigkeit_m_s == pytest.approx(
        (2.0, 0.0, 0.0), abs=1e-5)
    assert ergebnis.stufen[-1].pose[2] == pytest.approx(-0.2, abs=1e-5)
    assert ergebnis.stufen[-1].pose[5] == pytest.approx(0.0, abs=1e-5)
    assert ergebnis.stufen[-1].winkelgeschwindigkeit_rad_s == pytest.approx(
        (0.0, 0.0, 0.0))
    assert max(
        ergebnis.stufen[-1].normierte_restkraft,
        ergebnis.stufen[-1].normiertes_restmoment,
    ) <= 0.01
    assert ergebnis.ruderwinkel_rad == 0.0


def test_stabiles_gleichgewicht_besteht_zehnsekunden_verifikation():
    kraftfunktion = _StabilesTestmodell()
    stationaer = loese_stationaer(
        kraftfunktion,
        charakteristische_kraft_N=2.0,
        charakteristische_laenge_m=1.0,
        referenzgeschwindigkeit_m_s=2.0,
    )

    pruefung = pruefe_stationaer_dynamisch(
        kraftfunktion, stationaer.stufen[-1],
        masse_kg=1.0, traegheit_koerper=np.eye(3),
        charakteristische_laenge_m=1.0, dt_s=0.01, g_m_pro_s2=9.81)

    assert pruefung.bestanden
    assert pruefung.simulierte_dauer_s == pytest.approx(10.0)
    assert pruefung.relative_vorwaertsabweichung < 0.01


def test_instabiles_gleichgewicht_wird_dynamisch_abgelehnt():
    class InstabilesModell(_StabilesTestmodell):
        def __call__(self, pose, v, omega):
            ergebnis = super().__call__(pose, v, omega)
            ergebnis.F_gesamt = Vektor(
                (2.0 + 2.0 * (v[0] - 2.0), ergebnis.F_gesamt.y,
                 ergebnis.F_gesamt.z))
            ergebnis.F_A = ergebnis.F_gesamt
            return ergebnis

    stufe = StationaereStufe(
        "gekoppeltes Gleichgewicht", True, 1,
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (2.001, 0.0, 0.0), (0.0, 0.0, 0.0),
        (0.002, 0.0, 0.0), (0.0, 0.0, 0.0),
        0.001, 0.0)

    pruefung = pruefe_stationaer_dynamisch(
        InstabilesModell(), stufe, masse_kg=1.0,
        traegheit_koerper=np.eye(3), charakteristische_laenge_m=1.0,
        dt_s=0.01, g_m_pro_s2=9.81)

    assert not pruefung.bestanden
    assert pruefung.relative_vorwaertsabweichung > 0.01


def test_dynamikfehler_liefert_teilpruefung_mit_explizitem_grund():
    aufrufe = 0

    def modell_mit_fehler(_pose, v, omega):
        nonlocal aufrufe
        aufrufe += 1
        if aufrufe > 1:
            raise ValueError("eingespritzter nicht-endlicher Zustand")
        return SimpleNamespace(
            F_gesamt=Vektor((0.0, 0.0, 0.0)),
            F_A=Vektor((0.0, 0.0, 0.0)),
            M_gesamt=Vektor((0.0, 0.0, 0.0)),
            M=Vektor((0.0, 0.0, 0.0)),
            added_mass_diagonal=(0.0,) * 6,
            schwerkraft_beruecksichtigt=True,
        )

    stationaer = StationaereStufe(
        "gekoppeltes Gleichgewicht", True, 1,
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0), (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0, 0.0)

    pruefung = pruefe_stationaer_dynamisch(
        modell_mit_fehler, stationaer, masse_kg=1.0,
        traegheit_koerper=np.eye(3), charakteristische_laenge_m=1.0,
        dt_s=0.01, g_m_pro_s2=9.81)

    assert not pruefung.bestanden
    assert pruefung.simulierte_dauer_s == pytest.approx(0.01)
    assert "eingespritzter nicht-endlicher Zustand" in pruefung.fehlergrund


def test_solver_veraendert_den_festen_ruderwinkel_nicht():
    with pytest.raises(ValueError, match="festen Modell-Eingang"):
        loese_stationaer(
            _TestKraftfunktion(ruderwinkel_rad=0.1),
            charakteristische_kraft_N=4.0,
            charakteristische_laenge_m=2.0,
            referenzgeschwindigkeit_m_s=2.0,
            ruderwinkel_rad=0.0,
        )


def test_solver_lehnt_unbrauchbar_kleine_normierung_ab():
    with pytest.raises(ValueError, match="Skalierungen"):
        loese_stationaer(
            _TestKraftfunktion(),
            charakteristische_kraft_N=1e-10,
            charakteristische_laenge_m=2.0,
            referenzgeschwindigkeit_m_s=2.0,
        )


def test_solver_meldet_singularitaet_ohne_erfolgsschein():
    def konstante_kraft(_pose, v, omega):
        return SimpleNamespace(
            F_gesamt=Vektor((1.0, 0.0, 0.0)),
            M_gesamt=Vektor((0.0, 0.0, 0.0)),
        )

    with pytest.raises(StationaerSolverFehler, match="Jacobi"):
        loese_stationaer(
            konstante_kraft,
            charakteristische_kraft_N=1.0,
            charakteristische_laenge_m=1.0,
            referenzgeschwindigkeit_m_s=1.0,
        )
