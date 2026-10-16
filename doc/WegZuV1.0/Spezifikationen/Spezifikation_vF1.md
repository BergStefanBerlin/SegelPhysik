# SegelPhysik – Spezifikation vF1

**Zweck:** Verbindliche, funktional gegliederte Grundlage für die weitere
Entwicklung. Diese Fassung ersetzt die überholte Spezifikation v4.
Window Look & Feel wurde nach v4 beschlossen und ist in dieser Fassung
berücksichtigt.

## 1. Körper und Konfiguration

- Der Schwerpunktframe ist das sichtbare und rechnende Bezugssystem eines
  Körpers. Geometrie, Masse, Schwerpunkt und Trägheitstensor werden aus Meshes
  berechnet.
- Körperverbände und masselose Gruppen sind beliebig tief rekursiv.
  Gruppenwerte ergeben sich ausschließlich aus ihren Unterobjekten.
- Der Rechenkern verwendet SI-Einheiten. Eingabe- und Ausgabewerte werden an
  den GUI-Grenzen zwischen Anzeigeeinheiten und SI umgerechnet.
- Laufzeitkonfiguration besteht aus `konfigurationen/koerper.json`,
  `konfigurationen/materialien.json` und `konfigurationen/physik.json`;
  Vorlagen liegen unter `doc/`. Eingaben werden einschließlich doppelter
  Schlüssel validiert. Fehlende oder ungültige Dateien führen zu
  verständlichen Fehlern, nicht zu stillen Ersatzwerten.
- Körperblätter verwenden Material oder direkte Dichte. `wanddicke_m`
  beschreibt Schalen. Materialdaten und zugehörige Farben stammen aus der
  Materialkonfiguration.
- Änderungen an Materialeigenschaften über die GUI gelten nur für die aktuelle
  Sitzung und verändern keine JSON-Datei. Material- und Zahlenwerte werden
  unmittelbar auf Laufzeitkörper und Darstellung angewendet.
- Solver-Neuberechnung nach Änderungen an Körper- oder Materialeigenschaften
  ist zurückgestellt.

## 2. Simulation – statisch

- Der Solver bestimmt eine stabile Gleichgewichtslage aus Gewicht, Auftrieb
  und Momenten. Instabile Lösungen werden verworfen.
- Die statische Simulation verwendet dieselbe Kraft- und Momentenfunktion wie
  die dynamische Simulation.
- Das Ergebnis zeigt die berechnete Pose sowie relevante Kennwerte im
  Solver-Status. Fehler oder fehlende stabile Lösungen werden ausdrücklich
  angezeigt.
- Die Funktion muss über den Modus „Statisch“ in der aktuellen GUI erreichbar
  sein.

## 3. Simulation – dynamisch

- Die dynamische Simulation integriert die Körperbewegung über feste
  Zeitschritte. Zeitschritt, Schwerkraft und Dämpfung werden aus
  `physik.json` geladen.
- Dynamik und statischer Solver verwenden dasselbe physikalische Modell.
- Erster Umfang: vertikale Bewegung und Krängung. Weitere Freiheitsgrade,
  insbesondere Gieren, bleiben zurückgestellt.
- „Echtzeit“ ist ein eigener, exklusiver Modus. Nur in diesem Modus sind die
  Zeitsteuerungen `=` (Pause) und `>` (Fortsetzen) aktiviert und blau
  hervorgehoben. Eine Zurück-Taste ist nicht vorgesehen.
- Kinematisch vorgegebene Bewegung gilt nicht als dynamische Physiksimulation.

## 4. Darstellung und Visualisierung

- Weltkoordinaten sind rechtshändig: z nach oben, x in Bugrichtung, y nach
  Backbord. Die Wasserlinie liegt bei z = 0.
- Ober- und Unterwasserfarben folgen den Körper-/Materialdaten. Eine fehlende
  Unterwasserfarbe wird deterministisch aus der Überwasserfarbe abgeleitet.
- Schwerpunkt, Hauptachsen, Kräfte und Momente sind globale, unabhängig
  schaltbare Layer. Darstellungs-Overlays werden nicht im Körper gespeichert.
- Wasserlinienschnitt, Pose, Farben und Overlays müssen konsistent dargestellt
  werden. Dekorative Effekte dürfen keine physikalischen Vorgänge vortäuschen.
- Kamera-Presets, Beleuchtung, Hintergrund und Wasseroptik sind
  Darstellungsfunktionen. SSAO darf separat schaltbar sein.
- Im oberen Bereich des Visualisierungsfeldes erscheinen keine Hinweis- oder
  Tastentexte.

## 5. GUI und Bedienung

- „Statisch“ und „Echtzeit“ sind gegenseitig exklusiv; immer genau einer der
  beiden Modi ist aktiv. Der aktive Modus ist blau markiert.
- Die Echtzeit-Simulation startet beim Aktivieren des Modus. `=` pausiert,
  `>` setzt fort; außerhalb von Echtzeit sind beide Tasten deaktiviert.
- Der Körperbaum startet mit „Welt“ geöffnet und den Hauptkörpern geschlossen.
  Auf- und Zuklappen erfolgt ausschließlich über die Baum-Pfeile. Checkboxen
  steuern ausschließlich Auswahl und Aktivität.
- Rechtsklick auf eine editierbare Materialeigenschaft öffnet einen passenden
  Editor: vorhandene Materialien als Auswahl, Zahlenwerte als numerische
  Eingabe.
- Die GUI schreibt keine Konfigurations-JSON. Angezeigte Werte, Laufzeitkörper
  und Darstellung bleiben synchron.
- Status, Bedienbarkeit und Fehlermeldungen müssen dem tatsächlich aktiven
  Zustand entsprechen.

## 6. Prüfung und Abnahme

- Körper und Konfiguration werden anhand numerischer Referenzen für Masse,
  Schwerpunkt, Trägheit, Rekursion, Materialien und Farben geprüft.
- Konfigurationstests prüfen außerdem fehlende und ungültige Dateien, doppelte
  Schlüssel sowie verständliche Fehlerbehandlung.
- Solver und Dynamik werden auf Gleichgewicht, Stabilität, Determinismus,
  Zeitschrittverhalten und die gemeinsame Kraftfunktion geprüft.
- GUI und Darstellung werden auf Moduswechsel, aktive Zeitsteuerung, Baum- und
  Checkbox-Verhalten, Layer, Farben, Einheitenumrechnung und
  sitzungsgebundene Änderungen geprüft. Kamera, Beleuchtung, Hintergrund,
  Wasseroptik und SSAO werden entsprechend ihrer vorgesehenen Bedienung
  geprüft.
- Fehlerhafte Eingaben und fehlende Konfigurationen müssen klar scheitern.
- Ein Release gilt erst als geprüft, wenn die vollständige Testsuite besteht
  oder verbleibende Ausnahmen ausdrücklich vereinbart und dokumentiert sind.

## 7. Zurückgestellter Umfang

- Grafischer Konfigurator und dauerhaftes Speichern von GUI-Änderungen.
- Solver-Neuberechnung nach Material- oder Körperänderungen.
- Weitere dynamische Freiheitsgrade über Tauchbewegung und Krängung hinaus.

## 8. Versionsregel

- Jeder Commit erhöht die dritte Versionsstelle um eins.
- Jeder Push erhöht die zweite Stelle um eins und setzt die dritte Stelle
  zurück, z. B. Commits `0.1.1`, `0.1.2`, danach Push `0.2`.
