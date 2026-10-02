# ============================================================
# slider_defs.py - Definition aller GUI-Slider als Datenliste
# ------------------------------------------------------------
# (key, Label, min, max, Startwert, Schrittweite)
# Ausgelagert aus config.py, damit die GUI-Definitionstabelle beim
# Hinzufuegen neuer Regler (z. B. Ruderwinkel in Schritt 2) an einer
# eigenen Stelle gepflegt wird und config.py rein physikalisch bleibt.
# ============================================================

SLIDER_DEFS = [
    ('L',   'Laenge L [m]',               4.0,  15,    9.0,  0.1),
    ('B',   'Breite B [m]',               1.5,  5,     2.96, 0.05),
    ('H',   'Hoehe H [m]',                0.5,  3,     1.6,  0.05),
    ('rho', 'Struktur-Dichte rho',        80,   400,   130,  1),
    ('n',   'Aufloesung n',               8,    40,    16,   2),
    ('Fk',  'Klick-Kraft [g]',            0.1,  3.0,   1.0,  0.1),
    ('lk',  'Kiel-Laenge/L',              0.06, 0.20,  0.11, 0.01),
    ('tk',  'Kiel-Tiefe/L',               0.5,  1.8,   1.35, 0.05),
    ('rk',  'Bulb-Dichte',                7000, 11400, 11300, 100),
    ('FM',  'Scheiben-Kraft [N]',         0,    3000,  0,    50),
    ('FW',  'Kraftwinkel (0=Bug 90=StB)', 0,    360,   0,    5),
                ('RW',  'Ruderwinkel [deg]',  -35,  35,   0,   1)]
