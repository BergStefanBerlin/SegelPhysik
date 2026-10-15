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


def textur_bild(pixel=1024, grund=(44, 106, 153), punkt=(235, 245, 252),
                radius_px=3.0):
    """Kachelbares RGB-Bild: Wasserfarbe mit weichen Punkten."""
    bild = np.empty((pixel, pixel, 3), dtype=np.float64)
    bild[:] = grund
    zelle = pixel / KACHEL_ZELLEN
    yy, xx = np.mgrid[0:pixel, 0:pixel]
    for gx in range(KACHEL_ZELLEN):
        for gy in range(KACHEL_ZELLEN):
            px, py = punktlage(gx, gy, 1.0)
            cx = (px % KACHEL_ZELLEN) * zelle
            cy = (py % KACHEL_ZELLEN) * zelle
            x0 = int(cx) - 6; y0 = int(cy) - 6
            for ox in (-pixel, 0, pixel):
                for oy in (-pixel, 0, pixel):
                    xs = slice(max(0, x0 + ox), min(pixel, x0 + ox + 13))
                    ys = slice(max(0, y0 + oy), min(pixel, y0 + oy + 13))
                    if xs.start >= xs.stop or ys.start >= ys.stop:
                        continue
                    d = np.hypot(xx[ys, xs] - (cx + ox), yy[ys, xs] - (cy + oy))
                    w = np.clip(radius_px + 0.5 - d, 0.0, 1.0)[..., None]
                    bild[ys, xs] = bild[ys, xs] * (1 - w) + np.array(punkt) * w
    return bild.astype(np.uint8)


class WasserPunktFeld:
    def __init__(self, radius=12.0, abstand=ABSTAND, historie=12,
                 spur_punkte=6, hoehe=None, z0=0.02):
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
