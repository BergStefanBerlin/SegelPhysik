# Backlog v1 – priorisierte Arbeitsliste

**Stand:** 19.10.2026
**Zweck:** Nachverfolgbare Liste offener, laufender, zurückgestellter und
abgeschlossener Entwicklungsarbeiten. Die Nummern `BL1`, `BL2` usw. sind die
neuen stabilen Backlog-IDs. Die Spalte „Bisherige ID“ erhält die Zuordnung zu
den früheren Einträgen B-01 bis B-21.

Die Priorisierung richtet sich nach dem nächsten Entwicklungsschritt der
Hydrodynamik. „Sofort“ bedeutet, dass die Arbeit jetzt vorbereitet oder
abgeschlossen werden soll; es ist keine Freigabe, vor erfüllten fachlichen
und technischen Gates unvalidierte Kräfte produktiv einzuschalten.

## Priorisierte Punkte

| ID | Bisherige ID | Priorität vor Hydrodynamik | Thema und nächster Schritt | Status |
|---|---|---|---|---|
| **BL1** | B-21 | **Sofort** | Vorbereitung künftiger Hydrodynamik-/Aerodynamik-Eingaben: bestehende Verträge inventarisieren und offene Daten-/Quellenbedarfe dokumentieren. Keine Kraftansätze, Koeffizienten, Laufzeitinputs oder Modelle festlegen/einbauen. | **Erledigt als Bestandsaufnahme; offene Quellen-/Freigabefragen bleiben vor jeder neuen Physik offen.** |
| **BL2** | B-16 | **Sofort für Produktionsumschaltung** | Phase-11-Cutover zuerst isoliert mit Paket-Kandidatenpfad prüfen, externe Bestände dry-run-migrieren und validieren, GUI-Integration und Alt-/Neu-Parität nachweisen. BL3/BL4 nach Kandidatenwechsel wiederholen; produktiven Standard erst nach allen Gates ändern. | **Teilweise; Repository-Loader-/Migrationsregressionen bestanden. Externe Nutzerbestände und Cutover wurden nicht bearbeitet; Produktionspfad bleibt unverändert.** |
| **BL3** | B-08 | **Sofort** | Rückstand und Nachholrate auf dem aktuellen Pfad als Baseline messen; nach Paket-Kandidatenwechsel BL2 betroffene Messungen mit gleichen Einstellungen wiederholen. Insbesondere Gate ≥ `1,25 s/s`, Rückstandstrend und Verhalten bei Modus-/Körperwechsel prüfen. | **Teilweise; frühere Nachholraten `1,874 / 2,076 / 1,777 s/s` bestanden. Sichtbarer Zehnminutenlauf vom 17.10.2026: nur `0,00525 s/s`, nach `3,152 s` berechneter Simulationszeit Überlastpause und Rückstand `3,651 s`; Live-Zeitbilanz klar verfehlt.** |
| **BL4** | B-11 | **Sofort** | Sichtbare Live-Baseline erfassen und mit BL3 abgleichen; nach Paket-Kandidatenwechsel BL2 betroffene Messungen mit gleichen Einstellungen erneut ausführen. Widersprüchliche Nachholraten anhand Rohdaten klären. | **Teilweise; sichtbarer Zehnminutenlauf vom 17.10.2026 (`yacht1`, `exakt_union`, Windows/Qt): `12,97 FPS`, Frameabstand-P95 `205,186 ms`, automatische Überlastpause; Live-Gates verfehlt. Eingabelatenz war gültig (`7,852 ms`, 599/599 Eingaben beantwortet).** |
| **BL5** | B-15 | **Idealerweise** | Bekannten Fehler im bereits implementierten statischen Auftriebs-/Gleichgewichtssolver für `bleistift` untersuchen und korrigieren. Nur bei erfolgreicher stabiler Lösung abgeschlossen; andernfalls offen/blockiert. Keine neuen physikalischen Ansätze oder Modellpakete ergänzen. | **Erledigt; bestehender Solver findet stabilen `bleistift`-Gleichgewichtswinkel mit Regressionstest.** |
| **BL6** | B-14 | **Idealerweise** | Generische Geometrie-Importinfrastruktur vorbereiten/ergänzen, falls benötigt. Bestehende Loader-/Manifestverträge verwenden; keine neuen physischen Modelle oder Simulationsbeiträge hinzufügen. | **Erledigt durch nachgewiesenen Bestand; sichere Paket-/OBJ-/Form-Import- und Migrationsinfrastruktur samt Tests vorhanden, keine Zusatzimplementierung nötig.** |
| **BL7** | B-01 | Bei Bedarf | Fortschrittsanzeige oder expliziten Abbruch für Solverläufe nur bei bestätigtem UX-Bedarf spezifizieren. Hintergrundberechnung und GUI-Thread-sicheres Anwenden sind bereits vorhanden. | **Kernarbeit erledigt; UX-Erweiterung offen.** |
| **BL8** | B-02 | Zurückgestellt | Globalen Voxelpfad nur bei nachgewiesenem Leistungsproblem erneut untersuchen; frühere Laufzeit und Genauigkeitsabweichung gegen `exakt_union` beachten. | **Profiling abgeschlossen; als interaktiver Standard abgelehnt.** |
| **BL9** | B-03 | Zurückgestellt | Körperfestes Voxelraster nur bei begründetem Bedarf weiterentwickeln. Vor einer Freigabe müssen Volumen, Schwerpunkt, Kraft/Moment und vollständiges Solvergleichgewicht die geltenden Gates bestehen. | **Offen, aber bewusst nicht produktiv; Genauigkeits- und Gleichgewichtsgates verfehlt.** |
| **BL10** | B-04 | Erledigt / fortlaufend | Benchmarkwerkzeug für vollständige Arbeitslasten weiterverwenden; derzeit ausschließlich bereits implementierte Physik und vorhandene Modelle benchmarken. Künftige Fälle nur vorbereitend dokumentieren, nicht simulieren. | **Werkzeug umgesetzt und ausgeführt.** |
| **BL11** | B-05 | Bei Bedarf | Exakten Unionpfad nur bei messbarem Engpass optimieren; analytische und Boolesche Referenzen sowie explizite Fehlerbehandlung erhalten. | **`exakt_union` ist der ausgewählte genaue Pfad.** |
| **BL12** | B-06 | Bei Bedarf | Darstellung und GPU-Nutzung getrennt messen, falls neue Lasten die Live-Gates gefährden. GPU-Physik nicht allein aufgrund eines isolierten Mikrobenchmarks freigeben. | **CPU-Live-Yachtlauf gemessen; GPU-Physik nicht produktiv aktiviert.** |
| **BL13** | B-07 | Zurückgestellt | Voxel-/Geometriecache-Invalidierung nur weiterentwickeln, falls der Voxelpfad wieder benötigt wird. Änderungen an Geometrie, Auflösung und Material müssen dann getrennt geprüft werden. | **Offen; an den zurückgestellten körperfesten Voxelpfad gebunden.** |
| **BL14** | B-09 | Erledigt / bei Bedarf erneut messen | Vektorisierten Wasserlinienschnitt und Actor-Wiederverwendung beibehalten; bei veränderter Szene oder Renderlast gezielt erneut messen. | **Optimiert, Regressionen und integrierter Live-Lauf dokumentiert.** |
| **BL15** | B-10 | Zurückgestellt | OpenCL-/Voxel-Hydrostatik nicht produktiv freigeben, solange Genauigkeits-, statische/dynamische Paritäts- und vollständige Live-Gates gegenüber `exakt_union` nicht bestehen. | **Kernel vorhanden; Genauigkeitsgate verfehlt, Produktionsfreigabe gesperrt.** |
| **BL16** | B-12 | Zurückgestellt | Solver-Kennfelder, Warmstart oder weitere Memoisierung erst angehen, wenn Profiling des exakten Pfads einen konkreten Engpass zeigt und ein gültiges Fehlerbudget vorliegt. | **Begrenztes solverlokales Memoisieren umgesetzt; Kennfelder/Warmstart nicht begonnen.** |
| **BL17** | B-13 | Zurückgestellt | Voxel-, GPU-, Cache- und Warmstartarbeiten nur wieder aufnehmen, wenn `exakt_union` auf Zielhardware oder größeren Modellen vereinbarte Gates verfehlt. | **Nutzerentscheidung: zurückgestellt; `exakt_union` genügt derzeit.** |
| **BL18** | B-17 | Ggf. später | Nautisches Weltsystem, Kurs und Abdrift separat spezifizieren, falls Hydrodynamikfälle nautische Richtungsgrößen benötigen. | **Zurückgestellt; außerhalb des aktuellen Umbaus.** |
| **BL19** | B-18 | Später, nur bei Bedarf | Gekoppelte Mehrkörperdynamik beweglicher Teile mit eigener Physikspezifikation entwerfen. Nicht mit der bestehenden Ein-Körper-Näherung verwechseln. | **Zurückgestellt; nur nach eigener Spezifikation.** |
| **BL20** | B-19 | Erledigt | Deduplizierte, valide Segel-Meshes im Yachtpaket verwenden; Legacy-Quellen unverändert lassen. Produktionsfreigabe separat über BL2. | **Technische Meshbereinigung abgeschlossen.** |
| **BL21** | B-20 | Erledigt / Gate in BL2 | Allgemeine Selbstüberschneidungsprüfung mit Regressionen und Modell-/Knotenpfad-Fehlern beibehalten; keine erneute Implementierung einplanen. | **Funktional umgesetzt; T-011 im B-03-End-to-End-Gate enthalten.** |
| **BL22** | Neu | Blockiert HYD-0005/0013 | Ruderdrehachse, Drehpunkt, Vorzeichen und Winkelgrenzen für jede Produktions-/Manöverbewertung aus einer autoritativen Konstruktions-/Modellquelle nachweisen. Das aktuelle Yachtmanifest enthält für `ruder` weder Pose noch Gelenk. Eine Mesh-abgeleitete Kinematik ist nur als ausdrücklich genehmigte, getrennte Testannahme zulässig (Spec0066). | **Teilweise; eine Vorderkantenachse ist nutzerfreigegeben und ausschließlich als Testannahme im isolierten Modell umgesetzt. Autoritativer Nachweis, mechanische Grenzen und Produktionsgelenk fehlen; Spec0065 bleibt für Manöver-/Produktionsfreigabe offen.** |
| **BL23** | Neu | Blockiert HYD-0004/0008–0010 | Für die Yacht passende, ausreichend dokumentierte Referenzdaten zu Rumpfwiderstand und Kiel-/Ruderkräften beschaffen oder einen klar begrenzten Näherungszweig fachlich freigeben. TU-Delft-Ergebnisse zeigen Wechselwirkungen und experimentelle Unstimmigkeiten; Werte sind ohne Geometrie-/Bedingungsabgleich keine direkt übertragbaren Koeffizienten. | **Teilweise; nutzerfreigegebener Rudernormalkraftzweig isoliert implementiert und getestet. Er bleibt `berechnete_naeherung`; passende Yacht-Referenzdaten fehlen, Rumpfwiderstand und Kiel-/Ruderinteraktion sind nicht validiert, keine Produktivaktivierung.** |

## Ideen: Echtzeit-Berechnung und Darstellung

Die folgenden Ideen verwenden die projektweite Kennung `I-BL-…` gemäß
[Nummerierungs-Anweisung](../Anweisungen/Nummerierungs-Anweisung.md). Sie sind
Vorschläge, keine Umsetzungsfreigabe. Vorher-/Nachher-Messungen müssen
dieselben Modelle, Einstellungen, Hardware und Genauigkeitsgates verwenden.

| Idee-ID | Möglichkeit | Komplexität | Umsetzungsstand |
|---|---|---:|---|
| **I-BL-000001** | Aktuellen Echtzeitpfad end-to-end profilieren und Messung aus dem sichtbaren GUI-Zustand reproduzieren; Zeitanteile für Hydrostatik, Hydrodynamik, Integration, Worker/IPC und Rendering getrennt erfassen. | Niedrig bis mittel | Werkzeuge für Live-GUI, Physik und Nachholrate sind vorhanden. Screenshot-Baseline: `19,2 FPS`, `1,035 s` Rückstand, `1,05×` Zeitfaktor. Frisches komponentengetrenntes Profil des aktuellen Laufs fehlt. In die Spezifikation zuV0.9 als [A-V0.9-00003](../WegZuV1.0/Revisionslog/zuV0.9/Spezifikationen/Spezifikation_Echtzeitberechnung_und_Darstellung_v0.9.md) übernommen; Umsetzung offen. |
| **I-BL-000002** | Den genauen `exakt_union`-Pfad anhand des Profils optimieren, etwa Vorbereitungsdaten, Boolesche Operationen oder Poseauswertung gezielt verbessern. | Hoch | Nicht als gezielte Optimierung des aktuellen Hotspots nachgewiesen. Nur beginnen, wenn I-BL-000001 einen konkreten Anteil zeigt; Referenzgenauigkeit und Parität erhalten. In die Spezifikation zuV0.9 als [A-V0.9-00006](../WegZuV1.0/Revisionslog/zuV0.9/Spezifikationen/Spezifikation_Echtzeitberechnung_und_Darstellung_v0.9.md) übernommen; Umsetzung offen. |
| **I-BL-000003** | Wiederverwendung von Hydrostatikresultaten in Echtzeit erweitern, sofern Poseänderungen oder ein kontrollierter Näherungsfehler dies zulassen. | Mittel bis hoch | Cache-Hülle ist vorhanden; Echtzeit nutzt Intervall `1` und wertet daher exakt je Schritt neu aus. Größere Intervalle wären näherungsbehaftet und sind nicht freigegeben. In die Spezifikation zuV0.9 als [A-V0.9-00007](../WegZuV1.0/Revisionslog/zuV0.9/Spezifikationen/Spezifikation_Echtzeitberechnung_und_Darstellung_v0.9.md) übernommen; Umsetzung offen. |
| **I-BL-000004** | Körperfesten CPU-Voxelpfad als schnellere Hydrostatikoption untersuchen und gegebenenfalls neu gegen den exakten Referenzpfad validieren. | Hoch | Pfad ist implementiert, aber Genauigkeits-/Gleichgewichtsgates wurden verfehlt; nicht produktiv freigegeben. Verknüpfung: BL9, BL13, BL17. |
| **I-BL-000005** | OpenCL/GPU-Hydrostatik erneut bewerten und nur nach Bestehen von Genauigkeits-, Paritäts- und vollständigen Live-Gates produktiv erwägen. | Hoch | Prototyp vorhanden; Genauigkeitsgate verfehlt, Produktionsfreigabe gesperrt. Verknüpfung: BL12, BL15, BL17. |
| **I-BL-000006** | NPU-Eignung für den Echtzeitpfad ermitteln: zuerst NPU-Modell, Treiber, unterstützte Rechenlaufzeit und verfügbare Operatoren feststellen; danach einen isolierten, repräsentativen Teilkernel benchmarken. | Niedrig für Machbarkeitsprüfung; hoch für Implementierung | Neu. Hardwaremodell und Laufzeit sind noch nicht erfasst; keine NPU-Nutzung im Projekt nachgewiesen. NPUs sind nicht automatisch für Boolesche Mesh-Union oder beliebige NumPy-Geometrieoperationen geeignet. Nur weiterverfolgen, wenn sich ein numerisch passender, ausreichend großer Tensor-/Vektor-Teilpfad findet und End-to-End-Gates gegenüber CPU bestehen. In die Spezifikation zuV0.9 als [A-V0.9-00008](../WegZuV1.0/Revisionslog/zuV0.9/Spezifikationen/Spezifikation_Echtzeitberechnung_und_Darstellung_v0.9.md) übernommen; Machbarkeitsprüfung offen. |
| **I-BL-000007** | Einen durch Profiling belegten CPU-Hotspot mit JIT/kompiliertem Code (beispielsweise Numba oder eine native Erweiterung) beschleunigen. | Hoch | Nicht umgesetzt. Erst nach I-BL-000001; Messgewinn, Installations-/Wartungsaufwand und numerische Parität nachweisen. In die Spezifikation zuV0.9 als [A-V0.9-00005](../WegZuV1.0/Revisionslog/zuV0.9/Spezifikationen/Spezifikation_Echtzeitberechnung_und_Darstellung_v0.9.md) übernommen; Umsetzung offen. |
| **I-BL-000008** | Unabhängige Dreiecks- oder Bauteilbeiträge parallel berechnen, soweit der Algorithmus keine zeitliche Schrittabhängigkeit verletzt. | Hoch | Nicht umgesetzt. Abhängige Physikzeitschritte bleiben seriell; Parallelisierung auf Teilbeiträge begrenzen und Reduktions-/Determinismuseffekte testen. |
| **I-BL-000009** | Adaptive oder größere Physikzeitschritte als optionalen Leistungsmodus untersuchen. | Hoch | Nicht umgesetzt und nicht freigegeben. Erfordert vorher definierte Fehler- und Stabilitätsgrenzen, Vergleich gegen feste Zeitschritte und eigene Konvergenztests. |
| **I-BL-000010** | Renderlast getrennt reduzieren oder messen (Wasseroptik, SSAO, Overlay-Layer), um die sichtbare Bildrate und Bedienbarkeit zu verbessern. | Niedrig bis mittel | Keine Berechnungsbeschleunigung; vorhandener GUI-Live-Benchmark kann Render- und Physikmetriken getrennt erfassen. Die Screenshot-FPS von `19,2` belegen einen Anzeigeengpass, aber nicht allein dessen Ursache. Verknüpfung: BL4, BL12. In die Spezifikation zuV0.9 als [A-V0.9-00004](../WegZuV1.0/Revisionslog/zuV0.9/Spezifikationen/Spezifikation_Echtzeitberechnung_und_Darstellung_v0.9.md) übernommen; Umsetzung offen. |

Bereits umgesetzt und deshalb nicht als neue Idee geführt sind die
Physikberechnung im Hintergrund/Prozess-Worker, begrenzte Schrittbündelung,
Vorbereitung geometrischer Daten, vorberechnete hydrodynamische Meshkennwerte,
solverlokales Memoisieren sowie vektorisierte Wasserlinienschnitte und
Actor-Wiederverwendung. Ihre weitere Wirkung ist mit den oben genannten
End-to-End-Messungen zu überprüfen.

## Sofortige Umsetzungspläne

- [Hydrodynamik-Bestandsaufnahme HYD-0001 bis HYD-0006](../WegZuV1.0/Revisionslog/zuV0.6/Hydrodynamik_Bestandsaufnahme_HYD-0001-bis-0006.md):
  reproduzierbare Baseline, Yachtgeometrie, Laufzeit-/Kraftinventar und
  dokumentierte Sperrgates zu Ruderkinematik und Referenzdaten.
- [Ruderkraft-Näherungsmodell – Prüfvorschlag und Implementierungsstatus](../WegZuV1.0/Revisionslog/zuV0.6/Hydrodynamik_Ruder_Naeherungsmodell_Vorschlag.md):
  fachlicher Quellenreview, freigegebene Testachsenannahme,
  Gleichungen/Parameter und ausdrücklich nicht validierter Geltungsbereich.
- [Umsetzungsplan für BL1–BL4](../WegZuV1.0/Revisionslog/zuV0.6/UmsetzungsplanFuerBacklog1.md):
  Vorbereitung künftiger Umwelteingaben, Phase-11-Cutover und Abnahme vorhandener Physik.
- [Umsetzungsplan für BL5–BL6](../WegZuV1.0/Revisionslog/zuV0.6/UmsetzungsplanFuerBacklog2.md):
  Korrektur bestehender Auftriebssimulation und generische Geometrie-Importinfrastruktur ohne neue Körpermodelle.
- [BL1-Bestandsaufnahme](../WegZuV1.0/Revisionslog/zuV0.6/Bestandsaufnahme_Umwelteingaben_BL1.md):
  vorhandene Umwelt-/Kraftverträge und offene Quellenfragen ohne neue Physik.

## Mess- und Freigabegrundsätze

- Vorher-/Nachher-Benchmarks verwenden dieselbe Hardware, Python-/Bibliotheksversion,
  Eingaben, Modell, Solverparameter und Renderkonfiguration. Rohdaten,
  Umgebung, Warm-up, Wiederholungen und Auswertung werden gespeichert.
- Numerische Toleranzen und erwartete Referenzwerte werden vor dem
  Kandidatenlauf festgelegt; sie werden nicht nach Sichtung eines Ergebnisses
  gelockert.
- Fehlende Messwerte sind nicht bestanden. Ein fehlgeschlagener oder
  uneindeutiger Gate-Lauf wird sichtbar dokumentiert und nicht als Erfolg
  ausgegeben.
- Produktionspfade und bestehende validierte Physik bleiben unverändert, bis
  die jeweiligen funktionalen, numerischen und Leistungs-Gates bestanden
  sind.
- Zulässig sind Tests, Messungen und gezielte Fehlerkorrekturen an bereits
  implementierter Auftriebssimulation und bestehender Physik. Neue
  physikalische Simulationen, Kraftgesetze und physische Modellpakete sind
  nicht Teil der beiden Umsetzungspläne.
- Für Punkte mit Verweisen auf den bisherigen Umsetzungsplan gelten dessen
  vollständige G1–G4- und Paritätsregeln weiter.

## Ergänzender Messstand zuV0.9

Die historischen BL3-/BL4-Werte oben gelten weiterhin für ihre damaligen
Szenarien, nicht als aktueller Folkeboot-Nachweis. Im expliziten
Schulungs-Optikmodus erreicht Folkeboot einschließlich Segler in zwei
300-s-Läufen 33,64/33,68 Qt-Swaps/s, Frame-P95 47,343/47,242 ms und
Eingabe-P95 39,896/41,277 ms bei jeweils negativem Rückstandtrend.
Das ist kein Monitor-Scanoutnachweis, kein erneuter Nachholratenbeleg
für das separate BL3-Gate und keine allgemeine 30-FPS-Freigabe aller Modelle
oder hochwertiger Standardoptik. Pädagogische Nutzerabnahme bleibt offen.
Details und Kandidatenentscheidungen:
[Prüfprotokoll zuV0.9](../WegZuV1.0/Revisionslog/zuV0.9/Umsetzungsplan/Abnahme_v0.9.md).

## Backlog pflegen

Neue Erkenntnisse als nummerierten `BL`-Punkt ergänzen oder einen bestehenden
Punkt mit nachvollziehbarem Datum, Status, Messbedingungen, Abnahme und
Querverweis aktualisieren. Abgeschlossene Punkte nicht löschen; sie bleiben
als Historie und für Cutover-Nachweise sichtbar. Die bisherigen B-IDs dienen
nur noch zur Rückverfolgbarkeit.
