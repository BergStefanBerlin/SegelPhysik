# Umsetzungsbericht BL1–BL6

**Stand:** 17.10.2026
**Umfang:** Umsetzung der beiden Backlog-Pläne ohne neue physikalische
Modelle, Kraftgesetze oder Simulationsbeiträge.

## Ergebnisübersicht

| Backlog-ID | Ergebnis | Abnahme |
|---|---|---|
| BL1 | Vorhandene Umwelt-/Kraftverträge und offene Datenquellen in [Bestandsaufnahme_Umwelteingaben_BL1.md](./Bestandsaufnahme_Umwelteingaben_BL1.md) dokumentiert. | Vorbereitung abgeschlossen; Datenquellen und Freigaben für künftige neue Physik bleiben offen. |
| BL2 | Repository-Paket-, Migrations- und Paritätsregressionen ausgeführt; zwei Optimist-Archive als externe Kandidaten lesend geprüft. | Nicht vollständig abgenommen: die meisten OBJ-Dateien scheitern an nicht-planaren Polygonen, der README-Meterfaktor ist ausdrücklich eine Annahme und Manifest-/Material-/Golden-Daten fehlen; Produktions-Cutover bleibt gesperrt. |
| BL3 | Prozessworker-Start und Gate-Anzeige korrigiert; Nachholrate nach Korrektur dreimal über `1,25 s/s`. | Teilweise: Zehnminuten-Live-Lauf löste eine automatische Überlastpause aus und verfehlte die Live-Zeitbilanz. |
| BL4 | Historischen Bericht mit aktuellem sichtbarem Live-Lauf abgeglichen; Rohdaten gespeichert. | Teilweise: aktueller Lauf verfehlte FPS-/Frameabstand- und Überlast-Gates. |
| BL5 | Bestehender 2D-Auftriebssolver um begrenzte stabile Winkelabtastung ergänzt; realer `bleistift`-Fall findet stabile Lage. | Abgeschlossen; Kraft-/Auftriebsmodelle unverändert. |
| BL6 | Vorhandene Paket-/Manifest-, OBJ-/Form-, Meshvalidierungs- und Migrationsinfrastruktur geprüft. | Abgeschlossen ohne Zusatzloader oder neue Produktivmodelle; die Funktionen waren bereits implementiert. |

## BL3/BL4 – Messbedingungen und Befund

- Hardware: AMD Ryzen 5 8600G mit Radeon 760M; Windows 11 Pro,
  Build 26200.
- Python `3.14.8`, PySide6 `6.10.3`, VTK `9.7.1`, NumPy `2.5.4`;
  QPA `windows`.
- Szene `yacht1`, `exakt_union`, alle vier Pflicht-Layer aktiv,
  sichtbares Fenster, 30 s Warm-up und 600 s Messdauer.
- Der bestehende Snapshot besitzt `blatt_meshes`, nicht `.teile`.
  Die veraltete `.teile`-Prüfung ließ den Echtzeit-Prozessworker aus.
  Sie wurde auf die Snapshot-Geometrieschnittstelle umgestellt und mit
  einem GUI-Regressionsfall abgesichert.
- Zusätzlich schrieb der Nachholmodus seinen Status unter einem anderen
  Schlüssel als die sichtbare Gate-Zeile. Die Gate-Zuordnung wurde korrigiert
  und mit Erfolgs- und Fehlerfall getestet.
- Danach betrugen die drei Nachholraten `1,874`, `2,076` und `1,777 s/s`;
  alle drei Durchläufe wurden abgeschlossen und zeigten „bestanden“.
- Der sichtbare zehnminütige Lauf lief mit aktivem Prozessworker und ohne
  Simulationsfehler, pausierte aber automatisch wegen Überlast:
  `13,04` tatsächlich präsentierte FPS (Soll mindestens `30`),
  Frameabstand-P95 `205,098 ms`, maximaler Rückstand `3,078 s`,
  angeforderte Zeit `7,062 s`, berechnete Zeit `3,984 s`.
  Die Überlastpause trat auf; der gemeldete Nulltrend über das restliche
  pausierte Fenster ist kein Nachweis stabilen Dauerbetriebs.
- Eingaben wurden `599/599` sichtbar beantwortet; P95 der
  Eingabe-bis-Frame-Latenz war `7,837 ms`. Diese Eingabelatenz besteht,
  hebt die verfehlten Live-Gates aber nicht auf.
- Der historische Bericht [Abnahme_R-4a.md](../Bisherige/Abnahmen/Abnahme_R-4a.md)
  dokumentiert `4,4 / 4,5 / 4,8×` Nachholrate. Seine Rohdaten liegen nicht
  im Bericht und sind nicht nachweislich unter identischen Bedingungen
  erhoben worden; die Werte bleiben daher als historischer Befund getrennt.

Vollständige Rohdaten inklusive der 600 Rückstandsproben liegen in
`Messungen/BL3_BL4_live_yacht_exakt_union_worker_2026-10-17.json`.
Der Diagnose-Lauf ohne Worker ist separat als
`Messungen/BL3_BL4_live_pre_workerfix_yacht_exakt_union_2026-10-17.json`
gespeichert. Die erste abgeschlossene Nachholmessung vor Korrektur der sichtbaren
Gate-Zeile liegt in `Messungen/BL3_nachholen_yacht_worker_pre_gatefix_2026-10-17.json`;
die abschließende Dreifachmessung mit funktionierendem Gate-Status liegt in
`Messungen/BL3_nachholen_yacht_worker_gate_2026-10-17.json`.

## BL5 – bestehender `bleistift`-Fall

Der bestehende Newton-/Störleiterpfad fand aus `(z=0, phi=0)` nur eine
instabile Lage. Nachgewiesener Kandidat bei festem vertikalem
Kräftegleichgewicht lag bei ungefähr `89,97°` und hatte ein
restaurierendes Rollmoment. Die Korrektur durchsucht nun nur nach einem
konvergierten, aber instabilen Ergebnis den periodischen 2D-Rollwinkel in
180 festen Intervallen, löst je Winkel das bestehende vertikale
Kräftegleichgewicht und verfeinert Momentennulldurchgänge. Akzeptiert wird
nur ein Kandidat mit negativem Rollmomentgradienten und geprüftem Residuum.
Eine ausdrücklich leere Störleiter behält ihr bisheriges Verhalten.

Der echte Modell-/`exakt_union`-Regressionstest liefert:

- `z = -0,0011178701 m`, `phi = 1,5702679556 rad`;
- Restkraft `9,47e-10 N`, Restmoment `4,84e-9 N·m`;
- `stabil = true`, `neutral = false`, `GM = 0,502856 m`.

## BL2/BL6 – Umfangsgrenze und externe Abhängigkeit

Die Paket-/Loader-/Mesh-/Fabrik-/Migrationsauswahl ergab `114 passed`,
`1 skipped`. Sie deckt unter anderem synthetische OBJ-Fixtures,
Formgeometrien, sichere Paketpfade, Meshfehler, Bestandsparität, Dry-run und
Nichtüberschreiben ab. BL6 erforderte deshalb keine neue Importlogik.

Die externen Kandidatenarchive
[`optimist_einzelteile.zip`](../../../Backlog/Ideen/optimist_einzelteile.zip)
und [`optimist_obj.zip`](../../../Backlog/Ideen/optimist_obj.zip) wurden
nicht extrahiert oder verändert. 16 von 20 OBJ-Einzelteil-Dateien scheitern
bereits beim Parsing an nicht-planaren Polygonen; die beiden Gesamt-OBJs
scheitern ebenfalls. Nur Ruder und Pinne (jeweils Roh- und Meter-Variante)
lassen sich syntaktisch einlesen; damit sind weder Topologie noch Masse
abgenommen. Die README benennt `0,225105` als angenommene, nicht aus der
Quelldatei belegte Skalierung. Manifest/Legacy-Materialdaten und erwartete
Massen-/GUI-Golden fehlen. Für den BL2-Abschluss ist daher ein freigegebener,
repräsentativer externer Bestand mit reparierten/unterstützten Geometrien und
verifizierten Einheiten, Achsen, Material-/Dichteangaben und Golden-Daten
erforderlich. Es wurden weder Meshreparaturen vorgenommen noch Werte
geschätzt; die Produktionsumschaltung bleibt gesperrt.

## Testläufe

Die gezielten Solvertests wurden mit `26 passed` ausgeführt. Die
Paket-/Import-/Migrationsgruppe wurde mit `114 passed, 1 skipped` ausgeführt.
Die vollständige Regressionstestsuite endete mit `570 passed, 1 skipped`;
`git diff --check` war sauber.
