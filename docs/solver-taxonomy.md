# Read configurations by role, not as a solver leaderboard

[English](solver-taxonomy.md) | [简体中文](solver-taxonomy.zh-CN.md)

The comparison unit is a versioned **core + runtime path + physical model + numerical configuration**, not a bare algorithm name. The homepage uses [an explicit engine-specific display vocabulary](solver-taxonomy.json); the historical coverage inventory, observations, counts and verdicts are unchanged. This vocabulary classifies recorded names, not unobserved execution branches.

## What the names mean here

| Recorded example | Roles and limits |
| --- | --- |
| MuJoCo `PGS`, `CG`, `Newton` | Alternative methods for its constraint problem. Here CG is nonlinear conjugate gradient. Primal/dual formulation and friction-cone compatibility still matter; a shared role does not prove identical work or convergence. |
| SuperDex `Newton / GMRES` | Outer nonlinear method / inner linear-system method. `CG`, `GMRES`, `LDLT` and the other recorded linear selections are not peers of the outer Newton method. `AUTO` specifies branch selection, not proof of an executed LDLT branch. |
| SuperDex `BFGS / SR1` | Recorded outer-method selections. At the tested assembly period of one the existing report identifies Newton-equivalent steps; do not count them as two additional demonstrated algorithms. |
| Genesis `Newton / elliptic / signorini` | Constraint method / friction cone / contact-model selection. `PBD / rigid coupling` describes a separate deformable implementation and coupling path. |
| Newton Physics `Kamino / PADMM`, `Kamino / DVI` | System implementation / dynamics backend. XPBD, VBD and Featherstone labels identify native implementations whose actual equations and applicable objects must be checked per path. Style3D and ImplicitMPM are not generic linear subsolvers. |
| PhysX `PGS / patch friction` | Constraint method / friction model. `surface cloth` identifies a deformable path, not an alternative rigid constraint method. |
| Drake `SAP / kLagged / hydroelastic` | Constraint method / discrete contact approximation / contact model. Point versus hydroelastic and kLagged/kSimilar/kSap must not be flattened into independent algorithms. |

Read the frozen implementation evidence: [MuJoCo](mujoco-incline-results.md), [SuperDex](superdex-incline-results.md), [Genesis](genesis-incline-results.md), [Newton Physics](newton-incline-results.md), [PhysX](physx-incline-results.md), [Drake](drake-contact-paths-results.md). Primary terminology references include the [MuJoCo solver documentation](https://mujoco.readthedocs.io/en/stable/computation/index.html#solvers) and [Kamino's documented dynamics backends](https://newton-physics.github.io/newton/1.6.0/api/_generated/newton.solvers.SolverKamino.html). These references do not overwrite the runtime identities of historical records.

A summary collects names used by different profiles; it does **not** assert that every displayed combination is supported or tested. Unknown names remain visibly unresolved. Integrator, precision, iteration/update options and framework paths remain distinct. Native contact geometry is not the visible mesh; same-name settings or equal iteration counts are not matched models or compute budgets.

## Two different comparisons

**Scenario selection:** compare complete candidate profiles under declared physical references, finite development budgets and new frozen validation conditions. Report error, stability and measured cost, including failures and unsupported observables.

**Algorithm attribution:** hold the declared mathematical/physical problem and relevant interfaces fixed, vary the selected method, and test competing explanations. Changing geometry, contact law, controller, precision and solver together cannot isolate one algorithm's contribution.

The [SDF follow-up #178](https://github.com/huangkiki/Dexlab/issues/178) qualifies effective fine-feature geometry and contact response. Existing depth/spacing disclosure and a successful thin-stem scene do not establish equivalence. The [cloth follow-up #179](https://github.com/huangkiki/Dexlab/issues/179) separates material response, discretization, collision/coupling and grasp control. It preserves the narrow #32 repair and #77 negative evidence instead of declaring either universal success or universal failure.

## Read evidence on separate axes

Keep record integrity, numerical consistency, physical-reference validity/error, task outcome and attribution confidence separate. An invalid observation does not prove task impossibility; task success does not prove material fidelity. Historical scores, failure denominators and thresholds stay immutable. Any new precision protocol needs a sourced error argument, prospective freeze and new validation; changing epsilon after seeing failures is not validation.

For unavailable or unpublished implementations, identify whether a statement is an author description, public documentation, source inference, configured value or runtime observation. Do not invent source access, native readbacks, licenses, hidden SDF grids or historical branch telemetry. Missing evidence needs a concrete recovery condition, not a stronger adjective.

## Maintenance

Update `docs/solver-taxonomy.json` with a source-backed engine-specific role before presenting a newly understood label. Unknown labels remain visible until then. Regenerate both READMEs and site homepages with `scripts/build_visual_research.py`; run the focused taxonomy tests and the existing full applicable submission gate. The display vocabulary never grants qualification or changes task coverage. [Current work](current-work.md) keeps priorities and the pause state in one place.

## Learning route

**Learn before reading the configuration table:** [Sim Learning](https://github.com/huangkiki/sim-learning) provides Chinese lessons, English terminology and native engine courses. Start with the [Physics-Based Simulation study route](https://github.com/huangkiki/sim-learning/blob/main/docs/physics-based-simulation.md#english-reading-guide), then the [solver guide](https://github.com/huangkiki/sim-learning/tree/main/docs/solver-guide). Course source checks remain separate from DexLab experimental qualification.
