---
description: "Use when creating or modifying pytest test files in tests/ or code/cpp/tests/: naming, structure, fixtures, markers, and forbidden patterns for the SegelPhysik test suite."
applyTo: "**/tests/**/*.py, **/code/cpp/tests/**/*.py, **/conftest.py"
---

# Pflege der Teststruktur

Diese Regel gilt für alle Entwicklungsstände, Versionen und Revisionsschritte
des Projekts SegelPhysik. Sie ergänzt die Projektanweisung (`AGENTS.md`) und
die Regel zum Schnittstellenregister; bei Konflikten gelten die strengeren
Kennungs- und Nachweisregeln der jeweiligen Datei.

## Benennung und Gliederung

- Testdateien nach Fachmodul benennen (`test_<modul>.py` oder
  `test_<thema>.py`), nicht nach Meilenstein, Revision oder Block.
  Als Dateinamen unverträglich sind insbesondere Muster wie „schritt4",
  „rev_e", „v09", „v010", „a1" oder Blocknummern.
- Eine Datei = ein Thema/Modul. Greift ein Test über Modulgrenzen, gehört
  er zu einem Integrationsthema in eine eigene Datei mit Marker
  `integration`.
- Historische Blockkennungen (z. B. J1, W2, TC-H7, SpecNNNN, CPPI-xxxx)
  als Kommentar am jeweiligen Test erhalten, nie als Dateiname verwenden.
- Neue Kennungen nach der Nummerierungs-Anweisung vergeben; bestehende
  Kennungen nie umnummerieren oder wiederverwenden.

## Wiederverwendung

- Gemeinsame Fixtures (QApplication, Profildateien, Standard-Meshes)
  gehören in `tests/conftest.py`, nicht in einzelne Testdateien.
- Vordefinierte Formen verwenden (`koerper_formen.build_box` usw.);
  keine lokalen Quader-, Kegel- oder sonstigen Mesh-Fabriken in
  Testdateien nachbauen.
- Vor jedem neuen Test prüfen, ob das Verhalten bereits in einer
  bestehenden Datei abgedeckt ist; bestehende Tests erweitern statt
  parallel neu zu schreiben. Doppelabdeckung desselben Vertrags
  (z. B. Endpunkte plus Steigung derselben Funktion) vermeiden.

## Verbotene Muster

- Keine eigenen `__main__`-Runner oder `sys.exit` in Testdateien;
  pytest ist der einzige Ausführungspfad.
- Keine `sys.path.insert`-Hacks; Importe laufen über das installierte
  Paket bzw. `conftest.py`.
- Keine Tests, die nur das Fehlen entfernter Module behaupten
  (`ModuleNotFoundError` auf Legacy-Importe). Solche Erkenntnisse
  gehören ins Changelog bzw. in das betreffende Register.
- Architekturregeln (Importverbote, Schichtung, Layout) ausschließlich
  per AST-Scan prüfen (Muster: der frühere GUI-Import-Scan), nicht per
  Regex auf Quelldateien. Regex-Scans erfassen Relikte unzuverlässig
  und werden bei Umbenennungen stillschweigend wirkungslos.

## Laufzeit und Marker

- Tests mit Schleifen > ~1000 Iterationen, Modellbau (Union, OBJ-Laden)
  oder GUI-Start erhalten `@pytest.mark.slow` bzw. `@pytest.mark.gui`.
- Marker in der pytest-Konfiguration registrieren; neue Marker immer
  dort eintragen. Die schnelle Suite bleibt als Default lauffähig.
- Schwere Integrationstests gehören nicht in Unit-Testdateien des
  getesteten Moduls, sondern in eigene Dateien mit Marker.

## Physikalische Toleranzen

- Bestehende Paritätstoleranzen nicht lockern: Zustandsvergleiche
  Python/C++ mit `rel=0, abs=1e-12`, Batch-Sequenzen bit-exakt.
- Neue Vergleiche zwischen Rechenpfaden brauchen dieselbe Strenge oder
  eine dokumentierte Begründung im Test-Docstring (Fehlerbudget,
  Quelle der Toleranz).
- Erwartungswerte analytisch herleiten oder aus Tabellen lesen
  (projektüblich, siehe Projekt-Lektion „jede Zahl analytisch
  hergeleitet oder gemessen"), nicht hartkodieren, wo eine Quelle
  existiert.

## Nachweispflicht bei Umbauten

- Wird eine Testdatei umbenannt, aufgeteilt oder zusammengelegt, die
  als Nachweis für einen Registereintrag dient (Schnittstellenregister,
  Genauigkeitsreferenz), ist der Nachweis im selben Arbeitsschritt auf
  den neuen Ort umzuziehen. Ergebnisse nicht als bestanden darstellen,
  wenn der tragende Test entfernt wurde.
