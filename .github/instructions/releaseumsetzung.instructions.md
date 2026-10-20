---
description: "Use when preparing or implementing any project version or release: create or update its single specification and single implementation plan, organize requirements, milestones, evidence and acceptance. Arbeitsanweisung fuer die Releaseumsetzung aller Versionsschritte."
---
# Arbeitsanweisung Releaseumsetzung

## Zweck und Geltungsbereich

Diese Instruction regelt die fachliche Vorbereitung und Umsetzung eines
Versionsschritts im Revisionslog. „Releaseumsetzung“
meint hier die Arbeit an Spezifikation, Umsetzungsplan, Code und Nachweisen,
nicht das Erstellen eines GitHub-Releases.

Sie gilt ab Inkrafttreten für den aktuell bearbeiteten und alle künftigen
Versionsschritte. Abgeschlossene historische Versionsschritte werden
dadurch nicht nachträglich geändert oder umstrukturiert.

## Verbindliche Dokumentstruktur

- Pro Versionsschritt gibt es genau **eine maßgebliche Spezifikationsdatei**
  und genau **eine maßgebliche Datei für den Umsetzungsplan**.
- Alle Anforderungen und fachlichen Festlegungen des jeweiligen
  Versionsschritts werden in einer gemeinsamen Spezifikation geführt.
  Alle Umsetzungsschritte,
  Abhängigkeiten, Meilensteine und Umsetzungsstände stehen in einem
  gemeinsamen Umsetzungsplan.
- Themen, Komponenten oder Arbeitspakete sind als Abschnitte, Tabellen und
  Meilensteine in diesen beiden Dateien zu gliedern. Keine zusätzlichen
  Teil-, Neben- oder Ersatzspezifikationen und keine parallelen
  Umsetzungspläne für denselben Versionsschritt anlegen.
- Vor dem Anlegen oder Ändern prüfen, welche Dateien im Versionsordner
  bereits existieren. Eindeutige Hauptdateien nicht stillschweigend ersetzen,
  aufteilen oder umbenennen. Bei unklarer Abgrenzung oder konkurrierenden
  Kandidaten zuerst den Nutzer fragen.
- Unterstützende Nachweise wie Testergebnisse, Messdaten oder große
  maschinenlesbare Inventare dürfen bei Bedarf separat abgelegt werden.
  Sie sind keine zusätzlichen Spezifikationen oder Umsetzungspläne; die
  verbindlichen Anforderungen und Umsetzungsschritte bleiben in den beiden
  Hauptdateien und verlinken auf ihre Belege.
- Beispieldokumente sind nicht automatisch freigegebene Anforderungen oder
  verbindliche Vorlagen. Maßgeblich für den fachlichen Umfang ist
  ausschließlich die Spezifikation des jeweiligen Versionsschritts; für
  die Umsetzungsschritte ist es der zugehörige Umsetzungsplan.
  Unterstützende Nachweise belegen Ergebnisse, enthalten aber keine
  eigenständigen zusätzlichen Anforderungen oder parallelen Pläne.
  Übergreifende Projektregeln und die referenzierten Instructions gelten
  weiterhin.

## Anforderungen und Nachverfolgbarkeit

- Kennungen, Vergabe, Archivierung, Abhängigkeiten und Rückverfolgbarkeit
  richten sich nach der
  [Nummerierungs-Instruction](nummerierung.instructions.md). Sie ist die
  vollständige projektweite Regelung; Nummern nicht neu erfinden,
  wiederverwenden oder eigenständig umnummerieren.
- Jede aktive Anforderung steht in der einen Spezifikation und erhält ein
  prüfbares Ergebnis oder Abnahmekriterium. Jeder Umsetzungsschritt steht
  im einen Plan und verweist auf die zugehörigen Anforderungskennungen.
- Der Plan weist Abhängigkeiten und eine umsetzbare Reihenfolge aus.
  Meilensteine erhalten überprüfbare Eintritts- und Abnahmekriterien.
  Am Ende müssen alle aktiven Anforderungen Umsetzungsschritten und
  tatsächlichen Nachweisen zugeordnet sein.
- Zurückgezogene oder verworfene Anforderungen nicht stillschweigend
  löschen: nach der Nummerierungs-Instruction unter ihrer ursprünglichen
  Kennung archivieren. Übergänge ins Backlog während laufender Umsetzung
  nur mit Nutzerzustimmung.
- Technische Abweichungen, fehlende Nachweise und offene Punkte ausdrücklich
  dokumentieren. Umsetzung, Test, Integration und fachliche Abnahme nicht
  gleichsetzen; Status nur mit passenden Belegen ändern.

## Bisherige Arbeitsweise und Referenzen

- Für Kennungen und die bisherige Arbeitsweise mit Spezifikation,
  Umsetzungsschritten, Abhängigkeiten, Meilensteinen und
  Rückverfolgbarkeit gilt die
  [Nummerierungs-Instruction](nummerierung.instructions.md).
- Als historisches Beispiel für einen detaillierten Umsetzungsplan kann die
  [Umsetzungsanleitung der C++-Migration V0.10](../../doc/WegZuV1.0/Revisionslog/zuV0.10/Umsetzungsplan/Umsetzungsanleitung_CPP_Migration_V0.10.md)
  herangezogen werden. Die zugehörige
  [V0.10-Spezifikation](../../doc/WegZuV1.0/Revisionslog/zuV0.10/Spezifikationen/Spezifikation_CPP_Migration_V0.10.md)
  zeigt die damalige Trennung zwischen fachlicher Anforderung und
  Umsetzungsschritten.
- Dokumente früherer Versionsschritte sind historische Beispiele, keine
  zusätzliche Spezifikation oder Planungsdatei für den aktuellen
  Versionsschritt. Frühere versionsspezifische Freigaben, Ausnahmen,
  Messgrenzen oder offene Punkte gelten nicht automatisch für spätere
  Versionsschritte;
  ihre Übernahme erfordert einen aktuellen fachlichen Grund und, wo nötig,
  eine ausdrückliche Nutzerentscheidung.
- Bei Änderungen an Python/C++-Schnittstellen zusätzlich die
  [Schnittstellenregister-Instruction](schnittstellenregister.instructions.md)
  beachten und das Register mit belegtem Stand aktualisieren.

## Umsetzung und Abschluss

- In der Reihenfolge des freigegebenen Plans arbeiten. Den Plan fortlaufend
  mit tatsächlichem Status, Testergebnissen, Belegen und offenen Punkten
  aktualisieren; keine geplanten oder teilweise erledigten Arbeiten als
  abgeschlossen darstellen.
- Vor einer Erweiterung des Umfangs, Änderung fachlicher Verträge oder
  Änderung geltender Abnahmekriterien die nötige Nutzerentscheidung
  einholen.
- Zum Abschluss die aktive Anforderungsliste gegen Plan, Tests und Belege
  abgleichen. Fehlende Nachweise, bekannte Abweichungen und nicht erledigte
  Punkte sichtbar lassen; keine Vollständigkeit ohne Beleg behaupten.
- Git-Aktionen wie Commit, Push, Tag und Veröffentlichung folgen
  ausschließlich der
  [Release-Instruction](release.instructions.md) und benötigen den dort
  festgelegten ausdrücklichen Auftrag. Diese Arbeitsanweisung autorisiert
  keine Git-Veröffentlichung.
