"""Overlay-Layer (Spec V4 P5a/P5b): Layer-Registry + Hauptachsen-Berechnung.

P5a: Der KOERPER kennt keine Layer. Die Registry ist global (Szene) und
speichert nur Sichtbarkeiten; der Renderer projiziert die Wahrheit des
Koerpers (r_S, I_S) pro Frame neu - nie wird eine Ansicht im Koerper
gespeichert (Merksatz: Koerper = Wahrheit, Renderer = Projektion).

P5b: Ohne Physik darstellbar: Masseschwerpunkt (Layer 'schwerpunkt') und
Haupttraegheitsachsen (Layer 'hauptachsen', Eigenvektoren von I_S).
Rein numpy, pyvista-frei -> deterministisch, unit-testbar.

Phase C (P5c, Umsetzungsplan V5 rev 9 §5): Layer 'kraefte' (Kraeftebild)
- ebenfalls nur ein globaler Sichtbarkeits-Schalter; die
Geometrie liefert core.kraefte_bild, die Wahrheit core.auftrieb.
"""
import numpy as np

LAYER_SCHWERPUNKT = "schwerpunkt"
LAYER_HAUPTACHSEN = "hauptachsen"
LAYER_KRAEFTE = "kraefte"
LAYER_MOMENTE = "momente"
LAYER_FREMDKRAFT = "fremdkraft"
LAYER_ALL = (LAYER_SCHWERPUNKT, LAYER_HAUPTACHSEN,
             LAYER_KRAEFTE, LAYER_MOMENTE, LAYER_FREMDKRAFT)


class LayerRegistry:
    """Globaler Sichtbarkeits-Schalter pro Layer (P5a: global, nicht pro Koerper).

    Ein eingeschalteter Layer betrifft ALLE Koerper gleichzeitig; der
    Koerper selbst kennt keine Layer.
    """

    def __init__(self, standard_aus=True):
        self._zustand = {name: (not standard_aus) for name in LAYER_ALL}

    def ist_an(self, layer):
        return bool(self._zustand[layer])

    def umschalten(self, layer):
        self._zustand[layer] = not self._zustand[layer]
        return self._zustand[layer]

    def setzen(self, layer, wert):
        self._zustand[layer] = bool(wert)

    def zustand(self):
        return dict(self._zustand)


def _kanonisiere(v):
    """Vorzeichen kanonisieren: groesste Komponente positiv.

    Ein Eigenvektor ist nur bis auf das Vorzeichen bestimmt; die
    Kanonisierung macht die Darstellung deterministisch (K7-Prinzip).
    """
    v = np.asarray(v, float).copy()
    i = int(np.argmax(np.abs(v)))
    if v[i] < 0.0:
        v = -v
    return v


def hauptachsen(traegheitstensor):
    """Eigenwerte (absteigend) und Eigenvektoren von I_S.

    Rueckgabe (werte, vektoren): werte[0] >= werte[1] >= werte[2];
    vektoren[:, i] ist der zugehoerige Einheitsvektor (kanonisiert).
    """
    I = np.asarray(traegheitstensor, float)
    I = 0.5 * (I + I.T)          # Symmetrie numerisch erzwingen
    werte, vektoren = np.linalg.eigh(I)
    reihenfolge = np.argsort(werte)[::-1]
    werte = werte[reihenfolge]
    vektoren = vektoren[:, reihenfolge]
    for i in range(3):
        vektoren[:, i] = _kanonisiere(vektoren[:, i])
    return werte, vektoren
