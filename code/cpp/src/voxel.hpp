#pragma once

#include "datentypen.hpp"
#include <algorithm>
#include <limits>

namespace segelphysik {

inline std::vector<double> voxel_paare_bereit(std::vector<double> schnitte)
{
    while (schnitte.size() % 2) {
        if (schnitte.size() < 4) { return {}; }
        schnitte = std::vector<double>(schnitte.begin() + 1, schnitte.end() - 1);
    }
    return schnitte;
}

inline std::vector<std::array<double, 2>> voxel_intervalle(
        const std::vector<Vektor3>& punkte,
        const std::vector<std::array<std::int64_t, 3>>& dreiecke,
        double x, double z)
{
    std::vector<double> schnitte;
    for (const auto& f : dreiecke) {
        for (const auto index : f) {
            if (index < 0 || static_cast<std::uint64_t>(index) >= punkte.size()) {
                throw std::invalid_argument("Dreiecksindex ausserhalb des Punktarrays");
            }
        }
        const auto& p0 = punkte[f[0]];
        const auto& p1 = punkte[f[1]];
        const auto& p2 = punkte[f[2]];
        const double d = (p1[0] - p0[0]) * (p2[2] - p0[2])
            - (p2[0] - p0[0]) * (p1[2] - p0[2]);
        if (std::abs(d) < 1e-15) { continue; }
        const double w1 = ((x - p0[0]) * (p2[2] - p0[2])
            - (p2[0] - p0[0]) * (z - p0[2])) / d;
        const double w2 = ((p1[0] - p0[0]) * (z - p0[2])
            - (x - p0[0]) * (p1[2] - p0[2])) / d;
        if (w1 < -1e-12 || w2 < -1e-12 || w1 + w2 > 1. + 1e-12) {
            continue;
        }
        schnitte.push_back(p0[1] + w1 * (p1[1] - p0[1])
            + w2 * (p2[1] - p0[1]));
    }
    std::sort(schnitte.begin(), schnitte.end());
    std::vector<double> gedichtet;
    for (const auto wert : schnitte) {
        if (gedichtet.empty() || wert - gedichtet.back() > 1e-9) {
            gedichtet.push_back(wert);
        }
    }
    schnitte = voxel_paare_bereit(std::move(gedichtet));
    std::vector<std::array<double, 2>> intervalle;
    intervalle.reserve(schnitte.size() / 2);
    for (std::size_t i = 0; i < schnitte.size(); i += 2) {
        intervalle.push_back({schnitte[i], schnitte[i + 1]});
    }
    return intervalle;
}

struct VoxelSaeule {
    double x, z;
    std::vector<double> y, praefix;
};

class VoxelKontext {
public:
    VoxelKontext(std::vector<double> xs, std::vector<double> zs,
                 std::vector<std::int64_t> offsets,
                 std::vector<double> ys, std::vector<double> praefix,
                 double aufloesung)
        : aufloesung_(aufloesung)
    {
        positiv(aufloesung_, "Aufloesung");
        if (xs.size() != zs.size() || offsets.size() != xs.size() + 1
                || offsets.empty() || offsets.front() != 0
                || offsets.back() < 0
                || static_cast<std::uint64_t>(offsets.back()) != ys.size()
                || praefix.size() != ys.size() + xs.size()) {
            throw std::invalid_argument("Ungueltige Voxelspalten");
        }
        saeulen_.reserve(xs.size());
        for (std::size_t i = 0; i < xs.size(); ++i) {
            if (offsets[i] < 0 || offsets[i + 1] < offsets[i]
                    || static_cast<std::uint64_t>(offsets[i + 1]) > ys.size()) {
                throw std::invalid_argument("Ungueltige Voxelspaltenoffsets");
            }
            const auto start = static_cast<std::size_t>(offsets[i]);
            const auto ende = static_cast<std::size_t>(offsets[i + 1]);
            const auto praefix_start = start + i;
            VoxelSaeule saeule{xs[i], zs[i], {}, {}};
            saeule.y.assign(ys.begin() + start, ys.begin() + ende);
            saeule.praefix.assign(
                praefix.begin() + praefix_start,
                praefix.begin() + praefix_start + (ende - start) + 1);
            saeulen_.push_back(std::move(saeule));
        }
    }

    std::pair<double, Vektor3> auswerten(const Matrix3& rotation,
                                         const Vektor3& position) const
    {
        endlich(rotation, "Voxelrotation");
        endlich(position, "Voxelposition");
        if (saeulen_.empty()) { return {0., {0., 0., 0.}}; }
        const Vektor3 normale{rotation[6], rotation[7], rotation[8]};
        const double gradient = normale[1];
        const double gradient_toleranz =
            32. * std::numeric_limits<double>::epsilon();
        std::size_t nasse_anzahl = 0;
        Vektor3 summe{};
        for (const auto& saeule : saeulen_) {
            const double basis = normale[0] * saeule.x
                + normale[2] * saeule.z + position[2];
            if (std::abs(gradient) <= gradient_toleranz) {
                if (basis <= 0.) {
                    const auto anzahl = saeule.y.size();
                    nasse_anzahl += anzahl;
                    summe[0] += saeule.x * static_cast<double>(anzahl);
                    summe[1] += saeule.praefix.empty() ? 0. : saeule.praefix.back();
                    summe[2] += saeule.z * static_cast<double>(anzahl);
                }
                continue;
            }
            const double grenze = -basis / gradient;
            if (gradient > 0.) {
                const auto ende = static_cast<std::size_t>(
                    std::upper_bound(saeule.y.begin(), saeule.y.end(), grenze)
                    - saeule.y.begin());
                if (ende) {
                    nasse_anzahl += ende;
                    summe[0] += saeule.x * static_cast<double>(ende);
                    summe[1] += saeule.praefix[ende];
                    summe[2] += saeule.z * static_cast<double>(ende);
                }
            } else {
                const auto anfang = static_cast<std::size_t>(
                    std::lower_bound(saeule.y.begin(), saeule.y.end(), grenze)
                    - saeule.y.begin());
                if (anfang < saeule.y.size()) {
                    const auto anzahl = saeule.y.size() - anfang;
                    nasse_anzahl += anzahl;
                    summe[0] += saeule.x * static_cast<double>(anzahl);
                    summe[1] += saeule.praefix.back() - saeule.praefix[anfang];
                    summe[2] += saeule.z * static_cast<double>(anzahl);
                }
            }
        }
        if (!nasse_anzahl) { return {0., {0., 0., 0.}}; }
        const double anzahl = static_cast<double>(nasse_anzahl);
        const Vektor3 lokal{summe[0] / anzahl, summe[1] / anzahl,
                            summe[2] / anzahl};
        Vektor3 welt{};
        for (std::size_t i = 0; i < 3; ++i) {
            welt[i] = (rotation[3 * i] * lokal[0]
                + rotation[3 * i + 1] * lokal[1]
                + rotation[3 * i + 2] * lokal[2]) + position[i];
        }
        const double volumen = anzahl * std::pow(aufloesung_, 3.);
        if (!std::isfinite(volumen)) {
            throw std::invalid_argument("Rasterauswertung ergab nicht-endliche Werte");
        }
        endlich(welt, "Rasterauswertung");
        return {volumen, welt};
    }

private:
    double aufloesung_;
    std::vector<VoxelSaeule> saeulen_;
};

} // namespace segelphysik
