"""Expose the application package stored in the repository's ``code`` folder."""
from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent / "code")]
