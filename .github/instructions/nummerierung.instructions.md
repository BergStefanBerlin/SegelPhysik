---
description: "Use when assigning or checking requirement IDs, specification numbering, implementation steps, backlog transitions, traceability or CPPI interface IDs. Gilt fuer Kennungen, Spezifikationen und Umsetzungsplaene."
applyTo: "doc/**/*.md, doc/**/*.json"
---
# Projektweite Anforderungs- und Umsetzungsnummerierung

**Status:** Freigegeben am 20.10.2026; projektweit maßgeblich  
**Geltungsbereich:** Projektweit für Anforderungen, Ideen im Backlog und
Umsetzungsschritte sowie Python/C++-Interfaces.

Diese Instruction enthält die vollständige Regelung; eine separate
Nummerierungs-Anweisung wird nicht parallel gepflegt.

Eine Anforderung (`A-…`) wird ausschließlich in einer Spezifikation geführt.
Eine Idee (`I-…`) wird ausschließlich im Backlog geführt. Umsetzungsschritte
(`U-…`) stehen im zugehörigen Umsetzungsplan. Übergänge ändern nicht
rückwirkend die Kennung eines bestehenden Eintrags.

## Grundregeln

1. Jede Anforderung erhält eine eigene eindeutige Kennung. Eine Anforderung
   kann aus mehreren zusammengehörigen, gemeinsam abnehmbaren Details
   bestehen; einzeln prüfbare Anforderungen sollen nicht unnötig gebündelt
   werden. Ein Anforderungspunkt darf mehrere Details umfassen, sofern sie
   einen kohärenten Anforderungsvertrag bilden und gemeinsam abgenommen
   werden.
2. Eine einmal vergebene Kennung wird nie für einen anderen Inhalt
   wiederverwendet. Sie kann zurückgezogen werden; zurückgezogene Kennungen
   bleiben als solche nachvollziehbar.
3. Anforderungen erhalten eine versionsbezogene Kennung:

   ```text
   A-V<Version>-<laufende-nummer>
   ```

   Beispiel: `A-V0.7-00001`. `V0.7` ist nur ein Beispiel für den aktuell
   bearbeiteten Versionsschritt. Der A-Zähler beginnt für jede Version neu;
   die Kombination aus Version und Nummer ist eindeutig. Ältere Kennungen
   dürfen weiterhin als historische Referenz verwendet werden.
4. Wird eine Anforderung ins Backlog verschoben, wird sie als Idee mit einer
   `I-…`-Kennung geführt. Neue Backlog-Ideen verwenden das Format
   `I-BL-<laufende-nummer>`, zum Beispiel `I-BL-000001`. Da `BL` keine
   Versionsangabe enthält, läuft dieser Zähler projektweit fort und wird
   nicht mit einem neuen Versionsschritt zurückgesetzt.
5. Eine Backlog-Idee erhält erst dann eine neue Anforderungskennung
   `A-V<aktuelle-Version>-<laufende-nummer>`, wenn sie in eine aktuelle
   Spezifikation übernommen wird. Die A-ID wird neu vergeben; die frühere
   I-ID bleibt als Herkunftsverweis erhalten.
6. Jeder Umsetzungsschritt erhält eine eindeutige, versionsbezogene Kennung:

   ```text
   U-V<Version>-<laufende-nummer>
   ```

   Beispiel: `U-V0.7-000001`. Der U-Zähler beginnt für jede Version neu.
7. Jeder Umsetzungsschritt verweist auf mindestens eine passende
   Anforderungskennung `A-V<Version>-…`. Ein Umsetzungsschritt darf mehrere
   Anforderungen gemeinsam umsetzen; Anforderungen müssen nicht jeweils in
   einem eigenen Umsetzungsschritt implementiert werden. Am Ende der
   Umsetzung müssen alle aktiven Anforderungen der betreffenden Version
   mindestens einem Umsetzungsschritt zugeordnet und über die geplanten
   Meilensteine nachgewiesen sein. Umsetzungsschritte sind so zu ordnen,
   dass ihre Abhängigkeiten eingehalten werden und sie nacheinander
   erarbeitet und integriert werden können.

## Dauerhafte Kennungen für Python/C++-Interfaces

- Jedes einzelne Interface erhält eine eindeutige Kennung `CPPI-xxxx`
  (C++Interface), beginnend mit `CPPI-0001`. Die laufende Nummer wird
  mindestens vierstellig mit Nullen aufgefüllt und bei Bedarf verlängert.
- Der CPPI-Zähler läuft projektweit über alle Versionen und Revisionen
  hinweg fort; er wird nicht zurückgesetzt.
- Maßgebliche Vergabestelle ist das
  [Schnittstellenregister Python/C++](../../doc/Dokumentation/Schnittstellenregister_CPP.md).
  Jeder exportierte Datentyp, jede Funktion und jede qualifizierte
  Kontextmethode erhält einen eigenen Eintrag, keine Sammel-ID pro Familie.
- Konkrete geplante Interfaces erhalten bereits vor der Implementierung
  eine CPPI-ID. Noch nicht konkretisierte Arbeits- oder Abnahmebereiche
  erhalten keine Interface-Kennung.
- Vor einer Vergabe aktive und archivierte Einträge prüfen. Neue Nummern
  liegen oberhalb der höchsten jemals vergebenen Nummer; Lücken werden
  nicht aufgefüllt. Bestehende IDs niemals umnummerieren oder für andere
  Schnittstellen wiederverwenden.
- Statusänderungen und Umbenennungen derselben Schnittstelle behalten die
  CPPI-ID; den bisherigen Namen nachvollziehbar dokumentieren. Eine neue
  Ersatzschnittstelle erhält eine neue ID mit Verweis auf die ersetzte ID.
  Stillgelegte oder verworfene Einträge bleiben mit ursprünglicher ID,
  Begründung und gegebenenfalls Ersatz im Register erhalten.
- CPPI-IDs ergänzen A-/U-Verweise und ersetzen weder Anforderungs- noch
  Umsetzungsschrittkennungen.

## Ablauf und Beziehungen

```mermaid
flowchart TD
    I["Idee im Backlog<br/>I-BL-000001"]
    S["Anforderung in Spezifikation<br/>A-V0.7-00001"]
    U["Geordnete Umsetzungsschritte<br/>U-V0.7-000001, ...<br/>je U mindestens eine A-ID"]
    DONE["Umgesetzt und abgenommen"]
    LOG["doc/Log/Log.md<br/>ID, Version, Kurzbeschreibung"]
    WITHDRAW["doc/Log/zurückgezogen.md<br/>ID, Text, Begründung"]

    I -->|"ausgewählt und spezifiziert;<br/>neue A-ID, I-ID bleibt Herkunft"| S
    S -->|"freigegebener Umfang"| U
    U -->|"Tests und Meilensteine bestanden"| DONE
    DONE -->|"Eintrag"| LOG
    S -.->|"verworfen"| WITHDRAW
    I -.->|"verworfen"| WITHDRAW
    U -.->|"nach Rückfrage: A zurückziehen"| WITHDRAW
    U -.->|"neue I-ID aus zurückgezogener A-ID"| I
    U -->|"neue Idee entsteht während Umsetzung"| I
```

## Kennungs- und Rückverfolgbarkeitsprinzip

```text
I-BL-000001
   │ wird für eine Version ausgewählt
   ▼
A-V0.7-00001 ──────────────┐
A-V0.7-00002 ──────────────┼── referenziert durch ── U-V0.7-000001
A-V0.7-00003 ──────────────┘                         │
                                                     ▼
                                      Meilenstein mit gruppiertem Nachweis
                                                     │
                                                     ▼
                                 doc/Log/Log.md nach Umsetzung und Abnahme
```

Die Versionsbestandteile in den Beispielen sind Platzhalterwerte und keine
Festlegung auf `V0.7`. Der aktuelle Versionsschritt ist pro Vorhaben
festzustellen. Anforderungen aus älteren Versionen können als fachliche
Quellen referenziert werden; Umsetzungsschritte der aktuellen Version müssen
die für ihre aktuelle Umsetzung gültigen Anforderungs-IDs nennen. IDs sind
durch Typpräfix, Version (sofern im Format vorgesehen) und laufende Nummer
eindeutig; ein zusätzlicher Namens-Slug wird nicht verwendet.

## Abgestimmte Prozessregeln

### 1. Übergang zwischen Anforderung und Backlog-Idee

Die Kennung selbst wird nicht umgeschrieben. Wenn eine Anforderung aus einer
Spezifikation verworfen oder – nach Rückfrage und Zustimmung des Nutzers –
während ihrer Umsetzung ins Backlog verschoben wird:

- Die bisherige `A-…`-Kennung wird zurückgezogen und nie wieder vergeben.
- Der aktive normative Punkt wird aus dem aktiven Anforderungsteil der
  Spezifikation entfernt und dort gemäß dem bestehenden
  Spezifikationsverfahren unter seiner ursprünglichen ID als zurückgezogen
  archiviert.
- Die Backlog-Idee erhält eine neue `I-BL-…`-Kennung.
- Beide Kennungen werden miteinander verknüpft (zum Beispiel
  „ersetzt/abgeleitet aus“).
- Bei späterer Übernahme erhält die Idee eine neue `A-V…`-Kennung; die
  `I-BL-…`-Kennung bleibt als historische Herkunft erhalten.

Damit ist die inhaltliche Verschiebung von A nach I gemeint, nicht eine
Änderung der bereits vergebenen Kennung. Eine Anforderung wird niemals
ohne vorherige Rückfrage und Zustimmung aus einem laufenden Umsetzungsschritt
ins Backlog verschoben. Neue Ideen, die während der Umsetzung entstehen,
erhalten direkt eine neue `I-BL-…`-Kennung und werden im Backlog erfasst; sie
werden nicht ohne Spezifikationsaufnahme als Anforderungen behandelt.

### 1a. Übergang von einem alten Nummerierungsschema

Wenn eine bestehende Spezifikation von einem früheren Nummerierungsschema
auf das aktuelle Schema umgestellt wird:

- Die Anforderungen werden im aktiven Spezifikationstext ausschließlich
  mit den neuen, versionsbezogenen `A-V<Version>-<laufende-nummer>`-IDs
  bezeichnet.
- Am Ende der Spezifikation wird ein Anhang mit einer eindeutigen Zuordnung
  jeder alten Kennung zu ihrer neuen A-ID ergänzt.
- Alte Kennungen bleiben als historische Verweise dauerhaft reserviert und
  werden weder gelöscht noch für andere Inhalte wiederverwendet. Sie sind
  nach der Umstellung keine aktiven Anforderungskennungen.
- Neue Verweise in Spezifikation, Umsetzungsplan, Tests und Protokollen
  verwenden die neue A-ID. Die alte Kennung darf dort nur im ausdrücklich
  historischen Zuordnungskontext erscheinen.
- Die Umstellung ändert keine Anforderung inhaltlich. Wird eine Anforderung
  dabei geteilt, zusammengeführt oder fachlich geändert, ist dies gesondert
  nachvollziehbar zu dokumentieren; eine alte ID darf nicht mehrdeutig auf
  mehrere neue Anforderungen zeigen.

Diese Übergangsregel gilt projektweit und unabhängig davon, in welchem
Versions- oder Revisionsordner die Spezifikation liegt.

### 2. Umsetzung und zentrale Protokolle

Nach erfolgreicher Umsetzung und Abnahme wird jede erfüllte Anforderung in
`doc/Log/Log.md` eingetragen. Der Eintrag enthält mindestens die A-ID, die
Version und eine kurze Beschreibung. Der Log-Eintrag dokumentiert den
Abschluss; die Spezifikation bleibt als fachliche Quelle erhalten. Der
Logeintrag ist ein Abschlussnachweis und verschiebt die Anforderung nicht
aus ihrer Spezifikation.

Verworfene oder zurückgezogene Anforderungen und Ideen werden in
`doc/Log/zurückgezogen.md` eingetragen. Jeder Eintrag enthält mindestens
die ursprüngliche ID, den Anforderungstext beziehungsweise Ideentext und
eine kurze Begründung. Bei einem Übergang von A zu I werden beide IDs und
ihre Beziehung festgehalten: die zurückgezogene A-ID und die neu angelegte
I-BL-ID. Eine verworfene Anforderung erhält außerdem den beschriebenen
Archivvermerk in ihrer Spezifikation.

IDs der umgesetzten und zurückgezogenen Einträge bleiben dauerhaft reserviert
und werden niemals wiederverwendet. Die Protokolle sind Ergänzungen zur
Spezifikation und zum Backlog, keine Ablösung ihrer Einträge oder
Anforderungsquelle.

### 3. Granularität und Zähler

Jede eigenständig prüfbare Anforderung erhält eine ID.
Zusammengehörige Einzelaspekte dürfen als ein Anforderungspunkt beschrieben
werden, wenn sie einen kohärenten, gemeinsam abnehmbaren Vertrag bilden.

Der Zähler besteht aus einer laufenden Nummer. Der Typpräfix und – bei A/U –
die Versionsangabe erklären die Bedeutung der Kennung. Ein zusätzlicher
Namens-Slug wird nicht verwendet.

- A-Zähler beginnen je Version neu.
- U-Zähler beginnen je Version neu.
- I-BL-Zähler laufen im projektweiten Backlog fort, da `BL` keine Version
  kodiert.
- Die Nummer wird bei Bedarf verlängert, nie abgeschnitten oder
  wiederverwendet.

Beispiele für die abgestimmten Formate:

```text
A-V0.7-00001
I-BL-000001
U-V0.7-000001
```

### 4. Umsetzungsschritte, Reihenfolge und Meilensteine

Umsetzungsschritte werden so zugeschnitten, dass sie in einer sinnvollen,
abhängigkeitsgerechten Reihenfolge erstellt und integriert werden können.
Technisch zusammengehörige Anforderungen dürfen im selben Schritt
umgesetzt werden. Es ist nicht erforderlich und nicht immer sinnvoll, jede
Anforderung isoliert einzeln zu implementieren. Schritte bauen auf ihren
Voraussetzungen auf und werden mit gruppierten, prüfbaren Meilensteinen
abgenommen.

Jeder Umsetzungsschritt erhält eine eindeutige `U-V…`-ID und verweist auf
mindestens eine `A-V…`-ID. Die Umsetzungsschritte sollen Abhängigkeiten
sichtbar machen und an prüfbaren Meilensteinen enden. Meilensteintests und
Abnahmekriterien dürfen mehrere zusammengehörige Anforderungen gemeinsam
verifizieren; eine eigene Test-ID oder ein eigener Umsetzungsschritt pro
Anforderung ist nicht vorgeschrieben. Diese Regel bedeutet keine 1:1-
Zuordnung: Ein U-Schritt darf mehrere A-IDs bündeln, und eine A-ID darf
mehrere abhängige U-Schritte benötigen.

Zur Abnahme jeder Version wird eine Rückverfolgbarkeitsmatrix geführt:

| Aktive Anforderungs-ID | Spezifikation/Abschnitt | Umsetzungsschritt(e) | Test/Abnahmekriterium | Status |
|---|---|---|---|---|
| `A-V<Version>-…` | Fundstelle | ein oder mehrere passende `U-V<Version>-…` | zugehöriger Meilenstein-/Testnachweis | offen/erfüllt |

Am Ende müssen alle aktiven Anforderungen der Version in mindestens einem
Umsetzungsschritt referenziert und durch den betreffenden Meilenstein
nachgewiesen sein. Eine Anforderung, die nicht mehr Teil der aktuellen
Version ist, wird nicht stillschweigend ausgelassen: Sie wird zurückgezogen
und gegebenenfalls als neue Backlog-Idee mit Herkunftsverweis geführt.

### 5. Eindeutigkeit über Versionen

Die vollständige Kennung ist projektweit eindeutig. A- und U-Zähler dürfen
zwischen Versionen erneut beginnen, weil die Version Bestandteil der
Kennung ist. I-BL-Nummern sind projektweit fortlaufend. IDs werden nie neu
vergeben, auch nicht nach Löschung oder Archivierung des zugehörigen
Dokuments.

## Anwendung bei Projektarbeiten

- Vor jeder Neuvergabe aktive und archivierte IDs prüfen. Bestehende
  Kennungen nicht umnummerieren oder wiederverwenden. Eine Umstellung alter
  Spec-Kennungen nur auf ausdrücklichen Auftrag durchführen und die
  historische Zuordnung nach Abschnitt 1a erhalten.
- Jede Anforderung bleibt in ihrer Ursprungsspezifikation dokumentiert:
  aktive Punkte im Anforderungsteil, zurückgezogene oder verlegte Punkte
  unter ihrer ursprünglichen Kennung im vorgeschriebenen Archivabschnitt.
  A-/U-Verweise und Tests konsistent verknüpfen; fehlende Zuordnungen und
  Nachweise offen nennen.
- Eine Anforderung während laufender Umsetzung nur nach Zustimmung des
  Nutzers ins Backlog überführen. Fehlende Angaben nicht erraten. Den Ordner
  `doc/Backlog/Ideen/` nicht als Informationsquelle verwenden, außer der
  Nutzer verlangt ausdrücklich konkrete Inhalte daraus.
- Abschließend doppelte oder fehlende IDs, Wiederverwendung, Abhängigkeiten
  und Nachweislücken prüfen. Betroffene Dokumente und Kennungen knapp
  benennen; keine unbelegte Vollständigkeit behaupten.
- Bei Spezifikationsanfragen aktive Punkte nach Kennung tabellarisch
  auflisten, sofern nicht anders gewünscht.

## Freigabe

Der Nutzer hat diese projektweite Regelung einschließlich der am
20.10.2026 ergänzten CPPI-Regeln ausdrücklich freigegeben. Diese Instruction
ist die maßgebliche Regel für alle Versionen und Revisionsschritte. Änderungen
an der Nummerierungsregel selbst benötigen eine spätere ausdrückliche
Nutzerentscheidung; bestehende Kennungen bleiben unverändert.
