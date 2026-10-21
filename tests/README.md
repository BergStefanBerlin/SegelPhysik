# Tests ausführen und pflegen

Aus dem Repository-Hauptverzeichnis, in PowerShell:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q
```

Der Standardlauf wählt keine Marker ab. Er sammelt sowohl die regulären
Tests als auch die vier separat benannten Prüfdateien unter
[code/cpp/tests](../code/cpp/tests). Er benötigt den gebauten nativen
Backend und die Qt-/Renderingvoraussetzungen.

## Gezielte Profile

| Anlass | Auswahl |
|---|---|
| Lokale Änderung | Betroffene Dateien/Node-IDs in einem Aufruf; indirekte Verbraucher und Fehler-/Grenzfälle ergänzen. |
| Integration / unklare Reichweite | Passende Integration/Backendgrenzen; bei nicht sicher begrenzter Auswirkung Standardlauf. |
| Modelländerung | Betroffenes Modell und geänderte gemeinsame Lader-/Manifestverträge. |
| Sammlung / globale Fixtures / Meilenstein | Standardlauf einschließlich nativer Prüfungen. |
| Performanceänderung | Korrektheit/Parität des betroffenen Pfads plus separate vergleichbare Messung. |

Beispiel für Materialglanz und die betroffenen Frame-/Grafikgrenzen:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_materialglanz.py tests\test_frames.py tests\test_native_grafikgeometrie.py
```

Ein explizites günstiges Profil ist:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m "not slow and not gui and not integration and not hardware"
```

Dieses Profil ist kein vollständiger Stabilitätsnachweis. Marker sind in
[pyproject.toml](../pyproject.toml) registriert. `slow` kennzeichnet Fälle,
die in der V0.12-Baseline mindestens eine Sekunde benötigten; parametrisiert
markierte Funktionen können auch schnellere Einzelvarianten enthalten.
`native` bedeutet Build-Abhängigkeit, nicht automatisch langsam.
`gui` umfasst echte Qt-/Renderkontexte, nicht bloß Imports.
`diagnostic` kennzeichnet erhaltene spezielle Modell-/Fehlerverträge,
keinen Skip und kein erwartetes Fehlschlagen.

## Referenzfälle und Ausnahmen

Regulär reichen Quader, Kugel und für benötigte reale Gesamtpfade das
Folkeboot. Nicht jeden Test mit jedem Körper oder jeder Yacht kombinieren.
Offene/fehlerhafte Netze und sonstige gezielte Sonderfälle bleiben wichtig.

Der Optimist ist derzeit kein allgemeiner Stabilitätsmaßstab. Seine
Paket-/Geometrie-/Hydrodynamikverträge und ein bekannter nativer
Paritätsbefund bleiben sichtbar. `yacht1` bleibt dort, wo ein eigener
Vertrag geprüft wird, etwa Schalen-/Legacy-Editpfade oder die Diagnose
stationärer Nichtkonvergenz. Das sind begründete Ausnahmen, keine
allgemeine Yacht-Testmatrix.

## Bekannte Ausgangsbefunde vom 21.10.2026

- Der echte OpenCL-Vektoradditionstest hing in der lokalen Umgebung.
  `hardware` erlaubt die explizite Abwahl mit `-m "not hardware"` für einen
  als unvollständig gekennzeichneten Lauf. Es gibt keine automatische Abwahl.
  Eine spätere isolierte Prüfung und der abschließende ungefilterte
  Standardlauf liefen einschließlich dieses Tests durch. Die Ursache des
  ersten Hängers ist ungeklärt, nicht als behoben nachgewiesen.
- Der historische Referenzmanifesttest meldete bereits vor dem Umbau eine
  Abweichung von `konfigurationen/settings.json`.
- Die Optimist-Schrittparität meldete bereits vor dem Umbau eine
  Kraftabweichung von etwa `1.0103e-9` bei erlaubten `1e-9`.
  Der Test und seine Toleranz bleiben erhalten.

Diese Befunde dürfen weder als durch den Umbau verursachte Fehler noch als
bestandene Prüfungen dargestellt werden. Ein fehlender Hardware-/Buildnachweis
verhindert eine uneingeschränkte Gesamtfreigabe.

### Nachprüfung der Tests am Tagesende

Der Test für verborgene Navigationsanzeigen verwendet echte Widgets mit
Aufrufbeobachtung statt einer Ersatzfunktion mit veralteter Signatur.
Er prüft mehrere verdeckte Aktualisierungen und die vollständige Anzeige
des neuesten Zustands beim Öffnen.

Der Inventartest vergleicht historische Funktionsidentitäten einschließlich
ihrer Häufigkeiten statt einer festen Gesamtzahl interner Closures.
Die ausgelagerte Suche von `Koerper.gelenkwinkel_setzen.suche` nach
`Koerper._gelenkwinkel_setzen.suche` wird ausdrücklich zugeordnet und am
aktuellen Quellort geprüft. Die zwei bekannten entfernten Rendererclosures
bleiben separat ausgewiesen; das historische Inventar wird nicht geändert.

Beide korrigierten Tests bestehen gezielt. Der vorherige vollständige Lauf
nach Korrektur des Navigationstests hatte 1823 bestandene Tests, drei Fehler
und einen Skip. Er enthält noch nicht die anschließende Inventartestkorrektur.
Referenzkonfiguration und Optimist-Parität sind weiterhin offen.
Ein zusätzlicher Diagnoseversuch mit identischer Eingabepose für den
Kraftvergleich beseitigte die unabhängige Trajektorienabweichung des Optimist
nicht (1,30546e-12 bei erlaubten 1e-12). Diese Testvariante wurde nicht
übernommen; ursprüngliche Paritätstoleranzen und Tests bleiben erhalten.
Ohne ausdrückliche Ausnahme bleiben Commit, Tag und Push dadurch blockiert.

### Ausdrücklich genehmigte Sicherung als Tag 0.13

Am 21.10.2026 um 19:24 Uhr hat der Nutzer ausdrücklich genehmigt,
die beiden verbleibenden Fehler beim nächsten Termin zu bearbeiten und
den Stand ausnahmsweise trotzdem zu committen, als `0.13` zu taggen und
zu pushen. Diese Freigabe gilt nur für diese Sicherung, nicht als generelle
Änderung der Test-/Release-Regeln oder fachliche Gesamtfreigabe.

Ungefilterter Kontrolllauf vor der Sicherung:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q
```

**1824 bestanden, 2 fehlgeschlagen, 1 übersprungen; 147,76 s.**
Navigation und Inventar bestehen nun auch im Gesamtprofil.
Offen für den nächsten Termin:

- `test_referenzmanifest_umfasst_modelle_konfiguration_und_optik`:
  Abweichung der aktuellen GUI-Einstellungen in
  [settings.json](../konfigurationen/settings.json) vom historischen
  Sicherungscommit. Die Trennung historischer Referenzprüfung von späteren
  Anzeige-/Schemaeinstellungen ist fachlich zu klären; keine Referenzhashes
  wurden überschrieben.
- `test_nativer_batch_gegen_jeden_referenzschritt[optimist]`:
  maximale Momentenabweichung `1,01024256e-9` bei bestehender absoluter
  Grenze `1e-9`, betroffen sind Gesamtmoment z und Kielmoment z.
  Ursache und geeigneter Paritätsvertrag bleiben zu untersuchen.

Keine Tests übersprungen oder Toleranzen gelockert, um diese Freigabe zu
erzielen. Der vorhandene Skip bleibt im Gesamtergebnis sichtbar. Die
Ausnahme ist keine Erklärung, dass die beiden Tests falsch seien oder
die numerische Abweichung bereits behoben wäre.

## Pflege und Nachweise

Die [aktive Testpflege-Instruction](../.github/instructions/teststruktur.instructions.md)
regelt Auswahl, Fixtures, Struktur und Genauigkeit.
Der [historische V0.12-Abschlussnachweis](../doc/WegZuV1.0/Revisionslog/zuV0.12/Umsetzungsanleitungen/Abschlussnachweis_Teststruktur_und_Speed_V0.12.md)
führt den tatsächlichen Umbaustand und verlinkt die Maschinenbelege.
Historische Testkennungen bleiben erhalten; verschobene Node-IDs sind
zugeordnet. Korrektheit und Wandzeitmessung bleiben getrennt.

Vergleichsmessungen ohne konkurrierende Last durchführen. Suitekosten je
Stand mindestens dreimal, Produktivpfade nach getrenntem Warm-up mindestens
fünfmal messen. Rohzeiten, Median, Streuung, Umgebung und genaue Arbeitslast
angeben. Eine kleinere Testauswahl ist keine Beschleunigung derselben Arbeit.
Die Release-Instruction und ihre Commit-Prüfungen gelten unabhängig davon.
