# Backlog v1 – priorisierte Arbeitsliste

**Stand:** 17.10.2026
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
| **BL3** | B-08 | **Sofort** | Rückstand und Nachholrate auf dem aktuellen Pfad als Baseline messen; nach Paket-Kandidatenwechsel BL2 betroffene Messungen mit gleichen Einstellungen wiederholen. Insbesondere Gate ≥ `1,25 s/s`, Rückstandstrend und Verhalten bei Modus-/Körperwechsel prüfen. | **Teilweise; nach Worker- und Gate-Anzeige-Korrektur Nachholrate `1,874 / 2,076 / 1,777 s/s` bestanden, aber der Zehnminutenlauf löste eine Überlastpause aus und bestand die Live-Zeitbilanz nicht.** |
| **BL4** | B-11 | **Sofort** | Sichtbare Live-Baseline erfassen und mit BL3 abgleichen; nach Paket-Kandidatenwechsel BL2 betroffene Tests/Messungen erneut ausführen. Widersprüchliche Nachholraten anhand Rohdaten klären. | **Teilweise; R-4a dokumentiert historisch `4,4–4,8×`; aktueller Lauf mit Worker: `13,04 FPS`, Frameabstand-P95 `205,098 ms` und Überlastpause, daher Live-Gates fehlgeschlagen.** |
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

## Sofortige Umsetzungspläne

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

## Backlog pflegen

Neue Erkenntnisse als nummerierten `BL`-Punkt ergänzen oder einen bestehenden
Punkt mit nachvollziehbarem Datum, Status, Messbedingungen, Abnahme und
Querverweis aktualisieren. Abgeschlossene Punkte nicht löschen; sie bleiben
als Historie und für Cutover-Nachweise sichtbar. Die bisherigen B-IDs dienen
nur noch zur Rückverfolgbarkeit.
