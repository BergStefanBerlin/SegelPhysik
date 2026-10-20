"""Qt-Werteansicht auf dem gemeinsamen unveraenderlichen Anzeigesnapshot."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import math

from PySide6.QtCore import QAbstractItemModel, QByteArray, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDockWidget, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QTreeView, QVBoxLayout, QWidget,
)

from ..core.kraefte_anzeige import (
    AnzeigeId, BeitragsAnzeige, GUELTIGE_STATUS, KraefteAnzeigeSnapshot, anzeige_wrench,
)
from ..core.kraefte_darstellung import senkrechter_hebelarm, zahlenwert
from ..core.pfeilstil import GRUPPEN_TITEL, Stil, beitragsdefinition
from ..core.kraftmodell import Wrench

ID_ROLLE = Qt.ItemDataRole.UserRole
SNAPSHOT_ROLLE = ID_ROLLE + 1
BEITRAG_ROLLE = ID_ROLLE + 2
SPALTEN = (
    "Gruppe / Beitrag", "3D", "F_x", "F_y", "F_z", "|F|",
    "M_x um P", "M_y um P", "M_z um P", "|M um P|",
    "Punkt / Punktart", "Quelle", "Status",
)


def _punkttext(punkt, *, details=False):
    return "(" + "; ".join(
        zahlenwert(w, "m", details=details) for w in punkt) + ")"


def _summe(beitrag):
    return beitrag.herkunft in ("Gruppensumme", "Gesamtsumme")


def _titel(beitrag):
    if beitrag.herkunft == "Gesamtsumme":
        return "Summe: " + beitrag.name
    if beitrag.herkunft == "Gruppensumme":
        titel = GRUPPEN_TITEL.get(beitrag.gruppe, beitrag.gruppe)
        return "Summe: " + titel + beitrag.name[len(beitrag.gruppe):]
    return (beitragsdefinition(beitrag.name).titel
            + " [" + beitrag.instanz_id[1] + "]")


def _wert(beitrag, spalte, *, details=False):
    wrench = beitrag.wrench
    einheit = "N" if spalte < 6 else "N*m"
    if beitrag.status not in GUELTIGE_STATUS:
        return zahlenwert(None, einheit, status=beitrag.status)
    vektor = (None if wrench is None else wrench.kraft_N if spalte < 6
              else wrench.moment_Nm)
    wert = (None if vektor is None else math.hypot(*vektor)
            if spalte in (5, 9) else vektor[(spalte - 2) % 4])
    if spalte in (5, 9) and wert is not None and not math.isfinite(wert):
        return "Betrag nicht darstellbar"
    return zahlenwert(wert, einheit, status=beitrag.status, details=details)


@dataclass(eq=False)
class _Zeile:
    snapshot: KraefteAnzeigeSnapshot
    beitrag: BeitragsAnzeige | None = None
    eltern: _Zeile | None = None
    zeile: int = 0
    kinder: list[_Zeile] = field(default_factory=list)

    def anhaengen(self, beitrag):
        kind = _Zeile(self.snapshot, beitrag, self, len(self.kinder))
        self.kinder.append(kind)
        return kind


class KraefteWerteModell(QAbstractItemModel):
    sichtbarkeit_geaendert = Signal(object, bool)

    def __init__(self, eltern=None):
        super().__init__(eltern)
        self._wurzel: list[_Zeile] = []
        self._ids: dict[AnzeigeId, _Zeile] = {}
        self._sichtbar: dict[AnzeigeId, bool] = {}
        self._struktur = ()
        self._koerperframe = False
        self._weltursprung = False
        self._stil = Stil()

    def stil_setzen(self, stil):
        self._stil = stil
        for zeile in self._ids.values():
            index = self.createIndex(zeile.zeile, 0, zeile)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DecorationRole])

    def ansicht_setzen(self, *, koerperframe=False, weltursprung=False):
        self._koerperframe, self._weltursprung = bool(koerperframe), bool(weltursprung)
        for zeile in self._ids.values():
            self.dataChanged.emit(
                self.createIndex(zeile.zeile, 0, zeile),
                self.createIndex(zeile.zeile, len(SPALTEN) - 1, zeile))
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 2, 9)

    def sichtbarkeiten_setzen(self, sichtbar):
        if any(not isinstance(v, bool) for v in sichtbar.values()):
            raise TypeError("Sichtbarkeiten muessen Wahrheitswerte sein")
        self._sichtbar.update(sichtbar)
        for id_ in self._ids:
            index = self.index_fuer_id(id_, 1)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])

    def anzeigebeitrag(self, snapshot, beitrag):
        angriff = beitrag.originalangriff_m
        if angriff is not None and self._koerperframe:
            angriff = tuple(snapshot.kraftpose.invers().punkt_transformieren(angriff))
        elif angriff is not None:
            angriff = tuple(a + v for a, v in zip(angriff, snapshot.szenenversatz_m))
        wrench = anzeige_wrench(
            snapshot, beitrag, weltursprung=self._weltursprung,
            koerperframe=self._koerperframe)
        if wrench is not None and not self._koerperframe and any(snapshot.szenenversatz_m):
            wrench = Wrench(
                wrench.frame, tuple(p + v for p, v in zip(
                    wrench.bezugspunkt_m, snapshot.szenenversatz_m)),
                wrench.kraft_N, wrench.moment_Nm)
        return replace(beitrag, wrench=wrench, originalangriff_m=angriff)

    def snapshots_setzen(self, snapshots):
        snapshots = tuple(snapshots)
        if not all(isinstance(s, KraefteAnzeigeSnapshot) for s in snapshots):
            raise TypeError("Wertemodell erwartet Anzeigesnapshots")
        if len({s.koerper_id for s in snapshots}) != len(snapshots):
            raise ValueError("Pro Koerper ist genau ein Snapshot erlaubt")
        struktur = tuple((
            s.koerper_id, s.generation,
            tuple((b.instanz_id, b.gruppe) for b in s.gruppen),
            tuple((b.instanz_id, b.gruppe) for b in s.beitraege),
            s.bilanz.instanz_id) for s in snapshots)
        if struktur == self._struktur:
            for koerper, snapshot in zip(self._wurzel, snapshots):
                koerper.snapshot = snapshot
                beitraege = {b.instanz_id: b for b in (
                    *snapshot.beitraege, *snapshot.gruppen, snapshot.bilanz)}
                for beitrag in beitraege.values():
                    zeile = self._ids[beitrag.instanz_id]
                    zeile.snapshot = snapshot
                    zeile.beitrag = beitrag
                for eltern in (koerper, *koerper.kinder):
                    if eltern.kinder:
                        erstes, letztes = eltern.kinder[0], eltern.kinder[-1]
                        self.dataChanged.emit(
                            self.createIndex(erstes.zeile, 0, erstes),
                            self.createIndex(letztes.zeile, len(SPALTEN) - 1, letztes))
            if self._wurzel:
                self.dataChanged.emit(
                    self.index(0, 0), self.index(len(self._wurzel) - 1, len(SPALTEN) - 1))
            return
        wurzel, ids, sichtbar = [], {}, {}
        for snapshot in snapshots:
            koerper = _Zeile(snapshot, zeile=len(wurzel))
            wurzel.append(koerper)
            gruppen = {}
            for beitrag in snapshot.gruppen:
                gruppe = koerper.anhaengen(beitrag)
                gruppen[beitrag.gruppe] = gruppe
                ids[beitrag.instanz_id] = gruppe
            for beitrag in snapshot.beitraege:
                zeile = gruppen[beitrag.gruppe].anhaengen(beitrag)
                ids[beitrag.instanz_id] = zeile
            ids[snapshot.bilanz.instanz_id] = koerper.anhaengen(snapshot.bilanz)
        for instanz_id, zeile in ids.items():
            beitrag = zeile.beitrag
            standard = (beitrag.herkunft == "Gesamtsumme" if _summe(beitrag)
                        else beitragsdefinition(beitrag.name).sichtbar)
            sichtbar[instanz_id] = self._sichtbar.get(instanz_id, standard)
        self.beginResetModel()
        self._wurzel, self._ids, self._sichtbar = wurzel, ids, sichtbar
        self._struktur = struktur
        self.endResetModel()

    def _zeile(self, index):
        return (index.internalPointer()
                if index.isValid() and index.model() is self else None)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        eltern = self._zeile(parent)
        kinder = self._wurzel if eltern is None else eltern.kinder
        return self.createIndex(row, column, kinder[row])

    def parent(self, index):
        zeile = self._zeile(index)
        if zeile is None or zeile.eltern is None:
            return QModelIndex()
        eltern = zeile.eltern
        return self.createIndex(eltern.zeile, 0, eltern)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() and (parent.column() != 0 or parent.model() is not self):
            return 0
        zeile = self._zeile(parent)
        return len(self._wurzel if zeile is None else zeile.kinder)

    def columnCount(self, parent=QModelIndex()):
        return len(SPALTEN)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (role == Qt.ItemDataRole.DisplayRole
                and orientation == Qt.Orientation.Horizontal
                and 0 <= section < len(SPALTEN)):
            titel = SPALTEN[section]
            if 2 <= section <= 9 and section not in (5, 9):
                titel += " (Koerper)" if self._koerperframe else " (Welt)"
            return titel
        return None

    def flags(self, index):
        zeile = self._zeile(index)
        if zeile is None:
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 1 and zeile.beitrag is not None:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        zeile = self._zeile(index)
        if zeile is None:
            return None
        beitrag, snapshot = zeile.beitrag, zeile.snapshot
        if role == SNAPSHOT_ROLLE:
            return snapshot
        if role == BEITRAG_ROLLE:
            return beitrag
        if role == ID_ROLLE:
            return None if beitrag is None else beitrag.instanz_id
        if role == Qt.ItemDataRole.FontRole and (beitrag is None or _summe(beitrag)):
            schrift = QFont()
            schrift.setBold(True)
            return schrift
        if role == Qt.ItemDataRole.TextAlignmentRole and 2 <= index.column() <= 9:
            return (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter).value
        if role == Qt.ItemDataRole.CheckStateRole:
            if index.column() == 1 and beitrag is not None:
                return (Qt.CheckState.Checked.value
                        if self._sichtbar[beitrag.instanz_id]
                        else Qt.CheckState.Unchecked.value)
            return None
        if (role == Qt.ItemDataRole.DecorationRole and index.column() == 0
                and beitrag is not None):
            return QColor(self._stil.beitragsstil(beitrag, 1)["farbe"])
        if role == Qt.ItemDataRole.ToolTipRole:
            return (self.detailtext(beitrag.instanz_id) if beitrag is not None
                    else self.kopftext(snapshot))
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if beitrag is not None:
            beitrag = self.anzeigebeitrag(snapshot, beitrag)
        spalte = index.column()
        if beitrag is None:
            return {0: snapshot.koerper_id, 11: self.kopftext(snapshot),
                    12: snapshot.gleichgewichtsstatus}.get(spalte)
        if spalte == 0:
            return _titel(beitrag)
        if 2 <= spalte <= 9:
            return _wert(beitrag, spalte)
        if spalte == 10:
            punkt = (beitrag.originalangriff_m if beitrag.originalangriff_m is not None
                     else snapshot.kraftpose.translation_m if beitrag.wrench is None
                     else beitrag.wrench.bezugspunkt_m)
            return _punkttext(punkt) + " / " + beitrag.punktart
        if spalte == 11:
            return beitrag.herkunft + " / " + beitrag.name
        if spalte == 12:
            return beitrag.status.value
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        zeile = self._zeile(index)
        if (role != Qt.ItemDataRole.CheckStateRole or index.column() != 1
                or zeile is None or zeile.beitrag is None):
            return False
        zustand = value.value if isinstance(value, Qt.CheckState) else value
        if zustand not in (Qt.CheckState.Checked.value, Qt.CheckState.Unchecked.value):
            return False
        sichtbar = zustand == Qt.CheckState.Checked.value
        instanz_id = zeile.beitrag.instanz_id
        if self._sichtbar[instanz_id] != sichtbar:
            self._sichtbar[instanz_id] = sichtbar
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            self.sichtbarkeit_geaendert.emit(instanz_id, sichtbar)
        return True

    def index_fuer_id(self, instanz_id, spalte=0):
        zeile = self._ids.get(instanz_id)
        return (QModelIndex() if zeile is None or not 0 <= spalte < len(SPALTEN)
                else self.createIndex(zeile.zeile, spalte, zeile))

    def index_fuer_koerper(self, koerper_id):
        for zeile in self._wurzel:
            if zeile.snapshot.koerper_id == koerper_id:
                return self.createIndex(zeile.zeile, 0, zeile)
        return QModelIndex()

    def kopftext(self, snapshot):
        ursprung = tuple(-w for w in snapshot.szenenversatz_m)
        punkt = (snapshot.kraftpose.invers().punkt_transformieren(
            ursprung if self._weltursprung else snapshot.kraftpose.translation_m)
            if self._koerperframe else
            (0, 0, 0) if self._weltursprung else tuple(
                p + v for p, v in zip(
                    snapshot.kraftpose.translation_m, snapshot.szenenversatz_m)))
        return (
            f"{snapshot.koerper_id} | t = {zahlenwert(snapshot.zeit_s, 's')} | "
            f"Generation {snapshot.generation} / Snapshot #{snapshot.sequenz} | "
            f"Frame: {snapshot.kraftpose.quell_frame if self._koerperframe else snapshot.kraftpose.ziel_frame} | "
            f"Momentenbezug P = {_punkttext(punkt)} "
            f"({'Weltursprung' if self._weltursprung else 'Schwerpunkt'}) | "
            f"{snapshot.vollstaendigkeit} | {snapshot.gleichgewichtsstatus} | "
            f"Kraftpose zum Auswertungszeitpunkt; Koerperszene kann interpoliert sein. "
            f"Szenenversatz = {_punkttext(snapshot.szenenversatz_m)}"
            + "".join(" | " + h for h in snapshot.modellhinweise))

    def detailtext(self, instanz_id):
        zeile = self._ids[instanz_id]
        beitrag, snapshot = zeile.beitrag, zeile.snapshot
        beitrag = self.anzeigebeitrag(snapshot, beitrag)
        text = [
            _titel(beitrag), self.kopftext(snapshot),
            f"ID: {beitrag.instanz_id}",
            f"Quelle: {beitrag.name} / {beitrag.herkunft}",
            f"Status: {beitrag.status.value}",
        ]
        text.extend(f"{SPALTEN[s]}: {_wert(beitrag, s, details=True)}"
                    for s in range(2, 10))
        if beitrag.originalangriff_m is not None:
            text.extend((
                "Realer Angriff A = " + _punkttext(
                    beitrag.originalangriff_m, details=True),
                "M(P) = M(A) + (A - P) x F",
                "Ein direktes Quellenmoment M(A) kann zusaetzlich enthalten sein.",
            ))
            if beitrag.wrench is not None:
                import numpy as np
                w = beitrag.wrench
                arm = np.asarray(beitrag.originalangriff_m) - w.bezugspunkt_m
                hebelmoment = np.cross(arm, w.kraft_N)
                direkt = np.asarray(w.moment_Nm) - hebelmoment
                text.extend((
                    "Bezug P = " + _punkttext(w.bezugspunkt_m, details=True),
                    "Hebelarmmoment (A-P) x F = (" + "; ".join(
                        zahlenwert(v, "N*m", details=True) for v in hebelmoment) + ")",
                    "Direktes Quellenmoment M(A) = (" + "; ".join(
                        zahlenwert(v, "N*m", details=True) for v in direkt) + ")"))
                if math.hypot(*w.kraft_N) > 0:
                    a, b = senkrechter_hebelarm(
                        w.bezugspunkt_m, beitrag.originalangriff_m, w.kraft_N)
                    text.append("Senkrechter Hebelarm: " + zahlenwert(
                        math.dist(a, b), "m", details=True))
        else:
            text.append("Kein bestaetigter Originalangriff; P ist Momentenbezug.")
        if beitrag.quell_ids:
            text.append("Quellen: " + ", ".join(
                f"{key[0]} / {key[1]}" for key in beitrag.quell_ids))
        if _summe(beitrag):
            text.append(
                "Summe ist eine Ableitung, kein zusaetzlicher Bilanzbeitrag.")
        bewertung = snapshot.solverbewertung
        if bewertung is not None:
            text.append("Solver: " + bewertung.quelle + " / "
                        + ", ".join(bewertung.freiheitsgrade))
            for name, residuum, toleranz in bewertung.kriterien:
                text.append(f"{name}: Residuum {residuum:.17g}, "
                            f"Toleranz {toleranz:.17g}".replace(".", ","))
        text.append("Ausblenden aendert keine Physik. Werte sind schreibgeschuetzt.")
        return "\n".join(text)


class KraefteWerteFenster(QDockWidget):
    auswahl_geaendert = Signal(object)
    sichtbarkeit_geaendert = Signal(object, bool)
    neu_einpassen = Signal()
    ansicht_geaendert = Signal(str, bool)
    koerperumfang_geaendert = Signal(object)
    zuruecksetzen = Signal()

    def __init__(self, eltern=None):
        super().__init__("Kraefte und Momente", eltern)
        self.setObjectName("kraefte_werte")
        self.setFloating(True)
        self.modell = KraefteWerteModell(self)
        self.baum = QTreeView()
        self.baum.setModel(self.modell)
        self.baum.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.baum.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.baum.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.baum.setColumnWidth(0, 280)
        self.baum.setColumnWidth(1, 40)
        self.baum.header().setSectionsMovable(True)
        self.kopf = QLabel("Kein Anzeigesnapshot")
        self.kopf.setWordWrap(True)
        self.karten = tuple(QLabel() for _ in range(3))
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(230)
        inhalt = QWidget()
        layout = QVBoxLayout(inhalt)
        layout.addWidget(self.kopf)
        auswahl = QHBoxLayout()
        self.koerperwahl = QComboBox()
        self.koerperwahl.setToolTip(
            "Betrachteter Anzeigesnapshot; aendert keine physische Aktivierung")
        self.koerperwahl.currentIndexChanged.connect(self._umfang_aktualisieren)
        auswahl.addWidget(self.koerperwahl)
        self.optionen = {}
        for key, titel in (
                ("mehrkoerper", "Mehrkoerperanzeige"),
                ("koerperframe", "Koerperframe"),
                ("weltursprung", "Bezug Weltursprung"),
                ("komponenten", "Momentenkomponenten")):
            check = QCheckBox(titel)
            check.toggled.connect(
                lambda wert, key=key: self.ansicht_geaendert.emit(key, wert))
            auswahl.addWidget(check)
            self.optionen[key] = check
        layout.addLayout(auswahl)
        kartenlayout = QHBoxLayout()
        for karte in self.karten:
            karte.setWordWrap(True)
            karte.setTextFormat(Qt.TextFormat.PlainText)
            kartenlayout.addWidget(karte, 1)
        self.kopf.setTextFormat(Qt.TextFormat.PlainText)
        layout.addLayout(kartenlayout)
        layout.addWidget(self.baum, 1)
        layout.addWidget(self.details)
        self.legende = QLabel("Skalen werden beim ersten 3D-Datenstand initialisiert.")
        self.legende.setWordWrap(True)
        self.legende.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.legende)
        self.datenstatus = QLabel()
        self.datenstatus.setWordWrap(True)
        self.datenstatus.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.datenstatus)
        einpassen = QPushButton("Neu einpassen")
        einpassen.clicked.connect(self.neu_einpassen.emit)
        layout.addWidget(einpassen)
        reset = QPushButton("Anzeigestandard wiederherstellen")
        reset.clicked.connect(self.zuruecksetzen.emit)
        layout.addWidget(reset)
        self.setWidget(inhalt)
        self.resize(1100, 650)
        self._aktive_id: AnzeigeId | None = None
        self._in_update = False
        self._snapshots = ()
        self._koerper = ()
        self._mehrkoerper = False
        self._umfang = ()
        self.baum.selectionModel().currentChanged.connect(self._auswahl)
        self.modell.sichtbarkeit_geaendert.connect(self.sichtbarkeit_geaendert.emit)

    def ansicht_setzen(self, optionen):
        for key, check in self.optionen.items():
            blockiert = check.blockSignals(True)
            check.setChecked(optionen[key])
            check.blockSignals(blockiert)
        self.modell.ansicht_setzen(
            koerperframe=optionen["koerperframe"],
            weltursprung=optionen["weltursprung"])
        self._mehrkoerper = optionen["mehrkoerper"]
        self._umfang_aktualisieren()

    def _umfang_aktualisieren(self, *_):
        self.koerperwahl.setEnabled(not self._mehrkoerper)
        snapshots = (self._snapshots if self._mehrkoerper else tuple(
            s for s in self._snapshots if s.koerper_id == self.koerperwahl.currentData()))
        self._snapshots_anzeigen(snapshots)
        umfang = (tuple(self.koerperwahl.itemData(i)
                        for i in range(self.koerperwahl.count()))
                  if self._mehrkoerper else
                  (() if self.koerperwahl.currentData() is None
                   else (self.koerperwahl.currentData(),)))
        vorhanden = {s.koerper_id for s in snapshots}
        fehlende = tuple(name for name in umfang if name not in vorhanden)
        self.datenstatus.setText(
            "Nicht berechnet / keine gueltigen Kraftdaten: " + ", ".join(fehlende)
            if fehlende else "")
        if umfang != self._umfang:
            self._umfang = umfang
            self.koerperumfang_geaendert.emit(umfang)

    def legende_setzen(self, skalen, hinweise=()):
        zeilen = []
        for koerper, domaenen in skalen.items():
            for titel, einheit, abbildung in zip(
                    ("Kraft", "Momentenradius"), ("N", "N*m"), domaenen):
                punkte = "; ".join(
                    zahlenwert(wert, einheit) + " -> "
                    + format(grafik.groesse_px, ".4g").replace(".", ",") + " px"
                    for wert, grafik in abbildung.legende())
                zeilen.append(
                    f"{koerper}: {titel}, {abbildung.modus}, Referenz "
                    + zahlenwert(abbildung.referenz, einheit) + " | " + punkte)
        zeilen.extend(hinweise)
        self.legende.setText("\n".join(zeilen) or "Keine initialisierten 3D-Skalen")

    def layout_exportieren(self):
        dock = self.parent().dockWidgetArea(self).value
        return {
            "geometrie": bytes(self.saveGeometry().toHex()).decode("ascii"),
            "spalten": bytes(self.baum.header().saveState().toHex()).decode("ascii"),
            "frei": self.isFloating(), "dock": dock or 2,
            "sichtbar": not self.isHidden()}

    def layout_anwenden(self, layout):
        if not layout:
            return
        self.parent().addDockWidget(Qt.DockWidgetArea(layout["dock"]), self)
        self.setFloating(layout["frei"])
        if not self.restoreGeometry(QByteArray.fromHex(layout["geometrie"].encode("ascii"))):
            raise ValueError("Wertefenstergeometrie konnte nicht wiederhergestellt werden")
        if not self.baum.header().restoreState(
                QByteArray.fromHex(layout["spalten"].encode("ascii"))):
            raise ValueError("Wertespalten konnten nicht wiederhergestellt werden")
        self.position_erreichbar_machen()
        self.setVisible(layout["sichtbar"])

    def position_erreichbar_machen(self):
        if not self.isFloating():
            return
        bildschirme = QGuiApplication.screens()
        if not any(s.availableGeometry().contains(
                self.frameGeometry().center()) for s in bildschirme):
            bereich = QGuiApplication.primaryScreen().availableGeometry()
            self.resize(self.size().boundedTo(bereich.size()))
            self.move(bereich.topLeft())

    def koerper_setzen(self, koerper_ids):
        koerper = tuple(koerper_ids)
        if (any(not isinstance(k, str) or not k for k in koerper)
                or len(set(koerper)) != len(koerper)):
            raise ValueError("Anzeigekoerper brauchen eindeutige nichtleere IDs")
        if koerper == self._koerper:
            return
        self._koerper = koerper
        self._koerperwahl_aktualisieren()

    def _koerperwahl_aktualisieren(self):
        koerper = tuple(dict.fromkeys(
            (*self._koerper, *(s.koerper_id for s in self._snapshots))))
        # Auswahl bewahren, auch wenn die Reihenfolge der Workerantworten wechselt.
        alt = self.koerperwahl.currentData()
        if koerper != tuple(
                self.koerperwahl.itemData(i) for i in range(self.koerperwahl.count())):
            blockiert = self.koerperwahl.blockSignals(True)
            self.koerperwahl.clear()
            for name in koerper:
                self.koerperwahl.addItem(name, name)
            index = self.koerperwahl.findData(alt)
            self.koerperwahl.setCurrentIndex(max(0, index))
            self.koerperwahl.blockSignals(blockiert)
        self._umfang_aktualisieren()

    def snapshots_setzen(self, snapshots):
        self._snapshots = tuple(snapshots)
        self._koerperwahl_aktualisieren()

    def _snapshots_anzeigen(self, snapshots):
        alte_id = self._aktive_id
        alter_index = self.baum.currentIndex()
        alter_snapshot = alter_index.data(SNAPSHOT_ROLLE)
        offen = set()
        for index in self._indices():
            if self.baum.isExpanded(index):
                offen.add(index.data(ID_ROLLE) or index.data(SNAPSHOT_ROLLE).koerper_id)
        erster_stand = self.modell.rowCount() == 0
        self._in_update = True
        try:
            self.modell.snapshots_setzen(snapshots)
            neu = self.modell.index_fuer_id(alte_id)
            if (neu.isValid() and alter_snapshot is not None
                    and neu.data(SNAPSHOT_ROLLE).generation == alter_snapshot.generation):
                self.baum.setCurrentIndex(neu)
            else:
                koerper = (QModelIndex() if alter_snapshot is None else
                           self.modell.index_fuer_koerper(alter_snapshot.koerper_id))
                self.baum.setCurrentIndex(
                    koerper if koerper.isValid() else self.modell.index(0, 0))
            for index in self._indices():
                key = index.data(ID_ROLLE) or index.data(SNAPSHOT_ROLLE).koerper_id
                self.baum.setExpanded(index, erster_stand or key in offen)
        finally:
            self._in_update = False
        self._auswahl(self.baum.currentIndex(), alter_index)

    def _indices(self):
        def kinder(parent=QModelIndex()):
            for row in range(self.modell.rowCount(parent)):
                index = self.modell.index(row, 0, parent)
                yield index
                yield from kinder(index)
        return kinder()

    def auswaehlen(self, instanz_id: AnzeigeId | None):
        if instanz_id is None:
            snapshot = self.baum.currentIndex().data(SNAPSHOT_ROLLE)
            index = (self.modell.index(0, 0) if snapshot is None else
                     self.modell.index_fuer_koerper(snapshot.koerper_id))
        else:
            index = self.modell.index_fuer_id(instanz_id)
        if instanz_id is not None and not index.isValid():
            raise KeyError("Unbekannte Anzeige-ID: %r" % (instanz_id,))
        self._in_update = True
        try:
            self.baum.setCurrentIndex(index)
            if index.isValid():
                self.baum.scrollTo(index)
        finally:
            self._in_update = False
        self._anzeigen(index)

    def _auswahl(self, aktuell, vorher):
        if self._in_update:
            return
        alte_id = self._aktive_id
        self._anzeigen(aktuell)
        if self._aktive_id != alte_id:
            self.auswahl_geaendert.emit(self._aktive_id)

    def _anzeigen(self, index):
        self._aktive_id = index.data(ID_ROLLE)
        snapshot = index.data(SNAPSHOT_ROLLE)
        self.details.setPlainText(
            self.modell.detailtext(self._aktive_id)
            if self._aktive_id is not None else "Kein Beitrag ausgewaehlt")
        if snapshot is None:
            self.kopf.setText("Kein Anzeigesnapshot")
            for karte in self.karten:
                karte.clear()
            return
        self.kopf.setText(self.modell.kopftext(snapshot))
        bilanz = self.modell.anzeigebeitrag(snapshot, snapshot.bilanz)
        self.karten[0].setText(
            bilanz.name + "\n|Summe F|: " + _wert(bilanz, 5)
            + "\nF(x/y/z): " + " / ".join(_wert(bilanz, s) for s in (2, 3, 4)))
        self.karten[1].setText(
            "Moment um P\n|Summe M|: " + _wert(bilanz, 9)
            + "\nM(x/y/z): " + " / ".join(_wert(bilanz, s) for s in (6, 7, 8)))
        self.karten[2].setText(snapshot.vollstaendigkeit + "\n"
                               + snapshot.gleichgewichtsstatus)

    def oeffnen(self):
        self.position_erreichbar_machen()
        self.show()
        self.raise_()
        self.activateWindow()
