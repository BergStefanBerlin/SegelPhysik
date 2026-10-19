# -*- coding: utf-8 -*-
"""QTreeWidget-Ansicht des Komponentenbaums (Spec GUI v1, G2).

Layout je Zeile (Nutzerfestlegung 13.10.):
  links   Baumstruktur: Fuehrungslinien, +/- zum Auf-/Zuklappen (Gruppen "+")
  mitte   Icon + Name
  rechts  Checkbox fuer Hauptobjekte, Gruppen und Blaetter (Spalte 1);
          gemischte Blatt-Auswahl wird als Teilaktivitaet dargestellt.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPen, QBrush, QPolygon
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QHeaderView, QMenu,
    QMessageBox, QStyledItemDelegate, QTreeWidget, QTreeWidgetItem,
    QDialog, QDialogButtonBox, QWidget,
)

from .baum import (
    ART_WELT, ART_SUMMEN, ART_GRUPPE, ART_BLATT,
    ICON_GLOBUS, ICON_YACHT, ICON_KEGEL, ICON_WUERFEL,
)

SPALTE_NAME = 0
SPALTE_CHECK = 1

_FARBE = {"globus": "#3a7d44", "yacht": "#8a5a2b",
          "kegel": "#ff6a00", "wuerfel": "#5a7d9a"}


def _icon(art):
    pm = QPixmap(16, 16)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    farbe = _FARBE.get(art, _FARBE["wuerfel"])
    p.setPen(QPen(QColor(farbe), 1))
    p.setBrush(QBrush(QColor(farbe)))
    if art == ICON_KEGEL:
        p.drawPolygon(QPolygon([QPoint(8, 2), QPoint(14, 14), QPoint(2, 14)]))
    elif art == ICON_YACHT:
        p.drawPolygon(QPolygon([QPoint(2, 11), QPoint(14, 11), QPoint(11, 14), QPoint(5, 14)]))
        p.drawLine(9, 2, 9, 10)
        p.drawPolygon(QPolygon([QPoint(10, 3), QPoint(13, 10), QPoint(10, 10)]))
    elif art == ICON_GLOBUS:
        p.drawEllipse(2, 2, 12, 12)
    else:
        p.drawRect(3, 3, 10, 10)
    p.end()
    return QIcon(pm)


class TeilaktivDelegate(QStyledItemDelegate):
    """Zeigt Teilaktivitaet mit einem grauen statt blauen Minus an."""

    def paint(self, painter, option, index):
        zustand = index.data(Qt.ItemDataRole.CheckStateRole)
        if zustand != Qt.CheckState.PartiallyChecked.value:
            super().paint(painter, option, index)
            return

        groesse = min(16, option.rect.height() - 4)
        links = option.rect.left() + 4
        oben = option.rect.center().y() - groesse // 2
        box = option.rect.__class__(links, oben, groesse, groesse)
        painter.save()
        painter.setPen(QPen(QColor("#777777"), 1))
        painter.setBrush(QColor("#eeeeee"))
        painter.drawRoundedRect(box, 2, 2)
        mitte_y = box.center().y()
        painter.setPen(QPen(QColor("#777777"), 2))
        painter.drawLine(box.left() + 4, mitte_y, box.right() - 4, mitte_y)
        painter.restore()


class BaumWidget(QTreeWidget):
    laufzeit_aenderung = Signal(str)

    def __init__(self, eltern=None):
        super().__init__(eltern)
        self.setColumnCount(2)
        self.setHeaderLabels(["Komponente", ""])
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(SPALTE_NAME, QHeaderView.Stretch)
        self.header().setSectionResizeMode(
            SPALTE_CHECK, QHeaderView.ResizeToContents)
        self.setItemDelegateForColumn(
            SPALTE_CHECK, TeilaktivDelegate(self))
        self.setRootIsDecorated(True)
        self.setExpandsOnDoubleClick(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._welt = None
        self._in_update = False
        self._nur_aktives_bedienbar = False
        self.itemChanged.connect(self._geaendert)
        self.itemExpanded.connect(self._ausklappen_begrenzen)
        self.customContextMenuRequested.connect(self._kontextmenue)

    def lade(self, welt_knoten):
        expansion = self._expansion_speichern() if self._welt is not None else None
        self._in_update = True
        try:
            self.clear()
            self._welt = welt_knoten
            self._einfuegen(welt_knoten, None)
            if expansion is None:
                root = self.topLevelItem(0)
                if root is not None:
                    root.setExpanded(True)
            else:
                self._expansion_wiederherstellen(expansion)
        finally:
            self._in_update = False

    def _expansion_speichern(self):
        expansion = {}
        stack = [self.topLevelItem(i)
                 for i in range(self.topLevelItemCount())]
        while stack:
            item = stack.pop()
            knoten = item.data(SPALTE_NAME, Qt.ItemDataRole.UserRole)
            if knoten is not None:
                expansion[id(knoten)] = item.isExpanded()
            stack.extend(item.child(i) for i in range(item.childCount()))
        return expansion

    def _expansion_wiederherstellen(self, expansion):
        stack = [self.topLevelItem(i)
                 for i in range(self.topLevelItemCount())]
        while stack:
            item = stack.pop()
            knoten = item.data(SPALTE_NAME, Qt.ItemDataRole.UserRole)
            if knoten is not None and id(knoten) in expansion:
                item.setExpanded(expansion[id(knoten)])
            stack.extend(item.child(i) for i in range(item.childCount()))

    def nur_aktives_bedienbar_setzen(self, aktiv):
        self._nur_aktives_bedienbar = bool(aktiv)
        if self._welt is not None:
            self.lade(self._welt)

    def _einfuegen(self, knoten, eltern_item):
        item = QTreeWidgetItem([knoten.label, ""])
        item.setData(SPALTE_NAME, Qt.UserRole, knoten)
        item.setIcon(SPALTE_NAME, _icon(knoten.icon_art))
        if knoten.art in (ART_SUMMEN, ART_GRUPPE, ART_BLATT):
            if knoten.grau:
                zustand = Qt.PartiallyChecked
            elif knoten.art == ART_SUMMEN:
                zustand = Qt.Checked if knoten.sichtbar else Qt.Unchecked
            else:
                zustand = Qt.Checked if knoten.aktiv else Qt.Unchecked
            item.setCheckState(SPALTE_CHECK, zustand)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if knoten.sichtbar:
                item.setBackground(SPALTE_NAME, QColor("#e8f0fe"))
            if (self._nur_aktives_bedienbar and knoten.art in
                    (ART_GRUPPE, ART_BLATT) and not self._hat_aktive_blaetter(knoten)):
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        else:
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
        if eltern_item is None:
            self.addTopLevelItem(item)
        else:
            eltern_item.addChild(item)
        for label, wert in knoten.eigenschaften:
            zeile = QTreeWidgetItem(["%s: %s" % (label, wert), ""])
            zeile.setData(SPALTE_NAME, Qt.ItemDataRole.UserRole,
                          (knoten, label))
            zeile.setFlags(zeile.flags() & ~Qt.ItemIsUserCheckable)
            zeile.setForeground(SPALTE_NAME, QColor("#707070"))
            item.addChild(zeile)
        for kind in knoten.kinder:
            self._einfuegen(kind, item)
        return item

    @staticmethod
    def _hat_aktive_blaetter(knoten):
        return any(n.art == ART_BLATT and n.aktiv for n in knoten.iteriere())

    def _ausklappen_begrenzen(self, item):
        knoten = item.data(SPALTE_NAME, Qt.ItemDataRole.UserRole)
        if isinstance(knoten, tuple) or knoten is None:
            item.setExpanded(False)
            return
        if knoten.art == ART_WELT:
            return
        haupt = knoten
        while haupt is not None and haupt.art != ART_SUMMEN:
            haupt = haupt.eltern
        if haupt is None or not haupt.sichtbar:
            item.setExpanded(False)

    def _hauptkoerperwechsel_zuklappen(self):
        self.collapseAll()
        welt = self.topLevelItem(0)
        if welt is not None:
            welt.setExpanded(True)

    def _kontextmenue(self, position):
        zeile = self.itemAt(position)
        if zeile is None or not isinstance(
                zeile.data(SPALTE_NAME, Qt.ItemDataRole.UserRole), tuple):
            return
        knoten, eigenschaft = zeile.data(
            SPALTE_NAME, Qt.ItemDataRole.UserRole)
        menue = QMenu(self)
        bearbeiten = menue.addAction("%s ändern …" % eigenschaft)
        if menue.exec(self.viewport().mapToGlobal(position)) == bearbeiten:
            self._eigenschaft_bearbeiten(knoten, eigenschaft)

    def _eigenschaft_bearbeiten(self, knoten, eigenschaft):
        if (knoten.eintrag is None
                or getattr(self._welt, "konfiguration", None) is None):
            return
        index = next((i for i, (name, _) in enumerate(knoten.eigenschaften)
                      if name == eigenschaft), None)
        if index is None:
            return
        wert = knoten.eigenschaften[index][1]
        if eigenschaft == "Material":
            materialien = self._materialnamen_laden()
            if not materialien:
                QMessageBox.warning(
                    self, "Materialien", "Keine Materialien gefunden.")
                return
            eingabe = QComboBox()
            eingabe.addItems(materialien)
            eingabe.setCurrentText(str(wert))
            titel = "Material ändern"
            formular = QFormLayout()
            formular.addRow("Material:", eingabe)
        elif eigenschaft in (
                "Dichte", "Wanddicke", "Masse",
                "Position x", "Position y", "Position z"):
            eingabe = QDoubleSpinBox()
            eingabe.setDecimals(6)
            eingabe.setMinimum(
                -1_000_000_000 if eigenschaft.startswith("Position")
                else 0.000001)
            eingabe.setMaximum(1_000_000_000)
            eingabe.setValue(self._zahlwert(eigenschaft, wert))
            eingabe.setSuffix({
                "Dichte": " kg/m³", "Wanddicke": " mm", "Masse": " kg"
            }.get(eigenschaft, " m"))
            titel = "%s ändern" % eigenschaft
            formular = QFormLayout()
            formular.addRow("%s:" % eigenschaft, eingabe)
        else:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(titel)
        formular.addRow(self._dialog_buttons(dialog))
        dialog.setLayout(formular)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self._eigenschaft_setzen(
                knoten, eigenschaft,
                eingabe.currentText() if eigenschaft == "Material"
                else eingabe.value())
        except ValueError as fehler:
            QMessageBox.warning(self, "Eigenschaft ändern", str(fehler))

    def _eigenschaft_setzen(self, knoten, eigenschaft, wert):
        eintrag = knoten.eintrag
        if eintrag is None:
            raise ValueError("Knoten hat keinen Konfigurationseintrag.")
        index = next((i for i, (name, _) in enumerate(knoten.eigenschaften)
                      if name == eigenschaft), None)
        if index is None:
            raise ValueError("Eigenschaft nicht im Baum gefunden: %s" % eigenschaft)

        if knoten.id == "segler" and eigenschaft in (
                "Masse", "Position x", "Position y", "Position z"):
            from ..core.segler_einstellungen import seglerwerte_pruefen

            werte = {
                "masse_kg": eintrag["masse_kg"],
                "position_rumpf_m": list(eintrag["position_rumpf_m"]),
            }
            if eigenschaft == "Masse":
                werte["masse_kg"] = wert
            else:
                werte["position_rumpf_m"]["xyz".index(eigenschaft[-1])] = wert
            werte = seglerwerte_pruefen(werte)
            haupt = knoten
            while haupt.eltern is not None and haupt.art != ART_SUMMEN:
                haupt = haupt.eltern
            self._welt.konfiguration.segler_einstellungen.setzen(
                haupt.name, werte)
            eintrag.update(werte)
            knoten.eigenschaften[index] = (
                eigenschaft, "%g %s" % (
                    float(wert), "kg" if eigenschaft == "Masse" else "m"))
            self.lade(self._welt)
            self.laufzeit_aenderung.emit("eigenschaft")
            return

        if eigenschaft == "Material":
            materialien = self._materialnamen_laden()
            if wert not in materialien:
                raise ValueError("Unbekanntes Material: %r" % (wert,))
            eintrag["material"] = wert
            anzeige = str(wert)
        elif eigenschaft == "Dichte":
            dichte = float(wert)
            if dichte <= 0:
                raise ValueError("Die Dichte muss groesser als 0 sein.")
            eintrag["dichte_kg_pro_m3"] = dichte
            anzeige = self._zahlwert_anzeigen(eigenschaft, dichte)
        elif eigenschaft == "Wanddicke":
            dicke_m = float(wert) / 1000.0
            if dicke_m <= 0:
                raise ValueError("Die Wanddicke muss groesser als 0 sein.")
            eintrag["wanddicke_m"] = dicke_m
            anzeige = self._zahlwert_anzeigen(eigenschaft, float(wert))
        else:
            raise ValueError("Nicht editierbare Eigenschaft: %s" % eigenschaft)

        if getattr(self._welt, "manifest_baum", False):
            haupt = knoten
            while haupt.eltern is not None and haupt.art != ART_SUMMEN:
                haupt = haupt.eltern
            feld = {
                "Material": "material",
                "Dichte": "dichte_kg_pro_m3",
                "Wanddicke": "wanddicke_m",
            }[eigenschaft]
            alle = getattr(
                self._welt.konfiguration, "paket_ueberschreibungen", None)
            if alle is None:
                alle = {}
                self._welt.konfiguration.paket_ueberschreibungen = alle
            alle.setdefault(haupt.name, {}).setdefault(knoten.id, {})[
                feld] = (
                    float(wert) / 1000.0 if eigenschaft == "Wanddicke"
                    else wert)

        knoten.eigenschaften[index] = (eigenschaft, anzeige)
        self.lade(self._welt)
        self.laufzeit_aenderung.emit("eigenschaft")

    @staticmethod
    def _dialog_buttons(dialog):
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        return buttons

    @staticmethod
    def _zahlwert(eigenschaft, text):
        return float(str(text).split()[0])

    @staticmethod
    def _zahlwert_anzeigen(eigenschaft, zahl):
        if eigenschaft == "Dichte":
            return "%g kg/m3" % zahl
        return "%g mm" % zahl

    def _materialnamen_laden(self):
        konfiguration = getattr(self._welt, "konfiguration", None)
        if konfiguration is None:
            return []
        return sorted(konfiguration.materialien_blocks)

    def _geaendert(self, item, spalte):
        if self._in_update or spalte != SPALTE_CHECK:
            return
        knoten = item.data(SPALTE_NAME, Qt.UserRole)
        if knoten is None:
            return
        self._in_update = True
        try:
            if knoten.art == ART_SUMMEN:
                if item.checkState(SPALTE_CHECK) != Qt.Unchecked:
                    vorher_aktiv = next(
                        (haupt for haupt in self._welt.kinder
                         if haupt.art == ART_SUMMEN and haupt.sichtbar),
                        None)
                    if vorher_aktiv is not knoten:
                        self._hauptkoerperwechsel_zuklappen()
                    from .baum import sichtbarkeit_setzen
                    sichtbarkeit_setzen(self._welt, knoten.name)
                else:
                    item.setCheckState(SPALTE_CHECK, Qt.Checked)
            elif knoten.art == ART_GRUPPE:
                from .baum import gruppe_setzen
                gruppe_setzen(self._welt, knoten,
                              item.checkState(SPALTE_CHECK) != Qt.Unchecked)
            elif knoten.art == ART_BLATT:
                from .baum import blatt_setzen
                blatt_setzen(self._welt, knoten,
                             item.checkState(SPALTE_CHECK) == Qt.Checked)
        finally:
            self._in_update = False
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._baum_zustand_geaendert)

    def _baum_zustand_geaendert(self):
        self.lade(self._welt)
        self.laufzeit_aenderung.emit("auswahl")
