# PhysX SDF apple-stem grasp

[English](apple.md) | [简体中文](apple.zh-CN.md)

OpenArm + Wuji executes a **14-second native PhysX grasp through UniSim's Isaac Sim 5.1 backend**, including a continuous three-second hold. The apple and both pads use native SDF collision. Official PhysX, Isaac Sim and IsaacLab are unchanged; adapter extensions and controller settings are disclosed.

![PhysX stem-grasp close-up](media/physx-sdf.gif)

[Continuous video](media/physx-sdf.mp4) · [Single-scene acceptance](evidence/apple-grasp-v1/qualification.json) · [Independent geometry audit](evidence/apple-grasp-v1/geometry.json) · [Development and failures](evidence/apple-grasp-v1/development.json)

## Run

Install DexLab and the [optional PhysX worker](README.md#setup-and-run) first. Preparation inherits the existing SuperDex/MuJoCo model and kinematic prior; this is not a standalone PhysX asset-preparation chain. An existing complete MuJoCo run can be reused.

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless \
  --output demos/apple-stem-grasp/runs/physx-source
.venv/bin/python -m dexlab.physx_apple \
  --source-run demos/apple-stem-grasp/runs/physx-source \
  --output demos/physx-contact/runs/my-apple
# Independent triangle-surface coverage of every recorded physics step.
"$UNISIM_ISAACSIM_HOME/venv/bin/python" src/dexlab/physx_geometry.py \
  demos/physx-contact/runs/my-apple --output demos/physx-contact/runs/my-apple-geometry.json
.venv/bin/python -m dexlab.physx_apple_score \
  demos/physx-contact/runs/my-apple \
  --geometry demos/physx-contact/runs/my-apple-geometry.json \
  --output demos/physx-contact/runs/my-apple-qualification.json
```

Runner exit 0 means complete recording; the separate scorer decides acceptance. Without `--geometry`, native diagnostics are available but full acceptance cannot pass. Run directories and score files must not exist; failures are retained. The tested worker uses Python 3.11.14, Isaac Sim 5.1.0.0, IsaacLab core 0.47.2 and Torch 2.7.0+cu128. Geometry auditing uses Warp 1.17.0. Fresh-machine installation has not been repeated.

## Parameters and model scope

| Item | Setting and provenance |
|---|---|
| Object | Apple and stem form one free 0.2 kg body; no bending or fracture |
| Collision | Native SDF resolution 256, subgrid 6; source surfaces are resampled, not identical discrete SDFs across engines |
| Integration/solver | 1 ms, reported TGS profile with 8/2 iteration settings and per-iteration external forces; [solver-name readback absent, audit #126](../../docs/physx-solver-audit.md) |
| Material/offsets | Static/dynamic friction 1.0; contact offset 0.1 mm, rest offset zero; engineering settings, not calibrated material |
| Torsion | Explicit 1 mm minimum torsional patch radius on scene colliders, through the official PhysX property |
| Drives | Compiled source inertia/gains and target-velocity compensation; no claim of calibrated hardware motor/effort limits |
| Control | Known-state joint prior; one alignment after one-second settling, extra height 10.75 mm; 95% of the original hand-synergy path |

The source MuJoCo configuration uses `condim=4` and torsional friction coefficient `0.001`. The PhysX radius gives a related torque scale, not contact-model equivalence or material calibration. A zero-minimum-radius control with the same closure setting does not lift the apple. The option applies to the whole scene, so this difference cannot be attributed exclusively to apple contacts.

Reducing closure to 95% avoids excessive clamping and fruit/nail assistance. Full closure retains the apple but introduces nail load during hold, failing strict stem acceptance. Those failures, neighboring-height failures and the zero-radius control remain available. There is no vision policy, learned controller, attachment constraint, or object-pose write after initialization. Robot self-collision remains enabled with 267 source exclusion pairs. The table stays; the distant floor is omitted.

## Single-scene observations

| Metric | Result |
|---|---:|
| Physics steps / hold window | 14,000 / [11, 14) s |
| Minimum clearance | 125.087 mm |
| Wrist-relative displacement / rotation | 0.540 mm / 0.745° |
| Mean vertical hand support / weight | 0.999972 |
| Fruit and other-hand contact load during hold | 0 N |
| Maximum native hand penetration | 0.0487 mm |
| Maximum independent sampled surface penetration | 0.1397 mm |
| Penetration bound including spatial/time coverage | 0.7396 mm |

Native separation and reference-surface penetration are distinct measurements. The independent audit covers all 79 robot collision surfaces: disjoint bounding spheres exclude distant surfaces; the rest use bidirectional triangle-surface distance. Spatial edges are at most 0.4 mm. Rigid-motion bounds cover saved steps not queried separately, adding at most 0.2 mm. Warp FP32 queries also pass analytical-box and transform checks. The bound excludes source-mesh error and a general floating-point error proof; it is not a hardware-accuracy guarantee.

Every physics step records actual body/joint state, normal contacts and separate friction anchors. Peak linear-momentum residual is 0.00269% of weight. Complete contact moments are unavailable, so angular momentum and total energy accounting are not claimed. Full worker stderr is retained. The pinned SDK's `IPhysxBenchmarks` plugin-dependency declaration warning is listed separately; other physics warnings/errors prevent acceptance. Initial native apple/table overlap is about 1.470 mm and reported separately; the 1 mm limit applies to hand/apple overlap.

This is one development scene, reproduced from independent process starts with identical state records. It is not a held-out success rate or engine-accuracy ranking. Public reports are summaries, not substitutes for the complete local arrays and source geometry; the commands regenerate independently scorable records.

## Replay

```bash
.venv/bin/python -m dexlab.physx_apple_replay \
  demos/physx-contact/runs/my-apple \
  --display-run demos/apple-stem-grasp/runs/physx-source \
  --output demos/physx-contact/runs/my-apple-replay
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py \
  demos/physx-contact/runs/my-apple-replay --output demos/physx-contact/runs/my-apple-media
```

MuJoCo renders actual PhysX poses. Only folded massless fixed frames are reconstructed kinematically. The continuous 14-second video contains 280 frames and no fingertip markers; the apple-following camera is presentation only.
