# SegelPhysik – Umsetzungsplan vF1

Dieser Plan beschreibt die Umsetzung und Prüfung der
[Spezifikation v1.1](./Spezifikation_v1.1.md). Er ist nach technischen
Abhängigkeiten geordnet und ersetzt keine Anforderungen der Spezifikation.
Die vorhandene GUI-Darstellung und Bedienung bleibt 1:1 erhalten; einzig der
für erkannte Bauteilüberschneidungen erforderliche Auswahldialog ist neu
zulässig.

## 1. Arbeitsregeln und Abnahmeprinzip

- Vor jeder Phase werden Arbeitsbaum, Python-Version, Abhängigkeiten und
  Testergebnis festgehalten. Die vorhandenen Nutzerdaten und Modellquellen
  werden nicht durch Testläufe verändert.
- Zuerst werden die vorhandenen Implementierungen und Tests genutzt bzw.
  erweitert. Neue Abhängigkeiten und neue Modulgrenzen werden nur eingeführt,
  wenn ein konkreter Bedarf nachgewiesen ist.
- Jede Phase endet mit den unten genannten gezielten Tests und einer
  GUI-Regression. Fehler und Abweichungen werden vor dem Beginn der nächsten
  abhängigen Phase behoben oder ausdrücklich als blockierend dokumentiert.
- Physiktests verwenden SI-Einheiten und analytische oder exakte
  Referenzgeometrien. Zufällige Toleranzvergrößerungen, stilles Überspringen
  fehlerhafter Körper und Erfolgsmeldungen bei nicht konvergierter Rechnung
  sind nicht zulässig.
- Bestehende GUI-Steuerelemente, Beschriftungen, Docks, Farben, Anordnung,
  Kamera, Layer, Baumverhalten und Simulationsmodi werden nicht umgestaltet.
  Längere Berechnungen dürfen die GUI-Ereignisschleife nicht blockieren.
- Vorhandene Statusflächen und das Protokoll melden Rechenpfad, Fehler,
  Solverstatus und Wartezustand nachvollziehbar. Eine Fehlerbehandlung darf
  keinen erfolgreichen Zustand vortäuschen.
- Die Richtwerte von 100 ms Eingabereaktion und 30 Bildern/s werden bei
  repräsentativer Last gemessen und berichtet. Sie werden nicht als harte
  Einzelaufruf-Laufzeitgrenzen missverstanden; maßgeblich bleibt die
  flüssige, bedienbare Anwendung.
- Quellmodellkorrekturen erfolgen nur nach Erkennung des Konflikts und
  ausdrücklicher Auswahl des unangetasteten Vorrangkörpers. Die
  Ausgangsquelle wird vorher gesichert und bei jedem Fehler wiederhergestellt.
- Kein Commit und kein Push ohne ausdrückliche Beauftragung.

## 2. Phasenübersicht und Abhängigkeiten

| Phase | Ergebnis | Abhängigkeit |
|---|---|---|
| 0 | Reproduzierbare Ausgangsmessung und abgesicherte Testbasis | keine |
| 1 | Gültige Mesh-, Masse- und Trägheitsdaten | Phase 0 |
| 2 | GPU-Backend-Kompatibilität und reproduzierbarer Vergleichsprototyp | Phase 0 |
| 3 | Erkennung und dauerhaft-transaktionale Konfliktkorrektur | Phase 1 |
| 4 | CPU-Referenz, körperfestes Voxelmodell und Wasserlinienkennwerte | Phasen 1 und 3; Phase 2 für GPU-Vergleiche |
| 5 | Belastbarer 2-DOF-Solver und dynamische Kraftschnittstelle | Phasen 0 und 4 |
| 6 | Weitere Kraftmodule mit belegten Parametern | Phase 5 |
| 7 | 6-DOF-Dynamik | Phasen 1, 4, 5 und 6 |
| 8 | Gesamtabnahme und Freigabe | alle freizugebenden Phasen |

Die Nummerierung ist die empfohlene Arbeitsreihenfolge. Phase 2 kann parallel
zu Phase 1 vorbereitet werden. Phase 2 weist zunächst nur Backend-Kompatibilität
und einen tatsächlichen GPU-Kernel nach; eine endgültige CPU/GPU-Zuordnung oder
GPU-Implementierung der Hydrostatik erfolgt erst, wenn Phase 4 eine
repräsentative CPU-Referenz des körperfesten Rasters und der wiederholten
Auswertung bereitstellt. Der vollständige Vergleich umfasst Datentransfers und
Vorbereitung.

## 3. Phase 0 – Ausgangsbasis und Messbarkeit

### Umsetzung

1. Arbeitsbaum und vorhandene Änderungen sichern; insbesondere keine
   ungetrackten Nutzerdateien oder Modellquellen in Tests einbeziehen.
2. Mit der Projektumgebung unter `.venv` Python-Version und tatsächlich
   installierte Pakete erfassen. Ausgangszustand der vollständigen Testsuite
   und vorhandene Warnungen protokollieren.
3. Bestehende Messfälle für konfigurierten Quader und Yachtmodell festlegen.
   Pro Fall Mesh-/Voxelauflösung, Zahl der Teile, Hardware, Vorbereitungszeit,
   einzelne Hydrostatik-/Kraftauswertung und Solverlauf getrennt erfassen.
4. Einen reproduzierbaren GUI-Smoke-Test für Start, Szenenaufbau,
   Simulationsmodi, Zeitsteuerungen, Körperbaum und sämtliche bestehenden
   Darstellungssteuerungen festhalten: Layer, Kamera-Presets, Hintergründe,
   Beleuchtung, Wasseroberfläche, Wasseroptik und SSAO.
5. Den Ausgangszustand der Materialbearbeitung festhalten: Änderungen gelten
   nur für die Sitzung, aktualisieren Laufzeitkörper und Darstellung,
   schreiben keine Konfigurations-JSON und lösen keine Solver-Neuberechnung
   aus.
6. Referenzdaten und Testeingaben isolieren, damit Tests keine
   `konfigurationen/*.json` oder OBJ-Dateien verändern.

### Prüfungen und Abnahme

- Vollständige Bestandstests laufen in der Projektumgebung reproduzierbar
  durch; die tatsächlichen Ergebnisse werden dokumentiert, ohne eine frühere
  Testanzahl als Sollwert vorauszusetzen.
- Referenzmessungen sind wiederholbar und enthalten getrennte Zeiten für
  einmalige Vorbereitung und wiederholte Auswertungen.
- GUI-Smoke-Test startet in einer Qt-Offscreen-Sitzung und zusätzlich als
  normaler Windows-Prozess mit eingebettetem QtInteractor.
- Regressionen sichern die oben genannten Darstellungsfunktionen und das
  sitzungsgebundene Verhalten von Materialänderungen einschließlich
  unverändert gebliebener JSON-Dateien und ausbleibender Solver-Neuberechnung.
- Bekannte Basisfehler werden von später neu eingeführten Fehlern
  unterscheidbar festgehalten.

## 4. Phase 1 – Meshvalidierung, Masse und Trägheit

### Umsetzung

1. Die Mesh-Eingangsgrenze bei OBJ-Laden und prozeduraler Erzeugung
   vereinheitlichen. Vor jeder Volumenrechnung Punkte und Indizes auf
   Endlichkeit, gültige Indizes, leere Daten, entartete Dreiecke,
   geschlossene Kanten und konsistente Orientierung prüfen.
2. Geschlossene Volumenmeshes von offenen, flächenmassigen Schalen
   unterscheiden. Ein offenes Mesh darf nicht stillschweigend als
   verdrängendes Volumen behandelt werden; Schalen behalten ihre
   flächenbezogene Masse.
3. Volumen-, Flächen-, Schwerpunkt- und Trägheitsberechnung in
   `core/massen.py` und `core/koerper.py` anhand analytischer Formen prüfen.
   Fehlertexte sollen das betroffene Teil und die verletzte Meshbedingung
   identifizieren.
4. Für Verbände Transformationen, massengewichteten Schwerpunkt und
   Parallelaxensatz für alle Teile einschließlich unterschiedlicher Dichten
   und Schalen systematisch prüfen.
5. Sicherstellen, dass der Trägheitstensor um den Schwerpunkt symmetrisch und
   positiv semidefinit ist und seine Hauptmomente die
   Dreiecksungleichungen erfüllen. Rundungsabweichungen werden nur in
   begründeten numerischen Toleranzen akzeptiert.

### Betroffene Bereiche und Tests

- Produktionskandidaten: `segelphysik/core/massen.py`,
  `segelphysik/core/koerper.py`, `segelphysik/core/koerper_formen.py`,
  `segelphysik/core/fabriken.py` und `segelphysik/core/boot_bau.py`.
- Tests ergänzen: `tests/test_koerper.py`,
  `tests/test_bewegung_und_formen.py` und bei Bedarf ein eigenes
  `tests/test_mesh_validierung.py`.
- Abdecken: analytischer Quader und Kegel, Translation/Rotation eines
  Einzelteils, Verband mit versetzten Teilen und unterschiedlichen Dichten,
  Schalenfläche/-masse, offene/geschlossene/ungültige Meshes und endliche
  positive Masseneigenschaften.

### Abnahme

Ungültige Eingaben scheitern nachvollziehbar; Volumenkörper und Schalen
bleiben korrekt unterscheidbar. Alle Referenzwerte für Masse, Schwerpunkt
und Trägheit stimmen innerhalb der fachlich begründeten numerischen
Toleranzen.

## 5. Phase 2 – CPU/GPU-Technologieentscheid und Rechenpfad

### Technologieentscheid vor Implementierung

1. Für Windows x64 und Python 3.14.8 die praktisch verfügbaren
   GPU-Rechenbackends anhand offizieller Paket-/Treiberunterstützung und eines
   minimalen Ende-zu-Ende-Prototyps auf der AMD Radeon 760M prüfen. Eine
   erfolgreiche Installation oder ein erfolgreicher Import gilt nicht als
   Nachweis. Dieser Schritt entscheidet nur über technische Kompatibilität,
   noch nicht über die endgültige CPU/GPU-Zuordnung der Hydrostatik.
2. Mindestens Initialisierung, Speicherverfügbarkeit, Datentransfer,
   numerische Ausgabe und Fehlerverhalten eines tatsächlichen Rechenkernels
   testen. Rendering über PyVista/VTK ist kein Nachweis für GPU-Physik.
3. In Phase 2 nur Geräteerkennung, Backend-Initialisierung, Speicherzugriff
   und einen kleinen tatsächlichen Rechenkern mit Datentransfer auf der
   Zielhardware prüfen. Diese Prototypmessung weist technische
   Kompatibilität nach; sie ist kein repräsentativer CPU/GPU-Benchmark und
   entscheidet nicht über die Aufgabenverteilung. Quader und komplexes
   Modell werden erst nach Vorliegen der CPU-Referenz in Phase 4 für den
   maßgeblichen Vergleich einschließlich Vorberechnung, Transfers und
   wiederholter Kraftauswertung verwendet.
4. In dieser Phase nur Kandidaten und Messverfahren vorbereiten. Die
   endgültige Arbeitslastmessung und feste Aufgabenverteilung erfolgen nach
   Vorliegen der CPU-Referenz des körperfesten Rasters in Phase 4; dabei
   werden erwartete wiederholte Aufrufe, Vorbereitung und Transfers
   einbezogen. Die Zuordnung wird vor Freigabe durch Entwicklungsbenchmarks
   überprüft und bleibt zur Laufzeit unverändert.
5. Bei fehlendem kompatiblem Backend bleibt CPU der korrekte Betriebsweg.
   Kompatibilitätsnachweis und späterer Zuordnungsentscheid werden getrennt
   dokumentiert; es gibt keine automatische Laufzeit-Benchmark- oder
   Leistungswahl.

### Implementierung

- Eine kleine Physik-Backend-Grenze kapselt die festgelegte CPU- und
  gegebenenfalls GPU-Ausführung, ohne GUI- oder Rendercode mit
  Rechenbackend-Details zu vermischen.
- Beim Start wird ausschließlich GPU-Präsenz festgestellt. Ist eine GPU
  vorhanden und die Aufgabe laut Code dem GPU-Pfad zugeordnet, wird dieser
  versucht. Fehler bei tatsächlicher Initialisierung oder Ausführung werden
  im Protokoll mit Backend und Ursache ausgegeben; genau diese Berechnung
  wird auf der CPU wiederholt. Ein langsamer, aber fehlerfreier GPU-Aufruf
  löst keinen Laufzeitwechsel aus.
- CPU und GPU verwenden dasselbe fachliche Modell, dieselben SI-Einheiten und
  definierte Rückgabedaten. GPU-Ergebnisse, die unvollständig oder nicht
  endlich sind, gelten als Fehler und nicht als Erfolg.
- Neue Laufzeitabhängigkeiten werden nur nach erfolgreichem Zielhardwaretest
  in `requirements.txt` und gegebenenfalls `requirements-dev.txt`
  aufgenommen. Der CPU-Betrieb darf nicht von optionalen GPU-Paketen
  abhängen.

### Prüfungen und Abnahme

- CPU-Tests laufen unabhängig von GPU und Backendinstallation.
- Mocktests decken GPU nicht vorhanden, erfolgreichen GPU-Aufruf,
  Initialisierungsfehler und Ausführungsfehler mit CPU-Fallback ab. Sie
  ersetzen nicht den realen Abnahmelauf auf unterstützter Hardware.
- Bei verfügbarer GPU werden CPU/GPU mit identischen Testdaten verglichen:
  `|ΔV_disp| <= schranke_volumen_m3`; der Schwerpunkt wird nur verglichen,
  wenn beide Volumina oberhalb der Schranke liegen, dann
  `|ΔK| <= schranke_punkt_m`. Kraft- und Momentabweichungen werden zusätzlich
  mit den in Spezifikation Abschnitt 9 festgelegten, aus diesen Grenzen
  abgeleiteten Schranken geprüft.
- GPU-Erfolg wird anhand ausgeführter Rechenarbeit und erfüllter
  Genauigkeitstests nachgewiesen, nicht anhand eines Imports.
- Der tatsächlich verwendete Rechenpfad wird im vorhandenen Protokoll
  nachvollziehbar ausgegeben. GPU-Meldungen enthalten Backend und
  Gerätenamen; der CPU-Fallback und dessen Ursache werden ebenfalls
  ausgewiesen.
- Benchmarkbericht enthält Hardware, Treiber, Python-/Backendversion,
  Rasterauflösung, alle getrennten Zeitanteile und CPU/GPU-Ergebnisvergleich.

## 6. Phase 3 – Überschneidungen und dauerhafte Modellkorrektur

### Umsetzung

1. Für geschlossene, volumetrische Komponenten pro Hauptkörper eine
   robuste Konflikterkennung ergänzen. Berührende gemeinsame Grenzen gelten
   nicht als Volumenüberschneidung. Offene Schalen werden nicht als
   geschlossene Volumenkörper klassifiziert.
2. Vor dem Physiklauf betroffene Bauteile eindeutig benennen und bei
   erkanntem Konflikt anhalten. Ausschließlich für diesen Fall einen Dialog
   zur Auswahl des unangetasteten Vorrangkörpers verwenden; die bestehende
   allgemeine GUI bleibt unverändert.
3. Die Boolesche Differenz `Konfliktkörper minus Vorrangkörper` zunächst auf
   einer temporären Kopie berechnen. Nullvolumen, offene oder ungültige
   Resultate und fehlgeschlagene Operationen zurückweisen.
4. Die dauerhafte Speicherung für beide Quellarten konkret umsetzen:
   - OBJ: korrigierte Geometrie in der ursprünglichen OBJ-Quelle speichern
     und Koordinatentransformation/Skalierung verlustfrei berücksichtigen.
   - Prozedurale Definition: die korrigierte Geometrie als dauerhaft
     gespeicherte Mesh-Quelle/Geometrie-Überschreibung des betroffenen
     prozeduralen Bauteils in dessen ursprünglicher Definition bzw.
     Quelldaten ablegen. Der Lader muss diese gespeicherte Geometrie beim
     erneuten Laden anstelle der unbeschnittenen prozeduralen Ausgabe
     verwenden; die unveränderte prozedurale Definition bleibt als
     nachvollziehbare Herkunft erhalten. Datenformat und Lade-/Speicherpfad
     werden mit einem Prototyp vor der eigentlichen Konfliktkorrektur
     festgelegt und rückwärtskompatibel gehalten.
5. Vor jeder Änderung eine bytegetreue Sicherung erstellen. Erst eine
   transaktionale Speicherung übernehmen, die nach erneutem Laden dieselbe
   Geometrie ergibt und die Konfliktprüfung besteht. Bei jedem Fehler
   Ausgangsdatei wiederherstellen und verständlichen Fehler melden.
6. Nach erfolgreicher Korrektur Körper, Masse, Schwerpunkt, Trägheit,
   vorbereitete Geometriedaten und Darstellung vollständig neu aufbauen.
   Wiederholtes Laden darf die Korrektur weder verlieren noch erneut
   anwenden.

### Betroffene Bereiche und Tests

- Produktionskandidaten: `core/boot_bau.py`, `core/fabriken.py`,
  `core/koerper.py`, GUI-Lade-/Baumfluss in `gui/app.py`,
  `gui/baum.py`, `gui/hauptfenster.py`; neue Geometrieoperationen in einem
  klar abgegrenzten Physikkernmodul.
- Tests ergänzen: `tests/test_baum_regeln.py`,
  `tests/test_gui_baum_json.py` und gezielte neue Tests unter
  `tests/test_geometrie_konflikte.py`.
- Tests verwenden isolierte temporäre Modellquellen, niemals die
  Produktions-OBJ-Dateien.

### Prüfungen und Abnahme

- Keine Überlappung, bloße Berührung, eindeutige Überschneidung und mehrere
  benannte Konflikte testen.
- Vorrangkörpergeometrie bleibt unverändert; nur das andere Teil wird
  beschnitten. Volumen, Masse, Schwerpunkt und Trägheit basieren danach
  auf derselben korrigierten Geometrie.
- Für OBJ und prozedurale Quelle jeweils Auswahl, gespeicherte Differenz,
  erneutes Laden und konfliktfreie Wiederholungsprüfung testen.
- Für die prozedurale Quelle zusätzlich prüfen, dass nach erneutem Laden
  nicht die ursprüngliche unbeschnittene Erzeugung die gespeicherte
  Geometrie-Überschreibung verdrängt und dass unveränderte Definitionen
  weiterhin wie bisher geladen werden.
- Fehler vor dem Schreiben, während des Schreibens und bei der erneuten
  Validierung simulieren; in jedem Fall muss die ursprüngliche Datei
  bytegleich wiederhergestellt sein.
- Ohne ausdrückliche Auswahl darf keine Quelldatei verändert werden.

## 7. Phase 4 – Körperfestes Raster und Hydrostatik

### Umsetzung

1. Auf der nach Phase 3 geprüften und konfliktfreien Geometrie zunächst
   eine CPU-Referenz des körperfesten Rasters implementieren. Den aktuellen
   globalen Voxelpfad in `core/auftrieb.py` als Vergleichsreferenz erhalten,
   bis neue CPU-Ausgaben analytisch und gegen den exakten
   Mesh-/Tetraederpfad geprüft sind.
2. Beim Laden dieser validierten und gegebenenfalls dauerhaft korrigierten
   Geometrie ein körperfestes Raster einmalig
   vorbereiten. Rasterursprung, Auflösung und Abdeckung sind deterministisch;
   Modell-, Material- oder Auflösungsänderung invalidieren und erneuern die
   vorbereiteten Daten.
3. Für eine Pose die Wasserhalbebene in das Körperkoordinatensystem
   transformieren. Das Raster bleibt starr; es wird nicht pro Lage oder
   Kraftauswertung neu erzeugt. Die Auswertung liefert endliches
   verdrängtes Volumen und Volumenschwerpunkt.
4. Wasserlinienfläche und Flächenträgheit in einer klaren
   Hydrostatik-Ausgabe verfügbar machen, sobald die Stabilitätsdiagnostik sie
   benötigt. Ein fehlender Wasserlinienschnitt und verschwindendes Volumen
   ergeben definierte, endliche Ergebnisse ohne Division durch null.
5. Voxel-Union und Überlappungskorrektur auf eine gemeinsame,
   korrigierte Geometrie beziehen; keine doppelte Volumenzählung.
6. Nach der CPU-Referenz die endgültige Zuordnung für Vorbereitung und
   wiederholte Auswertung anhand repräsentativer vollständiger Arbeitslasten
   festlegen. Anschließend nur die laut Code GPU-zugeordneten Aufgaben
   implementieren. Der CPU-Pfad bleibt immer eigenständig ausführbar.

### Betroffene Bereiche und Tests

- Produktionskandidaten: `core/auftrieb.py`, `wasser_schnitt.py`,
  Geometrie-/Körperdaten aus Phase 1; bei Bedarf ein eigenes
  `core/voxelmodell.py`.
- Bestehende Tests erweitern: `tests/test_auftrieb.py`,
  `tests/test_wasser_schnitt.py`, `tests/test_wasserlinie_geometrie.py`.

### Prüfungen und Abnahme

- Analytische Fälle: trocken, tangentialer Kontakt, teilweise und vollständig
  eingetaucht, geneigte Körper, getrennte Teile und Mehrfachbelegung.
- Wasserlinienfläche und Flächenträgheit mit analytischen Schnittflächen
  prüfen, darunter zentrierter Quader/Ponton bei bekannter Eintauchtiefe,
  geneigter Schnitt und verschwindende Wasserlinienfläche. Fläche,
  Schwerpunkt und Tensorachsen müssen zur festgelegten Welt-/Körperkonvention
  passen und bei degeneriertem Schnitt endliche definierte Ergebnisse liefern.
- Verdrängtes Volumen ist monoton mit zunehmendem Tiefgang; Auftrieb ist
  `rho_w * g * V_disp`; Momentenvorzeichen entsprechen der Rollkonvention.
- Körperfestes Raster bleibt beim Lagewechsel identisch und wird nur bei
  Modell-/Material-/Auflösungsänderung neu erstellt.
- Voxelkonvergenz wird gegen analytische bzw. exakte Referenzen mit den
  konfigurierten Grenzen geprüft.
- CPU/GPU-Prüfungen erfüllen zusätzlich sämtliche in Phase 2 genannten
  Volumen-, Schwerpunkt-, Kraft- und Momentschranken.
- Vergleichsmessung weist Vorbereitungszeit, Transfers und wiederholte
  Auswertung getrennt aus.

## 8. Phase 5 – Statische Statik und 2-DOF-Dynamik absichern

### Statischer Solver

1. `core/statisch.py`, `core/statisch_robust.py` und
   `core/stoerung.py` so abstimmen, dass ein begrenztes Suchbudget gilt und
   nur eine geeignete stabile Lage gesucht wird; keine exhaustive
   Multi-Start-Suche ergänzen.
2. Erfolg, instabile Lage, neutrale Lage, Stagnation, Budgetende und
   ungültige Rechenergebnisse als unterscheidbare Ergebnisse/Fehler
   behandeln. Restkraft, Restmoment und Abbruchursache dürfen bei Misserfolg
   nicht verloren gehen.
3. Vorhandene Statusausgabe und 3D-Pose mit dem tatsächlichen Solverstatus
   verbinden. Keine neue Liste mehrerer Gleichgewichte und keine zusätzlichen
   allgemeinen GUI-Steuerelemente.

### Dynamik

1. Den festen SI-Zeitschritt aus `physik.json` als einzige Integrationsbasis
   erhalten. Wandzeit/Akkumulator bestimmt nur die Zahl vollständiger
   Schritte.
2. Bestehende z-/phi-Dynamik in `core/dynamik.py` gegen dieselbe
   Hydrostatik- und Kraftfunktion wie den Solver prüfen.
3. Ungedämpfte Grenzfälle, deterministische Wiederholung und passive
   Dämpfung testen. Dämpfung darf keine Energie zuführen; Schwerkraft wirkt
   im Schwerpunktframe ohne künstliches Eigenmoment.
4. Echtzeitaufrufe über bestehende `HauptFenster`-Timer-/Modussteuerung
   einbinden. Berechnung darf keine GUI-Änderung erzwingen und die
   Ereignisschleife nicht blockieren; Visualisierung wird sicher im
   GUI-Thread aktualisiert.

### Tests und Abnahme

- Bestehende Referenztests aus `tests/test_statisch.py`,
  `tests/test_statisch_robust.py`, `tests/test_stoerung.py`,
  `tests/test_dynamik.py` und `tests/test_sim_modus.py` erweitern.
- Solver: Gleichgewicht, Restfehler, Stabilität/Neutralität, Stagnation,
  ungültige Werte und begrenzte Abbrüche prüfen.
- Dynamik: fester Schritt, Determinismus, Kraft-/Momentenbilanz,
  Energieerhaltung im ungedämpften geeigneten Referenzfall und nicht
  zunehmende Energie bei passiver Dämpfung prüfen. Zusätzlich aus
  repräsentativen Anfangsstörungen das Einmünden in eine stabile
  Gleichgewichtslage testen; Endpose und Restkraft/-moment gegen die
  statische Solverlösung vergleichen.
- GUI-Regression mit `tests/test_gui_steuerung.py`,
  `tests/test_gui_laufzeit_edit.py`, `tests/test_gui_app.py`,
  `tests/test_grafik_bruecke_darstellung.py` und
  `tests/test_vista_ui.py`: Modi bleiben exklusiv; `=` und `>` bleiben nur
  im Echtzeitmodus aktiv; Baum- und Layersteuerung, Kamera-Presets,
  Hintergründe, Beleuchtung, Wasseroberfläche, Wasseroptik, SSAO, Farben,
  Wasserlinienschnitt, Pose und Docks bleiben funktionsgleich. Sitzungsgebundene
  Materialänderungen dürfen JSON-Dateien nicht verändern und lösen gemäß
  Spezifikation keine Solver-Neuberechnung aus.

## 9. Phase 6 – Kraftmodule

### Umsetzung

1. Eine gemeinsame Kraftschnittstelle einführen bzw. die bestehende
   Kraftfunktion so erweitern, dass sie Zustand, lineare Geschwindigkeit,
   Winkelgeschwindigkeit und Hydrostatikergebnis entgegennimmt.
2. Ausgabe von Gesamtkräften und -momenten von den für vorhandene
   Darstellung benötigten Auftriebsdaten trennen, aber über ein stabiles
   Ergebnisobjekt gemeinsam verfügbar halten.
3. Bestehende lineare Tauch-/Krängungsdämpfung als konfigurierbare Anteile
   in das Kraftmodell überführen, ohne die Integration von konkreten
   Kraftmodulen abhängig zu machen.
4. Linearen/quadratischen Widerstand, Fluidgeschwindigkeit und Added Mass
   einzeln ergänzen. Keine unbelegten Koeffizienten erfinden: Module bleiben
   deaktiviert, bis fachlich bestätigte Werte in einer validierten
   Konfiguration vorliegen.

### Prüfungen und Abnahme

- Jedes Modul mit isolierten Vorzeichen-, Einheiten-, Grenzfall- und
  Energieprüfungen testen; Nullgeschwindigkeit und Nullparameter liefern
  keinen künstlichen Beitrag.
- Superposition der Module gegen die gemeinsame Gesamtkraft prüfen.
- Sicherstellen, dass Solver und Echtzeitintegration dasselbe Kraftmodell
  aufrufen und die bestehenden Auftriebsdarstellungen weiter funktionieren.
- Konfigurationstests prüfen fehlende, ungültige und nicht endliche
  Koeffizienten. Nicht bestätigte oder ungültige Werte dürfen nicht still
  durch Standardwerte ersetzt werden.

## 10. Phase 7 – 6-DOF-Dynamik

Diese Phase beginnt erst, wenn 2-DOF, Kraftschnittstelle, Trägheitstensor und
Hydrostatik abgenommen sind.

### Umsetzung

1. Zustand um drei translatorische Freiheitsgrade und normierte
   Quaternion-Orientierung erweitern; bestehende 2-DOF-Schnittstellen
   kontrolliert weiterverwenden oder klar migrieren.
2. Newton-Euler-Kräfte und -Momente konsistent zwischen Körper- und
   Weltkoordinaten transformieren. Trägheit bleibt im Körperframe;
   Quaternionen werden nach jedem Schritt normiert.
3. Freiheitsgrade ohne rückstellende äußere Kräfte nicht künstlich
   stabilisieren. Keine neue GUI-Steuerung oder Änderung der Bedienmodi;
   vorhandene Pose-/Darstellungspipeline nimmt die berechnete Pose entgegen.
4. Festen Zeitschritt sowie numerische Stabilität für den erweiterten Zustand
   beibehalten und Fehler-/Abbruchzustände sichtbar machen.

### Prüfungen und Abnahme

- Quaternion-Normierung und Orientierungs-Transformationsinvarianten testen.
- Reine Translation, reine Rotation, Impuls- und Drehimpulsbilanz und
  Koordinateninvarianz mit analytischen Fällen prüfen.
- Gravitation ohne künstliches Moment und frei bewegliche Achsen prüfen.
- 2-DOF-Regression und alle GUI-Bedienungstests unverändert bestehen lassen.

## 11. Phase 8 – Gesamtabnahme

1. Gezielte Tests jeder geänderten Physik-, Geometrie-, Konfigurations- und
   GUI-Schnittstelle ausführen.
2. Vollständige Testsuite mit der Projekt-Pythonversion ausführen:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest
   ```

3. Konfiguration und Abhängigkeiten prüfen:

   ```powershell
   .\.venv\Scripts\python.exe -m pip check
   ```

4. GUI-Regression unter Offscreen-Qt und anschließend den realen
   Windows-Start mit QtInteractor prüfen. Sichtbare Bedienelemente,
   Beschriftungen, Anordnung, Farben, Kamera-Presets, Hintergründe,
   Beleuchtung, Wasseroberfläche, Wasseroptik, SSAO, Layer, Wasserlinienschnitt,
   Pose, Docks, Körperbaum und Simulationssteuerung mit der Ausgangsbasis
   vergleichen. Materialänderungen auf Sitzungsbindung, JSON-Unverändertheit
   und ausbleibende Solver-Neuberechnung prüfen.
5. Auf der Zielhardware interaktive Lasttests mit CPU und – falls verfügbar –
   mit dem unterstützten GPU-Pfad ausführen. Reaktionszeit, Bildrate,
   Initialisierung, Berechnungsdauer und Speicher-/Transferkosten getrennt
   berichten. Eingabereaktion und Bildrate werden unter dokumentierter
   repräsentativer Last gemessen und mit den Richtwerten 100 ms bzw. 30 FPS
   verglichen, ohne daraus harte Einzelaufruf-Laufzeitgrenzen abzuleiten.
   Warte- und Abbruchzustände müssen in bestehenden Statusflächen
   nachvollziehbar sein. Bei CPU-only-Ausführung bleibt die Anwendung
   vollständig bedienbar.
6. Vorher-/Nachher-Modellquellen prüfen: Tests haben keine echten
   Projektmodelle oder JSON-Konfigurationen verändert. Dauerhafte
   Korrekturtests haben ihre temporären Daten aufgeräumt.
7. `git diff --check` ausführen und Änderungen gegen den Arbeitsbaum vor
   Beginn der Umsetzung abgleichen. Keine fremden Nutzerdaten aufnehmen.

### Freigabekriterien

- Alle gezielten Tests und die vollständige Regression bestehen; begründete
  Ausnahmen sind einzeln dokumentiert und bedürfen ausdrücklicher
  Vereinbarung.
- Numerische Referenzen, CPU/GPU-Toleranzen, Konfliktkorrektur inklusive
  Rollback, Solverfehlerfälle und Dynamikprüfungen bestehen.
- GPU wird nur dann als verfügbarer Physikpfad ausgewiesen, wenn ein
  tatsächlicher Kernel auf der Zielhardware gelaufen ist und die numerischen
  Grenzwerte eingehalten wurden. Sonst wird der CPU-Pfad korrekt protokolliert.
- Bestehende Darstellung und Bedienung sind regressionsgeprüft; die
  GUI-Ereignisschleife bleibt unter repräsentativer Last bedienbar.
- Bekannte Warnungen, Backend-/Hardwaregrenzen und Messbedingungen sind
  nachvollziehbar dokumentiert.

## 12. Ausdrücklich nicht Teil dieses Plans

- Änderungen an GUI-Anordnung, Beschriftungen, vorhandenen Steuerungen oder
  allgemeinen Bedienelementen.
- Systematische Suche nach allen stabilen Gleichgewichtslagen.
- Laufzeit-Benchmarking oder leistungsabhängiger CPU/GPU-Wechsel.
- Automatisches Ändern von Modellquellen ohne Konflikterkennung und
  Vorrangkörperauswahl.
- Erfundenes Speichern von Sitzungs-Materialänderungen in Konfigurations-JSON.
- Widerstands-/Added-Mass-Koeffizienten ohne fachliche Grundlage.
- Commit, Tag oder Push ohne ausdrücklichen Auftrag.
