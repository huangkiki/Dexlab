# Engines, solvers and modeling assumptions

Matching visual meshes, parameter names or joint targets does not establish matching physical problems.

## Historical apple configurations

| Item | MuJoCo | SuperDex FP64 | PhysX |
|---|---|---|---|
| Contact path | SDF contact search and soft constraints | Surface-sampling integration and smooth penalty energy | Native SDF contacts and TGS |
| Physics step | 0.5 ms | 2 ms | 1 ms |
| Key approximations | SDF discretization and contact-point search | Surface density and smooth penalty response | SDF resolution, discrete contacts and torsional radius |
| Evidence scope | Default case and historical ten-scene cohort separate | Default case and historical ten-scene cohort separate | One development grasp, outside that held-out cohort |

Record collision geometry, contact law, integrator, constraint solver and drives separately. SDF defines geometry, not friction behavior or penetration accuracy. A smaller timestep need not improve every metric monotonically.

[Parameter provenance and implementation](https://github.com/huangkiki/Dexlab/blob/main/docs/sdf-backends.md) · [Contact/material research](https://github.com/huangkiki/Dexlab/blob/main/docs/research-focus.md)

## Latest-stable qualification

Before each new batch, qualify the latest stable native path or an officially compatible framework combination. Record core, binding and framework versions, hashes, precision and compute path separately; freeze throughout the batch. An older bundled core is not itself a blocker. Attribution experiments additionally match core versions; unmatched versions cannot isolate a framework effect.

Release leads checked on 2026-10-04: [MuJoCo 3.14.0](https://github.com/google-deepmind/mujoco/releases/tag/3.14.0), [Genesis 1.4.3](https://github.com/Genesis-Embodied-AI/genesis-world/releases/tag/v1.4.3), [Newton 1.6.0](https://github.com/newton-physics/newton/releases/tag/v1.6.0). This dated inventory alone does not establish task qualification. MuJoCo 3.14.0 now has the scoped cloth and friction development results in the [results report](results.md); newer native incline cohorts are listed below and remain separate from those historical tasks.

The qualified Newton 1.6.1 package declares `mujoco~=3.12.0` and `mujoco-warp~=3.12.0` for its `sim` extra; ovphysx 0.6.3 is classified Alpha. Stable bindings, embedded cores and standalone SDKs need separate checks. [Version task #41](https://github.com/huangkiki/Dexlab/issues/41)

## Genesis scope

Qualify rigid support, sliding and pinch/release first, then PBD thin cloth and coupling separately. MPM/FEM volume materials are distinct. Genesis's Newton method is not Newton Physics. Unsupported SDF-SDF must not become an undisclosed convex surrogate. [Qualification #42](https://github.com/huangkiki/Dexlab/issues/42)

## GPU contact development evidence

Six-device parameter checks on MuJoCo Warp 3.14.0 produced four passing and two failing configurations. The fixed 5 mm intrusion bound was unchanged; smaller timesteps did not monotonically improve penetration. This is a synthetic sphere/plane diagnostic, not apple or cloth qualification. [Full results, plots and reproducible records](https://github.com/huangkiki/Dexlab/blob/main/docs/engine-qualification.md).


## Synthetic tactile observation

Box/fixed-slab geometric occupancy is supported on the MuJoCo fixture; shear memory, optical rendering and hardware calibration are not. See all three batches and failed controls in the [report](https://github.com/huangkiki/Dexlab/blob/main/docs/synthetic-tactile.md).

## Two-track admission and Drake results

The 2026-10-09 coverage plan uses the two admission tracks above. Native Drake 1.57.0 now records SAP / kLagged / hydroelastic incline results: six passes, three failures. Applicable kSap, kSimilar and other profiles remain unrun. [报告 / Report](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.md).

## Native incline cohorts

The [coverage matrix](index.md) retains the initial cohorts separately. [Genesis 1.4.3](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) records five native CPU configurations. [Newton 1.6.1 / Warp 1.18.0](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) records seven: XPBD and Kamino PADMM pass 1/9 positives each, DVI passes 4/9, and the remaining profiles pass none. The 49 invalid positives, two invalid VBD negatives and interrupted DVI attempt remain visible. An explicit continuation completes only the missing negative. These fixed configurations do not establish reliable coverage-v1 credit, equal tuning or an engine ranking.
