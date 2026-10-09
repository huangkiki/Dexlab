# Drake: initial incline qualification

[简体中文](drake-incline-results.zh-CN.md) · [Frozen protocol](drake-incline-protocol.md) · [Full score](evidence/drake-incline/score-v2.json) · [#117](https://github.com/huangkiki/Dexlab/issues/117)

**Official Drake 1.57.0 / SAP / kLagged / strict hydroelastic completed nine positive cases: six passed and three sliding cases failed.** The no-floor control has valid free-fall dynamics and is correctly rejected by the unchanged physical scorer. This qualifies the direct recording path, not universal incline accuracy or `coverage-v1` reliable task coverage. CPU double precision; no engine modifications.

| Case | Outcome | Acceleration error (m/s²) | Force error RMSE (N) | Max rotation (rad) |
| --- | --- | --- | --- | --- |
| static-h0.002 | PASS | 2.16255e-13 | 1.21e-07 | 0.000291529 |
| static-h0.001 | PASS | 5.00233e-12 | 2.51794e-07 | 7.52268e-05 |
| static-h0.0005 | PASS | 1.56514e-16 | 3.23458e-07 | 4.11151e-05 |
| sliding-h0.002 | FAIL | 1.60734 | 0.296993 | 0.00747664 |
| sliding-h0.001 | FAIL | 1.61137 | 0.457299 | 0.00469234 |
| sliding-h0.0005 | FAIL | 1.62362 | 1.02549 | 0.0118299 |
| frictionless-h0.002 | PASS | 2.98147e-06 | 3.89324e-06 | 3.71514e-06 |
| frictionless-h0.001 | PASS | 2.21743e-05 | 3.90137e-06 | 1.8128e-07 |
| frictionless-h0.0005 | PASS | 9.61167e-06 | 3.78805e-06 | 5.16191e-08 |
| negative-no-floor | FAIL (negative) | 2.53901 | 0.62784 | 0 |

The original limits remain 0.05 m/s² acceleration error, 0.01 N force error, 0.01 rad rotation, 1 mm penetration, 1 cm sliding position RMSE and 1 cm/s velocity RMSE. Static cases instead require displacement ≤1 mm and speed ≤1 mm/s. Static drift is 0.128–0.153 mm. Frictionless position error is 0.564–2.209 mm; acceleration error is 2.98e-6–2.22e-5 m/s². All ten records satisfy clock, position/velocity, contact/generalized-force and momentum consistency; the maximum momentum residual is 2.783e-9 N·s against the unchanged 1e-7 gate. The sliding force error **increases** as the step shrinks (0.297 → 0.457 → 1.025 N). Reducing dt alone did not establish convergence. We do not attribute this to a specific solver mechanism: [#151](https://github.com/huangkiki/Dexlab/issues/151) owns material/contact-approximation diagnostics and the remaining applicable profiles.

## Preserved failure and explicit revision

The first v1 case, initialized exactly touching the plane, triggered an official native mesh/half-space clipping assertion before any completed step. The other v1 cases remain unrun. The original recorder caught `Exception`, so native `SystemExit` left `error:null`; its zero-length record was still rejected offline. The recorder now records and re-raises `BaseException`, with tests for interruption and native failure. The original failed bytes are retained, accompanied by a correction rather than rewritten metadata.

The [matching clipping source](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/proximity/mesh_half_space_intersection.cc) counts strictly positive vertices but chooses a nonnegative vertex in the one-positive branch. Three preregistered independent 0.1 s static diagnostics with 1 nm, 1 µm and 100 µm initial normal clearance each completed 50 valid steps. This supports a degenerate coplanar initialization explanation; the actual internal triangle signs were not observed. The preselected **1 µm** clearance was then frozen in [protocol v2](evidence/drake-incline/protocol-v2.json), before its nine-case outcomes. v2 is a separate cohort, not a silent change to the historical initial state. All other parameters and physical limits remain unchanged. Development accounting: two campaign starts, three diagnostic starts, two admission-only starts; 23,150 completed native updates; none charged to the pinch formal budget.

## Resources and reproduction

The frozen acquisition envelope was 16 GiB / four CPU-equivalent cores, swap disabled, an 8 GiB launch reserve and 1,800 s deadline. Complete v2 service wall time was 4.253 s; cgroup peak memory was 182,087,680 bytes (173.65 MiB), with zero memory high/max/OOM events and zero CPU throttles. These are this tiny CPU qualification's costs, not engine throughput. Its next equivalent measured batch can use the 8 GiB minimum tier; large backend regressions retain their independently measured allocation.

An initialization timestamp defect inflated the first interval's sampled CPU/I/O rate peaks. Those peaks are explicitly withdrawn from this report; cumulative CPU/I/O counters, kernel memory high-water mark and enforced limits remain valid. The timestamp is fixed for future runs and a delayed-GPU-query regression test covers it. CPU physics did not use GPU memory; desktop-wide GPU samples are not job allocations.

[Download all trajectories and failures](https://github.com/huangkiki/Dexlab/releases/download/v0.49.0/dexlab-drake-incline-v2.tar.gz). The score JSON binds the archive SHA-256. The archive contains both campaigns, all three diagnostics, both admissions, frozen source/protocol/proof, an explicit v1 error correction and per-file hashes. No official Drake wheel or private host paths are redistributed. Original physics files are copied byte-for-byte; resource publication is an explicitly selected projection with rate peaks withdrawn. The installed official wheel's 402 hashed files and actually mapped native libraries were verified before physics; the proof binds source/build identity separately from the Python package version.

```sh
# Separate Python 3.12 environment; verify against official-proof.json before physics.
python -m pip install drake==1.57.0
PYTHONPATH=src python -m dexlab.drake_incline \
  --protocol docs/evidence/drake-incline/protocol-v2.json \
  --proof docs/evidence/drake-incline/official-proof.json --output NEW_RUN
# Independent process; needs NumPy, not pydrake:
PYTHONPATH=src python -m dexlab.drake_incline_score \
  --input dexlab-drake-incline-v2/campaign-v2 --output NEW_SCORE.json
```

Acquire under the repository's bounded resource/qualification guard. Do not mix performance collection with hashing, transfers or another physics process. No outcomes from other engines are inferred: MuJoCo [#146](https://github.com/huangkiki/Dexlab/issues/146), SuperDex [#147](https://github.com/huangkiki/Dexlab/issues/147), Genesis [#148](https://github.com/huangkiki/Dexlab/issues/148), Newton Physics [#149](https://github.com/huangkiki/Dexlab/issues/149), PhysX [#150](https://github.com/huangkiki/Dexlab/issues/150) and further Drake profiles [#151](https://github.com/huangkiki/Dexlab/issues/151) remain independent. kSap, kSimilar and other applicable contact models are not run, not declared unsupported. Frozen holdout and equal tuning-budget coverage acceptance remain outstanding; six successful repetitions do not become six task types.

[Environment inventory](evidence/drake-incline/environment.json): Intel Core i9-14900K, Python 3.12.12, NumPy 2.5.3. This host inventory was captured after acquisition on the same host and unchanged isolated environment, not presented as historical per-step telemetry.
