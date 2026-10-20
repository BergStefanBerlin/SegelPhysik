"""Erzeugt das aufloesbare Einzelfunktionsinventar aus der V0.10-Spezifikation.

Nur explizit in der Spezifikation benannte Quellmodule werden gelesen.
Nicht gemessene Funktionen bleiben offen, nicht vermeintlich unkritisch.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VERSION = ROOT / "doc" / "WegZuV1.0" / "Revisionslog" / "zuV0.10"
SPEC = VERSION / "Spezifikationen" / "Spezifikation_CPP_Migration_V0.10.md"
PLAN = VERSION / "Umsetzungsplan" / "Umsetzungsanleitung_CPP_Migration_V0.10.md"
QUELLEN = ROOT / "code" / "python" / "segelphysik"
REFERENZ = "7a955c24ceb6c0825e05a574b959dd1176be2e2c"


def texthash(pfad):
    return hashlib.sha256(pfad.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def definitionen(pfad):
    ergebnis = []

    def besuchen(knoten, eltern=()):
        for kind in ast.iter_child_nodes(knoten):
            if isinstance(kind, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                qualifiziert = eltern + (kind.name,)
                if not isinstance(kind, ast.ClassDef):
                    profilzeile = min(
                        [kind.lineno] + [d.lineno for d in kind.decorator_list])
                    ergebnis.append((
                        ".".join(qualifiziert), kind.lineno, kind.end_lineno, profilzeile))
                besuchen(kind, qualifiziert)
            else:
                besuchen(kind, eltern)

    besuchen(ast.parse(pfad.read_text(encoding="utf-8")))
    return ergebnis


def spezifikationseintraege(text):
    abschnitte = list(re.finditer(
        r"^#### (A-V0\.10-\d{5})[^\n]*\n(.*?)(?=^#{3,4} A-V0\.10-|\Z)",
        text, re.M | re.S))
    if {int(m[1][-5:]) for m in abschnitte} != set(range(6, 31)):
        raise ValueError("Einzelfunktionsabschnitte 00006 bis 00030 fehlen")
    for match in abschnitte:
        aid, inhalt = match[1], match[2]
        vorspann = inhalt.split("\n|", 1)[0]
        module = re.findall(r"`([\w/]+\.py)`", vorspann)
        zeilen = [z for z in inhalt.splitlines() if z.startswith("|")]
        if not zeilen:
            # A00018 benennt seine vier Funktionen im Fliesstext.
            zeilen = ["| " + vorspann.split(".py`.", 1)[1] + " |"]
        else:
            zeilen = zeilen[2:]
        for zeile in zeilen:
            spalten = zeile.split("|")[1:-1]
            modulspalte = re.findall(r"`([\w/]+\.py)`", spalten[0])
            if modulspalte:
                dateien, funktionsspalte = modulspalte, spalten[1]
            else:
                dateien = module
                funktionsspalte = spalten[0] if "`" in spalten[0] else spalten[1]
            klasse = None
            for name in re.findall(r"`([^`]+)`", funktionsspalte):
                if not re.fullmatch(r"[\w.]+", name):
                    raise ValueError("Unbekanntes Funktionsformat: " + name)
                if "." in name and name.split(".")[0][0].isupper():
                    klasse = name.rsplit(".", 1)[0]
                yield aid, dateien, name, klasse, zeile.strip()


def inventar():
    spec = SPEC.read_text(encoding="utf-8")
    plan = PLAN.read_text(encoding="utf-8")
    matrix = {
        aid: re.findall(r"U-V0\.10-\d{6}", schritte)
        for aid, schritte in re.findall(
            r"^\| (A-V0\.10-\d{5}) \| [^|]+ \| ([^|]+) \|", plan, re.M)
    }
    meilensteine = {
        uid: milestone for uid, milestone in re.findall(
            r"^### (U-V0\.10-\d{6}).*?\*\*Meilenstein:\*\* (M\d+)",
            plan, re.M | re.S)
    }
    tests = {
        milestone: re.findall(r"`(test_\w+\.py)`", gruppe)
        for milestone, gruppe in re.findall(r"^\| (M\d+) \| ([^|]+) \|", plan, re.M)
    }
    module = {}
    eintraege = []
    for aid, dateien, name, klasse, zeile in spezifikationseintraege(spec):
        kandidaten = []
        for datei in dateien:
            if datei not in module:
                pfad = QUELLEN / datei
                module[datei] = definitionen(pfad)
            suchname = name
            if name.startswith(Path(datei).stem + "."):
                suchname = name.split(".", 1)[1]
            if "." not in suchname and klasse:
                suchname = klasse + "." + suchname
            for qualifiziert, start, ende, profilzeile in module[datei]:
                if (qualifiziert == suchname
                        or ("." not in suchname and qualifiziert.endswith("." + suchname))):
                    kandidaten.append((datei, qualifiziert, start, ende, profilzeile))
        if len(kandidaten) != 1:
            raise ValueError("%s/%s: Quelle nicht eindeutig: %s" % (aid, name, kandidaten))
        datei, qualifiziert, start, ende, profilzeile = kandidaten[0]
        eintrag = {
            "anforderung": aid, "umsetzungsschritte": matrix[aid],
            "modul": datei, "funktion": qualifiziert,
            "zeile": start, "ende_zeile": ende, "spec_zeile": zeile,
            "profilzeile": profilzeile, "erzeugte_closure": False,
            "quell_sha256": texthash(QUELLEN / datei),
            "regressionstests": sorted({
                test for uid in matrix[aid]
                for test in tests[meilensteine[uid]]
            }),
            "direkter_paritaetsfall": "Geplant: " + qualifiziert + " / " + zeile,
            "nativer_elternblock": None,
            "status": "noch offen/blockiert, mit konkreter Ursache",
            "ursache": "Zeitkritikalitaet, Paritaet und nativer Gewinn noch zu messen.",
            "profilbelege": [], "paritaetsbelege": [],
            "aufrufpfad": None, "aufrufe": None,
            "eigenzeit_s": None, "gesamtzeit_s": None, "eingabegroesse": None,
            "native_bibliotheksanteile": None,
        }
        eintraege.append(eintrag)
        for kind, kind_start, kind_ende, kind_profil in module[datei]:
            if kind.startswith(qualifiziert + "."):
                eintraege.append({
                    **eintrag, "funktion": kind,
                    "zeile": kind_start, "ende_zeile": kind_ende,
                    "profilzeile": kind_profil, "erzeugte_closure": True,
                    "direkter_paritaetsfall": "Geplant: Closure von " + qualifiziert,
                })
    return {
        "fassung": 1, "python_referenzcommit": REFERENZ,
        "spec_sha256": texthash(SPEC), "eintraege": eintraege,
        "hinweis": "Statisches Startinventar; kein Hotspot- oder Migrationsabschluss.",
    }


def referenzdateien():
    namen = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", REFERENZ], cwd=ROOT,
        text=True, encoding="utf-8").splitlines()
    return [
        name for name in namen
        if name.startswith(("code/", "konfigurationen/",
                            "doc/WegZuV1.0/Revisionslog/zuV0.7/Widgets/"))
        or name in ("segelphysik.py", "requirements.txt", "requirements-dev.txt",
                    "pyproject.toml",
                    "doc/WegZuV1.0/Revisionslog/zuV0.9/Messungen/"
                    "Genauigkeit_Referenzfaelle_v0.9.json")
    ]


PRODUKTIVE_MIGRATIONSDATEIEN = frozenset({
    "code/python/segelphysik/core/dynamik_6dof.py",
    "code/python/segelphysik/core/frames.py",
    "code/python/segelphysik/core/koerper.py",
    "code/python/segelphysik/core/volumen_union.py",
    "code/python/segelphysik/core/hydrostatik.py",
    "code/python/segelphysik/core/hydrodynamik.py",
    "code/python/segelphysik/core/kraftmodell.py",
    "code/python/segelphysik/core/auftrieb.py",
    "code/python/segelphysik/core/echtzeit_prozess.py",
    "code/python/segelphysik/core/stationaer_hydrodynamik.py",
    "code/python/segelphysik/core/bewegung.py",
    "code/python/segelphysik/core/stoerung.py",
    "code/python/segelphysik/core/statisch.py",
    "code/python/segelphysik/core/statisch_robust.py",
    "code/python/segelphysik/core/massen.py",
    "code/python/segelphysik/core/koerper_formen.py",
    "code/python/segelphysik/core/mesh.py",
    "code/python/segelphysik/core/voxelmodell.py",
    "code/python/segelphysik/core/dynamik.py",
    "code/python/segelphysik/core/navigationsanzeigen.py",
    "code/python/segelphysik/core/wasserpunkte.py",
    "code/python/segelphysik/core/kraefte_bild.py",
    "code/python/segelphysik/core/overlays.py",
    "code/python/segelphysik/render/vista.py",
    "code/python/segelphysik/grafik_bruecke.py",
    "code/python/segelphysik/gui/app.py",
    "code/python/segelphysik/gui/hauptfenster.py",
    "code/python/segelphysik/gui/navigationswidgets.py",
    "code/python/segelphysik/wasser_schnitt.py",
})


def referenzmanifest(*, native_kandidaten=False, produktive_migration=False):
    dateien = {}
    kandidatendateien = []
    produktivdateien = []
    for name in referenzdateien():
        original = subprocess.check_output(
            ["git", "show", REFERENZ + ":" + name], cwd=ROOT)
        sha = hashlib.sha256(original.replace(b"\r\n", b"\n")).hexdigest()
        aktuell = texthash(ROOT / name)
        if aktuell != sha:
            if produktive_migration and name in PRODUKTIVE_MIGRATIONSDATEIEN:
                produktivdateien.append({
                    "datei": name, "referenz_sha256": sha,
                    "produktiv_sha256": aktuell})
            elif native_kandidaten and name.startswith("code/cpp/"):
                kandidatendateien.append({
                    "datei": name, "referenz_sha256": sha, "kandidat_sha256": aktuell})
            else:
                raise ValueError("Referenzdatei weicht vom Sicherungscommit ab: " + name)
        dateien[name] = sha
    daten = {"fassung": 1, "commit": REFERENZ,
             "hashverfahren": "SHA256; CRLF nach LF normalisiert",
             "dateien": dateien}
    if native_kandidaten:
        daten["abweichende_native_kandidatendateien"] = kandidatendateien
        daten["hinweis"] = (
            "Originalreferenzen bleiben aus dem Sicherungscommit erhalten. "
            "Nur explizit gewaehlte native Kandidatenquellen duerfen abweichen; "
            "Python, Modelle, Konfigurationen und eingefrorene Werte bleiben streng geprueft.")
    if produktive_migration:
        daten["abweichende_produktive_migrationsdateien"] = produktivdateien
        daten["hinweis_produktive_migration"] = (
            "Expliziter Integrationsmodus: einzeln benannte produktive Quellen "
            "duerfen abweichen; Originalhashes bleiben unveraendert. Modelle, "
            "Konfigurationen und eingefrorene Werte bleiben strikt geprueft.")
    return daten


def profilbewertung(profil):
    """Wertet exklusive Zeiten aus; native Kanten nur fuer direkte Aufrufer."""
    gesamt = 0.
    python_projekt = 0.
    native = 0.
    andere = 0.
    anomalien = []
    direkte_native = {}
    for funktion in profil:
        eigenzeit = funktion["eigenzeit_s"]
        kumuliert = funktion["gesamtzeit_s"]
        if (not math.isfinite(eigenzeit) or not math.isfinite(kumuliert)
                or eigenzeit < 0 or kumuliert < 0):
            raise ValueError("Ungueltige Profilzeiten")
        if kumuliert < eigenzeit:
            anomalien.append({
                key: funktion[key] for key in
                ("datei", "zeile", "funktion", "eigenzeit_s", "gesamtzeit_s")})
        gesamt += eigenzeit
        if funktion["datei"].startswith("code/python/segelphysik/"):
            python_projekt += eigenzeit
        elif funktion["datei"] != "~":
            andere += eigenzeit
        if funktion["datei"] != "~":
            continue
        native += eigenzeit
        for aufrufer in funktion["aufrufer"]:
            pfad = Path(aufrufer["datei"])
            if pfad.is_absolute() and pfad.is_relative_to(ROOT):
                pfad = pfad.relative_to(ROOT)
            key = (pfad.as_posix(), aufrufer["zeile"])
            statistik = aufrufer["statistik"]
            zeit = statistik[2] if isinstance(statistik, (tuple, list)) else None
            if zeit is not None and (not math.isfinite(zeit) or zeit < 0):
                raise ValueError("Ungueltige native Profilkante")
            direkte_native.setdefault(key, []).append({
                "funktion": funktion["funktion"],
                "aufrufe": statistik[1] if isinstance(statistik, (tuple, list)) else statistik,
                "eigenzeit_s": zeit})
    if not math.isfinite(gesamt) or gesamt <= 0:
        raise ValueError("Positive Profilgesamtzeit erforderlich")
    return {
        "summe_eigenzeiten_s": gesamt,
        "projekt_python_eigenzeit_s": python_projekt,
        "native_eigenzeit_s": native,
        "andere_eigenzeit_s": andere,
        "zeitbewertung_gueltig": not anomalien, "zeitanomalien": anomalien,
        "native_anteile": direkte_native,
    }


def messnachweise(dateien):
    """Ordnet explizit angegebene Rohprofile zu, ohne Gesamtzeiten zu addieren."""
    if not dateien or len({p.resolve() for p in dateien}) != len(dateien):
        raise ValueError("Eindeutige, nicht leere Rohprofilliste erforderlich")
    daten = inventar()
    for eintrag in daten["eintraege"]:
        eintrag["profilbelege"] = []
    quellen = []
    bewertungen = []
    for datei in dateien:
        inhalt = json.loads(datei.read_text(encoding="utf-8"))
        profile = {}
        if "instrumentierte_profile" in inhalt:
            profile = inhalt["instrumentierte_profile"]
        elif "profil" in inhalt:
            profile = {"diagnoseprofil": inhalt["profil"]}
        elif "instrumentiertes_solverprofil" in inhalt:
            profile = {"stationaerer_solver": inhalt["instrumentiertes_solverprofil"]}
        elif "gui_callback_profil" in inhalt:
            profile = {"synchrone_gui_callbacks": inhalt["gui_callback_profil"]}
        else:
            raise ValueError("Keine vollstaendigen Rohprofile in " + str(datei))
        pfad = datei.resolve().relative_to(ROOT).as_posix()
        sha = texthash(datei)
        quellen.append({"datei": pfad, "sha256": sha})
        for szenario, profil in profile.items():
            bewertung = profilbewertung(profil)
            bewertungen.append({
                "rohdatei": pfad, "sha256": sha, "szenario": szenario,
                **{k: v for k, v in bewertung.items() if k != "native_anteile"},
            })
            for eintrag in daten["eintraege"]:
                for funktion in profil:
                    if (funktion["datei"] != "code/python/segelphysik/" + eintrag["modul"]
                            or funktion["zeile"] != eintrag["profilzeile"]
                            or funktion["aufrufe"] <= 0):
                        continue
                    eintrag["profilbelege"].append({
                        "rohdatei": pfad, "sha256": sha, "szenario": szenario,
                        "aufrufe": funktion["aufrufe"],
                        "eigenzeit_s": funktion["eigenzeit_s"],
                        "gesamtzeit_s": funktion["gesamtzeit_s"],
                        "profilzeitbewertung_gueltig": bewertung["zeitbewertung_gueltig"],
                        "profil_eigenzeitanteil": (
                            funktion["eigenzeit_s"] / bewertung["summe_eigenzeiten_s"]
                            if bewertung["zeitbewertung_gueltig"] else None),
                        "profil_gesamtzeitanteil": (
                            funktion["gesamtzeit_s"] / bewertung["summe_eigenzeiten_s"]
                            if bewertung["zeitbewertung_gueltig"] else None),
                        "direkte_native_aufrufe": bewertung["native_anteile"].get(
                            (funktion["datei"], funktion["zeile"]), []),
                        "aufrufer": funktion["aufrufer"],
                    })
    daten["profilquellen"] = quellen
    daten["profilbewertungen"] = bewertungen
    daten["eintraege_mit_aufrufbeleg"] = sum(
        bool(e["profilbelege"]) for e in daten["eintraege"])
    daten["hinweis"] = (
        "Kumulierte Aufrufbelege, nicht automatisch Zeitkritikalitaet. "
        "Tests koennen Funktionen mocken oder nur Fehlerwege aufrufen. "
        "Profilzeiten verschiedener Quellen/Elternbloecke nicht summieren. "
        "Native Zeiten umfassen auch CPython, I/O und Warten, nicht nur Numerik. "
        "Direkte native Kanten enthalten keine transitiven Bibliotheksaufrufe "
        "und sind kein vollstaendiger nativer Anteil eines Elternblocks. "
        "Der threadlokale Python-Profiler liefert Kantenaufrufe ohne Kantenzeit "
        "(eigenzeit_s=null), keine erfundenen Nullzeiten. "
        "Instrumentierte Anteile begruenden weder End-to-End-Gewinn noch Abnahme.")
    return daten


def schreiben(pfad, daten):
    text = json.dumps(daten, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("x", encoding="utf-8") as stream:
        stream.write(text)


def testnachweise(dateien):
    if not dateien or len({p.resolve() for p in dateien}) != len(dateien):
        raise ValueError("Eindeutige, nicht leere Testprofilliste erforderlich")
    daten = inventar()
    quellen = []
    for datei in dateien:
        inhalt = json.loads(datei.read_text(encoding="utf-8"))
        if inhalt["exitcode"] != 0:
            raise ValueError("Testprofil mit fehlgeschlagener Suite: " + str(datei))
        bestanden = {
            t["test"] for t in inhalt["tests"]
            if t["phase"] == "call" and t["ergebnis"] == "passed"}
        pfad = datei.resolve().relative_to(ROOT).as_posix()
        sha = texthash(datei)
        quellen.append({"datei": pfad, "sha256": sha})
        for node, profil in inhalt["testprofile"].items():
            if node not in bestanden:
                continue
            lookup = {
                (f["datei"], f["zeile"]): f["aufrufe"] for f in profil
                if f["aufrufe"] > 0}
            for eintrag in daten["eintraege"]:
                aufrufe = lookup.get((
                    "code/python/segelphysik/" + eintrag["modul"], eintrag["profilzeile"]))
                if aufrufe is not None:
                    eintrag.setdefault("konkrete_referenztests", []).append({
                        "rohdatei": pfad, "sha256": sha, "test": node, "aufrufe": aufrufe,
                        "ergebnis": "passed", "nativer_vergleich": False,
                    })
    daten["testprofilquellen"] = quellen
    daten["eintraege_mit_testbeleg"] = sum(
        bool(e.get("konkrete_referenztests")) for e in daten["eintraege"])
    daten["hinweis"] = (
        "Konkrete ausgefuehrte Python-Referenztests statt nur Testgruppen. "
        "Ein Funktionsaufruf beweist nicht automatisch jede interne Berechnung "
        "oder jeden Rueckgabewert. Keine native Paritaet oder Performanceabnahme; "
        "direkte Kandidatenvergleiche bleiben im jeweiligen Migrationsgate Pflicht.")
    return daten


def pruefplan(profildatei, testdatei):
    profile = json.loads(profildatei.read_text(encoding="utf-8"))
    tests = json.loads(testdatei.read_text(encoding="utf-8"))
    aktuell = inventar()
    for matrix in (profile, tests):
        if (matrix["python_referenzcommit"] != REFERENZ
                or matrix["spec_sha256"] != aktuell["spec_sha256"]):
            raise ValueError("Pruefmatrix hat eine andere Referenz oder Spezifikation")
    for quelle in [*profile["profilquellen"], *tests["testprofilquellen"]]:
        if texthash(ROOT / quelle["datei"]) != quelle["sha256"]:
            raise ValueError("Nachweisquelle geaendert: " + quelle["datei"])
    testprofile = {}
    testbewertungen = {}
    for quelle in tests["testprofilquellen"]:
        roh = json.loads((ROOT / quelle["datei"]).read_text(encoding="utf-8"))
        if roh["exitcode"] != 0 or not roh["testquellen_sha256"]:
            raise ValueError("Erfolgreiche Testquelle mit Quellhashes erforderlich")
        for datei, sha in roh["testquellen_sha256"].items():
            if texthash(ROOT / datei) != sha:
                raise ValueError("Referenztestquelle geaendert: " + datei)
        testprofile[quelle["datei"]] = roh.get("testprofile", {})

    def schluessel(eintrag):
        return (eintrag["anforderung"], eintrag["modul"], eintrag["funktion"],
                eintrag["zeile"], eintrag["spec_zeile"])

    profillookup = {schluessel(e): e for e in profile["eintraege"]}
    testlookup = {schluessel(e): e for e in tests["eintraege"]}
    erwartet = {schluessel(e) for e in aktuell["eintraege"]}
    if (set(profillookup) != erwartet or set(testlookup) != erwartet
            or len(profile["eintraege"]) != len(erwartet)
            or len(tests["eintraege"]) != len(erwartet)):
        raise ValueError("Unvollstaendige oder abweichende Funktionsmatrix")
    testquellen = {}
    messquellen = {}
    eintraege = []
    for eintrag in aktuell["eintraege"]:
        if texthash(QUELLEN / eintrag["modul"]) != eintrag["quell_sha256"]:
            raise ValueError("Produktivquelle geaendert: " + eintrag["modul"])
        key = schluessel(eintrag)
        testbelege = testlookup[key].get("konkrete_referenztests", [])
        if not testbelege:
            raise ValueError("Konkreter Referenztest fehlt: " + str(key))
        direkte_tests = []
        testmessungen = []
        for beleg in testbelege:
            node = beleg["test"]
            datei, *teile = node.split("::")
            if not teile:
                raise ValueError("Testfunktion fehlt in Node-ID: " + node)
            if datei not in testquellen:
                pfad = ROOT / datei
                testquellen[datei] = definitionen(pfad)
            funktion = ".".join(teile).split("[", 1)[0]
            funde = [d for d in testquellen[datei] if d[0] == funktion]
            if len(funde) != 1:
                raise ValueError("Testquelle nicht eindeutig: " + node)
            _, start, ende, dekorator = funde[0]
            direkte_tests.append({
                "test": node, "datei": datei, "sha256": texthash(ROOT / datei),
                "von_zeile": dekorator, "bis_zeile": ende,
                "eingaben_und_assertionen": (
                    "Unveraenderte Testdefinition einschliesslich Parametrisierung, "
                    "referenzierter Fixtures und Helfer. Keine neue Toleranzfreigabe."),
            })
            rohdatei = beleg.get("rohdatei")
            if rohdatei is not None:
                rohprofil = testprofile[rohdatei][node]
                profilkey = (rohdatei, node)
                if profilkey not in testbewertungen:
                    testbewertungen[profilkey] = profilbewertung(rohprofil)
                bewertung = testbewertungen[profilkey]
                funktionen = [
                    f for f in rohprofil
                    if f["datei"] == "code/python/segelphysik/" + eintrag["modul"]
                    and f["zeile"] == eintrag["profilzeile"] and f["aufrufe"] > 0]
                if len(funktionen) != 1:
                    raise ValueError("Direkter Funktionsprofilbeleg fehlt: " + node)
                f = funktionen[0]
                testmessungen.append({
                    "rohdatei": rohdatei, "sha256": beleg["sha256"], "szenario": node,
                    "aufrufe": f["aufrufe"], "eigenzeit_s": f["eigenzeit_s"],
                    "gesamtzeit_s": f["gesamtzeit_s"],
                    "profilzeitbewertung_gueltig": bewertung["zeitbewertung_gueltig"],
                    "profil_eigenzeitanteil": (
                        f["eigenzeit_s"] / bewertung["summe_eigenzeiten_s"]
                        if bewertung["zeitbewertung_gueltig"] else None),
                    "direkte_native_aufrufe": bewertung["native_anteile"].get(
                        (f["datei"], f["zeile"]), []),
                    "aufrufer": f["aufrufer"],
                    "eingabeverweis": node,
                    "hinweis": "Instrumentierter Referenztest, keine uninstrumentierte Baseline.",
                })
        messfaelle = []
        for beleg in profillookup[key]["profilbelege"]:
            pfad = beleg["rohdatei"]
            if pfad not in messquellen:
                messquellen[pfad] = json.loads((ROOT / pfad).read_text(encoding="utf-8"))
            roh = messquellen[pfad]
            messfaelle.append({
                **beleg,
                "eingabegroesse": {
                    name: roh[name] for name in (
                        "modell", "szene", "punkte", "dreiecke", "schritte_pro_batch",
                        "dt_s", "viewport_px", "viewport_vorgabe_px", "messfall")
                    if name in roh},
                "eingabeverweis": pfad,
            })
        gueltig = [b for b in messfaelle if b["profilzeitbewertung_gueltig"]]
        bewertungsart = "Szenarioprofil"
        if not gueltig:
            gueltig = [b for b in testmessungen if b["profilzeitbewertung_gueltig"]]
            bewertungsart = "Referenztestprofil; Zeitkritikalitaet im Elternblock gesondert messen"
        if gueltig:
            prioritaet = max(gueltig, key=lambda b: b["profil_eigenzeitanteil"])
            bewertung = {
                "art": bewertungsart,
                "max_beobachteter_eigenzeitanteil": prioritaet["profil_eigenzeitanteil"],
                "rohdatei": prioritaet["rohdatei"], "szenario": prioritaet["szenario"],
                "eigenzeit_s": prioritaet["eigenzeit_s"],
                "gesamtzeit_s": prioritaet["gesamtzeit_s"],
                "aufrufe": prioritaet["aufrufe"],
                "hinweis": (
                    "Szenariobezogener Priorisierungshinweis, kein addierbarer Gesamtanteil. "
                    "Native Kanten je Messfall; Bibliotheksarbeit nicht nochmals portieren. "
                    "Kein Nachweis von Irrelevanz bei kleinem Anteil."),
            }
        else:
            bewertung = {
                "max_beobachteter_eigenzeitanteil": None,
                "hinweis": (
                    "Nur Referenztest-/Aufrufbeleg, keine gueltige separate Zeitmessung. "
                    "Mit dem nativen Elternblock messen; kein Irrelevanzabschluss."),
            }
        eintraege.append({
            **eintrag, "konkrete_referenztests": direkte_tests,
            "testmessungen": testmessungen,
            "messfaelle": messfaelle, "zeitbewertung": bewertung,
            "vergleichsvertrag": (
                "Struktureller Harness exakt; vorhandene fachliche Assertions und "
                "deren Toleranzen ausschliesslich im zugeordneten Originaltest. "
                "Keine globale Lockerung oder Ableitung aus Kandidatenergebnissen."),
            "migrationsentscheidung": (
                "Im zugeordneten U-Schritt als Kandidat/Teil des Elternblocks pruefen; "
                "keine produktive Umschaltung ohne direkte Paritaet und End-to-End-Gewinn."),
        })
    return {
        "fassung": 1, "python_referenzcommit": REFERENZ,
        "spec_sha256": aktuell["spec_sha256"], "eintraege": eintraege,
        "quellen": [
            {"datei": p.resolve().relative_to(ROOT).as_posix(), "sha256": texthash(p)}
            for p in (profildatei, testdatei)],
        "hinweis": (
            "Referenzpruefplan, kein nativer Abschluss. Kleine/generische, Modell- und "
            "Grenz-/Fehlereingaben sind durch konkrete Testquellen reproduzierbar. "
            "Modell-/Viewportgroessen aus Rohberichten, nicht aus Profilzeiten geschaetzt. "
            "Fehlende Einzelfunktionszeiten bleiben explizit offen bis zum Elternblock."),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--referenzmanifest", action="store_true")
    parser.add_argument("--profile", nargs="+", type=Path)
    parser.add_argument("--testprofile", nargs="+", type=Path)
    parser.add_argument("--pruefplan", nargs=2, type=Path,
                        metavar=("PROFILMATRIX", "TESTMATRIX"))
    args = parser.parse_args()
    if sum(bool(v) for v in (
            args.profile, args.testprofile, args.referenzmanifest, args.pruefplan)) > 1:
        parser.error("Inventar-, Profil-, Test-, Pruefplan- und Referenzmodi nicht kombinieren")
    daten = (messnachweise(args.profile) if args.profile
             else testnachweise(args.testprofile) if args.testprofile
             else pruefplan(*args.pruefplan) if args.pruefplan
             else referenzmanifest() if args.referenzmanifest else inventar())
    schreiben(args.output, daten)
    print("Geschrieben: %s" % args.output)


if __name__ == "__main__":
    main()
