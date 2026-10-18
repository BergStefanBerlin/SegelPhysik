"""M0-Abnahme: V3-Module duerfen KEINE Physik-Module referenzieren."""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
NEU = ["code/demo_app.py", "code/steuerung.py",
       "code/grafik_bruecke.py",
       "code/core/bewegung.py", "code/core/koerper_formen.py"]
VERBOTEN = ["forces", "solver", "bodies", "sph", "fluid"]


def test_keine_physik_referenzen():
    for rel in NEU:
        pfad = os.path.join(ROOT, rel)
        assert os.path.isfile(pfad), f"fehlt: {rel}"
        with open(pfad, encoding="utf-8") as datei:
            src = datei.read()
        for schlecht in VERBOTEN:
            treffer = re.findall(r"(?:import|from)\s+\S*" + schlecht, src)
            assert not treffer, f"{rel} referenziert Physik ({schlecht}): {treffer}"


def test_neue_dateien_existieren():
    for rel in NEU:
        assert os.path.isfile(os.path.join(ROOT, rel)), rel
