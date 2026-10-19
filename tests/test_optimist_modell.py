from pathlib import Path

import numpy as np
import pytest

from segelphysik.core.auftrieb import G_NORM, baue_kraftfunktion
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.hydrodynamik import (
    HydrodynamikModell,
    hydrodynamik_teile_aus_koerper,
)
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.modell_lader import lade_modellpaket
from segelphysik.core.segler_einstellungen import SeglerEinstellungen


_WURZEL = Path(__file__).resolve().parents[1]
_PAKET = _WURZEL / "code" / "modelle" / "optimist"


def _blaetter(koerper):
    if not koerper.teile:
        return [koerper]
    return [
        blatt
        for kind, _pose in koerper.teile
        for blatt in _blaetter(kind)
    ]


@pytest.fixture(scope="module")
def optimist():
    konfig = lade_konfig(_WURZEL / "konfigurationen")
    konfig.segler_einstellungen = SeglerEinstellungen()
    paket = lade_modellpaket(_PAKET, konfig.materialien_blocks)
    koerper, _ = baue_summenkoerper(konfig, "optimist")
    return konfig, paket, koerper


def test_optimist_paket_hat_gepruefte_teile_und_plausible_abmessungen(
        optimist):
    _konfig, paket, _koerper = optimist

    assert paket.manifest.id == "optimist"
    assert set(paket.meshes) == {
        "rumpf", "schwert", "ruder", "pinne", "pinneverlaengerung",
        "mast", "baum", "spriet", "segel", "gummigelenk",
    }
    ruder = next(
        teil for teil in paket.manifest.koerper.teile
        if teil.id == "ruderanlage")
    assert ruder.name == "Ruder"
    assert {teil.id for teil in ruder.teile} == {
        "ruder", "pinne", "pinneverlaengerung", "gummigelenk",
    }
    assert next(
        teil for teil in paket.manifest.koerper.teile
        if teil.id == "rumpf").name == "Rumpf"
    assert next(
        teil for teil in paket.manifest.koerper.teile
        if teil.id == "schwert").name == "Schwert"

    rumpf = paket.meshes["rumpf"].punkte_si
    np.testing.assert_allclose(
        np.ptp(rumpf, axis=0), [2.359926, 1.12, 0.396154], atol=1e-5)
    mast = paket.meshes["mast"].punkte_si
    assert np.ptp(mast, axis=0)[2] == pytest.approx(2.271387, abs=1e-5)


def test_optimist_masse_und_auftrieb_ermoeglichen_schwimmlage(optimist):
    _konfig, _paket, koerper = optimist

    assert 90.0 < koerper.masse < 95.0
    auftrieb = baue_kraftfunktion(koerper, pfad="exakt_union")
    gewicht = koerper.masse * G_NORM

    assert auftrieb((0.0, 0.0, 0.0)).F_A.z > gewicht
    assert auftrieb((0.5, 0.0, 0.0)).F_A.z < gewicht


def test_optimist_hydrodynamik_nutzt_rumpf_schwert_und_ruder(optimist):
    _konfig, _paket, koerper = optimist

    teile = hydrodynamik_teile_aus_koerper(koerper)
    assert {teil.rolle for teil in teile} == {"rumpf", "kiel", "ruder"}

    modell = HydrodynamikModell.aus_koerper(koerper)
    beitraege = modell.beitraege_erzeugen(
        (0.0, 0.0, 0.0), v=(1.0, 0.0, 0.0))
    assert {beitrag.name for beitrag in beitraege} == {
        "hydrodynamik_rumpf", "hydrodynamik_kiel", "hydrodynamik_ruder",
    }
    assert all(np.isfinite(beitrag.wrench.kraft_N).all()
               for beitrag in beitraege)
    assert {blatt._name for blatt in _blaetter(koerper)} == {
        "rumpf", "schwert", "ruder", "pinne", "pinneverlaengerung",
        "mast", "baum", "spriet", "segel", "gummigelenk", "segler",
    }
