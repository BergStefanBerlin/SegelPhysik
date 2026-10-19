"""Validierte, modellbezogene Besatzungseinstellungen ohne Paketänderung."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import tempfile


def seglerwerte_pruefen(werte):
    if not isinstance(werte, dict) or set(werte) != {
            "masse_kg", "position_rumpf_m"}:
        raise ValueError("Segler benötigt masse_kg und position_rumpf_m")
    masse = werte["masse_kg"]
    position = werte["position_rumpf_m"]
    if not isinstance(position, (list, tuple)) or len(position) != 3:
        raise ValueError("Seglerposition benötigt drei Koordinaten in Metern")
    for zahl in (masse, *position):
        if isinstance(zahl, bool) or not isinstance(zahl, (int, float)):
            raise ValueError("Seglerwerte müssen endliche Zahlen sein")
        try:
            endlich = math.isfinite(zahl)
        except OverflowError as fehler:
            raise ValueError("Seglerwerte müssen endliche Zahlen sein") from fehler
        if not endlich:
            raise ValueError("Seglerwerte müssen endliche Zahlen sein")
    if masse <= 0:
        raise ValueError("Seglermasse muss positiv sein")
    return {"masse_kg": float(masse),
            "position_rumpf_m": [float(x) for x in position]}


class SeglerEinstellungen:
    def __init__(self, pfad=None):
        self.pfad = Path(pfad) if pfad is not None else None
        self._modelle = {}
        if self.pfad is not None and self.pfad.exists():
            try:
                from .modell_lader import _doppelter_schluessel
                daten = json.loads(
                    self.pfad.read_text(encoding="utf-8"),
                    object_pairs_hook=_doppelter_schluessel)
                if (not isinstance(daten, dict)
                        or set(daten) != {"schema_version", "modelle"}
                        or daten["schema_version"] != "1.0"
                        or not isinstance(daten["modelle"], dict)):
                    raise ValueError("Seglereinstellungen: Schema 1.0 erwartet")
                self._modelle = {
                    name: seglerwerte_pruefen(werte)
                    for name, werte in daten["modelle"].items()
                }
            except (OSError, UnicodeError, ValueError) as fehler:
                raise ValueError(
                    "Seglereinstellungen %s: %s" % (self.pfad, fehler)) from fehler

    def werte(self, modell_id, masse_kg, position_rumpf_m):
        werte = self._modelle.get(
            modell_id, {"masse_kg": masse_kg,
                        "position_rumpf_m": position_rumpf_m})
        return seglerwerte_pruefen(werte)

    def setzen(self, modell_id, werte):
        if self.pfad is None:
            raise ValueError("Reine Paketdefaults haben keinen Speicherpfad")
        neu = dict(self._modelle)
        neu[modell_id] = seglerwerte_pruefen(werte)
        daten = {"schema_version": "1.0", "modelle": neu}
        temp = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=self.pfad.parent,
                    prefix=self.pfad.name + ".", suffix=".tmp",
                    delete=False) as datei:
                temp = Path(datei.name)
                json.dump(daten, datei, ensure_ascii=False, indent=2,
                          allow_nan=False)
                datei.write("\n")
                datei.flush()
                os.fsync(datei.fileno())
            os.replace(temp, self.pfad)
        except OSError as fehler:
            raise ValueError(
                "Seglereinstellungen nicht gespeichert: %s" % fehler) from fehler
        finally:
            if temp is not None and temp.exists():
                temp.unlink()
        self._modelle = neu
