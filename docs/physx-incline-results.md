# PhysX incline: native SDK results and numerical boundaries

[简体中文](physx-incline-results.zh-CN.md) · [Protocol and reproduction](physx-incline-protocol.md)

Four native **PhysX SDK 5.9.0 / CPU / FP32** configurations completed 36 positive and four disabled-contact negative episodes. PGS and PGS with friction every iteration each pass **7/9**; the two TGS configurations each pass **3/9**. All four negatives have valid observations and are correctly rejected. **13 positive records fail the frozen numerical checks** and remain in the denominator. These are initial fixed-configuration results, without shared tuning, frozen holdouts or reliable coverage-v1 credit.

| Configuration | Positive passes | Invalid positives | Valid physical failures | Negative |
|---|---:|---:|---|---|
| PGS | 7/9 | 1 | Frictionless .5 ms: force balance | Valid, rejected |
| PGS friction every iteration | 7/9 | 0 | Sliding and frictionless .5 ms: force balance | Valid, rejected |
| TGS | 3/9 | 6 | None among the valid positives | Valid, rejected |
| TGS external forces every iteration | 3/9 | 6 | None among the valid positives | Valid, rejected |

All configurations pass the three static cases. PGS also passes sliding at 1/.5 ms and frictionless at 2/1 ms. PGS friction passes sliding at 2/1 ms and frictionless at 2/1 ms. Smaller steps do not monotonically improve these fixed configurations: the two PGS frictionless .5 ms records have force-balance RMSE **.010485 N**, above .01 N; PGS friction's .5 ms sliding record has **.012763 N**. Other frozen metrics for those three valid failures pass. Raw outcomes are retained without tuning a replacement configuration.

## What the invalid records mean

PGS sliding at 2 ms reaches a normal-impulse direction discrepancy of **1.008973e-10 N·s**, just above the frozen 1e-10 N·s engineering check. The callback computes the reported impulse by multiplying an FP32 normal by an FP32 scalar. This check compares it against the analytical plane normal; it is not a derived rounding-error bound. The record remains invalid, rather than changing the criterion after seeing the result.

Both TGS configurations' six moving cases exceed the unchanged **1e-7 N·s** state/impulse consistency guard: maxima range from **1.093918e-7 to 1.964716e-7 N·s**. Replacing nominal mass/gravity with their actual native FP32 readbacks does not remove the exceedances. The native [contact solver](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1566-L1584) updates accumulated impulses and velocities in separate FP32 operations; its [writeback](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1863-L1922) exposes accumulated impulses. This establishes the observation path, not a unique causal decomposition of every residual.

One independently launched repeat each of PGS sliding and TGS frictionless at 2 ms exactly reproduces all **1,000** original state/parameter/contact records, excluding wall time. Short static diagnostics also reproduce all four profiles when actor insertion order is reversed. No official engine patches or post-initialization state writes occurred. A guard failure alone does not prove injected state, missing force or an engine-wide inability to solve the task. [Repeat evidence](evidence/physx-incline/repeat-result.json) · [Numerical interpretation and source](evidence/physx-incline/readback-interpretation.json).

[Follow-up #163](https://github.com/huangkiki/Dexlab/issues/163) owns the bounded numerical analysis and any separately frozen precision-aware protocol with independent holdouts. The original scores remain immutable. [Descriptive measurements](evidence/physx-incline/observations/pgs.json), also available for `pgs-friction`, `tgs` and `tgs-external`, report displacement, speed, acceleration, rotation, penetration, support, force error, residuals and cost for every record. Normalized-quaternion rotation is explicitly diagnostic and cannot change acceptance.

## Admission failures and scope

Zero-step admission caught an incorrect negative-control mass: disabling collision before `updateMassAndInertia` makes that helper ignore the box. The recorder now initializes mass/inertia first, then disables only collision. The old ten-case admission and four short wrong-mass negative diagnostics remain in the archive; the final 40 admissions all verify 64 g and the intended inertia before formal runs. The first recorder builds used an obsolete geometry API and encountered GCC warnings in unchanged SDK headers; these preparation failures are retained. A module-discovery launch failed before any native starts and was repeated with an explicit frozen source path.

SDK 5.9 has only patch friction. Former one-/two-direction friction options are not available; TGS intrinsically processes friction every iteration, and its external-force flag is invalid for PGS. These are source-verified applicability decisions, not runtime failures relabeled as unsupported. The CPU SDK cohort does not qualify GPU or Isaac/ovphysx paths. [Version selection](evidence/physx-incline/release-selection.json) distinguishes the explicitly versioned stable SDK from wrapper releases; [#152](https://github.com/huangkiki/Dexlab/issues/152) retains compatible framework comparison.

No core-identified, protocol-compatible historical PhysX nine-case data was found in the [bounded reuse audit](evidence/physx-incline/history-reuse-audit.json). New readbacks do not repair missing #126 historical telemetry. [Prior failures](evidence/physx-incline/prior-failures.json) · [Official source/build identity](evidence/physx-incline/official-proof.json).

## Resources and evidence

The four serial acquisition services total **10.782 s**, recording **92,000 updates**; instrumented native simulate/fetch/contact-copy calls total **1.243 s**. The acquisition peak is **76.227 MiB**, with zero throttled CPU periods and no memory-high/OOM events. The frozen envelope is **8 GiB / four-core quota / zero swap**, with 8 GiB additional launch reserve. A larger quota is not demonstrated to improve this small CPU fixture. These are instrumented correctness costs, not cross-engine throughput figures. [Resource telemetry](evidence/physx-incline/resources.json) · [Per-case timings](evidence/physx-incline/timing.json).

Development separately uses 64 native starts: 50 zero-step admissions and 14 diagnostic/repeat processes totaling 2,240 updates. SDK compilation, dependency setup and submission are separate preparation costs. The first dependency setup hit the archive profile's 32-task cap; the recovered isolated environment uses the adaptive profile's 128-task cap, with the failed receipt retained.

[Scores and protocols](evidence/physx-incline/profiles.json) · [Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.54.0/dexlab-physx-incline-v1.tar.gz) · [SHA256](evidence/physx-incline/archive.json)
