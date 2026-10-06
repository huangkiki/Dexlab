# Synthetic response and compute cost: protocol

English | [简体中文](RESPONSE_COST.zh-CN.md)

Status: all 27 formal episodes and offline score reproduction completed. Full delivery regressions and evidence were published in [v0.24.0](https://github.com/huangkiki/Dexlab/releases/tag/v0.24.0).

## Question and reference

With native contact parameters fixed, does timestep refinement reduce discrepancy from a specified synthetic response, and at what cost? Retain the existing linear spring–damper target: K=20,000 N/m, D=40 N s/m, mass=0.2 kg. This is a design target, not measured material data or a universal contact law.

Use the existing transient scorer on positive-load windows without fitting time, phase or position offsets. Independently check unloading for tensile force and separation. Preserve engineering thresholds; passing them is not physical accuracy. Nondecreasing discrepancy is a valid negative result.

## Frozen matrix

`benchmarks/contact-response-cost-v1.json` retains two existing MuJoCo impedance profiles and one SuperDex load-dependent damping profile. Each runs at 0.5, 0.25 and 0.125 ms with three repeats: 27 serial fresh scenes in deterministic cyclic order. Each lasts 0.8 simulated seconds with 2, 4, 6 N loading and unloading. No retuning; repeated runs are not independent generalization scenarios.

Budget: 600 seconds per batch, 660 seconds enforced process timeout. Freeze source and matrix after resource and latest official stable-runtime admission. PhysX is excluded because stable-runtime qualification is unresolved; no older substitute.

## Timing boundaries

- Native API time includes collision, integration and solving, not only solver kernels.
- Observation time includes state, contact and solver-status extraction, disjoint from the native call.
- Outer step time includes task wrapping but excludes preceding action computation.
- Separately measure the full `run()` call including source snapshots, scene creation, actions, recording, cleanup and independent scoring; exclude batch startup and version admission.
- Record the complete bounded-process wall time separately. Report per-profile repeat minimum, median and maximum cost alongside absolute RMS/peak response discrepancy; disclose cold-start and cache effects.

Host wall-clock measurements include clock-call and scheduling overhead. Record clock resolution and call overhead before the formal batch; short intervals are not exact kernel benchmarks.

Four instrumentation controls completed: each engine's timing-off/on state arrays are bitwise equal and contact ledgers equal. Both MuJoCo runs passed the original engineering checks; both SuperDex failures remain. This supports noninterference only for the recorded quantities and tested cases.

Retain raw records, failures, native parameter readback and source hashes. Missing runs remain in the declared denominator of 27. Agreement with real materials requires separate independent measurements.

## Measured results

[Preregistration](https://github.com/huangkiki/Dexlab/issues/10#issuecomment-5996681658). Official MuJoCo 3.14.0 and SuperDex 1.0.0 FP64; source freeze verified. Costs below are medians of three 0.8-second episodes; the analysis script emits minimum/median/maximum. RMS is the worst of three positive-load windows across all repeats.

| Profile | Combined pass | Worst-window RMS / µm | Peak error / µm | Native API / ms | Observation / ms | Full call / s |
|---|---:|---:|---:|---:|---:|---:|
| mujoco-imp09-500us | 0/3 | 120.654 | 214.862 | 4.539 | 57.041 | 0.2690 |
| mujoco-imp09-250us | 0/3 | 76.542 | 140.812 | 8.958 | 97.718 | 0.5138 |
| mujoco-imp09-125us | 0/3 | 67.765 | 127.452 | 18.224 | 214.505 | 0.9687 |
| mujoco-imp0001-500us | 3/3 | 2.771 | 7.185 | 4.482 | 57.212 | 0.2745 |
| mujoco-imp0001-250us | 3/3 | 1.327 | 3.464 | 8.987 | 100.058 | 0.4844 |
| mujoco-imp0001-125us | 3/3 | 0.617 | 1.643 | 18.228 | 204.208 | 0.9725 |
| superdex-load-damping-500us | 0/3 | 9.209 | 22.843 | 20.193 | 90.800 | 0.3213 |
| superdex-load-damping-250us | 0/3 | 11.997 | 27.545 | 40.750 | 223.807 | 0.6438 |
| superdex-load-damping-125us | 0/3 | 13.751 | 30.200 | 81.981 | 450.553 | 1.2459 |

The low-impedance MuJoCo profile approaches the synthetic target as timestep decreases; this establishes neither material accuracy nor convergence order. The high-impedance profile improves but still misses the declared target. SuperDex discrepancy increases for this parameter mapping, and every timestep fails the no-tension check; smaller timesteps do not repair the difference from the specified reference.

Observation extraction exceeds native-call time for both backends. Calling full-script cost solver speed would be misleading. Short native intervals include timer overhead; three repeats describe local variability on this constrained machine only. All nine combined passes and eighteen failures remain; repeats are not generalization success-rate samples.

```bash
python demos/contact-benchmark/report_response_cost.py PATH_TO_EVIDENCE/study
```

![Synthetic response and measured cost](../../docs/evidence/response-cost-v1.png)

Execution platform: local Intel Core i9-14900K, cgroup quota equivalent to two logical CPUs without affinity pinning, 24 GiB memory cap and swap disabled. Scenes are recreated in one Python process, sharing caches; repeats are not isolated cold starts. These costs are not a standardized cross-machine or cross-engine ranking.
