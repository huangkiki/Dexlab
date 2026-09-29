# PhysX contact qualification

[English](README.md) | [简体中文](README.zh-CN.md)

Development work for [issue #5](https://github.com/huangkiki/Dexlab/issues/5).
The runner uses UniSim 1.7.10's public entity API and a separate Isaac Sim 5.1 / IsaacLab 2.3.0 worker. Native PhysX validation is pending; no PhysX apple-stem or SDF–SDF result is claimed.

## Setup and run

Install DexLab with `bash scripts/setup.sh` first. The optional worker requires Linux x86_64, an NVIDIA GPU/driver compatible with Isaac Sim 5.1, Git, a C++ compiler, CMake, and uv. It downloads several GB independently of the default apple demo; the main Python 3.12 environment is preserved. Torch uses hash-pinned official CUDA 12.8 wheels for CPython 3.11; ordinary CUDA dependencies come from PyPI. Reserve 35 GiB free for a fresh installation, or 25 GiB when all three pinned Torch packages are already installed. These are installation reserves, not SDK size: the [pinned SDK wheel audit](evidence/sdk-wheel-sizes.json) measures 4.36 GiB compressed and 9.70 GiB expanded, excluding Torch, ordinary dependencies and runtime caches.

```bash
export UNISIM_ISAACSIM_HOME="$HOME/.cache/unisim/isaacsim"
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_baseline run --case rest --output demos/physx-contact/runs/rest
.venv/bin/python -m dexlab.physx_baseline run --case slide --output demos/physx-contact/runs/slide
.venv/bin/python -m dexlab.physx_baseline run --case slide-frictionless --output demos/physx-contact/runs/frictionless
.venv/bin/python -m dexlab.physx_baseline verify demos/physx-contact/runs/rest
```

Use a new output directory for every run. Startup errors and partial arrays are retained with a failed summary. Installing packages or compiling a scene does not count as a completed physics test.

## Protocol

A 0.2 kg cube with 40 mm sides rests on a horizontal box. Both bodies use analytic box collision shapes. Inertia is computed from the homogeneous-cube formula. Gravity is 9.81 m/s². All are declared task assumptions, not hardware measurements. After 0.5 s settling, record every 1 ms step for 2 s. Sliding starts by setting the initial actual-state velocity of 0.5 m/s once; subsequent motion is passive. Static/dynamic material readback is recorded. Rest uses friction 0.5; sliding uses 0.3; the zero-friction control must continue moving.

Compare stopping distance with the ideal Coulomb reference `v²/(2 μ g)`. Independently compute box-plane penetration from actual pose and analytic geometry, including rotation. Check support against this case's `m g`, not a fixed weight. Engineering limits are frozen in `LIMITS` before native runs: penetration below 1 mm, mean support error below 5%, rest drift below 1 mm, rest/final sliding speed below 5 mm/s, stopping-distance error below the larger of 2 mm or 10%, and frictionless speed error below 10 mm/s.

PhysX requests eight position and two velocity iterations, 1 mm contact offset and zero rest offset. These are numerical settings to qualify, not material calibration. The adapter's import report distinguishes authored settings from native readback. Raw states/contact forces, source snapshot/hash, geometry hashes, runtime versions, configuration report and pass/failure details stay with each run. Step timing includes Python/IPC observations and is not pure solver time; rendering is disabled.

Remaining issue scope includes normal-force-controlled pinch with negative controls, robot joint/actuator qualification, then apple grasp. Primitive collision results cannot establish SDF equivalence or cloth capability. Full engine comparisons require matched calibration, timestep/geometry refinement and held-out scenes.

Sources: [Isaac Sim 5.1 Python installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html), [pinned IsaacLab source](https://github.com/isaac-sim/IsaacLab/tree/3c6e67bb5c7ada942a6d1884ab69338f57596f77), [UniSim entity contract](https://github.com/unilabsim/unisim/blob/v1.7.10/docs/en/entity-scenes.md).
