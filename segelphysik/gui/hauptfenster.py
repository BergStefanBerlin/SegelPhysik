# -*- coding: utf-8 -*-
"""Hauptfenster der SegelPhysik-GUI (Spec GUI v1, Stand G2)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QDockWidget, QTextEdit, QLabel, QCheckBox, QTreeWidget, QTreeWidgetItem,
)

from .baum_widget import BaumWidget


_aktives_fenster = None


class HauptFenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SegelPhysik")
        self.resize(1280, 800)
        self._baue_menues()
        self._baue_steuerzeile()
        self._baue_docks()

    def _baue_menues(self):
        m_datei = self.menuBar().addMenu("&Datei")
        m_datei.addAction("Konfiguration laden …")
        m_datei.addAction("Konfiguration speichern …")
        m_datei.addSeparator()
        m_datei.addAction("Beenden", self.close)
        m_einst = self.menuBar().addMenu("&Einstellungen")
        self._act_protokoll = m_einst.addAction("Protokoll anzeigen",
                                                self._protokoll_umschalten)
        self._act_protokoll.setCheckable(True)
        self._act_protokoll.setChecked(True)
        m_einst.addAction("Solver-Parameter …")
        self._act_nur_aktives = m_einst.addAction(
            "Nur aktive Unterobjekte bedienbar")
        self._act_nur_aktives.setCheckable(True)
        self._act_nur_aktives.setChecked(False)
        self._act_nur_aktives.toggled.connect(
            self._nur_aktives_bedienbar_setzen)
        m_hilfe = self.menuBar().addMenu("&Hilfe")
        m_hilfe.addAction("Bedienübersicht")
        m_hilfe.addAction("Über SegelPhysik")

    def _baue_steuerzeile(self):
        zentrale = QWidget()
        layout = QVBoxLayout(zentrale)
        layout.setContentsMargins(0, 0, 0, 0)
        zeile = QWidget()
        h = QHBoxLayout(zeile)
        h.setContentsMargins(6, 4, 6, 4)
        self._btn_statisch = QPushButton("Statisch")
        self._btn_statisch.setCheckable(True)
        self._btn_statisch.setChecked(True)
        self._btn_echtzeit = QPushButton("Echtzeit")
        self._btn_echtzeit.setCheckable(True)
        self._modusgruppe = QButtonGroup(self)
        self._modusgruppe.setExclusive(True)
        self._modusgruppe.addButton(self._btn_statisch)
        self._modusgruppe.addButton(self._btn_echtzeit)
        self._btn_rueck = QPushButton("<")
        self._btn_halt = QPushButton("=")
        self._btn_vor = QPushButton(">")
        for b in (self._btn_rueck, self._btn_halt, self._btn_vor):
            b.setMaximumWidth(36)
        h.addWidget(self._btn_statisch)
        h.addWidget(self._btn_echtzeit)
        h.addSpacing(24)
        h.addWidget(self._btn_rueck)
        h.addWidget(self._btn_halt)
        h.addWidget(self._btn_vor)
        h.addStretch(1)
        layout.addWidget(zeile)
        self._modusgruppe.buttonClicked.connect(
            lambda _knopf: self._steuerzeile_umschalten(
                self._btn_statisch.isChecked()))
        self._steuerzeile_umschalten(self._btn_statisch.isChecked())

        # Ansichtsbereich unter der Steuerzeile
        self.label_3d = QLabel(
            "3D-Ansicht\n\n(QtInteractor wird hier eingebettet,\n"
            "sobald pyvistaqt installiert ist)")
        self.label_3d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_3d.setStyleSheet("color:#888; background:#fafafa;")
        layout.addWidget(self.label_3d, 1)
        self._ansicht_layout = layout
        self.setCentralWidget(zentrale)

    def ansicht_setzen(self, widget):
        idx = self._ansicht_layout.indexOf(self.label_3d)
        if idx >= 0:
            self._ansicht_layout.removeWidget(self.label_3d)
            self.label_3d.deleteLater()
            self._ansicht_layout.insertWidget(idx, widget, 1)

    def _steuerzeile_umschalten(self, statisch_aktiv):
        for b in (self._btn_rueck, self._btn_halt, self._btn_vor):
            b.setEnabled(not statisch_aktiv)
            b.setStyleSheet(
                "QPushButton { background-color: #0078d4; color: white; }"
                if not statisch_aktiv else "")

    def _baue_docks(self):
        self.baum = BaumWidget()
        self.baum.nur_aktives_bedienbar_setzen(
            self._act_nur_aktives.isChecked())
        dock_baum = QDockWidget("Komponentenbaum", self)
        dock_baum.setWidget(self.baum)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_baum)


        layer = QWidget()
        v = QVBoxLayout(layer)
        self._layer_checks = {}
        for name in ("Achsen", "Kräfte", "Momente"):
            cb = QCheckBox(name)
            cb.setChecked(name != "Momente")
            self._layer_checks[name] = cb
            v.addWidget(cb)
        v.addStretch(1)

        status = QTreeWidget()
        status.setHeaderLabels(["Eigenschaft", "Wert"])
        for schluessel, wert in (("z*", "-"), ("phi*", "-"), ("GM", "-"),
                                 ("Iterationen", "-"), ("Lösungstyp", "-")):
            QTreeWidgetItem(status, [schluessel, wert])
        status.setRootIsDecorated(False)

        dock_layer = QDockWidget("Layer", self)
        dock_layer.setWidget(layer)
        dock_status = QDockWidget("Solver-Status", self)
        dock_status.setWidget(status)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_layer)
        self.splitDockWidget(dock_layer, dock_status, Qt.Orientation.Horizontal)

        self.protokoll = QTextEdit()
        self.protokoll.setReadOnly(True)
        self.protokoll.setMaximumHeight(120)
        dock_log = QDockWidget("Protokoll", self)
        dock_log.setWidget(self.protokoll)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_log)
        self._dock_protokoll = dock_log

    def bruecke_setzen(self, bruecke):
        """Referenz auf die GrafikBruecke (G3-Kopplung der Docks)."""
        self._bruecke = bruecke
    def protokoll_schreiben(self, text):


        self.protokoll.append(text)

    def _protokoll_umschalten(self):
        self._dock_protokoll.setVisible(self._act_protokoll.isChecked())

    def baum_setzen(self, welt_knoten):
        self.baum.lade(welt_knoten)

    def _nur_aktives_bedienbar_setzen(self, aktiv):
        baum = getattr(self, "baum", None)
        if baum is not None:
            baum.nur_aktives_bedienbar_setzen(aktiv)
