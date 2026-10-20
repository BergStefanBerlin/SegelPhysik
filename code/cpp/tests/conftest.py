import pytest

from segelphysik.core.rechenpfad import python_referenz


@pytest.fixture(autouse=True)
def unabhaengige_python_referenz():
    with python_referenz():
        yield
