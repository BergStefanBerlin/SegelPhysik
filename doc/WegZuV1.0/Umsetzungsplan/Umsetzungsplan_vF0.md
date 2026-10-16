# SegelPhysik – Umsetzungsplan vF0

Arbeitsreihenfolge zur Spezifikation [vF1](../Spezifikationen/Spezifikation_vF1.md).
Jede Phase erhält gezielte Tests; Änderungen werden unabhängig von diesem
Plan nur auf ausdrückliche Anweisung committed oder gepusht.

## 1. Verlässliche Testbasis

- Veraltete Konfigurationstests auf das aktuelle Schema bringen.
- Vollständige Pfade der Laufzeitdateien und Vorlagen prüfen; Validierung
  fehlender/ungültiger Dateien und doppelter Schlüssel ergänzen, falls nötig.
- Den abweichenden Brücken-/Kräfte-Regressionstest anhand der aktuellen
  Actor- und Overlay-Ausgabe korrigieren oder den Fehler beheben.
- Voxel-Warnungen untersuchen und verbleibende numerische Randfälle festhalten.
- Abnahmepunkt: Konfigurationsfehler sind verständlich und lösen keine stillen
  Ersatzwerte aus; vollständige Testsuite mit nachvollziehbarem Ergebnis.

## 2. Körper- und Materialbearbeitung

- GUI-Eingaben validieren und Materialliste aus der aktiven Konfiguration
  laden.
- Änderungen sitzungsgebunden auf Konfigurationsmodell, Körperfabrik,
  Laufzeitkörper und Renderer übertragen; JSON unverändert lassen.
- GUI-Eingaben aus Anzeigeeinheiten an der Eingabegrenze nach SI umrechnen;
  berechnete SI-Werte an der Ausgabegrenze für die Anzeige umrechnen.
- Numerische Referenzen für Masse, Schwerpunkt, Trägheit, Rekursion,
  Materialzuordnung und Farben als Regressionstests sichern.
- Abnahmepunkt: Material- und Zahlenänderungen sind in Baum und 3D-Darstellung
  synchron sichtbar, Einheiten werden korrekt umgerechnet und ein Neustart
  lädt wieder die JSON-Ausgangswerte.
- Solver-Neuberechnung bleibt ausgesetzt.

## 3. Statische Simulation in der GUI

- Modusauswahl mit dem statischen Solver verbinden.
- Pose und Kennwerte in 3D-Ansicht und Solver-Status aktualisieren.
- Keine stabile Lösung und Solverfehler ausdrücklich anzeigen.
- Gleichgewicht, Stabilität und numerische Kennwerte mit Referenzfällen prüfen.
- Abnahmepunkt: GUI-Ergebnis stimmt mit dem getesteten Solverergebnis überein.

## 4. Dynamische Physik

- Kraft-/Momentenfunktion als gemeinsame Grundlage bestätigen bzw. extrahieren.
- Konfigurierte Parameter und festen Zeitschritt in die Integration einbinden.
- Zuerst Tauchbewegung und Krängung integrieren; Stabilität, Dämpfung und
  Determinismus prüfen.
- Echtzeitmodus mit automatischem Start sowie `=` (Pause) und `>` (Fortsetzen)
  an die Integration anschließen; keine Zurück-Taste anbieten.
- Zeitschrittverhalten und gemeinsame Kraft-/Momentenfunktion mit
  Regressionstests absichern.
- Abnahmepunkt: dynamische Bewegung ist berechnet und nicht kinematisch
  vorgegeben; Solver und Integration verwenden dasselbe Kraftmodell.

## 5. Darstellung und GUI-Integration

- Layer, Körperfarben, Wasserlinienschnitt und Laufzeitpose durchgängig an die
  aktuelle GUI anbinden.
- Kamera-Presets, Beleuchtung, Hintergrund, Wasseroptik und separat
  schaltbares SSAO in der eingebetteten Darstellung umsetzen bzw. vervollständigen
  und prüfen; obere Visualisierungstexte bleiben entfernt.
- Modusfarben, exklusive Auswahl und Echtzeit-Pause/Fortsetzen regressionsprüfen.
- GUI-Tests decken Baumstart, Pfeil-Klappverhalten, Checkbox-Funktion,
  Einheitenumrechnung und sitzungsgebundene Änderungen ohne JSON-Schreibzugriff
  ab.
- Abnahmepunkt: sichtbare Bedienelemente steuern die dargestellte Laufzeit und
  melden ihren Zustand korrekt; alle spezifizierten Layer und
  Darstellungsfunktionen sind geprüft.

## 6. Abschluss je Release

- Gezielte Tests nach jeder Phase und vollständige Testsuite vor Freigabe.
- Referenzen, bekannte Warnungen und bewusste Abweichungen knapp dokumentieren.
- Versionszähler gemäß vF1 fortschreiben. Commit und Push erfolgen nur nach
  ausdrücklicher Nutzeranweisung.

### Abnahme des aktuellen Arbeitsstands

- Phasen 1 bis 5 sind umgesetzt; die Solver-Neuberechnung nach
  sitzungsgebundenen Eigenschaftsänderungen bleibt wie spezifiziert
  zurückgestellt.
- Vollständige Testsuite: **232 bestanden**, mit Warnungen als Fehler.
- GUI- und 3D-Szenenaufbau sowie Kamera-, Layer-, Wasser-, Licht- und
  SSAO-Steuerung wurden in einer Offscreen-Qt-Sitzung durchlaufen.
- `git diff --check` ist erfolgreich. Commit und Push wurden nicht ausgeführt;
  der Versionszähler bleibt bis dahin unverändert.
