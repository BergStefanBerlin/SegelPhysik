"""Dialog fuer Solver-Parameter (Statisch / Dynamisch), speichert sofort."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QVBoxLayout,
)

TITEL = {"statisch": "Solver-Parameter: Statisch",
         "dynamisch": "Solver-Parameter: Dynamisch"}


class EinstellungenDialog(QDialog):
    def __init__(self, einstellungen, bereich, parent=None):
        super().__init__(parent)
        self._ein = einstellungen
        self._bereich = bereich
        self._felder = {}
        self.setWindowTitle(TITEL.get(bereich, bereich))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)
        for schluessel, e in einstellungen.vorlage[bereich].items():
            feld = self._feld_bauen(schluessel, e)
            self._felder[schluessel] = feld
            if e["typ"] == "bool":
                form.addRow(feld)
            else:
                text = e["beschreibung"]
                if e.get("einheit"):
                    text += " [%s]" % e["einheit"]
                form.addRow(text, feld)
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

    def _feld_bauen(self, schluessel, e):
        if e["typ"] == "bool":
            feld = QCheckBox(e["beschreibung"])
            feld.toggled.connect(lambda v, k=schluessel: self._geaendert(k, v))
        elif e["typ"] == "int":
            feld = QSpinBox()
            feld.setRange(int(e["min"]), int(e["max"]))
            feld.valueChanged.connect(
                lambda v, k=schluessel: self._geaendert(k, int(v)))
        else:
            feld = QDoubleSpinBox()
            feld.setDecimals(int(e.get("dezimalen", 3)))
            feld.setRange(float(e["min"]), float(e["max"]))
            feld.setSingleStep(10.0 ** -min(int(e.get("dezimalen", 3)), 3))
            feld.valueChanged.connect(
                lambda v, k=schluessel: self._geaendert(k, float(v)))
        feld.setToolTip(e["beschreibung"])
        return feld

    def _anzeigen(self):
        for k, feld in self._felder.items():
            wert = self._ein.get(self._bereich, k)
            feld.blockSignals(True)
            if isinstance(feld, QCheckBox):
                feld.setChecked(bool(wert))
            else:
                feld.setValue(wert)
            feld.blockSignals(False)

    def _geaendert(self, schluessel, wert):
        try:
            self._ein.setzen(self._bereich, schluessel, wert)
            self._hinweis.setText("")
        except ValueError as fehler:
            self._hinweis.setText("Ungültig: %s" % fehler)

    def _standard(self):
        self._ein.zuruecksetzen(self._bereich)
        self._anzeigen()
