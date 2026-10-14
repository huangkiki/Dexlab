# SuperDex incline protocol v1

[简体中文](superdex-incline-protocol.zh-CN.md) · [Results](superdex-incline-results.md)

Issue #147 freezes one-factor solver changes around the historical Newton/AUTO/C1 profile. The native core/API are official SuperDex 1.0.0 FP64, build source `1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`; current official wheels and loaded libraries are checked before acquisition. Five CUDA enums are rejected by the native build gate, with zero time advanced. Twelve CPU profiles pass zero-duration admission; this is not an exhaustive Cartesian search over nonlinear, linear, friction and integrator options.

The 40 mm, 64 g uniform free cube starts at rest flush with an infinite plane. g=9.81 m/s²; 15°/μ=.5 static, 35°/μ=.5 sliding, 15°/nominal μ=0; dt=2/1/.5 ms, each 2 s. Backward Euler, 100 nonlinear iterations, absolute/relative tolerance 1e-9; other native solver settings are saved in each complete effective-parameter readback. Linear AUTO/max_iter=-1 and tolerance strategy retain native semantics, not equal numerical work. Nonlinear choices are Newton/BFGS/SR1; linear CPU choices are AUTO/CG/GMRES/AUGMENTED_CG/LDLT/LU/ASYNC_CG/PARALLEL_CG/MINRES; the alternate friction profile is C-infinity regularization. No outcome-based tuning.

Penalty 1e9 Pa/m, threshold 1e-4 m, smoothing half-distance 5e-5 m, friction falloff 1e-3 m/s, zero normal/viscous damping; both actor friction coefficients match. The source combines Coulomb coefficients geometrically; the effective combined law is not exposed per contact. These are numerical settings, not calibrated materials. All original thresholds and the 0.5–2 s scoring window stay unchanged, including the 1e-7 N·s force/state consistency limit. [Original equations and limits](incline-comparison-protocol.md).

Each profile adds one negative using the static 15°/μ=.5/1 ms setup with actor-pair contact disabled in both directions; the plane asset remains. Validity additionally requires zero observed force/contact and gravity-only velocity. An invalid negative cannot qualify a profile. The original AUTO/C1 positives are reused only after archive hash, protocol identity and all nine prior readbacks match; reconstruction does not turn missing old fields into observations.

Budget: twelve serial launches, 99 new positives + 12 negatives, 255,000 updates; at most 120 s per profile and six hours per package. Resources are frozen at 16 GiB/four-core quota, 8 GiB launch reserve and zero swap. Readbacks and failure-safe recording add overhead. No formal pinch budget is consumed. Independent analysis, final regression and archive work use separate resource receipts. The complete acquisition freeze and source hashes are included in the raw archive.

The BFGS and SR1 rows identify requested enum configurations, not additional independently exercised quasi-Newton algorithms. Both effective readbacks retain `d_residual_assembly_period=1`; the pinned [native implementation](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/solvers/newton_solver.cpp#L267-L272) states that this is equivalent to Newton. Reassembly on every iteration leaves no low-rank BFGS/SR1 update between assemblies. Their unchanged outcomes remain reported, but this batch does not qualify quasi-Newton behavior with a longer assembly period.

```bash
# Run only under the repository's bounded resource and research-lock wrapper.
python -m dexlab.incline_compare_run --manifest docs/evidence/superdex-incline/profiles/newton-cg-c1.json --output /data/new-cg --admission-only
python -m dexlab.incline_compare_run --manifest docs/evidence/superdex-incline/profiles/newton-cg-c1.json --output /data/new-cg-physical
# Offline, after extracting dexlab-superdex-incline-v1.tar.gz:
python -m dexlab.incline_compare_score --profile dexlab-superdex-incline-v1/campaign-v1/newton-cg-c1 --output cg-score.json
python -m dexlab.incline_compare_score --superdex dexlab-superdex-incline-v1/history/paired-incline/superdex --mujoco dexlab-superdex-incline-v1/history/paired-incline/mujoco --output historical-comparison.json
```

Each original campaign manifest and immutable recorder are archived. Public combined protocol/score files join historical AUTO/C1 positives and the new negative with explicit provenance; they do not rewrite the acquisition manifest. Independent scoring checks every contact ledger and native total torque before the unchanged analytic metrics. The six invalid CG-family records stay in the positive denominator and link to #159. No new task type or reliable coverage-v1 count is added.
