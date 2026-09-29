# OpenArm + Wuji articulation qualification

[English](robot.md) | [简体中文](robot.zh-CN.md)

PhysX, through UniSim, drives the **54 actual joints** of the OpenArm arms and Wuji hands. This protocol disables gravity and contacts to check model transfer, joint ordering, measured motion, forward-kinematics consistency, and return to the initial posture. It does not qualify loaded robot control, SDF contacts, apple grasping, or hardware accuracy.

## Model and controller provenance

Inputs are the compiled model, `model.xml`, and `command-plan.npz` from an existing MuJoCo apple-grasp run. Masses, centers of mass, inertias, and effective drive gains come from the compiled model, avoiding the XML's compile-only massless-link placeholders. The initial command is that run's pregrasp posture.

Fifteen fixed frames with zero mass and inertia are folded into their parents, composing both translations and rotations. Named sites preserve the original frames in the offline model. The robot changes from 92 links to 77 native bodies while retaining all 54 joints. Unit mass/inertia on the fixed root serves only as an import anchor, not a hardware parameter. At 17 postures the converter checks the full 54×54 joint mass matrix and retained link poses against the source, with a `1e-10` error bound. The self-contained scoring model retains joints and inertials without external meshes.

Drives retain the source run's effective gains, including its `dt × kp` damping term; the new experiment timestep is not substituted into that term. The source task has no motor torque limits, mapped by UniSim to `1e9 N·m`, **not a hardware limit**. This protocol does not establish identical transient drive responses in MuJoCo and PhysX. Fixed-frame folding, convex-mesh conversion, and disabled contacts are disclosed.

## Protocol and results

The timestep is 1 ms with 4,000 recorded steps. Squared-sine targets perform two excursions during the first 2 s, followed by 2 s returning to and settling at the initial posture. Each amplitude is at most 0.03 rad and points toward the roomier side of the joint range. Every step records actual joint positions/velocities and native link poses. The scorer independently recomputes forward kinematics from measured joint positions, never substituting target angles. There are no state resets or object pose drives inside the loop.

| Metric | Current qualification | Frozen bound |
|---|---:|---:|
| Maximum link-position consistency residual | 0.712 μm | < 100 μm |
| Maximum link-orientation consistency residual | 2.790 μrad | < 1,000 μrad |
| Minimum actual excursion across joints | 0.02819 rad | > 0.01 rad |
| Maximum return error during the final 0.5 s | 0.00001776 rad | < 0.001 rad |
| Maximum joint speed during the final 0.5 s | 0.0004318 rad/s | < 0.001 rad/s |

Additional checks cover complete sampling, finite values, joint limits, unit quaternions, 54-joint topology, native body order, mass readback, and source/record hashes. Frame reduction changes positions by at most `1.11e-16 m` and joint mass-matrix elements by at most `3.05e-16`. These measure consistency between digital models, not real-robot accuracy or engine superiority.

## Reproduce

Prepare the optional Isaac Sim worker using the [installation instructions](README.md#setup-and-run). Use a new output directory for every run.

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless \
  --output demos/apple-stem-grasp/runs/robot-source
.venv/bin/python -m dexlab.physx_robot run \
  --source-run demos/apple-stem-grasp/runs/robot-source \
  --output demos/physx-contact/runs/robot
.venv/bin/python -m dexlab.physx_robot verify demos/physx-contact/runs/robot
```

The [v0.7.0 evidence attachment](https://github.com/huangkiki/Dexlab/releases/download/v0.7.0/v0.7.0-robot-articulation-evidence.tar.gz) contains all nine import/development/qualification runs, including original failures. It is an optional 25.4 MiB download with 576 hashed artifacts, separate from ordinary installation. See the [archive identity](evidence/robot-v1/archive.json) and [final results](evidence/robot-v1/summary.json). After extraction:

```bash
.venv/bin/python -m dexlab.physx_robot verify robot-v1/robot-articulation-final-v1
```

Offline `verify` does not launch Isaac Sim. It checks original file hashes and recomputes joint-motion and pose consistency for every frame. Completion and acceptance are separate. Startup errors, partial trajectories, and cleanup errors cannot pass.

## Preserved failures and remaining work

- Direct source MJCF import was rejected by UniSim for the nondefault `inertiafromgeom` compiler option. Removing this redundant option with explicit inertials still requires comparison against the original compiled model.
- Isaac Sim's MJCF importer omitted both original `type="sdf"` fingertip colliders; UniSim rejected the native geometry-count mismatch. This contact-free experiment explicitly converts them to meshes. **Native PhysX SDF mapping is not implemented yet.**
- The first development trajectory barely exercised the thumb's final joint near its limit. The qualification protocol moves inward and requires measured motion at every joint.
- The first qualification record passed physics checks but the scorer incorrectly required mass metadata to say `exact`; the adapter reports `unknown` for actual floating-point differences. The corrected scorer compares native per-body values numerically to the model. The failed record is retained and physical thresholds are unchanged.

Next are gravity/loaded motion, native SDF geometry and collision filtering, then apple grasping. [Issue #5](https://github.com/huangkiki/Dexlab/issues/5) remains incomplete.
