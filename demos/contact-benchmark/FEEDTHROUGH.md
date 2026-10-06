# Applied-load dependence versus material response

[English](FEEDTHROUGH.md) | [简体中文](FEEDTHROUGH.zh-CN.md)

**Measured result:** nine low-impedance MuJoCo records pass the frozen data-validity checks; all nine high-impedance records fail settling. A small regression residual cannot turn the latter into valid material identification. This is a synthetic development fixture, not hardware calibration or an engine ranking.

![Validity, prediction and epoch diagnostics](../../docs/evidence/feedthrough-v1.png)

| Fixed profile | Valid / declared | Accepted pre-step fit | Limitation |
|---|---:|---|---|
| `solimp=0.001`, `solref=-24975 -49.95` | 9/9 | K≈19920.239 N/m; D≈39.84048 Ns/m; applied-load gain≈0.00398804 | Local response; no claim of global material equivalence |
| `solimp=0.9`, `solref=-2500 -5` | 0/9 | Not accepted | Settled-speed and settled-depth checks fail at 0.4 s |

The accepted augmented model predicts the smaller-amplitude force record with maximum RMS 2.19e-15 N. This is numerical agreement, not measurement uncertainty. The unchanged engineering reference remains K=20000 N/m, D=40 Ns/m with zero direct load dependence. Earlier transient, transfer and unloading failures remain failures. The low-impedance basic model also meets this experiment's prediction tolerance; tiny augmented residuals do not establish a practically significant accuracy improvement or a learned controller.

## Question and frozen protocol

[Preregistration](https://github.com/huangkiki/Dexlab/issues/10#issuecomment-6016384683) precedes the batch. Does an applied-load term explain a response that a spring-damper-only fit confounds? Fit both `F = a + K*depth + D*inward_speed` and `F = a + K*depth + D*inward_speed + alpha*applied_load`. MuJoCo's [documented approximate scalar constraint model](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters) motivates this question; it is not a proof of the coupled four-contact model.

- Official MuJoCo 3.15.0, Euler/Newton, 100 iterations, tolerance1e-10; installed payload checked against the official wheel and current stable inventory at batch freeze. No engine changes.
- A free 0.2 kg, 40 mm cube, zero friction, gravity9.81 m/s²; net downward load is applied at its COM with gravity compensation. Actual native states and forces are recorded. No pose overwrite or servo.
- Two unchanged profiles from the earlier response-cost study; high then low, descending timestep0.5/0.25/0.125 ms, ascending preload2/4/6 N:18 fresh serial scenes.
- Each1.2 s comprises0.4 s settling,0.4 s two-tone20/35 Hz at2% preload per tone, then0.4 s at1%. Validation continues the same trajectory; it is not an independent replicate or population holdout.
- Centered/scaled full-rank regression, condition≤20; fit and validation RMS≤5% of per-tone amplitude. Reuse unchanged tangent data checks: momentum≤1e-5 N, ledger≤1e-7 N, settled speed≤1e-5 m/s, settled height std≤1e-6 m, load balance≤1%, normal translation and retained contact. These are engineering diagnostics, not measured material tolerances.
- **Pre-step** state is the declared solved-force epoch. Post-step is reported separately without choosing the better result. All18 momentum residuals are≤6.00e-11 N; this does not override high-profile settling failures.

## Reproduce and audit

Within the documented bounded experiment environment, using the explicit MuJoCo qualification profile:

```bash
DEXLAB_MUJOCO_PROFILE=qualification-3.15.0 python -m dexlab.contact_feedthrough_run NEW_DIRECTORY
python demos/contact-benchmark/feedthrough_report.py RECORD_DIRECTORY --output REPORT_DIRECTORY
```

The first command requires the official engine; the second reads full raw arrays/contact ledgers without importing it. External stable-version, official-wheel and resource admission are still required; the runner itself is not a resource limiter. Diagnostic wall time includes readback/I/O and is not a performance benchmark.

[All18 independently rescored results](../../docs/evidence/feedthrough-v1.json) include invalid cases and both epochs; [figure provenance](../../docs/evidence/feedthrough-v1.provenance.json) binds the plot to its data. The original standalone driver, source snapshots, raw contacts and failed cases are retained. The integrated scorer recomputes regressions rather than trusting saved verdicts. Six new tests cover known coefficients, deficient excitation, invalid settling despite good prediction, epoch effects, coherent force injection and archive/parameter/warning tampering. Original native measurements were not rerun to manufacture successful records.

The integrated runner was additionally checked on one low-impedance4N/0.5ms reproduction: every saved state array, raw contact row and independent score exactly matched the original case. This implementation check is outside the18-case cohort, not an extra success trial.

Issue10 remains open: common-material calibration, unloading behavior and unobservable pair-law fields remain unresolved; hardware measurements belong to issue6. This report is prepared for the next release; publication must be verified separately.
