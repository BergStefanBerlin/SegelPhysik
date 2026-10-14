import json
import os

import numpy as np
import pytest

from segelphysik.core import geometrie_konflikte as gk
from segelphysik.core import fabriken
from segelphysik.core import koerper_formen
from segelphysik.core import boot_bau
from segelphysik.core.konfig_lader import lade_konfig


@pytest.fixture
def quader():
    return koerper_formen.bau_quader(2.0, 2.0, 2.0)


def _verschiebe(form, versatz):
    punkte, dreiecke = form
    return punkte + np.asarray(versatz), dreiecke


def _obj_schreiben(pfad, form):
    punkte, dreiecke = form
    zeilen = [
        *(f"v {x:.17g} {y:.17g} {z:.17g}\n" for x, y, z in punkte),
        *(f"f {a + 1} {b + 1} {c + 1}\n" for a, b, c in dreiecke),
    ]
    pfad.write_text("".join(zeilen), encoding="utf-8")


def test_konflikterkennung_unterscheidet_disjunkt_beruehrung_und_ueberlappung(
        quader):
    teile = [
        {"name": "A", "form": quader, "volumetrisch": True},
        {"name": "B", "form": _verschiebe(quader, (3, 0, 0)),
         "volumetrisch": True},
    ]
    assert gk.finde_konflikte(teile) == []

    teile[1]["form"] = _verschiebe(quader, (2, 0, 0))
    assert gk.finde_konflikte(teile) == []

    teile[1]["form"] = _verschiebe(quader, (0.5, 0, 0))
    konflikte = gk.finde_konflikte(teile)
    assert len(konflikte) == 1
    assert (konflikte[0].name_a, konflikte[0].name_b) == ("A", "B")
    assert konflikte[0].volumen == pytest.approx(6.0, abs=1e-5)


def test_offene_schale_wird_nicht_als_volumenkonflikt_geprueft(quader):
    punkte, dreiecke = quader
    teile = [
        {"name": "Volumen", "form": quader, "volumetrisch": True},
        {"name": "Schale", "form": (punkte, dreiecke[:-2]),
         "volumetrisch": False},
    ]

    assert gk.finde_konflikte(teile) == []


def test_mehrere_benannte_konflikte_werden_alle_gefunden():
    gross = koerper_formen.bau_quader(4.0, 4.0, 4.0)
    klein = koerper_formen.bau_quader(1.0, 1.0, 1.0)
    konflikte = gk.finde_konflikte([
        {"name": "Rumpf", "form": gross, "volumetrisch": True},
        {"name": "Teil A", "form": _verschiebe(klein, (-1, 0, 0)),
         "volumetrisch": True},
        {"name": "Teil B", "form": _verschiebe(klein, (1, 0, 0)),
         "volumetrisch": True},
    ])

    assert [(k.name_a, k.name_b) for k in konflikte] == [
        ("Rumpf", "Teil A"), ("Rumpf", "Teil B")]
    assert all(k.volumen == pytest.approx(1.0, abs=1e-5)
               for k in konflikte)


def test_mehrfache_obj_korrekturen_sichern_jeden_zwischenstand(
        tmp_path):
    quellpfad = tmp_path / "rumpf.obj"
    gross = koerper_formen.bau_quader(4.0, 4.0, 4.0)
    klein = koerper_formen.bau_quader(1.0, 1.0, 1.0)
    prioritaet_a = _verschiebe(klein, (-1, 0, 0))
    prioritaet_b = _verschiebe(klein, (1, 0, 0))
    _obj_schreiben(quellpfad, gross)
    original = quellpfad.read_bytes()

    gk.korrigiere_obj_quelle(
        quellpfad, gross, prioritaet_a, skala=1.0)
    zwischenstand = quellpfad.read_bytes()
    geladene_punkte, geladene_dreiecke = boot_bau.lade_obj(str(quellpfad))
    aktuelle_form = (
        gk._obj_zu_welt(geladene_punkte, 1.0), geladene_dreiecke)

    sicherung = gk.korrigiere_obj_quelle(
        quellpfad, aktuelle_form, prioritaet_b, skala=1.0)

    assert sicherung == tmp_path / "rumpf.obj.bak.1"
    assert (tmp_path / "rumpf.obj.bak").read_bytes() == original
    assert sicherung.read_bytes() == zwischenstand
    geladene_punkte, geladene_dreiecke = boot_bau.lade_obj(str(quellpfad))
    rest = (gk._obj_zu_welt(geladene_punkte, 1.0), geladene_dreiecke)
    assert gk.finde_konflikte([
        {"name": "Rest", "form": rest, "volumetrisch": True},
        {"name": "Priorität A", "form": prioritaet_a, "volumetrisch": True},
        {"name": "Priorität B", "form": prioritaet_b, "volumetrisch": True},
    ]) == []


def test_differenz_entfernt_ueberlappung_und_erhaelt_restvolumen(quader):
    konflikt = _verschiebe(quader, (0, 0, 0))
    vorrang = _verschiebe(quader, (0.5, 0, 0))

    punkte, dreiecke, volumen = gk.differenzieren(konflikt, vorrang)

    assert volumen == pytest.approx(2.0, abs=1e-5)
    assert gk.finde_konflikte([
        {"name": "Rest", "form": (punkte, dreiecke), "volumetrisch": True},
        {"name": "Vorrang", "form": vorrang, "volumetrisch": True},
    ]) == []


def test_yacht_kiel_bulb_konflikt_ist_berechenbar_und_entfernbar():
    konfig = lade_konfig("konfigurationen")
    specs = fabriken._specs_aus_konfig(
        konfig.boot_teile, konfig, boot_bau.SKALA, fabriken.YACHT_ORDNER)
    blaetter = {}

    def sammle(teile):
        for teil in teile:
            if "teile" in teil:
                sammle(teil["teile"])
            else:
                blaetter[teil["_name"]] = teil["form"]

    sammle(specs)
    kiel, bulb = blaetter["kiel"], blaetter["bulb"]
    alte_bulb_punkte, alte_bulb_dreiecke = boot_bau.lade_obj(
        os.path.join(fabriken.YACHT_ORDNER, "bulb.obj.bak"))
    alte_bulb = (
        gk._obj_zu_welt(alte_bulb_punkte, boot_bau.SKALA),
        alte_bulb_dreiecke)
    konflikte = gk.finde_konflikte([
        {"name": "kiel", "form": kiel, "volumetrisch": True},
        {"name": "bulb vorher", "form": alte_bulb, "volumetrisch": True},
    ])
    assert len(konflikte) == 1
    assert konflikte[0].volumen > 0.0

    punkte, dreiecke, volumen = gk.differenzieren(alte_bulb, kiel)
    assert volumen > 0.0
    assert gk.finde_konflikte([
        {"name": "bulb differenziert", "form": (punkte, dreiecke),
         "volumetrisch": True},
        {"name": "kiel", "form": kiel, "volumetrisch": True},
    ]) == []
    assert gk.finde_konflikte([
        {"name": "kiel", "form": kiel, "volumetrisch": True},
        {"name": "bulb", "form": bulb, "volumetrisch": True},
    ]) == []
    assert gk._manifold(*bulb).volume() == pytest.approx(volumen, abs=1e-8)


def test_obj_korrektur_sichert_quelle_speichert_und_prueft_reload(
        tmp_path, quader):
    quellpfad = tmp_path / "teil.obj"
    _obj_schreiben(quellpfad, quader)
    original = quellpfad.read_bytes()
    vorrang = _verschiebe(quader, (0.5, 0, 0))

    sicherung = gk.korrigiere_obj_quelle(
        quellpfad, quader, vorrang, skala=1.0)

    assert sicherung.read_bytes() == original
    assert quellpfad.read_bytes() != original
    from segelphysik.core.boot_bau import lade_obj
    geladene_punkte, geladene_dreiecke = lade_obj(str(quellpfad))
    geladene_form = (
        gk._obj_zu_welt(geladene_punkte, 1.0), geladene_dreiecke)
    assert gk.finde_konflikte([
        {"name": "Korrigiert", "form": geladene_form, "volumetrisch": True},
        {"name": "Vorrang", "form": vorrang, "volumetrisch": True},
    ]) == []


def test_prozedurales_override_bleibt_neben_ursprungsform_erhalten(
        tmp_path, quader):
    quellpfad = tmp_path / "koerper.json"
    ursprungsform = {
        "typ": "box", "dx_m": 2.0, "dy_m": 2.0, "dz_m": 2.0}
    quelle = {
        "summenkoerper": {
            "objekt": {
                "form": ursprungsform,
                "dichte_kg_pro_m3": 950.0,
                "farbe": "#ffffff",
                "farbe_unter_wasser": "#cccccc",
            },
        },
    }
    quellpfad.write_text(json.dumps(quelle), encoding="utf-8")
    original = quellpfad.read_bytes()
    vorrang = _verschiebe(quader, (0.5, 0, 0))

    sicherung = gk.korrigiere_prozedurale_quelle(
        quellpfad, ("summenkoerper", "objekt"), quader, vorrang)

    assert sicherung.read_bytes() == original
    gespeichert = json.loads(quellpfad.read_text(encoding="utf-8"))
    eintrag = gespeichert["summenkoerper"]["objekt"]
    assert eintrag["form"] == ursprungsform
    override = gk.override_aus_eintrag(eintrag)
    assert override is not None
    assert gk.finde_konflikte([
        {"name": "Korrigiert", "form": override, "volumetrisch": True},
        {"name": "Vorrang", "form": vorrang, "volumetrisch": True},
    ]) == []
    konfig = lade_konfig("konfigurationen")
    koerper = fabriken.baue_form(konfig, eintrag)
    assert koerper._volumen == pytest.approx(2.0, abs=1e-5)


def test_fehlgeschlagene_reload_pruefung_rollt_obj_quelle_zurueck(
        tmp_path, quader, monkeypatch):
    quellpfad = tmp_path / "teil.obj"
    _obj_schreiben(quellpfad, quader)
    original = quellpfad.read_bytes()
    monkeypatch.setattr(
        gk, "_obj_zu_welt",
        lambda punkte, _skala: np.full_like(punkte, np.nan))

    with pytest.raises(gk.GeometrieKonfliktFehler, match="zurückgerollt"):
        gk.korrigiere_obj_quelle(
            quellpfad, quader, _verschiebe(quader, (0.5, 0, 0)))

    assert quellpfad.read_bytes() == original
    assert (tmp_path / "teil.obj.bak").read_bytes() == original


def test_fehlgeschlagener_obj_schreibversuch_rollt_quelle_zurueck(
        tmp_path, quader, monkeypatch):
    quellpfad = tmp_path / "teil.obj"
    _obj_schreiben(quellpfad, quader)
    original = quellpfad.read_bytes()
    atomar = gk._atomar_schreiben
    anzahl = 0

    def fehler_einmal(pfad, daten):
        nonlocal anzahl
        anzahl += 1
        if anzahl == 1:
            raise OSError("simulierter Schreibfehler")
        atomar(pfad, daten)

    monkeypatch.setattr(gk, "_atomar_schreiben", fehler_einmal)
    with pytest.raises(gk.GeometrieKonfliktFehler, match="zurückgerollt"):
        gk.korrigiere_obj_quelle(
            quellpfad, quader, _verschiebe(quader, (0.5, 0, 0)))

    assert anzahl == 2
    assert quellpfad.read_bytes() == original
    assert (tmp_path / "teil.obj.bak").read_bytes() == original


def test_vorhandene_sicherung_wird_erhalten_und_neue_version_angelegt(
        tmp_path, quader):
    quellpfad = tmp_path / "teil.obj"
    _obj_schreiben(quellpfad, quader)
    sicherung = tmp_path / "teil.obj.bak"
    sicherung.write_bytes(b"bestehende Sicherung")
    original = quellpfad.read_bytes()

    sicherung = gk.korrigiere_obj_quelle(
        quellpfad, quader, _verschiebe(quader, (0.5, 0, 0)))

    assert sicherung == tmp_path / "teil.obj.bak.1"
    assert quellpfad.read_bytes() != original
    assert sicherung.read_bytes() == original
    assert (tmp_path / "teil.obj.bak").read_bytes() == b"bestehende Sicherung"
    assert (tmp_path / "teil.obj.bak.1").read_bytes() == original
