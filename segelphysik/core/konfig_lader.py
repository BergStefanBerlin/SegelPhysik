"""Lader fuer konfiguration.json (Spec V4, J): Template-Muster,
Doppelschluessel-Erkennung, rekursive Validierung, kein stiller Fallback."""
import json, os
VORLAGE_PFAD = os.path.join("doc", "configuration_template.json")
ARBEITSDATEI = os.path.join("konfigurationen", "konfiguration.json")
_ABS = ("materialien", "wasser", "boot", "darstellung")
_MAT = ("Holz", "GfK", "Stahl", "Blei", "Aluminium")
_WAS = ("Süßwasser", "Salzwasser", "Totes-Meer-Wasser", "Quecksilber")
_MAS = ("masse", "dichte", "material", "flaechenmasse_kg_pro_m2")

class KonfigFehler(ValueError):
    """Verstoss gegen die Regeln der Eingabedatei (Spec J)."""

def _hook(paar):
    gesehen = set()
    for s, _w in paar:
        if s in gesehen:
            raise KonfigFehler("Doppelter Schluessel: '%s'" % s)
        gesehen.add(s)
    return dict(paar)

def _val_teile(eintraege, pfad="boot.teile"):
    if not isinstance(eintraege, list) or not eintraege:
        raise KonfigFehler("%s: Liste fehlt oder ist leer" % pfad)
    for e in eintraege:
        if not isinstance(e, dict) or "name" not in e:
            raise KonfigFehler("%s: Eintrag ohne 'name'" % pfad)
        gesetzt = [s for s in _MAS if s in e]
        if "teile" in e:
            if gesetzt:
                raise KonfigFehler("%s (%s): reine Gruppe ohne Massengroesse (P2.5): %s" % (pfad, e["name"], gesetzt))
            _val_teile(e["teile"], pfad + "." + e["name"])
        elif len(gesetzt) != 1:
            raise KonfigFehler("%s (%s): GENAU EINE Massengroesse noetig, gefunden: %s (P3)" % (pfad, e["name"], gesetzt))

def _val(d):
    for a in _ABS:
        if a not in d:
            raise KonfigFehler("Abschnitt fehlt: '%s'" % a)
    for n in _MAT:
        if n not in d["materialien"]:
            raise KonfigFehler("materialien: '%s' fehlt" % n)
    w = d["wasser"]
    dic = w.get("dichten_kg_pro_m3")
    if not isinstance(dic, dict):
        raise KonfigFehler("wasser.dichten_kg_pro_m3 fehlt")
    for n in _WAS:
        if n not in dic:
            raise KonfigFehler("wasser: '%s' fehlt" % n)
    if w.get("standard") not in dic:
        raise KonfigFehler("wasser.standard: unbekannter Name")
    if "teile" not in d["boot"]:
        raise KonfigFehler("boot.teile fehlt")
    _val_teile(d["boot"]["teile"])
    da = d["darstellung"]
    dl = da.get("delta_helligkeit_unterwasser")
    if not isinstance(dl, (int, float)) or not 0.0 <= float(dl) <= 1.0:
        raise KonfigFehler("darstellung.delta_helligkeit_unterwasser: Zahl [0..1]")
    if not isinstance(da.get("farbe_standard"), str):
        raise KonfigFehler("darstellung.farbe_standard: Hex-String erwartet")

class Konfiguration:
    def __init__(self, daten, pfad):
        self._d = daten; self.pfad = pfad
    @property
    def materialien(self): return dict(self._d["materialien"])
    @property
    def wasser_dichten(self): return dict(self._d["wasser"]["dichten_kg_pro_m3"])
    def wasser_dichte(self, x=None):
        if x is None: x = self._d["wasser"]["standard"]
        if isinstance(x, (int, float)): return float(x)
        try: return float(self._d["wasser"]["dichten_kg_pro_m3"][x])
        except KeyError: raise KonfigFehler("Unbekanntes Wasser: '%s'" % x) from None
    @property
    def boot_teile(self): return self._d["boot"]["teile"]
    @property
    def delta_helligkeit(self): return float(self._d["darstellung"]["delta_helligkeit_unterwasser"])
    @property
    def farbe_standard(self): return self._d["darstellung"]["farbe_standard"]

def lade_konfiguration(pfad=ARBEITSDATEI):
    """Liest und validiert die Arbeitsdatei (kein stiller Fallback, Spec J)."""
    if not os.path.exists(pfad):
        raise KonfigFehler("'%s' nicht gefunden. Bitte den Ordner 'konfigurationen' anlegen und die Datei einmalig aus der Vorlage kopieren: %s. Kein stiller Fallback (Spec J)." % (pfad, VORLAGE_PFAD))
    with open(pfad, encoding="utf-8") as f:
        try:
            d = json.load(f, object_pairs_hook=_hook)
        except json.JSONDecodeError as e:
            raise KonfigFehler("Ungueltiges JSON in %s: %s" % (pfad, e)) from e
    _val(d)
    return Konfiguration(d, pfad)
