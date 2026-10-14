# MuJoCo incline solver results

[English](mujoco-incline-results.md) | [简体中文](mujoco-incline-results.zh-CN.md)

Official MuJoCo 3.15.0, CPU float64, Euler: the three elliptic profiles pass 3/9 positives each; the three pyramidal profiles pass 0/9. Six collision-disabled-plane negatives are valid freefall records and are correctly rejected. This is a result for the [frozen numerical profiles](mujoco-incline-protocol.md), not engine-wide incapability, material calibration or a six-engine ranking. No configuration earns reliable coverage-v1 credit.

| Solver / cone | Positives passed | Invalid positives | Negative |
|---|---:|---:|---|
| pgs-elliptic | 3/9 | 0 | Rejected as intended |
| pgs-pyramidal | 0/9 | 0 | Rejected as intended |
| cg-elliptic | 3/9 | 0 | Rejected as intended |
| cg-pyramidal | 0/9 | 3 | Rejected as intended |
| newton-elliptic | 3/9 | 0 | Rejected as intended |
| newton-pyramidal | 0/9 | 3 | Rejected as intended |

All three elliptic profiles fail the static 1 mm drift limit and all three sliding cases; their frictionless cases pass. All pyramidal profiles fail every positive under the same physical limits. CG/pyramidal and Newton/pyramidal additionally have three invalid nominal-zero-friction records each. Invalid cases stay in the denominator and cannot earn a pass; their physical accuracy metrics are withheld rather than computed from an inconsistent force/state record. Each hashed per-profile score and manifest is under [`evidence/mujoco-incline/`](evidence/mujoco-incline/pgs-elliptic-score.json).

The nine Newton/elliptic positives are unchanged historical observations. Their full 18-case original archive is retained, including the impedance .99 cohort; those additional cases do not enter this nine-case score. The historical archive included a later recorder. [Source recovery and reuse audit](evidence/mujoco-incline/history-reuse-audit.json) recovers the exact recorded source hash from commit `0904240e594f4e1fabb2bd908a32af830afa84b2`. Sixty prospective zero-step admissions passed, and all nine historical source XMLs reproduce identical effective native parameters. Their historical library mappings, per-contact traces and resource pressure remain unobserved; new admission is explicitly not historical telemetry.

For CG/pyramidal, maximum momentum residuals are .0120141691/.00204689054/.000303783207 N·s at 2/1/.5 ms. Newton/pyramidal residuals are .00114039045/.0000238631735/.0000126500777 N·s. The original bound is 1e-7 N·s. Every reconstructed contact force agrees with native generalized force, and native acceleration agrees with the velocity increment. The problematic samples stop well below the iteration cap. This does not identify a MuJoCo bug or a causal mechanism; [#157](https://github.com/huangkiki/Dexlab/issues/157) owns source and controlled attribution. No failed trajectory was rerun, discarded or made acceptable by a looser limit.

All 60 compiled XML export/reimport checks detected some rounding loss at a 1e-12 absolute comparison threshold. Maximum differences include 3.33e-11 kg·m² inertia, 4.09e-8 m position and 4.03e-7 in rotation-matrix components. These small observed differences are not a measured task-outcome effect. Acquisition always uses the original XML. Native geometry, COM, inertia, friction combination, solver settings, force/torque frames, contact ledger and clocks are independently checked. [Official wheel proof](evidence/mujoco-incline/official-proof.json) binds 137 code files and the actually mapped native core; no engine patch.

Six acquisition starts produced 51 new episodes / 117,000 native steps; nine historical positives were reused. New native stepping totals 0.519393 s, observation 2.144813 s and summed case setup 0.094822 s. These are recorded instrumentation costs, not an exclusive speed benchmark or a comparison with historical timing. The first four-profile command took 137.520 s because the original independent scorer repeatedly decompressed lazy NPZ arrays. The revised scorer materializes each channel once; all three previously successful score reports reproduce exactly, and the two inconsistent profiles now retain every invalid case. The continuation took 1.914 s. No native replay was needed for this reporting fix.

[Resource receipts](evidence/mujoco-incline/resources.json) retain cgroup counters, pressure, throttling, I/O and device-wide GPU snapshots. The frozen 16 GiB / four-core-equivalent batch peaked at 113.41 MiB; no memory-high/max/OOM events or CPU throttling occurred. The next equivalent workload can use the 8 GiB minimum tier; the separately measured full SDF-grasp gate needs its own 32 GiB plan. Neither observation changes a batch already in progress or fills historical gaps. Formal pinch budget: unused.

[Archive](https://github.com/huangkiki/Dexlab/releases/download/v0.50.0/dexlab-mujoco-incline-v1-evidence2.tar.gz) · SHA-256 `d6c38604d3b3110f58a98dfd82f9938133d4365c4f8391dfcd1acb31564cb13b` · 42,164,529 bytes

The archive contains all original and new traces, input/compiled models, source snapshots, protocol freezes, observed parameters, partial-status ledger, independent scores, resource evidence and per-file SHA256SUMS. Follow its README to rescore offline with NumPy. The first packaged draft is preserved locally; packaging revision 2 includes complete pressure/GPU/resource projections without private host paths. The protocol remains revision 1.
