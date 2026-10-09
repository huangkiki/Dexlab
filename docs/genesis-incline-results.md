# Genesis incline: contact model changes the result

[简体中文](genesis-incline-results.zh-CN.md) · [Protocol and commands](genesis-incline-protocol.md)

Under the frozen native Genesis 1.4.3 / Quadrants 1.3.3 CPU FP64 protocol, Newton/elliptic/Signorini passes all six nonzero-friction cases, but fails all three nominal-zero cases. Newton/elliptic/convex passes only the three static cases; the other three configurations pass none. All five disabled-contact negatives are valid and correctly rejected. These are case counts under fixed settings, not success probabilities or a general engine ranking.

| Solver / cone / contact model | Positive passes | Invalid positives | Negative |
|---|---:|---:|---|
| Newton / elliptic / signorini | 6/9 | 0 | Valid, rejected |
| Newton / elliptic / convex | 3/9 | 0 | Valid, rejected |
| Newton / pyramidal / convex | 0/9 | 0 | Valid, rejected |
| CG / elliptic / convex | 0/9 | 4 | Valid, rejected |
| CG / pyramidal / convex | 0/9 | 3 | Valid, rejected |

## Zero input is not zero effective contact friction

The official material constructor rejects μ=0. Its public geometry setter accepts zero and reads back zero, but contact generation applies **max(μA·ratioA, μB·ratioB, .01)**. Each contact's effective coefficient is recorded; all nominal-zero contacts read .01. The input, effective model and original zero-friction target are kept distinct. Source: [pinned contact combination](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/contact.py#L433-L463).

For Signorini, the nominal-zero acceleration deficit is about **0.0947573 m/s²**, matching μg cos(15°) for μ=.01. The three separately labeled effective-.01 diagnostics pass the same numeric limits. They cannot replace the original failures or add coverage. Convex contacts additionally lose continuous support under these settings; tighter timesteps do not make the entire task pass. Pyramidal static cases exceed the displacement limit. See every metric/check in the score files, including rotation, penetration and support failures.

## Seven CG records fail force/state consistency

CG/elliptic retains four invalid records: all static timesteps and the 2 ms sliding case. CG/pyramidal retains three: all nominal-zero timesteps. Maximum impulse residuals span **1.50305e-7 to 1.23691e-6 N·s**, above the unchanged 1e-7 limit. Native error bits are zero; geometry, clock, position/velocity and per-contact/net-force ledger checks pass. An error-free API return is insufficient physical evidence.

Separate diagnostic prefixes reproduce all seven offending state/force prefixes exactly. Native translational gradient × dt matches the measured impulse residual to 1e-15 N·s. Six stopping states satisfy the source's improvement threshold with a non-flat gradient; the 2 ms sliding sample still has `improved=true` at the configured 100-iteration cap. These are source-linked interpretations of observed fields, not an exposed iteration counter. At the 1 ms static sample, raising the cap from 100 to 1000 leaves the entire 106-step prefix unchanged: its improvement 1.8551521e-10 is already below the scaled threshold 1.9205120e-10. No engine patch, score relaxation or replacement acquisition was used.

[Diagnostic observations](evidence/genesis-incline/stopping-diagnosis.json) · [Native gradient and loop](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5136-L5160) · [Stopping conditions](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py#L568-L616).

## Scope, exclusions and cost

Five supported rigid solver/cone/contact combinations complete **45 positives + 5 negatives / 115,000 native updates**. Signorini with Newton/pyramidal, CG/elliptic or CG/pyramidal is rejected by the official API before stepping. This is a version-specific unsupported result; a supporting official release requires fresh qualification. Integrator/device and tuning sweeps are outside this cohort. Native execution is separate from the existing patched-framework pinch record and the future Isaac/MJWarp comparison [#152](https://github.com/huangkiki/Dexlab/issues/152).

The frozen acquisition uses 16 GiB, a four-core quota, one Quadrants execution/compile thread, zero swap and 8 GiB launch reserve. Measured peak is **623.391 MiB**; the next equivalent workload fits the minimum 8 GiB tier. There are no memory-limit/OOM events; two CPU-throttled periods total 223.285 ms. The two acquisition service segments total **83.878 s**, including offline validation and the intentional stop after invalid CG evidence. Summed setup/native-step/observation times are **17.801 / 15.312 / 12.583 s**. Diagnostic work is separate: three processes, nine prefixes, 2,217 updates, 21.467 s. These instrumented correctness costs do not support cross-engine speed rankings. [Per-case timing](evidence/genesis-incline/timing.json).

All native traces, effective options/kernel flags, contact ledgers, errors, failed setup attempts and frozen sources are retained. No compatible historical Genesis incline set was found in the checked manifests, releases or paired archive; historical telemetry remains absent. Full reliable coverage-v1 admission, a shared tuning budget and a frozen holdout comparison are not claimed. Five configurations and three rejected combinations still represent one task type.

[Complete scores and protocols](evidence/genesis-incline/profiles.json) · [Official identity](evidence/genesis-incline/official-proof.json) · [Native unsupported combinations](evidence/genesis-incline/unsupported.json) · [Resource records](evidence/genesis-incline/resources.json) · [History audit](evidence/genesis-incline/history-reuse-audit.json)

[Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.52.0/dexlab-genesis-incline-v1.tar.gz) · [Archive SHA256](evidence/genesis-incline/archive.json)
