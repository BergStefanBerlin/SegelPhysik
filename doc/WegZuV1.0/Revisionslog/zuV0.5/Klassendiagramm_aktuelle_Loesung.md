# Klassendiagramm der aktuellen Lösung

Das Diagramm bildet vorhandene konkrete Codebausteine ab, nicht das noch
nicht implementierte Zielmodell. `<<Funktion>>` kennzeichnet zustandslose
Funktionen oder Fabriken; gestrichelte Pfeile zeigen Nutzung/Erzeugung statt
Vererbung.

```mermaid
classDiagram
direction LR

namespace Konfiguration_und_Modell {
    class Konfiguration {
        +ordner
        +summenkoerper
        +materialien_blocks
        +wasser_dichte()
    }
    class Einstellungen {
        +pfad
        +vorlage
        +get()
        +setzen()
    }
    class ModellManifest {
        +schema_version
        +id
        +paketwurzel
        +koerper
    }
    class ModellKnoten {
        +id
        +name
        +teile
        +rolle
        +pose
        +gelenk
    }
    class Modellpaket {
        +manifest
        +meshes
    }
    class Mesh {
        +punkte_si
        +dreiecke
        +frame
        +metadaten
    }
    class KonfigLader {
        <<Funktion>>
        +lade_konfig(ordner)
        +lade_physik(ordner)
    }
    class ModellLoader {
        <<Funktion>>
        +lade_modellmanifest(wurzel, materialien)
        +lade_modellpaket(wurzel, materialien)
        +lade_modellkatalog(wurzel, materialien)
    }
    class Fabriken {
        <<Funktion>>
        +baue_summenkoerper(konfig, name)
        +baue_modellpaket(konfig, wurzel)
    }
}

namespace Laufzeitkoerper_und_Zustand {
    class Koerper {
        +masse
        +traegheitstensor
        +teile
        +zustand
        +snapshot()
        +gelenkwinkel_setzen(id, winkel)
    }
    class KoerperSnapshot {
        +masse
        +traegheitstensor
        +blatt_meshes
        +zustand
        +version
        +gelenkzustaende
    }
    class Zustand6DOF {
        +position
        +quaternion
        +geschwindigkeit_koerper
        +winkelgeschwindigkeit_koerper
    }
    class Pose {
        +ziel_frame
        +quell_frame
        +translation_m
        +rotation_quaternion_wxyz
        +komponieren()
        +invers()
    }
}

namespace Kraft_und_Simulation {
    class Kraftmodell {
        +hydrostatik
        +linear_widerstand
        +fluidgeschwindigkeit
        +fremdkraft_setzen()
        +mit_hydrostatik()
    }
    class Kraftbeitrag {
        +name
        +wrench
    }
    class Wrench {
        +frame
        +bezugspunkt_m
        +kraft_N
        +moment_Nm
        +auf_bezugspunkt()
    }
    class KraftErgebnis {
        +hydrostatik
        +F_gesamt
        +M_gesamt
        +beitraege
        +gesamt_wrench
    }
    class StatischerSolver {
        <<Funktion>>
        +loese_robust(kraftfunktion, masse)
    }
    class Dynamik6DOF {
        <<Funktion>>
        +schritt(zustand, kraftfunktion, masse, traegheit, dt, g)
    }
    class Hydrostatik {
        <<Funktion>>
        +baue_kraftfunktion(snapshot)
        +baue_kraftfunktion_6dof(snapshot)
    }
}

namespace GUI_und_Darstellung {
    class HauptFenster {
        +_laufzeit_objekte_aktualisieren()
        +_statische_simulation_ausfuehren()
        +_echtzeit_starten()
        +baum_setzen()
    }
    class _StatischeAufgabe {
        +generation
        +koerper_snapshot
        +run()
    }
    class _EchtzeitAufgabe {
        +generation
        +zustand
        +run()
    }
    class GrafikBruecke {
        +koerper_objekt_setzen()
        +physik_pose_6dof_setzen()
        +gelenkwinkel_setzen()
        +kraefte_daten_setzen()
    }
}

KonfigLader ..> Konfiguration : erstellt
ModellLoader ..> ModellManifest : validiert
ModellManifest *-- ModellKnoten : Struktur
Modellpaket *-- Mesh : Geometrie
Modellpaket --> ModellManifest
ModellLoader ..> Mesh : importiert und validiert
Fabriken ..> Konfiguration : Material- und Altdaten
Fabriken ..> ModellLoader : Manifest-/Paketpfad
Fabriken ..> Koerper : erstellt
Fabriken ..> Pose : transformiert Basispose
Koerper *-- KoerperSnapshot : erzeugt
Koerper --> Zustand6DOF : autoritativer Zustand
Koerper --> Pose : Basis- und Teilframes
Koerper ..> Mesh : Laufzeitgeometrie
KoerperSnapshot --> Zustand6DOF
KoerperSnapshot --> Mesh

HauptFenster ..> Einstellungen : liest und ändert
HauptFenster ..> Konfiguration : baut Laufzeitkörper
HauptFenster ..> Fabriken : Paket-/Legacy-Auswahl
HauptFenster ..> _StatischeAufgabe : startet
HauptFenster ..> _EchtzeitAufgabe : startet
_StatischeAufgabe --> KoerperSnapshot
_StatischeAufgabe ..> StatischerSolver : löst Gleichgewicht
_EchtzeitAufgabe --> Zustand6DOF
_EchtzeitAufgabe ..> Dynamik6DOF : integriert Zeitschritte
StatischerSolver ..> Hydrostatik : wertet Kandidaten aus
Dynamik6DOF ..> Hydrostatik : Kraftfunktion je Schritt
Hydrostatik ..> Kraftmodell : gemeinsame Beiträge
Kraftmodell ..> Kraftbeitrag : erzeugt Diagnosebeiträge
Kraftbeitrag --> Wrench
Kraftmodell --> KraftErgebnis
HauptFenster ..> GrafikBruecke : reicht Pose und Ergebnisse
GrafikBruecke ..> Koerper : stellt Geometrie dar
GrafikBruecke ..> KraftErgebnis : visualisiert Kräfte/Momente
GrafikBruecke ..> Pose : Gelenkdarstellung
```

## Einordnung

- `koerper.json` und `materialien.json` werden vom Legacy-Konfigurationslader
  eingelesen. Für die Repository-Paketmodelle liefert die Konfiguration
  weiterhin Material- und Umgebungseigenschaften; das Modellmanifest liefert
  die kanonische Baumstruktur und Geometriequellen.
- `Koerper` vereint ein einzelnes Geometrieblatt oder einen strukturierten
  Verband. Der Root hält den aktuellen 6-DOF-Zustand; Teilknoten halten ihre
  Definitionen und optionalen Gelenkwinkel.
- Statische und dynamische Berechnung sind getrennte Abläufe. Sie teilen sich
  Kraftmodell und Darstellung, aber nicht ihren Solver-/Integrationsalgorithmus.
- Ein Ergebnis kehrt nur nach Generations-/Zustandsprüfung in die GUI zurück.
  Kamera- und Anzeigeeinstellungen sind keine physikalischen Zustände.
- Das akzeptierte statische Solverresultat wird aktuell als Ergebnis und
  Darstellungspose gehalten. Erst beim Start der Echtzeit wird daraus ein
  `Zustand6DOF` erstellt und in `Koerper.zustand` gesetzt; die statische
  Übernahme in den autoritativen Körperzustand ist noch nicht abgeschlossen.
- Neue Hydrodynamik-/Aerodynamikklassen sind absichtlich nicht eingezeichnet:
  solche Behandlungen sind noch nicht implementiert.
