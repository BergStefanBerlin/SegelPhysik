#pragma once

#include "datentypen.hpp"
#include <algorithm>
#include <limits>

namespace segelphysik {

struct WasserRaster {
    std::size_t ny, nx;
    std::vector<double> werte;
};

inline std::size_t rastergroesse(std::size_t ny, std::size_t nx)
{
    if (!ny || !nx) {
        return 0;
    }
    if (ny > std::vector<double>().max_size() / nx) {
        throw std::overflow_error("Wasserraster ist zu gross");
    }
    return ny * nx;
}

inline WasserRaster bilinear_upsample(const WasserRaster& z, std::size_t faktor)
{
    if (!faktor || !z.nx || !z.ny) {
        throw std::invalid_argument("Ungueltige Wasserrasterdimension oder Vergroesserung");
    }
    const auto maximal = std::numeric_limits<std::size_t>::max();
    if ((z.nx > 1 && faktor > (maximal - 1) / (z.nx - 1))
            || (z.ny > 1 && faktor > (maximal - 1) / (z.ny - 1))) {
        throw std::overflow_error("Vergroessertes Wasserraster ist zu gross");
    }
    WasserRaster ziel{(z.ny - 1) * faktor + 1, (z.nx - 1) * faktor + 1, {}};
    ziel.werte.resize(rastergroesse(ziel.ny, ziel.nx));
    const double dx = ziel.nx > 1
        ? static_cast<double>(z.nx - 1) / static_cast<double>(ziel.nx - 1) : 0.;
    const double dy = ziel.ny > 1
        ? static_cast<double>(z.ny - 1) / static_cast<double>(ziel.ny - 1) : 0.;
    for (std::size_t y = 0; y < ziel.ny; ++y) {
        const double yi = y == ziel.ny - 1 ? static_cast<double>(z.ny - 1) : y * dy;
        const auto y0 = static_cast<std::size_t>(std::floor(yi));
        const auto y1 = std::min(y0 + 1, z.ny - 1);
        const double wy = yi - y0;
        for (std::size_t x = 0; x < ziel.nx; ++x) {
            const double xi = x == ziel.nx - 1 ? static_cast<double>(z.nx - 1) : x * dx;
            const auto x0 = static_cast<std::size_t>(std::floor(xi));
            const auto x1 = std::min(x0 + 1, z.nx - 1);
            const double wx = xi - x0;
            ziel.werte[y * ziel.nx + x] =
                ((z.werte[y0 * z.nx + x0] * (1. - wx) * (1. - wy)
                + z.werte[y0 * z.nx + x1] * wx * (1. - wy))
                + z.werte[y1 * z.nx + x0] * (1. - wx) * wy)
                + z.werte[y1 * z.nx + x1] * wx * wy;
        }
    }
    return ziel;
}

inline WasserRaster wasser_glaetten(WasserRaster z, double dx, std::int64_t durchlaeufe)
{
    rastergroesse(z.ny, z.nx);
    auto nachbar = [&](std::size_t y, std::size_t x, int dy, int dx) {
        const auto yy = static_cast<std::size_t>(std::clamp<std::int64_t>(
            static_cast<std::int64_t>(y) - dy, 0, static_cast<std::int64_t>(z.ny) - 1));
        const auto xx = static_cast<std::size_t>(std::clamp<std::int64_t>(
            static_cast<std::int64_t>(x) - dx, 0, static_cast<std::int64_t>(z.nx) - 1));
        return yy * z.nx + xx;
    };
    const auto anzahl = z.werte.size();
    std::vector<double> neu(anzahl);
    std::vector<bool> schlecht(anzahl);
    std::size_t fehlend = 0;
    for (std::size_t i = 0; i < anzahl; ++i) {
        schlecht[i] = !std::isfinite(z.werte[i]);
        fehlend += schlecht[i];
    }
    if (fehlend == anzahl) {
        std::fill(z.werte.begin(), z.werte.end(), 0.);
        return z;
    }
    if (!std::isfinite(dx)) {
        throw std::invalid_argument("Wassergitterabstand muss endlich sein");
    }
    for (int runde = 0; runde < 25 && fehlend; ++runde) {
        neu = z.werte;
        for (std::size_t y = 0; y < z.ny; ++y) {
            for (std::size_t x = 0; x < z.nx; ++x) {
                const auto i = y * z.nx + x;
                if (!schlecht[i]) { continue; }
                double summe = 0., zahl = 0.;
                for (int dy = -1; dy <= 1; ++dy) {
                    for (int dx = -1; dx <= 1; ++dx) {
                        if (!dy && !dx) { continue; }
                        const auto j = nachbar(y, x, dy, dx);
                        if (!schlecht[j]) { summe += z.werte[j]; zahl += 1.; }
                    }
                }
                const double fuellung = zahl > 0.
                    ? summe / zahl : std::numeric_limits<double>::quiet_NaN();
                if (std::isfinite(fuellung)) { neu[i] = fuellung; }
            }
        }
        z.werte.swap(neu);
        fehlend = 0;
        for (std::size_t i = 0; i < anzahl; ++i) {
            schlecht[i] = !std::isfinite(z.werte[i]);
            fehlend += schlecht[i];
        }
    }
    if (fehlend) {
        std::vector<double> werte;
        for (double wert : z.werte) {
            if (!std::isnan(wert)) { werte.push_back(wert); }
        }
        std::sort(werte.begin(), werte.end());
        const auto mitte = werte.size() / 2;
        const double median = werte.size() % 2
            ? werte[mitte] : (werte[mitte - 1] + werte[mitte]) / 2.;
        for (std::size_t i = 0; i < anzahl; ++i) {
            if (schlecht[i]) { z.werte[i] = median; }
        }
    }
    for (std::size_t y = 0; y < z.ny; ++y) {
        for (std::size_t x = 0; x < z.nx; ++x) {
            std::array<double, 9> werte{};
            std::size_t k = 0;
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    werte[k++] = z.werte[nachbar(y, x, dy, dx)];
                }
            }
            std::sort(werte.begin(), werte.end());
            const auto i = y * z.nx + x;
            neu[i] = std::abs(z.werte[i] - werte[4]) > 2.5 * dx ? werte[4] : z.werte[i];
        }
    }
    z.werte.swap(neu);
    for (std::int64_t runde = 0; runde < durchlaeufe; ++runde) {
        for (std::size_t y = 0; y < z.ny; ++y) {
            for (std::size_t x = 0; x < z.nx; ++x) {
                double summe = 0.;
                for (int dy = -1; dy <= 1; ++dy) {
                    for (int dx = -1; dx <= 1; ++dx) {
                        if (dy || dx) { summe += z.werte[nachbar(y, x, dy, dx)]; }
                    }
                }
                const auto i = y * z.nx + x;
                neu[i] = z.werte[i] + .5 * (summe / 8. - z.werte[i]);
            }
        }
        z.werte.swap(neu);
    }
    return z;
}

inline std::pair<std::vector<Vektor3>, std::vector<std::array<std::int64_t, 4>>>
wasser_flaeche(const WasserRaster& x, const WasserRaster& y, const WasserRaster& z)
{
    if (x.nx != y.nx || x.nx != z.nx || x.ny != y.ny || x.ny != z.ny) {
        throw std::invalid_argument("Wasserflaechenraster muessen gleich gross sein");
    }
    std::vector<Vektor3> punkte;
    punkte.reserve(x.werte.size());
    for (std::size_t i = 0; i < x.werte.size(); ++i) {
        punkte.push_back({x.werte[i], y.werte[i], z.werte[i]});
    }
    std::vector<std::array<std::int64_t, 4>> faces;
    // Die historische meshgrid-Ausgabe ordnet zuerst x, dann y.
    for (std::size_t i = 0; i + 1 < x.nx; ++i) {
        for (std::size_t j = 0; j + 1 < x.ny; ++j) {
            const auto a = static_cast<std::int64_t>(j * x.nx + i);
            const auto b = a + 1, c = a + static_cast<std::int64_t>(x.nx), d = c + 1;
            faces.push_back({3, a, b, d});
            faces.push_back({3, a, d, c});
        }
    }
    return {punkte, faces};
}

inline std::vector<std::array<double, 2>> wasser_kreis(std::size_t anzahl)
{
    std::vector<std::array<double, 2>> punkte;
    punkte.reserve(anzahl);
    if (!anzahl) { return punkte; }
    const double schritt = 2. * std::acos(-1.) / static_cast<double>(anzahl);
    for (std::size_t i = 0; i < anzahl; ++i) {
        const double winkel = static_cast<double>(i) * schritt;
        punkte.push_back({std::cos(winkel), std::sin(winkel)});
    }
    return punkte;
}

} // namespace segelphysik
