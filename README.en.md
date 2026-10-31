# DexLab

**Unified evaluation and failure diagnosis for contact-rich robot models.**

Connect a remote model service and customer robot configuration, then evaluate grasping, holding, wiping, cloth, cutting, and insertion under frozen tasks, simulator versions, seeds, and resource budgets. DexLab returns equal-task macro success, repeat stability, a per-task matrix, and failure evidence. **Official leaderboard scores are produced by DexLab's evaluation environment; self-reported scores are not accepted.**

[Request a model-evaluation pilot](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+) · [Evaluation protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html) · [简体中文](README.md) · [Completed experiments](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Live Lab](https://huangkiki.github.io/Dexlab/en/latest/index.html#live-lab)

> Current stage: task scenes, native observations, independent scoring, and evidence records exist; the remote model executor and public leaderboard are being built. Public issues may contain publishable information only. Never post API keys, private addresses, or checkpoint credentials.

## What the evaluation returns

| Output | Description |
| --- | --- |
| **Leaderboard score** | Equal-task macro success over a frozen suite, with every task result visible so longer tasks cannot gain hidden weight from a pooled raw episode count. |
| **Stability and cost** | Success dispersion across repeats, timeouts, request latency, action errors, and resource budget. |
| **Failure diagnosis** | Whether failure starts in observation/interface handling, grasp, hold, slip, contact switching, action timeout, or an invalid physics run, with the corresponding evidence. |
| **Verification state** | Separate local unverified results, DexLab-official results, and externally reproducible results where the team releases enough material. |

## Why not judge from one success video

In contact-rich manipulation, lifting an object is not proof of a stable grasp, and a completed routine is not proof that the contact physics was meaningful. DexLab records native state, contact readback, issued commands, scoring outcomes, and failure denominators, then separates:

- whether a model completes the full task;
- where the failure begins;
- whether an engine or scene problem makes the run invalid;
- whether the result only works on one memorized layout;
- whether another team can inspect or reproduce the result.

The evaluation is for generalist manipulation models, VLA/WAM policies, agents acting as policies, and remote robot APIs. It scores the **end-to-end system** made of the model, adapter, controller, and customer robot configuration. It does not invent a capability coefficient that pretends different embodiments reveal one model-only score.

## Completed experiments

These scenes demonstrate working task environments, observations, and scorers. They are **not leaderboard results for any external model**.

| Contact task | Recorded result |
| --- | --- |
| **[Grasp, hold, and slip resistance](https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html)**<br>Wuji sphere pinch under one controller, comparing point contact with synthetic torsional contact. | Two-second hold displacement falls from **2.734 mm to 1.025 mm**, passing the original 2 mm limit. A grasp pass is not completed in-hand manipulation. |
| **[Sponge wiping](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html)**<br>Source: RoboSimStudio `wipe_the_bar`; retained assisted and unassisted controls. | The original passes **3/3** tasks; the unassisted variant passes **0/3**. Final cleaning is approximately **95.47% / 39.92%**. |
| **[Cloth grasp and release](https://huangkiki.github.io/Dexlab/en/latest/cloth-comparison.html)**<br>Sag, stretch, coverage, drop, and robot cloth grasp are evaluated separately. | Penetration, rebound, and grasp failures remain. A cloth replay is not promoted to complete active folding. |
| **[Cutting and blade-face pushing](https://huangkiki.github.io/Dexlab/en/latest/cut-push.html)**<br>Continuous cutting, blade contact, and pushing for tofu and banana. | Separation and measured contact forces are shown; synthetic material cases are not real-food calibration. |

[Full experiment index](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [All results and failures](https://huangkiki.github.io/Dexlab/en/latest/results.html)

### How the RSS experiments enter the catalogue

The [RSS public-entry inventory](https://huangkiki.github.io/Dexlab/en/latest/solver-failure-inventory.html) covers **50 public entrypoints** at upstream `b001cc7`: 40 have task-scoped assertions and 10 are teaching, rendering, or hardware mocks. They are indexed by rigid grasp, cloth/soft body, rope/cable, wiping/bag/tape, cutting, granular/liquid/dough, and policy execution. A goal scorer and its scene can share one episode, so this is not 50 independent operations. The 18 exact paper scenes in Figure 5 still lack original inputs and are not the same denominator as the 50 public entrypoints.

## How a model is scored

Before an official cohort, DexLab freezes the tasks, embodiment, engine versions, seeds, repeats, timeouts, resource caps, and scorer. Each task first receives an independent success rate; the headline score is the equal-task macro average.

- Every episode for a task stays in that task's denominator;
- a task does not gain extra weight because it uses more episodes or costs more;
- infrastructure failure and model failure are recorded separately;
- an invalid engine, scene, or record does not silently become a model failure;
- retries and failures remain visible; teams cannot publish only the best attempt.

Reports show the complete task matrix, success dispersion, and failure classes. A task failure does not disappear inside an aggregate.

## Anti-gaming

DexLab borrows the official-execution and hidden-verification principles used by public benchmarks while retaining contact-specific evidence boundaries:

- **Official scoring.** DexLab controls tasks, resets, observations, model calls, and scoring. Customer-run results can only be labeled `local / unverified`.
- **Public plus hidden verification layouts.** Public layouts support reproduction and iteration; unpublished scene variations detect hardcoded coordinates, memorized trajectories, and tuning restricted to released tasks.
- **Frozen budgets.** Seeds, repeat counts, timeouts, and resource caps are fixed. Teams cannot rerun indefinitely and submit the best outcome.
- **One fixed system.** A leaderboard entry uses one checkpoint and inference procedure across all tasks. Per-task routing to different models is not allowed.
- **Technical review.** DexLab reviews adapters, action interfaces, duplicate systems, minimally changed variants, and suspicious task selection.
- **Every attempt retained.** Model failures, interface failures, timeouts, invalid executions, and platform faults remain distinct.

Formal boards expose these states:

| State | Meaning | Leaderboard eligible |
| --- | --- | --- |
| `local / unverified` | The team ran it without official frozen conditions or scoring. | No |
| `official verified` | DexLab ran it and it passed interface, leakage, and anti-gaming checks. | Yes |
| `reproducible` | An official result also publishes enough configuration and material for external review. | Separate badge |

Raw video, trajectories, and weights are private by default and may be released by the customer. Internal DexLab review is not equivalent to independent community review. See the [full evaluation and anti-gaming protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html).

## Join the pilot

1. Open a [model-evaluation request](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+) with publishable model type, robot configuration, observation/action interfaces, target tasks, and publication preference.
2. Agree on endpoint, credentials, budget, and data handling through a private channel.
3. Freeze one cohort and complete interface qualification plus the pilot run.
4. Receive a private report first, then decide whether to request a public score or publish reproducible material.

A remote model service is the preferred integration. The endpoint only receives deployable observations and returns actions; it cannot read scorer state, future state, or simulator-privileged information. The concrete schema will be frozen before a pilot. The repository does not yet publish a hosted endpoint.

## Inspect existing evidence now

No GPU is required to download one matched sponge-wiping recording pair and recompute holding displacement and cleaning from saved material and ink states:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/huangkiki/Dexlab.git
cd Dexlab
git sparse-checkout init --cone
git sparse-checkout set scripts demos/rss-wiping
uv run --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python scripts/download_assets.py \
  --manifest demos/rss-wiping/evidence-bundle.json \
  --destination downloads/rss-wiping-v1
uv run --offline --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python demos/rss-wiping/rescore_bundle.py downloads/rss-wiping-v1 \
  --output results/rss-wiping-v1
```

Open `results/rss-wiping-v1/comparison.png` for the curves. The directory also contains CSV files and `report.json`. The evidence archive is about **126 MiB** compressed and **349 MiB** extracted. The unassisted `task_pass: false` is a retained physical task failure, not a failed download.

[Rescoring scope and failure index](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html#offline-evidence) · [Raw data and per-file licensing](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1)

## Result boundaries

Task success is not physical truth. Physical validity is primarily the responsibility of the engine and scene qualification; the model is evaluated mainly by task success and stability. A simulation pass does not prove hardware success, and hidden verification does not prove real-world generalization. Real materials, sensors, robot safety, and deployment reliability still require independent validation.

[Research findings](https://huangkiki.github.io/Dexlab/en/latest/experience.html) · [Solver configuration roles](https://huangkiki.github.io/Dexlab/en/latest/solver-taxonomy.html) · [Development and acceptance](docs/autoresearch.md)
