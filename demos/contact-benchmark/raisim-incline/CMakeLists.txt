cmake_minimum_required(VERSION 3.18)
project(dexlab_raisim_incline LANGUAGES CXX)

find_package(raisim 2.16.0 EXACT CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)

add_executable(record_raisim_incline record.cpp)
target_compile_features(record_raisim_incline PRIVATE cxx_std_20)
target_link_libraries(record_raisim_incline PRIVATE raisim::raisim nlohmann_json::nlohmann_json)
