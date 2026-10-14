"""Masseneigenschaften aus Meshes (Spec V4, P1/P3) - rein numpy, exakte
Polyeder-Integration, deterministisch. SI-Einheiten (R6)."""
import numpy as np


def validiere_mesh_eingaben(punkte, dreiecke):
    """Normalisiert Mesharrays und prüft Werte, Indizes und Degeneration."""
    try:
        P = np.asarray(punkte, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("Meshpunkte müssen numerische 3D-Koordinaten sein") from fehler
    if P.ndim != 2 or P.shape[1:] != (3,) or len(P) == 0:
        raise ValueError("Mesh muss mindestens einen Punkt mit 3 Koordinaten enthalten")
    if not np.isfinite(P).all():
        raise ValueError("Meshpunkte enthalten nicht-endliche Koordinaten")

    try:
        F_num = np.asarray(dreiecke, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("Meshflächen müssen numerische Dreiecksindizes enthalten") from fehler
    if F_num.ndim != 2 or F_num.shape[1:] != (3,) or len(F_num) == 0:
        raise ValueError("Mesh muss mindestens ein Dreieck mit 3 Indizes enthalten")
    if not np.isfinite(F_num).all() or not np.equal(F_num, np.floor(F_num)).all():
        raise ValueError("Meshflächen enthalten ungültige oder nicht-ganzzahlige Indizes")
    if np.any(F_num < 0) or np.any(F_num >= len(P)):
        raise ValueError("Meshflächen verweisen auf Punkte außerhalb des Meshes")
    if np.any(F_num >= float(2**63)):
        raise ValueError("Meshflächenindex überschreitet den unterstützten Integerbereich")
    F = F_num.astype(np.int64)

    with np.errstate(over="ignore", invalid="ignore"):
        kantenlaenge = float(np.max(np.ptp(P, axis=0)))
    if not np.isfinite(kantenlaenge):
        raise ValueError("Mesh-Ausdehnung ist nicht endlich")
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    with np.errstate(over="ignore", invalid="ignore"):
        doppelflaeche = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    if not np.isfinite(doppelflaeche).all():
        raise ValueError("Mesh-Dreiecksfläche ist nicht endlich")
    flaechen_tol = (16.0 * np.finfo(np.float64).eps
                    * kantenlaenge * kantenlaenge)
    if kantenlaenge == 0.0 or np.any(doppelflaeche <= flaechen_tol):
        raise ValueError("Mesh enthält entartete Dreiecke mit verschwindender Fläche")
    return P, F, doppelflaeche


def validiere_mesh(punkte, dreiecke, geschlossen_erforderlich=False):
    """Prüft Geometrie und Topologie vor einer Masse-/Volumenberechnung.

    Offene Oberflächen sind für Schalen zulässig. Ein geschlossenes Volumennetz
    muss der Aufrufer ausdrücklich verlangen.
    """
    P, F, doppelflaeche = validiere_mesh_eingaben(punkte, dreiecke)
    kanten_gerichtet = np.concatenate(
        (F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]), axis=0)
    kanten_ungerichtet = np.sort(kanten_gerichtet, axis=1)
    _kanten, gruppen, anzahl = np.unique(
        kanten_ungerichtet, axis=0, return_inverse=True, return_counts=True)
    nichtmannigfaltig = anzahl > 2
    richtung = np.where(
        kanten_gerichtet[:, 0] < kanten_gerichtet[:, 1], 1, -1)
    orientierungssumme = np.bincount(
        gruppen, weights=richtung, minlength=len(anzahl))
    widerspruechliche_kanten = (anzahl == 2) & (orientierungssumme != 0)
    geschlossen = bool(
        np.all(anzahl == 2)
        and not np.any(nichtmannigfaltig)
        and not np.any(widerspruechliche_kanten))
    if geschlossen_erforderlich and not geschlossen:
        if np.any(nichtmannigfaltig):
            grund = "nicht-mannigfaltig: eine Kante wird von mehr als 2 Flächen geteilt"
        elif np.any(widerspruechliche_kanten):
            grund = "widersprüchliche Orientierung an gemeinsamen Flächenkanten"
        else:
            grund = "es besitzt offene Kanten"
        raise ValueError("Volumenmesh muss geschlossen und konsistent orientiert sein; %s"
                         % grund)
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    with np.errstate(over="ignore", invalid="ignore"):
        volumen = float(np.einsum("ij,ij->", a, np.cross(b, c)) / 6.0)
        flaeche = float(0.5 * doppelflaeche.sum())
    if not np.isfinite(volumen) or not np.isfinite(flaeche):
        raise ValueError("Mesh-Volumen oder -Fläche ist nicht endlich")
    return P, F, volumen, flaeche, geschlossen, int(np.count_nonzero(anzahl != 2))


def validiere_traegheitstensor(tensor):
    """Prüft physikalische Trägheitstensorbedingungen am Schwerpunkt."""
    I = np.asarray(tensor, dtype=np.float64)
    if I.shape != (3, 3) or not np.isfinite(I).all():
        raise ValueError("Trägheitstensor muss eine endliche 3x3-Matrix sein")
    skala = max(float(np.max(np.abs(I))), np.finfo(np.float64).tiny)
    tol = 128.0 * np.finfo(np.float64).eps * skala
    if float(np.max(np.abs(I - I.T))) > tol:
        raise ValueError("Trägheitstensor ist nicht symmetrisch")
    I = 0.5 * (I + I.T)
    hauptmomente = np.linalg.eigvalsh(I)
    if hauptmomente[0] < -tol:
        raise ValueError("Trägheitstensor ist nicht positiv semidefinit")
    if hauptmomente[0] + hauptmomente[1] + tol < hauptmomente[2]:
        raise ValueError("Hauptträgheitsmomente verletzen die Dreiecksungleichung")
    return I


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
