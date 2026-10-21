from dataclasses import FrozenInstanceError, replace
import math

import numpy as np
import pytest

from segelphysik.core.kraefte_anzeige import Datenstatus
from segelphysik.core.kraefte_darstellung import (
    BogenVerlauf, KameraAbbildung, SkalenAbbildung, abstand_zum_linienzug_px,
    anfangsreferenz, senkrechter_hebelarm, zahlenwert,
)


@pytest.fixture(params=("python", "cpp"), autouse=True)
def backend(request, monkeypatch):
    monkeypatch.setenv("SEGELPHYSIK_RECHENPFAD", request.param)


@pytest.mark.parametrize("modus", ("linear", "log"))
def test_skala_erfuellt_formel_null_referenz_monotonie_und_begrenzung(modus):
    skala = SkalenAbbildung(100, 180, modus)
    assert skala.abbilden(0).relativ == 0
    assert skala.abbilden(100).relativ == 1
    werte = [skala.abbilden(w).relativ for w in (0, 1e-9, 1e-3, 0.1, 1, 10, 100)]
    assert all(a < b for a, b in zip(werte, werte[1:]))
    erwartet = (0.1 if modus == "linear" else math.log1p(10) / math.log1p(100))
    assert skala.abbilden(10).relativ == pytest.approx(erwartet)
    assert skala.abbilden(100).groesse_px == 180
    assert not skala.abbilden(100).abgeschnitten
    assert skala.abbilden(101).abgeschnitten
    assert skala.abbilden(101).groesse_px == 180
    assert len(skala.legende()) == 3
    assert all(daten == skala.abbilden(wert) for wert, daten in skala.legende())


def test_referenzen_bleiben_ohne_explizite_aktion_fest_und_dimensionen_getrennt():
    kraft = SkalenAbbildung(100, 180)
    moment = SkalenAbbildung(10, 48)
    assert kraft.abbilden(10).groesse_px == 18
    assert moment.abbilden(10).groesse_px == 48
    for _ in range(20):
        assert kraft.abbilden(1000).abgeschnitten
    assert kraft.referenz == 100
    with pytest.raises(FrozenInstanceError):
        kraft.referenz = 200
    assert kraft.neu_einpassen((100, 200, 300)).referenz == pytest.approx(330)
    assert kraft.referenz == 100
    assert kraft.neu_einpassen((0, 0)) is kraft
    assert kraft.neu_einpassen(()).referenz == 100
    assert anfangsreferenz((3, 5), untergrenze=10) == 10
    assert anfangsreferenz((3, 5), manuell=2) == 2
    assert anfangsreferenz((0, 0)) == 1


@pytest.mark.parametrize("modus", ("linear", "log"))
def test_extreme_endliche_skalen_brauchen_keine_falschen_nullen_oder_ueberlaeufe(modus):
    klein = SkalenAbbildung(5e-324, 180, modus)
    assert klein.abbilden(5e-324).groesse_px == 180
    assert klein.abbilden(1e308).abgeschnitten
    gross = SkalenAbbildung(1e308, 180, modus)
    assert gross.abbilden(1e-300).kleinwert
    assert not gross.abbilden(0).kleinwert
    with pytest.raises(ValueError, match="Referenz"):
        gross.neu_einpassen((1.7e308,))


@pytest.mark.parametrize("ungueltig", (-1, float("nan"), float("inf")))
def test_ungueltige_skalenwerte_werden_gemeldet(ungueltig):
    with pytest.raises(ValueError):
        SkalenAbbildung(ungueltig, 180)
    with pytest.raises(ValueError):
        SkalenAbbildung(100, 180).abbilden(ungueltig)
    with pytest.raises(ValueError):
        SkalenAbbildung(100, 180).neu_einpassen((ungueltig,))
    with pytest.raises(ValueError):
        anfangsreferenz((ungueltig,))


def test_zahlenformat_rundet_nur_die_anzeige_und_erhaelt_status():
    assert zahlenwert(1234.567, "N") == "1 235 N"
    assert zahlenwert(-1234.567, "N*m") == "-1 235 Nm"
    assert zahlenwert(-0.0, "N") == "0 N"
    assert zahlenwert(1e-20, "N") == "0 N"
    assert zahlenwert(1.2345678901234567, "N", details=True) == "1 N"
    for status in Datenstatus:
        if status not in (Datenstatus.GUELTIG, Datenstatus.NULL):
            assert zahlenwert(None, "N", status=status) == status.value
    for wert in (None, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            zahlenwert(wert, "N")
    with pytest.raises(ValueError, match="Nullstatus"):
        zahlenwert(1e-30, "N", status=Datenstatus.NULL)


@pytest.mark.parametrize("details", (False, True))
@pytest.mark.parametrize(("wert", "einheit", "erwartet"), (
    (16290, "N", "16 290 N"),
    (-0.4675, "N", "0 N"),
    (0.5698, "N", "1 N"),
    (373.6, "N*m", "374 Nm"),
    (-0.03933, "N*m", "0 Nm"),
    (24.49, "m", "24,49 m"),
    (-0.4509, "m", "-0,45 m"),
    (-0.0001229, "m", "0,00 m"),
    (0, "m", "0,00 m"),
    (1.236, "m", "1,24 m"),
    (1234.567, "m", "1 234,57 m"),
))
def test_feste_anzeigeeinheiten_und_nachkommastellen(
        wert, einheit, erwartet, details):
    assert zahlenwert(wert, einheit, details=details) == erwartet


def test_zeitformat_bleibt_unveraendert():
    assert zahlenwert(47.15, "s") == "47,15 s"
    assert zahlenwert(1.2345678901234567, "s", details=True) == (
        "1,2345678901234567 s")


@pytest.mark.parametrize("dpi", (1.0, 1.5, 2.0))
@pytest.mark.parametrize("parallel", (False, True))
def test_bildschirmmasse_beachten_logische_pixel_zoom_und_kamera(dpi, parallel):
    physische_breite, physische_hoehe = 800 * dpi, 600 * dpi
    kamera = KameraAbbildung(
        (0, 0, 10), (0, 0, 0),
        (physische_breite / dpi, physische_hoehe / dpi), parallel, 3, 60)
    faktor = kamera.welt_pro_pixel((0, 0, 0))
    erwartet = 6 / 600 if parallel else 20 * math.tan(math.pi / 6) / 600
    assert faktor == pytest.approx(erwartet)
    for pixel in (3, 10, 48, 180):
        welt = pixel * faktor
        assert abs(welt / faktor - pixel) <= 1
    zoom = replace(kamera, position=(0, 0, 5), parallel_scale=1.5)
    assert zoom.welt_pro_pixel((0, 0, 0)) == pytest.approx(faktor / 2)


def test_horizontale_projektion_und_nicht_sichtbare_anker():
    kamera = KameraAbbildung((0, 0, 10), (0, 0, 0), (800, 600), False, 3, 60, True)
    assert kamera.welt_pro_pixel((0, 0, 0)) == pytest.approx(
        20 * math.tan(math.pi / 6) / 800)
    with pytest.raises(ValueError, match="vor der Kamera"):
        kamera.welt_pro_pixel((0, 0, 11))
    with pytest.raises(ValueError):
        replace(kamera, viewport_logisch=(0, 600))


@pytest.mark.parametrize("moment", (
    (1, 0, 0), (0, -1, 0), (0, 0, 1), (1, 2, -3), (1e-25, 0, 0),
))
def test_momentenbogen_liegt_in_ebene_und_hat_rechte_hand_drehsinn(moment):
    bogen = BogenVerlauf().bogen(("boot", "moment"), 1, moment, (1, 2, 3), 0.5)
    punkte = np.asarray(bogen.punkte) - (1, 2, 3)
    achse = np.array(moment) / math.hypot(*moment)
    np.testing.assert_allclose(punkte @ achse, 0, rtol=0, atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(punkte, axis=1), 0.5, rtol=0, atol=1e-12)
    drehsinn = np.cross(punkte[:-1], punkte[1:]) @ achse
    assert np.all(drehsinn > 0)
    np.testing.assert_allclose(
        np.cross(achse, punkte[-1]) / 0.5, bogen.richtung,
        rtol=0, atol=1e-12)
    winkel = np.arccos(np.clip(np.sum(
        punkte[:-1] * punkte[1:], axis=1) / 0.25, -1, 1))
    assert math.degrees(sum(winkel)) == pytest.approx(240, abs=1e-9)


def test_bogenphase_ist_stetig_beim_vorzeichenwechsel_und_null_cache():
    verlauf = BogenVerlauf()
    vorher = None
    for winkel in np.linspace(0, math.pi / 2, 100):
        moment = (math.sin(winkel), 0, math.cos(winkel))
        bogen = verlauf.bogen(("boot", "moment"), 1, moment, (0, 0, 0), 1)
        if vorher is not None:
            assert np.linalg.norm(np.array(bogen.punkte[0]) - vorher) < 0.03
        vorher = np.array(bogen.punkte[0])
    vorher = verlauf.bogen(("boot", "moment"), 1, (0, 0, 1), (0, 0, 0), 1)
    assert verlauf.bogen(("boot", "moment"), 1, (0, 0, 0), (0, 0, 0), 1) is None
    nachher = verlauf.bogen(("boot", "moment"), 1, (0, 0, 1), (0, 0, 0), 1)
    assert vorher == nachher
    negativ = verlauf.bogen(("boot", "moment"), 1, (0, 0, -1), (0, 0, 0), 1)
    assert negativ.achse == (0, 0, -1)
    np.testing.assert_allclose(negativ.punkte[0], nachher.punkte[0], atol=1e-12)
    frisch = BogenVerlauf().bogen(("boot", "moment"), 2, (0, 0, 1), (0, 0, 0), 1)
    assert verlauf.bogen(("boot", "moment"), 2, (0, 0, 1), (0, 0, 0), 1) == frisch
    with pytest.raises(ValueError, match="Veraltete"):
        verlauf.bogen(("boot", "moment"), 1, (0, 0, 1), (0, 0, 0), 1)
    verlauf.koerper_entfernen("boot")
    assert verlauf._basen == {} and verlauf._generationen == {}


def test_senkrechter_hebelarm_ist_nicht_der_gesamte_positionsvektor():
    a, b = senkrechter_hebelarm((0, 0, 0), (1, 2, 3), (0, 0, 10))
    assert a == (0, 0, 0)
    assert b == (1, 2, 0)
    assert np.dot(np.array(b) - a, (0, 0, 10)) == 0
    with pytest.raises(ValueError):
        senkrechter_hebelarm((0, 0, 0), (1, 2, 3), (0, 0, 0))


def test_trefferabstand_in_logischen_pixeln_mit_nullsegment_und_mehrfachtreffern():
    linie = [(0, 0), (10, 0), (10, 0)]
    assert abstand_zum_linienzug_px((5, 6), linie) == 6
    assert abstand_zum_linienzug_px((5, 6.01), linie) > 6
    assert abstand_zum_linienzug_px((15, 0), linie) == 5
    assert abstand_zum_linienzug_px((5, 0), [(5, 0)]) == 0
    kandidaten = [i for i, p in enumerate((linie, [(0, 1), (10, 1)]))
                  if abstand_zum_linienzug_px((5, 3), p) <= 6]
    assert kandidaten == [0, 1]
    with pytest.raises(ValueError):
        abstand_zum_linienzug_px((0, 0), [])
