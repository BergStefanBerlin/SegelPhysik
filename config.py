# ============================================================
# config.py - Zentrale Konstanten und Voreinstellungen
# ------------------------------------------------------------
# Hier stehen ALLE Stellschrauben an einem Ort: Physik-Konstanten,
# Anzeige-Parameter, Presets und die Slider-Definitionen der GUI.
# ============================================================

# ------------------------------ Physik ------------------------------
G = 9.81                 # Erdbeschleunigung [m/s^2]
RHO_W = 1000.0           # Wasserdichte [kg/m^3] (fest)
DT = 0.006               # Zeitschritt [s]
NSUB = 6                 # Teilschritte pro Bild
M_ADD_FAKTOR = 0.5       # added mass (Anteil der Verdraengungsmasse)

# ------------------------------ Anzeige -----------------------------
W_OPTO = 4.0             # opt. Verstaerkkung der Wasserbewegung
PFEIL_VOR = 1.35 * 0.5   # Kurspfeile: Abstand vorn (x, Anteil L)
MAST_H_FAKTOR = 1.45     # Masthoehe ueber Deck (Vielfaches von L)

# ------------------------------ Presets -----------------------------
PRESETS = {'Flach (stabil)': (4.0, 2.0, 1.2, 450),
           'Hoch (kentert)': (2.0, 1.0, 2.5, 700),
           'Yacht-Rohling':  (9.0, 2.5, 2.0, 300),
           'Holzstamm quer': (3.0, 0.4, 0.4, 600)}

# ------------------------ Slider-Definitionen -----------------------
# (key, Label, min, max, Startwert, Schrittweite)
SLIDER_DEFS = [
    ('L',   'Laenge L [m]',              4.0,  15,    9.0,  0.1),
    ('B',   'Breite B [m]',              1.5,  5,     2.96, 0.05),
    ('H',   'Hoehe H [m]',               0.5,  3,     1.6,  0.05),
    ('rho', 'Struktur-Dichte rho',       80,   400,   130,  1),
    ('n',   'Aufloesung n',              8,    40,    16,   2),
    ('Fk',  'Klick-Kraft [g]',           0.1,  3.0,   1.0,  0.1),
    ('lk',  'Kiel-Laenge/L',             0.06, 0.20,  0.11, 0.01),
    ('tk',  'Kiel-Tiefe/L',              0.5,  1.8,   1.35, 0.05),
    ('rk',  'Bulb-Dichte',               7000, 11400, 11300, 100),
    ('FM',  'Scheiben-Kraft [N]',        0,    3000,  0,    50),
    ('FW',  'Kraftwinkel (0=Bug 90=StB)', 0,   360,   0,    5)]
