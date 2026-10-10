# Release v0.4 (10.10.2026)

Release-Schnitt des aktuellen Stands vor der Spec-Anpassung (v1.1).

## Enthalten (gegenueber v0.2.0-Tag)
- Taichi/Vulkan-GPU-Backend + automatischer NumPy-Fallback
- PyVista-Renderer: Dichtefeld-Isoflaeche (Marching Cubes), Zweiton-Koerper,
  Wasserlinien-Ring, Kraft-/Geschwindigkeitspfeile, Status-Panel, RTF/FPS-HUD,
  Tiefenfaerbung
- Klick-Spawning (K8-Teil), Endloslauf als Default
- Performance: Substep-Buendelung, Sort 1x/step, Visualisierungsprofil
  (35.3 FPS @ 12.288 Partikel auf iGPU)
- Einseitige Ausschlusskollision Partikel<->Koerper (Kugel + Box)

## Bekannte offene Punkte (-> Plan v1.3 / Spec v1.1)
- K7-Kombiszenario (~21.700 Partikel + 10 Koerper) nicht gefahren
- K3 GPU-Hydrostatik -43% (float32) – dokumentiert; Blocker fuer Zwei-Wege-Kopplung
- Kontrollpanel (Beckenmasse/dt/Substeps zur Laufzeit) fehlt
- Spawn-Optionen Dichte/mu/e fehlen
- Repo-Hygiene: __pycache__ im Git, .gitignore fehlt
