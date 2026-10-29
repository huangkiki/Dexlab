# Current work and execution state

[English](current-work.md) | [简体中文](current-work.zh-CN.md)

**Decision date: 2026-10-26. The maintainer has authorized interactive autodev execution of the sequence below; scheduled development remains PAUSED.** This is the sole current ordering entry referenced by AGENTS and the operating guide. Continue eligible slices through acceptance and delivery. Each new physics campaign still requires its frozen protocol and finite resource budget; no training or background dispatch is authorized.

## Status reconciliation — 2026-10-29

The first four rows below are delivered: #243, #245, #244, #250 and #251 are closed. #48 remains the in-hand parent; its receiving-finger versus rolling decision and new transition protocol are still pending. This review resumes the existing #211 SDF engineering candidate through its full delivery gate, without launching the parent's native SDF campaign.

The three imported cases have separate outcomes: #260 is completed after PR #262 and the documented non-reproduction acceptance; PR #264 is merged but #259 remains blocked by the AMP recorder-parity failure; PR #265 is merged but #261 still lacks a compatible model and qualified native intervention evidence. Merged infrastructure does not complete either parent. Preserve the original records and budgets; existing eligible engineering work can continue while those decisions or inputs are missing.

## Intended delivery

Build a reproducible starting case around **Wuji grasping, unloading and contact switching**, so another user can rerun it and inspect why it fails. Qualify positive and negative grasp controls before interpreting a transition failure. Finding no solver failure is an acceptable result; separate task, acquisition/control, geometry and numerical-solver failures.

The [published audit](https://huangkiki.github.io/Dexlab/en/latest/solver-failure-audit.html) establishes no qualified Wuji in-hand solver failure: RSS wiping demonstrates assistance dependence in a fixed configuration, while Proxy cloth first fails acquisition. The plan adds those missing discriminating controls rather than presuming a unified multiphysics system is the answer. [Discussion #222](https://github.com/huangkiki/Dexlab/discussions/222)'s separation of contact intent from feedback and [#189](https://github.com/huangkiki/Dexlab/discussions/189)'s task-first entry point inform one concrete case below. The [first native Wuji fixture](https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html) now passes its six development controls with synthetic torsional contact; its two-second holding window and slow drift remain explicit. Improved user onboarding time has not been measured.

## Delivery order and acceptance endpoints

| Order | Issue | Evidence required at completion |
| --- | --- | --- |
| 1 | [Attempt isolation #243](https://github.com/huangkiki/Dexlab/issues/243) | Repeated starts, interruption and reset cannot overwrite prior artifacts or mix a new manifest with an old success summary; full applicable regression passes. |
| 2 | [Installation protection #245](https://github.com/huangkiki/Dexlab/issues/245); [author admission and pause #244](https://github.com/huangkiki/Dexlab/issues/244) before automated dispatch | Both installers reject incompatible environments before side effects. Dispatch obeys trusted authors, dependencies and one machine-readable pause authority. #244 does not block independently authorized interactive work. |
| 3 | [Public rescore bundle #250](https://github.com/huangkiki/Dexlab/issues/250) | Downloadable evidence reconstructs one existing latch/no-latch result and its curves offline, with raw observations, failed-attempt index, licenses and hashes. Remaining RSS raw-publication gaps stay in #247. |
| 4 | [Wuji grasp qualification #251](https://github.com/huangkiki/Dexlab/issues/251) | A fixed-wrist simple-object positive control works; hold/unload/release requests produce measured contact behavior and invalid controls are rejected. Stop at acquisition/control diagnosis if the positive control fails. Reusing the output entry point first depends on #243. |
| 5 | [Wuji in-hand parent #48](https://github.com/huangkiki/Dexlab/issues/48) | Controlled contact switching and signed rotation follow qualified grasping; reject palm-only motion, oscillation accumulation, hidden support and state injection, then validate ten new conditions after freezing development. |

This is delivery order, not a chain of artificial dependencies. #250 can use existing records independently, and #251's static preparation can start earlier. Before native execution, freeze configuration, justified metrics, the full applicable matrix, named cases and measured finite resource budgets in the corresponding issue. #251 preserves its prospectively frozen cohorts, actual outcomes and cumulative budget in the issue and evidence bundle. No new cloud resources, training, engine-source edits or hardware motion are included.

## Reconciliation and retained scope

The audit starts from 36 open issues and one draft PR, checking relevant source, merged evidence and Discussions #189/#220/#222. It is a task/evidence review, not a rerun of every historical experiment.

- [#246](https://github.com/huangkiki/Dexlab/issues/246) tracks the actual state repair: delivered #177/#183/#184 no longer lead the queue; #174's dependency syntax is corrected; #6 states hardware is unavailable; #223 is no longer dispatched again. Close #246 only after validation, merge, deployment and readback.
- [#223](https://github.com/huangkiki/Dexlab/issues/223)'s eight wiping-reproduction items were delivered by PR #225. Transfer its unresolved cross-cohort explanation to [#247](https://github.com/huangkiki/Dexlab/issues/247), preserving exact cohorts, metrics and recovery conditions. Closing reproduction does not explain that difference. #247 retains the 18 paper-scene inputs, Proxy attribution and unpublished raw records.
- LIBERO [#181](https://github.com/huangkiki/Dexlab/issues/181) retains **all 130 native tasks and every official demonstration**. Defer #185/#188/#174/#198 and visual-policy #182. #198 remains a P0 public-interpretation gap; #185 retains transfer failures and cumulative limits. Partial Object/Spatial evidence does not complete the parent or resume downloads/weight acquisition.
- Retain original acceptance and candidate code for SDF #178/#211, cloth #28/#179, six-engine incline #121 and #157/#159/#163/#165, pinch #130/#132/#133/#134, UniSim #142/#145, ManiSkill #47, replay audit #52 and material benchmark #3. Defer these to P2 this cycle. Old In Progress items without an actual executor return to Todo; genuine external/dependency blockers remain Blocked. #28 and #179 are parent/child, not duplicates. The 594+24 campaign and cumulative budgets remain unchanged.
- [#249](https://github.com/huangkiki/Dexlab/issues/249) first addresses Newton SolverMuJoCo versus direct MuJoCo Warp identity/wrapper parity at P2; #152 retains its independent Isaac Sim and other task scope. libuipc #218 remains candidate assessment. #200 lacks the author's matched cutting inputs and remains P0/needs-input. Hardware #6 remains Blocked; numerical work does not depend on it.
- [PR #199](https://github.com/huangkiki/Dexlab/pull/199) merged on 2026-10-28 as `43debaf917cbcafbd853bfd5d942ef054f005979`. The reading route is no longer a draft awaiting recovery; do not create a duplicate PR.

Planning adds no automated-dispatch approval. Historical `auto:approved` labels are cleared according to this ordering without revoking existing interactive authority. **Missing or invalid persistent dispatch state now defaults to paused; only explicit resume enables new automatic work.** See the [operating guide](autoresearch.md#author-admission-and-persistent-pause) for commands and interactive recovery. Before restoring automatic execution, require trusted-author admission, pause/dependency checks and actual `next --dry-run`, never this document alone.

## Recovery and delivery

[Project 4](https://github.com/users/huangkiki/projects/4) owns live queue state; issues own scope, dependencies, protocol, budget, acceptance and blockers; PRs/frozen records establish results. Preserve [UniSim #142](https://github.com/huangkiki/Dexlab/issues/142)'s ownership boundary: disclose qualified native reference paths used in experiments; new production-adapter gaps belong in UniSim, without building another framework for this cycle.

The [operating guide](autoresearch.md) and [AGENTS](../AGENTS.md) retain one executor, immutable evidence, explicit runtime profiles, resource admission and complete applicable gates. Follow each authorized slice through review, exact-head merge and deployed/asset readback; close only after complete acceptance, rather than stopping at PR creation.

The previous priority order is retained in the [2026-10-21 main snapshot](https://github.com/huangkiki/Dexlab/blob/af788be6be4a265edb1ec1b95671e11f05d1d1d2/docs/current-work.md). Earlier decisions remain in the [AGENTS snapshot](https://github.com/huangkiki/Dexlab/blob/e3561c8def027f777df25ad41e67a2aea3b21144/AGENTS.md) and [operating history](autoresearch-2026-10-10.md). Historical ordering is not a current launch instruction; scientific acceptance and evidence-preservation obligations remain binding.
