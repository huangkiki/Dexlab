# DexLab

## Contact-rich robotics, beyond rigid-body simulation.

DexLab is a physics-centric research platform for robot manipulation involving contact, deformation, and material separation.

[简体中文](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [Experiments](experiments.md) · [Research protocol](model-evaluation.md) · [Quick start](#quickstart) · [Architecture](#architecture) · [Uranus backend](uranus-backend.md)

> Native commands, contact readback, independent scoring, offline evidence, and several contact experiments are available today. Remote model execution, a public leaderboard, and cross-task unified conclusions are still being built.

## Research vision: Simulation–Learning Co-evolution

> **Models expose simulation gaps; more trustworthy simulation then produces better models.**

The near-term center is a **Physics Research Platform**: contact, deformation, and material separation become observable, attributable, and rescorable experiments. The long-term loop feeds model failures back into simulation, then uses improved simulation to train and evaluate models.

<a id="architecture"></a>
## Architecture

<img src="_static/images/dexlab-architecture.svg" width="100%" alt="DexLab execution and evaluation architecture with tasks, model, action execution, environment backends, independent evidence, and co-evolution feedback">

The task protocol fixes scenes and budgets. A model emits actions, a controller maps them to native physics or a candidate generative backend, and an independent evidence layer records native state, contact readback, and outcomes. The feedback loop is credited only when the corresponding evidence exists.

## What's new

- **2026-10-31 · Uranus generative backend:** added the candidate backend contract, candidate tasks, paired native/generative evaluation plan, and evidence boundaries. It is documented, not yet a DexLab runner. [Details](uranus-backend.md)
- **2026-10-31 · Poke RoboAPI adapter:** added model discovery, schema/session handling, action validation, execution feedback, and a credential-safe CLI. Per-task observation/action mappings remain pending. [Details](https://github.com/huangkiki/Dexlab/blob/main/docs/roboapi-poke.md)
- **2026-10-31 · Model-evaluation protocol:** added the public evaluation, anti-gaming, evidence-state, and hidden-layout protocol. Remote execution and the public leaderboard are still under construction. [Details](model-evaluation.md)

[All releases](https://github.com/huangkiki/Dexlab/releases)

## Demo gallery

These animations come from DexLab simulation recordings or recorded-state replays. Every result applies only to its reported version, material assumptions, and acceptance protocol.

| Grasp and slip resistance | Sponge wiping and grasp dependence |
| --- | --- |
| <a href="wuji-contact.html"><img src="_static/wuji-contact/comparison.gif" width="100%" alt="Wuji point and torsional contact comparison" loading="lazy"></a><br>Under the same control, synthetic torsional contact reduces two-second hold drift from **2.734 mm** to **1.025 mm**. | <a href="rss-wiping.html"><img src="_static/studio/rss.gif" width="100%" alt="Assisted sponge wiping replay" loading="lazy"></a><br>Assisted retention passes **3/3**; no assistance gives **0/3**, with final cleaning around **95.47% / 39.92%**. |
| **Deformable manipulation** | **Cutting and topology change** |
| <a href="cloth-comparison.html"><img src="_static/cloth-studio/grasp.gif" width="100%" alt="Robot grasping a deformable cloth in recorded simulation" loading="lazy"></a><br>The robot can pinch and move a cloth patch, but complete folding still fails: the current record reaches **12.55%** edge strain against a 5% limit. | <a href="cut-push.html"><img src="_static/cutting/showcase.gif" width="100%" alt="Tofu and banana cutting recorded-state replay" loading="lazy"></a><br>Continuous cutting and blade-face pushing create real topology changes; the full report records contact force, material separation, and retained failures. |

<section id="model-evaluation"></section>

## Why DexLab?

When a robot policy fails in simulation, we see one failure. It may come from the policy, controller, scene, contact discretization, material model, or numerical solver.

> **When a robot fails in simulation, is it the policy that fails, or the physics we trusted?**

DexLab makes these questions testable:

- Under matched geometry, load, and control, does the contact model change whether an object is held, slips, or releases?
- Do smaller timesteps, finer meshes, or more iterations approach the physical answer, or merely change numerical behavior?
- When can a robot grasp a cloth, and when can it actually fold, transfer, and release it?
- How should cutting, friction, and material separation be recorded and accepted beyond a video?
- Does a policy or API ranking survive replacement of the physics backend?

<section id="research-selection"></section>

## Research areas

| Area | Research question | Current entry |
| --- | --- | --- |
| **Contact physics** | Are normal response, friction, retention, sliding, impulse, and release independently checkable? | [Contact mechanics](contact-response.md) · [Hold and slip](wuji-contact.md) |
| **Deformable objects** | Can grasp, sag, stretch, layer contact, and release be scored separately? | [Cloth comparison](cloth-comparison.md) · [Replay rendering](studio-rendering.md) |
| **Topology-changing interaction** | How should cutting and material separation record contact, connectivity, and material response? | [Cutting and pushing](cut-push.md) |
| **Cross-backend evaluation** | When can engines, integrators, and solvers be compared under matched physical inputs? | [Engines](engines.md) · [Selection](selection.md) |
| **Policy and API evaluation** | How can model, adapter, and invalid-physics failures be separated? | [Evaluation](model-evaluation.md) · [RoboAPI adapter](https://github.com/huangkiki/Dexlab/blob/main/docs/roboapi-poke.md) |

<section id="research-findings"></section>

## Experiments and findings

| Experiment | Condition | Result and meaning |
| --- | --- | --- |
| **Contact representation changes the grasp verdict** | Wuji sphere pinch under matched control | `condim=3` drifts **2.734 mm**, above 2 mm; `condim=4` reaches **1.025 mm**. |
| **Wiping success depends on grasp assistance** | RoboSimStudio `wipe_the_bar` | Assisted **3/3**, cleaning around **95.47%**; unassisted **0/3**, around **39.92%**. |
| **Surface discretization changes the failure boundary** | Same cylinder, mass, force command, and step; only meshing changes | `256 → 1,024 → 4,096` triangles gives peak penetration **2.267 → 0.858 → 0.481 mm**. |
| **Grasp behavior can depend on the backend** | Apple-stem grasp, ten paired scenes | Current defaults pass MuJoCo **1/10** and SuperDex **10/10**; smaller steps do not monotonically reduce penetration. |
| **A stable cloth grasp is not a fold** | OpenArm + Wuji with passive cloth | Pinch, lift, and release pass; complete folding fails on strain, residual contact, and final geometry. |

Together, these results show why a success video is insufficient: **material models, contact response, and downstream policy transfer must be checked separately.**

[Full experiments](experiments.md) · [All results and failures](results.md) · [Research findings](experience.md)

(live-lab)=
## Browser live lab

Run MuJoCo 3.17 WebAssembly and render with the browser's WebGPU device. These browser runs do not inherit native experiment scores.

```{raw} html
<div class="dexlab-live-lab">
  <iframe
    src="../../_static/live-lab/index.html?embed=1"
    title="DexLab browser live simulation lab"
    loading="lazy"
    allow="fullscreen"
  ></iframe>
</div>
```

(quickstart)=
## Quick start

On Linux x86_64 with [uv](https://docs.astral.sh/uv/getting-started/installation/), run apple-stem grasping:

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

The verifier writes `summary.json`; when all checks pass, `passed: true`. Fourteen seconds is simulation time, not expected wall time. Add `--headless` without a display and use a fresh output directory.

To inspect the evidence chain without installing a simulator, start with [Quickstart](quickstart.md). Full dependencies and commands are on that page.

## Research roadmap

1. **Contact and material response:** calibrate stiffness, damping, friction, and real measurements before ranking engines.
2. **Deformable manipulation:** extend from pinch, transfer, and release to auditable folding geometry, self-contact, and material-point tracking.
3. **Topology-changing tasks:** define continuous geometry, contact-force, and outcome criteria for cutting, separation, and adhesion.
4. **Cross-backend attribution:** distinguish solver, integrator, collision geometry, precision, timestep, and framework wrapper.
5. **Policy and neural backends:** test whether API rankings and task conclusions transfer from native physics to learned world models.
6. **Co-evolution:** after evidence supports it, use model failures to improve simulation and improved simulation to train and evaluate better models.

## Ecosystem backend: Uranus

[Uranus](https://arxiv.org/abs/2609.24815) is a D-Robotics robot video world model that generates multi-view observations from future `qpos`, cameras, and robot geometry. It is currently a **documented candidate generative backend**, not a verified physics backend.

The integration path is `RoboAPI → IK/controller → qpos → Uranus → RGB → task scorer`. Uranus supplies visual observations; it does not provide native contact state, task success, or physical truth. [Read the full introduction, candidate tasks, and evidence boundary](uranus-backend.md).

<section id="research-diagnosis"></section>

## Evidence and boundaries

- Task success is not physical truth; numerical consistency is not real-world accuracy.
- A simulation pass is not hardware success; a rendered replay is not visual control.
- Engine coverage differs by task, material model, and acceptance condition; DexLab does not publish a universal engine ranking.
- Failures, invalid runs, and missing readouts remain visible; thresholds are not relaxed and counterexamples are not deleted.
- Uranus and remote model evaluation are candidates; an upstream paper or interface does not establish a DexLab reproduction.

<section id="research-scope"></section>

## Documentation and citation

[Experiments](experiments.md) · [Findings](experience.md) · [Solver roles](solver-taxonomy.md) · [Coverage](coverage.md) · [Contributing](contributing.md) · [Current Work](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.md)

No companion paper is published yet. When citing the repository, use its URL and a specific commit or release rather than attributing unpublished paper results.

```bibtex
@software{dexlab2026,
  author  = {DexLab contributors},
  title   = {DexLab: A Physics-Centric Research Platform for Contact-Rich Robot Manipulation},
  year    = {2026},
  url     = {https://github.com/huangkiki/Dexlab}
}
```

```{toctree}
:hidden:
:maxdepth: 1

Solver failure audit <solver-failure-audit>
Co-evolution and model evaluation <model-evaluation>
Studio replay rendering <studio-rendering>
Cloth engine comparison <cloth-comparison>
Experiments <experiments>
Quickstart <quickstart>
Results <results>
Coverage <coverage>
Findings <experience>
Diagnosis <diagnosis>
Wuji grasp and torsional contact <wuji-contact>
Contact prediction diagnostics <contact-response>
Sponge wiping and grasp-assistance comparison <rss-wiping>
Continuous cutting and blade-face pushing <cut-push>
Banana single-cut force <banana-force>
Synthetic tofu halving <cutting>
Sequential banana slicing <banana-cutting>
Crossed shallow tofu cuts <tofu-scoring>
Cutting method comparison <cutting-comparison>
Two tofu cuts and independent motion <tofu-comparison>
Cutting fidelity and measurements <cutting-fidelity>
Cutting-surface reconstruction <cutting-surface>
Solver synchronization and preCICE <solver-coupling>
Solver configuration roles <solver-taxonomy>
Visual comparisons <visual-comparisons>
Native LIBERO workflow <libero-workflow>
AMP recorder parity failure <amp-lift>
Selection <selection>
Engines <engines>
Uranus generative environment backend <uranus-backend>
Roadmap <dexterity>
Ledger <research-ledger>
Benchmark <benchmark>
References <references>
Contributing <contributing>
```
