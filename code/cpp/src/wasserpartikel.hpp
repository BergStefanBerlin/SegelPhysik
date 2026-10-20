#pragma once

#include "datentypen.hpp"
#include <algorithm>
#include <limits>
#include <optional>

namespace segelphysik {

inline std::vector<Vektor3> wasser_spiegeln(
        const std::vector<Vektor3>& punkte, double lx, double ly,
        double tiefe, double cell, double kr)
{
    std::vector<Vektor3> ausgabe = punkte;
    std::vector<Vektor3> aktuell = punkte;
    auto spiegeln = [&](std::size_t achse, double wand) {
        std::vector<Vektor3> gespiegelt;
        for (const auto& punkt : aktuell) {
            if (std::abs(punkt[achse] - wand) <= kr + cell) {
                auto neu = punkt;
                neu[achse] = 2. * wand - neu[achse];
                gespiegelt.push_back(neu);
            }
        }
        ausgabe.insert(ausgabe.end(), gespiegelt.begin(), gespiegelt.end());
        aktuell.insert(aktuell.end(), gespiegelt.begin(), gespiegelt.end());
    };
    spiegeln(0, -lx * .5);
    spiegeln(0, lx * .5);
    spiegeln(1, -ly * .5);
    spiegeln(1, ly * .5);
    std::vector<Vektor3> boden;
    for (const auto& punkt : aktuell) {
        if (std::abs(punkt[2] + tiefe) <= kr + cell) {
            auto neu = punkt;
            neu[2] = -2. * tiefe - neu[2];
            boden.push_back(neu);
        }
    }
    ausgabe.insert(ausgabe.end(), boden.begin(), boden.end());
    return ausgabe;
}

inline std::int64_t raster_index(double wert)
{
    if (!std::isfinite(wert)
            || wert < static_cast<double>(std::numeric_limits<std::int64_t>::min())
            || wert >= static_cast<double>(std::numeric_limits<std::int64_t>::max())) {
        return std::numeric_limits<std::int64_t>::min();
    }
    return static_cast<std::int64_t>(wert);
}

inline std::vector<float> wasser_splat(
        const std::vector<Vektor3>& punkte,
        const std::vector<std::array<std::int64_t, 3>>& offsets,
        std::size_t nx, std::size_t ny, std::size_t nz,
        double lx, double ly, double tiefe, double cell, double kr)
{
    if (nx && ny > std::numeric_limits<std::size_t>::max() / nx) {
        throw std::overflow_error("Wasserraster ist zu gross");
    }
    const auto nxy = nx * ny;
    if (nz && nxy > std::numeric_limits<std::size_t>::max() / nz) {
        throw std::overflow_error("Wasserraster ist zu gross");
    }
    const auto groesse = nxy * nz;
    std::vector<double> summe(groesse, 0.);
    const double inv = 1. / cell;
    for (const auto& punkt : punkte) {
        const double fx = (punkt[0] + lx * .5) * inv;
        const double fy = (punkt[1] + ly * .5) * inv;
        const double fz = (punkt[2] + tiefe) * inv;
        const auto cx = raster_index(fx), cy = raster_index(fy), cz = raster_index(fz);
        for (const auto& offset : offsets) {
            const auto index = [&](std::int64_t mitte, std::int64_t delta,
                                   std::size_t limit) {
                if (mitte == std::numeric_limits<std::int64_t>::min()
                        || (delta > 0 && mitte > std::numeric_limits<std::int64_t>::max() - delta)
                        || (delta < 0 && mitte < std::numeric_limits<std::int64_t>::min() - delta)) {
                    return std::numeric_limits<std::size_t>::max();
                }
                const auto wert = mitte + delta;
                return wert < 0 || static_cast<std::uint64_t>(wert) >= limit
                    ? std::numeric_limits<std::size_t>::max()
                    : static_cast<std::size_t>(wert);
            };
            const auto i = index(cx, offset[0], nx), j = index(cy, offset[1], ny);
            const auto k = index(cz, offset[2], nz);
            if (i >= nx || j >= ny || k >= nz) { continue; }
            const double qx = std::abs((static_cast<double>(i) - fx) * cell) / kr;
            const double qy = std::abs((static_cast<double>(j) - fy) * cell) / kr;
            const double qz = std::abs((static_cast<double>(k) - fz) * cell) / kr;
            const double ux = 1. - qx * qx, uy = 1. - qy * qy, uz = 1. - qz * qz;
            const double wx = qx >= 1. ? 0. : ux * ux;
            const double wy = qy >= 1. ? 0. : uy * uy;
            const double wz = qz >= 1. ? 0. : uz * uz;
            const float gewicht = static_cast<float>((wx * wy) * wz);
            if (gewicht > 0.f) {
                summe[(i * ny + j) * nz + k] += static_cast<double>(gewicht);
            }
        }
    }
    std::vector<float> raster(groesse);
    std::transform(summe.begin(), summe.end(), raster.begin(),
        [](double wert) { return static_cast<float>(wert); });
    if (nx > 2) {
        for (std::size_t j = 0; j < ny; ++j) {
            for (std::size_t k = 0; k < nz; ++k) {
                raster[(j * nz) + k] = raster[((ny + j) * nz) + k];
                raster[((nx - 1) * ny + j) * nz + k] =
                    raster[((nx - 2) * ny + j) * nz + k];
            }
        }
    }
    if (ny > 2) {
        for (std::size_t i = 0; i < nx; ++i) {
            for (std::size_t k = 0; k < nz; ++k) {
                raster[(i * ny) * nz + k] = raster[(i * ny + 1) * nz + k];
                raster[(i * ny + ny - 1) * nz + k] =
                    raster[(i * ny + ny - 2) * nz + k];
            }
        }
    }
    if (nz > 2) {
        for (std::size_t i = 0; i < nx; ++i) {
            for (std::size_t j = 0; j < ny; ++j) {
                raster[(i * ny + j) * nz] = raster[(i * ny + j) * nz + 1];
            }
        }
    }
    return raster;
}

inline std::optional<double> wasser_kalibrieren(
        const std::vector<float>& raster, std::size_t nx,
        std::size_t ny, std::size_t nz)
{
    std::vector<float> werte;
    const auto x0 = std::min<std::size_t>(3, nx);
    const auto x1 = std::min<std::size_t>(std::max<std::size_t>(4, nx - std::min<std::size_t>(3, nx)), nx);
    const auto y0 = std::min<std::size_t>(3, ny);
    const auto y1 = std::min<std::size_t>(std::max<std::size_t>(4, ny - std::min<std::size_t>(3, ny)), ny);
    const auto z1 = std::min<std::size_t>(std::max<std::size_t>(2, nz / 3), nz);
    for (std::size_t i = x0; i < x1; ++i) {
        for (std::size_t j = y0; j < y1; ++j) {
            for (std::size_t k = 0; k < z1; ++k) {
                const float wert = raster[(i * ny + j) * nz + k];
                if (wert > 0.f) { werte.push_back(wert); }
            }
        }
    }
    if (werte.size() < 20) { return std::nullopt; }
    const auto mitte = werte.size() / 2;
    std::nth_element(werte.begin(), werte.begin() + mitte, werte.end());
    float median = werte[mitte];
    if (werte.size() % 2 == 0) {
        const auto untere = *std::max_element(werte.begin(), werte.begin() + mitte);
        median = (untere + median) / 2.f;
    }
    return median > 1e-6f
        ? std::optional<double>{static_cast<double>(median)} : std::nullopt;
}

} // namespace segelphysik
