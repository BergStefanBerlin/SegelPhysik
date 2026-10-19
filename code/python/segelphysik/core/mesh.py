"""Kanonische, unveränderliche SI-Meshes und sichere Geometrieimporte."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Mapping

import numpy as np

from .massen import validiere_mesh, validiere_mesh_eingaben


def _unveraenderliches_array(array, dtype):
    zusammenhaengend = np.array(array, dtype=dtype, order="C", copy=True)
    return np.frombuffer(zusammenhaengend.tobytes(), dtype=dtype).reshape(
        zusammenhaengend.shape)


@dataclass(frozen=True, slots=True, eq=False)
class Mesh:
    punkte_si: np.ndarray
    dreiecke: np.ndarray
    frame: str
    metadaten: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if (not isinstance(self.frame, str) or not self.frame.strip()
                or self.frame != self.frame.strip()):
            raise ValueError("Mesh-Frame muss ein nichtleerer Name sein")
        punkte, dreiecke, _ = validiere_mesh_eingaben(
            self.punkte_si, self.dreiecke)
        if not isinstance(self.metadaten, Mapping):
            raise ValueError("Mesh-Metadaten müssen eine Zuordnung sein")
        metadaten = dict(self.metadaten)
        for schluessel, wert in metadaten.items():
            if not isinstance(schluessel, str) or not schluessel:
                raise ValueError("Mesh-Metadatenschlüssel müssen Text sein")
            if (wert is not None and type(wert) not in (str, int, float, bool)):
                raise ValueError(
                    "Mesh-Metadaten müssen unveränderliche Skalare sein")
            if isinstance(wert, float) and not math.isfinite(wert):
                raise ValueError("Mesh-Metadaten dürfen nicht unendlich sein")
        object.__setattr__(
            self, "punkte_si", _unveraenderliches_array(punkte, np.float64))
        object.__setattr__(
            self, "dreiecke", _unveraenderliches_array(dreiecke, np.int64))
        object.__setattr__(self, "metadaten", MappingProxyType(metadaten))

    @classmethod
    def aus_legacy_tupel(cls, form, frame, metadaten=None):
        try:
            punkte, dreiecke = form
        except (TypeError, ValueError) as fehler:
            raise ValueError(
                "Alt-Mesh muss aus Punkten und Dreiecken bestehen") from fehler
        return cls(
            punkte, dreiecke, frame,
            {} if metadaten is None else metadaten)

    def als_tupel(self):
        return self.punkte_si, self.dreiecke


def validiere_mesh_fuer_masse(mesh, *, wanddicke_m=None, fehlerkontext=""):
    """Prüft Topologie passend zur Massendefinition und normiert Außenflächen."""
    if not isinstance(mesh, Mesh):
        raise ValueError("Massengeometrie muss ein kanonisches Mesh sein")
    if wanddicke_m is not None and (
            isinstance(wanddicke_m, bool)
            or not isinstance(wanddicke_m, (int, float))
            or not math.isfinite(wanddicke_m)
            or wanddicke_m <= 0.0):
        raise ValueError("Wanddicke muss eine positive endliche Zahl sein")
    geschlossen_erforderlich = wanddicke_m is None
    kontext = (fehlerkontext + ": ") if fehlerkontext else ""
    try:
        punkte, dreiecke, volumen, _flaeche, geschlossen, _offene_kanten = (
            validiere_mesh(
                mesh.punkte_si,
                mesh.dreiecke,
                geschlossen_erforderlich=geschlossen_erforderlich,
                strenge_topologie=True,
                normalisiere_orientierung=True,
                pruefe_selbstueberschneidung=True))
    except ValueError as fehler:
        raise ValueError(kontext + str(fehler)) from fehler
    if geschlossen_erforderlich and geschlossen and abs(volumen) <= 1e-300:
        raise ValueError(kontext + "Volumenmesh hat kein positives Volumen")
    if (np.array_equal(punkte, mesh.punkte_si)
            and np.array_equal(dreiecke, mesh.dreiecke)):
        return mesh
    return Mesh(punkte, dreiecke, mesh.frame, mesh.metadaten)


def pfad_im_paket_aufloesen(paketwurzel, relativer_pfad):
    if not isinstance(relativer_pfad, str) or not relativer_pfad:
        raise ValueError("Geometriepfad muss nichtleerer relativer Text sein")
    if "\\" in relativer_pfad or ":" in relativer_pfad:
        raise ValueError(
            "Geometriepfad muss portabel mit '/' relativ angegeben werden")
    posix_pfad = PurePosixPath(relativer_pfad)
    windows_pfad = PureWindowsPath(relativer_pfad)
    if (posix_pfad.is_absolute() or windows_pfad.is_absolute()
            or windows_pfad.drive
            or any(teil in ("", ".", "..") for teil in relativer_pfad.split("/"))):
        raise ValueError("Geometriepfad darf nicht absolut sein oder Traversal enthalten")
    paketwurzel = Path(paketwurzel)
    if not paketwurzel.is_absolute():
        raise ValueError("Paketwurzel muss explizit absolut angegeben werden")
    wurzel = paketwurzel.resolve(strict=True)
    if not wurzel.is_dir():
        raise ValueError("Paketwurzel ist kein Verzeichnis: %s" % wurzel)
    try:
        ziel = wurzel.joinpath(*posix_pfad.parts).resolve(strict=True)
    except (OSError, RuntimeError) as fehler:
        raise ValueError(
            "Geometriedatei fehlt oder kann nicht aufgelöst werden: %s"
            % relativer_pfad) from fehler
    if not ziel.is_relative_to(wurzel):
        raise ValueError("Geometriepfad verlässt die Paketwurzel: %s"
                         % relativer_pfad)
    if not ziel.is_file():
        raise ValueError("Geometriepfad ist keine Datei: %s" % relativer_pfad)
    return ziel


def _polygon_selbstschneidet(punkte, tol_laenge):
    anzahl = len(punkte)
    tol_flaeche = tol_laenge * max(
        float(np.max(np.ptp(punkte, axis=0))), tol_laenge)

    def orientierung(a, b, c):
        ab = b - a
        ac = c - a
        return ab[0] * ac[1] - ab[1] * ac[0]

    def auf_strecke(a, b, p):
        return (np.all(p >= np.minimum(a, b) - tol_laenge)
                and np.all(p <= np.maximum(a, b) + tol_laenge))

    def schneiden(a, b, c, d):
        werte = (
            orientierung(a, b, c), orientierung(a, b, d),
            orientierung(c, d, a), orientierung(c, d, b))
        if (werte[0] * werte[1] < -tol_flaeche * tol_flaeche
                and werte[2] * werte[3] < -tol_flaeche * tol_flaeche):
            return True
        return (
            abs(werte[0]) <= tol_flaeche and auf_strecke(a, b, c)
            or abs(werte[1]) <= tol_flaeche and auf_strecke(a, b, d)
            or abs(werte[2]) <= tol_flaeche and auf_strecke(c, d, a)
            or abs(werte[3]) <= tol_flaeche and auf_strecke(c, d, b))

    for i in range(anzahl):
        i2 = (i + 1) % anzahl
        for j in range(i + 1, anzahl):
            j2 = (j + 1) % anzahl
            if i == j or i2 == j or j2 == i:
                continue
            if schneiden(punkte[i], punkte[i2], punkte[j], punkte[j2]):
                return True
    return False


def _trianguliere_polygon(vertices, index, pfad, zeilennummer):
    if len(index) > 3 and index[0] == index[-1]:
        index = index[:-1]
    if len(index) < 3 or len(set(index)) != len(index):
        raise ValueError(
            "%s, Zeile %d: Polygon hat weniger als 3 eindeutige Eckpunkte"
            % (pfad, zeilennummer))
    if len(index) == 3:
        return [tuple(index)]
    punkte = np.asarray([vertices[i] for i in index], dtype=np.float64)
    verschoben = punkte - punkte[0]
    spannweite = float(np.max(np.ptp(punkte, axis=0)))
    tol_laenge = max(
        spannweite * 1e-10,
        np.finfo(np.float64).eps
        * max(1.0, float(np.max(np.abs(punkte)))) * 32.0)
    normal = np.cross(verschoben, np.roll(verschoben, -1, axis=0)).sum(axis=0)
    normale_laenge = float(np.linalg.norm(normal))
    if not np.isfinite(normale_laenge) or normale_laenge <= tol_laenge**2:
        raise ValueError(
            "%s, Zeile %d: Polygon ist entartet" % (pfad, zeilennummer))
    normal /= normale_laenge
    abstaende = np.abs(verschoben @ normal)
    if np.any(abstaende > max(tol_laenge * 100.0, spannweite * 1e-8)):
        raise ValueError(
            "%s, Zeile %d: nicht-planare OBJ-Polygone werden abgelehnt"
            % (pfad, zeilennummer))
    projektion = np.delete(verschoben, int(np.argmax(np.abs(normal))), axis=1)
    if _polygon_selbstschneidet(projektion, tol_laenge):
        raise ValueError(
            "%s, Zeile %d: selbstschneidendes OBJ-Polygon"
            % (pfad, zeilennummer))
    x, y = projektion[:, 0], projektion[:, 1]
    area2 = float(np.dot(x, np.roll(y, -1))
                  - np.dot(y, np.roll(x, -1)))
    tol_flaeche = tol_laenge * max(spannweite, tol_laenge)
    if abs(area2) <= tol_flaeche:
        raise ValueError(
            "%s, Zeile %d: Polygonfläche ist null" % (pfad, zeilennummer))
    richtung = 1.0 if area2 > 0.0 else -1.0
    verbleibend = list(range(len(index)))
    dreiecke = []

    while len(verbleibend) > 3:
        ohr_gefunden = False
        for position, mitte in enumerate(verbleibend):
            vorher = verbleibend[position - 1]
            nachher = verbleibend[(position + 1) % len(verbleibend)]
            a, b, c = projektion[[vorher, mitte, nachher]]
            kreuz = ((b[0] - a[0]) * (c[1] - a[1])
                     - (b[1] - a[1]) * (c[0] - a[0]))
            if abs(kreuz) <= tol_flaeche:
                zwischen = (
                    np.all(projektion[mitte]
                           >= np.minimum(a, c) - tol_laenge)
                    and np.all(projektion[mitte]
                               <= np.maximum(a, c) + tol_laenge))
                if zwischen:
                    del verbleibend[position]
                    ohr_gefunden = True
                    break
                continue
            if richtung * kreuz <= tol_flaeche:
                continue
            punkt_im_ohr = False
            for kandidat in verbleibend:
                if kandidat in (vorher, mitte, nachher):
                    continue
                p = projektion[kandidat]
                kanten = (
                    (b[0] - a[0]) * (p[1] - a[1])
                    - (b[1] - a[1]) * (p[0] - a[0]),
                    (c[0] - b[0]) * (p[1] - b[1])
                    - (c[1] - b[1]) * (p[0] - b[0]),
                    (a[0] - c[0]) * (p[1] - c[1])
                    - (a[1] - c[1]) * (p[0] - c[0]))
                if all(richtung * k >= -tol_flaeche for k in kanten):
                    punkt_im_ohr = True
                    break
            if punkt_im_ohr:
                continue
            dreiecke.append((index[vorher], index[mitte], index[nachher]))
            del verbleibend[position]
            ohr_gefunden = True
            break
        if not ohr_gefunden:
            raise ValueError(
                "%s, Zeile %d: OBJ-Polygon kann nicht sicher trianguliert werden"
                % (pfad, zeilennummer))
    dreiecke.append(tuple(index[i] for i in verbleibend))
    return dreiecke


def _obj_index(text, anzahl, typ, pfad, zeilennummer):
    try:
        original = int(text)
    except (TypeError, ValueError) as fehler:
        raise ValueError(
            "%s, Zeile %d: ungültiger %sindex %r"
            % (pfad, zeilennummer, typ, text)) from fehler
    if original == 0:
        raise ValueError(
            "%s, Zeile %d: OBJ-Indizes beginnen bei 1, Null ist unzulässig"
            % (pfad, zeilennummer))
    index = original - 1 if original > 0 else anzahl + original
    if index < 0 or index >= anzahl:
        raise ValueError(
            "%s, Zeile %d: %sindex %d außerhalb des bisher gelesenen Bereichs"
            % (pfad, zeilennummer, typ, original))
    return index


def _obj_vertex_index(text, anzahl, pfad, zeilennummer):
    try:
        original = int(text)
    except (TypeError, ValueError) as fehler:
        raise ValueError(
            "%s, Zeile %d: ungültiger Vertexindex %r"
            % (pfad, zeilennummer, text)) from fehler
    if original == 0:
        raise ValueError(
            "%s, Zeile %d: OBJ-Indizes beginnen bei 1, Null ist unzulässig"
            % (pfad, zeilennummer))
    index = original - 1 if original > 0 else anzahl + original
    if index < 0 or index >= anzahl:
        raise ValueError(
            "%s, Zeile %d: Vertexindex %d außerhalb des bisher gelesenen "
            "Bereichs" % (pfad, zeilennummer, original))
    return index


def _einfaches_obj_laden(zeilen, pfad):
    vertices, dreiecke = [], []
    texturanzahl = normalenanzahl = 0
    ignorierte_zeilen = {"o", "g", "s", "usemtl", "mtllib"}

    for zeile in zeilen:
        werte = zeile.split()
        if not werte or werte[0].startswith("#"):
            continue
        typ = werte[0]
        if typ == "v":
            if len(werte) != 4:
                return None
            try:
                punkt = tuple(float(x) for x in werte[1:])
            except (ValueError, OverflowError):
                return None
            if not all(math.isfinite(x) for x in punkt):
                return None
            vertices.append(punkt)
        elif typ == "vt":
            if len(werte) not in (2, 3, 4):
                return None
            try:
                koordinaten = [float(x) for x in werte[1:]]
            except (ValueError, OverflowError):
                return None
            if not all(math.isfinite(x) for x in koordinaten):
                return None
            texturanzahl += 1
        elif typ == "vn":
            if len(werte) != 4:
                return None
            try:
                koordinaten = [float(x) for x in werte[1:]]
            except (ValueError, OverflowError):
                return None
            if not all(math.isfinite(x) for x in koordinaten):
                return None
            normalenanzahl += 1
        elif typ == "f":
            if len(werte) != 4:
                return None
            index = []
            for token in werte[1:]:
                vertex_text, trenner, rest = token.partition("/")
                if not vertex_text:
                    return None
                texture_text = normal_text = ""
                if trenner:
                    texture_text, trenner, normal_text = rest.partition("/")
                    if ((not trenner and not texture_text)
                            or (trenner and (
                                not normal_text or "/" in normal_text))):
                        return None
                try:
                    vertex = int(vertex_text)
                    textur = int(texture_text) if texture_text else None
                    normale = int(normal_text) if normal_text else None
                except (ValueError, OverflowError):
                    return None
                if vertex == 0:
                    return None
                vertex = vertex - 1 if vertex > 0 else len(vertices) + vertex
                if vertex < 0 or vertex >= len(vertices):
                    return None
                if textur is not None and (
                        textur == 0
                        or (textur > 0 and textur > texturanzahl)
                        or (textur < 0 and -textur > texturanzahl)):
                    return None
                if normale is not None and (
                        normale == 0
                        or (normale > 0 and normale > normalenanzahl)
                        or (normale < 0 and -normale > normalenanzahl)):
                    return None
                index.append(vertex)
            if len(set(index)) != 3:
                return None
            dreiecke.append(tuple(index))
        elif typ not in ignorierte_zeilen:
            return None

    return (
        np.asarray(vertices, dtype=np.float64),
        np.asarray(dreiecke, dtype=np.int64),
    )


def _robustes_obj_laden(zeilen, pfad):
    vertices, texturen, normalen, dreiecke = [], 0, 0, []
    ignorierte_zeilen = {"o", "g", "s", "usemtl", "mtllib"}
    for zeilennummer, zeile in enumerate(zeilen, 1):
        eintraege = zeile.partition("#")[0].split()
        if not eintraege:
            continue
        typ, werte = eintraege[0], eintraege[1:]
        if typ == "v":
            if len(werte) not in (3, 4):
                raise ValueError(
                    "%s, Zeile %d: OBJ-Vertex benötigt x y z [w]"
                    % (pfad, zeilennummer))
            try:
                punkt = tuple(float(x) for x in werte)
            except (ValueError, OverflowError) as fehler:
                raise ValueError(
                    "%s, Zeile %d: ungültige Vertexkoordinate"
                    % (pfad, zeilennummer)) from fehler
            if not all(math.isfinite(x) for x in punkt):
                raise ValueError(
                    "%s, Zeile %d: nicht-endliche Vertexkoordinate"
                    % (pfad, zeilennummer))
            if len(punkt) == 4:
                if punkt[3] == 0.0:
                    raise ValueError(
                        "%s, Zeile %d: homogene Vertexkoordinate w darf "
                        "nicht null sein" % (pfad, zeilennummer))
                punkt = tuple(x / punkt[3] for x in punkt[:3])
            vertices.append(punkt)
        elif typ == "vt":
            if len(werte) not in (1, 2, 3):
                raise ValueError(
                    "%s, Zeile %d: ungültige OBJ-Texturkoordinate"
                    % (pfad, zeilennummer))
            try:
                koordinaten = [float(x) for x in werte]
            except (ValueError, OverflowError) as fehler:
                raise ValueError(
                    "%s, Zeile %d: ungültige OBJ-Texturkoordinate"
                    % (pfad, zeilennummer)) from fehler
            if not np.isfinite(koordinaten).all():
                raise ValueError(
                    "%s, Zeile %d: nicht-endliche OBJ-Texturkoordinate"
                    % (pfad, zeilennummer))
            texturen += 1
        elif typ == "vn":
            if len(werte) != 3:
                raise ValueError(
                    "%s, Zeile %d: OBJ-Normale benötigt drei Werte"
                    % (pfad, zeilennummer))
            try:
                koordinaten = [float(x) for x in werte]
            except (ValueError, OverflowError) as fehler:
                raise ValueError(
                    "%s, Zeile %d: ungültige OBJ-Normale"
                    % (pfad, zeilennummer)) from fehler
            if not np.isfinite(koordinaten).all():
                raise ValueError(
                    "%s, Zeile %d: nicht-endliche OBJ-Normale"
                    % (pfad, zeilennummer))
            normalen += 1
        elif typ == "f":
            if len(werte) < 3:
                raise ValueError(
                    "%s, Zeile %d: OBJ-Fläche benötigt mindestens drei "
                    "Eckpunkte" % (pfad, zeilennummer))
            index = []
            for token in werte:
                if "/" not in token:
                    index.append(_obj_vertex_index(
                        token, len(vertices), pfad, zeilennummer))
                    continue
                komponenten = token.split("/")
                if len(komponenten) > 3 or not komponenten[0]:
                    raise ValueError(
                        "%s, Zeile %d: ungültiger OBJ-Flächenindex %r"
                        % (pfad, zeilennummer, token))
                index.append(_obj_vertex_index(
                    komponenten[0], len(vertices), pfad, zeilennummer))
                if len(komponenten) >= 2 and komponenten[1]:
                    _obj_index(komponenten[1], texturen, "Textur",
                               pfad, zeilennummer)
                elif len(komponenten) == 2:
                    raise ValueError(
                        "%s, Zeile %d: leerer Texturindex in %r"
                        % (pfad, zeilennummer, token))
                if len(komponenten) == 3 and komponenten[2]:
                    _obj_index(komponenten[2], normalen, "Normalen",
                               pfad, zeilennummer)
                elif len(komponenten) == 3:
                    raise ValueError(
                        "%s, Zeile %d: leerer Normalenindex in %r"
                        % (pfad, zeilennummer, token))
            if len(index) == 3:
                if len(set(index)) != 3:
                    raise ValueError(
                        "%s, Zeile %d: Dreieck hat doppelte Eckpunkte"
                        % (pfad, zeilennummer))
                dreiecke.append(tuple(index))
            else:
                dreiecke.extend(_trianguliere_polygon(
                    vertices, index, pfad, zeilennummer))
        elif typ not in ignorierte_zeilen:
            raise ValueError(
                "%s, Zeile %d: nicht unterstützte OBJ-Anweisung %r"
                % (pfad, zeilennummer, typ))

    return (
        np.asarray(vertices, dtype=np.float64),
        np.asarray(dreiecke, dtype=np.int64),
    )


def _lade_obj_roh(pfad):
    pfad = Path(pfad)
    try:
        with pfad.open(encoding="utf-8-sig") as quelle:
            einfach = _einfaches_obj_laden(quelle, pfad)
        if einfach is not None:
            return einfach
        with pfad.open(encoding="utf-8-sig") as quelle:
            return _robustes_obj_laden(quelle, pfad)
    except UnicodeDecodeError as fehler:
        raise ValueError("OBJ-Datei ist nicht UTF-8-kodiert: %s" % pfad) from fehler


def lade_obj_arrays(pfad):
    """Liest OBJ-Daten als validierte, veränderliche Arrays."""
    pfad = Path(pfad)
    punkte, flaechen = _lade_obj_roh(pfad)
    try:
        punkte, flaechen, _ = validiere_mesh_eingaben(punkte, flaechen)
    except (ValueError, TypeError, OverflowError) as fehler:
        raise ValueError(
            "Ungültiges OBJ-Mesh in %s: %s" % (pfad, fehler)) from fehler
    return punkte, flaechen


def lade_obj(pfad):
    """Liest OBJ-Vertices als unveränderliches Mesh im OBJ-Quellframe."""
    pfad = Path(pfad)
    punkte, flaechen = _lade_obj_roh(pfad)
    try:
        return Mesh(
            punkte, flaechen, frame="obj",
            metadaten={"quelle": "obj", "datei": str(pfad)})
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError(
            "Ungültiges OBJ-Mesh in %s: %s" % (pfad, fehler)) from fehler


def _obj_achsenmatrix_pruefen(matrix):
    try:
        matrix = np.asarray(matrix, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("OBJ-Achsenmatrix muss numerisch sein") from fehler
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all():
        raise ValueError("OBJ-Achsenmatrix muss eine endliche 3x3-Matrix sein")
    if (not np.allclose(matrix.T @ matrix, np.eye(3), rtol=0.0, atol=1e-10)
            or not np.isclose(np.linalg.det(matrix), 1.0,
                              rtol=0.0, atol=1e-10)):
        raise ValueError(
            "OBJ-Achsenmatrix muss rechtshändig und orthogonal sein")
    return matrix


@lru_cache(maxsize=128)
def _obj_mesh_cached(
        pfad, mtime_ns, ctime_ns, dateigroesse, skala, achsenmatrix, frame,
        datei):
    punkte, dreiecke = _lade_obj_roh(pfad)
    punkte = (punkte * skala) @ np.asarray(achsenmatrix).T
    return Mesh(
        punkte, dreiecke, frame,
        metadaten={
            "quelle": "obj",
            "datei": datei,
            "obj_zu_m": skala,
        })


def mesh_aus_quelle(geometrie, *, paketwurzel, obj_zu_m,
                    obj_achsenmatrix_zu_blatt, frame="blatt",
                    fehlerkontext=""):
    """Löst `form` oder `obj` in ein validiertes Mesh im Ziel-Frame auf."""
    kontext = (fehlerkontext + ": ") if fehlerkontext else ""
    if not isinstance(geometrie, Mapping):
        raise ValueError(kontext + "Geometriequelle muss ein Objekt sein")
    quelle = geometrie.get("quelle")
    if quelle == "obj":
        if set(geometrie) != {"quelle", "datei"}:
            raise ValueError(
                kontext + "OBJ-Quelle benötigt nur 'quelle' und 'datei'")
        if isinstance(obj_zu_m, bool) or not isinstance(
                obj_zu_m, (int, float, np.integer, np.floating)):
            raise ValueError(kontext + "OBJ-Skalierung muss eine Zahl sein")
        try:
            skala = float(obj_zu_m)
        except (TypeError, ValueError, OverflowError) as fehler:
            raise ValueError(kontext + "OBJ-Skalierung ist ungültig") from fehler
        if not math.isfinite(skala) or skala <= 0.0:
            raise ValueError(kontext + "OBJ-Skalierung muss positiv sein")
        matrix = _obj_achsenmatrix_pruefen(obj_achsenmatrix_zu_blatt)
        try:
            pfad = pfad_im_paket_aufloesen(paketwurzel, geometrie["datei"])
            dateistatus = pfad.stat()
            matrix_key = tuple(
                tuple(float(wert) for wert in zeile) for zeile in matrix)
            return _obj_mesh_cached(
                str(pfad), dateistatus.st_mtime_ns,
                dateistatus.st_ctime_ns, dateistatus.st_size,
                skala, matrix_key, frame, geometrie["datei"])
        except (OSError, RuntimeError, TypeError, ValueError,
                OverflowError) as fehler:
            raise ValueError(
                "%s%s: %s" % (kontext, geometrie["datei"], fehler)) from fehler
    if quelle == "form":
        if set(geometrie) != {"quelle", "parameter"}:
            raise ValueError(
                kontext + "Formquelle benötigt nur 'quelle' und 'parameter'")
        from .koerper_formen import baue_aus_form

        try:
            punkte, dreiecke = baue_aus_form(geometrie["parameter"])
            return Mesh(
                punkte, dreiecke, frame,
                metadaten={
                    "quelle": "form",
                    "typ": str(geometrie["parameter"].get("typ", "")),
                })
        except (AttributeError, TypeError, ValueError, OverflowError) as fehler:
            raise ValueError(kontext + "Formquelle ungültig: %s" % fehler) from fehler
    raise ValueError(kontext + "Unbekannte Geometriequelle: %r" % quelle)
