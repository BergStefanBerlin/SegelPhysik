# Spezifikation: Modellpakete und Segler-Massenkörper

**Stand:** 19.10.2026  
**Status:** Anforderungen für die laufende v0.9-Arbeit  
**Geltungsbereich:** Modellpakete unter `code/modelle/` und massewirksame
Besatzung in Segelboot- und Yachtmodellen.

## Kennzeichnungsregel

Aktive Anforderungen dieser Version verwenden die versionsbezogenen
Kennungen `A-V0.9-<laufende-nummer>`. Bei der Umstellung aus dem vorherigen
Schema bleiben die alten Kennungen ausschließlich als historische
Zuordnungen im Anhang erhalten. Neue Verweise verwenden nur die aktive A-ID.

## Aktive Anforderungen

### A-V0.9-00001 — Modellpakete aus dem Modellordner automatisch übernehmen

Jedes direkte Unterverzeichnis von `code/modelle/`, das ein gültiges
`modell.json` enthält, ist automatisch ein verfügbares Modell. Eine neue
Modell-ID und ihre Teilstruktur müssen nicht zusätzlich in
`konfigurationen/koerper.json` eingetragen werden.

Das Manifest ist für Paketmodelle die Quelle der Wahrheit für Modellname,
Teilbaum, Geometrien, Rollen, Posen, Massenangaben und Darstellung. Alle
aufgeführten Geometrieblätter müssen in den Modellbaum übernommen und beim
Aufbau des Laufzeitkörpers geladen und validiert werden. Optionale Einträge in
`koerper.json` dürfen bestehende Konfigurations- oder Sitzungs-Overrides
liefern, aber das Modellpaket nicht erst registrieren müssen.

Die Erkennung verwendet eine explizite, vom aktuellen Arbeitsverzeichnis
unabhängige Modellwurzel. Ungültige Manifeste, fehlende Geometriedateien oder
doppelte Modell-IDs müssen als Fehler erkennbar sein; ungültige Pakete dürfen
nicht stillschweigend als erfolgreiche Modelle erscheinen.

**Abnahmekriterien**

- Ein Paket mit gültigem Manifest erscheint im Modellbaum, auch ohne Eintrag
  in `konfigurationen/koerper.json`.
- Alle manifestierten Blätter und Geometrien werden übernommen und der
  Laufzeitkörper lässt sich daraus aufbauen.
- Vorhandene Modelle, Konfigurations-Overrides und Fehlerdiagnosen bleiben
  funktionsfähig.

### A-V0.9-00002 — Variabler Segler als massewirksamer Körper

Jedes Segelbootmodell muss einen konfigurierbaren Massenkörper mit der
stabilen ID `segler` bereitstellen. Dieser Körper repräsentiert die Besatzung
als zusammengefasste Masse und ist im Modellbaum als eigener Bestandteil
sichtbar. Masse und anfängliche Position sind pro Modell konfigurierbar. Für
das Optimist-Modell ist ein Kind mit einer Masse von ungefähr `50 kg` der
Referenzfall. Andere Klassen verwenden ausdrücklich modellbezogene Werte;
die Optimist-Referenzmasse wird nicht ungeprüft auf andere Boote übertragen.

Die Position des Seglers muss relativ zu einem im Modellpaket explizit
definierten, rumpfzentrierten Referenzpunkt in allen drei Achsen des
rumpffesten Koordinatensystems einstellbar sein. Dieser Referenzpunkt darf
nicht implizit mit dem Gesamtschwerpunkt des Bootes gleichgesetzt werden.
Die Einstellung muss vor einer Simulation veränderbar sein. Der gewählte
dreidimensionale Abstand wird mit dem Modell bzw. dessen Benutzereinstellung
gespeichert und bei späteren Simulationen desselben Modells wiederverwendet;
er darf beim Start einer Simulation oder beim Wechsel zwischen statischer
und dynamischer Simulation nicht auf eine Standardposition zurückgesetzt
werden.

Während einer Simulation ist der Segler starr an die eingestellte Position
des Rumpfs gebunden. Er ist kein unabhängig integrierter Mehrkörper und
bewegt sich während des Simulationslaufs nicht autonom. Seine Masse wirkt
auf den Gesamtkörper, als wäre sie fest mit dem Rumpf verbunden. Sie muss
daher in Gesamtmasse, Gesamtschwerpunkt und Trägheit des Bootes eingehen und
mit der Bootsbewegung transformiert werden. Eine eigene Seglergeometrie oder
ein zusätzliches verdrängendes Volumen ist für dieses Massenobjekt nicht
erforderlich; Masse und Position dürfen jedoch nicht aus der
Gesamtkörperberechnung herausfallen.

**Abnahmekriterien**

- Jedes Segelbootmodell enthält im Modellbaum einen eindeutig
  identifizierbaren `segler`-Massenkörper.
- Masse und rumpffeste Position `(x, y, z)` können je Modell eingestellt
  werden; alle drei Koordinaten beeinflussen die aggregierten
  Masseneigenschaften korrekt.
- Beim Optimist beträgt der dokumentierte Referenzwert etwa `50 kg`.
- Die eingestellte Position bleibt für nachfolgende statische und dynamische
  Simulationen desselben Modells erhalten und wird nicht als Laufzeitzustand
  unabhängig vom Boot integriert.
- Tests belegen Gesamtmasse, Schwerpunkt- und Trägheitsänderung bei
  Änderungen der Seglermasse bzw. jeder der drei Positionskoordinaten.
- Vorhandene Boote ohne Seglerdefinition bleiben während einer
  Migrationsphase ladbar; neu freigegebene Segelbootmodelle erfüllen diese
  Anforderung.

**Freigegebene Umsetzung vom 19.10.2026**

Der Nutzer hat folgende modellbezogenen Startwerte und die separate
Speicherung der Benutzereinstellungen freigegeben:

| Modell | Besatzungsmasse | Position relativ zum Rumpfreferenzpunkt | Expliziter Rumpfreferenzpunkt im Modellframe |
|---|---:|---|---|
| Optimist | 50 kg | (0; 0; 0,45) m | (0; 0; −1,435812) m |
| Folkeboot | 150 kg | (0; 0; 0,85) m | (0; 0; −0,47) m |

Der Referenzpunkt liegt jeweils mittig zwischen den äußeren x-/y-Grenzen
des Rumpfs auf dessen Unterkante, nicht im Gesamtmassenschwerpunkt.
Achsen im rumpffesten Frame: x längs, y quer, z nach oben.
Die Position bezeichnet den Schwerpunkt der zusammengefassten Besatzung.
`yacht1` bleibt in dieser Version ausdrücklich als Migrationsmodell
ohne neue Seglerdefinition ladbar.

Die Umsetzung verwendet eine geometriefreie Punktmasse: Eigenträgheit um
deren Schwerpunkt ist null; ihr Steiner-Anteil zur Gesamtträgheit wird
vollständig berücksichtigt. Das ist eine ausgewiesene
Besatzungs-Modellannahme, kein anatomisches Menschmodell.

Masse und Position können über die Eigenschaftszeilen des Seglers im
Modellbaum geändert werden. Die Einstellungen werden erst nach erfolgreichem
atomarem Schreiben in `konfigurationen/segler.json` übernommen; die
Paketmanifeste bleiben unverändert. Die Datei wird beim erneuten Laden der
Konfiguration eingelesen und ist als lokale Benutzereinstellung von Git
ausgenommen. Fehlende Datei bedeutet explizit Paketdefaults; beschädigte
Dateien und Schreibfehler werden als Fehler gemeldet und nicht durch
scheinbar erfolgreich gespeicherte Defaults verdeckt.

## Historische Kennungszuordnung

| Alte Kennung | Aktive Kennung | Hinweis |
|---|---|---|
| `Spec0114` | `A-V0.9-00001` | Historische Kennung der automatischen Modellpaket-Erkennung |
| `Spec0115` | `A-V0.9-00002` | Historische Kennung des Segler-Massenkörpers |

Die alten Kennungen bleiben als historische Verweise reserviert und werden
nicht wiederverwendet. Aktive Verweise in Spezifikation, Umsetzungsplan,
Tests und Protokollen verwenden die jeweilige `A-V0.9-…`-Kennung.
