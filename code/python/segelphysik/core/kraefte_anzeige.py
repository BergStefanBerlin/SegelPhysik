"""Unveraenderliche Anzeigedaten aus vorhandenen Kraftmodell-Ergebnissen."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import math

import numpy as np

from .frames import Pose
from .kraftmodell import KraftErgebnis, Wrench, aggregiere_kraftbeitraege, Kraftbeitrag
from .pfeilstil import beitragsdefinition

AnzeigeId = tuple[str, str]
Vektor3 = tuple[float, float, float]


class Datenstatus(str, Enum):
    GUELTIG = "aktiv"
    NULL = "null"
    FEHLEND = "fehlend"
    NICHT_BERECHNET = "nicht berechnet"
    DEAKTIVIERT = "deaktiviert"
    UNGUELTIG = "ungueltig"
    VERALTET = "veraltet"


GUELTIGE_STATUS = frozenset((Datenstatus.GUELTIG, Datenstatus.NULL))


def _punkt(werte, name: str) -> Vektor3:
    array = np.asarray(werte, dtype=np.float64)
    if array.shape != (3,) or not np.isfinite(array).all():
        raise ValueError("%s braucht drei endliche Werte" % name)
    return tuple(float(wert) for wert in array)


@dataclass(frozen=True, slots=True)
class Quellbezug:
    """Explizite Identitaet vom Erzeuger, unabhaengig von Ergebnisreihenfolge."""

    quell_id: str
    name: str
    status: Datenstatus = Datenstatus.GUELTIG
    originalangriff_m: Vektor3 | None = None

    def __post_init__(self):
        if (not isinstance(self.quell_id, str) or not self.quell_id
                or not isinstance(self.name, str) or not self.name):
            raise ValueError("Quell-ID und Quellname duerfen nicht leer sein")
        object.__setattr__(self, "status", Datenstatus(self.status))
        if self.originalangriff_m is not None:
            object.__setattr__(self, "originalangriff_m",
                               _punkt(self.originalangriff_m, "Originalangriff"))


@dataclass(frozen=True, slots=True)
class BeitragsAnzeige:
    instanz_id: AnzeigeId
    name: str
    gruppe: str
    wrench: Wrench | None
    status: Datenstatus
    herkunft: str
    quell_ids: tuple[AnzeigeId, ...]
    originalangriff_m: Vektor3 | None = None

    def __post_init__(self):
        instanz_id = tuple(self.instanz_id)
        quell_ids = tuple(tuple(q) for q in self.quell_ids)
        if any(len(q) != 2 or any(not isinstance(w, str) or not w for w in q)
               for q in (instanz_id, *quell_ids)):
            raise ValueError("Anzeige-IDs brauchen Koerper- und Quellkennung")
        if self.wrench is not None and not isinstance(self.wrench, Wrench):
            raise TypeError("Anzeigewerte brauchen einen Wrench")
        status = Datenstatus(self.status)
        if any(not isinstance(w, str) or not w
               for w in (self.name, self.gruppe, self.herkunft)):
            raise ValueError("Anzeigename, Gruppe und Herkunft muessen benannt sein")
        if self.wrench is None and status in GUELTIGE_STATUS:
            raise ValueError("Gueltige Anzeigewerte brauchen einen Wrench")
        if status == Datenstatus.NULL and self.wrench is not None and not _null(self.wrench):
            raise ValueError("Nullstatus widerspricht dem Wrench")
        object.__setattr__(self, "instanz_id", instanz_id)
        object.__setattr__(self, "quell_ids", quell_ids)
        object.__setattr__(self, "status", status)
        if self.originalangriff_m is not None:
            object.__setattr__(self, "originalangriff_m",
                               _punkt(self.originalangriff_m, "Originalangriff"))

    @property
    def punktart(self) -> str:
        return ("realer Angriff" if self.originalangriff_m is not None
                else "Momentenbezug")


@dataclass(frozen=True, slots=True)
class SolverBewertung:
    """Unveraenderter Solverentscheid mit explizitem Zustands-/Quellenbezug."""

    koerper_id: str
    generation: int
    sequenz: int
    quell_ids: tuple[str, ...]
    quelle: str
    freiheitsgrade: tuple[str, ...]
    kriterien: tuple[tuple[str, float, float], ...]
    erfuellt: bool
    stationaer: bool = False

    def __post_init__(self):
        _identitaet(self.koerper_id, self.generation, self.sequenz)
        ids = tuple(self.quell_ids)
        if (len(set(ids)) != len(ids)
                or any(not isinstance(q, str) or not q for q in ids)):
            raise ValueError("Solverbewertung braucht eindeutige Quell-IDs")
        freiheitsgrade = tuple(self.freiheitsgrade)
        if (not isinstance(self.quelle, str) or not self.quelle or not freiheitsgrade
                or len(set(freiheitsgrade)) != len(freiheitsgrade)
                or not set(freiheitsgrade) <= {
                    "x", "y", "z", "rollen", "nicken", "gieren"}):
            raise ValueError("Solverquelle und gepruefte Freiheitsgrade fehlen")
        kriterien = tuple((name, float(residuum), float(toleranz))
                          for name, residuum, toleranz in self.kriterien)
        if not kriterien or any(
                not isinstance(name, str) or not name or not math.isfinite(residuum)
                or not math.isfinite(toleranz) or toleranz <= 0
                for name, residuum, toleranz in kriterien):
            raise ValueError("Solverkriterien brauchen endliche Werte und Grenzen")
        if not isinstance(self.erfuellt, bool) or not isinstance(self.stationaer, bool):
            raise ValueError("Solverentscheid muss boolesch sein")
        object.__setattr__(self, "quell_ids", ids)
        object.__setattr__(self, "freiheitsgrade", freiheitsgrade)
        object.__setattr__(self, "kriterien", kriterien)


@dataclass(frozen=True, slots=True)
class KraefteAnzeigeSnapshot:
    koerper_id: str
    generation: int
    sequenz: int
    zeit_s: float
    kraftpose: Pose
    beitraege: tuple[BeitragsAnzeige, ...]
    gruppen: tuple[BeitragsAnzeige, ...]
    bilanz: BeitragsAnzeige
    rechenbilanz: Wrench
    vollstaendigkeit: str
    fehlende_quellen: tuple[AnzeigeId, ...]
    solverbewertung: SolverBewertung | None
    szenenversatz_m: Vektor3 = (0.0, 0.0, 0.0)
    modellhinweise: tuple[str, ...] = ()

    def __post_init__(self):
        _identitaet(self.koerper_id, self.generation, self.sequenz)
        zeit_s = float(self.zeit_s)
        if not math.isfinite(zeit_s):
            raise ValueError("Snapshotzeit muss endlich sein")
        if (not isinstance(self.kraftpose, Pose)
                or not isinstance(self.rechenbilanz, Wrench)
                or (self.solverbewertung is not None
                    and not isinstance(self.solverbewertung, SolverBewertung))):
            raise TypeError("Snapshot braucht unveraenderliche fachliche Daten")
        beitraege, gruppen = tuple(self.beitraege), tuple(self.gruppen)
        if not all(isinstance(b, BeitragsAnzeige)
                   for b in (*beitraege, *gruppen, self.bilanz)):
            raise TypeError("Snapshoteintraege brauchen unveraenderliche Anzeigedaten")
        if self.vollstaendigkeit not in ("vollstaendig", "teilsumme", "ungeklaert"):
            raise ValueError("Unbekannter Vollstaendigkeitsstatus")
        fehlende = tuple(tuple(q) for q in self.fehlende_quellen)
        if not set(fehlende) <= {b.instanz_id for b in beitraege}:
            raise ValueError("Fehlende Quelle ist nicht im Snapshot enthalten")
        object.__setattr__(self, "zeit_s", zeit_s)
        object.__setattr__(self, "beitraege", beitraege)
        object.__setattr__(self, "gruppen", gruppen)
        object.__setattr__(self, "fehlende_quellen", fehlende)
        object.__setattr__(self, "szenenversatz_m",
                           _punkt(self.szenenversatz_m, "Szenenversatz"))
        hinweise = tuple(self.modellhinweise)
        if any(not isinstance(h, str) or not h.strip() for h in hinweise):
            raise ValueError("Modellhinweise brauchen nichtleere Texte")
        object.__setattr__(self, "modellhinweise", hinweise)

    @property
    def gleichgewichtsstatus(self) -> str:
        if self.vollstaendigkeit != "vollstaendig":
            return "nicht bewertbar"
        bewertung = self.solverbewertung
        if bewertung is None:
            return "Gleichgewicht nicht bewertet"
        if not bewertung.erfuellt:
            return "Kriterien nicht erfuellt"
        if bewertung.stationaer:
            return "stationaerer Zustand gemaess Solver"
        if len(bewertung.freiheitsgrade) < 6:
            return "Teilgleichgewicht gemaess Solver"
        return "Im Gleichgewicht"


def _identitaet(koerper_id, generation, sequenz):
    if not isinstance(koerper_id, str) or not koerper_id:
        raise ValueError("Snapshot braucht eine stabile Koerper-ID")
    if any(type(wert) is not int or wert < 0 for wert in (generation, sequenz)):
        raise ValueError("Generation und Sequenz muessen nichtnegative Integer sein")


def _null(wrench: Wrench) -> bool:
    return all(wert == 0.0 for wert in (*wrench.kraft_N, *wrench.moment_Nm))


def _summe(beitraege, punkt, frame):
    return aggregiere_kraftbeitraege(
        tuple(Kraftbeitrag(b.name, b.wrench) for b in beitraege
              if b.status in GUELTIGE_STATUS and b.wrench is not None),
        punkt, frame)[0]


class KraefteAnzeigeAdapter:
    def aus_ergebnis(
            self, ergebnis: KraftErgebnis, *, koerper_id: str,
            generation: int, sequenz: int, zeit_s: float,
            masse_kg: float, g_m_s2: float,
            solverbewertung: SolverBewertung | None = None,
    ) -> KraefteAnzeigeSnapshot:
        if ergebnis.kraftpose is None:
            raise ValueError("Kraftergebnis enthaelt keine ausgewertete Kraftpose")
        if any(not b.quell_id for b in ergebnis.beitraege):
            raise ValueError("Kraftergebnis enthaelt einen Beitrag ohne Quellinstanz-ID")
        quellen = tuple(Quellbezug(
            b.quell_id, b.name, originalangriff_m=b.originalangriff_m)
            for b in ergebnis.beitraege)
        erwartet = quellen
        if not ergebnis.schwerkraft_beruecksichtigt:
            erwartet += (Quellbezug("schwerkraft", "schwerkraft"),)
        if (any(ergebnis.added_mass_diagonal)
                and not any(b.name == "added_mass" for b in ergebnis.beitraege)):
            erwartet += (Quellbezug(
                "added_mass", "added_mass", Datenstatus.NICHT_BERECHNET),)
        snapshot = self.snapshot(
            ergebnis, koerper_id=koerper_id, generation=generation,
            sequenz=sequenz, zeit_s=zeit_s, kraftpose=ergebnis.kraftpose,
            quellen=quellen, erwartet=erwartet, masse_kg=masse_kg,
            g_m_s2=g_m_s2, solverbewertung=solverbewertung)
        if ((any(ergebnis.linear_widerstand)
             or any(ergebnis.quadratischer_widerstand))
                and any(b.name.startswith("hydrodynamik_")
                        for b in ergebnis.beitraege)):
            snapshot = replace(snapshot, modellhinweise=(
                "Modellueberlagerung: allgemeiner Widerstand und "
                "geometriebezogene Hydrodynamik gleichzeitig konfiguriert; "
                "fachliche Ergaenzung oder Doppelmodellierung ungeklaert. "
                "Beide Quellen bleiben unveraendert in der Solverbilanz. "
                f"Linearer Widerstand (6D): {ergebnis.linear_widerstand}; "
                f"quadratischer Widerstand (6D): {ergebnis.quadratischer_widerstand}.",
            ))
        return snapshot

    def snapshot(
            self, ergebnis: KraftErgebnis, *, koerper_id: str,
            generation: int, sequenz: int, zeit_s: float, kraftpose: Pose,
            quellen: tuple[Quellbezug, ...],
            erwartet: tuple[Quellbezug, ...] | None,
            masse_kg: float, g_m_s2: float,
            solverbewertung: SolverBewertung | None = None,
    ) -> KraefteAnzeigeSnapshot:
        _identitaet(koerper_id, generation, sequenz)
        zeit_s = float(zeit_s)
        if not math.isfinite(zeit_s):
            raise ValueError("Snapshotzeit muss endlich sein")
        if not isinstance(kraftpose, Pose):
            raise TypeError("Snapshot braucht die ausgewertete Kraftpose")
        if not isinstance(ergebnis, KraftErgebnis):
            raise TypeError("Adapter erwartet einen expliziten KraftErgebnis-Vertrag")
        masse_kg, g_m_s2 = float(masse_kg), float(g_m_s2)
        if any(not math.isfinite(w) or w <= 0 for w in (masse_kg, g_m_s2)):
            raise ValueError("Masse und g muessen endlich positiv sein")
        quellen = tuple(quellen)
        if len(quellen) != len(ergebnis.beitraege):
            raise ValueError("Jeder gelieferte Beitrag braucht einen Quellbezug")
        ids = tuple(q.quell_id for q in quellen)
        if len(set(ids)) != len(ids):
            raise ValueError("Quellinstanz-IDs sind nicht eindeutig")
        if erwartet is not None:
            erwartet = tuple(erwartet)
            erwartete_ids = {q.quell_id: q for q in erwartet}
            if len(erwartete_ids) != len(erwartet):
                raise ValueError("Erwartete Quell-IDs sind nicht eindeutig")
            gewichtserwartungen = tuple(
                q for q in erwartet if q.name == "schwerkraft")
            if (len(gewichtserwartungen) != 1
                    or gewichtserwartungen[0].status == Datenstatus.DEAKTIVIERT):
                raise ValueError("Bekannter Quellenumfang muss Gewicht einmal enthalten")
            for quelle in quellen:
                erwartung = erwartete_ids.get(quelle.quell_id)
                if erwartung is None or erwartung.name != quelle.name:
                    raise ValueError("Gelieferte Quelle passt nicht zum Quellenumfang")
                if erwartung.status == Datenstatus.DEAKTIVIERT:
                    raise ValueError("Deaktivierte Quelle wurde fachlich geliefert")
        punkt = kraftpose.translation_m
        frame = kraftpose.ziel_frame
        if frame != ergebnis.gesamt_wrench.frame:
            raise ValueError("Kraftpose und KraftErgebnis liegen in anderen Frames")
        beitraege = []
        for quelle, beitrag in zip(quellen, ergebnis.beitraege):
            if quelle.name != beitrag.name or beitrag.wrench.frame != frame:
                raise ValueError("Quellname oder Frame widerspricht dem Ergebnis")
            if quelle.status == Datenstatus.DEAKTIVIERT:
                raise ValueError("Ein gelieferter Beitrag ist nicht deaktiviert")
            wrench = (beitrag.wrench if beitrag.wrench.bezugspunkt_m == tuple(punkt)
                      else beitrag.wrench.auf_bezugspunkt(punkt))
            status = ((Datenstatus.NULL if _null(wrench) else Datenstatus.GUELTIG)
                      if quelle.status in GUELTIGE_STATUS else quelle.status)
            definition = beitragsdefinition(quelle.name)
            beitraege.append(BeitragsAnzeige(
                (koerper_id, quelle.quell_id), quelle.name, definition.gruppe,
                wrench, status, "gelieferter Einzelbeitrag", (),
                quelle.originalangriff_m))
        if erwartet is not None:
            for quelle in erwartet:
                if quelle.quell_id not in ids:
                    status = (Datenstatus.FEHLEND
                              if quelle.status in GUELTIGE_STATUS else quelle.status)
                    beitraege.append(BeitragsAnzeige(
                        (koerper_id, quelle.quell_id), quelle.name,
                        beitragsdefinition(quelle.name).gruppe, None, status,
                        "erwartete Quelle", (), quelle.originalangriff_m))
        rechenbilanz = ergebnis.gesamt_wrench.auf_bezugspunkt(punkt)
        if not ergebnis.schwerkraft_beruecksichtigt:
            if any(q.name == "schwerkraft" for q in quellen):
                raise ValueError("Gewichtsmerkmal widerspricht den Quellbeitraegen")
            gewicht_id = (
                koerper_id,
                gewichtserwartungen[0].quell_id if erwartet is not None
                else "adapter:schwerkraft")
            if gewicht_id in {(koerper_id, q.quell_id) for q in quellen}:
                raise ValueError("Reservierte Adapter-ID wurde bereits vergeben")
            gewicht = Wrench(frame, punkt, (0, 0, -masse_kg * g_m_s2), (0, 0, 0))
            beitraege = [b for b in beitraege if b.instanz_id != gewicht_id]
            beitraege.append(BeitragsAnzeige(
                gewicht_id, "schwerkraft", "gewicht_auftrieb", gewicht,
                Datenstatus.GUELTIG, "Adapterergaenzung Gewicht", ()))
            rechenbilanz = aggregiere_kraftbeitraege((
                Kraftbeitrag("rechenbilanz", rechenbilanz),
                Kraftbeitrag("adapter:schwerkraft", gewicht)), punkt, frame)[0]
        elif not any(q.name == "schwerkraft" for q in quellen) and erwartet is None:
            beitraege.append(BeitragsAnzeige(
                (koerper_id, "solver:schwerkraft"), "schwerkraft",
                "gewicht_auftrieb", None, Datenstatus.FEHLEND,
                "erwartete Quelle", ()))
        fehlende = tuple(b.instanz_id for b in beitraege
                         if b.status not in GUELTIGE_STATUS
                         and b.status != Datenstatus.DEAKTIVIERT)
        vollstaendigkeit = (
            "ungeklaert" if erwartet is None
            else "teilsumme" if fehlende else "vollstaendig")
        gueltige = tuple(b for b in beitraege if b.status in GUELTIGE_STATUS)
        bilanz_wrench = (
            _summe(gueltige, punkt, frame)
            if gueltige or vollstaendigkeit == "vollstaendig" else None)
        bilanz = BeitragsAnzeige(
            (koerper_id, "summe:gesamt"),
            ("Gesamtbilanz" if vollstaendigkeit == "vollstaendig"
             else "Verfuegbare Teilsumme - unvollstaendig"
             if vollstaendigkeit == "teilsumme" else "Vollstaendigkeit ungeklaert"),
            "gesamtbilanz", bilanz_wrench,
            Datenstatus.FEHLEND if bilanz_wrench is None
            else Datenstatus.NULL if _null(bilanz_wrench) else Datenstatus.GUELTIG,
            "Gesamtsumme", tuple(b.instanz_id for b in gueltige))
        gruppen = []
        for gruppe in dict.fromkeys(b.gruppe for b in beitraege):
            kinder = tuple(b for b in gueltige if b.gruppe == gruppe)
            luecke = any(
                b.gruppe == gruppe and b.instanz_id in fehlende for b in beitraege)
            wrench = (_summe(kinder, punkt, frame) if kinder or not luecke else None)
            gruppen.append(BeitragsAnzeige(
                (koerper_id, "summe:" + gruppe),
                gruppe + (" - unvollstaendige Teilsumme" if luecke else ""),
                gruppe, wrench,
                Datenstatus.FEHLEND if wrench is None
                else Datenstatus.NULL if _null(wrench) else Datenstatus.GUELTIG,
                "Gruppensumme", tuple(b.instanz_id for b in kinder)))
        alle_ids = [b.instanz_id for b in (*beitraege, *gruppen, bilanz)]
        if len(set(alle_ids)) != len(alle_ids):
            raise ValueError("Quellinstanz-ID kollidiert mit einer Summen-ID")
        if solverbewertung is not None:
            if ((solverbewertung.koerper_id, solverbewertung.generation,
                 solverbewertung.sequenz) != (koerper_id, generation, sequenz)
                    or erwartet is None
                    or set(solverbewertung.quell_ids) != {
                        q.quell_id for q in erwartet
                        if q.status != Datenstatus.DEAKTIVIERT}):
                raise ValueError("Solverbewertung gehoert nicht zu diesem Snapshot")
        return KraefteAnzeigeSnapshot(
            koerper_id, generation, sequenz, zeit_s, kraftpose,
            tuple(beitraege), tuple(gruppen), bilanz, rechenbilanz,
            vollstaendigkeit, fehlende, solverbewertung)


@dataclass(frozen=True, slots=True)
class WirkungslinienAnzeige:
    anker_m: Vektor3
    restmoment_Nm: Vektor3
    aequivalent: bool
    grund: str | None


def wirkungslinie(
        wrench: Wrench, *, f_char_N: float,
        koerperausdehnung_m: float | None,
) -> WirkungslinienAnzeige:
    f_char_N = float(f_char_N)
    if not math.isfinite(f_char_N) or f_char_N < 1:
        raise ValueError("Charakteristische Kraft muss endlich und mindestens 1 N sein")
    grund = None
    kraft = np.asarray(wrench.kraft_N)
    # hypot vermeidet einen Ueberlauf beim Quadrieren endlicher Komponenten.
    betrag = math.hypot(*wrench.kraft_N)
    epsilon = max(1e-9, 1e-12 * f_char_N)
    if not math.isfinite(betrag):
        grund = "Wirkungslinie nicht endlich berechenbar"
    elif betrag <= epsilon:
        grund = "Kraft unter Wirkungsliniengrenze"
    elif koerperausdehnung_m is None:
        grund = "Koerpergeometrie fehlt"
    else:
        ausdehnung = float(koerperausdehnung_m)
        if not math.isfinite(ausdehnung) or ausdehnung < 0:
            raise ValueError("Koerperausdehnung muss endlich und nichtnegativ sein")
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            richtung = kraft / betrag
            arm = np.cross(richtung, np.asarray(wrench.moment_Nm) / betrag)
            anker = np.asarray(wrench.bezugspunkt_m) + arm
            rest = richtung * np.dot(richtung, np.asarray(wrench.moment_Nm))
        if not np.isfinite(anker).all() or not np.isfinite(rest).all():
            grund = "Wirkungslinie nicht endlich berechenbar"
        elif math.hypot(*arm) > 10 * max(ausdehnung, 0.05):
            grund = "Wirkungslinienanker weiter als zehn Koerperausdehnungen"
        else:
            return WirkungslinienAnzeige(
                tuple(float(w) for w in anker), tuple(float(w) for w in rest),
                True, None)
    return WirkungslinienAnzeige(
        wrench.bezugspunkt_m, wrench.moment_Nm, False, grund)


def wrench_transformieren(wrench: Wrench, pose: Pose) -> Wrench:
    if wrench.frame != pose.quell_frame:
        raise ValueError("Wrench passt nicht zum Quellframe der Transformation")
    return Wrench(
        pose.ziel_frame, pose.punkt_transformieren(wrench.bezugspunkt_m),
        pose.vektor_transformieren(wrench.kraft_N),
        pose.vektor_transformieren(wrench.moment_Nm))


def anzeige_wrench(snapshot: KraefteAnzeigeSnapshot, beitrag: BeitragsAnzeige,
                   *, weltursprung=False, koerperframe=False) -> Wrench | None:
    """Wechselt nur Bezug/Koordinaten vorhandener Daten, niemals die Kraftpose."""
    if beitrag.wrench is None:
        return None
    # Der Szenenursprung liegt bei statischer XY-Verschiebung im Solverframe
    # bei -Versatz. Der Originalsnapshot bleibt im tatsaechlichen Solverframe.
    punkt = (tuple(-w for w in snapshot.szenenversatz_m) if weltursprung
             else snapshot.kraftpose.translation_m)
    wrench = (beitrag.wrench if beitrag.wrench.bezugspunkt_m == punkt
              else beitrag.wrench.auf_bezugspunkt(punkt))
    return (wrench_transformieren(wrench, snapshot.kraftpose.invers())
            if koerperframe else wrench)
