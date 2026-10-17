import json
import os
from types import SimpleNamespace

import pytest

from segelphysik.core import einstellungen as ein
from segelphysik.core.einstellungen import Einstellungen, VORLAGE
from segelphysik.core.dynamik_6dof import Zustand6DOF

# Eingefrorene Datei der Schema-Version 1.0: muss in allen spaeteren
# Minor-Versionen weiter ladbar sein (Abwaertskompatibilitaet).
ALTE_DATEI_1_0 = {
    "schema_version": "1.0",
    "statisch": {"toleranz": 1e-6, "max_iterationen": 30,
                 "stagnation_anteil": 0.1},
    "dynamisch": {"zeitgenau": False, "max_schritte_pro_aufgabe": 8,
                  "max_schritte_nachholen": 32,
                  "ueberlast_rueckstand_s": 2.0, "ueberlast_dauer_s": 10.0,
                  "nachholen_ende_rueckstand_s": 0.2,
                  "nachholrate_ziel": 1.5},
}


def _datei(tmp_path, inhalt):
    pfad = tmp_path / "settings.json"
    pfad.write_text(json.dumps(inhalt), encoding="utf-8")
    return str(pfad)


def test_fehlende_datei_wird_mit_defaults_angelegt(tmp_path):
    pfad = str(tmp_path / "settings.json")
    e = Einstellungen.laden(pfad)
    assert os.path.exists(pfad)
    assert e.get("dynamisch", "zeitgenau") is False
    assert e.get("statisch", "max_iterationen") == 60
    assert e.get("modell", "paketfabrik_aktiv") is True
    assert json.load(open(pfad))["schema_version"] == ein.SCHEMA_VERSION


def test_alte_datei_1_0_bleibt_ladbar(tmp_path):
    e = Einstellungen.laden(_datei(tmp_path, ALTE_DATEI_1_0))
    for bereich in ("statisch", "dynamisch"):
        for k, v in ALTE_DATEI_1_0[bereich].items():
            assert e.get(bereich, k) == v
    assert e.get("anzeigen", "titel_sichtbar") is True
    assert e.get("anzeigen", "titel_beschreibung_sichtbar") is True
    assert e.get("anzeigen", "analog_sichtbar") is True
    assert e.get("anzeigen", "numerisch_sichtbar") is True
    assert e.meldungen == []


def test_setzen_speichert_sofort_und_prueft(tmp_path):
    pfad = str(tmp_path / "settings.json")
    e = Einstellungen.laden(pfad)
    e.setzen("dynamisch", "zeitgenau", False)
    assert json.load(open(pfad))["dynamisch"]["zeitgenau"] is False
    with pytest.raises(ValueError):
        e.setzen("dynamisch", "max_schritte_pro_aufgabe", 0)
    with pytest.raises(ValueError):
        e.setzen("dynamisch", "zeitgenau", 1)
    assert e.get("dynamisch", "max_schritte_pro_aufgabe") == 16


def test_ungueltige_und_fehlende_werte_fallen_auf_default(tmp_path):
    daten = {"schema_version": "1.0",
             "statisch": {"toleranz": -5.0},
             "dynamisch": {"zeitgenau": "ja"}}
    e = Einstellungen.laden(_datei(tmp_path, daten))
    assert e.get("statisch", "toleranz") == 1e-8
    assert e.get("dynamisch", "zeitgenau") is False
    assert e.get("statisch", "max_iterationen") == 60
    assert len(e.meldungen) == 2


def test_unbekannte_schluessel_bleiben_erhalten(tmp_path):
    daten = json.loads(json.dumps(ALTE_DATEI_1_0))
    daten["statisch"]["zukunft"] = 7
    daten["neuer_bereich"] = {"x": 1}
    pfad = _datei(tmp_path, daten)
    e = Einstellungen.laden(pfad)
    e.setzen("statisch", "max_iterationen", 99)
    neu = json.load(open(pfad))
    assert neu["statisch"]["zukunft"] == 7
    assert neu["neuer_bereich"] == {"x": 1}
    assert neu["statisch"]["max_iterationen"] == 99


def test_neuere_major_version_wird_nicht_ueberschrieben(tmp_path):
    daten = {"schema_version": "2.0", "statisch": {"x": 1}}
    pfad = _datei(tmp_path, daten)
    e = Einstellungen.laden(pfad)
    e.setzen("statisch", "max_iterationen", 99)
    assert json.load(open(pfad)) == daten
    assert e.get("statisch", "max_iterationen") == 99   # nur im Speicher
    assert e.meldungen


def test_kaputte_datei_wird_gesichert(tmp_path):
    pfad = tmp_path / "settings.json"
    pfad.write_text("{kaputt", encoding="utf-8")
    e = Einstellungen.laden(str(pfad))
    assert (tmp_path / "settings.json.bak").read_text() == "{kaputt"
    assert e.get("dynamisch", "zeitgenau") is False
    assert json.load(open(pfad))["schema_version"] == ein.SCHEMA_VERSION


def test_zuruecksetzen_nutzt_vorlage_defaults(tmp_path):
    e = Einstellungen.laden(_datei(tmp_path, ALTE_DATEI_1_0))
    e.zuruecksetzen("dynamisch")
    assert e.get("dynamisch", "zeitgenau") is False
    assert e.get("statisch", "max_iterationen") == 30   # Bereich unberuehrt
    e.zuruecksetzen()
    assert e.get("statisch", "max_iterationen") == 60


def test_defaults_kommen_aus_der_vorlagedatei(tmp_path):
    vorlage = json.loads(json.dumps(VORLAGE))
    vorlage["statisch"]["max_iterationen"]["default"] = 77
    pfad = tmp_path / "vorlage.json"
    pfad.write_text(json.dumps(vorlage), encoding="utf-8")
    e = Einstellungen(str(tmp_path / "s.json"), ein.vorlage_laden(str(pfad)))
    e.zuruecksetzen()
    assert e.get("statisch", "max_iterationen") == 77
    # defekte Vorlagedatei: eingebaute Vorlage
    pfad.write_text("nix", encoding="utf-8")
    assert ein.vorlage_laden(str(pfad)) == VORLAGE


def test_doc_vorlage_entspricht_eingebauter_vorlage():
    assert ein.vorlage_laden() == VORLAGE


def test_migration_wird_aufgerufen(tmp_path, monkeypatch):
    monkeypatch.setattr(ein, "SCHEMA_VERSION", "2.0")
    monkeypatch.setitem(
        ein.MIGRATIONEN, 1,
        lambda d: {**d, "schema_version": "2.0",
                   "statisch": {**d["statisch"], "max_iterationen": 11}})
    e = Einstellungen.laden(_datei(tmp_path, ALTE_DATEI_1_0))
    assert e.get("statisch", "max_iterationen") == 11


def test_dialog_aendert_und_setzt_zurueck(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui.einstellungen_dialog import EinstellungenDialog
    QApplication.instance() or QApplication([])
    e = Einstellungen.laden(str(tmp_path / "s.json"))
    d = EinstellungenDialog(e, "dynamisch")
    d._felder["zeitgenau"].setChecked(False)
    assert e.get("dynamisch", "zeitgenau") is False
    d._felder["max_schritte_pro_aufgabe"].setValue(5)
    assert e.get("dynamisch", "max_schritte_pro_aufgabe") == 5
    d._standard()
    assert e.get("dynamisch", "zeitgenau") is False
    assert d._felder["max_schritte_pro_aufgabe"].value() == 16


def test_anzeigeoptionen_dialog_speichert_sichtbarkeit(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui.einstellungen_dialog import EinstellungenDialog
    QApplication.instance() or QApplication([])
    e = Einstellungen.laden(str(tmp_path / "s.json"))
    d = EinstellungenDialog(e, "anzeigen")
    assert d.windowTitle() == "Anzeigeoptionen"
    assert all(d._felder[k].isChecked() for k in (
        "titel_sichtbar", "titel_beschreibung_sichtbar",
        "analog_sichtbar", "numerisch_sichtbar"))
    d._felder["analog_sichtbar"].setChecked(False)
    assert e.get("anzeigen", "analog_sichtbar") is False
    with open(e.pfad, encoding="utf-8") as f:
        gespeichert = json.load(f)
    assert gespeichert["anzeigen"]["analog_sichtbar"] is False
    d._standard()
    assert e.get("anzeigen", "analog_sichtbar") is True


def test_takt_schnellmodus_rechnet_ohne_rueckstand_und_pause(tmp_path, monkeypatch):
    import time
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui import hauptfenster as hf
    QApplication.instance() or QApplication([])
    gestartet = []
    monkeypatch.setattr(hf.QThreadPool, "start",
                        lambda self, aufgabe: gestartet.append(aufgabe))
    f = hf.HauptFenster()
    f._einstellungen = Einstellungen.laden(str(tmp_path / "s.json"))
    f._einstellungen.setzen("dynamisch", "zeitgenau", False)
    f._einstellungen.setzen("dynamisch", "max_schritte_pro_aufgabe", 5)
    f._echtzeit_physik = type("P", (), {"dt_s": 0.01})()
    f._echtzeit_zustand = Zustand6DOF()
    f._echtzeit_kraftfunktion = lambda *a: None
    f._laufzeit_koerper["k"] = SimpleNamespace(
        zustand=f._echtzeit_zustand,
        snapshot=lambda: SimpleNamespace(
            zustand=f._echtzeit_zustand, version=0))
    f._echtzeit_name = "k"
    # lange "Wandzeit" seit dem letzten Takt darf keinen Rueckstand erzeugen
    f._echtzeit_letzte_wandzeit = time.perf_counter() - 100.0
    f._echtzeit_takt()
    assert len(gestartet) == 1 and f._echtzeit_schritte_laufend == 5
    assert f._echtzeit_modus == "normal"
    assert f._echtzeit_rueckstand_s() == pytest.approx(0.05)
    f._echtzeit_takt()          # Auftrag laeuft noch: kein zweiter Start
    assert len(gestartet) == 1

def test_takt_schnellmodus_nie_schneller_als_reale_zeit(tmp_path, monkeypatch):
    import time
    from PySide6.QtWidgets import QApplication
    from segelphysik.gui import hauptfenster as hf
    QApplication.instance() or QApplication([])
    gestartet = []
    monkeypatch.setattr(hf.QThreadPool, "start",
                        lambda self, aufgabe: gestartet.append(aufgabe))
    f = hf.HauptFenster()
    f._einstellungen = Einstellungen.laden(str(tmp_path / "s.json"))
    f._einstellungen.setzen("dynamisch", "zeitgenau", False)
    f._einstellungen.setzen("dynamisch", "max_schritte_pro_aufgabe", 50)
    f._echtzeit_physik = type("P", (), {"dt_s": 0.01})()
    f._echtzeit_zustand = Zustand6DOF()
    f._echtzeit_kraftfunktion = lambda *a: None
    f._laufzeit_koerper["k"] = SimpleNamespace(
        zustand=f._echtzeit_zustand,
        snapshot=lambda: SimpleNamespace(
            zustand=f._echtzeit_zustand, version=0))
    f._echtzeit_name = "k"
    f._echtzeit_letzte_wandzeit = time.perf_counter() - 0.05
    f._echtzeit_takt()
    # 50 ms reale Zeit -> hoechstens ca. 5 Schritte, nicht der volle Block
    assert len(gestartet) == 1 and 4 <= f._echtzeit_schritte_laufend <= 8