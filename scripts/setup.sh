#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-}" == --source ]]; then
  shift
  exec bash "$root/scripts/setup_source.sh" "$@"
fi
for argument in "$@"; do
  if [[ "$argument" == --help || "$argument" == -h ]]; then
    exec python3 "$root/scripts/setup_preflight.py" "$@"
  fi
done
if [[ "$(uname -s)-$(uname -m)" != Linux-x86_64 ]]; then
  echo "This installer is validated on Linux x86_64. See docs/installation.md." >&2
  exit 1
fi
python3 "$root/scripts/setup_preflight.py" "$@"
uv_bin="$(command -v uv || true)"
if [[ -z "$uv_bin" && -x "$HOME/.local/bin/uv" ]]; then
  uv_bin="$HOME/.local/bin/uv"
fi
if [[ -z "$uv_bin" ]]; then
  echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi
if [[ ! -e "$root/.venv/bin/python" ]]; then
  "$uv_bin" venv --python 3.12 "$root/.venv"
fi
python3 "$root/scripts/setup_preflight.py" "$@"
"$uv_bin" pip install --python "$root/.venv/bin/python" \
  -r "$root/demos/apple-stem-grasp/requirements.txt" \
  -r "$root/scripts/runtime-requirements.txt"
SUPERDEX_PRECISION=fp64 "$root/.venv/bin/python" -I -c \
  'from superdex import physics, robotics; assert physics.uses_double_precision(); print("SuperDex FP64 runtime ready.")'
"$uv_bin" pip install --python "$root/.venv/bin/python" --torch-backend cpu -c "$root/scripts/python-constraints.txt" -e "$root"
"$root/.venv/bin/python" "$root/scripts/download_assets.py"

echo "Ready. Run: bash demos/apple-stem-grasp/run.sh"
