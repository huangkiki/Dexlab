# NeuralActuator: model actuator error separately; keep contact in physics

> **At a Glance**
>
> | Field | Details |
> | --- | --- |
> | **Work Covered** | *NeuralActuator: Neural Actuation Modeling for Robot Dynamics and External Force Perception* (MIT CSAIL / CDFG & Amazon Robotics, RSS 2026 Outstanding Systems Paper, [arXiv:2607.11734v2](https://arxiv.org/abs/2607.11734v2), 2026-07-17) |
> | **Pinned Sources** | [`Frank-ZY-Dou/Dynamics-Modeling@541a93a`](https://github.com/Frank-ZY-Dou/Dynamics-Modeling/tree/541a93aac4368e73883e86a51f31a7add6bde059/NeuralActuator) (MIT) · [Project Page](https://people.csail.mit.edu/frankzydou/projects/NeuralActuator/index.html) |
> | **Core Problem** | Low-cost servos exhibit nonlinear friction, backlash, saturation, and thermal drift while lacking joint torque sensors; using ideal $\tau = K_t I$ or position servos corrupts rollout accuracy and external force estimates. |
> | **Core Approach** | Feeds a 9-frame window of commands, joint state, and servo telemetry into a lightweight Transformer to predict a generalized effort trained via **differentiable simulation** from real pose trajectories (no torque labels), alongside 3D force, contact-gate, and motor-condition heads. |
> | **Open-Source Status** | Code (MIT), 11 checkpoints, the NAD dataset (OMX / SO-101 / Franka, 430 trajectories), and four differentiable backends (MJX, Newton, MuJoCo Warp, SuperDex) are all public. |
> | **DexLab Verdict** | **`pilot` (qualify hardware telemetry first, then pilot strictly at the actuator layer; never replace contact solvers)** — official training disables contact (`mjDSBL_CONTACT`), so actuator error and contact loads must stay explicitly separated. |

---

## 1. What This Work Actually Does

NeuralActuator targets a concrete gap in low-cost manipulation (~\$500–\$3,000 arms such as SO-101 and OpenManipulator-X): these robots lack joint torque sensors, yet their servos stream joint positions, velocities, current/load registers, voltage, and temperature. The paper encapsulates these **history-dependent actuator dynamics** as a modular neural actuation layer portable across multiple differentiable simulators.

### Problem Setup & I/O

- **Bottleneck**: Under a 500 g payload, a linear current-to-torque law $\tau = K_t I$ misses gearbox friction, backlash, saturation, and heating, causing simulated trajectories to drift from real executions. Conversely, replacing the entire simulator with an end-to-end black-box world model throws away rigid-body mechanics and mixes actuator error with contact error.
- **Inputs**: A 9-frame history window $\mathbf{X}_t$ (8 past frames + current frame). On OpenManipulator-X (4 arm joints + gripper), each step has 36 features: 5 commanded targets, 4 joint angles + gripper aperture, 5 currents, 5 velocities, 5 voltages, 5 temperatures, target aperture, and two tracking errors (replaced by signed load registers on SO-101 and commanded torques on Franka).
- **Outputs (4 heads over a shared pooled representation)**:
  1. Generalized simulator effort (torque surrogate) $\boldsymbol{\tau}_t^{\mathrm{pred}} \in \mathbb{R}^{n_m}$;
  2. Raw 3D end-effector external force $\hat{\mathbf{f}}_{\mathrm{raw}} \in \mathbb{R}^3$;
  3. Contact probability gate $g \in [0,1]$ (supervised by $\|\mathbf{f}_{\mathrm{gt}}\|_2 > 0.01\ \mathrm{N}$), producing gated force $\hat{\mathbf{f}} = g\hat{\mathbf{f}}_{\mathrm{raw}}$;
  4. Per-motor condition score $\mathbf{c} \in [0,1]^{n_m}$ (normal vs. mechanically restricted).

### System Pipeline & Four Core Modules

1. **Lightweight Gated-Attention Transformer (`models/transformer.py`)**: Projects inputs to 192 dimensions with learned positional embeddings and runs 4 pre-norm encoder layers (4 heads, 384-D FFN, query-dependent elementwise attention gate $\sigma(\mathbf{U}\mathbf{W}_g)$). At **1.44M parameters, 5.46M FLOPs, and 0.25 ms mean latency (~4,019 Hz)**, it fits inside fast control and simulation loops.
2. **Torque-Label-Free Differentiable Rollout Training (§III-B)**: Passes $\boldsymbol{\tau}_t^{\mathrm{pred}}$ into a differentiable simulator to step forward and backpropagates through time (BPTT) against real joint-angle trajectories (Huber loss, with gripper error scaled by $\kappa_g=1000$), avoiding physical torque sensing altogether.
3. **Engine-Portable Actuator Interface**: Keeps model, data, and loss unchanged while swapping four differentiable backends—**MJX, Newton, MuJoCo Warp, and SuperDex** (via a separate differentiable fork exposing per-step adjoints)—demonstrating that actuator dynamics can be cleanly separated from the physics engine.
4. **Neural Actuation Dataset (NAD, §IV)**: Twin-arm leader–follower teleoperation dataset (430 trajectories; 94.52 min OMX core subset) spanning free motion (34.15 min), payload-labeled (100–500 g) and six-axis F/T sensor interactions (46.24 min), and Joint-3 rubber-band mechanical restriction (14.13 min), plus SO-101 and Franka subsets.

![Figure 3: NeuralActuator pipeline and four-head Transformer architecture](https://arxiv.org/html/2607.11734v2/Figs/fig_pipeline.png)

*Figure 1 (from [Paper Figure 3](https://arxiv.org/html/2607.11734v2#S3.F3)): Nine frames of commands and servo telemetry enter a 4-layer gated Transformer predicting a torque surrogate, raw external force, contact gate, and motor condition; the torque surrogate drives a differentiable simulator supervised by real pose transitions.*

### Core Mechanism & Load-Bearing Equations

The key architectural trade-off lies between **torque-label-free BPTT** and **physical identifiability**:

$$
\mathbf{s}_{t+1} = F_t\!\left(\mathbf{s}_t, \boldsymbol{\tau}_t^{\mathrm{pred}}\right), \qquad
\boldsymbol{\tau}_t^{\mathrm{pred}} = g_\theta(\mathbf{X}_t), \qquad
\frac{d\mathbf{s}_{t+1}}{d\theta} = \frac{\partial F_t}{\partial \mathbf{s}_t}\frac{d\mathbf{s}_t}{d\theta} + \frac{\partial F_t}{\partial \boldsymbol{\tau}_t^{\mathrm{pred}}}\frac{d g_\theta(\mathbf{X}_t)}{d\theta}
$$

In rigid-body dynamics, inverse-dynamics generalized torque equals actuator torque plus external loads mapped through the Jacobian:

$$
\boldsymbol{\tau}_{\mathrm{ID}} = M(q)\ddot{q} + C(q,\dot{q})\dot{q} + \mathbf{g}(q) = \boldsymbol{\tau}_{\mathrm{act}} + J_v(q)^{\top}\mathbf{f}^{\mathrm{ext}}
$$

- $F_t(\cdot)$: single-step differentiable physics integrator; $g_\theta(\mathbf{X}_t)$: direct effort prediction (Table XIV shows direct outperforms residual $\tau_{\mathrm{base}}(u_t)+\Delta g_\theta$);
- $\boldsymbol{\tau}_{\mathrm{act}}$ and $J_v(q)^{\top}\mathbf{f}^{\mathrm{ext}}$: physical actuator torque vs. external end-effector force mapped to joint space;
- **Physical intuition & hidden tension**: Under default **implicit coupling**, only $\boldsymbol{\tau}_t^{\mathrm{pred}}$ drives the simulator while predicted external force $\hat{\mathbf{f}}$ is supervised but **never applied to dynamics**. Any effective effort that matches observed poses lowers the loss—so $\boldsymbol{\tau}_t^{\mathrm{pred}}$ acts as a **simulator-equivalent generalized effort** that can absorb unmodeled payloads rather than an identifiable physical actuator torque.

### Main Experiments, Results, and Built-in Counterexamples

| Experiment / Source (Author-Reported) | Setup & Protocol | Key Metrics | What This Proves / Counterexample |
| --- | --- | --- | --- |
| **OMX payload vs. model-based baselines** ([Table VII](https://arxiv.org/html/2607.11734v2#S5.T7)) | 100-step rollout across 7 tasks (200–500 g); baselines read GT state per step, NeuralActuator uses own rollout | Force MAE: ID-Linear `1.41 N`, ID-Friction `1.23 N`, GMO `0.66 N` → NeuralActuator **`0.12 N`** | Fixed linear $K_t I$ fails on these low-cost servos; does not prove all classical models fail universally |
| **OMX free-motion & F/T interaction** (Tables III–VI) | 500–600 steps (~10 s), 8/1/1 trajectory split per task | No-load joint MAE `2.8–3.2°` (grip `0.2 mm`); 6-dir F/T force MAE `0.23 N` (no-contact ref ~`0.00–0.01 N`); force gauge `0.08–0.10 N` | Controlled drift over 10 s rollouts; contact gate suppresses zero-force drift |
| **Direct vs. Residual & Implicit vs. Explicit coupling** ([Table XIV](https://arxiv.org/html/2607.11734v2#S5.T14)) | OMX 3 seeds, SO-101 6 tasks; explicit injects $\hat{\mathbf{f}}$ via $J_v^\top f$ | OMX worst joint MAE: Direct `0.39°` vs Residual `0.64°`; **counterexample: explicit coupling worsens both OMX (`0.88°→1.33°`) and SO-101 (`2.50°→6.90°`)** | Closing the dynamics loop with predicted force hurts rollouts, showing implicit accuracy relies on surrogate absorption |
| **Cross-platform validation** (Tables IX–X) | Trained from scratch on SO-101 (STS3215) & Franka Panda (7-DoF) | SO-101 500-step force MAE `0.47–0.73 N`, **worst joint MAE `9.77°`**; Franka offline future-state-conditioned force MAE `0.26–0.42 N` | Accuracy degrades markedly on cheaper servos; Franka is an offline force benchmark, not closed-loop rollout |
| **Motor-condition detection** ([Table XI](https://arxiv.org/html/2607.11734v2#S5.T11)) | Rubber bands restricting Joint 3, 4 held-out trajectories; baselines use 64-step windows | NeuralActuator Acc **`91.0%`** / Recall **`96.2%`** / AUC **`0.95`** (Random Forest `67.1% / 52.4% / 0.72`) | Independently confirms telemetry history carries nonlinear mechanical state, though not lifetime/fault prediction |
| **Online adaptation & force-aware BC** (Tables VIII, XIII) | 12 new trajectories (7,810 frames, 356 s fine-tuning); 40 real BC trials | Curve-level tracking error down ~`44%`; Pick-and-Place `80%→92.5%`, Lift-and-Hold `85%→95%` | Effective within fixed tasks and pretrained payload ranges; not general OOD payload transfer |

![Figure 15: Implicit vs. explicit external-force coupling on OMX](https://arxiv.org/html/2607.11734v2/Figs/fig_explicit_force_omx.png)

*Figure 2 (from [Paper Figure 15](https://arxiv.org/html/2607.11734v2#S5.F15)): Injecting predicted external force into dynamics (explicit coupling) increases trajectory error relative to implicit coupling, highlighting the identifiability boundary between actuator effort and external load.*

---

## 2. Counterexamples, Hidden Switches, and Evidence Boundaries

1. **Contact is explicitly disabled during training**: Pinned source `train_actuator_diffsim.py` sets `mjDSBL_CONTACT` with a 1-iteration Newton solver; payloads are omitted from scene geometry, the gripper tracks logged aperture, and trajectories avoid collisions by design. **Lower pose error under NeuralActuator never certifies better contact physics.**
2. **Telemetry-aligned rollout is not a counterfactual action model**: Evaluation feeds recorded currents, voltages, and temperatures synchronized with the real trajectory; the paper notes the model cannot predict servo effort responses to arbitrary unexecuted future commands.
3. **Force estimation is limited to 3D end-effector resultant**: No 6-D wrench, contact location, or multi-finger distribution is predicted, and training still requires independent payload or F/T supervision.
4. **Differentiable clamps ensure stability, not physical validity**: Clamping torques, joint velocities, and gripper limits prevents BPTT blow-up rather than validating physical contact or hardware safety limits.

---

## 3. What DexLab Should Borrow & First Minimal Validation Slice

In DexLab's contact and grasp diagnostics, unmodeled actuator lag can easily be misattributed to contact solvers or friction parameters. NeuralActuator's main lesson is to **isolate actuator error as its own engine-portable layer**, while its contact-disabled training draws a bright boundary: never allow a black-box actuator surrogate to silently absorb contact loads.

- **Adopt directly**:
  1. **Actuator telemetry qualification contract**: Require monotonic clocks, separate channels for `q_cmd`, `q`, `qdot`, `current/load`, `voltage`, `temperature`, independent force reference, frames/signs, and hardware identity before any actuator fitting.
  2. **Trajectory- and hardware-instance-level splits**: Never split adjacent frames randomly across train/test, which leaks thermal drift, friction history, and mount-specific bias.
  3. **Paired negative controls**: Retain free motion, no-load, nominal vs. restricted motor, and contact vs. matched no-contact trajectories together.
- **Validate after adaptation**:
  - Once qualified low-cost servo logs exist, run a single-platform, single-instance **actuator-only pilot** with the **contact solver enabled**, comparing direct surrogate, residual $K_t I + \Delta\tau$, and GMO against an independent force reference to verify the actuator layer is not absorbing contact loads, reporting pose, force, saturation, temperature, and no-contact false positives.
- **Defer or reject**:
  - Do not replace contact solving with an implicit torque surrogate;
  - Do not extrapolate 3D end-effector resultant force to multi-finger dexterous contact;
  - Do not treat telemetry-aligned rollouts as counterfactual planners;
  - Do not claim sensorless force perception without an independent measured force reference.

### First Minimal Falsifiable Slice

- **Question**: Can DexLab's hardware-log intake gate (`src/dexlab/hardware_log.py`, `docs/hardware/template/manifest.json`) programmatically reject logs that fail to separate command/actuator tracking error from an independent contact-load reference before any model is trained?
- **Controlled comparison**: Define an `actuator-calibration` profile over the existing bundle schema and test synthetic valid bundles against 5 invalid fixtures (clock drift/reversal, missing effort channels, command copied into feedback, missing force provenance, trajectory leakage). No model is trained and no physics claim is made in this slice.
- **Pass / stop criteria**: Valid bundles pass and all 5 invalid fixtures fail with specific provenance diagnostics. If real hardware logs do not yet pass this contract, fix data capture and calibration first rather than training a Transformer.

---

## 4. Verifiable Sources & Inspection Scope

- Paper: [NeuralActuator (arXiv:2607.11734v2)](https://arxiv.org/abs/2607.11734v2) (RSS 2026, full text and appendices) · [Project Page](https://people.csail.mit.edu/frankzydou/projects/NeuralActuator/index.html)
- Pinned code: [`Frank-ZY-Dou/Dynamics-Modeling@541a93a`](https://github.com/Frank-ZY-Dou/Dynamics-Modeling/tree/541a93aac4368e73883e86a51f31a7add6bde059/NeuralActuator) (static review of `models/transformer.py`, `train_actuator_diffsim.py`, implicit/explicit coupling, and MJX/SuperDex backends)
- Related tracking: [DexLab Discussion #414](https://github.com/huangkiki/Dexlab/discussions/414) · [Research intake #415](https://github.com/huangkiki/Dexlab/issues/415)
- **Inspection scope (2026-11-26)**: Based on arXiv `2607.11734v2` and static inspection of pinned commit `541a93a`. All numerical results are author-reported; no MJX, Newton, MuJoCo Warp, SuperDex, OMX, SO-101, or Franka runs or new hardware recordings were executed.
