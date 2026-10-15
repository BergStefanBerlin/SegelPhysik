import math

import numpy as np
import pytest

from segelphysik.core import koerper_formen as kf
from segelphysik.core import formerkennung as fe
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.statusanzeige import status_aus_ergebnis


@pytest.mark.parametrize("name,netz,erwartet", [
    ("kugel", lambda: kf.build_sphere(1.0), fe.KUGEL),
    ("kugel klein", lambda: kf.build_sphere(0.003), fe.KUGEL),
    ("zylinder stehend", lambda: kf.build_cylinder(0.5, 2.0), fe.ZYLINDER),
    ("zylinder liegend",
     lambda: kf.build_cylinder(0.5, 2.0, lage="liegend"), fe.ZYLINDER),
    # gleiche Hauptmomente wie eine Kugel, aber kein Rotationskoerper-Kugel
    ("zylinder H2=3R2", lambda: kf.build_cylinder(1.0, math.sqrt(3)),
     fe.ZYLINDER),
    ("zylinder flach", lambda: kf.build_cylinder(1.0, 0.1), fe.ZYLINDER),
    ("kegel", lambda: kf.build_cone(2.0, 1.0), fe.KEGEL),
    ("wuerfel", lambda: kf.build_box(2, 2, 2), fe.BELIEBIG),
    ("quader", lambda: kf.build_box(2, 1, 3), fe.BELIEBIG),
    ("pyramide", lambda: kf.build_pyramid(2, 2), fe.BELIEBIG),
    ("platte", lambda: kf.build_plate(2, 1, 0.02), fe.BELIEBIG),
    ("sechskantstab", lambda: kf.build_hexprism(0.004, 0.17, 0.015),
     fe.BELIEBIG),
])
def test_klassifiziere(name, netz, erwartet):
    assert fe.klassifiziere(*netz()) == erwartet


def test_gedrehtes_netz_wird_gleich_erkannt():
    v, f = kf.build_cylinder(0.5, 2.0)
    w = np.array([1.0, 2.0, 3.0]); w /= np.linalg.norm(w)
    k = np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])
    r = np.eye(3) + math.sin(0.9) * k + (1 - math.cos(0.9)) * (k @ k)
    assert fe.klassifiziere(v @ r.T, f) == fe.ZYLINDER


def test_koerper_der_koerper_json():
    konfig = lade_konfig("konfigurationen")
    erwartet = {"kugel": fe.KUGEL, "rolle": fe.ZYLINDER, "kegel": fe.KEGEL,
                "quader": fe.BELIEBIG, "pyramide": fe.BELIEBIG,
                "platte": fe.BELIEBIG, "bleistift": fe.BELIEBIG,
                "unregelmaessig": fe.BELIEBIG}
    for name, form in erwartet.items():
        koerper, _ = baue_summenkoerper(konfig, name)
        assert fe.klassifiziere_koerper(koerper) == form, name


def test_zusammengesetzter_koerper_ist_beliebig():
    konfig = lade_konfig("konfigurationen")
    koerper, _ = baue_summenkoerper(konfig, "yacht1")
    assert fe.klassifiziere_koerper(koerper) == fe.BELIEBIG


@pytest.mark.parametrize("form,text", [
    (fe.KUGEL, "rotationsneutral (Kugel)"),
    (fe.ZYLINDER, "rollneutral (Zylinder)"),
    (fe.KEGEL, "rollneutral (Kegel)"),
    (fe.ROTATIONSKOERPER, "rollneutral (Rotationskörper)"),
    (fe.BELIEBIG, "rollneutral"),
])
def test_status_neutral_nach_form(form, text):
    assert status_aus_ergebnis({"neutral": True}, form=form) == (text, "ok")
