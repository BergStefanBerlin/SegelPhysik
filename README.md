# Segelphysik

Dynamische Simulation eines schwimmenden Segelboot-Rumpfes mit vollen
6 Freiheitsgraden (Position + Lage, Quaternionen, Newton-Euler).

## Start

    python main.py                    (aus diesem Ordner)
    python Segelphysik/main.py        (aus dem uebergeordneten Ordner)

Benoetigt: `numpy`, `matplotlib`.

## Struktur

| Datei | Inhalt |
|---|---|
| `main.py` | Einstiegspunkt |
| `config.py` | Physik-/Anzeige-Konstanten, Presets |
| `slider_defs.py` | GUI-Slider-Definitionen (Datenliste) |
| `math_utils.py` | Quaternionen, Rotationsmatrizen, Euler-Winkel |
| `geometry.py` | Rumpfform + Fin-Kiel/Bulb/Ruder (`QuaderVoxel`) |
| `hydrostatics.py` | Auftrieb, CB, hydrostatische Momente |
| `dynamics.py` | `Simulation`: Newton-Euler, Integration, Gleichgewicht |
| `hydrodynamics.py` | Kiel-/Ruder-Hydrodynamik (**Schritt 2, Stub**) |
| `water.py` | Seezeichen-Muster (Bewegungsreferenz) |
| `rendering/arrows.py` | Pfeil-Polygone, Wasserlinien-Clipping |
| `rendering/scene.py` | 3D-Szene, Boot-Ansicht-Transformationen |
| `app.py` | GUI: Slider, Buttons, Maus-Events, Timer |

Die Physik-Module kennen die GUI nicht -> headless testbar.

## Stand / naechste Schritte

- Verhalten identisch zu `quader_app_4.py` (Refactoring ohne Aenderung).
- Bugfix gegenueber `quader_app_4.py`: "Gleichg." uebergibt jetzt die
  Slider-Werte `lk/tk/rk` statt stillschweigender Defaults.
- `hydrodynamics.py` ist vorbereitet und wird von `Simulation.schritt()`
  bereits aufgerufen (liefert aktuell Nullkraefte). Dort entsteht als
  naechstes die Kiel-/Ruder-Tragfluegel-Hydrodynamik (Vortrieb/Abtrieb).
