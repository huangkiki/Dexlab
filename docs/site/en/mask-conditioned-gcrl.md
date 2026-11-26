# Visual goal masks in DexLab: prove the progress signal before training GCRL

> **At a Glance**
>
> | Field | Details |
> | --- | --- |
> | **Work Covered** | *Dynamic Object Masks as Goal Representations for Visual Goal-Conditioned Reinforcement Learning* (University of Alberta, Amii, McGill, Vector Institute, et al., RLC 2026, [arXiv:2510.06277v2](https://arxiv.org/abs/2510.06277v2), 2026-08) |
> | **Pinned Sources** | [`fahimfss/GCRL@771cf55`](https://github.com/fahimfss/GCRL/tree/771cf5567ef656f941f0ace0e2881d38988fd94b) (MIT License) |
> | **Core Problem** | Visual goal-conditioned RL (GCRL) usually relies on privileged 3D coordinates, one-hot IDs, CLIP text, or pre-captured goal images—requiring pose estimation or lacking spatial grounding—while plain 3D distance rewards pull the end-effector near the object without aligning the gripper fingers. |
> | **Core Approach** | Appends a **per-step dynamic binary target mask** channel to RGB (stacked over 3 frames) as the policy's goal input, and converts the **mask pixel fraction (full-image or gripper ROI)** through a sigmoid into a dense approach reward. |
> | **Open-Source Status** | Training and real-robot scripts are open-source (MIT); **no pretrained policy checkpoints are released**, and simulation requires external RoboHive object assets. |
> | **DexLab Verdict** | **`pilot` (adopt visual progress monotonicity and detector-error audits first; do not add a visual GCRL training stack)** — DexLab's completed offline LIBERO audit ([PR #411](https://github.com/huangkiki/Dexlab/pull/411)) already confirmed false boxes and occlusion can spoof ROI progress. |

---

## 1. What This Work Actually Does

When a visual robot has no reliable 3D object pose estimator, its policy still needs to know both *which object in the image is the target* and *how close it is to being graspable*. Dynamic Object Masks unifies both by **recomputing a binary target mask every step and feeding it into both the observation and the dense approach reward**.

### Problem Setup & I/O

- **Bottleneck**: In tabletop reaching/grasping (UR10e, Franka) or mobile search (Create3), one-hot or CLIP text embeddings omit spatial location, while a pure 3D center-to-center distance reward allows a gripper to hover beside an apple without placing it between the fingers.
- **Inputs**:
  - **Visual observation**: Concatenates RGB with the current binary target mask $m_t$ into a 4-channel frame $I_t' = [I_t^{\mathrm{cam}}, m_t]_C$, then stacks the 3 most recent frames into a `90 × 160 × 12` tensor $I_t = [I_t', I_{t-1}', I_{t-2}']_C$ so the policy observes target location, scale, and motion direction;
  - **Proprioception**: Joint positions and previous action (plus binary two-finger contact flags for pick-up).
- **Outputs**: A 4-layer CNN + LayerNorm + tanh encoder feeds actor/critic networks outputting low-level joint velocities (arms) or base velocities (Create3). From-scratch sim and real learning use **5-Q ensemble SAC** (with random shift and weight clipping); UR10e zero-shot sim-to-real uses **PPO**.

### System Pipeline & Three Core Modules

1. **Dynamic Target-Mask Generator (`env_v1.py`, `franka_dense_env.py`)**: In simulation, masks are **not** learned segmentations—they are rectangles projected from privileged object centers using hand-coded per-object width/height scales and offsets. On real robots, the same channel is filled by color thresholding, Detic (fixed vocabulary, confidence `0.5`), or Grounding DINO (open-vocabulary text prompt).
2. **Mask-Size Reward & Gripper ROI Stage Switch (`env_v2.py`)**: Reaching rewards the full-image mask fraction. Pick-up restricts the sum to a **fixed ROI between the gripper fingers**, so approach reward only grows as the target enters the graspable zone; once both fingers make contact, the mask is cleared and reward switches to contact, lifting, and completion.
3. **Real-World Visual Domain Adaptation (UR10e sim-to-real)**: PPO training applies joint/pose/color/blur randomization and linearly mixes **80% simulated images with 20% random real backgrounds**; deployment runs Grounding DINO (~120 ms/step) over a 500 Hz `servoJ` controller.

![Figure 4: Gripper ROI mask guiding tabletop pick-up](https://arxiv.org/html/2510.06277v2/plots_and_images/pick.jpg)

*Figure 1 (from [Paper Figure 4](https://arxiv.org/html/2510.06277v2#S4.F4)): During pick-up, mask area is counted only inside the inter-finger ROI (green box shown for illustration only, not fed to the policy); once both fingers touch the apple, the mask clears and contact/lift rewards take over.*

### Core Mechanism & Load-Bearing Equations

Both visual goal progress and multi-stage grasping hinge on these reward definitions (§3–4, Eqs. 3–5):

$$
R' = \frac{1}{H \times W}\sum_{i=1}^{H}\sum_{j=1}^{W}\mathbf{1}\!\left\{m_t^{ij} > 0\right\},
\qquad
R^{\mathrm{mask}} = \frac{2}{1 + e^{-10 R'}} - 1 \in [0, 1]
$$

For UR10e pick-up, the ROI mask reward is embedded inside a composite staged reward:

$$
R^{\mathrm{pick}} = -1.1 + R^{\mathrm{reach}} + R^{\mathrm{contact}} + R^{\mathrm{lift}} + R^{\mathrm{goal}}
$$

- $H, W$: height and width of the full frame or gripper ROI; $R'$ is the fraction of active mask pixels;
- Constant $10$: sigmoid slope amplifying small area increases when the target is still distant;
- $R^{\mathrm{contact}}$ (`+10` first two-finger contact, `+0.1`/step sustained), $R^{\mathrm{lift}} = 1 - 3.3 D$ (height progress after contact), and $R^{\mathrm{goal}}$ (`+10` completion);
- **Intuition**: Under an egocentric wrist camera, moving closer grows the object's projected area, and restricting $R'$ to the gripper ROI couples approach to finger alignment—provided camera geometry is egocentric and the detector does not hallucinate boxes.

### Main Experiments, Results, and Built-in Counterexamples

| Experiment / Task | Setup & Budget | Key Metrics (Author-Reported) | What This Proves / Counterexample |
| --- | --- | --- | --- |
| **Sim Visual Reaching** (Franka / UR10e-MuJoCo) | 20 RoboHive objects (15 train / 5 held-out), SAC 300k steps, 11 seeds × 25 trials/obj | Mask train/held-out accuracy **`99.9%`** vs. 3D position `98.9% / 98.8%`; faster convergence than one-hot/CLIP/goal-image | Confirms dynamic mask is a strong visual interface; a `1.0 pp` margin alone does not prove superiority over privileged coordinates |
| **Sim Tabletop Pick-up** (UR10e-MuJoCo) | From-scratch SAC 1M steps, 11 seeds × 6 object classes × 50 trials | Mask GC+reward: **9/11 seeds** > `90%` success vs. **2/11 seeds** for 3D position+distance | Strongest mechanistic result: ROI mask fixes 3D distance's lack of finger-alignment guidance (still paired with contact/lift rewards) |
| **Mobile Visual Navigation** (Create3-Isaac Sim) | Square arena with colored wall stickers, color-threshold masks | Mask learns faster, **counterexample: final median falls below privileged 3D position** | When targets leave the field of view, mask policies must search first and lose spatial advantage |
| **UR10e Zero-Shot Sim-to-Real** (Table 1) | Best of 10 PPO seeds, Grounding DINO, 25 trials/set, 15 cm threshold | In-dist **`96%`** (0.076 m); OOD-1 **`92%`** (0.13 m); OOD-2 **`92%`** (0.092 m) | Shows interface transferability, but selects best-of-10 seeds with pre-measured target poses |
| **Franka Real From-Scratch** (Figure 3c) | Wrist camera 100k steps (100 steps/ep), RTX 3090, Detic (157 ms) vs. Grounding DINO (168 ms) | Detic learns reaching in ~60k steps; **counterexample: Grounding DINO fails because RL exploits false-positive boxes** | Exposes the true first failure layer: `false box → inflated mask area → fake reward → policy exploits detector errors` |

![Figure 3c: Real-world Franka from-scratch learning with Detic vs Grounding DINO](https://arxiv.org/html/2510.06277v2/plots_and_images/rw_scratch_franka.png)

*Figure 2 (from [Paper Figure 3](https://arxiv.org/html/2510.06277v2#S4.F3)): Real Franka learning curves. Detic succeeds, whereas Grounding DINO false positives corrupt the mask-size reward and derail training.*

---

## 2. Counterexamples, Hidden Switches, and Evidence Boundaries

1. **"Object-agnostic" is narrower in code than in the title**: Static review of `env_v1.py` confirms simulation masks are projected rectangles parameterized by **hand-coded per-object scale and offset constants** across 20 known objects (15 train / 5 held-out). The authors note this yields object-agnostic *reaching*, not part-level manipulation (e.g., mug handles or scissors).
2. **No 3D coordinates in the actor ≠ no privileged localization in the experiment**: Real-robot code (`franka_dense_env.py`) keeps `target_pos` out of the actor, yet still uses pre-recorded `target_pos` to terminate episodes at `< 0.13 m`. Policy inputs and termination/acceptance ground truth must be audited separately.
3. **Monotonicity breaks under fixed cameras, occlusion, and detector noise**: The paper includes no controlled ablation over missed detections, flicker, partial occlusion, or area jitter. In the Grounding DINO failure, the first failure layer is visual signal generation and reward semantics, not SAC or physics.
4. **Grasping still depends on physical contact stages**: Because the mask clears immediately on two-finger contact, hold stability and lifting remain governed by contact mechanics, geometry, and staged contact rewards.

---

## 3. What DexLab Should Borrow & Next Validation Slice

In DexLab, feeding an unverified visual signal into rewards or stage predicates turns detector bugs into apparent physics or policy failures. **DexLab already executed the first offline audit inspired by this paper on 2026-11-18 using recorded fixed-camera LIBERO `demo_0` frames ([PR #411](https://github.com/huangkiki/Dexlab/pull/411) / [LIBERO audit section](libero-workflow-report.md#mask-progress-signal-audit))** across 28 stage checkpoints and 4 controlled perturbations:

- Baseline target-mask ROI overlap rose across stages (pre-contact median `0` → contact-to-lift `0.535` → lift-to-success `0.877`, pre/post-contact AUC `0.861`), yet both post-success frames lost the target mask—proving mask loss cannot double as task failure or completion;
- **7 missed detections** dropped AUC to `0.738`; **3-frame delay** shifted contact stage alignment; **a spurious ROI box** pushed pre-contact overlap to `0.780` (showing high scores can reflect fake progress); and **occlusion** shrank the overlap denominator, paradoxically raising overlap in some cases.

DexLab's concrete stance:

- **Adopt directly**:
  1. **Visual progress monotonicity & perturbation contract**: Before any visual mask enters a reward or policy, log mask presence, area, center error, ROI overlap, true distance, and native contact events together under occlusion, missed detection, false box, and delay tests.
  2. **Separate privilege boundaries**: Explicitly distinguish actor inputs, reward signals, termination criteria, and final acceptance ground truth.
  3. **Isolate detector failure as its own root-cause layer**: Never collapse `detector failure → bad reward → policy failure` into "training instability."
- **Validate after adaptation**:
  - Only after an egocentric wrist-camera + real-detector audit passes monotonicity and false-box guards should DexLab compare mask conditioning against goal images or privileged coordinates.
- **Defer or reject**:
  - Do not treat mask-size reward as contact or grasp success;
  - Do not add a general detector/segmentation stack or visual GCRL framework from a single pick-up benchmark;
  - Do not extrapolate `99.9%` reaching to arbitrary unseen geometries or fixed third-person cameras.

### Next Minimal Falsifiable Slice

- **Question**: Building on the completed fixed-camera LIBERO audit (PR #411), when the same 4-perturbation test is applied to **egocentric wrist-camera streams with live open-vocabulary detector outputs**, can temporal consistency and confidence gating separate true stage progress from false boxes and occlusion?
- **Controlled comparison**: Freeze recorded trajectories with native contact readbacks (no policy training, no physics changes) and compare raw ROI overlap vs. gated ROI signals on stage-ranking AUC and pre-contact false-progress rate under the 4 perturbations.
- **Pass / stop criteria**: Stop before any visual GCRL training if false boxes or occlusion still rank uncontacted/failed stages ahead of valid contact and lift stages.

---

## 4. Verifiable Sources & Inspection Scope

- Paper: [Dynamic Object Masks as Goal Representations for Visual GCRL (arXiv:2510.06277v2)](https://arxiv.org/abs/2510.06277v2) (full review of 5 figures, 1 table, and 5 equations)
- Pinned code: [`fahimfss/GCRL@771cf55`](https://github.com/fahimfss/GCRL/tree/771cf5567ef656f941f0ace0e2881d38988fd94b) (static inspection of `env_v1.py`, `env_v2.py`, `rl_chemist/env.py`, `franka_dense_env.py`, `detic.py`)
- DexLab tracking: [Discussion #405](https://github.com/huangkiki/Dexlab/discussions/405) · [Research intake #406](https://github.com/huangkiki/Dexlab/issues/406) · [LIBERO offline audit PR #411](https://github.com/huangkiki/Dexlab/pull/411) · [Model evaluation boundaries](model-evaluation.md)
- **Inspection scope (2026-11-26)**: Paper and pinned repo reviewed statically; all paper success rates, hardware runtimes, and transfer numbers are author-reported (no RoboHive, MuJoCo, Isaac Sim, SAC/PPO, Detic, or Grounding DINO runs executed here). DexLab audit metrics are read back from merged [PR #411](https://github.com/huangkiki/Dexlab/pull/411).
