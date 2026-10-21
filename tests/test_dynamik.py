import math
from types import SimpleNamespace

import pytest

from segelphysik.core.dynamik import (
    Bewegungszustand, schritt, schritt_mit_kraeften,
)


def _kraft(f_a_z=0.0, moment_x=0.0):
    def berechne(lage, v=None, omega=None):
        return SimpleNamespace(
            F_A=SimpleNamespace(z=f_a_z),
            M=SimpleNamespace(x=moment_x))
    return berechne


def _federkraft(masse, g, steifigkeit_z, steifigkeit_phi):
    def berechne(lage, v=None, omega=None):
        return SimpleNamespace(
            F_A=SimpleNamespace(z=masse * g - steifigkeit_z * lage[0]),
            M=SimpleNamespace(x=-steifigkeit_phi * lage[1]))
    return berechne


def _energie(zustand, masse, traegheit_xx, steifigkeit_z,
             steifigkeit_phi):
    return (
        0.5 * masse * zustand.v_z ** 2
        + 0.5 * steifigkeit_z * zustand.z ** 2
        + 0.5 * traegheit_xx * zustand.omega_x ** 2
        + 0.5 * steifigkeit_phi * zustand.phi ** 2
    )


def test_schritt_haelt_gleichgewicht_deterministisch():
    state = Bewegungszustand(z=-0.5, phi=0.1, v_z=0.0, omega_x=0.0)
    kraft = _kraft(f_a_z=100.0 * 9.81)
    ergebnis = schritt(state, kraft, 100.0, 20.0, 0.01, 9.81)
    assert ergebnis == state


def test_schritt_freier_fall_und_semiimplizite_position():
    dt = 0.1
    ergebnis = schritt(Bewegungszustand(), _kraft(), 2.0, 3.0, dt, 9.81)
    assert ergebnis.v_z == pytest.approx(-9.81 * dt)
    assert ergebnis.z == pytest.approx(-9.81 * dt * dt)


def test_schritt_mit_kraeften_gibt_verwendetes_kraefteresultat_zurueck():
    kraefteresultat = SimpleNamespace(
        F_A=SimpleNamespace(z=20.0), M=SimpleNamespace(x=2.0))
    aufrufe = []

    def kraft(*_args, **_kwargs):
        aufrufe.append(True)
        return kraefteresultat

    zustand, ergebnis = schritt_mit_kraeften(
        Bewegungszustand(), kraft, 2.0, 3.0, 0.1, 9.81)

    assert ergebnis is kraefteresultat
    assert zustand.v_z == pytest.approx((20.0 - 2.0 * 9.81) / 2.0 * 0.1)
    assert aufrufe == [True]


def test_schritt_integriert_rollmoment_und_daempfung():
    state = Bewegungszustand(phi=0.2, omega_x=0.4)
    ergebnis = schritt(state, _kraft(moment_x=12.0), 3.0, 6.0,
                       0.1, 9.81, daempfung_kraengung=3.0)
    alpha = (12.0 - 3.0 * state.omega_x) / 6.0
    omega = state.omega_x + alpha * 0.1
    assert ergebnis.omega_x == pytest.approx(omega)
    assert ergebnis.phi == pytest.approx(state.phi + omega * 0.1)


def test_schritt_reicht_geschwindigkeit_an_kraftmodell_durch():
    erhalten = []

    def kraft(lage, v=None, omega=None):
        erhalten.append((lage, v, omega))
        return SimpleNamespace(F_A=SimpleNamespace(z=0.0),
                               M=SimpleNamespace(x=0.0))

    state = Bewegungszustand(z=0.2, phi=-0.1, v_z=0.3, omega_x=-0.4)
    schritt(state, kraft, 1.0, 1.0, 0.01, 9.81)
    assert erhalten == [((0.2, -0.1, 0.0), (0.0, 0.0, 0.3), (-0.4, 0.0, 0.0))]


@pytest.mark.parametrize("args", [
    (0.0, 1.0, 0.01, 9.81, 0.0, 0.0),
    (1.0, 0.0, 0.01, 9.81, 0.0, 0.0),
    (1.0, 1.0, 0.0, 9.81, 0.0, 0.0),
    (1.0, 1.0, 0.01, 9.81, -1.0, 0.0),
])
def test_schritt_lehnt_ungueltige_parameter_ab(args):
    with pytest.raises(ValueError):
        schritt(Bewegungszustand(), _kraft(), *args)


def test_wiederholte_trajectory_ist_deterministisch():
    def simuliere():
        zustand = Bewegungszustand(z=0.2, v_z=-0.3, phi=0.05, omega_x=0.1)
        werte = []
        for _ in range(100):
            zustand = schritt(zustand, _kraft(), 5.0, 2.0,
                              0.004, 9.80665, 8.0, 2.0)
            werte.append(zustand)
        return werte

    assert simuliere() == simuliere()
    assert math.isfinite(simuliere()[-1].z)


def test_ungedaempfte_kleinbewegung_erhaelt_energie_numerisch():
    masse, traegheit, kz, kphi = 2.0, 3.0, 20.0, 12.0
    zustand = Bewegungszustand(z=0.1, phi=0.08)
    kraft = _federkraft(masse, 9.81, kz, kphi)
    startenergie = _energie(zustand, masse, traegheit, kz, kphi)
    energien = []

    for _ in range(4000):
        zustand = schritt(zustand, kraft, masse, traegheit, 0.001, 9.81)
        energien.append(_energie(zustand, masse, traegheit, kz, kphi))

    assert max(abs(energie - startenergie) for energie in energien) \
        < startenergie * 0.01


def test_passive_daempfung_verringert_energie_der_kleinbewegung():
    masse, traegheit, kz, kphi = 2.0, 3.0, 20.0, 12.0
    zustand = Bewegungszustand(z=0.2, v_z=-0.1, phi=0.15, omega_x=0.2)
    kraft = _federkraft(masse, 9.81, kz, kphi)
    startenergie = _energie(zustand, masse, traegheit, kz, kphi)

    for _ in range(10000):
        vorherige_energie = _energie(
            zustand, masse, traegheit, kz, kphi)
        zustand = schritt(
            zustand, kraft, masse, traegheit, 0.001, 9.81,
            daempfung_tauchung=1.2, daempfung_kraengung=0.8)
        assert _energie(zustand, masse, traegheit, kz, kphi) \
            <= vorherige_energie + 1e-14

    endenergie = _energie(zustand, masse, traegheit, kz, kphi)
    assert endenergie < startenergie * 0.1
    assert abs(zustand.z) < 0.05
    assert abs(zustand.phi) < 0.05
