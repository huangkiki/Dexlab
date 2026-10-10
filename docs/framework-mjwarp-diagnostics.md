# Isaac Sim / MJWarp development diagnostics

[English](framework-mjwarp-diagnostics.md) | [简体中文](framework-mjwarp-diagnostics.zh-CN.md)

**The contact recorder is corrected; this is not three-task qualification.** Four final 0.2 s cases finish with clean process exit. Both no-floor controls pass the frozen trace checks. Both supported cases retain a failed 1e-7 N·s momentum check. No reliable task type is added. [#152](https://github.com/huangkiki/Dexlab/issues/152) remains open for native latest/matched-core paths, explicit asset alignment, collision, finite pinch, reset and untouched holdouts.

## Frozen scope and identities

A synthetic 40 mm, 64 g free cube starts 1 µm above a finite floor inclined 15°, with friction .5 and gravity 9.81 m/s². Each independent process executes 200 steps at 1 ms, one CUDA world, Newton solver/pyramidal cone, with either Newton or MJWarp contact generation. Each path has a support case and a disabled-floor control. This is a recorder diagnostic, separate from the historical incline cohort and the new coverage contract; no tuning or holdout result is claimed.

The locally built Isaac Sim v6.1.0 source tag reports `6.1.0-rc.26+mr.0.7c206f75.local`. It loads MuJoCo/MJWarp3.11.0, Newton1.5.0 and vendor Warp1.16.0. The audit compares 1,390 files across the first five pinned physics/conversion packages against official wheels, plus 42 official-tag integration Python files. Warp's 555 non-binary payload files match PyPI; its two native libraries differ from PyPI but match the NVIDIA extension archive. All 701 vendor archive files were compared; only generated extension metadata differs by archive location/formatting. This is **not** certification of every Isaac/Kit binary. Selected cached Python code was also compared with fresh compilation without modifying caches.

Actual loaded MuJoCo and Warp library hashes are checked before every case. Same version labels do not establish binary equality: future matched-core attribution must also control the Warp payload. Native latest3.15.0 and the matched native path remain pending. [Official framework explanation](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/physics/newton_physics.html) · [identity evidence](evidence/framework-mjwarp/qualification.json).

## Measurements and retained failures

| Contact path | Support momentum residual (N·s) | Native contact sum residual (N) | No-floor trace | Final lifecycle |
|---|---:|---:|---|---|
| Newton | 7.8766e-7 — failed | 9.8245e-7 — passed | Passed | Both exit0 |
| MJWarp | 7.2076e-7 — failed | 9.4023e-7 — passed | Passed | Both exit0 |

The unchanged contact-force bound is 1e-5 N. All four final cases pass clocks, effective timestep, counters, contact capacity and complete readback. GPU clock error after 200 steps is 2.265e-7 s; framework clock error is below1.4e-16 s. The compiled CPU model initially says2 ms, while the framework uses1 ms; actual GPU stepping reads1 ms. Initialization alone would have produced a false clock diagnosis.

`get_data_into` converts detected contacts to contiguous CPU constraint addresses even when some contacts have no active constraint. In the retained Newton step80 example, inactive contacts have GPU addresses−1,−1; active contacts start at0,4, while the CPU representation assigns0,4,8,12 with only8 constraints. The last two contact forces are then read as zero. The recorder now uses the official GPU `contact_force` API and retains both representations, original addresses and constraint forces. Independent NumPy pyramid decoding matches native GPU forces within2.24e-8 N. CPU conversion mismatches occur in7/200 Newton and176/200 MJWarp frames. The Newton v1/v4 state and generalized-force traces are exactly equal: the readback fix does not alter physics.

Momentum remains a separate numerical failure. At the worst Newton sample, the native acceleration/force equation itself has a7.8765e-4 N residual and the solver reports one iteration out of100. The stopping cause is not yet established; the original bound is unchanged and no engine-defect or material-accuracy claim follows. [Full scores and resource costs](evidence/framework-mjwarp/diagnostics.json).

The original128-task cap aborts initialization; four-core CPU affinity alone does not fix it. The added opt-in256 cap preserves historical profiles and frozen plans. Initial positive-duration runs used24 GiB; measured peak6.252 GiB selected16 GiB for the next frozen batch under the1.5× rule. Four CPU equivalents, zero swap and8 GiB admission reserve remain. `pids.peak` is recorded, with explicit null on older kernels. Timing includes initialization, observation and shutdown and is not solver throughput.

Earlier short runs aborted at shutdown; full teardown then spun for over120 s and was stopped. Detaching the stage and processing10 updates alone also failed. Explicit synchronous renderer initialization, with the detached-stage cleanup, yields clean exit for all four final cases. These observations support this launch configuration; they do not establish general lifecycle reliability. All20 starts and2,000 recorded updates, including the first10 zero-duration attempts, remain in [development history](evidence/framework-mjwarp/development-history.json).

## Evidence and reproduction

The [v0.56.0 evidence archive](https://github.com/huangkiki/Dexlab/releases/tag/v0.56.0) contains every diagnostic generation, source snapshots, original USD, intermediate MJCF, exact compiled MJB, effective parameters, raw step/contact readbacks, failures and resource receipts. [Archive identity](evidence/framework-mjwarp/archive.json). Public path/UUID redactions are listed with original/published hashes; numerical records are unchanged. No original installed engine is patched.

Run from a DexLab checkout using the qualified compatible runtime. Set `ISAAC_ROOT`, `OUT`, `EVIDENCE` and `DATA_DIR` to your own paths, with a block device for `IO_DEVICE`. The old receipt is a measurement for choosing the frozen profile, not a claim about another host's free memory:

```bash
export PYTHONPATH="$PWD/src"
export LD_LIBRARY_PATH="$ISAAC_ROOT/exts/isaacsim.pip.nv/pip_prebundle/nvidia/cuda_runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python scripts/bounded_run.py --profile adaptive --task-limit 256   --resource-plan "$OUT/resources-plan.json"   --peak-receipt "$EVIDENCE/clock-newton-support-v1-resources.json"   --data-dir "$DATA_DIR" --io-device "$IO_DEVICE" --timeout 1200   --receipt "$OUT/resources.json" --   bash "$ISAAC_ROOT/python.sh" --no-ros-env scripts/probe_isaac_mjwarp.py   --protocol configs/framework-clock-probe-v4.json --case newton-support   --output "$OUT/newton-support" --warp-cache "$OUT/warp-cache"   --portable-root "$OUT/kit-state"
python -m dexlab.framework_probe_score "$OUT/newton-support"
```

Use the existing research lock for acquisition and keep transfers/scoring separate. The other frozen case IDs are `newton-no-floor`, `mjwarp-support`, `mjwarp-no-floor`; preserve separate output directories. The scorer intentionally exits nonzero on either failed support case. The acquisition launcher used four allowed CPUs, four BLAS threads, per-session vendor analytics disabled, and resource telemetry enabled; the archived invocation/receipts retain these choices. New reproduction must freeze equivalent launch settings and verify official source/binary hashes first.
