"""Darstellung der Kraft- und Momentenpfeile (pyvista-frei).

Registry der Kraeftepaare und Pfeile, Einstellungsvorlage fuer die
Bereiche `kraftpfeile_*`, `pfeil_<id>`, `schwerpunkte`, `hauptachsen` und
`Stil`, der aus den Einstellungen absolute Masse (Meter) je Koerper bildet.

Darstellungsgruppen teilen Farben, erzwingen aber kein physikalisches
Kraeftegleichgewicht. BEITRAGS_DEFINITIONEN ordnet vorhandene Quellen den
historischen Stil-IDs zu; PAARE und PFEILE erhalten deren Einstellungen.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# (id, Titel, Paarfarbe)
PAARE = (
    ("gewicht_auftrieb", "Paar 1: Gewicht / Auftrieb", "#2166ac"),
    ("fremdkraft", "Paar 2: Fremdkraft", "#d73027"),
)

# (id, Titel, Paar-id oder None, Art, Farbe (None = Paarfarbe), sichtbar,
#  gestrichelt). Art: "kraft", "moment" oder "linie".
PFEILE = (
    ("f_g", "Gewichtskraft F_G", "gewicht_auftrieb", "kraft", None, True, False),
    ("f_a", "Auftriebskraft F_A", "gewicht_auftrieb", "kraft",
     None, True, True),
    ("m_x", "Moment M_x (Rollen)", "gewicht_auftrieb", "moment", None,
     False, False),
    ("m_y", "Moment M_y (Nicken)", "gewicht_auftrieb", "moment", None,
     False, False),
    ("m_z", "Moment M_z (Gieren)", "gewicht_auftrieb", "moment", None,
     False, False),
    ("fremd", "Fremdkraft F_fremd", "fremdkraft", "kraft", None, True, False),
    ("fremd_mx", "Fremdmoment M_x", "fremdkraft", "moment", None, False, False),
    ("fremd_my", "Fremdmoment M_y", "fremdkraft", "moment", None, False, False),
    ("fremd_mz", "Fremdmoment M_z", "fremdkraft", "moment", None, False, False),
    ("rest", "Resultierende Kraft", None, "kraft", "#dddddd", True, False),
    ("zusatz", "Widerstand / Added Mass", None, "kraft", "#e08214", True,
     False),
    ("hydro_sum", "Hydrodynamik-Summe", None, "kraft", "#e08214", True,
     False),
    ("mges_x", "Gesamtmoment M_x", None, "moment", "#762a83", True, False),
    ("mges_y", "Gesamtmoment M_y", None, "moment", "#1b7837", True, False),
    ("mges_z", "Gesamtmoment M_z", None, "moment", "#e08214", True, False),
    ("hebelarm", "Senkrechter Hebelarm", None, "linie", "#000000", True, False),
)


@dataclass(frozen=True, slots=True)
class BeitragsDefinition:
    id: str
    gruppe: str
    kraft_id: str
    moment_ids: tuple[str, ...]
    titel: str
    farbe: str
    sichtbar: bool = False
    gestrichelt: bool = False


GRUPPEN_TITEL = {
    "gewicht_auftrieb": "Gewicht und Auftrieb",
    "hydrodynamik": "Hydrodynamik",
    "widerstand": "Allgemeiner Widerstand",
    "fremdkraft": "Test- / Fremdkraft",
    "added_mass": "Added Mass",
    "nicht_zugeordnet": "Nicht zugeordnet",
}


BEITRAGS_DEFINITIONEN = (
    BeitragsDefinition(
        "schwerkraft", "gewicht_auftrieb", "f_g", (),
        "Gewicht F_G", "#2166ac", True),
    BeitragsDefinition(
        "hydrostatik", "gewicht_auftrieb", "f_a", ("m_x", "m_y", "m_z"),
        "Auftrieb F_A", "#2166ac", True, True),
    BeitragsDefinition(
        "widerstand", "widerstand", "zusatz", (),
        "Allgemeiner Widerstand", "#707070"),
    BeitragsDefinition(
        "hydrodynamik_rumpf", "hydrodynamik", "zusatz", (),
        "Hydrodynamik Rumpf", "#e08214"),
    BeitragsDefinition(
        "hydrodynamik_kiel", "hydrodynamik", "zusatz", (),
        "Hydrodynamik Kiel", "#1b7837"),
    BeitragsDefinition(
        "hydrodynamik_ruder", "hydrodynamik", "zusatz", (),
        "Hydrodynamik Ruder", "#762a83"),
    BeitragsDefinition(
        "hydrodynamik_volumenkoerper", "hydrodynamik", "zusatz", (),
        "Hydrodynamik Volumenkoerper", "#008b8b"),
    BeitragsDefinition(
        "fremdkraft", "fremdkraft", "fremd",
        ("fremd_mx", "fremd_my", "fremd_mz"),
        "Test- / Fremdkraft", "#d73027", True),
    BeitragsDefinition(
        "added_mass", "added_mass", "zusatz", (),
        "Added-Mass-Korrektur", "#8c564b"),
)


def beitragsdefinition(quellname: str) -> BeitragsDefinition:
    """Ordnet eine physikalische Quellart zu, nie eine Quellinstanz."""
    if not isinstance(quellname, str) or not quellname:
        raise ValueError("Kraftquelle braucht einen nichtleeren Namen")
    for definition in BEITRAGS_DEFINITIONEN:
        if definition.id == quellname:
            return definition
    return BeitragsDefinition(
        quellname, "nicht_zugeordnet", "zusatz", (),
        "Nicht zugeordnet: " + quellname, "#cc00cc")


BEREICH_ALLGEMEIN = "kraftpfeile_allgemein"
BEREICH_PAARE = "kraftpfeile_paare"
BEREICH_SCHWERPUNKTE = "schwerpunkte"
BEREICH_HAUPTACHSEN = "hauptachsen"

TITEL = {
    BEREICH_ALLGEMEIN: "Kraftpfeildarstellung: Allgemein",
    BEREICH_PAARE: "Kraftpfeildarstellung: Paarfarben",
    BEREICH_SCHWERPUNKTE: "Kraftpfeildarstellung: Schwerpunkte",
    BEREICH_HAUPTACHSEN: "Kraftpfeildarstellung: Hauptachsen",
}

FARBE_MUSTER = re.compile(r"^#[0-9a-fA-F]{6}$")


def pfeil_bereich(pfeil_id):
    return "pfeil_" + pfeil_id


def paar_pfeile(paar_id):
    return [p for p in PFEILE if p[2] == paar_id]


def paarlose_pfeile():
    return [p for p in PFEILE if p[2] is None]


def vorlage_bereiche(eintrag, seit="1.1"):
    """Vorlage der Darstellungs-Bereiche. `eintrag` ist die Fabrik
    `_eintrag(typ, default, beschreibung, einheit, min, max, dezimalen,
    seit)` aus core.einstellungen."""
    def e(typ, default, text, einheit="", lo=None, hi=None, dez=3):
        return eintrag(typ, default, text, einheit, lo, hi, dez, seit)

    ergebnis = {
        BEREICH_ALLGEMEIN: {
            "vordergrund": e(
                "bool", True, "Pfeile und Schwerpunkte immer im "
                "Vordergrund (durch den Koerper sichtbar)"),
            "dicke": e(
                "float", 0.5, "Grunddicke des Pfeilschafts (Prozent der "
                "Koerperausdehnung)", "%", 0.05, 5.0, 2),
            "kopf_durchmesser": e(
                "float", 2.5, "Pfeilkopf-Durchmesser (Faktor auf die "
                "Dicke)", "x", 1.2, 10.0, 2),
            "kopf_laenge": e(
                "float", 5.0, "Pfeilkopf-Laenge (Faktor auf die Dicke)",
                "x", 1.0, 20.0, 2),
            "kraftskala": e(
                "float", 0.05, "Historischer Kraftfaktor: 0,05 entspricht 1x "
                "auf die Pixelabbildung (kein Weltmassstab mehr)",
                "cm/N", 0.0001, 100.0, 4),
            "momentskala": e(
                "float", 0.05, "Historischer Momentenfaktor: 0,05 entspricht 1x "
                "auf die Pixelabbildung (kein Weltmassstab mehr)",
                "cm/Nm", 0.0001, 100.0, 4),
            "mindestlaenge": e(
                "float", 2.0, "Historische Mindestgroesse: 2 entspricht "
                "1 logischem Pixel Kleinwertgrenze; keine Pfeilverlaengerung",
                "%", 0.0, 20.0, 2),
            "strich_laenge": e(
                "float", 3.0, "Strichlaenge gestrichelter Pfeile "
                "(Prozent der Koerperausdehnung)", "%", 0.2, 30.0, 2),
            "strich_luecke": e(
                "float", 2.0, "Luecke gestrichelter Pfeile (Prozent der "
                "Koerperausdehnung)", "%", 0.2, 30.0, 2),
        },
        BEREICH_PAARE: {
            "farbe_" + pid: e("farbe", farbe, "Farbe von " + titel)
            for pid, titel, farbe in PAARE},
        BEREICH_SCHWERPUNKTE: {
            "s_radius": e("float", 1.5, "Radius Schwerpunkt S (Prozent der "
                          "Koerperausdehnung)", "%", 0.2, 10.0, 2),
            "s_farbe": e("farbe", "#ffffff", "Farbe Schwerpunkt S"),
            "s_kontur": e("farbe", "#000000",
                          "Konturfarbe Schwerpunkt S (leer: keine Kontur)"),
            "k_radius": e("float", 1.5, "Radius Auftriebsschwerpunkt K "
                          "(Prozent der Koerperausdehnung)", "%", 0.2,
                          10.0, 2),
            "k_farbe": e("farbe", "", "Farbe Auftriebsschwerpunkt K "
                         "(leer: Farbe von Paar 1)"),
            "kontur_breite": e("float", 0.3, "Breite der Kontur relativ "
                               "zum Radius", "", 0.05, 1.0, 2),
            "vordergrund": e("bool", True, "Schwerpunkte im Vordergrund"),
        },
        BEREICH_HAUPTACHSEN: {
            "dicke": e("float", 0.8, "Dicke der Hauptachsen (Prozent der "
                       "Koerperausdehnung)", "%", 0.05, 5.0, 2),
            "farbe_x": e("farbe", "#ffd700", "Farbe Hauptachse 1"),
            "farbe_y": e("farbe", "#00ffff", "Farbe Hauptachse 2"),
            "farbe_z": e("farbe", "#ff00ff", "Farbe Hauptachse 3"),
            "vordergrund": e("bool", False, "Hauptachsen im Vordergrund"),
        },
    }
    for pid, titel, paar, art, farbe, sichtbar, strich in PFEILE:
        eintraege = {
            "sichtbar": e("bool", sichtbar, "Pfeil anzeigen"),
            "farbe": e("farbe", farbe or "", "Farbe (leer: Paarfarbe)"),
            "dicke": e("float", 0.0, "Dicke in Prozent der Koerperausdehnung "
                       "(0: Grunddicke)", "%", 0.0, 5.0, 2),
            "kopf": e("float", 1.0, "Kopfgroesse (Faktor)", "x", 0.2, 5.0, 2),
            "gestrichelt": e("bool", strich, "gestrichelt"),
            "skala": e("float", 1.0, "Skalierung (Faktor; bei Momenten auf "
                       "den Bogenradius)", "x", 0.01, 100.0, 2),
            "deckkraft": e("float", 1.0, "Deckkraft", "", 0.1, 1.0, 2),
            "vordergrund": e("bool", True, "im Vordergrund"),
        }
        ergebnis[pfeil_bereich(pid)] = eintraege
    return ergebnis


def standard_bereiche():
    """Defaults aller Darstellungs-Bereiche (ohne Einstellungsdatei)."""
    def fabrik(typ, default, text, einheit, lo, hi, dez, seit):
        return {"default": default}
    return {b: {k: v["default"] for k, v in eintraege.items()}
            for b, eintraege in vorlage_bereiche(fabrik).items()}


def _hex(farbe, ersatz):
    return farbe if FARBE_MUSTER.match(farbe or "") else ersatz


class Stil:
    """Absolute Darstellungsmasse (m) aus den Einstellungen je Koerper."""

    def __init__(self, bereich=None):
        """bereich: Funktion name -> {schluessel: wert} (z. B.
        Einstellungen.bereich); ohne Angabe gelten die Defaults."""
        standard = standard_bereiche()
        self._hol = bereich or (lambda name: standard[name])
        self._standard = standard

    def _b(self, name):
        try:
            werte = dict(self._hol(name))
        except (KeyError, TypeError):
            werte = {}
        for k, v in self._standard[name].items():
            werte.setdefault(k, v)
        return werte

    def anzeige(self):
        from .einstellungen import VORLAGE
        werte = {k: e["default"] for k, e in VORLAGE["kraefteanzeige"].items()}
        if self._hol is not None:
            try:
                vorhanden = self._hol("kraefteanzeige")
            except KeyError:
                vorhanden = {}
            werte.update(vorhanden)
        return werte

    def beitragsfarbe(self, definition):
        farbe = self.anzeige()["farbe_" + definition.id] if any(
            d.id == definition.id for d in BEITRAGS_DEFINITIONEN) else definition.farbe
        if farbe != definition.farbe:
            return farbe
        pfeil = next(p for p in PFEILE if p[0] == definition.kraft_id)
        individuell = self._b(pfeil_bereich(definition.kraft_id))["farbe"]
        standard = self._standard[pfeil_bereich(definition.kraft_id)]["farbe"]
        if individuell and individuell != standard:
            return individuell
        if pfeil[2] is not None:
            return self.paarfarbe(pfeil[2])
        bisher = self.pfeil(definition.kraft_id, 1)["farbe"]
        return bisher if bisher != (standard or pfeil[4]) else farbe

    def beitragsstil(self, beitrag, ausdehnung):
        summe = beitrag.herkunft in ("Gruppensumme", "Gesamtsumme")
        definition = beitragsdefinition(beitrag.name)
        pfeil_id = ("hydro_sum" if beitrag.gruppe == "hydrodynamik" else "rest"
                    ) if summe else definition.kraft_id
        stil = self.pfeil(pfeil_id, ausdehnung)
        stil["sichtbar"] = stil["sichtbar"] and (
            beitrag.herkunft == "Gesamtsumme" if summe else definition.sichtbar)
        if beitrag.herkunft == "Gruppensumme":
            rolle = next((d for d in BEITRAGS_DEFINITIONEN
                          if d.gruppe == beitrag.gruppe), definition)
            stil["farbe"] = self.beitragsfarbe(rolle)
        elif not summe:
            stil["farbe"] = self.beitragsfarbe(definition)
        stil["kontur"] = "#333333" if beitrag.herkunft == "Gesamtsumme" else None
        return stil

    def bildschirmstil(self, stil, ausdehnung, welt_pro_pixel):
        optionen = self.anzeige()
        dicke = stil["durchmesser"] / (.005 * ausdehnung)
        kopf = stil["kopf_laenge"] / (5 * stil["durchmesser"])
        kopfbreite = stil["kopf_durchmesser"] / (2.5 * stil["durchmesser"])
        return {
            **stil,
            "durchmesser": optionen["breite_px"] * dicke * welt_pro_pixel,
            "kopf_laenge": optionen["kopflaenge_px"] * kopf * welt_pro_pixel,
            "kopf_durchmesser": 7 * kopfbreite * welt_pro_pixel,
            "strich": 8 * welt_pro_pixel * stil["strich"] / (.03 * ausdehnung),
            "luecke": 5 * welt_pro_pixel * stil["luecke"] / (.02 * ausdehnung),
            "kraftfaktor": stil["skala"] * stil["kraftskala"] / .0005,
            "momentfaktor": stil["skala"] * stil["momentskala"] / .0005,
            "kleinwert_px": max(1, stil["mindestlaenge"] / (.02 * ausdehnung)),
        }

    def momentkomponenten(self, beitrag, ausdehnung, grundstil=None):
        ids = (("mges_x", "mges_y", "mges_z")
               if beitrag.herkunft == "Gesamtsumme"
               else beitragsdefinition(beitrag.name).moment_ids)
        global_an = self.anzeige()["komponenten"]
        grundstil = grundstil or self.beitragsstil(beitrag, ausdehnung)
        ergebnis = []
        for i in range(3):
            stil = grundstil
            an = global_an
            if ids:
                b = pfeil_bereich(ids[i])
                alt = self._b(b)
                if alt["sichtbar"] != self._standard[b]["sichtbar"]:
                    an = alt["sichtbar"]
                if not an:
                    ergebnis.append((False, stil))
                    continue
                individuell = self.pfeil(ids[i], ausdehnung)
                individuell["kontur"] = grundstil.get("kontur")
                # Quellenfarbe erben, ausser bei expliziter Ueberschreibung.
                if not alt["farbe"] or alt["farbe"] == self._standard[b]["farbe"]:
                    individuell["farbe"] = stil["farbe"]
                stil = individuell
            ergebnis.append((an, stil))
        return tuple(ergebnis)

    def allgemein(self, ausdehnung):
        a = self._b(BEREICH_ALLGEMEIN)
        p = ausdehnung / 100.0
        return {
            "vordergrund": bool(a["vordergrund"]),
            "durchmesser": a["dicke"] * p,
            "kopf_durchmesser": float(a["kopf_durchmesser"]),
            "kopf_laenge": float(a["kopf_laenge"]),
            "kraftskala": float(a["kraftskala"]) / 100.0,
            "momentskala": float(a["momentskala"]) / 100.0,
            "mindestlaenge": a["mindestlaenge"] * p,
            "strich": a["strich_laenge"] * p,
            "luecke": a["strich_luecke"] * p,
        }

    def paarfarbe(self, paar_id):
        ersatz = dict((p[0], p[2]) for p in PAARE).get(paar_id, "#888888")
        return _hex(self._b(BEREICH_PAARE).get("farbe_" + paar_id), ersatz)

    def pfeil(self, pfeil_id, ausdehnung):
        """Wirksame Darstellung eines Pfeils (Durchmesser, Kopf in m)."""
        eintrag = next(p for p in PFEILE if p[0] == pfeil_id)
        w = self._b(pfeil_bereich(pfeil_id))
        a = self.allgemein(ausdehnung)
        standard_farbe = (self.paarfarbe(eintrag[2]) if eintrag[2]
                          else (eintrag[4] or "#888888"))
        durchmesser = (w["dicke"] * ausdehnung / 100.0
                       if w["dicke"] > 0.0 else a["durchmesser"])
        return {
            "id": pfeil_id, "art": eintrag[3], "paar": eintrag[2],
            "sichtbar": bool(w["sichtbar"]),
            "farbe": _hex(w["farbe"], standard_farbe),
            "durchmesser": durchmesser,
            "kopf_durchmesser": (a["kopf_durchmesser"] * durchmesser
                                 * w["kopf"]),
            "kopf_laenge": a["kopf_laenge"] * durchmesser * w["kopf"],
            "gestrichelt": bool(w["gestrichelt"]),
            "skala": float(w["skala"]),
            "deckkraft": float(w["deckkraft"]),
            "vordergrund": bool(w["vordergrund"]) and a["vordergrund"],
            "mindestlaenge": a["mindestlaenge"],
            "strich": a["strich"], "luecke": a["luecke"],
            "kraftskala": a["kraftskala"],
            "momentskala": a["momentskala"],
        }

    def schwerpunkte(self, ausdehnung):
        s = self._b(BEREICH_SCHWERPUNKTE)
        p = ausdehnung / 100.0
        a = self.allgemein(ausdehnung)
        return {
            "s_radius": s["s_radius"] * p,
            "s_farbe": _hex(s["s_farbe"], "#ffffff"),
            "s_kontur": _hex(s["s_kontur"], ""),
            "k_radius": s["k_radius"] * p,
            "k_farbe": _hex(s["k_farbe"], self.paarfarbe("gewicht_auftrieb")),
            "kontur_breite": float(s["kontur_breite"]),
            "vordergrund": bool(s["vordergrund"]) and a["vordergrund"],
        }

    def hauptachsen(self, ausdehnung):
        h = self._b(BEREICH_HAUPTACHSEN)
        a = self.allgemein(ausdehnung)
        return {
            "durchmesser": h["dicke"] * ausdehnung / 100.0,
            "farben": (_hex(h["farbe_x"], "#ffd700"),
                       _hex(h["farbe_y"], "#00ffff"),
                       _hex(h["farbe_z"], "#ff00ff")),
            "vordergrund": bool(h["vordergrund"]) and a["vordergrund"],
        }
