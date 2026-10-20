# DexLab

**Reproducible contact, friction and manipulation experiments to understand why robots hold or slip, and how to choose and tune a physics simulation.**

[简体中文](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [Quickstart](#quickstart) · [Full experiment index](experiments.md) · [Reports](results.md)

(research-findings)=
## Experiments we have run

```{raw} html
<span id="visual-experiment-catalogue"></span>
```

Click a GIF from actual simulation or recorded-state replay for full videos, curves and reproduction. Successes, failures and conditions stay together.

(rss)=
### RSS wiping: why does the sponge slip?

One gripper holds the bar while the other wipes off ink with a sponge. The left run retains RSS’s auxiliary node constraint; the right disables it.

```{raw} html
<a href="rss-wiping.html"><img src="_static/rss-wiping/preview.gif" width="880" alt="RSS wiping: why does the sponge slip?" loading="lazy"></a>
```

Across three repeats with fixed geometry and initial states, the original passed 3/3 with 95.5%–95.9% cleaning; disabling the constraint passed 0/3 with 39.9%–41.2% cleaning. This configuration depends on assisted retention; in-hand rotation is not reproduced. The GIF shows synchronized 10–30 s excerpts from trial 1 at 2× speed in the native collision-geometry view.

[Results and reproduction](rss-wiping.md)

(cut-push)=
### Sequential cutting: push the pieces with the final cut

Cut a tofu-like block into three pieces and a banana-like body into four, then lift the blade slightly and push sideways through knife contact.

```{raw} html
<a href="cut-push.html"><img src="_static/cutting/tofu-cut-push/surface.gif" width="420" alt="Sequential cutting: push the pieces with the final cut" loading="lazy"></a>
<a href="cut-push.html"><img src="_static/cutting/banana-cut-push/surface.gif" width="420" alt="Sequential cutting: push the pieces with the final cut" loading="lazy"></a>
```

Piece motion comes from knife contact, with no direct velocity increment applied to the material. The overlays show recorded contact forces and piece displacements; the report pairs surface and particle views. These are synthetic materials, without real-food calibration or the paper’s force-measurement experiment.

[Results and reproduction](cut-push.md)

(scoring)=
### Cross scoring: cuts with a connected base

Make a shallow cut, withdraw and rotate the knife by 90°, then cut again to inspect the incisions and connectivity.

```{raw} html
<a href="tofu-scoring.html"><img src="_static/cutting/tofu-scoring/particles.gif" width="880" alt="Cross scoring: cuts with a connected base" loading="lazy"></a>
```

Both the default and half-step records produce two shallow cuts with a connected base; the uncut control is rejected. Colors show native cut history. The current elastic surface rebounds after withdrawal, so color does not imply a permanently open incision.

[Results and reproduction](tofu-scoring.md)

(apple)=
### Apple-stem grasping: can two fingers hold the stem?

OpenArm + Wuji pinch the apple stem with thumb and index finger, lift and hold. Historical development runs: MuJoCo on the left, SuperDex FP64 on the right.

::::{grid} 1 1 2 2
:gutter: 3
:::{grid-item}
```{image} ../../../demos/apple-stem-grasp/media/mujoco-sdf.gif
:alt: Apple-stem grasping: can two fingers hold the stem?
:width: 420px
:target: experiments.html#apple-replays
```
:::
:::{grid-item}
```{image} ../../../demos/apple-stem-grasp/media/superdex-sdf.gif
:alt: Apple-stem grasping: can two fingers hold the stem?
:width: 420px
:target: experiments.html#apple-replays
```
:::
::::

Both recorded 14 s trajectories pass the full 3 s hold check. Actions use known poses and fixed joint targets, with no attachment constraint on the apple. This qualifies the fixed simulation scene, not a vision policy or real-robot accuracy.

[Results and reproduction](apple-replays)

(cloth)=
### Cloth grasping: hold and release after lifting

The robot grasps cloth through contact and friction, then lifts, holds and releases it.

```{image} ../../../demos/cloth-folding/media/compliance-grasp.gif
:alt: Cloth grasping: hold and release after lifting
:width: 880px
:target: experiments.html
```

After geometry and compliance corrections, one 9 s development scene passes the fixed v3 criteria. The historical table-intersection failure is retained, and self-contact penetration remains near the threshold. This is cloth grasping, not successful active folding or cross-material robustness.

[Results and reproduction](experiments.md)

(visual-highlight-pinch)=
### Gripper force limits: slipping at 0.4 N, holding at 0.8 N

Change the finger-joint drive-force limit in the same Genesis gripper scene and compare closing, lifting, holding and release.

```{raw} html
<a href="visual-comparisons.html#pinch"><img src="_static/force-limit/comparison.gif" width="880" alt="Gripper force limits: slipping at 0.4 N, holding at 0.8 N" loading="lazy"></a>
```

Under this protocol, the 0.4 N setting slips while 0.8 N retains the object; open-gripper controls and offset scenes are also recorded. A drive-force limit is not a measured contact force and cannot be read as a real gripper-force requirement.

[Results and reproduction](pinch)

(visual-highlight-libero)=
### LIBERO: does task success also pass physical diagnostics?

Replay official actions, retain successes and failures, and inspect contact and state records. Below is the recorded-state replay of native baseline demo 0.

```{raw} html
<a href="libero-workflow.html"><img src="_static/visual/libero-demo0-baseline.gif" width="880" alt="LIBERO: does task success also pass physical diagnostics?" loading="lazy"></a>
```

The Object suite has valid records for all 500 official demonstrations across ten tasks: 495 native task successes, five failures, and zero passes of all numerical diagnostics. The GIF is one existing replay, not evidence that all 500 succeed; this is not a closed-loop vision-policy evaluation.

[Results and reproduction](libero-workflow.md)

(visual-highlight-incline)=
### Six-engine incline: why does the same block slide differently?

Compare static, sliding and nominally frictionless responses of a block with the same dimensions and mass. The GIF shows the sliding records at a 1 ms timestep.

```{raw} html
<a href="visual-comparisons.html#incline"><img src="_static/visual/incline-sliding-0.001.gif" width="880" alt="Six-engine incline: why does the same block slide differently?" loading="lazy"></a>
```

Responses from MuJoCo, SuperDex, Genesis, Newton Physics, PhysX and Drake retain their configurations, failures and invalid observations. Equal parameter values do not establish equivalent contact models; full curves help distinguish motion differences from observation problems.

[Results and reproduction](incline)

(visual-highlight-normal)=
### Normal contact: after fitting loading, what happens on unloading?

Adjust contact parameters in one MuJoCo scene and compare indentation, holding and unloading.

```{raw} html
<a href="visual-comparisons.html#normal"><img src="_static/visual/normal-calibration.gif" width="880" alt="Normal contact: after fitting loading, what happens on unloading?" loading="lazy"></a>
```

Loading response can improve against the synthetic 20 kN/m target, while unloading, dynamics and mass transfer need separate validation. The replay preserves physical proportions; inspect the report curves for small displacements. A synthetic reference is not real-material calibration.

[Results and reproduction](normal)

For historical cutting, collision, cloth mechanics, mass/size transfer and error–cost sweeps, see the [full experiment index](experiments.md).

[Sources and conversion records for the new GIFs](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/visual/homepage-previews.json).

(quickstart)=
## Start with apple-stem grasping

Start with the MuJoCo apple-stem grasp covered by the existing setup script. You need Linux x86_64 and [uv](https://docs.astral.sh/uv/getting-started/installation/), with no model API key. This reproduces the pinned historical demo, not a latest-version six-engine comparison environment.

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
```

After SDF preparation, settling and planning, the viewer shows the stem grasp, lift and hold. Outputs go to `demos/apple-stem-grasp/runs/latest-mujoco-sdf/`. Add `--headless` without a display, or select `--backend superdex`. The 14 s simulation takes longer in wall time.

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

The verifier writes `summary.json`. When every check passes, `passed` is `true`; failures retain the individual checks and return a nonzero exit code.

[Installation, dependencies and asset provenance](https://github.com/huangkiki/Dexlab/blob/main/docs/installation.md) · [Task interface and commands](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md)

(research-diagnosis)=
## When a scene behaves unexpectedly

Check geometry, mass/inertia, control timing and actual contact readback first. Adjust parameters around one concrete question and evaluate the recorded result independently. See the [diagnostic workflow](diagnosis.md) for failures, fixes and next decisions.

(research-selection)=
## Choosing an engine and configuration for a new task

Find nearby experiments by load, contact scale, sticking/sliding, contact transitions and compliance, then validate candidate configurations. The research includes MuJoCo, SuperDex, Genesis, Newton Physics, PhysX and Drake, with different task coverage and acceptance. See [coverage and versions](coverage.md) and [starting strategies](selection.md).

(solver-coupling)=
## How multiple solvers work together

Simulation time, wall time and data-exchange intervals are distinct. Waiting affects speed, while delayed feedback can also affect the interaction. [Understand synchronization, iteration and preCICE through a finger-and-sponge example](solver-coupling.md). preCICE is a methodological reference here, not an integrated DexLab component.

(research-scope)=
## Current limits and further reading

Classical physical laws and existing empirical relations serve as references. Success applies to each experiment’s versions, scenes and criteria. Task success, numerical diagnostics and real-world physical accuracy are reported separately. In-hand rotation, active folding, real-material calibration and vision-policy capability still need their own validation.

[Research findings](experience.md) · [Solver configuration roles](solver-taxonomy.md) · [Research directions](dexterity.md) · [External references](references.md) · [Data and releases](https://github.com/huangkiki/Dexlab/releases)

[Development and acceptance](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.md) · [Current work and pause state](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.md)

```{toctree}
:hidden:
:maxdepth: 1

Experiments <experiments>
Quickstart <quickstart>
Results <results>
Coverage <coverage>
Findings <experience>
Diagnosis <diagnosis>

Solver synchronization and preCICE <solver-coupling>

RSS wiping and latch ablation <rss-wiping>
Continuous cutting and blade-face pushing <cut-push>
Synthetic tofu halving <cutting>
Sequential banana slicing <banana-cutting>
Crossed shallow tofu cuts <tofu-scoring>
Cutting method comparison <cutting-comparison>
Two tofu cuts and independent motion <tofu-comparison>
Cutting fidelity and measurements <cutting-fidelity>

Solver configuration roles <solver-taxonomy>

Visual comparisons <visual-comparisons>
Native LIBERO workflow <libero-workflow>
Selection <selection>
Engines <engines>
Roadmap <dexterity>
Ledger <research-ledger>
Benchmark <benchmark>
References <references>
Contributing <contributing>
```
