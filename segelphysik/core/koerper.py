"""Koerper-Klasse (Spec V4: P1 Schwerpunktframe, P2 Rekursion, P3 Massen,
P4 Farbe). Nach der Erzeugung lebt jeder Koerper AUSSCHLIESSLICH im
Schwerpunktframe. SI-Einheiten (R6)."""
import colorsys
import numpy as np
from . import massen as ma

VOLUMEN_EPS = 1e-9

class KoerperFehler(ValueError):
    """Verstoss gegen die Koerper-Regeln (Spec P1-P4)."""

def _hex_zu_rgb(h):
    h = str(h).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(2 * z for z in h)
    if len(h) != 6:
        raise KoerperFehler("Farbe als Hex erwartet, bekommen: %r" % h)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

def _rgb_zu_hex(rgb):
    return "#" + "".join("%02x" % int(k * 255.0 + 0.5) for k in rgb)

def helle_auf(hex_farbe, delta):
    """Aufhellen im HSL-Raum: L_neu = L + delta*(1-L); H und S unveraendert.

    Spec P4: 'DeltaL = +0,25 - Lightness +25%' -> relative Formel
    (absolut wuerde der helle Default #c9c9c9 an der Weiss-Grenze clippen).
    """
    r, g, b = _hex_zu_rgb(hex_farbe)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = l + float(delta) * (1.0 - l)
    return _rgb_zu_hex(colorsys.hls_to_rgb(h, min(l, 1.0), s))

def _rel_pose(rel):
    if rel is None:
        return np.eye(3), np.zeros(3)
    R, t = rel
    return np.asarray(R, float), np.asarray(t, float)

class Koerper:
    """Ein starrer Koerper (auch zusammengesetzt) im eigenen Schwerpunktframe.

    Blatt:   Koerper(form=(punkte, dreiecke), genau-eine-Massengroesse, ...)
    Verband: Koerper(teile=[(kind, (R, t)), ...]) - reine Gruppe ohne eigene Werte
             oder bequemer: Koerper.verband([specs], ...) mit Specs im
             gemeinsamen Konstruktionsframe (rel_Posen werden automatisch
             aus den Teil-Schwerpunkten abgeleitet, Spec P2 Punkt 4).
    """

    def __init__(self, form=None, *, masse=None, dichte=None, material=None,
                 flaechenmasse=None, materialien=None, farbe="#c9c9c9",
                 farbe_unter_wasser=None, delta_helligkeit=0.4,
                 rel_pose=None, teile=()):
        self.farbe = farbe
        self.farbe_unter_wasser = farbe_unter_wasser
        self.delta_helligkeit = float(delta_helligkeit)
        self.position = np.zeros(3)
        self.orientierung = np.eye(3)
        if rel_pose is not None:
            self.setze_rel_pose(rel_pose)
        teile = list(teile)
        anzahl = sum(x is not None for x in (masse, dichte, material, flaechenmasse))
        if form is None:
            if anzahl:
                raise KoerperFehler("P2.5: reine Gruppe ohne eigene Form darf keine Massengroesse tragen")
            if not teile:
                raise KoerperFehler("Koerper braucht 'form' oder 'teile'")
            self._baue_verband(teile)
            return
        if teile:
            raise KoerperFehler("'form' und 'teile' gleichzeitig ist mehrdeutig - nur eines")
        if anzahl != 1:
            raise KoerperFehler("P3 Genau-eins-Regel: genau eine Massengroesse ist Pflicht (gefunden: %d)" % anzahl)
        punkte = np.asarray(form[0], float)
        dreiecke = np.asarray(form[1], np.int64)
        volumen = ma.mesh_volumen(punkte, dreiecke)
        if volumen < 0.0:
            dreiecke = dreiecke[:, [0, 2, 1]]
            volumen = -volumen
        self._volumen = abs(volumen)
        self._flaeche = ma.mesh_flaeche(punkte, dreiecke)
        if dichte is not None or material is not None:
            rho = float(dichte) if dichte is not None else self._material_dichte(material, materialien)
            if self._volumen < VOLUMEN_EPS:
                raise KoerperFehler("P3: volumenloses Mesh (z. B. Segel) verlangt flaechenmasse, nicht dichte/material")
            self.masse = rho * self._volumen
            r, _ = ma.schwerpunkt_homogen(punkte, dreiecke)
            I = ma.traegheitstensor_homogen(punkte, dreiecke, rho)
        elif masse is not None:
            self.masse = float(masse)
            if self._volumen > VOLUMEN_EPS:
                r, _ = ma.schwerpunkt_homogen(punkte, dreiecke)
                I = ma.traegheitstensor_homogen(punkte, dreiecke, self.masse / self._volumen)
            else:
                r, _ = ma.schwerpunkt_flaechig(punkte, dreiecke)
                I = ma.traegheitstensor_flaechig(punkte, dreiecke, self.masse / self._flaeche)
        else:
            self.masse = float(flaechenmasse) * self._flaeche
            r, _ = ma.schwerpunkt_flaechig(punkte, dreiecke)
            I = ma.traegheitstensor_flaechig(punkte, dreiecke, float(flaechenmasse))
        self.punkte = punkte - r
        self.dreiecke = dreiecke
        self.traegheitstensor = I
        self.teile = []
        self._r_eingabe = r

    def _baue_verband(self, teile):
        pts, tris = [], []
        versatz = 0
        m_ges = 0.0
        mr = np.zeros(3)
        I_summe = np.zeros((3, 3))
        kinder = []
        for eintrag in teile:
            kind, rel = eintrag if isinstance(eintrag, tuple) else (eintrag, None)
            R, t = _rel_pose(rel)
            pts.append(kind.punkte @ R.T + t)
            tris.append(kind.dreiecke + versatz)
            versatz += len(kind.punkte)
            I_summe += R @ kind.traegheitstensor @ R.T
            m_ges += kind.masse
            mr += kind.masse * t
            kinder.append((kind, R, t))
        if m_ges <= 0.0:
            raise KoerperFehler("Verband ohne Masse")
        r_s = mr / m_ges
        I_ges = I_summe.copy()
        for kind, _R, t in kinder:
            d = t - r_s
            I_ges += kind.masse * ((d @ d) * np.eye(3) - np.outer(d, d))
        self.punkte = np.vstack(pts) - r_s
        self.dreiecke = np.vstack(tris)
        self.masse = m_ges
        self.traegheitstensor = I_ges
        # FIX: Teile-Posen im EIGENEN (verschobenen) Frame speichern,
        # damit gilt: Summe m_i*r_i = 0 (P1-Invariante des Schwerpunktframes)
        self.teile = [(kind, (R, t - r_s)) for kind, R, t in kinder]
        self._volumen = None
        self._flaeche = None
        self._r_eingabe = r_s

    @classmethod
    def verband(cls, spezifikationen, **gemeinsam):
        """Zusammengesetzter Koerper aus Specs im gemeinsamen Konstruktionsframe."""
        eintraege = []
        for spec in spezifikationen:
            if "teile" in spec:
                kind = cls.verband(spec["teile"], **gemeinsam)
            else:
                kind = cls(
                    form=spec["form"],
                    masse=spec.get("masse"), dichte=spec.get("dichte"),
                    material=spec.get("material"),
                    flaechenmasse=spec.get("flaechenmasse"),
                    materialien=spec.get("materialien", gemeinsam.get("materialien")),
                    farbe=spec.get("farbe", gemeinsam.get("farbe", "#c9c9c9")),
                    farbe_unter_wasser=spec.get("farbe_unter_wasser"),
                    delta_helligkeit=gemeinsam.get("delta_helligkeit", 0.25))
            eintraege.append((kind, (np.eye(3), kind._r_eingabe.copy())))
        return cls(teile=eintraege, **gemeinsam)

    @staticmethod
    def _material_dichte(material, materialien):
        if not materialien or material not in materialien:
            raise KoerperFehler("material=%r verlangt die Materialtabelle aus konfiguration.json (Spec J)" % material)
        return float(materialien[material])

    def setze_rel_pose(self, rel):
        """Nur fuer Teile in einem Verband: (R, t) im Eltern-Konstruktionsframe."""
        R, t = _rel_pose(rel)
        self._rel_R, self._rel_t = R, t

    def setze_pose(self, position, orientierung=None):
        """Pose in Welt (A1): Position des Schwerpunkts + Orientierung."""
        self.position = np.asarray(position, float)
        if orientierung is not None:
            self.orientierung = np.asarray(orientierung, float)

    def punkte_in_welt(self):
        return self.punkte @ self.orientierung.T + self.position

    def unterwasser_farbe(self):
        if self.farbe_unter_wasser:
            return self.farbe_unter_wasser
        return helle_auf(self.farbe, self.delta_helligkeit)

    def teil_aggregate(self):
        """(masse, Teil-Schwerpunkt im EIGENEN Frame) je direktem Teil.

        Invariante (P1): Summe ueber m_i * r_i = 0, denn der Ursprung
        dieses Frames ist der Gesamtschwerpunkt.
        """
        out = []
        for kind, (_R, t) in self.teile:
            out.append((kind.masse, np.asarray(t, float).copy()))
        return out
