#pragma once

#include "anzeige.hpp"
#include <tuple>

namespace segelphysik {

inline std::pair<Vektor4, Vektor6> dynamik2d(
        const Vektor4& zustand, const Vektor6& parameter,
        const std::array<double, 2>& kraft_moment, const Vektor6& added)
{
    endlich(zustand, "Bewegungszustand"); endlich(parameter, "Dynamikparameter");
    endlich(kraft_moment, "Kraft/Moment"); nichtnegativ(added, "Added Mass");
    for (std::size_t i = 0; i < 4; ++i) {
        positiv(parameter[i], "Masse, Traegheit, Zeitschritt und g");
    }
    if (parameter[4] < 0. || parameter[5] < 0.) {
        throw std::invalid_argument("Daempfungswerte duerfen nicht negativ sein");
    }
    const double masse = parameter[0], dt = parameter[2];
    const double az = (kraft_moment[0] - masse * parameter[3]
        - parameter[4] * zustand[2]) / (masse + added[2]);
    const double alpha = (kraft_moment[1] - parameter[5] * zustand[3])
        / (parameter[1] + added[3]);
    const double v = zustand[2] + az * dt;
    const double omega = zustand[3] + alpha * dt;
    const Vektor4 neu{zustand[0] + v * dt, zustand[1] + omega * dt, v, omega};
    endlich(neu, "Bewegungszustand");
    return {neu, {0., 0., az, alpha, 0., 0.}};
}

using LoesungsAuswahl = std::tuple<
    std::optional<double>, std::optional<double>, bool, bool>;

inline std::optional<std::size_t> beste_loesung(const std::vector<LoesungsAuswahl>& werte)
{
    std::optional<std::size_t> beste;
    int bester_rang = 4;
    double tiefste = 0.;
    for (std::size_t i = 0; i < werte.size(); ++i) {
        const auto& [z, gm, stabil, neutral] = werte[i];
        const int rang = gm && *gm > 0. ? 0 : stabil && !neutral ? 1 : neutral ? 2 : 3;
        if (rang == 3) {
            continue;
        }
        if (!z || !std::isfinite(*z) || (gm && !std::isfinite(*gm))) {
            throw std::invalid_argument("Loesungstiefe und GM muessen endlich sein");
        }
        if (rang < bester_rang || (rang == bester_rang && *z < tiefste)) {
            beste = i; bester_rang = rang; tiefste = *z;
        }
    }
    return beste;
}

} // namespace segelphysik
