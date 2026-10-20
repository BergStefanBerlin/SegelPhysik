# Optimierungsliste SegelPhysik - nach absolutem Potenzial sortiert

**Basis:** Codeanalyse des Repos BergStefanBerlin/SegelPhysik (main, 20.10.2026) und
Web-Recherche zum Stand der Technik. Alle Befunde der vorherigen Durchsichten
(Serien A, B, C, D, E) sind hier zusammengefuehrt und nach **absolutem Zeitersparnis-
Potenzial** sortiert (Ersparnis je Ausloesereignis gewichtet mit typischer Haeufigkeit).

**Hinweise zu den Zahlen:** Groessenordnungen aus Codeanalyse, keine Messungen;
Faktor 2 Unsicherheit. Bedingte Hebel (nur bestimmter Pfad aktiv) sind mit
[bedingt] markiert. Legende der Zeilenanker: exakt = aus Sichtzaehlung,
ca. = geschaetzt an Funktionsnamen.

---

## Rangliste

| Rang | ID | Wo (Datei, Stelle) | Verbesserung | Potenzial | Quelle |
|------|----|--------------------|--------------|-----------|--------|
| 1 | **C1** | `grafik_bruecke.py`, `aktualisieren()` (ca. 707-730) | Dirty-Check per Pose-Fingerprint (R, Position, Koerper-Version): Wasserlinien-Schnitt `schneide_am_wasser(..., mit_deckel=True)` und Aufbau der drei PolyData-Objekte nur bei Aenderung, sonst nur `points` aktualisieren. | DOMINANT im GUI-Betrieb: 0,1-0,3 s je Frame in Ruhelagen werden komplett eingespart; Framerate steigt von ~3-10 auf 30+ fps; gibt ausserdem CPU-Kerne fuer den Physik-Worker frei (wichtig auf dem C++-Produktionspfad) | eigene Codeanalyse |
| 2 | **A1** | `core/auftrieb.py`, `_voxel_koerper` (225-232, mit 244-251) [bedingt: nur Voxel-Pfad] | Raeumliches Bucketing der Dreiecke nach Saeulen vor dem Scan statt je Saeule das gesamte Dreiecksarray zu testen; O(Saeulen x Dreiecke) -> O(Saeulen + Dreiecke). | Faktor 10-100 auf die Voxel-Auswertung: 0,3-3 s -> wenige ms je Solver-Iteration; je statischem Lauf 10 s bis Minuten Ersparnis | eigene Codeanalyse |
| 3 | **A3** | `core/voxelmodell.py`, `_auswerten_wasserhalbebene` (193-216) | Python-Saeulen-Loop durch vektorisierte NumPy-Logik ersetzen (searchsorted ueber alle Saeulen, maskierte Summation). Macht zusaetzlich den Naeherungspfad `voxel_koerperfest`/`voxel_opencl` produktionsreif (Freigabe als Naeherung noetig). | ca. 10x auf die Saeulenauswertung: 5-50 ms -> <1 ms je Physikschritt = 0,3-3 s je Simulationssekunde im Echtzeitbetrieb | eigene Codeanalyse |
| 4 | **E1** | C++-Kern (`_EbenenSchnitt` in den .hpp-Algorithmen), analog Python-Pfad | BVH ueber das Union-Mesh mit vorberechneten Volumen-/Momentsummen je Knoten; Ebenen-Query traversiert nur Knoten, deren AABB die Ebene schneidet; voll unterhalb liegende Knoten tragen ihre Summe bei, nur Randdreiecke werden geclippt. Exakt. | O(n) -> O(log n + k): bei 5.000 Dreiecken ca. 5-20x auf dem Schnitt, bei 100.000+ Dreiecken 100x+; Gewinn waechst linear mit Meshgroesse | Stack Overflow 21791666 (Schichtungs-/Sortierungsansatz); Stand der Technik Beschleunigungsstrukturen (BVH/kd-Baum) |
| 5 | **D1 / E3** | `core/kraftmodell.py`, `KraftmodellMitHydroCache.__call__` (Python) bzw. nativer Schnitt | Delta-basierte Invalidierung bzw. inkrementeller Schnitt statt `intervall=1`: Pose-Aenderung unter Schwellwerten (eps Translation / delta Rotation) => Hydrostatik behalten; nativ: nur neu geclippte Dreiecke updaten. Exakt mit steuerbaren Schwellwerten. | bis zu 40 % der Schrittzeit in ruhigen Phasen (0,3-1 ms je Schritt, Python-Pfad); wirkt auch nativ | eigene Codeanalyse; Prinzip der zeitlichen Kohaerenz aus Echtzeit-Physik |
| 6 | **D3** | `core/kraftmodell.py` (`mit_hydrostatik`, `aggregiere_kraftbeitraege`, `Wrench.__post_init__`, `mit_beschleunigung`) | Interne Pipeline auf NumPy-Arrays umstellen; Wrench/Kraftbeitrag-Objekte (ca. 10-20 validierte Datenklassen je Schritt mit tuple(float(...))-Konvertierung) nur an der API-Grenze bauen. | 15-30 % der Schrittzeit (0,2-0,5 ms); bei kleinen Modellen (Optimist) 30-50 % - dort der groesste Hebel | eigene Codeanalyse |
| 7 | **E4** | neu: Schnellstufe neben dem exakten Pfad | Vorberechnete Hydrostatik-Tabelle (V, K, ggf. Wasserflaeche) auf Gitter ueber Tiefgang x Kraengung x Trim, Laufzeit nur Interpolation (O(1)); Industriestandard der Schifffahrt (Bonjean-Kurven, Hydrostatic Tables, Cross Curves/KN). Validierung gegen den exakten Pfad ueber vorhandene `python_referenz()`-Infrastruktur. | groesster moeglicher Gewinn (O(1) statt O(n) je Pose); Naeherung mit steuerbarem Gitterfehler, Freigabe noetig | ShipCalculators Wiki "Hydrostatics and Bonjean curves"; ScienceDirect "Hydrostatic Data" (Tabellen-/Interpolationspraxis) |
| 8 | **A2** | `core/voxelmodell.py`, `_intervalle_saeule` (97-111, mit 25-61) | Dasselbe Bucketing wie A1, hier beim einmaligen Rasteraufbau. | 0,3-3 s -> ms je Modell (einmalig je Load) | eigene Codeanalyse |
| 9 | **B3** | `core/stationaer_hydrodynamik.py`, Newton-Schleifenende (ca. 318-322) | Redundante zweite `_residuum`-Auswertung nach Konvergenzabbruch streichen (beide Zweige berechnen identisch nochmals). | 0,5-3 s je statischem Lauf; trivial zu entfernen, risikofrei | eigene Codeanalyse |
| 10 | **E5** | `core/hydrodynamik.py`, `_benetzung_aus_dreiecksecken` (+ nativer counterpart) | Dieselbe BVH/Ebenen-Query wie E1 fuer die Nass/Trocken-Klassifikation nutzen; nur Dreiecke nahe der Wasserlinie brauchen Teilflaechen. | analog E1 auf dem Hydrodynamik-Anteil (O(n) -> O(log n + k) je Teil je Schritt) | wie E1 |
| 11 | **A6** | `core/hydrostatik.py`, `_ringe_aus_mesh` (56-79) | Kantenschnitt-Logik vektorisieren statt Python-Loop je Dreieck mit kleinen NumPy-Einzeloperationen und Dict-Einfuegen. | 0,2-1 s -> wenige ms je Hydro-Modellaufbau (je statischem Lauf) | eigene Codeanalyse |
| 12 | **C3/C4** | `gui/hauptfenster.py` (`_EchtzeitAufgabe.__init__`, ca. 66) + `core/koerper.py`, `snapshot()` (ca. 470-520) | Snapshot an `Koerper._version` cachen: Baum-Durchlauf + Transformation + Kopie aller Blattpunkte nur bei tatsaechlicher Aenderung. | 1-5 ms x 62 Tasks/s = 0,1-0,3 s je Echtzeitsekunde (10-30 % eines Kerns); kleiner Eingriff | eigene Codeanalyse |
| 13 | **C2** | `grafik_bruecke.py`, `gelenkwinkel_setzen()` (ca. 587-610) | Gelenk-Slider-Ereignisse entprellen/coalescen; `_farbgruppen` + Pruefung + komplette Union-Geometrie (`_benetzte_geometrie`) nur einmal pro Frame statt je Ereignis neu. | 0,1-0,5 s je Gelenkinteraktion; bei aktivem Ziehen mehrere Sekunden je Interaktionsminute | eigene Codeanalyse |
| 14 | **A4** | `wasser_schnitt.py`, `_punkt_in_ring` (375-381, genutzt 409-413) | Punkt-in-Polygon vektorisieren (Ray-Casting ueber alle Kanten gleichzeitig); `any()`-Rolling ueber alle Ringe in `_deckel_setzen` durch Batch-Test ersetzen. | 10-100 ms -> ms je Wasser-Schnitt; hilft zusaetzlich C1 (gleicher Pfad) | eigene Codeanalyse |
| 15 | **A5** | `core/hydrodynamik.py`, `wasserlinienlaenge_m` (301-311) | Dreifach verschachtelte Schleife (Teile x Dreiecke x 3 Kanten) durch zonal klassifizierte Kanten + gebatchte Schnittpunkte ersetzen. | 50-200 ms -> wenige ms; 1-2x je statischem Lauf | eigene Codeanalyse |
| 16 | **A7** | `render/vista.py`, `IsoSurfaceWater.splat` (204-211) | Kernel-Offsets auf die Kernreichweite (Kugel statt Wuerfel) trimmen: 343 Offsets, davon viele mit garantiert Gewicht 0; Loop weiter vektorisieren. | 20-50 ms -> ~1/3 je Frame; ca. 1-3 s Rechenzeit je Echtzeitminute; gibt Kerne fuer den Physik-Worker frei | eigene Codeanalyse |
| 17 | **C5** | `core/mesh.py`, `_lade_obj_roh` (ca. 495-515) | Doppelter OBJ-Parse vermeiden: einfachen Parser beim ersten Fehler abbrechen lassen oder robusten Parser als Standard nutzen. | 50-200 ms je Modell-Load (Parse-Arbeit halbiert) | eigene Codeanalyse |
| 18 | **B1** | `core/auftrieb.py`, `kraftfunktion_berechne` (295) | Bindung (`als_bindung(koerper)`) einmalig in `baue_kraftfunktion` cachen statt je Auswertung den Koerperbaum neu zu durchlaufen. | 1-5 ms je Auswertung = 0,1-0,3 s je statischem Lauf | eigene Codeanalyse |
| 19 | **C6** | `core/mesh.py`, `_polygon_selbstschneidet` (ca. 158-200), `_trianguliere_polygon` (ca. 200-300) | O(n^2)-Selbstschnitt und Ear-Clipping O(n^2)-O(n^3) nur bei Vieleck-OBJs relevant; im CPP-Pfad bereits native geloest. Ggf. Vielecke direkt an die native Triangulation durchreichen. | 10-100 ms je Vieleck-Polygon (Ladezeit) | eigene Codeanalyse |
| 20 | **D2** | `core/dynamik_6dof.py`, `schritt()` (Validierungsblock am Anfang) | Konstante Validierungen aus dem Schrittzug herausziehen: `np.linalg.eigvalsh(inertia)`, Symmetriepruefung, vier `_vektor`-Pruefungen einmal beim Worker-Start. | ca. 5 % der Schrittzeit (0,05-0,1 ms); risikofrei | eigene Codeanalyse |
| 21 | **C7** | `gui/hauptfenster.py`, `_StatischeAufgabe.run` (ca. 160-175) | Konfiguration (lade_physik + lade_konfig) pro Konfig-Stand cachen statt je statischem Lauf neu zu laden/validieren. | 5-20 ms je Lauf (< 0,1 s) | eigene Codeanalyse |
| 22 | **D4/B4** | `core/hydrodynamik.py`, `beitraege_erzeugen` | Normalen-Gueltigkeitsmaske cachen (Normalen sind unveraenderlich) statt sie je Aufruf - hier je Physikschritt - neu zu berechnen; Allokation `eck_en @ rotation.T` wiederverwenden. | 0,02-0,05 ms je Schritt (< 0,1 s je Lauf) | eigene Codeanalyse |
| 23 | **D5** | `core/dynamik_6dof.py`, `schritt()` | `quaternion_matrix(q)` nur einmal je Schritt berechnen und die Rotation durchreichen statt doppelt. | 0,01-0,02 ms je Schritt | eigene Codeanalyse |
| 24 | **B2** | `wasser_schnitt.py`, `_ketten` (312-350) | Verkettung der Kontursegmente ueber Set-/Dict-Lookup statt Listen-Scan je Schritt (Worst Case quadratisch). | 10-100 ms je Schnitt, gelegentlich | eigene Codeanalyse |

---

## Alternativen und nicht empfohlene Ansätze

| ID | Ansatz | Bewertung | Quelle |
|----|--------|-----------|--------|
| E2 | Sortierung + Praefixsummen je Normalenrichtung (statt BVH) | Nur fuer feste/quantisierte Richtung sinnvoll; hier dreht die Normale mit der Pose (Kraengung/Trim). E1 vorziehen. | Stack Overflow 21791666 |
| E6 | GPU/SDF-Voxelpfade als Ersatz des exakten Schnitts | Fuer Engineering-Genauigkeit nur als Vergleichs-/Beschleunigungsstufe; OpenCL-Voxel existiert im Projekt bereits (`voxel_opencl`). | Kim et al. 2006 (doi:10.1007/s00371-006-0071-x); aktuelle SPH/SDF-Kopplung 2025/26 |
| - | Convex-Hull-Naeherung der getauchten Vertices | < 3 % Volumenfehler bei 60 Hz, aber bei nicht-konvexen Ruempfen systematisch verzerrt; nicht engineering-exakt. | Pith Science 2025 (pith.science/paper/2509.03804) |
| - | Wechsel der Boolean-Bibliothek (z. B. trueform/MeshLib statt Manifold) | Nicht der Engpass: Union laeuft einmalig, nicht je Pose. 3-5x schnellere Bibliotheken aendern an der Laufzeit praktisch nichts. | MeshLib Blog 2026; dev.to Benchmark (trueform 3,9-5,5x vs. Manifold/MeshLib) |

## Kontextnotizen

- **Grundsatzbewertung:** Die Algorithmenfamilie des nativen Kerns (exakte
  Divergenzsatz-Integration auf einmal vorbereitetem Union-Mesh, ca. 11 Flops je
  Dreieck) entspricht dem Stand der Technik und modernen Panel-Methoden der
  Hydrostatik. Es fehlt nicht das richtige Verfahren, sondern Wiederholungsvermeidung
  zwischen den Posen - genau das leisten E1/E3/E4. Hintergrund: Rosenzweig 2018
  ("Hilariously Fast Volume Computation with the Divergence Theorem"); Vorlaeufer
  Messner/Taylor, ACM TOMS Algorithm 550 (1980).
- **Produktionspfad:** Default ist `cpp` (`rechenpfad.py`). Die Python-Befunde
  A3, D1-D5 wirken dort nicht direkt; dort dominieren C1/A7 (GUI verbraucht Kerne)
  und die Batchgroesse der Echtzeit-Requests.
- **Nicht im Dynamik-Schrittpfad:** A5 und A6 laufen nur im statischen Solver bzw.
  der Diagnostik; A1/A2 nur auf dem Voxel-Pfad.

## Quellenverzeichnis

1. Rosenzweig, A. (2018): "Hilariously Fast Volume Computation with the Divergence Theorem" - alyssarosenzweig.ca/blog/hilariously-fast-volume-computation-with-the-divergence-theorem.html
2. Messner/Taylor (1980): ACM TOMS Algorithm 550, Surface Integral Method fuer Mass Properties
3. Stack Overflow, Frage 21791666: "How to calculate the volume BELOW of a 3D mesh where the surface is made up of triangles"
4. Kim, J., Kim, S., Ko, H. et al. (2006): "Fast GPU computation of the mass properties of a general shape and its application to buoyancy simulation", The Visual Computer 22, 856-864 - doi:10.1007/s00371-006-0071-x
5. Pith Science (2025): "Real-Time Buoyancy Estimation for AUV Simulations Using Convex Hull-Based Submerged Volume Calculation" - pith.science/paper/2509.03804
6. ShipCalculators Wiki: "Hydrostatics and Bonjean curves" und "Cross Curves of Stability and KN Tables" - shipcalculators.com/wiki
7. ScienceDirect Topics: "Hydrostatic Data" / "Hydrostatic Calculation"
8. MeshLib Blog (2026): "Comparing 3D Boolean Libraries"; "Manifold alternative for 3D Boolean Operations" - meshlib.io/blog
9. dev.to (2026): "Evaluating Python Mesh Boolean Libraries: MeshLib, Manifold, and trueform"
