#pragma once

#include "ebenenschnitt.hpp"
#include <algorithm>
#include <limits>
#include <optional>

namespace segelphysik {

struct PfeilGeometrie {
    Vektor3 start, richtung, schaft_ende, spitze;
    double laenge, betrag, kopf_laenge, kopf_radius, schaft_radius;
};

inline PfeilGeometrie pfeil_geometrie(const Vektor3& start, const Vektor3& vektor,
        double kopfanteil, double radiusfaktor, bool fest = false,
        double durchmesser = 0., double kopf_durchmesser = 0.,
        double kopf_laenge = 0., double mindestlaenge = 0.)
{
    endlich(start, "Pfeilstart"); endlich(vektor, "Pfeilvektor");
    endlich(std::array<double, 6>{kopfanteil, radiusfaktor, durchmesser,
        kopf_durchmesser, kopf_laenge, mindestlaenge}, "Pfeilparameter");
    const double betrag = std::sqrt(skalarprodukt(vektor, vektor));
    if (betrag <= 0.) {
        throw std::invalid_argument("Pfeil mit Null-Laenge unzulaessig");
    }
    const double laenge = fest ? std::max(betrag, mindestlaenge) : betrag;
    double kopf_l = fest ? kopf_laenge : kopfanteil * laenge;
    double kopf_r = fest ? .5 * kopf_durchmesser : radiusfaktor * laenge;
    if (fest && kopf_l > .5 * laenge) {
        const double faktor = .5 * laenge / kopf_l;
        kopf_l *= faktor; kopf_r *= faktor;
    }
    PfeilGeometrie ergebnis{start, {}, {}, {}, laenge, betrag, kopf_l,
        kopf_r, .5 * durchmesser};
    for (std::size_t i = 0; i < 3; ++i) {
        ergebnis.richtung[i] = vektor[i] / betrag;
        ergebnis.spitze[i] = start[i] + laenge * ergebnis.richtung[i];
        ergebnis.schaft_ende[i] = fest
            ? ergebnis.spitze[i] - kopf_l * ergebnis.richtung[i]
            : start[i] + (1. - kopfanteil) * laenge * ergebnis.richtung[i];
    }
    endlich(ergebnis.richtung, "Pfeilrichtung");
    endlich(ergebnis.spitze, "Pfeilspitze");
    endlich(ergebnis.schaft_ende, "Pfeilschaft");
    endlich(std::array<double, 4>{laenge, betrag, kopf_l, kopf_r}, "Pfeilmasse");
    return ergebnis;
}

inline Vektor3 kraft_paarmoment(const Vektor3& angriff, const Vektor3& kraft,
                               const Vektor3& schwerpunkt)
{
    const Vektor3 arm{angriff[0] - schwerpunkt[0], angriff[1] - schwerpunkt[1],
        angriff[2] - schwerpunkt[2]};
    const auto moment = kreuzprodukt(arm, kraft);
    endlich(moment, "Kraftpaarmoment");
    return moment;
}

inline double kraft_skala(double masse, double g, double referenz, double fuellfaktor)
{
    endlich(std::array<double, 4>{masse, g, referenz, fuellfaktor}, "Kraftskala");
    const double fg = masse * g;
    if (fg <= 0. || referenz <= 0.) {
        throw std::invalid_argument("masse*g und referenz_laenge muessen positiv sein");
    }
    const double skala = fuellfaktor * referenz / fg;
    if (!std::isfinite(fg) || !std::isfinite(skala)) {
        throw std::invalid_argument("Kraftskala ist nicht endlich");
    }
    return skala;
}

struct MomentBogen {
    std::vector<Vektor3> punkte;
    Vektor3 spitze, richtung;
    double kopf_laenge, kopf_radius;
};

inline std::optional<MomentBogen> moment_bogen(double moment, const Vektor3& mitte,
        double radius, int achse, double schwelle, double start_grad,
        double winkel_grad, std::size_t anzahl)
{
    endlich(mitte, "Bogenmittelpunkt");
    endlich(std::array<double, 6>{moment, radius, schwelle, start_grad, winkel_grad,
        static_cast<double>(anzahl)}, "Bogenparameter");
    if (radius <= 0.) {
        throw std::invalid_argument("radius muss positiv sein");
    }
    if (achse < 0 || achse > 2) {
        throw std::invalid_argument("achse muss 0, 1 oder 2 sein");
    }
    if (std::abs(moment) <= schwelle) { return std::nullopt; }
    if (anzahl < 2) {
        throw std::invalid_argument("Momentbogen benoetigt mindestens zwei Punkte");
    }
    const auto u = static_cast<std::size_t>((achse + 1) % 3);
    const auto v = static_cast<std::size_t>((achse + 2) % 3);
    const double vorzeichen = moment > 0. ? 1. : -1.;
    const double rad = std::acos(-1.) / 180.;
    const double start = start_grad * rad, spanne = winkel_grad * rad;
    MomentBogen ergebnis{{}, {}, {}, .35 * radius, .12 * radius};
    ergebnis.punkte.reserve(anzahl);
    double ende = start;
    const double schritt = 1. / static_cast<double>(anzahl - 1);
    for (std::size_t i = 0; i < anzahl; ++i) {
        const double anteil = i == anzahl - 1 ? 1. : static_cast<double>(i) * schritt;
        ende = start + spanne * vorzeichen * anteil;
        auto punkt = mitte;
        punkt[u] += radius * std::cos(ende);
        punkt[v] += radius * std::sin(ende);
        endlich(punkt, "Momentbogenpunkt");
        ergebnis.punkte.push_back(punkt);
    }
    ergebnis.richtung[u] = -vorzeichen * std::sin(ende);
    ergebnis.richtung[v] = vorzeichen * std::cos(ende);
    const double norm = std::sqrt(skalarprodukt(ergebnis.richtung, ergebnis.richtung));
    for (std::size_t i = 0; i < 3; ++i) {
        ergebnis.richtung[i] /= norm;
        ergebnis.spitze[i] = ergebnis.punkte.back()[i]
            + ergebnis.kopf_laenge * ergebnis.richtung[i];
    }
    endlich(ergebnis.spitze, "Momentbogenspitze");
    return ergebnis;
}

struct StrichLinien {
    std::vector<Vektor3> punkte;
    std::vector<std::int64_t> zellen;
};

inline StrichLinien strich_linien(const std::vector<Vektor3>& punkte,
                                 double strich, double luecke, double abstand)
{
    endlich(std::array<double, 3>{strich, luecke, abstand}, "Strichparameter");
    if (strich <= 0. || luecke < 0.) {
        throw std::invalid_argument("strich > 0 und luecke >= 0 erforderlich");
    }
    if (abstand == 0.) {
        throw std::invalid_argument("Strichabstand darf nicht null sein");
    }
    std::vector<double> kum(punkte.size(), 0.);
    for (std::size_t i = 0; i < punkte.size(); ++i) {
        endlich(punkte[i], "Linienpunkt");
        if (i) {
            const Vektor3 d{punkte[i][0] - punkte[i - 1][0],
                punkte[i][1] - punkte[i - 1][1], punkte[i][2] - punkte[i - 1][2]};
            kum[i] = kum[i - 1] + std::sqrt(skalarprodukt(d, d));
        }
    }
    if (kum.empty() || kum.back() <= 0.) {
        throw std::invalid_argument("Linienzug ohne Laenge");
    }
    if (!std::isfinite(kum.back()) || !std::isfinite(strich + luecke)) {
        throw std::invalid_argument("Linienlaenge oder Strichperiode ist nicht endlich");
    }
    StrichLinien ergebnis;
    for (double s = 0.; s < kum.back() - 1e-12; ) {
        const double ende = std::min(s + strich, kum.back());
        const double schritte = std::max(1., std::ceil((ende - s) / abstand));
        if (!std::isfinite(schritte)
                || schritte >= static_cast<double>(ergebnis.punkte.max_size() - 1)) {
            throw std::overflow_error("Zu viele Strichpunkte");
        }
        const auto anzahl = static_cast<std::size_t>(schritte) + 1;
        const auto offset = ergebnis.punkte.size();
        ergebnis.zellen.push_back(static_cast<std::int64_t>(anzahl));
        const double dt = (ende - s) / static_cast<double>(anzahl - 1);
        for (std::size_t i = 0; i < anzahl; ++i) {
            const double t = i == anzahl - 1 ? ende : s + static_cast<double>(i) * dt;
            const auto oben = std::upper_bound(kum.begin(), kum.end(), t);
            Vektor3 punkt{};
            if (oben == kum.end()) {
                punkt = punkte.back();
            } else {
                const auto rechts = static_cast<std::size_t>(oben - kum.begin());
                const auto links = rechts - 1;
                for (std::size_t achse = 0; achse < 3; ++achse) {
                    const double steigung = (punkte[rechts][achse] - punkte[links][achse])
                        / (kum[rechts] - kum[links]);
                    punkt[achse] = steigung * (t - kum[links]) + punkte[links][achse];
                }
            }
            endlich(punkt, "Strichpunkt");
            ergebnis.punkte.push_back(punkt);
            ergebnis.zellen.push_back(static_cast<std::int64_t>(offset + i));
        }
        const double weiter = s + (strich + luecke);
        if (weiter <= s) {
            throw std::overflow_error("Strichperiode ist numerisch nicht aufloesbar");
        }
        s = weiter;
    }
    if (ergebnis.punkte.empty()) {
        throw std::invalid_argument("Linienzug besitzt keine aufloesbaren Striche");
    }
    return ergebnis;
}

struct WirkungsLinie {
    Vektor3 anker, richtung;
    std::optional<Vektor3> schnittpunkt;
};

inline WirkungsLinie wirkungslinie(const Vektor3& kraft, const Vektor3& moment,
        const Vektor3& bezugspunkt, const Mesh& mesh, const Matrix3& rotation, double toleranz)
{
    endlich(kraft, "Wirkungslinienkraft"); endlich(moment, "Wirkungslinienmoment");
    endlich(bezugspunkt, "Wirkungslinienbezugspunkt");
    if (!std::isfinite(toleranz)) {
        throw std::invalid_argument("Wirkungslinientoleranz muss endlich sein");
    }
    rotation_pruefen(rotation);
    const double quadrat = skalarprodukt(kraft, kraft);
    if (!std::isfinite(quadrat)) {
        throw std::invalid_argument("Wirkungslinienkraft ist numerisch nicht aufloesbar");
    }
    if (quadrat <= toleranz * toleranz) {
        throw std::invalid_argument("Kraftwirkungslinie ist fuer Nullkraft undefiniert");
    }
    const double norm = std::sqrt(quadrat);
    const auto versatz = kreuzprodukt(kraft, moment);
    WirkungsLinie ergebnis{};
    for (std::size_t i = 0; i < 3; ++i) {
        ergebnis.richtung[i] = kraft[i] / norm;
        ergebnis.anker[i] = bezugspunkt[i] + versatz[i] / quadrat;
    }
    endlich(ergebnis.anker, "Wirkungslinienanker");
    endlich(ergebnis.richtung, "Wirkungslinienrichtung");
    std::vector<Vektor3> weltpunkte;
    weltpunkte.reserve(mesh.punkte.size());
    for (const auto& punkt : mesh.punkte) {
        auto welt = multiplizieren(rotation, punkt);
        for (std::size_t i = 0; i < 3; ++i) { welt[i] += bezugspunkt[i]; }
        endlich(welt, "Wirkungslinienmesh");
        weltpunkte.push_back(welt);
    }
    double kleinster_abstand = std::numeric_limits<double>::infinity();
    for (const auto& f : mesh.dreiecke) {
        const auto& a = weltpunkte[f[0]];
        const auto& b = weltpunkte[f[1]];
        const auto& c = weltpunkte[f[2]];
        Vektor3 e1{}, e2{}, tvec{};
        for (std::size_t i = 0; i < 3; ++i) {
            e1[i] = b[i] - a[i]; e2[i] = c[i] - a[i];
            tvec[i] = ergebnis.anker[i] - a[i];
        }
        const auto pvec = kreuzprodukt(ergebnis.richtung, e2);
        const double det = skalarprodukt(e1, pvec);
        if (std::abs(det) <= toleranz || det == 0.) { continue; }
        const double inv = 1. / det;
        const double u = skalarprodukt(tvec, pvec) * inv;
        const auto qvec = kreuzprodukt(tvec, e1);
        const double v = skalarprodukt(ergebnis.richtung, qvec) * inv;
        const double t = skalarprodukt(e2, qvec) * inv;
        if (u < -toleranz || v < -toleranz || u + v > 1. + toleranz) { continue; }
        Vektor3 position{};
        for (std::size_t i = 0; i < 3; ++i) {
            position[i] = ergebnis.anker[i] + t * ergebnis.richtung[i];
        }
        if (position[2] <= toleranz && std::abs(t) < kleinster_abstand) {
            endlich(position, "Wirkungslinienschnittpunkt");
            ergebnis.schnittpunkt = position;
            kleinster_abstand = std::abs(t);
        }
    }
    return ergebnis;
}

inline Vektor3 achse_kanonisieren(Vektor3 v)
{
    endlich(v, "Hauptachse");
    std::size_t index = 0;
    for (std::size_t i = 1; i < 3; ++i) {
        if (std::abs(v[i]) > std::abs(v[index])) { index = i; }
    }
    if (v[index] < 0.) {
        for (double& wert : v) { wert = -wert; }
    }
    return v;
}

inline std::pair<Vektor3, Matrix3> hauptachsen_aufbereiten(
        const Vektor3& werte, const Matrix3& vektoren)
{
    endlich(werte, "Haupttraegheiten"); endlich(vektoren, "Hauptachsen");
    std::array<std::size_t, 3> reihenfolge{2, 1, 0};
    std::stable_sort(reihenfolge.begin(), reihenfolge.end(),
        [&](auto a, auto b) { return werte[a] > werte[b]; });
    Vektor3 sortiert{};
    Matrix3 achsen{};
    for (std::size_t i = 0; i < 3; ++i) {
        const auto quelle = reihenfolge[i];
        sortiert[i] = werte[quelle];
        const auto v = achse_kanonisieren(
            {vektoren[quelle], vektoren[3 + quelle], vektoren[6 + quelle]});
        for (std::size_t j = 0; j < 3; ++j) { achsen[3 * j + i] = v[j]; }
    }
    return {sortiert, achsen};
}

} // namespace segelphysik
