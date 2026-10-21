# Offene Punkte zuV0.14

## Einfacher globaler Widerstand und Hydrodynamikpfad

Der in der Kräfteanzeige sichtbare Beitrag **„Einfacher Widerstand
[widerstand]“** ist ein globaler Widerstandsterm des Hauptkörpers. Er ist
nicht das auswählbare einfache, bauteilbezogene Hydrodynamikmodell.

```text
Hauptkörperbewegung relativ zum Wasser
v = (v_x, v_y, v_z)        ω = (ω_x, ω_y, ω_z)
                 │
                 ▼
   Einfacher, globaler Widerstandsterm
   F_i = -c_i·v_i - d_i·|v_i|·v_i       i = x, y, z
   M_i = -c_i·ω_i - d_i·|ω_i|·ω_i      i = Roll, Nick, Gier
                 │
                 ▼
   Kräfteanzeige: „Einfacher Widerstand [widerstand]“
   Ein aggregierter Beitrag; Kraft und Moment wirken der Bewegung entgegen.
```

Die Auswahl **„Hydrodynamikmodell“** schaltet dagegen zwischen den
bauteilbezogenen Berechnungen um:

```text
Hydrodynamikmodell
  ├─ Geometrisch ──► geometrische Beiträge von Rumpf / Kiel / Ruder
  └─ Einfach ──────► Koeffizientenmodell für Rumpf / Kiel / Ruder

Gesamtbilanz = Auftrieb + Gewicht + Wind/Fremdkraft
             + ausgewählte Bauteil-Hydrodynamik
             + globaler Widerstandsterm (falls aktiv)
```

Im einfachen Hydrodynamikpfad wird der globale Widerstandsterm deaktiviert,
damit er nicht zusätzlich zum einfachen Bauteilmodell zählt. Im vom Nutzer
gezeigten Kräftefenster ist der separate globale Beitrag sichtbar, beträgt
aber **0 N**.

### Noch zu klären

- Die Kräfteanzeige benennt die ausgewählte einfache oder geometrische
  Bauteil-Hydrodynamik derzeit nicht ausdrücklich. Die Bauteilzeilen allein
  zeigen nicht, welcher Pfad sie berechnet hat.
- Die Bezeichnung „Einfacher Widerstand“ kann mit dem auswählbaren
  „Einfach“-Hydrodynamikmodell verwechselt werden, obwohl es sich um zwei
  verschiedene Modellanteile handelt.
- Die Anzeige sollte den aktiven Hydrodynamikpfad klar ausweisen und den
  globalen Widerstandsterm so benennen, dass seine Abgrenzung erkennbar ist.
