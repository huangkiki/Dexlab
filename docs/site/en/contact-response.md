# Predicting contact loss from a qualified grasp

This prepared entry asks a smaller question than policy optimization: **can a predictor tell where the object moves and which finger loses contact?** It uses the six existing [synthetic Wuji v4 episodes](wuji-contact.md), including the failed open/no-contact/zero-friction controls. No learned model or new native intervention is qualified yet.

The six-episode offline report is complete, with all source integrity and numerical-balance checks passing and zero duplicate copies in this selected cohort. The implementation also passed 14 analytical regressions. The two baselines use only the origin state and the last completed contact observation. Future labels enter scoring only. Existing videos and overlapping windows do not add independent repeats or held-out episodes.


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

## Reproduce the offline diagnostics

After following the [Wuji bundle download](wuji-contact.md#rescore-without-installing-a-simulator), include the new entry in the sparse checkout and run with the same isolated offline dependencies:

```bash
git sparse-checkout add demos/contact-response
uv run --offline --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python demos/contact-response/baselines.py \
  --bundle downloads/wuji-contact-v1 --output response-baselines.json
```

The importer checks pinned manifest/data hashes, independent numerical consistency and complete episode fingerprints. It separates copied/recompressed episodes before evaluation. All accepted data remain diagnostic; no model is fitted and no generalization claim is made.

| Diagnostic | What it measures | Limit |
| --- | --- | --- |
| Hold / constant velocity | World position error and orientation error at 20, 100 and 200 ms | Neither baseline uses actions or predicts a contact switch |
| Contact persistence | Per-finger normal load above the original 0.02 N threshold | Opposing loads can cancel in net force; missing contacts do not measure positive gaps |
| Establishment / sustain / loss / switching | Endpoint confusion and events throughout each forecast window | Overlapping windows are correlated, reported separately by whole episode |
| Complete visible prefix | Position, angle, velocity, control, external inputs and native contact differences in separate units | A compatible prefix does not prove a causal intervention or identical hidden solver state |

Preparation with external support remains separate from unsupported holding. At forecast origin `i`, the pose/velocity are pre-solve values, and the most recent available contact is from completed solve `i-1`. Constant angular velocity is integrated in the recorded local frame; quaternion components are not treated as angular distances.

The prefix command requires a future frozen protocol with every field-specific tolerance and its basis. It always retains `UNIDENTIFIED` for causal response because these historical records do not establish fresh-process/complete-model identity or a qualified repeat envelope. [Detailed commands and observation contract](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-response/README.md).

[Issue #261](https://github.com/huangkiki/Dexlab/issues/261) retains candidate model compatibility, prospective perturbation/horizon/threshold choices, finite native repeats, physical prediction and control benefit. Lower loss, a visible gradient or a passing source grasp cannot stand in for those outcomes. This entry adds no completed engine task and does not alter [Wuji contact qualification](wuji-contact.md).
