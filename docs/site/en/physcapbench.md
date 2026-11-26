# Physical captions in DexLab: measure reference coverage before claiming video truth

> **At a Glance**
>
> | Field | Details |
> | --- | --- |
> | **Work Covered** | *PhysCapBench: A Cross-Domain Benchmark for Physically Grounded Video Captioning* (BAAI, PKU, Beihang, Tsinghua, Physis, [arXiv:2611.16424v2](https://arxiv.org/abs/2611.16424v2), 2026-11-16; distinct from Physis-Lang's homonymous benchmark—always cite the arXiv ID) |
> | **Pinned Sources** | Evaluator [`hfwang2001/PhysCapBench@0858c69`](https://github.com/hfwang2001/PhysCapBench/tree/0858c694f6aa2fae247c5fc907fb60488f27c4b7) (MIT) · Dataset [`HF@4b18722`](https://huggingface.co/datasets/hfwang01/PhysCapBench/tree/4b1872201558c6fb5e231f5be2b843ed16b2e105) · [Project Page](https://hfwang2001.github.io/physcapbench-site/) |
> | **Core Problem** | Standard video captioning metrics reward broad scene summaries while missing physical process details (actors/tools, contact onset/maintenance/release, state transitions, causal mechanisms, temporal order), making it hard to diagnose what world models or policy captions omit. |
> | **Core Approach** | Builds a 1,500-video, 3-domain structured physical reference dataset, **freezes per-dimension evidence applicability before seeing any candidate**, and uses a fixed text judge to score candidate-to-reference coverage across 7 physical dimensions. |
> | **Open-Source Status** | Evaluation code (MIT) and 1,500 structured annotations/videos are public (video licenses split by upstream source; EgoDex is CC BY-NC-ND); **downstream video-reconstruction and policy-training code/checkpoints are not released**. |
> | **DexLab Verdict** | **`pilot` (adopt structured event-chain references and candidate-blind applicability freezing; downgrade any "video truth certification" claim)** — the current judge checks text-to-reference coverage without penalizing unmentioned fabrications, so it cannot serve as a reward or physics oracle. |

---

## 1. What This Work Actually Does

PhysCapBench targets captions that sound plausible while omitting the mechanics that actually happened—e.g., describing a bimanual page turn simply as "a person turns a page" without stating which hand holds the page down, which applies torque, how long contact persists, or how the page state changes. The paper formalizes these records as **traceable structured physical references** and tests whether richer physical captions improve video reconstruction and policy fine-tuning.

### Problem Setup & I/O

- **Inputs**: A single-view or synchronized multi-view video $v$ and a free-text candidate caption $c$.
- **Core evaluation boundary**: The evaluator does **not** compare $c$ directly against video $v$; it compares $c$ against a human-verified structured Gold reference $r$ to score 7-dimension semantic agreement and coverage (**caption-to-reference**, not caption-to-video fact verification).
- **Balanced 3-domain dataset (1,500 videos, 9.16 hours)**:
  - **Third-person physical scenes (500 videos, 2.125 h)**: Single-view RGB spanning 8 physical categories (fluid 32.2%, gravity/support 16.0%, granular 13.0%, rotation/friction 12.0%, etc.) and 16 scene categories;
  - **Egocentric human manipulation (500 videos, 2.212 h)**: Sourced from Apple EgoDex (RGB + hand-pose cues) across 118 tasks and 15 scenario groups;
  - **Multi-view handheld grippers (500 episodes, 4.821 h)**: Sourced from Tencent `Hy-Embodied-0.5-VLA-Data` with synchronized left-wrist, overhead, and right-wrist views (30 fps, 424×240 each) plus gripper trajectory cues.

### System Pipeline & Four Core Modules

1. **Evidence-Grounded Structured Physical Record (Tables 7–9)**: Each sample stores entity IDs, initial/final states, event frame/time spans, actors/instruments/targets, motion direction and reference objects, contact relations, state deltas, mechanism statements, temporal links, **evidence frames/witness IDs**, revision logs, and SHA-256 dataset hashes.
2. **Seven Physical Evaluation Dimensions (Table 1)**: Decomposes caption quality into **Event Coverage, Objects & Roles, Actions & Motion, Contact & Interaction, States & Outcomes, Physical Mechanisms & Causality, and Temporal Order** (0–100 scale, 5-tier rubric), exposing cases where events are right but causality or release is missing.
3. **Domain-Adaptive Annotation Cues (§3, Figure 3)**: Third-person relies on RGB scene tracking; egocentric combines EgoDex hand-speed peak frames with HOI-DETR interaction cues; handheld gripper pairs overhead views for global events with wrist views and trajectory pose/aperture shifts for contact boundaries. VLM drafts undergo cross-checking by 7 annotators and schema validation.
4. **Candidate-Blind Applicability Freezing + Two-Stage Judge**: Stage 1 freezes whether Gold provides sufficient evidence for each dimension **without seeing any candidate output**; Stage 2 runs Doubao Seed 2.1 Pro (`temperature=0`, thinking disabled) over candidate, Gold, and frozen evidence to score all 7 dimensions.

![Figure 1: PhysCapBench three-domain data, 7-dimension evaluation, and downstream tasks](https://arxiv.org/html/2611.16424v2/physcapbench_overview_20261109.png)

*Figure 1 (from [Paper Figure 1](https://arxiv.org/html/2611.16424v2#S1.F1)): Overview linking the three-domain structured physical dataset, candidate-blind 7-dimension reference evaluation, and downstream reconstruction and policy studies.*

### Core Mechanism & Load-Bearing Equations

Score aggregation and egocentric motion-guided keyframe selection are governed by (§3–4, Eqs. 1–5):

$$
S(c, r) = \frac{1}{|D(r)|} \sum_{d \in D(r)} s_d(c, r)
$$

$$
v_t = f \left\lVert p_t - p_{t-1} \right\rVert_2, \qquad
\omega_t = f \arccos\!\left(\operatorname{clip}\!\left(\frac{\operatorname{tr}(R_{t-1}^{\top} R_t) - 1}{2},\, -1,\, 1\right)\right), \qquad
m_t = v_t + 0.05\,\omega_t, \qquad
F = \operatorname{UniqueSort}(U \cup P)
$$

- $D(r)$: subset of dimensions frozen as evaluable from reference $r$ before candidates appear; $s_d(c,r) \in [0, 100]$ is the per-dimension agreement/coverage score;
- $p_t, R_t$: camera-frame hand-center position and palm rotation at frame rate $f$; $m_t$ blends translational and angular hand speed;
- $F$: deduplicated union of up to 12 uniform frames $U$ and up to 8 peak-speed frames $P$;
- **Intuition**: Freezing $D(r)$ upfront stops evaluators from dropping hard dimensions after seeing weak model results. However, unweighted averaging over $D(r)$ measures only **how much of Gold is covered**, neither weighting critical dimensions nor penalizing fabricated details outside Gold.

### Main Experiments, Results, and Built-in Counterexamples

| Experiment / Task | Setup & Budget | Key Metrics (Author-Reported) | What This Proves / Boundary |
| --- | --- | --- | --- |
| **3rd-Person & Ego Captioning** ([Table 4](https://arxiv.org/html/2611.16424v2#S4.T4)) | 11 strategies (3rd-person); 7 strategies on Qwen3-VL-8B-Instruct (ego) | Ego overall: Physis **`79.36`** > Cosmos Ego `75.41` > Meta `42.41`; **mechanism/causality lags sharply: Physis `49.58`, Meta `7.08`** | Dimension breakdown exposes how generic captions miss contact (`38.57`) and mechanisms (`7.08`) |
| **Video Reconstruction** ([Figure 6](https://arxiv.org/html/2611.16424v2#S5.F6)) | MiniMax H3 33B & LingBot-World 2.0 14B, fixed first frame & duration, metadata vs. physical caption | 3rd-person LPIPS relative drop **`8.6–9.5%`** (PVCS `8.9–9.0%`); ego LPIPS drop **`26.9–30.9%`** (PVCS `27.9–28.1%`) | Consistent direction across two generators and metrics; **measures visual match, not physical dynamics validity** |
| **Single-Task Policy Enrichment** ([Table 5a–b](https://arxiv.org/html/2611.16424v2#S5.T5)) | 50 demos, 5k LoRA steps, **single seed `0`**, 40 shared held-out scenes × 1 rollout | Overall success `37.5% → 45.0%` (standard `50%→55%`, randomized `25%→35%`); PhysCapBench `27.3/34.7 → 69.4/73.3` | Only **+3 successful trials** (15→18/40), single seed, no dimension ablation—preliminary signal only |
| **Multi-Policy Benchmark Enrichment** ([Tables 5c–d, 6](https://arxiv.org/html/2611.16424v2#S5.T6)) | $\pi_{0.5}$, X-VLA, GalaxeaVLA, starVLA across 6 tasks each in RoboTwin 2.0 & RoboDojo Sim | RoboTwin mean `+0.5–1.5 pp` ($\pi_{0.5}$ `50.4→51.9%`); RoboDojo mean `+0.6–2.0 pp` ($\pi_{0.5}$ `30.6→32.6%`) | Consistent modest upward direction across 4 families, but training scripts are unreleased and length vs. physics content is unablated |

![Figure 6: Video reconstruction LPIPS and PVCS gains from physical captions](https://arxiv.org/html/2611.16424v2/figures/reconstruction_comparison.png)

*Figure 2 (from [Paper Figure 6](https://arxiv.org/html/2611.16424v2#S5.F6)): Across both MiniMax H3 33B and LingBot-World 2.0 14B, replacing metadata with structured physical captions lowers LPIPS and PVCS in third-person and egocentric domains.*

---

## 2. Counterexamples, Hidden Switches, and Evidence Boundaries

1. **Reference coverage ≠ video truth, and non-conflicting hallucinations go unpenalized**: The text judge never watches the video, and its prompt explicitly instructs neither to reward nor penalize extra candidate claims absent from Gold unless they contradict Gold. Fabricated contacts or reversed causality not negated in Gold can slip through.
2. **Single uncalibrated LLM judge and missing annotator agreement**: All scores rely solely on Doubao Seed 2.1 Pro, with no reported inter-annotator agreement (IAA), human-judge correlation, or cross-judge variance.
3. **Three verified version mismatches across paper, release, and leaderboard**:
   - The paper averages over applicable dimensions $D(r)$, whereas the released package (`4b18722`) outputs numeric scores for all 7 dimensions and attaches an unweighted `confidence` field to 48 `null`-evidence cells across 46 samples (45 mechanism, 3 temporal);
   - The paper ranks internal Physis first in third-person (`74.07`), whereas the public repo snapshot omits Physis and ranks LingBot Temporal first (`72.91`);
   - The pinned repo (`0858c69`) passes all 12 contract tests and 1,500-item SHA-256 validation, yet **contains no downstream reconstruction or policy training scripts**, and upstream video licenses split (EgoDex is CC BY-NC-ND).

---

## 3. What DexLab Should Borrow & First Minimal Validation Slice

DexLab needs auditable failure attribution and contact evaluation, not another caption leaderboard. PhysCapBench's strongest engineering lesson is its **hash-bound, candidate-blind reference contract** (1,500 validated IDs/hashes; all 60 `supplements.jsonl` revisions logged as `candidate_seen=false`).

- **Adopt directly**:
  1. **Event-chain failure records**: Structure DexLab failure explanations as `actor/tool/target → motion → contact onset/maintenance/release → state before/after → visible mechanism → temporal order`, bound to frame/time windows and code revisions.
  2. **Candidate-blind applicability freezing**: Freeze which predicates native measurements can actually support *before* running any candidate method; keep insufficient dimensions as `insufficient` instead of dropping hard metrics post hoc.
  3. **Separate omissions from fabrications**: Track false contacts, wrong causal arrows, and hallucinated state transitions separately from reference coverage.
- **Validate after adaptation**:
  - For DexLab simulation episodes, ground structured references directly in native contact forces, contact-switch timestamps, solver events, and object pose/velocity traces while preserving `command ≠ measurement` and `render ≠ physical control`.
- **Defer or reject**:
  - Do not treat the equal-weighted 7-dimension mean as a general physical-realism or sim-to-real score;
  - Do not wire a single uncalibrated LLM judge into RL rewards or task-success verdicts;
  - Do not cite "PhysCapBench" without its full title or arXiv ID due to the homonymous Physis-Lang benchmark.

### First Minimal Falsifiable Slice

- **Question**: On existing DexLab episodes, do structured physical event-chain descriptions improve blind first-failure-layer localization compared with short task prompts and generic video captions, without increasing false assertions?
- **Controlled comparison**: Sample 20–30 existing DexLab episodes (stable grasp, slip/contact switching, state recovery), generate all three description types (90–120 candidates), and have ≥2 blind human raters plus 2 independent judges score both 7-dimension coverage and 3 fabrication counts (false contact, wrong causality, wrong state transition).
- **Pass / stop criteria**: Advance to broader data auditing or instruction enrichment only if structured descriptions **simultaneously** improve first-failure localization, keep false assertions flat or lower, and show acceptable human–judge agreement.

---

## 4. Verifiable Sources & Inspection Scope

- Paper: [PhysCapBench (arXiv:2611.16424v2)](https://arxiv.org/abs/2611.16424v2) (full review of 12 figures, 17 tables, and 5 equations) · [Project Page](https://hfwang2001.github.io/physcapbench-site/)
- Pinned code & data: [GitHub `0858c69`](https://github.com/hfwang2001/PhysCapBench/tree/0858c694f6aa2fae247c5fc907fb60488f27c4b7) · [Hugging Face `4b18722`](https://huggingface.co/datasets/hfwang01/PhysCapBench/tree/4b1872201558c6fb5e231f5be2b843ed16b2e105)
- Related discussion & context: [DexLab Discussion #378](https://github.com/huangkiki/Dexlab/discussions/378) · [Model evaluation boundaries](model-evaluation.md)
- **Inspection scope (2026-11-26)**: Synthesized from arXiv `2611.16424v2`, executed 12 repo contract tests, `bench.py validate` across all 1,500 manifests/references/hashes, and SHA-256 + frame spot-checks on 4 downloaded videos across all 3 domains. No judge API calls, caption runs, reconstruction runs, or policy fine-tuning were executed; downstream numbers are author-reported.
