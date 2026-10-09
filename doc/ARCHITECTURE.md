# Architektur-Entscheidung (Issue 0) – Vorschlag

**Status:** Entwurf zur Bestätigung durch den Maintainer (Issue 0 auf GitHub anlegen und dieses Dokument verlinken).

## Entscheidung 1: SPH-Kern
**Taichi** als Zielplattform (GPU-Pfad für Kriterium 7), **NumPy-Referenzimplementierung**
als CPU-Fallback und für Unit-Tests in der CI. Beide hinter dem Interface `core/fluid.py`
(`density_at`, `velocity_at`, Partikelzustand) – Spec §7.1.

## Entscheidung 2: Starrkörper
**Eigener impulsbasierter Solver** für v0.2 (semi-implizite Euler, Restitution +
Coulomb-Reibung). Begründung: kleine Körperzahlen (≤ 10–100), volle Determinismus-Kontrolle
(K9), keine schwere Fremdabhängigkeit, keine Achsenkonventions-Falle. PyBullet wird als
Spike in M1 geprüft (Risikotabelle im Umsetzungsplan); ein Wechsel bleibt möglich, da der
Solver hinter `core/solver.py` gekapselt ist.

## Entscheidung 3: Rendering
Entscheidung vertagt nach M4 (Issue 11): ModernGL/pyrender vs. Taichi-GUI.
Kriterium: transparente Oberfläche + 30 FPS bei 20k Partikeln.

## Bekannte Vereinfachungen der Referenzimplementierung (M0/M1)
1. Quader-`submerged_volume` achsenparallel (Rotationsanteil vernachlässigt, dokumentiert).
2. Quader-Kollision über minimale Halbabmessung (Kugel-Näherung); exakte SAT-Kollision ist Ausbau in M4/M5.
3. Trägheitstensor diagonal, Körperframe ≈ Weltframe für kleine Winkel.
Diese Vereinfachungen sind im Code markiert und beeinträchtigen keines der Kriterien K1–K10 in der getesteten Konfiguration.

## Nachweis (M0/M1-Abnahme)
- `python -m unittest discover` grün: Config-Defaults, Auflösungsregel, Teilvolumen 4 m³,
  Kugel-Kappe (halb/voll/über Wasser), A_ref, Trägheitstensor, Impulserhaltung (x),
  elastischer Stoß (Geschwindigkeitstausch), Bodenpraller mit Restitution,
  Akkumulator 4 Substeps/Frame @ 60 FPS & 240 Substeps/s, Freifall (diskret exakt).
