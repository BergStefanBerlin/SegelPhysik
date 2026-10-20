#pragma once

#include "hydrostatik.hpp"
#include "anzeige.hpp"
#include <list>
#include <map>
#include <optional>

namespace segelphysik {

using Vektor2 = std::array<double, 2>;

struct StatikKontext {
    HydrostatikKontext hydro;
    HydroKontext rollen;
    Vektor6 linear{}, quadratisch{};
    Vektor3 fluid{}, fluidrotation{};
    std::array<double, 7> hydroparameter{};
    std::optional<double> cd, gewicht;
    std::optional<std::pair<Vektor3, Vektor3>> fremdkraft;
    bool kraftmodell{};

    Wrench kraefte(const Matrix3& rotation, const Matrix3& hydrorotation,
                  const Vektor3& position, const Vektor3& geschwindigkeit,
                  const Vektor3& winkelgeschwindigkeit, const Abbruch& abbruch) const
    {
        const auto h = hydro.auswerten(hydrorotation, position, abbruch);
        if (!kraftmodell) {
            return {"simulationsframe", position, h.kraft, h.moment};
        }
        Vektor6 relativ{};
        Vektor3 v{}, omega{};
        for (std::size_t i = 0; i < 3; ++i) {
            relativ[i] = v[i] = geschwindigkeit[i] - fluid[i];
            relativ[i + 3] = omega[i] = winkelgeschwindigkeit[i] - fluidrotation[i];
        }
        const auto drag = widerstand(linear, quadratisch, relativ);
        std::vector<Beitrag> beitraege{
            {"hydrostatik", {"simulationsframe", position, h.kraft, h.moment}},
            {"widerstand", {"simulationsframe", position,
                {drag[0], drag[1], drag[2]}, {drag[3], drag[4], drag[5]}}}};
        auto hydrodynamik = hydrodynamik_beitraege(
            rollen.teile, rotation, position, v, omega, hydroparameter, cd, abbruch);
        beitraege.insert(beitraege.end(), hydrodynamik.begin(), hydrodynamik.end());
        if (fremdkraft) {
            auto punkt = multiplizieren(rotation, fremdkraft->second);
            for (std::size_t i = 0; i < 3; ++i) {
                punkt[i] += position[i];
            }
            beitraege.push_back({"fremdkraft", {
                "simulationsframe", punkt, fremdkraft->first, {}}});
        }
        if (gewicht) {
            beitraege.push_back({"schwerkraft", {
                "simulationsframe", position, {0., 0., -*gewicht}, {}}});
        }
        return aggregiere_kraftbeitraege(beitraege, position, "simulationsframe").first;
    }

    Vektor2 auswerten(double z, double phi, double m, double g, const Abbruch& abbruch) const
    {
        positiv(m, "Masse"); positiv(g, "g");
        const auto rotation = euler_rotation(phi, 0., 0.);
        const auto wrench = kraefte(rotation, rotation, {0., 0., z}, {}, {}, abbruch);
        return {wrench.kraft[2] - (gewicht ? 0. : m * g), wrench.moment[0]};
    }

    Wrench stationaere_kraft(const Vektor6& werte, const Abbruch& abbruch) const
    {
        endlich(werte, "Stationaerer Zustand");
        const auto rotation = quaternion_matrix(quaternion_aus_matrix(
            euler_rotation(werte[4], werte[2], werte[5])));
        const double phi = std::atan2(rotation[7], rotation[8]);
        const double theta = std::asin(std::clamp(-rotation[6], -1., 1.));
        return kraefte(rotation, euler_rotation(phi, theta, 0.),
            {0., 0., werte[1]}, {werte[0], werte[3], 0.}, {}, abbruch);
    }

    std::pair<int, double> kontakt_start(
            double z0, double phi, double schritt, int max_schritte,
            const Abbruch& abbruch) const
    {
        endlich(std::array<double, 3>{z0, phi, schritt}, "Kontaktstart");
        auto volumen = [&](double z) {
            return hydro.auswerten(euler_rotation(phi, 0., 0.), {0., 0., z}, abbruch).volumen;
        };
        const double v0 = volumen(z0);
        double z = z0;
        if (v0 > 0.) {
            if (volumen(z0 + schritt) < v0) {
                return {0, z0};
            }
            for (int i = 0; i < max_schritte; ++i) {
                z += schritt;
                const double v = volumen(z);
                if (v < v0) {
                    return {0, v > 0. ? z : z - .5 * schritt};
                }
            }
            return {1, z};
        }
        for (int i = 0; i < max_schritte; ++i) {
            z -= schritt;
            if (volumen(z) > 0.) {
                return {0, z};
            }
        }
        return {2, z};
    }
};

struct StatikErgebnis {
    Vektor2 lage{}, residuum{};
    int iterationen{}, restarts{};
    bool erfolgreich{}, stagnation{}, neutral{}, stabil{}, robust{};
    std::optional<double> gm;
    std::string status{"fehler"}, meldung;
    std::size_t misses{}, hits{};
};

inline double norm2(const Vektor2& a)
{
    return std::sqrt(a[0] * a[0] + a[1] * a[1]);
}

inline std::optional<Vektor2> linear2(
        const Vektor2& a, const Vektor2& b, const Vektor2& rhs)
{
    double a00 = a[0], a10 = a[1], a01 = b[0], a11 = b[1];
    double r0 = rhs[0], r1 = rhs[1];
    if (std::abs(a10) > std::abs(a00)) {
        std::swap(a00, a10); std::swap(a01, a11); std::swap(r0, r1);
    }
    if (a00 == 0.) {
        return std::nullopt;
    }
    const double faktor = a10 / a00;
    a11 -= faktor * a01;
    r1 -= faktor * r0;
    if (a11 == 0.) {
        return std::nullopt;
    }
    const double y = r1 / a11;
    Vektor2 x{(r0 - a01 * y) / a00, y};
    return std::isfinite(x[0]) && std::isfinite(x[1])
        ? std::optional<Vektor2>{x} : std::nullopt;
}

class StatikSolver {
    const StatikKontext& kontext;
    double masse, gravitation, toleranz;
    const Abbruch& abbruch;
    using CacheEintrag = std::pair<Vektor2, Vektor2>;
    std::list<CacheEintrag> cache;
    std::map<Vektor2, std::list<CacheEintrag>::iterator> index;
    std::size_t hits{}, misses{};
    bool robust;

    Vektor2 r(double z, double phi)
    {
        abbruch.pruefen();
        const Vektor2 key{z, phi};
        endlich(key, "Solverlage");
        if (robust) {
            const auto fund = index.find(key);
            if (fund != index.end()) {
                ++hits;
                cache.splice(cache.begin(), cache, fund->second);
                return fund->second->second;
            }
        }
        ++misses;
        const auto wert = kontext.auswerten(z, phi, masse, gravitation, abbruch);
        endlich(wert, "Solverresiduum");
        if (robust) {
            cache.push_front({key, wert});
            index[key] = cache.begin();
            if (cache.size() > 512) {
                index.erase(cache.back().first);
                cache.pop_back();
            }
        }
        return wert;
    }

    Vektor2 fd(double z, double phi, std::size_t achse)
    {
        const auto start = r(z, phi);
        const std::array<double, 4> schritte{1e-6, 1e-3, .02, achse == 0 ? .1 : .15};
        for (double h : schritte) {
            const auto wert = r(z + (achse == 0 ? h : 0.), phi + (achse == 1 ? h : 0.));
            const Vektor2 d{(wert[0] - start[0]) / h, (wert[1] - start[1]) / h};
            if (norm2(d) > 0.) {
                return d;
            }
        }
        return {};
    }

    std::optional<double> sekante(double z, double phi, std::size_t achse)
    {
        auto f = [&](double x) {
            return r(achse == 0 ? x : z, achse == 1 ? x : phi)[achse];
        };
        double x0 = achse == 0 ? z : phi;
        double delta = achse == 0 ? .05 : .1;
        const double grenze = achse == 0 ? 2. : .5;
        double f0 = f(x0);
        if (std::abs(f0) < 1e-12) {
            return x0;
        }
        double x1 = x0 + delta, f1 = f(x1);
        for (int i = 0; i < 40; ++i) {
            if (!std::isfinite(f1) || std::abs(f1 - f0) < 1e-15) {
                delta *= 2.;
                if (delta > grenze) {
                    break;
                }
                x1 = x0 + delta; f1 = f(x1);
                continue;
            }
            double x2 = x1 - f1 * (x1 - x0) / (f1 - f0);
            if (std::abs(x2 - x1) > grenze) {
                x2 = x1 + std::copysign(grenze, x2 - x1);
            }
            const double f2 = f(x2);
            x0 = x1; f0 = f1; x1 = x2; f1 = f2;
            if (std::abs(f1) < 1e-9 || std::abs(x1 - x0) < 1e-12) {
                return x1;
            }
        }
        return std::isfinite(f1) && std::abs(f1) < std::abs(f0)
            ? std::optional<double>{x1} : std::nullopt;
    }

    double dmdphi(const Vektor2& lage)
    {
        for (double h : {1e-4, 1e-3, .02}) {
            const double d = (r(lage[0], lage[1] + h)[1]
                - r(lage[0], lage[1] - h)[1]) / (2. * h);
            if (std::abs(d) > 0.) {
                return d;
            }
        }
        return 0.;
    }

    std::optional<double> gm(const Vektor2& lage)
    {
        if (!robust && std::abs(lage[1]) > 1e-6) {
            return std::nullopt;
        }
        for (double h : {1e-4, 1e-3, .02}) {
            const double differenz = r(lage[0], (robust ? lage[1] : 0.) + h)[1]
                - r(lage[0], (robust ? lage[1] : 0.) - h)[1];
            if (!robust || std::abs(differenz) > 0.) {
                return -differenz / (2. * h) / (masse * gravitation);
            }
        }
        return std::nullopt;
    }

    StatikErgebnis versuch(Vektor2 lage, int max_iter, double stagnationsanteil)
    {
        auto residuum = r(lage[0], lage[1]);
        StatikErgebnis best;
        best.lage = lage; best.residuum = residuum; best.robust = robust;
        double best_n = norm2(residuum);
        int schlechte = 0;
        for (int it = 1; it <= max_iter; ++it) {
            best.iterationen = it;
            if (robust ? best_n < toleranz
                       : std::abs(residuum[0]) < toleranz && std::abs(residuum[1]) < toleranz) {
                best.status = "konvergiert";
                return best;
            }
            Vektor2 a{}, b{};
            if (robust) {
                a = fd(lage[0], lage[1], 0); b = fd(lage[0], lage[1], 1);
            } else {
                const double hz = std::max(1e-6, std::abs(lage[0]) * 1e-6);
                const auto rz = r(lage[0] + hz, lage[1]);
                const auto rp = r(lage[0], lage[1] + 1e-6);
                for (std::size_t j = 0; j < 2; ++j) {
                    a[j] = (rz[j] - residuum[j]) / hz;
                    b[j] = (rp[j] - residuum[j]) / 1e-6;
                }
            }
            auto schritt = linear2(a, b, {-residuum[0], -residuum[1]});
            if (!schritt) {
                if (!robust) {
                    best.status = "fehler"; best.meldung = "Jacobi singulaer";
                    return best;
                }
                if (auto z = sekante(lage[0], lage[1], 0)) {
                    lage[0] = *z;
                }
                if (std::abs(r(lage[0], lage[1])[1]) > 1e-12) {
                    if (auto phi = sekante(lage[0], lage[1], 1)) {
                        lage[1] = *phi;
                    }
                }
            } else {
                for (const auto achse_grenze : {Vektor2{1., .35}, Vektor2{0., .5}}) {
                    const auto achse = static_cast<std::size_t>(achse_grenze[0]);
                    if (std::abs((*schritt)[achse]) > achse_grenze[1]) {
                        const double faktor = achse_grenze[1] / std::abs((*schritt)[achse]);
                        (*schritt)[0] *= faktor; (*schritt)[1] *= faktor;
                    }
                }
                lage[0] += (*schritt)[0]; lage[1] += (*schritt)[1];
            }
            residuum = r(lage[0], lage[1]);
            const double n = norm2(residuum);
            if (!robust || n < best_n * .99) {
                best_n = n; best.lage = lage; best.residuum = residuum; schlechte = 0;
            } else {
                if (n < best_n) {
                    best_n = n; best.lage = lage; best.residuum = residuum;
                }
                if (++schlechte >= 6) {
                    best.stagnation = best_n <= std::max(toleranz, stagnationsanteil * masse * gravitation);
                    best.status = "stagnation";
                    return best;
                }
            }
        }
        best.stagnation = robust
            && best_n <= std::max(toleranz, stagnationsanteil * masse * gravitation);
        best.status = best.stagnation ? "stagnation" : "budget_erschoepft";
        return best;
    }

    std::optional<double> vertikal(double phi, double z_start)
    {
        const double f_start = r(z_start, phi)[0];
        if (std::abs(f_start) <= toleranz) {
            return z_start;
        }
        double schritt = 1e-4, z_b = z_start;
        bool klammer = false;
        for (int i = 0; i < 24; ++i) {
            z_b = z_start + std::copysign(schritt, f_start);
            if (f_start * r(z_b, phi)[0] <= 0.) {
                klammer = true; break;
            }
            schritt *= 2.;
        }
        if (!klammer) {
            return std::nullopt;
        }
        double links = std::min(z_start, z_b), rechts = std::max(z_start, z_b);
        double f_links = r(links, phi)[0];
        for (int i = 0; i < 64; ++i) {
            const double mitte = (links + rechts) / 2.;
            const double f = r(mitte, phi)[0];
            if (std::abs(f) <= toleranz) {
                return mitte;
            }
            if (f_links * f <= 0.) {
                rechts = mitte;
            } else {
                links = mitte; f_links = f;
            }
        }
        const double beste = std::abs(r(links, phi)[0]) <= std::abs(r(rechts, phi)[0])
            ? links : rechts;
        return std::abs(r(beste, phi)[0]) <= .05 * masse * gravitation
            ? std::optional<double>{beste} : std::nullopt;
    }

    std::optional<StatikErgebnis> rollscan(const Vektor2& start, int restarts)
    {
        std::optional<Vektor3> vorher;
        double z = start[0];
        for (int i = 0; i <= 180; ++i) {
            const double phi = start[1] + i * (2. * 3.14159265358979323846 / 180.);
            auto hoehe = vertikal(phi, z);
            if (!hoehe) {
                vorher.reset(); z = start[0]; continue;
            }
            z = *hoehe;
            const Vektor3 aktuell{phi, z, r(z, phi)[1]};
            if (vorher && (*vorher)[2] * aktuell[2] <= 0.) {
                double links = (*vorher)[0], z_links = (*vorher)[1], m_links = (*vorher)[2];
                double rechts = phi, z_rechts = z;
                for (int j = 0; j < 64; ++j) {
                    const double mitte = (links + rechts) / 2.;
                    auto z_mitte = vertikal(mitte, (z_links + z_rechts) / 2.);
                    if (!z_mitte) {
                        break;
                    }
                    const double m_mitte = r(*z_mitte, mitte)[1];
                    if (std::abs(m_mitte) <= toleranz) {
                        links = rechts = mitte; z_links = z_rechts = *z_mitte; break;
                    }
                    if (m_links * m_mitte <= 0.) {
                        rechts = mitte; z_rechts = *z_mitte;
                    } else {
                        links = mitte; z_links = *z_mitte; m_links = m_mitte;
                    }
                }
                const double kandidat_phi = (links + rechts) / 2.;
                auto kandidat_z = vertikal(kandidat_phi, (z_links + z_rechts) / 2.);
                if (kandidat_z) {
                    const Vektor2 lage{*kandidat_z, kandidat_phi};
                    const auto residuum = r(lage[0], lage[1]);
                    if (dmdphi(lage) < 0.
                            && std::abs(residuum[0]) <= std::max(toleranz, .05 * masse * gravitation)
                            && std::abs(residuum[1]) <= toleranz) {
                        StatikErgebnis ergebnis;
                        ergebnis.lage = lage; ergebnis.residuum = residuum;
                        ergebnis.restarts = restarts; ergebnis.robust = true;
                        ergebnis.erfolgreich = true; ergebnis.stabil = true;
                        ergebnis.stagnation = norm2(residuum) > toleranz;
                        ergebnis.gm = gm(lage);
                        return ergebnis;
                    }
                }
            }
            vorher = aktuell;
        }
        return std::nullopt;
    }

public:
    StatikSolver(const StatikKontext& modell, double m, double g, double tol,
                 bool robust_modus, const Abbruch& stopp)
        : kontext(modell), masse(m), gravitation(g), toleranz(tol),
          abbruch(stopp), robust(robust_modus)
    {
        positiv(m, "Masse"); positiv(g, "g"); positiv(tol, "Solvertoleranz");
    }

    StatikErgebnis loesen(const Vektor2& start, int max_iter, const std::vector<double>& leiter,
                          double stagnationsanteil, double neutral_toleranz)
    {
        endlich(start, "Solverstart"); endlich(leiter, "Stoerleiter");
        endlich(Vektor2{stagnationsanteil, neutral_toleranz}, "Solvertoleranzen");
        if (max_iter < 1 || stagnationsanteil < 0. || neutral_toleranz < 0.) {
            throw std::invalid_argument("Ungueltiges Solverbudget oder Toleranzen");
        }
        Vektor2 aktuelle = start;
        StatikErgebnis ergebnis;
        for (std::size_t restarts = 0;;) {
            ergebnis = versuch(aktuelle, max_iter, stagnationsanteil);
            ergebnis.restarts = static_cast<int>(restarts);
            const bool konvergiert = ergebnis.status == "konvergiert"
                || (robust && ergebnis.status == "stagnation" && ergebnis.stagnation);
            if (konvergiert) {
                const double dM = robust ? dmdphi(ergebnis.lage)
                    : r(ergebnis.lage[0], ergebnis.lage[1] + 1e-6)[1];
                ergebnis.neutral = robust
                    && std::abs(dM) <= neutral_toleranz * std::max(masse * gravitation, 1.)
                    && std::abs(ergebnis.residuum[1]) <= 1e-6 * std::max(masse * gravitation, 1.);
                ergebnis.stabil = dM < 0.;
                if (ergebnis.neutral || ergebnis.stabil) {
                    ergebnis.erfolgreich = true;
                    ergebnis.gm = ergebnis.neutral ? std::nullopt : gm(ergebnis.lage);
                    break;
                }
                if (restarts >= leiter.size()) {
                    if (robust && !leiter.empty()) {
                        if (auto scan = rollscan(start, ergebnis.restarts)) {
                            ergebnis = *scan; break;
                        }
                    }
                    ergebnis.status = robust ? "instabile_lage" : "fehler";
                    ergebnis.meldung = "Stoerleiter erschoepft; instabile Lage";
                    break;
                }
                aktuelle = {ergebnis.lage[0], ergebnis.lage[1]
                    + leiter[restarts] * (3.14159265358979323846 / 180.)};
            } else {
                if (!robust || restarts >= leiter.size()) {
                    if (ergebnis.meldung.empty()) {
                        ergebnis.meldung = "Keine Konvergenz; Iterationsbudget oder Stoerleiter erschoepft";
                    }
                    if (!robust) {
                        ergebnis.status = "fehler";
                    }
                    break;
                }
                aktuelle[1] += leiter[restarts] * (3.14159265358979323846 / 180.);
            }
            ++restarts;
        }
        ergebnis.hits = hits; ergebnis.misses = misses;
        return ergebnis;
    }
};

} // namespace segelphysik
