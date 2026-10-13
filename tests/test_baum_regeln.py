# -*- coding: utf-8 -*-
"""Baum-Regel-Tests (P-1..P-5, Baum-Spec v2) - Qt-frei."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from segelphysik.gui.baum import (welt_aus_json, standard_ansicht_aus_json,
    summenkoerper, finde, sichtbarkeit_setzen, blatt_setzen, gruppe_setzen,
    aktive_blaetter)

def _welt():
    return welt_aus_json({"summenkoerper":{
        "yacht1":{"teile":[
            {"name":"rumpf","material":"GfK"},
            {"name":"kielsystem","teile":[{"name":"kiel","material":"Stahl"},
                                          {"name":"bulb","material":"Blei"}]}]},
        "yacht2":{"teile":[{"name":"rumpf","material":"GfK"}]},
        "kegel":{"form":{"typ":"cone","H_m":2.0,"R_m":1.0},"dichte_kg_pro_m3":500,
                 "farbe":"#ff6a00","farbe_unter_wasser":"#b34700"},
        "quader":{"form":{"typ":"box","dx_m":2.0,"dy_m":2.0,"dz_m":2.0},
                  "dichte_kg_pro_m3":950,"farbe":"#00b140","farbe_unter_wasser":"#00802e"},
        "pyramide":{"form":{"typ":"pyramid","a_m":2.0,"H_m":2.0},"dichte_kg_pro_m3":500,
                    "farbe":"#d40078","farbe_unter_wasser":"#99005a"}},
        "darstellung":{"standard_ansicht":"quader"}})

def test_p5_fuenf_hauptobjekte():
    w=_welt(); assert len(summenkoerper(w))==5

def test_p4_standard_ansicht():
    assert standard_ansicht_aus_json({"darstellung":{"standard_ansicht":"quader"}})=="quader"
    assert standard_ansicht_aus_json({}) is None

def test_p1_single_choice_mit_unterobjekten():
    w=_welt()
    sichtbarkeit_setzen(w,"yacht1")
    yacht1=finde(w,"yacht1"); yacht2=finde(w,"yacht2")
    assert yacht1.sichtbar and not yacht2.sichtbar
    assert all(k.aktiv for k in yacht1.blaetter())     # C-3
    assert not any(k.aktiv for k in yacht2.blaetter()) # C-2
    sichtbarkeit_setzen(w,"quader")
    q=finde(w,"quader")
    assert q.sichtbar and not yacht1.sichtbar
    assert not any(k.aktiv for k in yacht1.blaetter()) # C-2 auch beim Wechsel

def test_p2_grau_rekursiv():
    w=_welt()
    sichtbarkeit_setzen(w,"yacht1")
    blatt_setzen(w,"kiel",False)
    kielsystem=finde(w,"kielsystem"); yacht1=finde(w,"yacht1")
    assert kielsystem.grau and yacht1.grau             # C-6
    blatt_setzen(w,"kiel",True)
    assert not kielsystem.grau and not yacht1.grau     # C-5

def test_p3_c8_schalter_platzhalter():
    w=_welt(); sichtbarkeit_setzen(w,"yacht1")
    blatt_setzen(w,"kiel",False)
    assert not finde(w,"kiel").aktiv

def test_gruppen_checkbox_aktiviert_und_deaktiviert_alle_nachfahren():
    w=_welt(); sichtbarkeit_setzen(w,"yacht1")
    gruppe_setzen(w,"kielsystem",False)
    assert not finde(w,"kiel").aktiv
    assert not finde(w,"bulb").aktiv
    assert not finde(w,"kielsystem").grau
    gruppe_setzen(w,"kielsystem",True)
    assert finde(w,"kiel").aktiv and finde(w,"bulb").aktiv
    assert not finde(w,"kielsystem").grau

def test_grau_zustand_nur_bei_tatsaechlicher_teilaktivitaet():
    w=_welt(); sichtbarkeit_setzen(w,"yacht1")
    blatt_setzen(w,"kiel",False)
    assert finde(w,"kielsystem").grau
    gruppe_setzen(w,"kielsystem",False)
    assert not finde(w,"kielsystem").grau

def test_blatt_gezielt_ueber_knoten_umschaltbar():
    w=_welt(); sichtbarkeit_setzen(w,"yacht1")
    kiel=finde(w,"kiel")
    blatt_setzen(w,kiel,False)
    assert not kiel.aktiv
    assert finde(w,"kielsystem").grau

def test_teilaktivitaet_propagiert_bis_zum_hauptobjekt():
    w=_welt()
    sichtbarkeit_setzen(w,"kegel")
    bulb=finde(w,"bulb")
    blatt_setzen(w,bulb,True)
    assert finde(w,"kielsystem").grau
    assert finde(w,"yacht1").grau
