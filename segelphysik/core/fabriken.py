"""Fabriken (Spec R4/J-3): bauen Hauptobjekte aus der koerper.json.
Zusammengesetzte Koerper koennen auf aktive Baum-Blaetter gefiltert werden;
baue_boot bleibt als Kompatibilitaets-Wrapper."""
import os
from . import koerper_formen as formen_alt
from . import boot_bau
from .koerper import Koerper

YACHT_ORDNER = os.path.join(boot_bau.MODELL_ORDNER, "yacht1")
DICHTE_KEGEL = 500.0
DICHTE_QUADER = 950.0
DICHTE_PYRAMIDE = 500.0


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
    geladenen Modell-Frame - fuer die Welt-Platzierung (Position += r_modell).
    """
    specs = _specs_aus_konfig(konfig.boot_teile, konfig, skala, ordner)
    k = Koerper.verband(specs, farbe=konfig.farbe_standard,
                        delta_helligkeit=konfig.delta_helligkeit)
    _protokoll_und_warnung(specs, konfig)
    return k, k._r_eingabe.copy()


def baue_form(konfig, eintrag):
    """J-1/J-3: einfache Figur aus einem 'form'-Eintrag der koerper.json."""
    f = eintrag["form"]
    typ = f["typ"]
    if typ == "cone":
        form = formen_alt.bau_kegel(float(f["H_m"]), float(f["R_m"]))
    elif typ == "box":
        form = formen_alt.bau_quader(float(f["dx_m"]), float(f["dy_m"]),
                                     float(f["dz_m"]))
    elif typ == "pyramid":
        form = formen_alt.bau_pyramide(float(f["a_m"]), float(f["H_m"]))
    else:
        raise ValueError("unbekannte Form %r (Loader erlaubt nur "
                         "cone/box/pyramid)" % (typ,))
    from .geometrie_konflikte import override_aus_eintrag
    form_override = override_aus_eintrag(eintrag)
    if form_override is not None:
        form = form_override
    if "material" in eintrag:
        rho = konfig.dichte_von(eintrag["material"])
        farbe, farbe_uw = konfig.farben_von(eintrag["material"])
        glanz = konfig.glanz_von(eintrag["material"])
    else:
        rho = float(eintrag["dichte_kg_pro_m3"])
        farbe = eintrag["farbe"]
        farbe_uw = eintrag["farbe_unter_wasser"]
        glanz = None
    if "wanddicke_m" in eintrag:
        kwargs = {"flaechenmasse": rho * float(eintrag["wanddicke_m"])}
    else:
        kwargs = {"dichte": rho}
    if glanz is not None:
        kwargs["glanz"] = glanz
    return Koerper(form=form, farbe=farbe, farbe_unter_wasser=farbe_uw,
                   delta_helligkeit=konfig.delta_helligkeit, **kwargs)


def baue_summenkoerper(konfig, name, eintrag=None, aktive_blaetter=None):
    """J-3: namensneutral - baut JEDES Hauptobjekt aus der JSON.

    Wenn aktive_blaetter angegeben ist, werden nur die benannten Blätter in
    den zusammengesetzten Körper aufgenommen; None bedeutet alle Blätter.
    Rueckgabe: (koerper, r_modell); r_modell ist bei zusammengesetzten
    Koerpern der Masseschwerpunkt im Modell-Frame (Position += r_modell),
    bei einfachen Figuren None."""
    if eintrag is None:
        eintrag = konfig.summenkoerper[name]
    if "form" in eintrag:
        return baue_form(konfig, eintrag), None
    ordner = os.path.join(boot_bau.MODELL_ORDNER, name)
    aktive_namen = (None if aktive_blaetter is None
                    else {getattr(blatt, "name", blatt)
                          for blatt in aktive_blaetter})
    specs = _specs_aus_konfig(eintrag["teile"], konfig, boot_bau.SKALA,
                              ordner, aktive_namen=aktive_namen)
    if not specs:
        raise ValueError("Hauptobjekt %r hat keine aktiven Unterobjekte" % name)
    k = Koerper.verband(specs, farbe=konfig.farbe_standard,
                        delta_helligkeit=konfig.delta_helligkeit)
    _protokoll_und_warnung(specs, konfig)
    return k, k._r_eingabe.copy()


def _werte(konfig, typ=None):
    if konfig is None:
        return "#c9c9c9", 0.25
    farbe = konfig.farbe_standard
    gk = getattr(konfig, "grundkoerper_farben", None) or {}
    if typ and typ in gk:
        farbe = gk[typ]
    return farbe, konfig.delta_helligkeit


def _specs_aus_konfig(eintraege, konfig, skala, ordner,
                      aktive_namen=None, _pfad=()):
    """Neues Schema (Spec P3/P4): 'material' = Name ODER Dichte-Zahl,
    optional 'wanddicke_m' -> Schale mit fm = rho*t;
    optional 'farbe'/'farbe_unter_wasser' -> Farb-Kanal je Blatt (P4)."""
    specs = []
    for eintrag in eintraege:
        name = eintrag["name"]
        if "teile" in eintrag:
            kinder = _specs_aus_konfig(
                eintrag["teile"], konfig, skala, ordner,
                aktive_namen=aktive_namen, _pfad=_pfad + (name,))
            if kinder:
                specs.append({"teile": kinder})
            continue
        if aktive_namen is not None and name not in aktive_namen:
            continue
        p, f = boot_bau.baue_teil(name, skala=skala, ordner=ordner)
        spec = {
            "form": (p, f),
            "_name": name,
            "_konflikt_name": "/".join(_pfad + (name,)),
            "_quellpfad": os.path.abspath(
                os.path.join(ordner, name + ".obj")),
        }
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

def _protokoll_und_warnung(specs, konfig):
    """Druckt je Blatt die Masse und warnt, wenn ein Teil dominiert."""
    zeilen = []
    def gehe(s):
        for si in s:
            if "teile" in si:
                gehe(si["teile"])
                continue
            kwargs = {k: v for k, v in si.items()
                      if not k.startswith("_") and k != "form"}
            k = Koerper(form=si["form"], **kwargs)
            zeilen.append((si["_name"], k.masse))
    gehe(specs)
    gesamt = sum(m for _n, m in zeilen)
    for n, m in zeilen:
        konfig.protokoll.append("%s: masse=%.3f kg (%.1f %%)" % (n, m, 100.0 * m / gesamt))
        if m > WARN_SCHWELLE * gesamt:
            print("WARNUNG (Plausibilitaet): Teil '%s' hat %.1f %% der Gesamtmasse "
                  "(> %.0f %%). Vergessen wanddicke_m? (Spec P3)"
                  % (n, 100.0 * m / gesamt, 100.0 * WARN_SCHWELLE))
    return zeilen, gesamt
