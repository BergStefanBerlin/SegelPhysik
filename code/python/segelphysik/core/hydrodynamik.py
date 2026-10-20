"""Geometriebezogene Hydrodynamik fuer Rumpf, Kiel und Ruder.

Die Modelle liefern benannte Wrenches in Weltkoordinaten. Geometrie wird
einmal vorbereitet; pro Auswertung werden nur Meshkoordinaten transformiert
und die aktuelle Benetzung aus den vorbereiteten Dreiecken bestimmt.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

from .dynamik_6dof import quaternion_matrix
from .kraftmodell import Kraftbeitrag, Wrench
from .rechenpfad import nativer_kern, rechenpfad

NU_WASSER_M2_S = 1.004e-6
CD_QUERSTROEMUNG = 1.17
ROLLE_RUMPF = "rumpf"
ROLLE_KIEL = "kiel"
ROLLE_RUDER = "ruder"
ROLLE_VOLUMENKOERPER = "volumenkoerper"
_ROLLEN_AKTIV = {
    ROLLE_RUMPF, ROLLE_KIEL, ROLLE_RUDER, ROLLE_VOLUMENKOERPER,
}


@dataclass(frozen=True, slots=True)
class HydrodynamikTestprofil:
    koerper_id: str
    kraft_betrag_N: float
    azimut_grad: float
    elevation_grad: float
    angriffspunkt_m: tuple[float, float, float]
    ruderwinkel_grad: float = 0.0
    modell: str = "rumpf_kiel_ruder"
    cd_volumenkoerper: float | None = None
    referenzgeschwindigkeit_m_pro_s: float = 1.0
    status: str = "vorläufig"


_TESTPROFILE = {
    "yacht1": HydrodynamikTestprofil(
        "yacht1", 510.1, 0.0, 0.0, (0.0, 0.0, 1.5)),
}


def hydrodynamik_testprofil(koerper_id, konfiguration=None):
    """Liefert das dokumentierte Testprofil eines hydrodynamischen Modells."""
    if not isinstance(koerper_id, str):
        raise TypeError("Körper-ID muss Text sein")
    if konfiguration is not None:
        modell = konfiguration["modell"]
        kraft = _vektor(konfiguration["testkraft_N"], "Testkraft", 3)
        punkt = _vektor(
            konfiguration["angriffspunkt_m"], "Angriffspunkt", 3)
        betrag = float(np.linalg.norm(kraft))
        if betrag <= 1e-12:
            azimut = elevation = 0.0
        else:
            azimut = math.degrees(math.atan2(kraft[1], kraft[0]))
            elevation = math.degrees(math.asin(
                max(-1.0, min(1.0, kraft[2] / betrag))))
        return HydrodynamikTestprofil(
            koerper_id=koerper_id,
            kraft_betrag_N=betrag,
            azimut_grad=azimut,
            elevation_grad=elevation,
            angriffspunkt_m=tuple(float(wert) for wert in punkt),
            ruderwinkel_grad=float(konfiguration["ruderwinkel_grad"]),
            modell=modell,
            cd_volumenkoerper=(
                float(konfiguration["cd_volumenkoerper"])
                if "cd_volumenkoerper" in konfiguration else None),
            referenzgeschwindigkeit_m_pro_s=float(
                konfiguration["referenzgeschwindigkeit_m_pro_s"]),
            status=konfiguration["status"],
        )
    return _TESTPROFILE.get(koerper_id.casefold())


def _vektor(wert, name, laenge):
    try:
        ergebnis = np.asarray(wert, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as fehler:
        raise ValueError("%s muss aus %d endlichen Zahlen bestehen"
                         % (name, laenge)) from fehler
    if (ergebnis.shape != (laenge,)
            or not np.isfinite(ergebnis).all()):
        raise ValueError("%s muss aus %d endlichen Zahlen bestehen"
                         % (name, laenge))
    return ergebnis


@nativer_kern("ittc_reibungsbeiwert", skalare=(0,))
def ittc_reibungsbeiwert(reynolds):
    """ITTC-1957-Linie oberhalb Re=5e5, stetiger laminarer Uebergang darunter."""
    reynolds = float(reynolds)
    if not math.isfinite(reynolds) or reynolds < 0.0:
        raise ValueError("Reynolds-Zahl muss endlich und nicht-negativ sein")
    if reynolds == 0.0:
        return 0.0
    laminar = 1.328 / math.sqrt(reynolds)
    if reynolds <= 1.0e5:
        return laminar
    turbulent = 0.075 / (math.log10(reynolds) - 2.0) ** 2
    if reynolds >= 5.0e5:
        return turbulent
    anteil = (math.log10(reynolds) - 5.0) / (
        math.log10(5.0e5) - 5.0)
    anteil = anteil * anteil * (3.0 - 2.0 * anteil)
    return (1.0 - anteil) * laminar + anteil * turbulent


def _benetzte_dreiecksflaechen(punkte, dreiecke):
    """Exakte Flaechenanteile dreieckiger Oberflaechen unter z=0."""
    ecken = punkte[dreiecke]
    kreuz = np.cross(ecken[:, 1] - ecken[:, 0],
                     ecken[:, 2] - ecken[:, 0])
    flaechen = 0.5 * np.linalg.norm(kreuz, axis=1)
    return _benetzung_aus_dreiecksecken(ecken, flaechen)


def _benetzung_aus_dreiecksecken(ecken, flaechen):
    tiefen = np.maximum(-ecken[:, :, 2], 0.0)
    trocken = np.maximum(ecken[:, :, 2], 0.0)
    nass = tiefen > 0.0
    anzahl_nass = np.sum(nass, axis=1)
    anteil = np.zeros(len(ecken), dtype=np.float64)
    anteil[anzahl_nass == 3] = 1.0

    eine_nasse_ecke = anzahl_nass == 1
    if np.any(eine_nasse_ecke):
        d = tiefen[eine_nasse_ecke]
        t = trocken[eine_nasse_ecke]
        n = nass[eine_nasse_ecke]
        index = np.argmax(n, axis=1)
        nass_tiefe = d[np.arange(len(d)), index]
        trocken_tiefen = np.where(n, 0.0, t)
        kanten = nass_tiefe[:, None] / (
            nass_tiefe[:, None] + trocken_tiefen)
        anteil[eine_nasse_ecke] = np.prod(kanten, axis=1)

    zwei_nasse_ecken = anzahl_nass == 2
    if np.any(zwei_nasse_ecken):
        d = tiefen[zwei_nasse_ecken]
        t = trocken[zwei_nasse_ecken]
        n = nass[zwei_nasse_ecken]
        index = np.argmax(~n, axis=1)
        trocken_hoehe = t[np.arange(len(t)), index]
        nass_tiefen = np.where(n, d, 0.0)
        nenner = trocken_hoehe[:, None] + nass_tiefen
        kanten = np.divide(
            trocken_hoehe[:, None],
            nenner,
            out=np.zeros_like(nenner),
            where=nenner > 0.0,
        )
        anteil[zwei_nasse_ecken] = 1.0 - np.prod(kanten, axis=1)
    return flaechen * anteil


@dataclass(frozen=True, slots=True)
class HydrodynamikTeil:
    name: str
    rolle: str
    punkte_m: np.ndarray
    dreiecke: np.ndarray
    _dreiecksecken: np.ndarray = field(
        init=False, repr=False, compare=False)
    _flaechen_m2: np.ndarray = field(
        init=False, repr=False, compare=False)
    _normalen: np.ndarray = field(
        init=False, repr=False, compare=False)
    _dreiecksmittelpunkte: np.ndarray = field(
        init=False, repr=False, compare=False)
    _oberflaeche_cache_m2: float = field(
        init=False, repr=False, compare=False)
    _planform_cache_m2: float = field(
        init=False, repr=False, compare=False)
    _spannweite_cache_m: float = field(
        init=False, repr=False, compare=False)

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Hydrodynamikteil braucht einen Namen")
        if self.rolle not in _ROLLEN_AKTIV:
            raise ValueError("Unbekannte hydrodynamische Rolle: %r"
                             % self.rolle)
        punkte = np.asarray(self.punkte_m, dtype=np.float64)
        dreiecke = np.asarray(self.dreiecke)
        if (punkte.ndim != 2 or punkte.shape[1] != 3
                or len(punkte) < 3 or not np.isfinite(punkte).all()):
            raise ValueError("Hydrodynamikpunkte muessen ein endliches Nx3 sein")
        if not np.issubdtype(dreiecke.dtype, np.integer):
            raise ValueError("Hydrodynamikdreiecke muessen ganzzahlig sein")
        dreiecke = dreiecke.astype(np.int64, copy=False)
        if (dreiecke.ndim != 2 or dreiecke.shape[1] != 3
                or len(dreiecke) == 0 or np.any(dreiecke < 0)
                or np.any(dreiecke >= len(punkte))):
            raise ValueError("Hydrodynamikdreiecke muessen gueltige Nx3-Indizes sein")
        punkte = np.array(punkte, copy=True)
        dreiecke = np.array(dreiecke, copy=True)
        ecken = punkte[dreiecke]
        kreuz = np.cross(ecken[:, 1] - ecken[:, 0],
                         ecken[:, 2] - ecken[:, 0])
        doppelflaechen = np.linalg.norm(kreuz, axis=1)
        flaechen = 0.5 * doppelflaechen
        normalen = np.zeros_like(kreuz)
        gueltig = doppelflaechen > 1e-15
        normalen[gueltig] = kreuz[gueltig] / doppelflaechen[gueltig, None]
        mittelpunkte = ecken.mean(axis=1)
        for array in (punkte, dreiecke, ecken, flaechen, normalen,
                      mittelpunkte):
            array.setflags(write=False)
        object.__setattr__(self, "punkte_m", punkte)
        object.__setattr__(self, "dreiecke", dreiecke)
        object.__setattr__(self, "_dreiecksecken", ecken)
        object.__setattr__(self, "_flaechen_m2", flaechen)
        object.__setattr__(self, "_normalen", normalen)
        object.__setattr__(self, "_dreiecksmittelpunkte", mittelpunkte)
        object.__setattr__(
            self, "_oberflaeche_cache_m2", float(flaechen.sum()))
        object.__setattr__(
            self, "_planform_cache_m2",
            float(0.5 * np.sum(doppelflaechen * np.abs(normalen[:, 1]))))
        object.__setattr__(
            self, "_spannweite_cache_m", float(np.ptp(punkte[:, 2])))

    @property
    def schwerpunkt_m(self):
        return self.punkte_m.mean(axis=0)

    @property
    def oberflaeche_m2(self):
        return self._oberflaeche_cache_m2

    @property
    def planform_m2(self):
        return self._planform_cache_m2

    @property
    def spannweite_m(self):
        return self._spannweite_cache_m


def hydrodynamik_teile_aus_koerper(koerper):
    """Erzeugt hydrodynamische Blatt-Meshes im Schwerpunktframe."""
    vorbereitete = []

    def sammle(knoten, rotation, translation, rolle_default=None):
        rolle = getattr(knoten, "rolle", None) or rolle_default
        if getattr(knoten, "teile", None):
            for kind, (rel_rotation, rel_translation) in knoten.teile:
                sammle(
                    kind,
                    rotation @ np.asarray(rel_rotation, dtype=np.float64),
                    translation + rotation @ np.asarray(
                        rel_translation, dtype=np.float64),
                    getattr(knoten, "rolle_default", None) or rolle,
                )
            return
        if rolle not in {ROLLE_RUMPF, ROLLE_KIEL, ROLLE_RUDER}:
            return
        punkte = np.asarray(knoten.punkte, dtype=np.float64) @ rotation.T
        punkte = punkte + translation
        vorbereitete.append(HydrodynamikTeil(
            str(getattr(knoten, "name", None)
                or getattr(knoten, "knoten_id", None)
                or rolle),
            rolle,
            punkte,
            np.asarray(knoten.dreiecke, dtype=np.int64),
        ))

    if hasattr(koerper, "hydrodynamik_teile"):
        return tuple(
            HydrodynamikTeil(name, rolle, punkte, dreiecke)
            for rolle, name, punkte, dreiecke in koerper.hydrodynamik_teile
            if rolle in _ROLLEN_AKTIV)
    if not hasattr(koerper, "teile"):
        return ()
    sammle(koerper, np.eye(3), np.zeros(3))
    return tuple(vorbereitete)


def wasserlinienlaenge_m(teile, *, z_m=0.0, phi_rad=0.0,
                         theta_rad=0.0):
    """Bestimmt die projizierte LWL aus Rumpf-Dreiecken an der Ebene z=0."""
    from .auftrieb import pose_matrix

    rotation = pose_matrix(z_m, phi_rad, theta_rad)[:3, :3]
    position = np.array((0.0, 0.0, z_m), dtype=np.float64)
    laengsachse = rotation[:, 0]
    abstaende = []
    for teil in teile:
        if teil.rolle != ROLLE_RUMPF:
            continue
        ecken = teil._dreiecksecken @ rotation.T + position
        for dreieck in ecken:
            for index in range(3):
                a = dreieck[index]
                b = dreieck[(index + 1) % 3]
                da, db = float(a[2]), float(b[2])
                if abs(da) <= 1e-10:
                    abstaende.append(float(np.dot(a, laengsachse)))
                if da * db < 0.0:
                    anteil = da / (da - db)
                    punkt = a + anteil * (b - a)
                    abstaende.append(float(np.dot(punkt, laengsachse)))
    if len(abstaende) < 2:
        return 0.0
    return max(abstaende) - min(abstaende)


def _generische_teile_aus_koerper(koerper):
    """Erzeugt Widerstandsteile aus den verdrängenden Meshes eines Opt-ins."""
    meshes = getattr(koerper, "blatt_meshes", None)
    if meshes is not None:
        return tuple(
            HydrodynamikTeil(
                "volumenkoerper" if index == 0
                else "volumenkoerper_%d" % (index + 1),
                ROLLE_VOLUMENKOERPER, punkte, dreiecke)
            for index, (punkte, dreiecke) in enumerate(meshes))
    if hasattr(koerper, "punkte") and hasattr(koerper, "dreiecke"):
        return (HydrodynamikTeil(
            str(getattr(koerper, "name", None) or "volumenkoerper"),
            ROLLE_VOLUMENKOERPER,
            koerper.punkte, koerper.dreiecke),)
    return ()


class HydrodynamikModell:
    """Vorbereitete Bauteilmodelle fuer Verdrängungsfahrt."""

    def __init__(self, teile, *, rho_kg_m3=1000.0,
                 nu_m2_s=NU_WASSER_M2_S, formfaktor_rumpf=0.2,
                 cd_quer=CD_QUERSTROEMUNG, wirkungsgrad=0.8,
                 cd0_profil=0.01, fluidgeschwindigkeit=(0.0, 0.0, 0.0),
                 fluidwinkelgeschwindigkeit=(0.0, 0.0, 0.0),
                 ruderwinkel_rad=0.0, cd_volumenkoerper=None):
        self.teile = tuple(teile)
        if any(not isinstance(teil, HydrodynamikTeil)
               for teil in self.teile):
            raise TypeError(
                "HydrodynamikModell benoetigt HydrodynamikTeil-Instanzen")
        self.rho = float(rho_kg_m3)
        self.nu = float(nu_m2_s)
        self.formfaktor_rumpf = float(formfaktor_rumpf)
        self.cd_quer = float(cd_quer)
        self.wirkungsgrad = float(wirkungsgrad)
        self.cd0_profil = float(cd0_profil)
        self.cd_volumenkoerper = (
            None if cd_volumenkoerper is None
            else float(cd_volumenkoerper))
        self.fluidgeschwindigkeit = _vektor(
            fluidgeschwindigkeit, "Fluidgeschwindigkeit", 3).copy()
        self.fluidwinkelgeschwindigkeit = _vektor(
            fluidwinkelgeschwindigkeit, "Fluid-Winkelgeschwindigkeit", 3).copy()
        self._ruderwinkel_rad = 0.0
        self.ruderwinkel_setzen(ruderwinkel_rad)
        skalare = (self.rho, self.nu, self.formfaktor_rumpf, self.cd_quer,
                   self.wirkungsgrad, self.cd0_profil, self.ruderwinkel_rad)
        if (self.cd_volumenkoerper is not None
                and not math.isfinite(self.cd_volumenkoerper)):
            raise ValueError("Volumenkoerper-Cd muss endlich sein")
        if not all(math.isfinite(x) for x in skalare):
            raise ValueError("Hydrodynamikparameter muessen endlich sein")
        if (self.rho <= 0.0 or self.nu <= 0.0
                or self.formfaktor_rumpf < 0.0 or self.cd_quer < 0.0
                or not 0.0 < self.wirkungsgrad <= 1.0
                or self.cd0_profil < 0.0
                or (self.cd_volumenkoerper is not None
                    and self.cd_volumenkoerper <= 0.0)):
            raise ValueError("Hydrodynamikparameter liegen ausserhalb des "
                             "gueltigen Bereichs")
        self.fluidgeschwindigkeit.setflags(write=False)
        self.fluidwinkelgeschwindigkeit.setflags(write=False)
        self._native_teile = None
        self._native_quellen = None
        if rechenpfad() == "cpp":
            self._native_vorbereiten()

    def _native_vorbereiten(self):
        from .native_backend import native_laden

        native = native_laden()
        self._native_teile = native.HydroKontext([
            native.HydroTeil(native.Mesh(
                teil.punkte_m, teil.dreiecke, teil.name, teil.rolle))
            for teil in self.teile])
        self._native_quellen = self.teile

    def __getstate__(self):
        daten = self.__dict__.copy()
        daten.pop("_native_teile", None)
        daten.pop("_native_quellen", None)
        return daten

    def __setstate__(self, daten):
        self.__dict__.update(daten)
        self._native_teile = None
        self._native_quellen = None
        if rechenpfad() == "cpp":
            self._native_vorbereiten()

    @property
    def ruderwinkel_rad(self):
        return self._ruderwinkel_rad

    def ruderwinkel_setzen(self, winkel_rad):
        if isinstance(winkel_rad, (bool, np.bool_)):
            raise ValueError("Ruderwinkel muss eine endliche Zahl sein")
        winkel = float(winkel_rad)
        if not math.isfinite(winkel) or abs(winkel) > math.pi / 2.0:
            raise ValueError("Ruderwinkel muss zwischen -90 und +90 Grad liegen")
        self._ruderwinkel_rad = winkel

    @classmethod
    def aus_koerper(cls, koerper, **parameter):
        teile = hydrodynamik_teile_aus_koerper(koerper)
        cd_volumenkoerper = parameter.get("cd_volumenkoerper")
        if not teile and cd_volumenkoerper is not None:
            teile = _generische_teile_aus_koerper(koerper)
        return None if not teile else cls(teile, **parameter)

    def beitraege_erzeugen(self, lage, v=None, omega=None):
        if isinstance(lage, (tuple, list)) and len(lage) == 2:
            position = _vektor(lage[0], "Position", 3)
            rotation = quaternion_matrix(lage[1])
        elif isinstance(lage, (tuple, list)) and len(lage) == 3:
            from .auftrieb import pose_matrix
            from .dynamik_6dof import quaternion_aus_matrix
            z, phi, theta = (float(wert) for wert in lage)
            transform = pose_matrix(z, phi, theta)
            position = np.array((0.0, 0.0, z), dtype=np.float64)
            rotation = quaternion_matrix(
                quaternion_aus_matrix(transform[:3, :3]))
        else:
            raise ValueError(
                "Hydrodynamik erwartet eine 6-DOF-Pose oder (z, phi, theta)")
        geschwindigkeit = _vektor(
            (0.0, 0.0, 0.0) if v is None else v,
            "Koerpergeschwindigkeit", 3) - self.fluidgeschwindigkeit
        winkelgeschwindigkeit = _vektor(
            (0.0, 0.0, 0.0) if omega is None else omega,
            "Koerper-Winkelgeschwindigkeit", 3
        ) - self.fluidwinkelgeschwindigkeit
        if rechenpfad() == "cpp":
            from .native_backend import native_laden

            native = native_laden()
            if self._native_quellen is not self.teile:
                self._native_vorbereiten()
            beitraege = self._native_teile.beitraege(
                rotation, position, geschwindigkeit,
                winkelgeschwindigkeit, np.array([
                    self.rho, self.nu, self.formfaktor_rumpf, self.cd_quer,
                    self.wirkungsgrad, self.cd0_profil, self.ruderwinkel_rad],
                    dtype=np.float64),
                self.cd_volumenkoerper, native.Abbruch())
            return tuple(Kraftbeitrag(b.name, Wrench(
                b.wrench.frame, tuple(b.wrench.bezugspunkt),
                tuple(b.wrench.kraft), tuple(b.wrench.moment)))
                for b in beitraege)
        beitraege = []
        for teil in self.teile:
            ecken = teil._dreiecksecken @ rotation.T + position
            nass_flaechen = _benetzung_aus_dreiecksecken(
                ecken, teil._flaechen_m2)
            nass_flaeche = float(nass_flaechen.sum())
            if nass_flaeche <= 1e-12:
                continue
            mittelpunkte = (
                teil._dreiecksmittelpunkte @ rotation.T + position)
            zentrum = np.average(
                mittelpunkte, axis=0, weights=nass_flaechen)
            arm = zentrum - position
            lokal_v = geschwindigkeit + np.cross(winkelgeschwindigkeit, arm)
            tempo = float(np.linalg.norm(lokal_v))
            if teil.rolle == ROLLE_VOLUMENKOERPER:
                if self.cd_volumenkoerper is None:
                    continue
                normalen = teil._normalen @ rotation.T
                gueltig = np.linalg.norm(teil._normalen, axis=1) > 0.0
                arme = mittelpunkte - position
                lokale_geschwindigkeiten = (
                    geschwindigkeit
                    + np.cross(winkelgeschwindigkeit, arme))
                lokale_tempi = np.linalg.norm(
                    lokale_geschwindigkeiten, axis=1)
                aktiv = gueltig & (lokale_tempi > 1e-9)
                if not np.any(aktiv):
                    continue
                richtungen = (
                    lokale_geschwindigkeiten[aktiv]
                    / lokale_tempi[aktiv, None])
                projektionsflaechen = 0.5 * nass_flaechen[aktiv] * np.abs(
                    np.einsum("ij,ij->i", normalen[aktiv], richtungen))
                kraefte = (
                    -0.5 * self.rho * self.cd_volumenkoerper
                    * projektionsflaechen[:, None]
                    * lokale_tempi[aktiv, None]
                    * lokale_geschwindigkeiten[aktiv])
                kraft = np.sum(kraefte, axis=0)
                moment = np.sum(np.cross(
                    mittelpunkte[aktiv] - zentrum, kraefte), axis=0)
                name = "hydrodynamik_volumenkoerper"
            elif tempo <= 1e-9:
                continue
            else:
                q = 0.5 * self.rho * tempo * tempo
                richtung = lokal_v / tempo
            if teil.rolle == ROLLE_VOLUMENKOERPER:
                pass
            elif teil.rolle == ROLLE_RUMPF:
                laenge = max(float(np.ptp(teil.punkte_m[:, 0])), 0.05)
                cf = ittc_reibungsbeiwert(tempo * laenge / self.nu)
                reibung = q * cf * nass_flaeche * (
                    1.0 + self.formfaktor_rumpf)
                normalen = teil._normalen @ rotation.T
                gueltig = np.linalg.norm(teil._normalen, axis=1) > 0.0
                projektionsflaeche = 0.5 * float(np.sum(
                    nass_flaechen[gueltig]
                    * np.abs(normalen[gueltig] @ richtung)))
                quer = q * self.cd_quer * projektionsflaeche
                kraft = -(reibung + quer) * richtung
                name = "hydrodynamik_rumpf"
            else:
                planform = teil.planform_m2
                spannweite = teil.spannweite_m
                if planform <= 1e-12 or spannweite <= 1e-12:
                    continue
                benetzungsgrad = min(
                    1.0, max(0.0, nass_flaeche / teil.oberflaeche_m2))
                flaeche = planform * benetzungsgrad
                if flaeche <= 1e-12:
                    continue
                streckung = spannweite * spannweite / planform
                winkel = math.atan2(lokal_v[1], lokal_v[0])
                if teil.rolle == ROLLE_RUDER:
                    winkel += self.ruderwinkel_rad
                cl_slope = (
                    2.0 * math.pi * streckung / (streckung + 2.0))
                cl = cl_slope * math.sin(winkel)
                cl_max = 1.2
                cl = cl_max * math.tanh(cl / cl_max)
                querichtung = np.array((-richtung[1], richtung[0], 0.0))
                quer_norm = float(np.linalg.norm(querichtung))
                if quer_norm <= 1e-12:
                    continue
                querichtung /= quer_norm
                lift = q * flaeche * cl
                cd_induced = cl * cl / (
                    math.pi * self.wirkungsgrad * streckung)
                cd_profile = self.cd0_profil + cd_induced
                drag = q * flaeche * cd_profile
                kraft = -lift * querichtung - drag * richtung
                name = "hydrodynamik_%s" % teil.rolle
            beitraege.append(Kraftbeitrag(name, Wrench(
                "simulationsframe",
                tuple(float(x) for x in zentrum),
                tuple(float(x) for x in kraft),
                tuple(float(x) for x in (
                    moment if teil.rolle == ROLLE_VOLUMENKOERPER
                    else (0.0, 0.0, 0.0))),
            )))
        return tuple(beitraege)
