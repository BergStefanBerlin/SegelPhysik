cmake_minimum_required(VERSION 3.20)
project(segelphysik_native LANGUAGES CXX)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_segelphysik_native src/modul.cpp)
target_compile_features(_segelphysik_native PRIVATE cxx_std_17)
if(MSVC)
    target_compile_options(_segelphysik_native PRIVATE /fp:precise)
endif()
install(TARGETS _segelphysik_native LIBRARY DESTINATION . RUNTIME DESTINATION .)
