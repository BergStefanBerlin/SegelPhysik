"""Gestufter Gleichgewichtssolver fuer stationaere Hydrodynamik."""
from __future__ import annotations

from dataclasses import dataclass
import math
import time

import numpy as np

from .dynamik_6dof import (
    Zustand6DOF,
    quaternion_aus_matrix,
    quaternion_matrix,
    schritt,
)


@dataclass(frozen=True, slots=True)
class StationaereStufe:
    name: str
    konvergiert: bool
    iterationen: int
    pose: tuple[float, float, float, float, float, float]
    geschwindigkeit_m_s: tuple[float, float, float]
    winkelgeschwindigkeit_rad_s: tuple[float, float, float]
    restkraft_N: tuple[float, float, float]
    restmoment_Nm: tuple[float, float, float]
    normierte_restkraft: float
    normiertes_restmoment: float


@dataclass(frozen=True, slots=True)
class StationaeresErgebnis:
    konvergiert: bool
    stufen: tuple[StationaereStufe, ...]
    laufzeit_s: float
    ruderwinkel_rad: float


@dataclass(frozen=True, slots=True)
class StationaereDynamikPruefung:
    bestanden: bool
    simulierte_dauer_s: float
    vorwaerts_start_m_s: float
    vorwaerts_ende_m_s: float
    relative_vorwaertsabweichung: float
    orientierung_mitte_rad: float
    orientierung_ende_rad: float
    winkelgeschwindigkeit_mitte_rad_s: float
    winkelgeschwindigkeit_ende_rad_s: float
    querfahrt_mitte_m_s: float
    querfahrt_ende_m_s: float
    laufzeit_s: float
    fehlergrund: str | None = None


class StationaerSolverFehler(RuntimeError):
    """Solverfehler mit explizitem letztem gueltigen Teilgleichgewicht."""

    def __init__(self, nachricht, *, stufen=()):
        super().__init__(nachricht)
        self.stufen = tuple(stufen)


def _rotation(phi, theta, psi):
    cphi, sphi = math.cos(phi), math.sin(phi)
    ctheta, stheta = math.cos(theta), math.sin(theta)
    cpsi, spsi = math.cos(psi), math.sin(psi)
    rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cphi, -sphi],
        [0.0, sphi, cphi],
    ])
    ry = np.array([
        [ctheta, 0.0, stheta],
        [0.0, 1.0, 0.0],
        [-stheta, 0.0, ctheta],
    ])
    rz = np.array([
        [cpsi, -spsi, 0.0],
        [spsi, cpsi, 0.0],
        [0.0, 0.0, 1.0],
    ])
    return rz @ ry @ rx


def _pose_und_bewegung(werte):
    u, z, theta, v, phi, psi = werte
    quaternion = quaternion_aus_matrix(_rotation(phi, theta, psi))
    pose = ((0.0, 0.0, float(z)), quaternion)
    return (
        pose,
        np.array((u, v, 0.0), dtype=np.float64),
        np.zeros(3, dtype=np.float64),
    )


def _beitrag_werte(ergebnis):
    kraft = np.asarray(ergebnis.F_gesamt.as_array(), dtype=np.float64)
    moment = np.asarray(ergebnis.M_gesamt.as_array(), dtype=np.float64)
    if (kraft.shape != (3,) or moment.shape != (3,)
            or not np.isfinite(kraft).all()
            or not np.isfinite(moment).all()):
        raise StationaerSolverFehler(
            "Kraftmodell lieferte ungueltige Kraft- oder Momentenwerte")
    return kraft, moment


def _residuum(kraftfunktion, werte, stufe, kraftskala, momentskala):
    pose, v, omega = _pose_und_bewegung(werte)
    kraft, moment = _beitrag_werte(kraftfunktion(pose, v=v, omega=omega))
    if stufe == 1:
        normiert = np.array((
            kraft[0] / kraftskala,
            kraft[2] / kraftskala,
            moment[1] / momentskala,
        ))
    else:
        normiert = np.concatenate((
            kraft / kraftskala, moment / momentskala))
    return normiert, kraft, moment


def _stufe_ergebnis(name, werte, kraft, moment, kraftskala, momentskala,
                    iterationen, stufe):
    pose, v, omega = _pose_und_bewegung(werte)
    phi = float(werte[4])
    theta = float(werte[2])
    kraft_auswahl = kraft[[0, 2]] if stufe == 1 else kraft
    moment_auswahl = moment[[1]] if stufe == 1 else moment
    norm_kraft = float(np.linalg.norm(kraft_auswahl) / kraftskala)
    norm_moment = float(np.linalg.norm(moment_auswahl) / momentskala)
    return StationaereStufe(
        name=name,
        konvergiert=max(norm_kraft, norm_moment) <= 0.01,
        iterationen=iterationen,
        pose=(0.0, 0.0, float(werte[1]), phi, theta, float(werte[5])),
        geschwindigkeit_m_s=tuple(float(x) for x in v),
        winkelgeschwindigkeit_rad_s=tuple(float(x) for x in omega),
        restkraft_N=tuple(float(x) for x in kraft),
        restmoment_Nm=tuple(float(x) for x in moment),
        normierte_restkraft=norm_kraft,
        normiertes_restmoment=norm_moment,
    )


def loese_stationaer(kraftfunktion, *, charakteristische_kraft_N,
                     charakteristische_laenge_m, referenzgeschwindigkeit_m_s,
                     start=None, max_iterationen=40, toleranz=1e-5,
                     ruderwinkel_rad=0.0, fortschritt=None):
    """Loest zuerst Geradeausfahrt und danach sechs gekoppelte Bilanzgroessen.

    Stufe 1 bestimmt Vorwaertsgeschwindigkeit, Eintauchen und Trim mit
    festgehaltenem Roll-, Drift- und Gierfreiheitsgrad. Stufe 2 gibt Roll,
    Drift und Gierorientierung frei und loest alle Kraefte/Momente erneut
    gemeinsam. Der stationaere Zustand hat keine Winkelgeschwindigkeit.
    Der Ruderwinkel ist ausschliesslich Metadatum des Ergebnisses und wird
    durch den Solver nicht veraendert.
    """
    skalare = (
        charakteristische_kraft_N, charakteristische_laenge_m,
        referenzgeschwindigkeit_m_s, toleranz, ruderwinkel_rad,
    )
    if not all(math.isfinite(float(x)) for x in skalare):
        raise ValueError("Solverparameter muessen endlich sein")
    kraftskala = float(charakteristische_kraft_N)
    laenge = float(charakteristische_laenge_m)
    geschwindigkeit = float(referenzgeschwindigkeit_m_s)
    if kraftskala <= 0.0 or laenge <= 0.0 or geschwindigkeit <= 0.0:
        raise ValueError("Kraft, Laenge und Referenzgeschwindigkeit muessen "
                         "positiv sein")
    if kraftskala < 1e-6 or laenge < 1e-6 or geschwindigkeit < 1e-6:
        raise ValueError("Solver-Skalierungen unter 1e-6 SI-Einheiten sind "
                         "nicht aussagekraeftig")
    if not 0.0 < toleranz <= 0.01:
        raise ValueError("Toleranz muss im Bereich (0, 1 %] liegen")
    if isinstance(max_iterationen, bool) or not isinstance(
            max_iterationen, int) or max_iterationen < 1:
        raise ValueError("Maximaliterationen muessen positiv sein")
    if fortschritt is not None and not callable(fortschritt):
        raise TypeError("Fortschritt muss aufrufbar sein")
    if abs(float(ruderwinkel_rad)) > math.pi / 2.0:
        raise ValueError("Ruderwinkel muss zwischen -90 und +90 Grad liegen")
    hydrodynamik = getattr(kraftfunktion, "hydrodynamik", None)
    aktueller_ruderwinkel = getattr(
        hydrodynamik, "ruderwinkel_rad", float(ruderwinkel_rad))
    if not math.isclose(
            float(aktueller_ruderwinkel), float(ruderwinkel_rad),
            rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(
            "Ruderwinkel im Solver muss dem festen Modell-Eingang entsprechen")

    momentskala = kraftskala * laenge
    skalen = np.array((
        geschwindigkeit, laenge, 1.0, geschwindigkeit, 1.0, 1.0))
    werte = np.zeros(6, dtype=np.float64)
    if start is not None:
        startwerte = np.asarray(start, dtype=np.float64)
        if startwerte.shape != (6,) or not np.isfinite(startwerte).all():
            raise ValueError("Startwert muss sechs endliche Werte enthalten")
        werte[:] = startwerte

    stufen = []
    startzeit = time.perf_counter()
    for stufe, name, indices in (
            (1, "Geradeausfahrt", (0, 1, 2)),
            (2, "gekoppeltes Gleichgewicht", (0, 1, 2, 3, 4, 5))):
        konvergiert = False
        residuum = None
        for iteration in range(1, max_iterationen + 1):
            residuum, kraft, moment = _residuum(
                kraftfunktion, werte, stufe, kraftskala, momentskala)
            if np.linalg.norm(residuum, ord=np.inf) <= toleranz:
                konvergiert = True
                break
            jacobi = np.zeros((len(indices), len(indices)))
            for spalte, index in enumerate(indices):
                schritt = 1e-5 * max(1.0, abs(werte[index] / skalen[index]))
                probe = werte.copy()
                probe[index] += schritt * skalen[index]
                versetzt, _fk, _fm = _residuum(
                    kraftfunktion, probe, stufe, kraftskala, momentskala)
                jacobi[:, spalte] = (
                    versetzt - residuum) / schritt
            try:
                delta = np.linalg.solve(jacobi, -residuum)
            except np.linalg.LinAlgError as fehler:
                raise StationaerSolverFehler(
                    "Singulaere Jacobi in Stufe %s" % name,
                    stufen=stufen) from fehler
            if not np.isfinite(delta).all():
                raise StationaerSolverFehler(
                    "Nicht-endlicher Newton-Schritt in Stufe %s" % name,
                    stufen=stufen)
            delta = np.clip(delta, -0.5, 0.5)
            basis = werte.copy()
            basis_norm = np.linalg.norm(residuum)
            verbessert = False
            for daempfung in (1.0, 0.5, 0.25, 0.125, 0.0625):
                probe = basis.copy()
                probe[list(indices)] += (
                    daempfung * delta * skalen[list(indices)])
                probe_residuum, _fk, _fm = _residuum(
                    kraftfunktion, probe, stufe,
                    kraftskala, momentskala)
                if np.linalg.norm(probe_residuum) < basis_norm:
                    werte = probe
                    verbessert = True
                    break
            if not verbessert:
                raise StationaerSolverFehler(
                    "Newton-Stufe %s verbessert das Residuum nicht" % name,
                    stufen=stufen)
        if not konvergiert:
            residuum, kraft, moment = _residuum(
                kraftfunktion, werte, stufe, kraftskala, momentskala)
        else:
            residuum, kraft, moment = _residuum(
                kraftfunktion, werte, stufe, kraftskala, momentskala)
        ergebnis = _stufe_ergebnis(
            name, werte, kraft, moment, kraftskala, momentskala, iteration,
            stufe)
        stufen.append(ergebnis)
        if fortschritt is not None:
            fortschritt(ergebnis)
        if (not konvergiert
                or np.linalg.norm(residuum, ord=np.inf) > toleranz):
            raise StationaerSolverFehler(
                "Keine Konvergenz in Stufe %s nach %d Iterationen"
                % (name, iteration),
                stufen=stufen)

    return StationaeresErgebnis(
        konvergiert=True,
        stufen=tuple(stufen),
        laufzeit_s=time.perf_counter() - startzeit,
        ruderwinkel_rad=float(ruderwinkel_rad),
    )


def pruefe_stationaer_dynamisch(kraftfunktion, stufe, *, masse_kg,
                                traegheit_koerper,
                                charakteristische_laenge_m, dt_s,
                                g_m_pro_s2,
                                dauer_s=10.0,
                                geschwindigkeitstoleranz=0.01):
    """Verifiziert einen stationaeren Zustand mit unveraenderter Kraft."""
    parameter = (masse_kg, charakteristische_laenge_m,
                 dt_s, g_m_pro_s2, dauer_s,
                 geschwindigkeitstoleranz)
    if not all(math.isfinite(float(wert)) for wert in parameter):
        raise ValueError("Dynamikpruefungsparameter muessen endlich sein")
    if (masse_kg <= 0.0 or charakteristische_laenge_m <= 0.0
            or dt_s <= 0.0 or g_m_pro_s2 <= 0.0
            or dauer_s <= 0.0
            or not 0.0 < geschwindigkeitstoleranz <= 0.01):
        raise ValueError("Dynamikpruefungsparameter liegen ausserhalb "
                         "des gueltigen Bereichs")
    if not stufe.konvergiert:
        raise ValueError("Dynamikpruefung erfordert eine konvergierte Stufe")
    inertia = np.asarray(traegheit_koerper, dtype=np.float64)
    if (inertia.shape != (3, 3) or not np.isfinite(inertia).all()
            or not np.allclose(inertia, inertia.T, atol=1e-10, rtol=0.0)
            or np.linalg.eigvalsh(inertia)[0] <= 0.0):
        raise ValueError("Traegheitstensor muss positiv definit sein")

    startzeit = time.perf_counter()
    rotation = _rotation(stufe.pose[3], stufe.pose[4], stufe.pose[5])
    quaternion = quaternion_aus_matrix(rotation)
    geschwindigkeit_start = np.asarray(
        stufe.geschwindigkeit_m_s, dtype=np.float64)
    omega_start = np.asarray(
        stufe.winkelgeschwindigkeit_rad_s, dtype=np.float64)
    zustand = Zustand6DOF(
        position=(0.0, 0.0, float(stufe.pose[2])),
        quaternion=tuple(float(x) for x in quaternion),
        geschwindigkeit_koerper=tuple(
            float(x) for x in rotation.T @ geschwindigkeit_start),
        winkelgeschwindigkeit_koerper=tuple(
            float(x) for x in rotation.T @ omega_start),
    )
    quaternion_start = quaternion
    halbzeit = dauer_s / 2.0
    vergangen = 0.0
    mitte = None
    fehlergrund = None
    while vergangen < dauer_s:
        schritt_s = min(float(dt_s), dauer_s - vergangen)
        try:
            zustand, _ergebnis = schritt(
                zustand, kraftfunktion, masse_kg, inertia, schritt_s,
                g_m_pro_s2)
        except (ValueError, FloatingPointError, OverflowError,
                np.linalg.LinAlgError) as fehler:
            fehlergrund = "%s: %s" % (type(fehler).__name__, fehler)
            break
        vergangen += schritt_s
        if mitte is None and vergangen >= halbzeit:
            q_mitte = np.asarray(zustand.quaternion, dtype=np.float64)
            r_mitte = quaternion_matrix(q_mitte)
            v_mitte = r_mitte @ np.asarray(
                zustand.geschwindigkeit_koerper, dtype=np.float64)
            mitte = (
                2.0 * math.acos(float(np.clip(
                    abs(np.dot(quaternion_start, q_mitte)), 0.0, 1.0))),
                float(np.linalg.norm(
                    zustand.winkelgeschwindigkeit_koerper)),
                float(np.linalg.norm(v_mitte[1:])),
            )
    if mitte is None:
        q_mitte = np.asarray(zustand.quaternion, dtype=np.float64)
        r_mitte = quaternion_matrix(q_mitte)
        v_mitte = r_mitte @ np.asarray(
            zustand.geschwindigkeit_koerper, dtype=np.float64)
        mitte = (
            2.0 * math.acos(float(np.clip(
                abs(np.dot(quaternion_start, q_mitte)), 0.0, 1.0))),
            float(np.linalg.norm(zustand.winkelgeschwindigkeit_koerper)),
            float(np.linalg.norm(v_mitte[1:])),
        )
    quaternion_ende = np.asarray(zustand.quaternion, dtype=np.float64)
    rotation_ende = quaternion_matrix(quaternion_ende)
    geschwindigkeit_ende = rotation_ende @ np.asarray(
        zustand.geschwindigkeit_koerper, dtype=np.float64)
    abweichung = abs(
        float(geschwindigkeit_ende[0]) - float(geschwindigkeit_start[0]))
    bezugsgeschwindigkeit = max(
        abs(float(geschwindigkeit_start[0])), 1e-6)
    relative_abweichung = abweichung / bezugsgeschwindigkeit
    orientierung_ende = 2.0 * math.acos(float(np.clip(
        abs(np.dot(quaternion_start, quaternion_ende)), 0.0, 1.0)))
    omega_ende = float(np.linalg.norm(
        zustand.winkelgeschwindigkeit_koerper))
    querfahrt_ende = float(np.linalg.norm(geschwindigkeit_ende[1:]))
    orientierungstoleranz = math.radians(0.1)
    omega_toleranz = max(
        1e-4, 0.01 * bezugsgeschwindigkeit
        / float(charakteristische_laenge_m))
    querfahrtstoleranz = max(1e-4, 0.01 * bezugsgeschwindigkeit)
    kein_wachstum = (
        orientierung_ende <= mitte[0] + orientierungstoleranz
        and omega_ende <= mitte[1] + omega_toleranz
        and querfahrt_ende <= mitte[2] + querfahrtstoleranz)
    return StationaereDynamikPruefung(
        bestanden=(fehlergrund is None
                   and relative_abweichung <= geschwindigkeitstoleranz
                   and kein_wachstum),
        simulierte_dauer_s=float(vergangen),
        vorwaerts_start_m_s=float(geschwindigkeit_start[0]),
        vorwaerts_ende_m_s=float(geschwindigkeit_ende[0]),
        relative_vorwaertsabweichung=relative_abweichung,
        orientierung_mitte_rad=mitte[0],
        orientierung_ende_rad=orientierung_ende,
        winkelgeschwindigkeit_mitte_rad_s=mitte[1],
        winkelgeschwindigkeit_ende_rad_s=omega_ende,
        querfahrt_mitte_m_s=mitte[2],
        querfahrt_ende_m_s=querfahrt_ende,
        laufzeit_s=time.perf_counter() - startzeit,
        fehlergrund=fehlergrund,
    )
