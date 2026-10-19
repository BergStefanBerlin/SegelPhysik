import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from segelphysik.core.fabriken import baue_modellpaket
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.koerper import Koerper, KoerperFehler
from segelphysik.core.modell_lader import lade_modellmanifest, ModellFehler
from segelphysik.core.segler_einstellungen import SeglerEinstellungen
from segelphysik.gui.baum import welt_aus_konfig
from segelphysik.gui.baum_widget import BaumWidget

ROOT = Path(__file__).resolve().parents[1]


def _konfig(tmp_path):
    konfig = lade_konfig(ROOT / "konfigurationen")
    konfig.segler_einstellungen = SeglerEinstellungen(tmp_path / "segler.json")
    return konfig


def _steiner(masse, position):
    r = np.asarray(position)
    return masse * ((r @ r) * np.eye(3) - np.outer(r, r))


@pytest.mark.parametrize("modell,masse,z", [
    ("optimist", 50.0, 0.45), ("folkeboot", 150.0, 0.85)])
@pytest.mark.parametrize("achse", range(3))
def test_segler_masse_schwerpunkt_traegheit_ohne_verdrangung(
        tmp_path, modell, masse, z, achse):
    konfig = _konfig(tmp_path)
    paket = ROOT / "code" / "modelle" / modell
    manifest = lade_modellmanifest(paket, konfig.materialien_blocks)
    # Die Ruder-Untergruppe enthält weitere Blätter.
    def blaetter(k):
        return [k.id] if not k.teile else [
            i for kind in k.teile for i in blaetter(kind)]
    ids = set(blaetter(manifest.koerper)) - {"segler"}
    boot, _ = baue_modellpaket(konfig, paket, aktive_blaetter=ids)

    for delta_masse in (0.0, 10.0):
        position = np.array([0.0, 0.0, z])
        position[achse] += 0.2
        m = masse + delta_masse
        konfig.segler_einstellungen.setzen(modell, {
            "masse_kg": m, "position_rumpf_m": position.tolist()})
        gesamt, _ = baue_modellpaket(konfig, paket)
        r = np.asarray(manifest.rumpfreferenz_m) + position
        erwartetes_r = (boot.masse * boot._r_eingabe + m * r) / (boot.masse + m)
        np.testing.assert_allclose(gesamt._r_eingabe, erwartetes_r, atol=1e-12)
        assert gesamt.masse == pytest.approx(boot.masse + m)
        np.testing.assert_allclose(
            gesamt.traegheitstensor,
            boot.traegheitstensor
            + _steiner(boot.masse, boot._r_eingabe - erwartetes_r)
            + _steiner(m, r - erwartetes_r), atol=1e-9)
        assert len(gesamt.snapshot().blatt_meshes) == len(boot.snapshot().blatt_meshes)
        segler = next(k for k, _ in gesamt.teile if k.knoten_id == "segler")
        assert segler.zustand is None
        assert not segler.verdrangend
        assert segler.punkte.shape == segler.dreiecke.shape == (0, 3)
        np.testing.assert_array_equal(segler.traegheitstensor, np.zeros((3, 3)))
        # Im gemeinsamen Modellframe sind auch die Auftriebsmeshes identisch.
        for (p, f), (p0, f0) in zip(
                gesamt.snapshot().blatt_meshes, boot.snapshot().blatt_meshes):
            np.testing.assert_allclose(
                p + gesamt._r_eingabe, p0 + boot._r_eingabe, atol=1e-12)
            np.testing.assert_array_equal(f, f0)


def test_segler_gui_speichert_alle_koordinaten_und_neuladen(tmp_path):
    app = QApplication.instance() or QApplication([])
    konfig = _konfig(tmp_path)
    welt = welt_aus_konfig(konfig)
    optimist = next(k for k in welt.kinder if k.name == "optimist")
    segler = next(k for k in optimist.blaetter() if k.id == "segler")
    widget = BaumWidget()
    widget.lade(welt)
    signale = []
    widget.laufzeit_aenderung.connect(signale.append)
    for feld, wert in [
            ("Masse", 55.0), ("Position x", -0.2),
            ("Position y", 0.3), ("Position z", 0.6)]:
        widget._eigenschaft_setzen(segler, feld, wert)
    assert signale == ["eigenschaft"] * 4
    neu = _konfig(tmp_path)
    gespeicherte_werte = neu.segler_einstellungen.werte("optimist", 1, (0, 0, 0))
    assert gespeicherte_werte == {
        "masse_kg": 55.0, "position_rumpf_m": [-0.2, 0.3, 0.6]}
    boot, _ = baue_modellpaket(neu, ROOT / "code" / "modelle" / "optimist")
    kind, _pose = next((k, p) for k, p in boot.teile if k.knoten_id == "segler")
    assert kind.masse == 55.0
    np.testing.assert_allclose(
        kind.basis_pose.translation_m, [-0.2, 0.3, -1.435812 + 0.6])
    widget.close()
    app.processEvents()


def test_echter_gui_moduswechsel_uebergibt_segler_an_beide_worker(
        tmp_path, monkeypatch):
    from PySide6.QtCore import QThreadPool
    from segelphysik.gui.baum import sichtbarkeit_setzen
    from segelphysik.gui.hauptfenster import HauptFenster

    app = QApplication.instance() or QApplication([])
    konfig = _konfig(tmp_path)
    konfig.segler_einstellungen.setzen("optimist", {
        "masse_kg": 61, "position_rumpf_m": [-.1, .2, .55]})
    welt = welt_aus_konfig(konfig)
    sichtbarkeit_setzen(welt, "optimist")
    boot, _ = baue_modellpaket(konfig, ROOT / "code" / "modelle" / "optimist")
    fenster = HauptFenster()
    fenster.baum_setzen(welt)

    class Bruecke:
        def physik_basis_position_ermitteln(self, name):
            return np.zeros(3)
        def physik_pose_6dof_setzen(self, *args):
            return True
        def statische_pose_loeschen(self, name):
            return True
        def layer_ist_an(self, layer):
            return False
        def render(self):
            return True

    fenster._bruecke = Bruecke()
    fenster._laufzeit_koerper["optimist"] = boot
    aufgaben = []
    monkeypatch.setattr(QThreadPool, "start", lambda self, task: aufgaben.append(task))
    fenster._btn_echtzeit.click()
    fenster._echtzeit_timer.stop()
    fenster._echtzeit_render_timer.stop()
    assert fenster._echtzeit_zustand is not None
    fenster._echtzeit_akkumulator = .004
    fenster._echtzeit_takt()
    assert len(aufgaben) == 1
    assert aufgaben[-1].koerper.masse == boot.masse
    np.testing.assert_array_equal(
        aufgaben[-1].koerper.traegheitstensor, boot.traegheitstensor)
    fenster._btn_statisch.click()
    assert len(aufgaben) == 2
    assert aufgaben[-1].koerper.masse == boot.masse
    np.testing.assert_array_equal(
        aufgaben[-1].koerper.traegheitstensor, boot.traegheitstensor)
    fenster._btn_echtzeit.click()
    fenster._zeit_pausieren()
    segler = next(k for k, _ in boot.teile if k.knoten_id == "segler")
    assert segler.masse == 61
    np.testing.assert_allclose(
        segler.basis_pose.translation_m, [-.1, .2, -1.435812 + .55])
    assert segler.zustand is None
    assert konfig.segler_einstellungen.werte("optimist", 1, (0, 0, 0)) == {
        "masse_kg": 61, "position_rumpf_m": [-.1, .2, .55]}
    fenster.close()
    app.processEvents()


@pytest.mark.parametrize("wert", [0, -1, float("nan"), float("inf"), True, "50"])
def test_ungueltige_seglerwerte_veraendern_datei_nicht(tmp_path, wert):
    einstellungen = SeglerEinstellungen(tmp_path / "segler.json")
    gut = {"masse_kg": 50, "position_rumpf_m": [0, 0, 0.45]}
    einstellungen.setzen("optimist", gut)
    vorher = einstellungen.pfad.read_bytes()
    with pytest.raises(ValueError):
        einstellungen.setzen("optimist", dict(gut, masse_kg=wert))
    assert einstellungen.pfad.read_bytes() == vorher
    assert einstellungen.werte("optimist", 1, (0, 0, 0)) == gut


def test_segler_schreibfehler_keine_scheinbare_speicherung(tmp_path, monkeypatch):
    einstellungen = SeglerEinstellungen(tmp_path / "segler.json")
    def fehler(*args):
        raise PermissionError("Test Schreibschutz")
    monkeypatch.setattr(os, "replace", fehler)
    with pytest.raises(ValueError, match="nicht gespeichert"):
        einstellungen.setzen("optimist", {
            "masse_kg": 50, "position_rumpf_m": [0, 0, 0.45]})
    assert not einstellungen.pfad.exists()
    assert list(tmp_path.iterdir()) == []


def test_gui_schreibfehler_laesst_baum_und_masseneinstellungen_unveraendert(
        tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    konfig = _konfig(tmp_path)
    welt = welt_aus_konfig(konfig)
    optimist = next(k for k in welt.kinder if k.name == "optimist")
    segler = next(k for k in optimist.blaetter() if k.id == "segler")
    widget = BaumWidget()
    widget.lade(welt)
    vorher = dict(segler.eintrag)
    vorher_eigenschaften = list(segler.eigenschaften)
    signale = []
    widget.laufzeit_aenderung.connect(signale.append)
    def fehler(*args):
        raise PermissionError("Test Schreibschutz")
    monkeypatch.setattr(os, "replace", fehler)
    with pytest.raises(ValueError, match="nicht gespeichert"):
        widget._eigenschaft_setzen(segler, "Position y", .4)
    assert segler.eintrag == vorher
    assert segler.eigenschaften == vorher_eigenschaften
    assert signale == []
    assert not konfig.segler_einstellungen.pfad.exists()
    widget.close()
    app.processEvents()


@pytest.mark.parametrize("position", [
    [0, 0], [0, 0, float("inf")], [0, True, 0], ["0", 0, 0], None])
def test_segler_position_wird_strikt_validiert(tmp_path, position):
    einstellungen = SeglerEinstellungen(tmp_path / "segler.json")
    with pytest.raises(ValueError):
        einstellungen.setzen("optimist", {
            "masse_kg": 50, "position_rumpf_m": position})
    assert not einstellungen.pfad.exists()


def test_beschaedigte_seglerdatei_wird_nicht_still_ersetzt(tmp_path):
    pfad = tmp_path / "segler.json"
    pfad.write_text('{"schema_version":"9.0","modelle":{}}', encoding="utf-8")
    vorher = pfad.read_bytes()
    with pytest.raises(ValueError, match="Schema"):
        SeglerEinstellungen(pfad)
    assert pfad.read_bytes() == vorher


def test_doppelte_json_schluessel_werden_nicht_still_uebernommen(tmp_path):
    pfad = tmp_path / "segler.json"
    pfad.write_text(
        '{"schema_version":"1.0","modelle":{},'
        '"modelle":{"optimist":{"masse_kg":50,"position_rumpf_m":[0,0,0]}}}',
        encoding="utf-8")
    with pytest.raises(ValueError, match="Doppelter JSON"):
        SeglerEinstellungen(pfad)


def test_reine_paketdefaults_sind_explizit_nicht_schreibbar():
    einstellungen = SeglerEinstellungen()
    assert einstellungen.werte("optimist", 50, (0, 0, .45)) == {
        "masse_kg": 50, "position_rumpf_m": [0, 0, .45]}
    with pytest.raises(ValueError, match="keinen Speicherpfad"):
        einstellungen.setzen("optimist", {
            "masse_kg": 50, "position_rumpf_m": [0, 0, .45]})


def test_punktmasse_explizit_ohne_geometrie():
    with pytest.raises(KoerperFehler):
        Koerper(masse=50)
    with pytest.raises(KoerperFehler):
        Koerper(masse=50, punktmasse=True, verdrangend=True)
    k = Koerper(masse=50, punktmasse=True, verdrangend=False)
    assert k.snapshot().blatt_meshes == ()


def test_segler_manifest_verlangt_referenz_und_starre_wurzel(tmp_path):
    source = ROOT / "code" / "modelle" / "optimist" / "modell.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    paket = tmp_path / "optimist"
    paket.mkdir()
    data.pop("rumpfreferenz_m")
    (paket / "modell.json").write_text(json.dumps(data), encoding="utf-8")
    materialien = lade_konfig(ROOT / "konfigurationen").materialien_blocks
    with pytest.raises(ModellFehler, match="rumpfreferenz"):
        lade_modellmanifest(
            paket, materialien, _pruefe_geometriepfade=False)
    data["rumpfreferenz_m"] = [0, 0, 0]
    segler = data["koerper"]["teile"].pop(0)
    data["koerper"]["teile"].append({
        "id": "crew", "name": "Crew", "teile": [segler]})
    (paket / "modell.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ModellFehler, match="Wurzelframe"):
        lade_modellmanifest(
            paket, materialien, _pruefe_geometriepfade=False)
