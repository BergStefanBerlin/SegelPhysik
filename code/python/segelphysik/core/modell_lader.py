"""Strikte Lade- und Paketvalidierung für versionierte Modellmanifeste."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from types import MappingProxyType

import numpy as np

from .koerper_formen import FORMEN
from .mesh import (
    Mesh,
    mesh_aus_quelle,
    pfad_im_paket_aufloesen,
    validiere_mesh_fuer_masse,
)

_SCHEMA_VERSION = "1.0"
_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_ROLLEN = {
    "rumpf", "kiel", "ruder", "segel", "stehendes_gut", "allgemein",
}


class ModellFehler(ValueError):
    """Fehler in Manifest, Modellpaket oder dessen Geometrie."""


@dataclass(frozen=True, slots=True)
class ModellPose:
    translation_m: tuple[float, float, float]
    rotation_quaternion_wxyz: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class ModellGelenk:
    eltern_id: str
    achse_eltern: tuple[float, float, float]
    winkel_rad: float


@dataclass(frozen=True, slots=True)
class ModellKnoten:
    id: str
    name: str
    teile: tuple[ModellKnoten, ...] = ()
    rolle_default: str | None = None
    rolle: str | None = None
    geometrie: Mapping[str, object] | None = None
    material: str | None = None
    dichte_kg_pro_m3: float | None = None
    wanddicke_m: float | None = None
    farbe: str | None = None
    farbe_unter_wasser: str | None = None
    verdraengend: bool | None = None
    pose: ModellPose | None = None
    gelenk: ModellGelenk | None = None
    masse_kg: float | None = None
    position_rumpf_m: tuple[float, float, float] | None = None


@dataclass(frozen=True, slots=True)
class ModellManifest:
    schema_version: str
    id: str
    name: str
    beschreibung: str | None
    paketwurzel: Path
    obj_zu_m: float
    obj_achsenmatrix_zu_blatt: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    koerper: ModellKnoten
    rumpfreferenz_m: tuple[float, float, float] | None = None


@dataclass(frozen=True, slots=True)
class Modellpaket:
    manifest: ModellManifest
    meshes: Mapping[str, Mesh]


def _doppelter_schluessel(paar):
    ergebnis = {}
    for schluessel, wert in paar:
        if schluessel in ergebnis:
            raise ModellFehler("Doppelter JSON-Schlüssel: %r" % schluessel)
        ergebnis[schluessel] = wert
    return ergebnis


def _mapping(wert, kontext):
    if not isinstance(wert, Mapping):
        raise ModellFehler("%s: JSON-Objekt erwartet" % kontext)
    return wert


def _felder(wert, erforderlich, optional, kontext):
    _mapping(wert, kontext)
    fehlend = erforderlich - wert.keys()
    unbekannt = wert.keys() - erforderlich - optional
    if fehlend:
        raise ModellFehler(
            "%s: Pflichtfelder fehlen: %s"
            % (kontext, ", ".join(sorted(fehlend))))
    if unbekannt:
        raise ModellFehler(
            "%s: unbekannte Felder: %s"
            % (kontext, ", ".join(sorted(unbekannt))))


def _text(wert, kontext):
    if not isinstance(wert, str) or not wert.strip():
        raise ModellFehler("%s: nichtleerer Text erwartet" % kontext)
    return wert


def _slug(wert, kontext):
    text = _text(wert, kontext)
    if not _SLUG.fullmatch(text):
        raise ModellFehler("%s: ungültiger Slug %r" % (kontext, text))
    return text


def _zahl(wert, kontext, positiv=False):
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        eigenschaft = "positive endliche Zahl" if positiv else "endliche Zahl"
        raise ModellFehler("%s: %s erwartet" % (kontext, eigenschaft))
    try:
        wert = float(wert)
    except (OverflowError, ValueError) as fehler:
        raise ModellFehler("%s: endliche Zahl erwartet" % kontext) from fehler
    if not math.isfinite(wert) or (positiv and wert <= 0.0):
        eigenschaft = "positive endliche Zahl" if positiv else "endliche Zahl"
        raise ModellFehler("%s: %s erwartet" % (kontext, eigenschaft))
    return wert


def _vektor3(wert, kontext):
    if not isinstance(wert, list) or len(wert) != 3:
        raise ModellFehler("%s: drei Koordinaten erwartet" % kontext)
    return tuple(_zahl(x, kontext) for x in wert)


def _farbe(wert, kontext):
    if (not isinstance(wert, str) or not wert.startswith("#")
            or len(wert) not in (4, 7)
            or any(ziffer not in "0123456789abcdefABCDEF"
                   for ziffer in wert[1:])):
        raise ModellFehler("%s: Hex-Farbe (#rgb oder #rrggbb) erwartet"
                           % kontext)
    return wert


def _rolle(wert, kontext):
    if not isinstance(wert, str) or wert not in _ROLLEN:
        raise ModellFehler(
            "%s: unbekannte Rolle %r (erlaubt: %s)"
            % (kontext, wert, ", ".join(sorted(_ROLLEN))))
    return wert


def _pose_laden(wert, kontext):
    _felder(
        wert,
        {"translation_m", "rotation_quaternion_wxyz"},
        set(),
        kontext,
    )
    translation = wert["translation_m"]
    quaternion = wert["rotation_quaternion_wxyz"]
    if not isinstance(translation, list) or len(translation) != 3:
        raise ModellFehler(
            "%s.translation_m: drei Koordinaten erwartet" % kontext)
    if not isinstance(quaternion, list) or len(quaternion) != 4:
        raise ModellFehler(
            "%s.rotation_quaternion_wxyz: vier Werte erwartet" % kontext)
    translation = tuple(
        _zahl(x, "%s.translation_m" % kontext) for x in translation)
    quaternion = tuple(
        _zahl(x, "%s.rotation_quaternion_wxyz" % kontext)
        for x in quaternion)
    norm = math.sqrt(sum(x * x for x in quaternion))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-10):
        raise ModellFehler(
            "%s.rotation_quaternion_wxyz: Quaternion muss normiert sein"
            % kontext)
    return ModellPose(translation, quaternion)


def _gelenk_laden(wert, kontext, eltern_id):
    _felder(
        wert,
        {"eltern_id", "achse_eltern", "winkel_rad"},
        set(),
        kontext,
    )
    if eltern_id is None:
        raise ModellFehler("%s: Wurzelknoten darf kein Gelenk haben" % kontext)
    referenz = _slug(wert["eltern_id"], kontext + ".eltern_id")
    if referenz != eltern_id:
        raise ModellFehler(
            "%s.eltern_id muss dem direkten Elternknoten %r entsprechen"
            % (kontext, eltern_id))
    achse = wert["achse_eltern"]
    if not isinstance(achse, list) or len(achse) != 3:
        raise ModellFehler(
            "%s.achse_eltern: drei Koordinaten erwartet" % kontext)
    achse = tuple(
        _zahl(komponente, kontext + ".achse_eltern")
        for komponente in achse)
    norm = math.sqrt(sum(komponente * komponente for komponente in achse))
    if not math.isfinite(norm) or norm <= 1e-12:
        raise ModellFehler(
            "%s.achse_eltern: Achse darf nicht null sein" % kontext)
    return ModellGelenk(
        referenz,
        tuple(komponente / norm for komponente in achse),
        _zahl(wert["winkel_rad"], kontext + ".winkel_rad"),
    )


def _form_parameter_pruefen(parameter, kontext):
    _mapping(parameter, kontext)
    if "typ" not in parameter or not isinstance(parameter["typ"], str):
        raise ModellFehler("%s.typ: Formtyp erwartet" % kontext)
    typ = parameter["typ"]
    definition = FORMEN.get(typ)
    if definition is None:
        raise ModellFehler("%s.typ: unbekannte Form %r" % (kontext, typ))
    zahlen = set(definition.get("zahlen", ()))
    optionale_zahlen = set(definition.get("optionale_zahlen", ()))
    texte = definition.get("texte", {})
    listen = set(definition.get("listen", ()))
    optionale_listen = set(definition.get("optionale_listen", ()))
    erlaubt = {"typ"} | zahlen | optionale_zahlen | set(texte) | listen | optionale_listen
    unbekannt = parameter.keys() - erlaubt
    if unbekannt:
        raise ModellFehler(
            "%s: unbekannte Formparameter: %s"
            % (kontext, ", ".join(sorted(unbekannt))))
    for feld in zahlen:
        if feld not in parameter:
            raise ModellFehler("%s.%s: Pflichtfeld fehlt" % (kontext, feld))
        _zahl(parameter[feld], "%s.%s" % (kontext, feld), positiv=True)
    for feld in optionale_zahlen & parameter.keys():
        _zahl(parameter[feld], "%s.%s" % (kontext, feld), positiv=True)
    for feld, werte in texte.items():
        if feld in parameter and parameter[feld] not in werte:
            raise ModellFehler(
                "%s.%s: erlaubte Werte: %s"
                % (kontext, feld, ", ".join(werte)))
    for feld in listen | (optionale_listen & parameter.keys()):
        if feld not in parameter:
            raise ModellFehler("%s.%s: Pflichtfeld fehlt" % (kontext, feld))
        liste = parameter[feld]
        if not isinstance(liste, list) or not liste:
            raise ModellFehler("%s.%s: nichtleere Liste erwartet"
                               % (kontext, feld))
        if feld == "eckpunkte_m":
            for index, punkt in enumerate(liste):
                if not isinstance(punkt, list) or len(punkt) != 3:
                    raise ModellFehler(
                        "%s.%s[%d]: drei Koordinaten erwartet"
                        % (kontext, feld, index))
                for koordinat in punkt:
                    _zahl(koordinat, "%s.%s[%d]" % (kontext, feld, index))
        else:
            for index, flaeche in enumerate(liste):
                if (not isinstance(flaeche, list) or len(flaeche) < 3
                        or any(isinstance(x, bool) or not isinstance(x, int)
                               for x in flaeche)):
                    raise ModellFehler(
                        "%s.%s[%d]: mindestens drei ganzzahlige Indizes "
                        "erwartet" % (kontext, feld, index))
                if min(flaeche) < 0 or max(flaeche) >= len(parameter["eckpunkte_m"]):
                    raise ModellFehler(
                        "%s.%s[%d]: Index außerhalb der Eckpunktliste"
                        % (kontext, feld, index))


def _geometrie_laden(wert, kontext, paketwurzel, pruefe_dateipfad=True):
    _mapping(wert, kontext)
    quelle = wert.get("quelle")
    if quelle == "obj":
        _felder(wert, {"quelle", "datei"}, set(), kontext)
        if pruefe_dateipfad:
            try:
                pfad_im_paket_aufloesen(paketwurzel, wert["datei"])
            except (OSError, RuntimeError, TypeError, ValueError) as fehler:
                raise ModellFehler("%s: %s" % (kontext, fehler)) from fehler
    elif quelle == "form":
        _felder(wert, {"quelle", "parameter"}, set(), kontext)
        _form_parameter_pruefen(wert["parameter"], kontext + ".parameter")
    else:
        raise ModellFehler(
            "%s.quelle: unbekannte Geometriequelle %r" % (kontext, quelle))
    return _einfrieren(wert)


def _einfrieren(wert):
    if isinstance(wert, dict):
        return MappingProxyType(
            {schluessel: _einfrieren(inhalt)
             for schluessel, inhalt in wert.items()})
    if isinstance(wert, list):
        return tuple(_einfrieren(inhalt) for inhalt in wert)
    return wert


def _wurzel_aufloesen(wert, kontext):
    try:
        wurzel = Path(wert)
    except (TypeError, ValueError) as fehler:
        raise ModellFehler("%s ist kein gültiger Dateipfad" % kontext) from fehler
    if not wurzel.is_absolute():
        raise ModellFehler("%s muss explizit absolut angegeben werden" % kontext)
    try:
        wurzel = wurzel.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as fehler:
        raise ModellFehler(
            "%s fehlt oder kann nicht aufgelöst werden: %s"
            % (kontext, wurzel)) from fehler
    if not wurzel.is_dir():
        raise ModellFehler("%s ist kein Verzeichnis: %s" % (kontext, wurzel))
    return wurzel


def _knoten_laden(
        wert, kontext, paketwurzel, materialien, ids, geerbte_rolle,
        pruefe_dateipfade, eltern_id=None):
    _mapping(wert, kontext)
    if "masse_kg" in wert:
        _felder(wert, {"id", "name", "masse_kg", "position_rumpf_m"},
                set(), kontext)
        if wert["id"] != "segler" or eltern_id is None:
            raise ModellFehler(
                "%s: Massenblatt muss 'segler' in einer Gruppe sein" % kontext)
        if "segler" in ids:
            raise ModellFehler("%s: doppelte Knoten-ID 'segler'" % kontext)
        ids.add("segler")
        return ModellKnoten(
            "segler", _text(wert["name"], kontext + ".name"),
            rolle="allgemein", verdraengend=False,
            masse_kg=_zahl(wert["masse_kg"], kontext + ".masse_kg", positiv=True),
            position_rumpf_m=_vektor3(
                wert["position_rumpf_m"], kontext + ".position_rumpf_m"))
    if "teile" in wert:
        _felder(
            wert, {"id", "name", "teile"},
            {"rolle_default", "pose", "gelenk"},
            kontext)
        knoten_id = _slug(wert["id"], kontext + ".id")
        knotenkontext = "%s[%s]" % (kontext, knoten_id)
        rolle_default = (
            _rolle(wert["rolle_default"], knotenkontext + ".rolle_default")
            if "rolle_default" in wert else None)
        pose = (
            _pose_laden(wert["pose"], knotenkontext + ".pose")
            if "pose" in wert else None)
        gelenk = (
            _gelenk_laden(
                wert["gelenk"], knotenkontext + ".gelenk", eltern_id)
            if "gelenk" in wert else None)
        geerbte_rolle_fuer_kinder = rolle_default or geerbte_rolle
        kinder = wert["teile"]
        if not isinstance(kinder, list) or not kinder:
            raise ModellFehler(
                "%s.teile: nichtleere Liste erwartet" % knotenkontext)
        teile = tuple(
            _knoten_laden(
                kind,
                "%s.teile[%d]" % (knotenkontext, position),
                paketwurzel,
                materialien,
                ids,
                geerbte_rolle_fuer_kinder,
                pruefe_dateipfade,
                knoten_id,
            )
            for position, kind in enumerate(kinder)
        )
        if knoten_id in ids:
            raise ModellFehler(
                "%s.id: doppelte Knoten-ID %r" % (knotenkontext, knoten_id))
        ids.add(knoten_id)
        return ModellKnoten(
            knoten_id, _text(wert["name"], knotenkontext + ".name"),
            teile=teile, rolle_default=rolle_default, pose=pose,
            gelenk=gelenk)

    _felder(
        wert,
        {"id", "name", "geometrie", "verdrängend"},
        {
            "material", "dichte_kg_pro_m3", "wanddicke_m", "farbe",
            "farbe_unter_wasser", "rolle", "pose", "gelenk",
        },
        kontext,
    )
    knoten_id = _slug(wert["id"], kontext + ".id")
    knotenkontext = "%s[%s]" % (kontext, knoten_id)
    if knoten_id in ids:
        raise ModellFehler(
            "%s.id: doppelte Knoten-ID %r" % (knotenkontext, knoten_id))
    ids.add(knoten_id)
    rolle = (
        _rolle(wert["rolle"], knotenkontext + ".rolle")
        if "rolle" in wert else geerbte_rolle)
    if rolle is None:
        raise ModellFehler(
            "%s: Blatt benötigt eine Rolle oder geerbten Default"
            % knotenkontext)
    if not isinstance(wert["verdrängend"], bool):
        raise ModellFehler(
            "%s.verdrängend: boolescher Wert erwartet" % knotenkontext)

    hat_material = "material" in wert
    hat_dichte = "dichte_kg_pro_m3" in wert
    if hat_material == hat_dichte:
        raise ModellFehler(
            "%s: genau eines von 'material' und 'dichte_kg_pro_m3' ist "
            "erforderlich" % knotenkontext)
    material = None
    dichte = None
    if hat_material:
        material = _text(wert["material"], knotenkontext + ".material")
        if material not in materialien:
            raise ModellFehler(
                "%s.material: unbekanntes Material %r"
                % (knotenkontext, material))
        if "farbe" in wert or "farbe_unter_wasser" in wert:
            raise ModellFehler(
                "%s: Materialblätter dürfen keine Farb-Overrides enthalten"
                % knotenkontext)
    else:
        dichte = _zahl(
            wert["dichte_kg_pro_m3"],
            knotenkontext + ".dichte_kg_pro_m3",
            positiv=True,
        )
    dicke = (
        _zahl(
            wert["wanddicke_m"], knotenkontext + ".wanddicke_m",
            positiv=True)
        if "wanddicke_m" in wert else None)
    farbe = (
        _farbe(wert["farbe"], knotenkontext + ".farbe")
        if "farbe" in wert else None)
    farbe_unter_wasser = (
        _farbe(wert["farbe_unter_wasser"], knotenkontext + ".farbe_unter_wasser")
        if "farbe_unter_wasser" in wert else None)
    pose = (
        _pose_laden(wert["pose"], knotenkontext + ".pose")
        if "pose" in wert else None)
    gelenk = (
        _gelenk_laden(
            wert["gelenk"], knotenkontext + ".gelenk", eltern_id)
        if "gelenk" in wert else None)
    return ModellKnoten(
        knoten_id,
        _text(wert["name"], knotenkontext + ".name"),
        rolle=rolle,
        geometrie=_geometrie_laden(
            wert["geometrie"], knotenkontext + ".geometrie", paketwurzel,
            pruefe_dateipfad=pruefe_dateipfade),
        material=material,
        dichte_kg_pro_m3=dichte,
        wanddicke_m=dicke,
        farbe=farbe,
        farbe_unter_wasser=farbe_unter_wasser,
        verdraengend=wert["verdrängend"],
        pose=pose,
        gelenk=gelenk,
    )


def lade_modellmanifest(
        paketwurzel, materialien, *, _pruefe_geometriepfade=True):
    """Lädt ein Manifest; optional übernimmt der anschließende Meshimport die Pfadprüfung."""
    if not isinstance(materialien, Mapping):
        raise ModellFehler("Materialkatalog muss explizit übergeben werden")
    wurzel = _wurzel_aufloesen(paketwurzel, "Paketwurzel")
    manifest_pfad = wurzel / "modell.json"
    try:
        aufgeloester_manifest_pfad = manifest_pfad.resolve(strict=True)
        if not aufgeloester_manifest_pfad.is_relative_to(wurzel):
            raise ModellFehler("modell.json verlässt die Paketwurzel")
        with aufgeloester_manifest_pfad.open(
                encoding="utf-8-sig") as datei:
            daten = json.load(datei, object_pairs_hook=_doppelter_schluessel)
    except ModellFehler:
        raise
    except OSError as fehler:
        raise ModellFehler(
            "Manifest %s konnte nicht gelesen werden: %s"
            % (manifest_pfad, fehler)) from fehler
    except UnicodeDecodeError as fehler:
        raise ModellFehler(
            "Manifest %s ist nicht UTF-8-kodiert" % manifest_pfad) from fehler
    except json.JSONDecodeError as fehler:
        raise ModellFehler(
            "Ungültiges JSON in %s: %s" % (manifest_pfad, fehler)) from fehler

    kontext = str(manifest_pfad)
    _felder(
        daten,
        {"schema_version", "modell", "geometrie_einheiten", "koerper"},
        {"rumpfreferenz_m"},
        kontext,
    )
    if daten["schema_version"] != _SCHEMA_VERSION:
        raise ModellFehler(
            "%s.schema_version: unterstützt wird nur %s"
            % (kontext, _SCHEMA_VERSION))

    modell = daten["modell"]
    _felder(modell, {"id", "name"}, {"beschreibung"}, kontext + ".modell")
    modell_id = _slug(modell["id"], kontext + ".modell.id")
    if modell_id != wurzel.name:
        raise ModellFehler(
            "%s.modell.id %r muss dem Paketordner %r entsprechen"
            % (kontext, modell_id, wurzel.name))
    name = _text(modell["name"], kontext + ".modell.name")
    beschreibung = (
        _text(modell["beschreibung"], kontext + ".modell.beschreibung")
        if "beschreibung" in modell else None)

    einheiten = daten["geometrie_einheiten"]
    _felder(
        einheiten,
        {"obj_zu_m", "obj_achsenmatrix_zu_blatt"},
        set(),
        kontext + ".geometrie_einheiten",
    )
    obj_zu_m = _zahl(
        einheiten["obj_zu_m"],
        kontext + ".geometrie_einheiten.obj_zu_m",
        positiv=True,
    )
    matrix = einheiten["obj_achsenmatrix_zu_blatt"]
    if (not isinstance(matrix, list) or len(matrix) != 3
            or any(not isinstance(zeile, list) or len(zeile) != 3
                   for zeile in matrix)):
        raise ModellFehler(
            "%s.geometrie_einheiten.obj_achsenmatrix_zu_blatt: "
            "3x3-Matrix erwartet" % kontext)
    matrix_tupel = tuple(
        tuple(_zahl(
            x,
            "%s.geometrie_einheiten.obj_achsenmatrix_zu_blatt"
            % kontext,
        ) for x in zeile)
        for zeile in matrix)
    matrix_array = np.asarray(matrix_tupel, dtype=np.float64)
    if (not np.allclose(
            matrix_array.T @ matrix_array, np.eye(3), rtol=0.0, atol=1e-10)
            or not np.isclose(
                np.linalg.det(matrix_array), 1.0, rtol=0.0, atol=1e-10)):
        raise ModellFehler(
            "%s.geometrie_einheiten.obj_achsenmatrix_zu_blatt muss "
            "rechtshändig und orthogonal sein" % kontext)
    ids = set()
    koerper = _knoten_laden(
        daten["koerper"],
        "%s (Modell %s).koerper" % (kontext, modell_id),
        wurzel,
        materialien,
        ids,
        None,
        _pruefe_geometriepfade,
    )
    referenz = (
        _vektor3(daten["rumpfreferenz_m"], kontext + ".rumpfreferenz_m")
        if "rumpfreferenz_m" in daten else None)
    if "segler" in ids:
        if referenz is None:
            raise ModellFehler("%s: Segler benötigt rumpfreferenz_m" % kontext)
        if not any(k.id == "segler" and k.masse_kg is not None
                   for k in koerper.teile):
            raise ModellFehler(
                "%s: Segler muss direkt im rumpffesten Wurzelframe liegen"
                % kontext)
    return ModellManifest(
        _SCHEMA_VERSION,
        modell_id,
        name,
        beschreibung,
        wurzel,
        obj_zu_m,
        matrix_tupel,
        koerper,
        referenz,
    )


def _blaetter(knoten, pfad=()):
    knotenpfad = pfad + (knoten.id,)
    if knoten.teile:
        for kind in knoten.teile:
            yield from _blaetter(kind, knotenpfad)
    else:
        yield knoten, "/".join(knotenpfad)


def lade_modellpaket(paketwurzel, materialien):
    """Lädt Manifest und Meshes, prüft deren Topologie passend zur Masse."""
    manifest = lade_modellmanifest(
        paketwurzel, materialien, _pruefe_geometriepfade=False)
    meshes = {}
    for knoten, knotenpfad in _blaetter(manifest.koerper):
        if knoten.masse_kg is not None:
            continue
        kontext = "%s/%s" % (manifest.id, knotenpfad)
        try:
            mesh = mesh_aus_quelle(
                knoten.geometrie,
                paketwurzel=manifest.paketwurzel,
                obj_zu_m=manifest.obj_zu_m,
                obj_achsenmatrix_zu_blatt=(
                    manifest.obj_achsenmatrix_zu_blatt),
                frame="blatt",
                fehlerkontext=kontext,
            )
            meshes[knoten.id] = validiere_mesh_fuer_masse(
                mesh,
                wanddicke_m=knoten.wanddicke_m,
                fehlerkontext=kontext,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as fehler:
            meldung = str(fehler)
            if not meldung.startswith(kontext + ": "):
                meldung = "%s: %s" % (kontext, meldung)
            raise ModellFehler(meldung) from fehler
    return Modellpaket(manifest, MappingProxyType(meshes))


def lade_modellkatalog(datenwurzel, materialien):
    """Listet gültige Paketmanifeste, ohne deren Meshdaten zu laden."""
    if not isinstance(materialien, Mapping):
        raise ModellFehler("Materialkatalog muss explizit übergeben werden")
    wurzel = _wurzel_aufloesen(datenwurzel, "Datenwurzel")

    manifesten = []
    ids = set()
    try:
        ordner_liste = sorted(wurzel.iterdir(), key=lambda pfad: pfad.name)
    except OSError as fehler:
        raise ModellFehler(
            "Datenwurzel kann nicht durchsucht werden: %s" % wurzel) from fehler
    for ordner in ordner_liste:
        if not ordner.is_dir():
            continue
        try:
            paketwurzel = ordner.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as fehler:
            raise ModellFehler(
                "Modellpaket kann nicht aufgelöst werden: %s" % ordner) from fehler
        if not paketwurzel.is_relative_to(wurzel):
            raise ModellFehler(
                "Modellpaket verlässt die Datenwurzel: %s" % ordner)
        manifest_pfad = paketwurzel / "modell.json"
        if not manifest_pfad.exists() and not manifest_pfad.is_symlink():
            continue
        manifest = lade_modellmanifest(paketwurzel, materialien)
        if manifest.id in ids:
            raise ModellFehler(
                "Doppelte Modell-ID im Katalog: %r" % manifest.id)
        ids.add(manifest.id)
        manifesten.append(manifest)
    return tuple(manifesten)
