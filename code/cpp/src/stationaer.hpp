#pragma once

#include "statik.hpp"
#include "dynamik.hpp"

namespace segelphysik {

struct StationaererNachlauf {
    Zustand zustand;
    double vergangen{};
    std::optional<Vektor3> mitte;
    std::optional<std::string> fehler;
};

inline StationaererNachlauf stationaerer_nachlauf(
        const StatikKontext& modell, const Zustand& start, double masse,
        const Matrix3& inertia, const Parameter& parameter, double dauer,
        const Abbruch& abbruch)
{
    positiv(dauer, "Pruefdauer"); dynamik_traegheit_pruefen(masse, inertia);
    parameter.pruefen();
    PhysikKontext physik{
        modell.hydro, modell.rollen, modell.hydroparameter, modell.cd,
        masse, inertia, parameter};
    StationaererNachlauf ergebnis{start, 0., {}, {}};
    const auto q0 = quaternion_normalisieren(
        {start.werte[3], start.werte[4], start.werte[5], start.werte[6]});
    while (ergebnis.vergangen < dauer) {
        abbruch.pruefen();
        physik.parameter.dt = std::min(parameter.dt, dauer - ergebnis.vergangen);
        try {
            ergebnis.zustand = physik.schritt(
                ergebnis.zustand, modell.fremdkraft, modell.hydroparameter[6],
                abbruch, true, modell.gewicht).zustand;
        } catch (const std::invalid_argument& fehler) {
            ergebnis.fehler = std::string("ValueError: ") + fehler.what(); break;
        } catch (const std::overflow_error& fehler) {
            ergebnis.fehler = std::string("OverflowError: ") + fehler.what(); break;
        }
        ergebnis.vergangen += physik.parameter.dt;
        if (!ergebnis.mitte && ergebnis.vergangen >= dauer / 2.) {
            const auto& z = ergebnis.zustand.werte;
            const Vektor4 q{z[3], z[4], z[5], z[6]};
            const auto v = multiplizieren(quaternion_matrix(q), Vektor3{z[7], z[8], z[9]});
            double dot = 0.;
            for (std::size_t i = 0; i < 4; ++i) {
                dot += q0[i] * q[i];
            }
            ergebnis.mitte = Vektor3{
                2. * std::acos(std::clamp(std::abs(dot), 0., 1.)),
                std::sqrt(z[10] * z[10] + z[11] * z[11] + z[12] * z[12]),
                std::sqrt(v[1] * v[1] + v[2] * v[2])};
        }
    }
    return ergebnis;
}

struct StationaereWerte {
    Vektor6 werte{};
    Vektor3 kraft{}, moment{};
    int iterationen{};
    bool konvergiert{};
    std::string fehler;
};

inline std::optional<Vektor6> linear6(
        std::array<double, 36> a, Vektor6 b, std::size_t n)
{
    for (std::size_t k = 0; k < n; ++k) {
        std::size_t pivot = k;
        for (std::size_t i = k + 1; i < n; ++i) {
            if (std::abs(a[6 * i + k]) > std::abs(a[6 * pivot + k])) {
                pivot = i;
            }
        }
        if (a[6 * pivot + k] == 0.) {
            return std::nullopt;
        }
        if (pivot != k) {
            for (std::size_t j = 0; j < n; ++j) {
                std::swap(a[6 * pivot + j], a[6 * k + j]);
            }
            std::swap(b[pivot], b[k]);
        }
        for (std::size_t i = k + 1; i < n; ++i) {
            const double faktor = a[6 * i + k] / a[6 * k + k];
            for (std::size_t j = k + 1; j < n; ++j) {
                a[6 * i + j] -= faktor * a[6 * k + j];
            }
            b[i] -= faktor * b[k];
        }
    }
    Vektor6 x{};
    for (int i = static_cast<int>(n) - 1; i >= 0; --i) {
        double wert = b[i];
        for (std::size_t j = i + 1; j < n; ++j) {
            wert -= a[6 * i + j] * x[j];
        }
        x[i] = wert / a[6 * i + i];
    }
    return x;
}

inline StationaereWerte stationaere_stufe(
        const StatikKontext& kontext, Vektor6 werte, int stufe,
        double kraftskala, double laenge, double geschwindigkeit,
        double toleranz, int max_iter, const Abbruch& abbruch)
{
    positiv(kraftskala, "Kraftskala"); positiv(laenge, "Laengenskala");
    positiv(geschwindigkeit, "Geschwindigkeitsskala"); positiv(toleranz, "Toleranz");
    endlich(werte, "Stationaerer Startwert");
    if ((stufe != 1 && stufe != 2) || max_iter < 1 || toleranz > .01) {
        throw std::invalid_argument("Ungueltige stationaere Stufe oder Iterationsparameter");
    }
    const double momentskala = kraftskala * laenge;
    const Vektor6 skalen{geschwindigkeit, laenge, 1., geschwindigkeit, 1., 1.};
    const std::size_t n = stufe == 1 ? 3 : 6;
    auto residuum = [&](const Vektor6& probe) {
        const auto wrench = kontext.stationaere_kraft(probe, abbruch);
        Vektor6 r{};
        if (stufe == 1) {
            r = {wrench.kraft[0] / kraftskala, wrench.kraft[2] / kraftskala,
                 wrench.moment[1] / momentskala, 0., 0., 0.};
        } else {
            for (std::size_t i = 0; i < 3; ++i) {
                r[i] = wrench.kraft[i] / kraftskala;
                r[i + 3] = wrench.moment[i] / momentskala;
            }
        }
        endlich(r, "Stationaeres Residuum");
        return r;
    };
    auto norm = [&](const Vektor6& r) {
        double summe = 0.;
        for (std::size_t i = 0; i < n; ++i) {
            summe += r[i] * r[i];
        }
        return std::sqrt(summe);
    };
    auto norm_inf = [&](const Vektor6& r) {
        double maximum = 0.;
        for (std::size_t i = 0; i < n; ++i) {
            maximum = std::max(maximum, std::abs(r[i]));
        }
        return maximum;
    };
    StationaereWerte ergebnis;
    for (int iteration = 1; iteration <= max_iter; ++iteration) {
        ergebnis.iterationen = iteration;
        const auto r = residuum(werte);
        if (norm_inf(r) <= toleranz) {
            ergebnis.konvergiert = true;
            break;
        }
        std::array<double, 36> jacobi{};
        for (std::size_t spalte = 0; spalte < n; ++spalte) {
            const double h = 1e-5 * std::max(1., std::abs(werte[spalte] / skalen[spalte]));
            auto probe = werte;
            probe[spalte] += h * skalen[spalte];
            const auto versetzt = residuum(probe);
            for (std::size_t zeile = 0; zeile < n; ++zeile) {
                jacobi[6 * zeile + spalte] = (versetzt[zeile] - r[zeile]) / h;
            }
        }
        Vektor6 rechts{};
        for (std::size_t i = 0; i < n; ++i) {
            rechts[i] = -r[i];
        }
        auto delta = linear6(jacobi, rechts, n);
        if (!delta) {
            ergebnis.fehler = "Singulaere Jacobi"; break;
        }
        bool endlich = true;
        for (double wert : *delta) {
            endlich = endlich && std::isfinite(wert);
        }
        if (!endlich) {
            ergebnis.fehler = "Nicht-endlicher Newton-Schritt"; break;
        }
        for (double& wert : *delta) {
            wert = std::clamp(wert, -.5, .5);
        }
        const double basis_norm = norm(r);
        bool verbessert = false;
        for (double daempfung : {1., .5, .25, .125, .0625}) {
            auto probe = werte;
            for (std::size_t i = 0; i < n; ++i) {
                probe[i] += daempfung * (*delta)[i] * skalen[i];
            }
            if (norm(residuum(probe)) < basis_norm) {
                werte = probe; verbessert = true; break;
            }
        }
        if (!verbessert) {
            ergebnis.fehler = "Newton-Stufe verbessert das Residuum nicht"; break;
        }
    }
    const auto wrench = kontext.stationaere_kraft(werte, abbruch);
    ergebnis.werte = werte;
    ergebnis.kraft = wrench.kraft; ergebnis.moment = wrench.moment;
    ergebnis.konvergiert = ergebnis.konvergiert && norm_inf(residuum(werte)) <= toleranz;
    return ergebnis;
}

} // namespace segelphysik
