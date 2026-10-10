# From anomalies to improvement directions

Start with a physical question. “Excessive penetration” needs a contact scale, load, geometry, compliance and acceptable error; “failed grasp” needs the full support, slip and release trajectory. A picture or one run cannot separate parameters, integration and solver mechanisms.

## A reusable diagnosis sequence

1. **Establish the physical expectation.** Check force/torque balance for static support and `|f| ≤ μₛN` for sticking. Under rigid-body, constant Coulomb friction, persistent-contact and no-rotation assumptions, incline sliding uses `a=g(sinθ−μₖcosθ)`. Impacts additionally declare restitution, external impulses and rotation. Do not assume a unique analytical solution for complex multi-contact systems; empirical references state source, units, conditions and uncertainty.
2. **Establish trustworthy observations.** Check geometry, mass/inertia, frames, control epochs, effective native parameters, contact capacity and readback addresses. Save source assets, intermediate models and conversion provenance. Missing readbacks remain missing, not defaults or zero.
3. **Run controlled parameter experiments.** Freeze scene, objective, scoring and budget; select candidates from prior experience and record hypotheses, expected changes and sources. AI proposes the next trial; execution retains every attempt and independent scoring checks all physical constraints together. Extra iterations, steps and observations contribute to cost.
4. **Locate remaining differences.** Use native readbacks, source and ablations to investigate contact generation, friction representation, constraints, stopping, integration and precision. Failed finite searches only establish failure within their tested range.

## Three existing cases

| Anomaly and reference | Verified change | Remaining question |
| --- | --- | --- |
| Excessively stiff response versus the frozen synthetic 20 kN/m target | MuJoCo calibration improves the fixed-mass response; a predeclared mass conversion improves two validation masses. | This does not establish arbitrary-geometry or real-material accuracy. [Experience and records](normal-response) |
| Incorrect PhysX negative-control mass versus model mass/inertia | Initialize mass/inertia before disabling collision. | Native TGS state/impulse residuals remain under #163. [Case](physx-observation) |
| Native/framework trajectories diverge under matched physical inputs/time | Align four GPU fields; reject out-of-bounds CPU contact readbacks as unavailable. | Support trajectories still diverge; no unique framework cause is established. [Case](framework-path) |

Separate **verified configuration improvements, localized integration fixes, evidenced algorithm research directions and unresolved questions**. This round automates parameter changes and evidenced integration fixes; solver-source changes first require research evidence.

## AI-controlled trial entry point

The first integrated path is native MuJoCo/SuperDex `normal-load` development. It reuses `contact_indent_run`, independent `--verify` and `MigrationBudget`, with no new model service or scheduler. Native PhysX inclines, framework comparisons and pinch continue through their own frozen protocols and runners; this path does not qualify their parameters.

`benchmarks/contact-trials-example-v1.json` reuses historical initial/fitted profiles to demonstrate recording. It is a known-outcome development example, not a new algorithm discovery or unseen holdout. Its manifest explicitly freezes the runtime version profile and full scene, every candidate parameter, hypothesis, expected effect, physical reference, evidence SHA-256, original checks and work package. AI fills these fields before execution and uses results to propose a successor; changed sources/candidates require a new manifest inheriting the prior ledger.

In a qualified environment at the repository root, set `OUT`, `DATA_DIR` and `IO_DEVICE` to your own new output directory, data directory and block device:

```bash
python -m dexlab.contact_trials init benchmarks/contact-trials-example-v1.json "$OUT"
python scripts/bounded_run.py --profile adaptive --cpu-cores 4 \
  --resource-plan "$OUT/resource-plan.json" --data-dir "$DATA_DIR" \
  --io-device "$IO_DEVICE" --timeout 900 --receipt "$OUT/resources-initial.json" -- \
  python scripts/research_guard.py run --lock "$DATA_DIR/research.lock" \
    --kind qualification --receipt "$OUT/window-initial.json" -- \
    python -m dexlab.contact_trials run "$OUT" initial-mujoco --timeout 840
python -m dexlab.contact_trials status "$OUT"
```

Use new resource/window receipts for each candidate, retaining the frozen resource plan within a batch. Execute `validation-mujoco-reference` against the same ledger. Exit 1 can mean a physical failure: inspect `attempts/*/result.json` instead of treating it as an infrastructure fault and retrying indefinitely.

Results retain proposed/resolved/effective parameters and differences, complete logs, independent scores, native stepping/observation costs, hashes and terminal outcome. Timeouts retain attempts. After a hard kill, establish that recorded processes have ended, then run `python -m dexlab.contact_trials recover "$OUT"`. Recovery charges the full reserved duration and never resets the budget. Recorded physical failures cannot retry; infrastructure failure permits at most one reasoned recovery within the original budget. Existing `prior_budget` inheritance and evidenced work-package rules remain unchanged.

Development is not holdout validation. Freeze independent transfer conditions, equal tuning budgets, negatives and acceptance before any new comparison. Previously inspected mass/size records cannot become unseen validation after tuning against them.

## Advance concrete evidence gaps

Reuse old PhysX traces first for [offline FP32 diagnostics](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-precision-diagnostics.md). [#163](https://github.com/huangkiki/Dexlab/issues/163) owns precision attribution and new-protocol holdouts; [#152](https://github.com/huangkiki/Dexlab/issues/152) owns remaining state/contact-path differences; [#145](https://github.com/huangkiki/Dexlab/issues/145) owns inertia/frame semantics. Existing fixed-model experiments do not depend on inertia-randomization qualification.

The six-engine matrix, 594-episode pinch study and later tasks remain. Preserve resource limits and one executor; scheduled development stays paused. Add a work package only with new evidence and a concrete hypothesis; one incomplete engine does not block independent research.

The executed integration check retains two runtime-version admission failures. After freezing the explicit profile and inheriting the ledger, two 1600-step MuJoCo 3.15.0 cases complete: the initial profile fails physically and the historical fitted profile passes. Effective parameters and independent scores are retained. This validates the workflow with known candidates, not new holdouts. [Results, costs and archive](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/contact-trials-integration-v1.json). Recovery also verifies termination of the bounded cgroup, covering interruption before a child PID can be published.
