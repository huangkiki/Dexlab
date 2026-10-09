# SuperDex incline: twelve frozen solver profiles

[简体中文](superdex-incline-results.zh-CN.md) · [Protocol and commands](superdex-incline-protocol.md)

Nine configurations pass 8/9 original incline cases. Newton with CG, ASYNC_CG or PARALLEL_CG passes 6/9, each retaining two invalid force/state records. Every configuration fails the 0.5 ms static displacement limit. All twelve negative controls are valid freefall and are correctly rejected. These are deterministic cases under fixed settings, not success probabilities, a complete tuning search or a general engine ranking.

| Nonlinear / linear / friction | Positive passes | Invalid positives | Negative |
|---|---:|---:|---|
| NEWTON / AUTO / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| NEWTON / CG / C1_REGULARIZED | 6/9 | 2 | Valid, rejected |
| NEWTON / GMRES / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| NEWTON / AUGMENTED_CG / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| NEWTON / LDLT / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| NEWTON / LU / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| NEWTON / ASYNC_CG / C1_REGULARIZED | 6/9 | 2 | Valid, rejected |
| NEWTON / PARALLEL_CG / C1_REGULARIZED | 6/9 | 2 | Valid, rejected |
| NEWTON / MINRES / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| BFGS / AUTO / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| SR1 / AUTO / C1_REGULARIZED | 8/9 | 0 | Valid, rejected |
| NEWTON / AUTO / CINF_REGULARIZED | 8/9 | 0 | Valid, rejected |

The AUTO/C1 nine positives are the unchanged v0.46.0 historical records; its negative is new. The other eleven profiles are prospective. Source/official-wheel identities and all nine original model/parameter readbacks match before reuse. Historical selected-linear-branch, per-contact and resource observations remain missing; new records do not fill them. See the [historical identity audit](superdex-solver-audit.md).

## What the failures mean

The six invalid records are nominal-zero-friction cases at 1 and 0.5 ms in the three CG variants. Maximum momentum residuals are respectively **2.1045017e-7 and 3.5577870e-7 N·s**, above the unchanged 1e-7 limit. At those samples both actor and scene report **STOPPED**, after five/four nonlinear iterations. Native residual norm × timestep equals the independently reconstructed momentum residual; signed per-contact force sums and total torque checks pass. This is evidence of an incompletely converged native step. The exact stopping trigger remains [#159](https://github.com/huangkiki/Dexlab/issues/159); neither an engine defect nor state injection is established. [Observed samples](evidence/superdex-incline/invalid-record-diagnosis.json).

The nine 8/9 configurations still fail a physical requirement. Switching a linear solver does not remove the shared 0.5 ms static creep failure. C1 and C-infinity are smooth friction laws, not exact set-valued stiction. None earns coverage-v1 reliable-task credit, and twelve configurations of an incline remain one task type. Cross-engine historical cohorts have different numerical contact laws and no common tuning/holdout budget.

## Five CUDA options are unavailable in this official build

CUDA_CG, CUDA_GMRES and the experimental CUDA sparse Cholesky/LDLT/LU options each fail native `set_solver_params`, before advancing time: the official FP64 wheel was not compiled with CUDA. The pinned [source guard](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp#L418-L425) and actual errors agree. A visible GPU does not make the binary support these solvers. Recovery requires an official CUDA-enabled build, renewed identity/admission checks and a newly frozen package. This is a build-specific unsupported result, not a claim that the engine has no GPU implementation.

## Evidence and cost

120 zero-duration admissions pass. Twelve serial acquisition processes add **99 positive + 12 negative two-second episodes / 255,000 native updates**; nine historical positives are rescored without replay. Full effective solver structs, local COM/DoFs, geometry, contact ownership/positions/forces, independent total force/torque, native iteration/residual observations, force epochs and partial completion are retained. AUTO's selected internal linear branch is still source-derived; native statistics do not expose that field. The original failed CUDA admission and continuation attempts remain available.

Acquisition service wall time is **63.150 s**. Summed setup/native step/observation time is **7.747 / 7.857 / 18.060 s**; serialization, process imports and other overhead explain additional time. These instrumented correctness records do not support a speed ranking against older cohorts. Independent scoring runs without importing MuJoCo, SuperDex or Drake. [Per-case timing and iteration observations](evidence/superdex-incline/timing-and-solver-stats.json).

The frozen envelope is 16 GiB, four CPU-equivalent cores, zero swap, with 8 GiB launch reserve and transfer/timing exclusion. Measured cgroup peak is **905.484 MiB**, with no memory-limit/OOM events. Three CPU-throttled periods total 5.514 ms. The next equivalent recording workload can use the minimum 8 GiB tier; the full SDF regression has its own measured 32 GiB plan. GPU-memory and pressure observations are saved, without claiming GPU execution.

No trajectory was replayed or tolerance relaxed after results. The later recorder change only preserves raw nonfinite observations for independent rejection; every collected value in this package is finite, so existing bytes/results are unchanged. Original acquisition source is archived separately from final delivery source.

[Scores and protocol identities](evidence/superdex-incline/profiles.json) · [Official runtime proof](evidence/superdex-incline/official-proof.json) · [Native rejection of CUDA options](evidence/superdex-incline/unsupported.json) · [Resource observations](evidence/superdex-incline/resources.json)

[Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.51.0/dexlab-superdex-incline-v1.tar.gz) · [Archive SHA256](evidence/superdex-incline/archive.json)
