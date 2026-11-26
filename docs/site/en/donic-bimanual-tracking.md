# Can a DONIC tracking score tell whether a handoff succeeded?

> **At a Glance**
>
> | Field | Details |
> | --- | --- |
> | **Work Covered** | *DONIC: Generalist Dexterous Bimanual Tracking Control from Human Demonstrations* (Ropedia, [arXiv:2610.29997v1](https://arxiv.org/abs/2610.29997v1), 2026-10-21) |
> | **Pinned Sources** | Official repo [`Ropedia/DONIC@62ba0e9`](https://github.com/Ropedia/DONIC/tree/62ba0e977696f976eba8fdc6ca05b325b5c67f56) (BiHOI processing pipeline only; policy and dataset pending) · [Project Page](https://ropedia.github.io/DONIC/) |
> | **Core Problem** | Existing dexterous reference trackers focus on single hands or single clips: in bimanual manipulation, contact roles shift asynchronously between hands and clip difficulty varies wildly, causing standard pose tracking and PPO updates to break down in a shared policy. |
> | **Core Approach** | Collects the high-bimanual-contact **BiHOI** dataset and trains a unified 52-DoF residual policy combining **role-gated per-hand contact rewards**, **Clip-Centered Advantages (CCA)**, and DexTrack-style **replay-verified demonstration recycling with behavior cloning**. |
> | **Open-Source Status** | BiHOI reconstruction code is public (CC BY-NC 4.0; full hand steps need external assets); **policy training/eval code, checkpoints, and the BiHOI dataset are still pending release**. |
> | **DexLab Verdict** | **`pilot` (adopt per-hand contact-role diagnostics and handoff counterexamples first; do not train a policy yet)** — test whether scoring separates tracking accuracy from contact-partner errors and brief loss of support before evaluating multi-clip training tricks. |

---

## 1. What This Work Actually Does

DONIC studies **generalist dexterous bimanual reference tracking from human demonstrations**: given a reference clip of two hands manipulating a single rigid object, it trains **one frozen closed-loop controller** in Isaac Gym to drive two 20-DoF dexterous hands (Wuji Hand V1 plus 6-DoF virtual wrists per hand, 52 DoF total) across diverse unseen references.

### Problem Setup & I/O

- **Bottleneck**: In real bimanual tasks such as handoffs, holding-while-opening, or cooperative lifting, contact roles switch dynamically (e.g., left hand supports → both hold → left releases while right moves the cup). Scaling single-hand trackers to two hands hits three obstacles: (1) a coupled contact reward lets one failing hand corrupt learning for the other; (2) pooling thousands of clips creates large reward-scale disparities where hard clips stay persistently negative under standard PPO advantages; and (3) public HOI datasets have relatively low simultaneous two-hand contact rates (15.7%–38.6%).
- **Inputs**: A 3,016-D observation vector (2,884 base features + 132 object features: 128-D BPS geometry, scale, and center of mass), containing per-hand proprioception, object pose/velocity, upcoming reference frames, tracking errors, wrist-frame fingertip-to-object distance vectors, hand identity, and a fixed left-hand weight. (All 40 contact-force observation channels are zeroed out; simulated contact force is used only in the training reward.)
- **Outputs**: A 52-D normalized residual action $\mathbf{a}_t \in [-1,1]^{52}$ (6 wrist + 20 finger DoFs per hand) added with bounded scaling around the next reference frame and sent to PD control: $\mathbf{q}_{t}^{\mathrm{pd}} = \operatorname{clamp}(\hat{\mathbf{q}}_{t+1} + \mathbf{s} \odot \mathbf{a}_{t},\, \mathbf{q}_{\min},\, \mathbf{q}_{\max})$, bounded to $0.1\ \mathrm{m}$ wrist translation, $1.0\ \mathrm{rad}$ wrist rotation, and $0.15\ \mathrm{rad}$ per finger joint.

### System Pipeline & Four Core Modules

1. **BiHOI Multi-View Capture & Retargeting Pipeline (§3, Appendix B)**: Captures 1,575 sequences across 229 objects (14.77 unique hours) with 32 calibrated RGB cameras (1920×1232, 30 fps), achieving **65.91% simultaneous bimanual contact** among frames with at least one hand in contact (vs. 32.21% in GRAB, 24.97% in OakInk2, 15.69% in TACO). Object meshes and 6D poses are reconstructed via SAM3 + Depth Anything 3 + MV-SAM3D + multi-view consensus FoundationPose; hands are fit via WiLoR + MANO and jointly refined with a 3 mm depth SDF loss (without explicit collision/penetration terms), retargeted via NLopt to dual Wuji Hand V1 hands (30 fps), and filtered by zero-residual replay to drop clips with immediate object drops or ejections.
2. **Shared Residual MLP & Four-Term Reward (§4.1–4.3, Appendix C)**: Separate Actor and Critic MLPs (1024-1024-1024-512 ReLU) train across 8,192 parallel Isaac Gym environments (524,288 transitions/iteration). Total reward combines hand pose, object motion, approach/contact, and hold terms with weights $(0.25, 0.45, 0.15, 0.15)$, where the object term $r_t^{\mathrm{obj}}$ continuously tracks position, geodesic orientation, and linear velocity.
3. **Role-Gated Per-Hand Contact Supervision (§4.3, Appendix C.2)**: Uses the reference frame to identify active hands $\mathcal{E}_t$ and expected contacting fingertips $\mathcal{C}_t^h$. Contact and hold rewards average only over currently active hands (weights $w_L=0.5$, $w_R=1$). Once the left hand is supposed to release, it leaves the contact term while hand pose and object motion terms remain active.
4. **Clip-Centered Advantages (CCA) + Replay-Verified BC Recycling (§4.4, Appendix C.3–C.4)**: Centers GAE advantages within each reference clip before the PPO actor update so hard clips still provide positive/negative action contrast; pairs PPO with a DexTrack-style demonstration buffer populated by specialist and shared-policy rollouts that pass displacement/lift replay verification, sampled in a separate 4,096-pair behavior-cloning batch ($\lambda_{\mathrm{BC}}=50$).

![Figure 2: DONIC training pipeline and core modules](https://arxiv.org/html/2610.29997v1/pipeline.png)

*Figure 1 (from [Paper Figure 2](https://arxiv.org/html/2610.29997v1#S4.F2)): Public demonstrations and BiHOI feed a shared residual tracking policy coupled with a replay-verified demonstration pool; bottom panels show object tracking, role-gated per-hand contact rewards, clip-centered advantages, and auxiliary BC.*

### Core Mechanisms & Load-Bearing Equations

**(a) Proximity-Gated Contact Proxy & Active-Hand Aggregation (§4.3, Eqs. 4–6)**

$$
\alpha_{i,t}^{h} = \mathbf{1}\!\left[f_{i,t}^{h} > f_{\min}\right]\,\mathbf{1}\!\left[\delta_{i,t}^{h} < \delta_{\max}\right],
\qquad
r_{t}^{u} = \begin{cases}
\displaystyle\frac{\sum_{h\in\mathcal{E}_{t}} w_{h} r_{t}^{u,h}}{\sum_{h\in\mathcal{E}_{t}} w_{h}}, & \mathcal{E}_{t}\neq\varnothing, \\[6pt]
0, & \mathcal{E}_{t}=\varnothing.
\end{cases}
$$

- $f_{i,t}^{h}$ and $\delta_{i,t}^{h}$: simulated net fingertip contact-force magnitude and distance to the object surface for hand $h\in\{L,R\}$, fingertip $i$, with fixed thresholds $f_{\min}=0.5\ \mathrm{N}$ and $\delta_{\max}=0.03\ \mathrm{m}$;
- $\mathcal{E}_t$: set of hands expected to contact the object at step $t$; $r_t^{u,h}$ is the per-hand contact or hold average over $\mathcal{C}_t^h$ ($u\in\{\mathrm{cont},\mathrm{hold}\}$);
- **Intuition**: Normalizing over $\mathcal{E}_t$ prevents one failing hand from erasing contact feedback for the supporting hand. The $3\ \mathrm{cm}$ proximity gate filters out far-away table or self-contact forces—yet it still reads **net fingertip force + proximity**, not verified collision pairs.

**(b) Clip-Centered Advantages (CCA, §4.4, Eq. 8)**

$$
\widetilde{A}_{j} = A_{j}^{\mathrm{GAE}} - \frac{1}{|\mathcal{G}_{m(j)}|}\sum_{k\in\mathcal{G}_{m(j)}} A_{k}^{\mathrm{GAE}}
$$

- $m(j)$: reference clip index for transition $j$; $\mathcal{G}_m$: all transitions from clip $m$ in the current rollout batch;
- **Intuition**: If a hard clip has GAE advantages $[-5, -3]$ and an easy clip has $[2, 4]$, centering maps both to $[-1, 1]$, preserving their within-clip margin of $2$ for the actor update while leaving critic targets unchanged.

### Main Experiments, Results, and Ablations

Evaluated in Isaac Gym on single-rigid-object tracking with **one frozen policy** (deterministic mean action from frame 0): 1,845 public training clips (GRAB, GigaHands, OakInk2, H2O, TACO), tested on 53 unseen trajectories of seen objects and 164 trajectories of unseen objects. Success requires clip-mean object/wrist translation error $\le 10\ \mathrm{cm}$, rotation error $\le 60^\circ$, and 20-joint finger MAE $\le 40^\circ$ for **both hands**.

| Configuration (Author-Reported, [Table 2](https://arxiv.org/html/2610.29997v1#S5.T2)) | Unseen Traj SR (/53) | Unseen Traj Comp (%) | Unseen Obj $T_o$ (cm) | Unseen Obj SR (/164) | Unseen Obj Comp (%) | What This Proves / Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| **DexTrack-bi** (adapted baseline) | 0/53 (0.00%) | 1.30 | 127.87 | 0/164 (0.00%) | 0.88 | Project page notes separate reference conversion & scene setup; cannot isolate one reward term |
| **Dexplore-bi** (adapted baseline) | 5/53 (9.43%) | 27.87 | 17.92 | 19/164 (11.59%) | 26.37 | Strong adapted baseline; direct single-hand scaling struggles on bimanual clips |
| **DONIC w/o CCA** | 43/53 (81.13%) | 62.72 | 16.83 | 79/164 (48.17%) | 43.89 | Unseen-object SR drops 9.15 pp, showing clip centering is a load-bearing gain |
| **DONIC w/o contact gate** | 43/53 (81.13%) | 65.03 | 17.61 | 80/164 (48.78%) | 49.52 | Removes only the 3 cm proximity gate (net force >0.5 N, object reward & per-hand avg kept) |
| **DONIC (1,845 public clips)** | **46/53 (86.79%)** | **67.62** | **15.74** | **94/164 (57.32%)** | **54.69** | Cleanest controlled comparison: one frozen policy outperforms adapted baselines on unseen objects |
| **DONIC + BiHOI (3,420 clips)** | **47/53 (88.68%)** | **68.72** | **13.96** | **98/164 (59.76%)** | **55.35** | Changes both dataset size (+85%) and distribution; cannot isolate bimanual-contact ratio alone |

*(Counts reconstructed from published percentages and denominators 53 / 164. Appendix Table S3 lists a single seed `42`, with no cross-seed intervals and no standalone BC ablation.)*

![Figure 3: Qualitative comparison on two held-out object references](https://arxiv.org/html/2610.29997v1/figures/policy_comparison.jpg)

*Figure 2 (from [Paper Figure 3](https://arxiv.org/html/2610.29997v1#S5.F3)): Time-aligned tracking snapshots comparing DexTrack-bi, Dexplore-bi, and DONIC on two unseen-object clips. Visual panels reveal gross drift but do not verify contact forces or load support.*

---

## 2. Counterexamples, Hidden Assumptions, and Evidence Boundaries

1. **SR and Comp do not certify uninterrupted handoff support**: SR checks **clip-averaged** errors and Comp checks per-frame thresholds while crediting recovered frames. If the left hand releases early, the cup drops briefly, and the right hand catches it, clip-mean tracking can still pass even though the physical handoff failed.
2. **The `f > 0.5 N & δ < 3 cm` contact proxy can misattribute contact partners**: Because $f$ is total fingertip net force rather than a finger–object collision pair force, a fingertip pressing the table within $3\ \mathrm{cm}$ of a cup satisfies $\alpha=1$. In addition, frames where the reference expects no contact do not separately penalize unintended contact.
3. **Dataset-addition confounding and unreleased core assets**: Adding BiHOI improves unseen-object SR by 4 clips (94→98/164) while nearly doubling dataset size (1,845→3,420), confounding scale with contact distribution. At pinned commit `62ba0e9`, only the BiHOI processing pipeline is public (listing 31 named camera inputs vs. 32 in the paper, with default export capped at 500 frames) under CC BY-NC 4.0; policy code, checkpoints, and BiHOI data remain pending.
4. **Scoped to reference-conditioned single-rigid-body simulation**: All quantitative claims assume a full future reference in Isaac Gym; autonomous goal selection, multi-object/deformable interaction, and real-hardware transfer remain unverified.

---

## 3. What DexLab Should Borrow & First Minimal Validation Slice

For DexLab, DONIC's highest-leverage contribution is not an RL training stack—it is a concrete scoring test plugged directly into [DexLab's scoring semantics audit (Discussion #302)](https://github.com/huangkiki/Dexlab/discussions/302): **when a clip already passes pose-tracking thresholds, what native evidence proves the right hand actually supported the object during handoff?**

- **Adopt directly**:
  1. **Three-track aligned timeline**: Report reference tracking error, per-hand verified collision pairs with force direction/impulse, and phase task outcome on one shared timeline, marking missing channels as `indeterminate` rather than silent pass.
  2. **Separate contact partner from load support**: Use collision pairs to verify *which* body was touched (cup vs. table), and check force direction, impulse, and subsequent object motion to verify load transfer.
- **Validate after adaptation**:
  - Only after independent scoring cleanly separates handoff success from counterexamples, evaluate **Clip-Centered Advantages (CCA)** and **replay-verified demonstration recycling** for multi-clip training (checking batch coverage, since a singleton clip centers to zero advantage).
- **Defer or reject**:
  - Do not try to reproduce the full DONIC training stack while policy code, checkpoints, and BiHOI data are unreleased;
  - Do not ingest CC BY-NC 4.0 BiHOI pipeline code or restricted third-party hand assets into DexLab;
  - Do not equate reference-tracking SR or Comp with autonomous task success or physical handoff certification.

### First Minimal Falsifiable Slice

- **Question**: On a fixed support → transfer → release reference, can an offline scorer catch both "near-object table contact" and "brief handoff support drop" even when overall tracking scores pass?
- **Controlled comparison**: First audit observation coverage in existing Wuji records (`demos/wuji-contact/score.py`, `docs/evidence/wuji-contact/results.json`), then verify the scoring rules on one qualified control plus two explicitly labeled synthetic counterexamples:
  1. **Counterexample A (wrong contact partner)**: Right fingertip stays within $3\ \mathrm{cm}$ with $>0.5\ \mathrm{N}$ net force, but contact is strictly against the table.
  2. **Counterexample B (handoff drop window)**: Left hand releases early before right-hand support builds, causing transient object drop followed by recovery while clip-mean tracking stays within bounds.
- **Pass / stop criteria**: Control passes all three tracks; Counterexample A isolates first failure to contact-partner attribution; Counterexample B isolates first failure to handoff support; missing fields remain indeterminate and legacy Wuji scores stay untouched. Stop before any policy training if offline counterexamples cannot be cleanly separated.

---

## 4. Verifiable Sources & Inspection Scope

- Paper: [DONIC (arXiv:2610.29997v1)](https://arxiv.org/abs/2610.29997v1) (full text and Appendices A–D) · [Project Page](https://ropedia.github.io/DONIC/) · [Hugging Face Paper Entry](https://huggingface.co/papers/2610.29997)
- Pinned repo: [`Ropedia/DONIC@62ba0e9` Release Checklist](https://github.com/Ropedia/DONIC/blob/62ba0e977696f976eba8fdc6ca05b325b5c67f56/README.md) · [BiHOI Stage Manifest](https://github.com/Ropedia/DONIC/blob/62ba0e977696f976eba8fdc6ca05b325b5c67f56/bihoi_pipeline/provenance/stages.json) · [Policy Directory README](https://github.com/Ropedia/DONIC/blob/62ba0e977696f976eba8fdc6ca05b325b5c67f56/donic/README.md)
- Related discussions: [DexLab Discussion #423](https://github.com/huangkiki/Dexlab/discussions/423) · [Scoring Semantics Discussion #302](https://github.com/huangkiki/Dexlab/discussions/302) · [Back to the dexterous simulation guide](dexterous-hand-simulation.md)
- **Inspection scope (2026-11-26)**: Synthesized from arXiv `2610.29997v1`, project-page comparison notes, and static inspection of pinned commit `62ba0e9`. All metrics are author-reported; policy code, checkpoints, and BiHOI data remain unreleased, and no Isaac Gym training, retargeting pipeline, or new DexLab physics experiments were run.
