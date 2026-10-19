# Umsetzungsplan zuV0.9: Modellpakete, Seglermasse und Echtzeitverhalten

**Stand:** 19.10.2026  
**Version:** zuV0.9  
**Status:** Technischer Integrationsstand geprüft; Kandidatenentscheidungen dokumentiert; pädagogische Nutzerabnahme ausdrücklich offen  
**Zugehörige Spezifikationen:**

- [Modellpakete und Segler-Massenkörper](../Spezifikationen/Spezifikation_Modellpakete_und_Seglerkoerper_v0.9.md)
- [Echtzeitberechnung und Darstellung als Schulungstool](../Spezifikationen/Spezifikation_Echtzeitberechnung_und_Darstellung_v0.9.md)

## 1. Zweck und verbindliche Grenzen

Dieser Plan ordnet die Umsetzung aller aktiven Anforderungen aus beiden
Spezifikationen in abhängige und prüfbare Arbeitsschritte. Jeder Schritt hat
eine versionsbezogene Kennung `U-V0.9-…` und verweist auf mindestens eine
Anforderung `A-V0.9-…`.

Die Arbeitsschritte beschreiben erforderliche Ergebnisse und Nachweise,
nicht die Annahme, dass im Repository noch keine Umsetzung existiert.
Vor neuen Änderungen ist der vorhandene Code einschließlich Tests gegen die
Abschlusskriterien zu prüfen; bereits erfüllte Punkte werden mit Nachweis
aktualisiert statt erneut implementiert.

SegelPhysik wird in diesem Umfang als Schulungs- und Anschauungstool behandelt,
nicht als Engineering-Simulation, Konstruktions-/Sicherheitsnachweis oder
Race-Optimizer. Geschwindigkeit allein ist kein Freigabekriterium. Bestehende
Physik und numerische Toleranzen bleiben Referenz, wenn ein Optimierungsschritt
den Algorithmus und die physikalischen Annahmen nicht ändert.

Für einen pädagogisch begründeten Näherungspfad gibt es keine pauschale
Genauigkeitsgrenze. Vor dessen Implementierung müssen Lernziel, betroffene
Messgrößen, Referenzfälle, absolute und/oder relative Grenzen und sichtbare
Kennzeichnung festgelegt und freigegeben sein. Diese Kriterien dürfen nicht
nachträglich gelockert werden, um ein Ergebnis zu akzeptieren. Nicht
verifizierte Modellgeometrie oder Kalibrierung ist nicht mit numerischer
Rechenabweichung gleichzusetzen und muss als Modellgrenze erkennbar bleiben.

Die Zielhardware für die Leistungsabnahme ist der Nutzer-PC mit AMD Ryzen 5
8600G, 32 GB RAM und Radeon 760M. NPU und integrierte GPU werden als getrennte
Rechenressourcen behandelt. Eine NPU-Abhängigkeit ist nicht zulässig.

## 2. Abhängigkeiten und Reihenfolge

Die Arbeit wird in vier Meilensteinen durchgeführt:

1. **M1 – Modellverträge:** Paketkatalog/-validierung und Segler-Massenkörper.
2. **M2 – Mess- und Genauigkeitsgrundlage:** Grenzwertvorschläge und
   ausdrückliche Nutzerfreigabe, verbindliche Lernziel-/Fehlerbudgets sowie
   reproduzierbare Echtzeit-Baseline.
3. **M3 – gezielte Kandidaten:** Rendering, CPU/exakter Unionpfad,
   Hydrostatik-Wiederverwendung und NPU-Machbarkeit, jeweils nur nach
   passendem Messbefund.
4. **M4 – integrierte Abnahme:** Regression, Spezifikationsmatrix und
   Dokumentation der offenen bzw. nicht lohnenden Kandidaten.

Die Startschritte U-V0.9-000001, U-V0.9-000010 und U-V0.9-000004 sind
voneinander unabhängig und können separat begonnen werden. U-V0.9-000002
benötigt den manifestbasierten Modellvertrag aus U-V0.9-000001.
U-V0.9-000010 erarbeitet Grenzwertvorschläge zur Prüfung durch den Nutzer.
Erst nach dessen ausdrücklicher Freigabe übernimmt U-V0.9-000003 die
freigegebenen Grenzen in verbindliche Fehlerbudgets und Prüfkriterien.
U-V0.9-000005 bis U-V0.9-000008 benötigen eine gültige Baseline aus
U-V0.9-000004. Jeder Kandidat, der Ergebnisse näherungsbehaftet verändert,
benötigt zusätzlich die Freigabekriterien aus U-V0.9-000003. U-V0.9-000009
schließt die vorherigen Schritte ab.

U-V0.9-000010 ist vor U-V0.9-000003 sachlich eingefügt. Seine Kennung ist
die nächste unbenutzte U-ID; bestehende Kennungen bleiben unverändert.

## 3. Umsetzungsschritte

### U-V0.9-000001 — Paketkatalog und Manifestvalidierung

**Anforderungen:** `A-V0.9-00001`  
**Abhängigkeiten:** keine  
**Aufwand:** mittel

Automatische Erkennung direkter Modellunterverzeichnisse mit gültigem
`modell.json` als verfügbare Modelle absichern. Manifest bleibt für Paketname,
Baum, Geometrien, Rollen, Posen, Massen und Darstellung maßgeblich.
Konfigurationsdateien dürfen bestehende Overrides liefern, aber keine
zusätzliche Registrierung voraussetzen. Modellwurzel muss
arbeitsverzeichnisunabhängig aufgelöst werden.

Ungültige Manifeste, fehlende Geometrien und doppelte IDs sind sichtbar als
Fehler zu behandeln. Bestehende Modelle, Overrides und Migration bleiben
funktionsfähig.

**Prüfung und Abschlusskriterien**

- Regressionstests belegen Paket-Erkennung ohne Eintrag in
  `konfigurationen/koerper.json`, Aufnahme aller Manifestblätter und
  Aufbau eines gültigen Laufzeitkörpers.
- Fehlerfälle für ungültiges Manifest, fehlende Datei und doppelte ID werden
  explizit geprüft.
- Bestehende Katalog-, Loader- und Override-Tests bestehen.

**Meilenstein:** M1.

### U-V0.9-000002 — Segler-Masse, Pose und persistente Einstellung

**Anforderungen:** `A-V0.9-00002`  
**Abhängigkeiten:** U-V0.9-000001  
**Aufwand:** mittel bis hoch

Für jedes freigegebene Segelbootmodell einen eindeutig identifizierbaren
Massenkörper `segler` im Modellbaum und ein modellbezogenes Gewicht sowie
eine Position relativ zum ausdrücklich definierten rumpfzentrierten
Referenzpunkt vorsehen. Die drei rumpffesten Koordinaten müssen vor der
Simulation konfigurierbar und für weitere statische und dynamische Läufe
desselben Modells persistent sein.

Die Seglermasse wird als starr an den Rumpf gebunden in Gesamtmasse,
Schwerpunkt und Trägheit einbezogen. Sie erhält weder autonome Integration
noch zusätzliches verdrängendes Volumen. Der Optimist-Referenzfall verwendet
etwa 50 kg; andere Bootsmodelle benötigen eigene ausgewiesene Werte.

**Prüfung und Abschlusskriterien**

- Tests ändern Masse sowie jede einzelne Positionskoordinate und prüfen die
  korrekte Änderung von Gesamtmasse, Schwerpunkt und Trägheit.
- Persistenz wird über Neustart bzw. erneutes Laden und über Wechsel
  statisch/dynamisch nachgewiesen.
- Es ist nachgewiesen, dass die Seglermasse nicht separat integriert wird
  und keinen zusätzlichen Auftriebskörper bildet.
- Der Optimist-Referenzwert und der explizit definierte rumpfzentrierte
  Bezugspunkt sind dokumentiert; bestehende Modelle ohne Segler bleiben in
  der Migrationsphase ladbar.

**Meilenstein:** M1.

### U-V0.9-000010 — Pädagogische Genauigkeitsgrenzen vorschlagen und Nutzerfreigabe einholen

**Anforderungen:** `A-V0.9-00009`  
**Abhängigkeiten:** keine  
**Aufwand:** niedrig bis mittel

**Freigegebene Vorlage:** [Genauigkeitsgrenzen, Fassung 1](Genauigkeitsvorschlaege_v0.9.md).
Der Nutzer hat Fassung 1 am 19.10.2026 vollständig freigegeben.
Bis zum Abschluss v0.9 sind Lockerungen ausgeschlossen, auch auf Wunsch
des Nutzers. Bestehende exakte Regressionstoleranzen bleiben unverändert.

Vor der verbindlichen Festlegung der Fehlerbudgets begründete Vorschläge
für pädagogisch sinnvolle Genauigkeitsgrenzen erarbeiten und dem Nutzer
zur Prüfung, Änderung und ausdrücklichen Freigabe vorlegen. Maßstab sind
die Lernziele eines Schulungs- und Anschauungstools, nicht die Anforderungen
einer Engineering-Simulation oder eines Race-Optimizers.

Die Vorschlagsvorlage enthält je betroffener Messgröße:

- Lernziel und Unterrichtsszenario sowie die Zusammenhänge, Vorzeichen
  und Größenordnungen, die durch eine Näherung erhalten bleiben müssen.
- Messgröße, Einheit, Gültigkeitsbereich und begründeten Vorschlag für
  absolute und/oder relative Abweichungen; bei Werten nahe null eine
  geeignete absolute Grenze statt einer alleinigen Prozentangabe.
- Referenzverfahren und Standard-, Grenz- und Wechselfälle, mit denen die
  Eignung später geprüft wird.
- Begründung der Grenze, bekannte Modellunsicherheiten und erwarteten
  Nutzen einer Vereinfachung; noch nicht gemessene Vorteile sind als
  Erwartungen zu kennzeichnen.
- Wo sinnvoll mehrere Alternativen mit Genauigkeits-/Aufwandsabwägung
  und einer Empfehlung sowie die vorgesehene Nutzerkennzeichnung.

Die Vorschläge sind keine Freigabe und rechtfertigen weder eine Änderung
bestehender numerischer Regressionstoleranzen noch die vorzeitige
Implementierung eines Näherungspfads.

**Prüfung und Abschlusskriterien**

- Die Vorlage trennt numerische Rechenabweichungen von Unsicherheiten
  geschätzter Geometrie-, Massen- oder Kalibrierungsdaten.
- Der Nutzer erhält die Vorschläge vor Umsetzung der betroffenen Näherung.
  Seine Entscheidung wird je Grenzwertsatz mit freigegebenem Wert,
  Gültigkeitsbereich, Datum und eindeutiger Fassung dokumentiert.
- Ohne ausdrückliche Freigabe bleibt der betroffene Grenzwertsatz offen;
  Schweigen oder die Freigabe des Umsetzungsplans gilt nicht als
  Grenzwertfreigabe. Abgelehnte oder zu überarbeitende Vorschläge werden
  entsprechend gekennzeichnet und nicht angewendet.
- Nur freigegebene Grenzwertsätze werden an U-V0.9-000003 übergeben.
  Bis zum Abschluss v0.9 sind Lockerungen der freigegebenen Fassung 1
  ausgeschlossen, auch auf Wunsch des Nutzers. Eine rückwirkende Lockerung
  zur Akzeptanz eines Kandidaten ist unzulässig.

**Meilenstein:** M2; Freigabegate für die betroffenen Fehlerbudgets und
alle darauf aufbauenden Näherungsschritte.

### U-V0.9-000003 — Pädagogische Fehlerbudgets und Kennzeichnung festlegen

**Anforderungen:** `A-V0.9-00009`  
**Abhängigkeiten:** U-V0.9-000010 (ausdrückliche Nutzerfreigabe der betroffenen Grenzwertsätze)  
**Aufwand:** niedrig bis mittel

Vor der Implementierung eines verändernden Näherungspfads einen
verbindlichen Prüfdatensatz aus den in U-V0.9-000010 vom Nutzer freigegebenen
Grenzwertsätzen anlegen: Lernziel, betroffene Messgrößen und Einheiten,
Referenzpfad/-fälle, repräsentative und Grenzfälle, akzeptierte absolute
und/oder relative Abweichungen sowie bekannte Grenzen und vorgesehene
Nutzerkennzeichnung. Die Grenzwerte sind anhand des Lernziels zu begründen.
Nicht freigegebene Grenzen dürfen weder als Testtoleranz noch als
Implementierungsgrundlage eines Näherungspfads übernommen werden.

Für reine Implementierungsoptimierungen mit gleichen Algorithmen und
physikalischen Annahmen gelten unverändert die bestehenden numerischen
Toleranzen und Referenztests. Für geschätzte Bootsdaten ist die physikalische
Modellunsicherheit getrennt von der Rechenabweichung zu dokumentieren.

**Prüfung und Abschlusskriterien**

- Ein wiederverwendbares Prüfprotokoll oder gleichwertiger
  Spezifikations-/Testnachweis enthält alle oben genannten Angaben.
- Kein Näherungskandidat wird vorab ohne festgelegtes, lernzielbezogenes
  Fehlerbudget implementiert oder freigegeben.
- Kriterien werden nicht rückwirkend an fehlgeschlagene Kandidaten angepasst.
- Die Kennzeichnung macht Näherungen und nicht verifizierte
  Modellannahmen verständlich und verhindert eine Darstellung als
  Engineering- oder Race-Optimizer-Ergebnis.

**Meilenstein:** M2; zusätzlich Voraussetzung für näherungsbehaftete Teile
von U-V0.9-000007 und U-V0.9-000008.

### U-V0.9-000004 — Reproduzierbare Echtzeit-Baseline und Profil

**Anforderungen:** `A-V0.9-00003`  
**Abhängigkeiten:** keine  
**Aufwand:** mittel

Einen auf dem Zielsystem reproduzierbaren End-to-End-Standardfall festlegen
und den Lauf in Hydrostatik/Geometrie, Hydrodynamik, Integration,
Worker-/Prozesskommunikation und Rendering aufteilen. Zusätzlich angeforderte
und berechnete Simulationszeit, Physikrückstand, Simulationszeit pro
Wandsekunde, Bildrate, Frameabstände und Eingabelatenz erfassen.

Der Bericht dokumentiert Modell, Modus, Parameter, Betriebssystem,
Prozessor/GPU/NPU-Inventar, Python-/Bibliotheksversionen, Renderoptionen,
Warm-up, Wiederholungen, Rohwerte, Median und 95. Perzentil. Start,
Pause/Fortsetzung sowie relevante Moduswechsel sind als Messfälle enthalten.
Ein Mikrobenchmark allein gilt nicht als Baseline.

**Prüfung und Abschlusskriterien**

- Ein anderer Lauf auf demselben Setup kann mit dokumentierten Eingaben
  wiederholt und verglichen werden.
- Nicht zuordenbare Zeit, Messfehler, Abbrüche und ungleiche Bedingungen
  werden ausdrücklich ausgewiesen.
- Als Ausgangspunkt vorhandene Live-GUI-, Nachhol- und Physikbenchmark-
  Werkzeuge verwenden; Instrumentierung nur ergänzen, wenn erforderliche
  Messwerte fehlen.

**Meilenstein:** M2.

### U-V0.9-000005 — Renderpfad pädagogisch verträglich optimieren

**Anforderungen:** `A-V0.9-00004`  
**Abhängigkeiten:** U-V0.9-000004  
**Aufwand:** niedrig bis mittel

Nur bei durch die Baseline belegtem Renderengpass Darstellungskosten wie
Wasseroptik, Schatten, SSAO oder zusätzliche Overlays einzeln messen und
gegebenenfalls reduzierbar bzw. abschaltbar machen. Körperlage,
Simulationszustand und für Lerninhalte wichtige Anzeigen müssen verständlich
bleiben. Physik und Anzeigeinterpolation sind voneinander getrennt zu halten.

**Prüfung und Abschlusskriterien**

- Vorher-/Nachher-Läufe vergleichen Bildrate, Frameabstands-P95,
  Physikrückstand, Eingabelatenz-P95 und erhaltene Lerninformationen.
- Für den Schulungs-Standardfall auf der Zielhardware werden mindestens
  30 FPS, Frameabstands-P95 höchstens 67 ms, Eingabelatenz-P95 höchstens
  100 ms und kein dauerhaft wachsender Physikrückstand über fünf Minuten
  bei 1x angestrebt und nachgewiesen oder als nicht erreicht dokumentiert.
- Rendering verändert die Physikergebnisse bei identischen Eingaben nicht
  außerhalb der bestehenden numerischen Toleranzen.
- Bei nicht erreichbaren Zielen wird ein eingeschränkter Zustand erkennbar
  gemacht; ausgelassene Frames oder verkürzte Messfenster kaschieren die
  Nichterfüllung nicht.

**Meilenstein:** M3.

### U-V0.9-000006 — Profilgeführte CPU- und exakte Unionoptimierung

**Anforderungen:** `A-V0.9-00005`, `A-V0.9-00006`  
**Abhängigkeiten:** U-V0.9-000003, U-V0.9-000004  
**Aufwand:** mittel bis hoch

Den dominanten CPU-Hotspot aus dem Profil auswählen; nicht belegte
Optimierungsideen werden nicht vorsorglich umgesetzt. JIT-/nativen Code nur
verwenden, wenn der End-to-End-Vorteil die Installations- und Wartungskosten
rechtfertigt. Falls `exakt_union` ein belegter Hotspot ist, ausschließlich
diesen Referenzpfad gezielt optimieren, ohne ihn stillschweigend in eine
Näherung umzudeuten.

**Prüfung und Abschlusskriterien**

- Vor Kandidatenlauf Referenzfälle und numerische Toleranzen festhalten.
- Ausgangs- und Kandidatenpfad mit identischen Eingaben und derselben
  Zielhardware vergleichen; ein reproduzierbarer End-to-End-Gewinn im
  Schulungs-Standardfall ist erforderlich.
- Geometrische, hydrostatische und aggregierte Referenz-/Regressionstests
  bestehen; Ergebnisse bleiben innerhalb bisheriger Toleranzen.
- Fehler werden sichtbar gemeldet; keine success-shaped Ersatzwerte.
- Mikrobenchmark-Gewinne ohne End-to-End-Nutzen reichen nicht.

**Meilenstein:** M3.

### U-V0.9-000007 — Exakte Hydrostatik-Wiederverwendung prüfen

**Anforderungen:** `A-V0.9-00007`  
**Abhängigkeiten:** U-V0.9-000003, U-V0.9-000004  
**Aufwand:** mittel

Zuerst ausschließlich eine exakte Wiederverwendung prüfen: Cachegültigkeit
für Pose, Geometrie, Wasserlage und alle weiteren Ergebnisinputs nachweisen
und jede relevante Änderung korrekt invalidieren. Der exakte Einzelschritt
bleibt als Vergleichspfad erhalten.

Ein größeres Berechnungsintervall oder andere veraltete/näherungsbehaftete
Resultate sind eine separate Schulungsnäherung. Sie dürfen nur nach
U-V0.9-000003, mit eigener sichtbarer Kennzeichnung und eigenem Fehlerbudget
umgesetzt werden. Der Standardmodus darf nicht unbemerkt auf diesen Pfad
wechseln. Ergibt sich kein ausreichender Gewinn oder kein vertretbares
Fehlerbudget, bleibt die Näherung unimplementiert.

**Prüfung und Abschlusskriterien**

- Tests prüfen Cachetreffer und Invalidierung für jede ergebnisrelevante
  Eingabe.
- Exakte Wiederverwendung entspricht dem Einzelschritt innerhalb der
  bestehenden Toleranzen und bringt einen messbaren End-to-End-Nutzen.
- Ein näherungsbehafteter Kandidat besteht vorab festgelegte Lernziel-,
  Grenzfall-, Kennzeichnungs- und Fehlerbudgettests; andernfalls wird er
  nicht freigegeben.

**Meilenstein:** M3.

### U-V0.9-000008 — NPU-Machbarkeit und gegebenenfalls Kernelbenchmark

**Anforderungen:** `A-V0.9-00008`  
**Abhängigkeiten:** U-V0.9-000003, U-V0.9-000004  
**Aufwand:** niedrig für Machbarkeit, hoch für Implementierung

Zuerst Betriebssystem, tatsächlich verfügbare NPU, Treiber, unterstützte
Laufzeit und Operatoren feststellen. Die Radeon 760M ist separat als GPU zu
bewerten. Ein Kernelbenchmark ist nur dann gerechtfertigt, wenn das Profil
einen ausreichend großen und für die verfügbare Laufzeit geeigneten
Tensor-/Vektorteilpfad zeigt. Boolesche Mesh-Union oder beliebige
NumPy-Geometrieoperationen werden nicht ohne Nachweis als NPU-geeignet
angenommen.

**Prüfung und Abschlusskriterien**

- Hardware-, Treiber-, Betriebssystem-, Laufzeit- und Operatorinventar ist
  dokumentiert; tatsächlicher NPU-Zugriff ist belegt oder als nicht verfügbar
  ausgewiesen.
- Ein geeigneter Kernel wird einschließlich Warm-up, Datentransfer,
  Start-/Synchronisationsaufwand und Wiederholungen gegen denselben
  CPU-Referenzlauf verglichen.
- Ein NPU-Pfad wird nur bei reproduzierbarem End-to-End-Vorteil,
  numerischer Übereinstimmung innerhalb geltender Toleranzen und robuster
  Fehlerbehandlung zur produktiven Weiterverfolgung empfohlen.
- Fehlt Laufzeit, geeigneter Kernel oder messbarer Nutzen, wird die Prüfung
  mit diesem Ergebnis abgeschlossen; der CPU-Pfad bleibt vollständig
  verfügbar und es wird keine NPU-Abhängigkeit eingeführt.

**Meilenstein:** M3.

### U-V0.9-000009 — Integrierte Regression und Abnahme

**Anforderungen:** `A-V0.9-00001` bis `A-V0.9-00009`  
**Abhängigkeiten:** U-V0.9-000001 bis U-V0.9-000008, U-V0.9-000010  
**Aufwand:** mittel

Alle Modellpaket-, Seglermassen-, GUI-, Echtzeit-, Genauigkeits- und
Benchmarkänderungen gemeinsam integrieren. Geänderte Pfade, vorhandene
Modelle und Einstellungen sowie Fehlerzustände regressiv prüfen. Alle aktiven
Spezifikationsanforderungen müssen durch Tests oder dokumentierte
Abnahmenachweise abgedeckt sein.

**Prüfung und Abschlusskriterien**

- Zielgerichtete Tests für Paketkatalog, Manifestvalidierung, Seglermasse,
  persistente Position, Cacheinvalidierung, Rendering und numerische Parität
  bestehen.
- Der volle Testsatz besteht auf der unterstützten Projektumgebung.
- Profil- und Live-Abnahmeberichte enthalten reproduzierbare Rohdaten und
  Bedingungen; nicht bestandene Leistungsziele werden offen ausgewiesen.
- Nicht produktiv umgesetzte Kandidaten (z. B. ungeeignete NPU-Nutzung oder
  ein Näherungspfad ohne passendes Fehlerbudget) sind mit Grund dokumentiert
  und werden nicht als erfüllt markiert.
- Jede erfüllte Anforderung wird nach der Nummerierungs-Anweisung im
  zentralen Umsetzungslog mit A-ID, Version und Kurzbeschreibung
  protokolliert. Offene Anforderungen bleiben offen.

**Meilenstein:** M4.

## 4. Meilensteine und Freigabegates

| Meilenstein | Enthaltene Schritte | Freigabebedingung |
|---|---|---|
| **M1 – Modellverträge** | U-V0.9-000001, U-V0.9-000002 | Automatische Paketerkennung, explizite Fehlerfälle sowie Segler-Masse, dreiachsige rumpffeste Position, Aggregation und Persistenz nachgewiesen. |
| **M2 – Mess- und Genauigkeitsgrundlage** | U-V0.9-000010, U-V0.9-000003, U-V0.9-000004 | Grenzwertvorschläge vom Nutzer ausdrücklich freigegeben und in lernzielbezogene Fehlerbudgets überführt; offene Grenzwertsätze sperren die betroffenen Näherungsschritte; Echtzeitprofil auf Zielhardware reproduzierbar und komponentengetrennt. |
| **M3 – Kandidaten bewertet** | U-V0.9-000005 bis U-V0.9-000008 | Jeder Kandidat hat End-to-End-Vergleich, Genauigkeits-/Lernzielprüfung und dokumentierte Entscheidung. Fehlgeschlagene Gates sperren Freigabe. |
| **M4 – Integrierte Abnahme** | U-V0.9-000009 | Regression und Vollsuite bestanden; Abnahmenachweise und offene Punkte nachvollziehbar; keine ungeprüfte Näherung als Standard aktiviert. |

Ein Meilenstein ist nicht bestanden, wenn Messwerte fehlen, ein Gate nicht
ausgeführt wurde oder Fehler als erfolgreiche Werte kaschiert werden. Ein
nicht lohnender Kandidat kann als „nicht umgesetzt“ mit Messergebnis
abgeschlossen werden; dadurch wird die zugehörige Spezifikationsanforderung
nicht als implementiert ausgegeben.

## 5. Rückverfolgbarkeitsmatrix

| Anforderungs-ID | Arbeitsschritt(e) | Abnahmenachweis | Status |
|---|---|---|---|
| `A-V0.9-00001` | U-V0.9-000001, U-V0.9-000009 | Katalog-/Loader-Tests, Manifestfehlerfälle, M1/M4 | Implementiert und integriert geprüft |
| `A-V0.9-00002` | U-V0.9-000002, U-V0.9-000009 | Massen-, Schwerpunkt-, Trägheits-, Persistenztests, M1/M4 | Implementiert und integriert geprüft |
| `A-V0.9-00003` | U-V0.9-000004, U-V0.9-000006 bis U-V0.9-000009 | [Komponenten-, Lifecycle- und Live-Bericht](../Messungen/Echtzeit_Abnahme_U000004-U000008_2026-10-19.md), Rohdaten und Wiederholung | Implementiert und geprüft; IPC-Rest sowie Grenzen des Qt-Swapproxys explizit |
| `A-V0.9-00004` | U-V0.9-000005, U-V0.9-000009 | Zwei 300-s-Schulungsmodusläufe, Darstellungsregressionen und dokumentierte Sichtprüfung | Technisch umgesetzt, Softwareproxy-Ziele zweimal bestanden; pädagogische Nutzerabnahme offen |
| `A-V0.9-00005` | U-V0.9-000006, U-V0.9-000009 | Hotspotprofil und GUI-CPU-Optimierung; kein separater Physik-CPU-Kandidat | Bewertet, keine zusätzliche Rechenkernoptimierung implementiert; nicht als erfüllte Beschleunigungsanforderung geloggt |
| `A-V0.9-00006` | U-V0.9-000006, U-V0.9-000009 | Exakte Referenzen unverändert; Worker annähernd 1x, Renderengpass vorrangig | Bewertet, keine neue Unionoptimierung implementiert |
| `A-V0.9-00007` | U-V0.9-000007, U-V0.9-000009 | 74.810 verschiedene Ganzposen bei 74.810 Aufrufen; null direkte Treffer | Bewertet, Ergebniscache nicht implementiert; kein Näherungsintervall aktiviert |
| `A-V0.9-00008` | U-V0.9-000008, U-V0.9-000009 | NPU-Inventar, fehlende Projektlaufzeit und fehlender geeigneter Kernel dokumentiert | Machbarkeitsprüfung abgeschlossen; negativ für Produktivnutzung, kein Kernelbenchmark gerechtfertigt |
| `A-V0.9-00009` | U-V0.9-000010, U-V0.9-000003, U-V0.9-000005 bis U-V0.9-000009 | Freigegebene unveränderte Fassung 1, ausführbare Gates, exakter Referenzreplay, Modell-/Verfahrenshinweise | Implementiert und geprüft; keine neue physikalische Näherung freigegeben |

## 6. Test- und Messstrategie

- Änderungen an Modellpaketen und Seglermasse werden zuerst mit fokussierten
  Loader-, Manifest-, Massen- und Persistenztests geprüft.
- Nach **jedem Meilenstein M1 bis M4** ist ein dokumentierter
  Regressionstestlauf Pflicht. M1 prüft Katalog, Loader, Overrides,
  Massenaggregation, Segler-Persistenz und zugehörige GUI-Bedienung.
  M2 prüft Messwerterfassung und die freigegebenen Genauigkeitsgates.
  M3 prüft für jeden tatsächlich geänderten Kandidaten numerische
  Regressionen, Invalidierung und GUI-Verhalten; hinzu kommen vergleichbare
  sichtbare Vorher-/Nachher-Messungen. M4 führt alle betroffenen Regressionen
  und anschließend die vollständige Projekttestsuite aus.
  Das Protokoll nennt Kommando, Umgebung, Datum, Ergebnis und offene Fehler.
  Ein fehlender oder fehlgeschlagener Pflichtnachweis sperrt die
  Meilensteinfreigabe; eine Zwischenmessung ersetzt diese Prüfung nicht.
- Optimierungen werden in derselben Python-/Bibliotheksumgebung, mit
  identischem Modell, Parametern, Hardware, Renderoptionen und Warm-up
  verglichen.
- Für unveränderte Algorithmen gelten vorhandene numerische Toleranzen.
  Jede neue Näherung benötigt eigene, vor der Kandidatenmessung fixierte
  und vom Nutzer ausdrücklich freigegebene absolute und/oder relative
  Grenzen sowie qualitative Lernzieltests. Die Prüfungen verweisen auf die
  freigegebene Fassung aus U-V0.9-000010.
- End-to-End-Messungen umfassen Median und 95. Perzentil sowie Rohwerte.
  Mikrobenchmarks sind ergänzend, nicht allein entscheidend.
- Für die integrierte Abnahme sind mindestens alle betroffenen gezielten
  Regressionen und anschließend die vollständige Projekttestsuite
  auszuführen. Die genauen Testmodule und Kommandos werden im jeweiligen
  Abnahmeprotokoll mit dem tatsächlich geänderten Umfang festgehalten.

## 7. Umfangsgrenzen

Dieser Plan nimmt keine Voxel-/OpenCL-Hydrostatik, adaptive oder größere
Physikzeitschritte und keine Parallelisierung zeitabhängiger Schritte auf.
Diese Optionen bleiben außerhalb dieses Umsetzungsumfangs; ihre
Zurückstellung ändert die zugehörigen Backlog-Einträge nicht. Eine
NPU-Produktivintegration ist ebenfalls kein vorab festgelegtes Ziel, sondern
nur bei geeignetem Profilbefund, vorhandener Laufzeit und bestandenem
End-to-End-/Genauigkeitsgate eine mögliche Folgemaßnahme.

## 8. Technischer Abschlussstand und historische Nachweise

**Stand:** 19.10.2026. Der Nutzer hat ausdrücklich entschieden, den
technisch geprüften Stand lokal zu committen und die pädagogische
Nutzerabnahme offen zu lassen. Kein Tag, Push oder Release ist freigegeben.
Vollständige funktionale Umsetzung, negative Kandidatenentscheidungen und
noch fehlende fachliche Abnahme werden nicht gleichgesetzt.
[Integriertes Prüfprotokoll](Abnahme_v0.9.md).

| Schritt | Stand | Nachweis / offene Arbeit |
|---|---|---|
| U-V0.9-000001 | Implementiert und integriert geprüft | Automatische Paketerkennung und Laufzeitaufbau ohne zusätzliche Registrierung. Katalogtests prüfen Arbeitsverzeichnisunabhängigkeit, ungültiges Manifest, fehlende Geometrie und doppelte Modell-ID. Override-/GUI-/Legacy-Regressionen einschließlich M4-Vollsuite bestanden. |
| U-V0.9-000002 | Implementiert und M1-regressiv geprüft | Striktes geometriefreies Masseblatt `segler`, explizite Rumpfreferenz, vollständige Massen-/Schwerpunkt-/Steiner-Aggregation, Baumeditor für Masse und x/y/z sowie atomare modellbezogene Benutzereinstellung. Nutzerfreigabe: Optimist 50 kg bei (0;0;0,45) m, Folkeboot 150 kg bei (0;0;0,85) m; yacht1 bleibt Migrationsmodell. Reale GUI-Moduswechsel übergeben dieselben Masseneigenschaften an beide Worker. |
| U-V0.9-000010 | Nutzerfreigabe erteilt | Fassung 1 am 19.10.2026 ausdrücklich vollständig freigegeben; zusätzliche Sperre gegen jede Lockerung bis Abschluss v0.9, auch durch den Nutzer. |
| U-V0.9-000003 | Fehlerbudgetgates und konkreter Referenzdatensatz implementiert | Unveränderliche Fassung 1 als ausführbare Hydrostatik-/Statik-/Dynamik-/Schwingungsgates; Grenzüberschreitungen werden pro Stichprobe abgelehnt. Eingefrorene exakte Hydrostatik-/Wasserlinienfälle für Optimist, Folkeboot, yacht1 mit Modellhashes, Rumpfmaßen und konkreten Beladungs-/Dynamikvorgaben. Referenz erneut exakt geprüft, keine Toleranzlockerung. Kein Näherungsverfahren freigegeben; der 30-s-Dynamik-Kandidatenvergleich wird nicht als ausgeführt behauptet. Modellannahmen sind im Baum und Solver-Status sichtbar. |
| U-V0.9-000004 | Komponentenprofil und korrigiertes Messverfahren implementiert | Workerprofile trennen Hydrostatik/Geometrie, Hydrodynamik, Kraftaggregation, Integration/Kraftaufrufverwaltung; Queue-/IPC-/Protokollrest bleibt als Rest ausgewiesen. Start/Pause/Fortsetzung/Moduswechsel diagnostiziert. VTK-EndEvents sind kein valider FPS-Nachweis; stattdessen Qt-Swapproxy mit expliziten Grenzen. Vergleichbare 300-s-Läufe einschließlich Segler und Modellhash liegen vor. |
| U-V0.9-000005 | Implementiert; Softwareziele wiederholt erreicht; Nutzerabnahme offen | Monotone Anzeigeuhr; exakte Wiederverwendung von Marker-, Pfeil-, Bogen-, Achsen- und Wasserspurgeometrien, Qt-Swap-Backpressure, keine unsichtbaren SVG-Renders. Persistenter Schulungs-Optikmodus ohne SSAO/MSAA, Basiswasseroptik. Zwei 300-s-Läufe: 33,64/33,68 Qt-Swaps/s, Frame-P95 47,343/47,242 ms, Eingabe-P95 39,896/41,277 ms, jeweils negativer Rückstandtrend. Kein Monitor-Scanout-Nachweis; hochwertige Standardoptik nicht als 30-FPS-fähig abgenommen. |
| U-V0.9-000006 | Profilgeführt bewertet; zusätzliche CPU-/Unionänderung nicht umgesetzt | Worker hält annähernd 1x; dominante verbleibende Einschränkung war GUI-Aufbereitung. Kein belegter zusätzlicher End-to-End-Vorteil für einen separaten CPU-/Unionkandidaten; keine spekulative JIT-/Native-Abhängigkeit. A-V0.9-00005 und A-V0.9-00006 werden nicht als implementierte Beschleunigungen ausgegeben. |
| U-V0.9-000007 | Exakte Wiederverwendung geprüft; Ergebniscache nicht umgesetzt | Baseline: 74.810 Hydroaufrufe, ebenso viele bitexakt verschiedene Ganzposen, null direkte Treffer. Keine Rundung, kein veraltetes Ergebnis und keine freigegebene reduzierte Invarianten-Cachedefinition. Hydrostatikintervall bleibt 1. Dokumentierte negative Kandidatenentscheidung, keine behauptete Cachebeschleunigung. |
| U-V0.9-000008 | Machbarkeit mit negativem Produktivergebnis geprüft | NPU-Gerät/Treiber vorhanden, Radeon separat erfasst. Projektlaufzeit/Provider und Operatorunterstützung nicht nachgewiesen; `onnxruntime` fehlt. Profil zeigt keinen belegten großen geeigneten Tensorkernel. Kein sinnvoller Kernelvergleich ohne Runtime/Kernel, keine Installation oder NPU-Abhängigkeit. CPU-Pfad bleibt vollständig verfügbar. |
| U-V0.9-000009 | Technische Integration bestanden; pädagogische Nutzerabnahme offen | Abschließende Vollsuite: 749 bestanden, 1 übersprungen (Windows-Symlinkrecht), 48,78 s; eingefrorene exakte Modellreferenzen unverändert reproduziert. Git-stabile LF-normalisierte Quellhashes zusätzlich getestet, keine numerischen Referenzwerte geändert. Beide Live-Wiederholungen und negative Kandidaten dokumentiert. Lokale Sicherung ausdrücklich freigegeben; kein Tag/Push. |

M1 und M2 sind technisch nachgewiesen. M3 ist hinsichtlich Implementierung,
Regression und Kandidatenentscheidung bearbeitet; die pädagogische
Sichtabnahme des Renderumfangs ist offen. M4 hat den vollständigen
technischen Integrationslauf bestanden, ist aber keine Gesamtfreigabe
aller neun Anforderungen oder eine Unterrichts-/Realbootvalidierung.

### Historischer Vorlauf (nicht zur aktuellen Bildratenabnahme verwenden)

Die folgenden frühen Messungen entstanden vor Seglerintegration und
Korrektur der VTK-Mehrfachzählung. Ihre als „präsentierte FPS“ bezeichneten
Zahlen sind keine gültigen Bildratenbelege. Sie bleiben als Fehler- und
Entwicklungshistorie erhalten; der maßgebliche aktuelle Nachweis steht im
[Echtzeitbericht](../Messungen/Echtzeit_Abnahme_U000004-U000008_2026-10-19.md).

Ausgeführte gezielte Validierung (Projekt-Python,
`QT_QPA_PLATFORM=offscreen`):

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_modellkatalog_auto.py tests\test_modell_lader.py tests\test_optimist_modell.py tests\test_folkeboot_modell.py tests\test_konfig_schema.py
```

Ergebnis damals: **50 Tests bestanden**. Dieser frühe Lauf prüfte
Modell-/Katalog- und Konfigurationsregressionen, noch nicht die anschließend
implementierte Seglerfunktion oder die sichtbaren Echtzeitleistungsziele.

### Sichtbare Echtzeit-Baseline vom 19.10.2026

[Rohbericht Folkeboot](../Messungen/Echtzeit_folkeboot_2026-10-19.json).
Ausgeführt mit dem vorhandenen Live-Benchmark:

```powershell
.\.venv\Scripts\python.exe werkzeuge\benchmark_gui_live.py --scene folkeboot --warmup 5 --duration 300
```

| Messgröße | Ergebnis |
|---|---|
| Messdauer / Aufwärmphase | 300,088 s / 5 s |
| Plattform | Windows-QPA, Python 3.14.8, Ryzen 5 8600G/Radeon 760M |
| Backend | `exakt_union`, exakte Hydrostatik je Physikschritt, Prozess-Worker |
| Vom Benchmark gemeldete präsentierte FPS | 34,17 (VTK-EndEvent-/SwapBuffers-Messung, keine unabhängige Displaymessung) |
| Explizite Renderaufrufe pro Sekunde | 17,07; getrennt von den Präsentierungsereignissen zu behandeln |
| Frameabstand P95 / Maximum | 60,095 ms / 107,595 ms |
| Eingabe bis präsentierter Frame P95 / Median | 8,833 ms / 7,054 ms; 299/299 Stimuli beantwortet |
| Poseauswertung P95 / Rendering P95 | 37,957 ms / 14,467 ms |
| Physikbatch Median / P95 | 70,318 ms / 137,173 ms |
| Angeforderte / berechnete Simulationszeit | 300,088 s / 299,040 s |
| Physikrückstand am Ende / Maximum | 1,048 s / 1,327 s |
| Rückstandstrend im Messfenster | −0,000120 s/s |
| Automatische Überlastpause | Nein |

Die Messung ist eine Baseline des gegenwärtigen Folkebootmodells ohne
Segler-Massenkörper. Sie ersetzt weder den komponentengetrennten Profiling-
Nachweis noch Wiederholungsläufe und die Abnahme nach den Modelländerungen.
Die zwei unterschiedlichen Frame-/Renderzählungen sind vor einer
Bildratenfreigabe zu klären. Noch keine Freigabe von M2, M3 oder M4.

### Anzeigeuhr: Korrektur und Nachher-Messung

Die Anzeige führt nun eine eigene Simulationszeit mit Wandzeitschritten.
Sie bleibt innerhalb des vorhandenen Zustandsverlaufs und puffert relativ
zum berechneten statt zum angeforderten Fortschritt. Neue Workerbatches
verschieben die Anzeige nicht sprunghaft nach vorn; ein wachsender Puffer
setzt die Anzeigezeit nicht zurück. Start, Körperwechsel und Pause setzen
die Anzeigeuhr passend zum übernommenen Zustand zurück; Fortsetzung zählt
die Pausenzeit nicht als Bewegung.

Die Korrektur verwendet weiterhin lineare Positionsinterpolation und SLERP,
keine Extrapolation oder zusätzlichen Physikschritte. Bei unzureichendem
Zustandsvorrat kann die Anzeige warten. Nach einem solchen Engpass wird
nicht schneller als Wandzeit vorgespult; zusätzlicher Anzeigeverzug ist
damit möglich. Vollständige Ruckelfreiheit unter beliebiger Überlast ist
ausdrücklich nicht nachgewiesen.

Gezielte Regressionen prüfen Interpolation und Quaternionen, unveränderten
Physikzustand und berechnete Zeit, Batchwechsel, Pufferwachstum,
Pause/Fortsetzung sowie unregelmäßige Batches mit 0, 1 und 10 s
angefordertem Physikrückstand. Beim gleichförmigen Testfall gilt nach
einer Sekunde Einpuffern exakt ein Bewegungsfortschritt von 1/30 s
je 30-Hz-Frame; schon während des Einpufferns gibt es weder negative
Zeitschritte noch einen Fortschritt über 1/30 s je Frame.

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_gui_laufzeit_edit.py tests\test_echtzeit_prozess.py tests\test_modellkatalog_auto.py tests\test_modell_lader.py tests\test_optimist_modell.py tests\test_folkeboot_modell.py tests\test_konfig_schema.py
```

Ergebnis: **73 Tests bestanden**. Keine Freigabe einer Näherung und
keine Lockerung bestehender oder freigegebener Genauigkeitsgrenzen.

[Nachher-Messbericht](../Messungen/Echtzeit_folkeboot_Anzeigeuhr_2026-10-19.json),
wiederum sichtbares Folkeboot, 5 s Warm-up und 300 s Messfenster:

| Messgröße | Vorher | Nachher |
|---|---:|---:|
| Messdauer | 300,088 s | 300,137 s |
| Vom Benchmark gemeldete präsentierte FPS | 34,17 | 30,71 |
| Explizite Renderaufrufe pro Sekunde | 17,07 | 14,49 |
| Frameabstand P95 | 60,095 ms | 69,144 ms |
| Eingabe bis präsentierter Frame P95 | 8,833 ms | 9,148 ms |
| Poseauswertung P95 | 37,957 ms | 45,804 ms |
| Rendering P95 | 14,467 ms | 15,950 ms |
| Physikrückstand am Ende | 1,048 s | 1,152 s |
| Rückstandstrend | −0,000120 s/s | +0,000280 s/s |
| Automatische Überlastpause | Nein | Nein |

**Bewertung:** Kein nachgewiesener Geschwindigkeitsgewinn. Das
Frameabstands-Ziel von höchstens 67 ms wird im Nachher-Lauf verfehlt.
Auch das Rückstandsziel ist anhand dieses leicht positiven Trends nicht
freigegeben. FPS und explizite Renderaufrufe bleiben unterschiedlich;
ohne Klärung dieser Zählung gibt es keine Bildratenabnahme.
Der reproduzierbare Glättungsnachweis stammt aus den gezielten Tests;
der Live-Lauf allein belegt weder subjektive Ruckelfreiheit noch
vollständig erhaltene Lerninformationen. Komponentenprofil und
weitere gezielte Renderarbeit bleiben offen. Keine Freigabe von M3.

**Messfehlerprotokoll:** Der erste Nachher-Lauf konnte wegen eines
Windows-Stdout-Dekodierungsfehlers nicht ausgewertet werden und zählt
nicht als gültiger Nachweis. Der zweite Lauf wurde vollständig beendet;
die nachgelagerte Extraktion scheiterte zunächst an CRLF-Zeilenenden.
Sein vollständiges JSON wurde anschließend aus der erfassten Ausgabe
wiederhergestellt. Numerische Felder blieben unverändert; ein deutsches
Textfeld zum Präsentierungsverfahren enthält durch die
Ausgabetranskodierung Ersatzzeichen. Dieser Umstand ist auch im
Messbericht ausdrücklich gekennzeichnet.
