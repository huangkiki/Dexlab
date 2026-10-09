# Standard block grasp: what changes with the force limit?

In these fixed simulation cases, per-finger limits of 0.2/0.4 N fail sustained retention, while 0.8/10 N hold and release the block. The pattern persists at preregistered ±2 mm initial offsets. All sixteen episodes completed and passed numerical checks; all three open-gripper negatives correctly stayed on the table.

## Question, protocol and evidence

We intervene on one existing task parameter: the finger actuator force limit. Geometry, material parameters, control trajectory and acceptance remain fixed. The [preregistered protocol](force-limit-protocol.md) was recorded at commit`9b65579` before native execution. Six development episodes preceded a source-freeze review and ten evaluation episodes. No control tuning or native reruns: sixteen independent processes recorded 128,000 physics samples.

The fixture uses three prismatic joints and a 40 mm, 64 g cube; official Genesis 1.4.3 / Quadrants 1.3.3 / CPU FP64, dt=0.5 ms, 4 s per episode. Friction 0.5, mass/inertia, force limits and initial states are read back. These are declared engineering parameters, not measured material properties; the fixture is not a calibrated UR7e or CTAG2F90D model.

![Synchronized failed and successful grasp](evidence/force-limit/comparison.gif)

Left: 0.4 N failure; right: 0.8 N success. Continuous full four-second recorded-state playback, without state interpolation. Genesis owns dynamics; MuJoCo is display-only. Original MP4s and frame mappings are in the [replay directory](evidence/force-limit/replays/), including the open negative. Images do not replace full-rate acceptance.

The [solver and force-sampling audit](genesis-solver-audit.md) identifies the historical Newton / approximate_implicitfast / elliptic configuration and distinguishes contact-solve epochs from final-state epochs. The full resolved native configuration snapshot is absent; [#125](https://github.com/huangkiki/Dexlab/issues/125) states recovery conditions. Historical native position-drive force bounds are not measured actuator outputs. Results and thresholds remain unchanged.

## Why retention fails

In the centered development case, the descriptive 1.025–1.075 s window gives these measured bilateral totals:

| Per-finger actuator cap N | Sum absolute pad x force N | Upward pad support N | Table support N |
|---|---:|---:|---:|
| 0.2 | 0.4000 | 0.2000 | 0.42784 |
| 0.4 | 0.8000 | 0.4000 | 0.22784 |
| 0.8 | 1.6000 | 0.62834 | 0 |
| 10 | 1.9809 | 0.62834 | 0 |

Weight is 0.62784 N. Under the lower caps, the pads do not support the entire weight and the table carries the remainder; higher-cap cases lift and retain the block. A 10 N cap does not mean10 N measured normal contact force. At the ±2 mm offsets, the 0.2 N cases have an x-force sum of about 0.23774 N, different from the centered case, further separating actuator bounds from measured contact loads.

The intervention supports an insufficient-support explanation within this model. The ideal symmetric static estimate is 0.62784 N per pad, not a true actuator threshold. Four levels do not establish continuous monotonicity or locate the exact boundary. Diagnostic windows were chosen during analysis for description only; preregistered acceptance did not change. Absolute x projection assumes flat pads and is not a general contact-normal observation or hardware measurement.

![Height and force curves](evidence/force-limit/force-height.png)

## Every case

PASS in an open-gripper row means the negative control passes, not successful grasping. Failed holds first violate the scoring window at 2.0 s; this is the first violating sample in that window, not slip onset.

| Case | Initial x mm | Cap N/finger | Numerical validity | Task/control | Hold minimum z mm | Maximum penetration mm |
|---|---:|---:|---|---|---:|---:|
| dev-cap-0.2 | 0 | 0.2 | PASS | FAIL | 19.9989 | 0.052226 |
| dev-cap-0.4 | 0 | 0.4 | PASS | FAIL | 19.9989 | 0.052615 |
| dev-cap-0.8 | 0 | 0.8 | PASS | PASS | 83.7011 | 0.664850 |
| dev-cap-10 | 0 | 10 | PASS | PASS | 83.7011 | 0.664849 |
| dev-repeat-10 | 0 | 10 | PASS | PASS | 83.7011 | 0.664849 |
| dev-open | 0 | 10 | PASS | PASS | 19.9989 | 0.003978 |
| eval-left-cap-0.2 | -2 | 0.2 | PASS | FAIL | 19.9989 | 0.048589 |
| eval-left-cap-0.4 | -2 | 0.4 | PASS | FAIL | 19.9989 | 0.098646 |
| eval-left-cap-0.8 | -2 | 0.8 | PASS | PASS | 83.7008 | 0.665087 |
| eval-left-cap-10 | -2 | 10 | PASS | PASS | 83.7008 | 0.665157 |
| eval-left-open | -2 | 10 | PASS | PASS | 19.9989 | 0.003978 |
| eval-right-cap-0.2 | 2 | 0.2 | PASS | FAIL | 19.9989 | 0.048589 |
| eval-right-cap-0.4 | 2 | 0.4 | PASS | FAIL | 19.9989 | 0.098646 |
| eval-right-cap-0.8 | 2 | 0.8 | PASS | PASS | 83.7008 | 0.665087 |
| eval-right-cap-10 | 2 | 10 | PASS | PASS | 83.7008 | 0.665157 |
| eval-right-open | 2 | 10 | PASS | PASS | 19.9989 | 0.003978 |

## Validity, cost and reproduction

Maximum native penetration is 0.665158 mm, below the unchanged 1 mm threshold. Native contact-vector sum versus native net force differs by 0 N; maximum per-step momentum residual is below 2.61e-9 weight impulses. These checks establish recording/numerical consistency, not physical truth. The 10 N independent-process repeat has identical sampled states and contacts. It does not guarantee universal determinism.

The sixteen native subprocesses took 210.695 s in total, including imports, initialization, simulation and output. First case with fresh campaign JIT cache: 51.134 s; subsequent cases: 10.278–11.127 s. Independent scoring took 3.971 s. Full per-case initialization/build/control/step/readback/write/destroy timing is retained in each`timings.json`; this is instrumented single-world cost, not an engine speed ranking. Preparation failures and bounded-service resource/cost accounting are recorded separately; rendering and compression occur outside physics timing windows.

The eight offset pinch cases include four passes and four failures. This fixed set has no declared sampling population: no confidence interval, general-success probability, hardware fidelity, learned/visual control or engine-superiority claim. Hardware calibration remains#6; broader calibrated comparisons remain #3. The pre-run manifest intentionally retains its original preregistration status; actual execution status is in[summary.json](evidence/force-limit/summary.json).

Every raw record is losslessly compressed under[cases/](evidence/force-limit/cases/), with exact decompression hashes. Keep the matching repository version. To rescore without starting Genesis, copy one case folder to a temporary directory, decompress its`*-0.json.gz` there, then run:

```bash
PYTHONPATH=src python -m dexlab.genesis_pinch_score TEMPORARY_CASE_DIRECTORY
```

The scorer verifies case identity, manifest and audited runner bytes before independent checks. This is provenance support, not proof against fabricated untrusted data. All six grasp failures and three negatives remain available. See[artifact hashes](evidence/force-limit/artifact-hashes.json),[official wheel proof](evidence/force-limit/official-proof.json),[frozen source hashes](evidence/force-limit/frozen.json),[installed package versions](evidence/force-limit/installed-packages.json), and[all case metrics](evidence/force-limit/summary.json).

Bounded services from preparation through replay/packaging total 1216.444 s, including failed attempts. The elapsed span is 1896.039 s including editing/checking gaps. The [resource and cost ledger](evidence/force-limit/resource-cost.json) records every exit status, memory peak, cgroup limits and failure reason; delivery gates are separate. CPU: Intel Core i9-14900K, with a two-core-equivalent quota for native runs; no remote hardware is pooled. Preparation failures included a download timeout, cache settings not reaching the service, helper Python version and MuJoCo profile configuration. All remain recorded. The first replay failed because FFmpeg auto threads exhausted available process resources; the failed output was retained and encoder/filter threads bounded to one, without raising resource limits or changing any physics trajectory. This post-run display fix is recorded separately from native source freeze.
