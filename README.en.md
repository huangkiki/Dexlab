# DexLab

**Let robot models and physics simulators point out each other's blind spots on the same failures, then improve together.**

DexLab turns a contact task into traceable evidence: run the model, record native state, contact readback, and the failing layer; when the gap is physical, improve the simulator, and when it is strategic, go back to the model. Every update binds model version, simulator version, task protocol, and raw evidence, then reruns the same cohort. A public leaderboard is one verifiable view left by that loop, not the goal itself.

[Understand co-evolution](#coevolution) · [Poke RoboAPI adapter](demos/roboapi-poke/README.md) · [简体中文](README.md) · [Completed experiments](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Evaluation and anti-gaming protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html) · [Live Lab](https://huangkiki.github.io/Dexlab/en/latest/index.html#live-lab)

> Current stage: task scenes, native observations, independent scoring, and evidence records exist; the remote model executor and public leaderboard are being built. Public issues may contain publishable information only. Never post API keys, private addresses, or checkpoint credentials.

<a id="coevolution"></a>
## Why co-evolution instead of one-way evaluation

A simulator is not only a model's test room. A single failure usually mixes three possibilities: the model did not learn it, the scene was not configured correctly, or the physics itself is wrong. DexLab separates them before deciding what to change.

1. **Run the model.** Execute one contact task under a fixed task, robot configuration, simulator version, and budget.
2. **Record real contact.** Keep native states, contact forces, impulses, solver status, commands, and raw trajectories, not just a success video.
3. **Attribute the failure.** Decide whether the failure comes from the model, adapter, controller, scene, or physics. An invalid engine run does not become a model penalty.
4. **Improve one side, then rerun the same protocol.** A physical gap improves the simulator; a policy gap improves the model. Either change creates a new versioned cohort.

Those four steps let the model and simulator trade roles: the model reveals where simulation is wrong, and simulation in turn raises physical conditions the model must survive.

## Two directions of co-evolution

| Direction | Existing evidence | What it shows |
| --- | --- | --- |
| **The model exposes a simulator boundary** | Sponge wiping passes **3/3** with assistance and **0/3** without it; final cleaning is about **95.47% / 39.92%**. | The result depends heavily on the simulated retention mechanism. One pass is not evidence for the policy, and one unassisted failure is not evidence against a solver. |
| **Physical change exposes a policy boundary** | Changing the Wuji pinch from point contact to synthetic torsional contact reduces two-second hold displacement from **2.734 mm to 1.025 mm**. | The same control performs differently under different physics; for a model, that is a new condition it must handle. |

The repository currently demonstrates the side where physical conditions change the result. Once external models are connected, it can also record the side where model strategy changes the result. Until then, co-evolution is an expanding method, not a completed loop.

## What every round leaves behind

| Artifact | Purpose |
| --- | --- |
| **Versioned result** | Every cohort binds model version, simulator version, task protocol, seeds, budget, and evidence so a later upgrade cannot reuse an old score. |
| **Failure attribution** | Shows whether failure starts in observation/interface handling, grasp, hold, slip, contact switching, action timeout, or an invalid physics run. |
| **Rescorable evidence** | Raw records, independent scoring, and reproduction entrypoints remain for the next model or simulator iteration. |
| **Verification state** | Separates `local / unverified`, `official verified`, and `reproducible`; internal review is not external reproduction. |

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

## How a result is scored

Each task receives its own success rate; the headline score is the equal-task macro average. Every episode stays in its task's denominator, and a longer task does not gain hidden weight. Infrastructure failure and model failure are recorded separately. An invalid engine, scene, or record does not silently become a model failure. Retries and failures remain visible; teams cannot publish only the best attempt.

## Verifiable anti-gaming for co-evolution

To keep "evolving together" from becoming result cherry-picking, DexLab uses public layouts for reproduction, hidden layout consistency checks, frozen seeds and budgets, one checkpoint across all tasks, and complete attempt retention. Official scores are produced by DexLab; customer-run results can only be labeled `local / unverified`. [Full evaluation and anti-gaming protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html)

## Join the pilot

1. Open a [model-evaluation request](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+) with publishable model type, robot configuration, observation/action interfaces, target tasks, and publication preference.
2. Agree on endpoint, credentials, budget, and data handling through a private channel.
3. Freeze one cohort and complete interface qualification plus the pilot run.
4. Receive a private report first, then decide whether to request a public score or publish reproducible material.

A remote model service is the preferred integration. The endpoint only receives deployable observations and returns actions; it cannot read scorer state, future state, or simulator-privileged information. The repository does not yet publish a hosted endpoint.

The [Poke RoboAPI adapter](demos/roboapi-poke/README.md) is available: set `POKE_ROBOAPI_KEY` to query models and schema or make one non-controlling inference call. Per-task observation and action mapping is documented in the [adapter and sim2real guide](docs/roboapi-poke.md).

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

Task success is not physical truth. Physical validity belongs first to a specific simulator version and scene qualification; the model is evaluated mainly by task success and stability. A simulation pass does not prove hardware success, and hidden verification does not prove real-world generalization. Real materials, sensors, robot safety, and deployment reliability still require independent validation.

[Research findings](https://huangkiki.github.io/Dexlab/en/latest/experience.html) · [Solver configuration roles](https://huangkiki.github.io/Dexlab/en/latest/solver-taxonomy.html) · [Development and acceptance](docs/autoresearch.md)
