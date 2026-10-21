from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core.auftrieb import Vektor, baue_kraftfunktion_6dof
from segelphysik.core.dynamik_6dof import (
    Zustand6DOF, quaternion_matrix, quaternion_normalisieren, schritt,
)
from segelphysik.core.koerper_formen import build_box


def _kraft(kraft=(0.0, 0.0, 0.0), moment=(0.0, 0.0, 0.0)):
    return SimpleNamespace(F_A=Vektor(kraft), M=Vektor(moment))


def _quaternion_multiplizieren(a, b):
    w, x, y, z = a
    p, q, r, s = b
    return (
        w * p - x * q - y * r - z * s,
        w * q + x * p + y * s - z * r,
        w * r - x * s + y * p + z * q,
        w * s + x * r - y * q + z * p,
    )


def test_quaternion_wird_normiert_und_transformiert_koerperachsen():
    q = np.array((2.0 ** -0.5, 0.0, 2.0 ** -0.5, 0.0))

    rotation = quaternion_matrix(q * 3.0)

    assert np.linalg.norm(quaternion_normalisieren(q * 3.0)) == pytest.approx(1.0)
    assert rotation @ np.array((1.0, 0.0, 0.0)) == pytest.approx(
        (0.0, 0.0, -1.0))
    assert rotation.T @ rotation == pytest.approx(np.eye(3))


def test_reine_translation_und_freier_fall_haben_analytische_loesung():
    masse, dt, g = 2.0, 0.1, 9.81
    start = Zustand6DOF(geschwindigkeit_koerper=(1.0, 0.0, 0.0))

    ende, _ = schritt(
        start, lambda *_args, **_kwargs: _kraft(),
        masse, np.diag((1.0, 2.0, 3.0)), dt, g)

    assert ende.geschwindigkeit_koerper == pytest.approx(
        (1.0, 0.0, -g * dt))
    assert ende.position == pytest.approx(
        (dt, 0.0, -g * dt * dt))
    assert ende.quaternion == pytest.approx((1.0, 0.0, 0.0, 0.0))


def test_koerperachsen_translation_wird_in_weltkoordinaten_transformiert():
    masse, g = 1.0, 9.81
    q = (2.0 ** -0.5, 0.0, 2.0 ** -0.5, 0.0)
    start = Zustand6DOF(
        quaternion=q, geschwindigkeit_koerper=(1.0, 0.0, 0.0))
    auftrieb = Vektor((0.0, 0.0, masse * g))

    ende, _ = schritt(
        start, lambda *_args, **_kwargs: SimpleNamespace(
            F_A=auftrieb, M=Vektor((0.0, 0.0, 0.0))),
        masse, np.eye(3), 0.1, g)

    assert ende.position == pytest.approx((0.0, 0.0, -0.1), abs=1e-12)


def test_reine_rotation_nutzt_koerpertraegheit_und_normiertes_quaternion():
    start = Zustand6DOF()

    ende, _ = schritt(
        start, lambda *_args, **_kwargs: _kraft(moment=(2.0, 0.0, 0.0)),
        1.0, np.diag((2.0, 3.0, 4.0)), 0.1, 9.81)

    assert ende.winkelgeschwindigkeit_koerper == pytest.approx(
        (0.1, 0.0, 0.0))
    assert np.linalg.norm(ende.quaternion) == pytest.approx(1.0)
    assert ende.quaternion[1] == pytest.approx(np.sin(0.005))


def test_starke_lineare_rotationsdaempfung_bleibt_implizit_stabil():
    masse, g, dt = 1.0, 9.81, 0.004

    def kraftfunktion(_lage, *, omega, **_kwargs):
        return SimpleNamespace(
            F_A=Vektor((0.0, 0.0, masse * g)),
            M=Vektor((-8000.0 * omega[0], 0.0, 0.0)),
            linear_widerstand=(0.0, 0.0, 0.0, 8000.0, 0.0, 0.0),
        )

    zustand = Zustand6DOF(winkelgeschwindigkeit_koerper=(1.0, 0.0, 0.0))
    for _ in range(100):
        zustand, _ = schritt(
            zustand, kraftfunktion, masse, np.eye(3), dt, g)

    assert np.isfinite(zustand.winkelgeschwindigkeit_koerper).all()
    assert zustand.winkelgeschwindigkeit_koerper[0] == pytest.approx(
        (1.0 / (1.0 + dt * 8000.0)) ** 100)
    assert zustand.winkelgeschwindigkeit_koerper[0] >= 0.0


def test_drehimpuls_aendert_sich_entsprechend_dem_aeusseren_drehmoment():
    masse, dt, g = 2.0, 1e-7, 9.81
    traegheit = np.diag((2.0, 3.0, 4.0))
    start = Zustand6DOF(
        quaternion=(np.cos(0.2), 0.0, 0.0, np.sin(0.2)),
        winkelgeschwindigkeit_koerper=(0.3, -0.2, 0.1))
    moment = np.array((0.2, -0.4, 0.1))
    rotation_start = quaternion_matrix(start.quaternion)
    drehimpuls_start = (
        rotation_start @ traegheit
        @ np.asarray(start.winkelgeschwindigkeit_koerper))

    ende, _ = schritt(
        start,
        lambda *_args, **_kwargs: _kraft(
            kraft=(0.0, 0.0, masse * g), moment=moment),
        masse, traegheit, dt, g)

    drehimpuls_ende = (
        quaternion_matrix(ende.quaternion) @ traegheit
        @ np.asarray(ende.winkelgeschwindigkeit_koerper))
    assert drehimpuls_ende - drehimpuls_start == pytest.approx(
        moment * dt, abs=1e-12)


def test_dynamik_ist_bei_welt_drehung_um_schwerkraftachse_invariant():
    winkel = 0.7
    qz = (np.cos(winkel / 2.0), 0.0, 0.0, np.sin(winkel / 2.0))
    rz = quaternion_matrix(qz)
    traegheit = np.diag((2.0, 3.0, 4.0))
    masse, g, dt = 2.0, 9.81, 0.002
    start = Zustand6DOF(
        position=(0.4, -0.3, 1.0),
        quaternion=(np.cos(0.15), np.sin(0.15), 0.0, 0.0),
        geschwindigkeit_koerper=(0.2, -0.1, 0.3),
        winkelgeschwindigkeit_koerper=(0.1, 0.2, -0.15))
    kraft = np.array((0.5, -0.2, masse * g + 0.4))
    moment = np.array((0.1, 0.4, -0.3))

    ende, _ = schritt(
        start, lambda *_args, **_kwargs: _kraft(kraft, moment),
        masse, traegheit, dt, g)
    gedrehter_start = Zustand6DOF(
        position=tuple(rz @ np.asarray(start.position)),
        quaternion=_quaternion_multiplizieren(qz, start.quaternion),
        geschwindigkeit_koerper=start.geschwindigkeit_koerper,
        winkelgeschwindigkeit_koerper=start.winkelgeschwindigkeit_koerper)
    ende_gedreht, _ = schritt(
        gedrehter_start,
        lambda *_args, **_kwargs: _kraft(rz @ kraft, rz @ moment),
        masse, traegheit, dt, g)

    assert ende_gedreht.position == pytest.approx(rz @ ende.position)
    assert quaternion_matrix(ende_gedreht.quaternion) == pytest.approx(
        rz @ quaternion_matrix(ende.quaternion))
    assert ende_gedreht.geschwindigkeit_koerper == pytest.approx(
        ende.geschwindigkeit_koerper)
    assert ende_gedreht.winkelgeschwindigkeit_koerper == pytest.approx(
        ende.winkelgeschwindigkeit_koerper)


def test_freie_rotation_um_hauptachse_erzeugt_keine_kuenstliche_kraefte():
    start = Zustand6DOF(winkelgeschwindigkeit_koerper=(0.0, 0.0, 0.5))
    torque_aufrufe = []

    ende, ergebnis = schritt(
        start,
        lambda *_args, **_kwargs: (
            torque_aufrufe.append(True) or _kraft()),
        2.0, np.diag((1.0, 2.0, 3.0)), 0.01, 9.81)

    assert ende.winkelgeschwindigkeit_koerper == pytest.approx(
        (0.0, 0.0, 0.5))
    assert ende.quaternion == pytest.approx(
        (np.cos(0.0025), 0.0, 0.0, np.sin(0.0025)))
    assert ergebnis.M.as_array() == pytest.approx(np.zeros(3))
    assert torque_aufrufe == [True]


def test_6dof_hydrostatik_hat_denselben_referenzwert_in_nullpose():
    box = build_box(2.0, 2.0, 2.0)
    koerper = SimpleNamespace(
        blatt_meshes=[box], r_S=np.zeros(3), teile=[])
    kraft = baue_kraftfunktion_6dof(koerper, rho_w=1000.0, g=9.81)

    result = kraft((np.zeros(3), (1.0, 0.0, 0.0, 0.0)))

    assert result.V_tauch == pytest.approx(4.0)
    assert result.F_A.as_array() == pytest.approx((0.0, 0.0, 39240.0))
    assert result.M.as_array() == pytest.approx(np.zeros(3))


@pytest.mark.parametrize(("position", "quaternion"), [
    ((0.2, -0.1, 0.0), (np.cos(0.2), np.sin(0.2), 0.0, 0.0)),
    ((-0.1, 0.3, -0.2), (np.cos(0.15), 0.0, np.sin(0.15), 0.0)),
    ((0.1, 0.2, -2.0), (0.8, 0.2, -0.3, 0.45)),
    ((0.1, 0.2, 3.0), (0.8, 0.2, -0.3, 0.45)),
])
def test_6dof_koerperframe_union_stimmt_mit_weltframe_referenz_ueberein(
        position, quaternion):
    from segelphysik.core.auftrieb import kraftfunktion_berechne

    box = build_box(2.0, 2.0, 2.0)
    koerper = SimpleNamespace(
        blatt_meshes=[box], r_S=np.zeros(3), teile=[])
    kraft = baue_kraftfunktion_6dof(koerper, rho_w=1000.0, g=9.81)
    rotation = quaternion_matrix(quaternion)
    welt_mesh = (box[0] @ rotation.T + np.asarray(position), box[1])
    referenz = kraftfunktion_berechne(
        SimpleNamespace(blatt_meshes=[welt_mesh], r_S=np.asarray(position),
                        teile=[]),
        (0.0, 0.0, 0.0), rho_w=1000.0, g=9.81, pfad="exakt_union")

    result = kraft((position, quaternion))

    assert result.V_tauch == pytest.approx(referenz.V_tauch, abs=1e-12)
    assert result.K.as_array() == pytest.approx(
        referenz.K.as_array(), abs=1e-12)
    assert result.F_A.as_array() == pytest.approx(
        referenz.F_A.as_array(), abs=1e-8)
    assert result.M.as_array() == pytest.approx(
        referenz.M.as_array(), abs=1e-10)


def test_6dof_koerperfestes_raster_ist_opt_in_und_wertet_pose_aus():
    box = build_box(2.0, 2.0, 2.0)
    koerper = SimpleNamespace(
        blatt_meshes=[box], r_S=np.zeros(3), teile=[])
    kraft = baue_kraftfunktion_6dof(
        koerper, rho_w=1000.0, g=9.81,
        pfad="voxel_koerperfest", aufloesung=0.5)

    result = kraft((np.array((0.0, 0.0, 0.0)), (1.0, 0.0, 0.0, 0.0)))

    assert result.V_tauch == pytest.approx(4.0)
    assert result.K.as_array() == pytest.approx((0.0, 0.0, -0.5))


def test_6dof_broadphase_bezieht_alle_teilmeshes_ein():
    box = build_box(2.0, 2.0, 2.0)
    trocken = (box[0] + np.array((0.0, 0.0, 4.0)), box[1])
    nass = (box[0] + np.array((0.0, 0.0, -4.0)), box[1])
    koerper = SimpleNamespace(
        blatt_meshes=[trocken, nass], r_S=np.zeros(3), teile=[])
    kraft = baue_kraftfunktion_6dof(koerper, rho_w=1000.0, g=9.81)

    result = kraft((np.zeros(3), (1.0, 0.0, 0.0, 0.0)))

    assert result.V_tauch == pytest.approx(8.0)
    assert result.F_A.as_array() == pytest.approx((0.0, 0.0, 78480.0))


@pytest.mark.slow
def test_opencl_voxel_hydrostatik_stimmt_mit_cpu_ueberein(caplog):
    from segelphysik.core.physik_backend import (
        BackendNichtVerfuegbar, OpenCLBackend,
    )

    try:
        geraete = OpenCLBackend.gpu_namen_ermitteln()
    except BackendNichtVerfuegbar as fehler:
        pytest.skip(str(fehler))
    if not geraete:
        pytest.skip("Kein OpenCL-GPU-Gerät verfügbar")

    box = build_box(2.0, 2.0, 2.0)
    koerper = SimpleNamespace(
        blatt_meshes=[box], r_S=np.zeros(3), teile=[])
    gpu = baue_kraftfunktion_6dof(
        koerper, rho_w=1000.0, g=9.81,
        pfad="voxel_opencl", aufloesung=0.25)
    cpu = baue_kraftfunktion_6dof(
        koerper, rho_w=1000.0, g=9.81,
        pfad="voxel_koerperfest", aufloesung=0.25)
    poses = (
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)),
        ((0.0, 0.0, -0.1), (np.cos(0.1), np.sin(0.1), 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (np.cos(0.1), 0.0, np.sin(0.1), 0.0)),
        ((0.0, 0.0, 0.125), (1.0, 0.0, 0.0, 0.0)),
    )
    for pose in poses:
        gpu_result = gpu(pose)
        cpu_result = cpu(pose)
        assert gpu_result.V_tauch == pytest.approx(
            cpu_result.V_tauch, abs=1e-12)
        assert gpu_result.K.as_array() == pytest.approx(
            cpu_result.K.as_array(), abs=1e-12)
        assert gpu_result.M.as_array() == pytest.approx(
            cpu_result.M.as_array(), abs=1e-10)
    assert "numerisch auf der Wasserfläche" in caplog.text


def test_opencl_ausfuehrungsfehler_wiederholt_pose_auf_cpu(
        monkeypatch, caplog):
    from segelphysik.core.physik_backend import (
        BackendFehler, OpenCLVoxelHydrostatik,
    )

    class FehlerBackend:
        name = "Test-GPU"

        def auswerten_6dof(self, *_args):
            raise BackendFehler("Kernelfehler")

    monkeypatch.setattr(
        OpenCLVoxelHydrostatik, "oeffnen",
        classmethod(lambda cls, *_args: FehlerBackend()))
    box = build_box(2.0, 2.0, 2.0)
    koerper = SimpleNamespace(
        blatt_meshes=[box], r_S=np.zeros(3), teile=[])
    gpu = baue_kraftfunktion_6dof(
        koerper, pfad="voxel_opencl", aufloesung=0.5)
    cpu = baue_kraftfunktion_6dof(
        koerper, pfad="voxel_koerperfest", aufloesung=0.5)
    pose = (np.zeros(3), (1.0, 0.0, 0.0, 0.0))

    assert gpu(pose).V_tauch == pytest.approx(cpu(pose).V_tauch)
    assert "dieselbe Pose läuft auf CPU weiter" in caplog.text
    assert gpu(pose).V_tauch == pytest.approx(cpu(pose).V_tauch)


@pytest.mark.parametrize("kwargs", [
    {"masse": 0.0},
    {"dt": 0.0},
    {"g": 0.0},
    {"traegheit_koerper": np.diag((1.0, 1.0, 0.0))},
])
def test_6dof_lehnt_ungueltige_dynamikparameter_ab(kwargs):
    parameter = {
        "masse": 1.0,
        "traegheit_koerper": np.eye(3),
        "dt": 0.01,
        "g": 9.81,
    }
    parameter.update(kwargs)

    with pytest.raises(ValueError):
        schritt(
            Zustand6DOF(), lambda *_args, **_kw: _kraft(),
            **parameter)


def test_6dof_validiert_geaenderten_traegheitstensor_erneut():
    traegheit = np.eye(3)
    parameter = (Zustand6DOF(), lambda *_args, **_kw: _kraft(),
                 1.0, traegheit, 0.01, 9.81)

    schritt(*parameter)
    traegheit[2, 2] = 0.0

    with pytest.raises(ValueError, match="positiv definit"):
        schritt(*parameter)
