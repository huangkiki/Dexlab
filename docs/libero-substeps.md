# Native LIBERO substep records

[English](libero-substeps.md) | [简体中文](libero-substeps.zh-CN.md)

Implementation and qualification work for [#188](https://github.com/huangkiki/Dexlab/issues/188).
Representative native paths have been checked; physical-reference qualification, repository
delivery and the full task matrix remain open.
Historical version-1 records and scores are unchanged.

Initialization qualification is version-specific. A retained whole-repository test failure
exposed a mismatched test assumption: for the same non-unit free/ball quaternions,
MuJoCo 2.3.7 `forward` normalized the saved coordinates while 3.15.0 retained them.
The unchanged executor rejects the latter under the pinned initialization contract.
Tests separately verify 2.3.7 acceptance and 3.15.0 rejection, without changing source
states, engine versions or tolerances. Latest-native SDF checks remain a separate path.

## Acquisition and persistence

The version-2 executor accepts `substep_recording: true` together with `recording: true`.
Omission retains control-step acquisition and explicitly leaves substep qualification pending.
The existing guarded runner owns admission, timeouts and cumulative budgets; this switch does
not supply authorization or resource admission.

`libero_physics.record_substeps` intercepts only existing `sim.step` calls. It calls the original
once and restores the hook on success or failure. The supported contract is the pinned
MuJoCo 2.3.7 Euler path with no plugins and a wrapper that calls `mj_step` once without a later
forward operation. Other integrators require their own epoch qualification and are rejected.

The record retains pre/post time, generalized position, velocity and activation, warnings,
actual actuator force and transmission, generalized smooth/constraint forces, packed inertia,
body transforms, applied external wrenches, all constraint identities and a lossless CSR
Jacobian. Each contact retains its geometry pair, frame, position, distance, parameters,
constraint address and native local force/torque. Applied body-wrench Jacobians are separately
labelled read-only computations from the native force-stage caches.

One pickle-free NPZ chunk is written per action, including a failed action's observed prefix.
Shapes, dtypes, empty arrays and non-finite numerical evidence survive serialization.
`substeps.json` indexes every chunk, while `run.json` binds all nested file hashes.
Consecutive action/substep indices, nonempty observations for completed actions and retained
failure receipts are required. The archive keeps only the current action in memory.

The new storage schema 2 encodes arrays in one contiguous byte payload plus JSON metadata,
rather than a ZIP member per array. Dtype (including byte order), shape and traversal
references determine nonoverlapping extents; missing, aliased, unused, truncated and
trailing data are rejected. Arrays are restored independently and writable. Numeric bits,
including signed zeros and NaN payloads, are retained. Storage schema 1 remains readable;
this storage version is separate from the physics model and scoring protocol versions.
The candidate passed 86 relevant regressions. All five complete reference sequences
(1,006 actions / 25,150 substeps) were losslessly converted and fully rescored; every field
and score matched, apart from the explicitly derived run-receipt hash. Substep archives
shrank from 1,837,228,156 to 442,665,669 bytes (75.91%). The original archives remain intact;
converted copies carry explicit offline storage-transform provenance. This is measured
size on that cohort, not a universal capacity or native throughput claim.

## Complete-run scoring and execution identity

`libero_score_v2` validates an externally pinned execution request, input manifest and run
receipt. It checks the complete action/substep denominator, task/entity/joint bindings,
all native goals, observation channels and terminal state before reporting per-coordinate
residuals. A structurally valid record can have a negative numerical result or native task
failure; these outcomes are reported separately. Historical records retain their original
identities and missing environment metadata stays unknown.

The existing `libero_trials init-tasks` / `run-task` entrypoints use the same cumulative
ledger and guarded resource contract for native execution and offline scoring. The new
execution manifest includes SciPy and llvmlite alongside the previously pinned packages,
plus an explicit `numerical_environment` mapping for `OPENBLAS_NUM_THREADS`,
`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMBA_NUM_THREADS`, `NUMBA_DISABLE_JIT` and
`NUMBA_CPU_NAME`. Each value is a string or null, where null means unset. The runner sets
or removes these variables before child import; the executor rejects a mismatch before
creating a native environment and preserves the values in its receipt. These are environment
controls, not measured thread-pool counts or a complete binary/platform identity.

This requirement follows a retained comparison failure. With identical saved poses and
package versions, offline native observation reconstruction matched the new relative
quaternions exactly under the explicit single-thread configuration and matched the old
ones exactly under inherited defaults. Changing both thread controls together isolates
the configuration pair, not the individual effect of either variable. No observation
threshold was relaxed, and the original failed comparison remains failed.

## Equations and epochs

For this pinned Euler path, force caches after `mj_step` belong to the pre-integration epoch;
the updated `qpos` and `qvel` belong to the end of the substep. They are not interchangeable.
The offline `libero_dynamics` module imports no engine and computes residuals for:

- Smooth-force accounting: `qfrc_smooth = qfrc_passive - qfrc_bias + qfrc_applied + qfrc_actuator + J_com^T xfrc_applied`.
- Actuator transmission: `qfrc_actuator = actuator_moment^T actuator_force`, with the recorded joint actuator-force clamps.
- Acceleration accounting: `M qacc_smooth = qfrc_smooth` and `M qacc = qfrc_smooth + qfrc_constraint`.
- Constraint transmission: `J^T efc_force = qfrc_constraint`; contact-wrench decoding checks each contact's constraint mapping and cone representation.
- Euler velocity: `(M + h diag(dof_damping)) (v_after - v_before) / h = qfrc_smooth + qfrc_constraint`.
- Euler position: update scalar/free translations with the new velocity and integrate free/ball quaternions with that angular velocity.

The damping term means stored `qacc` is not necessarily the acceleration used to update
velocity. Packed inertia is independently expanded from its DOF parent tree. Residuals
remain per-coordinate: generalized forces can mix N and N m, positions mix length and
rotation/quaternion coordinates. No universal physical threshold or pooled physics pass is
defined here. A frozen evaluation protocol must specify applicable units, tolerances,
references and uncertainty before outcomes.

For the pinned Newton/CG implementation, `M qacc - qfrc_smooth - qfrc_constraint` is also
the primal objective gradient. The solver can stop on scaled cost improvement, scaled
gradient, line-search failure or iteration count. Native `tolerance` therefore is not a
per-coordinate bound on this residual. A departure from a frozen diagnostic threshold
does not alone establish an integration or recording defect. Individual-run termination
attribution needs the corresponding solver observations.

These semantics follow the pinned [forward/integration source](https://github.com/google-deepmind/mujoco/blob/2.3.7/src/engine/engine_forward.c)
and [inertia/contact support source](https://github.com/google-deepmind/mujoco/blob/2.3.7/src/engine/engine_support.c).
The gradient and stopping rules are in the pinned
[solver source](https://github.com/google-deepmind/mujoco/blob/2.3.7/src/engine/engine_solver.c).

## Body accounting and solver observations

New `physics-model.json` records use schema 2. They retain body/root/DOF ownership,
principal inertias and inertia orientations, spatial motion axes and their derivatives,
spatial velocity/inertia caches, the native mean-inertia normalization and solver options.
The independent body calculation uses **pre-integration velocity**, not the updated
`qvel` left in native data after a step. It performs no native forward/inverse call.

At each tree COM, spatial vectors use world orientation and angular/linear order.
The offline Newton–Euler calculation reconstructs `I a + v ×* (I v)`, subtracts
localized contact and applied body wrenches, and accumulates children. It separately
checks spatial inertia, spatial velocity and projected body effort. Joint motor,
passive and directly applied effort, noncontact constraints and armature acceleration
remain explicit in that projection. The resulting **inferred net subtree wrench**
can include unresolved tendon/equality/passive loads; it is not a separately measured
bearing reaction. Root wrenches are shifted individually to the world origin before
interpretation; vectors from different tree origins are not blindly summed.

Rigid free-joint trees additionally retain world COM momentum change and expected
impulse, including contact, gravity, applied/generalized loads and the Euler damping
correction. Results are raw component errors in N s. Rotating COM offsets retain
discretization error; free articulated trees and nonzero armature are explicitly
unqualified by this diagnostic. No universal momentum threshold is introduced.

Solver acquisition retains only the current saved iteration prefix. The fixed native
capacity is 1,000; any excess count is reported as truncated statistics. Unconstrained
`solver_nnz` and disabled forward/inverse buffers can be stale and are represented as
unavailable, not zero observations. PGS lacks a primal-gradient statistic; a NoSlip
stage prevents direct comparison with the final main-solver gradient. The native API
does not expose an exact termination reason, which remains explicitly unknown.

Schema-2 model records require a separately frozen schema-2 protocol named
`mujoco-2.3.7-euler-body-v2`, including per-coordinate bounds for `spatial_inertia`,
`spatial_velocity` and `projected_body_effort` in addition to the original eight metrics.
Inertia components have kg, kg m and kg m² units; motion and generalized-effort
components also retain their respective angular/linear units. Body arrays are flattened
in body-major order for those numerical bounds. The scorer reports body-wrench maxima,
free-COM diagnostics and iteration counts per action, with physical-reference and
joint-reaction qualification still separate. Historical schema-1 records remain readable
with their original eight-metric protocol; current execution requires the new protocol.

The coordinate semantics are checked against the pinned
[body dynamics source](https://github.com/google-deepmind/mujoco/blob/2.3.7/src/engine/engine_core_smooth.c)
and [spatial algebra source](https://github.com/google-deepmind/mujoco/blob/2.3.7/src/engine/engine_util_spatial.c).

## Qualification boundary

Small native fixtures cover a free body with external force/torque, a damped driven slide,
an articulated limited/clamped drive, ball-joint rotation and contact in both cone and
dense/sparse Jacobian paths. Unit checks compare instrumented/native state and cache values
and deliberately corrupt forces, positions, timing and mappings. Storage/run integration has
separate mocked tests. Exact source identities and both successful and failed attempts belong
in the corresponding qualification receipts, not inferred from this document.

An earlier archive comparison encountered a negative-test fixture whose shared model had
been deliberately mutated. That failed receipt remains unchanged. The subsequent fixture
isolation edit is now covered by a new native package and offline replay; this does not
reclassify the original failed comparison.

The body/solver package passed 20 native fixture tests, including analytical static support
loads and world-origin moments, centered free-body impulse with external/generalized force,
COM-offset handling, articulated/contact/ball equations, corruption and stale-channel
checks. A separate scratch-data RNE comparison matched the original force epoch and exposed
the mixed-velocity error without changing live native data. All 139 retained positive
substeps then passed offline replay, followed by 83 record/archive/executor/budget regression
checks with no engine import and no skips. These are synthetic-reference and recording
checks, not real-material validation or complete native LIBERO integration.

The first complete free-object development package executed 139 actions per run in three
off/on/repeat runs. Both instrumented runs retained 3,475 substeps, passed structural
record validation, and reproduced the same numerical diagnostics. Current-version
control arrays matched exactly; the 139 repeated substep chunks were byte-identical.
The frozen comparison against the earlier runtime configuration failed in seven float32
relative-quaternion channels and their aggregate observation. The offline reconstruction
above explains that difference without reclassifying the failed comparison as passed.

Both instrumented runs retained 507 substeps above the frozen 1e-8 constrained-acceleration
residual bound, with maximum 3.2591526123865178e-6; the other seven numerical metrics
stayed within their original bounds. Native task success remained true. This is a
negative numerical diagnostic, not evidence of measured material inaccuracy. The package
used all three native starts; the environment-contract code added afterward passed 66
targeted unit/regression checks before the five-family qualification below.

The subsequent body/solver/environment package completed free-object, drawer, stove-joint,
simultaneous-target and long-sequence cases in 15 on/off/repeat runs: 3,018 actions and
50,300 recorded substeps. Every native final task query succeeded, and every instrumented
record was structurally valid. All current control arrays/goals and repeated substep bytes
matched exactly; full archive hashes and terminal resource telemetry were verified.
Constrained-acceleration and projected-body-effort violations per recorded run were
507/3,475, 166/3,450, 45/2,000, 749/9,700 and 367/6,525 respectively, with no violations
in the other nine metrics. All original numerical bounds remain frozen.

This package used 15 new starts and 1,155.1632 worker seconds, preserving lifetime charges
of 58 starts and 1,690.7071 seconds. Campaign files total 3,718,120,729 bytes; the frozen
archive comparator passed in 2.7922 seconds. [Recorded qualification and next storage check](https://github.com/huangkiki/Dexlab/issues/188#issuecomment-6159417739).
These are complete development sequences, not new holdouts. The subsequent packed-storage
native on/off/repeat check completed all three 139-action runs. All states/actions/goals and
complete scores matched the preceding native reference; repeated chunks were byte-identical,
and newly recorded fields matched the independently converted reference. Each instrumented
run retained its 507 constrained-acceleration and projected-body-effort diagnostic failures.

The first packed native launch failed at import before any action because its new config
directory omitted `config.yaml`. The original package stopped; its failure and cost remain.
The corrected revision copied the known configuration byte-for-byte, validated its source
paths and checked its hash before every dispatch. Its three worker times were 33.7453,
6.4440 and 30.9712 seconds; separate final comparison passed in 6.0474 seconds.
The cumulative native-process ledger retains 62 starts and 1,762.2619 worker seconds,
including that failed launch. Offline conversion, builds and comparisons have separate
receipts and are not hidden within a native-throughput figure. Repository delivery checks
and the complete task matrix remain open. Generalized forces
and inferred subtree loads do not by themselves qualify physical joint/support reactions;
uncomputed `cfrc` buffers are not observations. Independent physical references retain their
own acceptance. Numerical consistency, physical validity, native success and learned-policy
performance remain separate. Representative qualification never closes the 130-task parent.
