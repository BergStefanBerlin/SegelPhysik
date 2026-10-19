# Folkeboot-Rumpf: vorläufige Näherung

Dieses Modell ist eine sichtbare, maßstäbliche Arbeitsnäherung und **kein**
offizieller Folkeboot-Linienriss. Es ist noch nicht anhand von Messdaten
validiert und darf nicht als klassenkonform verstanden werden.

## Gesicherte Maßanker

Die öffentlich zugängliche NFIA-Zeichnung GRP 7 nennt 7,68 m Länge über alles,
6,00 m Wasserlinienlänge, 2,20 m Breite, 1,20 m Tiefgang und 1.930 kg
Mindestgewicht. Die Zeichnung GRP 9 zeigt einen Längsschnitt. Beide Zeichnungen
enthalten in der öffentlich sichtbaren Fassung keinen vollständigen Satz
numerischer Rumpfstationen/Offsets.

Quellen:

- [NFIA GRP 7 – General Arrangement](https://folkboat.com/wp-content/uploads/2025/06/GRP-7-236_03_Folkboat_GA_V025-1.pdf)
- [NFIA GRP 9 – Midsection](https://folkboat.com/wp-content/uploads/2025/06/GRP-9-236_03_FOLKBOAT_iYacht-Folkeboot-Midsection.pdf)
- [NFIA Class Rules and Documents](https://folkboat.com/class-rules/)

## Geschätzte Geometrie

- Die Rumpfbreite wird über elf Längsstationen verteilt; die maximale Breite
  beträgt genau 2,20 m.
- Die Verteilung der Stationsbreiten, Spantform, Kimm, Stevenform und
  Freibordkurve sind aus der GA-Zeichnung angenähert, nicht abgenommen.
- Der Rumpf ist 7,68 m lang. Die Außenkontur hat eine maximale Höhe von
  1,09 m; der Höhenbezug ist eine Modellannahme, kein bestätigtes Freibordmaß.
- Kiel und Ruder sind vereinfachte, geschlossene Volumenkörper. Ihre Formen,
  Massenverteilung und Positionen sind nicht durch Offsets belegt. Der
  vereinfachte Bleikiel ist geometrisch so dimensioniert, dass seine
  modellierte Masse ungefähr in der Größenordnung der offiziellen
  Klassenangabe von 1.000–1.050 kg liegt; das ist keine Messwertvalidierung.
- Mast, Großbaum, Großsegel und Fock sind als proportionale Arbeitsgeometrie
  ergänzt. Der Mast reicht vom modellierten Deckniveau bis 10,55 m über dem
  Rumpf-Nullpunkt; der Großbaum ist rund 3,37 m lang. Die Segel haben
  näherungsweise 16,9 m² (Großsegel) und 7,5 m² (Fock) projizierte Fläche.
  Die Segelflächen sind vereinfachte ebene Umrisse, keine vermessenen
  Segelschnitte oder Profile.
- Die Riggpositionen, Mast-/Baumquerschnitte, Segelkonturen, Segelflächen und
  Massen sind Näherungen. Sie sind nicht gegen den offiziellen NFIA-Segelplan
  oder Messbrief geprüft.
- Die resultierende Gesamtmasse ist nicht auf das Klassen-Mindestgewicht
  kalibriert; Ausrüstung, Innenausbau und weitere Massen fehlen.
- Innenausbau und stehendes/laufendes Gut sind nicht enthalten.
- Zusätzlich ist die am 19.10.2026 freigegebene Besatzungs-Punktmasse von
  150 kg enthalten. Ihr Startschwerpunkt liegt 0,85 m über dem expliziten
  Rumpfreferenzpunkt (Mitte der Rumpfbegrenzung auf Unterkante z = −0,47 m).
  Sie erzeugt kein zusätzliches verdrängendes Volumen. Die Masse und die
  drei rumpffesten Koordinaten lassen sich im Modellbaum einstellen und
  werden getrennt vom Paket als Benutzereinstellung gespeichert.

Die OBJ-Dateien lassen sich mit `generiere_meshes.py` reproduzieren. Für
Hydrostatik, Stabilität oder Leistungsprognosen muss das Modell durch den
vollständigen NFIA-Linienriss und belastbare Massen-/Schwerpunktdaten ersetzt
oder kalibriert werden.
