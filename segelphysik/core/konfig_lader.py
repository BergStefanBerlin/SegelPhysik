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

Glanz (Schritt 4, K3): optionaler Schluessel 'glanz' [0..1] im MATERIAL-Block
(Anknuepfung an die Materialtabelle, Spec P7). Fehlt er, gilt 0.15 (matt).

physik.json (D8, Umsetzungsplan V5 rev 9 §6): dritte Eingabedatei nach dem
P3-Muster - dt, g, Daempfung (Tauchung/Kraengung getrennt), Voxel-Parameter
(Aufloesung + zwei getrennte Schranken fuer Volumen und Punktlage, F24).
Vorlage: doc/physik_vorlage.json. Lader: lade_physik().
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

def _nichtnegative_zahl(w, wo):
    if isinstance(w, bool) or not isinstance(w, (int, float)) or w < 0:
        raise KonfigFehler(
            "%s: nicht-negative Zahl erwartet, gefunden: %r" % (wo, w))
    return float(w)

def _val_hex(w, wo):
    if (not isinstance(w, str) or not w.startswith("#")
            or len(w) not in (4, 7)):
        raise KonfigFehler("%s: Hex-Farbe (#rgb oder #rrggbb) erwartet, "
                           "gefunden: %r" % (wo, w))
    erlaubt = set("0123456789abcdefABCDEF")
    if any(z not in erlaubt for z in w[1:]):
        raise KonfigFehler("%s: ungueltige Hex-Zeichen in %r" % (wo, w))

GLANZ_DEFAULT = 0.15

def _val_glanz(w, wo):
    """K3: Glanzgrad [0..1] (0 = matt, 1 = Spiegel)."""
    ok = (not isinstance(w, bool)) and isinstance(w, (int, float))
    if (not ok) or (not 0.0 <= float(w) <= 1.0):
        raise KonfigFehler("%s: Zahl [0..1] erwartet, gefunden: %r" % (wo, w))

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
        if "glanz" in block:
            _val_glanz(block["glanz"], "%s.glanz" % hier)
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
    def glanz_von(self, material):
        """K3: Glanzgrad [0..1] zu Material-Name; GLANZ_DEFAULT wenn nicht gesetzt."""
        if isinstance(material, str):
            try:
                b = self._m["materialien"][material]
            except KeyError:
                raise KonfigFehler("Unbekanntes Material: '%s'" % material) from None
            return float(b.get("glanz", GLANZ_DEFAULT))
        return GLANZ_DEFAULT

def lade_konfig(ordner=KONFIG_ORDNER):
    """Liest und validiert BEIDE Konfig-Dateien (kein stiller Fallback, Spec J)."""
    mpfad = os.path.join(ordner, MATERIAL_DATEI)
    kpfad = os.path.join(ordner, KOERPER_DATEI)
    m = _lies(mpfad, VORLAGE_MATERIAL)
    k = _lies(kpfad, VORLAGE_KOERPER)
    _val_materialien(m, mpfad)
    _val_koerper(k, m["materialien"], kpfad)
    return Konfiguration(m, k, ordner)


# ---------------- physik.json (D8, Umsetzungsplan V5 rev 9 §6) ----------------

PHYSIK_DATEI = "physik.json"
VORLAGE_PHYSIK = os.path.join("doc", "physik_vorlage.json")

_PHYSIK_ERLAUBT = ("dt_s", "g_m_pro_s2", "daempfung", "voxel")
_DAEMPFUNG_ERLAUBT = ("tauchung", "kraengung")
_VOXEL_ERLAUBT = ("aufloesung_m", "schranke_volumen_m3", "schranke_punkt_m")


class PhysikParameter:
    """Unveraenderliche Physik-Parameter aus physik.json (D8).

    Daempfung (D2): Uebergangsmodell - zunaechst stark (kaum Schwingung,
    quasi-aperiodisch), spaeter Ersatz durch Hydro-/Aerodynamik.
    Voxel (D7/D10): Aufloesung = fester Betriebswert; die Halbierungs-
    Kalibrierung ist eine einmalige Vorschrift (F22). Zwei getrennte
    Schranken: Volumen (m^3) und Punktlage (m) (F24).
    """

    __slots__ = ("dt_s", "g_m_pro_s2", "daempfung_tauchung",
                 "daempfung_kraengung", "voxel_aufloesung_m",
                 "schranke_volumen_m3", "schranke_punkt_m")

    def __init__(self, dt_s, g_m_pro_s2, daempfung_tauchung,
                 daempfung_kraengung, voxel_aufloesung_m,
                 schranke_volumen_m3, schranke_punkt_m):
        self.dt_s = dt_s
        self.g_m_pro_s2 = g_m_pro_s2
        self.daempfung_tauchung = daempfung_tauchung
        self.daempfung_kraengung = daempfung_kraengung
        self.voxel_aufloesung_m = voxel_aufloesung_m
        self.schranke_volumen_m3 = schranke_volumen_m3
        self.schranke_punkt_m = schranke_punkt_m

    def __repr__(self):
        return ("PhysikParameter(dt=%g s, g=%g, daempfung=(%g, %g), "
                "voxel=%g m, schranken=(%g m^3, %g m))"
                % (self.dt_s, self.g_m_pro_s2, self.daempfung_tauchung,
                   self.daempfung_kraengung, self.voxel_aufloesung_m,
                   self.schranke_volumen_m3, self.schranke_punkt_m))


def _val_physik(d, pfad):
    if not isinstance(d, dict):
        raise KonfigFehler("%s: Objekt erwartet" % pfad)
    fremd_top = [s for s in d if s != "physik" and not s.startswith("_")]
    if fremd_top or "physik" not in d:
        raise KonfigFehler(
            "%s: alleiniger Abschnitt 'physik' erwartet, fremd: %s"
            % (pfad, fremd_top))
    p = d["physik"]
    if not isinstance(p, dict):
        raise KonfigFehler("%s.physik: Objekt erwartet" % pfad)
    fremd = [s for s in p if s not in _PHYSIK_ERLAUBT and not s.startswith("_")]
    if fremd:
        raise KonfigFehler(
            "%s.physik: unbekannte Schluessel %s (erlaubt: %s; "
            "Unterstrich-Schluessel sind Doku)"
            % (pfad, fremd, ", ".join(_PHYSIK_ERLAUBT)))
    dt = _positive_zahl(p.get("dt_s"), "%s.physik.dt_s" % pfad)
    g = _positive_zahl(p.get("g_m_pro_s2"), "%s.physik.g_m_pro_s2" % pfad)
    dae = p.get("daempfung")
    if not isinstance(dae, dict):
        raise KonfigFehler("%s.physik.daempfung: Objekt erwartet" % pfad)
    fremd_d = [s for s in dae
               if s not in _DAEMPFUNG_ERLAUBT and not s.startswith("_")]
    if fremd_d:
        raise KonfigFehler(
            "%s.physik.daempfung: unbekannte Schluessel %s (erlaubt: %s)"
            % (pfad, fremd_d, ", ".join(_DAEMPFUNG_ERLAUBT)))
    d_tauc = _nichtnegative_zahl(dae.get("tauchung"),
                                 "%s.physik.daempfung.tauchung" % pfad)
    d_krae = _nichtnegative_zahl(dae.get("kraengung"),
                                 "%s.physik.daempfung.kraengung" % pfad)
    vox = p.get("voxel")
    if not isinstance(vox, dict):
        raise KonfigFehler("%s.physik.voxel: Objekt erwartet" % pfad)
    fremd_v = [s for s in vox
               if s not in _VOXEL_ERLAUBT and not s.startswith("_")]
    if fremd_v:
        raise KonfigFehler(
            "%s.physik.voxel: unbekannte Schluessel %s (erlaubt: %s)"
            % (pfad, fremd_v, ", ".join(_VOXEL_ERLAUBT)))
    auf = _positive_zahl(vox.get("aufloesung_m"),
                         "%s.physik.voxel.aufloesung_m" % pfad)
    sv = _positive_zahl(vox.get("schranke_volumen_m3"),
                        "%s.physik.voxel.schranke_volumen_m3" % pfad)
    sp = _positive_zahl(vox.get("schranke_punkt_m"),
                        "%s.physik.voxel.schranke_punkt_m" % pfad)
    return dict(dt_s=dt, g_m_pro_s2=g, daempfung_tauchung=d_tauc,
                daempfung_kraengung=d_krae, voxel_aufloesung_m=auf,
                schranke_volumen_m3=sv, schranke_punkt_m=sp)


def lade_physik(ordner=KONFIG_ORDNER):
    """Liest und validiert physik.json (D8; kein stiller Fallback, Spec J)."""
    pfad = os.path.join(ordner, PHYSIK_DATEI)
    d = _lies(pfad, VORLAGE_PHYSIK)
    w = _val_physik(d, pfad)
    return PhysikParameter(**w)
