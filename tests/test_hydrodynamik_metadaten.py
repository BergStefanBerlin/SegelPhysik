import json

import pytest

from segelphysik.core.hydrodynamik_metadaten import (
    GeometriemetadatenFehler,
    erzeuge_geometriemetadaten,
    pruefe_geometriemetadaten,
    schreibe_geometriemetadaten,
)
from segelphysik.core.modell_lader import lade_modellpaket


def _manifest(modell_id="beispiel", dx=2.0, geometrie=None):
    if geometrie is None:
        geometrie = {
            "quelle": "form",
            "parameter": {
                "typ": "box",
                "dx_m": dx,
                "dy_m": 1.0,
                "dz_m": 0.5,
            },
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
            "id": "rumpf",
            "name": "Rumpf",
            "geometrie": geometrie,
            "dichte_kg_pro_m3": 750,
            "verdrängend": True,
            "rolle": "rumpf",
        },
    }


def _paket(tmp_path, daten):
    paket = tmp_path / daten["modell"]["id"]
    paket.mkdir()
    (paket / "modell.json").write_text(
        json.dumps(daten), encoding="utf-8")
    return paket


def test_erzeugung_ist_deterministisch_und_schreibt_nicht(tmp_path):
    paket = _paket(tmp_path, _manifest())
    erstes = erzeuge_geometriemetadaten(paket, {})
    zweites = erzeuge_geometriemetadaten(paket, {})

    assert erstes == zweites
    assert not (paket / "hydrodynamik").exists()
    teil = erstes["parts"][0]
    assert teil["geometry"]["surface_area_m2"]["value"] == pytest.approx(7.0)
    assert teil["geometry"]["volume_m3"]["value"] == pytest.approx(1.0)
    assert teil["geometry"]["profile_sections"]["classification"] == "unklar"
    assert len(teil["source"]["sha256"]) == 64
    assert len(teil["canonical_mesh_sha256"]) == 64


def test_sidecar_wird_geprueft_und_nie_ueberschrieben(tmp_path):
    paket = _paket(tmp_path, _manifest())
    sidecar = schreibe_geometriemetadaten(paket, {})
    vorher = sidecar.read_bytes()

    assert pruefe_geometriemetadaten(paket, {}) == json.loads(
        vorher.decode("utf-8"))
    with pytest.raises(GeometriemetadatenFehler, match="nicht ueberschrieben"):
        schreibe_geometriemetadaten(paket, {})
    assert sidecar.read_bytes() == vorher


def test_pruefung_erkennt_geaenderte_manifestgeometrie(tmp_path):
    paket = _paket(tmp_path, _manifest())
    sidecar = schreibe_geometriemetadaten(paket, {})
    manifest_pfad = paket / "modell.json"
    manifest = json.loads(manifest_pfad.read_text(encoding="utf-8"))
    manifest["koerper"]["geometrie"]["parameter"]["dx_m"] = 3.0
    manifest_pfad.write_text(
        json.dumps(manifest), encoding="utf-8")

    with pytest.raises(GeometriemetadatenFehler, match="stimmt nicht"):
        pruefe_geometriemetadaten(paket, {})


def test_pruefung_erkennt_geaenderte_obj_quelle(tmp_path):
    geometrie = {"quelle": "obj", "datei": "rumpf.obj"}
    paket = _paket(tmp_path, _manifest(geometrie=geometrie))
    obj_pfad = paket / "rumpf.obj"
    obj_pfad.write_text(
        "v 0 0 0\n"
        "v 1 0 0\n"
        "v 0 1 0\n"
        "v 0 0 1\n"
        "f 1 3 2\n"
        "f 1 2 4\n"
        "f 1 4 3\n"
        "f 2 3 4\n",
        encoding="utf-8",
    )
    sidecar = schreibe_geometriemetadaten(paket, {})
    sidecar_bytes = sidecar.read_bytes()

    obj_pfad.write_text(
        obj_pfad.read_text(encoding="utf-8").replace(
            "v 1 0 0", "v 2 0 0"),
        encoding="utf-8",
    )
    with pytest.raises(GeometriemetadatenFehler, match="stimmt nicht"):
        pruefe_geometriemetadaten(paket, {})
    assert sidecar.read_bytes() == sidecar_bytes


def test_loader_bleibt_read_only_und_sidecarfehler_sind_explizit(tmp_path):
    paket = _paket(tmp_path, _manifest())
    lade_modellpaket(paket, {})
    assert not (paket / "hydrodynamik").exists()

    with pytest.raises(GeometriemetadatenFehler, match="Sidecar fehlt"):
        pruefe_geometriemetadaten(paket, {})

    sidecar = schreibe_geometriemetadaten(paket, {})
    sidecar_bytes = sidecar.read_bytes()
    lade_modellpaket(paket, {})
    assert sidecar.read_bytes() == sidecar_bytes


def test_atomarer_schreibfehler_hinterlaesst_keine_teildatei(
        tmp_path, monkeypatch):
    paket = _paket(tmp_path, _manifest())

    def fehler(*_args, **_kwargs):
        raise OSError("simulierter Linkfehler")

    monkeypatch.setattr(
        "segelphysik.core.hydrodynamik_metadaten.os.link", fehler)
    with pytest.raises(GeometriemetadatenFehler, match="atomar"):
        schreibe_geometriemetadaten(paket, {})
    ordner = paket / "hydrodynamik"
    assert not (ordner / "geometrie_metadaten.json").exists()
    assert list(ordner.iterdir()) == []


def test_ungueltige_geometrie_wird_nicht_metadatenisiert(tmp_path):
    daten = _manifest()
    daten["koerper"]["geometrie"]["parameter"]["dx_m"] = float("nan")
    paket = _paket(tmp_path, daten)

    with pytest.raises(GeometriemetadatenFehler, match="analysiert werden"):
        erzeuge_geometriemetadaten(paket, {})
