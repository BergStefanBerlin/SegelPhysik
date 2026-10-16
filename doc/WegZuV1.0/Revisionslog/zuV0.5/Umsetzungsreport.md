# Umsetzungsreport zu Spec v0.5

**Stand:** 16.10.2026

**Grundlage:** Implementierung im Repository, dokumentierter Umsetzungsplan,
automatisierte Tests und B-03-Bericht.
**Gesamtstatus:** Weit fortgeschritten, aber nicht vollständig abgenommen.
Phase 11 ist teilweise umgesetzt; Phase 12 ist auf Nutzerwunsch vertagt.

> **Bewertung:** „Vollständig“ bedeutet, dass die geplanten Funktionen in der
> Codebasis implementiert und durch Tests oder Inventar belegt sind. Es
> bedeutet nicht automatisch, dass sämtliche formellen G1–G4-Gates der Phase
> abgenommen sind. „Teilweise“ benennt konkrete offene Punkte. „Nicht
> umgesetzt“ bedeutet, dass die neue Funktionalität der Phase fehlt; vorhandene
> Altphysik wie Hydrostatik bleibt davon unberührt.

## Phasenübersicht

| Phase | Thema | Status | Kurzbeschreibung und offener Punkt |
|---:|---|---|---|
| 0 | Bestehendes Verhalten einfrieren und messen | **Teilweise** | Baseline-Datensatz für B-01–B-11 und Modellinventar sind vorhanden. Die Erfassung wurde mit dirty Worktree dokumentiert; nicht jede spätere Änderung ist gegen alle Baseline-Arbeitslasten erneut gemessen. |
| 1 | Datenverträge, Koordinaten und Versionsregeln | **Vollständig** | v0.5-Spezifikation legt Manifest, IDs, Frames, Körperzustand, Verantwortungstrennung, Einheiten und Migrationsregeln fest. |
| 2 | Kanonisches Mesh und sichere Geometrieauflösung | **Vollständig** | Unveränderliche SI-Meshes, OBJ-/Formresolver, sichere Paketpfade, strenge Topologie- und Selbstüberschneidungsprüfung sind implementiert und getestet. Der Symlink-Test ist in der Windows-Umgebung übersprungen. |
| 3 | Modellloader und Paketkatalog | **Vollständig** | Versionierter Manifestloader, Materialinjektion, Baum-/Referenzvalidierung, Katalog und Paketbeispiele sind vorhanden; das Bestandsinventar ist dokumentiert. |
| 4 | Laufzeitkörper und einheitliche Fabrik | **Vollständig** | Paketfabrik erzeugt Einzel- und Verbandskörper, aggregiert Massenkennwerte und hält Rollen, Mesh, Posen sowie Metadaten. Repo-Paketpfad ist per Einstellung wählbar; Legacy bleibt als Rückfall erhalten. |
| 5 | Posen und Simulationszustand | **Vollständig** | Benannte Frames, Posekomposition und inverse Transformationen sowie Körperzustand und unveränderliche Snapshots sind implementiert und getestet. |
| 6 | Einheitlicher Kraftbeitragsvertrag | **Vollständig** | `Kraftbeitrag`, `Wrench` und `KraftErgebnis` führen Kräfte und Momente mit Frame/Bezugspunkt zusammen. Hydrostatik, Widerstände, Fremdkraft und Gewicht fließen in die gemeinsame Auswertung ein. |
| 7 | Statische Simulation auf Snapshot umstellen | **Teilweise** | Statischer Worker rechnet auf Körper-Snapshot; Generationsschutz und Übernahme der akzeptierten Solver-/Darstellungslösung sind vorhanden. Der statische Callback schreibt die akzeptierte Pose noch nicht direkt in `Koerper.zustand`; dieser wird erst beim Start der Dynamik aus dem Solverresultat initialisiert. |
| 8 | Dynamischen Schritt auf Laufzeitkörper umstellen | **Vollständig** | 6-DOF-Schritt, Hydro-/Kraftauswertung, Worker-Aufträge, Zustandsvalidierung und Generationsschutz sind in der Echtzeit-GUI verbunden. |
| 9 | Settings, GUI-Baum und gemeinsame Darstellung | **Teilweise** | Manifest-IDs, Rollen/aktivierte Blätter, Schema-1.2-Modellschalter, Renderer, Status und Snapshots sind integriert. Die Kamera folgt der Translation des Körpers; vollständige Körperorientierungsbindung und formelle GUI-/Leistungsabnahme sind noch nicht belegt. |
| 10 | Bewegliche Teile als Ein-Körper-Näherung | **Teilweise** | Gelenkmanifest, Elternframe-Achse, Winkelzustand/Snapshot und Rendering sind umgesetzt. Masse, Schwerpunkt, Trägheit und Auftrieb bleiben wie spezifiziert an der Anfangspose. Gelenkwinkel wirken noch nicht auf Hydro-/Aerodynamikbeiträge; vollständige Mehrkörperdynamik ist ausgeschlossen. |
| 11 | Produktionsumschaltung und Altpfade kontrolliert entfernen | **Teilweise** | Schalter, Rückfallpfad und Dry-run-first-Migrationswerkzeug mit Nichtüberschreibschutz bestehen Tests. Migration mit realen externen Nutzerbeständen, deren GUI-Integration, systematischer Alt-/Neu-Workflowvergleich und formelle G1–G4-Cutover-Abnahme fehlen. |
| 12 | Hydrodynamik und Aerodynamik | **Nicht umgesetzt** | Keine neuen empirischen Rumpf-/Segelkräfte oder Koeffizienten aktiviert. Auf Nutzerwunsch vertagt, bis Wind-/Strömungsmodelle und Referenzdaten fachlich festgelegt sind (Backlog B-21). Bereits vorhandene Hydrostatik und konfigurierte Widerstände bleiben davon unberührt. |

## Nachweise und Grenzen

| Nachweis | Ergebnis |
|---|---|
| Vollständige Testsuite | **562 passed, 1 skipped**; übersprungener Test benötigt Symlink-Rechte, die in der Windows-Umgebung fehlen. |
| B-03, Paketfabrik gegenüber explizitem Legacy-Pfad, T-011 aktiv | **Bestanden**; Medianverhältnis Paket/Legacy `0,883`, Bootstrap-95-%-Intervall `[0,859; 0,913]`, 30 gepaarte Messungen. |
| Gelenkverhalten | Rendering und Zustand ändern sich; aggregierte Masse, Schwerpunkt, Trägheit und Auftriebsgeometrie bleiben unverändert. |
| Migration | Dry-run legt keine Zielpakete an; bei Validierungsfehlern wird nichts veröffentlicht; vorhandene Pakete werden nicht überschrieben; Quellen bleiben unverändert. |

Die vollständige Umsetzung ist noch nicht erreicht: Die größten verbleibenden
Arbeiten sind die Phase-11-Cutover-Abnahme und, nach fachlicher Freigabe,
Phase 12. Das aktuelle Klassendiagramm und der Datenfluss stehen in den
separaten Dateien [Klassendiagramm_aktuelle_Loesung.md](./Klassendiagramm_aktuelle_Loesung.md)
und [Datenfluss_Koerper_bis_Simulation.md](./Datenfluss_Koerper_bis_Simulation.md).
