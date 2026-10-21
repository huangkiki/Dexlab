# Which solver failed? Audit dated 21 October 2026

A failed manipulation is evidence about a complete configuration: geometry, material model, controller, contact law, coupling and numerical solve. This audit distinguishes a missing interaction, a failed fixed configuration, a numerical diagnostic, an expected physical failure and an execution error.

The new audit reproduces a Kamino–VBD default two-attachment construction failure in Newton 1.7, and identifies an official configuration that bypasses it. The strongest existing physical mechanism evidence is **Genesis 1.4.3's legacy PBD–rigid path**: the inspected contact implementation omits tangential friction, and a free-body test measures reaction momentum arriving one 2 ms step late. RSS wiping establishes a different result: removing auxiliary sponge retention defeats the tested configuration, but does not isolate a SuperDex algorithm defect. No qualified Wuji in-hand manipulation failure has been established by these records.

## New direct comparisons in this audit

### Newton 1.7: default two-attachment construction fails; disabling proxies bypasses it

The original minimal model from [Discussion 4055](https://github.com/newton-physics/newton/discussions/4055) was checked on Linux / RTX 4090 / Newton 1.7 / Warp 1.18: Kamino rigid bodies and a VBD cable with cross-solver FIXED attachments. Model and ADMM settings are retained; only the second attachment is conditional.

| Condition | Local result | Scope |
|---|---|---|
| One FIXED attachment | Builds; six bodies advance 10 × 1 ms with finite recorded states | Construction and short-stepping positive control, not constraint-accuracy validation |
| Two FIXED attachments | Two attempts fail Kamino construction validation with `ROD (3 instances)` | Partition compatibility failure under the default proximal-joint visibility configuration |

Two subsequently frozen diagnostics change only the documented `joint_proximal_bodies` option from its default True to False. Both the one-attachment and two-attachment models build and advance 10 × 1 ms with finite recorded states. A configuration that bypasses the rejection therefore exists. This does not qualify attachment error, force transfer or complete-task accuracy, and is not a claim that all coupling problems are repaired. Both original default-configuration failures remain preserved.

The rejection occurs before ADMM iterations. Source first expands proximal visibility across attachments, then constructs each solver view; Kamino rejects the ROD joints it sees. This does not establish ADMM nonconvergence, inability under every configuration, or reproduction of the author's larger CUDA 700 case.

An incorrect import adaptation and a subsequent omitted collision-buffer argument were audit-script errors; both were corrected and retained, not counted as solver failures. The final positive control uses the official `CollisionPipeline.contacts()` / `collide(state, contacts)` API. Engine source is unchanged.


Implementation references: [ADMM neighbor visibility](https://github.com/newton-physics/newton/blob/7e75abe28b8d69522bc0b34837aaed2c303dff5a/newton/_src/solvers/coupled/solver_coupled_admm.py#L717), [Kamino joint validation](https://github.com/newton-physics/newton/blob/7e75abe28b8d69522bc0b34837aaed2c303dff5a/newton/_src/solvers/kamino/solver_kamino.py#L1465).

### MuJoCo–VBD towel grasp: coupling configuration changes task outcome

The native RSS YAM towel uses 60 Hz control, 16 substeps, five VBD iterations and full-surface contact. The authored scene and controller remain fixed while the coupler configuration changes. Repeats use fresh processes, not unseen tasks. Upstream thresholds require over 60 mm rise, under 10 mm final hand error, at least half the grasp strip remaining near the hand, and under 20 mm hold displacement.

| Attempt | Coupler / transfer / outer iterations | Cloth rise mm | Hold displacement mm | Near hand | Hand error mm |
|---|---|---:|---:|---:|---:|
| `towel-one-way-01` | one_way | 96.5145 | 3.838 | 85.7% | 3.983 |
| `towel-proxy-01` | Proxy/staggered/1 | 0.0000 | 106.121 | 0.0% | 3.875 |
| `towel-one-way-02` | one_way | 96.3007 | 3.856 | 85.7% | 3.983 |
| `towel-proxy-02` | Proxy/staggered/1 | 0.0000 | 106.134 | 0.0% | 3.878 |
| `towel-one-way-03` | one_way | 96.3647 | 4.041 | 85.7% | 3.983 |
| `towel-proxy-03` | Proxy/staggered/1 | 0.0000 | 106.121 | 0.0% | 3.876 |
| `towel-proxy-4iter-01` | Proxy/staggered/4 | 0.0000 | 106.121 | 0.0% | 3.876 |
| `towel-proxy-16iter-01` | Proxy/staggered/16 | -0.0000 | 106.123 | 0.0% | 3.877 |
| `towel-proxy-4iter-02` | Proxy/staggered/4 | 0.0000 | 106.116 | 0.0% | 3.873 |
| `towel-proxy-16iter-02` | Proxy/staggered/16 | -0.0000 | 106.121 | 0.0% | 3.876 |
| `towel-proxy-lagged-01` | Proxy/lagged/1 | -0.0000 | 106.123 | 0.0% | 3.873 |
| `towel-proxy-lagged-02` | Proxy/lagged/1 | 0.0000 | 106.126 | 0.0% | 3.874 |

Failure to lift does not automatically mean a successfully acquired grasp later slipped. The controller algorithm is unchanged but reacts to actual state, so trajectory length and applied command history differ. In the third pair, all 17 captured compiled-model arrays match exactly. After native warmup/reset, particle positions differ by up to 5.424 micrometres and velocities by 6.437 mm/s; the starting states are not bitwise identical. Hand telemetry shows the Proxy approach exhausts its 600-step arrival budget. At the end of closing, target error is 7.58 mm and jaw width 9.56 mm: a valid grasp was not acquired. One-way reaches the target while carrying no cloth reaction. This is task compatibility between coupling and controller, not failure to retain a qualified grasp or proof of Proxy nonconvergence. Every-substep contact geometry and real-material accuracy remain unvalidated.

The four/sixteen outer-iteration and lagged-transfer configurations were frozen as diagnostics after observing the initial failure. They are not independent holdouts or an exhaustive tuning search. Engine source and physical thresholds remain unchanged; all failures are retained.

### Current RSS sponge wiping: paired retention-assistance ablation

Newton 1.7 / MuJoCo 3.15 / SuperDex 1.0 FP32. The ablation removes extra node constraints and their hand-following updates while retaining the original control and twelve-tick contact-readiness gate. It uses unchanged task thresholds and the existing independent DexLab material-point scorer. Displacement follows a fixed material patch in the measured hand frame; it is not interchangeable with another cohort's slip definition.

| Attempt | Record integrity | Task pass | Cleaned | Material-patch displacement mm | Actual latch groups |
|---|---|---|---:|---:|---:|
| `wipe-current-original-01` | True | True | 95.47% | 0.061 | 1 |
| `wipe-current-no-latch-01` | True | False | 47.33% | 446.256 | 0 |
| `wipe-current-original-02` | True | True | 95.88% | 0.060 | 1 |
| `wipe-current-no-latch-02` | True | False | 46.09% | 440.653 | 0 |

Both pairs have identical compiled models, initial/settled particle arrays and tracked material indices; all four independent record-integrity checks pass. Both ablations contain zero active latch groups.

Latch adds compliant node constraints; it is neither glue nor a rigid weld. Passing establishes the assisted configuration. The ablation failure is attributed to the complete configuration; SuperDex contact law, reaction transfer and control have not been individually isolated. Sources: [original wiping task](https://github.com/robosimstudio/robosimstudio/tree/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/wipe_the_bar), [unchanged independent scorer](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/demos/rss-wiping/score.py).


## What the existing DexLab evidence actually establishes

| Configuration | Observation | Supported interpretation |
|---|---|---|
| Genesis 1.4.3, legacy PBD–rigid | Friction inputs 0.01 and 0.5 produce identical complete trajectories: 60 mm horizontal travel in 0.3 s, retaining 0.2 m/s. Support and disabled-coupling controls behave as declared. | Missing tangential interaction on this particular path. This does not describe Genesis IPC coupling. |
| Same path, free cloth and free 1 g plate, zero gravity | Cloth momentum changes by 3.2e-5 kg m/s at step 56; the opposite plate change arrives at step 57. Same-step residual exceeds the frozen 3.3e-7 threshold although final momentum cancels. | A measured one-step exchange delay, consistent with source execution order. Corrected actuator gravity compensation still did not produce cloth retention. |
| Historical RSS wiping, Newton 1.6 / MuJoCo 3.12 / SuperDex 1.0 FP32 | Matched original runs pass 3/3; no-latch runs pass 0/3. No-latch held material-patch displacement is 440.47–449.98 mm, with 39.92–41.15% cleaned. | The configuration depends on auxiliary retention. This is distinct from the author's 69/226/218 mm cohort; contact, control and coupling have not been uniquely separated. |
| SuperDex 1.0 FP64, finite-pad edge contact | Splitting the same prism surface from 256 to 1,024 to 4,096 triangles reduces overload penetration from 2.267 to 0.858 to 0.481 mm, and momentum-rate residual/weight from 7.036 to 0.216 to 0.000993. Smaller timesteps or 100→400 iterations did not remove the original failure. | Sensitivity to surface discretization in this experiment; the finest mesh passes its frozen controls. No general engine repair is established. |
| MuJoCo 3.15, marginal pinch | Tolerance 1e-6→1e-10→1e-14 reduces impulse residual from 1.234e-6→1.240e-8→1.245e-10 N s, while approximately 2 mm/s creep persists. | Numerical closure and soft-contact retention are separate requirements. |
| Genesis 1.4.3 rigid contact | A nominal zero friction input is clamped to an effective 0.01; native contact readback and the incline acceleration discrepancy agree. | A contact-model expression limit in this version. |
| Newton 1.6.1 VBD compliant | At fixed step 16, 99/101/1001 and 100/1000 terminal iterations form two position/returned-force groups; residuals remain approximately 4.31e-6 and 4.04e-6 N s. | A local terminal-update observation; neither an exact full-state cycle nor a unique global cause has been proved. |

Sources: [Genesis cloth](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/genesis-cloth.md), [matched wiping](rss-wiping.md), [contact development](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/demos/contact-benchmark/README.md), [pinch residuals](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/pinch-impulse-results.md), [Genesis incline](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/genesis-incline-results.md), [Newton incline diagnosis](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/newton-incline-results.md).

These are historical experiments, not new full reruns. This audit verified all **147 registry-bound files** without a hash mismatch and independently rescored the frozen Genesis plane and free-body coupling records; both scores exactly matched their published results. Registry coverage contains 74 engine/configuration rows, 54 cohorts and 13 task families. Eight research experiences, 15 demo directories and 30 evidence directories overlap these records and must not be added as independent trials.

## Why an RSS success needs its configuration attached

RSS is an orchestration toolkit, not one unified IPC solver. Its examples combine MuJoCo/MuJoCo-Warp, Newton VBD, SuperDex and Genesis, with task-specific feedback paths.

| Mechanism | What the successful example establishes | Remaining limit |
|---|---|---|
| Towel `one_way` | Cloth follows the moving hand through contact and friction. | Cloth reaction does not load the arm. |
| Paper `one_way` with `slide_feedback` | Soft-contact load can stall the gripper slides at their force cap. | A delayed equal/opposite force pair acts across each slide; it does not apply the complete net reaction to the robot. |
| Sponge latch | Compliant node constraints carry the grasped region after contact readiness, then release on opening. | Assisted retention is additional to friction. |
| Label's rigid pull tab | Frictional grasp can peel the attached label. | It does not test direct grasp of a freely deforming thin film. |
| Cable contact history | A fixed authored friction/contact configuration retains and routes a cable. | The example uses gripper friction 60; this is not an identified real contact material. |
| Suction weld/wrench | The declared suction model holds and releases the plate. | Adhesive/suction retention is not a friction-only grasp. |

[Upstream arrangements](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/robosimstudio/specs/arrangement.py), [one-way and slide-feedback implementation](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/robosimstudio/scene/physics/couplers.py), [cable conditions](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/route_the_cable/README.md).

### Supplemental rope check: a passing test can confirm a limitation

All eight assertions in upstream `tests.test_superdex_cable_robot` pass in this audit. One deliberately checks a limitation: with `feedback="off"`, a full-close command takes the jaws below 3 mm despite the cable's 22 mm diameter. That pass confirms the missing reaction barrier; it is not successful physical grasping. With the example's grip amount 0.80, the measured width is 19.20 mm, rise 112.82 mm and hold drift 0.412 mm. Whether the object rises alone does not identify the contact mechanism. [Original test and limitations](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_superdex_cable_robot.py)

The earlier soft-tab reconstruction is **not qualified solver-failure evidence**: its grasp acquisition failed, and later prepositioned rigid controls had initialization/geometry problems or failed themselves. The unchanged rigid-tab control did peel all 144 bonds. Those failed attempts remain in the cumulative record.


Current inventory: 50/50 entries pass their scoped assertions; 0 skipped, 0 failure/error outcomes need review, and 0 remain incomplete. This is not a zero-failure full-suite run: original failures and subsequent retries are described below. Scope limits remain attached to each row.

[Full inventory: 50 public entrypoints, 18 paper showcases, 30 evidence directories and 15 demos](solver-failure-inventory.md)

## libuipc and Newton: current status of known failures

This is a source/status audit, with the Newton 4055 case checked locally as described above. It is not an execution of all examples from either project.

| Reference | Verified status on 21 October | Interpretation |
|---|---|---|
| [Newton 4055](https://github.com/newton-physics/newton/discussions/4055) | Reported on Newton 1.5/Warp 1.16 Windows; locally reproduced two-attachment construction rejection on Newton 1.7 Linux, with one attachment stepping, as detailed above. | Default partition compatibility failure; disabling proximal bodies allows construction and short stepping. This is not proof of ADMM nonconvergence. |
| [Newton 3660](https://github.com/newton-physics/newton/issues/3660), [fix 3664](https://github.com/newton-physics/newton/pull/3664) | Buffer overallocation fix merged on 30 July, commit `36b2ddfe`; the inspected Newton 1.7 allocator counts compatible pairs. | Historical capacity/integration defect, not a currently unfixed physics result. |
| [Newton 1599](https://github.com/newton-physics/newton/issues/1599) | Closed; comments discuss inertia, collision margins, stale normals and MuJoCo/MJWarp paths with differing attributions. | Retain version and configuration. Adding armature changes the inertia model; it does not validate fidelity. No independent local reproduction here. |
| [libuipc 423](https://github.com/spiriMirror/libuipc/issues/423) | Open. Contact thickness and material thickness remain coupled in the inspected main revision `c283e98`. | Model representation limit, not an independently established manipulation failure. |
| [libuipc 467](https://github.com/spiriMirror/libuipc/issues/467) | Closed on 20 October. Sample 95 at `b70f322` uses new directional stretch moduli; the sample requires a newer source build, while the older 0.0.29 wheel lacks the API. | Do not repeat the old anisotropic-material omission as a current source defect. The sample disables gravity/contact for biaxial tension, so it is not contact validation. |
| [libuipc discussion 193](https://github.com/spiriMirror/libuipc/discussions/193) | `ExternalArticulationConstraint` is implemented. | “Only SoftTransform; no articulation” is outdated. Interface availability is not qualified closed-loop manipulation. |
| [libuipc 413](https://github.com/spiriMirror/libuipc/issues/413) | CMake build workaround, open. | Build issue, not physical solver failure. |

The existing local pyuipc 0.0.28 FEM/ABD 100-step, reset and FP64 readback checks establish lifecycle and precision only. They do not establish success or failure of dexterous manipulation. The newer sample repository also contains a four-finger apple transfer example; this audit does not claim that libuipc lacks robot grasping.

Version discrepancy: the RSS arrangement comment attributes Proxy cloth difficulty to unsupported full-surface feedback. Installed Newton 1.7 VBD declares `coupling_supports_full_surface_soft_contacts()` true, and the current Proxy scene constructs and executes. The old comment cannot uniquely explain the newly observed failure.


## Execution errors are separate from physical conclusions

The inventory uses scoped assertions and finalized records; it does not declare the whole RSS test suite green. One `tests.test_examples` module invocation retained 28 parent tests with one failure, 21 error/subtest-error events and one missing-Genesis skip:

- The standalone rope child receives an empty `CUDA_VISIBLE_DEVICES` when the parent has no setting, selecting CPU SuperDex while its assertion assumes GPU VBD. The unchanged test passes with an explicit GPU. This diagnoses an environment/test-entry assumption.
- The long page-construction loop first reports a CUDA out-of-memory error during dough Nanogrid allocation, followed by CUDA 700 and tiny-allocation failures. Fresh-process dough, new-kind and towel page retries pass. Not all 21 errors were individually rerun or declared repaired; a poisoned context does not establish a physical defect in every later scene.
- The local Newton audit script initially used an incorrect import path and then omitted the required collision buffer argument. Both were corrected at their entrypoint, with original failures and costs preserved. The install script's initial PATH error is also retained separately. None is an upstream solver result.

After the base-environment batch, all 2,248 checked engine files match their installed wheel RECORD hashes. Each invocation checks source cleanliness. This is not a claim of a nonexistent full pre-batch file scan, and physical thresholds were not changed to recover from dependency or execution failures.


## What was executed and how to repeat it

The scope is RSS public examples plus existing DexLab-related experiments; libuipc/Newton receive known-failure checks. RSS is frozen at `b001cc7e10a83577261aac4471fa45e0ced6d415`, DexLab historical evidence at `c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3`. The base RSS environment follows its lockfile: Python 3.12.12, Newton 1.7.0, MuJoCo/MuJoCo-Warp 3.15.0, Warp 1.18.0 and SuperDex 1.0 FP32. Optional Genesis/GaP checks use a separately frozen environment; no package upgrade is mixed into a batch.

The optional environment uses Genesis 1.3.3, Quadrants 1.3.0, pyuipc 0.0.28 and Torch 2.10.0, with the same Newton/MuJoCo/Warp versions as the base environment. All 211 applicable registry version pins were checked before execution. Dependency retrieval required a separate recipe: mirrored registry downloads retain the original lock hashes; three large wheels were assembled from ranges and verified by whole-file SHA-256; GaP and its core were built from the exact pinned `09e45f8` source without unrelated recursive benchmark assets. RSS itself excludes those benchmark dependencies. The final offline `uv sync` refused the local-wheel origin, so it did not pass; installed pin verification and the recorded source/hash checks are reported separately. No physical assertion was changed.

Each native invocation selects upstream unittest tests without changing their physical assertions. Scene construction, twenty-step smoke checks, manipulation tasks, task-goal scoring, expected negative controls and mocked hardware have different meanings. A module pass is not a count of successful manipulation trials. The source remains clean; the harness records versions, assertions, commands, resource receipts and selected measured observations. Official geometry-preprocessing outputs are reused only with matching input/output hashes. Native assertions do not supply independent every-substep collision or material validation.

To run a particular native selection from the inventory, use a disposable checkout and its official locked environment:

```bash
git clone https://github.com/robosimstudio/robosimstudio.git
cd robosimstudio
git checkout b001cc7e10a83577261aac4471fa45e0ced6d415
uv sync --frozen --extra superdex --no-group rtx
ROBOSIMSTUDIO_RENDERER=tiled JAX_PLATFORMS=cpu \
  .venv/bin/python -m unittest tests.test_example_grasps_cloth -v
```

Water and policy selections need the declared `genesis` and `gap` extras in a separate environment. These commands identify the upstream test entry, not a guarantee of hardware-independent success. The local audit additionally uses bounded execution and hash-checked geometry caching.

Experiments are serialized on one RTX 4090 shared with the desktop, with a 16 GiB memory ceiling, 4 CPU cores, 128 tasks, zero experiment swap and 8 GiB desktop reserve. The frozen new-experiment ceiling is 100 invocations, 10,800 cumulative wall seconds and 600 seconds per invocation, ending no later than 23:00 Beijing. Dependency installation and repository validation are recorded separately. These are execution limits, not a shared performance benchmark.

The final ledger retains 81 new invocations and 5,373.764 s: 64 processes exited normally and 17 exited nonzero. Nonzero exits include tested failures and audit-harness errors, not 17 independent solver failures. The earlier soft-tab cohort retains its separate eight attempts and 339.306 s. Ten optional dependency installation/download-stage invocations consumed 4,849.298 s including failures and cancellation; this is setup time, not physics execution.

Final optional-environment checks covered the four policy entrypoints, first-grasp-miss recovery, water pouring, its scored goal, and shallow-tilt/aside-target negative controls. All 18 original assertions across ten fresh-process invocations passed without skips. This completes public-entrypoint coverage, not reproduction of all paper showcases.

The complete local bundle retains the ledger, all failures, source snapshots, package manifests, observations and control-step trajectories for the ablations. **This PR publishes the interpretation and inventory; the new raw bundle is not a public release asset.** Historical public evidence remains linked above. Missing paper scene/data access, unqualified initial controls and unknown physical fidelity are not converted into successful qualification.

Relation to earlier discussion: [Discussion 220](https://github.com/huangkiki/Dexlab/discussions/220) identified wiping assistance and reaction timing; this audit adds current-version paired evidence for assistance dependence, without attributing slip uniquely to delay. [Discussion 222](https://github.com/huangkiki/Dexlab/discussions/222) distinguishes motion tracking from contact effect; the towel diagnosis likewise checks whether acquisition actually occurred. Its light-touch/press/release proposal remains separate and was not launched by this audit.


Remaining evidence gaps and recovery criteria are tracked in [#247](https://github.com/huangkiki/Dexlab/issues/247); it does not launch another development plan.


```{toctree}
:hidden:

solver-failure-inventory
```
