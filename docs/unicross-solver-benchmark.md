# UniCross: cross-skill contact diagnostics for DexLab

[简体中文](unicross-solver-benchmark.zh-CN.md)

**Status: research proposal only.** No UniCross reproduction, policy execution, or cross-engine measurement is claimed.

## Reference and relevance

- [UniCross project](https://zdchan.github.io/UniCross/) studies unified dexterous manipulation across grasping, relocation, in-hand rotation and translation.
- DexLab already studies contact/friction, grasp retention, parameter sensitivity and solver qualification. The opportunity is to link isolated diagnostic cases into **contact-mode transitions across sequential skills**, not to treat a policy success score as a physics ground truth.
- Existing [dexterity roadmap](dexterity-roadmap.md) already plans multifinger rotation (#48). This proposal complements rather than replaces it.

## Research questions

1. Which contact mechanisms fail first when a grasp transitions into relocation, rotation or translation?
2. Can an independently scored failure be localized to collision geometry, contact creation, friction/slip, constraint convergence, timestep, actuator execution or policy mismatch?
3. Under what *specified* objects, loads, contact regimes and compute budgets does each qualified solver profile remain reliable?

## Proposed bounded protocol (not executed)

1. **Inventory and licensing:** Verify upstream code, assets, robot models, controller/policy availability, versions and licenses before reuse. If unavailable, implement a minimal original task contract without claiming UniCross reproduction.
2. **Freeze cases:** Begin with grasp/hold and a controlled in-hand rotation/contact-switching probe; add translation and relocation only after independent acceptance. Freeze geometry, mass/inertia, initial conditions, command trajectories, timestep/budgets, evaluation windows and failure criteria before runs.
3. **Physics-level probes:** Replay fixed *commands*, not injected states, where supported. Measure object pose, first slip/loss time, contact persistence, normal/tangential forces or impulses with epochs, penetration, residuals where observable, sensitivity to timestep/tolerance, and runtime cost. Explicitly mark missing observables.
4. **Task-level evaluation:** Separately score task completion, drops, unintended motion and recovery; distinguish fixed-controller transfer from retrained-policy results. Never attribute differences to solver alone without auditing drives, interfaces and material/contact semantics.
5. **Coverage and evidence:** Follow [research focus](research-focus.md), [task coverage](task-coverage.md) and [AGENTS](../AGENTS.md). Freeze the applicable six-engine/profile matrix, classify every cell as passed/failed/blocked/unsupported/not-run, preserve failures and provenance, and reuse verified historical evidence without relabeling it as new.
6. **Diagnosis output:** For each failure, report first divergent event, alternative hypotheses, single-factor ablations, confidence/unknowns, and conditional solver-selection guidance. Analytical checks and numerical self-convergence are not real-world validation; hardware accuracy remains unverified without matched measurements.

## Suggested deliverables

- Versioned, engine-neutral task/phase specification and two minimal contact probes.
- Independent scorer and raw traces, including negative controls and explicit unavailable signals.
- A case-to-mechanism diagnostic table and conditional solver-selection notes, with failures and costs.
- A follow-up decision on whether broader UniCross skill composition offers information beyond existing #48 coverage.

## Non-goals

No leaderboard, claims of general engine superiority, policy training, hardware calibration, or unsupported upstream reproduction. No implementation or measurements are included in this document.
