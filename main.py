# ============================================================
# main.py - Einstiegspunkt der Segelphysik-Simulation
# ------------------------------------------------------------
# Start:   python main.py                    (aus diesem Ordner)
#          python Segelphysik/main.py        (aus dem uebergeordneten Ordner)
# Benoetigt: numpy, matplotlib
# ============================================================
from app import QuaderApp


def main():
    QuaderApp().show()


if __name__ == '__main__':
    main()
