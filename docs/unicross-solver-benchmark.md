# UniCross: reference review and incremental question for DexLab

[English](unicross-solver-benchmark.md) | [简体中文](unicross-solver-benchmark.zh-CN.md)

**Review date: 2026-10-11. Status: reference-only; no implementation or experimental acceptance.** This note does not launch a cross-engine campaign, change existing priorities, or resume scheduled development.

## Source identity and review depth

Reference: Hui Zhang, Julian Ferchow, Jie Song and Mirko Meboldt, *UniCross: Unified Cross-Skill Dexterous Manipulation Synthesis*, [arXiv:2607.28198v2](https://arxiv.org/abs/2607.28198v2), revised 2026-10-07; [official project page](https://zdchan.github.io/UniCross/).

The project page and arXiv abstract/metadata were checked, not the full paper or implementation. The authors describe a shared hand-object relational formulation for grasping, relocation, in-hand rotation and in-hand translation, with a unified per-hand policy for composition. The project page also describes Isaac Gym, Isaac Lab and mjlab implementations, while its code entry still says “Coming soon” on the review date. These are author-reported demonstrations, not a DexLab-verified runnable release.

Code revision, task assets, policy/controller availability, redistribution terms, native solver identity and effective parameters remain unqualified. A paper license does not establish code or asset permission. Do not infer source access from a video or treat different frameworks as independent physics engines. This supplement does not change the historical 38-paper survey count or claim another reproduction.

## What would add information beyond existing work?

The existing [dexterity roadmap](https://github.com/huangkiki/Dexlab/blob/main/docs/dexterity-roadmap.md) and [#48](https://github.com/huangkiki/Dexlab/issues/48) already cover in-hand rotation, contact switching, drops and independent scoring. Adding another rotation demonstration would largely duplicate that scope.

The incremental hypothesis is narrower: **does changing the relational goal between skills, without resetting the object or restoring a prepared grasp, expose a reproducible failure not explained by the constituent single-skill cases?** Study transition history, the first divergent contact event, retained support and accumulated error. This is a proposed DexLab question, not a physics-accuracy claim established by UniCross.

Reuse the task/phase formulation as a reference; defer adopting a training stack. Keep scene-selection questions separate from controlled solver attribution. Lower policy success alone cannot locate the error in geometry, actuation, contact modelling or the solver.

## Candidate probe, not a frozen execution protocol

A possible original probe is hold → prescribed in-hand rotation or translation → hold. Define targets relative to the hand, disclose wrist constraints, initial preparation and every external support, and forbid hidden object-state injection or between-skill resets. Verify a usable controller first; random actions are not a reproduced manipulation skill.

Compare the composed sequence with separately declared constituent controls. Do not claim identical starts from equal seeds or silently restore a mid-episode state. A reduced fragment must reproduce the corresponding full-prefix observation before being used for attribution. Fixed command replay and a fixed closed-loop controller are different experiments: the same controller can issue different commands after the engines' measured states diverge.

Before execution, freeze geometry/inertia, effective material/contact settings, clocks, control, applicable profiles, cases, references, thresholds and resource budget. Independently retain record integrity, numerical consistency, physical-reference validity, task outcome and remaining causal alternatives. Keep all failures, costs and unavailable signals. Development choices need genuinely new frozen validation conditions; historical records cannot become unseen holdouts.

Follow existing six-engine applicability and evidence rules, but do not launch a six-engine implementation programme merely because this reference exists. [SDF #178](https://github.com/huangkiki/Dexlab/issues/178) applies when the selected probe depends on fine-feature SDF geometry; [cloth #179](https://github.com/huangkiki/Dexlab/issues/179) applies only to a cloth/deformable extension, not as an artificial prerequisite for rigid rotation. Real-material validation still needs matched measurements; synthetic reference work does not wait for unrelated hardware data.

## Reuse/defer decision

**Reuse:** relational goal definitions and continuous skill-transition questions, connected to #48 rather than a duplicate task line.

**Defer:** upstream reproduction, policy training, new simulation frameworks, broad asset downloads and comparative performance claims until the needed source, controller, license and runtime evidence exists. No training, paid service, new scheduler, engine patch, threshold change or native run is authorized by this note.

Advance only when an available controller and qualified fixture can test a transition-specific hypothesis with information beyond #48. Otherwise keep this as a reference. The first deliverable is a source/admission checklist and the incremental question, not a success-rate table. The related taxonomy and workflow correction was delivered by [#177 / PR #180](https://github.com/huangkiki/Dexlab/pull/180). [Current work](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.md) governs execution priorities; [PR #176](https://github.com/huangkiki/Dexlab/pull/176) records the documentation review and validation for this reference.
