#pragma once

#include "frames.hpp"

namespace segelphysik {

inline double wasser_hash(std::int64_t ix, std::int64_t iy, std::int64_t salz)
{
    std::uint64_t h = (static_cast<std::uint64_t>(ix) * 73856093)
        ^ (static_cast<std::uint64_t>(iy) * 19349663)
        ^ (static_cast<std::uint64_t>(salz) * 83492791);
    h = (h ^ (h >> 13)) * 1274126177;
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.;
}

inline std::array<double, 2> punktlage(std::int64_t gx, std::int64_t gy, double abstand)
{
    const auto modulo = [](std::int64_t n) { return (n % 16 + 16) % 16; };
    const double hx = wasser_hash(modulo(gx), modulo(gy), 1);
    const double hy = wasser_hash(modulo(gx), modulo(gy), 2);
    const std::array<double, 2> ergebnis{
        (gx + .8 * (hx - .5)) * abstand, (gy + .8 * (hy - .5)) * abstand};
    endlich(ergebnis, "Wasserpunktlage");
    return ergebnis;
}

inline std::int64_t gitter_index(double wert)
{
    if (!std::isfinite(wert)
            || static_cast<long double>(wert) <= std::numeric_limits<std::int64_t>::min()
            || static_cast<long double>(wert) >= std::numeric_limits<std::int64_t>::max()) {
        throw std::invalid_argument("Wasserpunktindex liegt ausserhalb des Int64-Bereichs");
    }
    return static_cast<std::int64_t>(wert);
}

struct WasserPunkte {
    std::vector<Vektor3> punkte;
    std::vector<double> rand;
};

inline WasserPunkte wasserpunkte(
        const std::array<double, 2>& zentrum, double radius, double abstand, double z0)
{
    endlich(zentrum, "Wasserpunktzentrum"); positiv(radius, "Wasserpunktradius");
    positiv(abstand, "Wasserpunktabstand"); endlich(std::array<double, 1>{z0}, "Wasserhoehe");
    const auto xmin = gitter_index(std::floor((zentrum[0] - radius) / abstand));
    const auto xmax = gitter_index(std::ceil((zentrum[0] + radius) / abstand));
    const auto ymin = gitter_index(std::floor((zentrum[1] - radius) / abstand));
    const auto ymax = gitter_index(std::ceil((zentrum[1] + radius) / abstand));
    WasserPunkte ergebnis;
    for (auto x = xmin; x <= xmax; ++x) {
        for (auto y = ymin; y <= ymax; ++y) {
            const auto punkt = punktlage(x, y, abstand);
            const double d = std::hypot(punkt[0] - zentrum[0], punkt[1] - zentrum[1]);
            if (d <= radius) {
                ergebnis.punkte.push_back({punkt[0], punkt[1], z0});
                ergebnis.rand.push_back(std::clamp((radius - d) / (.35 * radius), 0., 1.));
            }
        }
    }
    return ergebnis;
}

struct WasserSpuren {
    std::vector<double> spuren, alpha;
};

inline std::size_t runden_gerade(double wert)
{
    const auto unten = static_cast<std::size_t>(std::floor(wert));
    const double rest = wert - unten;
    return unten + (rest > .5 || (rest == .5 && unten % 2 != 0) ? 1 : 0);
}

inline WasserSpuren wasserspuren(
        const std::vector<Vektor3>& punkte, const std::vector<double>& rand,
        const std::vector<std::array<double, 2>>& verlauf, std::size_t s)
{
    if (verlauf.empty() || s < 2 || punkte.size() != rand.size()) {
        throw std::invalid_argument("Ungueltige Wasserspurformen oder Stuetzstellenzahl");
    }
    if (s > std::numeric_limits<std::size_t>::max() / 3
            || punkte.size() > std::numeric_limits<std::size_t>::max() / (3 * s)) {
        throw std::overflow_error("Wasserspurarray ist zu gross");
    }
    for (const auto& c : verlauf) {
        endlich(c, "Wasserspurverlauf");
    }
    WasserSpuren ergebnis;
    ergebnis.spuren.resize(punkte.size() * s * 3);
    ergebnis.alpha.resize(punkte.size() * s);
    const double schritt = -static_cast<double>(verlauf.size() - 1) / (s - 1);
    const auto& aktuell = verlauf.back();
    for (std::size_t i = 0; i < s; ++i) {
        const double x = i + 1 == s ? 0. : i * schritt + static_cast<double>(verlauf.size() - 1);
        const auto index = runden_gerade(x);
        const double transparenz = std::pow(i + 1 == s ? 0. : 1. - i * (1. / (s - 1)), 1.5);
        for (std::size_t p = 0; p < punkte.size(); ++p) {
            endlich(punkte[p], "Wasserpunkt");
            for (std::size_t k = 0; k < 3; ++k) {
                ergebnis.spuren[(p * s + i) * 3 + k] = punkte[p][k]
                    + (k < 2 ? aktuell[k] - verlauf[index][k] : 0.);
                if (!std::isfinite(ergebnis.spuren[(p * s + i) * 3 + k])) {
                    throw std::invalid_argument("Wasserspurpunkt muss endlich sein");
                }
            }
            if (!std::isfinite(rand[p])) {
                throw std::invalid_argument("Wasserrandtransparenz muss endlich sein");
            }
            ergebnis.alpha[p * s + i] = rand[p] * transparenz;
        }
    }
    return ergebnis;
}

struct DunstGitter {
    std::vector<Vektor3> punkte;
    std::vector<std::array<std::int64_t, 5>> flaechen;
    std::vector<std::array<std::uint8_t, 4>> farben;
};

inline DunstGitter dunst_gitter(const std::vector<Vektor3>& zeilen,
        const std::vector<double>& winkel, const std::array<std::uint8_t, 3>& farbe)
{
    if (zeilen.empty() || winkel.empty()) {
        throw std::invalid_argument("Dunstgitter braucht Zeilen und Winkel");
    }
    DunstGitter ergebnis;
    const std::size_t n = winkel.size();
    for (const auto& zeile : zeilen) {
        endlich(zeile, "Dunstzeile");
        if (zeile[2] < 0. || zeile[2] > 1.) {
            throw std::invalid_argument("Dunsttransparenz muss zwischen null und eins liegen");
        }
        const auto alpha = runden_gerade(255. * zeile[2]);
        for (double w : winkel) {
            endlich(std::array<double, 1>{w}, "Dunstwinkel");
            ergebnis.punkte.push_back({zeile[0] * std::cos(w), zeile[0] * std::sin(w), zeile[1]});
            ergebnis.farben.push_back({farbe[0], farbe[1], farbe[2], static_cast<std::uint8_t>(alpha)});
        }
    }
    for (std::size_t i = 0; i + 1 < zeilen.size(); ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            const auto j2 = (j + 1) % n;
            ergebnis.flaechen.push_back({4, static_cast<std::int64_t>(i * n + j),
                static_cast<std::int64_t>(i * n + j2),
                static_cast<std::int64_t>((i + 1) * n + j2),
                static_cast<std::int64_t>((i + 1) * n + j)});
        }
    }
    return ergebnis;
}

} // namespace segelphysik
