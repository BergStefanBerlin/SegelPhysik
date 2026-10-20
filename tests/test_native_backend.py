from types import SimpleNamespace

import pytest

from segelphysik.core import native_backend


def _modul():
    modul = SimpleNamespace(
        ABI_VERSION=1, RECHENPFAD="cpp/datenschicht",
        **{name: object() for name in native_backend.DATENTYPEN + native_backend.FUNKTIONEN})
    for klasse, methoden in native_backend.METHODEN.items():
        setattr(modul, klasse, SimpleNamespace(**{name: lambda: None for name in methoden}))
    return modul


def test_native_laden_ist_explizit_und_prueft_den_vertrag(monkeypatch):
    modul = _modul()
    namen = []

    def laden(name):
        namen.append(name)
        return modul

    monkeypatch.setattr(native_backend.importlib, "import_module", laden)
    assert native_backend.native_laden() is modul
    assert namen == ["_segelphysik_native"]


@pytest.mark.parametrize("fehler", [ModuleNotFoundError("fehlt"), OSError("DLL fehlt")])
def test_native_ladefehler_werden_nicht_durch_referenz_erfolg_ersetzt(monkeypatch, fehler):
    def laden(name):
        raise fehler

    monkeypatch.setattr(native_backend.importlib, "import_module", laden)
    with pytest.raises(native_backend.NativeBackendFehler, match="nicht automatisch") as exc:
        native_backend.native_laden()
    assert exc.value.__cause__ is fehler


@pytest.mark.parametrize("mutation", ["abi", "export", "rechenpfad", "methode"])
def test_native_inkompatibilitaet_wird_explizit_abgewiesen(monkeypatch, mutation):
    modul = _modul()
    if mutation == "abi":
        modul.ABI_VERSION = 999
    elif mutation == "export":
        del modul.Ergebnis
    elif mutation == "methode":
        del modul.StatikKontext.stationaere_dynamik
    else:
        modul.RECHENPFAD = "python"
    monkeypatch.setattr(native_backend.importlib, "import_module", lambda name: modul)
    with pytest.raises(native_backend.NativeBackendFehler):
        native_backend.native_laden()
