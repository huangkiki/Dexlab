# Genesis rigid qualification: quality and cost

[简体中文](GENESIS_COST.zh-CN.md)

**The bounded primitive cases pass their engineering checks, but smaller steps do not establish convergence.** Native peak penetration increases from0.044 to0.665 to0.758mm as the step is refined. All stay below the unchanged1mm criterion. An apparently smaller coarse-step peak is not evidence of higher accuracy; contact-event sampling and soft response matter. No engine ranking or hardware accuracy follows.

![Measured quality and cost](../../docs/evidence/genesis-cost.png)

## Frozen protocol and measured costs

Genesis1.4.3 / Quadrants1.3.3 / Torch2.9.1+cpu, CPU FP64, i9-14900K, two-core CPU quota,24GiB cap,swap0. Official package versions were rechecked on2026-10-06. Geometry, mass, friction, PD drives, contact settings and acceptance are those of [the pinch report](GENESIS_PINCH.md). Only timestep changes, in fixed1/0.5/0.25ms order. Each process runs four4s episodes: two reset repeats each for pinch and open-pad negative. All12 outcomes passed; reset trajectories matched within each configuration. These are development controls, not12 independent held-out successes.

| Step(ms) | Native peak(mm) | Positive stepping/reset0 / reset1(s) | Mean positive observations(s) | Whole4-episode process(s) | Separate scoring process(s) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.044 | 0.817 / 0.654 | 0.554 | 14.045 | 0.373 |
| 0.5 | 0.665 | 1.466 / 1.318 | 1.303 | 21.101 | 0.762 |
| 0.25 | 0.758 | 2.790 / 2.629 | 2.605 | 35.197 | 1.514 |

[Complete costs, scores and source/input hashes](../../docs/evidence/genesis-cost.json). Instrumented0.5ms records equal all four previously published records exactly, including states and contacts: adding timers did not change those observed trajectories on this host.

Existing JIT caches were retained. Init costs1.139–1.146s and scene construction/build2.310–2.329s per process. The first positive step takes about0.158s, versus about0.0004s on the reset repeat; first-step cost remains included in stepping and is also reported separately. Do not subtract it twice or call these cold-compilation timings. Build may contain initialization/JIT work; separate compiler instrumentation is absent.

Control, stepping, observations, reset/readback and JSON serialization/write have separate timers. The entire child-process wall time includes imports and overhead absent from the stage sum. Full-rate recording and timer overhead are included; this is not an uninstrumented maximum-throughput test. Scoring is a separate engine-independent process after all physics runs. No archival/transfer ran during measurement. Rendering was not executed in this window: prior replay manifests report it separately; it is neither zero-cost nor Genesis simulation time. Two same-process reset timings are descriptive, not a confidence interval or randomized-order timing study.

## Capability audit and reuse boundary

| Requirement | Evidence | Boundary |
|---|---|---|
| Support/sliding and contact transient | [Cone report](GENESIS_CONE.md), retained controls/raw failure | Conditional translating Coulomb reference, not measured material truth |
| Imported inertia, actual joints and limits | [Joint report](GENESIS_JOINT.md) | Zero-armature configuration qualified; failed soft-limit histories retained |
| Pinch/hold/release and negative | [Pinch report](GENESIS_PINCH.md), full-rate force ledger and momentum checks | Primitive box, synthetic criteria; independent geometry reference only covers box/table |
| Reset, GPU isolation and overflow | [GPU report](GENESIS_GPU.md) | Short primitive batch; no GPU grasp or throughput claim |
| Continuous close-up | [Measured replay](GENESIS_PINCH.md#continuous-measured-state-replay) | Display-only, no image-based control, not full-rate collision proof |
| Quality/stability/cost | This report and raw timings | Three development steps, no convergence or cross-engine ranking |

UniSim1.7.10's installed `unisim/backend/genesis/dependencies.py` explicitly requires Genesis1.3.3 and rejects other installed versions before loading the runtime. This conflicts with the selected official1.4.3; native scene ownership is retained. The adapter does expose solver/friction-cone and armature/contact operations, so the decision is **not** a claim that it lacks those concepts. Direct/adapter physical equivalence and engineering savings have not been measured; [#4](https://github.com/huangkiki/Dexlab/issues/4) retains that work. No pin bypass or engine edit was used.

Rigid contact is the measured profile. PBD cloth and MPM/FEM are separate, unqualified profiles here; neither volume-material capability nor rigid checks proves thin-cloth performance. Apple SDF-SDF is not qualified on Genesis and was never silently replaced by convex geometry. Before closing #42, finish the issue-wide evidence/publication audit and its requested separate cloth follow-up.

## Reproduce

Use the official environment and resource guard from the linked reports. Run `python -m dexlab.genesis_pinch_probe NEW_DIRECTORY --dt 0.001`, then0.0005 and0.00025 in fresh directories; each produces `timings.json` plus all four raw records. Run `python -m dexlab.genesis_pinch_score DIRECTORY` after simulation. The plot is reproducible with `python scripts/plot_genesis_cost.py docs/evidence/genesis-cost.json NEW_FIGURE.png`. No output overwrite, threshold change or failed-case deletion is permitted.

The [archive manifest](../../docs/evidence/genesis-cost-manifest.json) covers all12raw episodes and source hashes. The [v0.34.0 release](https://github.com/huangkiki/Dexlab/releases/tag/v0.34.0) publishes this package. Downloaded size and SHA-256 match the manifest; this delivery copy is not an independent backup.
