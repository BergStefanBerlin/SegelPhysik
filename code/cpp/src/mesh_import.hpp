#pragma once

#include "ebenenschnitt.hpp"
#include <algorithm>
#include <numeric>

namespace segelphysik {

using PolygonPunkt = std::array<double, 2>;

inline double polygon_orientierung(const PolygonPunkt& a, const PolygonPunkt& b,
                                   const PolygonPunkt& c)
{
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
}

inline bool polygon_auf_strecke(const PolygonPunkt& a, const PolygonPunkt& b,
                               const PolygonPunkt& p, double tol)
{
    return p[0] >= std::min(a[0], b[0]) - tol && p[0] <= std::max(a[0], b[0]) + tol
        && p[1] >= std::min(a[1], b[1]) - tol && p[1] <= std::max(a[1], b[1]) + tol;
}

inline bool polygon_selbstschnitt(const std::vector<PolygonPunkt>& punkte, double tol)
{
    if (!std::isfinite(tol) || punkte.empty()) {
        throw std::invalid_argument("Polygon benoetigt endliche Punkte und Toleranz");
    }
    auto minimum = punkte[0], maximum = punkte[0];
    for (const auto& p : punkte) {
        endlich(p, "Polygonpunkt");
        for (std::size_t i = 0; i < 2; ++i) {
            minimum[i] = std::min(minimum[i], p[i]);
            maximum[i] = std::max(maximum[i], p[i]);
        }
    }
    const double flaeche = tol * std::max(
        std::max(maximum[0] - minimum[0], maximum[1] - minimum[1]), tol);
    const auto n = punkte.size();
    for (std::size_t i = 0; i < n; ++i) {
        const auto i2 = (i + 1) % n;
        for (std::size_t j = i + 1; j < n; ++j) {
            const auto j2 = (j + 1) % n;
            if (i2 == j || j2 == i) { continue; }
            const auto& a = punkte[i]; const auto& b = punkte[i2];
            const auto& c = punkte[j]; const auto& d = punkte[j2];
            const double o1 = polygon_orientierung(a, b, c), o2 = polygon_orientierung(a, b, d);
            const double o3 = polygon_orientierung(c, d, a), o4 = polygon_orientierung(c, d, b);
            if ((o1 * o2 < -flaeche * flaeche && o3 * o4 < -flaeche * flaeche)
                    || (std::abs(o1) <= flaeche && polygon_auf_strecke(a, b, c, tol))
                    || (std::abs(o2) <= flaeche && polygon_auf_strecke(a, b, d, tol))
                    || (std::abs(o3) <= flaeche && polygon_auf_strecke(c, d, a, tol))
                    || (std::abs(o4) <= flaeche && polygon_auf_strecke(c, d, b, tol))) {
                return true;
            }
        }
    }
    return false;
}

inline std::vector<std::array<std::int64_t, 3>> polygon_triangulieren(
        const std::vector<Vektor3>& punkte, const std::vector<std::int64_t>& index)
{
    const auto n = punkte.size();
    if (n < 4 || n != index.size()) {
        throw std::invalid_argument("Polygon hat weniger als 4 zugeordnete Eckpunkte");
    }
    auto minimum = punkte[0], maximum = punkte[0];
    double betrag = 1.;
    std::vector<Vektor3> verschoben;
    verschoben.reserve(n);
    for (const auto& p : punkte) {
        endlich(p, "Polygonpunkt");
        Vektor3 v{};
        for (std::size_t i = 0; i < 3; ++i) {
            minimum[i] = std::min(minimum[i], p[i]);
            maximum[i] = std::max(maximum[i], p[i]);
            betrag = std::max(betrag, std::abs(p[i]));
            v[i] = p[i] - punkte[0][i];
        }
        verschoben.push_back(v);
    }
    double spannweite = 0.;
    for (std::size_t i = 0; i < 3; ++i) {
        spannweite = std::max(spannweite, maximum[i] - minimum[i]);
    }
    const double tol = std::max(spannweite * 1e-10,
        std::numeric_limits<double>::epsilon() * betrag * 32.);
    Vektor3 normal{};
    for (std::size_t i = 0; i < n; ++i) {
        const auto kreuz = kreuzprodukt(verschoben[i], verschoben[(i + 1) % n]);
        for (std::size_t j = 0; j < 3; ++j) { normal[j] += kreuz[j]; }
    }
    const double norm = std::sqrt(skalarprodukt(normal, normal));
    if (!std::isfinite(norm) || norm <= tol * tol) {
        throw std::invalid_argument("Polygon ist entartet");
    }
    for (double& wert : normal) { wert /= norm; }
    for (const auto& p : verschoben) {
        if (std::abs(skalarprodukt(p, normal)) > std::max(tol * 100., spannweite * 1e-8)) {
            throw std::invalid_argument("nicht-planare OBJ-Polygone werden abgelehnt");
        }
    }
    std::size_t weg = 0;
    for (std::size_t i = 1; i < 3; ++i) {
        if (std::abs(normal[i]) > std::abs(normal[weg])) { weg = i; }
    }
    std::vector<PolygonPunkt> projektion;
    for (const auto& p : verschoben) {
        PolygonPunkt ziel{};
        std::size_t j = 0;
        for (std::size_t i = 0; i < 3; ++i) {
            if (i != weg) { ziel[j++] = p[i]; }
        }
        projektion.push_back(ziel);
    }
    if (polygon_selbstschnitt(projektion, tol)) {
        throw std::invalid_argument("selbstschneidendes OBJ-Polygon");
    }
    double links = 0., rechts = 0.;
    for (std::size_t i = 0; i < n; ++i) {
        links += projektion[i][0] * projektion[(i + 1) % n][1];
        rechts += projektion[i][1] * projektion[(i + 1) % n][0];
    }
    const double area2 = links - rechts;
    const double tol_flaeche = tol * std::max(spannweite, tol);
    if (std::abs(area2) <= tol_flaeche) {
        throw std::invalid_argument(u8"Polygonfl\u00e4che ist null");
    }
    const double richtung = area2 > 0. ? 1. : -1.;
    std::vector<std::size_t> rest(n);
    std::iota(rest.begin(), rest.end(), 0);
    std::vector<std::array<std::int64_t, 3>> dreiecke;
    while (rest.size() > 3) {
        bool ohr = false;
        for (std::size_t position = 0; position < rest.size(); ++position) {
            const auto mitte = rest[position], vorher = rest[(position + rest.size() - 1) % rest.size()];
            const auto nachher = rest[(position + 1) % rest.size()];
            const auto& a = projektion[vorher]; const auto& b = projektion[mitte];
            const auto& c = projektion[nachher];
            const double kreuz = polygon_orientierung(a, b, c);
            if (std::abs(kreuz) <= tol_flaeche) {
                if (polygon_auf_strecke(a, c, b, tol)) {
                    rest.erase(rest.begin() + position);
                    ohr = true;
                    break;
                }
                continue;
            }
            if (richtung * kreuz <= tol_flaeche) { continue; }
            bool innen = false;
            for (const auto kandidat : rest) {
                if (kandidat == vorher || kandidat == mitte || kandidat == nachher) { continue; }
                const auto& p = projektion[kandidat];
                if (richtung * polygon_orientierung(a, b, p) >= -tol_flaeche
                        && richtung * polygon_orientierung(b, c, p) >= -tol_flaeche
                        && richtung * polygon_orientierung(c, a, p) >= -tol_flaeche) {
                    innen = true;
                    break;
                }
            }
            if (innen) { continue; }
            dreiecke.push_back({index[vorher], index[mitte], index[nachher]});
            rest.erase(rest.begin() + position);
            ohr = true;
            break;
        }
        if (!ohr) {
            throw std::invalid_argument("OBJ-Polygon kann nicht sicher trianguliert werden");
        }
    }
    dreiecke.push_back({index[rest[0]], index[rest[1]], index[rest[2]]});
    return dreiecke;
}

inline std::vector<Vektor3> obj_transformieren(
        const std::vector<Vektor3>& punkte, const Matrix3& rotation, double skala)
{
    positiv(skala, "OBJ-Skalierung");
    rotation_pruefen(rotation);
    std::vector<Vektor3> ziel;
    ziel.reserve(punkte.size());
    for (auto punkt : punkte) {
        for (double& wert : punkt) { wert *= skala; }
        endlich(punkt, "Skalierter OBJ-Punkt");
        const auto gedreht = multiplizieren(rotation, punkt);
        endlich(gedreht, "Transformierter OBJ-Punkt");
        ziel.push_back(gedreht);
    }
    return ziel;
}

} // namespace segelphysik
