# DexLab

**Let robot models and physics simulators point out each other's blind spots on the same failures, then improve together.**

The model executes contact-rich tasks; DexLab records native contact readback and attributes failures. A physical gap improves the simulator; a policy gap returns to the model. Every change binds model version, simulator version, and raw evidence, then reruns the same protocol.

[简体中文](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [Co-evolution protocol](model-evaluation.md) · [Request a pilot](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+) · [Live Lab](#live-lab) · [Quickstart](#quickstart) · [Full experiment index](experiments.md) · [Reports](results.md)

(model-evaluation)=
## Simulator and model co-evolution

DexLab is for generalist manipulation models, VLA/WAM policies, agents acting as policies, and remote robot APIs. Customers provide their robot and interfaces; the model executes while DexLab records contact and failure, then feeds the result back to either the model or the simulator.

- **Loop:** run the model → record real contact → attribute the failure → improve one side and rerun the same protocol.
- **Score:** each task receives its own success rate; the headline metric is the equal-task macro average, with the full task matrix retained.
- **Physics boundary:** an invalid engine or scene run is not charged to the model; it becomes evidence for the next simulator improvement.
- **Anti-gaming:** only official execution enters the formal board. Public layouts support reproduction, hidden variations detect overfitting, and every attempt remains visible.
- **Evidence states:** `local / unverified`, `official verified`, and `reproducible` remain distinct; an official run is not presented as externally reproducible.

A remote model service is the preferred integration. The repository already shows that physical conditions change outcomes; once external models are connected, it can also record how model strategy changes outcomes. The remote executor and public leaderboard are still under construction.

[Read the full co-evolution and anti-gaming protocol](model-evaluation.md) · [Request a model evaluation](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+)

**Learn before reading the configuration table:** [Sim Learning](https://github.com/huangkiki/sim-learning) provides Chinese lessons, English terminology and native engine courses. Start with the [Physics-Based Simulation study route](https://github.com/huangkiki/sim-learning/blob/main/docs/physics-based-simulation.md#english-reading-guide), then the [solver guide](https://github.com/huangkiki/sim-learning/tree/main/docs/solver-guide). Course source checks remain separate from DexLab experimental qualification.

(live-lab)=
## Browser live lab

Run MuJoCo 3.17 WebAssembly and render with the browser's local WebGPU device directly
on this page. Three solver configurations share the same box, gravity, friction,
initial state and timestep. After pressing Run, inspect contacts, tangential displacement,
solver iterations and the measured simulation speed.

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

Browser runs do not inherit native experiment results. The renderer, MuJoCo version,
runtime and measured simulation speed are reported separately.

(research-findings)=
## Experiments we have run

```{raw} html
<span id="visual-experiment-catalogue"></span>
```

Click an experiment or GIF for the full report and reproduction steps.

| Experiment | Animated preview |
| --- | :---: |
| **[Wuji sphere pinch](wuji-contact.md)**<br>Same control and commands: synthetic torsional contact reduces two-second hold displacement from 2.734 to 1.025 mm, passing the original 2 mm limit. Rescore offline; not solver failure or hardware validation. | <a href="wuji-contact.html"><img src="_static/wuji-contact/comparison.gif" width="300" alt="Wuji v3 point contact and v4 torsional contact, full synchronized replay" loading="lazy"></a> |
| <a id="rss"></a>**[Sponge wiping](rss-wiping.md)**<br>Source: RoboSimStudio `wipe_the_bar`. The original uses compliant grasp assistance after contact readiness and releases it when the hand opens. Success does not establish friction-only retention; [see the unassisted comparison](latch). | <a href="rss-wiping.html#latch"><img src="_static/studio/rss.gif" width="300" alt="Assisted sponge wiping, RTX replay at 10–19.9 s" loading="lazy"></a> |
| <a id="cut-push"></a><a id="banana-force"></a>**[Cutting and pushing](cut-push.md)** | <a href="cut-push.html"><img src="_static/cutting/tofu-cut-push/surface-rtx.gif" width="207" alt="Tofu cutting and pushing in RTX" loading="lazy"></a> <a href="cut-push.html"><img src="_static/cutting/banana-cut-push/surface-rtx.gif" width="207" alt="Banana cutting and pushing in RTX" loading="lazy"></a> |
| <a id="scoring"></a>**[Cross scoring](tofu-scoring.md)** | <a href="tofu-scoring.html"><img src="_static/cutting/tofu-scoring/surface.gif" width="233" alt="Surface reconstruction from recorded states" loading="lazy"></a> |
| <a id="apple"></a>**[Apple-stem grasp](apple-replays)** | <a href="studio-rendering.html"><img src="_static/studio/apple.gif" width="412" alt="MuJoCo 3.16 / SuperDex 1.0 RTX replay" loading="lazy"></a> |
| <a id="cloth-comparison"></a>**[Cloth engine comparison](cloth-comparison.md)** | <a href="cloth-comparison.html"><img src="_static/cloth-studio/sag.gif" width="208" alt="Matched sag across four engines" loading="lazy"></a> |
| <a id="cloth"></a>**[Robot cloth grasp](experiments.md)** | <a href="experiments.html"><img src="_static/cloth-studio/grasp.gif" width="262" alt="Cloth grasp, lift and release" loading="lazy"></a> |
| <a id="visual-highlight-pinch"></a>**[Force-limit comparison](pinch)** | <a href="studio-rendering.html"><img src="_static/studio/pinch.gif" width="412" alt="Actuator limit 0.4 N / 0.8 N" loading="lazy"></a> |
| <a id="visual-highlight-libero"></a>**[LIBERO replay](libero-workflow.md)** | <a href="studio-rendering.html"><img src="_static/studio/libero.gif" width="206" alt="Demo 0 native baseline state replay" loading="lazy"></a> |
| <a id="visual-highlight-incline"></a>**[Six-engine incline](incline)** | <a href="studio-rendering.html"><img src="_static/studio/incline.gif" width="309" alt="Sliding records at 1 ms timestep" loading="lazy"></a> |
| <a id="visual-highlight-normal"></a>**[Normal contact calibration](normal)** | <a href="studio-rendering.html"><img src="_static/studio/normal.gif" width="412" alt="Loading, hold and unloading against a synthetic target" loading="lazy"></a> |

[Full experiment index](experiments.md) · GIFs show actual simulation or recorded-state replay; results apply to each report’s configuration and conditions.

[Which solver failed?](solver-failure-audit.md) reviews RSS tasks, existing failures and attribution limits.

(quickstart)=
## Rescore one wiping pair first (no GPU)

Download **one matched latch / no-latch raw recording pair** and recompute displacement and cleaning from particle and ink states. You need [uv](https://docs.astral.sh/uv/getting-started/installation/); the commands use an isolated Python 3.12 environment with only NumPy, Matplotlib and their dependencies. The first run needs network access for source and dependencies. The evidence archive itself is about **126 MiB**, expanding to **349 MiB**; allow 2 GB of free space. The checkout below includes only the directories needed for rescoring. Rescoring requires no simulator, GPU or model API key.

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

Solver synchronization and preCICE <solver-coupling>

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

Solver configuration roles <solver-taxonomy>

Visual comparisons <visual-comparisons>
Native LIBERO workflow <libero-workflow>
AMP recorder parity failure <amp-lift>
Selection <selection>
Engines <engines>
Roadmap <dexterity>
Ledger <research-ledger>
Benchmark <benchmark>
References <references>
Contributing <contributing>
```
