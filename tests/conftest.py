"""GUI-Tests duerfen die persoenliche Anwendungskonfiguration nicht migrieren."""
import pytest

from segelphysik.core.einstellungen import Einstellungen


@pytest.fixture(autouse=True)
def isolierte_anwendungseinstellungen(tmp_path, monkeypatch):
    laden = Einstellungen.laden.__func__

    def testdatei_laden(cls, pfad=None, vorlage=None):
        if pfad is None:
            pfad = str(tmp_path / "anwendungssettings" / "settings.json")
        return laden(cls, pfad, vorlage)

    monkeypatch.setattr(Einstellungen, "laden", classmethod(testdatei_laden))
