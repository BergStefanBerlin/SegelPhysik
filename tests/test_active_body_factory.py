"""C-7: ausgewaehlte Baum-Blaetter bestimmen die Koerperfabrik."""
from types import SimpleNamespace

from segelphysik.core import fabriken


class _Konfig:
    def __init__(self):
        self.protokoll = []

    def dichte_von(self, _material):
        return 1000.0

    def farben_von(self, _material):
        return "#ffffff", "#888888"

    def glanz_von(self, _material):
        return 0.2


def test_specs_enthalten_nur_aktive_blaetter(monkeypatch):
    monkeypatch.setattr(
        fabriken.boot_bau, "baue_teil",
        lambda _name, **_kwargs: ([], []))
    eintraege = [
        {"name": "rumpf", "material": "GfK"},
        {"name": "rigg", "teile": [
            {"name": "mast", "material": "Aluminium"},
            {"name": "segel", "material": "Tuch"},
        ]},
    ]

    specs = fabriken._specs_aus_konfig(
        eintraege, _Konfig(), 1.0, "nicht-verwendet",
        aktive_namen={"mast"})

    assert len(specs) == 1
    assert specs[0]["teile"][0]["_name"] == "mast"


def test_summenkoerper_mit_allem_abgewaehlten_blaettern_meldet_fehler(
        monkeypatch):
    konfig = SimpleNamespace(
        summenkoerper={"yacht1": {"teile": []}})
    monkeypatch.setattr(fabriken, "_specs_aus_konfig",
                        lambda *_args, **_kwargs: [])

    try:
        fabriken.baue_summenkoerper(
            konfig, "yacht1", aktive_blaetter=set())
    except ValueError as fehler:
        assert "keine aktiven Unterobjekte" in str(fehler)
    else:
        raise AssertionError("Leerer aktiver Koerper muss abgelehnt werden")


def test_summenkoerper_protokolliert_nur_die_aktiven_blaetter(monkeypatch):
    class _DummyKoerper:
        masse = 2.0
        _r_eingabe = [0.0, 0.0, 0.0]

        def __init__(self, **_kwargs):
            self.masse = 2.0

        @classmethod
        def verband(cls, *_args, **_kwargs):
            return cls()

    konfig = _Konfig()
    konfig.summenkoerper = {
        "yacht1": {"teile": [
            {"name": "rumpf", "material": "GfK"},
            {"name": "rigg", "teile": [
                {"name": "mast", "material": "Aluminium"},
                {"name": "segel", "material": "Tuch"},
            ]},
        ]},
    }
    konfig.farbe_standard = "#ffffff"
    konfig.delta_helligkeit = 0.2
    aufruf = {}
    monkeypatch.setattr(fabriken, "Koerper", _DummyKoerper)
    monkeypatch.setattr(
        fabriken, "_specs_aus_konfig",
        lambda *_args, **kwargs: (
            aufruf.update(kwargs)
            or [{"teile": [{"form": ([], []), "_name": "mast"}]}]))

    fabriken.baue_summenkoerper(
        konfig, "yacht1",
        aktive_blaetter=[SimpleNamespace(name="mast")])

    assert aufruf["aktive_namen"] == {"mast"}
    assert any("mast:" in zeile for zeile in konfig.protokoll)
    assert not any("rumpf:" in zeile or "segel:" in zeile
                   for zeile in konfig.protokoll)
