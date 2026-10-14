# PhysX contact qualification

[English](README.md) | [简体中文](README.zh-CN.md)

The [historical solver/version audit](../../docs/physx-solver-audit.md) separates native scene readbacks, source/report TGS profiles and missing fields; [P0 #126](https://github.com/huangkiki/Dexlab/issues/126) retains contemporaneous core/loaded-library identity gaps.

Development work for [issue #5](https://github.com/huangkiki/Dexlab/issues/5).

See the complete [PhysX SDF grasp](apple.md) for sustained robot holding and independent surface checks. The primitive protocol remains below.
The runner uses UniSim 1.7.10's public entity API and a separate Isaac Sim 5.1 / IsaacLab core 0.47.2 worker. Three native primitive-contact cases pass independent acceptance with the disclosed UniSim contact-reporting fix. PhysX itself is unchanged. These primitive tests do not qualify robot grasping, SDF–SDF contact or cloth. A separate [drive protocol](drive.md) qualifies a loaded prismatic actuator.

## Setup and run

Install DexLab with `bash scripts/setup.sh` first. The optional worker requires Linux x86_64, an NVIDIA GPU/driver compatible with Isaac Sim 5.1, Git, a C++ compiler, CMake, and uv. The multi-GB SDK lives in Python 3.11; setup also installs the explicit UniSim adapter fix into DexLab's Python 3.12 environment. Torch uses hash-pinned official CUDA 12.8 wheels; ordinary CUDA dependencies come from PyPI. Reserve 35 GiB for a fresh installation, 25 GiB with the pinned Torch stack, or 8 GiB when all audited SDK wheels and Torch are already installed. The [SDK audit](evidence/sdk-wheel-sizes.json) measures 4.36 GiB compressed and 9.70 GiB expanded, excluding Torch, ordinary dependencies and runtime caches. `click==8.1.7` and `wheel==0.45.1` preserve compatibility with SDK dependencies.

```bash
export UNISIM_ISAACSIM_HOME="$HOME/.cache/unisim/isaacsim"
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_baseline run --case rest --output demos/physx-contact/runs/rest
.venv/bin/python -m dexlab.physx_baseline run --case slide --output demos/physx-contact/runs/slide
.venv/bin/python -m dexlab.physx_baseline run --case slide-frictionless --output demos/physx-contact/runs/frictionless
.venv/bin/python -m dexlab.physx_baseline verify demos/physx-contact/runs/rest
```

Use a new output directory for every run. Startup errors and partial arrays are retained with a failed summary. Installing packages or compiling a scene does not count as a completed physics test.

## Native results and adapter provenance

| Case | Measured result | Acceptance |
|---|---|---|
| Rest | Mean support error 0.000086%; tail speed below 0.052 mm/s | Pass |
| Slide, μ = 0.3 | Stops after 42.224 mm; Coulomb reference 42.474 mm | Pass |
| Slide, μ = 0 | Maintains 0.5 m/s; travels 1.000019 m in 2 s | Pass |

Each case records all 2,000 measured steps after 0.5 s settling. Native mass/friction and free/fixed body roles are checked. Ideal primitive geometry and FP32 observations do not establish hardware accuracy. These are single-case qualifications, not a success-rate or engine-ranking study.

[Complete records](evidence/qualification-v1/manifest.json) include arrays, source snapshots, import reports and original failures. They can be rescored without Isaac Sim:

```bash
.venv/bin/python -m dexlab.physx_baseline verify demos/physx-contact/evidence/qualification-v1/rest
```

Unmodified UniSim 1.7.10 failed both pair-sensor initialization and body-net force reads because imported bodies lacked `PhysxContactReportAPI`. The [five-line adapter patch](../../scripts/patches/unisim-1.7.10-physx-contact-reporting.patch) enables reporting before simulation and changes the role-cache identity to prevent stale USD reuse. The original qualification applied it only to upstream commit `dc41b5e79d58d9b58eba9b2f27d10d71e16cf03d`, checks the entire tracked diff, and builds a separate package. No PhysX solver/source patch or threshold relaxation is used. Upstream adapter checks passed: Ruff, mypy, Pyright, 1,304 tests (92 optional-runtime skips), and package build. This is local verification, not upstream approval.

## Physical protocol

A 0.2 kg cube with 40 mm sides rests on a horizontal box. Both bodies use analytic box collision shapes. Inertia is computed from the homogeneous-cube formula. Gravity is 9.81 m/s². All are declared task assumptions, not hardware measurements. After 0.5 s settling, record every 1 ms step for 2 s. Sliding starts by setting the initial actual-state velocity of 0.5 m/s once; subsequent motion is passive. Static/dynamic material readback is recorded. Rest uses friction 0.5; sliding uses 0.3; the zero-friction control must continue moving.

Compare stopping distance with the ideal Coulomb reference `v²/(2 μ g)`. Independently compute box-plane penetration from actual pose and analytic geometry, including rotation. Check support against this case's `m g`, not a fixed weight. Engineering limits are frozen in `LIMITS` before native runs: penetration below 1 mm, mean support error below 5%, rest drift below 1 mm, rest/final sliding speed below 5 mm/s, stopping-distance error below the larger of 2 mm or 10%, and frictionless speed error below 10 mm/s.

PhysX requests eight position and two velocity iterations, 1 mm contact offset and zero rest offset. These are numerical settings, not material calibration. The import report distinguishes authored settings from native readback. Pair sensors report world-frame normal contact forces, not friction forces; vertical support can be checked on this horizontal plane. Raw states, source/adapter snapshots, report/geometry hashes, versions and pass/failure details stay with each run. Step timing includes Python/IPC observations and is not pure solver time; rendering is disabled.

The primitive protocol covers the controls below. Subsequent [robot motion](robot.md), [native SDF contacts](sdf.md), [apple grasp](apple.md) and [surface cloth](cloth.md) provide separate evidence. Full engine comparisons still require matched calibration, timestep/geometry refinement and held-out scenes.

Sources: [Isaac Sim 5.1 Python installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html), [pinned IsaacLab source](https://github.com/isaac-sim/IsaacLab/tree/3c6e67bb5c7ada942a6d1884ab69338f57596f77), [UniSim entity contract](https://github.com/unilabsim/unisim/blob/v1.7.10/docs/en/entity-scenes.md).

## Controlled pinch and release

An ideal prismatic fixture measures about 4 N normal load per finger. The 0.2 kg, μ=0.3 case holds; the 0.5 kg overload and μ=0 controls drop 103.39 mm and 197.18 mm within 200 ms after preparation support is removed. Fully released motion has acceleration near −9.81 m/s². All three final qualifications pass; the initial travel-stop readback failure is retained. [Protocol, complete outcomes and reproduction](pinch.md).

This is not robot joint/actuator or apple-grasp qualification; tangential contact forces are not observed.

## Loaded joint drive

A 0.1 kg prismatic drive reproduces TGS steady-state position/velocity inconsistency. The native per-iteration external-force option passes independent equilibrium, velocity, force-limit and return checks. The default configuration remains a recorded failure. [Protocol, native SDK control and limitations](drive.md). Current setup installs the disclosed [combined adapter patch](../../scripts/patches/unisim-1.7.10-physx-adapter.patch); the new option is opt-in and does not change existing contact defaults.

## Robot articulation

The actual OpenArm/Wuji 54-joint articulation passed an unloaded, contact-free motion qualification. Frame reduction preserves the source joint mass matrix and forward kinematics. This motion protocol excludes native SDF and loaded grasping; see the separate [grasp qualification](apple.md). [Protocol, results and failures](robot.md).

[Native SDF controls and known convex-control drift](sdf.md)

## Detailed contact forces

[Normal/friction recording and loaded apple diagnostics](contact-details.md): the sliding-block momentum check passes; robot collision filtering now preserves source semantics. That page preserves the earlier continuous-hold failures; the subsequent [grasp qualification](apple.md) passes.

[PhysX surface cloth](cloth.md) runs through the UniLab task with independent geometry scoring; prescribed per-node-force extension is unsupported.
