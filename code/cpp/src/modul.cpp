#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <optional>

#include "datentypen.hpp"
#include "frames.hpp"
#include "koerperkontext.hpp"
#include "ebenenschnitt.hpp"
#include "wasserschnitt.hpp"
#include "hydrodynamik.hpp"
#include "kraftmodell.hpp"
#include "hydrostatik.hpp"
#include "dynamik.hpp"
#include "anzeige.hpp"
#include "statik.hpp"
#include "stationaer.hpp"
#include "massen.hpp"
#include "interaktion.hpp"
#include "navigation.hpp"
#include "wasserpunkte.hpp"
#include "mesh_pruefung.hpp"
#include "kraftgeometrie.hpp"
#include "wasser_render.hpp"
#include "wasserpartikel.hpp"
#include "voxel.hpp"
#include "grafikgeometrie.hpp"
#include "formen.hpp"
#include "mesh_import.hpp"

namespace py = pybind11;
namespace sp = segelphysik;

namespace {

template <typename T>
py::array_t<T> array_pruefen(const py::array& array, py::ssize_t dimensionen,
                           py::ssize_t spalten, const char* name)
{
    if (!array.dtype().equal(py::dtype::of<T>())) {
        throw py::type_error(std::string(name) + " hat einen falschen Datentyp");
    }
    if (array.ndim() != dimensionen || array.shape(dimensionen - 1) != spalten) {
        throw py::value_error(std::string(name) + " hat eine falsche Arrayform");
    }
    return py::reinterpret_borrow<py::array_t<T>>(array);
}

template <std::size_t N>
std::array<double, N> vektor(const py::array& array, const char* name)
{
    const auto daten = array_pruefen<double>(array, 1, N, name).unchecked<1>();
    std::array<double, N> werte{};
    for (std::size_t i = 0; i < N; ++i) {
        werte[i] = daten(i);
    }
    sp::endlich(werte, name);
    return werte;
}

sp::Matrix3 matrix(const py::array& array)
{
    const auto geprueft = array_pruefen<double>(array, 2, 3, "Traegheit");
    if (array.shape(0) != 3) {
        throw py::value_error("Traegheit muss eine 3x3-Matrix sein");
    }
    const auto daten = geprueft.unchecked<2>();
    sp::Matrix3 werte{};
    for (std::size_t i = 0; i < 3; ++i) {
        for (std::size_t j = 0; j < 3; ++j) {
            werte[3 * i + j] = daten(i, j);
        }
    }
    return werte;
}

template <std::size_t N>
py::array_t<double> ausgabe(const std::array<double, N>& werte)
{
    py::array_t<double> array(N);
    std::copy(werte.begin(), werte.end(), array.mutable_data());
    return array;
}

template <typename T, std::size_t N>
py::array_t<T> mesh_array(const std::vector<std::array<T, N>>& werte)
{
    py::array_t<T> array({static_cast<py::ssize_t>(werte.size()), py::ssize_t(N)});
    auto daten = array.template mutable_unchecked<2>();
    for (py::ssize_t i = 0; i < static_cast<py::ssize_t>(werte.size()); ++i) {
        for (py::ssize_t j = 0; j < N; ++j) {
            daten(i, j) = werte[i][j];
        }
    }
    return array;
}

template <typename T, std::size_t N>
std::vector<std::array<T, N>> array_zeilen(const py::array& array, const char* name)
{
    const auto quelle = array_pruefen<T>(array, 2, N, name).template unchecked<2>();
    std::vector<std::array<T, N>> werte(array.shape(0));
    for (py::ssize_t i = 0; i < array.shape(0); ++i) {
        for (std::size_t j = 0; j < N; ++j) {
            werte[i][j] = quelle(i, j);
        }
    }
    return werte;
}

template <typename T>
std::vector<T> array_werte(const py::array& array, const char* name)
{
    const auto quelle = array_pruefen<T>(array, 1, array.size(), name).template unchecked<1>();
    std::vector<T> werte(array.size());
    for (py::ssize_t i = 0; i < array.size(); ++i) {
        werte[i] = quelle(i);
    }
    return werte;
}

py::array_t<double> punkte_transformieren(
        const sp::Pose& pose, const std::vector<sp::Vektor3>& punkte)
{
    py::array_t<double> array({static_cast<py::ssize_t>(punkte.size()), py::ssize_t(3)});
    double* ziel = array.mutable_data();
    {
        py::gil_scoped_release frei;
        const auto rotation = sp::quaternion_matrix(pose.quaternion);
        for (std::size_t i = 0; i < punkte.size(); ++i) {
            const auto& wert = punkte[i];
            const double x = wert[0], y = wert[1], z = wert[2];
            ziel[3 * i] = (rotation[0] * x + rotation[1] * y)
                + rotation[2] * z + pose.translation[0];
            ziel[3 * i + 1] = (rotation[3] * x + rotation[4] * y)
                + rotation[5] * z + pose.translation[1];
            ziel[3 * i + 2] = (rotation[6] * x + rotation[7] * y)
                + rotation[8] * z + pose.translation[2];
        }
        for (std::size_t i = 0; i < punkte.size() * 3; ++i) {
            if (!std::isfinite(ziel[i])) {
                throw std::invalid_argument("Transformierte Punkte sind nicht endlich");
            }
        }
    }
    return array;
}

py::dict pfeil_daten(const sp::PfeilGeometrie& pfeil, bool fest = false)
{
    py::dict daten;
    daten["start"] = ausgabe(pfeil.start);
    daten["schaft_start"] = ausgabe(pfeil.start);
    daten["richtung"] = ausgabe(pfeil.richtung);
    daten["schaft_ende"] = ausgabe(pfeil.schaft_ende);
    daten["spitze"] = ausgabe(pfeil.spitze);
    daten["laenge"] = pfeil.laenge;
    daten["kopf_laenge"] = pfeil.kopf_laenge;
    daten["kopf_radius"] = pfeil.kopf_radius;
    if (fest) {
        daten["betrag"] = pfeil.betrag;
        daten["schaft_radius"] = pfeil.schaft_radius;
    }
    return daten;
}

sp::WasserRaster wasser_raster(const py::array& array)
{
    if (array.ndim() != 2) {
        throw py::value_error("Wasserraster muss zweidimensional sein");
    }
    const auto daten = array_pruefen<double>(array, 2, array.shape(1),
        "Wasserraster").unchecked<2>();
    sp::WasserRaster raster{static_cast<std::size_t>(array.shape(0)),
        static_cast<std::size_t>(array.shape(1)), {}};
    raster.werte.resize(sp::rastergroesse(raster.ny, raster.nx));
    for (std::size_t y = 0; y < raster.ny; ++y) {
        for (std::size_t x = 0; x < raster.nx; ++x) {
            raster.werte[y * raster.nx + x] = daten(y, x);
        }
    }
    return raster;
}

py::array_t<double> raster_ausgabe(const sp::WasserRaster& raster)
{
    py::array_t<double> array({static_cast<py::ssize_t>(raster.ny),
        static_cast<py::ssize_t>(raster.nx)});
    std::copy(raster.werte.begin(), raster.werte.end(), array.mutable_data());
    return array;
}

sp::Vektor3 kamera_vektor(const py::array& array)
{
    const auto daten = array_pruefen<double>(array, 1, 3, "Kameravektor").unchecked<1>();
    // Eine ungueltige Ausgangsansicht hat vertragsgemaess keine Kameralage.
    return {daten(0), daten(1), daten(2)};
}

} // namespace

PYBIND11_MODULE(_segelphysik_native, modul)
{
    modul.doc() = "Native C++-Anbindung fuer SegelPhysik";
    modul.attr("ABI_VERSION") = 1;
    modul.attr("RECHENPFAD") = "cpp/datenschicht";

    modul.def("form_huellflaechen", [](const py::array& punkte, double toleranz) {
        const auto p = array_zeilen<double, 3>(punkte, "Huellpunkte");
        std::vector<sp::FormHuellFlaeche> flaechen;
        {
            py::gil_scoped_release frei;
            flaechen = sp::form_huellflaechen(p, toleranz);
        }
        py::list ausgaben;
        for (const auto& flaeche : flaechen) {
            py::array_t<std::int64_t> ids(flaeche.indices.size());
            py::array_t<double> winkel(flaeche.winkel.size());
            std::copy(flaeche.indices.begin(), flaeche.indices.end(), ids.mutable_data());
            std::copy(flaeche.winkel.begin(), flaeche.winkel.end(), winkel.mutable_data());
            ausgaben.append(py::make_tuple(ids, winkel));
        }
        return ausgaben;
    });
    modul.def("form_huelldreiecke", [](const py::array& punkte,
                                     const std::vector<py::array>& ordnungen) {
        const auto p = array_zeilen<double, 3>(punkte, "Huellpunkte");
        std::vector<std::vector<std::int64_t>> ids;
        for (const auto& ordnung : ordnungen) {
            ids.push_back(array_werte<std::int64_t>(ordnung, "Huellindizes"));
        }
        std::vector<std::array<std::int64_t, 3>> f;
        {
            py::gil_scoped_release frei;
            f = sp::form_huelldreiecke(p, ids);
        }
        return mesh_array(f);
    });
    modul.def("form_faecher", [](const std::vector<std::vector<std::int64_t>>& polygone) {
        std::vector<std::array<std::int64_t, 3>> f;
        {
            py::gil_scoped_release frei;
            f = sp::form_faecher(polygone);
        }
        return mesh_array(f);
    });
    modul.def("polygon_selbstschnitt", [](const py::array& punkte, double toleranz) {
        const auto zeilen = array_zeilen<double, 2>(punkte, "Polygonpunkte");
        bool ergebnis;
        {
            py::gil_scoped_release frei;
            ergebnis = sp::polygon_selbstschnitt(zeilen, toleranz);
        }
        return ergebnis;
    });
    modul.def("polygon_triangulieren", [](const py::array& punkte, const py::array& index) {
        const auto zeilen = array_zeilen<double, 3>(punkte, "Polygonpunkte");
        const auto indices = array_werte<std::int64_t>(index, "Polygonindizes");
        std::vector<std::array<std::int64_t, 3>> dreiecke;
        {
            py::gil_scoped_release frei;
            dreiecke = sp::polygon_triangulieren(zeilen, indices);
        }
        py::list ausgaben;
        for (const auto& f : dreiecke) { ausgaben.append(py::make_tuple(f[0], f[1], f[2])); }
        return ausgaben;
    });
    modul.def("obj_transformieren", [](const py::array& punkte,
                                     const py::array& rotation, double skala) {
        const auto quelle = array_zeilen<double, 3>(punkte, "OBJ-Punkte");
        const auto r = matrix(rotation);
        std::vector<sp::Vektor3> ziel;
        {
            py::gil_scoped_release frei;
            ziel = sp::obj_transformieren(quelle, r, skala);
        }
        return mesh_array(ziel);
    });
    modul.def("form_mesh", [](int typ, const py::array& parameter,
                             std::size_t nseg, bool liegend) {
        const auto p = vektor<3>(parameter, "Formparameter");
        sp::Mesh mesh;
        {
            py::gil_scoped_release frei;
            mesh = sp::form_mesh(typ, p, nseg, liegend);
        }
        return py::make_tuple(mesh_array(mesh.punkte), mesh_array(mesh.dreiecke));
    });
    modul.def("form_ring", [](double r, double z, std::size_t n, double versatz) {
        std::vector<sp::Vektor3> punkte;
        {
            py::gil_scoped_release frei;
            punkte = sp::form_ring(r, z, n, versatz);
        }
        return mesh_array(punkte);
    });
    modul.def("form_schwerpunkt", [](const sp::Mesh& mesh) {
        sp::Vektor3 zentrum;
        {
            py::gil_scoped_release frei;
            zentrum = sp::form_schwerpunkt(mesh);
        }
        return ausgabe(zentrum);
    });
    modul.def("form_zentrieren", [](const sp::Mesh& mesh) {
        sp::Mesh zentriert;
        {
            py::gil_scoped_release frei;
            zentriert = sp::form_zentrieren(mesh);
        }
        return py::make_tuple(mesh_array(zentriert.punkte), mesh_array(zentriert.dreiecke));
    });
    modul.def("form_liegend", [](const py::array& punkte) {
        auto zeilen = array_zeilen<double, 3>(punkte, "Formpunkte");
        {
            py::gil_scoped_release frei;
            sp::form_liegend(zeilen);
        }
        return mesh_array(zeilen);
    });
    modul.def("instrument_aufbereitung", &sp::instrument_aufbereitung);
    modul.def("svg_rahmen", &sp::svg_rahmen);
    modul.def("geschwindigkeitseinheiten", &sp::geschwindigkeitseinheiten);
    modul.def("kameralage", [](const py::array& position, const py::array& fokus,
                             const std::optional<double>& heading) -> py::object {
        const auto p = kamera_vektor(position), f = kamera_vektor(fokus);
        std::optional<sp::KameraLage> lage;
        {
            py::gil_scoped_release frei;
            lage = sp::kameralage(p, f, heading);
        }
        return lage ? py::cast(*lage) : py::none();
    });
    modul.def("kamera_aktualisieren", [](const py::array& position,
            const py::array& fokus, const py::array& oben, const py::array& ziel,
            const std::optional<double>& heading, const std::optional<double>& letzter_heading,
            const std::optional<sp::KameraLage>& alt) -> py::object {
        const auto p = kamera_vektor(position), f = kamera_vektor(fokus);
        const auto o = vektor<3>(oben, "Kameraoben"), z = vektor<3>(ziel, "Kameraziel");
        std::optional<sp::KameraUpdate> neu;
        {
            py::gil_scoped_release frei;
            neu = sp::kamera_aktualisieren(p, f, o, z, heading, letzter_heading, alt);
        }
        if (!neu) { return py::none(); }
        return py::make_tuple(neu->lage, neu->heading, ausgabe(neu->position),
            ausgabe(neu->oben), neu->geaendert);
    });
    modul.def("grafik_transformieren", [](const py::array& rotation,
            const py::array& translation, const std::vector<py::array>& meshes) {
        const auto r = matrix(rotation);
        sp::rotation_pruefen(r);
        const auto t = vektor<3>(translation, "Grafiktranslation");
        std::vector<std::vector<sp::Vektor3>> daten;
        for (const auto& p : meshes) {
            daten.push_back(array_zeilen<double, 3>(p, "Grafikpunkte"));
        }
        {
            py::gil_scoped_release frei;
            for (auto& p : daten) { p = sp::grafik_punkte(p, r, t); }
        }
        py::list ziel;
        for (const auto& p : daten) { ziel.append(mesh_array(p)); }
        return ziel;
    });
    modul.def("grafik_hauptachsen", [](const py::array& punkte,
            const py::array& eigenvektoren, const py::array& rotation) {
        const auto p = array_zeilen<double, 3>(punkte, "Grafikpunkte");
        const auto eigen = matrix(eigenvektoren);
        const auto r = matrix(rotation);
        std::pair<sp::Matrix3, sp::Vektor3> ergebnis;
        {
            py::gil_scoped_release frei;
            ergebnis = sp::grafik_hauptachsen(p, eigen, r);
        }
        py::array_t<double> richtungen({3, 3});
        std::copy(ergebnis.first.begin(), ergebnis.first.end(),
                  richtungen.mutable_data());
        return py::make_tuple(richtungen, ausgabe(ergebnis.second));
    });
    modul.def("grafik_farbgeometrie", [](const py::array& eltern,
            const py::array& rotationen, const py::array& translationen,
            const py::array& zentren, const py::array& blaetter,
            const std::vector<py::array>& meshes) {
        const auto e = array_werte<std::int64_t>(eltern, "Grafikeltern");
        const auto r = array_zeilen<double, 9>(rotationen, "Grafikrotationen");
        const auto t = array_zeilen<double, 3>(translationen, "Grafiktranslationen");
        const auto z = array_zeilen<double, 3>(zentren, "Grafikzentren");
        const auto b = array_werte<std::int64_t>(blaetter, "Grafikblaetter");
        std::vector<std::vector<sp::Vektor3>> daten;
        for (const auto& p : meshes) {
            daten.push_back(array_zeilen<double, 3>(p, "Grafikpunkte"));
        }
        {
            py::gil_scoped_release frei;
            daten = sp::grafik_farbgeometrie(e, r, t, z, b, daten);
        }
        py::list ziel;
        for (const auto& p : daten) { ziel.append(mesh_array(p)); }
        return ziel;
    });
    modul.def("grafik_meshes_vereinen", [](const std::vector<sp::Mesh>& meshes) {
        sp::Mesh ziel;
        {
            py::gil_scoped_release frei;
            ziel = sp::grafik_meshes_vereinen(meshes);
        }
        return py::make_tuple(mesh_array(ziel.punkte), mesh_array(ziel.dreiecke));
    });
    modul.def("grafik_dreieckszellen", [](const py::array& dreiecke) {
        const auto quelle = array_zeilen<std::int64_t, 3>(dreiecke, "Grafikdreiecke");
        std::vector<std::array<std::int64_t, 4>> ziel;
        {
            py::gil_scoped_release frei;
            ziel = sp::grafik_dreieckszellen(quelle);
        }
        return mesh_array(ziel);
    });
    modul.def("wasser_upsample", [](const py::array& raster, std::size_t faktor) {
        const auto quelle = wasser_raster(raster);
        sp::WasserRaster ziel;
        {
            py::gil_scoped_release frei;
            ziel = sp::bilinear_upsample(quelle, faktor);
        }
        return raster_ausgabe(ziel);
    });
    modul.def("wasser_glaetten", [](const py::array& raster, double dx,
                                  std::int64_t durchlaeufe) {
        auto quelle = wasser_raster(raster);
        sp::WasserRaster ziel;
        {
            py::gil_scoped_release frei;
            ziel = sp::wasser_glaetten(std::move(quelle), dx, durchlaeufe);
        }
        return raster_ausgabe(ziel);
    });
    modul.def("wasser_flaeche", [](const py::array& x, const py::array& y,
                                 const py::array& z) {
        const auto xx = wasser_raster(x), yy = wasser_raster(y), zz = wasser_raster(z);
        std::pair<std::vector<sp::Vektor3>,
            std::vector<std::array<std::int64_t, 4>>> daten;
        {
            py::gil_scoped_release frei;
            daten = sp::wasser_flaeche(xx, yy, zz);
        }
        return py::make_tuple(mesh_array(daten.first), mesh_array(daten.second));
    });
    modul.def("wasser_kreis", [](std::size_t anzahl) {
        return mesh_array(sp::wasser_kreis(anzahl));
    });
    modul.def("wasser_quadrat", [] {
        return mesh_array(std::vector<std::array<double, 2>>{
            {-1., -1.}, {1., -1.}, {1., 1.}, {-1., 1.}, {-1., -1.}});
    });
    modul.def("wasser_spiegeln", [](const py::array& punkte, double lx,
                                   double ly, double tiefe, double cell, double kr) {
        const auto eingabe = array_zeilen<double, 3>(punkte, "Wasserpartikel");
        std::vector<sp::Vektor3> ergebnis;
        {
            py::gil_scoped_release frei;
            ergebnis = sp::wasser_spiegeln(eingabe, lx, ly, tiefe, cell, kr);
        }
        return mesh_array(ergebnis);
    });
    modul.def("wasser_splat", [](const py::array& punkte, const py::array& offsets,
                                std::size_t nx, std::size_t ny, std::size_t nz,
                                double lx, double ly, double tiefe,
                                double cell, double kr) {
        const auto p = array_zeilen<double, 3>(punkte, "Wasserpartikel");
        const auto off = array_zeilen<std::int64_t, 3>(offsets, "Wasseroffsets");
        std::vector<float> raster;
        {
            py::gil_scoped_release frei;
            raster = sp::wasser_splat(p, off, nx, ny, nz, lx, ly, tiefe, cell, kr);
        }
        py::array_t<float> ausgabe({
            static_cast<py::ssize_t>(nx), static_cast<py::ssize_t>(ny),
            static_cast<py::ssize_t>(nz)});
        std::copy(raster.begin(), raster.end(), ausgabe.mutable_data());
        return ausgabe;
    });
    modul.def("wasser_kalibrieren", [](const py::array& raster) -> py::object {
        if (!raster.dtype().equal(py::dtype::of<float>()) || raster.ndim() != 3) {
            throw py::type_error("Wasserdichteraster muss ein dreidimensionales float32-Array sein");
        }
        auto quelle = py::reinterpret_borrow<py::array_t<float>>(raster);
        const auto daten = quelle.unchecked<3>();
        std::vector<float> kopie(static_cast<std::size_t>(raster.size()));
        std::size_t position = 0;
        for (py::ssize_t i = 0; i < raster.shape(0); ++i) {
            for (py::ssize_t j = 0; j < raster.shape(1); ++j) {
                for (py::ssize_t k = 0; k < raster.shape(2); ++k) {
                    kopie[position++] = daten(i, j, k);
                }
            }
        }
        std::optional<double> kalibrierung;
        {
            py::gil_scoped_release frei;
            kalibrierung = sp::wasser_kalibrieren(
                kopie, static_cast<std::size_t>(raster.shape(0)),
                static_cast<std::size_t>(raster.shape(1)),
                static_cast<std::size_t>(raster.shape(2)));
        }
        return kalibrierung ? py::cast(*kalibrierung) : py::none();
    });
    py::class_<sp::VoxelKontext>(modul, "_VoxelKontext")
        .def(py::init([](const py::array& xs, const py::array& zs,
                         const py::array& offsets, const py::array& ys,
                         const py::array& praefix, double aufloesung) {
            return sp::VoxelKontext(
                array_werte<double>(xs, "Voxelspalten-x"),
                array_werte<double>(zs, "Voxelspalten-z"),
                array_werte<std::int64_t>(offsets, "Voxelspaltenoffsets"),
                array_werte<double>(ys, "Voxel-y"),
                array_werte<double>(praefix, "Voxel-y-Praefix"),
                aufloesung);
        }))
        .def("auswerten", [](const sp::VoxelKontext& kontext,
                             const py::array& rotation, const py::array& position) {
            std::pair<double, sp::Vektor3> ergebnis;
            const auto r = matrix(rotation);
            const auto p = vektor<3>(position, "Voxelposition");
            {
                py::gil_scoped_release frei;
                ergebnis = kontext.auswerten(r, p);
            }
            return py::make_tuple(ergebnis.first, ausgabe(ergebnis.second));
        });
    modul.def("voxel_paare_bereit", [](const std::vector<double>& schnitte) {
        std::vector<double> ergebnis;
        {
            py::gil_scoped_release frei;
            ergebnis = sp::voxel_paare_bereit(schnitte);
        }
        return ergebnis;
    });
    modul.def("voxel_intervalle", [](const py::array& punkte,
                                      const py::array& dreiecke,
                                      double x, double z) {
        const auto p = array_zeilen<double, 3>(punkte, "Voxelmeshpunkte");
        const auto f = array_zeilen<std::int64_t, 3>(dreiecke, "Voxelmeshdreiecke");
        std::vector<std::array<double, 2>> intervalle;
        {
            py::gil_scoped_release frei;
            intervalle = sp::voxel_intervalle(p, f, x, z);
        }
        py::list ausgabe;
        for (const auto& intervall : intervalle) {
            ausgabe.append(py::make_tuple(intervall[0], intervall[1]));
        }
        return ausgabe;
    });
    modul.def("pfeil_daten", [](const py::array& start, const py::array& kraft,
                              double kopfanteil, double radiusfaktor) {
        return pfeil_daten(sp::pfeil_geometrie(vektor<3>(start, "Pfeilstart"),
            vektor<3>(kraft, "Pfeilvektor"), kopfanteil, radiusfaktor));
    });
    modul.def("pfeil_fest", [](const py::array& start, const py::array& kraft,
            double durchmesser, double kopf_durchmesser, double kopf_laenge,
            double mindestlaenge) {
        return pfeil_daten(sp::pfeil_geometrie(vektor<3>(start, "Pfeilstart"),
            vektor<3>(kraft, "Pfeilvektor"), 0., 0., true, durchmesser,
            kopf_durchmesser, kopf_laenge, mindestlaenge), true);
    });
    modul.def("kraft_paarmoment", [](const py::array& angriff, const py::array& kraft,
                                    const py::array& schwerpunkt) {
        return ausgabe(sp::kraft_paarmoment(vektor<3>(angriff, "Kraftangriff"),
            vektor<3>(kraft, "Kraft"), vektor<3>(schwerpunkt, "Schwerpunkt")));
    });
    modul.def("kraft_skala", &sp::kraft_skala);
    modul.def("kraft_pfeile", [](const py::array& schwerpunkt, const py::array& angriff,
            double auftrieb, double masse, double g, double skala,
            double kopfanteil, double radiusfaktor) {
        const auto s = vektor<3>(schwerpunkt, "Schwerpunkt");
        const auto k = vektor<3>(angriff, "Auftriebszentrum");
        sp::endlich(std::array<double, 4>{auftrieb, masse, g, skala}, "Kraftpfeilwerte");
        const auto fg = sp::pfeil_geometrie(s, {0., 0., -masse * g * skala},
            kopfanteil, radiusfaktor);
        const auto fa = sp::pfeil_geometrie(k, {0., 0., auftrieb * skala},
            kopfanteil, radiusfaktor);
        return py::make_tuple(pfeil_daten(fg), pfeil_daten(fa));
    });
    modul.def("zusatz_pfeile", [](const py::array& schwerpunkt, const py::array& gesamt,
            const py::array& auftrieb, double masse, double g, double skala,
            double schwelle, double kopfanteil, double radiusfaktor) {
        const auto s = vektor<3>(schwerpunkt, "Schwerpunkt");
        const auto fg = vektor<3>(gesamt, "Gesamtkraft");
        const auto fa = vektor<3>(auftrieb, "Auftrieb");
        sp::endlich(std::array<double, 4>{masse, g, skala, schwelle}, "Zusatzpfeilwerte");
        const std::array<sp::Vektor3, 2> kraefte{{
            {fg[0], fg[1], fg[2] - masse * g},
            {fg[0] - fa[0], fg[1] - fa[1], fg[2] - fa[2]}}};
        py::tuple ausgaben(2);
        for (std::size_t i = 0; i < kraefte.size(); ++i) {
            sp::endlich(kraefte[i], "Zusatzpfeilkraft");
            if (std::sqrt(sp::skalarprodukt(kraefte[i], kraefte[i])) <= schwelle) {
                ausgaben[i] = py::none();
            } else {
                auto kraft = kraefte[i];
                for (double& wert : kraft) { wert *= skala; }
                ausgaben[i] = pfeil_daten(sp::pfeil_geometrie(s, kraft,
                    kopfanteil, radiusfaktor));
            }
        }
        return ausgaben;
    });
    modul.def("moment_bogen", [](double moment, const py::array& mitte,
            double radius, int achse, double schwelle, double start_grad,
            double winkel_grad, std::size_t anzahl) -> py::object {
        const auto zentrum = vektor<3>(mitte, "Bogenmittelpunkt");
        std::optional<sp::MomentBogen> bogen;
        {
            py::gil_scoped_release frei;
            bogen = sp::moment_bogen(moment, zentrum, radius, achse, schwelle,
                start_grad, winkel_grad, anzahl);
        }
        if (!bogen) { return py::none(); }
        py::dict daten;
        daten["punkte"] = mesh_array(bogen->punkte);
        daten["spitze"] = ausgabe(bogen->spitze);
        daten["richtung"] = ausgabe(bogen->richtung);
        daten["kopf_laenge"] = bogen->kopf_laenge;
        daten["kopf_radius"] = bogen->kopf_radius;
        daten["moment"] = moment;
        daten["achse"] = achse;
        return daten;
    });
    modul.def("strich_linien", [](const py::array& punkte, double strich,
                                  double luecke, double abstand) {
        const auto zeilen = array_zeilen<double, 3>(punkte, "Linienpunkte");
        sp::StrichLinien daten;
        {
            py::gil_scoped_release frei;
            daten = sp::strich_linien(zeilen, strich, luecke, abstand);
        }
        py::array_t<std::int64_t> zellen(daten.zellen.size());
        std::copy(daten.zellen.begin(), daten.zellen.end(), zellen.mutable_data());
        return py::make_tuple(mesh_array(daten.punkte), zellen);
    });
    modul.def("wirkungslinie", [](const py::array& kraft, const py::array& moment,
            const py::array& bezug, const sp::Mesh& mesh, const py::array& rotation,
            double toleranz) {
        const auto f = vektor<3>(kraft, "Wirkungslinienkraft");
        const auto m = vektor<3>(moment, "Wirkungslinienmoment");
        const auto r = vektor<3>(bezug, "Wirkungslinienbezugspunkt");
        const auto rot = matrix(rotation);
        sp::WirkungsLinie linie;
        {
            py::gil_scoped_release frei;
            linie = sp::wirkungslinie(f, m, r, mesh, rot, toleranz);
        }
        py::dict daten;
        daten["anker"] = ausgabe(linie.anker);
        daten["richtung"] = ausgabe(linie.richtung);
        daten["schnittpunkt"] = linie.schnittpunkt
            ? py::object(ausgabe(*linie.schnittpunkt)) : py::none();
        return daten;
    });
    modul.def("achse_kanonisieren", [](const py::array& achse) {
        return ausgabe(sp::achse_kanonisieren(vektor<3>(achse, "Hauptachse")));
    });
    modul.def("hauptachsen_aufbereiten", [](const py::array& werte,
                                          const py::array& vektoren) {
        const auto [w, v] = sp::hauptachsen_aufbereiten(
            vektor<3>(werte, "Haupttraegheiten"), matrix(vektoren));
        py::array_t<double> achsen({py::ssize_t(3), py::ssize_t(3)});
        std::copy(v.begin(), v.end(), achsen.mutable_data());
        return py::make_tuple(ausgabe(w), achsen);
    });
    modul.def("mesh_selbstschnitt", &sp::mesh_selbstschnitt,
        py::call_guard<py::gil_scoped_release>());
    modul.def("wasser_hash", [](const py::array& gitter) {
        const auto zeilen = array_zeilen<std::int64_t, 3>(gitter, "Wassergitter");
        py::array_t<double> array(zeilen.size());
        double* ziel = array.mutable_data();
        {
            py::gil_scoped_release frei;
            for (std::size_t i = 0; i < zeilen.size(); ++i) {
                ziel[i] = sp::wasser_hash(zeilen[i][0], zeilen[i][1], zeilen[i][2]);
            }
        }
        return array;
    });
    modul.def("punktlage", [](const py::array& gitter, double abstand) {
        const auto zeilen = array_zeilen<std::int64_t, 2>(gitter, "Wassergitter");
        sp::endlich(std::array<double, 1>{abstand}, "Wasserpunktabstand");
        std::vector<std::array<double, 2>> ergebnis(zeilen.size());
        {
            py::gil_scoped_release frei;
            for (std::size_t i = 0; i < zeilen.size(); ++i) {
                ergebnis[i] = sp::punktlage(zeilen[i][0], zeilen[i][1], abstand);
            }
        }
        return mesh_array(ergebnis);
    });
    modul.def("wasserpunkte", [](const py::array& zentrum, double radius, double abstand, double z0) {
        const auto c = vektor<2>(zentrum, "Wasserpunktzentrum");
        sp::WasserPunkte werte;
        {
            py::gil_scoped_release frei;
            werte = sp::wasserpunkte(c, radius, abstand, z0);
        }
        py::array_t<double> rand(werte.rand.size());
        std::copy(werte.rand.begin(), werte.rand.end(), rand.mutable_data());
        return py::make_tuple(mesh_array(werte.punkte), rand);
    });
    modul.def("wasserspuren", [](const py::array& punkte, const py::array& rand,
            const py::array& verlauf, std::size_t s) {
        const auto p = array_zeilen<double, 3>(punkte, "Wasserpunkte");
        const auto r = array_werte<double>(rand, "Wasserrand");
        const auto v = array_zeilen<double, 2>(verlauf, "Wasserspurverlauf");
        sp::WasserSpuren werte;
        {
            py::gil_scoped_release frei;
            werte = sp::wasserspuren(p, r, v, s);
        }
        py::array_t<double> spuren({static_cast<py::ssize_t>(p.size()),
            static_cast<py::ssize_t>(s), py::ssize_t(3)});
        py::array_t<double> alpha({static_cast<py::ssize_t>(p.size()), static_cast<py::ssize_t>(s)});
        std::copy(werte.spuren.begin(), werte.spuren.end(), spuren.mutable_data());
        std::copy(werte.alpha.begin(), werte.alpha.end(), alpha.mutable_data());
        return py::make_tuple(spuren, alpha);
    });
    modul.def("dunst_gitter", [](const py::array& zeilen, const py::array& winkel,
            const py::array& farbe) {
        const auto z = array_zeilen<double, 3>(zeilen, "Dunstzeilen");
        const auto w = array_werte<double>(winkel, "Dunstwinkel");
        const auto f = array_werte<std::uint8_t>(farbe, "Dunstfarbe");
        if (f.size() != 3) {
            throw py::value_error("Dunstfarbe muss drei Komponenten haben");
        }
        sp::DunstGitter werte;
        {
            py::gil_scoped_release frei;
            werte = sp::dunst_gitter(z, w, {f[0], f[1], f[2]});
        }
        return py::make_tuple(mesh_array(werte.punkte), mesh_array(werte.flaechen), mesh_array(werte.farben));
    });
    modul.def("winkel_360", &sp::winkel_360);
    modul.def("wrap_180", &sp::wrap_180);
    modul.def("richtungssektor", &sp::richtungssektor);
    modul.def("navigationswerte", [](const std::optional<py::array>& rotation,
            std::optional<double> offset, std::optional<double> elevation,
            std::optional<double> segelwinkel) {
        std::optional<sp::Matrix3> r;
        if (rotation) {
            r = matrix(*rotation);
        }
        std::array<std::optional<double>, 7> werte;
        {
            py::gil_scoped_release frei;
            werte = sp::navigationswerte(r, offset, elevation, segelwinkel);
        }
        return werte;
    });
    modul.def("dynamik2d", [](const py::array& zustand, const py::array& parameter,
            const py::array& kraft, const py::array& added) {
        const auto z = vektor<4>(zustand, "Bewegungszustand");
        const auto p = vektor<6>(parameter, "Dynamikparameter");
        const auto f = vektor<2>(kraft, "Kraft/Moment");
        const auto a = vektor<6>(added, "Added Mass");
        std::pair<sp::Vektor4, sp::Vektor6> werte;
        {
            py::gil_scoped_release frei;
            werte = sp::dynamik2d(z, p, f, a);
        }
        return py::make_tuple(ausgabe(werte.first), ausgabe(werte.second));
    });
    modul.def("beste_loesung", &sp::beste_loesung, py::call_guard<py::gil_scoped_release>());
    modul.def("projektion", [](const py::array& position, const py::array& winkel) {
        const auto p = vektor<3>(position, "Position"), w = vektor<3>(winkel, "Winkel");
        sp::endlich(p, "Position"); sp::endlich(w, "Winkel");
        return py::make_tuple(p[2], w[0]);
    });
    modul.def("stoss_pose", [](const py::array& basis, const py::array& versatz,
            const py::array& winkel) {
        auto position = vektor<3>(basis, "Basisposition");
        const auto translation = vektor<3>(versatz, "Versatz"), w = vektor<3>(winkel, "Winkel");
        sp::endlich(position, "Basisposition"); sp::endlich(translation, "Versatz");
        sp::Matrix3 rotation;
        {
            py::gil_scoped_release frei;
            rotation = sp::euler_rotation(w[0], w[1], w[2]);
            for (std::size_t i = 0; i < 3; ++i) {
                position[i] += translation[i];
            }
            sp::endlich(position, "Stoerposition");
        }
        auto array = ausgabe(rotation);
        array.resize({3, 3});
        return py::make_tuple(array, ausgabe(position));
    });
    modul.def("mesh_flaeche", &sp::mesh_flaeche, py::call_guard<py::gil_scoped_release>());
    modul.def("massenschwerpunkt", [](const sp::Mesh& mesh, bool schale) {
        std::pair<sp::Vektor3, double> werte;
        {
            py::gil_scoped_release frei;
            werte = sp::massenschwerpunkt(mesh, schale);
        }
        return py::make_tuple(ausgabe(werte.first), werte.second);
    });
    modul.def("massentraegheit", [](const sp::Mesh& mesh, double dichte, bool schale) {
        sp::Matrix3 werte;
        {
            py::gil_scoped_release frei;
            werte = sp::massentraegheit(mesh, dichte, schale);
        }
        auto array = ausgabe(werte);
        array.resize({3, 3});
        return array;
    });
    py::class_<sp::StatikKontext>(modul, "StatikKontext")
        .def(py::init([](
                const sp::HydrostatikKontext& hydro, const sp::HydroKontext& rollen,
                const py::array& linear, const py::array& quadratisch,
                const py::array& fluid, const py::array& fluidrotation,
                const py::array& hp, std::optional<double> cd,
                std::optional<double> gewicht,
                const std::optional<std::pair<sp::Vektor3, sp::Vektor3>>& fremd,
                bool kraftmodell) {
            const auto l = vektor<6>(linear, "Linearer Widerstand");
            const auto q = vektor<6>(quadratisch, "Quadratischer Widerstand");
            sp::nichtnegativ(l, "Linearer Widerstand");
            sp::nichtnegativ(q, "Quadratischer Widerstand");
            if (gewicht) {
                sp::positiv(*gewicht, "Gewicht");
            }
            if (fremd) {
                sp::endlich(fremd->first, "Fremdkraft");
                sp::endlich(fremd->second, "Fremdkraftpunkt");
            }
            return sp::StatikKontext{
                hydro, rollen, l, q, vektor<3>(fluid, "Fluid"),
                vektor<3>(fluidrotation, "Fluidrotation"),
                vektor<7>(hp, "Hydrodynamikparameter"), cd, gewicht, fremd, kraftmodell};
        }))
        .def("residuum", [](const sp::StatikKontext& kontext, double z, double phi,
                            double m, double g, const sp::Abbruch& abbruch) {
            return ausgabe(kontext.auswerten(z, phi, m, g, abbruch));
        })
        .def("kontakt_start", &sp::StatikKontext::kontakt_start,
             py::call_guard<py::gil_scoped_release>())
        .def("stationaere_dynamik", [](const sp::StatikKontext& kontext,
                const sp::Zustand& zustand, double masse, const py::array& inertia,
                const py::array& added, double dt, double g, double dauer,
                const sp::Abbruch& abbruch) {
            const auto tensor = matrix(inertia);
            const sp::Parameter parameter{
                kontext.hydro.rho, g, dt, kontext.linear, kontext.quadratisch,
                vektor<6>(added, "Added Mass"), kontext.fluid, kontext.fluidrotation};
            sp::StationaererNachlauf ergebnis{zustand, 0., {}, {}};
            {
                py::gil_scoped_release frei;
                ergebnis = sp::stationaerer_nachlauf(
                    kontext, zustand, masse, tensor, parameter, dauer, abbruch);
            }
            return py::make_tuple(
                ergebnis.zustand, ergebnis.vergangen, ergebnis.mitte, ergebnis.fehler);
        })
        .def("stationaere_kraft", [](const sp::StatikKontext& kontext,
                const py::array& werte, const sp::Abbruch& abbruch) {
            const auto wrench = kontext.stationaere_kraft(
                vektor<6>(werte, "Stationaerer Zustand"), abbruch);
            return py::make_tuple(ausgabe(wrench.kraft), ausgabe(wrench.moment));
        })
        .def("stationaere_stufe", [](const sp::StatikKontext& kontext,
                const py::array& werte, int stufe, double kraft, double laenge,
                double geschwindigkeit, double toleranz, int max_iter,
                const sp::Abbruch& abbruch) {
            const auto start = vektor<6>(werte, "Stationaerer Startwert");
            sp::StationaereWerte ergebnis;
            {
                py::gil_scoped_release frei;
                ergebnis = sp::stationaere_stufe(
                    kontext, start, stufe, kraft, laenge, geschwindigkeit,
                    toleranz, max_iter, abbruch);
            }
            return py::make_tuple(
                ausgabe(ergebnis.werte), ausgabe(ergebnis.kraft), ausgabe(ergebnis.moment),
                ergebnis.iterationen, ergebnis.konvergiert, ergebnis.fehler);
        })
        .def("loesen", [](const sp::StatikKontext& kontext, double m, double g,
                const py::array& start, double tol, int max_iter,
                const std::vector<double>& leiter, bool robust,
                double stagnation, double neutral, const sp::Abbruch& abbruch) {
            const auto lage = vektor<2>(start, "Solverstart");
            sp::StatikErgebnis ergebnis;
            {
                py::gil_scoped_release frei;
                sp::StatikSolver solver(kontext, m, g, tol, robust, abbruch);
                ergebnis = solver.loesen(lage, max_iter, leiter, stagnation, neutral);
            }
            py::dict daten;
            daten["z"] = ergebnis.lage[0]; daten["phi"] = ergebnis.lage[1];
            daten["restkraft"] = std::abs(ergebnis.residuum[0]);
            daten["restmoment"] = std::abs(ergebnis.residuum[1]);
            daten["iterationen"] = ergebnis.iterationen;
            daten["restarts"] = ergebnis.restarts;
            if (robust) {
                daten["stagnation"] = ergebnis.stagnation;
                daten["kraftauswertungen"] = ergebnis.misses;
                daten["wiederverwendete_kraftwerte"] = ergebnis.hits;
                if (ergebnis.erfolgreich || ergebnis.status == "instabile_lage") {
                    daten["neutral"] = ergebnis.neutral;
                    daten["stabil"] = ergebnis.stabil;
                }
            }
            if (ergebnis.erfolgreich) {
                daten["gm"] = ergebnis.gm ? py::cast(*ergebnis.gm) : py::none();
            }
            return py::make_tuple(
                ergebnis.erfolgreich, daten, ergebnis.status, ergebnis.meldung);
        });

    modul.def("euler_rotation", [](double phi, double theta, double psi) {
        auto array = ausgabe(sp::euler_rotation(phi, theta, psi));
        array.resize({3, 3});
        return array;
    }, py::arg("phi"), py::arg("theta"), py::arg("psi"));
    modul.def("rotation_matrix", [](double phi, const py::array& axis) {
        auto array = ausgabe(sp::rotationsmatrix_achsenwinkel(
            vektor<3>(axis, "Rotationsachse"), phi));
        array.resize({3, 3});
        return array;
    }, py::arg("phi"), py::arg("axis").noconvert());

    modul.def("quaternion_slerp", [](const py::array& a, const py::array& b, double anteil) {
        return ausgabe(sp::quaternion_slerp(
            vektor<4>(a, "Anfang"), vektor<4>(b, "Ende"), anteil));
    }, py::arg("anfang").noconvert(), py::arg("ende").noconvert(), py::arg("anteil"));
    modul.def("anzeige_interpolieren", &sp::anzeige_interpolieren,
              py::arg("zeiten"), py::arg("verlauf"), py::arg("anzeigezeit"),
              py::arg("vergangen"), py::arg("verzoegerung"),
              py::call_guard<py::gil_scoped_release>());

    modul.def("linear_loesen", [](const py::array& a, const py::array& b) {
        return ausgabe(sp::linear_loesen(matrix(a), vektor<3>(b, "Rechte Seite")));
    }, py::arg("matrix").noconvert(), py::arg("rechte_seite").noconvert());

    py::class_<sp::PhysikKontext>(modul, "PhysikKontext")
        .def(py::init([](
                const sp::HydrostatikKontext& hydro, const sp::HydroKontext& rollen,
                const py::array& hydroparameter, std::optional<double> cd,
                double masse, const py::array& inertia, const sp::Parameter& parameter) {
            sp::positiv(masse, "Masse");
            parameter.pruefen();
            const auto tensor = matrix(inertia);
            sp::dynamik_traegheit_pruefen(masse, tensor);
            return sp::PhysikKontext{
                hydro, rollen, vektor<7>(hydroparameter, "Hydrodynamikparameter"),
                cd, masse, tensor, parameter};
        }))
        .def("batch", [](
                const sp::PhysikKontext& kontext, const sp::Zustand& zustand,
                const py::object& schrittzahl,
                const std::optional<std::pair<sp::Vektor3, sp::Vektor3>>& fremd,
                double ruder, const sp::Abbruch& abbruch) {
            if (PyBool_Check(schrittzahl.ptr())) {
                throw py::type_error("Batchanzahl darf kein Wahrheitswert sein");
            }
            auto index = py::reinterpret_steal<py::object>(
                PyNumber_Index(schrittzahl.ptr()));
            if (!index) {
                throw py::error_already_set();
            }
            const std::int64_t anzahl = PyLong_AsLongLong(index.ptr());
            if (PyErr_Occurred()) {
                throw py::error_already_set();
            }
            if (anzahl < 1) {
                throw py::value_error("Batch braucht mindestens einen Schritt");
            }
            if (!std::isfinite(ruder) || std::abs(ruder) > 3.14159265358979323846 / 2.) {
                throw py::value_error("Ruderwinkel muss zwischen -90 und +90 Grad liegen");
            }
            if (fremd) {
                sp::endlich(fremd->first, "Fremdkraft");
                sp::endlich(fremd->second, "Fremdkraft-Angriffspunkt");
            }
            py::gil_scoped_release frei;
            auto ergebnis = kontext.schritt(zustand, fremd, ruder, abbruch);
            for (std::int64_t i = 1; i < anzahl; ++i) {
                abbruch.pruefen();
                ergebnis = kontext.schritt(ergebnis.zustand, fremd, ruder, abbruch);
            }
            return ergebnis;
        }, py::arg("zustand"), py::arg("anzahl"), py::arg("fremdkraft"),
           py::arg("ruderwinkel"), py::arg("abbruch"));

    py::class_<sp::HydrostatikWerte>(modul, "HydrostatikWerte")
        .def_readonly("volumen", &sp::HydrostatikWerte::volumen)
        .def_property_readonly("schwerpunkt", [](const sp::HydrostatikWerte& w) {
            return ausgabe(w.schwerpunkt);
        })
        .def_property_readonly("kraft", [](const sp::HydrostatikWerte& w) {
            return ausgabe(w.kraft);
        })
        .def_property_readonly("moment", [](const sp::HydrostatikWerte& w) {
            return ausgabe(w.moment);
        });
    py::class_<sp::HydrostatikKontext>(modul, "HydrostatikKontext")
        .def(py::init([](
                const sp::Mesh& mesh, const py::array& minimum, const py::array& maximum,
                double volumen, const py::array& schwerpunkt, const py::array& r_s,
                double rho, double g) {
            sp::positiv(rho, "Wasserdichte"); sp::positiv(g, "Schwerebeschleunigung");
            if (!std::isfinite(volumen) || volumen < 0.) {
                throw py::value_error("Gesamtvolumen muss endlich und nicht-negativ sein");
            }
            return sp::HydrostatikKontext{
                sp::EbenenSchnitt{mesh}, vektor<3>(minimum, "Minimum"),
                vektor<3>(maximum, "Maximum"), volumen,
                vektor<3>(schwerpunkt, "Gesamtschwerpunkt"),
                vektor<3>(r_s, "Koerperschwerpunkt"), rho, g};
        }))
        .def("auswerten", [](const sp::HydrostatikKontext& kontext,
                            const py::array& rotation, const py::array& position,
                            const sp::Abbruch& abbruch) {
            const auto r = matrix(rotation);
            const auto p = vektor<3>(position, "Position");
            py::gil_scoped_release frei;
            return kontext.auswerten(r, p, abbruch);
        });

    modul.def("wrench_verschieben", [](const sp::Wrench& w, const py::array& ziel) {
        return sp::wrench_verschieben(w, vektor<3>(ziel, "Wrench-Bezugspunkt"));
    });
    modul.def("aggregiere_kraftbeitraege", [](
            const std::vector<sp::Beitrag>& beitraege, const py::array& ziel,
            const std::string& frame) {
        return sp::aggregiere_kraftbeitraege(
            beitraege, vektor<3>(ziel, "Gesamt-Wrench-Bezugspunkt"), frame);
    });
    modul.def("widerstand", [](const py::array& linear, const py::array& quadratisch,
                              const py::array& relativ) {
        return ausgabe(sp::widerstand(
            vektor<6>(linear, "Linearer Widerstand"),
            vektor<6>(quadratisch, "Quadratischer Widerstand"),
            vektor<6>(relativ, "Relativgeschwindigkeit")));
    });
    modul.def("added_mass_kraft", [](const py::array& rotation, const py::array& added,
                                    const py::array& beschleunigung) {
        return ausgabe(sp::added_mass_kraft(
            matrix(rotation), vektor<6>(added, "Added Mass"),
            vektor<6>(beschleunigung, "Beschleunigung")));
    });

    py::class_<sp::HydroTeil>(modul, "HydroTeil")
        .def(py::init<sp::Mesh>(), py::arg("mesh"));
    modul.def("ittc_reibungsbeiwert", &sp::ittc_reibungsbeiwert);
    py::class_<sp::HydroKontext>(modul, "HydroKontext")
        .def(py::init<std::vector<sp::HydroTeil>>(), py::arg("teile"))
        .def("beitraege", [](
            const sp::HydroKontext& kontext, const py::array& rotation,
            const py::array& position, const py::array& v, const py::array& omega,
            const py::array& parameter, std::optional<double> cd_volumen,
            const sp::Abbruch& abbruch) {
        const auto r = matrix(rotation);
        const auto p = vektor<3>(position, "Position");
        const auto geschwindigkeit = vektor<3>(v, "Geschwindigkeit");
        const auto winkel = vektor<3>(omega, "Winkelgeschwindigkeit");
        const auto werte = vektor<7>(parameter, "Hydrodynamikparameter");
        py::gil_scoped_release frei;
        return sp::hydrodynamik_beitraege(
            kontext.teile, r, p, geschwindigkeit, winkel, werte, cd_volumen, abbruch);
    });

    modul.def("wasserschnitt", [](const sp::Mesh& mesh, double ebene,
                                  bool mit_deckel, const sp::Abbruch& abbruch) {
        sp::WasserSchnitt ergebnis;
        {
            py::gil_scoped_release frei;
            ergebnis = sp::wasserschnitt(mesh, ebene, mit_deckel, abbruch);
        }
        return py::make_tuple(
            mesh_array(ergebnis.unten.punkte), mesh_array(ergebnis.unten.dreiecke),
            mesh_array(ergebnis.oben.punkte), mesh_array(ergebnis.oben.dreiecke),
            mesh_array(ergebnis.kontur));
    }, py::arg("mesh"), py::arg("ebene"), py::arg("mit_deckel"), py::arg("abbruch"));
    modul.def("wasserlinie", [](const sp::Mesh& mesh, double ebene, double toleranz) {
        return mesh_array(sp::wasserlinie(mesh, ebene, toleranz));
    });
    modul.def("clip_polygon", [](const sp::Mesh& mesh, double ebene, bool oben) {
        return mesh_array(sp::clip_polygon(mesh.punkte, ebene, oben));
    });
    modul.def("konturketten", [](const sp::Mesh& mesh, double toleranz) {
        py::list ausgabe;
        for (const auto& ring : sp::ketten(mesh.punkte, toleranz)) {
            ausgabe.append(mesh_array(ring));
        }
        return ausgabe;
    });
    modul.def("ringflaeche", [](const sp::Mesh& mesh) {
        return sp::ringflaeche(mesh.punkte);
    });
    modul.def("ringmomente", [](const sp::Mesh& mesh) -> py::object {
        const auto ergebnis = sp::ringmomente(mesh.punkte);
        if (!ergebnis) {
            return py::none();
        }
        return py::cast(*ergebnis);
    });
    modul.def("wasserlinien_ringe", [](const sp::Mesh& mesh, double ebene, double toleranz) {
        std::vector<sp::Ring> ringe;
        {
            py::gil_scoped_release frei;
            ringe = sp::wasserlinien_ringe(mesh, ebene, toleranz);
        }
        py::list ausgabe;
        for (const auto& ring : ringe) {
            ausgabe.append(mesh_array(ring));
        }
        return ausgabe;
    });
    modul.def("punkt_in_ring", [](const py::array& punkt, const sp::Mesh& mesh) {
        return sp::punkt_in_ring(vektor<3>(punkt, "Ringpunkt"), mesh.punkte);
    });
    modul.def("einzigartige_konturpunkte", [](const sp::Mesh& mesh, double toleranz) {
        return mesh_array(sp::einzigartige_konturpunkte(mesh.punkte, toleranz));
    });
    modul.def("polygonzug", [](const sp::Mesh& mesh, double toleranz) {
        return mesh_array(sp::polygonzug(mesh.punkte, toleranz));
    });
    modul.def("deckel_setzen", [](sp::Mesh mesh, double ebene, bool oben,
                                 const std::optional<sp::Mesh>& rand) {
        {
            py::gil_scoped_release frei;
            sp::deckel_setzen(mesh, ebene, oben, rand ? &rand->punkte : nullptr);
        }
        return py::make_tuple(mesh_array(mesh.punkte), mesh_array(mesh.dreiecke));
    });
    modul.def("mesh_volumen", [](const sp::Mesh& mesh) {
        sp::VolumenMoment summe;
        for (const auto& tri : mesh.dreiecke) {
            summe.dreieck(mesh.punkte[tri[0]], mesh.punkte[tri[1]], mesh.punkte[tri[2]]);
        }
        return summe.det6() / 6.;
    });

    py::class_<sp::EbenenSchnitt>(modul, "EbenenSchnitt")
        .def(py::init([](const sp::Mesh& mesh) {
            mesh.pruefen();
            return sp::EbenenSchnitt{mesh};
        }), py::arg("mesh"))
        .def("auswerten", [](const sp::EbenenSchnitt& schnitt,
                            const py::array& normale, double offset,
                            const sp::Abbruch& abbruch) {
            const auto n = vektor<3>(normale, "Ebenennormale");
            std::pair<double, sp::Vektor3> ergebnis;
            {
                py::gil_scoped_release frei;
                ergebnis = schnitt.auswerten(n, offset, abbruch);
            }
            return py::make_tuple(ergebnis.first, ausgabe(ergebnis.second));
        }, py::arg("normale").noconvert(), py::arg("offset"), py::arg("abbruch"));

    py::class_<sp::Zustand>(modul, "Zustand")
        .def(py::init([](const py::array& werte) {
            return sp::Zustand(vektor<13>(werte, "Zustand"));
        }), py::arg("werte").noconvert())
        .def_property_readonly("werte", [](const sp::Zustand& z) { return ausgabe(z.werte); });

    py::class_<sp::Mesh>(modul, "Mesh")
        .def(py::init([](const py::array& punkte, const py::array& dreiecke,
                         std::string name, std::string rolle, bool verdraengend) {
            const auto p = array_pruefen<double>(punkte, 2, 3, "Punkte").unchecked<2>();
            const auto f = array_pruefen<std::int64_t>(
                dreiecke, 2, 3, "Dreiecke").unchecked<2>();
            sp::Mesh mesh{{}, {}, std::move(name), std::move(rolle), verdraengend};
            mesh.punkte.reserve(p.shape(0));
            mesh.dreiecke.reserve(f.shape(0));
            for (py::ssize_t i = 0; i < p.shape(0); ++i) {
                mesh.punkte.push_back({p(i, 0), p(i, 1), p(i, 2)});
            }
            for (py::ssize_t i = 0; i < f.shape(0); ++i) {
                mesh.dreiecke.push_back({f(i, 0), f(i, 1), f(i, 2)});
            }
            mesh.pruefen();
            return mesh;
        }), py::arg("punkte").noconvert(), py::arg("dreiecke").noconvert(),
            py::arg("name") = "", py::arg("rolle") = "", py::arg("verdraengend") = true)
        .def_property_readonly("punkte", [](const sp::Mesh& m) { return mesh_array(m.punkte); })
        .def_property_readonly("dreiecke", [](const sp::Mesh& m) { return mesh_array(m.dreiecke); })
        .def("eingabe_identisch", [](const sp::Mesh& m, const py::array& punkte,
                                     const py::array& dreiecke) {
            const auto p = array_pruefen<double>(punkte, 2, 3, "Punkte").unchecked<2>();
            const auto f = array_pruefen<std::int64_t>(
                dreiecke, 2, 3, "Dreiecke").unchecked<2>();
            if (static_cast<std::size_t>(p.shape(0)) != m.punkte.size()
                    || static_cast<std::size_t>(f.shape(0)) != m.dreiecke.size()) {
                return false;
            }
            for (py::ssize_t i = 0; i < p.shape(0); ++i) {
                for (py::ssize_t j = 0; j < 3; ++j) {
                    if (p(i, j) != m.punkte[i][j]) {
                        return false;
                    }
                }
            }
            for (py::ssize_t i = 0; i < f.shape(0); ++i) {
                for (py::ssize_t j = 0; j < 3; ++j) {
                    if (f(i, j) != m.dreiecke[i][j]) {
                        return false;
                    }
                }
            }
            return true;
        }, py::arg("punkte").noconvert(), py::arg("dreiecke").noconvert())
        .def_readonly("name", &sp::Mesh::name)
        .def_readonly("rolle", &sp::Mesh::rolle)
        .def_readonly("verdraengend", &sp::Mesh::verdraengend);

    py::class_<sp::Modell>(modul, "Modell")
        .def(py::init([](double masse, const py::array& inertia,
                         std::vector<sp::Mesh> meshes, std::uint64_t version,
                         const py::array& r_S) {
            sp::Modell modell{masse, matrix(inertia), std::move(meshes), version,
                              vektor<3>(r_S, "Modellschwerpunkt")};
            {
                py::gil_scoped_release frei;
                modell.pruefen();
            }
            return modell;
        }), py::arg("masse"), py::arg("traegheit").noconvert(), py::arg("meshes"),
            py::arg("version"), py::arg("r_S").noconvert())
        .def_readonly("masse", &sp::Modell::masse)
        .def_readonly("version", &sp::Modell::version)
        .def_property_readonly("meshes", [](const sp::Modell& m) { return m.meshes; })
        .def_property_readonly("r_S", [](const sp::Modell& m) { return ausgabe(m.r_S); })
        .def_property_readonly("traegheit", [](const sp::Modell& m) {
            auto array = ausgabe(m.traegheit);
            array.resize({3, 3});
            return array;
        });

    py::class_<sp::Parameter>(modul, "Parameter")
        .def(py::init([](double rho, double g, double dt,
                         const py::array& linear, const py::array& quadratisch,
                         const py::array& added_mass, const py::array& fluid,
                         const py::array& fluidrotation) {
            sp::Parameter p{rho, g, dt, vektor<6>(linear, "Linearer Widerstand"),
                vektor<6>(quadratisch, "Quadratischer Widerstand"),
                vektor<6>(added_mass, "Added Mass"), vektor<3>(fluid, "Fluidgeschwindigkeit"),
                vektor<3>(fluidrotation, "Fluidwinkelgeschwindigkeit")};
            p.pruefen();
            return p;
        }), py::arg("rho"), py::arg("g"), py::arg("dt"),
            py::arg("linear").noconvert(), py::arg("quadratisch").noconvert(),
            py::arg("added_mass").noconvert(), py::arg("fluid").noconvert(),
            py::arg("fluidrotation").noconvert())
        .def_readonly("rho", &sp::Parameter::rho)
        .def_readonly("g", &sp::Parameter::g)
        .def_readonly("dt", &sp::Parameter::dt)
        .def_property_readonly("linear", [](const sp::Parameter& p) { return ausgabe(p.linear); })
        .def_property_readonly("quadratisch", [](const sp::Parameter& p) { return ausgabe(p.quadratisch); })
        .def_property_readonly("added_mass", [](const sp::Parameter& p) { return ausgabe(p.added_mass); })
        .def_property_readonly("fluid", [](const sp::Parameter& p) { return ausgabe(p.fluid); })
        .def_property_readonly("fluidrotation", [](const sp::Parameter& p) { return ausgabe(p.fluidrotation); });

    py::class_<sp::Wrench>(modul, "Wrench")
        .def(py::init([](std::string frame, const py::array& bezugspunkt,
                         const py::array& kraft, const py::array& moment) {
            sp::Wrench w{std::move(frame), vektor<3>(bezugspunkt, "Bezugspunkt"),
                        vektor<3>(kraft, "Kraft"), vektor<3>(moment, "Moment")};
            w.pruefen();
            return w;
        }), py::arg("frame"), py::arg("bezugspunkt").noconvert(),
            py::arg("kraft").noconvert(), py::arg("moment").noconvert())
        .def_readonly("frame", &sp::Wrench::frame)
        .def_property_readonly("bezugspunkt", [](const sp::Wrench& w) { return ausgabe(w.bezugspunkt); })
        .def_property_readonly("kraft", [](const sp::Wrench& w) { return ausgabe(w.kraft); })
        .def_property_readonly("moment", [](const sp::Wrench& w) { return ausgabe(w.moment); });

    py::class_<sp::Beitrag>(modul, "Beitrag")
        .def(py::init([](std::string name, const sp::Wrench& wrench) {
            sp::Beitrag b{std::move(name), wrench};
            b.pruefen();
            return b;
        }), py::arg("name"), py::arg("wrench"))
        .def_readonly("name", &sp::Beitrag::name)
        .def_property_readonly("wrench", [](const sp::Beitrag& b) { return b.wrench; });

    py::class_<sp::Ergebnis>(modul, "Ergebnis")
        .def(py::init([](const sp::Zustand& zustand, double volumen,
                         const py::array& auftriebsschwerpunkt, const sp::Wrench& gesamt,
                         std::vector<sp::Beitrag> beitraege, const sp::Wrench& auftrieb,
                         const py::array& added_mass, const py::array& linear,
                         const py::array& quadratisch, const py::array& fluid,
                         const py::array& fluidrotation, bool schwerkraft_beruecksichtigt) {
            sp::Ergebnis e{zustand, volumen, vektor<3>(
                auftriebsschwerpunkt, "Auftriebsschwerpunkt"), gesamt, std::move(beitraege),
                auftrieb, vektor<6>(added_mass, "Added Mass"), vektor<6>(linear, "Linearer Widerstand"),
                vektor<6>(quadratisch, "Quadratischer Widerstand"),
                vektor<3>(fluid, "Fluidgeschwindigkeit"),
                vektor<3>(fluidrotation, "Fluidwinkelgeschwindigkeit"), schwerkraft_beruecksichtigt};
            e.pruefen();
            return e;
        }), py::arg("zustand"), py::arg("volumen"), py::arg("auftriebsschwerpunkt").noconvert(),
            py::arg("gesamt"), py::arg("beitraege"), py::arg("auftrieb"),
            py::arg("added_mass").noconvert(), py::arg("linear").noconvert(),
            py::arg("quadratisch").noconvert(), py::arg("fluid").noconvert(),
            py::arg("fluidrotation").noconvert(), py::arg("schwerkraft_beruecksichtigt"))
        .def_property_readonly("zustand", [](const sp::Ergebnis& e) { return e.zustand; })
        .def_readonly("volumen", &sp::Ergebnis::volumen)
        .def_property_readonly("auftriebsschwerpunkt", [](const sp::Ergebnis& e) {
            return ausgabe(e.auftriebsschwerpunkt);
        })
        .def_property_readonly("gesamt", [](const sp::Ergebnis& e) { return e.gesamt; })
        .def_property_readonly("beitraege", [](const sp::Ergebnis& e) { return e.beitraege; })
        .def_property_readonly("auftrieb", [](const sp::Ergebnis& e) { return e.auftrieb; })
        .def_property_readonly("added_mass", [](const sp::Ergebnis& e) { return ausgabe(e.added_mass); })
        .def_property_readonly("linear", [](const sp::Ergebnis& e) { return ausgabe(e.linear); })
        .def_property_readonly("quadratisch", [](const sp::Ergebnis& e) { return ausgabe(e.quadratisch); })
        .def_property_readonly("fluid", [](const sp::Ergebnis& e) { return ausgabe(e.fluid); })
        .def_property_readonly("fluidrotation", [](const sp::Ergebnis& e) { return ausgabe(e.fluidrotation); })
        .def_readonly("schwerkraft_beruecksichtigt", &sp::Ergebnis::schwerkraft_beruecksichtigt);

    py::class_<sp::Abbruch>(modul, "Abbruch")
        .def(py::init<>())
        .def("abbrechen", &sp::Abbruch::abbrechen)
        .def_property_readonly("abgebrochen", &sp::Abbruch::abgebrochen)
        .def("pruefen", &sp::Abbruch::pruefen, py::call_guard<py::gil_scoped_release>());

    modul.def("quaternion_normalisieren", [](const py::array& q) {
        return ausgabe(sp::quaternion_normalisieren(vektor<4>(q, "Quaternion")));
    }, py::arg("quaternion").noconvert());
    modul.def("quaternion_matrix", [](const py::array& q) {
        auto array = ausgabe(sp::quaternion_matrix(vektor<4>(q, "Quaternion")));
        array.resize({3, 3});
        return array;
    }, py::arg("quaternion").noconvert());
    modul.def("quaternion_aus_matrix", [](const py::array& rotation) {
        return ausgabe(sp::quaternion_aus_matrix(matrix(rotation)));
    }, py::arg("rotation").noconvert());
    modul.def("quaternion_multiplizieren", [](const py::array& q, const py::array& p) {
        return ausgabe(sp::quaternion_multiplizieren(
            vektor<4>(q, "Quaternion"), vektor<4>(p, "Quaternion")));
    }, py::arg("q").noconvert(), py::arg("p").noconvert());
    modul.def("orientierung_schritt", [](const py::array& q, const py::array& omega, double dt) {
        return ausgabe(sp::orientierung_schritt(
            vektor<4>(q, "Quaternion"), vektor<3>(omega, "Winkelgeschwindigkeit"), dt));
    }, py::arg("q").noconvert(), py::arg("omega").noconvert(), py::arg("dt"));
    modul.def("rotationsmatrix_achsenwinkel", [](const py::array& achse, double winkel) {
        auto array = ausgabe(sp::rotationsmatrix_achsenwinkel(
            vektor<3>(achse, "Gelenkachse"), winkel));
        array.resize({3, 3});
        return array;
    }, py::arg("achse").noconvert(), py::arg("winkel"));

    py::class_<sp::Pose>(modul, "Pose")
        .def(py::init([](std::string ziel, std::string quelle, const py::array& t,
                         const py::array& q) {
            return sp::Pose(std::move(ziel), std::move(quelle),
                vektor<3>(t, "Pose-Translation"), vektor<4>(q, "Pose-Quaternion"));
        }), py::arg("ziel_frame"), py::arg("quell_frame"),
            py::arg("translation_m").noconvert(), py::arg("rotation_quaternion_wxyz").noconvert())
        .def_readonly("ziel_frame", &sp::Pose::ziel)
        .def_readonly("quell_frame", &sp::Pose::quelle)
        .def_property_readonly("translation_m", [](const sp::Pose& p) { return ausgabe(p.translation); })
        .def_property_readonly("rotation_quaternion_wxyz", [](const sp::Pose& p) { return ausgabe(p.quaternion); })
        .def_property_readonly("rotationsmatrix", [](const sp::Pose& p) {
            auto array = ausgabe(sp::quaternion_matrix(p.quaternion));
            array.resize({3, 3});
            return array;
        })
        .def("punkt_transformieren", [](const sp::Pose& p, const py::array& v) {
            return ausgabe(p.punkt_transformieren(vektor<3>(v, "Punkt")));
        }, py::arg("punkt").noconvert())
        .def("vektor_transformieren", [](const sp::Pose& p, const py::array& v) {
            return ausgabe(p.vektor_transformieren(vektor<3>(v, "Vektor")));
        }, py::arg("vektor").noconvert())
        .def("punkte_transformieren", [](const sp::Pose& p, const py::array& punkte) {
            const auto daten = array_pruefen<double>(punkte, 2, 3, "Punkte").unchecked<2>();
            std::vector<sp::Vektor3> werte;
            werte.reserve(daten.shape(0));
            for (py::ssize_t i = 0; i < daten.shape(0); ++i) {
                werte.push_back({daten(i, 0), daten(i, 1), daten(i, 2)});
                sp::endlich(werte.back(), "Punkt");
            }
            return punkte_transformieren(p, werte);
        }, py::arg("punkte").noconvert())
        .def("vorbereitete_punkte_transformieren", [](const sp::Pose& p, const sp::Mesh& m) {
            return punkte_transformieren(p, m.punkte);
        }, py::arg("mesh"))
        .def("invers", &sp::Pose::invers)
        .def("komponieren", &sp::Pose::komponieren, py::arg("innen"));
    modul.def("pose_mit_gelenkwinkel", [](const sp::Pose& basis,
                                         const py::array& achse, double winkel) {
        return sp::pose_mit_gelenkwinkel(basis, vektor<3>(achse, "Gelenkachse"), winkel);
    }, py::arg("basis"), py::arg("achse").noconvert(), py::arg("winkel"));

    py::class_<sp::Koerperteil>(modul, "Koerperteil")
        .def(py::init([](double masse, const py::array& inertia,
                         const sp::Mesh& mesh, const sp::Pose& pose) {
            sp::Koerperteil teil{masse, matrix(inertia), mesh, pose};
            teil.pruefen();
            return teil;
        }), py::arg("masse"), py::arg("traegheit").noconvert(),
            py::arg("mesh"), py::arg("pose"));
    py::class_<sp::Verband>(modul, "Verband")
        .def_readonly("masse", &sp::Verband::masse)
        .def_property_readonly("schwerpunkt", [](const sp::Verband& v) { return ausgabe(v.schwerpunkt); })
        .def_property_readonly("traegheit", [](const sp::Verband& v) {
            auto array = ausgabe(v.traegheit);
            array.resize({3, 3});
            return array;
        })
        .def_property_readonly("punkte", [](const sp::Verband& v) { return mesh_array(v.punkte); })
        .def_property_readonly("dreiecke", [](const sp::Verband& v) { return mesh_array(v.dreiecke); })
        .def_property_readonly("teilzentren", [](const sp::Verband& v) { return mesh_array(v.teilzentren); })
        .def_property_readonly("teilrotationen", [](const sp::Verband& v) {
            py::array_t<double> array({
                static_cast<py::ssize_t>(v.teilrotationen.size()), py::ssize_t(3), py::ssize_t(3)});
            auto daten = array.mutable_unchecked<3>();
            for (py::ssize_t n = 0; n < static_cast<py::ssize_t>(v.teilrotationen.size()); ++n) {
                for (py::ssize_t i = 0; i < 3; ++i) {
                    for (py::ssize_t j = 0; j < 3; ++j) {
                        daten(n, i, j) = v.teilrotationen[n][3 * i + j];
                    }
                }
            }
            return array;
        });
    modul.def("verband_aggregieren", [](
            const std::vector<sp::Koerperteil>& teile, const sp::Abbruch& abbruch) {
        py::gil_scoped_release frei;
        return sp::verband_aggregieren(teile, abbruch);
    }, py::arg("teile"), py::arg("abbruch"));
    py::class_<sp::VerbandKontext>(modul, "VerbandKontext")
        .def(py::init([](std::vector<sp::Koerperteil> teile, std::uint64_t version) {
            if (teile.empty()) {
                throw py::value_error("Verband braucht mindestens ein Teil");
            }
            for (const auto& teil : teile) {
                teil.pruefen();
            }
            return sp::VerbandKontext{std::move(teile), version};
        }), py::arg("teile"), py::arg("version"))
        .def_readonly("version", &sp::VerbandKontext::version)
        .def("aggregieren", [](const sp::VerbandKontext& kontext, const sp::Abbruch& abbruch) {
            py::gil_scoped_release frei;
            return sp::verband_aggregieren(kontext.teile, abbruch);
        }, py::arg("abbruch"));

    py::class_<sp::BlattKontext>(modul, "BlattKontext")
        .def(py::init([](const sp::Mesh& mesh, const py::array& rotation,
                         const py::array& translation) {
            auto r = matrix(rotation);
            sp::rotation_pruefen(r);
            return sp::BlattKontext{mesh, r, vektor<3>(translation, "Blatttranslation")};
        }), py::arg("mesh"), py::arg("rotation").noconvert(),
            py::arg("translation").noconvert());
    py::class_<sp::SnapshotKontext>(modul, "SnapshotKontext")
        .def(py::init([](double masse, const py::array& inertia, std::uint64_t version,
                         std::vector<sp::BlattKontext> blaetter) {
            auto tensor = matrix(inertia);
            sp::Modell{masse, tensor, {}, version, {0., 0., 0.}}.pruefen();
            return sp::SnapshotKontext{masse, tensor, version, std::move(blaetter)};
        }), py::arg("masse"), py::arg("traegheit").noconvert(),
            py::arg("version"), py::arg("blaetter"))
        .def_readonly("version", &sp::SnapshotKontext::version)
        .def("auswerten", [](const sp::SnapshotKontext& kontext, const sp::Abbruch& abbruch) {
            py::gil_scoped_release frei;
            return kontext.auswerten(abbruch);
        }, py::arg("abbruch"));
}
