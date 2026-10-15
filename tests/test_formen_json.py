"""Alle Formtypen der koerper.json: Loader, Fabrik, Geometrie."""
import math
import numpy as np
import pytest

from segelphysik.core import koerper_formen as kf
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig


def _volumen(v, f):
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


@pytest.mark.parametrize("bau,erwartet,tol", [
    (lambda: kf.build_sphere(1.0), 4/3*math.pi, 0.02),
    (lambda: kf.build_cylinder(0.5, 2.0), math.pi*0.25*2.0, 0.005),
    (lambda: kf.build_cylinder(0.5, 2.0, lage="liegend"), math.pi*0.5, 0.005),
    (lambda: kf.build_plate(2.0, 1.0, 0.02), 0.04, 1e-9),
    (lambda: kf.build_hexprism(0.004, 0.17, 0.015),
     1.5*math.sqrt(3)*0.004**2*(0.155 + 0.015/3), 1e-9),
])
def test_volumen_positiv_und_analytisch(bau, erwartet, tol):
    v, f = bau()
    assert _volumen(v, f) == pytest.approx(erwartet, rel=tol)


def test_liegender_zylinder_achse_x():
    v, _ = kf.build_cylinder(0.5, 2.0, lage="liegend")
    assert np.ptp(v[:, 0]) == pytest.approx(2.0)
    assert np.ptp(v[:, 2]) == pytest.approx(1.0, rel=0.01)


def test_polyhedron_konvexe_huelle_wuerfel():
    ecken = [[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    v, f = kf.build_polyhedron(ecken)
    assert _volumen(v, f) == pytest.approx(1.0)
    assert np.abs(v.mean(axis=0)).max() < 1e-9


def test_polyhedron_ebene_punkte_abgelehnt():
    with pytest.raises(ValueError):
        kf.build_polyhedron([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])


def test_echte_koerper_json_laedt_und_baut():
    konfig = lade_konfig("konfigurationen")
    formkoerper = [n for n, e in konfig.summenkoerper.items() if "form" in e]
    assert {"kugel", "rolle", "platte", "bleistift",
            "unregelmaessig"} <= set(formkoerper)
    for name in formkoerper:
        koerper, _ = baue_summenkoerper(konfig, name)
        assert koerper.masse > 0


def test_unbekannte_form_wird_abgelehnt(tmp_path):
    from segelphysik.core.konfig_lader import KonfigFehler
    import json
    import shutil
    ziel = tmp_path / "k"
    shutil.copytree("konfigurationen", ziel)
    pfad = ziel / "koerper.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    daten["summenkoerper"]["kegel"]["form"] = {"typ": "torus", "R_m": 1}
    pfad.write_text(json.dumps(daten), encoding="utf-8")
    with pytest.raises(KonfigFehler, match="torus"):
        lade_konfig(str(ziel))
