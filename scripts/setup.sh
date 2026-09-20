#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# == 1 && "${1:-}" == --source ]]; then
  shift
  exec bash "$root/scripts/setup_source.sh" "$@"
fi
if [[ $# != 0 ]]; then
  echo "Usage: bash scripts/setup.sh [--source]" >&2
  exit 1
fi
if [[ "$(uname -s)-$(uname -m)" != Linux-x86_64 ]]; then
  echo "This installer is validated on Linux x86_64. See docs/installation.md." >&2
  exit 1
fi
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
"$root/.venv/bin/python" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else "Existing .venv must use Python 3.12.")'
"$uv_bin" pip install --python "$root/.venv/bin/python" \
  -r "$root/demos/apple-stem-grasp/requirements.txt" \
  -r "$root/scripts/runtime-requirements.txt"
SUPERDEX_PRECISION=fp64 "$root/.venv/bin/python" -I -c \
  'from superdex import physics, robotics; assert physics.uses_double_precision(); print("SuperDex FP64 runtime ready.")'
"$root/.venv/bin/python" "$root/scripts/download_assets.py"

echo "Ready. Run: bash demos/apple-stem-grasp/run.sh"
