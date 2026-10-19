"""Expose the application package stored in ``code/python/segelphysik``."""
from pathlib import Path

__path__ = [
    str(Path(__file__).resolve().parent / "code" / "python" / "segelphysik")
]
