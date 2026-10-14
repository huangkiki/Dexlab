# Drake incline qualification v1

[简体中文](drake-incline-protocol.zh-CN.md) · [Issue #117](https://github.com/huangkiki/Dexlab/issues/117)

This is initial native-path qualification, not a completed six-engine comparison or `coverage-v1` admission. Freeze the [protocol](evidence/drake-incline/protocol-v1.json), [official wheel proof](evidence/drake-incline/official-proof.json), recorder/scorer bytes and resource plan before physics. No outcome-based tuning is allowed in this batch. The original nine cases retain the 40 mm / 64 g cube, 15° static μ=.5, 35° sliding μ=.5, 15° nominal-zero friction, 2/1/.5 ms steps, two-second duration, 0.5–2 s scoring window and all original physical thresholds. MuJoCo-only impedance is not a Drake setting.

The tenth case removes the floor from the 1 ms static case. It must retain valid free-fall dynamics and fail independent support/hold checks. Native exceptions, incomplete traces or inconsistent observations stop the batch; ordinary physical failures remain results. Initial budget: nine positive cases and one negative, at most 30 minutes native runtime, one process. A frozen 16 GiB / four-core adaptive envelope includes an independent 8 GiB launch reserve; the service deadline is 1,800 s, which also bounds native runtime. No performance ranking is made from these qualification costs.

## Fixed native configuration

Drake 1.57.0, official build source `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`, CPU double precision, discrete plant, **SAP solver / kLagged contact approximation / strict hydroelastic contact**. The box has rigid hydroelastic surface geometry (10 mm resolution hint); the analytic half-space has compliant hydroelastic properties (0.1 m slab, 1e8 Pa modulus). Both surfaces use zero Hunt–Crossley dissipation and equal static/dynamic coefficients. The pair API uses a harmonic combination; equal inputs preserve the coefficient, including zero. These are numerical settings, not measured materials or calibrated equivalence to other engines. No point-contact fallback or surrogate is enabled.

Authored stiction tolerance is 1e-4 m/s; near-rigid threshold is 1.0, with native getter verification. The discrete model resolves dynamic friction and ignores the separate static coefficient. The installed public API exposes SAP and three approximations (`kSap`, `kSimilar`, `kLagged`); TAMSI is absent. Only kLagged/hydroelastic is executed in this initial slice. Other applicable configurations remain **not run**, assigned to [#151](https://github.com/huangkiki/Dexlab/issues/151), not labeled unsupported.

[Matching solver source](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.h) gives default Newton budget 100, optimality absolute/relative tolerance 1e-14 / 1e-6, cost tolerance 1e-30 / 1e-15, exact line search (100 maximum) and block-sparse Cholesky. The absolute optimality tolerance has square-root-joule units; it is not a force tolerance. These are **source-derived defaults**, not a saved native SAP parameter object or achieved iterations. Public pydrake provides no per-step SAP statistics/parameter getter or stiction-tolerance getter. The material `HydroelasticType` enum has no Python value binding; that readback stays null. Configured setters and available geometry/material readbacks are saved separately.

## Observation and independent acceptance

Use sampled dynamic output ports, verified enabled. [Plant source](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h) defines dynamics from the update using the previous state, alongside the newly integrated kinematic state. Save each interval's start/end clock, integrated hydroelastic contact force and torque at surface centroid, contact area, generalized contact force, pose and spatial velocity. No fresh end-state force solve is substituted. Quadrature forces and native solver statistics are unavailable.

Before stepping, verify native mass/inertia/COM, cube dimensions, collision and plane frames, gravity, solver/contact selection, material parameters and initial state. Offline checks reject changed hashes, unqualified native identities, reset contamination, bad coordinates/clock, lost contact patches and wrong force signs. The contact sum must match native generalized linear force within 1e-7 N; momentum consistency retains the shared 1e-7 N·s gate. Position increments must match the native end velocity times dt within 1e-10 m. Penetration is reconstructed analytically from recorded end-state cube/plane geometry, not called a native quadrature-depth readback. The original analytic position, velocity, acceleration, rotation, support and penetration limits remain unchanged.

The six-engine queue remains explicit: MuJoCo #146, SuperDex #147, Genesis #148, Newton Physics #149 and PhysX #150 are independent; Drake #151 consumes this integration. Historical MuJoCo/SuperDex records retain their original cohort. No new result is inferred for another engine or another Drake profile.

```sh
# In the separately qualified optional Drake environment, under the bounded guard:
PYTHONPATH=src python -m dexlab.drake_incline \
  --protocol docs/evidence/drake-incline/protocol-v1.json \
  --proof docs/evidence/drake-incline/official-proof.json --output NEW_RUN
PYTHONPATH=src python -m dexlab.drake_incline_score --input NEW_RUN --output NEW_SCORE.json
```

## Explicit v2 revision

After the preserved v1 native clipping failure and three preregistered clearance diagnostics, [v2](evidence/drake-incline/protocol-v2.json) adds exactly 1 µm initial normal clearance. All nine cases, the negative, material settings, score window and limits remain unchanged. This is a separate cohort. The new source/protocol hashes and 1,800 s batch budget were frozen [before execution](https://github.com/huangkiki/Dexlab/issues/117#issuecomment-6084573507). See [results and all failures](drake-incline-results.md).
