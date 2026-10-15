"""Wasserbewegung: Koerper zentriert, weltfestes Punktfeld mit Spuren."""
import numpy as np

from segelphysik.core.wasserpunkte import WasserPunktFeld
from segelphysik.grafik_bruecke import GrafikBruecke


def test_punkte_sind_weltfest_und_liegen_im_radius():
    feld = WasserPunktFeld(radius=10.0, abstand=1.5)
    p1, _ = feld.punkte_welt((0.0, 0.0))
    p2, _ = feld.punkte_welt((0.7, 0.2))
    assert len(p1) > 100
    assert np.all(np.hypot(p1[:, 0], p1[:, 1]) <= 10.0 + 1e-9)
    # gleiche Gitterzelle -> identische Weltposition (kein Mitwandern)
    gemeinsam = {tuple(np.round(p, 9)) for p in p1} \
        & {tuple(np.round(p, 9)) for p in p2}
    assert len(gemeinsam) > 0.5 * len(p1)


def test_spuren_zeigen_gegen_die_fahrt_und_graun_aus():
    feld = WasserPunktFeld(historie=10, spur_punkte=5)
    for i in range(10):
        punkte, spuren, alpha = feld.aktualisieren((0.5 * i, 0.0))
    # Spurende liegt in +x (Koerper fuhr +x, Punkt zieht nach -x vorbei
    # und die Spur bleibt hinter ihm, also bei groesserem x)
    assert np.all(spuren[:, -1, 0] > spuren[:, 0, 0])
    assert np.allclose(spuren[:, -1, 0] - spuren[:, 0, 0], 4.5)
    assert np.all(np.diff(alpha, axis=1) <= 1e-12)
    assert np.allclose(alpha[:, -1], 0.0)


def test_spur_verschwindet_im_stand():
    feld = WasserPunktFeld(historie=5, spur_punkte=4)
    for i in range(3):
        feld.aktualisieren((float(i), 0.0))
    for _ in range(6):
        _, spuren, _ = feld.aktualisieren((2.0, 0.0))
    assert np.allclose(spuren[:, :, 0], spuren[:, :1, 0])


def test_hoehenfunktion_hebt_punkte():
    feld = WasserPunktFeld(hoehe=lambda x, y: 0.1 * np.ones_like(x), z0=0.0)
    punkte, _ = feld.punkte_welt((0.0, 0.0))
    assert np.allclose(punkte[:, 2], 0.1)


def test_bruecke_kamera_folgt_dem_koerper():
    pv = __import__("pyvista")
    bruecke = GrafikBruecke()
    bruecke._renderer = type("R", (), {"_surf_actor": None})()
    bruecke._plotter = pv.Plotter(off_screen=True)
    bruecke._koerper["b"] = {
        "pd": pv.Sphere(), "aktiv": True, "position": np.zeros(3)}
    bruecke._koerper["b"]["pd"]["referenz_punkte"] = \
        bruecke._koerper["b"]["pd"].points.copy()
    bruecke._statisch_anwenden = lambda *a, **k: None
    assert bruecke.wasser_bewegung_setzen(True)
    bruecke._plotter.camera_position = [(5, -5, 3), (0, 0, 0), (0, 0, 1)]
    bruecke.physik_pose_6dof_setzen("b", np.eye(3), np.array([1.0, 2.0, 0.0]))
    bruecke.physik_pose_6dof_setzen("b", np.eye(3), np.array([4.0, 6.0, 0.0]))
    fokus = np.asarray(bruecke._plotter.camera.focal_point)
    assert np.allclose(fokus[:2], [3.0, 4.0])   # nur Differenz seit 1. Pose
    assert "wasser_spuren" in bruecke._plotter.actors
    assert bruecke._ozean_actor is not None
    assert np.allclose(bruecke._ozean_actor.GetPosition()[:2], [4.0, 6.0])
    tc = np.asarray(bruecke._ozean_mesh.active_texture_coordinates)
    erwartet = (np.asarray(bruecke._ozean_mesh.points)[:, :2]
                + [4.0, 6.0]) / bruecke._ozean_kachel
    assert np.allclose(tc, erwartet, atol=1e-3)
    assert bruecke.wasser_bewegung_setzen(False)
    assert bruecke._ozean_actor is None
    assert "wasser_spuren" not in bruecke._plotter.actors
    bruecke._plotter.close()


def test_textur_ist_kachelbar_und_punkte_passen_zu_spuren():
    from segelphysik.core.wasserpunkte import (textur_bild, punktlage,
                                               KACHEL_ZELLEN)
    bild = textur_bild(pixel=256)
    assert bild.shape == (256, 256, 3)
    # Punkt einer Zelle liegt an der Texturstelle seiner Weltposition
    zelle = 256 / KACHEL_ZELLEN
    px, py = punktlage(3, 5, 1.0)
    x = int((px % KACHEL_ZELLEN) * zelle)
    y = int((py % KACHEL_ZELLEN) * zelle)
    grund = bild[0, 0].astype(int)
    assert bild[y, x].sum() > grund.sum() + 100
    # periodisch: Zelle + Kachel hat dieselbe Lage (modulo Kachel)
    qx, qy = punktlage(3 + KACHEL_ZELLEN, 5, 1.0)
    assert np.isclose(qx - px, KACHEL_ZELLEN)
    assert np.isclose(qy, py)

def test_dunst_gitter_blendet_zum_horizont_ein_und_nach_oben_aus():
    from segelphysik.core.wasserpunkte import dunst_gitter
    punkte, flaechen, rgba = dunst_gitter(ringe=10, hoehenstufen=4, segmente=16)
    assert punkte.shape == (14 * 16, 3) and rgba.shape == (14 * 16, 4)
    assert flaechen.shape == (13 * 16, 5) and (flaechen[:, 0] == 4).all()
    alpha = rgba[:, 3].reshape(14, 16)[:, 0]
    assert alpha[0] == 0 and alpha[9] > 200 and alpha[-1] == 0
    assert (np.diff(alpha[:10]) >= 0).all()