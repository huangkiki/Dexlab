# Matched normal-damping ablation

English | [简体中文](DAMPING_ABLATION.zh-CN.md)

Status: six preregistered cases completed, independently rescored and published in [v0.28.0](https://github.com/huangkiki/Dexlab/releases/tag/v0.28.0). Question: does setting the SuperDex normal viscous coefficient to zero remove the previously recorded tensile normal force during unloading, with every other condition fixed within each pair?

The [six-case matrix](../../benchmarks/contact-damping-ablation-v1.json) fixes a 0.2 kg, 40 mm cube, zero friction, the same initial pose/velocity, native BOX/plane representation, penalty 12,500,000, threshold1µm and smoothing0.5µm. Prescribed net downward loads2/4/6/−1N last0.2s each. Coefficients0/10s/m are paired at0.5/0.25/0.125ms; alternate execution order by pair. One serial run per case,600s batch budget,660s enforced service limit; official latest runtime/source admission before execution. No online retuning.

Reference for the primary question: nonadhesive contact cannot pull the bodies together. Retain the existing1e−6N no-tension tolerance, all momentum/contact-ledger/geometry/settling/release checks and every failed case. Report minimum vertical contact force, negative-force step count/duration and event times, separating loading from unloading. Forces are read after the native step and correspond to that step; state arrays include the initial state. Check ledger sums and momentum rather than inferring contact forces from motion alone.

The constant K=20kN/m,D=40Ns/m transient target remains a separately labeled synthetic diagnostic. Zero damping need not meet it. If negative force persists with zero damping, the simple damping-only explanation is rejected; if it disappears, this supports dependence on that parameter in this fixture, not proof of the internal contact-law formula or a universal engine defect. Geometry/cooking and full pair-law observability remain limited. Deterministic pairs do not justify population confidence intervals; real-material calibration remains separate.

## Paired results

All six native runs completed and independently reproduced. Each pair matches actual initial state, input mesh, step commands/clock, source and native runtime/solver/actor settings except damping; contact-ledger and momentum checks pass. This covers observable representation, not a full internal combined-law readback.

| Timestep | Damping 0: minimum force | Damping 10: minimum force | Damping 10: negative steps / duration | Zero-damping engineering result |
|---|---:|---:|---:|---|
| 0.5 ms | 0 N | −0.450712 N | 2 / 1.00 ms | Pass |
| 0.25 ms | 0 N | −0.281743 N | 3 / 0.75 ms | Plateau settling fails |
| 0.125 ms | 0 N | −0.161407 N | 4 / 0.50 ms | Plateau settling fails |

All negative-force events occur during unloading. All zero-damping runs have no force below the existing tension tolerance; all nonzero-damping runs fail no tension. **Zeroing the parameter eliminates the recorded tensile force in these matched cases, but is not a complete repair.** Only1/6 passes engineering acceptance and0/6 passes jointly with the original transient target. Zero damping is not the40Ns/m constant-damping target and does not constitute material calibration.

![Paired unloading contact forces](../../docs/evidence/damping-ablation-v1.png)

The plot shows solved-step samples during0–15ms after unloading; joining lines do not reconstruct substep force. Duration is negative-step count times timestep. Full records remain in raw evidence. [All outcomes/event intervals](../../docs/evidence/damping-ablation-v1.json) · [Plot provenance](../../docs/evidence/damping-ablation-v1.provenance.json)

This intervention supports parameter dependence in these trajectories, not separation of every mediated trajectory effect or a universal internal engine defect. Official SuperDex1.0.0FP64 with MuJoCo3.15.0 in the environment; pre-batch latest/official-wheel admission passed. Six runs share frozen execution source. No official engine, controller or acceptance threshold was changed.

```bash
.venv/bin/python demos/contact-benchmark/report_damping_ablation.py PATH_TO_STUDY
.venv/bin/python demos/contact-benchmark/plot_damping_ablation.py PATH_TO_STUDY --output damping.png
```

The report first reproduces every historical outcome, then rejects missing/reordered pairs, extra parameter changes, mismatched native readback, missing data and invalid clocks. Five new tests include counterexamples and the unloading boundary. Consult this version's PR/Release for complete submission and publication status.

## Raw evidence and reproduction

[Versioned raw evidence](https://github.com/huangkiki/Dexlab/releases/download/v0.28.0/dexlab-damping-ablation-v1.tar.gz): 2,929,207 bytes,231 files checked and independently extracted/re-scored with all six outcomes identical and raw bytes unchanged. SHA-256: `45bf706bfa2f5552dba5e11dfb184ec2d46164035f742cb502b3a0623d942f35`. Check this external digest first, then the package manifest; install requirements.txt and follow PROVENANCE.md. source/ retains execution-time bytes; analysis-src/ adds only the subsequent paired-analysis module and is not the execution snapshot. Same-host extracted replay does not prove cross-hardware reproducibility; same-disk copies are not independent backups.

The batch enforced24GiB, two-CPU quota, zero swap and660s deadline. Whole-service time16.676s includes admission and recording, not engine throughput. All failures remain.

## Point-level unloading audit

An offline extension reuses these six frozen archives; it adds no native episodes and changes no historical verdict. `--pointwise` first reproduces the original report, then checks each step's point-force ledger, finite observations, upward native normal and plane-side position at world z=0. Only for this qualified horizontal-plane fixture does world-vertical point force represent the normal component. Unknown frames, missing rows or ledger discrepancies are rejected. The 1e-12 m/frame checks test serialized geometry, not material accuracy. The existing 1e-6 N tension tolerance is unchanged.

| Timestep | Damping 0: minimum observed unloading point force / N | Damping 10: minimum / N | Damping 10: negative point samples / affected steps |
|---|---:|---:|---:|
| 0.5 ms | 2.426e-9 | −0.075119 | 12 / 2 |
| 0.25 ms | 0.003374 | −0.046957 | 18 / 3 |
| 0.125 ms | 0.004274 | −0.026901 | 24 / 4 |

All six have zero loading-phase negative point samples. Zero damping has none during unloading either. No observed negative-point step is hidden by a nonnegative aggregate in this cohort. This closes an observation gap in the previous aggregate-only diagnosis; it does not repair the settling/transient failures. A dedicated synthetic counterexample confirms that the diagnostic detects a negative point force even when another positive point makes the total positive.

Counts are solved-step point samples, not distinct persistent contacts. Empty-contact windows produce `null` for minimum observed point force, not a fabricated zero. Durations count affected steps once and do not measure substep lifetime. The minimum in this table excludes steps without contacts; it differs from the aggregate minimum, which includes zero-force separated steps. This is retrospective diagnosis of already observed data, not a new preregistered outcome or proof for arbitrary surfaces.

```bash
python demos/contact-benchmark/report_damping_ablation.py PATH_TO_STUDY --pointwise
```

[Complete point-level report](../../docs/evidence/damping-pointwise-v1.json) retains original engineering/transient scores and includes every event interval. The default command returns the original report unchanged. Nine focused tests pass: the five existing ablation tests plus four point-level tests covering cancellation, empty/positive minima, tolerance, missing observations, invalid frames, nonfinite force, ledger mismatch and clock corruption. Offline reanalysis of all six archives verified exact equality of the original report before and after removing the optional diagnostic fields. Raw sources and bytes remain attached to v0.28.0; this later analysis does not relabel their engine version.
