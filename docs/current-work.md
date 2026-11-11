# Current work and execution state

[English](current-work.md) | [简体中文](current-work.zh-CN.md)

**Updated 2026-11-11. Development follows question → scoring semantics → comparison → attribution → finding; scheduled development remains PAUSED.** This is the sole current entry for research selection and recovery. This update adopts design ordering; it launches no training or physics run and changes no queue labels, existing protocols, scientific thresholds or execution permissions. [Full workflow](autoresearch.md#research-loop)

## Start from the findings

Synthetic torsional contact reduces Wuji's two-second maximum hold displacement from 2.734 to 1.025 mm, without establishing solver failure or hardware calibration. RSS controls show that assistance can determine task success. Contact-response baselines reduce position error but still miss contact loss. These [findings and evidence](../README.en.md#findings) put measurement semantics and the first failing layer ahead of expansion.

## Recovery and design order

| Direction | Existing entry and current evidence | Next step and exit |
| --- | --- | --- |
| **Recover the in-hand candidate first** | CHORD preparation [#283 / PR #284](https://github.com/huangkiki/Dexlab/pull/284) is merged. [PR #292](https://github.com/huangkiki/Dexlab/pull/292) remains draft at this check; public records report finite training/checkpoint reload but failed off/on and off/off repeatability. Complete migration remains 0/3. | Recover original handles, records and cumulative budgets in [#285](https://github.com/huangkiki/Dexlab/issues/285). Diagnose repeatability and recording before independent scoring; off/on differences alone do not isolate a recorder effect. Preserve the existing delivery gate. |
| **First new design: scorer semantics audit** | [Discussion #302](https://github.com/huangkiki/Dexlab/discussions/302) proposes using existing Wuji evidence; the audit is not implemented or run. | State required events and task intent, then design region/tolerance, event-order, idle, hidden-support and state-injection counterexamples, identifying the responsible check layer. Resolve semantic false positives or missing observations before interpreting gains. |
| **Conditional follow-up: a short persistent contact sequence** | Single-episode passes do not establish reliable state propagation across jobs; reset/no-reset comparisons remain a proposal. | After scoring semantics are clear, design the shortest hold, unload/re-establish, release sequence. Freeze job boundaries, carry state and run-based statistics. Stop expansion for unstable positive controls, accepted negatives or no interpretable difference. Preserve [#48](https://github.com/huangkiki/Dexlab/issues/48)'s original acceptance. |
| **With compatible inputs: learning and action response** | [#261](https://github.com/huangkiki/Dexlab/issues/261) has delivered offline baselines but lacks native action interventions and a compatible model. CHORD parent [#282](https://github.com/huangkiki/Dexlab/issues/282) retains all three native tasks. | Following [#281](https://github.com/huangkiki/Dexlab/discussions/281) and [#293](https://github.com/huangkiki/Dexlab/discussions/293), fix the policy before comparing actions/physics. Consider retraining and crossed evaluation only for independently justified physics changes; report task and physical gains separately. |

This is recovery priority and design ordering, not a serial dependency chain. Scorer audit preparation can use existing evidence independently; CHORD recovery does not wait for the new sequence. New designs have no execution task or budget yet, and a Discussion grants no launch permission. Native experiments still freeze the complete applicable matrix, cases, protocol and finite resource plan under existing rules; a minimal case does not shrink existing acceptance scope.

## Preserved scope and blockers

- **Wuji #48:** the receiving-finger/rolling route and transition protocol remain undecided. Signed rotation after qualified grasping, no hidden support and ten new conditions remain required. A persistent sequence does not replace in-hand acceptance.
- **CHORD #282:** tissue-box first, then the two ARCTIC tasks with lawful data/licenses and runtime prerequisites. Finite training is not independent task success; unmerged candidates are not mainline results.
- **Existing failures and evidence gaps:** retain AMP #259 recorder parity, RSS #247 provenance/raw gaps, LIBERO #181's full scope and #198's public interpretation, cutting #200's matched inputs and hardware #6's missing measurements. Missing hardware does not block independently justified numerical analysis.
- **Delivered infrastructure:** attempt isolation #243, installation protection #245, author/pause admission #244, offline bundle #250, Wuji qualification #251 and SDF engineering #211 are delivered, not new backlog. Parent obligations for native SDF research, cloth, applicable engine coverage and UniSim migration remain open where unmet.
- **Deferred expansion:** generative assets/worlds, the seven-task factory, a universal differentiable engine interface and larger task libraries. The browser claw machine remains a toy demonstration, not a mainline research result or automatic README milestone.

Detailed acceptance, historical priorities and cumulative scope remain in the [November 3 main snapshot](https://github.com/huangkiki/Dexlab/blob/4c3dafc1cd96b90c09a36f0c178c6eeab9bd015b/docs/current-work.md) and each Issue. The snapshot is provenance, not a current dispatch order. This update closes no task and changes none of their scope or state.

## Execution and delivery entries

[Project 4](https://github.com/users/huangkiki/projects/4) and Issues hold live execution scope, dependencies, budgets and blockers; read back actual state on recovery. Preserve [UniSim #142](https://github.com/huangkiki/Dexlab/issues/142)'s ownership boundary: DexLab owns experiments, recording and independent scoring; production adapter gaps belong to UniSim, with qualified native references retained.

Follow the [operating guide](autoresearch.md) and [AGENTS](../AGENTS.md): one executor, preserved dirty work, failures and cumulative budgets; missing or malformed dispatch state means paused. `next --dry-run` inspects candidates without resuming a scheduler. Priorities, Discussions and plans cannot bypass author, dependency, resource or authorization checks.

Each delivery updates the report's finding, scope and next decision; README retains consequential findings and milestones. Continue authorized exact-head review, applicable gates, merge and deployment readback; partial delivery does not close a parent. Obsidian commit/push remains paused.
