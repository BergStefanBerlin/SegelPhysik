# Produktive C++-Migration: Nachtrag vom 20.10.2026

## Auftrag und Abnahmegrenze

Der Nutzer hat am 20.10.2026 ausdrücklich die Workerumschaltung und die
weitere vollständige Umsetzung auch bei zunächst nicht erreichter strenger
Numerikparität beauftragt. Prüfungen dürfen vorläufig gelockert werden,
wenn die Ergebnisse ungefähr stimmen und Abweichungen dokumentiert werden.
Die Genauigkeitsbereinigung ist nachgelagert. Seit dem 19.10. sind auch
langsamere Übertragungen produktiv zu integrieren und zu vermessen.

Dies ist **kein vollständiger Abschluss von V0.10**. Endlichkeit, Schemas,
Frames, Einheiten, benannte Beiträge, Batch-/Zeitindizes, ungültige
Eingaben, Datenbesitz und explizite Fehler bleiben strenge Anforderungen.
Keine Änderung an Verfahren, Zeitschritt, Hydrostatikintervall, Float64
oder Compiler-Gleitkommaoptionen. Keine erneuerten Goldenwerte.

Historische Berichte und Rohmessungen vom 19.10. bleiben unverändert.
Spezifikationskennungen bleiben erhalten; die bisherige unbedingte
Numeriksperre ist am Spezifikationsende unter ihren ursprünglichen
Kennungen archiviert.

## Produktiv integrierte Erweiterungen

| Anforderung / Schritt | Umsetzung | Beleg und Einschränkung |
|---|---|---|
| A00006/A00023, U000010 | Ganzer exakter Echtzeitbatch in `PhysikKontext`, einmalige native Vorbereitung, öffentliche Ergebnisadapter | Keine Pythonkraftcallbacks innerhalb des Batches; Windows-Spawn, Pickle, Batchlängen 1/10/100 und Steuer-/Fehlerfälle geprüft |
| A00017/A00018, U000011 | Beide statischen Solver separat nativ, einschließlich Residuen, Newton, FD, Sekanten, Stagnation, exaktem LRU512-Cache, GM/Neutralität und Rollscan | Direkte Modellparität für Optimist/Folkeboot/yacht1; vollständige schwierige Sonderfalldiagnosen noch offen |
| A00019, U000011 | Stationäre 3D-/6D-Newtonstufen mit nativer Kraftauswertung, Jacobi, Pivotlösung, Begrenzung und Dämpfung | 100 gestörte Modellzustände gegen öffentliche Kraftauswertung; echter 6D-Newtonfall mit Querfahrt/Roll/Gier; keine Pythonresiduen im nativen Solver; Fortschritt nur zwischen Stufen |
| A00021, U000012 | Volumen, Fläche, homogene/Schalen-Schwerpunkte, beide exakten Trägheitsintegrationen | Zufällige Boxvarianten, große Schalenkoordinaten und Leermeshfehler geprüft; Validierung/Generatoren nicht pauschal als migriert gezählt |
| A00024, U000013 | SLERP, Anzeigezeit-/Pufferauswahl, Positions-/Orientierungsinterpolation | 1000 SLERPs, antipodale Quaternionen, Pausen, Rückstand, Einzelpose und wachsende Puffer geprüft |
| A00019/A00029 | Gemeinsame Eulerrotation, kinematische Achsenwinkelrotation, Störrotation | Defaultargumente, Achsen und zufällige Rotationen geprüft; weitere Stör-/Kontaktblöcke bleiben offen |

`A000xx` bzw. `U000xxx` kürzen hier lediglich die unveränderten Kennungen
`A-V0.10-000xx` bzw. `U-V0.10-000xxx` ab.

Vorbereitete exakte Modelle verwenden die nativen Solver. Beliebige
Python-Kraftcallbacks ohne nativen Modellkontext bleiben ein expliziter
Erweiterungspfad; dies ist keine native Vollmigration dieser Callbacks und
kein automatischer Fallback bei fehlendem Modul. Optionale Voxel-/OpenCL-
Verfahren behalten ihre bisherige Bedeutung.

## Numerische Abweichungen und vorläufige Prüfungen

### Worker: unabhängige 120-s-Folgen

Je Modell 30.000 Schritte bei `dt=0.004 s`; Python und C++ laufen unabhängig
vom selben Referenzstart aus. Jeder Zeitschritt und alle benannten
Kraft-/Moment-/Punktfelder werden verglichen, nicht nur die Endlage.

| Modell | Max. Zustandskomponentenabweichung, gemischte SI-Komponenten | Max. Abweichung eines Kraftdatensatzfelds | 1000-Schritt-Batchfaktor Python/C++ |
|---|---:|---:|---:|
| Optimist | 2.6449678e-12 | 9.41435874e-10 | 32.978 |
| Folkeboot | 6.16900871e-7 | 0.269893421 | 56.772 |
| yacht1 | 7.86697096e-15 | 2.35615971e-11 | 23.136 |

Die Maxima der Datensatzfelder haben unterschiedliche Einheiten.
Insbesondere ist das Folkebootmaximum kein Positionsfehler von 0.27 m;
es liegt im Ruder-Kraft-/Momentbereich. Komponentenweise Zustandsmaxima,
Schemas und Rohfolgen stehen in:

- [Optimist](Worker_120s_2026-10-20/optimist.json).
- [Folkeboot](Worker_120s_Fortsetzung_2026-10-20/folkeboot.json).
- [yacht1](Worker_120s_Fortsetzung_2026-10-20/yacht1.json).

Vorläufige Grenzen: Position `1e-5 m`, Quaternionkomponenten `1e-6`,
Körpergeschwindigkeit und Körperwinkelgeschwindigkeit je Komponente
`1e-5` in SI-Einheiten; Volumen `1e-7 m³`, Punkte `1e-5 m`,
Kraft/Moment `1 N`/`1 Nm` mit `rtol=1e-6`. Die Zustandsprüfung benutzt
die absoluten komponentenweisen Grenzen ohne zusätzliche relative
Toleranz. Zeit-, Index- und Schemavergleiche sind exakt.

**Nachträgliche Lockerung:** Die zunächst verwendete Kraft-/Momentgrenze
`0.01` wurde bei Folkeboot nach 38.624 s überschritten. Die vollständigen
120-s-Rohfolgen waren bereits gespeichert. Nach Auswertung des Maximums
`0.269893421` wurde die vorläufige Grenze gemäß Nutzerauftrag auf `1`
gesetzt. Der erste Lauf ist damit nicht nachträglich als ursprünglich
bestanden erklärt. Alle drei Modelle bestehen die benannte Ersatzprüfung.
Die ursprünglichen strengen Ergebnisse stehen zusätzlich in den Berichten.

Frühere 1000-Schritt-Diagnose: Optimist Zustand `1.0303820297e-11`,
Kraftfelder `1.03769249193e-7`; identischer Eingangszustand liefert maximal
`3.33066907388e-16` Schrittzustandsunterschied. Letzte Bits aus Löser-/
Matrix-/Quaternionrechnung werden im empfindlichen Ruderpfad verstärkt.
Eine vollständige Ursachenbereinigung ist nicht behauptet.

### Massenintegration / Goldenwerte

Der erste vollständige Lauf nach der Massenmigration ergab **1109
bestanden, 1 fehlgeschlagen, 1 vorhandener Skip**. Die alte
Golden-Trägheitsprüfung hatte für nahe null liegende Nebendiagonalen
`atol=1e-20`; beobachtet wurde eine Differenz bis `9.71445147e-15 kg m²`
bei Hauptträgheiten um `1159 kg m²`.

Die Prüfung ist jetzt ausdrücklich zweigeteilt: Python weiterhin mit
`rtol=1e-12, atol=1e-20`, C++ vorläufig mit
`rtol=1e-12, atol=1e-10 kg m²`. Andere Vertragsprüfungen und die Goldenwerte
bleiben unverändert. Das ersetzt keine spätere strenge Numerikbereinigung.

### Eingefrorener Hydrostatikreplay

Die unveränderte strenge Prüfung besteht im expliziten Pythonpfad.
Im nativen Aufbau ändert sich beim Folkeboot eine abgeleitete
Eingabeposition von `0.9420427299170873` auf `0.9420427299170874 m`,
also um `1.1102230246251565e-16 m`. Der exakt-bitgleiche Eingabevergleich
schlägt deshalb fehl; keine Referenzdatei wurde geändert.

Die separate [vorläufige Replayprüfung](Produktiv_2026-10-20_v3/replay_vorlaeufig.json)
erlaubt ausschließlich für Eingabepositionen/Quaternionen `atol=1e-12`.
Die physikalischen Hydrostatik-/Wasserliniengrenzen bleiben unverändert
bei `atol=1e-9`, skalare Modellgrößen bei `1e-10`. Schemas, Modellhashes,
Beladung und Prüfvorgaben werden weiterhin exakt verglichen.
Alle drei Modelle bestehen. Mutationstests erkennen falsche Hashes,
Kräfte, Positionen, Schemas und NaN.

## Performance: historischer 72-Fall-Zwischenstand

[72 Messfälle mit Rohzeiten](Produktiv_2026-10-20_v3/produktive_vergleiche.json)
und [Umgebung/Build-/Quellhashes](Produktiv_2026-10-20_v3/umgebung.json):
je ein Warm-up in beiden Pfaden, danach sieben uninstrumentierte
Wiederholungen in wechselnder Reihenfolge. Adapter, Konvertierungen,
Validierung und Ergebnisaufbau sind enthalten. Faktor = Python/C++,
also Werte kleiner eins sind Verschlechterungen.

| Übertragung | Optimist | Folkeboot | yacht1 |
|---|---:|---:|---:|
| Klassischer statischer Solver | 18.864 | 26.661 | 11.905 |
| Robuster statischer Solver | 18.785 | 27.209 | 11.914 |
| Meshvolumen | 3.287 | 1.948 | 1.775 |
| Meshfläche | 4.135 | 2.490 | 1.806 |
| Homogener Schwerpunkt | 4.469 | 2.730 | 2.692 |
| Schalenschwerpunkt | 4.964 | 3.101 | 3.107 |
| Homogene Trägheit | 10.954 | 6.519 | 5.593 |
| Schalenträgheit | 15.240 | 10.163 | 10.225 |

Statische Solverstarts liegen jeweils `0.001 m`/`0.001 rad` neben einem
unabhängig robust bestimmten Referenzgleichgewicht. Dies ist keine
Leistungsaussage über alle möglichen Starts oder Rollscan-Sonderfälle.
Der stationäre analytische Quaderfall misst beide Stufen einschließlich
des Newtonpfads der ersten Stufe: Faktor **42.757**, Median
`9879.80 → 231.07 µs`. Der zusätzliche echte 6D-Newtonfall ist separat
funktional geprüft, aber nicht in dieser Zeitangabe enthalten.

SLERP: Faktor **1.860**, `15.94 → 8.57 µs`.
Default-Achsenwinkelrotation: Faktor **0.918**, `7.80 → 8.50 µs`,
also leicht langsamer.
Die gesamte Anzeigeinterpolation mit 101 Samples ist ausdrücklich
**langsamer**: Faktor **0.0252**, `24.92 → 988.56 µs`, etwa 39.7-fache Zeit.
Ursache ist insbesondere die Konvertierung des gesamten Verlaufs in
native Zustandsrecords je Frame. Nach Nutzerauftrag bleibt der Pfad
trotzdem produktiv; dies ist kein behaupteter Anzeige-Performancegewinn.

Die Workerfaktoren oben messen sieben ganze 1000-Schritt-Aufrufe aus
gleichen Starts mit frisch vorbereitetem Kontext je Wiederholung.
Kontextaufbau ist separat gespeichert. Kein Prozesspool-/IPC-/GUI-
Gesamtvergleich und keine Fünf-Minuten-Liveabnahme.

## Build und Prüfungen des historischen Massen-Zwischenstands

Branch `v0.10`, Ausgangs-HEAD `7a955c2`, unveröffentlichter Arbeitsstand.
Release-Build, C++17, MSVC, `/fp:precise`, kein Fast-Math.
Geprüfter und in der Projektvenv installierter Wheel:
`build\native-massen-wheels\segelphysik_native-0.10.0-cp314-cp314-win_amd64.whl`,
SHA256 `88c66b7c742c6bf4d6f0be9191ebc9cebf43866ddb1ab36d67d5c35ec3622340`.

- Produktivsuite nach der dokumentierten Goldenaufteilung:
  **1111 bestanden, 1 vorhandener Windows-Symlink-Skip**.
- Danach ergänzt: sechs Replay-/Mutationstests bestanden;
  beide stationären Starts einschließlich echter 6D-Newtoniteration geprüft.
- Unveränderte separate strenge Batchsuite: **14 bestanden, 1
  fehlgeschlagen** (Optimist, erste Grenzüberschreitung `1.01024256e-9`
  gegenüber `1e-9`). Nicht als erfolgreich oder übersprungen gewertet.

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests code\cpp\tests\vertrag_native.py code\cpp\tests\paritaet_frames.py code\cpp\tests\paritaet_koerperkontext.py
.\.venv\Scripts\python.exe -m pytest -q code\cpp\tests\paritaet_batch.py
.\.venv\Scripts\python.exe werkzeuge\migration_replay.py --output <neue-jsondatei>
.\.venv\Scripts\python.exe werkzeuge\migration_worker.py --dauer 120 --output <neuer-messordner>
```

Der erste 30-s-Workerlauf scheiterte am NumPy-Testharness
(`assert_allclose` mit arrayförmigem `atol`); komponentenweise `isclose`
ersetzt diese nicht nutzbare Formatierung. Die Messordner
`Produktiv_2026-10-20` und `_v2` enthalten abgebrochene
Messharnessversuche wegen fehlender/falsch benannter Argumente.
Sie sind keine erfolgreichen Performancebelege; `_v3` ist vollständig.
Historische Messdaten wurden nicht überschrieben.

## Fortsetzung: Nachlauf, Interaktion, Wasser, Navigation und Selbstschnitt

Dieser inzwischen historische Produktivstand ersetzte den Massen-Build:
`build\native-meshpruefung-wheels\segelphysik_native-0.10.0-cp314-cp314-win_amd64.whl`,
SHA256 `e9cf11e3cdefefab9ce5b3d2e7b09ad156d159c701c8db0f07183006a0fb2220`.
Dieses Wheel ist in Test- und Projektumgebung installiert.
Die vollständige Produktivsuite dieses Zwischenstands ergibt **1156 bestanden,
1 vorhandener Windows-Symlink-Skip**, keine Fehler; JUnit:
`build\v010-produktiv-2026-10-20-v6.xml`.
Das Funktionsinventar wurde nach der Selbstschnittübertragung neu erzeugt.

Zusätzlich produktiv und funktional geprüft:

- Stationärer dynamischer Nachlauf als ganzer nativer, GILfreier Block
  ohne Pythonkraftcallbacks. Historische Euler-Hydrostatikreduktion,
  eigenes Modellgewicht auch bei abweichender Integratormasse, Added Mass,
  Restzeitschritt und Halbzeitdiagnostik bleiben erhalten.
- Kontaktstart, Stoßpose, Projektion, priorisierte Lösungsauswahl und
  vereinfachter SI-Integrationskern. Überschriebene Kraftcallbacks von
  Modellsubklassen bleiben explizite Erweiterungspfade; sie werden nicht
  versehentlich durch eine native Standardkraft ersetzt.
- Ganze Navigations-/Kamerawertableitung, Winkel-Wrapping und
  16-Punkt-Kompassrichtung. Ungültige Anzeigewerte bleiben `None`.
- Deterministische Wasserhashes, Punktlagen, gesamtes Punktfeld,
  Spurarrays/-transparenz und Dunstgeometrie. Auflösung, Reihenfolgen,
  RGBA und negative Gitterkoordinaten sind unverändert geprüft.
- Gesamte Sweep-and-prune-Selbstschnittprüfung mit koplanaren und
  Segment-Dreieck-Prädikaten. 1000 zufällige Fünfdreiecksmeshes,
  einschließlich koplanarer und weit verschobener Fälle, liefern
  denselben ersten Fehlerpaarindex wie der Referenz-Batchalgorithmus.
  Python- und C++-Cachefreigaben sind getrennt.

Die **96 Messfälle dieses Zwischenstands** stehen mit Rohzeiten unter
[Produktiv v6](Produktiv_2026-10-20_v6/produktive_vergleiche.json),
die Build-/Quellhashes unter
[Umgebung v6](Produktiv_2026-10-20_v6/umgebung.json).
Messverfahren weiterhin ein Warm-up und sieben wechselnde Wiederholungen
einschließlich öffentlicher Adapter. Frühere v3/v4/v5 bleiben historische
Zwischenstände; v4 hatte unpräzise gemeinsame Eingabemetadaten, die in
v5/v6 pro Fall korrigiert sind.

| Neu gemessener Block | Median Python → C++ in µs | Faktor Python/C++ |
|---|---:|---:|
| Stationärer 1-s-Nachlauf, analytischer Quader | 172771.600 → 935.600 | 184.664 |
| Navigationswerte | 27.991 → 14.073 | 1.989 |
| Dunstgitter | 3011.582 → 280.816 | 10.724 |
| Wasserpunktfeld, Punkte | 62.609 → 12.034 | 5.202 |
| Wasserpunktfeld einschließlich vollem Spurverlauf | 126.624 → 105.298 | 1.203 |
| 1000 periodische Punktlagen | 57.260 → 30.834 | 1.857 |
| Stationäre Eulerrotation | 4.748 → 6.313 | 0.752 |
| Störrotation | 5.386 → 8.261 | 0.652 |
| Stoßpose | 6.793 → 7.208 | 0.942 |
| Projektion | 0.693 → 6.191 | 0.112 |
| Lösungsauswahl | 0.731 → 6.331 | 0.115 |
| Winkel 360 | 0.207 → 5.716 | 0.036 |
| Winkel ±180 | 0.244 → 5.710 | 0.043 |
| 16-Punkt-Richtung | 0.281 → 5.636 | 0.050 |
| Hash, 1000 Gitterzellen | 18.219 → 31.672 | 0.575 |

| Modellabhängiger Block: Faktor Python/C++ | Optimist | Folkeboot | yacht1 |
|---|---:|---:|---:|
| Kontaktstart einschließlich Hydrostatik | 13.879 | 13.292 | 15.081 |
| Vereinfachter SI-Schritt einschließlich Kraftadapter | 4.507 | 3.494 | 5.137 |
| Kalte Selbstschnittprüfung | 64.603 | 44.982 | 129.990 |

Bei der Selbstschnittmessung wird der Cache vor **jedem** Aufruf unter
seinem Lock geleert; dieser Aufwand ist enthalten. Das misst den ganzen
Prüfalgorithmus, keinen warmen Cachehit. Die kleinen skalaren Adapter
sind teils erheblich langsamer, bleiben aber auf Nutzerauftrag produktiv.
Keine Ableitung einer GUI-/IPC-/Livegesamtleistung aus diesen Faktoren.
Die ursprünglichen strengen Batch-/Replayabweichungen oben bleiben
offene Genauigkeitsschulden, nicht als bestanden umgedeutet.

## Fortsetzung: Kraft-, Wasser- und Körpergrafik; Zwischenstand v8

Dieser Zwischenstand wurde produktiv installiert und vollständig geprüft:
`build\native-grafikgeometrie-wheels\segelphysik_native-0.10.0-cp314-cp314-win_amd64.whl`,
SHA256 `06022734be8cd434e1c81d272dc0799e5dd736668e133bd25ff10e4604699ea9`.
**1239 bestanden, 1 vorhandener Windows-Symlink-Skip**, keine Fehler;
JUnit `build\v010-produktiv-2026-10-20-v8.xml`.
Die [125 aktuellen Adaptermessfälle](Produktiv_2026-10-20_v8/produktive_vergleiche.json)
und [Build-/Quellhashes](Produktiv_2026-10-20_v8/umgebung.json)
ersetzen die früheren Zwischenstände bis zur folgenden Kamerafortsetzung.

Neu produktiv: beide Pfeilgeometrien, beide Paarmomente, Skala,
Gewicht-/Auftriebs- und Zusatzpfeile, beide Momentbogenadapter, gesamte
Strichlinieninterpolation und gesamte Wirkungsliniensuche einschließlich
Welttransformation. Hauptachsen werden nativ sortiert und kanonisiert;
der bestehende native NumPy-Eigenlöser bleibt unverändert erhalten.
Je 1000 Zufallsfälle für Pfeile/Momente, je 1000 Bögen pro Achse,
1000 Wirkungslinien, 1003 Tensoren sowie doppelte Linienstützpunkte,
Null-/Fehlerfälle und unabhängige Ausgabe-Arrays sind geprüft.

Neu produktiv: Oberflächentriangulierung, bilineare Verfeinerung,
Wassergrundformen und gesamte vorhandene Wasseraufbereitung mit bis zu
25 Lochfüllrunden, Medianrestfüllung, lokalem Neunermedian, unveränderter
Spitzenkappung und Laplace-Durchläufen. Die Lochmaske ist hier
absichtlich Teil des bisherigen Renderereingabevertrags, keine
freigegebene nichtendliche Physik. Rasterwerte stimmen in den gezielten
Prüfungen exakt überein, auch bei einzelnen Zeilen/Spalten, Strides und
Restlöchern nach 25 Runden. Kreise sind bis `1e-15` geprüft.
Gesichterreihenfolge, Auflösung und der identische Rückgabewert bei
Verfeinerungsfaktor eins bleiben erhalten.

Neu produktiv: alle drei Farbgruppenpfade einschließlich verschachtelter
Gelenktransformationen, benetzte Sammelgeometrie, Dreieckszellen und
gesammelte statische Punkttransformationen. Farbnamen, Glanz, Blatt-IDs,
Sichtbarkeit und Aktualisierungsregeln bleiben unverändert.
Alle drei Bootmodelle einschließlich Gelenkänderungen und generische
verschachtelte Körper sind geprüft; versteckte Körper aktualisieren
weiterhin keine Gruppen-/Overlayactors.

Der erste Gesamtlauf (v7) erkannte einen echten Adapterfehler bei leeren
Punktmassen: zu früher Zugriff auf deren nicht erforderlichen
Eingabeschwerpunkt. Vor der Datenvorbereitung werden diese Blätter nun
wie bisher ausgelassen. Keine Toleranzlockerung; danach 14 gezielte Fälle
und die gesamte v8-Suite bestanden. Der fehlgeschlagene JUnit-Nachweis
bleibt als `build\v010-produktiv-2026-10-20-v7.xml` erhalten.

| Neuer Block | Median Python → C++ in µs | Faktor Python/C++ |
|---|---:|---:|
| Pfeildaten | 4.750 → 8.434 | 0.563 |
| Pfeil mit festen Maßen | 5.190 → 13.564 | 0.383 |
| Auftriebspaarmoment | 15.086 → 9.768 | 1.544 |
| Allgemeines Kraftpaarmoment | 14.870 → 8.398 | 1.771 |
| Skala | 0.270 → 10.148 | 0.027 |
| Gewicht-/Auftriebspfeile | 15.072 → 22.770 | 0.662 |
| Zusatzpfeile | 15.534 → 23.154 | 0.671 |
| Rollmomentbogen | 17.746 → 9.066 | 1.957 |
| Allgemeiner Achsmomentbogen | 17.546 → 8.894 | 1.973 |
| Strichlinien | 734.654 → 17.686 | 41.539 |
| Wirkungslinie, Einheitsquader | 129.602 → 56.760 | 2.283 |
| Hauptachsen einschließlich NumPy-Eigenlöser | 17.058 → 14.684 | 1.162 |
| Einzelne Achsenkanonisierung | 2.556 → 7.678 | 0.333 |
| Polydatenadapter einschließlich PyVista-Objekt | 54.293 → 58.886 | 0.922 |
| Dreieckspolydaten einschließlich PyVista-Objekt | 50.393 → 57.869 | 0.871 |
| Wasseroberflächenobjekt | 135.043 → 123.547 | 1.093 |
| Bilineare Wasserverfeinerung | 199.667 → 58.587 | 3.408 |
| Einheitskreis | 6.150 → 7.033 | 0.874 |
| Einheitsquadrat | 1.037 → 6.473 | 0.160 |
| Wasseraufbereitung, Löcher/Median/Laplace | 1292.947 → 96.427 | 13.409 |

| Modellabhängiger Block: Faktor Python/C++ | Optimist | Folkeboot | yacht1 |
|---|---:|---:|---:|
| Ganze Farbgruppenvorbereitung | 0.811 | 0.924 | 0.898 |
| Benetzte Sammelgeometrie einschließlich Snapshotadapter | 0.151 | 0.210 | 0.147 |
| Statische Sammeltransformation | 0.705 | 0.652 | 0.505 |

Diese Verschlechterungen werden nicht verschwiegen oder zurückgeschaltet.
Insbesondere beinhaltet die benetzte Geometrie weiterhin den öffentlichen
Snapshot-/Prüfadapter; dies ist kein reiner C++-Kernvergleich.
Die statische Sammelmessung schließt Actor-/Overlayausgabe **ausdrücklich
aus** und weist dies im jeweiligen Messfall aus. Sie ist kein
Rendering-/GUI-Gesamtnachweis. Arrays, Topologie und Metadaten sind geprüft;
die vollständige sichtbare Optik-/Liveabnahme steht weiterhin aus.

## Fortsetzung: Kamera und Instrumente; Zwischenstand v9

In diesem Zwischenstand in Projekt- und Prüfumgebung installiert:
`build\native-instrumente-wheels\segelphysik_native-0.10.0-cp314-cp314-win_amd64.whl`,
SHA256 `efdcaf9351beb92580508ae7d3d20ba33715deed33bf457f9553cce29ac71e11`.
**1258 bestanden, 1 vorhandener Windows-Symlink-Skip**, keine Fehler;
JUnit `build\v010-produktiv-2026-10-20-v9.xml`.
Aktuell **134 Messfälle** mit Rohzeiten:
[Produktiv v9](Produktiv_2026-10-20_v9/produktive_vergleiche.json),
[Umgebung v9](Produktiv_2026-10-20_v9/umgebung.json).

Die gesamte Kamera-Folgegeometrie einschließlich Initiallage,
Objektwechsel, optionalem Heading, vertikaler Ansicht, gespeichertem
Offset, Kameraoben-Projektion und unverändertem `1e-9`-No-op-Vergleich
läuft nativ. Auch die manuelle Kameralageableitung ist nativ. Observer,
Busy-Schutz, Qt-/VTK-Setter und Vordergrund-Kameraidentität bleiben
Objektadapter; keine zusätzliche Glättung oder Frequenzänderung.
Fünf Ausgangsansichten mit je 1000 Folgeschritten und 1000 manuelle
Änderungen sind gegen die Referenz geprüft. Undefinierte Ausgangsansicht
liefert weiterhin keine Kameralage; eine gültige gespeicherte Pose kann
wie zuvor einen ungültigen aktuellen Kamerastand ersetzen.

Instrumentwinkel, Warnungsentscheidung, Kompassrundung,
Kameraindikatorwinkel, Geschwindigkeitseinheiten und gemeinsame
SVG-Zielrechtecke rechnen nativ. XML-Attribute/-Serialisierung,
Textformatierung und Qt-SVG-Rendering bleiben bestehende Adapter.
`_fehlerkreis` und `_gefahrenring` erzeugen unveränderte statische
XML-Elemente ohne numerischen Hotspot; kein Neuschreiben der vorhandenen
nativen Qt-Painting- oder Vordergrund-Kameraoperationen.
Für alle drei Instrumenttypen stimmen die SVGbytes einschließlich
Null-/Fehler-/Warnungsgrenzen exakt überein. Je drei unterschiedliche
Fensterseitenverhältnisse liefern zudem **exakt identische Pixelbilder**.
Geschwindigkeitsfehler und Platzhalter bleiben unverändert.
1000 Rahmen-/Einheitenfälle sind exakt geprüft.

| Neuer Block | Median Python → C++ in µs | Faktor Python/C++ |
|---|---:|---:|
| Ganze Kamera-Folgegeometrie einschließlich VTK-Setter/Observer | 67.931 → 39.195 | 1.733 |
| Manuelle Kameralageableitung | 6.759 → 8.331 | 0.811 |
| Kompass einschließlich XML/Qt-SVG | 1051.495 → 913.020 | 1.152 |
| Krängungsinstrument einschließlich XML/Qt-SVG | 1621.280 → 1720.755 | 0.942 |
| Stampfinstrument einschließlich XML/Qt-SVG | 1053.285 → 925.830 | 1.138 |
| Geschwindigkeitswidget einschließlich XML/Qt-SVG | 192.200 → 222.545 | 0.864 |
| Alle vier Anzeigen gemeinsam | 2533.790 → 2691.660 | 0.941 |
| Gemeinsamer SVG-Rahmen | 0.378 → 9.903 | 0.038 |
| Geschwindigkeitseinheiten | 0.201 → 9.407 | 0.021 |

Die gemeinsame Anzeigenmessung ist damit ca. **6.23 % langsamer**.
Sie ist nicht als Gesamtgewinn dargestellt; Streuung und Einzelrohzeiten
stehen im Messdatensatz. Diese Anzeigenmessungen enthalten XML- und
Qt-SVG-Aufbereitung, aber **kein Paint-Event**. Kameramessungen enthalten
echte VTK-Kamera-/Observeroperationen, aber keinen Renderframe.
Die separaten Pixelvergleiche ersetzen keine vollständige Liveabnahme.
Die ursprünglich fehlende lokale QApplication-Testfixture wurde im
Prüfharness ergänzt; keine Produktionsfallbacks oder Toleranzlockerung.

## Fortsetzung: Grundformen, Polyeder und OBJ; aktueller Stand v11

In Projekt- und Prüfumgebung installiert:
`build\native-polyeder-wheels\segelphysik_native-0.10.0-cp314-cp314-win_amd64.whl`,
SHA256 `f9a7bab65e2687ba3b26594e5ab1057df0aa5269491cef49ad647e849c67f44f`.
**1285 bestanden, 1 vorhandener Windows-Symlink-Skip**, keine Fehler;
JUnit `build\v010-produktiv-2026-10-20-v11.xml`.
**154 vollständige Adaptermessfälle** mit je sieben wechselnden
Wiederholungen und einem Warm-up pro Pfad:
[Produktiv v11](Produktiv_2026-10-20_v11/produktive_vergleiche.json),
[Umgebung v11](Produktiv_2026-10-20_v11/umgebung.json).
Historische Rohdaten bleiben unverändert.

Alle Grundformen einschließlich Platte und Sechskantspitze, Ring,
Formvolumenschwerpunkt, Zentrierung und Liegendtransformation laufen
produktiv nativ. Die Formschwerpunkt-Nullvolumenschwelle bleibt `1e-18`.
Auch Polyederfächer, vollständige Konvexhüllenkandidatensuche,
Ebenengruppierung, Winkelprojektion und abschließende Orientierung
sind nativ. Die vorhandene native NumPy-`argsort`-Sortierung bleibt
explizit erhalten; keine neue Hüllbibliothek, Näherung oder andere
Dreiecksreihenfolge.

OBJ-Selbstschnitt, Planarität/Projektion, vollständige Ohrtriangulierung
und Skalierung vor Rotation laufen nativ. Datei-/Schema-/Indexadapter
und präziser Datei-/Zeilenfehlerkontext bleiben Python.
Triangulierung liefert weiterhin eine Liste von Tupeln. Referenz- und
Produktivpfad besitzen getrennte OBJ-Cacheeinträge.
Zufällige Grundformen, 103 Hüllgeometrien, exakte Face-Reihenfolgen,
1000 Polygontriangulierungen und 1000 Polygon-Selbstschnittfälle sind
gegen die Referenz geprüft; Punkte mit `atol=2e-12`, Indizes exakt.
Für diesen Übertragungsblock wurde keine weitere Prüfung gelockert.

Der erste Gesamtlauf v10 ergab 1284 bestandene Tests, einen Skip und
einen Fehler: Das abgeleitete Funktionsinventar enthielt noch die alten
Quellpositionen. Nach Regenerierung besteht die gesamte Suite v11.
Kein Fachfehler wurde übersprungen oder zum Erfolg umgedeutet.

| Neuer Block | Median Python → C++ in µs | Faktor Python/C++ |
|---|---:|---:|
| Kegel, 64 Segmente | 22.370 → 12.060 | 1.855 |
| Quader | 6.610 → 11.580 | 0.571 |
| Pyramide | 4.325 → 8.070 | 0.536 |
| Kugel, 64 Segmente | 2481.150 → 118.885 | 20.870 |
| Zylinder stehend, 64 Segmente | 223.610 → 35.040 | 6.382 |
| Zylinder liegend, 64 Segmente | 94.295 → 17.640 | 5.346 |
| Platte | 13.410 → 19.045 | 0.704 |
| Sechskant | 62.210 → 10.850 | 5.734 |
| Sechskant mit Spitze, liegend | 67.145 → 11.150 | 6.022 |
| Ring, 64 Segmente | 8.394 → 8.417 | 0.997 |
| Formvolumenschwerpunkt | 23.282 → 14.828 | 1.570 |
| Formzentrierung | 26.901 → 14.921 | 1.803 |
| Liegendtransformation | 3.317 → 7.947 | 0.417 |
| Polyederhülle, 8 Punkte | 4371.700 → 188.900 | 23.143 |
| Polyederhülle, 24 Punkte | 46758.300 → 713.800 | 65.506 |
| Polyederhülle, 64 Punkte | 1385244.500 → 17698.700 | 78.268 |
| Polyeder mit sechs expliziten Vierecken | 36.125 → 30.559 | 1.182 |
| Polygon-Selbstschnitt, 32 Punkte | 2199.560 → 11.865 | 185.382 |
| Konkave OBJ-Ohrtriangulierung, 32 Punkte | 3592.640 → 27.905 | 128.745 |
| OBJ-Import, kalter Anwendungscache | 6165.635 → 1158.150 | 5.324 |

Kleine Primitive, Platte und Liegendtransformation verschlechtern sich;
der Ring zeigt keinen Gewinn. Alle bleiben auf Nutzerauftrag produktiv.
Die OBJ-Gesamtmessung enthält Cacheleeren, Dateilesen/-parsen,
Triangulierung, Transformation, Validierung und unveränderliches Mesh.
Der Betriebssystem-Dateicache wird nicht geleert; dies ist kein
Kaltstart-/Datenträgerbenchmark und kein warmer Anwendungscachehit.
Keine Faktoren zu einem Gesamtgewinn addieren; kein Live-/Rendernachweis.
Die Langzeit-/Replaybelege älterer Builds gelten nicht automatisch für
dieses neue Wheel und sind aktuell erneut auszuführen.

## Weiterhin zu erledigen

Kein Gesamtabschluss der 20 Umsetzungsschritte:
vollständige Einzelfunktionsabnahme M2–M4 und vollständige stationäre Sonderfallabnahme,
schwierige native Solverfehler-/Neutralitäts-/Rollscanfälle, übrige
Validierungs-/Formerkennungs-/Vermessungspfade, übrige Actor-/Overlayaufbereitung,
vollständige Instrument-/Kameraabnahme,
vollständige Bewegungs-/Kontaktabnahme, optionale Voxel-/GPU-Bestandspfade sowie
vollständige aktuelle Live-/Speicher-/Optik-/End-to-End-Abnahme und
Abschlussmatrix stehen noch aus. Die Nutzerfreigabe zur Numeriklockerung
macht diese Arbeiten nicht automatisch abgeschlossen.

## Fortsetzung v15: Wasser-/Voxelkerne und Abnahme

### Umfang und Fehlerkorrektur

Nach dem abgebrochenen v14-Messversuch war `auftrieb` im Modulimport von
`migration_produktiv.py` nicht importiert, obwohl neue Voxel-Messfälle
`auftrieb._y_intervalle_saeule_v` aufriefen. Der Import wurde ergänzt.
Der unvollständige Ordner v14 wurde nicht verändert; der vollständige
erneute Lauf schrieb nach
[Produktiv_2026-10-20_v15](Produktiv_2026-10-20_v15/produktive_vergleiche.json).
Er enthält **162 Fälle** (v12: 157), je sieben uninstrumentierte
Wiederholungen nach Warmup und mit wechselnder Reihenfolge. Das
Umgebungsmanifest verweist auf den vorhandenen v14-JUnit-Nachweis und
speichert dessen SHA256; der v15-Vergleich selbst ist kein zusätzlicher
JUnit-Lauf.

Wheel-/Umgebungsbeleg: Python 3.14.8, Windows 11, MSVC 19.44.35229.0,
Release-Build, natives Modul
`_segelphysik_native.cp314-win_amd64.pyd`, SHA256
`e6946a4d8f742a99e28aff7a0c0fcaaff66ae68458c8b5821d4b495fcf38814a`.
Rohvergleich SHA256
`e5cb65ff6a7d85f33674ac3ca173d6cad5c0f37382861d0332e9a61394afae89`;
Umgebungsmanifest SHA256
`4aef9cb7b4f02b499e9ac18391e512f8786b748f02d3c1404843d2a0afc392cb`.

### Neue produktive Messfälle

Faktor = Python-Median / C++-Median; Werte unter eins sind langsamer:

| Funktion/Elternblock | Faktor | Aussage |
|---|---:|---|
| `IsoSurfaceWater._mirrored` | 2,591 | Spiegelung von 250 Partikeln nativ |
| `IsoSurfaceWater.splat` ohne Marching Cubes | 7,455 | Splatting einschließlich float32-Gewichte, Aggregation und Randkopie |
| `IsoSurfaceWater._calibrate` | 0,239 | C++ rund 4,19x langsamer; bleibt auf Nutzerauftrag produktiv |
| Voxelpose, `auswerten` | 37,375 | 1000 Voxelzentren, vorbereiteter Körperkontext |
| Voxelpose, `auswerten_6dof` | 22,215 | Translation und Quaternion |
| Voxelmodell vorbereiten und erste Pose | 2,608 | Validierung, Raster, native Kopie und erste Auswertung enthalten |
| Säulenintervalle im Koerpermit-Pfad | 2,338 | Pythonadapter und Arrayschnittstelle enthalten |
| Gesamter Unterwasser-Rasterpfad | 3,402 | Schnitt, Raster, Intervalle, Vereinigung und Schwerpunkt |

Diese Faktoren sind keine Gesamtleistungswerte. Der Isoflächenbenchmark
schließt PyVista-Marching-Cubes ausdrücklich aus. Der gesamte Rasterfall
verwendet ein kleines analytisches Mesh und belegt keine vollständige
Modell-/Pose-Genauigkeitsmatrix.

### Aktuelle Regression, Replay und numerische Diagnose

Nach der Importkorrektur lief die vollständige Suite auf dem aktuellen
Arbeitsstand:

```text
1171 passed, 1 skipped
SKIPPED tests/test_mesh.py:229: Symlinks sind in dieser Windows-Umgebung nicht verfügbar
```

Zusätzlich bestanden **8 gezielte OpenCL-Tests** (27 nicht ausgewählt).
Die OpenCL-Prüfung fand eine tatsächlich verfügbare AMD-GPU `gfx1103`
mit fp64-Unterstützung; es handelte sich nicht nur um einen gemockten
Gerätetest.

Der aktuelle eingefrorene Replay besteht vorläufig. Die unveränderte
strenge Replayprüfung bleibt fehlgeschlagen, weil die Folkeboot-
Eingabeposition weiterhin um `1.1102230246251565e-16 m` abweicht.
Die gelockerte Eingabetoleranz bleibt auf `1e-12`; die physikalischen
Hydrostatikgrenzen bleiben `1e-9` und wurden nicht gelockert.
[Replaydaten](Produktiv_2026-10-20_v15/replay_vorlaeufig.json).

Die erneute 1000-Schritt-Strengdiagnose besteht nicht für alle Modelle:

| Modell | Max. Zustandsabweichung | Max. Kraftfeldabweichung | Grenze |
|---|---:|---:|---|
| Optimist | `1.0303820297e-11` | `1.03769249193e-7` | Streng `1e-12` / `1e-9` verfehlt |
| Folkeboot | `5.55111512313e-16` | `1.81898940355e-11` | Beide strengen Grenzen bestanden |
| yacht1 | `3.1918911958e-16` | `2.72848410532e-12` | Beide strengen Grenzen bestanden |

Der Batch-Diagnoselauf endete deshalb erwartungsgemäß mit Exitcode 1.
Er wurde nicht als erfolgreicher Produktivbatch oder als vorläufige
Genauigkeitsfreigabe umgedeutet. Rohdaten und Umgebung liegen unter
[Batch_Numerik_Diagnose_2026-10-20_v15](Batch_Numerik_Diagnose_2026-10-20_v15/umgebung.json).

Die drei unabhängigen 120-s-Workerfolgen (je 30.000 Schritte) bestanden
die bestehende vorläufige Zustands-/Kraftgrenze:

| Modell | Max. Zustand | Max. Kraft-/Momentfeld | Batchfaktor Python/C++ |
|---|---:|---:|---:|
| Optimist | `2.6449678e-12` | `9.41435874e-10` | 31,589 |
| Folkeboot | `6.16900871e-7` | `0.269893421` | 54,559 |
| yacht1 | `7.86697096e-15` | `2.35615971e-11` | 20,105 |

Feldmaxima haben gemischte SI-Einheiten und sind kein einzelner
Positionsfehler. Die Folkebootabweichung bleibt sichtbar und ungelöst.
Rohfolgen: [Optimist](Worker_120s_2026-10-20_v15/optimist.json),
[Folkeboot](Worker_120s_2026-10-20_v15/folkeboot.json),
[yacht1](Worker_120s_2026-10-20_v15/yacht1.json).

### Sichtbare Live-GUI: drei Hydrostatikpfade

Jeder Lauf nutzte `yacht1`, Windows-QPA, 30 s Warmup und rund 60 s Messung,
Lifecyclephasen (Pause/Fortsetzung/Statik/Echtzeit), Eingabeprobe und
sekündliche Working-Set-Messung. Die GUI wurde sichtbar aufgebaut; je
Pfad ist ein Screenshot abgelegt.

| Backend | Renderaufrufe/s | Abgeschlossene Frame-Events/s | Physikbatch Median | Simulationszeit / Wandzeit | Max. Rückstand | Eingabelatenz-Median | Max. GUI Working Set |
|---|---:|---:|---:|---:|---:|---:|---:|
| `exakt_union` | 23,40 | 14,61 | 3,499 ms | 0,934 | 0,978 s | 49,068 ms | 611,9 MiB |
| `voxel_koerperfest` | 24,78 | 16,16 | 26,155 ms | 0,909 | 1,517 s | 50,302 ms | 603,7 MiB |
| `voxel_opencl` | 25,32 | 17,48 | 31,637 ms | 0,910 | 2,634 s | 47,878 ms | 747,4 MiB |

Alle drei Messläufe sind als gültig markiert, ohne protokollierte Fehler;
alle 59 Eingabeproben pro Lauf reagierten. Speicherzeitreihen enthalten
60 Stichproben je Prozess: Worker-Maximum 44,9 MiB (exakt), 43,7 MiB
(CPU-Voxel) und 176,5 MiB (OpenCL); die letzte Zahl umfasst GPU-/OpenCL-
Puffer im Workerprozess.

Die Lifecyclewechsel wurden ausgeführt. Bei `voxel_opencl` blieb die
Überlastbeobachtung während Fortsetzung und Echtzeit aktiv; der
Simulationsdurchsatz lag bei rund 0,91 s Simulation pro Wandsekunde und
der Rückstand erreichte 2,634 s. Das ist ein erfolgreicher Messlauf, aber
kein Nachweis eines rückstandsfreien Echtzeitbetriebs.
`tatsaechlich_praesentierte_fps` und Scanout-Zeitpunkt sind bei allen
Läufen nicht verfügbar. Die Frame-Event-Raten dürfen daher nicht als
Monitor-FPS ausgegeben werden. Auch sind 60-s-Läufe keine vollständige
10-minütige Live-/Optikabnahme und enthalten keinen visuellen
Python-Referenzscreenshot.

Berichte und Bildnachweise:

- [exakt_union JSON](Live_GUI_2026-10-20_v15_exakt_union.json),
  [Screenshot](Live_GUI_2026-10-20_v15_exakt_union.png)
- [voxel_koerperfest JSON](Live_GUI_2026-10-20_v15_voxel_cpu.json),
  [Screenshot](Live_GUI_2026-10-20_v15_voxel_cpu.png)
- [voxel_opencl JSON](Live_GUI_2026-10-20_v15_voxel_opencl.json),
  [Screenshot](Live_GUI_2026-10-20_v15_voxel_opencl.png)

### Noch offene Abnahmen

Der v15-Nachweis schließt weder U-V0.10-000019 noch U-V0.10-000020 ab.
Offen bleiben insbesondere die vollständige M2–M4-Einzelfunktionsparität,
die strenge Optimist-Batchabweichung, Solver-Sonderfälle, allgemeine
Topologie-/Formerkennung und Modellvermessung, übrige Actor-/Overlay-
Numerik, vollständige Instrument-/Kamera- und Optikmatrix, PyVista-/
Qt-Objektpfade, die systematische Voxelgenauigkeitsmatrix sowie
Langzeit-/Speicher-/End-to-End-Wiederholungen. Die getestete GPU macht
keine Aussage über andere Geräte oder alle physikalischen Eingaben.

## Fortsetzung v16: Hauptachsen-Overlay

Der numerische Teil von `_overlays_aktualisieren` für Hauptachsen wurde
weiter in den produktiven C++-Pfad überführt. Neu nativ sind die
Richtungsrotation gemäß bestehender Python-Auswertungsreihenfolge,
Punktprojektionen und die daraus abgeleiteten Achsenlängen. Eigenwert-
und Eigenvektorberechnung bleibt bei NumPy; VTK-Matrix- und Actorverwaltung
bleiben Bibliotheksadapter. Die native Funktion ist ein Pflichtsymbol des
Backends, ein stiller Fallback ist ausgeschlossen.

**Parität und Regression**

- 200 reproduzierbare zufällige Punkt-/Rotationsfälle einschließlich
  leerer Punktmengen; Richtungen und Längen stimmen bei `atol=2e-12`.
- `tests/test_native_grafikgeometrie.py`,
  `tests/test_native_backend.py` und
  `tests/test_grafik_bruecke_darstellung.py`: **24 bestanden**.
- Vollständige Suite nach Einbindung und Inventarregenerierung:
  **1172 bestanden, 1 vorhandener Skip** (Windows-Symlinkberechtigung),
  JUnit `build/v010-produktiv-2026-10-20-v16.xml`.
- V16 enthält 165 uninstrumentierte Messfälle; das native Overlay ist
  langsamer:

| Modell | Median Python | Median C++ | Faktor Python/C++ |
|---|---:|---:|---:|
| Optimist | 12,840 µs | 37,975 µs | 0,338 |
| Folkeboot | 14,720 µs | 37,630 µs | 0,391 |
| yacht1 | 14,440 µs | 50,640 µs | 0,285 |

Der C++-Aufruf einschließlich Adapter ist rund 2,56–3,51x langsamer.
Aufgrund der expliziten Nutzerfreigabe bleibt er dennoch produktiv; dies
ist kein Leistungsgewinn. Die Nebenmessungen aus v16 sind nicht zu den
v15-Messwerten addiert. Wheel-SHA256
`e4fdf4420046d7a110f10bdd0425b437b2578b85178a83d47115e64298807ac4`,
geladene native Binärdatei SHA256
`70ea30be3f19bf9d332288a68f3f3e6a0f1b5814cc92f3f246507c8fae1b526b`.
JUnit-SHA256 `2bdeaf58f189e5aaf10e0b839153340e17d9b36a6e9e35b47052b0d5ccdbe5fe`.

Die im selben v16-Lauf wiederholten Wasser-/Voxel-Fälle ergaben:

| Funktion | Python/C++ |
|---|---:|
| IsoSurfaceWater-Spiegelung | 3,029 |
| IsoSurfaceWater-Splatting | 9,216 |
| IsoSurfaceWater-Kalibrierung | 0,279 |
| Voxelpose, `auswerten` | 53,311 |
| Voxelpose, `auswerten_6dof` | 13,907 |
| Voxelmodell vorbereiten und erste Pose | 1,919 |
| Säulenintervalle | 3,880 |
| Gesamter Unterwasser-Rasterpfad | 3,162 |

Die deutlich voneinander abweichenden Wiederholungen v15/v16 bleiben
getrennt, nicht gemittelt; sie sind Hinweise auf Messstreuung und kein
stabiler allgemeiner Beschleunigungsfaktor.

**Sichtbarer Lauf mit der aktuellen Erweiterung**

`yacht1`, `exakt_union`, Windows-QPA, 30 s Warmup und 60,092 s Messung,
Lifecycle, Speichererfassung und Screenshot:

- Bericht als gültig markiert, keine Fehler; 60/60 Eingaben reagierten.
- 23,56 Renderaufrufe/s und 14,79 abgeschlossene Frame-Events/s.
  Präsentierte Monitor-FPS und Scanout bleiben nicht nachgewiesen.
- 848 Physikbatches, 0,932 Simulationssekunden pro Wandsekunde,
  maximaler Rückstand 0,984 s.
- 61 Speicherstichproben; Lifecycle Pause/Fortsetzung/Statik/Echtzeit
  ohne Programmfehler.

Rohdaten: [v16 Produktivvergleich](Produktiv_2026-10-20_v16/produktive_vergleiche.json),
[Umgebung](Produktiv_2026-10-20_v16/umgebung.json),
[GUI-Bericht](Live_GUI_2026-10-20_v16_exakt_union.json) und
[Screenshot](Live_GUI_2026-10-20_v16_exakt_union.png).
Der [Funktionsinventarstand](../Umsetzungsplan/Funktionsinventar_V0.10.json)
wurde regeneriert, nachdem der neue Grafikcode die Quellzeilen verschoben
hatte.

Dieser Teilnachweis reduziert den offenen U-V0.10-000014-Umfang, schließt
aber weder den übrigen Actor-/Overlay-/Optikvertrag noch U-V0.10-000019
oder U-V0.10-000020 ab. Die geringere Geschwindigkeit wird nicht
verschwiegen oder als Erfolg umetikettiert.

## Abschlussprüfung und Nutzerentscheidung vom 20.10.2026

Die strenge Optimist-Batchabweichung darf nach ausdrücklicher
Nutzerentscheidung beim V0.10-Abschluss ignoriert werden. Sie ist damit
eine akzeptierte Abschlussausnahme, keine bestandene strenge Parität.
Die historischen Messungen und Fehlerwerte oben bleiben unverändert.
Dies ist keine pauschale Freigabe anderer fehlender Abnahmen.

Aktueller Abschlusstest: **1172 bestanden, 1 vorhandener Windows-Symlink-Skip**
in 49,18 s. Expliziter C++-Replay erneut vorläufig bestanden; die strenge
Folkeboot-Eingabeparität scheitert weiterhin an ca. `1,11e-16`.
Alle 57 v16-Quellhashes und die native Binärdatei stimmen noch mit dem
aktuellen Stand überein. Es wurde keine neue Performance-/Liveabnahme
ausgeführt. Die 165 v16-Fälle sind mit Einzelzeiten, P95, Faktor und
Nachweisen in der
[Abschlussbilanz](Abschlussbilanz_V0.10_2026-10-20.md)
zusammengeführt und im
[CPPI-Einzelregister](../../../Revisionsinformation/Schnittstellenregister_CPP.md)
als Python-/V0.10-Adapterwerte bzw. ausdrücklich nur als Elternblock
zugeordnet. Nicht separat gemessene Interfaces bleiben gekennzeichnet.
Die Abschlussbilanz nennt die übrigen Implementierungs- und Abnahmegrenzen;
der ursprüngliche Gesamtplan ist noch nicht vollständig erfüllt.

**Nachfolgende ausdrückliche Nutzerfreigabe:** V0.10 wird als begrenzter
Versionsstand abgeschlossen. Die übrigen Restarbeiten sind im
[Backlog nach A-Kennung](../../../../Backlog/Restarbeiten_V0.10.md)
dokumentiert. Der Abschluss ist weder ein vollständiger Migrationsnachweis
noch eine strenge Gesamtnumerikfreigabe. Die Abschlussbilanz bezeichnet
diesen Umfang ausdrücklich; historische Fehler und offene Nachweise
bleiben erhalten. Keine automatische Zuordnung zu einer Folgeversion,
kein Commit, Push, Tag oder Release.
