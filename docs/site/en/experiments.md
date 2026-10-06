# Experiment catalog

Keep existing code paths to preserve asset references, reproduction commands and historical evidence. Each experiment connects a question, configuration, raw record, independent score, report and failures.

| Experiment | Code | Question and status |
|---|---|---|
| Apple stem grasp | [demos/apple-stem-grasp/](https://github.com/huangkiki/Dexlab/tree/main/demos/apple-stem-grasp/) | OpenArm + Wuji SDF-SDF frictional holding; distinguish default cases and historical perturbations |
| Robot cloth grasp | [demos/cloth-folding/](https://github.com/huangkiki/Dexlab/tree/main/demos/cloth-folding/) | Pinch, lift and release; historical intersections retained; one repaired 9 s development case passes, robustness untested |
| Contact and drives | [demos/contact-benchmark/](https://github.com/huangkiki/Dexlab/tree/main/demos/contact-benchmark/) | Sliding, loading/unloading and transients; synthetic response is not hardware calibration |
| Basic cloth | [demos/cloth-benchmark/](https://github.com/huangkiki/Dexlab/tree/main/demos/cloth-benchmark/) | Stretch, drape, collision and falling folds; separate material/solver capabilities |
| PhysX | [demos/physx-contact/](https://github.com/huangkiki/Dexlab/tree/main/demos/physx-contact/) | Native rigid bodies, SDFs, joints and surface cloth; one success does not establish held-out performance |
| Genesis | [#42](https://github.com/huangkiki/Dexlab/issues/42) | Scoped rigid evidence in #42; [PBD cloth diagnostics](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.md) retain failed momentum/grasp checks; tested frictional grasp profile rejected; equal-time response, connected folds and two held-out offsets recorded |

`src/dexlab/` contains shared task registration, scoring and recording. `scripts/` contains setup, rescoring, documentation and research tools. Share code only for real duplication or invariants; this is not a new general simulation framework.

## Apple control and dynamics

The right thumb/index pinch the stem while the left arm remains parked. Apple and stem form a 0.2 kg free rigid body. Known poses, IK and fixed joint targets drive the robot; the engine integrates actual object motion without attachment or object-position actuation. The continuous hold window is 11–14 s, with fruit contact allowed during approach.

The display camera follows recorded apple poses for playback only. There is no validated visual controller, stem fracture or hardware accuracy claim.

[Implementation and parameters](https://github.com/huangkiki/Dexlab/blob/main/docs/sdf-backends.md) · [Full inventory](https://github.com/huangkiki/Dexlab/blob/main/docs/inventory/README.md)

## Continuous close-up records

These are development-scene replays at the original pinned versions, not held-out success rates. The cloth recording preserves the detected table-intersection failure.

::::{grid} 1 1 2 2
:gutter: 3
:::{grid-item-card} MuJoCo
![MuJoCo](../../../demos/apple-stem-grasp/media/mujoco-sdf.gif)
:::
:::{grid-item-card} SuperDex FP64
![SuperDex FP64](../../../demos/apple-stem-grasp/media/superdex-sdf.gif)
:::
:::{grid-item-card} PhysX
![PhysX](../../../demos/physx-contact/media/physx-sdf.gif)
:::
:::{grid-item-card} Cloth: geometric failure
![Cloth: geometric failure](../../../demos/cloth-folding/media/grasp.gif)
:::
::::

## Hardware acquisition preparation

The [protocol, empty template and log validator](https://github.com/huangkiki/Dexlab/blob/main/docs/hardware/README.md) cover two UR7e arms and two identical CTAG2F90D grippers. Commands, measured feedback and independent references remain separate; unknown data stays unknown. The tool only reads files and does not control hardware. Format validity does not establish calibration.

## Friction response development

The [16-run planar report](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/FRICTION_RESPONSE.md) retains all paired MuJoCo 3.14.0 / SuperDex FP64 outcomes, measured initial states, speed-bin force ratios and costs. Every run passes existing plane checks, while low-speed resistance differs. This is not matched material calibration or an engine-accuracy ranking.

## Repaired cloth development case

![Continuous repaired pinch, lift and release](../../../demos/cloth-folding/media/compliance-grasp.gif)

One 9 s candidate passes the fixed v3 criteria; self penetration remains close to its limit. [Metrics, failed controls, video provenance and exact command](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SETTLING.md). This does not replace the historical failure above or establish robustness.
