# -*- coding: utf-8 -*-
"""Block H (J-5): Schema-Tests fuer die summenkoerper-Struktur (J-1)."""
import json, os, tempfile
from segelphysik.core.konfig_lader import lade_konfig, KonfigFehler

def _schreibe(od, mat, kor):
    open(os.path.join(od,"materialien.json"),"w",encoding="utf-8").write(json.dumps(mat))
    open(os.path.join(od,"koerper.json"),"w",encoding="utf-8").write(json.dumps(kor))

def _mat():
    return {"materialien":{"Test":{"dichte_kg_pro_m3":1000,"farbe":"#cccccc","farbe_unter_wasser":"#999999"}},
            "wasser":{"dichten_kg_pro_m3":{"Suess":1000},"standard":"Suess"}}

def _kor():
    return {"summenkoerper":{
              "yacht1":{"teile":[{"name":"wuerfel","material":"Test"}]},
              "quader":{"form":{"typ":"box","dx_m":2.0,"dy_m":2.0,"dz_m":2.0},
                        "dichte_kg_pro_m3":950,"farbe":"#00b140","farbe_unter_wasser":"#00802e"}},
            "darstellung":{"delta_helligkeit_unterwasser":0.4,
                           "farbe_standard":"#c9c9c9","standard_ansicht":"quader"}}

def test_j1_gueltige_mehrfach_struktur_laedt():
    with tempfile.TemporaryDirectory() as od:
        _schreibe(od,_mat(),_kor())
        k=lade_konfig(od)
        assert set(k.summenkoerper)=={"yacht1","quader"}
        assert k.standard_ansicht=="quader"
        assert k.boot_teile==_kor()["summenkoerper"]["yacht1"]["teile"]

def test_j2_altes_boot_schema_klare_meldung():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor(); del kor["summenkoerper"]
        kor["boot"]={"teile":[{"name":"wuerfel","material":"Test"}]}
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler as e:
            assert "summenkoerper" in str(e)

def test_j3_fremder_top_abschnitt_abgelehnt():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor(); kor["fremd"]={}
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_j4_leere_summenkoerper_liste_fehler():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor(); kor["summenkoerper"]={}
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_j5_unbekannte_form_fehler():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor()
        kor["summenkoerper"]["kugel"]={"form":{"typ":"kugel","R_m":1.0},
                                       "dichte_kg_pro_m3":500,
                                       "farbe":"#123456","farbe_unter_wasser":"#654321"}
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_j6_standard_ansicht_muss_existieren():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor(); kor["darstellung"]["standard_ansicht"]="nixda"
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_j7_form_mit_gruppe_gemeinsam_fehler():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor()
        kor["summenkoerper"]["x"]={"form":{"typ":"box","dx_m":1.0,"dy_m":1.0,"dz_m":1.0},
                                   "teile":[{"name":"a","material":"Test"}]}
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_h3_fremder_massenschluessel_fehler():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor(); kor["summenkoerper"]["yacht1"]["teile"][0]["flaechenmasse_kg_pro_m2"]=0.5
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_h4_unbekanntes_material_cross_file():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor(); kor["summenkoerper"]["yacht1"]["teile"][0]["material"]="Unobtainium"
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_h5_doppelter_schluessel_beide_dateien():
    with tempfile.TemporaryDirectory() as od:
        roh='{"materialien": {"A": 1, "A": 2}, "wasser": {"dichten_kg_pro_m3": {"S": 1000}, "standard": "S"}}'
        open(os.path.join(od,"materialien.json"),"w",encoding="utf-8").write(roh)
        open(os.path.join(od,"koerper.json"),"w",encoding="utf-8").write(json.dumps(_kor()))
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass

def test_h6_gruppe_mit_masseschluessel_fehler():
    with tempfile.TemporaryDirectory() as od:
        kor=_kor(); kor["summenkoerper"]["yacht1"]["teile"][0]={"name":"g","material":"Test","teile":[{"name":"a","material":"Test"}]}
        _schreibe(od,_mat(),kor)
        try:
            lade_konfig(od); assert False,"KonfigFehler erwartet"
        except KonfigFehler:
            pass
