#!/usr/bin/env bash
set -euo pipefail
demo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$demo_root/../.." && pwd)"
python_bin="${DEXLAB_PYTHON:-$root/.venv/bin/python}"
robot_model="${DEXLAB_ROBOT_MODEL:-$root/demos/apple-stem-grasp/runs/latest-mujoco-sdf/model.xml}"
exec "$python_bin" "$demo_root/src/run_cloth.py" \
  --robot-model "$robot_model" --output "$demo_root/runs/latest" "$@"
