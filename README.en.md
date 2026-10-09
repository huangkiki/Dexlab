# DexLab

**DexLab investigates how contact and friction shape robotic grasping, using reproducible experiments grounded in established physical laws and empirical relations to assess the reliability of physics simulation.**

We use inclined-plane friction, one-dimensional collisions and pinch experiments to examine simulated forces, motion and contact against analytical solutions, conservation laws and sourced empirical relations. This repository provides **findings, reproducible code and raw data** to investigate measurable factors that affect grasping performance and identify the conditions under which each conclusion applies.

[简体中文](README.md) · [Documentation (中文)](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [Experiment reports](docs/site/en/results.md) · [Installation](docs/installation.md) · [Releases and data](https://github.com/huangkiki/Dexlab/releases)

The documentation site updates on every merge to main, with findings, matched comparisons and six-engine coverage on the homepage.

## What tasks can I run?

Choose a task entry point, then use its documented protocol, environment and results. This table describes **implementations with retained DexLab evidence**. “Executed” includes failures; a pass applies only to the reported version, configuration and cases.

| Task | Implemented engines and validation | Run and evidence entry points |
|---|---|---|
| Inclined-plane friction and one-dimensional impact | MuJoCo / SuperDex have paired incline cases, including failures; MuJoCo has recorded impact experiments | [Incline comparison](docs/incline-comparison-results.md) · [Impact](docs/elastic-impact-results.md) |
| Plane sliding, normal loading / unloading, and cylinder pinch | MuJoCo / SuperDex / PhysX development cases executed, retaining failures and geometry refinement | [Contact experiments and commands](demos/contact-benchmark/README.md) |
| Finite-fixture pinch, lift, hold and release | Genesis completed 16 force-limit cases for studying drive limits and failure mechanisms | [Force-limit results and reproduction](docs/force-limit-results.md) |
| Robot SDF apple-stem grasp | MuJoCo / SuperDex passed the specified 14 s scene; PhysX has separate single-scene acceptance with its own configuration and preparation chain | [MuJoCo / SuperDex](demos/apple-stem-grasp/README.md) · [PhysX](demos/physx-contact/apple.md) |
| Cloth extension, sag, sphere draping and pre-folded drop | MuJoCo flex / SuperDex shell / Newton Physics have historical experiments, including failures; PhysX surface cloth has separate passive cases, without per-node-force extension support | [Cloth benchmark](demos/cloth-benchmark/README.md) · [PhysX scope](demos/physx-contact/cloth.md) |
| Robot cloth grasp, lift and release | One specified 9 s MuJoCo 3.14 development case passed the limited protocol; self-contact is near the threshold and robustness remains unproven | [Passing configuration, failures and commands](demos/cloth-folding/SETTLING.md) |
| Basic rigid sphere–plane contact | Newton Physics 1.6.1 / XPBD normal, repeat and collision-disabled controls passed admission; robot grasping is outside this test | [Protocol, records and verification](docs/newton-contact.md) |

Two-hand cloth folding has no demonstrated success. Drake 1.57.0 passes six of nine initial incline cases; all three sliding cases fail and the negative is correctly rejected. [Full records](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.md). [#143](https://github.com/huangkiki/Dexlab/issues/143) verifies adapter correspondence; the full research campaign remains [#130](https://github.com/huangkiki/Dexlab/issues/130).

**Our assessment standard: a better engine should reliably cover more types of tasks.** We assess task types alongside physical credibility, stability across conditions and execution cost. Reliably completing more task types under retained criteria expands a configuration's validated scope. Installation, adapter declarations, multiple solvers for one task and repeated runs do not add task types; pass counts from different historical protocols do not form a universal ranking.

## Task coverage by solver

MuJoCo 3.15.0 initial six-profile qualification: elliptic 3/9 each, pyramidal 0/9 each; all six negatives rejected. CG/Newton pyramidal each retain three invalid force/state records. [详细证据 / Evidence](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md).

Across twelve SuperDex 1.0.0 FP64 incline profiles, nine pass 8/9 and three CG paths pass 6/9; all negatives are rejected, and five CUDA options are unsupported in the official build. Failures and historical gaps remain explicit. [Evidence / 详细证据](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md).

<!-- task-coverage:start -->

States: passed / partial / failed / not run / blocked / unsupported. Cells link to evidence or recovery conditions.

**Historical protocols remain separate; a pass applies only to its protocol.** Reliable coverage under the new protocol requires positive and negative cases, independent physics scoring, frozen holdouts and equal tuning budgets.

### Rigid tasks · historical protocols

| Core / solver / path / version / cohort | Basic contact | Incline | Collision | Fixture pinch | Robot grasp |
| --- | --- | --- | --- | --- | --- |
| **MuJoCo · Newton / Euler**<br>native · 3.15.0<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.md) | [Partial](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-stiffness-results.md) | [Partial](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-load-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · PGS / elliptic / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-pgs-elliptic-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · PGS / pyramidal / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-pgs-pyramidal-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Failed 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · CG / elliptic / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-cg-elliptic-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · CG / pyramidal / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-cg-pyramidal-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Failed 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · Newton / elliptic / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-newton-elliptic-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · Newton / pyramidal / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-newton-pyramidal-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Failed 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · Newton / AUTO / FP64**<br>native · 1.0.0<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / approximate_implicitfast**<br>native CPU FP64 · 1.4.3<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Passed](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / approximate_implicitfast**<br>UniSim 1.7.12 + disclosed local patch · 1.4.3<br>genesis-contact-migration-v4 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial](https://github.com/huangkiki/Dexlab/blob/main/docs/unisim-contact-migration.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · XPBD**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>rigid-history | [Passed](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-contact.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **PhysX · historical readback incomplete (#126)**<br>SDK historical · historical core identity unrecovered (#126)<br>rigid-history | [Partial](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · SAP / kLagged / hydroelastic**<br>native CPU FP64 · 1.57.0<br>drake-incline-qualification-v2 | [Not run](https://github.com/huangkiki/Dexlab/issues/151) | [Partial 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/151) | [Not run](https://github.com/huangkiki/Dexlab/issues/151) | [Not run](https://github.com/huangkiki/Dexlab/issues/151) |
| **MuJoCo · Newton / implicitfast**<br>native · 3.11.0<br>apple-sdf-14s | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Passed](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) |
| **SuperDex · Newton / GMRES / FP64**<br>native · 1.0.0<br>apple-sdf-14s | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Passed](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) |
| **SuperDex · NEWTON / AUTO / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-auto-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-cg-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / GMRES / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-gmres-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / AUGMENTED_CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-augmented-cg-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / LDLT / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-ldlt-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / LU / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-lu-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / ASYNC_CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-async-cg-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / PARALLEL_CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-parallel-cg-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / MINRES / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-minres-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · BFGS / AUTO / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-bfgs-auto-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · SR1 / AUTO / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-sr1-auto-c1-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / AUTO / CINF_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-auto-cinf-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Partial 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / CUDA_CG / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Unsupported](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / CUDA_GMRES / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Unsupported](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / EXPERIMENTAL_CUDA_SPARSE_CHOLESKY / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Unsupported](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / EXPERIMENTAL_CUDA_SPARSE_LDLT / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Unsupported](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / EXPERIMENTAL_CUDA_SPARSE_LU / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Unsupported](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) | [Not run](https://github.com/huangkiki/Dexlab/issues/121) |

### Manipulation · historical protocols and gaps

| Core / solver / path / version / cohort | Pushing | In-hand rotation | Cloth grasp/lift | Active folding |
| --- | --- | --- | --- | --- |
| **MuJoCo · Newton / Euler**<br>native · 3.15.0<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/48) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **SuperDex · Newton / AUTO / FP64**<br>native · 1.0.0<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/48) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **Genesis · Newton / approximate_implicitfast**<br>native CPU FP64 · 1.4.3<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/48) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **Newton Physics · XPBD**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/48) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **PhysX · pending qualification**<br>ManiSkill / SAPIEN · official combination pending #47<br>rigid-history | [Blocked](https://github.com/huangkiki/Dexlab/issues/47) | [Blocked](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **Drake · SAP / kLagged / hydroelastic**<br>native CPU FP64 · 1.57.0<br>drake-incline-qualification-v2 | [Not run](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/48) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **MuJoCo · Newton / implicitfast**<br>native · 3.14.0<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/48) | [Passed](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SETTLING.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **Genesis · PBD / rigid coupling**<br>native CPU FP64 · 1.4.3<br>genesis-cloth-diagnostic | [Not run](https://github.com/huangkiki/Dexlab/issues/47) | [Not run](https://github.com/huangkiki/Dexlab/issues/48) | [Failed](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.md) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |

### Cloth tasks · separate historical protocols

| Core / solver / path / version / cohort | Extension | Sag | Sphere drape | Folded drop |
| --- | --- | --- | --- | --- |
| **MuJoCo · Newton**<br>native cpu float64 · 3.11.0<br>cloth-heldout-v1 | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **SuperDex · experimental-shell**<br>native cpu float64 · 1.0.0<br>cloth-heldout-v1 | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Partial 3/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · xpbd**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · vbd**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · semi_implicit**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · featherstone**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · style3d**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Passed 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Failed 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [Partial 1/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Genesis · PBD / rigid coupling**<br>native CPU FP64 · 1.4.3<br>genesis-cloth-diagnostic | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **Drake · not qualified**<br>native · not qualified<br>rigid-history | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) | [Not run](https://github.com/huangkiki/Dexlab/issues/28) |
| **PhysX · surface cloth**<br>Isaac Sim 5.1.0.0 / IsaacLab 0.47.2 · historical core identity unrecovered (#126)<br>physx-cloth-final-v2 | [Unsupported](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [Passed](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [Partial](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [Passed](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) |

**Reliable coverage under the new protocol: not yet qualified.** Existing capabilities remain valid within their original protocols; historical runs are not retroactively admitted.

Cloth counts are recomputed from 105 historical summaries, not rescored trajectories. Featherstone cloth uses semi-implicit particle kernels; folded drop is not active folding. Missing runs do not establish lack of support.

[Inventory and generation rules](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.md)

<!-- task-coverage:end -->

Genesis 1.4.3 PBD actuated cloth clamping/holding was run and failed; see the [retained negative results](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.md). Its plane support, stretch/bend response and connected-fold diagnostics are different from the seven-profile shared cloth holdout protocol.


The [coverage-first development plan](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.md) proceeds through migration discrepancies, independent engine baselines, native MJWarp/Isaac Sim comparisons, then pushing, rotation and cloth. The 594-case pinch study advances between newly delivered task types. Native paths use latest stable cores; frameworks use official compatible combinations, with matched-core attribution studied separately.

A 24-process native diagnostic isolated batched parameter storage as the low-force discrepancy factor. The subsequent storage-aligned comparison passed all 19 pairs and 12 exact reset replays across 38 launches / 56 episodes, at unchanged thresholds. The six earlier failed pairs and low-force grasp failures remain recorded. This result covers the disclosed Genesis 1.4.3 / local adapter patch combination and adds no task type. [Cause, evidence and reproduction](docs/unisim-contact-migration.md) · [#143](https://github.com/huangkiki/Dexlab/issues/143).

## Engines, solvers and versions

This table distinguishes **available evidence** from **matched-case comparisons**. Results from different tasks or versions do not form a single ranking. Versions are those actually used in the cited reports, not a claim about the latest release.

| Engine / runtime version | Solver and numerical configuration | Evidence scope |
|---|---|---|
| MuJoCo 3.15.0 | Newton solver; Euler integration; elliptic friction cone; 100 iterations maximum, tolerance 1e-10 | Nine paired incline cases below, plus collision and pinch diagnostics |
| SuperDex 1.0.0 FP64 | Same-byte reconstruction: Newton, linear AUTO (dense LDLᵀ on the small-system source path), C1-regularized friction; historical readback: Backward Euler, 100 iterations, absolute/relative tolerance 1e-9. [Evidence and historical telemetry gap #124](docs/superdex-solver-audit.md) | Nine paired incline cases below; [frozen configuration](docs/evidence/incline-comparison/manifest.json) |
| Genesis 1.4.3 CPU FP64 | Historical configuration: Newton / approximate_implicitfast / elliptic, noslip=0; [source resolution and historical effective-settings gap #125](docs/genesis-solver-audit.md) | [16 force-limit cases](docs/force-limit-results.md), not part of the paired incline cohort |
| Newton Physics 1.6.1 / Warp 1.18.0 | CPU SolverXPBD, float32; 4 iterations, dt=1 ms | [Sphere–plane and negative controls](docs/newton-contact.md), not a grasp comparison |
| PhysX (historical Isaac Sim 5.1; UniSim and direct SDK paths) | Three SDK controls read back PGS/TGS and force timing; surface cloth is separate. [Cohort audit and native-core identity gap #126](docs/physx-solver-audit.md) | [Historical contact experiments](demos/contact-benchmark/README.md); outside the paired cohort below |
| Drake | 1.57.0 / SAP / kLagged / hydroelastic / CPU FP64 | [Incline 6/9; sliding failures and negative retained](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.md) |

Historical audits [#124](https://github.com/huangkiki/Dexlab/issues/124), [#125](https://github.com/huangkiki/Dexlab/issues/125) and [#126](https://github.com/huangkiki/Dexlab/issues/126) complete bounded searches and attribution review: SuperDex same-byte reconstruction, Genesis matching-source derivation and three PhysX scene readbacks remain distinct. Missing telemetry stays missing; unsupported exact-core and algorithm-causality attribution is withdrawn. Engine qualification children carry new experiments with separate records; closing these audits adds no reliable task coverage.

Future evaluations must cover **MuJoCo, SuperDex, Genesis, Newton Physics, PhysX and Drake**, including applicable registered solver profiles. Every report lists the complete case matrix: passed, failed, blocked, unsupported or not run; missing cells link to Issues, and incomplete coverage is reported only as an interim result. Historical findings retain their original scope. ManiSkill/SAPIEN/Isaac Sim integration layers and the UniLab task layer are not extra physics engines; Newton Physics is also distinct from MuJoCo's Newton algorithm.

## Engine comparison: one cube, two fixed profiles

Official **MuJoCo 3.15.0** and **SuperDex 1.0.0 FP64**: the same 40 mm, 64 g cube, initial state and gravity; three timesteps (2/1/0.5 ms), 2 s per case. Published MuJoCo records are reused; nine SuperDex cases are new.

| Case | MuJoCo (impedance=0.9) | SuperDex (fixed penalty profile) |
|---|---|---|
| 15° static friction, μ=0.5 | **1.301–1.336 mm** drift; 0/3 pass | **0.708–1.132 mm** drift; 2/3 pass |
| 35° sliding, μ=0.5 | Rotation and intermittent support; 0/3 pass | Stable sliding in the scoring window; 3/3 pass |
| 15° nominal zero friction | Velocity RMSE **8.21×10⁻⁵ m/s**; 3/3 pass | Velocity RMSE **8.04×10⁻¹²–1.52×10⁻¹⁰ m/s**; 3/3 pass |

**Contact settings change drift and stability; engine names alone do not predict the outcome.** SuperDex meets more criteria under these fixed profiles, but its static drift increases with timestep refinement. Existing MuJoCo impedance=0.99 records drift only **0.141–0.179 mm**, less than these SuperDex results. The zero-friction difference also involves MuJoCo's native friction floor. Velocity errors use the 0.5–2 s window; the report retains initial transients, every failure and the conditions of the different contact models.

[Full comparison, parameters and raw data](docs/incline-comparison-results.md). These counts describe fixed-case tolerance checks, not real-material accuracy or a universal engine ranking.

## What we have learned

### 1. Correct post-impact velocity does not establish an accurate collision process

In one-dimensional elastic-impact experiments with official MuJoCo 3.15.0, all 18 cases passed the final-state criteria while contact overlap reached **5–20 mm**. After varying stiffness and timestep, **24 of 27 cases passed the final-state criteria, but only 2 also met the predefined 1 mm overlap budget**. Collision evaluation therefore needs velocity, energy and contact history together.

[Elastic-impact results](docs/elastic-impact-results.md) · [Stiffness and penetration](docs/impact-stiffness-results.md) · [Discrete contact explanation](docs/impact-discrete-results.md)

### 2. A more accurate solve does not necessarily produce a steadier grasp

In the MuJoCo 3.15.0 standard-block pinch diagnostic, tighter solver tolerances substantially reduced the residual between force and motion records, yet the block still slipped about **2 mm during one second of loading**. Numerical force balance and object retention are separate outcomes that need separate measurements.

[Pinch load and slip](docs/pinch-load-results.md) · [Six-case residual diagnostic](docs/pinch-impulse-results.md)

### 3. Gripper force limits change grasp outcomes

Across 16 cases in the fixed Genesis standard-block fixture, **0.2/0.4 N limits failed retention, while 0.8/10 N held and released the object**. The result persisted at ±2 mm initial offsets, establishing a reproducible boundary for this fixture.

[Every case, failure and raw record](docs/force-limit-results.md)

![Standard-block closing, lifting and release](demos/contact-benchmark/media/genesis-pinch.gif)

*Continuous close-up replay of measured Genesis states, displayed by MuJoCo. This illustrates one fixed configuration; the report contains every force-limit case.*

### 4. Contact parameters tuned for one scene are not general material parameters

Transferring three fixed contact configurations across ten mass/size combinations produced **30 runs that all missed the combined target for a prescribed synthetic dynamic response**. These parameter mappings have limited applicability and need checks across loads and sizes.

[Parameter-transfer experiment and all outcomes](demos/contact-benchmark/TRANSFER.md)

Each finding applies to the engine version, model and conditions frozen in its report. These are analytical-model and numerical-experiment findings; real-material accuracy requires measured references. The results cannot be pooled into an engine ranking.

## Next: unified-drive pinch boundary

[Development roadmap](docs/pinch-boundary-roadmap.md) · [Discussion](https://github.com/huangkiki/Dexlab/discussions/129) · [Research tracker](https://github.com/huangkiki/Dexlab/issues/130)

[Common protocol and data contract v1](docs/pinch-boundary-protocol.md) now defines the finite fixture, 1 ms external-PD clock, 594 formal cases, 24 controls and up to 32 qualification/bridge cases, with case expansion and record-shape checks. Backend qualification and independent scoring are next; no backend is admitted and no formal campaign has run. Six-engine gaps and historical evidence scope remain explicit.

## Learn the engines: Sim Atlas

The **[Sim Atlas learning home](https://github.com/huangkiki/sim-atlas)** provides the two-track map, shared foundations and six-engine navigation. Each engine has a separate learning repository, with application and principles/source tracks covering modeling, state and time, control, contact solvers, sensing, rendering, parallelism and extensions.

The [GitHub Projects tracker](https://github.com/users/huangkiki/projects/2) organizes all six repositories by engine, learning track and stage, with board and curriculum-table views.

[MuJoCo Atlas](https://github.com/huangkiki/mujoco-atlas) · [SuperDex Atlas](https://github.com/huangkiki/superdex-atlas) · [Genesis Atlas](https://github.com/huangkiki/genesis-atlas) · [Newton Atlas](https://github.com/huangkiki/newton-atlas) · [PhysX Atlas](https://github.com/huangkiki/physx-atlas) · [Drake Atlas](https://github.com/huangkiki/drake-atlas)

Initial guides and pinned source maps are available; the full course is in development. This phase focuses on understanding engine mechanisms. Later experiments will reuse DexLab with their original versions, configurations and workloads. Course progress is tracked separately from the experimental coverage above.

## Start here

- **Read findings and figures:** [Full experiment reports](docs/site/en/results.md) and the [stage report](docs/holiday-report.md).
- **Recompute results:** Each report links its frozen protocol, scorer and raw records; public archives are available in [Releases](https://github.com/huangkiki/Dexlab/releases).
- **Run a demo:** Follow the [installation guide](docs/installation.md), then try the apple-stem grasp below.

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# Or --backend superdex; add --headless without a display
```

The viewer opens after SDF preparation and planning. No model API key is needed. Use each research report's recorded versions and commands for its experiments.

Future work, unfinished tasks and blockers are tracked in [Issues](https://github.com/huangkiki/Dexlab/issues).

## Code and sources

Experiments use official physics engines and retain parameter provenance, failures and independent scoring. [Experiments](demos/) · [Development workflow](docs/autoresearch.md) · [Asset sources and licenses](docs/ASSETS.md)

Thanks to [UniLab](https://github.com/unilabsim/UniLab), [Project SuperDex](https://github.com/unilabsim/project_superdex), [MuJoCo](https://github.com/google-deepmind/mujoco), [Genesis](https://github.com/Genesis-Embodied-AI/Genesis), [Newton](https://github.com/newton-physics/newton), [OpenArm](https://github.com/enactic/openarm) and [Wuji](https://github.com/wuji-technology). Code is licensed under [Apache-2.0](LICENSE).
