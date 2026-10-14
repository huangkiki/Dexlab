# PhysX loaded joint drive

[English](drive.md) | [简体中文](drive.zh-CN.md)

The [historical solver/version audit](../../docs/physx-solver-audit.md) separates native scene readbacks, source/report TGS profiles and missing fields; [P0 #126](https://github.com/huangkiki/Dexlab/issues/126) retains contemporaneous core/loaded-library identity gaps.

A fixed-base prismatic joint runs through UniSim and official Isaac Sim 5.1. Enabling native per-iteration TGS external forces passes independent acceptance for the complete two-second record. The default setting fails the stationary-velocity check; its record is retained. This qualifies an ideal single joint, not OpenArm/Wuji actuators, drives in contact, or apple grasping.

## Finding and native control

Under a constant 1 N load, equilibrium is near `0.01 − 1/500 = 0.008 m`. Default TGS stops changing position but reports about 4.29 mm/s. An independent USD scene bypassing DexLab, UniSim and MJCF conversion reproduces this. IsaacLab cached observations and raw PhysX tensors agree exactly at every sample.

| Independent SDK configuration | Mean steady position | Mean reported velocity |
|---|---:|---:|
| TGS, default force timing | 8.000806 mm | 4.293650 mm/s |
| TGS, external forces every position iteration | 7.999971 mm | 0.001418 mm/s |
| PGS control | 8.000002 mm | −0.000115 mm/s |

PhysX documents this discrepancy when external forces are applied once per frame but spring forces are applied over TGS substeps, and explains the `enableExternalForcesEveryIteration` option. [Official mechanism](https://nvidia-omniverse.github.io/PhysX/physx/5.7.0/docs/Simulation.html#tgs-steady-state-velocity-and-position-discrepancy). This supports attribution for this isolated experiment; it does not validate every scene. Small FP32 differences do not establish hardware accuracy.

## Protocol and parameter provenance

- Moving mass 0.1 kg, fixed base, no contact, gravity, attachment or state resets during motion. Inertia follows homogeneous box geometry.
- Native implicit position drive: `kp=500 N/m`, `kd=10 N·s/m`, maximum force 2 N, travel ±20 mm. The target is initially 10 mm and returns to zero at 1.5 s.
- External load is −1 N during [0.5, 1.0) s, −3 N during [1.0, 1.04) s, and zero otherwise.
- Timestep 1 ms, position/velocity iterations 8/2; actual joint and body state recorded at every step, 2,000 samples total.

These are declared engineering test parameters, not calibrated robot motor properties. Acceptance tolerances were frozen before qualification: equilibrium error <50 μm, stationary velocity <0.1 mm/s, joint/body position error <1 μm and velocity difference <1 μm/s. The drive force inferred from `m a − F_external` during the short saturated interval must be within 2 N ±0.05 N. This is not native actuator-force measurement or a complete motor characterization.

Default force timing fails only loaded stationary velocity. Per-iteration timing passes all 21 checks, with inferred overload drive force 2.000002 N. The new adapter option is disabled by default. All six existing rest, sliding, zero-friction, pinch, overload and release qualifications were rerun with the new package and passed their original thresholds.

## Implementation and reproduction

The [combined adapter patch](../../scripts/patches/unisim-1.7.10-physx-adapter.patch) retains contact reporting and adds the public `isaacsim_external_forces_every_iteration` argument. Both host and worker validate a boolean, author the native scene before initialization, and verify USD readback. `None` retains the SDK default, `False` explicitly disables it, and `True` enables it. PhysX source and binaries are unchanged.

Setup defaults to a new `UniSim-physx-drive` source directory, preserving the old adapter checkout. An explicit `DEXLAB_UNISIM_SOURCE` must match the pinned upstream commit and complete new patch. Adapter checks passed Ruff, mypy, Pyright, 1,313 tests (92 optional SDK skips) and packaging. Setup replay passed in the populated environment; a fresh-machine install was not rerun.

```bash
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_drive run --force-timing substep \
  --output demos/physx-contact/runs/drive-substep
.venv/bin/python -m dexlab.physx_drive verify demos/physx-contact/runs/drive-substep
# Preserve the default control; currently expected to exit 1, not be relabeled a pass
.venv/bin/python -m dexlab.physx_drive run --force-timing default \
  --output demos/physx-contact/runs/drive-default
```

The [complete evidence and SHA-256 manifest](evidence/drive-v1/manifest.json) contains both drive qualifications, six contact regressions, three independent SDK controls, source snapshots, USD scenes and logs. Logs and exported USD scenes are losslessly gzip-compressed, with decompressed hashes recorded separately. The first independent SDK fixture omitted `DriveAPI` and is invalid for engine evaluation; its record and shutdown handling are preserved. Subsequent valid fixtures explicitly create native drives.

```bash
# Recheck packaged passing and failing records without starting the SDK
.venv/bin/python -m dexlab.physx_drive verify demos/physx-contact/evidence/drive-v1/qualification/substep
.venv/bin/python -m dexlab.physx_drive verify demos/physx-contact/evidence/drive-v1/qualification/default
```
