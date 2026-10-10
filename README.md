# SegelPhysik v0.4

Echtzeit-3D-Physiksimulation (Wasser/Luft, SPH + Starrkoerper) als Fundament
fuer eine Segelboot-Simulation.

## Status v0.4 (Release-Schnitt, 10.10.2026)

### Physik
- SPH-Wasserkern (WCSPH, kubischer Spline, Kontinuitaetsform) auf **Taichi/Vulkan**
  mit NumPy-Referenz-Fallback (automatisch, gekennzeichnet im Startbanner)
- Starrkoerper: Kugel/Quader, semi-implizite Euler, impulsbasierte Kollisionen
- Kopplung: Archimedes-Auftrieb + quadratischer Drag (Kontinuum),
  einseitige Ausschlusskollision Partikel<->Koerper (Kugel + Box) – keine Doppelzaehlung
- Determinismus (K9): CPU-stabiler Sort, GPU-Laeufe bit-identisch

### Performance (Ryzen 5 8600G, Radeon 760M iGPU, Vulkan)
- Messkette: 6.0 FPS (NumPy) -> 10.6 -> 22.3 -> 35.3 FPS @ 12.288 Partikel
- Visualisierungsprofil: c=30 m/s, cfl_acoustic=0.3 (Default-Config)
- Messprofil fuer Akzeptanztests: c=60, cfl=0.2 (siehe doc/ACCEPTANCE.md)

### Visualisierung (Spec §6)
- Wasseroberflaeche als Marching-Cubes-Isoflaeche eines 3D-Partikel-Dichtefelds
  (Boundary-Pad an Waenden/Kanten/Ecken, Auto-Kalibrierung der Iso-Schwelle)
- Koerper zweifarbig (unter/ueber Wasserlinie) mit Wasserlinien-Kontur
- Kraft- und Geschwindigkeitspfeile, Status-Panel (Position, |v|,
  Eintauchtiefe, verdraengtes Volumen, resultierende Kraft)
- HUD: Realtime-Faktor, FPS, Simulationszeit; Tiefenfaerbung der Oberflaeche

### Interaktion (Spec K8)
- Klick-Spawning (Kugel/Box, Taste n umschalten), g/Wind zur Laufzeit
- Endloslauf als Default (`python gui.py --backend taichi`)

## Start

```bash
python gui.py --backend taichi   # endlos bis Fenster zu / q
python demo.py                   # headless
python -m unittest discover -s segelphysik/tests -t .
```

## Dokumentation
- `doc/SPEC.md` – Spezifikation (v0.2.5; Anpassung v1.1 in Arbeit)
- `doc/UMSETZUNGSPLAN.md` – Plan v1.2 (M0–M5, 18 Issues)
- `doc/ACCEPTANCE.md` – Abnahmeprotokoll K1–K10 + Profile-Hinweis
- `doc/V03A.md`, `doc/ARCHITECTURE.md`
