---
html_theme.sidebar_secondary.remove: true
html_theme.sidebar_primary.remove: true
---

<div class="research-eyebrow">DEXLAB / PHYSICS EVALUATION NOTES</div>

# How does contact shape grasping?

<div class="research-deck">Start with physics. Test the explanation.</div>

Reproducible contact and friction experiments grounded in established physical laws and empirical relations. Findings come first; models, solvers, raw records and their limits follow.

<div class="research-links"><a href="#comparison">Read the comparison ↗</a><a href="#coverage">Six-engine coverage</a><a href="https://github.com/huangkiki/Dexlab/releases">Code & data ↗</a></div>

<div class="research-meta">Evidence release v0.46.0 · Analytical verification / fixed cases · Full-engine matrix incomplete</div>

## Three findings to start with

::::{grid} 1 1 3 3
:gutter: 3
:::{grid-item-card} 01 / Contact settings change drift
:class-card: research-finding
**Engine names do not predict the outcome.** SuperDex satisfies more checks in the fixed incline comparison; a historical higher-impedance MuJoCo profile has less static drift.

[Parameters and counterexample](#comparison)
:::
:::{grid-item-card} 02 / Correct endpoints can hide errors
:class-card: research-finding
**24/27 endpoint passes; 2/27 also meet the overlap budget.** Collision velocity, energy and overlap must be checked separately.

[Collision evidence](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-stiffness-results.md)
:::
:::{grid-item-card} 03 / Smaller residuals do not ensure a hold
:class-card: research-finding
**The cube still slips about 2 mm after tightening tolerances.** Numerical consistency and grasp retention are different outcomes.

[Pinch evidence](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-impulse-results.md)
:::
::::

(comparison)=
## One cube. Two fixed profiles.

40 mm · 64 g · matched initial state and gravity · 2 / 1 / 0.5 ms timesteps · 2 seconds per case. Verified MuJoCo records are reused; nine SuperDex cases are new. **An interim paired comparison, not a six-engine ranking.**

| Case and observation | MuJoCo 3.15.0 | SuperDex 1.0.0 FP64 |
|---|---|---|
| 15° static friction, μ=0.5 · displacement | **1.301–1.336 mm** · 0/3 pass | **0.708–1.132 mm** · 2/3 pass |
| 35° sliding, μ=0.5 · support and motion | Rotation, intermittent support loss · 0/3 | Stable sliding in scoring window · 3/3 |
| 15° nominal zero friction · velocity RMSE | **8.21×10⁻⁵ m/s** · 3/3 | **8.04×10⁻¹²–1.52×10⁻¹⁰ m/s** · 3/3 |

<div class="research-caution"><strong>Counterexamples belong in the conclusion.</strong> Historical MuJoCo impedance=0.99 drift is 0.141–0.179 mm, below this SuperDex profile. SuperDex static drift increases with timestep refinement; MuJoCo has a native friction floor. These results do not establish a universal winner.</div>

**Solver settings.** MuJoCo: Newton / Euler / elliptic, impedance=0.9, 100 iterations maximum, tolerance 1e-10. SuperDex same-byte reconstruction: Newton / AUTO (dense LDLᵀ on the small-system source path) / C1-regularized friction; historical readback: Backward Euler, 100 iterations, absolute/relative tolerance 1e-9. [Identity, combination law and historical telemetry gap #124](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-solver-audit.md). Equal μ is not material or contact-model equivalence. Velocity errors use the 0.5–2 s window; the report preserves initial transients and failures.

[Full results and raw data](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.md) · [Frozen protocol](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-protocol.md) · [Parameter manifest](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/incline-comparison/manifest.json)

(coverage)=
## Six engines. What is covered?

Matched cases and scoring are separate from having some previous experiment. The table concerns the nine incline cases above. Versions are historical evidence identities, not claims about current latest releases. Missing runs are never counted as passes.

| Engine | Recorded version / solver | Nine paired incline cases | Other evidence |
|---|---|---|---|
| MuJoCo | 3.15.0 / Newton | Executed, including failures | Collision and pinch diagnostics |
| SuperDex | 1.0.0 FP64 / [Newton reconstruction; historical telemetry limit](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-solver-audit.md) | Executed, including failures | Loading, parameter transfer |
| Genesis | 1.4.3 / Newton / approximate_implicitfast; [historical settings and readback limits](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-solver-audit.md) | Not run | [16 force-limit cases](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) |
| Newton Physics | 1.6.1, Warp 1.18.0 / XPBD | Not run | [Sphere–plane and negatives](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-contact.md) |
| PhysX | Three SDK controls read back PGS/TGS; [cohort settings and native-core identity gap #126](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md) | Not run; integration qualification incomplete | [Historical contact cases](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/README.md) |
| Drake | No accepted version / solver yet | Not run | [Integration #117](https://github.com/huangkiki/Dexlab/issues/117) |

Unresolved facts or provenance behind public findings must link to actionable Issues and take priority over capability expansion. SuperDex package identity/configuration reconstruction and Genesis historical solver enums are verified; [#124](https://github.com/huangkiki/Dexlab/issues/124) and [#125](https://github.com/huangkiki/Dexlab/issues/125) retain historical readback gaps, while PhysX has three recovered native scene-solver readbacks and [#126](https://github.com/huangkiki/Dexlab/issues/126) retains cohort core/library identities and remaining missing readbacks. Reconstruction, source inference and historical native readback are labeled separately.

[Follow-up work and blockers](https://github.com/huangkiki/Dexlab/issues) · [PhysX integration #47](https://github.com/huangkiki/Dexlab/issues/47). Frameworks and native engines are distinct; Newton Physics is not MuJoCo's Newton algorithm.

## Next: unified-drive pinch boundary

[Development roadmap](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-boundary-roadmap.md) · [Discussion](https://github.com/huangkiki/Dexlab/discussions/129) · [Research tracker](https://github.com/huangkiki/Dexlab/issues/130)

The plan is adopted; the protocol and formal campaign are not yet delivered. After public-evidence P0 work, develop the common fixture/external PD, qualify two backends, validate independent scoring, then acquire 594 formal episodes plus 24 controls. Retain six-engine gaps and the scope of historical evidence.

## How we check

1. **Define the reference first.** Static friction |f| ≤ μₛN, threshold tanθ=μₛ, sliding acceleration a=g(sinθ−μₖcosθ). Declare rigid-body/Coulomb assumptions, initial conditions and applicability before comparison.
2. **Freeze cases and expose differences.** Match mass, inertia, geometry, frames, controls and initial state; record engine/solver versions, precision, timestep, budgets and contact parameters.
3. **Retain failures and test sensitivity.** Report absolute errors, trajectories, convergence/sensitivity and cost. Support loss, rotation and unobservable parameters do not disappear into averages.
4. **Keep evidence levels separate.** Analytical verification, sourced empirical references and real-system validation are different. The first two can proceed independently but do not replace measured calibration of a specific material.

## From contact experiments to grasping

![Native Genesis pinch, lift and release replay](../../../demos/contact-benchmark/media/genesis-pinch.gif)

Continuous replay of native Genesis states, displayed by MuJoCo. In16 fixed cases, 0.2/0.4 N force caps cannot retain the object; 0.8/10 N hold and release, including ±2 mm initial offsets. This is a fixture-specific result, not a cross-engine grasp ranking.

[Force-limit report](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) · [All research results](results.md) · [Installation and reproduction](quickstart.md)

<div class="research-footer">Organization informed by <a href="https://mandarobotics.com/blog/comparing-physics-engines/index.html">Manda Robotics' engine comparison</a>: findings first, case-by-case evidence and disclosed differences. All numbers here come from published DexLab evidence.</div>

```{toctree}
:hidden:
:maxdepth: 1

Quickstart <quickstart>
Experiments <experiments>
Research results <results>
Engines and models <engines>
Dexterity roadmap <dexterity>
Research ledger <research-ledger>
Benchmark <benchmark>
Contributing <contributing>
```
