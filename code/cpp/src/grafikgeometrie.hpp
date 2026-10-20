#pragma once

#include "frames.hpp"
#include <limits>

namespace segelphysik {

inline std::vector<Vektor3> grafik_punkte(const std::vector<Vektor3>& punkte,
                                        const Matrix3& rotation, const Vektor3& translation)
{
    std::vector<Vektor3> ziel;
    ziel.reserve(punkte.size());
    for (const auto& punkt : punkte) {
        endlich(punkt, "Grafikpunkt");
        auto welt = multiplizieren(rotation, punkt);
        for (std::size_t i = 0; i < 3; ++i) { welt[i] += translation[i]; }
        endlich(welt, "Transformierter Grafikpunkt");
        ziel.push_back(welt);
    }
    return ziel;
}

inline std::pair<Matrix3, Vektor3> grafik_hauptachsen(
        const std::vector<Vektor3>& punkte, const Matrix3& eigenvektoren,
        const Matrix3& rotation)
{
    rotation_pruefen(rotation);
    endlich(eigenvektoren, "Grafik-Hauptachsen");
    Matrix3 richtungen{};
    Vektor3 laengen{};
    for (std::size_t achse = 0; achse < 3; ++achse) {
        Vektor3 richtung{};
        for (std::size_t koordinate = 0; koordinate < 3; ++koordinate) {
            for (std::size_t j = 0; j < 3; ++j) {
                richtung[koordinate] += eigenvektoren[3 * achse + j]
                    * rotation[3 * koordinate + j];
            }
        }
        for (std::size_t koordinate = 0; koordinate < 3; ++koordinate) {
            richtungen[3 * achse + koordinate] = richtung[koordinate];
        }
        double halbe = 0.;
        for (const auto& punkt : punkte) {
            endlich(punkt, "Grafikpunkt");
            double projektion = 0.;
            for (std::size_t koordinate = 0; koordinate < 3; ++koordinate) {
                projektion += punkt[koordinate] * richtung[koordinate];
            }
            halbe = std::max(halbe, std::abs(projektion));
        }
        laengen[achse] = std::max(1.05 * halbe, 0.05);
    }
    endlich(richtungen, "Transformierte Grafik-Hauptachsen");
    endlich(laengen, "Grafik-Hauptachsenlaengen");
    return {richtungen, laengen};
}

inline std::vector<std::vector<Vektor3>> grafik_farbgeometrie(
        const std::vector<std::int64_t>& eltern,
        const std::vector<Matrix3>& lokal_rotation,
        const std::vector<Vektor3>& lokal_translation,
        const std::vector<Vektor3>& zentren,
        const std::vector<std::int64_t>& blaetter,
        const std::vector<std::vector<Vektor3>>& punkte)
{
    const auto n = eltern.size();
    if (!n || lokal_rotation.size() != n || lokal_translation.size() != n
            || zentren.size() != n || blaetter.size() != punkte.size()) {
        throw std::invalid_argument("Inkonsistente Grafikbaumdaten");
    }
    std::vector<Matrix3> rotationen(n);
    std::vector<Vektor3> translationen(n);
    for (std::size_t i = 0; i < n; ++i) {
        rotation_pruefen(lokal_rotation[i]);
        endlich(lokal_translation[i], "Grafiktranslation");
        endlich(zentren[i], "Grafikschwerpunkt");
        if (i == 0) {
            if (eltern[i] != -1) {
                throw std::invalid_argument("Grafikwurzel darf keinen Elternknoten haben");
            }
            rotationen[i] = lokal_rotation[i];
            translationen[i] = lokal_translation[i];
        } else {
            const auto elternindex = eltern[i];
            if (elternindex < 0 || static_cast<std::uint64_t>(elternindex) >= i) {
                throw std::invalid_argument("Grafikeltern muessen vor ihren Kindern stehen");
            }
            const auto j = static_cast<std::size_t>(elternindex);
            rotationen[i] = multiplizieren(rotationen[j], lokal_rotation[i]);
            const auto t = multiplizieren(rotationen[j], lokal_translation[i]);
            for (std::size_t achse = 0; achse < 3; ++achse) {
                translationen[i][achse] = translationen[j][achse] + t[achse];
            }
        }
    }
    std::vector<std::vector<Vektor3>> ziel;
    ziel.reserve(blaetter.size());
    for (std::size_t blatt = 0; blatt < blaetter.size(); ++blatt) {
        const auto i = blaetter[blatt];
        if (i < 0 || static_cast<std::uint64_t>(i) >= n) {
            throw std::invalid_argument("Grafikblattindex ausserhalb des Baums");
        }
        const auto versatz = multiplizieren(rotationen[i], zentren[i]);
        Vektor3 schwerpunkt{};
        for (std::size_t achse = 0; achse < 3; ++achse) {
            schwerpunkt[achse] = translationen[i][achse] + versatz[achse];
        }
        ziel.push_back(grafik_punkte(punkte[blatt], rotationen[i], schwerpunkt));
    }
    return ziel;
}

inline Mesh grafik_meshes_vereinen(const std::vector<Mesh>& meshes)
{
    Mesh ziel{};
    for (const auto& mesh : meshes) {
        const auto offset = static_cast<std::int64_t>(ziel.punkte.size());
        ziel.punkte.insert(ziel.punkte.end(), mesh.punkte.begin(), mesh.punkte.end());
        for (auto dreieck : mesh.dreiecke) {
            for (auto& index : dreieck) {
                if (index > std::numeric_limits<std::int64_t>::max() - offset) {
                    throw std::overflow_error("Grafikdreiecksindex ist zu gross");
                }
                index += offset;
            }
            ziel.dreiecke.push_back(dreieck);
        }
    }
    return ziel;
}

inline std::vector<std::array<std::int64_t, 4>> grafik_dreieckszellen(
        const std::vector<std::array<std::int64_t, 3>>& dreiecke)
{
    std::vector<std::array<std::int64_t, 4>> ziel;
    ziel.reserve(dreiecke.size());
    for (const auto& f : dreiecke) { ziel.push_back({3, f[0], f[1], f[2]}); }
    return ziel;
}

} // namespace segelphysik
