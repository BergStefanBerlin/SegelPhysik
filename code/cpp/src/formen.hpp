#pragma once

#include "ebenenschnitt.hpp"

namespace segelphysik {

inline std::vector<Vektor3> form_ring(double r, double z, std::size_t n, double versatz)
{
    endlich(Vektor3{r, z, versatz}, "Ringparameter");
    std::vector<Vektor3> punkte;
    punkte.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        const double winkel = 2. * std::acos(-1.) * (static_cast<double>(i) + versatz)
            / static_cast<double>(n);
        punkte.push_back({r * std::cos(winkel), r * std::sin(winkel), z});
    }
    return punkte;
}

inline Vektor3 form_schwerpunkt(const Mesh& mesh)
{
    std::vector<double> volumen;
    Vektor3 moment{};
    for (const auto& f : mesh.dreiecke) {
        const auto& a = mesh.punkte[f[0]];
        const auto& b = mesh.punkte[f[1]];
        const auto& c = mesh.punkte[f[2]];
        const double v = skalarprodukt(a, kreuzprodukt(b, c)) / 6.;
        volumen.push_back(v);
        for (std::size_t i = 0; i < 3; ++i) {
            moment[i] += ((a[i] + b[i]) + c[i]) / 4. * v;
        }
    }
    const double gesamt = paarweise_summe(volumen.data(), volumen.size());
    if (std::abs(gesamt) < 1e-18) {
        throw std::invalid_argument("Koerper ohne Volumen");
    }
    for (double& wert : moment) { wert /= gesamt; }
    endlich(moment, "Formschwerpunkt");
    return moment;
}

inline Mesh form_zentrieren(Mesh mesh)
{
    const auto zentrum = form_schwerpunkt(mesh);
    for (auto& p : mesh.punkte) {
        for (std::size_t i = 0; i < 3; ++i) { p[i] -= zentrum[i]; }
        endlich(p, "Zentrierter Formpunkt");
    }
    return mesh;
}

inline void form_liegend(std::vector<Vektor3>& punkte)
{
    for (auto& p : punkte) {
        endlich(p, "Formpunkt");
        p = {p[2], p[1], -p[0]};
    }
}

struct FormHuellFlaeche {
    std::vector<std::int64_t> indices;
    std::vector<double> winkel;
    Vektor3 normale;
};

inline std::vector<FormHuellFlaeche> form_huellflaechen(
        const std::vector<Vektor3>& p, double tol)
{
    const auto n = p.size();
    if (n > 64) {
        throw std::invalid_argument("eckpunkte_m: hoechstens 64 Punkte ohne 'flaechen'");
    }
    if (!n || !std::isfinite(tol)) {
        throw std::invalid_argument("Ungueltige Huelleingabe");
    }
    auto minimum = p[0], maximum = p[0];
    for (const auto& punkt : p) {
        endlich(punkt, "Huellpunkt");
        for (std::size_t i = 0; i < 3; ++i) {
            minimum[i] = std::min(minimum[i], punkt[i]);
            maximum[i] = std::max(maximum[i], punkt[i]);
        }
    }
    double skala = 1e-12;
    for (std::size_t i = 0; i < 3; ++i) {
        skala = std::max(skala, maximum[i] - minimum[i]);
    }
    std::vector<FormHuellFlaeche> flaechen;
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i + 1; j < n; ++j) {
            for (std::size_t k = j + 1; k < n; ++k) {
                Vektor3 a{}, b{};
                for (std::size_t achse = 0; achse < 3; ++achse) {
                    a[achse] = p[j][achse] - p[i][achse];
                    b[achse] = p[k][achse] - p[i][achse];
                }
                auto normale = kreuzprodukt(a, b);
                const double norm = std::sqrt(skalarprodukt(normale, normale));
                if (norm == 0. || norm < tol * skala * skala) { continue; }
                for (double& wert : normale) { wert /= norm; }
                bool unten = true, oben = true;
                std::vector<double> abstaende;
                for (const auto& punkt : p) {
                    const Vektor3 d{punkt[0] - p[i][0], punkt[1] - p[i][1],
                        punkt[2] - p[i][2]};
                    const double s = skalarprodukt(d, normale);
                    abstaende.push_back(s);
                    unten = unten && s <= tol * skala;
                    oben = oben && s >= -tol * skala;
                }
                if (!unten && !oben) { continue; }
                if (!unten) {
                    for (double& wert : normale) { wert = -wert; }
                    for (double& wert : abstaende) { wert = -wert; }
                }
                std::vector<std::int64_t> indices;
                for (std::size_t index = 0; index < n; ++index) {
                    if (std::abs(abstaende[index]) <= tol * skala) {
                        indices.push_back(static_cast<std::int64_t>(index));
                    }
                }
                const bool vorhanden = std::any_of(flaechen.begin(), flaechen.end(),
                    [&](const auto& flaeche) { return flaeche.indices == indices; });
                if (!vorhanden) { flaechen.push_back({indices, {}, normale}); }
            }
        }
    }
    if (flaechen.empty()) {
        throw std::invalid_argument("eckpunkte_m: Punkte liegen in einer Ebene");
    }
    for (auto& flaeche : flaechen) {
        Vektor3 mitte{};
        for (const auto index : flaeche.indices) {
            for (std::size_t i = 0; i < 3; ++i) { mitte[i] += p[index][i]; }
        }
        for (double& wert : mitte) { wert /= static_cast<double>(flaeche.indices.size()); }
        Vektor3 u{};
        for (std::size_t i = 0; i < 3; ++i) { u[i] = p[flaeche.indices[0]][i] - mitte[i]; }
        const double projektion = skalarprodukt(u, flaeche.normale);
        for (std::size_t i = 0; i < 3; ++i) { u[i] -= flaeche.normale[i] * projektion; }
        const double norm = std::sqrt(skalarprodukt(u, u));
        if (!std::isfinite(norm) || norm == 0.) {
            throw std::invalid_argument("Huellflaeche besitzt keine eindeutige Winkelbasis");
        }
        for (double& wert : u) { wert /= norm; }
        const auto w = kreuzprodukt(flaeche.normale, u);
        for (const auto index : flaeche.indices) {
            const Vektor3 d{p[index][0] - mitte[0], p[index][1] - mitte[1],
                p[index][2] - mitte[2]};
            flaeche.winkel.push_back(std::atan2(skalarprodukt(d, w), skalarprodukt(d, u)));
        }
    }
    return flaechen;
}

inline std::vector<std::array<std::int64_t, 3>> form_faecher(
        const std::vector<std::vector<std::int64_t>>& flaechen)
{
    std::vector<std::array<std::int64_t, 3>> dreiecke;
    for (const auto& poly : flaechen) {
        if (poly.size() < 3) { throw std::invalid_argument("flaechen: ungueltiger Index"); }
        for (std::size_t i = 1; i + 1 < poly.size(); ++i) {
            dreiecke.push_back({poly[0], poly[i], poly[i + 1]});
        }
    }
    return dreiecke;
}

inline std::vector<std::array<std::int64_t, 3>> form_huelldreiecke(
        const std::vector<Vektor3>& p, const std::vector<std::vector<std::int64_t>>& ordnungen)
{
    if (p.empty()) { throw std::invalid_argument("Huelle benoetigt Punkte"); }
    auto dreiecke = form_faecher(ordnungen);
    Vektor3 mitte{};
    for (const auto& punkt : p) {
        endlich(punkt, "Huellpunkt");
        for (std::size_t i = 0; i < 3; ++i) { mitte[i] += punkt[i]; }
    }
    for (double& wert : mitte) { wert /= static_cast<double>(p.size()); }
    for (auto& f : dreiecke) {
        for (const auto index : f) {
            if (index < 0 || static_cast<std::uint64_t>(index) >= p.size()) {
                throw std::invalid_argument("Huellindex ausserhalb des Punktarrays");
            }
        }
        Vektor3 b{}, c{}, d{};
        for (std::size_t i = 0; i < 3; ++i) {
            b[i] = p[f[1]][i] - p[f[0]][i];
            c[i] = p[f[2]][i] - p[f[0]][i];
            d[i] = p[f[0]][i] - mitte[i];
        }
        if (skalarprodukt(kreuzprodukt(b, c), d) < 0.) { std::swap(f[1], f[2]); }
    }
    return dreiecke;
}

inline Mesh form_mesh(int typ, const Vektor3& parameter, std::size_t nseg, bool liegend)
{
    endlich(parameter, "Formparameter");
    Mesh mesh{};
    auto& p = mesh.punkte;
    auto& f = mesh.dreiecke;
    const double a = parameter[0], b = parameter[1], c = parameter[2];
    if (nseg > (static_cast<std::size_t>(std::numeric_limits<std::int64_t>::max()) - 2) / 2) {
        throw std::overflow_error("Zu viele Formsegmente");
    }
    const auto n = static_cast<std::int64_t>(nseg);
    if (typ == 0) {
        if (a <= 0. || b <= 0. || nseg < 3) {
            throw std::invalid_argument("H>0, R>0, nseg>=3 erforderlich");
        }
        p = form_ring(b, -a / 4., nseg, 0.);
        p.push_back({0., 0., 3. * a / 4.});
        p.push_back({0., 0., -a / 4.});
        for (std::int64_t i = 0; i < n; ++i) { f.push_back({i, (i + 1) % n, n}); }
        for (std::int64_t i = 0; i < n; ++i) { f.push_back({n + 1, (i + 1) % n, i}); }
    } else if (typ == 1) {
        if (a <= 0. || b <= 0. || c <= 0.) {
            throw std::invalid_argument("dx, dy, dz > 0 erforderlich");
        }
        const double x = a / 2., y = b / 2., z = c / 2.;
        p = {{-x, -y, -z}, {x, -y, -z}, {x, y, -z}, {-x, y, -z},
             {-x, -y, z}, {x, -y, z}, {x, y, z}, {-x, y, z}};
        const std::array<std::array<std::int64_t, 4>, 6> quads{{
            {0, 3, 2, 1}, {4, 5, 6, 7}, {0, 1, 5, 4},
            {2, 3, 7, 6}, {1, 2, 6, 5}, {3, 0, 4, 7}}};
        for (const auto& q : quads) {
            f.push_back({q[0], q[1], q[2]}); f.push_back({q[0], q[2], q[3]});
        }
    } else if (typ == 2) {
        if (a <= 0. || b <= 0.) {
            throw std::invalid_argument("a>0, H>0 erforderlich");
        }
        const double h = a / 2., zb = -b / 4., zt = 3. * b / 4.;
        p = {{-h, -h, zb}, {h, -h, zb}, {h, h, zb}, {-h, h, zb}, {0., 0., zt}};
        f = {{0, 1, 4}, {1, 2, 4}, {2, 3, 4}, {3, 0, 4}, {0, 3, 2}, {0, 2, 1}};
    } else if (typ == 3) {
        if (a <= 0. || nseg < 6) {
            throw std::invalid_argument("R>0, nseg>=6 erforderlich");
        }
        const auto ringe = n / 2 - 1;
        p.push_back({0., 0., a});
        for (std::int64_t i = 1; i <= ringe; ++i) {
            const double theta = std::acos(-1.) * static_cast<double>(i)
                / static_cast<double>(ringe + 1);
            const auto ring = form_ring(a * std::sin(theta), a * std::cos(theta), nseg, 0.);
            p.insert(p.end(), ring.begin(), ring.end());
        }
        p.push_back({0., 0., -a});
        const auto sued = static_cast<std::int64_t>(p.size()) - 1;
        for (std::int64_t i = 0; i < n; ++i) { f.push_back({0, 1 + i, 1 + (i + 1) % n}); }
        for (std::int64_t r = 0; r < ringe - 1; ++r) {
            const auto o = 1 + r * n, u = 1 + (r + 1) * n;
            for (std::int64_t i = 0; i < n; ++i) {
                const auto j = (i + 1) % n;
                f.push_back({o + i, u + i, u + j});
                f.push_back({o + i, u + j, o + j});
            }
        }
        const auto u = 1 + (ringe - 1) * n;
        for (std::int64_t i = 0; i < n; ++i) { f.push_back({u + (i + 1) % n, u + i, sued}); }
    } else if (typ == 4 || typ == 5) {
        if (typ == 4 && (a <= 0. || b <= 0. || nseg < 3)) {
            throw std::invalid_argument("R>0, H>0, nseg>=3 erforderlich");
        }
        if (typ == 5 && (a <= 0. || b <= 0. || c < 0. || c >= b)) {
            throw std::invalid_argument("umkreisradius>0, H>0, 0<=spitzenlaenge<H erforderlich");
        }
        const auto segmente = typ == 5 ? std::int64_t(6) : n;
        const double unten = typ == 5 ? 0. : -b / 2.;
        const double oben = typ == 5 ? b - c : b / 2.;
        p = form_ring(a, unten, segmente, 0.);
        const auto ring = form_ring(a, oben, segmente, 0.);
        p.insert(p.end(), ring.begin(), ring.end());
        p.push_back({0., 0., unten});
        p.push_back({0., 0., typ == 5 ? b : oben});
        for (std::int64_t i = 0; i < segmente; ++i) {
            const auto j = (i + 1) % segmente;
            f.push_back({i, j, segmente + j});
            f.push_back({i, segmente + j, segmente + i});
            f.push_back({2 * segmente, j, i});
            f.push_back({2 * segmente + 1, segmente + i, segmente + j});
        }
        if (typ == 5) { mesh = form_zentrieren(std::move(mesh)); }
        if (liegend) { form_liegend(mesh.punkte); }
    } else {
        throw std::invalid_argument("Unbekannter nativer Formtyp");
    }
    mesh.pruefen();
    return mesh;
}

} // namespace segelphysik
