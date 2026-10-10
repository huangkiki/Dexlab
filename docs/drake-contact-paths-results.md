# Drake: contact-path results

[English](drake-contact-paths-results.md) | [简体中文](drake-contact-paths-results.zh-CN.md)

Native **Drake1.57.0 / CPU FP64 / SAP** now has initial incline evidence for three approximations across point/hydroelastic paths. These are fixed engineering configurations with **no tuning**, not an engine ranking or reliable task-coverage admission. [Protocol, identity and commands](drake-contact-paths-protocol.md) · [all evidence](evidence/drake-contact-paths/manifest.json) · [archive/replay](https://github.com/huangkiki/Dexlab/releases/tag/v0.55.0).

| SAP approximation / contact | Positive passes | Invalid positives | Valid rejected negative |
|---|---:|---:|---:|
| kLagged / hydroelastic (reused #117) | 6/9 | 0 | 1/1 |
| lagged-point | 0/9 | 0 | 1/1 |
| similar-hydroelastic | 5/9 | 2 | 1/1 |
| similar-point | 0/9 | 2 | 1/1 |
| sap-hydroelastic | 3/9 | 0 | 1/1 |
| sap-point | 2/9 | 1 | 1/1 |


| Configuration | Sliding timestep | Maximum momentum residual (N·s) |
|---|---:|---:|
| similar-hydroelastic | sliding-h0.001 | 1.135117926e-07 |
| similar-hydroelastic | sliding-h0.0005 | 2.131288136e-07 |
| similar-point | sliding-h0.001 | 1.376389105e-07 |
| similar-point | sliding-h0.0005 | 1.363337982e-07 |
| sap-point | sliding-h0.0005 | 1.698106175e-07 |


The unchanged momentum guard is1e-7 N·s. All five invalid positives remain in the denominator. Independent fresh processes exactly reproduce the selected Similar/hydroelastic1 ms and SAP/point.5 ms traces and contacts. Native parameter, clock, contact-sum and generalized force/torque checks pass; a complete explanation of their small momentum residuals remains [#165](https://github.com/huangkiki/Dexlab/issues/165). Invalid observations do not establish engine inability or physical accuracy.

Similar/hydroelastic passes two static cases and all three nominal-zero-friction cases; SAP/hydroelastic passes three static cases; SAP/point passes the1/.5 ms zero-friction cases. Both other point profiles pass none. Retained failures include lost support, force imbalance, translation, rotation and penetration; smaller timesteps do not uniformly improve outcomes. The point model's single pairwise contact and the hydroelastic surface model are different approximations; equal asset dimensions do not equate them. No-floor controls have valid observations and fail physical support as intended. Full displacement, velocity, acceleration, rotation, penetration, support and timing metrics are in the five `*-score.json` files; invalid observations have no physical acceptance metrics.

## Why the old Lagged sliding case stayed near rest

Three new observation-only replays reproduce every state, force, generalized force, count and timestamp from #117 **exactly**. The recorded pressure field gradient matches the authored compliant plane; actual face normals include small side faces, so a single-plane force decomposition cannot identify all contact components. The initial plane-only diagnosis is retained with that limitation.

The source's Lagged model caps tangential impulse using the **previous elastic normal impulse**, whereas the reported normal impulse uses the updated velocity. For each eligible face, with zero HC dissipation:

`fe0=A*p; k=A*(-grad_plane·n); fn=max(0,fe0-h*k*vn_next)`

`Ft=-μ*fe0*vt_next/sqrt(|vt_next|²+epsilon²)`

The offline [diagnostic](../scripts/diagnose_drake_lagged.py) reconstructs the regularization from mass/inertia and the source Delassus approximation, then sums every normal and tangential contribution. Maximum vector-force error is **2.365e-13 /1.871e-13 /3.930e-13 N** at2/1/.5 ms; this is an observed reconstruction error, not a changed acceptance tolerance. Mean downhill force stays near−.361 N; substituting updated normal magnitudes at those same observed states gives−.179/−.206/−.240 N. This counterfactual is an algebraic diagnostic, **not** a kSimilar simulation or a repaired trajectory.

The reconstruction supports attribution of the apparent excessive tangential support to the implemented lagged-friction response and actual surface geometry; it is not evidence of a force-sign adapter bug. It does not make the original failed incline accurate or prove a universal engine defect. Native per-face solved impulses/iterations remain unexposed; reconstructed quantities are labeled source-derived. [Lagged equations](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.cc) · [Delassus approximation](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_model.cc) · [numerical report](evidence/drake-contact-paths/lagged-formula-public-v1.json).

## Cost, recovery and scope

50 formal native processes completed115000 updates. Summed native-call wall time **4.678698 s**, observation time **3.961814 s**, setup **0.457769 s**, case wall **16.858062 s**. Both formal service receipts total44.645 s including startup/controller failure; peak225.70 MiB under8 GiB/four-core limits, no memory-high/OOM/CPU-throttle events. These timings include different costs and are not cross-engine throughput measurements. [Counters and pressure](evidence/drake-contact-paths/resources.json).

The log-name collision occurred before the second native launch; its record remains, and the continuation reuses the successful first case. The34-start/13360-update development ledger includes zero-step/probe admissions, three old-case observation replays and two independent numerical repeats. It is separate from formal and pinch budgets. Public metadata redactions are explicit in the archive; native observations are unmodified and engine-free rescoring is supported.

Fallback and enum aliases are not extra effective configurations here. This cohort covers **incline only**: basic-contact/collision/pinch/grasp and framework paths remain independently tracked in [#121](https://github.com/huangkiki/Dexlab/issues/121) and [#152](https://github.com/huangkiki/Dexlab/issues/152). Old #117 and historical cohorts retain their own protocols. Additional solver rows do not increase task types or trigger the next pinch workstream slice.

## All newly acquired cases

| Profile | Case | Verdict | Force RMSE (N) | Rotation (rad) | Penetration (m) |
|---|---|---|---:|---:|---:|
| lagged-point | static-h0.002 | fail / 失败 | 0.914017 | 0.0480727 | 0.000260203 |
| lagged-point | static-h0.001 | fail / 失败 | 0.569409 | 0.00616052 | 2.14521e-05 |
| lagged-point | static-h0.0005 | fail / 失败 | 0.483948 | 0.00435504 | 9.18007e-06 |
| lagged-point | sliding-h0.002 | fail / 失败 | 0.771351 | 0.053002 | 0.000228128 |
| lagged-point | sliding-h0.001 | fail / 失败 | 0.517506 | 0.0113026 | 2.03728e-05 |
| lagged-point | sliding-h0.0005 | fail / 失败 | 0.480135 | 0.00715864 | 6.04426e-06 |
| lagged-point | frictionless-h0.002 | fail / 失败 | 0.696747 | 0.278998 | 0.0010982 |
| lagged-point | frictionless-h0.001 | fail / 失败 | 0.408008 | 0.023033 | 0.000151765 |
| lagged-point | frictionless-h0.0005 | fail / 失败 | 0.216658 | 0.000904812 | 9.31601e-06 |
| lagged-point | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| similar-hydroelastic | static-h0.002 | fail / 失败 | 0.747741 | 0.00125539 | 3.69029e-05 |
| similar-hydroelastic | static-h0.001 | pass / 通过 | 1.91757e-07 | 0.000113872 | 8.47573e-06 |
| similar-hydroelastic | static-h0.0005 | pass / 通过 | 2.99865e-07 | 4.03214e-05 | 1.36893e-06 |
| similar-hydroelastic | sliding-h0.002 | fail / 失败 | 3.54752 | 3.13962 | 0.0034847 |
| similar-hydroelastic | sliding-h0.001 | invalid / 无效 | — | — | — |
| similar-hydroelastic | sliding-h0.0005 | invalid / 无效 | — | — | — |
| similar-hydroelastic | frictionless-h0.002 | pass / 通过 | 3.89324e-06 | 3.71514e-06 | 3.69029e-05 |
| similar-hydroelastic | frictionless-h0.001 | pass / 通过 | 3.90137e-06 | 1.8128e-07 | 8.47573e-06 |
| similar-hydroelastic | frictionless-h0.0005 | pass / 通过 | 3.78805e-06 | 5.16191e-08 | 1.36893e-06 |
| similar-hydroelastic | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| similar-point | static-h0.002 | fail / 失败 | 1.24196 | 0.579581 | 0.000752525 |
| similar-point | static-h0.001 | fail / 失败 | 1.20581 | 0.137582 | 0.000172008 |
| similar-point | static-h0.0005 | fail / 失败 | 0.841577 | 0.0200776 | 1.51416e-05 |
| similar-point | sliding-h0.002 | fail / 失败 | 5.87829 | 3.14122 | 0.00243922 |
| similar-point | sliding-h0.001 | invalid / 无效 | — | — | — |
| similar-point | sliding-h0.0005 | invalid / 无效 | — | — | — |
| similar-point | frictionless-h0.002 | fail / 失败 | 0.696747 | 0.278998 | 0.0010982 |
| similar-point | frictionless-h0.001 | fail / 失败 | 0.408008 | 0.023033 | 0.000151765 |
| similar-point | frictionless-h0.0005 | fail / 失败 | 0.216658 | 0.000904812 | 9.31601e-06 |
| similar-point | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| sap-hydroelastic | static-h0.002 | pass / 通过 | 7.53842e-07 | 0.00174914 | 6.98226e-05 |
| sap-hydroelastic | static-h0.001 | pass / 通过 | 7.71259e-07 | 0.00107974 | 3.85492e-05 |
| sap-hydroelastic | static-h0.0005 | pass / 通过 | 4.81753e-07 | 0.000570978 | 1.97884e-05 |
| sap-hydroelastic | sliding-h0.002 | fail / 失败 | 3.91991 | 3.13934 | 0.00262861 |
| sap-hydroelastic | sliding-h0.001 | fail / 失败 | 3.89722 | 3.13952 | 0.00118512 |
| sap-hydroelastic | sliding-h0.0005 | fail / 失败 | 7.20703 | 3.14113 | 0.000804191 |
| sap-hydroelastic | frictionless-h0.002 | fail / 失败 | 0.00481608 | 0.198409 | 3.88287e-05 |
| sap-hydroelastic | frictionless-h0.001 | fail / 失败 | 1.52561 | 3.1407 | 0.00241714 |
| sap-hydroelastic | frictionless-h0.0005 | fail / 失败 | 3.71195 | 3.1412 | 0.000987014 |
| sap-hydroelastic | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| sap-point | static-h0.002 | fail / 失败 | 0.339866 | 0.0458186 | 0.00395454 |
| sap-point | static-h0.001 | fail / 失败 | 0.253228 | 0.0210218 | 0.000479555 |
| sap-point | static-h0.0005 | fail / 失败 | 0.261055 | 0.00706249 | 0.000218955 |
| sap-point | sliding-h0.002 | fail / 失败 | 3.88151 | 3.13998 | 0.00133591 |
| sap-point | sliding-h0.001 | fail / 失败 | 6.09537 | 3.1399 | 0.000705559 |
| sap-point | sliding-h0.0005 | invalid / 无效 | — | — | — |
| sap-point | frictionless-h0.002 | fail / 失败 | 0.162925 | 0.0047957 | 0.00715774 |
| sap-point | frictionless-h0.001 | pass / 通过 | 2.82731e-06 | 0.000143903 | 6.14185e-05 |
| sap-point | frictionless-h0.0005 | pass / 通过 | 9.53597e-07 | 5.16191e-08 | 2.94452e-05 |
| sap-point | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |


Archive / 归档：`dexlab-drake-contact-paths-v1.tar.gz`，50023597 bytes，1074 files。SHA-256：`9e30d58c3ad3395a405dac335430e1e942e792e81463c0b0e4a40529c10b505c`。[Manifest / 清单](evidence/drake-contact-paths/archive.json)。
