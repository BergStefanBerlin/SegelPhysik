import json
import os
from types import SimpleNamespace

import numpy as np
import pytest

from segelphysik.core.auftrieb import Vektor
from segelphysik.core.dynamik import Bewegungszustand, schritt_mit_kraeften
from segelphysik.core.konfig_lader import KonfigFehler, lade_physik
from segelphysik.core.kraftmodell import (
    KraftErgebnis, Kraftmodell, KraftmodellMitHydroCache)


def _hydro(f_a=(0.0, 0.0, 10.0), moment=(0.0, 0.0, 0.0)):
    return SimpleNamespace(
        V_tauch=0.5,
        K=Vektor((1.0, 2.0, 3.0)),
        F_A=Vektor(f_a),
        M=Vektor(moment),
    )


def test_nicht_konfigurierte_module_liefern_unveraenderte_hydrostatik():
    modell = Kraftmodell(lambda *_args, **_kwargs: _hydro())

    ergebnis = modell((0.0, 0.0, 0.0), v=(0.0, 0.0, 0.0),
                      omega=(0.0, 0.0, 0.0))

    assert ergebnis.F_A.as_array() == pytest.approx((0.0, 0.0, 10.0))
    assert ergebnis.F_gesamt.as_array() == pytest.approx(ergebnis.F_A.as_array())
    assert ergebnis.M.as_array() == pytest.approx((0.0, 0.0, 0.0))
    assert ergebnis.V_tauch == 0.5
    assert ergebnis.K.as_array() == pytest.approx((1.0, 2.0, 3.0))


def test_lineare_quadratische_widerstaende_nutzen_relativgeschwindigkeit():
    modell = Kraftmodell(
        lambda *_args, **_kwargs: _hydro(moment=(7.0, 0.0, 0.0)),
        linear_widerstand=(0, 0, 2, 4, 0, 0),
        quadratischer_widerstand=(0, 0, 3, 5, 0, 0),
        fluidgeschwindigkeit=(0, 0, 1),
        fluidwinkelgeschwindigkeit=(1, 0, 0),
    )

    ergebnis = modell(
        (0.0, 0.0, 0.0), v=(0.0, 0.0, 2.0), omega=(2.0, 0.0, 0.0))

    assert ergebnis.F_gesamt.as_array() == pytest.approx((0.0, 0.0, 5.0))
    assert ergebnis.M_gesamt.as_array() == pytest.approx((-2.0, 0.0, 0.0))


def test_echtzeit_hydro_cache_haelt_hydrostatik_und_aktualisiert_widerstand():
    aufrufe = []

    def hydro(lage, **_kwargs):
        aufrufe.append(lage)
        z = lage[0]
        return _hydro(f_a=(0.0, 0.0, 10.0 + z))

    cache = KraftmodellMitHydroCache(
        Kraftmodell(hydro, linear_widerstand=(0, 0, 2, 0, 0, 0)),
        intervall=4)
    ergebnisse = [
        cache((float(i), 0.0, 0.0), v=(0.0, 0.0, float(i)))
        for i in range(4)
    ]

    assert len(aufrufe) == 1
    assert [wert.F_A.z for wert in ergebnisse] == pytest.approx(
        (10.0, 10.0, 10.0, 10.0))
    assert [wert.F_gesamt.z for wert in ergebnisse] == pytest.approx(
        (10.0, 8.0, 6.0, 4.0))

    cache.aktualisieren()
    erneuert = cache((4.0, 0.0, 0.0))
    assert len(aufrufe) == 2
    assert erneuert.F_A.z == pytest.approx(14.0)


def test_echtzeit_hydro_cache_mit_intervall_eins_ist_exakt_pro_schritt():
    aufrufe = []

    def hydro(lage, **_kwargs):
        aufrufe.append(lage)
        return _hydro(f_a=(0.0, 0.0, 10.0 + lage[0]))

    cache = KraftmodellMitHydroCache(
        Kraftmodell(hydro), intervall=1)
    erster = cache((1.0, 0.0, 0.0))
    zweiter = cache((2.0, 0.0, 0.0))

    assert len(aufrufe) == 2
    assert erster.F_A.z == pytest.approx(11.0)
    assert zweiter.F_A.z == pytest.approx(12.0)


@pytest.mark.parametrize("kwargs", [
    {"linear_widerstand": (0, 0, -1, 0, 0, 0)},
    {"quadratischer_widerstand": (0, 0, float("inf"), 0, 0, 0)},
    {"fluidgeschwindigkeit": (0, float("nan"), 0)},
    {"added_mass_diagonal": (0, 0, -1, 0, 0, 0)},
    {"added_mass_diagonal": (0, 0, float("inf"), 0, 0, 0)},
])
def test_kraftmodule_lehnen_ungueltige_parameter_ab(kwargs):
    with pytest.raises(ValueError):
        Kraftmodell(lambda *_args, **_kw: _hydro(), **kwargs)


def test_added_mass_aendert_effektive_tauchmasse_und_kraftresultat():
    modell = Kraftmodell(
        lambda *_args, **_kwargs: _hydro(),
        added_mass_diagonal=(0, 0, 2, 0, 0, 0))
    kraft = modell((0.0, 0.0, 0.0))

    zustand, ergebnis = schritt_mit_kraeften(
        Bewegungszustand(), lambda *_args, **_kwargs: kraft,
        masse=2.0, traegheit_xx=3.0, dt=0.1, g=9.81)
    erwartete_beschleunigung = (10.0 - 2.0 * 9.81) / 4.0

    assert zustand.v_z == pytest.approx(erwartete_beschleunigung * 0.1)
    assert ergebnis.F_gesamt.z == pytest.approx(
        10.0 - 2.0 * erwartete_beschleunigung)
    assert isinstance(ergebnis, KraftErgebnis)


def _physikdatei(tmp_path, kraefte=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "doc", "WegZuV1.0", "Backlog",
                           "physik_vorlage.json"),
              encoding="utf-8") as datei:
        daten = json.load(datei)
    if kraefte is not None:
        daten["physik"]["kraefte"] = kraefte
    pfad = tmp_path / "physik.json"
    pfad.write_text(json.dumps(daten), encoding="utf-8")
    return lade_physik(str(tmp_path))


def test_kraftkonfiguration_ist_standardmaessig_deaktiviert(tmp_path):
    physik = _physikdatei(tmp_path)

    assert physik.fluidgeschwindigkeit == (0.0, 0.0, 0.0)
    assert physik.fluidwinkelgeschwindigkeit == (0.0, 0.0, 0.0)
    assert physik.linear_widerstand == (0.0,) * 6
    assert physik.quadratischer_widerstand == (0.0,) * 6
    assert physik.added_mass_diagonal == (0.0,) * 6


def test_kraftkonfiguration_lehnt_nichtendliche_und_negative_werte_ab(
        tmp_path):
    with pytest.raises(KonfigFehler, match="endliche Zahl"):
        _physikdatei(tmp_path, {
            "linear_widerstand_kg_pro_s": [0, 0, 0, 0, 0, float("nan")]
        })

    with pytest.raises(KonfigFehler, match="nicht-negative"):
        _physikdatei(tmp_path, {
            "added_mass_kg_und_kg_m2": [0, 0, -1, 0, 0, 0]
        })
