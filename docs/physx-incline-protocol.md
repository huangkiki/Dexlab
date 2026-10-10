# Native PhysX incline protocol

[English](physx-incline-protocol.md) | [简体中文](physx-incline-protocol.zh-CN.md)

[#150](https://github.com/huangkiki/Dexlab/issues/150) evaluates four fixed CPU configurations of official **PhysX SDK 5.9.0**, source `517a0073715120e114ee055b63b26c95e00d9039`, tag `110.1-omni-and-physx-5.9.0`. This is a native C++ SDK cohort. It does not identify historical Isaac cores, compare framework conversion, or award coverage-v1 credit. Framework-compatible paths remain [#152](https://github.com/huangkiki/Dexlab/issues/152).

## Model and applicable profiles

The [original nine incline conditions](incline-comparison-protocol.md) remain: a uniform 40 mm, 64 g box, inertia mL²/6, zero local COM, gravity [0,0,-9.81] m/s². Rotate box and infinite plane about +Y, with the bottom initially flush. Run static 15°/μ=.5, sliding 35°/μ=.5 and frictionless 15°/μ=0 at 2/1/.5 ms, for 2 s each; score .5–2 s. A tenth 15°/.5/1 ms case disables cube collision after mass/inertia initialization. There are no drives, damping, sleeping or state writes after initialization. Each case uses a fresh process.

Both shapes use contact offset .0001 m, rest offset zero, equal static/dynamic friction, zero restitution, average material combination and native strong friction. The body uses eight position and two velocity iterations. CPU dispatcher: one worker. Native effective limits, geometry, frames, mass, inertia, material, initial state and scene options are recorded and hash-frozen per case before positive-duration runs. FP32 values are saved with 17 decimal digits; no lossy exported model is reimported.

| Profile | Native solver | Additional setting |
|---|---|---|
| PGS | Projected Gauss–Seidel | Native friction iteration schedule |
| PGS friction | PGS | Friction every iteration |
| TGS | Temporal Gauss–Seidel | Native external-force schedule |
| TGS external | TGS | External forces every iteration |

All four use PCM, enhanced determinism and patch friction. SDK 5.9 retains only patch friction; older one- and two-direction options are unavailable. TGS already processes friction every iteration, so toggling the PGS friction flag is not a separate effective TGS profile. The per-iteration external-force flag is invalid for PGS. These statements follow the frozen SDK's [scene definitions](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/include/PxSceneDesc.h). This CPU cohort makes no GPU qualification claim.

## Observations and frozen acceptance

Copy native contacts and friction anchors inside `onContact`; the stream is transient. `extractContacts` returns **normal impulse only**, while `extractFrictionAnchors` returns separate world-space friction impulses. Sum both with the sign for the cube's position in the actor pair. Never reconstruct contact force from velocity. Record the native flags, channel availability, declared and copied contact counts, patch counts, positions, separation and 256-entry recorder capacity. Missing or truncated observations invalidate the case. Source: [callback API](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/include/PxSimulationEventCallback.h).

The simulation receives an FP32 step. Record its requested value and exact effective value; sample time is N times that effective value, independently checked against `PxScene::getTimestamp()` increments. Check pre/post continuity and absence of post-initialization writes. TGS per-iteration gravity does not implement one final-velocity semi-implicit Euler position update, so that identity is not imposed. This choice was frozen from the SDK documentation before formal outcomes. Model readback tolerance is eight FP32 epsilons times max(abs(expected),1e-8), and impulse-direction checks use 1e-10 N·s absolute tolerance; neither is an iterative error bound.

The existing physical thresholds remain: static displacement/speed .001 m/.001 m/s; sliding position/velocity RMSE .01 m/.01 m/s; acceleration error .05 m/s²; rotation .01 rad; reported contact penetration .001 m; force balance RMSE .01 N; continuous support. The independent state/impulse consistency limit remains **1e-7 N·s**. Penetration comes from the native contact-generation separation, not an additional post-step geometric estimate. All failures and invalid observations remain in the nine-positive denominator. Negative acceptance requires valid observations and rejection of unsupported motion. Fixed configurations use zero outcome tuning; a later shared development/holdout comparison must be separately frozen.

## Build, budget and replay

Official SDK files were compared with the Git source tree before and after compilation. The official archive contains 22 CRLF-normalized Windows command files outside the PhysX subtree; the 2,155 PhysX files match Git bytes exactly. There are no engine patches. GCC 11.4, CMake 3.22.1 and the official `linux-gcc-cpu-only` Release preset build the static SDK. The recorder is project code, not an engine modification.

```bash
cmake -S "$SDK_ROOT" -B "$BUILD" -DPHYSX_PRESET=linux-gcc-cpu-only \
  -DCMAKE_BUILD_TYPE=release -DPX_OUTPUT_LIB_DIR="$BUILD/lib" \
  -DPX_OUTPUT_BIN_DIR="$BUILD/bin" -DPX_OUTPUT_DLL_DIR="$BUILD/bin"
cmake --build "$BUILD" --parallel 4 --target PhysX PhysXExtensions PhysXCooking
bash scripts/build_physx_incline.sh "$SDK_ROOT" \
  "$BUILD/lib/bin/linux.x86_64/release" "$RECORDER"
```

Freeze source, recorder binary, runner, independent scorer, common scorer, admission and resource hashes before running. The batch has four serial profiles, 40 fresh native processes, 92,000 updates and a maximum 1800 s per profile. The measured zero-step admission peak was 46 MiB; the minimum adaptive tier is **8 GiB / four-core quota**, zero swap, plus a separate 8 GiB launch reserve. A new workload starts at 16 GiB, or 24 GiB for complex models; this measured small fixture does not justify reducing those defaults. The six-hour/64-start development package and the pinch research budget remain separate.

Use the existing bounded runner and cooperative research window for each profile; keep local deployment paths private:

```bash
python scripts/bounded_run.py --profile adaptive --resource-plan "$NEW_PLAN" \
  --peak-receipt "$MEASURED_RECEIPT" --cpu-cores 4 --timeout 1800 \
  --data-dir "$DATA_DIR" --io-device "$DATA_DEVICE" --receipt "$RESOURCE_RECEIPT" -- \
  python scripts/research_guard.py run --lock "$RESEARCH_LOCK" \
  --kind qualification --receipt "$WINDOW_RECEIPT" -- \
  python -m dexlab.physx_incline --protocol frozen-v1/pgs.json \
  --proof reports/official-proof.json --binary "$RECORDER" --output "$NEW_OUTPUT"
```

Binary hashes are build-specific: a rebuilt recorder requires new admissions and a prospective identity freeze, not editing an old campaign. The archive's scoring source and NumPy 2.5.3 allow engine-free replay:

```bash
PYTHONPATH=frozen-v1/scoring-source python -m dexlab.physx_incline_score \
  --input campaign-v1/pgs --output score.json
```

Native step timing includes simulate/fetch and contact copying, excludes JSON output/compression, and is serialized against other research work. Whole-service cost includes orchestration and compression between native cases. Neither is a cross-engine throughput ranking. See the [results and retained failures](physx-incline-results.md).
