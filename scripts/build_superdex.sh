#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="${SUPERDEX_ROOT:-$root/vendor/project_superdex}"
python_bin="${SUPERDEX_PYTHON:-$root/.venv/bin/python}"
export CC="${CC:-clang-18}"
export CXX="${CXX:-clang++-18}"
cmake -S "$source_root" -B "$source_root/build-grasp-fp64" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_SCAN_FOR_MODULES=OFF \
  -DPython_EXECUTABLE="$python_bin" -DMOCHI_BUILD_DEBUGGER=OFF \
  -DMOCHI_BUILD_MESH_CLI=OFF -DMOCHI_BUILD_RENDERER=OFF \
  -DMOCHI_BUILD_SHARED=ON -DMOCHI_USE_DOUBLE_PRECISION=ON \
  -DMOCHI_USE_PYBIND=ON -DSUPERDEX_BUILD_ROBOTICS=ON
cmake --build "$source_root/build-grasp-fp64" \
  --target mochi_physics_pybind superdex_robotics_pybind --parallel "${BUILD_JOBS:-8}"
