#pragma once

#include "anzeige.hpp"
#include <tuple>

namespace segelphysik {

inline double winkel_360(double winkel)
{
    endlich(std::array<double, 1>{winkel}, "Winkel");
    const double periode = 2. * std::acos(-1.);
    double rest = std::fmod(winkel, periode);
    if (rest < 0.) {
        rest += periode;
    }
    return rest == 0. ? 0. : rest;
}

inline double wrap_180(double winkel)
{
    return winkel_360(winkel + std::acos(-1.)) - std::acos(-1.);
}

inline int richtungssektor(double grad)
{
    endlich(std::array<double, 1>{grad}, "Heading");
    double rest = std::fmod(grad, 360.);
    if (rest < 0.) {
        rest += 360.;
    }
    return static_cast<int>(std::floor((rest + 11.25) / 22.5)) % 16;
}

inline std::array<std::optional<double>, 7> navigationswerte(
        const std::optional<Matrix3>& rotation,
        const std::optional<double>& offset, const std::optional<double>& elevation,
        const std::optional<double>& segelwinkel)
{
    std::array<std::optional<double>, 7> werte{};
    constexpr double epsilon = 1e-10;
    const double pi = std::acos(-1.);
    for (const auto& winkel : {offset, elevation, segelwinkel}) {
        if (winkel) {
            endlich(std::array<double, 1>{*winkel}, "Navigationswinkel");
        }
    }
    if (rotation) {
        const auto& r = *rotation;
        endlich(r, "Navigationsrotation");
        const double horizontal = std::hypot(r[0], r[3]);
        if (horizontal > epsilon) {
            werte[0] = winkel_360(std::atan2(-r[3], r[0]));
            werte[1] = std::atan2(-r[7], r[8]);
        }
        werte[2] = std::atan2(r[6], horizontal);
    }
    if (werte[0] && offset && elevation && *elevation >= 0. && *elevation < pi / 2.) {
        endlich(std::array<double, 2>{*offset, *elevation}, "Kamerawinkel");
        const double heading = *werte[0];
        const double azimut = winkel_360(heading + *offset);
        werte[3] = azimut;
        const Vektor3 kamera{
            std::cos(*elevation) * std::cos(azimut),
            -std::cos(*elevation) * std::sin(azimut), std::sin(*elevation)};
        const Vektor3 bug{std::cos(heading), -std::sin(heading), 0.};
        const auto steuerbord = kreuzprodukt(bug, {0., 0., 1.});
        const double pitch_x = skalarprodukt(kamera, bug);
        const double roll_x = skalarprodukt(kamera, steuerbord);
        if (std::hypot(pitch_x, kamera[2]) > epsilon) {
            werte[4] = std::atan2(kamera[2], pitch_x);
        }
        if (std::hypot(roll_x, kamera[2]) > epsilon) {
            werte[5] = std::atan2(kamera[2], roll_x);
        }
    }
    for (std::size_t i = 0; i < 6; ++i) {
        if (werte[i]) {
            *werte[i] *= 180. / pi;
        }
    }
    werte[6] = segelwinkel;
    return werte;
}

using KameraLage = std::tuple<std::optional<double>, double, double>;

using InstrumentDaten = std::tuple<bool, bool, double, std::optional<double>,
                                  std::optional<int>>;

inline InstrumentDaten instrument_aufbereitung(int typ,
        const std::optional<double>& winkel, const std::optional<double>& kamera)
{
    if (typ < 0 || typ > 2) {
        throw std::invalid_argument("Unbekannter Instrumenttyp");
    }
    for (const auto& wert : {winkel, kamera}) {
        if (wert) { endlich(std::array<double, 1>{*wert}, "Instrumentwinkel"); }
    }
    const bool fehler = !winkel, gefahr = winkel && typ != 0 && std::abs(*winkel) > 90.;
    std::optional<double> kamera_grad;
    std::optional<int> gerundet;
    double pose = 0.;
    if (typ == 0) {
        auto modulo = [](double grad) {
            double rest = std::fmod(grad, 360.);
            if (rest < 0.) { rest += 360.; }
            return rest == 0. ? 0. : rest;
        };
        if (winkel) {
            pose = modulo(*winkel);
            gerundet = static_cast<int>(std::floor(pose + .5)) % 360;
        }
        if (kamera) { kamera_grad = modulo(*kamera); }
    } else {
        pose = winkel ? -*winkel : 0.;
        if (kamera) { kamera_grad = 90. - *kamera; }
    }
    return {fehler, gefahr, pose, kamera_grad, gerundet};
}

inline Vektor4 svg_rahmen(double breite, double hoehe, double svg_breite, double svg_hoehe)
{
    endlich(Vektor4{breite, hoehe, svg_breite, svg_hoehe}, "SVG-Rahmen");
    const double skala = std::min(breite / std::max(svg_breite, 1.),
        hoehe / std::max(svg_hoehe, 1.));
    const double w = svg_breite * skala, h = svg_hoehe * skala;
    return {(breite - w) / 2., (hoehe - h) / 2., w, h};
}

inline Vektor3 geschwindigkeitseinheiten(double wert)
{
    endlich(Vektor3{wert, 0., 0.}, "Geschwindigkeitsanzeige");
    const Vektor3 einheiten{wert, wert * 3.6, wert * 1.9438444924406};
    endlich(einheiten, "Geschwindigkeitseinheiten");
    return einheiten;
}

inline std::optional<KameraLage> kameralage(const Vektor3& position,
        const Vektor3& fokus, const std::optional<double>& heading)
{
    Vektor3 richtung{};
    for (std::size_t i = 0; i < 3; ++i) { richtung[i] = position[i] - fokus[i]; }
    const double distanz = std::sqrt(skalarprodukt(richtung, richtung));
    const double horizontal = std::sqrt(richtung[0] * richtung[0] + richtung[1] * richtung[1]);
    if (!std::isfinite(distanz) || distanz <= 1e-10) { return std::nullopt; }
    std::optional<double> offset;
    if (horizontal > 1e-10 && heading) {
        offset = wrap_180(std::atan2(-richtung[1], richtung[0]) - *heading);
    }
    return KameraLage{offset, std::atan2(richtung[2], horizontal), distanz};
}

struct KameraUpdate {
    KameraLage lage;
    std::optional<double> heading;
    Vektor3 position, oben;
    bool geaendert;
};

inline std::optional<KameraUpdate> kamera_aktualisieren(
        const Vektor3& position, const Vektor3& fokus, const Vektor3& oben,
        const Vektor3& ziel, const std::optional<double>& heading,
        const std::optional<double>& letzter_heading, const std::optional<KameraLage>& alt)
{
    endlich(ziel, "Kameraziel"); endlich(oben, "Kameraoben");
    for (const auto& wert : {heading, letzter_heading}) {
        if (wert) { endlich(std::array<double, 1>{*wert}, "Kameraheading"); }
    }
    auto lage = alt ? alt : kameralage(position, fokus, heading);
    if (!lage) { return std::nullopt; }
    auto [offset, elevation, distanz] = *lage;
    endlich(std::array<double, 2>{elevation, distanz}, "Kameralage");
    if (offset) { endlich(std::array<double, 1>{*offset}, "Kameraoffset"); }
    const auto neu_heading = heading ? heading : letzter_heading;
    if (heading && !offset) {
        const double x = position[0] - fokus[0], y = position[1] - fokus[1];
        if (std::sqrt(x * x + y * y) > 1e-10) {
            offset = wrap_180(std::atan2(-y, x) - *heading);
        }
    }
    Vektor3 versatz{};
    if (offset) {
        if (!neu_heading) {
            throw std::invalid_argument("Kameraoffset benoetigt einen Headingbezug");
        }
        const double azimut = *neu_heading + *offset;
        versatz = {distanz * (std::cos(elevation) * std::cos(azimut)),
            distanz * (-std::cos(elevation) * std::sin(azimut)),
            distanz * std::sin(elevation)};
    } else {
        for (std::size_t i = 0; i < 3; ++i) { versatz[i] = position[i] - fokus[i]; }
    }
    endlich(versatz, "Kameraversatz");
    const double betrag = std::max(std::sqrt(skalarprodukt(versatz, versatz)), 1e-10);
    Vektor3 blickrichtung{}, hoch{};
    for (std::size_t i = 0; i < 3; ++i) { blickrichtung[i] = -versatz[i] / betrag; }
    for (std::size_t i = 0; i < 3; ++i) {
        hoch[i] = (i == 2 ? 1. : 0.) - blickrichtung[2] * blickrichtung[i];
    }
    const double norm = std::sqrt(skalarprodukt(hoch, hoch));
    if (norm > 1e-10) {
        for (double& wert : hoch) { wert /= norm; }
    } else {
        hoch = oben;
    }
    KameraUpdate neu{{offset, elevation, distanz}, neu_heading, {}, hoch, false};
    for (std::size_t i = 0; i < 3; ++i) {
        neu.position[i] = ziel[i] + versatz[i];
        if (!std::isfinite(position[i]) || !std::isfinite(fokus[i])
                || std::abs(position[i] - neu.position[i]) > 1e-9
                || std::abs(fokus[i] - ziel[i]) > 1e-9
                || std::abs(oben[i] - hoch[i]) > 1e-9) {
            neu.geaendert = true;
        }
    }
    endlich(neu.position, "Kameraposition");
    return neu;
}

} // namespace segelphysik
