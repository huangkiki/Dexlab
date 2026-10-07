# Force-limit failure boundary: preregistration

Research question: how does the per-finger actuator force limit change sustained block retention, and does the result persist at two frozen lateral offsets? The [manifest](../demos/contact-benchmark/force-limit-v1.json) fixes sixteen intended episodes before outcomes. This records the pre-run protocol; completed execution is reported in [results](force-limit-results.md).

Reuse the qualified [primitive pinch task](../demos/contact-benchmark/GENESIS_PINCH.md). Change only the symmetric finger force limit (0.2, 0.4, 0.8, 10 N) and, for evaluation, initial x (−2 or +2 mm). Six centered development episodes include an independent-process 10 N repeat and an open negative; ten evaluation episodes include eight pinch cases and two open negatives. Freeze controller, runner and scorer before evaluation. No training or per-case tuning.

A force limit is not measured contact force. The ideal symmetric flat-pad static estimate mg/(2μ)=0.62784 N per pad assumes quasistatic bilateral contact; it is a diagnostic reference, not a predicted actuator threshold or a pass criterion. Record native force vectors and explicitly label any projected normal-force proxy. Transients, geometry and numerical failures can invalidate the proposed explanation.

Keep the existing 1 mm penetration, 1e-8 N ledger and 5% weight-impulse residual checks. Hold requires z≥60 mm throughout 2–3 s with both pads and ≤0.01 N other support; release requires z≤30 mm and ≤0.01 N pad-force sum throughout 3.8–4 s. Report numerical validity separately from task success, including the first failed sample. Open negatives must stay below 30 mm and lack pad contact during hold.

Each episode uses a fresh process and read-back initial parameters. Preserve incomplete and failed attempts. Sixteen intended episodes, at most twenty-four total attempts including instrumentation repairs, at most thirty minutes per invocation and three hours aggregate native execution; one admitted cgroup worker, no swap. Performance windows exclude transfers and hashing. Preparation, compilation, control, stepping, readback, scoring, rendering and total wall time remain separate.

Publish every case, actual-state close-up replay, force/height curves and raw evidence. These fixed challenges do not define a population success probability. No hardware fidelity, learned policy, visual control or engine ranking follows. Hardware calibration remains under #6; this experiment does not complete #3. Full acceptance is tracked in [Issue #90](https://github.com/huangkiki/Dexlab/issues/90).

## Reproduction entrypoints

Use the resource-qualified environment and bounded invocation described in [execution rules](autoresearch.md). Each case must use a fresh process and a new output directory on the configured data volume. Example inside that bounded invocation:

```bash
python -m dexlab.genesis_pinch_probe OUTPUT --case-id dev-cap-0.2
python -m dexlab.genesis_pinch_score OUTPUT
```

The schema-2 scorer verifies the manifest snapshot, case identity and audited runner bytes before evaluating native records. This provenance check supports a source audit; it cannot prove that arbitrary untrusted JSON was never fabricated. The raw force ledger, momentum checks and full-rate records remain necessary. The published runner/scorer must stay frozen across evaluation.
