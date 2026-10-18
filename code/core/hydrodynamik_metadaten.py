"""Explizite, reproduzierbare Geometriemetadaten fuer Modellpakete."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from collections.abc import Mapping

import numpy as np

from .massen import (
    schwerpunkt_flaechig,
    schwerpunkt_homogen,
    traegheitstensor_flaechig,
    validiere_mesh,
)
from .modell_lader import _blaetter, lade_modellmanifest, lade_modellpaket
from .mesh import pfad_im_paket_aufloesen

SCHEMA_VERSION = "1.0"
ALGORITHMUS_VERSION = "1.0"
SIDECAR_ORDNER = "hydrodynamik"
SIDECAR_DATEI = "geometrie_metadaten.json"


class GeometriemetadatenFehler(ValueError):
    """Fehler beim Erzeugen, Pruefen oder Schreiben von Geometriemetadaten."""


def _sha256_bytes(daten: bytes) -> str:
    return hashlib.sha256(daten).hexdigest()


def _datei_lesen(pfad: Path, kontext: str) -> bytes:
    try:
        return pfad.read_bytes()
    except OSError as fehler:
        raise GeometriemetadatenFehler(
            "%s kann nicht gelesen werden: %s" % (kontext, fehler)) from fehler


def _rund(wert: float) -> float:
    wert = round(float(wert), 12)
    return 0.0 if wert == 0.0 else wert


def _liste_rund(werte) -> list[float]:
    return [_rund(wert) for wert in np.asarray(werte).reshape(-1)]


def _mesh_hash(mesh) -> str:
    punkte = np.array(
        mesh.punkte_si, dtype="<f8", order="C", copy=True)
    punkte[punkte == 0.0] = 0.0
    dreiecke = np.asarray(mesh.dreiecke, dtype="<i8", order="C")
    digest = hashlib.sha256(b"SegelPhysik-SI-Mesh-v1\0")
    digest.update(np.asarray(punkte.shape, dtype="<i8").tobytes())
    digest.update(punkte.tobytes(order="C"))
    digest.update(np.asarray(dreiecke.shape, dtype="<i8").tobytes())
    digest.update(dreiecke.tobytes(order="C"))
    return digest.hexdigest()


def _json_wert(wert):
    if isinstance(wert, Mapping):
        return {schluessel: _json_wert(inhalt)
                for schluessel, inhalt in wert.items()}
    if isinstance(wert, (list, tuple)):
        return [_json_wert(inhalt) for inhalt in wert]
    return wert


def _quelle_hash(knoten, paketwurzel: Path) -> tuple[str, str | None]:
    geometrie = knoten.geometrie
    if not isinstance(geometrie, Mapping):
        raise GeometriemetadatenFehler(
            "Geometriequelle fehlt fuer Knoten %s" % knoten.id)
    quelle = geometrie.get("quelle")
    if quelle == "obj":
        relativ = geometrie.get("datei")
        try:
            pfad = pfad_im_paket_aufloesen(paketwurzel, relativ)
        except (OSError, RuntimeError, TypeError, ValueError) as fehler:
            raise GeometriemetadatenFehler(
                "OBJ-Quelle fuer %s ist ungueltig: %s"
                % (knoten.id, fehler)) from fehler
        return _sha256_bytes(_datei_lesen(pfad, str(pfad))), relativ
    if quelle == "form":
        try:
            daten = json.dumps(
                _json_wert(geometrie),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError) as fehler:
            raise GeometriemetadatenFehler(
                "Formquelle fuer %s ist nicht kanonisch serialisierbar"
                % knoten.id) from fehler
        return _sha256_bytes(daten), None
    raise GeometriemetadatenFehler(
        "Unbekannte Geometriequelle fuer %s: %r" % (knoten.id, quelle))


def _geometrie_messen(mesh) -> dict[str, object]:
    punkte = mesh.punkte_si
    dreiecke = mesh.dreiecke
    try:
        _, _, volumen, flaeche, geschlossen, randkanten = validiere_mesh(
            punkte, dreiecke, strenge_topologie=True)
        if flaeche <= 0.0:
            raise ValueError("Mesh hat keine positive Oberflaeche")
        schwerpunkt = (
            schwerpunkt_homogen(punkte, dreiecke)[0]
            if geschlossen else schwerpunkt_flaechig(punkte, dreiecke)[0])
        tensor_flaechig = traegheitstensor_flaechig(punkte, dreiecke)
        eigenwerte, eigenvektoren = np.linalg.eigh(tensor_flaechig)
    except (ArithmeticError, TypeError, ValueError, np.linalg.LinAlgError) as fehler:
        raise GeometriemetadatenFehler(
            "Geometriemessung fuer Frame %s fehlgeschlagen: %s"
            % (mesh.frame, fehler)) from fehler

    min_xyz = np.min(punkte, axis=0)
    max_xyz = np.max(punkte, axis=0)
    richtungen = eigenvektoren.copy()
    for spalte in range(richtungen.shape[1]):
        vektor = richtungen[:, spalte]
        pivot = int(np.argmax(np.abs(vektor)))
        if vektor[pivot] < 0.0:
            richtungen[:, spalte] *= -1.0

    return {
        "vertex_count": int(len(punkte)),
        "triangle_count": int(len(dreiecke)),
        "frame": mesh.frame,
        "bounds_m": {
            "min": _liste_rund(min_xyz),
            "max": _liste_rund(max_xyz),
            "extent": _liste_rund(max_xyz - min_xyz),
            "status": "geometrisch_abgeleitet",
        },
        "surface_area_m2": {
            "value": _rund(flaeche),
            "status": "geometrisch_abgeleitet",
        },
        "volume_m3": {
            "value": _rund(abs(volumen)) if geschlossen else None,
            "status": (
                "geometrisch_abgeleitet" if geschlossen else "nicht_verfuegbar"),
        },
        "centroid_m": {
            "value": _liste_rund(schwerpunkt),
            "method": (
                "homogenes_volumen" if geschlossen
                else "flaechengewichteter_schwerpunkt"),
            "status": "geometrisch_abgeleitet",
        },
        "surface_principal_axes": {
            "eigenvalues_m4": _liste_rund(eigenwerte),
            "directions_as_columns": [
                _liste_rund(richtungen[:, index])
                for index in range(richtungen.shape[1])
            ],
            "convention": (
                "Eigenvektor-Vorzeichen durch groesste Komponente "
                "kanonisiert; bei mehrfachen Eigenwerten nicht eindeutig"),
            "status": "geometrisch_abgeleitet",
        },
        "topology": {
            "closed_oriented_surface": bool(geschlossen),
            "boundary_edge_count": int(randkanten),
            "status": "validiert",
        },
        "profile_sections": {
            "classification": "unklar",
            "sections": None,
            "reason": (
                "Kein validierter Profil- und Querschnittsdetektor in "
                "dieser Algorithmusversion"),
            "status": "unklar",
        },
    }


def _baue_metadaten(paketwurzel, materialien):
    try:
        wurzel = Path(paketwurzel).resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as fehler:
        raise GeometriemetadatenFehler(
            "Paketwurzel kann nicht aufgeloest werden: %s" % fehler) from fehler
    manifest_pfad = wurzel / "modell.json"
    manifest_vorher = _datei_lesen(manifest_pfad, "Modellmanifest")
    try:
        manifest = lade_modellmanifest(wurzel, materialien)
        quellinfos = {}
        for knoten, _ in _blaetter(manifest.koerper):
            quellinfos[knoten.id] = _quelle_hash(knoten, wurzel)
        paket = lade_modellpaket(wurzel, materialien)
    except (OSError, RuntimeError, TypeError, ValueError) as fehler:
        raise GeometriemetadatenFehler(
            "Modellpaket kann nicht analysiert werden: %s" % fehler) from fehler

    teile = []
    quellpfade = []
    for knoten, knotenpfad in _blaetter(paket.manifest.koerper):
        quelle_hash, quelle_pfad = quellinfos[knoten.id]
        if quelle_pfad is not None:
            quellpfade.append((quelle_pfad, quelle_hash))
        mesh = paket.meshes[knoten.id]
        teile.append({
            "node_id": knoten.id,
            "node_path": knotenpfad,
            "role": knoten.rolle,
            "source": {
                "type": knoten.geometrie["quelle"],
                "path": quelle_pfad,
                "sha256": quelle_hash,
                "hash_scope": (
                    "raw_file_bytes" if quelle_pfad is not None
                    else "canonical_geometry_definition"),
            },
            "canonical_mesh_sha256": _mesh_hash(mesh),
            "geometry": _geometrie_messen(mesh),
        })

    manifest_nachher = _datei_lesen(manifest_pfad, "Modellmanifest")
    if manifest_vorher != manifest_nachher:
        raise GeometriemetadatenFehler(
            "Modellmanifest wurde waehrend der Geometriemessung veraendert")
    for relativ, vorher in quellpfade:
        aktuell = _sha256_bytes(_datei_lesen(
            pfad_im_paket_aufloesen(wurzel, relativ), relativ))
        if vorher != aktuell:
            raise GeometriemetadatenFehler(
                "Geometriequelle wurde waehrend der Messung veraendert: %s"
                % relativ)

    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": {
            "name": "segelphysik.core.hydrodynamik_metadaten",
            "version": ALGORITHMUS_VERSION,
        },
        "model": {
            "id": paket.manifest.id,
            "name": paket.manifest.name,
            "manifest_sha256": _sha256_bytes(manifest_vorher),
            "obj_to_m": _rund(paket.manifest.obj_zu_m),
            "obj_axes_matrix_to_leaf": [
                _liste_rund(zeile)
                for zeile in paket.manifest.obj_achsenmatrix_zu_blatt
            ],
            "leaf_frame": "blatt",
        },
        "units": {
            "length": "m",
            "area": "m^2",
            "volume": "m^3",
        },
        "parts": teile,
    }


def erzeuge_geometriemetadaten(paketwurzel, materialien) -> dict[str, object]:
    """Analysiert ein Paket ohne Dateien zu schreiben oder den Loader zu aendern."""
    try:
        return _baue_metadaten(paketwurzel, materialien)
    except GeometriemetadatenFehler:
        raise
    except (ArithmeticError, OSError, RuntimeError, TypeError, ValueError) as fehler:
        raise GeometriemetadatenFehler(
            "Geometriemetadaten konnten nicht erzeugt werden: %s" % fehler
        ) from fehler


def sidecar_pfad(paketwurzel) -> Path:
    wurzel = Path(paketwurzel).resolve(strict=True)
    return wurzel / SIDECAR_ORDNER / SIDECAR_DATEI


def schreibe_geometriemetadaten(paketwurzel, materialien) -> Path:
    """Schreibt das Sidecar atomar und verweigert jedes Ueberschreiben."""
    metadaten = erzeuge_geometriemetadaten(paketwurzel, materialien)
    wurzel = Path(paketwurzel).resolve(strict=True)
    ordner = wurzel / SIDECAR_ORDNER
    if ordner.is_symlink():
        raise GeometriemetadatenFehler(
            "Hydrodynamik-Sidecarordner darf kein Symlink sein")
    try:
        ordner.mkdir(exist_ok=True)
        aufgeloester_ordner = ordner.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as fehler:
        raise GeometriemetadatenFehler(
            "Sidecarordner kann nicht sicher angelegt werden: %s" % fehler
        ) from fehler
    if not aufgeloester_ordner.is_relative_to(wurzel) or not aufgeloester_ordner.is_dir():
        raise GeometriemetadatenFehler(
            "Sidecarordner liegt nicht als Verzeichnis im Modellpaket")

    ziel = aufgeloester_ordner / SIDECAR_DATEI
    if ziel.exists() or ziel.is_symlink():
        raise GeometriemetadatenFehler(
            "Sidecar existiert bereits und wird nicht ueberschrieben: %s" % ziel)
    try:
        daten = (
            json.dumps(
                metadaten, ensure_ascii=False, allow_nan=False, sort_keys=True,
                indent=2)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as fehler:
        raise GeometriemetadatenFehler(
            "Geometriemetadaten sind nicht kanonisch serialisierbar") from fehler

    temp_pfad = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".geometrie-", suffix=".tmp",
                dir=aufgeloester_ordner, delete=False) as datei:
            temp_pfad = Path(datei.name)
            datei.write(daten)
            datei.flush()
            os.fsync(datei.fileno())
        os.link(temp_pfad, ziel)
    except FileExistsError as fehler:
        raise GeometriemetadatenFehler(
            "Sidecar wurde parallel angelegt; vorhandene Datei bleibt "
            "unveraendert: %s" % ziel) from fehler
    except OSError as fehler:
        raise GeometriemetadatenFehler(
            "Sidecar konnte nicht atomar und ohne Ueberschreiben "
            "veroeffentlicht werden: %s" % fehler) from fehler
    finally:
        if temp_pfad is not None:
            try:
                temp_pfad.unlink()
            except FileNotFoundError:
                pass
            except OSError as fehler:
                raise GeometriemetadatenFehler(
                    "Temporäre Sidecardatei konnte nicht entfernt werden: %s"
                    % fehler) from fehler
    return ziel


def pruefe_geometriemetadaten(paketwurzel, materialien) -> dict[str, object]:
    """Prueft Schemainhalt und Aktualitaet gegen das aktuelle Modellpaket."""
    ziel = sidecar_pfad(paketwurzel)
    wurzel = Path(paketwurzel).resolve(strict=True)
    if (wurzel / SIDECAR_ORDNER).is_symlink():
        raise GeometriemetadatenFehler(
            "Geometriemetadaten-Sidecarordner darf kein Symlink sein")
    if ziel.is_symlink():
        raise GeometriemetadatenFehler(
            "Geometriemetadaten-Sidecar darf kein Symlink sein")
    try:
        aufgeloest = ziel.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as fehler:
        raise GeometriemetadatenFehler(
            "Geometriemetadaten-Sidecar fehlt oder ist ungueltig: %s"
            % fehler) from fehler
    if not aufgeloest.is_relative_to(wurzel) or not aufgeloest.is_file():
        raise GeometriemetadatenFehler(
            "Geometriemetadaten-Sidecar liegt nicht als Datei im Modellpaket")
    rohdaten = _datei_lesen(aufgeloest, "Geometriemetadaten-Sidecar")

    def doppelter_schluessel(paar):
        ergebnis = {}
        for schluessel, wert in paar:
            if schluessel in ergebnis:
                raise GeometriemetadatenFehler(
                    "Doppelter JSON-Schluessel im Sidecar: %r" % schluessel)
            ergebnis[schluessel] = wert
        return ergebnis

    def keine_konstante(wert):
        raise GeometriemetadatenFehler(
            "Nicht-endliche JSON-Konstante im Sidecar: %s" % wert)

    try:
        geladen = json.loads(
            rohdaten, object_pairs_hook=doppelter_schluessel,
            parse_constant=keine_konstante)
    except GeometriemetadatenFehler:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as fehler:
        raise GeometriemetadatenFehler(
            "Sidecar enthaelt kein gueltiges UTF-8-JSON: %s" % fehler
        ) from fehler

    erwartet = erzeuge_geometriemetadaten(paketwurzel, materialien)
    if geladen != erwartet:
        raise GeometriemetadatenFehler(
            "Geometriemetadaten-Sidecar stimmt nicht mit Schema, "
            "Quellhashes oder aktueller Geometrie ueberein")
    return erwartet
