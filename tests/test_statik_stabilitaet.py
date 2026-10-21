"""Statische Stabilitaet: Flag, Loesungsauswahl und Kegel-Seitenlage (E1-E3)."""
from __future__ import annotations
import math
import numpy as np
import pytest

from segelphysik.core.statisch_robust import loese_robust
from segelphysik.core.stoerung import beste_loesung, kontakt_start
from segelphysik.core import koerper_formen as formen
from segelphysik.core.koerper import Koerper
from segelphysik.core import auftrieb as au

G = 9.80665; RHO_W = 1000.0; H_AUF = 0.05

class _V3:
    def __init__(self, a): self.a = np.asarray(a, float)
    def as_array(self): return self.a
class _Erg:
    def __init__(self, F_A, M, K, V):
        self.F_A, self.M, self.K = _V3(F_A), _V3(M), _V3(K); self.V_tauch = V

def test_e1_stabil_flag_wird_gesetzt():
    """Glatte Funktion: Loesung hat stabil=True und gm>0."""
    def kf(l):
        z, phi = float(l[0]), float(l[1])
        T = max(min(1.0 - z, 2.0), 0.0)
        V = 4.0 * 1.2 * T
        M = -9810.0 * V * 0.5 * math.sin(phi)
        return _Erg([0,0,9810.0*V],[M,0,0],[0,0,z-1.0+T/2],V)
    L = loese_robust(kf, 6000.0, G, start=(0.0, 0.0))
    assert L["stabil"] is True and L["gm"] is not None and L["gm"] > 0.0

def test_e2_beste_loesung_stabil_ohne_gm():
    """Rev-E-Luecke: stabil=True, gm=None (Voxel-Treppe) wird akzeptiert."""
    stabil_ohne_gm = {"z": -0.4, "gm": None, "stabil": True, "neutral": False}
    neutral = {"z": -0.5, "gm": None, "stabil": False, "neutral": True}
    instabil = {"z": -0.1, "gm": None, "stabil": False, "neutral": False}
    assert beste_loesung([stabil_ohne_gm, instabil])["z"] == -0.4
    assert beste_loesung([instabil]) is None
    mit_gm = {"z": -0.3, "gm": 0.2, "stabil": True, "neutral": False}
    assert beste_loesung([stabil_ohne_gm, mit_gm])["z"] == -0.3
    assert beste_loesung([neutral])["z"] == -0.5

@pytest.mark.integration
@pytest.mark.slow
def test_e3_kegel_liegt_seitlich_stabil():
    """Der physikalische Kernbefund (Kalibrierlauf): ein homogener Kegel
    (rho=500) liegt SEITLICH im Wasser (phi* nahe 90 Grad) - und diese
    Lage ist stabil, wie ein treibender Baumstamm. Echter Voxel-Kern."""
    k = Koerper(form=formen.bau_kegel(2.0, 1.0), dichte=500.0)
    kf = au.baue_kraftfunktion(k, rho_w=RHO_W, g=G, aufloesung=H_AUF)
    zk, phik = kontakt_start(lambda l: kf((l[0], l[1], 0.0)), 0.3, 0.5)
    L = loese_robust(lambda l: kf((l[0], l[1], 0.0)), k.masse, G,
                     start=(zk, phik))
    phi_mod = abs(math.degrees(L["phi"])) % 180.0
    abstand_zu_90 = abs(phi_mod - 90.0)
    assert abstand_zu_90 < 12.0, \
        "Erwartet Seitlage (nahe 90 Grad), bekommen phi*=%.2f Grad" \
        % math.degrees(L["phi"])
    assert L["restkraft"] < 0.05 * k.masse * G
    erg = kf((L["z"], L["phi"], 0.0))
    assert abs(erg.F_A.as_array()[2] - k.masse * G) < 0.05 * k.masse * G
