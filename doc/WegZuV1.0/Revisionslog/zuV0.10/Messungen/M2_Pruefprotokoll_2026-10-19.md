# M2: Native Datenbasis und erste Rechenkandidaten

> Historischer Stand vor der Nutzerentscheidung zur produktiven Übernahme
> auch langsamerer Blöcke. Der spätere Umfang, aktuelle Tests und offene
> Gates stehen im [Produktivprotokoll](Produktiv_Pruefprotokoll_2026-10-19.md).

**Stand:** 19.10.2026  
**Branch:** `v0.10`  
**Status:** U-V0.10-000004 und U-V0.10-000005 in Bearbeitung;
Daten-/Buildnachweise für U-V0.10-000004 erbracht, GUI-Anbindung noch offen.
Kein vollständiger M2-Abschluss und keine produktive C++-Physikfreigabe.

## Ausgangspunkt und Referenzschutz

M1 wurde mit 909 bestandenen Tests, einem bestehenden Windows-Symlink-Skip,
exaktem v0.9-Replay, 298 konkreten Funktionszuordnungen und 18 vollständigen
Speicher-Livebaselines abgeschlossen. Siehe
[M1-Prüfprotokoll](M1_Pruefprotokoll_2026-10-19.md).

Die ursprünglichen Python-Rechenfunktionen, Konfigurationen, Modelle und
eingefrorenen Referenzwerte bleiben unverändert. Neue Adapter liegen in
[native_backend.py](../../../../../code/python/segelphysik/core/native_backend.py).
Native Kandidaten ändern dagegen bestimmungsgemäß die C++-Quellen.
Der Referenzprüfer erlaubt dies nur im ausdrücklich gewählten
`native_kandidaten=True`-Modus und weist jeden abweichenden nativen
Quellhash einzeln aus. Die Originalhashes stammen weiterhin aus
`7a955c24ceb6c0825e05a574b959dd1176be2e2c`; Python-/Modellabweichungen
scheitern auch in diesem Modus. Der strikte M1-Baselinebetrieb bleibt strikt.

Keine Änderung des aktiven GUI-/Worker-Rechenpfads. Die Projektumgebung
wurde nicht durch den Kandidaten ersetzt; die Installation liegt in einer
gesonderten Testumgebung unter `build\native-m2-testenv`.

## U-V0.10-000004: Datenverträge und Build

- Eigene C++-Typen für 13-komponentigen Zustand, Mesh, Modell, Parameter,
  Wrench, benannte Beiträge und Ergebnis einschließlich separater
  Hydrostatikdaten, Added Mass, Widerständen, Fluidgeschwindigkeiten und
  Schwerkraftkennzeichen.
- Float64 für kontinuierliche Werte, Int64 für Dreiecksindizes,
  Quaternionreihenfolge wxyz und bestehende SI-/Framekonventionen.
  Dimensions-, Datentyp-, Index-, Endlichkeits- und grundlegende
  Tensorprüfungen; keine implizite Float32-/Listen-Konvertierung.
- Zusammenhängende, gestridete, rückwärts gestridete und schreibgeschützte
  Arrays getestet. Explizite Eingangskopie beim Kontextaufbau; keine
  geliehenen NumPy-Zeiger. Ausgaben sind unabhängige eigene Arrays und
  überleben Eingaben sowie native Kontexte.
- Semidefinite Trägheit bleibt für Punktmassendaten zulässig.
  Das ist keine Freigabe zur Dynamikinversion eines singulären Tensors.
  Die vorhandene physikalische NumPy-Eigenwertvalidierung bleibt bei der
  Modellvorbereitung bzw. außerhalb des Aggregationsblocks erhalten.
- Expliziter Lader prüft ABI `1`, Datentypen und gemeldeten Kandidatenpfad
  `cpp/datenschicht`; Modul-/DLL-/ABI-/Exportfehler sind Fehler, kein
  Python-Erfolg als Ersatz.
- Große reine C++-Arbeit läuft nach Datenübernahme ohne GIL; keine
  Python-/Qt-/VTK-Aufrufe darin. Atomarer Abbruchauftrag mit expliziter
  Fehlerantwort. Kein neuer Hallo-/TEST-Pfad.
- Mehrere saubere Release-Neubauten in neuen Buildverzeichnissen und
  Neuinstallation in der gesonderten Testumgebung erfolgreich.
  MSVC, C++17, ausdrücklich `/fp:precise`, kein Fast-Math.
  Die tatsächlich verwendete Compilerkonfiguration, Quellen- und
  Binärhashes stehen in den Messumgebungen.

Ein erster Aufruf mit `--no-build-isolation` scheiterte am fehlenden
lokalen Buildbackend. Der reguläre isolierte pip-Build installierte die
bereits deklarierten Buildabhängigkeiten und baute erfolgreich.
Eine erste Messumgebung fand PySide6-Metadaten nicht; ein lokaler
`.pth`-Verweis bindet nun die unveränderten Projektabhängigkeiten ein,
während das native Kandidatenmodul aus der Testumgebung kommt.
Beide tatsächlichen Importpfade wurden geprüft. Keine globale
PATH-Manipulation und keine Löschung unbekannter Umgebungen.

## U-V0.10-000005: Tatsächlich implementierte Kandidaten

Quellen:
[Frames/Quaternionen](../../../../../code/cpp/src/frames.hpp),
[Datentypen](../../../../../code/cpp/src/datentypen.hpp),
[Snapshotkern](../../../../../code/cpp/src/koerperkontext.hpp),
[Bindings](../../../../../code/cpp/src/modul.cpp).

- Quaternionnormierung, Matrixabbildung und Rückabbildung mit allen
  Spur-/Diagonalzweigen, Quaternionprodukt und Orientierungsfortschritt.
  Noch kein vollständiger nativer Integrator.
- Native Pose mit Punkt-/Vektor-/Punkteabbildung, Inversion, Verkettung,
  Achsenwinkel und Modell-/Gelenkabbildung.
- Numerische Aggregation vorbereiteter Körperteile: Masse, Schwerpunkt,
  gedrehte Trägheit, Steineranteile, kombinierte Punkte und verschobene
  Dreiecksindizes. Punktmassen ohne Verdrängung getestet.
- Dauerhafter `VerbandKontext` verhindert erneute Modelldatenkopien je
  Rechnung; Neuaufbau, reine Rechnung und Ausgaben separat gemessen.
  Die bestehende physikalische Eigenwertvalidierung bleibt außerhalb.
- Native Transformation vorbereiteter Blattgeometrie für Snapshots;
  unveränderte Geometrie wird einmal vorbereitet und exakt kopiert,
  ohne gerundete Zustandsschlüssel oder Physiknäherung.
- Explizite Invalidierung prüft Identität, Versionen, Masse, Trägheit,
  Unterbaum, Rollen, Gelenke und tatsächliche Meshwerte. Auch direkte
  unversionierte Punkt-/Dreiecks-/Unterbaumänderungen werden abgewiesen,
  nicht als gültiger Cachetreffer behandelt. Vor und nach der
  Snapshotausgabe geprüft; neue Quelle benötigt neue Vorbereitung.

Die Python-Baum-/Materialvorbereitung ist weiterhin die im Plan
ausdrücklich gestufte Aufbaugrenze für M7. Diese Kandidaten ersetzen
noch nicht den vollständigen öffentlichen Körperkonstruktor oder den
GUI-/Worker-Lebenszyklus.

## Parität und Testnachweise

- Zunächst 45 Daten-/Ladertests, danach sukzessive 78, 82, 85, 115,
  126 und 131 gezielte Tests bestanden; Zahlen bezeichnen Teilstände.
- [Gemeinsamer Referenz-/Kandidatenlauf](M2_Integrierte_Testumgebung_2026-10-19.xml):
  **1041 bestanden, ein bestehender Windows-Symlink-Skip**.
  Kein Skip wegen fehlender nativer Exporte.
- [Projekt-Referenzsuite](M2_Referenz_Vollsuite_2026-10-19.xml):
  **916 bestanden, derselbe vorhandene Skip**, anschließend exakter
  eingefrorener v0.9-Replay bestanden.
- Nach Konstantdatenoptimierung 133 Kandidaten-/Ladertests bestanden.
  [Neuester gezielter Regressionslauf](M2_Basispose_Regression_2026-10-19.xml):
  **173 Tests bestanden**, einschließlich bestehender Python-Körper-/
  Frameverträge, unabhängiger Snapshotausgaben, expliziter
  Überlaufabweisung und unversionierter Basisposeänderung.
  Diese überlappenden Testzahlen werden nicht addiert.

Direkte Prüfungen enthalten 1000 deterministische Quaternionfälle,
Matrixzweiggrenzen einschließlich benachbarter Float64-Werte,
Quaternionvorzeichen, zufällige Framekompositionen/Inversionen,
Steiner-/Punktmassenfälle, Modell-/Gelenkwinkel und Overrides,
alle drei echten Bootmodelle, benannte Ergebnisbeiträge und exakten
Datenrundlauf einschließlich aller Zusatzparameter.

Numerische Framevergleiche verwenden ausdrücklich `rtol=0`,
`atol=1e-12` aus dem bestehenden Frame-Test, kein pädagogisches
Fehlerbudget. Indizes, Felder, Frames, Beitragsnamen und
Datenrundläufe bleiben exakt. Überlauf ist keine nichtendliche
native Erfolgsantwort.

## Performance je Kandidat, einschließlich negativer Ergebnisse

[Neuester vollständiger Messstand](M2_Basispose_Invalidierung_2026-10-19/mathematik_frames.json),
[Umgebung, Compiler, Quellen und Binärhash](M2_Basispose_Invalidierung_2026-10-19/umgebung.json).
Je Fall sieben Wiederholungen nach Warmup; Rohwerte, Median, P95,
Streuung, absolute/prozentuale Differenz und Faktor gespeichert.
Einzelaufrufe enthalten pybind-Übergaben und genannte Ausgabeaufbereitung.
Aufbaukosten vorbereiteter Kontexte stehen separat im Bericht.

| Kandidat | Medianfaktor Python/C++ im neuesten Lauf |
|---|---:|
| Quaternionnormierung | 9,474 |
| Quaternion → Matrix | 14,800 |
| Matrix → Quaternion | 29,723 |
| Quaternionprodukt | 8,452 |
| Orientierungsfortschritt | 19,860 |
| Achsenwinkel | 26,541 |
| Poseaufbau einschließlich Quaternionausgabe | 4,302 |
| Pose-Rotationsmatrix | 7,039 |
| Punktabbildung | 14,752 |
| Vektorabbildung | 21,623 |
| Poseinverse einschließlich Matrixausgabe | 55,786 |
| Posekomposition einschließlich Matrixausgabe | 68,309 |
| Modellposeadapter | 2,239 |
| Gelenkposeadapter | 14,026 |
| Punkteabbildung, 1 Punkt, Arrayübergabe / vorbereitet | 17,525 / 14,707 |
| Punkteabbildung, 1000 Punkte, Arrayübergabe / vorbereitet | 1,389 / 1,685 |
| Punkteabbildung, 100000 Punkte, Arrayübergabe / vorbereitet | **0,594: langsamer** / 2,278 |
| Aggregation, 1 Teil, vorbereitet / mit Neuaufbau | 6,153 / 4,834 |
| Aggregation, 30 Teile, vorbereitet / mit Neuaufbau | 83,761 / 19,204 |
| Aggregation, 300 Teile, vorbereitet / mit Neuaufbau | 215,050 / 23,917 |
| Gesamter Snapshotadapter Optimist | **0,663: langsamer** |
| Gesamter Snapshotadapter Folkeboot | 1,217 |
| Gesamter Snapshotadapter yacht1 | **0,902: langsamer** |

**Keine Abnahme aus dieser Tabelle:** Gerade bei großen Arrays schwanken
die Vergleiche zur bereits nativen NumPy-Rechnung erheblich. Frühere
Messstände enthalten sowohl Vorteile als auch Faktoren deutlich unter 1;
sie bleiben unverändert erhalten. Ein einzelner positiver Messstand
beweist keinen robusten Gewinn. Direkte Arrayübergaben, vorbereitete Kontexte
und reine Kernarbeit dürfen nicht verwechselt werden.

Der ursprüngliche Snapshotkandidat war für alle drei Modelle langsamer.
Danach wurden unnötige Ausgabekopien und wiederholte Berechnung
unveränderlicher Geometrie entfernt. Die exakte Quellprüfung bleibt
erhalten, einschließlich unversionierter Änderungen. Sie zu entfernen
oder die Daten nur gerundet zu vergleichen wäre kein zulässiger Gewinn.
Der verbleibende Gewinn ist weiterhin nicht durchgängig belastbar.

Insbesondere werden Mikrobenchmarkfaktoren weder als FPS-Gewinn
hochgerechnet noch als fertiger nativer Physikbatch ausgegeben.

## Verbleibender M2-Abschluss

Die Daten-/Buildgrundlage aus U-V0.10-000004 ist geprüft; die
Rechenpfadanzeige und Fehlerweiterleitung im tatsächlichen GUI-Pfad
stehen vor einer produktiven Umschaltung noch aus. U-V0.10-000004 und
U-V0.10-000005 bleiben deshalb in Bearbeitung:

1. Die übrigen Körper-/Versions-/Eigenschaftsadapter einzeln den
   nativen Elternblöcken bzw. bereits nativen Bibliotheksarbeiten
   zuordnen und vollständig nachweisen.
2. Snapshot-/Großarraykosten weiter im tatsächlichen Elternpfad
   beurteilen; negative oder nur schwankende Vorteile nicht produktiv
   übernehmen. Ein relevanter ungelöster Hotspot bleibt offen.
3. Erst nach bestandenem M2-Gate Folgeintegration freigeben.
   Native Kraftcallbacks, vollständiger Batch, Solver, Darstellung
   und integrierte End-to-End-Abnahme sind noch nicht umgesetzt.

Keine produktive Umschaltung, kein neuer Commit, Push oder Tag.
