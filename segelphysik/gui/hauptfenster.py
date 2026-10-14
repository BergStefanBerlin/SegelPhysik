# -*- coding: utf-8 -*-
"""Hauptfenster der SegelPhysik-GUI (Spec GUI v1, Stand G2)."""
from __future__ import annotations

import math
import os
import time

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QDockWidget, QTextEdit, QLabel, QCheckBox, QTreeWidget, QTreeWidgetItem,
    QComboBox, QMessageBox,
)

from .baum_widget import BaumWidget
from ..core.overlays import (LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                             LAYER_KRAEFTE, LAYER_MOMENTE)


_aktives_fenster = None


class HauptFenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SegelPhysik")
        self.resize(1280, 800)
        self._baue_menues()
        self._baue_steuerzeile()
        self._baue_docks()
        self._echtzeit_timer = QTimer(self)
        self._echtzeit_timer.setInterval(16)
        self._echtzeit_timer.timeout.connect(self._echtzeit_takt)
        self._echtzeit_akkumulator = 0.0
        self._echtzeit_letzte_wandzeit = None
        self._echtzeit_zustand = None
        self._echtzeit_kraftfunktion = None
        self._echtzeit_physik = None
        self._echtzeit_name = None
        self._statische_ergebnisse = {}

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
        self._btn_halt = QPushButton("=")
        self._btn_vor = QPushButton(">")
        self._btn_halt.setToolTip("Echtzeit-Simulation pausieren")
        self._btn_vor.setToolTip("Echtzeit-Simulation fortsetzen")
        self._btn_halt.clicked.connect(self._zeit_pausieren)
        self._btn_vor.clicked.connect(self._zeit_fortsetzen)
        for b in (self._btn_halt, self._btn_vor):
            b.setMaximumWidth(36)
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
            b.setStyleSheet(
                "QPushButton { background-color: #0078d4; color: white; }"
                if not statisch_aktiv else "")

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
        for schluessel, wert in (("z*", "-"), ("phi*", "-"), ("GM", "-"),
                                 ("Iterationen", "-"), ("Lösungstyp", "-")):
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
                ("Momente", LAYER_MOMENTE)):
            bruecke.layer_setzen(layer, self._layer_checks[name].isChecked())
        self._darstellung_auf_bruecke_anwenden()
        self._laufzeit_objekte_aktualisieren("start")

    def _layer_setzen(self, layer, aktiviert):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            return
        if (aktiviert and layer in (LAYER_KRAEFTE, LAYER_MOMENTE)
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
        bruecke = getattr(self, "_bruecke", None)
        welt = self.baum._welt
        konfiguration = getattr(welt, "konfiguration", None)
        if bruecke is None or konfiguration is None:
            return

        from ..core.fabriken import baue_summenkoerper
        from .baum import aktive_blaetter, summenkoerper

        laufzeit_bereit = True
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
            war_laufend = self._echtzeit_timer.isActive()
            self._echtzeit_starten(
                zustand=(self._echtzeit_zustand
                         if grund == "eigenschaft"
                         and self._echtzeit_name in self._laufzeit_koerper
                         else None),
                auto_start=war_laufend)

    def _modus_geaendert(self, _knopf):
        statisch = self._btn_statisch.isChecked()
        self._steuerzeile_umschalten(statisch)
        if statisch:
            self._zeit_pausieren()
            self._echtzeit_name = None
            self._statische_simulation_ausfuehren()
        else:
            bruecke = getattr(self, "_bruecke", None)
            if bruecke is not None:
                for name in self._laufzeit_koerper:
                    bruecke.statische_pose_loeschen(name)
            self._echtzeit_starten()

    def _statische_simulation_ausfuehren(self):
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

        from ..core.auftrieb import baue_kraftfunktion
        from ..core.konfig_lader import lade_physik
        from ..core.statisch_robust import SolverFehler, loese_robust
        try:
            physik = lade_physik(konfiguration.ordner)
            kraftfunktion = baue_kraftfunktion(
                koerper, rho_w=konfiguration.wasser_dichte(),
                g=physik.g_m_pro_s2,
                aufloesung=physik.voxel_aufloesung_m)
            ergebnis = loese_robust(
                kraftfunktion, koerper.masse, g=physik.g_m_pro_s2)
        except (ImportError, OSError, ValueError, SolverFehler) as fehler:
            bruecke.statische_pose_loeschen(hauptkoerper.name)
            self._statische_ergebnisse.pop(hauptkoerper.name, None)
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: %s" % fehler})
            self.protokoll_schreiben(
                "Statischer Solver (%s): %s" % (hauptkoerper.name, fehler))
            return

        self._kraftbild_daten_setzen(
            bruecke, hauptkoerper.name, koerper, kraftfunktion, physik,
            ergebnis["z"], ergebnis["phi"])
        if not bruecke.statische_pose_setzen(
                hauptkoerper.name, ergebnis["z"], ergebnis["phi"]):
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
            return
        self._statische_ergebnisse[hauptkoerper.name] = ergebnis
        gm = ergebnis["gm"]
        self._solver_status_aktualisieren({
            "z*": "%.4f m" % ergebnis["z"],
            "phi*": "%.2f°" % math.degrees(ergebnis["phi"]),
            "GM": "-" if gm is None else "%.4f m" % gm,
            "Iterationen": str(ergebnis["iterationen"]),
            "Lösungstyp": ("neutral" if ergebnis.get("neutral")
                           else "stabil"),
        })

    def _echtzeit_starten(self, zustand=None, auto_start=True):
        if self._echtzeit_timer.isActive():
            self._echtzeit_timer.stop()
        self._echtzeit_letzte_wandzeit = None
        self._echtzeit_akkumulator = 0.0
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

        from ..core.auftrieb import baue_kraftfunktion
        from ..core.dynamik import Bewegungszustand
        from ..core.konfig_lader import lade_physik
        try:
            physik = lade_physik(konfiguration.ordner)
            kraftfunktion = baue_kraftfunktion(
                koerper, rho_w=konfiguration.wasser_dichte(),
                g=physik.g_m_pro_s2,
                aufloesung=physik.voxel_aufloesung_m)
        except (ImportError, OSError, ValueError) as fehler:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: %s" % fehler})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): %s" % (hauptkoerper.name, fehler))
            return

        if zustand is None:
            loesung = self._statische_ergebnisse.get(hauptkoerper.name)
            zustand = Bewegungszustand(
                z=loesung["z"] if loesung else 0.0,
                phi=loesung["phi"] if loesung else 0.0)
        self._echtzeit_name = hauptkoerper.name
        self._echtzeit_zustand = zustand
        self._echtzeit_physik = physik
        self._echtzeit_kraftfunktion = kraftfunktion
        if (bruecke.layer_ist_an(LAYER_KRAEFTE)
                or bruecke.layer_ist_an(LAYER_MOMENTE)):
            self._kraftbild_daten_setzen(
                bruecke, hauptkoerper.name, koerper, kraftfunktion, physik,
                zustand.z, zustand.phi, zustand.v_z, zustand.omega_x)
        if not bruecke.physik_pose_setzen(
                hauptkoerper.name, zustand.z, zustand.phi):
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
            return
        self._solver_status_aktualisieren({"Lösungstyp": "Echtzeit"})
        if auto_start:
            self._zeit_fortsetzen()

    def _zeit_pausieren(self):
        if not self._echtzeit_timer.isActive():
            return
        self._echtzeit_timer.stop()
        self._echtzeit_letzte_wandzeit = None
        self._echtzeit_akkumulator = 0.0
        self._solver_status_aktualisieren({"Lösungstyp": "Pausiert"})

    def _zeit_fortsetzen(self):
        if (not self._btn_echtzeit.isChecked()
                or self._echtzeit_timer.isActive()
                or self._echtzeit_kraftfunktion is None):
            return
        self._echtzeit_letzte_wandzeit = time.perf_counter()
        self._echtzeit_timer.start()
        self._solver_status_aktualisieren({"Lösungstyp": "Echtzeit"})

    def _echtzeit_takt(self):
        if (self._echtzeit_letzte_wandzeit is None
                or self._echtzeit_zustand is None
                or self._echtzeit_physik is None):
            self._zeit_pausieren()
            return
        jetzt = time.perf_counter()
        self._echtzeit_akkumulator += max(
            0.0, jetzt - self._echtzeit_letzte_wandzeit)
        self._echtzeit_letzte_wandzeit = jetzt
        from ..core.dynamik import schritt_mit_kraeften
        dt = self._echtzeit_physik.dt_s
        letztes_kraefteresultat = None
        try:
            while self._echtzeit_akkumulator >= dt:
                koerper = self._laufzeit_koerper[self._echtzeit_name]
                (self._echtzeit_zustand,
                 letztes_kraefteresultat) = schritt_mit_kraeften(
                    self._echtzeit_zustand, self._echtzeit_kraftfunktion,
                    koerper.masse, koerper.traegheitstensor[0, 0], dt,
                    self._echtzeit_physik.g_m_pro_s2,
                    self._echtzeit_physik.daempfung_tauchung,
                    self._echtzeit_physik.daempfung_kraengung)
                self._echtzeit_akkumulator -= dt
        except (ArithmeticError, KeyError, ValueError) as fehler:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: %s" % fehler})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): %s"
                % (self._echtzeit_name, fehler))
            return
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            pose = self._echtzeit_zustand
            if (bruecke.layer_ist_an(LAYER_KRAEFTE)
                    or bruecke.layer_ist_an(LAYER_MOMENTE)) \
                    and letztes_kraefteresultat is not None:
                koerper = self._laufzeit_koerper[self._echtzeit_name]
                self._kraftbild_daten_setzen(
                    bruecke, self._echtzeit_name, koerper,
                    self._echtzeit_kraftfunktion, self._echtzeit_physik,
                    pose.z, pose.phi, pose.v_z, pose.omega_x,
                    ergebnis=letztes_kraefteresultat)
            if not bruecke.physik_pose_setzen(
                    self._echtzeit_name, pose.z, pose.phi):
                self._zeit_pausieren()
                self._solver_status_aktualisieren(
                    {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
                return
            bruecke.render()

    def _aktuelles_kraftbild_aktualisieren(self):
        if (self._echtzeit_name is None or self._echtzeit_zustand is None
                or self._echtzeit_physik is None
                or self._echtzeit_kraftfunktion is None):
            return
        koerper = self._laufzeit_koerper.get(self._echtzeit_name)
        bruecke = getattr(self, "_bruecke", None)
        if koerper is not None and bruecke is not None:
            pose = self._echtzeit_zustand
            self._kraftbild_daten_setzen(
                bruecke, self._echtzeit_name, koerper,
                self._echtzeit_kraftfunktion, self._echtzeit_physik,
                pose.z, pose.phi, pose.v_z, pose.omega_x)

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
                name, erg, koerper.masse, physik.g_m_pro_s2, skala)
        except (ArithmeticError, AttributeError, TypeError, ValueError) as fehler:
            self.protokoll_schreiben(
                "Kräftebild (%s) konnte nicht aktualisiert werden: %s"
                % (name, fehler))

    def _solver_status_aktualisieren(self, werte):
        for schluessel, wert in werte.items():
            self._solver_werte[schluessel].setText(1, str(wert))

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
