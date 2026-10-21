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
| A-V0.13-00016 | zuV0.13 | Softwareseitig geprüfter Teilabschluss: Echtzeit-Zahlenanzeigen auf 100-ms-Takt gebündelt, Endwerte/Fehler unmittelbar; Physik, Kamera, Analog- und 3D-Ausgabe nicht gedrosselt. |
| A-V0.13-00017 | zuV0.13 | Softwareseitig geprüfter Teilabschluss: identische Kraft-/Solvertexte und Navigations-SVG-Ladeaufrufe unterlassen; Fehler und Detailtexte bleiben korrekt. |
| A-V0.13-00018 | zuV0.13 | Aktiven GUI-/Physik-Logpfad geprüft: keine unnötigen normalen Schritt-/Frameausgaben gefunden; Warnungen/Fehler und Startmeldungen erhalten, keine künstliche Loggingänderung. |
| A-V0.13-00019 | zuV0.13 | Softwareseitig geprüft: Kräfte in ganzen N, Momente in ganzen Nm, Längen in m mit zwei Nachkommastellen; Rechtsbündigkeit und interne Physikwerte unverändert. 382 gezielte Tests bestanden. |

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
- [CPPI-Register mit Performance](../Dokumentation/Schnittstellenregister_CPP.md)

Die ursprünglichen Anforderungen bleiben die fachliche Quelle; die
Restarbeiten sind keiner Folgeversion automatisch zugewiesen.
Kein Commit, Push, Tag oder Release im Rahmen dieses Abschlusses.

## V0.13: begrenzter Teilabschluss der Zahlenanzeigen

Nachweis für A-V0.13-00016 bis A-V0.13-00018:
[Umsetzungsplan, Abschnitt 8](../WegZuV1.0/Revisionslog/zuV0.13/Umsetzungsplan/Umsetzungsplan_V013.md#8-ergänzungsauftrag-zahlenanzeigen-und-logging).
343 gezielte Tests bestanden, keine Skips oder Abwahlen. Keine neue
Laufzeitmessung oder behauptete Framebeschleunigung, keine Zeitmarker.
Dies ist keine vollständige V0.13-Abnahme und keine interaktive
Nutzerabnahme; die offenen ursprünglichen Kandidaten und historischen
Gesamtprüfungsbefunde bleiben im Plan sichtbar.

Nachweis des ergänzenden Zahlenformats A-V0.13-00019:
[Umsetzungsplan, Abschnitt 9](../WegZuV1.0/Revisionslog/zuV0.13/Umsetzungsplan/Umsetzungsplan_V013.md#9-ergänzungsauftrag-feste-anzeigepräzision).
Nur Darstellung geändert, keine Rundung der Simulation und kein neuer
Performancebeleg.
