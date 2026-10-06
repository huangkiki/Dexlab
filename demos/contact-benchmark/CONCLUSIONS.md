# Contact diagnosis: conclusions and acceptance gaps

[English](CONCLUSIONS.md) | [简体中文](CONCLUSIONS.zh-CN.md)

**Static response matching does not establish a shared dynamic material.** The frozen profiles failed the declared transfer target; local identification explains some mechanisms but does not repair unloading or validate real material. Issue #10 remains open. This synthesis adds no experiment, retuning, changed threshold or new aggregate success rate.

## What question did each experiment answer?

| Question and fixed standard | Delivered result | Interpretation and boundary |
|---|---|---|
| Does cylinder surface refinement remove the observed contact failure with commands, mass, timestep and thresholds fixed? | SuperDex 256→1,024→4,096 triangles: overload penetration 2.267→0.858→0.481 mm; the intermediate case still fails; four finest-surface controls pass. | A controlled repair for this fixture, not a universal engine fix. [Development](README.md) |
| Do nominal profiles retain the synthetic K=20,000 N/m, D=40 N·s/m target across mass/size? | All 30 prospective paired cases fail the combined target; one passes the separate engineering checks. | Fixed-map transfer failed. This is not a comparison to measured material or proof of engine error. [Transfer](TRANSFER.md) |
| Can one fixed SuperDex coefficient produce constant tangent D=40 across 2,4,6 N? | Tight-tolerance native identification has nine valid records and approximately 20/40/60 N·s/m. Default-tolerance records fail the force/momentum gate. | Supports local load dependence under the declared assumptions. A single-load match does not calibrate the entire range. [Native tangent](TANGENT_IDENTIFICATION.md), [conditional derivation](DAMPING_REFERENCE.md) |
| Does an excellent MuJoCo force fit imply a valid measurement? | Low impedance:9/9 valid; high impedance:0/9 valid because the frozen settling checks fail. | Invalid fits remain invalid. Pre-step applied-load identification is local; the basic low-impedance model also passes the declared prediction tolerance. [Feedthrough](FEEDTHROUGH.md) |
| Is smaller timestep automatically an acceptable repair? | Response–cost study:9/27 combined passes,18 failures across three profiles, three steps and three repeats. | Cost is conditional on quality. Repeats are not independent held-out scenarios; historical runtime versions remain historical. [Response–cost](RESPONSE_COST.md) |

Counts have different denominators and criteria. Do not pool them into an engine leaderboard. Each linked report retains versions, frozen inputs, raw archives, independent scoring, figures and failures. Published scores remain attached to their original runtime; this documentation update does not rerun those cohorts on a newer version.

![Paired transfer discrepancy, including all failures](../../docs/evidence/contact-transfer-v1.png)

## Standard and evidence, not success-video selection

The transfer reference is explicitly synthetic, not measured truth. Its transient criteria use the first50 ms of each positive-load window: RMS below10 µm and peak discrepancy below25 µm, with no time/position fitting; independent engineering and unloading checks remain required. See [transient protocol](TRANSIENT_RESPONSE.md) for the complete score. A fit residual is a separate diagnostic and cannot replace these trajectory criteria.

The cylinder motion-onset detector requires downward COM speed above5 mm/s for20 ms. This is delayed motion detection, not the exact static-friction limit. Reference-surface overlap, native contact separation, wrist-relative displacement and material-point slip are distinct measurements. Missing contact observations are unknown, not zero. Complete slip accumulation is not claimed.

## Requirement-by-requirement audit

| Issue #10 requirement | Inspectable evidence | Status |
|---|---|---|
| Interpretable mechanism and controlled repair or supported negative result | Cylinder surface control, load-damping derivation/native identification, failed paired transfer | Delivered within the fixture and model assumptions above |
| Frozen physics, positive/negative outcomes, force, onset, penetration, release and cost | [Development](README.md), [unloading](DAMPING_ABLATION.md), [response–cost](RESPONSE_COST.md) | Published; measurements and historical timing limitations remain explicit |
| Independent scorer rejects adhesion and missing observations | `tests/test_contact_indent.py`, `test_contact_pinch.py`, `test_contact_plane.py`, `test_contact_tangent.py`, `test_contact_feedthrough.py` | Injected negatives exist; current release validation must report its actual test result |
| Paired scenarios, all failures, provenance and bilingual reproduction | Linked reports and immutable release raw archives; `test_contact_transfer.py` rejects missing cases/retuning | Published; report reproduction is not a new engine run |
| Later commitments: common-response calibration and unloading repair | Native local identification and ablation narrow the mechanism; transfer/unloading failures persist | **Not completed** |
| Complete internal contact-pair law and cooked geometry | [Native geometry](NATIVE_GEOMETRY.md) and contact readback distinguish submitted geometry from unexposed internals | **Unknown where public APIs do not expose it**, never an equivalence pass |

This audit is not an Issue closure declaration. The original deliverable permits a supported negative result, but later commitments must be explicitly reconciled before closure; they cannot disappear through wording. Broader frozen-condition comparison remains #3 and measured calibration remains #6. No physical-accuracy or hardware-fidelity claim follows from analytic consistency.

## Next experiment must have a stopping rule

Before another batch: state the remaining acceptance question, unchanged target, one controlled intervention, a positive/negative control, force/state sampling epochs, independent score, resource/case budget and a stopping decision for either outcome. A study that can only generate another parameter sweep is not ready. Do not rerun completed cohorts merely to accumulate releases. Success means answering the preregistered question; it does not require turning every physical failure into a pass.
