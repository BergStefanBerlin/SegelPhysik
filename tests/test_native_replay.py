from copy import deepcopy
import json

import pytest

from werkzeuge.migration_replay import vorlaeufig_pruefen
from werkzeuge.pruefe_genauigkeit_v09 import ZIEL, referenzfaelle


def test_vorlaeufiger_nativer_replay_gegen_unveraenderte_referenzen(monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", "cpp")
    alt = json.loads(ZIEL.read_text(encoding="utf-8"))
    neu = json.loads(json.dumps(referenzfaelle(), allow_nan=False))
    assert vorlaeufig_pruefen(alt, neu)["vorlaeufig_bestanden"]


@pytest.mark.parametrize("mutation", ["modellhash", "kraft", "position", "schema", "nan"])
def test_vorlaeufiger_replay_erkennt_unzulaessige_mutationen(mutation):
    alt = json.loads(ZIEL.read_text(encoding="utf-8"))
    neu = deepcopy(alt)
    modell = neu["modelle"]["optimist"]
    fall = modell["hydrostatik"][0]
    if mutation == "modellhash":
        modell["paket_sha256"] = "veraendert"
    elif mutation == "position":
        fall["position_m"][0] += 1e-6
    elif mutation == "schema":
        del fall["referenz"]
    elif mutation == "nan":
        fall["quaternion_wxyz"][0] = float("nan")
    else:
        feld = next(k for k, v in fall["referenz"].items() if isinstance(v, float))
        fall["referenz"][feld] += 1e-5
    with pytest.raises((AssertionError, KeyError)):
        vorlaeufig_pruefen(alt, neu)
