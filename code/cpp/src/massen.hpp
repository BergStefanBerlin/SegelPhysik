#pragma once

#include "ebenenschnitt.hpp"

namespace segelphysik {

inline std::pair<Vektor3, double> massenschwerpunkt(const Mesh& mesh, bool schale)
{
    if (mesh.dreiecke.empty()) {
        throw std::invalid_argument("Leeres Mesh");
    }
    std::vector<double> gewichte;
    gewichte.reserve(mesh.dreiecke.size());
    Vektor3 moment{};
    for (const auto& tri : mesh.dreiecke) {
        const auto& a = mesh.punkte[tri[0]];
        const auto& b = mesh.punkte[tri[1]];
        const auto& c = mesh.punkte[tri[2]];
        Vektor3 ab{}, ac{};
        for (std::size_t i = 0; i < 3; ++i) {
            ab[i] = b[i] - a[i]; ac[i] = c[i] - a[i];
        }
        const auto kreuz = kreuzprodukt(ab, ac);
        const double gewicht = schale
            ? .5 * std::sqrt(skalarprodukt(kreuz, kreuz))
            : skalarprodukt(a, kreuzprodukt(b, c));
        gewichte.push_back(gewicht);
        for (std::size_t i = 0; i < 3; ++i) {
            moment[i] += ((a[i] + b[i]) + c[i]) / (schale ? 3. : 4.) * gewicht;
        }
    }
    const double gesamt = paarweise_summe(gewichte.data(), gewichte.size());
    if ((schale ? gesamt : std::abs(gesamt)) < 1e-300) {
        throw std::invalid_argument(schale ? "Mesh hat keine Flaeche"
            : "Volumen null (Flaechen-Mesh?): schwerpunkt_flaechig nutzen");
    }
    for (double& wert : moment) {
        wert /= gesamt;
    }
    endlich(moment, "Massenschwerpunkt");
    return {moment, schale ? gesamt : gesamt / 6.};
}

inline double mesh_flaeche(const Mesh& mesh)
{
    if (mesh.dreiecke.empty()) {
        return 0.;
    }
    // Degenerierte Dreiecke haben Flaeche null, auch wenn das ganze Mesh degeneriert ist.
    std::vector<double> werte;
    werte.reserve(mesh.dreiecke.size());
    for (const auto& tri : mesh.dreiecke) {
        Vektor3 ab{}, ac{};
        for (std::size_t i = 0; i < 3; ++i) {
            ab[i] = mesh.punkte[tri[1]][i] - mesh.punkte[tri[0]][i];
            ac[i] = mesh.punkte[tri[2]][i] - mesh.punkte[tri[0]][i];
        }
        const auto kreuz = kreuzprodukt(ab, ac);
        werte.push_back(std::sqrt(skalarprodukt(kreuz, kreuz)));
    }
    const double flaeche = .5 * paarweise_summe(werte.data(), werte.size());
    if (!std::isfinite(flaeche)) {
        throw std::invalid_argument("Meshflaeche ist nicht endlich");
    }
    return flaeche;
}

inline Matrix3 massentraegheit(const Mesh& mesh, double dichte, bool schale)
{
    endlich(std::array<double, 1>{dichte}, "Dichte");
    const auto schwerpunkt = massenschwerpunkt(mesh, schale);
    Matrix3 moment{};
    for (const auto& tri : mesh.dreiecke) {
        Vektor3 a = mesh.punkte[tri[0]], b = mesh.punkte[tri[1]], c = mesh.punkte[tri[2]];
        if (schale) {
            for (std::size_t i = 0; i < 3; ++i) {
                a[i] -= schwerpunkt.first[i];
                b[i] -= schwerpunkt.first[i];
                c[i] -= schwerpunkt.first[i];
            }
        }
        Vektor3 ab{}, ac{}, g{};
        for (std::size_t i = 0; i < 3; ++i) {
            ab[i] = b[i] - a[i]; ac[i] = c[i] - a[i];
            g[i] = ab[i] * (1. / 6.) + ac[i] * (1. / 6.);
        }
        const auto kreuz = kreuzprodukt(ab, ac);
        const double gewicht = schale ? .5 * std::sqrt(skalarprodukt(kreuz, kreuz))
            : skalarprodukt(a, kreuzprodukt(b, c)) / 6.;
        for (std::size_t i = 0; i < 3; ++i) {
            for (std::size_t j = 0; j < 3; ++j) {
                double wert;
                if (schale) {
                    const double bub = ab[i] * (1. / 12.) * ab[j]
                        + ab[i] * (1. / 24.) * ac[j]
                        + ac[i] * (1. / 24.) * ab[j]
                        + ac[i] * (1. / 12.) * ac[j];
                    wert = gewicht * a[i] * a[j]
                        + (2. * gewicht) * (a[i] * g[j] + g[i] * a[j])
                        + (2. * gewicht) * bub;
                } else {
                    const double s = a[i] * a[j] + b[i] * b[j] + c[i] * c[j];
                    const double kreuzterm = (a[i] * b[j] + b[i] * a[j])
                        + (a[i] * c[j] + c[i] * a[j]) + (b[i] * c[j] + c[i] * b[j]);
                    wert = gewicht * (s / 10. + kreuzterm / 20.);
                }
                moment[3 * i + j] += wert;
            }
        }
    }
    for (double& wert : moment) {
        wert *= dichte;
    }
    const double spur = moment[0] + moment[4] + moment[8];
    Matrix3 tensor{};
    const auto& r = schwerpunkt.first;
    const double masse = dichte * std::abs(schwerpunkt.second);
    for (std::size_t i = 0; i < 3; ++i) {
        for (std::size_t j = 0; j < 3; ++j) {
            tensor[3 * i + j] = (i == j ? spur : 0.) - moment[3 * i + j];
            if (!schale) {
                tensor[3 * i + j] -= masse * (
                    (i == j ? skalarprodukt(r, r) : 0.) - r[i] * r[j]);
            }
        }
    }
    endlich(tensor, "Traegheitstensor");
    return tensor;
}

} // namespace segelphysik
