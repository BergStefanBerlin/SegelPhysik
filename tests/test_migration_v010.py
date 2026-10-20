from copy import deepcopy
from dataclasses import replace
import json
import sys

import numpy as np
import pytest

from segelphysik.core.kraftmodell import Kraftbeitrag, Wrench
from werkzeuge.migration_baseline import (
    funktionsmessungen, live_kommando, live_pruefen, profilieren,
)
from werkzeuge import migration_inventar
from werkzeuge import benchmark_gui_live
from werkzeuge.migration_inventar import (
    QUELLEN, ROOT, SPEC, definitionen, inventar, referenzmanifest,
    messnachweise, schreiben, spezifikationseintraege,
)
from werkzeuge.migration_vergleich import (
    messen, performancevergleich, vergleiche, zeitstatistik,
)


def _kraefte():
    return {
        "rotation": np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]]),
        "beitraege": (
            Kraftbeitrag("auftrieb", Wrench(
                "simulationsframe", (0., 1., 0.), (0., 0., 12.), (12., 0., 0.))),
            Kraftbeitrag("gewicht", Wrench(
                "simulationsframe", (0., 0., 0.), (0., 0., -10.), (0., 0., 0.))),
        ),
        "dreiecke": np.array([[0, 1, 2]], dtype=np.int64),
    }


def test_harness_erkennt_identische_daten_ohne_toleranz():
    vergleiche(_kraefte(), _kraefte())


@pytest.mark.parametrize("mutation", [
    "wert", "frame", "beitrag", "beitragsname", "rotation", "form", "dtype", "nan",
])
def test_harness_erkennt_gezielte_mutationen(mutation):
    referenz = _kraefte()
    kandidat = deepcopy(referenz)
    if mutation == "wert":
        a, b = kandidat["beitraege"]
        kandidat["beitraege"] = (
            replace(a, wrench=replace(a.wrench, kraft_N=(0., 0., 12.001))), b)
    elif mutation == "frame":
        a, b = kandidat["beitraege"]
        kandidat["beitraege"] = (
            replace(a, wrench=replace(a.wrench, frame="koerperframe")), b)
    elif mutation == "beitrag":
        kandidat["beitraege"] = kandidat["beitraege"][:1]
    elif mutation == "beitragsname":
        a, b = kandidat["beitraege"]
        kandidat["beitraege"] = (replace(a, name="unbenannt"), b)
    elif mutation == "rotation":
        kandidat["rotation"] = kandidat["rotation"].T.copy()
    elif mutation == "form":
        kandidat["rotation"] = kandidat["rotation"].reshape(9)
    elif mutation == "dtype":
        kandidat["rotation"] = kandidat["rotation"].astype(np.float32)
    else:
        kandidat["rotation"][0, 0] = np.nan
    with pytest.raises(AssertionError):
        vergleiche(referenz, kandidat)


def test_harness_toleranzen_sind_explizit_und_feldgenau():
    vergleiche({"x": 1.}, {"x": 1. + 1e-10}, toleranzen={"$.x": (0., 1e-9)})
    with pytest.raises(AssertionError):
        vergleiche({"x": 1.}, {"x": 1. + 1e-10})
    with pytest.raises(ValueError, match="Unbenutzte"):
        vergleiche({"x": 1.}, {"x": 1.}, toleranzen={"$.falsch": (0., 1e-9)})
    with pytest.raises(ValueError, match="Indizes"):
        vergleiche(1, 1, toleranzen={"$": (0., 1.)})


@pytest.mark.parametrize("grenze", [None, 1, (0.,), (-1., 0.), (0., float("inf")),
                                   (True, 1.), ("0", 1.)])
def test_harness_lehnt_ungueltige_toleranzen_ab(grenze):
    with pytest.raises(ValueError):
        vergleiche(1., 1., toleranzen={"$": grenze})


def test_harness_erkennt_grosse_integer_ohne_floatrundung():
    with pytest.raises(AssertionError):
        vergleiche(np.array([2**60]), np.array([2**60 + 1]))
    with pytest.raises(AssertionError):
        vergleiche(float("nan"), float("nan"))


def test_messung_hat_rohwerte_und_reicht_fehler_durch():
    aufrufe = []
    statistik, ergebnisse = messen(lambda: aufrufe.append(1) or 42)
    assert len(aufrufe) == 4
    assert ergebnisse == [42] * 3
    assert statistik["anzahl"] == 3
    assert len(statistik["rohwerte_s"]) == 3

    def fehler():
        raise ValueError("bewusster Messfehler")

    with pytest.raises(ValueError, match="bewusster Messfehler"):
        messen(fehler)


@pytest.mark.parametrize("werte", [[], [0.], [-1.], [float("nan")], [float("inf")], [True]])
def test_zeitstatistik_keine_erfolgsfoermigen_fehlwerte(werte):
    with pytest.raises(ValueError):
        zeitstatistik(werte)


def test_performancebericht_keine_unbelegte_freigabe():
    daten = performancevergleich([2., 2.1, 1.9], [1., 1.1, .9])
    assert daten["beschleunigungsfaktor"] == 2
    assert daten["ersparnis_prozent"] == 50
    assert daten["vorteil_groesser_als_spannweiten"]
    assert not performancevergleich([2., 3., 1.], [1.9, 2.9, .9])[
        "vorteil_groesser_als_spannweiten"]
    with pytest.raises(ValueError, match="drei"):
        performancevergleich([1., 2.], [1., 2., 3.])


def test_inventar_loest_alle_spec_funktionen_und_closures_auf():
    daten = inventar()
    zeilen = daten["eintraege"]
    geplant = list(spezifikationseintraege(SPEC.read_text(encoding="utf-8")))
    assert len([z for z in zeilen if not z["erzeugte_closure"]]) == len(geplant) == 271
    assert len(zeilen) == 298
    renderer = {z["funktion"] for z in zeilen if z["modul"] == "render/vista.py"}
    assert renderer.isdisjoint({
        "PyVistaRenderer._update_ring", "PyVistaRenderer._clamp_to_bodies",
        "PyVistaRenderer.update", "PyVistaRenderer._body_half_height"})
    assert {"PyVistaRenderer._smooth_surface", "PyVistaRenderer._refresh_arrows",
            "PyVistaRenderer.screen_to_water"} <= renderer
    assert {z["anforderung"] for z in zeilen} == {
        "A-V0.10-%05d" % n for n in range(6, 31)}
    assert any(z["erzeugte_closure"] and "baue_kraftfunktion_6dof." in z["funktion"]
               for z in zeilen)
    for zeile in zeilen:
        assert (zeile["funktion"], zeile["zeile"], zeile["ende_zeile"],
                zeile["profilzeile"]) in definitionen(QUELLEN / zeile["modul"])
        assert zeile["regressionstests"]
        assert all((ROOT / "tests" / name).is_file()
                   for name in zeile["regressionstests"])
        assert zeile["umsetzungsschritte"]
        assert zeile["eigenzeit_s"] is None
        assert zeile["profilbelege"] == []
    gespeichert = json.loads((
        ROOT / "doc" / "WegZuV1.0" / "Revisionslog" / "zuV0.10" /
        "Umsetzungsplan" / "Funktionsinventar_V0.10.json").read_text(encoding="utf-8"))
    assert gespeichert == daten


def test_referenzmanifest_umfasst_modelle_konfiguration_und_optik():
    daten = referenzmanifest(native_kandidaten=True, produktive_migration=True)
    namen = daten["dateien"]
    assert "konfigurationen/physik.json" in namen
    for modell in ("optimist", "folkeboot", "yacht1"):
        assert any(n.startswith("code/modelle/" + modell + "/") for n in namen)
    assert any(n.startswith("doc/WegZuV1.0/Revisionslog/zuV0.7/Widgets/") for n in namen)
    assert not any("Backlog" in n for n in namen)


def test_schreiben_ueberschreibt_keine_belege(tmp_path):
    ziel = tmp_path / "beleg.json"
    schreiben(ziel, {"erfolg": True})
    with pytest.raises(FileExistsError):
        schreiben(ziel, {"erfolg": False})
    assert json.loads(ziel.read_text(encoding="utf-8")) == {"erfolg": True}
    ungueltig = tmp_path / "ungueltig.json"
    with pytest.raises(ValueError):
        schreiben(ungueltig, {"wert": float("nan")})
    assert not ungueltig.exists()


def test_referenz_erkennt_geaenderte_dateien_aber_keine_crlf_unterschiede(
        tmp_path, monkeypatch):
    ziel = tmp_path / "modell.obj"
    ziel.write_bytes(b"v 0 0 0\r\n")
    monkeypatch.setattr(migration_inventar, "ROOT", tmp_path)
    monkeypatch.setattr(migration_inventar, "referenzdateien", lambda: ["modell.obj"])
    monkeypatch.setattr(migration_inventar.subprocess, "check_output",
                        lambda *args, **kwargs: b"v 0 0 0\n")
    assert referenzmanifest()["dateien"]
    ziel.write_bytes(b"v 0 0 1\n")
    with pytest.raises(ValueError, match="weicht"):
        referenzmanifest()
    with pytest.raises(ValueError, match="weicht"):
        referenzmanifest(native_kandidaten=True)


def test_nur_expliziter_kandidatenmodus_erlaubt_native_quellabweichungen(
        tmp_path, monkeypatch):
    ziel = tmp_path / "code" / "cpp" / "src" / "modul.cpp"
    ziel.parent.mkdir(parents=True)
    ziel.write_text("Kandidat", encoding="utf-8")
    monkeypatch.setattr(migration_inventar, "ROOT", tmp_path)
    monkeypatch.setattr(migration_inventar, "referenzdateien",
                        lambda: ["code/cpp/src/modul.cpp"])
    monkeypatch.setattr(migration_inventar.subprocess, "check_output",
                        lambda *args, **kwargs: b"Referenz")
    with pytest.raises(ValueError, match="weicht"):
        referenzmanifest()
    daten = referenzmanifest(native_kandidaten=True)
    assert daten["dateien"]["code/cpp/src/modul.cpp"] != migration_inventar.texthash(ziel)
    assert daten["abweichende_native_kandidatendateien"] == [{
        "datei": "code/cpp/src/modul.cpp",
        "referenz_sha256": daten["dateien"]["code/cpp/src/modul.cpp"],
        "kandidat_sha256": migration_inventar.texthash(ziel),
    }]


def test_produktiver_manifestmodus_erlaubt_keine_geaenderten_referenzwerte(
        tmp_path, monkeypatch):
    name = "konfigurationen/physik.json"
    ziel = tmp_path / name
    ziel.parent.mkdir(parents=True)
    ziel.write_text("geaendert", encoding="utf-8")
    monkeypatch.setattr(migration_inventar, "ROOT", tmp_path)
    monkeypatch.setattr(migration_inventar, "referenzdateien", lambda: [name])
    monkeypatch.setattr(migration_inventar.subprocess, "check_output",
                        lambda *args, **kwargs: b"Referenz")
    with pytest.raises(ValueError, match="weicht"):
        referenzmanifest(native_kandidaten=True, produktive_migration=True)


def test_profilzuordnung_ignoriert_gleichnamige_funktionen_anderer_module():
    eintrag = next(z for z in inventar()["eintraege"]
                   if z["funktion"] == "quaternion_matrix")
    profil = {
        "datei": "code/python/segelphysik/" + eintrag["modul"],
        "zeile": eintrag["profilzeile"], "funktion": "quaternion_matrix",
        "aufrufe": 2, "eigenzeit_s": .01, "gesamtzeit_s": .02,
    }
    daten = {
        "modell": "optimist", "eingabe_sha256": "test",
        "punkte": 8, "dreiecke": 12,
        "instrumentierte_profile": {"workerbatch": [
            profil, {**profil, "datei": "anderes_modul.py"}]},
    }
    zeilen = funktionsmessungen([daten])["eintraege"]
    gemessen = next(z for z in zeilen if z["funktion"] == "quaternion_matrix")
    assert len(gemessen["profilbelege"]) == 1
    assert gemessen["profilbelege"][0]["profil"]["aufrufe"] == 2
    ungemessen = next(z for z in zeilen if z["funktion"] == "_clip_polygon")
    assert ungemessen["profilbelege"] == []
    assert "nicht beobachtet" in ungemessen["messstatus"]


def test_profil_hat_alle_funktionen_und_aufrufbeziehungen():
    def kind():
        return sum(range(20))

    def eltern():
        return kind()

    wert, profil = profilieren(eltern)
    assert wert == 190
    assert any(z["funktion"] == "kind" and z["aufrufe"] == 1 and z["aufrufer"]
               for z in profil)


def test_live_kommando_fixiert_modell_dauer_backend_und_optik(tmp_path):
    ziel = tmp_path / "live.json"
    standard = live_kommando("optimist", "standard", ziel)
    schulung = live_kommando("optimist", "schulung", ziel)
    assert "--schulungsdarstellung" not in standard
    assert schulung[-1] == "--schulungsdarstellung"
    assert standard[standard.index("--duration") + 1] == "300.0"
    assert standard[standard.index("--backend") + 1] == "exakt_union"
    assert standard[standard.index("--viewport-width") + 1] == "640"
    assert standard[standard.index("--viewport-height") + 1] == "480"
    with pytest.raises(ValueError):
        live_kommando("yacht1", "standard", ziel, dauer=299)


def _live():
    return {
        "szene": "yacht1", "qpa_plattform": "windows",
        "hydrostatik_backend": "exakt_union", "messlauf_gueltig": True,
        "fehler": [], "messdauer_s": 300., "physik_batches": 20,
        "qt_frame_swapped": 200, "frameabstand_p95_ms": 50.,
        "batch_median_ms": 10., "eingabe_bis_praesentierter_frame_ms": 40.,
        "warmup_s": 30, "aktive_layer": {"kraefte": True, "momente": True},
        "render_optionen_override": {"schulungsdarstellung": False},
        "viewport_vorgabe_px": [640, 480], "viewport_start_px": [640, 480],
        "renderzustand": {"fenstergroesse_px": [640, 480]},
    }


def test_live_fortsetzung_prueft_rohberichte_ohne_sie_zu_veraendern(tmp_path):
    from werkzeuge.migration_baseline import vorhandene_liveberichte

    daten = _live()
    daten["rohwerte"] = {"speicher_zeitreihe": [
        {"wandzeit_s": t, "gui": {
            "pid": 1, "private_bytes": 20000, "working_set_bytes": 30000},
         "worker": [{"pid": 2, "private_bytes": 10000, "working_set_bytes": 12000}]}
        for t in (1., 150., 300.)]}
    datei = tmp_path / "yacht1_standard_2.json"
    schreiben(datei, daten)
    vorher = datei.read_bytes()
    assert vorhandene_liveberichte([datei], 3) == {
        "yacht1_standard_2": (datei.resolve(), daten)}
    assert datei.read_bytes() == vorher
    with pytest.raises(ValueError, match="doppelter"):
        vorhandene_liveberichte([datei, datei], 3)
    with pytest.raises(ValueError, match="Unbekannter"):
        vorhandene_liveberichte([datei], 1)
    daten["qt_frame_swapped"] = 0
    schreiben(tmp_path / "yacht1_standard_1.json", daten)
    with pytest.raises(ValueError, match="sichtbare"):
        vorhandene_liveberichte([tmp_path / "yacht1_standard_1.json"], 3)


@pytest.mark.parametrize("feld,wert", [
    ("qpa_plattform", "offscreen"), ("messdauer_s", 299.),
    ("physik_batches", 0), ("fehler", ["Workerfehler"]),
    ("messlauf_gueltig", False), ("eingabe_bis_praesentierter_frame_ms", None),
    ("frameabstand_p95_ms", float("nan")),
    ("render_optionen_override", {"schulungsdarstellung": True}),
    ("aktive_layer", {"kraefte": False}),
    ("warmup_s", 0),
    ("viewport_start_px", [491, 828]),
    ("renderzustand", {"fenstergroesse_px": [929, 828]}),
])
def test_live_gate_lehnt_ungueltige_messlaeufe_ab(feld, wert):
    daten = _live()
    live_pruefen(daten, "yacht1", "standard", 300)
    daten[feld] = wert
    with pytest.raises(ValueError):
        live_pruefen(daten, "yacht1", "standard", 300)


@pytest.mark.parametrize("argumente", [
    ["--viewport-width", "640"],
    ["--viewport-height", "480"],
    ["--viewport-width", "0", "--viewport-height", "480"],
    ["--viewport-width", "640", "--viewport-height", "-1"],
])
def test_live_cli_ungueltiger_viewport_startet_keine_gui(monkeypatch, argumente):
    def verboten(*args, **kwargs):
        pytest.fail("Ungueltiger Viewport darf keinen GUI-Lauf starten")

    monkeypatch.setattr(benchmark_gui_live, "benchmark", verboten)
    with pytest.raises(SystemExit) as fehler:
        benchmark_gui_live.main(argumente)
    assert fehler.value.code == 2


def test_kumulierte_profile_brauchen_aufloesbare_eindeutige_rohdaten(tmp_path, monkeypatch):
    eintrag = {
        "modul": "core/test.py", "profilzeile": 42,
        "profilbelege": [], "status": "offen",
    }
    monkeypatch.setattr(migration_inventar, "ROOT", tmp_path)
    monkeypatch.setattr(migration_inventar, "inventar",
                        lambda: {"eintraege": [dict(eintrag)]})
    pfad = tmp_path / "profil.json"
    schreiben(pfad, {"profil": [{
        "datei": "code/python/segelphysik/core/test.py", "zeile": 42,
        "aufrufe": 3, "eigenzeit_s": .01, "gesamtzeit_s": .02, "aufrufer": [],
    }]})
    daten = messnachweise([pfad])
    assert daten["eintraege_mit_aufrufbeleg"] == 1
    assert daten["eintraege"][0]["status"] == "offen"
    assert daten["eintraege"][0]["profilbelege"][0]["aufrufe"] == 3
    for profile in ([], [pfad, pfad]):
        with pytest.raises(ValueError, match="Rohprofilliste"):
            messnachweise(profile)
    falsch = tmp_path / "falsch.json"
    schreiben(falsch, {"profil": [{
        "datei": "anderes_modul.py", "zeile": 42, "aufrufe": 3,
        "eigenzeit_s": .01, "gesamtzeit_s": .02, "aufrufer": [],
    }]})
    assert messnachweise([falsch])["eintraege_mit_aufrufbeleg"] == 0
    ohne = tmp_path / "ohne.json"
    schreiben(ohne, {})
    with pytest.raises(ValueError, match="Keine vollstaendigen"):
        messnachweise([ohne])


def test_profilbewertung_summiert_nur_exklusive_zeiten_und_direkte_kanten():
    quellpfad = ROOT / "code" / "python" / "segelphysik" / "core" / "test.py"
    profil = [
        {"datei": "code/python/segelphysik/core/test.py", "zeile": 1,
         "eigenzeit_s": .1, "gesamtzeit_s": 1., "aufrufer": []},
        {"datei": "bibliothek.py", "zeile": 2,
         "eigenzeit_s": .2, "gesamtzeit_s": .7, "aufrufer": []},
        {"datei": "~", "zeile": 0, "funktion": "native_method",
         "eigenzeit_s": .7, "gesamtzeit_s": .7, "aufrufer": [
             {"datei": str(quellpfad), "zeile": 1, "statistik": [2, 2, .2, .2]},
             {"datei": "bibliothek.py", "zeile": 2, "statistik": [3, 3, .5, .5]}]},
    ]
    daten = migration_inventar.profilbewertung(profil)
    assert daten["summe_eigenzeiten_s"] == pytest.approx(1.)
    assert daten["projekt_python_eigenzeit_s"] == .1
    assert daten["native_eigenzeit_s"] == .7
    assert daten["andere_eigenzeit_s"] == pytest.approx(.2)
    assert daten["zeitbewertung_gueltig"] is True
    key = ("code/python/segelphysik/core/test.py", 1)
    assert daten["native_anteile"][key] == [{
        "funktion": "native_method", "aufrufe": 2, "eigenzeit_s": .2}]
    # Die transitiven .5 Sekunden werden dem direkten Projektaufrufer nicht zugeschlagen.
    assert daten["native_anteile"][("bibliothek.py", 2)][0]["eigenzeit_s"] == .5


@pytest.mark.parametrize("zeit", [-1., float("nan"), float("inf")])
def test_profilbewertung_lehnt_ungueltige_zeiten_ab(zeit):
    with pytest.raises(ValueError, match="Profilzeiten"):
        migration_inventar.profilbewertung([{
            "datei": "test.py", "eigenzeit_s": zeit, "gesamtzeit_s": 1.,
        }])


def test_profilbewertung_lehnt_leeres_profil_ab():
    with pytest.raises(ValueError, match="Profilgesamtzeit"):
        migration_inventar.profilbewertung([])


def test_callbackprofil_erfasst_nur_aktive_synchrone_aufrufe_und_reicht_fehler_durch():
    from werkzeuge.migration_baseline import CallbackProfil

    profil = CallbackProfil()
    aufrufe = []

    def innen():
        aufrufe.append("innen")
        return 42

    def aussen():
        return profil.aufrufen(innen)

    assert profil.aufrufen(aussen) == 42
    with pytest.raises(ValueError, match="Profilaufrufe"):
        profil.bericht()
    profil.messen = True
    assert profil.aufrufen(aussen) == 42
    assert profil.aufrufe == 1
    assert aufrufe == ["innen", "innen"]
    daten = profil.bericht()
    assert next(f for f in daten if f["funktion"] == "innen")["aufrufe"] == 1
    assert migration_inventar.profilbewertung(daten)["zeitbewertung_gueltig"]

    def fehler():
        raise RuntimeError("bewusster Callbackfehler")

    with pytest.raises(RuntimeError, match="Callbackfehler"):
        profil.aufrufen(fehler)
    assert profil.aktiv is False
    assert profil.aufrufe == 2
    profil.messen = False
    assert profil.aufrufen(innen) == 42
    assert profil.aufrufe == 2


def test_testnachweise_nutzen_nur_bestandene_testfaelle_ohne_native_abnahme(
        tmp_path, monkeypatch):
    monkeypatch.setattr(migration_inventar, "ROOT", tmp_path)
    monkeypatch.setattr(migration_inventar, "inventar", lambda: {"eintraege": [{
        "modul": "core/test.py", "profilzeile": 42, "status": "offen",
    }]})
    datei = tmp_path / "testprofile.json"
    schreiben(datei, {
        "exitcode": 0,
        "tests": [
            {"test": "test_ok", "phase": "call", "ergebnis": "passed"},
            {"test": "test_skip", "phase": "call", "ergebnis": "skipped"},
        ],
        "testprofile": {
            node: [{"datei": "code/python/segelphysik/core/test.py", "zeile": 42,
                    "aufrufe": 3}] for node in ("test_ok", "test_skip")},
    })
    daten = migration_inventar.testnachweise([datei])
    assert daten["eintraege_mit_testbeleg"] == 1
    eintrag = daten["eintraege"][0]
    assert eintrag["status"] == "offen"
    assert len(eintrag["konkrete_referenztests"]) == 1
    assert eintrag["konkrete_referenztests"][0]["test"] == "test_ok"
    assert eintrag["konkrete_referenztests"][0]["nativer_vergleich"] is False
    for dateien in ([], [datei, datei]):
        with pytest.raises(ValueError, match="Testprofilliste"):
            migration_inventar.testnachweise(dateien)
    fehler = tmp_path / "fehlgeschlagen.json"
    schreiben(fehler, {"exitcode": 1})
    with pytest.raises(ValueError, match="fehlgeschlagener Suite"):
        migration_inventar.testnachweise([fehler])


def test_callbackprofil_misst_keine_fremdthread_funktionen():
    import threading
    from werkzeuge.migration_baseline import CallbackProfil

    start = threading.Event()
    fertig = threading.Event()

    def fremdthread_funktion():
        fertig.set()

    def worker():
        if start.wait(10):
            fremdthread_funktion()

    def callback():
        start.set()
        assert fertig.wait(10), "Fremdthread wurde nicht ausgefuehrt"

    thread = threading.Thread(target=worker)
    thread.start()
    profil = CallbackProfil()
    profil.messen = True
    try:
        profil.aufrufen(callback)
    finally:
        start.set()
        thread.join(10)
    assert not thread.is_alive()
    namen = {p["funktion"] for p in profil.bericht()}
    assert "callback" in namen
    assert "fremdthread_funktion" not in namen


@pytest.mark.parametrize("mutation", [
    None, "spec", "fehlender_eintrag", "doppelter_eintrag",
    "rohhash", "testquelle", "kein_test", "unbekannter_test",
])
def test_pruefplan_verknuepft_nur_unveraenderte_eindeutige_referenzquellen(
        tmp_path, monkeypatch, mutation):
    monkeypatch.setattr(migration_inventar, "ROOT", tmp_path)
    monkeypatch.setattr(migration_inventar, "QUELLEN", tmp_path)
    quelle = tmp_path / "kern.py"
    quelle.write_text("def kern():\n    return 1\n", encoding="utf-8")
    testquelle = tmp_path / "test_kern.py"
    testquelle.write_text(
        "def test_kern():\n    assert True\n", encoding="utf-8")
    roh = tmp_path / "roh.json"
    schreiben(roh, {"exitcode": 0, "testquellen_sha256": {
        "test_kern.py": migration_inventar.texthash(testquelle)}})
    kopf = {
        "python_referenzcommit": migration_inventar.REFERENZ, "spec_sha256": "spec"}
    eintrag = {
        "anforderung": "A1", "modul": "kern.py", "funktion": "kern",
        "zeile": 1, "spec_zeile": "Kernblock",
        "quell_sha256": migration_inventar.texthash(quelle),
    }
    monkeypatch.setattr(migration_inventar, "inventar", lambda: {
        **kopf, "eintraege": [eintrag]})
    profile = {**kopf, "profilquellen": [], "eintraege": [{
        **eintrag, "profilbelege": []}]}
    tests = {**kopf, "testprofilquellen": [{
        "datei": "roh.json", "sha256": migration_inventar.texthash(roh)}],
        "eintraege": [{**eintrag, "konkrete_referenztests": [{
            "test": "test_kern.py::test_kern"}]}]}
    if mutation == "spec":
        tests["spec_sha256"] = "anders"
    elif mutation == "fehlender_eintrag":
        tests["eintraege"] = []
    elif mutation == "doppelter_eintrag":
        tests["eintraege"] *= 2
    elif mutation == "rohhash":
        tests["testprofilquellen"][0]["sha256"] = "anders"
    elif mutation == "testquelle":
        testquelle.write_text("def test_kern():\n    assert False\n", encoding="utf-8")
    elif mutation == "kein_test":
        tests["eintraege"][0]["konkrete_referenztests"] = []
    elif mutation == "unbekannter_test":
        tests["eintraege"][0]["konkrete_referenztests"][0]["test"] = (
            "test_kern.py::test_unbekannt")
    p, t = tmp_path / "profile.json", tmp_path / "tests.json"
    schreiben(p, profile)
    schreiben(t, tests)
    if mutation is not None:
        with pytest.raises(ValueError):
            migration_inventar.pruefplan(p, t)
        return
    plan = migration_inventar.pruefplan(p, t)
    assert len(plan["eintraege"]) == 1
    e = plan["eintraege"][0]
    assert e["zeitbewertung"]["max_beobachteter_eigenzeitanteil"] is None
    assert e["konkrete_referenztests"][0]["von_zeile"] == 1
    assert e["konkrete_referenztests"][0]["bis_zeile"] == 2
    assert "exakt" in e["vergleichsvertrag"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-Prozesszaehler")
def test_windows_prozessspeicher_liefert_echte_gui_und_prozesszaehler():
    import os
    from werkzeuge.migration_baseline import windows_prozessspeicher

    for pid in (None, os.getpid()):
        daten = windows_prozessspeicher(pid)
        assert daten["pid"] == os.getpid()
        assert daten["private_bytes"] > 0
        assert daten["working_set_bytes"] > 0
    with pytest.raises(OSError):
        windows_prozessspeicher(0)


@pytest.mark.parametrize("mutation", [
    None, "fehlender_worker", "zu_kurz", "zu_spaet", "nan", "reihenfolge", "null",
])
def test_speichergate_verlangt_vollstaendiges_fenster_und_gueltige_prozesse(mutation):
    from werkzeuge.migration_baseline import speicherreihe_pruefen

    reihe = [
        {"wandzeit_s": t, "gui": {
            "pid": 1, "private_bytes": 20000, "working_set_bytes": 30000},
         "worker": [{"pid": 2, "private_bytes": 10000, "working_set_bytes": 12000}]}
        for t in (1., 150., 300.)]
    if mutation is None:
        speicherreihe_pruefen(reihe, 300.)
        return
    if mutation == "fehlender_worker":
        reihe[1]["worker"] = []
    elif mutation == "zu_kurz":
        reihe.pop()
    elif mutation == "zu_spaet":
        reihe[0]["wandzeit_s"] = 6.
    elif mutation == "nan":
        reihe[1]["wandzeit_s"] = float("nan")
    elif mutation == "reihenfolge":
        reihe[1]["wandzeit_s"] = .5
    else:
        reihe[1]["worker"][0]["private_bytes"] = 0
    with pytest.raises(ValueError):
        speicherreihe_pruefen(reihe, 300.)


def test_profilbewertung_sperrt_inkonsistente_threadprofilzeiten(tmp_path, monkeypatch):
    monkeypatch.setattr(migration_inventar, "ROOT", tmp_path)
    monkeypatch.setattr(migration_inventar, "inventar", lambda: {"eintraege": [{
        "modul": "core/test.py", "profilzeile": 42, "profilbelege": [],
    }]})
    pfad = tmp_path / "profil.json"
    schreiben(pfad, {"profil": [{
        "datei": "code/python/segelphysik/core/test.py", "zeile": 42,
        "funktion": "test", "aufrufe": 3,
        "eigenzeit_s": .03, "gesamtzeit_s": .02, "aufrufer": [],
    }]})
    daten = messnachweise([pfad])
    assert daten["eintraege_mit_aufrufbeleg"] == 1
    assert daten["profilbewertungen"][0]["zeitbewertung_gueltig"] is False
    assert len(daten["profilbewertungen"][0]["zeitanomalien"]) == 1
    beleg = daten["eintraege"][0]["profilbelege"][0]
    assert beleg["profilzeitbewertung_gueltig"] is False
    assert beleg["profil_eigenzeitanteil"] is None
    assert beleg["profil_gesamtzeitanteil"] is None
