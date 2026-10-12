"""Fabriken (Spec R4): duenne Erzeuger fuer die vier bekannten Koerper.
Alle Werte (Materialien, Farben, DeltaL) kommen aus konfigurationen/.
Modelle liegen je Boot in modelle/<bootname>/ (z. B. modelle/yacht1/).
Farben (Spec P4, 12.10.): farbe/farbe_unter_wasser je BLATT optional;
ohne Angabe gilt darstellung.farbe_standard + automatische Aufhellung.

Schritt 4 (K3): Glanzgrad kommt je Blatt aus der Materialtabelle
(materialien.json, Schluessel 'glanz'); bei Direkt-Tripel gilt der Default.

rev E (Sichtprobe 12.10.): Die bisherigen Default-Dichten 1000.0 waren
exakt WASSERDICHTE. Ein solcher Koerper schwebt volltauchend in JEDEM
Tiefgang und JEDER Rollage (F_A = m*g erst bei voller Untertauchung,
dann M identisch 0) - es gibt keine eindeutige Gleichgewichtslage, der
statische Solver kann per Definition keine finden (Kalibrierlauf mit
dem echten Voxel-Kern). Neu (schwimmfaehig, Kalibrierlauf F2):
  Kegel    500 kg/m^3: liegt SEITLICH - physikalisch korrekt (wie eine
           Schwimmstange; aufrecht ist bei GM<0 instabil). Verifiziert:
           phi* nahe 90 Grad, stabil, Restkraft < 5 % m*g.
  Quader   950 kg/m^3: tiefe, stabile aufrechte Lage.
  Pyramide 500 kg/m^3: stabile aufrechte Lage (GM = +0.087 m).
"""
import os
from . import koerper_formen as formen_alt
from . import boot_bau
from .koerper import Koerper

YACHT_ORDNER = os.path.join(boot_bau.MODELL_ORDNER, "yacht1")

DICHTE_KEGEL = 500.0      # rev E: siehe Moduldokumentation
DICHTE_QUADER = 950.0     # rev E
DICHTE_PYRAMIDE = 500.0   # rev E


def baue_kegel(konfig=None, H=2.0, R=1.0, dichte=DICHTE_KEGEL):
    farbe, delta = _werte(konfig, "cone")
    return Koerper(form=formen_alt.bau_kegel(H, R), dichte=dichte,
                   farbe=farbe, delta_helligkeit=delta)


def baue_quader(konfig=None, dx=2.0, dy=2.0, dz=2.0, dichte=DICHTE_QUADER):
    farbe, delta = _werte(konfig, "box")
    return Koerper(form=formen_alt.bau_quader(dx, dy, dz), dichte=dichte,
                   farbe=farbe, delta_helligkeit=delta)


def baue_pyramide(konfig=None, a=2.0, H=2.0, dichte=DICHTE_PYRAMIDE):
    farbe, delta = _werte(konfig, "pyramid")
    return Koerper(form=formen_alt.bau_pyramide(a, H), dichte=dichte,
                   farbe=farbe, delta_helligkeit=delta)


def baue_boot(konfig, skala=boot_bau.SKALA, ordner=YACHT_ORDNER):
    """Boot aus konfigurationen/ + OBJ-Teilen (rekursiv: kielsystem/rigg).

    Rueckgabe (koerper, r_modell): r_modell ist der Masseschwerpunkt im
    geladenen Modell-Frame - fuer die Welt-Platzierung (Position += r_modell),
    damit die Darstellung identisch zum bisherigen Verfahren bleibt.
    """
    specs = _specs_aus_konfig(konfig.boot_teile, konfig, skala, ordner)
    k = Koerper.verband(specs, farbe=konfig.farbe_standard,
                        delta_helligkeit=konfig.delta_helligkeit)
    _protokoll_und_warnung(konfig.boot_teile, specs, konfig)
    return k, k._r_eingabe.copy()


def _werte(konfig, typ=None):
    if konfig is None:
        return "#c9c9c9", 0.25
    farbe = konfig.farbe_standard
    gk = getattr(konfig, "grundkoerper_farben", None) or {}
    if typ and typ in gk:
        farbe = gk[typ]
    return farbe, konfig.delta_helligkeit


def _specs_aus_konfig(eintraege, konfig, skala, ordner):
    """Neues Schema (Spec P3/P4): 'material' = Name ODER Dichte-Zahl,
    optional 'wanddicke_m' -> Schale mit fm = rho*t;
    optional 'farbe'/'farbe_unter_wasser' -> Farb-Kanal je Blatt (P4)."""
    specs = []
    for eintrag in eintraege:
        name = eintrag["name"]
        if "teile" in eintrag:
            specs.append({"teile": _specs_aus_konfig(
                eintrag["teile"], konfig, skala, ordner)})
            continue
        p, f = boot_bau.baue_teil(name, skala=skala, ordner=ordner)
        spec = {"form": (p, f), "_name": name}
        if "material" in eintrag:
            rho = konfig.dichte_von(eintrag["material"])
            farbe, farbe_uw = konfig.farben_von(eintrag["material"])
            spec["glanz"] = konfig.glanz_von(eintrag["material"])   # K3
        else:
            rho = float(eintrag["dichte_kg_pro_m3"])
            farbe = eintrag["farbe"]
            farbe_uw = eintrag["farbe_unter_wasser"]
        spec["farbe"] = farbe
        spec["farbe_unter_wasser"] = farbe_uw
        if "wanddicke_m" in eintrag:
            tt = float(eintrag["wanddicke_m"])
            spec["flaechenmasse"] = rho * tt
            konfig.protokoll.append(
                "%s: SCHALE  rho=%g * t=%g = %.3f kg/m^2" % (name, rho, tt, rho * tt))
        else:
            spec["dichte"] = rho
            konfig.protokoll.append("%s: VOLUMEN  rho=%g kg/m^3" % (name, rho))
        for key in ("farbe", "farbe_unter_wasser"):
            if key in eintrag:
                spec[key] = eintrag[key]
                konfig.protokoll.append("%s: %s=%s" % (name, key, eintrag[key]))
        specs.append(spec)
    return specs


WARN_SCHWELLE = 0.40   # Einzelteil > 40 % der Gesamtmasse -> Warnung

def _protokoll_und_warnung(eintraege, specs, konfig):
    """Druckt je Blatt die Masse und warnt, wenn ein Teil dominiert."""
    zeilen = []
    def gehe(e, s):
        for ei, si in zip(e, s):
            if "teile" in ei:
                gehe(ei["teile"], si["teile"])
                continue
            kwargs = {k: v for k, v in si.items()
                      if not k.startswith("_") and k != "form"}
            k = Koerper(form=si["form"], **kwargs)
            zeilen.append((si["_name"], k.masse))
    gehe(eintraege, specs)
    gesamt = sum(m for _n, m in zeilen)
    for n, m in zeilen:
        konfig.protokoll.append("%s: masse=%.3f kg (%.1f %%)" % (n, m, 100.0 * m / gesamt))
        if m > WARN_SCHWELLE * gesamt:
            print("WARNUNG (Plausibilitaet): Teil '%s' hat %.1f %% der Gesamtmasse "
                  "(> %.0f %%). Vergessen wanddicke_m? (Spec P3)"
                  % (n, 100.0 * m / gesamt, 100.0 * WARN_SCHWELLE))
    return zeilen, gesamt
