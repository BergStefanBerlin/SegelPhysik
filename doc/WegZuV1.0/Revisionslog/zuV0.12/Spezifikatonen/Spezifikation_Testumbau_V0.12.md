# Spezifikation V0.12: Schlanke und nachweisbare Teststruktur

**Stand:** 21.10.2026  
**Status:** Umsetzung beauftragt am 21.10.2026; technischer Stand im Umsetzungsplan, fachliche Abnahme offen  
**Ausgangsbasis:** Testbestand aus V0.11; Umbau erst in V0.12  
**Maßgebliche Spezifikation für V0.12:** diese Datei

## 1. Ziel, Geltung und Quellen

Tests sichern fachliche Richtigkeit, Stabilität und nachvollziehbare
Änderungen. Performanceverbesserungen müssen mit vergleichbaren Messungen
nachgewiesen werden. Ziel ist weniger Zeitaufwand bei erhaltener
Fehlererkennung, nicht eine möglichst kleine Testanzahl.

Diese Spezifikation beschreibt den geplanten Umbau des aktuellen,
aus V0.11 übernommenen Testbestands in V0.12. Dokumente und historische
Nachweise unter zuV0.11 bleiben unverändert. Das Erstellen dieser
Spezifikation und der Testpflege-Instruction verändert noch keine Tests,
Produktivpfade, pytest-Konfiguration oder Abhängigkeiten.

Grundlagen:

- Nutzerabstimmung vom 21.10.2026: Folkeboot und ein bis zwei Grundkörper
  statt teurer Testreihen über alle Yachten; risikobasierte Testauswahl;
  Zeit und Qualität gemeinsam bewerten.
- [Teststruktur-Findings](Teststruktur_Findings.md) und
  [bisheriger Instruction-Entwurf](teststruktur.instructions.md):
  historische Diskussionsquellen, keine zusätzlichen verbindlichen
  Spezifikationen oder aktiven Testpflege-Instructions.
- [Projektweite Testpflege-Instruction](../../../../../.github/instructions/teststruktur.instructions.md),
  [Nummerierungsregel](../../../../../.github/instructions/nummerierung.instructions.md),
  [Releaseumsetzung](../../../../../.github/instructions/releaseumsetzung.instructions.md)
  und [Schnittstellenregister-Regel](../../../../../.github/instructions/schnittstellenregister.instructions.md).

Der
[historische Abschlussnachweis Teststruktur und bisherige Speed-Arbeiten](../Umsetzungsanleitungen/Abschlussnachweis_Teststruktur_und_Speed_V0.12.md)
dokumentiert Durchführung, U-Kennungen und Teststruktur-Befunde. Der
[aktuelle Umsetzungsplan V0.12](../Umsetzungsanleitungen/Umsetzungsplan_V0.12.md)
ist die maßgebliche Plan-Datei für verbleibende Arbeiten im Versionsschritt.
Der Nutzer hat die Teststruktur-Umsetzung am 21.10.2026 ausdrücklich
beauftragt; eine Git-Veröffentlichung ist nicht beauftragt.

## 2. Ausgangsbefund und Grenzen der bisherigen Bewertung

Bei der Sichtung am 21.10.2026 bestanden 92 Dateien mit Namen
`test_*.py` unter [tests](../../../../../tests).
Die vorhandene [conftest.py](../../../../../tests/conftest.py) isoliert
Anwendungseinstellungen; sie darf nicht durch einen Neubau verloren gehen.
[pyproject.toml](../../../../../pyproject.toml) enthält noch keine
pytest-Konfiguration. Unter [code/cpp/tests](../../../../../code/cpp/tests)
liegen zusätzlich `paritaet_batch.py`, `paritaet_frames.py`,
`paritaet_koerperkontext.py`, `vertrag_native.py` und eine eigene
`conftest.py`. Die vier Prüfdateien werden mit dem üblichen
`test_*.py`-Namensmuster nicht automatisch gesammelt.

Die bisherige erfolgreiche pytest-Sammlung belegt nur Sammelbarkeit, keine
bestandene Suite oder ausreichende Abdeckung. Vor Umsetzung ist der dann
tatsächliche V0.11-Ausgangsstand eindeutig zu sichern und neu zu messen.

Die alten Findings werden nicht ungeprüft übernommen:

- Das Fehlen einer gemeinsamen `conftest.py` ist überholt.
- Ähnliche Assertions sind nicht automatisch redundante Tests.
- Adapter- und native Kerntests prüfen unterschiedliche Ebenen.
- Ein negativer Legacy-Test kann einen noch gültigen Vertrag sichern.
- Weder eine hohe Schleifenzahl noch Modellbau allein belegt einen
  langsamen Test; die tatsächliche Laufzeit entscheidet.
- Layout-/Ressourcenprüfungen brauchen nicht zwingend einen AST.
- Das Folkeboot ist die gewählte Modellreferenz, aber nicht durch diese
  Festlegung bereits physikalisch vollständig validiert.

## 3. Aktive Anforderungen nach Kennung

Die folgenden Abschnitte konkretisieren die gemeinsam prüfbaren Verträge.
Tatsächlicher Status und Belege aller Anforderungen stehen in der
Rückverfolgbarkeitsmatrix des Umsetzungsplans; eine fachliche Gesamtfreigabe
liegt noch nicht vor.

| Kennung | Anforderung | Abnahmekriterium |
|---|---|---|
| A-V0.12-00001 | Versionsgrenze und Umfang einhalten | Umbau nur im Rahmen V0.12; keine Änderung historischer V0.11-Dokumente, keine beiläufige Produktiv- oder Modellkorrektur; Abschnitt 1. |
| A-V0.12-00002 | Ausgangsbestand und Testkosten erfassen | Ausgangsrevision, Befehle, Umgebungsdaten, gesammelte/ausgeführte Tests, Fehler/Skips und Laufzeiten einschließlich separater nativer Prüfungen liegen vor; Abschnitt 6. |
| A-V0.12-00003 | Kleine reguläre Referenzmatrix verwenden | Folkeboot, Quader und Kugel decken die begründeten Standardfälle ab; keine routinemäßige teure Yacht-Kreuzproduktmatrix; Abschnitt 4. |
| A-V0.12-00004 | Modellgrenzen und Ausnahmen ehrlich behandeln | Optimist ist kein allgemeiner Stabilitäts- oder Performance-Abnahmemaßstab; bestehende modellspezifische Verträge bleiben nachvollziehbar geprüft oder begründet ersetzt; Abschnitt 4. |
| A-V0.12-00005 | Änderungsbezogene Auswahl mit Sicherheitsnetz ermöglichen | Betroffene direkte und indirekte Verträge samt Grenzflächen werden geprüft; Auswahl und Eskalationsgrund sind dokumentiert, Unsicherheit führt zur Erweiterung; Abschnitt 5. |
| A-V0.12-00006 | Prüfprofile explizit und vollständig auswählbar machen | Auswahlprofile, Marker und Befehle sind dokumentiert; keine versteckte Standard-Abwahl; Gesamtprofil enthält auch die vier nativen Prüfdateien; Abschnitt 5. |
| A-V0.12-00007 | Tests thematisch auffindbar gliedern | Gemischte Dateien sind bewertet und bei Nutzen thematisch aufgeteilt; historische Kennungen und alte/neue Testorte sind zugeordnet, keine Umbenennung um ihrer selbst willen. |
| A-V0.12-00008 | Testhilfen ohne Isolationsverlust wiederverwenden | Nachgewiesene gemeinsame Hilfen sind konsolidiert; Einstellungen, Qt-Lebensdauer, temporäre Dateien, mutable Daten und native Referenzkontexte bleiben isoliert; Abschnitt 7. |
| A-V0.12-00009 | Redundanz nur mit Vertragserhalt abbauen | Für entfernte/zusammengeführte Fälle sind bisherige Assertions, Grenzfälle und tragende Ersatztests nachvollziehbar zugeordnet; Abschnitt 7. |
| A-V0.12-00010 | Genauigkeit und unabhängige Referenzen erhalten | Bestehende Toleranzen und bit-exakte Verträge sind nicht gelockert; analytische Referenzen bleiben vom geprüften Rechenpfad unabhängig; Abschnitt 7. |
| A-V0.12-00011 | Performanceänderungen reproduzierbar nachweisen | Vergleichbare Vorher-/Nachher-Messungen mit Korrektheitsprüfung, Rohdaten, Streuung und ausgewiesener Messgrenze liegen vor; Abschnitt 6. |
| A-V0.12-00012 | Zeitgewinn des Testumbaus belegen | Iterationsprofil und qualitätsgleiches Gesamtprofil sind vor/nach dem Umbau vermessen; Zeitgewinn über der beobachteten Streuung oder fehlender Nachweis wird offen ausgewiesen; Abschnitt 6. |
| A-V0.12-00013 | Fehler, Ausschlüsse und fehlende Voraussetzungen sichtbar halten | Kein stiller Backendwechsel, pauschales Skip/Xfail oder als erfolgreich dargestellter unvollständiger Lauf; Abschnitt 5. |
| A-V0.12-00014 | Nachweise und Abnahme vollständig zuordnen | Alle aktiven A-IDs erhalten im einen Plan U-Zuordnungen und tatsächliche Belege; verschobene Testverweise sind aktuell, V0.11-Historie bleibt lesbar; Abschnitt 8. |
| A-V0.12-00015 | Dauerhafte Testpflege verbindlich beschreiben | Eine aktive Instruction im projektüblichen Instruction-Verzeichnis enthält Auswahl-, Modell-, Struktur-, Genauigkeits- und Messregeln ohne automatische Migration des Altbestands. |

## 4. Repräsentative Fälle statt aller Yachten

| Referenz | Zweck | Grenze |
|---|---|---|
| Quader | Schnelle analytische Referenzen für Volumen, Masse, Trägheit, Auftrieb, Schnitt und definierte Bewegung; gezielte Mehrkörperfälle aus einfachen Körpern bei Bedarf. | Erwartungswerte analytisch herleiten; keine langen Simulationen für lokal prüfbare Formeln. |
| Kugel | Ergänzende Symmetrie-, Rotations- und gekrümmte Geometriefälle. | Diskretisierungsfehler von Rechenfehlern unterscheiden und bestehendes Fehlerbudget erhalten. |
| Folkeboot | Ein repräsentativer realer Modellaufbau für benötigte End-to-End-, Worker-, Dynamik- und Gesamtpfadmessungen. | Deterministische Konfiguration und definierte Anfangsbedingungen; kein Beweis für jedes Modell oder jede Wetterlage. |

Die Matrix ist ein kleiner Fallvorrat, kein verpflichtendes Kreuzprodukt
aller Referenzen mit allen Tests, Backends, Posen und Parametern.
Der einfachste fachlich ausreichende Fall hat Vorrang. Fachlich notwendige
synthetische Sonderfälle, etwa offene oder fehlerhafte Meshes, bleiben erlaubt.

Nach Nutzerbeobachtung ist der Optimist noch nicht ausreichend implementiert
und kentert häufig. Deshalb wird aus einem erwarteten stabilen Optimist-Lauf
keine allgemeine Abnahme abgeleitet. Das ist weder eine automatische
Fehlerursachenfeststellung noch die Erlaubnis, seine bestehenden Paket-,
Geometrie- oder Hydrodynamiktests pauschal zu löschen, zu überspringen oder
auf erwartetes Fehlschlagen zu setzen.

Modellspezifische Änderungen benötigen die betroffenen Modelltests, auch
außerhalb der Referenzmatrix. Ein zusätzlicher teurer Modellfall benötigt
einen benannten Vertrag, den die Referenzen nicht abdecken. Ein günstiger
Katalog-/Ladetest über mehrere Modelle ist bei Änderungen an gemeinsamen
Ladern oder Manifestverträgen zulässig, aber kein Pflichtlauf über alle
Modelle bei jeder Änderung. Vollständige Dynamik- und Benchmarksuiten
werden daraus nicht abgeleitet.

## 5. Risikobasierte Ausführung

| Anlass / Profil | Erforderlicher Umfang |
|---|---|
| Reine Dokumentation | Links, Kennungen und Konsistenz; keine Physiksuite ohne fachlichen Anlass. |
| Lokale Entwicklung / Iteration | Betroffene Unit- und Regressionstests, relevante Fehler-/Grenzfälle sowie direkte und indirekte Verbraucher. Vorhandene Auswahlmöglichkeiten nutzen. |
| Gemeinsame Verträge oder unklare Auswirkung | Zusätzlich betroffene Integration, Serialisierung, Cache-/Worker- und Backendgrenzen; bei nicht sicher abgrenzbarer Auswirkung Gesamtprofil. |
| Modelländerung | Betroffenes Modell und geänderte gemeinsame Verträge; nicht automatisch alle Yachten simulieren. |
| Performanceänderung | Betroffene Korrektheit/Parität plus gezielte Messung des tatsächlich geänderten Pfads; bei Gesamtpfadänderung Folkeboot-End-to-End-Fall. |
| Umbau der Testsammlung/Fixtures, Meilenstein, Revisionsabnahme | Vollständiges Gesamtprofil der neu geordneten Suite einschließlich relevanter GUI- und nativer Verträge; Nachweise auswerten. |
| Commit | Zusätzlich stets die vorgeschriebenen Tests der Release-Instruction; ein Teilprofil ersetzt diese nicht. |

Ein Gesamtprofil bedeutet vollständige Vertragsabdeckung der gepflegten Suite,
nicht die Simulation jeder Yacht. Korrektheitstests für Messwerkzeuge gehören
dazu; wiederholte teure Performancekampagnen nur bei einschlägigem Anlass.

Auswahlentscheidungen berücksichtigen gemeinsam benutzte Fixtures, Geometrie,
Frames, Einheiten, Zustandsübergänge und Schnittstellen. Ein geänderter
Dateiname allein ist keine sichere Wirkungsanalyse. Rein statische oder
automatische Abhängigkeitsauswahl darf fachliche Grenzflächen nicht ausblenden.
Neue Auswahlwerkzeuge sind kein Selbstzweck.

Marker wie `integration`, `gui`, `native`, `slow` und gegebenenfalls
`performance` werden bei Einführung registriert und klar beschrieben.
`slow` folgt Messungen, nicht einer willkürlichen Schleifengrenze.
Ein Marker wählt ohne explizites Profil keine Tests ab.
Die technische Umsetzung und erprobten Befehle sind im Plan und in der
[Testanleitung](../../../../../tests/README.md) dokumentiert.
Die separate native Sammlung muss explizit eingebunden oder mit
nachgewiesen gleichwertigem Sammelmuster erfasst werden; ihre eigenen
Referenz-Fixtures müssen dabei wirksam bleiben.

Jeder Bericht unterscheidet ausgeführte, abgewählte, übersprungene und
fehlgeschlagene Fälle. Bekannte Ausgangsfehler bleiben mit Ursache oder
ungeklärtem Status sichtbar. Fehlender nativer Build oder fehlende
GUI-Voraussetzungen ergeben keinen vollständigen Erfolgsnachweis.

## 6. Laufzeit- und Performancenachweise

Vor dem Umbau sind Gesamtzeit, Sammelzeit, Setup-Kosten und langsame
Einzelfälle zu erfassen. Vorhandene Werkzeuge und pytest-Laufzeitberichte
haben Vorrang vor neuen Abhängigkeiten. Zeitaufwand für Modellerzeugung,
Fixture-Setup und Prozessstart gehört zur Testkostenbewertung.

Für Produktivmessungen werden Referenz- und Kandidatenrevision, Modell-/
Eingabestand, Rechenpfad, Hardware, Python-/Native-Build, Thread-/Prozesszahl,
Zeitschritt, Schrittzahl, Warm-up, Wiederholungen und Messgrenze dokumentiert.
Es gelten gleiche Eingaben und gleiche Messbedingungen. Geänderte Cache-,
Kaltstart- oder Warmstartbedingungen sind gesondert auszuweisen.

Nach mindestens einem getrennten Warm-up werden mindestens fünf Messungen
je Variante durchgeführt, möglichst abwechselnd und ohne konkurrierende
Testlast. Median, Streuung (mindestens Minimum/Maximum) und Rohdaten werden
aufbewahrt. Faktor = Referenzmedian / Kandidatenmedian; ein Faktor über 1
bedeutet schneller. Korrektheit und bestehende Genauigkeitsverträge werden
für den gemessenen Pfad gesondert nachgewiesen. Profilierung und normale
Laufzeitmessung dürfen nicht unkenntlich vermischt werden.

Für Suitevergleiche genügen mindestens drei vollständige Läufe je Stand
unter gleichen Bedingungen; Cache-/Setupbedingungen sind gleichzuhalten.
Iterations- und Gesamtprofil werden getrennt verglichen. Auswahlverkleinerung
und Beschleunigung derselben Arbeit werden getrennt berichtet. Weniger
ausgeführte Tests allein belegen keine schnellere Implementierung.

Ein Zeitgewinn gilt hier erst als belastbar, wenn die Differenz der Mediane
größer als die größere der beiden beobachteten Spannweiten (Maximum minus
Minimum) ist. Andernfalls ist der Gewinn zunächst nicht nachgewiesen;
weitere Messungen oder kontrolliertere Bedingungen sind nötig. Diese
konservative Regel ersetzt keine statistische Sicherheitsgarantie.
Eine unbelegte Prozentvorgabe wird nicht erfunden.

Abnahmeziel des Testumbaus ist ein nach dieser Regel messbar kürzerer
typischer Iterationslauf bei erhaltener Vertragsabdeckung und ohne
nachgewiesene Verlangsamung des qualitätsgleichen Gesamtprofils.
Wird dieses Ziel nicht erreicht, bleibt A-V0.12-00012 offen.
Eine fachlich notwendige Erweiterung der Suite wird als Umfangsänderung
separat ausgewiesen, nicht aus dem Vergleich versteckt entfernt.

Instabile Wandzeitgrenzen werden nicht in gewöhnliche Korrektheitstests
eingebaut. Performancegrenzen für konkrete Produktivpfade werden vor ihrer
Bewertung mit Arbeitslast und Messbedingungen festgelegt; historische
versionsspezifische Grenzwerte gelten nicht automatisch weiter.
Verschachtelte Zeiten werden nicht addiert oder als isolierte
Interfacegewinne ausgegeben. Interfacebelege folgen dem zentralen Register.

## 7. Struktur, Wiederverwendung und Genauigkeit

Dateien werden nach Verhalten/Fachthema benannt. Integrationsthemen dürfen
bewusst mehrere Module verbinden. Historische Sammeldateien werden nur bei
belegtem Nutzen aufgeteilt; keine mechanische Neuordnung der gesamten Suite.
Import-Schichtregeln werden per AST, Ressourcen-/Layoutverträge mit
passenden Pfad- und Laufzeitprüfungen getestet.

Gemeinsame Fixtures werden nur für tatsächlich wiederverwendete Aufbauten
extrahiert. Teure Setups werden nur dann geteilt, wenn Mutationen und
Testreihenfolge die Ergebnisse nicht beeinflussen. QApplication muss
zuverlässig gehalten, Widgets und Worker müssen gezielt beendet werden.
Der bestehende Schutz persönlicher Einstellungen bleibt erhalten.
Erzeugung teurer Modelle während der Testsammlung ist zu vermeiden.

Vorhandene Formfabriken sind zu bevorzugen, wenn sie nur Testeingaben
liefern. Wenn die Fabrik selbst oder ein von ihr abhängiger Pfad geprüft
wird, sind unabhängige analytische Eingaben/Erwartungswerte nötig.
Spezielle Netze für Schnitt-, Orientierungs- oder Fehlerfälle bleiben
zulässig. Die Produktionsfunktion darf nicht ihr eigener Wahrheitsmaßstab sein.

Parametrisierung ersetzt gleichförmigen Testcode, nicht automatisch
Rechenaufwand; unnötige Kombinationen werden vermieden.
Das Entfernen ähnlicher Tests benötigt einen Vergleich von Vertrag,
Assertions und Grenzfällen. Adaptertests ersetzen keine nativen
Kerntests und umgekehrt. Legacy-Tests oder Module werden nicht allein
wegen ihres Namens entfernt.

Bestehende numerische Verträge bleiben bestehen, insbesondere
Python/C++-Vergleiche mit `rel=0, abs=1e-12`, soweit für den jeweiligen
Vertrag vorgegeben, und bit-exakte Batch-Sequenzen. Diese Werte sind
keine pauschale Toleranz für alle physikalischen Approximationen.
Neue Toleranzen benötigen Herleitung, Einheit, Fehlerbudget oder belegte
Referenz; Laufzeitgewinn rechtfertigt keine Lockerung.

## 8. Abnahme und Rückverfolgbarkeit

Für jeden entfernten, verschobenen oder zusammengeführten Test wird der
alte Ort dem neuen Ort beziehungsweise dem belegten Ersatzvertrag
zugeordnet. IDs bleiben erhalten. Aktuelle Register-/Nachweisverweise werden
im selben Arbeitsschritt aktualisiert. Historische V0.11-Dokumente werden
nicht umgeschrieben; ihre alten Verweise bleiben über die Zuordnung lesbar.

Die Abnahme benötigt:

- Einen gemeinsamen Plan mit allen A-/U-Zuordnungen und tatsächlichem Status.
- Ausgangs- und Zielsammlung einschließlich der nativen Prüfungen sowie
  eine Begründung jeder Änderung an der Fallmenge.
- Erfolgreiche einschlägige Korrektheits-, Genauigkeits- und
  Integrationstests; Ausgangsfehler und fehlende Nachweise gesondert.
- Vergleichbare Messbelege für Produktivoptimierungen und Testkosten,
  soweit die jeweilige Anforderung sie verlangt.
- Geprüfte Profilbefehle sowie eine an einem konkreten Änderungsszenario
  nachvollziehbare gezielte Testauswahl mit begründeter Eskalation.

Der Umsetzungsplan enthält den tatsächlichen Umbau-, Test- und Messstand
sowie die Maschinenbelege. Ein kürzerer Vergleichslauf ist belegt;
ein belastbarer Gewinn im kurzen Iterationsszenario fehlt. Zwei bereits
im Ausgangsstand vorhandene Testfehler verhindern eine uneingeschränkte
Gesamtfreigabe. Umsetzung und fachliche Abnahme bleiben getrennt.

## Nicht umsetzen

Noch keine aktiven Anforderungen zurückgezogen. Aus den Diskussionsquellen
werden folgende Vorschläge bewusst nicht als Anforderungen übernommen:

- Routinemäßige teure Simulationen und Benchmarks über alle Yachten:
  unverhältnismäßige Kosten ohne benannten zusätzlichen Vertrag.
- Optimist als allgemeiner Stabilitätsmaßstab: nach Nutzerbeobachtung
  derzeit ungeeigneter Modellstand.
- Automatisches Löschen vermeintlicher Duplikate oder Legacy-Tests:
  Vertragserhalt ist zuerst nachzuweisen.
- Versteckte schnelle pytest-Standardauswahl: würde unvollständige Läufe
  wie Gesamtprüfungen erscheinen lassen.
- Pauschale Einführung von Parallelisierung oder Timeout-Abhängigkeiten:
  nur bei gemessenem Bedarf und nach Prüfung von Isolation/Messverzerrung.
