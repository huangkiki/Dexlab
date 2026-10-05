# Results and failures

## Current development evidence

The newest records answer narrower questions than the historical robustness cohorts below. They use official MuJoCo 3.14.0 and SuperDex 1.0.0 FP64 where applicable; a release regression pass does not requalify an older benchmark.

| Question | Observed result | Interpretation |
|---|---|---|
| Can the repaired cloth case complete pinch, lift and release? | One 9 s development case passes; maximum strain 3.5161%, self penetration 1.492 mm against a 1.5 mm limit | A working candidate with only 7.95 µm penetration margin; robustness remains untested |
| Do equal nominal friction coefficients give equal low-speed response? | All 16 development runs meet their fixed physical criteria; forward 1–10 mm/s median resisting ratios: MuJoCo 0.15641, SuperDex 0.02076 | Different effective response, not an engine-accuracy ranking or measured material fit |
| Has physical hardware accuracy been established? | No measured calibration dataset | The acquisition protocol is ready; hardware validation is not complete |

[Cloth metrics, continuous close-up, parameters and failed controls](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SETTLING.md) · [Friction curves, all 16 cases, frozen configuration and raw archive](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/FRICTION_RESPONSE.md) · [Hardware protocol](https://github.com/huangkiki/Dexlab/blob/main/docs/hardware/README.md)

The cloth maxima scan all 72,000 physics steps; force observations are 100 Hz and geometry checks cover 225 saved frames at 25 Hz. Zero sampled table/robot/floor crossings does not prove continuous finite-thickness separation. The friction ratio uses center-of-mass velocity and net contact force, excluding near-rest and direction-reversal intervals: it is not material-point slip. Bin medians do not match individual speeds across engines. Different settled heights are retained in the report.

![Current cloth strain and contact-force history](../../../demos/cloth-folding/media/compliance-diagnostic.svg)

Cloth plots sample at 100 Hz; the acceptance extrema use every physics step. The plotted strain peak is 3.0891%, not the 3.5161% per-step maximum.

![All-case friction response and velocity errors](../../../demos/contact-benchmark/media/friction-response-v1.png)

The friction figure includes all 16 development outcomes; empty speed bins are missing coverage, not zero resistance. The linked reports contain exact source/configuration hashes and failed development controls.

### Cost and reproducibility

Cloth simulation-loop wall time was 618.86 s and service wall time 642.18 s, including preparation and recording. The friction report separates preparation and stepping-plus-observation time. Neither isolates native stepping, renderer, evaluator and transport costs under a shared speed benchmark; unmeasured components remain unknown. Replaying saved states or rescoring an archive does not rerun dynamics. Follow each linked report's exact configuration and version rather than replacing the historical runtime silently.

## How to read a pass

Task completion, physical validity and temporal coverage are distinct. An object reaching its target or a robot becoming still is not proof of sustained frictional support or nonpenetration. Following the [ManiSkill source review](research-ledger.md), report all three, and keep unsupported or incomplete checks visible.

The friction fixture has no learned controller: one prescribed initial velocity follows native settling, then the body evolves freely. Its eight declared cases vary direction, initial speed, mass, friction and timestep; these are development controls, not held-out object splits. All 16 outcomes are included. The apple cohort below freezes ten perturbations of the same apple asset, not ten unseen object geometries. The cloth candidate uses known-state IK and an explicit pinch prior; its failed development controls remain in the linked report. Actual initial states, native versions, solver settings, precision and source hashes are recorded with each raw record. The version inventory records when releases were checked; it is not a guarantee that those versions remain latest forever.

## Historical evidence

The following records retain their original versions and protocols. **They do not rank physical accuracy.**


## Apple grasp: fixed-configuration robustness

Ten frozen scenes vary mass, horizontal position and orientation: twenty runs across two backends, without retuning for these cases.

| Historical configuration | Complete acceptance | 95% Wilson interval |
|---|---:|---:|
| MuJoCo 3.11.0, 0.5 ms | 1 / 10 | 1.8–40.4% |
| SuperDex 1.0.0 FP64, 2 ms | 10 / 10 | 72.2–100% |

![Per-case contact overlap and wrist-relative displacement](../../evidence/apple-metrics.svg)

Crosses denote full-protocol failure. Native contact overlap is not independent surface penetration; wrist-relative displacement is not material-point slip. Timesteps, friction and drives differ, without matched calibration or tuning budgets. PhysX's default development case is separate from these twenty runs.

## Cloth: retain and explain failure

The original nine-second trajectory has cloth-triangle/table intersection in 176 of 225 saved frames, with maximum interior depth 3.00 mm. Correcting the missed detection does not repair the trajectory. The diagnostic checks zero-thickness triangles, not continuous finite-thickness separation.

[Geometry, plots and score comparison](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SCORING.md) · [Physics repair #32](https://github.com/huangkiki/Dexlab/issues/32)

## Historical cohorts

![Outcome distribution for seven cohorts](../../evidence/outcomes.svg)

Each row has a different task and protocol. Retain failure, geometry review and unsupported outcomes; do not pool denominators into a global success rate or relabel development data as independent tests.

{download}`Per-case JSON <../../evidence/historical-v1.json>` · {download}`Metrics CSV <../../evidence/metrics.csv>` · {download}`Plot provenance <../../evidence/plot-provenance.json>`

## Missing evidence

- No formal hardware calibration set or independent measured accuracy.
- Historical timings do not share an isolated protocol; no speed ranking.
- Persistent material-point correspondences are unavailable; slip is unknown, not zero.
- MuJoCo 3.14.0 has the explicitly scoped development and regression evidence above. Genesis task qualification remains pending; none of these results establishes all-engine or all-task qualification.
