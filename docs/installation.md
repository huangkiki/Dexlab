# Installation

[English](installation.md) | [简体中文](installation.zh-CN.md)

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from the repository root:

```bash
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# Or:
bash demos/apple-stem-grasp/run.sh --backend superdex
```

The installer uses **official SuperDex 1.0.0 wheels from PyPI** and obtains Python 3.12 automatically. No Clang, CMake, Git checkout of SuperDex, or API key is required. The install script currently supports Linux x86_64. Although upstream provides other platform wheels, this Demo's native macOS and Windows execution has not been validated.

Both commands open an interactive MuJoCo window after SDF creation, apple settling and grasp planning. The selected backend computes dynamics; MuJoCo renders both. Startup and simulation take time, even with a fast installation.

Both run the [14-second SDF–SDF grasp](sdf-backends.md). The MuJoCo backend uses the official pinned `mujoco==3.11.0` wheel and generates its dynamics model locally; no engine patch or compiler is needed. These commands write to separate `runs/latest-superdex-sdf/` and `runs/latest-mujoco-sdf/` directories within the demo by default.

On a server without a desktop:

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless
```

## Verification and video

Each demo records 14 seconds of simulated motion. Dynamics run on the CPU and take longer than the simulated duration. Setup fetches the robot asset pack and apple albedo texture using the versioned [asset manifest](../demos/apple-stem-grasp/assets.json). Small task-specific apple meshes and parameters stay in Git.

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py demos/apple-stem-grasp/runs/latest-mujoco-sdf
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

Replace `latest-mujoco-sdf` with `latest-superdex-sdf` for the other backend. Video export requires FFmpeg and working OpenGL / EGL drivers. To preserve a recording, pass `--output demos/apple-stem-grasp/runs/my-run` to `run.sh`.

Both recorded runs pass the full three-second hold checks. See the [MuJoCo report](../demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json), [SuperDex report](../demos/apple-stem-grasp/evidence/sdf-superdex/summary.json), and [acceptance criteria](sdf-backends.md#verify-and-render).

## Runtime provenance

The default installation pins these official distributions in `scripts/runtime-requirements.txt`:

- [superdex-physics[double]==1.0.0](https://pypi.org/project/superdex-physics/1.0.0/)
- [superdex-robotics[double]==1.0.0](https://pypi.org/project/superdex-robotics/1.0.0/)

The extras install both FP64 payload packages. `SUPERDEX_PRECISION=fp64` is set before importing the public `superdex.physics` and `superdex.robotics` APIs. DexLab does not recompile or redistribute these wheels. Their source repository, publisher attestations and platform-specific file hashes are available on PyPI. The umbrella `superdex` package is unnecessary for this demo.

## UniLab runtime

Transitive dependencies are pinned in `scripts/python-constraints.txt` to the validated environment.

The installer also installs the DexLab task extension in editable mode, pins `unilab==1.3.3` and `unisim-core==1.7.10`, and selects the **CPU wheel** of `torch==2.9.1`, without CUDA runtime downloads. UniLab still depends on training, logging and numerical packages, so the first download is substantially larger than the standalone script environment; the CPU Torch wheel alone is about 176 MiB. Grasp execution works offline after installation. Do not substitute `unilab[superdex]`: that extra selects `superdex-physics-uni`, not the official 1.0.0 FP64 combination validated here.

This implementation uses UniLab registration and environment lifecycle with task-owned native scenes; it does not claim to use UniSim's built-in adapters. See the [task API](../demos/apple-stem-grasp/README.md#unilab-task-api).

## Optional UniLab source build

For developers who need the original UniLab source baseline:

```bash
bash scripts/setup.sh --source
SUPERDEX_ROOT="$PWD/vendor/project_superdex" bash demos/apple-stem-grasp/run.sh --backend superdex
```

This builds [UniLab Project SuperDex](https://github.com/unilabsim/project_superdex) at commit `f216dace36464d70f224caa4253074ec365ed14f`, without modifying engine source. This commit identifies the source-build path, not the provenance of the official PyPI wheels.

Requires Git, Clang 18 and C++ development headers; uv installs CMake 4.4.0 and Ninja 1.13.2. See [build_superdex.sh](../scripts/build_superdex.sh) for all CMake arguments: Release, double precision, shared libraries, Python bindings, and robotics enabled; debugger, mesh CLI and renderer disabled. Both `mochi_physics_pybind` and `superdex_robotics_pybind` are built. `BUILD_JOBS` defaults to 8.

The clean source baseline has also been built with Clang 18.1.8, Python 3.12.12 and glibc 2.35 on Ubuntu 22.04. Existing modified or differently versioned source checkouts are left unchanged. To reuse another build, set `SUPERDEX_ROOT`, `SUPERDEX_PYTHON`, and optionally `SUPERDEX_NATIVE_BIN`.

See [asset provenance](ASSETS.md) for robot and apple terms.

## Asset downloads

`setup.sh` installs the required assets automatically. To fetch or check them separately:

```bash
.venv/bin/python scripts/download_assets.py
```

The robot pack (~16 MB) comes from a versioned GitHub Release; the apple albedo texture is fetched directly from the NVIDIA source recorded in the manifest. Unused normal, roughness and metallic textures are not downloaded. See [asset provenance](ASSETS.md) for the applicable terms.

Both the archive and individual files are SHA-256 checked. Downloads are cached under `${XDG_CACHE_HOME:-~/.cache}/dexlab/assets`. Already installed matching files are reused offline. Missing files can be restored from cache. Modified files are preserved and reported: move them aside before rerunning setup. A failed download is never installed as a complete asset.

The approximately 2 MB of task-specific apple geometry remains versioned with the controller to avoid requiring USD conversion tools or changing collision geometry. Demo videos and validation summaries are also included.
