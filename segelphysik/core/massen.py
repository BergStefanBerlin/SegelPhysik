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


def traegheitstensor_flaechig(punkte, dreiecke, flaechenmasse=1.0):
    """Exakte Traegheit eines Flaechenkoerpers (Schale): die Masse sitzt
    gleichmaessig auf der Oberflaeche (Spez P3, flaechenmasse).

    Pro Dreieck wird int(x x^T) dA exakt ueber die affine Abbildung des
    Referenzdreiecks integriert (u,v im Referenzdreieck, |det B| = 2A):
        int(1) = 1/2,  int(u) = 1/6,  int(u u^T) = [[1/12,1/24],[1/24,1/12]]
        M_drei = A*aa + 2A*(a g^T + g a^T) + 2A*B U B^T,  g = B*(1/6,1/6)
    Summe -> Tensor um den Ursprung (J = tr(M)E - M), dann
    Parallel-Achsen-Satz rueckwaerts zum Flaechen-Schwerpunkt.
    Unabhaengig von der Windung (Flaechen sind ungerichtet)."""
    P = np.asarray(punkte, float); T = np.asarray(dreiecke, np.int64)
    if len(T) == 0: raise ValueError("Leeres Mesh")
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    A = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    if A.sum() < 1e-300: raise ValueError("Mesh hat keine Flaeche")
    B = np.stack((b - a, c - a), axis=2)                 # (n, 3, 2): Kanten als Spalten
    g = B @ np.array([1/6., 1/6.])                       # B * u_quer
    U = np.array([[1/12., 1/24.], [1/24., 1/12.]])
    BUB = np.einsum('nik,kl,njl->nij', B, U, B)
    aa = np.einsum('ni,nj->nij', a, a)
    ag = np.einsum('ni,nj->nij', a, g) + np.einsum('ni,nj->nij', g, a)
    A3 = A[:, None, None]
    M = A3 * aa + (2.0 * A3) * ag + (2.0 * A3) * BUB     # int(x x^T) dA je Dreieck
    fm = float(flaechenmasse)
    M = M.sum(axis=0) * fm
    J = np.trace(M) * np.eye(3) - M                      # um den Ursprung
    r, flaeche_ges = schwerpunkt_flaechig(P, T)
    m = fm * flaeche_ges
    J = J - m * ((r @ r) * np.eye(3) - np.outer(r, r))   # Steiner rueckwaerts
    return J
