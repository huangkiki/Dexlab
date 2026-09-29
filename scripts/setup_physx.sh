#!/usr/bin/env bash
# Optional isolated Isaac Sim 5.1 worker for UniSim 1.7.10.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
worker_root=${UNISIM_ISAACSIM_HOME:-"$HOME/.cache/unisim/isaacsim"}
isaaclab_commit=3c6e67bb5c7ada942a6d1884ab69338f57596f77

if [[ ${1:-} == --help ]]; then
  echo 'Usage: UNISIM_ISAACSIM_HOME=/path/to/worker bash scripts/setup_physx.sh'
  echo 'Linux x86_64 with an NVIDIA GPU; optional multi-GB Isaac Sim 5.1 installation.'
  exit 0
fi
[[ $# == 0 ]] || { echo 'Unknown argument; use --help.' >&2; exit 2; }
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || {
  echo 'This pinned worker supports Linux x86_64 only.' >&2; exit 1;
}
for executable in uv git flock nvidia-smi g++ cmake; do
  command -v "$executable" >/dev/null || { echo "Missing $executable" >&2; exit 1; }
done
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
mkdir -p "$worker_root"
worker_root=$(cd "$worker_root" && pwd)
exec 9>"$worker_root/.install.lock"
flock -n 9 || { echo "Another installer owns $worker_root/.install.lock" >&2; exit 1; }
worker_python="$worker_root/venv/bin/python"
if [[ ! -e "$worker_root/venv" ]]; then
  uv venv --no-project --python 3.11.14 --seed "$worker_root/venv"
fi
"$worker_python" -c 'import sys; assert sys.version_info[:2] == (3, 11) and sys.version_info.releaselevel == "final", sys.version'
# Reserve for remaining downloads/extraction; reuse an already installed Torch stack.
"$worker_python" - "$worker_root" <<'PY'
from importlib.metadata import PackageNotFoundError, version
import shutil
import sys

torch_pins = {"torch": "2.7.0+cu128", "torchvision": "0.22.0+cu128", "torchaudio": "2.7.0+cu128"}
try:
    torch_ready = all(version(name) == expected for name, expected in torch_pins.items())
except PackageNotFoundError:
    torch_ready = False
# The pinned SDK wheel audit measured 4.36 GiB compressed / 9.70 GiB expanded.
# 25 GiB also leaves room for ordinary dependencies and initial runtime caches.
reserve = 25 if torch_ready else 35
free = shutil.disk_usage(sys.argv[1]).free / 2**30
if free < reserve:
    raise SystemExit(f"Only {free:.1f} GiB free; reserve at least {reserve} GiB for the remaining optional worker installation. Existing data preserved.")
print(f"Worker space: {free:.1f} GiB free, {reserve} GiB reserved; pinned Torch present: {torch_ready}")
PY

isaaclab_dir="$worker_root/IsaacLab"
if [[ ! -e "$isaaclab_dir" ]]; then
  git init "$isaaclab_dir"
  git -C "$isaaclab_dir" remote add origin https://github.com/isaac-sim/IsaacLab.git
  git -C "$isaaclab_dir" fetch --depth=1 origin "$isaaclab_commit"
  git -C "$isaaclab_dir" checkout --detach FETCH_HEAD
fi
[[ $(git -C "$isaaclab_dir" rev-parse HEAD) == "$isaaclab_commit" ]] || {
  echo "IsaacLab must be pinned at $isaaclab_commit; existing checkout preserved." >&2; exit 1;
}
[[ -z $(git -C "$isaaclab_dir" status --porcelain --untracked-files=no) ]] || {
  echo 'IsaacLab has modified tracked files; existing checkout preserved.' >&2; exit 1;
}

# Direct official Torch URLs leave ordinary CUDA dependencies on PyPI.
export UV_HTTP_TIMEOUT=${UV_HTTP_TIMEOUT:-300}
uv pip install --python "$worker_python" --index-url https://pypi.org/simple \
  -r "$script_dir/requirements-physx-torch.txt"
# Explicit CUDA versions prevent an IsaacLab dependency from replacing Torch.
uv pip install --python "$worker_python" \
  --extra-index-url https://pypi.nvidia.com \
  --index-strategy unsafe-best-match \
  -r "$script_dir/requirements-physx.txt"

# Only the IsaacLab core package is needed by UniSim; no RL extension bundle.
uv pip install --python "$worker_python" \
  --index-strategy unsafe-best-match \
  --build-constraints "$script_dir/physx-build-constraints.txt" \
  --constraints "$script_dir/requirements-physx.txt" \
  -e "$isaaclab_dir/source/isaaclab"
uv pip check --python "$worker_python"
"$worker_python" -c 'import torch; assert torch.cuda.is_available(); print("CUDA", torch.version.cuda, "GPU", torch.cuda.get_device_name())'
uv pip freeze --python "$worker_python" > "$worker_root/requirements-installed.txt"
echo "Installed worker: $worker_root"
echo 'Installation is not physics qualification. Run the contact baselines next.'
