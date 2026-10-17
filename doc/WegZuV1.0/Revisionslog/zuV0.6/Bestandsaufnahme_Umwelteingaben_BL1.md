# Bestandsaufnahme künftiger Umwelteingaben (BL1)

**Stand:** 17.10.2026
**Zweck:** Vorbereitende Bestandsaufnahme; keine Freigabe neuer Physik.

## Abgrenzung

Diese Notiz hält nur bereits vorhandene Verträge und offene Datenfragen fest.
Sie führt weder Kraftansätze noch Kennwerte oder Laufzeitberechnungen ein.
Die unten aufgeführten Widerstands-, Fluid- und Added-Mass-Funktionen
existieren bereits im Code. Ihre Existenz ist weder eine neue Implementierung
noch ein Nachweis ihrer Gültigkeit für reale Wasser- oder Luftzustände.

## Bestehende Verträge und Komponenten

| Bereich | Bestand | Einordnung |
|---|---|---|
| Hydrostatik | `segelphysik/core/auftrieb.py`: Auftrieb aus verdrängendem Volumen, Angriffspunkt im Verdrängungsschwerpunkt; 2D- und 6-DOF-Kraftfunktionspfade. `exakt_union` ist der genaue Referenzpfad. | Vorhandene Auftriebssimulation; kein neuer Ansatz. |
| Beiträge und Bezug | `segelphysik/core/kraftmodell.py`: benannte `Kraftbeitrag`-Objekte und `Wrench` mit SI-Kraft, SI-Moment, Bezugspunkt und Frame; Aggregation auf einen Bezugspunkt. | Vorhandener Kraftvertrag für Beiträge. |
| Gewicht und Dynamikmodule | `Kraftmodell` kann Masse/Gewicht, linearen und quadratischen Widerstand, Fluid-Translations-/Winkelgeschwindigkeit und diagonale Added Mass verarbeiten. Die Module sind standardmäßig null; Konfiguration und Fabrik reichen vorhandene Werte durch. | Bestehende Funktionen; kein Nachweis einer extern validierten Parametrisierung. |
| Konfiguration | `segelphysik/core/konfig_lader.py` validiert `dt_s`, `g_m_pro_s2`, Dämpfung, Voxelparameter sowie optionale Kraftvektoren. `konfigurationen/physik.json` liefert feste Zeitschritt-, Schwere-, Dämpfungs- und Voxelwerte; nicht gesetzte Kraftmodule bleiben null. | Vorhandenes Schema, kein neuer Eingabevertrag. |
| Integration | `segelphysik/core/dynamik.py` und `dynamik_6dof.py` integrieren vorhandene Kraft-/Momentenergebnisse in den festen Zeitschritten. | Bestehender Dynamikpfad; keine Aussage über noch nicht freigegebene Umweltmodelle. |
| Einheiten und Frames | Im Code sind SI-Einheiten in Namen/Verträgen ausgewiesen; Wrenches verlangen einen benannten Frame und denselben Bezugspunkt bei der Aggregation. Spezifikationsreferenz: Abschnitt 2 und 6 von `Spezifikation_v0.5.md`. | Wiederverwendbare Infrastruktur; ein konkreter neuer Umweltzustand ist damit noch nicht spezifiziert. |

## Offene Entscheidungen und Datenbedarfe

Vor einer späteren Implementierungsfreigabe müssen fachlich zuständige
Quellen und Freigaben mindestens folgende Punkte beantworten:

1. Welche Wasser- und Luftzustände werden tatsächlich als externe Eingaben
   benötigt, und welche Quelle deckt jeden Zustand und Gültigkeitsbereich ab?
2. Welche Referenzmessungen oder unabhängig validierten Daten belegen
   Kennwerte, Unsicherheiten und Gültigkeitsgrenzen? Derzeit werden hier
   keine solchen Quellen oder Werte als geprüft behauptet.
3. Welcher Zeitbezug, welches Frame und welche Transformation gelten für
   jeden Umweltzustand und für den verwendeten Umgebungssnapshot?
4. Welche bereits vorhandene Funktion ist aktiv in der Produktionssimulation
   verdrahtet und welche ist nur über Konfiguration/API verfügbar? Dies ist
   je Lauf und Konfiguration nachzuweisen, nicht aus dem Vorhandensein einer
   Klasse abzuleiten.
5. Welche unabhängigen Referenz- und Echtzeitabnahmen wären für eine spätere
   fachliche Freigabe erforderlich?

Bis diese Fragen mit benannten Quellen, Zuständigkeiten und ausdrücklicher
Freigabe beantwortet sind, bleiben neue Umweltzustände, neue Koeffizienten
und neue Kraftbeiträge außerhalb des Implementierungsumfangs. Bereits
implementierte Auftriebs- und Kraftpfade dürfen separat getestet und bei
reproduziertem Fehler mit Regression korrigiert werden.

## Abnahme dieser Bestandsaufnahme

- Die Inventur beschreibt ausschließlich nachweisbare bestehende
  Komponenten und kennzeichnet ihre Grenzen.
- Es werden keine neuen Formeln, Parameter, Produktivinputs, physikalischen
  Modelle oder Simulationen eingeführt.
- Offene Datenquellen und Freigaben bleiben ausdrücklich offen.
