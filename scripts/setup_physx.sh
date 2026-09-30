#!/usr/bin/env bash
# Optional isolated Isaac Sim 5.1 worker for UniSim 1.7.10.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
worker_root=${UNISIM_ISAACSIM_HOME:-"$HOME/.cache/unisim/isaacsim"}
isaaclab_commit=3c6e67bb5c7ada942a6d1884ab69338f57596f77
unisim_commit=dc41b5e79d58d9b58eba9b2f27d10d71e16cf03d
host_python="$script_dir/../.venv/bin/python"

if [[ ${1:-} == --help ]]; then
  echo 'Usage: UNISIM_ISAACSIM_HOME=/path/to/worker bash scripts/setup_physx.sh'
  echo 'Linux x86_64 with an NVIDIA GPU; optional multi-GB Isaac Sim 5.1 installation.'
  echo 'Also installs the disclosed UniSim normal/friction reporting, drive, SDF and compliant-contact adapter extensions; PhysX is unchanged.'
  exit 0
fi
[[ $# == 0 ]] || { echo 'Unknown argument; use --help.' >&2; exit 2; }
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || {
  echo 'This pinned worker supports Linux x86_64 only.' >&2; exit 1;
}
for executable in uv git flock nvidia-smi g++ cmake; do
  command -v "$executable" >/dev/null || { echo "Missing $executable" >&2; exit 1; }
done
[[ -x "$host_python" ]] || { echo 'Run scripts/setup.sh first.' >&2; exit 1; }
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
"$worker_python" - "$worker_root" "$script_dir/../demos/physx-contact/evidence/sdk-wheel-sizes.json" <<'PY'
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import shutil
import sys

torch_pins = {"torch": "2.7.0+cu128", "torchvision": "0.22.0+cu128", "torchaudio": "2.7.0+cu128"}
try:
    torch_ready = all(version(name) == expected for name, expected in torch_pins.items())
except PackageNotFoundError:
    torch_ready = False
try:
    sdk_ready = all(version(item["name"]) == item["version"]
                    for item in json.loads(Path(sys.argv[2]).read_text()))
except PackageNotFoundError:
    sdk_ready = False
# The pinned SDK wheel audit measured 4.36 GiB compressed / 9.70 GiB expanded.
# 25 GiB also leaves room for ordinary dependencies and initial runtime caches.
reserve = 8 if torch_ready and sdk_ready else 25 if torch_ready else 35
free = shutil.disk_usage(sys.argv[1]).free / 2**30
if free < reserve:
    raise SystemExit(f"Only {free:.1f} GiB free; reserve at least {reserve} GiB for the remaining optional worker installation. Existing data preserved.")
print(f"Worker space: {free:.1f} GiB free, {reserve} GiB reserved; pinned Torch: {torch_ready}, SDK: {sdk_ready}")
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

# UniSim 1.7.10 omits PhysxContactReportAPI on imported rigid bodies.
# Build the explicit adapter-only patch, without editing installed engine files.
unisim_dir=${DEXLAB_UNISIM_SOURCE:-"$worker_root/UniSim-physx-precision"}
adapter_patch="$script_dir/patches/unisim-1.7.10-physx-adapter.patch"
if [[ ! -e "$unisim_dir" ]]; then
  git init "$unisim_dir"
  git -C "$unisim_dir" remote add origin https://github.com/unilabsim/unisim.git
  git -C "$unisim_dir" fetch --depth=1 origin "$unisim_commit"
  git -C "$unisim_dir" checkout --detach FETCH_HEAD
fi
[[ $(git -C "$unisim_dir" rev-parse HEAD) == "$unisim_commit" ]] || {
  echo "UniSim source must be pinned at $unisim_commit; existing checkout preserved." >&2; exit 1;
}
[[ -z $(git -C "$unisim_dir" ls-files --others --exclude-standard) ]] || {
  echo 'Unexpected untracked UniSim files; existing checkout preserved.' >&2; exit 1;
}
if git -C "$unisim_dir" diff --quiet HEAD; then
  git -C "$unisim_dir" apply --check "$adapter_patch"
  git -C "$unisim_dir" apply "$adapter_patch"
  # Include patch-created files in the exact diff; do not stage file contents.
  git -C "$unisim_dir" add --intent-to-add -- \
    src/unisim/backend/isaacsim/sdf_collision.py \
    tests/adapters/isaacsim/test_sdf_collision.py \
    src/unisim/backend/isaacsim/contact_details.py \
    tests/adapters/isaacsim/test_contact_details.py \
    tests/adapters/isaacsim/test_compliant_contact.py
fi
git -C "$unisim_dir" -c core.abbrev=7 diff --no-ext-diff --binary \
  --src-prefix=a/ --dst-prefix=b/ --no-color HEAD | cmp - "$adapter_patch" || {
  echo 'UniSim changes differ from the disclosed adapter patch; existing checkout preserved.' >&2; exit 1;
}
uv pip install --python "$host_python" --no-deps --reinstall-package unisim-core "$unisim_dir"
uv pip check --python "$host_python"
sha256sum "$adapter_patch" "$unisim_dir/src/unisim/backend/isaacsim/scene_worker.py" \
  > "$worker_root/unisim-adapter.sha256"
echo "Installed worker: $worker_root"
echo 'Installation is not physics qualification. Run the contact baselines next.'
