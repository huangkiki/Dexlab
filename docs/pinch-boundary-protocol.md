# Common-fixture pinch boundary: protocol v1

[简体中文](pinch-boundary-protocol.zh-CN.md) · [Machine-readable contract][protocol] · [Roadmap](pinch-boundary-roadmap.md) · [A #131][a] · [Stage decisions][discussion]

**This delivery defines the protocol and data contract, not a qualified backend or a completed campaign.** [B #132][b] implements and admits the engines; [C #133][c] validates independent scoring and freezes the final execution manifest; [D #134][d] acquires and reports results. Historical guided-plane MuJoCo and native-position-drive Genesis data remain separate cohorts. The experiment measures drive-force-cap boundaries for specified configurations, not real-material thresholds, hardware accuracy or an engine ranking.

## Fixture and provenance

The [v1 JSON][protocol] is the numeric source of truth. It pins the source revision and hashes of the original Genesis fixture and criteria. Geometry, mass, axes, initial state and trajectory come from `genesis_pinch_probe.py`; common collision-pair enforcement, external PD, the expanded matrix, observation contract and independent geometric scoring are new protocol requirements. The old execution does not establish their qualification.

World coordinates are right-handed, metres/kilograms/seconds/newtons, z up. Quaternions are scalar-first `wxyz`; all initial orientations are identity and all initial velocities are zero. Gravity is `(0,0,-9.81) m/s²`.

| Body | Shape, mass and COM-frame diagonal inertia | Initial position / DOF |
|---|---|---|
| Table | Fixed horizontal plane z=0 | No moving DOF |
| Cube | 40 mm cube, 0.064 kg; each inertia `m*s²/6 = 1.706666666666667e-5 kg·m²` | `(case_offset,0,0.02)`, six free DOFs |
| Lift carriage | No collision geometry; 1 kg, inertia `(0.01,0.01,0.01) kg·m²` | `(0,0,0)`; +z slide, range `[0,0.15] m` |
| Left/right fingers | Box half-sizes `(0.01,0.03,0.02) m`; 0.1 kg each; inertia `(4.333333333333334e-5,1.6666666666666667e-5,3.3333333333333335e-5) kg·m²` | Centers `(-0.04,0,0.025)` / `(0.04,0,0.025)` relative to carriage; inward +x / −x slides, each `[0,0.03] m` |

Ordered generalized coordinates are **lift, left_slide, right_slide**, initially zero. Finger centers are `(-.04+q_left,0,.025+q_lift)` and `(.04-q_right,0,.025+q_lift)`. No finger rotation DOFs, object attachment or runtime state correction. Verify native pose/axes against this kinematics in B; C may reconstruct finger OBBs from the qualified coordinates.

Enable exactly six geometric pairs: cube/table, cube/left, cube/right, left/table, right/table and left/right. Explicitly verify self-collision/filter settings; importing the same names is insufficient. The static base/carriage has no colliders. Nominal friction is 0.5 on all four colliders; the nominal-zero control requests zero on all four. B records actual floors, combination rules, rolling/torsional terms and native contact/solver settings; those remain fixed per backend throughout the campaign. Equal nominal friction does not establish material equivalence.

Read back geometry, mass/inertia, axes, ranges, initial state, collision pairs and disabled damping/armature/drives. Numeric model comparisons use absolute tolerances of `1e-10 m`, `1e-12 kg`, `1e-14 kg·m²`, plus relative `1e-9`; discrete identities/axes/filter choices must match. These are preregistered import tolerances, not measured physical accuracy.

## Integer clocks and external control

Use one physical step of 1,000 / 500 / 250 µs per record. Native internal substeps must be one; solver iterations do not count as additional physical steps. The control period is always 1,000 µs. For zero-based step `i`, `t_before=i*h`, `t_after=(i+1)*h`, `tick=t_before//1000`; update only when `t_before%1000==0`, using the **pre-step state**. Hold the same target, raw command and clipped command between control updates; do not recompute PD at physics frequency. Record 4,000 control updates and 4,000 / 8,000 / 16,000 physics records over four seconds.

At control time `t` in seconds:

```text
closure(t) = 0.012 * min(t/0.5, 1) for t < 3.2; otherwise 0
lift(t) = 0.08 * clamp(t - 1, 0, 1)
q_ref = [lift, closure, closure]
u_raw = [1000,500,500] * (q_ref - q) - [50,20,20] * qdot
u = clip(u_raw, -[50,cap,cap], +[50,cap,cap])
```

The open control uses zero closure for the entire trajectory while retaining lift motion and a 10 N finger cap. Both axes use positive inward generalized force; right-finger world force points −x. MuJoCo uses force actuators with unit gear, Genesis direct generalized force. Disable hidden position drives, passive joint damping and added armature and verify effective values. No target-velocity feedforward or gravity compensation. Each engine closes the loop on its own state; identical force sequences are not required.

## Matrix and qualification

The first campaign is CPU FP64 for MuJoCo and Genesis, eleven per-finger caps `0.2,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8,10 N`, offsets `−2,0,+2 mm`, three physical steps and three fresh processes per condition with **seed 0 in every repeat**. That is 594 formal episodes, or 198 fixed conditions. Add 18 open controls across engine/offset/step and six nominal-zero-friction controls at center/10 N across engine/step. There is no interpolation claim across the unsampled 0.8–10 N gap and no population success-probability estimate.

The current, engine-free entry point expands stable IDs without claiming admission:

```bash
python -m dexlab.pinch_boundary list-cases --include-qualification > expanded-cases.json
```

It emits 650 identities and the hash of the exact protocol bytes read. Without `--include-qualification`, it emits the 618 formal/control identities. Repetition and signed offset are part of the ID; attempt UUIDs are separate. Changing a case, protocol or scorer after freeze requires a new campaign/version. The remaining five commands below are **B/C deliverables**, not implemented runners in A.

| Qualification family | Cases | Required observation / acceptance |
|---|---:|---|
| `known_force` | 2 engines × 3 steps = 6 | 40 ms, no contact/gravity, known generalized forces; mode disablement, native actuator output and analytic dynamics |
| `pd_clock` | 6 | 40 ms of common PD; exact target, clipping, direction, integer update clock and held commands; native output at every physical step |
| `contact_observation` | 6 | 100 ms with open fingers/cube on table; native world signs/partners/positions/normals, net/pair force accounting and momentum/epochs |
| `open_smoke` | 6 | Four-second open controls at center; no spurious finger support; full-rate record and observation validity |
| `hold_smoke` | 2 | Four seconds, center/10 N/500 µs; observation/record validity. Grasp failure alone does not disqualify an otherwise valid backend |
| `bridge_native` / `bridge_external` | Genesis × 3 steps × 2 = 6 | Separate four-second center/10 N runs, native position drive versus external PD, both with 1 ms target updates; retain both outcomes |

These **32 base qualification cases** include model readback. Stop admission on necessary observability, control, model or clock failures; do not spend the remaining qualification slots blindly after an unresolved blocker. Bridge native drive uses the same gains/force caps with direct-force mode off, and is labeled distinctly; it does not backfill old observations. Physical holding/release outcomes from bridge/smoke records remain separate from admission checks and formal statistics.

The known-force fixture retains the carriage/finger masses and axes, moves to `q=(.075,.015,.015) m`, disables gravity and every collision pair, and starts at rest. Its constant diagonal generalized mass is `(1.2,.1,.1) kg`. Apply four 10 ms phases: `[0,0,0]`, `[2,1,-1]`, `[-2,-1,1]`, `[0,0,0] N`. Verify native drives/damping/armature remain disabled, all states stay inside limits and no limit/contact force contributes in the three generalized coordinates. Cube observations are retained but excluded from this three-DOF analytic check. Any mode-switch preparation ends before the declared zero-velocity initial snapshot; no state writes occur during the measured interval.

**Three different force checks:**

1. Direct-force output: each component satisfies `abs(native_u - command) <= 1e-9 N + 1e-9*abs(command)`. Check the qualified API's applied force, not a copied command or force inferred from acceleration.
2. Contact-free dynamics: each step uses the known command `F` and mass `M`, with `||M*(v_after-v_before)-F*h||₂ <= 1e-10 N·s + 1e-6*||F*h||₂`. Independently integrate the piecewise-constant analytical position from the declared initial state. At each time, allow the first-order integration envelope `0.5 * sum_j(||M^-1 F_j||₂ * h_j²) + 1e-8 m`; this bound covers explicit/semi-implicit Euler position bias and is not fitted to measurements.
3. Cube contact ledger: world-component maximum error between summed per-contact forces and native net contact force is at most **1e-8 N**. The separate momentum criterion is below. These are not interchangeable tolerances.

B records official stable-compatible engine/core/binding/compiler identities, source/native binary hashes, precision/device, integrator, solver algorithm, iteration/tolerance budgets, contact law and effective readbacks before admission. Separate authored, native-read, pinned-source-derived and unavailable fields. A framework version, caller options or configured iteration bound does not establish the native core, resolved options or achieved iterations. Necessary state/actuator/contact observations missing from the v1 contract block admission. Optional native telemetry stays null with a reason, never a guessed default.

## Raw records and command contracts

The final frozen campaign manifest binds SHA256 identities of **protocol, expanded cases, model, acquisition code, scorer and environment**, with a per-backend admission receipt and actual native configurations. It also binds qualification attempts, source/license records, backend-specific model bytes, units/body maps and observation API/sign/epoch evidence. It contains no credentials or private deployment paths. A’s case export is not this execution manifest and must never authorize a run.

Each attempt has a new immutable directory with `receipt.json`, initial state, `steps.jsonl`, logs and `terminal.json`; large raw files may be losslessly compressed with both uncompressed and stored-byte hashes. Never overwrite an earlier attempt. Write full-rate samples, not plots or interpolated states. Atomically seal an artifact manifest after close; preserve interrupted partial files and their bytes.

| Step field | Contract |
|---|---|
| `step`, `t_before_us`, `t_after_us`, `control_tick`, `control_updated` | Exact integers / boolean; no floating-time dispatch |
| `state_before`, `state_after` | `q_m`, `qdot_m_s`, cube position/linear velocity/angular velocity and `cube_quaternion_wxyz`; each vector length 3 except quaternion length 4, finite values; quaternion squared norm error ≤1e-6 |
| `target_m`, `command_raw_N`, `command_N` | Separate ordered length-3 vectors; held between controller ticks |
| `actuator_force_N`, `cube_net_contact_force_N` | Native output and native cube net contact force; required, never zero-filled when absent |
| `force_epoch`, `geometry_epoch` | `applied_during_step`, `state_after`; native getter timing and any documented native geometry lag also live in the header |
| `contacts` | Every native contact involving the cube exactly once; partner `table/left/right`, world position, unit normal toward cube, force on cube; source IDs where available, never invented persistent IDs |
| Contact optional fields | `native_penetration_m` plus `native_penetration_m_missing_reason`; `native_id` plus `native_id_missing_reason`. Observed value and missing reason are mutually exclusive |
| `solver` | `status`, `iterations`, `convergence_residual`, `native_time_s`, each with a corresponding `_missing_reason`; list of native warning strings. Actual iterations are integer, not configured caps |
| Cost | Nonnegative `step_wall_s` and `observation_wall_s`; complete process wall time comes from the external supervisor and includes initialization/compilation/writes/shutdown |

Store source-specific raw contact fields alongside normalized observations where normalization is needed. Native contacts belong to the solve that advances the pre-state; do not claim that contact positions/depths were recomputed at the post-state. Per-contact identities need not persist across steps, and friction anchors need not map one-to-one to normal points. Any native force/impulse conversion must be documented and qualified against the corresponding step interval. `validate_step` checks shape/clock/availability only, not provenance, continuity or physics.

| Planned command | Inputs | Outputs and failures |
|---|---|---|
| `qualify` | Frozen qualification manifest, registered qualification ID and the campaign ledger | Fresh attempt, readbacks, known-reference/observability checks, admission or explicit blocker; consumes campaign allowance |
| `run` | Frozen campaign manifest, exact formal/control ID, ledger | One new attempt/process only after admission and budget reservation; immutable raw record/terminal event |
| `score` | Frozen manifest and one attempt, including retained failure prefix | Independent result: integrity, numerical state, geometry, hold/release/control outcome, first violations and costs; does not launch an engine |
| `report` | Manifest, all attempts and offline scores | Chinese/English report, static curves, case tables and figure-to-raw hash references; labels incomplete campaigns |
| `check-campaign` | Same frozen manifest, ledger, attempt artifacts, scores and report | Separate coverage, evidence-validity and task-outcome summaries; refuses wrong-hash reuse, missing/duplicate identity, lost attempts or inconsistent figures |

CLI exits must distinguish complete operation (0), valid but failed physical outcome (1), and invalid input/infrastructure/incomplete evidence (2); terminal/result JSON is authoritative. `check-campaign` may return 0 for a complete campaign containing physical failures. `report` can emit an interim artifact while returning 2 for incomplete delivery. Qualified numerical aborts have a finite contiguous prefix, actual first-failure evidence and a structured terminal event; an unexplained process exit or truncated JSON is not a numerical outcome.

## Independent scoring

All window tests use **post-step samples including both endpoints**. Hold `[2,3] s`: cube COM z ≥0.06 m, both fingers effective, and the sum of absolute vertical force components from non-finger contacts ≤0.01 N at every sample. A finger is effective if **any** of its native per-contact force magnitudes is strictly greater than `1e-8 N`; this retains the old definition and does not assert normal load or friction capacity. Report measured normal load separately by projecting onto native normals. Release `[3.8,4] s`: COM z ≤0.03 m and sum of individual finger-contact force magnitudes ≤0.01 N. Do not take the magnitude of a cancellation-prone total vector instead.

Open controls must stay at or below 0.03 m throughout and have no effective finger contacts in the hold window. Nominal-zero-friction controls retain ordinary hold/release metrics plus their negative-control interpretation; unexpected holding prompts examination of geometry/support and actual friction, not retuning or hiding the result. The `1e-8 N` presence threshold and ledger tolerance happen to have equal numeric values but are distinct criteria.

Cube momentum uses `||m*(v_after-v_before) - (sum_contact_force + m*g)*h||₂ / (m*9.81*h) <= .05` at every complete step, including the initial step. There is no external force on the cube in formal/control cases. Report record integrity, numerical state, penetration, holding and release separately; a failed grasp with valid evidence is an experimental outcome.

Common geometry uses the same `state_after` for every pair. Cube/table and finger/table use analytic oriented-box support: `max(0, sum_i(half_i*abs(axis_i.z)) - center.z)`. For two finite OBBs, test all six face normals and nine edge-cross-edge directions; skip **only zero-length** parallel cross products, normalize every other axis. For unit axis `n`, compute `s(n)=r_A(n)+r_B(n)-abs((c_B-c_A)·n)`, with `r(n)=sum_i(half_i*abs(axis_i·n))`. If any `s<=0`, penetration is zero; otherwise penetration is `min s` over the complete axes. This is the minimum translational separation depth at fixed orientations, not the intersection-interval length (which is wrong for containment). The separating-axis basis follows [Eberly's OBB derivation](https://www.geometrictools.com/Documentation/DynamicCollisionDetection.pdf), sections 2.1–2.2. Normalize valid recorded quaternions for the geometry calculation without rewriting the raw state; reject nonfinite/invalid geometry rather than calling it no collision.

Score all six enabled pairs with the **1 mm** common-depth budget; retain pair IDs and first violating sample. Native depth is separately labeled with its own sampling epoch and 1 mm check where observable. Missing native depth is explicitly unavailable, never zero or a native pass; it does not replace the required common geometry. C must cover rotated edges, near-parallel and exactly parallel boxes, full containment, separation, touching and disabled-pair controls. This is discrete-step geometry, not continuous collision detection or material deformation.

Retain all three repeats, first recorded threshold violation, relative fixture displacement/velocity, actual normal loads, contact impulse and costs. The first threshold violation is not the physical onset of slip. Only monotonic measured results support a tested-grid transition interval; reversals/mixed repeats yield passing segments and mixed outcomes.

## Recoverable budget and completion

B first allocates one immutable campaign UUID and its persistent budget ledger. Before any qualification attempt, freeze a **qualification manifest** binding that UUID, protocol/case/model/acquisition/qualification-checker/environment hashes and candidate native configurations. It does not depend on future qualification results. A’s case export cannot serve as this manifest.

After qualification and independent C acceptance, freeze a **formal manifest** that extends the exact qualification-manifest hash, retains the same campaign UUID and ledger, and binds all qualification attempts, charged costs, admission evidence and the final scorer. Append authorization of its hash to the existing ledger; do not recreate or zero the ledger. Protocol, cases, model, environment and acquisition behavior must remain the qualified versions; changed versions need renewed reviewed qualification and a budget decision, never automatic allowance rollover. Each attempt names its phase and exact manifest hash. Unknown hashes, a broken manifest chain, changed campaign identity or missing earlier costs block execution. B/C must test recovery across this transition, including interruption before/after formal-manifest authorization.

The one-worker ledger is the persistent campaign authority; it binds the campaign UUID, initial qualification-manifest hash and authorized formal-manifest extension. Qualification and formal attempts share one cumulative allowance. Before spawning, atomically reserve one attempt UUID/case ID, one start and a timeout no greater than `min(1800 s, remaining wall allowance)` under the existing exclusive research lock. Persist `reserved` before spawn, then `running` with a verifiable process/service identity, boot ID, start clocks and deadline. A reservation conservatively counts as a start even if launch fails; never delete it or reset the ledger on resume.

The supervisor terminates the entire process group/service at the deadline and charges full launch-to-exit wall time. On recovery, first inspect the recorded live handle; observation timeouts are not process termination. Do not duplicate a live attempt. Reconcile a terminal attempt using supervisor evidence; if elapsed time cannot be recovered, retain its full timeout reservation as charged cost and classify the attempt as infrastructure failure. The budget must never grow because a process, machine or coordinator restarted. Persist append-only attempt events; atomic ledger snapshots may be rebuilt from those events, not from successful runs alone.

The cap is 21,600 cumulative process seconds and 700 starts, including qualification/bridge/formal/control/retry attempts. At most 650 base identities leave at most 50 extra starts. At most one retry per case is allowed, only for an infrastructure or recording failure, still subject to both global caps; physical failure is not retryable. A failed attempt remains visible even when a permitted retry yields valid evidence. Development/submission regression accounting is separate, but campaign attempts cannot be renamed debugging to evade the allowance.

Before formal launch, use complete four-second qualification process costs at every backend/step to estimate remaining work (at least the maximum observed matching cost times each remaining case count). Archive the cost basis and remaining allowance. If projection exceeds the allowance, block the formal launch and report the recovery decision in [D][d]/[Discussion][discussion]; do not promise completion or silently reduce the matrix. Measurement is a feasibility estimate, not a guarantee. If an admitted campaign later exhausts its budget, retain all attempts and mark remaining identities not-run with recovery conditions.

Complete delivery requires **all 594 formal and 24 control identities** to have a valid experimental terminal outcome, every attempt retained, independent rescoring and all report numbers/figures traceable to frozen raw records. `completed` can contain holding/release/penetration failures; `numerical_abort` can count only with the required reproducible prefix and first failure. `not_run`, unrecoverable corruption or exhausted infrastructure retries mean interim delivery. A bridge, a smoke test, a complete list of failed launches or a report file alone cannot satisfy the campaign. C must demonstrate recovery/no duplicate claim, budget non-reset, wrong-hash rejection, failure preservation and figure regeneration before freezing.

## Six-engine scope and next gate

| Engine | Common-fixture status | Recovery / qualification |
|---|---|---|
| MuJoCo | unqualified; first cohort | [B][b]: official stable CPU FP64, finite model, direct-force/native-output and contact-epoch checks |
| Genesis | unqualified; first cohort | [B][b]: official stable CPU FP64, disabled native drives, effective solver readback, direct force and separate bridge |
| SuperDex | not-run; later expansion | [Parent #130][parent]: common fixture/control qualification; old #124 cannot substitute for new runtime evidence |
| Newton Physics | not-run; later expansion | [Parent][parent]: applicable solver/precision admission; existing XPBD float32 evidence does not establish this FP64 cohort |
| PhysX | not-run; later expansion | [Parent][parent]: native core, common fixture and observable forces; old #126 remains a separate historical gap |
| Drake | not-run; later expansion | [#117](https://github.com/huangkiki/Dexlab/issues/117) and [parent][parent]: positive-duration model/control/observation qualification |

Keep the six-engine parent open after the first cohort. Return to the same Discussion after B qualification and D reporting, and convert subsequent actions into Issues. Discussion decisions change run behavior only through reviewed versioned protocol/manifest changes. A uses the repository's full scientific-change gate, including both 14-second regression episodes and independent acceptance; those regression results do not qualify this new fixture.

[protocol]: ../demos/contact-benchmark/pinch-boundary-v1.json
[a]: https://github.com/huangkiki/Dexlab/issues/131
[b]: https://github.com/huangkiki/Dexlab/issues/132
[c]: https://github.com/huangkiki/Dexlab/issues/133
[d]: https://github.com/huangkiki/Dexlab/issues/134
[parent]: https://github.com/huangkiki/Dexlab/issues/130
[discussion]: https://github.com/huangkiki/Dexlab/discussions/129
