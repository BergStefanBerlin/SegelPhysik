"""Misst die Boot-Referenzwerte neu (nach Geometrieaenderungen).

Verwendung (aus dem Repo-Wurzelverzeichnis):
    python werkzeuge/referenzwerte.py

Druckt die Ist-Werte von Masse, CM-Tiefe und diag(I) sowie paste-ready
Assert-Zeilen fuer test_tc_d5_schalenboot_kennzahlen (tests/test_koerper.py).
Nach dem Einsetzen: das Plausibilitaetsband in D5 wieder durch die harten
Referenzen ersetzen (Projektregel: messen, nicht schaetzen).
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core import fabriken


def main():
    konfig = lade_konfig(os.path.join(ROOT, "konfigurationen"))
    boot, r_modell = fabriken.baue_boot(konfig)
    d = np.diag(boot.traegheitstensor)
    print("Masse     : %.6f kg" % boot.masse)
    print("r_modell  : (%.6f, %.6f, %.6f) m" % tuple(r_modell))
    print("diag(I)   : (%.3f, %.3f, %.3f) kg*m^2" % tuple(d))
    print()
    print("Paste-ready Zeilen fuer test_tc_d5_schalenboot_kennzahlen:")
    print("    assert abs(boot.masse - %.4f) < 0.01" % boot.masse)
    print("    assert abs(r_modell[2] - (%.6f)) < 0.001" % r_modell[2])
    print("    assert abs(d[0] - %.3f) < 0.05" % d[0])
    print("    assert abs(d[1] - %.3f) < 0.05" % d[1])
    print("    assert abs(d[2] - %.3f) < 0.05" % d[2])


if __name__ == "__main__":
    main()
