# MuJoCo incline solver qualification

[English](mujoco-incline-protocol.md) | [简体中文](mujoco-incline-protocol.zh-CN.md)

This is the independent MuJoCo child [#146](https://github.com/huangkiki/Dexlab/issues/146) of the six-engine study. It extends the [historical paired protocol](incline-comparison-protocol.md), without changing its physical limits or treating repeated timesteps, solvers or execution paths as new task types. This initial analytical qualification is separate from coverage-v1's equal tuning budget and frozen holdout acceptance.

The frozen native baseline is official MuJoCo 3.15.0, Python binding 3.15.0, CPU float64, source commit `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`. The release inventory is checked before acquisition; the loaded library and installed code must match the official wheel. Its [native solver enum](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjtype.h) and [dispatch](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c) register PGS, CG and Newton. This batch covers each with elliptic and pyramidal cones; Euler integration is fixed to preserve the historical force/velocity interval. Other integrators are not declared unsupported. Framework and MJWarp qualification belongs to [#152](https://github.com/huangkiki/Dexlab/issues/152).

Every positive profile uses a free 40 mm, 64 g uniform cube, gravity 9.81 m/s², exactly touching the plane at rest, and a two-second trajectory. Nine cells combine static 15°/μ=.5, sliding 35°/μ=.5 and nominally frictionless 15° with 2/1/.5 ms. Freeze 100 solver iterations, tolerance 1e-10, solref [.02, 1], constant impedance .9, impratio 1, and the original thresholds and .5–2 s scoring window. Equal solver budgets do not imply equal convergence. Native combination uses maximum friction for equal-priority geometry; these identical input coefficients therefore agree. Nominal zero friction can be clamped by the native engine and is reported as observed. [Pinned combination implementation](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c).

Each profile also requires a two-second, 1 ms static-case negative with the plane collision masks disabled. The visible plane remains in the authored model but cannot support the cube. Valid freefall must fail the original physical checks; missing support is not replaced by zero-friction observations or a fabricated pass. The recorder reads forces and contact frames left by Euler's preintegration solve, and state after integration. Independent scoring reconstructs every contact force, compares the generalized-force and acceleration channels, and retains the original 1e-7 N·s momentum consistency bound.

Reuse the nine identity- and protocol-matching Newton/elliptic historical positives. The v0.46.0 archive contains all 18 original impedance .9/.99 cases; retain the unselected .99 failures as historical evidence. The archive's source copy is a later recorder, while its campaign names the original recorder's hash. Recover that exact original source from commit `0904240e594f4e1fabb2bd908a32af830afa84b2` and verify its recorded SHA-256; do not overwrite the archive. Historical package code matches the prospective official wheel, but historical loaded-library mapping, per-contact ledger and resource pressure were not recorded. Prospective observations cannot fill those historical fields. Before reuse, perform zero-step admission against each original XML and compare with the new profile's compiled readback.

Record source XML, compiled export, effective native parameters, geometry/COM/inertia/frames, per-contact distances/frames/forces/materials, force epochs, warnings, achieved iteration counts and arena use. Compare export/reimport numerically and report precision loss separately: physics always uses the original source XML, never the potentially lossy export. No engine patch, parameter tuning, state writes after initialization or physical tolerance change is allowed in this batch.

The initial acquisition budget is six serial starts: five missing profiles × (nine positives + one negative), then the missing Newton/elliptic negative. Zero-step admission and preparation are separate from positive-duration acquisition; new diagnostics require a stated hypothesis and separate package. Freeze 16 GiB and four CPU-equivalent cores for this unknown recorder workload, leave 8 GiB desktop headroom, disable swap, and retain memory pressure, CPU throttling, GPU allocation and I/O observations. Timing is scoped to native stepping, observation and whole command separately, with no performance ranking against historical records. Failures and interruptions keep their actual partial lengths and exception, and never count as completed cases.

Machine-readable manifests live under `docs/evidence/mujoco-incline/`. After the official-wheel proof and resource admission, reproduce one missing profile with:

```sh
python -m dexlab.incline_run \
  --manifest docs/evidence/mujoco-incline/pgs-elliptic.json \
  --proof official-proof.json --output pgs-elliptic
python -m dexlab.incline_score --input pgs-elliptic --output pgs-elliptic-score.json
```

Add `--admission-only` for the zero-step check. Use the repository's bounded resource runner and research lock around native commands. Scores remain provisional until the full repository gate, merge and deployed evidence verification.
