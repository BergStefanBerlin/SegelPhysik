import json
from pathlib import Path

import numpy as np
import pytest

from segelphysik.core.auftrieb import baue_kraftfunktion
from segelphysik.core.fabriken import baue_summenkoerper
from segelphysik.core.hydrodynamik import (
    HydrodynamikModell,
    hydrodynamik_teile_aus_koerper,
    hydrodynamik_testprofil,
    wasserlinienlaenge_m,
)
from segelphysik.core.konfig_lader import lade_konfig, lade_physik
from segelphysik.core.kraftmodell import baue_kraftmodell
from segelphysik.core.statisch_robust import loese_robust
from segelphysik.core.stationaer_hydrodynamik import (
    loese_stationaer,
    pruefe_stationaer_dynamisch,
)


@pytest.mark.parametrize("koerper_id", ("rolle", "platte", "unregelmaessig"))
def test_generische_schwimmkoerper_haben_synchrone_dichte_in_konfig_und_paket(
        koerper_id):
    wurzel = Path(__file__).resolve().parents[1]
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    manifest_pfad = (
        wurzel / "code" / "modelle" / koerper_id / "modell.json")
    manifest = json.loads(manifest_pfad.read_text(encoding="utf-8"))
    dichte_konfiguration = konfiguration.summenkoerper[koerper_id][
        "dichte_kg_pro_m3"]
    dichte_manifest = manifest["koerper"]["dichte_kg_pro_m3"]

    assert dichte_konfiguration == dichte_manifest
    assert dichte_konfiguration < konfiguration.wasser_dichte()


@pytest.mark.parametrize(
    "koerper_id",
    (
        "kegel", "quader", "pyramide", "kugel",
        "rolle", "platte", "bleistift", "unregelmaessig",
    ),
)
def test_generische_defaultprofile_erzeugen_endlichen_dissipativen_widerstand(
        koerper_id):
    wurzel = Path(__file__).resolve().parents[1]
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    profil = konfiguration.hydrodynamik_profile[koerper_id]
    koerper, _versatz = baue_summenkoerper(konfiguration, koerper_id)
    snapshot = koerper.snapshot()
    modell = HydrodynamikModell.aus_koerper(
        snapshot,
        rho_kg_m3=konfiguration.wasser_dichte(),
        cd_volumenkoerper=profil["cd_volumenkoerper"],
    )

    assert modell is not None
    beitraege = modell.beitraege_erzeugen(
        (0.0, 0.0, 0.0), v=(1.0, 0.0, 0.0))
    kraft = sum(
        (np.asarray(beitrag.wrench.kraft_N) for beitrag in beitraege),
        np.zeros(3),
    )

    assert beitraege
    assert np.isfinite(kraft).all()
    assert np.dot(kraft, (1.0, 0.0, 0.0)) < 0.0


def test_plattenprofil_besteht_stationaere_und_dynamische_pruefung():
    wurzel = Path(__file__).resolve().parents[1]
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    physik = lade_physik(wurzel / "konfigurationen")
    profil = konfiguration.hydrodynamik_profile["platte"]
    koerper, _versatz = baue_summenkoerper(konfiguration, "platte")
    snapshot = koerper.snapshot()
    hydrodynamik = HydrodynamikModell.aus_koerper(
        snapshot,
        rho_kg_m3=konfiguration.wasser_dichte(),
        cd_volumenkoerper=profil["cd_volumenkoerper"],
    )
    hydrostatik = baue_kraftfunktion(
        snapshot,
        rho_w=konfiguration.wasser_dichte(),
        g=physik.g_m_pro_s2,
        aufloesung=physik.voxel_aufloesung_m,
        pfad="exakt_union",
    )
    kraftmodell = baue_kraftmodell(
        hydrostatik, physik, masse=snapshot.masse,
        g=physik.g_m_pro_s2, hydrodynamik=hydrodynamik)
    kraftmodell.fremdkraft_setzen((
        profil["testkraft_N"], profil["angriffspunkt_m"]))
    hydrostatisches_gleichgewicht = loese_robust(
        hydrostatik, snapshot.masse, g=physik.g_m_pro_s2,
        tol=1e-8, max_iter=60, stagnation_anteil=0.05)
    laenge = max(np.ptp(
        np.concatenate([punkte for punkte, _ in snapshot.blatt_meshes]),
        axis=0))

    stationaer = loese_stationaer(
        kraftmodell,
        charakteristische_kraft_N=np.linalg.norm(profil["testkraft_N"]),
        charakteristische_laenge_m=laenge,
        referenzgeschwindigkeit_m_s=(
            profil["referenzgeschwindigkeit_m_pro_s"]),
        start=(profil["referenzgeschwindigkeit_m_pro_s"],
               hydrostatisches_gleichgewicht["z"], 0.0, 0.0,
               hydrostatisches_gleichgewicht["phi"], 0.0),
    )
    dynamik = pruefe_stationaer_dynamisch(
        kraftmodell, stationaer.stufen[-1],
        masse_kg=snapshot.masse,
        traegheit_koerper=snapshot.traegheitstensor,
        charakteristische_laenge_m=laenge,
        dt_s=physik.dt_s, g_m_pro_s2=physik.g_m_pro_s2)

    assert stationaer.konvergiert
    assert stationaer.stufen[-1].normierte_restkraft <= 0.01
    assert stationaer.stufen[-1].normiertes_restmoment <= 0.01
    assert dynamik.simulierte_dauer_s == pytest.approx(10.0)
    assert dynamik.bestanden
    assert dynamik.fehlergrund is None


def test_yacht1_testprofil_erreicht_stabiles_gleichgewicht_unter_rumpfgeschwindigkeit():
    wurzel = Path(__file__).resolve().parents[1]
    konfiguration = lade_konfig(wurzel / "konfigurationen")
    koerper, _versatz = baue_summenkoerper(konfiguration, "yacht1")
    snapshot = koerper.snapshot()
    physik = lade_physik(wurzel / "konfigurationen")
    profil = hydrodynamik_testprofil(
        "yacht1", konfiguration.hydrodynamik_profile["yacht1"])
    assert profil is not None

    hydrodynamik = HydrodynamikModell.aus_koerper(
        snapshot,
        rho_kg_m3=konfiguration.wasser_dichte(),
        fluidgeschwindigkeit=physik.fluidgeschwindigkeit,
        fluidwinkelgeschwindigkeit=physik.fluidwinkelgeschwindigkeit,
        ruderwinkel_rad=np.deg2rad(profil.ruderwinkel_grad),
    )
    hydrostatik = baue_kraftfunktion(
        snapshot,
        rho_w=konfiguration.wasser_dichte(),
        g=physik.g_m_pro_s2,
        aufloesung=physik.voxel_aufloesung_m,
        pfad="exakt_union",
    )
    kraftfunktion = baue_kraftmodell(
        hydrostatik, physik, masse=snapshot.masse,
        g=physik.g_m_pro_s2, hydrodynamik=hydrodynamik)
    azimut = np.deg2rad(profil.azimut_grad)
    elevation = np.deg2rad(profil.elevation_grad)
    kraftfunktion.fremdkraft_setzen((
        (
            profil.kraft_betrag_N * np.cos(elevation) * np.cos(azimut),
            profil.kraft_betrag_N * np.cos(elevation) * np.sin(azimut),
            profil.kraft_betrag_N * np.sin(elevation),
        ),
        profil.angriffspunkt_m,
    ))

    statisch = loese_robust(
        kraftfunktion, snapshot.masse, g=physik.g_m_pro_s2,
        tol=1e-8, max_iter=60, stagnation_anteil=0.05)
    rumpflaenge = wasserlinienlaenge_m(
        hydrodynamik_teile_aus_koerper(snapshot),
        z_m=statisch["z"], phi_rad=statisch["phi"])
    assert rumpflaenge == pytest.approx(3.78865, abs=0.02)
    hull_speed_m_s = 1.34 * 0.514444 * np.sqrt(rumpflaenge / 0.3048)
    referenz_m_s = 0.8 * hull_speed_m_s
    stationaer = loese_stationaer(
        kraftfunktion,
        charakteristische_kraft_N=profil.kraft_betrag_N,
        charakteristische_laenge_m=rumpflaenge,
        referenzgeschwindigkeit_m_s=referenz_m_s,
        start=(referenz_m_s, statisch["z"], 0.0, 0.0,
               statisch["phi"], 0.0),
        ruderwinkel_rad=np.deg2rad(profil.ruderwinkel_grad),
    )
    dynamik = pruefe_stationaer_dynamisch(
        kraftfunktion, stationaer.stufen[-1],
        masse_kg=snapshot.masse,
        traegheit_koerper=snapshot.traegheitstensor,
        charakteristische_laenge_m=rumpflaenge,
        dt_s=physik.dt_s, g_m_pro_s2=physik.g_m_pro_s2)

    geschwindigkeit = stationaer.stufen[-1].geschwindigkeit_m_s[0]
    assert stationaer.konvergiert
    assert geschwindigkeit < hull_speed_m_s
    assert geschwindigkeit == pytest.approx(referenz_m_s, rel=0.02)
    assert stationaer.stufen[-1].normierte_restkraft <= 0.01
    assert stationaer.stufen[-1].normiertes_restmoment <= 0.01
    assert dynamik.simulierte_dauer_s == pytest.approx(10.0)
    assert dynamik.bestanden
