"""Statustext der statischen Darstellung (Overlay unten links)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import numpy as np

from segelphysik.core import statusanzeige as sa
from segelphysik.core import auftrieb as au
from segelphysik.core import koerper_formen as formen
from segelphysik.core.koerper import Koerper
from segelphysik.core.statisch import SolverFehler

G = 9.81


def test_ergebnis_zustaende():
    assert sa.status_aus_ergebnis({}) == ("stabil", "ok")
    assert sa.status_aus_ergebnis({"stagnation": True}) == (
        "stabile Näherung", "ok")
    assert sa.status_aus_ergebnis({"neutral": True}) == (
        "rollneutral (Zylinder)", "ok")
    assert sa.status_aus_ergebnis({"neutral": True}, True) == (
        "rotationsneutral (Kugel)", "ok")


def test_fehler_zustaende():
    def f(status):
        return SolverFehler("x", status=status, diagnose={})
    assert sa.status_aus_fehler(f("instabile_lage")) == ("instabil", "hinweis")
    assert sa.status_aus_fehler(f("stagnation"), True) == (
        "Näherungslösung", "hinweis")
    assert sa.status_aus_fehler(f("budget_erschoepft"), False) == (
        "nicht lösbar", "problem")
    assert sa.status_aus_fehler(f("ungueltige_rechenergebnisse"), True) == (
        "nicht lösbar", "problem")
    assert sa.status_aus_fehler(f("sinkt")) == ("Sinken", "hinweis")
    assert sa.status_aus_fehler(f("schwebt")) == ("Schweben", "hinweis")
    assert sa.status_aus_fehler(ValueError("boom")) == ("Fehler", "problem")


def test_rotationssymmetrie_aus_traegheit():
    assert sa.ist_rotationssymmetrisch(np.eye(3) * 5.0)
    assert not sa.ist_rotationssymmetrisch(np.diag([1.0, 2.0, 3.0]))
    assert not sa.ist_rotationssymmetrisch(None)


def test_schwimmpruefung_sinken_und_tragen():
    schwer = Koerper(form=formen.bau_quader(1.0, 1.0, 1.0), dichte=2000.0)
    leicht = Koerper(form=formen.bau_quader(1.0, 1.0, 1.0), dichte=500.0)
    fs = au.baue_kraftfunktion(schwer, rho_w=1000.0, g=G, pfad="exakt_union")
    fl = au.baue_kraftfunktion(leicht, rho_w=1000.0, g=G, pfad="exakt_union")
    assert sa.schwimmpruefung(fs, schwer, schwer.masse, G) == "sinkt"
    assert sa.schwimmpruefung(fl, leicht, leicht.masse, G) is None


def test_overlay_texte_und_schweren():
    for text, schwere in (sa.BERECHNUNG_LAEUFT, sa.KEIN_HAUPTKOERPER,
                          sa.KOERPER_FEHLT):
        assert text and schwere == "info"
