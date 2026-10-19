"""Punktfeld mit Schattenspuren fuer die Wasserbewegung (rein rechnerisch).

Der Koerper bleibt im Bild zentriert (Kamera folgt). Damit die Bewegung
sichtbar bleibt, liegt ein weltfestes Punktfeld auf dem Wasser. Relativ zur
mitlaufenden Kamera ziehen die Punkte gegen die Fahrtrichtung vorbei und
hinterlassen Spuren, die zum Ende hin ausgrauen.

Das Feld kennt nur Weltkoordinaten. Spaeter lassen sich Wellen ueber
``hoehe(x, y)`` (Punkt-z) einbinden.
"""
import numpy as np


def _hash01(ix, iy, salz):
    """Deterministischer Pseudozufall in [0, 1) je Gitterzelle."""
    h = (ix * 73856093) ^ (iy * 19349663) ^ (salz * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


KACHEL_ZELLEN = 16
ABSTAND = 1.5
KACHEL_METER = KACHEL_ZELLEN * ABSTAND


def punktlage(gx, gy, abstand=ABSTAND):
    """Weltposition des Punkts der Zelle (gx, gy); periodisch in der
    Kachel, damit Textur und Spuren dieselben Punkte meinen."""
    hx = _hash01(gx % KACHEL_ZELLEN, gy % KACHEL_ZELLEN, 1)
    hy = _hash01(gx % KACHEL_ZELLEN, gy % KACHEL_ZELLEN, 2)
    return ((gx + 0.8 * (hx - 0.5)) * abstand,
            (gy + 0.8 * (hy - 0.5)) * abstand)


DUNST_FARBE = (200, 220, 238)


def dunst_gitter(r_innen=30.0, r_aussen=2000.0, hoehe=600.0, ringe=28,
                 hoehenstufen=8, segmente=96, z_basis=-0.05, farbe=DUNST_FARBE):
    """Dunstverlauf: Ring auf dem Wasser (transparent -> Dunstfarbe zum
    Horizont) plus Wand am Horizont, die nach oben in den Himmel ausblendet.
    Liefert (punkte (N,3), flaechen (M,4), rgba (N,4) uint8)."""
    zeilen = []   # (radius, z, alpha)
    radien = np.geomspace(r_innen, r_aussen, ringe)
    for r in radien:
        t = np.log(r / r_innen) / np.log(r_aussen / r_innen)
        zeilen.append((r, z_basis + 0.0005 * r, 0.97 * t ** 0.8))
    z_ende = z_basis + 0.0005 * r_aussen
    for h in np.linspace(0.0, 1.0, hoehenstufen + 1)[1:]:
        zeilen.append((r_aussen, z_ende + h * hoehe, 0.97 * (1.0 - h) ** 1.5))
    w = np.linspace(0.0, 2.0 * np.pi, segmente, endpoint=False)
    pts = []
    rgba = []
    for r, z, a in zeilen:
        pts.append(np.column_stack([r * np.cos(w), r * np.sin(w),
                                    np.full(segmente, z)]))
        c = np.empty((segmente, 4), dtype=np.uint8)
        c[:, :3] = farbe
        c[:, 3] = int(round(255 * a))
        rgba.append(c)
    punkte = np.vstack(pts)
    flaechen = []
    for i in range(len(zeilen) - 1):
        for j in range(segmente):
            j2 = (j + 1) % segmente
            flaechen.append([4, i * segmente + j, i * segmente + j2,
                             (i + 1) * segmente + j2, (i + 1) * segmente + j])
    return punkte, np.array(flaechen, dtype=np.int64), np.vstack(rgba)


class WasserPunktFeld:
    def __init__(self, radius=12.0, abstand=ABSTAND, historie=12,
                 spur_punkte=6, hoehe=None, z0=-0.02):
        self.radius = float(radius)
        self.abstand = float(abstand)
        self.historie = max(2, int(historie))
        self.spur_punkte = max(2, int(spur_punkte))
        self.hoehe = hoehe
        self.z0 = float(z0)
        self._verlauf = []

    def zuruecksetzen(self):
        self._verlauf = []

    def punkte_welt(self, zentrum):
        """Weltfeste Punkte im Quadrat um ``zentrum`` und Randtransparenz."""
        a, r = self.abstand, self.radius
        cx, cy = float(zentrum[0]), float(zentrum[1])
        ix = np.arange(int(np.floor((cx - r) / a)), int(np.ceil((cx + r) / a)) + 1)
        iy = np.arange(int(np.floor((cy - r) / a)), int(np.ceil((cy + r) / a)) + 1)
        gx, gy = np.meshgrid(ix, iy, indexing="ij")
        gx = gx.ravel(); gy = gy.ravel()
        x, y = punktlage(gx, gy, a)
        d = np.hypot(x - cx, y - cy)
        innen = d <= r
        x, y, d = x[innen], y[innen], d[innen]
        z = np.full_like(x, self.z0)
        if self.hoehe is not None:
            z = z + np.asarray(self.hoehe(x, y), dtype=float)
        rand = np.clip((r - d) / (0.35 * r), 0.0, 1.0)
        return np.column_stack([x, y, z]), rand

    def aktualisieren(self, zentrum):
        """Nimmt eine neue Koerperposition auf und liefert
        (punkte (N,3), spuren (N, S, 3), alpha (N, S)).
        Spur-Index 0 = Punkt selbst (voll sichtbar), letzter = Spurende (0)."""
        c = np.array([float(zentrum[0]), float(zentrum[1])])
        self._verlauf.append(c)
        if len(self._verlauf) > self.historie:
            self._verlauf.pop(0)
        punkte, rand = self.punkte_welt(c)
        n = len(self._verlauf)
        s = self.spur_punkte
        # S Stuetzstellen im Verlauf, 0 = jetzt, letzter = aeltester Eintrag
        idx = np.round(np.linspace(n - 1, 0, s)).astype(int)
        # Spurpunkt = Punkt + (Zentrum jetzt - Zentrum frueher)
        versatz = c[None, :] - np.array([self._verlauf[i] for i in idx])
        spuren = np.repeat(punkte[:, None, :], s, axis=1)
        spuren[:, :, 0:2] += versatz[None, :, :]
        verlauf_alpha = np.linspace(1.0, 0.0, s) ** 1.5
        alpha = rand[:, None] * verlauf_alpha[None, :]
        return punkte, spuren, alpha
