import json
from pathlib import Path

import numpy as np
import pytest

from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.fabriken import baue_modellpaket, baue_summenkoerper
from segelphysik.core.koerper import Koerper
from segelphysik.core.dynamik_6dof import Zustand6DOF
from segelphysik.core.modell_lader import (
    ModellFehler,
    lade_modellkatalog,
    lade_modellmanifest,
    lade_modellpaket,
)


def _manifest(modell_id="beispiel", geometrie=None):
    if geometrie is None:
        geometrie = {
            "quelle": "form",
            "parameter": {"typ": "box", "dx_m": 2, "dy_m": 1, "dz_m": 0.5},
        }
    return {
        "schema_version": "1.0",
        "modell": {"id": modell_id, "name": "Beispielmodell"},
        "geometrie_einheiten": {
            "obj_zu_m": 1.0,
            "obj_achsenmatrix_zu_blatt": [
                [1, 0, 0], [0, 1, 0], [0, 0, 1],
            ],
        },
        "koerper": {
            "id": "root",
            "name": "Wurzel",
            "geometrie": geometrie,
            "dichte_kg_pro_m3": 750,
            "farbe": "#abc",
            "verdrängend": True,
            "rolle": "allgemein",
        },
    }


def _paket(tmp_path, daten, modell_id="beispiel"):
    paket = tmp_path / modell_id
    paket.mkdir()
    (paket / "modell.json").write_text(
        json.dumps(daten), encoding="utf-8")
    return paket


def test_manifest_und_paket_laden_form_mesh_und_neutralrolle(tmp_path):
    paket = _paket(tmp_path, _manifest())

    manifest = lade_modellmanifest(paket, {})
    geladen = lade_modellpaket(paket, {})

    assert manifest.id == "beispiel"
    assert manifest.koerper.rolle == "allgemein"
    assert geladen.meshes["root"].frame == "blatt"
    assert geladen.meshes["root"].punkte_si.shape == (8, 3)
    assert not geladen.meshes["root"].punkte_si.flags.writeable


def test_modellfabrik_uebernimmt_basispose_des_blattes(tmp_path):
    daten = _manifest()
    blatt = daten["koerper"]
    blatt["pose"] = {
        "translation_m": [1.0, 2.0, 3.0],
        "rotation_quaternion_wxyz": [
            2.0 ** -0.5, 2.0 ** -0.5, 0.0, 0.0],
    }
    daten["koerper"] = {
        "id": "gruppe",
        "name": "Gruppe",
        "pose": {
            "translation_m": [4.0, 5.0, 6.0],
            "rotation_quaternion_wxyz": [
                2.0 ** -0.5, 0.0, 0.0, 2.0 ** -0.5],
        },
        "teile": [blatt],
    }
    paket = _paket(tmp_path, daten)

    koerper, versatz = baue_modellpaket(
        lade_konfig(Path(__file__).resolve().parents[1] / "konfigurationen"),
        paket)

    np.testing.assert_allclose(versatz, [2.0, 6.0, 9.0], atol=1e-12)
    assert isinstance(koerper.zustand, Zustand6DOF)
    assert koerper.basis_pose.translation_m == (4.0, 5.0, 6.0)
    kind, _pose = koerper.teile[0]
    assert kind.zustand is None
    assert kind.basis_pose.translation_m == (1.0, 2.0, 3.0)
    assert kind.basis_pose.rotation_quaternion_wxyz == pytest.approx(
        (2.0 ** -0.5, 2.0 ** -0.5, 0.0, 0.0))
    assert koerper.traegheitstensor[1, 1] != pytest.approx(
        koerper.traegheitstensor[2, 2])


def test_gelenkpose_aendert_darstellung_aber_nicht_masse_oder_auftrieb(
        tmp_path):
    daten = _manifest()
    beweglich = daten["koerper"]
    beweglich["id"] = "arm"
    beweglich["pose"] = {
        "translation_m": [1.0, 0.0, 0.0],
        "rotation_quaternion_wxyz": [1.0, 0.0, 0.0, 0.0],
    }
    beweglich["gelenk"] = {
        "eltern_id": "root",
        "achse_eltern": [0.0, 0.0, 4.0],
        "winkel_rad": 0.0,
    }
    daten["koerper"] = {
        "id": "root",
        "name": "Wurzel",
        "teile": [beweglich],
    }
    paket = _paket(tmp_path, daten)
    konfig = lade_konfig(
        Path(__file__).resolve().parents[1] / "konfigurationen")
    manifest = lade_modellmanifest(paket, konfig.materialien_blocks)
    koerper, _ = baue_modellpaket(konfig, paket)
    from segelphysik.grafik_bruecke import _farbgruppen

    arm = koerper.teile[0][0]
    masse = koerper.masse
    schwerpunkt = koerper._r_eingabe.copy()
    traegheit = koerper.traegheitstensor.copy()
    auftriebsmesh = koerper.punkte.copy()
    darstellung_start = _farbgruppen(koerper)[0]["punkte"]
    zustand = koerper.snapshot()

    assert manifest.koerper.teile[0].gelenk.achse_eltern == (
        0.0, 0.0, 1.0)
    assert zustand.gelenkzustaende[0].winkel_rad == 0.0
    koerper.gelenkwinkel_setzen("arm", np.pi / 2)

    np.testing.assert_allclose(koerper.masse, masse)
    np.testing.assert_allclose(koerper._r_eingabe, schwerpunkt)
    np.testing.assert_allclose(koerper.traegheitstensor, traegheit)
    np.testing.assert_allclose(koerper.punkte, auftriebsmesh)
    assert not np.allclose(
        _farbgruppen(koerper)[0]["punkte"], darstellung_start)
    assert arm.gelenkwinkel_rad == pytest.approx(np.pi / 2)
    assert koerper.snapshot().gelenkzustaende[0].winkel_rad == pytest.approx(
        np.pi / 2)

    from segelphysik.grafik_bruecke import GrafikBruecke
    bridge = GrafikBruecke.__new__(GrafikBruecke)
    gruppe = _farbgruppen(koerper)[0]
    gruppe["pd"] = {"referenz_punkte": gruppe["punkte"].copy()}
    bridge._koerper = {
        "beispiel": {"koerper": koerper, "gruppen": [gruppe]},
    }
    bridge._statisch_anwenden = lambda *_args: None
    assert bridge.gelenkwinkel_setzen("beispiel", "arm", 0.0)
    np.testing.assert_allclose(
        gruppe["pd"]["referenz_punkte"],
        _farbgruppen(koerper)[0]["punkte"])


def test_gelenk_erfordert_direkte_gueltige_elternreferenz(tmp_path):
    daten = _manifest()
    blatt = daten["koerper"]
    blatt["id"] = "arm"
    blatt["gelenk"] = {
        "eltern_id": "fremde_gruppe",
        "achse_eltern": [0.0, 0.0, 1.0],
        "winkel_rad": 0.0,
    }
    daten["koerper"] = {
        "id": "root",
        "name": "Wurzel",
        "teile": [blatt],
    }
    paket = _paket(tmp_path, daten)
    konfig = lade_konfig(
        Path(__file__).resolve().parents[1] / "konfigurationen")

    with pytest.raises(ModellFehler, match="direkten Elternknoten"):
        lade_modellmanifest(paket, konfig.materialien_blocks)


def test_manifest_ist_unveraenderlich_und_katalog_braucht_absoluten_pfad(
        tmp_path, monkeypatch):
    paket = _paket(tmp_path, _manifest())
    anderer_ort = tmp_path / "cwd"
    anderer_ort.mkdir()
    monkeypatch.chdir(anderer_ort)

    katalog = lade_modellkatalog(tmp_path, {})

    assert [manifest.id for manifest in katalog] == ["beispiel"]
    with pytest.raises((AttributeError, TypeError)):
        katalog[0].koerper.name = "geändert"
    with pytest.raises(ModellFehler, match="absolut"):
        lade_modellkatalog(".", {})
    with pytest.raises(ModellFehler, match="absolut"):
        lade_modellmanifest("beispiel", {})
    assert paket.is_dir()


@pytest.mark.parametrize(
    "aenderung,fehler",
    [
        (lambda d: d.update({"unbekannt": True}), "unbekannte Felder"),
        (lambda d: d.update({"schema_version": "2.0"}), "schema_version"),
        (lambda d: d["modell"].update({"id": "Ungültig"}), "Slug"),
        (lambda d: d["modell"].update({"id": "anderes"}), "Paketordner"),
    ],
)
def test_manifest_lehnt_abweichende_vertraege_ab(
        tmp_path, aenderung, fehler):
    daten = _manifest()
    aenderung(daten)
    paket = _paket(tmp_path, daten)
    materialien = {"GfK": {}}

    with pytest.raises(ModellFehler, match=fehler):
        lade_modellmanifest(paket, materialien)


def test_manifest_vererbt_rolle_und_erkennt_doppelte_knoten_ids(tmp_path):
    daten = _manifest()
    daten["koerper"] = {
        "id": "root",
        "name": "Wurzel",
        "rolle_default": "allgemein",
        "teile": [{
            "id": "root",
            "name": "Kind",
            "geometrie": {
                "quelle": "form",
                "parameter": {
                    "typ": "box", "dx_m": 1, "dy_m": 1, "dz_m": 1,
                },
            },
            "dichte_kg_pro_m3": 1000,
            "verdrängend": True,
        }],
    }
    paket = _paket(tmp_path, daten)

    with pytest.raises(ModellFehler, match="doppelte Knoten-ID"):
        lade_modellmanifest(paket, {})


def test_materialblatt_darf_keine_farb_overrides_haben(tmp_path):
    daten = _manifest()
    blatt = daten["koerper"]
    blatt.pop("dichte_kg_pro_m3")
    blatt.pop("farbe")
    blatt["material"] = "GfK"
    blatt["farbe"] = "#123456"
    paket = _paket(tmp_path, daten)

    with pytest.raises(ModellFehler, match="Farb-Overrides"):
        lade_modellmanifest(paket, {"GfK": {}})


@pytest.mark.parametrize(
    "felder,entfernen,fehler",
    [
        ({"material": "fehlend"}, ("dichte_kg_pro_m3",), "unbekanntes Material"),
        ({"material": "GfK"}, (), "genau eines"),
        ({"pose": {
            "translation_m": [0, 0, 0],
            "rotation_quaternion_wxyz": [2, 0, 0, 0],
        }}, (), "normiert"),
        ({"farbe_unter_wasser": "nicht-hex"}, (), "Hex-Farbe"),
        ({"rolle": "unbekannt"}, (), "unbekannte Rolle"),
        ({"verdrängend": 1}, (), "boolescher Wert"),
    ],
)
def test_manifest_prueft_blattfelder_und_materialbezug(
        tmp_path, felder, entfernen, fehler):
    daten = _manifest()
    for feld in entfernen:
        daten["koerper"].pop(feld)
    daten["koerper"].update(felder)
    paket = _paket(tmp_path, daten)

    with pytest.raises(ModellFehler, match=fehler):
        lade_modellmanifest(paket, {})


def test_manifest_lehnt_traversal_und_fehlerhafte_formparameter_ab(tmp_path):
    ausserhalb = tmp_path / "ausserhalb.obj"
    ausserhalb.write_text("mesh", encoding="utf-8")
    daten = _manifest(geometrie={
        "quelle": "obj", "datei": "../ausserhalb.obj",
    })
    paket = _paket(tmp_path, daten)
    with pytest.raises(ModellFehler, match="Traversal"):
        lade_modellmanifest(paket, {})

    daten = _manifest()
    daten["koerper"]["geometrie"]["parameter"]["fremd"] = 1
    paket2 = _paket(tmp_path, daten, "falsche_form")
    daten["modell"]["id"] = "falsche_form"
    (paket2 / "modell.json").write_text(
        json.dumps(daten), encoding="utf-8")
    with pytest.raises(ModellFehler, match="unbekannte Formparameter"):
        lade_modellmanifest(paket2, {})


def test_katalog_parst_keine_meshes_aber_vollpaket_meldet_knotenfehler(
        tmp_path):
    paket = tmp_path / "objmodell"
    (paket / "mesh").mkdir(parents=True)
    (paket / "mesh" / "kaputt.obj").write_text(
        "keine gültige OBJ-Geometrie\n", encoding="utf-8")
    daten = _manifest(
        "objmodell",
        {"quelle": "obj", "datei": "mesh/kaputt.obj"},
    )
    daten["modell"]["id"] = "objmodell"
    (paket / "modell.json").write_text(json.dumps(daten), encoding="utf-8")

    assert [m.id for m in lade_modellkatalog(tmp_path, {})] == ["objmodell"]
    with pytest.raises(ModellFehler, match="objmodell/root"):
        lade_modellpaket(paket, {})


def test_doppelte_json_schluessel_sind_manifestfehler(tmp_path):
    paket = tmp_path / "beispiel"
    paket.mkdir()
    (paket / "modell.json").write_text(
        '{"schema_version":"1.0","schema_version":"1.0"}',
        encoding="utf-8",
    )

    with pytest.raises(ModellFehler, match="Doppelter JSON-Schlüssel"):
        lade_modellmanifest(paket, {})


def test_maschinenlesbare_modellvorlage_ist_gueltig(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    vorlage = json.loads(
        (repo / "doc" / "Vorlagen" / "modell_vorlage.json")
        .read_text(encoding="utf-8"))
    paket = _paket(tmp_path, vorlage)

    geladen = lade_modellpaket(paket, {"GfK": {}})

    assert geladen.manifest.id == "beispiel"
    assert len(geladen.meshes) == 1


def test_vollstaendiger_bestandskatalog_und_formpakete_laden():
    wurzel = Path(__file__).resolve().parents[1]
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    katalog = lade_modellkatalog(
        wurzel / "segelphysik" / "modelle",
        konfiguration.materialien_blocks,
    )
    ids = {manifest.id for manifest in katalog}
    bestand = {
        name for name in konfiguration.summenkoerper
        if not name.startswith("_")
    }

    assert ids == bestand
    for manifest in katalog:
        paket = lade_modellpaket(
            manifest.paketwurzel,
            konfiguration.materialien_blocks,
        )
        assert len(paket.meshes) == (10 if manifest.id == "yacht1" else 1)


def test_bestandsmodelle_stimmen_mit_phase3_goldenwerten_ueberein():
    wurzel = Path(__file__).resolve().parents[1]
    golden_pfad = (
        wurzel / "doc" / "WegZuV1.0" / "Revisionslog" / "zuV0.5"
        / "Inventar_Phase3.json")
    golden = json.loads(golden_pfad.read_text(encoding="utf-8"))
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    materialien = konfiguration.materialien_blocks
    katalog = {
        manifest.id: manifest
        for manifest in lade_modellkatalog(
            wurzel / "segelphysik" / "modelle", materialien)
    }

    for modell_id, erwartung in golden["modelle"].items():
        legacy, offset = baue_summenkoerper(
            konfiguration, modell_id,
            eintrag=konfiguration.summenkoerper[modell_id])
        assert legacy.masse == pytest.approx(erwartung["masse_kg"], rel=1e-12)
        np.testing.assert_allclose(
            legacy.traegheitstensor,
            erwartung["traegheit_kg_m2"],
            rtol=1e-12,
            atol=1e-20,
        )
        assert legacy.verdrangend is erwartung["verdraengend"]
        assert len(legacy.punkte) == erwartung["punkte"]
        assert len(legacy.dreiecke) == erwartung["dreiecke"]
        if offset is not None:
            np.testing.assert_allclose(
                offset, erwartung["initialer_modellversatz_m"],
                rtol=1e-12, atol=1e-14)
        else:
            assert erwartung.get("initialer_modellversatz_m") is None

        manifest = katalog[modell_id]
        kanonisch, paket_offset = baue_modellpaket(
            konfiguration, manifest.paketwurzel)
        assert kanonisch.masse == pytest.approx(
            erwartung["masse_kg"], rel=1e-12)
        np.testing.assert_allclose(
            kanonisch.traegheitstensor,
            erwartung["traegheit_kg_m2"],
            rtol=1e-12,
            atol=1e-20,
        )
        if offset is not None:
            np.testing.assert_allclose(
                paket_offset,
                erwartung["initialer_modellversatz_m"],
                rtol=1e-12,
                atol=1e-14,
            )
        else:
            assert paket_offset is None
        if modell_id == "yacht1":
            assert len(kanonisch.dreiecke) == erwartung["paket_dreiecke"]
            blaetter = []

            def sammle(knoten):
                if knoten.teile:
                    for kind, _pose in knoten.teile:
                        sammle(kind)
                else:
                    blaetter.append(knoten)

            sammle(kanonisch)
            assert {blatt.knoten_id for blatt in blaetter} == {
                "rumpf", "ruder", "kiel", "bulb", "mast",
                "mast_teil_01", "mast_teil_02", "boom",
                "grosssegel", "fock",
            }
            assert all(blatt.mesh is not None for blatt in blaetter)
            assert all(blatt.massendefinition is not None
                       for blatt in blaetter)
