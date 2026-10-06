# Native tangent identification — preregistered development protocol

[English](TANGENT_IDENTIFICATION.md) | [简体中文](TANGENT_IDENTIFICATION.zh-CN.md)

This synthetic BOX/PLANE fixture tests the conditional `D = c L` relation in
[DAMPING_REFERENCE](DAMPING_REFERENCE.md). It does not calibrate hardware or rank engines.
Protocol and engineering tolerances were fixed before native execution.

- Official SuperDex 1.0.0 FP64, existing backward-Euler native adapter; no engine changes.
- 40 mm cube, 0.2 kg, gravity 9.81 m/s², zero friction; existing penalty 12,500,000,
  threshold 1 µm and smoothing half-distance 0.5 µm; normal damping 10 s/m on both actors.
- Nine fresh scenes: preloads 2, 4, 6 N, at steps 0.5, 0.25, 0.125 ms. Execute by
  descending step then ascending load. No selected seeds or reruns of failures.
- Each scene: 0.4 s settling, 0.4 s fitting, 0.4 s smaller-amplitude validation.
  Apply world-COM force with gravity compensation. Add 20 and 35 Hz sine tones,
  each with amplitude 2% of preload for fitting and 1% for validation. Both windows
  contain integer periods. The second window continues the state; it is not an
  independent replicate, and no population confidence interval is claimed.
- Fit `Fz = intercept + K*depth + D*inward_speed`. Center and scale the two
  predictors; reject condition number above 20 or rank below 3. Report pre-step
  and post-step state fits separately. Post-step is the backward-Euler hypothesis;
  do not select the better epoch afterwards. The force query follows the solved step;
  internal contact linearization timing is not directly observable.
- Require the last 0.1 s settling speed ≤10 µm/s, height std ≤1 µm and mean
  support error ≤1%. Require retained and constant contact count during excitation,
  normal-only motion, aggregate/per-contact force agreement ≤1e-7 N, and every-step
  momentum residual ≤1e-5 N. Native convergence flags alone cannot validate data.
- Fit/prediction RMS limits are 5% of the per-tone command amplitude. Conditional
  damping error tolerance is 10% of `10*L` Ns/m; amplitude sensitivity tolerance
  is also 10% of that reference. These are declared numerical diagnostic tolerances,
  not measured material uncertainty. Report invalid data and rejected hypotheses.
- Smaller-step results are sensitivity evidence, not convergence proof. Fitted
  coefficients include discretization and contact-geometry effects. Hidden native
  contact combination laws, clipping and regularization remain unobserved.

Run in the configured bounded resource envelope:

```bash
python -m dexlab.contact_tangent_run OUTPUT
```

All measured poses, velocities, force ledgers, contact records, native actor/solver
readbacks, source hashes and failed outcomes are retained. Diagnostic elapsed time
includes observation and file I/O; it is not an isolated solver-speed comparison.

## Controlled solver follow-up

All nine default-solver runs failed the fixed 1e-5 N momentum bound (observed
0.00131–0.00194 N). The native absolute/relative tolerances read back as 0.001/1e-6.
These outcomes are retained. A second preregistered batch changes only those two
solver tolerances to 1e-9/1e-9; iteration cap remains 100. Use `--tight-solver`.
No physical parameter, forcing schedule or acceptance tolerance changes.

## Results and interpretation

**Default solver: 0/9 valid. Tighter solver: 9/9 valid**, with identical physical inputs,
initial states, native geometry and actor/solver readbacks except the declared two tolerances.
Every case was rescored from archived contact records and state arrays. Peak momentum
residual changes from 0.001312–0.001939 N to 9.91e-10–1.88e-9 N, without relaxing the
1e-5 N gate. This identifies solver termination as a controlled contributor to the
first batch's inconsistency; it is not a claim about default settings on other tasks.

In all nine valid cases, post-step local fits, smaller-amplitude prediction and the
conditional cL comparison meet the frozen limits. D is close to 20/40/60 Ns/m at
2/4/6 N. Pre-step pairing gives approximately 2.5/5/10 Ns/m larger damping as the
step increases from 0.125/0.25/0.5 ms. Thus a state/force epoch mismatch can look like
material damping. Both fits and all rejected records are published.

![All-case damping and momentum diagnostics](../../docs/evidence/tangent-identification-v1.png)

| Preload / 预载荷 (N) | Step / 步长 (ms) | K (N/m) | D (Ns/m) | Prediction RMS / 预测RMS (N) |
|---|---|---|---|---|
| 2 | 0.5 | 19999.853 | 19.98825 | 0.00007547 |
| 4 | 0.5 | 19998.972 | 39.98297 | 0.00022888 |
| 6 | 0.5 | 19997.629 | 59.98624 | 0.00039416 |
| 2 | 0.25 | 19999.902 | 19.98509 | 0.00007850 |
| 4 | 0.25 | 19999.107 | 39.97798 | 0.00023685 |
| 6 | 0.25 | 19997.805 | 59.97936 | 0.00040630 |
| 2 | 0.125 | 19999.914 | 19.98318 | 0.00008042 |
| 4 | 0.125 | 19999.167 | 39.97539 | 0.00024156 |
| 6 | 0.125 | 19997.889 | 59.97581 | 0.00041325 |

These measurements support the conditional load-dependent local law for this fixture.
They do not prove global trajectory equivalence, a physically accurate material, or
that the prior unloading defect is repaired. Full common-material calibration and
hardware reference remain unresolved. Three step levels are sensitivity evidence,
not an asymptotic convergence study. No confidence interval is manufactured from
these prescribed deterministic cases.

## Offline reproduction

The [v0.35.0 raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.35.0/contact-tangent-evidence-v1.tar.gz)
contains both batches, including all nine rejected runs.
The committed [all-case summary](../../docs/evidence/tangent-identification-v1.json)
and report script reproduce the figure. After unpacking the archive:

```bash
python -m dexlab.contact_tangent_verify tight/study/load-2-dt-500us
python demos/contact-benchmark/tangent_report.py default/study tight/study --output OUTPUT
```

Verification reads contact records again, checks archive hashes, reconstructs per-step
force/count/status arrays and checks momentum. A default-batch verification correctly
returns exit 1; it is not a corrupt/missing record.
