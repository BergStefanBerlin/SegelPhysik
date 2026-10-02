# ============================================================
# hydrostatics.py - Hydrostatik (Auftrieb, CB, Momente)
# ------------------------------------------------------------
# Voxelmessung in beliebiger 3D-Lage: Jeder getauchte Punkt
# erfahrt dF = rho_w*g*dV nach oben; Kraft = Summe,
# Moment = Summe r x dF (vollstaendiges Kreuzprodukt).
# Getrennt von der Geometrie: hydro(q, R, p) bekommt das
# QuaderVoxel-Objekt, die Rotationsmatrix und die Position.
# ============================================================
import numpy as np

from config import RHO_W, G


def hydro(q, R, p):
    """Hydrostatik von Rumpf UND Anhaengen fuer Rotationsmatrix R und
    Position p. Beide Wolken verdraengen Wasser; Moment um den
    Gesamt-CG, in Koerperkomponenten."""
    W = q.P @ R.T + p
    Wk = q.Pk @ R.T + p
    cg_w = R @ q.c_body + p
    sub = W[:, 2] < 0.0
    subk = Wk[:, 2] < 0.0
    kh, kk = int(sub.sum()), int(subk.sum())
    V_sub = kh*q.dV + kk*q.dVk
    F_A = RHO_W*G*V_sub
    if V_sub > 1e-12:
        fh = RHO_W*G*q.dV
        rk = RHO_W*G*q.dVk
        rh = W[sub] - cg_w
        rk_ = Wk[subk] - cg_w
        tau_world = (fh*np.array([rh[:, 1].sum(), -rh[:, 0].sum(), 0.0])
                     + rk*np.array([rk_[:, 1].sum(), -rk_[:, 0].sum(),
                                    0.0]))
        tau_body = R.T @ tau_world
        CB = ((W[sub].sum(axis=0)*q.dV +
               Wk[subk].sum(axis=0)*q.dVk)/V_sub) - cg_w
    else:
        tau_body = np.zeros(3)
        CB = None
    tiefgang = -min(W[:, 2].min(), Wk[:, 2].min())
    return {'F_A': F_A, 'tau_body': tau_body, 'tiefgang': tiefgang,
            'CB': CB, 'R': R, 'W': np.vstack([W, Wk]), 'k': kh + kk}
