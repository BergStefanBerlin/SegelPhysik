#pragma once

#include "frames.hpp"
#include <tuple>

namespace segelphysik {

inline Matrix3 euler_rotation(double phi, double theta, double psi)
{
    endlich(std::array<double, 3>{phi, theta, psi}, "Eulerwinkel");
    const double cp = std::cos(phi), sp = std::sin(phi);
    const double ct = std::cos(theta), st = std::sin(theta);
    const double cy = std::cos(psi), sy = std::sin(psi);
    return multiplizieren(multiplizieren(
        Matrix3{cy, -sy, 0., sy, cy, 0., 0., 0., 1.},
        Matrix3{ct, 0., st, 0., 1., 0., -st, 0., ct}),
        Matrix3{1., 0., 0., 0., cp, -sp, 0., sp, cp});
}

inline Quaternion quaternion_slerp(const Quaternion& anfang, const Quaternion& ende,
                                   double anteil)
{
    auto q0 = quaternion_normalisieren(anfang);
    auto q1 = quaternion_normalisieren(ende);
    if (!std::isfinite(anteil)) {
        throw std::invalid_argument("Interpolationsanteil muss endlich sein");
    }
    anteil = std::clamp(anteil, 0., 1.);
    double punkt = 0.;
    for (std::size_t i = 0; i < 4; ++i) {
        punkt += q0[i] * q1[i];
    }
    if (punkt < 0.) {
        for (double& wert : q1) {
            wert = -wert;
        }
        punkt = -punkt;
    }
    Quaternion ergebnis{};
    if (punkt > .9995) {
        for (std::size_t i = 0; i < 4; ++i) {
            ergebnis[i] = q0[i] + anteil * (q1[i] - q0[i]);
        }
        return quaternion_normalisieren(ergebnis);
    }
    const double winkel = std::acos(std::clamp(punkt, -1., 1.));
    const double sinus = std::sin(winkel);
    const double a = std::sin((1. - anteil) * winkel) / sinus;
    const double b = std::sin(anteil * winkel) / sinus;
    for (std::size_t i = 0; i < 4; ++i) {
        ergebnis[i] = a * q0[i] + b * q1[i];
    }
    return ergebnis;
}

inline std::tuple<double, std::size_t, Zustand> anzeige_interpolieren(
        const std::vector<double>& zeiten, const std::vector<Zustand>& verlauf,
        double anzeigezeit, double vergangen, double verzoegerung)
{
    if (zeiten.empty() || zeiten.size() != verlauf.size()) {
        throw std::invalid_argument("Anzeige braucht gleich viele Zeiten und Zustaende");
    }
    endlich(zeiten, "Anzeigezeiten");
    endlich(std::array<double, 3>{anzeigezeit, vergangen, verzoegerung}, "Anzeigeuhr");
    if (!std::is_sorted(zeiten.begin(), zeiten.end()) || vergangen < 0. || verzoegerung < 0.) {
        throw std::invalid_argument("Anzeige braucht monotone Zeiten und nichtnegative Dauern");
    }
    double zielzeit = std::max(zeiten.front(), anzeigezeit);
    const double puffergrenze = std::max(zielzeit, zeiten.back() - verzoegerung);
    zielzeit = std::min({zeiten.back(), puffergrenze, zielzeit + vergangen});
    if (zielzeit <= zeiten.front() || zeiten.size() == 1) {
        return {zielzeit, 0, verlauf.front()};
    }
    std::size_t index = 1;
    while (index < zeiten.size() && zeiten[index] < zielzeit) {
        ++index;
    }
    index = std::min(index, zeiten.size() - 1);
    const double dauer = zeiten[index] - zeiten[index - 1];
    const double anteil = dauer <= 0. ? 1. :
        std::clamp((zielzeit - zeiten[index - 1]) / dauer, 0., 1.);
    const auto& start = verlauf[index - 1].werte;
    auto ergebnis = verlauf[index];
    const auto q = quaternion_slerp(
        {start[3], start[4], start[5], start[6]},
        {ergebnis.werte[3], ergebnis.werte[4], ergebnis.werte[5], ergebnis.werte[6]}, anteil);
    for (std::size_t i = 0; i < 3; ++i) {
        ergebnis.werte[i] = start[i] + anteil * (ergebnis.werte[i] - start[i]);
    }
    std::copy(q.begin(), q.end(), ergebnis.werte.begin() + 3);
    endlich(ergebnis.werte, "Anzeigepose");
    return {zielzeit, index - 1, ergebnis};
}

} // namespace segelphysik
