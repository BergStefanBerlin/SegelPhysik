"""Masseneigenschaften aus Meshes (Spec V4, P1/P3) - rein numpy, exakte
Polyeder-Integration, deterministisch. SI-Einheiten (R6)."""
from collections import OrderedDict
import hashlib
import numpy as np
from threading import Lock


_SELBSTSCHNITT_CACHE = OrderedDict()
_SELBSTSCHNITT_CACHE_LOCK = Lock()
_SELBSTSCHNITT_CACHE_MAX = 128


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


def _kreuzprodukt_3d(a, b):
    return np.array((
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ))


def _koplanare_dreiecke_schneiden(a, b, normale, toleranz):
    entferne_achse = int(np.argmax(np.abs(normale)))
    a2 = np.delete(a, entferne_achse, axis=1)
    b2 = np.delete(b, entferne_achse, axis=1)
    kanten = np.vstack((
        np.roll(a2, -1, axis=0) - a2,
        np.roll(b2, -1, axis=0) - b2,
    ))
    for kante in kanten:
        achse = np.array((-kante[1], kante[0]))
        projektion_a = a2 @ achse
        projektion_b = b2 @ achse
        if (np.max(projektion_a) < np.min(projektion_b) - toleranz
                or np.max(projektion_b)
                < np.min(projektion_a) - toleranz):
            return False
    return True


def _segment_dreieck_schneiden(start, ende, dreieck, toleranz):
    richtung = ende - start
    kanten1 = dreieck[1] - dreieck[0]
    kanten2 = dreieck[2] - dreieck[0]
    p = _kreuzprodukt_3d(richtung, kanten2)
    determinant = float(np.dot(kanten1, p))
    skala = max(
        float(np.linalg.norm(richtung) * np.linalg.norm(kanten1)
              * np.linalg.norm(kanten2)),
        toleranz**3)
    determinant_tol = toleranz * skala
    if abs(determinant) <= determinant_tol:
        return False
    inverse = 1.0 / determinant
    versatz = start - dreieck[0]
    u = float(np.dot(versatz, p) * inverse)
    q = _kreuzprodukt_3d(versatz, kanten1)
    v = float(np.dot(richtung, q) * inverse)
    t = float(np.dot(kanten2, q) * inverse)
    bary_tol = toleranz / max(
        float(np.linalg.norm(kanten1)), float(np.linalg.norm(kanten2)),
        toleranz)
    return (
        -bary_tol <= u <= 1.0 + bary_tol
        and -bary_tol <= v
        and u + v <= 1.0 + bary_tol
        and -bary_tol <= t <= 1.0 + bary_tol
    )


def _koplanare_paare_schneiden(a, b, normale_a, koplanar, toleranz):
    schneidet = np.zeros(len(a), dtype=bool)
    achsen_entfernen = np.argmax(np.abs(normale_a[koplanar]), axis=1)
    for achse in range(3):
        mask = achsen_entfernen == achse
        if not np.any(mask):
            continue
        a2 = np.delete(a[koplanar][mask], achse, axis=2)
        b2 = np.delete(b[koplanar][mask], achse, axis=2)
        kanten = np.concatenate((
            np.roll(a2, -1, axis=1) - a2,
            np.roll(b2, -1, axis=1) - b2,
        ), axis=1)
        testachsen = np.stack((-kanten[:, :, 1], kanten[:, :, 0]), axis=2)
        laengen = np.linalg.norm(testachsen, axis=2)
        projektion_a = np.einsum("nvc,nkc->nvk", a2, testachsen)
        projektion_b = np.einsum("nvc,nkc->nvk", b2, testachsen)
        getrennt = (
            np.max(projektion_a, axis=1)
            < np.min(projektion_b, axis=1) - toleranz * laengen
        ) | (
            np.max(projektion_b, axis=1)
            < np.min(projektion_a, axis=1) - toleranz * laengen
        )
        schneidet[np.flatnonzero(koplanar)[mask]] = ~np.any(
            getrennt, axis=1)
    return schneidet


def _segmentpaare_dreieck_schneiden(start, ende, dreieck, toleranz):
    richtung = ende - start
    kanten1 = dreieck[:, 1] - dreieck[:, 0]
    kanten2 = dreieck[:, 2] - dreieck[:, 0]
    p = np.cross(richtung, kanten2[:, None, :])
    determinant = np.einsum("nc,nec->ne", kanten1, p)
    laenge_richtung = np.linalg.norm(richtung, axis=2)
    laenge1 = np.linalg.norm(kanten1, axis=1)
    laenge2 = np.linalg.norm(kanten2, axis=1)
    skala = np.maximum(
        laenge_richtung * laenge1[:, None] * laenge2[:, None],
        toleranz**3)
    parallel = np.abs(determinant) <= toleranz * skala
    inverse = np.divide(
        1.0, determinant, out=np.zeros_like(determinant), where=~parallel)
    versatz = start - dreieck[:, 0, None, :]
    u = np.einsum("nec,nec->ne", versatz, p) * inverse
    q = np.cross(versatz, kanten1[:, None, :])
    v = np.einsum("nec,nec->ne", richtung, q) * inverse
    t = np.einsum("nc,nec->ne", kanten2, q) * inverse
    bary_toleranz = toleranz / np.maximum(
        np.maximum(laenge1, laenge2), toleranz)
    trifft = (
        ~parallel
        & (u >= -bary_toleranz[:, None])
        & (u <= 1.0 + bary_toleranz[:, None])
        & (v >= -bary_toleranz[:, None])
        & (u + v <= 1.0 + bary_toleranz[:, None])
        & (t >= -bary_toleranz[:, None])
        & (t <= 1.0 + bary_toleranz[:, None])
    )
    return np.any(trifft, axis=1)


def _dreieckspaare_schneiden(a, b, toleranz):
    normale_a = np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0])
    normale_b = np.cross(b[:, 1] - b[:, 0], b[:, 2] - b[:, 0])
    laenge_a = np.linalg.norm(normale_a, axis=1)
    laenge_b = np.linalg.norm(normale_b, axis=1)
    abstaende_b = np.einsum("nvc,nc->nv", b - a[:, 0, None, :], normale_a)
    abstaende_a = np.einsum("nvc,nc->nv", a - b[:, 0, None, :], normale_b)
    getrennt = (
        np.all(abstaende_b > toleranz * laenge_a[:, None], axis=1)
        | np.all(abstaende_b < -toleranz * laenge_a[:, None], axis=1)
        | np.all(abstaende_a > toleranz * laenge_b[:, None], axis=1)
        | np.all(abstaende_a < -toleranz * laenge_b[:, None], axis=1)
    )
    treffer = ~getrennt
    normierte_a = np.abs(abstaende_a) / laenge_b[:, None]
    normierte_b = np.abs(abstaende_b) / laenge_a[:, None]
    koplanar = (
        treffer
        & (np.max(normierte_a, axis=1) <= toleranz)
        & (np.max(normierte_b, axis=1) <= toleranz)
    )
    koplanar_treffer = _koplanare_paare_schneiden(
        a, b, normale_a, koplanar, toleranz)
    treffer[koplanar] = koplanar_treffer[koplanar]
    nicht_koplanar = treffer & ~koplanar
    if np.any(nicht_koplanar):
        a_nicht = a[nicht_koplanar]
        b_nicht = b[nicht_koplanar]
        kanten_a = np.roll(a_nicht, -1, axis=1) - a_nicht
        kanten_b = np.roll(b_nicht, -1, axis=1) - b_nicht
        trifft_a = _segmentpaare_dreieck_schneiden(
            a_nicht, np.roll(a_nicht, -1, axis=1), b_nicht, toleranz)
        trifft_b = _segmentpaare_dreieck_schneiden(
            b_nicht, np.roll(b_nicht, -1, axis=1), a_nicht, toleranz)
        treffer[nicht_koplanar] = trifft_a | trifft_b
    return treffer


def _pruefe_mesh_selbstueberschneidung(P, F):
    fingerprint = hashlib.sha256()
    fingerprint.update(P.shape.__repr__().encode("ascii"))
    fingerprint.update(P.tobytes(order="C"))
    fingerprint.update(F.shape.__repr__().encode("ascii"))
    fingerprint.update(F.tobytes(order="C"))
    schluessel = fingerprint.digest()
    with _SELBSTSCHNITT_CACHE_LOCK:
        if schluessel in _SELBSTSCHNITT_CACHE:
            _SELBSTSCHNITT_CACHE.move_to_end(schluessel)
            return

    dreiecke_punkte = P[F]
    minima = dreiecke_punkte.min(axis=1)
    maxima = dreiecke_punkte.max(axis=1)
    ausdehnung = float(np.max(np.ptp(P, axis=0)))
    toleranz = max(
        ausdehnung * 1e-12,
        np.finfo(np.float64).eps
        * max(1.0, float(np.max(np.abs(P)))) * 64.0)
    reihenfolge = np.argsort(minima[:, 0], kind="stable")
    aktiv = []
    paare = []
    for index in reihenfolge:
        start_x = minima[index, 0]
        aktiv = [
            kandidat for kandidat in aktiv
            if maxima[kandidat, 0] >= start_x - toleranz
        ]
        if aktiv:
            kandidaten = np.asarray(aktiv, dtype=np.intp)
            kandidaten = kandidaten[
                (maxima[kandidaten, 1] >= minima[index, 1] - toleranz)
                & (maxima[index, 1] >= minima[kandidaten, 1] - toleranz)
                & (maxima[kandidaten, 2] >= minima[index, 2] - toleranz)
                & (maxima[index, 2] >= minima[kandidaten, 2] - toleranz)
            ]
            if len(kandidaten):
                flaechen = F[kandidaten]
                geteilt = np.any(
                    flaechen == F[index][0], axis=1
                ) | np.any(flaechen == F[index][1], axis=1) | np.any(
                    flaechen == F[index][2], axis=1)
                kandidaten = kandidaten[~geteilt]
        else:
            kandidaten = ()
        paare.extend((int(kandidat), int(index)) for kandidat in kandidaten)
        aktiv.append(int(index))
    if paare:
        paare = np.asarray(paare, dtype=np.intp)
        schneidet = _dreieckspaare_schneiden(
            dreiecke_punkte[paare[:, 0]],
            dreiecke_punkte[paare[:, 1]],
            toleranz)
        if np.any(schneidet):
            kandidat, index = paare[np.flatnonzero(schneidet)[0]]
            raise ValueError(
                "Mesh ist selbstüberschneidend: Dreiecke %d und %d"
                % (int(kandidat), int(index)))
    with _SELBSTSCHNITT_CACHE_LOCK:
        _SELBSTSCHNITT_CACHE[schluessel] = None
        _SELBSTSCHNITT_CACHE.move_to_end(schluessel)
        while len(_SELBSTSCHNITT_CACHE) > _SELBSTSCHNITT_CACHE_MAX:
            _SELBSTSCHNITT_CACHE.popitem(last=False)


def pruefe_mesh_selbstueberschneidung(punkte, dreiecke):
    """Lehnt Schnitte nicht benachbarter Dreiecke mit Sweep-and-prune ab."""
    P, F, _ = validiere_mesh_eingaben(punkte, dreiecke)
    _pruefe_mesh_selbstueberschneidung(P, F)


def validiere_mesh(punkte, dreiecke, geschlossen_erforderlich=False,
                   strenge_topologie=False, normalisiere_orientierung=False,
                   pruefe_selbstueberschneidung=False):
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
    if strenge_topologie and np.any(nichtmannigfaltig):
        raise ValueError(
            "Mesh ist nicht-mannigfaltig: eine Kante wird von mehr als 2 "
            "Flächen geteilt")
    if strenge_topologie and np.any(widerspruechliche_kanten):
        raise ValueError(
            "Mesh hat widersprüchliche Orientierung an gemeinsamen Kanten")
    if pruefe_selbstueberschneidung:
        _pruefe_mesh_selbstueberschneidung(P, F)
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
    if normalisiere_orientierung and geschlossen and volumen < 0.0:
        F = F[:, [0, 2, 1]]
        volumen = -volumen
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
    Die Integration erfolgt direkt relativ zum Flaechen-Schwerpunkt, damit
    kleine Schalen bei grossen absoluten Koordinaten stabil bleiben.
    Unabhaengig von der Windung (Flaechen sind ungerichtet)."""
    P = np.asarray(punkte, float); T = np.asarray(dreiecke, np.int64)
    if len(T) == 0: raise ValueError("Leeres Mesh")
    r, flaeche_ges = schwerpunkt_flaechig(P, T)
    P = P - r
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
    return np.trace(M) * np.eye(3) - M
