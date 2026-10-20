# Spezifikation V0.11: Kraft- und Momentendarstellung

**Stand:** 20.10.2026  
**Status:** Umsetzung am 20.10.2026 beauftragt; fachliche Abnahme offen; keine Releasefreigabe  
**Geltungsbereich:** Darstellung vorhandener Kraft- und Momentenbeiträge in 3D und in einer gruppierten Werteübersicht  
**Maßgebliche Spezifikation für V0.11:** diese Datei

## 1. Zweck, Quellen und Abgrenzung

Die Darstellung soll verständlich zeigen, welche bekannten Kräfte auf einen
Körper wirken, woher seine Momente stammen und wie Einzelbeiträge die
Gesamtbilanz bilden. Physikalische Daten und visuelle Skalierung bleiben
streng getrennt.

Grundlagen sind die
[Idee](BeispielSpecPfeile.md), die
[kritische Bewertung mit Nutzerkommentaren](Bewertung_Idee_Kraft_und_Momentendarstellung.md)
und der vorhandene Code. Die beiden Diskussionsdokumente sind keine
zusätzlichen normativen Spezifikationen. Ihre Kennungen bleiben historische
Quellverweise und werden nicht umnummeriert.

Diese Datei enthält genau eine gemeinsame Spezifikation. Der zugehörige
[Umsetzungsplan V0.11](Umsetzungsplan_V0.11.md) ordnet die Anforderungen
Arbeitsschritten, Meilensteinen und Nachweisen zu. Die
[Arbeitsanweisung Releaseumsetzung](../../../../.github/instructions/releaseumsetzung.instructions.md)
und die
[Nummerierungs-Instruction](../../../../.github/instructions/nummerierung.instructions.md)
gelten ergänzend. Die nachfolgenden A-Kennungen sind dauerhaft.

### Aktive Anforderungen nach Kennung

Die Abschnitte 2 bis 7 konkretisieren die folgenden Anforderungen. Alle
Anforderungen sind zunächst **offen**; Entwurfsentscheidungen sind keine
Behauptung einer bereits erfolgten Umsetzung oder Nutzerabnahme.
Die in Abschnitt 6.4 dokumentierte Bestätigung des Mockup-Prinzips ist
ein gesonderter Teilnachweis für A-V0.11-00029, keine produktive GUI-Abnahme.

| Kennung | Gegenstand | Abnahmekriterium / Verweis |
|---|---|---|
| A-V0.11-00001 | Umfang auf bekannte Physik und 3D begrenzen | Keine neuen Kraftgesetze, erfundenen Beiträge oder 2D-Diagramme; Abschnitt 2.1 |
| A-V0.11-00002 | Einheitliche Einheiten und Zahlenzustände | SI, float64, Null und fehlende/ungültige Daten unterscheidbar; Abschnitt 2.2 |
| A-V0.11-00003 | Frames, Bezugspunkt und Drehpunkt unterscheiden | Transformationen korrekt; Schwerpunkt nicht als festes Gelenk dargestellt; Abschnitt 2.3 |
| A-V0.11-00004 | Vollständiger Katalog vorhandener Beiträge | Alle im jeweiligen Rechenpfad gelieferten Beiträge erfasst; Abschnitt 3.1 |
| A-V0.11-00005 | Beiträge fachlich und stabil gruppieren | Eindeutige Primärzuordnung ohne erzwungene Gegenkraft; Abschnitt 3.2 |
| A-V0.11-00006 | Momente und Summen korrekt bilden | Gemeinsamer Frame/Bezug, vorhandene Wrenches korrekt verschoben; Abschnitt 3.3 |
| A-V0.11-00007 | Gewicht und Aggregationen genau einmal berücksichtigen | Kein doppeltes Gewicht oder Addieren von Summen zu ihren Quellen; Abschnitt 3.4 |
| A-V0.11-00008 | Wirkungslinie und Restmoment vollständig darstellen | Äquivalente Darstellung erhält Kraft und Moment; Abschnitt 3.5 |
| A-V0.11-00009 | Zentrales Beitragsregister führen | Stabile IDs, Quellen, Gruppen und Layoutvorgaben; Abschnitt 4.1 |
| A-V0.11-00010 | Bestehende Physikklassen wiederverwenden | Wrench, Kraftbeitrag und KraftErgebnis bleiben fachliche Quelle; Abschnitt 4.2 |
| A-V0.11-00011 | Herkunft und Quellenbeziehungen explizit modellieren | Einzelbeitrag, Summe und Momentableitung eindeutig; Abschnitt 4.2 |
| A-V0.11-00012 | Gemeinsamen unveränderlichen Anzeigestand verwenden | 3D und Werte haben denselben Körper-, Zeit- und Sequenzbezug; Abschnitt 4.3 |
| A-V0.11-00013 | Physikadapter von GUI und Rendering trennen | Keine Physikauswertung durch Zeichen- oder Tabellenklassen; Abschnitt 4.3 |
| A-V0.11-00014 | Skalierung zentral und dimensionsgetrennt kapseln | Kraft- und Momentenskala unabhängig; Abschnitt 4.4 |
| A-V0.11-00015 | Vorhandene IDs, Einstellungen und native Pfade integrieren | Keine parallele Registerpflege oder stiller Backendwechsel; Abschnitt 4.5 |
| A-V0.11-00016 | Kraftpfeile eindeutig darstellen | Angriff/Anker, Richtung und Betrag mit Null-/Grenzfallverhalten; Abschnitt 5.1 |
| A-V0.11-00017 | Momente als gerichtete 3D-Bögen darstellen | Rechte-Hand-Regel, Gesamtvektor und Komponenten unterscheidbar; Abschnitt 5.2 |
| A-V0.11-00018 | Hebelarme und Herkunft in 3D erklären | Senkrechter Hebelarm statt unbeschriftetem K-S-Abstand; Abschnitt 5.3 |
| A-V0.11-00019 | Lineare und nullverträgliche logarithmische Skala anbieten | Definierte Formeln, Referenzen und Grenzmarkierungen; Abschnitt 5.4 |
| A-V0.11-00020 | Skalierung während eines Laufs stabil halten | Ausblenden ändert Maßstab nicht; explizites Neu-Einpassen; Abschnitt 5.4 |
| A-V0.11-00021 | Größen und Strichstärken lesbar halten | Bildschirmstabile Köpfe/Dicken, DPI- und Kameratest; Abschnitt 5.5 |
| A-V0.11-00022 | Farben und Standardlayout festlegen | Registervorgaben aus Abschnitt 5.6 gelten ohne Nutzerüberschreibung |
| A-V0.11-00023 | Räumlichen und Vordergrundmodus unterscheiden | Beide Modi auswählbar und kenntlich; Abschnitt 5.7 |
| A-V0.11-00024 | Pfeile eindeutig auswählen und hervorheben | Bildschirmauswahl und Mehrfachtreffer nachvollziehbar; Abschnitt 5.7 |
| A-V0.11-00025 | Freifliegende gruppierte Werteübersicht anbieten | Ein schließbares, wieder öffnbares Qt-Dockfenster; Abschnitt 6.1 |
| A-V0.11-00026 | Werte und Bezug vollständig anzeigen | Komponenten, Betrag, Einheit, Quelle, Punktart und Status; Abschnitt 6.2 |
| A-V0.11-00027 | Zahlen konsistent formatieren | Rundung sichtbar, Details ausreichend genau, keine falschen Nullen; Abschnitt 6.2 |
| A-V0.11-00028 | Tabellen- und 3D-Auswahl synchronisieren | Identische IDs, bidirektionale Auswahl, keine Physikänderung; Abschnitt 6.3 |
| A-V0.11-00029 | Wertefenster zunächst als Mockup abstimmen | Gruppierung, Spalten und Bedienung vor produktiver GUI-Anbindung prüfen; Abschnitt 6.4 |
| A-V0.11-00030 | Physikalische Referenzfälle nachweisen | Fälle aus Abschnitt 7.1 mit erwarteten Zahlen bestanden |
| A-V0.11-00031 | Lifecycle und Rechenpfade prüfen | Kein veralteter Körper/Anzeigestand und kein stiller Datenverlust; Abschnitt 7.2 |
| A-V0.11-00032 | Darstellung und Interaktion sichtbar prüfen | Kamera-, DPI-, Überlappungs- und Nulltests; Abschnitt 7.3 |
| A-V0.11-00033 | Laufzeit und Ressourcen belegen | Vergleichsmessungen, Caching und begrenzte Actor-/Datenhaltung; Abschnitt 7.4 |
| A-V0.11-00034 | Nachvollziehbare Abnahme dokumentieren | A-ID, Test/Beleg, Ergebnis und offene Punkte vollständig zugeordnet; Abschnitt 7.5 |
| A-V0.11-00035 | Bisherige Kraft- und Momentendarstellung vollständig ablösen | Alle Aufrufstellen umgestellt; ersetzte Zeichenpfade und doppelte Darstellungsberechnungen entfernt, kein Altpfad/Fallback; Abschnitt 4.6 |
| A-V0.11-00036 | Werkzeugwahl anhand der Anforderungen belegen | Vorhandenen Stack bevorzugen, kritische Fälle erproben und genau einen produktiven Darstellungspfad auswählen; Abschnitt 4.7 |
| A-V0.11-00037 | Einheitliche Darstellung in allen Betriebszuständen | Gleiche Daten und wirksame Einstellungen erzeugen dieselbe Darstellung in Statik, stationärer Auswertung, Dynamik und Pause; Abschnitt 4.8 |
| A-V0.11-00038 | Änderungen ereignisgesteuert vollständig nachführen | Nicht abschließender Triggerkatalog verdrahtet; Aktualisierung ohne Animationstakt, veraltete Ergebnisse verworfen; Abschnitt 4.9 |
| A-V0.11-00039 | Vollständige Bilanz von Teilsumme unterscheiden | Fehlende/ungültige benötigte Beiträge sperren die Kennzeichnung als vollständige Bilanz; Abschnitt 3.6 |
| A-V0.11-00040 | Gleichgewichtsstatus fachlich begründen | Nur gültige Solver-Kriterien am selben Zustand verwenden; Abschnitt 3.7 |
| A-V0.11-00041 | Null-/Kleinwertgrenzen und Wirkungslinienstabilität festlegen | Physik-, Zahlen- und Grafikgrenzen getrennt; sicherer Wrench-Fallback bei instabiler Zerlegung; Abschnitt 3.8 |
| A-V0.11-00042 | Überlagerte Kraftmodelle transparent machen | Aktive Quellen unverändert zeigen und fachliche Überlagerungen prüfen; Abschnitt 3.6 |
| A-V0.11-00043 | Körperumfang der Anzeige eindeutig festlegen | Standard Einzelkörper, Mehrkörperanzeige ohne unbegründete Systemsumme; Abschnitt 4.10 |
| A-V0.11-00044 | Momentenbögen kontinuierlich orientieren | Stabile Bogenbasis bei Achsenänderung, Nulldurchgang und Vorzeichenwechsel; Abschnitt 5.8 |
| A-V0.11-00045 | Beschriftungsüberlagerung begrenzen | Priorisierte Labels, vollständige Werte im Fenster, kein verdeckter Informationsverlust; Abschnitt 5.9 |
| A-V0.11-00046 | Anzeigeeinstellungen dauerhaft und konsistent speichern | Settings-Wiederherstellung ohne gespeicherte Physik-/Veraltetdaten; Abschnitt 6.5 |
| A-V0.11-00047 | GUI-Aktualisierungen kontrolliert bündeln | Neuester Stand zuverlässig, atomare Ausgabe und begrenzte Warteschlange; Abschnitt 6.6 |
| A-V0.11-00048 | Anzeige gegen Solver-/Integratorbilanz nachweisen | Identischer Zustand, Frame, Bezug und Auswertungszeitpunkt; Abschnitt 7.6 |

## 2. Physikalische Grundlagen

### 2.1 Umfang — A-V0.11-00001

Es werden ausschließlich bereits vorhandene Kraftmodelle und ihre
Ergebnisse dargestellt. Die neue Anzeige erzeugt keine Ersatzkräfte,
keine künstlichen Gegenkräfte und keine neue Wellen-, Wind- oder
Segelphysik. Fehlt ein benötigter physikalischer Beitrag, ist die Lücke
sichtbar zu machen und vor einer fachlichen Erweiterung zu entscheiden.

Die erste Umsetzung behandelt 3D-Pfeile und eine numerische Übersicht.
2D-Projektionen und Zeitdiagramme sind nicht Teil dieses Umfangs.
Bestehende Simulations-, Solver- und Bedienfunktionen bleiben erhalten.

### 2.2 Einheiten und Datenzustände — A-V0.11-00002

- Physikalische Speicherung: Meter, Newton, Newtonmeter, Sekunden und
  doppelte Genauigkeit. Skalierungswerte für die Grafik verändern keine
  physikalischen Werte.
- Kräfte und Momente werden als Vektoren geführt. Betrag und Richtung
  sind Ableitungen, keine unabhängig editierbaren Kopien.
- Ein Nullvektor ist gültig, hat aber keine definierte Richtung.
  Fehlend, deaktiviert, noch nicht berechnet, veraltet und ungültig sind
  eigene Zustände; sie dürfen nicht still als Null erscheinen.
- NaN/Inf und widersprüchliche Frames werden mit Quellbezug als Fehler
  gemeldet. Betroffene Grafik wird nicht mit erfundenen Werten fortgeführt.
  Fehleranzeige und Protokollierung folgen den vorhandenen Projektwegen.

### 2.3 Frame, Bezugspunkt und Drehpunkt — A-V0.11-00003

Standard ist der vorhandene Simulations-/Weltframe mit expliziter
Achsenkennzeichnung. Körperfeste Werte werden nur mit benannter
Transformation und eindeutiger Kennzeichnung angezeigt. Die Kamera
ändert den fachlichen Frame nicht.

Standard-Momentenbezug ist der aktuelle Gesamtschwerpunkt S des
betrachteten Laufzeitkörpers. Für ein frei schwimmendes Boot ist S kein
feststehender Drehpunkt. Ein tatsächliches Gelenk oder eine Lagerung darf
nur dann als Zwangsdrehpunkt bezeichnet werden, wenn es diese Bindung
im vorhandenen Modell gibt; es wird keine neue Lagerphysik eingeführt.

Ein Kräftepaar hat ein bezugspunktunabhängiges Moment. Bei resultierender
Kraft hängt das Moment vom Bezugspunkt ab. Eine Momentenrichtung ist
nicht automatisch die momentane Winkelgeschwindigkeit oder Drehachse.

**Werkzeuge:** vorhandene
[Pose-Transformationen](../../../../code/python/segelphysik/core/frames.py)
für Punkte und Vektoren; vorhandene
[Wrench-Verschiebung](../../../../code/python/segelphysik/core/kraftmodell.py)
für Bezugspunktwechsel. Punkte erhalten Rotation und Translation,
freie Kraft-/Momentenvektoren nur die passende Rotation.

## 3. Kräfte, Momente, Gruppierung und Berechnung

### 3.1 Katalog vorhandener Quellen — A-V0.11-00004

Die Tabelle benennt die im bestehenden gemeinsamen Kraftmodell
nachgewiesenen Quellarten. Tatsächliche Verfügbarkeit hängt von
Körper, aktiviertem Modell und Rechenpfad ab. Sie ist keine Zusage, dass
jedes Modell alle Arten liefert.

| Quelle / vorhandener Name | Physikalische Daten | Angriff / Bezug | Zugehörige Momente |
|---|---|---|---|
| Gewicht / `schwerkraft` | F_G = (0, 0, −m·g) im Weltframe | Gesamtschwerpunkt S | Um S null; um einen anderen Bezugspunkt entsprechendes Hebelarmmoment |
| Auftrieb / `hydrostatik` | F_A und Moment aus dem vorhandenen Hydrostatikmodell | Auftriebsschwerpunkt K, soweit verfügbar; Wrench-Bezug des Ergebnisses | Geliefertes hydrostatisches Moment; keine zweite Addition von (K−S)×F_A |
| Allgemeiner Widerstand / `widerstand` | Vorhandener linearer und quadratischer 6D-Widerstand | Gelieferter Wrench-Bezug | Translatorische Kraft und rotatorischer Widerstandsanteil |
| Rumpf / `hydrodynamik_rumpf` | Gelieferte kombinierte Reibungs-/Widerstandskraft | Originaler Quellpunkt, wenn mitgeführt; sonst Wrench-Darstellung | Übertragenes Moment um S |
| Kiel / `hydrodynamik_kiel` | Gelieferte kombinierte Lift-/Widerstandskraft | Wie vom Modell geliefert bzw. als äquivalent gekennzeichnet | Übertragenes Moment um S |
| Ruder / `hydrodynamik_ruder` | Gelieferte kombinierte Lift-/Widerstandskraft mit aktuellem Rudereinfluss | Wie beim Kiel | Übertragenes Moment um S |
| Volumenkörper / `hydrodynamik_volumenkoerper` | Aggregierte verteilte Widerstandskräfte | Quellbezug; kein erfundener eindeutiger Angriffspunkt | Geliefertes Eigen-/Restmoment plus Bezugspunktverschiebung |
| Test-/Fremdkraft / `fremdkraft` | Bestehende konfigurierte Kraft | Konfigurierter Punkt mit vorhandener Pose transformiert | (A−S)×F, soweit nicht bereits im Wrench enthalten |
| Added Mass / `added_mass` | Beschleunigungsabhängiger vorhandener Beitrag, nur wenn tatsächlich ausgewertet | Gelieferter Wrench-Bezug | Gelieferter rotatorischer Zusatzanteil; keine erneute Trägheitskorrektur |

Die bestehende Hydrodynamik liefert teils kombinierte Kräfte. Die Anzeige
darf diese nicht eigenmächtig in vermeintlich gemessene Einzelwerte für
Lift, Reibung oder Druck zerlegen. Eine spätere transparente Zerlegung
derselben Physik erfordert eindeutige Quelldaten.

Mehrere Beiträge derselben Rolle bleiben einzeln identifizierbar; der Name
`hydrodynamik_rumpf` allein ist keine eindeutige Instanz-ID. Neue oder noch
nicht zugeordnete bekannte Beiträge werden als „nicht zugeordnet“ sichtbar
und mit Originalname aufgeführt, nicht aus Bilanz oder Übersicht entfernt.

**Quellen/Werkzeuge:**
[kraftmodell.py](../../../../code/python/segelphysik/core/kraftmodell.py),
[hydrodynamik.py](../../../../code/python/segelphysik/core/hydrodynamik.py).
Es werden keine neuen Kraftgesetze für die Anzeige implementiert.

### 3.2 Gruppierung — A-V0.11-00005

Primäre Hierarchie: **Laufzeitkörper → fachliche Gruppe → Quellbeitrag →
Kraft und Moment**. Ein Beitrag besitzt genau eine primäre Bilanzzuordnung.

| Gruppe | Inhalt | Angezeigte Ableitung |
|---|---|---|
| Gewicht und Auftrieb | Schwerkraft, Hydrostatik | Gemeinsame Kraft-/Momentenbilanz; keine Zwangsgleichheit der Beträge |
| Hydrodynamik | Untergruppen Rumpf, Kiel, Ruder, Volumenkörper | Rollensummen und Hydrodynamik-Gesamtsumme |
| Allgemeiner Widerstand | Vorhandener 6D-Widerstandsbeitrag | Kraft und rotatorisches Moment |
| Test-/Fremdkraft | Vorhandene Test-/Fremdkraftinstanzen | Kraft und zugehöriges Hebelarmmoment |
| Added Mass | Vorhandener beschleunigungsabhängiger Beitrag | Gelieferte Kraft-/Momentenkorrektur |
| Nicht zugeordnet | Gelieferte, noch nicht katalogisierte Beiträge | In Gesamtbilanz berücksichtigt, Zuordnungsbedarf sichtbar |
| Gesamtbilanz | Alle eindeutigen atomaren Beiträge | Gesamt-F und Gesamt-M um S |

Quellzuordnungen und Standardlayout sind stabil; Werte, Aktivierung,
Geometrie und tatsächliche Instanzen ändern sich mit dem Modell.
Eine Gruppe benötigt nicht zwingend zwei Kräfte. Newtonsche Gegenkräfte
wirken häufig auf einen anderen Körper, beispielsweise auf das Wasser.
Sie werden dem betrachteten Boot nicht zusätzlich zugeschlagen.

### 3.3 Berechnung — A-V0.11-00006

Alle Summanden müssen im selben Frame liegen. Für eine Kraft Fᵢ am
tatsächlichen Angriffspunkt Aᵢ und einen dort zusätzlich gelieferten
Momentenanteil Mᵢ,A gilt:

```text
rᵢ = Aᵢ − P
Mᵢ,P = rᵢ × Fᵢ + Mᵢ,A
F_Gruppe = Σ Fᵢ
M_Gruppe,P = Σ Mᵢ,P
```

Liegen die Daten bereits als Wrench (Fᵢ, Mᵢ,Q) um Q vor, gilt stattdessen:

```text
Mᵢ,P = Mᵢ,Q + (Q − P) × Fᵢ
```

Beide Darstellungen dürfen nicht gemeinsam denselben Hebelarm addieren.
Rotation in einen anderen Frame erfolgt vor dem Summieren mit den
vorhandenen Frame-Transformationen.

**Werkzeuge:** `Wrench.auf_bezugspunkt` und
`aggregiere_kraftbeitraege` in
[kraftmodell.py](../../../../code/python/segelphysik/core/kraftmodell.py).
Die GUI verwendet deren fachlich konsistente Ergebnisse.

### 3.4 Einmalige Bilanzierung — A-V0.11-00007

Gruppen- und Gesamtsummen referenzieren ihre atomaren Quellbeiträge.
Eine Summe ist kein zusätzlicher physikalischer Beitrag. Die bestehenden
Darstellungen `rest`, `zusatz` und `hydro_sum` müssen eindeutig als
abgeleitete Ansichten zugeordnet werden; `zusatz` darf nicht zusätzlich
zu seinen Widerstands-/Hydrodynamik-/Added-Mass-Quellen summiert werden.

Insbesondere liefert `KraftErgebnis.schwerkraft_beruecksichtigt`, ob
Gewicht bereits im Ergebnis steckt. Ein Adapter für einen älteren
Hydrostatikpfad darf fehlendes Gewicht genau einmal aus derselben Masse
und demselben g ergänzen und muss dies als Adapterbeitrag kennzeichnen.
Der Adapter verändert nicht die Solverbilanz.

Added Mass wird nur mit dem tatsächlich ausgewerteten Beschleunigungsstand
ausgewiesen. Die Anzeige darf den Beitrag weder erneut anwenden noch eine
fehlende Beschleunigung mit null ersetzen. Summe und ausgewiesene
Einzelbeiträge müssen denselben ausgewerteten Zustand beschreiben.

### 3.5 Äquivalente Wirkungslinie und Restmoment — A-V0.11-00008

Ein Wrench besitzt nicht immer einen einzigen physikalischen Angriffspunkt.
Fehlt der Originalpunkt, ist die Anzeige entweder am benannten Bezugspunkt
als Kraft plus Moment oder als explizit äquivalente Wirkungslinie zulässig.
Ein bloßer Geometrieschnitt ist kein Nachweis eines realen Angriffspunktes.

Für F ungleich null:

```text
A_eq = P + (F × M_P) / (F · F)
Wirkungslinie: A_eq + λ F
M_rest = M_P − (A_eq − P) × F
```

Das verbleibende Moment parallel zu F darf nicht verloren gehen. Für eine
reine Momentenwirkung bei F = 0 werden nur Moment und Bezug angezeigt,
keine Richtung oder Wirkungslinie einer erfundenen Kraft.

**Werkzeuge:** vorhandene
[Wirkungslinien-/Geometriehelfer](../../../../code/python/segelphysik/core/kraefte_bild.py)
weiterverwenden; Restmoment explizit in den Anzeigedaten erhalten.

### 3.6 Vollständigkeit und Quellenüberlagerung — A-V0.11-00039, A-V0.11-00042

Jeder Snapshot führt den Umfang der für diesen Körper und Rechenmodus
aktivierten und erwarteten Quellbeiträge mit. „Deaktiviert“ bedeutet nicht
„fehlend“: Ein bewusst ausgeschaltetes Modell ist kein benötigter Summand.
Ein aktiver, aber nicht berechneter oder ungültiger Beitrag ist dagegen
eine Bilanzlücke. Ausblenden in 3D ändert diesen Umfang nicht.

Nur bei vollständigen gültigen Daten darf eine Summe als „Gesamtbilanz“
bezeichnet werden. Andernfalls lautet sie „Verfügbare Teilsumme –
unvollständig“, mit ausdrücklicher Liste der fehlenden oder ungültigen
Quellen. Die vorhandenen gültigen Summanden dürfen zur Diagnose angezeigt
werden, ohne fehlende Beiträge als null zu ersetzen. Ist selbst der
erwartete Quellenumfang unbekannt, lautet der Status „Vollständigkeit
ungeklärt“. Eine vorliegende Solver-Gesamtsumme kann getrennt mit ihrer
Herkunft angezeigt werden, beweist aber keine vollständige Einzelauflösung.

Allgemeiner Widerstand und geometriebezogene Hydrodynamik können
gleichzeitig aktiviert sein. Ihre unterschiedliche Herkunft und
Parametrisierung werden sichtbar ausgewiesen. Vor der Abnahme ist zu
prüfen, ob eine fachlich beabsichtigte Ergänzung oder eine unbeabsichtigte
Modellüberlagerung vorliegt. Ungeklärte Überlagerungen werden als Hinweis
geführt. Die Darstellung entfernt oder korrigiert keinen vom Solver
tatsächlich verwendeten Beitrag eigenmächtig.

### 3.7 Aussage zum Gleichgewicht — A-V0.11-00040

„Im Gleichgewicht“ darf nur aus einem gültigen fachlichen Kriterium des
zuständigen Solvers für denselben Zustand, Quellenumfang und dieselben
betrachteten Freiheitsgrade abgeleitet werden. Kriterien, Toleranzen und
geprüfte Freiheitsgrade sind im Detailbereich zugänglich. Ein bestandener
Teilsolver darf nicht als vollständiges 6DOF-Gleichgewicht erscheinen.

Bei einer stationären Bewegung ist der Status als „stationärer Zustand
gemäß Solver“ mit dessen Bedingungen zu benennen. In laufender Dynamik
beweist eine kleine Momentaufnahme von Kraft und Moment kein statisches
Gleichgewicht. Ohne passende Kriterien heißt es „Gleichgewicht nicht
bewertet“; bei unvollständiger Bilanz „nicht bewertbar“. Nur bei gültigen,
auswertbaren und verfehlten Kriterien ist „Kriterien nicht erfüllt“
zulässig. Angezeigte Rundung oder Grafikschwellen sind keine
Gleichgewichtstoleranzen. Dies präzisiert auch die Bilanzstatuskarte des
Mockups; ihre Beispielbeschriftung ist keine eigenständige Statusregel.

### 3.8 Numerische und grafische Grenzen — A-V0.11-00041

Es werden getrennt geführt:

- **Physikalische/solverbezogene Toleranzen:** unverändert vom jeweiligen
  fachlichen Vertrag übernehmen und benennen.
- **Algebraische Null:** Ein tatsächlich gelieferter Nullvektor bleibt
  null; kleine endliche Originalwerte werden nicht auf null gesetzt.
- **Grafische Kleinwertgrenzen:** ausschließlich zur lesbaren Darstellung,
  mit Kleinwertkennzeichnung und weiterhin verfügbaren Originalwerten.

Für die grafische Wirkungslinienzerlegung gilt als Entwurfsgrenze
`epsilon_F = max(1e-9 N, 1e-12 · F_char)`. Dabei ist `F_char` die größere
Größe aus m·g und dem größten gültigen atomaren Kraftbetrag desselben
Snapshots, mindestens 1 N. Eine Änderung der visuellen Skalenreferenz
ändert diese Grenze nicht.

Für `|F| <= epsilon_F`, nicht endlich berechenbare Ergebnisse oder eine
äquivalente Ankerentfernung von mehr als zehn charakteristischen
Körperausdehnungen wird keine Wirkungslinie konstruiert. Stattdessen
werden der unveränderte Wrench am Bezugspunkt und der Grund
„Wirkungslinie numerisch/visuell nicht geeignet“ angezeigt. Die
charakteristische Körperausdehnung ist die größte Ausdehnung der
gültigen Körpergeometrie, mindestens 0,05 m; fehlt die Geometrie,
unterbleibt diese Zerlegung mit entsprechendem Hinweis.

Diese Grenze ist keine neue physikalische Näherung und kein Rückfall
auf einen alten Zeichenpfad, sondern eine Darstellung desselben Wrench
innerhalb der gemeinsamen Pipeline. Kleine Kräfte und zugehörige
Momente bleiben vollständig in Werten und Bilanz erhalten.
Tests prüfen beide Seiten der Grenzen, nahezu auslöschende Kräfte,
große Moment/Kraft-Verhältnisse und die Unabhängigkeit von der
gewählten grafischen Skalierung.

## 4. Datenmodell, Klassen und Datenfluss

### 4.1 Ein zentrales Register — A-V0.11-00009

Das vorhandene Register in
[pfeilstil.py](../../../../code/python/segelphysik/core/pfeilstil.py)
wird weiterentwickelt, nicht durch eine parallel gepflegte Liste ersetzt.
Eine Definition enthält:

| Feld | Bedeutung |
|---|---|
| Stabile Definitions-ID | Bestehende Pfeil-ID soweit passend erhalten |
| Quellart / Quellvertrag | Benannter Kraftmodellbeitrag bzw. definierte Ableitung |
| Fachlicher Name und Gruppe | Verständliche Beschriftung und Hierarchie |
| Größe und Ableitungsart | Kraft, Moment, Summe, Komponente oder Hilfsgeometrie |
| Quellen-IDs | Fachliche Herkunft einer Ableitung, keine Referenz auf GUI-Actors |
| Layoutvorgaben | Farbe, Linienart, Sichtbarkeit, Reihenfolge, Skalendomäne |
| Punktart | Tatsächlicher Angriff, Momentenbezug oder äquivalenter Anker |

Instanz-IDs verbinden Körper-ID, Definition und stabile Quellinstanz.
Listenpositionen allein dürfen nicht über wechselnde Auswertungen hinweg
eine vermeintliche Identität begründen.

### 4.2 Fachliche und darstellungsbezogene Klassen — A-V0.11-00010 bis A-V0.11-00011

Die Tabelle beschreibt Verantwortlichkeiten. Neue Namen sind Zielnamen,
keine Forderung nach einer eigenen Datei für jede Klasse oder nach einer
neuen tiefen Vererbungshierarchie.

| Klasse / Baustein | Bestehend / Ziel | Verantwortung |
|---|---|---|
| `Wrench` | Bestehend | Unveränderliche Kraft und Moment mit Frame und Bezugspunkt; korrektes Verschieben |
| `Kraftbeitrag` | Bestehend | Benannter atomarer Beitrag mit Wrench |
| `KraftErgebnis` | Bestehend | Physikergebnis einschließlich Beiträgen und Bilanzierungsmerkmalen |
| `Pose` | Bestehend | Eindeutige Körper-/Welttransformationen |
| `BeitragsDefinition` | Registereintrag, weiterzuentwickeln | Statische Quell-, Gruppen- und Layoutdefinition |
| `BeitragsAnzeige` | Neues schlankes Datenobjekt | Instanz-ID, Quell-IDs, Wrench, Punktart, optionaler Originalangriff, Status und Provenienz |
| `KraefteAnzeigeSnapshot` | Neuer Anzeigestand | Körper, Modellgeneration, Sequenz, physikalische Zeit, zugehörige Pose und Beiträge/Summen |
| `KraefteAnzeigeAdapter` | Neue fachliche Adaptergrenze | Physikergebnis in Anzeigestand überführen; unterschiedliche Ergebnisverträge explizit normalisieren |
| `SkalenAbbildung` | Neuer bzw. extrahierter Darstellungshelfer | Lineare/logarithmische Größenabbildung ohne Änderung der Physik |
| `Stil` | Bestehend | Nutzeroptionen und Registerdefaults auflösen |
| `GrafikBruecke` | Bestehend, zu erweitern | Actors aktualisieren, Geometrie wiederverwenden, Auswahl-IDs zuordnen |
| `KraefteWerteModell` | Neues Qt-Modell | Hierarchische Werte aus demselben Snapshot für das Wertefenster bereitstellen |

Herkunftsarten sind explizit: gelieferter Einzelbeitrag, übernommener
Wrench, physikalisch begründete Adapterergänzung, Gruppensumme und
Komponentenprojektion. Eine leere Quellenliste bedeutet nicht automatisch
„externes Moment“. Unbekannte Herkunft bleibt als solche sichtbar.

### 4.3 Konsistenter Datenfluss — A-V0.11-00012 bis A-V0.11-00013

```text
Vorhandene Physik / Worker
    → Ergebnis mit Pose, Zeit und Beiträgen
    → KraefteAnzeigeAdapter
    → KraefteAnzeigeSnapshot
        → GrafikBruecke / 3D
        → KraefteWerteModell / Wertefenster
```

Der Snapshot ist nach Veröffentlichung unveränderlich. GUI und Renderer
werten keine Kraftfunktion aus und erfinden keine fehlenden Fachwerte.
Bereits normalisierte Physikdaten werden nicht in einem zweiten GUI-Modell
abweichend nachgerechnet. Darstellungsableitungen und Caches beziehen sich
auf denselben gekennzeichneten Snapshot.

Bei zeitlich interpolierter Körperanzeige werden Kräfte nicht unbemerkt
als aktuelle Physikwerte umgedeutet. Kraftglyphen, Bezugspunkte und
Wertetabelle nutzen die mitgelieferte Kraftpose; ein zeitlicher Versatz
zur interpolierten Körperszene wird kenntlich gemacht. Fehlende
Kraftdaten für einen Modus werden als nicht verfügbar angezeigt, nicht
durch eine teure verdeckte GUI-Neuberechnung ersetzt.

Qt-/VTK-Objekte werden ausschließlich im GUI-Thread verändert.
Nach Reset, Körperwechsel oder neuer Modellgeneration sind alte
Snapshots und Auswahlverknüpfungen nicht weiterzuverwenden.

### 4.4 Skalierungsklasse — A-V0.11-00014

Eine gemeinsame Abbildung je Kraft- und Momentendomäne innerhalb der
aktuellen Vergleichsansicht. Einzelpfeile besitzen keine versteckten
abweichenden Betragsmaßstäbe. Vorhandene individuelle Skalenoptionen werden
bei Übernahme sichtbar berücksichtigt oder mit angekündigter
Einstellungsmigration vereinheitlicht, nicht still ignoriert.

Der Helfer erhält Größe, Domäne, Modus, Referenz, Darstellungsgrenzen
und liefert Darstellungsgröße sowie Grenz-/Kleinwertstatus.
Physikalischer Originalwert bleibt unverändert verfügbar.

### 4.5 Integration und Werkzeuge — A-V0.11-00015

- Bestehende Helfer in
  [kraefte_bild.py](../../../../code/python/segelphysik/core/kraefte_bild.py),
  [pfeilstil.py](../../../../code/python/segelphysik/core/pfeilstil.py) und
  [grafik_bruecke.py](../../../../code/python/segelphysik/grafik_bruecke.py)
  verwenden und gezielt erweitern. Kein paralleles Pfeilsystem.
- Einstellungen und vorhandene Sichtbarkeitsoptionen bleiben wirksam.
  Nötige semantische Änderungen wie „Gegenkraft“ zu „Auftriebskraft“ werden
  gezielt erläutert, ohne bekannte Einstellungen zu verlieren.
- Bestehende native Berechnung bleibt erhalten; kein stiller
  Python-Fallback und kein neuer Python-Rückruf im nativen Physikbatch.
- Sollten native Verträge betroffen sein, gelten die
  [Schnittstellenregister-Regeln](../../../../.github/instructions/schnittstellenregister.instructions.md).
  Dieser Entwurf definiert keine neuen C++-Exports und vergibt daher
  keine vorgezogenen CPPI-Kennungen.

### 4.6 Vollständige Ablösung der bisherigen Pfeildarstellung — A-V0.11-00035

Die neue Kraft- und Momentendarstellung ersetzt sämtliche bisherigen
Zeichenpfade für diese Größen in allen betroffenen Ansichten und
Betriebsarten. Es darf nur eine gemeinsame Implementierung für
Beitragszuordnung, Darstellungsberechnung, Skalierung und Rendering geben.
3D-Ansicht und Wertefenster beziehen ihre fachlichen Daten und Ableitungen
aus derselben Quelle; ihre jeweiligen Ausgabeadapter bleiben getrennt.

Geeignete vorhandene Funktionen werden übernommen oder angepasst,
nicht parallel neu implementiert. Vor der Umstellung sind die bisherigen
Zeichenpfade, Hilfsfunktionen, Register, Einstellungen und Aufrufstellen
zu erfassen. Alle relevanten Aufrufstellen werden auf die gemeinsame
Lösung umgestellt. Danach werden ersetzte Zeichenpfade, doppelte
Darstellungsberechnungen, ungenutzte Hilfsfunktionen und überholte
Registereinträge aus dem produktiven Code entfernt. Nicht mehr benötigte
Einstellungen werden mit nachvollziehbarer Migration entfernt; weiterhin
benötigte Nutzeroptionen bleiben gemäß A-V0.11-00015 erhalten.

Es bleibt kein wählbarer alternativer Altpfad und kein stiller Rückfall
auf die bisherige Darstellung bestehen. Vorübergehende Parallelität
während der Entwicklung ist nur als interne Übergangslösung zulässig,
nicht als abgenommener Zustand.

Die vorhandenen physikalischen Berechnungen bleiben die maßgebliche
Quelle. Die Bereinigung betrifft doppelte oder ersetzte
Darstellungsberechnungen; die weiterhin benötigten Physikfunktionen und
vorgesehenen Python-/C++-Rechenpfade bleiben erhalten.
Gemeinsam genutzte Helfer für andere Darstellungen werden
erhalten, soweit sie weiterhin gebraucht werden.

Zur Abnahme sind sowohl die Funktion der neuen Darstellung als auch
die vollständige Ablösung nachzuweisen: alle erfassten Aufrufstellen
umgestellt, keine verbliebenen produktiven Altpfad-Aufrufe, keine
parallele Register-/Skalenpflege und keine doppelten Actors nach
Körperwechsel, Reset oder erneutem Öffnen einer Ansicht. Tests und
Quellcodeprüfung belegen diese Punkte; ein erfolgreicher Build allein
genügt nicht.

### 4.7 Werkzeugwahl und Entscheidungsnachweis — A-V0.11-00036

Ausgangspunkt ist der vorhandene Stack aus NumPy, PySide6, PyVista und
VTK. Es wird keine zusätzliche Grafikbibliothek und kein eigener Renderer
eingeführt. Vorrang hat die einfachste wartbare Lösung, die die fachlichen,
grafischen und messbaren Anforderungen dieser Spezifikation erfüllt.

| Aufgabe | Bevorzugtes Werkzeug / Verfahren | Bedingung für eine andere Umsetzung im vorhandenen Stack |
|---|---|---|
| Physikdaten, Momente und Summen | Vorhandene Wrench-/Kraftmodellfunktionen | Keine unabhängige GUI-Ersatzberechnung; Vertragsänderungen begründen und prüfen |
| Skalierung und Darstellungsdaten | Vorhandene Helfer erweitern, NumPy | Zentral und ohne Renderer testbar halten |
| Kraftpfeile und Momentenbögen | Bestehende PyVista-/VTK-Geometrien und wiederverwendete Actors | Direkte VTK-Nutzung, wenn die PyVista-Ebene notwendige Kontrolle nicht bietet |
| Bildschirmstabile Köpfe und Strichstärken | Vorhandene Kameraumrechnung oder vtkDistanceToCamera | An Kamera-, DPI- und Kurzpfeilfällen nachweisen; nicht nur gesamten Pfeil skalieren |
| Wertefenster | PySide6 QDockWidget, QTreeView und gemeinsames Datenmodell | Keine parallele Datenhaltung oder neue GUI-Bibliothek |
| Auswahl | Vorhandene PyVista-/VTK-Picker | Ergänzungen nur für nachgewiesene Lücken wie Bildschirmtoleranz oder Mehrfachtreffer |
| Viele gleichartige Pfeile | Zunächst vorhandene Geometrie-/Actor-Wiederverwendung | vtkGlyph3DMapper nur bei belegtem Vorteil und vollständiger Erfüllung von Gestaltung und Auswahl |

Vor einer grundlegenden Änderung des Darstellungsverfahrens wird geprüft,
ob gezielte Erweiterungen des vorhandenen Verfahrens ausreichen. Kritische
Fälle werden in einem begrenzten Darstellungsversuch erprobt: kurze Pfeile
mit unabhängigem Kopf, Momentenrichtung und -radius, Kameraperspektive,
DPI, Überlagerung und eindeutige Auswahl.

Die Entscheidung wird im gemeinsamen Umsetzungsplan mit geprüften
Anforderungen, Testergebnissen, notwendigen Vergleichsmessungen und
Wartungsaufwand begründet. Ein theoretischer Geschwindigkeitsvorteil allein
rechtfertigt keinen Wechsel auf Glyph-Rendering. Grenzwerte und
Leistungsabnahme folgen Abschnitt 7.4.

Das ausgewählte Verfahren wird einheitlich produktiv integriert.
Versuchsvarianten und ersetzte Implementierungen bleiben nicht als
zusätzliche produktive Zeichenpfade bestehen; die Ablösung erfolgt nach
A-V0.11-00035. Ein Vergleichsversuch begründet keine zweite dauerhaft
gepflegte Codebasis.

### 4.8 Einheitliches Verhalten in Statik und Dynamik — A-V0.11-00037

Für statische, stationäre und dynamische Auswertung sowie angehaltene
Dynamik gilt dieselbe gemeinsame Darstellungspipeline. Gleiche fachliche
Daten und gleiche wirksame Einstellungen ergeben unabhängig vom Modus
dieselben Pfeile, Momentenbögen, Quellen-/Hebelarmanzeigen und Zahlenwerte.
Für die verlaufsabhängige Phasenlage der Momentenbögen nach Abschnitt 5.8
setzt geometrische Identität zusätzlich denselben initialisierten
Darstellungszustand voraus. Abweichende Verlaufscaches dürfen weder
Betrag, Momentenachse und Drehsinn noch die Zahlenwerte verändern.
Verfügbare Kräfte können sich zwischen den Physikmodi unterscheiden;
dies wird als Datenverfügbarkeit dargestellt, nicht durch andere
Zeichenregeln oder erfundene Ersatzbeiträge verdeckt.

Farben, Sichtbarkeit, Skalierungsmodus, Referenzen, Größen, Beschriftungen
und Vordergrund-/Raummodus folgen den Einstellungen. Ein Moduswechsel
setzt gemeinsame Darstellungsoptionen nicht unbemerkt zurück.
Die Regeln gelten auch bei gestopptem Timer, offener Werteübersicht
ohne laufende Simulation und beim erneuten Einblenden der Pfeile.

### 4.9 Aktualisierung und nicht abschließender Triggerkatalog — A-V0.11-00038

Jede Änderung einer fachlichen oder grafischen Abhängigkeit muss eine
passende Aktualisierung auslösen. Die folgende Liste nennt ausdrücklich
zu berücksichtigende Fälle, begrenzt den Geltungsbereich aber nicht:
Weitere vorhandene oder künftig ergänzte Eingabewege derselben
Abhängigkeiten unterliegen derselben Regel.

Es werden drei Arten unterschieden:

- **Fachlich:** Eingaben invalidieren, vorhandenen Physik-/Solverweg
  kontrolliert ausführen und einen neuen konsistenten Snapshot liefern.
  Keine Kraftberechnung im Renderer oder Tabellenmodell.
- **Ableitung:** Aus gültigen Quelldaten Frame-/Bezugstransformation,
  Gruppierung, Komponenten oder Formatierung neu ableiten, ohne erneut
  die Physik auszuwerten.
- **Grafisch:** Geometrie, Stil, Auswahl oder Projektion aus gültigen
  Anzeigedaten aktualisieren und ein Rendern anfordern.

| Nr. | Auslöser, ausdrücklich einschließlich | Erforderliche Reaktion |
|---|---|---|
| 1 | Erstes Laden einer Welt/eines Modells, Erzeugen oder Ersetzen eines Laufzeitkörpers | Fachlich initialisieren; Beiträge, Geometrie und Werte konsistent erstmals anzeigen |
| 2 | Wechsel des betrachteten Körpers, Hinzufügen/Entfernen eines Körpers, Modell-/Paket-/Konfigurationswechsel und erneutes Laden | Generation und Zuordnungen aktualisieren; alte Daten/Actors entfernen, neue Daten anfordern |
| 3 | Aktivieren/Deaktivieren physischer Komponenten oder Blätter, Änderung der Körperzusammensetzung | Fachlich neu aufbauen; Masse, Schwerpunkt, Trägheit und Beiträge nachführen; nicht mit bloßem Ausblenden verwechseln |
| 4 | Änderungen an Geometrie, Abmessungen, Material, Dichte, Masse, Ballast, Schwerpunkt, Trägheit oder hydrodynamischen Rollen | Fachlich invalidieren; betroffene Vorbereitungen/Caches und Momentenbezüge erneuern |
| 5 | Gelenkwinkel, Bauteiltransformationen oder andere Änderungen der relativen Modellgeometrie | Fachlich neu vorbereiten und auswerten, sofern physikalisch wirksam; sonst ausdrücklich rein grafisch behandeln |
| 6 | Physische Position, Orientierung, Eintauchtiefe, Krängung, Trimm, Störpose oder Wiederherstellen einer Pose | Fachlich neu auswerten; Angriffspunkte, Benetzung, Kräfte und Momente derselben Pose zuordnen |
| 7 | Lineare/angulare Geschwindigkeit, vorgegebene Anströmung oder Fluidgeschwindigkeit/-rotation | Vorhandene geschwindigkeitsabhängige Beiträge fachlich neu auswerten |
| 8 | Beschleunigung oder neue Verfügbarkeit von Beschleunigungsdaten | Vorhandenen Added-Mass-Anzeigebeitrag konsistent nachführen; niemals die Korrektur erneut in die Dynamik einrechnen |
| 9 | Ein-/Ausschalten einer Test-/Fremdkraft, Betrag, Azimut, Elevation, Komponenten oder Angriffspunkt | Fachlich aktualisieren, insbesondere sofort auch in statischer und pausierter Anzeige; gegebenenfalls neue Gleichgewichtssuche anstoßen |
| 10 | Ruderwinkel und Änderungen eines vorhandenen hydrodynamischen Testprofils | Betroffene Kraftmodelle/Ergebnisse invalidieren; statische/stationäre Auswertung oder pausierten Zustand nachführen |
| 11 | g, Wasserdichte, physikalischer Wasserstand sowie weitere vom bestehenden Modell tatsächlich verwendete Umgebungsparameter | Fachlich neu auswerten; rein optische Wasseranimation verändert keine Kräfte |
| 12 | Auswahl/Aktivierung eines Physikmodells, Widerstands-/Added-Mass-Parameter, Backend/Rechenpfad und relevante Solver-/Hydrostatikparameter | Ergebnisgeneration und Caches invalidieren; erforderlichen vorhandenen Rechenweg neu anfordern |
| 13 | Start oder erneuter Auftrag einer statischen/stationären Berechnung | Bisherige betroffene Anzeige unmittelbar als veraltet/in Berechnung kennzeichnen; kein Warten auf einen Animationstakt |
| 14 | Gültiger Solver-Zwischenstand, Abschluss, Nichtkonvergenz, Fehler oder Abbruch | Nur freigegebene konsistente Zwischenstände anzeigen; Abschluss übernehmen oder Fehler/veralteten Stand explizit kenntlich machen |
| 15 | Jeder akzeptierte dynamische Zustand mit zugehörigem Kraftergebnis bzw. neue Snapshot-Sequenz | Pfeile, Momente und Werte gemeinsam auf diesen Anzeigestand aktualisieren; Null-/Vorzeichenwechsel und verschwundene Beiträge einschließen |
| 16 | Wechsel zwischen Statik, stationärer Auswertung und Dynamik, Pause, Fortsetzen, Einzelschritt soweit vorhanden, Reset/Neustart | Zustands-/Zeitbezug aktualisieren; keine alten Modusdaten übernehmen; notwendige fachliche Initialisierung veranlassen |
| 17 | Während Pause/Statik geänderte fachliche Eingaben | Unabhängig vom Laufzeittimer fachliche Aktualisierung auslösen; Wiederaufnahme der Simulation ist nicht erforderlich |
| 18 | Wechsel des Anzeige-Frames, Momentenbezugs, Gesamt-/Komponentendarstellung oder der fachlichen Auswahl | Ableitungen und Hilfsgeometrie aus demselben gültigen Snapshot neu bilden; keine Solverneuberechnung für reine Anzeigeoptionen |
| 19 | Layer, Einzel-/Gruppensichtbarkeit, Kraft-/Momentenanzeige, Hilfspunkte, Quellen, Hebelarme oder Beschriftung ein-/ausschalten | Grafisch aktualisieren; beim Einblenden neuesten gültigen Stand nutzen; Bilanz und eingefrorene Skalen nicht ändern |
| 20 | Linear/Log, Referenzwert, „Neu einpassen“, Pfeil-/Bogenmaße, Kopf-/Strichgröße und individuelle Skalierung | Skalen-/Geometriecaches invalidieren, betroffene Pfeile und Legende neu darstellen |
| 21 | Gruppen-/Einzelfarbe, Linienart, Deckkraft, Kontur, Vordergrund-/Raummodus und Darstellungsprofil | Stil und betroffene Actors unmittelbar aktualisieren |
| 22 | Kamera drehen/verschieben/zoomen, Kamerapreset, Navigation/Folgekamera, Perspektiv-/Parallelprojektion, Kameraaustausch | Kamerabhängige Größen, Labels und Picking-Projektion nachführen; physikalische Vektoren unverändert lassen |
| 23 | Fenster-/Viewportgröße, Split-/Docklayout, Maximieren, DPI-/Monitorwechsel oder Bildschirm-Skalierung | Bildschirmgrößen, Projektion, Auswahlzone und Layout nachführen |
| 24 | Auswahl in 3D oder Wertefenster, Abwahl, Wechsel des ausgewählten Beitrags | Gemeinsame Auswahl, Quellenhervorhebung, Hebelarme und Detailwerte aktualisieren |
| 25 | Wertefenster/Ansicht öffnen, schließen, wieder öffnen, wieder sichtbar machen oder Renderer neu erzeugen | Neueste gültige Daten darstellen; keine doppelten Actors, Modelle oder Signalverbindungen erzeugen |
| 26 | Änderung von Anzeigeeinheiten, Genauigkeit oder Zahlenformat | Werte, Labels und Legende aus Originalwerten neu formatieren; keine Physikänderung |
| 27 | Einstellungen anwenden, zurücksetzen, Profil laden oder Konfiguration neu einlesen | Tatsächlich geänderte Abhängigkeiten bestimmen und fachliche bzw. grafische Aktualisierung wie oben auslösen |
| 28 | Gleiche Änderungen über GUI, Steuer-API, Skript, Import oder sonstigen vorhandenen Bedienweg | Dieselben zentralen Aktualisierungsregeln ausführen; keine nur an einzelne Widgets gebundene Sonderlogik |

Sobald gültige neue Daten oder Einstellungen vorliegen, wird die
Aktualisierung spätestens im nächsten GUI-Ereignis-/Renderzyklus
angefordert, auch ohne laufende Simulation. Teure fachliche Berechnungen
werden über die vorhandenen kontrollierten Rechenwege abgewickelt;
bis zum Ergebnis ist der alte Stand ausdrücklich als veraltet bzw.
„in Berechnung“ markiert oder ausgeblendet. Es dürfen keine neuen
Eingaben mit alten Kräften unmarkiert als konsistenter Zustand erscheinen.

Änderungsserien dürfen gebündelt werden, müssen aber den letzten
Eingabestand zuverlässig erreichen. Generation/Sequenz verhindern, dass
verspätete Solver-/Workerergebnisse neuere Eingaben überschreiben.
Eine reine Darstellungsänderung startet keinen Solver; eine fachliche
Änderung wird nicht mit einem bloßen Redraw als erledigt behandelt.
Ein unveränderter gültiger Snapshot benötigt keine wiederholte
Physikberechnung pro Bild.

**Vorhandene Anknüpfungspunkte:** Einstellungen, Moduswechsel,
Laufzeitkörperumbau, Solver-/Worker-Signale, Ruder- und Fremdkraftänderungen
in [hauptfenster.py](../../../../code/python/segelphysik/gui/hauptfenster.py)
sowie Pose-, Layer-, Stil-, Kamera- und Renderaktualisierungen in
[grafik_bruecke.py](../../../../code/python/segelphysik/grafik_bruecke.py).
Diese Einstiegsstellen sind zu integrieren, nicht als paralleles
Aktualisierungssystem zu duplizieren.

### 4.10 Körperumfang — A-V0.11-00043

Standardmäßig beziehen sich neue Kraft-/Momentenanzeige und Wertefenster
auf den ausgewählten Laufzeitkörper. Eine ausdrücklich zuschaltbare
Mehrkörperanzeige zeigt für jeden Körper einen getrennten Zweig mit
eigenem Schwerpunkt, Framebezug und Bilanzstatus. Körper-ID und Name
bleiben bei Auswahl und Hervorhebung eindeutig.

Die Auswahl als Betrachtungsobjekt darf nicht den physischen
Aktivierungszustand des Körpers ändern. Eine Summe über mehrere Körper
wird in diesem Umfang nicht eingeführt: Dafür müssten zusätzlich
Systemgrenze, innere/äußere Kräfte und gemeinsamer Momentenbezug
fachlich definiert werden. Skalenvergleich zwischen Körpern folgt
Abschnitt 5.4.

## 5. Grafische Darstellung der Pfeile

### 5.1 Kräfte — A-V0.11-00016

Gerader 3D-Pfeil vom fachlich bekannten Angriffspunkt in Richtung F.
Bei äquivalenter Darstellung wird der Anker anders markiert und als
„äquivalent“ beschriftet. Die Pfeilspitze ist keine Lage eines zweiten
physikalischen Punktes; ihre Länge ist ausschließlich eine Anzeigegröße.

Nullkräfte besitzen keinen Richtungspfeil. Sehr kleine von null
verschiedene Kräfte werden nicht durch eine Mindestlänge als groß
ausgegeben: eine eventuell vergrößerte Kleinwertdarstellung wird markiert.
Beschriftung und Detailwerte bleiben erreichbar.

**Werkzeuge:** vorhandenes `pfeil_fest` und Actor-Caching; PyVista/VTK
für Schaft und Kopf. [PyVista Arrow](https://docs.pyvista.org/api/utilities/_autosummary/pyvista.Arrow.html)
ist ein verfügbarer Geometriebaustein, aber keine fertige Lösung für
unabhängig bildschirmstabile Köpfe.

### 5.2 Momente — A-V0.11-00017

3D-Bogen senkrecht zum Momentenvektor, Mittelpunkt am benannten Bezug.
Standard-Bogenwinkel bleibt 240°. Drehsinn nach Rechte-Hand-Regel,
aus dem Momentenvektor abgeleitet; kein unabhängiges widersprüchliches
Vorzeichenfeld.

Standardmäßig ist der Gesamtmomentenvektor darstellbar. Komponenten x/y/z
können ergänzend eingeblendet werden und heißen ausdrücklich
„Komponente im Weltframe“ bzw. im ausgewählten Körperframe.
Gesamtvektor und Komponenten sind keine zusätzlichen Summanden.
Die Bezeichnungen Rollen/Nicken/Gieren beziehen sich auf entsprechend
ausgerichtete Körperachsen, nicht pauschal auf unveränderte Weltachsen.

Der Betrag wird standardmäßig über den Bogenradius kodiert; Dicke und
Winkel bleiben konstant. Nullmoment besitzt keinen gerichteten Bogen.
Ein reines Moment benötigt keine künstliche Quellkraft.

**Werkzeuge:** vorhandene Bogenhelfer und deren native Kerne; bei Bedarf
[vtkArcSource](https://vtk.org/doc/nightly/html/classvtkArcSource.html)
mit Normalenvektor und Winkel für allgemeine Momentenrichtungen.
Keine Neuberechnung von Physik durch den Geometrieerzeuger.

### 5.3 Bezug, Hebelarm und Quellen — A-V0.11-00018

Bei Auswahl werden Momentenbezug P, bekannte Angriffspunkte,
Kraftwirkungslinien und zugehörige Quellen hervorgehoben.
Für eine Einzelkraft ist der senkrechte geometrische Hebelarm:

```text
r = A − P
r_senkrecht = r − (r · F) / (F · F) · F    (F ≠ 0)
Hebelarmbetrag = |r_senkrecht|
```

Der Abschnitt von P zum Lotfuß auf die Wirkungslinie wird gestrichelt
gezeigt. Ein zusätzlicher Positionsvektor P→A ist anders beschriftet.
Der Abstand K−S darf nicht pauschal als wirksamer Hebelarm bezeichnet werden.
Für direkte Momente oder unbekannte Originalpunkte wird kein physischer
Hebelarm erfunden. Momentenrichtungslinien heißen nicht „Drehachse“,
solange keine entsprechende physikalische Bindung nachgewiesen ist.

**Werkzeuge:** vorhandene Linien-/Strichelungshelfer, PyVista `PolyData`
und bei Bedarf Tubes; Quellenbeziehungen aus dem Register.

### 5.4 Abbildung und stabile Maßstäbe — A-V0.11-00019 bis A-V0.11-00020

Für den nichtnegativen Betrag m und eine positive feste Referenz R:

```text
Linear:       u(m) = m / R
Logarithmisch: u(m) = log1p(m / m0) / log1p(R / m0)
m0 = R / 100
u_anzeige = min(1, max(0, u(m)))
```

Der Log-Modus ist nahe null stetig und benötigt keinen positiven
Minimalbetrag. Richtung und Vorzeichen stammen aus dem Originalvektor.
Die Kurven sind vor Begrenzung streng steigend; nach Begrenzung werden
Werte oberhalb R ausdrücklich als abgeschnitten gekennzeichnet.

Kraftpfeillänge bzw. Momentenradius ergibt sich aus `u_anzeige` mal
der jeweiligen Maximalgröße. Darstellungstechnische Mindestgrößen
dürfen weder Nullkräfte erzeugen noch unmarkiert die Abbildung verfälschen.

Entwurfsdefaults sind 180 logische Pixel maximale Kraftpfeillänge und
48 logische Pixel maximaler Momentenradius. Der Radius wird am
Momentenbezug in eine Weltgröße umgerechnet; Perspektive bleibt sichtbar.
Diese Layoutwerte werden im Mockup geprüft und bei einer Änderung hier
aktualisiert.

Referenzen werden beim ersten gültigen Datenstand je Körper gesetzt:
R_F mindestens max(m·g, größter vorhandener Kraftbetrag),
R_M mindestens größter vorhandener Momentenbetrag. Für eine Domäne mit
ausschließlich Nullwerten bleibt der positive Nutzerreferenzwert bestehen;
ohne Vorgabe gilt ein transparent angezeigter Startwert von 1 N bzw. 1 N·m.

Die Referenzen bleiben während des Laufs eingefroren. „Neu einpassen“
setzt R auf das 1,1-Fache des aktuellen größten gültigen Betrags aller
Beiträge und Summen der Domäne, unabhängig von der Sichtbarkeit; bei
ausschließlich null bleibt R unverändert. Referenzen sind manuell änderbar.
Kein automatisches Pumpen und keine Auto-Range-Hysterese in diesem Umfang.

Linear ist Standard, Log optional. Legende zeigt Modus, Referenz und
mindestens drei Referenzgrößen mit ihrer tatsächlich verwendeten
Abbildung. Bei körperübergreifendem Vergleich ist dieselbe ausdrücklich
gewählte Referenz zu verwenden; sonst werden körperbezogene Skalen
kenntlich gemacht.

**Werkzeuge:** `numpy.log1p`, zentraler Skalierungshelfer; keine neue
Skalierungsbibliothek erforderlich.

### 5.5 Bildschirmgrößen — A-V0.11-00021

Kopflänge zunächst 10, Schaft-/Bogenbreite 3 logische Pixel. Diese Größen
kodieren keinen Betrag. Köpfe kurzer Pfeile werden passend verkleinert;
sehr kleine Werte behalten ihre Kleinwertkennzeichnung.

Qt-DPI-Skalierung, perspektivische und parallele Kamera sowie
Fenstergrößenwechsel werden berücksichtigt. Bildschirmstabil meint
die kamerabezogene Größe am Anker, nicht eine erzwungene frontale
Ausrichtung aller Vektoren. Ein in Blickrichtung gerichteter Pfeil darf
physikalisch korrekt verkürzt erscheinen; Zahlen und Auswahl bleiben
verfügbar.

**Werkzeuge:**
[vtkDistanceToCamera](https://vtk.org/doc/nightly/html/classvtkDistanceToCamera.html)
oder äquivalente vorhandene Kameraumrechnung für Welt-/Bildschirmgröße.
Ein Skalieren des gesamten Pfeilmeshes allein erfüllt die unabhängige
Kopfgröße nicht.

### 5.6 Farben und Standardlayout — A-V0.11-00022

Die Tabelle gilt ohne bestehende explizite Nutzerüberschreibungen.
Kontrastkontur und Text sichern Erkennbarkeit auch bei ähnlichen Farben.
Farbe zeigt Gruppenzugehörigkeit; Betrag wird nicht zusätzlich über Farbe
oder Dicke kodiert.

| Gruppe / Darstellung | Farbe | Linienart und Kennzeichnung | Standard in 3D |
|---|---|---|---|
| Gewicht | Blau `#2166ac` | Durchgezogen, Label F_G | Ein |
| Auftrieb | Blau `#2166ac` | Gestrichelt, Label F_A | Ein |
| Gruppenmoment Gewicht/Auftrieb | Blau `#2166ac` | Bogen, Gruppenlabel | Aus |
| Hydrodynamik Rumpf | Orange `#e08214` | Durchgezogen, Rollenlabel | Aus |
| Hydrodynamik Kiel | Grün `#1b7837` | Durchgezogen, Rollenlabel | Aus |
| Hydrodynamik Ruder | Violett `#762a83` | Durchgezogen, Rollenlabel | Aus |
| Hydrodynamik Volumenkörper | Türkis `#008b8b` | Durchgezogen, Rollenlabel | Aus |
| Hydrodynamik-Summe | Orange `#e08214` | Summenzeichen im Label | Aus |
| Allgemeiner Widerstand | Grau `#707070` | Eindeutiges Widerstandslabel | Aus |
| Test-/Fremdkraft | Rot `#d73027` | Durchgezogen, Testkennzeichnung | Ein, falls vorhanden |
| Added Mass | Braun `#8c564b` | Beschrifteter Korrekturbeitrag | Aus |
| Gesamt-F / Gesamt-M | Hellgrau `#dddddd` mit dunkler Kontur | ΣF bzw. ΣM | Ein |
| Nicht zugeordnet | Magenta `#cc00cc` | Warnkennzeichnung und Originalname | Aus; Hinweis im Wertefenster |

Momente eines Quellbeitrags erben seine Farbe. Selektionskontur, Punktart
und Labels unterscheiden Kraft, Moment, Komponente und Summe.
Es wird kein Layout als Nachweis einer Kraft/Gegenkraft-Kopplung benutzt.

### 5.7 Sichtbarkeit und Auswahl — A-V0.11-00023 bis A-V0.11-00024

Der bestehende wählbare Vordergrundmodus bleibt erhalten und wird als
„durch Körper sichtbar“ kenntlich gemacht. Zusätzlich ist räumlich
tiefengeprüfte Darstellung verfügbar. Keine pauschale Abschaltung des
Tiefentests nur zwischen Pfeilen; verdeckte Kräfte bleiben über das
Wertefenster auswählbar.

Auswahl erfolgt zunächst per Klick. Eine zusätzliche Trefferzone von
6 logischen Pixeln um die projizierte Geometrie erleichtert das Treffen
dünner Pfeile. Bei mehreren Kandidaten werden diese zur eindeutigen
Auswahl angeboten, statt beliebig einen Beitrag zu wählen. Navigation
und bestehende Maustastenbelegung dürfen nicht unbemerkt geändert werden.

**Werkzeuge:** bestehende PyVista-/VTK-Picker und Qt-Auswahlanzeige.
Die [PyVista-Picking-Toleranz](https://docs.pyvista.org/api/plotting/_autosummary/pyvista.Plotter.enable_point_picking.html)
ist pickerabhängig und teils ein Anteil der Fensterdiagonale; sie darf
nicht ohne Umrechnung als Pixelwert verwendet werden.

### 5.8 Stabile Orientierung der Momentenbögen — A-V0.11-00044

Für jede Momenteninstanz wird eine deterministische Bogenbasis geführt.
Beim ersten Auftreten wird aus einer zur Achse ausreichend unabhängigen
Referenzrichtung eine orthonormale Basis gebildet. Bei nachfolgenden
gültigen Achsen wird die bisherige Basis auf die neue Bogenebene
projiziert und normalisiert; ist diese Projektion degeneriert, wird eine
deterministische Ersatzbasis gewählt. Die Basis ist Darstellungszustand,
kein zusätzlicher physikalischer Momentenwert.

Beim Vorzeichenwechsel ist die geometrische Phasenlage soweit möglich
beizubehalten; der Drehsinn folgt weiter dem Originalmoment.
Während eines Null-/grafischen Kleinwertzustands wird keine instabile
Richtung normalisiert. Eine bisherige Basis darf als interner
Darstellungscache erhalten bleiben, ohne einen nicht vorhandenen
Momentenpfeil anzuzeigen. Nach Körper-/Generationswechsel wird sie
verworfen. Tests umfassen kontinuierliche Achsenbewegung, nahezu
parallele Referenzachsen, antiparallele Achsen und Nulldurchgänge.

### 5.9 Beschriftungsprioritäten — A-V0.11-00045

Im Standardlayout erhalten ausgewählte Beiträge Vorrang, danach
Gesamtsummen. Beschriftungen aller Einzelbeiträge werden nicht dauerhaft
erzwungen. Eine Option kann weitere Labels einblenden; Überschneidungen
werden durch begrenztes Versetzen oder Unterdrücken niedriger
priorisierter Labels reduziert, ohne ihre physikalischen Anker zu
verschieben. Versetzte Labels erhalten bei Bedarf Verbindungslinien.

Quellen- und Hebelarmerklärungen erscheinen vorrangig zur Auswahl.
Ausgeblendete Labels bedeuten keinen ausgeblendeten Bilanzbeitrag.
Alle Werte und Quellen bleiben unabhängig von Labelplatz und
Verdeckung im Wertefenster erreichbar. Tests umfassen dichte
Pfeilgruppen, lange Namen sowie kleine Fenster und hohe DPI.

## 6. Darstellung der Werte

### 6.1 Freifliegendes Fenster — A-V0.11-00025

Ein Fenster „Kräfte und Momente“, frei schwebend und optional andockbar,
zeigt die aktuelle Körper-/Gruppenhierarchie. Es ist schließbar und
erneut öffnbar, ohne Simulationszustand oder aktuelle Auswahl zu zerstören.
Körperwechsel, Pause und Reset werden eindeutig abgebildet.

**Werkzeuge:** vorhandenes PySide6, `QDockWidget`, `QTreeView` und ein
schlankes `QAbstractItemModel` als `KraefteWerteModell`. Keine neue
GUI-Bibliothek und keine zweite unabhängige Datenliste.

### 6.2 Werte, Status und Format — A-V0.11-00026 bis A-V0.11-00027

Die Kopfzeile zeigt Körper, physikalische Zeit, Snapshot-Sequenz,
Frame, Momentenbezug und Verfügbarkeit/Aktualität.

| Bereich / Spalte | Inhalt |
|---|---|
| Name / Gruppe | Lesbare Hierarchie und stabile Identität |
| Sichtbar | Anzeigeoption für 3D; beeinflusst keine Physiksumme |
| Kraft | F_x, F_y, F_z und Betrag mit N bzw. kN |
| Moment um P | M_x, M_y, M_z und Betrag mit N·m bzw. kN·m |
| Punkt | Koordinaten plus Punktart: realer Angriff, Bezug oder äquivalent |
| Quelle / Status | Physikquelle, Summe/Komponente, aktiv/null/fehlend/ungültig/veraltet |
| Details der Auswahl | Quellen, Formel, Einzelmomente, Frame, Bezug und Originalwerte |

Summen sind optisch als Summen markiert; sie zählen nicht erneut in ihre
Elterngruppe. Es muss möglich sein, alle vorhandenen Beiträge zu sehen,
auch wenn ihre 3D-Pfeile ausgeblendet sind.

Kompaktanzeige mit vier signifikanten Stellen, deutsch lokalisierter
Zahlenformatierung und eindeutigem Einheitenpräfix. Details bieten die
zugrunde liegenden Werte mit bis zu 17 signifikanten Stellen.
Gerundete Anzeige behauptet keine zusätzliche physikalische Genauigkeit.

Kleine von null verschiedene Werte werden nötigenfalls wissenschaftlich
geschrieben, nicht als physikalisch exakte Null dargestellt.
Unterschiedliche Zustände erhalten Text statt bedeutungsloser Leerzellen:
beispielsweise „nicht berechnet“, „deaktiviert“ und „ungültig“.

**Werkzeuge:** PySide6-Modell/View und bestehende Lokalisierungs-/
Formatierungshilfen; interne SI-Werte bleiben unverändert.

### 6.3 Gemeinsame Interaktion — A-V0.11-00028

Auswahl einer Wertezeile hebt denselben Beitrag in 3D hervor und
umgekehrt. Bei einem Moment werden seine verfügbaren Quellen und
Hilfsgeometrien nach Abschnitt 5.3 angezeigt. Verdeckte oder ausgeblendete
Pfeile lassen sich über eine ausdrücklich angebotene Anzeigeoption
sichtbar machen; die Auswahl verändert keine Bilanz.

Berechnete Physikwerte sind hier schreibgeschützt. Bestehende
Testkraft-Eingaben bleiben in ihrem bisherigen Bedienweg und erzeugen
einen neuen physikalischen Zustand statt einer lokalen Tabellenkorrektur.

### 6.4 Mockup — A-V0.11-00029

Vor produktiver Anbindung wird ein Mockup des Wertefensters mit
gekennzeichneten synthetischen Beispieldaten vorgelegt. Es zeigt
Gruppen, Summen, Kraft-/Momentenkomponenten, Punktarten, Auswahl,
Sichtbarkeit und mindestens einen fehlenden/ungültigen Datenzustand.

Das Mockup wird auf Verständlichkeit und nutzbare Größe abgestimmt.
Es ist kein neues Kraftmodell und keine zusätzliche Spezifikation.
Layoutänderungen werden anschließend in dieser Datei nachgeführt.

#### Abgestimmte Prinzipdarstellung

Der Nutzer hat am 20.10.2026 das
[gerenderte Mockup des Wertefensters](Mockup_Wertefenster.html)
als Prinzipdarstellung für diese Spezifikation bestätigt. Die Zustimmung
betrifft Aufbau und Darstellungsprinzip, nicht eine pixelgenaue Gestaltung,
die physikalische Gültigkeit der synthetischen Beispieldaten oder eine
bereits erfolgte Implementierungsabnahme.

| Fensterbereich | Übernommenes Darstellungsprinzip |
|---|---|
| Kopfbereich | Körper, Frame, Simulationszeit, Snapshot und Momentenbezug sichtbar; Datenaktualität und Schreibschutz erkennbar |
| Bilanzübersicht oben | Karten für Betrag und Komponenten von Gesamt-F und Gesamt-M sowie den Bilanzstatus |
| Haupttabelle in der Mitte | Körper-/Gruppenhierarchie mit Einzelbeiträgen und klar markierten Summen; x-/y-/z-Komponenten, Einheiten, Punktart und Status |
| Sichtbarkeit | Zugeordnete Checkboxen für die 3D-Anzeige; Ausblenden verändert keine physikalische Bilanz |
| Detailbereich unten links | Ausgewählter Beitrag mit Quelle, Kraft-/Momentenbetrag, Angriffspunkt, Bezugspunkt, senkrechtem Hebelarm und nachvollziehbarer Momentenableitung |
| Erläuterungsbereich unten rechts | Aktueller Skalierungsmodus und Referenzen sowie Hinweise zu Summen, Sichtbarkeit und fehlenden Werten |
| Fehlende oder deaktivierte Beiträge | Explizite Textkennzeichnung statt scheinbarer Nullwerte; Umfang der tatsächlich verfügbaren Bilanz sichtbar |

Das HTML-Mockup ist eine unterstützende Layoutreferenz, keine zweite
GUI-Codebasis. Die produktive Umsetzung erfolgt wie in Abschnitt 6.1
mit PySide6 und dem gemeinsamen Datenmodell, nicht durch Einbetten einer
zusätzlichen Browseroberfläche. Farben, Abstände und Spaltenbreiten dürfen
an das vorhandene Qt-Layout angepasst werden, solange Informationsgehalt,
Gruppierung und Bedienprinzip erhalten bleiben.

### 6.5 Persistenz — A-V0.11-00046

Die vorhandene Settings-Struktur speichert Farben, Linien-/Größenoptionen,
Sichtbarkeit, Skalierungsmodus und manuell gesetzte Referenzen sowie
Fenstergeometrie, Dockzustand und Spaltenlayout. Körperbezogene Optionen
werden nur bei stabiler Körper-/Definitions-ID wieder zugeordnet.
Eine automatisch aus einem Snapshot gewählte Referenz wird nicht
unbemerkt als dauerhafte manuelle Referenz gespeichert.

Aktuelle Kräfte, Momente, Solverstatus, Snapshot-Sequenzen,
Veraltetkennzeichnungen und temporäre Auswahl werden nicht als
Wiederherstellung eines gültigen physikalischen Zustands gespeichert.
Nach dem Laden gelten neue Daten erst nach fachlicher Initialisierung.

Ungültige Einstellungen werden über die vorhandene Validierung mit
Meldung behandelt. Alte ersetzte Schlüssel werden nachvollziehbar
migriert, nicht parallel weiter gepflegt. Ein auf einem nicht mehr
vorhandenen Monitor gespeichertes Fenster wird erreichbar platziert.
Abnahme: Einstellungen ändern, Anwendung neu starten, Wiederherstellung
und Standardwerte-Reset prüfen, einschließlich Monitorwechsel.

### 6.6 Aktualisierungstakt und Bündelung — A-V0.11-00047

Die zentrale Datenhaltung übernimmt den neuesten gültigen Snapshot.
In laufender Simulation dürfen ausstehende noch nicht angezeigte
Snapshots durch neuere derselben gültigen Generation ersetzt werden;
eine anwachsende Warteschlange sämtlicher Simulationsschritte ist
unzulässig. Ein angezeigter Zyklus veröffentlicht 3D-Kräfte und
Wertetabelle atomar aus derselben Snapshot-Sequenz.

Kontinuierliche Datenaktualisierungen erfolgen höchstens im vorhandenen
GUI-Anzeigetakt, nicht pro Integrationsschritt. Grafik kann für
Kamerabewegungen öfter neu gerendert werden, ohne neue Physikdaten zu
publizieren. Besteht kein Anzeigetakt, wird für neue Daten genau eine
GUI-Aktualisierung angefordert. Die konkrete Taktrate wird anhand
der Vergleichsmessungen aus Abschnitt 7.4 festgelegt und dokumentiert.

In Statik und Pause sind gültige neue Daten und reine Anzeigeänderungen
im nächsten möglichen GUI-Zyklus zu veröffentlichen; sie dürfen nicht
auf einen zukünftigen Simulationsschritt warten. Bei gebündelten
Änderungsserien muss der letzte Zustand zuverlässig erscheinen.
Fehler- und Ungültigkeitsmeldungen dürfen durch die Bündelung nicht
verschwinden, sondern bleiben im vorhandenen Protokoll nachvollziehbar.

Abnahme: schnelle Folge von Eingaben und Worker-Ergebnissen,
begrenzte Queue, übereinstimmende Sequenzen in 3D und Tabelle sowie
zuverlässige letzte Aktualisierung bei gestopptem Timer.

## 7. Prüfung und Abnahme

### 7.1 Physikalische Referenzfälle — A-V0.11-00030

Numerische Adapter-/Aggregationsfälle werden mindestens mit
`rtol=1e-10` und `atol=1e-9` in der jeweiligen SI-Größe verglichen.
Diese Grenzen gelten für die angegebenen kleinen algebraischen
Referenzfälle, nicht als neue Freigabegrenzen der gesamten Simulation.

| Fall | Erwartetes Ergebnis |
|---|---|
| Einzelkraft durch S: F=(0,0,10) N, M_A=0 | M_S=(0,0,0) N·m; kein erfundenes Gegenkraftpaar |
| Kraft bei A−S=(0,0.35,0) m: F=(0,0,10) N | M_S=(3.5,0,0) N·m |
| Gleiches Kräftepaar an verschiedenen Punkten | Resultierende Kraft null; Moment bleibt bei Bezugspunktwechsel gleich |
| Ungleiches Gewicht/Auftrieb | Tatsächliche resultierende Kraft bleibt erhalten; keine automatische Angleichung |
| Reines Moment F=0, M=(0,0,5) N·m | Momentenbogen, keine Kraftwirkungslinie |
| Wrench F=(0,0,10) N, M_S=(2,0,3) N·m | A_eq−S=(0,+0.2,0) m; M_rest=(0,0,3) N·m |
| Beispiel aus der Idee: A−S=(0.10,0.35,−0.30) m, F=(0,0,49050) N | M_S=(17167.5,−4905,0) N·m, nicht ausschließlich x |
| Gewicht bereits enthalten / noch nicht enthalten | In beiden Adaptervarianten genau eine Gewichtskraft in der dargestellten Bilanz |
| Mehrere gleichnamige Hydrodynamikbeiträge | Eindeutige Instanzen, keine verlorenen oder doppelt addierten Beiträge |
| Summen und Komponenten zusätzlich eingeblendet | Physikalische Gesamtbilanz unverändert |
| Verteilte Kräfte mit Restmoment | Äquivalente Grafik rekonstruiert den vollständigen ursprünglichen Wrench |
| Körper-/Welttransformation | Gedrehte Vektoren und verschobene Punkte korrekt; Bezugspunktwechsel kommutiert fachlich korrekt mit Framewechsel |

Skalierungstests prüfen null, sehr kleine Werte, R, Werte oberhalb R,
ungleiche Größenordnungen, identische Beträge und ungültige Referenzen.
`u(0)=0`, `u(R)=1`, Monotonie vor Begrenzung und Grenzkennzeichnungen
müssen in beiden Modi nachgewiesen sein.

### 7.2 Lifecycle und Rechenpfade — A-V0.11-00031

Statische Auswertung, stationärer Zustand und laufende Dynamik werden
mit den tatsächlich verfügbaren Ergebnisverträgen geprüft.
Python- und C++-Pfad werden berücksichtigt, soweit vorhanden.
Fehlende Quelldaten müssen ausdrücklich sichtbar bleiben.

Tests umfassen Nullkräfte, Vorzeichenwechsel, aktive/inaktive Modelle,
Added-Mass-Verfügbarkeit, Körperwechsel, Reset, Pause, Wiederaufnahme und
veraltete Worker-Ergebnisse. Keine verdeckte GUI-Physikauswertung,
keine alten Actors oder Werte nach Modellgenerationenwechsel.

Für A-V0.11-00037 und A-V0.11-00038 wird jeder anwendbare Trigger aus
Abschnitt 4.9 in statischer Anzeige und pausierter Dynamik ausdrücklich
geprüft, soweit der jeweilige Bedienweg dort existiert. Laufende Dynamik
und stationäre Auswertung werden ergänzend geprüft. Nicht anwendbare
Fälle werden mit Begründung dokumentiert; zusätzliche entdeckte Trigger
werden in die Nachweismatrix aufgenommen.

Nachweise umfassen mindestens: Stil- und Fremdkraftänderung bei
gestopptem Timer sichtbar, fachliche Änderung führt zu aktuellem
Ergebnis oder sichtbarem Wartezustand, schnelle Änderungsfolgen behalten
den letzten Stand, verspätete Ergebnisse werden verworfen und reine
Kamera-/Stiländerungen rufen keine Kraftfunktion auf. Identische
Test-Snapshots und Einstellungen erzeugen in Statik und Dynamik gleiche
Darstellungsdaten; hierfür werden eine feste manuelle Skalenreferenz und
derselbe initialisierte Darstellungszustand der Bogenbasis benutzt.

### 7.3 Sichtbare Abnahme — A-V0.11-00032

Sichtbare Tests bei 100 %, 150 % und 200 % DPI, perspektivischer und
paralleler Kamera, verschiedenen Zoomstufen und Fenstergrößen.
Kopf-/Strichgrößen werden in einer nicht verkürzten Testlage mit
höchstens 1 logischem Pixel Abweichung von der Sollgröße geprüft.

Zusätzlich: Blick entlang eines Vektors, sich überlagernde Pfeile,
verdeckte Beiträge, Vordergrund-/Raummodus, reine Momente,
Null-/Kleinwertanzeige, Auswahlzone und Mehrfachtrefferauswahl.
Fenster und 3D müssen denselben Beitrag und Snapshot ausweisen.
Ein offscreen-Test allein belegt nicht die gesamte sichtbare Bedienung.

### 7.4 Laufzeit und Ressourcen — A-V0.11-00033

Vorher-/Nachher-Messungen mit identischem Modell, Rechenpfad, Fenster,
Hardware und Simulationszustand; Anzeige aus/ein sowie viele Beiträge.
Erfasst werden Aktualisierungsdauer, Frameabstände, Actoranzahl und
Speicherentwicklung bei wiederholten Körper-/Fensterwechseln.

Keine vollständige Neuerzeugung aller Meshes und Tabellenzeilen pro
Frame ohne technischen Grund. Caches und begrenzte Aktualisierung auf
neue Snapshots nutzen; Anzeige darf den Worker nicht blockieren.
Ein
[vtkGlyph3DMapper](https://vtk.org/doc/nightly/html/classvtkGlyph3DMapper.html)
ist bei nachgewiesenem Bedarf eine Option, keine vorgeschriebene neue
Architektur.

Da hierfür noch keine neue Baseline vorliegt, wird keine erfundene
FPS-/Zeitgrenze als bereits abgesichert behauptet. Vergleichsbelege und
etwaige Verschlechterungen sind vor Abnahme vorzulegen; erforderliche
Grenzwerte oder akzeptierte Abweichungen entscheidet der Nutzer anhand
der Messungen. Offene Leistungskriterien sind keine bestandene Abnahme.

### 7.5 Nachweismatrix — A-V0.11-00034

Der [gemeinsame Umsetzungsplan](Umsetzungsplan_V0.11.md) ordnet allen aktiven A-IDs
Umsetzungsschritte und konkrete Tests/Abnahmekriterien zu.
Ergebnisse, Befehle, Umgebung, Messstände, Skips und offene Fehler
werden nachvollziehbar belegt. Build, implementierte Funktion,
sichtbare Darstellung und fachliche Abnahme sind getrennte Nachweise.

Bestehende passende pytest-Tests werden erweitert; für die produktive
Umsetzung gelten die projektüblichen Regressionstests und bei nativen
Änderungen Build-/Schnittstellennachweise. Fremde historische
Ausnahmefreigaben gelten nicht automatisch für V0.11.

### 7.6 Vergleich mit der verwendeten Solver-/Integratorbilanz — A-V0.11-00048

Die Anzeige wird nicht nur gegen ihre eigene Summe geprüft. Für denselben
physikalischen Zustand, Modellgeneration, Auswertungszeitpunkt,
Geschwindigkeits-/Beschleunigungsstand, Frame und Bezugspunkt werden
Gesamt-F und Gesamt-M mit der tatsächlich vom Solver bzw. Integrator
verwendeten Bilanz verglichen. Bei mehrstufigen Integratoren sind
Zwischenauswertung und akzeptierter Endzustand ausdrücklich zuzuordnen;
ein Vergleich unterschiedlicher Stufen ist kein Paritätsnachweis.

Gewicht wird in beiden Vergleichsseiten genau einmal berücksichtigt.
Bei Added Mass ist zu dokumentieren, ob der Rechenkern die Korrektur als
ausgewiesenen Beitrag oder als Teil der effektiven Trägheit behandelt.
Es werden nur äquivalente Bilanzformen verglichen: Eine nachträglich
berechnete Added-Mass-Kraft darf nicht ohne diese Umrechnung mit
einer unkorrigierten äußeren Kraftsumme verglichen werden.
Die Anzeige ändert dafür nicht das Integrationsverfahren.

Zusätzlich muss die vollständige angezeigte atomare Auflösung die
ausgewiesene Gesamtbilanz rekonstruieren. Fehlen die dazu nötigen
Diagnosedaten, bleibt dieser Nachweis offen und die Einzelauflösung
ist als unvollständig gekennzeichnet; eine intern passende Teilsumme
ersetzt keine Parität zum Solver.

Die algebraischen Referenzfälle verwenden Abschnitt 7.1. Für reale
Rechenpfade gelten deren bestehende fachlich begründete
Vergleichstoleranzen; Quelle und Werte werden im Prüfprotokoll genannt.
Fehlen geeignete Grenzen, sind sie vor Abnahme explizit festzulegen,
nicht still aus Grafikschwellen abzuleiten. Erforderliche Nachweise
umfassen Statik, stationäre Auswertung und Dynamik sowie vorhandene
Python-/C++-Pfade, jeweils mit aktivem Gewicht, Widerstand,
Hydrodynamik und Added Mass soweit im betreffenden Modus verfügbar.

## 8. So nicht umsetzen

Diese Einträge archivieren verworfene Ansätze aus dem Ideendokument
unter dessen ursprünglichen Kennungen. Es wurden dafür keine aktiven
V0.11-Anforderungskennungen vergeben.

| Ursprüngliche Kennung / Ansatz | Nicht übernehmen, weil |
|---|---|
| KO-02: pauschal neuer Ursprung „Kielmitte“ | Vorhandene Frames und Bezugspunkte dürfen nicht durch einen unbelegten Universalursprung ersetzt werden. |
| C-05.5, C-05.7, B-01, E-03–05: STARR-Kopplung von Auftrieb und Gewicht | Keine allgemeine physikalische Gleichheit und kein Newtonsches Gegenkraftpaar auf demselben Körper. Das Zahlenbeispiel bleibt nur als ausdrücklich angenommener Gleichgewichtsfall zulässig. |
| B-02: grundsätzlich nie speichern, in jedem Frame neu berechnen | Konsistente Snapshots und Caching sind erlaubt; keine zweite unabhängige GUI-Physik. |
| S-03: Betrag ausschließlich durch Dicke bei konstantem Radius | Für vergleichbare Momentengrößen zu schlecht ablesbar; stattdessen Radius und Zahlenwert bei konstanter Dicke. |
| S-04: laufend automatische Bereichsanpassung | Zunächst fixierte, ausdrücklich neu einpassbare Maßstäbe ohne Pumpen. |
| R-09: kein Tiefentest zwischen Pfeilen als feste Regel | Keine eindeutige räumliche Ordnung; bewusste Raum-/Vordergrundmodi statt Sonderregel. |
| I-02: editierbare berechnete Kräfte mit Gegenkraftsperre | Physikwerte bleiben Anzeige; Testkraftänderungen erfolgen über vorhandene Eingabefunktionen. |
| E-06: ausschließliches x-Moment bei den genannten Koordinaten | Der x-Versatz erzeugt zusätzlich ein y-Moment. |
| E-07: frei erfundenes Wellenmoment und daraus abgeleiteter Drehpunkt | Keine bekannte produktive Quelle nachgewiesen; ein reines Moment beweist keinen Zwangsdrehpunkt. |

## 9. Quellen und Werkzeugrahmen

Die werkzeugbezogenen Links stehen unmittelbar bei den betreffenden
Anforderungen. PySide6, NumPy, PyVista und VTK sind vorhandene
Projektbausteine; eine neue große Bibliothek ist nicht erforderlich.
VTK beschreibt seine freie Nutzung unter einer BSD-artigen Lizenz auf
der [Projektseite](https://vtk.org/about/). Bei Übernahme konkreten
Beispielcodes sind dessen jeweilige Lizenz und Hinweise zu beachten.

Frei zugängliche
[PyVista-Glyph-Beispiele](https://docs.pyvista.org/examples/01-filter/glyph.html)
können Orientierung geben, ersetzen aber weder das Beitragsregister
noch die physikalischen Datenverträge und Abnahmetests.
