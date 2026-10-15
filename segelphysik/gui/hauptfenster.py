# -*- coding: utf-8 -*-
"""Hauptfenster der SegelPhysik-GUI (Spec GUI v1, Stand G2)."""
from __future__ import annotations

import math
import os
import time

import numpy as np
from PySide6.QtCore import Qt, QObject, QRunnable, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton,
    QDockWidget, QTextEdit, QLabel, QCheckBox, QTreeWidget, QTreeWidgetItem,
    QComboBox, QMessageBox, QDoubleSpinBox, QGridLayout,
)

from .baum_widget import BaumWidget
from ..core.overlays import (LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                             LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT)


_aktives_fenster = None
_ECHTZEIT_HYDROSTATIK_PFAD = "exakt_union"


class _EchtzeitAufgabeSignale(QObject):
    abgeschlossen = Signal(int, int, str, object, object, object, float)


class _EchtzeitAufgabe(QRunnable):
    def __init__(self, generation, sequenz, koerper_name, zustand,
                 kraftfunktion, koerper, physik, dt, anzahl_schritte,
                 signale, prozess_executor=None, fremdkraft=None):
        super().__init__()
        self.fremdkraft = fremdkraft
        self.generation = generation
        self.sequenz = sequenz
        self.koerper_name = koerper_name
        self.zustand = zustand
        self.kraftfunktion = kraftfunktion
        self.koerper = koerper
        self.physik = physik
        self.dt = dt
        self.anzahl_schritte = anzahl_schritte
        self.signale = signale
        self.prozess_executor = prozess_executor

    def run(self):
        if hasattr(self.kraftfunktion, "aktualisieren"):
            self.kraftfunktion.aktualisieren()
        if self.prozess_executor is not None:
            from concurrent.futures import CancelledError
            from concurrent.futures.process import BrokenProcessPool
            import pickle
            from ..core.echtzeit_prozess import schritte_berechnen

            startzeit = time.perf_counter()
            try:
                zustand, ergebnis, fehler, dauer = (
                    self.prozess_executor.submit(
                        schritte_berechnen, self.zustand,
                        self.anzahl_schritte, self.fremdkraft).result())
            except (BrokenProcessPool, CancelledError, EOFError, OSError,
                    pickle.PickleError, RuntimeError, TypeError,
                    ValueError) as fehler:
                self.signale.abgeschlossen.emit(
                    self.generation, self.sequenz, self.koerper_name,
                    None, None, fehler,
                    time.perf_counter() - startzeit)
                return
            self.signale.abgeschlossen.emit(
                self.generation, self.sequenz, self.koerper_name,
                zustand, ergebnis, fehler, dauer)
            return

        from ..core.dynamik_6dof import schritt

        startzeit = time.perf_counter()
        ergebnis = None
        try:
            if hasattr(self.kraftfunktion, "fremdkraft_setzen"):
                self.kraftfunktion.fremdkraft_setzen(self.fremdkraft)
            for _ in range(self.anzahl_schritte):
                self.zustand, ergebnis = schritt(
                    self.zustand, self.kraftfunktion, self.koerper.masse,
                    self.koerper.traegheitstensor, self.dt,
                    self.physik.g_m_pro_s2)
        except (ArithmeticError, KeyError, ValueError) as fehler:
            self.signale.abgeschlossen.emit(
                self.generation, self.sequenz, self.koerper_name,
                None, None, fehler,
                time.perf_counter() - startzeit)
            return
        self.signale.abgeschlossen.emit(
            self.generation, self.sequenz, self.koerper_name,
            self.zustand, ergebnis, None,
            time.perf_counter() - startzeit)


class _StatischeAufgabeSignale(QObject):
    abgeschlossen = Signal(int, object, object, object, object)


class _StatischeAufgabe(QRunnable):
    def __init__(self, generation, name, koerper, ordner, rho_w, signale,
                 parameter=None):
        super().__init__()
        self.generation = generation
        self.name = name
        self.koerper = koerper
        self.ordner = ordner
        self.rho_w = rho_w
        self.signale = signale
        p = parameter or {}
        self.parameter = {"tol": p.get("toleranz", 1e-8),
                          "max_iter": p.get("max_iterationen", 60),
                          "stagnation_anteil": p.get("stagnation_anteil",
                                                     0.05)}

    def run(self):
        from ..core.statisch import SolverFehler
        from ..core.auftrieb import baue_kraftfunktion
        from ..core.konfig_lader import lade_physik
        from ..core.kraftmodell import baue_kraftmodell
        from ..core.statisch_robust import loese_robust

        try:
            physik = lade_physik(self.ordner)
            kraftfunktion = baue_kraftfunktion(
                self.koerper, rho_w=self.rho_w,
                g=physik.g_m_pro_s2,
                aufloesung=physik.voxel_aufloesung_m,
                pfad="exakt_union")
            kraftfunktion = baue_kraftmodell(kraftfunktion, physik)
            ergebnis = loese_robust(
                kraftfunktion, self.koerper.masse,
                g=physik.g_m_pro_s2, **self.parameter)
        except (ImportError, OSError, ValueError, SolverFehler) as fehler:
            self.signale.abgeschlossen.emit(
                self.generation, self.name, None, None, fehler)
            return
        self.signale.abgeschlossen.emit(
            self.generation, self.name, ergebnis, (kraftfunktion, physik), None)


class HauptFenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SegelPhysik")
        self.resize(1280, 800)
        from ..core.einstellungen import Einstellungen
        self._einstellungen = Einstellungen.laden()
        self._einstellungen_dialoge = {}
        self._baue_menues()
        self._baue_steuerzeile()
        self._baue_docks()
        self._echtzeit_timer = QTimer(self)
        self._echtzeit_timer.setInterval(16)
        self._echtzeit_timer.timeout.connect(self._echtzeit_takt)
        self._echtzeit_render_timer = QTimer(self)
        self._echtzeit_render_timer.setInterval(33)
        self._echtzeit_render_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._echtzeit_render_timer.timeout.connect(
            self._echtzeit_render_takt)
        self._echtzeit_akkumulator = 0.0
        self._echtzeit_angefordert_s = 0.0
        self._echtzeit_berechnet_s = 0.0
        self._echtzeit_modus = "pausiert"
        self._echtzeit_ueberlast_seit = None
        self._echtzeit_nachholen_start = None
        self._echtzeit_nachholen_berechnet_start = 0.0
        self._echtzeit_nachholen_fenster_start = None
        self._echtzeit_nachholen_fenster_berechnet = 0.0
        self._echtzeit_nachholen_raten = []
        self._echtzeit_letzte_wandzeit = None
        self._echtzeit_zustand = None
        self._echtzeit_kraftfunktion = None
        self._echtzeit_kraefteresultat = None
        self._echtzeit_physik = None
        self._echtzeit_name = None
        self._laufzeit_schwerpunkt = {}
        self._echtzeit_generation = 0
        self._echtzeit_aufgabe_laeuft = False
        self._echtzeit_schritte_laufend = 0
        self._echtzeit_auftragssequenz = 0
        self._echtzeit_aufgabe_sequenz_laufend = None
        self._echtzeit_prozess_executor = None
        self._echtzeit_prozess_koerper = None
        self._echtzeit_prozess_pfad = None
        self._echtzeit_aktiver_prozess_executor = None
        self._echtzeit_anzeige_start = None
        self._echtzeit_anzeige_ziel = None
        self._echtzeit_anzeige_startzeit = None
        self._echtzeit_anzeige_dauer = 0.0
        self._echtzeit_fps_start = time.perf_counter()
        self._echtzeit_fps_zaehler = 0
        self._echtzeit_angeforderte_fps = 0.0
        self._echtzeit_signale = _EchtzeitAufgabeSignale()
        self._echtzeit_signale.abgeschlossen.connect(
            self._echtzeit_aufgabe_abgeschlossen)
        self._statisch_generation = 0
        self._statisch_signale = _StatischeAufgabeSignale()
        self._statisch_signale.abgeschlossen.connect(
            self._statische_aufgabe_abgeschlossen)
        self._statische_ergebnisse = {}
        for meldung in self._einstellungen.meldungen:
            self.protokoll_schreiben("Einstellungen: %s" % meldung)

    def _einstellungen_dialog(self, bereich, **spezifikation):
        from .einstellungen_dialog import EinstellungenDialog
        dialog = self._einstellungen_dialoge.get(bereich)
        if dialog is None:
            dialog = EinstellungenDialog(
                self._einstellungen, bereich, self, **spezifikation)
            if spezifikation:
                dialog.geaendert.connect(self._stil_anwenden)
            self._einstellungen_dialoge[bereich] = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _pfeil_dialog(self, schluessel, titel, formular, pfeile=None):
        self._einstellungen_dialog(
            schluessel, titel="Kraftpfeildarstellung: " + titel,
            formular=formular, pfeile=pfeile)

    def _kraftpfeil_menue_bauen(self, menue):
        from ..core import pfeilstil as ps
        m = menue.addMenu("Kraftpfeildarstellung")
        m.addAction("Allgemein …", lambda: self._pfeil_dialog(
            "kp_allgemein", "Allgemein", [(ps.BEREICH_ALLGEMEIN, None)]))
        for pid, titel, _farbe in ps.PAARE:
            pfeile = [(ps.pfeil_bereich(p[0]), p[1])
                      for p in ps.paar_pfeile(pid)]
            m.addAction(titel + " …", lambda pid=pid, titel=titel,
                        pfeile=pfeile: self._pfeil_dialog(
                            "kp_" + pid, titel,
                            [(ps.BEREICH_PAARE, ["farbe_" + pid])], pfeile))
        weitere = m.addAction("Weitere Kräftepaare (noch keine)")
        weitere.setEnabled(False)
        m.addAction("Weitere Pfeile …", lambda: self._pfeil_dialog(
            "kp_weitere", "Weitere Pfeile", [],
            [(ps.pfeil_bereich(p[0]), p[1]) for p in ps.paarlose_pfeile()]))
        m.addAction("Schwerpunkte …", lambda: self._pfeil_dialog(
            "kp_schwerpunkte", "Schwerpunkte",
            [(ps.BEREICH_SCHWERPUNKTE, None)]))
        m.addAction("Hauptachsen …", lambda: self._pfeil_dialog(
            "kp_hauptachsen", "Hauptachsen",
            [(ps.BEREICH_HAUPTACHSEN, None)]))

    def _dyn(self, schluessel):
        return self._einstellungen.get("dynamisch", schluessel)

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
        m_solver = m_einst.addMenu("Solver-Parameter")
        m_solver.addAction(
            "Statisch …", lambda: self._einstellungen_dialog("statisch"))
        m_solver.addAction(
            "Dynamisch …", lambda: self._einstellungen_dialog("dynamisch"))
        self._kraftpfeil_menue_bauen(m_einst)
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
        self._btn_halt = QPushButton("=")
        self._btn_vor = QPushButton(">")
        self._btn_halt.setToolTip("Echtzeit-Simulation pausieren")
        self._btn_vor.setToolTip("Echtzeit-Simulation fortsetzen")
        self._btn_halt.clicked.connect(self._zeit_pausieren)
        self._btn_vor.clicked.connect(self._zeit_fortsetzen)
        for b in (self._btn_halt, self._btn_vor):
            b.setMaximumWidth(36)
            b.setCheckable(True)
        self._zeitgruppe = QButtonGroup(self)
        self._zeitgruppe.setExclusive(True)
        self._zeitgruppe.addButton(self._btn_halt)
        self._zeitgruppe.addButton(self._btn_vor)
        self._btn_halt.setChecked(True)
        self._btn_halt.toggled.connect(self._zeittasten_darstellen)
        self._btn_vor.toggled.connect(self._zeittasten_darstellen)
        h.addWidget(self._btn_statisch)
        h.addWidget(self._btn_echtzeit)
        h.addSpacing(24)
        h.addWidget(self._btn_halt)
        h.addWidget(self._btn_vor)
        h.addStretch(1)
        layout.addWidget(zeile)
        self._modusgruppe.buttonClicked.connect(
            self._modus_geaendert)
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
        for b in (self._btn_halt, self._btn_vor):
            b.setEnabled(not statisch_aktiv)
        self._zeittasten_darstellen()

    def _zeittasten_darstellen(self, *_):
        statisch = self._btn_statisch.isChecked()
        for b in (self._btn_halt, self._btn_vor):
            b.setStyleSheet(
                "QPushButton { background-color: #0078d4; color: white; }"
                if not statisch and b.isChecked() else "")

    def _zeittasten_setzen(self, laeuft):
        (self._btn_vor if laeuft else self._btn_halt).setChecked(True)

    def _baue_docks(self):
        self.baum = BaumWidget()
        self.baum.laufzeit_aenderung.connect(
            self._laufzeit_objekte_aktualisieren)
        self.baum.nur_aktives_bedienbar_setzen(
            self._act_nur_aktives.isChecked())
        dock_baum = QDockWidget("Komponentenbaum", self)
        dock_baum.setWidget(self.baum)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_baum)


        layer = QWidget()
        v = QVBoxLayout(layer)
        self._layer_checks = {}
        layer_einstellungen = (
            ("Schwerpunkt", LAYER_SCHWERPUNKT, False),
            ("Achsen", LAYER_HAUPTACHSEN, True),
            ("Kräfte", LAYER_KRAEFTE, True),
            ("Fremdkraft", LAYER_FREMDKRAFT, True),
            ("Momente", LAYER_MOMENTE, False),
        )
        for name, layer_name, aktiviert in layer_einstellungen:
            cb = QCheckBox(name)
            cb.setChecked(aktiviert)
            self._layer_checks[name] = cb
            cb.toggled.connect(
                lambda an, l=layer_name: self._layer_setzen(l, an))
            v.addWidget(cb)
        v.addStretch(1)

        status = QTreeWidget()
        status.setHeaderLabels(["Eigenschaft", "Wert"])
        self._solver_werte = {}
        for schluessel, wert in (
                ("z*", "-"), ("phi*", "-"), ("GM", "-"),
                ("Restkraft", "-"), ("Restmoment", "-"),
                ("Iterationen", "-"), ("Bildrate", "-"),
                ("Physik angefordert", "-"), ("Physik berechnet", "-"),
                ("Physik-Rückstand", "-"),
                ("Nachholrate letztes Fenster", "-"),
                ("Nachholrate gesamt", "-"),
                ("Nachholrate ≥1,25", "-"),
                ("Nachholfenster s/s", "-"), ("Lösungstyp", "-")):
            self._solver_werte[schluessel] = QTreeWidgetItem(
                status, [schluessel, wert])
        status.setRootIsDecorated(False)
        self._laufzeit_koerper = {}

        dock_layer = QDockWidget("Layer", self)
        dock_layer.setWidget(layer)
        dock_status = QDockWidget("Solver-Status", self)
        dock_status.setWidget(status)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_layer)
        self.splitDockWidget(dock_layer, dock_status, Qt.Orientation.Horizontal)

        darstellung = QWidget()
        darstellung_layout = QVBoxLayout(darstellung)
        self._kamera_auswahl = QComboBox()
        for label, wert in (
                ("Drei Viertel", "drei_viertel"),
                ("Bug", "bug"),
                ("Heck", "heck"),
                ("Draufsicht", "draufsicht")):
            self._kamera_auswahl.addItem(label, wert)
        self._kamera_auswahl.currentIndexChanged.connect(
            self._kamera_preset_geaendert)
        darstellung_layout.addWidget(QLabel("Kamera"))
        darstellung_layout.addWidget(self._kamera_auswahl)
        self._hintergrund_auswahl = QComboBox()
        for label, wert in (
                ("Verlauf", "verlauf"),
                ("Weiß", "weiss"),
                ("Dunkel", "dunkel")):
            self._hintergrund_auswahl.addItem(label, wert)
        self._hintergrund_auswahl.currentIndexChanged.connect(
            self._hintergrund_geaendert)
        darstellung_layout.addWidget(QLabel("Hintergrund"))
        darstellung_layout.addWidget(self._hintergrund_auswahl)
        self._licht_check = QCheckBox("Studio-Beleuchtung")
        self._licht_check.setChecked(True)
        self._licht_check.toggled.connect(self._beleuchtung_geaendert)
        darstellung_layout.addWidget(self._licht_check)
        self._wasser_check = QCheckBox("Wasseroberfläche")
        self._wasser_check.setChecked(True)
        self._wasser_check.toggled.connect(self._wasser_sichtbarkeit_geaendert)
        darstellung_layout.addWidget(self._wasser_check)
        self._wasseroptik_check = QCheckBox("Wasseroptik")
        self._wasseroptik_check.setChecked(True)
        self._wasseroptik_check.toggled.connect(
            self._wasseroptik_geaendert)
        darstellung_layout.addWidget(self._wasseroptik_check)
        self._wasserbew_check = QCheckBox("Körper zentriert, Wasser bewegt sich")
        self._wasserbew_check.setChecked(True)
        self._wasserbew_check.toggled.connect(self._wasserbewegung_geaendert)
        darstellung_layout.addWidget(self._wasserbew_check)
        self._ssao_check = QCheckBox("SSAO")
        self._ssao_check.setChecked(False)
        self._ssao_check.toggled.connect(self._ssao_geaendert)
        darstellung_layout.addWidget(self._ssao_check)
        darstellung_layout.addStretch(1)
        dock_darstellung = QDockWidget("Darstellung", self)
        dock_darstellung.setWidget(darstellung)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,
                           dock_darstellung)
        self.splitDockWidget(dock_layer, dock_darstellung,
                             Qt.Orientation.Vertical)

        fremd = QWidget()
        fremd_layout = QGridLayout(fremd)
        self._fremd_check = QCheckBox("Fremdkraft aktiv")
        self._fremd_check.toggled.connect(self._fremdkraft_geaendert)
        fremd_layout.addWidget(self._fremd_check, 0, 0, 1, 2)
        self._fremd_felder = {}
        for zeile, (schluessel, text, bereich, schritt, einheit) in enumerate((
                ("betrag", "Betrag", (0.0, 1e6, 100.0), 10.0, " N"),
                ("azimut", "Richtung Azimut", (-180.0, 180.0, 90.0), 5.0, "°"),
                ("elevation", "Richtung Höhe", (-90.0, 90.0, 0.0), 5.0, "°"),
                ("x", "Angriff x", (-100.0, 100.0, 0.0), 0.1, " m"),
                ("y", "Angriff y", (-100.0, 100.0, 0.0), 0.1, " m"),
                ("z", "Angriff z", (-100.0, 100.0, 0.0), 0.1, " m")), 1):
            feld = QDoubleSpinBox()
            feld.setRange(bereich[0], bereich[1])
            feld.setValue(bereich[2])
            feld.setSingleStep(schritt)
            feld.setDecimals(2)
            feld.setSuffix(einheit)
            feld.valueChanged.connect(self._fremdkraft_geaendert)
            self._fremd_felder[schluessel] = feld
            fremd_layout.addWidget(QLabel(text), zeile, 0)
            fremd_layout.addWidget(feld, zeile, 1)
        fremd_layout.setRowStretch(7, 1)
        dock_fremd = QDockWidget("Fremdkraft", self)
        dock_fremd.setWidget(fremd)
        self.splitDockWidget(dock_darstellung, dock_fremd,
                             Qt.Orientation.Vertical)

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
        for name, layer in (
                ("Schwerpunkt", LAYER_SCHWERPUNKT),
                ("Achsen", LAYER_HAUPTACHSEN),
                ("Kräfte", LAYER_KRAEFTE),
                ("Fremdkraft", LAYER_FREMDKRAFT),
                ("Momente", LAYER_MOMENTE)):
            bruecke.layer_setzen(layer, self._layer_checks[name].isChecked())
        self._stil_anwenden()
        self._darstellung_auf_bruecke_anwenden()
        self._laufzeit_objekte_aktualisieren("start")

    def _stil_anwenden(self):
        """Gibt den Pfeilstil aus den Einstellungen an die Bruecke."""
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None or not hasattr(bruecke, "stil_setzen"):
            return
        from ..core.pfeilstil import Stil
        bruecke.stil_setzen(Stil(self._einstellungen.bereich))
        if self._btn_echtzeit.isChecked():
            self._aktuelles_kraftbild_aktualisieren()
            bruecke.render()

    def _layer_setzen(self, layer, aktiviert):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            return
        if (aktiviert and layer in (LAYER_KRAEFTE, LAYER_MOMENTE,
                                      LAYER_SCHWERPUNKT, LAYER_FREMDKRAFT)
                and self._btn_echtzeit.isChecked()):
            self._aktuelles_kraftbild_aktualisieren()
        bruecke.layer_setzen(layer, aktiviert)
        bruecke.render()

    def _darstellung_auf_bruecke_anwenden(self):
        self._kamera_preset_geaendert()
        self._hintergrund_geaendert()
        self._beleuchtung_geaendert(self._licht_check.isChecked())
        self._wasser_sichtbarkeit_geaendert(self._wasser_check.isChecked())
        self._wasseroptik_geaendert(self._wasseroptik_check.isChecked())
        self._wasserbewegung_geaendert(self._wasserbew_check.isChecked())
        if self._ssao_check.isChecked():
            self._ssao_geaendert(True)

    def _darstellung_aktion(self, beschreibung, funktion):
        try:
            if not funktion():
                self.protokoll_schreiben(
                    "%s ist in der aktuellen 3D-Ansicht nicht verfügbar."
                    % beschreibung)
                return False
        except (AttributeError, RuntimeError, TypeError, ValueError) as fehler:
            self.protokoll_schreiben(
                "%s konnte nicht angewendet werden: %s"
                % (beschreibung, fehler))
            return False
        return True

    def _kamera_preset_geaendert(self, _index=None):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            preset = self._kamera_auswahl.currentData()
            self._darstellung_aktion(
                "Kamera-Preset",
                lambda: bruecke.kamera_preset_setzen(preset))

    def _hintergrund_geaendert(self, _index=None):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            preset = self._hintergrund_auswahl.currentData()
            self._darstellung_aktion(
                "Hintergrund",
                lambda: bruecke.hintergrund_setzen(preset))

    def _beleuchtung_geaendert(self, aktiviert):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            self._darstellung_aktion(
                "Studio-Beleuchtung",
                lambda: bruecke.beleuchtung_setzen(aktiviert))

    def _wasser_sichtbarkeit_geaendert(self, sichtbar):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            self._darstellung_aktion(
                "Wasseroberfläche",
                lambda: bruecke.wasser_sichtbar_setzen(sichtbar))

    def _wasseroptik_geaendert(self, aktiviert):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            self._darstellung_aktion(
                "Wasseroptik",
                lambda: bruecke.wasseroptik_setzen(aktiviert))

    def _wasserbewegung_geaendert(self, aktiviert):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            self._darstellung_aktion(
                "Wasserbewegung",
                lambda: bruecke.wasser_bewegung_setzen(aktiviert))

    def _ssao_geaendert(self, aktiviert):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            return
        if not self._darstellung_aktion(
                "SSAO", lambda: bruecke.ssao_setzen(aktiviert)):
            self._ssao_check.blockSignals(True)
            self._ssao_check.setChecked(not aktiviert)
            self._ssao_check.blockSignals(False)

    def _vorrang_bei_konflikt_waehlen(self, konflikt):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Bauteilüberschneidung")
        dialog.setText(
            "Überschneidung zwischen %s und %s (%.9g m³)."
            % (konflikt.name_a, konflikt.name_b, konflikt.volumen))
        dialog.setInformativeText(
            "Welches Bauteil soll unverändert bleiben? Das andere wird "
            "dauerhaft beschnitten. Vor dem Schreiben wird eine bytegetreue "
            "Sicherung mit der Endung .bak angelegt.")
        unveraendert_a = dialog.addButton(
            "%s unverändert lassen" % konflikt.name_a,
            QMessageBox.ButtonRole.AcceptRole)
        unveraendert_b = dialog.addButton(
            "%s unverändert lassen" % konflikt.name_b,
            QMessageBox.ButtonRole.AcceptRole)
        abbrechen = dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        gewaehlt = dialog.clickedButton()
        if gewaehlt is abbrechen:
            return None
        if gewaehlt is unveraendert_a:
            return konflikt.name_a
        if gewaehlt is unveraendert_b:
            return konflikt.name_b
        return None

    def _geometrie_konflikte_bereinigen(
            self, konfiguration, knoten, aktive):
        eintrag = knoten.eintrag
        if not isinstance(eintrag, dict) or "teile" not in eintrag:
            return True

        from ..core import boot_bau, fabriken, geometrie_konflikte as gk

        aktive_namen = {blatt.name for blatt in aktive}
        ordner = os.path.join(boot_bau.MODELL_ORDNER, knoten.name)

        def lade_specs():
            return fabriken._specs_aus_konfig(
                eintrag["teile"], konfiguration, boot_bau.SKALA, ordner,
                aktive_namen=aktive_namen)

        def blaetter(specs):
            for spec in specs:
                if "teile" in spec:
                    yield from blaetter(spec["teile"])
                else:
                    yield spec

        specs = lade_specs()
        anzahl = sum(1 for spec in blaetter(specs)
                     if "flaechenmasse" not in spec)
        max_korrekturen = anzahl * (anzahl - 1) // 2
        korrekturen = 0
        while True:
            teile = [
                {
                    "name": spec["_konflikt_name"],
                    "form": spec["form"],
                    "volumetrisch": "flaechenmasse" not in spec,
                }
                for spec in blaetter(specs)
            ]
            konflikte = gk.finde_konflikte(teile)
            if not konflikte:
                return True
            if korrekturen >= max_korrekturen:
                raise gk.GeometrieKonfliktFehler(
                    "Konfliktkorrektur hat die maximale Anzahl an "
                    "Bauteilpaaren überschritten")

            konflikt = konflikte[0]
            vorrang = self._vorrang_bei_konflikt_waehlen(konflikt)
            if vorrang is None:
                self.protokoll_schreiben(
                    "Geometriekorrektur abgebrochen; Physiklauf angehalten.")
                return False

            nachrang_name = (konflikt.name_b
                             if vorrang == konflikt.name_a
                             else konflikt.name_a)
            by_name = {spec["_konflikt_name"]: spec
                       for spec in blaetter(specs)}
            nachrang = by_name[nachrang_name]
            vorrang_spec = by_name[vorrang]
            gk.korrigiere_obj_quelle(
                nachrang["_quellpfad"], nachrang["form"],
                vorrang_spec["form"], skala=boot_bau.SKALA)
            self.protokoll_schreiben(
                "Geometrie korrigiert: %s beschnitten, %s bleibt unverändert."
                % (nachrang_name, vorrang))
            specs = lade_specs()
            korrekturen += 1

    def _laufzeit_objekte_aktualisieren(self, grund="auswahl"):
        self._statisch_generation += 1
        bruecke = getattr(self, "_bruecke", None)
        welt = self.baum._welt
        konfiguration = getattr(welt, "konfiguration", None)
        if bruecke is None or konfiguration is None:
            return

        from ..core.fabriken import baue_summenkoerper
        from .baum import aktive_blaetter, summenkoerper

        laufzeit_bereit = True
        schwerpunkt_alt = {}
        for knoten in summenkoerper(welt):
            if not knoten.sichtbar or knoten.eintrag is None:
                bruecke.sichtbar_setzen(knoten.name, False)
                self._laufzeit_koerper.pop(knoten.name, None)
                continue
            aktive = aktive_blaetter(knoten)
            if "teile" in knoten.eintrag and not aktive:
                bruecke.sichtbar_setzen(knoten.name, False)
                self._laufzeit_koerper.pop(knoten.name, None)
                continue
            try:
                if not self._geometrie_konflikte_bereinigen(
                        konfiguration, knoten, aktive):
                    bruecke.sichtbar_setzen(knoten.name, False)
                    self._laufzeit_koerper.pop(knoten.name, None)
                    laufzeit_bereit = False
                    continue
                koerper, modell_schwerpunkt = baue_summenkoerper(
                    konfiguration, knoten.name, aktive_blaetter=aktive)
                position = (tuple(modell_schwerpunkt)
                            if modell_schwerpunkt is not None else (0.0, 0.0, 0.0))
                schwerpunkt_alt[knoten.name] = self._laufzeit_schwerpunkt.get(
                    knoten.name)
                self._laufzeit_schwerpunkt[knoten.name] = position
                bruecke.koerper_objekt_setzen(
                    knoten.name, koerper, position=position)
                self._laufzeit_koerper[knoten.name] = koerper
            except (ImportError, OSError, ValueError) as fehler:
                bruecke.sichtbar_setzen(knoten.name, False)
                self._laufzeit_koerper.pop(knoten.name, None)
                laufzeit_bereit = False
                nachricht = ("Laufzeitkoerper %s konnte nicht aktualisiert "
                             "werden: %s" % (knoten.name, fehler))
                self.protokoll_schreiben(nachricht)
        if not laufzeit_bereit:
            self._zeit_pausieren()
            self._echtzeit_name = None
            return
        if grund in ("start", "auswahl") and self._btn_statisch.isChecked():
            self._statische_simulation_ausfuehren()
        elif self._btn_echtzeit.isChecked():
            war_laufend = (self._echtzeit_timer.isActive()
                           or self._btn_vor.isChecked())
            self._echtzeit_starten(
                zustand=(self._zustand_nach_umbau(schwerpunkt_alt)
                         if grund != "start" else None),
                auto_start=war_laufend)

    def _zustand_nach_umbau(self, schwerpunkt_alt):
        """Haelt die Modellpose beim Umbau fest: der Schwerpunkt wandert,
        die Lage der Geometrie im Raum bleibt unveraendert."""
        zustand = self._echtzeit_zustand
        name = self._echtzeit_name
        alt = schwerpunkt_alt.get(name)
        neu = self._laufzeit_schwerpunkt.get(name)
        if zustand is None or alt is None or neu is None:
            return zustand
        import numpy as np
        from ..core.dynamik_6dof import Zustand6DOF, quaternion_matrix
        versatz = quaternion_matrix(zustand.quaternion) @ (
            np.asarray(neu, float) - np.asarray(alt, float))
        position = np.asarray(zustand.position, float) + versatz
        return Zustand6DOF(
            position=tuple(float(w) for w in position),
            quaternion=zustand.quaternion,
            geschwindigkeit_koerper=zustand.geschwindigkeit_koerper,
            winkelgeschwindigkeit_koerper=zustand.winkelgeschwindigkeit_koerper)

    def _modus_geaendert(self, _knopf):
        statisch = self._btn_statisch.isChecked()
        self._steuerzeile_umschalten(statisch)
        if statisch:
            self._statisch_generation += 1
            self._zeit_pausieren()
            self._echtzeit_name = None
            self._statische_simulation_ausfuehren()
        else:
            self._statisch_generation += 1
            bruecke = getattr(self, "_bruecke", None)
            if bruecke is not None:
                for name in self._laufzeit_koerper:
                    bruecke.statische_pose_loeschen(name)
            self._echtzeit_starten()

    def _statische_simulation_ausfuehren(self):
        self._statisch_generation += 1
        generation = self._statisch_generation
        welt = self.baum._welt
        konfiguration = getattr(welt, "konfiguration", None)
        if konfiguration is None:
            return
        from .baum import summenkoerper
        hauptkoerper = next(
            (knoten for knoten in summenkoerper(welt) if knoten.sichtbar), None)
        if hauptkoerper is None:
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Kein Hauptkörper ausgewählt"})
            return
        koerper = self._laufzeit_koerper.get(hauptkoerper.name)
        bruecke = getattr(self, "_bruecke", None)
        if koerper is None or bruecke is None:
            return

        self._solver_status_aktualisieren(
            {"Lösungstyp": "Statische Berechnung läuft"})
        aufgabe = _StatischeAufgabe(
            generation, hauptkoerper.name, koerper,
            konfiguration.ordner, konfiguration.wasser_dichte(),
            self._statisch_signale,
            self._einstellungen.bereich("statisch"))
        QThreadPool.globalInstance().start(aufgabe)
    def _statische_aufgabe_abgeschlossen(
            self, generation, name, ergebnis, arbeitsdaten, fehler):
        if (generation != self._statisch_generation
                or not self._btn_statisch.isChecked()):
            return
        bruecke = getattr(self, "_bruecke", None)
        koerper = self._laufzeit_koerper.get(name)
        if bruecke is None or koerper is None:
            return
        if fehler is not None:
            from ..core.statisch import SolverFehler

            bruecke.statische_pose_loeschen(name)
            self._statische_ergebnisse.pop(name, None)
            status = "Fehler: %s" % fehler
            werte = {
                "z*": "-", "phi*": "-", "GM": "-",
                "Restkraft": "-", "Restmoment": "-",
                "Lösungstyp": status,
            }
            if isinstance(fehler, SolverFehler):
                diagnose = fehler.diagnose
                statusnamen = {
                    "instabile_lage": "Instabile Lage",
                    "stagnation": "Stagnation",
                    "budget_erschoepft": "Budget erschöpft",
                    "ungueltige_rechenergebnisse":
                        "Ungültige Rechenergebnisse",
                }
                werte["Lösungstyp"] = "%s: %s" % (
                    statusnamen.get(fehler.status, fehler.status), fehler)
                if "restkraft" in diagnose:
                    werte["Restkraft"] = "%.3g N" % diagnose["restkraft"]
                if "restmoment" in diagnose:
                    werte["Restmoment"] = "%.3g N·m" % diagnose["restmoment"]
                if "z" in diagnose:
                    werte["z*"] = "%.4f m" % diagnose["z"]
                if "phi" in diagnose:
                    werte["phi*"] = "%.2f°" % math.degrees(diagnose["phi"])
                kandidat = (
                    fehler.status in (
                        "instabile_lage", "stagnation", "budget_erschoepft")
                    and "z" in diagnose and "phi" in diagnose
                    and math.isfinite(diagnose["z"])
                    and math.isfinite(diagnose["phi"]))
                if kandidat and bruecke.statische_pose_setzen(
                        name, diagnose["z"], diagnose["phi"]):
                    werte["Lösungstyp"] = (
                        "Kandidat (nicht konvergiert/instabil) – %s"
                        % werte["Lösungstyp"])
            self._solver_status_aktualisieren(werte)
            self.protokoll_schreiben(
                "Statischer Solver (%s): %s" % (name, fehler))
            return

        kraftfunktion, physik = arbeitsdaten
        self._kraftbild_daten_setzen(
            bruecke, name, koerper, kraftfunktion, physik,
            ergebnis["z"], ergebnis["phi"])
        if not bruecke.statische_pose_setzen(
                name, ergebnis["z"], ergebnis["phi"]):
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
            return
        self._statische_ergebnisse[name] = ergebnis
        gm = ergebnis["gm"]
        self._solver_status_aktualisieren({
            "z*": "%.4f m" % ergebnis["z"],
            "phi*": "%.2f°" % math.degrees(ergebnis["phi"]),
            "GM": "-" if gm is None else "%.4f m" % gm,
            "Restkraft": "%.3g N" % ergebnis["restkraft"],
            "Restmoment": "%.3g N·m" % ergebnis["restmoment"],
            "Iterationen": str(ergebnis["iterationen"]),
            "Lösungstyp": (
                "neutral" if ergebnis.get("neutral")
                else "stabil (Stagnation)" if ergebnis.get("stagnation")
                else "stabil"),
        })

    def _echtzeit_starten(self, zustand=None, auto_start=True):
        if (self._echtzeit_timer.isActive()
                or self._echtzeit_render_timer.isActive()
                or self._echtzeit_schritte_laufend):
            self._zeit_pausieren()
        self._echtzeit_generation += 1
        self._echtzeit_letzte_wandzeit = None
        welt = self.baum._welt
        konfiguration = getattr(welt, "konfiguration", None)
        bruecke = getattr(self, "_bruecke", None)
        if konfiguration is None or bruecke is None:
            return
        from .baum import summenkoerper
        hauptkoerper = next(
            (knoten for knoten in summenkoerper(welt) if knoten.sichtbar), None)
        if hauptkoerper is None:
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Kein Hauptkörper ausgewählt"})
            return
        koerper = self._laufzeit_koerper.get(hauptkoerper.name)
        if koerper is None:
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Kein Laufzeitkörper verfügbar"})
            return

        from ..core.auftrieb import baue_kraftfunktion_6dof
        from ..core.dynamik_6dof import Zustand6DOF, quaternion_matrix
        from ..core.konfig_lader import lade_physik
        from ..core.kraftmodell import (
            KraftmodellMitHydroCache, baue_kraftmodell)
        try:
            physik = lade_physik(konfiguration.ordner)
            kraftfunktion = baue_kraftfunktion_6dof(
                koerper, rho_w=konfiguration.wasser_dichte(),
                g=physik.g_m_pro_s2,
                pfad=_ECHTZEIT_HYDROSTATIK_PFAD)
            kraftfunktion = KraftmodellMitHydroCache(
                baue_kraftmodell(kraftfunktion, physik), intervall=1)
            kraftfunktion.fremdkraft_setzen(self._fremdkraft_aktuell())
            basisposition = bruecke.physik_basis_position_ermitteln(
                hauptkoerper.name)
            prozess_executor = self._echtzeit_prozess_pool_aktualisieren(
                koerper, konfiguration.wasser_dichte(), physik,
                _ECHTZEIT_HYDROSTATIK_PFAD)
        except (ImportError, OSError, RuntimeError, ValueError) as fehler:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: %s" % fehler})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): %s" % (hauptkoerper.name, fehler))
            return

        if zustand is None:
            loesung = self._statische_ergebnisse.get(hauptkoerper.name)
            z = loesung["z"] if loesung else 0.0
            phi = loesung["phi"] if loesung else 0.0
            zustand = Zustand6DOF(
                position=(basisposition[0], basisposition[1], z),
                quaternion=(math.cos(phi / 2.0), math.sin(phi / 2.0),
                            0.0, 0.0))
        elif not isinstance(zustand, Zustand6DOF):
            raise TypeError("Echtzeit-Zustand muss ein Zustand6DOF sein")
        elif self._echtzeit_name != hauptkoerper.name:
            # Anderer Körper: Lage (z, Orientierung) übernehmen, Bewegung nicht
            zustand = Zustand6DOF(
                position=(basisposition[0], basisposition[1],
                          zustand.position[2]),
                quaternion=zustand.quaternion)
        self._echtzeit_name = hauptkoerper.name
        self._echtzeit_zustand = zustand
        self._echtzeit_anzeige_start = zustand
        self._echtzeit_anzeige_ziel = zustand
        self._echtzeit_anzeige_startzeit = None
        self._echtzeit_anzeige_dauer = 0.0
        self._echtzeit_physik = physik
        self._echtzeit_kraftfunktion = kraftfunktion
        self._echtzeit_aktiver_prozess_executor = prozess_executor
        self._echtzeit_kraefteresultat = None
        if (bruecke.layer_ist_an(LAYER_KRAEFTE)
                or bruecke.layer_ist_an(LAYER_MOMENTE)
                or bruecke.layer_ist_an(LAYER_FREMDKRAFT)
                or bruecke.layer_ist_an(LAYER_SCHWERPUNKT)):
            self._echtzeit_kraefteresultat = kraftfunktion(
                (zustand.position, zustand.quaternion),
                v=quaternion_matrix(zustand.quaternion)
                @ np.asarray(zustand.geschwindigkeit_koerper),
                omega=quaternion_matrix(zustand.quaternion)
                @ np.asarray(zustand.winkelgeschwindigkeit_koerper))
            self._kraftbild_daten_setzen(
                bruecke, hauptkoerper.name, koerper, kraftfunktion, physik,
                0.0, 0.0, ergebnis=self._echtzeit_kraefteresultat)
        if not self._echtzeit_pose_anzeigen(zustand, render=True):
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
            return
        self._solver_status_aktualisieren({"Lösungstyp": "Echtzeit"})
        if auto_start:
            self._zeit_fortsetzen()

    def _echtzeit_prozess_pool_aktualisieren(
            self, koerper, rho_w, physik, hydrostatik_pfad):
        if (not hasattr(koerper, "teile")
                or QApplication.platformName().casefold()
                in ("offscreen", "minimal")):
            return None
        if (self._echtzeit_prozess_executor is not None
                and self._echtzeit_prozess_koerper is koerper
                and self._echtzeit_prozess_pfad == hydrostatik_pfad):
            return self._echtzeit_prozess_executor
        from concurrent.futures import ProcessPoolExecutor
        from multiprocessing import get_context
        from ..core.echtzeit_prozess import initialisieren

        vorher = self._echtzeit_prozess_executor
        if vorher is not None:
            vorher.shutdown(wait=False, cancel_futures=True)
        executor = ProcessPoolExecutor(
            max_workers=1, mp_context=get_context("spawn"),
            initializer=initialisieren,
            initargs=(koerper, rho_w, physik, hydrostatik_pfad))
        self._echtzeit_prozess_executor = executor
        self._echtzeit_prozess_koerper = koerper
        self._echtzeit_prozess_pfad = hydrostatik_pfad
        return executor

    def _zeit_pausieren(self, automatisch=False):
        war_laufend = self._echtzeit_timer.isActive()
        jetzt = time.perf_counter()
        if (self._echtzeit_letzte_wandzeit is not None
                and self._echtzeit_modus in (
                    "normal", "ueberlast_beobachtung")):
            vergangen = max(
                0.0, jetzt - self._echtzeit_letzte_wandzeit)
            self._echtzeit_akkumulator += vergangen
            self._echtzeit_angefordert_s += vergangen
        self._echtzeit_generation += 1
        if war_laufend:
            self._echtzeit_timer.stop()
        if self._echtzeit_render_timer.isActive():
            self._echtzeit_render_timer.stop()
        if self._echtzeit_schritte_laufend and self._echtzeit_physik is not None:
            self._echtzeit_akkumulator += (
                self._echtzeit_schritte_laufend * self._echtzeit_physik.dt_s)
            self._echtzeit_schritte_laufend = 0
        self._echtzeit_letzte_wandzeit = None
        self._echtzeit_modus = (
            "automatisch_pausiert" if automatisch else "pausiert")
        self._echtzeit_ueberlast_seit = None
        self._zeittasten_setzen(False)
        if self._echtzeit_zustand is not None:
            self._echtzeit_anzeige_start = self._echtzeit_zustand
            self._echtzeit_anzeige_ziel = self._echtzeit_zustand
            self._echtzeit_anzeige_startzeit = None
            self._echtzeit_anzeige_dauer = 0.0
        if war_laufend:
            self._solver_status_aktualisieren({
                "Lösungstyp": "Pausiert",
                **self._echtzeit_zeitbilanz_status(),
            })
            self._echtzeit_pose_anzeigen(self._echtzeit_zustand, render=True)

    def _zeit_fortsetzen(self):
        if (not self._btn_echtzeit.isChecked()
                or self._echtzeit_timer.isActive()
                or self._echtzeit_kraftfunktion is None):
            return
        jetzt = time.perf_counter()
        self._echtzeit_letzte_wandzeit = jetzt
        self._echtzeit_fps_start = jetzt
        self._echtzeit_zf_berechnet = self._echtzeit_berechnet_s
        self._echtzeit_fps_zaehler = 0
        if self._echtzeit_rueckstand_s() > self._dyn(
                "nachholen_ende_rueckstand_s"):
            self._echtzeit_modus = "nachholen"
            self._echtzeit_nachholen_start = jetzt
            self._echtzeit_nachholen_berechnet_start = (
                self._echtzeit_berechnet_s)
            self._echtzeit_nachholen_fenster_start = jetzt
            self._echtzeit_nachholen_fenster_berechnet = (
                self._echtzeit_berechnet_s)
            self._echtzeit_nachholen_raten = []
        else:
            self._echtzeit_modus = "normal"
            self._echtzeit_nachholen_start = None
        self._echtzeit_timer.start()
        self._echtzeit_render_timer.start()
        self._zeittasten_setzen(True)
        self._solver_status_aktualisieren({
            "Lösungstyp": "Echtzeit",
            **self._echtzeit_zeitbilanz_status(),
        })

    def _rueckstand_text(self):
        return "%.3f s" % self._echtzeit_rueckstand_s()

    def _echtzeit_zeitbilanz_status(self):
        return {
            "Physik angefordert": "%.3f s" % self._echtzeit_angefordert_s,
            "Physik berechnet": "%.3f s" % self._echtzeit_berechnet_s,
            "Physik-Rückstand": self._rueckstand_text(),
        }

    def _echtzeit_rueckstand_s(self):
        return max(
            0.0, self._echtzeit_angefordert_s - self._echtzeit_berechnet_s)

    def _echtzeit_pose_anzeigen(self, pose, render=False):
        if pose is None:
            return False
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None or self._echtzeit_name is None:
            return False
        from ..core.dynamik_6dof import quaternion_matrix
        if not bruecke.physik_pose_6dof_setzen(
                self._echtzeit_name, quaternion_matrix(pose.quaternion),
                np.asarray(pose.position, dtype=np.float64)):
            return False
        if render:
            bruecke.render()
        return True

    def _echtzeit_render_takt(self):
        start = self._echtzeit_anzeige_start
        ziel = self._echtzeit_anzeige_ziel
        if start is None or ziel is None:
            return
        jetzt = time.perf_counter()
        if self._echtzeit_anzeige_startzeit is None:
            anteil = 1.0
        elif self._echtzeit_anzeige_dauer <= 0.0:
            anteil = 1.0
        else:
            anteil = min(
                1.0, max(0.0, (jetzt - self._echtzeit_anzeige_startzeit)
                         / self._echtzeit_anzeige_dauer))
        from ..core.dynamik_6dof import quaternion_slerp
        position = (
            np.asarray(start.position)
            + anteil * (np.asarray(ziel.position) - start.position))
        pose = type(ziel)(
            position=tuple(position),
            quaternion=tuple(quaternion_slerp(
                start.quaternion, ziel.quaternion, anteil)),
            geschwindigkeit_koerper=ziel.geschwindigkeit_koerper,
            winkelgeschwindigkeit_koerper=(
                ziel.winkelgeschwindigkeit_koerper))
        if not self._echtzeit_pose_anzeigen(pose, render=True):
            return
        self._echtzeit_fps_zaehler += 1
        vergangen = jetzt - self._echtzeit_fps_start
        if vergangen >= 1.0:
            self._echtzeit_angeforderte_fps = (
                self._echtzeit_fps_zaehler / vergangen)
            self._echtzeit_fps_zaehler = 0
            self._echtzeit_fps_start = jetzt
            zf_start = getattr(self, "_echtzeit_zf_berechnet", None)
            zeitfaktor = (
                (self._echtzeit_berechnet_s - zf_start) / vergangen
                if zf_start is not None else 0.0)
            self._echtzeit_zf_berechnet = self._echtzeit_berechnet_s
            self._solver_status_aktualisieren({
                "Bildrate": "%.1f FPS" % self._echtzeit_angeforderte_fps,
                "Zeitfaktor": "%.2f ×" % zeitfaktor,
                **self._echtzeit_zeitbilanz_status(),
            })

    def _echtzeit_takt(self):
        if (self._echtzeit_letzte_wandzeit is None
                or self._echtzeit_zustand is None
                or self._echtzeit_physik is None):
            self._zeit_pausieren()
            return
        jetzt = time.perf_counter()
        vergangen = max(0.0, jetzt - self._echtzeit_letzte_wandzeit)
        schnell = not self._dyn("zeitgenau")
        if schnell:
            # So schnell wie moeglich, aber nie schneller als die reale
            # Zeit: Wandzeit fuellt den Akkumulator, der auf einen Block
            # begrenzt ist. Ueberschuss verfaellt (Zeitlupe), kein
            # Rueckstand, keine Ueberlast-Pause, kein Nachholen.
            if self._echtzeit_modus == "nachholen":
                self._echtzeit_nachholen_start = None
            self._echtzeit_modus = "normal"
            self._echtzeit_ueberlast_seit = None
            self._echtzeit_letzte_wandzeit = jetzt
            block = (self._dyn("max_schritte_pro_aufgabe")
                     * self._echtzeit_physik.dt_s)
            self._echtzeit_akkumulator = min(
                self._echtzeit_akkumulator + vergangen, block)
            if self._echtzeit_aufgabe_laeuft:
                return
            self._echtzeit_angefordert_s = (
                self._echtzeit_berechnet_s + self._echtzeit_akkumulator)
        elif self._echtzeit_modus != "nachholen":
            self._echtzeit_akkumulator += vergangen
            self._echtzeit_angefordert_s += vergangen
        self._echtzeit_letzte_wandzeit = jetzt
        rueckstand = self._echtzeit_rueckstand_s()
        if self._echtzeit_modus == "nachholen":
            if rueckstand <= self._dyn("nachholen_ende_rueckstand_s"):
                gesamt_dauer = max(
                    jetzt - (self._echtzeit_nachholen_start or jetzt),
                    1e-12)
                gesamt_rate = (
                    self._echtzeit_berechnet_s
                    - self._echtzeit_nachholen_berechnet_start
                ) / gesamt_dauer
                ziel_rate = self._dyn("nachholrate_ziel")
                gesamt_gate = ("bestanden" if gesamt_rate >= ziel_rate
                               else "nicht erreicht")
                if gesamt_rate < ziel_rate:
                    self.protokoll_schreiben(
                        "Nachholrate %.3f s/s unterschreitet das Ziel "
                        "von %.2f s/s." % (gesamt_rate, ziel_rate))
                self._solver_status_aktualisieren({
                    "Nachholrate gesamt": "%.3f s/s" % gesamt_rate,
                    "Nachholrate Ziel erreicht": gesamt_gate,
                    "Nachholfenster s/s": ", ".join(
                        "%.3f" % rate
                        for rate in self._echtzeit_nachholen_raten),
                    **self._echtzeit_zeitbilanz_status(),
                })
                self._echtzeit_modus = "normal"
                self._echtzeit_nachholen_start = None
            elif (self._echtzeit_nachholen_fenster_start is not None
                  and jetzt - self._echtzeit_nachholen_fenster_start >= 1.0):
                fenster_dauer = (
                    jetzt - self._echtzeit_nachholen_fenster_start)
                rate = (
                    self._echtzeit_berechnet_s
                    - self._echtzeit_nachholen_fenster_berechnet
                ) / fenster_dauer
                self._echtzeit_nachholen_raten.append(rate)
                if rate < self._dyn("nachholrate_ziel"):
                    self.protokoll_schreiben(
                        "Nachholrate im Messfenster %.3f s/s "
                        "unterschreitet %.2f s/s."
                        % (rate, self._dyn("nachholrate_ziel")))
                self._echtzeit_nachholen_fenster_start = jetzt
                self._echtzeit_nachholen_fenster_berechnet = (
                    self._echtzeit_berechnet_s)
                self._solver_status_aktualisieren({
                    "Nachholrate letztes Fenster": "%.3f s/s" % rate,
                    **self._echtzeit_zeitbilanz_status(),
                })
        elif not schnell and rueckstand >= self._dyn(
                "ueberlast_rueckstand_s"):
            if self._echtzeit_ueberlast_seit is None:
                self._echtzeit_ueberlast_seit = jetzt
            self._echtzeit_modus = "ueberlast_beobachtung"
            if jetzt - self._echtzeit_ueberlast_seit >= self._dyn(
                    "ueberlast_dauer_s"):
                self.protokoll_schreiben(
                    "Echtzeit automatisch pausiert: Rückstand %.3f s "
                    "bestand mindestens %.1f s."
                    % (rueckstand, self._dyn("ueberlast_dauer_s")))
                self._zeit_pausieren(automatisch=True)
                self._solver_status_aktualisieren({
                    "Lösungstyp": "Automatisch pausiert (Überlast)",
                    **self._echtzeit_zeitbilanz_status(),
                })
                return
        else:
            self._echtzeit_ueberlast_seit = None
            self._echtzeit_modus = "normal"
        dt = self._echtzeit_physik.dt_s
        if not math.isfinite(dt) or dt <= 0.0:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: ungültiger Physik-Zeitschritt"})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): ungültiger Physik-Zeitschritt"
                % self._echtzeit_name)
            return
        if self._echtzeit_aufgabe_laeuft:
            return
        anzahl_schritte = min(
            int((self._echtzeit_akkumulator + 1e-12) / dt),
            (self._dyn("max_schritte_nachholen")
             if self._echtzeit_modus == "nachholen"
             else self._dyn("max_schritte_pro_aufgabe")))
        if anzahl_schritte == 0:
            return
        self._echtzeit_akkumulator -= anzahl_schritte * dt
        koerper = self._laufzeit_koerper.get(self._echtzeit_name)
        if koerper is None:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: Laufzeitkörper fehlt"})
            return
        self._echtzeit_auftragssequenz += 1
        sequenz = self._echtzeit_auftragssequenz
        aufgabe = _EchtzeitAufgabe(
            self._echtzeit_generation, sequenz, self._echtzeit_name,
            self._echtzeit_zustand,
            self._echtzeit_kraftfunktion, koerper, self._echtzeit_physik,
            dt, anzahl_schritte, self._echtzeit_signale,
            prozess_executor=self._echtzeit_aktiver_prozess_executor,
            fremdkraft=self._fremdkraft_aktuell())
        self._echtzeit_aufgabe_laeuft = True
        self._echtzeit_aufgabe_sequenz_laufend = sequenz
        self._echtzeit_schritte_laufend = anzahl_schritte
        QThreadPool.globalInstance().start(aufgabe)

    def _echtzeit_aufgabe_abgeschlossen(
            self, generation, sequenz, koerper_name, zustand,
            kraefteresultat, fehler, dauer_s):
        if sequenz != self._echtzeit_aufgabe_sequenz_laufend:
            return
        self._echtzeit_aufgabe_laeuft = False
        self._echtzeit_aufgabe_sequenz_laufend = None
        anzahl_schritte = self._echtzeit_schritte_laufend
        self._echtzeit_schritte_laufend = 0
        if (generation != self._echtzeit_generation
                or koerper_name != self._echtzeit_name
                or not self._btn_echtzeit.isChecked()):
            return
        if fehler is not None:
            if self._echtzeit_physik is not None:
                self._echtzeit_akkumulator += (
                    self._echtzeit_physik.dt_s * anzahl_schritte)
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: %s" % fehler})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): %s"
                % (self._echtzeit_name, fehler))
            return
        self._echtzeit_berechnet_s += (
            anzahl_schritte * self._echtzeit_physik.dt_s)
        if (self._echtzeit_modus == "ueberlast_beobachtung"
                and self._echtzeit_rueckstand_s() < self._dyn(
                    "ueberlast_rueckstand_s")):
            self._echtzeit_ueberlast_seit = None
            self._echtzeit_modus = "normal"
        vorherige_anzeige = (
            self._echtzeit_anzeige_ziel or self._echtzeit_zustand)
        self._echtzeit_zustand = zustand
        self._echtzeit_kraefteresultat = kraefteresultat
        self._echtzeit_anzeige_start = vorherige_anzeige
        self._echtzeit_anzeige_ziel = zustand
        self._echtzeit_anzeige_startzeit = time.perf_counter()
        self._echtzeit_anzeige_dauer = max(
            float(dauer_s), 1.0 / 60.0)
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            pose = zustand
            if (bruecke.layer_ist_an(LAYER_KRAEFTE)
                    or bruecke.layer_ist_an(LAYER_MOMENTE)
                    or bruecke.layer_ist_an(LAYER_FREMDKRAFT)
                or bruecke.layer_ist_an(LAYER_SCHWERPUNKT)):
                koerper = self._laufzeit_koerper.get(self._echtzeit_name)
            else:
                koerper = None
            if koerper is not None and kraefteresultat is not None:
                self._kraftbild_daten_setzen(
                    bruecke, self._echtzeit_name, koerper,
                    self._echtzeit_kraftfunktion, self._echtzeit_physik,
                    0.0, 0.0, ergebnis=kraefteresultat)
            if self._echtzeit_render_timer.isActive():
                return
            self._echtzeit_pose_anzeigen(pose, render=True)

    def _fremdkraft_aktuell(self):
        """Welt-Kraft und koerperfester Angriffspunkt (rel. Schwerpunkt)
        aus den Reglern; None wenn abgeschaltet."""
        check = getattr(self, "_fremd_check", None)
        if check is None or not check.isChecked():
            return None
        w = {k: f.value() for k, f in self._fremd_felder.items()}
        az, el = math.radians(w["azimut"]), math.radians(w["elevation"])
        kraft = (w["betrag"] * math.cos(el) * math.cos(az),
                 w["betrag"] * math.cos(el) * math.sin(az),
                 w["betrag"] * math.sin(el))
        return kraft, (w["x"], w["y"], w["z"])

    def _fremdkraft_geaendert(self, *_):
        if self._echtzeit_kraftfunktion is None:
            return
        try:
            self._echtzeit_kraftfunktion.fremdkraft_setzen(
                self._fremdkraft_aktuell())
        except (AttributeError, ValueError) as fehler:
            self.protokoll_schreiben("Fremdkraft: %s" % fehler)
            return
        if self._echtzeit_timer.isActive():
            return
        # Pausiert: Kraftbild sofort mit der neuen Kraft neu zeichnen
        self._echtzeit_kraefteresultat = None
        self._aktuelles_kraftbild_aktualisieren()
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None and self._echtzeit_zustand is not None:
            self._echtzeit_pose_anzeigen(self._echtzeit_zustand, render=True)

    def _aktuelles_kraftbild_aktualisieren(self):
        if (self._echtzeit_name is None or self._echtzeit_zustand is None
                or self._echtzeit_physik is None
                or self._echtzeit_kraftfunktion is None):
            return
        koerper = self._laufzeit_koerper.get(self._echtzeit_name)
        bruecke = getattr(self, "_bruecke", None)
        if koerper is not None and bruecke is not None:
            pose = self._echtzeit_zustand
            ergebnis = self._echtzeit_kraefteresultat
            if ergebnis is None:
                from ..core.dynamik_6dof import quaternion_matrix
                rotation = quaternion_matrix(pose.quaternion)
                ergebnis = self._echtzeit_kraftfunktion(
                    (pose.position, pose.quaternion),
                    v=rotation @ np.asarray(pose.geschwindigkeit_koerper),
                    omega=rotation @ np.asarray(
                        pose.winkelgeschwindigkeit_koerper))
            self._kraftbild_daten_setzen(
                bruecke, self._echtzeit_name, koerper,
                self._echtzeit_kraftfunktion, self._echtzeit_physik,
                0.0, 0.0, ergebnis=ergebnis)

    def _kraftbild_daten_setzen(self, bruecke, name, koerper, kraftfunktion,
                                physik, z, phi, v_z=0.0, omega_x=0.0,
                                ergebnis=None):
        if (not callable(kraftfunktion)
                or not hasattr(bruecke, "kraefte_daten_setzen")):
            return
        try:
            from ..core.kraefte_bild import skala_waehlen
            erg = ergebnis
            if erg is None:
                erg = kraftfunktion(
                    (z, phi, 0.0), v=(0.0, 0.0, v_z),
                    omega=(omega_x, 0.0, 0.0))
            ausdehnung = float(np.ptp(np.asarray(koerper.punkte), axis=0).max())
            skala = skala_waehlen(
                koerper.masse, physik.g_m_pro_s2,
                referenz_laenge=max(ausdehnung, 0.05))
            bruecke.kraefte_daten_setzen(
                name, erg, koerper.masse, physik.g_m_pro_s2, skala,
                fremd=self._fremdkraft_aktuell())
        except (ArithmeticError, AttributeError, TypeError, ValueError) as fehler:
            self.protokoll_schreiben(
                "Kräftebild (%s) konnte nicht aktualisiert werden: %s"
                % (name, fehler))

    def _solver_status_aktualisieren(self, werte):
        for schluessel, wert in werte.items():
            self._solver_werte[schluessel].setText(1, str(wert))

    def protokoll_schreiben(self, text):


        self.protokoll.append(text)

    def closeEvent(self, ereignis):
        if (self._echtzeit_timer.isActive()
                or self._echtzeit_render_timer.isActive()
                or self._echtzeit_schritte_laufend):
            self._zeit_pausieren()
        rueckstand = self._echtzeit_rueckstand_s()
        if rueckstand > 0.0:
            self.protokoll_schreiben(
                "Anwendung geschlossen; %.6f s Simulationsrückstand bleiben "
                "unberechnet (angefordert %.6f s, berechnet %.6f s)."
                % (rueckstand, self._echtzeit_angefordert_s,
                   self._echtzeit_berechnet_s))
        executor = self._echtzeit_prozess_executor
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)
            self._echtzeit_prozess_executor = None
        super().closeEvent(ereignis)

    def _protokoll_umschalten(self):
        self._dock_protokoll.setVisible(self._act_protokoll.isChecked())

    def baum_setzen(self, welt_knoten):
        self.baum.lade(welt_knoten)

    def _nur_aktives_bedienbar_setzen(self, aktiv):
        baum = getattr(self, "baum", None)
        if baum is not None:
            baum.nur_aktives_bedienbar_setzen(aktiv)
