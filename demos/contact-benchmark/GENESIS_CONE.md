# Genesis friction-cone diagnostic

[简体中文](GENESIS_CONE.zh-CN.md)

This staged contribution to #42 investigates a primitive block's vertical transient after a horizontal velocity kick. It does not qualify SDF grasping, joints, GPU batching, cloth, or hardware accuracy.

Official Genesis 1.4.3 / Quadrants 1.3.3, CPU FP64, seed 0, deterministic mode requested. A 50 mm cube of density 1000 kg/m³ settles for 0.5 s on a plane. Both materials have μ=0.5; gravity is 9.81 m/s². The step is 5 ms, substeps 1. Newton constraint solver, approximate-implicitfast integrator, 25 iterations, no-slip postprocessing disabled. Full resolved options are recorded. Geometry is primitive box/plane, not SDF-SDF.

Four controls reset the same scene: no velocity write, zero all velocities, set x velocity to 0.5 m/s while zeroing other components, and change only x velocity. Repeat with pyramidal and elliptic friction cones. Observe every step for 0.2 s. The conditional reference is vₓ=max(0.5−μgt,0), assuming pure translation and flat contact. Rotation limits its interpretation; no measured material reference exists.

## Preliminary measurements

| Cone | First normal force (N) | First vertical speed (m/s) | Maximum reference velocity discrepancy (m/s) |
|---|---:|---:|---:|
| Pyramidal | 6.142033 | 0.196631 | 0.098316 |
| Elliptic | 1.226250 | ~0 | 0.000879 |

These are earlier local diagnostic measurements, pending public raw-data delivery and release validation. They support a configuration-dependent transient in this scene, not an engine ranking. The no-write and zero-write controls remained settled; both kick APIs gave essentially the same transient. The earlier one-second, 5 ms/high-friction test failed its frozen 0.05 m/s discrepancy threshold and remains a failure. A separate μ=0 attempt was rejected by the official validator (minimum 0.01); low friction is not frictionless. Reset pairs matched on this host; cross-host determinism is unverified.

## Reproduce

Use an isolated Python 3.12 environment with DexLab editable and official `genesis-world==1.4.3`; the tested Torch package was 2.9.1+cpu. Apply the repository's bounded-run resource admission before executing. Installation alone does not establish latest-version or native-binary provenance; retain package hashes with evidence.

```bash
python -m dexlab.genesis_cone_probe /path/to/new-output
python -m dexlab.genesis_cone_score /path/to/new-output
```

The runner refuses existing output, records source hash/settings and all eight traces, and preserves exceptions. Scoring is a separate standard-library process and rejects missing/nonfinite samples. It reports discrepancies, not an overall physical-success flag. Build/init, stepping and observation times are separated; rendering and archiving are absent. These short CPU timings are not throughput benchmarks. Joint/pinch/release, capacity/isolation, continuous media and GPU checks remain outstanding.

## Evidence delivery

The public runner reproduced all eight diagnostic traces. [Scores](../../docs/evidence/genesis-cone-score.json) and [archive manifest](../../docs/evidence/genesis-cone-manifest.json) are included. The 406,767-byte raw archive contains 36 hash-verified records, including earlier failures; its GitHub Release attachment is pending publication. The archive is a same-disk delivery copy, not an independent backup.
