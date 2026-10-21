"""Geometrie-/Darstellungspfade importieren keine entfernten Legacy-Physikmodule."""
import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
QUELLEN = os.path.join("code", "python", "segelphysik")
NEU = [os.path.join(QUELLEN, rel) for rel in (
    "demo_app.py", "steuerung.py", "grafik_bruecke.py",
    "core/bewegung.py", "core/koerper_formen.py")]
VERBOTEN = ["forces", "solver", "bodies", "sph", "fluid"]


def test_keine_physik_referenzen():
    for rel in NEU:
        pfad = os.path.join(ROOT, rel)
        assert os.path.isfile(pfad), f"fehlt: {rel}"
        with open(pfad, encoding="utf-8") as datei:
            baum = ast.parse(datei.read(), filename=pfad)
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Import):
                namen = [alias.name for alias in knoten.names]
            elif isinstance(knoten, ast.ImportFrom):
                modul = knoten.module or ""
                namen = [modul, *(f"{modul}.{alias.name}" for alias in knoten.names)]
            else:
                continue
            for name in namen:
                assert not set(name.split(".")) & set(VERBOTEN), (
                    f"{rel}:{knoten.lineno} importiert Legacy-Physik: {name}")


def test_neue_dateien_existieren():
    for rel in NEU:
        assert os.path.isfile(os.path.join(ROOT, rel)), rel
