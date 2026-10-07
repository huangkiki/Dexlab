# Incline sliding diagnosis

[简体中文](incline-diagnosis.zh-CN.md)

## Frozen protocol

Follow-up to the six failed sliding cases in [v0.43.0](incline-friction-results.md), Issue #97. Reuse the released ratio=1 baseline and all its thresholds. At 35°, μ=0.5, test friction-to-normal constraint impedance ratio `impratio`=0.1 and10, each at impedance0.9/0.99 and timestep2/1/0.5ms:12 cases,2s each. No additional tuning batch. Geometry, mass, inertia, initial state, solver, iterations, integration, contact parameters and gravity remain as in the [original protocol](incline-friction-protocol.md).

The [official parameter definition](https://mujoco.readthedocs.io/en/stable/XMLreference.html#option-impratio) makes this a numerical contact-model sensitivity test, not a change to the friction coefficient or measured material. Prediction to test: altering relative friction impedance may change contact continuity and rotational growth. Either direction or no change is admissible evidence; no improvement is presumed.

Compare every case with its existing matched baseline: lost-contact fraction, maximum rotation, acceleration error, velocity/position RMSE, force residual, penetration and native step cost. Retain all original pass thresholds and all failures. Do not infer hardware accuracy, universal engine fault or optimal settings. A changed outcome supports sensitivity to this single option; it does not uniquely identify the internal instability mechanism.

One local admitted worker, official MuJoCo3.15.0 CPUFP64,16GiB/two-CPU/128task/swap0/30min cap. No transfers or large checksums during timing. Record setup and scoring separately. Current source, manifest hash and preregistration comment precede physics; raw evidence stays immutable.
