# Backlog: Restarbeiten nach dem begrenzten Abschluss V0.10

**Stand:** 20.10.2026  
**Status:** Auf ausdrücklichen Nutzerauftrag aus dem V0.10-Abschluss übernommen.
Keine automatische Zuordnung zu einer Folgeversion.

**Anforderungsquelle:**
[Spezifikation V0.10](../WegZuV1.0/Revisionslog/zuV0.10/Spezifikationen/Spezifikation_CPP_Migration_V0.10.md)  
**Nachweise und Abschlussentscheidung:**
[Abschlussbilanz V0.10](../WegZuV1.0/Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md)  
**Technische Einzelschnittstellen:**
[CPPI-Register](../Dokumentation/Schnittstellenregister_CPP.md)

V0.10 ist als begrenzter Versionsstand abgeschlossen, nicht als vollständig
erfüllter ursprünglicher C++-Migrationsplan. Die Tabelle führt je
ursprünglicher Anforderungsnummer ausschließlich die verbleibende Arbeit.
Die Anforderungen bleiben unverändert in ihrer Spezifikation; hier werden
keine neuen Anforderungen oder Ideen definiert und keine A-IDs umgewidmet.
Zusammenhängende Restarbeiten dürfen gemeinsam umgesetzt werden; die
Zuordnung zu allen betroffenen A-IDs bleibt dabei erhalten.

Die **Optimist-Batchabweichung ist als Abschlussausnahme akzeptiert** und
kein offener V0.10-Abnahmeblocker mehr. Historische Fehlerwerte bleiben in
der Abschlussbilanz erhalten. Andere numerische Grenzen, insbesondere
Folkeboot-Worker und Replay, sind damit nicht streng abgenommen.

Die Restspalte nennt noch fehlende Nachweise ebenso wie fehlende
Implementierungen. Ein fehlender Nachweis ist nicht automatisch ein
nachgewiesener Codefehler. Ein offener Teilumfang bedeutet nicht, dass
die bereits produktiven C++-Kerne der betreffenden Anforderung fehlen.

<!-- BEGIN REQUIREMENT REMAINDERS -->
| Anforderung | Restarbeit |
|---|---|
| **A-V0.10-00001** Vollständigkeit zeitkritischer Pfade | Vollständige native Einzelentscheidungen und verbleibende Hotspots |
| **A-V0.10-00002** Funktion und Numerik | Folkeboot und weitere strenge Parität nur vorläufig, siehe Abschnitt 4 |
| **A-V0.10-00003** Grobkörnige Schnittstelle und Datenbesitz | Vollständige Datenbesitz-/Lifecyclematrix außerhalb geprüfter Pfade |
| **A-V0.10-00004** Build und Referenzbetrieb | Neuer sauberer Abschlussbuild und erneute Installation |
| **A-V0.10-00005** Fehler und Nebenläufigkeit | Vollständige Last-/Wechsel-/Abbruch-Gesamtmatrix |
| **A-V0.10-00006** Quaternionen und 6DOF | Übrige Einzel- und Langzeitnumerik nicht vollständig abgenommen |
| **A-V0.10-00007** Kraft-/Momentenaggregation | Restliche Einzelbeitrags-/Fehlerparität |
| **A-V0.10-00008** Zusammengesetztes Kraftmodell | Vollständige fachliche Varianten-/Einzelmatrix |
| **A-V0.10-00009** Benetzung und Flächen | Vollständige Benetzungs-/Randfallmatrix |
| **A-V0.10-00010** Hydrodynamische Rollenkräfte | Alle Rollen-/Parameter-/Fehlerkombinationen vollständig abnehmen |
| **A-V0.10-00011** Hydrovorbereitung und Rudernäherung | Vorbereitungshilfen und Testnäherung vollständig abnehmen |
| **A-V0.10-00012** Hydrostatik und Auftrieb | Weitere Varianten und Einzelabnahmen |
| **A-V0.10-00013** Vorbereiteter Union-Ebenenschnitt | Vollständige Rand-/Übergangs-/End-to-End-Nachweise |
| **A-V0.10-00014** Union-/Bibliotheksübergänge | Vollständige Datenübergangs-/Variantenabnahme |
| **A-V0.10-00015** Wasserschnitt und Deckel | Vollständige Schnitt-/Kontur-/Deckel-Einzelmatrix |
| **A-V0.10-00016** Wasserlinienkennwerte | Vollständige Einzelparität und Randfälle |
| **A-V0.10-00017** Robuster statischer Solver | Schwierige Sonderlösungen, Nichtkonvergenz und Diagnosen |
| **A-V0.10-00018** Weiterer statischer Solver | Vollständige Sonderfall-/Abbruch-/Diagnosematrix |
| **A-V0.10-00019** Stationärer Solver und Nachlauf | Sämtliche stationären Sonderfalldiagnosen |
| **A-V0.10-00020** Körper, Snapshots und Gelenke | Einmalige Vorbereitung, Invalidierung und vollständige Einzelabnahme |
| **A-V0.10-00021** Meshvalidierung und Massen | Allgemeine Eingabe-/Topologievalidierung |
| **A-V0.10-00022** Weitere Modellvorbereitung | Formerkennung, Modellvermessung, Konflikt-/Fehler-/Schreibtransaktionen |
| **A-V0.10-00023** Physikbatch und Transport | Vollständige Live-/Transport-/Lifecycleabnahme; übrige Numerik siehe Abschnitt 4 |
| **A-V0.10-00024** Anzeigeinterpolation und Pose | Übrige GUI-Aufbereitung und vollständige Live-/Optikmatrix |
| **A-V0.10-00025** Körperdarstellung und Farben | Übrige schwere Numerik prüfen, volle Layer-/Optikmatrix |
| **A-V0.10-00026** Kräfte, Bögen und Achsen | Übrige Overlay-/Actor-Numerik sowie Live-/Optikabnahme |
| **A-V0.10-00027** Wasser und Spuren | PyVista-Isoflächenübergänge und volle Live-/Optikmatrix; ausgenommene Altpfade bleiben archiviert |
| **A-V0.10-00028** Navigation, Instrumente, Kamera | Vollständige Instrument-/Kamera-/Optik-/Einzelmatrix |
| **A-V0.10-00029** Weitere Bewegungspfade | Vollständige Pfadabnahme; ausgenommene alte Körperhöhenhilfe bleibt archiviert |
| **A-V0.10-00030** Optionale Voxel-/GPU-Pfade | Genauigkeits-/Transfer-/Gerätematrix und GPU-Kernelübertragung offen |
| **A-V0.10-00031** Parität pro Block | Nicht sämtliche native Einzel-/Rand-/Fehlerfälle nachgewiesen |
| **A-V0.10-00032** Produktivübernahme und Gesamtvergleich | Wiederholter Langzeit-/Speicher-/Live-Gesamtvergleich zur Referenz |
| **A-V0.10-00033** Vollständiger Abschluss | Ursprüngliche vollständige Migration und native 298-Einzelmatrix noch offen |
| **A-V0.10-00034** Performance jeder Übertragung | Fehlende Einzel-/Elternblocknachweise und End-to-End-Nutzen vervollständigen |
<!-- END REQUIREMENT REMAINDERS -->

## Weiterbearbeitung

Vor Umsetzung den konkreten Rest gegen aktuellen Code und vorhandene
Prüfungen abgleichen. Originale Toleranzen, freigegebene Ausnahmen und
vorläufige Grenzen getrennt ausweisen. Erledigung nur mit Test-/Messbeleg
dokumentieren und mit Abschlussmatrix, CPPI-Register und gegebenenfalls
Umsetzungslog synchron halten. Keine neuen Einzel-Performancefaktoren aus
Elternblockzeiten ableiten; die 118 CPPI-Kennungen bleiben dauerhaft erhalten.
