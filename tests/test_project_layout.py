from importlib.util import find_spec
from pathlib import Path

import segelphysik


def test_segelphysik_package_is_loaded_from_python_directory():
    code_directory = (
        Path(__file__).resolve().parents[1] / "code" / "python" / "segelphysik"
    )
    assert Path(segelphysik.__path__[0]) == code_directory
    assert find_spec("segelphysik.gui.app") is not None


def test_shared_resources_stay_outside_language_directories():
    from segelphysik.core.boot_bau import MODELL_ORDNER
    from segelphysik.core.einstellungen import standard_ordner
    from segelphysik.gui.app import _finde_koerper_json

    root = Path(__file__).resolve().parents[1]
    assert Path(MODELL_ORDNER) == root / "code" / "modelle"
    assert Path(standard_ordner()) == root / "konfigurationen"
    assert Path(_finde_koerper_json()) == root / "konfigurationen" / "koerper.json"
    assert (root / "code" / "cpp" / "README.md").is_file()


def test_resources_are_independent_of_working_directory(tmp_path, monkeypatch):
    from segelphysik.core.boot_bau import MODELL_ORDNER
    from segelphysik.core.einstellungen import standard_ordner
    from segelphysik.gui.app import _finde_koerper_json

    monkeypatch.chdir(tmp_path)
    root = Path(__file__).resolve().parents[1]
    assert Path(MODELL_ORDNER) == root / "code" / "modelle"
    assert Path(standard_ordner()) == root / "konfigurationen"
    assert Path(_finde_koerper_json()) == root / "konfigurationen" / "koerper.json"
