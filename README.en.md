# DexLab

[简体中文](README.md) | [English](README.en.md)

**Robot contact-dynamics experiments built on UniLab: audit models, measure contact behavior, and reproduce grasps.**

DexLab uses small, repeatable robot tasks to investigate penetration, jitter, slip, and numerical stability. The current case is **apple-stem grasping with OpenArm dual arms and Wuji hands**, using official MuJoCo and SuperDex FP64 SDF–SDF dynamics. The focus is parameter provenance, collision and drive models, and independent physical acceptance.

[Quick start](#run) · [Results](#results) · [Diagnostics](#model-audits-and-diagnostics) · [Research methods](docs/research-focus.md) · [Releases](https://github.com/huangkiki/Dexlab/releases)

## MuJoCo

![MuJoCo stem-grasp close-up](demos/apple-stem-grasp/media/mujoco-sdf.gif)

## SuperDex

![SuperDex stem-grasp close-up](demos/apple-stem-grasp/media/superdex-sdf.gif)

Each GIF shows the continuous 14-second approach, pinch, lift, and hold. Only the grasp close-up is shown. The presentation camera follows the recorded apple and is not a control input. Both recordings replay actual physics poses using MuJoCo's renderer. [MuJoCo video](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex video](demos/apple-stem-grasp/media/superdex-sdf.mp4)

## Robot cloth grasp

![Wuji cloth pinch, lift and release close-up](demos/cloth-folding/media/grasp.gif)

A Wuji hand pinches, lifts and releases MuJoCo flex cloth through frictional contact. The continuous 9-second recording passes independent checks. Control uses known state and a scripted sequence; robot collisions use convex mesh approximations, without cloth attachment constraints. Bimanual folding has not passed. [Video and physics measurements](demos/cloth-folding/README.md)

## What is available

| Capability | Delivered behavior |
|---|---|
| Two-backend grasp | The same robot and task with two native SDF contact implementations, physics-step execution and evidence recording |
| Model audit | Source/runtime mass, COM, inertia, joints, drives, collision filters and initial overlap reports |
| Stability diagnostics | Position, velocity and force RMS/peaks, plus per-pad contact interruptions; missing data stays unknown |
| Independent acceptance | Checks the entire hold using recorded forces and poses rather than judging success from a video |
| Cloth experiments | MuJoCo flex, SuperDex shells and five Newton solvers; extension, sag, drape and self-collision checks; [results and limits](demos/cloth-benchmark/README.md) |
| Issue-driven development | Automated implementation, validation and review, followed by eligible merges and releases tied to commits and logs |

Integration currently uses the **UniLab task layer**. DexLab owns the scenes; UniSim's built-in adapters are not yet used. PhysX, multi-scene regression and hardware calibration are tracked in [Issues](https://github.com/huangkiki/Dexlab/issues).

## Grasp details

- The right thumb and index finger pinch the stem; the left arm stays parked. The apple and stem form **one free 0.2 kg rigid body**.
- The apple and both fingertip pads use **SDF collision geometry**. There are no attachment constraints, direct object position drives, or engine source patches.
- Control uses **known object poses, inverse kinematics, and scripted joint targets**. This is not a visual policy or a learned skill; no model API key is needed.
- The engines are tuned separately. MuJoCo uses SDF contact-point search and soft contact constraints with a **0.5 ms** timestep. SuperDex uses surface-sample integration and smooth penalty energy with a **2 ms** timestep. The same SDF geometry does not imply the same contact-force law.

Independent checks cover clearance, two-finger support, penetration, wrist-relative motion, and momentum balance during a continuous three-second hold. Fruit-body contact is allowed during approach. This is one tuned scene, without stem bending, fracture, or demonstrated hardware accuracy.

[MuJoCo acceptance](demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex acceptance](demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [Parameters and engine internals](docs/sdf-backends.md)

## Results

These are single-scene records using the released default configurations. The hold window is 11–14 s, with evidence recorded at every physics step.

| Metric | MuJoCo 3.11.0 | SuperDex 1.0.0 FP64 |
|---|---:|---:|
| Physics steps, full episode | 28,000 | 7,000 |
| Minimum table clearance, hold | 124.43 mm | 115.22 mm |
| Maximum hand penetration, full episode | 0.159 mm | 0.452 mm |
| Maximum wrist-relative displacement, hold | 0.275 mm | 0.040 mm |
| Mean-centered wrist-relative position RMS, hold | 0.0786 mm | 0.0115 mm |

Timesteps, friction and drives differ, so these numbers cannot rank engine accuracy. Displacement is not cumulative material-point slip; centered RMS still includes slow drift. See the [acceptance evidence](docs/sdf-backends.md#results-and-limits) and [diagnostic definitions](docs/jitter.md) for coverage and approximations.

## Run

Linux x86_64; install [uv](https://docs.astral.sh/uv/getting-started/installation/) first.

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# or
bash demos/apple-stem-grasp/run.sh --backend superdex
```

The viewer opens after SDF preparation and planning; add `--headless` on a server. Both commands step the registered **UniLab task `DexLab-AppleStem-v0`**. DexLab currently owns the native SDF scenes; these have not been replaced by UniSim's built-in backends.

[Installation](docs/installation.md) · [Task API and reproduction](demos/apple-stem-grasp/README.md) · [Autoresearch and issues](docs/autoresearch.md)

## Model audits and diagnostics

Each grasp run exports model-audit JSON. The MuJoCo path records both native source and compiled parameters. Intentional massless coordinate frames are distinguished from errors; the report never silently repairs a model.

```bash
# Recheck model parameters without rerunning physics
.venv/bin/python -m dexlab.model_audit \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf/model-audit.mujoco.json
# Measure jitter and contact interruptions from existing step records
.venv/bin/python -m dexlab.jitter demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

The [model audit](docs/model-audit.md) explains parameters and initial overlaps. [Jitter diagnostics](docs/jitter.md) explain load, missing records and duration bounds. Reports do not establish hardware calibration, and current logs are insufficient for a full-system energy balance.

## Contributing experiments

Submit reproducible problems, parameter experiments and failed trials as an [Issue](https://github.com/huangkiki/Dexlab/issues), including code version, commands, parameter sources, raw records and expected acceptance criteria. Autoresearch handles explicitly queued tasks, preserves failures and never relaxes thresholds to manufacture success. Validated and reviewed changes are automatically merged and released; unresolved problems are fixed or recorded as blockers. [Workflow and release policy](docs/autoresearch.md)

## Acknowledgments

Thanks to [UniLab](https://github.com/unilabsim/UniLab), [Project SuperDex](https://github.com/unilabsim/project_superdex), [MuJoCo](https://github.com/google-deepmind/mujoco), [OpenArm](https://github.com/enactic/openarm), and [Wuji](https://github.com/wuji-technology). The SuperDex grasp appears in [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex); Astra assisted development and debugging.

Code: [Apache-2.0](LICENSE). Third-party assets retain their own terms; see [asset sources](docs/ASSETS.md).
