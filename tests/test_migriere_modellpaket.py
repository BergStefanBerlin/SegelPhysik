import json

import pytest

from segelphysik.core.modell_lader import lade_modellpaket
from werkzeuge.migriere_modellpaket import MigrationFehler, migriere


_TETRA_OBJ = """\
v 0 0 0
v 1 0 0
v 0 1 0
v 0 0 1
f 1 3 2
f 1 2 4
f 1 4 3
f 2 3 4
"""


def _legacy_daten(tmp_path):
    konfiguration = tmp_path / "legacy"
    geometrien = tmp_path / "obj"
    konfiguration.mkdir()
    geometrien.mkdir()
    (konfiguration / "materialien.json").write_text(
        json.dumps({
            "materialien": {
                "Stahl": {
                    "dichte_kg_pro_m3": 7800,
                    "farbe": "#777777",
                    "farbe_unter_wasser": "#555555",
                },
            },
            "wasser": {
                "dichten_kg_pro_m3": {"suss": 1000},
                "standard": "suss",
            },
        }),
        encoding="utf-8",
    )
    (konfiguration / "koerper.json").write_text(
        json.dumps({
            "summenkoerper": {
                "testmodell": {
                    "teile": [{"name": "rumpf", "material": "Stahl"}],
                },
                "formmodell": {
                    "form": {"typ": "box", "dx_m": 1, "dy_m": 1,
                             "dz_m": 1},
                    "dichte_kg_pro_m3": 500,
                    "farbe": "#ff0000",
                    "farbe_unter_wasser": "#aa0000",
                },
            },
            "darstellung": {
                "delta_helligkeit_unterwasser": 0.4,
                "farbe_standard": "#ffffff",
            },
        }),
        encoding="utf-8",
    )
    (geometrien / "rumpf.obj").write_text(_TETRA_OBJ, encoding="utf-8")
    return konfiguration, geometrien


def test_migration_dry_run_validiert_ohne_zielordner_anzulegen(tmp_path):
    konfiguration, geometrien = _legacy_daten(tmp_path)
    ausgabe = tmp_path / "pakete"

    bericht = migriere(konfiguration, geometrien, ausgabe)

    assert bericht["status"] == "validiert_nur_vorschau"
    assert [modell["id"] for modell in bericht["modelle"]] == [
        "testmodell", "formmodell"]
    assert not bericht["fehler"]
    assert not ausgabe.exists()


def test_migration_schreibt_validierte_pakete_ohne_zu_ueberschreiben(
        tmp_path):
    konfiguration, geometrien = _legacy_daten(tmp_path)
    ausgabe = tmp_path / "pakete"
    quellkonfiguration = (
        konfiguration / "koerper.json").read_bytes()
    quellmaterialien = (
        konfiguration / "materialien.json").read_bytes()
    quellmesh = (geometrien / "rumpf.obj").read_bytes()

    bericht = migriere(
        konfiguration, geometrien, ausgabe, anwenden=True)

    assert bericht["status"] == "angewendet"
    paketwurzel = ausgabe / "testmodell"
    manifest = json.loads(
        (paketwurzel / "modell.json").read_text(encoding="utf-8"))
    assert manifest["geometrie_einheiten"]["obj_zu_m"] == 0.25
    assert manifest["koerper"]["teile"][0]["rolle"] == "allgemein"
    assert manifest["koerper"]["teile"][0]["verdrängend"] is True
    assert (paketwurzel / "geometrie" / "rumpf" / "rumpf.obj").is_file()
    paket = lade_modellpaket(paketwurzel, {
        "Stahl": {
            "dichte_kg_pro_m3": 7800,
            "farbe": "#777777",
            "farbe_unter_wasser": "#555555",
        },
    })
    assert set(paket.meshes) == {"rumpf"}
    assert (konfiguration / "koerper.json").read_bytes() == quellkonfiguration
    assert (konfiguration / "materialien.json").read_bytes() == quellmaterialien
    assert (geometrien / "rumpf.obj").read_bytes() == quellmesh

    original = (paketwurzel / "modell.json").read_bytes()
    with pytest.raises(ValueError, match="nichts wird überschrieben"):
        migriere(konfiguration, geometrien, ausgabe, anwenden=True)
    assert (paketwurzel / "modell.json").read_bytes() == original


def test_migration_fehler_legt_keine_zielpakete_an(tmp_path):
    konfiguration, geometrien = _legacy_daten(tmp_path)
    (geometrien / "rumpf.obj").unlink()
    ausgabe = tmp_path / "pakete"

    with pytest.raises(MigrationFehler) as fehler:
        migriere(konfiguration, geometrien, ausgabe, anwenden=True)

    assert fehler.value.bericht["status"] == "fehlgeschlagen"
    assert "rumpf.obj" in fehler.value.bericht["fehler"][0]
    assert not ausgabe.exists()
