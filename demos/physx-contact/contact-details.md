# Contact forces and loaded apple diagnostics

[English](contact-details.md) | [简体中文](contact-details.zh-CN.md)

This page retains the v0.9.0 force records and failed grasps. See the later [PhysX SDF grasp](apple.md) for the passing case, reproducible runner and controls.

Native normal contacts and tangential friction anchors are now recorded separately through an explicit UniSim adapter extension. A sliding-block momentum check passes. The loaded OpenArm/Wuji development runs **do not pass continuous apple-grasp acceptance**; transient lifting is not success.

## Reproduce the force check

```bash
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_contact_details run --output demos/physx-contact/runs/my-contact-details
# Offline verification of bundled raw observations; no Isaac Sim required
.venv/bin/python -m dexlab.physx_contact_details verify demos/physx-contact/evidence/contact-details-v1
```

The 0.2 kg block settles for 0.1 s, receives an initial horizontal speed of 0.5 m/s, then evolves freely for 0.25 s at 1 ms. Friction is 0.3; the reported TGS profile has 8 position / 2 velocity iteration settings ([source attribution versus missing solver-name readback](../../docs/physx-solver-audit.md)), external forces every position iteration, 0.1 mm contact offset and zero rest offset. These are engineering settings, without measured-material calibration. The block's link and mass-center origins coincide. From each actual velocity change, independently recompute `m * Δv / dt - F_normal - F_friction - m * g`.

The maximum residual is **0.000029445 N**, or **0.00150% of weight**, below the declared 1% engineering limit. Peak friction is 0.58862 N. [Raw records, source snapshots and frozen checks](evidence/contact-details-v1/summary.json) are bundled; failures return nonzero, existing output directories are never overwritten. A small residual checks force accounting, not physical accuracy against hardware. It excludes the settling interval and the commanded initial-velocity change.

## Adapter boundaries

Official PhysX and IsaacLab remain unchanged. The [disclosed UniSim patch](../../scripts/patches/unisim-1.7.10-physx-adapter.patch) adds `enable_contact_details(entity, capacity=8192)` and `get_contact_details()` for one explicitly selected single-body rigid entity in one mapped environment, already covered by a declared contact sensor. The native view filters all other declared colliding bodies. Unsupported scope and invalid or possibly saturated buffers fail explicitly.

Normal contacts and friction anchors are different native records, with world-frame forces in N and points/separation in m. They are not paired one-to-one. The adapter copies normal buffers before querying friction because the SDK can reuse their count/index storage. Diagnostics poll every physics substep; the getter returns only the latest completed substep, not all intermediate substeps. This qualification calls once per physics step. Existing normal-force sensors retain their original meaning.

The adapter passes Ruff, mypy, Pyright, 1,330 tests (92 optional-runtime skips), and package build. Patch replay against pinned UniSim commit `dc41b5e79d58d9b58eba9b2f27d10d71e16cf03d` reproduces the full diff. These are local checks, not upstream approval. Setup uses a new `UniSim-physx-grasp` directory and preserves older adapter checkouts.

## Robot collision semantics

MuJoCo implicitly filters same-weld and, by default, parent-weld body pairs. An MJCF importer preserving only explicit exclusions loses those semantics. The compiled-model transfer now materializes source-implied pairs without disabling articulation self-collision. This robot adds 21 pairs to its 246 explicit exclusions; native USD readback matches all **267 pairs**, without missing or additional pairs. Conflicting explicit geom-pair overrides are rejected instead of silently discarded.

## Failed loaded grasp experiments

All runs use actual native body/joint states, SDF apple and right finger pads, a free apple, the table and a scripted known-state control prior. The distant floor is omitted. Initial preparation is inherited from the existing MuJoCo/SuperDex scene, not an independent PhysX scene generator. Control uses source compiled gains, target-velocity feedforward and one settling-based arm alignment. No object attachment or post-initialization pose drive is used.

| Development setting | Peak fruit/table clearance | Minimum hold clearance, [11,14) s | Result |
|---|---:|---:|---|
| Alignment height offset 7.25 mm, 1 ms | 0.004 mm | −0.579 mm | Table supports apple |
| Same offset, 0.5 ms | 0.013 mm | −0.887 mm | Table supports apple |
| Offset 12.25 mm, 1 ms | 0.241 mm | −0.835 mm | Stem-tip contact lost during lift |
| Offset 10.25 mm, 1 ms | 126.361 mm | −0.672 mm | Transient lift, then drop |

The offset is a declared control adjustment, not a material parameter. These are tuning experiments, not a success-rate sample. The [development index](evidence/apple-development-v1.json) preserves 11 records, including initialization failure, disabled-self-collision ablation and earlier controls. Full apple arrays and models remain in the local run directories; this public index alone cannot independently rescore or replay the grasp.

Penetration scope matters: initial apple/table native overlap is 1.470 mm in all four runs. Maximum native hand/apple separation penetration is reported separately (0.043, 0.015, 0.032 and 0.103 mm respectively). These native values do not replace common-reference geometric penetration. Old diagnostics that mixed table and hand contacts are retained; revised diagnostics explicitly separate them. Approximate contact locations use post-step body poses; they are not material-point slip measurements. A paired run with/without detailed reporting had bitwise-identical saved state arrays; that observation does not establish invariance for every scene.

Remaining work under [Issue #5](https://github.com/huangkiki/Dexlab/issues/5): stable loaded stem support, a portable complete grasp runner, common-reference penetration and full independent acceptance. The benchmark must count loss during the full hold window as failure, even after a high transient lift.
