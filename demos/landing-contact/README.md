# Audit G1 landing contacts

[English](README.md) | [简体中文](README.zh-CN.md)

Check whether a saved geometric intersection and a recorded contact force refer to the same state, geometry and physics substep. The audit preserves the upstream task score and never substitutes a CPU-solved force for the recorded GPU force.

The public first-run archive contains 571 control steps and 2284 physics substeps. DexLab independently matched all 29 joint names and control-boundary states: joint positions agree exactly, and the largest root angular-velocity difference is 2.39e-6 rad/s. The author's stored geometric classification flags frame 119 (2.38 s); the recorded nonfoot loaded-pair count is zero throughout. This rules out a simple joint-order mismatch **for this archive**. It does not establish the contact epoch or explain the discrepancy. The archive lacks the native model and complete contact-pair stream. The author's separate passing reevaluation remains a separate result.

## Recompute the public record

Use Python 3.12 and the installed DexLab NumPy dependencies. Set `OUT` to a fresh directory on a data volume with at least 50 GiB free. Download and extraction preserve the raw ZIP and verify its published SHA-256, size, CRC and archive paths. On shared research hosts, run transfer through the repository's `research_guard.py` and `bounded_run.py` archive envelope.

```bash
python demos/landing-contact/fetch_release.py --output "$OUT"
python -m dexlab.landing_audit "$OUT/evaluation" \
  --protocol demos/landing-contact/protocol.json --output "$OUT/audit.json"
```

Expect `state_alignment.aligned: true`, `upstream_geometric_nonfoot_frames: [119]`, `native_pairs: "unavailable"` and `task_success: null`. The JSON records input and protocol hashes. `unavailable` is not zero contact. Output files refuse overwrite. This path audits downloaded evidence; it does not execute the policy.

## Capture a new native reference

Native qualification is pending. The fixed reference needs Linux/NVIDIA, Isaac Lab commit `46d6cc3`, Newton commit `71eeba1`, MuJoCo/MuJoCo Warp 3.15.0, Warp 1.17.0+cu12 and Torch 2.11.0+cu128. Keep this historical source cohort separate from DexLab's 3.17.0 submission profile. Use a new isolated environment and the [pinned upstream preparation instructions](https://github.com/liudi159/supermimic-backflip-5090/blob/5b313d75e804cdd2ff1ce9bdcfa899a98eca856b/docs/REPRODUCE.zh-CN.md). Do not run its training command. Code, robot assets, motion and weights retain their respective upstream provenance; DexLab does not relicense them.

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

[Issue #260](https://github.com/huangkiki/Dexlab/issues/260) retains full physical qualification, repeat results, synchronized video/curves and causal interpretation. The source Warp path is not yet qualified; the other five engines and direct MuJoCo profiles lack an identical qualified G1 policy/asset adapter. This is not a six-engine comparison or a production UniSim adapter.

[Independent historical audit](../../docs/evidence/landing/historical-audit.json) · [Source evaluation and limitations](https://github.com/liudi159/supermimic-backflip-5090/blob/5b313d75e804cdd2ff1ce9bdcfa899a98eca856b/docs/EVALUATION.zh-CN.md) · [Original downloadable archive](https://github.com/liudi159/supermimic-backflip-5090/releases/tag/v14-baseline-9029)
