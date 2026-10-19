"""Erstellt oder prüft eingefrorene exakte Hydrostatikreferenzen für v0.9.

Aufruf aus dem Repository: python werkzeuge\\pruefe_genauigkeit_v09.py
Die Referenz darf nur bewusst mit --schreiben neu erstellt werden.
Es wird kein Näherungsverfahren aktiviert oder freigegeben.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segelphysik.core.auftrieb import baue_kraftfunktion_6dof
from segelphysik.core.fabriken import baue_modellpaket
from segelphysik.core.genauigkeit_v09 import GenauigkeitV09
from segelphysik.core.konfig_lader import lade_konfig, lade_physik
from segelphysik.core.modell_lader import lade_modellpaket
from segelphysik.core.segler_einstellungen import SeglerEinstellungen

ZIEL = (ROOT / "doc" / "WegZuV1.0" / "Revisionslog" / "zuV0.9"
        / "Messungen" / "Genauigkeit_Referenzfaelle_v0.9.json")


def _quaternion(roll, nick):
    r, p = math.radians(roll) / 2, math.radians(nick) / 2
    return (math.cos(p) * math.cos(r), math.cos(p) * math.sin(r),
            math.sin(p) * math.cos(r), -math.sin(p) * math.sin(r))


def _fingerabdruck(paket):
    """Textdateien unabhängig von Gits CRLF/LF-Konvertierung identifizieren."""
    return {
        p.name: hashlib.sha256(
            p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for p in sorted(paket.iterdir())
        if p.suffix in (".json", ".obj")
    }


def _werte(ergebnis):
    return {
        "volumen_m3": ergebnis.V_tauch,
        "kraft_N": ergebnis.F_A.as_array().tolist(),
        "moment_Nm": ergebnis.M.as_array().tolist(),
        "schwerpunkt_m": ergebnis.K.as_array().tolist(),
    }


def referenzfaelle():
    konfig = lade_konfig(ROOT / "konfigurationen")
    konfig.segler_einstellungen = SeglerEinstellungen()
    physik = lade_physik(ROOT / "konfigurationen")
    modelle = {}
    for name in ("optimist", "folkeboot", "yacht1"):
        pfad = ROOT / "code" / "modelle" / name
        paket = lade_modellpaket(pfad, konfig.materialien_blocks)
        boot, _ = baue_modellpaket(konfig, pfad)
        snapshot = boot.snapshot()
        kraft = baue_kraftfunktion_6dof(
            snapshot, rho_w=konfig.wasser_dichte(), g=physik.g_m_pro_s2,
            pfad="exakt_union")
        meshes = snapshot.blatt_meshes
        punkte = np.vstack([p for p, _ in meshes])
        trocken_z = -float(punkte[:, 2].min()) + .01
        voll_z = -float(punkte[:, 2].max()) - .01
        v0 = kraft(((0, 0, voll_z), (1, 0, 0, 0))).V_tauch
        rumpfknoten = next(k for k in paket.manifest.koerper.teile
                          if k.rolle == "rumpf")
        rumpf = paket.meshes[rumpfknoten.id].punkte_si
        l, b = np.ptp(rumpf, axis=0)[:2]
        grenzen = GenauigkeitV09(l, b, boot.masse, physik.g_m_pro_s2, v0)
        faelle = []
        for z in np.linspace(voll_z, trocken_z, 7):
            for roll in (-20, -10, 0, 10, 20):
                for nick in (-5, 0, 5):
                    q = _quaternion(roll, nick)
                    ergebnis = _werte(kraft(((0, 0, float(z)), q)))
                    grenzen.hydrostatik(ergebnis, ergebnis)
                    faelle.append({
                        "position_m": [0, 0, float(z)], "quaternion_wxyz": q,
                        "wasserliniengrenze": False, "referenz": ergebnis})
        wasserlinien = []
        for index, (p, _f) in enumerate(meshes):
            for z in (-float(p[:, 2].min()), -float(p[:, 2].max())):
                for delta in (-.0001, .0001):
                    hoehe = z + delta
                    ergebnis = _werte(kraft(((0, 0, hoehe), (1, 0, 0, 0))))
                    grenzen.hydrostatik(ergebnis, ergebnis,
                                        wasserliniengrenze=True)
                    wasserlinien.append({
                        "blatt_index": index, "position_m": [0, 0, hoehe],
                        "quaternion_wxyz": [1, 0, 0, 0],
                        "wasserliniengrenze": True, "referenz": ergebnis})
        segler = next((k for k in paket.manifest.koerper.teile
                       if k.masse_kg is not None), None)
        modelle[name] = {
            "paket_sha256": _fingerabdruck(pfad),
            "laenge_m": float(l), "breite_m": float(b),
            "masse_kg": boot.masse, "g_m_pro_s2": physik.g_m_pro_s2,
            "vollvolumen_m3": v0, "rho_w_kg_m3": konfig.wasser_dichte(),
            "hydrostatik": faelle, "wasserlinien": wasserlinien,
            "beladung": None if segler is None else {
                "massen_kg": [segler.masse_kg * .8, segler.masse_kg,
                              segler.masse_kg * 1.2],
                "position_rumpf_m": segler.position_rumpf_m,
                "verschiebung_je_achse_m": .2,
                "rueckstellung": True},
            "dynamik_pruefvorgabe": {
                "dauer_s": 30, "dt_s": physik.dt_s,
                "fluidgeschwindigkeit_m_s": physik.fluidgeschwindigkeit,
                "fluidwinkelgeschwindigkeit_rad_s": physik.fluidwinkelgeschwindigkeit,
                "linear_widerstand": physik.linear_widerstand,
                "quadratischer_widerstand": physik.quadratischer_widerstand,
                "added_mass_diagonal": physik.added_mass_diagonal,
                "stoerung_roll_grad": 5, "stoerung_nick_grad": 2,
                "stoerung_hoehe_m": .01,
                "vergleich": "Jeder identische Integrationszeitpunkt",
                "abklingen_fenster_s": 120,
                "periodenmessung": "Gleichgerichtete Nulldurchgänge nach Gleichgewichtsabzug",
                "abklingmessung": "Zeit bis aufeinanderfolgende Maxima unter 1/e der Anfangsamplitude liegen",
                "status": "Prüfvorgabe, kein ausgeführter Dynamik-Kandidatenvergleich",
            },
        }
    return {"fassung": 1, "backend": "exakt_union", "modelle": modelle}


def pruefen(gespeichert, aktuell):
    if (gespeichert.keys() != aktuell.keys()
            or gespeichert["fassung"] != aktuell["fassung"]
            or gespeichert["backend"] != aktuell["backend"]
            or gespeichert["modelle"].keys() != aktuell["modelle"].keys()):
        raise ValueError("Referenzstruktur verändert")
    for name, neu in aktuell["modelle"].items():
        alt = gespeichert["modelle"][name]
        if alt["paket_sha256"] != neu["paket_sha256"]:
            raise ValueError("%s: Modellfassung verändert; bewusste Neuprüfung nötig" % name)
        for feld in ("beladung", "dynamik_pruefvorgabe"):
            # JSON normalisiert Tupel zu Listen.
            if alt[feld] != json.loads(json.dumps(neu[feld])):
                raise ValueError("%s: eingefrorene Prüfvorgabe verändert" % name)
        for feld in ("laenge_m", "breite_m", "masse_kg", "g_m_pro_s2",
                     "vollvolumen_m3", "rho_w_kg_m3"):
            np.testing.assert_allclose(neu[feld], alt[feld], rtol=0, atol=1e-10)
        for gruppe in ("hydrostatik", "wasserlinien"):
            if len(alt[gruppe]) != len(neu[gruppe]):
                raise ValueError("%s: Fallanzahl in %s verändert" % (name, gruppe))
            for a, b in zip(alt[gruppe], neu[gruppe]):
                for feld in ("position_m", "quaternion_wxyz"):
                    np.testing.assert_array_equal(a[feld], b[feld])
                for feld in a["referenz"]:
                    # Exakter Pfad: keine Verwendung des größeren Schulungsbudgets.
                    np.testing.assert_allclose(
                        a["referenz"][feld], b["referenz"][feld],
                        rtol=0, atol=1e-9, err_msg="%s/%s" % (name, feld))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schreiben", action="store_true")
    args = parser.parse_args()
    aktuell = referenzfaelle()
    if args.schreiben:
        ZIEL.write_text(json.dumps(aktuell, ensure_ascii=False, indent=2,
                                   allow_nan=False) + "\n", encoding="utf-8")
    else:
        pruefen(json.loads(ZIEL.read_text(encoding="utf-8")), aktuell)
    print("v0.9: exakte Hydrostatikreferenzen für drei Modelle geprüft.")
