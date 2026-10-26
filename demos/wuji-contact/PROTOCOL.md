# Wuji fixed-wrist contact qualification — prospective development protocol

This is a synthetic numerical experiment, not a hardware-calibrated hand or a solver-failure claim. Freeze this document, `protocol.json`, source and asset identities before the first physics step. All six cases are development controls, never held-out validation for #48.

## Model and static admission

Use the published Wuji Hand 2 Beta 1 right-hand prefab from SuperDex assets at `f216dace36464d70f224caa4253074ec365ed14f`, verified through `assets.json`. The source prefab SHA-256 is `624af8b45f2bef30302d082a806d9839fc007dc2e60cbf23155e90734b346567`. Preserve all 20 joint frames, source mass/COM/inertia, limits, effort caps and explicit contact exclusions. Replace only the free wrist root by a declared world-fixed transform. No arm, table support or idealized replacement fingers participate.

MuJoCo 3.17.0 uses the convex hull of each original collision mesh, separately from the visible mesh. This is a declared rigid-contact approximation; it is not source SDF equivalence. The object is an analytic sphere, radius 10 mm, mass 20 g, diagonal inertia `2 m r² / 5`. Initial object position is the midpoint of the existing measured thumb/index pad targets. Orient the pinch axis horizontally. SI units and right-handed world coordinates apply; gravity is `(0,0,-9.81)` m/s².

Static admission, before dynamics: separate JSON FK must match native body transforms within 1e-9 m / matrix entries. The 26 mm open target has no object contact. The 19 mm closure target intersects only the thumb/index pads, approximately 0.51/0.59 mm in this purely kinematic target; it is not a measured dynamic penetration. IK target errors are below 0.001 mm. The source has 36 hand links, 20 hinges; the resulting scene has 38 bodies including world/object and no equality constraint. Source geometry supports a candidate two-pad pinch; it does not prove a feasible force-controlled grasp.

## Commands and measured observations

`protocol.json` is authoritative for numeric settings. Native timestep 0.5 ms; controller zero-order hold every 4 steps (2 ms). Use synthetic PD gains 12 Nm/rad and 0.08 Nms/rad with native bias-force compensation, clipped to each asset's declared effort cap. These are synthetic controller choices, not measured motor behavior. Log requested torque, native actuator force and saturation separately.

Start at the open posture. Close smoothly from 0.2–0.8 s. Preparation applies an explicit object centering spring/damper and gravity compensation until 1.0 s. Save every preparation wrench; after 1.0 s all auxiliary force/torque and state injection are forbidden. No latch, weld, object teleport, floor support or prescribed object trajectory occurs in the scored interval. Hold from 1.2–3.2 s, then ramp the action over 0.4 s and observe until 4.4 s. The 0.2 s interval after support removal is declared settling, not scored holding.

Cases, in this fixed order:

1. `hold-release`: hold, open both fingers and observe release.
2. `unload-index_finger`: same hold, open only index; thumb retains its command.
3. `unload-thumb`: same hold, open only thumb; index retains its command.
4. `open`: fingers remain open.
5. `no-contact`: disable both contact masks on the object; other hand physics stays enabled.
6. `zero-friction`: zero every geom friction component so MuJoCo's pair mixing cannot retain the other surface's coefficient.

The last three must not be mistaken for a qualified grasp. Zero-friction retention requires inspection of actual normals and geometric support; it is not automatically a solver defect. An unload case may legitimately drop a sphere after losing one of only two supporting contacts. Assess measured unloading separately from continued retention.

Save pre/post-step qpos and qvel, every object contact's native pair identity, world position, frame, distance and six-component force, every actual actuator force, external wrench, joint-force input, penetration, warning counter, per-island iteration count and last-iteration gradient/improvement. No-iteration steps are distinguished by their count; a zero placeholder is not evidence of convergence. Native contact force belongs to the pre-integration solve and acts on geom2 in the contact frame. Record wall cost independently of task success.

## Independent acceptance and rationale

- **Integrity:** complete clocks/arrays, continuous pre/post states, native force reconstruction, no warnings, no auxiliary scored force/equality and actual torque within source caps. Partial or interrupted records remain invalid, never task successes.
- **Linear momentum:** reconstruct world force from native contacts, then evaluate `m(v_after-v_before) - dt(sum(F_contact)+mg+F_preparation)` each step. Absolute residual <= 1e-6 Ns (about 1% of a gravity impulse per step). This checks temporal/sign consistency, not material fidelity or unique contact-force truth.
- **Holding:** displacement from the state at support removal <= 2 mm, speed <= 0.05 m/s throughout the two-second window; both pads carry at least 0.02 N for >= 99% of its steps. Non-pad object contact <= 0.002 N. Maximum native penetration during holding <= 1 mm. The displacement bound is 10% of sphere diameter and the penetration bound 10% of radius: explicit task tolerances, not claims of universal numerical accuracy.
- **Release:** after the ramp plus 0.2 s, all object contact force <= 0.002 N; object descends >= 50 mm by the end. Holding without release is insufficient.
- **Unloading:** the selected pad's late maximum normal force <= max(0.02 N, 5% of its mean during hold). Report object loss and other-pad force independently.
- **Negatives:** independently score the same hold criteria. Never alter thresholds, retain the sphere with support or delete a failed attempt to obtain a positive control.

If the positive control fails, stop further native starts and solver attribution. Diagnose the first failing layer using the recorded geometry, commands, saturation, contacts and momentum checks; do not start a hidden parameter search. A negative result can be reported, but unexecuted controls and the #48 dependency stay explicit.

## Scope and finite resources

`applicability.json` freezes the first admitted native path plus all 74 historical registered profile rows. Historical rows are not-run under this protocol, not silently requalified or called unsupported. Other-engine matched fixtures require independent later qualification under #48; this slice establishes no cross-engine comparison.

Use the existing durable `MigrationBudget`, a new work package capped at 12 native starts and 7,200 seconds cumulatively, 900 seconds per process (stricter than the planning ceiling of 30 minutes). At most one evidenced infrastructure retry for an unrecorded case; recorded results are never retried. Source corrections inherit prior ledger consumption; neither a new directory nor source revision resets the allowance. Stop on missing observations, positive-control failure or exhausted budget. Static construction/FK, synthetic scorer tests, rendering and mandatory repository regression are separately accounted and are not new development cases.

Choose the immutable adaptive resource envelope from the measured static-model receipt, require actual cgroup limits/final telemetry and zero swap, and serialize simulation against transfers/compression. Preserve all attempts, interruptions and raw records. A continuous close-up must be rendered from these same states; visual quality cannot replace numerical acceptance. #48's contact switching, signed rotation and ten new post-development validation conditions remain separate.
