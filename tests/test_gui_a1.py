# -*- coding: utf-8 -*-
"""A1: core/ und render/ bleiben frei von GUI-Importen (AST-Scan)."""
import ast
import os

VERBOTEN = ("PySide6", "pyvistaqt", "PyQt5", "PyQt6")
WURZELN = ("core", "render")
BASIS = os.path.join(os.path.dirname(__file__), "..", "segelphysik")


def _py_dateien(rel):
    ordner = os.path.join(BASIS, rel)
    if not os.path.isdir(ordner):
        return
    for wurzel, _, dateien in os.walk(ordner):
        for name in dateien:
            if name.endswith(".py"):
                yield os.path.join(wurzel, name)


def test_a1_keine_gui_importe_in_core_und_render():
    treffer = []
    for rel in WURZELN:
        for pfad in _py_dateien(rel):
            with open(pfad, "r", encoding="utf-8") as datei:
                baum_ast = ast.parse(datei.read(), pfad)
            for knoten in ast.walk(baum_ast):
                namen = []
                if isinstance(knoten, ast.Import):
                    namen = [a.name for a in knoten.names]
                elif isinstance(knoten, ast.ImportFrom) and knoten.module:
                    namen = [knoten.module]
                for n in namen:
                    if any(n.startswith(v) for v in VERBOTEN):
                        treffer.append((pfad, n))
    assert not treffer, "GUI-Importe in Kerncode: %r" % (treffer,)
