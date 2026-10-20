#pragma once

#include "datentypen.hpp"
#include <algorithm>
#include <limits>

namespace segelphysik {

using Quaternion = std::array<double, 4>;

inline Quaternion quaternion_normalisieren(Quaternion q)
{
    endlich(q, "Quaternion");
    const double norm = std::sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
    if (norm <= std::numeric_limits<double>::min()) {
        throw std::invalid_argument("Quaternion darf nicht die Nullrotation sein");
    }
    for (double& wert : q) {
        wert /= norm;
    }
    return q;
}

inline Matrix3 quaternion_matrix(const Quaternion& quaternion)
{
    const auto q = quaternion_normalisieren(quaternion);
    const double w = q[0], x = q[1], y = q[2], z = q[3];
    return {
        1. - 2. * (y * y + z * z), 2. * (x * y - z * w), 2. * (x * z + y * w),
        2. * (x * y + z * w), 1. - 2. * (x * x + z * z), 2. * (y * z - x * w),
        2. * (x * z - y * w), 2. * (y * z + x * w), 1. - 2. * (x * x + y * y),
    };
}

inline Matrix3 transponieren(const Matrix3& a)
{
    return {a[0], a[3], a[6], a[1], a[4], a[7], a[2], a[5], a[8]};
}

inline Matrix3 multiplizieren(const Matrix3& a, const Matrix3& b)
{
    Matrix3 c{};
    for (std::size_t i = 0; i < 3; ++i) {
        for (std::size_t j = 0; j < 3; ++j) {
            for (std::size_t k = 0; k < 3; ++k) {
                c[3 * i + j] += a[3 * i + k] * b[3 * k + j];
            }
        }
    }
    return c;
}

inline Vektor3 multiplizieren(const Matrix3& a, const Vektor3& v)
{
    Vektor3 c{};
    for (std::size_t i = 0; i < 3; ++i) {
        for (std::size_t j = 0; j < 3; ++j) {
            c[i] += a[3 * i + j] * v[j];
        }
    }
    return c;
}

inline void rotation_pruefen(const Matrix3& a)
{
    endlich(a, "Rotation");
    const auto produkt = multiplizieren(transponieren(a), a);
    for (std::size_t i = 0; i < 9; ++i) {
        if (std::abs(produkt[i] - (i % 4 == 0 ? 1. : 0.)) > 1e-8) {
            throw std::invalid_argument("Orientierung muss eine gueltige 3x3-Rotation sein");
        }
    }
    const double det = a[0] * (a[4] * a[8] - a[5] * a[7])
        - a[1] * (a[3] * a[8] - a[5] * a[6])
        + a[2] * (a[3] * a[7] - a[4] * a[6]);
    if (std::abs(det - 1.) > 1e-8) {
        throw std::invalid_argument("Orientierung muss rechtshaendig sein");
    }
}

inline Quaternion quaternion_aus_matrix(const Matrix3& a)
{
    rotation_pruefen(a);
    const double spur = a[0] + a[4] + a[8];
    Quaternion q{};
    if (spur > 0.) {
        const double s = std::sqrt(spur + 1.) * 2.;
        q = {.25 * s, (a[7] - a[5]) / s, (a[2] - a[6]) / s, (a[3] - a[1]) / s};
    } else {
        std::size_t achse = 0;
        if (a[4] > a[0]) {
            achse = 1;
        }
        if (a[8] > a[3 * achse + achse]) {
            achse = 2;
        }
        if (achse == 0) {
            const double s = std::sqrt(1. + a[0] - a[4] - a[8]) * 2.;
            q = {(a[7] - a[5]) / s, .25 * s, (a[1] + a[3]) / s, (a[2] + a[6]) / s};
        } else if (achse == 1) {
            const double s = std::sqrt(1. + a[4] - a[0] - a[8]) * 2.;
            q = {(a[2] - a[6]) / s, (a[1] + a[3]) / s, .25 * s, (a[5] + a[7]) / s};
        } else {
            const double s = std::sqrt(1. + a[8] - a[0] - a[4]) * 2.;
            q = {(a[3] - a[1]) / s, (a[2] + a[6]) / s, (a[5] + a[7]) / s, .25 * s};
        }
    }
    return quaternion_normalisieren(q);
}

inline Quaternion quaternion_multiplizieren(const Quaternion& q, const Quaternion& p)
{
    return {
        q[0] * p[0] - q[1] * p[1] - q[2] * p[2] - q[3] * p[3],
        q[0] * p[1] + q[1] * p[0] + q[2] * p[3] - q[3] * p[2],
        q[0] * p[2] - q[1] * p[3] + q[2] * p[0] + q[3] * p[1],
        q[0] * p[3] + q[1] * p[2] - q[2] * p[1] + q[3] * p[0],
    };
}

inline Quaternion orientierung_schritt(const Quaternion& q, const Vektor3& omega, double dt)
{
    endlich(q, "Quaternion");
    endlich(omega, "Winkelgeschwindigkeit");
    if (!std::isfinite(dt)) {
        throw std::invalid_argument("Zeitschritt muss endlich sein");
    }
    const double betrag = std::sqrt(omega[0] * omega[0] + omega[1] * omega[1] + omega[2] * omega[2]);
    const double winkel = betrag * dt;
    Quaternion delta{1., 0., 0., 0.};
    if (betrag > 1e-15) {
        const double faktor = std::sin(.5 * winkel) / betrag;
        delta = {std::cos(.5 * winkel), omega[0] * faktor, omega[1] * faktor, omega[2] * faktor};
    }
    return quaternion_normalisieren(quaternion_multiplizieren(q, delta));
}

inline Matrix3 rotationsmatrix_achsenwinkel(Vektor3 achse, double winkel)
{
    endlich(achse, "Gelenkachse");
    if (!std::isfinite(winkel)) {
        throw std::invalid_argument("Gelenkwinkel muss endlich sein");
    }
    const double norm = std::sqrt(
        achse[0] * achse[0] + achse[1] * achse[1] + achse[2] * achse[2]);
    if (norm <= 1e-12) {
        throw std::invalid_argument("Gelenkachse darf nicht null sein");
    }
    for (double& wert : achse) {
        wert /= norm;
    }
    const double x = achse[0], y = achse[1], z = achse[2];
    const double c = std::cos(winkel), s = std::sin(winkel), t = 1. - c;
    return {
        t*x*x+c, t*x*y-s*z, t*x*z+s*y,
        t*x*y+s*z, t*y*y+c, t*y*z-s*x,
        t*x*z-s*y, t*y*z+s*x, t*z*z+c,
    };
}

struct Pose {
    std::string ziel;
    std::string quelle;
    Vektor3 translation;
    Quaternion quaternion;

    Pose(std::string ziel_frame, std::string quell_frame, Vektor3 t, Quaternion q)
        : ziel(std::move(ziel_frame)), quelle(std::move(quell_frame)),
          translation(t), quaternion(quaternion_normalisieren(q))
    {
        name_pruefen(ziel, "Ziel-Frame");
        name_pruefen(quelle, "Quell-Frame");
        endlich(translation, "Pose-Translation");
    }

    Vektor3 vektor_transformieren(const Vektor3& v) const
    {
        endlich(v, "Vektor");
        return multiplizieren(quaternion_matrix(quaternion), v);
    }

    Vektor3 punkt_transformieren(const Vektor3& v) const
    {
        auto punkt = vektor_transformieren(v);
        for (std::size_t i = 0; i < 3; ++i) {
            punkt[i] += translation[i];
        }
        return punkt;
    }

    Pose invers() const
    {
        const auto rotation = transponieren(quaternion_matrix(quaternion));
        auto t = multiplizieren(rotation, translation);
        for (double& wert : t) {
            wert = -wert;
        }
        return Pose(quelle, ziel, t, quaternion_aus_matrix(rotation));
    }

    Pose komponieren(const Pose& innen) const
    {
        if (quelle != innen.ziel) {
            throw std::invalid_argument("Pose-Frames passen nicht");
        }
        const auto rotation = multiplizieren(
            quaternion_matrix(quaternion), quaternion_matrix(innen.quaternion));
        return Pose(ziel, innen.quelle, punkt_transformieren(innen.translation),
                    quaternion_aus_matrix(rotation));
    }
};

inline Pose pose_mit_gelenkwinkel(const Pose& basis, const Vektor3& achse, double winkel)
{
    const auto rotation = multiplizieren(
        rotationsmatrix_achsenwinkel(achse, winkel), quaternion_matrix(basis.quaternion));
    return Pose(basis.ziel, basis.quelle, basis.translation, quaternion_aus_matrix(rotation));
}

struct Koerperteil {
    double masse;
    Matrix3 traegheit;
    Mesh mesh;
    Pose pose;

    void pruefen() const
    {
        positiv(masse, "Teilmasse");
        endlich(traegheit, "Teiltraegheit");
        mesh.pruefen();
    }
};

struct Verband {
    double masse{};
    Matrix3 traegheit{};
    Vektor3 schwerpunkt{};
    std::vector<Vektor3> punkte;
    std::vector<std::array<std::int64_t, 3>> dreiecke;
    std::vector<Vektor3> teilzentren;
    std::vector<Matrix3> teilrotationen;
};

struct VerbandKontext {
    std::vector<Koerperteil> teile;
    std::uint64_t version;
};

inline Verband verband_aggregieren(const std::vector<Koerperteil>& teile, const Abbruch& abbruch)
{
    if (teile.empty()) {
        throw std::invalid_argument("Verband braucht mindestens ein Teil");
    }
    Verband ergebnis;
    std::vector<Vektor3> zentren;
    for (const auto& teil : teile) {
        abbruch.pruefen();
        teil.pruefen();
        const auto rotation = quaternion_matrix(teil.pose.quaternion);
        const auto& t = teil.pose.translation;
        const auto inertia = multiplizieren(
            multiplizieren(rotation, teil.traegheit), transponieren(rotation));
        for (std::size_t i = 0; i < 9; ++i) {
            ergebnis.traegheit[i] += inertia[i];
        }
        ergebnis.masse += teil.masse;
        for (std::size_t i = 0; i < 3; ++i) {
            ergebnis.schwerpunkt[i] += teil.masse * t[i];
        }
        const auto versatz = static_cast<std::int64_t>(ergebnis.punkte.size());
        for (const auto& punkt : teil.mesh.punkte) {
            auto p = multiplizieren(rotation, punkt);
            for (std::size_t i = 0; i < 3; ++i) {
                p[i] += t[i];
            }
            ergebnis.punkte.push_back(p);
        }
        for (auto dreieck : teil.mesh.dreiecke) {
            for (auto& index : dreieck) {
                if (index > std::numeric_limits<std::int64_t>::max() - versatz) {
                    throw std::overflow_error("Dreiecksindex im Verband zu gross");
                }
                index += versatz;
            }
            ergebnis.dreiecke.push_back(dreieck);
        }
        zentren.push_back(t);
        ergebnis.teilrotationen.push_back(rotation);
    }
    positiv(ergebnis.masse, "Verbandmasse");
    for (double& wert : ergebnis.schwerpunkt) {
        wert /= ergebnis.masse;
    }
    for (std::size_t n = 0; n < teile.size(); ++n) {
        abbruch.pruefen();
        auto d = zentren[n];
        for (std::size_t i = 0; i < 3; ++i) {
            d[i] -= ergebnis.schwerpunkt[i];
        }
        const double quadrat = d[0] * d[0] + d[1] * d[1] + d[2] * d[2];
        for (std::size_t i = 0; i < 3; ++i) {
            for (std::size_t j = 0; j < 3; ++j) {
                ergebnis.traegheit[3 * i + j] += teile[n].masse
                    * ((i == j ? quadrat : 0.) - d[i] * d[j]);
            }
        }
        ergebnis.teilzentren.push_back(d);
    }
    for (auto& punkt : ergebnis.punkte) {
        for (std::size_t i = 0; i < 3; ++i) {
            punkt[i] -= ergebnis.schwerpunkt[i];
        }
        endlich(punkt, "Verbandpunkt");
    }
    endlich(ergebnis.schwerpunkt, "Verband-Schwerpunkt");
    endlich(ergebnis.traegheit, "Verband-Traegheit");
    return ergebnis;
}

} // namespace segelphysik
