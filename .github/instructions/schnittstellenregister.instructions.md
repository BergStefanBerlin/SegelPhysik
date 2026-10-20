---
description: "Use when changing Python/C++ interfaces, native bindings, backend contracts, or the C++ interface register; keep interface status and evidence current across all SegelPhysik revisions."
applyTo: "**/*.py, **/*.pyi, **/*.cpp, **/*.cc, **/*.cxx, **/*.h, **/*.hpp, **/*.hh, **/*.hxx, **/Schnittstellenregister_CPP.md"
---
# Pflege des Python/C++-Schnittstellenregisters

Diese Regel gilt für alle Entwicklungsstände, Versionen und Revisionsschritte
des Projekts SegelPhysik, nicht nur für V0.10. Das zentrale Register ist
`doc/WegZuV1.0/Revisionsinformation/Schnittstellenregister_CPP.md`;
maßgeblich sind dessen Statusdefinitionen und Pflegehinweise.

## Prüfzeitpunkte

- Zu Beginn eines einschlägigen Arbeitspakets die betroffenen Registereinträge
  und ihren aktuellen Status prüfen.
- Nach Änderungen an Schnittstellen, nativen Bindings, Backendverträgen oder
  deren Aufrufpfaden das Register mit dem tatsächlichen Stand abgleichen.
- Bei Abschluss eines einschlägigen Arbeitspakets sowie bei Meilenstein- oder
  Revisionsprüfungen offene beziehungsweise nicht aktive Einträge erneut
  bewerten.
- Diese Prüfungen sind anlassbezogen; sie begründen keinen unbeaufsichtigten
  Hintergrundprozess und keine Prüfung bei jeder irrelevanten Änderung.

## Status und Aktivierungsversuche

- Implementierung, Anbindung und tatsächliche Nutzung getrennt bewerten. Ein
  vorhandener Export oder eine erfolgreiche Kompilierung allein belegt keine
  aktive Nutzung.
- Status nur mit überprüfbaren Belegen ändern, etwa passenden Tests,
  Aufrufpfaden oder einer dokumentierten Laufzeitprüfung. Performanceaussagen
  benötigen geeignete Messungen.
- Nicht aktive oder offene Schnittstellen bei passenden Prüfzeitpunkten auf
  einen sinnvollen Aktivierungskandidaten und bekannte Hindernisse untersuchen.
  Einen Aktivierungsversuch durchführen, wenn er zum aktuellen Auftrag passt,
  abgrenzbar ist und sich sicher testen lässt.
- Keine außerhalb des Auftrags liegenden Umbauten erzwingen und keine
  Schnittstelle ohne Nachweis als aktiv markieren. Ist ein Versuch nicht
  sinnvoll oder nicht erfolgreich, Grund, fehlenden Nachweis beziehungsweise
  Voraussetzung und einen konkreten nächsten Schritt im Register festhalten.

## Registerpflege

- Jedes einzelne Interface (exportierter Datentyp, Funktion oder qualifizierte
  Kontextmethode) als eigenen Eintrag mit dauerhafter Kennung `CPPI-xxxx`
  führen, beginnend mit `CPPI-0001`. Familien nicht als Sammeleinträge führen.
  Konkrete geplante Interfaces erhalten die Kennung vor der Implementierung;
  bloße Arbeits- oder Abnahmebereiche sind noch keine Interfaces.
- Den CPPI-Zähler projektweit und versionsunabhängig fortführen. Vor einer
  Neuvergabe aktive und archivierte Registereinträge prüfen und eine Nummer
  oberhalb der höchsten jemals vergebenen wählen; mindestens vierstellig
  auffüllen. Nie umnummerieren oder Kennungen wiederverwenden, auch nicht bei
  Stilllegung. Umbenennungen derselben Schnittstelle mit bisherigem Namen
  unter derselben ID dokumentieren; Ersatzschnittstellen erhalten neue IDs
  und einen Verweis. Die maßgebliche Kennungsregel steht in
  `doc/Anweisungen/Nummerierungs-Anweisung.md`.
- Neue, geänderte, ersetzte oder stillgelegte Schnittstellen im selben
  Arbeitsschritt im Register nachführen. Bestehende Einträge nicht allein
  wegen eines Umbaus löschen; Status und Begründung nachvollziehbar
  aktualisieren.
- Einträge so pflegen, dass CPPI-Kennung, einzelne Schnittstelle, Status, Begründung
  und Nachweis beziehungsweise Referenz erkennbar sind. Historische Aussagen
  nur aufnehmen, wenn sie belegt sind; Unbekanntes als ungeklärt kennzeichnen.
- Bei der Prüfung die tatsächliche technische Vertragsquelle und relevante
  Aufrufstellen heranziehen. Inventare nicht ungeprüft aus einer einzelnen
  Liste ableiten oder doppelt pflegen.
- Verwandte Tests und projektübliche Prüfungen ausführen. Fehlende oder nicht
  erreichbare Nachweise ausdrücklich im Register dokumentieren; Ergebnisse
  nicht als bestanden darstellen.
- Pro Interface die Performance-Spalten `Python-Referenz` und die bereits
  bearbeiteten Versionen (aktuell `V0.10`) pflegen. Neue Versionsspalten erst
  bei Bearbeitung der betreffenden Version ergänzen. Vorhandene freigegebene
  Messstände nicht durch neuere Werte überschreiben.
- Vergleichbare Messfälle mit festgelegtem Referenz-/Quellstand,
  Eingabegröße, Hardware/Build, Wiederholungen und Rohdaten verlinken.
  Laufzeitmedian und Faktor Python/C++ ausweisen (über 1 schneller,
  unter 1 langsamer). Adapter-/Gesamtpfadkosten ausdrücklich kennzeichnen.
  Verschachtelte Zeiten weder addieren noch als isolierte Einzelgewinne
  beteiligter Interfaces ausgeben. Ohne Einzelmessung `nicht separat
  gemessen` eintragen; vorhandene Elternblocknachweise nur als solche verlinken.
