"""Versionierte Einstellungen (konfigurationen/settings.json).

Format der Datei:  {"schema_version": "M.N", "<bereich>": {"<schluessel>": wert}}
Die Vorlage (doc/Vorlagen/settings_vorlage.json, zusaetzlich fest im Code) beschreibt
jeden Eintrag mit Default, Einheit, Grenzen und "seit_version".

Kompatibilitaetsregeln (siehe doc/Vorlagen/Settings.md):
- Neue Eintraege nur additiv: Minor erhoehen, Defaults ergaenzen fehlende.
- Umbenennen, Loeschen oder geaenderte Bedeutung: Major erhoehen und eine
  Migration in MIGRATIONEN eintragen.
- Unbekannte Schluessel bleiben beim Speichern erhalten.
"""
from __future__ import annotations

import copy
import json
import os
import shutil

from . import pfeilstil
SCHEMA_VERSION = "1.6"
DATEINAME = "settings.json"
VORLAGE_DATEINAME = "settings_vorlage.json"


def _eintrag(typ, default, beschreibung, einheit="", minimum=None,
             maximum=None, dezimalen=3, seit="1.0"):
    e = {"typ": typ, "default": default, "einheit": einheit,
         "beschreibung": beschreibung, "seit_version": seit}
    if typ in ("float", "int"):
        e["min"] = minimum
        e["max"] = maximum
    if typ == "float":
        e["dezimalen"] = dezimalen
    return e


# Eingebaute Vorlage: Rueckfallebene, falls die Dokumentationsvorlage fehlt.
VORLAGE = {
    "schema_version": SCHEMA_VERSION,
    "statisch": {
        "toleranz": _eintrag(
            "float", 1e-8, "Abbruchtoleranz des Newton-Verfahrens",
            "", 1e-10, 1e-3, 10),
        "max_iterationen": _eintrag(
            "int", 60, "Maximale Newton-Iterationen je Versuch",
            "", 5, 500),
        "stagnation_anteil": _eintrag(
            "float", 0.05, "Anteil der Iterationen ohne Fortschritt "
            "bis zur Stagnationserkennung", "", 0.001, 0.5, 3),
    },
    "dynamisch": {
        "zeitgenau": _eintrag(
            "bool", False, "Legacy-Option; dynamisch wird nur angeforderte "
            "Echtzeit berechnet. Rueckstand wird ohne automatische Pause "
            "angezeigt."),
        "max_schritte_pro_aufgabe": _eintrag(
            "int", 16, "Maximale Physikschritte je Rechenauftrag",
            "Schritte", 1, 256),
        "max_schritte_nachholen": _eintrag(
            "int", 64, "Maximale Physikschritte je Auftrag bei hohem "
            "Echtzeit-Rueckstand", "Schritte", 1, 1024),
        "ueberlast_rueckstand_s": _eintrag(
            "float", 1.0, "Rueckstand, ab dem groessere Rechenauftraege "
            "verwendet werden",
            "s", 0.1, 60.0, 2),
        "ueberlast_dauer_s": _eintrag(
            "float", 5.0, "Legacy-Parameter; Ueberlast loest keine "
            "automatische Pause mehr aus", "s", 0.5, 600.0, 1),
        "nachholen_ende_rueckstand_s": _eintrag(
            "float", 0.1, "Legacy-Parameter; dynamische Zeit wird nicht "
            "mehr durch schnelleres Nachholen vorgespult", "s", 0.01, 5.0, 2),
        "nachholrate_ziel": _eintrag(
            "float", 1.25, "Legacy-Parameter; die Simulation laeuft nicht "
            "schneller als die angeforderte Echtzeit", "s/s", 1.0, 10.0, 2),
    },
    "modell": {
        "paketfabrik_aktiv": _eintrag(
            "bool", True,
            "Paketbasierte Modellfabrik verwenden; ausgeschaltet bleibt "
            "der Legacy-Konfigurationspfad verfügbar",
            seit="1.2"),
    },
    "anzeigen": {
        "schulungs_darstellung": _eintrag(
            "bool", False, "Expliziter Schulungs-Darstellungsmodus: ohne SSAO "
            "und MSAA, reduzierte Wasseroptik; Physik und Lernanzeigen unverändert",
            seit="1.5"),
        "titel_sichtbar": _eintrag(
            "bool", True, "Titel der Instrumentkarten anzeigen", seit="1.3"),
        "titel_beschreibung_sichtbar": _eintrag(
            "bool", True, "Beschreibung unter dem Titel anzeigen",
            seit="1.3"),
        "analog_sichtbar": _eintrag(
            "bool", True, "Analoge Instrumentdarstellung anzeigen",
            seit="1.3"),
        "numerisch_sichtbar": _eintrag(
            "bool", True, "Numerische Instrumentwerte anzeigen",
            seit="1.3"),
        "hydrodynamik_rumpf": _eintrag(
            "bool", True, "Hydrodynamische Detailkraft am Rumpf anzeigen",
            seit="1.4"),
        "hydrodynamik_kiel": _eintrag(
            "bool", True, "Hydrodynamische Detailkraft an Kiel/Schwert anzeigen",
            seit="1.4"),
        "hydrodynamik_ruder": _eintrag(
            "bool", True, "Hydrodynamische Detailkraft am Ruder anzeigen",
            seit="1.4"),
    },
}
# Seit 1.1: Darstellung der Kraft- und Momentenpfeile
VORLAGE.update(pfeilstil.vorlage_bereiche(_eintrag, "1.1"))
VORLAGE["kraefteanzeige"] = {
    "koerperframe": _eintrag(
        "bool", False, "Komponenten im Koerperframe statt im Weltframe",
        seit="1.6"),
    "weltursprung": _eintrag(
        "bool", False, "Momentenbezug Weltursprung statt Koerperschwerpunkt",
        seit="1.6"),
    "komponenten": _eintrag(
        "bool", False, "Momentenkomponenten zusaetzlich zum Gesamtvektor",
        seit="1.6"),
    "mehrkoerper": _eintrag(
        "bool", False, "Alle verfuegbaren Koerpersnapshots getrennt anzeigen",
        seit="1.6"),
    "logarithmisch": _eintrag(
        "bool", False, "Logarithmische statt linearer Kraft-/Momentenskalen",
        seit="1.6"),
    "kraftreferenz_N": _eintrag(
        "float", 0.0, "Manuelle Kraftreferenz; 0: je Koerper initialisieren",
        "N", 0.0, 1e15, 4, seit="1.6"),
    "momentreferenz_Nm": _eintrag(
        "float", 0.0, "Manuelle Momentenreferenz; 0: je Koerper initialisieren",
        "N*m", 0.0, 1e15, 4, seit="1.6"),
    "kraftmaximum_px": _eintrag(
        "float", 180.0, "Maximale Kraftpfeillaenge", "logische px",
        20.0, 1000.0, 1, seit="1.6"),
    "momentmaximum_px": _eintrag(
        "float", 48.0, "Maximaler Momentenradius", "logische px",
        10.0, 500.0, 1, seit="1.6"),
    "breite_px": _eintrag(
        "float", 3.0, "Schaft-/Bogenbreite", "logische px",
        1.0, 20.0, 1, seit="1.6"),
    "kopflaenge_px": _eintrag(
        "float", 10.0, "Pfeilkopflaenge", "logische px",
        2.0, 100.0, 1, seit="1.6"),
    "beschriftung": _eintrag(
        "bool", True, "Auswahl und Gesamtbilanz beschriften", seit="1.6"),
    "fensterlayout": _eintrag(
        "fensterlayout", {}, "Gespeichertes Wertefensterlayout", seit="1.6"),
    "sichtbarkeiten": _eintrag(
        "sichtbarkeiten", {}, "Sichtbarkeit je stabiler Koerper-/Quell-ID",
        seit="1.6"),
}
for _definition in pfeilstil.BEITRAGS_DEFINITIONEN:
    VORLAGE["kraefteanzeige"]["farbe_" + _definition.id] = _eintrag(
        "farbe", _definition.farbe, "Farbe: " + _definition.titel, seit="1.6")


def version_tupel(text):
    teile = str(text).split(".")
    return int(teile[0]), int(teile[1]) if len(teile) > 1 else 0


# Migrationen: {alte_major: funktion(daten) -> daten mit neuer Major-Version}.
MIGRATIONEN = {}


def standard_ordner():
    return os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..",
        "konfigurationen"))


def vorlage_laden(pfad=None):
    """Vorlage aus der Dokumentation; bei Fehler die eingebaute."""
    if pfad is None:
        pfad = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "doc",
            "Vorlagen", VORLAGE_DATEINAME))
    try:
        with open(pfad, encoding="utf-8") as f:
            daten = json.load(f)
        if (version_tupel(daten["schema_version"])[0]
                != version_tupel(SCHEMA_VERSION)[0]):
            raise ValueError("Vorlage hat andere Major-Version")
        for bereich, eintraege in VORLAGE.items():
            if bereich == "schema_version":
                continue
            for schluessel in eintraege:
                daten[bereich][schluessel]["default"]
        return daten
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return copy.deepcopy(VORLAGE)


def wert_pruefen(eintrag, wert):
    """Liefert den bereinigten Wert oder wirft ValueError."""
    typ = eintrag["typ"]
    if typ == "sichtbarkeiten":
        if (not isinstance(wert, dict)
                or any(not isinstance(k, str) or not k
                       or not isinstance(v, dict)
                       or any(not isinstance(q, str) or not q
                              or not isinstance(b, bool) for q, b in v.items())
                       for k, v in wert.items())):
            raise ValueError("Sichtbarkeiten brauchen Koerper-/Quell-IDs und Wahrheitswerte")
        return copy.deepcopy(wert)
    if typ == "fensterlayout":
        if not isinstance(wert, dict):
            raise ValueError("Fensterlayout muss ein Objekt sein")
        if not wert:
            return {}
        if (set(wert) != {"geometrie", "spalten", "frei", "dock", "sichtbar"}
                or not isinstance(wert["geometrie"], str)
                or len(wert["geometrie"]) > 65536
                or not isinstance(wert["frei"], bool)
                or not isinstance(wert["sichtbar"], bool)
                or type(wert["dock"]) is not int
                or wert["dock"] not in (1, 2, 4, 8)
                or not isinstance(wert["spalten"], str)
                or len(wert["spalten"]) > 65536):
            raise ValueError("Ungueltiges Wertefensterlayout")
        try:
            bytes.fromhex(wert["geometrie"])
            bytes.fromhex(wert["spalten"])
        except ValueError as fehler:
            raise ValueError("Fenstergeometrie muss hexadezimal sein") from fehler
        return copy.deepcopy(wert)
    if typ == "farbe":
        if not isinstance(wert, str) or not (
                wert == "" or pfeilstil.FARBE_MUSTER.match(wert)):
            raise ValueError("Farbe im Format #rrggbb erwartet")
        return wert
    if typ == "bool":
        if not isinstance(wert, bool):
            raise ValueError("Wahrheitswert erwartet")
        return wert
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise ValueError("Zahl erwartet")
    if typ == "int":
        if int(wert) != wert:
            raise ValueError("Ganzzahl erwartet")
        wert = int(wert)
    else:
        wert = float(wert)
        if wert != wert or wert in (float("inf"), float("-inf")):
            raise ValueError("endliche Zahl erwartet")
    if wert < eintrag["min"] or wert > eintrag["max"]:
        raise ValueError("ausserhalb [%g, %g]" % (eintrag["min"],
                                                  eintrag["max"]))
    return wert


class Einstellungen:
    def __init__(self, pfad, vorlage=None):
        self.pfad = pfad
        self.vorlage = vorlage or vorlage_laden()
        self.meldungen = []
        self._daten = self._defaults()

    # --- Aufbau ---------------------------------------------------------
    def _defaults(self):
        daten = {"schema_version": SCHEMA_VERSION}
        for bereich, eintraege in self.vorlage.items():
            if bereich == "schema_version":
                continue
            daten[bereich] = {k: copy.deepcopy(e["default"])
                              for k, e in eintraege.items()}
        return daten

    def _bereiche(self):
        return [b for b in self.vorlage if b != "schema_version"]

    @classmethod
    def laden(cls, pfad=None, vorlage=None):
        """Laedt die Datei; fehlende oder ungueltige Werte werden durch
        Defaults ersetzt. Eine neuere Major-Version wird nie ueberschrieben."""
        if pfad is None:
            pfad = os.path.join(standard_ordner(), DATEINAME)
        obj = cls(pfad, vorlage)
        obj._laden()
        return obj

    def _laden(self):
        self._nur_lesen = False
        if not os.path.exists(self.pfad):
            self.meldungen.append("settings.json fehlt - Defaults angelegt")
            self.speichern()
            return
        try:
            with open(self.pfad, encoding="utf-8") as f:
                roh = json.load(f)
            if not isinstance(roh, dict):
                raise ValueError("Wurzel ist kein Objekt")
            version = version_tupel(roh["schema_version"])
        except (OSError, ValueError, KeyError, TypeError, IndexError) as fehler:
            self.meldungen.append(
                "settings.json unlesbar (%s) - Defaults, Sicherung .bak"
                % fehler)
            try:
                shutil.copyfile(self.pfad, self.pfad + ".bak")
            except OSError:
                pass
            self.speichern()
            return
        aktuell = version_tupel(SCHEMA_VERSION)
        if version[0] > aktuell[0]:
            self.meldungen.append(
                "settings.json hat neuere Version %d.%d - Defaults, "
                "Datei bleibt unveraendert" % version)
            self._nur_lesen = True
            return
        geaendert = False
        while version[0] < aktuell[0]:
            migration = MIGRATIONEN.get(version[0])
            if migration is None:
                self.meldungen.append(
                    "Keine Migration ab Version %d - Defaults" % version[0])
                self.speichern()
                return
            roh = migration(roh)
            version = version_tupel(roh["schema_version"])
            geaendert = True
        # Bekannte Werte uebernehmen (geprueft), unbekannte Schluessel erhalten
        ergebnis = dict(roh)
        for bereich in self._bereiche():
            vorhanden = roh.get(bereich)
            if not isinstance(vorhanden, dict):
                vorhanden = {}
                geaendert = True
            neu = dict(vorhanden)
            for k, e in self.vorlage[bereich].items():
                if k not in vorhanden:
                    neu[k] = copy.deepcopy(e["default"])
                    geaendert = True
                    continue
                try:
                    neu[k] = wert_pruefen(e, vorhanden[k])
                except ValueError as fehler:
                    self.meldungen.append(
                        "%s.%s ungueltig (%s) - Default %r"
                        % (bereich, k, fehler, e["default"]))
                    neu[k] = e["default"]
                    geaendert = True
            ergebnis[bereich] = neu
        if version < aktuell:
            geaendert = True
        ergebnis["schema_version"] = SCHEMA_VERSION
        self._daten = ergebnis
        if geaendert:
            self.speichern()

    # --- Zugriff --------------------------------------------------------
    def get(self, bereich, schluessel):
        return copy.deepcopy(self._daten[bereich][schluessel])

    def bereich(self, bereich):
        return dict(self._daten[bereich])

    def setzen(self, bereich, schluessel, wert):
        """Prueft, setzt und speichert sofort. ValueError bei ungueltig."""
        wert = wert_pruefen(self.vorlage[bereich][schluessel], wert)
        if self._daten[bereich][schluessel] == wert:
            return wert
        self._daten[bereich][schluessel] = wert
        self.speichern()
        return wert

    def zuruecksetzen(self, bereich=None):
        """Setzt auf die Defaults der Vorlage zurueck und speichert."""
        for b in ([bereich] if bereich else self._bereiche()):
            for k, e in self.vorlage[b].items():
                self._daten[b][k] = copy.deepcopy(e["default"])
        self.speichern()

    def speichern(self):
        if getattr(self, "_nur_lesen", False):
            return False
        try:
            os.makedirs(os.path.dirname(self.pfad) or ".", exist_ok=True)
            temp = self.pfad + ".tmp"
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(self._daten, f, indent=2, ensure_ascii=False)
                f.write("\n")
            os.replace(temp, self.pfad)
            return True
        except OSError as fehler:
            self.meldungen.append("settings.json nicht speicherbar: %s"
                                  % fehler)
            return False
