# Umsetzungsprotokoll – Schnitt 0.8

**Datum:** 19.10.2026  
**Stand:** für Commit und Tag `0.8` vorbereitet  
**Normative Grundlage:** [Hydrodynamik-Spezifikation](./Spezifikatonen/Hydrodynamik.md)  
**Fortsetzung:** [Backlog offener Anforderungen](../../../Backlog/Hydrodynamik_offene_Anforderungen.md) und [Umsetzungsplan Hydrodynamik 2](./Umsetzungsplan/Hydrodynamik_2.md)

## Schnittentscheidung

Der zuV0.8-Arbeitsstand wird als abgeschlossener Entwicklungsschnitt
gesichert. Das bedeutet keine vollständige Abnahme der Hydrodynamik-Spec:
Alle aktiven Anforderungen bleiben in der Spec rückverfolgbar. Die eine
vollständig erfüllte Anforderung wird als abgeschlossen dokumentiert; alle
übrigen aktiven Anforderungen werden mit ihren dauerhaften IDs ins Backlog
übernommen. A-V0.8-00003 bleibt als zurückgezogener Punkt ausgeschlossen.
Die fachliche Weiterarbeit an Modellqualität und grafischen Änderungen
beginnt nach diesem Schnitt unter v0.9.

## Umgesetzter Stand

- Hydrodynamik-Kern mit benannten Kraft-/Momentenbeiträgen und generischer
  Geometrieauswertung integriert.
- Generische Volumenkörper werten die lokale Strömung je benetztem Dreieck
  aus und berücksichtigen die daraus entstehenden Kräfte und Momente.
- 6-DOF-Integration behandelt konfigurierte lineare und quadratische
  Dämpfung implizit; die Platten-Regression besteht dadurch auch die
  stationäre und 10-s-Dynamikprüfung.
- Stationärer Gleichgewichtssolver, dynamische Prüfung und strukturierte
  Fehlergründe sind vorhanden; die GUI gibt den Fehlergrund aus.
- Konfigurations-, Körperwechsel-, GUI-, Worker- und Solvertests wurden
  erweitert.
- Nicht abgeschlossene Anforderungen sind im
  [Hydrodynamik-Backlog](../../../Backlog/Hydrodynamik_offene_Anforderungen.md)
  einzeln mit Spec-ID und offenem Rest festgehalten.

## Abnahme- und Validierungsstand

- Vollständige Testsuite: **675 bestanden, 1 übersprungen**.
- Quelltext-Whitespace-Prüfung: erfolgreich. Git meldet für Markdown nur die
  im Repository verwendeten zwei End-Leerzeichen für harte Zeilenumbrüche
  sowie LF/CRLF-Hinweise.
- Der stationäre Yacht1-Solver-Lauf ist mit `0,315 s` dokumentiert und liegt
  unter dem Ziel von 5 s. Diese Messung stammt von vor der jüngsten
  Hydrodynamik-Hot-Path-Änderung.
- Stationär und dynamisch bestanden: `pyramide`, `rolle`, `platte`.
- Stationäres Gleichgewicht nicht erreicht: `kegel`, `quader`, `kugel`,
  `bleistift`, `unregelmaessig`. Toleranzen wurden nicht gelockert und
  Testkräfte nicht zur Vortäuschung einer Konvergenz angepasst.
- Yacht1-LWL: Mesh-Auswertung `3,789 m`, Spec-Richtwert `4,14 m`; Differenz
  ungeklärt.
- Unabhängige Yacht1-/Körperreferenzdaten fehlen.
- Hot-Path-, Echtzeit-/IPC-Überlast- und vollständige GUI-Abnahmen sind
  noch offen.

## Anforderungsstatus am Schnitt

| Status | Anzahl | IDs |
|---|---:|---|
| Abgeschlossen | 1 | A-V0.8-00020 |
| Teilweise umgesetzt, ins Backlog übernommen | 26 | A-V0.8-00001, A-V0.8-00002, A-V0.8-00004 bis A-V0.8-00019, A-V0.8-00021 bis A-V0.8-00028 |
| Gar nicht umgesetzt | 0 | – |
| Zurückgezogen, nicht aktiv | 1 | A-V0.8-00003 |

## Versions- und Repository-Aktionen

- Zieltag: `0.8` (annotierter Tag, ohne `v`).
- Commit erfolgt erst nach erneutem Lauf der vorgeschriebenen Tests.
- Danach werden `main` und Tag `0.8` nach `origin` gepusht.
- Der nächste Entwicklungsschnitt ist v0.9.
