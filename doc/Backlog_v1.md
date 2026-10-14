# Optimierungs-Backlog v1

Dieses Backlog sammelt Optimierungskandidaten und Leistungsbefunde aus der
Entwicklung. Ein Eintrag ist kein Auftrag, die Physik, die Bedienung oder die
Abnahmekriterien ungeprüft zu ändern. Vor einer Umsetzung sind Nutzen,
Messbarkeit und Regressionen zu prüfen.

## Erfasste Kandidaten

### B-01 – Statische Berechnung von der GUI-Ereignisschleife entkoppeln

- **Priorität:** Hoch
- **Status:** Umsetzung und GUI-Reaktionsmessung erfolgt
- **Befund:** Der statische Solver und die Echtzeit-Physik laufen nun in
  Hintergrundaufgaben. Künstlich blockierende GUI-Regressionen prüfen, dass
  Qt-Ereignisse weiterlaufen und veraltete Solverergebnisse nicht angewendet
  werden. Unter echter Yacht-Voxelarbeit kehrte der Echtzeit-Takt in
  `0,095 ms` zurück; ein GUI-Ereignis wurde nach `16,4 ms` verarbeitet.
  Der globale Voxelpfad hatte zuvor im vollständigen Solverlauf `190,69 s`
  benötigt.
- **Restarbeit:** Fortschrittsanzeige oder expliziter Solverabbruch bleiben
  ungeprüft und benötigen eine gesonderte UX-Entscheidung. Ergebnisse werden
  bereits ausschließlich im GUI-Thread angewendet.
- **Abnahme:** Ereignis-Richtwert `100 ms` in der dokumentierten Lastprobe
  eingehalten. Künstlich blockierender Solver, sichere GUI-Thread-
  Poseaktualisierung und Verwerfen eines nach Moduswechsel veralteten
  Ergebnisses regressionsgeprüft.

### B-02 – Globalen Voxelpfad und Solver-Arbeitslast profilieren

- **Priorität:** Hoch
- **Status:** Offen
- **Befund:** Im Yacht-Solververgleich bei `0,025 m` wurden 152
  Kraftauswertungen benötigt und der globale Pfad brauchte 190,69 s. Eine
  frühere Vektorisierung der Säulenberechnung hatte den Yacht-Start von
  Minuten auf unter eine Sekunde verkürzt; der aktuelle vollständige
  Solverlauf zeigt weiterhin hohe Kosten pro Auswertung.
- **Später prüfen:** Zeiten getrennt für Wasserlinienschnitt, Mesh-
  Transformation, Säulen-/Voxelklassifikation und Solver messen. Erst den
  dominanten Anteil optimieren; numerische Referenz und bestehende
  Voxel-Union-Semantik erhalten.
- **Abnahme:** Wiederholbare Messung gleicher Körper, Posen und Auflösung;
  keine Verschlechterung der festgelegten Genauigkeits- und Kraft-/Moment-
  grenzen.

### B-03 – Körperfestes Raster schneller vorbereiten und korrekt in den
Solver integrieren

- **Priorität:** Hoch
- **Status:** Offen – Genauigkeitslücke beim Solvergleichgewicht
- **Befund:** Bei `0,025 m` speichert das Yacht-Raster rund 202.704
  Voxelzentren. Die Vorbereitung lag in wiederholten Läufen bei etwa
  14,6–17,8 s; neun Poseauswertungen dauerten etwa 0,018–0,020 s. Der Solver
  inklusive Vorbereitung war deutlich schneller als der globale Voxelpfad
  (etwa 18,06 s statt 190,69 s), fand aber eine um rund `3,78°` abweichende
  Rollage. Am exakten Union-Gleichgewicht lag der Schwerpunktfehler über der
  geltenden Grenze von `0,005 m`.
- **Später prüfen:** Rastererzeugung profilieren und beschleunigen;
  Solvergleichgewicht und Momentenrest gegen `exakt_union` validieren. Keine
  Standardumstellung, solange Gleichgewichtslage, Schwerpunkt und Momente
  nicht innerhalb der geltenden Abnahmekriterien übereinstimmen.
- **Abnahme:** Phase-4-CPU-Volumenabweichung höchstens `0,5 %` des
  ungeschnittenen Gesamtvolumens, Schwerpunktabweichung höchstens `0,005 m`
  in allen Abnahmeposen sowie ausreichende Übereinstimmung der vollständigen
  Solverlösung. Die absolute CPU/GPU-Schranke aus der Spezifikation ist davon
  getrennt und bleibt unverändert.

### B-04 – Wiederholbare Benchmark-Suite für vollständige Arbeitslasten

- **Priorität:** Hoch
- **Status:** Offen
- **Befund:** Bisherige CPU-Messungen waren einzelne manuelle Läufe. Die
  Vergleichbarkeit litt zudem an doppelter Rastervorbereitung in einem
  Solver-Benchmark; der dokumentierte Wert wurde anschließend durch einen
  Einmal-Aufbau-Lauf korrigiert.
- **Später prüfen:** Ein kleines Benchmarkwerkzeug ergänzen, das Hardware,
  Python-/Backendversion, Geometrie, Posefolge, Rasterweite, Vorbereitung,
  Kraftauswertungen, Solverzeit, Aufrufanzahl und Abweichungen zur
  `exakt_union`-Referenz getrennt ausgibt. Messungen mehrfach wiederholen und
  Streuung berichten.
- **Abnahme:** Gleiche Eingaben liefern reproduzierbare Ergebniswerte;
  Vorbereitung wird genau einmal gezählt und von wiederholter Auswertung
  getrennt ausgewiesen.

### B-05 – Exakte Union-Referenz bei Bedarf beschleunigen

- **Priorität:** Mittel
- **Status:** Beobachten
- **Befund:** `exakt_union` benötigte für neun Yachtposen ungefähr `0,22 s`
  und für den vollständigen Solverlauf ungefähr `0,83 s`. Der Pfad ist
  derzeit die union-konsistente CPU-Referenz, nicht der freigegebene
  Produktionsstandard.
- **Später prüfen:** Mesh-Konvertierung und Manifold3D-Union getrennt
  profilieren. Wiederverwendbare Daten nur dann cachen, wenn Pose- und
  Geometrieinvalidierung eindeutig bleibt.
- **Abnahme:** Referenzwerte stimmen mit analytischen und
  Booleschen Regressionstests überein; Fehler werden ausdrücklich gemeldet,
  nicht als Erfolg oder Nullvolumen kaschiert.

### B-06 – Darstellung und GPU-Nutzung separat messen

- **Priorität:** Mittel
- **Status:** Offen – keine Beschleunigung belegt
- **Befund:** Die bisher dokumentierten Leistungswerte betreffen CPU-
  Berechnung. Eine signifikant schnellere Darstellung wurde nicht gemessen.
  GPU-Präsenz bzw. der OpenCL-Prototyp belegen keine GPU-beschleunigte
  Physikberechnung; Rendering und Physikbackend sind getrennte Arbeitslasten.
- **Später prüfen:** Bildrate, Eingabereaktionszeit und Renderzeit unter
  repräsentativer Szene messen; GPU-Rechenaufgaben nur anhand der
  Arbeitslastmessung zuordnen. Mesh-LOD oder GPU-Berechnung sind Kandidaten,
  falls ein Profil einen Engpass bestätigt.
- **Abnahme:** Zielwerte und CPU/GPU-Genauigkeitsgrenzen der Spezifikation
  einhalten (unter anderem höchstens `100 ms` Eingabereaktionszeit und
  mindestens `30 FPS` in der definierten Referenzszene); kein GUI-Blockieren
  und keine sichtbare Änderung der physikalischen Geometrie durch reine
  Darstellungsoptimierung.

### B-07 – Raster- und Geometriecache über Laufzeitänderungen verwalten

- **Priorität:** Mittel
- **Status:** Offen
- **Befund:** Ein gebundenes körperfestes Raster wird einmal erstellt und
  während Poseauswertungen wiederverwendet. Die Laufzeit-GUI kann Körper nach
  Materialänderungen neu aufbauen. Eine Integration des körperfesten Pfads
  in diesen Lebenszyklus ist noch nicht freigegeben.
- **Später prüfen:** Cache-Lebenszyklus an Geometrie- und
  Auflösungsänderungen binden; sicherstellen, dass Masse-/Materialänderungen
  Solverdaten aktualisieren, ohne unnötig unveränderte Geometrie neu zu
  rasterisieren. Keine veralteten vorbereiteten Daten weiterverwenden.
- **Abnahme:** Tests für unveränderte Geometrie, Geometrieänderung,
  Auflösungsänderung und Materialänderung belegen korrekte Invalidierung
  sowie die erwartete Zahl von Rasteraufbauten.

### B-08 – Echtzeit-Rückstand unter Last messen

- **Priorität:** Mittel
- **Status:** Gemessen – Durchsatzoptimierung offen
- **Befund:** Die Echtzeitphysik wird jetzt außerhalb der GUI-Ereignisschleife
  in Batches mit höchstens vier festen SI-Schritten berechnet. Aufgelaufene
  Simulationszeit bleibt erhalten, damit überlastete Berechnung keine
  Physikschritte stillschweigend verwirft. Auf der Zielhardware dauerte ein
  Batch mit höchstens vier Yacht-Voxel-Schritten `0,624 s` für höchstens
  `0,016 s` Simulationszeit. Die GUI blieb bedienbar, aber der Rechenkern
  schafft unter dieser Last nicht Wandzeitgeschwindigkeit.
- **Später prüfen:** Globalen Voxelpfad profilieren/beschleunigen und
  Durchsatz mit repräsentativen Körpern und Auflösungen erneut messen. Eine
  Begrenzung oder Verwerfung aufgelaufener Simulationszeit wäre eine
  Verhaltensentscheidung und darf nicht stillschweigend eingeführt werden.
- **Abnahme:** Noch offen: Rechenleistung verbessert oder eine ausdrücklich
  festgelegte Regel für Überlast und Simulationszeit vereinbart. GUI-
  Reaktionsfähigkeit unter der gemessenen Last ist bereits nachgewiesen.

## Messkontext und Grenzen

- Yachtmodell: geometrisches Unionvolumen ungefähr `3,16786 m³`.
- CPU-Messungen vom 14.10.2026: Windows x64, Python 3.14.8,
  AMD Ryzen 5 8600G mit integrierter Radeon 760M.
- Phase-4-CPU-Konvergenz: relative Volumenabweichung höchstens `0,5 %` des
  ungeschnittenen Gesamtvolumens und Schwerpunktabweichung höchstens
  `0,005 m`. Das ersetzt nicht die absoluten, separat geltenden
  CPU/GPU-Schranken der Spezifikation.
- Solver- und Rasterzeiten sind Einzelmessungen; sie sind keine
  Laufzeitgarantie. Für eine Standardpfad- oder Backendentscheidung ist ein
  wiederholbarer vollständiger Anwendungslauf erforderlich.
- Es wurde bisher keine beschleunigte Darstellung nachgewiesen.
- Weiterführende Quellen: [Umsetzungsplan](./Umsetzungsplan_vF1.md),
  [Spezifikation](./Spezifikation_v1.1.md),
  [Voxelmodell](../segelphysik/core/voxelmodell.py),
  [Auftrieb](../segelphysik/core/auftrieb.py),
  [Union-Referenz](../segelphysik/core/volumen_union.py),
  [Solver](../segelphysik/core/statisch_robust.py) und
  [GUI-Hauptfenster](../segelphysik/gui/hauptfenster.py).

## Backlog pflegen

Neue Erkenntnisse als eigenen Eintrag mit Datum, Status, Messbedingungen,
Ergebnis, Abnahmekriterium und Verweis auf betroffene Tests/Dokumente
ergänzen. Überholte Befunde nicht stillschweigend entfernen, sondern mit
einem Folgeeintrag und begründeter Statusänderung nachvollziehbar ablösen.
