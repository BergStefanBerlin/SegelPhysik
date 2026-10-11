"""Fabriken (Spec R4): duenne Erzeuger fuer die vier bekannten Koerper.
Alle Werte (Materialien, Farben, DeltaL) kommen aus konfiguration.json.
Modelle liegen je Boot in modelle/<bootname>/ (z. B. modelle/yacht1/)."""
import os
from . import koerper_formen as formen_alt
from . import boot_bau
from .koerper import Koerper

# Standard-Modellboot; weitere Boote spaeter als eigene Ordner daneben
YACHT_ORDNER = os.path.join(boot_bau.MODELL_ORDNER, "yacht1")


def baue_kegel(konfig=None, H=2.0, R=1.0, dichte=1000.0):
    farbe, delta = _werte(konfig)
    return Koerper(form=formen_alt.bau_kegel(H, R), dichte=dichte,
                   farbe=farbe, delta_helligkeit=delta)


def baue_quader(konfig=None, dx=2.0, dy=2.0, dz=2.0, dichte=1000.0):
    farbe, delta = _werte(konfig)
    return Koerper(form=formen_alt.bau_quader(dx, dy, dz), dichte=dichte,
                   farbe=farbe, delta_helligkeit=delta)


def baue_pyramide(konfig=None, a=2.0, H=2.0, dichte=1000.0):
    farbe, delta = _werte(konfig)
    return Koerper(form=formen_alt.bau_pyramide(a, H), dichte=dichte,
                   farbe=farbe, delta_helligkeit=delta)


def baue_boot(konfig, skala=boot_bau.SKALA, ordner=YACHT_ORDNER):
    """Boot aus konfiguration.json + OBJ-Teilen (rekursiv: kielsystem/rigg).

    Rueckgabe (koerper, r_modell): r_modell ist der Masseschwerpunkt im
    geladenen Modell-Frame - fuer die Welt-Platzierung (Position += r_modell),
    damit die Darstellung identisch zum bisherigen Verfahren bleibt.
    """
    specs = _specs_aus_konfig(konfig.boot_teile, konfig.materialien, skala, ordner)
    k = Koerper.verband(specs, farbe=konfig.farbe_standard,
                        delta_helligkeit=konfig.delta_helligkeit)
    return k, k._r_eingabe.copy()


def _werte(konfig):
    if konfig is None:
        return "#c9c9c9", 0.25
    return konfig.farbe_standard, konfig.delta_helligkeit


def _specs_aus_konfig(eintraege, materialien, skala, ordner):
    specs = []
    for eintrag in eintraege:
        name = eintrag["name"]
        if "teile" in eintrag:
            specs.append({"teile": _specs_aus_konfig(
                eintrag["teile"], materialien, skala, ordner)})
            continue
        p, f = boot_bau.baue_teil(name, skala=skala, ordner=ordner)
        spec = {"form": (p, f)}
        if "material" in eintrag:
            spec["dichte"] = float(materialien[eintrag["material"]])
        elif "flaechenmasse_kg_pro_m2" in eintrag:
            spec["flaechenmasse"] = float(eintrag["flaechenmasse_kg_pro_m2"])
        elif "dichte" in eintrag:
            spec["dichte"] = float(eintrag["dichte"])
        elif "masse" in eintrag:
            spec["masse"] = float(eintrag["masse"])
        specs.append(spec)
    return specs
