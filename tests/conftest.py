"""GUI-Tests duerfen die persoenliche Anwendungskonfiguration nicht migrieren."""
from pathlib import Path
import uuid

import pytest

from segelphysik.core.einstellungen import Einstellungen


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


@pytest.fixture
def profildatei():
    datei = Path(".pytest_cache") / ("worker-" + uuid.uuid4().hex + ".jsonl")
    datei.parent.mkdir(exist_ok=True)
    try:
        yield datei
    finally:
        datei.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def isolierte_anwendungseinstellungen(tmp_path, monkeypatch):
    laden = Einstellungen.laden.__func__

    def testdatei_laden(cls, pfad=None, vorlage=None):
        if pfad is None:
            pfad = str(tmp_path / "anwendungssettings" / "settings.json")
        return laden(cls, pfad, vorlage)

    monkeypatch.setattr(Einstellungen, "laden", classmethod(testdatei_laden))
