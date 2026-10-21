"""Einziger snapshotbasierter Zeichenpfad fuer Kraefte und Momente."""
from __future__ import annotations

import math
from functools import lru_cache
import numpy as np

from .core import kraefte_bild as kb
from .core.kraefte_anzeige import GUELTIGE_STATUS, anzeige_wrench, wirkungslinie
from .core.kraefte_darstellung import (
    BogenVerlauf, KameraAbbildung, SkalenAbbildung,
    abstand_zum_linienzug_px, anfangsreferenz, senkrechter_hebelarm,
)
from .core.overlays import (
    LAYER_FREMDKRAFT, LAYER_HYDRO_KIEL, LAYER_HYDRO_RUDER, LAYER_HYDRO_RUMPF,
    LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_SCHWERPUNKT,
)


@lru_cache(maxsize=8)
def _kugelvorlage(radius):
    import pyvista as pv

    return pv.Sphere(radius=radius, center=(0.0, 0.0, 0.0))


def _kugel_mesh(mitte, radius):
    vorlage = _kugelvorlage(float(radius))
    mesh = vorlage.copy(deep=True)
    mesh.points = vorlage.points + np.asarray(mitte, dtype=vorlage.points.dtype)
    return mesh


class KraefteZeichner:
    def __init__(self, bruecke):
        self.bruecke = bruecke
        self.boegen = BogenVerlauf()
        self.skalen = {}
        self.sichtbar = {}
        self.auswahl = None
        self.picklinien = {}
        self.generationen = {}
        self.labels = {}
        self.label_linien = {}
        self.skalen_parameter = {}
        self.koerperumfang = None
        self.zeichenzustaende = {}

    def labels_entfernen(self, koerper_id):
        for key in tuple(self.labels):
            if key[0] == koerper_id:
                self.bruecke._plotter.renderer.RemoveActor(self.labels.pop(key))
                linie = self.label_linien.pop(key, None)
                if linie is not None:
                    self.bruecke._plotter.renderer.RemoveActor(linie)

    def entfernen(self, koerper_id):
        self.boegen.koerper_entfernen(koerper_id)
        self.skalen.pop(koerper_id, None)
        self.skalen_parameter.pop(koerper_id, None)
        self.zeichenzustaende.pop(koerper_id, None)
        self.generationen.pop(koerper_id, None)
        self.labels_entfernen(koerper_id)
        self.sichtbar = {q: v for q, v in self.sichtbar.items() if q[0] != koerper_id}
        self.picklinien = {q: v for q, v in self.picklinien.items() if q[0] != koerper_id}
        if self.auswahl is not None and self.auswahl[0] == koerper_id:
            self.auswahl = None

    def kamera(self):
        plotter = self.bruecke._plotter
        cam = plotter.renderer.GetActiveCamera()
        ratio = float(plotter.devicePixelRatioF()) if hasattr(
            plotter, "devicePixelRatioF") else 1.0
        width, height = plotter.ren_win.GetSize()
        return KameraAbbildung(
            tuple(cam.GetPosition()), tuple(cam.GetFocalPoint()),
            (max(width / ratio, 1), max(height / ratio, 1)),
            bool(cam.GetParallelProjection()), cam.GetParallelScale(),
            cam.GetViewAngle(), bool(cam.GetUseHorizontalViewAngle()))

    def neu_einpassen(self, snapshot):
        optionen = self.bruecke._stil.anzeige()
        werte = [anzeige_wrench(snapshot, b, weltursprung=optionen["weltursprung"])
                 for b in (*snapshot.beitraege, *snapshot.gruppen,
                                    snapshot.bilanz)
                 if b.status in GUELTIGE_STATUS and b.wrench is not None]
        if snapshot.koerper_id not in self.skalen:
            self.zeichnen(snapshot, self.bruecke._koerper[snapshot.koerper_id])
        force, moment = self.skalen[snapshot.koerper_id]
        self.skalen[snapshot.koerper_id] = (
            force.neu_einpassen(math.hypot(*w.kraft_N) for w in werte),
            moment.neu_einpassen(math.hypot(*w.moment_Nm) for w in werte))

    def generation_setzen(self, snapshot):
        koerper_id = snapshot.koerper_id
        vorherige_generation = self.generationen.get(koerper_id)
        if vorherige_generation != snapshot.generation:
            self.boegen.koerper_entfernen(koerper_id)
            if (vorherige_generation is not None and self.auswahl is not None
                    and self.auswahl[0] == koerper_id):
                self.auswahl = None
            self.generationen[koerper_id] = snapshot.generation

    def zeichnen(self, snapshot, k):
        import pyvista as pv
        owner = self.bruecke
        optionen = owner._stil.anzeige()
        koerper_id = snapshot.koerper_id
        self.generation_setzen(snapshot)
        kamera = self.kamera()
        beitraege = (*snapshot.beitraege, *snapshot.gruppen, snapshot.bilanz)
        gueltig = [b for b in beitraege
                   if b.status in GUELTIGE_STATUS and b.wrench is not None]
        wrenches = {b.instanz_id: anzeige_wrench(
            snapshot, b, weltursprung=optionen["weltursprung"]) for b in gueltig}
        parameter = (optionen["kraftreferenz_N"], optionen["momentreferenz_Nm"],
                     optionen["logarithmisch"], optionen["kraftmaximum_px"],
                     optionen["momentmaximum_px"], optionen["weltursprung"])
        vorher = self.skalen_parameter.get(koerper_id)
        if koerper_id not in self.skalen or vorher != parameter:
            alt = self.skalen.get(koerper_id)
            modus = "log" if optionen["logarithmisch"] else "linear"
            f_ref = (None if alt is None or vorher is None or vorher[0] != parameter[0]
                     else alt[0].referenz)
            m_ref = (None if alt is None or vorher is None or vorher[1] != parameter[1]
                     else alt[1].referenz)
            self.skalen[koerper_id] = (
                SkalenAbbildung(anfangsreferenz(
                    (math.hypot(*b.wrench.kraft_N) for b in gueltig),
                    manuell=f_ref or parameter[0] or None),
                    optionen["kraftmaximum_px"], modus),
                SkalenAbbildung(anfangsreferenz(
                    (math.hypot(*w.moment_Nm) for w in wrenches.values()),
                    manuell=m_ref or parameter[1] or None),
                    optionen["momentmaximum_px"], modus))
            self.skalen_parameter[koerper_id] = parameter
        f_skala, m_skala = self.skalen[koerper_id]
        ausdehnung = owner._ausdehnung(k)
        zustand = (
            snapshot.generation, snapshot.kraftpose, snapshot.szenenversatz_m,
            snapshot.beitraege, snapshot.gruppen, snapshot.bilanz, kamera,
            owner._stil, f_skala, m_skala, ausdehnung, self.auswahl,
            tuple((q, v) for q, v in self.sichtbar.items() if q[0] == koerper_id),
            tuple((q, v) for q, v in optionen.items()
                  if q not in ("fensterlayout", "sichtbarkeiten", "mehrkoerper")),
            tuple(owner._layer.ist_an(l) for l in (
                LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT,
                LAYER_HYDRO_RUMPF, LAYER_HYDRO_KIEL, LAYER_HYDRO_RUDER,
                LAYER_SCHWERPUNKT)))
        if self.zeichenzustaende.get(koerper_id) == zustand:
            return
        store = k.setdefault("kraefte_actors", {})
        gezeichnet = set()
        self.picklinien = {q: v for q, v in self.picklinien.items()
                           if q[0] != koerper_id}

        def mesh(name, fabrik, stil, anker, *form):
            signatur = owner._overlay_signatur(stil, *form)
            gezeichnet.add(name)
            if owner._overlay_translation_aus_cache(store, name, signatur, anker):
                return
            owner._mesh_setzen(
                store, name, fabrik(), stil["vordergrund"],
                color=stil["farbe"], opacity=stil["deckkraft"],
                smooth_shading=True, kontur=stil.get("kontur"))
            owner._overlay_translation_merke(store, name, signatur, anker)

        ausgewaehlt = next((b for b in gueltig if b.instanz_id == self.auswahl), None)
        quellen = set() if ausgewaehlt is None else set(ausgewaehlt.quell_ids)
        for beitrag in gueltig:
            id_ = beitrag.instanz_id
            summe = beitrag.herkunft in ("Gruppensumme", "Gesamtsumme")
            stil = owner._stil.beitragsstil(beitrag, ausdehnung)
            if not self.sichtbar.get(id_, stil["sichtbar"]) and id_ not in quellen:
                continue
            wrench = wrenches[id_]
            p = np.asarray(wrench.bezugspunkt_m)
            f = np.asarray(wrench.kraft_N)
            m = np.asarray(wrench.moment_Nm)
            if beitrag.originalangriff_m is not None:
                anker = np.asarray(beitrag.originalangriff_m)
                rest = m - np.cross(anker - p, f)
            elif summe:
                anker, rest = p, m
            else:
                linie = wirkungslinie(
                    wrench, f_char_N=max(1, f_skala.referenz),
                    koerperausdehnung_m=ausdehnung)
                anker, rest = np.asarray(linie.anker_m), np.asarray(linie.restmoment_Nm)
            p = p + snapshot.szenenversatz_m
            anker = anker + snapshot.szenenversatz_m
            tiefe = np.dot(anker - kamera.position,
                           np.asarray(kamera.ziel) - kamera.position)
            if not kamera.parallel and tiefe <= 0:
                continue
            pixel = kamera.welt_pro_pixel(anker)
            basisstil = stil
            stil = owner._stil.bildschirmstil(stil, ausdehnung, pixel)
            if id_ == self.auswahl or id_ in quellen:
                stil["durchmesser"] = 5 * pixel
            prefix = "kraefte_" + repr(id_)
            pick = []
            betrag = math.hypot(*f)
            kraftlayer = (LAYER_FREMDKRAFT if beitrag.name == "fremdkraft"
                          else LAYER_KRAEFTE)
            kraftlayer = {
                "hydrodynamik_rumpf": LAYER_HYDRO_RUMPF,
                "hydrodynamik_kiel": LAYER_HYDRO_KIEL,
                "hydrodynamik_ruder": LAYER_HYDRO_RUDER,
            }.get(beitrag.name, kraftlayer)
            if owner._layer.ist_an(kraftlayer) and betrag > 0:
                skalenwert = f_skala.abbilden(betrag * stil["kraftfaktor"])
                if not skalenwert.kleinwert and skalenwert.groesse_px >= stil["kleinwert_px"]:
                    pfeil = kb.pfeil_fest(
                        anker, f / betrag * skalenwert.groesse_px * pixel,
                        stil["durchmesser"], stil["kopf_durchmesser"],
                        stil["kopf_laenge"], 0.0)
                    name = prefix + "_F"
                    owner._kraftpfeil_zeichnen(store, name, stil, pfeil)
                    gezeichnet.add(name)
                    pick.append(np.asarray([pfeil["start"], pfeil["spitze"]]))
                    if skalenwert.abgeschnitten:
                        mesh(prefix + "_F_grenze", lambda: _kugel_mesh(
                            pfeil["spitze"], 3 * pixel),
                            stil, pfeil["spitze"], 3 * pixel)
                else:
                    mesh(prefix + "_F_klein", lambda: _kugel_mesh(
                        anker, 2 * pixel), stil, anker, 2 * pixel)
                    pick.append(np.asarray([anker]))
            def moment_zeichnen(kennung, vektor, mitte, momentstil):
                moment = math.hypot(*vektor)
                if moment == 0:
                    return
                if not kamera.parallel and np.dot(
                        np.asarray(mitte) - kamera.position,
                        np.asarray(kamera.ziel) - kamera.position) <= 0:
                    return
                moment_pixel = kamera.welt_pro_pixel(mitte)
                momentstil = owner._stil.bildschirmstil(
                    momentstil, ausdehnung, moment_pixel)
                wert = m_skala.abbilden(moment * momentstil["momentfaktor"])
                if not wert.kleinwert and wert.groesse_px >= momentstil["kleinwert_px"]:
                    bogen = self.boegen.bogen(
                        (id_[0], id_[1] + kennung), snapshot.generation, vektor, mitte,
                        wert.groesse_px * moment_pixel)
                    punkte = np.asarray(bogen.punkte)
                    kopf_l = min(momentstil["kopf_laenge"], .5 * bogen.radius_m)
                    richtung = np.asarray(bogen.richtung)
                    spitze = punkte[-1] + kopf_l * richtung
                    name = prefix + kennung
                    owner._momentbogen_zeichnen(
                        store, name, {**momentstil, "gestrichelt": False},
                        vektor, mitte, bogen.radius_m, bogen=bogen)
                    gezeichnet.add(name)
                    pick.append(np.vstack((punkte, spitze)))
                    if wert.abgeschnitten:
                        mesh(name + "_grenze", lambda: pv.Sphere(
                            radius=3 * moment_pixel, center=spitze),
                            momentstil, spitze, 3 * moment_pixel)
                else:
                    mesh(prefix + kennung + "_klein", lambda: _kugel_mesh(
                        mitte, 2 * moment_pixel),
                        momentstil, mitte, 2 * moment_pixel)
                    pick.append(np.asarray([mitte]))

            moment = math.hypot(*rest)
            if owner._layer.ist_an(LAYER_MOMENTE):
                # Auswahl erklaert das volle Moment um P, nicht nur das Restmoment.
                moment_zeichnen("_M", m if id_ == self.auswahl else rest,
                                p if id_ == self.auswahl else anker, basisstil)
                basis = (snapshot.kraftpose.rotationsmatrix
                         if optionen["koerperframe"] else np.eye(3))
                komponenten = owner._stil.momentkomponenten(
                    beitrag, ausdehnung, basisstil)
                for achse, richtung, (an, komponentenstil) in zip(
                        "xyz", basis.T, komponenten):
                    if an:
                        moment_zeichnen("_M_" + achse,
                                        richtung * np.dot(richtung, m), p, komponentenstil)
            anzeige_aktiv = (owner._layer.ist_an(kraftlayer)
                             or owner._layer.ist_an(LAYER_MOMENTE))
            if id_ == self.auswahl and anzeige_aktiv:
                mesh(prefix + "_P", lambda: pv.Sphere(
                    radius=4 * pixel, center=p), stil, p, 4 * pixel)
            if (id_ == self.auswahl and anzeige_aktiv
                    and betrag > 0 and beitrag.originalangriff_m is not None):
                a, b = senkrechter_hebelarm(p, anker, f)
                hebelstil = owner._stil.bildschirmstil(
                    owner._stil.pfeil("hebelarm", ausdehnung), ausdehnung, pixel)
                if math.dist(a, b) > 0 and hebelstil["sichtbar"]:
                    punkte, zellen = kb.strich_linien(
                        [a, b], hebelstil["strich"], hebelstil["luecke"])
                    mesh(prefix + "_hebelarm", lambda: pv.PolyData(
                        punkte, lines=zellen).tube(
                            radius=.5 * hebelstil["durchmesser"], n_sides=8),
                        hebelstil, a, np.asarray(b) - a, pixel)
                mesh(prefix + "_A", lambda: pv.Sphere(radius=4 * pixel, center=anker),
                     stil, anker, 4 * pixel)
                richtung = f / betrag
                mesh(prefix + "_wirkungslinie", lambda: pv.Line(
                    anker - richtung * ausdehnung,
                    anker + richtung * ausdehnung).tube(
                        radius=.5 * pixel, n_sides=6),
                        stil, anker, richtung, ausdehnung, pixel)
            if anzeige_aktiv and betrag == 0 and moment == 0:
                mesh(prefix + "_null", lambda: pv.Polygon(
                    center=p, normal=np.asarray(kamera.ziel) - kamera.position,
                    radius=3 * pixel, n_sides=16, fill=False).tube(
                        radius=.5 * pixel, n_sides=6), stil, p, pixel,
                        np.asarray(kamera.ziel) - kamera.position)
                pick.append(np.asarray([p]))
            if anzeige_aktiv and beitrag.originalangriff_m is None and not summe:
                mesh(prefix + "_aequivalent", lambda: pv.Polygon(
                    center=anker, normal=np.asarray(kamera.ziel) - kamera.position,
                    radius=4 * pixel, n_sides=4, fill=False).tube(
                        radius=.5 * pixel, n_sides=6), stil, anker, pixel,
                        np.asarray(kamera.ziel) - kamera.position)
                pick.append(np.asarray([anker]))
            self.picklinien[id_] = tuple(pick)
            if (beitrag.name == "hydrostatik"
                    and beitrag.originalangriff_m is not None
                    and owner._layer.ist_an(LAYER_SCHWERPUNKT)):
                sp = owner._stil.schwerpunkte(ausdehnung)
                name = prefix + "_angriff"
                owner._kugel_zeichnen(
                    store, name, anker, sp["k_radius"], sp["k_farbe"],
                    sp["s_kontur"], sp["kontur_breite"], sp["vordergrund"])
                gezeichnet.update((name, name + "_kontur"))
        gezeichnet.update(name + "_kontur" for name in tuple(gezeichnet)
                          if name + "_kontur" in store)
        for name in tuple(store):
            if name not in gezeichnet:
                owner._actor_weg(name)
                store.pop(name)
        if optionen["beschriftung"]:
            self._labels(snapshot, gueltig)
        else:
            self.labels_entfernen(koerper_id)
        self.zeichenzustaende[koerper_id] = zustand

    def _labels(self, snapshot, beitraege):
        import pyvista as pv
        from vtkmodules.vtkRenderingCore import vtkActor2D, vtkPolyDataMapper2D, vtkTextActor
        from .core.kraefte_darstellung import zahlenwert
        renderer = self.bruecke._plotter.renderer
        if not any(self.bruecke._layer.ist_an(l) for l in (
                LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT,
                LAYER_HYDRO_RUMPF, LAYER_HYDRO_KIEL, LAYER_HYDRO_RUDER)):
            for koerper in tuple({q[0] for q in self.labels}):
                self.labels_entfernen(koerper)
            return
        ratio = (float(self.bruecke._plotter.devicePixelRatioF()) if hasattr(
            self.bruecke._plotter, "devicePixelRatioF") else 1.0)
        gueltig = {}
        besetzt = []
        eintraege = [(s, b) for s in self.bruecke._kraefte_daten.values()
                     for b in (*s.beitraege, *s.gruppen, s.bilanz)
                     if b.wrench is not None and b.status in GUELTIGE_STATUS]
        for snapshot, beitrag in sorted(eintraege, key=lambda paar: (
                paar[1].instanz_id != self.auswahl,
                paar[1].herkunft != "Gesamtsumme", paar[1].instanz_id)):
            id_ = beitrag.instanz_id
            if id_ != self.auswahl and beitrag.herkunft != "Gesamtsumme":
                continue
            if not self.picklinien.get(id_):
                continue
            optionen = self.bruecke._stil.anzeige()
            wrench = anzeige_wrench(
                snapshot, beitrag, weltursprung=optionen["weltursprung"])
            renderer.SetWorldPoint(
                *(np.asarray(wrench.bezugspunkt_m) + snapshot.szenenversatz_m), 1)
            renderer.WorldToDisplay()
            x, y, tiefe = renderer.GetDisplayPoint()
            anker = (x, y)
            if not 0 <= tiefe <= 1:
                continue
            actor = self.labels.get(id_)
            neu = actor is None
            if actor is None:
                actor = vtkTextActor()
                prop = actor.GetTextProperty()
                prop.SetColor(.1, .1, .1)
                prop.SetBackgroundColor(1, 1, 1)
                prop.SetBackgroundOpacity(.85)
                prop.SetFrame(True)
            actor.GetTextProperty().SetFontSize(max(1, round(
                13 * ratio * 72 / max(1, self.bruecke._plotter.ren_win.GetDPI()))))
            actor.SetInput(
                beitrag.name + " |F|=" + zahlenwert(math.hypot(*wrench.kraft_N), "N")
                + "\n|M um P|=" + zahlenwert(math.hypot(*wrench.moment_Nm), "N*m")
                + (" [Komponenten: Koerperframe]" if optionen["koerperframe"]
                   else " [Komponenten: Weltframe]")
                + (" [aequivalenter Anker]" if beitrag.originalangriff_m is None
                   and beitrag.herkunft not in ("Gesamtsumme", "Gruppensumme") else ""))
            width, height = self.bruecke._plotter.ren_win.GetSize()
            groesse = [0., 0.]
            actor.GetSize(renderer, groesse)
            breite, hoehe = (g + 4 * ratio for g in groesse)
            rand = 5 * ratio
            if breite > width - 2 * rand or hoehe > height - 2 * rand:
                continue
            xs = (min(max(rand, x + 12 * ratio), width - breite - rand),
                  min(max(rand, x - breite - 12 * ratio), width - breite - rand))
            ys = [min(max(rand, y + 12 * ratio), height - hoehe - rand)]
            for _, oy, _, oh in besetzt:
                ys.extend((oy + oh + rand, oy - hoehe - rand))
            position = next(((nx, ny) for ny in ys for nx in xs
                             if rand <= ny <= height - hoehe - rand
                             and all(nx + breite + rand <= ox
                                     or ox + ob + rand <= nx
                                     or ny + hoehe + rand <= oy
                                     or oy + oh + rand <= ny
                                     for ox, oy, ob, oh in besetzt)), None)
            if position is None:
                continue
            x, y = position
            besetzt.append((x, y, breite, hoehe))
            if neu:
                renderer.AddActor(actor)
            actor.SetPosition(x, y)
            linie = self.label_linien.get(id_)
            if linie is None:
                linie = vtkActor2D()
                linie.SetMapper(vtkPolyDataMapper2D())
                linie.GetMapper().ScalarVisibilityOff()
                linie.GetProperty().SetColor(.2, .2, .2)
                renderer.AddActor(linie)
                self.label_linien[id_] = linie
            randpunkt = (min(max(anker[0], x), x + breite),
                         min(max(anker[1], y), y + hoehe))
            linie.GetMapper().SetInputData(pv.Line((*anker, 0), (*randpunkt, 0)))
            gueltig[id_] = actor
        for id_ in tuple(self.labels):
            if id_ not in gueltig:
                renderer.RemoveActor(self.labels.pop(id_))
                renderer.RemoveActor(self.label_linien.pop(id_))
        self.labels.update(gueltig)

    def kandidaten(self, punkt_logisch):
        renderer = self.bruecke._plotter.renderer
        ratio = float(self.bruecke._plotter.devicePixelRatioF()) if hasattr(
            self.bruecke._plotter, "devicePixelRatioF") else 1.0
        treffer = []
        for id_, linien in self.picklinien.items():
            for linie in linien:
                projiziert = []
                for p in linie:
                    renderer.SetWorldPoint(*p, 1)
                    renderer.WorldToDisplay()
                    x, y, _ = renderer.GetDisplayPoint()
                    projiziert.append((x / ratio, y / ratio))
                if abstand_zum_linienzug_px(punkt_logisch, projiziert) <= 6:
                    treffer.append(id_)
                    break
        return tuple(sorted(treffer))
