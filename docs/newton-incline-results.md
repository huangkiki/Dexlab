# Newton Physics incline: separate physical failure from numerical checks

[简体中文](newton-incline-results.zh-CN.md) · [Protocol and reproduction](newton-incline-protocol.md)

Seven native Newton 1.6.1 / Warp 1.18.0 CPU FP32 configurations were evaluated under the frozen 40 mm / 64 g cube protocol. XPBD and Kamino PADMM each pass one of nine positives; Kamino DVI passes four. The other configurations pass none. **49 positive records fail numerical/representation checks; two VBD negative records also fail.** These are initial fixed-configuration results, not an engine ranking, an equal-tuning comparison or reliable coverage-v1 admission.

| Solver configuration | Positive passes | Invalid positives | Disabled-contact negative |
|---|---:|---:|---|
| XPBD / 100 sweeps | 1/9 | 6 | Valid, rejected |
| SemiImplicit | 0/9 | 4 | Valid, rejected |
| Featherstone | 0/9 | 9 | Valid, rejected |
| VBD legacy / 100 sweeps | 0/9 | 9 | Invalid, retained |
| VBD compliant / 100 sweeps | 0/9 | 9 | Invalid, retained |
| Kamino PADMM / Euler | 1/9 | 8 | Valid, rejected |
| Kamino DVI / Euler | 4/9 | 4 | Valid, rejected; explicit continuation |

All three successful configurations pass the .5 ms static case. DVI additionally passes all three sliding cases. XPBD's other static cases exceed displacement and/or speed limits. SemiImplicit's valid records still fail physical acceptance under the fixed penalty/smoothing settings. Invalid cases stay in the denominator; an invalid negative cannot qualify coverage.

## What the rejected records establish

The original **1e-7 N·s** momentum guard and physical error thresholds remain unchanged. The frozen 8-epsilon FP32 checks were engineering consistency checks, **not derived forward-error bounds for repeated solver updates**. Their failure does not by itself prove injected states, a broken recorder or task impossibility. No engine patches or post-initialization state writes occurred. [Source-linked interpretation](evidence/newton-incline/readback-interpretation.json).

- **XPBD:** the native kernel updates position and velocity incrementally, with separate FP32 rounding, and snaps very small velocities to zero. Reconstructing velocity from the final position delta is disabled by default. All six moving cases exceed the frozen position/velocity check; supplementary measurements also find momentum residuals **4.64e-7–1.50e-6 N·s**, above the separate guard. These remain invalid. [Pinned update kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L869-L938).
- **Kamino:** the Euler path multiplies a quaternion exponential by the prior quaternion without explicit renormalization in that update. PADMM norm drift reaches **3.56e-5**; DVI reaches **2.22e-6**, versus the frozen 8-epsilon check of about 9.54e-7. Raw states are retained; the scorer does not normalize them to manufacture passes. [Pinned pose update](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/core/math.py#L544-L560).
- **VBD:** all positives and both negatives exceed the momentum guard. The no-contact negative residual is **1.74884e-5 N·s** in both modes; native velocities are reconstructed from FP32 pose differences. Contact cases additionally expose a difference between the last primal force and the final-dual force query. This is a measured numerical limitation of the frozen evidence, not a uniquely established explanation of every residual. [Velocity update](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/rigid_vbd_kernels.py#L6675-L6740).

Separate VBD diagnostics first reproduce the original 100-sweep prefixes exactly. A second probe fixes the first 15 steps at 100 sweeps and varies only step 16. The compliant mode repeats the same X/Z positions and returned forces for odd caps 99/101/1001 and even caps 100/1000; small out-of-plane/orientation differences remain. The selected-step residual alternates between **4.31014e-6** and **4.03585e-6 N·s**. More iterations do not remove this observed pattern. Legacy improves at that selected step (1000: 1.15088e-7; 1001: 3.97352e-8 N·s), but earlier errors and all original 100-sweep failures remain. These probes are not replacement scores. [Native fields and comparisons](evidence/newton-incline/vbd-diagnosis.json).

Every case also has [descriptive raw measurements](evidence/newton-incline/observations/xpbd.json): displacement, speed, fitted acceleration, position/velocity errors, force errors, contact counts, norm drift and momentum residual. Equivalent files exist for each profile. Geometric diagnostics explicitly use normalized quaternion direction; they calculate no acceptance. They help inspect rejected records without silently admitting them. A new precision-aware protocol requires a prospective freeze and independent holdout validation.

## The interrupted negative remains visible

DVI completed all nine positives, then its frozen **1800 s** service limit interrupted the negative after **1588 of 2000** completed updates, with one further attempted update unresolved. The original campaign remains `interrupted` and is rejected by the scorer. Final cgroup telemetry is missing; the last sample remains labeled as such.

A separately preregistered **one-start / 2000-update / 600 s** continuation reinitializes only that negative, using the same native recorder, model, options and thresholds. Its 1588 overlapping state/force samples match exactly. All nine completed positives are reused byte-for-byte. The composite archive includes the complete original attempt and validates every binding. No timeout was extended retrospectively and no original failure was erased. [Continuation freeze](evidence/newton-incline/continuation-v1-freeze.json) · [Recovery validation](evidence/newton-incline/scoring-revision2.json).

## Scope and resources

Style3D and ImplicitMPM advance particle systems rather than this stand-alone free rigid cube. Their source-based exclusions apply only to this model and version; constructor errors are not the proof. `SolverMuJoCo` belongs to the MuJoCo core and its compatible wrapper path remains separately unrun. [Scope evidence](evidence/newton-incline/unsupported.json). No protocol-compatible historical Newton incline cohort was found in the [specified search](evidence/newton-incline/history-reuse-audit.json); sphere-contact and cloth history are not relabeled as incline data.

Acquisition freezes **8 GiB / four-core quota / zero swap / 8 GiB launch reserve**. The largest observed acquisition high-water mark is **604.988 MiB**, from DVI's final pre-timeout sample. The completed PADMM service peaks at 515.980 MiB. DVI's sampled CPU peak is about 1.37 cores, with no throttled periods in that last sample; neither extra RAM nor an eight-core quota is demonstrated to fix its runtime limit.

Original services plus continuation total **3759.875 s**; recorded native step calls total **3638.126 s**. There are **161000 updates** in the completed scoring set, plus the retained **1588** interrupted-negative updates and one unresolved attempted update. Native step timers exclude collision generation, readback and serialization. Development diagnostics use a separate budget and contribute 1000 updates. Cache state, compiler overhead and solver budgets differ, so these instrumented correctness costs are not a speed ranking. [Resources](evidence/newton-incline/resources.json) · [Case timings](evidence/newton-incline/timing.json).

[Scores and protocols](evidence/newton-incline/profiles.json) · [Official identity](evidence/newton-incline/official-proof.json) · [Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.53.0/dexlab-newton-incline-v1.tar.gz) · [SHA256](evidence/newton-incline/archive.json)
