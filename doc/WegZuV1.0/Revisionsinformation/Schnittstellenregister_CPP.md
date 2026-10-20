# Schnittstellenregister Python/C++

**Stand:** 20.10.2026  
**Geltungsbereich:** Python/C++-Grenzen des nativen Moduls `_segelphysik_native`  
**Arbeitsstand:** V0.10 als begrenzter Versionsstand abgeschlossen;
kein vollständiger Abschluss der ursprünglichen C++-Migration.
Restarbeiten nach A-Kennung im
[Backlog](../../Backlog/Restarbeiten_V0.10.md).

## Zweck und Statusbegriffe

Dieses Register führt native C++-Exporte, die zugehörigen produktiven
Python-Aufrufpfade und künftig geplante, aber noch nicht verfügbare
Schnittstellenfamilien zentral auf. Es ergänzt das
[Funktionsinventar V0.10](../Revisionslog/zuV0.10/Umsetzungsplan/Funktionsinventar_V0.10.json):
Das Inventar ordnet fachliche Python-Funktionen Anforderungen, Tests und
Profilbelegen zu; dieses Register beschreibt die Python/C++-Vertragsgrenze
und ihren Lebenszyklus.

**Lebenszyklusstatus**

- **Aktiv angebunden:** Export ist im nativen Vertrag verpflichtend und ein
  Python-Adapter bzw. produktiver Aufrufpfad ist im Quellcode vorhanden.
  Das bedeutet nicht, dass der Pfad in jeder Sitzung oder im Standardmodus
  ausgeführt wird. Optionale und `cpp`-pfadabhängige Funktionen sind als
  solche bezeichnet.
- **Nie produktiv aktiviert:** Implementiert/exportiert, aber absichtlich
  nicht in einem produktiven Aufrufpfad aktiviert. Der Eintrag benötigt
  einen Grund und einen Nachweis, dass dies tatsächlich nie geschehen ist.
- **Nicht mehr aktiv:** Früher produktiv angebunden, inzwischen deaktiviert
  oder entfernt. Ersatz, Zeitpunkt und Grund sind anzugeben.
- **Geplant:** In einer aktiven Anforderung vorgesehen, aber noch kein
  nativer Export bzw. keine produktive native Anbindung vorhanden.

Der C++-Exportvertrag wird in
[`native_backend.py`](../../../code/python/segelphysik/core/native_backend.py)
festgelegt. Der installierte Modulstand zum Erfassungszeitpunkt enthielt
**22 Datentypen, 88 Funktionen und 7 verpflichtend geprüfte Methoden**
(117 Vertragsnamen). Das Modul exportierte insgesamt 112 öffentliche
Attribute; der Unterschied entsteht insbesondere durch interne Hilfs- und
Kompatibilitätsexporte, die nicht alle Teil des verpflichtenden
`native_backend`-Vertrags sind.

Ein Quellcode-Aufruf ist ein Integrationsnachweis, aber keine Aussage über
Häufigkeit, Standardpfadwahl oder gemessene Laufzeit. Dafür gelten die
jeweiligen Tests und Messberichte. Nicht statisch eindeutig zuordenbare
Nutzung muss vor einer Stilllegung zur Laufzeit geprüft werden.

## Kennungen und Eintragsgranularität

Jeder einzelne exportierte Datentyp, jede Funktion und jede qualifizierte
Kontextmethode erhält genau einen eigenen Eintrag mit dauerhafter Kennung
`CPPI-xxxx` (C++Interface), beginnend mit `CPPI-0001`. Der Zähler läuft
projektweit und versionsunabhängig weiter. Neue Kennungen werden oberhalb
der höchsten jemals vergebenen Nummer vergeben; bestehende Einträge werden
nicht umnummeriert. Kennungen stillgelegter oder verworfener Schnittstellen
bleiben reserviert und mit Begründung erhalten. Eine Umbenennung derselben
Schnittstelle erhält die Kennung und dokumentiert den bisherigen Namen;
eine neue Ersatzschnittstelle erhält eine neue Kennung und einen Ersatzverweis.

Familien dienen nur der fachlichen Gliederung und ersetzen keine
Einzeleinträge. Noch unscharfe Arbeits- und Abnahmebereiche in Abschnitt 4
sind keine definierten Interfaces und erhalten keine Schein-Interface-ID.
Sobald daraus eine konkrete geplante Vertragsgrenze festgelegt wird, erhält
sie bereits vor der Implementierung einen eigenen CPPI-Eintrag.

Die Erstvergabe umfasst **118 Interfaces**: 22 Datentypen, 88 verpflichtende
Funktionen, den zusätzlichen Export `linear_loesen` und 7 Kontextmethoden.
Der Backendvertrag oben ist der gemeinsame Vertragsnachweis; die bisherigen
familienbezogenen Einschränkungen bleiben unten erhalten. Durch diese
Umstrukturierung werden keine Nutzungsstatus oder Abnahmen hochgestuft.

## Performance-Spalten und V0.10-Abnahme

Die Spalten `Python-Referenz` und `V0.10` zeigen **Medianzeiten in µs**.
In der Versionsspalte folgt der Faktor Python/C++: über 1 schneller,
unter 1 langsamer. Jede Zahl verlinkt den konkreten Messfall in der
[Abschlussbilanz V0.10](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md).
Mehrere Werte in einer Zelle entsprechen in beiden Spalten denselben
verlinkten Fällen in gleicher Reihenfolge; Modelle und Eingabegrößen stehen
im jeweiligen Fall. Die Messungen enthalten den öffentlichen Adapter und
gegebenenfalls Bibliotheksobjekte, keine isolierten C++-Kernelzeiten.

Vergleichsbasis ist der unveränderte v16-Messzwischenstand innerhalb V0.10
mit sieben Wiederholungen je Fall, festgelegten Eingaben und erfassten
Quell-/Buildhashes. P95, Streuung, Rohwerte, Hardware und Referenzwahl sind in
der Abschlussbilanz und deren Rohbelegen dokumentiert. Die Übereinstimmung
der 57 erfassten Quellen und des nativen Moduls wurde am 20.10.2026 erneut
geprüft; dies ist keine neue Performanceausführung.

`nicht separat gemessen` bedeutet fehlende Einzelmessung, nicht Nullzeit
oder fehlende Nutzung. `nur Elternblock` verlinkt einen gemeinsamen
Integrationspfad, ohne dessen Gesamtzeit als individuellen Interfacegewinn
auszugeben. Datentypen erhalten keine erfundene Funktionslaufzeit.
Verschachtelte Messungen dürfen nicht addiert werden. Ein Anwendungs-
Gesamtgewinn und tatsächlich präsentierte Monitor-FPS sind nicht belegt.
Neue Versionsspalten werden erst bei Bearbeitung der betreffenden Version
angelegt; bestehende freigegebene Messstände bleiben erhalten.

Die strenge Optimist-Batchabweichung ist seit Nutzerauftrag vom 20.10.2026
eine **akzeptierte Abschlussausnahme**, kein bestandenes strenges Gate.
Der Nutzer hat außerdem den begrenzten V0.10-Versionsabschluss mit
dokumentierten Restarbeiten ausdrücklich freigegeben. Die übrigen
Implementierungs- und Abnahmerestpunkte in Abschnitt 4, Abschlussbilanz
und Backlog sind damit nicht erledigt oder streng abgenommen.

## 1. Native Datentypen

Alle folgenden Typen sind im C++-Modul implementiert und im
`native_backend`-Vertrag erforderlich. Nutzung kann vom Rechenpfad oder
vom jeweiligen Physik-/Grafikverfahren abhängen.

| Kennung | Interface | Status | Einordnung / Grenze | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|---|
| CPPI-0001 | `Zustand` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0002 | `Mesh` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0003 | `Modell` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0004 | `Parameter` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0005 | `Wrench` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0006 | `Beitrag` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0007 | `Ergebnis` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0008 | `Abbruch` | Aktiv angebunden | Rechenkern- und Batchdaten | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0009 | `Pose` | Aktiv angebunden | Körper-, Frame- und Snapshotvorbereitung | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0010 | `Koerperteil` | Aktiv angebunden | Körper-, Frame- und Snapshotvorbereitung | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0011 | `Verband` | Aktiv angebunden | Körper-, Frame- und Snapshotvorbereitung | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0012 | `VerbandKontext` | Aktiv angebunden | Körper-, Frame- und Snapshotvorbereitung | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0013 | `BlattKontext` | Aktiv angebunden | Körper-, Frame- und Snapshotvorbereitung | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0014 | `SnapshotKontext` | Aktiv angebunden | Körper-, Frame- und Snapshotvorbereitung | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0015 | `EbenenSchnitt` | Aktiv angebunden | Schnitt- und Hydrostatikpfade | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0016 | `HydroTeil` | Aktiv angebunden | Schnitt- und Hydrostatikpfade | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0017 | `HydroKontext` | Aktiv angebunden | Schnitt- und Hydrostatikpfade | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0018 | `HydrostatikKontext` | Aktiv angebunden | Schnitt- und Hydrostatikpfade | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0019 | `HydrostatikWerte` | Aktiv angebunden | Schnitt- und Hydrostatikpfade | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0020 | `PhysikKontext` | Aktiv angebunden | Worker-/Solverkontext | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0021 | `StatikKontext` | Aktiv angebunden | Worker-/Solverkontext | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |
| CPPI-0022 | `_VoxelKontext` | Aktiv angebunden; optionaler Pfad | Privater Python-Name; Voxelverfahren ist nicht der allgemeine Standardpfad | nicht separat gemessen | Datentyp; keine eigene Laufzeitmessung |

## 2. Native Funktionen

Die Statusangabe „Aktiv angebunden“ bedeutet, dass die Funktion im
verpflichtenden Exportvertrag steht und ein Python-Adapter bzw. ein
fachlicher Aufrufpfad existiert. Es bedeutet nicht, dass alle Funktionen
gleich häufig oder standardmäßig ausgeführt werden.

### Quaternionen, Frames und Körperkontext

Vorbereitetes Modell-/Frameverfahren.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0023 | `quaternion_normalisieren` | Aktiv angebunden | [6.560](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-029) | [18.093 / 0.363x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-029) |
| CPPI-0024 | `quaternion_matrix` | Aktiv angebunden | [14.360](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-030) | [18.412 / 0.780x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-030) |
| CPPI-0025 | `quaternion_aus_matrix` | Aktiv angebunden | [58.967](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-031) | [20.098 / 2.934x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-031) |
| CPPI-0026 | `quaternion_multiplizieren` | Aktiv angebunden | [2.525](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-033) | [8.361 / 0.302x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-033) |
| CPPI-0027 | `orientierung_schritt` | Aktiv angebunden | [10.231](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-034) | [9.798 / 1.044x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-034) |
| CPPI-0028 | `rotationsmatrix_achsenwinkel` | Aktiv angebunden | [7.369](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-041) | [9.299 / 0.792x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-041) |
| CPPI-0029 | `pose_mit_gelenkwinkel` | Aktiv angebunden | [7.674](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-043) | [21.724 / 0.353x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-043) |
| CPPI-0030 | `verband_aggregieren` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [111](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-111), [135](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-135), [159](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-159) |

### Wasser-/Ebenenschnitt und Konturen

Vollständige Einzelfunktionsabnahme bleibt teilweise offen.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0031 | `wasserschnitt` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [114](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-114), [138](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-138), [162](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-162) |
| CPPI-0032 | `wasserlinie` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [113](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-113), [137](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-137), [161](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-161) |
| CPPI-0033 | `clip_polygon` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [114](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-114), [138](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-138), [162](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-162) |
| CPPI-0034 | `konturketten` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [114](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-114), [138](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-138), [162](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-162) |
| CPPI-0035 | `ringflaeche` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [113](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-113), [137](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-137), [161](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-161) |
| CPPI-0036 | `ringmomente` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [113](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-113), [137](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-137), [161](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-161) |
| CPPI-0037 | `wasserlinien_ringe` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [113](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-113), [137](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-137), [161](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-161) |
| CPPI-0038 | `punkt_in_ring` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [113](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-113), [137](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-137), [161](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-161) |
| CPPI-0039 | `einzigartige_konturpunkte` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [114](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-114), [138](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-138), [162](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-162) |
| CPPI-0040 | `polygonzug` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [114](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-114), [138](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-138), [162](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-162) |
| CPPI-0041 | `deckel_setzen` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [114](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-114), [138](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-138), [162](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-162) |

### Mesh- und Kraftkern

Fachliche Pfade und Modellgrenzen sind testspezifisch.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0042 | `mesh_volumen` | Aktiv angebunden | [39.033](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-103)<br>[75.383](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-127)<br>[161.100](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-151) | [28.483 / 1.370x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-103)<br>[43.927 / 1.716x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-127)<br>[88.660 / 1.817x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-151) |
| CPPI-0043 | `mesh_flaeche` | Aktiv angebunden | [48.097](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-104)<br>[92.543](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-128)<br>[179.080](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-152) | [28.143 / 1.709x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-104)<br>[43.780 / 2.114x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-128)<br>[82.847 / 2.162x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-152) |
| CPPI-0044 | `massenschwerpunkt` | Aktiv angebunden | [57.910](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-105)<br>[65.813](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-106)<br>[101.620](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-129)<br>[115.173](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-130)<br>[234.037](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-153)<br>[257.297](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-154) | [28.280 / 2.048x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-105)<br>[28.390 / 2.318x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-106)<br>[44.147 / 2.302x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-129)<br>[45.170 / 2.550x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-130)<br>[87.090 / 2.687x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-153)<br>[97.940 / 2.627x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-154) |
| CPPI-0045 | `massentraegheit` | Aktiv angebunden | [241.983](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-107)<br>[429.310](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-108)<br>[385.690](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-131)<br>[523.637](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-132)<br>[1062.493](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-155)<br>[2088.733](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-156) | [47.010 / 5.147x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-107)<br>[50.240 / 8.545x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-108)<br>[56.233 / 6.859x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-131)<br>[54.860 / 9.545x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-132)<br>[181.283 / 5.861x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-155)<br>[208.760 / 10.005x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-156) |
| CPPI-0046 | `ittc_reibungsbeiwert` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [117](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-117), [141](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-141), [165](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-165) |
| CPPI-0047 | `wrench_verschieben` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [117](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-117), [141](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-141), [165](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-165) |
| CPPI-0048 | `aggregiere_kraftbeitraege` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [117](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-117), [141](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-141), [165](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-165) |
| CPPI-0049 | `widerstand` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [117](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-117), [141](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-141), [165](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-165) |
| CPPI-0050 | `added_mass_kraft` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [117](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-117), [141](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-141), [165](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-165) |

### Worker und Solver

Native Kontextmethoden sind separat unter Abschnitt 3 aufgeführt.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0051 | `dynamik2d` | Aktiv angebunden | [339.915](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-099)<br>[444.540](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-123)<br>[424.030](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-147) | [103.290 / 3.291x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-099)<br>[143.395 / 3.100x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-123)<br>[111.925 / 3.789x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-147) |
| CPPI-0052 | `beste_loesung` | Aktiv angebunden | [0.751](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-053) | [8.577 / 0.088x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-053) |

### Anzeigeinterpolation und Bewegung

Nutzung hängt vom GUI-/Anzeigepfad ab.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0053 | `quaternion_slerp` | Aktiv angebunden | [13.422](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-032) | [8.793 / 1.526x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-032) |
| CPPI-0054 | `anzeige_interpolieren` | Aktiv angebunden | [20.953](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-047) | [1264.494 / 0.017x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-047) |
| CPPI-0055 | `euler_rotation` | Aktiv angebunden | [4.742](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-049) | [8.446 / 0.561x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-049) |
| CPPI-0056 | `rotation_matrix` | Aktiv angebunden | [11.870](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-048)<br>[5.421](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-050) | [24.112 / 0.492x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-048)<br>[10.486 / 0.517x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-050) |
| CPPI-0057 | `stoss_pose` | Aktiv angebunden | [6.817](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-051) | [9.137 / 0.746x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-051) |
| CPPI-0058 | `projektion` | Aktiv angebunden | [0.702](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-052) | [8.202 / 0.086x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-052) |

### Navigation und Richtungswerte

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0059 | `winkel_360` | Aktiv angebunden | [0.209](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-055) | [7.497 / 0.028x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-055) |
| CPPI-0060 | `wrap_180` | Aktiv angebunden | [0.713](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-056) | [17.731 / 0.040x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-056) |
| CPPI-0061 | `richtungssektor` | Aktiv angebunden | [0.772](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-057) | [16.542 / 0.047x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-057) |
| CPPI-0062 | `navigationswerte` | Aktiv angebunden | [28.772](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-054) | [18.479 / 1.557x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-054) |

### Wasserpunkte und Oberflächen

Isoflächenextraktion/Marching-Cubes bleibt PyVista.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0063 | `wasser_hash` | Aktiv angebunden | [18.441](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-058) | [37.432 / 0.493x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-058) |
| CPPI-0064 | `punktlage` | Aktiv angebunden | [60.484](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-059) | [52.503 / 1.152x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-059) |
| CPPI-0065 | `wasserpunkte` | Aktiv angebunden | [86.495](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-061) | [31.412 / 2.754x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-061) |
| CPPI-0066 | `wasserspuren` | Aktiv angebunden | [92.802](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-062) | [46.918 / 1.978x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-062) |
| CPPI-0067 | `dunst_gitter` | Aktiv angebunden | [3797.949](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-060) | [137.651 / 27.591x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-060) |
| CPPI-0068 | `wasser_upsample` | Aktiv angebunden | [247.680](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-079) | [185.833 / 1.333x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-079) |
| CPPI-0069 | `wasser_glaetten` | Aktiv angebunden | [2270.913](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-082) | [152.483 / 14.893x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-082) |
| CPPI-0070 | `wasser_flaeche` | Aktiv angebunden | [254.757](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-078) | [246.417 / 1.034x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-078) |
| CPPI-0071 | `wasser_kreis` | Aktiv angebunden | [12.207](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-080) | [18.353 / 0.665x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-080) |
| CPPI-0072 | `wasser_quadrat` | Aktiv angebunden | [2.043](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-081) | [16.433 / 0.124x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-081) |
| CPPI-0073 | `wasser_spiegeln` | Aktiv angebunden | [104.019](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-001) | [34.340 / 3.029x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-001) |
| CPPI-0074 | `wasser_splat` | Aktiv angebunden | [8231.000](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-002) | [893.133 / 9.216x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-002) |
| CPPI-0075 | `wasser_kalibrieren` | Aktiv angebunden | [2.290](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-003) | [8.215 / 0.279x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-003) |

### Mesh-Selbstschnitt und Geometrieprüfung

Ersetzt nicht die noch offene allgemeine Topologievalidierung.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0076 | `mesh_selbstschnitt` | Aktiv angebunden | [21256.067](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-102)<br>[23495.100](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-126)<br>[139686.600](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-150) | [467.967 / 45.422x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-102)<br>[361.833 / 64.933x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-126)<br>[1570.600 / 88.938x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-150) |
| CPPI-0077 | `polygon_selbstschnitt` | Aktiv angebunden | [2226.225](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-026) | [11.965 / 186.061x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-026) |
| CPPI-0078 | `polygon_triangulieren` | Aktiv angebunden | [3493.670](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-027) | [25.000 / 139.747x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-027) |

### Kräfte, Pfeile und Wirkungslinien

Qt-/VTK-Actorverwaltung bleibt Adapter.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0079 | `pfeil_daten` | Aktiv angebunden | [4.818](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-063) | [9.528 / 0.506x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-063) |
| CPPI-0080 | `pfeil_fest` | Aktiv angebunden | [5.278](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-064) | [14.700 / 0.359x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-064) |
| CPPI-0081 | `kraft_paarmoment` | Aktiv angebunden | [14.904](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-065)<br>[14.742](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-066) | [10.558 / 1.412x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-065)<br>[9.416 / 1.566x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-066) |
| CPPI-0082 | `kraft_skala` | Aktiv angebunden | [0.288](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-067) | [11.464 / 0.025x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-067) |
| CPPI-0083 | `kraft_pfeile` | Aktiv angebunden | [10.966](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-068) | [11.330 / 0.968x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-068) |
| CPPI-0084 | `zusatz_pfeile` | Aktiv angebunden | [15.416](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-069) | [11.868 / 1.299x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-069) |
| CPPI-0085 | `moment_bogen` | Aktiv angebunden | [18.040](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-070)<br>[17.982](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-071) | [9.798 / 1.841x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-070)<br>[9.764 / 1.842x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-071) |
| CPPI-0086 | `strich_linien` | Aktiv angebunden | [759.136](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-072) | [19.960 / 38.033x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-072) |
| CPPI-0087 | `wirkungslinie` | Aktiv angebunden | [203.876](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-073) | [102.872 / 1.982x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-073) |

### Hauptachsen

Eigenlöser bleibt NumPy, VTK-Actoradapter bleibt Python.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0088 | `achse_kanonisieren` | Aktiv angebunden | [4.512](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-075) | [18.484 / 0.244x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-075) |
| CPPI-0089 | `hauptachsen_aufbereiten` | Aktiv angebunden | [29.416](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-074) | [29.480 / 0.998x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-074) |
| CPPI-0090 | `grafik_hauptachsen` | Aktiv angebunden | [12.840](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-096)<br>[14.720](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-120)<br>[14.440](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-144) | [37.975 / 0.338x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-096)<br>[37.630 / 0.391x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-120)<br>[50.640 / 0.285x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-144) |

### Körpergrafik

PyVista-/VTK-Objekte werden weiterhin im Adapter verwaltet.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0091 | `grafik_transformieren` | Aktiv angebunden | [45.430](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-097)<br>[36.585](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-121)<br>[52.185](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-145) | [67.565 / 0.672x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-097)<br>[63.395 / 0.577x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-121)<br>[91.050 / 0.573x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-145) |
| CPPI-0092 | `grafik_farbgeometrie` | Aktiv angebunden | [73.330](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-094)<br>[51.970](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-118)<br>[70.310](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-142) | [74.750 / 0.981x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-094)<br>[50.400 / 1.031x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-118)<br>[81.900 / 0.858x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-142) |
| CPPI-0093 | `grafik_meshes_vereinen` | Aktiv angebunden | [117.990](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-095)<br>[108.420](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-119)<br>[197.110](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-143) | [674.010 / 0.175x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-095)<br>[550.890 / 0.197x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-119)<br>[1211.010 / 0.163x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-143) |
| CPPI-0094 | `grafik_dreieckszellen` | Aktiv angebunden | [89.534](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-077) | [102.280 / 0.875x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-077) |

### Kamera und Instrumente

Qt, SVG/XML- und VTK-Objektverwaltung bleiben Adapter.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0095 | `kameralage` | Aktiv angebunden | [12.971](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-084) | [20.221 / 0.641x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-084) |
| CPPI-0096 | `kamera_aktualisieren` | Aktiv angebunden | [90.646](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-083) | [77.996 / 1.162x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-083) |
| CPPI-0097 | `instrument_aufbereitung` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [085](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-085), [086](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-086), [087](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-087) |
| CPPI-0098 | `svg_rahmen` | Aktiv angebunden | [0.964](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-090) | [24.265 / 0.040x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-090) |
| CPPI-0099 | `geschwindigkeitseinheiten` | Aktiv angebunden | [0.518](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-091) | [23.192 / 0.022x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-091) |

### Grundformen und Formgeometrie

Formerkennung und weitere Eingabe-/Topologievalidierung sind damit nicht
abgeschlossen.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0100 | `form_mesh` | Aktiv angebunden | [22.700](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-009)<br>[6.390](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-010)<br>[4.400](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-011)<br>[3832.345](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-012)<br>[96.305](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-013)<br>[112.355](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-014)<br>[6.450](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-015)<br>[65.470](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-016)<br>[81.155](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-017) | [12.090 / 1.878x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-009)<br>[8.895 / 0.718x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-010)<br>[8.855 / 0.497x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-011)<br>[179.780 / 21.317x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-012)<br>[17.470 / 5.513x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-013)<br>[20.640 / 5.444x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-014)<br>[9.735 / 0.663x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-015)<br>[11.015 / 5.944x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-016)<br>[12.895 / 6.294x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-017) |
| CPPI-0101 | `form_ring` | Aktiv angebunden | [10.372](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-018) | [12.680 / 0.818x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-018) |
| CPPI-0102 | `form_schwerpunkt` | Aktiv angebunden | [27.943](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-019) | [16.090 / 1.737x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-019) |
| CPPI-0103 | `form_zentrieren` | Aktiv angebunden | [47.583](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-020) | [34.159 / 1.393x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-020) |
| CPPI-0104 | `form_liegend` | Aktiv angebunden | [5.912](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-021) | [17.230 / 0.343x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-021) |
| CPPI-0105 | `form_huellflaechen` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [022](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-022), [023](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-023), [024](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-024) |
| CPPI-0106 | `form_huelldreiecke` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [022](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-022), [023](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-023), [024](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-024) |
| CPPI-0107 | `form_faecher` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [025](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-025) |

### OBJ-Geometrie

Datei-/Schemaadapter bleiben Python.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0108 | `obj_transformieren` | Aktiv angebunden | nicht separat gemessen | nur Elternblock: [028](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-028) |

### Voxel-Hilfen

Optionaler CPU-Voxelpfad; vollständige Genauigkeitsmatrix offen.

| Kennung | Interface | Status | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|
| CPPI-0109 | `voxel_paare_bereit` | Aktiv angebunden; optionaler Pfad | nicht separat gemessen | nur Elternblock: [008](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-008) |
| CPPI-0110 | `voxel_intervalle` | Aktiv angebunden; optionaler Pfad | [31.968](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-007) | [8.239 / 3.880x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-007) |

### Zusätzlicher Solver-Export

Öffentlicher Modul-Export außerhalb der verpflichtenden `FUNKTIONEN`-Liste.

| Kennung | Interface | Status | Hinweis | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|---|
| CPPI-0111 | `linear_loesen` | Aktiv angebunden | Solver-Hilfsfunktion | nicht separat gemessen | nur Elternblock: [100](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-100), [101](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-101), [124](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-124), [125](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-125), [148](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-148), [149](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-149) |

Zusätzliche öffentliche Kompatibilitäts-/Diagnoseattribute werden nicht als
fachliche Python/C++-Schnittstelle gezählt.

## 3. Methoden nativer Kontextklassen

| Kennung | Interface | Status | Hinweis | Python-Referenz [µs] | V0.10 [µs / Faktor] |
|---|---|---|---|---|---|
| CPPI-0112 | `PhysikKontext.batch` | Aktiv angebunden | Native Batches für vorbereitete exakte Modelle; Workerpfad | nicht separat gemessen | kein Einzelmesswert vorhanden |
| CPPI-0113 | `StatikKontext.residuum` | Aktiv angebunden | Native Statik-/Residualauswertung | nicht separat gemessen | nur Elternblock: [100](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-100), [101](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-101), [124](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-124), [125](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-125), [148](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-148), [149](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-149) |
| CPPI-0114 | `StatikKontext.loesen` | Aktiv angebunden | Native Statik-/Residualauswertung | nicht separat gemessen | nur Elternblock: [100](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-100), [101](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-101), [124](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-124), [125](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-125), [148](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-148), [149](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-149) |
| CPPI-0115 | `StatikKontext.kontakt_start` | Aktiv angebunden | Für unterstützte vorbereitete Modellkontexte | [520.200](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-098)<br>[710.500](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-122)<br>[670.780](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-146) | [49.700 / 10.467x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-098)<br>[83.820 / 8.476x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-122)<br>[60.380 / 11.109x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-146) |
| CPPI-0116 | `StatikKontext.stationaere_kraft` | Aktiv angebunden | Native stationäre Solverstufen und dynamischer Nachlauf | nicht separat gemessen | nur Elternblock: [092](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-092) |
| CPPI-0117 | `StatikKontext.stationaere_stufe` | Aktiv angebunden | Native stationäre Solverstufen und dynamischer Nachlauf | nicht separat gemessen | nur Elternblock: [092](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-092) |
| CPPI-0118 | `StatikKontext.stationaere_dynamik` | Aktiv angebunden | Native stationäre Solverstufen und dynamischer Nachlauf | [272645.200](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-093) | [1860.300 / 146.560x](../Revisionslog/zuV0.10/Messungen/Abschlussbilanz_V0.10_2026-10-20.md#messfall-093) |

## 4. Geplante oder noch nicht vollständig native Schnittstellenfamilien

Diese Punkte sind im aktiven V0.10-Plan benannt, aber nicht als abgeschlossene
native Schnittstelle zu verstehen. Wo bereits einzelne Kerne existieren,
bezieht sich „geplant/offen“ auf den jeweils fehlenden Umfang.

| Fachlicher Umfang | Zuordnung | Status | Grund / Abnahmerest |
|---|---|---|---|
| Allgemeine Mesh-, Eingabe- und Topologievalidierung | U-V0.10-000012 | Nie vollständig nativ aktiviert; teilweise Umsetzung aktiv | Selbstschnittkerne sind vorhanden, allgemeine Validatoren und ungültige Topologien noch nicht vollständig portiert bzw. abgenommen |
| Geometrische Formerkennung | U-V0.10-000012 | Nie nativ aktiviert | `formerkennung.py` bleibt Python; vollständige Algorithmusparität und Performancebeleg fehlen |
| Modellvermessung, Konflikt- und Metadatenpfade | U-V0.10-000012 | Teilweise aktiv / Rest geplant | Einzelne Form- und OBJ-Kerne sind nativ; restliche Änderungspfade und Fehler-/Schreibtransaktionen sind offen |
| Übrige Actor-/Overlay- und Poseaufbereitung | U-V0.10-000014 | Teilweise aktiv / Rest geplant | Numerische Kerne sind teilweise nativ; Qt-/VTK-Actorverwaltung und weitere Overlayblöcke bleiben Adapter |
| Vollständige GUI-/Optik-/Instrumentabnahme | U-V0.10-000013 bis U-V0.10-000016 | Nicht vollständig abgenommen | Sichtbare Läufe existieren, aber keine vollständige Referenzbild-, Langzeit- und Geräteabnahme |
| OpenCL-/GPU-Kernelübertragung | U-V0.10-000018 | Nie als C++-Kernel aktiviert; vorhandener Pfad ist OpenCL | Optionaler GPU-Pfad und CPU-Voxelkerne sind vorhanden; allgemeine Übertragung/Genauigkeitsmatrix steht aus |
| Vollständige Einzelparität und End-to-End-Matrix | U-V0.10-000019 | Offen | Der Plan enthält verbleibende strenge numerische, Modell- und End-to-End-Gates |

## 5. Nicht mehr aktive Schnittstellen

Zum Erfassungszeitpunkt ist **keine** Schnittstelle mit einem belegten
Status „früher produktiv, inzwischen nicht mehr aktiv“ dokumentiert. Das
ist keine Behauptung, dass historisch nie ein solcher Fall existierte:
Die bisherigen Register enthielten dafür keine vollständige Lifecycle-
Historie.

Neue Stilllegungen sind unter ihrer unveränderten CPPI-Kennung mit
ursprünglichem Namen, letztem aktivem Stand,
Datum, Grund, Nachweis und gegebenenfalls Ersatz hier zu archivieren.
Einträge werden nicht gelöscht oder umbenannt, um eine Stilllegung zu
verbergen.

## 6. Pflege- und Nachweisregeln

Bei jeder neuen oder geänderten Python/C++-Schnittstelle sind mindestens
zu aktualisieren:

1. C++-Export und ABI-/Backendvertrag;
2. Python-Adapter und produktiver bzw. optionaler Aufrufpfad;
3. eigener CPPI-Eintrag in diesem Register mit Status, U-/A-Zuordnung und Begründung;
4. Paritäts-/Fehlertests und Performancebeleg;
5. bei Deaktivierung: Stilllegungsgrund und Ersatz.

„Produktiv angebunden“ darf nicht mit „streng numerisch abgenommen“ oder
„Performancegewinn nachgewiesen“ gleichgesetzt werden. Abweichungen,
Verschlechterungen und nicht ausgeführte optionale Pfade sind ausdrücklich
zu markieren.

Diese Datei ist die zentrale Lifecycle-Übersicht; die detaillierten
Einzelfunktions- und Messbelege verbleiben in den verlinkten Prüfplänen
und Prüfprotokollen. Die anlassbezogene Pflege ist in der
[Registerpflege-Instruktion](../../../.github/instructions/schnittstellenregister.instructions.md)
festgelegt; die Kennungsvergabe zusätzlich in der
[Nummerierungs-Instruction](../../../.github/instructions/nummerierung.instructions.md).
Ein unbeaufsichtigter Hintergrundprozess ist damit nicht eingerichtet.

## 7. Anlassprüfung V0.11 — 20.10.2026

**V0.11-Diagnoseintegration (implementiert und regressionsgeprüft;
Gesamtabnahme der Anzeige offen):**
CPPI-0006 (`Beitrag`) erhält additive optionale Diagnosefelder
`quell_id` und `originalangriff`; CPPI-0007 (`Ergebnis`) erhält einen
optionalen `kraftzustand` mit dem tatsächlichen Eingangszustand der
Kraftauswertung. CPPI-0002 (`Mesh`) transportiert zusätzlich eine
`quell_id`. Konstruktoren bleiben mit bisherigen Argumenten aufrufbar.
CPPI-0048 muss Beitragsmetadaten bei der Normalisierung erhalten;
CPPI-0112 muss die Eingangspose ohne Python-Rückruf im Batch mitführen.
Die Änderungen verändern keine Kräfte oder Integrationsgleichungen.
CPPI-0114 (`StatikKontext.loesen`) wird im selben Paket additiv um
`solverkriterien` im erfolgreichen robusten Ergebnis ergänzt. Transportiert
werden die ursprünglichen Residuen/Grenzen, einschließlich des gesonderten
Rollscan-Entscheids; keine nachträgliche GUI-Toleranz und keine Änderung
der bisherigen Konvergenzentscheidung.
Erneuter nativer Build mit
`.\.venv\Scripts\python.exe -m pip install -e . --no-deps` erfolgreich.
Die [Integrationstests](../../../tests/test_kraefte_integration.py) prüfen
Metadatenerhalt, native Rundreise, gleichnamige Quellinstanzen, explizite
Nullzustände, letzte Batch-Eingangspose, gemeinsame GUI-Snapshotreferenz
und die zum tatsächlichen Integratorschritt äquivalente Anzeigebilanz
mit Dämpfung/Added Mass. Die
[nativen Statiktests](../../../tests/test_native_statik.py) vergleichen
die ursprünglichen robusten Kriterien mit der Python-Referenz.
Gesamtregression dieses Pakets: **1386 bestanden, 1 Skip, 1 historischer
Settings-Manifestfehler**, `QT_QPA_PLATFORM=offscreen`, 59,94 s.
Der bekannte Fehler bleibt gemäß Nutzerentscheidung dokumentiert;
keine Behauptung eines grünen Gesamtabschlusses.

| Interface | Python-Referenz | V0.11 | Aktueller Vertrags-/Nutzungsnachweis |
|---|---|---|---|
| CPPI-0002 `Mesh` | nicht separat gemessen | nicht separat gemessen | Quell-ID in Hydro-/Körpervorbereitung transportiert; Integration und native Massentests |
| CPPI-0006 `Beitrag` | nicht separat gemessen | nicht separat gemessen | Quell-ID und bestätigter Originalpunkt bleiben bei Rundreise erhalten |
| CPPI-0007 `Ergebnis` | nicht separat gemessen | nicht separat gemessen | Tatsächlicher Kraft-Eingangszustand getrennt vom Integrator-Endzustand |
| CPPI-0048 `aggregiere_kraftbeitraege` | nicht separat gemessen | nicht separat gemessen | Normalisierung erhält Diagnosemetadaten; Python-/C++-Integrationstests |
| CPPI-0080 `pfeil_fest` | nicht separat gemessen | nicht separat gemessen | Produktiver Snapshotrenderer verwendet die vorhandenen absoluten Kopf-/Schaftdaten; tatsächliche Mappernetze, Normalen und vier Richtungen in den Integrationstests geprüft |
| CPPI-0085 `moment_bogen` | nicht separat gemessen | nicht separat gemessen | Freier Snapshotbogen verwendet den bestehenden Einheitsbogenkern; Darstellungs- und Renderingtests |
| CPPI-0112 `PhysikKontext.batch` | nicht separat gemessen | nicht separat gemessen | Letzte Eingangspose und Quell-IDs ohne Python-Rückruf im nativen Batch |
| CPPI-0114 `StatikKontext.loesen` | nicht separat gemessen | nicht separat gemessen | Robuste Originalkriterien einschließlich Rollscan werden im Ergebnis mitgeführt |

Die vorhandenen V0.10-Einzel-/Elternblockmessstände werden durch diese
Vertragsprüfungen nicht ersetzt. Noch offene sichtbare Abnahme,
vollständige Modell-/Modusparität und Leistungsnachweise stehen im
[V0.11-Umsetzungsplan, Abschnitt 9.10](../Revisionslog/zuV0.11/Umsetzungsplan_V0.11.md#910-anzeigeoptionen-netzvorlagen-und-nachhermessungen).

**Weitere Aufrufpfadprüfung V0.11:**
Der zusätzliche Vista-Kraftzeichenpfad ist entfernt. Das Demo-HUD
verwendet die gemeinsame Snapshotbilanz, nicht mehr `text_zeile` als
separate numerische Auftriebsinterpretation. CPPI-0079 (`pfeil_daten`),
CPPI-0081 (`kraft_paarmoment`), CPPI-0083 (`kraft_pfeile`) und
CPPI-0084 (`zusatz_pfeile`) bleiben als verpflichtende Exporte mit
Python-Adaptern und historischen Mess-/Regressionaufrufen erhalten.
Diese Anbindung belegt keine Verwendung durch die neue produktive
Kraftanzeige. Eine erneute produktive Aktivierung dieser alten
Ableitungen ist nicht sinnvoll, weil sie den gerade abgelösten
Parallelzeichenpfad wiederherstellen würde. Vor einer Vertragsstilllegung
sind die historischen Messwerkzeuge und Verbraucher ausdrücklich
abzugleichen; derzeit keine Exportlöschung oder neue CPPI-Kennung.
CPPI-0080 und CPPI-0085 bleiben im gemeinsamen Zeichenpfad eingebunden.

Die zusätzliche Netzvorlage mit Normalentransformation, dunkle
VTK-Silhouetten, Frame-/Bezugsansicht und Anzeigenfilter ändern
keine native Signatur oder Integrationsgleichung; hierfür kein erneuter
nativer Build erforderlich. Die in Abschnitt 9.10 verlinkten
Renderer-Nachhermessungen enthalten auch Adapter-/Python-/VTK-Kosten,
sind ausdrücklich keine Einzelmessungen dieser Interfaces und ersetzen
keine freigegebenen V0.10-Messstände.
Gesamtlauf dieses damaligen Folgestands: **1484 bestanden, 1 Skip,
1 bekannter Settings-Manifestfehler**, 87,45 s, beide verfügbaren
Rechenpfade in den zugehörigen Integrationstests. Dies ist weiterhin
keine vollständige Modell-/Modus- oder Leistungsabnahme.

**Erweiterte Aufrufpfad- und Lebenszyklusprüfung V0.11:**
Die gemeinsame Anzeige besitzt keinen synchronen GUI-Ersatzrechenpfad
mehr. Fehlende Workerdaten invalidieren die Anzeige ausdrücklich.
Importe erneuern Laufzeitkörper, Quellen und Generationen; entfernte
Körper werden einschließlich bereits ausgeblendeter Modelle abgebaut.
100 Importe mit unterschiedlichen Körpernamen prüfen die globale
Statikauftragsbegrenzung und den letzten aktuellen Snapshot in beiden
Backends. Auch ohne angeschlossenen Plotter werden Kraftdaten und
Generations-/Rendercaches entfernt.

Die reale Paritätsmatrix umfasst Quader und Optimist/Folkeboot/Yacht1,
statische sowie stationäre Residuen und die äquivalente teilimplizite
Dynamikbilanz. Stationäre Modellfälle werden mit und ohne zusätzliche
lineare/quadratische Widerstandsparameter und Added Mass geprüft.
Explizite Nullbeschleunigung liefert einen gültigen Nullbeitrag;
fehlende Beschleunigungsdiagnose in Pause bleibt als Teilsumme sichtbar.
Nichtkonvergenz wird nicht zur erfolgreichen Lösung umgedeutet.

CPPI-0080/0085 bleiben produktiv im Snapshotrenderer; CPPI-0079,
CPPI-0081, CPPI-0083 und CPPI-0084 bleiben ausschließlich in den
historischen Adapter-/Mess-/Regressionspfaden erhalten. Die verbliebenen
Demoaufrufe von `kraefte_daten_setzen` sind ein kompatibler Eingang in
denselben Snapshotrenderer, kein zweiter Kraftzeichenpfad.
Diese Python-/GUI-Änderungen benötigen keinen weiteren nativen Build
und keine neue CPPI-ID. Die 600-Zyklen-Windowsproben erfassen zusätzlich
den Prozessspeicher einschließlich nativer Allokationen; sie sind weder
isolierte Interface-Performancewerte noch eine Leckfreiheitsgarantie.
Für sämtliche hier genannten Interfaces weiterhin
**nicht separat gemessen**. Aktuelle Befehle, Ergebnisse, Rohbelege und
offene physische Monitor-/Leistungsabnahme:
[Umsetzungsplan 9.13](../Revisionslog/zuV0.11/Umsetzungsplan_V0.11.md#913-trigger--import--und-modellabschlussnachweise).
Letzter Gesamtlauf: **1620 bestanden, 1 Skip, 1 bekannter historischer
Settings-Manifestfehler**, 150,71 s (`QT_QPA_PLATFORM=offscreen`).
Verlangsamte GUI zusätzlich mit geöffnetem und geschlossenem
Wertefenster geprüft: je vier erfolgreiche Fälle in offscreen und
echten Windows-Qt-Fenstern, beide Rechenpfade, keine Workerblockierung
und unverändertes GUI-Timerintervall.
Keine zusätzliche Integrationsregression; weiterhin keine vollständig
grüne Gesamtsuite und keine fachliche oder Leistungsfreigabe.

Für U-V0.11-000003/000004 wurden CPPI-0005 (`Wrench`),
CPPI-0006 (`Beitrag`), CPPI-0047 (`wrench_verschieben`) und CPPI-0048
(`aggregiere_kraftbeitraege`) mit den tatsächlichen Python-Verträgen
und Aufrufpfaden abgeglichen. Der neue
[Anzeigeadapter](../../../code/python/segelphysik/core/kraefte_anzeige.py)
verwendet vorhandene Wrench-/Aggregationsfunktionen. Die
[Anzeigedatentests](../../../tests/test_kraefte_anzeige.py) prüfen
explizit Python- und C++-Pfad; bisherige Status bleiben unverändert.
Keine neuen Exporte, Signaturen oder Python-Rückrufe im nativen Batch.
Ein nativer Neubuild ist für diese reine Python-Datenbasis nicht erforderlich.

Die ursprüngliche Bestandsaufnahme zu CPPI-0112 (`PhysikKontext.batch`) und dem
Ergebnistransport zeigt fehlende stabile Quellinstanz-IDs und fehlenden
expliziten Kraftpose/-zeit-Bezug. Der native Schritt liefert den neuen
Körperzustand zusammen mit an der Eingangspose ausgewerteten Kräften.
Vor produktiver Anzeigeanbindung sind minimale Diagnoseverträge zu
konkretisieren und gegebenenfalls neue Interfaces vor Implementierung
mit eigenen CPPI-IDs zu registrieren. Die unveränderten bestehenden
Pfade bleiben erhalten; kein automatischer Backendwechsel.

Die [V0.11-Baselines](../Revisionslog/zuV0.11/Umsetzungsplan_V0.11.md)
sind ausschließlich Rendering-Gesamtpfadmessungen, keine neuen
Einzelmessungen dieser Interfaces. Alle bisherigen V0.10-Messstände
bleiben erhalten; für die hier berührten Interfaces weiterhin
**nicht separat gemessen**. Vollständige Anzeigeintegration und
Solver-/Integratorparität waren zu diesem Erhebungszeitpunkt noch offen;
der weiterentwickelte Stand ist oben getrennt dokumentiert.

U-V0.11-000006 verwendet außerdem CPPI-0085 (`moment_bogen`) weiterhin
als Geometriekern: Ein 240°-Einheitsbogen wird im rendererfreien
[Darstellungsbaustein](../../../code/python/segelphysik/core/kraefte_darstellung.py)
auf die tatsächliche Momentenachse ausgerichtet. Kein neuer Export und
keine Änderung der bisherigen Signatur oder physikalischen Schwellwerte;
die alte Achsenfunktion bleibt für ihre bisherigen Aufrufer unverändert.
Die [Darstellungstests](../../../tests/test_kraefte_darstellung.py) prüfen
beide Pfade einschließlich Drehsinn, Null, Vorzeichenwechsel und
Generationscache. Die produktive Anbindung an den neuen Actorpfad ist
inzwischen regressionsgeprüft; sichtbare Verfahrensabnahme und vollständiger
Altpfadabbau bleiben offen. Weiterhin **nicht separat gemessen**.
