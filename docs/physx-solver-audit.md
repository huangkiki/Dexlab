# Historical PhysX: solver readbacks and runtime provenance

[简体中文](physx-solver-audit.zh-CN.md) · [Receipt index](physx-historical-receipts.md) · [P0 #126][issue]

**Three standalone SDK controls explicitly read back PGS, TGS and TGS with external forces every position iteration. Historical PhysX evidence therefore does not describe one uniform TGS profile.** Other cohorts often retain iteration/offset configuration but omit the solver name. Surface deformables use a separate API. The exact native PhysX core/build and loaded-library identities remain unrecovered; [#126][issue] stays open for these historical gaps.

## Audit scope and identity layers

The 2026-10-09 read-only audit covers the public PhysX qualification, drive, robot, SDF, contact-detail, apple, cloth, contact-development and normal/transient-response evidence at repository baseline `19c686437e4c40c4af2a8ccebf3272e64d6fb401`. It checks six release archives, repository manifests and retained apple/robot records against published hashes. The [index](physx-historical-receipts.md) lists **145 logical receipt entries**, including reused records and failures; this is not a count of independent successful trials. No physics process, new scoring or threshold change was performed.

| Layer | What the evidence establishes | Limit |
|---|---|---|
| Host and worker | Where recorded: `isaacsim==5.1.0.0`, `isaaclab==0.47.2`, Torch `2.7.0+cu128`; many worker receipts also record `isaacsim-kernel==5.1.0.0` | Early failures and some development receipts omit packages. Do not inherit a later run's versions |
| Adapter | UniSim `1.7.10` where recorded, with cohort-specific source snapshots/patches; later receipts include aggregate code hashes | Version alone does not distinguish adapter changes. Standalone SDK controls and surface simulation do not use the UniSim physics adapter |
| Distribution | The [historical wheel inventory][wheels] records the official `isaacsim_extscache_physics-5.1.0.0` wheel and SHA256 `a4b450c7b33d2ada42e1736ac48e002103aac0b93e4f618d9fa4c212762dc74b` | Distribution inventory is not a per-run attestation of loaded native libraries |
| Integration and native core | The preserved installation's `omni.physx` manifest reports `107.3.26`, consistent with the [official integration registry][registry] | This current inspection does not identify each historical PhysX core. Even the official [107.3 / PhysX 5.6.1 release][release] cannot prove that its binaries ran in a particular record |

Host Python/package versions, integration-extension versions and native SDK versions are separate fields. Native solver precision is not established merely by NumPy output dtype or CUDA device naming.

## Direct solver evidence and source interpretation

The [standalone comparison][controls] contains three separate `run.json`, source and compressed USD snapshots. The source explicitly sets `PhysxCfg(solver_type=...)`; `scene_readback` reads `GetSolverTypeAttr()` and the external-force attribute. The archived USD agrees:

| Record | Historical scene solver | External forces every position iteration | Physics step / configured position, velocity iterations |
|---|---|---|---|
| `pgs` | PGS | false | 1 ms / 8, 2 |
| `tgs-default` | TGS | false | 1 ms / 8, 2 |
| `tgs-substep` | TGS | true | 1 ms / 8, 2 |

The last option changes force application inside solver iterations; it is not eight separate 1 ms Python physics steps. These are USD scene settings, not measured iteration counts or a native convergence trace. The earlier `direct-v1` fixture omitted DriveAPI and is retained as an invalid fixture, not an engine-accuracy result. Its receipt's `completed` status alone cannot qualify it.

The [archived adapter helper][helper] builds IsaacLab `PhysxCfg` without overriding `solver_type`. The preserved, clean IsaacLab source at [`3c6e67bb5c7ada942a6d1884ab69338f57596f77`][isaaclab] defines `0=PGS`, `1=TGS`, default `1`. This explains the TGS source path, **conditional on that source being the historical dependency**. It is not a substitute for the missing per-run dependency identity or solver-name readback. The helper's `read_engine_solver_values` reads USD settings but omits solver type; many import reports consequently contain `solver.requested=null` and `solver.effective=null`. Neither value means PGS, zero iterations or a failed simulation.

## Cohort-specific settings and changes

Here, **8/2** denotes configured position/velocity iteration values, not achieved counts. Values apply to records that contain them; missing early receipts remain missing in the index. A report's “TGS” profile text is an attribution, not an independent runtime measurement.

| Public cohort / receipt entries | Settings and representation | Adapter/evidence boundary |
|---|---|---|
| [Primitive qualification][primitive] / 5 | 1 ms, 8/2, contact offset 1 mm, rest offset 0 in the three valid imports | Three completed cases and two original admission errors. Contact-report/role-cache fix; solver name absent |
| [Pinch v2][pinch] / 7 | Frozen source: 1 ms, 3.5 s; finite primitive fingers, 8/2 and 1 mm/0 offsets where recorded | Original/revised qualification and error retained; same contact-report fix. Do not pool different protocol rounds |
| [Drive v1][drive] / 13 | Three explicit controls above, two earlier SDK diagnostics, eight adapter qualification/regression receipts | Native force-timing option; default velocity failure retained. Direct SDK and adapter records remain distinct |
| [Robot v0.7.0][robot] / 9; parent-filter repeat / 1 | Final records: 1 ms, 8/2, per-iteration external force; convex colliders/frame reduction; unloaded 54-joint motion | Archive includes two rejected imports and one import-only receipt. Later collision-filter repeat is separate; neither qualifies loaded SDF grasping |
| [SDF v0.8.0][sdf] / 16 | SDF resolution 256/subgrid 6 versus convex negative control; 8/2 and force timing where recorded; later 0.1 mm/0 offsets | Two early errors; includes a 20-step robot import, not loaded grasp acceptance. Earlier missing offsets are not backfilled |
| [Contact details][details] / 1 | 1 ms, 8/2, 0.1 mm/0 offsets; normal contacts and friction anchors are distinct | Adapter copies normal buffers before the friction getter reuses SDK storage. Solver name absent |
| [Apple development and public grasp][apple] / 20 | Mostly 1 ms, one 0.5 ms development case; final 8/2, 0.1 mm/0 offsets, minimum torsional radius 1 mm, force timing enabled | Collision exclusions, SDF transport and torsion options vary. Final receipt and 107 artifacts match the published manifest; full raw arrays remain locally retained, not publicly downloadable |
| [Surface cloth v0.11.0][cloth] / 54 | Triangle-surface `OmniPhysicsSurfaceDeformableSimAPI`, 16 body position iterations; 0.5/0.25/0.125 ms; rest/contact offsets = case radius / twice radius | Direct SDK surface API, not rigid-body PGS/TGS attribution. Authored mass is not native nodal-mass readback; `physx-surface` is a task profile name |
| [Contact development v0.12.0][development] / 10 | Nine completed PhysX records: four plane, one indentation, four cylinder; baseline 0.5 ms, 1 ms control; 8/2 and 0.1 mm/0 offsets | One sensor admission error retained. Native adapter identity/source aggregate recorded; normal/friction observations remain separate |
| [Normal response v0.13.0][normal] / 5 | 0.5 ms and one 0.25 ms case; 8/2, 0.1 mm/0 offsets; force-based compliant contact, 5,000 N/m and 2 N·s/m per constraint | UniSim compliance extension; parameters from composed USD, not native material tensors. 0.4 kg settling and inertia failures retained |
| [Transient response v0.14.0][transient] / 4 | Three force-spring cases at 0.5/0.25/0.125 ms with damping 10 N·s/m; separate inertia repeat retains damping 2 | Precision extension writes compiled inertials at 17 significant digits. This fixes adapter serialization, not PhysX precision; old failures remain |

The cloth archive contains **42 `completed`, 10 `unsupported`, one `preparing` and one `running`** receipt. The last two are sealed historical intermediate states, not currently running jobs or completed experiments. “Completed” does not mean “passed”; the published surface-crossing failures and repeat disagreement remain unchanged.

The original contact-report patch SHA256 is `3042eb5d1078c605d18069ac76ae3ac2625ceb99a6c7f18c8cf9961939b39a08`. Later normal-response adapter code hashes are `5397e9754f1633d90cf907c2098247f39995b3858b4a61bd6628f2f8644d6aac` (v0.13) and `6092ace9eda2a14b0721e545c19ca480bb1efaeda27d90feabc0186ecc9cefa0` (v0.14). Do not apply the latest combined patch identity to earlier cohorts. Cloth receipts instead record native API source hashes for `deformableUtils.py` and the tensor API; those are not hashes of the PhysX core.

Later [friction response][friction], [response–cost][cost] and [paired transfer][transfer] studies explicitly exclude PhysX pending stable-runtime qualification. They add no PhysX trials to this inventory.

## Timing, observations and archive verification

Most adapter timing is declared step size times synchronous completed steps, not a native clock readback. Contact getters expose the latest completed substep; normal-contact points and friction anchors must not be paired one-to-one. The [contact-detail report][details] checks force accounting against observed velocity changes. That does not recover missing actuator-force history or native convergence telemetry. USD iteration bounds and offset settings are configuration evidence, even when a legacy provenance label says “native runtime readback.”

All six complete archive sizes/SHA256 values and all manifest entries were verified. Tar hardlinks were resolved as logical files without executing payloads. Repository manifests additionally verified 52 primitive, 89 pinch and 132 drive entries, including the drive manifest's decompressed log/USD checks. The apple final manifest verified its receipt plus 107 native artifacts; the two development indexes verified 11 receipt hashes and nine state-array hashes. The separate parent-filter repeat matched both published receipt/state hashes.

| Release archive | Bytes | SHA256 | Manifest entries verified |
|---|---:|---|---:|
| [v0.7.0 robot][a7] | 26,639,986 | `239065360b79dbb146550684a16a9d09a3022af52da55214d29c16f734bbd3c8` | 576 |
| [v0.8.0 SDF][a8] | 2,508,468 | `1275587a5236d8523ca7d2f3060a837c8c0267667dfe6ed8d02c5f7fe97c6ae6` | 365 |
| [v0.11.0 cloth][a11] | 280,621,732 | `07bb00d45c487cae3ab1a4ee987eaade24f5f37ed23c4d11970fee3690ff134e` | 1,840 |
| [v0.12.0 contact][a12] | 136,594,576 | `5a836c146ed5b726d29f60813322e68e4cb03a1ba7f9c8f301c379ec4e003279` | 709 |
| [v0.13.0 normal][a13] | 3,928,405 | `8d6b187dc6f9ce6f2e6d1175a07bac4c5a838f953b22e4dd88f00feb7dd97f7a` | 342 |
| [v0.14.0 transient][a14] | 3,638,099 | `2e5e1934d43e05fb0d4f86ce3f36603384fcf55b514d8cfba8af29b5d71bc199` | 276 |

## Remaining blocker and recovery

[#126][issue] retains two specific questions: **which native core/build/libraries were loaded for each cohort, and which solver was selected in records lacking explicit readback?** Required evidence is a contemporaneous, record-bound native version/build or library inventory and solver configuration snapshot. Reviewed source attribution may bound an interpretation, but must not be labeled a recovered historical observation. Available archived logs did not supply the missing core identity; a referenced full SDK application log was not retained at its recorded location. A new probe cannot create old evidence.

The independent new [protocol #131](https://github.com/huangkiki/Dexlab/issues/131) and [qualification #132](https://github.com/huangkiki/Dexlab/issues/132) should record authored and effective settings separately, identify available loaded native binaries and source, and name unavailable fields before freezing. This historical blocker is not a blanket dependency for newly qualified evidence. No formal pinch-campaign budget was consumed by this audit.

[issue]: https://github.com/huangkiki/Dexlab/issues/126
[registry]: https://docs.omniverse.nvidia.com/kit/docs/kit-registry-reference/latest/107/shared.html
[release]: https://github.com/NVIDIA-Omniverse/PhysX/releases/tag/107.3-physx-5.6.1
[isaaclab]: https://github.com/isaac-sim/IsaacLab/blob/3c6e67bb5c7ada942a6d1884ab69338f57596f77/source/isaaclab/isaaclab/sim/simulation_cfg.py
[wheels]: ../demos/physx-contact/evidence/sdk-wheel-sizes.json
[controls]: ../demos/physx-contact/evidence/drive-v1/native-drive-comparison-v1/
[helper]: ../demos/physx-contact/evidence/drive-v1/qualification/substep/unisim-physx-solver.py
[primitive]: ../demos/physx-contact/README.md
[pinch]: ../demos/physx-contact/pinch.md
[drive]: ../demos/physx-contact/drive.md
[robot]: ../demos/physx-contact/robot.md
[sdf]: ../demos/physx-contact/sdf.md
[details]: ../demos/physx-contact/contact-details.md
[apple]: ../demos/physx-contact/apple.md
[cloth]: ../demos/physx-contact/cloth.md
[development]: ../demos/contact-benchmark/README.md
[normal]: ../demos/contact-benchmark/NORMAL_RESPONSE.md
[transient]: ../demos/contact-benchmark/TRANSIENT_RESPONSE.md
[friction]: ../demos/contact-benchmark/evidence/friction-response-v1.json
[cost]: ../demos/contact-benchmark/RESPONSE_COST.md
[transfer]: ../demos/contact-benchmark/TRANSFER.md
[a7]: https://github.com/huangkiki/Dexlab/releases/download/v0.7.0/v0.7.0-robot-articulation-evidence.tar.gz
[a8]: https://github.com/huangkiki/Dexlab/releases/download/v0.8.0/v0.8.0-sdf-contact-evidence.tar.gz
[a11]: https://github.com/huangkiki/Dexlab/releases/download/v0.11.0/v0.11.0-physx-cloth-evidence.tar.gz
[a12]: https://github.com/huangkiki/Dexlab/releases/download/v0.12.0/v0.12.0-contact-development-evidence.tar.gz
[a13]: https://github.com/huangkiki/Dexlab/releases/download/v0.13.0/v0.13.0-normal-response-evidence.tar.gz
[a14]: https://github.com/huangkiki/Dexlab/releases/download/v0.14.0/v0.14.0-transient-response-evidence.tar.gz
