# -*- coding: utf-8 -*-
"""Komponentenbaum als Qt-freies Datenmodell (Baum-Spec v2, 13.10.).

Quelle: konfigurationen/koerper.json - ab J-1 der Abschnitt 'summenkoerper'
(beliebig viele Hauptobjekte). "Welt" ist reines GUI-Element.

Begriffe: Welt (GUI-Wurzel), Hauptobjekt (oberste Instanz), Systemknoten
(strukturgebend ohne Masse), Unterobjekt (masse-tragend, beliebig tief),
Eigenschaftszeile (Blatt ohne Checkbox).

Regeln: C-1 genau ein Hauptobjekt gecheckt | C-2 Check checkt fremde
Unterobjekte komplett ab | C-3 Check checkt eigene Unterobjekte komplett an |
C-4/C-5/C-6 Gruppen-Checkboxen und Grau-Zustand rekursiv | C-7 abgecheckte
Unterobjekte inaktiv (E-2) | C-8 Schalter 'nur_aktives_bedienbar'
(Standard AUS).
"""
from __future__ import annotations

ART_WELT="welt"; ART_SUMMEN="summen"; ART_GRUPPE="gruppe"; ART_BLATT="blatt"
ICON_GLOBUS="globus"; ICON_YACHT="yacht"; ICON_KEGEL="kegel"; ICON_WUERFEL="wuerfel"
_RESERVIERT=("darstellung",)

class Knoten:
    def __init__(self,name,art,icon_art,aktiv=True,sichtbar=False):
        self.name=name; self.art=art; self.icon_art=icon_art
        self.aktiv=aktiv; self.sichtbar=sichtbar; self.grau=False
        self.eigenschaften=[]; self.kinder=[]; self.eltern=None
    def hinzufuegen(self,kind):
        kind.eltern=self; self.kinder.append(kind); return kind
    def iteriere(self):
        yield self
        for k in self.kinder: yield from k.iteriere()
    def blaetter(self):
        for k in self.iteriere():
            if k.art==ART_BLATT: yield k

def _ist_top(s): return not s.startswith("_") and s not in _RESERVIERT

def _eigenschaften(teil):
    p=[]
    if "material" in teil: p.append(("Material",str(teil["material"])))
    if "dichte_kg_pro_m3" in teil: p.append(("Dichte","%g kg/m3"%teil["dichte_kg_pro_m3"]))
    if "wanddicke_m" in teil: p.append(("Wanddicke","%g mm"%(teil["wanddicke_m"]*1000.0)))
    if "farbe" in teil: p.append(("Farbe",str(teil["farbe"])))
    return p

def _teil_knoten(teil):
    if "teile" in teil:
        k=Knoten(str(teil.get("name","Gruppe")),ART_GRUPPE,ICON_WUERFEL)
        for u in teil["teile"]: k.hinzufuegen(_teil_knoten(u))
        return k
    b=Knoten(str(teil.get("name","Teil")),ART_BLATT,ICON_WUERFEL)
    b.eigenschaften=_eigenschaften(teil)
    return b

def _form_knoten(name,eintrag):
    k=Knoten(str(name),ART_SUMMEN,ICON_KEGEL)
    f=eintrag.get("form",{})
    if f.get("typ")=="cone":
        k.eigenschaften.append(("Form","Kegel H=%g R=%g m"%(f.get("H_m",0),f.get("R_m",0))))
    elif f.get("typ")=="box":
        k.eigenschaften.append(("Form","Quader %gx%gx%g m"%(f.get("dx_m",0),f.get("dy_m",0),f.get("dz_m",0))))
    elif f.get("typ")=="pyramid":
        k.eigenschaften.append(("Form","Pyramide a=%g H=%g m"%(f.get("a_m",0),f.get("H_m",0))))
    k.eigenschaften+=_eigenschaften(eintrag)
    return k

def welt_aus_konfig(konfig):
    """T-4: baut den Welt-Knoten aus dem Konfiguration-Objekt (J-1)."""
    return welt_aus_json({"summenkoerper": konfig.summenkoerper,
                          "darstellung": {"standard_ansicht": konfig.standard_ansicht}})

def welt_aus_json(daten):
    """Baut den Welt-Knoten aus geparsten JSON-Daten (J-1; Uebergangszeit
    versteht weiterhin Top-Level-'boot')."""
    welt=Knoten("Welt",ART_WELT,ICON_GLOBUS,aktiv=True,sichtbar=False)
    sk=daten.get("summenkoerper")
    quelle=sk if isinstance(sk,dict) else {k:v for k,v in daten.items() if _ist_top(k) and isinstance(v,dict)}
    for name,wert in quelle.items():
        if name.startswith("_") or not isinstance(wert,dict): continue
        if "form" in wert:
            welt.hinzufuegen(_form_knoten(name,wert)); continue
        s=Knoten(name,ART_SUMMEN,ICON_YACHT); welt.hinzufuegen(s)
        for teil in wert.get("teile",[]): s.hinzufuegen(_teil_knoten(teil))
    return welt

def einfache_figur(name):
    """Erzeugt einen einfachen Platzhalter-Hauptobjektknoten."""
    return Knoten(name, ART_SUMMEN, ICON_KEGEL)

def standard_ansicht_aus_json(daten):
    da=daten.get("darstellung")
    if isinstance(da,dict):
        sa=da.get("standard_ansicht")
        if isinstance(sa,str) and sa and not sa.startswith("_"): return sa
    return None

def summenkoerper(welt): return [k for k in welt.kinder if k.art==ART_SUMMEN]

def finde(welt,name):
    for k in welt.iteriere():
        if k.name==name: return k
    return None

def _unter_objekte(knoten):
    return [k for k in knoten.iteriere() if k is not knoten and k.art in (ART_GRUPPE,ART_BLATT)]

def _grau_aktualisieren(welt):
    """C-4/C-5/C-6: aktualisiert den Teilaktiv-Zustand des ganzen Baums."""
    def aktualisiere(k):
        kinder = [c for c in k.kinder if c.art in (ART_GRUPPE, ART_BLATT)]
        if not kinder:
            aktiv = bool(k.aktiv) if k.art == ART_BLATT else False
            return aktiv, aktiv
        zustaende = [aktualisiere(c) for c in kinder]
        aktiv = any(teil[0] for teil in zustaende)
        vollstaendig = all(teil[1] for teil in zustaende)
        k.aktiv = vollstaendig
        k.grau = aktiv and not vollstaendig
        return aktiv, vollstaendig

    for hauptobjekt in summenkoerper(welt):
        aktualisiere(hauptobjekt)

def sichtbarkeit_setzen(welt,name):
    """C-1/C-2/C-3: genau ein Hauptobjekt sichtbar + komplett angecheckt."""
    ziel=finde(welt,name)
    if ziel is None or ziel.art!=ART_SUMMEN:
        raise ValueError("kein Hauptobjekt: %r"%(name,))
    for s in summenkoerper(welt):
        s.sichtbar=(s is ziel)
        if s is not ziel:
            for u in _unter_objekte(s): u.aktiv=False   # C-2
    for u in _unter_objekte(ziel): u.aktiv=True          # C-3
    _grau_aktualisieren(welt)

def blatt_setzen(welt,name,aktiv):
    """C-4/C-5/C-6: einzelnes Unterobjekt an/ab + Grau propagieren."""
    ziel = name if isinstance(name, Knoten) else finde(welt, name)
    if ziel is None or ziel.art!=ART_BLATT:
        raise ValueError("kein Blatt: %r"%(name,))
    ziel.aktiv=bool(aktiv)
    _grau_aktualisieren(welt)

def gruppe_setzen(welt, name, aktiv):
    """Aktiviert/deaktiviert alle Blätter einer Gruppe rekursiv."""
    ziel = name if isinstance(name, Knoten) else finde(welt, name)
    if ziel is None or ziel.art != ART_GRUPPE:
        raise ValueError("keine Gruppe: %r" % (name,))
    for knoten in ziel.iteriere():
        if knoten.art == ART_GRUPPE:
            knoten.aktiv = bool(aktiv)
        elif knoten.art == ART_BLATT:
            knoten.aktiv = bool(aktiv)
    _grau_aktualisieren(welt)

def aktive_blaetter(summen_knoten):
    """C-7: nur die Unterobjekte, die physikalisch mitzaehlen."""
    return [b for b in summen_knoten.blaetter() if b.aktiv]
