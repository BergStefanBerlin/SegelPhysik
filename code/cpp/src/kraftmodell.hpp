#pragma once

#include "hydrodynamik.hpp"

namespace segelphysik {

inline Wrench wrench_verschieben(const Wrench& quelle, const Vektor3& ziel)
{
    quelle.pruefen();
    endlich(ziel, "Wrench-Bezugspunkt");
    Vektor3 arm{};
    for (std::size_t i = 0; i < 3; ++i) {
        arm[i] = quelle.bezugspunkt[i] - ziel[i];
    }
    auto moment = kreuzprodukt(arm, quelle.kraft);
    for (std::size_t i = 0; i < 3; ++i) {
        moment[i] += quelle.moment[i];
    }
    Wrench ergebnis{quelle.frame, ziel, quelle.kraft, moment};
    ergebnis.pruefen();
    return ergebnis;
}

inline std::pair<Wrench, std::vector<Beitrag>> aggregiere_kraftbeitraege(
        const std::vector<Beitrag>& beitraege, const Vektor3& ziel,
        const std::string& frame)
{
    Wrench gesamt{frame, ziel, {}, {}};
    gesamt.pruefen();
    std::vector<Beitrag> normalisiert;
    for (const auto& beitrag : beitraege) {
        if (beitrag.wrench.frame != frame) {
            throw std::invalid_argument("Kraftbeitrag " + beitrag.name
                + " liegt im falschen Frame " + beitrag.wrench.frame);
        }
        auto wrench = wrench_verschieben(beitrag.wrench, ziel);
        for (std::size_t i = 0; i < 3; ++i) {
            gesamt.kraft[i] += wrench.kraft[i];
            gesamt.moment[i] += wrench.moment[i];
        }
        normalisiert.push_back({beitrag.name, std::move(wrench),
            beitrag.quell_id, beitrag.originalangriff});
    }
    gesamt.pruefen();
    return {gesamt, normalisiert};
}

inline Vektor6 widerstand(const Vektor6& linear, const Vektor6& quadratisch,
                         const Vektor6& relativ)
{
    endlich(linear, "Linearer Widerstand");
    endlich(quadratisch, "Quadratischer Widerstand");
    endlich(relativ, "Relativgeschwindigkeit");
    Vektor6 ergebnis{};
    for (std::size_t i = 0; i < 6; ++i) {
        ergebnis[i] = -linear[i] * relativ[i]
            - quadratisch[i] * std::abs(relativ[i]) * relativ[i];
    }
    endlich(ergebnis, "Widerstandskraft");
    return ergebnis;
}

inline Vektor6 added_mass_kraft(const Matrix3& rotation, const Vektor6& added,
                               const Vektor6& beschleunigung)
{
    const auto inverse = transponieren(rotation);
    Vektor6 ergebnis{};
    for (std::size_t block = 0; block < 2; ++block) {
        const auto i = 3 * block;
        auto a = multiplizieren(inverse, Vektor3{
            beschleunigung[i], beschleunigung[i + 1], beschleunigung[i + 2]});
        for (std::size_t j = 0; j < 3; ++j) {
            a[j] *= -added[i + j];
        }
        a = multiplizieren(rotation, a);
        std::copy(a.begin(), a.end(), ergebnis.begin() + i);
    }
    endlich(ergebnis, "Added-Mass-Kraft");
    return ergebnis;
}

} // namespace segelphysik
