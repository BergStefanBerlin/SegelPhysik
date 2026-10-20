#pragma once

#include "hydrostatik.hpp"
#include "anzeige.hpp"

namespace segelphysik {

inline Vektor3 linear_loesen(Matrix3 a, Vektor3 b)
{
    endlich(a, "Dynamikmatrix");
    endlich(b, "Rechte Seite");
    for (std::size_t k = 0; k < 3; ++k) {
        std::size_t pivot = k;
        for (std::size_t i = k + 1; i < 3; ++i) {
            if (std::abs(a[3 * i + k]) > std::abs(a[3 * pivot + k])) {
                pivot = i;
            }
        }
        if (a[3 * pivot + k] == 0.) {
            throw std::invalid_argument("Dynamikmatrix ist singulaer");
        }
        if (pivot != k) {
            for (std::size_t j = 0; j < 3; ++j) {
                std::swap(a[3 * k + j], a[3 * pivot + j]);
            }
            std::swap(b[k], b[pivot]);
        }
        for (std::size_t i = k + 1; i < 3; ++i) {
            const double faktor = a[3 * i + k] / a[3 * k + k];
            for (std::size_t j = k + 1; j < 3; ++j) {
                a[3 * i + j] -= faktor * a[3 * k + j];
            }
            b[i] -= faktor * b[k];
        }
    }
    Vektor3 x{};
    for (int i = 2; i >= 0; --i) {
        double wert = b[i];
        for (int j = i + 1; j < 3; ++j) {
            wert -= a[3 * i + j] * x[j];
        }
        x[i] = wert / a[3 * i + i];
    }
    endlich(x, "Dynamikloesung");
    return x;
}

inline void dynamik_traegheit_pruefen(double masse, const Matrix3& tensor)
{
    Modell{masse, tensor, {}, 0, {}}.pruefen();
    Matrix3 l{};
    for (std::size_t i = 0; i < 3; ++i) {
        for (std::size_t j = 0; j <= i; ++j) {
            double wert = tensor[3 * i + j];
            for (std::size_t k = 0; k < j; ++k) {
                wert -= l[3 * i + k] * l[3 * j + k];
            }
            if (i == j) {
                positiv(wert, "Dynamiktraegheit");
                l[3 * i + j] = std::sqrt(wert);
            } else {
                l[3 * i + j] = wert / l[3 * j + j];
            }
        }
    }
}

struct PhysikKontext {
    HydrostatikKontext hydrostatik;
    HydroKontext hydrodynamik;
    std::array<double, 7> hydroparameter;
    std::optional<double> cd_volumen;
    double masse;
    Matrix3 traegheit;
    Parameter parameter;

    Ergebnis schritt(const Zustand& zustand,
                     const std::optional<std::pair<Vektor3, Vektor3>>& fremdkraft,
                     double ruderwinkel, const Abbruch& abbruch,
                     bool hydro_euler = false, std::optional<double> gewicht = {}) const
    {
        const auto& z = zustand.werte;
        const Vektor3 position{z[0], z[1], z[2]};
        const auto q = quaternion_normalisieren({z[3], z[4], z[5], z[6]});
        const auto rotation = quaternion_matrix(q);
        const auto inverse = transponieren(rotation);
        const Vektor3 v{z[7], z[8], z[9]}, omega{z[10], z[11], z[12]};
        const auto v_welt = multiplizieren(rotation, v);
        const auto omega_welt = multiplizieren(rotation, omega);
        const auto hydro = hydro_euler
            ? hydrostatik.auswerten(
                euler_rotation(std::atan2(rotation[7], rotation[8]),
                    std::asin(std::clamp(-rotation[6], -1., 1.)), 0.),
                {0., 0., position[2]}, abbruch)
            : hydrostatik.auswerten(rotation, position, abbruch);
        Vektor6 relativ{};
        Vektor3 rel_v{}, rel_omega{};
        for (std::size_t i = 0; i < 3; ++i) {
            rel_v[i] = v_welt[i] - parameter.fluid[i];
            rel_omega[i] = omega_welt[i] - parameter.fluidrotation[i];
            relativ[i] = rel_v[i]; relativ[i + 3] = rel_omega[i];
        }
        const auto drag = widerstand(parameter.linear, parameter.quadratisch, relativ);
        const Wrench auftrieb{"simulationsframe", position, hydro.kraft, hydro.moment};
        std::vector<Beitrag> beitraege{
            {"hydrostatik", auftrieb},
            {"widerstand", {"simulationsframe", position,
                {drag[0], drag[1], drag[2]}, {drag[3], drag[4], drag[5]}}}};
        auto hp = hydroparameter;
        hp[6] = ruderwinkel;
        auto rollen = hydrodynamik_beitraege(
            hydrodynamik.teile, rotation, position, rel_v, rel_omega,
            hp, cd_volumen, abbruch);
        beitraege.insert(beitraege.end(), rollen.begin(), rollen.end());
        if (fremdkraft) {
            auto punkt = multiplizieren(rotation, fremdkraft->second);
            for (std::size_t i = 0; i < 3; ++i) {
                punkt[i] += position[i];
            }
            beitraege.push_back({"fremdkraft", {
                "simulationsframe", punkt, fremdkraft->first, {}}});
        }
        beitraege.push_back({"schwerkraft", {
            "simulationsframe", position, {0., 0., -gewicht.value_or(masse * parameter.g)}, {}}});
        auto aggregat = aggregiere_kraftbeitraege(beitraege, position, "simulationsframe");
        Vektor6 rate{};
        for (std::size_t i = 0; i < 6; ++i) {
            rate[i] = parameter.linear[i] + parameter.quadratisch[i] * std::abs(relativ[i]);
        }
        Vektor3 v_neu{}, omega_neu{};
        for (std::size_t block = 0; block < 2; ++block) {
            const auto versatz = 3 * block;
            Matrix3 mass = block == 0 ? Matrix3{} : traegheit;
            for (std::size_t i = 0; i < 3; ++i) {
                mass[3 * i + i] += (block == 0 ? masse : 0.)
                    + parameter.added_mass[versatz + i];
            }
            auto matrix = mass;
            for (std::size_t i = 0; i < 3; ++i) {
                for (std::size_t j = 0; j < 3; ++j) {
                    double daempfung = 0.;
                    for (std::size_t k = 0; k < 3; ++k) {
                        daempfung += ((parameter.dt * rotation[3 * k + i])
                            * rate[versatz + k]) * rotation[3 * k + j];
                    }
                    matrix[3 * i + j] += daempfung;
                }
            }
            const auto& geschwindigkeit = block == 0 ? v : omega;
            const auto impuls = multiplizieren(mass, geschwindigkeit);
            const auto gyro = kreuzprodukt(omega, impuls);
            const auto& kraft = block == 0 ? aggregat.first.kraft : aggregat.first.moment;
            const auto& fluid = block == 0 ? parameter.fluid : parameter.fluidrotation;
            Vektor3 korrigiert{}, fluidkraft{};
            for (std::size_t i = 0; i < 3; ++i) {
                korrigiert[i] = kraft[i] - (-rate[versatz + i] * relativ[versatz + i]);
                fluidkraft[i] = rate[versatz + i] * fluid[i];
            }
            const auto aussen = multiplizieren(inverse, korrigiert);
            const auto f = multiplizieren(inverse, fluidkraft);
            Vektor3 rhs{};
            for (std::size_t i = 0; i < 3; ++i) {
                rhs[i] = impuls[i] + parameter.dt * ((aussen[i] + f[i]) - gyro[i]);
            }
            (block == 0 ? v_neu : omega_neu) = linear_loesen(matrix, rhs);
        }
        const auto q_neu = orientierung_schritt(q, omega_neu, parameter.dt);
        const auto rotation_neu = quaternion_matrix(q_neu);
        const auto translation = multiplizieren(rotation_neu, v_neu);
        Zustand neu = zustand;
        Vektor6 beschleunigung{};
        Vektor3 a{}, alpha{};
        for (std::size_t i = 0; i < 3; ++i) {
            neu.werte[i] = position[i] + translation[i] * parameter.dt;
            neu.werte[7 + i] = v_neu[i]; neu.werte[10 + i] = omega_neu[i];
            a[i] = (v_neu[i] - v[i]) / parameter.dt;
            alpha[i] = (omega_neu[i] - omega[i]) / parameter.dt;
        }
        std::copy(q_neu.begin(), q_neu.end(), neu.werte.begin() + 3);
        a = multiplizieren(rotation, a); alpha = multiplizieren(rotation, alpha);
        std::copy(a.begin(), a.end(), beschleunigung.begin());
        std::copy(alpha.begin(), alpha.end(), beschleunigung.begin() + 3);
        const auto zusatz = added_mass_kraft(rotation, parameter.added_mass, beschleunigung);
        if (std::any_of(zusatz.begin(), zusatz.end(), [](double wert) { return wert != 0.; })) {
            aggregat.second.push_back({"added_mass", {"simulationsframe", position,
                {zusatz[0], zusatz[1], zusatz[2]}, {zusatz[3], zusatz[4], zusatz[5]}}});
            for (std::size_t i = 0; i < 3; ++i) {
                aggregat.first.kraft[i] += zusatz[i];
                aggregat.first.moment[i] += zusatz[i + 3];
            }
        }
        endlich(neu.werte, "Zustand");
        Ergebnis ergebnis{
            neu, hydro.volumen, hydro.schwerpunkt, aggregat.first, aggregat.second,
            auftrieb, parameter.added_mass, parameter.linear, parameter.quadratisch,
            parameter.fluid, parameter.fluidrotation, true};
        ergebnis.pruefen();
        return ergebnis;
    }
};

} // namespace segelphysik
