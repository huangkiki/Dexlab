# Genesis CUDA diagnostics

[English](GENESIS_GPU.md) | [简体中文](GENESIS_GPU.zh-CN.md)

Official Genesis 1.4.3, Quadrants 1.3.3, PyTorch 2.9.1+cu128, CUDA 12.8, RTX 4090; FP64, seed 0, 1 ms step, elliptic cone, experimental no-slip disabled. No engine patches or CPU fallback. These are primitive initialization and isolation diagnostics, not GPU grasp qualification.

| Case | Acceptance | Result |
|---|---|---|
| One environment | Two resets, all 20 positions and contact forces identical | Pass |
| Two environments | Move only environment 1 by 0.1 m; environment 0 position and force unchanged | Pass |
| Four cubes × two environments | All 40 recorded steps finite and native error masks clear; reset trajectories identical | Pass |
| Deliberately insufficient capacity | Native candidate-contact overflow detected during build | Expected failure detected |

Each cube is 40 mm, density 1000 kg/m³, friction 0.5, initial center height 19.9 mm (0.1 mm overlap with plane). Four cubes have 0.1 m spacing. These engineering inputs are not calibrated hardware properties. Full native options and every sampled observation appear in [raw JSON](../../docs/evidence/genesis-gpu.json).

Requested 32 pairs resolves to one possible pair / five contact points for the one-cube scene, and ten pairs / fifty points for four cubes. Requested one pair in the four-cube scene fails during build with candidate capacity five. This does not test broad-phase overflow or establish a maximum supported batch size. Capacity fields are native internal readbacks and may change between engine versions.

## Stage costs

Existing JIT caches were retained. These are single-run wall times with CUDA synchronization around each measured operation, not cold compilation costs or statistically qualified throughput. Each positive case has two 20-step episodes. The first step is separate; “remaining stepping” totals 39 calls. Observation includes device-to-host lists; checks and reset are separate. Python/import and teardown costs are outside this table.

| Case | Init (s) | Build (s) | First step (ms) | Remaining stepping (ms) | Observations (ms) |
|---|---:|---:|---:|---:|---:|
| Reset | 0.1285 | 1.1621 | 54.05 | 19.00 | 4.43 |
| Isolation | 0.1255 | 1.1595 | 53.80 | 21.43 | 4.60 |
| Capacity | 0.1469 | 0.9513 | 156.29 | 39.77 | 8.72 |
| Overflow | 0.1245 | 0.8644 (failed build) | — | — | — |

Rendering and archival were not executed in these timed windows. Independent scoring ran afterward. No engine-speed ranking follows from these numbers. Continuous grasp media and full GPU pinch acceptance remain separate outstanding work.

## Reproduce

Use a separate CUDA-enabled Python environment with the versions above; run under the documented resource envelope. First run `reset`, then `isolation`, `capacity`, and `overflow`, each with a fresh output directory:

```bash
python src/dexlab/genesis_gpu_probe.py --case reset --output runs/gpu-reset
python src/dexlab/genesis_gpu_score.py runs/gpu-reset/result.json
```

The scorer rejects missing samples, nonfinite observations, cross-environment changes and unrelated exceptions. An expected overflow passes the diagnostic while the physical run remains incomplete. Raw records include the exact runner hash. GPU memory admission still requires desktop headroom; CPU cgroup limits do not impose a global GPU memory limit.
