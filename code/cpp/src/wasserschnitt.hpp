#pragma once

#include "ebenenschnitt.hpp"
#include <map>
#include <optional>
#include <tuple>

namespace segelphysik {

using Ring = std::vector<Vektor3>;
using Gitterpunkt = std::array<std::int64_t, 3>;
constexpr double schnitt_eps = 1e-12;

inline Gitterpunkt gitterpunkt(const Vektor3& punkt, double toleranz)
{
    positiv(toleranz, "Konturtoleranz");
    Gitterpunkt schluessel{};
    for (std::size_t i = 0; i < 3; ++i) {
        const double wert = std::nearbyint(punkt[i] / toleranz);
        if (!std::isfinite(wert)
                || wert < -9223372036854775808. || wert >= 9223372036854775808.) {
            throw std::invalid_argument("Konturpunkt liegt ausserhalb des Int64-Gitters");
        }
        schluessel[i] = static_cast<std::int64_t>(wert);
    }
    return schluessel;
}

inline double punktabstand(const Vektor3& a, const Vektor3& b)
{
    Vektor3 d{};
    for (std::size_t i = 0; i < 3; ++i) {
        d[i] = a[i] - b[i];
    }
    return std::sqrt(skalarprodukt(d, d));
}

inline Ring clip_polygon(const Ring& polygon, double ebene, bool oben)
{
    Ring roh, ergebnis;
    for (std::size_t i = 0; i < polygon.size(); ++i) {
        const auto& a = polygon[i];
        const auto& b = polygon[(i + 1) % polygon.size()];
        const double da = a[2] - ebene, db = b[2] - ebene;
        const bool ia = oben ? da >= 0. : da <= 0.;
        const bool ib = oben ? db >= 0. : db <= 0.;
        if (ia) {
            roh.push_back(a);
        }
        if (ia != ib) {
            const double t = std::abs(da - db) > schnitt_eps ? da / (da - db) : 0.;
            Vektor3 p{};
            for (std::size_t j = 0; j < 3; ++j) {
                p[j] = a[j] + t * (b[j] - a[j]);
            }
            roh.push_back(p);
        }
    }
    for (const auto& p : roh) {
        if (ergebnis.empty() || punktabstand(p, ergebnis.back()) > schnitt_eps) {
            ergebnis.push_back(p);
        }
    }
    if (ergebnis.size() >= 2
            && punktabstand(ergebnis.front(), ergebnis.back()) <= schnitt_eps) {
        ergebnis.pop_back();
    }
    return ergebnis;
}

inline Ring wasserlinie(const Mesh& mesh, double ebene, double toleranz)
{
    std::map<std::array<std::int64_t, 2>, std::size_t> kanten;
    for (const auto& tri : mesh.dreiecke) {
        for (std::size_t i = 0; i < 3; ++i) {
            std::array<std::int64_t, 2> k{tri[i], tri[(i + 1) % 3]};
            std::sort(k.begin(), k.end());
            ++kanten[k];
        }
    }
    Ring rand;
    for (const auto& eintrag : kanten) {
        if (eintrag.second != 1) {
            continue;
        }
        const auto& a = mesh.punkte[eintrag.first[0]];
        const auto& b = mesh.punkte[eintrag.first[1]];
        if (std::abs(a[2] - ebene) <= toleranz && std::abs(b[2] - ebene) <= toleranz) {
            rand.push_back(a);
            rand.push_back(b);
        }
    }
    return rand;
}

inline std::vector<Ring> ketten(const Ring& segmente, double toleranz)
{
    if (segmente.size() % 2 != 0) {
        throw std::invalid_argument("Kontur braucht vollstaendige Segmentpaare");
    }
    const auto n = segmente.size() / 2;
    std::vector<Gitterpunkt> gitter;
    std::map<Gitterpunkt, std::vector<std::size_t>> abgang;
    for (const auto& p : segmente) {
        gitter.push_back(gitterpunkt(p, toleranz));
    }
    for (std::size_t i = 0; i < n; ++i) {
        abgang[gitter[2 * i]].push_back(i);
    }
    std::vector<bool> benutzt(n, false);
    std::vector<Ring> ringe;
    for (std::size_t anfang = 0; anfang < n; ++anfang) {
        if (benutzt[anfang]) {
            continue;
        }
        benutzt[anfang] = true;
        Ring ring{segmente[2 * anfang], segmente[2 * anfang + 1]};
        auto ziel = gitter[2 * anfang + 1];
        const auto start = gitter[2 * anfang];
        std::size_t schritte = 0;
        while (ziel != start && schritte <= n) {
            std::size_t naechster = n;
            const auto gefunden = abgang.find(ziel);
            if (gefunden != abgang.end()) {
                for (const auto j : gefunden->second) {
                    if (!benutzt[j]) {
                        naechster = j;
                        break;
                    }
                }
            }
            if (naechster == n) {
                break;
            }
            benutzt[naechster] = true;
            ring.push_back(segmente[2 * naechster + 1]);
            ziel = gitter[2 * naechster + 1];
            ++schritte;
        }
        if (ziel == start && ring.size() >= 4) {
            ring.pop_back();
            ringe.push_back(std::move(ring));
        }
    }
    return ringe;
}

inline double ringflaeche(const Ring& ring)
{
    std::vector<double> kreuze;
    for (std::size_t i = 0; i < ring.size(); ++i) {
        const auto& a = ring[i];
        const auto& b = ring[(i + 1) % ring.size()];
        kreuze.push_back(a[0] * b[1] - b[0] * a[1]);
    }
    return .5 * paarweise_summe(kreuze.data(), kreuze.size());
}

inline Vektor3 ringzentrum(const Ring& ring)
{
    Vektor3 zentrum{};
    for (const auto& p : ring) {
        for (std::size_t i = 0; i < 3; ++i) {
            zentrum[i] += p[i];
        }
    }
    for (double& wert : zentrum) {
        wert /= static_cast<double>(ring.size());
    }
    return zentrum;
}

inline bool punkt_in_ring(const Vektor3& p, const Ring& ring)
{
    bool innen = false;
    for (std::size_t i = 0; i < ring.size(); ++i) {
        const auto& a = ring[i];
        const auto& b = ring[(i + 1) % ring.size()];
        if ((a[1] > p[1]) != (b[1] > p[1])) {
            const double xs = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]);
            if (p[0] < xs) {
                innen = !innen;
            }
        }
    }
    return innen;
}

inline Ring einzigartige_konturpunkte(const Ring& kontur, double toleranz)
{
    std::map<Gitterpunkt, bool> gesehen;
    Ring punkte;
    for (const auto& p : kontur) {
        if (gesehen.emplace(gitterpunkt(p, toleranz), true).second) {
            punkte.push_back(p);
        }
    }
    return punkte;
}

inline Ring polygonzug(const Ring& kontur, double toleranz)
{
    auto punkte = einzigartige_konturpunkte(kontur, toleranz);
    if (punkte.size() < 3) {
        return punkte;
    }
    const auto zentrum = ringzentrum(punkte);
    std::stable_sort(punkte.begin(), punkte.end(), [&](const Vektor3& a, const Vektor3& b) {
        return std::atan2(a[1] - zentrum[1], a[0] - zentrum[0])
            < std::atan2(b[1] - zentrum[1], b[0] - zentrum[0]);
    });
    Ring behalten{punkte[0]};
    for (std::size_t i = 1; i < punkte.size(); ++i) {
        const double x1 = punkte[i][0] - behalten.back()[0];
        const double y1 = punkte[i][1] - behalten.back()[1];
        const double x2 = punkte[(i + 1) % punkte.size()][0] - punkte[i][0];
        const double y2 = punkte[(i + 1) % punkte.size()][1] - punkte[i][1];
        const double n1 = std::sqrt(x1 * x1 + y1 * y1);
        const double n2 = std::sqrt(x2 * x2 + y2 * y2);
        if (std::abs(x1 * y2 - y1 * x2) > 1e-9 * std::max({n1, n2, 1.})) {
            behalten.push_back(punkte[i]);
        }
    }
    return behalten;
}

inline std::optional<Vektor6> ringmomente(const Ring& ring)
{
    std::array<std::vector<double>, 6> summanden;
    for (std::size_t i = 0; i < ring.size(); ++i) {
        const auto& a = ring[i];
        const auto& b = ring[(i + 1) % ring.size()];
        const double x = a[0], y = a[1], xn = b[0], yn = b[1];
        const double kreuz = x * yn - xn * y;
        summanden[0].push_back(kreuz);
        summanden[1].push_back((x + xn) * kreuz);
        summanden[2].push_back((y + yn) * kreuz);
        summanden[3].push_back((x * x + x * xn + xn * xn) * kreuz);
        summanden[4].push_back((y * y + y * yn + yn * yn) * kreuz);
        summanden[5].push_back((2 * x * y + x * yn + xn * y + 2 * xn * yn) * kreuz);
    }
    Vektor6 s{};
    for (std::size_t i = 0; i < 6; ++i) {
        s[i] = paarweise_summe(summanden[i].data(), summanden[i].size());
    }
    const double flaeche = .5 * s[0];
    if (std::abs(flaeche) <= 1e-15) {
        return std::nullopt;
    }
    return Vektor6{flaeche, flaeche * (s[1] / (6. * flaeche)),
                   flaeche * (s[2] / (6. * flaeche)), s[3] / 12.,
                   s[4] / 12., s[5] / 24.};
}

inline std::vector<Ring> wasserlinien_ringe(const Mesh& mesh, double ebene, double toleranz)
{
    std::map<Gitterpunkt, std::size_t> knoten;
    Ring punkte;
    std::map<std::array<std::size_t, 2>, bool> gesehen;
    std::vector<std::array<std::size_t, 2>> segmente;
    for (const auto& tri : mesh.dreiecke) {
        std::array<Vektor3, 3> ecken{
            mesh.punkte[tri[0]], mesh.punkte[tri[1]], mesh.punkte[tri[2]]};
        std::array<double, 3> d{};
        bool koplanar = true;
        for (std::size_t i = 0; i < 3; ++i) {
            d[i] = ecken[i][2] - ebene;
            koplanar = koplanar && std::abs(d[i]) <= toleranz;
        }
        if (koplanar) {
            continue;
        }
        std::vector<std::size_t> ids;
        for (std::size_t i = 0; i < 3; ++i) {
            const auto j = (i + 1) % 3;
            Vektor3 p{};
            if (std::abs(d[i]) <= toleranz) {
                p = ecken[i];
            } else if (std::abs(d[j]) <= toleranz) {
                p = ecken[j];
            } else if ((d[i] < 0.) != (d[j] < 0.)) {
                const double t = d[i] / (d[i] - d[j]);
                for (std::size_t k = 0; k < 3; ++k) {
                    p[k] = ecken[i][k] + t * (ecken[j][k] - ecken[i][k]);
                }
            } else {
                continue;
            }
            p[2] = ebene;
            const auto key = gitterpunkt(p, toleranz);
            const auto eingefuegt = knoten.emplace(key, punkte.size());
            if (eingefuegt.second) {
                punkte.push_back(p);
            }
            const auto id = eingefuegt.first->second;
            if (std::find(ids.begin(), ids.end(), id) == ids.end()) {
                ids.push_back(id);
            }
        }
        if (ids.size() != 2) {
            continue;
        }
        Vektor3 ab{}, ac{}, pq{};
        for (std::size_t k = 0; k < 3; ++k) {
            ab[k] = ecken[1][k] - ecken[0][k];
            ac[k] = ecken[2][k] - ecken[0][k];
            pq[k] = punkte[ids[1]][k] - punkte[ids[0]][k];
        }
        const auto normale = kreuzprodukt(ab, ac);
        if (skalarprodukt(pq, {-normale[1], normale[0], 0.}) < 0.) {
            std::swap(ids[0], ids[1]);
        }
        std::array<std::size_t, 2> key{ids[0], ids[1]};
        std::sort(key.begin(), key.end());
        if (gesehen.emplace(key, true).second) {
            segmente.push_back({ids[0], ids[1]});
        }
    }
    std::vector<std::vector<std::size_t>> ausgehend(punkte.size()), eingehend(punkte.size());
    std::vector<std::size_t> reihenfolge;
    for (const auto& segment : segmente) {
        if (ausgehend[segment[0]].empty()) {
            reihenfolge.push_back(segment[0]);
        }
        ausgehend[segment[0]].push_back(segment[1]);
        eingehend[segment[1]].push_back(segment[0]);
    }
    for (std::size_t i = 0; i < punkte.size(); ++i) {
        if (ausgehend[i].size() > 1 || eingehend[i].size() > 1
                || ausgehend[i].empty() != eingehend[i].empty()) {
            throw std::invalid_argument(
                "Wasserliniensegmente bilden keine eindeutigen geschlossenen Ringe");
        }
    }
    std::vector<bool> benutzt(punkte.size(), false);
    std::vector<Ring> ringe;
    for (const auto anfang : reihenfolge) {
        if (benutzt[anfang]) {
            continue;
        }
        Ring ring;
        auto aktuell = anfang;
        while (!benutzt[aktuell]) {
            benutzt[aktuell] = true;
            ring.push_back(punkte[aktuell]);
            aktuell = ausgehend[aktuell][0];
        }
        if (aktuell != anfang || ring.size() < 3) {
            throw std::invalid_argument("Offener oder entarteter Wasserlinienring");
        }
        ringe.push_back(std::move(ring));
    }
    return ringe;
}

inline void deckel_setzen(Mesh& mesh, double ebene, bool oben, const Ring* rand = nullptr)
{
    if (mesh.dreiecke.empty()) {
        return;
    }
    const auto segmente = rand ? *rand : wasserlinie(mesh, ebene, 1e-9);
    auto ringe = ketten(segmente, 1e-7);
    std::stable_sort(ringe.begin(), ringe.end(), [](const Ring& a, const Ring& b) {
        return std::abs(ringflaeche(a)) > std::abs(ringflaeche(b));
    });
    std::vector<Ring> aeussere;
    for (const auto& ring : ringe) {
        const auto zentrum = ringzentrum(ring);
        bool innen = false;
        for (const auto& aussen : aeussere) {
            innen = innen || punkt_in_ring(zentrum, aussen);
        }
        if (!innen) {
            aeussere.push_back(ring);
        }
    }
    for (auto ring : aeussere) {
        const double flaeche = ringflaeche(ring);
        if (std::abs(flaeche) < 1e-14) {
            continue;
        }
        if ((flaeche > 0.) == oben) {
            std::reverse(ring.begin(), ring.end());
        }
        auto zentrum = ringzentrum(ring);
        zentrum[2] = ebene;
        const auto basis = static_cast<std::int64_t>(mesh.punkte.size());
        const auto n = static_cast<std::int64_t>(ring.size());
        mesh.punkte.insert(mesh.punkte.end(), ring.begin(), ring.end());
        mesh.punkte.push_back(zentrum);
        for (std::int64_t i = 0; i < n; ++i) {
            mesh.dreiecke.push_back({basis + n, basis + i, basis + (i + 1) % n});
        }
    }
}

struct WasserSchnitt {
    Mesh unten, oben;
    Ring kontur;
};

inline WasserSchnitt wasserschnitt(
        const Mesh& quelle, double ebene, bool mit_deckel, const Abbruch& abbruch)
{
    if (!std::isfinite(ebene)) {
        throw std::invalid_argument("Schnittebene muss endlich sein");
    }
    WasserSchnitt ergebnis;
    std::vector<std::size_t> geschnitten;
    bool direkt = true;
    const auto anhaengen = [](Mesh& mesh, const std::array<Vektor3, 3>& tri) {
        const auto basis = static_cast<std::int64_t>(mesh.punkte.size());
        mesh.punkte.insert(mesh.punkte.end(), tri.begin(), tri.end());
        mesh.dreiecke.push_back({basis, basis + 1, basis + 2});
    };
    for (std::size_t i = 0; i < quelle.dreiecke.size(); ++i) {
        abbruch.pruefen();
        const auto& indizes = quelle.dreiecke[i];
        std::array<Vektor3, 3> tri{};
        bool oben = true, unten = true;
        for (std::size_t j = 0; j < 3; ++j) {
            tri[j] = quelle.punkte[indizes[j]];
            const double d = tri[j][2] - ebene;
            oben = oben && d >= -schnitt_eps;
            unten = unten && d <= schnitt_eps;
            direkt = direkt && std::abs(d) > schnitt_eps;
        }
        if (oben) {
            anhaengen(ergebnis.oben, tri);
        } else if (unten) {
            anhaengen(ergebnis.unten, tri);
        } else {
            geschnitten.push_back(i);
        }
    }
    for (const bool oben : {false, true}) {
        auto& ziel = oben ? ergebnis.oben : ergebnis.unten;
        for (std::size_t ecke = 0; ecke < 3; ++ecke) {
            for (unsigned art = 0; art < 3; ++art) {
                for (const auto index : geschnitten) {
                    abbruch.pruefen();
                    const auto& indizes = quelle.dreiecke[index];
                    std::array<Vektor3, 3> tri{}, schnitte{};
                    std::array<double, 3> d{};
                    std::array<bool, 3> innen{};
                    unsigned anzahl = 0;
                    for (std::size_t j = 0; j < 3; ++j) {
                        tri[j] = quelle.punkte[indizes[j]];
                        d[j] = tri[j][2] - ebene;
                        innen[j] = oben ? d[j] >= 0. : d[j] <= 0.;
                        anzahl += innen[j];
                    }
                    if (art == 0 ? !(anzahl == 1 && innen[ecke])
                                 : !(anzahl == 2 && !innen[ecke])) {
                        continue;
                    }
                    for (std::size_t j = 0; j < 3; ++j) {
                        const auto k = (j + 1) % 3;
                        const double nenner = d[j] - d[k];
                        const double t = std::abs(nenner) > schnitt_eps ? d[j] / nenner : 0.;
                        for (std::size_t l = 0; l < 3; ++l) {
                            schnitte[j][l] = tri[j][l] + t * (tri[k][l] - tri[j][l]);
                        }
                        schnitte[j][2] = ebene;
                    }
                    std::array<Vektor3, 3> ausgabe{};
                    const auto start = (ecke + 1) % 3, ende = (ecke + 2) % 3;
                    if (art == 0) {
                        ausgabe = {tri[ecke], schnitte[ecke], schnitte[ende]};
                    } else if (art == 1) {
                        ausgabe = {tri[start], tri[ende], schnitte[ende]};
                    } else {
                        ausgabe = {tri[start], schnitte[ende], schnitte[ecke]};
                    }
                    if (punktabstand(ausgabe[0], ausgabe[1]) > schnitt_eps
                            && punktabstand(ausgabe[1], ausgabe[2]) > schnitt_eps
                            && punktabstand(ausgabe[2], ausgabe[0]) > schnitt_eps) {
                        anhaengen(ziel, ausgabe);
                    }
                }
            }
        }
    }
    if (direkt) {
        for (const auto& indizes : quelle.dreiecke) {
            bool positiv = false, negativ = false;
            for (const auto j : indizes) {
                positiv = positiv || quelle.punkte[j][2] > ebene;
                negativ = negativ || quelle.punkte[j][2] < ebene;
            }
            if (!positiv || !negativ) {
                continue;
            }
            for (std::size_t j = 0; j < 3; ++j) {
                const auto& a = quelle.punkte[indizes[j]];
                const auto& b = quelle.punkte[indizes[(j + 1) % 3]];
                const double da = a[2] - ebene, db = b[2] - ebene;
                if ((da < 0. && db > 0.) || (da > 0. && db < 0.)) {
                    Vektor3 p{};
                    const double t = -da / (db - da);
                    for (std::size_t k = 0; k < 3; ++k) {
                        p[k] = a[k] + t * (b[k] - a[k]);
                    }
                    p[2] = ebene;
                    ergebnis.kontur.push_back(p);
                }
            }
        }
    } else {
        ergebnis.kontur = wasserlinie(ergebnis.unten, ebene, 1e-9);
        const auto oben = wasserlinie(ergebnis.oben, ebene, 1e-9);
        ergebnis.kontur.insert(ergebnis.kontur.end(), oben.begin(), oben.end());
    }
    if (mit_deckel) {
        deckel_setzen(ergebnis.unten, ebene, false, direkt ? &ergebnis.kontur : nullptr);
        deckel_setzen(ergebnis.oben, ebene, true, direkt ? &ergebnis.kontur : nullptr);
    }
    return ergebnis;
}

} // namespace segelphysik
