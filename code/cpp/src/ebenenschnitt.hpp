#pragma once

#include "frames.hpp"

namespace segelphysik {

inline Vektor3 kreuzprodukt(const Vektor3& a, const Vektor3& b)
{
    return {a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]};
}

inline double skalarprodukt(const Vektor3& a, const Vektor3& b)
{
    return (a[0] * b[0] + a[1] * b[1]) + a[2] * b[2];
}

inline double paarweise_summe(const double* werte, std::size_t n)
{
    if (n < 8) {
        double summe = -0.;
        for (std::size_t i = 0; i < n; ++i) {
            summe += werte[i];
        }
        return summe;
    }
    if (n <= 128) {
        std::array<double, 8> s{};
        std::copy(werte, werte + 8, s.begin());
        std::size_t i = 8;
        for (; i + 7 < n; i += 8) {
            for (std::size_t j = 0; j < 8; ++j) {
                s[j] += werte[i + j];
            }
        }
        double summe = ((s[0] + s[1]) + (s[2] + s[3]))
            + ((s[4] + s[5]) + (s[6] + s[7]));
        for (; i < n; ++i) {
            summe += werte[i];
        }
        return summe;
    }
    const auto mitte = (n / 2) & ~std::size_t(7);
    return paarweise_summe(werte, mitte)
        + paarweise_summe(werte + mitte, n - mitte);
}

struct VolumenMoment {
    std::vector<double> determinanten;
    Vektor3 moment{};

    void dreieck(const Vektor3& a, const Vektor3& b, const Vektor3& c)
    {
        const double det = skalarprodukt(a, kreuzprodukt(b, c));
        determinanten.push_back(det);
        for (std::size_t i = 0; i < 3; ++i) {
            moment[i] += det * ((a[i] + b[i]) + c[i]);
        }
    }

    double det6() const
    {
        return paarweise_summe(determinanten.data(), determinanten.size());
    }
};

struct EbenenSchnitt {
    Mesh mesh;

    std::pair<double, Vektor3> auswerten(
            const Vektor3& normale, double offset, const Abbruch& abbruch) const
    {
        endlich(normale, "Ebenennormale");
        if (!std::isfinite(offset)) {
            throw std::invalid_argument("Ebenenoffset muss endlich sein");
        }
        std::vector<double> abstaende;
        abstaende.reserve(mesh.punkte.size());
        for (const auto& punkt : mesh.punkte) {
            abstaende.push_back(skalarprodukt(punkt, normale) - offset);
        }
        Vektor3 apex{};
        for (std::size_t i = 0; i < 3; ++i) {
            apex[i] = offset * normale[i];
        }
        VolumenMoment voll;
        std::array<VolumenMoment, 2> eins;
        std::array<VolumenMoment, 3> zwei;
        for (const auto& tri : mesh.dreiecke) {
            abbruch.pruefen();
            std::array<bool, 3> innen{};
            unsigned anzahl = 0;
            for (std::size_t i = 0; i < 3; ++i) {
                innen[i] = abstaende[tri[i]] >= 0.;
                anzahl += innen[i];
            }
            if (anzahl == 0) {
                continue;
            }
            if (anzahl == 3) {
                voll.dreieck(mesh.punkte[tri[0]], mesh.punkte[tri[1]], mesh.punkte[tri[2]]);
                continue;
            }
            std::size_t start = 0;
            while (innen[start] != (anzahl == 1)) {
                ++start;
            }
            if (anzahl == 2) {
                start = (start + 1) % 3;
            }
            const auto ia = tri[start], ib = tri[(start + 1) % 3], ic = tri[(start + 2) % 3];
            const auto& a = mesh.punkte[ia];
            const auto& b = mesh.punkte[ib];
            const auto& c = mesh.punkte[ic];
            const auto schneiden = [&](const Vektor3& p, const Vektor3& q,
                                       double sp, double sq) {
                Vektor3 schnitt{};
                const double anteil = sp / (sp - sq);
                for (std::size_t i = 0; i < 3; ++i) {
                    schnitt[i] = p[i] + (q[i] - p[i]) * anteil;
                }
                return schnitt;
            };
            const auto ac = schneiden(a, c, abstaende[ia], abstaende[ic]);
            if (anzahl == 1) {
                const auto ab = schneiden(a, b, abstaende[ia], abstaende[ib]);
                eins[0].dreieck(a, ab, ac);
                eins[1].dreieck(apex, ac, ab);
            } else {
                const auto bc = schneiden(b, c, abstaende[ib], abstaende[ic]);
                zwei[0].dreieck(a, b, bc);
                zwei[1].dreieck(a, bc, ac);
                zwei[2].dreieck(apex, ac, bc);
            }
        }
        double det = voll.det6();
        auto moment = voll.moment;
        const auto addieren = [&](const VolumenMoment& teil) {
            det += teil.det6();
            for (std::size_t i = 0; i < 3; ++i) {
                moment[i] += teil.moment[i];
            }
        };
        for (const auto& teil : eins) {
            addieren(teil);
        }
        for (const auto& teil : zwei) {
            addieren(teil);
        }
        const double volumen = det / 6.;
        if (!std::isfinite(volumen)) {
            throw std::invalid_argument("Schnittvolumen ist nicht endlich");
        }
        if (volumen <= 1e-15) {
            return {0., {0., 0., 0.}};
        }
        for (double& wert : moment) {
            wert /= 24. * volumen;
        }
        endlich(moment, "Schnittschwerpunkt");
        return {volumen, moment};
    }
};

} // namespace segelphysik
