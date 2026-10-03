# Segelphysik-Viewer (Godot 4)

Visualisierung der Segelphysik-Simulation mit echter 3D-Grafik.

## Architektur

    Python (viewer_bridge.py)  --UDP/JSON 60 Hz-->  Godot-Viewer
    Physik bleibt 1:1 der getestete Code aus dynamics/hydrodynamics.

Der Bridge exportiert beim Start die Rumpfform als OBJ
(yacht_hull.obj, yacht_keel.obj) in diesen Ordner.

## Starten

1. **Godot 4.2+** installieren (godotengine.org). Ordner `viewer/`
   in Godot importieren (Import -> project.godot) und F5 druecken.
2. Bridge starten (aus dem Segelphysik-Hauptordner):

       python viewer_bridge.py --fm 1200 --fw 70

   Erst wenn beide laufen, erscheint die Yacht und bewegt sich.

## Darstellung

- **Kraftpfeile** starten IMMER am Wirkpunkt, zeigen in Kraftrichtung,
  Laenge proportional zur Kraft (1,5 m pro 1000 N).
- **Gegenkraefte**: gleiche Farbe wie ihre Kraft, aber GESTRICHELT:
  - Blau: Auftrieb (durchgezogen) <-> Gewicht (gestrichelt)
  - Gruen: Segelkraft (durchgezogen) <-> Kiel, Ruder, Widerstand (gestrichelt)
- **Cyan-Pfeile** im Wasser: lokale Stroemung, Laenge ~ Geschwindigkeit.
- **Eintauchen**: Rumpf wird unter der Wasserlinie dunkler gerendert,
  Cyan-Band an der Wasserlinie; Wasser animiert + transparent.

## Steuerung

| Eingabe | Wirkung |
|---|---|
| Linke Maustaste ziehen | Kamera drehen |
| Mausrad | Zoom |
| Pfeil links/rechts | Ruderwinkel |
| Bild auf / ab | Segelkraft FM |
| R | Reset |

## Fehlerbehebung

- Port 9999 belegt: alte Instanz beenden.
- Yacht unsichtbar: Bridge gestartet? Firewall: localhost erlauben.
- OBJ fehlen: Bridge einmal starten (erzeugt sie), dann F5.
