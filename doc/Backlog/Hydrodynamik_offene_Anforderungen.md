# Backlog: offene Hydrodynamik-Anforderungen nach Schnitt 0.8

**Stand:** 19.10.2026  
**Ausgangsbasis:** [Hydrodynamik-Spezifikation](../WegZuV1.0/Revisionslog/zuV0.8/Spezifikatonen/Hydrodynamik.md)  
**Umsetzungsnachweis:** [Umsetzungsprotokoll 0.8](../WegZuV1.0/Revisionslog/zuV0.8/Umsetzungsprotokoll.md)

Dieses Backlog übernimmt alle aktiven Spezifikationsanforderungen, die zum
Schnitt 0.8 nicht vollständig abgenommen sind. Die bestehenden Kennungen
bleiben erhalten. Die Anforderungen sind nach Bereichen gruppiert; die
Spezifikation bleibt die normative Quelle. Eine Aufnahme hier gilt nicht
als Erledigung und lockert keine Abnahmekriterien.

**Status zum Schnitt:** 1 Anforderung abgeschlossen, 26 teilweise umgesetzt,
0 vollständig ohne Umsetzung. Alle 26 teilweise umgesetzten Anforderungen
bleiben offen, bis ihre vollständigen Abnahmen nachgewiesen sind.

## Geltungsbereich und Hydrostatik

| ID | Anforderung | Offener Rest |
|---|---|---|
| A-V0.8-00001 | Verdrängungsfahrt als erster Gültigkeitsbereich | Yacht1-LWL-Abweichung zwischen Meshwert `3,789 m` und Spec-Richtwert `4,14 m` klären; unabhängige Yacht1-Widerstandsreferenz beschaffen; Gültigkeitsgrenzen belegen. |
| A-V0.8-00002 | Vertikale Hydrostatik unverändert erhalten | Vollständige Regression über alle betroffenen Solver-, Dynamik- und GUI-Pfade dokumentieren. |

## Dynamik, Modellgrenzen und Validierung

| ID | Anforderung | Offener Rest |
|---|---|---|
| A-V0.8-00004 | Lokale Relativströmung an jedem Kraftangriffspunkt | Lokale Strömung, Körperrotation und Frames an allen Bauteilen und Angriffspunkten validieren. |
| A-V0.8-00005 | Dissipativer Widerstand bei Vorwärts- und Rückwärtsfahrt | Alle spezifizierten Widerstandsanteile und beide Fahrtrichtungen testen; Modell gegen unabhängige Referenzen validieren. |
| A-V0.8-00006 | Seitlicher Rumpfwiderstand | Kraftvorzeichen, Energiekonsistenz und Referenzverhalten vollständig nachweisen. |
| A-V0.8-00007 | Kielwirkung bei Abdrift | Nullanströmung sowie positive, negative und gespiegelte Abdrift samt Kraftvorzeichen vollständig prüfen. |
| A-V0.8-00008 | Ruderwirkung und Gierdämpfung | Ruderdrehachse, Hebelarm, abgesicherter Winkelbereich sowie Kraft- und Momentenvorzeichen validieren. |
| A-V0.8-00009 | Begrenzte und stetige Modellbereiche | Stetigkeit, Endlichkeit und sichtbare Behandlung aller Modellgrenzen einschließlich außerhalb des Verdrängerbereichs abnehmen. |
| A-V0.8-00010 | Energetisch konsistente Kraftanteile | Leistung sämtlicher Widerstandsbeiträge und Trennung von Widerstands- und Auftriebsanteilen prüfen. |
| A-V0.8-00011 | Geometriebezug und Modellannahmen offenlegen | Quellen, Herleitungen, Einheiten, Unsicherheiten und Gültigkeitsbereiche der Koeffizienten belegen; unabhängige Referenzvergleiche ergänzen. |
| A-V0.8-00012 | Lageabhängige Benetzung berücksichtigen | Konsistenz der Benetzung zwischen Solver, Dynamik und GUI nachweisen und Hot-Path-Auswertung messen. |
| A-V0.8-00013 | Bauteilbeiträge korrekt aggregieren | Einzel-Wrenches, Hebelarmmomente, Framewechsel, Gesamtsumme und genau einmalige Integratoreingabe vollständig abnehmen. |
| A-V0.8-00014 | Nicht konfigurierte Körper unverändert lassen | Regression aller relevanten nicht konfigurierten Körper und ihrer bisherigen Hydrostatik-/Kraftmodellpfade abschließen. |
| A-V0.8-00015 | Echtzeitfähige Auswertung | Hydrodynamik-Hot-Path nach der Dreiecksauswertung neu messen; Überlast-, Rückstands- und Echtzeitsemantik vollständig prüfen. |
| A-V0.8-00018 | Gesamtverhalten reproduzierbar testen | Vereinbarte Betriebsfälle mit vorab festgelegten Akzeptanzbereichen und unabhängigen Referenzdaten absichern. |
| A-V0.8-00021 | Körperbezogene Gleichgewichtsreferenz im Verdrängerbereich | Yacht1- und generische Profile unabhängig validieren; die nicht konvergierenden generischen Fälle ohne Toleranzlockerung beheben. |

## Statik und Gleichgewicht

| ID | Anforderung | Offener Rest |
|---|---|---|
| A-V0.8-00019 | Stationären hydrodynamischen Gleichgewichtspunkt direkt lösen | Fünf generische Standardprofile erreichen mit den aktuellen Konfigurationen kein stationäres Gleichgewicht. Solverfortschritt, Ursachenanalyse und stabile Referenzfälle vollständig abnehmen. |
| A-V0.8-00027 | Konvergenz und dynamische Gleichgewichtsprüfung quantifizieren | 1-%-Bilanz und unabhängige 10-s-Prüfung für die erforderlichen Referenzfälle nachweisen; Fehlfälle und GUI-Ergebnisdarstellung vollständig abnehmen. |

## GUI und Einstellungen

| ID | Anforderung | Offener Rest |
|---|---|---|
| A-V0.8-00016 | Hydrodynamische Beiträge aus den berechneten Kräften anzeigen | Für alle Beitragstypen nachweisen, dass GUI-Vektoren exakt aus den in die Dynamik gehenden Kräften stammen. |
| A-V0.8-00022 | Kraft- und Momentenpfeile an physikalisch begründeten Orten anzeigen | Angriffspunkte, Wirkungslinie, freies Restmoment, Summenmoment und Nullkraftverhalten vollständig visual prüfen. |
| A-V0.8-00023 | Detailkraftanzeigen unabhängig schalten | Drei unabhängige Toggles, gespeicherte Defaults und unveränderte Physik/Simulation durch Tests nachweisen. |
| A-V0.8-00024 | Ergebnis und Konvergenz des stationären Solvers anzeigen | Erfolgs- und Fehlerszenarien mit Teilstufen, letztem gültigem Zustand, Resten und Laufzeit vollständig abnehmen. |
| A-V0.8-00026 | Körperbezogene Hydrodynamik-Defaults beim Körperwechsel laden | Profile, Eingaberesets und Verhalten für alle unterstützten Körper vollständig durch die GUI-Abnahmematrix prüfen. |
| A-V0.8-00028 | Ruderausschlag als eigenständige Körpereinstellung führen | Default, Bereich, Körperwechsel und sichtbare Warnung außerhalb des physikalisch abgesicherten Bereichs abnehmen. |

## Konfiguration und Testbarkeit

| ID | Anforderung | Offener Rest |
|---|---|---|
| A-V0.8-00017 | Physikparameter explizit validieren | Vollständige Negativtests und kontextreiche Fehlermeldungen für alle Parameter, Einheiten und Grenzen abnehmen. |
| A-V0.8-00025 | APIs für automatisierte Prüfung anpassen, ohne Produktfunktionen zu verändern | Nachweisen, dass Steuer- und Testzugänge Produktverhalten, Defaults und Nutzerabläufe nicht verändern. |

## Abgeschlossen

| ID | Anforderung | Nachweis |
|---|---|---|
| A-V0.8-00020 | Laufzeitziel für den stationären Solver | Dokumentierter Yacht1-Referenzlauf: `0,315 s` bei Zielwert `≤ 5 s`. Die Messung ist vor der jüngsten Hot-Path-Änderung entstanden; bei erneutem Leistungsnachweis ist sie zu wiederholen. |

## Aus dem Backlog ausgeschlossen

**A-V0.8-00003** ist zurückgezogen und keine aktive Anforderung. Sie wird
nicht umgesetzt und nicht als offene Arbeit geführt.
