# What do we mean when we discuss the Sim-to-Real Gap?

This article reorganizes the existing experiments around one question: what does it mean for a simulation to “look right” or complete a task?

## The short answer

The Sim-to-Real Gap is usually described as an error, one failed rollout, or the observation that “simulation differs from reality.” None of those descriptions is specific enough to test.

A more useful definition is that **the gap is an evidence chain that can fail at multiple layers.** A task or embodiment may not represent reality; requested parameters may never reach the engine; units, initial state and actuator budgets may already be wrong; geometry, contact and coupling may not support the task; timestep and stopping conditions may invalidate the record; observation, scoring and logging may turn failure into apparent success; and even if all of these checks pass inside a frozen model, no hardware data means no measured real-world error.

DexLab therefore does not begin with “which engine is best.” It begins with the earliest layer that departs from the expected behavior. Vanishing normal load before a bread slice falls, task failure after cloth penetrates a table, and a metric that worsens at a smaller timestep are outcomes. The first failing layer may be earlier in grasp geometry, actuator budget, auxiliary constraints, collision coverage, contact laws, observation refresh or evidence recording.

> **Without hardware experiments, DexLab can establish parameter delivery, internally consistent records, conservation and budget closure, valid positive/negative controls, and reproducible regressions after parameter changes. It cannot establish real sensor timing, actuator response, material parameters or completed sim-to-real transfer.**

This page applies five questions to every experiment: **symptom → first failing layer → causal chain → what the evidence proves and does not prove → the next attribution gate**. “Root cause” means only the earliest layer supported by present evidence. Insufficient cases remain `not uniquely identified`; successful or admission-only experiments are marked `no attributable failure observed`.

## The gap is a chain, not one quantity

<div class="gap-chain" role="group" aria-labelledby="gap-chain-title">
  <div class="gap-chain-copy">
    <p id="gap-chain-title">A failed simulation can depart from reality at any layer.</p>
    <strong>Find the earliest divergence before explaining the final outcome.</strong>
  </div>
  <ol class="gap-chain-track">
    <li><span>01</span><strong>Task &amp;<br>embodiment</strong><small>Is this the same problem?</small></li>
    <li><span>02</span><strong>Parameter<br>delivery</strong><small>Did configuration reach runtime?</small></li>
    <li><span>03</span><strong>Units &amp;<br>initial state</strong><small>Does every trajectory share one origin?</small></li>
    <li><span>04</span><strong>Actuator<br>budget</strong><small>Who supplies the required force and torque?</small></li>
    <li><span>05</span><strong>Geometry, contact<br>&amp; material</strong><small>Does the required mechanism exist?</small></li>
    <li><span>06</span><strong>Observation, score<br>&amp; recording</strong><small>Is the conclusion reading valid state?</small></li>
    <li><span>07</span><strong>Hardware<br>validation</strong><small>Was real-world error measured?</small></li>
  </ol>
  <div class="gap-chain-boundary">
    <span><b>P/A/G/C/N/O</b> are tested inside the model through readback, controls, conservation and regression</span>
    <span><b>Hardware validity</b> is not supplied by passing the first six layers in simulation</span>
  </div>
</div>

| Check layer | Question | What goes wrong if this layer fails first |
| --- | --- | --- |
| 1. Task and embodiment | Do the task, robot, objects, environment and success conditions represent the real problem? | A stable engine may be answering a different question |
| 2. Parameter delivery | Did mass, inertia, friction, contact pairs, solver and precision actually reach runtime? | Correct files and YAML do not establish correct native state |
| 3. Units, initial state and clocks | Are length, mass, angle, gravity, reset, control and physics steps consistent? | Every later trajectory starts from the wrong state |
| 4. Actuator and force budgets | Who supplies finger force, torque, support, work and energy? | “Cannot grasp” may be a physically reasonable failure |
| 5. Geometry, contact, material and discretisation | Can collision shape, normal, friction, contact moment, coupling and timestep express the needed mechanism? | Contact does not imply support, and penetration does not imply solver error |
| 6. Observation, scoring and recording | Are policy and scorer reading fresh state? Does scoring cover the real failure? Does logging perturb the run? | Stale input, missed failures or recorder drift can create a false conclusion |
| 7. Hardware validation | Were real sensors, actuators, materials, timing and task performance measured? | Simulation-internal passes are still not sim-to-real validation |

The diagnostic labels remain `P/A/G/C/N/O/U`: `P` covers task and geometry; `A` covers control, actuators and assistance; `G` covers collision and geometric discretisation; `C` covers contact, materials and coupling; `N` covers time discretisation, stopping and precision; `O` covers observation, adapters, scoring and evidence; and `U` means the present records cannot uniquely separate mechanisms. A case can have a primary cause plus an amplifier. An amplifier never replaces the first proven failing layer.

## Representative experiments

| Research layer | Representative evidence | Central judgment |
| --- | --- | --- |
| Task geometry | RoboDojo layout 011 | The bread rotates under a shallow pinch and top-edge margin falls from 14.41 to 2.87 mm before normal impulse collapses; the final drop is not the cause |
| Actuation and hidden assistance | 0.4 N pinch and RSS wiping | Low finger force leaves table support active; RSS passes 3/3 with a latch and 0/3 without it |
| Geometry and coupling | Historical cloth and Genesis PBD | Vertex scoring can pass while triangle interiors cross the table; nominal friction can change while tangential retention remains absent |
| Contact-moment space | Wuji point contact | Both fingers stay in contact while the sphere rotates about the pinch line; adding torsion lowers peak angular speed from 29.336 to 0.024992 rad/s |
| Parameter transfer and transients | Mass/size transfer and contact onset | Nominal calibration can pass while 0/30 joint transfer targets fail; tighter stopping tolerance does not remove creep |
| Observation and comparison semantics | LIBERO, banana 64× and AMP | Stale observations, mismatched contact phases and recorder affects must be excluded before dynamics attribution |
| Multi-engine comparison | Six-engine incline | Equal task names do not establish equal material targets, contact representations or numerical gates, so a combined ranking is false |
| Hardware validation | Acquisition protocol | A protocol exists, but no qualified hardware dataset does; hardware experiments remain zero |

Together, these experiments show that **the Sim-to-Real Gap is not the difference between a final frame and a video. It is the gap between a claim and the evidence that would make the claim trustworthy.**

## Where the gap breaks in the recorded evidence

<div class="gap-evidence-gallery">
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="robodojo-bread-slip.html" aria-label="Open the complete RoboDojo layout 011 record">
      <img src="_static/robodojo-bread-slip/layout-011-preview.gif" alt="RoboDojo layout 011 recording of shallow top-edge pinch, bread rotation and loss of contact geometry" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">P · Task geometry</span>
      <strong>The bread does not simply “drop”</strong>
      <p>Before bilateral normal impulse collapses, mean top-edge margin in the OBB proxy has already fallen from <b>14.41</b> to <b>2.87 mm</b>. Only then does contact geometry disappear.</p>
      <small><b>Evidence boundary:</b> The image shows orientation change. The first failing layer comes from the phase-aligned margin, rotation and impulse timeline, not from guessing at the GIF.</small>
      <a href="robodojo-bread-slip.html">Open the complete layout 011 record →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="_static/force-limit/comparison.gif" aria-label="Open the Genesis low-force pinch comparison GIF">
      <img src="_static/force-limit/comparison.gif" alt="Genesis pinch and lift comparison at 0.4 N and 0.8 N per-finger force limits" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">A · Actuator budget</span>
      <strong>“Cannot grasp” may only mean “cannot afford the force”</strong>
      <p>At low limits, fingers provide only <b>0.2/0.4 N</b> while the table still carries about <b>0.428/0.228 N</b>. At 0.8/10 N, the object finally leaves with the gripper.</p>
      <small><b>Evidence boundary:</b> This is a physically explained failure, not a numerical-solver defect. The image is a measured-pose replay; support comes from the force ledger.</small>
      <a href="visual-comparisons.html#pinch">Open the pinch and release comparison →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="wuji-contact.html" aria-label="Open the complete Wuji point- and torsional-contact report">
      <img src="_static/wuji-contact/comparison.gif" alt="Synchronized Wuji point-contact failure and torsional-contact pass in the same task" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">C · Contact wrench space</span>
      <strong>Contact can persist while the sphere rotates</strong>
      <p>Both point contacts remain present, yet peak angular speed reaches about <b>29.336 rad/s</b>. Adding only the torsional direction lowers it to <b>0.024992 rad/s</b>.</p>
      <small><b>Evidence boundary:</b> This identifies a missing contact-moment direction in this fixture; it does not calibrate real fingertips or indict every solver.</small>
      <a href="wuji-contact.html">Open the contact model and hold curves →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="visual-comparisons.html#incline" aria-label="Open the complete six-engine incline comparison">
      <img src="_static/visual/incline-static-0.001.png" alt="Six physics engines in the same incline scene, with versions, precision and pass or failure labels" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">C · N · U</span>
      <strong>One task name is not one physical target</strong>
      <p>The incline cohort records static, sliding and nominal-zero-friction cases separately. Contact representation, precision, stopping gates and invalid records must remain configuration-specific.</p>
      <small><b>Evidence boundary:</b> The figure supports configuration differences and rejection reasons. It does not support adding unlike budgets and gates into an engine ranking.</small>
      <a href="visual-comparisons.html#incline">Open synchronized replay and the full matrix →</a>
    </figcaption>
  </figure>
</div>

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
| RoboDojo v67 `s0/l025`, `s1/l026`, `s1/l049` | **P → U(A/C/N): deep insertion continues after a slot jam; internal escape attribution remains unresolved** | During a downward target, observed-joint FK places TCP 10.6–28.3 cm higher. This establishes simulated state escape, not that the solver alone supplied all energy |
| AMP box lift | **O: recorder-parity qualification failure** | Two probes finish but recorded/unrecorded state differences exceed the gate. This does not establish an AMP policy lift failure; full episodes were not run |
| Contact-loss prediction | **O / model target** | Constant velocity lowers pose error while missing release events; low pose error is not contact-event prediction |

The [complete legacy inventory](solver-failure-inventory.md) retains all 50 public RSS entries, all evidence directories and successful negative controls. Manifests, plots and version attachments at the `docs/evidence` root belong to their parent cohorts and do not become independent experiments. This atlas does not relabel scoped passes in external examples as DexLab failure experiments.

## Complete failure-case cards

The cards below retain the original numbers, timelines, evidence and next gates. The representative table provides a reading path; these cards keep the synthesis verifiable rather than turning it into an unsupported summary.

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

### 12. RoboDojo v67: why does a downward press jump upward?

- **Symptom:** all three cases target `z=0.924 m`, but post-action TCP reaches `1.049–1.258 m`, rising 10.6–28.3 cm from its pre-action pose with 13.0–47.8 cm total target error.
- **First failing layer: P, a deep position target continues after slot jamming.** `s1/l026` and `s1/l049` have already stopped 19/28 mm high before escape; in `s0/l025`, jam and escape occur in the same `seat` action. Transport did not first lose the slice.
- **Causal chain:** insertion-pose/clearance miss → bread/finger/rim enters constrained multi-contact → stiff active drive continues doing work → observed joint state escapes upward and sideways over 40–44 ms → grasp releases or withdrawal/IK fails → slot occupancy cannot be confirmed and the task stops.
- **Proved:** `final_xyz` is FK of post-step observed joints, not planner fallback. The frozen source also contains risk amplifiers—4400 arm stiffness, zero velocity iterations, stabilization off and a mismapped bread-friction field.
- **Not proved:** the batch lacks per-step drive effort, contact impulse, penetration and resolved runtime material pairing. The actuator is itself an energy source, so endpoint pose cannot prove that a passive solver created all excess energy. The A/C/N split remains U.
- **Next gate:** retreat 20–30 mm on first jam; freeze the three cases and A/B velocity/position iterations, stabilization, depenetration velocity and timestep; close a 4 ms energy ledger with `Στ·Δq`, contact impulses and `Δ(K+U)`.

[Full wrist GIFs, per-case timelines and repair order](robodojo-bread-slip.md) · <a href="_static/robodojo-bread-slip/contact-escape-v67.json">Machine-readable evidence</a>

## Six-engine incline: why not force one root cause?

The incline cohort is a set of per-configuration diagnoses, not one shared-cause experiment. MuJoCo combines cone/impedance choices with numerical-consistency rejects. SuperDex has 0.5 ms static drift plus CG stopping residuals. Genesis combines contact representation, a nominal-zero-friction floor and stopping accuracy. Many Newton positives are rejected first by an FP32 numerical gate. Some PhysX PGS/TGS residuals remain unexplained. Drake lagged friction reconstructs additional tangential support while small impulse residuals remain. The honest classification is **C/N/U**, scoped to each backend's protocol.

Without a common material target, equivalent contact representation, unified observations and shared numerical gates, adding pass counts only mixes “different model,” “invalid record” and “task failure” into a false ranking.

## No hardware data: how can physical correctness be checked?

The answer is not “the simulation looks real.” Separate the claims that can be tested independently:

1. **Implementation consistency:** Did configuration reach runtime, and do records match actual state?
2. **Mathematical consistency:** Do units, initial state, force-displacement, momentum, angular momentum and energy close?
3. **Numerical reliability:** With physics fixed, vary timestep, tolerance, precision and budget; report sensitivity instead of assuming finer is more real.
4. **Physical boundary:** Do normal support, friction cone, contact moment, non-penetration, coupling and release satisfy the current model assumptions?
5. **Scoring validity:** Are positives, negatives, idle, no-contact, zero-friction, hidden support and wrong-reset controls classified correctly?
6. **External validity:** Only real sensor, actuator, material and task measurements can evaluate the corresponding reality gap.

The first five layers can be investigated through simulation, analytical references and negative controls. The sixth cannot be replaced by the first five. DexLab has completed parts of the first five layers in bounded profiles; hardware experiments remain **0**, so it does not claim measured material error, hardware-timing error or completed sim-to-real transfer.

## The required order for every future judgment

1. **Freeze the verdict.** Score task success, physical validity, numerical validity and record validity separately.
2. **Find the earliest change.** Order commands, actuator state, relative pose, geometric margin, contact count/impulse, external collision, residual and task outcome in time.
3. **Close conservation and budgets first.** Who supports the weight? Does the required moment direction exist? Do external force, impulse and momentum close?
4. **Change one variable.** Grasp depth, force cap, latch, collision mesh, contact model, timestep or tolerance—one at a time.
5. **Retain positive and negative controls.** Keep open/no-contact/zero-friction, no-ground, no-push, no-assistance and exact-repeat records.
6. **Read back runtime state.** A config file is not the resolved material pair, combine mode, solver, precision or collision shape.
7. **Stop at U when evidence stops.** If tangential impulse, hardware material data or native geometry is missing, state the next gate rather than promoting a candidate mechanism to a root cause.

The [legacy solver failure audit](solver-failure-audit.md) retains backend-specific and historical evidence. This article reorganizes that evidence into the layers of a Sim-to-Real Gap. Neither page establishes real-material calibration, hardware validation or a universal engine ranking.

## References

1. <a id="ref-reality-gap"></a>Elie Aljalbout et al. [The Reality Gap in Robotics: Challenges, Solutions, and Best Practices](https://arxiv.org/abs/2510.20808). arXiv:2510.20808, 2025.
2. <a id="ref-mujoco-paper"></a>Emanuel Todorov, Tom Erez, and Yuval Tassa. [MuJoCo: A physics engine for model-based control](https://doi.org/10.1109/IROS.2012.6386109). IROS, 2012.
3. <a id="ref-mujoco-docs"></a>Google DeepMind. [MuJoCo documentation](https://mujoco.readthedocs.io/). Current official engine and contact documentation.
4. <a id="ref-genesis"></a>Genesis Authors. [Genesis: A Generative and Universal Physics Engine for Robotics and Beyond](https://genesis-world.readthedocs.io/en/latest/). Official documentation and citation.
5. <a id="ref-newton"></a>The Newton Developers. [Newton Physics documentation](https://newton-physics.github.io/newton/). Solver, contact and versioned API documentation.
6. <a id="ref-physx"></a>NVIDIA. [PhysX SDK](https://github.com/NVIDIA-Omniverse/PhysX). Official source and release documentation.
7. <a id="ref-drake"></a>Russ Tedrake and the Drake Development Team. [Drake: Model-Based Design and Verification for Robotics](https://drake.mit.edu/), 2019.
8. <a id="ref-libero"></a>Bo Liu et al. [LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning](https://arxiv.org/abs/2306.03310). arXiv:2306.03310, 2023.
9. <a id="ref-robodojo"></a>Chen et al. [RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies](https://arxiv.org/abs/2607.04434). arXiv:2607.04434, 2026.
10. <a id="ref-robosimstudio"></a>RoboSimStudio Authors. [RoboSimStudio: An Interactive Toolkit for Rapid Real2Sim of Robot Manipulation Tasks](https://arxiv.org/abs/2610.18835). arXiv:2610.18835, 2026.
11. <a id="ref-superdex"></a>Meta Research. [SuperDex](https://github.com/facebookresearch/project_superdex). Official repository and versioned implementation.

### Project citation

```bibtex
@software{dexlab2026,
  author  = {Kiki Huang},
  title   = {DexLab: A Physics-Centric Research Platform for Contact-Rich Robot Manipulation},
  year    = {2026},
  url     = {https://github.com/huangkiki/Dexlab}
}
```
