"""Erzeugt oder prueft Geometriemetadaten fuer ein Repository-Modellpaket.

Aufruf aus dem Repository-Hauptverzeichnis:
    .venv\\Scripts\\python.exe werkzeuge\\erzeuge_hydrodynamik_metadaten.py yacht1
    .venv\\Scripts\\python.exe werkzeuge\\erzeuge_hydrodynamik_metadaten.py yacht1 --pruefen

Die Erzeugung ist explizit, schreibt nur ein neues Sidecar und ueberschreibt
keine bestehende Datei. Der normale Modellpaketloader bleibt read-only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.hydrodynamik_metadaten import (
    pruefe_geometriemetadaten,
    schreibe_geometriemetadaten,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "modell_id",
        help="ID eines Pakets unter segelphysik/modelle/",
    )
    parser.add_argument(
        "--pruefen", action="store_true",
        help="vorhandenes Sidecar gegen Paket und Quellhashes pruefen",
    )
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", args.modell_id):
        parser.error("Modell-ID muss ein einzelner gueltiger Paket-Slug sein.")

    paket = (ROOT / "segelphysik" / "modelle" / args.modell_id).resolve()
    modellwurzel = (ROOT / "segelphysik" / "modelle").resolve()
    if not paket.is_relative_to(modellwurzel):
        parser.error("Modellpaket muss unter segelphysik/modelle/ liegen.")
    konfiguration = lade_konfig(ROOT / "konfigurationen")
    if args.pruefen:
        pruefe_geometriemetadaten(
            paket, konfiguration.materialien_blocks)
        print("Geometriemetadaten sind aktuell: %s" % paket)
        return 0
    ziel = schreibe_geometriemetadaten(
        paket, konfiguration.materialien_blocks)
    print("Geometriemetadaten geschrieben: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
