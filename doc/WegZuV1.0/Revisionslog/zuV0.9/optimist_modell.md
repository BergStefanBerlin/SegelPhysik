# Optimist – Näherungsmodell

## Herkunft und Geometrie

Das Paket [optimist](../../../../code/modelle/optimist/modell.json) wurde aus
`optimist_einzelteile.zip` in diesem Ordner aufgebaut. Verwendet werden die
Meter-OBJ-Varianten der Bauteile. Deren Kopfzeilen nennen eine angenommene
Skalierung von `0,225105` auf `2,36 m` Rumpflänge. Die lokale OBJ-Achsenlage
ist `X = Breite`, `Y = Höhe`, `Z = Längsachse`; das Paket bildet sie in das
SegelPhysik-Modellframe ab. Die Querrichtung wurde zusätzlich einheitlich
skaliert, damit die Rumpfbreite `1,12 m` beträgt.

Als Plausibilitätswerte dienen die technischen Angaben der
[UK Optimist Class – Boat Specifications](https://www.optimist.org.uk/the-boat/technical-info/):
Länge `2,36 m`, Breite `1,12 m`, Masthöhe `2,26 m`, Segelfläche `3,3 m²`
und Mindestgewicht `35 kg`. Die lokale Rumpf- und Masthöhe liegen in der
Nähe dieser Werte. Die übernommene Segelmesh-Oberfläche ist kein unabhängiger
Nachweis der wirksamen Segelfläche.

Die gelieferten OBJ-Dateien enthalten nichtplanare Polygone; der bestehende
Importer akzeptiert nur Dreiecke bzw. planare Polygone. Der Rumpf und das
Schwert enthalten außerdem nicht-mannigfaltige Kanten. Die gelieferten
Rumpf-/Schwertflächen wurden deshalb **nicht** als exakte Physikmeshes
verwendet. Für diese beiden Teile wurden geschlossene konvexe Hüllen aus
ihren Meter-Mesh-Eckpunkten trianguliert. Das hält die Meshes für
Hydrostatik und Masseberechnung geschlossen, füllt aber Cockpit,
Einbuchtungen und andere konkave Details auf. Es ist eine Näherung, keine
Reparatur des Original-CAD.

Die übrigen Komponenten wurden trianguliert und in der Breite mit demselben
Faktor wie der Rumpf korrigiert. Sie bleiben in ihrer gelieferten
Montageposition. Ruderblatt, Pinne, Pinnenausleger und Gummigelenk sind im
Manifest unter der Baugruppe „Ruder“ gruppiert. Das Gummigelenk-Mesh stammt
aus `optimist_rubber_joint_meter.obj` und liegt geometrisch an der Verbindung
von Pinne und Ruder; es wird deshalb als Bestandteil der Ruderbaugruppe
berücksichtigt. Ruderkontakt, Schwertverstellung und Segelkinematik sind
nicht als bewegliche Gelenke modelliert; alle Bauteile gehören zu einem
starren Gesamtkörper.

## Massenannahmen

Die Quelldaten enthalten keine verifizierten Massen, Schwerpunkt- oder
Trägheitsdaten. Die Modellmassen sind daher Näherungen:

- Rumpf: angenommene GfK-Dichte `1900 kg/m³`, effektive Schalenstärke `3 mm`.
  Die daraus resultierende Rumpfmasse liegt nahe dem publizierten
  Mindestgewicht von `35 kg`; das ist eine Kalibrierannahme, keine Messung.
- Mast und Baum: Aluminium mit jeweils angenommener Schalenstärke `1 mm`;
  Spriet `0,8 mm`.
- Schwert und Ruder: flächenbasierte Holz-/Verbund-Näherungen mit
  `600` bzw. `700 kg/m³`.
- Segel: `1250 kg/m³` mit effektiver Dicke `0,08 mm`; keine gemessene
  Segelmasse.
- Pinne, Ausleger und Gummigelenk: angenommene Volumendichten.
- Segler: ausdrücklich freigegebene Punktmasse `50 kg`, Startschwerpunkt
  `(0; 0; 0,45) m` relativ zur Mitte der Rumpfbegrenzung auf der
  Rumpfunterkante. Der Referenzpunkt ist im Manifest als
  `(0; 0; −1,435812) m` gespeichert. Mit Besatzung beträgt die modellierte
  Gesamtmasse bei Paketdefaults rund `92,587 kg`; die Bootsmasse ohne
  Segler bleibt rund `42,587 kg`.

Seglermasse und alle drei rumpffesten Koordinaten lassen sich im Baum
einstellen und werden in der separaten lokalen Benutzereinstellung
gespeichert. Die Punktmasse trägt keinen eigenen Auftrieb und keine
autonome Bewegung bei, aber ihren vollständigen Steiner-Anteil zur
Gesamtträgheit. Die Punktmassen-Eigenträgheit ist null; das ist eine
ausgewiesene Schulungsannahme.

Der aggregierte Schwerpunkt und Trägheitstensor werden aus diesen Massen
und den Meshgeometrien berechnet. Sie sind nicht durch Herstellerdaten
validiert. Das Modell ist damit für Entwicklung, Visualisierung und
qualitative Versuche gedacht, nicht als klassenzugelassenes,
quantitativ validiertes Optimist-Modell.

## Bekannte Grenzen und nächste Arbeit

- Die konvexe Rumpfnäherung kann Wasserlinienfläche, Verdrängung und
  Auftrieb gegenüber dem echten offenen Rumpf systematisch verfälschen.
- Es fehlen verifizierte Rumpfmasse, Gesamtmasse, Schwerpunkt,
  Trägheitstensor, Rumpflinien und Hydrostatik-/Widerstandsreferenzen.
- Das hydrodynamische Modell verwendet die vorhandenen allgemeinen
  Rumpf-/Kiel-/Ruderansätze; Optimist-spezifische Kalibrierung ist nicht
  erfolgt.
- Für höhere physikalische Genauigkeit muss die konvexe Näherung durch
  ein wasserdichtes, manuell oder aus Original-CAD bereinigtes Rumpfmesh
  ersetzt und gegen reale Optimist-Daten geprüft werden.
