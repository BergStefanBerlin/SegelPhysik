from dataclasses import replace
import math

import pytest

from segelphysik.core.genauigkeit_v09 import GenauigkeitV09
from segelphysik.core.dynamik_6dof import Zustand6DOF


@pytest.fixture
def gate():
    return GenauigkeitV09(4, 2, 100, 10, 2)


@pytest.fixture
def hydro():
    return {"volumen_m3": 1.0, "kraft_N": [0, 0, 1000],
            "moment_Nm": [10, 0, 0], "schwerpunkt_m": [0, 0, 0]}


@pytest.mark.parametrize("feld,wert", [
    ("volumen_m3", 1.0220001),
    ("kraft_N", [0, 0, 1040.0001]),
    ("moment_Nm", [12.500001, 0, 0]),
    ("schwerpunkt_m", [0.0200001, 0, 0]),
])
def test_hydro_jede_grenze_wird_einzeln_erzwungen(gate, hydro, feld, wert):
    gate.hydrostatik(hydro, hydro)
    with pytest.raises(ValueError, match="überschreitet"):
        gate.hydrostatik(hydro, dict(hydro, **{feld: wert}))


def test_hydro_kleine_benetzung_schwerpunktgate_nicht_anwenden(gate, hydro):
    referenz = dict(hydro, volumen_m3=.01)
    gate.hydrostatik(referenz, dict(referenz, schwerpunkt_m=[10, 0, 0]))
    with pytest.raises(ValueError):
        gate.hydrostatik(hydro, dict(hydro, kraft_N=[0, 0, float("nan")]))
    trocken = dict(hydro, volumen_m3=0, kraft_N=[0, 0, 0], moment_Nm=[0, 0, 0])
    with pytest.raises(ValueError, match="Benetzt"):
        gate.hydrostatik(trocken, dict(trocken, volumen_m3=.0001))
    with pytest.raises(ValueError, match="Rückstellrichtung"):
        gate.hydrostatik(
            dict(trocken, moment_Nm=[.001, 0, 0]),
            dict(trocken, moment_Nm=[-.001, 0, 0]), rueckstelltest=True)


def test_statikwinkel_hoehe_und_quaternion_vorzeichen(gate):
    gate.statik([0, 0, 0], [1, 0, 0, 0], [0, 0, .02], [-1, 0, 0, 0])
    with pytest.raises(ValueError, match="höhe"):
        gate.statik([0, 0, 0], [1, 0, 0, 0], [0, 0, .020001], [1, 0, 0, 0])
    winkel = math.radians(1.001) / 2
    with pytest.raises(ValueError, match="orientierung"):
        gate.statik([0, 0, 0], [1, 0, 0, 0], [0, 0, 0],
                    [math.cos(winkel), math.sin(winkel), 0, 0])


def test_dynamik_vergleicht_gleiche_zeit_und_jede_stichprobe(gate):
    z = Zustand6DOF()
    for t in range(31):
        gate.dynamik(t, t, z, z)
    for t in (-1, 30.1, float("nan")):
        with pytest.raises(ValueError):
            gate.dynamik(t, t, z, z)
    with pytest.raises(ValueError):
        gate.dynamik(1, 2, z, z)
    with pytest.raises(ValueError, match="Dynamikposition"):
        gate.dynamik(1, 1, z, replace(z, position=(.050001, 0, 0)))
    with pytest.raises(ValueError, match="Geschwindigkeit"):
        gate.dynamik(1, 1, z, replace(
            z, geschwindigkeit_koerper=(.020001, 0, 0)))
    w = math.radians(2.001) / 2
    with pytest.raises(ValueError, match="Dynamikorientierung"):
        gate.dynamik(1, 1, z, replace(
            z, quaternion=(math.cos(w), 0, 0, math.sin(w))))


def test_schwingungszeiten_und_fehlende_messbarkeit(gate):
    gate.schwingung(10, 11, 20, 22)
    gate.schwingung(None, None, None, None)
    with pytest.raises(ValueError, match="Periode"):
        gate.schwingung(10, 11.001, 20, 20)
    with pytest.raises(ValueError, match="Abklingzeit"):
        gate.schwingung(10, 10, 20, 22.001)
    with pytest.raises(ValueError):
        gate.schwingung(None, 10, None, None)


@pytest.mark.parametrize("mutation", ["hash", "hydro", "dt", "fassung"])
def test_eingefrorene_referenz_akzeptiert_keine_stille_aenderung(mutation):
    from copy import deepcopy
    import json
    from werkzeuge.pruefe_genauigkeit_v09 import ZIEL, pruefen

    referenz = json.loads(ZIEL.read_text(encoding="utf-8"))
    neu = deepcopy(referenz)
    pruefen(referenz, neu)
    modell = neu["modelle"]["optimist"]
    if mutation == "hash":
        modell["paket_sha256"]["modell.json"] = "andere Modellfassung"
    elif mutation == "hydro":
        modell["hydrostatik"][0]["referenz"]["volumen_m3"] += .0001
    elif mutation == "dt":
        modell["dynamik_pruefvorgabe"]["dt_s"] *= 2
    else:
        neu["fassung"] = 2
    with pytest.raises((ValueError, AssertionError)):
        pruefen(referenz, neu)


def test_pakethash_ignoriert_nur_git_zeilenenden(tmp_path):
    from werkzeuge.pruefe_genauigkeit_v09 import _fingerabdruck

    manifest = tmp_path / "modell.json"
    mesh = tmp_path / "rumpf.obj"
    manifest.write_bytes(b'{"id":"boot"}\n')
    mesh.write_bytes(b"v 0 0 0\nv 1 0 0\n")
    referenz = _fingerabdruck(tmp_path)
    manifest.write_bytes(b'{"id":"boot"}\r\n')
    mesh.write_bytes(b"v 0 0 0\r\nv 1 0 0\r\n")
    assert _fingerabdruck(tmp_path) == referenz
    mesh.write_bytes(b"v 0 0 0\r\nv 2 0 0\r\n")
    assert _fingerabdruck(tmp_path)["rumpf.obj"] != referenz["rumpf.obj"]
