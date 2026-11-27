#!/usr/bin/env bash
# Compile our recorder against an independently qualified official CPU SDK build.
set -euo pipefail
if [[ $# != 3 ]]; then
    echo 'Usage: build_physx_incline.sh SDK_ROOT STATIC_LIBRARY_DIR OUTPUT_BINARY' >&2
    exit 2
fi
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
library_suffix=_64
if [[ ! -f "$2/libPhysX_static_64.a" && -f "$2/libPhysX_static.a" ]]; then
    library_suffix=
fi
"${CXX:-g++}" -std=c++14 -O2 -DNDEBUG -DPX_PHYSX_STATIC_LIB \
    -Wall -Wextra -Werror -Wno-deprecated-declarations \
    "$repo/native/physx_incline.cpp" -isystem "$1/include" -L "$2" \
    -Wl,--start-group "-lPhysXExtensions_static$library_suffix" "-lPhysX_static$library_suffix" \
    "-lPhysXPvdSDK_static$library_suffix" "-lPhysXCooking_static$library_suffix" \
    "-lPhysXCommon_static$library_suffix" "-lPhysXFoundation_static$library_suffix" \
    -Wl,--end-group -ldl -lpthread -o "$3"
