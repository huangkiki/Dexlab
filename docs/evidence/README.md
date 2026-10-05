# Historical rescoring: metrics and evidence boundaries (D03)

[English](README.md) | [简体中文](README.zh-CN.md)

**Conclusion: 208 records from seven frozen cohorts are read again with current scorers. The old robot-cloth pass requires geometry review. Other cohort outcomes are below. This is neither measured accuracy nor an equal-budget engine ranking.**

This is offline historical rescoring, not a new dynamics experiment; release validation is recorded in [GitHub Releases](https://github.com/huangkiki/Dexlab/releases). Controllers, engines and physical limits are unchanged. Every declared raw input is hash-checked before and after analysis.

## Results and conclusions

![Cohort outcomes](outcomes.svg)

| Cohort | N | Historical passes | Current protocol passes | Protocol failures | Geometry review | Unsupported | Timeout / runtime failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Apple grasp regression | 20 | 11 | 11 | 9 | 0 | 0 | 0 / 0 |
| Nominal cloth held-out | 105 | 52 | 52 | 53 | 0 | 0 | 0 / 0 |
| PhysX cloth held-out | 15 | 10 | 10 | 1 | 0 | 4 | 0 / 0 |
| Contact development | 38 | 25 | 25 | 13 | 0 | 0 | 0 / 0 |
| Static response development | 17 | 11 | 11 | 6 | 0 | 0 | 0 / 0 |
| Transient response development | 12 | 6 | 6 | 6 | 0 | 0 | 0 / 0 |
| Robot cloth diagnostic | 1 | 1 | 0 | 0 | 1 | 0 | 0 / 0 |

Denominators belong to different tasks and development stages: do not pool them into an overall success rate. Contact/static/transient cohorts are development configurations, not random trials. Four unsupported PhysX force-driven cloth cases remain in the full denominator. The unfinished 100-scenario apple evaluation is not merged into this 20-run regression.

The selection comprises complete, predeclared published cohorts, not every historical run. The contact release also retains three initialization failures; other early development, qualification and refinement records remain in their original reports and are not rescored in this table.

![Per-scenario grasp metrics](apple-metrics.svg)

Apple curves use separately fixed parameters. Native overlap and wrist-relative translation have separate panels; 1 mm / 2 mm dashed lines are unchanged limits and crosses mark full-protocol failures. Very small displacement can occur when the apple was never lifted: clearance and support checks still apply. Native overlap depends on each contact algorithm and is not a common-surface accuracy ranking. Accumulated material-point slip is unavailable for every record.

Robot cloth: 176 of 225 saved 25 Hz frames intersect the table, with 3.00 mm maximum interior depth. Passing the old protocol does not remove this geometry problem. This zero-thickness-triangle diagnostic against a 6 mm table is distinct from native SDF distance and vertical penetration. Physical repair is tracked in [#32](https://github.com/huangkiki/Dexlab/issues/32).

## Measurement contract

Each row contains frozen cohort/record IDs, historical/current outcomes, failed checks, raw-file SHA-256 hashes, current scorer SHA-256 hashes and sampling coverage. Values use SI; plots explicitly convert metres to millimetres. Definitions and approximations are below and in [metrics.json](metrics.json). Unobserved quantities are null, never zero-filled or interpolated across gaps. Absent obstacles or pinned boundaries are not_applicable, not observed zero.

| Metric ID | Unit | Definition and boundary |
|---|---|---|
| `apple.native_depth` | m | max native recorded overlap over apple/right-hand contact points; backend-specific contact construction. Native contacts and SDF discretization; not a common reference-surface distance |
| `apple.wrist_translation` | m | max norm of wrist-frame apple position minus first held position. Object pose drift; no persistent contact-material correspondence |
| `apple.wrist_rotation` | rad | max relative orientation geodesic angle from first held pose. Object rotation; distinct from translation and rolling/sliding classification |
| `apple.clearance` | m | minimum recorded apple lowest-point height above tabletop. Uses the recorded geometry-based clearance approximation |
| `apple.support` | 1 | mean total hand contact force z / (mass*9.81). Net measured hand force, not commanded force or per-contact normal load |
| `apple.momentum` | 1 | max norm(total force - gravity - mass*delta_velocity/dt) / weight. Step-end force/velocity epoch in the frozen native log; not energy conservation |
| `cloth.ground_depth` | m | max(0, collision_radius - minimum vertex z). Plane reference; prescribed collision radius, not measured cloth thickness |
| `cloth.sphere_depth` | m | max(0, sphere_radius + collision_radius - closest triangle-interior distance). Triangle interiors and declared sphere, not native contact depth |
| `cloth.edge_strain` | 1 | max absolute(edge_length/rest_length - 1). Edge strain only; not continuum stress or material calibration |
| `cloth.pin_error` | m | max pinned-vertex displacement from rest. Prescribed boundary condition; not robot grasp quality |
| `cloth.final_tip_sag` | m | mean(rest_z - final_z) over declared tip vertices. Signed displacement; positive downwards; not measured material error |
| `cloth.crossing_pairs` | count | maximum intersecting nonadjacent triangle pairs across audited frames. Shared-vertex pairs excluded; no thickness overlap or continuous-time guarantee |
| `robot_cloth.table_depth` | m | max interior depth over zero-thickness triangle interiors in table box union. LP diagnostic; capped by half 6mm table thickness, not vertical/native penetration; no new pass threshold |
| `robot_cloth.intrusion_frames` | count | number of frames with interior depth > numerical zero 1e-8 m. Observed frame count, not continuous duration or a new physical tolerance |
| `robot_cloth.anchor_error` | m | max norm of selected material-point position minus kinematic anchor. Includes normal separation, deformation and tangential motion; not accumulated slip |
| `robot_cloth.lift` | m | maximum selected material-point z minus planned material-point initial z. One selected material point, not minimum whole-cloth clearance |
| `plane.box_depth` | m | max(0, -minimum transformed box-corner z). Analytical box-plane geometry; separate from native soft-contact distance |
| `cylinder.sat_depth` | m | max SAT overlap of cylinder prism against either pad box. Declared polygonal prism, not ideal cylinder; sections/faceting remain in receipt |
| `contact.momentum` | 1 | max norm(mass*delta_velocity/dt - contact - external + gravity) / weight. Net native force on tested body at declared step epoch, not contact command |
| `normal.static_error` | 1 | max abs(mean indentation - load/20000) / (load/20000). Synthetic 20 kN/m target; 2/6 N fit and 4 N validation; not hardware accuracy |
| `normal.plateau_std` | m | maximum population standard deviation among 2,4,6 N plateaus. Mean removed only; slow drift remains; not detrended jitter |
| `normal.transient_rms` | m | maximum per-window RMS error against m*xdd+40*xd+20000*x=load. Exact underdamped synthetic response; no offset/time fit; excludes detachment |
| `normal.transient_peak` | m | maximum absolute error across the three transient windows. Same synthetic reference as transient_rms; not fitted material dynamics |
| `material_slip` | m | cumulative relative tangential material displacement would be required. No persistent material-pair record exists; value must be null, never zero |

Coverage: apple states are recorded every physics step, with hold [11,14) s; basic cloth/contact include the unstepped initial state. Robot-cloth surface diagnostics cover 25 Hz only; hold checks use the 100 Hz trace in [2,hold_end) s. Cloth self-crossings retain their actual sampled surface_coverage, without continuous-time collision claims. Forces are native world-frame resultants on the tested body aligned with the corresponding velocity increment; drive targets are not measured force.

Evidence errors are separate from physical failures: missing files, hash changes, duplicate/truncated times and contradictory checks abort report generation rather than shrink the denominator or become physical failures. Complete runs with native warnings or retention/stability failures remain protocol failures. Unsupported operations, timeouts and runtime errors retain separate states.

## Two evaluation tracks

| Track | Current status |
|---|---|
| Error against measured physical references | Unavailable: no measured forces, material responses or hardware trajectories. 20 kN/m + 40 N·s/m is a synthetic engineering target. |
| Task performance after equal-budget tuning | Historical tuning budgets are unmatched. Only fixed-profile protocol outcomes are reported. |

No speed ranking is exported. Preparation, physics stepping, control/recording, rendering and archival require separate timing; historical runs lack uniform isolation. Full energy accounting, material slip, real friction and drive identification remain unsupported by these records.

## Data, code and reproduction

[All rows and per-file hashes](historical-v1.json) · [Tidy metric CSV](metrics.csv) · [Frozen cohort selection](cohorts.json) · [Offline scorer](../../src/dexlab/evidence_report.py) · [Plot generator](../../scripts/render_evidence_report.py)

The two completed public cohorts use explicit metadata projections and the frozen historical scorer; all 106 records reproduce exactly. See [portable reproduction](PUBLIC-ARCHIVE.md) for layout, transformations and limits. The immutable historical report retains its original availability snapshot; this table gives current download locations.

| Cohort | Complete raw records |
|---|---|
| Apple grasp regression | [Release archive](https://github.com/huangkiki/Dexlab/releases/download/v0.13.0/v0.13.0-grasp-regression-evidence.tar.gz) |
| Nominal cloth held-out | [Release archive](https://github.com/huangkiki/Dexlab/releases/download/v0.19.1/dexlab-historical-evidence-v1.tar.gz) |
| PhysX cloth held-out | [Release archive](https://github.com/huangkiki/Dexlab/releases/download/v0.11.0/v0.11.0-physx-cloth-evidence.tar.gz) |
| Contact development | [Release archive](https://github.com/huangkiki/Dexlab/releases/download/v0.12.0/v0.12.0-contact-development-evidence.tar.gz) |
| Static response development | [Release archive](https://github.com/huangkiki/Dexlab/releases/download/v0.13.0/v0.13.0-normal-response-evidence.tar.gz) |
| Transient response development | [Release archive](https://github.com/huangkiki/Dexlab/releases/download/v0.14.0/v0.14.0-transient-response-evidence.tar.gz) |
| Robot cloth diagnostic | [Release archive](https://github.com/huangkiki/Dexlab/releases/download/v0.19.1/dexlab-historical-evidence-v1.tar.gz) |

For the two public projected cohorts, use the bundled standalone reproducer above. Its copied receipts bind public hashes; the original tracked receipts deliberately retain private-original hashes and cannot validate a mixture of projected and original files. The other five archives retain their original receipt/scorer provenance. The following command regenerates plots from the immutable 208-record report; it does not rescore raw data.

```bash
.venv/bin/python scripts/render_evidence_report.py docs/evidence/historical-v1.json --output /tmp/evidence-report
```

The developer-facing `dexlab.evidence_report` tool requires unredacted original inputs and a compatible recorded-model runtime. Current scorers may require evidence absent from old recordings; use the pinned bundled sources to reproduce published historical values. Missing evidence remains missing. Plotting additionally requires matplotlib.

Rescoring loads saved MuJoCo models for geometry/FK analysis but never integrates dynamics. Scorer identity is bound to source-file hashes, not just a package version. Generating plots does not establish release-gate completion.

[Task and parameter provenance](../inventory/README.md) · [Research methods](../research-focus.md) · [Homepage](../../README.en.md)
