# Unified-drive pinch boundary: development roadmap

[简体中文](pinch-boundary-roadmap.zh-CN.md) · [Discussion](https://github.com/huangkiki/Dexlab/discussions/129) · [Research tracker](https://github.com/huangkiki/Dexlab/issues/130) · [Autodev retrospective](https://github.com/huangkiki/Dexlab/discussions/127)

**Status: [A protocol/data contract](pinch-boundary-protocol.md) and engine-free case expansion are implemented; backend qualification, independent scoring and the formal campaign remain undelivered.** This page records approved requirements and task relationships, not an executable frozen protocol. A defines the repository protocol and matrix; C freezes the independently verified implementation/scorer before D starts the formal campaign. Planning baseline: `026855534c612ba395c2a2f9cfe75a71ecd5a1bf`; `b4ca4e3` is a historical source. Recheck main when starting work and freezing a campaign.

## Question and adopted choices

Under a common fixture and external PD controller, determine how per-finger drive-force caps affect retention and release, including sensitivity to initial state, timestep and repeated execution. The first cohort covers MuJoCo and Genesis CPU FP64, with static curves, case-level results, raw records and bilingual reports. Retain the complete six-engine coverage table. An interactive replay viewer is outside this first delivery; preserve states and timing for later replay.

- Derive the common fixture from the existing Genesis finite gripper: a 40 mm, 64 g cube, two finite fingers, a lift carriage and horizontal table. Fix masses/inertias, joint axes/limits, initial state, collision pairs and the four-second close/lift/hold/release trajectory. Build the corresponding finite MuJoCo fixture. Do not pool the old guided-plane or native-drive cohorts.
- DOF order: lift, left finger, right finger. `u = clip(Kp * (q_ref - q) - Kd * qdot)`, with `Kp=[1000,500,500] N/m`, `Kd=[50,20,20] N·s/m`, lift cap ±50 N and symmetric per-finger case caps. No target-velocity feedforward or gravity compensation.
- Use a 1 ms control clock and 1/0.5/0.25 ms physics steps, integer control ticks and zero-order hold between updates. Each backend closes the loop on its own state. Use unit-transmission MuJoCo force actuators and direct Genesis joint forces; disable and verify hidden position drives, passive damping and added joint inertia.
- Admit official latest-stable compatible combinations before freezing versions, source/native binaries, dependencies, contact/solver settings and effective readbacks. Equal nominal friction is not material equivalence; current defaults cannot identify a historical algorithm.

## Deliveries and ownership

| Item | Dependency | Acceptance |
|---|---|---|
| [A: protocol and data contract](https://github.com/huangkiki/Dexlab/issues/131) | None | Freeze fixture, matrix, criteria, budget, observation epochs and six-engine status |
| [B: two native backends and qualification](https://github.com/huangkiki/Dexlab/issues/132) | A | Shared controller, finite fixtures, direct force control and native observations qualified |
| [C: independent scoring and campaign checks](https://github.com/huangkiki/Dexlab/issues/133) | B | Offline scoring, negative/corruption tests, check-campaign and formal version freeze |
| [D: formal campaign and bilingual evidence](https://github.com/huangkiki/Dexlab/issues/134) | C | Complete cohort, independent rescore, curves, data and reproduction instructions |

The parent is tracking-only and must not be dispatched. Children use `priority:P1` and `auto:approved`. First inspect and safely recover or conclude in-flight work; then handle actionable P0s; then prefer eligible children of this maintainer-selected workstream. Read `next --dry-run`, confirm the child is eligible, and use the existing `start ISSUE` entry. The default selector's creation-time tie-break does not override this explicit workstream choice. If no child is eligible, record why and continue other independent authorized tasks. Preserve isolated worktrees, a single worker and the existing `submit` gate. No new scheduler or scheduled job is introduced.

[#124](https://github.com/huangkiki/Dexlab/issues/124), [#125](https://github.com/huangkiki/Dexlab/issues/125) and [#126](https://github.com/huangkiki/Dexlab/issues/126) remain higher priority. Add an audit dependency only when consuming its affected historical evidence; unrelated historical gaps do not block independently qualified new records. The incline matrix [#121](https://github.com/huangkiki/Dexlab/issues/121) and Drake [#117](https://github.com/huangkiki/Dexlab/issues/117) retain their own acceptance; pinch delivery cannot close them.

Discussion preserves reasoning, dissent and adopted decisions. Issues own bounded questions, scope, dependencies and acceptance; PRs deliver implementation. Runs follow reviewed repository protocols/manifests. Changes after freeze use a new version while retaining old evidence. Track concrete uncertainties immediately. Return to the same Discussion after B qualification and D reporting, record which assumptions survived and turn actions into Issues. A link or consensus is not technical resolution.

## Planned interface and records

The available `python -m dexlab.pinch_boundary list-cases` exports protocol identities only. The planned acquisition/scoring entry has `qualify / run / score / report / check-campaign` commands; these do not exist yet. Inputs are a frozen manifest and case identity. Acquisition, offline scoring and reporting are independent. A defines the minimum data contract; B/C implement it without a speculative general framework.

At every physics step, separately retain pre/post states, control-update epoch, target, pre/post saturation commands, native actuator force, and contact identities/positions/normals/forces with their epochs. Record solver status, warnings, costs and first failure. Commands, actuator forces and contact forces are separate observations. Unobservable fields remain missing with a reason; unavailable required observations block backend admission. Never copy a command as native measurement. Hash-bind protocol, models, acquisition code, scorer and raw records.

## Campaign and budget

| Dimension | Adopted requirement |
|---|---|
| Backends | MuJoCo and Genesis; CPU FP64 |
| Per-finger caps / N | 0.2, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 10 |
| Initial lateral offsets / mm | −2, 0, +2 |
| Physics steps / ms | 1, 0.5, 0.25; control period fixed at 1 |
| Repeats and duration | Three fresh processes per condition with the same seed; 4 s each |

The formal cohort has `2 × 11 × 3 × 3 × 3 = 594` episodes: 198 fixed conditions, not a population success-probability estimate. Add 24 controls: 18 open-finger cases (two engines × three offsets × three steps) and six nominal-zero-friction cases (centered, 10 N, two engines × three steps). Record friction floors/combination rules and torsional/rolling terms. At most 32 qualification episodes include no-contact known-force checks, control-mode checks and a separately reported native-Genesis-drive/external-PD bridge.

**The campaign has a cumulative 6 h / 700-start cap, with at most 30 min per process and no new cloud resources.** Include qualification, bridging, formal runs, controls and retries, including initialization, compilation, observations and writes. Development and submission regressions are accounted separately under existing resource limits; relabeling campaign attempts as debugging cannot evade the cap. The maximum base allocation is 650 starts (594+24+32); using all qualification slots leaves at most 50 additional starts.

B/C must deliver a recoverable ledger of every attempt, complete process wall time, reason, remaining allowance and output. Check allowance before launch, actively terminate at timeout, preserve totals across recovery and avoid duplicate claims. Each timeout is bounded by both the remaining global allowance and 30 min. Only infrastructure/recording failures allow bounded retries; physical failures cannot be rerun until success. Use qualification timings to assess complete-cohort feasibility, not promise completion from a budget. On exhaustion, remaining cases stay not-run with an interim report and recovery conditions; never shrink the matrix to declare completion.

## Scoring and completion

The [A protocol](pinch-boundary-protocol.md) fixes these adopted criteria; B/C must implement and verify them:

- Hold window [2,3] s: center height always ≥60 mm, both fingers in effective contact, other vertical support ≤0.01 N. Release window [3.8,4] s: center height ≤30 mm and sum of per-contact finger-force magnitudes ≤0.01 N. Define effective contact, frames and sample epochs.
- Retain the 1 mm penetration budget, `1e-8 N` contact-ledger consistency and 5% gravity-impulse residual. The ledger compares summed contact forces with net object contact force; it does not qualify actuator output or known-force dynamics. A/B separately define and verify those checks and tolerances.
- Use analytical cube/plane geometry and a complete finite-OBB check with an explicit quantitative penetration definition at the same state epoch. Report native contact depths separately.
- Separately report record integrity, numerical status, penetration, hold/release, fixture-relative displacement/velocity, measured normal load, contact impulse and cost. First threshold breach is not a physical slip-onset estimate.
- Test PD/saturation/sign/control ticks across all timesteps; known no-contact forces and native output; contact signs/frames/epoch mismatch/missing samples; rotation/edge overlap/no-collision geometry; corrupted records, wrong hashes, duplicate/missing cases, numerical abort and ordinary task failure; open-finger and nominal-zero-friction controls. Investigate geometric support or contact configuration before interpreting anomalous retention; do not change thresholds to remove it.
- Test recovery without duplicate dispatch or budget reset, refusal of wrong-hash reuse, retention of failures and regeneration of figures from frozen data. Code delivery retains the full repository regression gates.

Retain all three repeats per curve. Only monotonic results support a tested-grid transition interval; report passing segments and mixed results for reversals/disagreement. Do not interpolate a precise boundary across the unsampled 0.8–10 N gap.

`check-campaign` checks coverage, evidence validity and task outcomes separately; it does not require every grasp to succeed. Qualified physical failures, penetration violations and numerical aborts with a reproducible valid prefix and first-failure evidence are outcomes. Not-run cases, unrecoverable records and exhausted infrastructure retries cannot establish complete delivery. Formal completion requires verifiable experimental terminal outcomes for all 594+24 cases, every attempt retained, independent rescoring and traceability of every figure/number. Otherwise deliver an interim report.

## Six-engine coverage and expansion

These states refer to **this common fixture**, not historical success on other tasks:

| Engine | Current state | Qualification or restoration requirement |
|---|---|---|
| MuJoCo | not-run; common fixture unqualified | [B](https://github.com/huangkiki/Dexlab/issues/132): finite fixture, direct forces and native observation qualification |
| Genesis | not-run; external PD unqualified | [B](https://github.com/huangkiki/Dexlab/issues/132): control transition, native readbacks and bridge; #125 audits old evidence |
| SuperDex | not-run; later expansion | [Parent](https://github.com/huangkiki/Dexlab/issues/130): common fixture/control/observation qualification; #124 before historical identity reuse |
| Newton Physics | not-run; later expansion | [Parent](https://github.com/huangkiki/Dexlab/issues/130): applicable solver, precision and fixture qualification; existing float32 evidence does not establish FP64 |
| PhysX | not-run; later expansion | [Parent](https://github.com/huangkiki/Dexlab/issues/130): native version, interfaces and common fixture; historical #126 does not replace new admission |
| Drake | not-run; later expansion | [Parent](https://github.com/huangkiki/Dexlab/issues/130) with #117: installation/import is not positive-duration qualification |

Keep the parent open after the first cohort. Before expansion create bounded backend tasks and qualify against the same protocol. First-cohort claims concern drive-force caps under specified configurations, not real-material thresholds, robot accuracy or a universal engine ranking.
