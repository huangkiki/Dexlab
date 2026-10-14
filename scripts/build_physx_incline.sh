#!/usr/bin/env bash
# Compile our recorder against an independently qualified official CPU SDK build.
set -euo pipefail
if [[ $# != 3 ]]; then
    echo 'Usage: build_physx_incline.sh SDK_ROOT STATIC_LIBRARY_DIR OUTPUT_BINARY' >&2
    exit 2
fi
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
"${CXX:-g++}" -std=c++14 -O2 -DNDEBUG -DPX_PHYSX_STATIC_LIB \
    -Wall -Wextra -Werror -Wno-deprecated-declarations \
    "$repo/native/physx_incline.cpp" -isystem "$1/include" -L "$2" \
    -Wl,--start-group -lPhysXExtensions_static_64 -lPhysX_static_64 \
    -lPhysXPvdSDK_static_64 -lPhysXCooking_static_64 \
    -lPhysXCommon_static_64 -lPhysXFoundation_static_64 \
    -Wl,--end-group -ldl -lpthread -o "$3"
