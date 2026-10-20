# Abschlussbilanz V0.10: Abnahme und Performance

**Stand:** 20.10.2026  
**Status:** V0.10 als **begrenzter Versionsstand abgeschlossen**, ausdrücklich
vom Nutzer am 20.10.2026 freigegeben. Optimist-Batchausnahme akzeptiert;
übrige Restarbeiten nach ursprünglichen Anforderungsnummern im
[Backlog](../../../../Backlog/Restarbeiten_V0.10.md) dokumentiert.
Kein vollständiger Abschluss des ursprünglichen Migrationsplans,
keine strenge Gesamtnumerikfreigabe und kein Release.

**Abschlussumfang:** Produktiv eingebundener v16-Code-/Binärstand,
aktuelle Regression und vorläufiger Replay, dokumentierte 165 Messfälle
sowie 118 CPPI-Einträge mit Python-/V0.10-Performancezuordnung.
Die Abschlussdokumentation dieses begrenzten Stands ist fertig;
Restimplementierungen und ausstehende Abnahmen sind nicht als erledigt
freigegeben und keiner Folgeversion automatisch zugewiesen.

## 1. Auftrag und ausdrücklich akzeptierte Ausnahme

Der Nutzer hat am 20.10.2026 die Performance-Spalten `Python-Referenz` und
`V0.10` pro Interface beauftragt. Eine Spalte für die nächste Version wird
noch nicht angelegt. Die strenge Optimist-Batchabweichung darf für den
V0.10-Abschluss ignoriert werden: Sie ist als akzeptierte Abschlussausnahme
zu behandeln, nicht als bestandener strenger Test oder behobener Fehler.
Die historische 1000-Schritt-Diagnose v15 verfehlt die strengen Grenzen:
Zustand `1.0303820297e-11`, Kraftdaten `1.03769249193e-7`
gegen `1e-12` bzw. `1e-9`. Siehe
[Produktivprotokoll](Produktiv_Pruefprotokoll_2026-10-20.md).

Diese Ausnahme gilt nicht pauschal für Folkeboot, Endlichkeit, Datenverträge,
Solverfehler, fehlende Implementierungen oder nicht ausgeführte Abnahmen.
Die bestehenden vorläufigen Workergrenzen und die vorläufige
Replay-Eingabetoleranz bleiben als solche ausgewiesen. Es werden keine
Referenzwerte neu erzeugt oder Tests zur Erzielung eines grünen Ergebnisses
abgeschwächt.

## 2. Aktuell wiederholte Prüfungen

- Vollständige Regression: **1172 bestanden, 1 übersprungen**, keine Fehler;
  Laufzeit 49,18 s. Skip: fehlende Windows-Symlinkberechtigung in
  `tests/test_mesh.py:229`.
  [JUnit](../../../../../build/v010-abschluss-2026-10-20.xml).
- Expliziter C++-Referenzreplay:
  [Ergebnis](../../../../../build/v010-abschluss-replay-2026-10-20.json).
  Vorläufig bestanden; streng fehlgeschlagen. Folkeboot-Eingabekomponente
  weicht um `1.1102230246251565e-16` ab; zugelassene Eingabe-ATOL `1e-12`,
  Hydrostatik-ATOL `1e-9`. Optimist/yacht1 haben keine
  Eingabekomponentenabweichung. Das ist kein Langzeit-Workervergleich und
  kein neuer Beleg zur Folkeboot-Kraftabweichung.
- Messstand v16 gegen aktuellen Arbeitsstand geprüft: alle **57**
  erfassten Quelldateien stimmen nach der dokumentierten
  CRLF/LF-Normalisierung mit ihren SHA256-Werten überein. Auch die native
  Binärdatei stimmt mit ihrem erfassten SHA256 überein. Die Werte unten
  sind vorhandene, weiterhin zuordenbare Messungen, keine neu ausgeführte
  Performanceabnahme.
- Keine neue Live-/Langzeit-/Speicherabnahme und kein sauberer Release-Neubau
  in diesem Abschlussschritt. Bestehende Nachweise bleiben im
  [Produktivprotokoll](Produktiv_Pruefprotokoll_2026-10-20.md) referenziert.

Ausgeführte Prüfkommandos im Repository-Hauptverzeichnis:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q -rs --junitxml=build\v010-abschluss-2026-10-20.xml
$env:SEGELPHYSIK_RECHENPFAD = 'cpp'
.\.venv\Scripts\python.exe werkzeuge\migration_replay.py --output build\v010-abschluss-replay-2026-10-20.json
```

## 3. Vergleichsbasis und Interpretationsgrenzen

Grundlage sind die **165 Fälle** aus
[Produktivvergleich v16](Produktiv_2026-10-20_v16/produktive_vergleiche.json)
und dessen [Umgebungs-/Build-/Quellnachweis](Produktiv_2026-10-20_v16/umgebung.json).
Der Präfix `v16` bezeichnet einen Messzwischenstand innerhalb V0.10,
nicht eine Softwareversion V0.16.

- Referenzbasis: Commit `7a955c24ceb6c0825e05a574b959dd1176be2e2c`.
  Gemessen wird der explizite threadlokale Python-Referenzpfad des
  erfassten Arbeitsstands, nicht ein in diesem Schritt erneut ausgecheckter
  historischer Commit. Dessen eingefrorenes Referenzmanifest und die
  Arbeitsquellhashes sind im Umgebungsnachweis getrennt erfasst.
- Kandidat: nicht committierter Arbeitsstand, durch die 57 Quellhashes
  und die native Binärdatei identifiziert; kein erfundener Kandidatencommit.
  Binär-SHA256:
  `70ea30be3f19bf9d332288a68f3f3e6a0f1b5814cc92f3f246507c8fae1b526b`.
- Windows 11, AMD64 Family 25 Model 117 Stepping 2, 12 logische
  CPU-Threads, Python 3.14.8; NumPy 2.5.4, PySide6 6.10.3,
  PyVista 0.49.1, VTK 9.7.1, Manifold3D 3.5.4.
- MSVC 19.44, Visual Studio 17 2022, x64, Release `/O2 /Ob2 /DNDEBUG`;
  vollständige Compilerkonfiguration und weitere Versionen im Rohbeleg.
- Je Fall sieben Wiederholungen nach Aufwärmaufruf, wechselnde Reihenfolge
  Python/C++; jeder Wiederholungswert ist die mittlere Zeit je Aufruf über
  die im Rohbeleg genannte Aufrufanzahl. Die Tabelle nennt den Median
  dieser sieben Werte und P95, keine Einzelaufruf-Latenzverteilung.
- Zeitangaben in Mikrosekunden. Faktor = Python-Median / C++-Median:
  über 1 schneller, unter 1 langsamer. Auch Verschlechterungen bleiben
  sichtbar. Rohreihen, Minimum/Maximum, Standardabweichung, Eingaben,
  A-Zuordnung und Prüfhashes stehen in den verlinkten JSON-Dateien.
- Die Messungen enthalten öffentliche Pythonadapter, Validierung,
  Konvertierung und Ausgabeobjekte. Sie sind keine isolierten C++-Kernelzeiten.
  Soweit ein gemeinsamer Block gemessen wurde, ist dessen Gesamtwert
  keinem einzelnen untergeordneten Interface als Eigenzeit zuzurechnen.
- Im [Schnittstellenregister](../../../Revisionsinformation/Schnittstellenregister_CPP.md)
  stehen zuordenbare Adaptermessungen in den Versionsspalten.
  Fehlende Einzelmessungen bleiben ausdrücklich gekennzeichnet;
  Elternblocklinks sind nur Integrationskontext.
- Fälle mit mehreren Eingabegrößen oder Modellen bleiben getrennt.
  Historische Messzwischenstände werden nicht gemittelt. Wegen überlappender
  Pfade sind weder Summe noch Durchschnitt der Faktoren ein Gesamtgewinn.
  Ein repräsentativer Gesamtgewinn der Anwendung ist weiterhin nicht belegt.

Aufrufschema für eine neue Vergleichsmessung (kein historischer Prozesslog;
in diesem Abschlussschritt nicht ausgeführt). Vor Ausführung einen eigenen
Ausgabeordner und den tatsächlich verwendeten Release-Buildordner festlegen:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:SEGELPHYSIK_RECHENPFAD = 'cpp'
.\.venv\Scripts\python.exe werkzeuge\migration_produktiv.py `
  --output $NeuesAusgabeverzeichnis `
  --build-verzeichnis $ReleaseBuildverzeichnis `
  --paritaetsnachweis build\v010-produktiv-2026-10-20-v16.xml
```

Das v16-Ausgabeverzeichnis ist bereits belegt und wird nicht überschrieben.
Das historische JUnit
und sein Hash stehen im Umgebungsnachweis. Einzelne damalige Build-/CLI-
Pfade sind nicht vollständig als Prozesskommando gespeichert; die
Buildkonfiguration ist erfasst. Obiger Aufruf beschreibt die reproduzierbare
Werkzeugverwendung, keinen zusätzlich nachgewiesenen Prozesslog.

## 4. Abschlussgrenzen und konkret verbleibende Arbeit

| Bereich | Tatsächlicher Stand / Ursache | Fehlender Abschlussnachweis / nächster Schritt |
|---|---|---|
| Optimist-Batch | Strenge Abweichung bekannt; vom Nutzer für den Abschluss akzeptiert | Kein Abschlussblocker mehr; historische Fehlerwerte erhalten, keine strenge Parität behaupten |
| Folkeboot-Worker | Vorläufige 120-s-Prüfung bestanden; historisch Kraftdatenmaximum ca. 0,269893421 in gemischten Kraftdatensatzfeldern, kein Positionsfehler | Ursache feld-/beitragsgenau weiter klären; vorläufige Grenzwerte sind keine strenge Freigabe |
| Folkeboot-Referenzreplay | Aktuell nur Eingabeweichung von ca. 1,11e-16; vorläufiger Replay bestanden | Von der Worker-Kraftabweichung getrennt behandeln; exakte historische Eingabeparität nicht erfüllt |
| M2–M4-Einzelabnahme | Produktive Kerne und Regressionen vorhanden, Inventar-/Referenztestabdeckung ist nicht überall native Einzelparität | Direkte Rand-/Fehler-/Variantenfälle und deren Zuordnung vollständig nachweisen |
| Modell-/Topologievalidierung, Formerkennung, Modellvermessung | Teilkerne vorhanden, weitere Python-Numerik und deren Bewertung offen | Fehlende Kerne übertragen oder mit belastbarem Profil als nicht zeitkritisch bzw. bereits nativ begründen; Funktionsmatrix nachführen |
| Solver-Sonderfälle | Produktive Hauptpfade getestet, schwierige Mehrfachlösungs-/Nichtkonvergenz-/Diagnosefälle nicht vollständig abgenommen | Native Parität einschließlich Abbruch und Diagnose für Sonderfälle vervollständigen |
| GUI-/Actor-/Overlay-Pfade | Numerik teilweise nativ; Qt-/VTK-Objektadapter dürfen Python bleiben, sind aber kein Freibrief für verbleibende schwere Python-Numerik | Restnumerik bewerten; Layer-/Optik-/Kamera-/Instrumentmatrix und Referenzbildnachweise vervollständigen |
| Optionale Voxel-/OpenCL-Pfade | CPU-Kerne sowie ein OpenCL-Gerät geprüft; OpenCL ist kein übertragener C++-GPU-Kernel | Genauigkeits-/Transfermatrix und vorhandene Sperren systematisch nachweisen; keine allgemeine Gerätefreigabe ableiten |
| End-to-End/Live/Speicher | Bisher sichtbare 60-s-Läufe, keine vollständige wiederholte Langzeitmatrix | Mindestens drei vergleichbare Wiederholungen und die geforderte Live-Dauer je Referenz/Kandidat; Speicher-/Lifecycle-/Lastmatrix |
| Release-Neubau und Gesamtmatrix | Aktuelle Installation regressionsgeprüft; noch kein neuer sauberer Abschlussbuild, native Einzelmatrix nicht vollständig | Release-Neubau installieren und prüfen; 298 Inventareinträge und alle 34 Anforderungen mit Nachweisen oder ausdrücklich freigegebener Umfangsgrenze bilanzieren |

Die v15/v16-Liveberichte belegen Renderaufrufe und abgeschlossene
Frame-Events, keine tatsächlich präsentierten Monitor-FPS.
Ein fehlerfreier 60-s-Lauf ist keine bestandene fünfminütige
Vergleichs-/Speicherabnahme. Die positive visuelle Nutzerbeobachtung bleibt
wertvolles Feedback, ersetzt aber nicht diese technischen Nachweise.

Der Nutzer hat nach Vorlage dieser Grenzen den begrenzten Abschluss
ausdrücklich bestätigt und die Dokumentation der Restarbeiten im Backlog
nach ursprünglichen Anforderungsnummern beauftragt. Der
[Restarbeitskatalog](../../../../Backlog/Restarbeiten_V0.10.md) führt
Anforderung und verbleibende Arbeit einzeln auf. Dadurch sind die offenen
Pflichtumfänge nicht erledigt oder stillschweigend aus der Spezifikation
gestrichen; sie blockieren aber den freigegebenen begrenzten Versionsschnitt
nicht mehr.

## 5. Abschlussmatrix der 34 aktiven Anforderungen

Die Zeilen stehen in Kennungsreihenfolge. Kurze U-Verweise in der Tabelle
bezeichnen `U-V0.10-` mit sechsstelliger Nummer. Maßgeblich bleiben die
[Spezifikation](../Spezifikationen/Spezifikation_CPP_Migration_V0.10.md),
der [Umsetzungsplan](../Umsetzungsplan/Umsetzungsanleitung_CPP_Migration_V0.10.md)
und das [Produktivprotokoll](Produktiv_Pruefprotokoll_2026-10-20.md).
Die [aktuelle Vollsuite](../../../../../build/v010-abschluss-2026-10-20.xml)
ist ein Regressionsnachweis, keine automatische vollständige Abnahme jeder
Anforderung. Performance-Fallnummern verweisen auf Abschnitt 6.
Für die 298 einzelnen Inventareinträge fehlt weiterhin eine vollständig
aktuelle native Abnahmematrix; die vorhandene Referenztestmatrix ersetzt sie nicht.

| Anforderungs-ID | Gegenstand | U-Schritte | Belegter Stand / Nachweis | Restumfang bis zur vollständigen Abnahme |
|---|---|---|---|---|
| A-V0.10-00001 | Vollständigkeit zeitkritischer Pfade | 000001, 000002, 000018, 000020 | M1-Inventar mit 298 aktiven Einträgen; CPPI-Register mit 118 Einzelinterfaces | Vollständige native Einzelentscheidungen und verbleibende Hotspots |
| A-V0.10-00002 | Funktion und Numerik | 000001, 000003, 000019 | Vollsuite grün; Replay vorläufig; Optimist-Batchausnahme akzeptiert | Folkeboot und weitere strenge Parität nur vorläufig, siehe Abschnitt 4 |
| A-V0.10-00003 | Grobkörnige Schnittstelle und Datenbesitz | 000004, 000010, 000019 | Native Kontexte und callbackfreier exakter Batch; Backend-/Workertests im JUnit | Vollständige Datenbesitz-/Lifecyclematrix außerhalb geprüfter Pfade |
| A-V0.10-00004 | Build und Referenzbetrieb | 000001, 000004, 000019 | Installierter Release-Kandidat und v16-Binärhash unverändert, Regression grün | Neuer sauberer Abschlussbuild und erneute Installation |
| A-V0.10-00005 | Fehler und Nebenläufigkeit | 000004, 000010, 000019 | Backend-/Windows-Spawn-/Workertests bestanden, kein stiller Fallback | Vollständige Last-/Wechsel-/Abbruch-Gesamtmatrix |
| A-V0.10-00006 | Quaternionen und 6DOF | 000005, 000010 | Produktive Kerne; Fälle 029–034; Optimist-Abschlussausnahme | Übrige Einzel- und Langzeitnumerik nicht vollständig abgenommen |
| A-V0.10-00007 | Kraft-/Momentenaggregation | 000009 | Produktive Wrench-/Aggregationskerne; Kraftmodell-Elternfälle 117/141/165 | Restliche Einzelbeitrags-/Fehlerparität |
| A-V0.10-00008 | Zusammengesetztes Kraftmodell | 000009 | Produktiv; Fälle 117/141/165 einschließlich Adapter | Vollständige fachliche Varianten-/Einzelmatrix |
| A-V0.10-00009 | Benetzung und Flächen | 000008 | Nativer Rollenkontext; Fälle 116/140/164 als Elternblock | Vollständige Benetzungs-/Randfallmatrix |
| A-V0.10-00010 | Hydrodynamische Rollenkräfte | 000008 | Produktive Rumpf-/Kiel-/Ruder-/generische Rollen, Elternfälle 116/140/164 | Alle Rollen-/Parameter-/Fehlerkombinationen vollständig abnehmen |
| A-V0.10-00011 | Hydrovorbereitung und Rudernäherung | 000008 | Vorbereitung produktiv; Fälle 115/139/163 mit negativem Laufzeitvergleich | Vorbereitungshilfen und Testnäherung vollständig abnehmen |
| A-V0.10-00012 | Hydrostatik und Auftrieb | 000006, 000007 | Vorbereiteter exakter 6DOF-Auftrieb produktiv; Fälle 112/136/160 | Weitere Varianten und Einzelabnahmen |
| A-V0.10-00013 | Vorbereiteter Union-Ebenenschnitt | 000006 | Produktiv; Fälle 112/136/160, vorläufiger Referenzreplay | Vollständige Rand-/Übergangs-/End-to-End-Nachweise |
| A-V0.10-00014 | Union-/Bibliotheksübergänge | 000006 | Bestehendes Manifold bleibt erhalten; vorbereitete native Pfade vorhanden | Vollständige Datenübergangs-/Variantenabnahme |
| A-V0.10-00015 | Wasserschnitt und Deckel | 000007 | Produktiver Elternblock; Fälle 114/138/162 | Vollständige Schnitt-/Kontur-/Deckel-Einzelmatrix |
| A-V0.10-00016 | Wasserlinienkennwerte | 000007 | Ringe/Momente produktiv; Fälle 113/137/161 | Vollständige Einzelparität und Randfälle |
| A-V0.10-00017 | Robuster statischer Solver | 000011 | Produktiv; Fälle 101/125/149 und native Solverregressionen | Schwierige Sonderlösungen, Nichtkonvergenz und Diagnosen |
| A-V0.10-00018 | Weiterer statischer Solver | 000011 | Produktiv; Fälle 100/124/148 und native Solverregressionen | Vollständige Sonderfall-/Abbruch-/Diagnosematrix |
| A-V0.10-00019 | Stationärer Solver und Nachlauf | 000011 | Native Newtonstufen und callbackfreier Nachlauf; Fälle 092/093 | Sämtliche stationären Sonderfalldiagnosen |
| A-V0.10-00020 | Körper, Snapshots und Gelenke | 000005, 000012 | Native Aggregation und Snapshots; Fälle 035–046 sowie 109/133/157 | Einmalige Vorbereitung, Invalidierung und vollständige Einzelabnahme |
| A-V0.10-00021 | Meshvalidierung und Massen | 000012 | Native Selbstschnitt-/Massenkerne; Fälle 102–108, 126–132, 150–156 | Allgemeine Eingabe-/Topologievalidierung |
| A-V0.10-00022 | Weitere Modellvorbereitung | 000012 | Grundformen/Polyeder/OBJ-Teilkerne produktiv; Fälle 009–028 | Formerkennung, Modellvermessung, Konflikt-/Fehler-/Schreibtransaktionen |
| A-V0.10-00023 | Physikbatch und Transport | 000010 | Exakter nativer Batch, Windows-Spawn und vorläufige 120-s-Vergleiche | Vollständige Live-/Transport-/Lifecycleabnahme; übrige Numerik siehe Abschnitt 4 |
| A-V0.10-00024 | Anzeigeinterpolation und Pose | 000013 | Produktive SLERP-/Pufferinterpolation; Fälle 032/047, auch Verschlechterung sichtbar | Übrige GUI-Aufbereitung und vollständige Live-/Optikmatrix |
| A-V0.10-00025 | Körperdarstellung und Farben | 000014 | Farb-/Sammelgeometrie produktiv; Fälle 094/095/097 und Modellvarianten | Übrige schwere Numerik prüfen, volle Layer-/Optikmatrix |
| A-V0.10-00026 | Kräfte, Bögen und Achsen | 000014 | Produktiv; Fälle 063–075, 096/120/144; Overlay langsamer | Übrige Overlay-/Actor-Numerik sowie Live-/Optikabnahme |
| A-V0.10-00027 | Wasser und Spuren | 000015 | Produktive Wasserkerne; Fälle 001–003, 058–062, 078–082 | PyVista-Isoflächenübergänge und volle Live-/Optikmatrix; ausgenommene Altpfade bleiben archiviert |
| A-V0.10-00028 | Navigation, Instrumente, Kamera | 000016 | Produktive Kerne; Fälle 054–057, 083–091; SVG-/Pixelparität im Produktivprotokoll | Vollständige Instrument-/Kamera-/Optik-/Einzelmatrix |
| A-V0.10-00029 | Weitere Bewegungspfade | 000017 | Produktive Rotations-/Stoß-/Projektions-/Kontakt-/SI-Kerne; Fälle 048–053, 098/099 und Modellvarianten | Vollständige Pfadabnahme; ausgenommene alte Körperhöhenhilfe bleibt archiviert |
| A-V0.10-00030 | Optionale Voxel-/GPU-Pfade | 000018 | CPU-Kerne und ein OpenCL-Gerät geprüft; Fälle 004–008, historische Liveberichte | Genauigkeits-/Transfer-/Gerätematrix und GPU-Kernelübertragung offen |
| A-V0.10-00031 | Parität pro Block | 000003, 000019 | Aktuelle Regression 1172/1; vorläufiger C++-Replay | Nicht sämtliche native Einzel-/Rand-/Fehlerfälle nachgewiesen |
| A-V0.10-00032 | Produktivübernahme und Gesamtvergleich | 000002, 000003, 000019 | Native Kerne produktiv auch bei Verschlechterung; 165 Adaptermessfälle | Wiederholter Langzeit-/Speicher-/Live-Gesamtvergleich zur Referenz |
| A-V0.10-00033 | Vollständiger Abschluss | 000002, 000020 | Diese 34-zeilige Bilanz und Restpunktliste vorhanden | Ursprüngliche vollständige Migration und native 298-Einzelmatrix noch offen |
| A-V0.10-00034 | Performance jeder Übertragung | 000002, 000003, 000019, 000020 | Alle 165 v16-Fälle dokumentiert; 118 CPPI-Zeilen mit Wert oder Messlücke | Fehlende Einzel-/Elternblocknachweise und End-to-End-Nutzen vervollständigen |

<!-- BEGIN GENERATED PERFORMANCE TABLES -->
## 6. Vollständige Performance-Fallübersicht v16

**98 Fälle schneller, 67 langsamer.** Das ist eine Fallzählung,
keine gewichtete Anwendungsbeschleunigung. P95 stammt aus den sieben
Wiederholungsmittelwerten; alle Zeiten sind µs je Aufruf.
Im Register haben **67 Interfaces** zuordenbare Adaptermesswerte,
**28** ausschließlich Elternblockverweise und
**23** keine zugeordnete Einzelmessung
(darunter die 22 Datentypen). Keine fehlende Messung wird als Nullzeit geführt.

Rohdaten-SHA256: `6f80e4b34c1d29ff2fc9a8d9cb4bba1a9c5397f1daec835785f7da11f75aeaab`.

| Fall | Gemessener Adapter / Block | Eingabe / Modell | Aufrufe je Wiederholung | Python Median | Python P95 | V0.10 Median | V0.10 P95 | Faktor |
|---|---|---|---:|---:|---:|---:|---:|---:|
| <a id="messfall-001"></a>001 | IsoSurfaceWater._mirrored | `{"partikel": 250, "becken_und_bodenrand": "gespiegelt"}` | 100 | 104.019 | 107.513 | 34.340 | 36.025 | 3.029x |
| <a id="messfall-002"></a>002 | IsoSurfaceWater.splat ohne Marching Cubes | `{"partikel": 250, "grid": [8, 7, 8], "offsets_je_partikel": 125, "kosten": "Spiegelung, float32-Gewichte, bincount-Aggregation, Randkopie; PyVista-Isoflaechenextraktion ausgeschlossen"}` | 3 | 8231.000 | 8950.480 | 893.133 | 1090.897 | 9.216x |
| <a id="messfall-003"></a>003 | IsoSurfaceWater._calibrate | `{"grid": [8, 7, 8], "dtype": "float32"}` | 20 | 2.290 | 2.448 | 8.215 | 8.352 | 0.279x |
| <a id="messfall-004"></a>004 | KoerperfestesVoxelmodell.auswerten | `{"voxelzentren": 1000, "aufloesung_m": 0.2, "pose": {"z_m": -0.31, "roll_rad": 0.37}}` | 100 | 277.483 | 458.218 | 5.205 | 8.948 | 53.311x |
| <a id="messfall-005"></a>005 | KoerperfestesVoxelmodell.auswerten_6dof | `{"voxelzentren": 1000, "aufloesung_m": 0.2, "position_m": [0.12, -0.08, -0.31], "quaternion_wxyz": [0.9829362506302315, 0.18394653352804122, 0.0, 0.0]}` | 100 | 343.414 | 439.996 | 24.694 | 26.199 | 13.907x |
| <a id="messfall-006"></a>006 | KoerperfestesVoxelmodell Vorbereitung und erste Pose | `{"meshpunkte": 8, "meshdreiecke": 12, "aufloesung_m": 0.2, "kosten": "Validierung, Rasteraufbau, native Datenkopie und erste Auswertung"}` | 5 | 5176.560 | 7755.008 | 2697.660 | 4842.382 | 1.919x |
| <a id="messfall-007"></a>007 | Voxel-Saeulenintervalle im Koerpermit-Pfad | `{"meshpunkte": 8, "meshdreiecke": 12, "xz_m": [0.13, -0.27], "kosten": "Pythonadapter und Arrayschnittstelle enthalten"}` | 100 | 31.968 | 32.968 | 8.239 | 9.404 | 3.880x |
| <a id="messfall-008"></a>008 | Voxel gesamter Unterwasser-Rasterpfad | `{"meshpunkte": 8, "meshdreiecke": 12, "aufloesung_m": 0.2, "kosten": "Wasserschnitt, Raster, Saeulenintervalle, Vereinigung und Schwerpunkt; keine OpenCL-GPU"}` | 2 | 3379.600 | 3456.950 | 1068.700 | 1214.210 | 3.162x |
| <a id="messfall-009"></a>009 | build_cone | `{"parameter_si": {"H": 2.0, "R": 0.5, "nseg": 64}}` | 20 | 22.700 | 23.560 | 12.090 | 13.745 | 1.878x |
| <a id="messfall-010"></a>010 | build_box | `{"parameter_si": {"dx": 2.0, "dy": 3.0, "dz": 4.0}}` | 20 | 6.390 | 6.604 | 8.895 | 9.379 | 0.718x |
| <a id="messfall-011"></a>011 | build_pyramid | `{"parameter_si": {"a": 2.0, "H": 3.0}}` | 20 | 4.400 | 4.594 | 8.855 | 9.061 | 0.497x |
| <a id="messfall-012"></a>012 | build_sphere | `{"parameter_si": {"R": 0.5, "nseg": 64}}` | 20 | 3832.345 | 4756.331 | 179.780 | 184.408 | 21.317x |
| <a id="messfall-013"></a>013 | build_cylinder stehend | `{"parameter_si": {"R": 0.5, "H": 2.0, "nseg": 64, "lage": "stehend"}}` | 20 | 96.305 | 146.633 | 17.470 | 28.411 | 5.513x |
| <a id="messfall-014"></a>014 | build_cylinder liegend | `{"parameter_si": {"R": 0.5, "H": 2.0, "nseg": 64, "lage": "liegend"}}` | 20 | 112.355 | 184.349 | 20.640 | 29.003 | 5.444x |
| <a id="messfall-015"></a>015 | build_plate | `{"parameter_si": {"dx": 2.0, "dy": 1.0, "dicke": 0.02}}` | 20 | 6.450 | 9.875 | 9.735 | 14.092 | 0.663x |
| <a id="messfall-016"></a>016 | build_hexprism | `{"parameter_si": {"umkreisradius": 0.004, "H": 0.17, "spitzenlaenge": 0.0, "lage": "stehend"}}` | 20 | 65.470 | 90.885 | 11.015 | 12.973 | 5.944x |
| <a id="messfall-017"></a>017 | build_hexprism Spitze liegend | `{"parameter_si": {"umkreisradius": 0.004, "H": 0.17, "spitzenlaenge": 0.03, "lage": "liegend"}}` | 20 | 81.155 | 92.905 | 12.895 | 19.694 | 6.294x |
| <a id="messfall-018"></a>018 | Formring | `{"quaderpunkte": 8, "dreiecke": 12, "ringparameter": [0.5, 0.3, 64]}` | 100 | 10.372 | 22.399 | 12.680 | 15.576 | 0.818x |
| <a id="messfall-019"></a>019 | Formvolumenschwerpunkt | `{"quaderpunkte": 8, "dreiecke": 12, "ringparameter": [0.5, 0.3, 64]}` | 100 | 27.943 | 49.008 | 16.090 | 30.545 | 1.737x |
| <a id="messfall-020"></a>020 | Formzentrierung | `{"quaderpunkte": 8, "dreiecke": 12, "ringparameter": [0.5, 0.3, 64]}` | 100 | 47.583 | 52.951 | 34.159 | 36.596 | 1.393x |
| <a id="messfall-021"></a>021 | Liegendtransformation | `{"quaderpunkte": 8, "dreiecke": 12, "ringparameter": [0.5, 0.3, 64]}` | 100 | 5.912 | 6.133 | 17.230 | 17.579 | 0.343x |
| <a id="messfall-022"></a>022 | build_polyhedron Konvexhuelle | `{"punkte": 8, "sortierung": "unveraendertes natives NumPy argsort"}` | 1 | 3117.400 | 3729.540 | 167.900 | 236.440 | 18.567x |
| <a id="messfall-023"></a>023 | build_polyhedron Konvexhuelle | `{"punkte": 24, "sortierung": "unveraendertes natives NumPy argsort"}` | 1 | 72464.400 | 80357.180 | 1367.100 | 1462.540 | 53.006x |
| <a id="messfall-024"></a>024 | build_polyhedron Konvexhuelle | `{"punkte": 64, "sortierung": "unveraendertes natives NumPy argsort"}` | 1 | 1402067.200 | 1533688.130 | 35268.900 | 36344.530 | 39.754x |
| <a id="messfall-025"></a>025 | build_polyhedron explizite Polygonflaechen | `{"punkte": 8, "vierecke": 6}` | 100 | 67.298 | 69.123 | 69.625 | 71.012 | 0.967x |
| <a id="messfall-026"></a>026 | Polygon-Selbstschnitt | `{"punkte": 32, "polygon": "einfach und konkav"}` | 20 | 2226.225 | 3083.760 | 11.965 | 14.729 | 186.061x |
| <a id="messfall-027"></a>027 | OBJ-Ohrtriangulierung | `{"punkte": 32, "polygon": "einfach und konkav"}` | 20 | 3493.670 | 6677.896 | 25.000 | 25.575 | 139.747x |
| <a id="messfall-028"></a>028 | OBJ-Import mit kaltem Anwendungscache | `{"punkte": 32, "skalierung": 0.3, "rotation": [[0.9067599067599067, -0.400932400932401, 0.13053613053613056], [0.3449883449883451, 0.8834498834498834, 0.31701631701631705], [-0.2424242424242425, -0.24242424242424243, 0.9393939393939393]], "kosten": "Cacheleeren, Dateilesen/Parsen, Triangulierung, Transformation, Validierung und unveraenderliches Mesh enthalten; Betriebssystem-Dateicache nicht geleert"}` | 20 | 4678.370 | 6781.294 | 975.710 | 1140.166 | 4.795x |
| <a id="messfall-029"></a>029 | quaternion_normalisieren | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 6.560 | 6.735 | 18.093 | 18.681 | 0.363x |
| <a id="messfall-030"></a>030 | quaternion_matrix | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 14.360 | 15.558 | 18.412 | 18.601 | 0.780x |
| <a id="messfall-031"></a>031 | quaternion_aus_matrix | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 58.967 | 60.301 | 20.098 | 21.336 | 2.934x |
| <a id="messfall-032"></a>032 | quaternion_slerp | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 13.422 | 13.527 | 8.793 | 11.579 | 1.526x |
| <a id="messfall-033"></a>033 | _quaternion_multiplizieren | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 2.525 | 2.586 | 8.361 | 9.122 | 0.302x |
| <a id="messfall-034"></a>034 | _orientierung_schritt | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 10.231 | 20.262 | 9.798 | 21.459 | 1.044x |
| <a id="messfall-035"></a>035 | Pose.__post_init__ | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 15.561 | 15.902 | 23.700 | 24.047 | 0.657x |
| <a id="messfall-036"></a>036 | Pose.rotationsmatrix | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 14.776 | 15.375 | 18.879 | 19.520 | 0.783x |
| <a id="messfall-037"></a>037 | Pose.punkt_transformieren | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 20.676 | 20.979 | 20.881 | 21.017 | 0.990x |
| <a id="messfall-038"></a>038 | Pose.vektor_transformieren | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 10.012 | 19.821 | 12.340 | 21.127 | 0.811x |
| <a id="messfall-039"></a>039 | Pose.invers | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 53.352 | 58.526 | 22.175 | 22.351 | 2.406x |
| <a id="messfall-040"></a>040 | Pose.komponieren | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 87.007 | 123.915 | 31.693 | 63.678 | 2.745x |
| <a id="messfall-041"></a>041 | rotationsmatrix_achsenwinkel | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 7.369 | 8.513 | 9.299 | 10.077 | 0.792x |
| <a id="messfall-042"></a>042 | pose_aus_modellpose | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 7.559 | 7.883 | 11.010 | 11.485 | 0.687x |
| <a id="messfall-043"></a>043 | pose_mit_gelenkwinkel | `{"quaternion": [2.0, -0.3, 0.2, 0.4]}` | 200 | 7.674 | 7.996 | 21.724 | 22.390 | 0.353x |
| <a id="messfall-044"></a>044 | Pose.punkte_transformieren | `{"punkte": 1}` | 20 | 10.395 | 10.927 | 9.395 | 9.725 | 1.106x |
| <a id="messfall-045"></a>045 | Pose.punkte_transformieren | `{"punkte": 1000}` | 20 | 19.255 | 19.863 | 26.880 | 29.386 | 0.716x |
| <a id="messfall-046"></a>046 | Pose.punkte_transformieren | `{"punkte": 100000}` | 5 | 1688.620 | 1925.432 | 4348.680 | 4770.380 | 0.388x |
| <a id="messfall-047"></a>047 | anzeige_interpolieren mit 101 Samples | `{"samples": 101, "anzeigezeit_s": 0.1, "dt_s": 0.016, "verzoegerung_s": 0.1}` | 200 | 20.953 | 37.545 | 1264.494 | 2065.667 | 0.017x |
| <a id="messfall-048"></a>048 | rotation_matrix einschliesslich Defaultachse | `{"phi_rad": 0.3, "achse": [0.0, 1.0, 0.0]}` | 200 | 11.870 | 13.679 | 24.112 | 24.784 | 0.492x |
| <a id="messfall-049"></a>049 | stationaere Eulerrotation | `{"winkel_rad": [0.1, 0.2, 0.3]}` | 200 | 4.742 | 5.174 | 8.446 | 9.665 | 0.561x |
| <a id="messfall-050"></a>050 | Stoerrotation | `{"winkel_rad": [0.1, 0.2, 0.3]}` | 200 | 5.421 | 5.620 | 10.486 | 11.081 | 0.517x |
| <a id="messfall-051"></a>051 | stoss_pose | `{"position": [1.0, 2.0, 3.0], "winkel_rad": [0.1, 0.2, 0.3], "versatz_m": [0.2, -0.1, 0.5]}` | 200 | 6.817 | 7.001 | 9.137 | 9.455 | 0.746x |
| <a id="messfall-052"></a>052 | projektion | `{"position": [1.0, 2.0, 3.0], "winkel_rad": [0.1, 0.2, 0.3]}` | 200 | 0.702 | 0.712 | 8.202 | 8.994 | 0.086x |
| <a id="messfall-053"></a>053 | beste_loesung | `{"loesungen": [{"z": -0.1, "gm": null, "neutral": true}, {"z": 0.1, "gm": 0.2}, {"z": 0.0, "gm": 0.3}]}` | 200 | 0.751 | 0.758 | 8.577 | 9.532 | 0.088x |
| <a id="messfall-054"></a>054 | navigationswerte_ableiten | `{"quaternion_wxyz": [1.0, 0.1, 0.2, 0.3], "offset_rad": 0.4, "elevation_rad": 0.5, "segelwinkel_rad": 0.1}` | 200 | 28.772 | 33.076 | 18.479 | 24.461 | 1.557x |
| <a id="messfall-055"></a>055 | winkel_360 | `{"winkel_rad": -10.0}` | 200 | 0.209 | 0.216 | 7.497 | 10.431 | 0.028x |
| <a id="messfall-056"></a>056 | wrap_180 | `{"winkel_rad": 10.0}` | 200 | 0.713 | 0.764 | 17.731 | 21.265 | 0.040x |
| <a id="messfall-057"></a>057 | richtung_16 | `{"heading_grad": 75.0}` | 200 | 0.772 | 0.778 | 16.542 | 16.657 | 0.047x |
| <a id="messfall-058"></a>058 | _hash01: 1000 Gitterzellen | `{"gx_gy_int64": [-500, 499], "zellen": 1000, "salz": 1}` | 200 | 18.441 | 18.978 | 37.432 | 42.249 | 0.493x |
| <a id="messfall-059"></a>059 | punktlage: 1000 Gitterzellen | `{"gx_gy_int64": [-500, 499], "zellen": 1000, "abstand_m": 1.5}` | 200 | 60.484 | 61.163 | 52.503 | 53.022 | 1.152x |
| <a id="messfall-060"></a>060 | dunst_gitter: unveraenderte Standardaufloesung | `{"r_innen_m": 30.0, "r_aussen_m": 2000.0, "hoehe_m": 600.0, "ringe": 28, "hoehenstufen": 8, "segmente": 96, "z_basis_m": -0.05, "farbe_rgb": [200, 220, 238]}` | 200 | 3797.949 | 3908.496 | 137.651 | 282.702 | 27.591x |
| <a id="messfall-061"></a>061 | WasserPunktFeld.punkte_welt | `{"zentrum_m": [0.1, 0.2], "radius_m": 12.0, "abstand_m": 1.5}` | 200 | 86.495 | 87.955 | 31.412 | 31.858 | 2.754x |
| <a id="messfall-062"></a>062 | WasserPunktFeld.aktualisieren mit vollem Verlauf | `{"zentrum_m": [0.1, 0.2], "radius_m": 12.0, "abstand_m": 1.5, "historie": 12, "spur_punkte": 6}` | 200 | 92.802 | 102.041 | 46.918 | 58.901 | 1.978x |
| <a id="messfall-063"></a>063 | pfeil_daten | `{"start": [1.0, 2.0, 3.0], "vektor": [4.0, 5.0, 6.0]}` | 50 | 4.818 | 4.992 | 9.528 | 10.067 | 0.506x |
| <a id="messfall-064"></a>064 | pfeil_fest | `{"start": [1.0, 2.0, 3.0], "vektor": [4.0, 5.0, 6.0], "durchmesser": 0.1, "kopf_durchmesser": 0.2, "kopf_laenge": 0.3}` | 50 | 5.278 | 5.457 | 14.700 | 15.030 | 0.359x |
| <a id="messfall-065"></a>065 | paar_moment_auftrieb | `{"auftrieb_N": 900.0, "angriff": [0.1, 0.2, -0.3]}` | 50 | 14.904 | 16.132 | 10.558 | 11.986 | 1.412x |
| <a id="messfall-066"></a>066 | paar_moment_kraft | `{"kraft_N": [30.0, -20.0, 1000.0], "angriff": [0.1, 0.2, -0.3]}` | 50 | 14.742 | 15.338 | 9.416 | 9.842 | 1.566x |
| <a id="messfall-067"></a>067 | skala_waehlen | `{"masse_kg": 100.0, "g_m_pro_s2": 9.81, "referenz_laenge_m": 2.0}` | 50 | 0.288 | 0.441 | 11.464 | 13.897 | 0.025x |
| <a id="messfall-068"></a>068 | kraft_pfeile | `{"masse_kg": 100.0, "g_m_pro_s2": 9.81, "skala": 0.001}` | 50 | 10.966 | 11.118 | 11.330 | 11.478 | 0.968x |
| <a id="messfall-069"></a>069 | zusatz_pfeile | `{"masse_kg": 100.0, "g_m_pro_s2": 9.81, "skala": 0.001}` | 50 | 15.416 | 16.061 | 11.868 | 12.805 | 1.299x |
| <a id="messfall-070"></a>070 | moment_bogen | `{"moment_Nm": 10.0, "radius_m": 0.5, "punkte": 49}` | 50 | 18.040 | 20.355 | 9.798 | 10.205 | 1.841x |
| <a id="messfall-071"></a>071 | moment_bogen_achse | `{"moment_Nm": -10.0, "radius_m": 0.5, "achse": 2, "punkte": 49}` | 50 | 17.982 | 18.746 | 9.764 | 10.104 | 1.842x |
| <a id="messfall-072"></a>072 | strich_linien | `{"stuetzpunkte": 101, "laenge_m": 10.0, "strich_m": 0.1, "luecke_m": 0.05}` | 50 | 759.136 | 1311.160 | 19.960 | 37.741 | 38.033x |
| <a id="messfall-073"></a>073 | wirkungslinie_auf_geometrie | `{"modell": "analytischer Einheitsquader", "dreiecke": 12}` | 50 | 203.876 | 206.250 | 102.872 | 103.629 | 1.982x |
| <a id="messfall-074"></a>074 | hauptachsen: NumPy-Eigenloeser und native Sortierung/Kanonisierung | `{"traegheit_kg_m2": [[2.0, 0.1, 0.2], [0.1, 3.0, 0.1], [0.2, 0.1, 4.0]]}` | 50 | 29.416 | 31.029 | 29.480 | 34.428 | 0.998x |
| <a id="messfall-075"></a>075 | _kanonisiere | `{"vektor": [-1.0, 0.3, 0.2]}` | 50 | 4.512 | 4.878 | 18.484 | 19.339 | 0.244x |
| <a id="messfall-076"></a>076 | _polydaten einschliesslich PyVista-Datenobjekt | `{"modell": "analytischer Einheitsquader", "dreiecke": 12}` | 100 | 89.137 | 100.678 | 103.629 | 107.365 | 0.860x |
| <a id="messfall-077"></a>077 | _dreiecks_polydaten einschliesslich PyVista-Datenobjekt | `{"modell": "analytischer Einheitsquader", "dreiecke": 12}` | 100 | 89.534 | 90.373 | 102.280 | 105.169 | 0.875x |
| <a id="messfall-078"></a>078 | _surface_polydata einschliesslich PyVista-Datenobjekt | `{"raster": [40, 40], "dreiecke": 3042}` | 30 | 254.757 | 257.726 | 246.417 | 259.829 | 1.034x |
| <a id="messfall-079"></a>079 | _bilinear_upsample | `{"raster": [40, 40], "faktor": 3}` | 30 | 247.680 | 289.216 | 185.833 | 187.804 | 1.333x |
| <a id="messfall-080"></a>080 | _unit_circle | `{"punkte": 48}` | 30 | 12.207 | 13.656 | 18.353 | 18.920 | 0.665x |
| <a id="messfall-081"></a>081 | _unit_square | `{"punkte": 5}` | 30 | 2.043 | 2.082 | 16.433 | 16.685 | 0.124x |
| <a id="messfall-082"></a>082 | PyVistaRenderer._smooth_surface: Loecher, Median, Laplace | `{"raster": [40, 40], "fehlende_hoehen": 25, "smooth_passes": 2, "dx_m": 0.1}` | 30 | 2270.913 | 2296.155 | 152.483 | 154.772 | 14.893x |
| <a id="messfall-083"></a>083 | navigationskamera_aktualisieren einschliesslich VTK-Kamera und Observer | `{"ziel": [1.0, 2.0, 3.0], "wechselnde_headings_rad": [0.3, 0.4], "rendering": "nicht enthalten"}` | 100 | 90.646 | 103.989 | 77.996 | 87.822 | 1.162x |
| <a id="messfall-084"></a>084 | _navigationskamera_geaendert: manuelle Kamerageometrie | `{"ausgangsabstand": "vorbereiteter Kamera-Folgepfad", "rendering": "nicht enthalten"}` | 100 | 12.971 | 13.365 | 20.221 | 20.597 | 0.641x |
| <a id="messfall-085"></a>085 | SVGInstrumentWidget.aktualisieren: kompass | `{"typ": "kompass", "winkel_grad": [47.0, 20.0, -15.0], "kosten": "einschliesslich XML- und Qt-SVG-Aufbereitung, ohne Paint-Event"}` | 20 | 571.235 | 585.839 | 626.175 | 647.154 | 0.912x |
| <a id="messfall-086"></a>086 | SVGInstrumentWidget.aktualisieren: kraengung | `{"typ": "kraengung", "winkel_grad": [47.0, 20.0, -15.0], "kosten": "einschliesslich XML- und Qt-SVG-Aufbereitung, ohne Paint-Event"}` | 20 | 879.100 | 918.843 | 904.320 | 964.606 | 0.972x |
| <a id="messfall-087"></a>087 | SVGInstrumentWidget.aktualisieren: stampfen | `{"typ": "stampfen", "winkel_grad": [47.0, 20.0, -15.0], "kosten": "einschliesslich XML- und Qt-SVG-Aufbereitung, ohne Paint-Event"}` | 20 | 1646.475 | 1742.196 | 1721.010 | 1767.979 | 0.957x |
| <a id="messfall-088"></a>088 | GeschwindigkeitsWidget.aktualisieren einschliesslich XML und Qt-SVG | `{"geschwindigkeit_m_pro_s": 3.5, "paint_event": "nicht enthalten"}` | 20 | 198.495 | 203.448 | 225.380 | 243.625 | 0.881x |
| <a id="messfall-089"></a>089 | NavigationsWidgetFenster._instrumente_rendern: alle vier Anzeigen | `{"instrumente": 4, "geschwindigkeit_m_pro_s": 3.5, "paint_event": "nicht enthalten"}` | 10 | 3514.840 | 5165.184 | 3131.070 | 5883.205 | 1.123x |
| <a id="messfall-090"></a>090 | SVG-Rahmen: gemeinsamer numerischer Paint-Event-Block | `{"widget_px": [501, 301], "svg_px": [624, 810]}` | 100 | 0.964 | 1.056 | 24.265 | 24.980 | 0.040x |
| <a id="messfall-091"></a>091 | Geschwindigkeitseinheiten: m/s, km/h, kn | `{"geschwindigkeit_m_pro_s": 3.5}` | 100 | 0.518 | 0.830 | 23.192 | 23.742 | 0.022x |
| <a id="messfall-092"></a>092 | loese_stationaer: beide Stufen einschliesslich Newton/Jacobi/Daempfung | `{"modell": "analytischer Einheitsquader", "masse_kg": 500.0}` | 3 | 12616.267 | 13023.413 | 324.133 | 372.477 | 38.923x |
| <a id="messfall-093"></a>093 | pruefe_stationaer_dynamisch: nativer 1-s-Nachlauf ohne Pythoncallbacks | `{"modell": "analytischer Einheitsquader", "masse_kg": 500.0, "dauer_s": 1.0, "dt_s": 0.004}` | 1 | 272645.200 | 275766.650 | 1860.300 | 2032.440 | 146.560x |
| <a id="messfall-094"></a>094 | _farbgruppen: gesamte numerische Grafikvorbereitung | `{"modell": "optimist", "punkte": 1373, "dreiecke": 2706}` | 10 | 73.330 | 90.507 | 74.750 | 108.644 | 0.981x |
| <a id="messfall-095"></a>095 | _benetzte_geometrie: gesamte numerische Grafikvorbereitung | `{"modell": "optimist", "punkte": 1373, "dreiecke": 2706}` | 10 | 117.990 | 201.980 | 674.010 | 886.379 | 0.175x |
| <a id="messfall-096"></a>096 | Hauptachsen-Overlay: native Richtungsrotation und Projektionsausdehnung | `{"modell": "optimist", "punkte": 1373}` | 20 | 12.840 | 13.665 | 37.975 | 38.573 | 0.338x |
| <a id="messfall-097"></a>097 | GrafikBruecke._statisch_anwenden: numerischer Sammelblock ohne Actor-/Overlayausgabe | `{"modell": "optimist", "gruppen": 10, "punkte": 1373, "actor_und_overlayausgabe": "explizit ausgeschlossen"}` | 20 | 45.430 | 46.729 | 67.565 | 71.657 | 0.672x |
| <a id="messfall-098"></a>098 | kontakt_start einschliesslich nativer Hydrostatik | `{"modell": "optimist", "z_start": 2.0, "phi": 0.1}` | 5 | 520.200 | 558.668 | 49.700 | 54.282 | 10.467x |
| <a id="messfall-099"></a>099 | dynamik.schritt_mit_kraeften: vereinfachter SI-Schritt einschliesslich Kraftadapter | `{"modell": "optimist", "dt_s": 0.004}` | 20 | 339.915 | 350.938 | 103.290 | 115.157 | 3.291x |
| <a id="messfall-100"></a>100 | segelphysik.core.statisch.loese | `{"modell": "optimist", "z0": -0.05614826248505138, "phi0": 3.637243563773037}` | 3 | 3518.667 | 5063.033 | 209.667 | 213.990 | 16.782x |
| <a id="messfall-101"></a>101 | segelphysik.core.statisch_robust.loese_robust | `{"modell": "optimist", "z0": -0.05614826248505138, "phi0": 3.637243563773037}` | 3 | 3956.967 | 3988.970 | 227.333 | 231.023 | 17.406x |
| <a id="messfall-102"></a>102 | Mesh-Selbstschnitt: kalter Sweep-and-prune-Elternblock mit Dreieckspraedikaten | `{"modell": "optimist", "punkte": 344, "dreiecke": 684, "cache": "vor jedem Aufruf geleert"}` | 3 | 21256.067 | 23593.150 | 467.967 | 504.400 | 45.422x |
| <a id="messfall-103"></a>103 | mesh_volumen | `{"modell": "optimist", "punkte": 344, "dreiecke": 684}` | 30 | 39.033 | 40.070 | 28.483 | 28.951 | 1.370x |
| <a id="messfall-104"></a>104 | mesh_flaeche | `{"modell": "optimist", "punkte": 344, "dreiecke": 684}` | 30 | 48.097 | 72.173 | 28.143 | 32.961 | 1.709x |
| <a id="messfall-105"></a>105 | schwerpunkt_homogen | `{"modell": "optimist", "punkte": 344, "dreiecke": 684}` | 30 | 57.910 | 62.677 | 28.280 | 29.410 | 2.048x |
| <a id="messfall-106"></a>106 | schwerpunkt_flaechig | `{"modell": "optimist", "punkte": 344, "dreiecke": 684}` | 30 | 65.813 | 81.127 | 28.390 | 29.738 | 2.318x |
| <a id="messfall-107"></a>107 | traegheitstensor_homogen | `{"modell": "optimist", "punkte": 344, "dreiecke": 684}` | 30 | 241.983 | 251.204 | 47.010 | 50.790 | 5.147x |
| <a id="messfall-108"></a>108 | traegheitstensor_flaechig | `{"modell": "optimist", "punkte": 344, "dreiecke": 684}` | 30 | 429.310 | 447.531 | 50.240 | 52.150 | 8.545x |
| <a id="messfall-109"></a>109 | Koerper.snapshot | `{"modell": "optimist"}` | 50 | 97.916 | 121.023 | 524.620 | 591.790 | 0.187x |
| <a id="messfall-110"></a>110 | Koerper.punkte_in_welt | `{"modell": "optimist"}` | 50 | 30.648 | 31.892 | 50.026 | 52.526 | 0.613x |
| <a id="messfall-111"></a>111 | Modellaufbau einschliesslich Koerper.verband/_baue_verband | `{"modell": "optimist"}` | 1 | 16355.100 | 17258.230 | 14445.500 | 17973.110 | 1.132x |
| <a id="messfall-112"></a>112 | baue_kraftfunktion_6dof: vorbereitete exakte Union/Ebenenschnitt | `{"modell": "optimist"}` | 50 | 345.030 | 509.367 | 50.654 | 53.154 | 6.812x |
| <a id="messfall-113"></a>113 | wasserlinien_querschnitt/_ringe_aus_mesh/_ringmomente | `{"modell": "optimist"}` | 2 | 32614.250 | 38287.255 | 4984.000 | 8809.475 | 6.544x |
| <a id="messfall-114"></a>114 | schneide_am_wasser mit Deckel: Elternblock inklusive Konturketten | `{"modell": "optimist"}` | 5 | 1033.500 | 1090.068 | 162.280 | 166.114 | 6.369x |
| <a id="messfall-115"></a>115 | HydrodynamikModell.aus_koerper einschliesslich nativer Vorbereitung | `{"modell": "optimist"}` | 5 | 304.120 | 439.588 | 421.420 | 457.558 | 0.722x |
| <a id="messfall-116"></a>116 | HydrodynamikModell.beitraege_erzeugen: alle vorhandenen Rollen | `{"modell": "optimist"}` | 50 | 761.560 | 772.450 | 136.346 | 167.872 | 5.585x |
| <a id="messfall-117"></a>117 | Kraftmodell.mit_hydrostatik: Widerstand, Rollen und Gesamtwrench | `{"modell": "optimist"}` | 50 | 698.090 | 1085.352 | 334.038 | 353.435 | 2.090x |
| <a id="messfall-118"></a>118 | _farbgruppen: gesamte numerische Grafikvorbereitung | `{"modell": "folkeboot", "punkte": 257, "dreiecke": 486}` | 10 | 51.970 | 84.012 | 50.400 | 178.794 | 1.031x |
| <a id="messfall-119"></a>119 | _benetzte_geometrie: gesamte numerische Grafikvorbereitung | `{"modell": "folkeboot", "punkte": 257, "dreiecke": 486}` | 10 | 108.420 | 113.362 | 550.890 | 558.628 | 0.197x |
| <a id="messfall-120"></a>120 | Hauptachsen-Overlay: native Richtungsrotation und Projektionsausdehnung | `{"modell": "folkeboot", "punkte": 257}` | 20 | 14.720 | 14.829 | 37.630 | 38.266 | 0.391x |
| <a id="messfall-121"></a>121 | GrafikBruecke._statisch_anwenden: numerischer Sammelblock ohne Actor-/Overlayausgabe | `{"modell": "folkeboot", "gruppen": 7, "punkte": 257, "actor_und_overlayausgabe": "explizit ausgeschlossen"}` | 20 | 36.585 | 42.464 | 63.395 | 72.920 | 0.577x |
| <a id="messfall-122"></a>122 | kontakt_start einschliesslich nativer Hydrostatik | `{"modell": "folkeboot", "z_start": 2.0, "phi": 0.1}` | 5 | 710.500 | 782.094 | 83.820 | 90.134 | 8.476x |
| <a id="messfall-123"></a>123 | dynamik.schritt_mit_kraeften: vereinfachter SI-Schritt einschliesslich Kraftadapter | `{"modell": "folkeboot", "dt_s": 0.004}` | 20 | 444.540 | 449.081 | 143.395 | 156.529 | 3.100x |
| <a id="messfall-124"></a>124 | segelphysik.core.statisch.loese | `{"modell": "folkeboot", "z0": -0.44995488430240804, "phi0": 0.0005503877640912315}` | 3 | 3063.467 | 3809.573 | 127.833 | 179.833 | 23.965x |
| <a id="messfall-125"></a>125 | segelphysik.core.statisch_robust.loese_robust | `{"modell": "folkeboot", "z0": -0.44995488430240804, "phi0": 0.0005503877640912315}` | 3 | 3408.500 | 4745.293 | 140.067 | 221.067 | 24.335x |
| <a id="messfall-126"></a>126 | Mesh-Selbstschnitt: kalter Sweep-and-prune-Elternblock mit Dreieckspraedikaten | `{"modell": "folkeboot", "punkte": 189, "dreiecke": 374, "cache": "vor jedem Aufruf geleert"}` | 3 | 23495.100 | 23852.687 | 361.833 | 436.390 | 64.933x |
| <a id="messfall-127"></a>127 | mesh_volumen | `{"modell": "folkeboot", "punkte": 189, "dreiecke": 374}` | 30 | 75.383 | 81.631 | 43.927 | 46.808 | 1.716x |
| <a id="messfall-128"></a>128 | mesh_flaeche | `{"modell": "folkeboot", "punkte": 189, "dreiecke": 374}` | 30 | 92.543 | 100.812 | 43.780 | 52.273 | 2.114x |
| <a id="messfall-129"></a>129 | schwerpunkt_homogen | `{"modell": "folkeboot", "punkte": 189, "dreiecke": 374}` | 30 | 101.620 | 112.865 | 44.147 | 46.970 | 2.302x |
| <a id="messfall-130"></a>130 | schwerpunkt_flaechig | `{"modell": "folkeboot", "punkte": 189, "dreiecke": 374}` | 30 | 115.173 | 122.031 | 45.170 | 49.463 | 2.550x |
| <a id="messfall-131"></a>131 | traegheitstensor_homogen | `{"modell": "folkeboot", "punkte": 189, "dreiecke": 374}` | 30 | 385.690 | 418.507 | 56.233 | 66.960 | 6.859x |
| <a id="messfall-132"></a>132 | traegheitstensor_flaechig | `{"modell": "folkeboot", "punkte": 189, "dreiecke": 374}` | 30 | 523.637 | 549.368 | 54.860 | 56.404 | 9.545x |
| <a id="messfall-133"></a>133 | Koerper.snapshot | `{"modell": "folkeboot"}` | 50 | 64.756 | 123.546 | 404.710 | 459.188 | 0.160x |
| <a id="messfall-134"></a>134 | Koerper.punkte_in_welt | `{"modell": "folkeboot"}` | 50 | 43.064 | 44.505 | 65.768 | 67.663 | 0.655x |
| <a id="messfall-135"></a>135 | Modellaufbau einschliesslich Koerper.verband/_baue_verband | `{"modell": "folkeboot"}` | 1 | 12854.100 | 15404.690 | 11826.400 | 14275.320 | 1.087x |
| <a id="messfall-136"></a>136 | baue_kraftfunktion_6dof: vorbereitete exakte Union/Ebenenschnitt | `{"modell": "folkeboot"}` | 50 | 256.530 | 292.417 | 33.828 | 35.442 | 7.583x |
| <a id="messfall-137"></a>137 | wasserlinien_querschnitt/_ringe_aus_mesh/_ringmomente | `{"modell": "folkeboot"}` | 2 | 6312.500 | 9006.850 | 1643.250 | 2402.345 | 3.841x |
| <a id="messfall-138"></a>138 | schneide_am_wasser mit Deckel: Elternblock inklusive Konturketten | `{"modell": "folkeboot"}` | 5 | 872.780 | 962.246 | 123.840 | 131.404 | 7.048x |
| <a id="messfall-139"></a>139 | HydrodynamikModell.aus_koerper einschliesslich nativer Vorbereitung | `{"modell": "folkeboot"}` | 5 | 429.360 | 508.736 | 501.220 | 544.800 | 0.857x |
| <a id="messfall-140"></a>140 | HydrodynamikModell.beitraege_erzeugen: alle vorhandenen Rollen | `{"modell": "folkeboot"}` | 50 | 422.730 | 621.227 | 88.298 | 138.323 | 4.788x |
| <a id="messfall-141"></a>141 | Kraftmodell.mit_hydrostatik: Widerstand, Rollen und Gesamtwrench | `{"modell": "folkeboot"}` | 50 | 687.688 | 842.427 | 326.954 | 536.899 | 2.103x |
| <a id="messfall-142"></a>142 | _farbgruppen: gesamte numerische Grafikvorbereitung | `{"modell": "yacht1", "punkte": 2131, "dreiecke": 4197}` | 10 | 70.310 | 143.922 | 81.900 | 89.461 | 0.858x |
| <a id="messfall-143"></a>143 | _benetzte_geometrie: gesamte numerische Grafikvorbereitung | `{"modell": "yacht1", "punkte": 2131, "dreiecke": 4197}` | 10 | 197.110 | 253.975 | 1211.010 | 1611.567 | 0.163x |
| <a id="messfall-144"></a>144 | Hauptachsen-Overlay: native Richtungsrotation und Projektionsausdehnung | `{"modell": "yacht1", "punkte": 2131}` | 20 | 14.440 | 14.785 | 50.640 | 58.315 | 0.285x |
| <a id="messfall-145"></a>145 | GrafikBruecke._statisch_anwenden: numerischer Sammelblock ohne Actor-/Overlayausgabe | `{"modell": "yacht1", "gruppen": 8, "punkte": 2131, "actor_und_overlayausgabe": "explizit ausgeschlossen"}` | 20 | 52.185 | 53.948 | 91.050 | 101.502 | 0.573x |
| <a id="messfall-146"></a>146 | kontakt_start einschliesslich nativer Hydrostatik | `{"modell": "yacht1", "z_start": 2.0, "phi": 0.1}` | 5 | 670.780 | 740.388 | 60.380 | 89.106 | 11.109x |
| <a id="messfall-147"></a>147 | dynamik.schritt_mit_kraeften: vereinfachter SI-Schritt einschliesslich Kraftadapter | `{"modell": "yacht1", "dt_s": 0.004}` | 20 | 424.030 | 483.309 | 111.925 | 138.626 | 3.789x |
| <a id="messfall-148"></a>148 | segelphysik.core.statisch.loese | `{"modell": "yacht1", "z0": -0.14261573149529846, "phi0": 0.003983376204656998}` | 3 | 3184.267 | 4138.493 | 282.633 | 293.627 | 11.266x |
| <a id="messfall-149"></a>149 | segelphysik.core.statisch_robust.loese_robust | `{"modell": "yacht1", "z0": -0.14261573149529846, "phi0": 0.003983376204656998}` | 3 | 3691.900 | 3975.600 | 308.900 | 317.673 | 11.952x |
| <a id="messfall-150"></a>150 | Mesh-Selbstschnitt: kalter Sweep-and-prune-Elternblock mit Dreieckspraedikaten | `{"modell": "yacht1", "punkte": 1538, "dreiecke": 3072, "cache": "vor jedem Aufruf geleert"}` | 3 | 139686.600 | 156563.993 | 1570.600 | 1699.410 | 88.938x |
| <a id="messfall-151"></a>151 | mesh_volumen | `{"modell": "yacht1", "punkte": 1538, "dreiecke": 3072}` | 30 | 161.100 | 175.490 | 88.660 | 98.706 | 1.817x |
| <a id="messfall-152"></a>152 | mesh_flaeche | `{"modell": "yacht1", "punkte": 1538, "dreiecke": 3072}` | 30 | 179.080 | 208.453 | 82.847 | 94.332 | 2.162x |
| <a id="messfall-153"></a>153 | schwerpunkt_homogen | `{"modell": "yacht1", "punkte": 1538, "dreiecke": 3072}` | 30 | 234.037 | 249.796 | 87.090 | 106.423 | 2.687x |
| <a id="messfall-154"></a>154 | schwerpunkt_flaechig | `{"modell": "yacht1", "punkte": 1538, "dreiecke": 3072}` | 30 | 257.297 | 267.443 | 97.940 | 100.937 | 2.627x |
| <a id="messfall-155"></a>155 | traegheitstensor_homogen | `{"modell": "yacht1", "punkte": 1538, "dreiecke": 3072}` | 30 | 1062.493 | 1092.950 | 181.283 | 197.862 | 5.861x |
| <a id="messfall-156"></a>156 | traegheitstensor_flaechig | `{"modell": "yacht1", "punkte": 1538, "dreiecke": 3072}` | 30 | 2088.733 | 2170.771 | 208.760 | 228.435 | 10.005x |
| <a id="messfall-157"></a>157 | Koerper.snapshot | `{"modell": "yacht1"}` | 50 | 133.006 | 224.358 | 811.294 | 908.679 | 0.164x |
| <a id="messfall-158"></a>158 | Koerper.punkte_in_welt | `{"modell": "yacht1"}` | 50 | 50.174 | 56.038 | 75.058 | 85.659 | 0.668x |
| <a id="messfall-159"></a>159 | Modellaufbau einschliesslich Koerper.verband/_baue_verband | `{"modell": "yacht1"}` | 1 | 21417.900 | 21873.640 | 18778.800 | 19184.960 | 1.141x |
| <a id="messfall-160"></a>160 | baue_kraftfunktion_6dof: vorbereitete exakte Union/Ebenenschnitt | `{"modell": "yacht1"}` | 50 | 480.072 | 529.714 | 80.984 | 93.085 | 5.928x |
| <a id="messfall-161"></a>161 | wasserlinien_querschnitt/_ringe_aus_mesh/_ringmomente | `{"modell": "yacht1"}` | 2 | 59112.150 | 61084.750 | 9296.700 | 9981.130 | 6.358x |
| <a id="messfall-162"></a>162 | schneide_am_wasser mit Deckel: Elternblock inklusive Konturketten | `{"modell": "yacht1"}` | 5 | 2218.360 | 2371.320 | 415.280 | 510.100 | 5.342x |
| <a id="messfall-163"></a>163 | HydrodynamikModell.aus_koerper einschliesslich nativer Vorbereitung | `{"modell": "yacht1"}` | 5 | 1082.800 | 1235.204 | 1489.020 | 1730.904 | 0.727x |
| <a id="messfall-164"></a>164 | HydrodynamikModell.beitraege_erzeugen: alle vorhandenen Rollen | `{"modell": "yacht1"}` | 50 | 1541.810 | 1684.717 | 248.322 | 263.861 | 6.209x |
| <a id="messfall-165"></a>165 | Kraftmodell.mit_hydrostatik: Widerstand, Rollen und Gesamtwrench | `{"modell": "yacht1"}` | 50 | 1868.080 | 2662.266 | 611.320 | 735.400 | 3.056x |
<!-- END GENERATED PERFORMANCE TABLES -->
