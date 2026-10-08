# Analytical incline findings

[简体中文](incline-friction-results.zh-CN.md) · [Preregistered protocol](incline-friction-protocol.md) · [All metrics and hashes](evidence/incline-friction/results.json)

All18 frozen cases ran using official MuJoCo3.15.0. Nine meet the joint engineering tolerances; nine fail. These counts describe a deterministic matrix, not a statistical success rate or engine ranking. Raw numerical consistency and agreement with the ideal physical response are separate checks.

## What the experiment establishes

At15° and μ0.5, the block is statically admissible under the declared ideal Coulomb model. With constant contact impedance0.9, two-second drift is1.336/1.313/1.301mm as the time step decreases2/1/0.5ms. All three exceed the frozen1mm bound. At impedance0.99 the respective drifts are0.179/0.154/0.141mm and pass. Fixed-parameter timestep refinement does not remove the observed static drift. The matched impedance change has a larger effect here. This is evidence for contact-parameter sensitivity in this model, not calibration of a real surface.

Requested-zero-friction cases all pass the chosen tolerances. Native contact readback is μ=1e−5, even though compiled geom friction is zero. The observed acceleration deficit9.476e−5m/s² agrees with μg cos15° for that floor. Thus this result must not be advertised as exact zero-friction dynamics or a pure time-integration error.

All six35° sliding cases fail the nonrotating, continuously supported reference assumptions. They lose contact for72.8–75.6% of sampled solve epochs; orientation excursions range0.113–3.141rad. The first contact-free epoch occurs9–24ms after initialization, before the0.5s scoring window. A fitted acceleration close to the ideal prediction is insufficient: the contact-force response and motion assumptions fail. These traces establish a failure of this specified free-box setup to realize steady ideal sliding. They do not isolate the cause or demonstrate that every sliding model in MuJoCo fails. No controller, constraint, revised softness or threshold was introduced to conceal it.

![Error and cost curves](evidence/incline-friction/error-cost.png)

## Complete matrix

Travel in moving cases is not static creep; acceleration errors for cases violating the assumptions are diagnostic only. Contact loss is measured over the whole run. Detailed scoring-window force errors, initial-rest trajectory errors, timings and independent checks are in the JSON.

| Case | drift / travel (mm) | acceleration error (m/s²) | rotation (rad) | contact loss | joint pass |
|---|---:|---:|---:|---:|---|
| static-d0.9-h0.002 | 1.3360 | 2.62941e-12 | 0.00127253 | 0.00% | False |
| static-d0.9-h0.001 | 1.3125 | 1.11739e-12 | 0.00127253 | 0.00% | False |
| static-d0.9-h0.0005 | 1.3008 | 6.5559e-13 | 0.00127253 | 0.00% | False |
| static-d0.99-h0.002 | 0.1793 | 1.11795e-13 | 0.000126981 | 0.00% | True |
| static-d0.99-h0.001 | 0.1541 | 3.42595e-14 | 0.000126981 | 0.00% | True |
| static-d0.99-h0.0005 | 0.1415 | 1.48528e-14 | 0.000126981 | 0.00% | True |
| sliding-d0.9-h0.002 | 3219.5391 | 0.0123525 | 3.13036 | 72.80% | False |
| sliding-d0.9-h0.001 | 3218.0635 | 0.000904311 | 0.168716 | 74.15% | False |
| sliding-d0.9-h0.0005 | 3206.5829 | 0.0227201 | 1.20449 | 73.28% | False |
| sliding-d0.99-h0.002 | 3218.4667 | 0.0179469 | 3.13789 | 75.60% | False |
| sliding-d0.99-h0.001 | 3209.0721 | 0.0106093 | 3.14074 | 73.10% | False |
| sliding-d0.99-h0.0005 | 3217.0765 | 0.00497492 | 0.112732 | 73.32% | False |
| frictionless-d0.9-h0.002 | 5082.9180 | 9.47573e-05 | 1.03238e-07 | 0.00% | True |
| frictionless-d0.9-h0.001 | 5080.3791 | 9.47573e-05 | 1.07454e-07 | 0.00% | True |
| frictionless-d0.9-h0.0005 | 5079.1096 | 9.47573e-05 | 1.03238e-07 | 0.00% | True |
| frictionless-d0.99-h0.002 | 5082.9180 | 9.47573e-05 | 4.21468e-08 | 0.00% | True |
| frictionless-d0.99-h0.001 | 5080.3791 | 9.47573e-05 | 8.9407e-08 | 0.00% | True |
| frictionless-d0.99-h0.0005 | 5079.1096 | 9.47573e-05 | 5.16191e-08 | 0.00% | True |

## Reproduction and costs

After installing the qualified official runtime, run inside the repository's admitted cgroup/research window:

```bash
python -m dexlab.incline_run --manifest docs/evidence/incline-friction/manifest.json --output /data/new-incline-run
python -m dexlab.incline_score --input /data/new-incline-run --output /data/new-incline-report.json
```

The scorer checks artifact hashes, compiled configuration, trace structure, initial state, native friction, timing and discrete impulse/position consistency. Synthetic negatives cover state injection, force/time corruption and missing support. This is source-backed provenance, not a cryptographic proof against fabricated observations.

The native campaign took0.806s inside a1.373s bounded service; summed native stepping was0.101s for42,000 steps. Record these as one short Intel Core i9-14900K CPU measurement with substantial overhead/noise, not a throughput ranking. Per-case setup, observation and total time are retained; no rendering or transfer ran during stepping. Setup of the isolated environment separately took61.474s. A16GiB cgroup,2CPU quota,128tasks,swap0 and1800s ceiling were verified by the existing launcher. Source hashes identify the runner used before later scorer fixes.

The first summary failed JSON serialization; the second incorrectly classified observed loss of support as corrupt evidence. Both processing failures were retained and corrected; the physical campaign was not rerun, and no numerical tolerance changed. Loss of support now remains an explicit failed reference condition. All18 raw traces remain available for rescoring.

## Connection to grasping and next work

This benchmark directly shows why a friction coefficient alone is insufficient to specify numerical contact behavior. Static creep and actual contact continuity matter when interpreting grasp retention. It does not establish the accuracy of any particular real material or the full grasp controller. Further work: diagnose the sliding contact lifecycle without changing this frozen result; then add a separately preregistered centered1D collision and restitution/conservation evaluation. Hardware comparison remains a distinct future layer, not a prerequisite for these analytical evaluations.

[Raw18-case archive](https://github.com/huangkiki/Dexlab/releases/download/v0.43.0/incline-friction-raw-v1.zip) · [SHA256 and offline-read verification](evidence/incline-friction/archive.json). The archive includes the original runner and the independently revised scorer.
