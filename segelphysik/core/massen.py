"""Masseneigenschaften aus Meshes (Spec V4, P1/P3) - rein numpy, exakte
Polyeder-Integration, deterministisch. SI-Einheiten (R6)."""
import numpy as np

def mesh_volumen(punkte, dreiecke):
    P = np.asarray(punkte, float); T = np.asarray(dreiecke, np.int64)
    if len(T) == 0: return 0.0
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    return float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6.0)

def mesh_flaeche(punkte, dreiecke):
    P = np.asarray(punkte, float); T = np.asarray(dreiecke, np.int64)
    if len(T) == 0: return 0.0
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())

def schwerpunkt_homogen(punkte, dreiecke):
    P = np.asarray(punkte, float); T = np.asarray(dreiecke, np.int64)
    if len(T) == 0: raise ValueError("Leeres Mesh")
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    sv = np.einsum("ij,ij->i", a, np.cross(b, c))
    g = sv.sum()
    if abs(g) < 1e-300:
        raise ValueError("Volumen null (Flaechen-Mesh?): schwerpunkt_flaechig nutzen")
    r = ((a + b + c) / 4.0 * sv[:, None]).sum(axis=0) / g
    return r, float(g / 6.0)

def schwerpunkt_flaechig(punkte, dreiecke):
    P = np.asarray(punkte, float); T = np.asarray(dreiecke, np.int64)
    if len(T) == 0: raise ValueError("Leeres Mesh")
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    A = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    if A.sum() < 1e-300: raise ValueError("Mesh hat keine Flaeche")
    r = ((a + b + c) / 3.0 * A[:, None]).sum(axis=0) / A.sum()
    return r, float(A.sum())

def traegheitstensor_homogen(punkte, dreiecke, dichte=1.0):
    """Exakte Polyeder-Integration; Tetraeder-Momente: Quadrate V/10,
    Kreuzterme V/20; Kompakt-Tensor J = tr(M)*E - M; Parallel-Achsen-Satz."""
    P = np.asarray(punkte, float); T = np.asarray(dreiecke, np.int64)
    if len(T) == 0: raise ValueError("Leeres Mesh")
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    sv = np.einsum("ij,ij->i", a, np.cross(b, c))
    if abs(sv.sum()) < 1e-300: raise ValueError("Volumen null: Tensor undefiniert")
    def aussen(u, v):
        return np.einsum("ni,nj->nij", u, v) + np.einsum("ni,nj->nij", v, u)
    S = (np.einsum("ni,nj->nij", a, a) + np.einsum("ni,nj->nij", b, b)
         + np.einsum("ni,nj->nij", c, c))
    C = aussen(a, b) + aussen(a, c) + aussen(b, c)
    M = (sv[:, None, None] / 6.0) * (S / 10.0 + C / 20.0)
    M = M.sum(axis=0) * float(dichte)
    J = np.trace(M) * np.eye(3) - M
    s, _v = schwerpunkt_homogen(P, T)
    m = float(dichte) * abs(float(sv.sum()) / 6.0)
    d = s
    J = J - m * ((d @ d) * np.eye(3) - np.outer(d, d))
    return J
