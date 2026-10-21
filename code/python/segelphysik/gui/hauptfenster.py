# -*- coding: utf-8 -*-
"""Hauptfenster der SegelPhysik-GUI (Spec GUI v1, Stand G2)."""
from __future__ import annotations

import math
import os
import time
from dataclasses import replace

import numpy as np
from PySide6.QtCore import (
    Qt, QObject, QRunnable, QSignalBlocker, QThreadPool, QTimer, Signal,
)
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton,
    QDockWidget, QTextEdit, QLabel, QCheckBox, QTreeWidget, QTreeWidgetItem,
    QComboBox, QMessageBox, QDoubleSpinBox, QGridLayout,
)

from .baum_widget import BaumWidget
from ..core import formerkennung, statusanzeige

# Netzrauschen (Facetten) bei Kugel/liegendem Rotationskoerper: dM/mg ~ 1e-4
ROLL_NEUTRAL_TOLERANZ = 1e-2
from ..core.overlays import (LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
                             LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT,
                             LAYER_HYDRO_RUMPF, LAYER_HYDRO_KIEL,
                             LAYER_HYDRO_RUDER)


_aktives_fenster = None
_ECHTZEIT_HYDROSTATIK_PFAD = "exakt_union"
_ECHTZEIT_ANZEIGE_PUFFER_MAX_S = 0.25


def _stationaere_rotation(stufe):
    from ..core.stationaer_hydrodynamik import _rotation

    return _rotation(*(float(w) for w in stufe.pose[3:6]))


def _stationaere_kraftlage(stufe):
    from ..core.dynamik_6dof import quaternion_aus_matrix

    rotation = _stationaere_rotation(stufe)
    pose = ((0.0, 0.0, float(stufe.pose[2])),
            quaternion_aus_matrix(rotation))
    geschwindigkeit = np.asarray(stufe.geschwindigkeit_m_s, dtype=float)
    winkelgeschwindigkeit = np.asarray(
        stufe.winkelgeschwindigkeit_rad_s, dtype=float)
    return pose, geschwindigkeit, winkelgeschwindigkeit, rotation


class _EchtzeitAufgabeSignale(QObject):
    abgeschlossen = Signal(int, int, str, object, object, object, float)


class _EchtzeitAufgabe(QRunnable):
    def __init__(self, generation, sequenz, koerper_name, zustand,
                 kraftfunktion, koerper, physik, dt, anzahl_schritte,
                 signale, prozess_executor=None, fremdkraft=None,
                 ruderwinkel_rad=0.0):
        super().__init__()
        self.fremdkraft = fremdkraft
        self.ruderwinkel_rad = float(ruderwinkel_rad)
        self.generation = generation
        self.sequenz = sequenz
        self.koerper_name = koerper_name
        self.zustand = zustand
        self.kraftfunktion = kraftfunktion
        self.koerper = koerper.snapshot()
        self.koerper_version = self.koerper.version
        self.physik = physik
        self.dt = dt
        self.anzahl_schritte = anzahl_schritte
        self.signale = signale
        self.prozess_executor = prozess_executor

    def run(self):
        try:
            if hasattr(self.kraftfunktion, "aktualisieren"):
                self.kraftfunktion.aktualisieren()
            if hasattr(self.kraftfunktion, "ruderwinkel_setzen"):
                self.kraftfunktion.ruderwinkel_setzen(
                    self.ruderwinkel_rad)
        except (ArithmeticError, AttributeError, KeyError, TypeError, ValueError) as fehler:
            self.signale.abgeschlossen.emit(
                self.generation, self.sequenz, self.koerper_name,
                None, None, fehler, 0.0)
            return
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
                        self.anzahl_schritte, self.fremdkraft,
                        self.ruderwinkel_rad).result())
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
            if hasattr(self.kraftfunktion, "ruderwinkel_setzen"):
                self.kraftfunktion.ruderwinkel_setzen(
                    self.ruderwinkel_rad)
            if self.anzahl_schritte == 0:
                from ..core.dynamik_6dof import quaternion_matrix
                rotation = quaternion_matrix(self.zustand.quaternion)
                ergebnis = self.kraftfunktion(
                    (self.zustand.position, self.zustand.quaternion),
                    v=rotation @ np.asarray(self.zustand.geschwindigkeit_koerper),
                    omega=rotation @ np.asarray(
                        self.zustand.winkelgeschwindigkeit_koerper))
                if ergebnis is None:
                    raise ValueError("Kraftauswertung hat keine Daten geliefert")
            for _ in range(self.anzahl_schritte):
                self.zustand, ergebnis = schritt(
                    self.zustand, self.kraftfunktion, self.koerper.masse,
                    self.koerper.traegheitstensor, self.dt,
                    self.physik.g_m_pro_s2)
        except (ArithmeticError, AttributeError, KeyError, TypeError, ValueError) as fehler:
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
    fortschritt = Signal(int, str, object)


class _StatischeAufgabe(QRunnable):
    def __init__(self, generation, name, koerper, ordner, rho_w, signale,
                 parameter=None, fremdkraft=None, ruderwinkel_rad=0.0):
        super().__init__()
        self.generation = generation
        self.name = name
        self.koerper = koerper.snapshot()
        self.koerper_version = self.koerper.version
        self.ordner = ordner
        self.rho_w = rho_w
        self.signale = signale
        self.fremdkraft = fremdkraft
        self.ruderwinkel_rad = float(ruderwinkel_rad)
        p = parameter or {}
        self.parameter = {"tol": p.get("toleranz", 1e-8),
                          "max_iter": p.get("max_iterationen", 60),
                          "stagnation_anteil": p.get("stagnation_anteil",
                                                     0.05)}

    def run(self):
        from ..core.statisch import SolverFehler
        from ..core.auftrieb import baue_kraftfunktion
        from ..core.konfig_lader import lade_konfig, lade_physik
        from ..core.kraftmodell import baue_kraftmodell
        from ..core.hydrodynamik import (
            HydrodynamikModell,
            hydrodynamik_testprofil,
            wasserlinienlaenge_m,
        )
        from ..core.statisch_robust import loese_robust

        try:
            physik = lade_physik(self.ordner)
            konfiguration = lade_konfig(self.ordner)
            profil_konfig = konfiguration.hydrodynamik_profile.get(
                self.name)
            profil = hydrodynamik_testprofil(self.name, profil_konfig)
            cd_volumenkoerper = (
                profil.cd_volumenkoerper
                if profil is not None
                and profil.modell == "generischer_volumenkoerper"
                else None)
            kraftfunktion = baue_kraftfunktion(
                self.koerper, rho_w=self.rho_w,
                g=physik.g_m_pro_s2,
                aufloesung=physik.voxel_aufloesung_m,
                pfad="exakt_union")
            hydromodell = HydrodynamikModell.aus_koerper(
                self.koerper, rho_kg_m3=self.rho_w,
                cd_volumenkoerper=cd_volumenkoerper,
                fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
                fluidwinkelgeschwindigkeit=(
                    physik.fluidwinkelgeschwindigkeit),
                ruderwinkel_rad=self.ruderwinkel_rad)
            kraftfunktion = baue_kraftmodell(
                kraftfunktion, physik, masse=self.koerper.masse,
                g=physik.g_m_pro_s2,
                hydrodynamik=hydromodell)
            kraftfunktion.fremdkraft_setzen(self.fremdkraft)
            problem = statusanzeige.schwimmpruefung(
                kraftfunktion, self.koerper, self.koerper.masse,
                physik.g_m_pro_s2)
            if problem is not None:
                raise SolverFehler(
                    "Körper kann nicht tragen (%s)" % problem,
                    status=problem, diagnose={})
            parameter = dict(self.parameter)
            form, achse = formerkennung.analysiere_koerper(self.koerper)
            if formerkennung.rollneutral_erwartet(form, achse):
                parameter["neutral_toleranz"] = ROLL_NEUTRAL_TOLERANZ
            ergebnis = loese_robust(
                kraftfunktion, self.koerper.masse,
                g=physik.g_m_pro_s2, **parameter)
            testkraft = (np.asarray(self.fremdkraft[0], dtype=float)
                         if self.fremdkraft is not None
                         else np.zeros(3))
            if (hydromodell is not None
                    and float(np.linalg.norm(testkraft)) > 1e-6):
                from ..core.stationaer_hydrodynamik import (
                    StationaeresErgebnis,
                    StationaerSolverFehler,
                    loese_stationaer,
                    pruefe_stationaer_dynamisch,
                )

                rumpfteile = [
                    teil for teil in hydromodell.teile
                    if teil.rolle == "rumpf"]
                if rumpfteile:
                    laenge = wasserlinienlaenge_m(
                        rumpfteile, z_m=ergebnis["z"],
                        phi_rad=ergebnis["phi"])
                else:
                    meshes = getattr(self.koerper, "blatt_meshes", ())
                    punkte = (np.concatenate(
                        [np.asarray(mesh[0], dtype=float) for mesh in meshes])
                        if meshes else np.empty((0, 3)))
                    laenge = (float(np.max(np.ptp(punkte, axis=0)))
                              if len(punkte) else 0.0)
                if laenge <= 1e-6:
                    raise ValueError(
                        "Stationaerer Hydrodynamiksolver benoetigt eine "
                        "positive charakteristische Koerperlaenge")
                if profil is not None and profil.modell == (
                        "generischer_volumenkoerper"):
                    referenzgeschwindigkeit = (
                        profil.referenzgeschwindigkeit_m_pro_s)
                else:
                    rumpfgeschwindigkeit = (
                        1.34 * 0.514444 * math.sqrt(laenge / 0.3048))
                    referenzgeschwindigkeit = 0.8 * rumpfgeschwindigkeit
                start = np.array((
                    referenzgeschwindigkeit, ergebnis["z"], 0.0, 0.0,
                    ergebnis["phi"], 0.0))
                startzeit = time.perf_counter()
                try:
                    stationaer = loese_stationaer(
                        kraftfunktion,
                        charakteristische_kraft_N=float(
                            np.linalg.norm(testkraft)),
                        charakteristische_laenge_m=laenge,
                        referenzgeschwindigkeit_m_s=referenzgeschwindigkeit,
                        start=start, ruderwinkel_rad=self.ruderwinkel_rad,
                        fortschritt=lambda stufe:
                            self.signale.fortschritt.emit(
                                self.generation, self.name, stufe))
                except StationaerSolverFehler as fehler:
                    stationaer = StationaeresErgebnis(
                        False, fehler.stufen,
                        time.perf_counter() - startzeit,
                        self.ruderwinkel_rad)
                    ergebnis["stationaer_fehler"] = str(fehler)
                else:
                    ergebnis["stationaer_dynamikpruefung"] = (
                        pruefe_stationaer_dynamisch(
                            kraftfunktion, stationaer.stufen[-1],
                            masse_kg=self.koerper.masse,
                            traegheit_koerper=(
                                self.koerper.traegheitstensor),
                            charakteristische_laenge_m=laenge,
                            dt_s=physik.dt_s,
                            g_m_pro_s2=physik.g_m_pro_s2))
                ergebnis["stationaer_hydrodynamik"] = stationaer
            stationaer = ergebnis.get("stationaer_hydrodynamik")
            stufe = (next((s for s in reversed(stationaer.stufen) if s.konvergiert), None)
                     if stationaer is not None else None)
            if stufe is None:
                kraft_ergebnis = kraftfunktion((ergebnis["z"], ergebnis["phi"], 0.0))
                kriterien = ergebnis.get("solverkriterien", ())
                ergebnis["kraft_solver"] = (
                    "statisch_robust.loese_robust", ("z", "rollen"),
                    kriterien, True, False) if kriterien else None
            else:
                pose, v, omega, _rotation = _stationaere_kraftlage(stufe)
                kraft_ergebnis = kraftfunktion(pose, v=v, omega=omega)
                ergebnis["kraft_solver"] = (
                    "stationaer_hydrodynamik: " + stufe.name,
                    stufe.solver_freiheitsgrade, stufe.solver_kriterien,
                    stufe.solver_erfuellt, True
                ) if getattr(stufe, "solver_erfuellt", None) is not None else None
            if hasattr(kraft_ergebnis, "mit_beschleunigung"):
                kraft_ergebnis = kraft_ergebnis.mit_beschleunigung((0.0,) * 6)
            ergebnis["kraft_ergebnis"] = kraft_ergebnis
        except (AttributeError, ImportError, OSError, TypeError, ValueError, SolverFehler,
                ArithmeticError, RuntimeError) as fehler:
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
        self._kraftanzeige_snapshots = {}
        self._kraftanzeige_generation = 0
        self._kraftanzeige_kontext = None
        self._kraftanzeige_sequenz = 0
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
        self._echtzeit_letzte_wandzeit = None
        self._echtzeit_zustand = None
        self._echtzeit_kraftfunktion = None
        self._echtzeit_kraefteresultat = None
        self._echtzeit_physik = None
        self._echtzeit_name = None
        self._laufzeit_schwerpunkt = {}
        self._echtzeit_generation = 0
        self._echtzeit_aufgabe_laeuft = False
        self._echtzeit_kraftauswertung_ausstehend = False
        self._echtzeit_schritte_laufend = 0
        self._echtzeit_auftragssequenz = 0
        self._echtzeit_aufgabe_sequenz_laufend = None
        self._echtzeit_prozess_executor = None
        self._echtzeit_prozess_koerper = None
        self._echtzeit_prozess_pfad = None
        self._echtzeit_prozess_cd = None
        self._echtzeit_aktiver_prozess_executor = None
        self._echtzeit_anzeige_verlauf = []
        self._echtzeit_anzeige_verzoegerung_s = 0.0
        self._echtzeit_anzeigezeit_s = 0.0
        self._echtzeit_anzeige_wandzeit = None
        self._echtzeit_fps_start = time.perf_counter()
        self._echtzeit_fps_zaehler = 0
        self._echtzeit_angeforderte_fps = 0.0
        self._echtzeit_signale = _EchtzeitAufgabeSignale()
        self._echtzeit_signale.abgeschlossen.connect(
            self._echtzeit_aufgabe_abgeschlossen)
        self._statisch_generation = 0
        self._statische_aufgaben = {}
        self._statische_aufgaben_ausstehend = {}
        self._statisch_signale = _StatischeAufgabeSignale()
        self._statisch_signale.abgeschlossen.connect(
            self._statische_aufgabe_abgeschlossen)
        self._hydrodynamik_profil_koerper = None
        self._statisch_signale.fortschritt.connect(
            self._statische_aufgabe_fortschritt)
        self._statische_ergebnisse = {}
        self._statische_arbeitsdaten = {}
        self._statische_fremdkraft = None
        self._navigationsfenster = None
        self._navigations_timer = QTimer(self)
        self._navigations_timer.setInterval(33)
        self._navigations_timer.timeout.connect(
            self._navigationsanzeigen_aktualisieren)
        from .steuer_api import GUIControlAPI
        self.steuer_api = GUIControlAPI(self)
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
            elif bereich == "statisch":
                dialog.geaendert.connect(self._solver_einstellung_geaendert)
            elif bereich == "modell":
                dialog.geaendert.connect(
                    self._modellpfad_einstellung_geaendert)
            elif bereich == "anzeigen":
                dialog.geaendert.connect(
                    self._navigationssichtbarkeit_aktualisieren)
            self._einstellungen_dialoge[bereich] = dialog
        dialog.neu_laden()
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _solver_einstellung_geaendert(self):
        """Geaenderte Solver-Parameter gelten sofort: statisch neu rechnen."""
        if self._btn_statisch.isChecked():
            self._statische_simulation_ausfuehren()

    def _modellpfad_einstellung_geaendert(self):
        welt = getattr(getattr(self, "baum", None), "_welt", None)
        konfiguration = getattr(welt, "konfiguration", None)
        if konfiguration is None:
            return
        aktiviert = self._einstellungen.get("modell", "paketfabrik_aktiv")
        if getattr(konfiguration, "paketfabrik_aktiv", None) == aktiviert:
            return
        konfiguration.paketfabrik_aktiv = aktiviert
        self._laufzeit_objekte_aktualisieren("modellpfad")

    def _pfeil_dialog(self, schluessel, titel, formular, pfeile=None):
        self._einstellungen_dialog(
            schluessel, titel="Kraftpfeildarstellung: " + titel,
            formular=formular, pfeile=pfeile)

    def _kraftpfeil_menue_bauen(self, menue):
        from ..core import pfeilstil as ps
        m = menue.addMenu("Kraftpfeildarstellung")
        m.addAction("Skalen und Bildschirmgroessen …", lambda: self._pfeil_dialog(
            "kp_snapshot", "Skalen und Bildschirmgroessen", [
                ("kraefteanzeige", [k for k, e in
                 self._einstellungen.vorlage["kraefteanzeige"].items()
                 if e["typ"] not in ("fensterlayout", "sichtbarkeiten")])]))
        m.addAction("Neu einpassen", self._kraftanzeige_neu_einpassen)
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
        m_einst.addAction(
            "Modellfabrik …", lambda: self._einstellungen_dialog("modell"))
        m_einst.addAction(
            "Anzeigeoptionen …",
            lambda: self._einstellungen_dialog("anzeigen"))
        self._kraftpfeil_menue_bauen(m_einst)
        m_ansicht = self.menuBar().addMenu("&Ansicht")
        self._menue_ansicht = m_ansicht
        m_ansicht.addAction(
            "Navigationsanzeigen",
            self._navigationsfenster_anzeigen)
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
        self._layer_settings = {}
        layer_einstellungen = (
            ("Schwerpunkt", LAYER_SCHWERPUNKT, True, None),
            ("Achsen", LAYER_HAUPTACHSEN, False, None),
            ("Kräfte", LAYER_KRAEFTE, True, None),
            ("Fremdkraft", LAYER_FREMDKRAFT, False, None),
            ("Momente", LAYER_MOMENTE, True, None),
            ("Hydrodynamik Rumpf", LAYER_HYDRO_RUMPF,
             self._einstellungen.get("anzeigen", "hydrodynamik_rumpf"),
             "hydrodynamik_rumpf"),
            ("Hydrodynamik Kiel/Schwert", LAYER_HYDRO_KIEL,
             self._einstellungen.get("anzeigen", "hydrodynamik_kiel"),
             "hydrodynamik_kiel"),
            ("Hydrodynamik Ruder", LAYER_HYDRO_RUDER,
             self._einstellungen.get("anzeigen", "hydrodynamik_ruder"),
             "hydrodynamik_ruder"),
        )
        self._layer_namen = tuple(
            (name, layer_name)
            for name, layer_name, _aktiviert, _einstellung
            in layer_einstellungen)
        for name, layer_name, aktiviert, einstellung in layer_einstellungen:
            cb = QCheckBox(name)
            cb.setChecked(aktiviert)
            self._layer_checks[name] = cb
            self._layer_settings[layer_name] = einstellung
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
                ("Geschwindigkeit", "-"),
                ("Normierte Restkraft", "-"),
                ("Normiertes Restmoment", "-"),
                ("Solver-Laufzeit", "-"),
                ("Dynamikprüfung", "-"),
                ("Iterationen", "-"), ("Bildrate", "-"),
                ("Zeitfaktor", "-"),
                ("Physik angefordert", "-"), ("Physik berechnet", "-"),
                ("Physik-Rückstand", "-"),
                ("Anzeigezeit", "-"), ("Anzeigeverzug", "-"),
                ("Darstellungszustand", "-"),
                ("Modellhinweis", "-"),
                ("Verfahren", "Keine zusätzliche v0.9-Schulungsnäherung freigegeben"),
                ("Lösungstyp", "-")):
            self._solver_werte[schluessel] = QTreeWidgetItem(
                status, [schluessel, wert])
        status.setRootIsDecorated(False)
        self._laufzeit_koerper = {}
        self._laufzeit_weltnamen = set()
        from .kraefte_werte import KraefteWerteFenster
        self._kraefte_werte = KraefteWerteFenster(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._kraefte_werte)
        self._kraefte_werte.setFloating(True)
        self._kraefte_werte.hide()
        self._kraefte_werte.auswahl_geaendert.connect(self._kraftauswahl_setzen)
        self._kraefte_werte.sichtbarkeit_geaendert.connect(
            self._kraftsichtbarkeit_setzen)
        self._kraefte_werte.neu_einpassen.connect(self._kraftanzeige_neu_einpassen)
        self._kraefte_werte.ansicht_geaendert.connect(self._kraftansicht_setzen)
        self._kraefte_werte.koerperumfang_geaendert.connect(self._kraftumfang_setzen)
        self._kraefte_werte.zuruecksetzen.connect(self._kraftanzeige_zuruecksetzen)
        self._kraftanzeige_koerperquellen = {}
        try:
            self._kraefte_werte.layout_anwenden(
                self._einstellungen.get("kraefteanzeige", "fensterlayout"))
        except ValueError as fehler:
            self._einstellungen.meldungen.append(str(fehler))
        self._menue_ansicht.addAction(self._kraefte_werte.toggleViewAction())
        self._stil_anwenden()

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
                ("Oben Backbord Bug", "oben_backbord_bug"),
                ("Oben Backbord Heck", "oben_backbord_heck"),
                ("Oben Steuerbord Bug", "oben_steuerbord_bug"),
                ("Oben Steuerbord Heck", "oben_steuerbord_heck"),
                ("Unten Backbord Bug", "unten_backbord_bug"),
                ("Unten Backbord Heck", "unten_backbord_heck"),
                ("Unten Steuerbord Bug", "unten_steuerbord_bug"),
                ("Unten Steuerbord Heck", "unten_steuerbord_heck"),
                ("Backbord (Seite)", "backbord"),
                ("Steuerbord (Seite)", "steuerbord"),
                ("Bug", "bug"),
                ("Heck", "heck"),
                ("Oben", "oben"),
                ("Unten", "unten")):
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
        self._ssao_check.setChecked(True)
        self._ssao_check.toggled.connect(self._ssao_geaendert)
        darstellung_layout.addWidget(self._ssao_check)
        self._schulungsdarstellung_check = QCheckBox(
            "Schulungs-Darstellung (reduzierte Optik)")
        self._schulungsdarstellung_check.setToolTip(
            "Ohne SSAO und Kantenglättung, reduzierte Wasseroptik. Alle Lernanzeigen "
            "und die exakte Physik bleiben unverändert.")
        self._schulungsdarstellung_check.setChecked(
            self._einstellungen.get("anzeigen", "schulungs_darstellung"))
        self._schulungsdarstellung_check.toggled.connect(
            self._schulungsdarstellung_geaendert)
        darstellung_layout.addWidget(self._schulungsdarstellung_check)
        darstellung_layout.addStretch(1)
        dock_darstellung = QDockWidget("Darstellung", self)
        dock_darstellung.setWidget(darstellung)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,
                           dock_darstellung)
        self.splitDockWidget(dock_layer, dock_darstellung,
                             Qt.Orientation.Vertical)

        fremd = QWidget()
        fremd_layout = QGridLayout(fremd)
        self._fremd_check = QCheckBox("Test-/Fremdkraft aktiv")
        self._fremd_check.setToolTip(
            "Körperbezogene Testprofile sind Kalibrierhilfen, keine "
            "realen Segelkräfte.")
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
        self._ruderwinkel_feld = QDoubleSpinBox()
        self._ruderwinkel_feld.setRange(-90.0, 90.0)
        self._ruderwinkel_feld.setValue(0.0)
        self._ruderwinkel_feld.setSingleStep(1.0)
        self._ruderwinkel_feld.setDecimals(1)
        self._ruderwinkel_feld.setSuffix("°")
        self._ruderwinkel_feld.valueChanged.connect(
            self._ruderwinkel_geaendert)
        fremd_layout.addWidget(QLabel("Ruderwinkel"), 7, 0)
        fremd_layout.addWidget(self._ruderwinkel_feld, 7, 1)
        fremd_layout.setRowStretch(8, 1)
        dock_fremd = QDockWidget("Testkraft / Fremdkraft", self)
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

    def _kraftansicht_abkoppeln(self):
        plotter_alt = getattr(self, "_kraft_frame_plotter", None)
        if plotter_alt is not None:
            plotter_alt.frameSwapped.disconnect(self._schulungsframe_fertig)
            self._kraft_frame_plotter = None
        filter_alt = getattr(self, "_kraftauswahl_filter", None)
        if filter_alt is not None:
            filter_alt.ansicht.removeEventFilter(filter_alt)
            filter_alt.deleteLater()
            self._kraftauswahl_filter = None

    def bruecke_setzen(self, bruecke):
        """Referenz auf die GrafikBruecke (G3-Kopplung der Docks)."""
        alt = getattr(self, "_bruecke", None)
        self._kraftansicht_abkoppeln()
        if alt is not bruecke and hasattr(alt, "kraefte_anzeige_beenden"):
            alt.kraefte_anzeige_beenden()
        self._bruecke = bruecke
        if isinstance(getattr(bruecke, "_plotter", None), QWidget):
            from .kraefte_auswahl import KraefteAuswahlFilter
            self._kraftauswahl_filter = KraefteAuswahlFilter(
                bruecke._plotter, bruecke, self._kraefte_werte)
        if (isinstance(getattr(bruecke, "_plotter", None), QWidget)
                and hasattr(bruecke._plotter, "frameSwapped")):
            bruecke._plotter.frameSwapped.connect(
                self._schulungsframe_fertig)
            self._kraft_frame_plotter = bruecke._plotter
        if self._navigationsfenster is None:
            from .navigationswidgets import NavigationsWidgetFenster
            self._navigationsfenster = NavigationsWidgetFenster(self)
            self._navigationsfenster.sichtbarkeit_setzen(
                self._einstellungen.bereich("anzeigen"))
            self._navigationsfenster.show()
            self._navigations_timer.start()
        for name, layer in self._layer_namen:
            bruecke.layer_setzen(layer, self._layer_checks[name].isChecked())
        self._stil_anwenden()
        self._darstellung_auf_bruecke_anwenden()
        self._laufzeit_objekte_aktualisieren("start")

    def _stil_anwenden(self):
        """Gibt den Pfeilstil aus den Einstellungen an die Bruecke."""
        bruecke = getattr(self, "_bruecke", None)
        from ..core.pfeilstil import Stil
        self._kraefte_werte.modell.stil_setzen(Stil(self._einstellungen.bereich))
        self._kraefte_werte.ansicht_setzen(
            self._einstellungen.bereich("kraefteanzeige"))
        if bruecke is None or not hasattr(bruecke, "stil_setzen"):
            return
        bruecke.stil_setzen(Stil(self._einstellungen.bereich))
        self._kraftsichtbarkeiten_abgleichen()
        self._kraftlegende_aktualisieren()

    def _kraftansicht_setzen(self, schluessel, wert):
        self._einstellungen.setzen("kraefteanzeige", schluessel, wert)
        self._stil_anwenden()

    def _kraftumfang_setzen(self, koerper_ids):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None and hasattr(bruecke, "kraefte_koerperumfang_setzen"):
            bruecke.kraefte_koerperumfang_setzen(koerper_ids)
        self._kraftsichtbarkeiten_abgleichen(neu_zeichnen=False)

    def _kraftanzeige_zuruecksetzen(self):
        from ..core import pfeilstil as ps
        layout = self._einstellungen.get("kraefteanzeige", "fensterlayout")
        for bereich in ("kraefteanzeige", *ps.standard_bereiche()):
            self._einstellungen.zuruecksetzen(bereich)
        self._einstellungen.setzen("kraefteanzeige", "fensterlayout", layout)
        for name, dialog in self._einstellungen_dialoge.items():
            if name.startswith("kp_"):
                dialog.neu_laden()
        bruecke = getattr(self, "_bruecke", None)
        zeichner = getattr(bruecke, "_kraefte_zeichner", None)
        if zeichner is not None and hasattr(zeichner, "sichtbar"):
            zeichner.sichtbar.clear()
            zeichner.skalen.clear()
            zeichner.skalen_parameter.clear()
        self._stil_anwenden()

    def _kraftsichtbarkeiten_abgleichen(self, bruecke=None, *, neu_zeichnen=True):
        from ..core.pfeilstil import Stil
        stil = Stil(self._einstellungen.bereich)
        gespeichert = self._einstellungen.get("kraefteanzeige", "sichtbarkeiten")
        sichtbar = {}
        for name, snapshot in self._kraftanzeige_snapshots.items():
            quelle = self._kraftanzeige_koerperquellen.get(name)
            for b in (*snapshot.beitraege, *snapshot.gruppen, snapshot.bilanz):
                sichtbar[b.instanz_id] = gespeichert.get(quelle, {}).get(
                    b.instanz_id[1], stil.beitragsstil(b, 1)["sichtbar"])
        self._kraefte_werte.modell.sichtbarkeiten_setzen(sichtbar)
        bruecke = bruecke or getattr(self, "_bruecke", None)
        zeichner = getattr(bruecke, "_kraefte_zeichner", None)
        if zeichner is not None and hasattr(zeichner, "sichtbar"):
            zeichner.sichtbar.update(sichtbar)
            if neu_zeichnen:
                bruecke.kraefte_neu_zeichnen()

    def _kraftanzeige_neu_einpassen(self):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None and hasattr(bruecke, "kraefte_neu_einpassen"):
            bruecke.kraefte_neu_einpassen()
            self._kraftlegende_aktualisieren()

    def _kraftlegende_aktualisieren(self):
        zeichner = getattr(getattr(self, "_bruecke", None), "_kraefte_zeichner", None)
        if zeichner is not None and hasattr(zeichner, "skalen"):
            from ..core.pfeilstil import Stil
            stil = Stil(self._einstellungen.bereich)
            hinweise = [
                "Werte schreibgeschuetzt; Ausblenden aendert keine Physik.",
                "Koerperbezogene Skalen; zum Vergleich gemeinsame manuelle "
                "Kraft-/Momentenreferenzen einstellen.",
                ("Vordergrund: durch Koerper sichtbar" if
                 stil.allgemein(1)["vordergrund"] else
                 "Raeumlich: verdeckte Pfeile bleiben im Wertefenster auswaehlbar.")]
            for name, snapshot in self._kraftanzeige_snapshots.items():
                for b in (*snapshot.beitraege, *snapshot.gruppen, snapshot.bilanz):
                    s = stil.bildschirmstil(stil.beitragsstil(b, 1), 1, 1)
                    if s["kraftfaktor"] != 1 or s["momentfaktor"] != 1:
                        hinweise.append(
                            f"{name} / {b.instanz_id[1]}: Anzeigefaktor "
                            f"F x{s['kraftfaktor']:.4g}, M x{s['momentfaktor']:.4g}")
            self._kraefte_werte.legende_setzen(zeichner.skalen, hinweise)

    def _kraftauswahl_setzen(self, instanz_id):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None and hasattr(bruecke, "kraefte_auswahl_setzen"):
            bruecke.kraefte_auswahl_setzen(instanz_id)

    def _kraftsichtbarkeit_setzen(self, instanz_id, sichtbar):
        quelle = self._kraftanzeige_koerperquellen.get(instanz_id[0])
        if quelle is not None:
            optionen = self._einstellungen.get("kraefteanzeige", "sichtbarkeiten")
            optionen.setdefault(quelle, {})[instanz_id[1]] = bool(sichtbar)
            self._einstellungen.setzen("kraefteanzeige", "sichtbarkeiten", optionen)
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None and hasattr(bruecke, "kraefte_sichtbarkeit_setzen"):
            bruecke.kraefte_sichtbarkeit_setzen(instanz_id, sichtbar)

    def _layer_setzen(self, layer, aktiviert):
        bruecke = getattr(self, "_bruecke", None)
        setting = self._layer_settings.get(layer)
        if setting is not None:
            self._einstellungen.setzen("anzeigen", setting, bool(aktiviert))
        if bruecke is None:
            return
        if (aktiviert and layer in (LAYER_KRAEFTE, LAYER_MOMENTE,
                                      LAYER_SCHWERPUNKT, LAYER_FREMDKRAFT,
                                      LAYER_HYDRO_RUMPF, LAYER_HYDRO_KIEL,
                                      LAYER_HYDRO_RUDER)
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
        self._wasserbewegung_aktivieren()
        if self._ssao_check.isChecked():
            self._ssao_geaendert(True)
        if self._schulungsdarstellung_check.isChecked():
            self._schulungsdarstellung_geaendert(True, persistieren=False)

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
            self._navigationsanzeigen_aktualisieren()

    def _navigationssichtbarkeit_aktualisieren(self):
        aktiv = self._einstellungen.get("anzeigen", "schulungs_darstellung")
        if aktiv != self._schulungsdarstellung_check.isChecked():
            self._schulungsdarstellung_check.blockSignals(True)
            self._schulungsdarstellung_check.setChecked(aktiv)
            self._schulungsdarstellung_check.blockSignals(False)
            self._schulungsdarstellung_geaendert(aktiv, persistieren=False)
        if self._navigationsfenster is not None:
            optionen = self._einstellungen.bereich("anzeigen")
            self._navigationsfenster.sichtbarkeit_setzen(optionen)

    def _navigationsfenster_anzeigen(self):
        if self._navigationsfenster is not None:
            self._navigationsfenster.show()
            self._navigationsfenster.raise_()
            self._navigationsfenster.activateWindow()

    def _navigationspose_ermitteln(self):
        bruecke = getattr(self, "_bruecke", None)
        welt = getattr(getattr(self, "baum", None), "_welt", None)
        if bruecke is None or welt is None:
            return None
        from .baum import summenkoerper
        sichtbare = [knoten for knoten in summenkoerper(welt)
                     if knoten.sichtbar]
        if self._btn_statisch.isChecked():
            knoten = next(iter(sichtbare), None)
            name = knoten.name if knoten is not None else None
            ergebnis = self._statische_ergebnisse.get(name)
            koerper = self._laufzeit_koerper.get(name)
            if koerper is None:
                return None
            from ..core.dynamik_6dof import (
                Zustand6DOF, quaternion_aus_matrix)
            if ergebnis is not None:
                phi = float(ergebnis["phi"])
                c, s = math.cos(phi), math.sin(phi)
                rotation = np.array((
                    (1.0, 0.0, 0.0),
                    (0.0, c, -s),
                    (0.0, s, c),
                ))
                basis = bruecke.physik_basis_position_ermitteln(name)
                pose = Zustand6DOF(
                    position=(float(basis[0]), float(basis[1]),
                              float(ergebnis["z"])),
                    quaternion=quaternion_aus_matrix(rotation))
            elif koerper.zustand is not None:
                pose = koerper.zustand
            else:
                rotation = koerper.orientierung
                pose = Zustand6DOF(
                    position=tuple(float(w) for w in koerper.position),
                    quaternion=quaternion_aus_matrix(rotation))
        else:
            name = self._echtzeit_name
            if name is None:
                knoten = next(iter(sichtbare), None)
                name = knoten.name if knoten is not None else None
            koerper = self._laufzeit_koerper.get(name)
            pose = self._echtzeit_zustand
            if pose is None and koerper is not None:
                pose = koerper.zustand
                if pose is None:
                    from ..core.dynamik_6dof import (
                        Zustand6DOF, quaternion_aus_matrix)
                    pose = Zustand6DOF(
                        position=tuple(float(w) for w in koerper.position),
                        quaternion=quaternion_aus_matrix(
                            koerper.orientierung))
        if name is None or pose is None:
            return None
        return name, pose

    def _navigationsanzeigen_aktualisieren(self):
        fenster = self._navigationsfenster
        bruecke = getattr(self, "_bruecke", None)
        if fenster is None:
            return
        if bruecke is None:
            return
        auswahl = self._navigationspose_ermitteln()
        if auswahl is None:
            from ..core.navigationsanzeigen import Navigationswerte
            fenster.aktualisieren(
                Navigationswerte(None, None, None, None, None, None),
                self._einstellungen.bereich("anzeigen"), None)
            return
        name, pose = auswahl
        from ..core.navigationsanzeigen import navigationswerte_ableiten
        vorlaeufig = navigationswerte_ableiten(pose.quaternion)
        offset, elevation = bruecke.navigationskamera_aktualisieren(
            name, pose.position,
            (None if vorlaeufig.heading_grad is None
             else math.radians(vorlaeufig.heading_grad)))
        werte = navigationswerte_ableiten(
            pose.quaternion, offset, elevation,
            self._segelwinkel_ermitteln(name))
        geschwindigkeit = float(np.linalg.norm(
            np.asarray(pose.geschwindigkeit_koerper, dtype=float)))
        fenster.aktualisieren(
            werte, self._einstellungen.bereich("anzeigen"),
            geschwindigkeit, verzoegert=self._echtzeit_timer.isActive())

    def _segelwinkel_ermitteln(self, koerper_name):
        knoten = getattr(self, "baum", None)
        welt = getattr(knoten, "_welt", None)
        if welt is None:
            return None
        from .baum import summenkoerper
        koerper = next(
            (k for k in summenkoerper(welt)
             if k.name == koerper_name), None)
        if koerper is None:
            return None
        werte = []

        def sammeln(k):
            if (getattr(k, "rolle", None) == "segel"
                    and getattr(k, "gelenkdefinition", None) is not None
                    and k.gelenkwinkel_rad is not None):
                werte.append(float(k.gelenkwinkel_rad))
            for kind, _pose in getattr(k, "teile", ()):
                sammeln(kind)

        sammeln(koerper)
        return werte[0] if len(werte) == 1 else None

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

    def _schulungsdarstellung_geaendert(self, aktiviert, persistieren=True):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            if persistieren:
                self._einstellungen.setzen(
                    "anzeigen", "schulungs_darstellung", bool(aktiviert))
            return
        if aktiviert:
            if not hasattr(self, "_schulungsdarstellung_vorher"):
                self._schulungsdarstellung_vorher = (
                    self._ssao_check.isChecked(),
                    self._wasseroptik_check.isChecked(),
                    bruecke._plotter.render_window.GetMultiSamples())
            ssao, wasseroptik, samples = False, False, 0
        else:
            ssao, wasseroptik, samples = self._schulungsdarstellung_vorher
        for check, wert in (
            (self._ssao_check, ssao), (self._wasseroptik_check, wasseroptik),
        ):
            check.setEnabled(not aktiviert)
            check.setChecked(wert)
        self._ssao_geaendert(ssao)
        self._wasseroptik_geaendert(wasseroptik)
        self._darstellung_aktion(
            "Kantenglättung", lambda: bruecke.kantenglaettung_setzen(samples))
        self._echtzeit_render_timer.setInterval(20 if aktiviert else 33)
        if not aktiviert:
            del self._schulungsdarstellung_vorher
        if persistieren:
            self._einstellungen.setzen(
                "anzeigen", "schulungs_darstellung", bool(aktiviert))
        self.protokoll_schreiben(
            "Schulungs-Darstellung aktiv: reduzierte Optik, unveränderte "
            "Physik und Lernanzeigen." if aktiviert else
            "Standarddarstellung wiederhergestellt.")

    def _schulungsframe_fertig(self):
        if (self._schulungsdarstellung_check.isChecked()
                and self._echtzeit_render_timer.isActive()):
            QTimer.singleShot(0, self._echtzeit_render_takt)

    def _wasserbewegung_aktivieren(self):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None:
            self._darstellung_aktion(
                "Wasserbewegung", lambda: bruecke.wasser_bewegung_setzen())

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
        from ..core.fabriken import _ist_repo_konfig
        if (_ist_repo_konfig(konfiguration)
                and getattr(konfiguration, "paketfabrik_aktiv", True)):
            return True

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

    def _hydrodynamik_testprofil_laden(self, koerper_name):
        from ..core.hydrodynamik import hydrodynamik_testprofil

        welt = getattr(getattr(self, "baum", None), "_welt", None)
        konfiguration = getattr(welt, "konfiguration", None)
        profile = getattr(konfiguration, "hydrodynamik_profile", {})
        profil_konfig = profile.get(koerper_name)
        profil = (None if koerper_name is None
                  else hydrodynamik_testprofil(
                      koerper_name, profil_konfig))
        werte = {
            "betrag": 0.0 if profil is None else profil.kraft_betrag_N,
            "azimut": 0.0 if profil is None else profil.azimut_grad,
            "elevation": 0.0 if profil is None else profil.elevation_grad,
            "x": 0.0 if profil is None else profil.angriffspunkt_m[0],
            "y": 0.0 if profil is None else profil.angriffspunkt_m[1],
            "z": 0.0 if profil is None else profil.angriffspunkt_m[2],
        }
        widgets = [self._fremd_check, self._ruderwinkel_feld]
        widgets.extend(self._fremd_felder.values())
        blockers = [QSignalBlocker(widget) for widget in widgets]
        self._fremd_check.setChecked(profil is not None)
        for schluessel, wert in werte.items():
            self._fremd_felder[schluessel].setValue(wert)
        self._ruderwinkel_feld.setValue(
            0.0 if profil is None else profil.ruderwinkel_grad)
        del blockers

    def _hydrodynamik_profil_auswahl_setzen(self, koerper_name):
        if koerper_name == self._hydrodynamik_profil_koerper:
            return
        profil_name = koerper_name
        if koerper_name is not None:
            welt = getattr(getattr(self, "baum", None), "_welt", None)
            konfiguration = getattr(welt, "konfiguration", None)
            profile = getattr(
                konfiguration, "hydrodynamik_profile", {})
            koerper = self._laufzeit_koerper.get(koerper_name)
            snapshot_erzeugen = getattr(koerper, "snapshot", None)
            snapshot = (
                snapshot_erzeugen() if callable(snapshot_erzeugen) else None)
            hydrodynamik_teile = getattr(
                snapshot, "hydrodynamik_teile", ())
            if koerper_name in profile:
                modell = profile[koerper_name]["modell"]
                if modell == "generischer_volumenkoerper":
                    unterstuetzt = bool(
                        snapshot is not None
                        and getattr(snapshot, "blatt_meshes", ()))
                else:
                    unterstuetzt = any(
                        rolle in ("rumpf", "kiel", "ruder")
                        for rolle, _name, _punkte, _faces
                        in hydrodynamik_teile)
            else:
                unterstuetzt = any(
                    rolle in ("rumpf", "kiel", "ruder")
                    for rolle, _name, _punkte, _faces
                    in hydrodynamik_teile)
            if not unterstuetzt:
                profil_name = None
        self._hydrodynamik_testprofil_laden(profil_name)
        self._hydrodynamik_profil_koerper = koerper_name

    def _laufzeit_objekte_aktualisieren(self, grund="auswahl"):
        self._statisch_generation += 1
        self._kraftanzeige_verwerfen("Koerperdaten werden aktualisiert")
        bruecke = getattr(self, "_bruecke", None)
        welt = self.baum._welt
        konfiguration = getattr(welt, "konfiguration", None)
        if bruecke is None or konfiguration is None:
            return

        from ..core.fabriken import baue_summenkoerper
        from .baum import aktive_blaetter, summenkoerper

        hauptkoerper = tuple(summenkoerper(welt))
        vorhandene_namen = {knoten.name for knoten in hauptkoerper}
        entfernte_namen = (
            self._laufzeit_weltnamen | self._laufzeit_koerper.keys()) - vorhandene_namen
        self._laufzeit_weltnamen = vorhandene_namen
        for name in entfernte_namen:
            bruecke.koerper_entfernen(name)
            self._laufzeit_koerper.pop(name, None)
            self._laufzeit_schwerpunkt.pop(name, None)
            self._statische_ergebnisse.pop(name, None)
            self._statische_arbeitsdaten.pop(name, None)
            self._statische_aufgaben_ausstehend.pop(name, None)
            self._kraftanzeige_koerperquellen.pop(name, None)
        laufzeit_bereit = True
        schwerpunkt_alt = {}
        for knoten in hauptkoerper:
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
        self._kraefte_werte.koerper_setzen(self._laufzeit_koerper)
        if laufzeit_bereit:
            auswahl = next(
                (knoten for knoten in summenkoerper(welt)
                 if knoten.sichtbar), None)
            koerper_name = None if auswahl is None else auswahl.name
            modellhinweis = next(
                (text for label, text in auswahl.eigenschaften
                 if label == "Modellhinweis"), "") if auswahl else ""
            hinweis = (
                "Schulungstool – kein Engineering-/Sicherheitsnachweis "
                "und kein Race-Optimizer."
                + (" " + modellhinweis if modellhinweis else ""))
            self._solver_werte["Modellhinweis"].setToolTip(1, hinweis)
            self._solver_status_aktualisieren({"Modellhinweis": hinweis})
            self._hydrodynamik_profil_auswahl_setzen(koerper_name)
        if not laufzeit_bereit:
            self._zeit_pausieren()
            self._echtzeit_name = None
            return
        if self._btn_statisch.isChecked():
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

    def _statusoverlay(self, anzeige):
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            return
        setzen = getattr(bruecke, "statusoverlay_setzen", None)
        if setzen is None:
            return
        text, schwere = anzeige if anzeige else (None, "info")
        setzen(text, schwere)

    def _modus_geaendert(self, _knopf):
        statisch = self._btn_statisch.isChecked()
        self._steuerzeile_umschalten(statisch)
        if statisch:
            self._statisch_generation += 1
            self._zeit_pausieren()
            self._solver_status_aktualisieren({
                "Anzeigezeit": "-", "Anzeigeverzug": "-",
                "Darstellungszustand": "Statische Ansicht",
            })
            self._echtzeit_name = None
            self._statische_simulation_ausfuehren()
        else:
            self._statisch_generation += 1
            self._statische_aufgaben_ausstehend.clear()
            self._statusoverlay(None)
            self._wasserpunkte_fuer_modus(False)
            bruecke = getattr(self, "_bruecke", None)
            if bruecke is not None:
                for name in self._laufzeit_koerper:
                    bruecke.statische_pose_loeschen(name)
            self._echtzeit_starten()

    def _wasserpunkte_fuer_modus(self, statisch):
        bruecke = getattr(self, "_bruecke", None)
        setzen = getattr(bruecke, "wasserpunkte_sichtbar_setzen", None)
        if setzen is not None:
            setzen(not statisch)

    def _statische_simulation_ausfuehren(self):
        self._statisch_generation += 1
        self._statische_aufgaben_ausstehend.clear()
        self._kraftanzeige_verwerfen("Statische Berechnung laeuft")
        generation = self._statisch_generation
        fremdkraft = self._fremdkraft_aktuell()
        self._statische_fremdkraft = fremdkraft
        self._wasserpunkte_fuer_modus(True)
        welt = self.baum._welt
        konfiguration = getattr(welt, "konfiguration", None)
        if konfiguration is None:
            return
        from .baum import summenkoerper
        sichtbare = [knoten for knoten in summenkoerper(welt) if knoten.sichtbar]
        if not sichtbare:
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Kein Hauptkörper ausgewählt"})
            self._statusoverlay(statusanzeige.KEIN_HAUPTKOERPER)
            return
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            self._statusoverlay(statusanzeige.KOERPER_FEHLT)
            return

        self._solver_status_aktualisieren(
            {"Lösungstyp": "Statische Berechnung läuft"})
        self._statusoverlay(statusanzeige.BERECHNUNG_LAEUFT)
        for knoten in sichtbare:
            koerper = self._laufzeit_koerper.get(knoten.name)
            if koerper is None:
                self.protokoll_schreiben(
                    "Statischer Solver (%s): Laufzeitkoerper fehlt" % knoten.name)
                self._statusoverlay(statusanzeige.KOERPER_FEHLT)
                continue
            aufgabe = _StatischeAufgabe(
                generation, knoten.name, koerper,
                konfiguration.ordner, konfiguration.wasser_dichte(),
                self._statisch_signale,
                self._einstellungen.bereich("statisch"),
                fremdkraft=fremdkraft,
                ruderwinkel_rad=math.radians(
                    self._ruderwinkel_feld.value()))
            self._statische_aufgabe_starten(aufgabe)

    def _statische_aufgabe_starten(self, aufgabe):
        self._statische_aufgaben_ausstehend[aufgabe.name] = aufgabe
        self._statische_folgeaufgaben_starten()

    def _statische_folgeaufgaben_starten(self):
        if not self._btn_statisch.isChecked():
            self._statische_aufgaben_ausstehend.clear()
            return
        pool = QThreadPool.globalInstance()
        for name, aufgabe in tuple(self._statische_aufgaben_ausstehend.items()):
            if aufgabe.generation != self._statisch_generation:
                self._statische_aufgaben_ausstehend.pop(name)
                continue
            if name in self._statische_aufgaben:
                continue
            if len(self._statische_aufgaben) >= max(1, pool.maxThreadCount()):
                break
            self._statische_aufgaben_ausstehend.pop(name)
            self._statische_aufgaben[name] = aufgabe.generation
            pool.start(aufgabe)

    def _statische_aufgabe_fortschritt(self, generation, name, stufe):
        if (generation != self._statisch_generation
                or not self._btn_statisch.isChecked()):
            return
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            return
        restkraft = float(np.linalg.norm(stufe.restkraft_N))
        restmoment = float(np.linalg.norm(stufe.restmoment_Nm))
        self._solver_status_aktualisieren({
            "Geschwindigkeit": "%.3f m/s" % float(np.linalg.norm(
                stufe.geschwindigkeit_m_s)),
            "Restkraft": "%.3g N" % restkraft,
            "Restmoment": "%.3g N·m" % restmoment,
            "Normierte Restkraft": "%.3g" % stufe.normierte_restkraft,
            "Normiertes Restmoment": "%.3g" % stufe.normiertes_restmoment,
            "Solver-Laufzeit": "läuft …",
            "Iterationen": str(stufe.iterationen),
            "Lösungstyp": (
                "Vorläufig: %s" % stufe.name if stufe.konvergiert
                else "Nicht konvergiert: %s" % stufe.name),
        })
        if stufe.konvergiert:
            R = _stationaere_rotation(stufe)
            position = bruecke.physik_basis_position_ermitteln(name)
            position[2] = float(stufe.pose[2])
            bruecke.physik_pose_6dof_setzen(name, R, position)
            self._statusoverlay(
                ("Vorläufiges hydrodynamisches Teilgleichgewicht: "
                 + stufe.name, "info"))

    def _statische_aufgabe_abgeschlossen(
            self, generation, name, ergebnis, arbeitsdaten, fehler):
        if self._statische_aufgaben.get(name) == generation:
            self._statische_aufgaben.pop(name)
            self._statische_folgeaufgaben_starten()
        if fehler is not None and (
                generation != self._statisch_generation
                or not self._btn_statisch.isChecked()):
            self.protokoll_schreiben(
                "Veralteter statischer Auftrag (%s, Generation %s): %s"
                % (name, generation, fehler))
        if (generation != self._statisch_generation
                or not self._btn_statisch.isChecked()):
            return
        bruecke = getattr(self, "_bruecke", None)
        koerper = self._laufzeit_koerper.get(name)
        if bruecke is None or koerper is None:
            return
        if fehler is not None:
            from ..core.statisch import SolverFehler

            status = "Fehler: %s" % fehler
            werte = {
                "z*": "-", "phi*": "-", "GM": "-",
                "Restkraft": "-", "Restmoment": "-",
                "Lösungstyp": status,
            }
            kandidat_abgelehnt = False
            if isinstance(fehler, SolverFehler):
                diagnose = fehler.diagnose
                statusnamen = {
                    "instabile_lage": "Instabile Lage",
                    "stagnation": "Stagnation",
                    "budget_erschoepft": "Budget erschöpft",
                    "ungueltige_rechenergebnisse":
                        "Ungültige Rechenergebnisse",
                    "sinkt": "Sinken",
                    "schwebt": "Schweben",
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
                if kandidat:
                    kandidat_abgelehnt = True
                    werte["Lösungstyp"] = (
                        "Kandidat nicht übernommen – %s"
                        % werte["Lösungstyp"])
            self._solver_status_aktualisieren(werte)
            self._statusoverlay(
                statusanzeige.status_aus_fehler(
                    fehler, kandidat_abgelehnt=kandidat_abgelehnt))
            self.protokoll_schreiben(
                "Statischer Solver (%s): %s" % (name, fehler))
            return

        kraftfunktion, physik = arbeitsdaten
        stationaer = ergebnis.get("stationaer_hydrodynamik")
        stufe = None
        if stationaer is not None and stationaer.stufen:
            stufe = next(
                (teil for teil in reversed(stationaer.stufen)
                 if teil.konvergiert),
                None)
        if stufe is not None:
            pose, v, omega, rotation = _stationaere_kraftlage(stufe)
            position = bruecke.physik_basis_position_ermitteln(name)
            position[2] = float(stufe.pose[2])
            if not bruecke.physik_pose_6dof_setzen(
                    name, rotation, position):
                self._solver_status_aktualisieren(
                    {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
                self._statusoverlay(statusanzeige.KOERPER_FEHLT)
                return
            kraft_ergebnis = ergebnis.get("kraft_ergebnis")
            self._kraftbild_daten_setzen(
                bruecke, name, koerper, kraftfunktion, physik,
                stufe.pose[2], stufe.pose[3], ergebnis=kraft_ergebnis,
                solverdiagnose=ergebnis.get("kraft_solver"))
            ergebnis["z"], ergebnis["phi"] = (
                float(stufe.pose[2]), float(stufe.pose[3]))
        else:
            self._kraftbild_daten_setzen(
                bruecke, name, koerper, kraftfunktion, physik,
                ergebnis["z"], ergebnis["phi"],
                ergebnis=ergebnis.get("kraft_ergebnis"),
                solverdiagnose=ergebnis.get("kraft_solver"))
            if not bruecke.statische_pose_setzen(
                    name, ergebnis["z"], ergebnis["phi"]):
                self._solver_status_aktualisieren(
                    {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
                self._statusoverlay(statusanzeige.KOERPER_FEHLT)
                return
        self._statische_ergebnisse[name] = ergebnis
        self._statische_arbeitsdaten[name] = (kraftfunktion, physik)
        self._navigationsanzeigen_aktualisieren()
        self._statusoverlay(statusanzeige.status_aus_ergebnis(
            ergebnis, form=formerkennung.klassifiziere_koerper(koerper)))
        gm = ergebnis["gm"]
        werte = {
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
        }
        if stationaer is not None:
            dynamik = ergebnis.get("stationaer_dynamikpruefung")
            dynamik_bestanden = (
                stationaer.konvergiert and dynamik is not None
                and dynamik.bestanden)
            restkraft = (
                "-" if stufe is None
                else "%.3g N" % np.linalg.norm(stufe.restkraft_N))
            restmoment = (
                "-" if stufe is None
                else "%.3g N·m" % np.linalg.norm(stufe.restmoment_Nm))
            if dynamik is None:
                dynamik_text = (
                    "Nicht ausgeführt: Solver nicht konvergiert"
                    if not stationaer.konvergiert
                    else "Nicht ausgeführt: kein Prüfergebnis")
            else:
                fehlergrund = getattr(dynamik, "fehlergrund", None)
                dynamik_text = (
                    "%s; Δu=%.3g%%; ΔWinkel=%.3g°; |ω|=%.3g rad/s%s"
                    % ("Bestanden" if dynamik_bestanden
                       else "Nicht bestanden",
                       100.0 * dynamik.relative_vorwaertsabweichung,
                       math.degrees(dynamik.orientierung_ende_rad),
                       dynamik.winkelgeschwindigkeit_ende_rad_s,
                       "; " + fehlergrund if fehlergrund else ""))
            werte.update({
                "Geschwindigkeit": (
                    "-" if stufe is None else "%.3f m/s" % float(
                        np.linalg.norm(stufe.geschwindigkeit_m_s))),
                "Restkraft": restkraft,
                "Restmoment": restmoment,
                "Normierte Restkraft": (
                    "-" if stufe is None
                    else "%.3g" % stufe.normierte_restkraft),
                "Normiertes Restmoment": (
                    "-" if stufe is None
                    else "%.3g" % stufe.normiertes_restmoment),
                "Solver-Laufzeit": "%.3f s" % stationaer.laufzeit_s,
                "Iterationen": str(sum(
                    teil.iterationen for teil in stationaer.stufen)),
                "Lösungstyp": (
                    ("Hydrodynamisch stationär (konvergiert)"
                     if dynamik_bestanden else
                     "Hydrodynamisch stationär; Dynamikprüfung "
                     "nicht bestanden")
                    if stationaer.konvergiert else
                    "Hydrodynamisch nicht vollständig konvergiert"),
                "Dynamikprüfung": dynamik_text,
            })
            if not stationaer.konvergiert:
                hinweis = ergebnis.get("stationaer_fehler", "")
                text = ("Hydrodynamischer Solver nicht konvergiert; "
                        "letzter gültiger Teilzustand bleibt sichtbar")
                if hinweis:
                    text += ": " + hinweis
                self._statusoverlay((text, "problem"))
            else:
                status = (
                    "Stationäres Gleichgewicht und 10-s-Dynamikprüfung "
                    + ("bestanden" if dynamik_bestanden
                       else "nicht bestanden"))
                fehlergrund = (
                    None if dynamik is None
                    else getattr(dynamik, "fehlergrund", None))
                if fehlergrund:
                    status += ": " + fehlergrund
                self._statusoverlay((
                    status, "ok" if dynamik_bestanden else "problem"))
        self._solver_status_aktualisieren(werte)

    def _echtzeit_starten(self, zustand=None, auto_start=True):
        if (self._echtzeit_timer.isActive()
                or self._echtzeit_render_timer.isActive()
                or self._echtzeit_schritte_laufend):
            self._zeit_pausieren()
        self._echtzeit_generation += 1
        self._kraftanzeige_verwerfen("Dynamische Initialisierung laeuft")
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
        self._hydrodynamik_profil_auswahl_setzen(hauptkoerper.name)
        koerper = self._laufzeit_koerper.get(hauptkoerper.name)
        if koerper is None:
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Kein Laufzeitkörper verfügbar"})
            return

        koerper_snapshot = koerper.snapshot()
        from ..core.auftrieb import baue_kraftfunktion_6dof
        from ..core.dynamik_6dof import Zustand6DOF, quaternion_matrix
        from ..core.konfig_lader import lade_physik
        from ..core.kraftmodell import (
            KraftmodellMitHydroCache, baue_kraftmodell)
        try:
            physik = lade_physik(konfiguration.ordner)
            from ..core.hydrodynamik import (
                HydrodynamikModell,
                hydrodynamik_testprofil,
            )
            profil_konfig = konfiguration.hydrodynamik_profile.get(
                hauptkoerper.name)
            profil = hydrodynamik_testprofil(
                hauptkoerper.name, profil_konfig)
            cd_volumenkoerper = (
                profil.cd_volumenkoerper
                if profil is not None
                and profil.modell == "generischer_volumenkoerper"
                else None)
            hydrodynamik = HydrodynamikModell.aus_koerper(
                koerper_snapshot, rho_kg_m3=konfiguration.wasser_dichte(),
                cd_volumenkoerper=cd_volumenkoerper,
                fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
                fluidwinkelgeschwindigkeit=(
                    physik.fluidwinkelgeschwindigkeit),
                ruderwinkel_rad=math.radians(
                    self._ruderwinkel_feld.value()))
            self._ruderwinkel_feld.setEnabled(
                hydrodynamik is not None and any(
                    teil.rolle == "ruder" for teil in hydrodynamik.teile))
            kraftfunktion = baue_kraftfunktion_6dof(
                koerper_snapshot, rho_w=konfiguration.wasser_dichte(),
                g=physik.g_m_pro_s2,
                pfad=_ECHTZEIT_HYDROSTATIK_PFAD)
            kraftfunktion = KraftmodellMitHydroCache(
                baue_kraftmodell(
                    kraftfunktion, physik, masse=koerper_snapshot.masse,
                    g=physik.g_m_pro_s2, hydrodynamik=hydrodynamik),
                intervall=1)
            kraftfunktion.fremdkraft_setzen(self._fremdkraft_aktuell())
            basisposition = bruecke.physik_basis_position_ermitteln(
                hauptkoerper.name)
            prozess_executor = self._echtzeit_prozess_pool_aktualisieren(
                koerper_snapshot, konfiguration.wasser_dichte(), physik,
                _ECHTZEIT_HYDROSTATIK_PFAD,
                cd_volumenkoerper=cd_volumenkoerper)
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
        try:
            koerper.zustand = zustand
        except ValueError as fehler:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: ungültiger Körperzustand"})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): %s"
                % (hauptkoerper.name, fehler))
            return
        zustand = koerper.zustand
        self._echtzeit_zustand = zustand
        self._echtzeit_anzeige_verlauf = [
            (self._echtzeit_berechnet_s, zustand)]
        self._echtzeit_anzeigezeit_s = self._echtzeit_berechnet_s
        self._echtzeit_anzeige_wandzeit = None
        self._echtzeit_anzeige_verzoegerung_s = min(
            _ECHTZEIT_ANZEIGE_PUFFER_MAX_S,
            physik.dt_s * self._dyn("max_schritte_pro_aufgabe"))
        self._echtzeit_physik = physik
        self._echtzeit_kraftfunktion = kraftfunktion
        self._echtzeit_koerper_version = koerper_snapshot.version
        self._echtzeit_aktiver_prozess_executor = prozess_executor
        self._echtzeit_kraefteresultat = None
        self._aktuelles_kraftbild_aktualisieren()
        if not self._echtzeit_pose_anzeigen(zustand, render=True):
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Körper in 3D-Ansicht fehlt"})
            return
        self._navigationsanzeigen_aktualisieren()
        self._solver_status_aktualisieren({"Lösungstyp": "Echtzeit"})
        if auto_start:
            self._zeit_fortsetzen()

    def _echtzeit_prozess_pool_aktualisieren(
            self, koerper, rho_w, physik, hydrostatik_pfad,
            cd_volumenkoerper=None):
        if (not hasattr(koerper, "blatt_meshes")
                or QApplication.platformName().casefold()
                in ("offscreen", "minimal")):
            return None
        if (self._echtzeit_prozess_executor is not None
                and self._echtzeit_prozess_koerper is koerper
                and self._echtzeit_prozess_pfad == hydrostatik_pfad
                and self._echtzeit_prozess_cd == cd_volumenkoerper):
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
            initargs=(koerper, rho_w, physik, hydrostatik_pfad,
                      cd_volumenkoerper))
        self._echtzeit_prozess_executor = executor
        self._echtzeit_prozess_koerper = koerper
        self._echtzeit_prozess_pfad = hydrostatik_pfad
        self._echtzeit_prozess_cd = cd_volumenkoerper
        return executor

    def _zeit_pausieren(self):
        war_laufend = self._echtzeit_timer.isActive()
        jetzt = time.perf_counter()
        if (self._echtzeit_letzte_wandzeit is not None
                and self._echtzeit_modus in (
                    "normal", "ueberlast_beobachtung")):
            vergangen = max(
                0.0, jetzt - self._echtzeit_letzte_wandzeit)
            self._echtzeit_akkumulator += vergangen
            self._echtzeit_angefordert_s += vergangen
        if (self._echtzeit_aufgabe_laeuft
                and self._echtzeit_schritte_laufend == 0
                and self._echtzeit_kraefteresultat is None):
            self._echtzeit_kraftauswertung_ausstehend = True
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
        self._echtzeit_anzeige_wandzeit = None
        self._echtzeit_anzeigezeit_s = self._echtzeit_berechnet_s
        self._echtzeit_modus = "pausiert"
        self._zeittasten_setzen(False)
        if self._echtzeit_zustand is not None:
            self._echtzeit_anzeige_verlauf = [
                (self._echtzeit_berechnet_s, self._echtzeit_zustand)]
        if war_laufend:
            self._kraefte_werte.ausstehende_werte_anzeigen()
            self._navigationsanzeigen_aktualisieren()
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
        self._echtzeit_anzeige_wandzeit = jetzt
        self._echtzeit_fps_start = jetzt
        self._echtzeit_zf_berechnet = self._echtzeit_berechnet_s
        self._echtzeit_fps_zaehler = 0
        self._echtzeit_modus = "normal"
        if self._echtzeit_rueckstand_s() >= self._dyn(
                "ueberlast_rueckstand_s"):
            self._echtzeit_modus = "ueberlast_beobachtung"
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
        einschraenkungen = []
        if self._echtzeit_rueckstand_s() >= self._dyn("ueberlast_rueckstand_s"):
            einschraenkungen.append("Physikrückstand")
        if 0 < self._echtzeit_angeforderte_fps < 30:
            einschraenkungen.append("Renderaufrufrate unter 30/s")
        return {
            "Physik angefordert": "%.3f s" % self._echtzeit_angefordert_s,
            "Physik berechnet": "%.3f s" % self._echtzeit_berechnet_s,
            "Physik-Rückstand": self._rueckstand_text(),
            "Anzeigezeit": "%.3f s" % self._echtzeit_anzeigezeit_s,
            "Anzeigeverzug": "%.3f s" % max(
                0.0, self._echtzeit_angefordert_s - self._echtzeit_anzeigezeit_s),
            "Darstellungszustand": (
                "Eingeschränkt: " + ", ".join(einschraenkungen)
                if einschraenkungen else "Gepufferte Anzeige"),
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
        if (self._schulungsdarstellung_check.isChecked()
                and getattr(getattr(self, "_bruecke", None),
                            "_render_ausstehend", False)):
            return
        verlauf = self._echtzeit_anzeige_verlauf
        if not verlauf:
            return
        jetzt = time.perf_counter()
        vergangen = (
            0.0 if self._echtzeit_anzeige_wandzeit is None else
            max(0.0, jetzt - self._echtzeit_anzeige_wandzeit))
        self._echtzeit_anzeige_wandzeit = jetzt
        from ..core.dynamik_6dof import anzeige_interpolieren
        zielzeit, index, pose = anzeige_interpolieren(
            verlauf, self._echtzeit_anzeigezeit_s, vergangen,
            self._echtzeit_anzeige_verzoegerung_s)
        self._echtzeit_anzeigezeit_s = zielzeit
        self._echtzeit_anzeige_verlauf = verlauf[index:]
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
                "Bildrate": "%.1f Render/s" % self._echtzeit_angeforderte_fps,
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
        self._echtzeit_akkumulator += vergangen
        self._echtzeit_angefordert_s += vergangen
        self._echtzeit_letzte_wandzeit = jetzt
        rueckstand = self._echtzeit_rueckstand_s()
        if rueckstand >= self._dyn("ueberlast_rueckstand_s"):
            self._echtzeit_modus = "ueberlast_beobachtung"
        else:
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
        if self._echtzeit_kraftauswertung_ausstehend:
            self._aktuelles_kraftbild_aktualisieren()
            return
        anzahl_schritte = min(
            int((self._echtzeit_akkumulator + 1e-12) / dt),
            (self._dyn("max_schritte_nachholen")
             if self._echtzeit_modus == "ueberlast_beobachtung"
             else self._dyn("max_schritte_pro_aufgabe")))
        if anzahl_schritte == 0:
            return
        self._echtzeit_anzeige_verzoegerung_s = min(
            _ECHTZEIT_ANZEIGE_PUFFER_MAX_S,
            max(self._echtzeit_anzeige_verzoegerung_s,
                anzahl_schritte * dt))
        self._echtzeit_akkumulator -= anzahl_schritte * dt
        koerper = self._laufzeit_koerper.get(self._echtzeit_name)
        if koerper is None:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: Laufzeitkörper fehlt"})
            return
        zustand = koerper.zustand
        if zustand is None:
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: Körperzustand fehlt"})
            return
        self._echtzeit_auftragssequenz += 1
        sequenz = self._echtzeit_auftragssequenz
        aufgabe = _EchtzeitAufgabe(
            self._echtzeit_generation, sequenz, self._echtzeit_name,
            zustand,
            self._echtzeit_kraftfunktion, koerper, self._echtzeit_physik,
            dt, anzahl_schritte, self._echtzeit_signale,
            prozess_executor=self._echtzeit_aktiver_prozess_executor,
            fremdkraft=self._fremdkraft_aktuell(),
            ruderwinkel_rad=math.radians(self._ruderwinkel_feld.value()))
        self._echtzeit_aufgabe_laeuft = True
        self._echtzeit_aufgabe_sequenz_laufend = sequenz
        self._echtzeit_schritte_laufend = anzahl_schritte
        QThreadPool.globalInstance().start(aufgabe)

    def _echtzeit_aufgabe_abgeschlossen(
            self, generation, sequenz, koerper_name, zustand,
            kraefteresultat, fehler, _dauer_s):
        if fehler is not None and (
                sequenz != self._echtzeit_aufgabe_sequenz_laufend
                or generation != self._echtzeit_generation):
            self.protokoll_schreiben(
                "Veralteter Echtzeitauftrag (%s, Generation %s, Sequenz %s): %s"
                % (koerper_name, generation, sequenz, fehler))
        if sequenz != self._echtzeit_aufgabe_sequenz_laufend:
            return
        self._echtzeit_aufgabe_laeuft = False
        self._echtzeit_aufgabe_sequenz_laufend = None
        anzahl_schritte = self._echtzeit_schritte_laufend
        self._echtzeit_schritte_laufend = 0
        if (generation != self._echtzeit_generation
                or koerper_name != self._echtzeit_name
                or not self._btn_echtzeit.isChecked()):
            if self._echtzeit_kraftauswertung_ausstehend:
                self._aktuelles_kraftbild_aktualisieren()
            return
        if fehler is None and kraefteresultat is None:
            fehler = ValueError("Echtzeitauftrag lieferte kein Kraftergebnis")
        if fehler is not None:
            self._kraftanzeige_verwerfen("Kraftauswertung fehlgeschlagen")
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
        if anzahl_schritte == 0:
            self._echtzeit_kraefteresultat = kraefteresultat
            self._echtzeit_kraftzeit_s = self._echtzeit_berechnet_s
            self._aktuelles_kraftbild_aktualisieren()
            return
        self._echtzeit_berechnet_s += (
            anzahl_schritte * self._echtzeit_physik.dt_s)
        koerper = self._laufzeit_koerper.get(koerper_name)
        if koerper is None:
            self._kraftanzeige_verwerfen("Laufzeitkoerper fehlt")
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: Laufzeitkörper fehlt"})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): Laufzeitkoerper fehlt" % koerper_name)
            return
        try:
            koerper.zustand = zustand
        except ValueError as state_error:
            self._kraftanzeige_verwerfen("Ungueltiger Koerperzustand")
            self._zeit_pausieren()
            self._solver_status_aktualisieren(
                {"Lösungstyp": "Fehler: ungültiger Körperzustand"})
            self.protokoll_schreiben(
                "Echtzeit-Simulation (%s): %s"
                % (koerper_name, state_error))
            return
        zustand = koerper.zustand
        self._echtzeit_zustand = koerper.zustand
        self._navigationsanzeigen_aktualisieren()
        self._echtzeit_kraefteresultat = kraefteresultat
        self._echtzeit_kraftzeit_s = max(
            0.0, self._echtzeit_berechnet_s - self._echtzeit_physik.dt_s)
        self._echtzeit_anzeige_verlauf.append(
            (self._echtzeit_berechnet_s, zustand))
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
            if kraefteresultat is not None:
                koerper = self._laufzeit_koerper.get(self._echtzeit_name)
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

    def _ruderwinkel_geaendert(self, winkel_grad):
        """Uebergibt den festen Ruderwinkel an das aktive Kraftmodell."""
        winkel_rad = math.radians(float(winkel_grad))
        war_laufend = self._echtzeit_timer.isActive()
        self._kraftanzeige_verwerfen("Ruderwinkel geaendert; neue Berechnung ausstehend")
        if war_laufend:
            self._zeit_pausieren()
        else:
            self._echtzeit_generation += 1
        kraftfunktion = self._echtzeit_kraftfunktion
        if kraftfunktion is not None and not self._echtzeit_aufgabe_laeuft:
            try:
                kraftfunktion.ruderwinkel_setzen(winkel_rad)
            except (AttributeError, ValueError) as fehler:
                self.protokoll_schreiben(
                    "Ruderwinkel konnte nicht gesetzt werden: %s" % fehler)
                if war_laufend:
                    self._zeit_fortsetzen()
                return
        if self._btn_statisch.isChecked():
            self._statische_simulation_ausfuehren()
        elif not self._echtzeit_timer.isActive():
            self._echtzeit_kraefteresultat = None
            self._aktuelles_kraftbild_aktualisieren()
        if war_laufend:
            self._zeit_fortsetzen()

    def _fremdkraft_geaendert(self, *_):
        if self._btn_statisch.isChecked():
            fremdkraft = self._fremdkraft_aktuell()
            if fremdkraft == self._statische_fremdkraft:
                return
            self._statische_simulation_ausfuehren()
            return
        if self._echtzeit_kraftfunktion is None:
            return
        war_laufend = self._echtzeit_timer.isActive()
        self._kraftanzeige_verwerfen("Fremdkraft geaendert; neue Berechnung ausstehend")
        if war_laufend:
            self._zeit_pausieren()
        else:
            self._echtzeit_generation += 1
        try:
            if not self._echtzeit_aufgabe_laeuft:
                self._echtzeit_kraftfunktion.fremdkraft_setzen(
                    self._fremdkraft_aktuell())
        except (AttributeError, ValueError) as fehler:
            self.protokoll_schreiben("Fremdkraft: %s" % fehler)
            if war_laufend:
                self._zeit_fortsetzen()
            return
        if war_laufend:
            self._echtzeit_kraefteresultat = None
            self._zeit_fortsetzen()
            return
        # Pausiert: Kraftbild sofort mit der neuen Kraft neu zeichnen
        self._echtzeit_kraefteresultat = None
        self._aktuelles_kraftbild_aktualisieren()
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is not None and self._echtzeit_zustand is not None:
            self._echtzeit_pose_anzeigen(self._echtzeit_zustand, render=True)

    def _statisches_kraftbild_aktualisieren(self):
        """Zeichnet die geänderte Fremdkraft bis zum neuen Gleichgewicht."""
        bruecke = getattr(self, "_bruecke", None)
        if bruecke is None:
            return
        if hasattr(bruecke, "kraefte_neu_zeichnen"):
            bruecke.kraefte_neu_zeichnen()
            self._kraftlegende_aktualisieren()

    def _aktuelles_kraftbild_aktualisieren(self):
        if (not self._btn_echtzeit.isChecked()
                or self._echtzeit_name is None or self._echtzeit_zustand is None
                or self._echtzeit_physik is None
                or self._echtzeit_kraftfunktion is None):
            return
        koerper = self._laufzeit_koerper.get(self._echtzeit_name)
        bruecke = getattr(self, "_bruecke", None)
        if koerper is not None and bruecke is not None:
            ergebnis = self._echtzeit_kraefteresultat
            if ergebnis is None:
                self._echtzeit_kraftauswertung_ausstehend = True
                if self._echtzeit_aufgabe_laeuft:
                    return
                self._echtzeit_auftragssequenz += 1
                sequenz = self._echtzeit_auftragssequenz
                aufgabe = _EchtzeitAufgabe(
                    self._echtzeit_generation, sequenz, self._echtzeit_name,
                    self._echtzeit_zustand, self._echtzeit_kraftfunktion,
                    koerper, self._echtzeit_physik,
                    self._echtzeit_physik.dt_s, 0, self._echtzeit_signale,
                    fremdkraft=self._fremdkraft_aktuell(),
                    ruderwinkel_rad=math.radians(self._ruderwinkel_feld.value()))
                self._echtzeit_kraftauswertung_ausstehend = False
                self._echtzeit_aufgabe_laeuft = True
                self._echtzeit_aufgabe_sequenz_laufend = sequenz
                self._echtzeit_schritte_laufend = 0
                QThreadPool.globalInstance().start(aufgabe)
                return
            self._echtzeit_kraftauswertung_ausstehend = False
            self._kraftbild_daten_setzen(
                bruecke, self._echtzeit_name, koerper,
                self._echtzeit_kraftfunktion, self._echtzeit_physik,
                0.0, 0.0, ergebnis=ergebnis)

    def _kraftanzeige_verwerfen(self, grund):
        hat_daten = bool(self._kraftanzeige_snapshots)
        bruecke = getattr(self, "_bruecke", None)
        for name in self._kraftanzeige_snapshots:
            if bruecke is not None and hasattr(bruecke, "kraefte_daten_veralten"):
                bruecke.kraefte_daten_veralten(name)
            elif bruecke is not None and hasattr(bruecke, "kraefte_daten_entfernen"):
                bruecke.kraefte_daten_entfernen(name)
        self._kraftanzeige_snapshots.clear()
        self._kraftanzeige_kontext = None
        self._kraefte_werte.snapshots_setzen(())
        self._kraefte_werte.kopf.setText(grund + " | keine gueltigen Anzeigedaten")
        self._kraefte_werte.legende_setzen({})
        if hat_daten and bruecke is not None and hasattr(bruecke, "render"):
            bruecke.render()

    def _kraftbild_daten_setzen(self, bruecke, name, koerper, kraftfunktion,
                                physik, z, phi, v_z=0.0, omega_x=0.0,
                                ergebnis=None, solverdiagnose=None):
        try:
            erg = ergebnis
            if erg is None:
                raise ValueError(
                    "Kraftergebnis fehlt; fachliche Auswertung im Worker erforderlich")
            if hasattr(bruecke, "kraefte_snapshot_setzen"):
                from ..core.kraefte_anzeige import KraefteAnzeigeAdapter, SolverBewertung
                from ..core.kraftmodell import KraftErgebnis, Kraftmodell
                if not isinstance(erg, KraftErgebnis):
                    modell = Kraftmodell(
                        lambda *_args, **_kwargs: erg,
                        masse=koerper.masse, g=physik.g_m_pro_s2)
                    modell.fremdkraft_setzen(self._fremdkraft_aktuell())
                    erg = modell.mit_hydrostatik(erg, lage=(z, phi, 0.0))
                kontext = (self._btn_statisch.isChecked(),
                           self._statisch_generation,
                           self._echtzeit_generation)
                if kontext != self._kraftanzeige_kontext:
                    self._kraftanzeige_generation += 1
                    self._kraftanzeige_kontext = kontext
                    self._kraftanzeige_snapshots.clear()
                    self._kraftanzeige_sequenz = 0
                self._kraftanzeige_sequenz += 1
                zeit = (getattr(self, "_echtzeit_kraftzeit_s", self._echtzeit_berechnet_s)
                        if ergebnis is not None
                        and ergebnis is self._echtzeit_kraefteresultat
                        else self._echtzeit_berechnet_s
                        if self._btn_echtzeit.isChecked() else 0.0)
                bewertung = None
                if solverdiagnose is not None:
                    quelle, freiheitsgrade, kriterien, erfuellt, stationaer = solverdiagnose
                    quell_ids = tuple(b.quell_id for b in erg.beitraege)
                    if not erg.schwerkraft_beruecksichtigt:
                        quell_ids += ("schwerkraft",)
                    if (any(erg.added_mass_diagonal)
                            and not any(b.name == "added_mass" for b in erg.beitraege)):
                        quell_ids += ("added_mass",)
                    bewertung = SolverBewertung(
                        name, self._kraftanzeige_generation, self._kraftanzeige_sequenz,
                        quell_ids, quelle, freiheitsgrade, kriterien,
                        erfuellt, stationaer)
                snapshot = KraefteAnzeigeAdapter().aus_ergebnis(
                    erg, koerper_id=name, generation=self._kraftanzeige_generation,
                    sequenz=self._kraftanzeige_sequenz, zeit_s=zeit,
                    masse_kg=koerper.masse, g_m_s2=physik.g_m_pro_s2,
                    solverbewertung=bewertung)
                if (self._btn_statisch.isChecked()
                        and hasattr(type(bruecke), "physik_basis_position_ermitteln")):
                    basis = bruecke.physik_basis_position_ermitteln(name)
                    snapshot = replace(snapshot, szenenversatz_m=(
                        float(basis[0]), float(basis[1]), 0.0))
                if bruecke.kraefte_snapshot_setzen(snapshot) is False:
                    self.protokoll_schreiben(
                        "Kraeftebild (%s): veralteter Snapshot %s/%s verworfen"
                        % (name, snapshot.generation, snapshot.sequenz))
                    return
                koerperquelle = getattr(koerper, "quell_id", None)
                if koerperquelle is not None:
                    self._kraftanzeige_koerperquellen[name] = koerperquelle
                    sichtbar = self._einstellungen.get(
                        "kraefteanzeige", "sichtbarkeiten").get(koerperquelle, {})
                    for id_, aktiv in sichtbar.items():
                        key = (name, id_)
                        if hasattr(bruecke, "_kraftzeichner"):
                            bruecke._kraftzeichner().sichtbar[key] = aktiv
                self._kraftanzeige_snapshots[name] = snapshot
                self._kraftsichtbarkeiten_abgleichen(bruecke, neu_zeichnen=False)
                self._kraefte_werte.koerper_setzen(self._laufzeit_koerper)
                self._kraefte_werte.snapshots_setzen(
                    self._kraftanzeige_snapshots.values(),
                    verzoegert=self._echtzeit_timer.isActive())
                QTimer.singleShot(0, self._kraftlegende_aktualisieren)
            else:
                raise ValueError(
                    "Grafikbruecke unterstuetzt den gemeinsamen Snapshotpfad nicht")
        except (ArithmeticError, AttributeError, TypeError, ValueError) as fehler:
            self._kraftanzeige_snapshots.pop(name, None)
            verwerfen = getattr(bruecke, "kraefte_daten_veralten", None)
            if callable(verwerfen):
                verwerfen(name)
            self._kraefte_werte.snapshots_setzen(
                self._kraftanzeige_snapshots.values())
            self._kraefte_werte.kopf.setText(
                "Kraeftebild (%s): ungueltige Anzeigedaten | %s" % (name, fehler))
            self.protokoll_schreiben(
                "Kräftebild (%s) konnte nicht aktualisiert werden: %s"
                % (name, fehler))
            render = getattr(bruecke, "render", None)
            if callable(render):
                render()

    def _solver_status_aktualisieren(self, werte):
        for schluessel, wert in werte.items():
            eintrag = self._solver_werte.get(schluessel)
            if eintrag is not None:
                text = str(wert)
                if eintrag.text(1) != text:
                    eintrag.setText(1, text)

    def protokoll_schreiben(self, text):


        self.protokoll.append(text)

    def closeEvent(self, ereignis):
        self._statisch_generation += 1
        self._statische_aufgaben_ausstehend.clear()
        self._kraftansicht_abkoppeln()
        self._einstellungen.setzen(
            "kraefteanzeige", "fensterlayout",
            self._kraefte_werte.layout_exportieren())
        self._navigations_timer.stop()
        if self._navigationsfenster is not None:
            self._navigationsfenster.close()
        if (self._echtzeit_timer.isActive()
                or self._echtzeit_render_timer.isActive()
                or self._echtzeit_schritte_laufend):
            self._zeit_pausieren()
        self._echtzeit_generation += 1
        self._echtzeit_kraftauswertung_ausstehend = False
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
        bruecke = getattr(self, "_bruecke", None)
        if hasattr(bruecke, "kraefte_anzeige_beenden"):
            bruecke.kraefte_anzeige_beenden()
        super().closeEvent(ereignis)

    def _protokoll_umschalten(self):
        self._dock_protokoll.setVisible(self._act_protokoll.isChecked())

    def baum_setzen(self, welt_knoten):
        konfiguration = getattr(welt_knoten, "konfiguration", None)
        if konfiguration is not None:
            konfiguration.paketfabrik_aktiv = self._einstellungen.get(
                "modell", "paketfabrik_aktiv")
        self.baum.lade(welt_knoten)
        if getattr(self, "_bruecke", None) is not None:
            self._laufzeit_objekte_aktualisieren("import")

    def _nur_aktives_bedienbar_setzen(self, aktiv):
        baum = getattr(self, "baum", None)
        if baum is not None:
            baum.nur_aktives_bedienbar_setzen(aktiv)
