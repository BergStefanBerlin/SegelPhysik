# -*- coding: utf-8 -*-
# Lader fuer die Konfig-Dateien (Spec V4 J; J-1/J-2 13.10.: summenkoerper).
# koerper.json: 'summenkoerper' (beliebig viele Hauptobjekte; 'teile'=Verband,
# 'form'=einfache Figur cone/box/pyramid) + darstellung (standard_ansicht T-2).
# Kein stiller Fallback; der feste Schluessel 'boot' ist entfernt (klare
# Meldung); unbekannte Top-Level-Abschnitte werden abgelehnt.
# Massen-Regel P3 am Blatt: 'material' ODER Direkt-Tripel
# (dichte_kg_pro_m3+farbe+farbe_unter_wasser); optional wanddicke_m -> Schale.
# Farb-Regel P4: Farbe ist Stoff-Eigenschaft. physik.json (D8): lade_physik().
import json, math, os
KONFIG_ORDNER="konfigurationen"; MATERIAL_DATEI="materialien.json"
KOERPER_DATEI="koerper.json"; PHYSIK_DATEI="physik.json"
VORLAGE_MATERIAL=os.path.join("doc","Vorlagen","materialien_vorlage.json")
VORLAGE_KOERPER=os.path.join("doc","Vorlagen","koerper_vorlage.json")
VORLAGE_PHYSIK=os.path.join("doc","Backlog","physik_vorlage.json")
_VERBOTEN_BLATT=("masse","dichte","flaechenmasse_kg_pro_m2")
_VERBOTEN_GRUPPE=_VERBOTEN_BLATT+("material","wanddicke_m","dichte_kg_pro_m3","farbe","farbe_unter_wasser")
GLANZ_DEFAULT=0.15

class KonfigFehler(ValueError):
    """Verstoss gegen die Regeln der Eingabedateien (Spec J)."""

def _hook(paar):
    g=set()
    for s,_w in paar:
        if s in g: raise KonfigFehler("Doppelter Schluessel: '%s'"%s)
        g.add(s)
    return dict(paar)

def _lies(pfad,vorlage):
    if not os.path.exists(pfad):
        raise KonfigFehler("'%s' nicht gefunden. Bitte einmalig aus der Vorlage kopieren: %s. Kein stiller Fallback (Spec J)."%(pfad,vorlage))
    try:
        with open(pfad, encoding="utf-8") as datei:
            return json.load(datei, object_pairs_hook=_hook)
    except OSError as e:
        raise KonfigFehler("'%s' konnte nicht gelesen werden: %s" % (pfad, e)) from e
    except json.JSONDecodeError as e:
        raise KonfigFehler("Ungueltiges JSON in %s: %s"%(pfad,e)) from e

def _pos(w,wo):
    if isinstance(w,bool) or not isinstance(w,(int,float)) or not w>0:
        raise KonfigFehler("%s: positive Zahl erwartet, gefunden: %r"%(wo,w))
    return float(w)

def _nneg(w,wo):
    if isinstance(w,bool) or not isinstance(w,(int,float)) or w<0:
        raise KonfigFehler("%s: nicht-negative Zahl erwartet, gefunden: %r"%(wo,w))
    return float(w)

def _hex(w,wo):
    if not isinstance(w,str) or not w.startswith("#") or len(w) not in (4,7) \
       or any(z not in set("0123456789abcdefABCDEF") for z in w[1:]):
        raise KonfigFehler("%s: Hex-Farbe erwartet, gefunden: %r"%(wo,w))

def _glanz(w,wo):
    if isinstance(w,bool) or not isinstance(w,(int,float)) or not 0.0<=float(w)<=1.0:
        raise KonfigFehler("%s: Zahl [0..1] erwartet, gefunden: %r"%(wo,w))

def _val_materialien(d,pfad):
    mat=d.get("materialien")
    if not isinstance(mat,dict) or not mat:
        raise KonfigFehler("%s: Abschnitt 'materialien' fehlt oder leer"%pfad)
    for n,b in mat.items():
        if n.startswith("_"): continue
        h="%s.materialien.%s"%(pfad,n)
        if not isinstance(b,dict): raise KonfigFehler("%s: Block erwartet"%h)
        _pos(b.get("dichte_kg_pro_m3"),h+".dichte_kg_pro_m3")
        _hex(b.get("farbe"),h+".farbe"); _hex(b.get("farbe_unter_wasser"),h+".farbe_unter_wasser")
        if "glanz" in b: _glanz(b["glanz"],h+".glanz")
    w=d.get("wasser")
    if not isinstance(w,dict): raise KonfigFehler("%s: Abschnitt 'wasser' fehlt"%pfad)
    dic=w.get("dichten_kg_pro_m3")
    if not isinstance(dic,dict) or not dic:
        raise KonfigFehler("%s: wasser.dichten_kg_pro_m3 fehlt oder leer"%pfad)
    for n,x in dic.items():
        if not n.startswith("_"): _pos(x,"%s.wasser.%s"%(pfad,n))
    if w.get("standard") not in dic:
        raise KonfigFehler("%s: wasser.standard: unbekannter Name"%pfad)

def _val_teil(e,pfad,mats):
    if not isinstance(e,dict) or "name" not in e:
        raise KonfigFehler("%s: Eintrag ohne 'name'"%pfad)
    h="%s (%s)"%(pfad,e["name"])
    if "teile" in e:
        v=[s for s in _VERBOTEN_GRUPPE if s in e]
        if v: raise KonfigFehler("%s: reine Gruppe ohne Massengroesse (P2.5): %s"%(h,v))
        t=e["teile"]
        if not isinstance(t,list) or not t: raise KonfigFehler("%s: leere Gruppe"%h)
        for i,x in enumerate(t): _val_teil(x,"%s.teile[%d]"%(h,i),mats)
        return
    v=[s for s in _VERBOTEN_BLATT if s in e]
    if v: raise KonfigFehler("%s: unzulaessiger Massenschluessel %s (P3)"%(h,v))
    hm="material" in e; hd="dichte_kg_pro_m3" in e
    if hm and hd: raise KonfigFehler("%s: 'material' UND 'dichte_kg_pro_m3' gesetzt - genau EINE Form (P3)"%h)
    if not hm and not hd: raise KonfigFehler("%s: weder 'material' noch Direkt-Tripel (P3/P4)"%h)
    if hm:
        m=e["material"]
        if not isinstance(m,str) or m not in mats:
            raise KonfigFehler("%s: unbekanntes Material %r (nicht in materialien.json)"%(h,m))
        fs=[s for s in ("farbe","farbe_unter_wasser") if s in e]
        if fs: raise KonfigFehler("%s: Farb-Schluessel %s unzulaessig - Farbe ist STOFF-Eigenschaft (P4)"%(h,fs))
    else:
        _pos(e.get("dichte_kg_pro_m3"),h+".dichte_kg_pro_m3")
        _hex(e.get("farbe"),h+".farbe"); _hex(e.get("farbe_unter_wasser"),h+".farbe_unter_wasser")
    if "wanddicke_m" in e: _pos(e["wanddicke_m"],h+".wanddicke_m")

_KOERPER_TOP=("summenkoerper","darstellung")

from .koerper_formen import FORMEN as _FORMEN

def _liste_pruefen(w,h,punkte):
    if not isinstance(w,list) or not w: raise KonfigFehler("%s: nicht leere Liste erwartet"%h)
    for i,x in enumerate(w):
        if not isinstance(x,list) or (punkte and len(x)!=3) or any(isinstance(z,bool) or not isinstance(z,(int,float)) for z in x):
            raise KonfigFehler("%s[%d]: %s erwartet"%(h,i,"[x, y, z]" if punkte else "Liste von Indizes"))

def _val_form(e,h,mats):
    f=e.get("form")
    if not isinstance(f,dict) or "typ" not in f:
        raise KonfigFehler("%s: 'form' mit 'typ' erwartet"%h)
    t=f["typ"]
    if t not in _FORMEN:
        raise KonfigFehler("%s.form.typ: unbekannte Form '%s' (erlaubt: %s)"%(h,t,", ".join(sorted(_FORMEN))))
    d=_FORMEN[t]
    zahl=d.get("zahlen",()); opt=d.get("optionale_zahlen",()); txt=d.get("texte",{})
    lst=d.get("listen",()); olst=d.get("optionale_listen",())
    erlaubt=set(zahl)|set(opt)|set(txt)|set(lst)|set(olst)
    fr=[s for s in f if s!="typ" and s not in erlaubt and not s.startswith("_")]
    if fr: raise KonfigFehler("%s.form: unbekannte Schluessel %s (fuer '%s': %s)"%(h,fr,t,", ".join(sorted(erlaubt))))
    for k in zahl: _pos(f.get(k),"%s.form.%s"%(h,k))
    for k in opt:
        if k in f: _pos(f[k],"%s.form.%s"%(h,k))
    for k,ok in txt.items():
        if k in f and f[k] not in ok:
            raise KonfigFehler("%s.form.%s: erlaubt sind %s"%(h,k,", ".join(ok)))
    for k in lst: _liste_pruefen(f.get(k),"%s.form.%s"%(h,k),k=="eckpunkte_m")
    for k in olst:
        if k in f: _liste_pruefen(f[k],"%s.form.%s"%(h,k),False)
    try:
        _FORMEN[t]["bau"](f)
    except (ValueError,TypeError,AssertionError) as x:
        raise KonfigFehler("%s.form: ungueltige Geometrie: %s"%(h,x))
    v=[s for s in _VERBOTEN_BLATT if s in e]
    if v: raise KonfigFehler("%s: unzulaessiger Massenschluessel %s (P3)"%(h,v))
    hm="material" in e; hd="dichte_kg_pro_m3" in e
    if hm and hd: raise KonfigFehler("%s: 'material' UND 'dichte_kg_pro_m3' gesetzt - genau EINE Form (P3)"%h)
    if not hm and not hd: raise KonfigFehler("%s: weder 'material' noch Direkt-Tripel (P3/P4)"%h)
    if hm:
        m=e["material"]
        if not isinstance(m,str) or m not in mats: raise KonfigFehler("%s: unbekanntes Material %r"%(h,m))
        fs=[s for s in ("farbe","farbe_unter_wasser") if s in e]
        if fs: raise KonfigFehler("%s: Farb-Schluessel %s unzulaessig (P4)"%(h,fs))
    else:
        _pos(e.get("dichte_kg_pro_m3"),h+".dichte_kg_pro_m3")
        _hex(e.get("farbe"),h+".farbe"); _hex(e.get("farbe_unter_wasser"),h+".farbe_unter_wasser")
    if "wanddicke_m" in e: _pos(e["wanddicke_m"],h+".wanddicke_m")

def _val_koerper(d,mats,pfad):
    fr=[s for s in d if s not in _KOERPER_TOP and not s.startswith("_")]
    if fr: raise KonfigFehler("%s: unbekannte Abschnitte %s (erlaubt: %s; Unterstrich = Doku)"%(pfad,fr,", ".join(_KOERPER_TOP)))
    if "boot" in d and "summenkoerper" not in d:
        raise KonfigFehler("%s: Schema geaendert (J-1): der feste Schluessel 'boot' gehoert jetzt unter 'summenkoerper' (z. B. 'yacht1'); Vorlage: doc/Vorlagen/koerper_vorlage.json"%pfad)
    sk=d.get("summenkoerper")
    if not isinstance(sk,dict) or not sk:
        raise KonfigFehler("%s: Abschnitt 'summenkoerper' fehlt oder leer"%pfad)
    for n,e in sk.items():
        if n.startswith("_"): continue
        h="%s.summenkoerper.%s"%(pfad,n)
        if not isinstance(e,dict): raise KonfigFehler("%s: Objekt erwartet"%h)
        ht="teile" in e; hf="form" in e
        if ht and hf: raise KonfigFehler("%s: 'teile' UND 'form' - genau eines (J-1)"%h)
        if ht:
            t=e["teile"]
            if not isinstance(t,list) or not t: raise KonfigFehler("%s: teile leer"%h)
            for i,x in enumerate(t): _val_teil(x,"%s.teile[%d]"%(h,i),mats)
        elif hf: _val_form(e,h,mats)
        else: raise KonfigFehler("%s: weder 'teile' noch 'form' (J-1)"%h)
    da=d.get("darstellung")
    if not isinstance(da,dict): raise KonfigFehler("%s: Abschnitt 'darstellung' fehlt"%pfad)
    dl=da.get("delta_helligkeit_unterwasser")
    if isinstance(dl,bool) or not isinstance(dl,(int,float)) or not 0.0<=float(dl)<=1.0:
        raise KonfigFehler("%s: darstellung.delta_helligkeit_unterwasser: Zahl [0..1]"%pfad)
    _hex(da.get("farbe_standard"), "%s.darstellung.farbe_standard" % pfad)
    sa=da.get("standard_ansicht")
    if sa is not None:
        if not isinstance(sa,str):
            raise KonfigFehler("%s: darstellung.standard_ansicht: String erwartet (T-2)"%pfad)
        if sa.startswith("_") or sa not in sk:
            raise KonfigFehler("%s: darstellung.standard_ansicht: '%s' ist kein Summenkoerper-Name (T-2)"%(pfad,sa))
    gk=da.get("grundkoerper")
    if gk is not None:
        if not isinstance(gk,dict): raise KonfigFehler("%s: darstellung.grundkoerper: Objekt erwartet"%pfad)
        for k,w in gk.items():
            if k.startswith("_"): continue
            if k not in _FORMEN:
                raise KonfigFehler("%s: darstellung.grundkoerper: unbekannter Schluessel '%s' (erlaubt: %s)"%(pfad,k,", ".join(sorted(_FORMEN))))
            _hex(w,"%s.grundkoerper.%s"%(pfad,k))

class Konfiguration:
    def __init__(self,m,k,ordner):
        self._m=m; self._k=k; self.ordner=ordner; self.protokoll=[]
    @property
    def materialien(self):
        return {n:float(b["dichte_kg_pro_m3"]) for n,b in self._m["materialien"].items() if not n.startswith("_")}
    @property
    def materialien_blocks(self):
        return {n:b for n,b in self._m["materialien"].items() if not n.startswith("_")}
    @property
    def wasser_dichten(self): return dict(self._m["wasser"]["dichten_kg_pro_m3"])
    def wasser_dichte(self,x=None):
        if x is None: x=self._m["wasser"]["standard"]
        if isinstance(x,(int,float)): return float(x)
        try: return float(self._m["wasser"]["dichten_kg_pro_m3"][x])
        except KeyError: raise KonfigFehler("Unbekanntes Wasser: '%s'"%x) from None
    @property
    def summenkoerper(self):
        # J-1: Dict aller Hauptobjekte {name: eintrag}
        return self._k["summenkoerper"]
    @property
    def standard_ansicht(self):
        # T-2: Start-Hauptobjekt oder None
        return self._k["darstellung"].get("standard_ansicht")
    @property
    def boot_teile(self):
        # Kompatibilitaet (J-3): Teile des ersten zusammengesetzten Hauptobjekts
        sk=self._k["summenkoerper"]
        for b in ("yacht1","boot"):
            e=sk.get(b)
            if isinstance(e,dict) and "teile" in e: return e["teile"]
        for n,e in sk.items():
            if not n.startswith("_") and isinstance(e,dict) and "teile" in e: return e["teile"]
        return None
    @property
    def delta_helligkeit(self): return float(self._k["darstellung"]["delta_helligkeit_unterwasser"])
    @property
    def farbe_standard(self): return self._k["darstellung"]["farbe_standard"]
    @property
    def grundkoerper_farben(self): return dict(self._k["darstellung"].get("grundkoerper") or {})
    def dichte_von(self,material):
        if isinstance(material,str):
            try: return float(self._m["materialien"][material]["dichte_kg_pro_m3"])
            except KeyError: raise KonfigFehler("Unbekanntes Material: '%s'"%material) from None
        return float(material)
    def farben_von(self,material):
        if isinstance(material,str):
            try:
                b=self._m["materialien"][material]; return b["farbe"],b["farbe_unter_wasser"]
            except KeyError: raise KonfigFehler("Unbekanntes Material: '%s'"%material) from None
        return None
    def glanz_von(self,material):
        if isinstance(material,str):
            try: b=self._m["materialien"][material]
            except KeyError: raise KonfigFehler("Unbekanntes Material: '%s'"%material) from None
            return float(b.get("glanz",GLANZ_DEFAULT))
        return GLANZ_DEFAULT

def lade_konfig(ordner=KONFIG_ORDNER):
    mp=os.path.join(ordner,MATERIAL_DATEI); kp=os.path.join(ordner,KOERPER_DATEI)
    m=_lies(mp,VORLAGE_MATERIAL); k=_lies(kp,VORLAGE_KOERPER)
    _val_materialien(m,mp); _val_koerper(k,m["materialien"],kp)
    return Konfiguration(m,k,ordner)

_PHYSIK=("dt_s","g_m_pro_s2","daempfung","voxel","kraefte")
_DAEMPFUNG=("tauchung","kraengung")
_VOXEL=("aufloesung_m","schranke_volumen_m3","schranke_punkt_m")
_KRAEFTE=("fluidgeschwindigkeit_m_pro_s",
          "fluidwinkelgeschwindigkeit_rad_pro_s",
          "linear_widerstand_kg_pro_s",
          "quadratischer_widerstand_kg_pro_m",
          "added_mass_kg_und_kg_m2")

class PhysikParameter:
    __slots__=("dt_s","g_m_pro_s2","daempfung_tauchung","daempfung_kraengung",
               "voxel_aufloesung_m","schranke_volumen_m3","schranke_punkt_m",
               "fluidgeschwindigkeit","fluidwinkelgeschwindigkeit",
               "linear_widerstand","quadratischer_widerstand",
               "added_mass_diagonal")
    def __init__(self,dt_s,g_m_pro_s2,daempfung_tauchung,daempfung_kraengung,
                 voxel_aufloesung_m,schranke_volumen_m3,schranke_punkt_m,
                 fluidgeschwindigkeit=(0.0,0.0,0.0),
                 fluidwinkelgeschwindigkeit=(0.0,0.0,0.0),
                 linear_widerstand=(0.0,)*6,
                 quadratischer_widerstand=(0.0,)*6,
                 added_mass_diagonal=(0.0,)*6):
        self.dt_s=dt_s; self.g_m_pro_s2=g_m_pro_s2
        self.daempfung_tauchung=daempfung_tauchung
        self.daempfung_kraengung=daempfung_kraengung
        self.voxel_aufloesung_m=voxel_aufloesung_m
        self.schranke_volumen_m3=schranke_volumen_m3
        self.schranke_punkt_m=schranke_punkt_m
        self.fluidgeschwindigkeit=fluidgeschwindigkeit
        self.fluidwinkelgeschwindigkeit=fluidwinkelgeschwindigkeit
        self.linear_widerstand=linear_widerstand
        self.quadratischer_widerstand=quadratischer_widerstand
        self.added_mass_diagonal=added_mass_diagonal
    def __repr__(self):
        return ("PhysikParameter(dt=%g s, g=%g, daempfung=(%g, %g), voxel=%g m, "
                "schranken=(%g m^3, %g m))"%(self.dt_s,self.g_m_pro_s2,
                self.daempfung_tauchung,self.daempfung_kraengung,
                self.voxel_aufloesung_m,self.schranke_volumen_m3,self.schranke_punkt_m))

def _val_physik(d,pfad):
    if not isinstance(d,dict): raise KonfigFehler("%s: Objekt erwartet"%pfad)
    ft=[s for s in d if s!="physik" and not s.startswith("_")]
    if ft or "physik" not in d:
        raise KonfigFehler("%s: alleiniger Abschnitt 'physik' erwartet, fremd: %s"%(pfad,ft))
    p=d["physik"]
    if not isinstance(p,dict): raise KonfigFehler("%s.physik: Objekt erwartet"%pfad)
    fr=[s for s in p if s not in _PHYSIK and not s.startswith("_")]
    if fr: raise KonfigFehler("%s.physik: unbekannte Schluessel %s (erlaubt: %s)"%(pfad,fr,", ".join(_PHYSIK)))
    dt=_pos(p.get("dt_s"),"%s.physik.dt_s"%pfad)
    g=_pos(p.get("g_m_pro_s2"),"%s.physik.g_m_pro_s2"%pfad)
    dae=p.get("daempfung")
    if not isinstance(dae,dict): raise KonfigFehler("%s.physik.daempfung: Objekt erwartet"%pfad)
    fd=[s for s in dae if s not in _DAEMPFUNG and not s.startswith("_")]
    if fd: raise KonfigFehler("%s.physik.daempfung: unbekannte Schluessel %s"%(pfad,fd))
    dta=_nneg(dae.get("tauchung"),"%s.physik.daempfung.tauchung"%pfad)
    dk=_nneg(dae.get("kraengung"),"%s.physik.daempfung.kraengung"%pfad)
    vox=p.get("voxel")
    if not isinstance(vox,dict): raise KonfigFehler("%s.physik.voxel: Objekt erwartet"%pfad)
    fv=[s for s in vox if s not in _VOXEL and not s.startswith("_")]
    if fv: raise KonfigFehler("%s.physik.voxel: unbekannte Schluessel %s"%(pfad,fv))
    au=_pos(vox.get("aufloesung_m"),"%s.physik.voxel.aufloesung_m"%pfad)
    sv=_pos(vox.get("schranke_volumen_m3"),"%s.physik.voxel.schranke_volumen_m3"%pfad)
    sp=_pos(vox.get("schranke_punkt_m"),"%s.physik.voxel.schranke_punkt_m"%pfad)
    kraefte=p.get("kraefte",{})
    if not isinstance(kraefte,dict):
        raise KonfigFehler("%s.physik.kraefte: Objekt erwartet"%pfad)
    fk=[s for s in kraefte if s not in _KRAEFTE and not s.startswith("_")]
    if fk:
        raise KonfigFehler("%s.physik.kraefte: unbekannte Schluessel %s"
                           %(pfad,fk))

    def vektor(schluessel, anzahl, nichtnegativ=False):
        werte=kraefte.get(schluessel,[0.0]*anzahl)
        if not isinstance(werte,list) or len(werte)!=anzahl:
            raise KonfigFehler("%s.physik.kraefte.%s: %d Werte erwartet"
                               %(pfad,schluessel,anzahl))
        ausgabe=[]
        for i,wert in enumerate(werte):
            if (isinstance(wert,bool) or not isinstance(wert,(int,float))
                    or not math.isfinite(float(wert))
                    or (nichtnegativ and wert<0.0)):
                erlaubnis="nicht-negative " if nichtnegativ else ""
                raise KonfigFehler(
                    "%s.physik.kraefte.%s[%d]: %sendliche Zahl erwartet"
                    %(pfad,schluessel,i,erlaubnis))
            ausgabe.append(float(wert))
        return tuple(ausgabe)

    fv=vektor("fluidgeschwindigkeit_m_pro_s",3)
    fw=vektor("fluidwinkelgeschwindigkeit_rad_pro_s",3)
    linear=vektor("linear_widerstand_kg_pro_s",6,True)
    quadratisch=vektor("quadratischer_widerstand_kg_pro_m",6,True)
    added=vektor("added_mass_kg_und_kg_m2",6,True)
    return dict(dt_s=dt,g_m_pro_s2=g,daempfung_tauchung=dta,daempfung_kraengung=dk,
                voxel_aufloesung_m=au,schranke_volumen_m3=sv,schranke_punkt_m=sp,
                fluidgeschwindigkeit=fv,fluidwinkelgeschwindigkeit=fw,
                linear_widerstand=linear,quadratischer_widerstand=quadratisch,
                added_mass_diagonal=added)

def lade_physik(ordner=KONFIG_ORDNER):
    pf=os.path.join(ordner,PHYSIK_DATEI)
    d=_lies(pf,VORLAGE_PHYSIK); w=_val_physik(d,pf)
    return PhysikParameter(**w)
