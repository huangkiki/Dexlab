# DexLab

[简体中文](README.md) | [English](README.en.md)

**Robot contact-dynamics experiments built on UniLab: audit models, measure contact behavior, and reproduce grasps.**

DexLab uses reproducible rigid grasping and cloth experiments to study penetration, jitter, slip, and numerical stability. Cases include **OpenArm dual arms with Wuji hands grasping an apple stem and pinching cloth**, plus cloth extension, sag, and collision tests across solvers. Each experiment retains parameter provenance, raw trajectories, independent checks, and failed records.

[Quick start](#run) · [Results](#results) · [Diagnostics](#model-audits-and-diagnostics) · [Task and evidence inventory](docs/inventory/README.md) · [Research methods](docs/research-focus.md) · [Releases](https://github.com/huangkiki/Dexlab/releases)

## MuJoCo

![MuJoCo stem-grasp close-up](demos/apple-stem-grasp/media/mujoco-sdf.gif)

## SuperDex

![SuperDex stem-grasp close-up](demos/apple-stem-grasp/media/superdex-sdf.gif)

## PhysX

![PhysX stem-grasp close-up](demos/physx-contact/media/physx-sdf.gif)

Each GIF shows a continuous 14-second approach, pinch, lift and hold. The apple-following camera is presentation only; MuJoCo renders actual poses recorded from each engine. [MuJoCo video](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex video and recording](demos/apple-stem-grasp/media/superdex-sdf.mp4) · [PhysX video and reproduction](demos/physx-contact/apple.md)

## Robot cloth grasp

![Wuji cloth pinch, lift and release close-up](demos/cloth-folding/media/grasp.gif)

**Reassessment: this cloth recording intersects the table and does not establish a physically valid grasp.** The legacy protocol passed, but the new scorer finds triangle interiors inside the table in 176 of 225 saved frames, with a maximum interior depth of 3.00 mm. The GIF continuously replays the original 9-second trajectory with the success caption corrected; physical repair is tracked in [#32](https://github.com/huangkiki/Dexlab/issues/32). Control still uses known state and scripted joints, with no cloth attachments.

![Cloth table-intersection diagnostic](demos/cloth-folding/media/table-diagnostic.svg)

The curve measures zero-thickness triangle interiors inside the table, not native contact distance or a new physical threshold. [Old/new scores, measurements and coverage](demos/cloth-folding/SCORING.md) · [Video and reproduction](demos/cloth-folding/README.md)

## Engines and experiments

| Native profile | Current validation scope |
|---|---|
| MuJoCo 3.11.0 | SDF–SDF stem grasp, flex cloth, and frictional robot cloth grasp |
| SuperDex 1.0.0 FP64 | SDF–SDF stem grasp and experimental triangle shells |
| Newton XPBD / VBD / Style3D / SemiImplicit / Featherstone | Cloth experiments on a pinned upstream version; material and self-contact capabilities documented per solver |
| PhysX / Isaac Sim 5.1 | [SDF–SDF stem grasp](demos/physx-contact/apple.md), [primitive contacts and drives](demos/physx-contact/README.md), [54-joint motion](demos/physx-contact/robot.md); independent surface checks pass, failed controls retained; [native surface cloth](demos/physx-contact/cloth.md) |

The cloth benchmark completed **105 frozen held-out episodes: 52 passed the protocol checks and 53 failed, with no timeouts**. Cases cover extension, sag, sphere drape, and folded drop. Nominal materials are not calibrated across solvers; pass counts do not rank physical accuracy. [All results and reproduction](demos/cloth-benchmark/README.md#held-out-results)

Contact-mechanics development covers sliding, loading/unloading and two-pad load sweeps. Original failures are retained; refining the same cylinder surface lets SuperDex pass all four development hold/drop conditions. Cross-engine material calibration remains incomplete. [Experiments, failures and reproduction](demos/contact-benchmark/README.md).

A separate normal-loading protocol completed 17 development checks: 11 passes and 6 failures. Mass transfer and settling remain distinct from matching static stiffness. [Response fitting and retained failures](demos/contact-benchmark/NORMAL_RESPONSE.md).

Apple SDF grasping is registered and stepped through **UniLab**, with native scenes owned by DexLab. PhysX rigid-body qualifications use **UniSim's Isaac Sim backend**; the separate cloth task reuses its runtime discovery. Rigid and cloth experiments have separate scores; incomplete and unsupported capabilities remain explicit.

PhysX native surface cloth adds **15 frozen held-out cases: 10 passes, one surface-crossing failure and four unsupported force-extension cases**. Eight of nine development refinement runs pass; repeat and refined-mesh failures are retained. [Results, GIF and raw evidence](demos/physx-contact/cloth.md)

A further 12 predeclared contact-transient experiments retain six combined passes and six failures. Timestep refinement separates contact-law mismatch from numerical error, including tensile-release failures. [Parameters, curves and reproduction](demos/contact-benchmark/TRANSIENT_RESPONSE.md).

## Grasp details

- The right thumb and index finger pinch the stem; the left arm stays parked. The apple and stem form **one free 0.2 kg rigid body**.
- The apple and both fingertip pads use **SDF collision geometry**. There are no attachment constraints, direct object position drives, or engine source patches.
- Control uses **known object poses, inverse kinematics, and scripted joint targets**. This is not a visual policy or a learned skill; no model API key is needed.
- Engines are tuned separately. MuJoCo uses SDF contact search and soft constraints at **0.5 ms**; SuperDex uses surface integration and smooth penalty energy at **2 ms**; PhysX uses native SDF contact and TGS at **1 ms**, with an explicit torsional patch radius. Shared source surfaces do not imply identical discrete geometry or contact laws.

Independent checks cover clearance, two-finger support, penetration, wrist-relative motion, and momentum balance during a continuous three-second hold. Fruit-body contact is allowed during approach. The GIFs show the default scene; stem bending, fracture and hardware accuracy are not validated.

[MuJoCo acceptance](demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex acceptance](demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [Parameters and engine internals](docs/sdf-backends.md)

## Results

Apple-stem grasping completed **10 frozen paired cases: 20 episodes across both backends**. Mass, horizontal position and yaw were perturbed without retuning the released policies on these cases.

| Configuration | Passed full acceptance | Success rate, 95% Wilson interval |
|---|---:|---:|
| MuJoCo 3.11.0, 0.5 ms | 1 / 10 | 1.8–40.4% |
| SuperDex 1.0.0 FP64, 2 ms | 10 / 10 | 72.2–100% |

These measure separately configured task robustness, **not engine accuracy**. All failures and raw evidence are retained. Six additional timestep episodes completed; MuJoCo at 0.25 ms failed the penetration limit, so refinement did not improve acceptance monotonically. A separate 100-case test set is frozen but has not completed evaluation.

PhysX currently passes one development grasp scene and is not included in that held-out evaluation. Native separation and independent reference-surface penetration are reported separately. [Parameters, failures and measurement scope](demos/physx-contact/apple.md)

[Protocol, all results and reproduction](docs/benchmark.md) · [Default demo measurements](docs/sdf-backends.md#results-and-limits) · [Diagnostic definitions](docs/jitter.md)

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

Thanks to [UniLab](https://github.com/unilabsim/UniLab), [Project SuperDex](https://github.com/unilabsim/project_superdex), [MuJoCo](https://github.com/google-deepmind/mujoco), [Newton](https://github.com/newton-physics/newton), [OpenArm](https://github.com/enactic/openarm), and [Wuji](https://github.com/wuji-technology). The SuperDex grasp appears in [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex); Astra assisted development and debugging.

Code: [Apache-2.0](LICENSE). Third-party assets retain their own terms; see [asset sources](docs/ASSETS.md).
