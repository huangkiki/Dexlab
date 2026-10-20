# DexLab

**Reproducible contact, friction and manipulation experiments to understand why robots hold or slip, and how to choose and tune a physics simulation.**

[简体中文](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [Quickstart](#quickstart) · [Full experiment index](experiments.md) · [Reports](results.md)

(research-findings)=
## Experiments we have run

```{raw} html
<span id="visual-experiment-catalogue"></span>
```

Click an experiment or GIF for the full report and reproduction steps.

````{list-table}
:header-rows: 1
:widths: 20 45 35

* - Experiment
  - Animated preview
  - Result
* - ```{raw} html
    <span id="rss"></span>
    ```

    [RSS wiping](rss-wiping.md)
  - ```{image} ../../../docs/evidence/rss-wiping/preview.gif
    :alt: RSS original / no latch, 2×
    :width: 300px
    :target: rss-wiping.html
    ```

  - Retains the sponge with auxiliary constraints; slips without them. Wiping reproduction.
* - ```{raw} html
    <span id="cut-push"></span><span id="banana-force"></span>
    ```

    [Cutting and pushing](cut-push.md)
  - ```{image} ../../../docs/evidence/cutting/tofu-cut-push/surface.gif
    :alt: Tofu-like / banana-like material
    :width: 145px
    :target: cut-push.html
    ```

    ```{image} ../../../docs/evidence/cutting/banana-cut-push/surface.gif
    :alt: Tofu-like / banana-like material
    :width: 145px
    :target: cut-push.html
    ```

  - Blade contact pushes synthetic material; [separate single-cut force results do not establish convergence](banana-force.md).
* - ```{raw} html
    <span id="scoring"></span>
    ```

    [Cross scoring](tofu-scoring.md)
  - ```{image} ../../../docs/evidence/cutting/tofu-scoring/particles.gif
    :alt: Native particle cut history
    :width: 300px
    :target: tofu-scoring.html
    ```

  - Two shallow cuts leave a connected base; colors show cut history.
* - ```{raw} html
    <span id="apple"></span>
    ```

    [Apple-stem grasp](apple-replays)
  - ```{image} ../../../demos/apple-stem-grasp/media/mujoco-sdf.gif
    :alt: Historical scripted MuJoCo / SuperDex runs
    :width: 145px
    :target: experiments.html#apple-replays
    ```

    ```{image} ../../../demos/apple-stem-grasp/media/superdex-sdf.gif
    :alt: Historical scripted MuJoCo / SuperDex runs
    :width: 145px
    :target: experiments.html#apple-replays
    ```

  - Historical scripted MuJoCo / SuperDex runs both complete a 3 s hold.
* - ```{raw} html
    <span id="cloth-comparison"></span>
    ```

    [Cloth engine comparison](cloth-comparison.md)
  - ```{image} ../../../docs/evidence/cloth-studio/sag.gif
    :alt: Cloth engine comparison
    :width: 300px
    :target: cloth-comparison.html
    ```

  - Historical cloth responses across four engines, retaining failures and coverage gaps.
* - ```{raw} html
    <span id="cloth"></span>
    ```

    [Robot cloth grasp](experiments.md)
  - ```{image} ../../../docs/evidence/cloth-studio/grasp.gif
    :alt: Cloth grasp, lift and release
    :width: 300px
    :target: experiments.html
    ```

  - One development scene lifts, holds and releases; active folding remains unverified.
* - ```{raw} html
    <span id="visual-highlight-pinch"></span>
    ```

    [Force-limit comparison](pinch)
  - ```{image} ../../../docs/evidence/force-limit/comparison.gif
    :alt: Actuator limit 0.4 N / 0.8 N
    :width: 300px
    :target: visual-comparisons.html#pinch
    ```

  - In the same Genesis protocol, actuator limits of 0.4 N slip and 0.8 N hold.
* - ```{raw} html
    <span id="visual-highlight-libero"></span>
    ```

    [LIBERO replay](libero-workflow.md)
  - ```{image} ../../../docs/evidence/visual/libero-demo0-baseline.gif
    :alt: Demo 0 native baseline state replay
    :width: 300px
    :target: libero-workflow.html
    ```

  - 500 official demonstrations: 495 task successes; none pass every numerical diagnostic.
* - ```{raw} html
    <span id="visual-highlight-incline"></span>
    ```

    [Six-engine incline](incline)
  - ```{image} ../../../docs/evidence/visual/incline-sliding-0.001.gif
    :alt: Sliding records at 1 ms timestep
    :width: 300px
    :target: visual-comparisons.html#incline
    ```

  - Compare sliding responses across six engines; equal parameter values do not imply equivalent models.
* - ```{raw} html
    <span id="visual-highlight-normal"></span>
    ```

    [Normal contact calibration](normal)
  - ```{image} ../../../docs/evidence/visual/normal-calibration.gif
    :alt: Loading, hold and unloading against a synthetic target
    :width: 300px
    :target: visual-comparisons.html#normal
    ```

  - Loading fits a synthetic target better; unloading and transfer need separate validation.
````

[Full experiment index](experiments.md) · GIFs show actual simulation or recorded-state replay; results apply to each report’s configuration and conditions.

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

Cloth engine comparison <cloth-comparison>

Experiments <experiments>
Quickstart <quickstart>
Results <results>
Coverage <coverage>
Findings <experience>
Diagnosis <diagnosis>

Solver synchronization and preCICE <solver-coupling>

RSS wiping and latch ablation <rss-wiping>
Continuous cutting and blade-face pushing <cut-push>
Banana single-cut force <banana-force>
Synthetic tofu halving <cutting>
Sequential banana slicing <banana-cutting>
Crossed shallow tofu cuts <tofu-scoring>
Cutting method comparison <cutting-comparison>
Two tofu cuts and independent motion <tofu-comparison>
Cutting fidelity and measurements <cutting-fidelity>
Cutting-surface reconstruction <cutting-surface>

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
