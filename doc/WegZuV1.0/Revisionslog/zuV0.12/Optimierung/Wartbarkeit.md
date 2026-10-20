# Robustheit & Wartbarkeit (Kriterium 6) und Messbarkeit (Kriterium 7)

Repo: BergStefanBerlin/SegelPhysik · Branch `main` · Stand: 20.10.2026
Geprüfte Dateien: `tests/` (Bestandsliste), `code/cpp/tests/vertrag_native.py`,
`code/cpp/tests/paritaet_batch.py`, `tests/test_benchmark_profil.py`,
`requirements-dev.txt`, `.github/` (Struktur).

---

## 6. Robustheit & Wartbarkeit

### 6.1 Was bereits bemerkenswert gut ist

| Punkt | Beleg |
|-------|-------|
| Fehlerbehandlung an der C++-Grenze **exzellent getestet** | `vertrag_native.py`: parametrisierte Abweisungstests für dtype (`float32`→TypeError), Shape, NaN/Inf, negative Indizes, ungültige SI-Skalaren; Ownership-Tests (Eingaben werden kopiert, Ausgaben leben unabhängig — mit `gc.collect()`-Verifikation); Thread-übergreifender Abbruch-Test |
| Explizite ABI-Vertragprüfung | `native_backend.py` prüft ABI_VERSION, alle Exporte, Methoden und den Rechenpfad-String beim Laden; `NativeBackendFehler` statt stiller Fallback (gewollt: kein automatischer Referenz-Fallback) |
| Parität als Regressionsanker | `paritaet_batch.py`: 1000 Schritte C++ vs. Python bei atol=1e-12, Kräfte 1e-9, Batch(1)-Sequenz vs. Batch(100) bit-exakt |
| Genauigkeitstest vorhanden | `tests/test_genauigkeit_v09.py` (physikalische Referenzwerte) |
| GUI ist getestet | u. a. `test_gui_laufzeit_edit.py` (34 KB), `test_gui_steuerung.py`, `test_grafik_bruecke_darstellung.py` |

### 6.2 Befunde W-Serie

| ID | Befund | Verbesserung | Aufwand | Effekt |
|----|--------|--------------|---------|--------|
| **W1** | **Keine CI-Workflows**: `.github/` enthält nur `agents/` und `instructions/`, kein `workflows/`. Die ~40 Python-Testdateien + 4 C++-Testdateien laufen nur lokal auf Abruf | GitHub-Actions-Workflow: Python-Tests + C++-Build/Tests auf Push; Matrix Linux/Windows (CMake-Build ist plattformabhängig) | gering (1 YAML-Datei) | **hoch** — sichert alle Refactorings aus Struktur.md/Optimierungen_2.md ab |
| **W2** | **Keine Coverage-Messung** (`requirements-dev.txt`: nur pytest). Die Abdeckung der Hot Paths ist unbekannt — besonders: Ist `wasser_schnitt.py` deckel/kontur-Pfad (A4/B2) und `_polygon_selbstschneidet` (C6) im Python-Zweig überhaupt von Tests berührt? Diese laufen nur, wenn `SEGELPHYSIK_RECHENPFAD=python` gesetzt ist | `pytest-cov` ergänzen; Coverage-Matrix pro Rechenpfad (`python`/`cpp`) fahren — genau hier liegt die typische Lücke bei Dual-Pfad-Architekturen | gering | mittel–hoch |
| **W3** | **God-Files** (S5): `hauptfenster.py` (101 KB), `grafik_bruecke.py` (76 KB), `modul.cpp` (70 KB). Komplexität konzentriert sich in wenigen Einheiten | Split nach Zielstruktur aus Struktur.md (szene/, gui/, backend/); als Metrik grob: Zeilen je Modul + Import-Abhängigkeiten | hoch | mittel (Wartbarkeit, indirekt Performance via C1/C2) |
| **W4** | **Fehlendes natives Backend im GUI**: `native_laden()` wirft `NativeBackendFehler`; ein stiller Python-Fallback ist bewusst ausgeschlossen (gut!). Offen: Wie verhält sich die GUI, wenn das Rad fehlt/ABI mismatch? Nicht aus Tests ersichtlich | Expliziter Startdialog/Fehlermeldung mit Handlungsanweisung (Rad bauen / Pfad wechseln); Test mit simuliertem Ladefehler | gering | mittel |
| **W5** | **Benchmark-Artefakte in `.pytest_cache`** (bewusst dokumentiert im Fixture) — ok, aber JSONL-Profile werden nach dem Test gelöscht; Verlaufsdaten gehen verloren | Optionale Umgebungsvariable zum Behalten der Profile (für Trendanalyse, siehe M1) | minimal | klein |

---

## 7. Messbarkeit (Benchmark-Profil)

### 7.1 Bestand: deutlich ausgereifter als üblich

`tests/test_benchmark_profil.py` + `werkzeuge/benchmark_profil.py` bieten:

- **Komponentenzerlegung der Schrittzeit** (Python-Pfad): `hydrostatik_geometrie`,
  `hydrodynamik`, `kraftaggregation_exklusiv`, `integrator_exklusiv`,
  `kraftaufruf_rest`, `worker_rest`; C++-Pfad: `nativer_batch` + `worker_rest`.
  Summenprüfung `sum(Komponenten) == worker_s` mit abs=1e-12 — messlückenfrei.
- **Pose-Probe statt Ergebnis-Cache**: `hydro_messen` cacht nicht das Ergebnis, sondern
  die Pose (bitgenau, 1e-16 wird als neu behandelt) — misst Cache-Trefferquote, ohne
  das Messergebnis zu verfälschen.
- **Eingabe-Hash** über alle Slots/Parameter (Änderung der fluidgeschwindigkeit ändert Hash).
- **Parität der Messhüllen**: Profil-Lauf muss exakt dasselbe liefern wie der unprofilierte
  Lauf (atol=1e-12) — die Instrumentierung selbst ist verifiziert.
- Statistik mit median/p95, JSONL-Ausgabe, `cpu_hotspots`.

### 7.2 Befunde M-Serie

| ID | Befund | Verbesserung | Aufwand | Effekt |
|----|--------|--------------|---------|--------|
| **M1** | **Kein Regressionstor**: Das Profil läuft als Test, aber ohne CI (W1) und ohne gespeicherte Verlaufsdaten (Profile werden gelöscht, W5). Verschlechterungen durch Commits bleiben unsichtbar | Mit W1 kombinieren: CI-Job führt Benchmark-Profil aus, speichert JSONL als Artefakt, vergleicht median/p95 gegen Vorcommit (Schwellwert z. B. +10 %) | gering (nach W1) | **hoch** |
| **M2** | **Keine Allokationsmessung**: Zeitkomponenten ja, Speicher/GC-Druck nein (siehe Kriterium 1 aus der Kriterienliste) | `tracemalloc`-Zähler in `WorkerProfil.messen` ergänzen (Allokationen/Schritt je Komponente) | gering | mittel — erklärt *warum*, nicht nur *wie viel* |
| **M3** | **GUI-Frame-Zeit fehlt im Profil**: gemessen wird nur der Physik-Worker. C1 (GUI rechnet je Frame den Wasser-Schnitt) ist im Profil unsichtbar | Frame-Messung in `GrafikBruecke.aktualisieren()` (Schnittzeit, Meshbau, Render) ins Profil aufnehmen; `test_qt_renderanforderung_koalesziert_bis_zum_swap` zeigt, dass Render-Koaleszierung bereits getestet wird — Messung wäre konsistent ergänzbar | mittel | hoch (macht C1/C2 messbar) |
| **M4** | **Kein Mikro-Benchmark des nativen Schnitts**: Für die E1-Entscheidung (BVH lohnt ab welcher Meshgröße?) fehlt eine Messung `_EbenenSchnitt.auswerten` über n = 1k/5k/50k Dreiecke | Kleines `werkzeuge/benchmark_ebenenschnitt.py` (Batch-API mit steigender Dreieckszahl, µs/Dreieck ausgeben) | gering | mittel — Entscheidungsgrundlage für E1/P1 |
| **M5** | Batchgröße im Echtzeitbetrieb nicht gemessen: `batchkomponenten` existieren, aber der Einfluss der Batchanzahl (Marshalling-Amortisierung) ist nicht Teil des Profils | Profil-Lauf mit variabler Batchanzahl (1/4/16) in den Bericht aufnehmen | gering | klein–mittel |

---

## 8. Sortierte Empfehlungen (Aufwand vs. Effekt)

1. **W1** CI-Workflow (gering/hoch) — Fundament für alles Weitere
2. **M1** Benchmark als Regressionstor in CI (gering nach W1/hoch)
3. **W2** Coverage pro Rechenpfad (gering/mittel–hoch)
4. **M3** GUI-Frame-Zeit messen (mittel/hoch — macht C1 handhabbar)
5. **W4** GUI-Verhalten bei fehlendem nativen Backend (gering/mittel)
6. **M4** Ebenenschnitt-Mikrobenchmark (gering/mittel)
7. **M2** Allokationsmessung (gering/mittel)
8. **M5** Batchanzahl-Variation (gering/klein–mittel)
9. **W3** God-File-Split (hoch/mittel — langfristig, mit Struktur.md synchron)

**Kernbotschaft:** Die Test-*qualität* ist überdurchschnittlich (Grenztests, Parität,
Genauigkeit, instrumentierte Messhüllen) — es fehlt fast ausschließlich die *Automatisierung
und Kontinuität* (CI, Coverage, Verlaufsdaten). Das ist der günstigste Hebel des gesamten
Optimierungsprogramms, weil er jeden einzelnen Befund aus Optimierungen_2.md absichert.

---

## 9. Quellen

- Direkt gelesen (Branch `main`, 20.10.2026): `code/cpp/tests/vertrag_native.py`,
  `code/cpp/tests/paritaet_batch.py`, `tests/test_benchmark_profil.py`,
  `requirements-dev.txt`, `.github/`-Verzeichnisstruktur, `tests/`-Dateiliste.
- Verfahren: Coverage-getriebene Dual-Pfad-Prüfung und Benchmark-Regressionstors sind
  Standardpraxis (pytest-cov-Dokumentation; GitHub-Actions-Dokumentation).
