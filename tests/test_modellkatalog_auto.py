from pathlib import Path

import pytest

from segelphysik.core import boot_bau
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.modell_lader import ModellFehler
from segelphysik.gui.baum import finde, welt_aus_konfig


def _blaetter(koerper):
    if not koerper.teile:
        return [koerper]
    return [
        blatt
        for kind, _pose in koerper.teile
        for blatt in _blaetter(kind)
    ]


def test_modellpaket_aus_ordner_ohne_koerper_json_eintrag():
    wurzel = Path(__file__).resolve().parents[1]
    konfig = lade_konfig(wurzel / "konfigurationen")

    assert "optimist" not in konfig.summenkoerper

    welt = welt_aus_konfig(konfig)
    optimist = finde(welt, "optimist")
    assert optimist is not None
    assert finde(welt, "rumpf").label == "Rumpf"
    assert finde(welt, "schwert").label == "Schwert"
    ruder = finde(welt, "ruderanlage")
    assert ruder is not None
    assert ruder.label == "Ruder"
    assert {kind.label for kind in ruder.kinder} == {
        "Ruderblatt", "Pinne", "Pinnenausleger", "Gummigelenk",
    }
    assert {blatt.id for blatt in optimist.blaetter()} == {
        "rumpf", "schwert", "ruder", "pinne", "pinneverlaengerung",
        "mast", "baum", "spriet", "segel", "gummigelenk", "segler",
    }

    koerper, _ = baue_summenkoerper(konfig, "optimist")
    assert koerper.masse > 0.0
    assert {blatt._name for blatt in _blaetter(koerper)} == {
        "rumpf", "schwert", "ruder", "pinne", "pinneverlaengerung",
        "mast", "baum", "spriet", "segel", "gummigelenk", "segler",
    }


def test_paketkatalog_und_fabrik_unabhaengig_vom_arbeitsverzeichnis(
        tmp_path, monkeypatch):
    wurzel = Path(__file__).resolve().parents[1]
    konfig = lade_konfig(wurzel / "konfigurationen")
    monkeypatch.chdir(tmp_path)

    welt = welt_aus_konfig(konfig)
    koerper, _ = baue_summenkoerper(konfig, "optimist")

    assert finde(welt, "optimist") is not None
    assert koerper.masse > 0.0


def test_neues_paket_ohne_legacyeintrag_hat_funktionierende_gui_overrides(
        monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui.baum_widget import BaumWidget
    from segelphysik.core.segler_einstellungen import SeglerEinstellungen

    app = QApplication.instance() or QApplication([])
    wurzel = Path(__file__).resolve().parents[1]
    konfig = lade_konfig(wurzel / "konfigurationen")
    konfig.segler_einstellungen = SeglerEinstellungen()
    manifest_pfad = wurzel / "code" / "modelle" / "optimist" / "modell.json"
    vorher = manifest_pfad.read_bytes()
    welt = welt_aus_konfig(konfig)
    optimist = next(k for k in welt.kinder if k.name == "optimist")
    rumpf = next(k for k in optimist.blaetter() if k.id == "rumpf")
    alt, _ = baue_summenkoerper(konfig, "optimist")
    widget = BaumWidget()
    widget.lade(welt)
    widget._eigenschaft_setzen(rumpf, "Dichte", 2000.0)
    neu, _ = baue_summenkoerper(konfig, "optimist")
    alt_rumpf = next(k for k in _blaetter(alt) if k.knoten_id == "rumpf")
    neu_rumpf = next(k for k in _blaetter(neu) if k.knoten_id == "rumpf")
    assert neu_rumpf.masse == pytest.approx(alt_rumpf.masse * 2000 / 1900)
    assert konfig.paket_ueberschreibungen["optimist"]["rumpf"] == {
        "dichte_kg_pro_m3": 2000.0}
    assert manifest_pfad.read_bytes() == vorher
    widget.close()
    app.processEvents()


def test_paketkatalog_meldet_ungueltiges_manifest(
        tmp_path, monkeypatch):
    wurzel = Path(__file__).resolve().parents[1]
    konfig = lade_konfig(wurzel / "konfigurationen")
    paket = tmp_path / "kaputt"
    paket.mkdir()
    (paket / "modell.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(boot_bau, "MODELL_ORDNER", str(tmp_path))

    with pytest.raises(ModellFehler, match="JSON"):
        welt_aus_konfig(konfig)


def test_paketkatalog_meldet_fehlende_geometrie(
        tmp_path, monkeypatch):
    wurzel = Path(__file__).resolve().parents[1]
    konfig = lade_konfig(wurzel / "konfigurationen")
    paket = tmp_path / "folkeboot"
    paket.mkdir()
    (paket / "modell.json").write_text(
        (wurzel / "code" / "modelle" / "folkeboot" / "modell.json")
        .read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(boot_bau, "MODELL_ORDNER", str(tmp_path))

    with pytest.raises(ModellFehler, match="rumpf.obj"):
        welt_aus_konfig(konfig)


def test_paketkatalog_meldet_doppelte_ids_als_fehler(
        tmp_path, monkeypatch):
    from segelphysik.core import modell_lader

    wurzel = Path(__file__).resolve().parents[1]
    konfig = lade_konfig(wurzel / "konfigurationen")
    manifest = modell_lader.lade_modellmanifest(
        wurzel / "code" / "modelle" / "folkeboot",
        konfig.materialien_blocks)
    for name in ("erstes", "zweites"):
        paket = tmp_path / name
        paket.mkdir()
        (paket / "modell.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(boot_bau, "MODELL_ORDNER", str(tmp_path))
    monkeypatch.setattr(
        modell_lader, "lade_modellmanifest", lambda *_args: manifest)

    with pytest.raises(ModellFehler, match="Doppelte Modell-ID"):
        welt_aus_konfig(konfig)
