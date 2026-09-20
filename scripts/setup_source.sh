#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="$root/vendor/project_superdex"
revision="f216dace36464d70f224caa4253074ec365ed14f"

if [[ "$(uname -s)" != Linux ]]; then
  echo "This installer supports Linux. See docs/installation.md."
  exit 1
fi
uv_bin="$(command -v uv || true)"
if [[ -z "$uv_bin" && -x "$HOME/.local/bin/uv" ]]; then
  uv_bin="$HOME/.local/bin/uv"
fi
if [[ -z "$uv_bin" ]]; then
  echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi
for command in git "${CC:-clang-18}" "${CXX:-clang++-18}"; do
  if ! command -v "$command" >/dev/null; then
    echo "Missing $command. Install the system prerequisites in docs/installation.md."
    exit 1
  fi
done

if [[ ! -e "$root/.venv/bin/python" ]]; then
  "$uv_bin" venv --python 3.12 "$root/.venv"
fi
"$root/.venv/bin/python" -c \
  'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else "Existing .venv must use Python 3.12.")'
"$uv_bin" pip install --python "$root/.venv/bin/python" \
  -r "$root/demos/apple-stem-grasp/requirements.txt" cmake==4.4.0 ninja==1.13.2

if [[ ! -d "$source_root" ]]; then
  git init -q "$source_root"
  git -C "$source_root" remote add origin https://github.com/unilabsim/project_superdex.git
fi
if [[ ! -d "$source_root/.git" && ! -f "$source_root/.git" ]]; then
  echo "Existing vendor/project_superdex is not a Git checkout; leaving it unchanged."
  exit 1
fi
if ! git -C "$source_root" cat-file -e "$revision^{commit}" 2>/dev/null; then
  git -C "$source_root" fetch --depth 1 origin "$revision"
fi
if git -C "$source_root" rev-parse --verify HEAD >/dev/null 2>&1; then
  if [[ "$(git -C "$source_root" rev-parse HEAD)" != "$revision" ]] || \
     [[ -n "$(git -C "$source_root" status --porcelain --untracked-files=no)" ]]; then
    echo "Existing SuperDex checkout differs from the pinned source; leaving it unchanged."
    exit 1
  fi
else
  git -C "$source_root" checkout --detach "$revision"
fi
git -C "$source_root" submodule update --init --recursive

export PATH="$root/.venv/bin:$PATH"
export SUPERDEX_ROOT="$source_root"
export SUPERDEX_PYTHON="$root/.venv/bin/python"
bash "$root/scripts/build_superdex.sh"
SUPERDEX_NATIVE_BIN="$source_root/build-grasp-fp64/bin" \
  bash "$root/demos/apple-stem-grasp/run.sh" --help >/dev/null

"$root/.venv/bin/python" "$root/scripts/download_assets.py"

echo "Ready. Run: bash demos/apple-stem-grasp/run.sh"
