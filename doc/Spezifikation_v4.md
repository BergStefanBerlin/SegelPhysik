# SPEC V4: Körper-Klasse & Architektur (verbindliche Fassung)

Status: VOLLSTÄNDIG – alle Punkte entschieden oder bewusst zurückgestellt
(Stand 11.10.2026; mehrere Konsistenzprüfungen, letzte inkl. Eingabedatei-Beschluss,
Dateinamen-Klärung und Text-Überarbeitungsdurchlauf).
Zweck: Verbindliche Grundlage für die Umsetzung (Schritt 1: Körper-Klasse).
Datum: 11.10.2026

---

## A. Architektur-Rahmen (unstrittig)

**A1 – Welt als Mastersystem.** Alle Posen (Position + Orientierung) sind weltbezogen.
Alles Sichtbare und alle Berechnungen (Wasserlinien-Schnitt, Kräfte, Achsen)
laufen in Weltkoordinaten. Welt: rechtshändig, z nach oben, Ursprung auf der
Wasseroberfläche, x = Bug, y = Backbord.

**A2 – Zwei Frames pro Körper.**
| Frame | Ursprung | Wer legt fest | Zweck |
|---|---|---|---|
| Konstruktionsframe | dort, wo modelliert wurde | Erbauer (nur Eingabekanal) | Geometrie eingeben, Teile platzieren |
| **Schwerpunktframe** | Massenschwerpunkt, Achsen parallel zum Konstruktionsframe | Klasse, automatisch berechnet | Darstellung, Berechnung, Physik |

---

## P1 – Koordinatensysteme [ENTSCHEIDEN]

**Regel (verbindlich):** Der Schwerpunktframe ist DAS einzige sichtbare und
rechnende System – für Darstellung, Physik und alle Ausgaben. Der
Konstruktionsframe ist KEIN Teil der Rechen- und Ausgabe-API. Einzige,
ausdrückliche Ausnahme: als Eingabekonvention beim Erzeugen (Geometrie-Eingabe,
rel_Posen von Teilbodies – siehe P2 Punkt 4). Nach der
Schwerpunktberechnung verschiebt die Klasse alle Punkte um −r_S; ab dann
existiert er nur noch intern und ist für den Nutzer unsichtbar.

**Berechnung des Schwerpunkts (automatisch, nie von Hand):**
- Homogener Körper: geometrischer Schwerpunkt = Masseschwerpunkt, berechnet aus
  dem Mesh (Divergenzsatz über geschlossene Dreiecks-Meshes).
- Zusammengesetzter Körper: jeder Teilbody hat eigene Masse; Gesamtschwerpunkt
  = massengewichtete Summe der Teil-Schwerpunkte:
      m = Σ m_i
      r_S = (Σ m_i · r_S,i) / m
      I_S = Σ ( I_S,i + m_i · ( ‖d_i‖²·1 − d_i·d_iᵀ ) )   [Parallel-Achsen-Satz]
  wobei d_i = Vektor vom Gesamtschwerpunkt zum Teil-Schwerpunkt i; die
  Teil-Tensoren I_S,i sind zuvor mit der rel_Pose (P2) in den Orientierungs-
  frame des Elternteils rotiert worden.
- Nach der Berechnung gilt der Schwerpunktframe als „das wahre Koordinatensystem"
  des Körpers.

**Akzeptanzkriterien P1:**
- AK-P1a: Homogener Quader → r_S exakt in der Mitte (< 1e-12).
- AK-P1b: Homogener Kegel (H=2, R=1) → r_S bei H/4 über Basis (< 1e-9).
- AK-P1c: Zusammengesetzter Zweiteilkörper → r_S gegen unabhängige Integration < 0,1 %.
- AK-P1d: Boot (8 OBJ-Teile, Dichten laut Materialtabelle) → r_S plausibel unter
  Rumpfmitte, gegen numerische Referenzintegration < 0,5 %.
  (Materialzuordnung je Teil: festgelegt in der Arbeitsdatei `konfiguration.json`,
  JSON-Pfad `boot.teile` – Rumpf/Ruder GfK, Kiel Stahl, Bulb Blei, Mast/Boom
  Aluminium, Segel über Flächenmasse 0,5 kg/m².)

---

## P2 – Komposition (Rekursion) [ENTSCHEIDEN]

**Regel (verbindlich):** Durchgängig rekursiv – Flachheit ist eine Folge, keine Sonderregel.
1. Ein Körper kann Teile enthalten; jedes Teil ist selbst ein vollwertiger Körper
   (eigene Form, eigene Masse/Dichte/Material/Flächenmasse gemäß P3, eigene Farbe
   gemäß P4, eigener berechneter Schwerpunktframe gemäß P1).
2. Einfache Modelle sind automatisch flach (ein Teil oder keins) – kein separater
   Flach-Modus, keine Sonderbehandlung.
3. Verschachtelte Gruppen jederzeit möglich; die Klasse behandelt jede Tiefe
   identisch mit denselben Summationsregeln aus P1. Reale Beispiele in der
   Vorlage (Spec-Abschnitt J): „rigg“ (Mast + Boom + Großsegel + Fock) und
   „kielsystem“ (Kiel + Bulb) – beide reine Gruppen ohne eigene Werte.
   WICHTIG: Die Gruppierung ändert NICHTS an den Gesamtwerten des Boots
   (Masse, Gesamtschwerpunkt, Tensor sind identisch zur flachen Struktur –
   die Rekursion summiert dasselbe). Ihr Gewinn ist semantisch: benannte
   Zwischenaggregate (z. B. „Schwerpunkt des Kielsystems“) und später die
   Fähigkeit, eine Gruppe ALS EINHEIT zu manipulieren (z. B. Rigg kippen).
4. API: Der Konstruktor nimmt eine Teile-Liste; jede rel_Pose wird im
   Konstruktionsframe des Elternkörpers angegeben (lesbar in Modellkoordinaten),
   ausgewertet wird rekursiv von der Wurzel abwärts.
5. Reine Gruppen (ohne eigene Form, z. B. „Rigg“) haben KEINEN Massen-Parameter:
   Die Genau-eins-Regel aus P3 gilt nur für Körper mit eigener Geometrie.
   Masse, Schwerpunkt und Tensor einer Gruppe ergeben sich AUSSCHLIESSLICH aus
   ihren Teilen (Summationsregeln P1) – eine Angabe an der Gruppe wäre entweder
   doppelt gezählt oder unbelegbar und ist daher unzulässig.

---

## P3 – Massen-Input [ENTSCHEIDEN]

**Regel (verbindlich):** Genau EINE der folgenden Größen ist Pflicht pro Körper/Teil.
Weder zwei gesetzt noch keins gesetzt → Validierungsfehler beim Erzeugen.

| Parameter | Einheit | Bedeutung | Typischer Einsatz |
|---|---|---|---|
| `masse` | kg | explizite Gesamtmasse | Testfälle, Overrides, Kalibrierung |
| `dichte` | kg/m³ | Materialdichte; m = ρ · V (V aus Mesh, Divergenzsatz) | Normalfall für Volumenkörper |
| `material` | Auswahl | benanntes Material → feste Dichte aus Tabelle | bequeme Standardfälle |
| `flaechenmasse` | kg/m² | m = f · A (A = Flächeninhalt des Meshes) | Flächen ohne Volumen (Segel!) |

Alle vier laufen intern auf dieselbe Teilmasse m_i; danach ist alles einheitlich
(rekursive Summation gemäß P1).

**Materialtabelle (Default-Werte; Quelle: Arbeitsdatei `konfiguration.json`, beschrieben in Spec-Abschnitt J):**

| Material | Dichte (kg/m³) | Quelle/Anmerkung |
|---|---|---|
| Holz | 600 | Mittelwert übliche Bootsbauhölzer (Fichte ~450 … Eiche ~750); bewusst gerundeter Default |
| GfK | 1900 | typisches Laminat im Bootsbau (~1800–2000) |
| Stahl | 7850 | Standardwert |
| Blei | 11340 | Standardwert |
| Aluminium | 2700 | ergänzt 11.10. für Mast/Boom (Leichtmetall, kein Stahl-Ersatzwert) |

**Wassertabelle (Umwelt; Quelle: ebenfalls `konfiguration.json`, Spec-Abschnitt J):**

| Wasser | Dichte (kg/m³) | Anmerkung |
|---|---|---|
| Süßwasser | 1000 | bisheriger Spec-Default |
| Salzwasser | 1025 | Standardwert Ozean |
| Totes-Meer-Wasser | 1240 | typischer Literaturwert (~1230–1240) |
| Quecksilber | 13546 | Referenz/Sonderfall |

**Konsequenzen:**
- ALLE Tabellen und Defaults (Materialien, Wasser, Boot-Zuordnung, ΔL, Default-
  Farbe) stammen ausschließlich aus der Arbeitsdatei `konfiguration.json`
  (Spec-Abschnitt J) – im Code gibt es keine stillen Duplikate dieser Werte.
- Wasser-Dichte ist in `konfiguration.json` hinterlegt (Auswahl per Name oder
  direkter Zahl; direkte Zahl bleibt immer zulässig).
- Für V3 (kinematisch) hat die Masse keinen Effekt auf die Darstellung – die
  Klassen-API trägt sie aber schon, damit V4 ohne Umbau aufsetzen kann.
- Segel: als Flächen (ohne Volumen) zwingend über `flaechenmasse`; Dichte/Material
  an einem volumenlosen Mesh ist ein Validierungsfehler.
- Reine Gruppen ohne eigene Form (P2 Punkt 5) haben keinen Massen-Parameter;
  ihre Masse ergibt sich ausschließlich aus den Teilen.

**Akzeptanzkriterien P3:**
- AK-P3a: Validierung – genau-eins-Regel wirft Fehler in beiden Verstoßfällen.
- AK-P3b: Quader 2×2×2 m mit dichte=1000 → m = 8000 kg exakt.
- AK-P3c: material="Blei" auf Bulb-Geometrie → m = 11340 · V_Bulb.
- AK-P3d: Segelfläche 10 m² mit flaechenmasse=0,5 → m = 5 kg exakt.

---

## P4 – Farbe [ENTSCHEIDEN – präzisiert 11.10.]

**Regel (verbindlich):**
1. **Überwasserfarbe (`farbe`):** pro Instanz vorgebbar (Hex-String oder RGB-Tripel),
   Default hellgrau #c9c9c9.
2. **Unterwasserfarbe (`farbe_unter_wasser`):** OPTIONAL pro Instanz vorgebbar.
3. **Default-Verhalten:** Wird keine Unterwasserfarbe angegeben, ist die
   Unterwasserfärbung automatisch **um eine gut sichtbare Nuance heller** als die
   Überwasserfarbe (Aufhellen im HSL-Raum um ΔL = +0,25 – Lightness +25 %,
   Sättigung unverändert; Wert vom Nutzer bestätigt, gepflegt in
   `konfiguration.json`; deterministisch, per Test festgenagelt).
4. Muster/Texturen werden bewusst NICHT vorgesehen – sie lenken vom Ziel ab:
   die Darstellung der Kräfte und Momente. Spätere Ergänzung bleibt möglich.

**Konsequenz für die Brücke:** Die Klasse liefert ZWEI Farben (über/unter Wasser);
die Brücke färbt die beiden Teil-Meshes aus schneide_am_wasser damit ein. Die
bisher fest verdrahtete Blau/Rot-Logik wird konfigurierbar mit sinnvollem Default.

**Akzeptanzkriterien P4:**
- AK-P4a: farbe gesetzt, farbe_unter_wasser nicht → Unterwasserfarbe = aufgehellt
  (deterministisch, Test mit Referenzfarbwerten).
- AK-P4b: beide gesetzt → beide exakt verwendet.
- AK-P4c: Default hellgrau #c9c9c9 für alle Instanzen ohne Farbangabe.

---

## P5 – Overlay-Layer, Drehachsen & Zwei-Modi-Physik [ENTSCHEIDEN 11.10. – P5c als Zielbild, Umsetzung später]

**P5a – Layer-System [ENTSCHEIDEN]:**
- Drehachsen, Kraftdarstellungen und Momentdarstellungen werden jeweils einem
  **Layer** zugeordnet; Layer lassen sich in der Darstellung ein-/ausschalten.
- **Architektur-Regel (kritische Präzisierung):** Der KÖRPER kennt keine Layer.
  Trennung der Verantwortlichkeiten:
  | Ebene | Speichert/Berechnet | Beispiel |
  |---|---|---|
  | Körper | Eigenschaften (Wahrheit) | Geometrie, Masse, r_S, I_S, Farben, Achsrichtungen |
  | Szene/Layer-Registry | Sichtbarkeit pro Layer | layer["kraefte"] = an/aus |
  | Renderer | Projektion on-the-fly | zeichnet Pfeile/Achsen je nach Layer-Status |
- Layer sind global (nicht pro Körper); ein eingeschalteter Kraft-Layer zeigt
  die Kraftpfeile ALLER Körper gleichzeitig.
- Merksatz: **Körper = Wahrheit, Renderer = Projektion der Wahrheit.**
  Berechnete Ansichten (Pfeil-Längen, Linien-Geometrien) werden NIEMALS im
  Körper gespeichert – sie entstehen pro Frame neu aus Pose + Eigenschaften.

**P5b – Was ist ohne Physik darstellbar? [ENTSCHEIDEN]:**
- **Massenschwerpunkt r_S:** JA – rein aus Geometrie+Masse berechenbar (P1).
  Overlay: Markierung/Punkt am Schwerpunkt (Layer "schwerpunkt").
- **Hauptträgheitsachsen:** JA – die drei Eigenrichtungen des Trägheitstensors
  I_S sind reine lineare Algebra aus Form+Dichte, KEINE Dynamik nötig.
  Overlay: drei Linien durch r_S (Layer "hauptachsen").
  (Bei symmetrischen Körpern fallen sie nahezu mit den Konstruktionsachsen
  zusammen; bei asymmetrischen Rümpfen weichen sie sichtbar ab.)
- **Momentane Drehachse der Bewegung:** NEIN – braucht die Dynamik (V4).
- **Kräfte und Momente:** NEIN in V3 – die kinematische Pose ist vorgeschrieben,
  nicht im Gleichgewicht; Pfeile würden Physik suggerieren, die nicht rechnet.
  (Technisch wäre der Gewichts-Pfeil m·g am r_S schon jetzt möglich – bewusst
  ZURÜCKGESTELLT auf V4, um Ehrlichkeit der Darstellung zu wahren.)

**P5c – Zwei-Modi-Physik [ZIELBILD FESTGELEGT 11.10., Umsetzung später]:**
Beschluss des Nutzers: Die Physik wird JETZT nicht umgesetzt – aber das
Zielbild ist verbindlich und die Architektur muss es von Anfang an tragen.

Am Ende gibt es ZWEI Darstellungsarten:
1. **Echtzeitmodus** – zeitgetreues Erlebnis: über Zeitschritte gerechnet
   (Integration, Δt = 1/240 s, interaktiv).
2. **Solvermodus** – statisch und verständlich: ein Solver ermittelt die
   stabilen Werte (Gleichgewicht: ΣF = 0, ΣM = 0) und stellt sie dar
   (Endpose im Fenster + Zahlen im Status-Panel: Tiefgang, Krängung,
   V_verdrängt, Auftrieb = Gewicht).

Architektur-Regel (damit später nichts neu diskutiert werden muss):
- EINE Kraft-/Momentenfunktion kraefte_und_momente(pose); beide Modi sind
  nur zwei TREIBER darüber (Integration vs. Wurzelfindung). Nie zwei
  Kraftmodelle pflegen.
- Der Solver nutzt wasser_schnitt.schneide_am_wasser für V_sub und den
  Auftriebsansatzpunkt B (Infrastruktur existiert bereits).
- Umsetzungsreihenfolge bei Wiederaufnahme: Solver zuerst (deterministisch,
  exakt testbar), dann Echtzeit; Freiheitsgrade zuerst Tauchgang + Krängung,
  Gieren später.
- Zugang vorerst: Taste p setzt die Solver-Ergebnispose; die kinematische
  Demo läuft unverändert weiter. Der echte Echtzeitmodus kommt mit der
  Physik selbst.

---

## P6 – Konfigurator [GEPLANT – nur gemerkt, NICHT Teil der aktuellen Umsetzung]

Idee des Nutzers (11.10.2026): Später ein **Konfigurator**, über den neue Modelle
und Konfigurationen geändert werden können – Selbstbedienung statt Entwickler-
Anfrage. Status: nur als Absicht dokumentiert. Kein Design, kein Zeitplan.
Er baut später auf dieser Körper-Klasse und dem Szenen-/Parameterobjekt auf
(deshalb saubere API als Fundament). Vorläufer: die Arbeitsdatei
`konfiguration.json` (Spec-Abschnitt J) – seine Oberfläche wird genau diese
Struktur lesen und schreiben.

---

## P7 – Grafik-Optimierung „schickes Aussehen" [PRIORISIERT 11.10.: zuerst K1 + K2 + K5]

Ziel: Das 3D-Fenster soll hochwertig wirken (Präsentationsqualität), ohne die
physikalische Ehrlichkeit zu gefährden (keine Deko, die Daten vortäuscht).
Ausgangsbasis: Original-vista.py-Look (Blaues Becken, Grau-Rahmen, Weißer Grund).

### Vorschlagskatalog (in Kategorien, Priorisierung durch Nutzer)

**K1 Licht & Atmosphäre (höchster Hebel, geringes Risiko):**
- Weiches Key-/Fill-/Rim-Lighting statt Einzellicht; leicht warmes Key-Licht,
  kühles Fill (klassische Studio-Anordnung)
- Ambient Occlusion (SSAO, PyVista hat es eingebaut) – gibt Tiefe an Kanten
  und Spalten, der größte einzelne „Schick"-Hebel
- Dezenter Hintergrundverlauf (Himmelblau → Dunstweiß) statt reinem Weiß

**K2 Wasser (mittlerer Aufwand, großer Effekt):**
- Wasserfläche mit Fresnel-artiger Glanzreflexion + leichte Transparenz
  (aktuell schon vorhanden, aber flach); evtl. sanfte Normal-Map-Störung
  (rein optisch, KEINE Physik – dokumentiert als Deko!)
- Unterwasser-„Tiefe": Farbverlauf nach unten (schon in vista.py angelegt,
  könnte verstärkt/kalibriert werden)

**K3 Materialien der Körper:**
- Specular/Glanzgrade pro Material (Stahl glänzt, Holz matt) – knüpft an die
  Materialtabelle aus P3 an (Deko-Konvention, dokumentiert)
- Optional: leichte Kantenbetonung (Edge-Rendering) für technische Lesbarkeit

**K4 Overlay-Qualität (wichtig für spätere Kräfte/Momente):**
- Pfeile/Linien mit Tube-Rendering statt dünner Linien (besser sichtbar,
  professioneller)
- Konsistente Farbkonvention für Overlays (z. B. Kräfte = Rot-Töne,
  Achsen = Gelb/Cyan, Schwerpunkt = Weißer Marker)

**K5 Komfort/Kamera:**
- Voreingestellte Kamerapositionen (Bugansicht, Heckansicht, 3/4-Standard,
  Draufsicht) per Tastendruck
- Sanftes Kamera-Einfangen (Interpolation) beim Wechsel

### Grenzen (unstrittig):
- Keine Wellenbewegung (Spec V3: statisches Wasser) – alles Optische bleibt
  statisch, außer Körperbewegung
- Keine Partikel/Effekte, die physikalische Vorgänge suggerieren
- Performance-Ziel: weiterhin 60 FPS mit 4+ Körpern

Status: PRIORISIERT (Beschluss 11.10.): Zuerst K1 + K2 + K5 (Licht/Atmosphäre,
Wasser-Glanz, Kamera-Presets) – reine Renderer-Einstellungen, kein Umbau.
K3 (Materialglanz) und K4 (Tube-Overlays) folgen, sobald die Overlays aus P5
umgesetzt sind. Umsetzung: als eigener Meilenstein NACH der Körper-Klasse,
additiv in der Brücke; vista.py bleibt unangetastet (Einstellungen werden
von der Brücke gesetzt, nicht in vista.py geändert).

---

## J – Eingabedatei `konfiguration.json` [ENTSCHEIDEN 11.10., präzisiert: Template-Muster]

**Zweck:** Bis der Konfigurator (P6) existiert sind ALLE veränderbaren Werte in
einer einzigen JSON-Eingabedatei zusammengefasst. Der Nutzer kann Werte dort
selbst eintragen oder sie erzeugen lassen. Die Datei ist die EINZIGE Quelle –
im Code gibt es keine stillen Duplikate der Tabellen.

**Template-Muster (Beschluss 11.10.):**
- Im Repo liegt die VORLAGE: `doc/configuration_template.json`
  (Werkseinstellungen, versioniert, unverändert in Gebrauch).
- Beim Einrichten des Projekts wird die Vorlage EINMAL explizit nach
  `konfiguration.json` (Projekt-Root bzw. Laufzeitpfad) kopiert – das ist die
  ARBEITSDATEI, in der der Nutzer experimentiert, ohne die Vorlage zu zerstören.
- Der Loader liest AUSSCHLIESSLICH `konfiguration.json`. Fehlt sie, gibt es
  einen klaren Fehler mit Hinweis: „Bitte aus doc/configuration_template.json
  erzeugen (kopieren)." KEIN stiller Fallback auf im Code versteckte Werte.
- Der Konfigurator (P6) schreibt später die Arbeitsdatei; die Vorlage bleibt
  Referenz der Werkseinstellungen.

**Inhalt (Abschnitte):**
- `materialien`: Name → Dichte in kg/m³ (Holz, GfK, Stahl, Blei, Aluminium)
- `wasser`: Dichten in kg/m³ (Süßwasser, Salzwasser, Totes-Meer-Wasser,
  Quecksilber) + Standard-Auswahl (aktuell Süßwasser)
- `boot.teile`: REKURSIVE Struktur (gemäß P2). Ein Eintrag MIT `"teile"` ist
  eine reine GRUPPE ohne eigene Werte (keine Masse/Dichte/Material/
  Flächenmasse, keine Farbe) – seine Werte ergeben sich ausschließlich aus
  den Teilen. Ein Eintrag OHNE `"teile"` ist ein BLATT und muss GENAU EINE
  Massengröße tragen (Genau-eins-Regel, P3). Aktuelle Struktur:
  rumpf (GfK) · ruder (GfK) · kielsystem [kiel (Stahl), bulb (Blei)] ·
  rigg [mast (Aluminium), boom (Aluminium), großsegel (0,5 kg/m²),
  fock (0,5 kg/m²)]
- Geometrie-Zuordnung: Der Teilename wird per Konvention auf die OBJ-Datei
  `modelle/<name>.obj` abgebildet (alle 8 Boot-Teile folgen dieser Konvention).
- rel_Posen: Die Vorlage gibt KEINE rel_Posen an – alle Teile teilen den
  gemeinsamen Modellursprung, ihre rel_Pose ist damit implizit die Identität
  (Angabe gemäß P2 Punkt 4 nur, wenn abweichend nötig).
- Farben: In der Vorlage sind keine Farbangaben gesetzt – für alle Boot-Teile
  gilt der Default gemäß P4 (#c9c9c9, Unterwasser automatisch heller).
- Gruppen-Erkennung: ausschließlich über das Vorhandensein von `"teile"` –
  es gibt KEIN zusätzliches Typ-Feld (die Verschachtelung selbst ist die
  eine Wahrheit; ein Typ-Feld könnte der Struktur widersprechen).
- `darstellung`: ΔL der Unterwasser-Aufhellung (0,25) und Default-Farbe

**Zuordnungstabelle Spec-Parameter ↔ JSON-Schlüssel** (die JSON-Schlüssel
tragen Einheiten im Namen, die Spec-Parameter nicht):

| Spec-Parameter (P3/P4) | JSON-Schlüssel | JSON-Pfad |
|---|---|---|
| `material` (Name) | `<Materialname>` → Dichte | `materialien` |
| `dichte` (direkte Zahl) | – (direkte Zahl im Körper-Konstruktor) | – |
| `flaechenmasse` | `flaechenmasse_kg_pro_m2` | `boot.teile[]` |
| Wasser-Auswahl | `standard` (Name) bzw. direkte Zahl | `wasser.standard`; Namensauflösung in `wasser.dichten_kg_pro_m3` |
| ΔL der Aufhellung | `delta_helligkeit_unterwasser` | `darstellung` |
| `farbe` (Default) | `farbe_standard` | `darstellung` |

**Regeln:**
- Fehlender oder doppelter Schlüssel → Validierungsfehler beim Laden
  (kein stiller Fallback auf im Code versteckte Werte).
  Implementierungshinweis: Pythons `json.load` akzeptiert doppelte Schlüssel
  stillschweigend (letzter gewinnt). Die Doppelschlüssel-Erkennung ist daher
  NUR mit `object_pairs_hook` (Prüfung auf doppelte Keys je Objekt) erfüllbar –
  dieser Check ist Pflichtbestandteil des Loaders.
- Direkte Zahlen bleiben überall zulässig (Dichte statt Materialname usw.);
  die Datei definiert nur die benannten Defaults.
- Die Validierung läuft REKURSIV über die gesamte teile-Baumstruktur:
  Gruppe mit Massen-Schlüssel → Fehler; Blatt mit keiner oder mehr als einer Massengröße →
  Fehler; leere Gruppe → Fehler.
- Die Arbeitsdatei ist der Vorläufer des Konfigurators (P6).

---

## R. Regeln (unstrittig)

- R1 Überlappungen: exakte Erkennung unverhältnismäßig; dokumentierte
  Verantwortung des Nutzers + optionaler Stichproben-Check + Plausibilität
  „Σ Teilvolumina ≈ Gesamtvolumen".
- R2 Einsprachige native API: die öffentliche API ist durchgängig deutsch,
  KEINE Alias-Doppelung mehr (alte Fassaden bleiben unangetastet, werden nicht
  erweitert).
- R3 Umsetzung in vier Schritten (Reihenfolge gemäß P5c/P7-Beschlüssen):
  (1) Klasse + Massenintegration + Umstellung der vier bekannten Körper,
  Regression grün; (2) Grafik-Optimierung K1+K2+K5 als eigener Meilenstein;
  (3) Overlays (r_S, Hauptachsen) als eigener Schritt; (4) Materialglanz K3
  und Tube-Overlays K4 (gemäß P7 erst NACH Schritt 3).
- R4 Geplante Dateien (alle neu, Altbestand unberührt):
  core/koerper.py (Klasse), core/massen.py (Divergenzsatz, r_S, Tensor),
  Fabrik-Funktionen, tests/test_koerper.py, konfiguration.json (ARBEITSDATEI,
  einmalig erzeugt aus der Vorlage doc/configuration_template.json –
  siehe Spec-Abschnitt J).
- **R5 (DAUERHAFTE ANWEISUNG des Nutzers, 11.10.2026): Kritische Begleitung ist
  Pflicht.** Ideen werden stets kritisch geprüft und herausgefordert – Ziel ist
  gemeinsam das Optimum, nicht schnelle Zustimmung. Diese Regel gilt für die
  gesamte weitere Zusammenarbeit.
- R6 Einheitenregel: Intern wird durchgängig in ISO-SI-Einheiten gerechnet
  (Längen m · Massen kg · Dichten kg/m³ · Flächenmassen kg/m² · Kräfte N ·
  Momente N·m · Zeiten s · Winkel rad intern). Umrechnungen (z. B. Knoten,
  Grad) erfolgen AUSSCHLIESSLICH in der Darstellungsschicht – nie in der
  Eingabedatei, nie im Rechenkern. Die Eingabedatei enthält ausschließlich
  SI-Werte; ihre `_einheit`-Felder dokumentieren die Leseeinheit je Block.
