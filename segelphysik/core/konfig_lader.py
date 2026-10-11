"""Lader fuer die Konfig-Dateien (Spec V4, J; Schema-Reform 11.10.):
  konfigurationen/materialien.json  - Stoffdaten (Materialien + Wasser)
  konfigurationen/koerper.json      - Koerper-Hierarchie + Darstellung
Vorlagen: doc/materialien_vorlage.json + doc/koerper_vorlage.json.
Doppelschluessel-Erkennung (object_pairs_hook) auf BEIDEN Dateien,
rekursive Validierung, Cross-File-Materialpruefung, kein stiller Fallback.

Massen-Regel (Spec P3, ein Kanal pro Groesse):
  material (Pflicht) = Name aus der Materialtabelle ODER direkte Dichte [kg/m^3]
  wanddicke_m (optional, >0)  -> SCHALE:  flaechenmasse = rho * t
  wanddicke_m fehlt           -> VOLUMEN: masse = rho * V
  Jeder andere Massenschluessel ist ein Validierungsfehler.
"""
import json, os

KONFIG_ORDNER = "konfigurationen"
MATERIAL_DATEI = "materialien.json"
KOERPER_DATEI = "koerper.json"
VORLAGE_MATERIAL = os.path.join("doc", "materialien_vorlage.json")
VORLAGE_KOERPER = os.path.join("doc", "koerper_vorlage.json")
_VERBOTEN_BLATT = ("masse", "dichte", "flaechenmasse_kg_pro_m2", "dichte_kg_pro_m3")
_VERBOTEN_GRUPPE = _VERBOTEN_BLATT + ("material", "wanddicke_m")

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

def _val_materialien(d, pfad):
    mat = d.get("materialien")
    if not isinstance(mat, dict) or not mat:
        raise KonfigFehler("%s: Abschnitt 'materialien' fehlt oder leer" % pfad)
    for n, w in mat.items():
        if not n.startswith("_"):
            _positive_zahl(w, "%s.materialien.%s" % (pfad, n))
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
            "%s: unzulaessiger Massenschluessel %s - seit der Schema-Reform gilt: "
            "'material' (Name oder Dichte-Zahl) + optional 'wanddicke_m' (P3)"
            % (hier, verboten))
    if "material" not in e:
        raise KonfigFehler("%s: 'material' fehlt (Pflicht, P3)" % hier)
    mat = e["material"]
    if isinstance(mat, str):
        if mat not in materialien:
            raise KonfigFehler("%s: unbekanntes Material '%s' (nicht in "
                               "materialien.json)" % (hier, mat))
    else:
        _positive_zahl(mat, "%s.material (Dichte kg/m^3)" % hier)
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

class Konfiguration:
    def __init__(self, m, k, ordner):
        self._m = m; self._k = k; self.ordner = ordner; self.protokoll = []
    @property
    def materialien(self): return dict(self._m["materialien"])
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
    def dichte_von(self, material):
        """Dichte zu Material-Name ODER direkter Zahl (Spec P3)."""
        if isinstance(material, str):
            try: return float(self._m["materialien"][material])
            except KeyError: raise KonfigFehler("Unbekanntes Material: '%s'" % material) from None
        return float(material)

def lade_konfig(ordner=KONFIG_ORDNER):
    """Liest und validiert BEIDE Konfig-Dateien (kein stiller Fallback, Spec J)."""
    mpfad = os.path.join(ordner, MATERIAL_DATEI)
    kpfad = os.path.join(ordner, KOERPER_DATEI)
    m = _lies(mpfad, VORLAGE_MATERIAL)
    k = _lies(kpfad, VORLAGE_KOERPER)
    _val_materialien(m, mpfad)
    _val_koerper(k, m["materialien"], kpfad)
    return Konfiguration(m, k, ordner)
