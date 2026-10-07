# Arrival-phase sensitivity: the coarse endpoint survives the tested shifts

[English](impact-phase-results.md) | [简体中文](impact-phase-results.zh-CN.md)

**36 valid cases: 30 final-state passes, 14 joint passes; only 2 of 9 speed/step groups pass all four tested phases.** We reused nine published high-stiffness records and recorded 27 new phase offsets, without re-simulating the baseline.

The initial suspicion that the nearly exact 1 ms endpoint depended only on the original arrival alignment was **not supported**. Across all four tested phases and three speeds, 1 ms endpoints retain approximately machine-precision velocity/energy agreement. In contrast, energy errors vary from 0.5964–2.2464% at 0.5 ms and 0.05207–0.79007% at 0.25 ms. This does not identify the remaining numerical mechanism or establish a universally best timestep.

![Arrival-phase sensitivity](evidence/impact-phase/sensitivity.png)

The two complete joint-pass groups are 0.5 m/s with 1 ms and 0.25 ms steps. All four 1 m/s, 1 ms cases are **boundary-only geometric rejections**: stored overlap 0.0010000000000000009 m exceeds 1 mm by about 8.67e-19 m. We preserve strict acceptance and explicitly avoid interpreting this as physical excess. The boundary diagnostic never changes pass counts. Rounded table values must not be used to recount verdicts.

## All finite groups

| u (m/s) | h (ms) | Joint passes / 4 | All four | Worst velocity error (m/s) | Energy error range (%) | Overlap range (mm) |
|---:|---:|---:|---|---:|---:|---:|
| 0.5 | 1 | 4 | pass | 6.66134e-16 | 1.77636e-13–2.66454e-13 | 0.5–0.5 |
| 0.5 | 0.5 | 2 | fail | 0.0055542 | 0.596356–2.24636 | 0.490234375–0.515625 |
| 0.5 | 0.25 | 4 | pass | 0.00196743 | 0.0520681–0.79007 | 0.49730525–0.502826571 |
| 1 | 1 | 0 | fail | 1.33227e-15 | 1.77636e-13–2.66454e-13 | 1–1 |
| 1 | 0.5 | 2 | fail | 0.0111084 | 0.596356–2.24636 | 0.98046875–1.03125 |
| 1 | 0.25 | 2 | fail | 0.00393486 | 0.0520681–0.79007 | 0.9946105–1.00565314 |
| 2 | 1 | 0 | fail | 2.66454e-15 | 1.77636e-13–2.66454e-13 | 2–2 |
| 2 | 0.5 | 0 | fail | 0.0222168 | 0.596356–2.24636 | 1.9609375–2.0625 |
| 2 | 0.25 | 0 | fail | 0.00786973 | 0.0520681–0.79007 | 1.989221–2.01130629 |

## All cases

stiffness-* rows are reused. Final and joint verdicts remain separate; no failed cases are omitted.

| Case | u (m/s) | h (ms) | Phase | Velocity error (m/s) | Energy error (%) | Overlap (mm) | Final / joint |
|---|---:|---:|---:|---:|---:|---:|---|
| stiffness-10 | 0.5 | 1 | 0 | 4.44089e-16 | 1.77636e-13 | 0.5 | pass / pass |
| stiffness-11 | 0.5 | 0.5 | 0 | 0.0055542 | 2.24636 | 0.515625 | fail / fail |
| stiffness-12 | 0.5 | 0.25 | 0 | 0.00196743 | 0.79007 | 0.502826571 | pass / pass |
| stiffness-13 | 1 | 1 | 0 | 1.11022e-15 | 2.22045e-13 | 1 | pass / fail |
| stiffness-14 | 1 | 0.5 | 0 | 0.0111084 | 2.24636 | 1.03125 | fail / fail |
| stiffness-15 | 1 | 0.25 | 0 | 0.00393486 | 0.79007 | 1.00565314 | pass / fail |
| stiffness-16 | 2 | 1 | 0 | 2.66454e-15 | 2.66454e-13 | 2 | pass / fail |
| stiffness-17 | 2 | 0.5 | 0 | 0.0222168 | 2.24636 | 2.0625 | fail / fail |
| stiffness-18 | 2 | 0.25 | 0 | 0.00786973 | 0.79007 | 2.01130629 | pass / fail |
| phase-01 | 0.5 | 1 | 0.25 | 5.55112e-16 | 2.22045e-13 | 0.5 | pass / pass |
| phase-02 | 0.5 | 1 | 0.5 | 4.44089e-16 | 1.77636e-13 | 0.5 | pass / pass |
| phase-03 | 0.5 | 1 | 0.75 | 6.66134e-16 | 2.66454e-13 | 0.5 | pass / pass |
| phase-04 | 0.5 | 0.5 | 0.25 | 0.00202942 | 0.815062 | 0.49609375 | pass / pass |
| phase-05 | 0.5 | 0.5 | 0.5 | 0.00149536 | 0.596356 | 0.490234375 | pass / pass |
| phase-06 | 0.5 | 0.5 | 0.75 | 0.00502014 | 1.9879 | 0.502929687 | fail / fail |
| phase-07 | 0.5 | 0.25 | 0.25 | 0.000132263 | 0.0528912 | 0.49730525 | pass / pass |
| phase-08 | 0.5 | 0.25 | 0.5 | 0.00170716 | 0.680532 | 0.49914569 | pass / pass |
| phase-09 | 0.5 | 0.25 | 0.75 | 0.000130136 | 0.0520681 | 0.500986131 | pass / pass |
| phase-10 | 1 | 1 | 0.25 | 8.88178e-16 | 1.77636e-13 | 1 | pass / fail |
| phase-11 | 1 | 1 | 0.5 | 1.33227e-15 | 2.66454e-13 | 1 | pass / fail |
| phase-12 | 1 | 1 | 0.75 | 8.88178e-16 | 1.77636e-13 | 1 | pass / fail |
| phase-13 | 1 | 0.5 | 0.25 | 0.00405884 | 0.815062 | 0.9921875 | pass / pass |
| phase-14 | 1 | 0.5 | 0.5 | 0.00299072 | 0.596356 | 0.98046875 | pass / pass |
| phase-15 | 1 | 0.5 | 0.75 | 0.0100403 | 1.9879 | 1.00585937 | fail / fail |
| phase-16 | 1 | 0.25 | 0.25 | 0.000264526 | 0.0528912 | 0.9946105 | pass / pass |
| phase-17 | 1 | 0.25 | 0.5 | 0.00341432 | 0.680532 | 0.998291381 | pass / pass |
| phase-18 | 1 | 0.25 | 0.75 | 0.000260273 | 0.0520681 | 1.00197226 | pass / fail |
| phase-19 | 2 | 1 | 0.25 | 2.22045e-15 | 2.22045e-13 | 2 | pass / fail |
| phase-20 | 2 | 1 | 0.5 | 2.66454e-15 | 2.66454e-13 | 2 | pass / fail |
| phase-21 | 2 | 1 | 0.75 | 1.77636e-15 | 1.77636e-13 | 2 | pass / fail |
| phase-22 | 2 | 0.5 | 0.25 | 0.00811768 | 0.815062 | 1.984375 | pass / fail |
| phase-23 | 2 | 0.5 | 0.5 | 0.00598145 | 0.596356 | 1.9609375 | pass / fail |
| phase-24 | 2 | 0.5 | 0.75 | 0.0200806 | 1.9879 | 2.01171875 | fail / fail |
| phase-25 | 2 | 0.25 | 0.25 | 0.000529052 | 0.0528912 | 1.989221 | pass / fail |
| phase-26 | 2 | 0.25 | 0.5 | 0.00682864 | 0.680532 | 1.99658276 | pass / fail |
| phase-27 | 2 | 0.25 | 0.75 | 0.000520545 | 0.0520681 | 2.00394452 | pass / fail |

## Evidence and reproduction

The [frozen protocol](impact-phase-protocol.md) and [manifest](evidence/impact-phase/manifest.json) were committed at d4ae95dd35580728dca85e5b47408f0410b174d6 and [preregistered](https://github.com/huangkiki/Dexlab/issues/103#issuecomment-6048317646) before the new batch. Only the initial free-flight gap changes: x1=-0.06 m and x2=0.06+u*h*alpha m. Masses 1 kg each, radius 0.05 m, stiffness 1000000 s⁻², zero damping, Euler/Newton100/tol1e-12, constant impedance0.9, no gravity/friction/spin/actuation; duration0.2 s and final window0.02 s. Official MuJoCo3.15.0 CPU FP64; exact runtime identity and compiled settings are checked.

[Results JSON](evidence/impact-phase/results.json) contains every force peak, signed impulse/error norm, contact duration, onset diagnostic, timing, file hash and group extrema. Force samples use the pre-integration epoch; corresponding post-step states are one step later. First sampled contact occurs approximately0–0.75 ms after the ballistic arrival reference in this set. These are sampled diagnostics, not a validated continuous force waveform. All27 prior stiffness-study result rows were re-scored identically before selecting the nine baselines.

Download impact-stiffness-raw-v1.zip from [v0.44.1](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.1) and impact-phase-raw-v1.zip from [v0.44.2](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.2). Check [archive hashes](evidence/impact-phase/archive.json), extract into separate directories containing manifest.json and case subdirectories, then:

```bash
python -m dexlab.impact_phase --baseline stiffness --input phase --output rescored.json
python scripts/plot_impact_phase.py --input rescored.json --output sensitivity.png
```

Scientific fields should match; observed scoring wall time varies. No engine run is needed for rescoring. Published baseline runtime, manifest and trace/XML hashes are bound before combining the campaigns.

## Cost, scope and next question

The new27-case campaign took0.07986 s; cumulative setup0.01715 s, native stepping0.01529 s, observation0.02102 s, case totals0.07461 s. Combined scoring took0.05886 s. Bounded service times were0.882 s simulation and0.376 s scoring, excluding installation/release checks. Intel Core i9-14900K;16 GiB, two CPUs,128 tasks, zero swap,1800 s enforced limit and exclusive research window. Baseline timings come from a prior campaign; tiny unrepeated observations do not establish speed rankings.

The finite-phase criterion strengthens the previously single-phase evidence but is not a probability or general robustness claim. A successful endpoint still does not validate transient contact forces or calibrated grasp behavior. For grasping, retain separate geometry and motion budgets and report sensitivity before selecting a configuration. The next scientific question is whether a discrete undamped contact model explains the persistent 1 ms endpoint behavior; that mechanism needs an independently derived prediction before further tests. No engine-superiority or real-material-accuracy conclusion follows here.
