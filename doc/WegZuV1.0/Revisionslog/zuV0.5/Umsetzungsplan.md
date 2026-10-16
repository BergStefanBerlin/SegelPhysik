# Umsetzungsplan zu Spec v0.5

**Bezug:** [Spezifikation v0.5](./Spezifikation_v0.5.md)
**Stand:** 16.10.2026
**Status:** In Umsetzung; Phasen 0–9 funktional umgesetzt, Phase 10 teilweise umgesetzt. Das B-03-Leistungsgate ist bestanden. Phase 11 (externe Migration und vollständige Cutover-Abnahme) sowie Phase 12 (fachliche Festlegung der Hydrodynamik/Aerodynamik) sind offen.

## 1. Ziel und Erfolgsdefinition

Der Umbau soll die bestehende Funktionalität vollständig erhalten und die
Körper-/Importarchitektur erweitern. „100 % Funktionalität und Geschwindigkeit“
wird als verbindliches Nichtregressionsziel behandelt: Kein bestehender
Anwendungsfall darf verloren gehen; bei gleicher Hardware, Datenbasis,
Konfiguration und Arbeitslast darf der neue Stand keine nachweisbare
Verschlechterung der vereinbarten Laufzeitkennzahlen zeigen.

Eine buchstäblich identische Laufzeit in jedem einzelnen Durchlauf ist wegen
Betriebssystem-, Scheduler- und Messrauschen nicht garantierbar. Deshalb wird
die Forderung mit reproduzierbaren Baselines, Messstreuung und einem
Abnahme-Gate operationalisiert. **Ein Umbauabschnitt wird nicht freigegeben,
wenn funktionale Parität fehlt oder ein signifikanter Performance-Rückgang
auftritt.**

Jeder Abschnitt endet in einem rücksetzbaren, getesteten Commit. Bestehende
APIs und Ladepfade bleiben so lange verfügbar, bis deren Ersatz nachweislich
paritätisch und mindestens gleich schnell ist. Neue Features werden nicht als
Entschuldigung für Regressionen an bisherigen Abläufen verwendet.

### 1.1 Abgrenzung der Parität

| Kategorie | Was „100 % erhalten“ hier bedeutet | Nachweis |
|---|---|---|
| Bestehende Modelle | Alle derzeit unterstützten Körper, Boote, Formen, Materialien und JSON-Konfigurationen laden weiterhin oder werden verlustfrei migriert. | Reale Bestandsdaten, Inventar und Migrationstest. |
| Physik | Bestehende statische Gleichgewichte, Statusmeldungen, Kräfte, Momente, Bewegungsabläufe und numerische Stabilität bleiben innerhalb dokumentierter numerischer Toleranzen. | Referenzergebnisse, analytische Tests und Regressionstrajektorien. |
| Darstellung/Bedienung | Bestehende Auswahl, Editierung, Kamera, Wasser, Kraftpfeile, Status und Steuerung bleiben funktional. | GUI-Smoke- und Interaktionsfälle. |
| Leistung | Modellladen/-aufbau, Hydrostatik, Solver, Dynamikschritt, Rendering und GUI-Reaktion zeigen auf derselben Arbeitslast keine signifikante Verschlechterung. | Kontrollierte Baseline-Benchmarks vor/nach jedem relevanten Abschnitt. |
| Neue Spezifikationsregeln | Neue Fähigkeiten werden zusätzlich eingeführt, ohne Altverhalten still zu ändern. Explizite Modellannahmen wie die Ein-Körper-Näherung sind separat testbar. | Neue K-01–K-38-Abnahmetests. |

## 2. Verbindliche Schutzregeln

1. **Vorher messen:** Keine Performanceoptimierung oder Datenpfadänderung ohne
   reproduzierbare Messung des betroffenen Ist-Pfads.
2. **Doppelte Ausführung nur als zeitlich begrenzter Testmodus:** Alte und neue
   Resultate dürfen zum Vergleichen parallel berechnet werden, aber nicht
   dauerhaft in der interaktiven Simulation doppelt laufen.
3. **Adapter statt Big Bang:** Bestehende Loader-, Fabrik-, Solver-,
   Darstellungs- und Integrator-APIs bleiben als dünne Adapter erhalten, bis
   Aufrufer migriert und Parität belegt ist.
4. **Ein Ergebnis, ein Commit:** Pro Phase genau ein fachlich abgrenzbarer
   Umbau, Tests und Benchmark; bei Regression wird der Abschnitt korrigiert
   oder nicht freigegeben.
5. **Korrektheit vor Optimierung:** Keine Cache-/Batch-/Approximationstechnik,
   die unbemerkt alte oder inkonsistente Werte liefert.
6. **Gleiche Arbeitslast:** Vergleiche nutzen identische Python-Version,
   Abhängigkeiten, Hardware-Einstellungen, Beispieldaten, Solverparameter,
   Renderauflösung und Simulationsdauer.
7. **Messung nicht durch GUI-Rauschen verfälschen:** Kernbenchmarks messen
   Loader, Geometrie, Solver und Integrator getrennt; End-to-End-Messungen
   messen zusätzlich Start bis erster sichtbarer Frame und Interaktionslatenz.
8. **Keine vorzeitige Modellphysik:** Noch nicht abgesicherte Wasser-/Luftkräfte
   bleiben deaktiviert, bis ihre eigenen physikalischen Referenztests bestehen.

## 3. Vorgehensmodell und Freigabegates

Jede Phase hat vier verbindliche Gates:

- **G1 – Bestehende Tests:** relevante bestehende Tests und danach vollständige
  Testsuite bestehen.
- **G2 – Neue Abnahmetests:** alle in der Phase festgelegten Tests bestehen.
- **G3 – Parität:** Bestandsmodelle und Referenzsimulationen bleiben im
  Toleranzvertrag aus Abschnitt 4.
- **G4 – Leistung:** Betroffene Pfade werden gemessen; ein fehlendes oder
  nicht bestandenes Ergebnis sperrt die Produktionsumschaltung. Eine
  folgende Phase darf einen nicht-produktiven Kandidaten bauen, wenn dieser
  ausdrücklich zur Behebung oder belastbaren Messung des offenen Gates
  erforderlich ist. Sie darf den Legacy-Produktivpfad nicht ablösen.

Die Gesamtfreigabe einer Phase erfolgt erst nach allen vier Gates. Fehler und
fehlgeschlagene Messungen werden sichtbar protokolliert; ein fehlender
Benchmark ist kein bestandener Benchmark.

## 4. Referenzstand und Performancevertrag

### 4.1 Baseline vor dem Umbau (Phase 0)

Vor der ersten Codeänderung wird ein unveränderliches Baseline-Protokoll
erzeugt und mit Commit, Python-/Bibliotheksversionen, Rechnerdaten und
Konfiguration verknüpft. Mindestens zu messen sind:

| ID | Arbeitslast | Messwerte |
|---|---|---|
| B-01 | Anwendungsstart mit Standardkonfiguration | Prozessstart bis GUI bedienbar, Start bis erste 3D-Szene, Spitzen-RAM |
| B-02 | Laden/Aufbauen eines einzelnen parametrischen Körpers | Ladezeit, Fabrikzeit, Mesh-/Knotenanzahl, RAM |
| B-03 | Laden/Aufbauen der Yacht/des komplexesten Bestandsmodells | Ladezeit, OBJ-Parsezeit, Fabrikzeit, Mesh-/Knotenanzahl, RAM |
| B-04 | Hydrostatik für feste Pose und vollständige Körpergeometrie im aktuellen Echtzeit-Betriebsmodus (`intervall=1`) | Laufzeit je Pose, Arbeitsmenge, Cachezustand; p95 nur mit ausreichender Stichprobe |
| B-05 | Statische Gleichgewichtssuche | Gesamtlaufzeit, Kraftauswertungen, Iterationen, Endresiduum, Ergebnisstatus |
| B-06 | Ein dynamischer Schritt ohne GUI | Schritte/Sekunde und Laufzeit je Schritt; gleiche Anfangsbedingungen |
| B-07 | Echtzeit-Batch mit aktueller Batchgröße | Simulationszeit/Wandzeit, Rückstand, Anzahl Schritte, maximale Update-Latenz |
| B-08 | Szene mit Wasser, Spuren und Kraftpfeilen | Zeit pro Renderupdate, Framezeit p50/p95, RAM |
| B-09 | Interaktive Parameteränderung (z. B. Masse) | Zeit bis konsistente Neuberechnung und sichtbare Aktualisierung |
| B-10 | Modellkatalog anzeigen, ohne Geometrien zu parsen | Kataloglaufzeit, Paket-/Manifestanzahl, Meshallokationen |
| B-11 | Meshvalidierung und Berechnung der Masseneigenschaften | Validierungs- und Kennwertzeit getrennt, Meshgröße, RAM |
| B-12 | Nur bei gewünschter approximativer Hydrostatik: Intervallwiederverwendung gegen exakten Pfad | Laufzeit, Kraft-/Momentabweichung je Pose, maximale und kumulative Trajektorienabweichung |

Baseline und Kandidat werden paarweise mit identischen Eingaben und derselben
Umgebung gemessen; die Reihenfolge wird zwischen Baseline/Kandidat
abwechselnd oder randomisiert. Nach fünf Warm-up-Läufen sind mindestens 30
Messpaare pro Kernbenchmark nötig. Bei sehr teuren End-to-End-Szenarien sind
mindestens 10 Paare zulässig. Es werden Median, Rohwerte und Streuung
gespeichert. p95 bleibt bis 1.000 Messpaaren informativ; erst ab 1.000 Paaren
kann es für kontrollierte Kernbenchmarks ein Abnahmekriterium sein. Bei
teuren End-to-End-Messungen bleibt p95 informativ; dort wird die
Median-Abnahme paarweise bewertet. Ausreißer werden nicht still verworfen.
Bei Hardware-/Treiberwechsel ist eine neue Baseline zu erstellen, bevor
Umbauvergleiche fortgesetzt werden.

### 4.2 Abnahmeregel für Laufzeit

- Jeder Einzelbenchmark wird mit einer explizit zugeordneten Baseline-ID
  verglichen; schnelle Verbesserungen in einem Pfad dürfen Regressionen in
  einem anderen nicht kompensieren.
- Aus den gepaarten Laufzeitverhältnissen Kandidat/Baseline wird ein
  95-%-Bootstrap-Konfidenzintervall für den Median berechnet. Bei mindestens
  1.000 gepaarten Stichproben wird p95 zusätzlich durch ein Bootstrap-
  Konfidenzintervall der gepaarten p95-Verhältnisse bewertet. End-to-End-p95
  bleibt informativ.
  Ein Benchmark besteht nur, wenn die obere Konfidenzgrenze höchstens 1,00
  beträgt.
- Schneidet das Intervall 1,00, ist das Ergebnis **uneindeutig und nicht
  freigegeben**, nicht automatisch „kein Unterschied“. Die Stichprobe wird
  für Medianvergleiche bis höchstens 100 Paare, für p95-pflichtige
  Kernbenchmarks bis 1.000 Paare und für End-to-End-Messungen bis 30 Paare
  erweitert. Bleibt das Ergebnis dann uneindeutig, wird die Phase nicht
  freigegeben; Messumgebung und Workload sind zu prüfen und neu zu messen.
  Abweichungen werden nicht durch Verbesserungen anderer Benchmarks
  verrechnet.
- Numerische Physik-/Geometrievergleiche verwenden pro Messgröße vorab
  festgelegte Toleranzen aus wiederholten Baseline-Läufen und unabhängigen
  Referenzwerten. Toleranzen dürfen nach Sichtung eines Kandidatenergebnisses
  nicht nachträglich gelockert werden.
- Ist die Messung nicht eindeutig, werden zusätzliche Läufe gemacht. Eine
  bloße Behauptung „fühlt sich gleich schnell an“ genügt nicht.
- Es gibt keine pauschale 5-/10-%-Toleranz, die eine langsamere Umsetzung
  automatisch freigibt. Jede signifikante Verschlechterung blockiert die
  Migration bis zur Optimierung oder einer ausdrücklich vom Nutzer
  freigegebenen Zieländerung.
- Auch Spitzen-RAM und GUI-Reaktionslatenz sind Leistungskennzahlen; keine
  lineare RAM-Steigerung durch doppelt gehaltene alte/neue Meshes im
  Regelbetrieb.

## 5. Optimale Umsetzungsreihenfolge

### Phase 0 – Bestehendes Verhalten einfrieren und messen

**Zweck:** Vor jedem Umbau wissen, was Funktionalität und Geschwindigkeit
heute konkret bedeuten.

| Arbeit | Ergebnis |
|---|---|
| Bestehende Test-/Demo-/Modellinventare aufnehmen | Liste aller Körper, Konfigurationsdateien, GUI-Modi, veränderbaren Parameter und aktiven Darstellungen. |
| Referenzfälle aus echten Dateien aufbauen | Golden-Datensatz für Masse, Schwerpunkt, Trägheit, Volumen, Hydrostatik, Solverstatus, Kraft-/Momentenresultat und kurze dynamische Trajektorien. |
| B-01 bis B-11 messen; B-12 nur bei Freigabe einer Näherung | Vergleichbare, wiederholbare Baseline mit Umgebungsmetadaten. |
| Snapshot der bestehenden öffentlichen APIs und Aufrufer erstellen | Adapter-/Migrationsliste; kein Aufruf wird versehentlich übersehen. |

**Abnahme:** Bestehende Suite ist grün; alle Baselinefälle reproduzierbar;
keine Messgröße ohne dokumentierte Eingabe und Auswertung.

### Phase 1 – Datenverträge, Koordinaten und Versionsregeln festlegen

**Abhängigkeit:** Phase 0.

| Arbeit | Anforderungen |
|---|---|
| IDs, Manifestversion, Paketwurzel und Schemafehler spezifizieren | K-01, K-02, K-03, K-21, K-22 |
| Körpersystem, Teilsystem, Kamerasystem und Rechenframe normieren | K-05, K-14, K-27 |
| Nautisches Weltsystem ausdrücklich aus dem aktuellen Umbau ausschließen | K-05, K-27 |
| Daten-/GUI-/Physik-Schichtgrenzen und Funktions-vs.-Klassen-Regel verankern | K-23, K-24 |
| Laufzeitkörper vs. Manifest vs. Simulationszustand und atomare Aktualisierung festlegen | K-25, K-26 |
| Ursprung und Transformationssemantik festlegen: OBJ-Frame, Knotenframe, Elternkomposition, Schwerpunktzentrierung samt Rückversatz und initialer Gesamtschwerpunkt | K-05, K-14, K-27 |
| Transformationsgleichung und Konvention für Achsenabbildung, Einheiten, Quaternionen und lokale Posen verbindlich festschreiben | K-05, K-14, K-27 |
| Aktive/abgewählte Teilsemantik, Material- und Massendefinitionen festschreiben | K-08, K-18, K-19 |
| Normative Manifestfelder samt Paketwurzel, Slugs und minimaler Vorlage festlegen; Referenzpunkte für OBJ-, Pose-, Zentrierungs- und Invers-Transformationen dokumentieren | K-01, K-02, K-03, K-05, K-08, K-14, K-21 |

**Abnahme:** Schemaentwurf, Referenzbeispiele und Koordinatentestfälle sind
freigegeben, bevor der Loader geändert wird.

### Phase 2 – Kanonisches Mesh und sichere Geometrieauflösung

**Abhängigkeit:** Phase 1.

| Reihenfolge | Arbeit | Anforderungen |
|---|---|---|
| 2.1 | Unveränderlichen Mesh-Vertrag `(punkte_SI, dreiecke, frame, Metadaten)` einführen; vorerst mit Adaptern aus Altquellen speisen. | K-04, K-05, K-27 |
| 2.2 | Gemeinsame Meshvalidierung und Fehler mit Modell-/Knotenpfad anbinden. | K-07 |
| 2.3 | Paketrelative Pfadprüfung gegen Traversal/Symlinks/absolute Pfade implementieren; Pfade nach Auflösung innerhalb Paketwurzel verifizieren. | K-06 |
| 2.4 | OBJ-Unterstützung für positive/negative Indizes und optionale Normal-/Texturindizes; Polygonfälle korrekt triangulieren oder gezielt ablehnen. | K-06 |
| 2.5 | Formquelle und OBJ-Quelle durch denselben Resolver auf Mesh abbilden. | K-04 |
| 2.6 | Meshableitungen nur nach Messung cachen; Cache-Key aus kanonischen Eingangsdaten und Importoptionen. | K-27, K-34 |

**Leistungsschutz:** Parser und Meshvalidierer nicht mehrfach pro GUI-Click
ausführen. Warm- und Kaltpfad separat messen; Geometrien einmalig vorbereiten
und immutable Meshes weiterreichen.

**Umsetzung Phase 2:** Der kanonische Mesh-Vertrag, die gemeinsame
Meshvalidierung, paketrelative Pfadprüfung und der gemeinsame Form-/OBJ-
Resolver sind in `segelphysik/core/mesh.py` umgesetzt. Die zur Masse passende
Topologieprüfung lehnt lokale Orientierungsfehler und nicht-mannigfaltige
Kanten ab, verlangt geschlossene Netze für Volumenmasse und normalisiert
konsistent invertierte geschlossene Netze. Der OBJ-Loader
unterstützt positive und negative Vertex-, Textur- und Normalenindizes;
einfache Dreiecke werden beschleunigt verarbeitet, komplexere Polygone
robust trianguliert oder mit konkretem Fehler abgelehnt. Der
Legacy-Kompatibilitätspfad bleibt als explizit wählbarer Rückfall erhalten.
Alle acht vorhandenen Yacht-OBJ-Dateien lassen sich syntaktisch laden. Die
gezielten Mesh-/Pakettests bestehen mit **22 passed, 1 skipped**;
die aktuelle vollständige Testsuite besteht mit **563 passed, 1 skipped**.
Der Symlink-Test ist in der aktuellen Windows-Umgebung mangels Symlink-
Rechten übersprungen; die Pfadprüfung wertet aufgelöste Ziele dennoch gegen
die Paketwurzel aus.

T-011 besitzt eine Sweep-and-prune-Prüfung mit koplanarem SAT-Test für
nicht-benachbarte Dreiecke. Tests decken echte Schnitte, koplanare
Überlappung, gemeinsame Kanten, getrennte Komponenten sowie Kontextfehler ab.
Die Yacht-Mastdatei bestand aus neun jeweils geschlossenen Komponenten, deren
Beschläge sich im selben OBJ gegenseitig schnitten. Die ursprüngliche
Paketmigration bildete sie als Mastbaugruppe mit einem Mastprofil und acht
getrennten Beschlagkomponenten ab; die Legacy-OBJ-Quelle blieb unverändert.
Großbaum und Großsegel schneiden das Mastmesh nicht. Die Golden-Parität für
Masse und Trägheit bestand nach dieser Aufteilung. **Modellkorrektur vom
16.10.2026:** Auf Nutzerwunsch enthält das aktive Yachtpaket nur noch das
Mastprofil als einzelnes Blatt `Mast`; die zwei zuletzt verbliebenen
Zusatz-Patches und ihre Paket-OBJ-Dateien sind entfernt. Dadurch liegt die
Paketmasse nun bei `450.365556 kg` statt beim historischen Phase-3-Wert
`450.379457 kg`; die Legacy-Referenz wurde nicht verändert. Die
Phase-3-Goldenwerte und der B-03-Vergleich dokumentieren weiterhin den
vorherigen Paketstand. T-011-Funktionstests bestehen. Der aktuelle
End-to-End-B-03-Bericht in
Phase 3/4 besteht das Leistungsgate; der frühere negative Befund ist damit
historisch und kein aktueller Blocker.

Ein diagnostischer, gepaarter Parservergleich mit 50 Wiederholungen über die
acht Yacht-OBJ-Dateien ergab für den kanonischen Parser gegenüber dem
schmaleren Legacy-Parser ein Medianverhältnis von **1,72**
(Bootstrap-95-%-Intervall **1,68–1,73**). Die Parser leisten nicht exakt
denselben Validierungsumfang; dies ist deshalb allein kein formales B-03-
Abnahmeergebnis. Der kanonische Paketpfad ist inzwischen per Settings-Schalter
für Repository-Modelle aktiv. Der vollständige gepaarte B-03-Vergleich mit
T-011 ist in Phase 3/4 dokumentiert und bestanden; die frühere Diagnose bleibt
nur zur Einordnung des Parser-Overheads relevant.

### Phase 3 – Modellloader, Validierung und Modellpaketkatalog

**Abhängigkeit:** Phase 2.

| Reihenfolge | Arbeit | Anforderungen |
|---|---|---|
| 3.1 | Versioniertes Manifest laden; Pflichtfelder/Versionen strikt prüfen. | K-01, K-02 |
| 3.2 | Baumformen, IDs, Masse auf Gruppen, leere Gruppen, Rollen und Referenzen validieren. | K-03, K-08, K-10 |
| 3.3 | Modellpakete über explizite Datenwurzel finden; niemals CWD-abhängig laden. | K-01, K-21 |
| 3.4 | Quellenresolver und Materialkatalog injizieren; keine Format-/Materiallogik in GUI einbauen. | K-04, K-08, K-23 |
| 3.5 | Sichtbare, präzise Fehler samt relativer Datei und Knotenpfad durchreichen. Keine stillen Fallbacks. | K-06, K-21, K-32 |
| 3.6 | Loader-/Schema-/Paketbeispiele in automatisierte Validierung integrieren. | K-22 |
| 3.7 | Vollständiges Inventar aller unterstützten Modelle/Konfigurationen und eine explizite Altquelle-zu-Paket-Zuordnung anlegen; keine Auswahl nur repräsentativer Modelle. | K-20, K-22, K-37 |
| 3.8 | Migrationsfälle, erwartete Manifest-/Geometriezuordnung und Golden-Daten (Masse, Schwerpunkt, Trägheit, Volumen, Startpose) für jedes Inventarmodell vorbereiten; nicht abbildbare Fälle als offene Blocker dokumentieren. | K-20, K-22, K-37 |

**Leistungsschutz:** Paketkatalog darf Verzeichnisse cachen, muss Änderungen
oder expliziten Refresh unterstützen; keine Meshdaten vollständig laden, um
nur Modellnamen anzuzeigen.

**Fortschritt Phase 3 – funktionale Arbeiten und B-03-Leistungsgate
abgeschlossen:** Der strikte Loader,
Materialinjektion, Paketkatalog mit expliziter absoluter Datenwurzel,
Schema-/Pfadprüfungen sowie der vollständige Abgleich mit den neun derzeit
konfigurierten Hauptobjekten sind umgesetzt. Die maschinenlesbare Vorlage
wird mitgeprüft; die acht Formpakete bestehen auch den vollständigen
Mesh-/Massentopologiepfad. [`Inventar_Phase3.json`](./Inventar_Phase3.json)
friert die Legacy-Massen-, Schwerpunkt-/Modellversatz-, Trägheits- und
Geometriewerte aller neun Bestandsmodelle ein. Die acht OBJ-Blätter der
Yacht sind paketbasiert ladbar. Für Großsegel und Fock liegen deduplizierte
Paketkopien vor; die Legacy-OBJ-Quellen bleiben unverändert. Durch die
Verdopplung der jeweiligen Manifest-Wanddicke bleiben Masse, Schwerpunkt
und Trägheit gemäß Legacy-Golden unverändert. B-19 ist damit technisch
abgenommen. Die Legacy-Goldenwerte bleiben als Phase-3-Referenz eingefroren;
die aktuellen Paketkennwerte einschließlich der Mastprofil-Korrektur sind
separat getestet. Phase 3 ist funktional umgesetzt. Der erste B-03-Vergleich
und der nachfolgende Vergleich mit 19,063-facher Laufzeit sind historische
Messungen; auch der aktuelle End-to-End-Vergleich wurde vor der
Mastprofil-Korrektur aufgenommen.

Der aktuelle gepaarte B-03-Vergleich (fünf Warm-ups je Pfad, 30 alternierende
Paare, 20.000 Bootstrap-Resamples, T-011 aktiv) maß den Legacy-Median mit
**0,02265 s** und den Paketfabrik-Median mit **0,02013 s**. Das Medianverhältnis
Paket/Legacy beträgt **0,883** (Bootstrap-95-%-Intervall **0,859–0,913**);
das B-03-Leistungsgate ist bestanden. Die Legacy-Abbildung und der
Paketaufruf sind im Benchmarkwerkzeug explizit getrennt. Rohwerte und
Messaufbau stehen in
[`B03_Paketvergleich_Phase4.json`](./B03_Paketvergleich_Phase4.json).
Dies weist das B-03-Gate nach, ersetzt jedoch nicht die vollständige
GUI-/Migrations-/Physikabnahme aus Phase 11.
Der Messlauf lässt sich mit dem Werkzeug
[`benchmark_modellpaket.py`](../../../../werkzeuge/benchmark_modellpaket.py)
und dessen Standardparametern aus dem Repository-Hauptverzeichnis
wiederholen.

### Phase 4 – Laufzeitkörper und einheitliche Fabrik

**Abhängigkeit:** Funktionale Ergebnisse aus Phase 3; das B-03-Leistungsgate
ist bestanden. Die endgültige Cutover-Freigabe hängt weiterhin von Phase 11
ab.

| Reihenfolge | Arbeit | Anforderungen |
|---|---|---|
| 4.1 | Fabrik baut für Einzelblatt und Verband denselben Laufzeitkörpertyp. | K-09, K-25 |
| 4.2 | Blatt besitzt Mesh, Massendefinition, effektive Rolle, Verdrängungsflag und Basispose; Gruppen bleiben strukturell. | K-10, K-11, K-26 |
| 4.3 | Aggregierte Masse, Schwerpunkt und Trägheit genau einmal und konsistent berechnen. | K-08, K-26 |
| 4.4 | Zustand als Teil des Laufzeitkörpers modellieren; Kompatibilität zu `Zustand6DOF` erhalten, ohne doppelten Zustand. | Zielarchitektur §3.3, K-25 |
| 4.5 | Alt-Fabriken (`baue_summenkoerper`, `baue_boot`) werden dünne Adapter auf die neue Fabrik. | K-09, K-37 |
| 4.6 | Änderungen an Masse/Material erzeugen atomaren Neuaufbau oder konsistenten Snapshot; keine Zwischenkombination alter/neuer Kennwerte. | K-08, K-25 |
| 4.7 | Jedes unterstützte Repo-Bestandsmodell gemäß Phase-3-Zuordnung verlustfrei in ein Paket migrieren; alle Paketdateien bleiben lokal/relativ, Quelldaten werden nicht überschrieben und der Migrationsbericht ordnet Quelle, Ziel und Ergebnis eindeutig zu. | K-01, K-20, K-21 |
| 4.8 | Paketloader/Fabrik bauen sämtliche migrierten Bestandsmodelle sowie parametrische Testmodelle aus dem neuen Format; Kennwerte werden gegen Alt-Fabrik und Golden-Daten verglichen. | K-01, K-09, K-20 |
| 4.9 | Für jedes Modell aus dem Phase-3-Inventar Golden-Daten im Paketpfad reproduzieren und Abweichungen innerhalb vorab festgelegter Toleranzen nachweisen; fehlende/abweichende Modelle blockieren Phase 5–8. | K-20, K-22, K-37 |

**Leistungsschutz:** Alt- und Neuobjekt nicht parallel im Regelbetrieb
vorhalten. Dual-Build nur im Test-/Vergleichsmodus; Vergleichsmodus muss
abschaltbar und in Runtime-Benchmarks ausgeschlossen sein.

**Zwischenstand:** Die Paketfabrik baut Einzelblatt und Verband als `Koerper`,
bewahrt Mesh-/Massen-/Rollenmetadaten und Manifest-Basisposen auf und
aggregiert die Masseneigenschaften einmal. Die Paketfabrik initialisiert genau
den Laufzeit-Root mit einem validierten `Zustand6DOF`; aus dem Manifest
erzeugte interne Teilobjekte haben keinen eigenen Simulationszustand. Der
dynamische Worker erhält einen unveränderlichen Zustandswert und schreibt nur
akzeptierte Ergebnisse an den Körper zurück. Manifestposen werden in Frames
umgerechnet; die Einzel- und Paket-Golden-Tests bestehen. Die Paketfabrik ist
für Repository-Modelle der Standard und über den versionierten
Settings-Schalter abschaltbar. Die Legacy-Factory bleibt als Rückfalladapter
erhalten. Der verbleibende Cutover-Nachweis (externe Migration und
vollständige GUI-/Physik-Abnahme) liegt in Phase 11.

### Phase 5 – Posen und Simulationszustand sicher einführen

**Abhängigkeit:** Phase 4.

| Arbeit | Anforderungen |
|---|---|
| Pose-Snapshots und zentrale Körper-/Teil-/Rechenframe-Umrechnung implementieren | K-05, K-14, K-27 |
| Alte Funktionssignaturen über Adapter konvertieren | K-37 |
| Initialen Körperbezugspunkt definieren und im Run konstant halten | K-14, K-16 |
| Kamerasystem nur in Renderer/GUI halten, nicht in Kraftkontext oder Körperdynamik | K-14 |
| Identitäts-, Kompositions- und Invers-Transformationstests integrieren | K-05, K-14, K-27 |

**Abnahme:** Jeder Punkt lässt sich Körper → Rechenframe → Körper ohne
Koordinaten-/Vorzeichenabweichung transformieren; Renderpose entspricht
derselben physikalischen Pose.

### Phase 6 – Einheitlichen Kraftbeitragsvertrag einführen

**Abhängigkeit:** Phase 5.

| Reihenfolge | Arbeit | Anforderungen |
|---|---|---|
| 6.1 | Wertobjekte für Einzelbeitrag und Gesamt-Wrench mit Frames/Bezugspunkten einführen. | K-12, K-27, K-28 |
| 6.2 | Bestehende Hydrostatik, Widerstände und manuelle Fremdkraft auf denselben Ergebnisvertrag abbilden, ohne neue Physik zu aktivieren. | K-13, K-29, K-37 |
| 6.3 | Schwerkraft als `F_G = m · g_vec` im benannten Simulationsframe in den gemeinsamen Beitragsweg migrieren; bei positivem `g` gilt aktuell `g_vec=(0,0,-g)`. Integratoraddition im selben Änderungsschritt entfernen. | K-30 |
| 6.4 | Aggregator transformiert Beiträge genau einmal auf den vereinbarten Schwerpunkt und bewahrt Diagnosebeiträge. | K-28, K-29, K-36 |
| 6.5 | Bestehende öffentliche APIs als Adapter erhalten; noch keine Simulationsalgorithmen oder Kraftparameter ändern. | K-13, K-30, K-37 |

**Abnahme:** Bestehende Kraft-/Momentenwerte, Gleichgewichte, Netto-
Beschleunigungen und Trajektorien bleiben innerhalb vorab eingefrorener
Baseline-Toleranzen; Gewicht wird genau einmal berücksichtigt. Die noch
unmigrierten Solver-/Integratoraufrufe werden über Adapter bedient.

### Phase 7 – Statische Simulation auf Körper-Snapshot umstellen

**Abhängigkeit:** Phase 5 und 6.

**Migrationsgate:** Alle unterstützten Bestandsmodelle müssen bereits in Phase
3 inventarisiert, in Phase 4 paketiert und mit Golden-Daten verglichen sein.
Fehlt ein Modell oder besteht eine Abweichung, beginnen die Solverumbauten
nicht.

| Arbeit | Anforderungen |
|---|---|
| Solver erhält unveränderlichen Modell-/Körper- und Umgebungssnapshot | K-25, K-33, K-35 |
| Jede Kandidatenlage wird als Eingabe an die Kraftauswertung übergeben; aktive Körperpose bleibt unangetastet | Zielarchitektur §3.2 |
| Residuum, Status, Näherung/Stagnation und Diagnose bleiben kompatibel | G1/G3 |
| Nur akzeptierte Lösung wird atomar in `Koerper.zustand` übernommen; bei Fehler/Abbruch bleiben letzte akzeptierte Pose und Ergebnis erhalten | K-35, K-36 |
| Statischer Kraftpfeil/Status aus dem akzeptierten Ergebnis darstellen; Solverfehlerstatus klar von „Kandidat nicht übernommen“ unterscheiden | K-36 |

**Leistungsschutz:** vorhandenes Voxel-/Tetraederverfahren und
Hydrostatikcache nicht ersetzen, bis ein gleichwertiger Benchmark und
Referenztest vorliegen.

### Phase 8 – Dynamischen Schritt auf denselben Laufzeitkörper umstellen

**Abhängigkeit:** Phase 6 und 7.

| Arbeit | Anforderungen |
|---|---|
| Engine liest Körperzustand und aggregierte Anfangs-Massenwerte | Spec §5, K-25, K-26 |
| Kraftauswertung liefert ein Ergebnis, der Integrator liefert neuen Zustand; Ergebnis wird nach Validierung atomar übernommen | K-35, K-36 |
| Laufzeitkörper ist autoritative Quelle des zuletzt freigegebenen Zustands; Worker erhalten versionierte unveränderliche Snapshots und liefern Ergebnisse mit Auftragsgeneration zurück | K-23, K-25, K-35 |
| Zeit, Position, Orientierung, Geschwindigkeit und Winkelgeschwindigkeit werden deterministisch fortgeschrieben | bestehende Dynamikparität |
| Worker liefert unveränderliche Resultate mit Generation; GUI verwirft veraltete Generationen | K-35 |

**Leistungsschutz:** Zeitschritt-Hot-Path profilieren. Keine JSON-Arbeit,
Meshkonvertierung, Dateisystemzugriffe, GUI-Objekterzeugung oder
unveränderte Tensorneuberechnung pro Schritt.

### Phase 9 – Settings, GUI-Baum und gemeinsame Darstellung

**Abhängigkeit:** Phase 4 und Ergebnisverträge aus Phase 6–8.

| Arbeit | Anforderungen |
|---|---|
| Bestehendes versioniertes Settingsformat additiv erweitern, Vorlage und Migration aktualisieren | K-18 |
| GUI-Baum aus Manifest-IDs/Struktur speisen; Sichtbarkeit/Aktivierung/Rolle getrennt halten | K-19 |
| Renderer liest Körperzustand und Simulationsergebnis für statisch/dynamisch | K-14, K-36 |
| Kamera relativ zum Körper bewegen; sicherstellen, dass Kamera keine Physik invalidiert oder verändert | K-14 |
| Worker/GUI mit Snapshots, Generationen und verständlicher Fehlerweitergabe koppeln; es existiert nur ein autoritativer freigegebener Zustand | K-23, K-35 |
| Bestehende Dialoge/Bedienelemente erhalten; Anzeigeoptionen nur renderer-seitig anwenden | K-18, K-36 |

**Fortschritt:** Settings-Schema 1.2 enthält den additiven Schalter
`modell.paketfabrik_aktiv` (Default `true`); Vorlage, eingebaute
Rückfallebene, gespeicherte Repository-Einstellungen und Settings-Handbuch
sind synchronisiert. Der GUI-Baum wird aus Manifest-IDs aufgebaut; aktive
Auswahl, Rolle, Label und Verdrängungsflag bleiben getrennt. Die Kamera folgt
dem Körper ohne Physikzustandsänderung. Renderer-, Worker- und
Snapshot-Generationen sind in den bestehenden Abläufen integriert. Ein
Regressionstest deckt den Umschalt-Callback ab. Gezielte GUI-/Settings-Tests
und die vollständige Testsuite bestehen (zuletzt **563 passed, 1 skipped**).

### Phase 10 – Bewegliche Teile gemäß Ein-Körper-Näherung

**Abhängigkeit:** Posen, Laufzeitkörper, Kraftbeiträge und Renderer sind stabil.

| Arbeit | Anforderungen |
|---|---|
| Gelenkdefinition, Eltern-ID, Achse, Winkel und initiale Pose an Manifest/Laufzeitkörper anbinden | K-14, K-15 |
| Initiale Teilmassen genau einmal aggregieren; Gesamtmasse, Schwerpunkt, Trägheit und Bezugspunkt danach einfrieren | K-16, K-38 |
| Aktuelle Gelenkpose in Darstellung sowie Hydro-/Aerodynamik verwenden | K-15, K-38 |
| Auftriebsberechnung für bewegliche Geometrie auf initiale Teilpose festlegen; Gesamtkörperpose weiter auswerten | K-17, K-31, K-38 |
| Winkeländerungen dürfen Massenkennwerte/Schwerpunkt/Auftrieb aus Teilbewegung nicht ändern | K-15–K-17, K-38 |
| Konfiguration explizit als Ein-Körper-Näherung diagnostizierbar machen; keine Behauptung vollständiger Mehrkörperdynamik | K-16, K-38 |

Diese Phase wird nicht vorgezogen: Ohne gemeinsame Pose-/Frame-/Ergebnisverträge
würde Gelenklogik mehrfach in Renderer und Physik entstehen.

**Fortschritt/Abgrenzung:** Manifestvalidierung, Elternframe-Achse,
Gelenkwinkel im Körperzustand/Snapshot sowie die aktuelle Renderpose sind
implementiert und getestet. Winkeländerungen invalidieren die Körpergeneration,
lassen aber aggregierte Masse, Schwerpunkt, Trägheit und das für den Auftrieb
verwendete Anfangsmesh unverändert. Noch offen ist die Verwendung der
Gelenkpose in Hydro-/Aerodynamikbeiträgen; diese hängt von den fachlichen
Kraftmodellen aus Phase 12 ab. Vollständige Mehrkörperdynamik bleibt gemäß
Backlog B-18 ausdrücklich außerhalb dieses Umbaus.

### Phase 11 – Produktionsumschaltung und Altpfade kontrolliert entfernen

**Abhängigkeit:** Phasen 2–10; vollständiger Paket- und Golden-Daten-Nachweis
aus Phase 3/4 sowie grüne Paritäts- und Performancegates.

| Arbeit | Anforderungen |
|---|---|
| Vollständigkeit des Phase-3-Inventars und der Phase-4-Paketmigration erneut prüfen; Quellen bleiben gesichert | K-20 |
| Einmaliges Migrationswerkzeug für noch nicht paketierte externe Nutzerbestände mit Dry-run, Validierungsbericht und Nichtüberschreiben bauen; Repo-Bestandsmodelle sind bereits migriert. | K-20, K-21 |
| Bestehende Repo-Pakete unverändert gegen Golden-Daten und Nutzerabläufe prüfen; keine erneute Repo-Modellmigration in dieser Phase beginnen. | K-20 |
| Anwendung zunächst per explizitem Feature-Schalter paketbasiert starten; kein stiller Mischpfad | K-01, K-09, K-20 |
| Neue und alte Pfade auf Bestandsdaten vergleichen; Unterschied muss null oder dokumentierte numerische Toleranz sein | K-20, G3 |
| Umschaltung nach erfolgreicher GUI-/Import-/Physik-/Performanceabnahme | K-20, K-22 |
| Alte Loader/Adapter erst nach Suche aller Aufrufer, voller Suite und Rückfallplan entfernen | K-37 |

**Fortschritt:** Der explizite Settings-Schalter und die beiden Fabrikpfade
sind vorhanden; ein GUI-Regressionstest deckt das Umschalten ab. B-03 ist
bestanden und die vollständige Testsuite ist grün (**563 passed, 1 skipped**).
Phase 11 ist dennoch
**nicht abgenommen**: Das Dry-run-first-Migrationswerkzeug
[`migriere_modellpaket.py`](../../../../werkzeuge/migriere_modellpaket.py)
validiert Pakete und verweigert existierende Zielpakete; Tests decken
Dry-run ohne Zieldateien, erfolgreiche Ausgabe, fehlerhafte Geometrie und
Nichtüberschreiben ab
([`test_migriere_modellpaket.py`](../../../../tests/test_migriere_modellpaket.py)).
Ein vollständiger Alt-/Neu-Vergleich mit realen
externen Nutzerbeständen, die GUI-Integration externer Pakete sowie die
formelle G1–G4-Cutover-Abnahme fehlen weiterhin. Bis dahin bleiben
Legacy-Adapter und Rückfallpfad erhalten.

### Phase 12 – Hydrodynamik und Aerodynamik

**Abhängigkeit:** Phase 8; für Gelenkkräfte zusätzlich Phase 10.

Navigation (Kompasskurs, Abdrift, KdW/KüG und nautisches Weltsystem) liegt
außerhalb dieses Plans und erfordert eine eigene freizugebende Spezifikation.

| Arbeit | Anforderungen |
|---|---|
| Rollenregistry und passive/nicht implementierte Rollen diagnostisch abschließen | K-10, K-32 |
| Wasser-/Luftzustand als explizite Snapshots weiterreichen | K-33 |
| Hydrodynamik und Aerodynamik als getrennte Behandlungen integrieren | K-12, K-32, K-33 |
| Empirische/analytische Kraftreferenzen, Einheiten- und Vorzeichentests erstellen | K-12, K-33 |
| Kraftpfeile und Diagnose aus Einzelbeiträgen speisen | K-36 |

**Leistungsschutz:** Kräfte pro Zeitschritt ohne Meshneuberechnung; stabile
geometrische Kennwerte vorbereiten; Cache nur mit vollständigen Abhängigkeiten.

**Status:** Auf Nutzerwunsch vertagt; kein unvalidiertes Kraftmodell wird
implementiert. Der noch offene fachliche Eingabebedarf ist in Backlog B-21
festgehalten.

**Blocker:** Die Spezifikation schließt empirisch nicht abgesicherte
Rumpf-/Kiel-/Ruder-/Segelkräfte ausdrücklich aus und enthält keine
freigegebenen Wind-/Strömungszustände, Kraftkoeffizienten oder
Referenzmessungen. Deshalb wird Phase 12 nicht mit erfundenen Parametern
implementiert. Zunächst ist die fachliche Festlegung aus Backlog B-21 nötig;
bis dahin bleiben bestehende Hydrostatik und klar gekennzeichnete, bereits
validierte Kraftbeiträge unverändert.

## 6. Testfallkatalog

Die Fälle sind kumulativ: Bestehende Tests bleiben erhalten; neue Fälle
ergänzen sie. Die Testnamen sind Vorschläge, Tests können nach Repo-Konvention
gruppiert werden.

### 6.1 Vertrags-, Import- und Meshfälle

| ID | Testfall / Eingabe | Erwartung | Zuordnung |
|---|---|---|---|
| T-001 | Paket mit gültigem versioniertem Manifest und eindeutigen IDs laden | Deterministischer Modellbaum und identische IDs/Labels | K-01, K-02, K-03 |
| T-002 | Fehlende Schema-Version, unbekannte Major-Version, doppelte/ungültige ID | Expliziter Fehler mit Paketpfad/ID; kein Fallbackmodell | K-02, K-21 |
| T-003 | Gruppe mit Masse, leere Gruppe, Knoten mit Gruppe und Geometrie zugleich | Jeweils gezielter Validierungsfehler mit Knotenpfad | K-03 |
| T-004 | Paket laden, während CWD außerhalb des Repositorys liegt | Gleiches Modell wird über explizite Paketwurzel geladen | K-01 |
| T-005 | Relative gültige Geometriedatei sowie fehlende Datei | Gültiger Fall lädt; fehlende Datei nennt relativen Pfad | K-01, K-06, K-21 |
| T-006 | Absoluter Pfad, `..`, Symlink/aufgelöster Pfad außerhalb Paket | Abweisung vor Dateiinhalt-Import | K-06 |
| T-007 | OBJ positive Indizes, negative Indizes, optionale vt/vn-Felder | Gleiche kanonische Geometrie/Orientierung nach Normalisierung | K-06 |
| T-008 | Konvex planar, konkav planar, nicht-planar und entartetes Polygon | Konvex und konkav planar werden robust trianguliert; nicht-planare und entartete Polygone werden mit eindeutigem Grund abgelehnt | K-06, K-07 |
| T-009 | Geschlossenes korrekt orientiertes Mesh mit Volumenmasse | Mesh- und Volumenvalidierung erfolgreich | K-07 |
| T-010 | Offene Schale mit Flächenmasse / offene Schale mit Volumenmasse | Erster Fall erfolgreich, zweiter mit fachlichem Fehler abgelehnt | K-07, K-08 |
| T-011 | Mesh mit Loch, Selbstüberschneidung oder Nullflächen-Dreieck | Kein stilles Reparieren; Fehler identifiziert betroffenen Knoten | K-07 |
| T-012 | Negativ orientiertes, ansonsten korrektes geschlossenes Mesh | Globale Orientierung wird durch konsistentes Umkehren normalisiert; Volumen und Kennwerte stimmen mit der positiv orientierten Referenz überein | K-07 |
| T-013 | Formparameter in Metern plus OBJ-Scale | OBJ wird skaliert, Formparameter nicht doppelt skaliert | K-04, K-05 |
| T-014 | Unity-Y-up und Z-up OBJ mit bekannten Punkten | Beide ergeben identische kanonische Körpersystempunkte und Volumen | K-05, K-27 |
| T-015 | Geometriequelle unbekannt | Sichtbarer Ladefehler; kein Ersatzkörper | K-04, K-21 |
| T-016 | Material-ID unbekannt oder Material plus widersprüchliche direkte Massendaten | Sichtbarer Validierungsfehler | K-08 |
| T-017 | Rolle geerbt von Gruppe und am Blatt überschrieben | Je Blatt genau die richtige effektive Rolle | K-10 |
| T-018 | Umbenennen eines Knotens bei stabiler ID | Settings/GUI-Auswahl referenzieren denselben Knoten | K-02, K-19 |
| T-019 | Geometrisch kugelförmiges Mesh mit Rolle `rumpf` und umbenannte OBJ-Datei | Geometrieanalyse und Physikrolle bleiben unabhängig | K-11 |
| T-020 | Dasselbe immutable Mesh an Renderer und Physik übergeben | Keine unerwartete Mutation; Punkte und Faces bleiben identisch | K-27 |

### 6.2 Körper-, Masse- und Posefälle

| ID | Testfall / Eingabe | Erwartung | Zuordnung |
|---|---|---|---|
| T-021 | Ein Einzelblatt über neue Fabrik bauen | Derselbe Laufzeitkörpertyp/Vertrag wie beim Verband | K-09, K-25 |
| T-022 | Mehrteiliger Körper mit bekannten analytischen Massen | Gesamtmasse, Schwerpunkt und Trägheit entsprechen Handrechnung/Parallelachsen-Theorem | K-08, K-26 |
| T-023 | Dichte/Material/Wanddicke ändern | Neue Instanz/Snapshot ist vollständig konsistent; kein Mischzustand | K-08, K-25 |
| T-024 | Verschachtelte Rotation und Translation zweier Teilknoten | Weltpunkte, Angriffspunkt, Schwerpunkt und Rendererpose stimmen; Quellursprung und jeder Montageversatz bleiben erhalten | K-05, K-14, K-27 |
| T-025 | Körper → Rechenframe → Körper Transformation | Position und Vektoren werden innerhalb Toleranz rücktransformiert; Rotation bleibt rechtshändig | K-05, K-27 |
| T-026 | Kamera um Körper bewegen, gleiche Simulationsinputs | Körperzustand, Solverresultat und Kraftbeiträge bleiben identisch | K-14 |
| T-027 | Zustand gehört genau einmal zum Laufzeitkörper | Worker/GUI halten keinen abweichenden Zustand; nächster Schritt liest den zuletzt freigegebenen Zustand | Zielarchitektur §3.3, K-25, K-35 |
| T-028 | Fehlerhafte neue Körperwerte bei atomarem Update | Voriger gültiger Zustand bleibt ganz erhalten; Fehler wird gemeldet | K-25, K-35 |

### 6.3 Simulation, Kraft- und Darstellungskonsistenz

| ID | Testfall / Eingabe | Erwartung | Zuordnung |
|---|---|---|---|
| T-029 | Statischer Solver prüft mehrere Kandidaten | Aktiver Körperzustand bleibt bis Solverabschluss unverändert | Statischer Ablauf, K-25, K-35 |
| T-030 | Statischer Solver findet akzeptierte Pose | Genau diese Pose wird atomar übernommen und dargestellt | Statischer Ablauf, K-35, K-36 |
| T-031 | Statischer Solver scheitert/abgebrochen | Letzte akzeptierte Pose und Ergebnis bleiben aktiv; Fehlerstatus/Diagnose sichtbar, Kandidat überschreibt aktive Pose nicht | K-35 |
| T-032 | Dynamischer Schritt bei Nullresultierender Kraft/Moment | Zustand bleibt gemäß bisherigem Verhalten stationär | Dynamikparität |
| T-033 | Körper mit Masse, positiver Fallbeschleunigung `g` und anfänglicher Ruhe im festgelegten Simulationsframe frei fallen lassen | Nach einem und mehreren Schritten gilt `a = g_vec = (0,0,-g)` im benannten Frame; Gewicht wird genau einmal addiert und die Pose-/Frameorientierung führt nicht zu Vorzeichenwechseln | K-30 |
| T-034 | Gleichgewicht aus Auftrieb und Gewicht | Vertikale Resultierende innerhalb Referenztoleranz null | K-30, K-31 |
| T-035 | Kraft an verschobenem Angriffspunkt gegen äquivalentes freies Moment | Identische Wrench nach Bezugspunktumrechnung | K-28, K-29 |
| T-036 | Mehrere Kraftbeiträge in Teilframes | Transformierte Einzelbeiträge summieren exakt zur Wrench | K-12, K-27, K-29 |
| T-037 | Disjunkte verdrängende Meshes und überlappende Meshes | Union wird berechnet; Überlappung wird nicht doppelt gezählt | K-31 |
| T-038 | Nicht verdrängendes Blatt unter Wasser / Segel über Wasser | Nur als verdrängend definierte Volumina tragen Auftrieb bei | K-31 |
| T-039 | Manuelle Fremdkraft-Alt-API plus neue Beiträge | Altaufruf funktioniert; kein Überschreiben/neue doppelte Addition | K-13, K-37 |
| T-040 | Kraftpfeil ein-/ausblenden | Physikresultat und Trajektorie bleiben bitgleich bzw. innerhalb deterministischer Toleranz | K-36 |
| T-041 | Einzelbeiträge visualisieren | Ihre Wrench-Summe entspricht dem Integrationsergebnis | K-36 |
| T-042 | Widerstands-/Fluidgeschwindigkeit ändern | Beiträge werden mit aktuellem Umgebungssnapshot neu berechnet | K-33 |
| T-043 | Unbekannte/aktive Rolle ohne Handler | Fehler oder explizite Passivdiagnose; nie Erfolg vortäuschen | K-10, K-32 |
| T-044 | Wiederholte gleiche dynamische Simulation | Deterministische Trajektorie wie Baseline | Dynamikparität |
| T-045 | Historische Tests für Kugelneutralität, Instabilität und Stagnation | Solverstatus und stabile/rollneutrale Einordnung bleiben erhalten | Dynamik-/Solverparität |

### 6.4 Gelenk-Näherung

| ID | Testfall / Eingabe | Erwartung | Zuordnung |
|---|---|---|---|
| T-046 | Starrkörper mit beweglichem Teil, Startwinkel 0 | Masse, Schwerpunkt und Trägheit werden aus der initialen Lage aggregiert | K-16, K-38 |
| T-047 | Gelenkwinkel während Simulation ändern | Aktuelle Teilpose und Hydro-/Aerodynamik ändern sich wie vorgesehen | K-15, K-38 |
| T-048 | Vorher/nachher Gelenkwinkel vergleichen | Gesamtmasse, festgelegter Schwerpunkt, Körperbezugspunkt und Trägheit bleiben unverändert | K-16, K-38 |
| T-049 | Bewegliches verdrängendes Teil winkelverstellen | Auftriebsgeometrie bleibt initial; Gelenkwinkel allein ändert Auftrieb nicht | K-17, K-38 |
| T-050 | Gesamtkörper relativ zur Wasserlinie bewegen, Gelenkwinkel fest | Hydrostatik wird neu berechnet und ändert sich entsprechend der Pose | K-17, K-34 |
| T-051 | Teilpose im Renderer gegen Teilpose in Hydro-/Aerodynamik | Identische aktuelle Gelenktransformation; keine separate optische Drehachse | K-14, K-15 |
| T-052 | Mehrere Gelenke in verschachtelter Struktur | Lokale Achsen/Posen werden korrekt über Eltern transformiert; keine Masse-Neuaggregation | K-14, K-16 |

### 6.5 Settings, GUI, Migration und Kompatibilität

| ID | Testfall / Eingabe | Erwartung | Zuordnung |
|---|---|---|---|
| T-053 | Alte Settingsdatei laden | Alte Nutzerwerte bleiben erhalten und Datei wird korrekt versioniert migriert | K-18 |
| T-054 | Unbekannte Settingsfelder und ungültige Modell-ID | Unbekannte Felder bleiben; ungültige ID wird sichtbar gemeldet | K-18 |
| T-055 | GUI-Baum: Gruppe/Blatt aktivieren und deaktivieren | Sichtbarkeit, Aktivierung, Rolle und Modell-ID bleiben unterscheidbar; Masse/Kräfte folgen Aktivierungsregel | K-19 |
| T-056 | GUI: Masseänderung | Masse, Schwerpunkt, Trägheit, statische Simulation und Darstellung aktualisieren konsistent | K-08, K-25 |
| T-057 | GUI: Kamera ändern | Ansicht ändert sich, Physik nicht | K-14 |
| T-058 | Worker liefert verzögert älteres Ergebnis | Ergebnisgeneration wird verworfen; neuerer Zustand bleibt sichtbar | K-35 |
| T-059 | Hauptfenster während Solver-/Dynamikarbeit bedienen | GUI bleibt reaktionsfähig; keine Worker-Widget-Manipulation | K-23, K-35 |
| T-060 | Migrationswerkzeug Dry-run | Bericht zeigt geplante Änderungen, schreibt/überschreibt keine Quelle | K-20 |
| T-061 | Reale Altmodelle migrieren | Alle Zielpakete validieren; Masse/Schwerpunkt/Trägheit/Volumen/Ergebnisse matchen Golden-Daten | K-20 |
| T-062 | Migration zweimal auf demselben Ziel ausführen | Kein Duplikat/Überschreiben; verständlicher idempotenter Status oder Abbruch | K-20 |
| T-063 | Adapter- und Aufrufersuche vor Abschaltung | Kein produktiver Altaufrufer bleibt unberücksichtigt; vorhandene Demo/Suite laufen | K-37 |
| T-064 | Beispielmanifest-/Dokumentationsprüfung in CI | Schema, referenzierte Dateien und interne Links sind valide | K-22 |
| T-065 | Automatisierte Architekturgrenze: `core` importiert kein Qt/Renderer | Schichten bleiben technisch entkoppelt; der Check läuft reproduzierbar in CI | K-23 |
| T-066 | OBJ mit bekannter nichttrivialer Achsenabbildung/Skalierung, Quellursprung, zwei verschachtelten Teilen, lokaler Rotation und nicht-null Translationen sowie bekannten Blatt- und Gesamt-CG importieren | `p_Blatt=A_OBJ→Blatt(s·p_OBJ)` und `p_K=R_Eltern·(R_Blatt·(p_Blatt−c_Blatt)+t_Blatt+R_Blatt·c_Blatt)+t_Eltern−c_Gesamt` werden in dokumentierten Frames numerisch gegen handgerechnete Referenzpunkte geprüft; Achsenabbildung und Zentrierung erfolgen genau einmal, Renderer und Physik liefern dieselben Punkte/Angriffspunkte | K-05, K-14, K-27 |
| T-067 | Wasser-/Luftdichte, Wind-/Fluidgeschwindigkeit und Schwerebeschleunigung einzeln verändern | Nur betroffene Beiträge werden mit dem neuen Umgebungssnapshot neu berechnet; erwartete Änderung stimmt mit Referenz/analytischem Fall überein | K-30, K-33 |
| T-068 | Cache nach Änderung von Pose, Wasserreferenz/-zustand, Geometrie und relevanten Parametern erneut abfragen | Jeder Cachetreffer entspricht einer exakten Neuberechnung; geänderte Abhängigkeit ergibt keinen veralteten Treffer | K-17, K-34 |
| T-069 | Nach akzeptierter statischer Lösung einen Solverfehler, Abbruch und nicht konvergierte Kandidaten zustellen | Bisherige Pose, Ergebnis und zugehörige Arbeitsdaten bleiben aktiv; Kandidat wird als nicht übernommen gekennzeichnet; nur Diagnose/Fehlerstatus aktualisiert sich | K-35, K-36 |
| T-070 | Architekturreview anhand einer festen Verantwortlichkeits-Checkliste durchführen | Jede Klasse hat begründeten Zustand oder Strategievertrag; zustandslose Logik bleibt Funktion; Befunde sind dokumentiert | K-23, K-24 |
| T-071 | Intervallcache ausdrücklich aktivieren und mit exakter Neuberechnung für gleiche sowie wechselnde Posen vergleichen | Approximation ist niemals als exakter Treffer ausgewiesen; Kraft-, Moment- und Trajektorienabweichungen werden reproduzierbar gemessen und bleiben innerhalb des vor Freigabe festgelegten Fehlerbudgets; ohne freigegebenes Fehlerbudget bleibt der Modus nicht produktiv freigebbar | K-17, K-34 |

### 6.6 Performancefälle

| ID | Messfall | Vergleich / Abnahme |
|---|---|---|
| P-001 | Modellkatalog anzeigen ohne Geometrien zu parsen | Gegen B-10; keine Meshallokation |
| P-002 | Kalt-/Warm-Laden von kleinem Körper | Beide getrennt gegen B-02; Cache darf Kaltpfad nicht verschlechtern |
| P-003 | Yacht-OBJ-Import und Fabrikaufbau | Gegen B-03; keine doppelte OBJ-Parse-/Transformationsrunde |
| P-004 | Meshvalidierung + Masseneigenschaften | Gegen B-11; Validierung nur einmal je unverändertem Mesh |
| P-005 | Statischer Solve derselben Starts/Parameter | Gegen B-05; Iterationen und Anzahl Kraftauswertungen mitprotokollieren |
| P-006 | Exakte Hydrostatik je Pose und Cachehit/-miss | Gegen B-04; Cachehit nur bei identischer Pose und vollständigen Abhängigkeiten; Ergebnis immer gegen exakte Neuberechnung prüfen |
| P-007 | Dynamischer Hot-Path mit Kraftmodell | Gegen B-06; keine Objekt-/Mesh-/Dateisystemarbeit pro Schritt |
| P-008 | Echtzeitbatch und Rückstand | Gegen B-07; keine schlechtere Schrittzahl oder sichtbare Latenz |
| P-009 | Renderer mit identischer Szene/Overlays | Gegen B-08; Kamera-/Status-/Pfeiländerungen getrennt messen |
| P-010 | GUI-Masseänderung bis sichtbare konsistente Szene | Gegen B-09; keine alte und neue vollständige Modellkopie dauerhaft parallel |
| P-011 | Memory-Profil für Modellladen und Laufzeit | Gegen B-02/B-03/B-08; immutable Meshsharing, keine unbeschränkte Resultathistorie |
| P-012 | Gesamter Kurzlauf statisch + dynamisch + GUI | Gegen B-01 und B-05 bis B-09; gleiche Abläufe, Kennzahlen einzeln statt aggregiert vergleichen |

## 7. Anforderung-zu-Phase-zu-Test-Matrix

| Spec-ID | Primärphase(n) | Abnahmetests |
|---|---|---|
| K-01 | 1, 3, 4, 11 | T-001, T-004, T-005, T-061 |
| K-02 | 1, 3 | T-001, T-002, T-018 |
| K-03 | 1, 3 | T-003 |
| K-04 | 2, 3 | T-013, T-015 |
| K-05 | 1, 2, 5 | T-013, T-014, T-024, T-025, T-066 |
| K-06 | 2, 3 | T-005–T-008 |
| K-07 | 2 | T-008–T-012 |
| K-08 | 1, 4 | T-016, T-022, T-023, T-056 |
| K-09 | 4, 11 | T-021, T-061, T-063 |
| K-10 | 3, 4, 12 | T-017, T-043 |
| K-11 | 3, 4 | T-019 |
| K-12 | 6, 12 | T-035–T-037, T-042 |
| K-13 | 6 | T-039 |
| K-14 | 5, 9, 10 | T-024, T-026, T-051, T-052, T-066 |
| K-15 | 10 | T-047, T-049, T-051 |
| K-16 | 4, 10 | T-022, T-046, T-048, T-052 |
| K-17 | 6, 10 | T-049, T-050, T-068, T-071 |
| K-18 | 1, 9 | T-053, T-054 |
| K-19 | 9 | T-018, T-055 |
| K-20 | 3, 4, 11 | T-060–T-062 |
| K-21 | 1, 3, 11 | T-002, T-005, T-015, T-060 |
| K-22 | 3, 11 | T-064 |
| K-23 | 1, 8, 9 | T-059, T-065, T-070 |
| K-24 | 1, fortlaufend | T-070 |
| K-25 | 1, 4, 5, 7, 8 | T-027–T-031, T-056, T-058, T-069 |
| K-26 | 4 | T-022, T-046 |
| K-27 | 2, 5, 6 | T-014, T-020, T-025, T-036, T-066 |
| K-28 | 6 | T-035, T-036 |
| K-29 | 6 | T-034–T-037 |
| K-30 | 6, 12 | T-033, T-034, T-067 |
| K-31 | 6, 10 | T-034, T-037, T-038, T-049, T-050 |
| K-32 | 3, 6, 12 | T-043 |
| K-33 | 7, 8, 12 | T-042, T-067 |
| K-34 | 2, 6, 10 | T-050, T-068, T-071, P-006 |
| K-35 | 7, 8, 9 | T-027–T-031, T-058, T-059, T-069 |
| K-36 | 7–9 | T-030, T-040, T-041, T-069 |
| K-37 | 4, 6, 11 | T-039, T-063 |
| K-38 | 10 | T-046–T-052 |

## 8. Bestehende Tests und ergänzende Testorganisation

Die vorhandenen Testmodule bleiben maßgebliche Regressionen; sie werden nicht
ersetzt, nur weil eine neue Architektur hinzukommt. Besonders relevante
Gruppen im aktuellen Repository:

| Bereich | Bestehende Tests (Auswahl) |
|---|---|
| Körper/Fabrik/Masse | `test_koerper.py`, `test_massenaenderung.py`, `test_active_body_factory.py`, `test_mesh_validierung.py`, `test_farben_komposition.py` |
| Modell-/GUI-Baum und Settings | `test_baum_regeln.py`, `test_gui_baum_json.py`, `test_gui_baum_widget.py`, `test_einstellungen.py`, `test_gui_laufzeit_edit.py` |
| Auftrieb/Hydrostatik/Volumenunion | `test_auftrieb.py`, `test_hydrostatik.py`, `test_volumen_union.py`, `test_wasser_schnitt.py`, `test_voxelmodell.py` |
| Solverstatus | `test_statisch.py`, `test_statisch_robust.py`, `test_statisch_kugel.py` |
| Dynamik/Echtzeit | `test_dynamik.py`, `test_dynamik_6dof.py`, `test_echtzeit_prozess.py`, `test_sim_modus.py`, `test_bewegung_und_formen.py` |
| Rendering/GUI/Overlays | `test_grafik_bruecke_darstellung.py`, `test_grafik_optimierung.py`, `test_statische_darstellung.py`, `test_overlays.py`, `test_vista_ui.py`, `test_statusanzeige.py` |
| Architekturgrenzen | `test_keine_physik_imports.py`, `test_demo_importierbar.py`, `test_konfig_schema.py` |

Pro Commit: kleinste betroffene Testgruppe. Vor jedem Phasen-Gate: vollständige
Testsuite, dokumentierte Start-/GUI-Smoke-Tests und betroffene Benchmarks.
Testdaten mit echten Dateien und erwarteten Kennwerten werden versioniert;
temporäre Benchmarkausgaben bleiben außerhalb des Produktivdatenpakets, sofern
sie nicht als Freigabeartefakt ausgewiesen sind.

## 9. Rückfall-, Umschalt- und Fehlerstrategie

- Neue Paketverarbeitung zunächst hinter einem expliziten Entwicklungs- oder
  Feature-Schalter testen; bestehender Standardpfad bleibt unverändert, bis
  Freigabegates bestanden sind.
- Bei Abweichung: Eingabe, neue/alte Kennwerte, Kraftbeiträge, Koordinatenrahmen,
  Cachezustand und Laufzeitbenchmark protokollieren.
- Keine automatische Umschaltung auf einen anderen Körper oder einen stillen
  alten/neuen Mischpfad im Fehlerfall.
- Rückfall erfolgt durch deaktivieren des neuen Pfads bzw. Revert des
  abgegrenzten Commits, nicht durch Verlust/Migration der Quelldaten.
- Altpfade werden erst entfernt, wenn sämtliche realen Modellpakete migriert,
  alle Aufrufer gefunden und alle G1–G4-Gates bestanden sind.

## 10. Abschlusskriterien

Spec v0.5 gilt technisch umgesetzt, wenn:

1. K-01 bis K-38 in der Rückverfolgbarkeitsmatrix einem Implementierungsabschnitt
   und mindestens einem Test zugeordnet sind;
2. alle Bestandsmodelle und Bedienabläufe erhalten sind oder ihre
   verlustfreie Migration nachgewiesen ist;
3. statische und dynamische Pfade denselben Laufzeitkörper und Kraftvertrag
   verwenden, ohne ihre unterschiedlichen Algorithmen zu vermischen;
4. Zustands-, Kraft-, Momenten- und Darstellungsergebnisse den jeweiligen
   Verträgen entsprechen;
5. vollständige Testsuite und GUI-Smoke-Tests grün sind;
6. B-01 bis B-11 und P-001 bis P-012 keine signifikante Performance- oder
   RAM-Regression zeigen;
7. alle Adapter, die noch gebraucht werden, dokumentiert sind; alle entfernten
   Altpfade nachweislich keinen Aufrufer mehr besitzen.
