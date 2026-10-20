#pragma once

#include "kraftmodell.hpp"

namespace segelphysik {

struct HydrostatikWerte {
    double volumen{};
    Vektor3 schwerpunkt{}, kraft{}, moment{};
};

struct HydrostatikKontext {
    EbenenSchnitt schnitt;
    Vektor3 grenzen_min, grenzen_max;
    double gesamtvolumen;
    Vektor3 gesamtschwerpunkt, r_s;
    double rho, g;

    HydrostatikWerte auswerten(const Matrix3& rotation, const Vektor3& position,
                              const Abbruch& abbruch) const
    {
        endlich(rotation, "Rotation"); endlich(position, "Position");
        abbruch.pruefen();
        const Vektor3 normale{rotation[6], rotation[7], rotation[8]};
        double unten = std::numeric_limits<double>::infinity();
        double oben = -unten;
        for (const double x : {grenzen_min[0], grenzen_max[0]}) {
            for (const double y : {grenzen_min[1], grenzen_max[1]}) {
                for (const double z : {grenzen_min[2], grenzen_max[2]}) {
                    const double p = skalarprodukt({x, y, z}, normale);
                    unten = std::min(unten, p); oben = std::max(oben, p);
                }
            }
        }
        unten += position[2]; oben += position[2];
        const double skala = std::max({
            1., std::sqrt(skalarprodukt(grenzen_min, grenzen_min)),
            std::sqrt(skalarprodukt(grenzen_max, grenzen_max)),
            std::sqrt(skalarprodukt(position, position))});
        const double delta = 64. * std::numeric_limits<double>::epsilon() * skala;
        HydrostatikWerte ergebnis;
        if (unten > delta) {
            ergebnis.volumen = 0.;
        } else if (oben < -delta) {
            ergebnis.volumen = gesamtvolumen;
            ergebnis.schwerpunkt = multiplizieren(rotation, gesamtschwerpunkt);
            for (std::size_t i = 0; i < 3; ++i) {
                ergebnis.schwerpunkt[i] += position[i];
            }
        } else {
            const auto geschnitten = schnitt.auswerten(
                {-normale[0], -normale[1], -normale[2]}, position[2], abbruch);
            ergebnis.volumen = geschnitten.first;
            ergebnis.schwerpunkt = geschnitten.second;
            if (ergebnis.volumen > 0.) {
                ergebnis.schwerpunkt = multiplizieren(rotation, ergebnis.schwerpunkt);
                for (std::size_t i = 0; i < 3; ++i) {
                    ergebnis.schwerpunkt[i] += position[i];
                }
            }
        }
        ergebnis.kraft = {0., 0., rho * g * ergebnis.volumen};
        auto arm = multiplizieren(rotation, r_s);
        for (std::size_t i = 0; i < 3; ++i) {
            arm[i] = ergebnis.schwerpunkt[i] - (arm[i] + position[i]);
        }
        ergebnis.moment = kreuzprodukt(arm, ergebnis.kraft);
        endlich(ergebnis.schwerpunkt, "Auftriebsschwerpunkt");
        endlich(ergebnis.kraft, "Auftriebskraft"); endlich(ergebnis.moment, "Auftriebsmoment");
        return ergebnis;
    }
};

} // namespace segelphysik
