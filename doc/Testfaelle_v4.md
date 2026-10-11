# TESTCASES V4 – Vorgaben für tests/test_koerper.py (und Lader-Tests)

Status: VERBINDLICH · Grundlage: doc/Spezifikation_v4.md (11.10.2026) · Datum: 11.10.2026

Konventionen für ALLE Tests:
- SI-Einheiten (R6); Toleranzen absolut, wo nicht anders angegeben.
- Determinismus: Jeder Test muss bei Wiederholung bitidentische Ergebnisse
  liefern (keine Zufallswerte ohne festen Seed).
- Referenzwerte werden analytisch oder mit unabhängiger Methode (z. B.
  Monte-Carlo-Integration mit festem Seed) bestimmt – nie mit derselben
  Funktion, die getestet wird.

---

## Block A – Konfig-Lader (Schritt 0, Spec J)

| ID | Titel | Eingabe/Aktion | Erwartung |
|---|---|---|---|
| TC-A1 | Vorlage lädt | kopierte konfiguration.json laden | Alle Abschnitte materialien/wasser/boot/darstellung vorhanden; Werte = Vorlagenwerte |
| TC-A2 | Fehlende Arbeitsdatei | konfiguration.json umbenennen, laden | Klare Fehlermeldung mit Hinweis auf doc/configuration_template.json; KEIN stiller Fallback |
| TC-A3 | Doppelschlüssel | JSON mit doppeltem Key (z. B. „Blei" zweimal) | Validierungsfehler (object_pairs_hook-Pflicht) |
| TC-A4 | Fehlender Schlüssel | materialien ohne „Blei" | Validierungsfehler beim Zugriff/Load |
| TC-A5 | Gruppe mit Masse | kielsystem erhält zusätzlich „dichte" | Validierungsfehler (P2.5) |
| TC-A6 | Blatt ohne Massengröße | rumpf ohne material/dichte/… | Validierungsfehler (Genau-eins-Regel) |
| TC-A7 | Blatt mit zwei Massengrößen | kiel mit material UND dichte | Validierungsfehler |
| TC-A8 | Leere Gruppe | rigg mit „teile": [] | Validierungsfehler |
| TC-A9 | Direkte Zahl zulässig | Bulb mit dichte=11340 statt material | lädt ohne Fehler, gleiche Masse wie Variante material=Blei |

## Block B – Masseneigenschaften einzelner Körper (Schritt 1, P1/P3)

| ID | Titel | Eingabe | Erwartung (Referenz) |
|---|---|---|---|
| TC-B1 | Quader-Schwerpunkt (AK-P1a) | homogener Quader 2×2×2, dichte=1000 | m = 8000 kg exakt; r_S = Mitte (< 1e-12); V = 8 m³ |
| TC-B2 | Kegel-Schwerpunkt (AK-P1b) | Kegel H=2, R=1, homogen | r_S bei H/4 über Basis (< 1e-9); m = ρ·π·R²·H/3 |
| TC-B3 | Tensor Quader | Quader a×b×c homogen | Diagonaltensor mit analytischen Werten m(b²+c²)/12 usw. (< 1e-9 relativ) |
| TC-B4 | Tensor Kugel-Konsistenz | aus feinem Kegel-/Quader-Mesh grob gegen Kugelnäherung | Abweichung plausibel klein; Symmetrie Ixx=Iyy=Izz am Würfel exakt |
| TC-B5 | Flächenmasse (AK-P3d) | Segelfläche 10 m², flaechenmasse=0,5 | m = 5 kg exakt; Volumen = 0 |
| TC-B6 | Volumenloser Körper + Dichte | Segel-Mesh mit dichte gesetzt | Validierungsfehler (P3) |
| TC-B7 | Genau-eins-Regel (AK-P3a) | beide/keine Massengrößen | Fehler in beiden Fällen |
| TC-B8 | Material-Auflösung (AK-P3c) | Bulb-Geometrie, material=Blei | m = 11340 · V_Bulb (V aus Divergenzsatz) |

## Block C – Komposition/Rekursion (Schritt 1, P2)

| ID | Titel | Eingabe | Erwartung |
|---|---|---|---|
| TC-C1 | Zweiteilkörper (AK-P1c) | zwei Quader unterschiedlicher Masse, bekannte Positionen | r_S gegen unabhängige Integration < 0,1 %; m = Σm_i |
| TC-C2 | Parallel-Achsen-Satz | gleicher Zweiteilkörper | I_ges = Σ(I_i + m_i(‖d‖²1 − ddᵀ)) analytisch (< 1e-9) |
| TC-C3 | Tensor-Rotation | Teil mit rel_Pose = 90°-Drehung | Ohne Rotation falsches Ergebnis; mit Rotation korrekt (Gegenprobe: gedrehtes Mesh direkt integrieren) |
| TC-C4 | Gruppe = Summe | kielsystem (kiel+bulb) | Gruppen-m/r_S/I_S identisch zu flacher Summe derselben Teile (exakt) |
| TC-C5 | Flach ≡ gruppiert (P2-WICHTIG) | Boot einmal flach, einmal mit kielsystem/rigg-Gruppen | Gesamtes m, r_S, I_S identisch (exakt gleich) |
| TC-C6 | Tiefe 3 | Gruppe in Gruppe | dieselben Summationsregeln liefern analytisch korrektes Ergebnis |
| TC-C7 | Schwerpunktframe-Verschiebung | beliebiger zusammengesetzter Körper | Nach Erzeugung: Σ(m_i · r_i) = 0 im eigenen Frame (< 1e-9); Konstruktionskoordinaten nicht mehr abfragbar |

## Block D – Boot (Schritt 1, AK-P1d + J)

| ID | Titel | Eingabe | Erwartung |
|---|---|---|---|
| TC-D1 | Boot aus Konfiguration | konfiguration.json + 8 OBJ-Dateien | 8 Teile geladen; Materialien je Spec J (rumpf/ruder GfK, kiel Stahl, bulb Blei, mast/boom Aluminium, Segel flaechenmasse 0,5) |
| TC-D2 | Boot-r_S plausibel (AK-P1d) | berechnetes Boot | r_S unter Rumpfmitte; gegen numerische Referenzintegration < 0,5 % |
| TC-D3 | Boot-Masse | Summe aller Teilmassen | plausibel (Rumpf leicht, Bulb dominiert); exakt = Σ ρ_i·V_i + Σ f_j·A_j |
| TC-D4 | Segel volumenlos | grosssegel/fock | V = 0; Masse nur über flaechenmasse |

## Block E – Farbe (Schritt 1, P4)

| ID | Titel | Eingabe | Erwartung |
|---|---|---|---|
| TC-E1 | Default-Aufhellung (AK-P4a) | farbe=#c9c9c9, keine Unterwasserfarbe | Unterwasserfarbe = HSL-Aufhellung ΔL=+0,25, S unverändert; Referenzwerte fest im Test |
| TC-E2 | Beide gesetzt (AK-P4b) | beide Farben angegeben | beide exakt übernommen, keine Transformation |
| TC-E3 | Default-Farbe (AK-P4c) | keine Farbangabe | farbe = #c9c9c9 (aus konfiguration.json, nicht hart codiert) |
| TC-E4 | ΔL aus Konfiguration | delta_helligkeit_unterwasser=0.4 in Kopie | Aufhellung folgt der Datei (keine Code-Konstante) |

## Block F – Regression & Integration (Schritt 1)

| ID | Titel | Erwartung |
|---|---|---|
| TC-F1 | Alte Suite | bestehende 22 Tests bleiben grün (unverändert) |
| TC-F2 | Demo-Lauf deterministisch | Kegel/Quader/Pyramide/Boot erzeugt → φ(t)-Folgen bitidentisch zu vorher (K7″-Prinzip) |
| TC-F3 | Wasserlinien-Schnitt unverändert | schneide_am_wasser liefert für Boot identische Konturen wie vor Umstellung |
| TC-F4 | Keine stillen Duplikate | Quelltextsuche: Material-/Wasser-Dichten kommen NUR aus konfiguration.json (Review-Check, automatisiert als Test: Lader-Ergebnis == Vorlagewerte) |

---

## Abdeckungs-Matrix (Test ↔ Spec)

| Spec-Forderung | Test(s) |
|---|---|
| AK-P1a | TC-B1 |
| AK-P1b | TC-B2 |
| AK-P1c | TC-C1 |
| AK-P1d | TC-D2 |
| AK-P3a | TC-B7 (+TC-A5..A8 für JSON-Seite) |
| AK-P3b | TC-B1 |
| AK-P3c | TC-B8 |
| AK-P3d | TC-B5 |
| AK-P4a | TC-E1 |
| AK-P4b | TC-E2 |
| AK-P4c | TC-E3 |
| P2 (Rekursion, Flach≡gruppiert) | TC-C1..C7 |
| J (Loader-Regeln) | TC-A1..A9 |
| R6 (SI) | Konvention alle Tests; TC-E4 (ΔL dimensionslos) |
| P5b-Vorbereitung | TC-B4 (Eigenvektor-Grundlage: Tensor korrekt) |

Hinweis: P5-Overlays (Schritt 3) und Grafik (Schritt 2) bekommen ihre
Testvorgaben mit den jeweiligen Schritt-Specs – hier nur die numerische
Grundlage (Tensor korrekt ⇒ Eigenvektoren sinnvoll prüfbar).
