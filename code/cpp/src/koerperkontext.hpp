#pragma once

#include "frames.hpp"

namespace segelphysik {

struct BlattKontext {
    Mesh mesh;
    Matrix3 rotation;
    Vektor3 translation;
};

struct SnapshotKontext {
    double masse;
    Matrix3 traegheit;
    std::uint64_t version;
    std::vector<BlattKontext> blaetter;

    Modell auswerten(const Abbruch& abbruch) const
    {
        Modell modell{masse, traegheit, {}, version, {0., 0., 0.}};
        for (const auto& blatt : blaetter) {
            abbruch.pruefen();
            const auto& quelle = blatt.mesh;
            const bool hydrodynamisch = quelle.rolle == "rumpf"
                || quelle.rolle == "kiel" || quelle.rolle == "ruder";
            if (!quelle.verdraengend && !hydrodynamisch) {
                continue;
            }
            Mesh mesh = quelle;
            for (auto& punkt : mesh.punkte) {
                punkt = multiplizieren(blatt.rotation, punkt);
                for (std::size_t i = 0; i < 3; ++i) {
                    punkt[i] += blatt.translation[i];
                }
                endlich(punkt, "Snapshotpunkt");
            }
            if (quelle.verdraengend) {
                Mesh verdrangend = mesh;
                verdrangend.rolle.clear();
                modell.meshes.push_back(std::move(verdrangend));
            }
            if (hydrodynamisch) {
                mesh.verdraengend = false;
                modell.meshes.push_back(std::move(mesh));
            }
        }
        modell.pruefen();
        return modell;
    }
};

} // namespace segelphysik
