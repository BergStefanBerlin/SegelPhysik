from pathlib import Path

import numpy as np

from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.konfig_lader import lade_konfig
from segelphysik.core.modell_lader import lade_modellpaket
from segelphysik.core.segler_einstellungen import SeglerEinstellungen
from segelphysik.gui.baum import finde, welt_aus_konfig


_WURZEL = Path(__file__).resolve().parents[1]
_PAKET = _WURZEL / "code" / "modelle" / "folkeboot"


def test_folkeboot_naeherung_wird_geladen_und_ist_in_der_gui_auffindbar():
    konfig = lade_konfig(_WURZEL / "konfigurationen")
    konfig.segler_einstellungen = SeglerEinstellungen()
    paket = lade_modellpaket(_PAKET, konfig.materialien_blocks)
    welt = welt_aus_konfig(konfig)
    eintrag = finde(welt, "folkeboot")

    assert eintrag is not None
    assert eintrag.label == "Nordisches Folkeboot (Näherung)"
    assert set(paket.meshes) == {
        "rumpf", "kiel", "ruder", "mast", "grossbaum",
        "grosssegel", "fock",
    }
    np.testing.assert_allclose(
        np.ptp(paket.meshes["rumpf"].punkte_si, axis=0),
        [7.68, 2.20, 1.09],
        atol=1e-6,
    )
    np.testing.assert_allclose(
        np.ptp(paket.meshes["kiel"].punkte_si, axis=0),
        [0.84, 0.16, 0.88],
        atol=1e-6,
    )
    np.testing.assert_allclose(
        np.ptp(paket.meshes["mast"].punkte_si, axis=0)[2],
        10.17,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        np.ptp(paket.meshes["grossbaum"].punkte_si, axis=0)[0],
        3.37,
        atol=1e-6,
    )
    assert np.ptp(paket.meshes["grosssegel"].punkte_si[:, 0]) > 3.0
    assert np.ptp(paket.meshes["grosssegel"].punkte_si[:, 2]) > 9.0
    assert np.ptp(paket.meshes["fock"].punkte_si[:, 0]) > 2.8
    assert np.ptp(paket.meshes["fock"].punkte_si[:, 2]) > 9.0

    koerper, _ = baue_summenkoerper(konfig, "folkeboot")
    assert 0.0 < koerper.masse < 2500.0
