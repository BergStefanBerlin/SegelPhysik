"""Auftriebsphysik (P5c Phase A, Umsetzungsplan V5 rev 9 §1/§3).

Eine Kraftfunktion, zwei Treiber (Spec §0): Diese Funktion ist rein
(kein Zustand, keine Grafik, keine Zeit-Annahmen) und wird vom statischen
Solver (Phase B) und der Echtzeit-Integration (Phase D) gleichermassen
genutzt. SI-Einheiten (R6).

Berechnungskette (§1):
  1. V_tauch: schneide_am_wasser je Blatt-Mesh an z=0 (Welt-Frame);
     V_tauch ueber die WIRKSAMEN (vereinigten) Volumina gem. D7 -
     Standardpfad = Voxelgitter direkt auf den Schnitt-Meshes (D10);
     exakter Pfad = Tetraeder-Integration je Blatt + Summe, nur fuer
     disjunkte Testgeometrien als Referenz (D10).
  2. F_A = rho_W * g * V_tauch, Richtung +z
  3. K = Schwerpunkt DES VERDRAENGTEN VOLUMENS (nicht des Koerpers, F1);
     K mit derselben Methode wie V_tauch (F13): exakt = volumengewichtetes
     Tetraeder-Mittel, Voxel = voxelgewichteter Schwerpunkt.
  4. M = (K - r_S) x F_A

Konventionen (D11): z positiv nach oben, Wasserlinie der Welt bei z=0;
phi positiv = Kraengung nach Steuerbord; Momente positiv in Richtung
wachsendem phi (restaurierendes Moment bei phi>0 -> negatives Vorzeichen).
Meshes werden vor dem Schnitt mit der Pose in die Welt transformiert.

Voxel-Verfahren (D7/D10): globales Raster (x,z) ueber allen getauchten
Teilmeshes; je Saeule even-odd entlang y ueber die Dreiecke, deren
xz-Projektion den Saeulenpunkt enthaelt (geschlossene Teilmeshes dank
Deckel). Ein Voxel zaehlt, wenn sein Mittelpunkt in MINDESTENS EINEM
getauchten Blatt-Volumen liegt (Vereinigungsmenge). Bei achsenparallelen
Testkoerpern mit 0.5*h-Raster-Offset ist das Ergebnis exakt.
"""
from __future__ import annotations

import numpy as np

from .. import wasser_schnitt as ws

G_NORM = 9.80665  # D4: Norm-Schwere; im Betrieb aus physik.json (D8)


class AuftriebFehler(ValueError):
    """Verstoss gegen die Regeln der Auftriebsrechnung (Plan §3)."""


class Vektor:
    """Schlanker 3D-Vektor mit benannten Komponenten."""

    __slots__ = ("x", "y", "z")

    def __init__(self, arr):
        self.x, self.y, self.z = (float(v) for v in arr)

    def as_array(self):
        return np.array([self.x, self.y, self.z])

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __repr__(self):
        return "Vektor(x=%.6f, y=%.6f, z=%.6f)" % (self.x, self.y, self.z)


class Auftriebsergebnis:
    """Datenrecord der Kraftfunktion (Plan §3): (V_tauch, K, F_A, M)."""

    __slots__ = ("V_tauch", "K", "F_A", "M")

    def __init__(self, V_tauch, K, F_A, M):
        self.V_tauch = float(V_tauch)
        self.K = K if isinstance(K, Vektor) else Vektor(K)
        self.F_A = F_A if isinstance(F_A, Vektor) else Vektor(F_A)
        self.M = M if isinstance(M, Vektor) else Vektor(M)

    def __repr__(self):
        return ("Auftriebsergebnis(V_tauch=%.6f m^3, K=%r, F_A=%r, M=%r)"
                % (self.V_tauch, self.K, self.F_A, self.M))


def lage_pruefen(lage):
    """Validiert die Lage (z, phi, theta); theta ist Wache (D6)."""
    if len(lage) != 3:
        raise AuftriebFehler(
            "Lage muss (Tauchung z, Kraengung phi, Trim theta) sein, "
            "erhalten: %r" % (lage,))
    z, phi, theta = (float(x) for x in lage)
    if theta != 0.0:
        raise AuftriebFehler(
            "Trim theta ist Platzhalter mit Wache (D6): theta=%g unzulaessig "
            "(Rechnung erst in Schritt 3)" % theta)
    return z, phi, theta


def pose_matrix(z, phi, theta=0.0):
    """4x4 Pose-Matrix: Rotation um die Laengsachse (Welt-x, Rollwinkel phi)
    + Translation z entlang Welt-z (D11: z = z-Position von r_S).

    R_x(phi): positive phi dreht +y nach oben und -y (Steuerbord) nach
    unten -> Kraengung nach Steuerbord (D11)."""
    c, s = np.cos(phi), np.sin(phi)
    T = np.eye(4)
    T[:3, :3] = np.array([
        [1.0, 0.0, 0.0],
        [0.0, c, -s],
        [0.0, s, c],
    ])
    T[2, 3] = z
    return T


def _in_welt(punkte, T):
    P = np.asarray(punkte, dtype=float).reshape(-1, 3)
    return P @ T[:3, :3].T + T[:3, 3]


def _tetraeder_beitraege(P, T):
    """Signierte Tetraeder-Volumina (Ecke = Ursprung) + Dreiecks-Schwerpunkte."""
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    return vol6 / 6.0, (a + b + c) / 4.0


def _exakt_blatt(P, F):
    """Exakter Pfad (D10, Referenz): (V, K) eines geschlossenen Meshes
    via Divergenzsatz. K ist von der Windungsrichtung unabhaengig; V wird
    als Betrag gefuehrt (die Windungsrichtung prueft N0 separat)."""
    P = np.asarray(P, dtype=float).reshape(-1, 3)
    F = np.asarray(F, dtype=np.int64).reshape(-1, 3)
    if len(F) == 0:
        return 0.0, np.zeros(3)
    vol, schw = _tetraeder_beitraege(P, F)
    V_sig = float(vol.sum())
    if abs(V_sig) < 1e-15:
        return 0.0, np.zeros(3)
    K = (vol[:, None] * schw).sum(axis=0) / vol.sum()
    return abs(V_sig), K


def _unterwasser_teile(punkte, gesichter):
    """Unterwasser-Teilmesh eines Blatts, geschlossen via Deckel (damit
    even-odd-y und Divergenzsatz ein Volumen sehen)."""
    u_p, u_t, _o_p, _o_t, _k = ws.schneide_am_wasser(punkte, gesichter,
                                                     mit_deckel=True)
    return u_p, u_t


def _y_intervalle_saeule(u_p, u_t, x0, z0):
    """Even-odd entlang y fuer die Vertikale (x0, z0) durch ein geschlossenes
    Teilmesh: sammelt die y-Hoehen aller Dreiecke, deren xz-Projektion den
    Punkt enthaelt, sortiert und paarweise zu Intervallen verbunden."""
    schnitte = []
    for tri in u_t:
        p0, p1, p2 = u_p[tri[0]], u_p[tri[1]], u_p[tri[2]]
        d = ((p1[0] - p0[0]) * (p2[2] - p0[2])
             - (p2[0] - p0[0]) * (p1[2] - p0[2]))
        if abs(d) < 1e-15:
            continue  # xz-entartet (z.B. horizontale Flaeche)
        w1 = ((x0 - p0[0]) * (p2[2] - p0[2])
              - (p2[0] - p0[0]) * (z0 - p0[2])) / d
        w2 = ((p1[0] - p0[0]) * (z0 - p0[2])
              - (x0 - p0[0]) * (p1[2] - p0[2])) / d
        if w1 < -1e-12 or w2 < -1e-12 or w1 + w2 > 1.0 + 1e-12:
            continue
        schnitte.append(p0[1] + w1 * (p1[1] - p0[1]) + w2 * (p2[1] - p0[1]))
    if len(schnitte) < 2:
        return []
    schnitte.sort()
    # Eine Vertikale durch eine GEMEINSAME Kante zweier Dreiecks (z. B. die
    # Diagonale eines Faechers) liefert den Schnittwert doppelt. Ohne
    # Deduplication heben sich die Paare im even-odd gegenseitig auf und die
    # ganze Saeule geht verloren. Merge innerhalb Toleranz:
    gedichtet = [schnitte[0]]
    for s in schnitte[1:]:
        if s - gedichtet[-1] > 1e-9:
            gedichtet.append(s)
    schnitte = gedichtet
    schnitte = _paare_bereit(schnitte)
    if not schnitte:
        return []
    return [(schnitte[i], schnitte[i + 1])
            for i in range(0, len(schnitte), 2)]


def _paare_bereit(schnitte):
    """Tangenten-Restfall: ungerade Schnittezahl bedeutet Beruehrung ohne
    Durchdringung. Entfernt solange aeussere Paare, bis die Zahl gerade ist
    (oder nichts uebrig bleibt). Fix: die bisherige Einmal-Behandlung liess
    bei ungerader Zahl >= 5 wieder eine ungerade Liste zurueck (IndexError
    in der Paarbildung)."""
    while len(schnitte) % 2 == 1:
        if len(schnitte) < 4:
            return []
        schnitte = schnitte[1:-1]
    return schnitte


def _voxel_koerper(blatt_welt, aufloesung):
    """Voxel-Vereinigung (D7/D10) ueber alle Blatt-Meshes.

    Rueckgabe: (V_tauch, K) - V = Anzahl-Treffer * h^3, K = Mittel der
    Voxelzentren (voxelgewichtet, F13)."""
    h = float(aufloesung)
    teile = []
    for P, F in blatt_welt:
        u_p, u_t = _unterwasser_teile(P, F)
        if len(u_t) >= 4:
            teile.append((u_p, u_t))
    if not teile:
        return 0.0, np.zeros(3)

    lo = np.min([u_p.min(axis=0) for u_p, _ in teile], axis=0) - h
    hi = np.max([u_p.max(axis=0) for u_p, _ in teile], axis=0) + h
    def _zentren(a_lo, a_hi):
        k0 = int(np.ceil(a_lo / h - 0.5))
        k1 = int(np.floor(a_hi / h - 0.5))
        return (np.arange(k0, k1 + 1) + 0.5) * h
    xs = _zentren(lo[0], hi[0])
    zs = _zentren(lo[2], hi[2])
    ys = _zentren(lo[1], hi[1])

    # Vektorisierte Saeulen-Berechnung (Sichtprobe-Fix: Boot mit tausenden
    # Dreiecken dauerte in der reinen Python-Schleife Minuten). Logik und
    # Toleranzen identisch zu _y_intervalle_saeule, aber alle Dreiecke
    # gleichzeitig je Saeule.
    treffer_spalten = []
    for x0 in xs:
        for z0 in zs:
            maske = np.zeros(len(ys), dtype=bool)
            for u_p, u_t in teile:
                for y_a, y_b in _y_intervalle_saeule_v(u_p, u_t, x0, z0):
                    maske |= (ys > y_a) & (ys < y_b)
            if maske.any():
                treffer_spalten.append((x0, z0, np.where(maske)[0]))
    if not treffer_spalten:
        return 0.0, np.zeros(3)
    n_treffer = sum(len(iy) for _, _, iy in treffer_spalten)
    summe = np.zeros(3)
    for x0, z0, iy in treffer_spalten:
        summe[0] += len(iy) * x0
        summe[1] += ys[iy].sum()
        summe[2] += len(iy) * z0
    return n_treffer * h ** 3, summe / n_treffer


def _y_intervalle_saeule_v(u_p, u_t, x0, z0):
    """Vektorisierte Variante von _y_intervalle_saeule (gleiche Logik,
    gleiche Toleranzen): alle Dreiecke gleichzeitig per numpy."""
    p0 = u_p[u_t[:, 0]]
    p1 = u_p[u_t[:, 1]]
    p2 = u_p[u_t[:, 2]]
    d = ((p1[:, 0] - p0[:, 0]) * (p2[:, 2] - p0[:, 2])
         - (p2[:, 0] - p0[:, 0]) * (p1[:, 2] - p0[:, 2]))
    ok = np.abs(d) >= 1e-15
    if not ok.any():
        return []
    n1 = ((x0 - p0[:, 0]) * (p2[:, 2] - p0[:, 2])
          - (p2[:, 0] - p0[:, 0]) * (z0 - p0[:, 2]))
    n2 = ((p1[:, 0] - p0[:, 0]) * (z0 - p0[:, 2])
          - (x0 - p0[:, 0]) * (p1[:, 2] - p0[:, 2]))
    w1 = np.divide(n1, d, out=np.zeros_like(d), where=ok)
    w2 = np.divide(n2, d, out=np.zeros_like(d), where=ok)
    drin = ok & (w1 >= -1e-12) & (w2 >= -1e-12) & (w1 + w2 <= 1.0 + 1e-12)
    if not drin.any():
        return []
    schnitte = (p0[drin, 1] + w1[drin] * (p1[drin, 1] - p0[drin, 1])
                + w2[drin] * (p2[drin, 1] - p0[drin, 1]))
    schnitte.sort()
    gedichtet = [schnitte[0]]
    for s in schnitte[1:]:
        if s - gedichtet[-1] > 1e-9:
            gedichtet.append(s)
    schnitte = _paare_bereit(gedichtet)
    if not schnitte:
        return []
    return [(schnitte[i], schnitte[i + 1])
            for i in range(0, len(schnitte), 2)]


def kraftfunktion_berechne(koerper, lage, v=None, omega=None, rho_w=1000.0,
                           g=G_NORM, aufloesung=0.05, pfad="voxel",
                           voxelmodell=None):
    """Kernrechnung der Kraftfunktion (Plan §3). Der Koerper wird als
    Argument uebergeben; die GEBUNDENE Signatur (F19) liefert
    baue_kraftfunktion().

    koerper : Objekt mit .blatt_meshes [(punkte, gesichter), ...] im
              Koerper-Frame (r_S im Ursprung, P1) und .r_S
    pfad    : "voxel" (Standard), "voxel_koerperfest", "exakt" (Blattsumme)
              oder "exakt_union" (Boolesche Union als Referenz)
    """
    koerper = als_bindung(koerper)
    z, phi, theta = lage_pruefen(lage)
    T = pose_matrix(z, phi, theta)

    if pfad == "voxel_koerperfest":
        if voxelmodell is None:
            from .voxelmodell import KoerperfestesVoxelmodell
            voxelmodell = KoerperfestesVoxelmodell(
                koerper.blatt_meshes, aufloesung)
        V, K = voxelmodell.auswerten(z, phi)
    elif pfad in ("exakt", "voxel", "exakt_union"):
        blatt_welt = [(_in_welt(P, T), np.asarray(F, dtype=np.int64))
                      for P, F in koerper.blatt_meshes]
    else:
        raise AuftriebFehler(
            "unbekannter Pfad %r ('voxel', 'voxel_koerperfest', 'exakt' "
            "oder 'exakt_union' erwartet)" % pfad)

    if pfad == "exakt":
        V = 0.0
        K_sum = np.zeros(3)
        for P, F in blatt_welt:
            u_p, u_t = _unterwasser_teile(P, F)
            if len(u_t) == 0:
                continue
            vb, kb = _exakt_blatt(u_p, u_t)
            V += vb
            K_sum += vb * kb
        K = K_sum / V if V > 1e-15 else np.zeros(3)
    elif pfad == "voxel":
        V, K = _voxel_koerper(blatt_welt, aufloesung)
    elif pfad == "exakt_union":
        from .volumen_union import volumen_schwerpunkt_union
        V, K = volumen_schwerpunkt_union(blatt_welt, ebene_z=0.0)

    F_A = np.array([0.0, 0.0, rho_w * g * V])
    r_S_welt = _in_welt(np.asarray(koerper.r_S, dtype=float).reshape(1, 3),
                        T)[0]
    M = np.cross(K - r_S_welt, F_A)
    return Auftriebsergebnis(V, K, F_A, M)


def als_bindung(koerper):
    """F19: Nimmt ein Objekt mit .blatt_meshes/.r_S (Test-Stub) oder einen
    echten Koerper-Verband (.teile-Rekursion, P1) und liefert ein Objekt
    mit blatt_meshes (Blaetter im Verbands-Schwerpunktframe) und r_S=0."""
    if hasattr(koerper, "blatt_meshes") and hasattr(koerper, "r_S"):
        return koerper
    if not hasattr(koerper, "teile"):
        raise AuftriebFehler("koerper muss Stub oder Koerper-Verband sein")
    blaetter = []
    def sammle(k, R, t):
        if getattr(k, "teile", None):
            for kind, (Rk, tk) in k.teile:
                sammle(kind, R @ Rk, t + R @ tk)
        else:
            if not getattr(k, "verdrangend", True):
                return
            blaetter.append((np.asarray(k.punkte, float) @ R.T + t,
                             np.asarray(k.dreiecke, np.int64)))
    sammle(koerper, np.eye(3), np.zeros(3))
    class _Bindung: pass
    b = _Bindung(); b.blatt_meshes = blaetter; b.r_S = np.zeros(3)
    return b


def baue_kraftfunktion(koerper, rho_w=1000.0, g=G_NORM, aufloesung=0.05,
                       pfad="voxel"):
    """Bindet den Koerper + Parameter (F19): Rueckgabe ist eine Funktion
    (lage, v, omega) -> Auftriebsergebnis. v/omega stehen in der
    Schnittstelle (F9) und werden in Phase A ignoriert (Daempfung §6)."""

    voxelmodell = None
    if pfad == "voxel_koerperfest":
        from .voxelmodell import KoerperfestesVoxelmodell
        voxelmodell = KoerperfestesVoxelmodell(
            als_bindung(koerper).blatt_meshes, aufloesung)

    def funktion(lage, v=None, omega=None):
        return kraftfunktion_berechne(koerper, lage, v=v, omega=omega,
                                      rho_w=rho_w, g=g,
                                      aufloesung=aufloesung, pfad=pfad,
                                      voxelmodell=voxelmodell)

    return funktion


def wasserdichtheit(punkte, gesichter):
    """N0-Kriterium: Ein geschlossenes Mesh hat JEDE Kante genau 2x.
    Rueckgabe: (ist_geschlossen, anzahl_schlechter_kanten, signiertes_V)."""
    from .massen import validiere_mesh
    try:
        _P, _F, volumen, _flaeche, geschlossen, schlecht = validiere_mesh(
            punkte, gesichter)
    except ValueError:
        return False, 1, 0.0
    return geschlossen, schlecht, volumen
