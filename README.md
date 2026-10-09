# SegelPhysik

3D-Physiksimulationsumgebung (Wasser/Luft, starre Körper) – Basis für die
Segelboot-Simulation. Grundlage: `doc/SPEC.md` (Spec 1.0),
Umsetzung: `doc/UMSETZUNGSPLAN.md` (Plan v1.2).

## Status
- [x] M0 Architektur & Gerüst (Issue 0–1) – siehe `doc/ARCHITECTURE.md`
- [x] M1 Starrkörper-Welt (Issue 2–4)
- [x] M2 SPH-Wasserkern (NumPy-Referenz, `core/sph.py`; Taichi-Port offen)
- [ ] M3 Kopplung Fluid↔Körper
- [ ] M4 Rendering & UI
- [ ] M5 Abnahme (K1–K10)

## Tests (aus dem Repo-Root)
```bash
python -m unittest discover -s segelphysik/tests -t .
```
Erwartet: 18 Tests, alle grün.
