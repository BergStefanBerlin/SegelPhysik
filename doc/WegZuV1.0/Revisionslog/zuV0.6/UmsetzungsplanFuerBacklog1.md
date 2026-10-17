# Umsetzungsplan für Backlog 1 – sofortige Punkte

**Stand:** 17.10.2026
**Backlog:** [Backlog v1](../../../Backlog/Backlog_v1.md)
**Ziel:** Die unmittelbaren fachlichen und technischen Voraussetzungen für
eine spätere Hydrodynamik sowie die offene Produktions- und Live-Abnahme
geordnet vorbereiten. Es werden keine neuen physikalischen Simulationen,
Kraftgesetze oder Modellbeiträge eingebaut.

## 0. Verbindliche Abgrenzung

Dieser Plan bereitet Verträge, Datenanforderungen, Dokumentation und
Abnahmeumgebung vor. Die Ausnahme des Nutzers gilt für die bereits
implementierte Auftriebssimulation und weitere vorhandene physikalische
Teile: Sie dürfen geprüft, gemessen und bei nachgewiesenem Fehler korrigiert
werden. Sie ist keine Freigabe, neue Hydrodynamik-/Aerodynamikbeiträge oder
weitere physikalische Modelle zu implementieren.

Zulässig sind:

- Daten-/Schnittstellenentwürfe und offene Entscheidungslisten für spätere
  Umweltzustände, ohne neue Laufzeitberechnung dieser Zustände.
- Tests und Benchmarks der bereits vorhandenen Yacht-/Auftriebs-/Dynamikpfade.
- Phase-11-Loader-, Migrations- und Kompatibilitätsarbeiten für bestehende
  Modelle und bestehende Physik.

Nicht Teil dieses Plans sind:

- neue hydrodynamische oder aerodynamische Kraftbeiträge, Koeffizienten,
  Polaren, Widerstands- oder Added-Mass-Modelle;
- Code, der Wind-/Strömungszustände in neue Kräfte oder Momente umsetzt;
- neue physikalische Referenzsimulationen, die eine solche Berechnung
  voraussetzen. Für spätere Referenzfälle dürfen hier nur Anforderungen und
  Quellen gesammelt werden, nicht Modellwerte freigegeben oder umgesetzt.

## 1. Umfang und Reihenfolge

| Reihenfolge | Backlog-ID | Arbeitspaket | Voraussetzung |
|---:|---|---|---|
| 1 | BL1 | Künftige Eingabedaten und Schnittstellen dokumentieren, ohne Kraftmodelle festzulegen oder umzusetzen | Keine; bestehende Spezifikation und Datenverträge prüfen |
| 2 | BL3 | Baseline von Rückstand und Nachholrate auf dem aktuellen, unveränderten Pfad messen | Zielhardware und dokumentierte Referenzkonfiguration |
| 3 | BL4 | Sichtbare Live-Baseline ausführen und widersprüchliche Nachweise abgleichen | BL3-Messdefinition und vorhandene Live-Benchmark-Werkzeuge |
| 4 | BL2 | Phase-11-Kandidatenpfad isoliert vergleichen; Cutover erst nach erfolgreicher Kandidatenprüfung freigeben | Bestehende Paket-/Golden-Daten, Testbestand und erfüllte G1–G4-Gates |

BL1 kann parallel zur Vorbereitung der Messläufe spezifiziert werden. BL3 und
BL4 liefern Baselines für BL2. BL2 muss nach dem Umschalten auf den Paket-
Kandidatenpfad alle betroffenen BL3-/BL4-Tests und Messungen erneut
ausführen. Die Messungen vor und nach dem Kandidatenwechsel sind getrennt
auszuweisen. Der Kandidatenpfad wird zunächst nur in einer isolierten
Testkonfiguration aktiviert; der produktive Standard wird erst nach
bestandenen Vergleichs- und Abnahmegates geändert. Wenn ein Gate scheitert,
ist der betroffene Punkt zu korrigieren und erneut zu messen; die Reihenfolge
darf nicht dazu benutzt werden, ein offenes Gate zu umgehen.

## 2. Verbindliche Regeln

1. Keine empirischen Koeffizienten, Wind-/Strömungsprofile oder vermeintlich
   realistischen Parameter erfinden oder als Implementierungsauftrag
   formulieren.
2. Bereits implementierte Auftriebssimulation und weitere bestehende,
   validierte physikalische Teile unverändert lassen, außer bei einem
   nachgewiesenen Fehler mit gezieltem Regressionstest.
3. Der Paketpfad darf für BL2 in einer isolierten Testkonfiguration
   umgeschaltet werden. Produktiven Standardpfad nicht ändern, Legacy-
   Adapter nicht entfernen und Rückfallpfad nicht löschen, bevor alle
   Phase-11-Gates bestanden und die Freigabe dokumentiert ist.
4. Messungen müssen ihre Eingaben, Umgebung, Versionen, Konfiguration,
   Rohwerte, Auswertung und Abweichungen festhalten. `null`, fehlend oder
   nicht reproduzierbar bedeutet „nicht abgenommen“.
5. Änderungen werden in fachlich abgegrenzten Schritten getestet. Bei einem
   fehlgeschlagenen Gate wird nicht weiter zur Freigabe übergegangen.

## 3. BL1 – Vorbereitung künftiger Umwelteingaben und Schnittstellen

### Ziel und Ergebnisse

Es wird nur dokumentiert, welche Informationen eine spätere, ausdrücklich
freizugebende Hydrodynamik-/Aerodynamikphase benötigen könnte. Die Arbeit
legt weder Kraftansätze noch Koeffizienten fest und fügt keine Laufzeit-
Eingabe oder Kraftberechnung hinzu.

Vorbereitend zu erfassen sind:

- erwartete Kategorien zukünftiger Wasser-/Luftzustände (z. B.
  Geschwindigkeit, Dichte, Zeitbezug), zunächst als offene Anforderungen;
- vorhandene Frame-, Einheiten-, Wrench- und Snapshot-Verträge, die später
  wiederverwendet werden könnten;
- offene fachliche Entscheidungen samt benötigter Quelle, Zuständigkeit und
  Freigabe, ohne sie spekulativ zu entscheiden;
- noch nicht vorhandene Referenzdaten, Koeffizienten und Gültigkeitsbereiche
  als ausdrücklich offene Punkte, nicht als angenommene Modellwerte;
- Abgrenzung zwischen der bereits implementierten Hydrostatik/Auftriebskraft
  und noch nicht implementierten dynamischen Wasser-/Luftkräften.

### Arbeitsschritte

1. Abschnitt 11 der Spezifikation v0.5, Phase 12, bestehende Kraftbeiträge
   und aktuelle Schnittstellen inventarisieren. Ergebnis der Bestandsaufnahme
   ist `Bestandsaufnahme_Umwelteingaben_BL1.md`; es werden vorhandene
   Widerstands-/Fluid-/Added-Mass-Funktionen als Bestand, nicht als
   Implementierungsauftrag, ausgewiesen.
2. Bereits vorhandene Physik von zukünftigem, noch nicht implementiertem
   Verhalten klar trennen; bestehende Auftriebssimulation nicht als offene
   neue Hydrodynamik behandeln.
3. Offene fachliche Entscheidungen als Fragen-/Quellenliste dokumentieren.
   Keine Kraftformel, numerische Koeffizienten, Wind-/Strömungsprofile oder
   erwarteten neuen Kraftwerte festlegen.
4. Für spätere Arbeit bloß die nötigen Referenzdatenarten und deren Herkunft
   benennen; keine Simulationen ausführen, die nicht implementierte Beiträge
   voraussetzen.
5. Schnittstellenentwurf als nicht implementierungsfreigebend kennzeichnen
   und mit der fachlichen Freigabeinstanz abstimmen.

### Tests und Abnahmekriterien

- Keine ausführbaren Kraft-/Hydrodynamik-/Aerodynamiktests hinzufügen.
- Vorhandene Einheiten-, Frame- und Kraftvertragstests nur inventarisieren
  und als mögliche Basis späterer Arbeit verweisen.
- Dokumentationsreview prüft, dass keine neuen Kraftformeln, Koeffizienten,
  Laufzeitinputs oder Erfolgserwartungen für nicht existierende Beiträge
  eingeführt wurden.
- Abnahme dieses Vorbereitungspunkts bedeutet nur, dass offene Daten- und
  Quellenbedarfe verständlich festgehalten sind; sie bedeutet ausdrücklich
  keine fachliche Freigabe oder Implementierungsfreigabe für neue Physik.

## 4. BL3 – Rückstand und Nachholrate auf Zielhardware

### Arbeitsschritte

1. Hardware, Betriebssystem, Python-/Qt-/VTK-Version, Modell,
   Hydrostatik-Backend und Konfiguration für den Lauf dokumentieren.
2. Vorhandene Regressionen für Zeitbuchung, Pause/Fortsetzen,
   verspätete Workerresultate, Snapshot-Prozessworker sowie
   Körper-/Moduswechsel gezielt ausführen.
3. Den vorhandenen Benchmark `werkzeuge\benchmark_nachholen.py` auf der
   Zielhardware mit der Yacht-Referenz ausführen. Standardmäßig erzeugt er
   drei Wiederholungen mit jeweils `3 s` künstlichem Rückstand.
4. Zusätzlich die vereinbarte zehnminütige Lastmessung ohne stilles
   Verwerfen von Simulationszeit durchführen. Angeforderte und übernommene
   Zeit, Rückstand, Ein-Sekunden-Nachholfenster, Gesamtnachholrate und
   Überlastpausen zeitlich korreliert protokollieren.
5. Rohdaten und Zusammenfassung unter dem bestehenden Abnahme-/Messpfad
   sichern; BL4 verwendet dieselbe Konfiguration, soweit die Messart
   kompatibel ist. Diese Läufe verwenden ausschließlich bereits vorhandene
   Yacht-/Auftriebs-/Dynamikfunktionalität. Dies ist zunächst die Baseline
   des aktuellen Pfads; nach dem isolierten Paket-Kandidatenwechsel in BL2
   sind betroffene Messungen mit unveränderter Konfiguration zu wiederholen.
   Nach Prozessworker-Korrektur bestanden die drei Nachholraten
   `1,874 / 2,076 / 1,777 s/s`; der UI-Gate-Status wurde ebenfalls korrigiert
   und zeigte jeweils „bestanden“. Der 600-s-Lauf mit demselben Yachtmodell,
   Backend und aktiven Pflicht-Layern löste jedoch eine automatische
   Überlastpause aus; sein Live-Gate ist fehlgeschlagen. Siehe die
   versionierten Rohdaten unter `Messungen/`.

### Testanweisungen

Im Repository-Hauptverzeichnis in PowerShell:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_echtzeit_prozess.py tests\test_dynamik_6dof.py tests\test_statusanzeige.py
```

Der Nachhol-Benchmark benötigt eine funktionsfähige GUI-/Qt-Umgebung; er ist
ein eigener Messlauf und kein Ersatz für die Regressionstests:

```powershell
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe werkzeuge\benchmark_nachholen.py --scene yacht1 --rueckstand 3 --wiederholungen 3
```

Den zehnminütigen Live-Lastlauf für Zeitbilanz, Rückstand und Trend separat
ausführen:

```powershell
.\.venv\Scripts\python.exe werkzeuge\benchmark_gui_live.py --scene yacht1 --warmup 30 --duration 600 --backend exakt_union
```

Der Live-Lastlauf erfasst Rückstand und Durchsatz, aber nicht allein die
induzierte Nachholrate; diese wird separat mit `benchmark_nachholen.py`
gemessen. Beide Läufe müssen dieselbe Zielhardware, Modell- und Backend-
Konfiguration verwenden. Die Standardoptionen des Nachholskripts allein
belegen keine zehnminütige Langzeitabnahme.

### Abnahme

- Alle Zeitbuchungs- und Wechselregressionen bestehen; es gibt keine
  doppelte Zeitgutschrift, verlorene angeforderte Zeit oder veraltete
  Zustandsübernahme.
- Die Nachholrate erreicht in den vereinbarten Fenstern mindestens
  `1,25 s/s`, oder das Gate wird als fehlgeschlagen ausgewiesen.
- Rückstandstrend, maximale Rückstandshöhe und Überlastpause sind mit Rohdaten
  belegt. Kein Datenpunkt wird stillschweigend entfernt.
- Bei Nichterreichen: Ursache und Messdaten dokumentieren, keine
  Durchsatz-/Genauigkeitsschranke still lockern und BL2 nicht als vollständig
  abgenommen markieren.

## 5. BL4 – Sichtbare Live-Abnahme und Nachweisabgleich

### Arbeitsschritte

1. Den bestehenden Bericht `Abnahme_R-4a.md`, die Artefakte des
   Live-Benchmarks und die Aussagen zu BL3/BL13 vergleichen. `Abnahme_R-4a.md`
   weist bereits eine separate Nachholmessung von `4,4–4,8×` aus; historische
   Rohdaten liegen dem Bericht nicht bei. Der erste aktuelle Lauf hatte
   keinen Prozessworker, weil die Poolprüfung noch die alte `.teile`-
   Struktur statt `KoerperSnapshot.blatt_meshes` erwartete. Nach Korrektur
   und Regression bestanden die drei Nachholraten mit sichtbarem Gate-Status:
   `1,874 / 2,076 / 1,777 s/s` (siehe `Messungen/`). Der sichtbare
   Zehnminutenlauf nach der Korrektur nutzte den Prozessworker, löste aber
   eine automatische Überlastpause aus und erreichte nur `13,04` tatsächlich
   präsentierte FPS bei `205,098 ms` Frameabstand-P95. Daher bleibt die
   Live-Abnahme fehlgeschlagen; historische und aktuelle Zahlen sind wegen
   nicht identischer Bedingungen getrennt auszuweisen.
2. Wenn die Rohdaten die Abnahmedefinition nicht erfüllen, den
   Live-Benchmark mit sichtbarem Fenster auf Zielhardware erneut ausführen;
   Offscreen- und Renderaufrufzahlen sind kein Ersatz für präsentierte
   Frames.
3. Standardmäßig `30 s` aufwärmen und `10 min` messen. `exakt_union` als
   genaue Produktionsreferenz verwenden, sofern keine ausdrücklich
   freigegebene Vergleichsmessung etwas anderes verlangt.
4. Pflicht-Layer, Frame-/Präsentationsmessung, Eingabereaktion,
   Physikdurchsatz der bereits implementierten Physik, angeforderte/
   berechnete Simulationszeit, Rückstand und Trend erfassen. Fehlende Werte
   ausdrücklich als nicht messbar markieren.
5. Ergebnisse, Maschinen-/Softwaremanifest, Kommandozeile, Rohdaten und
   Interpretation im Abnahmebericht ablegen und mit BL3 verknüpfen.

### Testanweisungen

Die automatisierte GUI-/Statusregression zunächst offscreen ausführen:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_grafik_bruecke_darstellung.py tests\test_statusanzeige.py tests\test_echtzeit_prozess.py
```

Anschließend den sichtbaren Messlauf aus einer interaktiven Windows-Sitzung
starten. Der Benchmark verwendet standardmäßig `30 s` Warm-up und `10 min`
Messzeit:

```powershell
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe werkzeuge\benchmark_gui_live.py
```

Ein verkürzter Lauf darf nur als Smoke-Test bezeichnet werden, nicht als
Abnahme. Messung in einer nicht sichtbaren Sitzung oder mit Offscreen-QPA
zählt nicht für Präsentations-FPS und Eingabe-bis-sichtbar-Latenz.

### Abnahme

- Pflicht-Layer und sichtbarer Referenzablauf laufen über die volle
  Messdauer; tatsächliche präsentierte Frames und Eingabereaktion sind
  nachvollziehbar erfasst.
- Die in der Spezifikation und Phase-11-Abnahme festgelegten FPS-,
  Latenz-, Durchsatz- und Rückstandsgates bestehen.
- BL3- und BL4-Aussagen beziehen sich auf klar benannte Läufe und
  Messbedingungen; widersprüchliche Zahlen werden durch Rohdaten aufgelöst,
  nicht durch bloße Textänderung.
- Fehlende Präsentations- oder Nachholwerte sperren die betreffende
  Abnahme.

## 6. BL2 – Phase-11-Cutover

### Voraussetzungen

- Bestehende Repository-Pakete und Golden-Daten sind inventarisiert.
- Der B-03-Leistungsnachweis und T-011-Selbstüberschneidungsprüfung bleiben
  erhalten; bereits migrierte Repository-Modelle werden nicht erneut
  migriert, sofern kein konkreter Fehler das verlangt.
- Für externe Bestände liegt ein repräsentativer, freigegebener Testbestand
  vor. Fehlt er, wird diese Gate-Komponente als offen markiert und keine
  vollständige Cutover-Freigabe behauptet.

Erste externe Kandidaten `doc/Backlog/Ideen/optimist_einzelteile.zip` und
`optimist_obj.zip` wurden nur lesend geprüft. Von 20 Einzelteil-OBJ-Dateien
wurden 16 wegen nicht-planarer Polygone vom bestehenden Parser abgelehnt;
auch beide Gesamt-OBJ-Dateien wurden abgelehnt. Die README kennzeichnet den
Meterfaktor ausdrücklich als Annahme; Manifest, Material-/Dichteangaben und
Golden-Massen fehlen. Diese Archive sind damit noch kein freigegebener
Phase-11-Bestand. Es werden weder die Geometrien automatisch repariert noch
Maßstäbe oder Masseneigenschaften geraten.

### Arbeitsschritte

1. Phase-3-Inventar, Migrationswerkzeug, Settings-Schalter, Fabrikpfade,
   Adapter und alle produktiven Aufrufer erfassen.
2. Externe Nutzerbestände ausschließlich mit Dry-run zuerst untersuchen.
   Bericht muss Pfade, Validierungsresultate und geplante Änderungen
   ausweisen; Originalquellen dürfen nicht überschrieben werden.
3. Freigegebene Testbestände migrieren und Paketloader/Manifest/OBJ-
   Validierung einschließlich Fehlerfällen prüfen.
4. Paket- und Legacy-Pfade für dieselben Modelle und Abläufe gegen Golden-
   Daten vergleichen: Masse, Schwerpunkt, Trägheit, Volumen, Hydrostatik,
   statische Lösung, dynamische Trajektorie und GUI-Verhalten innerhalb der
   vorab festgelegten Toleranzen.
5. GUI-Paketwahl, Start, Körperwechsel, Einstellungen, Fehlerdiagnose und
   Rückfall über den expliziten Schalter in einer isolierten Kandidaten-
   Testkonfiguration testen; kein stiller Mischpfad. Die produktive
   Standardkonfiguration bleibt bis zur Freigabe auf dem bisherigen Pfad.
6. Performance-Gates getrennt nach Modellladen, Fabrik, Solver,
   dynamischem Schritt, Echtzeit, Rendering und GUI-Aktualisierung
   auswerten.
7. Aufrufer-/Adapter-Suche und Dokumentations-/CI-Prüfungen abschließen.
   Legacy-Adapter erst in einem separaten Schritt nach Freigabe und mit
   Rückfallplan entfernen.
8. G1–G4-Ergebnisse, Abweichungen und Freigabeentscheidung im
   Abnahmebericht erfassen. Nach dem Kandidatenwechsel alle betroffenen
   BL3-/BL4-Tests und -Messungen wiederholen und mit der Baseline vergleichen.
   Bei irgendeinem offenen Gate bleibt der produktive Standardpfad
   unverändert und der Legacy-Rückfallpfad verfügbar.

### Testanweisungen

Gezielte Migration-, Loader- und GUI-Regressionsläufe:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_migriere_modellpaket.py tests\test_modell_lader.py tests\test_manifest_baum.py tests\test_gui_laufzeit_edit.py tests\test_active_body_factory.py
```

Danach ist die vollständige Suite verpflichtend:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q
```

Zusätzlich sind Dry-run und Migration mit repräsentativen externen Daten
sowie der Alt-/Neu-Vergleich auszuführen. Automatisierte Tests allein
ersetzen diese Phase-11-Nachweise nicht.

### Abnahme

- G1 bestehende Tests und G2 neue Abnahmetests bestehen.
- G3 Alt-/Neu-Parität für unterstützte Modelle und Abläufe ist gegen
  Golden-Daten belegt.
- G4 Performance je betroffenem Pfad besteht; fehlende oder uneindeutige
  Messung ist nicht freigegeben.
- Dry-run, Nichtüberschreiben, Fehlerabbruch und Rückfallpfad sind belegt.
- Kein unberücksichtigter produktiver Altaufrufer verbleibt.
- BL3-/BL4-Baselines und Wiederholungen auf dem Paket-Kandidatenpfad
  verwenden gleiche Hardware, Modell, Einstellungen und Messdefinition;
  Unterschiede sind erklärt und erfüllen die vorhandenen Gates.
- Erst nach allen Punkten wird Phase 11 als abgenommen markiert und eine
  produktive Phase 12 als künftiger separater Auftrag erwogen. Phase 11
  aktiviert keine neuen physikalischen Beiträge. BL1 ist nur
  Vorbereitung/Dokumentation und keine fachliche Freigabe für Phase 12.

## 7. Gemeinsame Test- und Abschlussanweisung

Für jeden Codeänderungsschritt: zuerst gezielte Tests, danach die vollständige
Suite. Testbefehle und Ergebnisse, Python-/Abhängigkeitsversionen,
Betriebssystem, Hardware, Modell und Laufparameter in den jeweiligen
Nachweisen festhalten.

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q
```

Ein Testfehler, nicht verfügbarer Zielbestand, fehlender Messwert oder
fehlgeschlagenes numerisches/Performance-Gate stoppt die Freigabe des
betroffenen Arbeitspakets. Bestehende Änderungen und Messartefakte dürfen
nicht stillschweigend verworfen oder durch neue Zahlen ersetzt werden.
