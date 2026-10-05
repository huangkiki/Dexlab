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

Before each new batch, resolve official latest stable core, solver, bindings and wrappers. Record loaded versions, hashes, precision and compute path; freeze throughout the batch. Exclude alpha/beta/RC/dev, yanked packages and experimental solver options from the primary comparison. Block incompatible combinations rather than silently downgrading.

Release leads checked on 2026-10-04: [MuJoCo 3.14.0](https://github.com/google-deepmind/mujoco/releases/tag/3.14.0), [Genesis 1.4.3](https://github.com/Genesis-Embodied-AI/genesis-world/releases/tag/v1.4.3), [Newton 1.6.0](https://github.com/newton-physics/newton/releases/tag/v1.6.0). This dated inventory alone does not establish task qualification. MuJoCo 3.14.0 now has the scoped cloth and friction development results in the [results report](results.md); Genesis and Newton qualification remain separate.

Newton's MuJoCo extra still restricts the core to 3.12.x; ovphysx 0.6.3 is classified Alpha. Stable bindings, embedded cores and standalone SDKs need separate checks. [Version task #41](https://github.com/huangkiki/Dexlab/issues/41)

## Genesis scope

Qualify rigid support, sliding and pinch/release first, then PBD thin cloth and coupling separately. MPM/FEM volume materials are distinct. Genesis's Newton method is not Newton Physics. Unsupported SDF-SDF must not become an undisclosed convex surrogate. [Qualification #42](https://github.com/huangkiki/Dexlab/issues/42)

## GPU contact development evidence

Six-device parameter checks on MuJoCo Warp 3.14.0 produced four passing and two failing configurations. The fixed 5 mm intrusion bound was unchanged; smaller timesteps did not monotonically improve penetration. This is a synthetic sphere/plane diagnostic, not apple or cloth qualification. [Full results, plots and reproducible records](https://github.com/huangkiki/Dexlab/blob/main/docs/engine-qualification.md).
