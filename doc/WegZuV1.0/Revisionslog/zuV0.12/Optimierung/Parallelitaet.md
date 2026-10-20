# Parallelität, SIMD & GPU-Lastverteilung — Befunde P-Serie

Repo: BergStefanBerlin/SegelPhysik · Branch `main` · Stand: 20.10.2026
Kontext: Produktionspfad ist der native C++-Kern (`SEGELPHYSIK_RECHENPFAD` defaultet auf `cpp`,
siehe `core/rechenpfad.py`). Diese Analyse prüft, ob der native Kern und die Prozess-/Thread-
Struktur die vorhandene Hardware ausnutzen.

---

## 1. Was bereits richtig gemacht ist

| Punkt | Beleg |
|-------|-------|
| Prozess-Isolation GUI ↔ Physik | `core/echtzeit_prozess.py`: Physik läuft im eigenen Worker-Prozess, Batch-API `schritte_berechnen` gibt nur pickelbare Daten zurück → kein GIL-Wettbewerb mit der GUI |
| GIL-Freigabe im nativen Kern | `code/cpp/src/modul.cpp`: jeder rechenintensiven Bindung folgt `py::gil_scoped_release` → GUI bleibt bedienbar, während der Worker rechnet |
| Release-Build aktiv | `pyproject.toml`: `cmake.build-type = "Release"` → `-O3 -DNDEBUG` ist gesetzt (die nackte `CMakeLists.txt` allein suggeriert fälschlich einen ungeoptimierten Build) |

**Korrektur gegenüber früheren Aussagen:** Ein OpenCL-/GPU-Backend existiert im Repo **nicht**.
`rechenpfad.py` kennt nur `"cpp"` und `"python"`; im Paketbaum gibt es keine OpenCL-Datei.
Die GPU wird ausschließlich vom Render-Pfad (PyVista/VTK/OpenGL) genutzt.

---

## 2. Befunde P-Serie

| ID | Datei | Stelle | Befund | Verbesserung | Potenzial | Aufwand |
|----|-------|--------|--------|--------------|-----------|---------|
| P1 | `code/cpp/src/ebenenschnitt.hpp` | `EbenenSchnitt::auswerten` (ab ca. Z. 70) | **Kein SIMD.** Distanzberechnung `skalarprodukt(punkt, normale) - offset` läuft als Skalarschleife über `std::array<double,3>`-Punkte (Array-of-Structures); Dreiecksklassifikation über Dreier-`bool`-Schleife | SoA-Layout (flaches `double[3n]`) + AVX2: 4 Punkte pro Instruction klassifizieren; Dreiecksfälle über Sign-Maske statt Branch-Kette | 2–4× auf den Ebenenschnitt, mehr bei großen Meshes | mittel |
| P2 | `code/cpp/src/dynamik.hpp` | `PhysikKontext::schritt`, Aufruf `hydrodynamik_beitraege(hydrodynamik.teile, …)` | **Batch-Lauf seriell auf einem Kern.** Die Integrationsschritte sind sequentiell abhängig (nicht parallelisierbar), aber `hydrodynamik_beitraege` iteriert über unabhängige Körperteile | Per-thread Akkumulatoren + OpenMP über Teile/Dreiecke. **Achtung:** ändert Summationsreihenfolge → kollidiert mit Reproduzierbarkeitsziel von `/fp:precise`; feste Zuordnung Teil→Thread nötig | bis n_Kerne× auf Hydrodynamik-Anteil | mittel–hoch |
| P3 | `code/cpp/src/ebenenschnitt.hpp` | `VolumenMoment::dreieck` (ca. Z. 33): `determinanten.push_back(det)` | **Heap-Reallokation im Hot Loop.** Der Vektor wächst je Auswertung von 0 auf n_Dreiecke (log n Reallocations + Memcpys) | Puffer als Member einmal `reserve(n)` / wiederverwenden | 10–30 % der Schnittzeit | gering |
| P4 | `code/cpp/CMakeLists.txt` | Z. 7–11 | **Keine Architektur-Flags.** Nur MSVC `/fp:precise`; kein `/arch:AVX2`, kein LTO | Baseline `/arch:AVX2` (MSVC) bzw. `-mavx2` (GCC/Clang) + `-flto`. `-march=native` wäre für verteilte Wheels falsch (Portabilität). Hinweis: `/fp:precise` drosselt Auto-Vektorisierung (keine Reassoziation) — deshalb ist P1 als *explizite* SIMD-Implementierung der richtige Weg, nicht das Warten auf den Compiler | 5–15 % nativ gesamt | gering |
| P5 | `code/cpp/src/voxel.hpp` | `VoxelKontext::auswerten`, Schleife über `saeulen_` | Säulen-Loop seriell mit Binärsuche je Säule; Spalten sind unabhängig | OpenMP- oder SIMD-Parallelisierung über Säulen; lohnt erst bei sehr feinen Rastern | 2–4× auf Voxel-Auswertung (große Raster) | mittel |
| P6 | `core/echtzeit_prozess.py` + GUI (`grafik_bruecke.py`) | Worker-Erzeugung / `aktualisieren()` | **Keine Kernaffinität/Priorität.** Worker- und GUI-Prozess werden vom Scheduler frei verteilt; C1 (GUI rechnet je Frame den Wasser-Schnitt) nimmt dem Worker Kerne weg | Erst C1 fixen (Dirty-Check), dann Prioritäten tunen: Worker-Prozess leicht hochstufen bzw. GUI auf Below-Normal; unter Linux `os.sched_setaffinity` | klein, aber gratis | gering |
| P7 | — | — | **GPU-Lastverteilung: kein Konflikt vorhanden.** Physik ist rein CPU (C++/NumPy); GPU nur im Render-Pfad | Kein Handlungsbedarf. Falls später ein GPU-Voxel-Pfad (E4-Variante) kommt: Splat-Kernel (A7) und Physik auf getrennte Queues legen | — | — |

---

## 3. Sortierung nach Potenzial

1. **P1** — SIMD/SoA im Ebenenschnitt: größter algorithmischer Hebel im nativen Kern
2. **P2** — OpenMP über Körperteile: skaliert mit Kernzahl, braucht Determinismus-Konzept
3. **P4** — Arch-Flags + LTO: fast gratis (zwei Zeilen CMake)
4. **P3** — Puffer-Reserve: klein, risikofrei, sofort umsetzbar
5. **P5** — Voxel-Parallelisierung: nur für feine Raster relevant
6. **P6** — Affinität/Priorität: nach C1, sonst symptombasiert
7. **P7** — kein Handlungsbedarf

---

## 4. Empfohlene Reihenfolge & Zusammenspiel

- **Start:** P3 + P4 (zwei Zeilen CMake, ein `reserve()`) — risikofreier Sofortgewinn.
- **Kerninvestition:** P1. Sie verstärkt auch den Effekt von E1 (BVH aus `Optimierungen_2.md`),
  weil die verbleibenden Knoten-Auswertungen dann vektorisiert laufen.
- **Zuletzt:** P2 wegen der Reproduzierbarkeits-Frage (`/fp:precise` vs. parallele Summation);
  erst umsetzen, wenn die Paritätstests (`code/cpp/tests/paritaet_*.py`) ein festes
  Zuordnungsschema abdecken.

---

## 5. Quellen

- Codebefunde: direkt gelesen aus den genannten Repo-Dateien (Branch `main`, Stand 20.10.2026):
  `CMakeLists.txt`, `pyproject.toml`, `ebenenschnitt.hpp`, `voxel.hpp`, `dynamik.hpp`,
  `modul.cpp`, `echtzeit_prozess.py`, `rechenpfad.py`.
- Verfahren (SoA/SIMD-Layout, OpenMP-Reduktion, LTO, `/fp`-Semantik): Standardtechnik der
  Compiler-/HPC-Dokumentation — Intel Intrinsics Guide, OpenMP-Spezifikation,
  MSVC-Dokumentation zu `/fp:precise` und `/arch`.
