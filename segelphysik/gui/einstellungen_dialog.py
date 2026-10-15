"""Dialog fuer Einstellungen (Solver, Kraftpfeildarstellung), speichert sofort."""
from __future__ import annotations

import re

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QDialog, QDoubleSpinBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

TITEL = {"statisch": "Solver-Parameter: Statisch",
         "dynamisch": "Solver-Parameter: Dynamisch"}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class FarbFeld(QWidget):
    """Hex-Eingabe (leer erlaubt) mit Farbwahl-Knopf."""
    geaendert = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        zeile = QHBoxLayout(self)
        zeile.setContentsMargins(0, 0, 0, 0)
        self._text = QLineEdit()
        self._text.setMaxLength(7)
        self._text.setFixedWidth(70)
        self._text.setPlaceholderText("Standard")
        self._knopf = QPushButton("")
        self._knopf.setFixedWidth(24)
        zeile.addWidget(self._text)
        zeile.addWidget(self._knopf)
        self._text.editingFinished.connect(self._eingabe)
        self._knopf.clicked.connect(self._waehlen)

    def setText(self, text):
        self._text.setText(text)
        self._anzeigen(text)

    def text(self):
        return self._text.text().strip()

    def _anzeigen(self, text):
        farbe = text if _HEX.match(text or "") else "transparent"
        self._knopf.setStyleSheet("background-color: %s;" % farbe)

    def _eingabe(self):
        text = self.text()
        if text and not _HEX.match(text):
            self._text.setStyleSheet("color: red;")
            return
        self._text.setStyleSheet("")
        self._anzeigen(text)
        self.geaendert.emit(text)

    def _waehlen(self):
        start = QColor(self.text()) if _HEX.match(self.text()) else QColor("white")
        farbe = QColorDialog.getColor(start, self)
        if farbe.isValid():
            self.setText(farbe.name())
            self.geaendert.emit(farbe.name())


class EinstellungenDialog(QDialog):
    """Dialog fuer einen Bereich (`bereich`) oder frei zusammengestellt:

    formular: Liste (bereich, schluessel-Liste oder None) als Formular.
    pfeile: Liste (bereich, titel); je Bereich eine Rasterzeile.
    """
    geaendert = Signal()

    def __init__(self, einstellungen, bereich=None, parent=None, titel=None,
                 formular=None, pfeile=None):
        super().__init__(parent)
        self._ein = einstellungen
        self._bereich = bereich
        self._felder = {}
        self._feld_liste = []
        if formular is None and not pfeile:
            formular = [(bereich, None)]
        self.setWindowTitle(titel or TITEL.get(bereich, str(bereich)))
        layout = QVBoxLayout(self)
        inhalt = QWidget()
        innen = QVBoxLayout(inhalt)
        innen.setContentsMargins(0, 0, 0, 0)
        for b, schluessel in (formular or []):
            form = QFormLayout()
            innen.addLayout(form)
            for k, e in einstellungen.vorlage[b].items():
                if schluessel is not None and k not in schluessel:
                    continue
                feld = self._feld_bauen(b, k, e)
                self._felder[k] = feld
                self._feld_liste.append((b, k, feld))
                if e["typ"] == "bool":
                    form.addRow(feld)
                else:
                    text = e["beschreibung"]
                    if e.get("einheit"):
                        text += " [%s]" % e["einheit"]
                    form.addRow(text, feld)
        if pfeile:
            innen.addWidget(self._raster(pfeile))
        if pfeile:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(inhalt)
            layout.addWidget(scroll)
            self.resize(900, 420)
        else:
            layout.addWidget(inhalt)
        self._hinweis = QLabel("")
        layout.addWidget(self._hinweis)
        zeile = QHBoxLayout()
        btn_default = QPushButton("Standardwerte")
        btn_default.clicked.connect(self._standard)
        btn_zu = QPushButton("Schließen")
        btn_zu.clicked.connect(self.close)
        zeile.addWidget(btn_default)
        zeile.addStretch(1)
        zeile.addWidget(btn_zu)
        layout.addLayout(zeile)
        self._anzeigen()

    def _raster(self, pfeile):
        box = QGroupBox("Pfeile (je Zeile ein Pfeil)")
        gitter = QGridLayout(box)
        spalten = list(self._ein.vorlage[pfeile[0][0]].keys())
        for c, k in enumerate(spalten, start=1):
            kopf = QLabel(k)
            kopf.setToolTip(self._ein.vorlage[pfeile[0][0]][k]["beschreibung"])
            gitter.addWidget(kopf, 0, c)
        for r, (b, titel) in enumerate(pfeile, start=1):
            gitter.addWidget(QLabel(titel), r, 0)
            for c, k in enumerate(spalten, start=1):
                feld = self._feld_bauen(b, k, self._ein.vorlage[b][k],
                                        mit_text=False)
                self._feld_liste.append((b, k, feld))
                gitter.addWidget(feld, r, c)
        return box

    def _feld_bauen(self, bereich, schluessel, e, mit_text=True):
        def setzen(v, b=bereich, k=schluessel):
            self._geaendert(b, k, v)

        if e["typ"] == "bool":
            feld = QCheckBox(e["beschreibung"] if mit_text else "")
            feld.toggled.connect(setzen)
        elif e["typ"] == "farbe":
            feld = FarbFeld()
            feld.geaendert.connect(setzen)
        elif e["typ"] == "int":
            feld = QSpinBox()
            feld.setRange(int(e["min"]), int(e["max"]))
            feld.valueChanged.connect(lambda v: setzen(int(v)))
        else:
            feld = QDoubleSpinBox()
            feld.setDecimals(int(e.get("dezimalen", 3)))
            feld.setRange(float(e["min"]), float(e["max"]))
            feld.setSingleStep(10.0 ** -min(int(e.get("dezimalen", 3)), 3))
            feld.valueChanged.connect(lambda v: setzen(float(v)))
        feld.setToolTip(e["beschreibung"])
        return feld

    def neu_laden(self):
        """Zeigt immer die aktuell gespeicherten Werte."""
        self._anzeigen()

    def _anzeigen(self):
        for b, k, feld in self._feld_liste:
            wert = self._ein.get(b, k)
            feld.blockSignals(True)
            if isinstance(feld, QCheckBox):
                feld.setChecked(bool(wert))
            elif isinstance(feld, FarbFeld):
                feld.setText(wert)
            else:
                feld.setValue(wert)
            feld.blockSignals(False)

    def _geaendert(self, bereich, schluessel, wert):
        try:
            self._ein.setzen(bereich, schluessel, wert)
            self._hinweis.setText("")
        except ValueError as fehler:
            self._hinweis.setText("Ungültig: %s" % fehler)
            return
        self.geaendert.emit()

    def _standard(self):
        for b, k, _feld in self._feld_liste:
            self._ein.setzen(b, k, self._ein.vorlage[b][k]["default"])
        self._anzeigen()
        self.geaendert.emit()
