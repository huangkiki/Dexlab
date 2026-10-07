# Incline sliding diagnosis

[简体中文](incline-diagnosis.zh-CN.md)

## Frozen protocol

Follow-up to the six failed sliding cases in [v0.43.0](incline-friction-results.md), Issue #97. Reuse the released ratio=1 baseline and all its thresholds. At 35°, μ=0.5, test friction-to-normal constraint impedance ratio `impratio`=0.1 and10, each at impedance0.9/0.99 and timestep2/1/0.5ms:12 cases,2s each. No additional tuning batch. Geometry, mass, inertia, initial state, solver, iterations, integration, contact parameters and gravity remain as in the [original protocol](incline-friction-protocol.md).

The [official parameter definition](https://mujoco.readthedocs.io/en/stable/XMLreference.html#option-impratio) makes this a numerical contact-model sensitivity test, not a change to the friction coefficient or measured material. Prediction to test: altering relative friction impedance may change contact continuity and rotational growth. Either direction or no change is admissible evidence; no improvement is presumed.

Compare every case with its existing matched baseline: lost-contact fraction, maximum rotation, acceleration error, velocity/position RMSE, force residual, penetration and native step cost. Retain all original pass thresholds and all failures. Do not infer hardware accuracy, universal engine fault or optimal settings. A changed outcome supports sensitivity to this single option; it does not uniquely identify the internal instability mechanism.

One local admitted worker, official MuJoCo3.15.0 CPUFP64,16GiB/two-CPU/128task/swap0/30min cap. No transfers or large checksums during timing. Record setup and scoring separately. Current source, manifest hash and preregistration comment precede physics; raw evidence stays immutable.

## Results

**0/12 meet the original joint acceptance. Changing relative friction impedance did not restore continuous supported sliding.** Lost-contact fractions remain72.4–76.4%; maximum rotation0.0868–3.1382rad exceeds0.01rad throughout. Every acceleration error is below0.015m/s², illustrating why this scalar alone cannot establish valid sliding. The baseline six failures remain unchanged, alongside the original static/frictionless results.

| Case | No contact | Max rotation (rad) | Acceleration error (m/s²) |
|---|---:|---:|---:|
| sliding-d0.9-h0.002-ratio0.1 | 75.200% | 3.138179 | 0.014165 |
| sliding-d0.9-h0.001-ratio0.1 | 72.600% | 0.166029 | 0.001921 |
| sliding-d0.9-h0.0005-ratio0.1 | 72.475% | 0.104360 | 0.011988 |
| sliding-d0.99-h0.002-ratio0.1 | 74.700% | 0.364117 | 0.000541 |
| sliding-d0.99-h0.001-ratio0.1 | 72.800% | 0.162559 | 0.006913 |
| sliding-d0.99-h0.0005-ratio0.1 | 72.400% | 0.086777 | 0.001744 |
| sliding-d0.9-h0.002-ratio10.0 | 76.400% | 3.132893 | 0.002106 |
| sliding-d0.9-h0.001-ratio10.0 | 73.750% | 0.109987 | 0.006825 |
| sliding-d0.9-h0.0005-ratio10.0 | 73.850% | 0.131376 | 0.012930 |
| sliding-d0.99-h0.002-ratio10.0 | 74.900% | 0.221934 | 0.004287 |
| sliding-d0.99-h0.001-ratio10.0 | 74.450% | 0.178824 | 0.002162 |
| sliding-d0.99-h0.0005-ratio10.0 | 72.675% | 0.193549 | 0.002332 |

All12 traces pass artifact/runtime and discrete impulse consistency checks; these checks do not mean physical-reference acceptance. Full metrics, timings and hashes: [results](evidence/incline-diagnosis/results.json), [manifest](evidence/incline-diagnosis/manifest.json), [archive receipt](evidence/incline-diagnosis/archive.json). Preregistered source96ad8a9, [comment](https://github.com/huangkiki/Dexlab/issues/97#issuecomment-6045969503). Native stepping summed0.050908s; campaign wall0.278770s; bounded service1.206s, scoring service1.205s. These short measurements are noisy and are not an engine ranking.

## What the evidence resolves

The declared plane orientation and downhill/normal vectors are orthogonal, the initial cube face is aligned with the plane, mass/inertia match a uniform40mm64g cube, and the plane collision surface is infinite. Native forces and state updates satisfy the discrete impulse check. Old traces show genuine normal displacement and angular growth, not merely a plotting label or threshold mistake. No source/frame error was identified in this bounded audit.

For ideal nonrotating sliding, the tangential contact force creates a moment balanced by a shifted normal-force resultant: required offset=μ times half-height=10mm, within the20mm half-footprint. Thus the declared ideal model permits supported sliding; this is not evidence that a real material will do so. Contact loss violates that model's condition. Changing only impratio did not remove the observed failure, so do not present this option as a fix. Exact initiation and growth mechanisms remain unresolved; contact torque/solver residual instrumentation and a separately preregistered integration/contact-law diagnostic would be needed. No additional tuning runs were performed.

## Operational evidence and next research

The first isolated setup failed with a full system volume, also losing final telemetry; it is not a successful qualified run. Only the new incomplete environment was relocated after no-consumer checks and complete file/hash readback, under the archive cgroup and existing exclusive lock. The data-volume retry succeeded in8.755s. A launcher spelling error (`benchmark` instead of `timing`) exited before physics; its receipt is preserved. All historical evidence remains. No independent backup is claimed for a relocation.

Next separate work: instrument contact torque and convergence to narrow causality, or preregister centered1D collision with a justified restitution reference. For grasping, continuous support and orientation must accompany slip-speed/acceleration metrics; an average motion fit can conceal repeated loss of contact. Hardware validation remains a separate evidence class.
