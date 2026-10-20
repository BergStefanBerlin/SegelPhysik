"""SegelPhysik V3 - Koerper-Formen (rein geometrische Fabrik) (SPEC_V3.md Abschnitt 3).

KEINE Physik: keine Dichte, keine Masse, keine Kraefte. Geschlossene
Dreiecks-Meshes (vertices, faces) im KOERPERFRAME; Ursprung im geometrischen
Schwerpunkt (Kegel/Pyramide: H/4 ueber der Basis).

V4-Schnittstelle: spaetere Physik (Volumen-/Schwerpunktintegration,
Ebenen-Clip fuer V_sub) konsumiert diese Meshes als Consumer, ohne sie zu
veraendern. Altbestand core/bodies.py dient nur als Referenz, nicht als
Importquelle.
"""
from __future__ import annotations
import operator

import numpy as np

from .rechenpfad import rechenpfad

__all__ = ["build_cone", "build_box", "build_pyramid", "build_sphere",
           "build_cylinder", "build_plate", "build_hexprism",
           "build_polyhedron", "FORMEN", "baue_aus_form"]


def _close(vertices, faces):
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)
    assert f.min() >= 0 and f.max() < len(v)
    return v, f


def _native_form(typ, parameter, nseg=0, liegend=False):
    from .native_backend import native_laden
    return native_laden().form_mesh(
        typ, np.asarray(parameter, dtype=np.float64), operator.index(nseg), liegend)


def build_cone(H=2.0, R=1.0, nseg=64):
    """Kegel, Achse = Koerper-z, Spitze oben; Basis z=-H/4, Spitze z=+3H/4.

    Hinweis: Die Basis ist ein regulaeres n-Eck (n = nseg). Das Mesh-Volumen
    weicht daher vom Kreiskegel um den Faktor (n/(2*pi))*sin(2*pi/n) ab
    (bei n=64: -0.16 %); mit steigendem nseg konvergiert es quadratisch.
    """
    if H <= 0 or R <= 0 or nseg < 3:
        raise ValueError("H>0, R>0, nseg>=3 erforderlich")
    if rechenpfad() == "cpp":
        return _native_form(0, (H, R, 0.), nseg)
    zb, zt = -H / 4.0, 3.0 * H / 4.0
    ang = 2.0 * np.pi * np.arange(nseg) / nseg
    ring = np.stack([R*np.cos(ang), R*np.sin(ang), np.full(nseg, zb)], axis=1)
    v = np.vstack([ring, [[0.0, 0.0, zt]], [[0.0, 0.0, zb]]])
    i = np.arange(nseg); j = (i + 1) % nseg
    side = np.stack([i, j, np.full(nseg, nseg)], axis=1)      # nach aussen orientiert
    base = np.stack([np.full(nseg, nseg+1), j, i], axis=1)    # nach unten orientiert
    return _close(v, np.vstack([side, base]))


def build_box(dx=2.0, dy=2.0, dz=2.0):
    """Quader dx*dy*dz, zentriert im Ursprung (= Schwerpunkt)."""
    if min(dx, dy, dz) <= 0:
        raise ValueError("dx, dy, dz > 0 erforderlich")
    if rechenpfad() == "cpp":
        return _native_form(1, (dx, dy, dz))
    hx, hy, hz = dx/2.0, dy/2.0, dz/2.0
    v = np.array([[-hx,-hy,-hz],[hx,-hy,-hz],[hx,hy,-hz],[-hx,hy,-hz],
                  [-hx,-hy,hz],[hx,-hy,hz],[hx,hy,hz],[-hx,hy,hz]])
    quads = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(3,0,4,7)]
    f = []
    for a,b,c,d in quads:
        f += [[a,b,c],[a,c,d]]
    return _close(v, f)


def build_pyramid(a=2.0, H=2.0):
    """Quadratische Pyramide Basis a*a, Hoehe H; Basis z=-H/4, Spitze z=+3H/4."""
    if a <= 0 or H <= 0:
        raise ValueError("a>0, H>0 erforderlich")
    if rechenpfad() == "cpp":
        return _native_form(2, (a, H, 0.))
    h = a/2.0; zb, zt = -H/4.0, 3.0*H/4.0
    v = np.array([[-h,-h,zb],[h,-h,zb],[h,h,zb],[-h,h,zb],[0.0,0.0,zt]])
    f = [[0,1,4],[1,2,4],[2,3,4],[3,0,4],[0,3,2],[0,2,1]]
    return _close(v, f)


# --- deutsche Alias-Namen (sprechende API) ---
bau_kegel = build_cone
bau_quader = build_box
bau_pyramide = build_pyramid


# --- weitere Formen -------------------------------------------------------

def _volumenschwerpunkt(v, f):
    """Schwerpunkt eines geschlossenen, aussen orientierten Dreiecksnetzes."""
    if rechenpfad() == "cpp":
        from .native_backend import mesh_vorbereiten, native_laden
        return native_laden().form_schwerpunkt(mesh_vorbereiten(v, f))
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    gesamt = vol.sum()
    if abs(gesamt) < 1e-18:
        raise ValueError("Koerper ohne Volumen")
    return ((a + b + c) / 4.0 * vol[:, None]).sum(axis=0) / gesamt


def _zentriert(v, f):
    v = np.asarray(v, dtype=np.float64)
    if rechenpfad() == "cpp":
        from .native_backend import mesh_vorbereiten, native_laden
        return native_laden().form_zentrieren(mesh_vorbereiten(v, f))
    return _close(v - _volumenschwerpunkt(v, np.asarray(f, np.int64)), f)


def _liegend(v):
    """Achse z -> x (Bug-Richtung), eigentliche Drehung (det = +1)."""
    v = np.asarray(v, dtype=np.float64)
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        return native_laden().form_liegend(v)
    return np.stack([v[:, 2], v[:, 1], -v[:, 0]], axis=1)


def _ring(r, z, n, versatz=0.0):
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        return native_laden().form_ring(float(r), float(z), operator.index(n), float(versatz))
    ang = 2.0 * np.pi * (np.arange(n) + versatz) / n
    return np.stack([r*np.cos(ang), r*np.sin(ang), np.full(n, float(z))],
                    axis=1)


def build_sphere(R=1.0, nseg=48):
    """Kugel (UV-Netz mit Polen), Mittelpunkt im Ursprung."""
    if R <= 0 or nseg < 6:
        raise ValueError("R>0, nseg>=6 erforderlich")
    if rechenpfad() == "cpp":
        return _native_form(3, (R, 0., 0.), nseg)
    ringe = nseg // 2 - 1
    teile = [[[0.0, 0.0, R]]]
    for i in range(1, ringe + 1):
        theta = np.pi * i / (ringe + 1)
        teile.append(_ring(R*np.sin(theta), R*np.cos(theta), nseg))
    teile.append([[0.0, 0.0, -R]])
    v = np.vstack(teile)
    sued = len(v) - 1
    f = []
    j = np.arange(nseg); k = (j + 1) % nseg
    f += [[0, 1 + a, 1 + b] for a, b in zip(j, k)]
    for r in range(ringe - 1):
        o, u = 1 + r*nseg, 1 + (r + 1)*nseg
        for a, b in zip(j, k):
            f += [[o + a, u + a, u + b], [o + a, u + b, o + b]]
    u = 1 + (ringe - 1)*nseg
    f += [[u + b, u + a, sued] for a, b in zip(j, k)]
    return _close(v, f)


def build_cylinder(R=0.5, H=2.0, nseg=64, lage="stehend"):
    """Zylinder; stehend: Achse z, liegend: Achse x. Mitte im Ursprung."""
    if R <= 0 or H <= 0 or nseg < 3:
        raise ValueError("R>0, H>0, nseg>=3 erforderlich")
    if rechenpfad() == "cpp":
        return _native_form(4, (R, H, 0.), nseg, lage == "liegend")
    v = np.vstack([_ring(R, -H/2.0, nseg), _ring(R, H/2.0, nseg),
                   [[0.0, 0.0, -H/2.0]], [[0.0, 0.0, H/2.0]]])
    j = np.arange(nseg); k = (j + 1) % nseg
    f = []
    for a, b in zip(j, k):
        f += [[a, b, nseg + b], [a, nseg + b, nseg + a],
              [2*nseg, b, a], [2*nseg + 1, nseg + a, nseg + b]]
    if lage == "liegend":
        v = _liegend(v)
    return _close(v, f)


def build_plate(dx=2.0, dy=1.0, dicke=0.02):
    """Duenne Platte dx*dy*dicke (Dicke in z), zentriert."""
    return build_box(dx, dy, dicke)


def build_hexprism(umkreisradius=0.004, H=0.17, spitzenlaenge=0.0,
                   lage="stehend"):
    """Sechskantstab der Gesamtlaenge H mit optionaler konischer Spitze.

    Spitze am +Ende; stehend: Achse z, liegend: Achse x. Der Ursprung liegt
    im Volumenschwerpunkt."""
    if umkreisradius <= 0 or H <= 0 or not 0.0 <= spitzenlaenge < H:
        raise ValueError("umkreisradius>0, H>0, 0<=spitzenlaenge<H erforderlich")
    if rechenpfad() == "cpp":
        return _native_form(5, (umkreisradius, H, spitzenlaenge), 6, lage == "liegend")
    schaft_oben = H - spitzenlaenge
    unten = _ring(umkreisradius, 0.0, 6)
    oben = _ring(umkreisradius, schaft_oben, 6)
    j = np.arange(6); k = (j + 1) % 6
    # 12 = Mitte unten, 13 = Mitte oben bzw. Spitzenpunkt (z = H)
    v = np.vstack([unten, oben, [[0.0, 0.0, 0.0]], [[0.0, 0.0, H]]])
    f = []
    for a, b in zip(j, k):
        f += [[a, b, 6 + b], [a, 6 + b, 6 + a], [12, b, a]]
        f += [[13, 6 + a, 6 + b]]
    v, f = _zentriert(v, f)
    if lage == "liegend":
        v = _liegend(v)
    return v, f


def build_polyhedron(eckpunkte, flaechen=None):
    """Geschlossener Koerper aus Eckpunkten.

    Ohne 'flaechen' (Indexlisten, Polygone werden faecherfoermig zerlegt,
    aussen im Gegenuhrzeigersinn) ist es die KONVEXE Huelle der Punkte.
    Ursprung im Volumenschwerpunkt."""
    p = np.asarray(eckpunkte, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 4:
        raise ValueError("eckpunkte_m: mindestens 4 Punkte [x, y, z]")
    if not np.isfinite(p).all():
        raise ValueError("eckpunkte_m: nur endliche Zahlen")
    if flaechen is not None:
        f = []
        polygone = []
        for poly in flaechen:
            poly = [int(i) for i in poly]
            if len(poly) < 3 or min(poly) < 0 or max(poly) >= len(p):
                raise ValueError("flaechen: ungueltiger Index")
            if rechenpfad() == "cpp":
                polygone.append(poly)
            else:
                f += [[poly[0], poly[i], poly[i + 1]]
                      for i in range(1, len(poly) - 1)]
        if rechenpfad() == "cpp":
            from .native_backend import native_laden
            f = native_laden().form_faecher(polygone)
        return _zentriert(p, f)
    return _zentriert(*_konvexe_huelle(p))


def _konvexe_huelle(p, tol=1e-9):
    if rechenpfad() == "cpp":
        from .native_backend import native_laden
        native = native_laden()
        punkte = np.asarray(p, dtype=np.float64)
        flaechen = native.form_huellflaechen(punkte, float(tol))
        ordnungen = [index[np.argsort(winkel)] for index, winkel in flaechen]
        return p, native.form_huelldreiecke(punkte, ordnungen)
    n = len(p)
    if n > 64:
        raise ValueError("eckpunkte_m: hoechstens 64 Punkte ohne 'flaechen'")
    skala = max(float(np.ptp(p, axis=0).max()), 1e-12)
    ebenen = {}
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                nv = np.cross(p[j] - p[i], p[k] - p[i])
                ln = np.linalg.norm(nv)
                if ln < tol * skala * skala:
                    continue
                nv /= ln
                s = (p - p[i]) @ nv
                if np.all(s <= tol * skala):
                    pass
                elif np.all(s >= -tol * skala):
                    nv, s = -nv, -s
                else:
                    continue
                auf = frozenset(np.flatnonzero(np.abs(s) <= tol * skala))
                ebenen.setdefault(auf, nv)
    if not ebenen:
        raise ValueError("eckpunkte_m: Punkte liegen in einer Ebene")
    mitte = p.mean(axis=0)
    f = []
    for auf, nv in ebenen.items():
        idx = sorted(auf)
        z = p[idx].mean(axis=0)
        u = p[idx[0]] - z
        u -= nv * (u @ nv)
        u /= np.linalg.norm(u)
        w = np.cross(nv, u)
        winkel = np.arctan2((p[idx] - z) @ w, (p[idx] - z) @ u)
        ordnung = [idx[i] for i in np.argsort(winkel)]
        for i in range(1, len(ordnung) - 1):
            f.append([ordnung[0], ordnung[i], ordnung[i + 1]])
    f = np.asarray(f, dtype=np.int64)
    # nach aussen orientieren (konvex: Normale zeigt von der Mitte weg)
    a, b, c = p[f[:, 0]], p[f[:, 1]], p[f[:, 2]]
    innen = np.einsum("ij,ij->i", np.cross(b - a, c - a), a - mitte) < 0
    f[innen] = f[innen][:, [0, 2, 1]]
    return p, f


# --- Formtabelle: einzige Quelle fuer Loader, Fabrik und Baumanzeige ------
# zahlen/optionale_zahlen: positive Zahlen (JSON-Schluessel mit Einheit),
# texte: {Schluessel: erlaubte Werte}, listen: Pflicht-Listen,
# optionale_listen: optionale Listen, bau(f): -> (vertices, faces),
# titel(f): Anzeigetext fuer den Komponentenbaum.
def _g(f, k):
    return float(f[k])


FORMEN = {
    "cone": dict(
        zahlen=("H_m", "R_m"),
        bau=lambda f: build_cone(_g(f, "H_m"), _g(f, "R_m")),
        titel=lambda f: "Kegel H=%g R=%g m" % (f["H_m"], f["R_m"])),
    "box": dict(
        zahlen=("dx_m", "dy_m", "dz_m"),
        bau=lambda f: build_box(_g(f, "dx_m"), _g(f, "dy_m"), _g(f, "dz_m")),
        titel=lambda f: "Quader %gx%gx%g m" % (f["dx_m"], f["dy_m"], f["dz_m"])),
    "pyramid": dict(
        zahlen=("a_m", "H_m"),
        bau=lambda f: build_pyramid(_g(f, "a_m"), _g(f, "H_m")),
        titel=lambda f: "Pyramide a=%g H=%g m" % (f["a_m"], f["H_m"])),
    "sphere": dict(
        zahlen=("R_m",),
        bau=lambda f: build_sphere(_g(f, "R_m")),
        titel=lambda f: "Kugel R=%g m" % f["R_m"]),
    "cylinder": dict(
        zahlen=("R_m", "H_m"),
        texte={"lage": ("stehend", "liegend")},
        bau=lambda f: build_cylinder(_g(f, "R_m"), _g(f, "H_m"),
                                     lage=f.get("lage", "stehend")),
        titel=lambda f: "Zylinder R=%g H=%g m (%s)" % (
            f["R_m"], f["H_m"], f.get("lage", "stehend"))),
    "plate": dict(
        zahlen=("dx_m", "dy_m", "dicke_m"),
        bau=lambda f: build_plate(_g(f, "dx_m"), _g(f, "dy_m"),
                                  _g(f, "dicke_m")),
        titel=lambda f: "Platte %gx%gx%g m" % (
            f["dx_m"], f["dy_m"], f["dicke_m"])),
    "hexprism": dict(
        zahlen=("umkreisradius_m", "H_m"),
        optionale_zahlen=("spitzenlaenge_m",),
        texte={"lage": ("stehend", "liegend")},
        bau=lambda f: build_hexprism(
            _g(f, "umkreisradius_m"), _g(f, "H_m"),
            float(f.get("spitzenlaenge_m", 0.0)),
            lage=f.get("lage", "stehend")),
        titel=lambda f: "Sechskantstab r=%g H=%g m" % (
            f["umkreisradius_m"], f["H_m"])),
    "polyhedron": dict(
        listen=("eckpunkte_m",),
        optionale_listen=("flaechen",),
        bau=lambda f: build_polyhedron(f["eckpunkte_m"], f.get("flaechen")),
        titel=lambda f: "Polyeder (%d Ecken)" % len(f["eckpunkte_m"])),
}


def baue_aus_form(f):
    """Baut (vertices, faces) aus einem 'form'-Dict der koerper.json."""
    typ = f.get("typ")
    if typ not in FORMEN:
        raise ValueError("unbekannte Form %r (erlaubt: %s)"
                         % (typ, ", ".join(sorted(FORMEN))))
    return FORMEN[typ]["bau"](f)
