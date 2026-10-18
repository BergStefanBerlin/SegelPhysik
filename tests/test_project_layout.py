from importlib.util import find_spec
from pathlib import Path

import segelphysik


def test_segelphysik_package_is_loaded_from_code_directory():
    code_directory = Path(__file__).resolve().parents[1] / "code"
    assert Path(segelphysik.__path__[0]) == code_directory
    assert find_spec("segelphysik.gui.app") is not None
