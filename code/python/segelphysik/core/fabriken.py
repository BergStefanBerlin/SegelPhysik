"""Fabriken (Spec R4/J-3): bauen Hauptobjekte aus der koerper.json.
Zusammengesetzte Koerper koennen auf aktive Baum-Blaetter gefiltert werden;
baue_boot bleibt als Kompatibilitaets-Wrapper."""
import os
from types import MappingProxyType
from . import koerper_formen as formen_alt
from . import boot_bau
from .koerper import Koerper, KoerperFehler
from .frames import pose_aus_modellpose

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
    if (_ist_repo_konfig(konfig)
            and skala == boot_bau.SKALA
            and os.path.abspath(ordner) == os.path.abspath(YACHT_ORDNER)):
        return baue_summenkoerper(konfig, "yacht1")

    specs = _specs_aus_konfig(konfig.boot_teile, konfig, skala, ordner)
    k = Koerper.verband(specs, farbe=konfig.farbe_standard,
                        delta_helligkeit=konfig.delta_helligkeit)
    _protokoll_und_warnung(k, konfig)
    return k, k._r_eingabe.copy()


def baue_form(konfig, eintrag):
    """J-1/J-3: einfache Figur aus einem 'form'-Eintrag der koerper.json."""
    f = eintrag["form"]
    form = formen_alt.baue_aus_form(f)
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
        paketwurzel = os.path.join(boot_bau.MODELL_ORDNER, name)
        if (_ist_repo_konfig(konfig)
                and getattr(konfig, "paketfabrik_aktiv", True)):
            manifest_pfad = os.path.join(paketwurzel, "modell.json")
            if os.path.isfile(manifest_pfad):
                return baue_modellpaket(
                    konfig, paketwurzel, aktive_blaetter=aktive_blaetter,
                    sitzungs_ueberschreibungen=getattr(
                        konfig, "paket_ueberschreibungen", {}).get(
                            name, {}))
            if name in konfig.summenkoerper:
                raise ValueError(
                    "Paketfabrik ist aktiv, aber Modellpaket %r fehlt"
                    % name)
            raise ValueError(
                "Unbekanntes Modell %r: kein Paket unter %s"
                % (name, boot_bau.MODELL_ORDNER))
        eintrag = konfig.summenkoerper[name]
    if "form" in eintrag:
        return baue_form(konfig, eintrag), None
    ordner = os.path.join(boot_bau.MODELL_ORDNER, name)
    aktive_namen = (
        None if aktive_blaetter is None
        else _aktive_legacy_namen(aktive_blaetter, eintrag))
    specs = _specs_aus_konfig(eintrag["teile"], konfig, boot_bau.SKALA,
                              ordner, aktive_namen=aktive_namen)
    if not specs:
        raise ValueError("Hauptobjekt %r hat keine aktiven Unterobjekte" % name)
    k = Koerper.verband(specs, farbe=konfig.farbe_standard,
                        delta_helligkeit=konfig.delta_helligkeit)
    _protokoll_und_warnung(k, konfig)
    return k, k._r_eingabe.copy()


def _aktive_legacy_namen(aktive_blaetter, eintrag):
    legacy_namen = set()

    def indexiere(teil):
        if "teile" in teil:
            for kind in teil["teile"]:
                indexiere(kind)
        elif "name" in teil:
            legacy_namen.add(teil["name"])

    indexiere(eintrag)
    ergebnis = set()
    for blatt in aktive_blaetter:
        identifier = getattr(
            blatt, "id", getattr(blatt, "name", blatt))
        if identifier in legacy_namen:
            ergebnis.add(identifier)
            continue
        passende_namen = [
            name for name in legacy_namen
            if identifier.startswith(name + "_")
        ]
        if passende_namen:
            ergebnis.add(max(passende_namen, key=len))
    return ergebnis


def baue_modellpaket(konfig, paketwurzel, aktive_blaetter=None,
                     sitzungs_ueberschreibungen=None):
    """Baut einen Laufzeitkörper aus einem validierten Modellpaket.

    Rückgabe wie bei baue_summenkoerper: (Körper, Modellversatz); für ein
    einzelnes Blatt ist der Modellversatz None.
    """
    from .modell_lader import lade_modellmanifest

    manifest = lade_modellmanifest(
        paketwurzel, konfig.materialien_blocks,
        _pruefe_geometriepfade=False)
    if aktive_blaetter is None or not manifest.koerper.teile:
        aktive_ids = None
    else:
        aktive_ids = {
            getattr(blatt, "id", getattr(blatt, "name", blatt))
            for blatt in aktive_blaetter
        }
    spezifikation = _spec_aus_modellknoten(
        manifest.koerper, manifest, konfig, aktive_ids,
        sitzungs_ueberschreibungen=sitzungs_ueberschreibungen)
    if spezifikation is None:
        raise ValueError(
            "Modellpaket %r hat keine aktiven Geometrieblätter" % manifest.id)

    gemeinsam = {
        "farbe": konfig.farbe_standard,
        "delta_helligkeit": konfig.delta_helligkeit,
    }
    if manifest.koerper.teile:
        koerper = Koerper.verband(
            spezifikation["teile"], **gemeinsam)
        koerper.knoten_id = spezifikation["knoten_id"]
        koerper.name = spezifikation["name"]
        koerper.rolle = spezifikation["rolle"]
        koerper.rolle_default = spezifikation["rolle_default"]
        koerper.basis_pose = spezifikation["basis_pose"]
        _protokoll_und_warnung(koerper, konfig)
        return koerper, _modellversatz(koerper, spezifikation)

    try:
        koerper = Koerper(
            form=spezifikation["form"],
            dichte=spezifikation.get("dichte"),
            flaechenmasse=spezifikation.get("flaechenmasse"),
            materialien=konfig.materialien_blocks,
            farbe=spezifikation["farbe"],
            farbe_unter_wasser=spezifikation["farbe_unter_wasser"],
            glanz=spezifikation["glanz"],
            delta_helligkeit=konfig.delta_helligkeit,
            knoten_id=spezifikation["knoten_id"],
            name=spezifikation["name"],
            rolle=spezifikation["rolle"],
            verdrangend=spezifikation["verdrangend"],
            basis_pose=spezifikation["basis_pose"],
            strenge_topologie=True,
        )
    except KoerperFehler as fehler:
        raise KoerperFehler(
            "%s: %s" % (spezifikation["_fehlerkontext"], fehler)) from fehler
    koerper._name = spezifikation["_name"]
    koerper.mesh = spezifikation["_mesh"]
    koerper.massendefinition = spezifikation["_massendefinition"]
    koerper.basis_pose = spezifikation["basis_pose"]
    return koerper, _modellversatz(koerper, spezifikation)


def _modellversatz(koerper, spezifikation):
    if spezifikation["basis_pose"] is None:
        return (koerper._r_eingabe.copy() if koerper.teile else None)
    pose = pose_aus_modellpose(
        spezifikation["basis_pose"],
        "modell",
        spezifikation["knoten_id"],
    )
    return pose.punkt_transformieren(koerper._r_eingabe)


def _ist_repo_konfig(konfig):
    """Nur die mit den Repo-Paketen migrierte Konfiguration umschalten."""
    ordner = getattr(konfig, "ordner", None)
    if ordner is None:
        return False
    repo_konfigurationen = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..",
        "konfigurationen"))
    return os.path.normcase(os.path.abspath(ordner)) == os.path.normcase(
        repo_konfigurationen)


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


def _spec_aus_modellknoten(
        knoten, manifest, konfig, aktive_ids, pfad=(),
        sitzungs_ueberschreibungen=None):
    sitzungs_ueberschreibungen = sitzungs_ueberschreibungen or {}
    knotenpfad = pfad + (knoten.id,)
    if knoten.teile:
        kinder = [
            spec for kind in knoten.teile
            if (spec := _spec_aus_modellknoten(
                kind, manifest, konfig, aktive_ids, knotenpfad,
                sitzungs_ueberschreibungen)) is not None
        ]
        if not kinder:
            return None
        return {
            "knoten_id": knoten.id,
            "name": knoten.name,
            "rolle": knoten.rolle,
            "rolle_default": knoten.rolle_default,
            "basis_pose": knoten.pose,
            "gelenkdefinition": knoten.gelenk,
            "teile": kinder,
        }
    if aktive_ids is not None and knoten.id not in aktive_ids:
        return None
    if knoten.masse_kg is not None:
        from .modell_lader import ModellPose

        werte = konfig.segler_einstellungen.werte(
            manifest.id, knoten.masse_kg, knoten.position_rumpf_m)
        translation = tuple(
            r + x for r, x in zip(
                manifest.rumpfreferenz_m, werte["position_rumpf_m"]))
        return {
            "punktmasse": True, "masse": werte["masse_kg"],
            "_name": knoten.id, "knoten_id": knoten.id,
            "_fehlerkontext": "%s/segler" % manifest.id,
            "name": knoten.name, "rolle": "allgemein",
            "verdrangend": False,
            "basis_pose": ModellPose(translation, (1.0, 0.0, 0.0, 0.0)),
        }

    from .mesh import mesh_aus_quelle

    override = sitzungs_ueberschreibungen.get(knoten.id, {})
    material = override.get("material", knoten.material)
    dichte_eintrag = override.get(
        "dichte_kg_pro_m3", knoten.dichte_kg_pro_m3)
    wanddicke = override.get("wanddicke_m", knoten.wanddicke_m)
    mesh = mesh_aus_quelle(
        knoten.geometrie,
        paketwurzel=manifest.paketwurzel,
        obj_zu_m=manifest.obj_zu_m,
        obj_achsenmatrix_zu_blatt=(
            manifest.obj_achsenmatrix_zu_blatt),
        frame="blatt",
        fehlerkontext="%s/%s" % (manifest.id, "/".join(knotenpfad)),
    )
    if material is not None:
        dichte = konfig.dichte_von(material)
        materialfarbe, materialfarbe_uw = konfig.farben_von(material)
        glanz = konfig.glanz_von(material)
    else:
        dichte = dichte_eintrag
        materialfarbe = materialfarbe_uw = None
        glanz = None
    farbe = override.get(
        "farbe", knoten.farbe) or materialfarbe or konfig.farbe_standard
    farbe_uw = override.get(
        "farbe_unter_wasser", knoten.farbe_unter_wasser) or materialfarbe_uw
    if wanddicke is None:
        massenangabe = {"dichte": dichte}
    else:
        massenangabe = {
            "flaechenmasse": dichte * wanddicke}

    return {
        "form": mesh.als_tupel(),
        "_mesh": mesh,
        "_name": knoten.id,
        "_fehlerkontext": "%s/%s" % (
            manifest.id, "/".join(knotenpfad)),
        "strenge_topologie": True,
        "_massendefinition": MappingProxyType({
            "material": material,
            "dichte_kg_pro_m3": dichte,
            "wanddicke_m": wanddicke,
        }),
        "knoten_id": knoten.id,
        "name": knoten.name,
        "rolle": knoten.rolle,
        "basis_pose": knoten.pose,
        "gelenkdefinition": knoten.gelenk,
        "gelenkwinkel_rad": (
            knoten.gelenk.winkel_rad if knoten.gelenk is not None else None),
        "verdrangend": knoten.verdraengend,
        "farbe": farbe,
        "farbe_unter_wasser": farbe_uw,
        "glanz": glanz,
        **massenangabe,
    }


WARN_SCHWELLE = 0.40   # Einzelteil > 40 % der Gesamtmasse -> Warnung

def _protokoll_und_warnung(koerper, konfig):
    """Protokolliert die bereits gebauten Blätter ohne zweite Massenberechnung."""
    zeilen = []
    punktmassen = set()

    def gehe(knoten):
        for kind, _pose in knoten.teile:
            if kind.teile:
                gehe(kind)
                continue
            name = getattr(kind, "_name", None)
            if not name:
                raise ValueError("Zusammengesetztes Blatt ohne stabilen Namen")
            zeilen.append((name, kind.masse))
            if getattr(kind, "punktmasse", False):
                punktmassen.add(name)

    gehe(koerper)
    gesamt = sum(m for _n, m in zeilen)
    for n, m in zeilen:
        konfig.protokoll.append("%s: masse=%.3f kg (%.1f %%)" % (n, m, 100.0 * m / gesamt))
        if n not in punktmassen and m > WARN_SCHWELLE * gesamt:
            print("WARNUNG (Plausibilitaet): Teil '%s' hat %.1f %% der Gesamtmasse "
                  "(> %.0f %%). Vergessen wanddicke_m? (Spec P3)"
                  % (n, 100.0 * m / gesamt, 100.0 * WARN_SCHWELLE))
    return zeilen, gesamt
