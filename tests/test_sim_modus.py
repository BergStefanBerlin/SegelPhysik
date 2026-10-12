"""Testblock M - Simulationsmodi (P5c Schritt 1: nur Umschaltung)."""
import pytest

from segelphysik.core.sim_modus import Modus, SimSteuerung, MODUS_TASTEN


def test_m1_start_im_ruhemodus():
    s = SimSteuerung()
    assert s.modus is Modus.RUHEND
    assert s.wechsel == 0


def test_m2_alle_sechs_uebergaenge():
    for quelle in Modus:
        for ziel_taste, ziel in MODUS_TASTEN.items():
            s = SimSteuerung(start=quelle)
            geaendert = s.taste(ziel_taste)
            assert geaendert == (ziel is not quelle)
            assert s.modus is (ziel if geaendert else quelle)


def test_m3_gleiche_taste_ist_noop():
    for quelle in Modus:
        s = SimSteuerung(start=quelle)
        taste = [t for t, m in MODUS_TASTEN.items() if m is quelle][0]
        assert s.taste(taste) is False
        assert s.modus is quelle
        assert s.wechsel == 0


def test_m4_unbekannte_taste_aendert_nichts():
    s = SimSteuerung()
    for t in ("x", "1", "", "R", "S"):
        assert s.taste(t) is False
    assert s.modus is Modus.RUHEND
    assert s.wechsel == 0


def test_m5_zweiton_folge_und_zaehler():
    s = SimSteuerung()
    folge = ["s", "z", "r", "z", "s", "r"]
    erwarte = [Modus.STATISCH, Modus.ECHTZEIT, Modus.RUHEND,
               Modus.ECHTZEIT, Modus.STATISCH, Modus.RUHEND]
    for t, m in zip(folge, erwarte):
        assert s.taste(t) is True
        assert s.modus is m
    assert s.wechsel == 6


def test_m6_textformat():
    s = SimSteuerung()
    assert s.text() == "MODUS: RUHEND"
    s.taste("z")
    assert s.text() == "MODUS: ECHTZEIT"


def test_m7_start_nur_gueltige_modi():
    with pytest.raises(ValueError):
        SimSteuerung(start="statisch")
