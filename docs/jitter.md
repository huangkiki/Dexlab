# Jitter and contact-interruption diagnostics

[English](jitter.md) | [简体中文](jitter.zh-CN.md)

The offline analyzer reads existing physics-step archives. It does not run a controller, step a scene, change engine parameters, or replace grasp acceptance.

## Run

After [installation](installation.md) and a completed or interrupted recording:

```bash
.venv/bin/python -m dexlab.jitter demos/apple-stem-grasp/runs/latest-mujoco-sdf
.venv/bin/python -m dexlab.jitter demos/apple-stem-grasp/runs/latest-superdex-sdf
```

Each command writes `jitter-diagnostics.json` in that run directory and prints the same JSON. `--output path.json` changes the destination. Input files are read-only. A successful command means that a report was generated, not that the grasp or data quality passed. Malformed archive structure raises an error; incomplete traces remain visible in the report.

Inputs are `engine.json`, `sdf-dynamics.npz`, and, when available, `sdf-contacts.npz`. MuJoCo also needs its matching raw `model.mjb` or lossless model archive to resolve body IDs, loaded without stepping; SuperDex IDs come from `engine.json`. These are full local run artifacts, not just the smaller packaged acceptance summaries. The report hashes its inputs and analyzer source. No dependency on the separate model-audit feature is required.

## Signals, units, and definitions

The default hold window is **[11, 14) seconds**. Sampling comes from `engine.json`: currently 2,000 Hz for MuJoCo and 500 Hz for SuperDex, independent of video frame rate. The report includes expected, unique, missing and duplicate samples, off-grid timestamps, observed spacing, and contiguous unknown intervals. Both recorders label a row by step start; position/velocity are read after integration, while contact forces describe that solved step.

| Signal | Definition | Unit |
|---|---|---|
| `apple_origin_world_position` | Apple body-origin position in world coordinates | m |
| `apple_origin_wrist_relative_position` | Apple origin expressed in the measured wrist frame | m |
| `apple_com_world_velocity` | Recorded apple linear/COM velocity in world coordinates | m/s |
| `hand_force_on_apple_world` | Net world force from the right hand on the apple | N |
| Per-pad `load` | Sum of magnitudes of recorded point-force vectors for that pad | N |

For finite observed vector samples `x`, `mean_components = mean(x)`, `rms_norm = sqrt(mean(||x||²))`, and `peak_norm = max(||x||)`. Centered metrics apply the same formulas to `x - mean(x)`. Scalar pad loads use a single component. Raw force RMS includes the support load; centered force RMS measures variation around it. Position variation includes slow drift: no detrending, frequency filtering, spectral estimate, or cumulative material-point slip is implied.

Statistics use equal weights at the declared fixed timestep. Missing, duplicated, malformed or non-finite samples are omitted, never interpolated or replaced by zeros; each signal reports valid/unknown counts. No observations yields JSON `null` metrics. Partial statistics can be biased and must be read with their coverage.

## Contact interruptions and unavailable data

The existing verifier requires each pad's summed point-force magnitudes to exceed **0.1 N** throughout the hold. Diagnostics retain that boundary and report contiguous observed bins at or below it. This is low-load support, not proof of geometric separation or a new pass/fail rule.

- An explicit valid zero-force row is observed zero load.
- A missing dynamics step or an absent per-pad ledger row is **unknown**, not zero. The sparse ledger has no per-finger completeness marker.
- Contact vectors are reconciled against the independently recorded net hand force using the verifier's `atol=1e-8 N`, `rtol=1e-5`. A mismatch or invalid contact payload makes that step unknown for both pads. Missing ledgers or unassignable contact timestamps make all contact bins untrusted.
- Multiple contact points are aggregated per pad and step. Load sums magnitudes, while reconciliation sums vectors. Opposing forces therefore do not falsely imply zero grip load.
- Unknown bins split low-force episodes. An episode touching an unknown bin or window edge is marked censored on that side. Durations are observed sample counts times `dt`, not exact continuous event times. Bounds on total low-force duration assign unknown bins first to high load, then to low load; they concern sampled bins and do not certify substep continuity.

Reconciliation cannot detect every balanced omission of contact rows. Even a fully covered report relies on the recorder being intact. No normal-force diagnostic is inferred from the SuperDex ledger's placeholder normal column.

## Energy boundary

`energy.available` is false for these archives. They lack complete system velocities/inertias, actuator work, and dissipated/contact energy needed for a full energy balance. An actuated, frictional, damped system is not expected to conserve mechanical energy. A momentum-balance pass is not evidence of energy conservation.

## Baseline observations and validation

Offline analysis of the existing `unilab-mujoco` / `unilab-superdex` default run archives on 2026-09-29 gives the following centered metrics. These are the baseline task configurations with different timesteps, friction, and drives; they are not a controlled engine-accuracy or speed ranking.

| Hold metric | MuJoCo 3.11.0 | SuperDex FP64 1.0.0 |
|---|---:|---:|
| Unique / expected samples | 6,000 / 6,000 | 1,500 / 1,500 |
| Wrist-relative position RMS / peak | 0.07858 / 0.14479 mm | 0.01151 / 0.02367 mm |
| COM velocity RMS / peak | 0.17056 / 0.80133 mm/s | 0.00942 / 0.03141 mm/s |
| Net hand-force RMS / peak | 0.007534 / 0.047451 N | 0.000167 / 0.000460 N |
| Observed low-force duration, thumb / index | 0 / 0 s | 0 / 0 s |
| Unknown contact bins, thumb / index | 0 / 0 | 0 / 0 |

Tests cover stationary loads, analytic oscillations, smooth drift, explicit zero load, threshold equality, missing/duplicate/off-grid steps, incomplete ledgers, invalid values, multiple contacts, coordinate transforms and input immutability. These tests validate measurement behavior; full physical acceptance remains the separate [SDF verifier](../demos/apple-stem-grasp/src/verify_sdf_grasp.py). Submission still runs both complete 14-second backend episodes under unchanged thresholds.

[Implementation](../src/dexlab/jitter.py) · [Tests](../tests/test_jitter.py) · [Research focus](research-focus.md)
