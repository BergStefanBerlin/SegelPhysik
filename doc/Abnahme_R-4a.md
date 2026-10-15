# Abnahme R-3 / R-4a – CPU-Live-Lauf (15.10.2026)

## Messbedingungen

- Hardware: Ryzen 5 8600G, Radeon 760M, Windows, Qt-Plattform `windows`
  (sichtbares Fenster, nicht offscreen), Python 3.14.8.
- Szene `yacht1`, Pfad `exakt_union` (exakte Hydrostatik in jedem Schritt),
  Prozess-Worker aktiv, alle vier Pflicht-Layer an.
- 30 s Warm-up, 600 s Messung (`werkzeuge/benchmark_gui_live.py`, Standard).
- Präsentationszeitpunkt: VTK-`EndEvent` des Renderfensters plus
  `WaitForCompletion`. Eingabelatenz: einmal pro Sekunde simulierte
  Mausdrehung (599 Eingaben) bis zum ersten Frame mit geänderter Kamera.
- Grenze: Die FPS enthalten die zusätzlichen Frames durch die simulierten
  Eingaben; der Frameabstand p95 ist davon nicht verfälscht nach oben.

## Ergebnis gegen die Gates

| Gate | Soll | Ist | Status |
|---|---|---|---|
| Präsentierte FPS | ≥ 30 | 69,8 (Abstand p95 31,6 ms, max 90 ms) | erfüllt |
| Eingabereaktion p95 | ≤ 100 ms | 4,1 ms (Median 3,0 ms), 599/599 | erfüllt |
| Stationärer Durchsatz | ≥ 1,0x | 0,9999x (taktbegrenzt auf Echtzeit) | erfüllt |
| Rückstand p95 | ≤ 100 ms | 48,6 ms (max 210 ms) | erfüllt |
| Rückstandszunahme (300 s) | ≤ 50 ms | +0,09 ms/s ≈ 28 ms | erfüllt |
| Überlastpause | keine | keine | erfüllt |
| Nachholrate | ≥ 1,25x | nicht gemessen | offen |

Weitere Werte: Physik-Batch median 5,1 ms, p95 7,6 ms (20879 Batches),
Posen-Update im GUI-Thread median 14,2 ms, p95 17,1 ms, keine Fehler.

## Bewertung

R-3 ist erfüllt: Der Benchmark liefert gültige FPS- und Latenzwerte. R-4a ist
bis auf die Nachholrate bestanden. Die Nachholrate wird ein eigener Test
(Pause, Fortsetzen, Zeit bis Rückstand < 100 ms).
