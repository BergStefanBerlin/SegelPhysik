# SegelPhysik

3D-Physiksimulationsumgebung (Wasser/Luft, starre Körper, SPH) nach `doc/SPEC.md`.

## Status (Umsetzungsplan M0–M5)

| Meilenstein | Status |
|---|---|
| M0 Architektur & Gerüst | ✅ |
| M1 Starrkörper-Welt | ✅ |
| M2 SPH-Wasserkern (NumPy-Referenz) | ✅ |
| M3 Fluid↔Körper-Kopplung | ✅ |
| M4 Rendering & UI | ✅ |
| M5 Abnahme (Serialisierung, Akzeptanz-Suite, Benchmark) | ✅ |

Details: `doc/UMSETZUNGSPLAN.md`, Abnahme: `doc/ACCEPTANCE.md`.

## Schnellstart

```bash
pip install numpy matplotlib

# Tests (QUICK, CI-tauglich):
python -m unittest discover -s segelphysik/tests -t .

# Tests (FULL, inkl. SPH-Kriterien, mehrere Minuten):
set SEGELPHYSIK_FULL=1 && python -m unittest discover -s segelphysik/tests -t .  # Windows

# K7-Benchmark (manuell):
python benchmarks/benchmark_k7.py --frames 300
```

## Interaktive Demo

```python
import matplotlib.pyplot as plt
from segelphysik.core.app import SimulationApp
from segelphysik.core.render import HeightFieldSurface, MatplotlibRenderer

app = SimulationApp()
app.spawn_sphere(radius=0.5, density=300.0, position=(0, 0, 1.5))
app.set_wind(speed=5.0, azimuth_deg=30.0)
surf = HeightFieldSurface(app.cfg.basin, nx=40, ny=40)
renderer = MatplotlibRenderer()
plt.ion()
for _ in range(300):
    app.step_frame()
    surf.update(app.sph.pos[:app.sph.n_real])
    renderer.render(app.world, surf)
    plt.pause(0.01)
    plt.close(renderer.fig)
```

## Struktur

```
segelphysik/           Python-Paket (Kern ohne Rendering-Abhängigkeiten)
  core/                config, bodies, solver, sph, forces, fluid, scene, render, app
  tests/               Unit- + Akzeptanztests (QUICK/FULL)
benchmarks/            K7-Benchmark (manuell)
doc/                   SPEC, UMSETZUNGSPLAN, ARCHITECTURE, ACCEPTANCE
```
