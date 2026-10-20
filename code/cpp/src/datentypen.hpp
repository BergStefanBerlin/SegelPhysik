#pragma once

#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace segelphysik {

using Vektor3 = std::array<double, 3>;
using Vektor4 = std::array<double, 4>;
using Vektor6 = std::array<double, 6>;
using Matrix3 = std::array<double, 9>;

template <typename Werte>
void endlich(const Werte& werte, const char* name)
{
    for (double wert : werte) {
        if (!std::isfinite(wert)) {
            throw std::invalid_argument(std::string(name) + " muss endlich sein");
        }
    }
}

inline void positiv(double wert, const char* name)
{
    if (!std::isfinite(wert) || wert <= 0.) {
        throw std::invalid_argument(std::string(name) + " muss endlich positiv sein");
    }
}

inline void nichtnegativ(const Vektor6& werte, const char* name)
{
    endlich(werte, name);
    for (double wert : werte) {
        if (wert < 0.) {
            throw std::invalid_argument(std::string(name) + " darf nicht negativ sein");
        }
    }
}

inline void name_pruefen(const std::string& wert, const char* name)
{
    if (wert.empty()) {
        throw std::invalid_argument(std::string(name) + " darf nicht leer sein");
    }
}

struct Zustand {
    std::array<double, 13> werte;

    explicit Zustand(std::array<double, 13> daten) : werte(daten)
    {
        endlich(werte, "Zustand");
        bool rotation_vorhanden = false;
        for (std::size_t i = 3; i < 7; ++i) {
            rotation_vorhanden = rotation_vorhanden || werte[i] != 0.;
        }
        if (!rotation_vorhanden) {
            throw std::invalid_argument("Quaternion darf nicht null sein");
        }
    }
};

struct Mesh {
    std::vector<Vektor3> punkte;
    std::vector<std::array<std::int64_t, 3>> dreiecke;
    std::string name;
    std::string rolle;
    bool verdraengend;
    std::string quell_id{};

    void pruefen() const
    {
        for (const auto& punkt : punkte) {
            endlich(punkt, "Meshpunkt");
        }
        for (const auto& dreieck : dreiecke) {
            for (auto index : dreieck) {
                if (index < 0 || static_cast<std::uint64_t>(index) >= punkte.size()) {
                    throw std::invalid_argument("Dreiecksindex ausserhalb des Punktarrays");
                }
            }
        }
    }
};

struct Modell {
    double masse;
    Matrix3 traegheit;
    std::vector<Mesh> meshes;
    std::uint64_t version;
    Vektor3 r_S;

    void pruefen() const
    {
        positiv(masse, "Masse");
        endlich(traegheit, "Traegheit");
        endlich(r_S, "Modellschwerpunkt");
        for (std::size_t i = 0; i < 3; ++i) {
            for (std::size_t j = 0; j < 3; ++j) {
                if (std::abs(traegheit[3 * i + j] - traegheit[3 * j + i]) > 1e-10) {
                    throw std::invalid_argument("Traegheit muss symmetrisch sein");
                }
            }
        }
        Matrix3 faktor{};
        double skala = std::numeric_limits<double>::min();
        for (double wert : traegheit) {
            if (std::abs(wert) > skala) {
                skala = std::abs(wert);
            }
        }
        const double toleranz = 128. * std::numeric_limits<double>::epsilon() * skala;
        for (std::size_t i = 0; i < 3; ++i) {
            for (std::size_t j = 0; j <= i; ++j) {
                double wert = traegheit[3 * i + j];
                for (std::size_t k = 0; k < j; ++k) {
                    wert -= faktor[3 * i + k] * faktor[3 * j + k];
                }
                if (i == j) {
                    if (wert < -toleranz) {
                        throw std::invalid_argument("Traegheit muss positiv semidefinit sein");
                    }
                    faktor[3 * i + j] = std::sqrt(wert > 0. ? wert : 0.);
                } else {
                    if (faktor[3 * j + j] == 0.) {
                        if (std::abs(wert) > toleranz) {
                            throw std::invalid_argument("Traegheit muss positiv semidefinit sein");
                        }
                    } else {
                        faktor[3 * i + j] = wert / faktor[3 * j + j];
                    }
                }
            }
        }
        for (const auto& mesh : meshes) {
            mesh.pruefen();
        }
    }
};

struct Parameter {
    double rho;
    double g;
    double dt;
    Vektor6 linear;
    Vektor6 quadratisch;
    Vektor6 added_mass;
    Vektor3 fluid;
    Vektor3 fluidrotation;

    void pruefen() const
    {
        positiv(rho, "Wasserdichte");
        positiv(g, "g");
        positiv(dt, "Zeitschritt");
        nichtnegativ(linear, "Linearer Widerstand");
        nichtnegativ(quadratisch, "Quadratischer Widerstand");
        nichtnegativ(added_mass, "Added Mass");
        endlich(fluid, "Fluidgeschwindigkeit");
        endlich(fluidrotation, "Fluidwinkelgeschwindigkeit");
    }
};

struct Wrench {
    std::string frame;
    Vektor3 bezugspunkt;
    Vektor3 kraft;
    Vektor3 moment;

    void pruefen() const
    {
        name_pruefen(frame, "Frame");
        endlich(bezugspunkt, "Bezugspunkt");
        endlich(kraft, "Kraft");
        endlich(moment, "Moment");
    }
};

struct Beitrag {
    std::string name;
    Wrench wrench;
    std::string quell_id{};
    std::optional<Vektor3> originalangriff{};

    void pruefen() const
    {
        name_pruefen(name, "Beitragsname");
        wrench.pruefen();
        if (originalangriff) {
            endlich(*originalangriff, "Originalangriff");
        }
    }
};

struct Ergebnis {
    Zustand zustand;
    double volumen;
    Vektor3 auftriebsschwerpunkt;
    Wrench gesamt;
    std::vector<Beitrag> beitraege;
    Wrench auftrieb;
    Vektor6 added_mass;
    Vektor6 linear;
    Vektor6 quadratisch;
    Vektor3 fluid;
    Vektor3 fluidrotation;
    bool schwerkraft_beruecksichtigt;
    std::optional<Zustand> kraftzustand{};

    void pruefen() const
    {
        if (!std::isfinite(volumen) || volumen < 0.) {
            throw std::invalid_argument("Tauchvolumen muss endlich nichtnegativ sein");
        }
        endlich(auftriebsschwerpunkt, "Auftriebsschwerpunkt");
        gesamt.pruefen();
        auftrieb.pruefen();
        if (auftrieb.frame != gesamt.frame) {
            throw std::invalid_argument("Auftriebsframe passt nicht zum Gesamtframe");
        }
        nichtnegativ(added_mass, "Added Mass");
        nichtnegativ(linear, "Linearer Widerstand");
        nichtnegativ(quadratisch, "Quadratischer Widerstand");
        endlich(fluid, "Fluidgeschwindigkeit");
        endlich(fluidrotation, "Fluidwinkelgeschwindigkeit");
        for (const auto& beitrag : beitraege) {
            beitrag.pruefen();
            if (beitrag.wrench.frame != gesamt.frame) {
                throw std::invalid_argument("Beitragsframe passt nicht zum Gesamtframe");
            }
        }
    }
};

class Abbruch {
public:
    void abbrechen() { abgebrochen_.store(true, std::memory_order_relaxed); }
    bool abgebrochen() const { return abgebrochen_.load(std::memory_order_relaxed); }
    void pruefen() const
    {
        if (abgebrochen()) {
            throw std::runtime_error("Native Berechnung abgebrochen");
        }
    }

private:
    std::atomic<bool> abgebrochen_{false};
};

} // namespace segelphysik
