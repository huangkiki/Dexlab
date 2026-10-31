# Simulator and model co-evolution

DexLab is a co-evolution protocol for generalist manipulation models, VLA/WAM policies, agents acting as policies, and remote robot APIs. The model is served through a remote endpoint and evaluated under frozen robot configurations, tasks, simulator versions, seeds, and resource budgets. Reports expose per-task success, repeat stability, a complete task matrix, and failure evidence.

**Official leaderboard entries are scored by DexLab's evaluation environment; self-reported scores are not accepted.**

## The co-evolution loop

A failure may come from the model, adapter, controller, scene, or physics. DexLab's job is not to label a model good or bad, but to point the next change at the correct side:

1. run the model under a fixed task and simulator version;
2. record native state, contact readback, commands, solver status, and raw trajectories;
3. attribute the failure and separate invalid engine runs from model failures;
4. improve the simulator or the model, then place the result in a new versioned cohort.

Every result binds model version, simulator version, task protocol, seeds, budget, and evidence. Without that version pair, we cannot tell whether changing the model or the simulator produced the change.

## Current status

The repository already contains task scenes, native observations, independent scoring, retained failures, and offline evidence records. The remote model executor and public leaderboard are still being built. Scoped pilot requests are welcome, but a scripted example in this repository is not a measured score for an external model.

[Request a model-evaluation pilot](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+) · [Browse experiments](experiments.md) · [Rescore one evidence pair](quickstart.md)

## What is evaluated

The first benchmark focus is contact-rich manipulation:

- grasp, lift, hold, and slip;
- sponge wiping, surface contact, and cleaning outcomes;
- cloth grasp, lift, and release;
- cutting, blade contact, and pushing;
- insertion, constrained-space operation, and contact switching;
- later extensions to granular, liquid, and deformable-object manipulation.

The task set for a formal cohort must be frozen before evaluation. Existing experiments demonstrate working scenes, runners, and scorers; a candidate task is neither open to model submissions nor benchmark-qualified merely because it appears in this list.

The [RSS public-entry inventory](solver-failure-inventory.md) covers 50 entrypoints: 40 task-scoped assertions and 10 teaching/rendering/mocks. It expands candidate tasks and source traceability without counting a goal scorer and its shared scene as two independent operations. The 18 exact paper showcases still lack original inputs.

## Scoring

For a fixed suite of `T` tasks, run every task `R` times under matched conditions:

```text
task_success_i = successful_episodes_i / R
macro_success = (task_success_1 + ... + task_success_T) / T
```

The headline leaderboard metric is this equal-task macro average.

Each report also shows:

- success rate and failure classes for every task;
- mean success and repeat-to-repeat dispersion;
- timeouts, invalid actions, interface failures, and physically invalid runs;
- selected public replays and publishable failure evidence for every task.

Episodes from different tasks are never pooled into one raw pass-rate denominator. A task does not receive extra weight merely because it uses more episodes or costs more to run.

### Physical validity evolves with the versioned loop

Physical validity belongs first to a specific simulator version and evaluation environment. Every official cohort must pass version, scene, unit, and contact-readback qualification. Invalid runs caused by the engine or evaluator are excluded from the model denominator while their receipts, causes, and recovery conditions remain preserved; those failures become the input for the next simulator improvement.

A model is charged with a failure only when evidence shows that it repeatedly emits invalid actions, depends on simulator-privileged observations that would not be deployed, or bypasses the declared interface.

## Customer-provided robot configurations

Teams may provide their own robot, gripper, cameras, and controller configuration. DexLab does not apply embodiment-specific capability coefficients or pretend that the result is an embodiment-independent score for the model alone. The leaderboard measures the end-to-end system formed by the model, adapter, controller, and customer robot configuration.

Every entry records at least:

- robot, gripper, cameras, and control frequency;
- observation and action interfaces;
- model name, version, and immutable identity;
- adapter, runtime image, and dependency versions;
- tasks, scenes, seeds, and repeat count;
- every run, failure, and retry.

The public result is therefore an **end-to-end system score**. A new embodiment or adapter creates a new entry or explicitly new version; it cannot inherit the old score.

## Official evaluation flow

1. **Apply.** The team supplies model and interface information without secrets; private credentials are transferred through an agreed private channel.
2. **Qualify the interface.** DexLab checks the model endpoint, observation and action formats, timeouts, reset semantics, and errors.
3. **Freeze the cohort.** Tasks, robot configuration, engine version, seeds, repeats, resource caps, and scorer are fixed.
4. **Run officially.** DexLab controls scene reset, observations, action intake, timeouts, and scoring. The customer endpoint only receives declared observations and returns declared actions.
5. **Report completely.** Deliver macro success, stability, task matrix, cost, failure classes, and evidence index.
6. **Choose publication.** Private evaluations remain private by default. A formal leaderboard request is reviewed before its score, version, and public state are published.

## Anti-gaming and anti-overfitting

The v0 design builds on the [RoboDojo evaluation-integrity protocol](https://robodojo-benchmark.com/leaderboard/protocol) and its [public repository commit `f57e163`](https://github.com/RoboDojo-Benchmark/RoboDojo/tree/f57e1633ffed59761bc8e568cfe7530c4b33381c), checked on 2026-10-31. It follows a verification pattern compatible with public reproducible benchmarks while focusing on contact-rich evidence:

- **Official scoring.** Official results come from DexLab execution, not client-computed scores, screenshots, or self-reported logs.
- **Public layouts for reproduction.** Published tasks and configurations remain inspectable for local iteration.
- **Hidden verification layouts.** A formal leaderboard run also uses unpublished scene variations to detect hardcoded coordinates, scene memorization, and tuning against public layouts. Hidden cases are an auxiliary consistency check, not a replacement for the public primary set.
- **Frozen budgets.** Seeds, repeat counts, timeouts, and resource caps are fixed per entry. Teams cannot choose the best run from an unreported pool.
- **Retain every attempt.** Infrastructure failure, model failure, timeout, and invalid execution remain distinct. Automatic retries are limited to predefined evaluator faults.
- **One fixed system.** A leaderboard entry uses one checkpoint and one inference procedure across every task. Per-task routing to different model or checkpoint variants is not allowed.
- **Technical review.** DexLab reviews adapters, action interfaces, duplicate systems, minimally changed variants, and suspicious task selection without requesting unauthorized credentials.
- **Public correction.** Changes to tasks, scorers, or qualification rules create a new cohort; old results and denominators remain.

Hidden layouts reduce public-set overfitting; they do not prove real-world generalization. Safety-critical claims still require physical robots, materials, and independent measurement.

## `local`, `official verified`, and `reproducible`

Reports and leaderboard entries use three distinct states:

| State | Meaning | Leaderboard eligible |
| --- | --- | --- |
| `local / unverified` | The team ran it locally. Useful during development, but official tasks, budgets, and scoring are not established. | No |
| `official verified` | DexLab ran a frozen cohort, passed interface checks, leakage checks, and anti-gaming review. | Yes |
| `reproducible` | An official entry also publishes a deployable description, configuration, result explanation, and enough external-review material. | Verified badge plus reproducibility badge |

An official run with private raw evidence can be verified, but it is not externally reproducible. Publication of weights, code, raw trajectories, and video remains the team's choice and is shown on the entry. Internal DexLab review is not equivalent to independent community review.

## Remote model interface boundary

The pilot prioritizes a remote model service:

- `reset`: clear session state before a new episode;
- `act`: receive deployable observations and return an action or action chunk;
- `health`: report whether the model is loaded and its version;
- fixed request timeout and action frequency;
- credentials transferred only through a private channel;
- no access to scorer state, future state, or simulator-privileged observations;
- request count, errors, timeouts, and version changes included in receipts.

The concrete schema, concurrency protocol, and network limits will be frozen before a pilot. The repository does not yet publish a hosted endpoint that external teams can connect to.

## What current evidence establishes

Existing cases show that DexLab can separate task outcome, record integrity, numerical consistency, and physical reference. For example:

- changing the contact term in the Wuji sphere-pinch fixture reduces two-second hold displacement from **2.734 mm to 1.025 mm** under the same control;
- sponge wiping passes 3/3 with the original assistance and 0/3 without it; final cleaning is approximately **95.47%** versus **39.92%**;
- cutting, cloth, and contact studies retain failures, parameters, and offline-rescorable records.

These are scene and scoring evidence, not general model scores, and they do not rank every engine or every model.

## Request a pilot

Use the [model-evaluation request template](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+). Put only publishable organization, model type, robot configuration, and evaluation goals in the public issue. **Do not submit API keys, access tokens, private addresses, checkpoint credentials, or non-public data.**

The current pilot is coordinated manually to establish the interface, budget, and privacy boundary. Until self-service submission and the public leaderboard are implemented, no private request is represented as scheduled or accepted.
