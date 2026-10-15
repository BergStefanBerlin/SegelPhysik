"""Schritt-3-Tests (P5a/P5b): Layer-Registry + Hauptachsen.

Rein numpy-basiert (pyvista-frei) - die Overlay-Geometrie (Eigenvektoren
von I_S, r_S-Marker-Anker) ist rein rechnerisch pruefbar. Referenzwerte
analytisch hergeleitet (R5), nie mit derselben Funktion.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import numpy as np

from segelphysik.core.overlays import (LayerRegistry, hauptachsen,
                                       LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                                       LAYER_KRAEFTE, LAYER_MOMENTE)
from segelphysik.core.koerper import Koerper
from segelphysik.core import koerper_formen as formen

TOL = 1e-6


def _rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def test_g1_layer_registry_global_und_unabhaengig():
    reg = LayerRegistry()
    assert not reg.ist_an(LAYER_SCHWERPUNKT)
    assert not reg.ist_an(LAYER_HAUPTACHSEN)
    assert not reg.ist_an(LAYER_KRAEFTE)
    assert not reg.ist_an(LAYER_MOMENTE)
    assert reg.umschalten(LAYER_SCHWERPUNKT) is True
    assert reg.ist_an(LAYER_SCHWERPUNKT)
    assert not reg.ist_an(LAYER_HAUPTACHSEN)     # unabhaengig
    assert reg.umschalten(LAYER_HAUPTACHSEN) is True
    # Layer bleiben unabhaengig voneinander schaltbar.
    assert reg.zustand() == {LAYER_SCHWERPUNKT: True, LAYER_HAUPTACHSEN: True,
                             LAYER_KRAEFTE: False, LAYER_MOMENTE: False,
                             'fremdkraft': False}
    reg.setzen(LAYER_SCHWERPUNKT, False)
    assert not reg.ist_an(LAYER_SCHWERPUNKT)


def test_g2_wuerfel_hauptachsen_orthonormal():
    # Wuerfel 2x2x2, dichte 1000 -> m = 8000 kg; I = m*a^2/6 = 5333.333...
    k = Koerper(form=formen.bau_quader(2.0, 2.0, 2.0), dichte=1000.0)
    werte, vektoren = hauptachsen(k.traegheitstensor)
    erwartet = 8000.0 * 4.0 / 6.0
    assert np.allclose(werte, erwartet, rtol=TOL)
    assert np.allclose(vektoren.T @ vektoren, np.eye(3), atol=TOL)
    assert np.allclose(np.linalg.norm(vektoren, axis=0), 1.0, atol=TOL)


def test_g3_quader_achsenparallel_hauptachsen_konstruktionsachsen():
    # Quader 2x1x0.5, dichte 1000 -> m = 1000 kg
    # I_x = m(b^2+c^2)/12 = 104.1667; I_y = m(a^2+c^2)/12 = 354.1667
    # I_z = m(a^2+b^2)/12 = 416.6667
    k = Koerper(form=formen.bau_quader(2.0, 1.0, 0.5), dichte=1000.0)
    werte, vektoren = hauptachsen(k.traegheitstensor)
    erwartet = np.array([416.6666667, 354.1666667, 104.1666667])
    assert np.allclose(werte, erwartet, rtol=TOL)
    assert abs(abs(vektoren[2, 0]) - 1.0) < TOL   # groesstes Moment: z
    assert abs(abs(vektoren[1, 1]) - 1.0) < TOL   # mittleres: y
    assert abs(abs(vektoren[0, 2]) - 1.0) < TOL   # kleinstes: x


def test_g4_gedrehter_quader_hauptachsen_weichen_ab():
    # Quader 2x1x0.5 um 30 Grad um z gedreht (rel_Pose). Hauptachsen = die
    # EIGENEN Achsen des Quaders (30 Grad gedreht), NICHT die Konstruktions-
    # achsen des Verbands. Analytisch: I_ges = R diag(104.17,354.17,416.67) R^T
    teil = Koerper(form=formen.bau_quader(2.0, 1.0, 0.5), dichte=1000.0)
    R = _rot_z(np.radians(30.0))
    k = Koerper(teile=[(teil, (R, np.zeros(3)))])
    werte, vektoren = hauptachsen(k.traegheitstensor)
    erwartet = np.array([416.6666667, 354.1666667, 104.1666667])
    assert np.allclose(werte, erwartet, rtol=TOL)
    assert abs(abs(vektoren[2, 0]) - 1.0) < TOL          # z bleibt Hauptachse
    rot_y = np.array([-np.sin(np.radians(30)), np.cos(np.radians(30)), 0.0])
    rot_x = np.array([np.cos(np.radians(30)), np.sin(np.radians(30)), 0.0])
    assert abs(abs(np.dot(vektoren[:, 1], rot_y)) - 1.0) < TOL
    assert abs(abs(np.dot(vektoren[:, 2], rot_x)) - 1.0) < TOL


def test_g5_schwerpunkt_marker_anker_in_welt():
    # Der r_S-Marker sitzt am Koerper-Schwerpunkt in Welt = position
    # (Schwerpunktframe-Ursprung == CM, P1).
    k = Koerper(form=formen.bau_quader(2.0, 2.0, 2.0), dichte=1000.0)
    k.setze_pose([1.0, -2.0, 3.0])
    welt = k.punkte_in_welt()
    assert np.allclose(welt.mean(axis=0), [1.0, -2.0, 3.0], atol=TOL)
    assert np.allclose(k.position, [1.0, -2.0, 3.0], atol=TOL)
