# Teststruktur – Findings

Projekt: BergStefanBerlin/SegelPhysik · Branch `main` · Stand 20.10.2026
Umfang der Sichtung: vollständige Dateiliste (`tests/` 93 Dateien, `code/cpp/tests/` 4 Dateien),
15 Dateien im Volltext gelesen. Zeilen-/Funktionsanker vor Übernahme kurz gegenprüfen.

---

## 1. Bestandsaufnahme

| Bereich | Anzahl | Anmerkung |
|---|---|---|
| `tests/*.py` | 93 | flache Struktur im Repo-Root, kein Unterordner |
| `code/cpp/tests/*.py` | 4 | Parität + Native-Vertrag, mit eigenem `conftest.py` |
| `tests/conftest.py` | **fehlt** | gemeinsame Fixtures fehlen → Duplikation |
| pytest-Konfig in `pyproject.toml` | **fehlt** | keine Marker, keine `testpaths`, keine ini_options |
| CI-Workflows | **keine** | `.github/` enthält nur Agent-/Instruktionsdateien |

Inhaltliche Qualität der Suite ist hoch (analytische Referenzwerte, strenge Parität,
Vertragsprüfung). Die Befunde betreffen die **Organisation**, nicht die Substanz.

---

## 2. Findings (T-Serie)

| ID | Titel | Beleg / Ort | Bewertung |
|----|-------|-------------|-----------|
| T1 | Meilensteins-Namen statt Themen-Namen | `test_schritt4.py` („Testblock J – Schritt 4"), `test_rev_e.py` („Tests rev E"), `test_genauigkeit_v09.py`, `test_migration_v010.py`, `test_gui_a1.py` („A1"), `test_farben_komposition.py` („Block I, Spec P4") | Dateinamen für Neulinge unfindbar; Inhalt hat mit dem Namen nichts mehr zu tun |
| T2 | Gemischte Themen je Datei | `test_schritt4.py`: J1–J10 (Glanz über konfig_lader/koerper/fabriken/grafik_bruecke) **plus** W1–W4 (Schalentensor in `core/massen`, Röhrenradius in `grafik_bruecke`) – vier Module in einer Datei. `test_rev_e.py`: statisch_robust + stoerung + koerper_formen + auftrieb gemischt | Split nach Thema |
| T3 | Lokale Duplikation von Testhilfen; kein zentrales conftest | `test_schritt4.py` definiert eigene `quader_mesh()`, obwohl `koerper_formen.build_box` existiert; `QApplication.instance() or QApplication([])` und `profildatei`-Fixture in mehreren GUI-/Benchmark-Dateien wiederholt | Hoher Nutzen, geringer Aufwand: `tests/conftest.py` anlegen |
| T4 | Drei konkurrierende Architektur-Metatests | `test_gui_a1.py` (AST-Scan: keine GUI-Imports in core/render – sauber, als Muster behalten); `test_keine_physik_imports.py` (Regex-Scan nach Relikt-Namen „forces/solver/bodies/sph/fluid", Docstring „M0-Abnahme V3-Module" = alter Refactor-Meilenstein); `test_project_layout.py` + `test_manifest_baum.py` (Pfadprüfungen) | Regex-Fossil durch AST-Ansatz ersetzen |
| T5 | Zombie-Test | `test_migration_referenzpfade.test_entfernter_legacy_body_typ_ist_keine_ausfuehrbare_referenz`: testet permanent, dass `segelphysik.core.bodies` einen `ModuleNotFoundError` wirft – dokumentiert toten Code als Test | Streichen; Erkenntnis ins Changelog/Archiv |
| T6 | Abdeckungsgetriebene Sammeldatei | `test_migration_referenzpfade.py` („Direkte Referenzfälle für zuvor nicht aufgerufene Inventarfunktionen"): wasser_schnitt + massen + bewegung + vista + grafik_bruecke + hauptfenster + echtzeit_prozess in einer Datei; entstanden für Inventarabdeckung, nicht zur Verhaltensprüfung | Nach Themen auflösen, gute Einzeltests behalten |
| T7 | Redundanz innerhalb von Dateien | `glanz_kw` doppelt geprüft in `test_schritt4.py` (J9 Endpunkte+Linearität vs. W2 Steigung – W2 ist Teilmenge von J9); `_farbgruppen` in `test_schritt4.py` (J10), `test_benchmark_profil.py`, indirekt `test_farben_komposition.py` | Deduplizieren |
| T8 | Zwei Dynamik-Module mit je Testdatei; Integrationstests in Unit-Datei | `test_dynamik.py` prüft das Legacy-2DOF-Modul `core/dynamik.py` (3,6 KB) neben dem Produktionspfad `dynamik_6dof.py`; die letzten beiden Tests in `test_dynamik.py` sind schwere Integrationstests (800–200 000 Integrationsschritte, Yacht-Union-Aufbau) mitten in der Unit-Datei | Legacy-Klärung; Integrationstests raus + Marker `slow` |
| T9 | Keine Marker / keine Laufzeitsteuerung | keine `slow`/`integration`/`gui`-Marker erkennbar; GUI-Tests (Qt) und Worker-Benchmarks laufen in derselben Sammlung wie schnelle Unit-Tests; weder `pytest-timeout` noch `pytest-xdist` in den dev-Requirements (nur `pytest==9.1.1`) | Marker registrieren, `-m`-Profile, `testpaths` |
| T10 | Stil-Inkonsistenzen | eigener `__main__`-Runner mit `sys.exit` in `test_rev_e.py` (neben pytest); `sys.path.insert`-Hack in `test_schritt4.py`; `os.path`-Strings vs. `pathlib`; gemischte Docstring-Sprachen | Einheitliche Konvention festlegen |

---

## 3. Positiv – nicht verändern

- **16 `test_native_*`-Dateien** spiegeln die `.hpp`-Header 1:1 (Adapterverträge Python-seitig)
  und ergänzen die C++-Paritätstests (`code/cpp/tests/paritaet_*.py`). Das ist bewusste
  Doppelbuchung zweier Ebenen (Adapter vs. Kern), **kein** Duplikat.
- `test_hydrodynamik_metadaten.py`: vorbildlich – deterministische Erzeugung, Read-only-Vertrag,
  atomares Schreiben, Sidecar-Integrität.
- Strenge Parität (`rel=0, abs=1e-12`, Batch-Sequenzen bit-exakt) – von keinem Refactoring antasten.
- `test_gui_a1.py`: sauberer AST-Scan als Muster für Architekturregeln.

---

## 4. Priorisierte Verbesserungen

1. **`tests/conftest.py` anlegen** (T3): `qapp`-, `profildatei`-Fixtures, Standard-Meshes über
   `koerper_formen.build_box` statt lokaler Mesh-Bauer. Entfernt sofort Duplikation in ~6 Dateien.
2. **Marker + pytest-Konfig** (T9): `slow`/`gui`/`native`-Marker registrieren, schnelle Suite als
   Default, volle Suite in CI; `pytest-timeout` ergänzen.
3. **Umbenennen/Splitten nach Thema** (T1/T2/T6): z. B.
   - `test_schritt4.py` → `test_glanz.py` + `test_massen_schale.py`
   - `test_rev_e.py` → `test_statisch_loeser.py`
   - `test_migration_referenzpfade.py` auflösen
   Bestehende Blockkennungen (J1, W2, SpecNNNN) als Kommentare erhalten – passt zur
   Kennungs-Philosophie aus `AGENTS.md`.
4. **Fossilien entfernen** (T4/T5): `test_keine_physik_imports.py` durch AST-Variante ersetzen,
   Zombie-Test streichen.
5. **`core/dynamik.py`-Frage klären** (T8): Falls Legacy, Modul + Test deprecaten.

---

## 5. Quellen

- Vollständiger Repo-Baum: GitHub-API `git/trees/main?recursive=1` (20.10.2026)
- Volltext gelesen: `test_dynamik.py`, `test_schritt4.py`, `test_rev_e.py`,
  `test_genauigkeit_v09.py`, `test_migration_referenzpfade.py`, `test_keine_physik_imports.py`,
  `test_project_layout.py`, `test_native_backend.py`, `test_farben_komposition.py`,
  `test_gui_a1.py`, `test_vista_ui.py`, `test_hydrodynamik_metadaten.py`,
  `AGENTS.md`, `.github/instructions/schnittstellenregister.instructions.md`
- Dateiliste `tests/` (93 Dateien) und `code/cpp/tests/` (4 Dateien) aus dem Baum
