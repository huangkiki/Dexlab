# Elastic impact: accurate final velocities do not establish low penetration

[English](elastic-impact-results.md) | [简体中文](elastic-impact-results.zh-CN.md)

All18 preregistered cases pass the numerical tolerances. Maximum final-velocity absolute error is0.00160672m/s, relative kinetic-energy error0.16077%, and full-trajectory momentum error below1.12e-15kg m/s. Maximum geometric overlap spans5.0003–20.0161mm. Penetration is outside this batch’s final-state tolerances: this pass is not low-penetration grasp qualification.

[Frozen protocol](elastic-impact-protocol.md) · [#99](https://github.com/huangkiki/Dexlab/issues/99) · [Preregistration](https://github.com/huangkiki/Dexlab/issues/99#issuecomment-6047131003)

Final-velocity error decreases across the three steps in each of six conditions. This is finite-step sensitivity for this fixed configuration, not a universal convergence-order proof. Zero damping still produces small numerical energy gain; worst energy error at the finest step is about0.00935%. Transverse and spin readings are zero.

Compliant contact permits compression. The scalar approximation r̈+10000r=0 has natural frequency100s⁻¹ and overlap scale incoming relative speed/100, suggesting5/10/20mm. This interpretation agrees with observations but the full contact ODE was not independently accepted here. Reducing timestep at fixed stiffness cannot eliminate model compliance. Grasp follow-up must separately assess stiffness, overlap, peak force, impulse and cost. These results neither calibrate real restitution nor validate multiple contacts or complex shapes.

| Case | m2 (kg) | u1 (m/s) | dt (ms) | max velocity error (m/s) | energy error (%) | overlap (mm) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| impact-01 | 1 | 0.5 | 1 | 0.0003013 | 0.12058 | 5.0040 | PASS |
| impact-02 | 1 | 0.5 | 0.5 | 0.0000451 | 0.01803 | 5.0005 | PASS |
| impact-03 | 1 | 0.5 | 0.25 | 0.0000175 | 0.00701 | 5.0003 | PASS |
| impact-04 | 1 | 1 | 1 | 0.0006025 | 0.12058 | 10.0081 | PASS |
| impact-05 | 1 | 1 | 0.5 | 0.0000901 | 0.01803 | 10.0010 | PASS |
| impact-06 | 1 | 1 | 0.25 | 0.0000350 | 0.00701 | 10.0007 | PASS |
| impact-07 | 1 | 2 | 1 | 0.0012050 | 0.12058 | 20.0161 | PASS |
| impact-08 | 1 | 2 | 0.5 | 0.0001803 | 0.01803 | 20.0020 | PASS |
| impact-09 | 1 | 2 | 0.25 | 0.0000701 | 0.00701 | 20.0014 | PASS |
| impact-10 | 2 | 0.5 | 1 | 0.0004017 | 0.16077 | 5.0040 | PASS |
| impact-11 | 2 | 0.5 | 0.5 | 0.0000601 | 0.02404 | 5.0005 | PASS |
| impact-12 | 2 | 0.5 | 0.25 | 0.0000234 | 0.00935 | 5.0003 | PASS |
| impact-13 | 2 | 1 | 1 | 0.0008034 | 0.16077 | 10.0081 | PASS |
| impact-14 | 2 | 1 | 0.5 | 0.0001202 | 0.02404 | 10.0010 | PASS |
| impact-15 | 2 | 1 | 0.25 | 0.0000467 | 0.00935 | 10.0007 | PASS |
| impact-16 | 2 | 2 | 1 | 0.0016067 | 0.16077 | 20.0161 | PASS |
| impact-17 | 2 | 2 | 0.5 | 0.0002404 | 0.02404 | 20.0020 | PASS |
| impact-18 | 2 | 2 | 0.25 | 0.0000935 | 0.00935 | 20.0014 | PASS |

Local Intel Core i9-14900K, CPU FP64; no mixed remote timings, no rendering. Enforced16GiB/twoCPU/128tasks/swap0/1800s and exclusive research window. Environment setup16.252s; formal service0.896s. Eighteen-case campaign wall0.05879s: accumulated scene preparation0.01029s, native stepping0.01167s, observations0.01804s; remaining time includes compression/output. Independent scoring0.02105s, service0.385s. Observation overhead matters at this scale; no engine speed ranking. Runtime verification/imports are outside campaign timing and included in service wall; the full publication gate is separate.

Source protocol/runner/scorer commit: `3edc3eff7e0b125233fabe132fc13abddc7b5f48`. Native MuJoCo3.15.0, package record hash `a48c3263e40378576b39f2739cc8d5b151a56ffd69ca0fcc11d66b32b60668e1`. This analytical primitive is separate from whole-grasp/backend qualification.

[Machine-readable results](evidence/elastic-impact/results.json) · [Archive digest](evidence/elastic-impact/archive.json) · [Raw release asset](https://github.com/huangkiki/Dexlab/releases/download/v0.44.0/elastic-impact-raw-v1.zip). Archive 282871bytes; SHA256 `56fb67cf6ffa5cf930ae2dbe777504d2fe28c3f41d2e68e00f9490dd239a5b3c`; every entry read back. No physics rerun is needed to score:

```bash
python -m dexlab.impact_score --input extracted-archive --output rescored.json
# New, explicitly requested reproduction only:
python -m dexlab.impact_run --manifest docs/evidence/elastic-impact/manifest.json --output new-run
```

Scoring first verifies native settings/hashes, complete trajectories, force epochs, per-body impulses and initialization. Four tests cover reference algebra, synthetic elastic evidence, nine corruption classes and a momentum-conserving inelastic negative. Provenance is not real-material validation. All18 formal outcomes are retained without repeated trials or outcome-based threshold changes.
