# Native / Isaac Sim MJWarp diagnostics

[English](framework-mjwarp-diagnostics.md) | [简体中文](framework-mjwarp-diagnostics.zh-CN.md)

**The matched native core also fails the frozen support momentum check.** Explicitly aligning four GPU parameters does not eliminate the failure or reproduce the framework trajectory. Three independent aligned native processes produce identical recorded steps. These are development diagnostics, not complete incline/collision/pinch qualification, and add no reliable task type. [#152](https://github.com/huangkiki/Dexlab/issues/152) remains open for latest-native comparison, remaining effective-state differences, the three complete tasks, reset and untouched holdouts.

## Frozen scope and identity

A synthetic40 mm,64 g free cube starts1 µm above a finite15° floor with friction.5 and gravity9.81 m/s². Each process executes200 steps at1 ms, one CUDA world, Newton solver and pyramidal cone. Framework paths use Newton or MJWarp contact generation; native uses MJWarp. Each has a disabled-floor negative. The development protocol preserves the1e-7 N·s momentum bound; no tuning/holdout acceptance or real-material accuracy is claimed.

The Isaac Sim v6.1.0 local source-tag build reports `6.1.0-rc.26+mr.0.7c206f75.local`, loading MuJoCo/MJWarp3.11.0, Newton1.5.0 and vendor Warp1.16.0. Prior audits checked1,390 physics/conversion package files,42 integration files and701 vendor archive files, with only generated vendor metadata differences. This is not certification of every Isaac/Kit binary. [Framework audit](evidence/framework-mjwarp/qualification.json).

The native path loads the framework's exact MJB and matches its CPU model readback. Its239 MuJoCo and281 MJWarp files match the official wheels;684 selected vendor Warp files match the audited NVIDIA archive. Actual loaded MuJoCo and Warp library hashes are checked before stepping. The official Newton authoring-to-runtime sleep-policy projection is recorded explicitly. No engine source or binary is patched. Latest-native3.15.0 remains pending. [Matched identity](evidence/framework-mjwarp/qualification-matched.json) · [Official framework conversion/contact paths](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/physics/newton_physics.html).

## Results and the attribution limit

| Path | Maximum support momentum residual (N·s) | No-floor state checks | Completed processes |
|---|---:|---|---:|
| Framework / Newton contacts / v6 | 7.8766e-7 — failed | Passed | 2 |
| Framework / MJWarp contacts / v6 | 7.2076e-7 — failed | Passed | 2 |
| Native matched core / original GPU inputs | 1.0071e-6 — failed | Passed | 2 |
| Native matched core / four GPU fields aligned | 7.7014e-7 — failed | Passed | 4, including two support repeats |

All10 listed processes finish200 steps and exit0. Native checks cover state, time, capacity and momentum; native per-contact force acceptance was not measured. The framework's independent contact-sum residual remains below1e-5 N, with independent pyramid decoding within2.24e-8 N. Successful acquisition is distinct from physical acceptance. [Scores, resource costs and comparisons](evidence/framework-mjwarp/matched-core.json).

Of55 selected GPU fields, four initially differ despite identical CPU models: `body_iquat`, `body_inertia`, `body_invweight0`, and `stat.meaninertia`. This is direct evidence that matching the imported CPU model alone is insufficient. The cube's inertia is nearly isotropic: a different inertia-frame quaternion is not evidence of a large physical inertia error. The ablation assigns only these four fields through official Warp arrays and records source hashes and before/after values. All55 selected values/dtypes and the selected compilation options then match at initialization and after the first step. This is **not** equality of every model/internal-state field.

The three aligned native support processes have exactly equal recorded steps and the same failed residual. Their maximum translation difference from the framework/MJWarp path is8.0851e-5 m; maximum linear-velocity vector difference is.019214 m/s. No-floor traces match exactly across paths. Therefore these four input differences do not explain the entire support divergence, and this numerical failure is not exclusive to the framework. State synchronization, other internal fields and solver behavior remain to be isolated in [#152](https://github.com/huangkiki/Dexlab/issues/152); no sole-framework or engine-defect conclusion follows.

Clocks remain consistent: GPU error after200 steps is2.265e-7 s and framework error is below1.4e-16 s. The initial CPU model says2 ms; effective stepping is1 ms. Initial CPU configuration alone would give the wrong clock diagnosis.

## CPU contact readback correction

In this3.11.0 fixture, `get_data_into` assigns contiguous CPU constraint addresses even when some detected GPU contacts are inactive. The retained Newton step80 has GPU addresses−1,−1,0,4 but CPU addresses0,4,8,12 with only8 constraints. **CPU force values from the out-of-bounds addresses are unavailable observations.** The v0.56 report's zero/numeric interpretation and its combined mismatch frame counts are superseded by this bounds audit; the original records and release are preserved.

v5 exposed this by producing a different invalid CPU value while every primary state/force observation stayed identical. Remaining v5 cases were stopped. v6 checks the full pyramid address width before calling the CPU force API and stores `null` when invalid. The offline auditor applies the same rule to old files. There are22 invalid CPU contact records in the Newton support case and5 in the MJWarp case. Among valid addresses, mismatches remain in0 and172 frames respectively; validity alone does not prove that a converted address refers to the correct contact. Original GPU forces remain authoritative. v4 and v6 primary states, generalized forces, clocks and counts are exactly equal for all four cases.

## Resources and retained history

Framework v6 uses the frozen16 GiB/four-core/256-task profile selected from the earlier6.252 GiB peak. Native matched cases initially use16 GiB; their measured1.147 GiB peak selects8 GiB for the next aligned batch, with four CPU equivalents and128 tasks. All profiles disable swap and retain8 GiB admission reserve. Memory events, CPU throttling, pressure, GPU memory and I/O telemetry are saved. Whole-process times include initialization, caches, observation and shutdown and must not be used as solver throughput comparisons.

The inherited six-hour/64-start ledger contains33 starts and4,400 recorded updates. It retains initialization/shutdown failures, the partial v5 batch and a zero-step native dependency failure fixed by installing `packaging` in the owned environment. The previous v0.56 delivery remains immutable. [Development history](evidence/framework-mjwarp/development-history.json).

## Evidence and reproduction

The [v0.57.0 evidence archive](https://github.com/huangkiki/Dexlab/releases/tag/v0.57.0) preserves all generations, frozen protocols/source, USD/MJCF/MJB assets, effective parameters, raw states/contacts, failures and resource receipts. [Archive identity](evidence/framework-mjwarp/archive.json). Public path/UUID redactions list original and published hashes; numerical measurements are unchanged.

Run from a DexLab checkout using the qualified compatible runtime. Set `ISAAC_ROOT`, `OUT`, `EVIDENCE` (the extracted archive) and `DATA_DIR` to your own absolute paths, with a block device for `IO_DEVICE`. `OUT` must be new; the system Python used for offline scoring needs NumPy. The example passes CUDA/Python paths inside the bounded child because the resource runner does not inherit them from the calling shell. The old receipt is a measurement for choosing the frozen profile, not a claim about another host's free memory:

```bash
CASE_ID=newton-support
CPUS=$(python3 -c 'import os; print(",".join(map(str, sorted(os.sched_getaffinity(0))[:4])))')
mkdir "$OUT"
cat > "$OUT/privacy.toml" <<'TOML'
[privacy]
performance = false
personalization = false
usage = false
TOML
python3 scripts/bounded_run.py --profile adaptive --task-limit 256 \
  --cpu-cores 4 --resource-plan "$OUT/resources-plan.json" \
  --peak-receipt "$EVIDENCE/clock-newton-support-v1-resources.json" \
  --data-dir "$DATA_DIR" --io-device "$IO_DEVICE" --timeout 1200 \
  --receipt "$OUT/$CASE_ID-resources.json" -- \
  env PYTHONPATH="$PWD/src" CUDA_CACHE_PATH="$OUT/cuda-cache" \
  LD_LIBRARY_PATH="$ISAAC_ROOT/exts/isaacsim.pip.nv/pip_prebundle/nvidia/cuda_runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  python3 scripts/research_guard.py run \
  --lock "$DATA_DIR/.control/window.lock" --kind qualification \
  --receipt "$OUT/$CASE_ID-window.json" -- \
  taskset -c "$CPUS" bash "$ISAAC_ROOT/python.sh" --no-ros-env \
  scripts/probe_isaac_mjwarp.py --protocol configs/framework-clock-probe-v6.json \
  --case "$CASE_ID" --output "$OUT/$CASE_ID" --warp-cache "$OUT/warp-cache" \
  --portable-root "$OUT/kit-state-$CASE_ID" \
  --/log/file="$OUT/$CASE_ID-kit.log" \
  --/telemetry/enableAnonymousData=false \
  --/structuredLog/privacySettingsFile="$OUT/privacy.toml" \
  --/telemetry/log/file="$OUT/$CASE_ID-telemetry.log"
PYTHONPATH="$PWD/src" python3 -m dexlab.framework_probe_score "$OUT/$CASE_ID"
```

Use the existing research lock for acquisition and keep transfers/scoring separate. To run the other frozen cases, set `CASE_ID` to `newton-no-floor`, `mjwarp-support` or `mjwarp-no-floor` and repeat only the acquisition and scoring commands. Reuse the same frozen resource plan and caches, and keep separate case outputs, receipts and Kit state. Never overwrite an earlier attempt. The scorer intentionally exits nonzero on either failed support case. The acquisition launcher used four allowed CPUs, four BLAS threads, per-session vendor analytics disabled, and resource telemetry enabled; the archived invocation/receipts retain these choices. New reproduction must freeze equivalent launch settings and verify official source/binary hashes first.

For the native matched path, use a separate Python3.12 environment with the audited MuJoCo/MJWarp3.11.0 packages, NumPy and `packaging`; explicitly select the audited vendor Warp1.16.0 package instead of assuming PyPI binaries are equal. Set `NATIVE_PYTHON` and `WARP_VENDOR` to those absolute paths. Use a separate new native `OUT`, the existing research lock and a frozen resource plan. After declaring `CPUS` as above:

```bash
CASE_ID=mjwarp-support
mkdir "$OUT"
python3 scripts/bounded_run.py --profile adaptive --cpu-cores 4 \
  --resource-plan "$OUT/resources-plan.json" \
  --peak-receipt "$EVIDENCE/native-mjwarp-support-v2-resources.json" \
  --data-dir "$DATA_DIR" --io-device "$IO_DEVICE" --timeout 1200 \
  --receipt "$OUT/$CASE_ID-resources.json" -- \
  env PYTHONPATH="$PWD/src:$WARP_VENDOR" \
  PYTHONPYCACHEPREFIX="$OUT/python-cache" CUDA_CACHE_PATH="$OUT/cuda-cache" \
  OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  LD_LIBRARY_PATH="$ISAAC_ROOT/exts/isaacsim.pip.nv/pip_prebundle/nvidia/cuda_runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  python3 scripts/research_guard.py run \
  --lock "$DATA_DIR/.control/window.lock" --kind qualification \
  --receipt "$OUT/$CASE_ID-window.json" -- \
  taskset -c "$CPUS" "$NATIVE_PYTHON" -s scripts/probe_native_mjwarp.py \
  --protocol configs/native-mjwarp-aligned-v1.json --case "$CASE_ID" \
  --source-case "$EVIDENCE/clock-$CASE_ID-v4" \
  --output "$OUT/$CASE_ID" --warp-cache "$OUT/warp-cache"
PYTHONPATH="$PWD/src" python3 -m dexlab.framework_probe_score --native-state "$OUT/$CASE_ID"
```

The original-input variant selects `configs/native-mjwarp-matched-v1.json`; the negative selects `mjwarp-no-floor`. Use fresh output/receipt names and the same frozen plan within a batch. Support scoring intentionally exits nonzero. These commands reproduce diagnostics, not the still-pending task qualification.
