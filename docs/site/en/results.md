# Results and failures

These are retained historical records under their original versions and protocols, not comparisons of newly upgraded engines. **They do not rank physical accuracy.**

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
- New stable releases and Genesis have not passed new task qualification.
