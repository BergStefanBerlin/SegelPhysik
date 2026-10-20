#pragma once

#include "wasserschnitt.hpp"

namespace segelphysik {

inline double ittc_reibungsbeiwert(double reynolds)
{
    if (!std::isfinite(reynolds) || reynolds < 0.) {
        throw std::invalid_argument("Reynolds-Zahl muss endlich und nicht-negativ sein");
    }
    if (reynolds == 0.) {
        return 0.;
    }
    const double laminar = 1.328 / std::sqrt(reynolds);
    if (reynolds <= 1e5) {
        return laminar;
    }
    const double logarithmus = std::log10(reynolds);
    const double turbulent = .075 / ((logarithmus - 2.) * (logarithmus - 2.));
    if (reynolds >= 5e5) {
        return turbulent;
    }
    double anteil = (logarithmus - 5.) / (std::log10(5e5) - 5.);
    anteil = anteil * anteil * (3. - 2. * anteil);
    return (1. - anteil) * laminar + anteil * turbulent;
}

inline double benetzungsanteil(const std::array<Vektor3, 3>& ecken)
{
    unsigned nass = 0;
    std::array<double, 3> tiefen{}, trocken{};
    for (std::size_t i = 0; i < 3; ++i) {
        tiefen[i] = std::max(-ecken[i][2], 0.);
        trocken[i] = std::max(ecken[i][2], 0.);
        nass += tiefen[i] > 0.;
    }
    if (nass == 3) {
        return 1.;
    }
    if (nass == 0) {
        return 0.;
    }
    std::size_t index = 0;
    while ((tiefen[index] > 0.) != (nass == 1)) {
        ++index;
    }
    const double hoehe = nass == 1 ? tiefen[index] : trocken[index];
    double produkt = 1.;
    for (std::size_t i = 0; i < 3; ++i) {
        const double gegenhoehe = nass == 1 ? trocken[i] : tiefen[i];
        const double nenner = hoehe + gegenhoehe;
        produkt *= nenner > 0. ? hoehe / nenner : 0.;
    }
    return nass == 1 ? produkt : 1. - produkt;
}

struct HydroTeil {
    Mesh mesh;
    std::vector<std::array<Vektor3, 3>> ecken;
    std::vector<Vektor3> normalen, mittelpunkte;
    std::vector<double> flaechen;
    double oberflaeche{}, planform{}, spannweite{}, laenge{};

    explicit HydroTeil(Mesh eingabe) : mesh(std::move(eingabe))
    {
        mesh.pruefen();
        if (mesh.punkte.empty() || mesh.dreiecke.empty()) {
            throw std::invalid_argument("Hydrodynamikteil braucht Punkte und Dreiecke");
        }
        double min_x = mesh.punkte[0][0], max_x = min_x;
        double min_z = mesh.punkte[0][2], max_z = min_z;
        for (const auto& p : mesh.punkte) {
            min_x = std::min(min_x, p[0]); max_x = std::max(max_x, p[0]);
            min_z = std::min(min_z, p[2]); max_z = std::max(max_z, p[2]);
        }
        laenge = std::max(max_x - min_x, .05);
        spannweite = max_z - min_z;
        std::vector<double> projektionen;
        for (const auto& tri : mesh.dreiecke) {
            std::array<Vektor3, 3> e{mesh.punkte[tri[0]], mesh.punkte[tri[1]], mesh.punkte[tri[2]]};
            Vektor3 ab{}, ac{}, mitte{};
            for (std::size_t i = 0; i < 3; ++i) {
                ab[i] = e[1][i] - e[0][i];
                ac[i] = e[2][i] - e[0][i];
                mitte[i] = ((e[0][i] + e[1][i]) + e[2][i]) / 3.;
            }
            auto normale = kreuzprodukt(ab, ac);
            const double doppelt = std::sqrt(skalarprodukt(normale, normale));
            if (doppelt > 1e-15) {
                for (double& wert : normale) {
                    wert /= doppelt;
                }
            } else {
                normale = {};
            }
            ecken.push_back(e);
            normalen.push_back(normale);
            mittelpunkte.push_back(mitte);
            flaechen.push_back(.5 * doppelt);
            projektionen.push_back(doppelt * std::abs(normale[1]));
        }
        oberflaeche = paarweise_summe(flaechen.data(), flaechen.size());
        planform = .5 * paarweise_summe(projektionen.data(), projektionen.size());
    }
};

struct HydroKontext {
    std::vector<HydroTeil> teile;

    explicit HydroKontext(std::vector<HydroTeil> eingabe)
        : teile(std::move(eingabe)) {}
};

inline std::vector<Beitrag> hydrodynamik_beitraege(
        const std::vector<HydroTeil>& teile, const Matrix3& rotation,
        const Vektor3& position, const Vektor3& v, const Vektor3& omega,
        const std::array<double, 7>& parameter, std::optional<double> cd_volumen,
        const Abbruch& abbruch)
{
    const double rho = parameter[0], nu = parameter[1], form = parameter[2];
    const double cd_quer = parameter[3], eta = parameter[4], cd0 = parameter[5];
    const double ruder = parameter[6], pi = 3.14159265358979323846;
    endlich(parameter, "Hydrodynamikparameter");
    positiv(rho, "Wasserdichte"); positiv(nu, "Viskositaet");
    positiv(eta, "Wirkungsgrad");
    std::vector<Beitrag> beitraege;
    for (const auto& teil : teile) {
        abbruch.pruefen();
        std::vector<double> nass;
        std::vector<Vektor3> mitten;
        Vektor3 zentrum{};
        for (std::size_t i = 0; i < teil.ecken.size(); ++i) {
            auto e = teil.ecken[i];
            for (auto& p : e) {
                p = multiplizieren(rotation, p);
                for (std::size_t j = 0; j < 3; ++j) {
                    p[j] += position[j];
                }
            }
            const double flaeche = teil.flaechen[i] * benetzungsanteil(e);
            nass.push_back(flaeche);
            auto mitte = multiplizieren(rotation, teil.mittelpunkte[i]);
            for (std::size_t j = 0; j < 3; ++j) {
                mitte[j] += position[j];
                zentrum[j] += mitte[j] * flaeche;
            }
            mitten.push_back(mitte);
        }
        const double nass_flaeche = paarweise_summe(nass.data(), nass.size());
        if (nass_flaeche <= 1e-12) {
            continue;
        }
        Vektor3 arm{};
        for (std::size_t i = 0; i < 3; ++i) {
            zentrum[i] /= nass_flaeche;
            arm[i] = zentrum[i] - position[i];
        }
        auto lokal = kreuzprodukt(omega, arm);
        for (std::size_t i = 0; i < 3; ++i) {
            lokal[i] += v[i];
        }
        const double tempo = std::sqrt(skalarprodukt(lokal, lokal));
        Vektor3 kraft{}, moment{};
        std::string name;
        const auto& rolle = teil.mesh.rolle;
        if (rolle == "volumenkoerper") {
            if (!cd_volumen) {
                continue;
            }
            bool aktiv = false;
            for (std::size_t i = 0; i < mitten.size(); ++i) {
                if (skalarprodukt(teil.normalen[i], teil.normalen[i]) <= 0.) {
                    continue;
                }
                Vektor3 hebel{};
                for (std::size_t j = 0; j < 3; ++j) {
                    hebel[j] = mitten[i][j] - position[j];
                }
                auto geschwindigkeit = kreuzprodukt(omega, hebel);
                for (std::size_t j = 0; j < 3; ++j) {
                    geschwindigkeit[j] += v[j];
                }
                const double t = std::sqrt(skalarprodukt(geschwindigkeit, geschwindigkeit));
                if (t <= 1e-9) {
                    continue;
                }
                aktiv = true;
                auto richtung = geschwindigkeit;
                for (double& w : richtung) {
                    w /= t;
                }
                const auto normale = multiplizieren(rotation, teil.normalen[i]);
                const double projektion = .5 * nass[i] * std::abs(skalarprodukt(normale, richtung));
                Vektor3 f{}, h{};
                for (std::size_t j = 0; j < 3; ++j) {
                    f[j] = (-.5 * rho * *cd_volumen * projektion * t) * geschwindigkeit[j];
                    h[j] = mitten[i][j] - zentrum[j];
                    kraft[j] += f[j];
                }
                const auto m = kreuzprodukt(h, f);
                for (std::size_t j = 0; j < 3; ++j) {
                    moment[j] += m[j];
                }
            }
            if (!aktiv) {
                continue;
            }
            name = "hydrodynamik_volumenkoerper";
        } else {
            if (tempo <= 1e-9) {
                continue;
            }
            const double q = .5 * rho * tempo * tempo;
            Vektor3 richtung = lokal;
            for (double& w : richtung) {
                w /= tempo;
            }
            if (rolle == "rumpf") {
                const double cf = ittc_reibungsbeiwert(tempo * teil.laenge / nu);
                const double reibung = q * cf * nass_flaeche * (1. + form);
                std::vector<double> projektionen;
                for (std::size_t i = 0; i < nass.size(); ++i) {
                    if (skalarprodukt(teil.normalen[i], teil.normalen[i]) > 0.) {
                        projektionen.push_back(nass[i] * std::abs(skalarprodukt(
                            multiplizieren(rotation, teil.normalen[i]), richtung)));
                    }
                }
                const double projektion = .5 * paarweise_summe(projektionen.data(), projektionen.size());
                const double quer = q * cd_quer * projektion;
                for (std::size_t i = 0; i < 3; ++i) {
                    kraft[i] = -(reibung + quer) * richtung[i];
                }
                name = "hydrodynamik_rumpf";
            } else {
                if (teil.planform <= 1e-12 || teil.spannweite <= 1e-12) {
                    continue;
                }
                const double grad = std::min(1., std::max(0., nass_flaeche / teil.oberflaeche));
                const double flaeche = teil.planform * grad;
                if (flaeche <= 1e-12) {
                    continue;
                }
                const double streckung = teil.spannweite * teil.spannweite / teil.planform;
                double winkel = std::atan2(lokal[1], lokal[0]);
                if (rolle == "ruder") {
                    winkel += ruder;
                }
                const double slope = 2. * pi * streckung / (streckung + 2.);
                const double cl = 1.2 * std::tanh(slope * std::sin(winkel) / 1.2);
                Vektor3 quer{-richtung[1], richtung[0], 0.};
                const double norm = std::sqrt(skalarprodukt(quer, quer));
                if (norm <= 1e-12) {
                    continue;
                }
                const double lift = q * flaeche * cl;
                const double drag = q * flaeche * (cd0 + cl * cl / (pi * eta * streckung));
                for (std::size_t i = 0; i < 3; ++i) {
                    kraft[i] = -lift * (quer[i] / norm) - drag * richtung[i];
                }
                name = "hydrodynamik_" + rolle;
            }
        }
        endlich(kraft, "Hydrodynamikkraft"); endlich(moment, "Hydrodynamikmoment");
        beitraege.push_back(Beitrag{name, Wrench{"simulationsframe", zentrum, kraft, moment}});
    }
    return beitraege;
}

} // namespace segelphysik
