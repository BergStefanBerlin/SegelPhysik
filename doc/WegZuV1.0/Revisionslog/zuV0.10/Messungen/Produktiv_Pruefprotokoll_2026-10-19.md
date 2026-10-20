# Produktive C++-Integration V0.10: Stand und offene Abnahme

## Auftrag und Geltungsbereich

Der Nutzer verlangt die vollständige produktive Migration auch langsamerer
Blöcke. Die frühere Gewinnschranke ist in Spezifikation und Plan archiviert.
Korrektheit, Robustheit, Physik und vorhandene Toleranzen bleiben verbindlich.
Dieser Bericht dokumentiert einen Zwischenstand, keinen Gesamtabschluss.
Branch: `v0.10`, Ausgangscommit `7a955c2`; Änderungen uncommittet.

## Produktiver Umfang

Standardauswahl ist `cpp`. `SEGELPHYSIK_RECHENPFAD=python` wählt ausdrücklich
die Referenz. `python_referenz()` isoliert direkte Vergleiche im aktuellen
Thread/Kontext; die Auswahl wird nicht automatisch in neue Prozesse vererbt.
Fehlende Exporte, ABI-/DLL-Fehler und ungültige Auswahlen führen nicht zu
einem automatischen Rückfall auf Python.

Produktiv integriert:

- Quaternionbasis, Frame-/Poseoperationen und Körperaggregation;
- unabhängige Snapshotausgaben mit exakter Quellprüfung;
- vorbereiteter Ebenenschnitt und vollständiger exakter 6DOF-Auftrieb;
- Wasserschnitt einschließlich Konturen, Ketten und Deckeln;
- Wasserlinienringe und Ringmomente;
- vorbereitete hydrodynamische Rollenkräfte einschließlich Benetzung;
- Wrenchverschiebung, Kraftaggregation, Widerstand und Added-Mass-Kern.

Manifold, NumPy, Qt und VTK werden nicht durch neue Ersatzbibliotheken ersetzt.
Öffentliche Records, Validierungs- und Steueradapter bleiben erhalten.
Snapshotkontexte werden derzeit je Snapshotaufruf aufgebaut; einmalige
Wiederverwendung mit vollständiger Invalidierung ist noch nicht abgeschlossen.
Integrator-/Worker-Innenschleife, Solver, weitere Modellvorbereitung,
Darstellungsaufbereitung und optionale Pfade sind nicht vollständig migriert.

## Prüfungen

| Prüfung | Ergebnis | Beleg |
|---|---|---|
| Produktivsuite einschließlich bisheriger nativer Vertrags-/Frame-/Körperprüfungen | 1068 bestanden, 1 vorhandener Windows-Symlink-Skip | [JUnit](Produktiv_M4_Kraft_Hydrostatik_2026-10-19.xml) |
| Dieselbe Produktivsuite am gehärteten Kandidatenbuild | 1068 bestanden, 1 vorhandener Windows-Symlink-Skip | [Neuer Buildnachweis](Produktiv_M4_Vertrag_2026-10-19.xml) |
| Eingefrorene V0.9-Hydrostatik | Drei Modelle erfolgreich, Referenzdateien nicht neu geschrieben | `werkzeuge\pruefe_genauigkeit_v09.py`, ohne `--schreiben` |
| Geometrieparität | 100 konkrete Wasserschnitte arraygleich, 200 Ebenenschnitte sowie Wasserliniengrenzen geprüft | In Produktivsuite enthalten |
| Rollenkräfte | 200 direkte Vergleiche und Pickle-Neuaufbereitung geprüft | In Produktivsuite enthalten |
| Gesonderter Batchkandidat einschließlich boolescher/überlaufender Schrittzahlen und nichtendlicher/singulärer Lösermatrizen | 14 bestanden, 1 fehlgeschlagen | [Kandidaten-JUnit](Batch_Kandidatenvertrag_2026-10-19.xml) |

Produktivkommando:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests code\cpp\tests\vertrag_native.py code\cpp\tests\paritaet_frames.py code\cpp\tests\paritaet_koerperkontext.py
```

Der Batchkandidat wird gemäß der vorhandenen Trennung der Kandidatenprüfungen
gesondert unter `code\cpp\tests\paritaet_batch.py` ausgeführt. Sein rotes
Ergebnis ist kein Skip und wird nicht als Produktivabnahme ausgegeben.
Der erste vorübergehende Integrationsversuch hatte einen Profilharnessfehler;
sein [JUnit](Produktiv_Batch_Integration_2026-10-19.xml) bleibt als
fehlgeschlagener Versuch erhalten. Die Workerumschaltung wurde zurückgenommen.

## Aktuelle Performance: öffentliche Adapter einschließlich Vollkosten

[Rohdaten](Produktiv_M2_M4_Vergleich_2026-10-19/produktive_vergleiche.json)
und [Umgebung/Quell-/Binär-/JUnit-Hashes](Produktiv_M2_M4_Vergleich_2026-10-19/umgebung.json).
44 Fälle, je sieben Wiederholungen mit wechselnder Reihenfolge.
Faktor = Pythonmedian / produktiver C++-Adaptermedian; kleiner 1 ist langsamer.
Keine instrumentierten Profile als uninstrumentierte Performance ausgegeben.

| Öffentlicher Gesamtadapter | Optimist | Folkeboot | yacht1 |
|---|---:|---:|---:|
| Exakte vorbereitete 6DOF-Auftriebsauswertung | 9,678 | 10,055 | 7,223 |
| Wasserlinienquerschnitt | 5,809 | 4,447 | 5,499 |
| Wasserschnitt mit Deckel | 6,680 | 8,900 | 6,678 |
| Vorbereitete Rollenkräfte | 2,875 | 4,032 | 4,736 |
| Kraftbilanz mit Rollen und Widerstand | 2,405 | 2,372 | 2,251 |
| Hydrodynamikaufbau einschließlich nativer Vorbereitung | 0,767 | 0,791 | 0,849 |
| Snapshot einschließlich Kontextaufbau | 0,194 | 0,198 | 0,174 |

Weitere negative Werte stehen unverändert in den Rohdaten:
Quaternionnormierung 0,656; Quaternionprodukt 0,549; gelenklose Poseableitung
0,508; Punktetransformation bei 100000 Punkten 0,280. Diese Blöcke bleiben
auf ausdrücklichen Nutzerwunsch produktiv. Daraus wird weder ein FPS-Gewinn
noch ein vollständiger End-to-End- oder Live-Speichervorteil abgeleitet.
Die frühere M2/M3-Serie bleibt unveränderte Historie, nicht Abschlussbeleg.

## Offenes M5-Gate: unabhängige Trajektorien

`PhysikKontext` berechnet Kräfte, implizite Dämpfung, Added Mass,
3×3-Lösung und Zustandsfortschritt vollständig in C++. Ganze Batches geben
den GIL frei; keine Pythonkraftcallbacks je Schritt, Teil oder Dreieck.
Ein 100-Schritt-Batch ist einschließlich Fremdkraft und Ruder bitgleich
zu 100 aufeinanderfolgenden nativen Einzelschritten. Eingabefehler und
Abbruch vor dem ersten Schritt werden gesondert geprüft.

Die unabhängige Python-/C++-Trajektorie besteht jedoch beim Optimist nicht
die strenge Prüfung mit `rtol=0`, Zustand `atol=1e-12` und Kraftfeldern
`atol=1e-9`. Die Prüfung umfasst inzwischen auch Einzelmomente,
Bezugspunkte, Namen und Frames, nicht nur die Gesamtkraft.
Die Zustandsgrenze wurde nicht nachträglich vergrößert und die Prüfung
nicht auf identische Eingänge reduziert.

[Reproduzierbare Diagnose mit Roharrays, Matrizen, Schemas und Quellhashes](Batch_Numerik_Quellnachweis_2026-10-19/umgebung.json):

| Modell, je 1000 Schritte | Max. Komponentenabweichung Zustand | Max. Kraftfeldabweichung | Max. Zustandsabweichung bei identischem Eingang |
|---|---:|---:|---:|
| Optimist | 1,03038e-11 | 1,03769e-7 | 3,33067e-16 |
| Folkeboot | 5,55112e-16 | 1,81899e-11 | 2,22045e-16 |
| yacht1 | 3,19189e-16 | 2,72848e-12 | 5,55112e-17 |

Zustandskomponenten haben unterschiedliche SI-Einheiten; die Maxima sind
Diagnosen, keine neue einheitliche physikalische Fehlergrenze.
Kraftfelder enthalten unter anderem Kräfte und Momente, nicht ausschließlich N.
1000 Schritte entsprechen bei unverändertem `dt=0,004 s` vier Sekunden,
nicht dem noch ausstehenden 30-/120-s-Nachweis.

Die isolierte Prüfung von 2000 Optimist-Lösungen auf identischen Matrizen
und rechten Seiten ergab maximal 2,22045e-16 Abweichung zwischen eigenem
3×3-Löser und NumPy; 1030 Lösungen waren bitgleich. Dies belegt einen
Rundungsanteil, aber noch keine vollständige Ursachenbehebung. Weitere
Matrix-/Quaternionreihenfolgen und die Verstärkung im Rudermodell bleiben
zu untersuchen. Die Diagnose speichert alle Originalmatrizen.

Der gemessene Produktiv-/erste Diagnosebuild liegt unter
`build\native-solver-diagnose`; Wheel-SHA256:
`311db3a8fa9ef994432529902b5fb752b9667ff9975db79d8f6c78ea054836d6`.
Der danach gehärtete Kandidat in der separaten Testumgebung liegt unter
`build\native-batch-vertrag`; Wheel-SHA256:
`bb95cff553d0a220744f5e7864ab4516d67bb6051ecfd7b104bbac8564846a6b`.
Die Projektinstallation enthält den ersten Kandidaten, aber der Worker
ruft ihn nicht auf. `PhysikKontext` ist noch kein Pflichtbestandteil des
produktiven Ladervertrags. Der Diagnosebefehl liefert bei Grenzverletzung
Exitcode 1:

```powershell
.\build\native-m2-testenv\Scripts\python.exe werkzeuge\migration_batch.py --output <neuer-diagnoseordner>
.\build\native-m2-testenv\Scripts\python.exe -m pytest -q code\cpp\tests\paritaet_batch.py
```

## Noch nicht abgenommen

- M2–M4: vollständige Einzelfunktionszuordnung, übrige Varianten und Restgates.
- M5: numerische Trajektorienparität vor produktiver Workerumschaltung.
- M6–M9: Solver, restliche Modell-/Darstellungs-/Interaktions-/Optionalpfade.
- M10: vollständige Abschlussmatrix, aktuelle sichtbare 300-s-Liveprüfungen,
  Speicher- und abschließender integrierter Gesamtvergleich.

Es wurde weder ein vollständiger Abschluss noch eine vollständige
Performanceverbesserung behauptet. Kein Commit, Push, Tag oder Release.
