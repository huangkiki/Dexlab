# Simulation Failure Root-Cause Atlas

## TL;DR

DexLab's most reliable lesson is not that one engine is best. It is: **find the earliest layer that departs from the expected behavior, instead of treating the final visible symptom as the root cause.** Vanishing normal load before a bread slice falls, task failure after cloth penetrates a table, and a metric that worsens at a smaller timestep are outcomes. Their causes may begin earlier in grasp geometry, actuator budget, auxiliary constraints, collision coverage, contact laws, observation refresh or evidence recording.

This page applies five questions to the existing experiments: **symptom → first failing layer → causal chain → what the evidence proves and does not prove → the next attribution gate**. “Root cause” means only the earliest layer supported by present evidence. Insufficient cases remain `not uniquely identified`; successful or admission-only experiments are marked `no attributable failure observed`.

Every failure case that this page lists, classifies or uses to support a conclusion should reach this explanatory depth rather than stop at an error string or final-frame symptom. When the physics maps cleanly, add an everyday analogy and state its limits. The analogy explains a mechanism already supported by measurements and chronology; it is not evidence by itself. Summary tables may compress presentation, but detailed cards, linked evidence or an explicit `not uniquely identified` status must preserve the attribution boundary.

## Seven first-failure layers

| Code | First failing layer | Test | Representative case |
| --- | --- | --- | --- |
| **P Policy / task geometry** | Grasp point, action sequence, clearance, goal or termination logic fails first | The action has already brought the system into an unholdable state before contact or solver anomalies | RoboDojo top-edge pinch and neighbor interference |
| **A Control / actuator / assistance** | Force limits, controller state or hidden retention determines the outcome first | The force ledger closes with the control budget or an extra constraint | 0.2/0.4 N finger-force limit and RSS latch |
| **G Collision / geometric discretization** | Collision shape, mesh, contact points or scoring geometry fails first | Changing only geometric coverage moves the failure boundary | Historical cloth triangle/table intersection and cylinder surface refinement |
| **C Contact / material / coupling** | Friction, normal response, contact moment, bidirectional coupling or material mapping cannot support the task | Control and geometry are valid, but the needed force, moment direction or coupling is absent | Wuji point contact without torsion and Genesis PBD without tangential retention |
| **N Time discretization / stopping / precision** | Timestep, stopping criteria, residual or numeric representation fails its gate first | With model and inputs fixed, a numerical gate or refinement curve rejects the record | SuperDex contact onset and some incline/pinch records |
| **O Observation / adapter / scorer / evidence** | Stale state, field mapping, score coverage or recorder parity fails first | The input or measurement required for the dynamics claim is already untrustworthy | Stale LIBERO observation, AMP recorder parity and historical cloth scoring |
| **U Not uniquely identified** | Existing records narrow the range but cannot separate mechanisms | A controlled A/B, runtime readback or phase-aligned comparison is missing | MJWarp path differences and some multi-engine incline residuals |

A case can have a primary cause plus an amplifier. RoboDojo layout 011 is primarily **P: shallow top-edge grasp**, with lift acceleration as an amplifier. Missing compliance may contribute, but remains an unverified **C** mechanism and cannot replace the proven geometric chain.

## Coverage of existing experiments

### Fifteen historical demos

| Experiment | Observed failure or boundary | First failing layer | Current attribution |
| --- | --- | --- | --- |
| `apple-stem-grasp` | Historical ten-scene results are MuJoCo 1/10 and SuperDex 10/10; timestep, friction, drives and contact representations are unmatched | **U**, with C/G/control-configuration candidates | Fixed-profile robustness only. Backend differences do not identify an engine cause; a passing default development scene does not repair the historical cohort |
| `banana-cut` | Three cuts/four mechanically separated pieces pass; original development failures are retained | No attributable published failure observed | Establishes synthetic cut history and mechanical separation, not real-banana mechanics |
| `banana-force` | The 64× particle case does not reach anvil contact within 0.5 s; nRMSE is 2.051 | **O: comparison phase/window mismatch** | The comparison fails before reaching the same physical phase; it cannot establish refinement convergence or material-force error |
| `cloth-benchmark` | Seven configurations/105 records have different pass counts with unmatched materials and contact assumptions | **U** | Preserve protocol-specific outcomes; do not merge them into an engine ranking or common material failure |
| `cloth-folding` | Historical record has triangle/table intersection in 176/225 frames; historical bimanual runs also fail strain, release and final-state checks | **O → G**, followed by task geometry | Vertex scoring first misses the triangle crossing. The repaired 9 s single-hand candidate passes but does not complete the bimanual-fold claim |
| `contact-benchmark` | 25/38 early development runs pass; later studies separate geometry, response, transfer, unloading and numerical gates | **G/C/N/U**, per subprotocol | There is no single “contact benchmark cause”; see the cards below |
| `cut-push` | Numerical jitter, timestep effects and material differences remain; blade-driven pushing closes its force/motion ledger | **U** for uncalibrated material behavior | Establishes that blade contact drives the piece; not real-food accuracy. Passing records do not need an invented failure cause |
| `cutting-refinement` | Refined records pass mechanical checks | No attributable failure observed | Supports the specified synthetic checks, not a continuum limit or real-material convergence certificate |
| `libero-contact` | The official task may succeed, but evaluation uses a stale post-settling observation and physical diagnostics only partly pass | **O: state-refresh semantics** | A one-line refresh repairs observation identity. It does not establish policy improvement or assign remaining contact failures to the solver |
| `physx-contact` | Missing contact-report API is supplied by an adapter; among 15 cloth settings, one surface crossing and four unsupported external-force interfaces remain | **O/G/capability boundary** | Primitive passes prove local admission only. Unsupported API is not a physics failure; surface crossing needs separate geometric diagnosis |
| `rss-wiping` | With latch 3/3 pass; removing only the latch gives 0/3 | **A: auxiliary-retention dependence** | Task success depends on additional compliant node constraints; no-latch failure does not uniquely identify a contact solver |
| `tofu-comparison` | Historical two-cut and current knife-push inputs differ | **O: protocols are not directly comparable** | Do not combine the author's terminal initial velocity and current blade-contact push as one physical comparison |
| `tofu-cut` | Full-cut and uncut/partial-cut controls meet the protocol | No attributable published failure observed | Supports synthetic topology change, not arbitrary-pose cutting or real-tofu calibration |
| `tofu-knife-push` | Half-step, no-push and material controls are retained; real-material accuracy remains unqualified | **U** for material fidelity | Closes “what moved the final piece,” not material error |
| `tofu-scoring` | Default and half-step cases retain a connected base; uncut negative is rejected | No attributable failure observed | Supports specified guided incisions and connectivity scoring, not free cutting |

### Eight research experiences

| Experience | First failing layer and causal chain | Claim boundary |
| --- | --- | --- |
| `normal-response` | Fixed MuJoCo parameters change effective slope under mass transfer; some SuperDex/PhysX cases first hit stability or inertia-readback gates: **C/O** | Static stiffness matching is not dynamic-material equivalence; PhysX inertia serialization repair leaves the stability failure intact |
| `transient-cost` | High-impedance MuJoCo misses the target; SuperDex load-dependent damping creates transient tensile force on unloading and smaller steps do not remove it: primary **C**, with timestep as an **N** diagnostic/amplifier | 9/27 joint passes and 18 retained failures; whole-script time is not a solver ranking |
| `mass-size-transfer` | Three frozen mappings omit mass/area compensation and score 0/30 on the joint target: **C, parameter mapping outside its domain** | The frozen mappings fail; this does not prove a native algorithm error, and other mappings may work |
| `physx-observation` | Original adapter lacks or misclassifies contact/ground fields: **O, adapter semantics** | Repair restores observability; it does not automatically make every task pass |
| `pinch-load` | Low impedance creeps, high impedance improves; critical load loses/recontacts; six records are invalid by residual gates: **C + N** | 3/18 pass, nine physical failures and six numerical rejects. Smaller residual is not eliminated creep |
| `six-engine-incline` | Contact representation, friction regularization, stopping and precision differ by backend: **C/N/U** | Attribute per configuration only. Different denominators and gates do not support a total ranking |
| `framework-path` | CPU model/core alignment leaves GPU field and trajectory differences: **O/U** | Scope is narrowed to framework path/runtime fields but not a unique core algorithm |
| `libero-workflow` | Failure to refresh after settling creates 4.481 mm EE and 12.143 mm gripper-joint semantic discrepancies: **O** | Observation semantics are repaired, not policy benefit. The 1 ms physical diagnostic falls to 3/10 from 5/10 at 2 ms, so smaller steps are not an automatic fix |

### Remaining registered evidence families

These cohorts are not separate task directories, but they are part of the historical experiment ledger. `cloth-studio`, `cutting`, `force-limit`, `framework-mjwarp`, `genesis-cloth`, `libero`, `pinch-load` and `rss-wiping` already map to the tables or cards above/below and are not counted again.

| Evidence family | First failing layer | Root-cause conclusion and boundary |
| --- | --- | --- |
| `drake-contact-paths` / `drake-incline` | **C + U/N** | The kLagged friction formula reconstructs added tangential support, so sliding discrepancy includes a contact-approximation mechanism; five small impulse residuals remain unidentified |
| `elastic-impact` | No terminal-gate failure observed | 18/18 establishes only the bounded final-state checks; without continuous trajectories or measured material data it is not collision-accuracy evidence |
| `engine-qualification` | **O/G** | Version/API admission is not task admission. A newer MuJoCo cloth sample still penetrates the table; an upgrade does not overwrite that geometric failure |
| `genesis-incline` | **C/N** | Contact representation, the nominal-zero-friction floor and CG stopping consistency all affect outcomes; attribution remains per configuration |
| `impact-discrete` | No discrete-equation reconstruction failure observed | 54/54 matches the declared discrete update; this does not establish continuous-time physical accuracy |
| `impact-phase` / `impact-stiffness` | **G/N/C** | Contact-arrival phase, stiffness and timestep jointly change penetration. Floating-point boundary rejects remain, and the finest grid is not truth |
| `incline-comparison` / `incline-diagnosis` / `incline-friction` | **C/U** | Geometry is shared but contact models are not equivalent. Changing `impratio` alone does not remove the full failure set; soft-contact drift and sliding error remain |
| `mujoco-incline` | **C/N/U** | Elliptic passes 3/9 and pyramidal 0/9, with six numerical-consistency rejects. This is a fixed-profile result, not universal MuJoCo failure |
| `newton-incline` / `newton-xpbd` | **N/O**; no sphere–plane admission failure | Many incline positives first fail an FP32 numerical gate that is not a strict error bound; the separate XPBD sphere–plane positive/negative controls pass |
| `physx-incline` | **N/U** | PGS/TGS outcomes coexist with 13 numerical rejects; small TGS residuals remain unidentified |
| `superdex-incline` | **C/N** | 0.5 ms static drift, friction regularization and CG `STOPPED` residuals coexist. BFGS/SR1 at assembly=1 are effectively Newton steps and are not separate algorithm attributions |
| `pinch-impulse` | **N + C** | Tighter stopping tolerances reduce impulse residual while creep persists; better numerical closure is not repaired retention |
| `synthetic-tactile` | **A/O** | Gravity compensation first masks actual support and creates endpoint error. A local pass after longer tracking is a controller correction, not tactile-sensor fidelity evidence |
| `unisim-contact-migration` / `unisim-reuse` | **O**, no new cause in the qualified adapter scope | Twenty-one native/adapter rescores agree while retaining low-force failures; this establishes wrapper semantics, not new solver capability or task success |
| `studio` / `visual` | No physical root-cause verdict | Reuses existing trajectories and provenance for presentation; visual agreement is not a new simulation run or physical acceptance |

### Later additions

| Experiment | First failing layer | Current conclusion |
| --- | --- | --- |
| Wuji sphere pinch | **C: incomplete contact wrench space** | The point-contact force grasp map has rank five and cannot resist gravity torque about the pinch line; more normal force cannot create the missing moment direction |
| RoboDojo layout 002 | **P/G: top-edge pinch plus insufficient neighbor/shelf clearance** | Neighbor impulse amplifies rotation and the contact rolls over the edge; the close command is not missing |
| RoboDojo layout 011 | **P: top-edge shallow pinch**, with lifting as an amplifier | In-plane rotation and loss of edge margin precede the normal-impulse collapse; load does not “vanish for no reason” |
| AMP box lift | **O: recorder-parity qualification failure** | Two probes finish but recorded/unrecorded state differences exceed the gate. This does not establish an AMP policy lift failure; full episodes were not run |
| Contact-loss prediction | **O / model target** | Constant velocity lowers pose error while missing release events; low pose error is not contact-event prediction |

The [complete legacy inventory](solver-failure-inventory.md) retains all 50 public RSS entries, all evidence directories and successful negative controls. Manifests, plots and version attachments at the `docs/evidence` root belong to their parent cohorts and do not become independent experiments. This atlas does not relabel scoped passes in external examples as DexLab failure experiments.

## Representative root-cause cards

### 1. RoboDojo layout 011: why can it fall without a collision?

- **Symptom:** at step 188 bilateral normal impulse falls from about 0.25 N·s to 0.0019 N·s, followed by free fall; the close command remains `0`.
- **First failing layer: P, shallow grasp geometry.** From step 186 to 188, in-plane bread rotation relative to the wrist grows from about **6.93° to 12.45°**, while mean top-edge margin in the OBB proxy shrinks from **14.41 to 2.87 mm**. Only then does contact geometry disappear.
- **Causal chain:** shallow top-edge pinch → about **4.58 m/s²** upward wrist acceleration amplifies effective load → slice rotates about the pinch line and contacts roll upward → bilateral impulse collapses → empty fingers close farther → the slice falls and first hits the table at step 192.
- **Proved:** rotation and edge-margin loss precede impulse collapse; no neighbor/shelf impulse occurs before release.
- **Not proved:** without full tangential impulse, resolved runtime material pairing and native collision mesh, the contributions of friction, rigid edges, missing compliance and acceleration are not uniquely separable; this is not a proven PhysX solver defect.
- **Next gate:** hold the initial state fixed and A/B grasp depth `0.016 → 0.028 → 0.034 m`; read back the material pair, tangential impulse and contact patch before testing compliance.

[Videos and the paired diagnosis](robodojo-bread-slip.md) · <a href="_static/robodojo-bread-slip/layout-011-root-cause.json">Derived timeline JSON</a>

### 2. Wuji: why does a tighter pinch still rotate?

- **Symptom:** both v3 point contacts persist for all 4,000 hold steps, yet the sphere drifts and reaches about 29.336 rad/s.
- **First failing layer: C, one missing contact-wrench direction.** The pure-force grasp map has rank five and native contact torque about the normal is zero. A 0.310–0.985 mm sphere-center offset creates gravity torque about the pinch line.
- **Causal chain:** center-of-mass offset → torsion about the pinch line is required → point contact cannot supply it → rotation and drift continue despite contact and normal force.
- **Controlled evidence:** adding only synthetic torsional contact reduces two-second maximum displacement **2.734→1.025 mm** and angular-speed peak **29.336→0.024992 rad/s**.
- **Boundary:** this identifies a contact-model mechanism in this fixture, not calibrated fingertip material or a solver defect.

[Wuji report](wuji-contact.md)

### 3. The 0.4 N pinch: why is failure physically reasonable?

- **Symptom:** Genesis 0.2/0.4 N per-finger limits fail to retain; 0.8/10 N hold and release.
- **First failing layer: A, actuator budget.** At low limits the fingers provide only 0.2/0.4 N upward and the table still carries about 0.428/0.228 N. At 0.8/10 N, the fingers supply about 0.628 N, matching the approximately 0.628 N object weight while table support reaches zero.
- **Causal chain:** force cap → insufficient frictional support → table remains load-bearing → the object does not leave with the gripper.
- **Boundary:** a physically explained task failure, not a numerical-solver defect; ±2 mm controls preserve the outcome.

### 4. RSS wiping: why does “success” depend on hidden retention?

- **Symptom:** original task passes 3/3. Removing only the latch yields 0/3 and cleaning drops roughly 95.47%→39.92%, even with higher measured contact force.
- **First failing layer: A, auxiliary constraint.** `pin_nodes + ride` provides roughly 4,000 N/m and 20 N·s/m compliant retention; this is not a friction-only grasp.
- **Causal chain:** latch carries the sponge with the hand → the sponge remains between the fingers → wiping completes; without it the sponge leaves the jaws → press control fails and exits.
- **Boundary:** proves dependence on assistance, but does not uniquely separate contact-model and solver contributions in the no-latch case.

[Wiping comparison](rss-wiping.md)

### 5. Historical cloth grasp: why can a task score pass while cloth crosses the table?

- **Symptom:** the online protocol passes; independent checks find triangle interiors crossing the table in 176/225 saved frames, with 3.00 mm maximum depth.
- **First failing layer: O, incomplete scorer coverage; exposed physical layer is G.** Vertices above a table do not imply the triangle interior is above it.
- **Causal chain:** vertex-only check → misses triangle/table intersection → invalid trajectory is labeled pass → independent face check restores the actual verdict.
- **Boundary:** fixing the scorer does not repair the trajectory. The new 9 s single-hand candidate also does not replace historical bimanual strain, release and final-state failures.

### 6. Genesis PBD cloth: why does gravity compensation not make it lift?

- **Symptom:** the gripper rises 79.988 mm while cloth minimum height stays near 4 mm; both ±3 mm controls fail too.
- **First failing layer: C, insufficient PBD–rigid retention/coupling.** In the official path, nominal friction 0.01 and 5 produce identical trajectories and the patch slides about 60 mm at 0.2 m/s. Momentum response is also delayed by one 2 ms step.
- **Causal chain:** no observable tangential retention → finger surfaces cannot transfer lift friction → gravity compensation repairs only gripper elevation → cloth stays on the table; same-step momentum accounting rejects the delayed coupling.
- **Boundary:** scoped to this legacy PBD/rigid path and version, not all Genesis deformable configurations.

### 7. LIBERO: why can the task succeed while the record is semantically stale?

- **Symptom:** after five zero-action settling steps, evaluation still uses the pre-settling observation; EE position has changed 4.481 mm and gripper joints 12.143 mm.
- **First failing layer: O, observation lifecycle.** Environment state advances but the policy/scorer input is not refreshed.
- **Causal chain:** reset observation → extra settling changes state → no new observation → action and diagnostics begin from stale input.
- **Repair boundary:** one-line refresh restores identity, not proven policy benefit. Changing 2 ms to 1 ms reduces physical diagnostic passes from 5/10 to 3/10 and nearly doubles cost; timestep reduction cannot replace attribution.

[LIBERO report](libero-workflow.md)

### 8. Mass/size transfer: why does a tuned nominal point yield 0/30?

- **Symptom:** three frozen configurations across ten mass/size pairs yield 1/30 engineering passes, 0/30 transient-target passes and 0/30 joint passes.
- **First failing layer: C, the parameter mapping omits mass and area dependence.** Candidates reuse nominal-point parameters without mass/area compensation.
- **Causal chain:** nominal fit → mass/size changes → effective inertia, contact count or area changes → identical native parameters no longer represent the same synthetic K/D target.
- **Boundary:** rejects transfer of these three frozen mappings, not all mappings or the native algorithms.

### 9. Contact transients and pinch creep: why are more iterations or smaller steps insufficient?

- **Symptom:** SuperDex frictional contact-onset differences are non-monotonic from 1 to 0.125 ms; tightening stopping tolerances by 100/10,000× leaves about 3.206 mm difference. MuJoCo critical-pinch impulse residual falls with tolerance, but creep remains.
- **First failing layers: C + N.** Stopping error affects residual closure, while contact law/impedance still determines creep and unloading.
- **Causal chain:** tighter tolerance → better numerical closure; if the physical law still has load-dependent damping, soft contact or incomplete retention → task drift remains.
- **Boundary:** the finest grid is not truth; no convergence order or measured material reference exists.

### 10. Banana 64×: why does large RMSE not prove non-convergence?

- **Symptom:** refined nRMSE is 2.051, but particles have not reached anvil support within 0.5 s.
- **First failing layer: O, curves are from different event phases.** The baseline has experienced support contact; the refined case has not.
- **Causal chain:** refinement changes arrival time and compute budget → fixed window captures different event phases → direct curve RMSE mixes phase and force differences.
- **Next gate:** align by contact event or extend to a shared termination condition, then compare force–displacement. Present evidence establishes neither convergence nor non-convergence.

[Banana force study](banana-force.md)

### 11. AMP: why does a completed program still fail qualification?

- **Symptom:** two 0.2 s probes finish, but state parity with recording disabled/enabled exceeds the frozen threshold.
- **First failing layer: O, recorder qualification.** Full policy episodes cannot become dynamics evidence before recording is shown not to perturb the run beyond its gate.
- **Causal chain:** enable recording → state difference exceeds threshold → recording path fails admission → three-seed and no-hand-contact episodes stop.
- **Boundary:** this is experimental-instrument failure, not an AMP lifting-policy failure; the full task was not run.

[AMP recorder report](amp-lift.md)

## Six-engine incline: why not force one root cause?

The incline cohort is a set of per-configuration diagnoses, not one shared-cause experiment. MuJoCo combines cone/impedance choices with numerical-consistency rejects. SuperDex has 0.5 ms static drift plus CG stopping residuals. Genesis combines contact representation, a nominal-zero-friction floor and stopping accuracy. Many Newton positives are rejected first by an FP32 numerical gate. Some PhysX PGS/TGS residuals remain unexplained. Drake lagged friction reconstructs additional tangential support while small impulse residuals remain. The honest classification is **C/N/U**, scoped to each backend's protocol.

Without a common material target, equivalent contact representation, unified observations and shared numerical gates, adding pass counts only mixes “different model,” “invalid record” and “task failure” into a false ranking.

## The required order for every future failure

1. **Freeze the verdict.** Score task success, physical validity, numerical validity and record validity separately.
2. **Find the earliest change.** Order commands, actuator state, relative pose, geometric margin, contact count/impulse, external collision, residual and task outcome in time.
3. **Close conservation and budgets first.** Who supports the weight? Does the required moment direction exist? Do external force, impulse and momentum close?
4. **Change one variable.** Grasp depth, force cap, latch, collision mesh, contact model, timestep or tolerance—one at a time.
5. **Retain positive and negative controls.** Keep open/no-contact/zero-friction, no-ground, no-push, no-assistance and exact-repeat records.
6. **Read back runtime state.** A config file is not the resolved material pair, combine mode, solver, precision or collision shape.
7. **Stop at U when evidence stops.** If tangential impulse, hardware material data or native geometry is missing, state the next gate rather than promoting a candidate mechanism to a root cause.

The [legacy solver failure audit](solver-failure-audit.md) retains backend-specific and historical evidence. This atlas reorganizes that evidence by first failing layer. Neither page establishes real-material calibration or a universal engine ranking.
