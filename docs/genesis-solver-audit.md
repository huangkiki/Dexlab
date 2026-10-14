# Genesis force-limit solver audit: recorded selection and resolved defaults

[简体中文](genesis-solver-audit.zh-CN.md) · [Historical results](force-limit-results.md) · [Audit #125][issue]

The sixteen archived cases record **Newton (`constraint_solver=1`), `approximate_implicitfast` (`integrator=2`), elliptic friction and zero noslip iterations**. These names are resolved against the exact official source matching the historical wheel, not today's defaults. The archive contains the caller's options object; it does **not** contain every resolved solver setting. The reviewed boundary in [#125][issue] retains the absent native readbacks and accepts the explicitly labeled matching-source interpretation below.

## Identity and evidence scope

The [original wheel proof](evidence/force-limit/official-proof.json), recorded on 2026-10-07, identifies `genesis-world==1.4.3` and wheel SHA256 `26a8229031d66535a568fbdd15b9dcf506843fb91b739a6d4ec7a4a015bf5eb8`. The 2026-10-09 read-only audit verified this cached wheel and all **264** Python source hashes. Every file also matches its Git blob at official [v1.4.3 source commit](https://github.com/Genesis-Embodied-AI/genesis-world/tree/216a708e06124595521a9d36a51fae5393fd4ff8) `216a708e06124595521a9d36a51fae5393fd4ff8`. The preserved installation still matches those files; this present-day check is separate from the historical proof.

All **126** entries in the [artifact manifest](evidence/force-limit/artifact-hashes.json) passed SHA256 verification. Sixteen independent case records contain 8,000 samples each, **128,000** total, with identical archived `initial.options`. Every case's archived runner and challenge manifest match [frozen hashes](evidence/force-limit/frozen.json):

| Artifact | SHA256 |
|---|---|
| Historical runner `genesis_pinch_probe.py` | `e195c50b5fb03a38c5e29914655d491f47f106cc3330225645c45f2def23528f` |
| Independent scorer `genesis_pinch_score.py` | `988ec53e28d2ed4bae9249dba95ae6ff45ea8d5e98657abaebe475d0b4a3fb85` |
| Challenge `force-limit-v1.json` | `2ed2d8d1c608d16aaacf052d92777b55398dca1cef7e71df361f7e4e70d14e76` |

[Case protocols](evidence/force-limit/cases/) and [package inventory](evidence/force-limit/installed-packages.json) identify Genesis 1.4.3, Quadrants 1.3.3 and Torch 2.9.1+cpu. Quadrants is the kernel compilation dependency, not an additional physics engine. These records establish package/source identity; they do not contain a reproducible build or hashes of every historical JIT machine-code artifact.

## Recorded versus source-resolved settings

**H** means a value in the historical record, including caller configuration; **S** means a conclusion derived from matching source plus the frozen caller/scene. H is not automatically native readback. Neither S nor a future reconstruction fills a missing historical field.

| Field | H: archived value | S: matching-source interpretation |
|---|---|---|
| Rigid solver | `constraint_solver=1` | [Newton][enums]; no explicit solver override in the frozen runner |
| Integrator | `integrator=2` | [`approximate_implicitfast`][enums], distinct from `implicitfast=1`; [documented approximation][options] |
| Friction / noslip | `friction_cone=1`, `noslip_iterations=0` | Elliptic; the additional noslip pass is disabled, friction is still active |
| Backend / arithmetic / clock | CPU, FP64, seed 0; dt 0.0005 s; 8,000 steps | Frozen runner requests deterministic algorithms; SimOptions uses one substep; no universal determinism claim |
| Iteration budgets | 25 solver iterations; line search 50, tolerance 0.01 | [Early termination][body] is allowed; these are ceilings, not measured iteration counts |
| Solver tolerance | `null` | [FP64 resolution][tolerance] gives 1e-9 with MuJoCo compatibility disabled; [scaled convergence rule][exit], not an absolute force threshold |
| Contact resolution | `null`; elliptic, Newton, MuJoCo compatibility false | [Resolution][resolve] selects Signorini: normal row plus friction disc, updated against developed normal force |
| Tangential/normal impedance ratio | `impratio=null` | [Resolution][resolve] gives 100 for this configuration |
| Sparse representation / execution body | `sparse_solve=null`; CPU; three-DoF gripper plus free cube | [Topology and CPU rules][static] select sparse representation and monolithic body; Newton Cholesky path, not CG; no per-step factorization telemetry |
| Extra contact modes | Torsional/rolling friction false; hibernation false | Those optional terms/passes are disabled |
| Geometry material data | Native geometry friction readbacks all 0.5; plane/cube time constant 0.002 s; joint 0.01 s | Combined-contact values follow the source rule below; they were not separately logged |

Why are the resolved values absent? The runner saves `options.model_dump(...)` from the object passed to Scene. [SceneOptions][copy] makes a [field-preserving copy][copy-fields], inheriting unset shared fields from SimOptions. The solver resolves its own copy afterward. Thus the saved `null` tolerance/contact-resolution/impratio/sparse fields are not evidence of zero values or unresolved runtime behavior. They remain missing **native readbacks**; the S column describes the conditional source path and preserves that distinction.

## Contact law and force epochs

The matching [contact combiner][pair] uses `max(mu_a * ratio_a, mu_b * ratio_b, 0.01)`, averages geometry solver parameters, and floors the combined time constant at twice the substep. Consequently a future nominal-zero-friction case must not assume an effective zero coefficient. Elliptic cone shape alone does not specify the normal/friction coupling; this source's Signorini resolution and impedance ratio affect that interpretation. Equal nominal μ does not establish equivalence to MuJoCo or SuperDex materials.

Each archived row is collected after `scene.step()` and labeled `(step+1)*dt`. [Contact finalization][forces] computes per-contact forces and accumulates net link force; [the post-solve step][post] then integrates the state. The [getters][api] return the saved contact solve and current state. Therefore:

- Pose and velocity belong to the end of the step. Contact force belongs to the solve used for that step's update, not a fresh solve at the final pose.
- Contact position/normal/penetration describe the collision/solve geometry before that integration. The scorer's analytic table depth uses the recorded final pose; these depths do not have identical epochs.
- The contact ledger checks the sum on the cube against its native net contact force to **1e-8 N**. It verifies accounting consistency, not independent physical truth.
- The momentum check pairs that step's contact force and gravity with `m * (v_after - v_before)`, using the initial velocity for the first row. Its **5% weight-impulse** allowance is separate from solver tolerance and the force ledger.

The historical controller is Genesis's native position drive with configured gains and force bounds. There is **no native actuator-output history** in these records. A position target, force bound, contact force and actuator force must not be substituted for one another. New external-PD actuator qualification belongs to [#132](https://github.com/huangkiki/Dexlab/issues/132), after [protocol #131](https://github.com/huangkiki/Dexlab/issues/131); historical grasp success is not that qualification.

## Retained limitations and reviewed disposition

[#125][issue] retains the missing contemporaneous **resolved solver-options/static-configuration snapshot**, including contact resolution, effective tolerance, impedance ratio and sparse selection, plus per-contact combined parameters. The archived file records these settings as `null` or does not expose them. This limits runtime attribution, not the recovered Newton/integrator names. Actual iteration counts and JIT/factorization traces were also not saved and are not claimed here.

**Reviewed disposition (2026-10-09):** the search of all 126 manifest entries, sixteen complete records, frozen runner/options and 264 matching official source files does not recover the missing native snapshot. Accept the S column only as conditional source derivation; withdraw any interpretation that it measures historical effective parameters, achieved iterations or actuator output. This completes #125's bounded audit under the maintainer's coverage-first plan. Original records, thresholds and all six hold failures remain unchanged.

[Genesis #148](https://github.com/huangkiki/Dexlab/issues/148) and [pinch #132](https://github.com/huangkiki/Dexlab/issues/132) carry the effective-setting/epoch recording requirements. The separately recorded [migration #143](unisim-contact-migration.md) qualifies a new execution path; it does not repair old observations. Reopen the historical question only for a newly discovered contemporaneous artifact bound to the sixteen case identities.

This audit ran no Genesis import or physics step and did not rescore or modify the original data, thresholds, successes or six failed grasps. Its bounded read-only source/archive pass completed in 5.074 s of launcher wall time, with kernel memory peak 306,806,784 bytes and no OOM; this is audit overhead, not physics throughput. The new 6-hour/700-start campaign allowance was not consumed.

## Historical record identity index

SHA256 below is over the exact **decompressed JSON bytes**, before parsing. Compressed files and their other artifacts are covered by the original manifest above. Every row has 8,000 samples and the same H options.

| Case | Decompressed record SHA256 |
|---|---|
| `dev-cap-0.2` | `76f97458f57ba6c0785c70f8049563281cd58da772e6a93655f41a6cb91185f9` |
| `dev-cap-0.4` | `d0a077422df494bed68451388cb15718a0bc708cefa3a11374992295b928aab1` |
| `dev-cap-0.8` | `0c1fde9432a08942aa4ecbc1f3782e66a160f676b166c0e7023327418b8c4cf6` |
| `dev-cap-10` | `e5daf2c2abfab350711f6e8112a9e5f2e5d5a292ae3291273408ab768d44654c` |
| `dev-open` | `91353c980501857672fdcda4166f408df578de253ceffe2a3ef390a37e67f8dc` |
| `dev-repeat-10` | `94d2c54b0b2f98761c27d1832e38bc10ceccfc7b3ed90129d50a02bb52299981` |
| `eval-left-cap-0.2` | `d65d7c0324168153eb340f8436f475e9ce9fe6bf9902ac5102da1371cd0aa43b` |
| `eval-left-cap-0.4` | `d151fbb916e70734cab3f6b41361b8d122a6d08fe975875c3d44c0be2d54c50f` |
| `eval-left-cap-0.8` | `2253aeeeb02df68ea4a620cad700c075b041539d6e6790382732bdee7e3ad9b5` |
| `eval-left-cap-10` | `81c82fba9040338c67a3fa9b08bfc46c81fa1ccda605a564e4b1757691a16f2b` |
| `eval-left-open` | `064a27c39d4d5a6bcaa926e57dc33c484706e72b2d1a98884e495717bbaede86` |
| `eval-right-cap-0.2` | `a4fb9e9c8d9feecb45d4a8a0fee974cf5e85e14289e5fe4d398859ae42ab67c4` |
| `eval-right-cap-0.4` | `a0774bfbb0f7e995b0a8a83aa86bdfaf23a2eb3f9ddfe3f81526ab05fe48c2fd` |
| `eval-right-cap-0.8` | `6f013782e43c68fea2684415f5fb214919ec08b1c03f6acff251e88ea5c5e6a0` |
| `eval-right-cap-10` | `17e060d31dbe9f2c27324ae551a4f57e405f7a2728929956d748eccdfc88fdf8` |
| `eval-right-open` | `9e3e545574f6ade152e45dbc2b8c882be5fd74f44af6964d94dd866cb4f37803` |

[enums]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/constants.py#L61-L112
[options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L445-L646
[copy]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/scene.py#L63-L88
[copy-fields]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/options.py#L112-L127
[resolve]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L263-L298
[tolerance]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L334-L341
[static]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L477-L625
[body]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5592-L5662
[exit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py#L567-L615
[pair]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/contact.py#L433-L463
[forces]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5668-L5764
[post]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L3662-L3684
[api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L3162-L3264
[issue]: https://github.com/huangkiki/Dexlab/issues/125
