"""Lader fuer die Konfig-Dateien (Spec V4, J; Material-Reform 12.10.):
  konfigurationen/materialien.json  - Stoffdaten: Materialien (Dichte + Farben) + Wasser
  konfigurationen/koerper.json      - Koerper-Hierarchie + Darstellung
Vorlagen: doc/materialien_vorlage.json + doc/koerper_vorlage.json.
Doppelschluessel-Erkennung (object_pairs_hook) auf BEIDEN Dateien,
rekursive Validierung, Cross-File-Materialpruefung, kein stiller Fallback.

Massen-Regel (Spec P3, ein Kanal pro Groesse) - am BLATT genau EINE Form:
  (a) "material": "<Name>"  -> Dichte UND Farben aus der Materialtabelle
  (b) ohne "material": dichte_kg_pro_m3 + farbe + farbe_unter_wasser direkt
Optional wanddicke_m (>0) -> SCHALE: fm = rho * t; fehlt -> VOLUMEN: m = rho*V.
Jeder andere Massenschluessel ist ein Validierungsfehler.

Farb-Regel (Spec P4, Reform 12.10.): Farbe ist eine STOFF-Eigenschaft. Ein
Blatt MIT 'material' traegt keine eigenen Farb-Schluessel; ohne 'material'
sind beide Farben Teil des Pflicht-Tripels.
"""
import json, os

KONFIG_ORDNER = "konfigurationen"
MATERIAL_DATEI = "materialien.json"
KOERPER_DATEI = "koerper.json"
VORLAGE_MATERIAL = os.path.join("doc", "materialien_vorlage.json")
VORLAGE_KOERPER = os.path.join("doc", "koerper_vorlage.json")
_VERBOTEN_BLATT = ("masse", "dichte", "flaechenmasse_kg_pro_m2")
_VERBOTEN_GRUPPE = _VERBOTEN_BLATT + ("material", "wanddicke_m",
                                      "dichte_kg_pro_m3",
                                      "farbe", "farbe_unter_wasser")

class KonfigFehler(ValueError):
    """Verstoss gegen die Regeln der Eingabedateien (Spec J)."""

def _hook(paar):
    gesehen = set()
    for s, _w in paar:
        if s in gesehen:
            raise KonfigFehler("Doppelter Schluessel: '%s'" % s)
        gesehen.add(s)
    return dict(paar)

def _lies(pfad, vorlage):
    if not os.path.exists(pfad):
        raise KonfigFehler(
            "'%s' nicht gefunden. Bitte einmalig aus der Vorlage kopieren: %s. "
            "Kein stiller Fallback (Spec J)." % (pfad, vorlage))
    with open(pfad, encoding="utf-8") as f:
        try:
            return json.load(f, object_pairs_hook=_hook)
        except json.JSONDecodeError as e:
            raise KonfigFehler("Ungueltiges JSON in %s: %s" % (pfad, e)) from e

def _positive_zahl(w, wo):
    if isinstance(w, bool) or not isinstance(w, (int, float)) or not w > 0:
        raise KonfigFehler("%s: positive Zahl erwartet, gefunden: %r" % (wo, w))
    return float(w)

def _val_hex(w, wo):
    if (not isinstance(w, str) or not w.startswith("#")
            or len(w) not in (4, 7)):
        raise KonfigFehler("%s: Hex-Farbe (#rgb oder #rrggbb) erwartet, "
                           "gefunden: %r" % (wo, w))
    erlaubt = set("0123456789abcdefABCDEF")
    if any(z not in erlaubt for z in w[1:]):
        raise KonfigFehler("%s: ungueltige Hex-Zeichen in %r" % (wo, w))

def _val_materialien(d, pfad):
    mat = d.get("materialien")
    if not isinstance(mat, dict) or not mat:
        raise KonfigFehler("%s: Abschnitt 'materialien' fehlt oder leer" % pfad)
    for n, block in mat.items():
        if n.startswith("_"):
            continue
        hier = "%s.materialien.%s" % (pfad, n)
        if not isinstance(block, dict):
            raise KonfigFehler(
                "%s: Material ist seit der Reform ein Block mit "
                "dichte_kg_pro_m3 + farbe + farbe_unter_wasser" % hier)
        _positive_zahl(block.get("dichte_kg_pro_m3"), "%s.dichte_kg_pro_m3" % hier)
        _val_hex(block.get("farbe"), "%s.farbe" % hier)
        _val_hex(block.get("farbe_unter_wasser"), "%s.farbe_unter_wasser" % hier)
    wasser = d.get("wasser")
    if not isinstance(wasser, dict):
        raise KonfigFehler("%s: Abschnitt 'wasser' fehlt" % pfad)
    dic = wasser.get("dichten_kg_pro_m3")
    if not isinstance(dic, dict) or not dic:
        raise KonfigFehler("%s: wasser.dichten_kg_pro_m3 fehlt oder leer" % pfad)
    for n, w in dic.items():
        if not n.startswith("_"):
            _positive_zahl(w, "%s.wasser.%s" % (pfad, n))
    if wasser.get("standard") not in dic:
        raise KonfigFehler("%s: wasser.standard: unbekannter Name" % pfad)

def _val_teil(e, pfad, materialien):
    if not isinstance(e, dict) or "name" not in e:
        raise KonfigFehler("%s: Eintrag ohne 'name'" % pfad)
    hier = "%s (%s)" % (pfad, e["name"])
    if "teile" in e:
        verboten = [s for s in _VERBOTEN_GRUPPE if s in e]
        if verboten:
            raise KonfigFehler("%s: reine Gruppe ohne Massengroesse (P2.5): %s"
                               % (hier, verboten))
        teile = e["teile"]
        if not isinstance(teile, list) or not teile:
            raise KonfigFehler("%s: leere Gruppe" % hier)
        for i, t in enumerate(teile):
            _val_teil(t, "%s.teile[%d]" % (hier, i), materialien)
        return
    verboten = [s for s in _VERBOTEN_BLATT if s in e]
    if verboten:
        raise KonfigFehler(
            "%s: unzulaessiger Massenschluessel %s (P3): 'material' (Name) "
            "oder das Direkt-Tripel verwenden" % (hier, verboten))
    hat_mat = "material" in e
    hat_direkt = "dichte_kg_pro_m3" in e
    if hat_mat and hat_direkt:
        raise KonfigFehler(
            "%s: 'material' UND 'dichte_kg_pro_m3' gesetzt - genau EINE Form "
            "(P3): Materialname ODER direkte Stoffangabe" % hier)
    if not hat_mat and not hat_direkt:
        raise KonfigFehler(
            "%s: weder 'material' noch das Direkt-Tripel (dichte_kg_pro_m3 "
            "+ farbe + farbe_unter_wasser) - genau EINE Form (P3/P4)" % hier)
    if hat_mat:
        mat = e["material"]
        if not isinstance(mat, str):
            raise KonfigFehler(
                "%s: 'material' muss ein Name aus materialien.json sein; "
                "eine direkte Dichte gehoert in 'dichte_kg_pro_m3' "
                "(mit Farben)" % hier)
        if mat not in materialien:
            raise KonfigFehler("%s: unbekanntes Material '%s' (nicht in "
                               "materialien.json)" % (hier, mat))
        farbschluessel = [s for s in ("farbe", "farbe_unter_wasser") if s in e]
        if farbschluessel:
            raise KonfigFehler(
                "%s: Farb-Schluessel %s am Blatt unzulaessig - Farbe ist eine "
                "STOFF-Eigenschaft (P4): Werte in materialien.json pflegen "
                "oder Material wechseln" % (hier, farbschluessel))
    else:
        _positive_zahl(e.get("dichte_kg_pro_m3"),
                       "%s.dichte_kg_pro_m3" % hier)
        _val_hex(e.get("farbe"), "%s.farbe" % hier)
        _val_hex(e.get("farbe_unter_wasser"), "%s.farbe_unter_wasser" % hier)
    if "wanddicke_m" in e:
        _positive_zahl(e["wanddicke_m"], "%s.wanddicke_m" % hier)

def _val_koerper(d, materialien, pfad):
    boot = d.get("boot")
    if not isinstance(boot, dict) or "teile" not in boot:
        raise KonfigFehler("%s: boot.teile fehlt" % pfad)
    teile = boot["teile"]
    if not isinstance(teile, list) or not teile:
        raise KonfigFehler("%s: boot.teile leer" % pfad)
    for i, t in enumerate(teile):
        _val_teil(t, "%s.boot.teile[%d]" % (pfad, i), materialien)
    da = d.get("darstellung")
    if not isinstance(da, dict):
        raise KonfigFehler("%s: Abschnitt 'darstellung' fehlt" % pfad)
    dl = da.get("delta_helligkeit_unterwasser")
    if isinstance(dl, bool) or not isinstance(dl, (int, float)) or not 0.0 <= float(dl) <= 1.0:
        raise KonfigFehler("%s: darstellung.delta_helligkeit_unterwasser: Zahl [0..1]" % pfad)
    if not isinstance(da.get("farbe_standard"), str):
        raise KonfigFehler("%s: darstellung.farbe_standard: Hex-String erwartet" % pfad)
    gk = da.get("grundkoerper")
    if gk is not None:
        if not isinstance(gk, dict):
            raise KonfigFehler(
                "%s: darstellung.grundkoerper: Objekt erwartet" % pfad)
        for schluessel, wert in gk.items():
            if schluessel.startswith("_"):
                continue   # Doku-Schluessel (Projektkonvention)
            if schluessel not in ("cone", "box", "pyramid"):
                raise KonfigFehler(
                    "%s: darstellung.grundkoerper: unbekannter Schluessel "
                    "'%s' (erlaubt: cone, box, pyramid)" % (pfad, schluessel))
            _val_hex(wert, "%s.grundkoerper.%s" % (pfad, schluessel))

class Konfiguration:
    def __init__(self, m, k, ordner):
        self._m = m; self._k = k; self.ordner = ordner; self.protokoll = []
    @property
    def materialien(self):
        """Flaches Dichte-Dict {name: kg/m^3} (kompatibel zur Klasse)."""
        return {n: float(b["dichte_kg_pro_m3"])
                for n, b in self._m["materialien"].items()
                if not n.startswith("_")}
    @property
    def materialien_blocks(self):
        """Volle Material-Bloecke (Dichte + Farben)."""
        return {n: b for n, b in self._m["materialien"].items()
                if not n.startswith("_")}
    @property
    def wasser_dichten(self): return dict(self._m["wasser"]["dichten_kg_pro_m3"])
    def wasser_dichte(self, x=None):
        if x is None: x = self._m["wasser"]["standard"]
        if isinstance(x, (int, float)): return float(x)
        try: return float(self._m["wasser"]["dichten_kg_pro_m3"][x])
        except KeyError: raise KonfigFehler("Unbekanntes Wasser: '%s'" % x) from None
    @property
    def boot_teile(self): return self._k["boot"]["teile"]
    @property
    def delta_helligkeit(self): return float(self._k["darstellung"]["delta_helligkeit_unterwasser"])
    @property
    def farbe_standard(self): return self._k["darstellung"]["farbe_standard"]

    @property
    def grundkoerper_farben(self):
        """Optionale Farben der Demo-Grundkoerper (darstellung.grundkoerper)."""
        return dict(self._k["darstellung"].get("grundkoerper") or {})
    def dichte_von(self, material):
        """Dichte zu Material-Name (aus Block) oder Zahl."""
        if isinstance(material, str):
            try:
                return float(self._m["materialien"][material]["dichte_kg_pro_m3"])
            except KeyError:
                raise KonfigFehler("Unbekanntes Material: '%s'" % material) from None
        return float(material)
    def farben_von(self, material):
        """(farbe, farbe_unter_wasser) zu Material-Name; None bei Direktangabe."""
        if isinstance(material, str):
            try:
                b = self._m["materialien"][material]
                return b["farbe"], b["farbe_unter_wasser"]
            except KeyError:
                raise KonfigFehler("Unbekanntes Material: '%s'" % material) from None
        return None

def lade_konfig(ordner=KONFIG_ORDNER):
    """Liest und validiert BEIDE Konfig-Dateien (kein stiller Fallback, Spec J)."""
    mpfad = os.path.join(ordner, MATERIAL_DATEI)
    kpfad = os.path.join(ordner, KOERPER_DATEI)
    m = _lies(mpfad, VORLAGE_MATERIAL)
    k = _lies(kpfad, VORLAGE_KOERPER)
    _val_materialien(m, mpfad)
    _val_koerper(k, m["materialien"], kpfad)
    return Konfiguration(m, k, ordner)
