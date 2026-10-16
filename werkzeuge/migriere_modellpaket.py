"""Migriert Legacy-koerper.json/materialien.json in validierte Modellpakete.

Standardmaessig wird nur ein Validierungsbericht ausgegeben. Erst --anwenden
schreibt Pakete; Quelldateien werden nie veraendert und Ziele nie ueberschrieben.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata

from segelphysik.core import konfig_lader, koerper, massen
from segelphysik.core.mesh import mesh_aus_quelle, validiere_mesh_fuer_masse
from segelphysik.core.modell_lader import lade_modellpaket


OBJ_ZU_M = 0.25
OBJ_ACHSMATRIX = (
    (0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
)
_SLUG_UNGUELTIG = re.compile(r"[^a-z0-9_-]+")


class MigrationFehler(ValueError):
    """Fehler bei Validierung oder sicherer Veroeffentlichung."""

    def __init__(self, bericht):
        self.bericht = bericht
        super().__init__("; ".join(bericht.get("fehler", [])))


def _slug(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode(
        "ascii", "ignore").decode("ascii").lower()
    slug = _SLUG_UNGUELTIG.sub("_", ascii_text).strip("_-")
    if not slug or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):
        raise ValueError(
            "Name kann nicht sicher als Modell-ID abgebildet werden: %r"
            % text)
    return slug


def _unterhalb(pfad, wurzel):
    try:
        pfad.relative_to(wurzel)
        return True
    except ValueError:
        return False


def _knoten_id(name, eltern_id):
    teil = _slug(name)
    return teil if eltern_id == "root" else eltern_id + "_" + teil


def _obj_quelle(name, geometriewurzel, paketwurzel, paket_relativ):
    if Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError(
            "OBJ-Blattname muss einem einzelnen Dateinamen entsprechen: %r"
            % name)
    quelle = (geometriewurzel / (name + ".obj")).resolve(strict=True)
    if not _unterhalb(quelle, geometriewurzel):
        raise ValueError(
            "OBJ-Datei liegt außerhalb der Geometriewurzel: %s" % quelle)
    if not quelle.is_file():
        raise ValueError("OBJ-Quelle ist keine Datei: %s" % quelle)
    ziel_relativ = paket_relativ / (name + ".obj")
    ziel = paketwurzel / ziel_relativ
    ziel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(quelle, ziel)
    return {"quelle": "obj", "datei": ziel_relativ.as_posix()}


def _geometrie_aus_legacy(
        eintrag, name, geometriewurzel, paketwurzel, paket_relativ):
    if "form" in eintrag:
        return {
            "quelle": "form",
            "parameter": copy.deepcopy(eintrag["form"]),
        }
    return _obj_quelle(
        name, geometriewurzel, paketwurzel, paket_relativ)


def _knoten_aus_legacy(
        eintrag, name, eltern_id, geometriewurzel, paketwurzel,
        zaehler, geerbte_rolle=None):
    knoten_id = _knoten_id(name, eltern_id)
    if knoten_id in zaehler["ids"]:
        raise ValueError("Knoten-ID kollidiert: %s" % knoten_id)
    zaehler["ids"].add(knoten_id)
    if "teile" in eintrag:
        knoten = {
            "id": knoten_id,
            "name": name,
            "teile": [
                _knoten_aus_legacy(
                    teil, teil["name"], knoten_id, geometriewurzel,
                    paketwurzel, zaehler,
                    eintrag.get("rolle_default", geerbte_rolle))
                for teil in eintrag["teile"]
            ],
        }
        if "rolle_default" in eintrag:
            knoten["rolle_default"] = eintrag["rolle_default"]
        return knoten

    geometrie = _geometrie_aus_legacy(
        eintrag, name, geometriewurzel, paketwurzel,
        Path("geometrie") / knoten_id)
    mesh = mesh_aus_quelle(
        geometrie,
        paketwurzel=paketwurzel,
        obj_zu_m=OBJ_ZU_M,
        obj_achsenmatrix_zu_blatt=OBJ_ACHSMATRIX,
        frame="blatt",
        fehlerkontext=knoten_id,
    )
    mesh = validiere_mesh_fuer_masse(
        mesh,
        wanddicke_m=eintrag.get("wanddicke_m"),
        fehlerkontext=knoten_id,
    )
    _punkte, _dreiecke, volumen, _flaeche, geschlossen, _offene_kanten = (
        massen.validiere_mesh(
            mesh.punkte_si, mesh.dreiecke,
            strenge_topologie=True,
            normalisiere_orientierung=True))
    verdrangend = bool(
        geschlossen and abs(volumen) >= koerper.VOLUMEN_EPS)

    knoten = {
        "id": knoten_id,
        "name": name,
        "geometrie": geometrie,
        "verdrängend": verdrangend,
        "rolle": eintrag.get("rolle", geerbte_rolle or "allgemein"),
    }
    for feld in (
            "material", "dichte_kg_pro_m3", "wanddicke_m", "farbe",
            "farbe_unter_wasser", "pose", "gelenk"):
        if feld in eintrag:
            knoten[feld] = copy.deepcopy(eintrag[feld])
    zaehler["blaetter"] += 1
    if geometrie["quelle"] == "obj":
        zaehler["obj_dateien"] += 1
    return knoten


def _paket_erstellen(
        modell_id, modellname, eintrag, geometriewurzel, paketwurzel,
        materialien):
    paketwurzel.mkdir(parents=True)
    zaehler = {
        "ids": set() if "form" in eintrag else {"root"},
        "blaetter": 0,
        "obj_dateien": 0,
    }
    if "form" in eintrag:
        wurzel = _knoten_aus_legacy(
            eintrag, modellname, "root", geometriewurzel, paketwurzel,
            zaehler)
        wurzel["id"] = "root"
    else:
        wurzel = {
            "id": "root",
            "name": modellname,
            "teile": [
                _knoten_aus_legacy(
                    teil, teil["name"], "root", geometriewurzel,
                    paketwurzel, zaehler,
                    eintrag.get("rolle_default"))
                for teil in eintrag["teile"]
            ],
        }
    manifest = {
        "schema_version": "1.0",
        "modell": {
            "id": modell_id,
            "name": modellname,
            "beschreibung": (
                "Migriert aus dem Legacy-Format; physikalische Rollen ohne "
                "Legacy-Angabe auf 'allgemein' gesetzt."),
        },
        "geometrie_einheiten": {
            "obj_zu_m": OBJ_ZU_M,
            "obj_achsenmatrix_zu_blatt": [
                list(zeile) for zeile in OBJ_ACHSMATRIX],
        },
        "koerper": wurzel,
    }
    with (paketwurzel / "modell.json").open(
            "w", encoding="utf-8", newline="\n") as datei:
        json.dump(manifest, datei, ensure_ascii=False, indent=2)
        datei.write("\n")
    paket = lade_modellpaket(paketwurzel, materialien)
    if zaehler["blaetter"] == 0 or not paket.meshes:
        raise ValueError("Migriertes Modell besitzt keine Geometrieblätter")
    return zaehler


def migriere(
        konfigurationsordner, geometriewurzel, ausgabeordner, *, anwenden=False):
    konfigurationsordner = Path(konfigurationsordner).resolve(strict=True)
    geometriewurzel = Path(geometriewurzel).resolve(strict=True)
    ausgabeordner = Path(ausgabeordner).resolve()
    if not konfigurationsordner.is_dir() or not geometriewurzel.is_dir():
        raise ValueError("Quellpfade müssen Verzeichnisse sein")
    if not ausgabeordner.is_absolute():
        raise ValueError("Ausgabewurzel muss absolut sein")
    for quelle in (konfigurationsordner, geometriewurzel):
        if (_unterhalb(ausgabeordner, quelle)
                or _unterhalb(quelle, ausgabeordner)):
            raise ValueError(
                "Ausgabewurzel darf Quellverzeichnisse weder enthalten "
                "noch darin liegen")
    if ausgabeordner.exists() and not ausgabeordner.is_dir():
        raise ValueError("Ausgabepfad ist kein Verzeichnis")

    konfig = konfig_lader.lade_konfig(str(konfigurationsordner))
    modelle = {}
    for name, eintrag in konfig.summenkoerper.items():
        if name.startswith("_"):
            continue
        modell_id = _slug(name)
        if modell_id in modelle:
            raise ValueError("Modell-ID kollidiert nach Normalisierung: %s"
                             % modell_id)
        modelle[modell_id] = (name, eintrag)
    if not modelle:
        raise ValueError("Legacy-Konfiguration enthält keine Modelle")

    vorhandene_ziele = [
        str(ausgabeordner / modell_id)
        for modell_id in modelle
        if (ausgabeordner / modell_id).exists()
    ]
    if vorhandene_ziele:
        raise ValueError(
            "Zielpaket(e) existieren bereits; nichts wird überschrieben: %s"
            % ", ".join(vorhandene_ziele))

    bericht = {
        "status": "validiert_nur_vorschau",
        "quellen": {
            "konfiguration": str(konfigurationsordner),
            "geometrien": str(geometriewurzel),
        },
        "ziel": str(ausgabeordner),
        "anwenden": bool(anwenden),
        "obj_zu_m": OBJ_ZU_M,
        "obj_achsenmatrix_zu_blatt": [
            list(zeile) for zeile in OBJ_ACHSMATRIX],
        "rollenregel": (
            "allgemein, wenn die Legacy-Quelle keine Rolle definiert"),
        "modelle": [],
        "fehler": [],
    }
    temp_elternordner = None
    if anwenden:
        ausgabeordner.parent.mkdir(parents=True, exist_ok=True)
        temp_elternordner = ausgabeordner.parent
    with tempfile.TemporaryDirectory(
            prefix="segelphysik-migration-",
            dir=temp_elternordner) as temporaer:
        staging = Path(temporaer)
        for modell_id, (name, eintrag) in modelle.items():
            paketwurzel = staging / modell_id
            try:
                zaehler = _paket_erstellen(
                    modell_id, name, eintrag, geometriewurzel, paketwurzel,
                    konfig.materialien_blocks)
                bericht["modelle"].append({
                    "id": modell_id,
                    "name": name,
                    "blätter": zaehler["blaetter"],
                    "obj_dateien": zaehler["obj_dateien"],
                    "validierung": "bestanden",
                })
            except (OSError, ValueError, konfig_lader.KonfigFehler) as fehler:
                bericht["fehler"].append("%s: %s" % (name, fehler))
        if bericht["fehler"]:
            bericht["status"] = "fehlgeschlagen"
            raise MigrationFehler(bericht)
        if not anwenden:
            return bericht
        ausgabeordner.mkdir(parents=True, exist_ok=True)
        for modell_id in modelle:
            ziel = ausgabeordner / modell_id
            if ziel.exists():
                bericht["fehler"].append(
                    "Ziel wurde zwischenzeitlich angelegt: %s" % ziel)
                bericht["status"] = "fehlgeschlagen"
                raise MigrationFehler(bericht)
        for modell_id in modelle:
            paketwurzel = staging / modell_id
            paketwurzel.rename(ausgabeordner / modell_id)
        bericht["status"] = "angewendet"
        bericht["ziel_erfolgreich"] = [
            str(ausgabeordner / modell_id) for modell_id in modelle]
        return bericht


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Validiert Legacy-Modelle als Modellpakete. Ohne --anwenden "
            "werden keine Zielpakete geschrieben."))
    parser.add_argument(
        "--konfiguration", required=True,
        help="Ordner mit koerper.json und materialien.json")
    parser.add_argument(
        "--geometrien", required=True,
        help="Ordner mit <Blattname>.obj Dateien")
    parser.add_argument(
        "--ausgabe", required=True,
        help="Zielordner, in dem je Modell ein Paket angelegt wird")
    parser.add_argument(
        "--anwenden", action="store_true",
        help="Pakete nach erfolgreicher Vorschau-Validierung schreiben")
    args = parser.parse_args(argv)
    try:
        bericht = migriere(
            args.konfiguration, args.geometrien, args.ausgabe,
            anwenden=args.anwenden)
    except MigrationFehler as fehler:
        bericht = fehler.bericht
        print(json.dumps(bericht, ensure_ascii=False, indent=2))
        return 1
    except (OSError, ValueError, konfig_lader.KonfigFehler) as fehler:
        print(json.dumps({
            "status": "fehlgeschlagen",
            "fehler": [str(fehler)],
        }, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(bericht, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
