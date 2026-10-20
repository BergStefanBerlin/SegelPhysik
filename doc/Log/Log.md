# Umgesetzte Anforderungen

Dieses projektweite Register protokolliert Anforderungen nach erfolgreicher
Umsetzung und Abnahme. Die Spezifikation bleibt die fachliche Quelle; dieses
Log dokumentiert den Abschluss. IDs werden nicht wiederverwendet.

| Anforderungs-ID | Version | Kurzbeschreibung |
|---|---|---|
| A-V0.9-00001 | zuV0.9 | Automatische Modellpaketerkennung mit Manifestvalidierung, Legacy-/Override-Parität und integrierten Regressionen. |
| A-V0.9-00002 | zuV0.9 | Geometriefreie starre Seglerpunktmasse, dreiachsiger Baumeditor, atomare modellbezogene Persistenz und korrekte Massen-/Schwerpunkt-/Trägheitsaggregation. |
| A-V0.9-00003 | zuV0.9 | Komponentenprofil, Lifecycle- und Live-Messung mit Rohdaten, unabhängiger 300-s-Wiederholung sowie explizitem Qt-Swapproxy und nicht zuordenbarem Kommunikationsrest. |
| A-V0.9-00008 | zuV0.9 | NPU-Machbarkeitsprüfung abgeschlossen: Hardware/Treiber vorhanden, kein nachgewiesener geeigneter Projektlaufzeit-/Kernelpfad; keine Produktivintegration. |
| A-V0.9-00009 | zuV0.9 | Freigegebene Genauigkeitsgrenzen unverändert als harte Gates, eingefrorene exakte Referenzen und sichtbare Modell-/Verfahrensgrenzen; keine neue Physiknäherung freigegeben. |

Nachweise und offene Punkte:
[Prüfprotokoll zuV0.9](../WegZuV1.0/Revisionslog/zuV0.9/Umsetzungsplan/Abnahme_v0.9.md).
A-V0.9-00004 ist technisch umgesetzt und zweimal softwareseitig gemessen,
aber wegen der ausdrücklich offenen pädagogischen Nutzerabnahme noch
nicht als vollständig abgenommen eingetragen. A-V0.9-00005 bis
A-V0.9-00007 sind als zusätzliche Rechenkern-/Union-/Cachebeschleunigungen
nicht implementiert; negative Kandidatenentscheidungen stehen im Plan.

## V0.10: begrenzter Versionsabschluss am 20.10.2026

Der Nutzer hat den begrenzten Abschluss des produktiven V0.10-Stands und
die Dokumentation der Restarbeiten im Backlog ausdrücklich freigegeben.
Aktuelle Regression: 1172 bestanden, ein Windows-Symlink-Skip; C++-Replay
vorläufig bestanden. Die strenge Optimist-Batchabweichung ist als
Abschlussausnahme akzeptiert. Die Performancebilanz umfasst 165 Messfälle;
das zentrale Register enthält 118 einzelne CPPI-Kennungen mit
Python-/V0.10-Performancezuordnung oder ausdrücklich fehlender Einzelmessung.

Dies ist ein Versionsschnitt, keine vollständige Abnahme der 34
A-V0.10-Anforderungen. Deshalb werden sie nicht pauschal in die Tabelle
vollständig umgesetzter Anforderungen oben aufgenommen.

- [Abschlussbilanz und Anforderungsmatrix](../WegZuV1.0/Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md)
- [Restarbeiten nach ursprünglicher A-Kennung](../Backlog/Restarbeiten_V0.10.md)
- [CPPI-Register mit Performance](../WegZuV1.0/Revisionsinformation/Schnittstellenregister_CPP.md)

Die ursprünglichen Anforderungen bleiben die fachliche Quelle; die
Restarbeiten sind keiner Folgeversion automatisch zugewiesen.
Kein Commit, Push, Tag oder Release im Rahmen dieses Abschlusses.
