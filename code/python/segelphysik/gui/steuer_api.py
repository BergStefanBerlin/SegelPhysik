"""Programmierbare Steuer- und Diagnose-API fuer das Hauptfenster."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractButton, QComboBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit,
    QSlider, QSpinBox, QTextEdit, QTreeWidget, QTreeWidgetItem, QWidget,
)
from shiboken6 import isValid as qt_object_is_valid


_UNSET = object()


class GUIControlAPI:
    """Steuert sichtbare GUI-Elemente und liefert einen serialisierbaren Snapshot.

    Alle Methoden muessen im GUI-Thread aufgerufen werden. `controls()` liefert
    die verwendbaren IDs; schreibende Aufrufe verwenden Qt-Setter oder
    `click()`/`trigger()` und loesen dadurch die normalen GUI-Signale aus.

    Beispiel: `fenster.steuer_api.set_control("fremd_felder.betrag", 20.0)`.
    """

    def __init__(self, fenster):
        self._fenster = fenster

    def controls(self):
        self._thread_pruefen()
        aliases = self._widget_aliases()
        ergebnis = []
        for widget in self._fenster.findChildren(QWidget):
            if not self._ist_bedienbar(widget):
                continue
            ids = sorted(aliases.get(widget, ()))
            steuer_id = ids[0] if ids else self._widget_pfad(widget)
            ergebnis.append(self._widget_beschreiben(widget, steuer_id, ids))
            if isinstance(widget, QTreeWidget):
                ergebnis.extend(self._baum_elemente(widget, steuer_id))
        ergebnis.extend(self._aktionen())
        return sorted(ergebnis, key=lambda element: element["id"])

    def get_control(self, control_id):
        self._thread_pruefen()
        ziel = self._finden(control_id)
        return self._beschreiben_ziel(ziel)

    def set_control(self, control_id, value):
        self._thread_pruefen()
        ziel = self._finden(control_id)
        element = ziel["element"]
        if isinstance(element, QTreeWidgetItem):
            if not element.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                raise TypeError("Baumknoten ist nicht schaltbar: %s" % control_id)
            if not isinstance(value, bool):
                raise TypeError("Baumstatus muss boolesch sein")
            element.setCheckState(
                ziel["tree"].columnCount() - 1,
                Qt.CheckState.Checked if value
                else Qt.CheckState.Unchecked)
            return self.get_control(control_id)
        if isinstance(element, QAbstractButton):
            if not element.isCheckable():
                raise TypeError(
                    "Schaltflaeche braucht activate(): %s" % control_id)
            if not isinstance(value, bool):
                raise TypeError("Schaltstatus muss boolesch sein")
            if element.isChecked() != value:
                element.click()
            if element.isChecked() != value:
                raise RuntimeError(
                    "Steuerstatus konnte nicht gesetzt werden: %s"
                    % control_id)
        elif isinstance(element, QComboBox):
            self._combo_setzen(element, value, control_id)
        elif isinstance(element, (QDoubleSpinBox, QSpinBox, QSlider)):
            try:
                element.setValue(value)
            except (TypeError, ValueError, OverflowError) as fehler:
                raise ValueError(
                    "Ungueltiger Wert fuer %s: %r" % (control_id, value)
                ) from fehler
        elif isinstance(element, QLineEdit):
            element.setText(str(value))
        elif isinstance(element, (QTextEdit, QPlainTextEdit)):
            element.setPlainText(str(value))
        else:
            raise TypeError("Steuerelement ist nicht schreibbar: %s" % control_id)
        return self.get_control(control_id)

    def activate(self, control_id):
        self._thread_pruefen()
        ziel = self._finden(control_id)
        element = ziel["element"]
        if isinstance(element, QAbstractButton):
            element.click()
        elif isinstance(element, QAction):
            element.trigger()
        elif isinstance(element, QTreeWidgetItem):
            if not element.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                raise TypeError("Baumknoten ist nicht schaltbar: %s" % control_id)
            spalte = ziel["tree"].columnCount() - 1
            zustand = element.checkState(spalte)
            element.setCheckState(
                spalte,
                Qt.CheckState.Unchecked
                if zustand == Qt.CheckState.Checked
                else Qt.CheckState.Checked)
        else:
            raise TypeError("Steuerelement kann nicht aktiviert werden: %s"
                            % control_id)
        return self.get_control(control_id)

    def snapshot(self):
        self._thread_pruefen()
        fenster = self._fenster
        name = self._aktiver_koerpername()
        koerper = getattr(fenster, "_laufzeit_koerper", {}).get(name)
        zustand = getattr(fenster, "_echtzeit_zustand", None)
        if zustand is None and koerper is not None:
            zustand = koerper.zustand
        ergebnis = getattr(fenster, "_echtzeit_kraefteresultat", None)
        return {
            "mode": (
                "statisch" if fenster._btn_statisch.isChecked()
                else "echtzeit"),
            "simulation": {
                "timer_active": fenster._echtzeit_timer.isActive(),
                "render_timer_active": (
                    fenster._echtzeit_render_timer.isActive()),
                "worker_active": fenster._echtzeit_aufgabe_laeuft,
                "requested_s": fenster._echtzeit_angefordert_s,
                "computed_s": fenster._echtzeit_berechnet_s,
                "backlog_s": fenster._echtzeit_rueckstand_s(),
                "mode": fenster._echtzeit_modus,
                "status": self._solver_status(),
            },
            "body": self._koerper_abbilden(name, koerper, zustand),
            "physics": self._wert_abbilden(
                getattr(fenster, "_echtzeit_physik", None)),
            "external_force": self._wert_abbilden(
                fenster._fremdkraft_aktuell()),
            "force_model": self._wert_abbilden(
                getattr(fenster, "_echtzeit_kraftfunktion", None)),
            "force_result": self._wert_abbilden(ergebnis),
            "static_results": self._wert_abbilden(
                getattr(fenster, "_statische_ergebnisse", {})),
            "settings": self._wert_abbilden(fenster._einstellungen),
            "controls": {
                element["id"]: element["value"]
                for element in self.controls()
            },
            "variables": self.variables(),
        }

    def variables(self):
        """Liefert alle Hauptfenster-Attribute in lesbarer, JSON-tauglicher Form."""
        self._thread_pruefen()
        return {
            name: self._wert_abbilden(value)
            for name, value in vars(self._fenster).items()
            if not callable(value)
        }

    def _thread_pruefen(self):
        if QThread.currentThread() != self._fenster.thread():
            raise RuntimeError("GUIControlAPI muss im GUI-Thread laufen")

    def _widget_aliases(self):
        aliases = {}
        for name, value in vars(self._fenster).items():
            alias = name.lstrip("_")
            if isinstance(value, QWidget):
                aliases.setdefault(value, set()).add(alias)
            elif isinstance(value, dict):
                for key, widget in value.items():
                    if isinstance(widget, QWidget):
                        aliases.setdefault(widget, set()).add(
                            "%s.%s" % (alias, key))
        return aliases

    @staticmethod
    def _ist_bedienbar(widget):
        return isinstance(widget, (
            QAbstractButton, QComboBox, QDoubleSpinBox, QLineEdit,
            QPlainTextEdit, QSlider, QSpinBox, QTextEdit, QTreeWidget,
        ))

    def _widget_beschreiben(self, widget, control_id, aliases):
        return {
            "id": control_id,
            "aliases": aliases,
            "kind": type(widget).__name__,
            "label": self._widget_label(widget),
            "enabled": widget.isEnabled(),
            "visible": widget.isVisible(),
            "value": self._widget_wert(widget),
            "minimum": (
                widget.minimum()
                if isinstance(widget, (QDoubleSpinBox, QSpinBox, QSlider))
                else None),
            "maximum": (
                widget.maximum()
                if isinstance(widget, (QDoubleSpinBox, QSpinBox, QSlider))
                else None),
            "options": (
                [widget.itemText(index)
                 for index in range(widget.count())]
                if isinstance(widget, QComboBox) else None),
        }

    @staticmethod
    def _widget_label(widget):
        if isinstance(widget, QAbstractButton):
            return widget.text()
        if isinstance(widget, QComboBox):
            return widget.objectName() or type(widget).__name__
        return widget.objectName() or type(widget).__name__

    @staticmethod
    def _widget_wert(widget):
        if isinstance(widget, QAbstractButton):
            return widget.isChecked() if widget.isCheckable() else None
        if isinstance(widget, QComboBox):
            return {
                "index": widget.currentIndex(),
                "text": widget.currentText(),
                "data": GUIControlAPI._wert_abbilden(
                    widget.currentData()),
            }
        if isinstance(widget, (QDoubleSpinBox, QSpinBox, QSlider)):
            return widget.value()
        if isinstance(widget, QLineEdit):
            return widget.text()
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            return widget.toPlainText()
        return None

    def _baum_elemente(self, tree, prefix):
        result = []

        def sammeln(parent, pfad):
            for index in range(parent.childCount()):
                item = parent.child(index)
                text = item.text(0)
                item_path = pfad + (text or type(item).__name__,)
                item_id = prefix + ".item." + ".".join(item_path)
                result.append({
                    "id": item_id,
                    "aliases": [],
                    "kind": "QTreeWidgetItem",
                    "label": text,
                    "enabled": bool(item.flags() & Qt.ItemFlag.ItemIsEnabled),
                    "visible": tree.isVisible(),
                    "value": self._baum_wert(item, tree),
                    "minimum": None,
                    "maximum": None,
                    "options": None,
                })
                sammeln(item, item_path)

        for index in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(index)
            text = item.text(0)
            item_path = (text or type(item).__name__,)
            result.append({
                "id": prefix + ".item." + ".".join(item_path),
                "aliases": [],
                "kind": "QTreeWidgetItem",
                "label": text,
                "enabled": bool(item.flags() & Qt.ItemFlag.ItemIsEnabled),
                "visible": tree.isVisible(),
                "value": self._baum_wert(item, tree),
                "minimum": None,
                "maximum": None,
                "options": None,
            })
            sammeln(item, item_path)
        return result

    @staticmethod
    def _baum_wert(item, tree):
        zustand = item.checkState(tree.columnCount() - 1)
        return {
            "checked": zustand == Qt.CheckState.Checked,
            "check_state": zustand.name.lower(),
            "checkable": bool(
                item.flags() & Qt.ItemFlag.ItemIsUserCheckable),
        }

    def _aktionen(self):
        result = []

        def sammeln(menu, pfad):
            for index, action in enumerate(menu.actions()):
                name = action.text().replace("&", "")
                action_path = pfad + (name or "action_%d" % index,)
                if action.menu() is not None:
                    sammeln(action.menu(), action_path)
                    continue
                result.append({
                    "id": "menu." + ".".join(action_path),
                    "aliases": [],
                    "kind": "QAction",
                    "label": name,
                    "enabled": action.isEnabled(),
                    "visible": action.isVisible(),
                    "value": action.isChecked() if action.isCheckable() else None,
                    "minimum": None,
                    "maximum": None,
                    "options": None,
                })

        sammeln(self._fenster.menuBar(), ())
        return result

    def _widget_pfad(self, widget):
        teile = []
        aktuell = widget
        while aktuell is not None and aktuell is not self._fenster:
            name = aktuell.objectName() or self._widget_label(aktuell)
            parent = aktuell.parentWidget()
            gleichartige = (
                [kind for kind in parent.findChildren(QWidget)
                 if type(kind) is type(aktuell)
                 and (kind.objectName() or self._widget_label(kind)) == name]
                if parent is not None else [aktuell])
            index = gleichartige.index(aktuell) if aktuell in gleichartige else 0
            teile.append("%s:%s[%d]" % (
                type(aktuell).__name__, name, index))
            aktuell = parent
        return "widget." + "/".join(reversed(teile))

    def _finden(self, control_id):
        for widget in self._fenster.findChildren(QWidget):
            if not self._ist_bedienbar(widget):
                continue
            ids = self._widget_aliases().get(widget, set())
            pfad = self._widget_pfad(widget)
            if control_id in ids or control_id == pfad:
                return {"element": widget}
            if isinstance(widget, QTreeWidget):
                prefix = sorted(ids)[0] if ids else pfad
                for ziel in self._baum_ziel_elemente(widget, prefix):
                    if control_id == ziel["id"]:
                        return ziel
        for ziel in self._aktions_ziel_elemente():
            if control_id == ziel["id"]:
                return ziel
        raise KeyError("Unbekanntes GUI-Steuerelement: %s" % control_id)

    def _beschreiben_ziel(self, ziel):
        element = ziel["element"]
        if isinstance(element, QTreeWidgetItem):
            tree = ziel["tree"]
            return {
                "id": ziel["id"],
                "kind": "QTreeWidgetItem",
                "label": element.text(0),
                "enabled": bool(
                    element.flags() & Qt.ItemFlag.ItemIsEnabled),
                "visible": tree.isVisible(),
                "value": self._baum_wert(element, tree),
            }
        if isinstance(element, QAction):
            return {
                "id": ziel["id"],
                "kind": "QAction",
                "label": element.text().replace("&", ""),
                "enabled": element.isEnabled(),
                "visible": element.isVisible(),
                "value": element.isChecked() if element.isCheckable() else None,
            }
        aliases = sorted(self._widget_aliases().get(element, ()))
        return self._widget_beschreiben(
            element,
            aliases[0] if aliases else self._widget_pfad(element),
            aliases,
        )

    def _baum_ziel_elemente(self, tree, prefix):
        result = []

        def sammeln(parent, pfad):
            for index in range(parent.childCount()):
                item = parent.child(index)
                text = item.text(0)
                item_path = pfad + (text or type(item).__name__,)
                result.append({
                    "id": prefix + ".item." + ".".join(item_path),
                    "element": item,
                    "tree": tree,
                })
                sammeln(item, item_path)

        for index in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(index)
            text = item.text(0)
            item_path = (text or type(item).__name__,)
            result.append({
                "id": prefix + ".item." + ".".join(item_path),
                "element": item,
                "tree": tree,
            })
            sammeln(item, item_path)
        return result

    def _aktions_ziel_elemente(self):
        result = []

        def sammeln(menu, pfad):
            for index, action in enumerate(menu.actions()):
                name = action.text().replace("&", "")
                action_path = pfad + (name or "action_%d" % index,)
                if action.menu() is not None:
                    sammeln(action.menu(), action_path)
                else:
                    result.append({
                        "id": "menu." + ".".join(action_path),
                        "element": action,
                    })

        sammeln(self._fenster.menuBar(), ())
        return result

    def _aktiver_koerpername(self):
        welt = getattr(getattr(self._fenster, "baum", None), "_welt", None)
        if welt is None:
            return getattr(self._fenster, "_echtzeit_name", None)
        from .baum import summenkoerper
        return next(
            (knoten.name for knoten in summenkoerper(welt)
             if knoten.sichtbar),
            getattr(self._fenster, "_echtzeit_name", None))

    def _koerper_abbilden(self, name, koerper, zustand):
        if koerper is None:
            return {"name": name, "available": False}
        return {
            "name": name,
            "available": True,
            "mass_kg": koerper.masse,
            "inertia_kg_m2": self._wert_abbilden(
                koerper.traegheitstensor),
            "model_center_m": self._wert_abbilden(koerper._r_eingabe),
            "version": getattr(koerper, "version", None),
            "state": self._wert_abbilden(zustand),
        }

    def _solver_status(self):
        return {
            name: item.text(1)
            for name, item in getattr(
                self._fenster, "_solver_werte", {}).items()
        }

    @classmethod
    def _wert_abbilden(cls, value):
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        if is_dataclass(value) and not isinstance(value, type):
            return {
                feld.name: cls._wert_abbilden(getattr(value, feld.name))
                for feld in fields(value)
            }
        if hasattr(value, "as_array") and callable(value.as_array):
            return cls._wert_abbilden(value.as_array())
        if type(value).__name__ == "Auftriebsergebnis":
            return {
                name: cls._wert_abbilden(getattr(value, name))
                for name in ("V_tauch", "K", "F_A", "M")
            }
        if type(value).__name__ == "Einstellungen":
            return {
                "path": str(value.pfad),
                "data": cls._wert_abbilden(value._daten),
                "messages": cls._wert_abbilden(value.meldungen),
                "read_only": getattr(value, "_nur_lesen", False),
            }
        if type(value).__name__ == "Kraftmodell":
            return {
                name: cls._wert_abbilden(getattr(value, name))
                for name in (
                    "linear_widerstand", "quadratischer_widerstand",
                    "fluidgeschwindigkeit", "fluidwinkelgeschwindigkeit",
                    "added_mass_diagonal", "masse", "g", "fremdkraft",
                )
            }
        if type(value).__name__ == "KraftmodellMitHydroCache":
            return {
                "interval": value.intervall,
                "model": cls._wert_abbilden(value.kraftmodell),
            }
        slots = getattr(type(value), "__slots__", ())
        if isinstance(slots, str):
            slots = (slots,)
        if slots:
            return {
                name: cls._wert_abbilden(getattr(value, name))
                for name in slots
                if hasattr(value, name)
            }
        if isinstance(value, dict):
            return {
                str(key): cls._wert_abbilden(item)
                for key, item in value.items()
                if not isinstance(item, QWidget)
            }
        if isinstance(value, (tuple, list)):
            return [cls._wert_abbilden(item) for item in value]
        if isinstance(value, QWidget):
            if not qt_object_is_valid(value):
                return {"type": type(value).__name__, "valid": False}
            return {
                "type": type(value).__name__,
                "object_name": value.objectName(),
                "visible": value.isVisible(),
                "enabled": value.isEnabled(),
            }
        if isinstance(value, QTreeWidgetItem):
            return {"type": type(value).__name__, "text": value.text(0)}
        return {"type": type(value).__name__}

    @staticmethod
    def _combo_setzen(widget, value, control_id):
        if isinstance(value, int) and not isinstance(value, bool):
            if not 0 <= value < widget.count():
                raise ValueError(
                    "Index ausserhalb des Bereichs fuer %s: %s"
                    % (control_id, value))
            widget.setCurrentIndex(value)
            return
        for index in range(widget.count()):
            if (widget.itemText(index) == value
                    or widget.itemData(index) == value):
                widget.setCurrentIndex(index)
                return
        raise ValueError(
            "Option %r ist fuer %s nicht vorhanden" % (value, control_id))


__all__ = ["GUIControlAPI"]
