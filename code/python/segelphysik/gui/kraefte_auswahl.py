"""Klickauswahl ohne Aenderung der vorhandenen Kamera-Dragbedienung."""
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QMenu


class KraefteAuswahlFilter(QObject):
    def __init__(self, ansicht, bruecke, wertefenster):
        super().__init__(ansicht)
        self.ansicht = ansicht
        self.bruecke = bruecke
        self.wertefenster = wertefenster
        self._start = None
        ansicht.installEventFilter(self)

    def eventFilter(self, objekt, ereignis):
        art = ereignis.type()
        if art in (QEvent.Type.Resize, QEvent.Type.Show,
                   QEvent.Type.ScreenChangeInternal, QEvent.Type.DevicePixelRatioChange):
            self.bruecke._kraftkamera_geaendert()
        if (art == QEvent.Type.MouseButtonPress
                and ereignis.button() == Qt.MouseButton.LeftButton
                and ereignis.modifiers() == Qt.KeyboardModifier.NoModifier):
            self._start = ereignis.position()
        elif art == QEvent.Type.MouseButtonRelease and self._start is not None:
            start, self._start = self._start, None
            if (ereignis.button() == Qt.MouseButton.LeftButton
                    and (ereignis.position() - start).manhattanLength() <= 3):
                self._waehlen(ereignis.position(), ereignis.globalPosition())
        return False

    def _waehlen(self, position, global_position):
        zeichner = self.bruecke._kraftzeichner()
        kandidaten = zeichner.kandidaten(
            (position.x(), self.ansicht.height() - position.y()))
        if len(kandidaten) == 1:
            self._setzen(kandidaten[0])
        elif kandidaten:
            menue = QMenu(self.ansicht)
            menue.setTitle("Mehrere Kraft-/Momentenbeitraege")
            for id_ in kandidaten:
                action = menue.addAction(id_[0] + " / " + id_[1])
                action.triggered.connect(lambda _an=False, id_=id_: self._setzen(id_))
            menue.exec(global_position.toPoint())
            menue.deleteLater()

    def _setzen(self, id_):
        self.wertefenster.auswaehlen(id_)
        self.bruecke.kraefte_auswahl_setzen(id_)
