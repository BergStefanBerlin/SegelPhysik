# Spezifikation V0.10: Zeitkritische Verarbeitung nach C++ übertragen

**Stand:** 19.10.2026  
**Status:** Entwurf zur Nutzerprüfung; keine pauschale Migrations- oder Produktivfreigabe  
**Version:** V0.10  
**Entwicklungsbranch:** `v0.10`

## Zweck und Ausgangspunkt

Alle zeitkritischen Funktionen und zusammenhängenden Verarbeitungsblöcke
sollen in C++ ausgeführt werden, soweit sie nicht bereits wirksam in nativen
Bibliotheken laufen. Python bleibt für Bedienung, Konfiguration,
Versuchssteuerung und geeignete Schnittstellen erhalten.

**Ausschließlich Performanceverbesserungen sind zulässig.** Der Sprachwechsel
ist keine Erlaubnis für Funktionsabbau, geringere Darstellungsqualität,
andere Physik, neue Näherungen oder gelockerte numerische Toleranzen.
Eine bloße C++-Hülle um dieselbe langsame Aufrufkette ist kein Erfolg.

Gesicherter Ausgangspunkt ist Tag `0.9`, Commit `1b16648`. Der zu
vergleichende V0.10-Arbeitsstand enthält zusätzlich die bestätigte
Quelltrennung und die native Buildgrundlage ohne den inzwischen entfernten
Hallo-Verbindungstest. Dieser konkrete
Stand muss vor Messbeginn als unveränderliche Vergleichsbasis gesichert
und mit Commit, Konfiguration und Buildinventar bezeichnet werden.
Der frühere Verbindungstest war kein Leistungsnachweis.

Quellablage:

- Python: [code/python/segelphysik](../../../../../code/python/segelphysik).
- C++: [code/cpp](../../../../../code/cpp).
- Gemeinsame Modelle: [code/modelle](../../../../../code/modelle).
- Buildprodukte außerhalb der Quellen unter `build/native`.

Die vorhandene [Buildanleitung](../../../../../code/cpp/README.md)
beschreibt das native Modul. Die [v0.9-Abnahme](../../zuV0.9/Umsetzungsplan/Abnahme_v0.9.md)
und der [Echtzeitbericht](../../zuV0.9/Messungen/Echtzeit_Abnahme_U000004-U000008_2026-10-19.md)
bleiben historische Nachweise, ersetzen aber keine neue Vergleichsmessung.

### Befunde, nicht Annahmen

Im v0.9-Workerprofil waren Hydrostatik/Geometrie, Hydrodynamik und
Kraftaggregation relevante Kostenblöcke. GUI-Aufbereitung war ebenfalls
ein wesentlicher Engpass. Dies beweist noch keinen Hotspot jeder unten
genannten Einzelfunktion.

Der exakte Unionpfad vereinigt starre Teilmeshes bereits bei der
Vorbereitung und besitzt einen Ebenenschnitt im vorbereiteten Frame.
Diese Fähigkeiten sind Bestand, keine neu zu erfindenden Optimierungen.
NumPy, VTK, Qt und Manifold3D enthalten bereits nativen Code. Bei ihnen
sind Python-Aufrufanzahl, Datenkopien, Zwischenergebnisse und Vorbereitung
zu untersuchen, nicht pauschal die native Bibliothek neu zu schreiben.

## Aktive Anforderungen

### A-V0.10-00001 — Vollständigkeit und Nachweis zeitkritischer Pfade

Alle produktiven zeitkritischen Pfade für Echtzeit, Statik, stationäre
Hydrodynamik, sichtbare Darstellung sowie Modellaufbau/-änderung sind zu
inventarisieren und bis zu ihren aufwendigen Unterfunktionen zu verfolgen.
Die untenstehende Liste ist ein verbindliches Startinventar, keine
Erlaubnis, später gefundene Hotspots zu ignorieren.

Für jede genannte Funktion bzw. jeden klar abgegrenzten Block ist
nachzuweisen: Aufrufpfad, Häufigkeit, Eigen-/Gesamtzeit, Eingabegröße,
Zuordnung zu Python/nativer Bibliothek, Migrationsentscheidung und Test.
Hilfsfunktionen ohne eigenen messbaren Anteil dürfen mit dem nativen
Elternblock übertragen werden; ihre Abdeckung bleibt einzeln sichtbar.
Neu identifizierte eigenständig prüfbare Blöcke erhalten neue unbenutzte
A-Kennungen an sachlich passender Stelle, ohne Umnummerierung.

Ein gemessener zeitkritischer Python-Rechenkern wird nach C++ übertragen.
Ausnahmen sind nur zulässig, wenn er bereits nativ ausgeführt wird, keine
Zeitkritikalität nachgewiesen wird oder der native Kandidat keinen
reproduzierbaren Vorteil erzielt. Ein weiterhin relevanter ungelöster
Hotspot bleibt offen; eine Ausnahme ist kein erfüllter Migrationspunkt.

### A-V0.10-00002 — Unveränderte Funktionalität und numerische Verträge

Alle unterstützten Eingaben, Ausgaben, Einheiten, Koordinatensysteme,
Vorzeichen, Rollen, Modellannahmen, Fehlerfälle und Bedienabläufe bleiben
erhalten. Das gilt auch für benannte Einzelkräfte/-momente, Angriffspunkte,
Diagnosen, GUI-Steuer-API, persistente Einstellungen und Moduswechsel.

Bestehende exakte Referenztoleranzen sind maßgeblich, nicht die größeren
pädagogischen Fehlerbudgets. Die freigegebenen Genauigkeitsgrenzen
Fassung 1 bleiben unverändert; sie dürfen keine numerische Verschlechterung
des unveränderten Verfahrens legitimieren. Float64 bleibt der Standard
für die entsprechende bisherige Float64-Rechnung.

Nicht zulässig sind insbesondere Fast-Math ohne gesonderten
Äquivalenznachweis, geringere Rechengenauigkeit, größere/adaptive
Zeitschritte, größere Hydrostatikintervalle, gerundete Zustandscaches,
Ersatzmeshes, Kennfelder oder neuronale Ersatzmodelle als Teil dieser
Migration. Ebenso wenig dürfen Kräfte, Overlays oder Aktualisierungen
weggelassen werden. Bereits vorhandene Optionen behalten ihre Bedeutung.

### A-V0.10-00003 — Grobkörnige native Schnittstelle und Datenbesitz

Das native Modul wird über pybind11 angebunden. Vorbereitete Körper-,
Mesh-, Massen- und Verfahrensdaten bleiben für ihre gültige Lebensdauer
im nativen Kontext. Ein Physikbatch darf nicht pro Teilkraft, Dreieck oder
Integrationsschritt nach Python zurückrufen. Einzelaufrufe bleiben für
Vergleichstests und bestehende öffentliche Verträge adaptierbar.

Arrayform, Datentyp, Speicherlayout, Besitz, Veränderbarkeit und
Lebensdauer werden explizit definiert und validiert. Keine ungültigen
Zeiger auf kurzlebige NumPy-Daten, keine unbemerkten Kopien großer
Modelldaten je Schritt. Kopien und Übergabekosten werden gemessen.
Ausgaben bleiben außerhalb ihrer nativen Lebensdauer gültig.

### A-V0.10-00004 — Build, Installation und Referenzbetrieb

Reproduzierbarer Release-Build für die vorhandene Windows-x64-Umgebung
mit Projekt-Python, MSVC, CMake und deklarierten Buildabhängigkeiten.
Keine manuelle globale PATH-Manipulation und keine Binärprodukte im
Quellbestand. Compiler-/Python-/Bibliotheksversionen und Buildflags
werden dokumentiert; Neuinstallation und sauberer Neubau werden geprüft.

Die Python-Referenz bleibt während der Migration explizit auswählbar.
Fehlender/fehlerhafter nativer Code darf nicht stillschweigend auf Python
zurückfallen und einen nativen Erfolg vortäuschen. Ein bewusst gewählter
Referenzbetrieb und der tatsächlich aktive Rechenpfad sind erkennbar.
Die GUI bleibt bei fehlendem Modul mit expliziter Diagnose bedienbar;
ein nativer Auftrag gilt dann nicht als erfolgreich gerechnet.

### A-V0.10-00005 — Native Ausführung, Fehler und Nebenläufigkeit

Der Workerprozess und seine Generation-/Sequenz-/Modellzuordnung bleiben
korrekt. Reine C++-Rechnung gibt den GIL frei, sofern dabei keine
Python-Objekte oder Python-APIs berührt werden. Qt-/VTK-Aufrufe erfolgen
nur auf dem jeweils zulässigen Thread; GIL-Freigabe ersetzt keine
Thread-Sicherheit.

Ungültige Eingaben und native Fehler werden in die vorhandenen
Fehler-/Protokollwege übersetzt. Kein Überschreiten von Arraygrenzen,
kein Weiterrechnen mit NaN/Inf und keine success-shaped Ersatzantwort.
Start, Pause/Fortsetzung, Modellwechsel, Abbruch/Verwerfen veralteter
Aufträge und Schließen während der Berechnung müssen funktionieren.
Keine neue Parallelisierung oder andere Reduktionsreihenfolge ohne
Numerik-, Nebenläufigkeits- und Performancevergleich.

### Einzelne Migrationsblöcke

Die Funktionsnamen beziehen sich auf den Python-Ausgangsstand.
**Laufzeit** bedeutet Bestandteil des untersuchten Berechnungspfads,
nicht bereits einzeln gemessener Hotspot. **Aufbau** umfasst Lade-,
Änderungs- und Vorbereitungszeiten; diese werden separat von FPS bewertet.
Python-Adapter dürfen verbleiben, die zeitkritische innere Arbeit nicht.

#### A-V0.10-00006 — Quaternionen und 6-DOF-Integration

Quelle: `core/dynamik_6dof.py`. Den vollständigen inneren Integrationspfad
einschließlich seiner Validierung und Kraftauswertung nativ ausführen.

| Einzelne Funktion | Zu erhaltender Inhalt |
|---|---|
| `quaternion_normalisieren` | Normierung, ungültige Quaternionen |
| `quaternion_matrix` | Quaternion zur Rotationsmatrix |
| `quaternion_aus_matrix` | Matrix zur Quaternion, alle Fallzweige |
| `_quaternion_multiplizieren` | Multiplikationsreihenfolge |
| `_orientierung_schritt` | Orientierungsfortschritt |
| `schritt` | Translation, Rotation, Trägheit, Widerstand/Added Mass und Ergebnisvertrag |
| `_vektor` | Eingabeprüfung im nativen Pfad |

`quaternion_slerp` ist gesondert in A-V0.10-00024 erfasst.

#### A-V0.10-00007 — Kraft- und Momentenaggregation

Quelle: `core/kraftmodell.py`.

| Einzelne Funktion / Block | Zu erhaltender Inhalt |
|---|---|
| `Wrench.auf_bezugspunkt` | Bezugspunktwechsel und Hebelarmmoment |
| `aggregiere_kraftbeitraege` | Gesamtbilanz und sämtliche benannten Beiträge |
| `KraftErgebnis.gesamt_wrench` | Ergebnisdarstellung am richtigen Bezugspunkt |
| `KraftErgebnis.mit_beschleunigung` | Beschleunigungsbezogene Ergebnisergänzung |

#### A-V0.10-00008 — Zusammengesetztes Kraftmodell

Quelle: `core/kraftmodell.py`.

| Einzelne Funktion / Block | Zu erhaltender Inhalt |
|---|---|
| `Kraftmodell.__call__` | Hydrostatik und weitere Module gemeinsam |
| `Kraftmodell.mit_hydrostatik` | Linearer/quadratischer Widerstand, Fluidbezug, Hydrodynamik, Fremdkraft, Schwerkraft |
| `Kraftmodell.fremdkraft_setzen` | Kraft und körperfester Angriffspunkt |
| `Kraftmodell.ruderwinkel_setzen` | Validierte Übergabe an Rudermodell |
| `_hydrostatik_lage`, `_position_aus_lage` | Unterstützte Lageformate und Frames |
| `_vektor`, `_flussvektor`, `Wrench.__post_init__` | Native Grenzvalidierung statt Python-Aufwand je Beitrag |
| `KraftmodellMitHydroCache.__call__`, `aktualisieren` | Bestehende Intervall-/Resetsemantik; Standardintervall unverändert 1 |

#### A-V0.10-00009 — Benetzung und hydrodynamische Flächen

Quelle: `core/hydrodynamik.py`.

| Einzelne Funktion / Block | Zu erhaltender Inhalt |
|---|---|
| `_benetzte_dreiecksflaechen` | Benetzte Flächenbestimmung |
| `_benetzung_aus_dreiecksecken` | Voll-, Teil- und Nichtbenetzung |
| `HydrodynamikModell.beitraege_erzeugen`: Geometrieblock | Dreiecksecken/-mittelpunkte, Normalen, benetztes Zentrum und Hebelarme |
| `wasserlinienlaenge_m` | Verwendete Wasserlinienlänge |

#### A-V0.10-00010 — Hydrodynamische Kräfte aller vorhandenen Rollen

Quelle: `core/hydrodynamik.py`, zusammenhängend mit A-V0.10-00009.

| Einzelne Funktion / Block | Zu erhaltender Inhalt |
|---|---|
| `ittc_reibungsbeiwert` | Bestehende Formel und Gültigkeitsbehandlung |
| `beitraege_erzeugen`: Rumpfblock | Reibung, Formfaktor, projizierte Querfläche |
| `beitraege_erzeugen`: Kiel-/Ruderblock | Anströmwinkel, Ruderwinkel, Liftbegrenzung, Profil-/induzierter Widerstand |
| `beitraege_erzeugen`: Volumenkörperblock | Lokale Flächengeschwindigkeiten, Kräfte und Eigenmomente |
| `HydrodynamikModell.ruderwinkel_setzen` | Winkelgrenzen und Fehlerfälle |

Nullströmung, reine Translation/Rotation, Rückwärtsströmung, Teilbenetzung
und fehlende optionale Module werden getrennt verglichen.

#### A-V0.10-00011 — Hydrodynamische Vorbereitung und Ruder-Testnäherung

Quellen: `core/hydrodynamik.py`, `core/hydrodynamik_ruder_naeherung.py`.

| Einzelne Funktion / Block | Kontext |
|---|---|
| `hydrodynamik_teile_aus_koerper`, `_generische_teile_aus_koerper` | Aufbau |
| `HydrodynamikTeil.__post_init__`, `HydrodynamikModell.aus_koerper` | Vorbereitete Geometriedaten |
| `RuderTestkinematik.pose` | Bereits vorhandene explizite Testkinematik |
| `RuderGeometrie.aus_mesh` | Ruder-Geometrievorbereitung |
| `RuderKraftNaeherung.beitrag_erzeugen`, `f_alpha_pro_rad` | Vorhandener optionaler Näherungspfad |

Die Migration aktiviert keine bisher nicht freigegebene Modellannahme.

#### A-V0.10-00012 — Hydrostatik und Auftriebsbilanz

Quelle: `core/auftrieb.py`.

| Einzelne Funktion / Block | Zu erhaltender Inhalt |
|---|---|
| `lage_pruefen`, `pose_matrix`, `_in_welt` | Lagevalidierung und Transformation |
| `_tetraeder_beitraege` | Volumen-/Momentenbeiträge |
| `_exakt_blatt`, `_unterwasser_teile` | Blattweise Geometrieauswertung |
| `kraftfunktion_berechne` | Unterstützter bestehender Auftriebspfad |
| `baue_kraftfunktion`, `baue_kraftfunktion_6dof` einschließlich erzeugter Closures | Vorbereitung und wiederholte Kraft-/Momentenrechnung |

Gesamtvolumen, verdrängtes Volumen, Schwerpunkt, Auftrieb und Moment
einschließlich trocken/vollständig nass bleiben äquivalent. Seglerpunktmassen
erhalten unverändert keinerlei Verdrängung.

#### A-V0.10-00013 — Exakter vorbereiteter Union-Ebenenschnitt

Quelle: `core/volumen_union.py`.

| Einzelne Funktion / Block | Zu erhaltender Inhalt |
|---|---|
| `_EbenenSchnitt.__init__` | Vorbereitete Determinanten und Momente |
| `_EbenenSchnitt._summe` | Tetraederreduktion |
| `_EbenenSchnitt.auswerten` | Schnittfälle mit 0/1/2/3 inneren Ecken, Abschlussflächen, Randkonvention |
| `VorbereitetesUnionModell.auswerten_ebene` | Normalisierung und gültige Ebeneneingaben |

Die vorhandene Randbehandlung für Punkte auf der Ebene, kleinen Volumina
und Schwerpunktbestimmung bleibt erhalten. Nicht durch einen Voxelpfad ersetzen.

#### A-V0.10-00014 — Union-Vorbereitung und native Bibliotheksübergänge

Quelle: `core/volumen_union.py`; Aufbau und vorhandene alternative Referenzpfade.

| Einzelne Funktion / Block | Zu untersuchender Anteil |
|---|---|
| `_manifolds_aus_meshes` | Validierung, Konvertierung und native Vorbereitung |
| `_volumen_schwerpunkt_aus_soliden` | Volumen-/Schwerpunktaggregation |
| `_mesh_aus_union`, `_volumen_schwerpunkt_aus_union` | Extraktion, Momente, gegebenenfalls Schnitt |
| `VorbereitetesUnionModell.__init__` | Bereits vorhandene einmalige Vereinigung |
| `VorbereitetesUnionModell.auswerten` | Transformation und Auswertung |
| `auswerten_ebene_manifold`, `gesamtwerte` | Erhalt des Bibliotheksreferenzpfads und der Gesamtwerte |
| `volumen_schwerpunkt_union` | Bestehender äußerer Vertrag |

Manifold3D nicht ohne Nachweis neu implementieren. Wo die Arbeit bereits
nativ läuft, kann der Abschlussnachweis aus nativer Ausführung und
reduzierten Übergängen bestehen; eine bloße Umbenennung reicht nicht.

#### A-V0.10-00015 — Wasserlinienschnitt und Deckelgeometrie

Quelle: `wasser_schnitt.py`.

| Einzelne Funktion / Block | Inhalt |
|---|---|
| `_clip_polygon`, `_fan_triangulieren` | Polygonbeschnitt und Triangulierung |
| `_schnittkontur_berechnen`, `wasserlinie_aus_teilmesh` | Schnittsegmente |
| `schneide_am_wasser` | Über-/Unterwassergeometrie einschließlich bestehender Varianten |
| `mesh_volumen` | Volumen des Schnittmeshes |
| `einzigartige_konturpunkte`, `polygonzug_der_kontur`, `_ketten` | Konturverknüpfung |
| `_ring_flaeche_xy`, `_punkt_in_ring`, `_deckel_setzen` | Orientierung, Ringzuordnung und Deckel |

#### A-V0.10-00016 — Hydrostatik-Wasserlinienkennwerte

Quelle: `core/hydrostatik.py`.

| Einzelne Funktion | Inhalt |
|---|---|
| `_ringe_aus_mesh` | Zusammenhängende Konturen |
| `_ringmomente` | Flächen-/Trägheitsmomente |
| `wasserlinien_querschnitt` | Wasserlinienkennwerte |
| `wasserlinien_bei_pose` | Poseabhängige Auswertung |

#### A-V0.10-00017 — Robuster statischer Solver

Quelle: `core/statisch_robust.py`. Iterationen und ihre Kraftauswertungen
gemeinsam nativ ausführen; Fortschritt/Abbruch dürfen grobkörnig angebunden bleiben.

| Einzelne Funktion | Inhalt |
|---|---|
| `_residuum`, `_fd_spalte` | Residuum und finite Differenzen |
| `_sekante_1d`, `_dmdphi` | Eindimensionale Suche und Ableitung |
| `_vertikales_gleichgewicht`, `_gm_aus_rollableitung` | Höhenlösung und Stabilität |
| `_suche_stabile_rolllage`, `_newton_versuch` | Rollsuche und Newtonverfahren |
| `_diagnose`, `loese_robust` | Diagnose, Lösungswahl und äußerer Solververtrag |

Suchreihenfolge, Abbruchbedingungen, Toleranzen, stabile Lösungswahl und
vorhandene diagnostische Fehler bleiben gleich.

#### A-V0.10-00018 — Weiterer statischer Solver

Quelle: `core/statisch.py`.
`_residuum`, `_dmdphi`, `loese` und `_metazentrische_hoehe` sind
einzeln im Inventar nachzuweisen und bei relevantem Aufrufpfad nativ
zu übertragen. Nicht stillschweigend durch den robusten Solver ersetzen.

#### A-V0.10-00019 — Stationärer Hydrodynamiksolver und Dynamikprüfung

Quelle: `core/stationaer_hydrodynamik.py`.

| Einzelne Funktion | Inhalt |
|---|---|
| `_rotation`, `_pose_und_bewegung` | Zustands-/Frameabbildung |
| `_beitrag_werte`, `_residuum` | Beiträge und Restgrößen |
| `_stufe_ergebnis`, `loese_stationaer` | Stufen, Konvergenz, Resultate |
| `pruefe_stationaer_dynamisch` | Vorhandene dynamische Nachprüfung |

#### A-V0.10-00020 — Körperaggregation, Snapshots und Gelenke

Quellen: `core/koerper.py`, `core/frames.py`.

| Einzelne Funktion / Block | Inhalt |
|---|---|
| `Koerper._baue_verband`, `Koerper.verband` | Rekursive Massen-/Schwerpunkt-/Steiner-Aggregation |
| `Koerper.snapshot`, `Koerper.teil_aggregate` | Versionsgebundene Rechendaten und Teilaggregate |
| `Koerper.punkte_in_welt`, `setze_pose`, `setze_rel_pose` | Numerische Transformationen; Python-Eigenschaftsadapter dürfen bleiben |
| `Koerper.gelenkwinkel_setzen` | Geometrie-/Aggregatänderung und Invalidierung |
| `Pose.rotationsmatrix`, `punkt_transformieren`, `vektor_transformieren`, `punkte_transformieren` | Frameoperationen |
| `Pose.invers`, `Pose.komponieren` | Inverse und Verkettung |
| `pose_aus_modellpose`, `rotationsmatrix_achsenwinkel`, `pose_mit_gelenkwinkel` | Modell-/Gelenkabbildung |

Punktmassen, aktive Blätter, Materialänderungen und Gelenke müssen sämtliche
abhängigen nativen Vorbereitungsdaten rechtzeitig aktualisieren.

#### A-V0.10-00021 — Meshvalidierung und Masseneigenschaften

Quelle: `core/massen.py`; überwiegend Aufbau-/Änderungsleistung.

| Einzelne Funktion / Block | Inhalt |
|---|---|
| `validiere_mesh_eingaben`, `validiere_mesh` | Form, Endlichkeit, Indizes und Topologie |
| `_kreuzprodukt_3d` | Geometrischer Hilfskern |
| `_koplanare_dreiecke_schneiden`, `_segment_dreieck_schneiden` | Schnittprädikate |
| `_koplanare_paare_schneiden`, `_segmentpaare_dreieck_schneiden`, `_dreieckspaare_schneiden` | Paarprüfungen |
| `_pruefe_mesh_selbstueberschneidung`, `pruefe_mesh_selbstueberschneidung` | Selbstschnitt einschließlich Fehlerkontext |
| `validiere_traegheitstensor` | Trägheitsprüfung |
| `mesh_volumen`, `mesh_flaeche` | Volumen und Oberfläche |
| `schwerpunkt_homogen`, `schwerpunkt_flaechig` | Schwerpunkte |
| `traegheitstensor_homogen`, `traegheitstensor_flaechig` | Volumen-/Flächenträgheit |

#### A-V0.10-00022 — Weitere numerische Modellvorbereitung

| Quelle | Einzelne Funktionen / Blöcke |
|---|---|
| `core/mesh.py` | `_polygon_selbstschneidet`, `_trianguliere_polygon`, `_obj_mesh_cached`, `mesh_aus_quelle`: numerischer Anteil; Dateipfad-/Schemaadapter dürfen Python bleiben |
| `core/koerper_formen.py` | `build_cone`, `build_box`, `build_pyramid`, `build_sphere`, `build_cylinder`, `build_plate`, `build_hexprism`, `build_polyhedron`, `_konvexe_huelle`, `_volumenschwerpunkt`, `_zentriert`, `_liegend`, `_ring`, `_g`, `baue_aus_form` |
| `core/formerkennung.py` | `_dreiecke_daten`, `_schwerpunkt_und_kovarianz`, `_oberflaechenpunkte`, `_achsenkandidaten`, `_ist_kurve`, `_profil_art`, `analysiere`, `analysiere_koerper` sowie zugehörige Klassifizierungs-/Rollneutralitätsableitung |
| `core/geometrie_konflikte.py` | `_manifold`, `_mesh_daten`, `_bounds_ueberschneiden`, `_schnittvolumen`, `finde_konflikte`, `differenzieren`, `_obj_zu_welt`, `_welt_zu_obj` |
| `core/hydrodynamik_metadaten.py` | `_geometrie_messen`, `_baue_metadaten`, `erzeuge_geometriemetadaten`: numerische Vermessung |

Jede genannte Funktion erhält einen eigenen Inventareintrag, auch wenn
mehrere gemeinsam migriert werden. Atomare Dateioperationen,
Sicherungen, JSON-/OBJ-Semantik und Fehlerkontexte bleiben erhalten.
Kein Beschleunigen durch Auslassen von Validierung.

#### A-V0.10-00023 — Physikbatch und Datentransport

Quellen: `core/echtzeit_prozess.py`, `gui/hauptfenster.py`.

| Einzelne Funktion / Block | Inhalt |
|---|---|
| `echtzeit_prozess.initialisieren` | Nativen Modellkontext einmalig vorbereiten |
| `echtzeit_prozess.schritte_berechnen` | Ganze Schrittfolge nativ, gültige Batchparameter und Fehlervertrag |
| `_EchtzeitAufgabe.run` | Prozess-/Threadadapter und Ergebnisübergabe |
| `_StatischeAufgabe.run` | Nativer Solveraufruf, Fortschritt und Fehlerabbildung |
| `HauptFenster._echtzeit_aufgabe_abgeschlossen` | Ergebnisdekodierung und gültige Zustandsübernahme |

Qt-Signale, Scheduling und Protokollierung dürfen Python bleiben.
Keine Python-Kraftcallbacks im nativen Batch. Serialisierung,
Allokationen und Kopien sind separat von Rechenzeit auszuweisen.

#### A-V0.10-00024 — Anzeigeinterpolation und Poseaufbereitung

Quellen: `core/dynamik_6dof.py`, `gui/hauptfenster.py`.

| Einzelne Funktion / Block | Inhalt |
|---|---|
| `quaternion_slerp` | Kürzester Orientierungsübergang und Randfälle |
| `_echtzeit_render_takt`: numerischer Teil | Zustandsauswahl und Positions-/Orientierungsinterpolation |
| `_echtzeit_pose_anzeigen` | Poseübergabe und zugehörige Aufbereitung |
| `_stationaere_rotation`, `_stationaere_kraftlage` | Stationäre Darstellungstransformation |
| `_navigationspose_ermitteln`, `_segelwinkel_ermitteln` | Numerische Pose-/Winkelableitung |

Monotone Anzeigeuhr, Puffer, Pause/Fortsetzung, kein Vorspulen,
keine Extrapolation und unveränderter Physikzustand bleiben verbindlich.
Timer-/Signalverknüpfungen müssen nicht nach C++ umgeschrieben werden.

#### A-V0.10-00025 — Körperdarstellung und Farbberechnung

Quelle: `grafik_bruecke.py`.

| Einzelne Funktion / Block | Inhalt |
|---|---|
| `_polydaten`, `_dreiecks_polydaten`, `_gesichter` | Array-/VTK-Geometrieaufbereitung |
| `_farbgruppen`, `_benetzte_geometrie` | Bestehende drei Farb-/Benetzungspfade |
| `GrafikBruecke._actors_aktualisieren`, `_gruppen_actors` | Numerische Geometrie-/Poseaufbereitung |
| `physik_pose_6dof_setzen`, `_statisch_anwenden` | Körpertransformation und Kopplung der Anzeigen |

Bereits native VTK-Operationen dürfen bestehen bleiben. Viele kleine
Python-Übergänge sind gegebenenfalls durch eine native Sammelaktualisierung
zu ersetzen, nicht durch eine neue Darstellung mit anderem Aussehen.

#### A-V0.10-00026 — Kraftpfeile, Momentbögen und Achsen

Quellen: `core/kraefte_bild.py`, `core/overlays.py`, `grafik_bruecke.py`.

| Quelle / Block | Einzelne Funktionen |
|---|---|
| Pfeil-/Liniengeometrie | `pfeil_daten`, `pfeil_fest`, `strich_linien`, `kraft_pfeile`, `zusatz_pfeile` |
| Momente / Hebelarme | `paar_moment_auftrieb`, `paar_moment_kraft`, `hebelarm_segment`, `moment_bogen`, `moment_bogen_achse`, `wirkungslinie_auf_geometrie`, `skala_waehlen` |
| Hauptachsen | `overlays._kanonisiere`, `overlays.hauptachsen` |
| Actoraufbereitung | `_kraftpfeil_zeichnen`, `_momentbogen_zeichnen`, `_kugel_zeichnen`, `_kugel_mesh_setzen`, `_kraefte_actors` |
| Overlayaufbereitung | `_overlays_aktualisieren`, `_overlay_schwerpunkt_setzen`, `_overlay_hauptachsen_setzen`, `_roehre_oder_linie` |
| Wiederverwendung | `_overlay_translation_aus_cache`, `_overlay_translation_merke`, `_overlay_signatur` |

Längen, Radien, Farben, Layer, Vordergrundverhalten, Sichtbarkeit und
Invalidierung bleiben gleich. Nicht weniger Pfeile oder Details anzeigen.

#### A-V0.10-00027 — Wassergeometrie und Wasserspuren

Quellen: `render/vista.py`, `core/wasserpunkte.py`, `grafik_bruecke.py`.

| Quelle / Block | Einzelne Funktionen |
|---|---|
| Oberflächenaufbereitung | `_surface_polydata`, `_bilinear_upsample`, `_unit_circle`, `_unit_square` |
| Vorhandene Isofläche | `IsoSurfaceWater.splat`, `mesh`, `_mirrored`, `_calibrate`, `_half` |
| Renderer-Geometrie | `PyVistaRenderer._smooth_surface`, `_update_ring`, `_clamp_to_bodies`, `update`: numerischer Anteil |
| Wasserpunkte | `_hash01`, `punktlage`, `dunst_gitter`, `WasserPunktFeld.punkte_welt`, `aktualisieren` |
| Bewegungs-/Spuraufbereitung | `GrafikBruecke._wasser_bewegung_nachfuehren`, `_wasserpunkte_zeichnen`, `_flaeche_verschieben` |

Auflösung, Wasseroptik, Transparenz, Spuren und deterministische Punktlagen
werden nicht zur Leistungsverbesserung reduziert.

#### A-V0.10-00028 — Navigation, Instrumente und Kamera

Quellen: `core/navigationsanzeigen.py`, `gui/navigationswidgets.py`,
`grafik_bruecke.py`.

| Einzelne Funktion / Block | Inhalt |
|---|---|
| `navigationswerte_ableiten`, `winkel_360`, `wrap_180`, `richtung_16` | Winkel-, Kurs-, Abdrift- und Richtungswerte |
| `_rotation_setzen`, `_fehlerkreis`, `_gefahrenring` | Instrumentgeometrie/-transformation |
| `SVGInstrumentWidget._render`, `aktualisieren` | Sichtbare Instrumentaufbereitung |
| `GeschwindigkeitsWidget.aktualisieren`, `paintEvent` | Vorhandene Geschwindigkeitsanzeige |
| `NavigationsWidgetFenster._instrumente_rendern` | Sammelaktualisierung, versteckte Fenster unverändert behandeln |
| `GrafikBruecke.navigationskamera_aktualisieren`, `_vordergrund_kamera_abgleichen` | Kameraberechnungen und Synchronisierung |

Qt-Painting ist bereits nativ; nur nachgewiesene Python-Aufbereitung
übertragen. Keine zusätzliche Kameraglättung, veränderte Perspektive,
geringere Instrumentfrequenz oder geänderte SVG-Optik.

#### A-V0.10-00029 — Kinematische und weitere bestehende Bewegungspfade

| Quelle | Einzelne Funktionen / Blöcke |
|---|---|
| `core/bewegung.py` | `rotation_matrix`, `body_pose`, `koerper_pose`; numerische Poseberechnung |
| `core/dynamik.py` | `schritt`, `schritt_mit_kraeften`; soweit noch aufgerufen |
| `core/stoerung.py` | `rotationsmatrix`, `stoss_pose`, `projektion`, `kontakt_start`, `beste_loesung` |
| `render/vista.py` | `screen_to_water`, `_body_half_height`, `_refresh_arrows`: numerischer Anteil |

Kinematik, Störung und vereinfachte Dynamik werden nicht durch den
6-DOF-Pfad ersetzt. Zufalls-/Störungsparameter und Bedienverhalten bleiben gleich.

#### A-V0.10-00030 — Bereits vorhandene optionale Voxel-/GPU-Pfade

Diese Bestandsoptionen sind im Vollständigkeitsinventar getrennt zu führen:

| Quelle | Einzelne Funktionen / Blöcke |
|---|---|
| `core/auftrieb.py` | `_y_intervalle_saeule`, `_paare_bereit`, `_voxel_koerper`, `_y_intervalle_saeule_v` |
| `core/voxelmodell.py` | `_intervalle_saeule`, `KoerperfestesVoxelmodell.__init__`, `auswerten`, `auswerten_6dof`, `_auswerten_wasserhalbebene` |
| `core/physik_backend.py` | `OpenCLVoxelHydrostatik.auswerten_6dof` und dessen Datenvorbereitung/-transfer |

Bereits native OpenCL-Kernels werden nicht als Python-Neumigration gezählt.
Python-Hotspots im optionalen Aufrufpfad sind bei nachgewiesener
Zeitkritikalität ebenfalls zu übertragen. Ein neuer Build darf keine bisher
gesperrte Voxel-/GPU-Option produktiv freigeben oder bestehende
Genauigkeitsfehler verdecken. Keine neue GPU-/NPU-Abhängigkeit.

### A-V0.10-00031 — Paritäts- und Regressionstest pro Migrationsblock

Jeder implementierte Block wird mit identischen Eingaben direkt gegen die
gesicherte Python-Referenz verglichen. Nicht nur Endlagen, sondern auch
Zwischengrößen, Einzelbeiträge, Arrays, Frames, Randfälle und Fehlerwege
werden geprüft. Vorhandene Tests werden nicht abgeschwächt.

Mindestumfang: Optimist, Folkeboot, yacht1 sowie vorhandene analytische/
generische Testkörper; trocken/teil-/vollbenetzt; Wasserlinienwechsel;
Roll-/Nick-/Gierlagen; Masse/Seglerposition/Gelenk-/Modelländerung;
Null-/Rückwärts-/Rotationsströmung; Fremdkraft und Ruder; Statik,
stationäre Lösung und dynamische Zustandsfolgen zu gleichen Zeiten.
Dynamikvergleiche umfassen mindestens die vorhandenen 30-s-Prüfvorgaben;
längere Schwingungs-/Abklingfälle bleiben dort erforderlich, wo messbar.

GUI-Klicks, Start/Pause/Fortsetzung, Modell-/Moduswechsel, sichtbare
Lernanzeigen und API-Steuerung bleiben geprüft. Native Schnittstellentests
prüfen die jeweils real migrierten Funktionen; der entfernte
Hallo-Verbindungstest wird nicht als Produktfunktion wieder eingeführt.
Nach jeder integrierten Migrationsstufe laufen passende Regressionen;
vor Gesamtfreigabe die vollständige Projektsuite und eingefrorene
Referenzprüfung. Keine fehlende native Installation als Skip verstecken.

### A-V0.10-00032 — Reproduzierbarer Performancegewinn ohne Gegenleistung

Für jeden Kandidaten sind native Rechenzeit sowie Konvertierung,
Vorbereitung, Kopien, GIL-/Prozessübergänge und Gesamtzeit zu messen.
Mikrobenchmarkgewinne ohne Vorteil im zugehörigen Anwendungspfad reichen
nicht zur Produktivübernahme.

Vorher/Nachher verwenden dieselbe Zielhardware, Python-/Bibliotheksumgebung,
Modelle, Eingaben, Zeitschritte, Auflösung/Viewport/DPR, Layer, Wasseroptik,
SSAO/MSAA, Warm-up und Simulationsgeschwindigkeit. Standardoptik und der
bestehende explizite Schulungsmodus werden getrennt betrachtet; eine
Optikumschaltung darf keinen C++-Gewinn vortäuschen.

Mindestens drei vergleichbare Wiederholungen je Ausgangs-/Kandidatenstand
sind auszuwerten. Live-Vergleiche umfassen jeweils mindestens fünf Minuten
nach Aufwärmung. Berichtet werden Rohwerte, Median/P95, Streuung,
Physikdurchsatz, Rückstandtrend, Qt-Swaprate, Frameabstände, Eingabeproxy,
Start-/Lade-/Änderungszeit und Speicherentwicklung. Instrumentierte Profile
werden von unverfälschten Leistungsabnahmen getrennt.

Ein Kandidat wird nur übernommen, wenn sein End-to-End-Vorteil im
betroffenen Pfad reproduzierbar und größer als die beobachtete
Messstreuung ist, alle Paritätsgates bestehen und kein anderer relevanter
Bedien-/Simulationspfad reproduzierbar verschlechtert wird. Kein
Performanceversprechen allein aufgrund der Sprache. Es wird noch kein
unbelegter Faktor wie 2x oder 10x vorgeschrieben.

Die bisherigen Softwareziele (mindestens 30 Qt-Swaps/s,
Frame-P95 höchstens 67 ms, Eingabeproxy-P95 höchstens 100 ms und kein
dauerhaft wachsender Physikrückstand bei 1x über fünf Minuten) bleiben
Vergleichsgrößen, kein Ersatz für den zusätzlichen C++-Nutzenbeleg.
Qt-Swaps und Eingabeproxy bleiben ausdrücklich keine optische
Monitor-/Photonenmessung.

### A-V0.10-00034 — Performanceverbesserung jeder Übertragung dokumentieren

Für jede einzelne übertragene Funktion und jeden übertragenen Block ist
ein dauerhafter Vorher-/Nachher-Nachweis verpflichtend. Sammelberichte
sind zulässig, müssen aber jede Einzelfunktion bzw. jeden Block eindeutig
zuordnen; allein ein Gesamt-FPS-Wert reicht nicht.

Jeder Eintrag nennt A-ID, Quellfunktion/Block, Python-Referenzcommit,
C++-Kandidatencommit, Testeingaben und Messkommando, Hardware,
Buildflags und Versionen, Wiederholungen, Rohdaten sowie Median/P95.
Python- und C++-Zeiten, absolut eingesparte Zeit, relative Verbesserung
und Beschleunigungsfaktor sind auszuweisen. Übergabe-, Kopier- und
Vorbereitungsaufwand sowie der End-to-End-Nutzen im zugehörigen
Anwendungspfad werden getrennt dokumentiert. Paritätsergebnis und
Messstreuung gehören zum selben Nachweis.

Bei gemeinsam übertragenen Hilfsfunktionen sind deren Anteile, soweit
messbar, separat zu erfassen; andernfalls ist ausdrücklich festzuhalten,
dass der Nutzen nur für den gemeinsam ausgeführten Block nachgewiesen
ist. Kein erfundener individueller Beschleunigungsfaktor.
Fehlender, nicht messbarer oder negativer Gewinn wird explizit genannt
und darf nicht als dokumentierte Performanceverbesserung gelten.
Produktivübernahme bleibt an A-V0.10-00032 gebunden.

### A-V0.10-00033 — Vollständiger Abschluss und nachvollziehbarer Status

Die Abnahmematrix führt jede A-ID und jeden darin genannten
Einzelfunktions-/Blockeintrag mit einem dieser Zustände:

- nativ übertragen, eingebunden und mit Gewinn abgenommen;
- bereits native Ausführung nachgewiesen;
- gemessen nicht zeitkritisch, mit Profilbeleg;
- Kandidat ohne Gewinn verworfen, Anforderung gegebenenfalls weiter offen;
- noch offen oder blockiert, mit konkreter Ursache.

Nicht ausgeführte, fehlgeschlagene oder nicht vergleichbare Prüfungen gelten
nicht als bestanden. Alle ermittelten zeitkritischen Python-Rechenblöcke
müssen ohne verdeckte Python-Innenschleifen abgedeckt sein; andernfalls
darf kein vollständiger Migrationsabschluss behauptet werden.
Unproduktive Kandidaten werden nicht als implementiert protokolliert.

Erfüllte Anforderungen werden nach Abnahme im zentralen
[Umsetzungslog](../../../../Log/Log.md) erfasst. Bestehende
Kennungen bleiben unverändert. Diese Spezifikation ist kein
Umsetzungsplan und vergibt deshalb keine U-Kennungen.

## Umfangsgrenzen und noch ausstehende Freigabe

Nicht verlangt ist eine vollständige Neuschreibung von GUI, Dateiverwaltung,
Konfigurationsschema, Modellkatalog oder Werkzeugen in C++. Deren schwere
numerische Teilpfade sind jedoch nicht pauschal ausgenommen.
Keine neue Physik, vereinfachte Darstellung, NPU-Ersatzmodelle,
neue Engine, Hardwareanschaffung oder neue Produktivfreigabe vorhandener
experimenteller Verfahren als Nebenwirkung dieser Migration.

Der Nutzer prüft diesen Entwurf vor Erstellung eines verbindlichen
Umsetzungsplans. Insbesondere ist noch keine bestimmte Beschleunigungshöhe
zugesagt; die Forderung nach ausschließlich Performanceverbesserung
und vollständigem Funktionserhalt ist verbindlicher Entwurfsinhalt.

## Nicht umsetzen

Aktuell keine zurückgezogenen Anforderungen. Dieser Abschnitt ist kein
Backlog; spätere Rücknahmen werden unter ihrer ursprünglichen Kennung
mit Begründung archiviert.
