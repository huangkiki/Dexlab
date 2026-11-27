cmake_minimum_required(VERSION 3.18)
project(dexlab_raisim_incline LANGUAGES CXX)

set(DEXLAB_RAISIM_VERSION "2.16.0" CACHE STRING "Exact RaiSim SDK release")
find_package(raisim ${DEXLAB_RAISIM_VERSION} EXACT CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)

add_executable(record_raisim_incline record.cpp)
target_compile_features(record_raisim_incline PRIVATE cxx_std_20)
target_compile_definitions(record_raisim_incline PRIVATE DEXLAB_RAISIM_VERSION="${raisim_VERSION}")
target_link_libraries(record_raisim_incline PRIVATE raisim::raisim nlohmann_json::nlohmann_json)
