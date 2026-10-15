"""Grafik-Optimierung V4 - Schritt 2 (Spec P7: K1 + K2 + K5).

Wirkt VON AUSSEN auf die fertige Render-Pipeline:
segelphysik/render/vista.py bleibt BYTEIDENTISCH (Additivprinzip).

K1  Studio-Beleuchtung (Light Kit: Key/Fill/Head/Back) + Ambient Occlusion
K2  Hintergrundverlauf (Himmelblau -> Dunstweiss), Fresnel-artiger
    Wasser-Glanz, vertiefte Beckensohle
K5  Kamera-Presets per Tastendruck mit sanftem Uebergang (Interpolation)

Grenzen (Spec V3/V4): KEINE Wellenbewegung, nichts Physik-suggerierend -
alles hier ist Deko und als solche dokumentiert. SI-Einheiten (R6).
"""
from __future__ import annotations
import numpy as np


# ---------------------------------------------------------------- K5 ----
def kamera_presets(lx=10.0, ly=10.0, d=3.0):
    """Kamera-Presets (Position, Blickpunkt, Up) - rein rechnerisch,
    ohne pyvista testbar. x = Bug, y = Backbord, z = hoch (A1).
    Seitenansichten blicken waagerecht auf Hoehe der Wasserlinie, die
    Wasserflaeche erscheint dort als Linie. Zusaetzlich die 8 Eckansichten
    "<oben|unten>_<backbord|steuerbord>_<bug|heck>"."""
    r = max(lx, ly)
    ursprung = (0.0, 0.0, 0.0)
    hoch = (0.0, 0.0, 1.0)
    presets = {
        "bug":        ((2.4 * r, 0.0, 0.0), ursprung, hoch),
        "heck":       ((-2.4 * r, 0.0, 0.0), ursprung, hoch),
        "backbord":   ((0.0, 2.4 * r, 0.0), ursprung, hoch),
        "steuerbord": ((0.0, -2.4 * r, 0.0), ursprung, hoch),
        "oben":       ((0.0, 0.0, 3.2 * d), ursprung, (0.0, 1.0, 0.0)),
        "unten":      ((0.0, 0.0, -3.2 * d), ursprung, (0.0, 1.0, 0.0)),
    }
    for hoehe, sz in (("oben", 1.0), ("unten", -1.0)):
        for seite, sy in (("backbord", 1.0), ("steuerbord", -1.0)):
            for laengs, sx in (("bug", 1.0), ("heck", -1.0)):
                presets["%s_%s_%s" % (hoehe, seite, laengs)] = (
                    (sx * 1.7 * r, sy * 1.7 * r, sz * 1.5 * d), ursprung,
                    hoch)
    return presets


class GrafikOptimierung:
    """Haelt alle Schritt-2-Erweiterungen; tick() pro Frame aufrufen."""

    ANTIQUELL = 0.12   # Interpolationsfaktor des sanften Uebergangs

    def __init__(self, bruecke):
        self._p = bruecke._plotter
        self._r = bruecke._renderer
        self._presets = kamera_presets(bruecke.app.cfg.basin["lx"],
                                       bruecke.app.cfg.basin["ly"],
                                       bruecke.app.cfg.water["depth"])
        self._ziel = None
        self.aktiv = {"licht": False, "ssao": False, "verlauf": False,
                      "wasser_glanz": False}

    # ------------------------------------------------------------ K1 ----
    def beleuchtung(self):
        """Light Kit (Studio-Beleuchtung) + SSAO, jeweils fehlvertraeglich."""
        p = self._p
        try:
            p.enable_lightkit()
            self.aktiv["licht"] = True
        except Exception as fehler:
            print("Hinweis: Light Kit nicht verfuegbar:", fehler)
        try:
            # SSAO bewusst NICHT automatisch aktivieren (Flacker-Artefakte
            # ueber halbtransparentem Wasser); Einschalten per Taste 'o'.
            pass
        except Exception as fehler:
            print("Hinweis: SSAO nicht verfuegbar (VTK zu alt?):", fehler)

    # ------------------------------------------------------------ K2 ----
    def hintergrund(self):
        """Verlauf Himmelblau (oben) -> Dunstweiss (unten) statt reinem Weiss."""
        try:
            self._p.set_background("#f2f7fc", top="#9dc3e6")
            self.aktiv["verlauf"] = True
        except Exception as fehler:
            print("Hinweis: Hintergrundverlauf nicht verfuegbar:", fehler)

    def wasser_glanz(self):
        """Fresnel-artiger Glanz auf der Wasseroberflaeche + vertiefte
        Beckensohle. Greift NUR auf Actor-Eigenschaften zu (keine Geometrie)."""
        r, p = self._r, self._p
        surf = getattr(r, "_surf", None)
        if surf is None:
            return
        actor = self._finde_actor(surf)
        if actor is None:
            return
        eig = actor.property
        eig.interpolation = "phong"
        eig.specular = 1.0          # starker Glanz (Sonnenreflex)
        eig.specular_power = 120.0  # scharfes Glanzlicht
        eig.diffuse = 0.85
        eig.ambient = 0.10
        try:
            actor.SetOpacity(0.85)  # etwas dichter -> besser sichtbar
        except Exception:
            pass
        # Beckensohle vertiefen (Tiefe lesen lassen)
        for a in list(p.actors.values()):
            daten = getattr(a, "mapper", None)
            daten = getattr(daten, "dataset", None) if daten is not None else None
            if daten is None or daten is surf:
                continue
            try:
                zmin = float(daten.bounds[4])
            except Exception:
                continue
            if abs(zmin + r.depth) < 1e-6:   # Ebene liegt auf z = -depth
                try:
                    a.GetProperty().SetColor(0.05, 0.22, 0.36)
                    a.GetProperty().SetOpacity(0.45)
                except Exception:
                    pass
        self.aktiv["wasser_glanz"] = True

    # ------------------------------------------------------------ K5 ----
    def kamera(self, name):
        """Preset anwaehlen; der Uebergang passiert weich in tick()."""
        if name in self._presets:
            self._ziel = self._presets[name]

    def ssao_umschalten(self):
        """SSAO ein-/ausschalten (Taste 'o'). Gibt Meldung zurueck."""
        try:
            if self.aktiv.get("ssao"):
                self._p.disable_ssao()
                self.aktiv["ssao"] = False
                meldung = "AUS"
            else:
                try:
                    self._p.enable_ssao(radius=0.8, bias=0.002)
                    meldung = "AN (parametriert)"
                except TypeError:
                    self._p.enable_ssao()
                    meldung = "AN (einfach)"
                self.aktiv["ssao"] = True
            print("SSAO:", meldung)
            return meldung
        except Exception as fehler:
            meldung = "nicht verfuegbar -> %s" % fehler
            print("SSAO-Umschaltung nicht moeglich:", fehler)
            return meldung

    def tick(self):
        """Sanfter Kamera-Uebergang; aus der Demo-Schleife pro Frame rufen."""
        if self._ziel is None:
            return
        p = self._p
        cam = p.camera
        pos = np.asarray(cam.position, dtype=float)
        blick = np.asarray(cam.focal_point, dtype=float)
        up = np.asarray(cam.up, dtype=float)
        zpos, zblick, zup = (np.asarray(x, dtype=float) for x in self._ziel)
        f = self.ANTIQUELL
        pos = pos + (zpos - pos) * f
        blick = blick + (zblick - blick) * f
        up = up + (zup - up) * f
        p.camera_position = [tuple(pos), tuple(blick), tuple(up)]
        if (np.max(np.abs(pos - zpos)) < 1e-3
                and np.max(np.abs(blick - zblick)) < 1e-3):
            self._ziel = None

    # ---------------------------------------------------------- Hilfe ----
    def _finde_actor(self, datenobjekt):
        for a in list(self._p.actors.values()):
            mapper = getattr(a, "mapper", None)
            if mapper is not None and getattr(mapper, "dataset", None) is datenobjekt:
                return a
        return None

    @classmethod
    def anwenden(cls, bruecke):
        """Ein Aufruf in der Demo nach fenster_bauen(): alles aktivieren."""
        opt = cls(bruecke)
        opt.beleuchtung()
        opt.hintergrund()
        opt.wasser_glanz()
        bericht = ", ".join("%s=%s" % (k, "an" if v else "aus")
                            for k, v in opt.aktiv.items())
        print("Grafik-Optimierung (Schritt 2):", bericht)
        return opt


def anwenden(bruecke):
    """Modul-Ebene: bequemer Einstieg fuer die Demo (delegiert an die Klasse)."""
    return GrafikOptimierung.anwenden(bruecke)
