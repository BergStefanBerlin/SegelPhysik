# SegelPhysik – Architektur-Analyse und Zielstruktur

Stand: 20.10.2026 · Basis: Repo `BergStefanBerlin/SegelPhysik` (Branch `main`)
Diese Datei bewertet den **Aufbau** des Codes (nicht die Mikro-Optimierung; dafür siehe `Optimierungen_2.md`).

---

## 1. Gesamturteil

Der Code ist strukturell besser als sein Ruf:

- **Klare Schichtung**: Physik-Kern (`core/`), Render (`render/`), GUI (`gui/`), natives Backend (`code/cpp/`) sind getrennt.
- **Durchdachte Dual-Pfad-Strategie**: Python-Referenzpfad vs. C++-Produktionspfad (`rechenpfad.py`, Default `cpp`), mit A/B-Validierungs-Infrastruktur (`python_referenz()`).
- **Solider Testumfang**: ~40 Testdateien unter `tests/`, darunter Benchmark-Profil (`test_benchmark_profil.py`) und Genauigkeitstests (`test_genauigkeit_v09.py`).
- **Sauberes Packaging**: `pyproject.toml`, requirements-Trennung (Basis / dev / gpu), CI-Ordner `.github/`.

**Nicht optimal** ist der Aufbau an fünf Stellen (S1–S5). Wichtig: Die meisten Performance-Befunde
aus der Hot-Spot-Analyse sind **Symptome** genau dieser strukturellen Punkte.

---

## 2. Strukturelle Schwächen (S-Serie)

| ID | Schwäche | Wo | Symptome daraus |
|----|----------|----|-----------------|
| S1 | **Validierung im Hot Path statt an der Grenze** – `_vektor`-Prüfungen, `np.linalg.eigvalsh`, Datenklassen-`__post_init__` laufen pro Physikschritt | `dynamik_6dof.py`, `kraftmodell.py` | D2, D3 |
| S2 | **Kein einheitliches Caching-Konzept** – ein `_version`-Zähler existiert, wird aber nicht als Vertrag genutzt; manche Caches fingerprint-basiert (`massen.py`), andere fehlen ganz | `koerper.py`, `grafik_bruecke.py`, `kraftmodell.py` | C1, C3/C4, D1 |
| S3 | **Parallele Implementierungen desselben Konzepts** – 4 Auftriebs-/Voxel-Pfade, 2 OBJ-Parser, Python/C++-Duplikate ohne gemeinsame Schnittstelle | `auftrieb.py`, `voxelmodell.py`, `mesh.py` | A1/A2/A3, C5 |
| S4 | **Geometrie-Vorbereitung verstreut** – Union, Voxelraster, Benetzung bereiten jeweils eigenes vor; kein gemeinsamer „Geometrie-Kontext" | `volumen_union.py`, `voxelmodell.py`, `hydrodynamik.py` | E1/E5 ohne Doppelarbeit nicht umsetzbar |
| S5 | **God-Files im GUI** – `hauptfenster.py` (~101 KB), `grafik_bruecke.py` (~76 KB); GUI greift direkt in Physik-Interna (`ws.schneide_am_wasser`) | `gui/hauptfenster.py`, `grafik_bruecke.py` | C1, C2, C7 |

---

## 3. Zielstruktur

```
segelphysik/
  geometrie/   # Mesh, OBJ-Import (1 Parser), Union, BVH, Voxel-Raster – "einmal vorbereiten"
  physik/      # Hydrostatik, Hydrodynamik, Dynamik 6DOF, Solver (reine Array-Pipeline)
  kern/        # Kraftmodell: NumPy-intern, Objekte nur an der API-Grenze
  backend/     # Registry: python_referenz | cpp | voxel_opencl (eine Schnittstelle, pluggable)
  szene/       # Grafik-Brücke mit Dirty-Tracking + Szenen-Cache (GUI sieht nur dies)
  gui/         # dünne Widgets/Dialoge, keine Physik-Aufrufe
  io/          # Lader/Konfig: einmal geladen, per Dependency Injection weitergereicht
```

Kernidee: **Ein** vorbereitetes `GeometrieKontext`-Objekt (Union + BVH + Voxelraster) wird an alle
Backends übergeben. Invalidierung läuft über einen **Pose-Fingerprint als zentralen Vertrag**
statt über verstreute Cache-Logik in einzelnen Modulen.

---

## 4. Priorisierung: Aufwand vs. Effekt

### Quadrant 1 – wenig Aufwand, viel Effekt (zuerst)

| Nr. | Maßnahme | Befund | Aufwand |
|-----|----------|--------|---------|
| 1 | Dirty-Check in `aktualisieren()` der Grafik-Brücke | C1 | ~20 Zeilen |
| 2 | Snapshot an `_version` cachen | C3/C4 | klein |
| 3 | Validierungen aus `schritt()` ins Setup ziehen | D2 | risikofrei |
| 4 | Redundanten `_residuum`-Aufruf streichen; Parser-Reihenfolge tauschen | B3, C5 | trivial |

### Quadrant 2 – mittlerer Aufwand, großer Effekt

| Nr. | Maßnahme | Befund | Nutzen |
|-----|----------|--------|--------|
| 5 | `GeometrieKontext` einführen | S4 | ermöglicht E1/E5, löst nebenbei A1/A2 |
| 6 | Delta-Invalidierung im HydroCache | D1/E3 | bis 40 % der Schrittzeit in ruhigen Phasen |
| 7 | Array-Pipeline im Kraftmodell | D3/S1 | 15–30 % Schrittzeit |

### Quadrant 3 – viel Aufwand, großer Effekt

| Nr. | Maßnahme | Befund | Nutzen |
|-----|----------|--------|--------|
| 8 | Backend-Registry vereinheitlichen | S3 | macht OpenCL-Pfad pflegbar |
| 9 | GUI-Split (hauptfenster/grafik_bruecke aufteilen) | S5 | Wartbarkeit, indirekt Performance |

### Quadrant 4 – wenig Aufwand, wenig Effekt (nachrangig)

C7, B1, B4/D4, D5.

---

## 5. Zusammenhang zu den Performance-Befunden

Die Befunde aus `Optimierungen_2.md` ordnen sich so ein:

- **C1, C3/C4, D1** sind Symptome von S2 (fehlender Cache-Vertrag).
- **D2, D3** sind Symptome von S1 (Validierung im Hot Path).
- **A1/A2/A3, C5** sind Symptome von S3 (parallele Implementierungen).
- **E1/E5** scheitern heute an S4 (verstreute Geometrie-Vorbereitung).
- **C1, C2, C7** werden durch S5 (GUI-Größe) verschärft.

Deshalb: Die strukturellen Maßnahmen 5–7 (Quadrant 2) bringen mehr als die Summe ihrer
Einzelpunkte, weil sie jeweils eine ganze Befundklasse erledigen.

---

## 6. Empfohlene Reihenfolge

1. Quadrant 1 komplett (1–4) – sofortiger messbarer Gewinn, geringes Risiko.
2. Maßnahme 5 (`GeometrieKontext`) – architektonisches Fundament für die Algorithmus-Ebene.
3. Maßnahmen 6–7 – Hot-Path-Gewinne auf dem neuen Fundament.
4. Maßnahmen 8–9 – nach Bedarf, wenn Pflege/OpenCL/GUI-Erweiterungen anstehen.
