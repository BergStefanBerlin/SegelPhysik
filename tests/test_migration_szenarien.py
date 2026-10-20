from dataclasses import replace
from types import SimpleNamespace
import math
import threading

import numpy as np
import pytest
import json

from segelphysik.core.auftrieb import Vektor
from segelphysik.core.dynamik_6dof import Zustand6DOF
from segelphysik.core.kraftmodell import Kraftbeitrag, Wrench
from werkzeuge.migration_szenarien import (
    folge_berechnen, folge_pruefen, kraftzeile, pruefe_gui_lifecycle,
    schrittanzahl, zustandszeile,
)
from werkzeuge.migration_vergleich import vergleiche
from werkzeuge import migration_szenarien


def _kraft(trocken=False):
    return SimpleNamespace(
        V_tauch=0. if trocken else 1.,
        K=Vektor((0., 0., 0.)), F_A=Vektor((0., 0., 10.)),
        F_gesamt=Vektor((0., 0., 1.)), M_gesamt=Vektor((0., 1., 0.)),
        bezugspunkt_m=(0., 0., 0.),
        beitraege=() if trocken else (
            Kraftbeitrag("auftrieb", Wrench(
                "simulationsframe", (0., 0., 0.), (0., 0., 10.), (0., 0., 0.))),),
    )


def test_schrittanzahl_haelt_30sekunden_und_original_dt_ein():
    assert schrittanzahl(30., .004) == 7500
    assert schrittanzahl(30., .01) == 3000
    assert schrittanzahl(120., .004) == 30000


@pytest.mark.parametrize("dauer,dt", [
    (30., 0.), (0., .01), (-1., .01), (float("nan"), .01),
    (30., float("inf")), (1., .3),
])
def test_schrittanzahl_ungueltige_oder_unpassende_eingaben(dauer, dt):
    with pytest.raises(ValueError):
        schrittanzahl(dauer, dt)


def test_kraftschema_behaelt_benannte_einzelbeitraege_frames_und_bezugspunkte():
    schema, daten = kraftzeile(_kraft())
    assert schema == (("auftrieb", "simulationsframe"),)
    assert daten.shape == (25,)
    assert daten.dtype == np.float64
    assert daten[0] == 1.
    assert daten[16:].tolist() == [0., 0., 0., 0., 0., 10., 0., 0., 0.]
    defekt = _kraft()
    defekt.F_gesamt = Vektor((float("nan"), 0., 0.))
    with pytest.raises(ValueError, match="Nicht-endliche"):
        kraftzeile(defekt)


def test_dynamik_friert_jeden_zeitpunkt_und_wechselnde_beitragslisten_ein(tmp_path):
    aufrufe = []

    def batch(zustand, anzahl):
        aufrufe.append(anzahl)
        x = zustand.position[0] + 1.
        ende = replace(zustand, position=(x, 0., 0.))
        return ende, _kraft(trocken=x == 2.), None, .001

    daten, schema, zeiten = folge_berechnen(Zustand6DOF(), 3, .01, batch)
    assert aufrufe == [1, 1, 1]
    np.testing.assert_array_equal(daten["zeit_s"], np.arange(4) * .01)
    np.testing.assert_array_equal(daten["zustaende"][:, 0], [0., 1., 2., 3.])
    assert daten["schema_indices"].tolist() == [0, 1, 0]
    assert schema == [(("auftrieb", "simulationsframe"),), ()]
    assert daten["kraft_offsets"].tolist() == [0, 25, 41, 66]
    assert zeiten["worker_einzelschritte"]["anzahl"] == 3
    folge_pruefen(daten, schema, .03, .01)
    datei = tmp_path / "folge.npz"
    np.savez_compressed(datei, **daten)
    with np.load(datei, allow_pickle=False) as gespeichert:
        vergleiche(daten, dict(gespeichert))


def test_dynamikfehler_erscheint_nicht_als_erfolgsfolge():
    def defekt(*_args):
        return None, None, "bewusster Workerfehler", .01

    with pytest.raises(RuntimeError, match="Dynamikschritt 1: bewusster Workerfehler"):
        folge_berechnen(Zustand6DOF(), 3, .01, defekt)


def test_dynamik_lehnt_nichtendlichen_start_und_falsche_schrittzahl_ab():
    for anzahl in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            folge_berechnen(Zustand6DOF(), anzahl, .01, None)
    with pytest.raises(ValueError, match="Anfangszustand"):
        folge_berechnen(
            Zustand6DOF(position=(float("nan"), 0., 0.)), 3, .01, None)


def test_zustandsspalten_haben_feste_reihenfolge_ohne_framewechsel():
    z = Zustand6DOF(
        position=(1., 2., 3.), quaternion=(1., 0., 0., 0.),
        geschwindigkeit_koerper=(4., 5., 6.),
        winkelgeschwindigkeit_koerper=(7., 8., 9.))
    assert zustandszeile(z).tolist() == [
        1., 2., 3., 1., 0., 0., 0., 4., 5., 6., 7., 8., 9.]


def test_kalter_aufbau_meldungen_bleiben_sichtbar_ohne_json_zu_beschaedigen(
        monkeypatch, capsys):
    def mit_meldung(name):
        print("WARNUNG: bestehende Plausibilitaetsmeldung")
        return {"modell": name, "dauer_s": .01}

    monkeypatch.setattr(migration_szenarien, "kalter_aufbau", mit_meldung)
    migration_szenarien.main(["--kind-aufbau", "folkeboot"])
    ausgabe = capsys.readouterr()
    assert "WARNUNG" in ausgabe.err
    assert json.loads(ausgabe.out) == {"modell": "folkeboot", "dauer_s": .01}


def _lifecycle():
    return {
        "messlauf_gueltig": True, "fehler": [], "qpa_plattform": "windows",
        "renderzustand": {"fenstergroesse_px": [640, 480]},
        "lebenszyklus": [
            {"phase": phase, "modus": modus, "wandzeit_s": t, "angefordert_s": 2.}
            for phase, modus, t in (
                ("pause", "pausiert", 2.), ("fortsetzung", "normal", 3.),
                ("wechsel_statisch", "pausiert", 5.),
                ("wechsel_echtzeit", "ueberlast_beobachtung", 7.))
        ],
    }


def test_lifecycle_hat_tatsaechliche_phasen_und_pause_ohne_neue_zeitforderung():
    bericht = _lifecycle()
    pruefe_gui_lifecycle(bericht)
    bericht["lebenszyklus"][1]["angefordert_s"] = 3.
    with pytest.raises(ValueError, match="Pause"):
        pruefe_gui_lifecycle(bericht)


@pytest.mark.parametrize("mutation", ["phase", "modus", "reihenfolge", "offscreen", "fehler"])
def test_lifecycle_lehnt_unvollstaendige_oder_fehlerhafte_nachweise_ab(mutation):
    bericht = _lifecycle()
    if mutation == "phase":
        bericht["lebenszyklus"].pop()
    elif mutation == "modus":
        bericht["lebenszyklus"][0]["modus"] = "normal"
    elif mutation == "reihenfolge":
        bericht["lebenszyklus"][1]["wandzeit_s"] = 1.
    elif mutation == "offscreen":
        bericht["qpa_plattform"] = "offscreen"
    else:
        bericht["fehler"] = ["Workerfehler"]
    with pytest.raises(ValueError):
        pruefe_gui_lifecycle(bericht)


@pytest.mark.parametrize("mutation", [
    "zeit", "zustandsform", "schema", "offset", "kraft", "nan", "dtype", "quaternion",
])
def test_dynamikartefakt_pruefung_erkennt_jede_strukturmutation(mutation):
    def batch(zustand, _anzahl):
        return zustand, _kraft(), None, .01

    daten, schemas, _ = folge_berechnen(Zustand6DOF(), 3, .01, batch)
    folge_pruefen(daten, schemas, .03, .01)
    if mutation == "zeit":
        daten["zeit_s"][1] += 1e-6
    elif mutation == "zustandsform":
        daten["zustaende"] = daten["zustaende"][:-1]
    elif mutation == "schema":
        daten["schema_indices"][0] = 2
    elif mutation == "offset":
        daten["kraft_offsets"][1] -= 1
    elif mutation == "kraft":
        daten["kraftwerte"] = daten["kraftwerte"][:-1]
    elif mutation == "nan":
        daten["kraftwerte"][0] = np.nan
    elif mutation == "dtype":
        daten["zustaende"] = daten["zustaende"].astype(np.float32)
    else:
        daten["zustaende"][1, 3:7] = (1., 1., 0., 0.)
    with pytest.raises((ValueError, AssertionError)):
        folge_pruefen(daten, schemas, .03, .01)


def test_schwingungskennwerte_messen_periode_und_abklingende_maxima():
    zeit = np.arange(0., 12.001, .001)
    werte = 2. + np.exp(-zeit / 4.) * np.cos(math.pi * zeit)
    daten = migration_szenarien.schwingungskennwerte(zeit, werte, 2.)
    assert daten["periodenstatus"] == daten["abklingstatus"] == "messbar"
    assert daten["periode_median_s"] == pytest.approx(2., abs=.001)
    assert 4. < daten["abklingzeit_s"] < 5.1
    assert daten["anfangsamplitude"] == 1.
    assert len(daten["maxima_amplitude"]) > 2


def test_schwingungskennwerte_erfinden_keine_messung_bei_fehlenden_perioden():
    zeit = np.arange(11, dtype=float)
    daten = migration_szenarien.schwingungskennwerte(zeit, np.ones(11), 1.)
    assert daten["periode_median_s"] is daten["abklingzeit_s"] is None
    assert daten["periodenstatus"].startswith("nicht messbar")
    assert daten["abklingstatus"].startswith("nicht messbar")


def test_schwingungskennwerte_akzeptieren_keine_voruebergehende_abnahme():
    daten = migration_szenarien.schwingungskennwerte(
        np.arange(11, dtype=float),
        [1., 0., .2, 0., .2, 0., .6, 0., .2, 0., .1], 0.)
    assert daten["abklingzeit_s"] is None


@pytest.mark.parametrize("zeiten,werte,lage", [
    ([0., 0., 1.], [1., 0., 0.], 0.),
    ([0., 1., 2.], [1., 0.], 0.),
    ([0., 1., 2.], [1., float("nan"), 0.], 0.),
    ([0., 1., 2.], [1., 0., 0.], float("inf")),
])
def test_schwingungskennwerte_verwerfen_ungueltige_reihen(zeiten, werte, lage):
    with pytest.raises(ValueError, match="Schwingungsreihen"):
        migration_szenarien.schwingungskennwerte(zeiten, werte, lage)


@pytest.mark.parametrize("phi", [0., math.tau, -math.tau, 2. * math.tau])
def test_schwingungsauswertung_behaelt_rollwinkelast_und_einheiten(phi):
    from segelphysik.core.dynamik_6dof import quaternion_aus_matrix
    from segelphysik.core.stationaer_hydrodynamik import _rotation

    zustaende = np.zeros((3, 13))
    zustaende[:, 2] = 1.01
    for i, delta in enumerate((.1, .08, .06)):
        zustaende[i, 3:7] = quaternion_aus_matrix(_rotation(phi + delta, .02, 0.))
    daten = migration_szenarien.schwingungsauswertung(
        {"zeit_s": np.arange(3, dtype=float), "zustaende": zustaende},
        {"z": 1., "phi": phi})
    assert daten["rollen_rad"]["anfangsamplitude"] == pytest.approx(.1, abs=1e-14)
    assert daten["heben_m"]["anfangsamplitude"] == pytest.approx(.01, abs=1e-14)
    assert daten["nicken_rad"]["anfangsamplitude"] == pytest.approx(.02, abs=1e-14)


@pytest.mark.parametrize("art,dauer", [
    ("dynamik", "0"), ("dynamik", "-1"), ("dynamik", "nan"),
    ("dynamik", "inf"), ("prozess", "120"),
])
def test_dynamikdauer_cli_lehnt_falsche_vorgaben_vor_dateierzeugung_ab(
        tmp_path, art, dauer):
    ziel = tmp_path / "nicht_erzeugen"
    with pytest.raises(SystemExit) as fehler:
        migration_szenarien.main([
            "--art", art, "--dynamik-dauer", dauer, "--output", str(ziel)])
    assert fehler.value.code == 2
    assert not ziel.exists()


def test_beladungsfaelle_halten_massen_und_alle_verschiebungen_ein():
    original = {"masse_kg": 50., "position_rumpf_m": [1., 2., 3.]}
    faelle = migration_szenarien.beladungsfaelle(original)
    assert len(faelle) == 21
    assert {f["masse_kg"] for f in faelle} == {40., 50., 60.}
    for masse in (40., 50., 60.):
        positionen = [f["position_rumpf_m"] for f in faelle if f["masse_kg"] == masse]
        assert [1., 2., 3.] in positionen
        for achse in range(3):
            for delta in (-.2, .2):
                erwartet = [1., 2., 3.]
                erwartet[achse] += delta
                assert erwartet in positionen
    assert original == {"masse_kg": 50., "position_rumpf_m": [1., 2., 3.]}


def test_aenderungsszenarien_isolieren_einstellungen_und_pruefen_rueckstellung(
        tmp_path, monkeypatch):
    from segelphysik.core import echtzeit_prozess, fabriken, konfig_lader, modell_lader
    from segelphysik.core.koerper import GelenkSnapshot, KoerperSnapshot
    from segelphysik.core.segler_einstellungen import SeglerEinstellungen

    einstellungen = SeglerEinstellungen(tmp_path / "nutzer.json")
    einstellungen.setzen("optimist", {
        "masse_kg": 70., "position_rumpf_m": [0., 0., .55]})
    vorher = einstellungen.pfad.read_bytes()
    konfig = SimpleNamespace(
        segler_einstellungen=einstellungen, materialien_blocks={},
        wasser_dichte=lambda: 1000.)
    punkt = SimpleNamespace(masse_kg=50., position_rumpf_m=[0., 0., .45], teile=())
    manifest = SimpleNamespace(koerper=SimpleNamespace(masse_kg=None, teile=(punkt,)))
    monkeypatch.setattr(konfig_lader, "lade_konfig", lambda _: konfig)
    monkeypatch.setattr(konfig_lader, "lade_physik", lambda _: SimpleNamespace(dt_s=.004))
    monkeypatch.setattr(modell_lader, "lade_modellmanifest", lambda *_: manifest)

    class Koerper:
        def __init__(self):
            self.werte = konfig.segler_einstellungen.werte(
                "optimist", 50., [0., 0., .45])
            self.winkel = 0.
            self.version = 0

        def snapshot(self):
            return KoerperSnapshot(
                self.werte["masse_kg"], np.eye(3), (),
                tuple(self.werte["position_rumpf_m"]), Zustand6DOF(), self.version,
                gelenkzustaende=(GelenkSnapshot("ruder", "boot", (0., 0., 1.), self.winkel),))

        def gelenkwinkel_setzen(self, _knoten, winkel):
            self.winkel = winkel
            self.version += 1

    monkeypatch.setattr(fabriken, "baue_modellpaket", lambda *_: (Koerper(), None))
    worker = {}
    monkeypatch.setattr(echtzeit_prozess, "initialisieren",
                        lambda snapshot, *_: worker.update(snapshot=snapshot))
    monkeypatch.setattr(echtzeit_prozess, "_kraftfunktion",
                        SimpleNamespace(aktualisieren=lambda: None))

    def batch(zustand, _anzahl):
        kraft = _kraft()
        kraft.gesamt_wrench = kraft.beitraege[0].wrench
        ende = replace(zustand, position=(
            worker["snapshot"].masse, 0., 0.))
        return ende, kraft, None, .001

    monkeypatch.setattr(echtzeit_prozess, "schritte_berechnen", batch)
    daten = migration_szenarien.aenderungsmessung("optimist")
    assert len(daten["faelle"]) == 27
    assert daten["gelenkanzahl"] == 1
    assert all(f["wiederholungen_exakt_identisch"] for f in daten["faelle"])
    beladung = [f for f in daten["faelle"] if f["art"] == "beladung"]
    assert {f["werte"]["masse_kg"] for f in beladung} == {56., 70., 84.}
    assert len([f for f in daten["faelle"] if f["art"].endswith("rueckstellung")]) == 3
    assert konfig.segler_einstellungen is einstellungen
    assert einstellungen.pfad.read_bytes() == vorher
    assert list(tmp_path.iterdir()) == [einstellungen.pfad]

    monkeypatch.setattr(echtzeit_prozess, "schritte_berechnen",
                        lambda *_: (None, None, "bewusster Fehler", .001))
    with pytest.raises(RuntimeError, match="bewusster Fehler"):
        migration_szenarien.aenderungsmessung("optimist")


def test_verzoegertes_signal_haelt_echten_wert_bis_zur_freigabe():
    erhalten = []
    tor = migration_szenarien.VerzoegertesSignal(
        SimpleNamespace(emit=lambda *args: erhalten.append(args)))
    thread = threading.Thread(target=lambda: tor.emit(1, "echtes Ergebnis"))
    thread.start()
    try:
        assert tor.bereit.wait(2.)
        assert tor.ergebnis == (1, "echtes Ergebnis")
        assert erhalten == []
    finally:
        tor.freigabe.set()
        thread.join(2.)
    assert not thread.is_alive()
    assert erhalten == [(1, "echtes Ergebnis")]
    assert tor.fehler is None


def _lastbericht(aktion="wechsel"):
    return {
        "modell": "optimist", "aktion": aktion,
        "zielmodell": "folkeboot" if aktion == "wechsel" else None,
        "aktionsdauer_s": .1, "qpa_plattform": "windows", "viewport_px": [640, 480],
        "generation_alt": 1, "generation_neu": 2,
        "altes_ergebnis_tatsaechlich_berechnet": True,
        "altes_ergebnis_nach_aktion_zugestellt": True,
        "veraltetes_ergebnis_ohne_zustandsaenderung_verworfen": True,
        "neues_modell_rechnet_und_praesentiert": aktion == "wechsel",
    }


def test_lastgate_akzeptiert_nur_tatsaechlich_gepruefte_aktionen():
    for aktion in ("wechsel", "schliessen"):
        migration_szenarien.pruefe_gui_lastfall(_lastbericht(aktion))


@pytest.mark.parametrize("feld,wert", [
    ("aktion", "unbekannt"), ("modell", "unbekannt"), ("zielmodell", "optimist"),
    ("qpa_plattform", "offscreen"), ("viewport_px", [491, 480]),
    ("aktionsdauer_s", float("nan")), ("aktionsdauer_s", -.01),
    ("generation_neu", 1), ("altes_ergebnis_tatsaechlich_berechnet", False),
    ("altes_ergebnis_nach_aktion_zugestellt", False),
    ("veraltetes_ergebnis_ohne_zustandsaenderung_verworfen", False),
    ("neues_modell_rechnet_und_praesentiert", False),
])
def test_lastgate_lehnt_unbelegte_oder_veraenderte_ergebnisse_ab(feld, wert):
    bericht = _lastbericht()
    bericht[feld] = wert
    with pytest.raises(ValueError, match="Schliessnachweis"):
        migration_szenarien.pruefe_gui_lastfall(bericht)


def test_warte_bis_zeitueberschreitung_wird_nicht_als_erfolg_gewertet():
    with pytest.raises(TimeoutError, match="bewusster Timeout"):
        migration_szenarien.warte_bis(
            SimpleNamespace(processEvents=lambda: None), lambda: False,
            "bewusster Timeout", timeout_s=0.)


def test_actorreferenz_erfasst_geometrie_transformation_farbe_und_keine_2d_texte():
    import pyvista as pv
    from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkTextActor

    mesh = pv.Sphere(theta_resolution=8, phi_resolution=8)
    mapper = vtkPolyDataMapper()
    mapper.SetInputData(mesh)
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(.1, .2, .3)
    bruecke = SimpleNamespace(
        _plotter=SimpleNamespace(renderer=SimpleNamespace(actors={
            "kugel": actor, "text": vtkTextActor()})), _vg_actors={})
    original = migration_szenarien.aktoren_snapshot(bruecke)
    assert set(original) == {"szene:kugel"}
    assert original["szene:kugel"]["punkte"] == mesh.n_points
    assert original["szene:kugel"]["farbe"] == (.1, .2, .3)
    assert migration_szenarien.aktoren_snapshot(bruecke) == original
    actor.SetPosition(1., 0., 0.)
    verschoben = migration_szenarien.aktoren_snapshot(bruecke)
    assert verschoben["szene:kugel"]["matrix"][0][3] == 1.
    assert verschoben["szene:kugel"]["geometrie_sha256"] == original["szene:kugel"]["geometrie_sha256"]
    mesh.points[0, 0] += .1
    assert (migration_szenarien.aktoren_snapshot(bruecke)["szene:kugel"]["geometrie_sha256"]
            != original["szene:kugel"]["geometrie_sha256"])
    mesh.points[0, 0] = np.nan
    with pytest.raises(ValueError, match="Nicht-endliche Actorgeometrie"):
        migration_szenarien.aktoren_snapshot(bruecke)
