# Wuji contact prediction diagnostics

[English](README.md) | [简体中文](README.zh-CN.md)

Predict where a held object will move, and whether each finger will remain in loaded contact. This entry evaluates **hold and constant-velocity baselines on six existing synthetic Wuji v4 episodes**. It does not contain a learned model, launch physics or train a policy.

All six episodes were imported and independently rescored successfully. Hold/constant-velocity diagnostics and 14 analytical regressions passed their implementation checks; this does not qualify an action-conditioned model. [Full machine-readable report](../../docs/evidence/contact-response/baselines.json). [Issue #261](https://github.com/huangkiki/Dexlab/issues/261) retains model admission, fresh native repetitions/interventions and control-benefit assessment. Existing release/unload runs are different commands, not a qualified causal trio. The [Wuji qualification result](../wuji-contact/README.md) remains the source task result.


## Observed baseline errors

At 100 ms horizon, the 100 origins per episode run from 1.20 to 3.18 s; targets can extend to 3.28 s, including the start of release/unload. These are correlated windows from single development episodes, not repeated trials.

| Source case | Hold position RMSE (mm) | Constant-velocity RMSE (mm) |
| --- | ---: | ---: |
| hold-release | 0.0491 | 0.0221 |
| unload-index_finger | 0.0484 | 0.0181 |
| unload-thumb | 0.0505 | 0.0232 |
| open | 1342.0424 | 49.2953 |
| no-contact | 1342.0424 | 49.2953 |
| zero-friction | 1326.2571 | 49.2953 |

Constant velocity reduces short-horizon displacement error here, but neither contact-persistence baseline forecasts loss. For commanded-release/unload origins at 100 ms horizon, the three grasp cases contain respectively 5/6, 6/6 and 5/5 index/thumb loss-containing windows, all missed by both baselines. Those counts overlap and are not independent physical events. Constant velocity also omits gravity: in the free-fall controls its approximately 49.2953 mm error matches the semi-implicit reference `g*h*(h+dt)/2` for `h=0.1 s`, `dt=0.0005 s`, `g=9.81 m/s²`.

[Complete per-phase, per-pad, per-horizon data](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/contact-response/baselines.json) retain both the original task scores and the prediction diagnostics. SHA-256: `ae888c5cd970f6f9ab694741203484c30c00a049ab7c92be37350b55ca1d0c98`. A rerun in an exclusive execution window produced the same report byte-for-byte; this is offline reproducibility, not a new native repeat. Native causal response and control benefit remain unevaluated.

## Run offline

Use Linux CPython 3.12 and NumPy 2.5.2, with the verified [Wuji evidence bundle](https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html). No MuJoCo, Torch or GPU is imported by these commands. `BUNDLE` is the extracted directory containing `runs/`.

```bash
python demos/contact-response/baselines.py \
  --bundle "$BUNDLE" --output response-baselines.json
```

The command verifies the pinned bundle index and each selected manifest/observation hash, reruns the corrected independent Wuji scorer, checks state continuity and imports only the six v4 cases. It refuses incomplete or numerically inconsistent records. Physical-array fingerprints remove identical episode copies despite recompression, timing changes or quaternion sign changes. Duplicate paths are reported; the surviving whole episode remains in a single `diagnostic-only` partition. There is no train/test split or claim of independent holdouts, and historical v1–v3 failures remain in the original bundle.

The frozen `protocol.json` selects 20, 100 and 200 ms horizons with a 20 ms origin stride. These are descriptive horizons, not tuned acceptance thresholds. Each episode is reported separately. Overlapping windows and shared acquisition trajectories are correlated; their count is not a count of independent trials. Geometric distances are available only for contacts actually reported by the native solver; absence is not a measured positive gap.

## Input and output epochs

| Field | Units / frame | Availability |
| --- | --- | --- |
| 20 joint positions / rates | rad / rad/s, source order | Before solve `i` |
| Object position / linear velocity | m / m/s, world | Before solve `i` |
| Object quaternion / angular velocity | wxyz / rad/s, angular velocity local | Before solve `i` |
| Joint target | rad, position command | Before solve; baselines ignore actions |
| Requested torque | N m, before clipping | Control output, distinct from measured actuator force |
| Pad normal loads | N, sum per pad–object pair | Latest completed solve `i-1` only |
| Future state and contact labels | Same units, solve `i+h` | Scoring only; never fed into prediction |

Constant velocity extrapolates translation and integrates the local angular rate on the right of the quaternion. Hold copies the origin pose. Both retain the previous completed pad-contact label, using the unchanged 0.02 N v4 normal-load threshold. Opposing loads can cancel in the net force, so net force is not the contact label. Neither baseline anticipates a contact transition.

Reports separate assisted preparation, settling, holding and commanded release/unload origins. Per pad and horizon they split windows into establishment, sustained contact, loss, absence and loss/recontact switching, including transitions inside a window. They report position and orientation errors, endpoint contact confusion counts and establishment/loss event counts. A zero precision/recall denominator is `null`, not success. Windows crossing stage boundaries retain their declared origin stage; no aggregate score substitutes for per-episode evidence.

## Compare a visible prefix

`prefix.py` compares **every tick** before a declared intervention, including the state at onset and only commands/solve observations strictly before onset. It checks position, geodesic orientation, velocity, requested and measured controls, applied inputs, pad loads and native contact identities/frames/wrenches with separate units. A changed native contact count or ordering rejects compatibility.

```bash
python demos/contact-response/prefix.py \
  --baseline "$BASELINE" --repeat "$REPEAT" --intervention "$INTERVENTION" \
  --protocol frozen-prefix-protocol.json --output visible-prefix.json
```

This future protocol must supply `intervention_start_s`, `horizon_s`, a nonempty `tolerance_basis` and every tolerance named in `prefix.UNITS`. No numeric native tolerance defaults are supplied: the upstream 1 mm, action +0.15 and noise-ratio thresholds were defined for another robot/environment. The input must be frozen and justified before new response outcomes, together with the native matrix and finite budget required by #261.

Even a compatible visible prefix produces **`UNIDENTIFIED`**. The current source record format does not establish fresh-process identity or complete compiled-model identity, hidden solver caches are not observable, and a calibrated repeated-response envelope and predeclared effect/direction thresholds are still missing. Maximum observed intervention/repeat displacement is diagnostic only. This entry does not convert a lower prediction error into physical task success or a control benefit.

The design borrows continuous baseline/repeat/intervention comparison from [Ref2Dex-agent](https://github.com/hitsz-oyx/Ref2Dex-agent/blob/31cdb9ac759838b83d62bbc0addfd5cf28f3dff4/src/task/dex-contact-mbrl/tools/audit/compare_serial_response.py). It additionally requires the entire unit-separated visible prefix, rather than qualifying only the object position at the intervention tick. No external weights or assets are redistributed here.
