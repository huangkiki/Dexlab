# Audit G1 landing contacts

[English](README.md) | [简体中文](README.zh-CN.md)

Check whether a saved geometric intersection and a recorded contact force refer to the same state, geometry and physics substep. The audit preserves the upstream task score and never substitutes a CPU-solved force for the recorded GPU force.

The fixed reference now passes its native support/recorder probe and **three complete policy repeats on an RTX 4090**. Each repeat covers 571 controls, 2284 physics substeps and the five-second final hold. All three pass the unchanged upstream `strict_v3` and legacy gates. Independent reconstruction finds no nonfoot penetration or loaded nonfoot contact in these new records.

![Complete G1 native-geometry replay with recorded contact forces](../../docs/evidence/landing/replays/policy-repeat-1/preview.gif)

Full-duration, original-speed replay of repeat 1: all 572 saved boundaries, including both endpoints. The native model uses four 5 mm contact spheres per foot, not cosmetic foot meshes. Only display lighting, color and camera change; no dynamics are rerun. [50 Hz video 1](../../docs/evidence/landing/replays/policy-repeat-1/replay.mp4) · [video 2](../../docs/evidence/landing/replays/policy-repeat-2/replay.mp4) · [video 3](../../docs/evidence/landing/replays/policy-repeat-3/replay.mp4) · [force curves](../../docs/evidence/landing/replays/policy-repeat-1/curves.svg).

[Complete native records (17.75 MB ZIP)](../../docs/evidence/landing/native-v1.zip) · [batch report](../../docs/evidence/landing/native-summary.json) · [archive identity and offline verification](../../docs/evidence/landing/native-bundle.json) · [asset lineage](../../docs/evidence/landing/asset-lineage.json).

| Same-seed fresh process | Upstream strict gate | Final two-second horizontal drift | Exported / raw contact samples |
| --- | --- | --- | --- |
| 1 | Pass | 1.416 mm | 17,014 / 17,014 |
| 2 | Pass | 1.207 mm | 17,013 / 17,013 |
| 3 | Pass | 1.335 mm | 17,015 / 17,015 |

The support fixture measures 98.69% of body weight as average vertical support, with positive loading on both feet. The maximum difference between summed contact force and root constraint force is 0.000835 N; recorder trajectory differences satisfy the original limits. The fixture uses horizontal/attitude stabilization with zero vertical assistance, and is absent from policy evaluation.

Across 6,428 substeps with the same shared native-pair set at both poses, recorded distances are closer to **pre-step geometry in 6,427**. Maximum pre-step distance error is 2.38e-7 m; the post-step error reaches 0.0202 m. This supports a contact/pose timing distinction for these records. It does not explain the historical anomaly below. Three same-seed repeats are not random-initial-condition reliability trials; the requested two-sided 95% binomial-model interval for 0/3 failures is [0, 0.7076], without an established independence claim.

Each repeat has 74 scalar-joint actuator-force samples exactly on a saved CPU-model limit and none outside it. Individual actuator/control limits are disabled; the joint limits are separate. The GPU clamp branch and whole-system COM momentum are unavailable, so neither saturation causality nor a whole-body momentum-balance pass is claimed. Raw controls and generalized forces remain in the archive.

## Recompute the new native records

The archive preserves all three complete native records, models, support-probe evidence, the original budget ledger, resource receipts and licenses. Its 99 manifest entries passed byte/CRC checks, and all three geometry audits reproduced exactly after extraction. The ZIP SHA-256 is `70c7a6f6c4119a13cb3d20b33348d859a8e89dc00cf3aad35cc17a1098772802`. Use a fresh `OUT` directory and the recorded MuJoCo 3.15.0 interpreter with this checkout on `PYTHONPATH`:

```bash
python -m zipfile -e docs/evidence/landing/native-v1.zip "$OUT"
"$NATIVE_PYTHON" -m dexlab.landing_audit "$OUT/policy-repeat-1" \
  --protocol "$OUT/protocol.json" --geometry --output "$OUT/recomputed-1.json"
"$NATIVE_PYTHON" -m dexlab.landing_replay "$OUT/policy-repeat-1" \
  --protocol "$OUT/protocol.json" --output "$OUT/new-replay-1"
```

Repeat with cases 2 and 3 for complete coverage. Audit uses NumPy and native MuJoCo; replay additionally uses Matplotlib, Pillow, system FFmpeg and a configured rendering context. Historical absolute invocation paths are retained for byte identity; they are not paths to execute. `landing_report` regenerates the batch report from the original campaign layout and ledger. All outputs refuse overwrite.

The 38 source mesh blobs match the pinned official Unitree repository. The fixed upstream URDF differs from the official file in six joint effort/velocity limits, two palm attributes, the mid360 transform and material inlining. These frozen simulation inputs are retained, not presented as verified hardware settings. The [notice](NOTICE) and bundled license files cover converted models and evaluated, cropped/padded reference samples; no checkpoint or original motion NPZ is redistributed.

## Historical discrepancy remains a separate result

The public first-run archive contains 571 control steps and 2284 physics substeps. DexLab independently matched all 29 joint names and control-boundary states: joint positions agree exactly, and the largest root angular-velocity difference is 2.39e-6 rad/s. The author's stored geometric classification flags frame 119 (2.38 s); the recorded nonfoot loaded-pair count is zero throughout. This rules out a simple joint-order mismatch **for this archive**. It does not establish the contact epoch or explain the discrepancy. The archive lacks the native model and complete contact-pair stream. The author's separate passing reevaluation remains a separate result.

## Recompute the historical public record

Use Python 3.12 and the installed DexLab NumPy dependencies. Set `OUT` to a fresh directory on a data volume with at least 50 GiB free. Download and extraction preserve the raw ZIP and verify its published SHA-256, size, CRC and archive paths. On shared research hosts, run transfer through the repository's `research_guard.py` and `bounded_run.py` archive envelope.

```bash
python demos/landing-contact/fetch_release.py --output "$OUT"
python -m dexlab.landing_audit "$OUT/evaluation" \
  --protocol demos/landing-contact/protocol.json --output "$OUT/audit.json"
```

Expect `state_alignment.aligned: true`, `upstream_geometric_nonfoot_frames: [119]`, `native_pairs: "unavailable"` and `task_success: null`. The JSON records input and protocol hashes. `unavailable` is not zero contact. Output files refuse overwrite. This path audits downloaded evidence; it does not execute the policy.

## Capture a new native reference

The qualified local reference uses Linux/NVIDIA, Isaac Lab commit `46d6cc3`, Newton commit `71eeba1`, MuJoCo/MuJoCo Warp 3.15.0, Warp 1.17.0+cu12 and Torch 2.11.0+cu128. Keep this RTX 4090 cohort separate from the author's RTX 5090 and DexLab's 3.17.0 submission profile. Use a new isolated environment and the [pinned upstream preparation instructions](https://github.com/liudi159/supermimic-backflip-5090/blob/5b313d75e804cdd2ff1ce9bdcfa899a98eca856b/docs/REPRODUCE.zh-CN.md). Do not run its training command. Code, robot assets, motion and weights retain their respective upstream provenance; DexLab does not relicense them.

All 217 original dependency pins matched. That original list nevertheless has seven declared dependency conflicts involving MuJoCo/USD conversion and NumPy consumers. Versions were retained: the original converter and this native batch ran successfully, while unrelated installed package paths remain unqualified. Preserve the metadata diagnostics instead of silently changing the reference stack.

`run.py` requires that exact clean upstream checkout and the released checkpoint hash. It injects only the evaluation recorder into the original probe or evaluator. Set `CUDA_VISIBLE_DEVICES` and `MUJOCO_EGL_DEVICE_ID` explicitly to the selected single GPU; select fresh outputs. Execute under a frozen adaptive resource plan and the shared research lock, with the [protocol](protocol.json)'s six-attempt / 3600-second total budget tracked by the existing `MigrationBudget` ledger.

```bash
python demos/landing-contact/init_budget.py "$BUDGET"
"$NATIVE_PYTHON" demos/landing-contact/run.py --upstream "$UPSTREAM" \
  --mode probe --case support-probe --budget "$BUDGET" --output "$PROBE_OUT"
# Only after the support probe qualifies:
"$NATIVE_PYTHON" demos/landing-contact/run.py --upstream "$UPSTREAM" \
  --mode evaluate --case policy-repeat-1 --budget "$BUDGET" \
  --checkpoint "$CHECKPOINT" --output "$RUN_OUT"
"$NATIVE_PYTHON" -m dexlab.landing_audit "$RUN_OUT" \
  --protocol demos/landing-contact/protocol.json --geometry --output "$RUN_OUT/audit.json"
```

The native interpreter must resolve this checkout's `src` (for example `PYTHONPATH="$DEXLAB/src"` for the audit command). Initialization, failure and timeout consume attempts. The support probe includes two unrecorded controls and one recorded control; policy evaluation stops if qualification fails. The full 321-frame motion and 250-step hold are mandatory. Three matched fresh-process repeats retain every failure; their frequency does not estimate random-initial-condition reliability. Conditional interventions need a predeclared single change and matched control before execution.

The recorder saves:

- Original-compatible state, control, actuator and force arrays at every substep, plus states and native clock on both sides of the MuJoCo Warp step, after Newton refreshes its input state.
- Every contact exported by `get_data_into`, with local force, frame, signed distance and constraint address; all raw Warp candidates are retained separately before the copy helper filters types. Contact/constraint capacity overflow fails explicitly.
- Model geometry filters, margins, actuator limits, separate CPU-model and executing GPU options, native state precision, iteration counts and copy-source hash. A convergence residual/status is unavailable, not inferred from iteration count.

`--geometry` requires the recorded native version, model and pair stream. It runs only `mj_kinematics` and `mj_collision` at pre/post poses, compares identical geometry pairs, and reports absent pairs separately from zero distance. Native clock alignment does not by itself establish the collision-cache epoch. The CPU contact-copy tests are not Warp qualification.

## Scope and evidence

[Issue #260](https://github.com/huangkiki/Dexlab/issues/260) tracks PR delivery and the unresolved historical interpretation. The source Warp path passed the support fixture and complete repeated task in this fixed local cohort; the other five engines and direct MuJoCo profiles lack an identical qualified G1 policy/asset adapter. This is not a six-engine comparison, real-robot validation or a production UniSim adapter. No conditional interventions were run because the historical mismatch was not reproduced and localized. Four native starts used 156.07 seconds in the existing ledger; the two conditional slots and original 3600-second ceiling remain unchanged. Full bounded-window times, including identity checks, are separate.

[Independent historical audit](../../docs/evidence/landing/historical-audit.json) · [Source evaluation and limitations](https://github.com/liudi159/supermimic-backflip-5090/blob/5b313d75e804cdd2ff1ce9bdcfa899a98eca856b/docs/EVALUATION.zh-CN.md) · [Original downloadable archive](https://github.com/liudi159/supermimic-backflip-5090/releases/tag/v14-baseline-9029)
