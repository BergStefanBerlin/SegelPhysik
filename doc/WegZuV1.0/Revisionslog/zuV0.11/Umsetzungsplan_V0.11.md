# Umsetzungsplan V0.11: Kraft- und Momentendarstellung

**Stand:** 20.10.2026  
**Status:** Umsetzung beauftragt am 20.10.2026; gemeinsame Anzeige produktiv integriert, Modell-/Triggernachweise fortgeschrieben; physische Monitorprüfung und fachliche/Leistungs-Gesamtabnahme offen  
**Fachliche Quelle:** [Spezifikation_V0.11.md](Spezifikation_V0.11.md)  
**Umfang:** 48 aktive Anforderungen, 14 Umsetzungsschritte, sechs Meilensteine  
**Maßgeblicher Umsetzungsplan für V0.11:** diese Datei

## 1. Arbeitsvertrag und Freigabe

Dieser Plan beschreibt die vollständige Umsetzung der aktuellen
Spezifikation. Er erteilt keine eigenständige Implementierungs-, Commit-,
Branchwechsel-, Push-, Tag- oder Releasefreigabe. Die Spezifikation ist
zur Umsetzung freigegeben: Nutzerauftrag vom 20.10.2026
„Bitte Umsetzungsplan umsetzen.“ Dies ist keine fachliche Abnahme
der Implementierung. Statusangaben werden nicht eigenmächtig
in eine fachliche Abnahme umgedeutet.

Es gelten die
[Arbeitsanweisung Releaseumsetzung](../../../../.github/instructions/releaseumsetzung.instructions.md),
die [Nummerierungsregeln](../../../../.github/instructions/nummerierung.instructions.md)
und bei Git-Aktionen die
[Release-Regeln](../../../../.github/instructions/release.instructions.md).
Alte Versionsschritte werden nicht bereinigt oder umstrukturiert.

- Eine gemeinsame Spezifikation und dieser eine Umsetzungsplan bleiben
  maßgeblich. Inventare, Testprotokolle und Rohmessungen dürfen als
  unterstützende Belege abgelegt werden, enthalten aber keine zusätzlichen
  Anforderungen oder parallelen Arbeitspläne.
- Bestehende Physik und Python-/C++-Rechenpfade erhalten. Keine neuen
  Kraftgesetze, keine Gegenkraftfiktion und keine GUI-Ersatzphysik.
- Jede Quellinstanz eindeutig zuordnen. Herkunft, Frame, Bezugspunkt,
  Zeitschritt und fehlende Daten dürfen nicht durch Darstellung verdeckt
  werden. Summen und Komponenten nicht erneut bilanzieren.
- Eine gemeinsame Anzeige für Statik, stationäre Auswertung, laufende
  und pausierte Dynamik. Kein Timerzwang für statische Aktualisierungen.
- Übernommene Helfer sind Teil der neuen gemeinsamen Lösung.
  Übergangsweise Varianten sind keine zweite dauerhaft gepflegte Codebasis.
  Alle ersetzten produktiven Zeichenpfade werden vor Abnahme entfernt.
- Änderungen an nativen Verträgen nur bei nachgewiesenem Bedarf; dann
  [Schnittstellenregister-Regeln](../../../../.github/instructions/schnittstellenregister.instructions.md)
  einschließlich Build, Vertragsnachweis und CPPI-Pflege anwenden.
- Nicht erfüllte Anforderungen bleiben offen. Scopeänderungen,
  geänderte fachliche Grenzen oder Verschiebungen ins Backlog benötigen
  eine ausdrückliche Entscheidung.

## 2. Reihenfolge und Meilensteine

Die Nummern geben die empfohlene Integrationsreihenfolge wieder.
Sachliche Voraussetzungen stehen ausdrücklich in den Schritten.
Unabhängige Vorbereitung darf vorgezogen werden, ersetzt aber kein Gate.

| Meilenstein | Schritte | Eintritt | Ergebnis / Austrittsgate |
|---|---|---|---|
| M1 – Ausgangslage und Referenz | U-V0.11-000001, U-V0.11-000002 | Freigegebener Arbeitsumfang | Alle Quell-/Altpfade und Trigger zugeordnet; Referenzfälle, Messumgebung und Datenlücken dokumentiert |
| M2 – Gemeinsame fachliche Daten | U-V0.11-000003, U-V0.11-000004 | M1 | Register und unveränderliche Snapshots; korrekte Bilanz und Gleichgewichtsstatus; algebraische Tests und erster Solververgleich bestanden |
| M3 – Darstellungsbausteine | U-V0.11-000005, U-V0.11-000006, U-V0.11-000007 | M2 | Skalierung, gewähltes Zeichenverfahren, Bögen, Hebelarme und Auswahl aus gemeinsamen Daten geprüft |
| M4 – Wertefenster und Einstellungen | U-V0.11-000008, U-V0.11-000009 | M3; Mockup-Prinzip bestätigt | PySide6-Fenster, bidirektionale Auswahl, Status, Körperumfang und Settings-Wiederherstellung geprüft |
| M5 – Betriebsarten und vollständige Ablösung | U-V0.11-000010, U-V0.11-000011, U-V0.11-000012 | M4 | Alle Modi und Trigger integriert; keine produktiven Altpfade, keine doppelte Physik/Actors; Integratorparität nachgewiesen |
| M6 – Gesamtabnahme | U-V0.11-000013, U-V0.11-000014 | M5 | Sichtbare Prüfungen, Regression, Ressourcen-/Leistungsbelege und vollständige 48-A-Abschlussmatrix; offene Entscheidungen ausdrücklich aufgelöst |

Ein Meilenstein ist erst nach tatsächlichen Nachweisen bestanden.
Vorhandene Implementierung, Build, Tests, sichtbare Prüfung und
Nutzerabnahme werden getrennt dokumentiert.

## 3. Umsetzungsschritte

### U-V0.11-000001 — Ausgangsstand, Quellen und Altpfade erfassen

**Anforderungen:** A-V0.11-00001, A-V0.11-00003, A-V0.11-00004,
A-V0.11-00015, A-V0.11-00035, A-V0.11-00038, A-V0.11-00042,
A-V0.11-00048  
**Abhängigkeiten:** keine  
**Meilenstein:** M1

- Branch, Commit, uncommittierte Änderungen und betroffene Dateien
  festhalten; fremde Änderungen erhalten, keine automatische Git-Sicherung.
- Vorhandene Quellen in Kraftmodell, Hydrostatik, Hydrodynamik,
  statischen/stationären Solvern und dynamischen Worker-/Batchpfaden
  erfassen. Für jeden Modus Datenverfügbarkeit, Gewichtbehandlung,
  Added-Mass-Formulierung, Frames und tatsächlichen Momentenbezug prüfen.
- Alle alten Kraft-/Momentenzeichenpfade, Aufrufer, Register, Einstellungen,
  Geometriehelfer, Caches und zugehörige Tests inventarisieren.
  Kennzeichnung je Eintrag: weiterverwenden, anpassen oder ersetzen/entfernen.
  Gemeinsam genutzte Helfer anderer Darstellungen ausdrücklich schützen.
- Für jeden der 28 Trigger aus Spezifikation 4.9 vorhandenen Eingabeweg,
  Signal/Callback, betroffene Abhängigkeit und Gültigkeitsmodus zuordnen.
  Steuer-API und indirekte Modelländerungen einschließen.
- Fachlich mögliche Überlagerungen von Widerstand und Hydrodynamik
  sowie nicht vorhandene Originalangriffspunkte auflisten.
- Lücken in benötigten Diagnosedaten benennen und minimalen Transport
  planen; fehlende Diagnose nicht durch GUI-Neuberechnung ersetzen.

**Gate/Nachweis:** Rückverfolgbares Quellen-/Altpfad-/Triggerinventar mit
Fundstellen und vorgesehenem Ziel. Alle bekannten Eingänge eingeordnet;
ungeklärte physikalische Verträge sind vor ihrer Umsetzung zu klären.

### U-V0.11-000002 — Referenztests, Baseline und Prüfmatrix vorbereiten

**Anforderungen:** A-V0.11-00002, A-V0.11-00030, A-V0.11-00031,
A-V0.11-00032, A-V0.11-00033, A-V0.11-00034, A-V0.11-00048  
**Abhängigkeiten:** U-V0.11-000001  
**Meilenstein:** M1

- Vor Änderungen gezielte Bestandsregression ausführen und tatsächliche
  Ergebnisse festhalten. Vorbestehende Fehler getrennt melden.
- Die algebraischen Referenzfälle aus Spezifikation 7.1 als Fixtures
  und Vergleichsfunktionen vorbereiten, unabhängig vom neuen Renderer.
- Modus-/Backendmatrix für Statik, stationäre Auswertung und
  Dynamik/Pause aufstellen; vorhandene Python-/C++-Pfade zuordnen.
- Reproduzierbare Szenen für Nullwerte, viele Beiträge, verteilte Kräfte,
  Mehrkörperanzeige, Kamera/DPI und Lifecycle festlegen.
- Vorhermessung von Aktualisierungsdauer, Frameabständen, Actoranzahl
  und Speicher mit Anzeige aus/ein aufnehmen. Quellstand, Modell,
  Eingaben, Hardware, Build und Wiederholungen festhalten.
- Bestehende Solver-/Integratorvergleichstoleranzen mit Quelle erfassen.
  Fehlende reale Grenzwerte als Entscheidungspunkt führen, nicht erfinden.

**Gate/Nachweis:** Wiederholbarer Ausgangszustand und konkrete Testmatrix.
Algebraische Grenzen: `rtol=1e-10`, `atol=1e-9` gemäß Spezifikation 7.1.
Dies ist noch kein Nachweis der neuen Anzeige.

### U-V0.11-000003 — Beitragsregister, Identitäten und Snapshots aufbauen

**Anforderungen:** A-V0.11-00002, A-V0.11-00004, A-V0.11-00005,
A-V0.11-00009, A-V0.11-00010, A-V0.11-00011, A-V0.11-00012,
A-V0.11-00013, A-V0.11-00015, A-V0.11-00022  
**Abhängigkeiten:** U-V0.11-000001, U-V0.11-000002  
**Meilenstein:** M2

- Vorhandenes Register und `Stil` weiterentwickeln: Quellen,
  Gruppenzuordnung, Layout, Punktart und Ableitungsart zentral führen.
- Bestehende IDs erhalten; stabile Quellinstanzen gleicher Rolle
  auseinanderhalten. Keine dauerhafte Identität aus Listenposition ableiten.
- Schlanke Anzeigedaten und Snapshot mit Körper-ID, Generation,
  Sequenz, physikalischer Zeit und Kraftpose umsetzen. Vorhandene
  `Wrench`, `Kraftbeitrag`, `KraftErgebnis` und `Pose` wiederverwenden.
- Status für null, fehlend, deaktiviert, ungültig und veraltet
  explizit führen. Unbekannte gelieferte Beiträge sichtbar zuordnen.
- Keine GUI-/VTK-Objekte in fachliche Daten und Worker-Nachrichten
  aufnehmen; Unveränderlichkeit auch bei enthaltenen Arrays sicherstellen.

**Gate/Nachweis:** Tests für Identitäten, Gruppen, Provenienz, sämtliche
Datenzustände und unabhängigen Datenbesitz. Rendererfreie Snapshottests.
Vorhandene Settings-/Pfeilregistertests gezielt erweitern.

### U-V0.11-000004 — Bilanzadapter, Wirkungslinien und Status absichern

**Anforderungen:** A-V0.11-00003, A-V0.11-00006, A-V0.11-00007,
A-V0.11-00008, A-V0.11-00030, A-V0.11-00039, A-V0.11-00040,
A-V0.11-00041, A-V0.11-00042, A-V0.11-00048  
**Abhängigkeiten:** U-V0.11-000003  
**Meilenstein:** M2

- Ergebnisverträge explizit normalisieren. Bestehende Wrench-
  Transformation und Aggregation verwenden; Hebelarm nicht erneut addieren.
- Gewicht über vorhandenes Merkmal genau einmal berücksichtigen.
  Added Mass anhand der tatsächlichen Bilanzform einordnen.
- Quellenauflösung und tatsächlich vorliegende Solver-Gesamtsumme
  getrennt nachvollziehbar führen. Summen/Komponenten nicht bilanzieren.
- Vollständigkeit aus erwarteten aktiven Quellen ableiten:
  Gesamtbilanz, Teilsumme und ungeklärter Umfang eindeutig unterscheiden.
- Gleichgewicht nur aus passenden Solver-Kriterien, Freiheitsgraden und
  demselben Zustand ausweisen. Kein Status aus gerundeten Zahlen ableiten.
- Äquivalente Wirkungslinie mit Restmoment und instabilitätsbedingter
  Wrench-Darstellung nach Spezifikation 3.8 umsetzen; keine echte
  Kraftanwendung an einem nur geometrischen Schnittpunkt behaupten.

**Gate/Nachweis:** Alle algebraischen Fälle aus 7.1, Grenzfälle beidseits
von epsilon_F und zehn Körperausdehnungen, fehlende Geometrie,
NaN/Inf, doppelte Namen, unvollständige Quellen und Framewechsel testen.
Erster Vergleich gegen vorhandene Solver-/Integratorreferenzen.

### U-V0.11-000005 — Gemeinsame Skalierung und Formatierung implementieren

**Anforderungen:** A-V0.11-00014, A-V0.11-00019, A-V0.11-00020,
A-V0.11-00027, A-V0.11-00041  
**Abhängigkeiten:** U-V0.11-000004  
**Meilenstein:** M3

- Linear-/log1p-Abbildung, Referenzinitialisierung, Einfrieren,
  manuelle Referenzen und „Neu einpassen“ gemäß Spezifikation 5.4
  umsetzen. Keine unbeauftragte automatische Nachregelung.
- Kraft-/Momentendomänen getrennt; Sichtbarkeit verändert Referenzen
  und Bilanz nicht. Körpervergleich nur mit gekennzeichneter Skala.
- Grenz-/Kleinwertkennzeichnung, Legendenwerte und deutsch lokalisierte
  Zahlenformatierung aus Originalwerten ableiten.
- Vier signifikante Stellen kompakt und bis zu 17 in Details;
  kleine Werte nicht als exakte Null und Fehler nicht als Zahl anzeigen.

**Gate/Nachweis:** `u(0)=0`, `u(R)=1`, Monotonie vor Begrenzung,
ungültige Referenzen, Extremwerte und identische Beträge prüfen.
Formatierungs- und Sichtbarkeitsinvarianztests.

### U-V0.11-000006 — Zeichenverfahren erproben und gemeinsame 3D-Geometrie integrieren

**Anforderungen:** A-V0.11-00016, A-V0.11-00017, A-V0.11-00021,
A-V0.11-00022, A-V0.11-00023, A-V0.11-00036, A-V0.11-00044  
**Abhängigkeiten:** U-V0.11-000005  
**Meilenstein:** M3

- Vorhandene Geometrie-/Actor-Helfer mit kurzen Pfeilen, beliebigen
  Momentenrichtungen, Perspektive, paralleler Kamera und DPI erproben.
- Werkzeugentscheidung hier im Plan begründen: vorhandenes Verfahren
  bevorzugen, direktes VTK nur für konkrete Lücken; Glyph-Rendering
  nur nach belegtem Vorteil und vollständigem Funktionsnachweis.
- Eine zentrale Darstellung für Kraftpfeile, 240°-Momentenbögen,
  Restmomente und Komponenten integrieren. Richtung aus Originalvektor,
  Radius aus Momentskala; stabile Bogenbasis umsetzen.
- Kameraabhängige Größen, konstante Strichstärke, kurze Köpfe,
  Kleinwerte, Nullwerte und Raum-/Vordergrundmodus abdecken.
- Registerfarben, Linienarten, Sichtbarkeit und explizite
  Nutzerüberschreibungen einheitlich auflösen; Geometrie wiederverwenden.

**Gate/Nachweis:** Numerische Geometrietests einschließlich
Rechte-Hand-Regel, Vorzeichenwechsel, Achsendegeneration und Null.
Sichtbare Verfahrenserprobung; kein Verfahrenswechsel nur aus Vermutung.
Native Geometrieverträge bei tatsächlicher Änderung mitprüfen.

### U-V0.11-000007 — Hilfsgeometrie, Beschriftung und Picking anbinden

**Anforderungen:** A-V0.11-00018, A-V0.11-00024, A-V0.11-00028,
A-V0.11-00045  
**Abhängigkeiten:** U-V0.11-000006  
**Meilenstein:** M3

- Reale/äquivalente Punkte, Momentenbezug, Wirkungslinien und
  senkrechte Hebelarme darstellen; unbekannte Herkunft nicht ersetzen.
- Auswahl-ID zentral halten; Quellen und Momente gemeinsam hervorheben.
  Labels priorisieren: Auswahl vor Gesamtbilanz vor Einzelbeiträgen.
- Picker mit sechs logischen Pixeln zusätzlicher Trefferzone,
  DPI-/Kameraumrechnung und eindeutiger Mehrfachtrefferauswahl anbinden.
- Vorhandene Navigation nicht still umbelegen; verdeckte oder
  ausgeblendete Beiträge bleiben über die spätere Tabelle erreichbar.

**Gate/Nachweis:** Bekannter senkrechter Hebelarm, reine Momente,
äquivalenter Anker, dicht überlagerte Pfeile, Auswahl/Abwahl,
Langnamen und kleine Fenster prüfen. Keine Physikaufrufe durch Auswahl.

### U-V0.11-000008 — Wertefenster nach Prinzipdarstellung umsetzen

**Anforderungen:** A-V0.11-00025, A-V0.11-00026, A-V0.11-00027,
A-V0.11-00028, A-V0.11-00029, A-V0.11-00039, A-V0.11-00040,
A-V0.11-00043  
**Abhängigkeiten:** U-V0.11-000007  
**Meilenstein:** M4

- Bestätigtes [HTML-Mockup](Mockup_Wertefenster.html) als Prinzipreferenz
  verwenden. Statusbeschriftung an die inzwischen präzisierte Spezifikation
  anpassen; keine erneute Freigabe des unveränderten Prinzips verlangen.
  Den vorhandenen Abstimmungsbeleg für A-V0.11-00029 gesondert führen;
  die produktive Qt-Umsetzung und deren Abnahme belegen insbesondere
  A-V0.11-00025 bis A-V0.11-00028, nicht die Mockup-Abstimmung.
- PySide6-Dockfenster mit Modell/View integrieren; keine HTML-
  Einbettung und keine duplizierte fachliche Liste.
- Kopf, Bilanzkarten, Gruppen, Komponenten, Punktart, Quellen,
  Status und Detailformeln aus demselben Snapshot erzeugen.
- Auswahl bidirektional verbinden, Werte schreibgeschützt halten;
  Sichtbarkeit beeinflusst keine Summen.
- Standard Einzelkörper, optional getrennte Mehrkörperzweige;
  keine neue physikalische Gesamtsumme über mehrere Körper.

**Gate/Nachweis:** Qt-Tests für Hierarchie, Detailauswahl, Sichtbarkeit,
Status-/Teilsummenkennzeichnung, Fensterwiederöffnung und Körperwechsel.
Sichtprüfung gegen das abgestimmte Prinzip, keine pixelgenaue HTML-Kopie.

### U-V0.11-000009 — Einstellungen, Migration und Persistenz abschließen

**Anforderungen:** A-V0.11-00015, A-V0.11-00020, A-V0.11-00022,
A-V0.11-00043, A-V0.11-00046  
**Abhängigkeiten:** U-V0.11-000008  
**Meilenstein:** M4

- Bestehende Settings-Schlüssel übernehmen oder nachvollziehbar
  migrieren. Überschreibungen und einheitliche Maßstäbe explizit abgleichen.
- Registerfarben, Sichtbarkeit, Skalenmodus, manuelle Referenzen,
  Geometrieoptionen und Fenster-/Spaltenlayout dauerhaft speichern.
- Automatische Snapshotreferenzen nicht als manuelle Werte persistieren.
  Keine Kräfte, Auswahl, Sequenzen oder vermeintlich gültigen Solverzustände
  aus GUI-Einstellungen wiederherstellen.
- Validierungsfehler melden; Reset und Monitorwechsel mit
  erreichbarer Fensterposition behandeln.

**Gate/Nachweis:** Tests mit vorhandenen und neuen Settings,
Nutzerüberschreibungen, Reset, Neustart und fehlendem Monitor.
Keine parallele Pflege überholter Schlüssel.

### U-V0.11-000010 — Alle Modi und Aktualisierungstrigger verdrahten

**Anforderungen:** A-V0.11-00012, A-V0.11-00013, A-V0.11-00031,
A-V0.11-00037, A-V0.11-00038, A-V0.11-00047  
**Abhängigkeiten:** U-V0.11-000009  
**Meilenstein:** M5

- Gemeinsame Snapshot-/Anzeigeanbindung für Statik, stationäre Auswertung,
  Dynamik und Pause aktivieren. Erforderliche Diagnosedaten am vorhandenen
  Rechenweg mitführen, ohne Renderer-/Tabellen-Physik einzuführen.
- Kraftglyphen, Bezugspunkte und Tabelle der mitgelieferten Kraftpose
  zuordnen. Einen Zeitversatz zur interpolierten Körperszene sichtbar
  kennzeichnen; keine Kräfte still auf eine andere Körperpose übertragen.
- Alle 28 Triggerfamilien aus Spezifikation 4.9 anhand des Inventars
  verdrahten; neu gefundene Eingänge ergänzen. GUI und Steuer-API
  müssen dieselben Abhängigkeiten invalidieren.
- Fachlich, Ableitung und grafisch trennen. Auch bei gestoppten Timern
  aktualisieren bzw. explizit „veraltet/in Berechnung“ anzeigen.
- Generation/Sequenz, Pause/Reset und veraltete Workerergebnisse behandeln.
  Neueste Ergebnisse begrenzt bündeln; 3D und Tabelle atomar publizieren.
  Fehler- und Ungültigkeitsmeldungen unabhängig von ersetzten Snapshots
  im vorhandenen Protokoll erhalten.
- Kamera und Stil lösen keine Kraftfunktion aus; Quellenänderungen
  werden nicht durch bloßes Rendern als erledigt ausgegeben.

**Gate/Nachweis:** Parametrisierte Trigger-/Modusmatrix. Jeder anwendbare
Fall in Statik und Pause mit gestopptem Timer geprüft; laufende Dynamik
und stationäre Auswertung ergänzend. Nichtanwendbarkeit begründen.
Schnelle Eingabeserien, verspätete Ergebnisse und letzte Veröffentlichung
prüfen. Einen von einem gültigen Ergebnis unmittelbar überholten
Fehlerstand einspeisen und dessen erhaltenen Protokolleintrag nachweisen.
Interpolierte Körperpose und abweichende Kraftpose gezielt prüfen:
3D-Kräfte und Tabelle bleiben am selben Snapshot, der Zeitversatz ist sichtbar.
Gleicher Snapshot und Settings ergeben gleiche Darstellungsdaten;
für identische Bogenphasen denselben initialisierten Darstellungszustand
verwenden und keine modusabhängigen Sonderregeln zulassen.

### U-V0.11-000011 — Solver-/Integratorparität durchgängig nachweisen

**Anforderungen:** A-V0.11-00006, A-V0.11-00007, A-V0.11-00030,
A-V0.11-00039, A-V0.11-00040, A-V0.11-00042, A-V0.11-00048  
**Abhängigkeiten:** U-V0.11-000010  
**Meilenstein:** M5

- Reale statische, stationäre und dynamische Zustände mit
  akzeptierter Zeit/Stufe, Frame und Bezug instrumentiert vergleichen.
- Anzeige, atomare Summe und tatsächlich verwendete Solverbilanz
  gegenüberstellen. Gewicht und Added Mass in äquivalenten Bilanzformen
  prüfen; Diagnosebeitrag nicht als zusätzliche Dynamikkraft anwenden.
- Python-/C++-Varianten soweit vorhanden einbeziehen. Fehlende
  Diagnose-/Grenzwerte explizit offen halten, keine unbelegte Parität.
- Überlagerte Modelle mit aktivierter Konfiguration belegen;
  bei fachlicher Unklarheit Entscheidung einholen, nichts herausfiltern.

**Gate/Nachweis:** Reproduzierbare Vergleichsfälle mit tatsächlichen
Toleranzquellen und Ergebnissen. Keine verglichenen unterschiedlichen
Integrationsstufen oder unmarkierte unvollständige Einzelauflösung.

### U-V0.11-000012 — Ersetzte Altpfade vollständig entfernen

**Anforderungen:** A-V0.11-00015, A-V0.11-00035, A-V0.11-00036  
**Abhängigkeiten:** U-V0.11-000011  
**Meilenstein:** M5

- Das ursprüngliche Inventar zeilenweise abschließen: Aufrufer auf
  gemeinsame Lösung umgestellt, übernommene Helfer identifiziert,
  ersetzte Zeichenpfade und doppelte Berechnungen entfernt.
- Nicht mehr benötigte Register-/Settingslogik nach erfolgreicher
  Migration entfernen; kein wählbarer Altpfad und kein stiller Fallback.
- Testhilfen mit überholten Annahmen gezielt an neue Verträge anpassen;
  keine Tests nur entfernen, um Fehler zu verdecken. Physikreferenzen
  und benötigte gemeinsame Helfer erhalten.
- Aktive Renderwege und Actor-/Signalregistrierung prüfen;
  wiederholte Körper-/Fensterwechsel erzeugen keine Duplikate.

**Gate/Nachweis:** Quellcode-/Aufruferprüfung und Regression belegen die
Entfernung. Kein leerer „erledigt“-Vermerk und kein Build als alleiniger
Beweis. Temporäre produktive Verzweigungen sind beseitigt.

### U-V0.11-000013 — Sichtbare, Performance- und Ressourcenabnahme durchführen

**Anforderungen:** A-V0.11-00021, A-V0.11-00024, A-V0.11-00031,
A-V0.11-00032, A-V0.11-00033, A-V0.11-00037, A-V0.11-00044,
A-V0.11-00045, A-V0.11-00047  
**Abhängigkeiten:** U-V0.11-000012  
**Meilenstein:** M6

- Sichtbare Prüfung bei 100/150/200 % DPI, Perspektive/Parallelkamera,
  Zoom, kleinen Fenstern und Vektoren in Blickrichtung.
- Kopf-/Strichgrößen in nicht verkürzter Testlage mit höchstens einem
  logischen Pixel Abweichung prüfen; überlagerte/verdeckte Pfeile,
  Auswahltoleranz, Labels und Momentenorientierung testen.
- Statische/pausierte Änderung sichtbar ohne Start des Timers nachweisen.
  Wertefenster und 3D müssen dieselbe Snapshotsequenz zeigen.
- Vorher-/Nachhermessung auf der M1-Baseline für einfache und viele
  Beiträge, Anzeige aus/ein, Mehrkörper und wiederholte Lifecyclewechsel.
  Aktualisierungsdauer, Frameabstände, Actors, Queue und Speicher erfassen.
- Mit gezielt verlangsamter GUI sowie geöffnetem und geschlossenem
  Wertefenster prüfen, dass Anzeige und Snapshottransport den Worker
  nicht blockieren. Worker-Fortschritt und Ergebnisübergabe belegen;
  Laufzeitschwankungen von blockierendem Warten unterscheiden und die
  ursprüngliche GUI-Taktrate nach dem Versuch wiederherstellen.
- Taktrate mit Messergebnis dokumentieren. Leistungsgrenzen bzw.
  akzeptierte Verschlechterungen vor Abnahme ausdrücklich entscheiden
  lassen; keine erfundenen FPS-Werte und keine rückwirkende Baselineänderung.

**Gate/Nachweis:** Tatsächliche sichtbare Belege und Rohmessungen mit
Umgebung. Offscreen-Erfolg allein reicht nicht. Offene Leistungsentscheidung
sperrt den vollständigen Abschluss.

### U-V0.11-000014 — Regression, Nachweismatrix und Abschluss dokumentieren

**Anforderungen:** A-V0.11-00001, A-V0.11-00034; abschließender Abgleich
aller A-V0.11-00001 bis A-V0.11-00048  
**Abhängigkeiten:** U-V0.11-000013  
**Meilenstein:** M6

- Abschließende Regression und erforderliche native Builds/Vertragstests
  ausführen. Skips und nicht ausgeführte sichtbare Prüfungen getrennt nennen.
- Alle 48 A-Zeilen unten mit konkreten Tests/Belegen und tatsächlichem
  Status abschließen. Kein Meilenstein gilt durch Tabellenpflege allein.
- Abschluss gegen Spezifikation, Triggerinventar, Altpfadabbau,
  Nutzeroptionen und Umfang auf bekannte Physik abgleichen.
- Erfüllte/abgenommene Anforderungen nach geltender Nummerierungsregel
  im zentralen Projektlog dokumentieren. Offene Punkte nicht eigenmächtig
  zurückziehen oder als neue Versionsarbeit behandeln.
- Arbeitsbaum und verbleibende Änderungen nennen. Keine Veröffentlichung,
  kein Tag und kein automatischer Commit.

**Gate/Nachweis:** Vollständige belegte Abschlussmatrix und ausdrückliche
fachliche Abnahme. Bei offenen Pflichtnachweisen bleibt der Abschluss offen;
eine begrenzte Freigabe bedarf einer gesonderten Nutzerentscheidung.

## 4. Prüfstrategie und vorhandene Tests

Während der Umsetzung zunächst den kleinsten passenden gemeinsamen
Testlauf verwenden; erst bei Integration und Abschluss die Regression
erweitern. Vorhandene Dateien sind Ausgangspunkte, keine Aussage über
bereits ausreichende Testabdeckung.

| Bereich | Vorhandene Ausgangspunkte / ergänzende Nachweise |
|---|---|
| Physik, Wrench, Gewicht, Added Mass | [test_kraftmodell.py](../../../../tests/test_kraftmodell.py), [test_frames.py](../../../../tests/test_frames.py); neue Adapter-/Snapshotfälle gemäß Spezifikation |
| Register, Stil, Migration | [test_pfeilstil.py](../../../../tests/test_pfeilstil.py); zentrale Skala, Farben, Status und Persistenz ergänzen |
| Geometrie und native Pfade | [test_native_kraftgeometrie.py](../../../../tests/test_native_kraftgeometrie.py), [test_overlays.py](../../../../tests/test_overlays.py); Restmoment, freie Bogenachse und Bildschirmumrechnung prüfen |
| GUI, API und Lifecycle | [test_gui_laufzeit_edit.py](../../../../tests/test_gui_laufzeit_edit.py), [test_gui_steuerung.py](../../../../tests/test_gui_steuerung.py), [test_gui_steuer_api.py](../../../../tests/test_gui_steuer_api.py) |
| Worker-/Generationsverhalten | [test_native_worker.py](../../../../tests/test_native_worker.py) und passende bestehende GUI-Workerfälle |
| Sichtbare Abnahme | Tatsächliches Qt-/VTK-Fenster; DPI, Kamera, Picking, statische Trigger und erneutes Öffnen |
| Leistung | Baseline und identische Nachmessung; Rohwerte, Umgebung und Nutzerentscheidung bei offenen Grenzwerten |

Beispiel für einen zusammengefassten gezielten Physik-/Stiltestlauf:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_kraftmodell.py tests\test_frames.py tests\test_pfeilstil.py
```

Abschlussregression:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q
```

Diese Befehle beschreiben die Prüfstrategie; tatsächliche Läufe und
Ergebnisse stehen in Abschnitt 9. Sichtbare Prüfungen erfolgen ohne erzwungenen
offscreen-Modus. Neue Testdateien werden nur nach konkretem Bedarf
innerhalb der bestehenden pytest-Struktur ergänzt.

## 5. Rückverfolgbarkeitsmatrix

Alle Zeilen verweisen auf die eine
[Spezifikation](Spezifikation_V0.11.md). U-Nummern stehen hier zur
Lesbarkeit sechsstellig verkürzt für `U-V0.11-<Nummer>`.
Die Kriterien bleiben verbindlich. Die Statusspalte unterscheidet
technische Prüfung und Teilnachweis; beides ist keine Nutzerabnahme.
Nachweiskürzel:
[D – Anzeigedaten](../../../../tests/test_kraefte_anzeige.py),
[G – Darstellungsgeometrie](../../../../tests/test_kraefte_darstellung.py),
[W – Wertefenster](../../../../tests/test_kraefte_werte.py),
[I – Integration](../../../../tests/test_kraefte_integration.py),
[S – Stil/Settings](../../../../tests/test_pfeilstil.py),
[Q – reale Windows-Qt-Probe](Messungen/pruefe_qt_kraftanzeige.py).
Die dort benannten Prüfungen sind ausgeführt; Q misst 100/150/200 %
mittels `QT_SCALE_FACTOR`, keinen physischen Monitorwechsel.

| A-ID | Spezifikation / Abschnitt | U-Schritte | Test / Abnahmekriterium | Status |
|---|---|---|---|---|
| A-V0.11-00001 | 2.1 | 000001, 000014 | Quellen-/Scopeprüfung: keine neue Physik, keine 2D-Erweiterung | Technisch geprüft: Inventar 9.1/9.2, gemeinsame Aufrufpfade 9.13, I; unveränderte Physikbilanz, keine 2D-Erweiterung |
| A-V0.11-00002 | 2.2 | 000002, 000003 | SI/float64, Null-/Fehl-/Ungültigzustände und unveränderte Originalwerte | Technisch geprüft: D, unveränderliche Snapshots und Extremwerte |
| A-V0.11-00003 | 2.3 | 000001, 000004 | Framewechsel, Bezugspunktverschiebung und korrekte Punktbenennung | Technisch geprüft: D/W/I, einschließlich statischem Weltursprungversatz |
| A-V0.11-00004 | 3.1 | 000001, 000003 | Alle tatsächlich gelieferten Quellen und gleichnamigen Instanzen erfasst | Technisch geprüft: I/D, reale drei Boote, Gewicht/Widerstand/Hydrostatik/Hydrodynamik/Added Mass/Fremdkraft und native Rundreise; gleiche Namen bleiben getrennte Instanzen |
| A-V0.11-00005 | 3.2 | 000003 | Eindeutige Primärgruppe, keine künstlichen Gegenkraftbeiträge | Technisch geprüft: D, Register und ausschließlich atomare Summanden |
| A-V0.11-00006 | 3.3 | 000004, 000011 | Algebraische Fälle und reale Bilanzrekonstruktion | Technisch geprüft: D/I, Quader und drei Boote gegen tatsächliche Residuen |
| A-V0.11-00007 | 3.4 | 000004, 000011 | Gewicht genau einmal; keine doppelte Summe oder Added-Mass-Korrektur | Technisch geprüft: D/I, beide Backends und implizite Integratorbilanz |
| A-V0.11-00008 | 3.5 | 000004 | Wirkungslinie plus Restmoment rekonstruiert ursprünglichen Wrench | Technisch geprüft: D, reine/nahezu auslöschende Wrenches |
| A-V0.11-00009 | 4.1 | 000003 | Ein Register, stabile Definitions-/Instanz-IDs | Technisch geprüft: D/I, gleiche Namen, Umordnung und Modellknoten |
| A-V0.11-00010 | 4.2 | 000003 | Bestehende Physikklassen wiederverwendet, keine Parallelphysik | Technisch geprüft: D/I, vorhandene Wrench- und Kraftmodellverträge |
| A-V0.11-00011 | 4.2 | 000003 | Quellen, Ableitungsart und unbekannte Herkunft eindeutig | Technisch geprüft: D/W, unbekannte Quelle bleibt in Bilanz |
| A-V0.11-00012 | 4.3 | 000003, 000010 | Unveränderliche Snapshots, gleiche Sequenz/Kraftpose in 3D/Tabelle; Versatz zur interpolierten Körperszene sichtbar | Technisch geprüft: D/I, Objektidentität und Eingangs- statt Endpose |
| A-V0.11-00013 | 4.3 | 000003, 000010 | Keine Kraftfunktionsaufrufe aus Renderer/Tabellenmodell | Technisch geprüft: I, fehlende Daten melden Fehler statt GUI-Ersatzrechnung |
| A-V0.11-00014 | 4.4 | 000005 | Gemeinsame getrennte Kraft-/Momentenskala | Technisch geprüft: G/I, getrennte feste Referenzen |
| A-V0.11-00015 | 4.5 | 000001, 000003, 000009, 000012 | IDs/Settings migriert, native Pfade und benötigte Helfer erhalten | Technisch geprüft: D/S/I/W, alle registrierten historischen Pfeil-IDs/Felder mit numerischen Wirkungen durch Migration/Neustart; native Verträge erhalten |
| A-V0.11-00016 | 5.1 | 000006 | Richtung, Angriff/Anker, Null und Kurzpfeil geprüft | Technisch geprüft: D/G/I, reale VTK-Netze und Ankergrenzen |
| A-V0.11-00017 | 5.2 | 000006 | 240°-Bogen, Rechte-Hand-Regel, Komponenten und Restmoment | Technisch geprüft: G/I, beide Backends |
| A-V0.11-00018 | 5.3 | 000007 | Senkrechter Hebelarm und reale/äquivalente Punkte | Technisch geprüft: D/G/W/I, Quellen- und Hebelarmdetails |
| A-V0.11-00019 | 5.4 | 000005 | Formeln, Monotonie, null/R/Überlauf und Legendenwerte | Technisch geprüft: G/I, linear/logarithmisch und Extremwerte |
| A-V0.11-00020 | 5.4 | 000005, 000009 | Kein Maßstabswechsel durch Ausblenden; manuelles Neu-Einpassen | Technisch geprüft: G/W/I, Auswahl-/Layer-/APIänderungen |
| A-V0.11-00021 | 5.5 | 000006, 000013 | Bildschirmgrößen bei 100/150/200 % DPI, Sollabweichung höchstens 1 logischer Pixel | Teilnachweis: I/Q, echte projizierte Maße; physischer DPI-/Monitorwechsel offen |
| A-V0.11-00022 | 5.6 | 000003, 000006, 000009 | Registerdefaults und Nutzerüberschreibungen korrekt | Technisch geprüft: S/W/I, einschließlich historischem Hebelarmstil |
| A-V0.11-00023 | 5.7 | 000006 | Raum-/Vordergrundmodus und Verdeckung sichtbar geprüft | Teilnachweis: I, getrennte Renderer und expliziter Fehler statt Rückfall; visuelle Gesamtabnahme offen |
| A-V0.11-00024 | 5.7 | 000007, 000013 | Trefferzone und eindeutige Mehrfachauswahl | Technisch geprüft: G/I/Q, logische Pixel, Mehrfachkandidaten und echte Klicks |
| A-V0.11-00025 | 6.1 | 000008 | Freifliegend/andockbar, schließen/öffnen ohne Duplikate | Technisch geprüft: W/I/Q, Docklayout und wiederholtes Öffnen |
| A-V0.11-00026 | 6.2 | 000008 | Komponenten, Beträge, Einheiten, Punktart, Quelle und Status vorhanden | Technisch geprüft: W, Modellvertrag, Details und Bilanzkarten |
| A-V0.11-00027 | 6.2 | 000005, 000008 | Vier/17 signifikante Stellen, wissenschaftliche Kleinwerte und Lokalisierung | Technisch geprüft: G/W, Kleinwerte und nicht darstellbare Beträge |
| A-V0.11-00028 | 6.3 | 000007, 000008 | Auswahl bidirektional, keine Bilanzänderung | Technisch geprüft: W/I/Q, einschließlich Auswahl vor erstem Render neuer Generation |
| A-V0.11-00029 | 6.4 | 000008 | Mockup-Abstimmung und Inhaltsabgleich | Prinzip am 20.10.2026 bestätigt; technischer Inhaltsabgleich 9.12, menschliche Gesamtabnahme separat |
| A-V0.11-00030 | 7.1 | 000002, 000004, 000011 | Referenzfälle mit rtol=1e-10 / atol=1e-9 | Technisch geprüft: D/I, tatsächliche Solver- und Integratorergebnisse |
| A-V0.11-00031 | 7.2 | 000002, 000010, 000013 | Reset/Pause/Körperwechsel/Generation und verfügbare Backends | I/W und explizite Trigger-/Moduszuordnung 9.13, beide Backends; physischer Monitorwechsel nicht nachgewiesen |
| A-V0.11-00032 | 7.3 | 000002, 000013 | Sichtbare Kamera-, DPI-, Null-, Überlappungs- und Bedienprüfung | Teilnachweis: I/Q und Bildschirmbelege; physische Mehrschirmabnahme offen |
| A-V0.11-00033 | 7.4 | 000002, 000013 | Identische Vorher-/Nachhermessung, Ressourcen, nicht blockierter Worker bei verlangsamter GUI und Leistungsentscheidung | Teilnachweis: 9.4/9.10/9.12/9.13, I/Q, 600-Zyklen-Prozessspeicherproben inklusive nativer Allokationen; akzeptierte Leistungsgrenze fehlt |
| A-V0.11-00034 | 7.5 | 000002, 000014 | 48 belegte Zeilen, tatsächliche Ergebnisse und offene Punkte | Fortgeführt: diese Matrix und Abschnitt 9; Vollabschluss wegen offener Gates nicht erklärt |
| A-V0.11-00035 | 4.6 | 000001, 000012 | Altpfadinventar abgeschlossen, keine produktiven Altaufrufe/Duplikate | Technisch geprüft: 9.2/9.10/9.12/9.13 und I; GUI ohne Ersatzphysik, Demo im gemeinsamen Renderer, historische Hilfsverträge nur in Mess-/Regressionspfaden |
| A-V0.11-00036 | 4.7 | 000006, 000012 | Verfahrenserprobung und begründete einheitliche Werkzeugentscheidung | Technisch belegt: 9.10, wiederverwendete VTK-Netze statt zusätzlichem Renderer |
| A-V0.11-00037 | 4.8 | 000010, 000013 | Identische Snapshots/Settings liefern gleiche Darstellung aller Modi; Bogenphasen mit gleichem Initialzustand | Technisch geprüft: I, vier Moduskontexte, feste Kraft-/Momentenreferenzen und neu initialisierte Bogenbasis; identische VTK-Netzpunkte und Tabellenwerte |
| A-V0.11-00038 | 4.9 | 000001, 000010 | Alle 28 Triggerfamilien und zusätzliche Eingänge mit Modusbelegen | Konkretisiert: 9.13 mit tatsächlichen GUI/API/Import-Belegen und begründeten nicht anwendbaren Eingängen; physischer Monitorwechsel bleibt offen |
| A-V0.11-00039 | 3.6 | 000004, 000008, 000011 | Fehlende aktive Quellen erzeugen Teilsummenstatus statt falscher Gesamtbilanz | Technisch geprüft: D/W/I, fehlend/deaktiviert/null und ungültige Folgeergebnisse |
| A-V0.11-00040 | 3.7 | 000004, 000008, 000011 | Solverbedingungen, Teilfreiheitsgrade und nicht bewertbare Zustände korrekt | Technisch geprüft: D/W/I, reale Stufen einschließlich expliziter Nichtkonvergenz |
| A-V0.11-00041 | 3.8 | 000004, 000005 | Epsilon-/Ankergrenzen, keine Skalenabhängigkeit oder verlorene Kleinwerte | Technisch geprüft: D/G/W, beide Grenzseiten und Extremwerte |
| A-V0.11-00042 | 3.6 | 000001, 000004, 000011 | Überlagerte Modelle sichtbar, keine eigenmächtige Physikkorrektur | Technisch geprüft: I, Hinweis auch bei Nullkraft plus Parameter/Herkunft; fachliche Absicht bleibt ungeklärt |
| A-V0.11-00043 | 4.10 | 000008, 000009 | Einzel-/Mehrkörperauswahl ohne physische Aktivierungsänderung/Systemsumme | Technisch geprüft: W/I, statische Mehrkörperdaten und explizit nicht berechnete Körper |
| A-V0.11-00044 | 5.8 | 000006, 000013 | Stabile Bogenbasis bei Achsenwechsel, Antiparallelität und Null | Technisch geprüft: G/I, Generationcache und Nulldurchgang |
| A-V0.11-00045 | 5.9 | 000007, 000013 | Labelpriorität in dichten Szenen, volle Werte unabhängig verfügbar | Technisch geprüft: I/W, echte Textmaße, kleine Fenster und globale Mehrkörperpriorität |
| A-V0.11-00046 | 6.5 | 000009 | Neustart/Reset/Monitorwechsel und valide Settingsmigration | Teilnachweis: W/S/I, echter Hauptfensterneustart ohne Physikpersistenz; physischer Monitorwechsel offen |
| A-V0.11-00047 | 6.6 | 000010, 000013 | Begrenzte Queue, atomare Ausgabe, letzter Stand bei gestopptem Timer und erhaltene Fehlermeldung bei überholtem Snapshot | Technisch geprüft: I, Statik je Körper letzter Folgeauftrag und global höchstens Poolkapazität gestartet; 100 Importe mit wechselnden Namen; Pause ein laufender plus letzter Bedarf |
| A-V0.11-00048 | 7.6 | 000001, 000002, 000004, 000011 | Gleichzustandsvergleich mit tatsächlicher Solver-/Integratorbilanz | Technisch geprüft: D/I, Quader und drei Boote, Python/C++, Statik/Stationär/Dynamik, Widerstand/Hydrodynamik/Added Mass einschließlich expliziter stationärer Nullbeschleunigung; fachliche Gesamtabnahme separat |

## 6. Entscheidungs- und Nachweisstellen

| Zeitpunkt | Zu entscheiden / nachzuweisen | Umgang bei offener Frage |
|---|---|---|
| Vor Implementierungsbeginn | Freigegebener fachlicher Umfang von Spezifikation und Plan | Keine automatische Umsetzung aus dem Planungsauftrag |
| M1/M2 | Fehlende Diagnosedaten, instabile Quellidentitäten, ungeklärte Modellüberlagerung | Kleinste nötige Vertragsänderung bestimmen; fachliche Änderung mit Nutzer klären |
| M3 | Zeichenverfahren, Bildschirmskalierung und Picking | Mit Versuch/Messung begründen, vorhandenen Stack bevorzugen |
| M4 | Wesentliche Abweichung vom bestätigten Layoutprinzip | Vor produktiver Abweichung abstimmen; reine Qt-Anpassung dokumentieren |
| M5/M6 | Fehlende reale Paritätstoleranzen | Aus bestehendem Fachvertrag belegen oder vor Abnahme festlegen lassen |
| M6 | Messbasierte Taktrate und Leistungsgrenzen/Abweichungen | Messungen vorlegen; ohne geklärte Pflichtkriterien kein Vollabschluss |

## 7. Fortschritt und Protokollpflege

| Schritt | Status | Tatsächlicher Beleg / Ergebnis |
|---|---|---|
| U-V0.11-000001 | Bestandsaufnahme durchgeführt und fortgeschrieben | Quellen-/Altpfadinventar und 28 Triggerzuordnungen in Abschnitt 9; anfängliche Diagnosetransportlücken durch 9.9 und gemeinsame Snapshots bearbeitet; Abschlusszuordnung 9.13 |
| U-V0.11-000002 | Referenzbasis vorbereitet | Bestandsregression, algebraische Tests und reproduzierbare Offscreen-Baselines in Abschnitt 9; historischer Manifestfehler getrennt nachgewiesen |
| U-V0.11-000003 | Technisch umgesetzt und geprüft | Quell-IDs, Originalpunkte und Kraftpose im Python-/C++-/Batchtransport, native Rundreise und unveränderliche Snapshots; Abschnitt 9.9/9.13 |
| U-V0.11-000004 | Technisch umgesetzt und geprüft | Gemeinsamer Adapter, explizite Nullbeiträge, Original-Solverkriterien und reale Statik-/Stationär-/Dynamikparität; Abschnitt 9.13 |
| U-V0.11-000005 | Technisch umgesetzt und geprüft | Linear/log1p, manuelle Referenzen, Neu-Einpassen und Legende; echte GUI-/API-/Stildialogeingaben ohne Physikauftrag; Abschnitt 9.9/9.13 |
| U-V0.11-000006 | Snapshotrenderer erweitert; Teilnachweis | Welt-/Körperkomponenten, Schwerpunkt-/Weltbezug, volle Auswahlmomente, Netzvorlagen mit transformierten Normalen und dunkle Summenkonturen; Abschnitt 9.10; reale Bildschirmabnahme offen |
| U-V0.11-000007 | Technisch umgesetzt und geprüft | P-/A-Marker, Quellenhervorhebung, Wirkungslinie/lotrechter Hebelarm, echte Textabmessungen und Verbindungslinien; globale Mehrkörperpriorität und kleine Fenster geprüft; menschliche Bedienabnahme separat |
| U-V0.11-000008 | Technisch umgesetzt und geprüft | Karten/Details, Körperwahl und Mehrkörperfilter; technischer Mockup-Inhaltsabgleich 9.12, bidirektionale Auswahl und echte Dialog-/Tastatureingaben geprüft |
| U-V0.11-000009 | Optionen und Reset integriert; Teilnachweis | Schema 1.6, alle historischen Pfeilfelder je registrierter Pfeil-ID über Migration/Speichern/Neuladen geprüft; echter Hauptfensterneustart stellt Layout/Stil/Optionen ohne Physikdaten wieder her; physischer Monitorwechsel offen |
| U-V0.11-000010 | Trigger integriert und technische Nachweise erweitert | 28-Familien-Matrix 9.13; reale Statik-/Pause-Änderungen, Importinvalidierung und vollständiger Körperabbau; globale Statikbegrenzung auch bei 100 wechselnden Namen; physischer Monitorwechsel nicht nachgewiesen |
| U-V0.11-000011 | Technisch umgesetzt und geprüft | Native/Python-Diagnosen, Eingangspose, implizite Dynamikbilanz und originale Solverkriterien; drei Bootmodelle mit/ohne Widerstand und Added Mass gegen tatsächliche Statik-/Stationärreste; Nichtkonvergenz ausdrücklich geprüft, 9.13 |
| U-V0.11-000012 | Technisch umgesetzt und geprüft | Separater Vista-Kraftpfeil entfernt; Demo-HUD liest Snapshot, kein redundanter Weltmaßstab, keine GUI-Ersatzphysik; abschließende Aufrufpfadprüfung in 9.13; historische native Hilfsverträge erhalten |
| U-V0.11-000013 | Automatisierte und sichtbare Teilprüfungen erweitert | Reale Windows-Qt-Proben, 600-Zyklen-Läufe mit 60 Körper-/Fensterwechseln und Windows-Prozessspeicher; stabile Actor-/Cachegrößen; physische Monitor-/Bedienabnahme und Leistungsentscheidung offen |
| U-V0.11-000014 | Regression und Nachweismatrix fortgeschrieben; Abschluss blockiert | Gesamtlauf: 1620 bestanden, 1 Skip, 1 bekannter historischer Manifestkonflikt, 150,71 s; 48-A-/14-U-Zuordnung, 438 lokale Dateilinks und Syntax geprüft; Nachweise/Grenzen in 9.13, keine vollständige fachliche Abnahme |

Bei tatsächlicher Ausführung werden pro Schritt und Gate Datum,
Quellstand/Arbeitsbaum, Umgebung, Befehle, Ergebnisse, Skips, Belegverweise,
offene Fehler und Entscheidung ergänzt. Messdaten dürfen unterstützend
separat liegen; der Status und die vollständige Zuordnung verbleiben
in diesem Plan.

Die Statusangaben unterscheiden technische Umsetzung von fachlicher
Nutzerabnahme. Die produktiven Daten-, Darstellungs-, Wertefenster- und
Altpfadablösungen sind integriert; konkrete technische Nachweise stehen
in 9.10–9.13. M3 bis M6 werden damit nicht pauschal geschlossen:
physische Monitor-/Bedienabnahme und die messungsbasierte
Leistungsentscheidung bleiben offen. Die A-Matrix in Abschnitt 5
weist diese Grenzen ausdrücklich aus. Keine menschliche Gesamtabnahme
oder uneingeschränkt grüne Gesamtregression behauptet.

## 8. Nicht umsetzen

Derzeit keine zurückgezogenen U-Schritte. Spätere Rücknahmen werden
unter ihrer ursprünglichen U-ID mit Begründung hier archiviert.

## 9. Ausführung und Belege vom 20.10.2026

### 9.1 Ausgangslage und Quelleninventar — U-V0.11-000001

Branch `main`, Ausgangscommit `682dbe5d41c8a31717ca3c014ff717242156d7c5`.
Bereits vorhandene Änderungen an Instructions, Agenten, VS-Code-Dateien,
V0.8-Dokumentverweisen, Register und V0.11-Planungsunterlagen bleiben
erhalten. Keine Git-Sicherung und keine Änderung dieser historischen
Fachstände als Teil der Anzeigeimplementierung.

| Quelle / Vertrag | Tatsächlicher Befund | Umsetzung / offene Integration |
|---|---|---|
| [Kraftmodell](../../../../code/python/segelphysik/core/kraftmodell.py) | `Kraftbeitrag(name, wrench)` ohne Quellinstanz-ID; `aggregiere_kraftbeitraege` normalisiert alle Beiträge; Gewicht über Merkmal gekennzeichnet | Explizite `Quellbezug`-IDs vom Erzeuger verlangen, keine Listenindizes als Identität; vorhandene Wrench-Funktionen verwenden |
| Hydrostatik / Gewicht | `hydrostatik` und `schwerkraft`; normalisiertes Moment enthält bereits die Bezugspunktverschiebung | Kein zweites Hebelarmmoment; fehlendes Legacy-Gewicht genau einmal als gekennzeichnete Adapterergänzung |
| Widerstand / Hydrodynamik | Allgemeiner 6D-Widerstand und Geometriemodelle können gleichzeitig liefern | Beide erhalten; fachliche Modellüberlagerung je aktivierter Konfiguration vor U000011-Abnahme bewerten |
| [Hydrodynamik](../../../../code/python/segelphysik/core/hydrodynamik.py) | Rumpf/Kiel/Ruder/Volumenkörper; mehrere gleichnamige Beiträge; trockene bzw. wirkungslose Teile können ganz fehlen | Minimaler Transport stabiler Teil-IDs und expliziter Aktiv-/Nullzustände nötig; fehlenden Beitrag nicht ungeprüft als Null werten |
| Originalpunkte | Normalisierung verliert die ursprünglichen Bezugspunkte; Hydrostatik führt K gesondert; verteilte Quellen haben keinen eindeutigen Angriff | Originalpunkt nur bei explizitem Nachweis übernehmen, sonst Wrench bzw. äquivalente Darstellung mit Restmoment |
| [Statischer Solver](../../../../code/python/segelphysik/core/statisch.py) | Residuen für Tauchung und Rollen; Stabilitätsprüfung separat; keine volle 6DOF-Gleichgewichtsaussage | Freiheitsgrade, Toleranzen und Zustand ausdrücklich an Solverbewertung binden |
| [Stationäre Auswertung / GUI](../../../../code/python/segelphysik/gui/hauptfenster.py) | `_stationaere_kraftlage` liefert Lage und Geschwindigkeiten aus Solverstufe | Stufe, Quellenumfang und Bedingungen für gemeinsame Anzeige mitführen |
| [Python-Dynamik](../../../../code/python/segelphysik/core/dynamik_6dof.py) | `schritt` wertet Kraft an Eingangspose aus, gibt Endzustand plus Kraftergebnis zurück; Dämpfung wird teilimplizit behandelt | Kraftpose/-zeit ist nicht automatisch Endpose/-zeit; äquivalente Integratorbilanz separat nachweisen |
| [Nativer Dynamikkern](../../../../code/cpp/src/dynamik.hpp) | Ergebnis kombiniert Endzustand mit an Eingangspose ausgewerteten Kräften; Added Mass ergänzt den Diagnosebeitrag | Kein Python-Rückruf in Batch; Diagnose-/Identitätstransport vor produktiver Anbindung erweitern |
| [Native Ergebnisanbindung](../../../../code/python/segelphysik/core/native_backend.py) | `ergebnis_nach_python` transportiert Namen und normalisierte Wrenches, keine Quellinstanz-ID oder Kraftpose/-zeit | Vertragsänderung erst konkret planen und registrieren; M2 ändert keine C++-Exports |
| Added Mass | `mit_beschleunigung` und nativer Schritt können einen beschleunigungsabhängigen Beitrag ergänzen | Tatsächlich ausgewertete Beschleunigung verwenden; nicht als zusätzliche Dynamikkraft erneut anwenden |

### 9.2 Altpfadinventar — U-V0.11-000001 / später U-V0.11-000012

| Fundstelle | Befund | Ziel |
|---|---|---|
| [GrafikBruecke](../../../../code/python/segelphysik/grafik_bruecke.py), `kraefte_daten_setzen`, `_kraefte_actors` | Eigene Ableitungen aus Masse, g, Hydrostatik und Fremdkraft; Hydrodynamik getrennt behandelt; `rest` addiert Gewicht unabhängig vom Ergebnismerkmal | Durch gemeinsame Snapshots ersetzen, danach produktive Altberechnungen entfernen |
| `_kraefte_actors`, Hydrodynamikzweige | Instanznamen aus Listenindex; äquivalente Kraftdarstellung ohne vollständige Restmomentanzeige; geometrischer Schnitt als Anker | Stabile Quell-ID und vollständige Wrench-Darstellung |
| `_ACTOR_ENDUNG`, `_kraefte_namen`, `_kraefte_actors_entfernen`, `_kraefte_entfernen` | Feste historische Actorlisten und Sonderbehandlung für Hydrodynamik | Gemeinsamer Actorlebenszyklus nach Instanz-ID, keine doppelten Actors |
| `_kraftpfeil_zeichnen`, `_momentbogen_zeichnen`, `_overlay_translation_*`, `_mesh_setzen` | Wiederverwendung und Vordergrundrenderer vorhanden; bisherige Bögen achsenbezogen | Geeignete Ausgabe-/Cachinghelfer weiterverwenden, keine zweite Renderingbasis |
| `_overlays_aktualisieren`, `_layer_aktualisieren`, Pose-/Layer-/Stileinstiege | Kraftanzeige an Körperpose und Layer gebunden | Auf gemeinsamen Darstellungsstand einschließlich Kraftpose umstellen |
| [pfeilstil.py](../../../../code/python/segelphysik/core/pfeilstil.py), `PAARE`, `PFEILE`, `Stil`, Vorlagen | Zentrales Register und persistierte IDs vorhanden; historische Gegenkraft-/Achsenbeschriftung und individuelle Maßstäbe | IDs erhalten, Semantik und Settings in M3/M4 angekündigt migrieren |
| [kraefte_bild.py](../../../../code/python/segelphysik/core/kraefte_bild.py) | Geometrie-/Wrenchhelfer mit nativen Gegenstücken; teilweise auch außerhalb aktueller Anzeige benötigt | Geeignete Funktionen übernehmen; keine pauschale Löschung nativer oder gemeinsam genutzter Helfer |
| [Hauptfenster](../../../../code/python/segelphysik/gui/hauptfenster.py), `_kraftbild_daten_setzen`, `_aktuelles_kraftbild_aktualisieren`, `_statisches_kraftbild_aktualisieren` | Fehlende Ergebnisse teilweise unmittelbar in GUI-Pfaden neu ausgewertet | Kontrollierten fachlichen Aktualisierungsweg mit Invalidierung vorsehen |
| Einstellungenmenü und Layer-Checkboxen | Bedienelemente aus bestehendem Register | Eine Registerpflege erhalten, weiterhin benötigte Optionen migrieren |
| Bestehende Stil-/Geometrie-/GUI-Tests | Ausgangsverhalten geprüft, noch kein Nachweis neuer Darstellung | Fachliche Referenzen erhalten und gezielt erweitern; keine Tests zur Fehlerverdeckung entfernen |

### 9.3 Triggerzuordnung — U-V0.11-000001 / später U-V0.11-000010

Die Nummern entsprechen Spezifikation 4.9. Dies ist das geprüfte
Einstiegsinventar, noch kein Nachweis vollständiger neuer Verdrahtung.
`HF` bezeichnet [hauptfenster.py](../../../../code/python/segelphysik/gui/hauptfenster.py),
`GB` bezeichnet [grafik_bruecke.py](../../../../code/python/segelphysik/grafik_bruecke.py).
Fehlende neue Bedienwege werden nicht als bereits implementiert behauptet.

| Nr. | Vorhandener Eingang / relevante Abhängigkeit | Zielprüfung / Lücke |
|---|---|---|
| 1 | HF `baum_setzen`, `bruecke_setzen`, `_laufzeit_objekte_aktualisieren` | Ersten gültigen Snapshot unabhängig vom Animationstakt publizieren |
| 2 | HF `_laufzeit_objekte_aktualisieren`, `_modellpfad_einstellung_geaendert`; GB `koerper_objekt_setzen` | Generation, Auswahl und Actors invalidieren |
| 3 | [BaumWidget](../../../../code/python/segelphysik/gui/baum_widget.py) `laufzeit_aenderung` → HF `_laufzeit_objekte_aktualisieren` | Physische Aktivierung von Anzeigesichtbarkeit trennen |
| 4 | BaumWidget `_eigenschaft_setzen`, `laufzeit_aenderung("eigenschaft")` | Masse/Material/Geometrie und vorbereitete Caches nachführen |
| 5 | Baum-/Paketgeometrie und Fabrikumbau | Physikalisch wirksame Gelenk-/Teilpose invalidieren; kein separater neuer Gelenkeditor behauptet |
| 6 | HF `_echtzeit_starten`, `_zustand_nach_umbau`; GB `physik_pose_setzen`, `physik_pose_6dof_setzen` | Fachliche Pose von interpolierter Anzeigepose trennen |
| 7 | Kraftmodell-Eingänge `v`, `omega`; Physikparameter Fluidgeschwindigkeit/-rotation | Fachliche Änderung neu auswerten; keinen nicht vorhandenen Liveeditor voraussetzen |
| 8 | Python-/C++-Schritt und `mit_beschleunigung` | Ausgewertete Beschleunigung und Added-Mass-Verfügbarkeit transportieren |
| 9 | HF `_fremdkraft_geaendert`, Fremdkraftfelder und Checkbox | Statik/Pause sofort invalidieren; alte Daten nicht als aktuell zeigen |
| 10 | HF `_ruderwinkel_geaendert`, `_hydrodynamik_testprofil_laden` | Vorhandenes Modell und pausierte/stationäre Auswertung nachführen |
| 11 | Konfigurations-/Physikladen und Körperneuaufbau | g, Dichte und fachlichen Wasserstand getrennt von optischer Wasserbewegung behandeln |
| 12 | HF `_solver_einstellung_geaendert`, `_modellpfad_einstellung_geaendert`; Rechenpfad-/Physikaufbau | Modell-/Backend-/Solveränderungen fachlich invalidieren |
| 13 | HF `_statische_simulation_ausfuehren` | Anzeige vor Auftrag als veraltet/in Berechnung markieren |
| 14 | HF `_statische_aufgabe_fortschritt`, `_statische_aufgabe_abgeschlossen` | Freigegebene Stufen, Fehler und Abbruch unterscheiden |
| 15 | HF `_echtzeit_aufgabe_abgeschlossen` | Kraftzustand mit passender Zeit/Pose/Sequenz publizieren |
| 16 | HF `_modus_geaendert`, `_zeit_pausieren`, `_zeit_fortsetzen`, `_echtzeit_starten` | Moduswechsel, Reset und verspätete Ergebnisse prüfen |
| 17 | HF `_aktuelles_kraftbild_aktualisieren`, `_statisches_kraftbild_aktualisieren` | Fachliche Neuberechnung aus GUI-Zeichenpfaden herauslösen, Timerstillstand prüfen |
| 18 | Neuer Adapter; bislang kein gemeinsamer Frame-/Bezugs-/Komponentenanzeigeschalter | Ableitungsweg und neue Bedienanbindung implementieren |
| 19 | HF `_layer_setzen`; GB `layer_setzen`, `_layer_aktualisieren` | Sichtbarkeit ohne Bilanz-/Referenzänderung aktualisieren |
| 20 | HF `_stil_anwenden`, bestehender Einstellungsdialog | Neue zentrale Skalen-/Neu-einpassen-Optionen und Cacheinvalidierung ergänzen |
| 21 | HF `_stil_anwenden`; GB `stil_setzen` | Farben, Konturen, Linienarten und Vordergrundmodus übernehmen |
| 22 | HF `_kamera_preset_geaendert`; GB Kamera-/Navigations-/Folgekamerapfade | Bildschirmgrößen, Labels und Picking auch ohne neue Physik aktualisieren |
| 23 | Qt-/VTK-Viewport und Dock-/Monitor-/DPI-Ereignisse | Zentrale Resize-/DPI-Anbindung fehlt bislang; gezielt ergänzen |
| 24 | Neuer Auswahlzustand, Picker und Wertefenster | Gemeinsame Auswahl-ID und Quellenhervorhebung implementieren |
| 25 | HF `ansicht_setzen`, `bruecke_setzen`; neues Wertefenster | Wiederöffnung/Rendererneubau ohne Actor-/Signalduplikate |
| 26 | Neue zentrale Formatierung und Werteansicht | Formatiereinstellungen ohne Physikaufruf nachführen |
| 27 | HF `_einstellungen_dialog`, bestehende `geaendert`-Signale | Reset/Anwenden auf tatsächliche fachliche/grafische Abhängigkeiten abbilden |
| 28 | [GUIControlAPI](../../../../code/python/segelphysik/gui/steuer_api.py) nutzt Qt-Setter/-Signale | Dieselben Regeln für GUI und API; weitere direkte Imports/Skripte bei Integration prüfen |

### 9.4 Referenz- und Messbasis — U-V0.11-000002

- Vor produktiven Änderungen: die neun Testdateien aus Abschnitt 4
  (`test_kraftmodell`, `test_frames`, `test_pfeilstil`,
  `test_native_kraftgeometrie`, `test_overlays`, `test_gui_laufzeit_edit`,
  `test_gui_steuerung`, `test_gui_steuer_api`, `test_native_worker`)
  zusammen ausgeführt: **150 bestanden**, 16,82 s, offscreen, Standardpfad C++.
- Expliziter Pythonpfad, dieselben fachlichen/GUI-Dateien ohne die beiden
  ausdrücklich nativen Dateien: **115 bestanden**, 5,63 s, offscreen.
- [Messprogramm](Messungen/baseline_kraftanzeige.py),
  [C++-Rohmessung](Messungen/baseline_cpp_2026-10-20.json) und
  [Python-Rohmessung](Messungen/baseline_python_2026-10-20.json):
  je drei Aufwärmzyklen und 20 Messzyklen; pro Zyklus ein nachgewiesenes
  VTK-Renderereignis; ein Körper, ein bzw. 24 Hydrodynamikbeiträge,
  Anzeige aus/ein. Vollständige Umgebung und Arbeitsbaum in JSON.
- Messumgebung: Python 3.14.8, NumPy 2.5.4, PyVista 0.49.1, VTK 9.7.1,
  AMD64 Family 25 Model 117, Windows, 800 × 600 offscreen.
  Läufe fanden in geteilter Umgebung statt; aus ihren Unterschieden
  wird kein isolierter Python-/C++-Geschwindigkeitsgewinn abgeleitet.

| Pfad | Hydro-Beiträge | Anzeige | Update-Median ms | Zyklus inkl. Render-Median ms | Actoranzahl |
|---|---|---|---|---|---|
| C++ | 1 | aus | 0,144 | 0,229 | 1 |
| C++ | 1 | ein | 2,841 | 3,426 | 7 |
| C++ | 24 | aus | 0,244 | 0,327 | 1 |
| C++ | 24 | ein | 9,036 | 9,732 | 31 |
| Python | 1 | aus | 0,094 | 0,155 | 1 |
| Python | 1 | ein | 2,727 | 3,147 | 7 |
| Python | 24 | aus | 0,160 | 0,232 | 1 |
| Python | 24 | ein | 12,302 | 13,332 | 31 |

Diese Zahlen messen die unveränderte bisherige Anzeige mit identischen
Ergebnissen, keine Solverlaufzeit, sichtbare FPS oder Workerblockierung.
Mehrkörper-, Lifecycle-, Qt- und DPI-Prüfungen bleiben eigene
Integrations-/Abnahmefälle. Sie werden nicht aus dieser Baseline abgeleitet.
Keine neuen verbindlichen Leistungsgrenzen festgelegt.

### 9.5 Implementierte Datenbasis — U-V0.11-000003 / U-V0.11-000004

- [pfeilstil.py](../../../../code/python/segelphysik/core/pfeilstil.py):
  zentrale Quell-/Gruppenzuordnung mit Verweisen auf vorhandene Pfeil-IDs;
  keine Änderung bestehender Settingsdefaults oder produktiver Zeichenpfade.
  Rollenfarben und Anzeigenamen sind inzwischen als Metadaten ergänzt;
  produktive Stil-/Settingsmigration folgt weiterhin in M3/M4.
- [kraefte_anzeige.py](../../../../code/python/segelphysik/core/kraefte_anzeige.py):
  explizite `Quellbezug`-Identitäten, unveränderliche `BeitragsAnzeige`,
  `KraefteAnzeigeSnapshot`, `SolverBewertung` und fachlicher Adapter.
  Fehlende, deaktivierte, ungültige und veraltete Quellen werden
  unterschieden. Gruppen-/Gesamtsummen referenzieren nur atomare Quellen.
- Gewicht wird entsprechend dem Ergebnismerkmal genau einmal
  berücksichtigt; unbekannter Quellenumfang bleibt ungeklärt.
  Ein vollständiger expliziter Quellenumfang muss Gewicht einmal führen.
- Wirkungslinie erhält Restmoment; Kleinwert-, Geometrie-, Überlauf- und
  Zehn-Ausdehnungen-Grenzen führen mit sichtbarem Grund zum gleichen Wrench,
  nicht zu einer alten Darstellung oder einem verlorenen Moment.
- [test_kraefte_anzeige.py](../../../../tests/test_kraefte_anzeige.py):
  algebraische Referenzen, Positivzeichen des äquivalenten Ankers,
  Frame-/Bezugspunktwechsel, stabile gleichnamige Instanzen,
  unveränderliche Daten, Null-/Fehlzustände und Solverstatus.
  Ein analytischer Fall mit echtem Statiksolver sowie eine echte
  Dynamik-Schrittauswertung mit Added Mass ergänzen die isolierten Tests.
  Beide Backendpfade werden parametrisiert ausgeführt.
- Noch **keine produktive Anbindung** dieser Klassen an Worker, Renderer
  oder Wertefenster; kein sichtbarer Wechsel der Anwendung behauptet.
  Insbesondere keine Vergabe von Quellinstanz-IDs aus Listenpositionen.

### 9.6 Regression und offene Hindernisse

Der erste Gesamtlauf nach Einführung der Datenbasis ergab
**1257 bestanden, 1 übersprungen, 1 fehlgeschlagen**. Die neue Änderung
an `pfeilstil.py` berührte die strikte V0.10-Manifestprüfung.
[migration_inventar.py](../../../../werkzeuge/migration_inventar.py) kann
deshalb ausdrücklich benannte spätere Python-Quellen separat als
Folgeentwicklung ausweisen; Originalhashes bleiben unverändert.
Modelle, Konfiguration und unbekannte Referenzquellen werden dadurch
nicht freigegeben. Tests prüfen weiterhin den strikten Standardmodus.

Nach dieser Zuordnung zeigt derselbe historische Manifesttest eine
**bereits am Ausgangscommit vorhandene** Abweichung von
`konfigurationen/settings.json` gegenüber V0.10-Referenzcommit
`7a955c24ceb6c0825e05a574b959dd1176be2e2c`.
Nachweis: Im Manifestaufruf ausschließlich den Hash von `pfeilstil.py`
durch dessen `HEAD`-Hash ersetzt; dann tritt derselbe Settingsfehler auf.
Die Settingsdatei entspricht unverändert `HEAD`, ihr JSON-Inhalt weicht
bereits dort von der alten Referenz ab. Keine Settings zurückgesetzt,
Referenzhashes überschrieben oder Konfigurationsprüfung gelockert.

Damit ist ein grüner Gesamtabschluss derzeit nicht nachgewiesen.
Der historische Referenzkonflikt ist getrennt zu entscheiden; er ist
keine Freigabe zum Ändern vorhandener Nutzerkonfiguration.

Letzter Gesamtlauf am 20.10.2026:
`QT_QPA_PLATFORM=offscreen`, `.\.venv\Scripts\python.exe -m pytest -q`:
**1262 bestanden, 1 übersprungen, 1 fehlgeschlagen**, 52,19 s.
Einziger Fehler: `test_referenzmanifest_umfasst_modelle_konfiguration_und_optik`
wegen des oben belegten historischen Settingskonflikts.
Die neuen Snapshot-/Adapter- und Folgeentwicklungs-Vertragstests
bestanden in diesem Gesamtlauf.
Dokumentlinks, 48-A-/14-U-Abdeckung, Python-Syntax der geänderten/neuen
Module, Messdaten mit je 23 Renderereignissen und `git diff --check`
sind geprüft. Keine C++-Quellen, Modelle oder Settings geändert.

**Nutzerentscheidung am 20.10.2026:** „Altfehler dokumentieren und
V0.11 weiter umsetzen.“ Die Umsetzung wird mit dem ausdrücklich
beibehaltenen historischen Manifestfehler fortgesetzt. Dies ist keine
Freigabe zum Ändern von Settings/Referenzhashes und keine Behauptung
eines grünen Gesamtlaufs oder einer abgeschlossenen Gesamtabnahme.

### 9.7 M3-Rechenbausteine — U-V0.11-000005 bis U-V0.11-000007

[kraefte_darstellung.py](../../../../code/python/segelphysik/core/kraefte_darstellung.py)
enthält die rendererfreien, gemeinsam verwendbaren Bausteine:

- Unveränderliche lineare/logarithmische `SkalenAbbildung`, Referenzinitialisierung,
  ausdrückliches Neu-Einpassen und tatsächlich abgebildete Legendenwerte.
  Extremwerte werden ohne überlaufende Betrag/Referenz-Division behandelt;
  Null bleibt null, Kleinwerte werden markiert, Referenzen nicht nachgeregelt.
- Deutsch formatierte kompakte Werte mit vier und Detailwerte mit bis
  zu 17 signifikanten Stellen; Datenzustände erscheinen als Text.
- `KameraAbbildung` berücksichtigt logische Pixel, vertikalen/horizontalen
  Blickwinkel, Perspektive, Parallelkamera und Ankertiefe.
- `BogenVerlauf` verwendet den vorhandenen Python-/C++-Bogenkern als
  gemeinsamen Geometriebaustein, rotiert dessen 240°-Bogen auf beliebige
  Momentenrichtungen und führt eine kontinuierliche Startphasenbasis.
  Vorzeichenwechsel erhält den Startpunkt soweit möglich; Null erzeugt
  keinen Bogen, neue Generation löscht alte Basis, verspätete Generation
  wird abgewiesen.
- Senkrechter Hebelarm statt bloßem Punktabstand; Abstand zum projizierten
  Linienzug für eine in logischen Pixeln prüfbare Picking-Zone.

[test_kraefte_darstellung.py](../../../../tests/test_kraefte_darstellung.py)
prüft Formeln, extreme Referenzen, Zahlenzustände, Kamera/DPI-Umrechnung,
Rechte-Hand-Regel, Bogenwinkel, Achsenbewegung, Vorzeichenwechsel, Null,
Generation und Pixelabstand in Python-/C++-Konfiguration.
Gemeinsamer gezielter Lauf mit `test_kraefte_anzeige.py`,
`test_native_kraftgeometrie.py` und `test_pfeilstil.py`:
**194 bestanden**, 6,96 s, offscreen.

Dies ist noch kein sichtbarer Kamera-/DPI-Nachweis der produktiven GUI.
Skalen-/Stiloptionen, Actors, Labels und Picker werden erst bei Integration
an diese Bausteine angeschlossen. Die endgültige Werkzeugentscheidung
benötigt weiterhin den begrenzten sichtbaren Versuch nach U000006;
kein Glyph-Verfahren und keine zusätzliche Grafikbibliothek eingeführt.

Gesamtlauf nach M3-Rechenbausteinen und verschärften
Unveränderlichkeitsprüfungen:
`QT_QPA_PLATFORM=offscreen`, `.\.venv\Scripts\python.exe -m pytest -q`:
**1310 bestanden, 1 übersprungen, 1 fehlgeschlagen**, 58,96 s.
Einziger Fehler ist weiterhin der ausdrücklich dokumentierte und zur
Fortsetzung akzeptierte historische Settings-Manifestkonflikt.
Keine neuen Testfehler. 48-A-/14-U-Zuordnung, zyklenfreie Abhängigkeiten,
Dokumentlinks, Python-Syntax und `git diff --check` erneut geprüft.

**Nächster offener Integrationspunkt:** U000006-Verfahrensversuch und
Actor-/Stilanbindung, danach U000007-Picker/Labels und produktive
M4-Wertefensteranbindung.
Vor U000010-Produktivanbindung müssen stabile Quellinstanz-IDs,
Originalpunkt-Provenienz und Kraftpose/-zeit minimal über die
vorhandenen Ergebnisverträge transportiert werden. Die Bestandsaufnahme
hat hierfür `HydrodynamikTeil.name` beziehungsweise Modellknotenidentität
als zu prüfende Quelle identifiziert; Gleichnamigkeit darf nicht durch
Listenindizes kaschiert werden. Native Vertragsänderungen sind noch
nicht implementiert oder registriert, weil die konkrete Vertragsform
noch festzulegen ist. Kein M3-, M4-, M5- oder M6-Abschluss behauptet.

### 9.8 Vorgezogener Qt-Wertebaustein — U-V0.11-000008

Das freigegebene Mockup-Prinzip ist im
[Qt-Wertebaustein](../../../../code/python/segelphysik/gui/kraefte_werte.py)
vorbereitet: `QDockWidget`, `QTreeView` und `QAbstractItemModel`, keine
HTML-Einbettung. Die Datenzeilen halten Referenzen auf denselben
unveränderlichen Snapshot beziehungsweise dessen Beiträge, keine
zweite physikalische Datenliste und keine Neuberechnung von Kräften,
Momenten oder Summen.

- Körperzweige, Gruppensummen und atomare Beiträge; keine
  körperübergreifende physikalische Gesamtsumme.
- Komponenten und Beträge mit vier signifikanten Stellen,
  SI-/Präfixeinheiten, Frame, Momentenbezug und bestätigter Punktart.
  Details mit bis zu 17 signifikanten Stellen, Quellen-IDs und der
  allgemeinen Beziehung `M(P) = M(A) + (A - P) x F`; kein ungeprüftes
  Weglassen eines direkten Quellenmoments.
- Herkunfts-/Statusanzeige unterscheidet Null, fehlend und nicht
  berechnet. Teilsummen und nicht bewertbares Gleichgewicht werden
  ausdrücklich bezeichnet. Ein aus endlichen Komponenten nicht mehr
  darstellbarer Betrag wird als solcher benannt, nicht als Null.
- Auswahl- und Sichtbarkeitssignale verwenden dieselben stabilen IDs.
  Externe Auswahl löst keine Rückkopplung aus. Checkboxen ändern keine
  Snapshotdaten und keine Bilanz.
- Auswahl und Baumzustand bleiben bei gleichartiger Aktualisierung
  erhalten; Generationswechsel verwirft die Beitragsauswahl.
  Körperentfernung/Reset räumt alte IDs und Sichtbarkeitszustände.
  Schließen und Wiederöffnen erhält den aktuellen Stand.
- Lesbare Anzeigenamen, Gruppenbezeichnungen, Rollenfarben und
  neue Standard-Sichtbarkeiten liegen im bestehenden zentralen
  Beitragsregister; historische `PFEILE`-/Settings-IDs bleiben
  unverändert. Noch keine produktive Layout-/Settingsmigration.

Die
[Qt-Tests](../../../../tests/test_kraefte_werte.py)
prüfen beide Rechenpfade einschließlich echter Qt-Tastaturbetätigung
der Checkbox, Auswahl-/Signalverhalten, Mehrkörpertrennung,
Null-/Klein-/Extremwerten, Generationen und Fenster-Lifecycle.
Gezielter Lauf zusammen mit Anzeige-, Darstellungs-, Stil-,
nativen Geometrie-, Grafikbrücken- und bestehenden GUI-Tests:
**246 bestanden**, 7,69 s, `QT_QPA_PLATFORM=offscreen`.

[Qt-Aufnahme mit synthetischen Daten](Messungen/wertefenster_cpp_2026-10-20.png):
echtes Qt-Widget bei 1700 × 850 Pixeln, C++-Pfad, ausdrücklich
gekennzeichneter Teststand. Die Offscreen-Plattform meldet keine
Systemschriftfamilien; für diese Aufnahme wurde vorhandenes
`C:\Windows\Fonts\segoeui.ttf` mit `QFontDatabase.addApplicationFont`
geladen. Keine Schriftdatei kopiert und keine neue Abhängigkeit
installiert. Die zuerst erzeugte unlesbare Aufnahme wurde ersetzt
und die lesbare Aufnahme geprüft.

Dies ist eine unabhängige Vorbereitung, kein Überspringen des
U000007-/M3-Integrationsgates: Auswahlvertrag und Modell/View sind
isoliert geprüft, aber noch nicht an Hauptfenster, Worker, Picker
oder Settings angeschlossen. Keine sichtbare End-to-End-, DPI-,
Monitorwechsel-, Leistungs- oder Nutzerabnahme behauptet.

Gesamtregression nach Qt-Baustein und Registermetadaten:
`.\.venv\Scripts\python.exe -m pytest -q`,
`QT_QPA_PLATFORM=offscreen`: **1340 bestanden, 1 übersprungen,
1 fehlgeschlagen**, 62,64 s. Weiterhin ausschließlich der historische
Settings-Manifestkonflikt aus Abschnitt 9.6; keine neuen Fehler.
48-A-/14-U-Rückverfolgbarkeit, Abhängigkeitsgraph, lokale
Dokumentlinks, Python-Syntax und Whitespace erneut erfolgreich geprüft.

### 9.9 Produktive Snapshotintegration und Settings

**Entwicklungsmodus:** Der Nutzer beauftragt die vollständige Umsetzung,
ausdrücklich ohne Release und dauerhaft im Entwicklungsmodus. Keine
Commits, Tags, Pushes oder Veröffentlichungen als Teil dieses Pakets.

**Implementierte Verbindungen:**

- [Kraftmodell](../../../../code/python/segelphysik/core/kraftmodell.py),
  [Körper](../../../../code/python/segelphysik/core/koerper.py),
  [Hydrodynamik](../../../../code/python/segelphysik/core/hydrodynamik.py)
  und [nativer Adapter](../../../../code/python/segelphysik/core/native_backend.py)
  erhalten Quellinstanzen, bestätigte Originalpunkte und die tatsächliche
  Kraftpose. Nachträglich vom Modellfabrikpfad zugeordnete Knoten-IDs
  bestimmen ebenfalls die Quell-ID. Gleichnamige Teile bleiben getrennt.
  Erfolgreich ausgewertete aktive trockene Teile liefern explizite
  Nullbeiträge; ungeprüft fehlende Daten werden nicht pauschal zu null.
- Der native Batch transportiert die letzte **Eingangspose**, nicht
  fälschlich den akzeptierten Endzustand als Kraftauswertungsort.
  Added-Mass-Diagnosen behalten IDs/Pose und werden nicht nochmals als
  Integrationskraft angewendet.
- [Snapshotrenderer](../../../../code/python/segelphysik/grafik_kraefte.py)
  und [Wertefenster](../../../../code/python/segelphysik/gui/kraefte_werte.py)
  erhalten aus dem [Hauptfenster](../../../../code/python/segelphysik/gui/hauptfenster.py)
  dieselbe unveränderliche Snapshotobjektreferenz.
  Der [Qt-Klickfilter](../../../../code/python/segelphysik/gui/kraefte_auswahl.py)
  verbindet 3D-Auswahl, Mehrfachtreffermenü und Tabelle.
- Die alte große Kraft-/Momentenableitung im Renderer wurde ersetzt.
  Kraft- und freie Momentenmeshes benutzen die gemeinsame
  [Grafikbrücken-Ausgabe](../../../../code/python/segelphysik/grafik_bruecke.py)
  und ihre Actor-/Translationscaches. Der alte breite Linienfallback
  für fehlgeschlagene Momentenmeshes wurde entfernt.
- Neue Snapshots werden auch ohne Pose-/Kameraänderung beim nächsten
  Renderauftrag ausgegeben. Statische Neuberechnung und fachliche
  Eingabeänderungen entfernen ungültig gewordene Daten sofort mit
  Statushinweis. Initialisierte Referenzen bleiben bei reiner fachlicher
  Neuberechnung erhalten; tatsächlicher Körperabbau räumt sie auf.
- Reine Stiländerungen starten keine neue Physikauswertung. Ein
  stationärer/statischer Abschluss transportiert seine finale
  Kraftauswertung aus dem Worker. Python und C++ liefern die
  ursprünglichen robusten Statikresiduen/-grenzen einschließlich
  Rollscan. Stationäre Stufen führen tatsächliche normierte Kriterien,
  Freiheitsgrade und Konvergenzentscheid mit.
- Schema 1.6 ergänzt Skalen, Bildschirmmaße, Rollenfarben, stabile
  Sichtbarkeit und geprüftes Fenster-/Spaltenlayout. Nicht erreichbare
  Monitorpositionen werden korrigiert. Automatische Referenzen, Kräfte,
  Auswahl und Sequenzen werden nicht als neue Einstellungsfelder
  gespeichert. Anwendungstests nutzen isolierte temporäre Settings.
- Gleiche Tabellenstruktur/generation aktualisiert bestehende
  Modellknoten mit `dataChanged`, statt alle Tabellenzeilen je
  Snapshot zurückzusetzen. Labels, Verbindungslinien, Pickgeometrie,
  Actors und Caches werden beim Daten-/Körperabbau bereinigt.

**Konkrete Teilnachweise (keine Gesamtabnahme):**

| A-IDs / Themen | Tests |
|---|---|
| A00002–00011, A00030, A00039–00042: Daten, Quellen, Summen, Gewicht, Wirkungslinie und Status | [Anzeigeadaptertests](../../../../tests/test_kraefte_anzeige.py), [Integration](../../../../tests/test_kraefte_integration.py) |
| A00012–00014, A00019–00022, A00037, A00044: gemeinsamer Stand, Skalen, Farben, Kamera/Bögen | [Darstellung](../../../../tests/test_kraefte_darstellung.py), [Integration](../../../../tests/test_kraefte_integration.py), [Settings](../../../../tests/test_einstellungen.py) |
| A00016–00018, A00023–00028, A00045–00046: Geometrie, Picking, Qt, Persistenz | [Kräfte](../../../../tests/test_kraefte.py), [Stil](../../../../tests/test_pfeilstil.py), [Wertefenster](../../../../tests/test_kraefte_werte.py), [Integration](../../../../tests/test_kraefte_integration.py) |
| A00031, A00038, A00047–00048: Worker, Eingangspose, Integratorbilanz und Solverdiagnose | [Integration](../../../../tests/test_kraefte_integration.py), [native Statik](../../../../tests/test_native_statik.py), [stationäre Stufen](../../../../tests/test_stationaer_hydrodynamik.py), [GUI/Worker](../../../../tests/test_gui_laufzeit_edit.py) |
| A00001, A00015, A00029, A00032–00036, A00043: Umfang, Altoptionen/-pfade, Mockup, reale Sichtbarkeit/Leistung, Mehrkörperbedienung | Vorhandene Bestands-/Bausteinbelege reichen nicht zum Abschluss; Restarbeiten unten |

`A000nn` bezeichnet hier unverändert `A-V0.11-000nn`.
Die DPI-Prüfung verwendet echte VTK-Projektion mit simulierten Faktoren
1/1,5/2 und beiden Kameramodi: Kopfprojektion höchstens ein logischer
Pixel vom Soll, Schaftmaß anhand der tatsächlich erzeugten Pfeilgeometrie.
Das ist **keine** tatsächliche Monitor-/DPI- oder sichtbare Bedienabnahme.
Die Dynamikparität rekonstruiert aus den tatsächlichen
Geschwindigkeitsänderungen die zum Anzeigewrench äquivalente Gleichung,
einschließlich impliziter Dämpfung, Added Mass und Coriolistermen;
Testgrenzen `atol=1e-9`, `rtol=1e-9`. Eine bloße Gegenprüfung der
Anzeigesumme gegen sich selbst ersetzt diesen Nachweis nicht.

**Build und Regression:**

- Erneuter nativer Build:
  `.\.venv\Scripts\python.exe -m pip install -e . --no-deps` erfolgreich,
  einschließlich der neuen robusten Solverdiagnosen.
- Abschließender Gesamtlauf dieses Pakets:
  `QT_QPA_PLATFORM=offscreen`,
  `.\.venv\Scripts\python.exe -m pytest -q`:
  **1386 bestanden, 1 übersprungen, 1 fehlgeschlagen**, 59,94 s.
- Ausschließlich der in Abschnitt 9.6 freigegebene historische
  Settings-Manifestkonflikt bleibt fehlgeschlagen. Die neuen Änderungen
  an `pfeilstil.py` und `einstellungen.py` sind ausdrücklich als spätere
  Python-Folgeentwicklungen benannt; keine Freigabe von Konfigurationshashes.
- Das historische V0.10-Startinventar bleibt unverändert. Der Live-Test
  verlangt weiterhin alle 271 spezifizierten Funktionen; 296 statt
  298 Einträge entstehen ausschließlich durch die zwei entfernten
  internen Altzeichen-Closures. Stabile Identitäten werden gegen das
  historische Inventar geprüft, nicht dessen veraltete Quellpositionen.
- Anschließende gezielte Nachprüfung der Layer-/Nullmarkerbereinigung:
  `test_kraefte_integration.py`, `test_kraefte.py`, `test_pfeilstil.py`,
  `test_benchmark_profil.py`, `test_grafik_bruecke_darstellung.py`,
  `test_grafik_optimierung.py`: **132 bestanden**, 4,48 s. Auch bei
  vollständig abgeschalteten Kraft-/Momentenlayern bleiben weder
  Nullmarker noch Labels oder Picklinien stehen.
- 375 lokale Links der drei aktualisierten Dokumente, alle 48 A-/14 U-IDs,
  Syntax der 12 berührten produktiven Pythonmodule und
  `git diff --check` geprüft. Keine Änderung der Nutzerkonfiguration
  zur Behebung des historischen Manifestfehlers.

**Noch nicht vollständig umgesetzt bzw. abgenommen:**

1. Gesamt-/Komponentendarstellung mit eindeutigem Welt-/Körperframe,
   vollständige Hervorhebung von Momentenquellen und Moment um P bei
   ausgewählter Einzelkraft; Restmoment allein ersetzt diese Ansicht nicht.
2. Vollständige explizite Migration aller historischen Größen-, Skalen-,
   Linien- und Komponentenoptionen; konsistente Checkbox-/Stildefaults,
   Legendenhinweise auf individuelle Faktoren und erreichbare Resetbedienung.
3. Ausdrücklicher Mehrkörper-Anzeigeschalter unabhängig von der physischen
   Aktivierung; vollständiger bestätigter Mockup-Inhaltsabgleich.
4. Vollständige End-to-End-Matrix aller 28 Triggerfamilien, einschließlich
   überholter Aufgaben, Frame-/Bezugswechsel, Monitor-/Rendererneuerzeugung
   und vorhandener Steuer-API-/Importwege; Pose-/Zeitversatz zur
   interpolierten Körperszene sichtbar erläutern.
5. Reale Modell-/Modusparität einschließlich Koordinatenzuordnung der
   statischen/stationären Auswertung und sämtlicher aktiver
   Widerstands-/Hydromodelle; komplette Altaufrufer-/Demo-/Fallbackprüfung.
6. Tatsächliche sichtbare Qt-/VTK-/DPI-/Überlagerungs-/Bedienprüfung,
   identische Vorher-/Nachhermessungen, Speicher-/Queue-/Workerbelege
   und ausdrücklich messungsbasierte Leistungsentscheidung.
7. Abschließende 48-A-Abnahme und Projektlog erst nach den Pflichtnachweisen.
   Keine offenen Anforderungen still zurückziehen oder als erledigt erklären.

### 9.10 Anzeigeoptionen, Netzvorlagen und Nachhermessungen

Fortsetzung nach dem erneuten Auftrag, sämtliche U-Schritte vollständig
umzusetzen. Die Liste am Ende von 9.9 beschreibt den damaligen Stand;
der folgende Abschnitt ersetzt deren Fortschrittsbewertung, nicht die
Anforderungen. Weiterhin Entwicklungsmodus ohne Commit, Tag oder Push.

**Zusätzlich implementiert:**

- Gemeinsamer `anzeige_wrench` für Welt-/Körperkomponenten und
  Schwerpunkt-/Weltursprungsbezug; Originalsnapshots bleiben unverändert.
  Die tatsächliche statische XY-Szenenzuordnung wird separat transportiert,
  ohne die Solverpose umzudeuten.
- Das Wertefenster bietet Körperwahl, expliziten Mehrkörperfilter und
  Momentenkomponenten. Die Auswahl ändert keine physische Aktivierung.
  Karten enthalten Komponenten; Details erläutern Hebelarmmoment und
  direktes Quellenmoment. Frame, Bezug, Kraftpose/-zeit und mögliche
  Interpolation der Körperszene sind kenntlich.
- Auswahl zeigt den vollen Moment um P, Quellenmarkierung, P-/A-Marker,
  Wirkungslinie und senkrechten Hebelarm. Optionale Komponentenbögen
  verwenden den gewählten Frame.
- Neue und historische Stile/Sichtbarkeiten werden gemeinsam abgeglichen.
  Relative Altgrößen sind in der
  [Settingsdokumentation](../../../Vorlagen/Settings.md) beschrieben.
  Der erreichbare Anzeige-Reset bewahrt Layout und Physikparameter.
- Resize-/Show-/Screen-/DPI-Ereignisse verwenden gebündelte Redraws.
  Bridgewechsel und Schließen entfernen alte FrameSwap-Verbindungen,
  Auswahlfilter, Kameraobserver, Actors und Anzeigecaches.
- Der zusätzliche Kraftpfeil in
  [Vista](../../../../code/python/segelphysik/render/vista.py) ist entfernt;
  dessen Geschwindigkeitspfeil bleibt bestehen.
  Das [Demo-HUD](../../../../code/python/segelphysik/demo_app.py)
  formatiert die vorhandene Snapshotbilanz statt einer alten separaten
  Auftriebs-/Momenteninterpretation.
- Summen besitzen eine dunkle kamerabezogene VTK-Silhouette.
  Raum-/Vordergrundebene, Kameramodus, Translation und Abbau bleiben
  konsistent. Fehler beim verlangten Vordergrundmodus werden explizit
  gemeldet, nicht still durch einen anderen Darstellungsmodus ersetzt.
- Labels verwenden tatsächliche VTK-Textabmessungen statt angenommener
  280-Pixel-Rechtecke. Bei Platzmangel werden sie ausgeblendet; Tabelle,
  Snapshot und Pickgeometrie bleiben verfügbar. Verbindungslinien sind
  einfarbig und enden am nächstgelegenen Labelrand.
- Solide Pfeile verwenden eine einmalige Schaft-/Kopfnetzvorlage.
  Pro Formänderung werden Punkte und inverse-transponiert transformierte
  Normalen aktualisiert, nicht Tube-/Conefilter je Pfeil neu aufgebaut.
  Kopf-/Schaftmaße werden an den tatsächlichen Mappernetzen für kurze
  und lange Pfeile sowie vier Richtungen geprüft. Das Originalnetz
  wird nicht verändert; beim Anzeigeende wird die Vorlage freigegeben.
- Das Restmoment einer äquivalenten Wirkungslinie wird stabil als
  Parallelprojektion auf F berechnet. Subtraktive Rundungsreste eines
  reinen Hebelarmmoments erzeugen keine zusätzlichen Marker mehr.

**Automatisierte Belege:**

Die ergänzten Tests liegen in
[Anzeigeadapter](../../../../tests/test_kraefte_anzeige.py),
[Darstellung](../../../../tests/test_kraefte_darstellung.py),
[Wertefenster](../../../../tests/test_kraefte_werte.py),
[Integration](../../../../tests/test_kraefte_integration.py),
[Stil](../../../../tests/test_pfeilstil.py) und den bestehenden
Kraft-/Benchmark-/Referenzpfadtests. Sie belegen insbesondere reale
GUI-Options-/API-Änderungen ohne Solveraufruf, Reset/Persistenz,
Bridge-/Signalabbau, Anzeigekörperfilter, Szenenversatz, volle
Auswahlmomente, Netzmaße/Normalen, kamerabezogene Konturen und
überschneidungsfreie Labels im geprüften Ein-Körper-Fall.

Gezielter zusammengefasster Lauf der neun betroffenen Anzeige-/
Referenzpfaddateien: **369 bestanden**, 10,23 s. Danach wurden noch
einfarbige Labelverbindungen und der explizite Restmoment-Regressionstest
ergänzt; deren Abschlussnachweis erfolgt im Gesamtlauf unten.
Ein vorangegangener Gesamtlauf ergab **1436 bestanden, 1 Skip,
1 Manifestfehler**. Die neu geänderte Demo-Datei ist inzwischen ausdrücklich
als Python-Folgeentwicklung benannt, genau wie Einstellungen und Stil.
Der historische Hash und die strikte Behandlung von Modell-/
Konfigurationsdateien bleiben erhalten; gezielte Nachprüfung meldet
wieder ausschließlich den bekannten Konflikt in `konfigurationen/settings.json`.

Abschließender Gesamtlauf des hier dokumentierten Codestands:
`QT_QPA_PLATFORM=offscreen`,
`.\.venv\Scripts\python.exe -m pytest -q`:
**1444 bestanden, 1 übersprungen, 1 fehlgeschlagen**, 78,58 s.
Der einzige Fehler ist unverändert
`test_referenzmanifest_umfasst_modelle_konfiguration_und_optik` wegen
`konfigurationen/settings.json`. Keine neue Fehlerfreigabe,
kein Entfernen oder Umdefinieren dieses Tests.
Zusätzlich: `git diff --check`, Syntax der elf unmittelbar betroffenen
Pythonmodule/Messdateien, 390 lokale Dokumentlinks und unverändert
48 A-/14 U-Kennungen geprüft.

**Bildbelege:**

- [Produktives Wertefenster](Messungen/wertefenster_produktiv.png)
- [Dazugehörige 3D-Auswahl](Messungen/auswahl_produktiv.png)

Beide Aufnahmen wurden über die produktive Snapshotanbindung erzeugt
und als Bilder geprüft; Nutzersettings waren dafür isoliert.
Dies sind Offscreen-Teilbelege, keine tatsächliche Monitor-/DPI- oder
Bedienabnahme.

**Nachhermessung und nachgewiesene Einschränkung:**

Das vorhandene
[Messprogramm](Messungen/baseline_kraftanzeige.py) verwendet dieselben
physikalischen Baselinevektoren und dieselbe Kamera, additive explizite
Quellmetadaten und die vorher sichtbaren Einzelbeiträge. Neue Gruppen
und Labels sind ausgeschaltet. Zusätzlich variiert `--veraenderlich`
die hydrodynamischen Vektoren pro Zyklus; die Ergebnisvorbereitung
liegt außerhalb des Updateintervalls. Je Fall drei Aufwärm- und
20 Messzyklen, `tracemalloc`, tatsächliche Renderereignisse und
Prozessspeicher. Eigene Messläufe wurden nacheinander ausgeführt.

| Rechenpfad / 24 Hydro-Beiträge, Anzeige an | Update-Median | Update + Render-Median | Actors | Rohdaten |
|---|---|---|---|---|
| C++, identischer Redraw | 4,792 ms | 6,418 ms | 55 | [JSON](Messungen/snapshot_cpp_kontrast_redraw_2026-10-20.json) |
| Python, identischer Redraw | 5,582 ms | 7,335 ms | 55 | [JSON](Messungen/snapshot_python_kontrast_redraw_2026-10-20.json) |
| C++, wechselnde Kräfte | 55,896 ms | 62,240 ms | 59 | [JSON](Messungen/snapshot_cpp_kontrast_wechsel_2026-10-20.json) |
| Python, wechselnde Kräfte | 54,265 ms | 61,560 ms | 59 | [JSON](Messungen/snapshot_python_kontrast_wechsel_2026-10-20.json) |

Zwischenstände sind nicht überschrieben: zunächst etwa 135–137 ms bei
identischem Redraw, danach Marker-/Zustandscaches; wechselnde Kräfte
zunächst 120–126 ms, dann Arrow-Quellversuch etwa 83–85 ms, anschließend
Netzvorlage etwa 51 ms ohne die ergänzte Konturarbeit. Die endgültigen
Werte oben enthalten die Konturen. Die zusätzlichen Actors im wechselnden
Fall sind stabile Überbereichsmarker mit Konturen; keine steigende
Actorzahl im Messintervall.

Identischer Redraw ist kein Dynamiknachweis. Die Messungen sind reine
Renderer-/Adapterteilpfade unter Speicherinstrumentierung, ohne
Qt-Tabelle oder Worker; sie sind weder isolierte C++-Kernzeiten noch
garantierte sichtbare Frameraten. Eine akzeptierte Leistungsgrenze ist
weiterhin nicht festgelegt.

### 9.11 Mehrkörper-, Worker- und sichtbare Qt-Nachweise fortgeführt

Zusätzlich zu 9.10 wurden die zuletzt offenen Integrationspunkte für
U-V0.11-000010/U-V0.11-000011/U-V0.11-000013 erweitert:

- Pausierte Initial-/Folgeauswertung nutzt nun den vorhandenen
  `_EchtzeitAufgabe`-Worker mit `anzahl_schritte=0`. Damit werden
  Kraftbilder bei pausierter Dynamik ohne synchrone GUI-Kraftrechnung
  erzeugt; Generation/Sequenz verwerfen überholte Nullschrittaufträge.
- `_EchtzeitAufgabe.run` meldet auch Fehler aus
  `aktualisieren`/`ruderwinkel_setzen` explizit zurück und liefert bei
  Nullschritt entweder ein Ergebnis oder einen klaren Fehler statt
  stiller Anzeige-Reste.
- Historische Stiloptionen `pfeil_hebelarm` (Farbe/Deckkraft/Sichtbarkeit/
  Vordergrund) wirken jetzt auch im gemeinsamen Snapshotrenderer.
  Die Geometrie nutzt dieselben Strich-/Lückenmaße wie der Stilbereich,
  keine hardcodierten 8/5-Pixelsegmente.
- Reale Modellbelege ergänzt:
  - Anzeigebilanz des impliziten Integrators jetzt zusätzlich mit den
    realen Modellpaketen `optimist`, `folkeboot`, `yacht1` verifiziert
    (beide Rechenpfade).
  - Statische und stationäre Restwrenches werden für die verfügbaren
    Solverstufen gegen die Snapshotbilanz verglichen; nicht konvergente
    Solverabbrüche bleiben explizit als solche erhalten.
- Sichtbare Qt-/VTK-Abnahme erweitert:
  [pruefe_qt_kraftanzeige.py](Messungen/pruefe_qt_kraftanzeige.py)
  führt echte Windowsfenster mit isolierten Einstellungen aus, prüft
  3D↔Tabelle-Auswahlklick, Kamerawechsel, Wiederöffnen ohne neue
  Physikauswertung und pixelnahe Kopf-/Schaftmaße bei
  `QT_SCALE_FACTOR=1/1.5/2`.
  Belege:
  [bildschirm_100.png](Messungen/bildschirm_100.png),
  [bildschirm_150.png](Messungen/bildschirm_150.png),
  [bildschirm_200.png](Messungen/bildschirm_200.png)
  sowie die zugehörigen JSON-Metadaten (`*_100.json`, `*_150.json`,
  `*_200.json`).

**Aktuelle Testläufe dieses Folgestands:**

- Betroffene Anzeige-/GUI-/Worker-/Modelltests:
  **318 bestanden**, 27,79 s.
- Gesamtsuite (`QT_QPA_PLATFORM=offscreen`):
  **1484 bestanden, 1 übersprungen, 1 fehlgeschlagen**, 87,45 s.
  Der einzige Fehler bleibt unverändert
  `test_referenzmanifest_umfasst_modelle_konfiguration_und_optik`
  wegen `konfigurationen/settings.json`.

**Weiter offen, nicht als bloße Abnahmeformalität umdeuten:**

Diese Liste dokumentiert den damaligen Stand nach 1484 bestandenen Tests.
Die nachfolgenden Abschnitte 9.12 und 9.13 führen die tatsächlich
nachgeholten Nachweise und die noch bestehenden Grenzen fort.

1. Die Statik wertet inzwischen alle sichtbaren Laufzeitkörper aus;
   Mehrkörperlabels priorisieren Auswahl und Bilanz global. Die
   Dynamik integriert weiterhin ihren bisherigen Hauptkörper.
   Andere Körper erscheinen ohne Snapshot ausdrücklich als
   nicht berechnet; keine zusätzliche GUI-Physik oder erfundene
   Systemsumme durch Umschalten des Anzeigefilters.
2. Vollständige reale Modell-/Modus-/28-Trigger-Matrix, einschließlich
   Import/API, überholter Aufgaben, Modellüberlagerung und atomarer
   Ausgabe bei verlangsamter GUI.
3. Historische Pfeilfelder, Hauptfensterneustart, technischer
   Mockup-Inhaltsabgleich und globale Mehrkörper-Labelpriorität sind
   inzwischen geprüft; physische Mehrschirm- und menschliche
   Darstellungsabnahme bleiben davon getrennt.
4. Vollständige Altbestands-/Vertragsabschlussprüfung: Nicht mehr
   produktiv zeichnende numerische Hilfen bleiben für historische
   Messungen und native Verträge erhalten; Exporte werden nicht
   ungeprüft gelöscht.
5. Physische Monitorwechsel-/Mehrschirmabnahme und vollständige
   Ressourcen-/Queue-Langläufe unter Last sowie messungsbasierte
   Leistungsentscheidung.
6. Abschließende 48-A-Abnahme und Projektlog. M3–M6 und sämtliche
   davon abhängigen Abschlussgates bleiben offen.

### 9.12 Queuebegrenzung, Generationen, Modellhinweise und Neustart

**Implementierung und konkrete Regressionen:**

- Statikaufträge werden je Körper gebündelt: höchstens ein gestarteter
  Auftrag und ein gespeicherter letzter Folgeauftrag. 100 Änderungen
  am Betrag sowie Azimut, Elevation, alle drei Angriffspunktfelder und
  Ruderänderung über die echte Steuer-API starten nicht 100 Worker.
  Moduswechsel und Schließen verwerfen den ausstehenden Folgeauftrag.
  Fehler des überholten gestarteten Auftrags bleiben im Protokoll.
- Der pausierte Nullschrittworker verarbeitet dieselben GUI/API-Felder.
  Eine künstlich blockierte Kraftfunktion erhält bei mehr als 50
  Änderungen genau zwei Aufrufe, beide außerhalb des GUI-Threads.
  Der zweite Snapshot enthält den letzten Kraftvektor, Angriffspunkt,
  sein Kreuzproduktmoment und den letzten Ruderwinkel; Körperzustand,
  Integrationszeit und Verlauf bleiben unverändert.
- `KraefteZeichner.generation_setzen` wird schon bei der Annahme eines
  Snapshots aufgerufen. Eine danach gewählte Quelle bleibt beim ersten
  Rendern dieser Generation ausgewählt. Regression über drei Generationen,
  statt das Problem durch vorgeschaltetes Rendern im Test zu umgehen.
- Ein fehlendes dynamisches Kraftergebnis gilt ausdrücklich als Fehler.
  Alte Actors, Tabelle und Snapshot werden invalidiert; keine Zeit wird
  als erfolgreich integriert fortgeschrieben. Auch fehlender Körper und
  ungültiger Zustand verwerfen alte Kraftanzeigen ausdrücklich.
- Der Hauptfenster-Anzeigepfad wertet fehlende Ergebnisse nicht mehr
  synchron aus. Die bisherigen Nachberechnungen in statischen/
  stationären Callbacks und der alternative Weltmaßskalenrückfall sind
  entfernt. Fehlende Workerdaten bzw. eine ungeeignete Grafikbrücke
  werden protokolliert. Das gemeinsame Neuzeichnen verwendet ausschließlich
  vorhandene Snapshots.
- Auch die Demo berechnet und speichert keinen ungenutzten alten
  Kraftweltmaßstab mehr. Ihr kompatibler Dateneingang führt in denselben
  Snapshotrenderer; das nur aus Kompatibilität erhaltene Argument `skala`
  hat keinen Einfluss auf Geometrie oder Referenzen. Native öffentliche
  Hilfsverträge werden nicht pauschal gelöscht.
- Gleichzeitiger allgemeiner linearer/quadratischer Widerstand und
  geometriebezogene Hydrodynamik erzeugen einen ausdrücklichen
  Überlagerungshinweis im Snapshot, Kopf- und Detailtext. Er enthält die
  vorhandenen 6D-Widerstandsparameter und kennzeichnet die fachliche Absicht
  als ungeklärt. Der Hinweis bleibt bei momentaner Nullkraft erhalten;
  beide tatsächlich berechneten Summanden bleiben unverändert erhalten.
- Echte Baumänderungen an Material, Dichte, Wanddicke, Seglermasse und
  allen drei Seglerpositionen sind in Statik und pausierter Dynamik
  über den realen Neuaufbau bis zum neuen Snapshot geprüft. Echte
  Baumcheckboxen prüfen zusätzlich Blattdeaktivierung und Modellwechsel.
  Snapshotgeneration, Gewicht bzw. Schwerpunkt sowie identische Daten
  für Grafik und Wertefenster werden kontrolliert, ohne laufenden Timer.
  Seglereinstellungen liegen ausschließlich in der temporären Testdatei.
- Neustart mit zwei tatsächlichen Hauptfensterinstanzen stellt
  Spaltenbreite/-reihenfolge, erreichbare Geometrie, Stil, Referenz,
  Sichtbarkeit und Anzeigeoptionen wieder her. Kräfte, Auswahl,
  Solver-/Dynamikzustand und Snapshots werden nicht wiederhergestellt.
  Ein gefundener Fehler ist behoben: Anzeigeoptionen wurden zuvor erst
  beim Anschluss einer 3D-Brücke übernommen.
- Alle registrierten historischen Pfeil-IDs werden mit sämtlichen
  individuellen Feldern und globalen Größen durch Settingsschema 1.0,
  Migration, Speicherung und erneutes Laden geprüft. Die erwarteten
  Kopf-/Schaft-/Strich-/Lückenmaße und Skalenfaktoren werden numerisch
  kontrolliert; nicht nur die gespeicherten Schlüssel verglichen.

**Technischer Inhaltsabgleich mit Spezifikation 6.4:**

| Prinzipbereich | Produktive Umsetzung / Beleg |
|---|---|
| Kopf und Aktualität | `KraefteWerteModell.kopftext`, explizite Invalidierung; Frame, Zeit, Generation, Sequenz, Bezug und Versatz |
| Bilanzkarten | Gesamt-F/Gesamt-M mit Komponenten und Beträgen; vollständige/teilweise/nicht bewertbare Bilanzzustände in Wertemodelltests |
| Hierarchie und Summen | `QAbstractItemModel` für Körper/Gruppen/Quellen, eindeutige IDs und nur atomare Summanden |
| Sichtbarkeit | Qt-Checkboxen und echte APIanbindung; physikalische Bilanz und Referenzen bleiben unverändert |
| Details | Quelle, Status, Originalangriff, Bezug, senkrechter Hebelarm, Hebelarmmoment und direktes Quellenmoment |
| Erläuterung | Gemeinsame Skalenlegende mit Modus/Referenzen und Hinweisen; kein zweiter HTML-Renderer |
| Fehlende Daten | Textstatus statt erfundener Nullkraft; fehlende Körper, unvollständige Bilanz und ungültige Folgeergebnisse separat getestet |

Dies ist ein Inhaltsabgleich, keine nachträglich behauptete menschliche
Abnahme oder pixelgenaue Nachbildung des HTML-Mockups.

**Erneute reale Windows-Qt-Prüfung:**

Bei jeder Skalierung zusätzlich 60 wechselnde Snapshotupdates, davon
12 Aufwärmzyklen, und sechs Wiederöffnungen. Je Fall bleiben Actor-,
Label-, Verbindungslinien- und Pickbestände nach dem Aufwärmen exakt
gleich groß; pro Körper bleibt genau ein aktueller Snapshot/Skalenstand.
Alle drei Läufe liefern 73 echte `frameSwapped`-Signale und vier
bestandene Kopf-/Schaftmessungen (Perspektive/Parallel, je zwei Zoomstufen).

| Logische Skalierung | Messzyklen nach Aufwärmen | Kraft-/Hilfsactors je Fall | Python-Speicher, erster → letzter Messpunkt |
|---|---|---|---|
| 100 % | 48 | 14 oder 16, fallabhängig stabil | 103896 → 209340 Byte |
| 150 % | 48 | 14 oder 16, fallabhängig stabil | 101899 → 211457 Byte |
| 200 % | 48 | 14 oder 16, fallabhängig stabil | 101683 → 211685 Byte |

Rohdaten:
[100 %](Messungen/bildschirm_100.json),
[150 %](Messungen/bildschirm_150.json),
[200 %](Messungen/bildschirm_200.json).
Der Speicher enthält unter anderem die wachsende Liste aufgezeichneter
Messpunkte; die Zahlen beweisen weder Speicherleckfreiheit noch einen
nativen Langlauf. Gemessene Zykluszeiten enthalten Qt-Events und GC und
werden nicht als reine Rendererzeiten oder zugesicherte Framerate
ausgegeben. Physischer Monitorwechsel und die Leistungsentscheidung
gemäß Spezifikation 7.4 sind damit nicht ersetzt.

**Verifikation dieses Folgestands:** Der Gesamtlauf vor der letzten
Baum-/Stil-/Altpfaderweiterung ergab **1510 bestanden, 1 übersprungen,
1 bekannter Settings-Manifestfehler**, 85,71 s. Historische Teststände in
9.10/9.11 bleiben als tatsächlich damals ausgeführte Läufe erhalten.
Der Altfehler wird weder durch Entfernen des Tests noch durch pauschale
Freigabe der veränderten persönlichen Settings verdeckt.

### 9.13 Trigger-, Import- und Modellabschlussnachweise

**Umsetzungsschritte:** U-V0.11-000009, U-V0.11-000010,
U-V0.11-000011, U-V0.11-000012, U-V0.11-000013, U-V0.11-000014.
Die historischen Inventare 9.1–9.3 bleiben als Eingangsbefund erhalten.
Diese Fortschreibung dokumentiert tatsächliche zusätzliche Arbeit;
sie ist keine Änderung der Anforderungen und keine Nutzerabnahme.

**Behobene Import- und Lebenszyklusfehler:**

- `HauptFenster.baum_setzen` löst bei bereits angeschlossener Brücke den
  zentralen Laufzeitneuaufbau aus. Ein Weltimport lädt nicht mehr nur
  den Baum und lässt alte Kräfte als aktuell stehen.
- Entfernte Weltkörper werden durch `GrafikBruecke.koerper_entfernen`
  einschließlich Modell, Actors, Overlays, Snapshot, Generationen und
  Caches entfernt. Das Hauptfenster bereinigt Laufzeit-, Schwerpunkt-,
  Statik-, Quellen- und ausstehende Auftragsdaten. Die Weltnamen werden
  getrennt von den gerade sichtbaren Laufzeitkörpern verfolgt; damit
  werden auch vor dem Import bereits ausgeblendete Körper entfernt.
- Statikaufträge werden nun zusätzlich körperübergreifend begrenzt:
  höchstens `max(1, QThreadPool.maxThreadCount())` bereits gestartete
  Aufträge, entsprechend der Qt-Mindestkapazität auch bei null bzw.
  negativem konfiguriertem Wert. Separate Queuefälle prüfen -1/0/1/2
  und die zuverlässige Weiterverarbeitung aller aktuellen Körper.
  Wartende Aufträge liegen ausschließlich in der kontrollierten
  aktuellen Generation, mit dem letzten Bedarf je aktuellem Körper.
  Ein frei gewordener Slot startet auch nach Entfernung des alten
  Körpers einen aktuellen Auftrag für einen anderen Namen.
  Es wird kein laufender QRunnable gewaltsam entfernt.
- Der Importtest führt 100 aufeinanderfolgende Weltimporte mit jeweils
  neuem Körpernamen aus, bei zwei kontrollierten Statikslots bzw.
  einem laufenden Pausenworker. Höchstens zwei Statikaufträge bzw.
  ein Pausenauftrag sind gestartet, höchstens ein aktueller Körper
  wartet; einschließlich des abschließenden aktuellen Auftrags werden
  höchstens drei Aufträge ausgeführt. Der letzte Snapshot wird für
  Tabelle und 3D identisch übernommen. Auch ein zuvor ausgeblendeter
  Körper wird aus der Grafikregistry entfernt.

**Nachweismatrix der 28 Triggerfamilien aus Spezifikation 4.9:**

`I` bezeichnet die
[produktiven Integrationstests](../../../../tests/test_kraefte_integration.py),
`W` die [Wertefenstertests](../../../../tests/test_kraefte_werte.py),
`S` die [Stiltests](../../../../tests/test_pfeilstil.py),
`D` die [Anzeigedatentests](../../../../tests/test_kraefte_anzeige.py)
und `Q` die realen Windows-Qt-Läufe aus 9.12.
Die autouse-Parametrisierung von I führt die Fälle mit Python und C++ aus.
Statik/Pause bezeichnet echte Neuaufträge bei gestopptem Laufzeittimer,
nicht nur eine neue Zeichnung alter Kräfte.

| Nr. | Tatsächlicher Nachweis / Eingang | Modus und Grenze |
|---|---|---|
| 1 | I: `konfigurationsimport...`, erster realer Modellaufbau bis zum gemeinsamen Snapshot | Statik und Pause, ohne Animationstakt |
| 2 | I: `koerperwechsel` und `importserie`, Modell-/Paketfabrikwechsel, Anzeigekörperumfang | Statik/Pause; 100 neue Namen, alte und zuvor ausgeblendete Modelle entfernt; Anzeigeauswahl verändert keine Physik |
| 3 | I: `reale_baumeigenschaft...`, echte Blatt-/Modellcheckboxen | Statik/Pause; höhere Generation, tatsächliche neue Masse bzw. neuer Körper |
| 4 | I: Material, Dichte, Wanddicke, Seglermasse und drei Seglerpositionsfelder; unabhängige Quaderabmessungs-/Dichtefälle | Statik/Pause für vorhandene Baumfelder; Quaderbilanz zusätzlich im realen Statikworker |
| 5 | Modell-/Fabrikumbau wie 2–4; bestehende Gelenkverträge in `test_modell_lader.py` und `test_native_grafikgeometrie.py` | Der vorhandene `GrafikBruecke.gelenkwinkel_setzen` ist ausdrücklich grafisch: Körpervertrag hält Masse und Auftriebsmesh fest. Physischer Ruderwinkel über 10. Kein weiterer physischer Gelenkeditor vorhanden |
| 6 | I/D: Kraft-Eingangspose statt Integrator-Endpose, reale Solverpose/-stufen und statischer Szenenversatz; Schwerpunktumbau in `reale_baumeigenschaft...` | Dynamik/Pause und statische/stationäre Solverwege; Grafikpose/Interpolation ist kein zusätzlicher physischer Poseeingang |
| 7 | I: reale Integratorbilanz mit v/omega und Fluidbewegung; Konfigurationsimport mit Fluidtranslation/-rotation | Dynamik und Statik/Pause; kein separater Live-Fluideditor vorhanden |
| 8 | I: `fremdangriff...`, `anzeigebilanz...` und Import von Added Mass | Dynamik mit tatsächlicher Beschleunigung; Statik/Stationär explizite Nullbeschleunigung, Pause ohne Diagnose bleibt ausdrücklich Teilsumme |
| 9 | I: `statische_aenderungsserien...` und `pausierte_kraftauswertung...` über echte GUI-/API-Setter | Betrag, Azimut, Elevation, x/y/z und Aktivierung; Statik/Pause, letzter Bedarf gewinnt |
| 10 | Dieselben Serien mit echtem Ruderfeld, reale hydrodynamische Modelle und Profil-/Fabrikneuaufbau | Statik/Pause; physischer Modellwinkel, kein Ersatz durch grafische Gelenkpose |
| 11 | I: echte Konfigurationsimporte für g und Wasserdichte; unabhängige Quadergleichgewichte | Statik/Pause; optische Wasseranimation ist kein geänderter physischer Wasserstand |
| 12 | I: Widerstand/Added Mass/Fluidimport, echte Paketfabrik- und Solverdialogänderungen | Statik/Pause und beide Rechenpfade; rein statische Solverparameter lösen in Pause keinen sachfremden Solver aus |
| 13 | I: echte Statik-/Stationäraufträge und Serien | Alte Snapshots und Actors sofort invalidiert; Folgeauftrag kontrolliert |
| 14 | I: reale konvergierte und nicht konvergierte Stationärstufen, Fehler-/Generationsserien | Nur freigegebene Daten; überholte Fehler protokolliert; keine erfundene Konvergenz |
| 15 | I: Dynamik-Eingangspose, native Batchsequenz, identische Snapshotreferenz; fehlendes Folgeergebnis | Dynamik und Nullschritt; fehlende Daten löschen alte Anzeige, Zeit nicht fälschlich fortgeschrieben |
| 16 | I: Moduswechsel-/Schließenserien, API-Reset und identische Snapshots in vier Moduskontexten | Statik, Stationär, Pause, Dynamik; veraltete Antworten werden nicht übernommen |
| 17 | I: reale Baum-/Fremdkraft-/Ruder-/Importänderungen bei gestopptem Timer | Statik/Pause; ausdrücklich echte Kraft-/Solveraufträge außerhalb des Zeichenpfads |
| 18 | I/W/D: echte API-/Qt-Optionen für Frame, Bezug, Komponenten und Auswahlmoment | Statik/Pause, Originalsnapshot unverändert und kein Physikauftrag |
| 19 | I/W: Layer, Quellcheckboxen, Optionen, Mehrkörperfilter, historischer Hebelarmstil | Statik/Pause; Nullmarker/Labels ebenfalls verborgen, Bilanz und feste Referenzen unverändert |
| 20 | I: Skalen/Neu-Einpassen und 22 echte Stildialogfelder; S: sämtliche historischen Pfeilfelder | Statik/Pause; Actorgeometrie/Legende aus denselben Daten erneuert, ohne Worker |
| 21 | I: echte Stildialogfelder, reale Actorfarbe/Deckkraft/Labels und Konturen; Q | Statik/Pause; Raum-/Vordergrundfehler explizit statt stiller Ersatzdarstellung |
| 22 | I: echte VTK-Projektion, Kamera-/Konturänderung und Perspektive/Parallel; Q | Aus demselben Snapshot, ohne Kraftauswertung; Größenabweichung höchstens ein logischer Pixel |
| 23 | I: gebündelte Resize-/DPI-Ereignisse, kleine Viewports und Labelkollisionen; Q bei 100/150/200 % | Technische Ereignis-/Skalierungsprüfung; physischer Mehrschirm-/Monitorwechsel weiterhin offen |
| 24 | I/W/Q: VTK-Mehrfachtreffer, Qt-Auswahl in beide Richtungen, Auswahl vor erstem Rendern neuer Generation | Gemeinsame Quell-ID, Details und Hervorhebung; keine Bilanzänderung |
| 25 | I/W: Brückenwechsel, Schließen/Wiederöffnen, Hauptfensterneustart; Q: sechs Wiederöffnungen je Skalierung | Keine doppelten Verbindungen/Actors; Physik und temporäre Auswahl nicht persistiert |
| 26 | D/W: zentrale Vier-/17-Stellenformatierung, SI-Einheiten und wissenschaftliche Kleinwerte; I: gleiche Tabellenwerte in vier Modi | Derzeit keine veränderbare Einheiten-/Präzisionseinstellung vorhanden; kein neuer Editor aus einem bedingten Trigger abgeleitet |
| 27 | I/W/S: echte Dialoge, Anzeige-Reset, Migration/Neustart und neue Konfiguration | Fachliche Änderungen neu berechnet, reine Anzeigestile ohne Physikauftrag |
| 28 | I: Steuer-API, echte Qt-Dialog-/Baumsignale, Konfigurationsimport bis zum Snapshot | Zentraler Neuaufbau statt nur widgetgebundener Aktualisierung; direkte interne Modellmutation ohne bestehenden Bedienvertrag ist kein neu erfundener Eingabeweg |

Die Matrix ist ausdrücklich nicht begrenzend. Sie behauptet keine
physische Monitorprüfung und keine vollständige kartesische Kombination
jeder beliebigen Konfiguration. Nicht vorhandene Editoren werden weder
als implementiert noch als fehlgeschlagener Test aufgeführt.

**Reale Solver-/Integratorparität:**

- Drei reale Bootmodelle (Optimist, Folkeboot, Yacht1) werden in Statik
  und stationären Teilstufen jeweils mit und ohne zusätzliche lineare/
  quadratische Widerstandsparameter und Added Mass geprüft, in Python
  und C++. Die letzten tatsächlich gelieferten Residuen werden verglichen,
  auch bei ausdrücklicher Stationär-Nichtkonvergenz.
- Im stationären Zustand wird wie im produktiven Worker eine explizite
  Nullbeschleunigung verwendet. Der vorhandene Added-Mass-Beitrag ist
  dann gültig null; er wird nicht als zweite Kraft in die Gleichung
  eingerechnet. Die Pause ohne Beschleunigungsdiagnose bleibt dagegen
  als Teilsumme erkennbar.
- Die dynamische Matrix prüft dieselben drei Boote und einen algebraischen
  Referenzkörper mit Gewicht, Fremdkraft, linearem/quadratischem Widerstand,
  Fluidbewegung und Added Mass. Verglichen wird die zum tatsächlichen
  teilimpliziten Integratorschritt äquivalente Bilanz einschließlich
  körperfester Coriolisterme, nicht eine inkompatible äußere Kraftsumme.
- Unabhängige Quaderfälle variieren Dichte, Abmessungen, Wasserdichte, g
  und vertikale Fremdkraft; der reale Statikworker wird gegen die
  analytische Eintauchtiefe geprüft.
- Reale Residuenvergleiche verwenden `atol=1e-8`, `rtol=1e-9`;
  der dynamische Integratorvergleich `atol=1e-9`, `rtol=1e-9`.
  Dies sind technische Gleichzustandsregressionen, keine neuen
  Konvergenzschwellen. Algebraische Verträge bleiben bei den strengeren
  Grenzen aus Spezifikation 7.1. Fachliche Freigabe dieser realen
  Vergleichsgrenzen bleibt Teil der Gesamtabnahme.

**Abschlussprüfung der alten Aufrufpfade:**

Gezielte Aufrufsuche in `code/python` und `werkzeuge` bestätigt:
Nur die Demo verwendet noch `kraefte_daten_setzen`; dieser kompatible
Eingang erzeugt einen gemeinsamen Snapshot und ignoriert ausdrücklich
das historische Weltmaßstabsargument. `pfeil_daten`, `kraft_pfeile`
und `zusatz_pfeile` besitzen keine produktiven GUI-/Demo-Zeichenaufrufe
mehr; historische Aufrufe verbleiben in `migration_produktiv.py`.
`text_zeile` ist kein produktiver numerischer Anzeigepfad mehr.
Native Exporte und historische Regressionen bleiben erhalten; keine
pauschale Stilllegung und keine neue CPPI-Kennung.

**Erweiterte reale Prozessspeicher-/Ressourcenprüfung:**

Das bestehende
[Qt-Prüfskript](Messungen/pruefe_qt_kraftanzeige.py) besitzt zusätzlich
`--wechsel`; mit 600 Zyklen werden je Skalierung 60 Körperersetzungen
und 60 Fensterwiederöffnungen geprüft. Nach zwölf Aufwärmzyklen
entstehen je 588 Messpunkte. `K32GetProcessMemoryInfo` erfasst
private belegte Bytes und Working Set des gesamten Prozesses,
einschließlich Python, VTK und nativer Allokationen. Ein API-Fehler
wird als Windowsfehler gemeldet, nicht als Nullmessung ausgegeben.

| DPR | Echte Frames | Private Bytes, erster → letzter Messpunkt | Working Set, erster → letzter Messpunkt | Kraft-/Hilfsactors |
|---|---|---|---|---|
| 1,0 | 614 | 933543936 → 908648448 | 563806208 → 554598400 | je Fall konstant 9 bzw. 11 |
| 1,5 | 612 | 1057050624 → 1021853696 | 659087360 → 636502016 | je Fall konstant 9 bzw. 11 |
| 2,0 | 614 | 1223245824 → 1158623232 | 808349696 → 756568064 | je Fall konstant 9 bzw. 11 |

Labels/Verbindungslinien bleiben je Fall bei 1/1, Pickbestände bei
3 bzw. 4, Haupt-Renderer bei 7 Actors; pro Körper genau ein aktueller
Snapshot, Generationseintrag und Skalenstand. Gegenüber 9.12 entfällt
nach dem ersten Körperersatz die temporäre Auswahlhervorhebung.
Die vollständigen Bestände bleiben danach je Fall exakt stabil.
Die vier Kopf-/Schaftmessungen je Skalierung bestehen weiterhin.

Rohbelege:
[100 %](Messungen/langlauf_100.json),
[150 %](Messungen/langlauf_150.json),
[200 %](Messungen/langlauf_200.json);
Wertefenster und 3D:
[100 % Werte](Messungen/langlauf_100.png) /
[3D](Messungen/langlauf_100_vtk.png),
[150 % Werte](Messungen/langlauf_150.png) /
[3D](Messungen/langlauf_150_vtk.png),
[200 % Werte](Messungen/langlauf_200.png) /
[3D](Messungen/langlauf_200_vtk.png).

Beispielbefehl, die beiden weiteren Läufe mit `QT_SCALE_FACTOR=1.5`
und `2` sowie passendem Belegnamen:

```powershell
$env:QT_QPA_PLATFORM='windows'
$env:QT_SCALE_FACTOR='1'
.\.venv\Scripts\python.exe doc\WegZuV1.0\Revisionslog\zuV0.11\Messungen\pruefe_qt_kraftanzeige.py --abbildung doc\WegZuV1.0\Revisionslog\zuV0.11\Messungen\langlauf_100.png --wechsel 600
```

Der Prozessspeicher sinkt zwischen erstem und letztem Messpunkt.
Der instrumentierte Python-Speicher steigt von ungefähr 0,33 auf
0,83 MiB; unter anderem wächst die gespeicherte Messpunktliste.
Weder die sinkenden Prozesswerte noch stabile Actorzahlen beweisen
unbegrenzte Leckfreiheit. Die instrumentierten Zyklusmediane
172,511/183,620/199,103 ms enthalten Qt-Events, GC und
Körper-/Fensterwechsel und sind keine garantierten Rendererzeiten
oder akzeptierten Leistungsgrenzen.

**Verbleibende Abschlussgrenzen:**

1. Physische Monitor-/Mehrschirmprüfung und menschliche sichtbare
   Bedien-/Darstellungsabnahme sind mit den verfügbaren isolierten
   Qt-/VTK-Prüfungen nicht ersetzbar. Die zusätzliche Abfrage mit
   unverändertem physischem Qt-Skalierungsfaktor meldet genau einen
   verfügbaren Bildschirm (3440 × 1440 logische Pixel, DPR 1,
   96 logische DPI). Ein tatsächlicher Wechsel auf einen zweiten
   Monitor ist in dieser Umgebung daher nicht ausführbar.
2. Die vorhandenen Vorher-/Nachhermessungen und Ressourcenproben sind
   keine Nutzerentscheidung über zulässige Verschlechterungen.
   Spezifikation 7.4 verlangt diese Entscheidung ausdrücklich.
   Begrenzte Actor-/Cacheproben und Python-Speichermessungen sind
   außerdem kein Nachweis nativer Langzeit-Leckfreiheit.
3. Der bekannte V0.10-Referenzmanifestfehler bleibt unverändert sichtbar.
   Die persönliche Settingsdatei wird nicht zur Erzeugung eines grünen
   Gesamtlaufs umgeschrieben.
4. Ohne diese Pflichtfreigaben weder M6 noch die 48-A-Gesamtabnahme
   schließen und keinen abschließenden Projektlogeintrag als abgenommen
   erzeugen. Keine Anforderungen ins Backlog verschoben.

**Letzte ausgeführte Gesamtverifikation dieses Arbeitsstands:**

Der Test `langsame_gui_blockiert_worker_nicht_und_haelt_auftragszahl_begrenzt`
prüft zusätzlich ausdrücklich das geöffnete und das geschlossene
Wertefenster in beiden Rechenpfaden. Der Worker beendet seinen Auftrag,
während die GUI absichtlich keine Ereignisse verarbeitet; 50 weitere
Taktaufrufe erzeugen keinen zweiten Auftrag. Nach Freigabe der GUI
erhalten Tabelle und 3D denselben Snapshot. Der Öffnungszustand und
das ursprüngliche GUI-Timerintervall bleiben unverändert.
Gezielt **4 bestanden**, 2,52 s mit `QT_QPA_PLATFORM=offscreen`;
zusätzlich **4 bestanden**, 2,08 s mit echten Windows-Qt-Fenstern
(`QT_QPA_PLATFORM=windows`). Beide Läufe schließen ihre Fenster selbst.

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

Ergebnis: **1620 bestanden, 1 übersprungen, 1 fehlgeschlagen,
150,71 s**. Ausschließlich der bereits bekannte Test
`tests/test_migration_v010.py::test_referenzmanifest_umfasst_modelle_konfiguration_und_optik`
schlägt wegen der vom historischen Sicherungscommit abweichenden
persönlichen `konfigurationen/settings.json` fehl. Keine neue
Integrationsregression im Gesamtlauf; keine Behauptung einer grünen
Gesamtsuite.

Zusätzlich geprüft: 48 aktive eindeutige A-Kennungen, genau 14
eindeutige U-Schritte mit vollständiger A-Zuordnung, azyklische
Abhängigkeiten, 438 vorhandene lokale Dateilinkziele in Spezifikation,
Plan, Settingsdokumentation und Schnittstellenregister sowie Syntax
und fehlende nachlaufende Leerzeichen in 13 betroffenen Pythondateien.
`git diff --check` ist erfolgreich; Git meldet lediglich die bestehende
LF/CRLF-Hinweismeldung zu `tests/test_kraefte.py`. Die vier eigenen
temporären Toolausgabedateien wurden gezielt entfernt.

Bis zur nachfolgenden ausdrücklichen Tagessicherungsfreigabe blieb der
Arbeitsstand uncommittiert auf `main`. Keine Änderungen an persönlichen
Settings zur Verschleierung des Altfehlers.

### 9.14 Ausdrückliche Ausnahme für die Tagessicherung am 20.10.2026

Der Nutzer hat um 22:18 Uhr ausdrücklich freigegeben:
„du darfst den Stand heute ohne weitere Tests comiten, tagen pushen.
dokumentiere die Abweichung vorher“.

- Diese einmalige Ausnahme gilt für die heutige Sicherung per Commit,
  annotiertem Versionstag und Push auf `main`. Es werden keine weiteren
  Tests gestartet. Der unmittelbar zuvor angestoßene Vor-Commit-Aufruf
  wurde unterbrochen und ist kein zusätzlicher bestandener Testlauf.
- Abweichung von der normalen Commit-Sperre: Der letzte vollständig
  ausgeführte Gesamtlauf bleibt bei 1620 bestandenen Tests, einem Skip
  und einem bekannten historischen Settings-Manifestfehler (150,71 s).
  Der Fehler wird weder behoben behauptet noch durch Hashänderung,
  Testentfernung oder eine neue pauschale Fehlerfreigabe verdeckt.
- Die Sicherung ist keine fachliche Abnahme, keine Leistungsfreigabe
  und kein GitHub-Release. Die in 9.13 dokumentierten Abnahmegrenzen
  bleiben unverändert offen; die Entwicklungsarbeit wird morgen fortgesetzt.
- Unabhängige Themen werden getrennt committet. Der gesperrte
  Ideenordner wird weder gelesen noch in die Sicherung aufgenommen;
  dort verbleibende unversionierte Inhalte bleiben lokal erhalten.
