#!/usr/bin/env bash
set -euo pipefail
demo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$demo_root/../.." && pwd)"
source_root="${SUPERDEX_ROOT:-$root/vendor/project_superdex}"
python_bin="${SUPERDEX_PYTHON:-$root/.venv/bin/python}"
native_bin="${SUPERDEX_NATIVE_BIN:-$source_root/build-grasp-fp64/bin}"
export SUPERDEX_PRECISION=fp64
# Explicit source overrides take precedence; otherwise use the installed wheel.
if [[ -n "${SUPERDEX_ROOT:-}" || -n "${SUPERDEX_NATIVE_BIN:-}" ]]; then
  export PYTHONPATH="$native_bin:$source_root/superdex_physics/wheels/superdex-physics:$source_root/superdex_robotics"
elif ! "$python_bin" -I -c 'import importlib.metadata; importlib.metadata.version("superdex-physics")' 2>/dev/null; then
  export PYTHONPATH="$native_bin:$source_root/superdex_physics/wheels/superdex-physics:$source_root/superdex_robotics"
else
  unset PYTHONPATH
fi
echo "Preparing SDF, settling, and planning first; the viewer opens afterward unless --headless is set."
exec "$python_bin" "$demo_root/src/wuji_stem_grasp.py" --sequence --output "$demo_root/runs/latest" "$@"
