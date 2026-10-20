# DexLab

**Reproducible contact, friction and manipulation experiments to understand why robots hold or slip, and how to choose and tune a physics simulation.**

[简体中文](README.md) · [Quickstart](#quickstart) · [Full experiment index](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Reports](https://huangkiki.github.io/Dexlab/en/latest/results.html)

<a id="research-findings"></a>

## Experiments we have run

<span id="visual-experiment-catalogue"></span>

Click a GIF from actual simulation or recorded-state replay for full videos, curves and reproduction. Successes, failures and conditions stay together.

<a id="rss"></a>

### RSS wiping: why does the sponge slip?

One gripper holds the bar while the other wipes off ink with a sponge. The left run retains RSS’s auxiliary node constraint; the right disables it.

<a href="https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html"><img src="docs/evidence/rss-wiping/preview.gif" width="880" alt="RSS wiping: why does the sponge slip?" loading="lazy"></a>

Across three repeats with fixed geometry and initial states, the original passed 3/3 with 95.5%–95.9% cleaning; disabling the constraint passed 0/3 with 39.9%–41.2% cleaning. This configuration depends on assisted retention; in-hand rotation is not reproduced. The GIF shows synchronized 10–30 s excerpts from trial 1 at 2× speed in the native collision-geometry view.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html)

The same recorded trajectory also supports **high-quality RTX replay**, retaining poses and sponge deformation while adding reflections, textures and soft shadows. [Matched views and reproduction](demos/rss-wiping/README.md#render-a-saved-trajectory--重渲染已有轨迹).

<a id="cut-push"></a>

### Sequential cutting: push the pieces with the final cut

Cut a tofu-like block into three pieces and a banana-like body into four, then lift the blade slightly and push sideways through knife contact.

<a href="https://huangkiki.github.io/Dexlab/en/latest/cut-push.html"><img src="docs/evidence/cutting/tofu-cut-push/surface.gif" width="420" alt="Sequential cutting: push the pieces with the final cut" loading="lazy"></a>
<a href="https://huangkiki.github.io/Dexlab/en/latest/cut-push.html"><img src="docs/evidence/cutting/banana-cut-push/surface.gif" width="420" alt="Sequential cutting: push the pieces with the final cut" loading="lazy"></a>

Piece motion comes from knife contact, with no direct velocity increment applied to the material. The overlays show recorded contact forces and piece displacements; the report pairs surface and particle views. These are synthetic materials, without real-food calibration or the paper’s force-measurement experiment.

Tofu and banana now share a paper-inspired reference linked volume: primal links store Hermite points and normals for the original boundary and recorded blade surfaces, native cut histories decide when links disconnect, and per-cell regions use QEF local dual vertices. Once native mechanical components separate, each is reconstructed as a closed volume; surface representatives follow a compatible TLMPM motion field through fixed weights. Particle views and frame measurements remain public, so a visible gap never substitutes for mechanical acceptance. The current CPU offline reconstruction supports recorded x/y straight planes only; arbitrary curved or tilted paths, the paper's online local GPU update and real-food geometry remain unimplemented. [Surface implementation and limits](docs/site/en/cutting-surface.md)

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/cut-push.html)

<a id="banana-force"></a>

### Banana single-cut force: does particle refinement converge?

Use the paper's published banana values, an independent perfect-J2 return, and a frozen protocol for the blade path, sampling, timestep and contact sensitivity.

<a href="https://huangkiki.github.io/Dexlab/en/latest/banana-force.html"><img src="docs/evidence/cutting/banana-force/force-protocol.svg" width="880" alt="Banana single-cut force: 20 samplings, 64-times particle refinement, force channels and sensitivity" loading="lazy"></a>

The pre-support material peak across 20 baseline runs is **0.8469 ± 0.1511 N**, with **0.07341 ± 0.01249 N·s** material impulse. The 64× particle run completes, but never reaches the support during the frozen 0.5 s path; its peak rises to **4.3059 N** and normalized RMSE against the baseline mean is **2.051**. The evidence therefore establishes neither timestep, contact or particle-refinement convergence nor real-banana force accuracy. Material, support, total resistance, actuator and guide channels remain separate.

[Complete result, frozen protocol and limits](https://huangkiki.github.io/Dexlab/en/latest/banana-force.html)

<a id="scoring"></a>

### Cross scoring: cuts with a connected base

Make a shallow cut, withdraw and rotate the knife by 90°, then cut again to inspect the incisions and connectivity.

<a href="https://huangkiki.github.io/Dexlab/en/latest/tofu-scoring.html"><img src="docs/evidence/cutting/tofu-scoring/particles.gif" width="880" alt="Cross scoring: cuts with a connected base" loading="lazy"></a>

Both the default and half-step records produce two shallow cuts with a connected base; the uncut control is rejected. Colors show native cut history. The current elastic surface rebounds after withdrawal, so color does not imply a permanently open incision.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/tofu-scoring.html)

<a id="apple"></a>

### Apple-stem grasping: can two fingers hold the stem?

OpenArm + Wuji pinch the apple stem with thumb and index finger, lift and hold. Historical development runs: MuJoCo on the left, SuperDex FP64 on the right.

<a href="https://huangkiki.github.io/Dexlab/en/latest/experiments.html#apple-replays"><img src="demos/apple-stem-grasp/media/mujoco-sdf.gif" width="420" alt="Apple-stem grasping: can two fingers hold the stem?" loading="lazy"></a>
<a href="https://huangkiki.github.io/Dexlab/en/latest/experiments.html#apple-replays"><img src="demos/apple-stem-grasp/media/superdex-sdf.gif" width="420" alt="Apple-stem grasping: can two fingers hold the stem?" loading="lazy"></a>

Both recorded 14 s trajectories pass the full 3 s hold check. Actions use known poses and fixed joint targets, with no attachment constraint on the apple. This qualifies the fixed simulation scene, not a vision policy or real-robot accuracy.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/experiments.html#apple-replays)

<a id="cloth"></a>

### Cloth grasping: hold and release after lifting

The robot grasps cloth through contact and friction, then lifts, holds and releases it.

<a href="https://huangkiki.github.io/Dexlab/en/latest/experiments.html"><img src="demos/cloth-folding/media/compliance-grasp.gif" width="880" alt="Cloth grasping: hold and release after lifting" loading="lazy"></a>

After geometry and compliance corrections, one 9 s development scene passes the fixed v3 criteria. The historical table-intersection failure is retained, and self-contact penetration remains near the threshold. This is cloth grasping, not successful active folding or cross-material robustness.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/experiments.html)

<a id="visual-highlight-pinch"></a>

### Gripper force limits: slipping at 0.4 N, holding at 0.8 N

Change the finger-joint drive-force limit in the same Genesis gripper scene and compare closing, lifting, holding and release.

<a href="https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#pinch"><img src="docs/evidence/force-limit/comparison.gif" width="880" alt="Gripper force limits: slipping at 0.4 N, holding at 0.8 N" loading="lazy"></a>

Under this protocol, the 0.4 N setting slips while 0.8 N retains the object; open-gripper controls and offset scenes are also recorded. A drive-force limit is not a measured contact force and cannot be read as a real gripper-force requirement.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#pinch)

<a id="visual-highlight-libero"></a>

### LIBERO: does task success also pass physical diagnostics?

Replay official actions, retain successes and failures, and inspect contact and state records. Below is the recorded-state replay of native baseline demo 0.

<a href="https://huangkiki.github.io/Dexlab/en/latest/libero-workflow.html"><img src="docs/evidence/visual/libero-demo0-baseline.gif" width="880" alt="LIBERO: does task success also pass physical diagnostics?" loading="lazy"></a>

The Object suite has valid records for all 500 official demonstrations across ten tasks: 495 native task successes, five failures, and zero passes of all numerical diagnostics. The GIF is one existing replay, not evidence that all 500 succeed; this is not a closed-loop vision-policy evaluation.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/libero-workflow.html)

<a id="visual-highlight-incline"></a>

### Six-engine incline: why does the same block slide differently?

Compare static, sliding and nominally frictionless responses of a block with the same dimensions and mass. The GIF shows the sliding records at a 1 ms timestep.

<a href="https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#incline"><img src="docs/evidence/visual/incline-sliding-0.001.gif" width="880" alt="Six-engine incline: why does the same block slide differently?" loading="lazy"></a>

Responses from MuJoCo, SuperDex, Genesis, Newton Physics, PhysX and Drake retain their configurations, failures and invalid observations. Equal parameter values do not establish equivalent contact models; full curves help distinguish motion differences from observation problems.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#incline)

<a id="visual-highlight-normal"></a>

### Normal contact: after fitting loading, what happens on unloading?

Adjust contact parameters in one MuJoCo scene and compare indentation, holding and unloading.

<a href="https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#normal"><img src="docs/evidence/visual/normal-calibration.gif" width="880" alt="Normal contact: after fitting loading, what happens on unloading?" loading="lazy"></a>

Loading response can improve against the synthetic 20 kN/m target, while unloading, dynamics and mass transfer need separate validation. The replay preserves physical proportions; inspect the report curves for small displacements. A synthetic reference is not real-material calibration.

[Results and reproduction](https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#normal)

For historical cutting, collision, cloth mechanics, mass/size transfer and error–cost sweeps, see the [full experiment index](https://huangkiki.github.io/Dexlab/en/latest/experiments.html).

[Sources and conversion records for the new GIFs](docs/evidence/visual/homepage-previews.json).

<a id="quickstart"></a>

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

[Installation, dependencies and asset provenance](docs/installation.md) · [Task interface and commands](demos/apple-stem-grasp/README.md)

<a id="research-diagnosis"></a>

## When a scene behaves unexpectedly

Check geometry, mass/inertia, control timing and actual contact readback first. Adjust parameters around one concrete question and evaluate the recorded result independently. See the [diagnostic workflow](https://huangkiki.github.io/Dexlab/en/latest/diagnosis.html) for failures, fixes and next decisions.

<a id="research-selection"></a>

## Choosing an engine and configuration for a new task

Find nearby experiments by load, contact scale, sticking/sliding, contact transitions and compliance, then validate candidate configurations. The research includes MuJoCo, SuperDex, Genesis, Newton Physics, PhysX and Drake, with different task coverage and acceptance. See [coverage and versions](https://huangkiki.github.io/Dexlab/en/latest/coverage.html) and [starting strategies](https://huangkiki.github.io/Dexlab/en/latest/selection.html).

<a id="solver-coupling"></a>

## How multiple solvers work together

Simulation time, wall time and data-exchange intervals are distinct. Waiting affects speed, while delayed feedback can also affect the interaction. [Understand synchronization, iteration and preCICE through a finger-and-sponge example](https://huangkiki.github.io/Dexlab/en/latest/solver-coupling.html). preCICE is a methodological reference here, not an integrated DexLab component.

<a id="research-scope"></a>

## Current limits and further reading

Classical physical laws and existing empirical relations serve as references. Success applies to each experiment’s versions, scenes and criteria. Task success, numerical diagnostics and real-world physical accuracy are reported separately. In-hand rotation, active folding, real-material calibration and vision-policy capability still need their own validation.

[Research findings](https://huangkiki.github.io/Dexlab/en/latest/experience.html) · [Solver configuration roles](https://huangkiki.github.io/Dexlab/en/latest/solver-taxonomy.html) · [Research directions](https://huangkiki.github.io/Dexlab/en/latest/dexterity.html) · [External references](https://huangkiki.github.io/Dexlab/en/latest/references.html) · [Data and releases](https://github.com/huangkiki/Dexlab/releases)

[Development and acceptance](docs/autoresearch.md) · [Current work and pause state](docs/current-work.md)
