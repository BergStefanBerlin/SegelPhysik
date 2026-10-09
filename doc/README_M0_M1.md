# SegelPhysik – M0/M1-Lieferstand

## Inhalt
```
segelphysik/
├── config.json          # Defaults (Spec 1.0 §7.1) – einzige Quelle der Wahrheit
├── core/
│   ├── config.py        # Config + validate_resolution (Auflösungsregel ≥ 8·Δx)
│   ├── bodies.py        # Body/Sphere/Box, Quaternionen, Teilvolumen, A_ref, Trägheit
│   ├── forces.py        # ForceModule-Interface (Gravity aktiv; Fluid-Module ab M3)
│   ├── fluid.py         # FluidSolver-Interface + NullFluid (M2 folgt)
│   └── solver.py        # World (Impuls-Solver, Kollisionen) + TimeLoop (Akkumulator)
└── tests/               # 18 Unit-Tests (alle grün)
ARCHITECTURE.md          # Issue-0-Entwurf (Taichi+NumPy, eigener Solver)
```

## Tests ausführen
```bash
python -m unittest discover -s segelphysik/tests -t .
```

## Minimalbeispiel
```python
from segelphysik.core.config import Config
from segelphysik.core.bodies import Sphere
from segelphysik.core.solver import World, TimeLoop

world = World(Config.load("segelphysik/config.json"))
world.add(Sphere(1.0, 500.0, position=(0, 0, 2.0)))   # schwimmt später (M3)
loop = TimeLoop(world)
loop.advance(1/60)   # ein Frame @ 60 FPS -> 4 Substeps
```

## Status
- [x] M0: Architektur (Issue 0), Config-System (Issue 1)
- [x] M1: Bodies (Issue 2), Solver/Kollisionen (Issue 3), Zeitschleife (Issue 4)
- [ ] M2: SPH-Wasserkern (Issues 5–6)
