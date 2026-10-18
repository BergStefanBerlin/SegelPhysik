"""Konflikterkennung und transaktionale Quellkorrektur für Volumenmeshes."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .massen import validiere_mesh


class GeometrieKonfliktFehler(ValueError):
    """Geometriekonflikt oder unsichere Korrektur einer Modellquelle."""


@dataclass(frozen=True)
class Konflikt:
    name_a: str
    name_b: str
    volumen: float


def _manifold3d():
    try:
        import manifold3d as m3d
    except ImportError as fehler:
        raise GeometrieKonfliktFehler(
            "Manifold3D wird für Boolesche Geometrieoperationen benötigt") from fehler
    return m3d


def _toleranz_pruefen(wert, name):
    try:
        wert = float(wert)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("%s muss eine endliche, nicht-negative Zahl sein"
                         % name) from fehler
    if not np.isfinite(wert) or wert < 0.0:
        raise ValueError("%s muss eine endliche, nicht-negative Zahl sein"
                         % name)
    return wert


def _manifold(punkte, dreiecke, toleranz=0.0):
    m3d = _manifold3d()
    toleranz = _toleranz_pruefen(toleranz, "Mesh-Toleranz")
    try:
        punkte, dreiecke, *_ = validiere_mesh(
            punkte, dreiecke, geschlossen_erforderlich=True)
        mesh = m3d.Mesh64(
            np.array(punkte, dtype=np.float64, order="C", copy=True),
            np.array(dreiecke, dtype=np.uint64, order="C", copy=True),
            tolerance=toleranz)
        solid = m3d.Manifold(mesh)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise GeometrieKonfliktFehler(
            "Volumenmesh konnte nicht an Manifold3D übergeben werden: %s"
            % fehler) from fehler
    if solid.status() != m3d.Error.NoError:
        raise GeometrieKonfliktFehler(
            "Manifold3D hat das Eingabemesh zurückgewiesen: %s"
            % solid.status())
    return solid


def _mesh_daten(solid):
    mesh = solid.to_mesh64()
    punkte = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    dreiecke = np.asarray(mesh.tri_verts, dtype=np.int64)
    if dreiecke.size == 0:
        raise GeometrieKonfliktFehler(
            "Boolesche Geometrieoperation lieferte ein volumenloses Mesh")
    if solid.status() != _manifold3d().Error.NoError:
        raise GeometrieKonfliktFehler(
            "Boolesches Ergebnis hat einen ungültigen Manifold3D-Status: %s"
            % solid.status())
    try:
        punkte, dreiecke, volumen, *_ = validiere_mesh(
            punkte, dreiecke, geschlossen_erforderlich=True)
    except ValueError as fehler:
        raise GeometrieKonfliktFehler(
            "Boolesches Ergebnis ist kein gültiges geschlossenes Volumenmesh: %s"
            % fehler) from fehler
    if not np.isfinite(volumen) or abs(volumen) <= 1e-12:
        raise GeometrieKonfliktFehler(
            "Boolesche Geometrieoperation lieferte ein volumenloses Mesh")
    if volumen < 0.0:
        dreiecke = dreiecke[:, [0, 2, 1]]
    return punkte, dreiecke, abs(volumen)


def _bounds_ueberschneiden(mesh_a, mesh_b, toleranz):
    bounds_a = mesh_a.bounding_box()
    bounds_b = mesh_b.bounding_box()
    grenzen_a = np.asarray((bounds_a[:3], bounds_a[3:])).T
    grenzen_b = np.asarray((bounds_b[:3], bounds_b[3:])).T
    ueberlappung = np.minimum(grenzen_a[:, 1], grenzen_b[:, 1]) - np.maximum(
        grenzen_a[:, 0], grenzen_b[:, 0])
    return bool(np.all(ueberlappung > toleranz))


def _schnittvolumen(mesh_a, mesh_b, beschreibung):
    try:
        schnitt = mesh_a ^ mesh_b
        volumen = float(schnitt.volume())
    except Exception as fehler:
        raise GeometrieKonfliktFehler(
            "Schnittprüfung für %s fehlgeschlagen: %s"
            % (beschreibung, fehler)) from fehler
    if schnitt.status() != _manifold3d().Error.NoError:
        raise GeometrieKonfliktFehler(
            "Schnittprüfung für %s lieferte ungültigen Status: %s"
            % (beschreibung, schnitt.status()))
    if not np.isfinite(volumen):
        raise GeometrieKonfliktFehler(
            "Schnittprüfung für %s lieferte nicht-endliches Volumen"
            % beschreibung)
    return volumen


def finde_konflikte(teile, *, toleranz=1e-8, mindestvolumen=1e-12):
    """Findet Paare überlappender, geschlossener und volumetrischer Blätter.

    `teile` enthält Dictionaries mit `name`, `form=(punkte, dreiecke)` und
    `volumetrisch`; Schalen werden ausdrücklich übersprungen.
    """
    toleranz = _toleranz_pruefen(toleranz, "Toleranz")
    mindestvolumen = _toleranz_pruefen(
        mindestvolumen, "Mindestvolumen")
    volumina = []
    for teil in teile:
        if not teil.get("volumetrisch", False):
            continue
        punkte, dreiecke = teil["form"]
        mesh = _manifold(punkte, dreiecke, toleranz)
        volumina.append((str(teil["name"]), mesh))

    konflikte = []
    for index, (name_a, mesh_a) in enumerate(volumina):
        for name_b, mesh_b in volumina[index + 1:]:
            if not _bounds_ueberschneiden(mesh_a, mesh_b, toleranz):
                continue
            volumen = _schnittvolumen(mesh_a, mesh_b, "%s/%s" % (
                name_a, name_b))
            if volumen > mindestvolumen:
                konflikte.append(Konflikt(name_a, name_b, volumen))
    return konflikte


def differenzieren(konflikt_form, vorrang_form, *, toleranz=1e-8):
    """Berechnet und validiert `Konfliktkörper minus Vorrangkörper`."""
    toleranz = _toleranz_pruefen(toleranz, "Toleranz")
    mesh_konflikt = _manifold(*konflikt_form, toleranz)
    mesh_vorrang = _manifold(*vorrang_form, toleranz)
    try:
        differenz = mesh_konflikt - mesh_vorrang
    except Exception as fehler:
        raise GeometrieKonfliktFehler(
            "Boolesche Differenz ist fehlgeschlagen: %s" % fehler) from fehler
    return _mesh_daten(differenz)


def _atomar_schreiben(pfad, daten):
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    temporaer = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="wb", dir=pfad.parent, prefix=pfad.name + ".",
                suffix=".tmp", delete=False) as datei:
            temporaer = Path(datei.name)
            datei.write(daten)
            datei.flush()
            os.fsync(datei.fileno())
        os.replace(temporaer, pfad)
    finally:
        if temporaer is not None and temporaer.exists():
            temporaer.unlink()


def _sicherung_anlegen(pfad, original):
    basis = Path(str(pfad) + ".bak")
    index = 0
    while True:
        sicherung = basis if index == 0 else Path("%s.%d" % (basis, index))
        try:
            with sicherung.open("xb") as datei:
                datei.write(original)
                datei.flush()
                os.fsync(datei.fileno())
            return sicherung
        except FileExistsError:
            index += 1


def _transaktionale_aenderung(pfad, neue_daten, validiere):
    pfad = Path(pfad)
    try:
        original = pfad.read_bytes()
    except OSError as fehler:
        raise GeometrieKonfliktFehler(
            "Modellquelle konnte nicht gesichert werden: %s" % fehler) from fehler
    sicherung = _sicherung_anlegen(pfad, original)
    try:
        _atomar_schreiben(pfad, neue_daten)
        validiere()
    except Exception as fehler:
        try:
            _atomar_schreiben(pfad, original)
        except OSError as rollback_fehler:
            raise GeometrieKonfliktFehler(
                "Änderung fehlgeschlagen (%s) und Quelle konnte nicht "
                "zurückgesichert werden (%s); Sicherung: %s"
                % (fehler, rollback_fehler, sicherung)) from fehler
        raise GeometrieKonfliktFehler(
            "Änderung zurückgerollt; ursprüngliche Quelle bleibt erhalten: %s"
            % fehler) from fehler
    return sicherung


def _obj_schreiben(punkte, dreiecke):
    zeilen = ["# Korrigiertes SegelPhysik-Mesh\n"]
    zeilen.extend("v %.17g %.17g %.17g\n" % tuple(punkt) for punkt in punkte)
    zeilen.extend(
        "f %d %d %d\n" % tuple(index + 1 for index in dreieck)
        for dreieck in dreiecke)
    return "".join(zeilen).encode("utf-8")


def _obj_zu_welt(punkte, skala):
    return np.stack((punkte[:, 2], punkte[:, 0], punkte[:, 1]), axis=1) * skala


def _welt_zu_obj(punkte, skala):
    return np.stack((punkte[:, 1], punkte[:, 2], punkte[:, 0]), axis=1) / skala


def korrigiere_obj_quelle(quellpfad, konflikt_form, vorrang_form, *,
                          skala=1.0, toleranz=1e-8):
    """Beschneidet eine OBJ-Quelle, sichert sie und validiert Reload/No-Conflict."""
    try:
        skala = float(skala)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError(
            "OBJ-Skalierung muss endlich und positiv sein") from fehler
    if not np.isfinite(skala) or skala <= 0.0:
        raise ValueError("OBJ-Skalierung muss endlich und positiv sein")
    punkte, dreiecke, _volumen = differenzieren(
        konflikt_form, vorrang_form, toleranz=toleranz)
    quelle_punkte = _welt_zu_obj(punkte, skala)
    neue_daten = _obj_schreiben(quelle_punkte, dreiecke)

    def validiere():
        from .boot_bau import lade_obj

        geladene_punkte, geladene_dreiecke = lade_obj(str(quellpfad))
        welt_punkte = _obj_zu_welt(geladene_punkte, skala)
        mesh = _manifold(welt_punkte, geladene_dreiecke, toleranz)
        vorrang_mesh = _manifold(*vorrang_form, toleranz)
        if (_bounds_ueberschneiden(mesh, vorrang_mesh, toleranz)
                and _schnittvolumen(
                    mesh, vorrang_mesh, "gespeicherte OBJ-Quelle/Vorrangkörper")
                > 1e-12):
            raise GeometrieKonfliktFehler(
                "Gespeicherte OBJ-Quelle überschneidet weiterhin den Vorrangkörper")
        _mesh_daten(mesh)

    return _transaktionale_aenderung(quellpfad, neue_daten, validiere)


def override_aus_eintrag(eintrag):
    """Lädt ein optionales, versioniertes Mesh-Override einer prozeduralen Form."""
    override = eintrag.get("_geometrie_override")
    if override is None:
        return None
    if not isinstance(override, dict) or override.get("version") != 1:
        raise GeometrieKonfliktFehler("Unbekannte prozedurale Mesh-Override-Version")
    try:
        punkte = np.asarray(override["punkte"], dtype=np.float64)
        dreiecke = np.asarray(override["dreiecke"], dtype=np.int64)
        punkte, dreiecke, volumen, *_ = validiere_mesh(
            punkte, dreiecke, geschlossen_erforderlich=True)
    except (KeyError, TypeError, ValueError) as fehler:
        raise GeometrieKonfliktFehler(
            "Ungültiges prozedurales Mesh-Override: %s" % fehler) from fehler
    if not np.isfinite(volumen) or abs(volumen) <= 1e-12:
        raise GeometrieKonfliktFehler(
            "Prozedurales Mesh-Override besitzt kein Volumen")
    return punkte, dreiecke


def korrigiere_prozedurale_quelle(quellpfad, eintrag_pfad,
                                  konflikt_form, vorrang_form, *,
                                  toleranz=1e-8):
    """Speichert eine Mesh-Überschreibung neben der unveränderten Formdefinition."""
    toleranz = _toleranz_pruefen(toleranz, "Toleranz")
    punkte, dreiecke, _volumen = differenzieren(
        konflikt_form, vorrang_form, toleranz=toleranz)
    quellpfad = Path(quellpfad)
    try:
        quelle = json.loads(quellpfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as fehler:
        raise GeometrieKonfliktFehler(
            "Prozedurale Quelldatei konnte nicht geladen werden: %s" % fehler) from fehler
    ziel = quelle
    try:
        for schluessel in eintrag_pfad:
            ziel = ziel[schluessel]
    except (KeyError, TypeError) as fehler:
        raise GeometrieKonfliktFehler(
            "Prozedurale Definition wurde nicht gefunden: %r"
            % (tuple(eintrag_pfad),)) from fehler
    if not isinstance(ziel, dict) or "form" not in ziel:
        raise GeometrieKonfliktFehler(
            "Mesh-Override kann nur an einer prozeduralen Form gespeichert werden")
    ziel["_geometrie_override"] = {
        "version": 1,
        "punkte": punkte.tolist(),
        "dreiecke": dreiecke.tolist(),
    }
    neue_daten = (json.dumps(
        quelle, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    def validiere():
        gespeicherte = json.loads(quellpfad.read_text(encoding="utf-8"))
        ziel_neu = gespeicherte
        for schluessel in eintrag_pfad:
            ziel_neu = ziel_neu[schluessel]
        form = override_aus_eintrag(ziel_neu)
        mesh = _manifold(*form, toleranz)
        vorrang_mesh = _manifold(*vorrang_form, toleranz)
        if (_bounds_ueberschneiden(mesh, vorrang_mesh, toleranz)
                and _schnittvolumen(
                    mesh, vorrang_mesh,
                    "gespeicherter prozeduraler Override/Vorrangkörper")
                > 1e-12):
            raise GeometrieKonfliktFehler(
                "Gespeicherter Override überschneidet weiterhin den Vorrangkörper")

    return _transaktionale_aenderung(quellpfad, neue_daten, validiere)
