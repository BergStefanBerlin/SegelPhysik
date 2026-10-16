# Datenfluss: Körperdatei bis Simulation und Darstellung

Die Grafik zeigt den aktuellen Ablauf inklusive des Repository-Paketpfads und
des auswählbaren Legacy-Rückfalls. Die Bezeichnungen `koerper.json` und
`materialien.json` meinen den bisherigen Konfigurationsvertrag.

```mermaid
flowchart TD
    subgraph EINGABE["1. Dateien und Einstellungen"]
        KOERPER["konfigurationen/koerper.json\nLegacy-Baum, Formen, Materialverweise"]
        MATERIAL["konfigurationen/materialien.json\nMaterialdichten und -farben"]
        PHYSIK["konfigurationen/physik.json\nWasser, Schwerkraft, Widerstand, Integratorparameter"]
        SETTINGS["konfigurationen/settings.json\nPaketfabrik-Schalter und GUI-/Solvereinstellungen"]
        MANIFEST["segelphysik/modelle/<id>/modell.json\nIDs, Baum, Rollen, Geometrien, Posen/Gelenke"]
        OBJS["Modellpaket: OBJ-Dateien\nbzw. parametrisierte Formquellen"]
    end

    subgraph LADEN["2. Laden, prüfen und Körper bauen"]
        KL["Konfigurationslader\nlade_konfig() / lade_physik()"]
        KONFIG["Konfiguration\nMaterialkatalog + Legacy-Daten + Wasser"]
        ML["Modellloader\nSchema, IDs, Referenzen, sichere Pfade"]
        MESH["Mesh-Resolver\nOBJ/Form → unveränderliches SI-Mesh\nTopologie und Selbstschnitt prüfen"]
        ROUTER{"Repository-Paketpfad\naktiviert?"}
        PAKETFAB["Paketfabrik\nbaue_modellpaket()"]
        LEGACYFAB["Legacy-Fabrik\nbaue_summenkoerper()"]
        KOERPER_RT["Koerper (Laufzeit)\nBlatt-Meshes + Massenkennwerte + Baum\nZustand6DOF + Gelenkwinkel"]
        SNAP["KoerperSnapshot\nunveränderliche Worker-Eingabe\nmit Version"]
    end

    subgraph RECHNUNG["3. Zwei getrennte Simulationswege"]
        STATIC["Statische Aufgabe\nKörper-Snapshot + Settings + Physik"]
        SOLVER["Robuster statischer Solver\nprüft z/phi-Kandidaten"]
        DYN["Echtzeit-Aufgabe\nZustand + feste Masse/Trägheit + dt"]
        INTEGRATOR["6-DOF-Schritt\nNewton–Euler-Integration"]
        FORCES["Gemeinsame Kraftauswertung\nHydrostatik + Widerstand + Fremdkraft\n+ Gewicht; Beiträge → Wrench"]
        STAT_RESULT["Solverresultat\nPose, Status, Restkraft/-moment"]
        STAT_GATE{"Solvergeneration aktuell\nund Lösung akzeptiert?"}
        STAT_CACHE["GUI-Solverresultat\n+ statische Darstellungspose\n(noch nicht Koerper.zustand)"]
        DYN_RESULT["Dynamikresultat\nneuer Zustand + Kraftresultat"]
        DYN_GATE{"Auftragsgeneration aktuell\nund Ergebnis gültig?"}
    end

    subgraph ANSICHT["4. GUI und Grafik"]
        GUI["HauptFenster\nBaum, Modus, Einstellungen, Workersteuerung"]
        BRIDGE["GrafikBruecke\nMesh-Actors, Pose und Kraftbild"]
        VIEW["3D-Ansicht + Status\nKörperpose, Gelenkpose, Wasser,\nKraft-/Momentenanzeigen"]
        CAMERA["Kamera / Anzeigeoptionen\nGUI-seitig, nicht Teil der Physik"]
    end

    KOERPER --> KL
    MATERIAL --> KL
    PHYSIK --> KL
    SETTINGS --> GUI
    KL --> KONFIG
    KONFIG --> ROUTER
    MANIFEST --> ML
    OBJS --> MESH
    ML --> MESH
    KONFIG --> ML
    ROUTER -->|ja| PAKETFAB
    ROUTER -->|nein / Rückfall| LEGACYFAB
    ML --> PAKETFAB
    MESH --> PAKETFAB
    KONFIG --> PAKETFAB
    KONFIG --> LEGACYFAB
    PAKETFAB --> KOERPER_RT
    LEGACYFAB --> KOERPER_RT
    KOERPER_RT --> SNAP
    GUI --> STATIC
    GUI --> DYN
    SNAP --> STATIC
    SNAP --> DYN
    STATIC --> SOLVER
    SOLVER --> FORCES
    FORCES --> SOLVER
    DYN --> INTEGRATOR
    INTEGRATOR --> FORCES
    FORCES --> INTEGRATOR
    SOLVER --> STAT_RESULT
    INTEGRATOR --> DYN_RESULT
    STAT_RESULT --> STAT_GATE
    STAT_GATE -->|ja| STAT_CACHE
    STAT_CACHE --> BRIDGE
    STAT_CACHE -. nächste Echtzeit initialisieren .-> DYN
    DYN_RESULT --> DYN_GATE
    DYN_GATE -->|ja: Zustand übernehmen| KOERPER_RT
    DYN_GATE -->|ja: darstellen| BRIDGE
    DYN_GATE -->|nein: verwerfen| GUI
    KOERPER_RT --> BRIDGE
    GUI --> BRIDGE
    BRIDGE --> VIEW
    CAMERA --> VIEW
```

## Was die Pfeile bedeuten

1. Der Konfigurationslader liest Legacy-Modelldaten, Materialien und
   Physikparameter. Für Repository-Modelle sind Manifest und Paketdateien die
   maßgebliche Geometrie- und Baumquelle; Legacy-Konfigurationen bleiben
   Rückfall- und Kompatibilitätspfad.
2. Der Modellloader prüft das Manifest und löst Quellen in kanonische
   SI-Meshes auf. Die Fabrik übernimmt Geometrie, Rolle, Verdrängungsflag,
   Masse und Pose in den Laufzeitkörper. Aggregierte Masse,
   Gesamtschwerpunkt und Trägheit stammen aus der Initialpose.
3. Der statische Solver untersucht Kandidaten auf einer unveränderten
   Snapshot-Eingabe. Eine akzeptierte statische Lösung wird aktuell als
   Solverresultat und Darstellungspose in der GUI gehalten, aber nicht direkt
   in `Koerper.zustand` geschrieben. Beim Start der Echtzeit wird sie in einen
   `Zustand6DOF` umgewandelt. Die dynamische Engine integriert danach Zustand
   für Zustand; beide Pfade nutzen dieselbe Kraftauswertung.
4. Worker liefern versionierte Ergebnisse. Veraltete Ergebnisse werden
   verworfen. Gültige dynamische Ergebnisse aktualisieren den Körperzustand;
   gültige statische Ergebnisse aktualisieren Solverresultat und Darstellung.
   Die Grafikbrücke stellt die jeweilige freigegebene Pose und Kraftdiagnose dar.
5. Die Kamera und Darstellungsoptionen leben im GUI-/Rendererpfad. Eine
   Gelenkwinkeländerung wirkt aktuell auf Zustand und Darstellung, nicht auf
   Masse, Schwerpunkt, Trägheit oder Auftrieb aus der Teilbewegung.

## Noch nicht enthalten

- Neue empirische Hydrodynamik oder Aerodynamik für Rumpf, Kiel, Ruder oder
  Segel; Phase 12 ist vertagt.
- Vollständige Mehrkörperdynamik oder winkelabhängige Masseneigenschaften.
- Vollständige Phase-11-Abnahme mit realen externen Paketbeständen und
  systematischem Alt-/Neu-GUI-/Physikvergleich.
