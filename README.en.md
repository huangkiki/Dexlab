<a id="architecture"></a>
<p align="center">
  <a href="docs/site/_static/images/dexlab-architecture.jpg">
    <img src="docs/site/_static/images/dexlab-architecture.jpg" width="100%" alt="DexLab architecture: tasks and protocols, systems under test, action execution, environment backends, and evidence and scoring">
  </a>
</p>

<p align="center">
  <strong>From manipulation tasks to physical evidence, improving simulation and models together.</strong><br>
  Contact-rich manipulation · Reproducible experiments · Failure attribution
</p>

<p align="center">
  <a href="README.md">简体中文</a> ·
  <a href="https://huangkiki.github.io/Dexlab/en/latest/">Documentation</a> ·
  <a href="#why-dexlab">Why DexLab</a> ·
  <a href="#whats-new">What's new</a> ·
  <a href="#quickstart">Quick start</a>
</p>

DexLab supports research on grasping, wiping, deformable manipulation and cutting. It connects **task execution, native contact records and independent scoring** so researchers can locate a failure and decide what to change next.

## From tasks to evidence

Read the architecture from left to right:

1. **Tasks and protocols:** fix scenes, initial states, seeds, budgets and acceptance criteria before deciding whether a task succeeded.
2. **Systems under test:** connect scripts, policies or models. RoboAPI handles model calls and sessions; each task owns its observation and action semantics.
3. **Action execution:** translate high-level actions through IK, planning and control into robot inputs, recording commands separately from measured feedback.
4. **Environment backends:** advance contact and motion in the applicable physics backend, recording engine versions, contact models and solver configurations for each task.
5. **Evidence and scoring:** retain states, contacts and failed trajectories. Independent criteria check outcomes and guide changes to the model, controller or physics configuration.

*Task thumbnails illustrate the research scope; actual runs appear in the experiment previews below. Native experiments, contact readback, independent scoring and offline rescoring are available. Remote model execution and the public leaderboard remain under construction. [Uranus](https://huangkiki.github.io/Dexlab/en/latest/uranus-backend.html) is a candidate generative backend; see the [coverage matrix](https://huangkiki.github.io/Dexlab/en/latest/coverage.html) for actual task coverage.*

## Why DexLab?

A failed grasp can come from an unlearned policy, an action that was not executed as intended, or unsuitable collision geometry or contact modeling. A success rate or video alone rarely identifies which layer to change.

- **Explain failures.** Align control commands, native contact and object motion to distinguish task failures, integration errors and physical-computation problems.
- **Make comparisons traceable.** Fix tasks, versions and budgets; retain failures and uncovered cases so each conclusion refers to a concrete experiment.
- **Make improvements checkable.** Score raw records independently, then use new controlled comparisons to assess changes to a model or simulation configuration.

This defines DexLab's research direction: **use models to expose simulation gaps, then improve models with more trustworthy simulation.** The [dexterous-hand simulation guide](https://huangkiki.github.io/Dexlab/en/latest/dexterous-hand-simulation.html) explains the questions; the [failure audit](https://huangkiki.github.io/Dexlab/en/latest/solver-failure-audit.html) provides existing evidence.

<a id="whats-new"></a>
## What's new

- **2026-11-02 · Research guides** — Published the [six layers of dexterous-hand simulation](https://huangkiki.github.io/Dexlab/en/latest/dexterous-hand-simulation.html) and [topic guide to 35 Newton papers](https://huangkiki.github.io/Dexlab/en/latest/newton-reading-guide.html), connecting concepts, papers and experiments.
- **2026-10-31 · RoboAPI adapter** — Added model discovery, continuous sessions, action validation and execution receipts. Per-task observation/action mappings remain pending. [Adapter guide](docs/roboapi-poke.md)
- **2026-10-28 · Browser experiment** — Run MuJoCo in the browser and interactively inspect contact behavior under different solver configurations. [Open the live lab](https://huangkiki.github.io/Dexlab/en/latest/index.html#live-lab)
- **2026-10-26 · Wuji contact evidence** — Published the point/torsional-contact sphere-pinch comparison, independent scoring and an offline rescore bundle. [Experiment report](https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html)

## Experiment previews

These animations come from DexLab simulation recordings or recorded-state replays. Every result applies only to its reported version, material assumptions, and acceptance protocol.

<table>
<tr>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html">
<img src="docs/evidence/wuji-contact/comparison.gif" width="100%" alt="Wuji point contact and torsional contact comparison" loading="lazy">
</a>
<strong>Grasp and slip resistance</strong><br>
Under the same control, replacing point contact with synthetic torsional contact reduces two-second hold drift from <strong>2.734 mm</strong> to <strong>1.025 mm</strong>.
</td>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html">
<img src="docs/evidence/studio/rss.gif" width="100%" alt="Assisted sponge wiping replay" loading="lazy">
</a>
<strong>Sponge wiping and grasp dependence</strong><br>
Assisted retention passes <strong>3/3</strong>; removing assistance gives <strong>0/3</strong>, with final cleaning around <strong>95.47% / 39.92%</strong>.
</td>
</tr>
<tr>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/cloth-comparison.html">
<img src="demos/cloth-folding/media/compliance-grasp.gif" width="100%" alt="Robot grasping a deformable cloth in recorded simulation" loading="lazy">
</a>
<strong>Deformable manipulation</strong><br>
The robot can pinch and move a cloth patch, but complete folding still fails: the current record reaches <strong>12.55%</strong> edge strain against a 5% limit.
</td>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/cut-push.html">
<img src="docs/evidence/cutting/showcase.gif" width="100%" alt="Tofu and banana cutting recorded-state surface replay" loading="lazy">
</a>
<strong>Cutting and topology change</strong><br>
Continuous cutting and blade-face pushing change the simulated topology; the full report records contact force, material separation, and retained failures beyond the visual replay.
</td>
</tr>
</table>

<a id="quickstart"></a>
## Quick start

The shortest simulation entry is apple-stem grasping. On Linux x86_64 with [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh --mujoco-profile historical-3.11.0
bash demos/apple-stem-grasp/run.sh \
  --backend mujoco \
  --output demos/apple-stem-grasp/runs/first-mujoco
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/first-mujoco
```

The verifier writes `summary.json`; when all checks pass, `passed: true`. Fourteen seconds is simulation time, not expected wall time. Add `--headless` without a display and use a fresh output directory for every run.

To inspect the evidence chain without installing a simulator, start with the [GPU-free wiping rescore](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html#offline-evidence). Full dependencies, assets, and commands are in the [installation guide](https://huangkiki.github.io/Dexlab/en/latest/quickstart.html).

## Continue on the website

- [Experiments](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Full results](https://huangkiki.github.io/Dexlab/en/latest/results.html): conditions, metrics, failures, raw records and reproduction paths.
- [Model-evaluation protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html) · [Solver configuration roles](https://huangkiki.github.io/Dexlab/en/latest/solver-taxonomy.html): defining comparable model and physics experiments.
- [Dexterous-hand simulation guide](https://huangkiki.github.io/Dexlab/en/latest/dexterous-hand-simulation.html) · [Papers and references](https://huangkiki.github.io/Dexlab/en/latest/references.html): research questions, reading routes and original sources.

Results apply to their stated configurations and protocols; they do not establish hardware validity or a universal engine ranking. The website maintains research and usage details. [Contributing](https://huangkiki.github.io/Dexlab/en/latest/contributing.html) · [Current work](docs/current-work.md) · [Citation](https://huangkiki.github.io/Dexlab/en/latest/index.html#documentation-and-citation).
