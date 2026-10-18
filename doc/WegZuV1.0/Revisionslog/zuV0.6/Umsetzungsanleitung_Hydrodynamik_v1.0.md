# Umsetzungsanleitung Hydrodynamik v1.0

**Stand:** 17.10.2026<br>
**Zugehörige Spezifikation:** [Spezifikation Hydrodynamik v1.0](./Spezifikation_Hydrodynamik_v1.0.md)<br>
**Status:** Umsetzungsplan; keine Anweisung, alle Stufen ohne Gates oder
fachliche Modellfreigabe in einem Zug zu aktivieren<br>
**Geltungsbereich:** Verdrängungsfahrt, Rumpfwiderstand, Kiel/Schwert,
Ruder, geometrische Metadaten und optionale vorab berechnete Kennlinien.

## 0. Zweck und verbindliche Grenzen

Diese Anleitung zerlegt die finale Spezifikation in ausführbare Arbeitspakete,
Abhängigkeiten, Tests und Freigabekriterien. Die `HYD-NNNN`-Kennungen dieses
Dokuments sind dauerhaft. Bei Aktualisierungen bleiben sie erhalten; neue
Arbeitspunkte bekommen unbenutzte Kennungen. Die `SpecNNNN`-Kennungen
verweisen auf Anforderungen in der Spezifikation und werden nicht durch
`HYD-NNNN` ersetzt.

Die Anleitung genehmigt noch keine konkrete Rudermeshänderung und keine
Produktivaktivierung. Implementierung erfolgt gestuft. Neue Modellbeiträge
bleiben in den frühen Stufen deaktiviert. Eine Näherung darf genutzt werden,
wenn sie klar gekennzeichnet ist und die fachliche Freigabestufe die Nutzung
ausdrücklich erlaubt; sie darf nie als extern validierte Referenz ausgegeben
werden.

Nicht erlaubt sind:

- neue Gleitfahrt-/Rumpfauftriebsmodelle, FEM, CFD/SPH, Slamming oder
  Wellenschlag im Umfang dieser Anleitung;
- stille Änderungen an vorhandenen Yachtmeshes oder Umnummerierungen von
  Spezifikationspunkten;
- ungeprüfte Konstanten aus älteren Anleitungen als bestätigte
  Modellparameter;
- die Verwendung des Ordners `doc/Backlog/Ideen/` als Quelle;
- physikalische Richtigkeit aus bloßer Reproduzierbarkeit eines Rechners
  abzuleiten.

## 1. Abhängigkeiten und Freigabestufen

| Phase | Arbeitspunkte | Ergebnis/Gate | Umsetzungsstand |
|---|---|---|---|
| A – Bestandsaufnahme | HYD-0001 bis HYD-0003 | Code-/Laufzeitpfad und Geometrie sind dokumentiert; keine produktive Physik geändert. | Erledigt; Inventarbericht liegt vor. |
| B – Fachliche Modellauswahl | HYD-0004 bis HYD-0005 | Modellkandidaten, Quellen, Unsicherheiten und Referenzmanöver liegen vor. Ohne begründeten Modellzweig wird dessen Implementierung blockiert. | Blockiert: passende Referenzdaten und autoritative Ruderkinematik fehlen. |
| C – Datenvertrag und isolierte Implementierung | HYD-0006 bis HYD-0010 | Metadaten-/Kennlinienvertrag und optionale isolierte Modellpfade bestehen ihre gezielten Tests; produktive Modelle bleiben unverändert. | HYD-0006 erledigt; isolierter Kleinwinkel-Rudernäherungszweig als Teil von HYD-0010 implementiert und getestet. Kennlinienartefakt und übrige Modellzweige bleiben offen. |
| D – Integration und Yachtvergleich | HYD-0011 bis HYD-0014 | Bestehende Wrench-/Frame-Verträge, Summen und optionale Komponenten sowie Original-/Rudervariante sind regressionsgeprüft. | Noch nicht begonnen; vorgelagerte Gates offen. |
| E – Leistung und Freigabe | HYD-0015 und HYD-0016 | Live-Performance, Dokumentation und explizite Fachfreigabe bestanden. Erst dann darf die Produktivkonfiguration neue Beiträge aktivieren. | Sichtbarer Zehnminuten-Baseline-Lauf fehlgeschlagen: `12,97 FPS`, Frameabstand-P95 `205,186 ms`, Überlastpause und `0,00525 s/s` Simulationsdurchsatz. Freigabe nicht erteilt. |

Eine Phase beginnt erst, wenn ihre Voraussetzungen erfüllt sind. Ein
fehlgeschlagenes Gate blockiert nachfolgende Freigaben; ein Näherungsstatus
oder eine Modellunsicherheit darf nicht durch ein bestandenes
Software-Regressionstestergebnis in einen Validierungsstatus umgedeutet
werden.

## 2. Arbeitspunkte

### HYD-0001 – Arbeitsbaum, Baseline und Schutz bestehender Modelle

**Spec-Bezug:** Spec0109, Spec0001–Spec0005, Spec0008, Spec0002, Spec0036,
Spec0046–Spec0047.

1. Branch und `git status --short --untracked-files=all` prüfen.
2. Bereits vorhandene uncommittete Änderungen sowie alle Modellpakete
   identifizieren. Keine Nutzeränderung verwerfen oder überschreiben.
3. Relevante Regressionen vor jeder Codeänderung ausführen:

   ```powershell
   $env:QT_QPA_PLATFORM = "offscreen"
   .\.venv\Scripts\python.exe -m pytest -q tests\test_kraftmodell.py tests\test_modell_lader.py tests\test_migriere_modellpaket.py tests\test_manifest_baum.py tests\test_auftrieb.py tests\test_dynamik_6dof.py tests\test_gui_laufzeit_edit.py
   ```

4. Bestehende Fixtures, Yacht-Golden-Daten, Konfigurationsdateien und
   Performance-Messungen mit Pfad, Revision und Prüfsumme festhalten.
5. Bereits bekannte Live-Gatefehler in der Baseline ausdrücklich notieren;
   ein neuer Beitrag darf nicht als Ursache oder Heilung dieser Fehler
   unterstellt werden.

**Tests:** vorgenannte Regressionen; `git diff --check`.

**Abnahme:** Baseline reproduzierbar dokumentiert; Originalmodelle und
Nutzeränderungen unverändert; fehlgeschlagene Baseline-Tests sind geklärt
oder blockieren die nächste Phase.

### HYD-0002 – Laufzeit- und Datenfluss der aktuellen Yacht

**Spec-Bezug:** Spec0006–Spec0013, Spec0028–Spec0029, Spec0035–Spec0037.

1. Vom Paketmanifest über `lade_modellpaket`, Fabriken, aktive
   Körper-/Snapshot-Objekte bis zum `Kraftmodell` den tatsächlichen Datenfluss
   verfolgen.
2. Für jeden hydrodynamisch relevanten Teil feststellen:
   Paket-ID, Rolle, Meshdatei, Meshframe, relative Pose, Gelenkdefinition,
   Masse/Trägheit, Verdrängungsstatus und derzeitige Sichtbarkeit.
3. Achsenabbildung, Wasserlinie, Schwerpunktframe, Posekomposition,
   Fluidtranslation und Fluidwinkelgeschwindigkeit anhand Code und Tests
   belegen.
4. Vorhandene Widerstände, Dämpfung, Hydrostatik, Added Mass und Fremdkraft
   tabellarisch den physikalischen Effekten zuordnen. Je Effekt angeben, ob
   ein bestehender Beitrag erhalten, ersetzt oder ausdrücklich nicht
   ergänzt wird.
5. Festhalten, dass `lade_modellpaket` derzeit ein Paket validiert/lädt,
   aber keinen persistenten Hydrodynamik-Metadatensatz erzeugt. Keine
   schreibende Nebenwirkung in einen reinen Ladepfad einbauen.

**Tests:** bestehende Loader-, Fabrik-/Baum-, Kraftmodell- und
Frame-/Dynamiktests; zusätzlich ein schriftlicher Datenfluss-Review.

**Abnahme:** jede Pose-/Frame-/Krafttransformation hat eine nachprüfbare
Code-/Testreferenz; doppelte Kraftbeiträge und noch nicht vorhandene
Rudersteuerpfade sind als solche ausgewiesen.

### HYD-0003 – Geometrieinventar und Klassifikation von Rumpf, Kiel und Ruder

**Spec-Bezug:** Spec0015–Spec0022, Spec0030–Spec0032, Spec0049–Spec0053,
Spec0061.

1. Die unveränderten produktiven Yachtmeshes über den kanonischen
   Manifest-/Meshloader laden. Roh-OBJ-Parsing nur als unabhängigen
   Prüfschritt verwenden.
2. Für Rumpf, Kiel, Schwert (falls eigenständiger Knoten), Bulb und Ruder
   mindestens Bounding-Box, Dreiecksoberfläche, Volumen, Schwerpunkt,
   Hauptachsen/Orientierung, Dreieckszahl, Topologiestatus und
   Querschnittsschnitte dokumentieren.
3. Für Kiel/Schwert/Ruder prüfen, ob die Querschnittsform und Auflösung
   tatsächlich ein Profil erkennen lassen. Wenn Profilkonturen, Vorder-/
   Hinterkante, Spannweite oder Bezugssehne nicht stabil ableitbar sind,
   als unprofiliert/unklar markieren; keine automatische Profilerkennung
   allein anhand des Namens vornehmen.
4. Rudermesh insbesondere gegen den sichtbaren Maßstab im Yachtmodell, die
   Lage zur Wasserlinie, Ruderachse und Rumpfkontur prüfen. Die bestehende
   Beobachtung, dass es visuell zu klein wirkt, als zu prüfende
   Nutzervorgabe erfassen, nicht als bereits quantifizierte
   Meshkorrektur.
5. Keine Geometrie, Pose oder Massendaten ändern.

**Tests:** deterministische Messwiederholung; Einheiten-/Achsenkontrolle;
Meshvalidator für jedes Teil; Bericht mit Rohgeometriehashes.

**Abnahme:** Klassifikation jedes relevanten Teils mit Beleg und
Konfidenz; alle nicht belastbar bestimmbaren Kennwerte explizit `fehlend`
oder `unklar`; Produktivmeshes bitidentisch unverändert.

### HYD-0004 – Quellen-, Modell- und Validierungsentscheidung

**Spec-Bezug:** Spec0015–Spec0018, Spec0023–Spec0026, Spec0044,
Spec0048, Spec0062–Spec0063.

1. Fachquellen für Rumpfreibung/-widerstand, 2D-Profilkennlinien,
   endliche Spannweite, Platten-/Crossflow-Näherungen und
   Kiel-Ruder-Interaktion recherchieren. Erste Anlaufstellen:
   - [ITTC Resistance Test](https://ittc.info/media/11780/75-02-02-01.pdf)
   - [TU Delft: Keel-rudder interaction on a sailing yacht](https://research.tudelft.nl/en/publications/keel-rudder-interaction-on-a-sailing-yacht/)
   - [TU Delft Repository: Keel-Rudder Interaction](https://repository.tudelft.nl/record/uuid:1be75bf7-04b2-4089-95af-95ac4031e034)
   - [MIT XFOIL 6.9 User Primer](https://web.mit.edu/drela/Public/web/xfoil/xfoil_doc.txt)
2. Für jede Quelle Inhalt und Herkunft prüfen und konkrete Seite, Tabelle,
   Datensatz, Lizenz-/Zugangsbedingungen, Geometrie, Fluidbedingungen,
   Reynoldsbereich, Anstellwinkelbereich sowie Unsicherheit aufnehmen.
   Suchzusammenfassungen sind kein Referenzdatensatz.
3. Modelloptionen getrennt bewerten:
   - Rumpf: Reibungsanteil und residueller/Formwiderstand nicht als
     austauschbar behandeln; eine ITTC-Reibungslinie allein ist kein
     vollständiger Gesamtwiderstand.
   - Profilierte Anbauten: vorhandene, passende 3D-Referenzkennlinien
     bevorzugen; 2D-Profilrechnung nur für hinreichend bekannte Sektionen
     und nur mit gekennzeichneter Korrektur-/Gültigkeitsgrenze verwenden.
   - Unprofilierte Anbauten: eigener Näherungszweig oder begründete
     Ablehnung des Lift-Zweigs.
   - Interaktion zwischen Kiel, Rumpf und Ruder gesondert erfassen;
     isolierte Profilpolaren belegen keine Interaktion.
4. Begründete Modellmatrix mit Entscheidungsstatus `validiert`,
   `Näherung` oder `nicht unterstützt` erstellen. Dieser Status beschreibt
   den Modellzweig, nicht den Speicherstatus nach Spec0062: dort sind
   `geometrisch abgeleitet`, `berechnete Näherung` und `gegen externe
   Referenz validiert` als getrennte Datensatz-Vertrauensstufen abzubilden.
   Keine Koeffizienten freigeben, die nicht bis auf Quelle und
   Betriebsbereich rückverfolgbar sind.
5. Wo für die aktuelle Yacht keine direkt passenden Daten existieren,
   entscheiden, ob eine unabhängig validierte, vergleichbare
   Geometrieklasse ausreicht. Andernfalls lediglich einen
   Näherungs-Prototyp erlauben oder den Modellzweig blockieren; Nutzer über
   wesentliche Auswirkungen auf die angestrebte Modelltreue informieren.

**Tests/Review:** Quellen- und Gültigkeitsreview durch einen zweiten
Fachreviewer oder explizite Nutzerfreigabe; Quellenlinks auf Erreichbarkeit
prüfen; Zahlen-/Einheitenreview.

**Abnahme:** jeder Modellzweig hat Modellgleichungen/Datensatzquelle,
Eingangsparameter, Gültigkeitsbereich und Vertrauensstatus. Keine
Implementierung beginnt, solange diese Angaben fehlen.

### HYD-0005 – Ruder-Manöver und Referenzbedingungen

**Spec-Bezug:** Spec0019–Spec0022, Spec0041, Spec0051–Spec0052,
Spec0064–Spec0066.

1. Referenzkurs auf 0° und anfänglichen Kurs-über-Grund-Fehler auf 10°
   setzen. Kurs als Richtung des Geschwindigkeitsvektors im globalen
   horizontalen Inertialframe messen; Bootskörper-Heading getrennt
   protokollieren. Initialzustand: Bootskörper-Heading 10°, Giergeschwindigkeit
   und Seitwärtsgeschwindigkeit null. Fehlerwinkel korrekt wrappen und gegen
   die Zielrichtung definieren.
2. Einen oder mehrere Vorwärtsgeschwindigkeitsfälle relativ zum ruhenden
   Wasser aus dem dokumentierten, vorgesehenen Verdrängungsfahrtbereich
   auswählen. Gibt es dafür keine belegte Modell-/Nutzungsangabe, ist ein
   dokumentierter Geschwindigkeits-Sensitivitätsbereich festzulegen; keine
   Einzelgeschwindigkeit als allgemein repräsentativ ausgeben.
3. Für den isolierten Testaufbau die Vorwärtskomponente der Geschwindigkeit
   im Bootskörperframe vorgeben; Seitwärts- und Gierbewegung dynamisch lassen.
   Die Umgebung ist ruhend, sodass Kurs über Grund und Kurs durchs Wasser
   übereinstimmen. Kein Wind, keine Wellen, keine Strömung und kein
   Produktiv-Antriebs-/Segelmodell zuschalten.
4. Einen dokumentierten Test-Proportionalregler verwenden:
   Ruderbefehl proportional zum gewrappten Kursfehler, begrenzt auf die
   verifizierten Gelenkgrenzen. Vorzeichen, Reglerverstärkung und eventuelle
   Rate sind vor dem Vergleich festzulegen und für Originalruder und
   Variante identisch zu halten. Numerische Integrator- und Winkeltoleranzen
   sind ebenfalls vorab festzuschreiben. Ohne im aktuellen Gelenkvertrag
   definierte Rate wird die Pose direkt gesetzt.
5. Kurs-über-Grund-Fehler, Bootskörper-Heading, Ruderwinkel, Kräfte,
   Momente, Geschwindigkeit und Überschwingung als Zeitreihe protokollieren.
6. Erfolg liegt je Geschwindigkeitsfall vor, wenn der absolute Kursfehler
   spätestens nach 10 s auf höchstens 50 % des Anfangsfehlers sinkt und ab
   dem ersten Erreichen dieser Grenze bis zum Ende des 10-s-Fensters
   höchstens 50 % des Anfangsfehlers bleibt. Eine Variante darf
   nur empfohlen werden, wenn sie alle Fälle besteht, in denen das Original
   scheitert, und keinen vom Original bestandenen Fall verschlechtert. Das
   ist ein projektspezifischer Variantenvergleich, kein Sicherheitsnachweis.
   Als Überschwingen zählt ein Vorzeichenwechsel des Kursfehlers mit einem
   Gegenseitenbetrag oberhalb der vorab festgelegten Winkeltoleranz; ein
   solcher Lauf gilt nicht als bestanden. Instabiles Verhalten oder ein
   Winkelgrenzenverstoß gelten ebenfalls nicht als Erfolg.

**Tests:** deterministischer Manöver-Runner mit fixierten Eingaben;
Wiederholung mit identischen Ergebniszeitreihen innerhalb der vorab
festgelegten numerischen Toleranz; positiver/negativer Kursfehler;
Rudergrenzentest; mehrere Geschwindigkeitsfälle, sofern ein Betriebsbereich
statt einer Einzelfallbedingung geprüft wird.

**Abnahme:** Manöver ist vollständig reproduzierbar beschrieben. Ein
fehlender Geschwindigkeits-/Betriebsbereich bleibt ausdrücklich als
Freigabelücke sichtbar. Original und Variante verwenden dieselbe
Reglerverstärkung und dieselben Randbedingungen; Ergebnisse sind je
Geschwindigkeitsfall ausgewiesen. Keine Rudervergrößerung darf allein über
Einzelfall-Tuning dieses Tests entschieden werden.

**Produktions-/Manöverblocker nach Spec0065:** Das aktuelle `yacht1`-Manifest
enthält für `ruder` weder `pose` noch `gelenk`; autoritative Drehachse,
Drehpunkt, Vorzeichen und mechanische Grenzen fehlen. Nach ausdrücklicher
Nutzerfreigabe wird die Vorderkantenachse aus Spec0066 ausschließlich im
getrennten Kleinwinkel-Kraftmodell verwendet. Sie erfüllt Spec0065 nicht.
Es wurde kein Produktionsgelenk, kein mechanischer Winkelanschlag und keine
vollständige Manöver-/Rudergrößenabnahme ergänzt.

### HYD-0006 – Vertrag für geometrische Importmetadaten

**Spec-Bezug:** Spec0007–Spec0008, Spec0030–Spec0032, Spec0035–Spec0036,
Spec0040, Spec0043, Spec0061.

1. Ein versioniertes, paketgebundenes Artefakt für automatisch abgeleitete
   Metadaten definieren, z. B. `hydrodynamik/geometrie_metadaten.json`.
   Es ist kein unbekanntes Feld in das streng validierte bestehende Manifest
   einzuschleusen.
2. Mindestens aufnehmen: Paket-/Knoten-IDs, Schema-Version,
   Quellmanifest-Hash, Rohgeometrie-Hash je Teil, kanonischer SI-Mesh-Hash,
   Einheiten und Achsenmapping, Berechnungsalgorithmus/-version,
   Bounding-Box, Oberfläche, Volumen/Topologie, Schwerpunkt,
   Bezugsrichtungen, Profil-/Schnittdaten soweit robust ableitbar sowie
   Quelle und Status jedes Werts.
3. Fehlende/mehrdeutige Größen ausdrücklich als fehlend/unklar
   serialisieren; nicht aus Namen oder Rollen ableiten.
4. Metadaten während einer expliziten Modellimport-/Paketvorbereitungs-
   operation erzeugen. Den normalen read-only Loader nicht durch
   ungefragte Dateiänderungen, Netzaufrufe oder Seiteneffekte erweitern.
5. Ausgabe atomar schreiben, vorhandene Pakete nicht überschreiben,
   Paketpfade sicher begrenzen und Erzeugung erneut starten können.
6. Falls sich Quellhash, Mesh, Manifest oder Algorithmusversion ändert,
   alte Daten als ungültig erkennen und kontrolliert neu berechnen.

**Tests:** gültige Pakete, offene Schalen, degenerierte Dreiecke,
fehlende Meshes, unsichere Sidecarpfade, Hashabweichung,
Algorithmusversionswechsel, deterministischer Zweitlauf,
Schreibfehler/Abbruch ohne Teildatei und Nichtüberschreiben.

**Abnahme:** identische Eingaben erzeugen byte-stabile kanonische
Metadaten; Änderungen an Eingang/Verfahren werden erkannt; aktueller Loader
und bestehende Manifeste bleiben rückwärtskompatibel.

**Umgesetzt:** `segelphysik/core/hydrodynamik_metadaten.py` berechnet
hashgebundene SI-Geometrie-, Topologie-, Schwerpunkt- und
Oberflächen-Hauptachsmetadaten. Nicht unterstützte Profil-/Querschnitts-
klassifikation bleibt ausdrücklich `unklar`. Das explizite Werkzeug
`werkzeuge/erzeuge_hydrodynamik_metadaten.py` erzeugt ein Sidecar atomar und
ohne Überschreiben bzw. prüft seine Aktualität; der normale Paketloader
bleibt schreibfrei. Gezielte Tests liegen in
`tests/test_hydrodynamik_metadaten.py`.

### HYD-0007 – Vertrag und Erzeugung optionaler Kennlinien

**Spec-Bezug:** Spec0015–Spec0018, Spec0023–Spec0026, Spec0035–Spec0036,
Spec0044, Spec0062–Spec0063.

1. Optionales Kennlinienartefakt getrennt von Geometriemetadaten definieren.
   Jeder Datensatz bindet sich an Meshhash und Geometrie-Metadatenversion.
2. Speichern: Teil-ID, Modellklasse, Methode, Programm/Version,
   Parameter, Fluideigenschaften, Geschwindigkeiten/Reynoldsbereiche,
   Anstell-/Ruderwinkel, Kraft-/Momentenkomponenten und Frames,
   Gültigkeitsbereich, numerische Konvergenz, Unsicherheitsangabe,
   Quellen und Vertrauensstatus.
3. Status mindestens als `geometrisch_abgeleitet`,
   `berechnete_naeherung` oder
   `gegen_externe_referenz_validiert` ablegen. Diese Statuswerte sind keine
   automatische Fortschrittskette; eine Kennlinie darf nur dann den
   Validierungsstatus erhalten, wenn ein unabhängiger, dokumentierter
   Vergleich ihren Gültigkeitsbereich tatsächlich abdeckt.
4. Kennlinien außerhalb des Echtzeitpfads erzeugen und validieren. Kein
   Rechner/Prozess wird als harte Laufzeitabhängigkeit eingeführt, solange
   Ausführbarkeit, Lizenz, Reproduzierbarkeit und Support nicht geprüft sind.
5. Validierung an einer Referenz muss sowohl Geometrieklasse als auch
   Bedingungen abdecken. Ergebnisse für eine andere Geometrie oder außerhalb
   des Bereichs behalten den Näherungsstatus.

**Tests:** Schemafehler und fehlende Herkunft; Meshhash-Konflikt;
Gültigkeitsbereichsprüfung; deterministische Ein-/Ausgabe;
Näherung wird nie als validiert geladen; externe Referenz nur nach
expliziter Validierungsmetadatenprüfung.

**Abnahme:** Import und spätere Nutzung wählen nur kompatible, gültige
Datensätze; Modell-/Solverprovenienz bleibt dauerhaft nachvollziehbar.

### HYD-0008 – Isolierter Rumpfwiderstand

**Spec-Bezug:** Spec0014, Spec0023–Spec0024, Spec0028–Spec0029,
Spec0038–Spec0039, Spec0044.

1. Erst nach HYD-0004 gewählte Reibungs- und Form-/Querwiderstandsanteile
   getrennt implementieren. Den Scope der Formel pro Geschwindigkeits- und
   Geometriebereich sichtbar machen.
2. Keine pauschale ITTC-Reibungslinie als Gesamtwiderstand behandeln.
   Vorhandene lineare/quadratische Widerstandsparameter für denselben
   Effekt deaktivieren oder eindeutig auf andere Freiheitsgrade begrenzen,
   damit keine Doppelkraft entsteht.
3. Hydrostatische Beiträge unverändert lassen; Rumpf-Lift, Gleiten und
   Froude-Blend nicht ergänzen.
4. Modell zunächst nur als isolierte Funktion mit vollständig
   dokumentiertem Parametersatz liefern; Produktivkonfiguration bleibt aus.

**Tests:** Nullgeschwindigkeit; Richtung und nichtpositive Widerstandsarbeit;
Vorzeichen über alle relevanten Bewegungsrichtungen; definierte
Referenzgeometrien; Grenz-/Ungültigkeitseingaben; Vergleich mit
unabhängig belegten Referenzen oder deutliche Kennzeichnung als Näherung.

**Abnahme:** alle Tests bestehen; Gültigkeits-/Unsicherheitsstatus ist
maschinell und in Berichten sichtbar; keine neue Kraft bei deaktiviertem
Feature.

### HYD-0009 – Profilierte Kiel-/Schwert-/Rudermodelle

**Spec-Bezug:** Spec0015, Spec0017–Spec0018, Spec0025, Spec0027,
Spec0038–Spec0041, Spec0044.

1. Zunächst nur als profiliert klassifizierte Teile unterstützen, deren
   Profilabschnitte und Bezugsgeometrie den freigegebenen Rechenweg erfüllen.
2. Abgeleitete 2D-Profilkurven dürfen nur als Näherung für den
   passenden Reynolds-/Winkelbereich verwendet werden. Endliche Spannweite,
   3D-Wake, Rumpfinteraktion, Ablösung/Stall sind separat zu berücksichtigen
   oder als nicht unterstützt zu kennzeichnen.
3. Pro Teil lokale Anströmung, Winkelkonvention, Kraftframe und Angriffspunkt
   aus HYD-0002 umsetzen. Auftriebs- und Widerstandsrichtung im Teilframe
   definieren und per Test absichern.
4. Separate Vorberechnungsfunktion für ausgewählte Winkel-/Bedingungsraster
   implementieren, falls HYD-0007 die Methode freigibt; Werte im sidecar
   speichern, nicht im Hot Path berechnen.
5. Bei fehlenden Profilangaben mit klarer Modellfehler-/Unsupported-Antwort
   abbrechen oder auf den explizit ausgewählten Näherungszweig verweisen;
   kein automatisches Fallback mit plausibel wirkenden Werten.

**Tests:** Nullwinkel, symmetrisches Profil, positives/negatives Alpha,
Nullfluss, Frame-/Ruderrotation, begrenzte Gültigkeitsbereiche,
Out-of-range-Ablehnung, Hashbindung, unabhängiger Referenzfall.

**Abnahme:** Profilzweig wird nur bei ausreichenden Eingangsdaten
ausgeführt; Kennlinienstatus und Unsicherheit bleiben sichtbar; alle
quantitativen Referenztests haben vorab dokumentierte Toleranzen.

### HYD-0010 – Unprofilierter Platten-/Crossflow-Zweig

**Spec-Bezug:** Spec0016–Spec0017, Spec0026–Spec0027, Spec0038–Spec0040,
Spec0044.

1. Für flache oder unzureichend beschriebene Geometrien einen ausdrücklich
   getrennten Näherungszweig spezifizieren; keine Profilparameter
   übernehmen.
2. Modellannahmen, Bezugsflächen, Einfallsrichtung, Sättigungs-/Grenzfälle
   und Unsicherheit vor Implementierung dokumentieren.
3. Koeffizienten nur nach HYD-0004 eintragen. Für einen ausdrücklich
   freigegebenen Lehrmodellzweig darf eine hergeleitete Näherung verwendet
   werden, wenn Gleichung, Quelle, Parameter, Gültigkeitsbereich und
   Unsicherheitsstatus dokumentiert sind. Keine Konstanten aus dem alten
   Guide ungeprüft übernehmen.
4. Ergebnisse als Näherung markieren und visuell/diagnostisch von
   Profilkennlinien unterscheiden.

**Tests:** planares synthetisches Mesh, Spiegelung, Richtungswechsel,
Nullfluss, Winkelbereiche, ungültige Fläche und Leistungsbilanz.

**Abnahme:** kein unprofilierter Körper wird als Profil behandelt; ohne
begründete Parameterfreigabe bleibt der Zweig deaktiviert.

**Teilweise umgesetzt:** `segelphysik/core/hydrodynamik_ruder_naeherung.py`
enthält ein getrenntes, nicht produktiv eingebundenes Rudernormalkraftmodell
für das vorhandene Yachtmesh. Die Testachse ist die ausdrücklich freigegebene
Vorderkantenannahme nach Spec0066; das Meshklassifikationsfeld bleibt
`unklar`. Die MMG-artige Endspannweitenformel verwendet geometrisch
abgeleitete Projektionsfläche und Streckung. Berücksichtigt werden lokale
Seitwärts-/Giergeschwindigkeit sowie ein idealisierter induzierter
Widerstand; Profilwiderstand, Stall, Rumpf-/Kielnachlauf und mechanische
Anschläge sind nicht modelliert. Der effektive Anstellwinkel ist auf ±10°
begrenzt; außerhalb wird mit `HydrodynamikModellFehler` abgelehnt. Ergebnisse
tragen `berechnete_naeherung`. Der separate Prüfvorschlag dokumentiert
Gleichung, Eingaben, Quellen und Grenzen; das Modell ist kein Ersatz für
HYD-0004-Referenzvalidierung.

### HYD-0011 – Einbindung in Kraftbeiträge und Wrenches

**Spec-Bezug:** Spec0007–Spec0013, Spec0027–Spec0029, Spec0035–Spec0037,
Spec0039, Spec0042.

1. Einzelne Rumpf-, Kiel-, Schwert- und Ruderbeiträge mit bestehenden
   `Kraftbeitrag`-/`Wrench`-Objekten oder einem kompatiblen strukturierten
   Äquivalent erzeugen.
2. Je Beitrag Teil-ID, Kraft, freies Moment, Angriffspunkt, Frame,
   Zeitpunkt und Vertrauensstatus nachvollziehbar halten.
3. Wrenchs auf denselben Schwerpunkt-Bezugspunkt transformieren und
   aggregieren. Kein eigenständiger zweiter Aggregator.
4. Vorhandene Hydrostatik/Schwerkraft/Added Mass unverändert in die
   bestehende Aggregation einordnen; Doppelkraftprüfung aus HYD-0002
   maschinell/testseitig abdecken.
5. Feature flag/optionale Konfiguration so anlegen, dass default-off und
   alte Konfigurationen identisches bisheriges Verhalten liefern.

**Tests:** Wrench-Transport-Identität, Hebelarmmoment, Rotation,
Superposition, Framefehler, deaktivierter Zustand, doppelte
Kraftkomponenten, Prozess-/Snapshot-Parität.

**Abnahme:** integrierte Beiträge stimmen bis zur festgelegten numerischen
Toleranz mit unabhängiger Einzel-/Summenrechnung überein; alte
Golden-Ergebnisse bleiben bei deaktiviertem Feature gleich.

### HYD-0012 – Summenanzeige und optionale Komponentenanzeige

**Spec-Bezug:** Spec0034, Spec0039, Spec0055.

1. Summenkraft, Summenmoment und zugehörigen Angriffspunkt grundsätzlich
   anzeigen.
2. Einzelne Kraft-/Momentenbeiträge samt Angriffspunkten optional und
   hierarchisch zuschaltbar darstellen (z. B. Gesamt → Rumpf → Kiel/Ruder).
3. Verdeckte Komponenten nicht automatisch zusätzlich über die Summe
   zeichnen; eindeutige Darstellung von Frame, Einheit und Skala.
4. Bei Umschaltung zwischen Teil- und Summenansicht dürfen Datenwerte nicht
   verändert werden. Statische und Echtzeitdarstellung müssen konsistent
   dieselben Beiträge verwenden.
5. Genaue Widget-/Bediengestaltung erst anhand des bestehenden GUI-Musters
   umsetzen; diese Anleitung schreibt keine neue UI-Technologie vor.

**Tests:** Aggregat bleibt stets sichtbar; optionale Knoten toggeln korrekt;
Summenwerte sind Summe der angezeigten Komponenten; Angriffspunkte/
Momente deckungsgleich; Laufzeit- und GUI-Regressionen bestehen.

**Abnahme:** Summen sichtbar bei Defaultzustand; Komponenten optional
hierarchisch; keine Doppelzählung oder visuelle Fehlzuordnung bei
Frame-/Modus-/Körperwechsel.

### HYD-0013 – Getrennte Rudergrößenvariante und Steuervergleich

**Spec-Bezug:** Spec0019–Spec0022, Spec0043, Spec0051–Spec0052,
Spec0060, Spec0064–Spec0065.

1. Originalruder und Yachtpaket unverändert sichern/hashprüfen.
2. Nur nach HYD-0003/HYD-0004 eine separate Variante anlegen, die
   ausschließlich die begründete Abwärtsvergrößerung enthält.
3. Pose, Drehachse, Gelenkwinkel, Boden-/Rumpffreiheit, Massendaten und
   Schwerpunkt für die Variante neu bestimmen und validieren.
4. HYD-0005-Referenzmanöver mit Original und Variante unter identischen
   Einstellungen durchführen; vollständige Zeitreihen und Eingaben
   speichern.
5. Ergebnis gegen vorläufige 50-%-/10-s-Anforderung und Stabilitäts-/
   Winkelgrenzen bewerten. Wenn beide bestehen, keine Vergrößerung als
   erforderlich behaupten. Wenn beide scheitern, keine Vergrößerung
   automatisch als Lösung akzeptieren.
6. Produktivwechsel bleibt gesperrt, bis die Variante separat fachlich
   angenommen und die Paritäts-/Performancegates erfüllt sind.

**Tests:** Originalhash unverändert; Variantenmesh valide; kein
Selbstschnitt/ungültiges Volumen; Gelenk und Pose konsistent; keine
Kollision im erforderlichen Bewegungsbereich; gleiche Manövereingaben;
Wiederholbarkeit.

**Abnahme:** Variante eigenständig ladbar und vergleichbar; messbarer
Nutzen gemäß Spec0051 nachgewiesen; Produktivmodell unverändert bis
separater Freigabe.

### HYD-0014 – Vollständige physikalische und numerische Testmatrix

**Spec-Bezug:** Spec0038–Spec0044, Spec0064.

1. Für jeden Testfall vor Codeänderung Name, Modellklasse, Eingaben,
   Einheiten, Sollwert/-bereich, Toleranz und Herkunft dokumentieren.
2. Testgruppen:
   - Mesh-/Metadaten-/Hash-/Sidecar-Validierung;
   - profilierte/unprofilierte Klassifikation und Fehlerantworten;
   - Nullfluss, Vorzeichen, Spiegelung, Rotation und Hebelarm;
   - Dissipation/Energiebilanz und nichtnegative Widerstandsarbeit;
   - Modellgrenzen, ungültige Werte und deterministisches Neuladen;
   - Summenwrench versus unabhängige Summe aller Teilwrenches;
   - bestehende Auftriebs-/Hydrostatik-/Solver-/Dynamik-Goldens;
   - Ruderreferenzmanöver und separate Variantengeometrie.
3. Mindestens einmal die komplette Suite ausführen:

   ```powershell
   $env:QT_QPA_PLATFORM = "offscreen"
   .\.venv\Scripts\python.exe -m pytest -q
   ```

**Abnahme:** jede neue Anforderung hat mindestens einen automatisierten
Test oder einen begründet dokumentierten manuellen Abnahmeschritt;
fehlende Referenzwerte sind Gatefehler, keine toleranzfreien Tests.

### HYD-0015 – Zielhardware und Live-Performance

**Spec-Bezug:** Spec0033, Spec0045, Spec0054.

1. Messung auf der aktuellen Projekt-Zielhardware und mit den etablierten
   Last-/Benchmarkwerkzeugen durchführen; Hardware, Python, Qt, VTK,
   Modell, Konfiguration und Gitrevision protokollieren.
2. Vorher-/Nachher-Messung mit identischem Modell und identischen
   Einstellungen durchführen; Rohdaten und Auswertung speichern.
3. Nachholrate separat prüfen: Ziel mindestens `1,25 s/s` auf der
   etablierten Messung.
4. Sichtbaren Zehnminutenlauf messen. Ziel mindestens `30 FPS`, keine
   Überlastpause und kein wachsender Zeitrückstand; alle projektspezifischen
   P95-/Frameabstand-Grenzen aus dem Live-Gate zusätzlich anwenden.
5. Da die letzte dokumentierte sichtbare Baseline nur `13,04 FPS` mit
   Frameabstand-P95 `205,098 ms` und Überlastpause erreichte, gilt das
   Live-Gate derzeit als **nicht bestanden**. Erst eine neue, gültige
   Baseline kann die Produktivfreigabe öffnen.
6. Performance darf nicht durch stilles Überspringen von Physikzeit,
   reduzierte Genauigkeit oder verdeckte Pausen „bestanden“ werden.

**Abnahme:** alle geltenden Gates bestanden und reproduzierbar gespeichert;
bis dahin keine Produktivaktivierung.

### HYD-0016 – Dokumentation, Rückverfolgbarkeit und Freigabe

**Spec-Bezug:** Spec0001, Spec0008, Spec0035–Spec0037, Spec0044–Spec0048,
Spec0049–Spec0064.

1. Implementierte Verhaltensweisen, Modellstatus, Quellen, Grenzen,
   Bedienung, Konfigurationsschema und Wiederherstellung dokumentieren.
2. Traceability-Matrix Spec → HYD → Code/Tests/Messungen aktualisieren.
3. `SpecNNNN`-IDs nicht umnummerieren. Überholte Punkte nach der
   Projektregel am Dokumentende unter Original-ID archivieren.
4. Prüfen, dass Modellpakete ohne optionale Hydroartefakte unverändert
   laden; fehlende/ungültige Sidecars erzeugen eine klare Diagnose.
5. Produktivfreigabe nur nach Fachfreigabe, bestandenen Regressionen,
   bestandenen Referenz- und Performancegates sowie separater Freigabe einer
   möglichen Rudervariante.

**Abnahme:** vollständige Dokument-/Code-/Test-/Messverknüpfung; keine
unbelegten Zahlen; Nutzer kann jeden Kennlinienwert bis zu Quelle,
Geometriehash und Rechenversion zurückverfolgen.

## 3. Abhängigkeiten

Gezielte Testfälle werden bereits mit dem jeweiligen Arbeitspunkt erstellt
und ausgeführt. HYD-0014 konsolidiert diese Fälle zur vollständigen
Abnahmematrix; es ist keine Voraussetzung für die Implementierung isolierter
Modelle.

| Arbeitspunkt | Muss abgeschlossen sein vor Start |
|---|---|
| HYD-0001 | Keine |
| HYD-0002 | HYD-0001 |
| HYD-0003 | HYD-0001, HYD-0002 |
| HYD-0004 | HYD-0002, HYD-0003 |
| HYD-0005 | HYD-0002; HYD-0004 für Geschwindigkeitsfälle/Modellbereich |
| HYD-0006 | HYD-0002, HYD-0003 |
| HYD-0007 | HYD-0004, HYD-0006 |
| HYD-0008 | HYD-0004, HYD-0006 |
| HYD-0009 | HYD-0003, HYD-0004, HYD-0006, HYD-0007 |
| HYD-0010 | HYD-0003, HYD-0004, HYD-0006, HYD-0007 |
| HYD-0011 | HYD-0002, HYD-0008, HYD-0009 oder HYD-0010 |
| HYD-0012 | HYD-0011 |
| HYD-0013 | HYD-0003, HYD-0004, HYD-0005, HYD-0009/0010, HYD-0011 |
| HYD-0014 | Testfälle werden ab HYD-0001 ergänzt; finale Matrix nach HYD-0011–0013 |
| HYD-0015 | HYD-0001, HYD-0011, HYD-0014 |
| HYD-0016 | Alle übrigen anwendbaren Arbeitspunkte |

## 4. Tests und Freigabeübersicht

| Gate | Prüfumfang | Bestehenskriterium |
|---|---|---|
| G0 – Baseline | Loader, Modellpaket, Kraftmodell, Hydrostatik, Dynamik, GUI | Baseline dokumentiert; Regressionen bestanden oder offene Fehler blockieren. |
| G1 – Geometrievertrag | Meshmetriken, Klassen, Hashes, Paketmetadaten | deterministisch; Originaldateien unverändert; fehlende Merkmale als fehlend markiert. |
| G2 – Fachmodell | Quellen, Kurven, Vertrauensstatus, Gültigkeitsbereiche | jede Zahl nachvollziehbar; Näherung bleibt als solche markiert; Referenzvalidierung belegt. |
| G3 – Kräfte/Frames | Einzelbeiträge, Summenwrench, Energie, Vorzeichen | automatisierte Sollwerte und Wrench-Parität innerhalb vorab definierter Toleranzen. |
| G4 – Ruder | Je vorab festgelegtem Geschwindigkeitsfall: 50 % Abbau des 10° Kurs-über-Grund-Anfangsfehlers innerhalb 10 s nach Spec0064 | identischer Testregler, Geschwindigkeitsfall, Randbedingungen und Anfangszustand; Fehler bleibt nach erstmaligem Erreichen bei höchstens 50 %; kein Überschwingen oberhalb der Winkeltoleranz; Variante besteht Original-Fehlerfälle ohne Regression bestandener Fälle. |
| G5 – GUI | Summe immer, Komponenten optional/hierarchisch | korrekte Summe/Momente/Punkte; optionales Einblenden verändert keine Physikwerte. |
| G6 – Live | Zielhardware, Nachholrate, zehnminütiger Sichtlauf | mindestens `1,25 s/s`, mindestens `30 FPS`, keine Überlastpause/kein wachsender Rückstand sowie geltende P95-Gates. |
| G7 – Produktivfreigabe | vollständige Traceability und alle vorherigen Gates | explizite Fachfreigabe; alle anwendbaren Gates bestanden. |

## 5. Rückverfolgbarkeit Spec → Umsetzung

| Spec-IDs | Umsetzungsarbeit |
|---|---|
| Spec0001–Spec0005 | HYD-0001, HYD-0016 |
| Spec0109 | HYD-0001 |
| Spec0006–Spec0008 | HYD-0001–HYD-0002, HYD-0016 |
| Spec0009–Spec0013 | HYD-0002, HYD-0011, HYD-0014 |
| Spec0014 | HYD-0008 |
| Spec0015–Spec0018 | HYD-0003–HYD-0004, HYD-0007, HYD-0009 |
| Spec0019–Spec0022 | HYD-0003, HYD-0005, HYD-0013 |
| Spec0023–Spec0026 | HYD-0004, HYD-0008–HYD-0010 |
| Spec0027–Spec0029 | HYD-0002, HYD-0011, HYD-0014 |
| Spec0030–Spec0033 | HYD-0003, HYD-0006–HYD-0007, HYD-0015 |
| Spec0034 | HYD-0012 |
| Spec0035–Spec0037 | HYD-0002, HYD-0006–HYD-0007, HYD-0011, HYD-0016 |
| Spec0038–Spec0045 | HYD-0008–HYD-0015 |
| Spec0046–Spec0047 | HYD-0001, HYD-0016 |
| Spec0048 | HYD-0004 |
| Spec0049–Spec0050 | HYD-0003, HYD-0006 |
| Spec0051–Spec0052 | HYD-0005, HYD-0013 |
| Spec0053 | HYD-0003, HYD-0006, HYD-0014 |
| Spec0054 | HYD-0015 |
| Spec0055 | HYD-0012 |
| Spec0056–Spec0060 | HYD-0001, HYD-0004, HYD-0013, HYD-0016; als verworfene Ansätze beachten, nicht implementieren |
| Spec0061 | HYD-0003, HYD-0006 |
| Spec0062 | HYD-0004, HYD-0007 |
| Spec0063 | HYD-0004 |
| Spec0064 | HYD-0005, HYD-0013, HYD-0014 |
| Spec0065 | HYD-0005, HYD-0013 |
| Spec0066 | HYD-0005, HYD-0010, HYD-0013 |

## 6. Quellen und methodische Hinweise

- Die [ITTC Resistance Test Procedure](https://ittc.info/media/11780/75-02-02-01.pdf)
  ist eine methodische Quelle für Widerstandstests. Sie macht eine
  Reibungslinie allein nicht zum validierten Gesamtwiderstandsmodell einer
  beliebigen Yacht.
- Die [TU-Delft-Arbeit zur Kiel-Ruder-Interaktion](https://research.tudelft.nl/en/publications/keel-rudder-interaction-on-a-sailing-yacht/)
  ist ein möglicher Vergleich für yacht-spezifische Wechselwirkungen.
  Werte dürfen nur bei ausreichend passender Geometrie und Versuchsbedingung
  übertragen werden.
- Der [TU-Delft-Repositoriumsbericht zur Kiel-Ruder-Interaktion](https://repository.tudelft.nl/record/uuid:1be75bf7-04b2-4089-95af-95ac4031e034)
  ist vor Verwendung auf Datenzugang, genaue Versuchsmethode und
  Übertragbarkeit zu prüfen.
- Der [MIT-XFOIL-User-Primer](https://web.mit.edu/drela/Public/web/xfoil/xfoil_doc.txt)
  dokumentiert ein isoliertes 2D-Profilwerkzeug mit begrenzter
  Separation-/Stallbehandlung und ist keine 3D-Yachtvalidierung.

Diese Quellen sind Startpunkte für HYD-0004, nicht automatisch akzeptierte
Parameter-/Golden-Datensätze. Keine weitere Informationsquelle wird aus
`doc/Backlog/Ideen/` herangezogen.
