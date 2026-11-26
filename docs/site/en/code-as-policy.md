# Code as Policy: from model-written programs to verified robot skills

> **At a Glance**
>
> | Field | Details |
> | --- | --- |
> | **Works Covered** | 1. [Code as Policies (arXiv:2209.07753)](https://arxiv.org/abs/2209.07753) (origin)<br>2. [CaP-X (arXiv:2603.22435v2)](https://arxiv.org/abs/2603.22435v2) · [COAP (arXiv:2610.12369v1)](https://arxiv.org/abs/2610.12369v1) · [ASPIRE (arXiv:2607.00272v2)](https://arxiv.org/abs/2607.00272v2)<br>3. [GR00T 2 Whitepaper (2026-11)](https://research.nvidia.com/labs/gear/gr00t-2) + local-contact counterexample [SuperMimic-manipulation](https://github.com/emoPointer/supermimic_manipulation) |
> | **Pinned Sources** | [`capgym/cap-x@53e9966d`](https://github.com/capgym/cap-x/tree/53e9966d7a8e2fa7494676772bccc35280f5c0ed) (MIT) · [`NVlabs/ASPIRE@fa00f0ef`](https://github.com/NVlabs/ASPIRE/tree/fa00f0ef2bc1d91d594b9aa502c22133c9f538f7) (Apache-2.0) · `Isaac-GR00T` non-default branch `codex/n2-action-expert@7e492ad1` (eval license) · [`supermimic_manipulation@eda7da48`](https://github.com/emoPointer/supermimic_manipulation/tree/eda7da480c6d92a68cc41c9628b7efdae08cae23) · COAP: no public repo found |
> | **Core Problem** | End-to-end VLAs obscure task-level logic, recovery, and root-cause attribution; yet when policies are written as code, model capability, API scaffolding, execution feedback, skill admission, and low-level contact control are routinely confounded. |
> | **Core Approach** | Represents task semantics, state, feedback, and recovery as inspectable programs or skill cards: CaP-X isolates abstraction and feedback axes; COAP freezes deterministic stateful code online while editing offline; ASPIRE pairs per-primitive traces with fresh-verifier skill promotion; GR00T 2 splits System-2 Agent, CaP recovery, and 2B WAM contact control under a single control worker. |
> | **Open-Source Status** | CaP-X and ASPIRE are open-source; COAP has no public repo; GR00T 2 default repo remains N1.7 (public N2 branch is evaluation-licensed with a private base checkpoint). |
> | **DexLab Verdict** | **`experiment` (adopt feedback-view ablation, single-owner recovery contracts, and fresh-verifier skill cards; never replace physics engines or scorers with code agents)** — prove fine-grained traces improve failure attribution before expanding skill libraries or agent loops. |

---

## 1. What This Paradigm & Four Representative Works Actually Do

**Code as Policy (CaP) is not "another VLA"—it is an explicit control representation that expresses task phases, sensing checks, action order, and failure recovery as inspectable programs.** (Terminology note: here `CaP = Code-as-Policy`, distinct from `CAP = Contact-Anchored Policy` in [Discussion #309](https://github.com/huangkiki/Dexlab/discussions/309).)

### Problem Setup, I/O, and Four-Layer Execution Stack

Consider picking up a bread slice, lifting it, and placing it onto a plate via `localize_object` → `select_grasp` → `move_to_pose` → `close_gripper` → `verify_hold` → `open_gripper`. Inputs are **language goals + structured perception/state APIs + execution traces**, and outputs are **executable task programs, skill cards, or allowlisted tool calls**. Reliability breaks cleanly into four layers with distinct ownership:

(execution-stack)=
| Layer | Question Answered | Typical Artifacts | Timescale & Non-Conflation Boundary |
| --- | --- | --- | --- |
| **Task layer (System 2)** | What to do next, when to retry or stop | Language goal, stage state, completion checks, recovery selection | Outer-loop seconds (CaP-X turn `6.8–23.8 s`; GR00T 2 Agent median `7.5 s`); not a high-rate contact controller |
| **Program layer (CaP)** | How sensing, branching, and recovery compose | Python state machines, conditionals, allowlisted primitive calls | COAP frozen code runs in `0.3 ms` median CPU; returning `True` does not certify physical hold |
| **Skill / policy layer** | How localization, motion, or contact is executed | Grasp generators, IK/planners, VLA/WAM action chunks (`73–167 ms`), local controllers | Do not conflate executable task programs with natural-language task skills |
| **Execution & scoring layer** | How commands produce physics and who scores success | Simulator/robot controller, native contact readback, independent scorer | Programs and agents must never read rewards or mutate success predicates |

### Taxonomy & Deep Breakdown of the Four Representative Works

Recent systems span four distinct architectures that should not be lumped together:

(policy-map)=
| Work | Online Task Decision Maker | Core Artifact & Mechanism | Bottleneck Addressed | Key Evidence Boundary |
| --- | --- | --- | --- | --- |
| **[CaP-X](https://arxiv.org/abs/2603.22435v2)** | Coding model (single/multi-turn code gen) | Benchmark + abstraction, feedback, and test-time compute controls | Separates model reasoning from hand-built API scaffolding | Paper v2 lists 187 tasks vs. 39 in repo README; skill compilation filters successful trials without a fresh verifier |
| **[COAP](https://arxiv.org/abs/2610.12369v1)** | **No online model** (frozen stateful code); offline coding agent | 3-part explicit state + 5-layer library + worktree diff change gate | Auditable state, deterministic runtime, regression-gated code evolution | All results in RoboDojo sim with benchmark constants; no public repo located |
| **[ASPIRE](https://arxiv.org/abs/2607.00272v2)** | Coding agent debugging & repairing online | Per-primitive trace engine + fresh-verifier skill promotion + K-way evolutionary search | Stops one-off lucky fixes from polluting shared skill memory | Fixed allowlisted APIs cap expressiveness; verification proves transferability, not generalization; high compute cost |
| **[GR00T 2](https://research.nvidia.com/labs/gear/gr00t-2)** | System-2 Agent plans; CaP recovers; 2B WAM handles contact | MCP tool server + single control worker + joint video-action DiT | Decouples long-horizon recovery from fine contact-rich control | 97%–98% reflects DAgger + RL + recovery skills combined; default repo still N1.7, N2 branch is eval-licensed |
| *[HexaShell](https://arxiv.org/abs/2610.23479) / [Auriga](https://arxiv.org/abs/2611.01112)* | Generalist VLM writing short cells/tool calls in a harness | Generic tools, sandbox, readback + ~39–61 line Markdown **task skills** | Cuts per-robot/per-task code adaptation | Harness contributes substantially to success; task skills are text guides, not frozen programs |

Breaking down the concrete mechanisms of the four core works:

1. **CaP-X — Turning abstraction and feedback into controlled variables (§3, `cap-x@53e9966d`)**: Systematically varies (1) **abstraction tier** (high-level macros vs. low-level localization/grasp/IK primitives), (2) **temporal interaction** (one-shot vs. multi-turn debug), (3) **perceptual grounding** (text logs vs. interleaved raw RGB vs. **structured visual-diff text** summarizing object motion and gripper contact), and (4) **test-time compute** (multi-turn, skill synthesis, 9-way single-model or 3×3 multi-model sampling). Counterintuitively, **interleaving raw RGB often underperforms plain text logs, whereas translating before/after images into structured visual diffs yields large gains**—showing feedback must match the decision interface.

![CaP-X high-level vs low-level abstraction comparison](https://arxiv.org/html/2603.22435v1/high_vs_low.png)

*Figure 1 (from [CaP-X Figure 2](https://arxiv.org/html/2603.22435v1#S3.F2)): Removing high-level hand-engineered macros exposes large performance gaps across models, proving API abstraction level must be logged alongside any success score.*

2. **COAP — Frozen explicit state machine online, coding agent offline (§3, `2610.12369v1`)**: Explicitly contrasts itself with online VLM harnesses. Online execution consumes 3-view RGB, language, joints, end-effector pose, and gripper echo with zero model calls, updating **environment state** (object poses/sizes/relations with uncertainty, source, and timestamp), **robot state**, and **task state** across a 5-layer stack (`motion → perception → manipulation → object family → task program`). Offline, a coding agent inspects failure logs, edits in an isolated worktree behind default-off guards, and merges only diffs that clear validation-layout noise margins.
3. **ASPIRE — Per-primitive traces and fresh-verifier promotion (§3, `ASPIRE@fa00f0ef`)**: Captures per-call inputs/outputs, keyframes, mask overlays, grasp candidates, and planner status while restricting generated code to allowlisted tools (no access to rewards, success predicates, or privileged simulator state). New skill proposals live outside the shared library until a **fresh verifier**—blind to the proposer's code—solves **≥4/5 development seeds within 2 attempts**; downstream runs tag skills `useful / misleading / wrong / not-applicable`. K-candidate evolutionary search activates only when single-trace debugging plateaus, evaluated strictly on frozen held-out seeds.

![ASPIRE execution engine, skill promotion, and evolutionary search architecture](https://arxiv.org/html/2607.00272v1/system_design.png)

*Figure 2 (from [ASPIRE Figure 1](https://arxiv.org/html/2607.00272v1#S2.F1)): ASPIRE connects per-primitive execution tracing, fresh-verifier skill admission, and multi-candidate evolutionary search while strictly separating dev and held-out seeds.*

4. **GR00T 2 — Agent + CaP + WAM layering and the SuperMimic local-contact counterexample**: GR00T 2 pairs a frozen Wan VAE, frozen Cosmos-Reason1, and a 2B Cosmos-Predict2.5 DiT jointly denoising multi-view future video and 48-step action chunks (supporting joint or action-only disjoint inference) for contact-rich steps, while a System-2 Agent calls MCP tools (`wam_act`, `stop_wam`, SAM 3 `localize_object`, cuRobo `move_to_pose`) serialized by **one control worker** so control sources never collide. Crucially, the independent community port **[SuperMimic-manipulation](https://github.com/emoPointer/supermimic_manipulation)** serves as a sharp counterexample: in fixed-table, full-state mjlab simulation, a per-task differentiable world-model controller reaches `95.0%` on square-nut insertion and `90.2%` on drawer closing (256 held-out ARX5 resets each)—proving WAM's unique value lies in **open vision, language, multi-tasking, and cross-embodiment**, not exclusive mastery of local contact.

### Main Experiments, Results, and Built-in Counterexamples

| Work & Benchmark | Protocol & Denominator | Key Results (Author-Reported) | What This Proves / Counterexample |
| --- | --- | --- | --- |
| **CaP-X** (7 core tasks, 12 models) | 100 trials/tier across abstraction, turns, visual diff, 9-way sampling | Removing high-level macros drops SR sharply; multi-turn + structured visual diff + parallel compute recover much of it | **API scaffolding and feedback format dominate scores**; raw model SR cannot be read without interface conditions |
| **COAP** (RoboDojo 42 bimanual tasks) | Sim RGB + proprioception + language, zero online LLM calls | COAP **`70.24%`** vs. best WAM `29.64%` / VLA `27.96%`; Memory **`90%`** vs. Harness `47%`; median CPU **`0.3 ms`** | Explicit state and pixel measurement excel in sim; yet 62% of remaining failures are still perception/contact |
| **ASPIRE** (LIBERO-Pro, Opus 4.6) | Zero-shot → trace engine + skill loop → + evolutionary search | Mean success **`14% → 62% → 72%`** (up to 99% under full budget/config) | **Largest gain comes from per-primitive trace + skill loop (+48 pp)**; evolutionary search adds +10 pp at high cost |
| **GR00T 2 Agent+CaP** (Real assembly & insertion) | 3 dumped-part assemblies (100 trials each); 5-in-a-row insertions (20 each) | Assembly SFT+DAgger `84/71/78` → +Agent+CaP **`98/97/97`**; insertions SFT+RL+Agent **`19/20` (cable), `20/20` (charger)** | Clear system-level reliability boost; **counterexample: S2 intervention without RL succeeds only `24%` (RoboDojo 188/773) and `56%` (RoboCasa 553/988)** |
| **SuperMimic-manipulation** (ARX5 mjlab) | 256 held-out resets, per-task training (3.4–10.5 h on A100) | `square` **`95.0%`**, `drawer` **`90.2%`**; second `drawer` seed `75.9%` (checkpoint swing `24–90%`) | Task-specific state controllers can cover local contact in known sim; lacks vision, language, cross-embodiment, and hardware validation |

---

## 2. Counterexamples, Hidden Switches, and Evidence Boundaries

1. **`S2 intervenes ≠ S2 rescues`, and visual checks still miss physical failure**: In 300 real GR00T 2 Agent assemblies, 3 of 8 failures were **partially driven screws marked complete by both GR00T 2 and the Agent**; in sim, 38%–39% of SFT+Agent failures needed finer manipulation than S2 motion planners could provide, 24%–38% hit unrecoverable states or timeouts, and robots spent 38% of YAM table-clearing time waiting on the Agent (median 7.5 s/turn).
2. **Abstraction leakage and skill contamination**: High-level `pick()` calls hide shallow grasps and slip; CaP-X (`53e9966d`) compiles skills strictly from successful trials without a fresh verifier, risking freezing scorer exploits; and even ASPIRE's 5-seed admission explicitly verifies *knowledge transferability*, not cross-task generalization or ongoing re-validation.
3. **Cross-paper headline scores are not comparable**: COAP's `70.24%` (42 RoboDojo tasks), HexaShell's `85.0%`, and GR00T 2's `75.8%` (RoboDojo layout bank 0) differ in layout banks, privileged constants, retry budgets, and default-executor selection.

(cap-evaluation)=
### Minimum 7-Item Evaluation Checklist for Code as Policy

Any credible comparison must log: (1) primitive abstraction tier and whether usage examples are supplied; (2) turn count, feedback modality, and token/call budget; (3) whether tool returns report actual arrival, contact, error codes, and keyframes; (4) separation of dev, unseen-check, and frozen held-out seeds; (5) pinned versions of program, model, harness, controller, simulator, and scorer; (6) inclusion of invalid runs, timeouts, API errors, and physics failures in the same denominator; and (7) confirmation that tested code/agents cannot read rewards, success predicates, or privileged/future state.

---

## 3. What DexLab Should Borrow & First Minimal Validation Slice

(dexlab-policy)=
For DexLab, Code as Policy is best used as **an auditable representation for failure attribution, command ownership, and verified diagnostic memory**—never as a substitute for physics engines or independent scorers.

- **Adopt directly**:
  1. **Four-layer ownership + single-commander contract**: Separate task logic, allowlisted primitives, execution readback, and independent scoring; stop any active controller before handoff and log `command_owner`, `recovery_attempted`, `recovery_succeeded`, `stage_resumed`, and `full_task_succeeded` separately, blocking agent access to reward/success.
  2. **Run feedback ablations before building agent loops**: Test which observation packet actually disambiguates competing physical hypotheses on existing failures.
  3. **Promote root-cause knowledge via gated skill cards**: Structure cards as `failure signature → trigger preconditions → repair action → scope boundary → supporting evidence → counterexamples`, distinguishing `verified_once`, `transferred`, and `refuted`.
- **Validate after adaptation**:
  - On one known full-state contact task in simulation, benchmark task-specific SuperMimic-style differentiable world-model control against same-state PPO, scripted control, and generalist WAM post-training under **identical observations and one independent scorer**.
- **Defer or reject**:
  - Do not build a multi-agent coordinator platform, automatic curriculum, or default 9-way/evolutionary search;
  - Do not overload "skill" across natural-language `task skills` and executable `task programs`;
  - Do not treat RoboDojo / LIBERO-Pro / real-world composite scores as default DexLab targets.

### First Minimal Falsifiable Slice

- **Question**: On DexLab's existing [bread-slip failure record](robodojo-bread-slip.md), with physics and independent scoring frozen, do structured per-primitive/contact traces and a single-owner recovery contract improve **first-failure-layer attribution** and reproducibility?
- **Controlled comparison**:
  1. **Feedback ablation (CaP-X / COAP)**: Present the same frozen failure trajectories under View `A` (stage, success predicate, before/after images or structured visual diff) vs. View `B` (`A` plus per-primitive commands/arrivals, contact onset/loss, normal impulse, and first slip timestamp) to independent diagnosticians;
  2. **Single-owner contract & skill-card gate (GR00T 2 / ASPIRE)**: Compare a fixed scripted baseline against a restricted Agent reading only structured state and invoking allowlisted recovery primitives (no reward/success access); promote any resulting repair only if a code-blind fresh verifier passes on 5 dev seeds (≤2 attempts) and reports held-out seeds separately.
- **Pass / stop criteria**: Require accurate first-failure localization supported by actual measurements, separation of competing hypotheses, and unchanged failure/timeout denominators. Stop before expanding agents or skill libraries if finer traces do not improve attribution or if fixed scripts match Agent recovery.

---

## 4. Verifiable Sources & Inspection Scope

- Papers & whitepapers: [Code as Policies (arXiv:2209.07753)](https://arxiv.org/abs/2209.07753) · [CaP-X (arXiv:2603.22435v2)](https://arxiv.org/abs/2603.22435v2) · [COAP (arXiv:2610.12369v1)](https://arxiv.org/abs/2610.12369v1) · [ASPIRE (arXiv:2607.00272v2)](https://arxiv.org/abs/2607.00272v2) · [HexaShell (arXiv:2610.23479)](https://arxiv.org/abs/2610.23479) · [Auriga (arXiv:2611.01112)](https://arxiv.org/abs/2611.01112) · [GR00T 2 Whitepaper](https://research.nvidia.com/labs/gear/gr00t-2/assets/gr00t2_whitepaper.pdf)
- Pinned repos: [`capgym/cap-x@53e9966d`](https://github.com/capgym/cap-x/tree/53e9966d7a8e2fa7494676772bccc35280f5c0ed) · [`NVlabs/ASPIRE@fa00f0ef`](https://github.com/NVlabs/ASPIRE/tree/fa00f0ef2bc1d91d594b9aa502c22133c9f538f7) · `Isaac-GR00T` `codex/n2-action-expert@7e492ad1` · [`emoPointer/supermimic_manipulation@eda7da48`](https://github.com/emoPointer/supermimic_manipulation/tree/eda7da480c6d92a68cc41c9628b7efdae08cae23)
- Related discussions & DexLab pages: [COAP #335](https://github.com/huangkiki/Dexlab/discussions/335) · [CaP-X #341](https://github.com/huangkiki/Dexlab/discussions/341) · [ASPIRE #342](https://github.com/huangkiki/Dexlab/discussions/342) · [GR00T 2 #419](https://github.com/huangkiki/Dexlab/discussions/419) · [Bread-slip evidence](robodojo-bread-slip.md) · [Model evaluation](model-evaluation.md) · [Dexterous simulation guide](dexterous-hand-simulation.md)
- **Inspection scope (2026-11-26)**: Synthesized from papers/whitepapers and static inspection of pinned commits. All success rates, latencies, and rescue counts are author-reported; no public COAP repo was found, and GR00T 2 official release code is listed for 2026-12 (the non-default N2 branch carries an evaluation license and private base checkpoint). No external agents, external benchmarks, or new DexLab physics experiments were run.
