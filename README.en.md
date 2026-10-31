# DexLab

**Let robot models and physics simulators point out each other's blind spots on the same failures.**

DexLab turns a contact task into evidence: record native contact and the failing layer, then decide whether to change the model or the simulator. Every update binds model, simulator, protocol, and evidence, then reruns the same cohort. A leaderboard is only one view of that loop.

[Co-evolution](#coevolution) · [System architecture](#architecture) · [Uranus backend](https://huangkiki.github.io/Dexlab/en/latest/uranus-backend.html) · [Poke RoboAPI adapter](demos/roboapi-poke/README.md) · [简体中文](README.md) · [Completed experiments](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Evaluation and anti-gaming protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html) · [Live Lab](https://huangkiki.github.io/Dexlab/en/latest/index.html#live-lab)

> Current: tasks, scoring, and evidence work; the remote executor and public leaderboard are still being built.

<a id="architecture"></a>
## System architecture

```text
DexLab
├── Tasks and protocols: scenes, initial states, seeds, budgets
├── System under test: RoboAPI / VLA / policy
├── Environment backends: MuJoCo / Newton / SuperDex / Genesis / Uranus
├── Action execution: IK / controller / session
└── Evidence and scoring: success, contact state, attribution, cohorts, anti-gaming
```

Native physics backends own state evolution and contact readback. Uranus is a candidate generative observation backend that produces multi-view video from future `qpos`. It does not own tasks, success predicates or physical truth.

## Environment backend: Uranus

**Uranus: Building the Next-Generation Simulation Infrastructure for Embodied AI**<br>
Wenkang Qin, Yukun Zhou, Noah Shen, Jisong Cai, Dongxiao Mao, Baicheng Li, Yue Zhang, Wei Sui<br>
D-Robotics / Peking University / Shanghai Jiao Tong University · arXiv 2026

Uranus generates synchronized multi-view RGB from reference observations, latent history, future joint-position trajectories, robot descriptions and camera geometry. A RoboAPI end-effector target must first pass through IK/controller conversion into `qpos`; an independent task predicate then decides success or failure from the generated observation.

[Paper](https://arxiv.org/abs/2609.24815) · [Project](https://d-robotics-ai-lab.github.io/large-model-team/blog/uranus/) · [Inference code](https://github.com/D-Robotics-AI-Lab/Uranus-OSS) · [Weights](https://huggingface.co/collections/D-Robotics/uranus) · [Full interface, tasks and evidence boundary](https://huangkiki.github.io/Dexlab/en/latest/uranus-backend.html)

> Status: documented candidate backend. DexLab has no Uranus adapter, runner, cohort or official score yet; paper results are not DexLab reproductions.

<a id="coevolution"></a>
## Co-evolution

A simulator is not only a model's test room. One failure usually mixes three possibilities: the model did not learn it, the scene was not configured, or the physics is wrong. Separate them before deciding what to change.

1. **Run:** fix the task, embodiment, simulator version, and budget.
2. **Record:** keep native states, contact forces, solver state, and trajectories.
3. **Attribute:** model, adapter, scene, or physics.
4. **Change one side, rerun:** either change becomes a new cohort.

The model exposes where simulation is wrong; simulation exposes the model's boundaries.

## Two directions

| Direction | Evidence | Meaning |
| --- | --- | --- |
| **The model exposes the simulator** | Sponge wiping passes **3/3** with assistance and **0/3** without it; cleaning is about **95.47% / 39.92%**. | Success depends on simulated retention, not on the model alone. |
| **Physics exposes the model** | Changing the Wuji contact reduces two-second hold displacement from **2.734 mm to 1.025 mm**. | The same control behaves differently under different physics. |

Today the evidence shows the physical-change side. The model-change side becomes measurable once external models connect.

## What each round leaves

| Artifact | Purpose |
| --- | --- |
| **Versioned result** | Model, simulator, protocol, seeds, budget, and evidence stay together. |
| **Failure attribution** | Model, adapter, scene, or physics. |
| **Rescorable evidence** | Raw records and scoring remain for the next iteration. |
| **Verification state** | `local / unverified`, `official verified`, `reproducible`. |

## Completed experiments

These scenes show working environments, observations, and scoring. They are **not leaderboard scores for an external model**.

| Task | Result |
| --- | --- |
| **[Grasp and slip resistance](https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html)**<br>Wuji sphere pinch: point versus synthetic torsional contact. | **2.734 → 1.025 mm**; a pass is not in-hand manipulation. |
| **[Sponge wiping](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html)**<br>Source: RoboSimStudio `wipe_the_bar`. | Assisted **3/3**, unassisted **0/3**; cleaning **95.47% / 39.92%**. |
| **[Cloth grasp](https://huangkiki.github.io/Dexlab/en/latest/cloth-comparison.html)**<br>Sag, stretch, drop, and grasp separately. | Penetration, rebound, and grasp failures remain. |
| **[Cutting and pushing](https://huangkiki.github.io/Dexlab/en/latest/cut-push.html)**<br>Tofu and banana cutting. | Separation and contact force remain; synthetic material is not food calibration. |

[Full experiment index](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [All results and failures](https://huangkiki.github.io/Dexlab/en/latest/results.html)

RSS entrypoints are listed in the [inventory](https://huangkiki.github.io/Dexlab/en/latest/solver-failure-inventory.html): 50 entries, 40 task assertions, 10 teaching/mocks; not 50 independent operations, and 18 paper scenes still lack inputs.

## Scoring

Each task gets its own success rate; the headline is the equal-task macro average. Longer tasks gain no weight. Invalid runs stay out of the model denominator, and failures remain visible.

## Anti-gaming

Official scores are executed by DexLab. Public layouts reproduce, hidden layouts check overfitting, seeds and budgets are fixed, and one checkpoint runs every task. Customer-run results are only `local / unverified`.[Full protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html)

## Join the pilot

1. Open a credential-free [request](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+).
2. Agree on endpoint, budget, and data handling privately.
3. Freeze one cohort and run the pilot.
4. Get a private report before deciding what to publish.

A remote model only receives deployable observations and returns actions. The [Poke RoboAPI adapter](demos/roboapi-poke/README.md) lets you set `POKE_ROBOAPI_KEY`, query models and schema, or make one non-controlling inference call. See the [adapter and sim2real guide](docs/roboapi-poke.md).

## Inspect one evidence pair

No GPU needed. Download one sponge-wiping pair and recompute retention and cleaning offline:

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

Open `results/rss-wiping-v1/comparison.png`. The archive is about **126 MiB** compressed and **349 MiB** extracted; unassisted `task_pass: false` is a retained physical failure.

[Rescoring scope](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html#offline-evidence) · [Raw data and licenses](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1)

## Boundaries

Task success is not physical truth, and a simulation pass is not hardware success. Real materials, sensors, safety, and deployment still need independent validation.

[Research findings](https://huangkiki.github.io/Dexlab/en/latest/experience.html) · [Solver configuration roles](https://huangkiki.github.io/Dexlab/en/latest/solver-taxonomy.html) · [Development and acceptance](docs/autoresearch.md)
