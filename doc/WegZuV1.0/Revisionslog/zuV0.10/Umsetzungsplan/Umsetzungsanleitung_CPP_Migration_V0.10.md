# Umsetzungsanleitung V0.10: C++-Migration

**Stand:** 19.10.2026  
**Status:** Plan zur Prüfung; keine Umsetzung durch dieses Dokument nachgewiesen  
**Branch:** `v0.10`  
**Fachliche Quelle:** [Spezifikation C++-Migration V0.10](../Spezifikationen/Spezifikation_CPP_Migration_V0.10.md)

## 1. Verbindlicher Arbeitsvertrag

Alle 34 aktiven Anforderungen der Spezifikation sind unten zugeordnet.
Die vollständigen Einzelfunktionslisten aus A-V0.10-00006 bis
A-V0.10-00030 sind Bestandteil jedes betreffenden Arbeitsschritts.
Eine Tabellenzeile mit mehreren Funktionsnamen ist vor Bearbeitung in
einzeln nachvollziehbare Inventareinträge zu zerlegen. Gemeinsam
übertragene Hilfsfunktionen bleiben einzeln einem nativen Elternblock
und dessen Nachweisen zugeordnet. Kein Teil darf durch eine pauschale
Meldung wie „Hydrostatik erledigt“ verschwinden.

Es gelten unverändert:

- Nur Performanceverbesserungen, kein Funktions-/Optikabbau, keine
  neue Physiknäherung und keine gelockerten numerischen Toleranzen.
- Gleiche Modelle, Eingaben, Verfahren, Zeitschritte, Hydrostatikintervalle,
  Einzelkräfte/-momente, Diagnosen, Einheiten und Bedienabläufe.
- Die exakten Python-Referenzen bleiben Vergleichsmaßstab. Keine
  Neuerzeugung eingefrorener Werte, um einen Kandidaten zu akzeptieren.
- Kein stiller Python-Fallback und keine Python-Rückrufe innerhalb des
  nativen Physikbatches. Bereits native Bibliotheksarbeit nicht unnötig
  neu schreiben.
- Für jede Übertragung Performancebericht nach A-V0.10-00034;
  Produktivübernahme nur nach Parität und End-to-End-Vorteil gemäß
  A-V0.10-00032.
- Ein weiterhin relevanter, ungelöster Python-Hotspot bleibt offen.
  „Kandidat ohne Gewinn“ ist kein vollständiger Migrationsabschluss.
- Keine Wiederaufnahme des entfernten Hallo-/TEST-Buttons.
- Keine automatische Veröffentlichung, Tags oder Releases. Sicherung
  auf dem Entwicklungsbranch erfolgt nur nach geltender Freigabe;
  keine eigenmächtige Rückkehr nach `main`.

## 2. Reihenfolge und Abhängigkeiten

M1 schafft erst die Vergleichsgrundlage; M2 die testbare native
Datenschicht. Danach werden Geometrie und Kräfte aufgebaut, bevor ein
vollständig nativer Integratorbatch und die Solver integriert werden.
Darstellung und Aufbaupfade folgen als getrennt messbare Kandidaten.
Die Reihenfolge verhindert, dass ein C++-Integrator mit Python-Kraftcallbacks
fälschlich als fertiger nativer Kern abgenommen wird.

Die Abhängigkeiten einzelner Quellen werden dabei ausdrücklich gestuft:
In M2 verarbeitet die native Körperaggregation bereits validierte
Geometrie-/Massendaten aus der bisherigen Vorbereitung; deren eigene
zeitkritische Pythonrechnung wird erst in M7 ersetzt und erneut integriert.
Das ist eine zeitweilige Aufbaugrenze, kein erlaubter Python-Rückruf
innerhalb des nativen Rechenkerns und kein vorzeitiger Abschluss von M7.
In M3 beginnt U-V0.10-000006 mit dem vorbereiteten Union-/Auftriebspfad.
Auftriebsvarianten, die die Schnittgeometrie aus U-V0.10-000007 benötigen,
werden erst mit diesem Folgeschritt vollständig nativ geschlossen.
A-V0.10-00012 wird deshalb erst am gemeinsamen M3-Gate abgenommen.

| Meilenstein | Schritte | Ergebnis | Eintrittsvoraussetzung |
|---|---|---|---|
| M1 | U-V0.10-000001 bis U-V0.10-000003 | Gesicherte Referenz, vollständiges Inventar, Prüfharness | Keine |
| M2 | U-V0.10-000004, U-V0.10-000005 | Native Basis, Datenbesitz, Frames und Körperkontext | M1 |
| M3 | U-V0.10-000006, U-V0.10-000007 | Exakte Hydrostatik und Wasserlinienkerne | M2 |
| M4 | U-V0.10-000008, U-V0.10-000009 | Hydrodynamik und zusammengesetzte Kraftbilanz | M2; M3 zusätzlich für Gesamtbilanz |
| M5 | U-V0.10-000010 | Vollständig nativer Echtzeitbatch | M3 und M4 |
| M6 | U-V0.10-000011 | Statische und stationäre Solver | M3 bis M5 |
| M7 | U-V0.10-000012 | Numerische Lade-/Änderungspfade | M2 und M3; in Planreihenfolge nach M6 |
| M8 | U-V0.10-000013 bis U-V0.10-000016 | Darstellung ohne Funktions-/Optikänderung | M5 und bestandene Kernregressionen; in Planreihenfolge nach M7 |
| M9 | U-V0.10-000017, U-V0.10-000018 | Weitere Bewegungs- und optionale Bestandspfade bewertet/migriert | M2 bis M5; in Planreihenfolge nach M8 |
| M10 | U-V0.10-000019, U-V0.10-000020 | Integrierte Abnahme und vollständige Nachweise | M1 bis M9 |

Die oben gewählte Ausführungsreihenfolge ist verbindlicher Standard.
Einzelne unabhängig vorbereitbare Kandidaten dürfen erst nach Prüfung
der angegebenen sachlichen Abhängigkeiten umgeordnet werden; dadurch
entfallen weder Gates noch Einzelfunktionsnachweise.

## 3. Arbeitsschritte

Die allgemeinen Prüfregeln aus Abschnitt 4 und die Querschnittsanforderungen
A-V0.10-00002 bis A-V0.10-00005 sowie A-V0.10-00031 bis
A-V0.10-00034 gelten zusätzlich für jeden betroffenen Migrationsschritt.

### U-V0.10-000001 — Ausgangsstand sichern und unveränderliche Referenz bilden

**Anforderungen:** A-V0.10-00001, A-V0.10-00002, A-V0.10-00004  
**Abhängigkeiten:** keine  
**Meilenstein:** M1

- Tag `0.9`/Commit `1b16648` als historischen Ursprung festhalten.
  Die tatsächliche Referenz ist der gesicherte V0.10-Stand mit
  Quelltrennung und Buildgrundlage, ohne Hallo-Test.
- Vorhandene uncommittete Änderungen einschließlich Nutzeränderungen
  inventarisieren; nichts verwerfen oder ungefragt in Sicherung aufnehmen.
  Wenn für die Referenzsicherung Commitfreigabe fehlt, diese einholen.
- Referenzcommit, Abhängigkeiten, Compiler, Flags, Python, Hardware,
  Konfigurationen, Modellhashes und Optikinventar festhalten.
- Python-Referenz unabhängig vom jeweils gewählten nativen Kandidaten
  ausführbar halten; keine automatische Referenzumschaltung.

**Abschluss:** Vollsuite und eingefrorener Referenzreplay erfolgreich;
identifizierbarer Referenzcommit und reproduzierbare Startkonfiguration
vorhanden. Die alten v0.9-Messungen allein erfüllen M1 nicht.

### U-V0.10-000002 — Einzelfunktionsinventar und neue Baselines erstellen

**Anforderungen:** A-V0.10-00001, A-V0.10-00032, A-V0.10-00033, A-V0.10-00034  
**Abhängigkeiten:** U-V0.10-000001  
**Meilenstein:** M1

- Sämtliche Funktionen/inneren Blöcke aus A-V0.10-00006 bis
  A-V0.10-00030 auflösen: Modul, qualifizierter Name, A-ID,
  Aufrufpfad, Häufigkeit, Eigen-/Gesamtzeit, Eingabegröße und native
  Bibliotheksanteile. Überlappende Gesamtzeiten nicht addieren.
- Echtzeit, Statik, stationäre Hydrodynamik, Modellaufbau/-änderung,
  alle Darstellungsvarianten und optionale Pfade getrennt erfassen.
- Optimist, Folkeboot, yacht1 und vorhandene analytische/generische
  Körper berücksichtigen. Kleine, typische und große gültige Eingaben
  sowie Fehler-/Grenzfälle bestimmen.
- Instrumentierte Profile von uninstrumentierten Baselines trennen.
  Ladezeit, Vorbereitungszeit, reine Rechnung und Datentransport
  getrennt erfassen.
- Noch nicht im Startinventar enthaltene Hotspots ergänzen; neue
  eigenständig prüfbare Anforderungen nach geltender Nummerierungsregel
  in die Spezifikation aufnehmen, nicht unter fremder ID verstecken.

**Abschluss:** Kein spezifizierter Funktionseintrag ohne Inventarzeile;
neue Baselines einschließlich wiederholter sichtbarer Messungen vorhanden.
Nicht aufgerufene Pfade anhand gezielter Szenarien untersuchen, nicht
aufgrund eines einzigen Folkebootlaufs als irrelevant erklären.
Soweit U-V0.10-000003 neue Messoptionen benötigt, sind betroffene Baselines
vor M1-Abnahme erneut damit zu erfassen. Die erste Inventarisierung darf
bestehende Werkzeuge verwenden; eine unvollständige frühe Messung sperrt
nicht die Verbesserung des Messharness, wohl aber die M1-Freigabe.

### U-V0.10-000003 — Vergleichsharness, Szenarien und Berichtsschema vorbereiten

**Anforderungen:** A-V0.10-00002, A-V0.10-00031, A-V0.10-00032, A-V0.10-00034  
**Abhängigkeiten:** U-V0.10-000001, U-V0.10-000002  
**Meilenstein:** M1

- Bestehende Tests den Inventareinträgen zuordnen und fehlende direkte
  Python-/C++-Vergleiche vor dem Kandidaten implementieren.
- Toleranzen, qualitative Gates, Messkonfiguration und Auswertungsverfahren
  vor Messbeginn einfrieren. Fehlende Paritätsgrenzen nicht nachträglich
  aus Kandidatenergebnissen ableiten; bei fachlichem Entscheidungsbedarf
  vorab Nutzerfreigabe einholen.
- Ergebnisse der unveränderten Python-Referenz erfassen; Fehlerfälle
  müssen tatsächlich scheitern. Absichtliche Testmutationen müssen
  abweichende Werte, fehlende Beiträge und falsche Frames erkennen.
- Berichtsvorlage und maschinenlesbare Rohdatenzuordnung aus Abschnitt 5
  einrichten; fehlende Messwerte sind Fehler, keine Null-/Erfolgswerte.

**Abschluss:** Harness funktioniert auf der Referenz, erkennt gezielte
Mutationen und ordnet jeden geplanten Block einem Test/Messfall zu.
Noch keine erfolgreich migrierte Funktion behaupten.
Vor Existenz des jeweiligen nativen Blocks wird nur der Referenz- und
Mutationspfad des Harness abgenommen. Die eigentlichen nativen
Paritätsfälle werden im betroffenen Migrationsschritt aktiviert und sind
bis dahin geplante Pflichtprüfungen, weder bestandene Tests noch Skips
wegen fehlender Implementierung. Die reguläre Suite muss in M1 ohne
noch nicht implementierte native Exporte ausführbar bleiben.

### U-V0.10-000004 — Native Schnittstelle, Build und sichere Datenhaltung

**Anforderungen:** A-V0.10-00003, A-V0.10-00004, A-V0.10-00005  
**Abhängigkeiten:** U-V0.10-000003  
**Meilenstein:** M2

- Vorhandenes pybind11-/CMake-Grundgerüst verwenden. Native Typen für
  Zustände, vorbereitete Modelldaten, Parameter, Beiträge und Ergebnisse
  definieren; keine neue Hello-Demo.
- Float64, Quaternionreihenfolge, Frames, Arrayform, Layout,
  Schreibbarkeit und Eigentum explizit festlegen.
- Fehlende Module, falsche ABI, ungültige Daten und native Fehler in
  explizite Python-/GUI-Diagnosen übersetzen. Tatsächlichen Rechenpfad anzeigen.
- GIL nur um reine C++-Arbeit freigeben. Kontrollierte Unterbrechung und
  Datenzugriff für spätere Worker-/Solverintegration vorsehen.
- Sauberen Neubau in einem neuen gezielten Buildverzeichnis und
  Installation in einer gesonderten Testumgebung prüfen; keine laufende
  Projektumgebung oder unbekannte Verzeichnisse löschen.

**Abschluss:** Release-Build/Neuinstallation funktionieren; Tests für
Lebensdauer, freigegebene Python-Eingaben, langlebige Ausgaben,
nicht zusammenhängende Arrays gemäß vereinbartem Vertrag,
NaN/Inf, Dimensionsfehler und fehlendes Modul bestehen.

### U-V0.10-000005 — Mathematik, Frames und Körperkontext übertragen

**Anforderungen:** A-V0.10-00006 (Quaternionbasis), A-V0.10-00020  
**Abhängigkeiten:** U-V0.10-000004  
**Meilenstein:** M2

Alle spezifizierten Quaternion-/Frameoperationen außer dem späteren
Integrator und der Anzeige-SLERP sowie Körperaggregation, Snapshots,
Gelenk-/Poseänderungen und Invalidierung abarbeiten.
Konstante Daten einmalig vorbereiten; geänderte Masse, Seglerposition,
aktive Blätter, Material und Gelenke müssen sie korrekt erneuern.

**Abschluss:** Rundläufe Matrix/Quaternion und Frame/Inverse, Steiner,
Punktmassen ohne Verdrängung, Körper-/Gelenkwechsel und Ausgabeleben
paritätisch geprüft; Performance jedes übertragenen Eintrags dokumentiert.

### U-V0.10-000006 — Union und exakte Auftriebsauswertung übertragen

**Anforderungen:** A-V0.10-00012, A-V0.10-00013, A-V0.10-00014  
**Abhängigkeiten:** U-V0.10-000005  
**Meilenstein:** M3

Erst den vorbereiteten Ebenenschnitt und seine Reduktionen übertragen,
dann Union-/Bibliotheksübergänge und Auftriebsbilanz einschließlich
erzeugter Kraftfunktions-Closures integrieren. Manifold3D-Bestand und
Referenzschnitt erhalten; Python-Konvertierungen von eigentlicher
nativer Bibliotheksarbeit unterscheiden.

**Abschluss:** 0/1/2/3 innere Dreiecksecken, koplanare Schnittlage,
kleine Volumina, nicht normierte/ungültige Ebene, Überlappungen,
trocken/vollnass und alle gespeicherten Modellfälle bestehen;
Volumen, Schwerpunkt, Kraft und Moment stimmen innerhalb exakter
Toleranzen. Kein voxelbasierter Ersatz und keine Seglerverdrängung.

### U-V0.10-000007 — Schnittgeometrie und Wasserlinienkennwerte übertragen

**Anforderungen:** A-V0.10-00012 (schnittabhängige Varianten),
A-V0.10-00015, A-V0.10-00016  
**Abhängigkeiten:** U-V0.10-000005, U-V0.10-000006  
**Meilenstein:** M3

Polygonclip, Konturketten, Ringzuordnung, Deckel und Flächenmomente
einschließlich aller spezifizierten Hilfsfunktionen übertragen.
Geometrie- und Hydrostatikpfad gemeinsam auf ihre Schnittstellen prüfen.

**Abschluss:** Mehrere Konturen, Löcher soweit unterstützt,
Orientierung, leere Schnitte, Schnitt durch Ecke/Kante und
Wasserlinienwechsel ergeben äquivalente Geometrie-/Kennwerte.
Nicht nur gleiche Vertexanzahl als Paritätsbeleg verwenden.
Danach sämtliche davon abhängigen Auftriebsvarianten aus
A-V0.10-00012 erneut integrieren und ohne innere Python-Schnittcallbacks
prüfen. Erst damit sind A-V0.10-00012 bis A-V0.10-00016 am M3-Gate
vollständig entscheidbar.

### U-V0.10-000008 — Hydrodynamische Vorbereitung, Benetzung und Rollenkräfte

**Anforderungen:** A-V0.10-00009, A-V0.10-00010, A-V0.10-00011  
**Abhängigkeiten:** U-V0.10-000005  
**Meilenstein:** M4

Vorbereitete Teilgeometrien, Benetzungsrechnung und alle Rollenkräfte
zusammenhängend übertragen. Vorhandene Ruder-Testnäherung separat
erhalten, aber nicht neu produktiv freigeben.

**Abschluss:** Null-, Vorwärts-/Rückwärts- und Rotationsströmung,
Teilbenetzung, Rudergrenzen, ungültige Eingaben, fehlende optionale
Module sowie sämtliche benannten Kräfte/Momente und Angriffspunkte
gegen Python geprüft; Vorbereitungs-/Laufzeitgewinn getrennt dokumentiert.

### U-V0.10-000009 — Aggregation und vollständiges Kraftmodell integrieren

**Anforderungen:** A-V0.10-00007, A-V0.10-00008  
**Abhängigkeiten:** U-V0.10-000006, U-V0.10-000008  
**Meilenstein:** M4

Wrench-Bezugspunktwechsel, Aggregation und Ergebnisergänzung integrieren;
Hydrostatik, Widerstände, Fluidbezug, Hydrodynamik, Fremdkraft und
Schwerkraft gemeinsam nativ ausführen. Cache-Reset und Standardintervall 1
unverändert lassen. Direktvergleichsschnittstellen dürfen Python-Adapter
verwenden, nicht die innere Gesamtberechnung.

**Abschluss:** Gesamtbilanz und jeder benannte Beitrag einschließlich
Eigen-/Hebelarmmoment stimmen; Parameterwechsel und Reset funktionieren.
Gezielte Laufzeitinstrumentierung muss null innere Python-Kraftaufrufe
nachweisen. Zusätzlich Python-Referenzfunktionen im explizit nativen
Testpfad durch fehlschlagende Wächter ersetzen: Der native Auftrag muss
weiter korrekt rechnen, ohne diese Wächter aufzurufen. Einen einzelnen
äußeren pybind11-Aufruf zu zählen genügt nicht als Nachweis.

### U-V0.10-000010 — Integrator, vollständigen Batch und Worker anbinden

**Anforderungen:** A-V0.10-00003, A-V0.10-00005, A-V0.10-00006 (Integration),
A-V0.10-00023 (Echtzeitteil)  
**Abhängigkeiten:** U-V0.10-000005, U-V0.10-000009  
**Meilenstein:** M5

Den unveränderten Integrationsalgorithmus mit dem nativen Kraftmodell
verbinden und ganze Batches ausführen. Einmaliger Kontextaufbau,
Parameterübergabe, Ergebnisdekodierung und Worker-Fehlervertrag anbinden.
Generationen/Sequenzen erhalten; ungültige Schrittzahlen explizit behandeln.

**Abschluss:** Einzelschritt und Batch verschiedener Länge, alle Zustände
zu identischen Zeiten für mindestens 30 s, messbare Perioden/Abklingfälle,
GIL-Freigabe, laufende GUI, Pause/Fortsetzung, Modellwechsel und Schließen
unter Last geprüft. Veraltete Ergebnisse werden nicht übernommen.
Kein Python-Aufruf je Schritt, Teil oder Dreieck; Übergabekosten separat.

### U-V0.10-000011 — Statische und stationäre Solver vollständig anbinden

**Anforderungen:** A-V0.10-00017, A-V0.10-00018, A-V0.10-00019,
A-V0.10-00023 (Statikteil)  
**Abhängigkeiten:** U-V0.10-000007, U-V0.10-000010  
**Meilenstein:** M6

Beide statischen Solver, stationäre Hydrodynamik und dynamische
Nachprüfung mit nativen Residuen und Kraftaufrufen übertragen.
Fortschritt und kontrollierten Abbruch grobkörnig anbinden.
Den einfachen Solver nicht stillschweigend durch den robusten ersetzen.

**Abschluss:** Gleiche stabile Lösungswahl, Such-/Abbruchkriterien und
Diagnosen; auch nicht konvergierende/ungültige Fälle prüfen.
GUI-Statikauftrag, Moduswechsel und veraltete Fortschrittsmeldungen testen.
End-to-End-Solverzeiten statt nur schnellerer Residuen dokumentieren.

### U-V0.10-000012 — Numerische Modellaufbau- und Änderungspfade abschließen

**Anforderungen:** A-V0.10-00021, A-V0.10-00022, A-V0.10-00020 (Reintegration)  
**Abhängigkeiten:** U-V0.10-000005, U-V0.10-000006  
**Meilenstein:** M7

Meshvalidierung/-schnittprädikate, Masseneigenschaften, Formgeneratoren,
Triangulierung, Formerkennung, Konfliktberechnung und Metadatenvermessung
nach Einzelfunktionsinventar übertragen bzw. Ausnahmen belegen.
Dateitransaktionen und Modellverträge unverändert lassen.

**Abschluss:** Ungültige Indizes, degenerierte/selbstschneidende Meshes,
unterstützte Polygonformen, bekannte analytische Masse/Trägheit,
Material-/Segler-/Gelenkänderung und Konfliktkorrektur einschließlich
Schreibfehlern getestet. Native Kontexte nach Änderungen erneut prüfen.
Kalte/warme Ladezeiten und Benutzeränderungen getrennt messen.

### U-V0.10-000013 — Anzeigeinterpolation und Poseaufbereitung übertragen

**Anforderungen:** A-V0.10-00024  
**Abhängigkeiten:** U-V0.10-000005, U-V0.10-000010  
**Meilenstein:** M8

SLERP, Zustandsauswahl, Positions-/Orientierungsinterpolation sowie
stationäre und nautische Poseableitung übertragen; Qt-Timer dürfen bleiben.

**Abschluss:** Quaternionvorzeichen, Batchgrenzen, 0/1/10 s Rückstand,
Pufferwachstum und Pause/Fortsetzung prüfen: kein Rücksprung,
kein Vorspulen, keine Extrapolation, unveränderter Physikzustand.

### U-V0.10-000014 — Körperdarstellung und Kraft-/Achsenaufbereitung

**Anforderungen:** A-V0.10-00025, A-V0.10-00026  
**Abhängigkeiten:** U-V0.10-000007, U-V0.10-000009, U-V0.10-000013  
**Meilenstein:** M8

Numerische Farb-/Benetzungs- und PolyData-Aufbereitung, Actortransformation,
Pfeile, Momentbögen, Marker und Hauptachsen übertragen. Bestehende
Wiederverwendung und Stil-/Geometrieinvalidierung erhalten.
VTK-Aufrufe auf zulässigem Thread; kein ungeprüfter Zugriff auf
VTK-Pythonobjekte aus GIL-freiem Code.

**Abschluss:** Alle Farbpfade und Layerkombinationen, Vordergrund,
Transparenz, Pfeilrichtung/-maße, Stilwechsel und Gelenke paritätisch.
Geometriearrays/Transforms direkt vergleichen und sichtbare gleiche
Szenen ergänzend prüfen; Screenshots allein genügen nicht.

### U-V0.10-000015 — Wasseroberfläche und Spuren übertragen

**Anforderungen:** A-V0.10-00027  
**Abhängigkeiten:** U-V0.10-000014  
**Meilenstein:** M8

Oberflächen-, Isoflächen-, Ring-/Spur- und Punktfeldrechnung aus dem
Inventar übertragen, ohne Auflösung, Optik oder Topologievertrag zu ändern.

**Abschluss:** Gleiche deterministische Punkte, Wassergeometrie,
Alpha-/Spurdaten und Sichtbarkeit; Topologie-/Modellwechsel invalidiert
korrekt. Vergleich mit identischer Wasseroptik und gleichem Viewport.

### U-V0.10-000016 — Navigation, Instrumente und Kamera abschließen

**Anforderungen:** A-V0.10-00028  
**Abhängigkeiten:** U-V0.10-000013, U-V0.10-000014  
**Meilenstein:** M8

Nautische Werte, SVG-Aufbereitung und Kameramathematik gemäß Inventar
übertragen. Bereits native Qt-Paintarbeit nachweisen, nicht duplizieren.

**Abschluss:** Winkelumschläge, Nullgeschwindigkeit, Perspektiven,
Fehler-/Gefahrenanzeigen, sichtbare/verdeckte Instrumentfenster und
Vordergrundkamera stimmen; keine neue Glättung oder geringere Frequenz.

### U-V0.10-000017 — Weitere Bewegung und Interaktion vervollständigen

**Anforderungen:** A-V0.10-00029  
**Abhängigkeiten:** U-V0.10-000005, U-V0.10-000010  
**Meilenstein:** M9

Kinematik, vereinfachte Dynamik, Störung/Kontakt und Bildschirm-/
Wasserprojektion einzeln prüfen und bei Zeitkritikalität übertragen.

**Abschluss:** Unveränderte Zufalls-/Störungsparameter, reproduzierbare
Bewegungen, Kontakt-/Projektionsfälle und Demo-/Interaktionspfade geprüft.
Nicht aufgerufene Bestandsfunktionen mit nachvollziehbarem Beleg führen.

### U-V0.10-000018 — Optionale Voxel-/GPU-Bestandspfade prüfen

**Anforderungen:** A-V0.10-00030, A-V0.10-00001  
**Abhängigkeiten:** U-V0.10-000006, U-V0.10-000010  
**Meilenstein:** M9

Säulenintervalle, körperfestes Voxelmodell und OpenCL-Datenvorbereitung
inventarisieren. Zeitkritische Pythonteile migrieren; vorhandene native
Kernels als solche belegen. Produktivsperren und Verfügbarkeitsdiagnosen
erhalten; keine neue GPU-/NPU-Abhängigkeit.

**Abschluss:** CPU-/Optionalpfadverträge, Transfers und fehlendes Backend
geprüft. Frühere Genauigkeitsfehler bleiben sichtbar; sie werden nicht
als bestandene exakte Physik ausgegeben. Nicht verfügbare Hardwareprüfung
bleibt ausdrücklich offen/begrenzt, keine erfundene GPU-Abnahme.

### U-V0.10-000019 — Integrierte Parität und End-to-End-Leistung abnehmen

**Anforderungen:** A-V0.10-00002 bis A-V0.10-00005,
A-V0.10-00031, A-V0.10-00032, A-V0.10-00034  
**Abhängigkeiten:** U-V0.10-000001 bis U-V0.10-000018  
**Meilenstein:** M10

Nach allen Migrationen vollständige Regression, native Direktvergleiche,
eingefrorenen Referenzreplay und vergleichbare Gesamtmessungen ausführen.
Saubere Installation und tatsächliche native Pfadwahl unabhängig prüfen.
Alle Modelle/Verfahren und beide unveränderten Optikprofile abdecken.

**Abschluss:** Keine unerklärte Paritätsabweichung, keine Regression,
kein ungelöster zeitkritischer Python-Innenpfad. Leistungsgewinn über
Messstreuung, unveränderte Funktion/Optik und keine reproduzierbare
Verschlechterung anderer relevanter Pfade belegt.

### U-V0.10-000020 — Einzelfunktionsmatrix und Abschlussdokumentation

**Anforderungen:** A-V0.10-00001, A-V0.10-00033, A-V0.10-00034  
**Abhängigkeiten:** U-V0.10-000019  
**Meilenstein:** M10

Jede A-ID und jeden Inventareintrag mit zulässigem Status, nativer
Implementierung bzw. begründeter Ausnahme, Test und Performancebericht
abschließen. Bereits native/nicht zeitkritische Funktionen von
implementierten Übertragungen unterscheiden. Offene Punkte nicht
stillschweigend zurückziehen oder ins Backlog verschieben.

**Abschluss:** Vollständigkeitsprüfung ohne Lücken; nur tatsächlich
umgesetzte und abgenommene Anforderungen in das zentrale
[Log](../../../../Log/Log.md) eintragen. Bleibt ein relevanter Hotspot
oder Pflichtnachweis offen, lautet der Stand Teilabschluss, nicht
„alle übertragen“. Produktivumschaltung erst nach allen Gates und
ausdrücklicher Gesamtfreigabe; keine automatische Veröffentlichung.

## 4. Meilensteinprüfungen

### Für jeden Meilenstein verpflichtend

1. Die zugehörigen Einzelfunktionen einschließlich Rand-/Fehlerfällen
   direkt Python/C++ vergleichen; Ergebnisse und unveränderte Toleranzen
   dokumentieren. In M1, vor Existenz der nativen Kandidaten, gilt
   stattdessen die Referenz-/Mutationsprüfung aus U-V0.10-000003;
   die nativen Vergleiche bleiben Pflicht des späteren Kandidatengates.
2. Die betroffenen vorhandenen Regressionen gemeinsam ausführen.
3. Jede tatsächlich übertragene Funktion in den Performancebericht
   aufnehmen; keine Freigabe allein anhand von Mikrobenchmarks.
4. Nach Integration die vollständige Projektsuite ausführen. Alle Skips
   mit Grund ausweisen; fehlende native Installation ist kein erlaubter
   Skip. Vorbestehende Umgebungssperren bleiben getrennt sichtbar.
5. Änderungen an Physik-/Geometrie-/Modellpfaden zusätzlich mit dem
   eingefrorenen Referenzreplay prüfen. Fehlgeschlagene Gates sperren
   Folgeintegration; Kandidaten verbessern, nicht Toleranzen verändern.

Die folgenden Testnamen sind vorhandene Regressionen, keine Behauptung
einer bereits vorhandenen C++-Paritätsabdeckung. Diese wird in
U-V0.10-000003 angelegt und bei jedem Block erweitert.

| Meilenstein | Vorhandene Tests unter `tests` | Zusätzlich neu nachzuweisende Tests |
|---|---|---|
| M1 | `test_project_layout.py`, `test_benchmark_profil.py`, `test_genauigkeit_v09.py` | Vollständigkeit des Funktionsinventars; eingefrorene Referenz-/Konfigurationshashes; Harness erkennt absichtliche Wert-/Frame-/Beitragsmutationen; vollständige Baselines |
| M2 | `test_frames.py`, `test_koerper.py`, `test_massenaenderung.py`, `test_segler.py`, `test_modell_lader.py` | Native Datengrenzen, Lebensdauer, ungültige Arrays, ABI-/Modulfehler, kein stiller Fallback; Quaternion-/Frameparität; Kontextinvalidierung |
| M3 | `test_volumen_union.py`, `test_auftrieb.py`, `test_hydrostatik.py`, `test_wasser_schnitt.py`, `test_wasserlinie_geometrie.py` | Direkte Schnittfall-/Kontur-/Randvergleichstests; alle eingefrorenen Hydrostatikfälle auf explizit nativem Pfad |
| M4 | `test_hydrodynamik_modell.py`, `test_hydrodynamik_referenz.py`, `test_hydrodynamik_ruder_naeherung.py`, `test_kraftmodell.py` | Benetzungsarrays und alle Rollen-/Einzelkräfte mit Eigen-/Hebelarmmoment; Null-/Rückwärts-/Rotationsströmung, Parameter-/Cache-Reset; keine Pythoncallbacks |
| M5 | `test_dynamik_6dof.py`, `test_echtzeit_prozess.py`, `test_gui_laufzeit_edit.py`, `test_gui_steuer_api.py` | Identische 30-s-Zustandsfolgen; messbare längere Perioden-/Abklingfälle; Batchlängen, Fehler, GIL-Freigabe ohne Timing-Flakiness, Generation/Sequenz, Schließen/Wechsel unter Last |
| M6 | `test_statisch.py`, `test_statisch_kugel.py`, `test_statisch_robust.py`, `test_stationaer_hydrodynamik.py`, `test_statische_darstellung.py` | Direkte Residuen-/Iterations-/Lösungsvergleiche, stabile Mehrfachlösungen, Nichtkonvergenz, Fortschritt/Abbruch und stationär-dynamische Nachprüfung |
| M7 | `test_mesh.py`, `test_mesh_validierung.py`, `test_formerkennung.py`, `test_formen_json.py`, `test_geometrie_konflikte.py`, `test_hydrodynamik_metadaten.py`, `test_active_body_factory.py`, `test_modellkatalog_auto.py` | Alle benannten Geometrieprädikate/Generatoren paritätisch; gültige/ungültige Polygonfälle, atomare Schreibfehler, kalter/warmer Aufbau, erneute Kontextinvalidierung |
| M8 | `test_gui_laufzeit_edit.py`, `test_grafik_bruecke_darstellung.py`, `test_farben_komposition.py`, `test_kraefte.py`, `test_overlays.py`, `test_pfeilstil.py`, `test_wasserbewegung.py`, `test_vista_ui.py`, `test_navigationswidgets.py`, `test_gui_steuerung.py` | SLERP/Anzeigepuffer, gleiche Arrays/Transforms/Farben, alle Layer-/Stilkombinationen, deterministische Wasserpunkte, SVG-/Kameravergleich und sichtbare Live-Parität ohne Optikreduktion |
| M9 | `test_bewegung_und_formen.py`, `test_dynamik.py`, `test_stoerung.py`, `test_sim_modus.py`, `test_voxelmodell.py`, `test_physik_backend.py` | Gleiches Kinematik-/Kontaktverhalten; optionale native Transfers, fehlendes Backend, unveränderte Sperren; keine behauptete Genauigkeitsfreigabe experimenteller Pfade |
| M10 | Gesamte Suite und eingefrorener Referenzreplay | Sauberer Release-Neubau/Installation, alle nativen Paritätsgruppen, vollständige GUI-/API-Lifecycleprüfung, Gesamtmessmatrix und Vollständigkeitsprüfung aller 34 A-IDs plus Einzelfunktionen |

### Ausführungsmuster für vorhandene Regressionen

Aus dem Repository-Hauptverzeichnis; die Buildwerkzeuge sind Voraussetzung:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw 'Nativer Build fehlgeschlagen.' }
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q -rs
if ($LASTEXITCODE -ne 0) { throw 'Regression fehlgeschlagen.' }
.\.venv\Scripts\python.exe werkzeuge\pruefe_genauigkeit_v09.py
if ($LASTEXITCODE -ne 0) { throw 'Referenzreplay fehlgeschlagen.' }
```

Einzelschritte nur bei erfolgreichem Vorgänger fortsetzen; insbesondere
ein erfolgreicher letzter Befehl darf einen vorherigen Testfehler nicht
überschreiben. Neu angelegte Paritätstests müssen vom regulären
pytest-Lauf erfasst werden. Falls der bisherige Referenzprüfer nur den
Python-Pfad auswertet, ist ein expliziter zusätzlicher nativer Replay
erforderlich; ein Python-Replay allein beweist keine native Parität.

Vorhandene Messwerkzeuge:
[Live-GUI](../../../../../werkzeuge/benchmark_gui_live.py),
[Workerprofil](../../../../../werkzeuge/benchmark_profil.py),
[Physik](../../../../../werkzeuge/benchmark_physik.py),
[Nachholen](../../../../../werkzeuge/benchmark_nachholen.py),
[Modellpaket](../../../../../werkzeuge/benchmark_modellpaket.py).
Ihre tatsächlichen CLI-Optionen vor Nutzung prüfen; Backend-/Ausgabeoptionen
bei Bedarf in U-V0.10-000003 ergänzen und testen. Keine noch nicht
existierenden Messbefehle als bereits ausführbar darstellen.

Sichtbare Messungen laufen mit Windows-QPA, nicht offscreen.
Aufwärmung, Profilkonfiguration und Viewport vorab fixieren.
Keine gleichzeitig laufenden CPU-/GPU-schweren Tests oder Benchmarks.

## 5. Performance- und Prüfprotokoll je Übertragung

Geplante Nachweise liegen unter `zuV0.10/Messungen`, die Einzelfunktions-
und Abnahmematrix unter `zuV0.10/Umsetzungsplan`. Diese Verzeichnisse/
Dateien werden im Umsetzungsschritt mit tatsächlichen Daten gefüllt,
nicht durch vorab als bestanden markierte Leerberichte ersetzt.

Jede Inventarzeile enthält mindestens:

| Feldgruppe | Pflichtinhalt |
|---|---|
| Identität | A-ID, U-ID, Modul, qualifizierte Funktion oder benannter innerer Block, nativer Elternblock |
| Referenz | Python-Referenzcommit, C++-Kandidatencommit, Modell-/Parameterhashes |
| Reproduktion | Eingaben/Eingabegröße, Kommando, Hardware, OS, Python-/Bibliotheks-/Compilerstände, Releaseflags, Warm-up, Wiederholungen |
| Korrektheit | Testfälle, bestehende Toleranzen, Einzel-/Zwischengrößen, Fehlerfälle, tatsächliches Ergebnis |
| Zeit | Python/C++ Median und P95, Streuung, Rohdatenlink; Eigen-/Gesamtzeit nicht verwechseln |
| Kostenaufteilung | Vorbereitung, Konvertierung, Kopien, Aufruf-/GIL-/IPC-Kosten und native Rechnung |
| Verbesserung | Absolut eingesparte Zeit, prozentuale Zeitersparnis, Beschleunigungsfaktor, End-to-End-Nutzen im zugehörigen Pfad |
| Entscheidung | Tatsächlicher Status, Ursache bei fehlendem Gewinn, offene Arbeit und Abnahmedatum |

Zulässige Einzelstatus entsprechen A-V0.10-00033: „nativ übertragen,
eingebunden und mit Gewinn abgenommen“, „bereits native Ausführung
nachgewiesen“, „gemessen nicht zeitkritisch, mit Profilbeleg“,
„Kandidat ohne Gewinn verworfen, Anforderung gegebenenfalls weiter offen“
oder „noch offen/blockiert, mit konkreter Ursache“. Nicht aufgerufen
oder noch nicht vermessen bedeutet nicht automatisch „nicht zeitkritisch“.

Für vergleichbare Zeitwerte:

- Zeitersparnis: `t_python - t_cpp`.
- Relative Zeitersparnis: `100 * (t_python - t_cpp) / t_python`.
- Beschleunigungsfaktor: `t_python / t_cpp`.

Bei Nullwerten, unzureichender Timerauflösung oder nicht isolierbaren
Hilfsfunktionen keine erfundenen Faktoren berechnen. Dann Messung
verbessern oder ausdrücklich nur den Gewinn des gemeinsamen Blocks
angeben; jeder Hilfseintrag verweist auf diesen Beleg.

Mindestens drei unabhängige Wiederholungen je Referenz/Kandidat unter
gleichen Bedingungen; bei uneindeutiger Streuung weitere Messungen,
keine Freigabe aus dem günstigsten Einzellauf. Reihenfolge möglichst
abwechselnd und unter gleichen Aufwärm-/Lastbedingungen; Referenzdaten
nicht zwischen Kandidaten stillschweigend ersetzen.

Für tatsächlich geänderte Live-Pfade jeweils mindestens 300 s nach
Warm-up. Aufbau-/Solverpfade zusätzlich mit ihrem vollständigen
Anwendungsfall messen, nicht künstlich durch FPS bewerten.
Standardoptik und bestehender Schulungsmodus separat bei exakt gleichen
jeweiligen Optionen vergleichen.

Die Gesamtmessmatrix umfasst alle drei Bootmodelle, repräsentative
analytische/generische Körper und den jeweils unterstützten Modus:
Statik, stationär, Echtzeit, Modell-/Beladungsänderung, Pause/Fortsetzung
sowie sichtbare/verdeckte Instrumente und relevante Layerkombinationen.
Nicht unterstützte Kombinationen mit Grund ausweisen. Bei
Szenarienbündelung bleibt jeder Fall einzeln rückverfolgbar.

Rohwerte, Median/P95, Streuung, Rückstandtrend, Physikdurchsatz,
Qt-Swaprate, Frameabstände, Eingabeproxy und Speicherentwicklung
dokumentieren. Die bekannten 30-Swap/s-, 67-ms-Frame-P95- und
100-ms-Eingabe-P95-Ziele ersetzen nicht den C++-Gewinnnachweis.
Scanout/Photonenlatenz wird nicht behauptet.

## 6. Rückverfolgbarkeitsmatrix aller aktiven Anforderungen

Alle Einträge sind **geplant**, nicht durch dieses Dokument erledigt.
Übergreifende Gates gelten zusätzlich bei jeder einzelnen Übertragung.

| Anforderung | Inhalt | Umsetzungsschritte | Maßgebliches Gate |
|---|---|---|---|
| A-V0.10-00001 | Vollständiges Hotspotinventar | U-V0.10-000001, U-V0.10-000002, U-V0.10-000018, U-V0.10-000020 | M1, M9, M10: keine unbegründete Lücke |
| A-V0.10-00002 | Funktion und Numerik erhalten | U-V0.10-000001, U-V0.10-000003, U-V0.10-000005 bis U-V0.10-000019 | Jedes Paritätsgate; M10 |
| A-V0.10-00003 | Native Schnittstelle/Datenbesitz | U-V0.10-000004, U-V0.10-000010, U-V0.10-000019 | M2/M5/M10: Lebensdauer, Kopien, keine inneren Pythoncallbacks |
| A-V0.10-00004 | Build/Installation/Referenz | U-V0.10-000001, U-V0.10-000004, U-V0.10-000019 | M1/M2/M10: sauberer Build, sichtbarer aktiver Pfad |
| A-V0.10-00005 | Fehler/Nebenläufigkeit | U-V0.10-000004, U-V0.10-000010, U-V0.10-000011, U-V0.10-000014 bis U-V0.10-000016, U-V0.10-000019 | GIL/Thread-/Lifecycle-/Fehlerprüfungen |
| A-V0.10-00006 | Quaternionen/6-DOF | U-V0.10-000005, U-V0.10-000010 | M2/M5: Mathematik und Zustandsfolgen |
| A-V0.10-00007 | Aggregation | U-V0.10-000009 | M4: Einzel-/Gesamtwrench |
| A-V0.10-00008 | Kraftmodell | U-V0.10-000009 | M4: alle Module/Resets |
| A-V0.10-00009 | Benetzung | U-V0.10-000008 | M4: Flächen-/Zentrenparität |
| A-V0.10-00010 | Rollenkräfte | U-V0.10-000008 | M4: alle Strömungs-/Ruderfälle |
| A-V0.10-00011 | Hydrodynamikaufbau/Testnäherung | U-V0.10-000008 | M4: Vorbereitung und vorhandener Testpfad |
| A-V0.10-00012 | Auftrieb | U-V0.10-000006, U-V0.10-000007 | M3: exakte Modellfälle einschließlich schnittabhängiger Varianten |
| A-V0.10-00013 | Union-Ebenenschnitt | U-V0.10-000006 | M3: alle Schnitt-/Randfälle |
| A-V0.10-00014 | Union/Bibliotheksübergänge | U-V0.10-000006 | M3: native Anteile und Kosten belegt |
| A-V0.10-00015 | Wasserlinienschnitt | U-V0.10-000007 | M3: Konturen/Deckel |
| A-V0.10-00016 | Wasserlinienkennwerte | U-V0.10-000007 | M3: Flächenmomente |
| A-V0.10-00017 | Robuster Solver | U-V0.10-000011 | M6: gleiche Lösung/Diagnose |
| A-V0.10-00018 | Weiterer statischer Solver | U-V0.10-000011 | M6: eigener Pfad erhalten |
| A-V0.10-00019 | Stationärer Solver | U-V0.10-000011 | M6: stationär und dynamisch |
| A-V0.10-00020 | Körper/Frames/Gelenke | U-V0.10-000005, U-V0.10-000012 | M2/M7: Aggregation/Invalidierung |
| A-V0.10-00021 | Mesh/Masseneigenschaften | U-V0.10-000012 | M7: Prädikate und Trägheit |
| A-V0.10-00022 | Weitere Modellvorbereitung | U-V0.10-000012 | M7: jede Generator-/Messfunktion |
| A-V0.10-00023 | Batches/Worker | U-V0.10-000010, U-V0.10-000011 | M5/M6: Echtzeit und Statik |
| A-V0.10-00024 | Anzeigeinterpolation | U-V0.10-000013 | M8: monotone gleiche Anzeige |
| A-V0.10-00025 | Körpergrafik/Farben | U-V0.10-000014 | M8: alle Farbpfade |
| A-V0.10-00026 | Pfeile/Momente/Achsen | U-V0.10-000014 | M8: Geometrie und Stil |
| A-V0.10-00027 | Wasser/Spuren | U-V0.10-000015 | M8: deterministische gleiche Daten |
| A-V0.10-00028 | Instrumente/Kamera | U-V0.10-000016 | M8: gleiche Optik/Frequenz |
| A-V0.10-00029 | Weitere Bewegung | U-V0.10-000017 | M9: Interaktion/Kinematik |
| A-V0.10-00030 | Optionale Voxel-/GPU-Pfade | U-V0.10-000018 | M9: Bestandssperren und Transfers |
| A-V0.10-00031 | Parität/Regression | U-V0.10-000003, U-V0.10-000005 bis U-V0.10-000019 | Alle Meilensteine, Vollsuite M10 |
| A-V0.10-00032 | Reproduzierbarer Gewinn | U-V0.10-000002, U-V0.10-000003, U-V0.10-000005 bis U-V0.10-000019 | Je Kandidat und Gesamtvergleich |
| A-V0.10-00033 | Vollständiger Abschluss | U-V0.10-000002, U-V0.10-000020 | M10: Einzelfunktionsmatrix und Log |
| A-V0.10-00034 | Performance je Übertragung dokumentieren | U-V0.10-000002, U-V0.10-000003, U-V0.10-000005 bis U-V0.10-000020 | Je Übertragung, Abschluss ohne Nachweislücke |

## 7. Abbruch, offene Entscheidungen und Status

Scheitert Parität oder Robustheit, wird der Kandidat nicht produktiv
aktiviert. Scheitert der Performancebeleg, wird die Ursache untersucht
und der Ansatz verbessert; bleibt ein relevanter Python-Hotspot
ungelöst, wird der Punkt offen/blockiert geführt. Eine alternative
Funktionsreduktion oder Näherung gehört nicht zu diesem Auftrag.

Nutzerentscheidungen sind vor der betroffenen Umsetzung einzuholen,
wenn Referenzsicherung, fehlende fachliche Toleranzen, Änderung eines
öffentlichen Vertrags oder eine Scopeänderung erforderlich werden.
Vorschläge werden mit plausiblen Optionen vorgelegt. Bereits geltende
Genauigkeitsgrenzen werden dabei nicht zur Lockerung angeboten.

Zu jedem Meilenstein enthält das Prüfprotokoll Datum, Commit,
Umgebung, tatsächliche Kommandos, Ergebnisse, Skips, Performancebelege,
offene Fehler und Entscheidung. Fehlende Tests/Messungen sperren das
Gate. Ein reiner Dokument- oder Buildstand ist kein Migrationsabschluss.

## Nicht umsetzen

Aktuell keine zurückgezogenen Umsetzungsschritte. Spätere Rücknahmen
bleiben unter ursprünglicher Kennung mit Begründung nachvollziehbar.
