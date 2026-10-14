# Native LIBERO substep records

[English](libero-substeps.md) | [简体中文](libero-substeps.zh-CN.md)

Implementation and qualification work for [#188](https://github.com/huangkiki/Dexlab/issues/188).
The engineering implementation is merged in [PR #193](https://github.com/huangkiki/Dexlab/pull/193).
Representative native paths have been checked; physical-reference qualification and the
full task matrix remain open.
Historical version-1 records and scores are unchanged.

Initialization qualification is version-specific. A retained whole-repository test failure
exposed a mismatched test assumption: for the same non-unit free/ball quaternions,
MuJoCo 2.3.7 `forward` normalized the saved coordinates while 3.15.0 retained them.
The executor retains rejection of the latter under the pinned initialization contract.
Tests separately verify 2.3.7 acceptance and 3.15.0 rejection, without changing source
states, engine versions or tolerances. Latest-native SDF checks remain a separate path.

## Versioned controller initialization

New execution payloads must explicitly declare
`initialization_contract: "osc-restored-pose-v1"`; admission rejects an omitted or unknown
contract. This version restores time/qpos/qvel once, calls the pinned OSC controller's
`update(force=True)` for its single native forward and cache refresh, then resets its
Cartesian position and orientation goals to that restored pose. It adds no dummy action,
settling step or per-action state injection. The qualified interface is one Panda arm,
delta `OSC_POSE`, without interpolation, on MuJoCo 2.3.7 / robosuite 1.4.0.

The earlier reset created the controller before restoring the saved native state, leaving
its cache marked current. In one exposed Salad-dressing development example the first
goal used an end-effector position 24.2377 mm away from the restored pose. A complete
forward-only control still failed; refreshing the cache changed native success while
source-trajectory differences remained. This identifies a controller-cache defect in
that execution path, not an engine defect or a complete reconstruction of the demonstration.
[Mechanism and retained controls](https://github.com/huangkiki/Dexlab/issues/198#issuecomment-6163777769).

The record stores controller memory before and after restoration, arm joint/site identities,
native cache readbacks and the state after goal reset. Offline scoring checks arm caches
against the saved native state, pose goals against the recorded restored pose, and unchanged
reset nullspace/gripper references. Pose-readback consistency is not independent forward
kinematics or physical validation. Tests use the real pinned OSC to exercise a relative
first goal and a zero-orientation action; synthetic record mutations test rejection separately.

The reset `initial_joint` and gripper `current_action` remain unchanged and are recorded.
Saved flat state does not provide source controller goals, integrated gripper action or
the skipped source prefix; this contract makes a fresh restored-pose start explicit rather
than inventing those histories. Original records retain their original initialization and
remain scoreable; they cannot be relabelled with this contract. Re-running an old manifest
under changed sources is not allowed. Freeze a new payload/source identity and cumulative
budget for each declared regression. Earlier representative-path controls and the 120-record
development cohorts do not qualify the new initialization. Complete affected-task regression,
remaining source-history attribution and the full 130-task scope remain open in
[#198](https://github.com/huangkiki/Dexlab/issues/198), [#188](https://github.com/huangkiki/Dexlab/issues/188)
and [#181](https://github.com/huangkiki/Dexlab/issues/181).

The first frozen regression covers the same seven exposed Alphabet-soup / Salad-dressing
diagnostic demonstrations: **21 complete on/off/repeat runs, 3,126 actions and 52,100 recorded
substeps**. All 14 instrumented records are valid. Control/state/non-image observation arrays
are exact across recording modes; repeated goal records, scores and substep archives match.
Four of the five original native failures become successes; Alphabet `demo_29` still fails,
and the two original success references remain successful. All three modes agree on each
native result. This selected set does not estimate a full-task improvement rate.

Every recorded run retains constrained-acceleration and projected-body-effort negatives under
the original bounds; the other nine diagnostics have no violating substeps. The package used
518.89 native worker seconds, with at most 1,104,654,336 bytes peak cgroup memory in the measured
8 GiB hard /7 GiB high /four-core /zero-swap envelope. Terminal receipts and all artifact hashes
were checked. Lifetime native accounting includes 241 starts /6,922.63 worker seconds; waiting
and offline verification are separate. [Frozen qualification report](evidence/libero/controller-restoration-v1.json).
The follow-up covers the other twelve previously qualified paths: free objects, a drawer,
a stove, simultaneous targets, a long sequence and the remaining Object tasks. **36 complete
on/off/repeat runs contain 6,426 actions and 107,100 recorded substeps**. All 24 instrumented
records are valid and all twelve examples retain native success in all three modes. Common
control/state/non-image arrays are exact across recording modes; repeated goals, scores and
substep files match, as do the original native model identities. Every instrumented run
retains constrained-acceleration and projected-body-effort negatives at unchanged bounds.

The package used 973.09 native worker seconds and at most 1,464,868,864 bytes peak cgroup
memory within the same 8 GiB hard /7 GiB high /four-core /zero-swap limits. All processes and
terminal resource receipts were verified. Cumulative native accounting is 277 starts /
7,895.72 worker seconds; queue waits and offline checks are separate. Together, the two
packages cover 19 exposed demonstrations across all fourteen previously qualified task
paths. Complete affected-task baselines, the other 116 task paths, source-history questions,
physical-reference validity and visual-policy evaluation remain open.
[Frozen twelve-path regression](evidence/libero/controller-path-regression-v1.json).

A separate source comparison rehashed both complete HDF5 files and compared the same 1,035
overlapping post-action states, with exact clocks and no validation trajectories. Alphabet
`demo_29` still fails and its maximum target/source translation difference increases from
131.64 to 511.85 mm; the successful Salad `demo_1` reference increases from 22.80 to 25.31 mm.
First-action finger-coordinate differences remain 5.37–5.39 mm across all seven examples.
These are descriptive source differences, not physical-error thresholds. Missing gripper and
controller history remains a hypothesis, not a demonstrated cause of the remaining failure.
[All joint/source comparisons](evidence/libero/controller-source-comparison-v1.json).

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

## Independent analytical references

`tests/test_libero_analytic_references.py` defines three synthetic references whose
expected values use declared constants and closed-form mechanics, without native
inertia, bias, force or acceleration caches as the reference:

| Fixture | Independent comparison | Error and interpretation |
| --- | --- | --- |
| Driven damped slider | For mass `m`, damping `b`, constant drive `F` and step `h`, use `r = m/(m + b h)` and `v_n = F/b + (v_0 - F/b) r^n`; sum the velocities for position. Compare the body load with `[F - b v_n, 0, m g]`. | Compare the finite-time position and velocity separately with the continuous exponential solution at 4, 2 and 1 ms. Agreement with the discrete recurrence does not erase its integration error. |
| Driven damped hinge | With COM radius `l` and central inertia `J`, use `alpha = (tau - b omega - m g l cos(theta))/(J + m l²)`. Derive COM acceleration and the support force from planar Newton–Euler mechanics. | The pivot moment includes the known drive/damping couple. The inferred subtree wrench is not a bearing-only measurement. A deliberately corrupted acceleration must disagree with the reference. |
| Centered free fall | Compare every momentum change with `m g h`, retaining the gravity direction. | Over duration `T`, semi-implicit Euler's vertical position error is exactly `-g T h/2` in this ideal constant-acceleration model, apart from arithmetic error; report it at all three step sizes. |

The fixtures declare gravity, mass, inertia, damping and drive as synthetic inputs.
They exclude contacts, material uncertainty, actuator dynamics and joint limits.
The predeclared `1e-10` absolute arithmetic acceptance allowance applies separately
to each fixture quantity in its own units (N, N m, m, m/s, rad/s² or N s). It is
neither a confidence interval nor a new bound for LIBERO records. Existing numerical
protocols remain unchanged. Recording-on/off native states must also match exactly.

These references qualify only the stated ideal load and integration paths. Physical
joint reactions in general articulated systems, contact/material accuracy and the
full task matrix retain their separate acceptance. The pinned
[integration specification](https://mujoco.readthedocs.io/en/2.3.7/computation.html#numerical-integration)
explains the implicit joint-damping and semi-implicit position updates used here.
Native results require the pinned 2.3.7 test environment; skipped tests are not
qualification evidence.

Set `LIBERO_PYTHON` to the qualified MuJoCo 2.3.7 interpreter, then run from the repository root:

```bash
PYTHONPATH=src:tests "$LIBERO_PYTHON" -m unittest test_libero_analytic_references -v
```

[Recorded results and provenance](evidence/libero/analytic-references-v1.json) preserve the reference errors and negative controls.

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
receipts and are not hidden within a native-throughput figure. The complete task matrix
remains open after the engineering delivery. Generalized forces
and inferred subtree loads do not by themselves qualify physical joint/support reactions;
uncomputed `cfrc` buffers are not observations. Independent physical references retain their
own acceptance. Numerical consistency, physical validity, native success and learned-policy
performance remain separate. Representative qualification never closes the 130-task parent.
