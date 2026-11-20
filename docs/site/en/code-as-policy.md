# Code as Policy: from model-written programs to verified robot skills

## TL;DR

**Code as Policy is not “another VLA model.” It is a control representation: task semantics, feedback conditions and action order become an inspectable, editable program.**

Consider “grasp a bread slice, lift it, and place it on a plate.” A program may call localization, grasp generation, motion planning, gripper control, a hold check and release. Reliability depends less on whether an LLM can write Python than on where measurements come from, whether a close command matches the acquired contact, when support is lost, what the robot actually executed, and how an independent scorer defines success.

This deserves its own topic because at least four forms now need to be distinguished:

- a model generates programs at runtime, as in CaP-X and ASPIRE;
- programs are frozen online while a model edits them offline, as in COAP;
- an agent harness supplies tools, measurements and an admission gateway, as in HexaShell and Auriga;
- task knowledge lives in a page of Markdown as a task skill, not in a strategy program executed at runtime.

**For DexLab, Code as Policy is a way to study failure attribution and skill memory—not a replacement for the physics engine or evaluation contract.** Establish an auditable feedback chain on one existing failure before discussing skill promotion or automated evolution.

## 1. Start with one dropped slice

The following is teaching pseudocode, not an implemented DexLab or author API:

```python
bread = localize_object("bread slice")
grasp = select_grasp(bread, strategy="top_down")
move_to_pose(grasp.approach_pose)
close_gripper()

if not verify_hold("bread slice", min_lift_m=0.02):
    raise TaskFailure("grasp_not_established")

move_to_pose(plate.approach_pose)
open_gripper()
```

The program is easier to inspect because it names a task decomposition. It also introduces new failure locations:

- `localize_object` may select a neighbor or a shelf edge;
- `select_grasp` may produce a shallow top-edge pinch;
- a successful motion plan is not a measured arrival;
- a successful close call does not establish load-bearing contact;
- `verify_hold` may use stale vision, a wrong threshold, or miss rotation;
- the scorer may treat “above the plate” as “placed on the plate.”

The value is not that code is automatically reliable. Explicit programs turn reliability into **separate propositions that can be checked**. Without traces, state and independent scoring, code only packages the failure in plausible logic.

(execution-stack)=
## 2. A program is not a standalone layer

| Layer | Question | Typical contents | Must not be conflated with |
| --- | --- | --- | --- |
| Task | What to accomplish and when to stop or recover | language goal, stages, success predicates, retry budget | directly executable control logic |
| Program | How to compose perception and action | conditions, loops, functions, error branches | low-level servoing or physical truth |
| Skill | Which capabilities are reusable | localization, grasp generation, IK, trajectory execution, tools | an entire task-level instruction document |
| Execution | How commands become joint, contact and object response | controller, planner, simulator/hardware, clocks | task success |

Task code usually runs in an outer loop. Contact acquisition, slip and release may need millisecond-scale inner-loop control. CaP-X reports code iterations of roughly `6.8–23.8 s` and VLA action chunks or single-action inference of roughly `73–167 ms` under its conditions. These are not a fair performance ranking, but they show why Code as Policy belongs primarily at the system-2 task layer rather than replacing high-frequency contact control by default.

(policy-map)=
## 3. Four related forms are not one system

| Work | Runtime task decision maker | Primary artifact | Problem addressed | Key boundary |
| --- | --- | --- | --- | --- |
| [Code as Policies](https://arxiv.org/abs/2209.07753) | an LLM writes programs from language and API context | executable policy code | turn instructions into compositions of perception, geometry and control APIs | depends on hand-designed primitives and few-shot examples |
| [CaP-X](https://arxiv.org/abs/2603.22435) | a coding model writes code over one or multiple turns | benchmark, programs, execution feedback, skill library and RL interface | compare abstraction, interaction, visual grounding and test-time compute | scores depend on API scaffolding, feedback and budget |
| [COAP](https://arxiv.org/abs/2610.12369) | fixed code runs online; a coding agent edits code offline | explicit state, task programs, shared code library | make state, task logic and code changes auditable | all reported results are simulated; cross-body/material transfer is unproven |
| [ASPIRE](https://arxiv.org/abs/2607.00272) | a coding agent executes, diagnoses and repairs online | primitive traces and a reusable skill library | persist validated repairs and transfer them to later tasks | fixed API, frontier-model dependence, and one-time validation is not generalization |
| [HexaShell](https://arxiv.org/abs/2610.23479) / [Auriga](https://arxiv.org/abs/2611.01112) | a general model calls tools or writes short programs inside a harness | general tools, measurements, admission and optional task skills | reduce per-robot and per-benchmark task-specific code | the harness itself contributes to success and cannot be hidden inside a model-only score |
| [GR00T 2](https://research.nvidia.com/labs/gear/gr00t-2) | an agent selects stages and checks execution; a WAM handles contact; CaP handles scriptable repair | task program, MCP tools, CaP primitives and WAM API | separate long-horizon orchestration, local recovery and contact-rich manipulation | depends on correction data, RL, reliable success checks and sufficiently precise recovery primitives |

The important distinction is not the presence of Python. It is **whether a model remains in the runtime loop, where experience is stored—code, text or weights—and who owns safety and success determination.**

### CaP is not VLA

- VLA policies usually learn a mapping from observations to actions or action chunks from demonstrations.
- Code as Policy writes an explicit program; planners, controllers and robot APIs execute it.
- Code can be modified and instrumented more directly, but depends on the exposed API and execution stack.
- VLA generates continuous actions more directly, while task logic and intermediate failure attribution are often harder to inspect.

They are not mutually exclusive. A practical system can use Code as Policy in the task layer and a VLA, impedance controller or specialized controller for local contact.

### GR00T 2: separate ownership for agent, CaP and contact policy

GR00T 2 provides a concrete division of labour: **the agent decides what to do, CaP performs programmable transport and recovery, and the World-Action Model performs contact-rich manipulation that is hard to script.** They connect through an MCP tool server, and one control worker serializes commands so the policy and code programs do not drive the robot at the same time.

In randomized toy-car assembly, for example, the agent detects that a stage has stalled after a part is dropped and calls `localize_object`, `move_to_pose` and `set_gripper` to recover the state. It then hands wheel alignment and fastening back to GR00T 2. The agent has not learned assembly; it repairs an observable local state and returns control to the contact policy.

The paper reports three assembly tasks rising from `84/71/78` successes with SFT+DAgger to `98/97/97` with Agent+CaP. Five consecutive insertions reach `19/20` for Ethernet cables and `20/20` for chargers with SFT+RL+Agent. These results jointly include correction data, RL, task programs, retries and success checks; they cannot be assigned to the agent or CaP alone.

The failures expose the limit. Three of 300 agent-assisted assembly episodes failed because a screw was only partly driven, while both GR00T 2 and the agent judged the subtle visual difference complete. Without RL, only `24%` of S2 interventions on RoboDojo and `56%` on RoboCasa365 succeeded. Calling a recovery program is not the same as measuring the physical state correctly or establishing that the repair worked.

Nor is the WAM the only possible contact layer. [SuperMimic-manipulation](https://github.com/emoPointer/supermimic_manipulation) adapts SuperMimic-style differentiable world-model optimization to state-based arm manipulation. At the pinned revision it reports `95.0%` on seating a square nut on a peg and `90.2%` on placing a pod in a drawer and pushing it closed, each over 256 held-out reset episodes in simulated ARX5. This shows that a task-specific controller can carry the local contact role when the task is known, full body/object state is available, the workcell is fixed, and reset banks can be built. It sees only low-dimensional state, trains one policy per task, and has no language, open-vision, cross-embodiment, agent-recovery or real-robot result. It therefore does not replace GR00T 2's full system role. A replacement claim must compare the same task, state, action interface and scorer.

This page uses **CaP = Code-as-Policy**. It is unrelated to [Contact-Anchored Policy (CAP)](https://github.com/huangkiki/Dexlab/discussions/309), which removes ambiguity about where interaction should occur by conditioning on a 3D contact anchor. See [Discussion #419](https://github.com/huangkiki/Dexlab/discussions/419) for the full GR00T 2 review. Its candidate slice is in Triage only and is not an execution authorization.

### Task skill is not task program

A task program is an executable policy. A task skill is runtime guidance read by a model, such as completion conditions, validated parameters, common failures and budgets. HexaShell's task skill is roughly one page of text, not a task program that is automatically executed. Calling both “skills” obscures which knowledge actually entered runtime decisions.

## 4. Why it works, and where it breaks

### Mechanisms that help

1. **Composition.** One set of localization, grasp, planning and motion APIs can be recomposed across tasks without collecting a full demonstration dataset for every long-tail instruction.
2. **Auditability.** Each measurement and branch can retain value, source, time and uncertainty, allowing a failure to land on a specific API or transition.
3. **Persistent modification.** A trace can become a program diff, constraint or helper instead of a new set of learned weights.
4. **Feedback loops.** Multi-turn execution, structured visual differencing and primitive traces can support recovery from several failure classes.

### Dominant failures

- **Abstraction leakage.** A high-level `pick()` can hide localization, grasp and hold failures; a score then misattributes them to model understanding.
- **Feedback mismatch.** Raw images, success flags, text logs and contact impulses answer different questions. More feedback is not automatically better diagnosis.
- **System-layer conflation.** Model, harness, controller, simulator and scorer jointly determine a score.
- **Safety and supply boundaries.** Generated code needs allowlisted tools and isolation; a watchdog is not a security sandbox.
- **Skill contamination.** Extracting helpers from all successful trials can preserve lucky behavior or scorer exploits. One successful repair is not a general skill.
- **Cost and latency.** Multi-turn inference, parallel candidates, verifiers and evolutionary search consume model calls and physical rollouts.

(cap-evaluation)=
## 5. What a Code as Policy evaluation must record

- primitive abstraction and whether usage examples are supplied;
- single/multi-turn count and token/call budgets;
- whether feedback contains measured arrival, contact, error codes and keyframes;
- development, unseen-check and final held-out seed partitions;
- program, model, harness, controller, simulator and scorer versions;
- invalid runs, timeouts, interface errors and physical failures in the denominator;
- whether generated code can read reward, success, native or future state.

A claim that “model A has higher success” is usually uninterpretable without these conditions. The improvement may come from the model, API, extra attempts or changed scoring.

(dexlab-policy)=
## 6. How DexLab should use this route

### Borrow directly

1. **Use Code as Policy as an experimental representation.** Give task logic, measurements, actions and scoring explicit ownership so a failure can be traced to its first failing layer.
2. **Start with a feedback ablation.** For the existing bread or slot-contact failure, compare a terminal/visual-progress pack against a primitive/contact-state pack.
3. **Turn a root cause into a skill card.** Include failure signature, trigger, candidate repair, applicability, evidence and counterexample.
4. **Separate promotion from task success.** `verified_once`, `transferred` and `refuted` are different states. Reproduction on a few source seeds shows that knowledge can transmit, not that it generalizes.

### Defer

- replacing the physics engine or independent scorer with a code agent;
- making parallel candidates, evolutionary search or an open-ended library the default after one gain;
- using “skill” for both executable task programs and text guidance;
- treating author-reported scores, demos or interface existence as a DexLab reproduction.

### First testable question

Take the published toast-slip case, freeze task, physics and scoring, and add two observation packs:

- `A`: task stage, success predicate, before/after images or structured visual change;
- `B`: `A` plus per-primitive request/result, measured arrival, contact establishment/loss, impulse and first slip.

Let independent diagnosticians write the first-failure chain under each condition. The result is useful only if it:

- lands on the layer the measurements actually support;
- distinguishes competing explanations;
- is reproducible under the same configuration;
- preserves failure denominators and the old scoring path.

Only after this feedback contract is stable should DexLab test “write one repair as a skill card and ask a fresh verifier to reproduce it.” If feedback does not improve attribution, code generation and automated skill libraries only add cost.

## 7. Recommended reading order

1. Start with [Code as Policies](https://arxiv.org/abs/2209.07753) for the language-program and policy-API formulation.
2. Read [CaP-X](https://arxiv.org/abs/2603.22435) for abstraction, feedback and test-time computation, then [Discussion #341](https://github.com/huangkiki/Dexlab/discussions/341).
3. Read [COAP](https://arxiv.org/abs/2610.12369) for explicit state and controlled code changes, then [Discussion #335](https://github.com/huangkiki/Dexlab/discussions/335).
4. Read [ASPIRE](https://arxiv.org/abs/2607.00272) for traces, skill admission and held-out evaluation, then [Discussion #342](https://github.com/huangkiki/Dexlab/discussions/342).
5. Read §3.4 and Appendix G of the [GR00T 2 whitepaper](https://research.nvidia.com/labs/gear/gr00t-2/assets/gr00t2_whitepaper.pdf) for the agent, CaP, contact-policy and single-controller split, then [Discussion #419](https://github.com/huangkiki/Dexlab/discussions/419).
6. Return to DexLab's [toast-slip evidence](robodojo-bread-slip.md) and [model-evaluation protocol](model-evaluation.md) to decide what can enter a real failure chain.

## Evidence scope

This page maps methods and transferable mechanisms; it is not a cross-paper leaderboard. All performance figures are author-reported. The fixed CaP-X and ASPIRE source establishes trace, feedback, skill-admission and evaluation boundaries. GR00T 2 is checked against the November 2026 official whitepaper; its official code is not due until December 2026, so this review does not inspect that implementation. The review ran no external agent, external benchmark or new DexLab physics experiment. HexaShell and Auriga are positioned as adjacent agent harnesses from their official abstracts; their success rankings are not restated here.

For the broader simulation question, start with “[What are we discussing when we discuss dexterous-hand simulation?](dexterous-hand-simulation.md).” Code as Policy is a topic within its policy-and-evaluation layer, not the whole simulation framework.
