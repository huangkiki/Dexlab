# Task, parameter and evidence inventory (D01)

[English](README.md) | [简体中文](README.zh-CN.md)

**Conclusion: current evidence supports contact experiments under specific configurations, not real-material accuracy or an overall engine ranking.** Geometry review invalidated the old cloth-grasp success claim; grasp, cloth and contact protocols cannot be pooled.

Audit date: 2026-09-30; source baseline [8be5d6a](https://github.com/huangkiki/Dexlab/tree/8be5d6a7aacfaa4d762ff17a78f6af28553adc72) (v0.15.0). This slice inventories existing work without changing models, controllers, thresholds or engines. [Pinned upstream task cards](upstream.md) are source reviews, not DexLab reproductions.

## Execution paths

Commands run from the repository root; `python` means this checkout’s `.venv/bin/python`, and `OUT` must be new. Follow [installation](../installation.md) for optional backends; `MJ_RECORD` is a complete MuJoCo apple recording. Entry points were audited, not all rerun during this inventory. Engine names are `mujoco/superdex/physx`; linked pages specify SDK, GPU and asset requirements.

| ID / task | Source/config | Entry point | Scene / engine / geometry | Control and observations | Independent scoring and limits |
|---|---|---|---|---|---|
| A1 — Apple-stem SDF grasp | [apple_stem](../../src/dexlab/tasks/apple_stem.py) · [protocol](../../docs/sdf-backends.md) | `bash demos/apple-stem-grasp/run.sh --backend mujoco --headless` (`superdex`) | DexLab native scenes; MuJoCo / SuperDex FP64; rigid apple and SDF pads | Known-pose planning, absolute joint targets; actual joints, object poses, per-step contact forces | `verify_sdf_grasp.py RECORD`; hold, support, penetration, momentum, wrist-relative motion |
| A2 — Apple scene/timestep regression | [benchmark](../../src/dexlab/benchmark.py) · [suite](../../benchmarks/apple-stem-v1.json) | `python -m dexlab.benchmark run --split regression --output OUT` | Reuses A1; frozen mass, translation, yaw; separately fixed backend parameters | Batch calls A1; no new controller | A1 per-episode scoring; `benchmark report` separately checks integrity, not physics |
| A3 — PhysX apple stem | [physx_apple](../../src/dexlab/physx_apple.py) · [run](../../demos/physx-contact/apple.md) | `python -m dexlab.physx_apple --source-run MJ_RECORD --output OUT` | DexLab scene description → UniSim IsaacSimBackend → SDK; native SDF/TGS | Transferred model, scripted joint targets; object/link poses, native contact ledger | `physx_geometry.py` + `physx_apple_score`; sampled surface bound reported separately |
| C1 — Robot frictional cloth grasp | [scene](../../demos/cloth-folding/src/cloth_model.py) · [audit](../../demos/cloth-folding/SCORING.md) | `bash demos/cloth-folding/run.sh --no-video --robot-model MJ_RECORD/model.xml --output OUT` | DexLab builds MuJoCo flex directly; no attachment constraint | Scripted joint targets; joints, cloth vertices, online contact summaries, 25 Hz replay | `verify_cloth.py RECORD --output NEW.json`; historical recording returns geometry-review status 2 |
| C2 — Basic cloth: extension, sag, drape, folded drop | [cloth_benchmark](../../src/dexlab/cloth_benchmark.py) · [cloth-v1](../../benchmarks/cloth-v1.json) · [self-contact](../../benchmarks/cloth-self-contact-v1.json) | `python -m dexlab.cloth_benchmark run --solver mujoco --case dev-sag --output OUT` | DexLab native scenes; MuJoCo flex, SuperDex shell, five Newton solver paths | Prescribed nodal forces or free evolution; node positions/velocities; SuperDex velocity is differenced | `cloth_benchmark verify RECORD`; pins, strain, obstacle surfaces, crossings, native warnings |
| C3 — PhysX surface cloth | [physx_cloth](../../src/dexlab/physx_cloth.py) · [worker](../../src/dexlab/physx_cloth_worker.py) · [details](../../demos/physx-contact/cloth.md) | C2 + `--solver physx-surface --device cuda:0 --iterations 16` | DexLab custom SDK worker; UniSim runtime discovery; native surface deformable | Nodal state readback; external nodal-force API unsupported, no substituted extension pass | Reuses C2 scorer; CPU unsupported; not a UniSim built-in cloth backend |
| R1 — Plane sliding | [contact_plane_native](../../src/dexlab/contact_plane_native.py) · [case](../../demos/contact-benchmark/cases/dev-slide.json) | `python -m dexlab.contact_plane_native --engine mujoco --case demos/contact-benchmark/cases/dev-slide.json --output OUT` | DexLab box/plane; direct native MJ/SD, PhysX via UniSim worker | One initial velocity after settling, then unactuated; poses, velocities, forces | Same module `--verify RECORD`; deceleration, momentum, penetration, orientation |
| R2 — Indentation/unloading | [contact_indent_run](../../src/dexlab/contact_indent_run.py) · [case](../../demos/contact-benchmark/cases/dev-indent.json) | `python -m dexlab.contact_indent_run --engine superdex --case demos/contact-benchmark/cases/dev-indent.json --output OUT` | Same ownership as R1; rigid contact response, not soft-tissue deformation | World-frame COM force; actual displacement, contact force, post-release gap | Same module `--verify RECORD`; loading, penetration, release |
| R3 — Two-pad cylinder load | [contact_pinch_run](../../src/dexlab/contact_pinch_run.py) · [case](../../demos/contact-benchmark/cases/dev-cylinder-overload.json) | `python -m dexlab.contact_pinch_run --engine physx --case demos/contact-benchmark/cases/dev-cylinder-overload.json --output OUT` | 64-sided prism cylinder + box pads; not SDF; same ownership as R1 | Frozen COM-force protocol; poses, velocities, native contact-point forces, reference overlap | Same module `--verify RECORD`; hold/overload/frictionless/release; independent SAT geometry |
| R4 — Static and transient response | [runner](../../demos/contact-benchmark/normal_response.py) · [static](../../benchmarks/contact-normal-v1.json) · [transient](../../benchmarks/contact-transient-v1.json) | `python demos/contact-benchmark/normal_response.py run OUT --suite benchmarks/contact-normal-v1.json` (or `contact-transient-v1.json`) | Reuses R2; synthetic 20 kN/m target; transient target additionally specifies 40 N·s/m | Piecewise loads, mass/timestep transfer; indentation and response time series | `normal_response.py verify RECORD`; exit 0 means all historical outcomes reproduced, including failures |
| P1 — PhysX rest/slide qualification | [physx_baseline](../../src/dexlab/physx_baseline.py) · [details](../../demos/physx-contact/README.md) | `python -m dexlab.physx_baseline run --case rest --output OUT` (`slide`, `slide-frictionless`) | DexLab description → UniSim IsaacSimBackend; box/ground | Free evolution after initialization; rigid states, mass/inertia/material readback | Same module `verify RECORD`; basic protocol, not a grasp substitute |
| P2 — PhysX legacy box pinch | [physx_pinch](../../src/dexlab/physx_pinch.py) · [protocol](../../demos/physx-contact/pinch.md) | `python -m dexlab.physx_pinch run --case hold --output OUT` (`overload`, `frictionless`) | UniSim worker; box object, prismatic pads; distinct from R3 cylinder | Limited drives, load/friction controls; object motion, support | Same module `verify RECORD`; preserves original failures and adapter fixes |
| P3 — PhysX drives and robot transfer | [drive](../../src/dexlab/physx_drive.py) · [robot](../../src/dexlab/physx_robot.py) · [transfer](../../src/dexlab/robot_transfer.py) | `python -m dexlab.physx_drive run --force-timing substep --output OUT`; `python -m dexlab.physx_robot run --source-run MJ_RECORD --output OUT` | UniSim worker; loaded 1-D drive / inherited 54-joint model | Targets and force timing; actual joint/link states, native drive readback | Each module `verify RECORD`; tracking, model/FK consistency; not hardware accuracy |
| P4 — PhysX SDF hole and contact ledger | [sdf](../../src/dexlab/physx_sdf.py) · [details](../../src/dexlab/physx_contact_details.py) | `python -m dexlab.physx_sdf run --case sdf-hole --output OUT`; `python -m dexlab.physx_contact_details run --output OUT` | UniSim worker; torus/sphere SDF vs convex control; separate slider | Gravity/initial velocity; poses, normal/tangential contact forces | Each module `verify RECORD`; hole geometry, momentum ledger; not a complete grasp |
| L1 — Historical SuperDex grasp path | [wuji_stem_grasp](../../demos/apple-stem-grasp/src/wuji_stem_grasp.py) · [legacy scorer](../../demos/apple-stem-grasp/src/verify_wuji_sequence.py) | `python demos/apple-stem-grasp/src/wuji_stem_grasp.py --help`; historical scoring: `python demos/apple-stem-grasp/src/verify_wuji_sequence.py demos/apple-stem-grasp/evidence` | Retained native SuperDex script; not the current A1 SDF protocol | Known state, IK, finger synergy prior; historical trajectories | Historical criteria; excluded from new-protocol success rates |

Rendering/video, `model_audit`, `jitter`, `cloth_report` and archive tools display or diagnose these records; they are not additional physical tasks. Geometry audits use recorded state and remain limited by models, spatial sampling and temporal coverage. [Model audit](../model-audit.md) · [Jitter](../jitter.md) · [Archive protocol](../remote-research.md).

## Actual UniLab reuse

[Registry modules](../../src/dexlab/tasks/__init__.py) declare five task IDs with single-scene stepping; registration does not unify contact laws.

| ID | Native path / data contract |
|---|---|
| `DexLab-AppleStem-v0` | MJ/SD; actual joints + privileged apple pose + time; absolute joint targets. |
| `DexLab-Cloth-v0` | MJ/SD/Newton/isaacsim; nodal state and prescribed forces; PhysX force limitation in C3. |
| `DexLab-ContactPlane-v0` | MJ/SD/PhysX; empty `(1,0)` action, free evolution after initial velocity. |
| `DexLab-ContactIndent-v0` | MJ/SD/PhysX; protocol-constrained world COM force. |
| `DexLab-ContactCylinder-v0` | MJ/SD/PhysX; 40-D state, prescribed `(1,3,3)` forces; actions must match frozen protocol. |

PhysX is the engine name in this table; the exact UniLab `sim_backend` key is `isaacsim`. The existing SuperDex apple normal-force column is a placeholder and cannot estimate normal load or friction margin; other recorded contact quantities retain their scorer-specific meaning.

These interfaces return placeholder zero rewards; no policy is trained. DexLab native code owns MuJoCo/SuperDex apple scenes. PhysX rigid paths actually use UniSim scene contracts and workers; cloth reuses runtime discovery only. Versions are UniLab 1.3.3 / UniSim 1.7.10. The [disclosed adapter patch](../../scripts/patches/unisim-1.7.10-physx-adapter.patch) does not modify official engine source. Further unification requires [#4](https://github.com/huangkiki/Dexlab/issues/4), not inference from registration success.

## Parameter provenance ledger

| Class | Current fact / approximation | Source |
|---|---|---|
| Measured | No formal hardware calibration dataset. Dual UR7e arms and two identical CTAG2F90D grippers are user-confirmed hardware identities, not error measurements. | [hardware #6](https://github.com/huangkiki/Dexlab/issues/6) |
| Inherited | OpenArm/Wuji geometry, joint frames and inertials come from prefabs; conversion consistency does not establish hardware fidelity. | [assets](../ASSETS.md) · [model audit](../model-audit.md) |
| Assumed / geometrically derived | Apple 0.2 kg, rigid stem; R3 radius 10 mm, half-height 30 mm, 64-sided prism, maximum radial error about 12.05 µm; homogeneous mass assumptions. | [SDF](../sdf-backends.md) · [contact](../../demos/contact-benchmark/README.md) |
| Tuned / numerical choices | Default grasp μ: MJ 1.0, SD 0.5, PhysX 1.0; dt: 0.5/2/1 ms; separately configured SDF discretization, solvers, drives and alignment offsets. | [MJ/SD](../sdf-backends.md) · [PhysX](../../demos/physx-contact/apple.md) |
| Synthetic-target fitting | R4 targets of 20 kN/m static stiffness and 40 N·s/m transient damping are engineering designs; fitting at 2/6 N and checking 4 N is not measured-material identification. | [normal](../../benchmarks/contact-normal-v1.json) · [transient](../../benchmarks/contact-transient-v1.json) |
| Nominal cloth parameters | Area mass, mesh, pins, thickness/contact radii and stiffness are declared in suites/builders; equal stiffness labels across solvers do not define equal materials. | [suite](../../benchmarks/cloth-v1.json) · [builders](../../src/dexlab/cloth_engines.py) · [shell](../../src/dexlab/cloth_superdex.py) |
| Unknown / uncovered | Real pad/stem friction and compliance, fabric extension/bending curves, actuator bandwidth, persistent material-point slip, full energy balance and sensor errors lack complete data. | [methods](../research-focus.md) · [jitter](../jitter.md) |

## Evidence coverage and next steps

These are published historical outcomes, not all rerun in this slice. Denominators count different scenes/development configurations and cannot be pooled for ranking.

| Path | Existing outcome | Interpretation and gap |
|---|---|---|
| A1/A2 | MJ 1/10, SD 10/10; six additional timestep experiments | [failures and intervals](../benchmark.md); 100-scene formal evaluation incomplete |
| A3 | One PhysX development scene passes | [record](../../demos/physx-contact/apple.md); no held-out result |
| C1 | Legacy protocol passes; table intrusion in 176/225 frames, maximum interior depth 3 mm | [D02](../../demos/cloth-folding/SCORING.md); not native or vertical penetration; robot-surface and interframe coverage remain incomplete |
| C2 | 7 configurations × 15 held-out cases: 52/105 pass, 53 fail | [records](../../demos/cloth-benchmark/README.md); not real-fabric error |
| C3 | 15 held-out: 10 pass, 1 fail, 4 unsupported; 8/9 separate refinements pass | [records](../../demos/physx-contact/cloth.md); unsupported is distinct from failure or success |
| R1–R3 | 38 development configurations: 25 pass, 13 fail | [original and refined](../../demos/contact-benchmark/README.md); not a random success rate |
| R4 | Static 11/17; transient 6/12 pass both check classes | [static](../../demos/contact-benchmark/NORMAL_RESPONSE.md) · [transient](../../demos/contact-benchmark/TRANSIENT_RESPONSE.md); synthetic response targets |

**Recommended sequence:** repair cloth physics and coverage under existing [#32](https://github.com/huangkiki/Dexlab/issues/32); unify metric definitions and historical rescoring in [#31](https://github.com/huangkiki/Dexlab/issues/31); prepare the hardware measurement protocol in [#33](https://github.com/huangkiki/Dexlab/issues/33). Cards separate contact mode, control, observations and physical checks: isolate error in minimal contact fixtures before testing transfer to manipulation. No duplicate tasks or claim of implemented upstream examples is introduced here.

There is no unified isolated speed ranking; some recorded times include logging, IPC or concurrent workloads. Formal timing windows must exclude archival, transfer and hashing. This report does not establish visual closed-loop control, tactile material identification or real UR7e/gripper calibration.

[Homepage](../../README.en.md)
