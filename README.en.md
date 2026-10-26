# DexLab

**Reproducible contact, friction and manipulation experiments to understand why robots hold or slip, and how to choose and tune a physics simulation.**

[简体中文](README.md) · [Quickstart](#quickstart) · [Full experiment index](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Reports](https://huangkiki.github.io/Dexlab/en/latest/results.html)

<a id="research-findings"></a>

## Experiments we have run

<span id="visual-experiment-catalogue"></span>

Click an experiment or GIF for the full report and reproduction steps.

| Experiment | Animated preview |
| --- | :---: |
| <a id="rss"></a>**[RSS wiping](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html)**<br>Uses latch assistance: compliant constraints carry part of the sponge with the hand after grasping and release when it opens. Success does not establish friction-only retention; [see the no-latch comparison](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html#latch). | <a href="https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html#latch"><img src="docs/evidence/studio/rss.gif" width="300" alt="RSS original with latch assistance, RTX replay at 10–19.9 s" loading="lazy"></a> |
| <a id="cut-push"></a><a id="banana-force"></a>**[Cutting and pushing](https://huangkiki.github.io/Dexlab/en/latest/cut-push.html)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/cut-push.html"><img src="docs/evidence/cutting/tofu-cut-push/surface-rtx.gif" width="207" alt="Tofu cutting and pushing in RTX" loading="lazy"></a> <a href="https://huangkiki.github.io/Dexlab/en/latest/cut-push.html"><img src="docs/evidence/cutting/banana-cut-push/surface-rtx.gif" width="207" alt="Banana cutting and pushing in RTX" loading="lazy"></a> |
| <a id="scoring"></a>**[Cross scoring](https://huangkiki.github.io/Dexlab/en/latest/tofu-scoring.html)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/tofu-scoring.html"><img src="docs/evidence/cutting/tofu-scoring/surface.gif" width="233" alt="Surface reconstruction from recorded states" loading="lazy"></a> |
| <a id="apple"></a>**[Apple-stem grasp](https://huangkiki.github.io/Dexlab/en/latest/experiments.html#apple-replays)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/studio-rendering.html"><img src="docs/evidence/studio/apple.gif" width="412" alt="MuJoCo 3.16 / SuperDex 1.0 RTX replay" loading="lazy"></a> |
| <a id="cloth-comparison"></a>**[Cloth engine comparison](https://huangkiki.github.io/Dexlab/en/latest/cloth-comparison.html)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/cloth-comparison.html"><img src="docs/evidence/cloth-studio/sag.gif" width="208" alt="Matched sag across four engines" loading="lazy"></a> |
| <a id="cloth"></a>**[Robot cloth grasp](https://huangkiki.github.io/Dexlab/en/latest/experiments.html)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/experiments.html"><img src="docs/evidence/cloth-studio/grasp.gif" width="262" alt="Cloth grasp, lift and release" loading="lazy"></a> |
| <a id="visual-highlight-pinch"></a>**[Force-limit comparison](https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#pinch)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/studio-rendering.html"><img src="docs/evidence/studio/pinch.gif" width="412" alt="Actuator limit 0.4 N / 0.8 N" loading="lazy"></a> |
| <a id="visual-highlight-libero"></a>**[LIBERO replay](https://huangkiki.github.io/Dexlab/en/latest/libero-workflow.html)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/studio-rendering.html"><img src="docs/evidence/studio/libero.gif" width="206" alt="Demo 0 native baseline state replay" loading="lazy"></a> |
| <a id="visual-highlight-incline"></a>**[Six-engine incline](https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#incline)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/studio-rendering.html"><img src="docs/evidence/studio/incline.gif" width="309" alt="Sliding records at 1 ms timestep" loading="lazy"></a> |
| <a id="visual-highlight-normal"></a>**[Normal contact calibration](https://huangkiki.github.io/Dexlab/en/latest/visual-comparisons.html#normal)** | <a href="https://huangkiki.github.io/Dexlab/en/latest/studio-rendering.html"><img src="docs/evidence/studio/normal.gif" width="412" alt="Loading, hold and unloading against a synthetic target" loading="lazy"></a> |

[Full experiment index](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · GIFs show actual simulation or recorded-state replay; results apply to each report’s configuration and conditions.

[Studio replay and reproduction](https://huangkiki.github.io/Dexlab/en/latest/studio-rendering.html) · [Cutting-surface reconstruction and limits](https://huangkiki.github.io/Dexlab/en/latest/cutting-surface.html)

[Which solver failed?](docs/site/en/solver-failure-audit.md) compares RSS tasks and existing DexLab evidence, separating missing coupling, failed configurations and execution errors.

<a id="quickstart"></a>

## Rescore one wiping pair first (no GPU)

Download **one matched latch / no-latch raw recording pair** and recompute displacement and cleaning from particle and ink states. You need [uv](https://docs.astral.sh/uv/getting-started/installation/); the commands use an isolated Python 3.12 environment with only NumPy, Matplotlib and their dependencies. The first run needs network access for source and dependencies. The evidence archive itself is about **126 MiB**, expanding to **349 MiB**; allow 2 GB of free space. The checkout below includes only the directories needed for rescoring. Rescoring requires no simulator, GPU or model API key.

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/huangkiki/Dexlab.git
cd Dexlab
git sparse-checkout set --cone scripts demos/rss-wiping
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

Open `results/rss-wiping-v1/comparison.png`; the same directory contains two CSV files and `report.json`. This pair has maximum holding-patch centroid displacement of **0.061 / 449.981 mm** and final cleaning of **95.47% / 39.92%**. Both records should pass consistency checks; the no-latch `task_pass: false` is the retained experimental failure, not a failed download or rescore. Choose a new output directory for each rescore.

[Raw data and per-file licensing](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1) · [Scope, failed-attempt index and native rerun prerequisites](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html#offline-evidence). The bundle covers one historical pair and does not establish a general solver defect.

## To rerun a simulation: apple-stem grasping

From the checkout cloned above, the existing setup script runs the MuJoCo apple-stem grasp. You need Linux x86_64 and [uv](https://docs.astral.sh/uv/getting-started/installation/), with no model API key. This reproduces the pinned historical demo, not a latest-version six-engine comparison environment. Setup checks the versions and ownership of an existing `.venv` first. It refuses incompatible or shared environments; preserve them and install in a separate checkout.

```bash
git sparse-checkout disable
bash scripts/setup.sh --mujoco-profile historical-3.11.0
bash demos/apple-stem-grasp/run.sh --backend mujoco --output demos/apple-stem-grasp/runs/first-mujoco
```

After SDF preparation, settling and planning, the viewer shows the stem grasp, lift and hold. Outputs go to `demos/apple-stem-grasp/runs/first-mujoco/`. Add `--headless` without a display, or select `--backend superdex` with a new output directory. The 14 s simulation takes longer in wall time.

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/first-mujoco
```

Use a new directory for a second run, check it independently, then compare the reports:

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --output demos/apple-stem-grasp/runs/second-mujoco
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py demos/apple-stem-grasp/runs/second-mujoco
diff -u demos/apple-stem-grasp/runs/first-mujoco/summary.json demos/apple-stem-grasp/runs/second-mujoco/summary.json
```

`diff` returns 1 when reports differ. An explicit directory must be empty; successful and failed records are both preserved. Omitting `--output` generates a separate directory printed as `Run output:`; use that actual path for scoring.

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
