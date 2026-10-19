# Optimist: Modell- und Besatzungsannahmen

Das Paket ist eine aus bereitgestellten Geometrien abgeleitete
Schulungsnäherung, kein validierter Klassenlinienriss, Engineering-Nachweis
oder Race-Optimizer. Massen und Geometrie sind nicht an ein vermessenes
reales Boot kalibriert.

Für A-V0.9-00002 wurde am 19.10.2026 eine Besatzungsmasse von 50 kg mit
Startposition (0; 0; 0,45) m freigegeben. Die drei Koordinaten beziehen sich
auf den expliziten Rumpfreferenzpunkt (0; 0; −1,435812) m im Modellframe:
Mitte der Rumpfbegrenzung in Längs-/Querrichtung auf der Rumpfunterkante.
x zeigt längs, y quer und z nach oben. Dieser Punkt ist nicht der
Gesamtschwerpunkt des Bootes.

Der Segler ist eine starr mit dem Rumpf verbundene geometriefreie
Punktmasse. Seine Masse, Position und sein Steiner-Anteil gehen in die
Gesamtmasseneigenschaften ein. Es gibt keinen zusätzlichen Auftrieb und
keine eigenständige Seglerintegration. Die Eigenträgheit der Punktmasse
ist eine bewusst ausgewiesene Modellannahme.

Masse und x/y/z-Position sind über die Eigenschaftszeilen des Seglers im
Modellbaum editierbar. Änderungen werden atomar in der lokalen
Benutzereinstellung `../../../konfigurationen/segler.json` gespeichert,
nicht in diesem Paket. Statische und dynamische Simulation verwenden
dieselben eingestellten Masseneigenschaften.
