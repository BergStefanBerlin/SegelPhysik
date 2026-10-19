#include <pybind11/pybind11.h>

PYBIND11_MODULE(_segelphysik_native, modul)
{
    modul.doc() = "Native C++-Anbindung fuer SegelPhysik";
}
