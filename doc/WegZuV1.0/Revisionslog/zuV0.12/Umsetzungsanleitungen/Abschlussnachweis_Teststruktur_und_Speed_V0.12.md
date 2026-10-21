# Abschlussnachweis V0.12: Teststruktur und bisherige Speed-Arbeiten

**Stand:** 21.10.2026

**Status:** Historischer Durchführungs- und Nachweisstand; nicht mehr maßgeblicher Umsetzungsplan. Teststruktur technisch umgesetzt und geprüft; zwei bekannte Ausgangsfehler und Iterationszeit-Ziel offen. Die vollständige Suite wurde ausgeführt (1.752 bestanden, 2 bekannte Fehler, 1 übersprungen). Für Speed sind die bisherigen Messdaten und Kandidatenversuche dokumentiert. Verbleibende Speed-Arbeiten richten sich ausschließlich nach dem neuen [Umsetzungsplan V0.12](./Umsetzungsplan_V0.12.md).

**Ausgangsbasis:** Teststruktur: Testbestand V0.11; Speed: festzuhaltender V0.12-Arbeitsstand
**Dokumentart:** abgeschlossener/historischer Ausführungsnachweis; die verbleibende Umsetzung ist im neuen maßgeblichen Umsetzungsplan geführt.

## 1. Auftrag und verbindliche Grundlagen

Dieser frühere gemeinsame Plan führte die getrennten Umsetzungsstrecken für
[Testumbau V0.12](../Spezifikatonen/Spezifikation_Testumbau_V0.12.md) und
[Speed V0.12](../Spezifikatonen/Spezifikation_Speed_V0.12.md) zusammen.
Er ergänzt deren Anforderungen nicht um einen weiteren fachlichen Umfang.
Es gibt keine parallelen Teilpläne für V0.12. Der Teststrukturteil wurde
am 21.10.2026 ausdrücklich beauftragt und ist mit den in Abschnitt 7
dokumentierten Einschränkungen technisch umgesetzt. Frühere Speed-Arbeiten
umfassten Messung, Kandidatenauswahl und begrenzte Kandidatenversuche. Die
GUI-Taktungs- und SVG-Versuche mit belegter Regression oder unklarem Effekt
wurden zurückgenommen. Die exakte Marker-Geometrieoptimierung ist als
gemessener Teilgewinn dokumentiert; ihre Wirkung gilt nur für die tatsächlich
gemessenen Signale und Szenarien. Weitere Arbeit richtet sich nach der
aktualisierten Speed-Spezifikation und beginnt mit der Wiederverwendung der
vorhandenen Belege, nicht mit einer erneuten Baseline-Messreihe.

Dieser Nachweis bewahrt die frühere Planung, Umsetzung und damaligen
Abnahmestände. Seine Speed-Schritte und -Kriterien sind historisch und
werden nicht als aktuelle Handlungsanweisung verwendet. Die aktuelle
Anforderungsbasis ist die [Speed-Spezifikation V0.12](../Spezifikatonen/Spezifikation_Speed_V0.12.md);
der verbindliche aktuelle Plan ist der
[Umsetzungsplan V0.12](./Umsetzungsplan_V0.12.md).

Es gelten die [Nummerierungsregel](../../../../../.github/instructions/nummerierung.instructions.md),
die [Arbeitsanweisung Releaseumsetzung](../../../../../.github/instructions/releaseumsetzung.instructions.md),
die [Testpflege-Instruction](../../../../../.github/instructions/teststruktur.instructions.md)
und bei einschlägigen Änderungen die
[Schnittstellenregister-Regel](../../../../../.github/instructions/schnittstellenregister.instructions.md).
Commit, Push, Tag und Release sind nicht beauftragt.

Historische V0.11-Dokumente bleiben unverändert. Der Umbau betrifft Tests,
Testkonfiguration und direkt zugehörige Dokumentation, nicht Produktivcode
oder Modelldaten. Der Ordner Optimierung wird nicht als Quelle verwendet.

## 2. Durchführung und Statusführung

- Schritte in der Tabellenreihenfolge und erst nach erfüllten Voraussetzungen
  bearbeiten. Bei Fehlern im Auftragsumfang Ursache untersuchen und beheben;
  keine Fehler durch Skip, Backendwechsel oder Toleranzlockerung verdecken.
- Nach jedem Schritt hier tatsächliche Befehle, Ergebnisse, Belegpfade und
  offene Punkte ergänzen. Unterstützende Mess-/Inventardaten dürfen separat
  liegen, sind aber keine zusätzlichen Anforderungen oder Pläne.
- Für veränderte Testorte eine Zuordnung alter Node-ID zu neuer Node-ID
  beziehungsweise Ersatzvertrag führen. Die Ausgangsliste nicht überschreiben.
- Während lokaler Änderungen gezielt prüfen; vor Abschluss zusammengehöriger
  Umbauten an Sammlung oder globalen Fixtures das Gesamtprofil ausführen.
  Identische Abschlussprüfungen nicht ohne neuen Anlass wiederholen.
- Statuswerte: offen, in Arbeit, blockiert, technisch geprüft, abgenommen.
  Ein Plan, eine Sammlung oder ein vorhandener Test ist kein bestandener
  Lauf. Fehlende Voraussetzungen und Ausgangsfehler bleiben sichtbar.

## 3. Arbeitsschritte und Abhängigkeiten

Die Tabelle beschreibt Arbeitsumfang und Abhängigkeiten. Tatsächliche
Schrittstände und Belege stehen in Abschnitt 7. Die Referenzen in der
zweiten Spalte bezeichnen die Anforderungen aus der Spezifikation.

| Schritt | Anforderungen | Voraussetzung | Arbeit und prüfbares Ergebnis |
|---|---|---|---|
| U-V0.12-000001 | A-V0.12-00001, A-V0.12-00002, A-V0.12-00013, A-V0.12-00014 | Umsetzungsauftrag | Ausgangsstand, Umgebung, Sammlung, Fehler und Testkosten sichern; Abschnitt 3.1. |
| U-V0.12-000002 | A-V0.12-00003, A-V0.12-00004, A-V0.12-00005, A-V0.12-00009, A-V0.12-00010 | U-V0.12-000001 | Verträge und Referenzfälle zuordnen, Auswahl- und Ersatzentscheidungen vor Änderungen festhalten; Abschnitt 3.2. |
| U-V0.12-000003 | A-V0.12-00005, A-V0.12-00006, A-V0.12-00013 | U-V0.12-000002 | Explizite Profile und Marker einrichten, native Prüfungen einbeziehen, Sammlung prüfen; Abschnitt 3.3. |
| U-V0.12-000004 | A-V0.12-00008, A-V0.12-00010, A-V0.12-00013 | U-V0.12-000003 | Gemeinsame Hilfen konsolidieren und Isolation nachweisen; Abschnitt 3.4. |
| U-V0.12-000005 | A-V0.12-00003, A-V0.12-00004, A-V0.12-00007, A-V0.12-00009, A-V0.12-00010, A-V0.12-00014 | U-V0.12-000004 | Thematisch ordnen und belegte Redundanz abbauen; Abschnitt 3.5. |
| U-V0.12-000006 | A-V0.12-00005, A-V0.12-00006, A-V0.12-00010, A-V0.12-00013 | U-V0.12-000005 | Auswahl an konkreten Szenarien und Gesamtprofil funktional prüfen; Abschnitt 3.6. |
| U-V0.12-000007 | A-V0.12-00002, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000006 | Vergleichbare Testkosten- und Performancebelege erstellen; Abschnitt 3.7. |
| U-V0.12-000008 | A-V0.12-00015 | U-V0.12-000007 | Vorhandene aktive Instruction gegen die erprobte Arbeitsweise abgleichen; Abschnitt 3.8. |
| U-V0.12-000009 | A-V0.12-00001, A-V0.12-00013, A-V0.12-00014 | U-V0.12-000008 | Alle Anforderungen, Nachweise und verbleibenden Lücken zur Abnahme zusammenführen; Abschnitt 3.9. |

### 3.1 U-V0.12-000001: Ausgangsstand und Kosten

1. Aktuellen benannten Branch, Revision und uncommittierte Änderungen
   erfassen. Keine fremden Änderungen übernehmen oder verwerfen, keinen
   Branchwechsel durchführen. Den tatsächlich verwendeten V0.11-Teststand
   einschließlich relevanter uncommittierter Inhalte eindeutig identifizieren.
2. Python-/pytest-Version, native Build-Identität, Hardware, Backend,
   Thread-/Prozesszahl und Qt-Konfiguration dokumentieren.
3. Beide Testbereiche sammeln; reguläre Node-IDs und die vier separat
   benannten nativen Prüfdateien gemeinsam inventarisieren.
4. Ausgangsfehler, Skips, Abwahlen und fehlende Voraussetzungen getrennt
   erfassen. Bei nicht lauffähigem Ausgangsstand keine erfolgreiche Baseline
   behaupten; Hindernis dokumentieren und im Auftragsumfang beheben.
5. Vor Änderungen mindestens drei vollständige Läufe unter gleichen
   Bedingungen messen. Sammel-, Setup-, Call-, Teardown- und äußere
   Gesamtkosten berücksichtigen. Ein repräsentatives Iterationsszenario
   bereits jetzt mit ausgewählten Verträgen festlegen und ebenfalls
   mindestens dreimal messen; nachträgliches Schönwählen vermeiden.

**Nachweis:** identifizierter Ausgangsstand, Inventar, genaue Befehle,
Einzelergebnisse und Rohzeiten. Die erfolgreichen früheren Sammelläufe
ersetzen diese Baseline nicht.

### 3.2 U-V0.12-000002: Vertrags- und Fallmatrix

- Bestehende Verträge Themen und Risiken zuordnen: analytische Physik,
  Modellaufbau, Darstellung, Worker, Cache, Backend und native Adapter/Kerne.
- Quader und Kugel für analytische Fälle, Folkeboot für notwendige reale
  Gesamtpfade zuordnen. Anfangszustand, Konfiguration, Schrittzahl und
  Erwartungen festhalten; keine Vollvalidierung des Folkeboots unterstellen.
- Jeden teuren Yachtfall einzeln bewerten: durch einen gleichwertigen
  Referenzfall ersetzen oder fachlich begründet behalten. Ein Modellwechsel
  darf spezifische Geometrie-/Manifestfehler nicht verdecken.
- Optimist nicht als normalen Stabilitätsmaßstab einplanen. Bestehende
  Paket-/Geometrie-/Hydrodynamikverträge erhalten; keine pauschalen Skips.
- Für ähnliche Tests Assertions, Randfälle, Toleranzen und Registerbezüge
  vergleichen. Ersatz muss vor Löschung benannt sein. Adapter- und
  Kerntests nicht als Duplikate behandeln; Legacy-Verträge zuerst prüfen.
- Für das Iterationsszenario direkte und indirekte Verbraucher sowie
  Eskalationsbedingungen benennen.

**Nachweis:** Fall-/Vertragszuordnung und begründete Behalten-/Ersetzen-
Entscheidungen. Kein Pflichtkreuzprodukt aller Körper und Parameter.

### 3.3 U-V0.12-000003: Sammlung und Profile

- Bestehende pytest-Optionen zuerst prüfen; nur nötige Einstellungen ergänzen.
  Marker `integration`, `gui`, `native`, `slow` und nur bei Bedarf
  `performance` registrieren. `slow` anhand der Baseline zuordnen.
- Gesamtprofil über explizite Pfade nach Abschnitt 4 führen. Kein
  standardmäßiges `-m` in `addopts`, kein pauschales Ignorieren nativer Dateien.
- Die vorhandene native Referenz-Fixture im nativen Unterbaum erhalten.
  Sammlung vor/nach der Konfigurationsänderung abgleichen; diese Änderung
  allein darf keine bisherigen Tests verlieren.
- Gezielte Auswahl mit Dateien/Node-IDs bevorzugen. Markerprofile nur für
  fachlich klare Gruppen verwenden; schnell bedeutet nicht automatisch
  ausreichend für jede Änderung.

**Nachweis:** dokumentierte, tatsächlich erprobte Befehle, erwartete und
gesammelte Fallmengen sowie sichtbare Abwahlen. Keine zusätzliche
Auswahlsoftware ohne belegten Bedarf.

### 3.4 U-V0.12-000004: Fixtures und Testhilfen

- Mehrfach verwendete QApplication-, Profil- und Meshaufbauten prüfen und
  nur bei tatsächlicher Gleichartigkeit im passenden Scope konsolidieren.
- Vorhandenen Schutz persönlicher Anwendungseinstellungen erhalten.
  QApplication verlässlich halten, Widgets und Worker gezielt beenden,
  Testdateien bereinigen. Keine gemeinsam veränderlichen Modellzustände.
- Teuren Aufbau aus Import/Sammlung entfernen, sofern vorhanden.
  Produktionsfabriken nur als Eingabegeneratoren nutzen; für deren eigene
  Prüfung unabhängige analytische Referenzen erhalten.
- Betroffene Tests einzeln und zusammen sowie in einer anderen expliziten
  Reihenfolge ausführen. Nach dem Fixture-Arbeitspaket Gesamtprofil prüfen.

**Nachweis:** Setupkostenvergleich, erfolgreiche Isolation und saubere
Ressourcenfreigabe; keine Veränderung persönlicher Konfigurationen.

### 3.5 U-V0.12-000005: Struktur und Redundanz

- Die gemischten historischen Dateien aus der Spezifikation am dann
  aktuellen Inhalt prüfen. Nur nutzbringend nach Themen aufteilen;
  fachlich zusammenhängende Integration darf mehrere Module verbinden.
- Historische Kennungen erhalten. Alte/neue Node-IDs und jede Änderung
  der parametrisierten Fallmenge mit Begründung dokumentieren.
- Nur belegte Redundanz reduzieren. Grenzwerte, Fehlerfälle, analytische
  Unabhängigkeit, strenge Parität und bit-exakte Sequenzen erhalten.
  Keine beiläufige Entfernung eines Produktivmoduls oder Modellkorrektur.
- Import-Schichtregeln per AST, Layout-/Ressourcenregeln passend zu ihrem
  Vertrag prüfen. Keine pauschale Umstellung sämtlicher Prüfungen auf AST.
- Aktuelle Nachweis-/Registerverweise im selben Schritt nachführen.
  V0.11-Historie nicht bearbeiten; alte Verweise über die Zuordnung erklären.

**Nachweis:** lückenloser Vergleich der alten und neuen Fallmengen,
Ersatzbelege für entfernte Assertions, betroffene Tests und Gesamtprofil.

### 3.6 U-V0.12-000006: Auswahl und Sicherheitsnetz

Mindestens folgende Szenarien als konkrete, anhand aktueller Aufrufpfade
begründete Auswahl demonstrieren; keine künstlichen Produktivänderungen nötig:

| Szenario | Erwartete Auswahl / Eskalation |
|---|---|
| Lokale Rechenfunktion | Direkte Unit-/Grenzfälle und betroffene Verbraucher; analytischer Grundkörper genügt, soweit der Vertrag das erlaubt. |
| Gemeinsamer Worker-/Backendvertrag | Zusätzlich Zustands-/Cache-/Serialisierungsintegration und Python/C++-Parität; bei unklarer Reichweite Gesamtprofil. |
| Änderung eines Modells | Dessen Modelltests und betroffene gemeinsame Lader-/Manifestverträge, keine vollständige Yacht-Simulationsmatrix. |
| Globale Fixture-/Sammlungsänderung | Gesamtprofil einschließlich nativer Prüfungen und relevanter GUI-Verträge. |

Gezielte Läufe ausführen und anschließend gegen den Gesamtbefund prüfen.
Ein erfolgreicher Szenarienvergleich ist kein allgemeiner Beweis, dass
automatische Testauswahl jede künftige Regression erkennt.

**Nachweis:** Fallliste, Begründung, Befehle und Ergebnisse; Fehler,
Abwahlen, Skips und fehlende Builds getrennt. Numerische Toleranzen gegen
Ausgangsstand vergleichen.

### 3.7 U-V0.12-000007: Messung und Bewertung

- Iterations- und qualitätsgleiches Gesamtprofil je mindestens dreimal
  unter den Baselinebedingungen ausführen. Auswahlgewinn, Setupgewinn
  und Beschleunigung gleicher Arbeit getrennt ausweisen.
- Je Variante Median, Minimum, Maximum und Rohdaten erfassen.
  Zeitgewinn nur belegt, wenn die Mediandifferenz größer als die größere
  Spannweite ist. Beim Gesamtprofil entsprechend nachgewiesene
  Verlangsamung ausweisen; keinen fehlenden Effekt als Verbesserung melden.
- Produktivpfade nicht nebenbei optimieren. Für den Performance-Nachweis
  eine vorhandene einschlägige Messung auf Grundkörper/Folkeboot wählen,
  Messgrenze und Korrektheitsprüfung dokumentieren. Mindestens ein
  separater Warm-up und fünf Messungen je Variante, ohne konkurrierende
  Last; Build, Rechenpfad, Eingaben und Cachebedingungen vergleichbar halten.
  Ist kein Produktivpfad verändert, dient dies der Prüfung des Messverfahrens,
  nicht der Behauptung eines Produktivgeschwindigkeitsgewinns.
- Profilingkosten von normalen Messungen trennen. Verschachtelte Zeiten
  nicht addieren; Interfacewerte nur nach Registerregel berichten.
- Bei nicht belastbarem Zeitgewinn gezielt die gemessene Ursache bearbeiten
  und betroffene Prüfungen wiederholen. Keine Testverträge kürzen, um das
  Ergebnis passend zu machen. A-V0.12-00012 bleibt ohne Beleg offen.

**Nachweis:** reproduzierbarer Vergleich mit Aussagegrenzen, Rohdatenlinks,
Korrektheitsbelegen und offenem Status bei nicht erreichtem Ziel.

### 3.8 U-V0.12-000008: Pflege-Instruction

Die bereits erstellte aktive Instruction gegen die nun erprobten Profile,
Auswahlentscheidungen, Modellgrenzen und Messregeln prüfen. Nur tatsächlich
nötige Klarstellungen vornehmen; keinen zweiten aktiven Entwurf anlegen.
Frontmatter, Anwendungsbereiche und Links prüfen. Historischen Entwurf
nicht als konkurrierende aktive Regel verwenden.

**Nachweis:** konsistente aktive Instruction, weiterhin begrenzte Geltung
und kein automatischer Altbestandsumbau.

### 3.9 U-V0.12-000009: Abschluss

Rückverfolgbarkeit nach Abschnitt 6 mit tatsächlichen Belegen vervollständigen.
Gesamtprofil aus Abschnitt 3.6/3.7 darf bei unverändertem Stand wiederverwendet
werden; nach testrelevanten Folgeänderungen betroffene Prüfungen erneuern.
Dateiumfang auf V0.11-Unverändertheit und Auftragsgrenzen prüfen.
Technische Umsetzung, bestandene Tests, Performancebeleg und fachliche
Nutzerabnahme getrennt ausweisen. Abschlussprotokoll erst nach tatsächlicher
Umsetzung/Abnahme gemäß Nummerierungsregel ergänzen. Keine Git-Aktion
aus diesem Schritt ableiten.

## 4. Geplante Prüfkommandos

Diese expliziten Befehle wurden für Baseline und Vergleichsläufe verwendet.
Die tatsächlichen Varianten und Ergebnisse stehen in Abschnitt 7 und im
Maschinenbeleg. Der Standardlauf sammelt nach dem Umbau dieselben Bereiche
automatisch; die gültigen Profile stehen auch in
[tests/README.md](../../../../../tests/README.md).
Alle Aufrufe erfolgen vom Repository-Hauptverzeichnis:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest --collect-only -q tests code\cpp\tests\paritaet_batch.py code\cpp\tests\paritaet_frames.py code\cpp\tests\paritaet_koerperkontext.py code\cpp\tests\vertrag_native.py
.\.venv\Scripts\python.exe -m pytest -q --durations=0 tests code\cpp\tests\paritaet_batch.py code\cpp\tests\paritaet_frames.py code\cpp\tests\paritaet_koerperkontext.py code\cpp\tests\vertrag_native.py
```

Für äußere Laufzeitmessungen die Dauer des gesamten jeweiligen Prozesses
zusätzlich erfassen; pytest-Dauern allein enthalten nicht alle Startkosten.
Rückgabecode und Einzelergebnis jedes Laufs festhalten.

Gezielte Dateien/Node-IDs aus der Vertragsmatrix werden in einem Aufruf
kombiniert. Nach registrierter und geprüfter Markierung ist beispielsweise
`-m "not slow and not gui and not integration"` ein explizites
Iterationsprofil, niemals automatisch ausreichende Abdeckung.
Ein Gesamtprofil erhält keinen solchen Filter.
Wiederholte Produktivbenchmarks werden separat nach dem in
U-V0.12-000007 ausgewählten vorhandenen Werkzeug dokumentiert, nicht als
ungeprüfter neuer Werkzeugaufruf erfunden.

Vor einem später ausdrücklich beauftragten Commit bleibt zusätzlich
der vorgeschriebene Aufruf aus der Release-Instruction erforderlich;
das native Gesamtprofil wird dadurch nicht automatisch ersetzt.

## 5. Meilensteine

| Meilenstein | Eintritt | Abnahme / Beleg |
|---|---|---|
| M1 – belastbare Ausgangsbasis | Umsetzungsauftrag; U-V0.12-000001 und U-V0.12-000002 bearbeitet | Identifizierter Ausgangsstand, vollständiges Inventar, Baselinezeiten, Fehlerliste und begründete Vertrags-/Referenzmatrix. |
| M2 – funktional geordnete Suite | M1 erfüllt; U-V0.12-000003 bis U-V0.12-000006 bearbeitet | Keine ungeklärten Fallverluste, Isolation und Parität erhalten; gezielte Profile und Gesamtprofil tatsächlich geprüft. |
| M3 – messbarer Nutzen und Pflege | M2 erfüllt; U-V0.12-000007 und U-V0.12-000008 bearbeitet | Messverfahren reproduzierbar; Iterationszeitgewinn belegt, keine nachgewiesene Gesamtprofil-Verlangsamung; aktive Instruction konsistent. Ohne Zeitbeleg nicht erreicht. |
| M4 – fachlicher Abschluss | M3 erfüllt; U-V0.12-000009 bearbeitet | Alle aktiven Anforderungen mit U-/Test-/Messbelegen zugeordnet; bekannte Abweichungen offen, fachliche Abnahme gesondert bestätigt. |

## 6. Rückverfolgbarkeit und Vollständigkeitsprüfung

**Plan-/Nachweisprüfung am 21.10.2026:** Alle 15 aktiven Anforderungen der
Spezifikation sind mindestens einem Schritt und einem geplanten
Abnahmekriterium zugeordnet. Es wurden keine zusätzlichen A-Kennungen
vergeben. Die tatsächlichen Prüfungen und Einschränkungen stehen unten.
Technische Prüfung ist keine fachliche Nutzerabnahme.

| Aktive Anforderungs-ID | Spezifikation/Abschnitt | Umsetzungsschritt(e) | Test/Abnahmekriterium | Status |
|---|---|---|---|---|
| A-V0.12-00001 | 1 | U-V0.12-000001, U-V0.12-000009 | Ausgangs-/Abschluss-Dateivergleich; V0.11 unverändert, keine beiläufigen Produktivänderungen; M1/M4. | technisch geprüft |
| A-V0.12-00002 | 2, 6 | U-V0.12-000001, U-V0.12-000007 | Inventar einschließlich vier nativer Prüfdateien; Befehle, Umgebungen, Rohzeiten und Fehlerstatus; M1/M3. | technisch geprüft; GPU-Baseline eingeschränkt |
| A-V0.12-00003 | 4 | U-V0.12-000002, U-V0.12-000005 | Quader/Kugel/Folkeboot-Vertragsmatrix, begründete Ausnahmen statt Yacht-Kreuzprodukt; M1/M2. | technisch geprüft |
| A-V0.12-00004 | 4 | U-V0.12-000002, U-V0.12-000005 | Kein Optimist-Stabilitätsmaßstab; Modellverträge erhalten oder belegter Ersatz; M2. | technisch geprüft |
| A-V0.12-00005 | 5 | U-V0.12-000002, U-V0.12-000003, U-V0.12-000006 | Vier Auswahlszenarien mit Verbrauchern, Grenzflächen und Eskalation; M2. | technisch geprüft |
| A-V0.12-00006 | 5 | U-V0.12-000003, U-V0.12-000006 | Geprüfte Sammlung/Profile, kein versteckter Filter, native Fixtures und vier Prüfdateien enthalten; M2. | technisch geprüft |
| A-V0.12-00007 | 7 | U-V0.12-000005 | Bewertete Themenstruktur und vollständige alte/neue Node-ID-Zuordnung; M2. | technisch geprüft |
| A-V0.12-00008 | 7 | U-V0.12-000004 | Einzel-/Gruppen-/Reihenfolgeprüfung; Einstellungen, Qt, Worker und mutable Daten isoliert; M2. | technisch geprüft |
| A-V0.12-00009 | 7 | U-V0.12-000002, U-V0.12-000005 | Assertion-/Grenzfallvergleich und tragender Ersatz für jede Entfernung; M2. | technisch geprüft |
| A-V0.12-00010 | 7 | U-V0.12-000002, U-V0.12-000004, U-V0.12-000005, U-V0.12-000006 | Toleranzvergleich, analytisch unabhängige Referenzen, Parität/bit-exakte Verträge; M2. | Verträge unverändert; Optimist-Parität offen |
| A-V0.12-00011 | 6 | U-V0.12-000007 | Messverfahren mit Warm-up, fünf Messungen je Variante, Rohdaten und Korrektheitsprüfung; keine unbelegte Produktivbeschleunigung; M3. | Messverfahren geprüft; keine Produktivänderung |
| A-V0.12-00012 | 6 | U-V0.12-000007 | Drei Suite-/Iterationsläufe je Stand; Mediandifferenz über Streuungsgrenze und kein belegter Gesamtprofilrückschritt; M3. | offen: kein belastbarer Iterationsgewinn |
| A-V0.12-00013 | 5 | U-V0.12-000001, U-V0.12-000003, U-V0.12-000004, U-V0.12-000006, U-V0.12-000009 | Fehler-/Skip-/Abwahlliste, fehlende Voraussetzungen sichtbar; kein stiller Ersatzpfad; M1/M2/M4. | technisch geprüft |
| A-V0.12-00014 | 8 | U-V0.12-000001, U-V0.12-000005, U-V0.12-000009 | Vollständige Zuordnung, aktuelle Registerlinks und unveränderte V0.11-Historie; M4. | Zuordnung geprüft; Gesamtfreigabe offen |
| A-V0.12-00015 | 1, 3 | U-V0.12-000008 | Eine aktive Instruction mit passenden Regeln, gültigem Frontmatter und Links; M3. | technisch geprüft |

## 7. Tatsächliche Nachweise und offene Punkte

### 7.1 Maschinenbeleg und realisierte Struktur

Der [Maschinenbeleg vom 21.10.2026](../Messungen/Teststruktur_Nachweis_2026-10-21.json)
enthält Ausgangsrevision, Testquellhashes, Umgebungsdaten, Befehle, Rohzeiten,
Fehlermeldungen, Modell-/Native-Identitäten, Messmethodenprüfung und die
vollständige Zuordnung aller alten auf neue Node-IDs.
Die technischen Profilbefehle stehen in
[tests/README.md](../../../../../tests/README.md).

- Alle **904 ursprünglichen Testfunktionen** erhalten, **36 Funktionen**
  thematisch verschoben. Neue Fachdateien statt der gemischten
  Schritt-/Revisions-/Referenzpfad-Dateien; schwere Hydrostatik/Dynamik-
  Integration aus der Unit-Datei herausgelöst.
- **1.765 alte auf 1.752 neue Fälle** vollständig zugeordnet.
  13 Modellvarianten entfallen, nicht 13 Testverträge:
  vier doppelte Integratorbilanzfälle (synthetischer Fall/Folkeboot bleiben),
  vier Optimist-Residuenfälle (gleiche negativen Assertions auf `yacht1`,
  positiver Folkeboot-Fall mit/ohne Zusatzmodelle bleiben),
  vier native Solver-Modellvarianten (beide Solver auf Folkeboot bleiben)
  und ein 1.000-Schritt-Yachtfall (Folkeboot bleibt).
- Der bereits fehlschlagende Optimist-Paritätsfall bleibt als
  `diagnostic` im ungefilterten Gesamtprofil enthalten. Keine Skip-/Xfail-
  Umwandlung, keine Toleranzlockerung. Günstige modellspezifische Paket-/
  Geometrieprüfungen bleiben bestehen.
- Standardmäßige native Sammlung und registrierte Marker, keine versteckte
  Abwahl. Die eigene native Python-Referenz-Fixture bleibt unverändert.
- Gemeinsame `qapp`- und `profildatei`-Fixtures, Einstellungsschutz erhalten;
  Quader-Eingaben für Glanz aus vorhandener Formfabrik. Unabhängige
  analytische Schalenreferenzen bleiben separat.
- Legacy-Importregel per AST; Layout-/Ressourcentests unverändert.
  Negative Renderer-Bestandsverträge sowie J9/W2 bleiben erhalten, da keine
  ausreichende Begründung für ihre ersatzlose Entfernung vorliegt.
- Aktuelles Schnittstellenregister geprüft: keine Verweise auf die vier
  ersetzten Testdateinamen gefunden, keine Interface-/Statusänderung.
  Historische V0.11-Dokumente und Produktivpfade unverändert.

### 7.2 Testergebnisse

| Prüfung | Tatsächliches Ergebnis |
|---|---|
| Ausgangssammlung | 1.765 Fälle einschließlich vier nativer Prüfdateien. |
| Drei Ausgangsläufe mit expliziter GPU-Abwahl | Je 1.761 bestanden, 2 fehlgeschlagen, 1 übersprungen, 1 abgewählt. |
| Drei Nachherläufe mit derselben GPU-Abwahl | Je 1.748 bestanden, dieselben 2 Fehler, 1 übersprungen, 1 abgewählt. |
| Abschließender Standardlauf ohne Abwahl | **1.749 bestanden, 2 bekannte Ausgangsfehler, 1 übersprungen**; GPU und native Prüfungen mit ausgeführt. |
| Explizites Kurzprofil ohne slow/gui/integration/hardware | 1.131 bestanden, 1 übersprungen, 620 abgewählt; 23,78 s äußere Laufzeit, kein Gesamtnachweis. |
| Qt-/Profil-/Einstellungsfixtures in anderer Dateireihenfolge | 84 bestanden. |
| Folkeboot-/Optimist-Paket-, Mesh- und Laderverträge | 50 bestanden. |
| Native Folkeboot-/Batch- und Qt-/Profilverträge | 108 bestanden; der bekannte diagnostische Paritätsfall explizit abgewählt und separat im Gesamtprofil geprüft. |
| Gezielte Integrator-/Residuenfälle nach Fallreduktion | 12 bestanden. |

Der erste ungekürzte Ausgangslauf hing nach 1.427 abgeschlossenen Fällen
beim echten OpenCL-Vektoradditionstest und wurde gezielt beendet.
Für faire Wiederholungsmessungen wurde genau dieser Fall auf beiden Ständen
explizit abgewählt. Eine spätere isolierte Prüfung und der abschließende
Standardlauf bestanden diesen Hardwaretest. Die Ursache des ersten Hängers
ist nicht geklärt; kein GPU-Fix wird behauptet.

**Unveränderte Ausgangsfehler:**

1. `test_referenzmanifest_umfasst_modelle_konfiguration_und_optik`:
   historischer V0.10-Referenzhash stimmt für
   `konfigurationen/settings.json` nicht mit dem aktuellen Stand überein.
   Kein Lockern des Referenzwächters oder Zurücksetzen der Einstellungen.
2. `test_nativer_batch_gegen_jeden_referenzschritt[optimist]`:
   Kraftabweichung etwa `1.01024256e-9` bei `atol=1e-9`.
   Test bleibt fehlgeschlagen sichtbar; kein pauschales Beheben durch
   Modellwechsel, Skip oder größere Toleranz.

Diese Befunde wurden vor dem Umbau reproduziert und werden nicht als neue
Regressionen oder als bestandene Prüfungen ausgegeben.

### 7.3 Zeit- und Performancenachweis

Jeweils drei äußere Prozesslaufzeiten, gleiche Aufrufe/Messbedingungen
bis auf dokumentierte Testorte und Modellvarianten:

| Profil | Vorher Median / Spannweite | Nachher Median / Spannweite | Bewertung |
|---|---|---|---|
| Vergleichs-Gesamtprofil ohne GPU-Fall | 170,50 s / 2,97 s | 150,02 s / 1,80 s | 20,48 s bzw. 12,01 % weniger; Differenz größer als Streuungsgrenze. |
| Kurzes Iterationsszenario Materialglanz + Frames + native Grafikgeometrie | 1,091 s / 0,564 s, 32 Fälle | 1,347 s / 0,421 s, 29 Fälle | Kein belastbarer Gewinn und nach derselben Regel kein belegter Rückschritt; A-V0.12-00012 bleibt offen. |

Die Gesamtzeitreduktion stammt aus vermiedener redundanter Modellarbeit,
nicht aus schnellerem Produktivcode. Die 13 reduzierten Modellvarianten
und Ersatzverträge sind im Maschinenbeleg einzeln zugeordnet.
Der ungefilterte Abschlusslauf dauerte 154,53 s; er ist kein Teil des
dreifachen Vorher-/Nachhervergleichs.

Das bestehende Mess-/Vergleichswerkzeug wurde mit unverändertem Produktivcode
am Folkeboot erprobt: 100 native Einzelschritte gegen einen nativen
100-Schritt-Batch, getrenntes Warm-up, fünf alternierende Messungen je
Variante. Jeder gemessene Endzustand war exakt gleich. Rohzeiten,
Messgrenze, native Build-/Modelldateihashes und Parameter stehen im Beleg.
Das ist ein Verfahrensnachweis, kein neu erzielter Produktivgeschwindigkeitsgewinn
und kein isolierter Interface-Performanceeintrag.

### 7.4 Schritt- und Meilensteinstand

| Schritt | Tatsächlicher Stand |
|---|---|
| U-V0.12-000001 | Technisch geprüft; Ausgangsfehler und abgebrochener erster GPU-Lauf dokumentiert, drei vergleichbare eingeschränkte Baselines vorhanden. |
| U-V0.12-000002 | Technisch geprüft; Fall-/Vertragsmatrix und Ausnahmen im Maschinenbeleg zugeordnet. |
| U-V0.12-000003 | Technisch geprüft; Standardsammlung, Marker und explizite Profile erprobt. |
| U-V0.12-000004 | Technisch geprüft; gemeinsame Fixtures und andere Dateireihenfolge getestet. |
| U-V0.12-000005 | Technisch geprüft; alle Funktionen erhalten und alle Fallreduktionen zugeordnet. |
| U-V0.12-000006 | Technisch geprüft mit Einschränkung: keine neuen Fehler, aber keine grüne Gesamtsuite wegen der beiden Ausgangsfehler. |
| U-V0.12-000007 | Teilweise erfüllt; Gesamtzeitgewinn und Messverfahren belegt, Iterationsgewinn nicht belegt. |
| U-V0.12-000008 | Technisch geprüft; aktive Instruction und erprobte Testanleitung konsistent. |
| U-V0.12-000009 | Nachweise zusammengeführt; uneingeschränkter fachlicher Abschluss blockiert. |

M1 ist mit den dokumentierten Baselinegrenzen nachgewiesen.
M2 ist technisch geprüft, aber wegen der beiden bestehenden Testfehler
nicht uneingeschränkt bestanden. M3 bleibt wegen des fehlenden belastbaren
Iterationsgewinns offen; damit ist auch M4 nicht erreicht.

**Offene nächste Entscheidungen/Arbeiten:** Die beiden Ausgangsfehler
getrennt fachlich klären, ohne Testverträge zu schwächen. Für das bereits
sehr kurze Iterationsszenario ist kein weiterer sicherer Kostentreiber
belegt; weder einen Zeitgewinn erfinden noch eigenmächtig das Abnahmekriterium
ändern. Fachliche Gesamtfreigabe bleibt ausdrücklich offen.

## 8. Historischer Speed-Arbeitsstand

Die folgenden Schritte, Kriterien und Statusangaben dokumentieren den
früheren Speed-Planungs- und Ausführungsstand. Für verbleibende Arbeiten ist
ausschließlich der neue
[Umsetzungsplan V0.12](./Umsetzungsplan_V0.12.md) maßgeblich. Die vorhandene
Diagnosemessung im Gespräch war nur ein
Hinweis für die Kandidatensuche: Sie erfasste sieben Wiederholungen
ausgewählter Wrapper, aber keine reproduzierbaren Rohdaten, vollständige
Umgebungs-/Buildidentität oder End-to-End-Wirkung. Sie ist deshalb weder
V0.12-Baseline noch Registermessbeleg und wird nicht als Abnahme verwendet.

### 8.1 Reihenfolge und Abhängigkeiten

| Historischer Umsetzungsschritt | Anforderungen | Voraussetzung | Damals geplante Arbeit und prüfbares Ergebnis |
|---|---|---|---|
| U-V0.12-000010 | A-V0.12-00001, A-V0.12-00002, A-V0.12-00007 | Speed-Arbeitsauftrag; vorhandene Messbelege verfügbar | Vorhandene Messungen samt Werten, Bedingungen, Messgrenzen und Rohdatenverweisen inventarisieren und als Referenz übernehmen. Nur bisher nicht erhobene, notwendige Messwerte ergänzen; Baseline- und bereits erfolgte Kandidatenmessungen nicht wiederholen. |
| U-V0.12-000011 | A-V0.12-00003, A-V0.12-00008, A-V0.12-00009, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000010 | Tatsächliche Aufrufpfade, Häufigkeiten und Kosten der relevanten bestehenden Funktionen aus vorhandenen Profilen auswerten; fehlende Profile nur für ausgewählte Kandidaten und noch unbeantwortete Messfragen erheben. Kandidaten gemäß Spezifikation und ihrem tatsächlichen Einsatzpfad eingrenzen. |
| U-V0.12-000012 | A-V0.12-00002, A-V0.12-00003, A-V0.12-00006, A-V0.12-00008, A-V0.12-00010, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000010, U-V0.12-000011 | Relevante Szenarien, Messgrenzen, Pflichtszenarien und vorab festgelegte Unsicherheitsauswertung bestimmen. Kandidatenentscheid anhand vorhandener Baselines und Profile begründen; keine absolute Mindestverbesserung festsetzen und Messlücken nicht durch Wiederholung bereits erhobener Messungen schließen. |
| U-V0.12-000013 | A-V0.12-00003, A-V0.12-00004, A-V0.12-00005, A-V0.12-00006, A-V0.12-00008, A-V0.12-00009, A-V0.12-00010, A-V0.12-00011, A-V0.12-00012 | U-V0.12-000011, U-V0.12-000012; zusätzlicher ausdrücklicher Produktivänderungsauftrag erforderlich | Nur nachgewiesen relevante, im Umfang liegende Kandidaten untersuchen bzw. nach gesonderter Freigabe implementieren. Näherungen bleiben ohne vorherige fachliche Freigabe ausgeschlossen. |
| U-V0.12-000014 | A-V0.12-00004, A-V0.12-00005, A-V0.12-00006, A-V0.12-00007, A-V0.12-00009, A-V0.12-00010, A-V0.12-00011 | U-V0.12-000013; für die Messung passende vorhandene Referenzwerte gemäß U-V0.12-000010 | Korrektheit und Stabilität gezielt prüfen; Kandidatenwerte unter vergleichbaren Bedingungen erheben. Vorhandene, methodisch passende Referenzmessungen wiederverwenden, neue Werte nur für bisher nicht gemessene Kandidatenläufe aufnehmen und Regressionen in jedem Pflichtszenario bewerten. |
| U-V0.12-000015 | A-V0.12-00001 bis A-V0.12-00012 | U-V0.12-000010 bis U-V0.12-000014, soweit U-V0.12-000013 freigegeben wurde | Mess-/Registerangaben und Rückverfolgbarkeit mit tatsächlichen Werten, Unsicherheiten, Nichtwiederholungsentscheidungen, Regressionen und offenen Punkten aktualisieren. Keine ungemessenen Einzelkosten ableiten; keine Anforderung als abgenommen markieren, wenn ihr Nachweis fehlt. |

Es bestehen keine impliziten Abhängigkeiten zu U-V0.12-000001 bis
U-V0.12-000009. Die in Abschnitt 7 dokumentierten Teststruktur-Befunde und
offenen Ausgangsfehler bleiben unabhängig sichtbar; sie dürfen weder als
Speed-Ergebnis noch als Grund für das Auslassen passender Korrektheitsprüfungen
umgedeutet werden.

### 8.2 U-V0.12-000010: reproduzierbare V0.12-Baseline

1. Vor der Messung Commit, Branch, Arbeitsbaumstatus und betroffene
   uncommittierte Änderungen erfassen. Die Basisrevision aus der
   Speed-Spezifikation ist nicht ungeprüft als exakter Messstand anzunehmen;
   der tatsächliche Quell- und Buildstand ist zu sichern. Keine fremden
   Änderungen übernehmen oder verwerfen.
2. Hardware, Betriebssystem, Python, Compiler, native Binärdatei/ABI,
   Abhängigkeiten, Rechenpfad, Thread-/Prozesszahl und Qt-/Renderumgebung
   festhalten. Eingaben, Modellhash, Konfiguration, Batch-/Schrittzahl,
   Warm-up, Start-/Endgrenze und Messmodus protokollieren.
3. Zuerst vorhandene Werkzeuge verwenden, insbesondere
   `werkzeuge/benchmark_gui_live.py`, `werkzeuge/benchmark_profil.py` und
   `werkzeuge/migration_native_m2.py`, soweit deren Messgrenzen zum
   untersuchten Pfad passen. Diagnoseprofile mit Instrumentierungs-Overhead
   von uninstrumentierten Leistungsläufen trennen. Ein neues Messwerkzeug nur
   ergänzen, wenn die benötigte Grenze mit vorhandenen Werkzeugen nicht
   zuverlässig erfasst werden kann.
4. Physik-/Workerpfad und GUI-Pfad getrennt erfassen. Kaltstart/Setup und
   wiederholten Warm-Pfad getrennt behandeln, falls beide für die Nutzung
   relevant sind. Für jede Variante einen separaten Warm-up und mindestens
   fünf Messläufe durchführen; Rohwerte, Median und vorab festgelegtes
   Streuungsmaß ablegen.
5. Während der Variantenmessungen keine konkurrierende Test- oder
   Benchmarklast ausführen. Fehlende Geräte-/Renderbedingungen, ungültige
   Läufe, Fehler oder abgebrochene Messungen sichtbar dokumentieren und
   nicht durch günstige Ersatzläufe stillschweigend ersetzen.

**Abnahme:** Ein reproduzierbarer Baseline-Beleg liegt mit vollständiger
Messgrenze, Rohdaten und Umgebungsidentität vor. Er weist tatsächliche
End-to-End-Zeiten aus und ist nicht lediglich eine Profilausgabe oder
Mikrobenchmarkreihe.

### 8.3 U-V0.12-000011: Aufrufpfade und Kandidaten

- Für Kandidaten zuerst den produktiven Aufrufpfad und alle relevanten
  Verbraucher feststellen. Insbesondere klären, ob der Wrapper im
  GUI-Hauptprozess, Physik-Workerprozess, nur im Diagnosepfad oder im
  relevanten Szenario überhaupt ausgeführt wird.
- Aufrufzahl, Einzeldauer und Anteil an der gemessenen Gesamtzeit ermitteln.
  Verschachtelte Zeiten nicht addieren. Profilierung darf die Rangfolge
  vorschlagen, aber die tatsächlichen Einzelmessungen und uninstrumentierten
  End-to-End-Zeiten nicht ersetzen.
- Python-Referenz und nativen Wrapper mit identischen realistischen Eingaben,
  identischer Ausgabeaufbereitung und dokumentierten Konvertierungs-/Adapter-
  kosten vergleichen. Mindestens fünf Messungen je Variante plus Warm-up;
  Rohwerte und Streuung sichern. Bei vernachlässigbarem Szenarioanteil trotz
  großer Mikrobenchmarkdifferenz den Kandidaten nicht priorisieren.
- Die bisherigen auffälligen Wrapper – Quaternion-Normalisierung/-Matrix,
  Winkel-/Richtungshelfer und SVG-/Einheitenhelfer – bleiben lediglich
  Suchkandidaten. Der beobachtete schnellere C++-Pfad für
  `pose_mit_gelenkwinkel` ist ein Gegenbeispiel gegen pauschale
  Rückschaltung. Keiner dieser Diagnosewerte wird ungeprüft als V0.12-
  Leistungseintrag übernommen.

**Abnahme:** Kandidatenmatrix mit CPPI-ID, tatsächlichem Aufrufpfad,
Aufrufzahl, Anteil/Blockzeit, Messmethode, Streuung, betroffenem Vertrag,
Mikrobenchmark und Relevanz für End-to-End liegt vor. Nicht direkt gemessene
Interfaces bleiben als solche gekennzeichnet.

### 8.4 U-V0.12-000012: primäres Szenario und Entscheidungstor

1. Nach der Baseline das primäre, nutzungsrelevante End-to-End-Szenario
   anhand der gemessenen Engpässe bestimmen und vor Änderungen unveränderlich
   protokollieren. Falls ein realer Yachtpfad relevant ist, Folkeboot
   verwenden; analytische Quader- und gegebenenfalls Kugelfälle decken
   gezielte Fachverträge ab. Kein routinemäßiges Testen aller Yachten.
2. GUI- und Physik-/Workerpfad nur dann als Pflichtszenarien aufnehmen, wenn
   sie von der Änderung betroffen oder für die Nutzungsentscheidung
   erforderlich sind. Den bekannten instabilen Optimist nicht als
   allgemeinen Stabilitäts- oder Performance-Abnahmemaßstab verwenden;
   bereits bestehende spezifische Verträge bleiben davon unberührt.
3. Messgrenze und Streuungsregel vor der Kandidatenmessung festhalten.
   Kandidat und Baseline müssen dieselben Eingaben, Schritte, Prozess- und
   Threadbedingungen verwenden. Für den Primärpfad zählen vollständige
   Nutzerkosten einschließlich relevanter Worker-/Übergabe- und
   GUI-Kosten, nicht die Summe verschachtelter Profilblöcke.
4. Vor einer Änderung festhalten, welche Kandidaten weiterverfolgt und
   welche ausgeschlossen werden, jeweils mit Profil-/Aufrufnachweis,
   erwarteter End-to-End-Wirkung, Risiko und betroffenen Tests.

**Historischer Abschlussvermerk:** Primärszenario, Pflichtszenarien,
Messgrenze, Streuungsmaß und Kandidatenentscheidung wurden im früheren
Planungsstand dokumentiert; die aktuelle Regelung steht in der
Speed-Spezifikation und im neuen Umsetzungsplan.

### 8.5 U-V0.12-000013: mögliche exakte Produktivänderung

Im Rahmen des Auftrags zur vollständigen Planumsetzung wurden zwei begrenzte
GUI-Taktungsvarianten experimentell geprüft: Backpressure an ausstehende
Qt-Swaps und eine zusätzliche Aktualisierung nach dem Swap. Beide Varianten
wurden zurückgenommen: Die Swap-Intervalle verbesserten sich, aber die
gemeldete Animationsrate sank relevant.

Ein exakter Kandidat wurde geprüft: Die Profildiagnose verzeichnete 2.615
PyVista-`Sphere`-Erzeugungen bei kleinen Kraft- und Momentmarkern. Eine auf
acht Radien begrenzte Vorlagen-Cache-Funktion erzeugt pro Aufruf eine
unabhängige Kopie und verschiebt nur deren Punkte. Punkte, Flächen und
Normalen stimmten in gezielten Tests bitgenau mit direkt erzeugten
PyVista-Kugeln überein; Kraftwerte, Schwellen und Darstellungsgrößen blieben
unverändert. Fünf gültige Vergleichsläufe ergaben einen um 10,2 % niedrigeren
Swap-Intervall-Median (168,30 auf 151,20 ms) und eine um 11,2 % höhere
gemeldete Animationsrate (10,7 auf 11,9 Render/s). Der Kandidat verschlechtert
die geprüften GUI-/Physiksignale nicht, verfehlt aber das 20-%-Ziel.

Ein zusätzlicher exakter Kandidat sollte redundante SVG-Aufbereitung bei
identischen Navigations- oder Geschwindigkeitsanzeigen überspringen. Der
kombinierte Stand aus Marker- und SVG-Änderung wurde in zehn gültigen Läufen
geprüft. Sein Swap-Intervall-Median lag 4,9 % unter der Baseline, die
Run-Median-Spannweite überlappte jedoch die Baseline. Zudem verschlechterten
sich im kombinierten Vergleich der Median der Pose-Aufbereitung um 23,2 %,
der Worker-Roundtrip um 27,4 %, die Eingabelatenz um 4,1 % und das
95-%-Swap-Intervall um 3,3 %; der höchste gemessene Rückstand betrug 1,661 s
statt 1,220 s in der Baseline. Die Animationsrate streute von 8,7 bis
12,8 Render/s. Damit ist kein belastbarer positiver End-to-End-Effekt
nachgewiesen; die SVG-no-op-Änderung und ihre Tests wurden zurückgenommen.
Einzelwerte und Rohdateien stehen im
[Kandidatenvergleich](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json).

Ein weiterer exakter Versuch ersetzte die wiederholte
`ElementTree`-Serialisierung durch eine vorab serialisierte SVG-Vorlage mit
bytegleichen dynamischen Feldersetzungen. Die gezielten Tests bestätigten
bytegleiche XML-Ausgabe; 328 Profil-, Kraftdarstellungs-, Integrations- und
Widgettests bestanden. In fünf gültigen End-to-End-Läufen lag der
Swap-Intervall-Median jedoch bei 178,82 ms statt 168,30 ms Baseline
(6,3 % langsamer). Alle Laufmediane (174,44–182,45 ms) lagen oberhalb des
Baselinebereichs (162,66–172,11 ms). Der Kandidat und seine Zusatztests
wurden deshalb entfernt; die Messdateien bleiben als verworfener Versuch
erhalten.

Die Marker-Geometrieoptimierung bleibt als exakter, bitgenau geprüfter
Teilfortschritt im Arbeitsstand. Ihre Fünf-Lauf-Serie weist für die dort
gemessene Qt-Swap-Metrik einen niedrigeren Median aus. Die gemischte
Zehn-Lauf-Serie ist kein Ersatz für die Marker-only-Serie und belegt keine
zusätzliche Wirkung des kombinierten Kandidaten. Die aktuellen
Abnahmekriterien ergeben sich aus A-V0.12-00006 der Speed-Spezifikation;
die Messungen werden nicht erneut ausgeführt.

Für weitere Kandidaten gilt:

- Nur Änderungen am nachgewiesenen Engpass durchführen; keine pauschale
  Umschaltung aller nach Einzelbenchmark langsamen CPPI-Schnittstellen.
- Bei selektiver Python-Rückschaltung die Auswahl im produktiven Aufrufpfad
  präzise begrenzen. Globalen Rechenpfad, öffentliche Signaturen,
  Datenverträge und andere unbeteiligte Interfaces nicht unbeabsichtigt
  ändern.
- Exakte Optimierung und Approximation klar trennen. Voxel-, Delta-Cache-
  oder sonstige Näherungsverfahren sind ohne die vorherige fachliche
  Entscheidung und Nachweise nach A-V0.12-00005 ausgeschlossen.
- Vorher-/Nachher-Quellstände und native Builds unverwechselbar sichern;
  für einen fairen Vergleich müssen beide Varianten vom gleichen Stand
  ausgehen. Keine Testtoleranz, Modellkonfiguration oder Messgrenze zugunsten
  des Kandidaten ändern.

**Historischer Abschlussvermerk:** Jede damals ausgeführte Änderung und
Rücknahme ist in diesem Nachweis beschrieben. Die Kriterien für verbleibende
Arbeit stehen im aktuellen Umsetzungsplan.

### 8.6 U-V0.12-000014: Korrektheit und Vorher-/Nachher-Messung

- Geänderte Schnittstellen mit den passenden gezielten Tests und
  unabhängigen Referenzen abdecken. Bei geändertem Python/C++-Verhalten
  relevante Paritäts-, Randfall- und Validierungstests auf beiden Pfaden
  ausführen; analytische Grundkörper und erforderliche Folkeboot-Integration
  getrennt bewerten.
- Der damalige Plan sah einen Vorher-/Nachher-Vergleich mit mindestens fünf
  Messungen je Variante vor. Aktuelle Messvorgaben, insbesondere das
  Wiederverwenden bereits erfolgter Messungen, stehen in A-V0.12-00001 und
  A-V0.12-00007 der Speed-Spezifikation.
- Die frühere 20-%-Akzeptanzschwelle ist überholt. Für aktuelle Bewertung
  gelten A-V0.12-00006 der Speed-Spezifikation und der neue Umsetzungsplan:
  kein Mindestgewinn, Unsicherheit transparent ausweisen und Regressionen
  je Pflichtszenario beurteilen.
- Testergebnisse als bestanden, fehlgeschlagen oder nicht ausgeführt
  ausweisen. Bestehende Fehler, fehlende Hardware-/Rendernachweise und
  sonstige Einschränkungen nicht als neue Regression oder Erfolg
  umdeuten.

**Historischer Abschlussvermerk:** Korrektheit und Leistung sind getrennt
dokumentiert. Eine aktuelle Speed-Abnahme ist mit diesem historischen
Abschnitt nicht verbunden.

### 8.7 U-V0.12-000015: Register und Abschluss

- Betroffene CPPI-Einträge im
  [Schnittstellenregister](../../../../Dokumentation/Schnittstellenregister_CPP.md)
  anhand der tatsächlichen Python-/C++-Vertragsquelle und des Aufrufpfads
  aktualisieren. Implementierung, Anbindung, tatsächliche Nutzung und
  Performance getrennt bewerten.
- Neue V0.12-Werte nur bei gültigen, vergleichbaren und belegten Messungen
  aufnehmen; V0.10-Werte unverändert historisch erhalten. Adapter- und
  End-to-End-Kosten als solche kennzeichnen. Ohne isolierte Einzelmessung
  `nicht separat gemessen` angeben, nicht aus Elternblöcken ableiten.
- Unterstützende Rohdaten und Umgebung separat unter
  `zuV0.12/Messungen/` ablegen und aus diesem einzigen Plan verlinken.
  Keine zusätzliche Spezifikation und keinen Nebenplan erzeugen.
- Abschließend jede aktive A-Kennung gegen Schritte, tatsächlich ausgeführte
  Tests, Messnachweise und offene Punkte abgleichen. Produktivänderung,
  erfolgreiche Tests, erfülltes Performanceziel und fachliche Abnahme als
  getrennte Statusaussagen führen.

**Abnahme:** Rückverfolgbarkeit für A-V0.12-00001 bis A-V0.12-00006 ist
vollständig, Nachweislücken sind sichtbar und das Register enthält keine
unbelegten Leistungs- oder Statusbehauptungen.

### 8.8 Speed-Meilensteine und Rückverfolgbarkeit

| Historischer Meilenstein | Damaliges Prüfkriterium | Tatsächlicher Stand zum dokumentierten Zeitpunkt |
|---|---|---|
| SP1 – Baseline und Nutzungspfad | Reproduzierbare Baseline, Messgrenze und Build-/Quellidentität vorhanden. | Technisch erfüllt mit Einschränkung: fünf gültige Folkeboot-GUI-Läufe; Quell- und Binärhashes dokumentiert. Compileridentität und ein separates natives End-to-End-Szenario fehlen. |
| SP2 – Kandidatenentscheidung | Relevante Aufrufpfade, Kandidaten und Primärszenario belegt; Kandidaten begründet priorisiert oder verworfen. | Technisch bearbeitet: Profile, Wrappermessungen und GUI-Kandidatenauswahl liegen vor. Szenario und Akzeptanzkriterien sind nachvollziehbar, aber nicht nachweislich vor dem ersten Kandidatenlauf separat festgeschrieben worden. |
| SP3 – Umsetzung und Verifikation | Kandidatenversuche geprüft; nur fachlich und messseitig akzeptable Änderungen bleiben bestehen. | Teilweise erfüllt: zwei GUI-Taktungsvarianten, SVG-no-op und SVG-Vorlagenserialisierung verworfen; die exakte Marker-Geometrieoptimierung bleibt als Teilfortschritt und erreicht in fünf Läufen 10,2 %, nicht 20 %. |
| SP4 – Speed-Abnahme | Aktive Anforderungen, Nachweise und offene Punkte abgeglichen; A-V0.12-00006 nur bei erfülltem End-to-End-Kriterium abgenommen. | Offen: A-V0.12-00006 nicht erfüllt; die Zehn-Lauf-Mischserie zeigt 4,9 % mit überlappender Streuung und Qualitätsverschlechterungen; der Vorlagen-Serializer regressiert in fünf Läufen um 6,3 %. |

| Aktive Anforderung | Umsetzungsschritte | Erforderlicher Nachweis | Tatsächlicher Status |
|---|---|---|---|
| A-V0.12-00001 | U-V0.12-000010, U-V0.12-000011, U-V0.12-000015 | Reproduzierbare Baseline mit Rohdaten, Quell-/Buildstand und Streuung. | Teilweise erfüllt: fünf gültige Läufe und Quell-/Binärhashes dokumentiert; Compileridentität fehlt. |
| A-V0.12-00002 | U-V0.12-000010, U-V0.12-000012 | Relevante Szenarien, Folkeboot/analytische Grundkörper nach Bedarf; kein Yacht-Kreuzprodukt. | Teilweise erfüllt: Folkeboot-GUI mit `exakt_union`/C++ gemessen; kein separates natives End-to-End-Szenario. |
| A-V0.12-00003 | U-V0.12-000011 bis U-V0.12-000013 | Kandidatenentscheidung nach Engpass und End-to-End-Anteil; keine pauschale Rückschaltung. | Technisch erfüllt: Profil- und Wrapperbefunde dokumentiert; kein Mikrobenchmark als End-to-End-Erfolg gewertet. |
| A-V0.12-00004 | U-V0.12-000013, U-V0.12-000014 | Gezielte Tests, unabhängige Referenzen und erforderliche Parität; keine Vertragslockerung. | Für den Endstand erfüllt: keine Produktivschnittstelle geändert. Die Versuchskandidaten hatten vier gezielte Tests bestanden, wurden aber wegen der Aktualisierungsratenregression verworfen. |
| A-V0.12-00005 | U-V0.12-000013 bis U-V0.12-000015 | Keine Näherung ohne Freigabe, Fehlerbudget und Referenzvalidierung. | Erfüllt: keine Näherung eingeführt. |
| A-V0.12-00006 | U-V0.12-000012 bis U-V0.12-000015 | Mindestens 20 % End-to-End-Medianverbesserung oberhalb der Streuung, ohne relevante Pflichtszenario-Verschlechterung. | Nicht erfüllt: der Marker-only-Kandidat erreicht in fünf Läufen 10,2 %; die zehn kombinierten Läufe erreichen 4,9 % bei überlappender Run-Spannweite und Verschlechterungen; der SVG-Vorlagen-Serializer liegt in fünf Läufen 6,3 % hinter der Baseline. |

| Umsetzungsschritt | Tatsächlicher Stand |
|---|---|
| U-V0.12-000010 | Technisch geprüft mit Einschränkung: fünf gültige uninstrumentierte Folkeboot-GUI-Läufe; 10 s Warm-up, 45 s Messdauer, 640×480. Compileridentität fehlt; ein separates natives End-to-End-Szenario wurde nicht gemessen. |
| U-V0.12-000011 | Technisch geprüft: Callback-/CPU-Profile und Wrappermessungen ausgewertet. CPPI-0080 hatte 506 Aufrufe, aber nur rund 4,2 ms Eigenzeit; CPPI-0085 und CPPI-0091 waren im C++-Pfad schneller. Langsame Einzelwrapper ergaben keinen belegten End-to-End-Beitrag von mindestens 20 %. |
| U-V0.12-000012 | Teilweise erfüllt: Folkeboot-GUI, nativer Rechenpfad, Messgrenze und Metriken sind in den Belegen festgehalten. Die explizite Vorab-Festschreibung vor dem ersten Kandidatenlauf ist nicht nachweisbar. |
| U-V0.12-000013 | Zwei GUI-Taktungsversuche, der SVG-no-op und die bytegleiche SVG-Vorlagenserialisierung wurden verworfen. Der exakte Marker-Vorlagenkandidat bleibt als Teilfortschritt; seine fünf Läufe zeigen 10,2 % Verbesserung ohne gemessene relevante Verschlechterung. |
| U-V0.12-000014 | Vollständige Suite: 1.752 bestanden, 2 bekannte Ausgangsfehler, 1 übersprungen (170,69 s). Die Fehler sind der abweichende Hash von `konfigurationen/settings.json` im historischen Referenzmanifest sowie die bekannte Optimist-Kraftabweichung von 1,01024256e-9 bei `atol=1e-9`; kein Skip, keine Toleranzänderung. Zusätzlich 324 gezielte Profil-, Kraftdarstellungs-, Integrations- und Widgettests nach Rücknahme der SVG-Kandidaten bestanden (104,27 s). Während des Serializer-Versuchs bestanden 328 gezielte Tests einschließlich Bytegleichheitsprüfungen, der Kandidat wurde aber wegen der End-to-End-Regression verworfen. Frühere Nachweise: 384 Schnittstellen-/Anzeigeparitätstests (93,24 s), vier Versuchstests (2,43 s) und zwölf Marker-/Overlaytests (1,69 s). |
| U-V0.12-000015 | Mess-/Registerangaben und Kandidatenvergleich dokumentiert; zehn kombinierte Läufe und fünf Serializer-Läufe gültig ausgewertet. Kein CPPI-Vertrag geändert; A-V0.12-00006 und fehlender Compiler-/separater nativer End-to-End-Nachweis bleiben offen. |

Die detaillierten Rohdaten, Umgebungs- und Quell-/Buildidentität sowie die
Entscheidung zu den verworfenen Varianten stehen im
[Speed-Nachweis](../Messungen/Speed_V0.12_2026-10-21/speed_evidence_v0.12.json)
und im [Kandidatenvergleich](../Messungen/Speed_V0.12_2026-10-21/speed_candidate_assessment_v0.12.json).
Der separate CPPI-0091-Mikrobenchmark für sieben Folkeboot-OBJ-Meshes
([257 Punkte insgesamt](../Messungen/Speed_V0.12_2026-10-21/grafik_transformieren_kandidaten.json))
ergab einen C++-Speedup von 2,69, ist aber kein End-to-End-Nachweis.

**Zwischenstand:** Die Baseline, verworfenen Taktungsvarianten, der
Marker-only-Kandidat, zehn kombinierte Marker-/SVG-Läufe und fünf Läufe des
bytegleichen SVG-Vorlagen-Serializers sind dokumentiert. Der Marker-Kandidat
verbessert die primäre Metrik in fünf Läufen um 10,2 %, erreicht aber nicht
die geforderten 20 %. Der SVG-no-op-Kandidat wurde mangels belastbarer
Verbesserung und der Vorlagen-Serializer wegen einer 6,3-%-Regression
zurückgenommen.
A-V0.12-00006 bleibt **nicht erfüllt**; die vollständige Pytest-Suite wurde
nicht ausgeführt.
