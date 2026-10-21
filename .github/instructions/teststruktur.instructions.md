---
description: "Use when creating, modifying, selecting or running tests, pytest profiles, fixtures or performance benchmarks in SegelPhysik. Strukturierte schlanke Tests, risikobasierte Auswahl, Modellreferenzen, Genauigkeit und reproduzierbare Messnachweise."
applyTo: "tests/**/*.py, code/cpp/tests/**/*.py, **/conftest.py, werkzeuge/benchmark_*.py, pyproject.toml, requirements-dev.txt"
---

# Schlanke und belastbare Testpflege

## Geltung

- Diese Datei ist die aktive projektweite Testpflege-Instruction.
  Der frühere Entwurf unter zuV0.12 bleibt Diskussionsquelle.
- Grundlage des geplanten Umbaus ist die
  [Spezifikation V0.12](../../doc/WegZuV1.0/Revisionslog/zuV0.12/Spezifikatonen/Spezifikation_Testumbau_V0.12.md).
  Umbau des V0.11-Testbestands erst in V0.12; historische V0.11-Dokumente
  nicht ändern. Diese Instruction autorisiert keinen automatischen Umbau.
- Bei neuen und beauftragten geänderten Tests diese Regeln anwenden;
  keinen auftragsfremden Altbestand bereinigen. Spätere freigegebene
  Spezifikationen bestimmen ihren fachlichen Umfang.
- [Nummerierungsregel](nummerierung.instructions.md),
  [Schnittstellenregister-Regel](schnittstellenregister.instructions.md)
  und [Release-Regeln](release.instructions.md) gelten ergänzend.
  Testauswahl ersetzt keine vorgeschriebenen Commit-Prüfungen.

## Auswahl: klein beginnen, bei Risiko erweitern

- Für jede Codeänderung den betroffenen Vertrag, direkte/indirekte
  Verbraucher und relevante Fehler-/Grenzfälle bestimmen. Kleinsten
  fachlich ausreichenden Testlauf ausführen, verwandte Selektoren in
  einem Runner bündeln.
- Gemeinsam genutzte Fixtures, Datenformate, Frames, Einheiten,
  Cache-/Workerzustände und Backendgrenzen mitdenken. Dateinamen oder
  automatische Abhängigkeitserkennung allein beweisen keine Vollständigkeit.
- Bei Änderungen gemeinsamer Verträge passende Integration und
  Python/C++-Parität ergänzen. Bei unklarer Reichweite, Änderungen an
  Sammlung/globalen Fixtures sowie zu Meilenstein/Revisionsabnahme
  auf das Gesamtprofil erweitern.
- Für reine Dokumentation keine Physiksuite starten, sofern keine
  Dokumentationstests oder geänderten fachlichen Nachweise dies verlangen.
- Auswahl kurz begründen und Befehl, Ergebnis, Abwahlen/Skips sowie
  verbleibende Prüflücken nennen. Ein Teilprofil ist kein Gesamtnachweis.
  Fehler im Auftragsumfang untersuchen; nicht durch pauschale Skips,
  Toleranzlockerung oder stillen Backendwechsel verdecken.

## Modelle und Testfälle

- Standardreferenzen: analytisch prüfbarer Quader, ergänzend Kugel,
  Folkeboot als repräsentatives reales Modell für notwendige teure
  Integrations-/Dynamik- und Gesamtpfadmessungen.
- Einfachsten ausreichenden Fall wählen; kein Pflichtkreuzprodukt
  Körper × Yacht × Backend × Pose × Parameter. Keine routinemäßigen
  teuren Simulationen oder Benchmarks an allen Yachten.
- Optimist ist wegen des vom Nutzer beobachteten häufigen Kenterns
  derzeit kein allgemeiner Stabilitäts-/Performance-Abnahmemaßstab.
  Daraus keine automatische Fehlerursache, Skip-/Xfail-Regel oder
  Löschfreigabe für bestehende Modelltests ableiten.
- Bei Modelländerungen das betroffene Modell prüfen. Weitere teure
  Modellfälle nur für einen benannten, sonst ungedeckten Vertrag.
  Günstige Katalog-/Ladeprüfungen mehrerer Modelle nur bei relevantem
  gemeinsamen Lader-/Manifestvertrag, nicht bei jeder Änderung.
- Synthetische Sonderfälle wie offene/fehlerhafte Netze erhalten.
  Folkeboot ersetzt keine analytischen Referenzen und ist nicht allein
  aufgrund seiner Auswahl als vollständig validiert anzusehen.

## Struktur und Wiederverwendung

- Neue Testdateien nach Verhalten/Fachthema benennen, nicht nach
  Versions- oder Meilensteinnummer. Zusammenhängende Integration darf
  mehrere Module prüfen; Altdateien nur bei belegtem Nutzen aufteilen.
- Vor neuen Tests nach bestehender Abdeckung suchen. Gleichförmigen
  Code bei Bedarf parameterisieren; zusätzliche Parameterkombinationen
  kosten weiterhin Laufzeit.
- Gemeinsame Fixtures nur für wirklich wiederverwendete Aufbauten
  in das passende `conftest.py` extrahieren; keine versteckten
  Abhängigkeiten zwischen Tests.
- Den vorhandenen Einstellungsschutz und die eigene native
  Python-Referenz-Fixture erhalten. Geteilte mutable Modelle vermeiden;
  geeignete Scopes nach Isolation, nicht nur Geschwindigkeit wählen.
- QApplication verlässlich halten; Widgets/Worker schließen und
  temporäre Daten gezielt bereinigen. Teure Modelle nicht beim
  Import oder während der Sammlung erzeugen.
- Vorhandene Formfabriken als Eingabegeneratoren bevorzugen.
  Für Tests derselben Fabrik beziehungsweise ihres Rechenpfads unabhängige
  Referenzen verwenden. Analytische und gezielte Spezialnetze sind erlaubt.
- Keine neuen `sys.path.insert`-Workarounds oder eigenen pytest-ersetzenden
  `__main__`-Runner; vorgesehene Paket-/Testkonfiguration verwenden.
- Import-/Schichtregeln per AST prüfen; Ressourcen- und Layoutverträge
  mit geeigneten Pfad-/Laufzeitprüfungen, nicht zwangsläufig per AST.

## Profile, Genauigkeit und Nachweise

- Eingeführte Marker in der pytest-Konfiguration registrieren und
  Auswahlbefehle dokumentieren. `slow` anhand gemessener Laufzeit
  vergeben, nicht allein wegen Schleifenzahl, GUI-Import oder Modellbau.
- Die geprüften Aufrufe und bekannten Umgebungs-/Ausgangsbefunde stehen
  in [tests/README.md](../../tests/README.md). Der Standardlauf sammelt auch
  `paritaet_*.py` und `vertrag_native.py`; diese Namen nicht durch eine
  spätere `python_files`- oder `testpaths`-Änderung verlieren.
- `hardware` kennzeichnet echte optionale Geräteprüfungen;
  `diagnostic` einen erhaltenen speziellen Bestands-/Fehlervertrag.
  Beide Marker bedeuten weder Skip noch Xfail. Explizit abgewählte
  Hardwareprüfungen und bestehende Fehler verhindern eine uneingeschränkte
  Gesamtfreigabe.
- Keine versteckten standardmäßigen Abwahlen. Gesamtprofil und
  gezielte Profile müssen explizit ausführbar sein. Native Prüfdateien
  unter `code/cpp/tests` außerhalb des `test_*.py`-Musters nicht vergessen.
  Fehlende native/GUI-Voraussetzungen als Prüflücke melden.
- Bestehende Toleranzen und bit-exakte Verträge erhalten. Insbesondere
  `rel=0, abs=1e-12` dort beibehalten, wo der Python/C++-Vertrag dies
  fordert; nicht pauschal auf alle Approximationen übertragen.
  Neue Toleranzen mit Einheit, Referenz und Fehlerbudget begründen.
- Erwartungswerte unabhängig analytisch herleiten oder aus belegten
  Referenzen beziehen; nicht durch denselben Produktionspfad berechnen.
- Ähnliche Tests nur nach Vergleich ihrer Assertions, Grenzfälle und
  Nachweisfunktion zusammenführen/entfernen. Adapter- und native
  Kernverträge sind verschiedene Ebenen. Negative Legacy-Verträge
  zuerst fachlich bewerten, nicht pauschal streichen.
- Bei Verschiebung Kennungen erhalten, alte/neue Testorte zuordnen und
  aktuelle Register-/Nachweisverweise im selben Schritt nachführen.
  Historische Nachweise nicht umschreiben; fehlenden Ersatz offen melden.

## Performance und Testkosten

- Korrektheit und Laufzeit getrennt nachweisen. Gewöhnliche
  Regressionstests nicht mit instabilen Wandzeitgrenzen versehen.
  Vorhandene Messwerkzeuge und Laufzeitberichte zuerst nutzen.
- Referenz/Kandidat unter gleichen Eingaben und Bedingungen messen:
  Revision, Modell-/Eingabestand, Rechenpfad, Hardware/Build,
  Thread-/Prozesszahl, Schrittzahl, Warm-up und Messgrenze festhalten.
  Cache-/Kaltstartunterschiede gesondert ausweisen.
- Sofern keine begründete freigegebene Messregel etwas anderes vorgibt:
  mindestens ein separater Warm-up, danach fünf Messungen pro Variante;
  Suitekosten mit mindestens drei vollständigen Läufen pro Stand.
  Keine konkurrierende Benchmark-/Testlast während Vergleichsmessungen.
- Median, Streuung, Rohdaten und Vorher/Nachher-Faktor berichten.
  Faktor = Referenzmedian / Kandidatenmedian. Einen Gewinn nur behaupten,
  wenn er über der beobachteten Streuung liegt; die V0.12-Abnahme verwendet
  die konkrete Regel der Spezifikation. Sonst: nicht nachgewiesen.
- Sammel-, Setup- und Prozessstartkosten berücksichtigen.
  Auswahlverkleinerung nicht als Beschleunigung derselben Arbeit ausgeben.
  Verschachtelte Zeiten nicht addieren oder als einzelne Interfacegewinne
  verkaufen; Interfacebelege gemäß Schnittstellenregister pflegen.
- Zusätzliche Tools, Parallelisierung, Caches oder Timeout-Abhängigkeiten
  nur bei belegtem Bedarf einführen. Isolation und Messbarkeit erhalten.
