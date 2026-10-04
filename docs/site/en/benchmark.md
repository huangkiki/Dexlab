# Benchmark and independent acceptance

## Separate two questions

**Physical error:** identify allowed parameters on a shared measured calibration set, then compare against independent hardware conditions. Without measurements, physical error is unknown.

**Engineering performance:** freeze task distribution, controller and tuning budget; report held-out task performance, stability and error/cost curves. Equal wall time and equal configuration counts are different budgets.

## Required measurements

| Dimension | Metric and coverage |
|---|---|
| Geometry | Independent intersection/depth, maxima and excess duration; disclose thickness, sampling and approximations |
| Loads | Native forces/impulses, support distribution and momentum residual; disclose frames, body and timing |
| Slip | Material slip needs persistent material correspondences; wrist displacement and rolling are separate |
| Stability | First anomaly, drift, oscillation, contact gaps, warnings and divergence |
| Task | Phases, sustained holding, release and failure reason; once/end/sustained success are separate |
| Cost | Build/JIT, native steps, controls/observations, rendering, scoring and transfer separately |

Register thresholds from task scale, tolerance and uncertainty before evaluation. Keep the primary controller fixed; do not relax thresholds, hide attachments or drop hard cases to manufacture success.

## Data and statistics

Separate calibration/development, validation and formal tests by object, material batch and session. Frames from one trajectory are not independent samples. Share actual starting states and actions across engines; equal seeds do not establish equal starts. Retain every preregistered denominator, failure, timeout, unsupported result and uncertainty interval.

Formal timing excludes this queue's transfers, compression and hashing. Low priority is not a resource limit, and offline model loading can be expensive. Mark measurements as interfered when isolation is unavailable.

[Full protocol](https://github.com/huangkiki/Dexlab/blob/main/docs/benchmark.md) · [Model audit](https://github.com/huangkiki/Dexlab/blob/main/docs/model-audit.md) · [Jitter definitions](https://github.com/huangkiki/Dexlab/blob/main/docs/jitter.md)
