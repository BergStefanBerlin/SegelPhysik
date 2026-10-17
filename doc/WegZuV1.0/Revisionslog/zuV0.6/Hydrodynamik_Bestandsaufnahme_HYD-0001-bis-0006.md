# Hydrodynamik-Bestandsaufnahme HYD-0001 bis HYD-0006

**Stand:** 17.10.2026<br>
**Geprüfte Revision:** `f928451` (`main`, vor den Codeänderungen dieser Bestandsaufnahme)<br>
**Zweck:** Reproduzierbare Bestandsaufnahme und dokumentierte Gates; keine
Freigabe für neue Produktivkräfte oder Yachtmesh-Änderungen.

## 1. Baseline und Erhalt bestehender Modelle

Der Prüfstand war `main` bei `f928451`. Vorhandene unversionierte Dateien
wurden nicht verändert. Der produktive Modellpaketloader und die aktuellen
Hydrostatik-, Auftriebs-, Kraftmodell-, Dynamik- und GUI-Regressionen wurden
ausgeführt:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q tests\test_kraftmodell.py tests\test_modell_lader.py tests\test_migriere_modellpaket.py tests\test_manifest_baum.py tests\test_auftrieb.py tests\test_dynamik_6dof.py tests\test_gui_laufzeit_edit.py
```

Ergebnis: **104 bestanden**, keine fehlgeschlagenen oder übersprungenen Tests.
Die vollständige Suite war unmittelbar vor dieser Arbeitsserie ebenfalls
ausgeführt worden: **570 bestanden, 1 übersprungen**. Ein neuer
Hydrodynamik-Kraftbeitrag war in dieser Baseline nicht aktiv.

## 2. Datenfluss- und Integrationsbefund

- `modell.json` wird strikt über `lade_modellmanifest` geprüft; `lade_modellpaket`
  löst die Geometrie über den kanonischen Meshloader auf, validiert die
  Topologie und liefert unveränderliche SI-Meshes. Der Loader schreibt keine
  Dateien und erzeugt keine dauerhaften Metadaten. Geometriemetadaten werden
  nun ausschließlich über das explizite Werkzeug
  `werkzeuge/erzeuge_hydrodynamik_metadaten.py` erzeugt; diese Trennung bleibt
  erhalten.
- `fabriken.baue_modellpaket` erstellt aus Manifest und Meshes den
  Laufzeit-Körperverband und übernimmt dabei die Modellposen. `frames.Pose`
  stellt benannte Translationen/Rotationen und deren Komposition bereit;
  `koerper.Koerper.setze_rel_pose` ändert die relative Pose eines
  Verbandsknotens. Diese vorhandene Mechanik setzt aber keine im
  `yacht1`-Manifest fehlende Ruderachse oder Grenzwinkel fest.
- Die vorhandene Körperstruktur und Gelenkpose dienen derzeit der bestehenden
  Modell-/GUI-Semantik; sie erzeugen nicht automatisch hydrodynamische
  Einzelkräfte.
- `Kraftmodell` nimmt linearen/quadratischen Widerstand, Fluidtranslation,
  Fluidwinkelgeschwindigkeit und diagonale Added Mass entgegen. Beiträge
  werden als `Kraftbeitrag`/`Wrench` geführt und auf den vereinbarten
  Bezugspunkt aggregiert. Es gibt noch keinen geometrieabhängigen
  Hydrodynamikbeitrag und keine automatisch erzeugte Yacht-Kennlinie.
- Hydrostatik/Verdrängung und bestehende Added-Mass-/Widerstandsbeiträge
  bleiben unangetastet. Ein neues Modell darf denselben Widerstand oder
  dieselbe Trägheitswirkung nicht zusätzlich doppelt ansetzen.
- Das Yachtmanifest enthält keine Knoten-ID `schwert`; das Kielsystem hat
  getrennte Blätter `kiel` und `bulb`.

**Baseline-Prüfsummen** (Dateibytes, SHA-256):

| Datei | SHA-256 |
|---|---|
| `konfigurationen/physik.json` | `6a94bcff76fc67c5c8d04baa09ff4c2721f57352a432872341c00ed8438a7fc3` |
| `konfigurationen/koerper.json` | `756935244f7da4ac47a872f87cf3628756ebbb2feffb1f676c4e8693e28cfc3f` |
| `konfigurationen/settings.json` | `80ae7758afdc87d2337dc0d2f83df74a556d46ba5bd15e900f46331cdc283f79` |
| `segelphysik/modelle/yacht1/modell.json` | `4257bf9e93fe4c4bd63366ec2a085a754c32ff80b94a645dfbe44732d3e8dc58` |

Die bestehende Phase-3-Golden-Datei ist
[`Inventar_Phase3.json`](../zuV0.5/Inventar_Phase3.json); ihr Inhalt wird
durch `test_bestandsmodelle_stimmen_mit_phase3_goldenwerten_ueberein` in
`tests/test_modell_lader.py` geprüft. Eine eigene, validierte
Hydrodynamik-Goldenreferenz für die Yacht existiert nicht.

## 3. Kanonisches Geometrieinventar

Die Maße wurden über `lade_modellpaket` und die bereits validierten Meshes
ermittelt. OBJ-Werte werden mit `obj_zu_m = 0,25` und folgender
rechtshändiger Achsenmatrix in das Blatt-/SI-Frame abgebildet:

```text
[[0, 0, 1],
 [1, 0, 0],
 [0, 1, 0]]
```

SHA-256 des Quellmanifests:<br>
`4257bf9e93fe4c4bd63366ec2a085a754c32ff80b94a645dfbe44732d3e8dc58`

| Teil | Bounding-Box-Ausdehnung (m) | Dreiecke | Fläche (m²) | Geschlossen / Volumen (m³) | Quell-OBJ-SHA-256 |
|---|---:|---:|---:|---|---|
| Rumpf | 4,225 × 1,2648155 × 1,1374335 | 3072 | 14,240168764 | Ja / 3,112343422095 | `5a2d8873746552c18d20ac5a46ebf9d4d31486d658b9a66fc487841457e1fdbd` |
| Ruder | 0,2625 × 0,0275 × 0,424575 | 96 | 0,205962452 | Ja / 0,002360179946 | `c7771fb72834b6dff6069c6826988495e09ffbe116d3edee43877cf6380020ff` |
| Kiel | 1,1 × 0,075 × 0,385625 | 184 | 0,939633428 | Ja / 0,022734755729 | `355d65a511b5d6603891d85379edfb614e275cc381e172b5292bc5fa459db8b9` |
| Bulb | 0,575 × 0,175 × 0,208984545 | 758 | 0,302825634 | Ja / 0,010575765 | `282294f26b4e01e49e0d9b42791f2ce9ada0d7e9bee6300487f4b24fe6b3d778` |

Die Meshes `rumpf`, `ruder`, `kiel` und `bulb` haben jeweils null
Randkanten; der Loader hat sie ohne Änderung akzeptiert. Flächen sind
geometrische Dreiecksflächen, keine automatisch freigegebenen
hydrodynamischen Bezugsflächen. Volumen dient hier nur als Geometriemesswert.

### Klassifikation und Grenzen

- **Rumpf:** geschlossenes Verdrängermesh. Keine Rumpf-Lift- oder
  Gleitfahrtberechnung aus dieser Vermessung ableiten.
- **Kiel:** schlankes, dünnes Anbauteil; die Bounding-Box beweist kein
  Profil. Profilsektionen und deren belastbare Vorderkante/Sehne sind nicht
  als Eingabedaten im Manifest hinterlegt. Bis zu einer nachvollziehbaren
  Sektionsermittlung als **Profil unbestätigt / unzureichend beschrieben**
  behandeln.
- **Ruder:** 50 Punkte, 96 Dreiecke und nur 0,0275 m Dicke in der dünnen
  Bounding-Box-Richtung; die bekannte plattige Erscheinung ist damit
  plausibel, aber weder ein Profilnachweis noch eine hydrodynamische
  Bezugsfläche. **Weder `pose` noch `gelenk` sind für das Ruder im
  Manifest definiert.** Drehachse, Drehpunkt, positives Vorzeichen und
  zulässige Winkelgrenzen können daher aus dem Modellvertrag nicht abgeleitet
  werden.
- **Schwert:** kein eigenständiger Manifestknoten.
- Keine Meshgröße oder sichtbare Proportion quantifiziert, ob das Ruder
  „zu klein“ ist. Für eine Größenentscheidung fehlen Ruderkinematik,
  Betriebsfälle und validierte Vergleichsdaten.

## 4. Quellenprüfung und Modellfreigabe

- Die [ITTC Resistance Test Procedure](https://ittc.info/media/11780/75-02-02-01.pdf)
  beschreibt einen methodischen Widerstandstest und dessen Mess-/
  Auswertungsrahmen. Sie ist keine universelle Quelle für einen
  Gesamtwiderstandsbeiwert dieser Yacht; eine Reibungsline allein deckt den
  residuellen/Formwiderstand nicht ab.
- Die [TU-Delft-Arbeit „Keel-Rudder Interaction on a Sailing Yacht“](https://research.tudelft.nl/en/publications/keel-rudder-interaction-on-a-sailing-yacht/)
  bibliografiert eine Konferenzarbeit von Keuning, Katgert und Vermeulen
  (Hiswa 2006). Die [TU-Delft-Repositoriumsarbeit zur
  Ruderstall-Asymmetrie](https://repository.tudelft.nl/record/uuid:1be75bf7-04b2-4089-95af-95ac4031e034)
  beschreibt Schleppversuche und RANS-CFD. Ihr Abstract nennt Abweichungen
  der positiven Stallwinkel zwischen Versuchssätzen, unerklärte negative
  Widerstandswerte aus einem Versuchsaufbau sowie Einflüsse von Kiel und
  Rumpf auf den Ruderstall. Das belegt gerade, dass isolierte
  2D-Polaren und beliebige Zahlen nicht ohne Geometrie- und
  Versuchsbedingungen auf diese Yacht übertragbar sind. Ein passender,
  vollständiger Datensatz mit Werten und Unsicherheiten für `yacht1` wurde
  nicht nachgewiesen.
- Der [MIT XFOIL 6.9 User Primer](https://web.mit.edu/drela/Public/web/xfoil/xfoil_doc.txt)
  beschreibt ein isoliertes 2D-Profilwerkzeug. Das allein validiert weder
  die unbekannten Yachtprofilsektionen noch endliche Spannweite,
  Kiel-/Rumpf-/Ruderinteraktion oder das Verhalten im Stall.

**Ergebnis HYD-0004:** keine belastbar übertragbaren Yachtkoeffizienten
freigegeben. Ein getrennt gekennzeichneter Näherungszweig benötigt eine
ausdrückliche Festlegung von Gleichungen, Eingangsbereich, Unsicherheit und
Validierungsstatus. Die Untersuchung wurde nicht als Codefreigabe behandelt.

**Ergebnis HYD-0005:** der Testvertrag ist dokumentiert, aber ein
ausführbarer Rudermanövertest bleibt durch fehlende Kinematikdaten gesperrt.
Es wurden kein Gelenk, keine Ruderwinkel und keine Geschwindigkeitswerte
erfunden. Siehe [BL22 und BL23](../../../Backlog/Backlog_v1.md).

## 5. Abnahme und verbleibende Gates

| Arbeitspunkt | Status | Nachweis / Blocker |
|---|---|---|
| HYD-0001 | Erledigt | Branch/Revision, Arbeitsbaum und Testbaseline dokumentiert; Nutzermeshes unverändert. |
| HYD-0002 | Bestandsaufnahme erledigt | Loader-/Kraft-/Frame-Verträge und fehlende geometrieabhängige Kräfte festgestellt; vollständiger dynamischer Teilbeitrags- und GUI-Pfad ist noch nicht integriert. |
| HYD-0003 | Inventar erledigt, Profilklassifikation teilweise | Geometrie vermessen; kein Ruder-Gelenk, kein eigenes Schwert; Profil-/Querschnittsdaten offen. |
| HYD-0004 | Blockiert | Kein passender quantitativer Yacht-Referenzdatensatz und keine fachlich freigegebene Näherungsparameterliste. |
| HYD-0005 | Blockiert | Ruderachse/-lage/-Vorzeichen/-Winkelgrenzen und belegter Geschwindigkeitsbereich fehlen. |
| HYD-0006 | Erledigt | `core/hydrodynamik_metadaten.py` und explizites CLI-Werkzeug erzeugen ein hashgebundenes Sidecar ohne Änderung am Loader; sieben gezielte Tests bestehen. Für `yacht1` wurde das Sidecar erzeugt und mit `--pruefen` verifiziert. |

### Implementierungs- und Abschlussprüfung

Die Metadatenimplementierung wurde nach der Baseline separat verifiziert:

| Prüfung | Ergebnis |
|---|---|
| `tests/test_hydrodynamik_metadaten.py` | 7 bestanden |
| Vollständige Testsuite | 577 bestanden, 1 übersprungen |
| `werkzeuge/erzeuge_hydrodynamik_metadaten.py yacht1 --pruefen` | bestanden; Sidecar ist aktuell |
| `git diff --check` | bestanden |

SHA-256 des erzeugten
[`yacht1`-Metadatensidecars](../../../../segelphysik/modelle/yacht1/hydrodynamik/geometrie_metadaten.json):
`FA596C6AC8969505158A50824999C0758E5646027907F66FDEE24BB5EF8D0A9F`.

Nach der separaten Implementierung des nicht validierten Rudernäherungszweigs
wurden die gezielten Regressionen und die vollständige Suite erneut
ausgeführt:

| Prüfung | Ergebnis |
|---|---|
| `tests/test_hydrodynamik_ruder_naeherung.py` | 17 bestanden |
| Vollständige Testsuite | 594 bestanden, 1 übersprungen |
| `werkzeuge/erzeuge_hydrodynamik_metadaten.py yacht1 --pruefen` | bestanden; Sidecar ist aktuell |
| Produktionsmanifest und `ruder.obj` | unverändert |
| `git diff --check` | bestanden |

Der sichtbare zehnminütige Baseline-Lauf (`yacht1`, `exakt_union`, Windows-
Qt, Python 3.14.8, 30 s Warm-up; Schwerpunkt-, Hauptachsen-, Kraft- und
Moment-Layer aktiv; Prozessworker) ist **nicht bestanden**:

| Messgröße | Ergebnis |
|---|---:|
| Tatsächlich präsentierte Bildrate | 12,97 FPS |
| Frameabstand P95 / Maximum | 205,186 ms / 219,441 ms |
| Eingabelatenz bis präsentierter Frame | 7,852 ms; 599/599 Eingaben beantwortet |
| Simulationsdurchsatz | 0,00525 Simulationssekunden je Wandsekunde |
| Berechnete Simulationszeit nach 600 s Wandzeit | 3,152 s |
| Automatische Überlastpause | Ja |
| Rückstand P95 / Maximum | 3,651 s / 3,651 s |
| Laufzeitfehler | Keine |

Die Eingabelatenz-Messung war gültig, aber sie ändert nichts am Fehlschlag
der Performance-Gates. Der Lauf bestätigt den bereits bekannten Live-
Engpass; er erfolgte ohne neuen Hydrodynamik-Kraftbeitrag. Messbedingungen
und Gates sind in BL3/BL4 im [Backlog](../../../Backlog/Backlog_v1.md)
nachgetragen.

Die Regressionen decken deterministische Messung, fehlende Seiteneffekte,
atomare No-Overwrite-Veröffentlichung, Erkennung geänderter Manifest- und
OBJ-Eingaben sowie den weiterhin schreibfreien Modellpaketloader ab. Das
Sidecar enthält keine behauptete Profilklassifikation oder Hydrodynamik-
Koeffizienten.

Nach ausdrücklicher Nutzerfreigabe wurde zusätzlich ein isolierter
Kleinwinkel-Rudernäherungszweig erstellt; siehe
[Ruderkraft-Näherungsmodell](./Hydrodynamik_Ruder_Naeherungsmodell_Vorschlag.md).
Er bleibt außerhalb des Produktivsolvers und hat den Status
`berechnete_naeherung`. Die Tests dazu stehen in
`tests/test_hydrodynamik_ruder_naeherung.py`. Das schließt weder HYD-0004/0005
noch Spec0065 ab: Yacht-Referenzdaten und reale Ruderkinematik fehlen,
Rumpf-/Kielinteraktion und mechanische Grenzen sind nicht validiert.
HYD-0007–0009 sowie HYD-0011–0016 bleiben offen/blockiert; HYD-0010 ist
teilweise umgesetzt und getestet.

Die [Spezifikation](./Spezifikation_Hydrodynamik_v1.0.md) und
[Umsetzungsanleitung](./Umsetzungsanleitung_Hydrodynamik_v1.0.md) bleiben
maßgeblich. Kein fehlgeschlagenes oder fehlendes Gate wurde als bestanden
gewertet.
