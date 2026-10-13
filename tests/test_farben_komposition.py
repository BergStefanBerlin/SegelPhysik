"""Block I - Farb-Kanal ueber das MATERIAL (Spec P4, Reform 12.10.)
plus TC-C6 (Verschachtelungstiefe) und TC-H7 (Migrations-Gegenprobe).

Regeln: Farbe ist Stoff-Eigenschaft -> materialien.json. Blatt mit
'material' traegt KEINE Farben; ohne 'material' sind die drei Direktwerte
Pflicht. Referenzwerte analytisch oder gemessen (R5).
"""
import json, os
import numpy as np
import pytest

from segelphysik.core import fabriken
from segelphysik.core.koerper import Koerper, helle_auf
from segelphysik.core.konfig_lader import KonfigFehler, lade_konfig

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def konfig_real():
    """Die echte Arbeits-Konfiguration aus konfigurationen/."""
    return lade_konfig(os.path.join(REPO_ROOT, "konfigurationen"))


def _temp_konfig(tmp_path, mat, kor):
    with open(os.path.join(str(tmp_path), "materialien.json"), "w", encoding="utf-8") as f:
        json.dump(mat, f)
    with open(os.path.join(str(tmp_path), "koerper.json"), "w", encoding="utf-8") as f:
        json.dump(kor, f)
    return str(tmp_path)


def _basis():
    mat = {"materialien": {"Test": {"dichte_kg_pro_m3": 1000, "farbe": "#cccccc",
                                    "farbe_unter_wasser": "#999999"}},
           "wasser": {"dichten_kg_pro_m3": {"Suess": 1000}, "standard": "Suess"}}
    kor = {"summenkoerper": {
               "yacht1": {"teile": [{"name": "kiel", "material": "Test"}]}},
           "darstellung": {"delta_helligkeit_unterwasser": 0.4,
                           "farbe_standard": "#c9c9c9"}}
    return mat, kor


def _blaetter(k):
    if not k.teile:
        yield k
    for kind, _rel in k.teile:
        yield from _blaetter(kind)


def test_i1_farben_aus_materialtabelle(konfig_real):
    """Oberwasser-Farben kommen aus der Materialtabelle (P4) - der Test liest
    die Erwartung AUS DER TABELLE, nicht hartkodiert (palettfest)."""
    boot, _r = fabriken.baue_boot(konfig_real)
    gef = {}
    for b in _blaetter(boot):
        gef[b.farbe] = gef.get(b.farbe, 0) + 1
    f_gfk   = konfig_real.farben_von("GfK")[0]
    f_alu   = konfig_real.farben_von("Aluminium")[0]
    f_stahl = konfig_real.farben_von("Stahl")[0]
    f_blei  = konfig_real.farben_von("Blei")[0]
    assert gef.get(f_gfk) == 2, "rumpf+ruder ueber GfK"
    assert gef.get(f_alu) == 2, "mast+boom ueber Aluminium"
    assert gef.get(f_stahl) == 1, "kiel ueber Stahl"
    assert gef.get(f_blei) == 1, "bulb ueber Blei"
    # Segel: Direkt-Tripel, Farbe steht am Blatt in koerper.json
    assert gef.get("#fbfaf7") == 2, "segel ueber Direkt-Tripel"


def test_i2_unterwasser_farben_exakt_uebernommen(konfig_real):
    """Unterwasserfarben exakt aus der Tabelle (explizit gesetzt => keine
    automatische Aufhellung) - Erwartung tabellgetrieben."""
    boot, _r = fabriken.baue_boot(konfig_real)
    gef = {}
    for b in _blaetter(boot):
        gef[b.farbe_unter_wasser] = gef.get(b.farbe_unter_wasser, 0) + 1
    for name in ("GfK", "Stahl", "Blei", "Aluminium"):
        uw = konfig_real.farben_von(name)[1]
        assert gef.get(uw) == gef.get(uw, 0) or gef.get(uw), "%s: UW-Farbe fehlt" % name
        assert uw in gef, "%s: Unterwasserfarbe %s fehlt am Boot" % (name, uw)
    # Segel (Direkt-Tripel): beide Segelblaetter tragen die Direkt-UW-Farbe
    assert gef.get("#d9d7cf") == 2


def test_i3_ohne_expizite_unterwasserfarbe_wird_aufgehellt():
    v = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
                  [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]], float)
    quads = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(3,0,4,7)]
    f = []
    for a,b,c,d in quads:
        f += [[a,b,c],[a,c,d]]
    k = Koerper(form=(v, np.array(f, np.int64)), dichte=1000.0,
                farbe="#c9c9c9", delta_helligkeit=0.4)
    assert k.unterwasser_farbe() == helle_auf("#c9c9c9", 0.4)


def test_i4_farbe_am_blatt_trotz_material_fehler(tmp_path):
    mat, kor = _basis()
    kor["summenkoerper"]["yacht1"]["teile"][0]["farbe"] = "#ff0000"
    with pytest.raises(KonfigFehler):
        lade_konfig(_temp_konfig(tmp_path, mat, kor))


def test_i5_material_ohne_farbe_in_tabelle_fehler(tmp_path):
    mat, kor = _basis()
    del mat["materialien"]["Test"]["farbe"]
    with pytest.raises(KonfigFehler):
        lade_konfig(_temp_konfig(tmp_path, mat, kor))


def test_i6_mischform_material_und_dichte_fehler(tmp_path):
    mat, kor = _basis()
    kor["summenkoerper"]["yacht1"]["teile"][0]["dichte_kg_pro_m3"] = 500
    with pytest.raises(KonfigFehler):
        lade_konfig(_temp_konfig(tmp_path, mat, kor))


def test_i7_direkttripel_vollstaendig_pflicht(tmp_path):
    """Direkt-Tripel ohne 'farbe' ist unvollstaendig -> Fehler."""
    mat, kor = _basis()
    blatt = kor["summenkoerper"]["yacht1"]["teile"][0]
    del blatt["material"]
    blatt["dichte_kg_pro_m3"] = 1000
    blatt["farbe_unter_wasser"] = "#999999"   # 'farbe' FEHLT absichtlich
    with pytest.raises(KonfigFehler):
        lade_konfig(_temp_konfig(tmp_path, mat, kor))


def test_i8_direkttripel_valide_und_farben_am_koerper(tmp_path):
    mat, kor = _basis()
    blatt = kor["summenkoerper"]["yacht1"]["teile"][0]
    del blatt["material"]
    blatt.update({"dichte_kg_pro_m3": 1000,
                  "farbe": "#123456",
                  "farbe_unter_wasser": "#223344"})
    k = lade_konfig(_temp_konfig(tmp_path, mat, kor))
    boot, _r = fabriken.baue_boot(k)
    blaetter = list(_blaetter(boot))
    assert blaetter[0].farbe == "#123456"
    assert blaetter[0].unterwasser_farbe() == "#223344"


def test_tc_c6_verschachtelungstiefe_und_additivitaet(konfig_real):
    boot, _r = fabriken.baue_boot(konfig_real)
    def tiefe(k):
        if not k.teile:
            return 1
        return 1 + max(tiefe(kind) for kind, _r2 in k.teile)
    assert tiefe(boot) == 3, "boot->gruppe->blatt = Tiefe 3"
    blaetter = list(_blaetter(boot))
    assert abs(sum(b.masse for b in blaetter) - boot.masse) < 1e-6


def test_tc_h7_migrationsgegenprobe_schalenboot(konfig_real):
    """Bootswerte muessen ueber ALLE Schema-Reformen identisch bleiben."""
    boot, r_modell = fabriken.baue_boot(konfig_real)
    # Fock v15 (Schritt 4.2): untere Ecken +0.38 m -> Masse 459.4368 - 0.29362
    # = 459.1432 kg (Delta analytisch: 2 * 0.5 kg/m^2 * 0.293615 m^2).
    assert abs(boot.masse - 459.1432) < 0.01
    assert r_modell[2] < -0.4, "CM deutlich unter der Wasserlinie"


def test_i9_grundkoerper_farben_aus_konfig(konfig_real):
    """Die drei Demo-Grundkoerper lesen ihre Farben aus darstellung.grundkoerper."""
    gk = konfig_real.grundkoerper_farben
    assert {s for s in gk if not s.startswith("_")} == {"cone", "box", "pyramid"}
    assert fabriken.baue_kegel(konfig_real).farbe == gk["cone"]
    assert fabriken.baue_quader(konfig_real).farbe == gk["box"]
    assert fabriken.baue_pyramide(konfig_real).farbe == gk["pyramid"]
