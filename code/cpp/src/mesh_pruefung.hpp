#pragma once

#include "frames.hpp"
#include <numeric>
#include <optional>

namespace segelphysik {

using DreieckPunkte = std::array<Vektor3, 3>;

inline Vektor3 differenz(const Vektor3& a, const Vektor3& b)
{
    return {a[0] - b[0], a[1] - b[1], a[2] - b[2]};
}

inline double vektorlaenge(const Vektor3& a)
{
    return std::sqrt(skalarprodukt(a, a));
}

inline bool segment_dreieck(
        const Vektor3& start, const Vektor3& ende, const DreieckPunkte& dreieck, double tol)
{
    const auto richtung = differenz(ende, start);
    const auto e1 = differenz(dreieck[1], dreieck[0]);
    const auto e2 = differenz(dreieck[2], dreieck[0]);
    const auto p = kreuzprodukt(richtung, e2);
    const double det = skalarprodukt(e1, p);
    const double skala = std::max(
        vektorlaenge(richtung) * vektorlaenge(e1) * vektorlaenge(e2), tol * tol * tol);
    if (std::abs(det) <= tol * skala) {
        return false;
    }
    const double inv = 1. / det;
    const auto versatz = differenz(start, dreieck[0]);
    const double u = skalarprodukt(versatz, p) * inv;
    const auto q = kreuzprodukt(versatz, e1);
    const double v = skalarprodukt(richtung, q) * inv;
    const double t = skalarprodukt(e2, q) * inv;
    const double bary = tol / std::max({vektorlaenge(e1), vektorlaenge(e2), tol});
    return u >= -bary && u <= 1. + bary && v >= -bary && u + v <= 1. + bary
        && t >= -bary && t <= 1. + bary;
}

inline bool koplanare_dreiecke(
        const DreieckPunkte& a, const DreieckPunkte& b, const Vektor3& normale, double tol)
{
    std::size_t entfernen = 0;
    for (std::size_t i = 1; i < 3; ++i) {
        if (std::abs(normale[i]) > std::abs(normale[entfernen])) {
            entfernen = i;
        }
    }
    std::array<std::size_t, 2> achsen{};
    std::size_t index = 0;
    for (std::size_t i = 0; i < 3; ++i) {
        if (i != entfernen) {
            achsen[index++] = i;
        }
    }
    for (const auto* dreieck : {&a, &b}) {
        for (std::size_t i = 0; i < 3; ++i) {
            const auto kante = differenz((*dreieck)[(i + 1) % 3], (*dreieck)[i]);
            const std::array<double, 2> achse{-kante[achsen[1]], kante[achsen[0]]};
            double amin = std::numeric_limits<double>::infinity(), amax = -amin;
            double bmin = amin, bmax = amax;
            for (std::size_t j = 0; j < 3; ++j) {
                const double pa = a[j][achsen[0]] * achse[0] + a[j][achsen[1]] * achse[1];
                const double pb = b[j][achsen[0]] * achse[0] + b[j][achsen[1]] * achse[1];
                amin = std::min(amin, pa); amax = std::max(amax, pa);
                bmin = std::min(bmin, pb); bmax = std::max(bmax, pb);
            }
            const double spiel = tol * std::sqrt(achse[0] * achse[0] + achse[1] * achse[1]);
            if (amax < bmin - spiel || bmax < amin - spiel) {
                return false;
            }
        }
    }
    return true;
}

inline bool dreiecke_schneiden(const DreieckPunkte& a, const DreieckPunkte& b, double tol)
{
    const auto na = kreuzprodukt(differenz(a[1], a[0]), differenz(a[2], a[0]));
    const auto nb = kreuzprodukt(differenz(b[1], b[0]), differenz(b[2], b[0]));
    const double la = vektorlaenge(na), lb = vektorlaenge(nb);
    positiv(la, "Dreiecksflaeche"); positiv(lb, "Dreiecksflaeche");
    std::array<double, 3> da{}, db{};
    for (std::size_t i = 0; i < 3; ++i) {
        db[i] = skalarprodukt(differenz(b[i], a[0]), na);
        da[i] = skalarprodukt(differenz(a[i], b[0]), nb);
    }
    auto ausserhalb = [&](const std::array<double, 3>& d, double l) {
        return std::all_of(d.begin(), d.end(), [&](double x) { return x > tol * l; })
            || std::all_of(d.begin(), d.end(), [&](double x) { return x < -tol * l; });
    };
    if (ausserhalb(da, lb) || ausserhalb(db, la)) {
        return false;
    }
    const bool koplanar = std::all_of(da.begin(), da.end(), [&](double x) {
        return std::abs(x) / lb <= tol;
    }) && std::all_of(db.begin(), db.end(), [&](double x) {
        return std::abs(x) / la <= tol;
    });
    if (koplanar) {
        return koplanare_dreiecke(a, b, na, tol);
    }
    for (std::size_t i = 0; i < 3; ++i) {
        if (segment_dreieck(a[i], a[(i + 1) % 3], b, tol)
                || segment_dreieck(b[i], b[(i + 1) % 3], a, tol)) {
            return true;
        }
    }
    return false;
}

inline std::optional<std::pair<std::size_t, std::size_t>> mesh_selbstschnitt(
        const Mesh& mesh, const Abbruch& abbruch)
{
    mesh.pruefen();
    if (mesh.punkte.empty() || mesh.dreiecke.empty()) {
        throw std::invalid_argument("Leeres Mesh");
    }
    Vektor3 pmin = mesh.punkte.front(), pmax = pmin;
    double betrag = 1.;
    for (const auto& p : mesh.punkte) {
        for (std::size_t i = 0; i < 3; ++i) {
            pmin[i] = std::min(pmin[i], p[i]); pmax[i] = std::max(pmax[i], p[i]);
            betrag = std::max(betrag, std::abs(p[i]));
        }
    }
    double ausdehnung = 0.;
    for (std::size_t i = 0; i < 3; ++i) {
        ausdehnung = std::max(ausdehnung, pmax[i] - pmin[i]);
    }
    endlich(std::array<double, 1>{ausdehnung}, "Mesh-Ausdehnung");
    const double tol = std::max(ausdehnung * 1e-12,
        std::numeric_limits<double>::epsilon() * betrag * 64.);
    const auto n = mesh.dreiecke.size();
    std::vector<DreieckPunkte> punkte(n);
    std::vector<Vektor3> minima(n), maxima(n);
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j < 3; ++j) {
            punkte[i][j] = mesh.punkte[mesh.dreiecke[i][j]];
        }
        positiv(vektorlaenge(kreuzprodukt(
            differenz(punkte[i][1], punkte[i][0]), differenz(punkte[i][2], punkte[i][0]))),
            "Dreiecksflaeche");
        minima[i] = maxima[i] = punkte[i][0];
        for (const auto& p : punkte[i]) {
            for (std::size_t k = 0; k < 3; ++k) {
                minima[i][k] = std::min(minima[i][k], p[k]);
                maxima[i][k] = std::max(maxima[i][k], p[k]);
            }
        }
    }
    std::vector<std::size_t> reihenfolge(n), aktiv;
    std::iota(reihenfolge.begin(), reihenfolge.end(), 0);
    std::stable_sort(reihenfolge.begin(), reihenfolge.end(), [&](auto a, auto b) {
        return minima[a][0] < minima[b][0];
    });
    for (auto index : reihenfolge) {
        abbruch.pruefen();
        aktiv.erase(std::remove_if(aktiv.begin(), aktiv.end(), [&](auto kandidat) {
            return maxima[kandidat][0] < minima[index][0] - tol;
        }), aktiv.end());
        for (auto kandidat : aktiv) {
            abbruch.pruefen();
            if (maxima[kandidat][1] < minima[index][1] - tol
                    || maxima[index][1] < minima[kandidat][1] - tol
                    || maxima[kandidat][2] < minima[index][2] - tol
                    || maxima[index][2] < minima[kandidat][2] - tol) {
                continue;
            }
            bool geteilt = false;
            for (auto a : mesh.dreiecke[kandidat]) {
                for (auto b : mesh.dreiecke[index]) {
                    geteilt = geteilt || a == b;
                }
            }
            if (!geteilt && dreiecke_schneiden(punkte[kandidat], punkte[index], tol)) {
                return std::make_pair(kandidat, index);
            }
        }
        aktiv.push_back(index);
    }
    return {};
}

} // namespace segelphysik
